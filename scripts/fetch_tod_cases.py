"""Download the inputs for the TOD comparison cases (docs/tod/CASE_ANALYSIS_PLAN.md) into data/raw/tod_cases/.

    uv run python scripts/fetch_tod_cases.py [--city census bps charlotte nyc stpaul chicago] [--refresh]

Raw (git-ignored): data/raw/tod_cases/<city>/...  and  data/raw/tod_cases/<city>/manifest.json
(URL, access time, bytes, SHA-256, licence, feature counts). Existing files are kept unless --refresh.

Every file comes from the publishing government's own service (or the Census Bureau):
- Charlotte: Mecklenburg County building permits (the City of Charlotte's ArcGIS Hub copy, item
  645eba06f0af44e5ac5d40ffc69d81e6, because the county server refuses scripted queries); City of Charlotte
  Rezoning History, Pre-UDO Zoning and All Parcel Data layers (land use only; owner fields are not requested);
  CATS rail stops from the BTS National Transit Map.
- Saint Paul: Housing Production layer, Principal Zoning snapshots (Nov 2010, 2011, 2012 and 2017), city tax parcels,
  Metro Transit light-rail stops.
- New York: DOB job application filings (Brooklyn new buildings), DCP zoning map amendments and list of
  city-initiated rezonings, MapPLUTO 02b, 04c and 09v2 (Brooklyn lots before, after and at the end of the window),
  subway stations.
- Census Building Permits Survey county files 1996-2014 (checks of the permit files' yearly totals).
- Philadelphia: L&I new-construction permits (Carto), remapping bills with enactment dates, base-district snapshots
  2015-2025, pre-2012 zoning, overlays, district dimensional table, PWD parcels, SEPTA stops.
- Raleigh: new residential building permits, rezoning cases, TOD overlay (to show why the case is context only).
- Phoenix and Ann Arbor: no file is fetched; no permit source with unit counts was found (CASE_RESULTS.md).
- Chicago (held out): building permits (new construction), zoning as of November 2012 and today, CTA and Metra stops,
  Cook County 2021 parcels in Chicago.
- Census 2010 blocks with housing-unit counts (TIGER2010BLKPOPHU) for the states above.

Standard library plus geopandas/shapely (for the area-of-interest tiling of parcel downloads).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW  # noqa: E402

D = RAW / "tod_cases"
UA = {"User-Agent": "missing-middleware research (housing policy model; TOD comparison cases)"}
NTM_STOPS = "https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_National_Transit_Map_Stops/FeatureServer/0"
NTM_LICENCE = "CC BY 3.0 US (BTS National Transit Map stops layer)"
CENSUS_LICENCE = "Public domain (U.S. government work)"


# --------------------------------------------------------------------------- helpers

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def http_get(url: str, params: dict | None = None, timeout: int = 300, retries: int = 3, data: bytes | None = None) -> bytes:
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA, data=data)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))
    raise AssertionError("unreachable")


class Manifest:
    def __init__(self, folder: Path, source_id: str, publisher: str):
        self.folder = folder
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / "manifest.json"
        self.m = json.loads(self.path.read_text()) if self.path.exists() else {}
        self.m.update({"source_id": source_id, "publisher": publisher})
        self.m.setdefault("files", {})

    def record(self, name: str, data: bytes, url: str, **extra) -> None:
        (self.folder / name).parent.mkdir(parents=True, exist_ok=True)
        (self.folder / name).write_bytes(data)
        rec = {"url": url, "accessed_utc": now(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        rec.update(extra)
        self.m["files"][name] = rec
        self.save()
        print(f"  {self.folder.name}/{name}: {len(data):,} bytes")

    def have(self, name: str, refresh: bool) -> bool:
        return (not refresh) and (self.folder / name).exists() and name in self.m["files"]

    def save(self) -> None:
        self.path.write_text(json.dumps(self.m, indent=1) + "\n")


def download_file(man: Manifest, name: str, url: str, refresh: bool, licence: str, timeout: int = 1800, **extra) -> None:
    if man.have(name, refresh):
        print(f"  {name}: kept")
        return
    data = http_get(url, timeout=timeout)
    man.record(name, data, url, licence=licence, **extra)


def arcgis_query(layer_url: str, where: str = "1=1", out_fields: str = "*", geometry: str | None = None,
                 page: int = 2000, geojson: bool = True, out_sr: int = 4326, order_by: str | None = None) -> tuple[list, str]:
    """All features of an ArcGIS layer matching `where` (and an optional envelope), paged. Returns (features, first URL)."""
    feats, off, first = [], 0, None
    while True:
        p = dict(where=where, outFields=out_fields, returnGeometry="true", outSR=out_sr,
                 f="geojson" if geojson else "json", resultOffset=off, resultRecordCount=page)
        if order_by:
            p["orderByFields"] = order_by
        if geometry:
            p.update(geometry=geometry, geometryType="esriGeometryEnvelope", inSR=4326, spatialRel="esriSpatialRelIntersects")
        url = f"{layer_url}/query?" + urllib.parse.urlencode(p)
        first = first or url
        d = json.loads(http_get(url, timeout=300))
        if "error" in d:
            raise RuntimeError(f"{layer_url}: {d['error']}")
        f = d.get("features", [])
        feats += f
        more = d.get("exceededTransferLimit") or d.get("properties", {}).get("exceededTransferLimit")
        if not f or (len(f) < page and not more):
            break
        off += len(f)
    return feats, first


def save_layer(man: Manifest, name: str, layer_url: str, refresh: bool, licence: str, **kw) -> None:
    if man.have(name, refresh):
        print(f"  {name}: kept")
        return
    feats, first = arcgis_query(layer_url, **kw)
    data = json.dumps({"type": "FeatureCollection", "features": feats}).encode()
    man.record(name, data, first, licence=licence, features=len(feats), note="first page URL shown; later pages add resultOffset")


def tiles_for(aoi, size_m: float = 1500.0) -> list[str]:
    """Envelopes (WGS84 'xmin,ymin,xmax,ymax') of a square grid covering a projected (metre) AOI geometry."""
    import geopandas as gpd
    from shapely.geometry import box
    xmin, ymin, xmax, ymax = aoi.bounds
    boxes = []
    x = xmin
    while x < xmax:
        y = ymin
        while y < ymax:
            b = box(x, y, x + size_m, y + size_m)
            if b.intersects(aoi):
                boxes.append(b)
            y += size_m
        x += size_m
    g = gpd.GeoSeries(boxes, crs=AOI_CRS).to_crs(4326)
    return [",".join(f"{v:.6f}" for v in b.bounds) for b in g]


AOI_CRS = 5070  # NAD83 Conus Albers (metres), used only for tiling


def save_tiled_layer(man: Manifest, name: str, layer_url: str, aoi, refresh: bool, licence: str, out_fields: str,
                     id_field: str, page: int = 2000, size_m: float = 1500.0) -> None:
    """Features of a large layer within an AOI, fetched tile by tile and de-duplicated on `id_field`."""
    if man.have(name, refresh):
        print(f"  {name}: kept")
        return
    seen, feats, first = set(), [], None
    tiles = tiles_for(aoi, size_m)
    for i, env in enumerate(tiles):
        f, url = arcgis_query(layer_url, out_fields=out_fields, geometry=env, page=page)
        first = first or url
        for ft in f:
            k = ft["properties"].get(id_field)
            if k in seen:
                continue
            seen.add(k)
            feats.append(ft)
        if i % 20 == 0:
            print(f"    tile {i + 1}/{len(tiles)}: {len(feats):,} features")
    data = json.dumps({"type": "FeatureCollection", "features": feats}).encode()
    man.record(name, data, first, licence=licence, features=len(feats), tiles=len(tiles),
               note=f"{len(tiles)} envelope queries of {size_m:.0f} m tiles covering the case area of interest; first URL shown")


def ntm_rail_stops(man: Manifest, name: str, ntd_ids: list[str], refresh: bool) -> None:
    where = "ntd_id IN (" + ",".join(f"'{i}'" for i in ntd_ids) + ") AND stop_type IN ('0','1','2','12')"
    save_layer(man, name, NTM_STOPS, refresh, NTM_LICENCE, where=where, page=2000)


def aoi_from(paths_and_buffers: list[tuple[object, float]]):
    """Union of buffered geometries (GeoSeries in any CRS, buffer in metres) in AOI_CRS."""
    import geopandas as gpd
    parts = []
    for g, buf in paths_and_buffers:
        parts.append(gpd.GeoSeries(g).to_crs(AOI_CRS).buffer(buf).union_all())
    return gpd.GeoSeries(parts, crs=AOI_CRS).union_all()


# --------------------------------------------------------------------------- Census 2010 blocks

CENSUS_STATES = {"37": "North Carolina", "27": "Minnesota", "17": "Illinois", "42": "Pennsylvania"}


def fetch_census(refresh: bool) -> None:
    man = Manifest(D / "census_2010_blocks", "tod_cases_census_2010_blocks", "U.S. Census Bureau, TIGER/Line 2010 blocks with population and housing units")
    for st in CENSUS_STATES:
        name = f"tabblock2010_{st}_pophu.zip"
        download_file(man, name, f"https://www2.census.gov/geo/tiger/TIGER2010BLKPOPHU/{name}", refresh, CENSUS_LICENCE,
                      note="2010 Census block polygons with HOUSING10 (housing units) and POP10")


def fetch_bps(refresh: bool) -> None:
    """Census Building Permits Survey county annual files 1996-2014 (2015 onward are in data/raw/census_bps_county/),
    used only to check the city permit files' yearly totals (Kings County NY, Mecklenburg County NC)."""
    man = Manifest(D / "bps_county", "tod_cases_bps_county", "U.S. Census Bureau, Building Permits Survey (county annual)")
    for y in range(1996, 2015):
        name = f"co{y}a.txt"
        download_file(man, name, f"https://www2.census.gov/econ/bps/County/{name}", refresh, CENSUS_LICENCE)


