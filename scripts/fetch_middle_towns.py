"""Housing units by 2020 tract part for every town-based Census permit unit (county subdivision) in Test 8's states.

Census permits in some states are filed by town or township (county subdivision), so Test 8 links tracts to towns by
2020 housing units (Census 2020 DHC, H1, summary level 080: tract parts within county subdivision and place/remainder).
Public domain; key read from the environment, never written. Output: data/raw/middle_tracts/towns/<state><county><cousub>.json
Run: set -a; source .env; set +a; uv run python scripts/fetch_middle_towns.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_middle_tracts as fm  # noqa: E402
import middle_test1_states as m  # noqa: E402

OUT = fm.OUT / "towns"
KEY = os.environ.get("CENSUS_API_KEY", "")
BASE = "https://api.census.gov/data/2020/dec/dhc?get=H1_001N"


def call(url: str):
    for a in range(6):
        try:
            req = urllib.request.Request(url + f"&key={KEY}", headers={"User-Agent": fm.UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read() or b"[]")
        except Exception:
            time.sleep(2 ** a)
    return None


def town(st: str, co: str, cs: str) -> None:
    p = OUT / f"{st}{co}{cs}.json"
    if p.exists():
        return
    q = urllib.parse.quote
    places = call(f"{BASE}&for={q('place/remainder (or part)')}:*&in={q(f'state:{st} county:{co} county subdivision:{cs}')}")
    rows = []
    for r in (places or [])[1:]:
        pl = r[-1]
        t = call(f"{BASE}&for={q('tract (or part)')}:*&in={q(f'state:{st} county:{co} county subdivision:{cs} place/remainder (or part):{pl}')}")
        rows += [{"place": pl, "tract": x[-1], "hu": int(x[0])} for x in (t or [])[1:]]
    if places is not None:
        p.write_text(json.dumps(rows))


def main() -> None:
    if not KEY:
        raise SystemExit("CENSUS_API_KEY is not set")
    OUT.mkdir(parents=True, exist_ok=True)
    d = m.load_all(2025)
    g = d.groupby("key").last()
    g = g[g["acs_geoid"].str.startswith("060|") & g["state_fips"].isin(fm.STATES)]
    jobs = sorted({(r.state_fips, r.county_fips.zfill(3), r.fips_mcd.zfill(5)) for r in g.itertuples()})
    print(len(jobs), "towns", flush=True)
    with ThreadPoolExecutor(4) as ex:
        for i, _ in enumerate(ex.map(lambda j: town(*j), jobs)):
            if i % 500 == 0:
                print(i, flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
