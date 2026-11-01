"""Station-area lot table, step C, for four existing cluster cases: Denver 2018, Portland 2020, Austin 2009,
Salt Lake City 2010 (docs/tod/STATION_AREA_PLAN.md: LOCKED section, owner answers, step C first pass).

Imported by scripts/build_tod_station_lot_table.py (adapter_cases); build(case) returns (D, S) in its schema.

Reform area and stops follow scripts/run_tod_station_area.py (upzoned_points, stops):
    Denver   zone map amendments ORD_YEAR 2018, ORD_NUM 15 and 17; RTD rail stations (existing) inside Denver
    Portland Better Housing by Design zone changes where the proposed zone allows more homes per acre; MAX and
             streetcar stops inside Portland
    Austin   day-one TOD regulating plans minus right-of-way (TROW); MetroRail stations inside Austin
    SLC      2020 zoning, zones starting "TSA"; light rail and streetcar stops (national transit map) inside SLC
Reform stops: within 1/2 mile of the upzoned area. Comparison stops: the city's other stops (in-city comparison,
flagged: these metros have few or no rail stops in other cities with parcel data).

Lots are kept only inside the reform city (census place, 2024 boundary): the new-home sources are city files, so a
lot across the city line would show zero new homes whatever was built there.

New homes per window:
    Denver, Portland, Austin  city permit points, cleaned (see the *_permits functions), each placed on the nearest
                              lot point within 60 m (all city lots, not only those near stops); homes summed by window
    SLC                       the regional Housing Unit Inventory (WFRC/UGRC; units and approximate year built per
                              building), placed the same way; chosen over the county file because the county's
                              house count misses most apartments (SLC lots 62,146 homes vs 106,310 in the inventory)
Existing homes (standing before the before-window starts):
    Denver    parcel units with year built before 2013 (unknown year counts as existing), after removing duplicate
              records (condo master and twin records with no values, identical copies) and non-homes (storage units,
              hotel rooms, nursing beds)
    SLC       inventory units built before 2004 (unknown year counts as existing)
    Portland  2010 census block housing units spread to the block's lots in proportion to lot count, plus homes
              permitted 2010-2012 on each lot (about one year from permit to completion); the taxlot UNITS field
              is blank for most houses, condos and many apartments (256,145 homes on Portland lots)
    Austin    2010 census block housing units minus homes permitted 2002-2008 in the block (completed between
              2003 and April 2010, about one year from permit to completion), spread in proportion to lot count;
              the Travis parcel file has no year built or homes
ADUs are left out of new homes where the source marks them (Portland permits, SLC inventory), as in LA, San Diego and
Honolulu; Denver and Austin permits do not mark ADUs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

CRS = 5070
QUARTER, HALF, MILE = 402.0, 805.0, 1609.0
SNAP_M = 60.0
RP = RAW / "tod_radius_programs"
NC = RAW / "tod_new_cities"

# windows fixed before counting (lot model and new-city test windows; plan, audit section G item 2)
CASES = {"denver_2018": {"before": (2013, 2017), "after": (2019, 2023)},
         "portland_2020": {"before": (2014, 2019), "after": (2021, 2025)},
         "austin_2009": {"before": (2003, 2008), "after": (2010, 2014)},
         "slc_2010": {"before": (2004, 2009), "after": (2011, 2015)}}

# one row per new-building record on a lot in D, from 2000 on (owner: keep the data, compute windows later); see events()
EVENTS: dict[str, pd.DataFrame] = {}

# case: (city label, census place name, state FIPS, BPS place name)
CITY = {"denver_2018": ("Denver", "Denver", "08", "Denver"),
        "portland_2020": ("Portland", "Portland", "41", "Portland"),
        "austin_2009": ("Austin", "Austin", "48", "Austin"),
        "slc_2010": ("Salt Lake City", "Salt Lake City", "49", "Salt Lake City")}


# --------------------------------------------------------------------------- places, stops, reform areas

def city_poly(case: str):
    _, name, st, _ = CITY[case]
    p = gpd.read_file(RAW / "census_cb_2024" / "cb_2024_us_place_500k.zip")
    return p[(p.NAME == name) & (p.STATEFP == st)].to_crs(CRS).geometry.union_all()


def reform_area(case: str) -> gpd.GeoDataFrame:
    if case == "denver_2018":
        z = gpd.read_file(NC / "denver" / "zone_map_amendments.geojson").to_crs(CRS)
        return z[(z.ORD_YEAR == 2018) & z.ORD_NUM.isin([15, 17])][["geometry"]]
    if case == "portland_2020":
        import run_tod_new_city_test as N
        b = gpd.read_file(NC / "portland" / "bhd_zone_changes.geojson").to_crs(CRS)
        return b[b.pr_zone.map(N.PDX_HPA) > b.ex_zone.map(N.PDX_HPA)][["geometry"]]
    if case == "austin_2009":
        a = gpd.read_file(REFERENCE / "tod_austin_dayone_regulating_plans.geojson").to_crs(CRS)
        return a[a.SUBDISTRICT_MAP != "TROW"][["geometry"]]
    s = gpd.read_file(RAW / "tod_slc" / "slc_zoning_2020_jacobs.geojson").to_crs(CRS)
    return s[s.ZONING.str.startswith("TSA")][["geometry"]]


def merge_platforms(g: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Platforms or stop pairs within 150 m are one station (as ntm_stations in the builder)."""
    blobs = g.buffer(75).union_all()
    parts = list(blobs.geoms) if hasattr(blobs, "geoms") else [blobs]
    st = gpd.GeoDataFrame(geometry=[p.centroid for p in parts], crs=CRS)
    j = gpd.sjoin_nearest(st, g[["stop_name", "stop_type_text", "geometry"]], how="left").drop_duplicates(subset="geometry")
    return j.reset_index(drop=True)[["stop_name", "stop_type_text", "geometry"]]


