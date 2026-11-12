"""Test 57: fetch San Francisco unit-adding permits issued 2003 onward (wave A needs before-years).

    uv run python scripts/fetch_parking_t57_sf.py [--refresh]

Raw (git-ignored): data/raw/parking_t57/sf_permits_2003.json
Source: DataSF Building Permits (i98e-djp9), PDDL-1.0. Same filter as fetch_parking_lot_cities.py,
plus filed_date, with the start date moved from 2013 to 2003. Fetch only: reads no counts.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW  # noqa: E402
from scripts.fetch_parking_lot_cities import PDDL, socrata  # noqa: E402
from scripts.fetch_tod_cases import Manifest  # noqa: E402

D = RAW / "parking_t57"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)
    man = Manifest(D, "parking_t57", "City and County of San Francisco")
    if not man.have("sf_permits_2003.json", a.refresh):
        rows, u = socrata("https://data.sf.gov/resource/i98e-djp9.json",
                          {"$select": "permit_number,permit_type,block,lot,filed_date,issued_date,existing_units,"
                                      "proposed_units,status,location",
                           "$where": "issued_date >= '2003-01-01' AND ((permit_type in ('1','2') AND proposed_units::number > 0) OR "
                                     "(permit_type = '6' AND existing_units::number > 0) OR "
                                     "(permit_type in ('3','8') AND proposed_units::number <> existing_units::number))"})
        man.record("sf_permits_2003.json", json.dumps(rows).encode(), u, licence=PDDL)
        print(f"rows={len(rows)}")


if __name__ == "__main__":
    main()