# --------------------------------------------------------------------------- Charlotte

CLT_HUB_ITEM = "645eba06f0af44e5ac5d40ffc69d81e6"
CLT_PERMITS_CSV = f"https://hub.arcgis.com/api/v3/datasets/{CLT_HUB_ITEM}_0/downloads/data?format=csv&spatialRefId=2264&where=1%3D1"
CLT_GIS = "https://gis.charlottenc.gov/arcgis/rest/services"
CLT_REZONING = f"{CLT_GIS}/PLN/RezoningHistory/MapServer/0"
CLT_PRE_UDO = "https://services.arcgis.com/9Nl857LBlQVyzq54/arcgis/rest/services/Pre_UDO_Zoning/FeatureServer/0"
CLT_PARCELS = f"{CLT_GIS}/PLN/AllParcelData/MapServer/0"
CLT_LICENCE = "Disclaimer only, no named licence (public record, D1)"


def fetch_charlotte(refresh: bool) -> None:
    import geopandas as gpd
    man = Manifest(D / "charlotte", "tod_cases_charlotte", "Mecklenburg County (permits) and City of Charlotte (zoning, parcels)")
    download_file(man, "permits.csv", CLT_PERMITS_CSV, refresh, CLT_LICENCE,
                  note="Mecklenburg County Building Permit Locations as republished on the City of Charlotte ArcGIS Hub "
                       "(item 645eba06f0af44e5ac5d40ffc69d81e6, service BuildingPermits/FeatureServer/0). Raw file contains "
                       "owner names: never copied to committed outputs.")
    save_layer(man, "rezoning_history.geojson", CLT_REZONING, refresh, CLT_LICENCE,
               out_fields="Petition,ExistingZoning,RequestedZoning,Approved,Status,Type", page=1000)
    save_layer(man, "pre_udo_zoning.geojson", CLT_PRE_UDO, refresh, CLT_LICENCE,
               out_fields="ZoneDes,ZoneClass,ZonePetition,RezoneDate,Overlay", page=2000)
    ntm_rail_stops(man, "rail_stops.geojson", ["40008"], refresh)
    save_layer(man, "council_districts.geojson", f"{CLT_GIS}/PLN/CouncilDistricts/MapServer/0", refresh, CLT_LICENCE,
               out_fields="*", page=100)
    rz = gpd.read_file(D / "charlotte" / "rezoning_history.geojson")
    treat = rz[rz["Petition"].astype(str).str.startswith("2019-102")]
    st = gpd.read_file(D / "charlotte" / "rail_stops.geojson")
    aoi = aoi_from([(treat.geometry, 700.0), (st.geometry, 1000.0)])
    save_tiled_layer(man, "parcels.geojson", CLT_PARCELS, aoi, refresh, CLT_LICENCE,
                     out_fields="parcelid,landusecode,landuse_description,txt_vacantorimproved", id_field="parcelid")



