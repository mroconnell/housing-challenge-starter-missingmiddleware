"""Toronto Eglinton Connects mid-rise rezoning, By-law 1030-2014 (enacted 28 August 2014): case adapter (batch 2).

Plan: CASE_ANALYSIS_PLAN.md section 7, entry of 2026-10-27 ("more cities for the trait test"). Same rules as every
other case: the one area rule (cases.uniform_areas), units per eligible acre per year, before = 6 years, after = 1-5.

Inputs (data/raw/tod_cases/toronto/, fetched by scripts/fetch_tod_cases_batch2.py; Open Government Licence - Toronto):
- permits_cleared_2000_2016.csv, permits_cleared_since_2017.csv, permits_active.csv: building permits with permit
  number, revision, type, work, address, GEO_ID (= address point id), issue date, DWELLING_UNITS_CREATED.
- zoning_area.gpkg: Zoning By-law 569-2013 zone areas (current consolidation); zoning_height_overlay.geojson.
- address_points.gpkg (EPSG:2952), property_boundaries.gpkg (parcels, EPSG:2952), ttc_gtfs.zip (stations).

Rules used here (docs/tod/CASE_RESULTS.md (section 'Added cities, batch 2'), section Toronto):
- Treatment boundary: the by-law's diagrams are images, but every lot it rezoned carries one of its new CR exceptions
  2621-2648 (sections 8 onward of the by-law). Treatment = parcels whose representative point lies in a current
  zone polygon labelled with one of those exceptions. Lots the City has since rezoned again under a later site-
  specific by-law lose the exception and drop out (3 of the 28 exceptions, 2623, 2626 and 2640, no longer appear).
- Did density rise: yes on every treatment lot. The by-law removed the floor space index limits of the CR labels and
  raised heights by up to 3 storeys (staff report, CASE_INVENTORY.md). "Already at the law" cannot be tested: no layer
  keeps the labels before 2014, so no lot is excluded as already at the law (as for Phoenix).
- Zoning before for other lots: the current consolidation (no 2013 snapshot is published). Later site-specific
  rezonings cannot be dated in the layer, so "rezoned outside the reform in the window" is not applied (limitation).
- Eligible land: zone class residential (R, RD, RS, RT, RM, RA, RAC), mixed (CR, CRE) or commercial (CL); open space
  (O*), utility (UT), institutional (I*) and employment (E*) zones are excluded; parcel type RESERVE is excluded.
  Treatment lots are all CR after; their class before is taken as eligible (mixed-use "Avenue" frontage).
- Outcome: permits of type New Building or New Houses, or Residential / Multiple Use / Non-Residential Building
  Permit with work "New Building ...", with DWELLING_UNITS_CREATED > 0 and an issue date; one row per permit number
  (revision 00 carries the permit's units; later revisions are dropped). Cancelled and refused permits are dropped.
- Location: GEO_ID joins the address point (ADDRESS_POINT_ID); otherwise number + street name match the address
  points; the point is placed in its parcel (cases.locate_points).
- Project (for resampling): the parcel.
- Dose: added height limit (feet) over eligible treatment land: the exception's maximum height (by-law text) minus
  the height overlay on the lot (the 569-2013 label the exception overrides). Lots where the exception sets no
  height, or where the overlay equals the exception height (lands the by-law itself added to the overlay map), have
  no dose. The removed FSI caps are not in the dose. No FAR dose (heights only), so the case stays out of per-FAR
  pooling, like Charlotte.
- Second comparison: parcels within 1/2 mile of TTC rail and rapid-transit stations (GTFS parent stations) whose own
  1/2-mile circle has no treated land.
- Effective year: 2014 (enacted August 2014). The parent Official Plan Amendment 253 was appealed and settled on
  28 September 2018, so a 2018 effective year is reported as a diagnostic.
"""
from __future__ import annotations

import re
import zipfile

import numpy as np
import pandas as pd

from missing_middleware.paths import RAW
from missing_middleware.tod import cases as C

