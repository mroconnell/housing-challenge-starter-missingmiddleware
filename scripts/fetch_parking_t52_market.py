"""Test 52a (CAUSAL_FRAMEWORK_PLAN.md, "52a. Market demand" and audit fix 6): market-demand inputs.

    set -a; source .env; set +a      # CENSUS_API_KEY, never written to any file or log
    uv run --all-extras python scripts/fetch_parking_t52_market.py

- ACS 5-year B25064 median gross rent (estimate and margin of error) for every place, county subdivision and county,
  releases ending 2010-2023 (Census Data API). Repeal years 2016-2024 need the release ending ey-1 (2015-2023) and the
  non-overlapping release ending ey-6 (2010-2018).
- BLS QCEW county annual average employment, all industries, all ownerships (total covered; own_code 0, industry 10,
  agglvl_code 70), 2010-2023, from the BLS open-data CSV slices (public domain).

Raw files: data/raw/parking_t52_market/ with _downloads.json (URL without the key, date, bytes, sha256).
Tidy tables: data/processed/t52/acs_b25064.csv (acs_geoid, year = last year of the release, rent, rent_moe) and
data/processed/t52/qcew_county.csv (county = 5-digit FIPS, year, employment).
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import PROCESSED, RAW  # noqa: E402

YEARS = tuple(range(2010, 2024))
OUT = RAW / "parking_t52_market"
TIDY = PROCESSED / "t52"
UA = {"User-Agent": "missing-middleware-research/1.0 (public data)"}
STATES = ["01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13", "15", "16", "17", "18", "19", "20", "21", "22",
          "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41",
          "42", "44", "45", "46", "47", "48", "49", "50", "51", "53", "54", "55", "56"]
ACS_LICENCE = "Public domain (17 U.S.C. 105); Census API terms of service"
BLS_LICENCE = "Public domain (17 U.S.C. 105); BLS QCEW open data"


def get(url: str, tries: int = 4) -> bytes:
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read()
        except Exception:  # noqa: BLE001 - retried, then raised
            if i == tries - 1:
                raise
            time.sleep(5 * (i + 1))
    raise RuntimeError(url)


def main() -> None:
    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        raise SystemExit("CENSUS_API_KEY is not set (run: set -a; source .env; set +a)")
    OUT.mkdir(parents=True, exist_ok=True)
    TIDY.mkdir(parents=True, exist_ok=True)
    jobs = []  # (file name, public URL without the key, needs key)
    for y in YEARS:
        api = f"https://api.census.gov/data/{y}/acs/acs5"
        geos = [("place", "place:*", ""), ("county", "county:*", "")]
        geos += [(f"cousub{st}", "county subdivision:*", f"state:{st}") for st in STATES]
        for level, f, inn in geos:
            q = {"get": "NAME,B25064_001E,B25064_001M", "for": f}
            if inn:
                q["in"] = inn
            jobs.append((f"acs5_{y}_{level}.json", f"{api}?{urllib.parse.urlencode(q, safe=':*,')}", True))
    for y in YEARS:
        jobs.append((f"qcew_{y}_a_industry10.csv", f"https://data.bls.gov/cew/data/api/{y}/a/industry/10.csv", False))

    def run(job):
        name, url, needs_key = job
        p = OUT / name
        if not (p.exists() and p.stat().st_size):
            p.write_bytes(get(f"{url}&key={key}" if needs_key else url))
        return name

    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        list(ex.map(run, jobs))
    log = {name: {"url": url, "accessed": dt.date.today().isoformat(), "bytes": (OUT / name).stat().st_size,
                  "sha256": hashlib.sha256((OUT / name).read_bytes()).hexdigest(),
                  "license": ACS_LICENCE if needs_key else BLS_LICENCE} for name, url, needs_key in jobs}
    (OUT / "_downloads.json").write_text(json.dumps(log, indent=2) + "\n")

    rows = []
    for name, _, needs_key in jobs:
        if not needs_key:
            continue
        y = int(name.split("_")[1])
        data = json.loads((OUT / name).read_text())
        d = pd.DataFrame(data[1:], columns=data[0])
        if "county subdivision" in d:
            g = "060|" + d["state"] + d["county"] + d["county subdivision"]
        elif "place" in d:
            g = "160|" + d["state"] + d["place"]
        else:
            g = "050|" + d["state"] + d["county"]
        e = pd.to_numeric(d["B25064_001E"], errors="coerce")
        m = pd.to_numeric(d["B25064_001M"], errors="coerce")
        rows.append(pd.DataFrame({"acs_geoid": g, "year": y, "rent": e.where(e > 0), "rent_moe": m.where(m >= 0)}))
    A = pd.concat(rows, ignore_index=True)
    A.to_csv(TIDY / "acs_b25064.csv", index=False)
    print("ACS rows by year and level")
    print(A.assign(level=A["acs_geoid"].str[:3]).groupby(["year", "level"])["rent"].agg(["size", "count"]).unstack().to_string())

    q = []
    for y in YEARS:
        d = pd.read_csv(OUT / f"qcew_{y}_a_industry10.csv", dtype={"area_fips": str, "own_code": str, "agglvl_code": str})
        d = d[(d["own_code"] == "0") & (d["agglvl_code"] == "70")]
        q.append(pd.DataFrame({"county": d["area_fips"].str.zfill(5), "year": y,
                               "employment": pd.to_numeric(d["annual_avg_emplvl"], errors="coerce"),
                               "disclosure": d["disclosure_code"].fillna("")}))
    Q = pd.concat(q, ignore_index=True)
    Q.to_csv(TIDY / "qcew_county.csv", index=False)
    print("QCEW counties by year:", Q.groupby("year")["employment"].apply(lambda s: int((s > 0).sum())).to_dict())


if __name__ == "__main__":
    main()
