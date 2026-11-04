"""ACS 5-year detailed tables behind TOD's Census traits (reference/tod_allvars_variable_map.csv, 46 tables), for every
place and county subdivision, releases ending 2013-2023 (Census Data API). Method 3 inputs
(docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Method 3"): each case uses the release ending the year before its event year.
Estimates only (no margins). Fetching changes no result.

    set -a; source .env; set +a      # CENSUS_API_KEY, never written to any file
    uv run python scripts/fetch_parking_acs_tod_traits.py

Output: data/raw/parking_acs_tod_traits/acs5_{year}_{table}.csv.gz (acs_geoid + estimate columns), _downloads.json
(URLs without the key, sizes, SHA-256)
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_parking_acs_history as h  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

YEARS = tuple(range(2013, 2024))
OUT = RAW / "parking_acs_tod_traits"


def tables() -> list[str]:
    m = pd.read_csv(REFERENCE / "tod_allvars_variable_map.csv")
    m = m[m["source"].astype(str).str.contains("ACS")]
    return sorted({t for x in m["acs_tables"].dropna() for t in re.findall(r"[BC]\d{5}[A-Z]?", str(x))})


def get(url: str, key: str, tries: int = 5) -> bytes:
    for i in range(tries):
        try:
            return h.get(f"{url}&key={key}" if "?" in url else f"{url}?key={key}")
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 ** i)


def estimate_vars(year: int, table: str, key: str) -> list[str]:
    js = json.loads(get(f"https://api.census.gov/data/{year}/acs/acs5/groups/{table}.json", key))
    return sorted(v for v in js["variables"] if re.fullmatch(rf"{table}_\d{{3}}E", v))


def fetch_table(year: int, table: str, key: str) -> tuple[str, list[str]]:
    name = f"acs5_{year}_{table}.csv.gz"
    p = OUT / name
    if p.exists() and p.stat().st_size:
        return name, []
    vs = estimate_vars(year, table, key)
    api = f"https://api.census.gov/data/{year}/acs/acs5"
    geos = [("place:*", "")] + [("county subdivision:*", f"state:{st}") for st in h.STATES]
    parts, urls = [], []
    for f, inn in geos:
        frames = []
        for i in range(0, len(vs), 48):
            q = {"get": ",".join(["NAME"] + vs[i:i + 48]), "for": f}
            if inn:
                q["in"] = inn
            url = f"{api}?{urllib.parse.urlencode(q, safe=':*,')}"
            urls.append(url)
            data = json.loads(get(url, key))
            d = pd.DataFrame(data[1:], columns=data[0])
            if "county subdivision" in d:
                d.index = "060|" + d["state"] + d["county"] + d["county subdivision"]
            else:
                d.index = "160|" + d["state"] + d["place"]
            frames.append(d[[c for c in d.columns if c in vs]])
        parts.append(pd.concat(frames, axis=1))
    out = pd.concat(parts).apply(pd.to_numeric, errors="coerce")
    out.index.name = "acs_geoid"
    out.to_csv(p, compression="gzip")
    return name, urls


def main() -> None:
    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        raise SystemExit("CENSUS_API_KEY is not set (run: set -a; source .env; set +a)")
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(y, t) for y in YEARS for t in tables()]
    log_p = OUT / "_downloads.json"
    log = json.loads(log_p.read_text()) if log_p.exists() else {}
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(fetch_table, y, t, key): (y, t) for y, t in jobs}
        for n, fu in enumerate(cf.as_completed(futs), 1):
            name, urls = fu.result()
            p = OUT / name
            if urls:
                log[name] = {"urls": urls[:3] + ([f"... {len(urls) - 3} more"] if len(urls) > 3 else []),
                             "accessed": dt.date.today().isoformat(), "bytes": p.stat().st_size,
                             "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                             "license": "Public domain (17 U.S.C. 105); Census API terms of service"}
            if n % 25 == 0:
                print(n, "of", len(jobs), flush=True)
                log_p.write_text(json.dumps(log, indent=2) + "\n")
    log_p.write_text(json.dumps(log, indent=2) + "\n")
    print("done", len(jobs))


if __name__ == "__main__":
    main()