# --------------------------------------------------------------------------- New York (Brooklyn)

NYC_SODA = "https://data.cityofnewyork.us/resource/ic3t-wcy2.csv"
NYC_DOB_FIELDS = ("job__,doc__,borough,house__,street_name,block,lot,bin__,job_type,job_status,job_status_descrp,"
                  "pre__filing_date,approved,fully_permitted,existing_dwelling_units,proposed_dwelling_units,building_type,"
                  "zoning_dist1,proposed_no_of_stories,gis_latitude,gis_longitude")
NYC_DCP = "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services"
NYC_BYTES = "https://s-media.nyc.gov/agencies/dcp/assets/files/zip/data-tools/bytes/mappluto"
NYC_LICENCE = "NYC Open Data terms of use (public record)"
NYC_PLUTO = {"mappluto_02b.zip": "MapPLUTO 02b (March 2003)", "mappluto_04c.zip": "MapPLUTO 04c (late 2004)",
             "mappluto_09v2.zip": "MapPLUTO 09v2 (2009)"}
# Yearly archives for the pooled set: each rezoning's zoning before and after, and changes during its window.
for _v in ("03c", "05d", "06c", "07c", "08b", "09v1", "10v1", "10v2", "11v1", "11v2", "12v1", "12v2", "13v1", "13v2",
           "14v1", "14v2", "15v1", "16v1", "17v1", "18v1"):
    NYC_PLUTO[f"mappluto_{_v}.zip"] = f"MapPLUTO {_v} (pooled set)"


