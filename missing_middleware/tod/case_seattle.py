"""Seattle light-rail station-area rezones: North Beacon Hill and Othello (2012) and Mount Baker / North Rainier
(2014). Case adapter (docs/tod/CASE_ANALYSIS_PLAN.md, section 7 entry "more cities for the trait test").

Inputs (data/raw/tod_cases/seattle/, fetched by fetch() below):
- permits_new_units.csv: SDCI Building Permits (data.seattle.gov 76t5-zqzr), building permits that add housing units,
  with permit number, type, issue date, units added and removed, zoning at permit and point. Contractor, address
  and other personal fields are not requested.
- zoning_current.geojson: the City's current zoning (Current_Land_Use_Zoning_Detail_2), whose ZONINGHISTORY field lists
  every zone, ordinance and effective date of each zoning polygon. Zoning at any date is read from it.
- parcels_2010.geojson: the City's Zoned Development Capacity parcels of 2010 (King County parcels, roll year 2011):
  zoning, maximum FAR and density, present use, existing units. Owner and taxpayer fields are not requested.
- parcels_2016.geojson: the same model for 2016 (zoning, maximum residential FAR), for the dose after.
- station_area_overlay.geojson: Station Area Overlay districts.
- rail_stops.geojson: Link light-rail stops (BTS National Transit Map, Sound Transit, NTD 00040).

Rules (the one area rule, cases.uniform_areas):
- Reform land: zoning polygons whose history has an entry from one of the case's rezone ordinances (REFORM_ORDS),
  within 1/2 mile of the case's stations.
- Level: maximum residential FAR from the City's capacity model (2010 before, 2016 after). Single-family zones are
  density-limited (one home per lot) and have FAR 0 in the model; a lot whose level rose counts as treated.
- Lots rezoned outside the reform during the window are in no area. Two citywide code changes are not counted as
  local rezonings, because they changed zone names or rules for every lot of a kind in both areas: the 2011 Lowrise
  code (Ordinance 123495, L-x to LRx) and Mandatory Housing Affordability (Ordinance 125791, April 2019; "(M)" zones).
- Outcome: housing units added by new-building permits (permit type "New"), one record per permit number, by issue
  year. Project = the parcel the permit falls on.
- Dose: added maximum residential FAR (City capacity model), acre-weighted over treated lots where both values are
  FAR-based; the share of treated acres covered is reported.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.paths import RAW
from missing_middleware.tod import cases as C

DIR = RAW / "tod_cases" / "seattle"
CRS_M = 32610  # WGS 84 / UTM 10N
FIRST_YEAR, LAST_FULL_YEAR = 2006, 2025
SEA = "https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services"
SEA_LICENCE = "City of Seattle open data: Public Domain"
PERMITS_URL = "https://data.seattle.gov/resource/76t5-zqzr.csv"
PERMIT_FIELDS = ("permitnum,permitclass,permitclassmapped,permittypemapped,permittypedesc,housingunits,housingunitsadded,"
                 "housingunitsremoved,issueddate,statuscurrent,zoning,latitude,longitude,parentpermitnum,dwellingunittype,"
                 "housingcategory")
CITYWIDE_ORDS = {"123495", "125791"}  # 2011 Lowrise code; 2019 Mandatory Housing Affordability

CASES = {
    "seattle_nbh_othello_2012": {"stations": ("Beacon Hill", "Othello"), "year": 2012, "effective": "2012-05-10"},
    "seattle_mount_baker_2014": {"stations": ("Mount Baker",), "year": 2014, "effective": "2014-08-02"},
}
UNIT_NAMES = {"Beacon Hill": "North Beacon Hill", "Othello": "Othello", "Mount Baker": "Mount Baker"}


# --------------------------------------------------------------------------- fetch

def fetch(refresh: bool = False) -> None:
    import urllib.parse
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    import fetch_tod_cases as F
    import geopandas as gpd
    man = F.Manifest(DIR, "tod_cases_seattle", "City of Seattle (SDCI permits, zoning, development capacity parcels)")
    name = "permits_new_units.csv"
    if not man.have(name, refresh):
        params = {"$select": PERMIT_FIELDS, "$where": "permittypemapped='Building' AND housingunitsadded>0",
                  "$limit": 200000, "$order": "permitnum"}
        url = PERMITS_URL + "?" + urllib.parse.urlencode(params)
        man.record(name, F.http_get(url, timeout=900), url, licence=SEA_LICENCE,
                   note="SDCI Building Permits (76t5-zqzr), building permits adding housing units; contractor and address fields not requested")
    F.save_layer(man, "zoning_current.geojson", f"{SEA}/Current_Land_Use_Zoning_Detail_2/FeatureServer/0", refresh, SEA_LICENCE,
                 out_fields="ZONING,ORDINANCE,EFFECTIVE,ZONING_PREV,ORDINANCE_PREV,EFFECTIVE_PREV,ZONINGHISTORY,LIGHTRAIL,BASE_ZONE,CATEGORY_DESC",
                 page=2000)
    F.save_layer(man, "station_area_overlay.geojson", f"{SEA}/Station_Area_Overlay_(light_rail)/FeatureServer/23", refresh,
                 SEA_LICENCE, out_fields="OVERLAY,DESCRIPTION", page=100)
    F.ntm_rail_stops(man, "rail_stops.geojson", ["00040"], refresh)
    st = gpd.read_file(DIR / "rail_stops.geojson")
    st = st[st["stop_lat"].between(47.48, 47.74) & st["stop_lon"].between(-122.44, -122.24)]
    aoi = F.aoi_from([(st.geometry, 1300.0)])
    F.save_tiled_layer(man, "parcels_2010.geojson", f"{SEA}/Zoned_Development_Capacity_2010/FeatureServer/0", aoi, refresh,
                       SEA_LICENCE, out_fields="PIN,ZONING,ZONELUT,MAXRDENS,MAXFAR,NR_UNITS,LAND_USE_DESC,PRES_USE,PUB_OWN_TYPE,"
                       "USE_CATEGORY,LU_GEN_DESC,VILLAGE_NAME,CLASS,LAND_SQFT,JURIS_NAME", id_field="PIN")
    F.save_tiled_layer(man, "parcels_2016.geojson", f"{SEA}/Zoned_Development_Capacity_Layers_2016/FeatureServer/2", aoi,
                       refresh, SEA_LICENCE, out_fields="PIN,ZONING,ZONELUT,RES_MAX_FAR,MAX_FAR,COMM_MAX_FAR,MAXRDENS,EXIST_UNITS",
                       id_field="PIN")


# --------------------------------------------------------------------------- zoning history

_HIST = re.compile(r"^\s*(?P<zone>[^,]+?)\s*(?:,\s*ORD\s*(?P<ord>\d+)\s*,\s*(?P<date>\d{1,2}/\d{1,2}/\d{4}))?\s*$")


def parse_history(h: str) -> list[tuple[str, str | None, pd.Timestamp | None]]:
    """'LR2 (M),ORD125791,04/19/2019; LR2,ORD123495,04/19/2011; L-2' -> newest first [(zone, ordinance, date), ...];
    the last entry (no ordinance) is the zoning before the oldest recorded change."""
    out = []
    for part in str(h or "").split(";"):
        m = _HIST.match(part)
        if not m or not m.group("zone").strip():
            continue
        d = pd.to_datetime(m.group("date"), format="%m/%d/%Y", errors="coerce") if m.group("date") else None
        out.append((m.group("zone").strip(), m.group("ord"), d))
    return out


def zone_at(hist: list, t: pd.Timestamp) -> str | None:
    """Zone in force on date t: the newest entry dated on or before t; before every dated change, the oldest zone."""
    for zone, _, d in hist:
        if d is not None and d <= t:
            return zone
    return hist[-1][0] if hist else None


def changes_between(hist: list, lo: pd.Timestamp, hi: pd.Timestamp, skip: set) -> list[str]:
    """Ordinances (other than skip) that changed the zone between lo and hi, inclusive."""
    return [o for z, o, d in hist if d is not None and lo <= d <= hi and o and o not in skip]


def base_zone(z) -> str:
    """'NC2-40 (M)' -> 'NC2-40'; 'LR3 RC' -> 'LR3'."""
    if z is None or (isinstance(z, float) and np.isnan(z)):
        return ""
    s = re.sub(r"\(.*?\)", "", str(z)).strip().upper()
    return s.split()[0] if s else ""


# --------------------------------------------------------------------------- build

_cache: dict = {}


def _load():
    import geopandas as gpd
    if _cache:
        return _cache
    p10 = gpd.read_file(DIR / "parcels_2010.geojson").to_crs(CRS_M)
    p10 = p10[p10.geometry.notna() & ~p10.geometry.is_empty].drop_duplicates("PIN").reset_index(drop=True)
    p10 = p10[p10["JURIS_NAME"].astype(str).str.upper().eq("SEATTLE")].reset_index(drop=True)
    p10["geometry"] = p10.geometry.make_valid()
    p10["acres"] = p10.geometry.area / C.SQM_PER_ACRE
    pts = p10.geometry.representative_point()
    zc = gpd.read_file(DIR / "zoning_current.geojson").to_crs(CRS_M)
    zc["geometry"] = zc.geometry.make_valid()
    j = gpd.sjoin(gpd.GeoDataFrame(geometry=pts, crs=CRS_M), zc[["ZONINGHISTORY", "ZONING", "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated()].reindex(pts.index)
    p10["hist"] = j["ZONINGHISTORY"].map(parse_history)
    p16 = gpd.read_file(DIR / "parcels_2016.geojson")[["PIN", "RES_MAX_FAR", "ZONING"]].rename(columns={"ZONING": "ZONING_16"})
    p10 = p10.merge(p16.drop_duplicates("PIN"), on="PIN", how="left")
    p10.index = range(len(p10))
    p10 = gpd.GeoDataFrame(p10, geometry="geometry", crs=CRS_M)
    st = gpd.read_file(DIR / "rail_stops.geojson").to_crs(CRS_M)
    st = st[st.geometry.within(p10.geometry.union_all().convex_hull.buffer(500))].reset_index(drop=True)
    from missing_middleware.tod import traits as T
    stations = T.cluster_stations(st, st["stop_name"].reset_index(drop=True))
    perm = pd.read_csv(DIR / "permits_new_units.csv", dtype=str)
    perm = perm[perm["permittypedesc"].astype(str).str.strip().eq("New")].drop_duplicates("permitnum")
    perm["units"] = pd.to_numeric(perm["housingunitsadded"], errors="coerce").fillna(0)
    perm["year"] = pd.to_datetime(perm["issueddate"], errors="coerce").dt.year
    perm = perm[(perm["units"] > 0) & perm["year"].notna()].dropna(subset=["latitude", "longitude"])
    pg = gpd.GeoDataFrame(perm, geometry=gpd.points_from_xy(perm["longitude"].astype(float), perm["latitude"].astype(float)),
                          crs=4326).to_crs(CRS_M)
    pg["pix"] = C.locate_points(pg, p10)
    pg["project"] = pg["pix"].astype("Int64").astype(str)
    _cache.update(parcels=p10, stations=stations, permits=pg)
    return _cache


def reform_ordinances(case: str) -> tuple[set, pd.DataFrame]:
    """Ordinances of the case's rezone: those dated in the case year whose zoning polygons lie within 1/2 mile of the
    case's stations (counted by acres). Returned with a table of what was found."""
    d = _load()
    spec = CASES[case]
    p, st = d["parcels"], d["stations"]
    mine = st[st["station"].isin(spec["stations"])]
    near = p.geometry.representative_point().within(mine.buffer(C.HALF_MILE_M).union_all())
    rows = []
    for ix in p.index[near]:
        for z, o, dt in p.at[ix, "hist"] or []:
            if dt is not None and dt.year == spec["year"] and o and o not in CITYWIDE_ORDS:
                rows.append({"ordinance": o, "date": dt.date(), "acres": p.at[ix, "acres"]})
    t = pd.DataFrame(rows, columns=["ordinance", "date", "acres"])
    if t.empty:
        return set(), t
    g = t.groupby(["ordinance", "date"])["acres"].sum().reset_index().sort_values("acres", ascending=False)
    keep = set(g.loc[g["acres"] >= 1.0, "ordinance"])
    return keep, g


