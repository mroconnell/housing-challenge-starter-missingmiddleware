"""TOD comparison cases: shared measurement functions (docs/tod/CASE_ANALYSIS_PLAN.md).

The plan was written before any permits were counted; these functions implement it as written:

- Areas (plan section 2, as changed in section 7 on 2026-10-26; uniform_areas): treatment = lots inside the
  official upzoning boundary whose allowed density rose and that were not already at the law; comparison = lots
  whose allowed density did not change in the window, outside the treatment, whose representative point lies within
  1/4 mile of the treated land, in the same city; second comparison = such lots within 1/2 mile of a rail or rapid-
  transit station whose own 1/2-mile area has no treated land. Lots rezoned outside the reform during the window and
  land already at the law are in no area. The original rule (assign_areas alone) is kept as a sensitivity.
- Eligible land: parcel acres in residential, mixed-use or commercial zoning before the change, less parks,
  water, institutional campuses and cemeteries (streets are not parcels).
- Outcome (section 3): housing units in new-construction building permits, by issue year, de-duplicated by
  permit number, on eligible parcels. Rate = units per eligible acre per year.
- Periods (section 4): before = up to 6 full years before the effective year (at least 3, else context only);
  after = years 1 to 5, each shown; year 0 shown but not used.
- Estimate: difference-in-differences of mean yearly rates, (T_after - T_before) - (C_after - C_before).
- Interval (section 5): 90% interval from resampling whole projects within each area, 2,000 draws, fixed seed.
- Dose: area-weighted mean of (new maximum FAR - old maximum FAR) over the treatment's eligible land.
- Effect per dose: estimate / dose.
- Sensitivities: second comparison area; leaving out the largest project in each area and period; permits per
  1,000 existing homes instead of per acre; the original area rule.
- Where a case has no defensible FAR conversion (Charlotte), the dose is added height in feet and the effect is per
  added foot; such cases have no effect per added FAR and stay out of any per-FAR pooling.

Inputs are plain pandas tables so the arithmetic can be tested without any geography. Geometry helpers take
GeoDataFrames in a projected CRS measured in metres.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

QUARTER_MILE_M = 402.336
HALF_MILE_M = 804.672
SQM_PER_ACRE = 4046.8564224
BEFORE_MAX = 6
BEFORE_MIN = 3
AFTER_YEARS = (1, 2, 3, 4, 5)
N_DRAWS = 2000
SEED = 20261026
LEVEL = 0.90
TREAT, COMP, COMP2 = "treatment", "comparison", "second_comparison"
AREAS = (TREAT, COMP, COMP2)
ROLES = ("fit", "medium", "heldout", "context", "mandate")


# --------------------------------------------------------------------------- periods

def period_years(effective_year: int, first_year: int, last_full_year: int) -> dict[str, list[int]]:
    """Before (up to 6 full years before the effective year, limited by the data), year 0, after (years 1-5)."""
    before = [y for y in range(effective_year - BEFORE_MAX, effective_year) if y >= first_year]
    after = [effective_year + k for k in AFTER_YEARS if effective_year + k <= last_full_year]
    return {"before": before, "year0": [effective_year], "after": after}


def case_status(before: list[int], after: list[int], has_units: bool = True, is_permits: bool = True) -> str:
    """'measured' when the plan's minimums hold; otherwise the reason the case is context only."""
    if not is_permits:
        return "context_only: not permits"
    if not has_units:
        return "context_only: no unit counts"
    if len(before) < BEFORE_MIN:
        return f"context_only: {len(before)} before years (plan needs {BEFORE_MIN})"
    if not after:
        return "context_only: no after years"
    return "measured"


# --------------------------------------------------------------------------- rates and DiD

def _check_permits(p: pd.DataFrame) -> None:
    missing = {"project", "area", "year", "units"} - set(p.columns)
    if missing:
        raise ValueError(f"permits table lacks {sorted(missing)}")