def fetch_nyc(refresh: bool) -> None:
    man = Manifest(D / "nyc", "tod_cases_nyc", "NYC Department of Buildings and Department of City Planning")
    name = "dob_nb_all.csv"
    if not man.have(name, refresh):
        params = {"$select": NYC_DOB_FIELDS, "$where": "job_type='NB' AND doc__='01'",
                  "$limit": 500000, "$order": "job__"}
        url = NYC_SODA + "?" + urllib.parse.urlencode(params)
        data = http_get(url, timeout=900)
        man.record(name, data, url, licence=NYC_LICENCE,
                   note="DOB Job Application Filings (ic3t-wcy2), new-building jobs in all boroughs, document 01; owner "
                        "and applicant fields not requested")
    else:
        print(f"  {name}: kept")
    save_layer(man, "nyzma.geojson", f"{NYC_DCP}/nyzma/FeatureServer/0", refresh, NYC_LICENCE, page=1000)
    save_layer(man, "bloomberg_rezonings.geojson", f"{NYC_DCP}/Bloomberg_rezonings/FeatureServer/0", refresh, NYC_LICENCE, page=1000)
    save_layer(man, "subway_stations.geojson", f"{NYC_DCP}/SubwayStations_share/FeatureServer/0", refresh, NYC_LICENCE, page=1000)
    for f, note in NYC_PLUTO.items():
        download_file(man, f, f"{NYC_BYTES}/{f}", refresh, NYC_LICENCE, note=note + "; raw only (contains owner names)")


# --------------------------------------------------------------------------- Saint Paul

STP = "https://services1.arcgis.com/9meaaHE3uiba0zr8/arcgis/rest/services"
STP_LICENCE = "AS IS under the Minnesota Government Data Practices Act (City of Saint Paul open data)"
STP_ZONING_SNAPSHOTS = {31: "zoning_2010_11.geojson", 28: "zoning_2011_11.geojson", 27: "zoning_2012_11.geojson",
                        15: "zoning_2017_11.geojson"}


def fetch_stpaul(refresh: bool) -> None:
    man = Manifest(D / "stpaul", "tod_cases_stpaul", "City of Saint Paul (housing production, zoning snapshots, parcels)")
    save_layer(man, "housing_production.geojson", f"{STP}/Housing_Production_Q3_2024/FeatureServer/73", refresh, STP_LICENCE,
               out_fields="OBJECTID,ParcelID,TypeOfWork,ResidenceType,DwellingUnitType,ProjectPermitIssueDate,"
                          "ProjectPermitIssueYear,ExistingDwellingUnits,NewDwellingUnits,TotalFinalFinalDwellingUnits", page=2000)
    for lid, name in STP_ZONING_SNAPSHOTS.items():
        save_layer(man, name, f"{STP}/PrincipalZoning_OverTime/FeatureServer/{lid}", refresh, STP_LICENCE,
                   out_fields="Zoning,Rezoned,File_No", page=2000)
    save_layer(man, "parcels.geojson", f"{STP}/Saint_Paul_Tax_Parcels/FeatureServer/0", refresh, STP_LICENCE,
               out_fields="ParcelID,LandUseCodeDescription,ParcelAcresPolygon,SiteCityName", page=2000)
    ntm_rail_stops(man, "rail_stops.geojson", ["50027"], refresh)


