"""Census TIGER/Line tract and block-group geometries, and point-in-polygon attach.

This module downloads its own copy of the state files (it does not depend on
the statewide foundation build). Tracts/BGs are 2020-census geography, which
TIGER 2024 still carries and ACS 2020-2024 uses.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

from . import fetch_util as fu

TIGER_YEAR = 2024
TIGER_URLS = {
    "tract": "https://www2.census.gov/geo/tiger/TIGER{y}/TRACT/tl_{y}_{st}_tract.zip",
    "block_group": "https://www2.census.gov/geo/tiger/TIGER{y}/BG/tl_{y}_{st}_bg.zip",
}


def fetch_tiger(raw_dir: Path, state_fips: str, year: int = TIGER_YEAR, log=print) -> dict:
    raw_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for level, tmpl in TIGER_URLS.items():
        url = tmpl.format(y=year, st=state_fips)
        path = raw_dir / url.rsplit("/", 1)[-1]
        if not path.exists():
            log(f"downloading {url}")
            path.write_bytes(fu.get(url, timeout=600))
        with zipfile.ZipFile(path) as z:  # integrity check only; read via pyogrio zip://
            bad = z.testzip()
            if bad:
                raise RuntimeError(f"{path.name}: corrupt member {bad}")
        entries.append({"level": level, "file": path.name, "url": url, "vintage": f"TIGER/Line {year}",
                        "accessed": fu.now_iso(), "sha256": fu.sha256_file(path)})
    fu.write_manifest(raw_dir / "manifest.json", entries, {
        "source_id": "tiger_wi", "publisher": "U.S. Census Bureau TIGER/Line",
        "license": "Public domain (U.S. Government work)",
    })
    return fu.read_manifest(raw_dir / "manifest.json")


def load_tiger(raw_dir: Path, state_fips: str, level: str, year: int = TIGER_YEAR):
    import geopandas as gpd

    url = TIGER_URLS[level].format(y=year, st=state_fips)
    gdf = gpd.read_file(f"zip://{raw_dir / url.rsplit('/', 1)[-1]}")
    return gdf[["GEOID", "geometry"]].to_crs(4326)


def attach_areas(points, tracts, bgs) -> pd.DataFrame:
    """For a GeoDataFrame of points (EPSG:4326), return tract_geoid and bg_geoid columns."""
    import geopandas as gpd

    out = pd.DataFrame(index=points.index)
    for name, polys in (("tract_geoid", tracts), ("bg_geoid", bgs)):
        j = gpd.sjoin(points[["geometry"]], polys.rename(columns={"GEOID": name}), how="left",
                      predicate="within")
        j = j[~j.index.duplicated(keep="first")]
        out[name] = j[name]
    return out