def rates_by_year(permits: pd.DataFrame, denom: Mapping[str, float], years: Iterable[int],
                  areas: Iterable[str] = AREAS, scale: float = 1.0) -> pd.DataFrame:
    """Units and units per denominator (x scale) by area and year; years with no permits count as 0."""
    _check_permits(permits)
    years = list(years)
    u = permits.groupby(["area", "year"])["units"].sum()
    rows = []
    for a in areas:
        if a not in denom or not denom[a] or np.isnan(denom[a]):
            continue
        for y in years:
            units = float(u.get((a, y), 0.0))
            rows.append({"area": a, "year": int(y), "units": units, "denominator": float(denom[a]),
                         "rate": units / float(denom[a]) * scale})
    return pd.DataFrame(rows, columns=["area", "year", "units", "denominator", "rate"])


def did_from_rates(rates: pd.DataFrame, before: list[int], after: list[int], treat: str = TREAT, comp: str = COMP) -> dict:
    """Difference-in-differences of mean yearly rates."""
    def m(area, yrs):
        r = rates[(rates["area"] == area) & (rates["year"].isin(yrs))]["rate"]
        return float(r.mean()) if len(r) else float("nan")
    tb, ta, cb, ca = m(treat, before), m(treat, after), m(comp, before), m(comp, after)
    return {"treat_before": tb, "treat_after": ta, "comp_before": cb, "comp_after": ca,
            "did": (ta - tb) - (ca - cb)}


def _did_fast(units: dict, denom: Mapping[str, float], before: list[int], after: list[int], treat: str, comp: str,
              scale: float = 1.0) -> float:
    def m(area, yrs):
        return sum(units.get((area, y), 0.0) for y in yrs) / len(yrs) / denom[area] * scale
    return (m(treat, after) - m(treat, before)) - (m(comp, after) - m(comp, before))


def did(permits: pd.DataFrame, denom: Mapping[str, float], before: list[int], after: list[int],
        treat: str = TREAT, comp: str = COMP, scale: float = 1.0) -> dict:
    rates = rates_by_year(permits, denom, before + after, areas=(treat, comp), scale=scale)
    return did_from_rates(rates, before, after, treat, comp)


def bootstrap_did(permits: pd.DataFrame, denom: Mapping[str, float], before: list[int], after: list[int],
                  treat: str = TREAT, comp: str = COMP, draws: int = N_DRAWS, seed: int = SEED,
                  level: float = LEVEL, scale: float = 1.0) -> tuple[float, float, np.ndarray]:
    """Interval for the DiD from resampling whole projects (with replacement) within each area.

    Only projects with permits in the before or after years enter; the denominators stay fixed. A project keeps
    all of its permits (all years) when drawn."""
    _check_permits(permits)
    yrs = set(before) | set(after)
    p = permits[permits["year"].isin(yrs) & permits["area"].isin([treat, comp])]
    rng = np.random.default_rng(seed)
    per_area = {}
    for a in (treat, comp):
        pa = p[p["area"] == a]
        proj = pa.groupby(["project", "year"])["units"].sum().reset_index()
        keys = list(pd.unique(proj["project"]))
        # matrix: project x year
        mat = np.zeros((len(keys), len(before) + len(after)))
        idx = {k: i for i, k in enumerate(keys)}
        cols = {y: j for j, y in enumerate(list(before) + list(after))}
        for r in proj.itertuples(index=False):
            mat[idx[r.project], cols[r.year]] += r.units
        per_area[a] = mat
    nb = len(before)
    out = np.empty(draws)
    for d in range(draws):
        means = {}
        for a, mat in per_area.items():
            if len(mat):
                s = mat[rng.integers(0, len(mat), len(mat))].sum(axis=0)
            else:
                s = np.zeros(len(before) + len(after))
            means[a] = (s[nb:].mean() - s[:nb].mean()) / denom[a] * scale
        out[d] = means[treat] - means[comp]
    lo, hi = np.quantile(out, [(1 - level) / 2, 1 - (1 - level) / 2])
    return float(lo), float(hi), out


