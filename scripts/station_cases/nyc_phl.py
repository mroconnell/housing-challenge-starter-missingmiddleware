"""New York and Philadelphia station-area lot tables (docs/tod/STATION_AREA_PLAN.md: LOCKED, city list decision,
owner answers of 15:57: each city's many rezonings are averaged into one case for city-level tests).

Cases: one per rezoning in the lot model (data/processed/tod_lot_model/lots_rebuilt_halfmile.parquet, placebo rows
left out): New York 23 (nyc_<ULURP no.>), Philadelphia 85 (phl_<bill no.>). Windows exactly as case_windows() in
scripts/run_tod_station_area.py: before = window_first..eff-1, after = eff+1..window_last.

Stops
- New York: subway stations (subway_stations.geojson), entries within 150 m merged into one station.
- Philadelphia: SEPTA rail, subway/elevated and trolley stops inside the city (rail_stops.geojson; platforms and
  entrances left out), merged within 150 m by type.
- Reform stops: within 1/2 mile (805 m) of the rezoning's treated (upzoned) lots in the lot model.
- Comparison stops (in-city, flagged): the city's other stops of the same type(s) as the reform stops, not within
  1/2 mile of the treated lots of any other lot-model rezoning in the same city effective within this case's
  before..after span. Rezonings with no treated lots have no reform stops (comparison only; flagged).
  New York lots also carry stop_near_other_zma: their nearest stop is within 1/2 mile of another adopted zoning map
  amendment (nyzma.geojson, any kind, effective in the span) that is not one of the lot model's 23.

Lots
- New York: MapPLUTO lots (XCoord/YCoord, NY state plane feet). Vintage = the last release dated the year before the
  reform (e.g. 02b for 2003); existing homes = UnitsRes on lots whose YearBuilt (same vintage) is before the before
  window (unknown year counts as existing); land value AssessLand, building value AssessTot - AssessLand (02b and 03c
  lack AssessTot: 04c values used, flagged); use LandUse; public = OwnerType C, M or O. year_built and homes_18v1
  from MapPLUTO 18v1 by lot number.
- Philadelphia: Water Department parcels (lot = parcel, point = representative point, acres from the shape);
  values = OPA assessments summed over the OPA points inside the parcel, for the year before the reform (2015 is the
  first year in the file, used for earlier reforms, flagged); use = building description; public = land fully
  tax-exempt (includes non-profits, flagged). OPA has no homes field, so existing homes = 2010 census block homes
  spread over the block's lots by building-type weights (row/semi/detached 1, converted 2.5, 2-4 units 3, 5-50
  units 20, 51-100 units 75, condo building 8, mixed store/apartments 2; others 0; equal split if a block has homes
  but no weighted lot).

New homes: city permits on both sides (in-city comparison): run_tod_station_area.permits() (New York: DOB
new-building jobs by fully-permitted year; Philadelphia: L&I new-construction permits by issue year, cleaned here as in
missing_middleware.tod.case_philadelphia: whole-building permit types only, staged duplicates merged). Each permit
is placed on the nearest lot (whole city) within 60 m; homes summed per lot and window. Parcel ids stay in data/.

City-level data are cached in data/processed/tod_station_area/nyc_phl_cache/ (local only).
"""
from __future__ import annotations

import sys
import zipfile
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware import geom as GM  # noqa: E402
from missing_middleware import geom_extra_station as X  # noqa: E402
from missing_middleware.paths import RAW  # noqa: E402

CRS = 5070
QUARTER, HALF, MILE = 402.0, 805.0, 1609.0
SNAP_PERMIT, SNAP_TREATED = 60.0, 30.0
NYC_DIR = RAW / "tod_cases" / "nyc"
PHL_DIR = RAW / "tod_cases" / "philadelphia"
CACHE = ROOT / "data" / "processed" / "tod_station_area" / "nyc_phl_cache"
LOT_MODEL = ROOT / "data" / "processed" / "tod_lot_model" / "lots_rebuilt_halfmile.parquet"
CITY = {"nyc": "New York", "phl": "Philadelphia"}
# One row per new-building record placed on a lot of D, per built case (owner contract addition): lot_index (row of D),
# homes, permit_year, completed_year, preferred ("permit" when both exist), source. All years from 2000 on.
EVENTS: dict[str, pd.DataFrame] = {}
NOT_HOMES_PHL = r"HOTEL|DORM|\bADU\b|ACCESSORY DWELL|ROOMING|STUDENT HOUS|\bBEDS\b|NURSING"