def raw_stops(case: str) -> gpd.GeoDataFrame:
    if case == "denver_2018":
        r = gpd.read_file(NC / "denver" / "rail_stations.geojson")
        r = r[r.STATUS == "Existing"]
        g = gpd.GeoDataFrame({"stop_name": r.STATION_NAME, "stop_type_text": "RTD rail (" + r.LINE_NAME.astype(str) + ")"},
                             geometry=r.geometry, crs=r.crs)
    elif case == "portland_2020":
        r = pd.concat([gpd.read_file(NC / "portland" / f) for f in ("max_stops.geojson", "streetcar_stops.geojson")], ignore_index=True)
        r = r[r.STATUS.fillna("Existing").eq("Existing")]
        g = gpd.GeoDataFrame({"stop_name": r.STATION, "stop_type_text": r.TYPE.astype(str)}, geometry=r.geometry, crs=r.crs)
    elif case == "austin_2009":
        r = gpd.read_file(NC / "austin" / "metrorail_stations.geojson")
        g = gpd.GeoDataFrame({"stop_name": r.NAME, "stop_type_text": "MetroRail (commuter rail, opened 2010)"}, geometry=r.geometry, crs=r.crs)
    else:
        s = pd.DataFrame(json.load(open(RAW / "tod_census_cases" / "ntm_rail_stops.json"))).dropna(subset=["stop_lat", "stop_lon"])
        s = s[s.stop_lon.between(-112.2, -111.7) & s.stop_lat.between(40.6, 40.9)]
        s = s[s.stop_type_text.str.contains("Light rail")]          # TRAX and S-Line; FrontRunner commuter rail left out
        g = gpd.GeoDataFrame({"stop_name": s.stop_name, "stop_type_text": s.stop_type_text.str.strip('"')},
                             geometry=gpd.points_from_xy(s.stop_lon, s.stop_lat), crs=4326)
    return g.to_crs(CRS)


def stops(case: str, area: gpd.GeoDataFrame, poly) -> gpd.GeoDataFrame:
    g = raw_stops(case)
    g = g[g.within(poly)]
    S = merge_platforms(g)
    S["place"] = CITY[case][0]
    S["group"] = np.where(S.distance(area.geometry.union_all()) <= HALF, "reform", "comparison")
    S["stop_id"] = np.arange(len(S))
    return S[["stop_id", "stop_name", "stop_type_text", "group", "place", "geometry"]]


# --------------------------------------------------------------------------- lots

def _gdf(L: pd.DataFrame, x, y) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(L, geometry=gpd.points_from_xy(x, y), crs=4326).to_crs(CRS)


DENVER_NOT_HOMES = "MINI WAREHOUSE"                 # storage units recorded as units
DENVER_NOT_HOMES_CLASS = ("COMMERCIAL-HOTEL", "RESIDENTIAL-NURSING FACILITY")   # rooms and beds (group quarters)


