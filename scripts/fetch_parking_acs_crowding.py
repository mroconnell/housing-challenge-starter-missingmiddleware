"""ACS 5-year crowding (B25014: occupants per room) for every place and county subdivision, releases ending 2013-2023
(Census Data API). Method 2 matching trait (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, item 3c): each case uses the latest
release ending before its event year (backtest pseudo-events reach back to 2009-2013).

    set -a; source .env; set +a      # CENSUS_API_KEY, never written to any file
    uv run python scripts/fetch_parking_acs_crowding.py

Output: data/raw/parking_acs_crowding/acs5_{year}_{level}.json, _downloads.json (URLs without the key);
reference/parking_acs_crowding.csv (acs_geoid, year = last year of the release, occupied, crowded, crowded_share)
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import os
import sys
import urllib.parse
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_parking_acs_history as h  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

YEARS = tuple(range(2013, 2024))
OUT = RAW / "parking_acs_crowding"
CROWD = ["B25014_005E", "B25014_006E", "B25014_007E", "B25014_011E", "B25014_012E", "B25014_013E"]  # 1.01+ per room


def main() -> None:
    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        raise SystemExit("CENSUS_API_KEY is not set (run: set -a; source .env; set +a)")
    OUT.mkdir(parents=True, exist_ok=True)
    cols = ",".join(["NAME", "B25014_001E"] + CROWD)
    jobs = []
    for y in YEARS:
        api = f"https://api.census.gov/data/{y}/acs/acs5"
        geos = [("place", "place:*", "")] + [(f"cousub{st}", "county subdivision:*", f"state:{st}") for st in h.STATES]
        for level, f, inn in geos:
            q = {"get": cols, "for": f}
            if inn:
                q["in"] = inn
            jobs.append((f"acs5_{y}_{level}.json", f"{api}?{urllib.parse.urlencode(q, safe=':*,')}"))

    def run(job):
        name, url = job
        p = OUT / name
        if not (p.exists() and p.stat().st_size):
            p.write_bytes(h.get(f"{url}&key={key}"))
        return name

    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        list(ex.map(run, jobs))
    log = {name: {"url": url, "accessed": dt.date.today().isoformat(), "bytes": (OUT / name).stat().st_size,
                  "sha256": hashlib.sha256((OUT / name).read_bytes()).hexdigest(),
                  "license": "Public domain (17 U.S.C. 105); Census API terms of service"} for name, url in jobs}
    (OUT / "_downloads.json").write_text(json.dumps(log, indent=2) + "\n")
    rows = []
    for name, _ in jobs:
        y = int(name.split("_")[1])
        data = json.loads((OUT / name).read_text())
        d = pd.DataFrame(data[1:], columns=data[0])
        if "county subdivision" in d:
            g = "060|" + d["state"] + d["county"] + d["county subdivision"]
        else:
            g = "160|" + d["state"] + d["place"]
        occ = pd.to_numeric(d["B25014_001E"], errors="coerce")
        cr = sum(pd.to_numeric(d[c], errors="coerce") for c in CROWD)
        rows.append(pd.DataFrame({"acs_geoid": g, "year": y, "occupied": occ, "crowded": cr,
                                  "crowded_share": (cr / occ).where(occ > 0)}))
    C = pd.concat(rows, ignore_index=True)
    C.to_csv(REFERENCE / "parking_acs_crowding.csv", index=False)
    print(C.groupby("year").size().to_string(), len(C))


if __name__ == "__main__":
    main()