# --------------------------------------------------------------------------- cases

def _cases() -> dict:
    d = pd.read_parquet(LOT_MODEL, columns=["city", "unit", "eff_year", "window_first", "window_last", "placebo"])
    d = d[d.city.isin(CITY.values()) & (d.placebo != 1)].drop_duplicates(["city", "unit"])
    out = {}
    for r in d.sort_values("unit").itertuples():
        e = int(r.eff_year)
        out[str(r.unit)] = {"eff": e, "before": (int(r.window_first), e - 1), "after": (e + 1, int(r.window_last)),
                            "city": r.city}
    return out


CASES = _cases()


@lru_cache(maxsize=1)
def _treated() -> pd.DataFrame:
    d = pd.read_parquet(LOT_MODEL, columns=["city", "unit", "treated", "placebo", "x5070", "y5070"])
    return d[d.city.isin(CITY.values()) & (d.placebo != 1) & (d.treated == 1)].assign(unit=lambda x: x.unit.astype(str))


# --------------------------------------------------------------------------- stops

def _merge(g: pd.DataFrame, name: str, kind: str) -> pd.DataFrame:
    """Platforms within 150 m are one station (union of 75 m GEOS buffers), named after the nearest stop."""
    cx, cy, i = X.merge_stops(g.x.values, g.y.values, 75.0)
    return pd.DataFrame({"stop_name": g[name].values[i], "stop_type_text": kind, "x": cx, "y": cy})


@lru_cache(maxsize=2)
def stops(city: str) -> pd.DataFrame:
    if city == "nyc":
        g = X.read_vector(NYC_DIR / "subway_stations.geojson", dst=CRS)
        S = _merge(g, "STATION", "Subway")
        S["place"] = "New York"
    else:
        g = X.read_vector(PHL_DIR / "rail_stops.geojson", dst=CRS)
        g = g[g.location_type.astype(str).isin(["Null", "0", "None", "nan", ""])].copy()
        g["kind"] = g.stop_type_text.str.strip('"').replace({"Subway, Metro": "Subway/elevated",
                                                             "Tram, Streetcar, Light rail": "Trolley"})
        p = X.read_vector(RAW / "census_cb_2024" / "cb_2024_us_place_500k.zip", dst=CRS, columns=["NAME", "STATEFP"])
        poly = list(p[(p.STATEFP == "42") & (p.NAME == "Philadelphia")].geometry)
        g = g[GM.points_in_any(g.x.values, g.y.values, poly, union=True)]
        S = pd.concat([_merge(gg, "stop_name", k) for k, gg in g.groupby("kind")], ignore_index=True)
        S["place"] = "Philadelphia"
    S["stop_id"] = np.arange(len(S))
    return S


# --------------------------------------------------------------------------- New York lots (MapPLUTO)

BORO = {"MN": 1, "BX": 2, "BK": 3, "QN": 4, "SI": 5}
PLUTO_FIELDS = ["borough", "block", "lot", "landuse", "ownertype", "lotarea", "unitsres", "assessland", "assesstot",
                "yearbuilt", "xcoord", "ycoord"]


def _vintage_for(eff: int) -> str:
    """Last MapPLUTO release dated the year before the reform."""
    yy = f"{(eff - 1) % 100:02d}"
    have = sorted(p.stem.split("_")[1] for p in NYC_DIR.glob(f"mappluto_{yy}*.zip"))
    if not have:
        raise FileNotFoundError(f"no MapPLUTO for 20{yy}")
    return have[-1]


def _dbf_fields(data: bytes) -> list[str]:
    """Field names of a dBASE table."""
    out, pos = [], 32
    while data[pos] != 0x0D:
        out.append(data[pos:pos + 11].split(b"\x00")[0].decode("ascii"))
        pos += 32
    return out


