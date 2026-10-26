"""Before/after comparison of parking-minimum repeal places against similar places
(pre-registered in docs/parking/COMPARISON_PLAN.md).

Pure functions; scripts/run_parking_comparison.py does the I/O.

Outcome: housing units permitted per 1,000 existing homes per year (Census BPS estimate
columns; homes = ACS 2020-2024 B25002 total housing units). For each repeal place:

    effect = (after - before)[place] - (after - before)[comparison places]

where the comparison rate is permits summed over all comparison places / their homes summed.
"""
from __future__ import annotations

import itertools
import math

import numpy as np
import pandas as pd

PRE_YEARS_MAX = 5
PRE_YEARS_MIN = 3
POST_YEARS = (1, 2, 3)
POP_WINDOW = (0.5, 2.0)
POP_WINDOW_WIDE = (1 / 3, 3.0)
MIN_CONTROLS = 5
FIRST_YEAR, LAST_YEAR = 2012, 2025
BOOT_DRAWS, BOOT_SEED = 2000, 20261026
CUTOFFS = (10_000, 20_000, 50_000, 100_000)


def panel(bps: pd.DataFrame) -> pd.DataFrame:
    """BPS place rows (parsers.read_bps(kind='place', state_fips=None) with a `year`)
    to one row per place and year. County-level unincorporated rows are dropped."""
    d = bps.copy()
    if "division" not in d.columns:
        d["division"] = ""
    for c in ("state_fips", "bps_id", "county_fips", "fips_place", "fips_mcd", "name", "division"):
        d[c] = d[c].astype(str).str.strip()
    d = d[d["fips_place"] != "99990"]
    d["units_2plus"] = d["2units_units"] + d["3_4units_units"] + d["5plus_units"]
    d["key"] = d["state_fips"] + "|" + d["bps_id"]
    d["acs_geoid"] = np.where(d["fips_place"].str.strip("0") != "",
                              "160|" + d["state_fips"] + d["fips_place"].str.zfill(5),
                              "060|" + d["state_fips"] + d["county_fips"].str.zfill(3) + d["fips_mcd"].str.zfill(5))
    keep = ["key", "state_fips", "division", "bps_id", "name", "county_fips", "fips_place", "fips_mcd", "acs_geoid",
            "year", "pop", "units_total", "units_2plus"]
    return d[keep].drop_duplicates(["key", "year"]).reset_index(drop=True)


# BPS names that differ from the common place name (state FIPS, lower-case name) -> BPS name
ALIASES = {("21", "lexington"): "lexington-fayette", ("02", "anchorage"): "municipality of anchorage"}


def match_place(p: pd.DataFrame, state_fips: str, name: str, population: float | None) -> str | None:
    """BPS key for a named place: same state, name equal ignoring case (or BPS name
    starting with it followed by a space, e.g. "Windham town"), never a county or
    balance-of-state row; preferring an exact name, then incorporated places, then the
    population closest to the given one, then the latest year."""
    n = ALIASES.get((state_fips, name.strip().lower()), name.strip().lower())
    s = p[p["state_fips"] == state_fips]
    low = s["name"].str.lower()
    cand = s[((low == n) | low.str.startswith(n + " ")) & ~low.str.contains("county|balance")]
    if cand.empty:
        return None
    cand = cand.sort_values("year").drop_duplicates("key", keep="last")
    cand = cand.assign(is_place=cand["fips_place"].str.strip("0") != "",
                       exact=cand["name"].str.lower() == n,
                       gap=(cand["pop"].fillna(0) - (population or 0)).abs())
    return cand.sort_values(["exact", "is_place", "gap"], ascending=[False, False, True]).iloc[0]["key"]


def state_share_repealed(p: pd.DataFrame, state_fips: str, year: int, reform_year: dict,
                         min_pop: int = 50_000) -> float:
    """Share of a state's population in places of min_pop+ (BPS population in year - 1)
    that lived in places with a citywide residential parking repeal adopted by `year`."""
    s = p[(p["state_fips"] == state_fips) & (p["year"] == year - 1) & (p["pop"] >= min_pop)]
    if s.empty or not s["pop"].sum():
        return np.nan
    done = s["key"].map(lambda k: reform_year.get(k, 9999) <= year)
    return float(s.loc[done, "pop"].sum() / s["pop"].sum())


def windows(event_year: int) -> tuple[list[int], list[int]]:
    pre = [y for y in range(event_year - PRE_YEARS_MAX, event_year) if y >= FIRST_YEAR]
    post = [event_year + k for k in POST_YEARS if event_year + k <= LAST_YEAR]
    return pre, post


def _rate(p: pd.DataFrame, keys, years, col, homes: pd.Series) -> float:
    s = p[p["key"].isin(keys) & p["year"].isin(years)]
    h = homes.reindex(list(keys)).sum()
    return float(s[col].sum()) / len(years) / h * 1000 if h else np.nan


def complete(p: pd.DataFrame, years) -> set:
    g = p[p["year"].isin(years)].groupby("key")["year"].nunique()
    return set(g[g == len(years)].index)


