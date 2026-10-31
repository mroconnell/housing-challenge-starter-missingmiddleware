"""No-reform comparison cities outside Wisconsin for the TOD lot model (docs/tod/LOT_MODEL_PLAN.md item 46).

    uv run --all-extras python scripts/fetch_tod_placebo_cities.py [--only columbus_parcels,columbus_permits,kc_parcels,kc_permits]

Public sources only. Owner names, owner addresses and applicant names are never requested or kept.
Writes data/raw/tod_placebo_cities/ (never committed) with a manifest of URLs, dates, sizes and hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from missing_middleware.paths import RAW  # noqa: E402

DIR = RAW / "tod_placebo_cities"
UA = {"User-Agent": "missing-middleware research (TOD lot model, no-reform cities)"}
COL_PARCELS = "https://gis.franklincountyohio.gov/hosting/rest/services/ParcelFeatures/Parcel_Features/MapServer/0"
COL_PERMITS = "https://services1.arcgis.com/9yy6msODkIBzkUXU/arcgis/rest/services/Building_Permits/FeatureServer/0"
KC = "https://data.kcmo.org/resource"


def get(url: str, timeout: int = 300) -> bytes:
    for k in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except Exception:  # noqa: BLE001
            if k == 4:
                raise
            time.sleep(2 ** (k + 1))
    return b""


def manifest() -> dict:
    p = DIR / "manifest.json"
    return json.loads(p.read_text()) if p.exists() else {"source_id": "tod_placebo_cities", "files": {}}


def record(m: dict, name: str, data: bytes, url: str, licence: str) -> None:
    (DIR / name).write_bytes(data)
    m["files"][name] = {"url": url, "accessed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "licence": licence}
    (DIR / "manifest.json").write_text(json.dumps(m, indent=1) + "\n")
    print(f"  {name}: {len(data):,} bytes", flush=True)


def arcgis_all(layer: str, where: str, fields: str, geometry: bool, page: int) -> tuple[list, str]:
    feats, off, first = [], 0, None
    while True:
        p = dict(where=where, outFields=fields, returnGeometry=str(geometry).lower(), outSR=4326, f="geojson",
                 resultOffset=off, resultRecordCount=page, orderByFields="OBJECTID")
        url = f"{layer}/query?" + urllib.parse.urlencode(p)
        first = first or url
        d = json.loads(get(url))
        if "error" in d:
            raise RuntimeError(d["error"])
        f = d.get("features", [])
        feats += f
        print(f"    {len(feats):,}", end="\r", flush=True)
        if len(f) < page:
            break
        off += page
    return feats, first


def socrata_all(dataset: str, select: str, where: str, geojson: bool = False) -> tuple[list, str]:
    rows, off, first, lim = [], 0, None, 50000
    ext = "geojson" if geojson else "json"
    while True:
        q = {"$select": select, "$limit": lim, "$offset": off, "$order": ":id"}
        if where:
            q["$where"] = where
        url = f"{KC}/{dataset}.{ext}?" + urllib.parse.urlencode(q)
        first = first or url
        d = json.loads(get(url))
        part = d["features"] if geojson else d
        rows += part
        print(f"    {len(rows):,}", end="\r", flush=True)
        if len(part) < lim:
            break
        off += lim
    return rows, first


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="columbus_parcels,columbus_permits,kc_parcels,kc_permits")
    a = ap.parse_args(argv)
    DIR.mkdir(parents=True, exist_ok=True)
    m = manifest()
    todo = a.only.split(",")
    if "columbus_parcels" in todo:
        print("Columbus parcels", flush=True)
        f, url = arcgis_all(COL_PARCELS, "CVTTXDSCRP='CITY OF COLUMBUS' OR CVTTXDSCRP LIKE 'COLUMBUS-%'",
                            "OBJECTID,PARCELID,ACRES,CLASSCD,USECD,RESYRBLT,LNDVALUEBASE,BLDVALUEBASE", True, 2000)
        record(m, "columbus_parcels.geojson", json.dumps({"type": "FeatureCollection", "features": f}).encode(), url,
               "Franklin County Auditor open GIS data (licence not stated on the service)")
    if "columbus_permits" in todo:
        print("Columbus permits", flush=True)
        f, url = arcgis_all(COL_PERMITS, "UNITS > 0 AND ISSUED_YEAR >= 2009 AND ISSUED_YEAR <= 2024",
                            "OBJECTID,B1_PER_TYPE,B1_PER_SUB_TYPE,B1_PER_CATEGORY,B1_PARCEL_NBR,ISSUED_YEAR,ISSUED_DT,UNITS",
                            True, 2000)
        record(m, "columbus_permits.geojson", json.dumps({"type": "FeatureCollection", "features": f}).encode(), url,
               "City of Columbus open data (public-domain dedication per the city's open data page)")
    if "kc_parcels" in todo:
        print("Kansas City parcels", flush=True)
        f, url = socrata_all("6g4y-sh3m", "the_geom,kivapin,landusecode,shape_area,assessed_land_value,assessed_improve_value", "", True)
        record(m, "kc_parcels.geojson", json.dumps({"type": "FeatureCollection", "features": f}).encode(), url,
               "City of Kansas City, Missouri open data (data.kcmo.org)")
    if "kc_permits" in todo:
        print("Kansas City permits", flush=True)
        rows = []
        for ds, col in (("cvnj-fvgf", "dwelling_units_gained_or_lost"), ("jnga-5v37", "dwelling_units_gained_or")):
            r, url = socrata_all(ds, f"year,month,res_non,type,sf_mf,{col} as units,pin,how_far_east,how_far_north",
                                 f"type = 'New Construction' AND year >= '2004'")
            for x in r:
                x["source"] = ds
            rows += r
        record(m, "kc_permits.json", json.dumps(rows).encode(), f"{KC}/cvnj-fvgf.json and {KC}/jnga-5v37.json (New Construction)",
               "City of Kansas City, Missouri open data (data.kcmo.org)")


if __name__ == "__main__":
    main()
