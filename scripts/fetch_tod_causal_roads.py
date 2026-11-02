"""TIGER/Line roads (2020) and area water (2024) for the counties of the 11 D-11 places, for the edge test's arterial
and water tags (docs/tod/CAUSAL_FRAMEWORK_PLAN.md, Test 2). US Census Bureau, public domain (17 U.S.C. 105).

    .venv/bin/python scripts/fetch_tod_causal_roads.py

Writes data/raw/tod_causal_roads/{roads,areawater}/ and data/raw/tod_causal_roads/manifest.json.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from missing_middleware.paths import RAW  # noqa: E402

OUT = RAW / "tod_causal_roads"
COUNTIES = {"New York": ["36005", "36047", "36061", "36081", "36085"], "Philadelphia": ["42101"], "Austin": ["48453", "48491"],
            "Charlotte": ["37119"], "Chicago": ["17031"], "Denver": ["08031"], "Portland": ["41051", "41067", "41005"],
            "Seattle": ["53033"], "Salt Lake City": ["49035"], "Saint Paul": ["27123"]}
WATER_NEW = ["08031", "41051", "41067", "41005", "48453", "48491", "49035"]   # counties without area water on disk


def get(url: str, path: Path, man: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with urllib.request.urlopen(url, timeout=120) as r:
            path.write_bytes(r.read())
    b = path.read_bytes()
    man["files"][str(path.relative_to(OUT))] = {"url": url, "accessed_utc": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                                                "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(),
                                                "licence": "US Census Bureau, public domain (17 U.S.C. 105)"}
    print(path.name, len(b))


def main() -> None:
    man = {"source_id": "tod_causal_roads", "publisher": "US Census Bureau", "files": {}}
    for cs in COUNTIES.values():
        for c in cs:
            get(f"https://www2.census.gov/geo/tiger/TIGER2020/ROADS/tl_2020_{c}_roads.zip", OUT / "roads" / f"tl_2020_{c}_roads.zip", man)
    for c in WATER_NEW:
        get(f"https://www2.census.gov/geo/tiger/TIGER2024/AREAWATER/tl_2024_{c}_areawater.zip", OUT / "areawater" / f"tl_2024_{c}_areawater.zip", man)
    (OUT / "manifest.json").write_text(json.dumps(man, indent=1))


if __name__ == "__main__":
    main()
