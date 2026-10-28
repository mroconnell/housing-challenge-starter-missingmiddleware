"""Download data for the Seattle 2012 and Portland 2002 checks (docs/parking/OLDER_REFORMS_PLAN.md).

    uv run python scripts/fetch_parking_older_reforms.py [--refresh]

Raw (git-ignored): data/raw/parking_older_reforms/
- seattle_res_permits.json: City of Seattle, Residential Building Permits Issued and Final since 1990 (PDDL-1.0).
- seattle_urban_villages.geojson: City of Seattle, Urban Centers and Villages (ArcGIS Online, City of Seattle).
- tabblock2010_53_pophu.zip, tl_2020_53_tabblock20.zip: Census 2010 and 2020 blocks, Washington (public domain).
- we1998a.txt ... we2011a.txt: Census permit place files, West region (public domain).
- Gaz_places_national.zip: Census 2010 Gazetteer places with 2010 housing units (public domain).
- places2k.zip: Census 2000 Gazetteer places with 2000 housing units (public domain).
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW  # noqa: E402
from scripts.fetch_tod_cases import Manifest, download_file  # noqa: E402

D = RAW / "parking_older_reforms"
PD = "US Census Bureau, public domain"
PERMITS = "https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services/Residential_Building_Permits_Issued_and_Final/FeatureServer/0/query"
VILLAGES = "https://services.arcgis.com/ZOyb2t4B0UYuYNYH/ArcGIS/rest/services/Urban_Centers_and_Villages_Growth_Monitoring/FeatureServer/0/query"
FIELDS = "PRMT_NR,RECORDNUMBER,NEW,DEMO,NET_UNITS,YEAR_ISSUED,ISS_DATE,COMP_PLAN_NAME,COMP_PLAN_TYPE,CLASS,ZONING_PRIMARY,GEOID20,DWELTYPE,APTYPE,STGLSTTITL"


def pages(url: str, params: dict, geojson: bool = False) -> tuple[list, str]:
    out, off, first = [], 0, None
    while True:
        q = urllib.parse.urlencode({**params, "resultOffset": off, "resultRecordCount": 2000, "orderByFields": "OBJECTID",
                                    "f": "geojson" if geojson else "json"})
        first = first or f"{url}?{q}"
        with urllib.request.urlopen(f"{url}?{q}", timeout=300) as r:
            d = json.load(r)
        f = d["features"]
        out += f
        off += len(f)
        if not f or (not geojson and not d.get("exceededTransferLimit")) or (geojson and len(f) < 2000):
            break
    return out, first


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)
    man = Manifest(D, "parking_older_reforms", "City of Seattle; US Census Bureau")
    if not man.have("seattle_res_permits.json", a.refresh):
        f, u = pages(PERMITS, dict(where="1=1", outFields=FIELDS, returnGeometry="false"))
        man.record("seattle_res_permits.json", json.dumps([x["attributes"] for x in f]).encode(), u, licence="PDDL-1.0 (City of Seattle)")
    if not man.have("seattle_urban_villages.geojson", a.refresh):
        f, u = pages(VILLAGES, dict(where="1=1", outFields="UV_NAME,UV_TYPE,TYPE_NAME,COMP_PLAN_TYPE,ACRES", outSR=4326), geojson=True)
        man.record("seattle_urban_villages.geojson", json.dumps({"type": "FeatureCollection", "features": f}).encode(), u,
                   licence="City of Seattle open data")
    download_file(man, "tabblock2010_53_pophu.zip",
                  "https://www2.census.gov/geo/tiger/TIGER2010BLKPOPHU/tabblock2010_53_pophu.zip", a.refresh, PD)
    download_file(man, "tl_2020_53_tabblock20.zip",
                  "https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_53_tabblock20.zip", a.refresh, PD)
    download_file(man, "tl_2020_53_place.zip", "https://www2.census.gov/geo/tiger/TIGER2020/PLACE/tl_2020_53_place.zip", a.refresh, PD)
    download_file(man, "places2k.zip", "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/places2k.zip", a.refresh, PD)
    download_file(man, "Gaz_places_national.zip", "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/Gaz_places_national.zip", a.refresh, PD)
    for y in range(1998, 2012):
        download_file(man, f"we{y}a.txt", f"https://www2.census.gov/econ/bps/Place/West%20Region/we{y}a.txt", a.refresh, PD)


if __name__ == "__main__":
    main()
