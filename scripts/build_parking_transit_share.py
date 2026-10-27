"""Round-3 variable V16 (docs/parking/ROUND3_PLAN.md): share of each repeal place's homes in census block
groups whose centre lies within half a mile of a fixed-route transit stop in the federal National Transit Map.
No effects are read.

    uv run python scripts/build_parking_transit_share.py [--fetch]

Inputs (fetched; public domain or CC BY 3.0 US):
  data/raw/census_cb_2024/cb_2024_us_{place,cousub,bg}_500k.zip   Census cartographic boundaries
  NTAD National Transit Map stops (BTS ArcGIS service), queried by each place's bounding box
  data/raw/census_acs5_2024_tbsf/acsdt5y2024-b25002.dat            homes per block group
Output: reference/parking_transit_share.csv; raw stop extracts in data/raw/ntm_stops_parking/
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.foundation import parsers  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

CB = RAW / "census_cb_2024"
CB_URL = "https://www2.census.gov/geo/tiger/GENZ2024/shp/{f}"
CB_FILES = ["cb_2024_us_place_500k.zip", "cb_2024_us_cousub_500k.zip", "cb_2024_us_bg_500k.zip"]
NTM = "https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_National_Transit_Map_Stops/FeatureServer/0/query"
STOPS = RAW / "ntm_stops_parking"
HALF_MILE_M = 804.672
UA = {"User-Agent": "missing-middleware research (public data)"}


def _log(path: Path, name: str, url: str, data: bytes) -> None:
    lp = path / "_downloads.json"
    log = json.loads(lp.read_text()) if lp.exists() else {}
    log[name] = {"accessed": dt.date.today().isoformat(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "url": url}
    lp.write_text(json.dumps(dict(sorted(log.items())), indent=2) + "\n")


def fetch_cb() -> None:
    CB.mkdir(parents=True, exist_ok=True)
    for f in CB_FILES:
        if (CB / f).exists():
            continue
        url = CB_URL.format(f=f)
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read()
        (CB / f).write_bytes(data)
        _log(CB, f, url, data)


def stops_in_bbox(key: str, bounds) -> pd.DataFrame:
    """Stops in a bounding box (lon/lat), cached per place."""
    STOPS.mkdir(parents=True, exist_ok=True)
    f = STOPS / f"{key.replace('|', '_')}.json"
    if not f.exists():
        feats, off = [], 0
        while True:
            p = dict(where="1=1", geometry=",".join(f"{b:.5f}" for b in bounds), geometryType="esriGeometryEnvelope",
                     inSR=4326, spatialRel="esriSpatialRelIntersects", outFields="OBJECTID", returnGeometry="true",
                     outSR=4326, f="json", resultOffset=off, resultRecordCount=2000)
            url = NTM + "?" + urllib.parse.urlencode(p)
            d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read())
            if "error" in d:
                raise RuntimeError(d["error"])
            fs = d.get("features", [])
            feats += [{"x": x["geometry"]["x"], "y": x["geometry"]["y"]} for x in fs if x.get("geometry")]
            if not d.get("exceededTransferLimit") and len(fs) < 2000:
                break
            off += len(fs)
        data = json.dumps(feats).encode()
        f.write_bytes(data)
        _log(STOPS, f.name, NTM + " (envelope query; see bounds in reference/parking_transit_share.csv)", data)
    return pd.DataFrame(json.loads(f.read_text()), columns=["x", "y"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    fetch_cb()
    v = pd.read_csv(REFERENCE / "parking_round3_vars.csv", dtype={"acs_geoid": str})
    place = gpd.read_file("zip://" + str(CB / "cb_2024_us_place_500k.zip"))[["GEOID", "geometry"]]
    place["acs_geoid"] = "160|" + place["GEOID"]
    cous = gpd.read_file("zip://" + str(CB / "cb_2024_us_cousub_500k.zip"))[["GEOID", "geometry"]]
    cous["acs_geoid"] = "060|" + cous["GEOID"]
    poly = pd.concat([place, cous], ignore_index=True).set_index("acs_geoid")
    poly = gpd.GeoDataFrame(poly, geometry="geometry", crs=place.crs).to_crs(4326)
    bg = gpd.read_file("zip://" + str(CB / "cb_2024_us_bg_500k.zip"))[["GEOID", "STATEFP", "geometry"]]
    states = {k.split("|")[1][:2] for k in v["acs_geoid"].dropna()}
    bg = bg[bg["STATEFP"].isin(states)].to_crs(5070)
    bg["pt"] = bg.geometry.representative_point()
    h = parsers.read_acs_sf(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", state_fips="", sumlevels=("150",))
    homes = h.set_index("geoid")["B25002_E001"]
    bg["homes"] = bg["GEOID"].map(homes).fillna(0)
    pts = gpd.GeoDataFrame(bg[["GEOID", "homes"]], geometry=bg["pt"], crs=5070)
    rows = []
    for r in v.itertuples():
        if r.acs_geoid not in poly.index:
            rows.append(dict(prn_key=r.prn_key, place=r.place, V16_share_homes_near_transit=np.nan, note="no boundary"))
            continue
        shp = poly.loc[[r.acs_geoid]]
        inside = pts[pts.within(shp.to_crs(5070).geometry.iloc[0])]
        minx, miny, maxx, maxy = shp.geometry.iloc[0].bounds
        pad = 0.012
        st = stops_in_bbox(r.key, (minx - pad, miny - pad, maxx + pad, maxy + pad))
        tot = inside["homes"].sum()
        if st.empty or tot == 0:
            share = 0.0 if tot else np.nan
            n_stops = 0
            island = 0.0
        else:
            sg = gpd.GeoSeries(gpd.points_from_xy(st["x"], st["y"]), crs=4326).to_crs(5070)
            near = inside.geometry.apply(lambda q: sg.distance(q).min() <= HALF_MILE_M)
            share = float(inside.loc[near, "homes"].sum() / tot)
            n_stops = len(st)
            # island size (owner, 2026-10-27, from the TOD work): the largest continuous patch of land within
            # half a mile of a stop, inside the place, in acres
            covered = gpd.GeoSeries([sg.buffer(HALF_MILE_M).union_all()], crs=5070).intersection(
                shp.to_crs(5070).geometry.iloc[0]).explode(index_parts=False)
            island = float(covered.area.max() / 4046.8564224) if len(covered) and covered.area.max() > 0 else 0.0
        rows.append(dict(prn_key=r.prn_key, place=r.place, block_groups=len(inside), homes_in_bgs=tot, stops_in_bbox=n_stops,
                         bounds=f"{minx:.4f},{miny:.4f},{maxx:.4f},{maxy:.4f}", V16_share_homes_near_transit=share,
                         V19_log_island_acres=float(np.log10(island + 1))))
    out = pd.DataFrame(rows)
    out.round(4).to_csv(REFERENCE / "parking_transit_share.csv", index=False)
    print(out["V16_share_homes_near_transit"].describe().round(3).to_dict(), (out["V16_share_homes_near_transit"] == 0).sum())


if __name__ == "__main__":
    main()
