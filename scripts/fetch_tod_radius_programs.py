"""Fetch data for the station-area radius programs (docs/tod/STATION_AREA_PLAN.md, LOCKED section).

Raw files stay local under data/raw/tod_radius_programs/<city>/ with a manifest (source, date, rows, sha256).
Stages: sd_permits, honolulu_permits, la_permits.
"""
from __future__ import annotations
import argparse, hashlib, json, time, urllib.parse, urllib.request
from datetime import date
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "tod_radius_programs"


def _get(url: str, data: bytes | None = None, tries: int = 4) -> bytes:
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": "housing-policy-model/0.1"})
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 ** (i + 1))
    raise RuntimeError


def _manifest(city: str, name: str, url: str, rows: int, path: Path, note: str = "") -> None:
    m = RAW / city / "manifest.json"
    d = json.loads(m.read_text()) if m.exists() else {}
    d[name] = {"url": url, "accessed": str(date.today()), "rows": rows, "bytes": path.stat().st_size,
               "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "note": note}
    m.write_text(json.dumps(d, indent=1))


def arcgis_all(layer: str, where: str, fields: str, page: int = 2000) -> list[dict]:
    """Page through an ArcGIS layer by OBJECTID ranges; returns attribute dicts."""
    ids = json.loads(_get(f"{layer}/query?" + urllib.parse.urlencode({"where": where, "returnIdsOnly": "true", "f": "json"})))["objectIds"] or []
    ids.sort()
    out: list[dict] = []
    for i in range(0, len(ids), page):
        chunk = ids[i:i + page]
        body = urllib.parse.urlencode({"where": f"OBJECTID>={chunk[0]} AND OBJECTID<={chunk[-1]} AND ({where})",
                                       "outFields": fields, "returnGeometry": "false", "f": "json"}).encode()
        out += [f["attributes"] for f in json.loads(_get(f"{layer}/query", body))["features"]]
    return out


def sd_permits() -> None:
    layer = "https://webmaps.sandiego.gov/arcgis/rest/services/Planning/PLN_Housing_ServiceLayers/MapServer/0"
    where = "TOTAL_DU>0 AND APPROVAL_TYPE IN ('Building Permit','Combination Building Permit')"
    rows = arcgis_all(layer, where, "OBJECTID,APPROVAL_ID,PROJECT_ID,DEVELOPMENT_ID,APPROVAL_TYPE,APPROVAL_STATUS,"
                      "JOB_BC_CODE,JOB_BC_CODE_DESCRIPTION,APPROVAL_ISSUE_DATE,APPROVAL_CLOSE_DATE,LAT_JOB,LNG_JOB,"
                      "TOTAL_DU,TOTAL_ADU,TOTAL_JADU,APPROVAL_DU_BONUS,APPROVAL_STORIES,RECORD_DATA_SOURCE")
    p = RAW / "san_diego" / "permits.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rows))
    _manifest("san_diego", "permits.json", layer, len(rows), p,
              "City of San Diego Housing Element permit layer; building and combination building permits with homes")
    print("san diego permits", len(rows))


def honolulu_permits() -> None:
    base = "https://data.honolulu.gov/resource/4vab-c87q.json"
    cols = ("buildingpermitno,issuedate,createddate,statusdescription,tmk,joblocation,numunitsadd,newbuilding,"
            "proposeduse,occupancygroupassessed,accessorydwellingunitadu,ohana,commercialresidential,structurecode,"
            "foundationonly,shellonly,addition,alteration,repair,demolition,externalfilenum,estimatedvalueofwork")
    rows, off = [], 0
    while True:
        q = urllib.parse.urlencode({"$select": cols, "$where": "numunitsadd>0", "$order": "objectid", "$limit": 50000, "$offset": off})
        b = json.loads(_get(f"{base}?{q}"))
        rows += b; off += len(b)
        if len(b) < 50000:
            break
    p = RAW / "honolulu" / "permits.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rows))
    _manifest("honolulu", "permits.json", base, len(rows), p, "City and County of Honolulu building permits with homes added; placed by TMK")
    print("honolulu permits", len(rows))


def arcgis_geojson(layer: str, out: Path, fields: str, page: int = 1000, offset: float = 0.00002) -> int:
    """Page an ArcGIS layer into one GeoJSON file (EPSG 4326, lightly simplified)."""
    ids = sorted(json.loads(_get(f"{layer}/query?" + urllib.parse.urlencode({"where": "1=1", "returnIdsOnly": "true", "f": "json"})))["objectIds"])
    feats = []
    for i in range(0, len(ids), page):
        c = ids[i:i + page]
        body = urllib.parse.urlencode({"where": f"objectid>={c[0]} AND objectid<={c[-1]}", "outFields": fields, "outSR": 4326,
                                       "geometryPrecision": 6, "maxAllowableOffset": offset, "f": "geojson"}).encode()
        feats += json.loads(_get(f"{layer}/query", body))["features"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    return len(feats)


def honolulu_parcels() -> None:
    layer = "https://geodata.hawaii.gov/arcgis/rest/services/ParcelsZoning/MapServer/11"
    p = RAW / "honolulu" / "parcels.geojson"
    n = arcgis_geojson(layer, p, "objectid,tmk,tmk8num,tmk9num,zone,section,plat,gisacres,street_parcel")
    _manifest("honolulu", "parcels.geojson", layer, n, p, "Oahu tax parcels (State GIS mirror of the City's HOLIS layer, April 2026); current parcels only")
    print("honolulu parcels", n)


def la_permits() -> None:
    """LADBS new-building permits, whole city (same fields as the earlier reform-area extracts; no people fields)."""
    sel = "permit_nbr,permit_type,permit_sub_type,issue_date,du_changed,adu_changed,apn,zone,work_desc,lat,lon"
    for ds in ("e67z-kt2n", "dyxf-7hc4", "pi9x-tg5x"):
        base = f"https://data.lacity.org/resource/{ds}.csv"
        out = RAW / "la" / f"permits_citywide_{ds}.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        parts, off = [], 0
        while True:
            q = urllib.parse.urlencode({"$select": sel, "$where": "permit_type='Bldg-New'", "$order": "permit_nbr", "$limit": 100000, "$offset": off})
            b = _get(f"{base}?{q}").decode()
            lines = b.splitlines()
            parts.append(lines if not parts else lines[1:])
            n = len(lines) - 1
            off += n
            if n < 100000:
                break
        out.write_text("\n".join(l for p in parts for l in p) + "\n")
        _manifest("la", out.name, base, off, out, "LADBS building permits, type Bldg-New, whole city")
        print(ds, off)


def program_areas() -> None:
    """Each program's own eligibility map: LA TOC tiers as of October 2017 (City Planning), San Diego transit priority
    areas (City Planning; check vintage against the 2021 regional plan)."""
    src = {"la/toc_tiers_oct2017.geojson": ("https://services1.arcgis.com/tzwalEyxl2rpamKs/arcgis/rest/services/TOC_Tiers_Oct2017_new/FeatureServer/0", "*"),
           "san_diego/transit_priority_areas_sandag_2022.geojson": ("https://geo.sandag.org/server/rest/services/Hosted/Transit_Priority_Areas/FeatureServer/0", "*"),
           "honolulu/tod_zone_change_waipahu_tc.geojson": ("https://services.arcgis.com/tNJpAOha4mODLkXz/arcgis/rest/services/TOD_ZoneChange_WaipahuTC_Approved/FeatureServer/0", "*"),
           "honolulu/tod_zone_change_west_loch.geojson": ("https://services.arcgis.com/tNJpAOha4mODLkXz/arcgis/rest/services/TOD_ZoneChange_WestLoch_Approved/FeatureServer/0", "*"),
           "honolulu/rail_stations.geojson": ("https://services6.arcgis.com/2cZSk3EXXiOHcbOl/arcgis/rest/services/HART_Transit_Stations_PUBLIC/FeatureServer/0", "*"),
           "san_diego/transit_priority_areas.geojson": ("https://webmaps.sandiego.gov/arcgis/rest/services/Planning/PLN_TransitPriorityArea/MapServer/0", "*")}
    for rel, (layer, fields) in src.items():
        out = RAW / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        q = urllib.parse.urlencode({"where": "1=1", "outFields": fields, "outSR": 4326, "f": "geojson"})
        b = _get(f"{layer}/query?{q}")
        out.write_bytes(b)
        n = len(json.loads(b)["features"])
        _manifest(rel.split("/")[0], out.name, layer, n, out, "program eligibility map")
        print(rel, n)


def arcgis_csv(layer: str, out: Path, fields: str, page: int = 2000, idf: str = "objectid", centroid: bool = False,
               where: str = "1=1") -> int:
    """Page an ArcGIS layer's attributes (no geometry) into a CSV, by object-id ranges."""
    import csv
    ids = sorted(json.loads(_get(f"{layer}/query?" + urllib.parse.urlencode({"where": where, "returnIdsOnly": "true", "f": "json"})))["objectIds"])
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = fields.split(",") + (["cx", "cy"] if centroid else [])
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for i in range(0, len(ids), page):
            c = ids[i:i + page]
            q = {"where": f"{idf}>={c[0]} AND {idf}<={c[-1]} AND ({where})", "outFields": fields, "returnGeometry": "false", "f": "json"}
            if centroid == "geom":   # services without centroid support: coarse shape, centre of its first ring
                q.update({"returnGeometry": "true", "outSR": 4326, "maxAllowableOffset": 0.0002, "geometryPrecision": 6})
            elif centroid:
                q.update({"returnCentroid": "true", "outSR": 4326})
            for f in json.loads(_get(f"{layer}/query", urllib.parse.urlencode(q).encode()))["features"]:
                a = dict(f["attributes"])
                if centroid == "geom" and f.get("geometry", {}).get("rings"):
                    r = f["geometry"]["rings"][0]
                    a["cx"], a["cy"] = sum(p[0] for p in r) / len(r), sum(p[1] for p in r) / len(r)
                elif centroid and f.get("centroid"):
                    a["cx"], a["cy"] = f["centroid"]["x"], f["centroid"]["y"]
                w.writerow(a)
    return len(ids)


def sd_parcels() -> None:
    """San Diego County parcels (SANDAG copy of SanGIS/Assessor): values, homes, effective year built, last
    recorded document date, land use and zoning, point coordinates. No owner names. Stays local."""
    layer = "https://geo.sandag.org/server/rest/services/Hosted/Parcels/FeatureServer/0"
    f = ("objectid,apn,situs_juris,asr_land,asr_impr,docdate,acreage,taxstat,ownerocc,asr_zone,asr_landuse,unitqty,"
         "nucleus_zone_cd,nucleus_use_cd,year_effective,total_lvg_area,x_coord,y_coord,multi")
    out = RAW / "san_diego" / "county_parcels.csv"
    n = arcgis_csv(layer, out, f)
    _manifest("san_diego", out.name, layer, n, out, "San Diego County parcels (SANDAG hosted); no owner names; local only")
    print("sd parcels", n)


def la_parcels() -> None:
    """LA County parcels (Assessor via county GIS): year built and homes for up to 5 buildings, roll values and
    base years (Proposition 13: values reflect the last sale year), use, public-agency flag, centre point. No owner names."""
    layer = "https://public.gis.lacounty.gov/public/rest/services/LACounty_Cache/LACounty_Parcel/MapServer/0"
    f = ("OBJECTID,AIN,SitusCity,UseCode,UseType,AgencyType,YearBuilt1,EffectiveYear1,Units1,SQFTmain1,YearBuilt2,Units2,"
         "YearBuilt3,Units3,YearBuilt4,Units4,YearBuilt5,Units5,Roll_Year,Roll_LandValue,Roll_ImpValue,Roll_LandBaseYear,"
         "Roll_ImpBaseYear,ParcelCreateDate,CENTER_LAT,CENTER_LON,Shape.STArea()")
    out = RAW / "la" / "county_parcels.csv"
    n = arcgis_csv(layer, out, f, page=1000, idf="OBJECTID")
    _manifest("la", out.name, layer, n, out, "LA County parcels (Assessor via county GIS); no owner names; local only")
    print("la parcels", n)


def honolulu_values() -> None:
    """Honolulu assessed land and building values by tax-map key (City cadastral table ASMTGIS). No owner fields."""
    layer = "https://services.arcgis.com/tNJpAOha4mODLkXz/arcgis/rest/services/CadastralTables/FeatureServer/9"
    out = RAW / "honolulu" / "assessed_values.csv"
    n = arcgis_csv(layer, out, "objectid,tmk,suffix,seq,taxyr,buildingvalue,landvalue,taxratecode,ovrclass,pittsqft,pittacre")
    _manifest("honolulu", out.name, layer, n, out, "Honolulu assessed values (ASMTGIS); local only")
    print("honolulu values", n)


def king_assessor() -> None:
    """King County Assessor extracts (Seattle, Bellevue and comparison cities): parcels, residential buildings,
    apartment complexes, commercial buildings, condo complexes. Year built and homes; no owner fields in these files.
    Values come from the King County value-history file already used by the lot model (tod_land_values)."""
    out = RAW / "king"
    out.mkdir(parents=True, exist_ok=True)
    for f in ("Parcel.zip", "Residential Building.zip", "Apartment Complex.zip", "Commercial Building.zip", "Condo Complex and Units.zip"):
        url = "https://aqua.kingcounty.gov/extranet/assessor/" + urllib.parse.quote(f)
        p = out / f.replace(" ", "_")
        p.write_bytes(_get(url))
        _manifest("king", p.name, url, -1, p, "King County Assessor data download; local only")
        print(f, p.stat().st_size)


def king_parcels() -> None:
    """King County parcel points with appraised land and building values, zoning, use, lot size. Taxpayer name and
    address fields are not requested."""
    layer = "https://services.arcgis.com/Ej0PsM5Aw677QF1W/arcgis/rest/services/PARCEL_ADDRESS_PUB_AREA_3069/FeatureServer/0"
    f = "OBJECTID,PIN,MAJOR,MINOR,CTYNAME,LAT,LON,LOTSQFT,APPRLNDVAL,APPR_IMPR,KCA_ZONING,KCA_ACRES,PREUSE_CODE,PREUSE_DESC,PROPTYPE,NEW_CONSTR"
    out = RAW / "king" / "parcels.csv"
    n = arcgis_csv(layer, out, f, page=1000, idf="OBJECTID")
    _manifest("king", out.name, layer, n, out, "King County parcels with address (public layer); no taxpayer fields; local only")
    print("king parcels", n)


def _socrata_csv(base: str, select: str, where: str, out: Path, page: int = 200000) -> int:
    parts, off = [], 0
    while True:
        q = urllib.parse.urlencode({"$select": select, "$where": where, "$order": ":id", "$limit": page, "$offset": off})
        lines = _get(f"{base}?{q}").decode().splitlines()
        parts.append(lines if not parts else lines[1:])
        n = len(lines) - 1
        off += n
        if n < page:
            break
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(l for p in parts for l in p) + "\n")
    return off


def cook_parcels() -> None:
    """Cook County Assessor parcel universe (points, class, census geography) and assessed values, for the
    Chicago 2022 before-window start (2016) and today (2024). No owner fields. Residential year built comes from
    the single- and multi-family characteristics file (large apartment and condo buildings have none: flagged)."""
    for y in (2016, 2024):
        n = _socrata_csv("https://datacatalog.cookcountyil.gov/resource/nj4t-kc8j.csv",
                         "pin,year,class,lon,lat,census_block_geoid,census_place_geoid,township_name",
                         f"year={y}", RAW / "cook" / f"parcel_universe_{y}.csv")
        _manifest("cook", f"parcel_universe_{y}.csv", "https://datacatalog.cookcountyil.gov/resource/nj4t-kc8j", n, RAW / "cook" / f"parcel_universe_{y}.csv", "local only")
        n = _socrata_csv("https://datacatalog.cookcountyil.gov/resource/uzyt-m557.csv",
                         "pin,year,class,certified_bldg,certified_land,board_bldg,board_land", f"year={y}", RAW / "cook" / f"assessed_values_{y}.csv")
        _manifest("cook", f"assessed_values_{y}.csv", "https://datacatalog.cookcountyil.gov/resource/uzyt-m557", n, RAW / "cook" / f"assessed_values_{y}.csv", "local only")
        print(y, "done")
    n = _socrata_csv("https://datacatalog.cookcountyil.gov/resource/x54s-btds.csv", "pin,year,card,class,char_yrblt,char_apts,char_bldg_sf,char_land_sf",
                     "year=2024", RAW / "cook" / "res_characteristics_2024.csv")
    _manifest("cook", "res_characteristics_2024.csv", "https://datacatalog.cookcountyil.gov/resource/x54s-btds", n, RAW / "cook" / "res_characteristics_2024.csv", "local only")
    print("cook res chars", n)


def slc_parcels() -> None:
    """Salt Lake County parcels (Utah UGRC LIR): market values, year built and effective year, homes, class, centre point."""
    layer = "https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/Parcels_SaltLake_LIR/FeatureServer/0"
    f = ("OBJECTID,PARCEL_ID,PARCEL_CITY,CURRENT_ASOF,TAXEXEMPT_TYPE,TOTAL_MKT_VALUE,LAND_MKT_VALUE,PARCEL_ACRES,PROP_CLASS,"
         "HOUSE_CNT,BLDG_SQFT,FLOORS_CNT,BUILT_YR,EFFBUILT_YR,PROP_TYPE")
    out = RAW / "salt_lake" / "county_parcels.csv"
    n = arcgis_csv(layer, out, f, page=2000, idf="OBJECTID", centroid=True)
    _manifest("salt_lake", out.name, layer, n, out, "Salt Lake County LIR parcels (UGRC); local only")
    print("salt lake parcels", n)


def stpaul_parcels() -> None:
    """Saint Paul tax parcels (Ramsey County via the City): values, land use, year built, homes, last sale, point.
    Owner, taxpayer and homestead name and address fields are not requested."""
    layer = "https://services1.arcgis.com/9meaaHE3uiba0zr8/arcgis/rest/services/Saint_Paul_Tax_Parcels/FeatureServer/0"
    f = ("OBJECTID,ParcelID,SiteCityName,OwnershipCategory,ParcelSquareFeet,EMVYear,EMVLand,EMVBuilding,LandUseCode,"
         "LandUseCodeDescription,TaxExemptYN,StructureDescription,DwellingType,LivingUnit,YearBuilt,EffectiveYearBuilt,"
         "LastSaleDate,SalePrice,Latitude,Longitude")
    out = RAW / "saint_paul" / "parcels.csv"
    n = arcgis_csv(layer, out, f, page=2000, idf="OBJECTID")
    _manifest("saint_paul", out.name, layer, n, out, "Saint Paul tax parcels; no owner fields; local only")
    print("saint paul parcels", n)


def denver_parcels() -> None:
    """Denver parcels, whole city (Assessor via the City): class, zoning, appraised values, year built, homes, last
    sale, centre point. Owner name and address fields are not requested."""
    layer = "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/ArcGIS/rest/services/ODC_PROP_PARCELS_A/FeatureServer/245"
    f = ("OBJECTID,SCHEDNUM,PROP_CLASS,D_CLASS_CN,ZONE_ID,APPRAISED_LAND_VALUE,APPRAISED_IMP_VALUE,LAND_AREA,"
         "RES_ORIG_YEAR_BUILT,COM_ORIG_YEAR_BUILT,COM_STRUCTURE_TYPE,TOT_UNITS,SALE_YEAR,SALE_PRICE,EXEMPT_AMT_LOCAL")
    out = RAW / "denver" / "parcels_citywide.csv"
    n = arcgis_csv(layer, out, f, page=2000, idf="OBJECTID", centroid=True)
    _manifest("denver", out.name, layer, n, out, "Denver parcels, whole city; no owner fields; local only")
    print("denver parcels", n)


def mecklenburg_parcels() -> None:
    """Mecklenburg County parcels from NC OneMap statewide parcels: land and building values, structure year,
    number of structures, use, last sale date, centre point. Owner names and mailing addresses not requested.
    No homes-per-parcel field: Charlotte counts come from city permits."""
    layer = "https://services.nconemap.gov/secure/rest/services/NC1Map_Parcels/FeatureServer/1"
    f = "objectid,parno,scity,landval,improvval,parval,gisacres,struct,structno,structyear,parusecode,parusedesc,owntype,saledate,revisedate"
    out = RAW / "mecklenburg" / "parcels.csv"
    n = arcgis_csv(layer, out, f, page=5000, idf="objectid", centroid=True, where="stcntyfips='37119'")
    _manifest("mecklenburg", out.name, layer, n, out, "NC OneMap parcels, Mecklenburg County; no owner fields; local only")
    print("mecklenburg parcels", n)


def travis_parcels() -> None:
    """Travis County appraisal district parcels (City of Austin copy): land value, zoning, centre point. Current
    values only; no year built or homes (Austin counts come from city permits)."""
    layer = "https://services.arcgis.com/0L95CJ0VTaxqcmED/arcgis/rest/services/EXTERNAL_tcad_parcel/FeatureServer/0"
    out = RAW / "travis" / "parcels.csv"
    n = arcgis_csv(layer, out, "OBJECTID_1,PROP_ID,CONDOID,NBHD,ZONING,LAND_VALUE,Shape__Area", page=2000, idf="OBJECTID_1", centroid=True)
    _manifest("travis", out.name, layer, n, out, "TCAD parcels (City of Austin copy); local only")
    print("travis parcels", n)


def portland_taxlots() -> None:
    """Portland-area taxlots (PortlandMaps; Multnomah, Washington and Clackamas): year built, homes, land and
    building values for three years, last sale, use, centre point. Owner names and addresses not requested."""
    layer = "https://www.portlandmaps.com/arcgis/rest/services/Public/Taxlots/MapServer/0"
    f = ("OBJECTID,STATE_ID,SITECITY,COUNTY,PROP_CODE,PRPCD_DESC,LANDUSE,YEARBUILT,BLDGSQFT,FLOORS,UNITS,MKTVALYR1,LANDVAL1,"
         "BLDGVAL1,MKTVALYR3,LANDVAL3,BLDGVAL3,SALEDATE,SALEPRICE,A_T_ACRES")
    out = RAW / "portland" / "taxlots.csv"
    n = arcgis_csv(layer, out, f, page=2000, idf="OBJECTID", centroid="geom")
    _manifest("portland", out.name, layer, n, out, "PortlandMaps taxlots (tri-county); no owner fields; local only")
    print("portland taxlots", n)


STAGES = {"portland_taxlots": portland_taxlots, "travis_parcels": travis_parcels, "mecklenburg_parcels": mecklenburg_parcels, "denver_parcels": denver_parcels, "stpaul_parcels": stpaul_parcels, "slc_parcels": slc_parcels, "cook_parcels": cook_parcels, "king_parcels": king_parcels, "king_assessor": king_assessor, "honolulu_values": honolulu_values, "la_parcels": la_parcels, "sd_parcels": sd_parcels, "program_areas": program_areas, "la_permits": la_permits, "sd_permits": sd_permits, "honolulu_permits": honolulu_permits, "honolulu_parcels": honolulu_parcels}

if __name__ == "__main__":
    a = argparse.ArgumentParser(); a.add_argument("stage", choices=STAGES); STAGES[a.parse_args().stage]()