def _pluto_raw(v: str) -> pd.DataFrame:
    z = NYC_DIR / f"mappluto_{v}.zip"
    zf = zipfile.ZipFile(z)
    names = [n for n in zf.namelist() if n.lower().endswith("mappluto.dbf")]
    out = []
    for n in names:
        data = zf.read(n)
        cols = {c.lower(): c for c in _dbf_fields(data)}
        d, _ = X._dbf_columns(data, [cols[f] for f in PLUTO_FIELDS if f in cols], "latin-1")
        d.columns = [c.lower() for c in d.columns]
        out.append(d)
    d = pd.concat(out, ignore_index=True)
    for f in PLUTO_FIELDS:
        if f not in d:
            d[f] = np.nan
    b = d.borough.astype(str).str.strip().str.upper().map(BORO)
    d["bbl"] = (b * 1_000_000_000 + pd.to_numeric(d.block, errors="coerce") * 10_000 + pd.to_numeric(d.lot, errors="coerce"))
    for f in ("lotarea", "unitsres", "assessland", "assesstot", "yearbuilt", "xcoord", "ycoord"):
        d[f] = pd.to_numeric(d[f], errors="coerce")
    d = d.dropna(subset=["bbl"]).drop_duplicates("bbl")
    return d[["bbl"] + [f for f in PLUTO_FIELDS if f not in ("borough", "block", "lot")]]


