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

Pure arithmetic on pandas tables. Geometry helpers take polygon features in a metre CRS (the missing_middleware.geom
model: a feature is a list of parts, each a list of rings, each an (n, 2) array) and use numpy/scipy only
(missing_middleware/geom_extra_tod.py; docs/GEOMETRY.md).
"""
from __future__ import annotations

import inspect
from typing import Mapping

import numpy as np
import pandas as pd

from missing_middleware import geom_extra_tod as X
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
    acres = C.parcel_acres(parcels)
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
    # distance to the union of the treated lots = distance to the nearest treated lot (0 inside any of them)
    from missing_middleware.geom_extra_station import distance_within
    rx, ry = C.rep_xy(parcels)
    dist = pd.Series(distance_within(rx.to_numpy(float), ry.to_numpy(float), list(parcels.loc[tr, "geometry"]), np.inf),
                     index=parcels.index)
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

def area(feature, tile: float = 250.0) -> float:
    """Planar area of the land a polygon feature covers: the union of its parts (holes subtracted). The features here
    are groups of lots, and lots can overlap (stacked or overlapping parcel outlines in Saint Paul, Chicago and
    Charlotte), so parts are not simply summed: where parts' boxes overlap, the union's area is integrated over small
    tiles (geom_extra_tod.region_area_by_tiles)."""
    if not feature:
        return 0.0
    if len(feature) == 1:
        return float(X.areas([feature])[0])
    from missing_middleware.geom_extra_station import feature_bounds
    parts = [[p] for p in feature]
    b = feature_bounds(parts)
    o = np.lexsort((b[:, 1], b[:, 0]))
    b = b[o]
    # any two parts whose boxes overlap with positive area? (sweep over x)
    overlap = False
    run = []
    for i in range(len(b)):
        run = [j for j in run if b[j, 2] > b[i, 0]]
        if any(b[j, 3] > b[i, 1] and b[i, 3] > b[j, 1] for j in run):
            overlap = True
            break
        run.append(i)
    if not overlap:
        return float(X.areas([feature])[0])
    x0, y0, x1, y1 = b[:, 0].min(), b[:, 1].min(), b[:, 2].max(), b[:, 3].max()
    box = [[np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])]]
    return float(X.region_area_by_tiles([box], X.Polygons(parts), tile=tile)[0])


def patches(geoms, close_m: float = PATCH_CLOSE_M) -> list:
    """Connected pieces of a set of lots: lots within close_m of each other are one piece (streets between facing
    lots are bridged). Returns one polygon feature per piece holding its lots' own outlines (the original land, not
    the closed outline). Lots are taken not to overlap; identical outlines count once."""
    seen, lots = set(), []
    for f in geoms:
        if not f:
            continue
        k = X.feature_key(f)
        if k not in seen:
            seen.add(k)
            lots.append(f)
    return [[part for i in grp for part in lots[i]] for grp in X.components_within(lots, close_m)]


def rect_sides(geom) -> tuple[float, float]:
    """(long side, short side) of the minimum rotated (minimum-area) rectangle, metres."""
    if not geom:
        return 0.0, 0.0
    return X.min_area_rectangle_sides(np.concatenate([r for part in geom for r in part]))


def elongation(geom) -> float:
    """Length / average width of the upzoned patch: length = long side of the minimum rotated rectangle; average
    width = patch area / length. A disc scores 4/pi (about 1.27); a 1 x 10 strip scores 10."""
    a = area(geom)
    if not geom or a <= 0:
        return float("nan")
    L, _ = rect_sides(geom)
    return float(L * L / a) if L > 0 else float("nan")


def corridor_share(geoms, min_len_m: float = CORRIDOR_MIN_M, close_m: float = PATCH_CLOSE_M) -> float:
    """Share of the land's area lying in pieces at least min_len_m long (minimum-rotated-rectangle long side)."""
    ps = patches(geoms, close_m)
    tot = sum(area(p) for p in ps)
    if tot <= 0:
        return float("nan")
    return float(sum(area(p) for p in ps if rect_sides(p)[0] >= min_len_m) / tot)


def largest_contiguous_site_acres(geoms, touch_m: float = TOUCH_M) -> float:
    """Acres of the largest group of touching lots (lots within touch_m of each other)."""
    ps = patches(geoms, close_m=touch_m)
    return float(max((area(p) for p in ps), default=0.0) / C.SQM_PER_ACRE)


def island_acres(unit_geom, patches_tbl, area_col: str = "patch_acres") -> float:
    """Acres of the covered patch the unit sits in: the patch overlapping most of the unit's land; 0 when the unit's
    land lies outside every covered patch. patches_tbl: a table with a 'poly' column (polygon features, same CRS as
    the unit) and area_col."""
    if not unit_geom or patches_tbl is None or not len(patches_tbl):
        return float("nan")
    from missing_middleware.geom_extra_station import feature_bounds
    parts = [[p] for p in unit_geom]          # the unit's lots as their union (lots may overlap)
    ub = feature_bounds([unit_geom])[0]
    pb = feature_bounds(list(patches_tbl["poly"]))
    box = [[np.array([(ub[0], ub[1]), (ub[2], ub[1]), (ub[2], ub[3]), (ub[0], ub[3]), (ub[0], ub[1])])]]
    ov = np.zeros(len(patches_tbl))
    for i, p in enumerate(patches_tbl["poly"]):
        if p and pb[i, 0] <= ub[2] and pb[i, 2] >= ub[0] and pb[i, 1] <= ub[3] and pb[i, 3] >= ub[1]:
            ov[i] = X.region_area_by_tiles([box], X.Polygons(parts) & X.Polygons([p]), tile=250.0)[0]
    if ov.max() <= 0:
        return 0.0
    return float(patches_tbl[area_col].iloc[int(np.argmax(ov))])


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