def _frame(case: str) -> dict:
    d = _load()
    spec = CASES[case]
    p = d["parcels"].copy()
    st = d["stations"]
    ords, found = reform_ordinances(case)
    eff = pd.Timestamp(spec["effective"])
    eyear = spec["year"]
    per = C.period_years(eyear, FIRST_YEAR, LAST_FULL_YEAR)
    lo, hi = pd.Timestamp(f"{per['before'][0]}-01-01"), pd.Timestamp(f"{per['after'][-1]}-12-31")
    mine = st[st["station"].isin(spec["stations"])]
    pts = p.geometry.representative_point()
    near_mine = pts.within(mine.buffer(C.HALF_MILE_M).union_all())
    rdate = {}
    for ix in p.index:
        for z, o, dt in p.at[ix, "hist"] or []:
            if o in ords and dt is not None:
                rdate[ix] = dt
    in_reform = pd.Series(p.index.isin(list(rdate)), index=p.index) & near_mine
    # zones before (on the day before the earliest reform date) and after (end of the reform year)
    first = min(rdate.values()) if rdate else eff
    p["zone_before"] = [zone_at(h or [], first - pd.Timedelta(days=1)) for h in p["hist"]]
    p["zone_after"] = [zone_at(h or [], pd.Timestamp(f"{eyear}-12-31")) for h in p["hist"]]
    far10 = pd.to_numeric(p["MAXFAR"], errors="coerce")
    far16 = pd.to_numeric(p["RES_MAX_FAR"], errors="coerce")
    p["old_level"] = far10.fillna(0.0)
    p["new_level"] = np.where(in_reform, far16, far10).astype(float)
    p["new_level"] = p["new_level"].fillna(p["old_level"])
    rose = in_reform & ((p["new_level"] > p["old_level"] + 1e-9) |
                        (p["zone_before"].map(base_zone) != p["zone_after"].map(base_zone)) &
                        p["zone_before"].astype(str).str.upper().str.startswith("SF"))
    changed = pd.Series([bool(changes_between(h or [], lo, hi, ords | CITYWIDE_ORDS)) for h in p["hist"]], index=p.index) & ~in_reform
    use = (p["LAND_USE_DESC"].astype(str) + " " + p["PRES_USE"].astype(str)).str.upper()
    zb = p["zone_before"].astype(str).str.upper()
    eligible = ~zb.str.match(r"^(IG|IB|IC|MIO|PARK|SF? ?PARK)") & ~use.str.contains(
        r"PARK|CEMETER|SCHOOL|CHURCH|RELIG|UTILIT|GOVERN|RIGHT.OF.WAY|WATER|HOSPITAL|COLLEGE|UNIVERS")
    uncapped = ~zb.str.startswith("SF")  # single-family zones: one home per lot (a density cap)
    p["area"], rule = C.uniform_areas(p, in_reform, rose, p["old_level"], p["new_level"], uncapped, changed, eligible,
                                      stations=st.geometry)
    p["eligible"] = eligible
    from missing_middleware.tod import traits as T
    lab = pd.Series(np.nan, index=p.index, dtype=object)
    tr = p.index[p["area"] == C.TREAT]
    if len(tr):
        lab.loc[tr] = T.nearest_station(p.loc[tr].geometry.representative_point(), mine).map(lambda s: UNIT_NAMES.get(s, s)).values
    p["unit_label"] = lab
    p["vpi"] = use.str.contains(r"VACANT|PARKING|INDUSTR|WAREHOUSE")
    p["homes_before"] = pd.to_numeric(p["NR_UNITS"], errors="coerce").fillna(0)
    pg = d["permits"]
    q = pg[pg["year"].between(per["before"][0], per["after"][-1])].copy()
    q["area"] = p["area"].reindex(q["pix"]).values
    q["el"] = eligible.reindex(q["pix"]).fillna(False).astype(bool).values
    permits = q[q["area"].notna() & q["el"]][["project", "area", "year", "units", "pix"]].copy()
    permits["year"] = permits["year"].astype(int)
    orig = C.assign_areas(p, in_reform, stations=None)
    q2 = q.assign(area=orig.reindex(q["pix"]).values)
    orig_p = q2[q2["area"].notna() & q2["el"]][["project", "area", "year", "units"]].astype({"year": int})
    orig_a = p[orig.notna() & eligible].groupby(orig)["acres"].sum().to_dict()
    return {"parcels": p, "permits": permits, "effective_year": eyear, "per": per, "dose_unit": "added FAR",
            "ordinances": sorted(ords), "found": found, "rule": rule, "original": (orig_p, orig_a), "in_reform": in_reform}


