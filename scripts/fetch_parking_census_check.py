"""Download census blocks (2010, 2020), 2020 place boundaries and 2009-2011 permit place files for the
census-count check (docs/parking/SALVAGE_PLAN.md, section 4).

    uv run python scripts/fetch_parking_census_check.py [--refresh]

Raw (git-ignored): data/raw/parking_census_check/. All US Census Bureau, public domain.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW  # noqa: E402
from scripts.fetch_tod_cases import Manifest, download_file  # noqa: E402

D = RAW / "parking_census_check"
PD = "US Census Bureau, public domain"
STATES = {"18": "mw", "27": "mw", "37": "so", "45": "so", "46": "mw", "42": "ne", "55": "mw"}
REGION_DIR = {"mw": "Midwest%20Region", "so": "South%20Region", "ne": "Northeast%20Region"}
BPS_YEARS = (2009, 2010, 2011)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)
    man = Manifest(D, "parking_census_check", "US Census Bureau")
    for st in STATES:
        download_file(man, f"tabblock2010_{st}_pophu.zip",
                      f"https://www2.census.gov/geo/tiger/TIGER2010BLKPOPHU/tabblock2010_{st}_pophu.zip", a.refresh, PD)
        download_file(man, f"tl_2020_{st}_tabblock20.zip",
                      f"https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_{st}_tabblock20.zip", a.refresh, PD)
        download_file(man, f"tl_2020_{st}_place.zip",
                      f"https://www2.census.gov/geo/tiger/TIGER2020/PLACE/tl_2020_{st}_place.zip", a.refresh, PD)
    for reg in sorted(set(STATES.values())):
        for y in BPS_YEARS:
            download_file(man, f"{reg}{y}a.txt", f"https://www2.census.gov/econ/bps/Place/{REGION_DIR[reg]}/{reg}{y}a.txt",
                          a.refresh, PD)


if __name__ == "__main__":
    main()
