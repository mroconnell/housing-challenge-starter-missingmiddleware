"""TOD net effect, borrowing and coverage (docs/tod/NET_EFFECT_PLAN.md), in the plan's order.

    uv run --all-extras python scripts/run_tod_net_effect.py --stage fetch     # ACS files for the car-dependence traits
    uv run --all-extras python scripts/run_tod_net_effect.py --stage areas [--case chicago ...]  # far land per case (cached)
    uv run --all-extras python scripts/run_tod_net_effect.py --stage net       # borrowing and net effect by case and city
    uv run --all-extras python scripts/run_tod_net_effect.py --stage traits    # unit traits (coverage, shape, binding) + test
    uv run --all-extras python scripts/run_tod_net_effect.py --stage distant   # distant-borrowing check (Census permits)

Each case's areas come from its own adapter (missing_middleware/tod/case_*.py, imported, never edited), run unchanged
while cases.uniform_areas and cases.locate_points (New York: case_nyc.locate_jobs) are wrapped to record the lots,
the rule's inputs and each permit's lot, as in scripts/run_tod_traits.py. Far land is then measured on those lots.
Where an adapter limits its work to a box or buffer smaller than 1 1/2 miles (New York 1,500 m, Philadelphia 2,000 m),
that one distance is widened to FAR_WORK_M while the adapter runs (plan section 8, deviation 1).

City coverage layers: scripts/build_tod_net_coverage.py (data/processed/tod_net_effect/coverage_*, coverage_cities.csv).

Outputs (committed; no parcel, permit, project or person identifiers):
- reference/tod_net_effect_by_case.csv   rates, borrowing, net homes a year, citywide net share, 90% intervals
- reference/tod_coverage_traits.csv      city coverage shares and corridor label; unit island size, largest site,
                                         elongation, corridor share, binding ratio
- reference/tod_net_traits_test.csv      unit traits under the trait-test rule (traits.judge_tools)
Caches (git-ignored): data/processed/tod_net_effect/ (areas_<case>.pkl: per member the treated and upzoned lots,
"treated_lots" / "upzoned_lots", lists of polygon features (missing_middleware.geom's model) standing for their union,
in the case's metre CRS, an EPSG code under "crs").
Geometry: missing_middleware.geom and its geom_extra_* helpers (no geopandas or shapely; docs/GEOMETRY.md).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pickle
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.paths import RAW, REFERENCE, processed_dir  # noqa: E402
from missing_middleware.tod import cases as C  # noqa: E402
from missing_middleware.tod import net_effect as NE  # noqa: E402
from missing_middleware.tod import traits as T  # noqa: E402

OUT = processed_dir("tod_net_effect")
BY_CASE_CSV = REFERENCE / "tod_net_effect_by_case.csv"
COVERAGE_CSV = REFERENCE / "tod_coverage_traits.csv"
TEST_CSV = REFERENCE / "tod_net_traits_test.csv"
FAR_WORK_M = 2700.0   # > 1 1/2 miles (2,414 m) plus a margin

CASES = {  # case id -> (city, adapter key, role in the trait test)
    "nyc_pooled_2003_2013": ("New York", "nyc", "fit"),
    "philadelphia_2012_remapping": ("Philadelphia", "philadelphia", "fit"),
    "charlotte_tod_2019": ("Charlotte", "charlotte", "fit"),
    "stpaul_green_line_2011": ("Saint Paul", "stpaul", "fit"),
    "la_warner_center_2013": ("Los Angeles", "la", "fit"),
    "la_cornfield_arroyo_seco_2013": ("Los Angeles", "la", "fit"),
    "seattle_nbh_othello_2012": ("Seattle", "seattle", "fit"),
    "seattle_mount_baker_2014": ("Seattle", "seattle", "fit"),
    "chicago_tod_2013_2015": ("Chicago", "chicago", "always held out"),
    "madison_tod_overlay_2023": ("Madison", "madison", "always held out"),
}
CITY_SLUG = {"New York": "new_york", "Philadelphia": "philadelphia", "Charlotte": "charlotte", "Saint Paul": "saint_paul",
             "Los Angeles": "los_angeles", "Seattle": "seattle", "Chicago": "chicago", "Madison": "madison"}


# =========================================================================== capture

@contextmanager
def capture(nyc=None):
    rec = {"uniform": [], "locate": [], "jobs": []}
    ou, ol = C.uniform_areas, C.locate_points

    def u(*a, **k):
        r = ou(*a, **k)
        rec["uniform"].append((NE.bind_uniform_args(*a, **k), r[0]))
        return r

    def loc(points, parcels, *a, **k):
        r = ol(points, parcels, *a, **k)
        rec["locate"].append((points, r))
        return r
    C.uniform_areas, C.locate_points = u, loc
    oj = None
    if nyc is not None:
        oj = nyc.locate_jobs

        def lj(jg, lots, *a, **k):
            r = oj(jg, lots, *a, **k)
            rec["jobs"].append((jg, r))
            return r
        nyc.locate_jobs = lj
    try:
        yield rec
    finally:
        C.uniform_areas, C.locate_points = ou, ol
        if nyc is not None:
            nyc.locate_jobs = oj


@contextmanager
def widen(distances: tuple[float, ...], to: float = FAR_WORK_M):
    """While active, the adapters' work distances in `distances` become `to`: cases.within_distance calls with that
    distance (Philadelphia's 2 km around a member), and New York's lot box (the member's bounds plus 1,500 m, drawn in
    case_nyc.build_member from geom_extra_station.feature_bounds), which grows by to - 1,500 m on every side."""
    import sys as _sys
    from missing_middleware import geom_extra_station as S
    from missing_middleware.tod import case_nyc as N
    ow, ofb = C.within_distance, S.feature_bounds

    def wd(px, py, polys, d):
        return ow(px, py, polys, to if d in distances else d)

    def fb(polys):
        b = ofb(polys)
        if 1500 in distances and _sys._getframe(1).f_code is N.build_member.__code__:
            g = to - 1500
            b = b + np.array([-g, -g, g, g])
        return b
    C.within_distance, S.feature_bounds = wd, fb
    try:
        yield
    finally:
        C.within_distance, S.feature_bounds = ow, ofb


def distinct(polys: list) -> list:
    """Non-empty polygon features with identical outlines kept once. A list of lots stands for their union: every
    use below treats a point as inside when it lies in any lot (no union is drawn, so no overlay error enters)."""
    from missing_middleware import geom_extra_tod as X
    seen, out = set(), []
    for f in polys:
        if not f:
            continue
        k = X.feature_key(f)
        if k not in seen:
            seen.add(k)
            out.append(f)
    return out


def region_acres(region, polys: list, pad: float) -> float:
    """Acres of a Region lying within `pad` metres of the polygons' bounding box (its whole area when it lies there)."""
    from missing_middleware import geom_extra_tod as X
    from missing_middleware.geom_extra_station import feature_bounds
    b = feature_bounds(polys)
    x0, y0 = np.nanmin(b[:, 0]) - pad - 1, np.nanmin(b[:, 1]) - pad - 1
    x1, y1 = np.nanmax(b[:, 2]) + pad + 1, np.nanmax(b[:, 3]) + pad + 1
    box = [[np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])]]
    return float(X.region_area_by_tiles([box], region).sum()) / C.SQM_PER_ACRE


