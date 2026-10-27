"""TOD net effect, borrowing and coverage (docs/tod/NET_EFFECT_PLAN.md, written before any comparison was computed).

- Areas (plan section 2), per case, under the case's own eligible-land and area rules (cases.uniform_areas):
  treatment (as before); ring = the case's comparison area (unchanged land within 1/4 mile of the treatment); far
  land = unchanged eligible land in the same city whose representative point is more than 1/4 mile and at most
  1 1/2 miles from the treated land. Land the uniform rule puts in no area (rezoned outside the reform, already at the
  law, inside the reform but not risen) is never far land.
- Borrowing (section 3): difference-in-differences of the ring against far land, homes permitted per eligible acre
  per year, after against before. Negative = building moved out of the ring.
- Net effect: (treatment DiD against far land x treatment acres) + (ring DiD against far land x ring acres), extra
  homes per year. Divided by the city's housing stock it is the citywide net share.
- Uncertainty: 90% intervals from resampling projects within each area of each case, 2,000 draws, seed 20261027.
- Unit traits (sections 4 and 8): island size (area of the continuous covered patch a unit sits in), largest
  contiguous eligible site, elongation, corridor share, binding limit. Judged in scripts/run_tod_net_effect.py with
  the trait test's tools (traits.judge_tools).

Pure arithmetic on pandas tables; geometry helpers take shapely/GeoPandas objects in a metre CRS.
"""
from __future__ import annotations

import inspect
import math
from typing import Mapping

import numpy as np
import pandas as pd

from missing_middleware.tod import cases as C

MILE_M = 1609.344
FAR_MIN_M = C.QUARTER_MILE_M
FAR_MAX_M = 1.5 * MILE_M
CORRIDOR_MIN_M = 0.5 * MILE_M
SEED = 20261027
N_DRAWS = 2000
LEVEL = 0.90
TREAT, RING, FAR = C.TREAT, C.COMP, "far"
AREAS3 = (TREAT, RING, FAR)
SQFT_PER_ACRE = 43_560.0
# Patches of upzoned land: lots closer than this are one patch (bridges streets up to 30 m, about a 100-foot right of
# way, between facing lots).
PATCH_CLOSE_M = 30.0
# Lots "touch" when they are within this distance (survey slivers between neighbouring lots).
TOUCH_M = 1.0


# --------------------------------------------------------------------------- areas

_UNIFORM = C.uniform_areas  # the original, for binding arguments while a caller wraps it

def excluded_by_uniform_rule(parcels, in_reform, rose, level_before, level_after, uncapped_before, changed_outside,
                             eligible, in_city=None, stations=None) -> pd.Series:
    """Lots the uniform rule (cases.uniform_areas) puts in no area: inside the reform but not treated, already at
    the law, or rezoned outside the reform. Mirrors cases.uniform_areas exactly."""
    in_reform, rose = in_reform.astype(bool), rose.astype(bool)
    acres = parcels.geometry.area / C.SQM_PER_ACRE
    base = in_reform & rose & eligible.astype(bool)
    med = C.weighted_median(level_after[base].replace(np.inf, np.nan).fillna(1e9), acres[base])
    at_law = uncapped_before.astype(bool) & (level_before.fillna(-1) >= med)
    changed = changed_outside.astype(bool)
    treated = in_reform & rose & ~at_law & ~changed
    return (in_reform & ~treated) | at_law | changed


def bind_uniform_args(*args, **kwargs) -> dict:
    """Arguments of a cases.uniform_areas call, by name."""
    b = inspect.signature(_UNIFORM).bind(*args, **kwargs)
    b.apply_defaults()
    return dict(b.arguments)


def far_land(parcels, area: pd.Series, excluded: pd.Series, eligible: pd.Series, in_city: pd.Series | None = None,
             near_m: float = FAR_MIN_M, far_m: float = FAR_MAX_M) -> tuple[pd.Series, pd.Series]:
    """(far mask, distance in metres to the treated land) for every lot. Far land: eligible, in the city, not
    excluded by the uniform rule, not treatment or ring, representative point more than near_m and at most far_m
    from the treated lots (all lots labelled treatment, as in cases.assign_areas)."""
    tr = area == TREAT
    if not tr.any():
        return pd.Series(False, index=parcels.index), pd.Series(np.nan, index=parcels.index)
    tunion = parcels.loc[tr].geometry.make_valid().union_all()
    pts = parcels.geometry.representative_point()
    dist = pts.distance(tunion)
    city = pd.Series(True, index=parcels.index) if in_city is None else in_city.astype(bool).reindex(parcels.index).fillna(False)
    lab = area.astype(object)
    m = eligible.astype(bool) & city & ~excluded.astype(bool) & ~lab.isin([TREAT, RING]) & (dist > near_m) & (dist <= far_m)
    return m, dist


def three_areas(area: pd.Series, far: pd.Series) -> pd.Series:
    """treatment / comparison (ring) / far / None."""
    out = area.where(area.isin([TREAT, RING]), None).astype(object)
    out[far.astype(bool)] = FAR
    return out


