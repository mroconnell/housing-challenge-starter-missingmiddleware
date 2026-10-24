"""Market-adjusted California regression for the Wisconsin with-law rate y (Gate 3 revision, AQ-034).

Replaces the judgment-based California-to-Wisconsin transfer ratio. Each California
jurisdiction's post-2020 ADU-type rate (2023-2025 plateau, per 1,000 one-unit detached
homes per year) is explained by its pre-2020 activity group (active / middle /
restrictive, the study's wave-3 groups), its housing market (ACS 2020-2024 median home
value, median gross rent, optionally income) and its size. The fitted model is applied
to every Wisconsin area with its own ACS market values to give an area-specific y.

Model: Poisson regression of plateau permits with log exposure (homes x observed years
/ 1,000) as offset. With an exposure offset the Poisson fit is the homes-weighted rate
regression (each home-year counts once), it handles zeros without an arbitrary +c, and
its coefficients read as percentage changes in the rate. California counts are
over-dispersed, so standard errors and intervals come from a jurisdiction bootstrap
(and a robust sandwich), never from the Poisson variance.

Everything here is a pure function of data frames so the tests run offline on fixtures.
Descriptive language only: coefficients are associations across California places,
not causal effects of home values on ADU production.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.foundation.parsers import read_acs_sf

SEED = 20261024
N_BOOT = 1000
K_FOLDS = 10
PLATEAU_YEARS = (2023, 2024, 2025)
WAVE3_PRE = (2017, 2018, 2019)
WAVE1_PRE = (2014, 2015, 2016)
WAVE3_CUTOFF = 1.038   # published non-holdout permissive cutoff, wave 3 (CA_STUDY_RESULTS.md, section 2)
WAVE1_CUTOFF = 0.084   # published non-holdout permissive cutoff, waves 1-2
GROUP_NAMES = {"permissive": "active", "middle": "middle", "restrictive": "restrictive"}

# ---------------------------------------------------------------------------
# ACS market tables (keyless table-based summary file)
# ---------------------------------------------------------------------------

ACS_SF = "https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData"
MARKET_SOURCE_ID = "census_acs5_2024_tbsf_market"
MARKET_TABLES = ("b25077", "b25064", "b19013", "b25003")
# Top and bottom codes in the summary file (ACS medians are reported as these values
# when the median falls in the open-ended interval).
TOP_CODES = {"value": 2000001, "rent": 3501, "income": 250001}
BOTTOM_CODES = {"value": 9999, "rent": 99, "income": 2499}
UA = "missing-middleware-ca-regression/0.1 (Wisconsin housing research; keyless bulk files)"


def fetch_market_tables(folder: Path, force: bool = False, log=print) -> dict[str, Path]:
    """Download the four ACS market tables into `folder`, recording URL, bytes,
    SHA-256 and access date in folder/_downloads.json."""
    folder.mkdir(parents=True, exist_ok=True)
    man_path = folder / "_downloads.json"
    man = json.loads(man_path.read_text()) if man_path.exists() else {}
    out = {}
    for t in MARKET_TABLES:
        name = f"acsdt5y2024-{t}.dat"
        url = f"{ACS_SF}/{name}"
        path = folder / name
        if force or not path.exists():
            log(f"fetching {url}")
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=300) as r, open(path, "wb") as f:
                f.write(r.read())
            man[name] = {"url": url, "accessed": dt.date.today().isoformat()}
        if "sha256" not in man.get(name, {}) or force:
            h = hashlib.sha256(path.read_bytes()).hexdigest()
            man.setdefault(name, {"url": url, "accessed": dt.date.today().isoformat()})
            man[name].update({"bytes": path.stat().st_size, "sha256": h})
        out[t] = path
    man_path.write_text(json.dumps(man, indent=2, sort_keys=True))
    return out


def read_market(paths: dict[str, Path], state_fips: str, sumlevels: tuple[str, ...]) -> pd.DataFrame:
    """One row per geoid: value (B25077), rent (B25064), income (B19013), renter share
    (B25003), with MOEs and top/bottom-code flags. Missing medians stay NaN."""
    frames = []
    spec = {"b25077": ("B25077_E001", "B25077_M001", "value"),
            "b25064": ("B25064_E001", "B25064_M001", "rent"),
            "b19013": ("B19013_E001", "B19013_M001", "income")}
    for t, (e, m, name) in spec.items():
        if t not in paths:
            continue
        d = read_acs_sf(paths[t], state_fips=state_fips, sumlevels=sumlevels)
        d = d[["geoid", "sumlevel", e, m]].rename(columns={e: name, m: f"{name}_moe"})
        d[f"{name}_topcoded"] = d[name].ge(TOP_CODES[name])
        d[f"{name}_bottomcoded"] = d[name].le(BOTTOM_CODES[name])
        # top-coded medians are "X or more": use the code minus one as the value
        d.loc[d[f"{name}_topcoded"], name] = TOP_CODES[name] - 1
        frames.append(d.set_index(["geoid", "sumlevel"]))
    if "b25003" in paths:
        d = read_acs_sf(paths["b25003"], state_fips=state_fips, sumlevels=sumlevels)
        d["renter_share"] = d["B25003_E003"] / d["B25003_E001"]
        d["occupied"] = d["B25003_E001"]
        frames.append(d.set_index(["geoid", "sumlevel"])[["renter_share", "occupied"]])
    out = pd.concat(frames, axis=1).reset_index()
    return out


# ---------------------------------------------------------------------------
# California jurisdictions: market values, groups, outcome
# ---------------------------------------------------------------------------

MARKET_COLS = ("value", "rent", "income", "renter_share")


def ca_jurisdiction_market(juris: pd.Series, market: pd.DataFrame) -> pd.DataFrame:
    """Market values for HCD-style jurisdiction ids (7-digit place geoid, or 'SSCCC_UNINC').

    Cities: the place (sumlevel 160). County unincorporated remainders: ACS medians
    cannot be differenced, so the remainder takes the whole county's median (sumlevel
    050) as a proxy (market_basis = county_proxy). A city with a missing median also
    falls back to its county (county_fallback); the county is read from `juris` ids for
    remainders and supplied by the caller's county map for cities.
    """
    pl = market[market.sumlevel.eq("160")].set_index("geoid")
    co = market[market.sumlevel.eq("050")].set_index("geoid")
    rows = []
    for j in juris:
        if j.endswith("_UNINC"):
            src, basis = co, "county_proxy"
            key = j[:5]
        else:
            src, basis = pl, "place"
            key = j
        r = {"census_geoid": j, "market_basis": basis}
        for c in MARKET_COLS:
            r[c] = src[c].get(key, np.nan) if c in src else np.nan
        for c in ("value_topcoded", "rent_topcoded"):
            r[c] = bool(src[c].get(key, False)) if c in src else False
        rows.append(r)
    return pd.DataFrame(rows)


def fill_from_county(df: pd.DataFrame, market: pd.DataFrame, county_of: pd.Series) -> pd.DataFrame:
    """Fill missing city medians from the county row; flag which columns were filled."""
    co = market[market.sumlevel.eq("050")].set_index("geoid")
    df = df.copy()
    df["filled"] = ""
    for c in ("value", "rent", "income"):
        miss = df[c].isna() & df["census_geoid"].map(county_of).notna()
        if miss.any():
            df.loc[miss, c] = df.loc[miss, "census_geoid"].map(county_of).map(co[c])
            df.loc[miss, "filled"] = df.loc[miss, "filled"] + f"{c}_county;"
    return df


def jurisdiction_groups(s: pd.DataFrame, pre_years: tuple[int, ...], cutoff: float) -> pd.DataFrame:
    """The study's group rules (ca_study.assign_groups) for one pre-period: permissive
    (active) = pre rate >= cutoff and >= 3 permits; restrictive = zero every pre-year;
    middle = the rest; excluded_missing = a missing pre-year."""
    pre = s[s["year"].isin(pre_years)]
    g = pre.groupby("census_geoid").agg(n_obs=("adu", "count"), pre_permits=("adu", "sum"),
                                        pre_max=("adu", "max"), homes=("homes", "first"))
    g["complete"] = g["n_obs"].eq(len(pre_years))
    g["pre_rate"] = g["pre_permits"] / (g["n_obs"] * g["homes"]) * 1000
    grp = pd.Series("middle", index=g.index, dtype=object)
    grp[(g["pre_rate"] >= cutoff) & (g["pre_permits"] >= 3)] = "permissive"
    grp[g["pre_max"].eq(0)] = "restrictive"
    grp[~g["complete"]] = "excluded_missing"
    g["group"] = grp
    return g


def panel_series(panel: pd.DataFrame, measure: str = "adu_main") -> pd.DataFrame:
    """All jurisdictions (holdout included: the holdout test is published, AQ-034)."""
    return (panel[["census_geoid", "year", "sf_detached", "name", "juris_type"]]
            .assign(adu=panel[measure]).rename(columns={"sf_detached": "homes"}))


def plateau_outcome(s: pd.DataFrame, years: tuple[int, ...] = PLATEAU_YEARS) -> pd.DataFrame:
    """Plateau permits and observed years per jurisdiction (missing years are not zero)."""
    p = s[s["year"].isin(years)].dropna(subset=["adu"])
    return p.groupby("census_geoid").agg(adu=("adu", "sum"), n_years=("adu", "count"), homes=("homes", "first"))


def adoption_events(s: pd.DataFrame, adoption: pd.Series) -> pd.DataFrame:
    """Event-time view: k = year - adoption_year + 1 for each jurisdiction-year."""
    a = s["census_geoid"].map(adoption).fillna(2020).astype(int)
    return s.assign(adoption_year=a, k=s["year"] - a + 1)


def event_plateau(s: pd.DataFrame, adoption: pd.Series, ks=(4, 5, 6)) -> pd.DataFrame:
    """Plateau in event time: event years 4-6 after the jurisdiction's own benchmark
    adoption (2023-2025 for the 2020 default)."""
    e = adoption_events(s, adoption)
    p = e[e["k"].isin(ks)].dropna(subset=["adu"])
    return p.groupby("census_geoid").agg(adu=("adu", "sum"), n_years=("adu", "count"), homes=("homes", "first"))


def event_groups(s: pd.DataFrame, adoption: pd.Series) -> pd.Series:
    """Pre-adoption activity group: the 3 years before each jurisdiction's adoption year.
    2020 adopters use the wave-3 cutoff (2017-2019 under the 2017-2018 state laws);
    earlier adopters use the wave-1 cutoff (their pre-years are the pre-2017 regime)."""
    out = jurisdiction_groups(s, WAVE3_PRE, WAVE3_CUTOFF)["group"]
    for j, a in adoption.items():
        a = int(a)
        if a == 2020 or j not in out.index:
            continue
        pre = tuple(range(a - 3, a))
        g = jurisdiction_groups(s[s.census_geoid.eq(j)], pre, WAVE1_CUTOFF)["group"]
        if j in g.index:
            out[j] = g[j]
    return out


def build_ca_dataset(panel: pd.DataFrame, market: pd.DataFrame, county_of: pd.Series,
                     measure: str = "adu_main", adoption: pd.Series | None = None) -> pd.DataFrame:
    """One row per grouped California jurisdiction with outcome, exposure, group and market.

    adoption: optional jurisdiction -> benchmark adoption year; when given, the outcome is
    the event-time plateau (event years 4-6) and the group the pre-adoption group.
    """
    s = panel_series(panel, measure)
    if adoption is None:
        grp = jurisdiction_groups(s, WAVE3_PRE, WAVE3_CUTOFF)
        out = plateau_outcome(s).join(grp[["group", "pre_rate"]], how="inner")
    else:
        g = event_groups(s, adoption)
        pre = jurisdiction_groups(s, WAVE3_PRE, WAVE3_CUTOFF)["pre_rate"]
        out = event_plateau(s, adoption).join(g.rename("group"), how="inner").join(pre)
    out = out[out["group"].isin(GROUP_NAMES)].copy()
    out["group"] = out["group"].map(GROUP_NAMES)
    names = s.groupby("census_geoid")[["name", "juris_type"]].first()
    out = out.join(names)
    mk = ca_jurisdiction_market(pd.Series(out.index), market)
    mk = fill_from_county(mk, market, county_of)
    out = out.join(mk.set_index("census_geoid"))
    out["rate"] = out["adu"] / (out["n_years"] * out["homes"]) * 1000
    out["exposure"] = out["n_years"] * out["homes"] / 1000
    out = out[(out["homes"] > 0) & (out["n_years"] > 0)]
    return out.reset_index()


# ---------------------------------------------------------------------------
# Design matrix and Poisson regression (numpy IRLS)
# ---------------------------------------------------------------------------

# Centring points make the intercept readable (an active place at $500k / $2,000 / 10k homes).
CENTRES = {"value": 500_000.0, "rent": 2_000.0, "income": 100_000.0, "homes": 10_000.0}
VALUE_KNOT = 700_000.0  # about the California median jurisdiction value ($714k), fixed as a round number


@dataclass(frozen=True)
class Spec:
    name: str
    terms: tuple[str, ...]          # from: group, log_value, log_rent, log_income, log_homes, renter_share, value_k
    label: str = ""


SPECS = (
    Spec("group_only", ("group",), "Group only (reproduces the study's pooled group curve)"),
    Spec("group_value", ("group", "log_value"), "Group + log home value"),
    Spec("group_rent", ("group", "log_rent"), "Group + log gross rent"),
    Spec("group_value_size", ("group", "log_value", "log_homes"), "Group + log home value + log size"),
    Spec("group_rent_size", ("group", "log_rent", "log_homes"), "Group + log rent + log size"),
    Spec("group_value_rent_size", ("group", "log_value", "log_rent", "log_homes"), "Group + log value + log rent + log size"),
    Spec("group_value_hinge_size", ("group", "log_value", "log_value_below_knot", "log_homes"),
         "Group + log home value with a second slope below $700k + log size"),
    Spec("group_value_income_size", ("group", "log_value", "log_income", "log_homes"), "Group + log value + log income + log size"),
)
SPEC_BY_NAME = {s.name: s for s in SPECS}


def design(df: pd.DataFrame, terms: tuple[str, ...], value_clamp: float | None = None) -> tuple[np.ndarray, list[str]]:
    cols, names = [np.ones(len(df))], ["intercept"]
    value = df["value"].astype(float)
    if value_clamp is not None:
        value = value.clip(lower=value_clamp)
    for t in terms:
        if t == "group":
            for g in ("middle", "restrictive"):
                cols.append(df["group"].eq(g).astype(float).to_numpy())
                names.append(f"group_{g}")
        elif t == "log_value":
            cols.append(np.log(value / CENTRES["value"]).to_numpy())
            names.append(t)
        elif t == "log_value_below_knot":   # extra slope below the knot (piecewise-linear in log value)
            cols.append(np.minimum(np.log(value / VALUE_KNOT), 0.0).to_numpy())
            names.append(t)
        elif t == "value_k":   # level form: per $100k
            cols.append(((value - CENTRES["value"]) / 100_000).to_numpy())
            names.append(t)
        elif t == "log_rent":
            cols.append(np.log(df["rent"].astype(float) / CENTRES["rent"]).to_numpy())
            names.append(t)
        elif t == "log_income":
            cols.append(np.log(df["income"].astype(float) / CENTRES["income"]).to_numpy())
            names.append(t)
        elif t == "log_homes":
            cols.append(np.log(df["homes"].astype(float).clip(lower=1) / CENTRES["homes"]).to_numpy())
            names.append(t)
        elif t == "renter_share":
            cols.append((df["renter_share"].astype(float) - 0.4).to_numpy())
            names.append(t)
        else:
            raise ValueError(f"unknown term {t}")
    return np.column_stack(cols), names


def fit_poisson(X: np.ndarray, y: np.ndarray, exposure: np.ndarray, maxit: int = 100, tol: float = 1e-10) -> np.ndarray:
    """Poisson MLE with log link and log(exposure) offset, by IRLS."""
    off = np.log(exposure)
    beta = np.zeros(X.shape[1])
    beta[0] = np.log(max(y.sum(), 1e-9) / exposure.sum())
    for _ in range(maxit):
        eta = X @ beta + off
        mu = np.exp(eta)
        z = eta - off + (y - mu) / mu
        XtW = X.T * mu
        new = np.linalg.solve(XtW @ X + 1e-10 * np.eye(X.shape[1]), XtW @ z)
        if np.max(np.abs(new - beta)) < tol:
            beta = new
            break
        beta = new
    return beta


def robust_se(X: np.ndarray, y: np.ndarray, exposure: np.ndarray, beta: np.ndarray) -> np.ndarray:
    mu = exposure * np.exp(X @ beta)
    bread = np.linalg.inv((X.T * mu) @ X)
    meat = (X.T * (y - mu) ** 2) @ X
    return np.sqrt(np.diag(bread @ meat @ bread))


def poisson_deviance(y: np.ndarray, mu: np.ndarray) -> float:
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(y > 0, y * np.log(y / mu), 0.0)
    return float(2 * np.sum(t - (y - mu)))


@dataclass
class Fit:
    spec: Spec
    names: list[str]
    beta: np.ndarray
    se: np.ndarray
    value_clamp: float | None = None
    dispersion: float = np.nan

    def predict_rate(self, df: pd.DataFrame) -> np.ndarray:
        X, _ = design(df, self.spec.terms, self.value_clamp)
        return np.exp(X @ self.beta)  # per 1,000 homes per year (exposure is in 1,000 home-years)


def fit(df: pd.DataFrame, spec: Spec, value_clamp: float | None = None) -> Fit:
    X, names = design(df, spec.terms, value_clamp)
    y = df["adu"].to_numpy(float)
    ex = df["exposure"].to_numpy(float)
    b = fit_poisson(X, y, ex)
    mu = ex * np.exp(X @ b)
    disp = float(np.sum((y - mu) ** 2 / mu) / max(len(y) - len(b), 1))
    return Fit(spec, names, b, robust_se(X, y, ex, b), value_clamp, disp)


def complete_rows(df: pd.DataFrame, spec: Spec) -> pd.Series:
    need = {"log_value": "value", "value_k": "value", "log_value_below_knot": "value", "log_rent": "rent", "log_income": "income",
            "renter_share": "renter_share"}
    ok = pd.Series(True, index=df.index)
    for t in spec.terms:
        if t in need:
            ok &= df[need[t]].notna() & (df[need[t]] > 0 if t != "renter_share" else True)
    return ok


# ---------------------------------------------------------------------------
# Cross-validation
# ---------------------------------------------------------------------------

def kfold_ids(n: int, k: int = K_FOLDS, seed: int = SEED) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.permutation(np.arange(n) % k)


def cross_validate(df: pd.DataFrame, specs=SPECS, k: int = K_FOLDS, seed: int = SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Out-of-fold predictions for every spec on the same rows (rows complete for all specs)
    and the same folds. Returns (predictions, metrics)."""
    ok = pd.Series(True, index=df.index)
    for s in specs:
        ok &= complete_rows(df, s)
    d = df[ok].reset_index(drop=True)
    folds = kfold_ids(len(d), k, seed)
    preds = d[["census_geoid", "name", "group", "homes", "n_years", "adu", "rate", "value", "exposure"]].copy()
    preds["fold"] = folds
    for s in specs:
        p = np.full(len(d), np.nan)
        for f in range(k):
            tr, te = folds != f, folds == f
            m = fit(d[tr], s)
            p[te] = m.predict_rate(d[te])
        preds[f"pred_{s.name}"] = p
    low = d["value"] <= d["value"].quantile(0.25)
    rows = []
    for s in specs:
        p = preds[f"pred_{s.name}"].to_numpy()
        for subset, mask in (("all", np.ones(len(d), bool)), ("lowest_value_quarter", low.to_numpy())):
            a, pr, h = preds["rate"].to_numpy()[mask], p[mask], preds["homes"].to_numpy()[mask]
            ex = preds["exposure"].to_numpy()[mask]
            err = a - pr
            act_tot, pred_tot = (a * ex).sum(), (pr * ex).sum()
            fold_err = []
            for f in range(k):
                fm = (folds[mask] == f)
                if fm.any():
                    fa, fp = (a[fm] * ex[fm]).sum(), (pr[fm] * ex[fm]).sum()
                    if fa > 0:
                        fold_err.append(abs(fp - fa) / fa)
            grp_err = []
            for g in ("active", "middle", "restrictive"):
                gm = preds["group"].to_numpy()[mask] == g
                if gm.any() and (a[gm] * ex[gm]).sum() > 0:
                    grp_err.append(abs((pr[gm] * ex[gm]).sum() - (a[gm] * ex[gm]).sum()) / (a[gm] * ex[gm]).sum())
            rows.append({
                "spec": s.name, "subset": subset, "n": int(mask.sum()),
                "mae": float(np.mean(np.abs(err))), "mae_homes_weighted": float(np.average(np.abs(err), weights=h)),
                "median_abs_error": float(np.median(np.abs(err))), "rmse": float(np.sqrt(np.mean(err ** 2))),
                "poisson_deviance_per_place": poisson_deviance(a * ex, pr * ex) / mask.sum(),
                "actual_total": float(act_tot), "predicted_total": float(pred_tot),
                "total_error_pct": float((pred_tot - act_tot) / act_tot * 100) if act_tot else np.nan,
                "mean_abs_fold_total_error_pct": float(np.mean(fold_err) * 100) if fold_err else np.nan,
                "mean_abs_group_total_error_pct": float(np.mean(grp_err) * 100) if grp_err else np.nan,
            })
    return preds, pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def bootstrap_betas(df: pd.DataFrame, spec: Spec, n_boot: int = N_BOOT, seed: int = SEED,
                    value_clamp: float | None = None) -> np.ndarray:
    """Jurisdiction bootstrap, resampling within each group (groups held fixed, as in the study)."""
    rng = np.random.default_rng(seed + 11)
    d = df[complete_rows(df, spec)].reset_index(drop=True)
    X, _ = design(d, spec.terms, value_clamp)
    y, ex = d["adu"].to_numpy(float), d["exposure"].to_numpy(float)
    idx_by_g = [np.flatnonzero(d["group"].to_numpy() == g) for g in ("active", "middle", "restrictive")]
    out = np.empty((n_boot, X.shape[1]))
    for b in range(n_boot):
        idx = np.concatenate([rng.choice(ix, size=len(ix), replace=True) for ix in idx_by_g if len(ix)])
        out[b] = fit_poisson(X[idx], y[idx], ex[idx])
    return out


