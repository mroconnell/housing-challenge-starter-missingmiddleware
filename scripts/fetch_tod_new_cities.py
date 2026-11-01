"""Fetch public data for the new TOD reform cities (docs/tod/NEW_REFORM_CITIES_PLAN.md).

    uv run --all-extras python scripts/fetch_tod_new_cities.py --city denver

Writes data/raw/tod_new_cities/<city>/ (never committed) with a manifest of URLs, dates, sizes and hashes.
Denver: zone map amendments (all), residential construction permits (all, points, units), parcels (all).
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

# Parcels only around the 2018 and 2016 candidate areas (north-east Denver), not the whole city
PARCEL_ENVELOPE = "-105.02,39.74,-104.75,39.82"
UA = {"User-Agent": "missing-middleware research (TOD lot model, new reform cities)"}
DEN = "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/ArcGIS/rest/services"
DENVER = {
    "zone_map_amendments": (f"{DEN}/ODC_ZONE_MAPAMENDMENTS_A/FeatureServer/356", "*"),
    "rail_stations": (f"{DEN}/ODC_TRANS_RAILTRANSITSTATIONS_P/FeatureServer/212", "*"),
    "parcels": (f"{DEN}/ODC_PROP_PARCELS_A/FeatureServer/245", "OBJECTID,SCHEDNUM,D_CLASS_CN,ZONE_ID,LAND_AREA,APPRAISED_LAND_VALUE,APPRAISED_IMP_VALUE,RES_ORIG_YEAR_BUILT,COM_ORIG_YEAR_BUILT,TOT_UNITS"),
    # Denver files apartment buildings as commercial construction permits, with their dwelling units
    "commercial_permits": (f"{DEN}/ODC_DEV_COMMERCIALCONSTPERMIT_P/FeatureServer/317",
                           "OBJECTID,DATE_ISSUED,PERMIT_NUM,CLASS,UNITS,SCHEDNUM,STAT_CODE_1,STAT_CODE_2,STAT_CODE_3,CANCEL"),
    "residential_permits": (f"{DEN}/ODC_DEV_RESIDENTIALCONSTPERMIT_P/FeatureServer/316",
                            "OBJECTID,DATE_ISSUED,PERMIT_NUM,CLASS,UNITS,SCHEDNUM,STAT_CODE_1,STAT_CODE_2,STAT_CODE_3,CANCEL"),
}


def get(url: str) -> bytes:
    for k in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
                return r.read()
        except Exception:  # noqa: BLE001
            if k == 4:
                raise
            time.sleep(2 ** (k + 1))
    return b""


def arcgis_all(layer: str, fields: str, page: int = 2000, envelope: str = "", where: str = "1=1") -> tuple[list, str]:
    feats, off, first = [], 0, None
    while True:
        p = dict(where=where, outFields=fields, returnGeometry="true", outSR=4326, f="geojson",
                 resultOffset=off, resultRecordCount=page, orderByFields="OBJECTID")
        if envelope:   # xmin,ymin,xmax,ymax in WGS84
            p.update(geometry=envelope, geometryType="esriGeometryEnvelope", inSR=4326, spatialRel="esriSpatialRelIntersects")
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


LICENCE = {"denver": "City and County of Denver Open Data (data.denvergov.org), Creative Commons Attribution 3.0",
           "portland": "City of Portland, PortlandMaps open data (licence as stated on the service)"}
PDX = "https://www.portlandmaps.com/arcgis/rest/services/Public"
PORTLAND = {
    "bhd_zone_changes": (f"{PDX}/BPS_Planning_Projects/MapServer/10", "OBJECTID,ex_zone,pr_zone,proposal,proposal_draft",
                         "proposal='bhd' AND proposal_draft='adopted'"),
    "max_stops": (f"{PDX}/Transit/MapServer/2", "*", "1=1"),
    "streetcar_stops": (f"{PDX}/Transit/MapServer/3", "*", "1=1"),
    "residential_permits": (f"{PDX}/BDS_Permit/MapServer/5", "OBJECTID,ISSUED,YEAR,NUMNEWUNITS,TYPE,WORK_DESCRIPTION,STATUS,PROPERTYKEY",
                            "NUMNEWUNITS > 0"),
    "commercial_permits": (f"{PDX}/BDS_Permit/MapServer/2", "OBJECTID,ISSUED,YEAR,NUMNEWUNITS,TYPE,WORK_DESCRIPTION,STATUS,PROPERTYKEY",
                           "NUMNEWUNITS > 0"),
    "taxlots": (f"{PDX}/Taxlots/MapServer/0", "OBJECTID,STATE_ID,RNO", "1=1"),
    # the city's zoning archive: whole-city zoning maps for each period
    "zoning_pre_2018_05_24": (f"{PDX}/PPD_Zoning_Archive/MapServer/91", "OBJECTID,ZONE,OVRLY,PLDIST", "1=1"),
    "zoning_2018_05_25": (f"{PDX}/PPD_Zoning_Archive/MapServer/3", "OBJECTID,ZONE,OVRLY,PLDIST", "1=1"),
    "zoning_2018_08_21_to_2020_02_29": (f"{PDX}/PPD_Zoning_Archive/MapServer/194", "OBJECTID,ZONE,OVRLY,PLDIST", "1=1"),
    "zoning_2020_03_01": (f"{PDX}/PPD_Zoning_Archive/MapServer/178", "OBJECTID,ZONE,OVRLY,PLDIST", "1=1"),
}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", required=True, choices=["denver", "portland"])
    ap.add_argument("--only", default="")
    a = ap.parse_args(argv)
    d = RAW / "tod_new_cities" / a.city
    d.mkdir(parents=True, exist_ok=True)
    mp = d / "manifest.json"
    m = json.loads(mp.read_text()) if mp.exists() else {"source_id": f"tod_new_cities_{a.city}", "files": {}}
    layers = DENVER if a.city == "denver" else PORTLAND
    for name, spec in layers.items():
        if a.only and name not in a.only.split(","):
            continue
        print(name, flush=True)
        layer, fields = spec[0], spec[1]
        where = spec[2] if len(spec) > 2 else "1=1"
        env = PARCEL_ENVELOPE if (a.city == "denver" and name == "parcels") else (
            "-122.84,45.43,-122.47,45.66" if (a.city == "portland" and name == "taxlots") else "")   # Portland city extent
        f, url = arcgis_all(layer, fields, envelope=env, where=where)
        data = json.dumps({"type": "FeatureCollection", "features": f}).encode()
        (d / f"{name}.geojson").write_bytes(data)
        m["files"][f"{name}.geojson"] = {"url": url, "accessed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                         "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                                         "licence": LICENCE[a.city]}
        mp.write_text(json.dumps(m, indent=1) + "\n")
        print(f"  {name}: {len(f):,} features", flush=True)


if __name__ == "__main__":
    main()
