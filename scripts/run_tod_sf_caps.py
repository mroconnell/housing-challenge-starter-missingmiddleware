"""Pasadena (Lower Hastings Ranch, 2016) and Culver City (house-size limits, 2015-2016): single-family caps from
Stacy et al.'s tightening list, measured with 2000/2010/2020 census blocks (docs/tod/CENSUS2000_PLAN.md section 7).

    uv run --all-extras python scripts/run_tod_sf_caps.py

Fetches (raw, git-ignored, data/raw/tod_sf_caps/): Pasadena zoning (City GIS) and LA County Assessor parcels with a
single-family use code around Culver City (geometry and use code only). Writes reference/tod_sf_caps.csv.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from scripts import run_tod_census2000 as C2  # noqa: E402
from scripts import run_tod_census_cases as R  # noqa: E402
from scripts.fetch_tod_cases import Manifest  # noqa: E402
from scripts.fetch_tod_census_cases import arcgis_geojson  # noqa: E402

D = RAW / "tod_sf_caps"
PAS = "https://services2.arcgis.com/zNjnZafDYCAJAbN0/arcgis/rest/services/Zoning/FeatureServer/0"
PARCELS = "https://public.gis.lacounty.gov/public/rest/services/LACounty_Cache/LACounty_Parcel/MapServer/0"
CC_ENVELOPE = (-118.4520, 33.9700, -118.3470, 34.0440)   # Culver City plus about 1/2 mile, WGS84


def fetch():
    man = Manifest(D, "tod_sf_caps", "City of Pasadena GIS; Los Angeles County Assessor (public GIS)")
    if not man.have("pasadena_zoning.geojson", False):
        data, url = arcgis_geojson(PAS, "1=1")
        man.record("pasadena_zoning.geojson", data, url, licence="City of Pasadena GIS, public layer")
    if not man.have("la_sf_parcels_culver.geojson", False):
        feats, off, first = [], 0, None
        while True:
            q = urllib.parse.urlencode(dict(where="UseCode LIKE '01%'", geometry=",".join(map(str, CC_ENVELOPE)),
                                            geometryType="esriGeometryEnvelope", inSR=4326, spatialRel="esriSpatialRelIntersects",
                                            outFields="UseCode,TaxRateCity", outSR=4326, f="geojson", resultOffset=off,
                                            resultRecordCount=1000))
            first = first or f"{PARCELS}/query?{q}"
            with urllib.request.urlopen(f"{PARCELS}/query?{q}", timeout=300) as r:
                f = json.load(r).get("features", [])
            feats += f
            off += len(f)
            if len(f) < 1000:
                break
        man.record("la_sf_parcels_culver.geojson", json.dumps({"type": "FeatureCollection", "features": feats}).encode(), first,
                   licence="Los Angeles County Assessor public GIS; use code and city only")


def measure(name, st, treated, comp, rng, note) -> dict:
    g = C2.three(st, treated, comp)
    d0, d1 = C2.diffs(g)
    lo0, hi0, lo, hi = C2.boot(g, rng)
    return {"case": name, "note": note, "treated_acres_2010": g[2010][0]["land"].sum() / R.ACRE,
            "treated_homes_2000": g[2000][0]["homes"].sum(), "treated_homes_2010": g[2010][0]["homes"].sum(),
            "treated_homes_2020": g[2020][0]["homes"].sum(), "comparison_homes_2000": g[2000][1]["homes"].sum(),
            "comparison_homes_2010": g[2010][1]["homes"].sum(), "comparison_homes_2020": g[2020][1]["homes"].sum(),
            "diff_2000_2010_per_acre": d0, "diff_2000_2010_low": lo0, "diff_2000_2010_high": hi0,
            "diff_2010_2020_per_acre": d1, "change_in_change": d1 - d0, "low": lo, "high": hi}


def main():
    fetch()
    rng = np.random.default_rng(C2.SEED + 1)
    z = gpd.read_file(D / "pasadena_zoning.geojson").to_crs(R.CRS)
    nd = z[z["OVERLAY_CODE"].astype(str).str.strip() == "ND"].geometry.make_valid().union_all()
    sf = z[z["GEN_CODE"].astype(str).str.contains("Single-Family")].geometry.make_valid().union_all()
    pas = measure("pasadena_lower_hastings_ranch_2016", "06", nd, sf.intersection(nd.buffer(R.HALF)).difference(nd), rng,
                  "RS-6 ND overlay vs single-family zones within 1/2 mile")
    p = gpd.read_file(D / "la_sf_parcels_culver.geojson").to_crs(R.CRS)
    city = p["TaxRateCity"].astype(str).str.upper().str.strip()
    cc = p[city == "CULVER CITY"].geometry.make_valid().union_all()
    ccline = gpd.read_file(R.D / "tl_2020_06_place.zip")
    ccline = ccline[ccline["NAME"] == "Culver City"].to_crs(R.CRS).geometry.union_all()
    other = p[city != "CULVER CITY"]
    other = other[other.geometry.representative_point().within(ccline.buffer(R.HALF).difference(ccline))].geometry.make_valid().union_all()
    cul = measure("culver_city_house_size_2015", "06", cc, other, rng,
                  "single-family parcels in Culver City vs single-family parcels within 1/2 mile outside it")
    out = pd.DataFrame([pas, cul])
    out.round(4).to_csv(REFERENCE / "tod_sf_caps.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.round(2).T.to_string())


if __name__ == "__main__":
    main()