def plain_language(fit_: Fit, draws: np.ndarray | None = None) -> pd.DataFrame:
    """Coefficient table with plain-language readings."""
    rows = []
    for i, n in enumerate(fit_.names):
        b = fit_.beta[i]
        lo = hi = np.nan
        if draws is not None:
            lo, hi = np.percentile(draws[:, i], [2.5, 97.5])
        if n == "intercept":
            txt = "rate for an active place at the centring point ($500k value, $2,000 rent, 10,000 homes)"
            eff, elo, ehi = np.exp(b), np.exp(lo), np.exp(hi)
        elif n.startswith("group_"):
            txt = f"{n[6:]} places' rate relative to active places with the same market and size (ratio)"
            eff, elo, ehi = np.exp(b), np.exp(lo), np.exp(hi)
        elif n.startswith("log_"):
            what = {"log_value_below_knot": "home values (extra effect below $700k)", "log_value": "home values", "log_rent": "rents", "log_income": "incomes", "log_homes": "size (homes)"}[n]
            txt = f"places with 10% higher {what} had this % higher ADU rate, other terms equal"
            eff, elo, ehi = (1.1 ** b - 1) * 100, (1.1 ** lo - 1) * 100, (1.1 ** hi - 1) * 100
        else:
            txt = "per unit change"
            eff, elo, ehi = np.exp(b), np.exp(lo), np.exp(hi)
        rows.append({"spec": fit_.spec.name, "term": n, "coef": b, "robust_se": fit_.se[i],
                     "boot_lo": lo, "boot_hi": hi, "effect": eff, "effect_lo": elo, "effect_hi": ehi,
                     "reading": txt})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Wisconsin application
