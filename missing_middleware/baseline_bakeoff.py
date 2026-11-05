"""Baseline bake-off, Part 1: the level (docs/shared/BASELINE_BAKEOFF_PLAN.md, locked 2026-11-05).

Every function takes a long table of state permits (state, year, size, units) and, where needed, homes at each
year (state, year, homes). A start year t uses data for years <= t and is scored on years t+1..t+5.
Annual levels are predicted per building size; five-year totals are 5 x annual (or the trend's own five years).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SIZES = ("1unit", "2units", "3_4units", "5plus")
CENSUS_YEARS = (1990, 2000, 2010, 2020)
FIRST_YEAR = 1990
HORIZON = 5
SCORE_STARTS = tuple(range(2000, 2021))
FIRST_FIT_START = 1992
GRID_005 = tuple(np.round(np.arange(0, 1.0001, 0.05), 2))
CANDIDATES = ("L0", "L1a", "L1b", "L1c", "L2", "L3", "L4a", "L4b", "L5")   # table order = tie order
FITTED = {"L3", "L5"}


# ---------------------------------------------------------------- homes at a start year (plan: shared rules)
def homes_by_year(census: pd.DataFrame, permits_all: pd.DataFrame, years) -> pd.DataFrame:
    """Homes at year t = most recent decennial count c with c + 1 <= t (published the year after), plus permits
    for years c+1..t. Demolitions are not subtracted. census: state, year, homes. permits_all: state, year, units
    (all sizes). Years before 1991 use the 1990 count with no permits added."""
    cen = census.pivot(index="state", columns="year", values="homes")
    per = permits_all.pivot(index="state", columns="year", values="units").fillna(0.0)
    rows = []
    for t in years:
        usable = [c for c in CENSUS_YEARS if c + 1 <= t] or [CENSUS_YEARS[0]]
        c = max(usable)
        add = per[[y for y in per.columns if c < y <= t]].sum(axis=1) if t > c else 0.0
        h = cen[c] + add
        rows.append(pd.DataFrame({"state": h.index, "year": t, "homes": h.values}))
    return pd.concat(rows, ignore_index=True)


# ---------------------------------------------------------------- candidates: annual level per size at start t
def _window(u: pd.DataFrame, t: int, k: int) -> pd.DataFrame:
    return u[(u["year"] > t - k) & (u["year"] <= t)]


def flat(u: pd.DataFrame, t: int, k: int) -> pd.Series:
    """Mean annual units over the k years ending at t, by (state, size)."""
    return _window(u, t, k).groupby(["state", "size"])["units"].mean()


def per_home_rate(u: pd.DataFrame, homes: pd.DataFrame, t: int, k: int | None) -> pd.Series:
    """Mean over years of units / homes that year, years t-k+1..t (k None: all years from 1990)."""
    w = u[u["year"] <= t] if k is None else _window(u, t, k)
    w = w.merge(homes, on=["state", "year"])
    return (w["units"] / w["homes"]).groupby([w["state"], w["size"]]).mean()


def at_homes(rate: pd.Series, homes: pd.DataFrame, t: int) -> pd.Series:
    h = homes[homes["year"] == t].set_index("state")["homes"]
    return rate * rate.index.get_level_values("state").map(h).values


def trend_five(u: pd.DataFrame, t: int, k: int | None) -> pd.Series:
    """Least-squares line over the years ending at t (k years, or all from 1990), extended to t+1..t+5; returns
    the five-year total / 5 (an annual figure). A negative fitted year counts as its fitted value, not 0."""
    w = u[u["year"] <= t] if k is None else _window(u, t, k)
    out = {}
    fut = np.arange(t + 1, t + HORIZON + 1)
    for key, g in w.groupby(["state", "size"]):
        b, a = np.polyfit(g["year"].values.astype(float), g["units"].values.astype(float), 1)
        out[key] = float((a + b * fut).sum()) / HORIZON
    return pd.Series(out).rename_axis(["state", "size"])


def division_rate(u: pd.DataFrame, homes: pd.DataFrame, t: int, k: int, division: pd.Series) -> pd.Series:
    """Pooled division rate per year: the division's units over k years / the division's homes summed over the
    same years, by (state, size): every state gets its own division's rate."""
    w = _window(u, t, k).merge(homes, on=["state", "year"])
    w["division"] = w["state"].map(division)
    num = w.groupby(["division", "size"])["units"].sum()
    hom = w.drop_duplicates(["state", "year"]).groupby("division")["homes"].sum()
    rate = num / num.index.get_level_values("division").map(hom).values
    idx = pd.MultiIndex.from_product([sorted(u["state"].unique()), SIZES], names=["state", "size"])
    return pd.Series([rate.get((division[s], z), np.nan) for s, z in idx], index=idx)


