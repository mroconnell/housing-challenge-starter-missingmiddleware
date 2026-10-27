"""Download CTA "L" daily station entries (2009-2019) and the "L" stops list into data/raw/cta_ridership/.

    uv run python scripts/fetch_cta_ridership.py [--refresh]

Plan: docs/tod/CHICAGO_RIDERSHIP_PREREG.md. Raw (git-ignored): data/raw/cta_ridership/
- l_station_entries_daily_2009_2019.csv: City of Chicago data portal, "CTA - Ridership - 'L' Station Entries -
  Daily Totals" (5neh-572f): station_id, stationname, date, daytype (W weekday, A Saturday, U Sunday or holiday),
  rides (entries). Counts by station and day only; no personal data.
- l_stops.csv: "CTA - System Information - List of 'L' Stops" (8pix-ypme): one row per platform direction, with
  map_id (= station_id above), line flags and location.
- manifest.json: URL, access time, bytes, SHA-256, row counts, licence/terms.

Terms: City of Chicago data portal terms of use (https://www.chicago.gov/city/en/narr/foia/data_disclaimer.html):
free use, provided as is, no warranty; attribution "Chicago Transit Authority". The portal's licence field for
5neh-572f reads "See Terms of Use".

Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW  # noqa: E402
from scripts.fetch_tod_cases import Manifest, http_get  # noqa: E402

D = RAW / "cta_ridership"
PORTAL = "https://data.cityofchicago.org/resource"
TERMS = ("City of Chicago data portal terms of use (free use, provided as is, no warranty; "
         "https://www.chicago.gov/city/en/narr/foia/data_disclaimer.html); portal licence field 'See Terms of Use'; "
         "attribution Chicago Transit Authority")
PAGE = 50_000


def soda_csv(dataset: str, params: dict) -> tuple[bytes, str, int]:
    """All rows of a SODA query as one CSV (paged). Returns (bytes, first URL, rows)."""
    out, header, off, first, n = io.StringIO(), None, 0, None, 0
    w = csv.writer(out, lineterminator="\n")
    while True:
        p = dict(params, **{"$limit": PAGE, "$offset": off})
        url = f"{PORTAL}/{dataset}.csv?" + urllib.parse.urlencode(p)
        first = first or url
        rows = list(csv.reader(io.StringIO(http_get(url, timeout=600).decode("utf-8"))))
        if header is None:
            header = rows[0]
            w.writerow(header)
        body = rows[1:]
        w.writerows(body)
        n += len(body)
        if len(body) < PAGE:
            break
        off += PAGE
    return out.getvalue().encode("utf-8"), first, n


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)
    man = Manifest(D, "cta_ridership", "Chicago Transit Authority, via the City of Chicago data portal")
    name = "l_station_entries_daily_2009_2019.csv"
    if man.have(name, a.refresh):
        print(f"  {name}: kept")
    else:
        data, url, n = soda_csv("5neh-572f", {
            "$select": "station_id,stationname,date,daytype,rides",
            "$where": "date between '2009-01-01T00:00:00' and '2019-12-31T23:59:59'",
            "$order": "station_id,date"})
        man.record(name, data, url, licence=TERMS, rows=n,
                   note="CTA - Ridership - 'L' Station Entries - Daily Totals (5neh-572f), 2009-2019; "
                        "first page URL shown, later pages add $offset")
    name = "l_stops.csv"
    if man.have(name, a.refresh):
        print(f"  {name}: kept")
    else:
        data, url, n = soda_csv("8pix-ypme", {"$select": "stop_id,direction_id,stop_name,station_name,"
                                              "station_descriptive_name,map_id,red,blue,g,brn,p,y,pnk,o,location",
                                              "$order": "stop_id"})
        man.record(name, data, url, licence=TERMS, rows=n,
                   note="CTA - System Information - List of 'L' Stops (8pix-ypme); location as a point")


if __name__ == "__main__":
    main()