def controls(p: pd.DataFrame, key: str, event_year: int, excluded: set, homes: pd.Series) -> tuple[list, str]:
    """Comparison places: same state and 0.5-2x population; widened to 1/3-3x, then (plan
    deviation 1, 2026-10-26) to the same Census division at 0.5-2x and 1/3-3x, until there
    are at least MIN_CONTROLS."""
    pre, post = windows(event_year)
    last = p[(p["year"] == event_year - 1)].set_index("key")
    base, div = last["pop"], last["division"] if "division" in last else pd.Series(dtype=str)
    pop0 = base.get(key, np.nan)
    st = key.split("|")[0]
    dv = div.get(key, None)
    ok = complete(p, pre + post) & set(homes.dropna().index)
    tried = [("state", POP_WINDOW), ("state", POP_WINDOW_WIDE), ("division", POP_WINDOW), ("division", POP_WINDOW_WIDE)]
    c, label = [], ""
    for scope, (lo, hi) in tried:
        same = (lambda k: k.startswith(st + "|")) if scope == "state" else (lambda k: dv not in (None, "") and div.get(k) == dv)
        c = [k for k, v in base.items() if same(k) and k != key and k not in excluded
             and k in ok and lo * pop0 <= v <= hi * pop0]
        label = f"{scope} {lo:.2f}-{hi:.2f}"
        if len(c) >= MIN_CONTROLS:
            return c, label
    return c, label + f" (fewer than {MIN_CONTROLS})"


def effects(p: pd.DataFrame, cases: pd.DataFrame, excluded: set, homes: pd.Series) -> pd.DataFrame:
    """One row per case and outcome. cases: key, event_year (+ any id columns kept)."""
    rows = []
    for r in cases.itertuples(index=False):
        pre, post = windows(int(r.event_year))
        base = dict(r._asdict())
        if len(pre) < PRE_YEARS_MIN or len(post) < len(POST_YEARS):
            rows.append({**base, "status": "excluded: too few years"})
            continue
        if r.key not in complete(p, pre + post) or pd.isna(homes.get(r.key)):
            rows.append({**base, "status": "excluded: missing permit years or homes"})
            continue
        ctrl, window = controls(p, r.key, int(r.event_year), excluded, homes)
        for col, lab in (("units_total", "all"), ("units_2plus", "2plus")):
            t0, t1 = _rate(p, [r.key], pre, col, homes), _rate(p, [r.key], post, col, homes)
            c0, c1 = _rate(p, ctrl, pre, col, homes), _rate(p, ctrl, post, col, homes)
            rows.append({**base, "status": "included", "outcome": lab, "homes": float(homes[r.key]),
                         "pre_years": f"{pre[0]}-{pre[-1]}", "post_years": f"{post[0]}-{post[-1]}",
                         "n_controls": len(ctrl), "pop_window": window,
                         "rate_before": t0, "rate_after": t1, "ctrl_before": c0, "ctrl_after": c1,
                         "effect": (t1 - t0) - (c1 - c0)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Models for the effect (section 5 of the plan)
# ---------------------------------------------------------------------------

def design(df: pd.DataFrame, spec: dict) -> np.ndarray:
    """Design matrix for a model spec: {'bands': (cut, ...)} or {'vars': [...]}."""
    cols = [np.ones(len(df))]
    if "bands" in spec:
        for c in spec["bands"]:
            cols.append((df["population"] >= c).astype(float).values)
    for v in spec.get("vars", []):
        cols.append(df[v].astype(float).values)
    return np.column_stack(cols)


def wls(X, y, w):
    sw = np.sqrt(w)
    beta, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    return beta


def candidate_specs(has_rent=True, has_metro=True, has_pre=True) -> dict:
    specs = {"M0 one average": {}}
    for k in (1, 2):
        for cuts in itertools.combinations(CUTOFFS, k):
            specs["M1 bands at " + ", ".join(f"{c:,}" for c in cuts)] = {"bands": cuts}
    specs["M2 log population"] = {"vars": ["log_pop"]}
    if has_rent:
        specs["M3 log population + rent"] = {"vars": ["log_pop", "rel_rent"]}
    if has_metro:
        specs["M4 log population + metro"] = {"vars": ["log_pop", "metro"]}
    if has_pre:
        specs["M5 log population + before rate"] = {"vars": ["log_pop", "rate_before"]}
    if has_rent and has_metro:
        specs["M6 log population + rent + metro"] = {"vars": ["log_pop", "rel_rent", "metro"]}
    return specs


def loo_error(df: pd.DataFrame, spec: dict, weight: str = "homes") -> float:
    """Weighted mean absolute leave-one-place-out error of the effect."""
    X, y, w = design(df, spec), df["effect"].values, df[weight].values.astype(float)
    err = []
    for i in range(len(df)):
        m = np.arange(len(df)) != i
        if np.linalg.matrix_rank(X[m]) < X.shape[1]:
            return np.nan
        err.append(abs(X[i] @ wls(X[m], y[m], w[m]) - y[i]))
    return float(np.sum(np.array(err) * w) / w.sum())


def compare_models(df: pd.DataFrame, specs: dict) -> pd.DataFrame:
    rows = []
    for name, spec in specs.items():
        n_par = design(df, spec).shape[1]
        rows.append(dict(model=name, parameters=n_par, loo_wmae=loo_error(df, spec)))
    out = pd.DataFrame(rows).sort_values(["loo_wmae", "parameters"]).reset_index(drop=True)
    out["chosen"] = False
    out.loc[out["loo_wmae"].first_valid_index(), "chosen"] = True
    return out


def bootstrap(df: pd.DataFrame, spec: dict, draws=BOOT_DRAWS, seed=BOOT_SEED) -> np.ndarray:
    rng = np.random.default_rng(seed)
    X, y, w = design(df, spec), df["effect"].values, df["homes"].values.astype(float)
    out = []
    for _ in range(draws):
        i = rng.integers(0, len(df), len(df))
        if np.linalg.matrix_rank(X[i]) < X.shape[1]:
            continue
        out.append(wls(X[i], y[i], w[i]))
    return np.array(out)


def log_pop(pop) -> np.ndarray:
    return np.log10(np.maximum(np.asarray(pop, dtype=float), 1.0))


__all__ = [n for n in dir() if not n.startswith("_") and n not in ("itertools", "math", "np", "pd")]