DIR = RAW / "tod_cases" / "toronto"
CRS_M = 2952  # NAD83(CSRS) / MTM zone 10 (metres)
EFFECTIVE_YEAR = 2014
ALT_EFFECTIVE_YEAR = 2018
FIRST_YEAR, LAST_FULL_YEAR = 2000, 2025
FT_PER_M = 3.280839895
NEAREST_NUMBER_MAX_GAP = 20  # house numbers; same street and side
LATER_REZONED_NEAR_M = 100.0  # sensitivity: later-rezoned Eglinton lots within this distance of the by-law's lands
EXCEPTIONS = range(2621, 2649)
# Maximum height (metres) set by each exception of By-law 1030-2014 (None: the exception sets no height).
EXCEPTION_HEIGHT_M: dict[int, float | None] = {
    2621: None, 2622: 25.5, 2623: 25.5, 2624: 25.5, 2625: 22.5, 2626: 22.5, 2627: 22.5, 2628: 25.5, 2629: 25.5,
    2630: 25.5, 2631: 22.5, 2632: 19.5, 2633: 19.5, 2634: 22.5, 2635: 25.5, 2636: 13.5, 2637: 25.5, 2638: 25.5,
    2639: 22.5, 2640: 25.5, 2641: None, 2642: 22.5, 2643: None, 2644: 25.5, 2645: 25.5, 2646: 25.5, 2647: 25.5,
    2648: 19.5}
ZONE_CLASS = {"R": "res", "RD": "res", "RS": "res", "RT": "res", "RM": "res", "RA": "res", "RAC": "res",
              "CR": "mixed", "CRE": "mixed", "CL": "com"}
NEW_TYPES = {"New Building", "New Houses"}
NEW_WORK_TYPES = {"Residential Building Permit", "Multiple Use Permit", "Non-Residential Building Permit"}
DROP_STATUS = {"Cancelled", "Refusal Notice", "Refused", "Application Withdrawn", "Withdrawn"}
PERMIT_FILES = ("permits_cleared_2000_2016.csv", "permits_cleared_since_2017.csv", "permits_active.csv")
PERMIT_COLS = ["PERMIT_NUM", "REVISION_NUM", "PERMIT_TYPE", "WORK", "STREET_NUM", "STREET_NAME", "STREET_DIRECTION",
               "GEO_ID", "ISSUED_DATE", "STATUS", "DWELLING_UNITS_CREATED"]


# --------------------------------------------------------------------------- pure helpers (tested)

def exception_no(zn_string) -> int | None:
    """The site-specific exception number in a 569-2013 zone label: 'CR SS2  (x2631)' -> 2631."""
    m = re.search(r"\(x(\d+)\)", str(zn_string or ""))
    return int(m.group(1)) if m else None


def in_bylaw(exc: int | None) -> bool:
    return exc is not None and exc in EXCEPTIONS


def zone_class(zone) -> str | None:
    return ZONE_CLASS.get(str(zone or "").strip().upper())


def first_number(s) -> str:
    m = re.match(r"\s*(\d+)", str(s or ""))
    return m.group(1) if m else ""


def address_key(num, name, direction="") -> str:
    """Join key for permit and address-point addresses: first house number | street name | direction (E/W/N/S)."""
    d = str(direction or "").strip().upper()[:1]
    d = d if d in ("E", "W", "N", "S") else ""
    return f"{first_number(num)}|{re.sub(r'[^A-Z0-9]', '', str(name or '').upper())}|{d}"