def denver_lots(log: dict) -> gpd.GeoDataFrame:
    d = pd.read_csv(RP / "denver" / "parcels_citywide.csv", low_memory=False).dropna(subset=["cx", "cy"]).reset_index(drop=True)
    u = pd.to_numeric(d.TOT_UNITS, errors="coerce").fillna(0)
    log["denver_units_raw"] = float(u.sum())
    # non-homes recorded as units
    nh = d.COM_STRUCTURE_TYPE.astype(str).str.contains(DENVER_NOT_HOMES) | d.D_CLASS_CN.isin(DENVER_NOT_HOMES_CLASS)
    log["denver_units_nonhomes_zeroed"] = float(u[nh].sum())
    u = u.where(~nh, 0)
    g = gpd.GeoSeries(gpd.points_from_xy(d.cx, d.cy), crs=4326).to_crs(CRS)
    x, y = g.x.values, g.y.values
    # records with no land or building value and several units are condo masters or building twins whose homes also sit
    # on valued records nearby (1,241 of 1,249 have at least as many homes on valued records within 150 m): drop those
    nov = d.APPRAISED_LAND_VALUE.isna() & d.APPRAISED_IMP_VALUE.isna()
    mst = (nov & (u > 1)).values
    tree = cKDTree(np.c_[x[~nov.values], y[~nov.values]])
    uv = u[~nov.values].values
    near = np.array([uv[tree.query_ball_point([x[i], y[i]], 150)].sum() for i in np.where(mst)[0]])
    drop = np.zeros(len(d), bool)
    drop[np.where(mst)[0][near >= u.values[mst]]] = True
    log["denver_units_master_dropped"] = float(u[drop].sum())
    # identical copies of one multi-unit building on several records (same point, homes, year, values)
    yb = pd.concat([pd.to_numeric(d.RES_ORIG_YEAR_BUILT, errors="coerce"), pd.to_numeric(d.COM_ORIG_YEAR_BUILT, errors="coerce")], axis=1)
    yb = yb.where(yb > 0).min(axis=1)
    key = pd.DataFrame({"x": np.round(x), "y": np.round(y), "u": u, "yb": yb, "lv": d.APPRAISED_LAND_VALUE, "iv": d.APPRAISED_IMP_VALUE})
    cp = key.duplicated() & (u > 1) & ~drop
    log["denver_units_copies_dropped"] = float(u[cp].sum())
    u = u.where(~(drop | cp), 0)
    log["denver_units_clean"] = float(u.sum())
    lv, iv = pd.to_numeric(d.APPRAISED_LAND_VALUE, errors="coerce"), pd.to_numeric(d.APPRAISED_IMP_VALUE, errors="coerce")
    L = pd.DataFrame({"city_name": "Denver", "acres": pd.to_numeric(d.LAND_AREA, errors="coerce") / 43560.0,
                      "land_value": lv, "bldg_value": iv, "year_built": yb, "use": d.D_CLASS_CN.astype(str),
                      # tax-exempt for local tax on (nearly) the whole value: public or nonprofit
                      "public": (pd.to_numeric(d.EXEMPT_AMT_LOCAL, errors="coerce").fillna(0) >= 0.95 * (lv.fillna(0) + iv.fillna(0)))
                                & ((lv.fillna(0) + iv.fillna(0)) > 0),
                      "units_now": u, "schednum": pd.to_numeric(d.SCHEDNUM, errors="coerce").astype("Int64").astype(str).str.zfill(13)})
    L["_yb"] = [(int(v) if v == v else 0,) for v in yb]
    L["_un"] = [(float(v),) for v in u]
    return gpd.GeoDataFrame(L, geometry=g.values, crs=CRS)


def portland_lots() -> gpd.GeoDataFrame:
    d = pd.read_csv(RP / "portland" / "taxlots.csv", low_memory=False).dropna(subset=["cx", "cy"])
    yb = pd.to_numeric(d.YEARBUILT, errors="coerce")
    desc = d.PRPCD_DESC.fillna("").astype(str).str.strip('" ')
    use = desc.where(desc != "", d.LANDUSE.fillna("").astype(str))
    L = pd.DataFrame({"city_name": d.SITECITY.fillna("").astype(str).str.title(), "acres": pd.to_numeric(d.A_T_ACRES, errors="coerce"),
                      "land_value": pd.to_numeric(d.LANDVAL1, errors="coerce"), "bldg_value": pd.to_numeric(d.BLDGVAL1, errors="coerce"),
                      "year_built": yb.where(yb.between(1800, 2026)), "use": use,
                      "public": d.LANDUSE.eq("PUB") | desc.str.contains("PUBLIC|PARK|SCHOOL"),
                      "vacant": desc.str.contains("VACANT") | d.LANDUSE.eq("VAC"),
                      "units_now": pd.to_numeric(d.UNITS, errors="coerce")})
    return _gdf(L, d.cx, d.cy)


def austin_lots() -> gpd.GeoDataFrame:
    d = pd.read_csv(RP / "travis" / "parcels.csv", low_memory=False, dtype={"PROP_ID": str}).dropna(subset=["cx", "cy"])
    # land value and zoning are blank in this extract; no year built or homes
    L = pd.DataFrame({"city_name": "Austin", "acres": pd.to_numeric(d.Shape__Area, errors="coerce") / 43560.0,   # sq ft (checked vs polygons)
                      "land_value": pd.to_numeric(d.LAND_VALUE, errors="coerce"), "bldg_value": np.nan, "year_built": np.nan,
                      "use": d.ZONING.fillna("").astype(str), "public": False, "vacant": False, "prop_id": d.PROP_ID.values})
    return _gdf(L, d.cx, d.cy)


