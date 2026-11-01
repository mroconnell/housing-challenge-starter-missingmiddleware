"""Join neighborhood traits to the station-area lot tables (docs/tod/STATION_AREA_PLAN.md, trait list v2; step C).

For every data/processed/tod_station_area/lots_<case>.parquet:
  - block group (EPA Smart Location Database, version before the reform: v2 = 2012 schedules for reforms through
    2018, v3 = 2020 schedules after): transit frequency (D4c, D4d), jobs per acre (D1C), transit job access (D5br),
    share of households with no car, national walkability index (v3 only);
  - block group job growth over the 5 years before the reform (Census LEHD LODES, summed from blocks);
  - National Register of Historic Places: lot inside a listed district or property listed before the reform;
  - tract: the lot model's 78 ACS variables (v_*) from the 5-year survey ending the year before the reform.
Writes the same file back with the new columns (local only).

    uv run --all-extras python scripts/enrich_tod_station_lots.py --case la_toc_2017     (or --all)
"""
from __future__ import annotations

import argparse
import gzip
import importlib.util
import sys
from functools import lru_cache
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import RAW  # noqa: E402

CRS = 5070
OUT = ROOT / "data" / "processed" / "tod_station_area"
TR = RAW / "tod_station_traits"
SLD_V2 = "/vsizip/" + str(TR / "sld" / "SmartLocationDb_v2.zip") + "/SMARTLOCATIONDB/SmartLocationDb.gdb"
SLD_V3 = "/vsizip/" + str(TR / "sld" / "SmartLocationDatabaseV3.zip") + "/SmartLocationDatabase.gdb"
ABBR = {"06": "ca", "08": "co", "15": "hi", "17": "il", "27": "mn", "36": "ny", "37": "nc", "41": "or", "42": "pa",
        "48": "tx", "49": "ut", "53": "wa", "55": "wi"}
LODES_YEARS = [2004, 2008, 2010, 2013, 2015, 2016, 2019, 2020, 2022]


def case_year(case: str) -> int:
    import build_tod_station_lot_table as B
    cfg = {**B.CASES, **{k: v for k, (_, v) in B.adapter_cases().items()}}[case]
    return int(cfg.get("eff", cfg["after"][0] - 1))


@lru_cache(maxsize=None)
def sld(version: int, state: str) -> gpd.GeoDataFrame:
    if version == 2:
        cols = ["GEOID10", "SFIPS", "D4c", "D4d", "D1C", "D5br", "PCT_AO0"]
        g = gpd.read_file(SLD_V2, columns=cols, where=f"SFIPS = '{state}'")
        g = g.rename(columns={"D4c": "sld_transit_freq", "D4d": "sld_transit_freq_sqmi", "D1C": "sld_jobs_per_acre",
                              "D5br": "sld_transit_job_access", "PCT_AO0": "sld_share_no_car"})
        g["sld_walk_index"] = np.nan
    else:
        cols = ["GEOID10", "GEOID20", "STATEFP", "D4C", "D4D", "D1C", "D5BR", "Pct_AO0", "NatWalkInd"]
        g = gpd.read_file(SLD_V3, columns=cols, where=f"STATEFP = '{state}'")
        g = g.rename(columns={"D4C": "sld_transit_freq", "D4D": "sld_transit_freq_sqmi", "D1C": "sld_jobs_per_acre",
                              "D5BR": "sld_transit_job_access", "Pct_AO0": "sld_share_no_car", "NatWalkInd": "sld_walk_index"})
    for c in ("sld_transit_freq", "sld_transit_freq_sqmi", "sld_transit_job_access"):
        g[c] = pd.to_numeric(g[c], errors="coerce").where(lambda s: s > -99999)   # -99999: no transit in the feed
    return g.to_crs(CRS)


@lru_cache(maxsize=None)
def lodes_bg(state: str, year: int) -> pd.Series:
    yr = min(LODES_YEARS, key=lambda y: (abs(y - year), y))
    with gzip.open(TR / "lodes" / f"{ABBR[state]}_wac_S000_JT00_{yr}.csv.gz", "rt") as fh:
        w = pd.read_csv(fh, usecols=["w_geocode", "C000"], dtype={"w_geocode": str})
    return w.groupby(w.w_geocode.str[:12]).C000.sum()


@lru_cache(maxsize=None)
def nrhp() -> gpd.GeoDataFrame:
    g = gpd.read_file(TR / "nrhp" / "nrhp_polygons.geojson").to_crs(CRS)
    g["listed"] = pd.to_datetime(g.CertDate, errors="coerce", unit="ms").dt.year
    return g[["listed", "ResType", "geometry"]]


