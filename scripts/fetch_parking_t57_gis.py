"""Test 57 audit addendum 2: fetch the GIS layers for the boundary checks (fetch only; reads no outcomes).

    uv run python scripts/fetch_parking_t57_gis.py [--refresh]

Raw (git-ignored), all in data/raw/parking_t57/:
  - nyctransitzones_201601.zip: NYC DCP Transit Zones as adopted 2016 (Bytes of the Big Apple archive file). nyc.gov
    answers HTTP 403 to non-browser clients, so it is taken from the Internet Archive's public copy (Wayback, capture
    2025-12-22) with this project's own user agent. Not worked around.
  - nycd_16a.zip, nybb_16a.zip: DCP community districts and borough boundaries, release 16A (Wayback copies, same reason).
  - sf_zoning_districts.geojson: DataSF "Zoning Map - Zoning Districts" (3i4a-hu95), PDDL-1.0. Current layer.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW  # noqa: E402
from scripts.fetch_parking_lot_cities import PDDL, socrata  # noqa: E402
from scripts.fetch_tod_cases import Manifest, download_file  # noqa: E402

D = RAW / "parking_t57"
NYC = "NYC DCP Bytes of the Big Apple (NYC Open Data terms of use, https://www.nyc.gov/main/terms-of-use); via Internet Archive copy"
WB = "https://web.archive.org/web/{ts}id_/https://{host}/assets/planning/download/zip/data-maps/open-data/{f}"
FILES = {
    "nyctransitzones_201601.zip": ("20251222031139", "www.nyc.gov"),
    "nycd_16a.zip": ("20181130061047", "www1.nyc.gov"),
    "nybb_16a.zip": ("20181130061038", "www1.nyc.gov"),
}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)
    man = Manifest(D, "parking_t57", "City and County of San Francisco; City of New York (DCP)")
    for f, (ts, host) in FILES.items():
        download_file(man, f, WB.format(ts=ts, host=host, f=f), a.refresh, licence=NYC,
                      original_url=f"https://{host}/assets/planning/download/zip/data-maps/open-data/{f}")
    if not man.have("sf_zoning_districts.geojson", a.refresh):
        rows, u = socrata("https://data.sf.gov/resource/3i4a-hu95.geojson",
                          {"$select": "zoning_sim,zoning,districtna,gen,codesectio,the_geom"})
        man.record("sf_zoning_districts.geojson", json.dumps({"type": "FeatureCollection", "features": rows}).encode(),
                   u, licence=PDDL)


if __name__ == "__main__":
    main()