def select_new_permits(p: pd.DataFrame) -> pd.DataFrame:
    """New-construction permits with units and an issue date, one per permit number (revision 00, else the lowest)."""
    p = p.copy()
    p["units"] = pd.to_numeric(p["DWELLING_UNITS_CREATED"], errors="coerce").fillna(0)
    typ, work = p["PERMIT_TYPE"].astype(str).str.strip(), p["WORK"].astype(str).str.strip()
    new = typ.isin(NEW_TYPES) | (typ.isin(NEW_WORK_TYPES) & work.str.startswith("New Building"))
    p = p[new & (p["units"] > 0) & ~p["STATUS"].astype(str).str.strip().isin(DROP_STATUS)]
    p["issued"] = pd.to_datetime(p["ISSUED_DATE"].astype(str).str[:10], errors="coerce")
    p = p.dropna(subset=["issued"])
    p["rev"] = pd.to_numeric(p["REVISION_NUM"], errors="coerce").fillna(99)
    p = p.sort_values(["PERMIT_NUM", "rev"]).drop_duplicates("PERMIT_NUM", keep="first")
    p["year"] = p["issued"].dt.year.astype(int)
    return p


def height_dose_m(exc: int | None, overlay_m: float | None) -> float:
    """Added height (metres) on a treatment lot: exception height minus the overlay height it overrides (NaN when the
    exception sets no height, the overlay is missing, or the overlay equals the exception height)."""
    h = EXCEPTION_HEIGHT_M.get(exc) if exc is not None else None
    if h is None or overlay_m is None or pd.isna(overlay_m) or overlay_m <= 0 or abs(h - overlay_m) < 1e-6:
        return float("nan")
    return float(h - overlay_m)


# --------------------------------------------------------------------------- loading

def load_permits() -> pd.DataFrame:
    parts = [pd.read_csv(DIR / f, dtype=str, usecols=lambda c: c in PERMIT_COLS, low_memory=False) for f in PERMIT_FILES]
    return select_new_permits(pd.concat(parts, ignore_index=True))


def load_stations() -> pd.DataFrame:
    """TTC stations (GTFS location_type 1) as a point frame (x, y) in CRS_M."""
    with zipfile.ZipFile(DIR / "ttc_gtfs.zip") as z:
        s = pd.read_csv(z.open("stops.txt"), dtype=str)
    s = s[s["location_type"] == "1"]
    from missing_middleware.geom_extra_station import crs, wgs84_to_csrs
    lo, la = wgs84_to_csrs(s["stop_lon"].astype(float).to_numpy(), s["stop_lat"].astype(float).to_numpy())
    x, y = crs(CRS_M).forward(lo, la)
    return pd.DataFrame({"x": x, "y": y})


def _wgs84_layer(path) -> pd.DataFrame:
    """A WGS 84 polygon layer in CRS_M (NAD83(CSRS)), with PROJ's datum shift (about 1 m) so it lines up with the
    property boundaries, which are published in CRS_M."""
    from missing_middleware.geom_extra_station import polys_wgs84_to, read_vector, wgs84_to_csrs
    g = read_vector(path)
    assert g.attrs["crs"].kind == "longlat"
    g["geometry"] = polys_wgs84_to(list(g["geometry"]), CRS_M, wgs84_to_csrs)
    return g


def _aoi_distance(px, py, treat_polys: list, step: float = 5.0) -> np.ndarray:
    """Approximate distance from points to the treated polygons (0 inside), from boundary points every `step` metres:
    used only to choose which parcels and address points to read (the area of interest), as the geopandas version's
    `mask` did; exact to within step / 2."""
    from scipy.spatial import cKDTree

    from missing_middleware.geom_extra_station import _segments_of
    seg, _ = _segments_of(treat_polys)
    L = np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1])
    k = np.maximum(1, np.ceil(L / step).astype(int))
    t = np.concatenate([np.arange(n) / n for n in k])
    s = seg[np.repeat(np.arange(len(seg)), k)]
    pts = np.c_[s[:, 0] + t * (s[:, 2] - s[:, 0]), s[:, 1] + t * (s[:, 3] - s[:, 1])]
    d = cKDTree(pts).query(np.c_[px, py])[0]
    return np.where(C.in_any(px, py, treat_polys), 0.0, d)