# ---------------------------------------------------------------------------

# Wisconsin -> California pre-2020 group (owner rule, 2026-10-24): Wisconsin places with
# current ADU activity behave like California's already-active places; places at zero or
# unmeasured activity behave like California's restrictive places in 2020. "Current
# activity" = a current-law rate at the Madison-like level (x >= 0.1: Madison, Wauwatosa,
# Appleton, and Milwaukee after its 2025 by-right reform). Two readings:
#   absolute: apply California's own pre-period thresholds. California's active cutoff is
#     1.04 per 1,000 a year; Madison-like 0.18 is non-zero but far below it, i.e. California
#     "middle". Everything else (x 0.03-0.06, which a typical place shows as zero permits
#     over three years) is "restrictive".
#   relative: rank within Wisconsin, so the observed-active places count as "active".
# Unmeasured places (undetermined rules, estimated x) are restrictive under the owner rule;
# `unmeasured_middle` is the sensitivity that maps them to middle instead.
#   rules (owner follow-up): by coded rights class. scenario_benchmark -> active,
#     restricted -> middle, prohibited -> restrictive, undetermined -> restrictive
#     (`rules_unmeasured_middle`: undetermined -> middle). California's active group mixes
#     permissive rules with strong markets; with market terms in the model, this mapping
#     lets the market term carry a benchmark place's lower level.
MIDDLE_X_THRESHOLD = 0.1


