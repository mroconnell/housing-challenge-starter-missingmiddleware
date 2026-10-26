"""All-housing baseline: permitted units by area, year and structure type, with a
current-law projection for 2026-2031. Shared by the parking and TOD scenarios.

Source: Census Building Permits Survey (BPS) annual place files for Wisconsin, already
parsed by the foundation build (data/processed/foundation/bps_place_annual.parquet).
Units are housing units authorized by building permits, using the BPS estimate columns
(reported plus Census imputation for months a place did not report), so that the areas
plus an explicit unallocated row add up to the published state total.

Structure types follow BPS: units in 1-unit, 2-unit, 3-4 unit and 5+ unit buildings.

Allocation of BPS rows to municipality pieces (area_id "muni:<geoid>"):
  - a place matched to one municipality piece: all of it (observed);
  - a municipality split across counties: by the piece's share of one-unit detached homes
    (the foundation crosswalk's alloc_share; assumed);
  - a county row for towns without their own BPS row: split per year by one-unit detached
    homes among the towns it covers that year (foundation allocation table; assumed);
  - anything else, and the difference between the published state total and the sum of
    the allocated rows, goes to the unallocated row.

Missing reports are missing, not zero: the foundation build marks Milwaukee city's 2-unit,
3-4 and 5+ series as not reported in 2020, 2023 and 2025 (KNOWN_BPS_GAPS). Those cells are
null here, are skipped when fitting or scoring, and the published state total (which
contains Milwaukee's zeros) is kept as published with a note.

Projection: each area and structure type starts from its mean over the last k years; a
candidate either holds that flat or scales it by the state's linear trend for that type.
The candidate is chosen by a held-out-year test (choose). The band (low/high) comes from
the spread of the chosen candidate's held-out errors at the state level, by structure
type, so it is measured, not assumed.

Gap rule: for Milwaukee city's flagged years only the 3-4 and 5+ series are null (BPS
shows 0 there despite documented apartment construction); its 2-unit and 1-unit counts
are kept. The foundation build nulls the combined 2-4 column; this split keeps the 2-unit
figure, which is not in doubt.

Pure functions only (no file paths); scripts/build_housing_baseline.py does the I/O.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TYPES = ("1unit", "2units", "3_4units", "5plus")
TYPE_LABELS = {"1unit": "1 unit", "2units": "2 units", "3_4units": "3-4 units", "5plus": "5+ units"}
BPS_UNIT_COLS = {"1unit": "1unit_units", "2units": "2units_units", "3_4units": "3_4units_units",
                 "5plus": "5plus_units"}
HISTORY_YEARS = tuple(range(2015, 2026))
BRIDGE_YEAR = 2026
FORECAST_YEARS = (2027, 2028, 2029, 2030, 2031)
UNALLOCATED = "unallocated"
WINDOWS = (1, 2, 3, 4, 5)
ORIGINS = (2019, 2020, 2021, 2022)   # last year of data used in each held-out test
HORIZON = 5                          # years after the origin that are scored (up to 2025)
GAP_TYPES = ("3_4units", "5plus")
KEYS = ["bps_id", "county_fips", "fips_mcd", "fips_place"]


def long_bps(bps_place: pd.DataFrame, gaps: dict) -> pd.DataFrame:
    """BPS place rows to long form (one row per place-year-type), gaps set to null.

    gaps maps (bps_id, year) -> anything; for those rows the 3-4 and 5+ series are null.
    """
    rows = []
    for t, col in BPS_UNIT_COLS.items():
        d = bps_place[KEYS + ["year", "name", "reporting_status", col]].rename(columns={col: "units"})
        d = d.assign(structure_type=t, units=d["units"].astype(float))
        if t in GAP_TYPES:
            hit = [(b, y) in gaps for b, y in zip(d["bps_id"], d["year"])]
            d.loc[hit, "units"] = np.nan
        rows.append(d)
    return pd.concat(rows, ignore_index=True)


def allocate(long: pd.DataFrame, xw: pd.DataFrame, alloc: pd.DataFrame) -> pd.DataFrame:
    """Allocate long BPS rows to municipality pieces. Returns area_id, year, structure_type,
    units, allocation (observed/assumed), plus unmatched rows with area_id = UNALLOCATED."""
    xk = xw.rename(columns={"bps_county_fips": "county_fips"})
    direct = xk[(xk["match_type"] != "county_unincorporated") & xk["area_id"].notna()]
    direct = direct[KEYS + ["area_id", "alloc_share", "n_pieces"]]
    a = long.merge(direct, on=KEYS, how="inner")
    a["units"] = a["units"] * a["alloc_share"]
    a["allocation"] = np.where(a["n_pieces"] > 1, "assumed_split_by_homes", "observed")

    ck = alloc.rename(columns={"bps_county_fips": "county_fips"})[KEYS + ["year", "area_id", "alloc_share"]]
    c = long.merge(ck, on=KEYS + ["year"], how="inner")
    c["units"] = c["units"] * c["alloc_share"]
    c["allocation"] = "assumed_county_row_split"

    used = pd.concat([a[KEYS + ["year"]], c[KEYS + ["year"]]]).drop_duplicates()
    rest = long.merge(used.assign(_u=1), on=KEYS + ["year"], how="left")
    rest = rest[rest["_u"].isna()].drop(columns="_u")
    rest = rest.assign(area_id=UNALLOCATED, allocation="unmatched_bps_row")

    cols = ["area_id", "year", "structure_type", "units", "allocation"]
    out = pd.concat([a[cols], c[cols], rest[cols]], ignore_index=True)
    # sum with min_count so an all-null cell stays null (missing, not zero)
    return (out.groupby(["area_id", "year", "structure_type", "allocation"], as_index=False)["units"]
            .sum(min_count=1))


def reconcile(by_area: pd.DataFrame, state: pd.DataFrame) -> pd.DataFrame:
    """Add the unallocated row so each year and type sums to the published state total.

    state: year, structure_type, units (published BPS state file).
    The unallocated row = state - sum of allocated areas (nulls counted as 0), plus any
    unmatched BPS rows already in by_area.
    """
    alloc_sum = (by_area[by_area["area_id"] != UNALLOCATED]
                 .groupby(["year", "structure_type"])["units"].sum().rename("allocated"))
    s = state.set_index(["year", "structure_type"])["units"].rename("state")
    r = pd.concat([s, alloc_sum], axis=1).fillna(0.0)
    r["units"] = r["state"] - r["allocated"]
    r = r.reset_index()[["year", "structure_type", "units"]]
    r = r.assign(area_id=UNALLOCATED, allocation="reconciliation_to_state")
    keep = by_area[by_area["area_id"] != UNALLOCATED]
    return pd.concat([keep, r[keep.columns]], ignore_index=True)


def area_year_type(by_area: pd.DataFrame) -> pd.DataFrame:
    """One row per area, year and structure type (allocation kinds summed; null stays null)."""
    g = by_area.groupby(["area_id", "year", "structure_type"], as_index=False)["units"].sum(min_count=1)
    kinds = (by_area.groupby(["area_id", "year", "structure_type"])["allocation"]
             .agg(lambda s: ";".join(sorted(set(s)))).reset_index())
    return g.merge(kinds, on=["area_id", "year", "structure_type"])


def flat_mean(hist: pd.DataFrame, origin: int, k: int) -> pd.Series:
    """Mean units per year over origin-k+1..origin for each (area, type), skipping nulls.
    Areas with no non-null year in the window get NaN."""
    w = hist[(hist["year"] > origin - k) & (hist["year"] <= origin)]
    return w.groupby(["area_id", "structure_type"])["units"].mean()


def state_trend_factor(hist: pd.DataFrame, origin: int, k: int, trend_years: int | None,
                       years: list[int]) -> pd.DataFrame:
    """Per type and future year: state linear trend value / state k-year mean.

    trend_years None means no trend (factor 1). The trend is an ordinary least-squares line
    through the state totals (sum over areas, nulls as 0) for the last trend_years years up
    to the origin, floored at zero."""
    rows = []
    st = hist.groupby(["structure_type", "year"])["units"].sum()
    for t in TYPES:
        s = st.loc[t]
        base = s[(s.index > origin - k) & (s.index <= origin)].mean()
        for y in years:
            if trend_years is None or not base:
                f = 1.0
            else:
                w = s[(s.index > origin - trend_years) & (s.index <= origin)]
                b, a = np.polyfit(w.index.astype(float), w.values.astype(float), 1)
                f = max(a + b * y, 0.0) / base
            rows.append(dict(structure_type=t, year=y, factor=f))
    return pd.DataFrame(rows)


# Candidate projections tested against held-out years: (name, k, trend_years).
# k = years averaged for each area's level; trend_years = years in the state trend line
# (None: flat). "all" uses every year up to the origin.
CANDIDATES = tuple([(f"flat_{k}y", k, None) for k in WINDOWS]
                   + [(f"trend5_level{k}y", k, 5) for k in (3, 5)]
                   + [(f"trendall_level{k}y", k, "all") for k in (3, 5)])


def predict(hist: pd.DataFrame, origin: int, k: int, trend_years, years: list[int]) -> pd.DataFrame:
    """Predicted units per area, type and future year from data up to origin."""
    ty = (origin - int(hist["year"].min()) + 1) if trend_years == "all" else trend_years
    lvl = flat_mean(hist, origin, k).rename("level").reset_index()
    f = state_trend_factor(hist, origin, k, ty, years)
    out = lvl.merge(f, on="structure_type")
    out["pred"] = out["level"] * out["factor"]
    return out


def holdout_scores(hist: pd.DataFrame, candidates=CANDIDATES, origins=ORIGINS, horizon=HORIZON) -> pd.DataFrame:
    """Held-out-year test of each candidate projection.

    For each origin T and candidate: predict each area-type's mean over T+1..T+horizon
    (capped at the last data year) from years up to T only, and compare with what happened.
    Only cells observed (non-null) in the scored years count; a missing report is
    neither a hit nor a miss. Returns one row per origin, candidate and structure type with:
      state_ratio = actual state total / predicted state total (mean annual units),
      area_wape   = sum |predicted - actual| / sum actual over areas (mean annual units).
    """
    last = int(hist["year"].max())
    first = int(hist["year"].min())
    rows = []
    for T in origins:
        yrs = list(range(T + 1, min(T + horizon, last) + 1))
        actual = hist[hist["year"].isin(yrs)].groupby(["area_id", "structure_type"])["units"].mean()
        for name, k, ty in candidates:
            if T - k + 1 < first or (isinstance(ty, int) and T - ty + 1 < first):
                continue
            pr = predict(hist, T, k, ty, yrs).groupby(["area_id", "structure_type"])["pred"].mean()
            j = pd.concat([pr.rename("pred"), actual.rename("actual")], axis=1).dropna()
            for t, g in j.groupby(level="structure_type"):
                rows.append(dict(origin=T, candidate=name, window=k, trend_years=ty, structure_type=t,
                                 years_scored=f"{yrs[0]}-{yrs[-1]}",
                                 predicted=g["pred"].sum(), actual=g["actual"].sum(),
                                 state_ratio=g["actual"].sum() / g["pred"].sum() if g["pred"].sum() else np.nan,
                                 area_wape=(g["pred"] - g["actual"]).abs().sum() / g["actual"].sum()
                                 if g["actual"].sum() else np.nan))
    return pd.DataFrame(rows)


def choose(scores: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    """Pick the candidate with the lowest area-level error per unit permitted, summed over
    origins and types (only origins every candidate was scored on). Ties go to the simpler
    candidate (flat before trend, longer window first)."""
    n = scores.groupby("candidate")["origin"].nunique()
    common = set.intersection(*[set(g["origin"]) for _, g in scores.groupby("candidate")])
    s = scores[scores["origin"].isin(common)]
    s = s.assign(abs_err=s["area_wape"] * s["actual"])
    summ = (s.groupby("candidate").agg(abs_err=("abs_err", "sum"), actual=("actual", "sum"),
                                       state_abs_log_ratio=("state_ratio", lambda r: np.abs(np.log(r)).mean()))
            .reset_index())
    summ["area_wape_all_types"] = summ["abs_err"] / summ["actual"]
    summ["origins_scored"] = ";".join(str(o) for o in sorted(common))
    summ["origins_available"] = summ["candidate"].map(n)
    order = {c[0]: i for i, c in enumerate(CANDIDATES)}
    summ["_o"] = summ["candidate"].map(order)
    summ = summ.sort_values(["area_wape_all_types", "_o"])
    best = summ.iloc[0]["candidate"]
    summ["chosen"] = summ["candidate"] == best
    return best, summ.drop(columns=["abs_err", "_o"]).sort_values("area_wape_all_types")


def band(scores: pd.DataFrame, candidate: str) -> pd.DataFrame:
    """Low/high multipliers by structure type from the chosen candidate's held-out errors:
    the smallest and largest state-level actual/predicted ratio across origins, widened to
    include 1 so the central path is always inside its band."""
    s = scores[scores["candidate"] == candidate]
    b = s.groupby("structure_type")["state_ratio"].agg(ratio_min="min", ratio_max="max").reset_index()
    b["low"] = b["ratio_min"].clip(upper=1.0)
    b["high"] = b["ratio_max"].clip(lower=1.0)
    return b


def project(hist: pd.DataFrame, candidate: str, bands: pd.DataFrame) -> pd.DataFrame:
    """Projection for 2026-2031 per area and type from all data, using the chosen
    candidate; low/high = central x the held-out band for that type. Areas with no
    observed year in the level window are projected at 0 and flagged."""
    _, k, ty = next(c for c in CANDIDATES if c[0] == candidate)
    last = int(hist["year"].max())
    years = [BRIDGE_YEAR] + list(FORECAST_YEARS)
    pr = predict(hist, last, k, ty, years)
    allpairs = hist[["area_id", "structure_type"]].drop_duplicates()
    out = allpairs.merge(pd.DataFrame({"year": years}), how="cross").merge(
        pr[["area_id", "structure_type", "year", "pred"]], on=["area_id", "structure_type", "year"], how="left")
    out["no_data_in_window"] = out["pred"].isna()
    out["central"] = out["pred"].fillna(0.0)
    out = out.merge(bands[["structure_type", "low", "high"]], on="structure_type", how="left")
    lo, hi = out["central"] * out["low"], out["central"] * out["high"]
    # the unallocated row can be negative (place rows exceed the state file); keep low <= high
    out["low"], out["high"] = np.minimum(lo, hi), np.maximum(lo, hi)
    out["in_five_year_total"] = out["year"].isin(FORECAST_YEARS)
    out["method"] = candidate
    out["window_years"] = f"{last - k + 1}-{last}"
    return out[["area_id", "structure_type", "year", "in_five_year_total", "low", "central", "high",
                "method", "window_years", "no_data_in_window"]]


def state_long_run_ratios(state: pd.DataFrame, k: int, horizon: int = HORIZON) -> pd.DataFrame:
    """Long-run check of a flat k-year mean at the state level.

    state: year, structure_type, units (published state totals, any span). For every origin T
    with k years behind it and a full horizon ahead, ratio = actual mean over T+1..T+horizon
    divided by the mean over T-k+1..T. One row per origin and type, plus type "all"."""
    s = pd.concat([state, state.groupby("year", as_index=False)["units"].sum().assign(structure_type="all")])
    rows = []
    for t, g in s.groupby("structure_type"):
        u = g.set_index("year")["units"].sort_index()
        for T in u.index:
            past = u[(u.index > T - k) & (u.index <= T)]
            fut = u[(u.index > T) & (u.index <= T + horizon)]
            if len(past) < k or len(fut) < horizon:
                continue
            rows.append(dict(origin=int(T), structure_type=t, years_scored=f"{T + 1}-{T + horizon}",
                             predicted=past.mean(), actual=fut.mean(), ratio=fut.mean() / past.mean()))
    return pd.DataFrame(rows)


LONG_RUN_QUANTILES = (0.10, 0.90)


def long_run_band(ratios: pd.DataFrame, q=LONG_RUN_QUANTILES) -> pd.DataFrame:
    """Per type: the 10th and 90th percentile of the long-run actual/predicted ratio (the
    band), and the worst and best five-year periods on record (shown as a stress case)."""
    g = ratios.groupby("structure_type")["ratio"]
    b = pd.DataFrame({"low": g.quantile(q[0]), "high": g.quantile(q[1]),
                      "worst": g.min(), "best": g.max(), "n_origins": g.size()}).reset_index()
    worst = ratios.loc[ratios.groupby("structure_type")["ratio"].idxmin(), ["structure_type", "years_scored"]]
    best = ratios.loc[ratios.groupby("structure_type")["ratio"].idxmax(), ["structure_type", "years_scored"]]
    b = b.merge(worst.rename(columns={"years_scored": "worst_period"}), on="structure_type")
    b = b.merge(best.rename(columns={"years_scored": "best_period"}), on="structure_type")
    b["low"] = b["low"].clip(upper=1.0)
    b["high"] = b["high"].clip(lower=1.0)
    return b