def member_frame(mid, eff: int, per: dict, args: dict, area: pd.Series, lots, permits: pd.DataFrame, crs: int) -> dict:
    """Treatment, ring and far land of one case or stacked member. permits: project, year, units, pix (lot index).
    lots: parcel frame (polygon features in "geometry", metre CRS `crs`, an EPSG code)."""
    from missing_middleware import geom_extra_tod as X
    excl = NE.excluded_by_uniform_rule(**args)
    elig = args["eligible"].astype(bool).reindex(lots.index).fillna(False)
    far, dist = NE.far_land(lots, area, excl, elig, args.get("in_city"))
    lab = NE.three_areas(area.where(~excl, None), far)
    lab = lab.where(elig, None)
    lot_acres = C.parcel_acres(lots)
    acres = lot_acres.groupby(lab).sum().to_dict()
    p = permits.dropna(subset=["pix"]).copy()
    p["area"] = lab.reindex(p["pix"].astype(int)).values
    p = p[p["area"].notna()][["project", "area", "year", "units"]].copy()
    p["year"] = p["year"].astype(int)
    tr = list(lots.loc[area == C.TREAT, "geometry"])
    # how far out the adapter's lots reach: share of the 1/4-1 1/2 mile band (around the treated land) that has lots
    tlots = distinct(tr)
    reach = {}
    if tlots:
        band = X.Buffer(tlots, NE.FAR_MAX_M) - X.Buffer(tlots, NE.FAR_MIN_M)
        rx, ry = C.rep_xy(lots)
        inband = X.points_in_region(rx.to_numpy(float), ry.to_numpy(float), band)
        reach = {"band_acres": round(region_acres(band, tlots, NE.FAR_MAX_M), 1),
                 "lot_acres_in_band": round(float(lot_acres[inband].sum()), 1),
                 "max_lot_distance_m": round(float(dist.max()), 0)}
    up = (args["in_reform"].astype(bool) & args["rose"].astype(bool)).reindex(lots.index).fillna(False)
    upzoned = distinct(list(lots.loc[up, "geometry"]))
    return {"id": str(mid), "effective_year": int(eff), "upzoned_lots": upzoned, "per": {"before": list(per["before"]), "after": list(per["after"])},
            "permits": p, "acres": {k: float(v) for k, v in acres.items()}, "reach": reach,
            "treated_lots": tlots, "crs": int(crs), "excluded_acres": round(float(lot_acres[excl & elig].sum()), 1)}


def _permits_from_points(points, pix) -> pd.DataFrame:
    q = pd.DataFrame({"project": points["project"].astype(str).values, "year": pd.to_numeric(points["year"], errors="coerce").values,
                      "units": pd.to_numeric(points["units"], errors="coerce").values, "pix": pd.Series(pix).values})
    return q.dropna(subset=["year"])


def build_simple(key: str) -> list[dict]:
    """Charlotte, Chicago, Saint Paul: one uniform_areas call on citywide lots; permits from the last locate call."""
    mod = importlib.import_module(f"missing_middleware.tod.case_{key}")
    with capture() as cap:
        ci, _ = mod.build()
    args, area = cap["uniform"][0]
    lots = args["parcels"]
    pts, pix = cap["locate"][-1]
    per = C.period_years(ci.effective_year, ci.first_year, ci.last_full_year)
    return [member_frame(ci.case, ci.effective_year, per, args, area, lots, _permits_from_points(pts, pix), mod.CRS_M)]


def build_la(case: str) -> list[dict]:
    from missing_middleware.tod import case_la as K
    with capture() as cap:
        parcels, qg, per, eff, rule, stations = K._areas(case)
    args, area = cap["uniform"][0]
    q = _permits_from_points(qg, qg["pix"])
    return [member_frame(case, eff.year, per, args, area, args["parcels"], q, K.CRS_M)]


def build_seattle(case: str) -> list[dict]:
    from missing_middleware.tod import case_seattle as K
    with capture() as cap:
        f = K._frame(case)
    args, area = cap["uniform"][-1]
    pg = K._load()["permits"]
    return [member_frame(case, f["effective_year"], f["per"], args, area, args["parcels"], _permits_from_points(pg, pg["pix"]), K.CRS_M)]


def build_philadelphia() -> list[dict]:
    from missing_middleware.tod import case_philadelphia as P
    d = P._load()
    rm = d["rm"]
    dp = rm[(rm["Origination"] == "DistrictPlan") & rm["changes"] & rm["enacted"].dt.year.between(*P.MEMBER_YEARS)]
    out = []
    q = _permits_from_points(d["permits"], d["permits"]["pix"])
    for b in sorted(dp["Bill_Number_TXT"].astype(str).unique()):
        with capture() as cap, widen((2000,)):
            m = P.build_member(b)
        if not m["acres"].get(C.TREAT, 0) > 0:
            continue
        args, area = cap["uniform"][-1]
        out.append(member_frame(b, m["effective"].year, m["per"], args, area, args["parcels"], q, P.CRS_M))
    return out


def build_nyc() -> list[dict]:
    from missing_middleware.tod import case_nyc as N
    out = []
    for ulurp, (name, boro) in N.POOLED.items():
        with capture(nyc=N) as cap, widen((1500,)):
            try:
                m = N.build_member(ulurp, boro)
            except Exception as e:  # noqa: BLE001
                print(f"  {name}: {type(e).__name__}: {e}")
                continue
        per = m["per"]
        if not (len(per["before"]) == C.BEFORE_MAX and len(per["after"]) == len(C.AFTER_YEARS) and m["acres"].get(C.TREAT)):
            continue
        args, area = cap["uniform"][-1]
        jg, ix = cap["jobs"][-1]
        q = _permits_from_points(jg, ix)
        fr = member_frame(ulurp, m["effective_year"], per, args, area, args["parcels"], q, N.CRS_M)
        fr["name"] = name
        out.append(fr)
    return out


