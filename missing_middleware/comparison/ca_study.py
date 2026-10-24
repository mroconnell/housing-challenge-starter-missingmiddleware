"""Pre-registered California comparison study (docs/gate3/CA_COMPARISON_PLAN.md, G2-8).

Descriptive comparisons only: groups are defined from pre-period outcomes, and every
result is an association around the statewide reform waves, not a causal effect.

Pipeline (all pure functions of data frames so tests run on tiny fixtures):

1. ``hcd_adu_outcome``: from de-identified APR Table A2 rows, ADU-type second homes by
   jurisdiction and year under the main measure (permit dated in the report year) and the
   issue-year sensitivity, with rows identifiable from free text as legalizations,
   ADUs built with a new house, or ADUs on multifamily lots excluded. Free text is read in
   memory only; only counts leave this module.
2. ``build_panel``: jurisdiction x year 2012-2025 with three outcome series (main,
   issue-year, compilation for 2018-2019), observed flags, ACS one-unit detached homes.
3. ``assign_groups`` / ``group_year`` / ``wave_summary`` / ``ramp`` / ``bootstrap``:
   pre-registered groups, event-study table, difference-in-differences, spillover, ramp,
   plateau, computed on NON-HOLDOUT jurisdictions only.
4. ``holdout_test``: predicts holdout jurisdictions' post-wave-3 rates from the
   non-holdout curve by pre-period group. No all-data refit is done anywhere.
5. ``share_model``: ADU-type second homes as a share of (BPS total units + ADUs not in
   BPS), for an unidentified ADU-in-BPS overlap s in [0, 0.5] (step 0, B1).
"""
from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

YEARS = tuple(range(2012, 2026))
COMPILATION_ONLY_YEARS = tuple(range(2012, 2018))
HCD_YEARS = tuple(range(2018, 2026))
LA_CITY = "0644000"
SEED = 20261024
N_BOOT = 2000
OVERLAP_S = (0.0, 0.25, 0.5)


@dataclass(frozen=True)
class Wave:
    wave: int
    effective: int
    pre: tuple[int, ...]
    post: tuple[int, ...]


WAVES = (
    Wave(1, 2017, (2014, 2015, 2016), (2017,)),
    Wave(2, 2018, (2014, 2015, 2016), (2018, 2019)),
    Wave(3, 2020, (2017, 2018, 2019), (2020, 2021, 2022, 2023, 2024, 2025)),
)
WAVE3 = WAVES[2]
PLATEAU_YEARS = (2023, 2024, 2025)  # years 4-6 after wave 3, counting 2020 as year 1


# ---------------------------------------------------------------------------
# 1. Outcome from HCD APR Table A2 rows
# ---------------------------------------------------------------------------

# Free-text rules, fixed before any group result was computed. Each matched permit is
# excluded from the outcome (the plan: "excluding rows identifiable as legalizations ...
# ADUs on multifamily lots or built with a new house excluded where the record identifies them").
TEXT_RULES = {
    "legalization": re.compile(
        r"legaliz|legalis|unpermitted|un-permitted|after[- ]the[- ]fact|as[- ]built|\babate|"
        r"code enforcement|code case|code violation|clear (a |the )?violation"),
    "new_house": re.compile(
        r"\bnew (sfd|sfr|single[- ]family (home|house|dwelling|residence))\b|"
        r"\b(sfd|sfr) (with|w/|and|&|\+) (an? )?(attached |detached )?adu\b|"
        r"accessory to (a )?new (sfd|sfr|house|home|single)|in (a )?new single[- ]family"),
    "multifamily_lot": re.compile(
        r"multi[- ]?family|\bapartments?\b|\btriplex\b|\bfourplex\b|\bfour-plex\b|\bquadplex\b"),
}
TEXT_RULE_ORDER = ("legalization", "new_house", "multifamily_lot")


def classify_adu_text(text: pd.Series) -> pd.Series:
    """First matching rule in TEXT_RULE_ORDER, else 'kept'. Case-insensitive."""
    t = text.fillna("").str.lower()
    out = pd.Series("kept", index=text.index, dtype=object)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="This pattern is interpreted as a regular expression")
        for name in reversed(TEXT_RULE_ORDER):
            out[t.str.contains(TEXT_RULES[name], regex=True)] = name
    return out


