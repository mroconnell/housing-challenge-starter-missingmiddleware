"""2000 census blocks: Old City's 2006 height cap, and before-trends for every census case.

    uv run --all-extras python scripts/run_tod_census2000.py

Plan: docs/tod/CENSUS2000_PLAN.md (written before counting). Fetches the 2000 Summary File 1 geographic headers
(public domain) into data/raw/census_sf1_2000/ (housing units HU100, internal point and land area are in the header).
Writes reference/tod_old_city_2006.csv and reference/tod_census2000_trends.csv.
"""
from __future__ import annotations

import io
import pickle
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.paths import PROCESSED, RAW, REFERENCE  # noqa: E402
from scripts import run_tod_census_cases as R  # noqa: E402
from scripts.fetch_tod_cases import Manifest, download_file  # noqa: E402

D = RAW / "census_sf1_2000"
SF1 = "https://www2.census.gov/census_2000/datasets/Summary_File_1"
STATES = {"42": ("Pennsylvania", "pa"), "34": ("New_Jersey", "nj"), "06": ("California", "ca"), "04": ("Arizona", "az"),
          "51": ("Virginia", "va"), "48": ("Texas", "tx"), "53": ("Washington", "wa"), "36": ("New_York", "ny"),
          "17": ("Illinois", "il"), "27": ("Minnesota", "mn"), "49": ("Utah", "ut"), "37": ("North_Carolina", "nc")}
SEED, DRAWS = 20261034, 2000
OVERLAYS = "https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services/Zoning_Overlays/FeatureServer/0"


def fetch() -> None:
    man = Manifest(D, "census_sf1_2000", "US Census Bureau")
    for st, (folder, ab) in STATES.items():
        download_file(man, f"{ab}geo_uf1.zip", f"{SF1}/{folder}/{ab}geo_uf1.zip", False, "US Census Bureau, public domain")
    if not man.have("old_city_overlay.geojson", False):
        from scripts.fetch_tod_census_cases import arcgis_geojson
        data, url = arcgis_geojson(OVERLAYS, "overlay_name LIKE '%Old City Residential%'")
        man.record("old_city_overlay.geojson", data, url, licence="City of Philadelphia open data")


def points_2000(st: str) -> gpd.GeoDataFrame:
    f = R.CACHE / f"blocks_{st}_2000.parquet"
    if f.exists():
        return gpd.read_parquet(f)
    ab = STATES[st][1]
    rows = []
    with zipfile.ZipFile(D / f"{ab}geo_uf1.zip") as z:
        name = z.namelist()[0]
        for line in io.TextIOWrapper(z.open(name), encoding="latin-1"):
            if line[8:11] == "101" and line[11:13] == "00":
                rows.append((float(line[301:310]), float(line[172:186]), float(line[310:319]) / 1e6, float(line[319:329]) / 1e6))
    d = pd.DataFrame(rows, columns=["homes", "land", "lat", "lon"])
    g = gpd.GeoDataFrame(d[["homes", "land"]], geometry=gpd.points_from_xy(d.lon, d.lat), crs=4269).to_crs(R.CRS)
    g.to_parquet(f)
    return g


def three(st: str, treated, comp):
    out = {}
    for y in (2000, 2010, 2020):
        p = points_2000(st) if y == 2000 else R.block_points(st, y)
        out[y] = (p[R.within(p, treated)], p[R.within(p, comp)])
    return out


def per_acre(a, b):
    acres = (a["land"].sum() + b["land"].sum()) / 2 / R.ACRE
    return (b["homes"].sum() - a["homes"].sum()) / acres if acres > 0 else np.nan


def diffs(g) -> tuple[float, float]:
    """(2000-2010 difference, 2010-2020 difference), treated minus comparison, net homes per acre per decade."""
    (t0, c0), (t1, c1), (t2, c2) = g[2000], g[2010], g[2020]
    return per_acre(t0, t1) - per_acre(c0, c1), per_acre(t1, t2) - per_acre(c1, c2)


def boot(g, rng) -> tuple[float, float, float, float]:
    vals = np.empty((DRAWS, 2))
    for i in range(DRAWS):
        gg = {y: tuple(x.iloc[rng.integers(0, len(x), len(x))] if len(x) else x for x in g[y]) for y in g}
        vals[i] = diffs(gg)
    cic = vals[:, 1] - vals[:, 0]
    lo0, hi0 = np.nanquantile(vals[:, 0], [0.05, 0.95])
    lo, hi = np.nanquantile(cic, [0.05, 0.95])
    return lo0, hi0, lo, hi


