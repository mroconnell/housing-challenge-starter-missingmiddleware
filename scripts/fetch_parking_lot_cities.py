"""Download permits and parcels for the five-city parking lot test (docs/parking/LOT_CITIES_PLAN.md).

    uv run python scripts/fetch_parking_lot_cities.py [--refresh]

Raw (git-ignored): data/raw/parking_lot_cities/
- sf_permits.json: DataSF Building Permits (i98e-djp9), permits adding units, issued 2013 on (PDDL-1.0).
- sf_parcels.geojson: DataSF Parcels - Active and Retired (acdm-wktn), active parcels (PDDL-1.0).
- buffalo_permits.json: OpenData Buffalo Permits (9p2d-f3yt), permits adding or removing units (public domain).
- buffalo_roll.json: OpenData Buffalo 2025 Final Assessment Roll (mn64-uxt6) (public domain).
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
from scripts.fetch_tod_cases import Manifest  # noqa: E402

D = RAW / "parking_lot_cities"
PDDL, PD = "PDDL-1.0 (City and County of San Francisco)", "Public domain (City of Buffalo)"


def socrata(base: str, params: dict, page: int = 50000) -> tuple[list, str]:
    out, off, first = [], 0, None
    while True:
        q = urllib.parse.urlencode({**params, "$limit": page, "$offset": off, "$order": ":id"})
        url = f"{base}?{q}"
        first = first or url
        with urllib.request.urlopen(url, timeout=600) as r:
            rows = json.load(r)
        rows = rows["features"] if isinstance(rows, dict) else rows
        out += rows
        off += len(rows)
        print(base.rsplit("/", 1)[-1], off, flush=True)
        if len(rows) < page:
            break
    return out, first


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)
    man = Manifest(D, "parking_lot_cities", "City and County of San Francisco; City of Buffalo")
    if not man.have("sf_permits.json", a.refresh):
        rows, u = socrata("https://data.sf.gov/resource/i98e-djp9.json",
                          {"$select": "permit_number,permit_type,block,lot,issued_date,existing_units,proposed_units,status,location",
                           "$where": "issued_date >= '2013-01-01' AND ((permit_type in ('1','2') AND proposed_units::number > 0) OR "
                                     "(permit_type = '6' AND existing_units::number > 0) OR "
                                     "(permit_type in ('3','8') AND proposed_units::number <> existing_units::number))"})
        man.record("sf_permits.json", json.dumps(rows).encode(), u, licence=PDDL)
    if not man.have("sf_parcels.geojson", a.refresh):
        rows, u = socrata("https://data.sf.gov/resource/acdm-wktn.geojson",
                          {"$select": "blklot,zoning_code,zoning_district,centroid_latitude,centroid_longitude,shape", "$where": "active = true"})
        man.record("sf_parcels.geojson", json.dumps({"type": "FeatureCollection", "features": rows}).encode(), u, licence=PDDL)
    if not man.have("buffalo_permits.json", a.refresh):
        rows, u = socrata("https://data.buffalony.gov/resource/9p2d-f3yt.json",
                          {"$select": "apno,aptype,issued,sbl,units_added,units_lost,latitude,longitude",
                           "$where": "units_added > 0 OR units_lost > 0"})
        man.record("buffalo_permits.json", json.dumps(rows).encode(), u, licence=PD)
    if not man.have("buffalo_roll.json", a.refresh):
        rows, u = socrata("https://data.buffalony.gov/resource/mn64-uxt6.json",
                          {"$select": "sbl,front,depth,acres,property_class_code,previous_property_class,number_of_units,year_built,latitude,longitude"})
        man.record("buffalo_roll.json", json.dumps(rows).encode(), u, licence=PD)


if __name__ == "__main__":
    main()