def drop_largest_project(permits: pd.DataFrame, before: list[int], after: list[int]) -> pd.DataFrame:
    """Leave out the largest project (most units) in each area and period (before, after)."""
    _check_permits(permits)
    p = permits.copy()
    p["period"] = np.where(p["year"].isin(before), "before", np.where(p["year"].isin(after), "after", "other"))
    tot = p[p["period"] != "other"].groupby(["area", "period", "project"])["units"].sum().reset_index()
    drop = set()
    for (a, per), g in tot.groupby(["area", "period"]):
        g = g.sort_values(["units", "project"], ascending=[False, True])
        if len(g) and g.iloc[0]["units"] > 0:
            drop.add((a, per, g.iloc[0]["project"]))
    keep = [(a, per, pr) not in drop for a, per, pr in zip(p["area"], p["period"], p["project"])]
    return p[keep].drop(columns="period")


def event_years(rates: pd.DataFrame, effective_year: int, before: list[int], treat: str = TREAT, comp: str = COMP) -> pd.DataFrame:
    """Year-by-year treatment-minus-comparison gap relative to the before mean (for the pooled ramp)."""
    t = rates[rates["area"] == treat].set_index("year")["rate"]
    c = rates[rates["area"] == comp].set_index("year")["rate"]
    base = (t.reindex(before).mean() - c.reindex(before).mean())
    rows = []
    for y in sorted(set(t.index) & set(c.index)):
        rows.append({"year": int(y), "event_year": int(y - effective_year), "gap_minus_before": float(t[y] - c[y] - base)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- dose

def dose(table: pd.DataFrame, acres: str = "acres", old: str = "old_far", new: str = "new_far") -> float:
    """Area-weighted mean of (new maximum FAR - old maximum FAR) over the given (eligible treatment) land."""
    t = table[[acres, old, new]].dropna()
    if t[acres].sum() <= 0:
        return float("nan")
    return float(((t[new] - t[old]) * t[acres]).sum() / t[acres].sum())


def far_from_height(height_ft: float, far_per_ft: float) -> float:
    """Allowed floor area ratio implied by a height limit, at a fixed FAR per foot of height."""
    return height_ft * far_per_ft


def far_from_density(units_per_acre: float, sqft_per_unit: float) -> float:
    """Allowed residential floor area ratio implied by a homes-per-acre cap."""
    return units_per_acre * sqft_per_unit / 43_560.0


# --------------------------------------------------------------------------- geometry helpers

def assign_areas(parcels, treated: pd.Series, in_city: pd.Series | None = None, stations=None,
                 ring_m: float = QUARTER_MILE_M, station_m: float = HALF_MILE_M) -> pd.Series:
    """Area label for each parcel (GeoDataFrame in metres): treatment, comparison, second_comparison or None.

    Comparison: not treated, representative point within ring_m of the treated parcels.
    Second comparison: not treated or comparison, representative point within station_m of a station whose own
    station_m circle contains no treated land (stations: GeoSeries of points in the same CRS)."""
    import geopandas as gpd  # noqa: F401
    treated = treated.astype(bool)
    in_city = pd.Series(True, index=parcels.index) if in_city is None else in_city.astype(bool)
    pts = parcels.geometry.representative_point()
    tunion = parcels.loc[treated].geometry.make_valid().union_all()
    area = pd.Series(None, index=parcels.index, dtype=object)
    area[treated] = TREAT
    near = pts.within(tunion.buffer(ring_m)) & ~treated & in_city
    area[near] = COMP
    if stations is not None and len(stations):
        keep = stations_not_upzoned(stations, tunion, station_m)
        if len(keep):
            zone = keep.buffer(station_m).union_all()
            sec = pts.within(zone) & area.isna() & in_city
            area[sec] = COMP2
    return area


def weighted_median(values: pd.Series, weights: pd.Series) -> float:
    v = pd.DataFrame({"v": values, "w": weights}).dropna().sort_values("v")
    if v.empty or v["w"].sum() <= 0:
        return float("nan")
    c = v["w"].cumsum() / v["w"].sum()
    return float(v.loc[c >= 0.5, "v"].iloc[0])


def uniform_areas(parcels, in_reform: pd.Series, rose: pd.Series, level_before: pd.Series, level_after: pd.Series,
                  uncapped_before: pd.Series, changed_outside: pd.Series, eligible: pd.Series,
                  in_city: pd.Series | None = None, stations=None) -> tuple[pd.Series, dict]:
    """Areas under the uniform rule (CASE_ANALYSIS_PLAN.md section 7, change of 2026-10-26; AQ-047 item 8).

    - Already at the law: the lot's zoning before had no separate homes-per-acre cap and allowed at least the
      acre-weighted median allowed level (FAR, or height where a case has no FAR) of the reform's new zoning on
      eligible land whose allowed density rose. Such land is in no area.
    - Treatment: lots inside the reform whose allowed density rose and that were not already at the law.
    - Lots inside the reform whose density did not rise, and lots whose zoning changed outside the reform during the
      before-to-after window (`changed_outside`), are in no area.
    - Comparison and second comparison: as in assign_areas, among the remaining lots (allowed density unchanged).
    Levels: use +inf for "no limit"."""
    in_reform, rose = in_reform.astype(bool), rose.astype(bool)
    acres = parcels.geometry.area / SQM_PER_ACRE
    base = in_reform & rose & eligible.astype(bool)
    med = weighted_median(level_after[base].replace(np.inf, np.nan).fillna(1e9), acres[base])
    at_law = uncapped_before.astype(bool) & (level_before.fillna(-1) >= med)
    treated = in_reform & rose & ~at_law & ~changed_outside.astype(bool)
    excluded = (in_reform & ~treated) | at_law | changed_outside.astype(bool)
    city = pd.Series(True, index=parcels.index) if in_city is None else in_city.astype(bool)
    area = assign_areas(parcels, treated, in_city=city & ~excluded, stations=stations)
    area[excluded] = None
    info = {"median_new_level_on_rising_land": med,
            "acres_already_at_law": round(float(acres[at_law & eligible.astype(bool)].sum()), 1),
            "acres_changed_outside_reform": round(float(acres[changed_outside.astype(bool) & eligible.astype(bool)].sum()), 1),
            "acres_in_reform_not_treated": round(float(acres[in_reform & ~treated & eligible.astype(bool)].sum()), 1)}
    return area, info


def stations_not_upzoned(stations, treated_union, station_m: float = HALF_MILE_M):
    """Stations whose station_m circle contains no treated land."""
    return stations[stations.distance(treated_union) > station_m]


def locate_points(points, parcels, max_m: float = 30.0) -> pd.Series:
    """Index of the parcel containing each point; points in no parcel (address points on the street frontage)
    take the nearest parcel within max_m metres. NaN when none."""
    import geopandas as gpd
    pp = parcels[["geometry"]]
    w = gpd.sjoin(points[["geometry"]], pp, how="left", predicate="within")
    w = w[~w.index.duplicated()]
    ix = w["index_right"].reindex(points.index)
    miss = ix.isna()
    if miss.any():
        n = gpd.sjoin_nearest(points.loc[miss, ["geometry"]], pp, how="left", max_distance=max_m)
        n = n[~n.index.duplicated()]
        ix.loc[miss] = n["index_right"].reindex(points.index[miss]).values
    return ix


def homes_by_area(blocks, parcels_area) -> dict[str, float]:
    """Existing homes per area: census block housing units whose internal point falls in a labelled parcel.

    blocks: GeoDataFrame of points with column 'homes'; parcels_area: GeoDataFrame with column 'area'."""
    import geopandas as gpd
    j = gpd.sjoin(blocks[["homes", "geometry"]], parcels_area[["area", "geometry"]].dropna(subset=["area"]),
                  how="inner", predicate="within")
    j = j[~j.index.duplicated()]
    return {a: float(v) for a, v in j.groupby("area")["homes"].sum().items()}


# --------------------------------------------------------------------------- one case end to end

@dataclass
class CaseInputs:
    case: str
    role: str                      # fit / medium / heldout / context / mandate
    effective_year: int
    first_year: int                # first full year of permit data
    last_full_year: int            # last full year of permit data
    permits: pd.DataFrame          # project, area, year, units (eligible parcels only)
    acres: dict                    # eligible acres by area
    homes: dict                    # existing homes by area (for the per-1,000-homes sensitivity)
    dose_table: pd.DataFrame | None  # treatment eligible land: acres, old_far, new_far
    parking_change: str = ""
    mandate: str = ""
    median_rent: float | None = None
    has_units: bool = True
    is_permits: bool = True
    notes: str = ""
    extra: dict = field(default_factory=dict)
    dose_unit: str = "far"         # "far", or "height_ft" when no defensible FAR conversion exists (Charlotte)
    original_spec: tuple | None = None  # (permits, acres) under the original area rule, for the sensitivity column
    status_override: str | None = None  # e.g. "context_only: no permit source with unit counts"
    measure: str = "units per eligible acre per year"  # or "permits per eligible acre per year" (counts, not homes)


def _fmt(x: float, nd: int = 4) -> float | None:
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), nd)


