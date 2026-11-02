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
pandas frames with polygon features (missing_middleware.geom's model) in a projected CRS measured in metres.
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
# Geometry is held in plain pandas frames (no geopandas: the contest allows permissive licences only): a parcel frame
# has a column "geometry" of polygon features (missing_middleware.geom's model: list of parts, each a list of rings)
# in a metre CRS, and optionally "rx"/"ry", its representative points (GEOS's point on surface, computed here when
# absent); point sets (stations, permits, blocks) are frames with "x" and "y" columns, or an (x, y) pair of arrays.

def xy(points) -> tuple[np.ndarray, np.ndarray]:
    """x and y arrays of a point frame (columns x, y) or an (x, y) pair."""
    if points is None:
        return np.zeros(0), np.zeros(0)
    if isinstance(points, pd.DataFrame):
        return points["x"].to_numpy(float), points["y"].to_numpy(float)
    x, y = points
    return np.asarray(x, float), np.asarray(y, float)


def subset_points(points, mask):
    """Rows of a point frame or (x, y) pair."""
    m = np.asarray(mask, bool)
    if isinstance(points, pd.DataFrame):
        return points[m]
    x, y = xy(points)
    return x[m], y[m]


def rep_xy(parcels: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Representative points (GEOS point on surface) of a parcel frame, as Series on its index; cached in rx/ry."""
    if "rx" not in parcels.columns or "ry" not in parcels.columns:
        from missing_middleware.geom_extra_station import interior_points
        x, y = interior_points(list(parcels["geometry"]))
        parcels["rx"], parcels["ry"] = x, y
    return parcels["rx"], parcels["ry"]


def parcel_acres(parcels: pd.DataFrame) -> pd.Series:
    from missing_middleware.geom_extra_station import areas
    return pd.Series(areas(list(parcels["geometry"])) / SQM_PER_ACRE, index=parcels.index)


def within_distance(px, py, polys: list, d: float) -> np.ndarray:
    """Points inside the polygons' union buffered by d metres, with GEOS's segmented round corners
    (geom_extra_station.within_buffer_geos)."""
    from missing_middleware.geom_extra_station import within_buffer_geos
    if not len(polys):
        return np.zeros(len(px), bool)
    return within_buffer_geos(px, py, polys, d)


def read_parcels(path, crs_m, dedupe: str | None = None, columns: list[str] | None = None, make_valid: bool = False,
                 keep=None) -> pd.DataFrame:
    """Parcel layer as a parcel frame in crs_m: empty shapes dropped, one row per `dedupe` id (first kept), rows kept by
    the optional `keep(frame)` mask, index 0..n-1, with acres (GEOS area) and representative points rx, ry.
    make_valid: repair nested rings first (geom_extra_station.make_valid_nested), as GEOS make_valid did."""
    from missing_middleware.geom_extra_station import make_valid_nested, nonempty, read_vector
    g = read_vector(path, crs_m, columns=columns)
    g = g[nonempty(g["geometry"])]
    if dedupe:
        g = g.drop_duplicates(dedupe)
    if keep is not None:
        g = g[keep(g)]
    g = g.reset_index(drop=True)
    if make_valid:
        g["geometry"] = make_valid_nested(list(g["geometry"]))
    g["acres"] = parcel_acres(g)
    rep_xy(g)
    return g


def polygons(path, crs_m, columns: list[str] | None = None, make_valid: bool = False) -> pd.DataFrame:
    """Any polygon layer (zoning, rezonings) as a frame with "geometry" in crs_m (make_valid: nested rings repaired,
    as GEOS make_valid did)."""
    from missing_middleware.geom_extra_station import make_valid_nested, read_vector
    g = read_vector(path, crs_m, columns=columns)
    if make_valid:
        g["geometry"] = make_valid_nested(list(g["geometry"]))
    return g


def points(path, crs_m, columns: list[str] | None = None) -> pd.DataFrame:
    """A point layer as a frame with x, y in crs_m."""
    from missing_middleware.geom_extra_station import read_vector
    return read_vector(path, crs_m, columns=columns)


def points_from_lonlat(df: pd.DataFrame, lon, lat, crs_m, src=4326) -> pd.DataFrame:
    """df with x, y (crs_m) from coordinate columns (or arrays) in src."""
    from missing_middleware.geom_extra_station import transform
    lo = df[lon] if isinstance(lon, str) else lon
    la = df[lat] if isinstance(lat, str) else lat
    x, y = transform(np.asarray(lo, float), np.asarray(la, float), src, crs_m)
    return df.assign(x=x, y=y)


def join_within(parcels: pd.DataFrame, layer: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Attributes of the first polygon of `layer` holding each parcel's representative point (sjoin 'within', first
    match kept); NaN where none. Indexed like parcels."""
    from missing_middleware.geom_extra_station import first_within
    rx, ry = rep_xy(parcels)
    k = first_within(rx.to_numpy(), ry.to_numpy(), list(layer["geometry"]))
    hit = k >= 0
    out = pd.DataFrame(index=parcels.index)
    for c in cols:
        src = layer[c].reset_index(drop=True)
        v = src.iloc[np.maximum(k, 0)].reset_index(drop=True) if len(src) else pd.Series([np.nan] * len(k))
        v = v.where(pd.Series(hit), np.nan)
        out[c] = v.infer_objects().to_numpy()
    return out


def in_any(px, py, layer) -> np.ndarray:
    """Points inside any polygon of a frame (or list of features): `within(union_all())`, so the parts of a feature
    count as their union (a nested shell does not cut a hole)."""
    from missing_middleware.geom_extra_station import first_within
    polys = list(layer["geometry"]) if isinstance(layer, pd.DataFrame) else list(layer)
    if not polys:
        return np.zeros(len(px), bool)
    return first_within(np.asarray(px, float), np.asarray(py, float), polys, union=True) >= 0


def block_points(zip_path, el: pd.DataFrame, crs_m) -> pd.DataFrame:
    """2010 census blocks (HOUSING10) read within the envelope of the given parcels (bbox in the file's NAD83
    coordinates, as GDAL's bbox read), as representative points in crs_m with column homes."""
    from missing_middleware.geom_extra_station import (bbox_to, feature_bounds, interior_points, polys_to_crs,
                                                         read_vector)
    b = feature_bounds(list(el["geometry"]))
    env = (np.nanmin(b[:, 0]), np.nanmin(b[:, 1]), np.nanmax(b[:, 2]), np.nanmax(b[:, 3]))
    g = read_vector(zip_path, None, columns=["HOUSING10"], bbox=bbox_to(env, crs_m, 4269))
    polys = polys_to_crs(list(g["geometry"]), g.attrs["crs"], crs_m)
    x, y = interior_points(polys)
    return pd.DataFrame({"homes": g["HOUSING10"].to_numpy(), "x": x, "y": y})


def assign_areas(parcels, treated: pd.Series, in_city: pd.Series | None = None, stations=None,
                 ring_m: float = QUARTER_MILE_M, station_m: float = HALF_MILE_M) -> pd.Series:
    """Area label for each parcel (frame with polygon "geometry" in metres): treatment, comparison, second_comparison
    or None.

    Comparison: not treated, representative point within ring_m of the treated parcels.
    Second comparison: not treated or comparison, representative point within station_m of a station whose own
    station_m circle contains no treated land (stations: point frame or (x, y) in the same CRS)."""
    from missing_middleware.geom_extra_station import within_point_buffers
    treated = treated.astype(bool)
    in_city = pd.Series(True, index=parcels.index) if in_city is None else in_city.astype(bool)
    rx, ry = rep_xy(parcels)
    tpolys = list(parcels.loc[treated, "geometry"])
    area = pd.Series(None, index=parcels.index, dtype=object)
    area[treated] = TREAT
    near = pd.Series(within_distance(rx.to_numpy(), ry.to_numpy(), tpolys, ring_m), index=parcels.index) & ~treated & in_city
    area[near] = COMP
    if stations is not None and len(xy(stations)[0]):
        keep = stations_not_upzoned(stations, tpolys, station_m)
        kx, ky = xy(keep)
        if len(kx):
            inz = within_point_buffers(rx.to_numpy(), ry.to_numpy(), kx, ky, station_m)
            sec = pd.Series(inz, index=parcels.index) & area.isna() & in_city
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
    acres = parcel_acres(parcels)
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


def stations_not_upzoned(stations, treated_polys, station_m: float = HALF_MILE_M):
    """Stations whose station_m circle contains no treated land (treated_polys: list of polygon features, or a parcel
    frame). Returns the same kind of object as `stations`."""
    from missing_middleware.geom_extra_station import distance_within
    if isinstance(treated_polys, pd.DataFrame):
        treated_polys = list(treated_polys["geometry"])
    sx, sy = xy(stations)
    if not len(treated_polys):                  # distance to an empty union is undefined: no station qualifies
        return subset_points(stations, np.zeros(len(sx), bool))
    d = distance_within(sx, sy, list(treated_polys), station_m)
    return subset_points(stations, d > station_m)


def locate_points(points, parcels, max_m: float = 30.0) -> pd.Series:
    """Index of the parcel containing each point; points in no parcel (address points on the street frontage)
    take the nearest parcel within max_m metres. NaN when none. points: point frame (index kept)."""
    from missing_middleware.geom_extra_station import nearest_polygon
    px, py = xy(points)
    pos, _ = nearest_polygon(px, py, list(parcels["geometry"]), max_m)
    lab = np.where(pos >= 0, parcels.index.to_numpy()[np.maximum(pos, 0)], np.nan).astype(float)
    return pd.Series(lab, index=points.index)


def homes_by_area(blocks, parcels_area) -> dict[str, float]:
    """Existing homes per area: census block housing units whose internal point falls in a labelled parcel.

    blocks: point frame with column 'homes'; parcels_area: parcel frame with columns 'area' and 'geometry'."""
    from missing_middleware.geom_extra_station import first_within
    pa = parcels_area.dropna(subset=["area"])
    bx, by = xy(blocks)
    k = first_within(bx, by, list(pa["geometry"]))
    hit = k >= 0
    if not hit.any():
        return {}
    s = pd.Series(blocks["homes"].to_numpy()[hit]).groupby(pa["area"].to_numpy()[k[hit]]).sum()
    return {a: float(v) for a, v in s.items()}


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
    if before and after and ci.acres.get(TREAT) and ci.acres.get(COMP) and (not ci.status_override or ci.status_override.startswith(("context_permit_count", "context_only"))):
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
