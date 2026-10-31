"""ACS 5-year total housing units (B25001_001E) and population (B01003_001E) for every place, county subdivision
and county, for releases ending 2016-2019 (Census Data API). Used by the parking no-reform model for homes at the
origin year (docs/parking/NO_REFORM_MODEL_PLAN.md, round 6).

    set -a; source .env; set +a      # CENSUS_API_KEY, never written to any file
    uv run python scripts/fetch_parking_acs_history.py

Output: data/raw/parking_acs_history/acs5_{year}_{level}.json, _downloads.json (URLs without the key);
reference/parking_acs_history_homes.csv (acs_geoid, year, homes, population)
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

YEARS = (2016, 2017, 2018, 2019)
OUT = RAW / "parking_acs_history"
STATES = ["01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13", "15", "16", "17", "18", "19", "20", "21", "22",
          "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41",
          "42", "44", "45", "46", "47", "48", "49", "50", "51", "53", "54", "55", "56"]


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "missing-middleware research"})
    return urllib.request.urlopen(req, timeout=120).read()


def main() -> None:
    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        raise SystemExit("CENSUS_API_KEY is not set (run: set -a; source .env; set +a)")
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = []
    for y in YEARS:
        api = f"https://api.census.gov/data/{y}/acs/acs5"
        geos = [("place", "place:*", ""), ("county", "county:*", "")]
        geos += [(f"cousub{st}", "county subdivision:*", f"state:{st}") for st in STATES]
        for level, f, inn in geos:
            q = {"get": "NAME,B25001_001E,B01003_001E", "for": f}
            if inn:
                q["in"] = inn
            jobs.append((f"acs5_{y}_{level}.json", f"{api}?{urllib.parse.urlencode(q, safe=':*,')}"))

    def run(job):
        name, url = job
        p = OUT / name
        if not (p.exists() and p.stat().st_size):
            p.write_bytes(get(f"{url}&key={key}"))
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
            d["acs_geoid"] = "060|" + d["state"] + d["county"] + d["county subdivision"]
        elif "place" in d:
            d["acs_geoid"] = "160|" + d["state"] + d["place"]
        else:
            d["acs_geoid"] = "050|" + d["state"] + d["county"]
        rows.append(pd.DataFrame({"acs_geoid": d["acs_geoid"], "year": y, "homes": pd.to_numeric(d["B25001_001E"], errors="coerce"),
                                  "population": pd.to_numeric(d["B01003_001E"], errors="coerce")}))
    H = pd.concat(rows, ignore_index=True)
    H.to_csv(REFERENCE / "parking_acs_history_homes.csv", index=False)
    print(H.groupby("year").size().to_string(), len(H))


if __name__ == "__main__":
    main()
