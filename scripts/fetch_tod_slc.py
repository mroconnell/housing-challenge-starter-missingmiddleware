"""Download Utah census blocks (2010, 2020), Utah Transit Authority stops and a 2020 Salt Lake City zoning map.

    uv run python scripts/fetch_tod_slc.py [--refresh]

Plan: docs/tod/SLC_CENSUS_PLAN.md. Raw (git-ignored): data/raw/tod_slc/
- tabblock2010_49_pophu.zip: Census 2010 blocks with HOUSING10 (public domain).
- tl_2020_49_tabblock20.zip: Census 2020 blocks with HOUSING20 (public domain).
- uta_stops.json: National Transit Map stops for the Utah Transit Authority (NTD 80001), US DOT BTS (public domain).
- slc_zoning_2020_jacobs.geojson: Salt Lake City zoning districts, 2020 snapshot hosted on ArcGIS Online by a
  consultant (Jacobs); public layer, no licence stated. Used only to locate TSA land; only derived counts are committed.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW  # noqa: E402
from scripts.fetch_tod_cases import Manifest, download_file  # noqa: E402
from scripts.fetch_tod_transit import NTM_LAYERS, ntm_query  # noqa: E402

D = RAW / "tod_slc"
PD = "US Census Bureau / US DOT, public domain"
ZONING = "https://services9.arcgis.com/eNX73FDxjlKFtCtH/arcgis/rest/services/SaltLakeCity_Zoning/FeatureServer/0/query"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)
    man = Manifest(D, "tod_slc", "US Census Bureau; US DOT BTS; Salt Lake City (via Jacobs ArcGIS Online)")
    download_file(man, "tabblock2010_49_pophu.zip",
                  "https://www2.census.gov/geo/tiger/TIGER2010BLKPOPHU/tabblock2010_49_pophu.zip", a.refresh, PD)
    download_file(man, "tl_2020_49_tabblock20.zip",
                  "https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_49_tabblock20.zip", a.refresh, PD)
    if not man.have("uta_stops.json", a.refresh):
        stops, urls = ntm_query(NTM_LAYERS["stops"], "ntd_id='80001'")
        man.record("uta_stops.json", json.dumps([s["attributes"] for s in stops]).encode(), urls[0], licence=PD)
    if not man.have("slc_zoning_2020_jacobs.geojson", a.refresh):
        feats, off, first = [], 0, None
        while True:
            q = urllib.parse.urlencode(dict(where="1=1", outFields="ZONING", outSR=4326, f="geojson", resultOffset=off,
                                            resultRecordCount=1000, orderByFields="OBJECTID"))
            first = first or f"{ZONING}?{q}"
            with urllib.request.urlopen(f"{ZONING}?{q}", timeout=180) as r:
                f = json.load(r)["features"]
            feats += f
            off += len(f)
            if len(f) < 1000:
                break
        man.record("slc_zoning_2020_jacobs.geojson", json.dumps({"type": "FeatureCollection", "features": feats}).encode(),
                   first, licence="public ArcGIS Online layer, no licence stated (owner: Jacobs); derived counts only")


if __name__ == "__main__":
    main()