def slc_lots() -> gpd.GeoDataFrame:
    d = pd.read_csv(RP / "salt_lake" / "county_parcels.csv", low_memory=False).dropna(subset=["cx", "cy"])
    yb = pd.to_numeric(d.BUILT_YR, errors="coerce")
    lv, tv = pd.to_numeric(d.LAND_MKT_VALUE, errors="coerce"), pd.to_numeric(d.TOTAL_MKT_VALUE, errors="coerce")
    L = pd.DataFrame({"city_name": d.PARCEL_CITY.fillna("").astype(str), "acres": pd.to_numeric(d.PARCEL_ACRES, errors="coerce"),
                      "land_value": lv, "bldg_value": tv - lv, "year_built": yb.where(yb > 1800), "use": d.PROP_CLASS.fillna("").astype(str),
                      "public": d.PROP_CLASS.fillna("").str.startswith("Tax Exempt") | d.TAXEXEMPT_TYPE.notna(),
                      "county_house_cnt": pd.to_numeric(d.HOUSE_CNT, errors="coerce")})
    return _gdf(L, d.cx, d.cy)


# --------------------------------------------------------------------------- new homes

def denver_permits() -> gpd.GeoDataFrame:
    """Denver new-building permits with homes, exactly as run_tod_station_area.permits("Denver"), keeping the schedule
    number so a permit can be placed on its own parcel (58% of homes; the rest were on parcels since re-platted)."""
    d = NC / "denver"
    g = pd.concat([gpd.read_file(d / "residential_permits.geojson"), gpd.read_file(d / "commercial_permits.geojson")], ignore_index=True)
    g["units"] = pd.to_numeric(g.UNITS, errors="coerce").fillna(0)
    g = g[g.CLASS.str.upper().eq("NEW BUILDING") & (g.units > 0) & g.CANCEL.isna() & g.geometry.notna()].to_crs(CRS)
    g["year"] = pd.to_datetime(g.DATE_ISSUED, unit="ms").dt.year
    return g[["year", "units", "SCHEDNUM", "geometry"]].rename(columns={"SCHEDNUM": "key"}).reset_index(drop=True)


PDX_KEEP_STATUS = ("Final", "Issued", "Under Inspection")
PDX_NOT_HOMES = ("Accessory Dwelling Unit", "Hotel/Motel", "Institutional", "Garage/Carport", "Accessory Structure",
                 "Storage", "Business", "Educational", "Mercantile")


def portland_permits() -> gpd.GeoDataFrame:
    """Portland new-construction permits with new homes (as run_tod_station_area.permits), cleaned: issued permits only
    (applications, permits under review, approved-to-issue, expired and on-hold dropped); ADUs (the ADU scenario's),
    hotels, institutions and non-residential types dropped."""
    d = NC / "portland"
    g = pd.concat([gpd.read_file(d / "residential_permits.geojson"), gpd.read_file(d / "commercial_permits.geojson")], ignore_index=True)
    g["units"] = pd.to_numeric(g.NUMNEWUNITS, errors="coerce").fillna(0)
    g = g[(g.units > 0) & g.geometry.notna() & g.STATUS.isin(PDX_KEEP_STATUS) & ~g.TYPE.isin(PDX_NOT_HOMES)].to_crs(CRS)
    g["year"] = pd.to_datetime(g.ISSUED, unit="ms").dt.year
    return g[["year", "units", "geometry"]].reset_index(drop=True)


AUS_KEEP_STATUS = ("Final", "Active")


def austin_permits(L: gpd.GeoDataFrame, log: dict) -> gpd.GeoDataFrame:
    """Austin new-building permits with homes (as run_tod_station_area.permits), cleaned: final or active only (void,
    withdrawn, cancelled and expired dropped); two residential-class permits carrying a whole subdivision (1,201 and
    1,846 homes on one house permit) dropped. Permits without coordinates are placed at their parcel when the record
    carries a TCAD property id ("R" + id); the rest (10-digit geographic ids) cannot be placed and are counted."""
    pm = pd.read_json(NC / "austin" / "permits.json", dtype={"tcad_id": str})
    pm["units"] = pd.to_numeric(pm.housing_units, errors="coerce").fillna(0)
    pm["year"] = pd.to_datetime(pm.issue_date).dt.year
    pm = pm[(pm.units > 0) & pm.status_current.isin(AUS_KEEP_STATUS)]
    bad = (pm.permit_class_mapped == "Residential") & (pm.units > 50)
    log["austin_subdivision_permits_dropped"] = pm[bad][["year", "units"]].to_dict("records")
    pm = pm[~bad].copy()
    log["austin_all_by_year"] = pm.groupby("year").units.sum()
    has = pm.latitude.notna() & pm.longitude.notna()
    a = gpd.GeoDataFrame(pm[has][["year", "units"]], geometry=gpd.points_from_xy(pm[has].longitude, pm[has].latitude), crs=4326).to_crs(CRS)
    rid = pm[~has].tcad_id.fillna("").str.extract(r"^R(\d+)$")[0]
    pt = L.drop_duplicates("prop_id").set_index("prop_id").geometry
    m = rid.map(pt)
    b = gpd.GeoDataFrame(pm[~has][["year", "units"]][m.notna().values], geometry=list(m.dropna().values), crs=CRS)
    log["austin_placed_by_prop_id"] = float(b.units.sum())
    log["austin_unplaceable_by_year"] = pm[~has][m.isna().values].groupby("year").units.sum()
    return pd.concat([a, b], ignore_index=True)