def old_city(rng) -> dict:
    ov = gpd.read_file(D / "old_city_overlay.geojson").to_crs(R.CRS)
    treated = ov.geometry.make_valid().union_all()
    comp = treated.buffer(R.HALF).difference(treated)
    g = three("42", treated, comp)
    d0, d1 = diffs(g)
    lo0, hi0, lo, hi = boot(g, rng)
    t = g
    return {"case": "philadelphia_old_city_height_cap_2006", "overlay_parts": "; ".join(sorted(ov["overlay_name"].astype(str).unique())),
            "treated_acres_2010": t[2010][0]["land"].sum() / R.ACRE,
            "treated_homes_2000": t[2000][0]["homes"].sum(), "treated_homes_2010": t[2010][0]["homes"].sum(),
            "treated_homes_2020": t[2020][0]["homes"].sum(),
            "comparison_homes_2000": t[2000][1]["homes"].sum(), "comparison_homes_2010": t[2010][1]["homes"].sum(),
            "comparison_homes_2020": t[2020][1]["homes"].sum(),
            "diff_2000_2010_per_acre": d0, "diff_2000_2010_low": lo0, "diff_2000_2010_high": hi0,
            "diff_2010_2020_per_acre": d1, "change_in_change": d1 - d0, "low": lo, "high": hi}


def census_set_areas():
    """Treated and comparison areas of every census-set reform, as in run_tod_census_predict.units()."""
    from scripts.run_tod_census_share import slc_boundary
    out = []
    geoms = {c: R.boundary(c) for c in R.NEW_CASES}
    geoms["salt_lake_city_tsa_2010"] = slc_boundary()
    every = unary_union([g[1] for g in geoms.values()])
    adopted = {"jersey_city_journal_square_2010": 2010, "milpitas_tasp_2008": 2008, "phoenix_wu_2015_2016": 2015,
               "bellevue_belred_2009": 2009, "austin_tod_station_plans": 2007, "tysons_2010": 2010, "salt_lake_city_tsa_2010": 2010}
    for c, (t, ex) in geoms.items():
        st = "49" if c == "salt_lake_city_tsa_2010" else R.NEW_CASES[c][0]
        out.append((c, st, adopted[c], t, t.buffer(R.HALF).difference(every).difference(ex)))
    cases = {"stpaul_green_line_2011": ("27", 2011), "seattle_nbh_othello_2012": ("53", 2012), "seattle_mount_baker_2014": ("53", 2014),
             "la_warner_center_2013": ("06", 2013), "la_cornfield_arroyo_seco_2013": ("06", 2013), "chicago_tod_2013_2015": ("17", 2013),
             "philadelphia_2012_remapping": ("42", 2012)}
    for c, (st, yr) in cases.items():
        mem = pickle.loads((PROCESSED / "tod_net_effect" / f"areas_{c}.pkl").read_bytes())
        to = lambda g, crs: gpd.GeoSeries([g], crs=crs).to_crs(R.CRS).iloc[0]  # noqa: E731
        t = unary_union([to(m["treated_union"], m["crs"]) for m in mem])
        u = unary_union([to(m["upzoned_union"], m["crs"]) for m in mem])
        out.append((c, st, yr, t, u.buffer(R.QUARTER).difference(u)))
    for m in pickle.loads((PROCESSED / "tod_net_effect" / "areas_nyc_pooled_2003_2013.pkl").read_bytes()):
        if 2008 <= m["effective_year"] <= 2013:
            to = lambda g: gpd.GeoSeries([g], crs=m["crs"]).to_crs(R.CRS).iloc[0]  # noqa: E731
            u = to(m["upzoned_union"])
            out.append((f"nyc_{m.get('id')}", "36", m["effective_year"], to(m["treated_union"]), u.buffer(R.QUARTER).difference(u)))
    z = gpd.read_file(RAW / "tod_cases" / "seattle" / "zoning_current.geojson").to_crs(R.CRS)
    rv = z[z["ZONINGHISTORY"].astype(str).str.contains("ORD123816")].geometry.make_valid().union_all()
    out.append(("seattle_roosevelt_2012", "53", 2012, rv, rv.buffer(R.HALF).difference(rv)))
    return out


def main() -> None:
    fetch()
    rng = np.random.default_rng(SEED)
    oc = old_city(rng)
    pd.DataFrame([oc]).round(4).to_csv(REFERENCE / "tod_old_city_2006.csv", index=False)
    print(pd.Series(oc).to_string())
    rows = []
    for c, st, yr, t, comp in census_set_areas():
        g = three(st, t, comp)
        if not len(g[2010][0]) or not len(g[2000][0]):
            rows.append({"case": c, "adopted": yr, "note": "no blocks in treated land"})
            continue
        d0, d1 = diffs(g)
        lo0, hi0, lo, hi = boot(g, rng)
        rows.append({"case": c, "adopted": yr, "diff_2000_2010_per_acre": d0, "diff_2000_2010_low": lo0, "diff_2000_2010_high": hi0,
                     "diff_2010_2020_per_acre": d1, "change_in_change": d1 - d0, "cic_low": lo, "cic_high": hi,
                     "before_decade_partly_after_adoption": yr < 2010,
                     "pretrend_within_1": abs(d0) <= 1.0})
        print(f"{c}: done", flush=True)
    tr = pd.DataFrame(rows)
    tr.round(4).to_csv(REFERENCE / "tod_census2000_trends.csv", index=False)
    pd.set_option("display.width", 250)
    print(tr.round(2).to_string())


if __name__ == "__main__":
    main()