def pluto(v: str) -> pd.DataFrame:
    """One MapPLUTO vintage, slim, with x/y in EPSG 5070 (missing coordinates filled from 18v1 by lot number)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"pluto_{v}.parquet"
    if f.exists():
        return pd.read_parquet(f)
    d = _pluto_raw(v)
    if v != "18v1":
        r = pluto("18v1").set_index("bbl")
        bad = ~(d.xcoord > 0) | ~(d.ycoord > 0)
        d["x"], d["y"] = np.nan, np.nan
        x, y = X.transform(d.xcoord.values.astype(float), d.ycoord.values.astype(float), 2263, CRS)
        d["x"], d["y"] = np.where(bad, d.bbl.map(r.x), x), np.where(bad, d.bbl.map(r.y), y)
        d["year_built_18"] = d.bbl.map(r.yearbuilt.where(r.yearbuilt > 0))
        d["homes_18v1"] = d.bbl.map(r.unitsres)
        # releases without total assessment or land use: take them from 04c by lot number (flagged)
        if d.assesstot.isna().all() or d.landuse.isna().all():
            f4 = _pluto_raw("04c").set_index("bbl")
            if d.assesstot.isna().all():
                d["assesstot"] = d.bbl.map(f4.assesstot)
                d["assessland"] = d.bbl.map(f4.assessland)
                d["values_from"] = "04c"
            if d.landuse.isna().all():
                d["landuse"] = d.bbl.map(f4.landuse)
        if "values_from" not in d:
            d["values_from"] = v
    else:
        ok = (d.xcoord > 0) & (d.ycoord > 0)
        x, y = X.transform(d.xcoord.values.astype(float), d.ycoord.values.astype(float), 2263, CRS)
        d["x"], d["y"] = np.where(ok, x, np.nan), np.where(ok, y, np.nan)
    d = d.dropna(subset=["x", "y"]).reset_index(drop=True)
    d["landuse"] = d.landuse.astype(str)
    d["ownertype"] = d.ownertype.astype(str)
    d.to_parquet(f)
    return d


def lots18_polys() -> pd.DataFrame:
    """MapPLUTO 18v1 lot shapes (bbl, geometry = geom.py features in EPSG 5070). Read from the GeoParquet cache
    written before the port when present (WKB decoded here), else from the shapefiles (not cached: writing GeoParquet
    would need a WKB writer, and the cache is only needed for vintages without a lot-number map)."""
    f = CACHE / "pluto_18v1_shapes.parquet"
    if f.exists():
        L = X.read_geoparquet_wkb(f, columns=["bbl"])
        return pd.DataFrame({"bbl": L.attrs.bbl.values, "geometry": L.polys})
    z = NYC_DIR / "mappluto_18v1.zip"
    out = []
    for n in [n for n in zipfile.ZipFile(z).namelist() if n.lower().endswith("mappluto.shp")]:
        out.append(X.read_vector(f"zip://{z}!{n}", dst=CRS, columns=["BBL"]))
    g = pd.concat(out, ignore_index=True)
    g["bbl"] = pd.to_numeric(g.BBL, errors="coerce")
    return g.dropna(subset=["bbl"]).drop_duplicates("bbl")[["bbl", "geometry"]].reset_index(drop=True)


def to18(v: str) -> pd.Series:
    """Lot number in 18v1 holding each lot of vintage v: same number if the 18v1 shape contains the old point, else
    the 18v1 shape that contains it (lots merged or split since), else none (-1). Cached."""
    f = CACHE / f"map_{v}_to_18v1.parquet"
    if f.exists():
        return pd.read_parquet(f).set_index("bbl").bbl18
    L = pluto(v)
    P = lots18_polys()
    pi, gi = X.point_poly_pairs(L.x.values, L.y.values, list(P.geometry))
    pairs = pd.DataFrame({"bbl18": P.bbl.values[gi]}, index=pi)
    j = pd.DataFrame({"bbl": L.bbl.values}).join(pairs, how="left")          # every match, as sjoin 'within' (left)
    j["same"] = j.bbl == j.bbl18
    j = j.sort_values("same", ascending=False, kind="stable")
    j = j[~j.index.duplicated()].sort_index()
    # fit-and-fix 4: lot number first (02b and 03c lot points often fall outside their 18v1 shape, which left 96% of
    # their lots unmatched and duplicated beside the 18v1 lots); the shape containing the point only when the number
    # is gone (lots merged or split)
    same_no = j.bbl.isin(P.bbl)
    m = pd.DataFrame({"bbl": j.bbl.values, "bbl18": np.where(same_no, j.bbl, j.bbl18.fillna(-1))})
    m.to_parquet(f)
    return m.set_index("bbl").bbl18


def nyc_lots(v: str, b0: int) -> pd.DataFrame:
    """Lots = 18v1 lots (after assemblages and splits), with the vintage-v lots inside each folded in: existing homes
    (UnitsRes of lots built before b0 or of unknown year), land and building values summed; use, owner type from the
    largest old lot. Old lots in no 18v1 shape stay as their own lot."""
    o = pluto(v).copy()
    o["k"] = o.bbl.map(to18(v)).fillna(-1)
    o.loc[o.k < 0, "k"] = -o.bbl[o.k < 0]
    yb = o.yearbuilt.where(o.yearbuilt > 0)
    o["he"] = np.where(yb >= b0, 0.0, o.unitsres.fillna(0))
    o["bv"] = o.assesstot - o.assessland
    big = o.sort_values("lotarea", ascending=False).drop_duplicates("k").set_index("k")
    agg = o.groupby("k").agg(homes_existing=("he", "sum"), land_value=("assessland", "sum"), bldg_value=("bv", "sum"),
                             n_old=("bbl", "size"), old_area=("lotarea", "sum"))
    n = pluto("18v1").set_index("bbl")
    keys = np.union1d(n.index.values, agg.index.values)
    L = pd.DataFrame(index=pd.Index(keys, name="k"))
    in18 = L.index.isin(n.index)
    L["x"] = np.where(in18, n.x.reindex(L.index), big.x.reindex(L.index))
    L["y"] = np.where(in18, n.y.reindex(L.index), big.y.reindex(L.index))
    L["acres"] = np.where(in18, n.lotarea.reindex(L.index), agg.old_area.reindex(L.index)) / 43560.0
    L["homes_existing"] = agg.homes_existing.reindex(L.index).fillna(0)
    L["land_value"] = agg.land_value.reindex(L.index)
    L["bldg_value"] = agg.bldg_value.reindex(L.index)
    L["use"] = big.landuse.reindex(L.index).fillna(n.landuse.reindex(L.index)).astype(str)
    L["public"] = big.ownertype.reindex(L.index).fillna(n.ownertype.reindex(L.index)).astype(str).str.upper().isin(["C", "M", "O"])
    L["year_built"] = n.yearbuilt.where(n.yearbuilt > 0).reindex(L.index)
    L["homes_18v1"] = n.unitsres.reindex(L.index)
    L["values_from"] = o.values_from.iloc[0]
    L = L.dropna(subset=["x", "y"]).reset_index()
    return L


def nyc_permits_bbl() -> pd.DataFrame:
    """run_tod_station_area.permits('New York') rows (same filters), with the job's lot number kept for placing."""
    d = pd.read_csv(NYC_DIR / "dob_nb_all.csv", low_memory=False)
    d = d[d.job_type == "NB"]
    d["units"] = pd.to_numeric(d.proposed_dwelling_units, errors="coerce").fillna(0)
    d["year"] = pd.to_numeric(d.fully_permitted.astype(str).str[-4:], errors="coerce")
    d = d.drop_duplicates(subset=["job__"])
    d = d[d.units > 0].dropna(subset=["gis_longitude", "gis_latitude", "year"])
    b = d.borough.astype(str).str.upper().map({"MANHATTAN": 1, "BRONX": 2, "BROOKLYN": 3, "QUEENS": 4, "STATEN ISLAND": 5})
    d["bbl"] = b * 1_000_000_000 + pd.to_numeric(d.block, errors="coerce") * 10_000 + pd.to_numeric(d.lot, errors="coerce")
    # fit-and-fix 1: "1-2-3 family" jobs at most 3 homes (two such jobs carry 3,291 and 4,871 homes; 11,001 homes in all
    # above 3); fit-and-fix 2: the same lot and home count fully permitted again within 2 years is one building (refiled job)
    d.loc[d.building_type.astype(str).str.strip() == "1-2-3 FAMILY", "units"] = d.units.clip(upper=3)
    d = d.sort_values(["bbl", "units", "year"])
    same = (d.bbl == d.bbl.shift()) & (d.units == d.units.shift()) & ((d.year - d.year.shift()) <= 2)
    d = d[~same]
    gx, gy = X.transform(d.gis_longitude.astype(float).values, d.gis_latitude.astype(float).values, 4326, CRS)
    p = pd.DataFrame({"year": d.year.values, "units": d.units.values, "bbl": d.bbl.values, "x": gx, "y": gy})
    return _move_to_building_lot(p)


