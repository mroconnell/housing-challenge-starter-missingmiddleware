"""Download Census permit counts for every US place (2000-2025) and 2010 home counts into data/raw/tod_control_cities/.

    uv run python scripts/fetch_tod_control_cities.py [--refresh]

Plan: docs/tod/CONTROL_CITIES_PLAN.md. Raw (git-ignored): data/raw/tod_control_cities/
- bps/<region><year>a.txt: Census Building Permits Survey annual place files, four regions, 2000-2025.
- Gaz_places_national.zip: 2010 Census Gazetteer place file (HU10 = 2010 housing units).
- Gaz_counties_national.zip: 2010 Census Gazetteer county file (Mecklenburg County's HU10).
- manifest.json: URL, access time, bytes, SHA-256, licence.

Both sources are US Census Bureau products in the public domain. Standard library only.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW  # noqa: E402
from scripts.fetch_tod_cases import Manifest, download_file  # noqa: E402

D = RAW / "tod_control_cities"
BPS = "https://www2.census.gov/econ/bps/Place"
REGIONS = {"mw": "Midwest%20Region", "ne": "Northeast%20Region", "so": "South%20Region", "we": "West%20Region"}
YEARS = range(2000, 2026)
GAZ = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/Gaz_places_national.zip"
GAZ_CO = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/Gaz_counties_national.zip"
LICENCE = "US Census Bureau, public domain (17 U.S.C. 105)"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)
    man = Manifest(D, "tod_control_cities", "US Census Bureau")
    for y in YEARS:
        for code, folder in REGIONS.items():
            download_file(man, f"bps/{code}{y}a.txt", f"{BPS}/{folder}/{code}{y}a.txt", a.refresh, LICENCE)
    download_file(man, "Gaz_places_national.zip", GAZ, a.refresh, LICENCE, note="2010 Gazetteer places; HU10 column")
    download_file(man, "Gaz_counties_national.zip", GAZ_CO, a.refresh, LICENCE,
                  note="2010 Gazetteer counties; HU10 for Mecklenburg County (Charlotte's permit office)")


if __name__ == "__main__":
    main()
