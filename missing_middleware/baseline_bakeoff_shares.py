"""Baseline bake-off, Part 2: how each building size's state total splits among municipality pieces
(docs/shared/BASELINE_BAKEOFF_PLAN.md, locked 2026-11-05).

Arrays are pieces x years (1990-2025) for one building size, NaN where a piece has no row that year. A start year t
uses years <= t; its outcome is t+1..t+5. Shares are scaled to the actual total of the scored pieces, so only the
split is tested.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

YEARS = np.arange(1990, 2026)
SIZES = ("1unit", "2units", "3_4units", "5plus")
SCORE_STARTS = tuple(range(2004, 2021))
FIRST_FIT_START = 1992
HORIZON = 5
K_GRID = tuple(10 ** (1 + 0.25 * j) for j in range(17))          # 10 to 100,000 homes, log grid
CANDIDATES = ("S0", "S1a", "S1b", "S2a", "S2b", "S3", "S4")       # table order = tie order


def _cols(t: int, k: int) -> np.ndarray:
    return np.where((YEARS > t - k) & (YEARS <= t))[0]


def nanmean_win(a: np.ndarray, t: int, k: int) -> np.ndarray:
    w = a[:, _cols(t, k)]
    with np.errstate(all="ignore"):
        m = np.nanmean(w, axis=1)
    return np.nan_to_num(m, nan=0.0)


def county_pace(a: np.ndarray, county: np.ndarray, t: int, k: int, split_k: int, homes_t: np.ndarray) -> np.ndarray:
    """County's total units per year over k years, split within the county by each piece's own split_k-year share
    (by homes when the county had none)."""
    w = np.nan_to_num(a[:, _cols(t, k)])
    ws = np.nan_to_num(a[:, _cols(t, split_k)]).sum(axis=1)
    df = pd.DataFrame({"c": county, "pace": w.sum(axis=1) / k, "own": ws, "h": homes_t})
    g = df.groupby("c")
    cp, co, ch = g["pace"].transform("sum"), g["own"].transform("sum"), g["h"].transform("sum")
    share = np.where(co > 0, df["own"] / co.where(co > 0, 1), df["h"] / ch.where(ch > 0, 1))
    return (cp * share).to_numpy()


def shrink(a: np.ndarray, county: np.ndarray, t: int, homes_t: np.ndarray, k: float) -> np.ndarray:
    """Own 3-year rate per home blended with the county's 3-year rate by n / (n + k), n = the piece's homes."""
    own = nanmean_win(a, t, 3)
    df = pd.DataFrame({"c": county, "u": own, "h": homes_t})
    g = df.groupby("c")
    crate = (g["u"].transform("sum") / g["h"].transform("sum").where(lambda s: s > 0, np.nan)).fillna(0).to_numpy()
    with np.errstate(all="ignore"):
        orate = np.where(homes_t > 0, own / homes_t, 0.0)
    w = homes_t / (homes_t + k)
    return (w * orate + (1 - w) * crate) * homes_t


def lumpy_cap(a: np.ndarray, t: int, cap: float = 2.0) -> np.ndarray:
    """5-year window; each year counts at most cap x the piece's average of its other 4 years; then the mean."""
    w = a[:, _cols(t, 5)]
    n = np.sum(~np.isnan(w), axis=1, keepdims=True)
    s = np.nansum(w, axis=1, keepdims=True)
    with np.errstate(all="ignore"):
        others = np.where(n > 1, (s - np.nan_to_num(w)) / (n - 1), np.nan)
        capped = np.where(np.isnan(w), np.nan, np.where(np.isnan(others), w, np.minimum(w, cap * others)))
        m = np.nanmean(capped, axis=1)
    return np.nan_to_num(m, nan=0.0)


def predict(cand: str, a: np.ndarray, county: np.ndarray, t: int, homes_t: np.ndarray, k: float | None = None,
            cap: float = 2.0) -> np.ndarray:
    if cand == "S0":
        return nanmean_win(a, t, 3)
    if cand == "S1a":
        return nanmean_win(a, t, 5)
    if cand == "S1b":
        return nanmean_win(a, t, 10)
    if cand == "S2a":
        return county_pace(a, county, t, 3, 10, homes_t)
    if cand == "S2b":
        return county_pace(a, county, t, 10, 10, homes_t)
    if cand == "S3":
        return shrink(a, county, t, homes_t, k)
    if cand == "S4":
        return lumpy_cap(a, t, cap)
    raise ValueError(cand)


def actual(a: np.ndarray, t: int) -> tuple[np.ndarray, np.ndarray]:
    """Actual units over t+1..t+5 and a mask of pieces with at least one reported outcome year."""
    w = a[:, (YEARS > t) & (YEARS <= t + HORIZON)]
    ok = ~np.all(np.isnan(w), axis=1)
    return np.nansum(w, axis=1), ok


def score_start(preds: dict, arrays: dict, t: int, mask: np.ndarray | None = None) -> float:
    """Sum over pieces and sizes of |scaled predicted - actual| / actual units, for one start year."""
    num = den = 0.0
    for z in SIZES:
        act, ok = actual(arrays[z], t)
        if mask is not None:
            ok = ok & mask
        p = preds[z][ok] * HORIZON
        ac = act[ok]
        if p.sum() > 0:
            p = p * ac.sum() / p.sum()
        num += np.abs(p - ac).sum()
        den += ac.sum()
    return num / den if den else np.nan


def homes_at(census: dict, permits_all: np.ndarray, t: int, fallback: np.ndarray) -> np.ndarray:
    """Homes at t by piece: most recent decennial count c with c + 1 <= t, plus permits for c+1..t. A piece missing
    from that census uses the next census minus permits in between (a labelled back-cast); none: today's ACS homes.
    census: {year: array of counts by piece, NaN if missing}."""
    usable = [c for c in sorted(census) if c + 1 <= t] or [min(census)]
    c = max(usable)
    add = np.nansum(permits_all[:, (YEARS > c) & (YEARS <= t)], axis=1)
    h = census[c] + add
    for c2 in sorted(y for y in census if y > c):
        back = census[c2] - np.nansum(permits_all[:, (YEARS > t) & (YEARS <= c2)], axis=1)
        h = np.where(np.isnan(h), back, h)
    return np.where(np.isnan(h), fallback, h)


def block_bootstrap_starts(starts, n_draws=2000, block=5, seed=20261105) -> np.ndarray:
    from missing_middleware.baseline_bakeoff import block_bootstrap_starts as bbs
    return bbs(starts, n_draws=n_draws, block=block, seed=seed)


def pick(summary: pd.DataFrame) -> str:
    """Two-part rule (option B): score <= 0.98 x S0's and the 90% paired-bootstrap range below 0. Lowest score wins;
    within 0.001, table order. None passes: S0."""
    base = summary.set_index("candidate").loc["S0", "score"]
    s = summary[summary["candidate"] != "S0"]
    ok = s[(s["score"] <= 0.98 * base) & (s["boot_hi"] < 0)]
    if ok.empty:
        return "S0"
    best = ok["score"].min()
    return min(ok[ok["score"] <= best + 0.001]["candidate"], key=CANDIDATES.index)