# --------------------------------------------------------------------------- estimates

def _mean_rate(units: Mapping, area: str, years: list[int], acres: float) -> float:
    if not years or not acres:
        return float("nan")
    return sum(units.get((area, y), 0.0) for y in years) / len(years) / acres


def net_estimate(permits: pd.DataFrame, acres: Mapping[str, float], before: list[int], after: list[int]) -> dict:
    """Rates (homes permitted per eligible acre per year), borrowing, treatment-vs-far DiD and net extra homes a year.

    permits: project, area (treatment / comparison / far), year, units."""
    u = permits.groupby(["area", "year"])["units"].sum().to_dict()
    r = {}
    for a in AREAS3:
        r[f"{a}_before"] = _mean_rate(u, a, before, acres.get(a, 0.0))
        r[f"{a}_after"] = _mean_rate(u, a, after, acres.get(a, 0.0))
    d = {a: r[f"{a}_after"] - r[f"{a}_before"] for a in AREAS3}
    r["treat_vs_far"] = d[TREAT] - d[FAR]
    r["ring_vs_far"] = d[RING] - d[FAR]          # borrowing
    r["treat_vs_ring"] = d[TREAT] - d[RING]       # the case's own estimate
    r["net_homes_per_year"] = r["treat_vs_far"] * acres.get(TREAT, 0.0) + r["ring_vs_far"] * acres.get(RING, 0.0)
    r["ring_homes_per_year"] = r["ring_vs_far"] * acres.get(RING, 0.0)
    r["treatment_homes_per_year"] = r["treat_vs_far"] * acres.get(TREAT, 0.0)
    return r


def _matrix(p: pd.DataFrame, years: list[int]) -> np.ndarray:
    proj = p.groupby(["project", "year"])["units"].sum().reset_index()
    keys = list(pd.unique(proj["project"]))
    mat = np.zeros((len(keys), len(years)))
    idx = {k: i for i, k in enumerate(keys)}
    cols = {y: j for j, y in enumerate(years)}
    for row in proj.itertuples(index=False):
        if row.year in cols:
            mat[idx[row.project], cols[row.year]] += row.units
    return mat


def bootstrap_net(permits: pd.DataFrame, acres: Mapping[str, float], before: list[int], after: list[int],
                  draws: int = N_DRAWS, seed: int = SEED) -> dict[str, np.ndarray]:
    """Draws of treat_vs_far, ring_vs_far and net_homes_per_year from resampling whole projects (with replacement)
    within each area; denominators fixed. Only projects with permits in the before or after years enter."""
    years = list(before) + list(after)
    p = permits[permits["year"].isin(years)]
    mats = {a: _matrix(p[p["area"] == a], years) for a in AREAS3}
    nb = len(before)
    rng = np.random.default_rng(seed)
    out = {k: np.empty(draws) for k in ("treat_vs_far", "ring_vs_far", "net_homes_per_year")}
    for i in range(draws):
        d = {}
        for a in AREAS3:
            m = mats[a]
            s = m[rng.integers(0, len(m), len(m))].sum(axis=0) if len(m) else np.zeros(len(years))
            ac = acres.get(a, 0.0)
            d[a] = (s[nb:].mean() - s[:nb].mean()) / ac if ac and nb and len(years) > nb else np.nan
        tf, rf = d[TREAT] - d[FAR], d[RING] - d[FAR]
        out["treat_vs_far"][i], out["ring_vs_far"][i] = tf, rf
        out["net_homes_per_year"][i] = tf * acres.get(TREAT, 0.0) + rf * acres.get(RING, 0.0)
    return out


def interval(draws: np.ndarray, level: float = LEVEL) -> tuple[float, float]:
    x = np.asarray(draws, dtype=float)
    x = x[~np.isnan(x)]
    if not len(x):
        return float("nan"), float("nan")
    lo, hi = np.quantile(x, [(1 - level) / 2, 1 - (1 - level) / 2])
    return float(lo), float(hi)


def stack_members(members: list[dict]) -> tuple[pd.DataFrame, dict]:
    """Stack rezonings in event time (as cases.build_pooled): year -> year - effective year, projects kept distinct
    per member, acres summed. Each member: {'id', 'effective_year', 'permits', 'acres'}."""
    ps, acres = [], {}
    for m in members:
        q = m["permits"].copy()
        q["year"] = q["year"] - m["effective_year"]
        q["project"] = str(m["id"]) + ":" + q["project"].astype(str)
        ps.append(q)
        for a, v in m["acres"].items():
            acres[a] = acres.get(a, 0.0) + v
    cols = ["project", "area", "year", "units"]
    return (pd.concat(ps, ignore_index=True)[cols] if ps else pd.DataFrame(columns=cols)), acres


# --------------------------------------------------------------------------- shapes