def unit_frame(case: str) -> dict:
    """For the trait test: parcels (metre CRS) with area, eligible, unit_label (station area), old_level, new_level,
    vpi, homes_before; permits with project, area, year, units, pix; effective_year; per; dose_unit."""
    f = _frame(case)
    cols = ["area", "eligible", "unit_label", "old_level", "new_level", "vpi", "homes_before", "acres", "geometry"]
    return {"parcels": f["parcels"][cols], "permits": f["permits"], "effective_year": f["effective_year"], "per": f["per"],
            "dose_unit": f["dose_unit"]}


def build(case: str) -> tuple[C.CaseInputs, dict]:
    f = _frame(case)
    p = f["parcels"]
    el = p[p["area"].notna() & p["eligible"].astype(bool)]
    acres = el.groupby("area")["acres"].sum().to_dict()
    homes = el.groupby("area")["homes_before"].sum().astype(float).to_dict()
    tr = el[el["area"] == C.TREAT]
    zb = tr["zone_before"].astype(str).str.upper()
    far_based = ~zb.str.startswith("SF") & (tr["old_level"] > 0)
    dose_table = pd.DataFrame({"acres": tr.loc[far_based, "acres"], "old_far": tr.loc[far_based, "old_level"],
                               "new_far": tr.loc[far_based, "new_level"]})
    cover = float(tr.loc[far_based, "acres"].sum() / tr["acres"].sum()) if len(tr) else np.nan
    per = f["per"]
    diag = {"rule": f["rule"], "reform_ordinances": f["ordinances"],
            "ordinance_acres_near_stations": f["found"].assign(date=f["found"]["date"].astype(str)).to_dict(orient="records") if len(f["found"]) else [],
            "acres": {k: round(v, 1) for k, v in acres.items()},
            "treatment_zoning_before": tr["zone_before"].value_counts().head(10).to_dict(),
            "treatment_zoning_after": tr["zone_after"].value_counts().head(10).to_dict(),
            "treated_acres_with_far_dose_share": None if np.isnan(cover) else round(cover, 3),
            "units_by_station_area": tr.groupby("unit_label")["acres"].sum().round(1).to_dict(),
            "permits_located_share": round(float(_load()["permits"]["pix"].notna().mean()), 4)}
    ci = C.CaseInputs(case=case, role="fit", effective_year=f["effective_year"], first_year=FIRST_YEAR,
                      last_full_year=LAST_FULL_YEAR, permits=f["permits"][["project", "area", "year", "units"]], acres=acres,
                      homes=homes, dose_table=dose_table, parking_change="reduced near stations (Station Area Overlay; source_lead)",
                      mandate="no (incentive zoning, voluntary)", original_spec=f["original"],
                      notes=f"dose = City capacity-model residential FAR on {0 if np.isnan(cover) else round(100 * cover)}% of treated acres; "
                            "single-family land has no FAR")
    return ci, diag
