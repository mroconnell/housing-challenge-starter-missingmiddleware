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
        with zipfile.ZipFile(path) as z:  # integrity check only; read by missing_middleware.geom_extra_foundation
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
    """The state's tracts or block groups as a missing_middleware.geom Layer (attribute GEOID; longitude/latitude).
    NAD83 coordinates are used as WGS 84 unchanged (as PROJ's NAD83 -> WGS 84 step does)."""
    from missing_middleware import geom as G
    from missing_middleware import geom_extra_foundation as GX

    url = TIGER_URLS[level].format(y=year, st=state_fips)
    layer, _ = GX.read_shapefile_polygons(raw_dir / url.rsplit("/", 1)[-1])
    layer.attrs = layer.attrs[["GEOID"]].reset_index(drop=True)
    layer.crs = G.crs(4326)
    return layer


def attach_areas(points: pd.DataFrame, tracts, bgs) -> pd.DataFrame:
    """For points (columns x = longitude, y = latitude; missing allowed), return tract_geoid and bg_geoid columns:
    the polygon each point lies in (the first one if several), missing outside every polygon."""
    from missing_middleware import geom as G

    out = pd.DataFrame(index=points.index)
    x = pd.to_numeric(points["x"], errors="coerce").to_numpy(float)
    y = pd.to_numeric(points["y"], errors="coerce").to_numpy(float)
    for name, polys in (("tract_geoid", tracts), ("bg_geoid", bgs)):
        k = G.points_in_polygons(x, y, polys.polys)
        ids = polys.attrs["GEOID"].to_numpy(dtype=object)
        vals = [ids[i] if i >= 0 else None for i in k]
        out[name] = pd.Series(vals, index=points.index, dtype="str")
    return out