# --------------------------------------------------------------------------- Chicago (held out)

CHI_PERMITS = "https://data.cityofchicago.org/resource/ydr8-5enu.csv"
CHI_ZONING_2012 = "https://data.cityofchicago.org/download/p8va-airx/application%2Fzip"
CHI_PARCELS = "https://datacatalog.cookcountyil.gov/resource/77tz-riq7.geojson"
CHI_LICENCE = "City of Chicago data portal terms of use (public record)"
COOK_LICENCE = "Cook County open data terms of use (public record)"


def fetch_chicago(refresh: bool) -> None:
    man = Manifest(D / "chicago", "tod_cases_chicago", "City of Chicago (permits, zoning) and Cook County (parcels)")
    name = "permits_new_construction.csv"
    if not man.have(name, refresh):
        params = {"$select": "id,permit_,permit_type,issue_date,work_description,latitude,longitude,community_area",
                  "$where": "permit_type='PERMIT - NEW CONSTRUCTION'", "$limit": 200000, "$order": "id"}
        url = CHI_PERMITS + "?" + urllib.parse.urlencode(params)
        man.record(name, http_get(url, timeout=900), url, licence=CHI_LICENCE,
                   note="Building Permits (ydr8-5enu), new-construction permits 2006 onward; contact fields not requested")
    else:
        print(f"  {name}: kept")
    download_file(man, "zoning_nov2012.zip", CHI_ZONING_2012, refresh, CHI_LICENCE,
                  note="Boundaries - Zoning Districts (deprecated October 2014), p8va-airx, file Zoning_nov2012.zip")
    ntm_rail_stops(man, "rail_stops.geojson", ["50066", "50118"], refresh)
    name = "zoning_current.geojson"
    if not man.have(name, refresh):
        url = "https://data.cityofchicago.org/resource/dj47-wfun.geojson?" + urllib.parse.urlencode(
            {"$select": "zone_class,the_geom", "$limit": 100000})
        man.record(name, http_get(url, timeout=900), url, licence=CHI_LICENCE,
                   note="Boundaries - Zoning Districts (current), dj47-wfun: zoning changes since November 2012")
    else:
        print(f"  {name}: kept")
    name = "parcels.geojson"
    if man.have(name, refresh):
        print(f"  {name}: kept")
        return
    feats, first, off = [], None, 0
    while True:
        params = {"$select": "pin10,assessorbldgclass,municipality,the_geom", "$where": "municipality='Chicago'",
                  "$limit": 50000, "$offset": off, "$order": "pin10"}
        url = CHI_PARCELS + "?" + urllib.parse.urlencode(params)
        first = first or url
        f = json.loads(http_get(url, timeout=900)).get("features", [])
        feats += f
        print(f"    {len(feats):,} parcels")
        if len(f) < 50000:
            break
        off += len(f)
    data = json.dumps({"type": "FeatureCollection", "features": feats}).encode()
    man.record(name, data, first, licence=COOK_LICENCE, features=len(feats),
               note="Cook County ccgisdata Parcel 2021 (77tz-riq7), all parcels with municipality Chicago, pages of 50,000")


# --------------------------------------------------------------------------- Philadelphia

PHL_CARTO = "https://phl.carto.com/api/v2/sql"
PHL_AGS = "https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services"
PHL_LICENCE = "City of Philadelphia open data (OpenDataPhilly); no licence text in the API; public record (D1)"
PHL_SNAPSHOTS = ["Zoning_BaseDistricts_032015", "Zoning_BaseDistricts_052016", "zoning_basedistricts_092017",
                 "zoning_basedistricts_072018", "zoning_basedistricts_122019", "zoning_basedistricts_062020",
                 "zoning_basedistricts_122021", "zoning_basedistricts_122022", "zoning_basedistricts_032023",
                 "zoning_basedistricts_122024", "zoning_basedistricts_122025"]


