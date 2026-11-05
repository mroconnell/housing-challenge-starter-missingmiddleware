"""Fetch USDA ERS rural-urban commuting area (RUCA) codes (2010 and 2020, census tracts) and the Census CBSA
principal-city list (delineation list 2, July 2023), plus
the 2020 and 2010 Census Gazetteer tract files (tract internal points, to place tracts in cities). Public domain (U.S. government works).

    uv run python scripts/fetch_parking_ruca.py
Raw files and a download log go to data/raw/parking_ruca/.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import RAW  # noqa: E402

UA = {"User-Agent": "missing-middleware-research/1.0 (public data)"}
URLS = {
    "ruca2020_tracts.csv": "https://www.ers.usda.gov/media/5443/2020-rural-urban-commuting-area-codes-census-tracts.csv?v=15806",
    "ruca2010_tracts.xlsx": "https://www.ers.usda.gov/media/5438/2010-rural-urban-commuting-area-codes-revised-732019.xlsx?v=32965",
    "cbsa_list2_2023.xlsx": "https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2023/delineation-files/list2_2023.xlsx",
    "gaz_tracts_2020.zip": "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_Gaz_tracts_national.zip",
    "gaz_tracts_2010.zip": "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/Gaz_tracts_national.zip",
}


def main() -> None:
    out = RAW / "parking_ruca"
    out.mkdir(parents=True, exist_ok=True)
    log = []
    for name, url in URLS.items():
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read()
        (out / name).write_bytes(data)
        log.append(dict(file=name, url=url, downloaded=dt.date.today().isoformat(), bytes=len(data),
                        sha256=hashlib.sha256(data).hexdigest(), licence="public domain (U.S. government work)"))
        print(name, len(data))
    (out / "_downloads.json").write_text(json.dumps(log, indent=2))


if __name__ == "__main__":
    main()
