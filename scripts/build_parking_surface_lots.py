"""Round-3 variables V17-V18 (docs/parking/ROUND3_PLAN.md): surface parking inside each repeal place,
from OpenStreetMap. No effects are read.

Evaluated, not used (2026-10-27): OpenStreetMap is ODbL (share-alike), which the project does not distribute
(owner decision D5), and the variables failed the round-3 test. The output is written to data/processed/parking/
(git-ignored), not to reference/.

  V17 share of land area in surface parking lots
  V18 share of that parking in large contiguous sites (>= 2 acres after joining lots within 30 m)

    uv run --all-extras python scripts/build_parking_surface_lots.py
Raw Overpass extracts: data/raw/osm_parking_lots/ (with _downloads.json); output data/processed/parking/parking_surface_lots.csv
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Polygon

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

OSM = RAW / "osm_parking_lots"
OVERPASS = "https://overpass-api.de/api/interpreter"
CB = RAW / "census_cb_2024"
ACRE_M2 = 4046.8564224
UA = {"User-Agent": "missing-middleware research (public data; contact via repository)"}


def query(key: str, bounds) -> list:
    OSM.mkdir(parents=True, exist_ok=True)
    f = OSM / f"{key.replace('|', '_')}.json"
    if not f.exists():
        s, w, n, e = bounds[1], bounds[0], bounds[3], bounds[2]
        q = (f'[out:json][timeout:120];(way["amenity"="parking"]({s},{w},{n},{e}););out geom;')
        data = None
        for attempt in range(6):
            try:
                req = urllib.request.Request(OVERPASS, data=urllib.parse.urlencode({"data": q}).encode(), headers=UA)
                data = urllib.request.urlopen(req, timeout=200).read()
                break
            except Exception:
                time.sleep(20 * (attempt + 1))
        if data is None:
            return None
        f.write_bytes(data)
        lp = OSM / "_downloads.json"
        log = json.loads(lp.read_text()) if lp.exists() else {}
        log[f.name] = {"accessed": dt.date.today().isoformat(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                       "url": OVERPASS, "query": q, "licence": "ODbL 1.0, (c) OpenStreetMap contributors"}
        lp.write_text(json.dumps(dict(sorted(log.items())), indent=2) + "\n")
        time.sleep(5)
    return json.loads(f.read_text()).get("elements", [])


def lots(elements) -> gpd.GeoDataFrame:
    polys = []
    for el in elements:
        tags = el.get("tags", {})
        if tags.get("parking") in ("multi-storey", "underground", "rooftop", "street_side", "lane", "on_street"):
            continue
        g = el.get("geometry") or []
        if len(g) >= 4 and g[0] == g[-1]:
            polys.append(Polygon([(p["lon"], p["lat"]) for p in g]))
    return gpd.GeoDataFrame(geometry=polys, crs=4326)


def main() -> None:
    v = pd.read_csv(REFERENCE / "parking_round3_vars.csv", dtype={"acs_geoid": str})
    place = gpd.read_file("zip://" + str(CB / "cb_2024_us_place_500k.zip"))[["GEOID", "ALAND", "geometry"]]
    place["acs_geoid"] = "160|" + place["GEOID"]
    cous = gpd.read_file("zip://" + str(CB / "cb_2024_us_cousub_500k.zip"))[["GEOID", "ALAND", "geometry"]]
    cous["acs_geoid"] = "060|" + cous["GEOID"]
    poly = gpd.GeoDataFrame(pd.concat([place, cous], ignore_index=True), geometry="geometry", crs=place.crs).set_index("acs_geoid").to_crs(4326)
    rows = []
    for r in v.itertuples():
        if r.acs_geoid not in poly.index:
            rows.append(dict(prn_key=r.prn_key, place=r.place, note="no boundary"))
            continue
        shp = poly.loc[r.acs_geoid]
        els = query(r.key, shp.geometry.bounds)
        if els is None:
            rows.append(dict(prn_key=r.prn_key, place=r.place, note="OpenStreetMap download failed"))
            continue
        g = lots(els)
        land_m2 = float(shp["ALAND"])
        if g.empty:
            rows.append(dict(prn_key=r.prn_key, place=r.place, lots=0, V17_share_land_surface_parking=0.0, V18_share_parking_in_large_sites=np.nan))
            continue
        g = g.to_crs(5070)
        boundary = gpd.GeoSeries([shp.geometry], crs=4326).to_crs(5070).iloc[0]
        g = g[g.intersects(boundary)].copy()
        g["geometry"] = g.geometry.buffer(0).intersection(boundary)
        area = g.geometry.area.sum()
        merged = gpd.GeoSeries(g.geometry.buffer(15).union_all(), crs=5070).explode(index_parts=False)
        big = 0.0
        for m in merged:
            a = g[g.intersects(m)].geometry.area.sum()
            if a >= 2 * ACRE_M2:
                big += a
        rows.append(dict(prn_key=r.prn_key, place=r.place, lots=len(g), parking_acres=area / ACRE_M2, land_acres=land_m2 / ACRE_M2,
                         V17_share_land_surface_parking=area / land_m2 if land_m2 else np.nan,
                         V18_share_parking_in_large_sites=big / area if area else np.nan))
    out = pd.DataFrame(rows)
    out_dir = REFERENCE.parent / "data" / "processed" / "parking"
    out_dir.mkdir(parents=True, exist_ok=True)
    out.round(5).to_csv(out_dir / "parking_surface_lots.csv", index=False)
    print(out[["lots", "V17_share_land_surface_parking", "V18_share_parking_in_large_sites"]].describe().round(4))


if __name__ == "__main__":
    main()
