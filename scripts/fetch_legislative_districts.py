"""Download the inputs for the legislative-district allocation (Gate 5) into data/raw/ (git-ignored).

1. Wisconsin State Assembly districts, 2024 plan (2023 Wisconsin Act 94), 99 polygons, and Senate districts
   (33 polygons), from the Legislative Technology Services Bureau's public ArcGIS FeatureServer layers, as
   GeoJSON in WGS84 (outSR=4326), paged 10 features per request. -> data/raw/wi_assembly_districts/ and
   data/raw/wi_senate_districts/
2. Census 2020 TIGER/Line tabulation blocks for Wisconsin (tl_2020_55_tabblock20.zip, about 290 MB), whose
   attribute table carries each block's 2020 housing-unit count (HOUSING20, PL 94-171) and internal point.
   -> data/raw/census_tiger_2020_tabblock/

Each folder gets a manifest.json with URL, access time, bytes, feature count and SHA-256. Existing files are
kept (delete them to refresh). Keyless public endpoints; standard library only.

Run: uv run python scripts/fetch_legislative_districts.py
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missing_middleware.paths import raw_dir  # noqa: E402

UA = "housing-challenge-missingmiddleware/0.1 (+https://github.com/mroconnell/housing-challenge-starter-missingmiddleware)"
LTSB = "https://services1.arcgis.com/FDsAtKBk8Hy4cAH0/arcgis/rest/services"
LAYERS = {
    "wi_assembly_districts": (f"{LTSB}/WI_Assembly_Districts_2024/FeatureServer/0", "assembly_2024.geojson", 99),
    "wi_senate_districts": (f"{LTSB}/WI_Senate_Districts_2024/FeatureServer/0", "senate_2024.geojson", 33),
}
BLOCKS_URL = "https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_55_tabblock20.zip"
LICENSE = {
    "wi_assembly_districts": "LTSB open data: 'open and publicly available ... use at your own risk'",
    "wi_senate_districts": "LTSB open data: 'open and publicly available ... use at your own risk'",
    "census_tiger_2020_tabblock": "Public domain (U.S. government work)",
}


def get(url: str, params: dict | None = None, timeout: int = 300) -> bytes:
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def write_manifest(folder: Path, source_id: str, entry: dict) -> None:
    (folder / "manifest.json").write_text(json.dumps({"source_id": source_id, "license": LICENSE[source_id],
                                                      "files": [entry]}, indent=2) + "\n")


def fetch_layer(source_id: str, url: str, fname: str, expected: int) -> None:
    folder = raw_dir(source_id)
    out = folder / fname
    if out.exists():
        print(f"{out} exists, kept")
        return
    info = json.loads(get(url, {"f": "json"}))
    feats, offset = [], 0
    while True:
        page = json.loads(get(url + "/query", {"where": "1=1", "outFields": "*", "outSR": 4326, "f": "geojson",
                                               "resultOffset": offset, "resultRecordCount": 10,
                                               "orderByFields": "FID"}))
        got = page.get("features", [])
        feats += got
        if len(got) < 10:
            break
        offset += 10
    if len(feats) != expected:
        raise SystemExit(f"{source_id}: {len(feats)} features, expected {expected}")
    data = json.dumps({"type": "FeatureCollection", "features": feats}).encode()
    out.write_bytes(data)
    edit = (info.get("editingInfo") or {}).get("lastEditDate")
    write_manifest(folder, source_id, {
        "file": fname, "url": url, "query": "where=1=1, outFields=*, outSR=4326, f=geojson, 10 per page",
        "features": len(feats), "layer_last_edit": dt.datetime.fromtimestamp(edit / 1000, dt.timezone.utc).date().isoformat() if edit else None,
        "accessed": now(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        "vintage": "2024 plan (2023 Wisconsin Act 94), in effect from the November 2024 elections"})
    print(f"{source_id}: {len(feats)} features, {len(data):,} bytes")


def fetch_blocks() -> None:
    folder = raw_dir("census_tiger_2020_tabblock")
    out = folder / Path(BLOCKS_URL).name
    if not out.exists():
        tmp = out.with_suffix(".part")
        req = urllib.request.Request(BLOCKS_URL, headers={"User-Agent": UA})
        h = hashlib.sha256()
        with urllib.request.urlopen(req, timeout=600) as r, open(tmp, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
                h.update(chunk)
        tmp.rename(out)
        write_manifest(folder, "census_tiger_2020_tabblock", {
            "file": out.name, "url": BLOCKS_URL, "accessed": now(), "bytes": out.stat().st_size,
            "sha256": h.hexdigest(), "vintage": "Census 2020 tabulation blocks (TIGER/Line 2020); HOUSING20 = 2020 "
                                               "census housing units (PL 94-171)"})
    print(f"{out}: {out.stat().st_size:,} bytes")


def main() -> None:
    for sid, (url, fname, n) in LAYERS.items():
        fetch_layer(sid, url, fname, n)
    fetch_blocks()


if __name__ == "__main__":
    main()
