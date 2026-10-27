"""Download the inputs for the California AB 2097 test (docs/tod/AB2097_TEST_PREREG.md) into data/raw/ab2097/.

    uv run python scripts/fetch_ab2097_inputs.py [--refresh]

Raw (git-ignored): data/raw/ab2097/... and data/raw/ab2097/manifest.json (URL, access time, bytes, SHA-256,
licence, feature counts, version notes). Existing files are kept unless --refresh.

Files:
- major_transit_stops.geojson: State of California (Caltrans) "High Quality Transit Stops" layer
  (CHrailroad/CA_HQ_Transit_Stops, ArcGIS item 856421337c4c489e8ea7a17e05a464c5), the features whose hqta_type
  starts with "major_stop" (rail, bus rapid transit, ferry and bus major transit stops, existing and planned).
  No pre-2023 version of this layer can be fetched (the service keeps only the current version and no archive copy
  was found), so the current version is used and the fact is recorded (prereg section 2).
- la_toc_tiers_2017.geojson: City of Los Angeles Department of City Planning "TOC_Tiers_Oct2017_new" (ArcGIS
  item 47618827cb57401a8cb5570df12b3605), the Transit Oriented Communities tier areas as of October 2017, the
  only citywide pre-2023 version openly published (a September 2021 layer covers Boyle Heights only).
- tl_2020_06_tabblock20.zip: Census 2020 tabulation blocks for California with HOUSING20 (2020 census housing units),
  ALAND20 and internal points.

The HCD Table A2 file (data/raw/hcd_apr_a2) and the 2024 California place outlines (data/raw/census_tiger_2024_ca_place)
are already fetched by other scripts.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.fetch_tod_cases import Manifest, download_file, http_get, save_layer  # noqa: E402
from missing_middleware.paths import RAW  # noqa: E402

D = RAW / "ab2097"
MTS_LAYER = "https://caltrans-gis.dot.ca.gov/arcgis/rest/services/CHrailroad/CA_HQ_Transit_Stops/MapServer/0"
MTS_ITEM = "https://caltrans-gis.dot.ca.gov/arcgis/rest/services/CHrailroad/CA_HQ_Transit_Stops/MapServer/info/iteminfo?f=json"
TOC_LAYER = "https://services1.arcgis.com/tzwalEyxl2rpamKs/arcgis/rest/services/TOC_Tiers_Oct2017_new/FeatureServer/0"
TOC_ITEM = "https://www.arcgis.com/sharing/rest/content/items/47618827cb57401a8cb5570df12b3605?f=json"
BLOCKS = "https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_06_tabblock20.zip"


def note(man: Manifest, name: str, version: str) -> None:
    man.m["files"][name]["version"] = version
    man.save()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    man = Manifest(D, "ab2097", "Caltrans; City of Los Angeles Department of City Planning; U.S. Census Bureau")
    print("Major transit stops (Caltrans)")
    save_layer(man, "major_transit_stops.geojson", MTS_LAYER, a.refresh, licence="Public (Caltrans item licence text)",
               where="hqta_type LIKE 'major_stop%'", out_fields="OBJECTID,agency_primary,hqta_type,stop_id,mpo,plan_name")
    note(man, "major_transit_stops.geojson", "current service version (no pre-2023 version fetchable); 20-minute bus headway definition (AB 2553)")
    if a.refresh or "major_transit_stops_iteminfo.json" not in man.m["files"]:
        man.record("major_transit_stops_iteminfo.json", http_get(MTS_ITEM), MTS_ITEM, licence="metadata")
    print("Los Angeles TOC tiers (October 2017)")
    save_layer(man, "la_toc_tiers_2017.geojson", TOC_LAYER, a.refresh, licence="City of Los Angeles open data (public item)")
    note(man, "la_toc_tiers_2017.geojson", "TOC_Tiers_Oct2017_new, published 2019-09-27 by LA City Planning; tiers as of October 2017")
    if a.refresh or "la_toc_tiers_2017_item.json" not in man.m["files"]:
        man.record("la_toc_tiers_2017_item.json", http_get(TOC_ITEM), TOC_ITEM, licence="metadata")
    print("Census 2020 blocks, California")
    download_file(man, "tl_2020_06_tabblock20.zip", BLOCKS, a.refresh, licence="Public domain (U.S. government work)",
                  vintage="Census 2020 tabulation blocks (TIGER/Line 2020); HOUSING20 = 2020 census housing units")


if __name__ == "__main__":
    main()