def predict(cand: str, u: pd.DataFrame, homes: pd.DataFrame, t: int, division: pd.Series,
            param: float | None = None) -> pd.Series:
    """Annual units by (state, size) predicted at start year t."""
    if cand == "L0":
        return flat(u, t, 3)
    if cand in ("L1a", "L1b", "L1c"):
        return flat(u, t, {"L1a": 5, "L1b": 7, "L1c": 10}[cand])
    if cand == "L2":
        return at_homes(per_home_rate(u, homes, t, None), homes, t)
    if cand == "L3":
        l0, l2 = flat(u, t, 3), predict("L2", u, homes, t, division)
        ratio = (l2 / l0).where(l0 > 0, 1.0)
        return (l0 * ratio ** param).where(l0 > 0, l2 * 0 + l0)
    if cand == "L4a":
        return trend_five(u, t, 10)
    if cand == "L4b":
        return trend_five(u, t, None)
    if cand == "L5":
        own = per_home_rate(u, homes, t, 3)
        div = division_rate(u, homes, t, 3, division).reindex(own.index)
        return at_homes(param * own + (1 - param) * div, homes, t)
    raise ValueError(cand)


# ---------------------------------------------------------------- scoring
def actual_five(u: pd.DataFrame, t: int) -> pd.Series:
    """Actual units over t+1..t+5 by (state, size)."""
    w = u[(u["year"] > t) & (u["year"] <= t + HORIZON)]
    return w.groupby(["state", "size"])["units"].sum()


def score_rows(cand: str, u: pd.DataFrame, homes: pd.DataFrame, starts, division: pd.Series,
               param: float | dict | None = None) -> pd.DataFrame:
    """One row per (state, start year): predicted and actual five-year totals, all sizes and by size, and
    |log(pred / actual)| on the all-sizes total. param: a number, or {start year: number} for fitted candidates."""
    rows = []
    for t in starts:
        p = param.get(t) if isinstance(param, dict) else param
        pred = predict(cand, u, homes, t, division, p) * HORIZON
        act = actual_five(u, t).reindex(pred.index)
        df = pd.DataFrame({"pred": pred, "actual": act}).reset_index()
        tot = df.groupby("state")[["pred", "actual"]].sum()
        by = df.pivot(index="state", columns="size", values=["pred", "actual"])
        by.columns = [f"{a}_{b}" for a, b in by.columns]
        r = tot.join(by).reset_index().assign(start=t, candidate=cand, param=p)
        r["abs_log"] = np.abs(np.log(r["pred"].clip(lower=1e-9) / r["actual"]))
        r["log_ratio"] = np.log(r["pred"].clip(lower=1e-9) / r["actual"])
        rows.append(r)
    return pd.concat(rows, ignore_index=True)


