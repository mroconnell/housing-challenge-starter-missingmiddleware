"""Fetch the inputs for the baseline bake-off (docs/shared/BASELINE_BAKEOFF_PLAN.md, locked 2026-11-05).

    set -a; source .env; set +a                      # CENSUS_API_KEY, read from the environment only
    uv run python scripts/fetch_baseline_bakeoff.py  # skips files already on disk; --force re-downloads

Downloads (all U.S. Census Bureau, public domain, 17 U.S.C. 105), into data/raw/baseline_bakeoff/ (git-ignored):
    bps_place/mw{1990..2014}a.txt     Building Permits Survey, Midwest region place files (Wisconsin rows used)
    bps_county/co{1990..1999}a.txt    Building Permits Survey, county files (2000-2025 are already on disk)
    hu_1990/st-98-51.txt              state housing units, April 1, 1990 census (revised count, as published 1999)
    hu_1990/pl9417wi.dbf, pl94stru.dbf  1990 P.L. 94-171 file for Wisconsin and its layout (county subdivisions)
    hu_api/dec_{2000,2010,2020}_{state,cousub55}.json  decennial housing units by state and WI county subdivision

State permit files 1990-2025 for every state are already on disk (data/raw/census_bps_state/, national files).

Every file is logged in data/raw/baseline_bakeoff/_downloads.json with URL, date, bytes and SHA-256.
The Census API key is never written: it is added to the request only, logged URLs omit it, and error
messages have it removed. Requests send a plain user agent.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import RAW  # noqa: E402

OUT = RAW / "baseline_bakeoff"
UA = "missing-middleware-research/1.0 (public data)"
LICENSE = "Public domain (17 U.S.C. 105); Census API terms of service for api.census.gov"
BPS = "https://www2.census.gov/econ/bps"
PL94 = "https://www2.census.gov/census_1990/1990_PL94-171/CD8%20-%20AZ%20GA%20MI%20NH%20ND%20WI"
HU90 = "https://www2.census.gov/programs-surveys/popest/tables/1990-2000/housing/totals/st-98-51.txt"

# Decennial housing units: (year, dataset, variable). 2020 uses the redistricting file (P.L. 94-171).
DEC = [(2000, "dec/sf1", "H001001"), (2010, "dec/sf1", "H001001"), (2020, "dec/pl", "H1_001N")]


def plain_jobs() -> list[tuple[str, str]]:
    jobs = [(f"bps_place/mw{y}a.txt", f"{BPS}/Place/Midwest%20Region/mw{y}a.txt") for y in range(1990, 2015)]
    jobs += [(f"bps_county/co{y}a.txt", f"{BPS}/County/co{y}a.txt") for y in range(1990, 2000)]
    jobs += [("hu_1990/st-98-51.txt", HU90),
             ("hu_1990/pl9417wi.dbf", f"{PL94}/pl9417wi.dbf"),
             ("hu_1990/pl94stru.dbf", f"{PL94}/pl94stru.dbf")]
    return jobs


def api_jobs() -> list[tuple[str, str]]:
    jobs = []
    for y, ds, var in DEC:
        base = f"https://api.census.gov/data/{y}/{ds}"
        q_state = urllib.parse.urlencode({"get": f"NAME,{var}", "for": "state:*"}, safe=":*,")
        q_cousub = urllib.parse.urlencode([("get", f"NAME,{var}"), ("for", "county subdivision:*"),
                                           ("in", "state:55"), ("in", "county:*")], safe=":*,")
        jobs += [(f"hu_api/dec_{y}_state.json", f"{base}?{q_state}"),
                 (f"hu_api/dec_{y}_cousub55.json", f"{base}?{q_cousub}")]
    return jobs


def get(url: str, key: str | None = None) -> bytes:
    full = f"{url}&key={key}" if key else url
    req = urllib.request.Request(full, headers={"User-Agent": UA})
    try:
        return urllib.request.urlopen(req, timeout=300).read()
    except Exception as e:  # never let the key reach a log or traceback
        msg = str(e).replace(key, "<key>") if key else str(e)
        raise SystemExit(f"download failed: {url} ({msg})") from None


def main() -> None:
    force = "--force" in sys.argv
    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        raise SystemExit("CENSUS_API_KEY is not set (run: set -a; source .env; set +a)")
    OUT.mkdir(parents=True, exist_ok=True)
    log_path = OUT / "_downloads.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {}
    for name, url, use_key in [(n, u, False) for n, u in plain_jobs()] + [(n, u, True) for n, u in api_jobs()]:
        p = OUT / name
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists() and p.stat().st_size and not force:
            continue
        data = get(url, key if use_key else None)
        if use_key and key.encode() in data:
            raise SystemExit(f"response for {name} contains the key; not written")
        p.write_bytes(data)
        log[name] = {"url": url, "accessed": dt.date.today().isoformat(), "bytes": len(data),
                     "sha256": hashlib.sha256(data).hexdigest(), "license": LICENSE}
        print(f"{name}: {len(data):,} bytes")
    log_path.write_text(json.dumps(dict(sorted(log.items())), indent=2) + "\n")
    text = log_path.read_text()
    assert key not in text, "key found in the download log"
    print(f"done: {len(log)} files logged in {log_path}")


if __name__ == "__main__":
    main()
