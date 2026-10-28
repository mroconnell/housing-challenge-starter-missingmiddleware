"""Audit: Census permit survey (homes permitted 2010-2019) vs census home counts (2010 -> 2020), for the lot-model cities.

    uv run --all-extras python scripts/run_tod_audit_permits_census.py

A large gap means permits miss building, or many homes were lost. Writes reference/tod_audit_permits_census.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import control_cities as cc  # noqa: E402

CITIES = {"New York": ("36", "New York city"), "Philadelphia": ("42", "Philadelphia city"), "Charlotte": ("37", "Charlotte city"),
          "Saint Paul": ("27", "St. Paul city"), "Seattle": ("53", "Seattle city"), "Los Angeles": ("06", "Los Angeles city"),
          "Chicago": ("17", "Chicago city"), "Madison": ("55", "Madison city"), "Bellevue": ("53", "Bellevue city"),
          "Milwaukee": ("55", "Milwaukee city")}


def find(pattern: str) -> Path:
    return sorted(RAW.rglob(pattern))[0]


def main() -> None:
    bps = cc.read_bps(RAW / "tod_control_cities" / "bps")
    gaz = cc.read_gazetteer(RAW / "tod_control_cities" / "Gaz_places_national.zip")
    panel, places = cc.link(bps, gaz, cc.read_county_hu(RAW / "tod_control_cities" / "Gaz_counties_national.zip"))
    rows = []
    for st in sorted({v[0] for v in CITIES.values()}):
        pl = gpd.read_file(find(f"tl_2020_{st}_place.zip"))
        bl = gpd.read_file(find(f"tl_2020_{st}_tabblock20.zip"), ignore_geometry=True, columns=["HOUSING20", "INTPTLAT20", "INTPTLON20"])
        pts = gpd.GeoDataFrame(bl, geometry=gpd.points_from_xy(bl.INTPTLON20.astype(float), bl.INTPTLAT20.astype(float)), crs=4269)
        for city, (s, name) in CITIES.items():
            if s != st:
                continue
            g = pl[pl["NAMELSAD"] == name]
            hu20 = float(pts[pts.within(g.geometry.iloc[0].to_crs if False else g.geometry.union_all())]["HOUSING20"].sum())
            geoid = s + g["PLACEFP"].iloc[0]
            hu10 = float(places.set_index("geoid").loc[geoid, "hu10"])
            p = panel[(panel["geoid"] == geoid) & panel["year"].between(2010, 2019)]["units"].sum()
            rows.append({"city": city, "homes_2010": hu10, "homes_2020": hu20, "census_change": hu20 - hu10,
                         "permits_2010_2019": float(p), "census_change_over_permits": (hu20 - hu10) / p if p else None})
            print(rows[-1], flush=True)
    R = pd.DataFrame(rows)
    R.round(3).to_csv(REFERENCE / "tod_audit_permits_census.csv", index=False)
    print(R.round(2).to_string())


if __name__ == "__main__":
    main()