def _move_to_building_lot(p: pd.DataFrame) -> pd.DataFrame:
    """Fit-and-fix 3: a job of 20+ homes often names one tax lot of a multi-lot zoning lot (or the lot before a condo was
    formed), which in 18v1 holds no homes while the building sits on a neighbouring lot of the same tax block. Such a job
    is moved to the lot of its tax block within 150 m whose 18v1 homes are closest to the job's count (at least half
    of it) and whose 18v1 year built is no earlier than the permit year minus 1 (permits up to 2017 only)."""
    n = pluto("18v1")
    n = n[n.unitsres > 0][["bbl", "x", "y", "unitsres", "yearbuilt"]].assign(blk=lambda x: x.bbl // 10_000)
    h = n.set_index("bbl").unitsres
    p = p.copy()
    p["moved"] = False
    c = p[(p.units >= 20) & (p.year <= 2017) & (p.bbl.map(h).fillna(0) < 0.5 * p.units)].assign(blk=lambda x: x.bbl // 10_000)
    m = c.reset_index().merge(n, on="blk", suffixes=("", "_n"))
    m = m[(np.hypot(m.x - m.x_n, m.y - m.y_n) <= 150) & (m.unitsres >= 0.5 * m.units) & (m.yearbuilt >= m.year - 1)]
    m = m.assign(gap=(m.unitsres - m.units).abs()).sort_values("gap").drop_duplicates("index").set_index("index")
    p.loc[m.index, "bbl"] = m.bbl_n
    p.loc[m.index, "moved"] = True
    return p


# --------------------------------------------------------------------------- Philadelphia lots

HOME_WEIGHTS = [(r"APTS?\s*51-100", 75.0), (r"APTS?\s*(?:100|101)", 150.0), (r"APTS?\s+5-50", 20.0), (r"APT 2-4", 3.0),
                (r"DORM|HOTEL|NURS", 0.0), (r"RES\.? ?CONDO", 8.0), (r"CONV|CON\.APT", 2.5), (r"STR/OFF\+APT|W-OFF/STR|B/OFF-STR", 2.0),
                (r"^(?:ROW|SEMI|S/D|DET|TWIN)", 1.0)]


def home_weight(desc: pd.Series) -> pd.Series:
    w = pd.Series(np.nan, index=desc.index)
    s = desc.fillna("").str.upper()
    for pat, v in HOME_WEIGHTS:
        w = w.where(w.notna() | ~s.str.contains(pat, regex=True), v)
    return w.fillna(0.0)


def phl_lots() -> pd.DataFrame:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / "phl_lots.parquet"
    if f.exists():
        return pd.read_parquet(f)
    P = X.read_vector(PHL_DIR / "parcels.geojson", dst=CRS)
    P = P[X.nonempty(list(P.geometry))].reset_index(drop=True)
    px, py = X.interior_points(list(P.geometry))
    L = pd.DataFrame({"pid": P.parcelid.values, "use": P.bldg_desc.astype(str).values, "acres": X.areas(list(P.geometry)) / 4046.86,
                      "x": px, "y": py})
    # 2010 census block homes, spread over the block's lots by building-type weight
    b = X.read_vector(RAW / "tod_census_cases" / "tabblock2010_42_pophu.zip", dst=CRS)
    b = b[b.COUNTYFP10 == "101"].reset_index(drop=True)
    k = X.first_within(L.x.values, L.y.values, list(b.geometry))
    L["block"] = pd.Series(np.where(k >= 0, b.BLOCKID10.values[np.maximum(k, 0)], None), dtype=object).where(k >= 0).values
    w = home_weight(L.use)
    L["w"] = w
    blk = b.set_index("BLOCKID10").HOUSING10.astype(float)
    sw = L.groupby("block").w.transform("sum")
    n = L.groupby("block").w.transform("size")
    h = L.block.map(blk).fillna(0)
    L["homes_census2010"] = np.where(sw > 0, h * L.w / sw.where(sw > 0, 1), h / n)
    unplaced = blk.sum() - L.homes_census2010.sum()
    print(f"Philadelphia: 2010 block homes {blk.sum():.0f}, spread over lots {L.homes_census2010.sum():.0f} "
          f"(blocks with no lot point: {unplaced:.0f})", flush=True)
    # OPA values, summed over OPA points inside each parcel (condo units to their building)
    o = pd.read_csv(RAW / "tod_land_values" / "philadelphia_opa_points.csv", dtype={"parcel_number": str}).dropna(subset=["lat", "lon"])
    ox, oy = X.transform(o.lon.values.astype(float), o.lat.values.astype(float), 4326, CRS)
    k = X.first_within(ox, oy, list(P.geometry))
    pmap = pd.Series(k[k >= 0], index=o.parcel_number.values[k >= 0])
    pmap = pmap[~pmap.index.duplicated()]
    a = pd.read_csv(RAW / "tod_land_values" / "philadelphia_assessments.csv", dtype={"parcel_number": str},
                    usecols=["parcel_number", "year", "taxable_land", "taxable_building", "exempt_land", "exempt_building"])
    a = a[a.parcel_number.isin(pmap.index)].copy()
    a["year"] = pd.to_numeric(a.year, errors="coerce")
    a = a.dropna(subset=["year"]).drop_duplicates(["parcel_number", "year"])
    a["row"] = a.parcel_number.map(pmap)
    a["land"] = a.taxable_land + a.exempt_land
    a["bldg"] = a.taxable_building + a.exempt_building
    v = a.groupby(["row", "year"])[["land", "bldg", "taxable_land", "exempt_land"]].sum().reset_index()
    for yr in range(2015, 2025):
        s = v[v.year == yr].set_index("row")
        L[f"land_{yr}"] = s.land.reindex(L.index).values
        L[f"bldg_{yr}"] = s.bldg.reindex(L.index).values
        L[f"exempt_{yr}"] = ((s.exempt_land > 0) & (s.taxable_land <= 0)).reindex(L.index).values
    L.drop(columns=["w"]).to_parquet(f)
    return L.drop(columns=["w"])


# --------------------------------------------------------------------------- permits

@lru_cache(maxsize=2)
def city_permits(city: str) -> pd.DataFrame:
    """Permit points (x, y in EPSG 5070), year, units."""
    import run_tod_station_area as SA
    if city == "nyc":
        return nyc_permits_bbl()
    from missing_middleware.tod.case_philadelphia import WHOLE_BUILDING
    from missing_middleware.tod.case_chicago import dedupe_staged
    d = pd.read_csv(PHL_DIR / "permits_new_construction.csv", dtype=str).drop_duplicates("permitnumber")
    d = d[d.typeofwork.isin(WHOLE_BUILDING)].copy()
    # hotels, dormitories/beds, rooming houses, nursing homes and ADUs are not homes here (owner contract addition)
    d = d[~d.approvedscopeofwork.fillna("").str.upper().str.contains(NOT_HOMES_PHL, regex=True)]
    d["units"] = pd.to_numeric(d.numberofunits, errors="coerce").fillna(0)
    d["year"] = pd.to_numeric(d.permitissuedate.str[:4], errors="coerce")
    d = d[(d.units > 0) & d.year.notna()].dropna(subset=["lat", "lon"])
    gx, gy = X.transform(d.lon.astype(float).values, d.lat.astype(float).values, 4326, CRS)
    d["x"], d["y"], d["issue_date"] = gx, gy, d.permitissuedate
    d = dedupe_staged(d)
    return d[["year", "units", "x", "y"]].reset_index(drop=True)


def permits_raw_phl() -> pd.DataFrame:
    """Philadelphia permits exactly as run_tod_station_area.permits() returns them (for the check)."""
    import run_tod_station_area as SA
    p = SA.permits("Philadelphia")
    return pd.DataFrame({"year": p.year.values, "units": p.units.values})


def snap_permits(city: str, lx: np.ndarray, ly: np.ndarray, keys: np.ndarray | None = None, v: str | None = None) -> pd.DataFrame:
    """Each permit -> a lot (row number in lx/ly); lot = -1 if none. New York: by the job's lot number (in 18v1, or via
    the older vintage's lot into its 18v1 lot) and else nearest lot within 60 m; Philadelphia: nearest lot within 60 m."""
    p = city_permits(city).copy()
    d, i = cKDTree(np.c_[lx, ly]).query(np.c_[p.x, p.y], distance_upper_bound=SNAP_PERMIT)
    p["lot"] = np.where(np.isfinite(d), i, -1)
    p["placed"] = np.where(p.lot >= 0, "nearest lot within 60 m", "none")
    if keys is not None:
        pos = pd.Series(np.arange(len(keys)), index=keys)
        pos = pos[~pos.index.duplicated()]
        k = p.bbl.map(pos)
        if v is not None:
            k = k.fillna(p.bbl.map(to18(v)).map(pos))
        p.loc[k.notna(), "placed"] = np.where(p.moved[k.notna()], "lot number (moved to building lot)", "lot number")
        p["lot"] = np.where(k.notna(), k.fillna(-1), p.lot).astype(int)
    return p


# --------------------------------------------------------------------------- build

def _treated_rows(unit: str, lx, ly) -> np.ndarray:
    """Lots matched to the lot model's treated points of one rezoning (nearest lot within 30 m of each point)."""
    t = _treated()
    t = t[t.unit == unit]
    if t.empty:
        return np.array([], dtype=int)
    d, i = cKDTree(np.c_[lx, ly]).query(np.c_[t.x5070, t.y5070], distance_upper_bound=SNAP_TREATED)
    return np.unique(i[np.isfinite(d)])


@lru_cache(maxsize=2)
def _zone_layer(city: str) -> pd.DataFrame:
    return X.read_vector(NYC_DIR / "nyzma.geojson" if city == "nyc" else PHL_DIR / "remapping.geojson", dst=CRS)


def _polygon(city: str, unit: str):
    """The rezoning's polygons (features whose union is the rezoned area), or None."""
    z = _zone_layer(city)
    if city == "nyc":
        z = z[("nyc_" + z.ULURPNO.astype(str).str.lower()) == unit]
    else:
        z = z[("phl_" + z.Bill_Number_TXT.astype(str)) == unit]
        z = z[z.ReMap_Status.astype(str).str.startswith("Enacted")]
    return [f for f in z.geometry if f] if len(z) else None


def _other_zma_nyc(case: str, y0: int, y1: int):
    """Adopted NYC zoning map amendments effective in the span that are not lot-model cases (flag only)."""
    z = _zone_layer("nyc").copy()
    z["eff"] = pd.to_datetime(z.EFFECTIVE, unit="ms", errors="coerce").dt.year
    z = z[(z.STATUS == "Adopted") & z.eff.between(y0, y1) & ~("nyc_" + z.ULURPNO.astype(str).str.lower()).isin(CASES)]
    return [f for f in z.geometry if f] if len(z) else None


def build(case: str):
    c = CASES[case]
    city = case.split("_")[0]
    b0, b1 = c["before"]
    a0, a1 = c["after"]
    S0 = stops(city)

    # lots for this case
    if city == "nyc":
        v = _vintage_for(c["eff"])
        L = nyc_lots(v, b0)
        keys = L.k.values
        L["source"] = f"DOB new-building permits (both sides); lots MapPLUTO 18v1; existing homes MapPLUTO {v} UnitsRes; values {L.values_from.iloc[0]}"
        L = L.drop(columns=["k", "values_from"])
    else:
        P = phl_lots()
        vy = min(max(c["eff"] - 1, 2015), 2024)
        L = pd.DataFrame({"acres": P.acres, "land_value": P[f"land_{vy}"], "bldg_value": P[f"bldg_{vy}"], "year_built": np.nan,
                          "use": P.use, "public": P[f"exempt_{vy}"].fillna(False).astype(bool), "homes_existing": P.homes_census2010,
                          "x": P.x, "y": P.y, "source": f"L&I new-construction permits (both sides); existing homes 2010 census blocks spread over lots; values OPA {vy}"})
        keys, v = None, None
    lx, ly = L.x.values, L.y.values

    # reform area = treated lots of this rezoning; reform and comparison stops
    tr = _treated_rows(case, lx, ly)
    sxy = np.c_[S0.x, S0.y]
    near_t = np.zeros(len(S0), bool)
    if len(tr):
        d, _ = cKDTree(np.c_[lx[tr], ly[tr]]).query(sxy)
        near_t = d <= HALF
    others = [u for u, o in CASES.items() if u != case and u.startswith(city + "_") and b0 <= o["eff"] <= a1]
    t = _treated()
    t = t[t.unit.isin(others)]
    near_o = np.zeros(len(S0), bool)
    if len(t):
        d, _ = cKDTree(np.c_[t.x5070, t.y5070]).query(sxy)
        near_o = d <= HALF
    types = set(S0.stop_type_text[near_t]) or set(S0.stop_type_text)
    grp = np.where(near_t, "reform", np.where(~near_o & S0.stop_type_text.isin(types), "comparison", "other"))
    S = S0.assign(group=grp)
    S = S[S.group != "other"].reset_index(drop=True)
    S = S[["stop_id", "stop_name", "stop_type_text", "group", "place", "x", "y"]]

    # nearest kept stop within 1 mile
    d, i = cKDTree(np.c_[S.x, S.y]).query(np.c_[lx, ly], distance_upper_bound=MILE)
    keep = np.isfinite(d)
    rows = np.flatnonzero(keep)
    D = L.iloc[rows].copy()
    D["stop_id"] = S.stop_id.values[i[keep]]
    D["group"] = S.group.values[i[keep]]
    D["dist_m"] = d[keep]
    D["band"] = pd.cut(D.dist_m, [-1, QUARTER, HALF, MILE], labels=["0-1/4", "1/4-1/2", "1/2-1"]).astype(str)
    D["in_reform_area"] = np.isin(rows, tr)

    # permits on both sides
    p = snap_permits(city, lx, ly, keys, v)
    w = p[p.year.between(b0, a1)]
    print(f"{case}: permit homes {b0}-{a1} placed: " + ", ".join(f"{k} {u:.0f}" for k, u in w.groupby("placed").units.sum().items()), flush=True)
    p = p[p.lot >= 0]
    # events: every placed record from 2000 on whose lot is in D
    pos = pd.Series(np.arange(len(rows)), index=rows)
    e = p[(p.year >= 2000) & p.lot.isin(rows)]
    ev = pd.DataFrame({"lot_index": e.lot.map(pos).astype(int).values, "homes": e.units.values.astype(float),
                       "permit_year": e.year.values.astype(float)})
    if city == "nyc":
        # completion: 18v1 year built of the lot, kept only when it is no earlier than the permit year minus 1 (the
        # building on the lot in 2018 can be this job's); NaN for later permits not yet built in 18v1
        yb = L.year_built.values[e.lot.values]
        ev["completed_year"] = np.where(yb >= e.year.values - 1, yb, np.nan)
        ev["source"] = "NYC DOB new-building job (fully permitted); completion MapPLUTO 18v1 YearBuilt"
    else:
        ev["completed_year"] = np.nan
        ev["source"] = "Philadelphia L&I new-construction permit (issued)"
    ev["preferred"] = "permit"
    EVENTS[case] = ev
    for lab, (y0, y1) in {"homes_before_win": (b0, b1), "homes_after_win": (a0, a1)}.items():
        w = p[p.year.between(y0, y1)]
        D[lab] = w.groupby("lot").units.sum().reindex(rows).fillna(0).values

    D["case"] = case
    D["city_name"] = CITY[city]
    G = D
    poly = _polygon(city, case)
    G["in_rezoning_polygon"] = GM.points_in_any(G.x.values, G.y.values, poly, union=True) if poly is not None else False
    if city == "nyc":
        oz = _other_zma_nyc(case, b0, a1)
        if oz is not None:
            sz = pd.Series(X.distance_within(S.x.values, S.y.values, oz, HALF + 1.0) <= HALF, index=S.stop_id.values)
            G["stop_near_other_zma"] = G.stop_id.map(sz).fillna(False).astype(bool)
        else:
            G["stop_near_other_zma"] = False
    G["implausible"] = False
    G["_yb"] = [()] * len(G)
    G["_un"] = [()] * len(G)
    cols = ["case", "city_name", "group", "stop_id", "dist_m", "band", "in_reform_area", "in_rezoning_polygon", "acres",
            "land_value", "bldg_value", "year_built", "use", "public", "homes_existing", "homes_before_win", "homes_after_win",
            "source", "implausible"] + [x for x in ("homes_18v1", "stop_near_other_zma") if x in G] + ["_yb", "_un", "x", "y"]
    G = G[cols].reset_index(drop=True)
    G["public"] = G.public.astype(bool)
    return G, S