def _in_aoi(px, py, treat_polys: list, stations: pd.DataFrame, extra: float = 0.0) -> np.ndarray:
    """Points within 1,600 m of the by-law's lands or within 1/2 mile + 50 m of a station (plus `extra`)."""
    from scipy.spatial import cKDTree
    near_t = _aoi_distance(px, py, treat_polys) <= 1600 + extra
    ds = cKDTree(stations[["x", "y"]].to_numpy()).query(np.c_[px, py])[0]
    return near_t | (ds <= C.HALF_MILE_M + 50 + extra)


def nearest_number(street_nums: pd.DataFrame, want: pd.DataFrame, max_gap: int = NEAREST_NUMBER_MAX_GAP) -> pd.Series:
    """For each wanted (street, number), the row label in street_nums of the closest house number on the same street
    and side (same parity), within max_gap numbers. street_nums: columns street, num (int); want: same columns."""
    out = pd.Series(np.nan, index=want.index, dtype=float)
    s = street_nums.assign(par=street_nums["num"] % 2, lab=street_nums.index.astype(float)).sort_values("num")
    w = want.assign(par=want["num"] % 2).reset_index().rename(columns={"index": "_w"}).sort_values("num")
    m = pd.merge_asof(w, s[["street", "par", "num", "lab"]].rename(columns={"num": "found"}), left_on="num", right_on="found",
                      by=["street", "par"], direction="nearest")
    ok = (m["found"] - m["num"]).abs() <= max_gap
    out.loc[m.loc[ok, "_w"].values] = m.loc[ok, "lab"].values
    return out


def locate_permits(pr: pd.DataFrame, addr, parcels) -> pd.DataFrame:
    """Permit -> address point (GEO_ID; else the same address; else the nearest house number on the same street side,
    within NEAREST_NUMBER_MAX_GAP: big sites are re-addressed after construction) -> parcel index ('pix')."""
    a = addr.copy().reset_index(drop=True)
    a["apid"] = pd.to_numeric(a["ADDRESS_POINT_ID"], errors="coerce")
    a["pos"] = np.arange(len(a), dtype=float)
    by_id = a.dropna(subset=["apid"]).drop_duplicates("apid").set_index("apid")["pos"]
    a["key"] = [address_key(n, nm, d) for n, nm, d in zip(a["LO_NUM"], a["LINEAR_NAME"], a["LINEAR_NAME_DIR"])]
    by_key = a.drop_duplicates("key").set_index("key")["pos"]
    gid = pd.to_numeric(pr["GEO_ID"], errors="coerce")
    geom = gid.map(by_id)          # position of the address point in `a`
    keys = pd.Series([address_key(n, nm, d) for n, nm, d in zip(pr["STREET_NUM"], pr["STREET_NAME"], pr["STREET_DIRECTION"])], index=pr.index)
    how = pd.Series(np.where(geom.notna(), "geo_id", "none"), index=pr.index)
    miss = geom.isna()
    geom[miss] = keys[miss].map(by_key)
    how[miss & geom.notna()] = "address"
    miss = geom.isna()
    if miss.any():
        street = lambda k: k.split("|", 1)[1]  # noqa: E731
        sn = pd.DataFrame({"street": a["key"].map(street), "num": pd.to_numeric(a["key"].str.split("|").str[0], errors="coerce")}).dropna()
        sn["num"] = sn["num"].astype(int)
        wk = keys[miss]
        want = pd.DataFrame({"street": wk.map(street), "num": pd.to_numeric(wk.str.split("|").str[0], errors="coerce")}, index=wk.index).dropna()
        want["num"] = want["num"].astype(int)
        lab = nearest_number(sn, want)
        hit = lab.dropna()
        geom[hit.index] = a["pos"].loc[hit.astype(int).values].values
        how[hit.index] = "nearest_number"
    pr = pr.assign(located_by=how)
    g = pr[geom.notna()].copy()
    pos = geom[geom.notna()].astype(int).to_numpy()
    g["x"], g["y"] = a["x"].to_numpy()[pos], a["y"].to_numpy()[pos]
    g["pix"] = C.locate_points(g, parcels)
    return g, pr["located_by"].value_counts().to_dict()