def build_madison() -> list[dict]:
    """The Madison test's areas and permits, as in run_tod_traits.build_madison (its own before and after years)."""
    spec = importlib.util.spec_from_file_location("run_tod_madison_test", ROOT / "scripts" / "run_tod_madison_test.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    from missing_middleware.permits import madison
    from missing_middleware.permits.match import AddressIndex
    from missing_middleware.tod import madison_test as MT
    L = M.lots()
    # the lot table holds outlines in 'poly' and GEOS interior points in px, py (EPSG:3071); the case helpers read
    # 'geometry' and cached representative points rx, ry (as run_tod_traits.build_madison)
    L["geometry"], L["rx"], L["ry"] = L["poly"], L["px"], L["py"]
    parcels_tbl = madison.parcel_table(madison.load_parcels(RAW / "madison_parcels"))
    ref = madison.address_reference(parcels_tbl, madison.load_address_points(RAW / "madison_parcels"))
    index = AddressIndex(ref)
    ref_pts = M.ref_points(index.ref)
    changed, _ = M.rezoned_lots(L, index, ref_pts)
    L["changed"] = changed
    args = NE.bind_uniform_args(L, in_reform=L.in_overlay, rose=L.rose, level_before=L.far_base, level_after=L.far_ovl,
                                uncapped_before=L.uncapped, changed_outside=L.changed, eligible=L.elig)
    area, _ = C.uniform_areas(**args)
    L["area"] = area
    L["eligible"] = L["elig"]
    d = M.permits_on_lots(L, index, ref_pts, parcels_tbl)
    x = d[d.placed].copy()
    q = pd.DataFrame({"project": x["project"].astype(str), "year": x["year"], "units": x["units"], "pix": x["lot"].astype(int)})
    per = {"before": list(MT.BEFORE), "after": list(MT.AFTER)}
    fr = member_frame("madison_tod_overlay_2023", 2023, per, args, area, L, q, M.CRS_M)
    # placed permits at their lots' representative points (EPSG:3071), for the distant check
    cw = pd.DataFrame({"year": q["year"].values, "units": q["units"].values,
                       "x": L["rx"].reindex(q["pix"]).values, "y": L["ry"].reindex(q["pix"]).values})
    cw.attrs["crs"] = int(M.CRS_M)
    cw.to_pickle(OUT / "madison_citywide.pkl")
    return [fr]


def builder(case: str):
    key = CASES[case][1]
    if key in ("charlotte", "chicago", "stpaul"):
        return lambda: build_simple(key)
    if key == "la":
        return lambda: build_la(case)
    if key == "seattle":
        return lambda: build_seattle(case)
    return {"philadelphia": build_philadelphia, "nyc": build_nyc, "madison": build_madison}[key]


def stage_areas(cases: list[str], rebuild: bool) -> None:
    for c in cases:
        f = OUT / f"areas_{c}.pkl"
        if f.exists() and not rebuild:
            print(f"{c}: cached")
            continue
        print(f"== {c}", flush=True)
        members = builder(c)()
        f.write_bytes(pickle.dumps(members))
        a = {}
        for m in members:
            for k, v in m["acres"].items():
                a[k] = a.get(k, 0) + v
        print(f"{c}: {len(members)} member(s); acres {({k: round(v, 1) for k, v in a.items()})}", flush=True)


def load_case(c: str) -> list[dict]:
    return pickle.loads((OUT / f"areas_{c}.pkl").read_bytes())


def member_lots(m: dict, kind: str) -> list:
    """A member's treated or upzoned land (kind "treated" / "upzoned") as a list of polygon features in its CRS
    (m["crs"]), standing for their union. Caches written before the geometry port hold one shapely union under
    "<kind>_union"; its polygons are read through its __geo_interface__, one feature each."""
    from missing_middleware import geom_extra_tod as X
    if f"{kind}_lots" in m:
        return list(m[f"{kind}_lots"])
    return [[part] for part in X.feature_from_geo_interface(m.get(f"{kind}_union"))]


def case_inputs(c: str) -> tuple[pd.DataFrame, dict, list[int], list[int], list[dict]]:
    ms = load_case(c)
    if len(ms) == 1 and c != "nyc_pooled_2003_2013" and c != "philadelphia_2012_remapping":
        m = ms[0]
        return m["permits"], m["acres"], m["per"]["before"], m["per"]["after"], ms
    p, a = NE.stack_members(ms)
    before = list(range(-C.BEFORE_MAX, 0))
    after = list(C.AFTER_YEARS)
    return p, a, before, after, ms


def stocks() -> pd.DataFrame:
    return pd.read_csv(OUT / "coverage_cities.csv").set_index("city")


WI_STATION_AREA_HOMES = 313_564     # 2020 census homes in the main-case station areas (GATE2_PACKET.md, MODEL.md)
WI_CURRENT = {"little (Los Angeles)": 171, "typical (Stacy et al.)": 2509, "strong (Auckland)": 17148}


def treated_homes(case: str) -> tuple[float, str]:
    """Homes in the treated area before the reform: the case's own count (reference/tod_case_estimates.csv,
    treatment_homes) where it has one; otherwise census block homes whose block point lies in the treated lots
    (Philadelphia: 2010 blocks, members together; Madison: 2020 blocks)."""
    e = pd.read_csv(REFERENCE / "tod_case_estimates.csv").set_index("case")
    src = {"nyc_pooled_2003_2013": "MapPLUTO residential units on treated lots in the snapshot before each rezoning (case count)",
           "la_warner_center_2013": "Assessor units on treated lots built before the window (case count)",
           "la_cornfield_arroyo_seco_2013": "Assessor units on treated lots built before the window (case count)",
           "seattle_nbh_othello_2012": "2010 zoned-capacity parcel units on treated lots (case count)",
           "seattle_mount_baker_2014": "2010 zoned-capacity parcel units on treated lots (case count)"}
    if case in e.index and pd.notna(e.loc[case, "treatment_homes"]):
        return float(e.loc[case, "treatment_homes"]), src.get(case, "2010 census block homes in treated eligible lots (case count)")
    f = OUT / f"treated_homes_{case}.json"
    if f.exists():
        d = json.loads(f.read_text())
        return d["homes"], d["source"]
    from missing_middleware.geom_extra_station import bbox_to, feature_bounds, interior_points, polys_to_crs, read_vector
    ms = load_case(case)
    crs = ms[0]["crs"]
    u = [f for m in ms for f in member_lots(m, "treated")]
    fb = feature_bounds(u)
    env = (np.nanmin(fb[:, 0]), np.nanmin(fb[:, 1]), np.nanmax(fb[:, 2]), np.nanmax(fb[:, 3]))
    bbox = bbox_to(env, crs, 4269)
    if case == "madison_tod_overlay_2023":
        path, col = RAW / "census_tiger_2020_tabblock" / "tl_2020_55_tabblock20.zip", "HOUSING20"
        source = "2020 census block homes whose block point lies in the treated lots"
    else:
        path, col = RAW / "tod_cases" / "census_2010_blocks" / "tabblock2010_42_pophu.zip", "HOUSING10"
        source = "2010 census block homes whose block point lies in the treated lots (members together)"
    b = read_vector(path, None, columns=[col], bbox=bbox)
    px, py = interior_points(polys_to_crs(list(b["geometry"]), b.attrs["crs"], crs))
    homes = float(pd.to_numeric(b[col], errors="coerce").fillna(0)[C.in_any(px, py, u)].sum())
    f.write_text(json.dumps({"homes": homes, "source": source}))
    return homes, source


def per_upzoned_home(R: pd.DataFrame, draws: dict) -> pd.DataFrame:
    """After-results addition (plan section 8): net extra homes over five years as a share of homes in the treated area,
    and what that share implies for Wisconsin (x 313,564 station-area homes). Intervals from the same draws."""
    th = {c: treated_homes(c) for c in draws}
    city_cases = R[R["level"] == "case"].groupby("city", sort=False)["case"].apply(list).to_dict()
    for i, r in R.iterrows():
        cs = [r["case"]] if r["level"] == "case" else city_cases.get(r["city"], [])
        h = sum(th[c][0] for c in cs)
        d = 5 * sum(draws[c]["net_homes_per_year"] for c in cs)
        lo, hi = NE.interval(d)
        R.loc[i, "treated_area_homes_before"] = h
        R.loc[i, "treated_area_homes_source"] = "; ".join(sorted({th[c][1] for c in cs}))
        R.loc[i, "treated_area_share_of_city_homes"] = h / r["city_housing_stock"]
        R.loc[i, "net_5yr_homes"] = 5 * r["net_extra_homes_per_year"]
        R.loc[i, "net_5yr_per_upzoned_home_pct"] = 100 * 5 * r["net_extra_homes_per_year"] / h if h else np.nan
        R.loc[i, "net_5yr_per_upzoned_home_low_pct"] = 100 * lo / h if h else np.nan
        R.loc[i, "net_5yr_per_upzoned_home_high_pct"] = 100 * hi / h if h else np.nan
        for k, src in (("", "net_5yr_per_upzoned_home_pct"), ("_low", "net_5yr_per_upzoned_home_low_pct"),
                       ("_high", "net_5yr_per_upzoned_home_high_pct")):
            R.loc[i, f"wisconsin_implied_extra_homes_2027_2031{k}"] = R.loc[i, src] / 100 * WI_STATION_AREA_HOMES
    return R


def stage_net() -> pd.DataFrame:
    cov = stocks()
    shapes = case_shapes()
    rows, draws = [], {}
    for c, (city, _, role) in CASES.items():
        if not (OUT / f"areas_{c}.pkl").exists():
            print(f"{c}: no areas yet")
            continue
        p, a, b, af, ms = case_inputs(c)
        e = NE.net_estimate(p, a, b, af)
        bs = NE.bootstrap_net(p, a, b, af)
        draws[c] = bs
        stock = float(cov.loc[city, "homes"])
        r = {"case": c, "city": city, "trait_test_role": role, "members_stacked": len(ms) if len(ms) > 1 else 0,
             "before_years": f"{b[0]} to {b[-1]}", "after_years": f"{af[0]} to {af[-1]}",
             "years_note": "event time (years since each member's effective year)" if len(ms) > 1 or c.startswith(("nyc", "phil")) else "calendar years",
             "treatment_acres": a.get(NE.TREAT, 0.0), "ring_acres": a.get(NE.RING, 0.0), "far_acres": a.get(NE.FAR, 0.0)}
        for k in ("treatment", "comparison", "far"):
            nm = "ring" if k == "comparison" else k
            r[f"{nm}_rate_before"] = e[f"{k}_before"]
            r[f"{nm}_rate_after"] = e[f"{k}_after"]
        for k, src in (("treatment_units_before", (NE.TREAT, b)), ("treatment_units_after", (NE.TREAT, af)),
                       ("ring_units_before", (NE.RING, b)), ("ring_units_after", (NE.RING, af)),
                       ("far_units_before", (NE.FAR, b)), ("far_units_after", (NE.FAR, af))):
            r[k] = float(p[(p["area"] == src[0]) & p["year"].isin(src[1])]["units"].sum())
        r["did_treatment_vs_ring"] = e["treat_vs_ring"]
        r["did_treatment_vs_far"] = e["treat_vs_far"]
        r["did_treatment_vs_far_low"], r["did_treatment_vs_far_high"] = NE.interval(bs["treat_vs_far"])
        r["borrowing_did_ring_vs_far"] = e["ring_vs_far"]
        r["borrowing_low"], r["borrowing_high"] = NE.interval(bs["ring_vs_far"])
        r["treatment_extra_homes_per_year"] = e["treatment_homes_per_year"]
        r["ring_extra_homes_per_year"] = e["ring_homes_per_year"]
        r["net_extra_homes_per_year"] = e["net_homes_per_year"]
        r["net_low"], r["net_high"] = NE.interval(bs["net_homes_per_year"])
        r["net_per_treatment_acre_per_year"] = e["net_homes_per_year"] / a[NE.TREAT] if a.get(NE.TREAT) else np.nan
        r["city_housing_stock"] = stock
        r["city_housing_stock_source"] = cov.loc[city, "homes_vintage"]
        r["net_share_of_city_stock_per_year_pct"] = 100 * e["net_homes_per_year"] / stock
        r["net_share_low_pct"], r["net_share_high_pct"] = (100 * x / stock for x in NE.interval(bs["net_homes_per_year"]))
        r["net_share_5yr_pct"] = 5 * r["net_share_of_city_stock_per_year_pct"]
        rr = [m["reach"] for m in ms if m["reach"]]
        band = sum(x["band_acres"] for x in rr)
        r["far_band_lot_acres_share"] = sum(x["lot_acres_in_band"] for x in rr) / band if band else np.nan
        r["far_band_max_lot_distance_m"] = max((x["max_lot_distance_m"] for x in rr), default=np.nan)
        sh = shapes.get(c, {})
        r["case_corridor_share"] = sh.get("corridor_share", np.nan)
        r["case_shape_label"] = NE.corridor_label(sh.get("corridor_share", np.nan))
        r["city_share_land_covered"] = cov.loc[city, "share_land_covered"]
        r["city_share_homes_covered"] = cov.loc[city, "share_homes_covered"]
        r["level"] = "case"
        rows.append(r)
    R = pd.DataFrame(rows)
    # city rows: cases of one city summed (draws added, independent resampling)
    crow = []
    for city, g in R.groupby("city", sort=False):
        if len(g) < 2:
            continue
        tot = sum(draws[c]["net_homes_per_year"] for c in g["case"])
        lo, hi = NE.interval(tot)
        stock = float(g["city_housing_stock"].iloc[0])
        x = {"case": f"{CITY_SLUG[city]}_all_cases", "city": city, "level": "city (cases summed)",
             "trait_test_role": g["trait_test_role"].iloc[0],
             "treatment_acres": g["treatment_acres"].sum(), "ring_acres": g["ring_acres"].sum(), "far_acres": g["far_acres"].sum(),
             "treatment_extra_homes_per_year": g["treatment_extra_homes_per_year"].sum(),
             "ring_extra_homes_per_year": g["ring_extra_homes_per_year"].sum(),
             "net_extra_homes_per_year": g["net_extra_homes_per_year"].sum(), "net_low": lo, "net_high": hi,
             "city_housing_stock": stock, "city_housing_stock_source": g["city_housing_stock_source"].iloc[0],
             "net_share_of_city_stock_per_year_pct": 100 * g["net_extra_homes_per_year"].sum() / stock,
             "net_share_low_pct": 100 * lo / stock, "net_share_high_pct": 100 * hi / stock,
             "net_share_5yr_pct": 500 * g["net_extra_homes_per_year"].sum() / stock,
             "city_share_land_covered": g["city_share_land_covered"].iloc[0], "city_share_homes_covered": g["city_share_homes_covered"].iloc[0]}
        crow.append(x)
    R = pd.concat([R, pd.DataFrame(crow)], ignore_index=True)
    R = per_upzoned_home(R, draws)
    R["net_share_5yr_low_pct"] = 5 * R["net_share_low_pct"]
    R["net_share_5yr_high_pct"] = 5 * R["net_share_high_pct"]
    R["warning"] = np.where(R["case"].eq("stpaul_green_line_2011"), "1 before year only (2010): the case is context only in the case work", "")
    R["warning"] = R["warning"].where(~R["case"].eq("madison_tod_overlay_2023"),
                                      "Madison's own years (before 2017-2022, after 2023-2025, effective year included as in its test plan)")
    num = R.select_dtypes("number").columns
    R[num] = R[num].round(5)
    assert not T.check_private(R)
    R.to_csv(BY_CASE_CSV, index=False, lineterminator="\n")
    (OUT / "net_draws.pkl").write_bytes(pickle.dumps(draws))
    pd.set_option("display.width", 250, "display.max_columns", 40)
    print(R[["case", "treatment_acres", "ring_acres", "far_acres", "borrowing_did_ring_vs_far", "borrowing_low", "borrowing_high",
             "net_extra_homes_per_year", "net_low", "net_high", "net_share_of_city_stock_per_year_pct", "net_share_low_pct",
             "net_share_high_pct", "far_band_lot_acres_share", "case_shape_label"]].round(4).to_string(index=False))
    return R


# =========================================================================== shapes and traits

def case_shapes() -> dict:
    """Case-level corridor share and elongation of each case's whole treatment (stacked members together)."""
    f = OUT / "case_shapes.json"
    if f.exists():
        return json.loads(f.read_text())
    out = {}
    for c in CASES:
        if not (OUT / f"areas_{c}.pkl").exists():
            continue
        out[c] = {}
        for key, tag in (("upzoned", ""), ("treated", "_treatment_lots")):
            geoms = []
            for m in load_case(c):
                geoms += member_lots(m, key)
            ps = NE.patches(geoms)
            out[c].update({f"corridor_share{tag}": NE.corridor_share(geoms), f"pieces{tag}": len(ps),
                           f"pieces_half_mile_or_longer{tag}": sum(1 for p in ps if NE.rect_sides(p)[0] >= NE.CORRIDOR_MIN_M),
                           f"acres{tag}": sum(NE.area(p) for p in ps) / C.SQM_PER_ACRE})
    if len(out) == len(CASES):
        f.write_text(json.dumps(out, indent=1))
    return out


NEW_TRAITS = {
    "n01_island_acres": {"label": "Island size: acres of the continuous covered patch the unit sits in", "log": True},
    "n02_largest_site_acres": {"label": "Largest contiguous eligible site: acres of the largest group of touching upzoned lots", "log": True},
    "n03_elongation": {"label": "Elongation: length / average width of the upzoned patch (minimum rotated rectangle)", "log": True},
    "n04_corridor_share": {"label": "Corridor share: share of the unit's upzoned land in pieces at least 1/2 mile long", "log": False},
    "n05_binding_ratio": {"label": "Binding limit: homes per eligible acre before / homes per acre the old FAR allowed", "log": False},
}
NEW_TRAITS.update({
    "n06_no_vehicle_share": {"label": "Car-free households: share of households with no vehicle (ACS B25044)", "log": False},
    "n07_transit_commute_share": {"label": "Transit commuting: share of workers commuting by public transit (ACS B08301)", "log": False},
    "n08_mean_commute_minutes": {"label": "Mean travel time to work, minutes (ACS B08013 aggregate / B08301 workers not at home)", "log": False},
})
FAR_LEVEL_CITIES = {"New York", "Chicago", "Saint Paul", "Seattle", "Madison", "Bellevue"}  # old_level is a FAR


def sqft_per_home() -> float:
    t = pd.read_csv(REFERENCE / "tod_floor_area_per_home.csv").set_index("area")
    return float(t.loc["pooled", "home_weighted_sqft_per_home"])


def unit_traits() -> pd.DataFrame:
    import build_tod_net_coverage as BC
    from missing_middleware.geom_extra_station import polys_to_crs
    import run_tod_traits as R
    units = pd.read_csv(R.UNITS_CSV)
    vals = pd.read_csv(R.VALUES_CSV).set_index("unit_id")
    sq = sqft_per_home()
    patches = {}
    rows = []
    for key in R.ALL_CITIES:
        f = R.OUT / f"units_{key}.pkl"
        if not f.exists():
            continue
        frames = R.load_city(key)["frames"]
        city = R.CITY_NAME[key]
        if city in CITY_SLUG and city not in patches:
            patches[city] = BC.covered_patches(CITY_SLUG[city])
        for fr in frames:
            if not len(fr):
                continue
            uid = fr["unit_id"].iloc[0]
            geoms = [g for g in fr["geometry"] if g]
            land = [part for f in distinct(geoms) for part in f]   # the lots as one feature (they do not overlap)
            isl = np.nan
            if city in patches:
                pc = patches[city]
                isl = NE.island_acres(polys_to_crs([land], R.CRS_OF[key], pc.attrs["crs"])[0] if land else land,
                                      pc.rename(columns={"geometry": "poly"}))
            ps = NE.patches(geoms)
            main = max(ps, key=NE.area) if ps else None
            dens = vals["t03_existing_density"].get(uid, np.nan) if uid in vals.index else np.nan
            bind = NE.binding_ratio(dens, fr["old_level"], fr["acres"], sq) if city in FAR_LEVEL_CITIES else np.nan
            rows.append({"unit_id": uid, "city": city, "n01_island_acres": isl,
                         "n02_largest_site_acres": NE.largest_contiguous_site_acres(geoms),
                         "n03_elongation": NE.elongation(land), "n03_elongation_largest_piece": NE.elongation(main) if main else np.nan,
                         "n04_corridor_share": NE.corridor_share(geoms), "n05_binding_ratio": bind,
                         "upzoned_pieces": len(ps), "treatment_lot_acres": float(fr["acres"].sum())})
    t = pd.DataFrame(rows)
    return t.merge(units[["unit_id", "unit_name", "kept", "treatment_acres"]], on="unit_id", how="left")


# --------------------------------------------------------------------------- car dependence (plan section 8, last entry)

RAWA = RAW / "tod_net_effect_acs"
CAR_SEQS = (25, 30, 97)      # ACS 2006-2010 sequences holding B08013, B08301 and B25044
CAR_TABLES_2022 = ("b25044", "b08301", "b08013")


def stage_fetch() -> None:
    """ACS sequences and tables not already on disk for the car-dependence traits."""
    import fetch_tod_cases as F
    import run_tod_traits as R
    man = F.Manifest(RAWA, "tod_net_effect_acs", "U.S. Census Bureau")
    for name, a2 in R.ACS10_SEQ_STATES.items():
        for q in CAR_SEQS:
            f = f"20105{a2}{q:04d}000.zip"
            F.download_file(man, f"acs2010/{name}_seq/{f}", f"{R.ACS10_SEQ_URL.format(s=name)}/{f}", False, R.CENSUS_LICENCE,
                            timeout=3600, note="ACS 2006-2010 5-year summary file, tracts and block groups, one sequence")
    for t in CAR_TABLES_2022:
        F.download_file(man, f"acs2022/acsdt5y2022-{t}.dat", R.ACS22_URL.format(t=t), False, R.CENSUS_LICENCE, timeout=3600,
                        note="ACS 2018-2022 5-year table-based summary file")


def _cells(look: pd.DataFrame, table: str, lines: tuple[int, ...]) -> dict[int, tuple[int, int]]:
    """(sequence, 1-based column) of each cell line of a table in the 2006-2010 summary file."""
    r = look[(look["Table ID"] == table) & look["Start Position"].notna()].iloc[0]
    seq, start = int(r["Sequence Number"]), int(r["Start Position"])
    return {ln: (seq, start + ln - 1) for ln in lines}


def car_values_2010() -> pd.DataFrame:
    """Tract car-dependence values from the ACS 2006-2010 5-year summary file (states of the comparison cases)."""
    import re
    import zipfile
    import run_tod_traits as R
    look = pd.read_csv(R.RAWT / "acs2010" / "Sequence_Number_and_Table_Number_Lookup.txt", dtype=str, encoding="latin-1")
    cells = {"B25044": _cells(look, "B25044", (1, 3, 10)), "B08301": _cells(look, "B08301", (1, 10, 21)),
             "B08013": _cells(look, "B08013", (1,))}
    out = []
    for st, name in R.ACS10_STATES.items():
        whole = R.RAWT / "acs2010" / f"{name}_Tracts_Block_Groups_Only.zip"
        if whole.exists():
            z = zipfile.ZipFile(whole)
            names = z.namelist()
            gtext = z.open(next(n for n in names if re.search(r"g20105\w\w\.txt$", n, re.I))).read()
            efile = lambda seq, z=z, names=names: z.open(next(n for n in names if re.search(rf"e20105\w\w{seq:04d}000\.txt$", n, re.I)))  # noqa: E731
        else:
            d = RAWA / "acs2010" / f"{name}_seq"
            gtext = next((R.RAWT / "acs2010" / f"{name}_seq").glob("g20105*.txt")).read_bytes()
            efile = lambda seq, d=d: (lambda zz: zz.open(next(n for n in zz.namelist() if n.startswith("e"))))(  # noqa: E731
                zipfile.ZipFile(next(d.glob(f"20105*{seq:04d}000.zip"))))
        lines = gtext.decode("latin-1").splitlines()
        g = pd.DataFrame({"logrecno": [x[13:20] for x in lines], "geoid": [x[178:218].strip() for x in lines]})
        g = g[g["geoid"].str.startswith("14000US")].copy()
        g["tract"] = g["geoid"].str[7:]
        cache = {}
        for t, cl in cells.items():
            for ln, (seq, col) in cl.items():
                if seq not in cache:
                    cache[seq] = pd.read_csv(efile(seq), header=None, dtype=str, encoding="latin-1")
                e = cache[seq]
                g[f"{t}_{ln}"] = g["logrecno"].map(pd.Series(pd.to_numeric(e[col - 1], errors="coerce").values,
                                                             index=e[5].astype(str).str.strip()))
        out.append(g)
    return _car_shares(pd.concat(out, ignore_index=True))


def car_values_2022() -> pd.DataFrame:
    cols = {"b25044": ["B25044_E001", "B25044_E003", "B25044_E010"], "b08301": ["B08301_E001", "B08301_E010", "B08301_E021"],
            "b08013": ["B08013_E001"]}
    res = None
    for t, cs in cols.items():
        d = pd.read_csv(RAWA / "acs2022" / f"acsdt5y2022-{t}.dat", sep="|", dtype=str, usecols=["GEO_ID"] + cs)
        d = d[d["GEO_ID"].str.startswith("1400000US")]
        x = pd.DataFrame({"tract": d["GEO_ID"].str[9:]})
        for c in cs:
            tb, cell = c.split("_E")
            x[f"{tb}_{int(cell)}"] = pd.to_numeric(d[c], errors="coerce").values
        res = x if res is None else res.merge(x, on="tract", how="outer")
    return _car_shares(res)


def _car_shares(g: pd.DataFrame) -> pd.DataFrame:
    """Counts kept as numerators and denominators so that unit values are ratios of acre-weighted sums."""
    return pd.DataFrame({"tract": g["tract"], "hh": g["B25044_1"], "hh_no_vehicle": g["B25044_3"] + g["B25044_10"],
                         "workers": g["B08301_1"], "workers_transit": g["B08301_10"],
                         "workers_not_home": g["B08301_1"] - g["B08301_21"], "travel_minutes": g["B08013_1"]})


def car_traits() -> pd.DataFrame:
    """Each unit's car-dependence values: the treatment lots' tracts (by representative point), each lot's tract counts
    weighted by the lot's acres, then numerator / denominator. ACS 2006-2010 outside Madison, 2018-2022 for Madison."""
    import run_tod_traits as R
    from missing_middleware.geom_extra_station import feature_bounds, first_within, polys_to_crs, transform
    v10, v22 = car_values_2010(), car_values_2022()
    tr10, tr20 = R.tract_shapes("2010"), R.tract_shapes("2020")
    rows = []
    for key in R.ALL_CITIES:
        f = R.OUT / f"units_{key}.pkl"
        if not f.exists() or key == "toronto":
            continue
        frames = [x for x in R.load_city(key)["frames"] if len(x)]
        if not frames:
            continue
        fr = pd.concat(frames, ignore_index=True)
        crs = R.CRS_OF[key]
        tracts, vals, vint = (tr20, v22, "2018-2022") if key == "madison" else (tr10, v10, "2006-2010")
        # tracts moved to the lots' CRS (those near the lots only); each lot's tract by its representative point,
        # the first containing tract kept (sjoin "within", duplicates dropped)
        tb = feature_bounds(list(tracts["geometry"]))
        lon, lat = transform(fr["rx"].to_numpy(float), fr["ry"].to_numpy(float), crs, tracts.attrs["crs"])
        near = (tb[:, 2] >= lon.min() - 0.1) & (tb[:, 0] <= lon.max() + 0.1) & (tb[:, 3] >= lat.min() - 0.1) & (tb[:, 1] <= lat.max() + 0.1)
        tn = tracts[near]
        k = first_within(fr["rx"].to_numpy(float), fr["ry"].to_numpy(float), polys_to_crs(list(tn["geometry"]), tracts.attrs["crs"], crs))
        j = pd.DataFrame({"acres": fr["acres"].values, "unit_id": fr["unit_id"].values,
                          "tract": np.where(k >= 0, tn["tract"].to_numpy(object)[np.maximum(k, 0)], None)})
        j = j.merge(vals, on="tract", how="left")
        for uid, g in j.groupby("unit_id"):
            w = g["acres"]

            def ratio(num, den):
                ok = g[num].notna() & g[den].notna() & (g[den] > 0)
                return float((g.loc[ok, num] * w[ok]).sum() / (g.loc[ok, den] * w[ok]).sum()) if ok.any() else np.nan
            rows.append({"unit_id": uid, "n06_no_vehicle_share": ratio("hh_no_vehicle", "hh"),
                         "n07_transit_commute_share": ratio("workers_transit", "workers"),
                         "n08_mean_commute_minutes": ratio("travel_minutes", "workers_not_home"), "acs_vintage": vint})
    return pd.DataFrame(rows)


def stage_traits() -> None:
    import run_tod_traits as R
    ut = unit_traits().merge(car_traits(), on="unit_id", how="left")
    ut.to_pickle(OUT / "unit_traits.pkl")
    # the trait test: same frame, folds, baseline and pass rule as the several-tools rerun (traits.judge_tools)
    d = R.wide_frame().merge(ut.drop(columns=["city", "unit_name", "kept", "treatment_acres"]), on="unit_id", how="left")
    rows, errs = [], []
    for t, spec in NEW_TRAITS.items():
        x = pd.to_numeric(d[t], errors="coerce").astype(float)
        d[f"x_{t}"] = np.log(x + 1.0) if spec["log"] else x
        dd = d.dropna(subset=[f"x_{t}"])
        e = R.tool_errors(dd, "one_trait", [f"x_{t}"])
        row = R.tool_row("one_trait", t, e, len(dd), "baseline judged on the same units (those with the trait)")
        row["trait_label"] = spec["label"]
        row["entered_as"] = "log(value + 1)" if spec["log"] else "value"
        row["fold_cities_with_trait"] = int(e["role"].eq("fold").sum())
        row["units_by_city"] = "; ".join(f"{c}: {n}" for c, n in dd.groupby("city", sort=False).size().items())
        if row["fold_cities_with_trait"] < len(T.WIDE_FIT_CITIES):
            row["detail"] += f"; testable in {row['fold_cities_with_trait']} of {len(T.WIDE_FIT_CITIES)} fold cities, so it cannot pass"
        rows.append(row)
        errs.append(e.assign(trait=t))
    out = pd.DataFrame(rows)
    out = out[["variant", "trait_label", "entered_as", "verdict"] + [c for c in out.columns if c not in ("variant", "trait_label", "entered_as", "verdict", "tool")]]
    out = out.rename(columns={"variant": "trait"})
    assert not T.check_private(out)
    out.round(4).to_csv(TEST_CSV, index=False, lineterminator="\n")
    pd.concat(errs).to_pickle(OUT / "trait_errors.pkl")
    pd.set_option("display.width", 250, "display.max_columns", 40)
    print(out[["trait", "verdict", "fold_cities_better", "fold_cities", "mean_error_baseline", "mean_error_model",
               "beats_baseline_chicago", "beats_baseline_madison", "units_used"]].to_string(index=False))
    print(pd.concat(errs)[["trait", "city", "error_baseline", "error_model", "measured_mean", "predicted_mean_model"]].round(3).to_string(index=False))
    write_coverage(ut)


def write_coverage(ut: pd.DataFrame) -> None:
    cov = stocks().reset_index()
    shapes = case_shapes()
    by_city = {}
    for c, (city, _, _) in CASES.items():
        if c in shapes:
            by_city.setdefault(city, []).append(f"{c}: {shapes[c]['corridor_share']:.3f} ({NE.corridor_label(shapes[c]['corridor_share'])})")
    crow = []
    for r in cov.itertuples(index=False):
        crow.append({"level": "city", "city": r.city, "unit_name": "", "land_acres": r.land_acres, "covered_land_acres": r.covered_land_acres,
                     "share_land_covered": r.share_land_covered, "homes": r.homes, "homes_covered": r.homes_covered,
                     "share_homes_covered": r.share_homes_covered, "covered_patches": r.patches, "largest_patch_acres": r.largest_patch_acres,
                     "case_corridor_share_and_label": "; ".join(by_city.get(r.city, [])),
                     "stop_layer_year": r.stop_layer_year, "bus_feed_date": r.bus_feed_date, "boundary_vintage": r.boundary_vintage,
                     "homes_vintage": r.homes_vintage, "notes": r.notes})
    u = ut.copy()
    u["level"] = "unit"
    u = u.rename(columns={"treatment_acres": "unit_treatment_acres_in_trait_test"})
    keep = ["level", "city", "unit_name", "kept", "unit_treatment_acres_in_trait_test", "n01_island_acres", "n02_largest_site_acres",
            "n03_elongation", "n03_elongation_largest_piece", "n04_corridor_share", "n05_binding_ratio", "upzoned_pieces",
            "n06_no_vehicle_share", "n07_transit_commute_share", "n08_mean_commute_minutes", "acs_vintage"]
    out = pd.concat([pd.DataFrame(crow), u[keep]], ignore_index=True)
    out = out[["level", "city", "unit_name"] + [c for c in out.columns if c not in ("level", "city", "unit_name")]]
    num = out.select_dtypes("number").columns
    out[num] = out[num].round(4)
    assert not T.check_private(out)
    out.to_csv(COVERAGE_CSV, index=False, lineterminator="\n")
    print(f"wrote {COVERAGE_CSV.relative_to(ROOT)} ({len(out)} rows)")


# =========================================================================== distant borrowing (check only)

STATE_COUNTY = {"New York": ("36", ["005", "047", "061", "081", "085"]), "Philadelphia": ("42", ["101"]),
                "Charlotte": ("37", ["119"]), "Saint Paul": ("27", ["123"]), "Chicago": ("17", ["031"]),
                "Seattle": ("53", ["033"]), "Madison": ("55", ["025"]), "Los Angeles": ("06", ["037"])}


def county_units(years) -> pd.DataFrame:
    """Units authorized (1, 2, 3-4, 5+ unit buildings) by county and year, Census Building Permits Survey."""
    rows = []
    for y in years:
        for d in (RAW / "tod_cases" / "bps_county", RAW / "census_bps_county"):
            f = d / f"co{y}a.txt"
            if f.exists():
                for line in f.read_text(errors="replace").splitlines()[2:]:
                    c = line.split(",")
                    if len(c) > 16 and c[1].strip().isdigit():
                        rows.append({"year": y, "state": c[1].strip().zfill(2), "county": c[2].strip().zfill(3),
                                     "units": sum(int(float(c[i] or 0)) for i in (7, 10, 13, 16))})
                break
    return pd.DataFrame(rows)


def metro_counties(city: str) -> list[tuple[str, str]]:
    """Counties of the city's metro (2024 CBSA), from the TIGER county file."""
    from missing_middleware.geom_extra_foundation import read_attributes
    st, cos = STATE_COUNTY[city]
    g = read_attributes(RAW / "census_tiger_2024" / "tl_2024_us_county.zip")
    cb = g[(g["STATEFP"] == st) & (g["COUNTYFP"] == cos[0])]["CBSAFP"].iloc[0]
    m = g[g["CBSAFP"] == cb]
    return [(s, c) for s, c in zip(m["STATEFP"], m["COUNTYFP"])]


def citywide_permits(case: str) -> pd.DataFrame | None:
    """All of the city's permits with units, year and a point (columns x, y in the case's metre CRS, attrs["crs"]),
    from the adapter's own loader."""
    city = CASES[case][0]
    out = None
    if city == "Chicago":
        from missing_middleware.tod import case_chicago as K
        p = pd.read_csv(K.DIR / "permits_new_construction.csv", dtype=str).drop_duplicates("permit_")
        p["units"] = p["work_description"].map(K.parse_units)
        p["year"] = pd.to_numeric(p["issue_date"].str[:4], errors="coerce")
        p = p[(p["units"] > 0) & p["year"].notna()].dropna(subset=["latitude", "longitude"])
        out = K.dedupe_staged(C.points_from_lonlat(p, "longitude", "latitude", K.CRS_M))
    elif city == "Saint Paul":
        from missing_middleware.tod import case_stpaul as K
        h = C.points(K.DIR / "housing_production.geojson", K.CRS_M)
        h = h[h["TypeOfWork"] == "New"].copy()
        h["units"] = pd.to_numeric(h["NewDwellingUnits"], errors="coerce").fillna(0)
        h["year"] = pd.to_numeric(h["ProjectPermitIssueYear"], errors="coerce")
        out = h[(h["units"] > 0)]
    elif city == "Charlotte":
        from missing_middleware.tod import case_charlotte as K
        pr = K.load_permits()
        g = C.points_from_lonlat(pr, "X", "Y", K.CRS_M, src=2264)
        districts = C.polygons(K.DIR / "council_districts.geojson", K.CRS_M)
        out = g[C.in_any(g["x"].to_numpy(float), g["y"].to_numpy(float), districts)]
    elif city == "Philadelphia":
        from missing_middleware.tod import case_philadelphia as K
        out = K._load()["permits"]
    elif city == "Seattle":
        from missing_middleware.tod import case_seattle as K
        out = K._load()["permits"]
    elif city == "New York":
        from missing_middleware.tod import case_nyc as K
        j = K.load_jobs(None)
        j = j[j["lon"].between(-74.3, -73.6)]
        out = C.points_from_lonlat(j, "lon", "lat", K.CRS_M)
    if out is None:
        return None  # Madison: handled from the Madison permit table (placed permits) in stage_distant; Los Angeles:
        #               permit files cover only the plans' envelopes
    out = out.copy()
    out.attrs["crs"] = int(K.CRS_M)
    return out


def stage_distant() -> pd.DataFrame:
    cu = county_units(range(1996, 2026))
    rows = []
    for c, (city, _, _) in CASES.items():
        if not (OUT / f"areas_{c}.pkl").exists():
            continue
        ms = load_case(c)
        if city == "Madison":
            fr = ms[0]
            allp = None
        else:
            allp = citywide_permits(c)
        if allp is None and city != "Madison":
            rows.append({"case": c, "city": city, "status": "no citywide permit file (permits fetched for the plans' envelopes only)"})
            continue
        st, own = STATE_COUNTY[city]
        mc = [x for x in metro_counties(city) if not (x[0] == st and x[1] in own)]
        reg = cu[cu.apply(lambda r: (r["state"], r["county"]) in mc, axis=1)].groupby("year")["units"].sum().to_dict()
        agg = {"beyond_before": 0.0, "beyond_after": 0.0, "region_before": 0.0, "region_after": 0.0}
        n_ok = 0
        for m in ms:
            b, a = m["per"]["before"], m["per"]["after"]
            if city == "Madison":
                g = madison_citywide()
                yrs, un = g["year"], g["units"]
            else:
                g = allp
                yrs, un = pd.to_numeric(g["year"], errors="coerce"), pd.to_numeric(g["units"], errors="coerce")
            if int(g.attrs.get("crs", m["crs"])) != int(m["crs"]):
                raise ValueError(f"{c}: permits in EPSG:{g.attrs['crs']}, member in EPSG:{m['crs']}")
            from missing_middleware.geom_extra_station import distance_within
            tu = member_lots(m, "treated")
            beyond = pd.Series(distance_within(g["x"].to_numpy(float), g["y"].to_numpy(float), tu, NE.FAR_MAX_M)
                               > NE.FAR_MAX_M, index=g.index)
            s = pd.Series(un.values, index=yrs.values)[beyond.values].groupby(level=0).sum().to_dict()
            s = {int(y): float(s.get(y, 0.0)) for y in b + a}
            chk = NE.distant_check(s, reg, b, a)
            if not np.isfinite(chk["region_growth"]):
                continue
            n_ok += 1
            for k in agg:
                agg[k] += chk[k]
        agg = {k: v / n_ok for k, v in agg.items()} if n_ok else agg   # stacked cases: mean over members
        gb = agg["beyond_after"] / agg["beyond_before"] if agg["beyond_before"] else np.nan
        gr = agg["region_after"] / agg["region_before"] if agg["region_before"] else np.nan
        rows.append({"case": c, "city": city, "status": "check (not judged)", "members_used": n_ok,
                     "beyond_homes_per_year_before": agg["beyond_before"], "beyond_homes_per_year_after": agg["beyond_after"],
                     "region_homes_per_year_before": agg["region_before"], "region_homes_per_year_after": agg["region_after"],
                     "beyond_growth_ratio": gb, "region_growth_ratio": gr, "relative_growth_minus_1": gb / gr - 1 if gr else np.nan,
                     "region": f"other counties of the metro (2024 CBSA): {len(mc)} counties, Census BPS units",
                     "note": ("mean over stacked members (each member's own calendar years)" if n_ok > 1 else "") +
                             ("; Saint Paul's permit file has units only from 2010 (1 before year), so its growth ratio is not meaningful"
                              if city == "Saint Paul" else "") +
                             ("; Madison: placed permits of the Madison test's own table" if city == "Madison" else "") +
                             ("; Chicago: units parsed from work descriptions, as in the case" if city == "Chicago" else "")})
    D = pd.DataFrame(rows)
    num = D.select_dtypes("number").columns
    D[num] = D[num].round(4)
    D.to_csv(OUT / "distant_check.csv", index=False)
    # joined into the by-case table
    R = pd.read_csv(BY_CASE_CSV)
    R = R.drop(columns=[c for c in R.columns if c.startswith("distant_")])
    D2 = D.set_index("case")[["status", "beyond_homes_per_year_before", "beyond_homes_per_year_after", "beyond_growth_ratio",
                            "region_homes_per_year_before", "region_homes_per_year_after", "region_growth_ratio",
                            "relative_growth_minus_1", "region", "note"]].add_prefix("distant_")
    R = R.merge(D2, left_on="case", right_index=True, how="left")
    R.to_csv(BY_CASE_CSV, index=False, lineterminator="\n")
    print(D.to_string(index=False))
    return D


def madison_citywide():
    """Madison's placed permits (the Madison test's own permit table): year, units and points x, y (EPSG:3071)."""
    f = OUT / "madison_citywide.pkl"
    return pd.read_pickle(f)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stage", choices=["fetch", "areas", "net", "traits", "distant", "all"], default="all")
    ap.add_argument("--case", nargs="*", default=list(CASES))
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args(argv)
    if a.stage == "fetch":
        stage_fetch()
    if a.stage in ("areas", "all"):
        stage_areas(a.case, a.rebuild)
    if a.stage in ("net", "all"):
        stage_net()
    if a.stage in ("traits", "all"):
        stage_traits()
    if a.stage in ("distant", "all"):
        stage_distant()


if __name__ == "__main__":
    main()
