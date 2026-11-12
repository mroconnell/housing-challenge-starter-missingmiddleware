"""Test 57 (CAUSAL_FRAMEWORK_PLAN.md, Test 57 LOCK): fetch the remaining raw files for the code step.

    uv run python scripts/fetch_parking_t57_outcomes.py [--refresh] [--only NAME ...]

FETCH ONLY: nothing is counted by area or by time. Each file's whole-file row total is printed, nothing else.
Raw (git-ignored), all in data/raw/parking_t57/, recorded in data/raw/parking_t57/manifest.json (URL, access time,
bytes, sha256, licence). Requests carry this project's own user agent; a refused request is reported, never worked
around.

New York (NYC Open Data; licence field blank on the datasets, so the NYC Open Data terms of use are recorded):
  - dobnow_nb.json: DOB NOW: Build - Job Application Filings (w9ak-ipjd), every filing whose job_type is
    'New Building' or 'ALT-CO - New Building with Existing Elements to Remain' (ALT-CO is fetched so its exclusion is
    visible; the build step drops it, as the lock says). Fields: job and filing ids, filing status, borough, block,
    lot, BIN, BBL, job type, building type, existing and proposed dwelling units, filing date, latitude, longitude.
    No owner, applicant or filing-representative field is requested.
  - hpd_affordable_by_building.json: HPD Affordable Housing Production by Building (hg8x-zxpr), all rows, all fields
    (no personal fields in the dataset).
  - mih_areas.geojson: Mandatory Inclusionary Housing areas (m79g-k9r4), with adoption dates (date_adopte). Needed
    for the lock's MIH rule (MIH-mapped lots dropped from both arms from each area's adoption date).
San Francisco (DataSF):
  - sf_zoning_2009.geojson: Historic Zoning Districts - 2009 (jud5-ja46). The lock names it as PDDL; the dataset's
    own licence field is blank, so the record says "PDDL-1.0 per DataSF portal default; dataset licence field blank".
  - sf_sud.geojson: Zoning Map - Special Use Districts (5yf5-ms5f), licence field "Public Domain U.S. Government".
    Needed to leave out the Telegraph Hill-North Beach Residential, North of Market, Washington-Broadway, Bernal
    Heights and Visitacion Valley/Schlage SUD lots named in the feasibility check and the rules block.
  - sf_planning_areas_datasf.geojson: DataSF "Planning Areas" (bkzf-eahq), licence field "Public Domain U.S.
    Government". The DataSF copy of the plan-area layer (the feasibility step found only the SF Planning ArcGIS copy,
    which has no stated licence and is not used). Used only as a mask: Eastern Neighborhoods RH/RM lots out of both
    arms, and Market-Octavia / Eastern Neighborhoods lots out of the controls. Never used to set treatment.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW  # noqa: E402
from scripts.fetch_tod_cases import Manifest  # noqa: E402

D = RAW / "parking_t57"
UA = {"User-Agent": "missing-middleware research (housing policy model; parking Test 57)"}
NYC_TERMS = "NYC Open Data terms of use (https://www.nyc.gov/main/terms-of-use); dataset licence field blank"
PDDL_DEFAULT = "PDDL-1.0 per DataSF portal default (lock text); dataset licence field blank"
USGOV = "Public Domain U.S. Government (DataSF dataset licence field)"
DOBNOW_FIELDS = ("job_filing_number,filing_status,borough,block,lot,bin,bbl,job_type,building_type,"
                 "existing_dwelling_units,proposed_dwelling_units,filing_date,approved_date,first_permit_date,"
                 "latitude,longitude")
NB, ALTCO = "New Building", "ALT-CO - New Building with Existing Elements to Remain"

FILES = {
    "dobnow_nb.json": dict(
        base="https://data.cityofnewyork.us/resource/w9ak-ipjd.json",
        params={"$select": DOBNOW_FIELDS, "$where": f"job_type in ('{NB}', '{ALTCO}')"},
        licence=NYC_TERMS, publisher="NYC Department of Buildings",
        note="DOB NOW: Build - Job Application Filings (w9ak-ipjd); New Building and ALT-CO new-building filings, all "
             "filing numbers (initial -I1 and later); no owner/applicant fields"),
    "hpd_affordable_by_building.json": dict(
        base="https://data.cityofnewyork.us/resource/hg8x-zxpr.json", params={},
        licence=NYC_TERMS, publisher="NYC Department of Housing Preservation and Development",
        note="Affordable Housing Production by Building (hg8x-zxpr), all rows and fields"),
    "mih_areas.geojson": dict(
        base="https://data.cityofnewyork.us/resource/m79g-k9r4.geojson", params={}, geojson=True,
        licence=NYC_TERMS, publisher="NYC Department of City Planning",
        note="Mandatory Inclusionary Housing areas (m79g-k9r4) with adoption dates"),
    "sf_zoning_2009.geojson": dict(
        base="https://data.sf.gov/resource/jud5-ja46.geojson", params={}, geojson=True,
        licence=PDDL_DEFAULT, publisher="City and County of San Francisco (Planning)",
        note="Historic Zoning Districts - 2009 (jud5-ja46)"),
    "sf_sud.geojson": dict(
        base="https://data.sf.gov/resource/5yf5-ms5f.geojson", params={}, geojson=True,
        licence=USGOV, publisher="City and County of San Francisco (Planning)",
        note="Zoning Map - Special Use Districts (5yf5-ms5f), current"),
    "sf_planning_areas_datasf.geojson": dict(
        base="https://data.sf.gov/resource/bkzf-eahq.geojson", params={}, geojson=True,
        licence=USGOV, publisher="City and County of San Francisco (Planning)",
        note="Planning Areas (bkzf-eahq), current; mask only"),
}


def socrata(base: str, params: dict, page: int = 50000) -> tuple[list, str]:
    """All rows (or GeoJSON features) of a Socrata query, paged in a stable order. Returns (rows, first URL)."""
    out, off, first = [], 0, None
    while True:
        url = f"{base}?{urllib.parse.urlencode({**params, '$limit': page, '$offset': off, '$order': ':id'})}"
        first = first or url
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=900) as r:
                rows = json.load(r)
        except urllib.error.HTTPError as e:  # blocked or refused: report and stop, never work around
            raise SystemExit(f"REFUSED {e.code} {base}: {e.reason}. Not worked around.")
        rows = rows["features"] if isinstance(rows, dict) else rows
        out += rows
        off += len(rows)
        if len(rows) < page:
            break
    return out, first


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--only", nargs="*", default=None, choices=list(FILES))
    a = ap.parse_args(argv)
    man = Manifest(D, "parking_t57", "City and County of San Francisco; City of New York (DCP, DOB, HPD)")
    for name, spec in FILES.items():
        if a.only and name not in a.only:
            continue
        if man.have(name, a.refresh):
            print(f"{name}: kept")
            continue
        rows, url = socrata(spec["base"], spec["params"])
        body = {"type": "FeatureCollection", "features": rows} if spec.get("geojson") else rows
        man.record(name, json.dumps(body).encode(), url, licence=spec["licence"], publisher=spec["publisher"],
                   note=spec["note"], rows=len(rows))
        print(f"{name}: whole-file rows = {len(rows):,}")


if __name__ == "__main__":
    main()
