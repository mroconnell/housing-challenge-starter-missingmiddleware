"""Download public Census data for middle housing Test 8 (stopped middle-housing places).

All sources are US Census Bureau (public domain). Files go to data/raw/middle_tracts/ (gitignored) with a
_downloads.json manifest (url, bytes, sha256, accessed). The API key is read from the environment and never written.
Run: set -a; source .env; set +a; uv run python scripts/fetch_middle_tracts.py
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "middle_tracts"
UA = "missing-middleware-research/1.0 (public data)"
# Law states plus every state that passes Test 1's comparison screen (fake law-state pool)
STATES = ["01", "02", "05", "06", "10", "11", "13", "16", "17", "18", "19", "20", "21", "22", "23", "26", "27", "28",
          "29", "31", "32", "34", "35", "36", "37", "38", "39", "40", "41", "42", "45", "46", "47", "50", "51", "54",
          "55", "56"]
ABBR = {"01": "AL", "02": "AK", "05": "AR", "06": "CA", "10": "DE", "11": "DC", "13": "GA", "16": "ID", "17": "IL",
        "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME", "26": "MI", "27": "MN", "28": "MS",
        "29": "MO", "31": "NE", "32": "NV", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
        "40": "OK", "41": "OR", "42": "PA", "45": "SC", "46": "SD", "47": "TN", "50": "VT", "51": "VA", "54": "WV",
        "55": "WI", "56": "WY"}
KEY = os.environ.get("CENSUS_API_KEY", "")


def manifest() -> dict:
    p = OUT / "_downloads.json"
    return json.loads(p.read_text()) if p.exists() else {}


def get(url: str, name: str, man: dict, api: bool = False) -> Path:
    p = OUT / name
    if p.exists() and name in man:
        return p
    full = url + (f"&key={KEY}" if api else "")
    for attempt in range(5):
        try:
            req = urllib.request.Request(full, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=300) as r:
                data = r.read()
            break
        except Exception:
            time.sleep(2 ** attempt * 2)
    else:
        raise SystemExit(f"failed: {url}")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    man[name] = {"url": url, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                 "accessed": dt.date.today().isoformat()}
    (OUT / "_downloads.json").write_text(json.dumps(man, indent=1))
    return p


def main() -> None:
    if not KEY:
        raise SystemExit("CENSUS_API_KEY is not set (run: set -a; source .env; set +a)")
    OUT.mkdir(parents=True, exist_ok=True)
    man = manifest()
    get("https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-b25127.dat",
        "acsdt5y2024-b25127.dat", man)
    get("https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/documentation/Geos20245YR.txt",
        "Geos20245YR.txt", man)
    get("https://www2.census.gov/geo/docs/maps-data/data/rel/trf_txt/us2010trf.txt", "us2010trf.txt", man)
    get("https://www2.census.gov/geo/docs/maps-data/data/rel2020/tract/tab20_tract20_tract10_natl.txt",
        "tab20_tract20_tract10_natl.txt", man)
    for st in STATES:
        get(f"https://api.census.gov/data/2000/dec/sf3?get=H030001,H030004,H030005&for=tract:*&in=state:{st}&in=county:*",
            f"sf3_2000_h030_{st}.json", man, api=True)
        get(f"https://www2.census.gov/geo/docs/maps-data/data/baf2020/BlockAssign_ST{st}_{ABBR[st]}.zip",
            f"BlockAssign_ST{st}_{ABBR[st]}.zip", man)
        cp = get(f"https://api.census.gov/data/2020/dec/pl?get=NAME&for=county:*&in=state:{st}", f"pl_counties_{st}.json", man, api=True)
        for row in json.loads(cp.read_text())[1:]:
            co = row[-1]
            get(f"https://api.census.gov/data/2020/dec/pl?get=H1_001N&for=block:*&in=state:{st}&in=county:{co}",
                f"pl_blocks/{st}{co}.json", man, api=True)
        print(st, "done", flush=True)


if __name__ == "__main__":
    main()
