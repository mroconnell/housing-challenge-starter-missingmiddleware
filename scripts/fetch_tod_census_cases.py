"""Download census blocks (2010, 2020) and upzoned-area boundaries for the census-count cases.

    uv run python scripts/fetch_tod_census_cases.py [--refresh]

Plan: docs/tod/CENSUS_CASES_PLAN.md. Raw (git-ignored): data/raw/tod_census_cases/
- tabblock2010_<st>_pophu.zip, tl_2020_<st>_tabblock20.zip: Census blocks with housing counts (public domain).
- boundary_<case>.geojson: official city or county layers (sources below); boundaries only, no personal data.
Phoenix and Bellevue boundaries come from the existing case folders (data/raw/tod_cases/).
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

D = RAW / "tod_census_cases"
STATES = ["34", "06", "04", "51", "48", "53", "39", "36", "17", "27", "37", "42"]
PD = "US Census Bureau, public domain"
BOUNDARIES = {
    "jersey_city_journal_square_2010": ("https://services2.arcgis.com/UXbywc7dSkfgdPp4/arcgis/rest/services/Zoning_Districts/FeatureServer/0",
                                        "ZONE='Journal Square 2060'", "City of Jersey City zoning layer (public web map; no licence stated)"),
    "milpitas_tasp_2008": ("https://services8.arcgis.com/OPmRdssd8jj0bT5H/arcgis/rest/services/TASP/FeatureServer/0", "1=1",
                           "City of Milpitas TASP layer (public; no licence stated)"),
    "austin_tod_station_plans": ("https://services.arcgis.com/0L95CJ0VTaxqcmED/arcgis/rest/services/PLANNINGCADASTRE_transit_oriented_development/FeatureServer/0",
                                 "1=1", "City of Austin open data (public domain dedication per City policy; verify)"),
    "tysons_2010": ("https://services1.arcgis.com/ioennV6PpG5Xodq0/arcgis/rest/services/Tysons_Urban_Center_Boundary/FeatureServer/49",
                    "1=1", "Fairfax County GIS (public; no licence stated)"),
}
# Cincinnati's zoning layer is a link-only asset on its portal and could not be downloaded (plan section 8, item 2).


def arcgis_geojson(url: str, where: str) -> tuple[bytes, str]:
    feats, off, first = [], 0, None
    while True:
        q = urllib.parse.urlencode(dict(where=where, outFields="*", outSR=4326, f="geojson", resultOffset=off,
                                        resultRecordCount=1000))
        first = first or f"{url}/query?{q}"
        with urllib.request.urlopen(f"{url}/query?{q}", timeout=300) as r:
            f = json.load(r).get("features", [])
        feats += f
        off += len(f)
        if len(f) < 1000:
            break
    return json.dumps({"type": "FeatureCollection", "features": feats}).encode(), first


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)
    man = Manifest(D, "tod_census_cases", "US Census Bureau; city and county GIS offices")
    for st in STATES:
        download_file(man, f"tabblock2010_{st}_pophu.zip",
                      f"https://www2.census.gov/geo/tiger/TIGER2010BLKPOPHU/tabblock2010_{st}_pophu.zip", a.refresh, PD)
        download_file(man, f"tl_2020_{st}_tabblock20.zip",
                      f"https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_{st}_tabblock20.zip", a.refresh, PD)
    for case, (url, where, lic) in BOUNDARIES.items():
        name = f"boundary_{case}.geojson"
        if not man.have(name, a.refresh):
            data, first = arcgis_geojson(url, where)
            man.record(name, data, first, licence=lic)


if __name__ == "__main__":
    main()