def wi_group(areas: pd.DataFrame, rule: str = "absolute") -> pd.Series:
    active_now = areas["x_rate"] >= MIDDLE_X_THRESHOLD
    if rule in ("absolute", "main"):
        g = np.where(active_now, "middle", "restrictive")
    elif rule == "relative":
        g = np.where(active_now, "active", "restrictive")
    elif rule == "unmeasured_middle":
        g = np.where(active_now | areas["rights_basis"].eq("undetermined"), "middle", "restrictive")
    elif rule in ("rules", "rules_unmeasured_middle"):
        # (c) by coded rules: benchmark -> active, restricted -> middle, prohibited -> restrictive,
        # undetermined -> restrictive (owner rule) or middle (sensitivity)
        rb = areas["rights_basis"]
        g = np.select([rb.eq("scenario_benchmark"), rb.eq("restricted"),
                       rb.eq("undetermined") & (rule == "rules_unmeasured_middle")],
                      ["active", "middle", "middle"], default="restrictive")
    elif rule == "all_restrictive":
        g = np.full(len(areas), "restrictive")
    elif rule == "all_middle":
        g = np.full(len(areas), "middle")
    else:
        raise ValueError(rule)
    return pd.Series(g, index=areas.index)


def wi_market(areas: pd.DataFrame, market: pd.DataFrame) -> pd.DataFrame:
    """ACS county-subdivision (060) medians per Wisconsin area. Area ids are
    'muni:' + 10-digit county-subdivision geoid. Missing medians (small places with too
    few sample cases) fall back to the same municipality's largest other county piece
    (cousub codes are state-unique), then to the county (050). Each fallback is flagged."""
    cs = market[market.sumlevel.eq("060")].set_index("geoid")
    co = market[market.sumlevel.eq("050")].set_index("geoid")
    a = areas[["area_id", "homes"]].copy()
    a["geoid"] = a["area_id"].str.replace("muni:", "", regex=False)
    a["county"] = a["geoid"].str[:5]
    a["cousub"] = a["geoid"].str[5:]
    occ = cs["occupied"] if "occupied" in cs else pd.Series(dtype=float)
    out = a.copy()
    for c in ("value", "rent", "income", "renter_share"):
        out[c] = a["geoid"].map(cs[c]) if c in cs else np.nan
        out[f"{c}_basis"] = np.where(out[c].notna(), "cousub", "")
    for c in ("value", "rent", "income"):
        miss = out[c].isna()
        if miss.any():
            # other pieces of the same municipality
            pieces = cs[cs[c].notna()].copy()
            pieces["cousub"] = pieces.index.str[5:]
            pieces["occ"] = occ.reindex(pieces.index).fillna(0)
            best = pieces.sort_values("occ", ascending=False).groupby("cousub")[c].first()
            fill = out.loc[miss, "cousub"].map(best)
            ok = fill.notna()
            out.loc[fill[ok].index, c] = fill[ok]
            out.loc[fill[ok].index, f"{c}_basis"] = "other_county_piece"
            miss = out[c].isna()
            out.loc[miss, c] = out.loc[miss, "county"].map(co[c])
            out.loc[miss, f"{c}_basis"] = "county_fallback"
        top = out["geoid"].map(cs.get(f"{c}_topcoded", pd.Series(dtype=bool))).fillna(False)
        out[f"{c}_topcoded"] = top.astype(bool)
    return out.drop(columns=["county", "cousub"])