def enrich(case: str) -> None:
    f = OUT / f"lots_{case}.parquet"
    D = pd.read_parquet(f)
    eff = case_year(case)
    pts = gpd.GeoDataFrame(D[[]], geometry=gpd.points_from_xy(D.x, D.y), crs=CRS)
    # state of each lot from the SLD block groups of candidate states (cheap: a case sits in one or two states)
    states = sorted({s for s in ABBR if s in _states_for(case)})
    # version 3 (2020 schedules) for every case and for Wisconsin: versions 2 and 3 measure transit frequency on different
    # scales (California block groups: median 12.7 vs 4.3; rank correlation 0.57), so mixing them would make the trait
    # mean different things in different cases. Version 2 (2012 schedules) is kept beside it as a check.
    version = 3
    keep = ["sld_transit_freq", "sld_transit_freq_sqmi", "sld_jobs_per_acre", "sld_transit_job_access", "sld_share_no_car", "sld_walk_index"]
    j = pd.concat([gpd.sjoin(pts, sld(version, s)[["GEOID10", *keep, "geometry"]], how="left", predicate="within") for s in states])
    j = j[j.GEOID10.notna() | ~j.index.duplicated(keep=False)]
    j = j[~j.index.duplicated()]
    for c in keep + ["GEOID10"]:
        D[c if c != "GEOID10" else "bg_geoid"] = j[c].reindex(D.index).values
    D["sld_version"] = version
    j2 = pd.concat([gpd.sjoin(pts, sld(2, s)[["sld_transit_freq", "geometry"]], how="left", predicate="within") for s in states])
    D["sld_transit_freq_v2"] = j2[~j2.index.duplicated()]["sld_transit_freq"].reindex(D.index).values
    # job growth in the block group, 5 years before the reform (LODES 8 uses 2020 blocks for every year, so the lot's
    # 2020 block group comes from the version 3 shapes)
    j20 = pd.concat([gpd.sjoin(pts, sld(3, s)[["GEOID20", "geometry"]], how="left", predicate="within") for s in states])
    j20 = j20[~j20.index.duplicated()]
    bg20 = j20.GEOID20.reindex(D.index)
    g = pd.Series(np.nan, index=D.index)
    for s, ix in D.groupby(bg20.str[:2]).groups.items():
        if s not in ABBR:
            continue
        a, b = lodes_bg(s, eff - 1), lodes_bg(s, eff - 6)
        g.loc[ix] = (bg20.loc[ix].map(a) / bg20.loc[ix].map(b).where(lambda v: v > 0) - 1).values
    D["bg_job_growth_5y"] = g.clip(-0.9, 5)
    # historic register
    h = nrhp()
    h = h[h.listed.fillna(0) < eff]
    hj = gpd.sjoin(pts, h[["geometry"]], how="left", predicate="within")
    D["historic"] = hj.index_right.notna().groupby(level=0).any().reindex(D.index).fillna(False).values
    tract_vars(D, pts, eff, states)
    D.to_parquet(f)
    print(case, f"version {version}; block group found {D.bg_geoid.notna().mean():.3f};",
          "medians:", D[keep + ["bg_job_growth_5y"]].median().round(2).to_dict(), f"historic share {D.historic.mean():.3f}")


@lru_cache(maxsize=None)
def _av():
    spec = importlib.util.spec_from_file_location("run_tod_allvars", ROOT / "scripts" / "run_tod_allvars.py")
    AV = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(AV)
    return AV


def tract_vars(D: pd.DataFrame, pts: gpd.GeoDataFrame, eff: int, states: list[str]) -> None:
    """The lot model's tract variables (v_*), 5-year ACS ending the year before the reform (enrich_all's method)."""
    from missing_middleware.tod import allvars as A
    AV = _av()
    y = A.survey_end_year(eff)
    for st in states:
        try:
            cells, ncells, _ = (AV.tbsf_cells if y >= 2021 else AV.seq_cells)(int(y), st)
            shp = AV.tract_shapes(A.tract_vintage(int(y)), st)
            cells = cells.join(shp.set_index("tract")[["ALAND_SQMI"]], how="left")
            parts = A.tract_parts(cells, ncells, int(y))
        except Exception as e:  # noqa: BLE001
            print(f"  tract variables {y} {st}: {type(e).__name__}: {e}")
            continue
        j = gpd.sjoin(pts, shp[["tract", "geometry"]].to_crs(CRS), how="inner", predicate="within")
        j = j[~j.index.duplicated()]
        for v in A.VARIABLES:
            n, d = parts[v["id"] + "__num"], parts[v["id"] + "__den"]
            val = (n / d.where(d > 0)) if v["kind"] == "ratio" else n
            D.loc[j.index, f"v_{v['id']}"] = j["tract"].map(val).values
    vcols = [c for c in D.columns if c.startswith("v_")]
    print(f"  tract variables: {len(vcols)} columns; share of lots filled (median over variables) "
          f"{float(D[vcols].notna().mean().median()) if vcols else 0:.3f}")


def _states_for(case: str) -> set[str]:
    m = {"la": "06", "san_diego": "06", "honolulu": "15", "denver": "08", "portland": "41", "austin": "48", "slc": "49",
         "seattle": "53", "bellevue": "53", "stpaul": "27", "charlotte": "37", "chicago": "17", "nyc": "36", "phl": "42",
         "philadelphia": "42", "wi": "55", "milwaukee": "55", "madison": "55"}
    return {v for k, v in m.items() if case.startswith(k)} or set(ABBR)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args(argv)
    cases = [p.stem.removeprefix("lots_") for p in sorted(OUT.glob("lots_*.parquet"))] if a.all else [a.case]
    for c in cases:
        enrich(c)


if __name__ == "__main__":
    main()
