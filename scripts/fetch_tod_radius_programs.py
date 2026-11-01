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


STAGES = {"program_areas": program_areas, "la_permits": la_permits, "sd_permits": sd_permits, "honolulu_permits": honolulu_permits, "honolulu_parcels": honolulu_parcels}

if __name__ == "__main__":
    a = argparse.ArgumentParser(); a.add_argument("stage", choices=STAGES); STAGES[a.parse_args().stage]()