def estimate_case(ci: CaseInputs, draws: int = N_DRAWS, seed: int = SEED) -> tuple[pd.DataFrame, dict]:
    """Rates by year (all areas, before/year 0/after) and the case's estimate row."""
    if ci.role not in ROLES:
        raise ValueError(f"unknown role {ci.role}")
    per = period_years(ci.effective_year, ci.first_year, ci.last_full_year)
    before, after = per["before"], per["after"]
    status = ci.status_override or case_status(before, after, ci.has_units, ci.is_permits)
    yrs = before + per["year0"] + after
    rates = rates_by_year(ci.permits, ci.acres, yrs)
    rates.insert(0, "case", ci.case)
    rates["period"] = rates["year"].map(lambda y: "before" if y in before else ("year0" if y == ci.effective_year else "after"))
    rates["status"] = status
    rates = rates.rename(columns={"denominator": "eligible_acres"})
    if status == "measured" and ci.measure.startswith("permits"):
        status = "context_permit_count"
    role = ci.role if status == "measured" or ci.role == "heldout" else "context"
    row: dict = {"case": ci.case, "role": role, "planned_role": ci.role, "status": status, "measure": ci.measure, "effective_year": ci.effective_year,
                 "before_years": f"{before[0]} to {before[-1]}" if before else "", "after_years": f"{after[0]} to {after[-1]}" if after else "",
                 "treatment_acres": _fmt(ci.acres.get(TREAT), 1), "comparison_acres": _fmt(ci.acres.get(COMP), 1),
                 "second_comparison_acres": _fmt(ci.acres.get(COMP2), 1)}
    d_raw = dose(ci.dose_table) if ci.dose_table is not None and len(ci.dose_table) else float("nan")
    d = d_raw if ci.dose_unit == "far" else float("nan")
    d_ft = d_raw if ci.dose_unit == "height_ft" else float("nan")
    est = {"did": float("nan"), "treat_before": float("nan"), "treat_after": float("nan"), "comp_before": float("nan"), "comp_after": float("nan")}
    lo = hi = float("nan")
    if before and after and ci.acres.get(TREAT) and ci.acres.get(COMP) and (not ci.status_override or ci.status_override == "context_permit_count"):
        est = did(ci.permits, ci.acres, before, after)
        lo, hi, _ = bootstrap_did(ci.permits, ci.acres, before, after, draws=draws, seed=seed)
    row.update({"treat_rate_before": _fmt(est["treat_before"]), "treat_rate_after": _fmt(est["treat_after"]),
                "comp_rate_before": _fmt(est["comp_before"]), "comp_rate_after": _fmt(est["comp_after"]),
                "estimate_units_per_acre_yr": _fmt(est["did"]), "interval90_low": _fmt(lo), "interval90_high": _fmt(hi),
                "dose_added_far": _fmt(d, 3)})
    epd = est["did"] / d if d and not np.isnan(d) and d != 0 else float("nan")
    row.update({"effect_per_dose": _fmt(epd), "effect_per_dose_low": _fmt(lo / d if d else float("nan")),
                "effect_per_dose_high": _fmt(hi / d if d else float("nan")),
                "dose_added_height_ft": _fmt(d_ft, 1),
                "effect_per_added_ft": _fmt(est["did"] / d_ft if d_ft else float("nan"), 5),
                "effect_per_added_ft_low": _fmt(lo / d_ft if d_ft else float("nan"), 5),
                "effect_per_added_ft_high": _fmt(hi / d_ft if d_ft else float("nan"), 5)})
    # sensitivities
    s2 = float("nan")
    if before and after and ci.acres.get(COMP2):
        s2 = did(ci.permits, ci.acres, before, after, comp=COMP2)["did"]
    sdrop = float("nan")
    if before and after and ci.acres.get(TREAT) and ci.acres.get(COMP):
        sdrop = did(drop_largest_project(ci.permits, before, after), ci.acres, before, after)["did"]
    sh = float("nan")
    if before and after and ci.homes.get(TREAT) and ci.homes.get(COMP):
        sh = did(ci.permits, ci.homes, before, after, scale=1000.0)["did"]
    so = float("nan")
    if before and after and ci.original_spec is not None:
        op, oa = ci.original_spec
        if oa.get(TREAT) and oa.get(COMP):
            so = did(op, oa, before, after)["did"]
    row.update({"sens_original_spec": _fmt(so), "sens_second_comparison": _fmt(s2), "sens_drop_largest": _fmt(sdrop),
                "sens_per_1000_homes": _fmt(sh), "treatment_homes": _fmt(ci.homes.get(TREAT), 0),
                "comparison_homes": _fmt(ci.homes.get(COMP), 0),
                "treatment_units_before": _fmt(ci.permits[(ci.permits.area == TREAT) & ci.permits.year.isin(before)].units.sum(), 0),
                "treatment_units_after": _fmt(ci.permits[(ci.permits.area == TREAT) & ci.permits.year.isin(after)].units.sum(), 0),
                "comparison_units_before": _fmt(ci.permits[(ci.permits.area == COMP) & ci.permits.year.isin(before)].units.sum(), 0),
                "comparison_units_after": _fmt(ci.permits[(ci.permits.area == COMP) & ci.permits.year.isin(after)].units.sum(), 0),
                "parking_change": ci.parking_change, "mandate": ci.mandate, "median_rent": ci.median_rent, "notes": ci.notes})
    row.update(ci.extra)
    return rates, row


# --------------------------------------------------------------------------- across cases

def fit_set(estimates: pd.DataFrame) -> pd.DataFrame:
    """Cases that may enter a fit or a comparison of designs: role 'fit' and status 'measured'.
    Held-out, medium, mandate and context cases never enter."""
    return estimates[(estimates["role"] == "fit") & (estimates["status"] == "measured")]


def fit_set_summary(estimates: pd.DataFrame) -> dict:
    f = fit_set(estimates)
    e = f["effect_per_dose"].dropna()
    return {"cases": list(f["case"]), "n": int(len(f)), "median_effect_per_dose": float(e.median()) if len(e) else float("nan")}


def pooled_ramp(event_rows: pd.DataFrame, estimates: pd.DataFrame) -> pd.DataFrame:
    """Mean gap (treatment minus comparison, less its before mean) by event year 0..5 over the fit set only."""
    cases = set(fit_set(estimates)["case"])
    e = event_rows[event_rows["case"].isin(cases) & event_rows["event_year"].between(0, 5)]
    return e.groupby("event_year")["gap_minus_before"].agg(["mean", "count"]).reset_index()