def slc_inventory() -> gpd.GeoDataFrame:
    h = gpd.read_file(NC / "slc" / "housing_unit_inventory.geojson").to_crs(CRS)
    h = h[h.geometry.notna()]
    return gpd.GeoDataFrame({"year": pd.to_numeric(h.APX_BLT_YR, errors="coerce"), "units": pd.to_numeric(h.UNIT_COUNT, errors="coerce").fillna(0),
                             "adu": h.SUBTYPE.eq("single_family_adu").values},
                            geometry=h.geometry.representative_point().values, crs=CRS).query("units > 0").reset_index(drop=True)


def snap(P: gpd.GeoDataFrame, L: gpd.GeoDataFrame) -> np.ndarray:
    """Position (in L) of the lot each point of P is placed on; -1 where none.
    1. Where both carry a parcel key (Denver schedule number), the permit's own parcel, if big enough (rule 3).
    2. Otherwise the nearest lot point that could contain the permit point: within 60 m, or within the lot's own reach
       (0.75 x the side of a square of the lot's area, up to 250 m), since a large lot's centre point can sit far from
       the address point of a building on it.
    3. Among those, only lots big enough to hold the homes (at most 2,000 homes per acre over all records placed on
       the lot, the builder's plausibility line; biggest records placed first): a big permit point often sits nearer a
       small neighbouring lot or a condo-unit point than its own lot.
       If no lot qualifies, the nearest lot within 60 m; if none, unplaced."""
    out = np.full(len(P), -1)
    acres = L.acres.values
    cap = np.nan_to_num(acres, nan=-1) * 2000.0          # homes a lot can plausibly hold (all permits together)
    used = np.zeros(len(L))
    units = P.units.values
    order = np.argsort(-units, kind="stable")             # big permits first
    key = None
    if "key" in P and "key" in L:
        k = pd.Series(np.arange(len(L)), index=L["key"].values)
        k = k[~k.index.duplicated()]
        key = P["key"].map(k).fillna(-1).astype(int).values
    t = cKDTree(np.c_[L.geometry.x.values, L.geometry.y.values])
    dist, idx = t.query(np.c_[P.geometry.x.values, P.geometry.y.values], k=400, distance_upper_bound=250.0)   # many condo-unit points can share one spot
    reach = np.maximum(SNAP_M, 0.75 * np.sqrt(np.nan_to_num(acres, nan=0) * 4046.86))
    for i in order:
        if key is not None and key[i] >= 0 and used[key[i]] + units[i] <= cap[key[i]]:
            out[i] = key[i]          # own parcel (if now too small, e.g. split or condo'd since: placed by distance)
        else:
            ok = np.isfinite(dist[i])
            if not ok.any():
                continue
            cand, dd = idx[i][ok], dist[i][ok]
            fit = cand[(dd <= reach[cand]) & (used[cand] + units[i] <= cap[cand])]
            if len(fit):
                out[i] = fit[0]
            elif dd[0] <= SNAP_M:
                out[i] = cand[0]
            else:
                continue
        used[out[i]] += units[i]
    return out


def sum_by_lot(P: pd.DataFrame, pos: np.ndarray, n: int, y0: float, y1: float) -> np.ndarray:
    m = (pos >= 0) & P.year.between(y0, y1).values
    return np.bincount(pos[m], weights=P.units.values[m], minlength=n)


# --------------------------------------------------------------------------- census blocks

def blocks2010(state: str, poly) -> gpd.GeoDataFrame:
    f = RAW / "tod_census_cases" / f"tabblock2010_{state}_pophu.zip"
    bb = gpd.GeoSeries([poly], crs=CRS).to_crs(4269).total_bounds
    b = gpd.read_file(f, bbox=tuple(bb)).to_crs(CRS)
    return b[["BLOCKID10", "HOUSING10", "geometry"]]