def patches(geoms, close_m: float = PATCH_CLOSE_M) -> list:
    """Connected pieces of a set of lots: lots within close_m of each other are one piece (streets between facing
    lots are bridged). Returns shapely polygons of the original land (not the closed outline)."""
    from shapely.ops import unary_union
    g = [x for x in geoms if x is not None and not x.is_empty]
    if not g:
        return []
    land = unary_union(g)
    grown = land.buffer(close_m / 2.0)
    parts = list(grown.geoms) if hasattr(grown, "geoms") else [grown]
    return [land.intersection(p) for p in parts]


def rect_sides(geom) -> tuple[float, float]:
    """(long side, short side) of the minimum rotated rectangle, metres."""
    r = geom.minimum_rotated_rectangle
    if r.geom_type != "Polygon":
        L = r.length / 2.0 if r.geom_type == "LineString" else 0.0
        return L, 0.0
    xy = list(r.exterior.coords)
    a = math.dist(xy[0], xy[1])
    b = math.dist(xy[1], xy[2])
    return max(a, b), min(a, b)


def elongation(geom) -> float:
    """Length / average width of the upzoned patch: length = long side of the minimum rotated rectangle; average
    width = patch area / length. A disc scores 4/pi (about 1.27); a 1 x 10 strip scores 10."""
    if geom is None or geom.is_empty or geom.area <= 0:
        return float("nan")
    L, _ = rect_sides(geom)
    return float(L * L / geom.area) if L > 0 else float("nan")


def corridor_share(geoms, min_len_m: float = CORRIDOR_MIN_M, close_m: float = PATCH_CLOSE_M) -> float:
    """Share of the land's area lying in pieces at least min_len_m long (minimum-rotated-rectangle long side)."""
    ps = patches(geoms, close_m)
    tot = sum(p.area for p in ps)
    if tot <= 0:
        return float("nan")
    return float(sum(p.area for p in ps if rect_sides(p)[0] >= min_len_m) / tot)


def largest_contiguous_site_acres(geoms, touch_m: float = TOUCH_M) -> float:
    """Acres of the largest group of touching lots (lots within touch_m of each other)."""
    ps = patches(geoms, close_m=touch_m)
    return float(max((p.area for p in ps), default=0.0) / C.SQM_PER_ACRE)


def island_acres(unit_geom, patches_gdf, area_col: str = "patch_acres") -> float:
    """Acres of the covered patch the unit sits in: the patch overlapping most of the unit's land; 0 when the unit's
    land lies outside every covered patch."""
    if unit_geom is None or unit_geom.is_empty or patches_gdf is None or not len(patches_gdf):
        return float("nan")
    ov = patches_gdf.geometry.intersection(unit_geom).area
    if ov.max() <= 0:
        return 0.0
    return float(patches_gdf.loc[ov.idxmax(), area_col])


def binding_ratio(homes_per_acre: float, old_far: pd.Series, acres: pd.Series, sqft_per_home: float) -> float:
    """Existing built density over the density allowed before the reform: homes per eligible acre before, divided by
    the homes per acre the old FAR allowed (acre-weighted mean old FAR x 43,560 / floor area per home). Lots without a
    finite, positive old FAR are left out of the allowed density. NaN when no lot has one."""
    f = pd.to_numeric(old_far, errors="coerce").astype(float)
    ok = np.isfinite(f) & (f > 0) & (acres > 0)
    if not ok.any() or homes_per_acre is None or not np.isfinite(homes_per_acre):
        return float("nan")
    allowed = float((f[ok] * acres[ok]).sum() / acres[ok].sum()) * SQFT_PER_ACRE / sqft_per_home
    return float(homes_per_acre / allowed) if allowed > 0 else float("nan")


def corridor_label(share: float) -> str:
    """'corridor' when at least half of the case's upzoned land lies in pieces at least 1/2 mile long."""
    if share is None or not np.isfinite(share):
        return ""
    return "corridor" if share >= 0.5 else "nodes"


# --------------------------------------------------------------------------- distant borrowing (check only)

def distant_check(beyond: Mapping[int, float], region: Mapping[int, float], before: list[int], after: list[int]) -> dict:
    """Homes permitted a year on land beyond 1 1/2 miles against the rest of the region (other counties of the metro).
    Ratio of growth: (beyond after / before) / (region after / before) - 1. Negative = the distant land grew less than
    the region (consistent with building drawn from it)."""
    def m(s, yrs):
        v = [s.get(y) for y in yrs]
        return float(np.mean(v)) if yrs and all(x is not None for x in v) else float("nan")
    bb, ba, rb, ra = m(beyond, before), m(beyond, after), m(region, before), m(region, after)
    g_b = ba / bb if bb else float("nan")
    g_r = ra / rb if rb else float("nan")
    return {"beyond_before": bb, "beyond_after": ba, "region_before": rb, "region_after": ra,
            "beyond_growth": g_b, "region_growth": g_r, "relative_growth_minus_1": g_b / g_r - 1 if g_r else float("nan")}