def hcd_adu_outcome(rows: pd.DataFrame, text_flag: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    """ADU-type second homes by HCD jurisdiction and year.

    rows: output of ca_inputs.classify_permit_rows (de-identified, with permit_key).
    text_flag: classify_adu_text of NOTES + PROJECT_NAME, aligned to rows' index.
    A permit is excluded if any of its listings is flagged.

    Returns (outcome, exclusions):
      outcome: juris_name, year, adu_main (permit dated in report year or undated),
               adu_issue (each permit once, in its issue year), adu_main_unadjusted.
      exclusions: counts of excluded units by rule and year (main measure).
    """
    r = rows[rows["unit_cat"].eq("ADU") & rows["bp_units"].fillna(0).gt(0)].copy()
    r["text_flag"] = text_flag.reindex(r.index).fillna("kept")
    flagged_keys = r.loc[r["text_flag"].ne("kept"), ["permit_key", "text_flag"]].drop_duplicates("permit_key")
    key_flag = dict(zip(flagged_keys["permit_key"], flagged_keys["text_flag"]))
    r["flag"] = r["permit_key"].map(key_flag).fillna("kept")
    primary = r["date_status"].isin(["date_in_year", "date_missing"])
    m = r[primary]
    main_all = m.groupby(["juris_name", "year"])["bp_units"].sum().rename("adu_main_unadjusted")
    main = m[m["flag"].eq("kept")].groupby(["juris_name", "year"])["bp_units"].sum().rename("adu_main")
    iss = r[r["flag"].eq("kept")].sort_values("year").drop_duplicates("permit_key", keep="first")
    iss = iss.assign(issue_year=iss["bp_issue_year"].fillna(iss["year"]).astype(int))
    iss = iss[iss["issue_year"].between(min(HCD_YEARS), max(HCD_YEARS))]
    issue = iss.groupby(["juris_name", "issue_year"])["bp_units"].sum().rename("adu_issue")
    issue.index = issue.index.set_names(["juris_name", "year"])
    out = pd.concat([main, issue, main_all], axis=1).fillna(0).reset_index()
    out["year"] = out["year"].astype(int)
    exc = (m.groupby(["year", "flag"])["bp_units"].sum().unstack(fill_value=0)
           .reindex(columns=["kept"] + list(TEXT_RULE_ORDER), fill_value=0).reset_index())
    exc.columns.name = None
    exc["year"] = exc["year"].astype(int)
    return out, exc


# ---------------------------------------------------------------------------
# 2. Jurisdiction-year panel
# ---------------------------------------------------------------------------

def build_panel(outcome: pd.DataFrame, comp: pd.DataFrame, filing: pd.DataFrame,
                xw: pd.DataFrame, den: pd.DataFrame) -> pd.DataFrame:
    """census_geoid x year 2012-2025.

    Columns: adu_main, adu_issue, adu_comp1819 (counts, NaN = missing, never zero),
    sf_detached (ACS 2020-2024), in_holdout, name, juris_type.
    Sources by year (plan): compilation 2012-2017; HCD main measure 2018+. Sensitivities:
    adu_issue uses the HCD issue-year measure for 2018+; adu_comp1819 uses the compilation
    for 2018-2019. An HCD year is observed only if the jurisdiction filed Table A2 rows that
    year (filing_status 'a2_rows'); 'filed_no_a2_rows' and 'no_record' are missing.
    """
    names = xw[["juris_name", "census_geoid"]].drop_duplicates()
    geo = (xw.drop_duplicates("census_geoid").set_index("census_geoid")[["juris_type", "in_holdout"]])
    c = comp.merge(names, on="juris_name", how="left")
    if c["census_geoid"].isna().any():
        raise ValueError(f"compilation names not in crosswalk: {sorted(c.loc[c.census_geoid.isna(), 'juris_name'])[:5]}")
    c = c[c["value_status"].eq("observed")].groupby(["census_geoid", "year"])["adu_permits"].sum()
    h = outcome.merge(names, on="juris_name", how="left")
    if h["census_geoid"].isna().any():
        raise ValueError("HCD names not in crosswalk")
    h = h.groupby(["census_geoid", "year"])[["adu_main", "adu_issue"]].sum()
    filed = filing[filing["filing_status"].eq("a2_rows")][["census_geoid", "year"]]
    filed = set(zip(filed["census_geoid"], filed["year"].astype(int)))
    geoids = sorted(set(geo.index) & (set(c.index.get_level_values(0)) | set(h.index.get_level_values(0))))
    idx = pd.MultiIndex.from_product([geoids, YEARS], names=["census_geoid", "year"])
    p = pd.DataFrame(index=idx).reset_index()
    p["comp"] = c.reindex(idx).to_numpy()
    hh = h.reindex(idx)
    is_filed = np.array([(g, y) in filed for g, y in zip(p["census_geoid"], p["year"])])
    for col in ("adu_main", "adu_issue"):
        v = hh[col].fillna(0).to_numpy()
        p[col + "_hcd"] = np.where(is_filed, v, np.nan)
    hcd_year = p["year"].isin(HCD_YEARS)
    p["adu_main"] = np.where(hcd_year, p["adu_main_hcd"], p["comp"])
    p["adu_issue"] = np.where(hcd_year, p["adu_issue_hcd"], p["comp"])
    p["adu_comp1819"] = np.where(p["year"].isin((2018, 2019)), p["comp"], p["adu_main"])
    p = p.drop(columns=["comp", "adu_main_hcd", "adu_issue_hcd"])
    d = den.set_index("geoid")
    p["sf_detached"] = p["census_geoid"].map(d["sf_detached"])
    xname = xw.drop_duplicates("census_geoid").set_index("census_geoid")["juris_name"].str.title()
    p["name"] = p["census_geoid"].map(d["name"]).fillna(p["census_geoid"].map(xname))
    p["juris_type"] = p["census_geoid"].map(geo["juris_type"])
    p["in_holdout"] = p["census_geoid"].map(geo["in_holdout"]).astype(bool)
    # a rate needs a positive denominator
    p.loc[~(p["sf_detached"] > 0), ["adu_main", "adu_issue", "adu_comp1819"]] = np.nan
    return p


# ---------------------------------------------------------------------------
# 3. Groups, event study, wave summaries, ramp, bootstrap
# ---------------------------------------------------------------------------

@dataclass
class Spec:
    """One fixed specification: outcome series, permissive cutoff, sample exclusions."""
    name: str
    measure: str = "adu_main"
    top_share: float = 0.25
    exclude: tuple[str, ...] = ()
    drop_years: tuple[int, ...] = ()
    label: str = ""


SPECS = (
    Spec("main", label="Main: compilation 2012-2017, HCD permits dated in report year 2018+; top quarter"),
    Spec("issue_year", measure="adu_issue", label="Sensitivity: HCD issue-year measure for 2018+"),
    Spec("comp_2018_2019", measure="adu_comp1819", label="Sensitivity: compilation for 2018-2019"),
    Spec("excl_2020", drop_years=(2020,), label="Robustness: 2020 excluded from post windows"),
    Spec("top_third", top_share=1 / 3, label="Robustness: permissive = top third"),
    Spec("excl_la", exclude=(LA_CITY,), label="Robustness: City of Los Angeles excluded"),
)


def series(panel: pd.DataFrame, spec: Spec, holdout: bool = False) -> pd.DataFrame:
    """Long frame census_geoid, year, adu, homes for the requested sample (observed only)."""
    p = panel[panel["in_holdout"].eq(holdout) & ~panel["census_geoid"].isin(spec.exclude)]
    s = p[["census_geoid", "year", "sf_detached"]].assign(adu=p[spec.measure]).rename(columns={"sf_detached": "homes"})
    return s


def pre_stats(s: pd.DataFrame, wave: Wave) -> pd.DataFrame:
    """Per jurisdiction: pre-period permits, rate per 1,000 homes per year, and whether every
    pre-year is observed."""
    pre = s[s["year"].isin(wave.pre)]
    g = pre.groupby("census_geoid").agg(n_obs=("adu", "count"), pre_permits=("adu", "sum"),
                                        pre_max=("adu", "max"), homes=("homes", "first"))
    g["complete"] = g["n_obs"].eq(len(wave.pre))
    g["pre_rate"] = g["pre_permits"] / (g["n_obs"] * g["homes"]) * 1000
    return g


def permissive_cutoff(pre: pd.DataFrame, top_share: float) -> float:
    """Rate at or above which a jurisdiction is in the top `top_share` of the wave's
    complete jurisdictions (ranked by pre-period rate, ties at the cut included)."""
    rates = pre.loc[pre["complete"], "pre_rate"].sort_values(ascending=False)
    k = int(np.ceil(top_share * len(rates)))
    return float(rates.iloc[k - 1]) if k > 0 else np.inf


def assign_groups(pre: pd.DataFrame, cutoff: float) -> pd.Series:
    """permissive / restrictive / middle / excluded_missing, per the pre-registered rules."""
    grp = pd.Series("middle", index=pre.index, dtype=object)
    grp[(pre["pre_rate"] >= cutoff) & (pre["pre_permits"] >= 3)] = "permissive"
    grp[pre["pre_max"].eq(0)] = "restrictive"
    grp[~pre["complete"]] = "excluded_missing"
    return grp


GROUPS = ("permissive", "middle", "restrictive")
STAT_GROUPS = GROUPS + ("all",)  # "all" = the three groups together (complete pre-period)


def pooled(s: pd.DataFrame) -> float:
    o = s.dropna(subset=["adu"])
    h = o["homes"].sum()
    return float(o["adu"].sum() / h * 1000) if h > 0 else np.nan


def unweighted(s: pd.DataFrame) -> float:
    o = s.dropna(subset=["adu"])
    return float((o["adu"] / o["homes"] * 1000).mean()) if len(o) else np.nan


def group_year(s: pd.DataFrame, grp: pd.Series, wave: Wave) -> pd.DataFrame:
    """Event-study table: per group and year, pooled (homes-weighted) and unweighted mean
    rates, each relative to the group's own pre-period mean."""
    out = []
    t = s.assign(group=s["census_geoid"].map(grp)).dropna(subset=["group"])
    for g in STAT_GROUPS:
        tg = t[t["group"].isin(GROUPS)] if g == "all" else t[t["group"].eq(g)]
        pre_p, pre_u = pooled(tg[tg["year"].isin(wave.pre)]), unweighted(tg[tg["year"].isin(wave.pre)])
        for y in YEARS:
            ty = tg[tg["year"].eq(y)]
            r_p, r_u = pooled(ty), unweighted(ty)
            out.append({"wave": wave.wave, "group": g, "year": y, "event_time": y - wave.effective,
                        "n_jurisdictions": int(ty["adu"].notna().sum()), "adu": float(ty["adu"].sum()),
                        "homes": float(ty.dropna(subset=["adu"])["homes"].sum()),
                        "rate_pooled": r_p, "rate_pooled_minus_pre": r_p - pre_p,
                        "rate_unweighted": r_u, "rate_unweighted_minus_pre": r_u - pre_u})
    return pd.DataFrame(out)


def _post(wave: Wave, drop_years: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(y for y in wave.post if y not in drop_years)


def matrices(s: pd.DataFrame, members) -> tuple[np.ndarray, np.ndarray]:
    """(adu with missing as 0, observed homes) as jurisdiction x YEARS arrays."""
    w = s[s["census_geoid"].isin(members)].pivot(index="census_geoid", columns="year", values="adu")
    w = w.reindex(index=list(members), columns=list(YEARS))
    homes = s.drop_duplicates("census_geoid").set_index("census_geoid")["homes"].reindex(list(members)).to_numpy()
    obs = w.notna().to_numpy()
    return np.nan_to_num(w.to_numpy()), obs * homes[:, None]


def _rate(num: np.ndarray, den: np.ndarray, years) -> np.ndarray:
    """Pooled rate per 1,000 over the given years; num/den are (draws x YEARS)."""
    cols = [YEARS.index(y) for y in years]
    d = den[:, cols].sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(d > 0, num[:, cols].sum(axis=1) / d * 1000, np.nan)


def stats_from_sums(sums: dict[str, tuple[np.ndarray, np.ndarray]], wave: Wave, drop_years=()) -> dict[str, np.ndarray]:
    """Wave statistics from per-group (num, den) arrays of shape (draws x YEARS)."""
    post = _post(wave, drop_years)
    r: dict[str, np.ndarray] = {}
    nan = np.full(next(iter(sums.values()))[0].shape[0], np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        for g in STAT_GROUPS:
            if g not in sums:
                for k in ("pre", "post", "change", "ratio"):
                    r[f"{g}_{k}"] = nan
                continue
            num, den = sums[g]
            r[f"{g}_pre"] = _rate(num, den, wave.pre)
            r[f"{g}_post"] = _rate(num, den, post)
            r[f"{g}_change"] = r[f"{g}_post"] - r[f"{g}_pre"]
            r[f"{g}_ratio"] = np.where(r[f"{g}_pre"] > 0, r[f"{g}_post"] / r[f"{g}_pre"], np.nan)
            if wave.wave == 3:
                r[f"{g}_plateau"] = _rate(num, den, PLATEAU_YEARS)
                r[f"{g}_plateau_ratio"] = np.where(r[f"{g}_pre"] > 0, r[f"{g}_plateau"] / r[f"{g}_pre"], np.nan)
                r[f"{g}_plateau_minus_pre"] = r[f"{g}_plateau"] - r[f"{g}_pre"]
                for k, y in enumerate(wave.post, start=1):
                    r[f"{g}_y{y}"] = _rate(num, den, (y,))
                inc = r[f"{g}_plateau"] - r[f"{g}_pre"]
                for k, y in enumerate(wave.post, start=1):
                    # increment ramp: share of the group's own pre-to-plateau rise reached in year k
                    r[f"{g}_inc_ramp_k{k}"] = np.where(inc > 0, (r[f"{g}_y{y}"] - r[f"{g}_pre"]) / inc, np.nan)
        r["did_restrictive_minus_permissive"] = r["restrictive_change"] - r["permissive_change"]
        if wave.wave == 3 and "restrictive" in sums:
            plat = r["restrictive_plateau"]
            for k, y in enumerate(wave.post, start=1):
                r[f"ramp_k{k}"] = np.where(plat > 0, r[f"restrictive_y{y}"] / plat, np.nan)
    return r


def _add_all(sums: dict) -> None:
    parts = [sums[g] for g in GROUPS if g in sums]
    sums["all"] = (sum(p[0] for p in parts), sum(p[1] for p in parts))


def _members(grp: pd.Series) -> dict[str, np.ndarray]:
    return {g: grp.index[grp.eq(g)].to_numpy() for g in GROUPS if grp.eq(g).any()}


def wave_stats(s: pd.DataFrame, grp: pd.Series, wave: Wave, drop_years=()) -> dict:
    """Point estimates for one wave on one sample."""
    sums = {}
    for g, m in _members(grp).items():
        A, H = matrices(s, m)
        sums[g] = (A.sum(axis=0)[None, :], H.sum(axis=0)[None, :])
    _add_all(sums)
    return {k: float(v[0]) for k, v in stats_from_sums(sums, wave, drop_years).items()}


def run_spec(panel: pd.DataFrame, spec: Spec) -> dict:
    """Point estimates for one specification: groups, thresholds, event study, wave stats."""
    s = series(panel, spec)
    res = {"spec": spec, "series": s, "groups": {}, "cutoffs": {}, "pre": {}, "event": [], "stats": {}}
    for w in WAVES:
        pre = pre_stats(s, w)
        cut = permissive_cutoff(pre, spec.top_share)
        grp = assign_groups(pre, cut)
        res["groups"][w.wave], res["cutoffs"][w.wave], res["pre"][w.wave] = grp, cut, pre
        ev = group_year(s, grp, w)
        if spec.drop_years:
            ev = ev[~ev["year"].isin(spec.drop_years)]
        res["event"].append(ev)
        res["stats"][w.wave] = wave_stats(s, grp, w, spec.drop_years)
    res["event"] = pd.concat(res["event"], ignore_index=True)
    return res


def bootstrap(res: dict, n_boot: int = N_BOOT, seed: int = SEED) -> dict[int, pd.DataFrame]:
    """Jurisdiction-clustered bootstrap: resample jurisdictions with replacement within each
    group (groups fixed at their pre-registered assignment), recompute wave statistics.
    Implemented with multinomial resampling weights (equivalent to drawing jurisdictions)."""
    rng = np.random.default_rng(seed)
    s = res["series"]
    out = {}
    for w in WAVES:
        sums = {}
        for g, m in _members(res["groups"][w.wave]).items():
            A, H = matrices(s, m)
            W = rng.multinomial(len(m), np.full(len(m), 1 / len(m)), size=n_boot)
            sums[g] = (W @ A, W @ H)
        _add_all(sums)
        out[w.wave] = pd.DataFrame(stats_from_sums(sums, w, res["spec"].drop_years))
    return out


def interval(draws: pd.DataFrame, key: str) -> tuple[float, float]:
    v = draws[key].replace([np.inf, -np.inf], np.nan).dropna()
    return (float(v.quantile(0.025)), float(v.quantile(0.975))) if len(v) else (np.nan, np.nan)


def group_counts(res: dict) -> pd.DataFrame:
    rows = []
    for w in WAVES:
        grp, pre = res["groups"][w.wave], res["pre"][w.wave]
        for g in GROUPS + ("excluded_missing",):
            sel = grp.eq(g)
            rows.append({"spec": res["spec"].name, "wave": w.wave, "group": g, "n_jurisdictions": int(sel.sum()),
                         "homes": float(pre.loc[sel, "homes"].sum()),
                         "pre_permits": float(pre.loc[sel, "pre_permits"].sum()),
                         "permissive_cutoff_rate": res["cutoffs"][w.wave]})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 4. Holdout test (non-holdout curve -> holdout jurisdictions)
# ---------------------------------------------------------------------------

def holdout_test(panel: pd.DataFrame, res: dict, n_boot: int = N_BOOT, seed: int = SEED):
    """Predict holdout jurisdictions' post-wave-3 rates from the non-holdout curve.

    Holdout jurisdictions get wave-3 groups from their own pre-period outcomes using the
    NON-HOLDOUT permissive cutoff. Prediction for jurisdiction j in year t = non-holdout
    pooled group rate in year t. A persistence predictor (own pre-period rate) is shown as a
    naive comparison. A predictive interval for each holdout group's pooled rate comes from
    drawing groups of the same size from the non-holdout group (seeded).

    Returns (group_level, jurisdiction_level, metrics).
    """
    spec = res["spec"]
    sh = series(panel, spec, holdout=True)
    pre_h = pre_stats(sh, WAVE3)
    grp_h = assign_groups(pre_h, res["cutoffs"][3])
    ev = res["event"]
    curve = ev[ev["wave"].eq(3)].set_index(["group", "year"])["rate_pooled"]
    st = res["stats"][3]
    t = sh[sh["year"].isin(WAVE3.post)].assign(group=sh["census_geoid"].map(grp_h))
    t = t[t["group"].isin(GROUPS)].dropna(subset=["adu"])
    t["rate"] = t["adu"] / t["homes"] * 1000
    t["pred_curve"] = [curve[(g, y)] for g, y in zip(t["group"], t["year"])]
    t["pred_persist"] = t["census_geoid"].map(pre_h["pre_rate"])
    # predictive interval for a group of the holdout's size
    rng = np.random.default_rng(seed + 3)
    s = res["series"]
    grp_n = res["groups"][3]
    glev = []
    for g in GROUPS:
        tg = t[t["group"].eq(g)]
        n_h = tg["census_geoid"].nunique()
        members = grp_n.index[grp_n.eq(g)].to_numpy()
        sim = {}
        if n_h and len(members):
            A, H = matrices(s, members)
            W = rng.multinomial(n_h, np.full(len(members), 1 / len(members)), size=n_boot)
            num, den = W @ A, W @ H
            sim = {str(y): _rate(num, den, (y,)) for y in WAVE3.post}
            sim["post"], sim["plateau"] = _rate(num, den, WAVE3.post), _rate(num, den, PLATEAU_YEARS)
        for y in list(WAVE3.post) + ["post", "plateau"]:
            if y == "post":
                ty, pred = tg, st[f"{g}_post"]
            elif y == "plateau":
                ty, pred = tg[tg["year"].isin(PLATEAU_YEARS)], st[f"{g}_plateau"]
            else:
                ty, pred = tg[tg["year"].eq(y)], curve[(g, y)]
            act = pooled(ty)
            v = sim.get(str(y))
            lo, hi = ((float(np.nanquantile(v, 0.025)), float(np.nanquantile(v, 0.975))) if v is not None else (np.nan, np.nan))
            glev.append({"group": g, "period": str(y), "n_holdout_jurisdictions": int(ty["census_geoid"].nunique()),
                         "holdout_homes": float(ty.groupby("census_geoid")["homes"].first().sum()),
                         "actual_rate": act, "predicted_rate": pred, "error": act - pred,
                         "pct_error": (act - pred) / pred if pred else np.nan,
                         "pred_interval_lo": lo, "pred_interval_hi": hi,
                         "inside_interval": bool(lo <= act <= hi) if not np.isnan(lo) else None,
                         "actual_adu": float(ty["adu"].sum()),
                         "predicted_adu": float((ty["homes"] * ty["pred_curve"] / 1000).sum())})
    glev = pd.DataFrame(glev)
    j = (t.groupby(["census_geoid", "group"])
         .agg(years=("year", "count"), homes=("homes", "first"), actual_adu=("adu", "sum"),
              pred_curve_rate=("pred_curve", "mean"), pred_persist_rate=("pred_persist", "first"))
         .reset_index())
    j["actual_rate"] = j["actual_adu"] / (j["years"] * j["homes"]) * 1000
    j["pred_curve_adu"] = (t.assign(x=t["homes"] * t["pred_curve"] / 1000).groupby("census_geoid")["x"].sum()
                           .reindex(j["census_geoid"]).to_numpy())
    j["pred_persist_adu"] = j["pred_persist_rate"] * j["years"] * j["homes"] / 1000
    j["error_rate"] = j["actual_rate"] - j["pred_curve_rate"]
    j["error_adu"] = j["actual_adu"] - j["pred_curve_adu"]
    j["name"] = j["census_geoid"].map(panel.drop_duplicates("census_geoid").set_index("census_geoid")["name"])
    j["pre_rate"] = j["census_geoid"].map(pre_h["pre_rate"])
    mets = []
    for g in GROUPS + ("all",):
        jj = j if g == "all" else j[j["group"].eq(g)]
        if not len(jj):
            continue
        w = jj["homes"] / jj["homes"].sum()
        for pred in ("curve", "persist"):
            e = jj["actual_rate"] - jj[f"pred_{pred}_rate"]
            mets.append({"group": g, "predictor": pred, "n_jurisdictions": len(jj),
                         "mae_rate": float(e.abs().mean()), "rmse_rate": float(np.sqrt((e ** 2).mean())),
                         "median_abs_error_rate": float(e.abs().median()),
                         "homes_weighted_mae_rate": float((w * e.abs()).sum()), "mean_error_rate": float(e.mean()),
                         "actual_adu": float(jj["actual_adu"].sum()), "predicted_adu": float(jj[f"pred_{pred}_adu"].sum()),
                         "total_pct_error": float(jj["actual_adu"].sum() / jj[f"pred_{pred}_adu"].sum() - 1)
                         if jj[f"pred_{pred}_adu"].sum() else np.nan})
    excl = grp_h.value_counts().to_dict()
    return glev, j.sort_values("error_adu", key=abs, ascending=False), pd.DataFrame(mets), excl


# ---------------------------------------------------------------------------
# 5. ADU-share model
# ---------------------------------------------------------------------------

def bps_by_jurisdiction(bps_map: pd.DataFrame) -> pd.DataFrame:
    """bps_map: ca_step0.bps_to_jurisdiction output. Returns census_geoid, year, bps_total,
    bps_1unit, bps_months_min."""
    return (bps_map[bps_map["known"]].groupby(["census_geoid", "year"])
            .agg(bps_total=("units_total", "sum"), bps_1unit=("1unit_units", "sum"),
                 bps_months_min=("months_reported", "min")).reset_index())


def share_model(panel: pd.DataFrame, bps: pd.DataFrame, xw: pd.DataFrame, measure: str = "adu_main") -> pd.DataFrame:
    """Per year 2012-2025, non-holdout jurisdiction-years with the ADU outcome observed and a
    BPS row with >0 months, excluding county remainders whose BPS may include cities (S6).
    share(s) = A / (B + (1 - s) A), with A = ADU-type second homes, B = BPS total units,
    s = share of ADUs already inside BPS (not identified; 0 to 0.5)."""
    excl = set(xw.loc[xw["bps_may_include_cities"].astype(bool), "census_geoid"])
    p = panel[~panel["in_holdout"] & ~panel["census_geoid"].isin(excl)].merge(bps, on=["census_geoid", "year"], how="inner")
    p = p[p[measure].notna() & p["bps_months_min"].gt(0)]
    a = p.groupby("year").agg(n_jurisdictions=("census_geoid", "nunique"), adu=(measure, "sum"),
                              bps_total=("bps_total", "sum"), bps_1unit=("bps_1unit", "sum"),
                              homes=("sf_detached", "sum")).reset_index()
    periods = {"pre_2014_2016": (2014, 2015, 2016), "wave1_2017": (2017,), "wave2_2018_2019": (2018, 2019),
               "wave3_2020_2022": (2020, 2021, 2022), "wave3_plateau_2023_2025": PLATEAU_YEARS,
               "wave3_2020_2025": WAVE3.post}
    rows = [dict(period=str(r.year), **{k: getattr(r, k) for k in ("n_jurisdictions", "adu", "bps_total", "bps_1unit", "homes")})
            for r in a.itertuples()]
    for name, ys in periods.items():
        q = a[a["year"].isin(ys)]
        rows.append(dict(period=name, n_jurisdictions=int(q["n_jurisdictions"].mean()) if len(q) else 0, adu=q["adu"].sum() / len(ys),
                         bps_total=q["bps_total"].sum() / len(ys), bps_1unit=q["bps_1unit"].sum() / len(ys),
                         homes=q["homes"].mean()))
    out = pd.DataFrame(rows)
    for s_ in OVERLAP_S:
        out[f"share_s{s_:.2f}"] = out["adu"] / (out["bps_total"] + (1 - s_) * out["adu"])
    out["adu_per_1000_homes"] = out["adu"] / out["homes"] * 1000
    out["measure"] = measure
    return out


def wi_share_volume(ca: pd.Series, wi_bps_total: float, wi_homes: float) -> pd.DataFrame:
    """Wisconsin ADU-type volume implied by the California share, over the unidentified
    ADU-in-BPS overlap in each state (s_ca, s_wi each in OVERLAP_S).

    ca: one share_model row (adu, bps_total). share = A / (B + (1 - s_ca) A) in California;
    Wisconsin: A_WI = share * B_WI / (1 - share * (1 - s_wi)). With s_ca == s_wi this reduces
    to A_WI = B_WI * A_CA / B_CA, so the overlap only matters where the states differ."""
    rows = []
    for s_ca in OVERLAP_S:
        share = ca["adu"] / (ca["bps_total"] + (1 - s_ca) * ca["adu"])
        for s_wi in OVERLAP_S:
            a = share * wi_bps_total / (1 - share * (1 - s_wi))
            rows.append({"overlap_s_ca": s_ca, "overlap_s_wi": s_wi, "ca_share": share, "wi_bps_total": wi_bps_total,
                         "wi_adu_per_year": a, "wi_adu_per_1000_homes": a / wi_homes * 1000})
    return pd.DataFrame(rows)


def share_bootstrap(panel: pd.DataFrame, bps: pd.DataFrame, xw: pd.DataFrame, measure: str = "adu_main",
                    periods: dict[str, tuple[int, ...]] | None = None, n_boot: int = N_BOOT,
                    seed: int = SEED) -> pd.DataFrame:
    """Jurisdiction-clustered bootstrap of the ADU-to-BPS ratio A/B per period (the share
    model's input) on the same sample as share_model."""
    periods = periods or {"pre_2014_2016": (2014, 2015, 2016), "wave3_plateau_2023_2025": PLATEAU_YEARS}
    excl = set(xw.loc[xw["bps_may_include_cities"].astype(bool), "census_geoid"])
    p = panel[~panel["in_holdout"] & ~panel["census_geoid"].isin(excl)].merge(bps, on=["census_geoid", "year"], how="inner")
    p = p[p[measure].notna() & p["bps_months_min"].gt(0)]
    geos = np.array(sorted(p["census_geoid"].unique()))
    A = p.pivot(index="census_geoid", columns="year", values=measure).reindex(index=geos, columns=list(YEARS)).fillna(0).to_numpy()
    B = p.pivot(index="census_geoid", columns="year", values="bps_total").reindex(index=geos, columns=list(YEARS)).fillna(0).to_numpy()
    rng = np.random.default_rng(seed + 5)
    W = rng.multinomial(len(geos), np.full(len(geos), 1 / len(geos)), size=n_boot)
    rows = []
    for name, ys in periods.items():
        cols = [YEARS.index(y) for y in ys]
        a, b = (W @ A[:, cols]).sum(axis=1), (W @ B[:, cols]).sum(axis=1)
        ratio = a / b
        rows.append({"measure": measure, "period": name, "adu_to_bps": A[:, cols].sum() / B[:, cols].sum(),
                     "ci95_lo": float(np.quantile(ratio, 0.025)), "ci95_hi": float(np.quantile(ratio, 0.975))})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 6. Results document (every number is read from the outputs)
# ---------------------------------------------------------------------------

def _f(x, d=2) -> str:
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:,.{d}f}"


def _ci(est, lo, hi, d=2) -> str:
    return f"{_f(est, d)} [{_f(lo, d)} to {_f(hi, d)}]"


def _pct(x, d=0) -> str:
    return "—" if not np.isfinite(x) else f"{x * 100:+.{d}f}%"


def _table(header: list[str], rows: list[list[str]], align: str | None = None) -> str:
    align = align or ("l" + "r" * (len(header) - 1))
    sep = ["---" if a == "l" else "---:" for a in align]
    return "\n".join(["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
                     + ["| " + " | ".join(r) + " |" for r in rows])


def load_outputs(ref, study) -> dict:
    from pathlib import Path
    ref, study = Path(ref), Path(study)
    o = {k: pd.read_csv(ref / f"ca_study_{k}.csv") for k in
         ("event_study", "groups", "wave_stats", "text_exclusions", "share_model", "share_bootstrap",
          "wi_share_volume", "holdout_group", "holdout_metrics")}
    o["holdout_j"] = pd.read_csv(study / "holdout_jurisdictions.csv", dtype={"census_geoid": str})
    o["groups_j"] = pd.read_csv(study / "groups_by_jurisdiction.csv", dtype={"census_geoid": str})
    import json
    o["holdout_counts"] = json.loads((study / "holdout_groups.json").read_text())
    o["wi_bps"] = pd.read_csv(ref / "ca_wi_statewide_bps_per_1000.csv")
    o["wi_context"] = pd.read_csv(ref / "ca_study_wi_context.csv")
    return o


def render_doc(o: dict) -> str:
    st = o["wave_stats"]

    def S_(stat, wave=3, spec="main"):
        r = st[(st["spec"] == spec) & (st["wave"] == wave) & (st["statistic"] == stat)]
        if not len(r):
            return (np.nan, np.nan, np.nan)
        r = r.iloc[0]
        return (float(r["estimate"]), float(r["ci95_lo"]), float(r["ci95_hi"]))

    def C(stat, wave=3, spec="main", d=2):
        return _ci(*S_(stat, wave, spec), d=d)

    def E(stat, wave=3, spec="main"):
        return S_(stat, wave, spec)[0]

    ev = o["event_study"]
    grp = o["groups"]
    gj = o["groups_j"]
    hg, hm, hj = o["holdout_group"], o["holdout_metrics"], o["holdout_j"]
    sh, sb, wv = o["share_model"], o["share_bootstrap"], o["wi_share_volume"]
    exc = o["text_exclusions"]
    wi = o["wi_bps"][o["wi_bps"]["state"].eq("Wisconsin")]
    wi_bps = float(wi[wi["year"].isin(PLATEAU_YEARS)]["units_total"].mean())
    wi_homes = float(wv["wi_homes"].iloc[0])
    sbm = sb[(sb["measure"] == "adu_main") & (sb["period"] == "wave3_plateau_2023_2025")].iloc[0]
    wi_mid = sbm["adu_to_bps"] * wi_bps / wi_homes * 1000
    wi_lo, wi_hi = sbm["ci95_lo"] * wi_bps / wi_homes * 1000, sbm["ci95_hi"] * wi_bps / wi_homes * 1000
    wvm = wv[(wv["measure"] == "adu_main") & (wv["ca_period"] == "wave3_plateau_2023_2025")]
    wv_min, wv_max = wvm["wi_adu_per_1000_homes"].min(), wvm["wi_adu_per_1000_homes"].max()
    hall = hm[(hm["group"] == "all") & (hm["predictor"] == "curve")].iloc[0]
    hper = hm[(hm["group"] == "all") & (hm["predictor"] == "persist")].iloc[0]
    hin = hg[hg["period"].isin([str(y) for y in WAVE3.post])]
    n_in, n_cells = int(hin["inside_interval"].astype(bool).sum()), len(hin)
    gm = grp[(grp["spec"] == "main")]

    def gcount(wave, g, col="n_jurisdictions"):
        return gm[(gm["wave"] == wave) & (gm["group"] == g)][col].iloc[0]

    med = gj[gj["spec"].eq("main")].groupby(["wave", "group"])["homes"].median()
    L: list[str] = []
    A = L.append
    A("# California comparison study: results")
    A("")
    A("Gate 3, work package A. Runs the pre-registered plan [CA_COMPARISON_PLAN.md](CA_COMPARISON_PLAN.md) "
      "(approved by the owner as G2-8) on the Gate 2 inputs ([CA_COMPARISON_DATA.md](../gate2/CA_COMPARISON_DATA.md)). "
      "This file is generated by `scripts/run_ca_study.py` from its outputs; `--check-doc` fails if it differs. "
      "**All results are descriptive comparisons around the statewide reform waves.** Groups are defined from "
      "pre-period outcomes and there is no untreated comparison state, so differences are *associated with* the "
      "waves; they are not estimates of causal effects. Every number that could feed the Wisconsin model is "
      "computed on non-holdout jurisdictions only; holdout jurisdictions are used once, in the hold-out test below, "
      "and no all-data refit has been done.")
    A("")
    A("## Plain-language summary")
    A("")
    A(f"- **Places that had no ADUs before 2020 started producing them after the 2020 state laws.** The "
      f"{gcount(3, 'restrictive')} non-holdout jurisdictions with zero ADU permits in every year 2017–2019 "
      f"(mostly small places, median {_f(med[(3, 'restrictive')], 0)} one-unit detached homes) reached "
      f"**{C('restrictive_plateau')} ADU-type second homes per 1,000 one-unit detached homes a year** in 2023–2025 "
      f"(jurisdiction-clustered bootstrap 95% interval in brackets).")
    A(f"- **They ramped up over about four years:** {_f(E('ramp_k1') * 100, 0)}% of that 2023–2025 level in 2020, "
      f"{_f(E('ramp_k2') * 100, 0)}% in 2021, {_f(E('ramp_k3') * 100, 0)}% in 2022 and {_f(E('ramp_k4') * 100, 0)}% in "
      f"2023; the rate was still rising in 2025, so the \"plateau\" is the pre-registered 2023–2025 average, not a "
      f"demonstrated ceiling.")
    A(f"- **Already-permissive places also rose (spillover).** The top quarter by 2017–2019 rate went from "
      f"{_f(E('permissive_pre'))} to {_f(E('permissive_plateau'))} per 1,000 (×{C('permissive_plateau_ratio')}). "
      f"Without the City of Los Angeles the permissive group went from {_f(E('permissive_pre', spec='excl_la'))} to "
      f"{_f(E('permissive_plateau', spec='excl_la'))} (×{_f(E('permissive_plateau_ratio', spec='excl_la'))}). "
      f"The middle group went from {_f(E('middle_pre'))} to {_f(E('middle_plateau'))}.")
    A(f"- **Across all grouped non-holdout jurisdictions** the rate went from {_f(E('all_pre', wave=1))} a year in "
      f"2014–2016 to {_f(E('all_pre'))} in 2017–2019 and {C('all_plateau')} in 2023–2025.")
    A(f"- **The owner's ADU-share model:** ADU-type second homes went from about 1% of new units (BPS total plus ADUs "
      f"outside BPS) in 2014–2016 to {_f(sh[(sh.measure == 'adu_main') & (sh.period == 'wave3_plateau_2023_2025')]['share_s0.00'].iloc[0] * 100, 0)}–"
      f"{_f(sh[(sh.measure == 'adu_main') & (sh.period == 'wave3_plateau_2023_2025')]['share_s0.50'].iloc[0] * 100, 0)}% in "
      f"2023–2025 (the range is the unidentified share of ADUs already inside BPS, 0 to 0.5). Applied to Wisconsin's "
      f"2023–2025 BPS totals it implies about {_f(wi_mid)} ADU-type second homes per 1,000 Wisconsin one-unit detached "
      f"homes a year (bootstrap {_f(wi_lo)}–{_f(wi_hi)}; {_f(wv_min)}–{_f(wv_max)} if the overlap differs between the states).")
    A(f"- **The hold-out test matched at the group level.** Using only the non-holdout curve, the "
      f"{int(hall['n_jurisdictions'])} grouped holdout jurisdictions' 2020–2025 ADUs were predicted at "
      f"{_f(hall['predicted_adu'], 0)} against {_f(hall['actual_adu'], 0)} observed ({_pct(hall['total_pct_error'])}); "
      f"{n_in} of {n_cells} group-year rates fell inside the (wide) predictive interval. Individual places miss by much more "
      f"(median absolute error {_f(hall['median_abs_error_rate'])} per 1,000 a year).")
    A(f"- **Candidate Wisconsin inputs (not adopted):** central `y` ≈ {_f(E('restrictive_plateau'))} per 1,000 "
      f"(restrictive-group plateau); upper `y` ≈ {_f(E('all_plateau'))} (all-group plateau) or {_f(wi_mid)} (share model); "
      f"ramp ≈ {', '.join(_f(E(f'ramp_k{k}'), 2) for k in range(1, 5))} of plateau in years 1–4; spillover "
      f"multiplier for already-permissive places ≈ ×{_f(E('permissive_plateau_ratio'), 1)} "
      f"(×{_f(E('permissive_plateau_ratio', spec='excl_la'), 1)} without Los Angeles). California has higher rents and "
      f"land values and a longer reform history; these transfer to Wisconsin only as stated assumptions.")
    A("")
    # ---------------- outcome
    A("## 1. Outcome and sources (as pre-registered)")
    A("")
    A("**Outcome:** ADU-type second homes permitted per 1,000 one-unit detached homes (ACS 2020–2024, B25024_002) per year, "
      "by jurisdiction (incorporated cities, San Francisco, and county unincorporated remainders).")
    A("")
    A(_table(["Years", "Main series", "Sensitivity A: issue-year", "Sensitivity B: compilation 2018–2019"], [
        ["2012–2017", "2012–2019 compilation (HCD-attributed, as reported)", "same", "same"],
        ["2018–2019", "HCD APR A2, permits dated in the report year (step 0 primary)", "HCD, each permit once in its issue year", "compilation"],
        ["2020–2025", "HCD APR A2, permits dated in the report year", "HCD, issue year", "HCD primary"],
    ], "llll"))
    A("")
    A("- **Missing is not zero.** An HCD year counts as observed only if the jurisdiction filed Table A2 rows that year; "
      "\"filed, no A2 rows\" and \"no record\" are missing. Jurisdictions missing any pre-period year are excluded from that wave.")
    A("- **Exclusions from HCD ADU permits (2018+),** by fixed keyword rules on the free-text notes and project name, read in "
      "memory only (`TEXT_RULES` in `ca_study.py`): legalizations (\"legalize\", \"unpermitted\", \"as-built\", code-enforcement "
      "abatement), ADUs built with a new house, and ADUs on multifamily lots. A permit is excluded if any of its listings matches. "
      "Junior ADUs are kept. Most records carry no usable text, so these are minimum exclusions; the remainder is a known overcount. "
      "The 2012–2017 compilation cannot be screened.")
    A("")
    rows = [[str(int(r.year)), _f(r.kept + r.legalization + r.new_house + r.multifamily_lot, 0), _f(r.legalization, 0),
             _f(r.new_house, 0), _f(r.multifamily_lot, 0), _f(r.kept, 0),
             _f((r.legalization + r.new_house + r.multifamily_lot) / (r.kept + r.legalization + r.new_house + r.multifamily_lot) * 100, 1) + "%"]
            for r in exc.itertuples()]
    A(_table(["Year (all jurisdictions, main measure)", "HCD ADU permits", "Legalization", "With new house", "Multifamily lot", "Kept", "Excluded"], rows))
    A("")
    # ---------------- groups
    A("## 2. Groups per wave (non-holdout jurisdictions)")
    A("")
    A("Permissive = top quarter of the wave's pre-period rate with at least 3 permits in the pre-period; restrictive = zero permits "
      "in every pre-period year; middle = the rest; jurisdictions with a missing pre-period year are excluded from that wave.")
    A("")
    rows = []
    for w in WAVES:
        for g in GROUPS + ("excluded_missing",):
            r = gm[(gm["wave"] == w.wave) & (gm["group"] == g)].iloc[0]
            rows.append([f"{w.wave} ({w.pre[0]}–{w.pre[-1]})", g, _f(r["n_jurisdictions"], 0), _f(r["homes"], 0),
                         _f(med.get((w.wave, g), np.nan), 0), _f(r["pre_permits"], 0),
                         _f(r["permissive_cutoff_rate"], 3)])
    A(_table(["Wave (pre-period)", "Group", "Jurisdictions", "One-unit detached homes", "Median homes", "Pre-period permits",
              "Permissive cutoff (per 1,000 / yr)"], rows, "llrrrrr"))
    A("")
    A("Waves 1 and 2 share the 2014–2016 pre-period, so their groups are identical. The Los Angeles city is in the permissive "
      f"group in every wave; in wave 3 it holds {_f(float(gj[(gj.spec == 'main') & (gj.wave == 3) & (gj.census_geoid == LA_CITY)]['homes'].iloc[0]) / gcount(3, 'permissive', 'homes') * 100, 0)}% of the permissive "
      "group's homes, which is why the Los Angeles-excluded check matters.")
    A("")
    # ---------------- event study
    A("## 3. Event-study tables")
    A("")
    A("Group rate per 1,000 one-unit detached homes per year, homes-weighted (total permits ÷ total homes of the group's "
      "jurisdictions observed that year), with the change from the group's own pre-period mean in parentheses. The unweighted "
      "mean of jurisdiction rates is in `reference/ca_study_event_study.csv`.")
    A("")
    for w in (WAVES[0], WAVE3):
        e = ev[(ev["spec"] == "main") & (ev["wave"] == w.wave)]
        label = "Waves 1–2 groups (pre-period 2014–2016)" if w.wave == 1 else "Wave 3 groups (pre-period 2017–2019)"
        A(f"**{label}**")
        A("")
        rows = []
        for y in YEARS:
            cells = [str(y)]
            for g in STAT_GROUPS:
                r = e[(e["group"] == g) & (e["year"] == y)].iloc[0]
                cells.append(f"{_f(r['rate_pooled'])} ({r['rate_pooled_minus_pre']:+.2f})")
            cells.append(" / ".join(str(int(e[(e['group'] == g) & (e['year'] == y)]['n_jurisdictions'].iloc[0])) for g in GROUPS))
            rows.append(cells)
        A(_table(["Year", "Permissive", "Middle", "Restrictive", "All grouped", "N (P / M / R)"], rows))
        A("")
    # ---------------- wave summaries
    A("## 4. Differences-in-differences per wave")
    A("")
    A("Change = group rate in the post window minus its pre-period rate (per 1,000 homes per year). DiD = restrictive change minus "
      "permissive change. 95% intervals from a jurisdiction-clustered bootstrap (2,000 draws, resampling jurisdictions within "
      "each group, seed 20261024).")
    A("")
    rows = []
    for w in WAVES:
        post = f"{w.post[0]}–{w.post[-1]}" if len(w.post) > 1 else str(w.post[0])
        rows.append([f"{w.wave} (pre {w.pre[0]}–{w.pre[-1]}, post {post})",
                     C("permissive_pre", w.wave), C("permissive_change", w.wave), C("middle_change", w.wave),
                     C("restrictive_change", w.wave), C("did_restrictive_minus_permissive", w.wave)])
    A(_table(["Wave", "Permissive pre", "Permissive change", "Middle change", "Restrictive change", "DiD (R − P)"], rows, "lrrrrr"))
    A("")
    A("Reading: in every wave the permissive group's absolute rise was larger than the restrictive group's, so the DiD is "
      "negative. This does not show that restrictive places responded less: already-active markets added more permits per home "
      "in absolute terms, and the restrictive group's rise is from zero. The groups are selected on pre-period outcomes, so some regression toward the mean is "
      "built in (permissive places selected on high values tend to fall back, restrictive places selected on zeros can only rise); "
      "this biases the DiD toward zero from the restrictive side and away from zero on the permissive side, and is a further "
      "reason to read it descriptively. Wave 1 and wave 2 share a clock and a pre-period, so wave 2 is cumulative from 2014–2016. "
      f"Without the City of Los Angeles the DiD is {_f(E('did_restrictive_minus_permissive', 1, 'excl_la'))} in wave 1, "
      f"{_f(E('did_restrictive_minus_permissive', 2, 'excl_la'))} in wave 2 and {_f(E('did_restrictive_minus_permissive', 3, 'excl_la'))} "
      "in wave 3: Los Angeles accounts for most of the permissive group's early rise.")
    A("")
    # ---------------- plateau & spillover
    A("## 5. Wave 3: plateau levels and spillover")
    A("")
    rows = []
    for g in STAT_GROUPS:
        rows.append([g, C(f"{g}_pre"), C(f"{g}_post"), C(f"{g}_plateau"), C(f"{g}_plateau_minus_pre"),
                     C(f"{g}_plateau_ratio") if g != "restrictive" else "— (pre = 0)"])
    A(_table(["Group", "Pre 2017–2019", "Post 2020–2025", "Plateau 2023–2025", "Plateau − pre", "Plateau ÷ pre"], rows, "lrrrrr"))
    A("")
    A(f"**Spillover** (plan: the permissive group's own post-wave-3 change): +{C('permissive_change')} per 1,000 over 2020–2025 and "
      f"+{C('permissive_plateau_minus_pre')} at the 2023–2025 plateau; plateau ÷ pre ×{C('permissive_plateau_ratio')}. "
      f"Wave 1 (shared clock) shows the same direction: +{C('permissive_change', 1)}. Note that the wave-3 pre-period "
      "(2017–2019) is already after waves 1 and 2, so this is the rise associated with the 2020 package on top of the earlier laws.")
    A("")
    # ---------------- ramp
    A("## 6. Ramp after wave 3")
    A("")
    A("Plan definition: the restrictive group's year-k level as a share of its year-4-to-6 plateau, counting 2020 as year 1 "
      "(plateau = 2023–2025). Because the restrictive pre-period rate is zero, this equals the share of the group's own rise. "
      "For comparison, the same increment share (level − pre) ÷ (plateau − pre) is shown for the other groups.")
    A("")
    rows = []
    for k, y in enumerate(WAVE3.post, start=1):
        rows.append([f"{k} ({y})", C(f"restrictive_y{y}"), C(f"ramp_k{k}"), C(f"middle_inc_ramp_k{k}"),
                     C(f"permissive_inc_ramp_k{k}"), C(f"all_inc_ramp_k{k}")])
    A(_table(["Year k", "Restrictive rate", "Restrictive ramp (plan)", "Middle, increment share", "Permissive, increment share",
              "All grouped, increment share"], rows, "lrrrrr"))
    A("")
    # ---------------- robustness
    A("## 7. Fixed sensitivities and robustness checks")
    A("")
    A("All pre-registered; none chosen after seeing results. Point estimates, per 1,000 one-unit detached homes per year.")
    A("")
    specs = [s.name for s in SPECS]
    keys = [("restrictive_plateau", 3, "Restrictive plateau (W3)"), ("middle_plateau", 3, "Middle plateau (W3)"),
            ("permissive_pre", 3, "Permissive pre (W3)"), ("permissive_plateau", 3, "Permissive plateau (W3)"),
            ("permissive_change", 3, "Permissive change 2020–25 (spillover)"), ("permissive_plateau_ratio", 3, "Permissive plateau ÷ pre"),
            ("restrictive_change", 3, "Restrictive change 2020–25"), ("did_restrictive_minus_permissive", 3, "DiD wave 3"),
            ("did_restrictive_minus_permissive", 2, "DiD wave 2"), ("did_restrictive_minus_permissive", 1, "DiD wave 1"),
            ("ramp_k1", 3, "Ramp year 1"), ("ramp_k2", 3, "Ramp year 2"), ("ramp_k3", 3, "Ramp year 3"), ("ramp_k4", 3, "Ramp year 4"),
            ("all_plateau", 3, "All-group plateau (W3)")]
    rows = [[lab] + [_f(E(k, w, sp)) for sp in specs] for k, w, lab in keys]
    rows.append(["Restrictive / permissive jurisdictions (W3)"] +
                [f"{int(grp[(grp.spec == sp) & (grp.wave == 3) & (grp.group == 'restrictive')]['n_jurisdictions'].iloc[0])} / "
                 f"{int(grp[(grp.spec == sp) & (grp.wave == 3) & (grp.group == 'permissive')]['n_jurisdictions'].iloc[0])}" for sp in specs])
    A(_table(["Statistic"] + specs, rows))
    A("")
    A("- `main`: compilation 2012–2017 and HCD permits dated in the report year from 2018; top quarter. `issue_year`: HCD issue-year "
      "measure for 2018+. `comp_2018_2019`: compilation for 2018–2019 (it has no missing years, so fewer jurisdictions drop out of "
      "wave 3 and more qualify as restrictive). `excl_2020`: 2020 dropped from post windows (plateau unaffected). `top_third`: "
      "permissive cutoff at the top third. `excl_la`: City of Los Angeles removed before grouping. Intervals for every specification "
      "are in `reference/ca_study_wave_stats.csv`.")
    A("")
    # ---------------- share model
    A("## 8. The owner's ADU-share model")
    A("")
    A("Share = ADU-type second homes ÷ (BPS total units + ADUs not in BPS) = A ÷ (B + (1 − s)·A), where s is the share of HCD "
      "ADUs already counted in BPS one-unit permits. **Step 0 found s not identified** (plausibly 0 to 0.5, place-specific), so the "
      "share is shown at s = 0, 0.25 and 0.5. Sample: non-holdout jurisdiction-years with the ADU outcome observed and a BPS row; "
      "county remainders whose BPS may include contract-permitted cities (step 0, S6) are excluded.")
    A("")
    rows = []
    for _, r in sh[sh["measure"] == "adu_main"].iterrows():
        rows.append([r["period"], str(int(r["n_jurisdictions"])), _f(r["adu"], 0), _f(r["bps_total"], 0)]
                    + [_f(r[f"share_s{s_:.2f}"] * 100, 1) + "%" for s_ in OVERLAP_S] + [_f(r["adu_per_1000_homes"])])
    A(_table(["Year or period (avg / yr)", "Jurisdictions", "ADU-type (A)", "BPS total (B)", "Share, s = 0", "s = 0.25", "s = 0.5",
              "A per 1,000 homes"], rows))
    A("")
    sbi = sb[sb["measure"] == "adu_main"].set_index("period")
    A(f"A ÷ B (the input the share model actually transfers, since s cancels if it is the same in both states): "
      f"{_ci(sbi.loc['pre_2014_2016', 'adu_to_bps'], sbi.loc['pre_2014_2016', 'ci95_lo'], sbi.loc['pre_2014_2016', 'ci95_hi'], 3)} in 2014–2016 and "
      f"{_ci(sbi.loc['wave3_plateau_2023_2025', 'adu_to_bps'], sbi.loc['wave3_plateau_2023_2025', 'ci95_lo'], sbi.loc['wave3_plateau_2023_2025', 'ci95_hi'], 3)} "
      "in 2023–2025 (jurisdiction-clustered bootstrap). The issue-year sensitivity is in `reference/ca_study_share_model.csv`.")
    A("")
    # ---------------- holdout
    A("## 9. Hold-out test (published before any all-data refit; none is done)")
    A("")
    hc = o["holdout_counts"]
    A(f"The {sum(hc.values())} holdout jurisdictions with data were grouped from their own 2017–2019 outcomes using the non-holdout "
      f"permissive cutoff ({_f(gm[gm.wave == 3]['permissive_cutoff_rate'].iloc[0], 3)} per 1,000): {hc.get('permissive', 0)} permissive, "
      f"{hc.get('middle', 0)} middle, {hc.get('restrictive', 0)} restrictive, {hc.get('excluded_missing', 0)} excluded for a missing "
      "pre-period year. Each jurisdiction's predicted rate in year t is the non-holdout group's rate in year t (main specification). "
      "The predictive interval is the 2.5–97.5 percentile of the pooled rate of random groups of the same size drawn from the "
      "non-holdout group. A naive persistence predictor (each place keeps its own 2017–2019 rate) is shown for comparison.")
    A("")
    rows = []
    for r in hg[hg["period"].isin(["post", "plateau"])].itertuples():
        rows.append([r.group, "2020–2025" if r.period == "post" else "2023–2025", str(r.n_holdout_jurisdictions), _f(r.actual_rate),
                     _f(r.predicted_rate), f"{_f(r.pred_interval_lo)}–{_f(r.pred_interval_hi)}", _pct(r.pct_error),
                     "yes" if r.inside_interval else "no"])
    A(_table(["Group", "Period", "Holdout jurisdictions", "Actual rate", "Predicted", "Predictive interval", "Error", "Inside"], rows, "llrrrrrl"))
    A("")
    A(f"Year by year (`reference/ca_study_holdout_group.csv`), {n_in} of {n_cells} group-year rates fall inside their interval; the "
      f"largest group-year miss is {hin.loc[hin['pct_error'].abs().idxmax(), 'group']} in {hin.loc[hin['pct_error'].abs().idxmax(), 'period']} "
      f"({_pct(hin['pct_error'].abs().max() * np.sign(hin.loc[hin['pct_error'].abs().idxmax(), 'pct_error']))}).")
    A("")
    rows = []
    for r in hm.itertuples():
        rows.append([r.group, r.predictor, str(r.n_jurisdictions), _f(r.mae_rate), _f(r.rmse_rate), _f(r.median_abs_error_rate),
                     _f(r.mean_error_rate), _f(r.actual_adu, 0), _f(r.predicted_adu, 0), _pct(r.total_pct_error)])
    A(_table(["Group", "Predictor", "N", "MAE", "RMSE", "Median abs. error", "Mean error (actual − pred.)", "Actual ADUs 2020–25",
              "Predicted", "Total error"], rows, "llrrrrrrrr"))
    A("")
    A("Jurisdiction-level errors are per 1,000 homes per year over 2020–2025. **Largest misses** by permits (actual − predicted, 2020–2025):")
    A("")
    rows = [[str(r.name) if isinstance(r.name, str) else r.census_geoid, r.group, _f(r.homes, 0), _f(r.pre_rate), _f(r.actual_rate),
             _f(r.pred_curve_rate), f"{r.error_adu:+,.0f}"] for r in hj.head(10).itertuples()]
    A(_table(["Holdout jurisdiction", "Group", "Homes", "Pre rate", "Actual rate", "Predicted", "Permit error"], rows, "llrrrrr"))
    A("")
    A("Reading: the group curve predicts group totals well and beats persistence, but it predicts individual places poorly; the "
      "spread within groups is large (some permissive places stayed near their pre-period rate, some middle places surged). "
      "For Wisconsin this supports using the curve for statewide or group totals, not for single-municipality forecasts.")
    A("")
    # ---------------- Wisconsin translation
    A("## 10. Candidate Wisconsin inputs (not adopted)")
    A("")
    A("Candidates for the conductor and owner. None is adopted here. Rates are ADU-type second homes per 1,000 one-unit detached homes per year.")
    A("")
    rows = [
        ["Central `y`", "Restrictive-group plateau, 2023–2025", C("restrictive_plateau"),
         f"Range over fixed sensitivities {_f(min(E('restrictive_plateau', 3, s) for s in specs))}–{_f(max(E('restrictive_plateau', 3, s) for s in specs))}. Places that started at zero, the closest analog to Wisconsin places that move from no ADU rights to the benchmark."],
        ["Central `y` (alternative)", "Middle-group plateau", C("middle_plateau"), "Places with some pre-2020 ADU activity; includes their earlier momentum."],
        ["Upper `y`", "All grouped jurisdictions, plateau", C("all_plateau"), f"Statewide-like level; {_f(E('all_plateau', spec='excl_la'))} without Los Angeles."],
        ["Upper `y` (share model)", "A ÷ B (2023–2025) × Wisconsin BPS total 2023–2025 ÷ WI homes", _ci(wi_mid, wi_lo, wi_hi),
         f"Wisconsin BPS total {_f(wi_bps, 0)} units a year; {_f(wi_homes, 0)} one-unit detached homes (ACS 2020–2024). {_f(wv_min)}–{_f(wv_max)} if the ADU-in-BPS overlap differs between states (0 vs 0.5)."],
        ["Not a statewide `y`", "Permissive-group plateau", C("permissive_plateau"), f"Selected on the strongest pre-2020 markets; {_f(E('permissive_plateau', spec='excl_la'))} without Los Angeles."],
    ]
    A(_table(["Input", "Source", "Value [95% interval]", "Note"], rows, "llrl"))
    A("")
    ctx = o["wi_context"].set_index("item")["value"]
    A(f"**Comparison points (context, not inputs from this study).** Owner prior (AQ-031): well under 0.1 for prohibited places "
      f"and somewhat above 2 for benchmark-law places. California before the 2017 law: {_f(E('all_pre', wave=1))} across grouped "
      f"jurisdictions (2014–2016). Madison, ADU-type components (detached, attached, conversion, two-unit) 2022–2025: "
      f"{_f(ctx['madison_adu_type_per_year'], 2)} a year on {_f(ctx['madison_homes'], 0)} one-unit detached homes = "
      f"{_f(ctx['madison_rate'])} per 1,000, or {_f(ctx['madison_rate_div_0_8'])} after ÷ 0.8 (AQ-030; computed here from "
      "`reference/madison_adu_permits_by_year.csv` for comparison only; the Madison floor itself belongs to another work package). "
      "Every California candidate is several times Madison's floor.")
    A("")
    rk = lambda key: ", ".join(_f(E(f"{key}{k}")) for k in range(1, 7))
    A("**Ramp shapes per path** (share of plateau reached in years 1–6 after the law takes effect):")
    A("")
    A(_table(["Path", "Candidate", "Years 1–6", "Basis"], [
        ["Central", "Restrictive group (plan definition)", rk("ramp_k"), "Places starting from zero."],
        ["Upper (faster, as the data show)", "Middle-group increment share", rk("middle_inc_ramp_k"),
         "Faster in years 1 and 3 than the restrictive ramp; places with an existing ADU trade. All-grouped: " + rk("all_inc_ramp_k") + "."],
        ["Lower", "No slower ramp is shown by the data", rk("ramp_k"),
         f"The slowest fixed sensitivity in year 2 is {_f(min(E('ramp_k2', 3, s) for s in specs))}; Madison's own path is a separate model (AQ-024)."],
    ], "llll"))
    A("")
    A(f"Values above 1 in years 5–6 mean the rate was still rising past the 2023–2025 average. A model that caps the ramp at 1 "
      "from year 4 would understate the later years.")
    A("")
    A(f"**Spillover multiplier for already-permissive places** (`scenario_benchmark`, e.g. Madison): permissive plateau ÷ its "
      f"2017–2019 rate = ×{C('permissive_plateau_ratio')}; ×{C('permissive_plateau_ratio', spec='excl_la')} without Los Angeles; "
      f"×{_f(E('permissive_plateau_ratio', spec='top_third'))} with the top-third cutoff. Additively, +{_f(E('permissive_plateau_minus_pre'))} "
      f"per 1,000. A multiplicative reading suits Wisconsin better, because California's permissive places started from rates "
      "(about 3 per 1,000) far above any Wisconsin city; an additive +4 would be implausible for Madison. Per AQ-027 it must not be "
      "added on top of a `y` already calibrated on statewide-reform evidence that includes it.")
    A("")
    A("**Transfer caveats (apply to every number above):**")
    A("")
    for t_ in [
        "California rents and land values are much higher than Wisconsin's, which raises the return on a second home; the same law may produce fewer permits per home in Wisconsin.",
        "California's 2020 package came after 2017 and 2018 laws, local ordinances since 1982, and a statewide ADU industry; restrictive places in wave 3 already had three years of statewide ADU marketing. A first Wisconsin law starts from less.",
        "HCD ADU counts still include legalizations, ADUs on multifamily lots and with new houses that the notes do not identify (identified ones, about 1%, are excluded), and the 2012–2017 compilation includes all of them.",
        "Junior ADUs (interior conversions within the house) are included, as in Wisconsin's observed counts; under AQ-030 the benchmark gives interior conversions no reform uplift, so the transferred `y` slightly overstates the benchmark-form response.",
        "California's 2020 package also capped fees, paused owner occupancy and set an exemption floor; the Wisconsin benchmark is silent on these (AQ-022, AQ-025).",
        "The restrictive group is small places (median about 5,000 homes); large Wisconsin cities are better matched by the middle group.",
        "The study has no untreated comparison state; rises after each wave also reflect California's housing market (rents, rates, the 2017–2018 wildfires and rebuilds in some places).",
        "Single-family-to-duplex conversions (Wisconsin-only component) have no California counterpart here; any reform effect applied to them is an assumption.",
    ]:
        A(f"- {t_}")
    A("")
    # ---------------- interpretations and deviations
    A("## 11. Interpretations of the plan and deviations")
    A("")
    A("Where the plan left a detail open, the choice below was fixed before any group result was computed. None changes a "
      "pre-registered group, window or check.")
    A("")
    for t_ in [
        "**Group mean** is the homes-weighted rate (permits ÷ homes, pooled over the group's observed jurisdictions); the unweighted mean of jurisdiction rates is also published. The plan's Los Angeles check implies a size-weighted mean.",
        "**\"At least 3 permits\"** is read as the pre-period total.",
        "**Top quarter** is by rank among the wave's jurisdictions with complete pre-periods, ties at the cut included.",
        "**Year counting:** 2020 is year 1, so the year-4-to-6 plateau is 2023–2025 (2026 is not yet observed).",
        "**Excluding 2020** drops 2020 from post windows and event tables; groups and the plateau are unchanged.",
        "**Text exclusions** use keyword rules (section 1); the plan asked for exclusions \"where the record identifies them\" without a method.",
        "**Holdout grouping** uses the non-holdout permissive cutoff, so the holdout test uses nothing estimated on holdout data.",
        "**Added after the first run, as extra descriptive columns only:** the \"all grouped\" line, the increment-share ramps for the middle and permissive groups, and the bootstrap of A ÷ B. The candidate upper-path ramp (middle group) was picked after seeing them, and is labelled a candidate.",
        "**Rerun after a bug fix:** the first run counted missing jurisdiction-years as zero inside the wave statistics (not in the event tables). It was fixed and everything, including the holdout test, was rerun with unchanged methods; the holdout test was not altered in response to its result.",
        "**Bootstrap** resamples jurisdictions within each pre-registered group (groups held fixed).",
        "**Share-model sample** excludes county remainders flagged in step 0 (S6) because their BPS may include cities.",
        "**Deviation:** the plan mentions an event-study chart; this package publishes the tables (and the CSV behind them) only.",
        "**Not done here:** the Madison vs Sun Prairie check, the unknown-rules holdout and later-state tests (other work packages); the statewide BPS view is in step 0.",
    ]:
        A(f"- {t_}")
    A("")
    A("## Files and commands")
    A("")
    A("```sh\nuv run python scripts/build_ca_comparison_data.py --skip-fetch   # Gate 2 inputs (if needed)\n"
      "uv run python scripts/run_ca_study.py                             # study, holdout test, this document\n"
      "uv run python scripts/run_ca_study.py --check-doc                 # fail if this document differs from outputs\n"
      "bash scripts/test.sh                                              # includes tests/test_ca_study.py\n```")
    A("")
    A("- Code: `missing_middleware/comparison/ca_study.py`; runner `scripts/run_ca_study.py`.")
    A("- `reference/ca_study_*.csv` (group aggregates, committed): `event_study`, `groups`, `wave_stats` (every statistic with its "
      "interval, every specification), `text_exclusions`, `share_model`, `share_bootstrap`, `wi_share_volume`, `holdout_group`, `holdout_metrics`.")
    A("- `data/processed/comparison_ca/study/` (git-ignored): `study_panel` (jurisdiction × year outcome series), "
      "`groups_by_jurisdiction.csv`, `holdout_jurisdictions.csv`, `hcd_adu_outcome.parquet` (cached outcome; `--rebuild-outcome` re-reads Table A2).")
    A("")
    return "\n".join(L) + "\n"


DOC_PATH = "docs/gate3/CA_STUDY_RESULTS.md"


def update_doc(root=None, check: bool = False) -> list[str]:
    """Write (or, with check=True, compare) the results document. Returns ['CA_STUDY_RESULTS.md'] if it differs."""
    from missing_middleware.paths import PROCESSED, REFERENCE, ROOT
    root = root or ROOT
    text = render_doc(load_outputs(REFERENCE, PROCESSED / "comparison_ca" / "study"))
    path = root / DOC_PATH
    old = path.read_text() if path.exists() else ""
    if check:
        return [] if old == text else [path.name]
    path.write_text(text)
    return []