def extrapolation_flags(wi: pd.DataFrame, ca: pd.DataFrame) -> pd.DataFrame:
    """Where Wisconsin inputs fall outside the California fitting range."""
    f = pd.DataFrame(index=wi.index)
    v5, vmin = ca["value"].quantile(0.05), ca["value"].min()
    r5, rmin = ca["rent"].quantile(0.05), ca["rent"].min()
    hmin = ca["homes"].min()
    f["value_below_ca_min"] = wi["value"] < vmin
    f["value_below_ca_p5"] = wi["value"] < v5
    f["rent_below_ca_min"] = wi["rent"] < rmin
    f["rent_below_ca_p5"] = wi["rent"] < r5
    f["homes_below_ca_min"] = wi["homes"] < hmin
    lab = []
    for i in f.index:
        r = f.loc[i]
        if r.value_below_ca_min or r.rent_below_ca_min:
            lab.append("outside_ca_range")
        elif r.value_below_ca_p5 or r.rent_below_ca_p5:
            lab.append("ca_tail")
        else:
            lab.append("inside")
        if r.homes_below_ca_min:
            lab[-1] += "+size_below_ca_min"
    f["extrapolation"] = lab
    return f


def predict_draws(df: pd.DataFrame, spec: Spec, draws: np.ndarray, value_clamp: float | None = None) -> np.ndarray:
    X, _ = design(df, spec.terms, value_clamp)
    return np.exp(X @ draws.T)  # areas x draws, per 1,000 homes per year