# --------------------------------------------------------------------------- build

def _did_row(permits: pd.DataFrame, acres: dict, per: dict, added, parcels) -> dict | None:
    if not (acres.get(C.TREAT) and acres.get(C.COMP)):
        return None
    d = C.did(permits, acres, per["before"], per["after"])
    lo, hi, _ = C.bootstrap_did(permits, acres, per["before"], per["after"])
    t = permits[permits["area"] == C.TREAT]
    return {"added_lots": int(added.sum()), "added_acres": round(float(parcels.loc[added, "acres"].sum()), 1),
            "treatment_acres": round(acres[C.TREAT], 1), "comparison_acres": round(acres[C.COMP], 1),
            "did": round(d["did"], 4), "interval90": [round(lo, 4), round(hi, 4)],
            "treatment_units_before": int(t[t["year"].isin(per["before"])]["units"].sum()),
            "treatment_units_after": int(t[t["year"].isin(per["after"])]["units"].sum())}


def build(effective_year: int = EFFECTIVE_YEAR) -> tuple[C.CaseInputs, dict]:
    from missing_middleware.geom_extra_station import feature_bounds, nonempty, read_vector
    z = _wgs84_layer(DIR / "zoning_area.gpkg")
    z["exc"] = z["ZN_STRING"].map(exception_no)
    z["in_bylaw"] = z["exc"].map(in_bylaw)
    treat_poly = z[z["in_bylaw"]]
    tpolys = list(treat_poly["geometry"])
    stations = load_stations()
    # area of interest (the geopandas version read features meeting the union of the buffers): a box prefilter, then
    # parcels with a vertex in the area
    tb = feature_bounds(tpolys)
    r = C.HALF_MILE_M + 50
    box = (min(np.nanmin(tb[:, 0]) - 1600, stations["x"].min() - r), min(np.nanmin(tb[:, 1]) - 1600, stations["y"].min() - r),
           max(np.nanmax(tb[:, 2]) + 1600, stations["x"].max() + r), max(np.nanmax(tb[:, 3]) + 1600, stations["y"].max() + r))
    parcels = read_vector(DIR / "property_boundaries.gpkg", CRS_M, bbox=box)
    parcels = parcels[nonempty(parcels["geometry"])].reset_index(drop=True)
    verts = [np.concatenate([rr for part in f for rr in part]) for f in parcels["geometry"]]
    own = np.repeat(np.arange(len(verts)), [len(v) for v in verts])
    V = np.concatenate(verts)
    hit = _in_aoi(V[:, 0], V[:, 1], tpolys, stations)
    keep = np.zeros(len(parcels), bool)
    keep[np.unique(own[hit])] = True
    parcels = parcels[keep].drop_duplicates("PARCELID").reset_index(drop=True)
    parcels["acres"] = C.parcel_acres(parcels)
    rx, ry = C.rep_xy(parcels)
    pts = pd.DataFrame({"x": rx, "y": ry})
    j = C.join_within(parcels, z, ["ZN_ZONE", "ZN_STRING", "exc", "in_bylaw"])
    h = _wgs84_layer(DIR / "zoning_height_overlay.geojson")[["HT_LABEL", "geometry"]]
    jh = C.join_within(parcels, h, ["HT_LABEL"])
    parcels["zone"] = j["ZN_ZONE"].values
    parcels["exc"] = j["exc"].values
    parcels["treated"] = j["in_bylaw"].fillna(False).astype(bool).values
    parcels["overlay_m"] = pd.to_numeric(jh["HT_LABEL"], errors="coerce").values
    parcels["zclass"] = np.where(parcels["treated"], "mixed", parcels["zone"].map(zone_class))
    parcels["eligible"] = parcels["zclass"].isin(["res", "mixed", "com"]) & (parcels["FEATURE_TYPE"].astype(str) != "RESERVE")
    in_city = pd.Series(True, index=parcels.index)

    # uniform rule: every treatment lot rose (FSI caps removed); no lot can be shown to be already at the law
    after_m = parcels["exc"].map(lambda e: EXCEPTION_HEIGHT_M.get(int(e)) if pd.notna(e) else None).astype(float)
    level_after = after_m.fillna(parcels["overlay_m"])
    # height levels (feet) for the trait test's dose per unit: before = the overlay the exception overrides
    parcels["dose_m"] = [height_dose_m(int(e) if pd.notna(e) else None, o) if t else np.nan
                         for e, o, t in zip(parcels["exc"], parcels["overlay_m"], parcels["treated"])]
    parcels["h_before"] = np.where(parcels["dose_m"].notna(), parcels["overlay_m"] * FT_PER_M, np.nan)
    parcels["h_after"] = parcels["h_before"] + parcels["dose_m"] * FT_PER_M
    none = pd.Series(False, index=parcels.index)
    parcels["area"], rule = C.uniform_areas(parcels, parcels["treated"], parcels["treated"], pd.Series(np.nan, index=parcels.index),
                                            level_after, none, none, parcels["eligible"], in_city=in_city, stations=stations)
    el = parcels[parcels["area"].notna() & parcels["eligible"]]
    acres = el.groupby("area")["acres"].sum().to_dict()

    pr = load_permits()
    abox = (box[0] - 100, box[1] - 100, box[2] + 100, box[3] + 100)
    addr = read_vector(DIR / "address_points.gpkg", CRS_M, bbox=abox,
                       columns=["ADDRESS_POINT_ID", "LO_NUM", "LINEAR_NAME", "LINEAR_NAME_DIR"])
    addr = addr[_in_aoi(addr["x"].to_numpy(), addr["y"].to_numpy(), tpolys, stations, extra=100.0)].reset_index(drop=True)
    near, located = locate_permits(pr, addr, parcels)
    near["eligible"] = parcels["eligible"].reindex(near["pix"]).fillna(False).astype(bool).values

    def permits_for(area: pd.Series) -> pd.DataFrame:
        q = near.assign(area=area.reindex(near["pix"]).values)
        q = q[q["area"].notna() & q["eligible"]].copy()
        q["project"] = "tor:" + q["pix"].astype(int).astype(str)
        return q[["project", "area", "year", "units"]]

    permits = permits_for(parcels["area"])
    orig_area = C.assign_areas(parcels, parcels["treated"], in_city=in_city, stations=stations)
    orig_acres = parcels[orig_area.notna() & parcels["eligible"]].groupby(orig_area)["acres"].sum().to_dict()

    # sensitivity (not the plan's boundary): add lots that left By-law 569-2013 through a later site-specific
    # rezoning (no zone in the layer), front on Eglinton (an Eglinton address point) and lie within
    # LATER_REZONED_NEAR_M of the by-law's lands. They are where most Eglinton projects stand, and the strict
    # boundary cannot contain them; whether each was in the by-law in 2014 cannot be checked from open data.
    eg = addr[addr["LINEAR_NAME"].astype(str).str.upper().str.strip().eq("EGLINTON")]
    from missing_middleware.geom_extra_station import point_poly_pairs
    eg_hit = np.unique(point_poly_pairs(eg["x"].to_numpy(), eg["y"].to_numpy(), list(parcels["geometry"]))[1])
    hole_eg = (parcels["zone"].isna() & parcels.index.isin(eg_hit)
               & pd.Series(C.within_distance(pts["x"].to_numpy(), pts["y"].to_numpy(), tpolys, LATER_REZONED_NEAR_M), index=parcels.index))
    t_s, el_s = parcels["treated"] | hole_eg, parcels["eligible"] | hole_eg
    area_s, _ = C.uniform_areas(parcels, t_s, t_s, pd.Series(np.nan, index=parcels.index), level_after, none, none, el_s,
                                in_city=in_city, stations=stations)
    acres_s = parcels[area_s.notna() & el_s].groupby(area_s)["acres"].sum().to_dict()
    q = near.assign(area=area_s.reindex(near["pix"]).values, eligible=el_s.reindex(near["pix"]).fillna(False).astype(bool).values)
    q = q[q["area"].notna() & q["eligible"]].assign(project=lambda d: "tor:" + d["pix"].astype(int).astype(str))
    permits_s = q[["project", "area", "year", "units"]]

    tr = el[el["area"] == C.TREAT].copy()
    dt = tr.dropna(subset=["dose_m"])
    dose_table = pd.DataFrame({"acres": dt["acres"], "old_far": dt["overlay_m"] * FT_PER_M,
                               "new_far": (dt["overlay_m"] + dt["dose_m"]) * FT_PER_M})

    per = C.period_years(effective_year, FIRST_YEAR, LAST_FULL_YEAR)
    alt = C.period_years(ALT_EFFECTIVE_YEAR, FIRST_YEAR, LAST_FULL_YEAR)
    tp = permits[permits["area"] == C.TREAT]
    diag = {
        "rule": rule,
        "bylaw_exceptions_found": sorted(int(e) for e in treat_poly["exc"].unique()),
        "bylaw_exceptions_missing": sorted(set(EXCEPTIONS) - set(int(e) for e in treat_poly["exc"].unique())),
        "bylaw_zone_polygon_acres": round(float(C.parcel_acres(treat_poly).sum()), 1),
        "eligible_parcels_by_area": el.groupby("area").size().to_dict(),
        "permits_new_with_units": int(len(pr)),
        "permits_located_by (address points of the case area only)": located,
        "acres_outside_569_2013_in_ring": round(float(parcels.loc[parcels["zone"].isna() & (orig_area == C.COMP), "acres"].sum()), 1),
        "units_on_lots_outside_569_2013_in_ring": {
            k: int(near.loc[near["pix"].isin(parcels.index[parcels["zone"].isna() & (orig_area == C.COMP)]) & near["year"].isin(v), "units"].sum())
            for k, v in (("before", per["before"]), ("after", per["after"]))},
        "permits_in_aoi_placed_in_parcel_share": round(float(near["pix"].notna().mean()), 4),
        "treatment_units_before": int(tp[tp["year"].isin(per["before"])]["units"].sum()),
        "treatment_units_after": int(tp[tp["year"].isin(per["after"])]["units"].sum()),
        "dose_land_share": round(float(dt["acres"].sum() / tr["acres"].sum()), 3) if len(tr) else None,
        "dose_added_height_m": round(C.dose(pd.DataFrame({"acres": dt["acres"], "old_far": dt["overlay_m"], "new_far": dt["overlay_m"] + dt["dose_m"]})), 2) if len(dt) else None,
        "original_rule_acres": {k: round(v, 1) for k, v in orig_acres.items()},
        "second_comparison_stations": int(len(C.stations_not_upzoned(stations, list(parcels.loc[parcels["area"] == C.TREAT, "geometry"])))),
        "sens_with_later_rezoned_eglinton_lots": _did_row(permits_s, acres_s, per, hole_eg, parcels),
        f"did_effective_{ALT_EFFECTIVE_YEAR}": C.did(permits, acres, alt["before"], alt["after"]) if acres.get(C.TREAT) and acres.get(C.COMP) else None,
    }
    ci = C.CaseInputs(case="toronto_eglinton_2014" if effective_year == EFFECTIVE_YEAR else f"toronto_eglinton_{effective_year}",
                      role="fit", effective_year=effective_year, first_year=FIRST_YEAR, last_full_year=LAST_FULL_YEAR,
                      permits=permits, acres=acres, homes={}, dose_table=dose_table,
                      parking_change="yes, small (Policy Area 4 to 3: lower apartment minimums)", mandate="no",
                      notes="dose is added height in feet on lots with a before height (FSI caps also removed); "
                            "treatment = lots still carrying By-law 1030-2014 exceptions; zoning before not published",
                      dose_unit="height_ft", original_spec=(permits_for(orig_area), orig_acres))
    return ci, diag
