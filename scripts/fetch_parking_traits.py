"""Fetch public traits for the parking traits-adjusted comparison (docs/parking/TRAITS_ADJUST_PLAN.md).

    set -a; source .env; set +a      # CENSUS_API_KEY, never written to any file
    uv run python scripts/fetch_parking_traits.py

- BLS QCEW county annual averages, all industries (industry 10), 2012-2025: data/raw/parking_traits/qcew_{year}.csv
- ACS 2015-2019 5-year B25044 (vehicles available) and B08301 (means of transportation to work) for places,
  county subdivisions and counties: data/raw/parking_traits/acs2019_{level}.json
Outputs: reference/parking_traits_county_jobs.csv (county x year: employment, average pay),
reference/parking_traits_acs2019.csv (acs_geoid: share of households with no vehicle, vehicles per household, transit share)
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import hashlib
import io
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

OUT = RAW / "parking_traits"
STATES = ["01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13", "15", "16", "17", "18", "19", "20", "21", "22",
          "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41",
          "42", "44", "45", "46", "47", "48", "49", "50", "51", "53", "54", "55", "56"]
VARS = ["B25044_001E", "B25044_003E", "B25044_010E", "B25044_004E", "B25044_005E", "B25044_006E", "B25044_007E", "B25044_008E",
        "B25044_011E", "B25044_012E", "B25044_013E", "B25044_014E", "B25044_015E", "B08301_001E", "B08301_010E"]


def get(url: str) -> bytes:
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "missing-middleware-research/1.0 (public data)"}), timeout=180).read()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    log = {}
    jobs = []
    for y in range(2012, 2026):
        f = OUT / f"qcew_{y}.csv"
        url = f"https://data.bls.gov/cew/data/api/{y}/a/industry/10.csv"
        if y < 2014:  # the open data API starts in 2014; earlier years come from the annual by-industry zip
            url = f"https://data.bls.gov/cew/data/files/{y}/csv/{y}_annual_by_industry.zip"
        if not (f.exists() and f.stat().st_size):
            raw = get(url)
            if y < 2014:
                import zipfile
                z = zipfile.ZipFile(io.BytesIO(raw))
                name = next(n for n in z.namelist() if n.endswith(" 10 Total, all industries.csv") or n.endswith("10 Total, all industries.csv"))
                raw = z.read(name)
            f.write_bytes(raw)
        log[f.name] = {"url": url, "license": "Public domain (BLS)"}
        d = pd.read_csv(f, dtype={"area_fips": str})
        d = d[(d["own_code"] == 0) & (d["agglvl_code"] == 70)]  # county, all ownerships
        jobs.append(d[["area_fips", "year", "annual_avg_emplvl", "avg_annual_pay"]])
    J = pd.concat(jobs).rename(columns={"area_fips": "county_fips5", "annual_avg_emplvl": "employment", "avg_annual_pay": "avg_pay"})
    J.to_csv(REFERENCE / "parking_traits_county_jobs.csv", index=False)

    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        raise SystemExit("CENSUS_API_KEY is not set (run: set -a; source .env; set +a)")
    api = "https://api.census.gov/data/2019/acs/acs5"
    geos = [("place", "place:*", ""), ("county", "county:*", "")] + [(f"cousub{s}", "county subdivision:*", f"state:{s}") for s in STATES]
    reqs = []
    for lev, f, inn in geos:
        q = {"get": ",".join(VARS), "for": f}
        if inn:
            q["in"] = inn
        reqs.append((f"acs2019_{lev}.json", f"{api}?{urllib.parse.urlencode(q, safe=':*,')}"))

    def run(j):
        name, url = j
        p = OUT / name
        if not (p.exists() and p.stat().st_size):
            p.write_bytes(get(f"{url}&key={key}"))
        return name

    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        list(ex.map(run, reqs))
    rows = []
    for name, url in reqs:
        log[name] = {"url": url, "license": "Public domain (17 U.S.C. 105); Census API terms of service"}
        data = json.loads((OUT / name).read_text())
        d = pd.DataFrame(data[1:], columns=data[0])
        for v in VARS:
            d[v] = pd.to_numeric(d[v], errors="coerce")
        if "county subdivision" in d:
            gid = "060|" + d["state"] + d["county"] + d["county subdivision"]
        elif "place" in d:
            gid = "160|" + d["state"] + d["place"]
        else:
            gid = "050|" + d["state"] + d["county"]
        hh = d["B25044_001E"].replace(0, float("nan"))
        veh = (d["B25044_004E"] + d["B25044_011E"]) * 1 + (d["B25044_005E"] + d["B25044_012E"]) * 2 + \
              (d["B25044_006E"] + d["B25044_013E"]) * 3 + (d["B25044_007E"] + d["B25044_014E"]) * 4 + (d["B25044_008E"] + d["B25044_015E"]) * 5
        rows.append(pd.DataFrame({"acs_geoid": gid, "no_vehicle_share": (d["B25044_003E"] + d["B25044_010E"]) / hh,
                                  "vehicles_per_household": veh / hh,
                                  "transit_share": d["B08301_010E"] / d["B08301_001E"].replace(0, float("nan"))}))
    pd.concat(rows).to_csv(REFERENCE / "parking_traits_acs2019.csv", index=False)
    for name in log:
        p = OUT / name
        log[name].update(accessed=dt.date.today().isoformat(), bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    (OUT / "_downloads.json").write_text(json.dumps(log, indent=2) + "\n")
    print(len(J), "county-years;", sum(len(r) for r in rows), "ACS geographies")


if __name__ == "__main__":
    main()