def fetch_philadelphia(refresh: bool) -> None:
    man = Manifest(D / "philadelphia", "tod_cases_philadelphia", "City of Philadelphia (L&I permits, zoning, remapping, parcels)")
    name = "permits_new_construction.csv"
    if not man.have(name, refresh):
        q = ("SELECT permitnumber, permittype, typeofwork, approvedscopeofwork, permitissuedate, numberofunits, "
             "numberofstories, parcel_id_num, ST_Y(the_geom) AS lat, ST_X(the_geom) AS lon FROM permits WHERE "
             "permittype='BP_NEWCNST' OR (permittype IN ('Residential Building','Building','Master Plan') "
             "AND typeofwork ILIKE 'new constr%')")
        url = PHL_CARTO + "?" + urllib.parse.urlencode({"q": q, "format": "csv"})
        man.record(name, http_get(url, timeout=900), url, licence=PHL_LICENCE,
                   note="L&I permits (Carto table permits), new-construction types; owner and contractor fields not requested")
    else:
        print(f"  {name}: kept")
    save_layer(man, "remapping.geojson", f"{PHL_AGS}/ProposedZoning_Implementation_Public_View/FeatureServer/0", refresh,
               PHL_LICENCE, out_fields="ExistCode,PropZone,Remapping_Name,Type_,Origination,Bill_Number_TXT,Enacted_Date,ReMap_Status", page=1000)
    save_layer(man, "zoning_pre_aug2012.geojson", f"{PHL_AGS}/Zoning_PreAug2012/FeatureServer/0", refresh, PHL_LICENCE,
               out_fields="CODE,CATEGORY", page=2000)
    for snap in PHL_SNAPSHOTS:
        save_layer(man, f"{snap.lower()}.geojson", f"{PHL_AGS}/{snap}/FeatureServer/0", refresh, PHL_LICENCE, out_fields="*", page=2000)
    save_layer(man, "zoning_overlays.geojson", f"{PHL_AGS}/Zoning_Overlays/FeatureServer/0", refresh, PHL_LICENCE, out_fields="*", page=2000)
    name = "zoning_code_characteristics.json"
    if not man.have(name, refresh):
        url = f"{PHL_AGS}/ZoningCodeCharacteristics/FeatureServer/0/query?where=1%3D1&outFields=*&returnGeometry=false&f=json"
        man.record(name, http_get(url), url, licence=PHL_LICENCE, note="maximum height, FAR, lot area and open area by district")
    save_layer(man, "parcels.geojson", f"{PHL_AGS}/PWD_PARCELS/FeatureServer/0", refresh, PHL_LICENCE,
               out_fields="parcelid,bldg_desc,gross_area", page=2000)
    ntm_rail_stops(man, "rail_stops.geojson", ["30019"], refresh)  # SEPTA rail, subway and trolley stops


# --------------------------------------------------------------------------- Raleigh

RAL = "https://services.arcgis.com/v400IkDOw1ad7Yad/arcgis/rest/services"
RAL_LICENCE = "Open Raleigh Data Policy (City of Raleigh open data)"


def fetch_raleigh(refresh: bool) -> None:
    man = Manifest(D / "raleigh", "tod_cases_raleigh", "City of Raleigh (building permits, rezoning cases, TOD overlay)")
    save_layer(man, "permits_new_residential.geojson", f"{RAL}/Building_Permits/FeatureServer/0", refresh, RAL_LICENCE,
               where="workclassmapped='New' AND permitclassmapped='Residential'",
               out_fields="permitnum,issueddate,issueddate_yr,housingunitstotal,censuslanduse,workclassmapped,permitclassmapped",
               page=2000)
    save_layer(man, "rezoning_cases.geojson", f"{RAL}/Rezoning_Case_Boundaries_View/FeatureServer/0", refresh, RAL_LICENCE,
               out_fields="ZONE_CASE,PrevZoning,ZON_REQ,STATUS,StatusDate", page=1000)
    save_layer(man, "tod_overlays.geojson", f"{RAL}/TOD_Zoning_Overlays_View/FeatureServer/0", refresh, RAL_LICENCE,
               out_fields="*", page=1000)

# --------------------------------------------------------------------------- main

FETCHERS = {"census": fetch_census, "bps": fetch_bps, "charlotte": fetch_charlotte, "nyc": fetch_nyc, "stpaul": fetch_stpaul, "chicago": fetch_chicago, "philadelphia": fetch_philadelphia, "raleigh": fetch_raleigh}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--city", nargs="*", choices=list(FETCHERS), help="default: all")
    ap.add_argument("--refresh", action="store_true", help="re-download files that already exist")
    a = ap.parse_args(argv)
    for c in a.city or list(FETCHERS):
        print(f"== {c}")
        FETCHERS[c](a.refresh)


if __name__ == "__main__":
    main()
