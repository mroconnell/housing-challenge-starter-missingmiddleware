"""Historic lot values for the land-value step (docs/tod/LAND_VALUE_PLAN.md). Public downloads only.

    uv run --all-extras python scripts/fetch_tod_land_values.py [--only king,philly,wi,la,nyc]

Writes data/raw/tod_land_values/ (never committed), with a manifest of URLs, dates, sizes and hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from missing_middleware.paths import RAW  # noqa: E402

DIR = RAW / "tod_land_values"
BIG = {
    "king": ("king_value_history.zip", "https://aqua.kingcounty.gov/extranet/assessor/Value%20History.zip",
             "King County Assessor; public records (RCW 42.56.070(9): no commercial use of lists of people)"),
    "philly": ("philadelphia_assessments.csv", "https://opendata-downloads.s3.amazonaws.com/assessments.csv",
               "City of Philadelphia open data licence, as is"),
    "wi": ("wi_parcels_v9_2023.zip", "https://web.s3.wisc.edu/parcels/v9_parcels/V9.0.1_Wisconsin_Parcels_2023_10.3_Compressed.zip",
           "Wisconsin Statewide Parcel Map Initiative, free with citation"),
    "wi_latest": ("wi_parcels_v12_2026.zip", "https://web.s3.wisc.edu/parcels/v12_parcels/V12.0.0_Wisconsin_Parcels_2026_10.3_Compressed.zip",
                  "Wisconsin Statewide Parcel Map Initiative, free with citation"),
}
PHL_POINTS = ("philadelphia_opa_points.csv",
              "https://phl.carto.com/api/v2/sql?format=csv&q=" + urllib.parse.quote(
                  "SELECT parcel_number, ST_Y(the_geom) AS lat, ST_X(the_geom) AS lon FROM opa_properties_public"),
              "City of Philadelphia open data licence, as is")
LA_TABLE = "https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Parcel_Data_2011_2015_Table/FeatureServer/0"
LA_BOXES = {"warner_center": (-118.63, 34.15, -118.54, 34.21), "cornfield": (-118.26, 34.04, -118.19, 34.10)}


def manifest() -> dict:
    p = DIR / "manifest.json"
    return json.loads(p.read_text()) if p.exists() else {"source_id": "tod_land_values", "files": {}}


def record(m: dict, name: str, url: str, licence: str) -> None:
    f = DIR / name
    h = hashlib.sha256()
    with open(f, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    m["files"][name] = {"url": url, "accessed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "bytes": f.stat().st_size, "sha256": h.hexdigest(), "licence": licence}
    (DIR / "manifest.json").write_text(json.dumps(m, indent=1) + "\n")
    print(f"  {name}: {f.stat().st_size:,} bytes", flush=True)


def big(m: dict, key: str) -> None:
    name, url, lic = BIG[key]
    if name in m["files"] and (DIR / name).exists():
        print(f"  {name}: kept", flush=True)
        return
    subprocess.run(["curl", "-sSfL", "--retry", "4", "-o", str(DIR / name), url], check=True)
    record(m, name, url, lic)


def la(m: dict) -> None:
    from scripts.fetch_tod_cases import http_get
    for k, (x0, y0, x1, y1) in LA_BOXES.items():
        name = f"la_roll2012_{k}.json"
        if name in m["files"] and (DIR / name).exists():
            continue
        where = (f"RollYear='2012' AND CENTER_LAT BETWEEN {y0} AND {y1} AND CENTER_LON BETWEEN {x0} AND {x1}")
        rows, off, first = [], 0, None
        while True:
            p = dict(where=where, outFields="AIN,RollYear,Roll_LandValue,Roll_ImpValue,Roll_TotalValue,CENTER_LAT,CENTER_LON,UseType",
                     returnGeometry="false", f="json", resultOffset=off, resultRecordCount=2000)
            url = f"{LA_TABLE}/query?" + urllib.parse.urlencode(p)
            first = first or url
            d = json.loads(http_get(url, timeout=300))
            if "error" in d:
                raise RuntimeError(d["error"])
            f = [x["attributes"] for x in d.get("features", [])]
            rows += f
            if len(f) < 2000:
                break
            off += 2000
        (DIR / name).write_text(json.dumps(rows))
        record(m, name, first, "Los Angeles County Assessor, informational purposes")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="king,philly,wi,wi_latest,la")
    a = ap.parse_args(argv)
    DIR.mkdir(parents=True, exist_ok=True)
    m = manifest()
    for k in a.only.split(","):
        print(k, flush=True)
        if k == "la":
            la(m)
        elif k == "philly_points":
            name, url, lic = PHL_POINTS
            subprocess.run(["curl", "-sSfL", "--retry", "4", "-o", str(DIR / name), url], check=True)
            record(m, name, url, lic)
        else:
            big(m, k)


if __name__ == "__main__":
    main()