def fit_param(cand: str, u, homes, t: int, division, grid=GRID_005) -> float:
    """No look-ahead (audit 1): fit on start years s with FIRST_FIT_START <= s <= t - 5, all states, by least mean
    |log ratio| of the all-sizes five-year total. Ties go to the first grid value (b = 0, or w = 0)."""
    fit_starts = [s for s in range(FIRST_FIT_START, t - HORIZON + 1)]
    best, best_v = None, np.inf
    for g in grid:
        v = score_rows(cand, u, homes, fit_starts, division, g)["abs_log"].mean()
        if v < best_v - 1e-12:
            best, best_v = g, v
    return float(best)


def block_bootstrap_starts(starts, n_draws=2000, block=5, seed=20261105) -> np.ndarray:
    """Moving blocks of `block` consecutive start years, drawn with replacement until the series is filled, last
    block cut to length (audit 2). Returns an (n_draws, len(starts)) array of start years; the same draws are used
    for every state and for L0 and the candidate (paired)."""
    starts = list(starts)
    n = len(starts)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / block))
    first = rng.integers(0, n - block + 1, size=(n_draws, nb))
    out = np.concatenate([np.array(starts)[first[:, [j]] + np.arange(block)] for j in range(nb)], axis=1)
    return out[:, :n]


def paired_diff(cand_rows: pd.DataFrame, base_rows: pd.DataFrame, draws: np.ndarray) -> np.ndarray:
    """Mean over states and drawn start years of (candidate |log| - L0 |log|), one value per draw."""
    a = cand_rows.pivot(index="start", columns="state", values="abs_log")
    b = base_rows.pivot(index="start", columns="state", values="abs_log").reindex_like(a)
    per_start = (a - b).mean(axis=1)
    return np.array([per_start.loc[d].mean() for d in draws])


def pick(summary: pd.DataFrame) -> str:
    """Option B pick rule. summary: one row per candidate with score, wi_score, boot_hi (95th pct of the paired
    difference). Passing: score <= 0.98 x L0; boot_hi < 0; wi_score <= 1.05 x L0's wi_score. Lowest score wins;
    scores within 0.001 go to table order."""
    base = summary.set_index("candidate").loc["L0"]
    s = summary[summary["candidate"] != "L0"].copy()
    s["passes"] = (s["score"] <= 0.98 * base["score"]) & (s["boot_hi"] < 0) & (s["wi_score"] <= 1.05 * base["wi_score"])
    ok = s[s["passes"]]
    if ok.empty:
        return "L0"
    best = ok["score"].min()
    tied = ok[ok["score"] <= best + 0.001]
    return min(tied["candidate"], key=CANDIDATES.index)


# ---------------------------------------------------------------- range and its out-of-sample coverage
def range_multipliers(ratios: pd.DataFrame, lo: float = 0.10, hi: float = 0.90) -> pd.DataFrame:
    """ratios: start, size, ratio (actual / predicted). Percentiles by size."""
    return ratios.groupby("size")["ratio"].quantile([lo, hi]).unstack().rename(columns={lo: "low", hi: "high"})


def coverage_check(ratios: pd.DataFrame, totals: pd.DataFrame, checks=range(2005, 2021),
                   steps=((0.10, 0.90), (0.05, 0.95), (0.025, 0.975))) -> pd.DataFrame:
    """For each check year t, the range from ratios at start years s <= t - 5 only; does t's actual all-sizes total
    land inside? totals: start, size, pred, actual (Wisconsin). Rows for each step in `steps` (widening rule)."""
    out = []
    for lo, hi in steps:
        for t in checks:
            past = ratios[ratios["start"] <= t - HORIZON]
            if past.empty:
                continue
            m = range_multipliers(past, lo, hi)
            cur = totals[totals["start"] == t].set_index("size")
            low = float((cur["pred"] * m["low"].reindex(cur.index)).sum())
            high = float((cur["pred"] * m["high"].reindex(cur.index)).sum())
            act = float(cur["actual"].sum())
            out.append(dict(lo=lo, hi=hi, start=t, low=low, high=high, actual=act, inside=low <= act <= high))
    return pd.DataFrame(out)
