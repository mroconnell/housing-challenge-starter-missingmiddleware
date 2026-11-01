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

UA = {"User-Agent": "missing-middleware research (TOD lot model, new reform cities)"}
DEN = "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/ArcGIS/rest/services"
DENVER = {
    "zone_map_amendments": (f"{DEN}/ODC_ZONE_MAPAMENDMENTS_A/FeatureServer/356", "*"),
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


def arcgis_all(layer: str, fields: str, page: int = 2000) -> tuple[list, str]:
    feats, off, first = [], 0, None
    while True:
        p = dict(where="1=1", outFields=fields, returnGeometry="true", outSR=4326, f="geojson",
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


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", required=True, choices=["denver"])
    ap.add_argument("--only", default="")
    a = ap.parse_args(argv)
    d = RAW / "tod_new_cities" / a.city
    d.mkdir(parents=True, exist_ok=True)
    mp = d / "manifest.json"
    m = json.loads(mp.read_text()) if mp.exists() else {"source_id": f"tod_new_cities_{a.city}", "files": {}}
    for name, (layer, fields) in DENVER.items():
        if a.only and name not in a.only.split(","):
            continue
        print(name, flush=True)
        f, url = arcgis_all(layer, fields)
        data = json.dumps({"type": "FeatureCollection", "features": f}).encode()
        (d / f"{name}.geojson").write_bytes(data)
        m["files"][f"{name}.geojson"] = {"url": url, "accessed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                         "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                                         "licence": "City and County of Denver Open Data (data.denvergov.org), Creative Commons Attribution 3.0"}
        mp.write_text(json.dumps(m, indent=1) + "\n")
        print(f"  {name}: {len(f):,} features", flush=True)


if __name__ == "__main__":
    main()