def spread_blocks(L: gpd.GeoDataFrame, B: gpd.GeoDataFrame, homes_b: pd.Series, weight: np.ndarray, inb: pd.Series,
                  log: dict, tag: str) -> np.ndarray:
    """Spread block homes (homes_b, indexed by BLOCKID10) to the block's lots in proportion to weight (lot count,
    vacant and public lots weighted 0 unless the block has no other lots)."""
    j = gpd.sjoin(L[["geometry"]], B[["BLOCKID10", "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated()]
    blk = j.BLOCKID10.reindex(L.index).values
    w = pd.Series(weight, index=L.index, dtype=float)
    wsum = w.groupby(blk).sum()
    cnt = pd.Series(1.0, index=L.index).groupby(blk).sum()
    use_cnt = pd.Series(blk).map(wsum).fillna(0).values == 0             # block with only vacant/public lots
    ww = np.where(use_cnt, 1.0, w.values)
    den = np.where(use_cnt, pd.Series(blk).map(cnt).values, pd.Series(blk).map(wsum).values)
    h = pd.Series(blk).map(homes_b).fillna(0).values
    out = np.where(den > 0, h * ww / np.where(den > 0, den, 1), 0.0)
    # blocks holding homes but no lot point (small blocks whose lots' points fall next door): homes to the nearest lot
    lotless = homes_b[~homes_b.index.isin(pd.unique(blk[pd.notna(blk)])) & (homes_b > 0) & inb.reindex(homes_b.index).values]
    if len(lotless):
        rp = B.set_index("BLOCKID10").loc[lotless.index].representative_point()
        dist, nn = cKDTree(np.c_[L.geometry.x.values, L.geometry.y.values]).query(np.c_[rp.x.values, rp.y.values])
        np.add.at(out, nn, lotless.values)
        log[f"{tag}_lotless_block_homes_to_nearest_lot"] = f"{lotless.sum():,.0f} homes, max distance {dist.max():,.0f} m"
    log[f"{tag}_lots_outside_blocks"] = int(pd.isna(blk).sum())
    return out


# --------------------------------------------------------------------------- build

def bps(case: str) -> pd.Series:
    from missing_middleware.tod.control_cities import read_bps
    _, _, st, nm = CITY[case]
    b = read_bps(RAW / "tod_control_cities" / "bps", years=range(2000, 2026))
    return b[(b.state == st) & (b.name == nm)].groupby("year").units.sum()


def events(case: str, P: pd.DataFrame, pos: np.ndarray, L: pd.DataFrame, D: pd.DataFrame) -> pd.DataFrame:
    """One row per new-building record placed on a lot in D, from 2000 on (ADUs left out, as in the window counts).
    Columns: lot_index (D's index), homes, permit_year, completed_year, preferred ("permit" when a permit year exists,
    else "completed"), source, match.
    Denver has both dates: each permit is matched to its lot's parcel year built when that year is 0-5 years after the
    permit year (match "both"); a lot with a year built from 2000 on and no matching permit gives a "completed_only"
    row with the lot's units ("completed_only_near_permit" when a permit for as many or more homes, issued 0-5 years
    before, lies on another lot within 100 m: likely the same building, e.g. condo-unit parcels; do not add it to the
    permit rows). Portland and Austin: permits only (taxlot year built is blank for units on most lots; Travis file
    has no year built). Salt Lake City: completions only (housing unit inventory year built)."""
    inD = (pos >= 0) & np.isin(pos, D.index.values)
    if case == "slc_2010":
        y = P.year.values[inD]
        E = pd.DataFrame({"lot_index": pos[inD], "homes": P.units.values[inD], "permit_year": np.nan, "completed_year": y,
                          "preferred": "completed", "source": "SLC housing unit inventory (year built)", "match": "completed_only"})
        return E[E.completed_year >= 2000].reset_index(drop=True)
    src = {"denver_2018": "Denver building permits", "portland_2020": "Portland building permits (no ADUs)",
           "austin_2009": "Austin building permits"}[case]
    E = pd.DataFrame({"lot_index": pos[inD], "homes": P.units.values[inD], "permit_year": P.year.values[inD].astype(float),
                      "completed_year": np.nan, "preferred": "permit", "source": src, "match": "permit_only"})
    E = E[E.permit_year >= 2000].reset_index(drop=True)
    if case != "denver_2018":
        return E
    yb = D.year_built.reindex(E.lot_index).values
    ok = (yb - E.permit_year.values >= 0) & (yb - E.permit_year.values <= 5)
    E.loc[ok, "completed_year"] = yb[ok]
    E.loc[ok, "match"] = "both"
    E.loc[ok, "source"] = "Denver building permits + parcel year built"
    units = L.units_now.reindex(D.index)
    lots = D[(D.year_built >= 2000) & (units > 0) & ~D.index.isin(E.lot_index[ok])]
    C = pd.DataFrame({"lot_index": lots.index.values, "homes": units.loc[lots.index].values, "permit_year": np.nan,
                      "completed_year": lots.year_built.values, "preferred": "completed",
                      "source": "Denver parcel year built x units", "match": "completed_only"})
    # completed-only rows near a permit for as many homes issued 0-5 years before: likely the same building
    t = cKDTree(np.c_[D.geometry.x.reindex(E.lot_index).values, D.geometry.y.reindex(E.lot_index).values])
    near = t.query_ball_point(np.c_[lots.geometry.x.values, lots.geometry.y.values], 100.0)
    py, ph = E.permit_year.values, E.homes.values
    same = [any((0 <= cy - py[j] <= 5) and ph[j] >= h for j in nb) for nb, cy, h in zip(near, C.completed_year.values, C.homes.values)]
    C.loc[np.array(same, bool), "match"] = "completed_only_near_permit"
    return pd.concat([E, C], ignore_index=True)


def coverage_poly(case: str):
    """The reform city, cut to the area the lot file covers (Austin: the Travis County part; 8% of the city's land, in
    Williamson and Hays counties, has no lots in the Travis file)."""
    poly = city_poly(case)
    if case == "austin_2009":
        c = gpd.read_file(RAW / "census_cb_2024" / "cb_2024_us_county_500k.zip")
        poly = poly.intersection(c[(c.STATEFP == "48") & (c.COUNTYFP == "453")].to_crs(CRS).geometry.iloc[0])
    return poly


def build(case: str):
    c = CASES[case]
    b0, b1 = c["before"]; a0, a1 = c["after"]
    log: dict = {}
    poly = coverage_poly(case)
    area = reform_area(case)
    S = stops(case, area, poly)

    loader = {"denver_2018": lambda: denver_lots(log), "portland_2020": portland_lots, "austin_2009": austin_lots,
              "slc_2010": slc_lots}[case]
    # all lots in and around the city (lots across the line are needed to spread census blocks that straddle it);
    # only lots inside the city are kept in the table (new-home sources are city files)
    L = loader()
    L = L[L.within(poly.buffer(2000))].reset_index(drop=True)
    incity = L.within(poly).values
    if case == "denver_2018":
        L["key"] = L.pop("schednum")
    n = len(L)

    P = {"denver_2018": denver_permits, "portland_2020": portland_permits, "slc_2010": slc_inventory}.get(case)
    P = P() if P else austin_permits(L, log)
    P = P[P.within(poly)].reset_index(drop=True) if case == "austin_2009" else P   # Travis part only (lot file coverage)
    pos = snap(P, L)
    pos = np.where((pos >= 0) & incity[np.maximum(pos, 0)], pos, -1)          # placed on a lot outside the city: unplaced
    notadu = ~P["adu"].values if "adu" in P else np.ones(len(P), bool)     # ADUs out of new homes
    Pn, posn = P[notadu], pos[notadu]
    before = sum_by_lot(Pn, posn, n, b0, b1)
    after = sum_by_lot(Pn, posn, n, a0, a1)
    for lab, (y0, y1) in (("before", (b0, b1)), ("after", (a0, a1))):
        m = Pn.year.between(y0, y1).values
        log[f"new_{lab}_all"] = float(Pn.units.values[m].sum())
        log[f"new_{lab}_unplaced"] = float(Pn.units.values[m & (posn < 0)].sum())

    if case == "denver_2018":
        # parcel units standing before the window (unknown year counts as existing), as the builder's homes_before
        existing = np.where(L.year_built.values >= b0, 0.0, L.units_now.values)
        src = "new: city permits placed on lots; existing: parcel units by year built (duplicates removed)"
    elif case == "slc_2010":
        # inventory homes standing before 2004 (unknown year counts as existing; ADUs included in existing homes)
        ex = (pos >= 0) & ~(P.year.values >= b0)
        existing = np.bincount(pos[ex], weights=P.units.values[ex], minlength=n)
        log["existing_unplaced"] = float(P.units.values[~(P.year.values >= b0) & (pos < 0)].sum())
        src = "new and existing: WFRC/UGRC housing unit inventory (year built x units) placed on county lots"
    else:
        B = blocks2010(CITY[case][2], poly.buffer(2000))
        weight = (~(L.vacant.values | L.public.values.astype(bool))).astype(float)
        bj = gpd.sjoin(L[["geometry"]], B[["BLOCKID10", "geometry"]], how="left", predicate="within")
        bj = bj[~bj.index.duplicated()].BLOCKID10.reindex(L.index)
        hu = B.set_index("BLOCKID10").HOUSING10.astype(float)
        inb = B.set_index("BLOCKID10").representative_point().within(poly)
        log["census2010_homes_in_city_blocks"] = float(hu[inb].sum())
        if case == "portland_2020":
            # homes standing at the start of 2014: 2010 census + homes permitted 2010-2012 (on their own lots)
            base = spread_blocks(L, B, hu, weight, inb, log, "census2010")
            add = sum_by_lot(Pn, posn, n, 2010, 2012)
            existing = base + add
            log["existing_added_permits_2010_2012"] = float(add.sum())
            src = ("new: city permits placed on lots (ADUs and hotels out); existing: 2010 census blocks spread by lot "
                   "count + homes permitted 2010-2012")
        else:
            # homes standing at the start of 2003: 2010 census minus homes permitted 2002-2008, by block
            sub = sum_by_lot(P, pos, n, 2002, 2008)
            pb = pd.Series(sub, index=L.index).groupby(bj.values).sum().reindex(hu.index).fillna(0)
            net = hu.sub(pb)
            log["austin_permits_2002_2008_subtracted"] = float(pb.sum())
            log["austin_blocks_negative"] = int((net < 0).sum())
            log["austin_homes_clipped_at_0"] = float(-net[net < 0].sum())
            neg = net[net < 0]
            existing = spread_blocks(L, B, net.clip(lower=0), weight, inb, log, "census2010_net")
            src = ("new: city permits placed on lots (no coordinates: by TCAD id); existing: 2010 census blocks minus "
                   "homes permitted 2002-2008, spread by lot count")
    if case != "denver_2018":
        L["_yb"] = [()] * n
        L["_un"] = [()] * n
    existing = np.where(incity, existing, 0.0)
    L = L[incity]

    # lots within 1 mile of any kept stop
    near = gpd.sjoin_nearest(L[["geometry"]], S[["stop_id", "group", "geometry"]], how="inner", max_distance=MILE, distance_col="dist_m")
    near = near[~near.index.duplicated()]
    idx = near.index.values
    D = L.loc[idx].copy()
    D[["stop_id", "group", "dist_m"]] = near[["stop_id", "group", "dist_m"]]
    D["band"] = pd.cut(D.dist_m, [-1, QUARTER, HALF, MILE], labels=["0-1/4", "1/4-1/2", "1/2-1"]).astype(str)
    inr = gpd.sjoin(D[["geometry"]], area, how="left", predicate="within")
    D["in_reform_area"] = inr.index_right.notna().groupby(level=0).any().reindex(D.index).values
    D["homes_before_win"] = before[idx]
    D["homes_after_win"] = after[idx]
    D["homes_existing"] = existing[idx]
    D["source"] = src
    D["case"] = case
    D["implausible"] = False
    D["public"] = D.public.astype(bool)
    keep = ["case", "city_name", "group", "stop_id", "dist_m", "band", "in_reform_area", "acres", "land_value", "bldg_value",
            "year_built", "use", "public", "homes_existing", "homes_before_win", "homes_after_win", "source", "implausible",
            "_yb", "_un", "geometry"]
    D = gpd.GeoDataFrame(D[keep], geometry="geometry", crs=CRS)
    D["city_name"] = CITY[case][0]

    EVENTS[case] = events(case, Pn, posn, L, D)
    ev = EVENTS[case]
    print(f"--- {case} events: {len(ev):,} rows, {ev.homes.sum():,.0f} homes; by match: "
          + ", ".join(f"{k} {v:,.0f}" for k, v in ev.groupby("match").homes.sum().items()))

    # ---- diagnostics (printed; nothing written outside data/)
    bp = bps(case)
    yrs = lambda y0, y1: float(bp.loc[y0:y1].sum())
    print(f"--- {case} diagnostics")
    print(f"city lots {int(incity.sum()):,}; lots within 1 mile {len(D):,}; stops {len(S)} (reform {int((S.group == 'reform').sum())})")
    for k, v in log.items():
        if isinstance(v, pd.Series):
            v = {int(a): int(b) for a, b in v.loc[2000:2025].items()}
        print(f"  {k}: {v}")
    for lab, (y0, y1) in (("before", (b0, b1)), ("after", (a0, a1))):
        tot = log[f"new_{lab}_all"]
        if "austin_all_by_year" in log:      # all cleaned permits, incl. no coordinates and the Williamson/Hays part
            allp = float(log["austin_all_by_year"].loc[y0:y1].sum())
            print(f"  {lab} {y0}-{y1}: all cleaned city permits {allp:,.0f}; Census ratio {allp / yrs(y0, y1):.2f}; "
                  f"placed on lots {tot - log[f'new_{lab}_unplaced']:,.0f} ({(tot - log[f'new_{lab}_unplaced']) / allp:.2f} of all)")
        print(f"  {lab} {y0}-{y1}: source homes {tot:,.0f} (unplaced {log[f'new_{lab}_unplaced']:,.0f}); "
              f"Census permits {yrs(y0, y1):,.0f}; ratio {tot / yrs(y0, y1):.2f}; "
              f"two-year-earlier Census permits {yrs(y0 - 2, y1 - 2):,.0f} (ratio {tot / yrs(y0 - 2, y1 - 2):.2f})")
    print(f"  existing homes before {b0}: city lots {existing.sum():,.0f}; within 1 mile {D.homes_existing.sum():,.0f}")
    print(f"  lots in reform area within 1 mile: {int(D.in_reform_area.sum()):,}")
    if case == "austin_2009":
        nb = neg[neg.index.isin(pd.unique(bj.loc[D.index].dropna()))]
        print(f"  blocks with more homes permitted 2002-2008 than standing in 2010, within 1 mile: {len(nb)} "
              f"({-nb.sum():,.0f} homes clipped)")
    return D, S
