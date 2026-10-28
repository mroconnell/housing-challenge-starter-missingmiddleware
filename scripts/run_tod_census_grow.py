"""Grow the census set (New York 2008-2013, Seattle Roosevelt, existing cases) and measure placebo rail stations.

    uv run --all-extras python scripts/fetch_tod_census_cases.py
    uv run --all-extras python scripts/run_tod_census_grow.py

Plan: docs/tod/CENSUS_CASES_PLAN.md section 10 (written before running).
Writes reference/tod_census_set.csv (every census-measured reform) and reference/tod_census_placebos.csv.
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import PROCESSED, RAW, REFERENCE  # noqa: E402
from missing_middleware.tod.control_cities import inventory_geoids, read_gazetteer  # noqa: E402
from scripts import run_tod_census_cases as R  # noqa: E402
from scripts.run_tod_census_share import slc_boundary  # noqa: E402

SEED = 20261032
MILE = 1609.344
STATES = ["34", "06", "04", "51", "48", "53", "39", "36", "17", "27", "37", "42", "49"]


def polys(st: str, year: int) -> gpd.GeoDataFrame:
    f = R.CACHE / f"polys_{st}_{year}.parquet"
    if f.exists():
        return gpd.read_parquet(f)
    if st == "49":
        src = RAW / "tod_slc" / ("tabblock2010_49_pophu.zip" if year == 2010 else "tl_2020_49_tabblock20.zip")
    else:
        src = R.D / (f"tabblock2010_{st}_pophu.zip" if year == 2010 else f"tl_2020_{st}_tabblock20.zip")
    b = gpd.read_file(src).rename(columns={"HOUSING10": "homes", "HOUSING20": "homes"}).to_crs(R.CRS)
    out = gpd.GeoDataFrame({"homes": b["homes"].astype(float).values, "land": b.area.values}, geometry=b.geometry.values, crs=R.CRS)
    out = out[out["land"] > 0]
    out.to_parquet(f)
    return out


def share_sums(b: gpd.GeoDataFrame, geom) -> tuple[float, float]:
    idx = b.sindex.query(geom, predicate="intersects")
    if not len(idx):
        return 0.0, 0.0
    sub = b.iloc[idx]
    s = np.clip(sub.geometry.intersection(geom).area.values / sub["land"].values, 0, 1)
    return float((sub["homes"].values * s).sum()), float((sub["land"].values * s).sum())


def area_share_diff(b10, b20, treated, comp) -> dict:
    th10, tl10 = share_sums(b10, treated)
    th20, tl20 = share_sums(b20, treated)
    ch10, cl10 = share_sums(b10, comp)
    ch20, cl20 = share_sums(b20, comp)
    ta, ca = (tl10 + tl20) / 2 / R.ACRE, (cl10 + cl20) / 2 / R.ACRE
    t = (th20 - th10) / ta if ta else np.nan
    c = (ch20 - ch10) / ca if ca else np.nan
    return {"treated_acres": ta, "treated_homes_2010": th10, "treated_homes_2020": th20,
            "pre_density_homes_per_acre_2010": th10 / ta if ta else np.nan,
            "treated_per_acre_decade": t, "comparison_per_acre_decade": c, "difference_per_acre_decade": t - c}


def nyc_members(rng) -> list[dict]:
    members = pickle.loads((PROCESSED / "tod_net_effect" / "areas_nyc_pooled_2003_2013.pkl").read_bytes())
    p10, p20 = R.block_points("36", 2010), R.block_points("36", 2020)
    rows = []
    for m in members:
        if not 2008 <= m["effective_year"] <= 2013:
            continue
        to = lambda g: gpd.GeoSeries([g], crs=m["crs"]).to_crs(R.CRS).iloc[0]  # noqa: E731
        treated, upz = to(m["treated_union"]), to(m["upzoned_union"])
        ring = upz.buffer(R.QUARTER).difference(upz)
        t10, t20, c10, c20 = p10[R.within(p10, treated)], p20[R.within(p20, treated)], p10[R.within(p10, ring)], p20[R.within(p20, ring)]
        est, lo, hi = R.diff_with_interval(t10, t20, c10, c20, rng)
        acres = (t10["land"].sum() + t20["land"].sum()) / 2 / R.ACRE
        rows.append({"case": f"nyc_{m.get('id')}", "label": f"New York rezoning {m.get('id')} ({m['effective_year']})",
                     "source": "census, centre point, ¼-mile ring (plan 10.1)", "adopted": str(m["effective_year"]),
                     "difference_per_acre_decade": est, "low": lo, "high": hi, "treated_acres": acres,
                     "treated_homes_2010": t10["homes"].sum(), "treated_homes_2020": t20["homes"].sum(),
                     "pre_density_homes_per_acre_2010": t10["homes"].sum() / acres if acres else np.nan})
    return rows


def roosevelt(rng) -> dict:
    z = gpd.read_file(RAW / "tod_cases" / "seattle" / "zoning_current.geojson").to_crs(R.CRS)
    treated = z[z["ZONINGHISTORY"].astype(str).str.contains("ORD123816")].geometry.make_valid().union_all()
    ring = treated.buffer(R.HALF).difference(treated)
    p10, p20 = R.block_points("53", 2010), R.block_points("53", 2020)
    t10, t20, c10, c20 = p10[R.within(p10, treated)], p20[R.within(p20, treated)], p10[R.within(p10, ring)], p20[R.within(p20, ring)]
    est, lo, hi = R.diff_with_interval(t10, t20, c10, c20, rng)
    acres = (t10["land"].sum() + t20["land"].sum()) / 2 / R.ACRE
    return {"case": "seattle_roosevelt_2012", "label": "Seattle, Roosevelt rezone (2012)", "adopted": "2012",
            "source": "census, centre point, ½-mile ring (plan 10.1)", "difference_per_acre_decade": est, "low": lo, "high": hi,
            "treated_acres": acres, "treated_homes_2010": t10["homes"].sum(), "treated_homes_2020": t20["homes"].sum(),
            "pre_density_homes_per_acre_2010": t10["homes"].sum() / acres if acres else np.nan}, treated


def reform_geoms() -> list:
    g = [R.boundary(c)[0] for c in R.NEW_CASES] + [slc_boundary()[0]]
    for case in R.METHOD_CASES:
        for m in pickle.loads((PROCESSED / "tod_net_effect" / f"areas_{case}.pkl").read_bytes()):
            g.append(gpd.GeoSeries([m["upzoned_union"]], crs=m["crs"]).to_crs(R.CRS).iloc[0])
    return g


def placebos(extra_geoms) -> pd.DataFrame:
    s = pd.DataFrame(json.load(open(R.D / "ntm_rail_stops.json")))
    s = s.dropna(subset=["stop_lat", "stop_lon"])
    pts = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.stop_lon, s.stop_lat), crs=4326).to_crs(R.CRS)
    # Merge same-name stops within ¼ mile (platforms of one station).
    pts["key"] = pts["stop_name"].str.lower().str.replace(r"\s*\(.*\)|\s+(platform|track|nb|sb|eb|wb)\b.*", "", regex=True).str.strip()
    pts["cell"] = (pts.geometry.x // R.QUARTER).astype(int).astype(str) + "_" + (pts.geometry.y // R.QUARTER).astype(int).astype(str)
    st = pts.groupby(["key", "cell"]).agg(name=("stop_name", "first"), x=("geometry", lambda g: g.x.mean()),
                                         y=("geometry", lambda g: g.y.mean())).reset_index()
    st = gpd.GeoDataFrame(st, geometry=gpd.points_from_xy(st.x, st.y), crs=R.CRS)
    # Leave out inventory cities and anything within 1 mile of a reform in the census set.
    gaz = read_gazetteer(RAW / "tod_control_cities" / "Gaz_places_national.zip")
    inv = inventory_geoids(pd.read_csv(REFERENCE / "tod_cases.csv"), gaz)
    places = pd.concat([gpd.read_file(R.D / f"tl_2020_{x}_place.zip") for x in STATES]).to_crs(R.CRS)
    bad = places[places["GEOID"].isin(inv)].geometry.union_all()
    near = unary_union(extra_geoms).buffer(MILE)
    st = st[~st.within(bad) & ~st.within(near)].reset_index(drop=True)
    pl = gpd.sjoin(st, places[["GEOID", "NAME", "geometry"]], how="left", predicate="within")
    pl = pl[~pl.index.duplicated()]
    st["place"], st["state"] = pl["NAME"].values, pl["GEOID"].astype(str).str[:2].values
    circles = st.geometry.buffer(R.HALF)
    all_circles = circles.union_all()
    rows = []
    for x in STATES:
        sub = st[st["state"] == x]
        if not len(sub):
            continue
        b10, b20 = polys(x, 2010), polys(x, 2020)
        for i, r in sub.iterrows():
            c = circles.iloc[i]
            ring = r.geometry.buffer(MILE).difference(all_circles)
            d = area_share_diff(b10, b20, c, ring)
            rows.append({"station": r["name"], "place": r["place"], "state": x, **d})
        print(f"placebos {x}: {len(sub)}", flush=True)
    return pd.DataFrame(rows)


def main() -> None:
    rng = np.random.default_rng(SEED)
    rows = []
    share = pd.read_csv(REFERENCE / "tod_census_share.csv").set_index("case")
    cases = pd.read_csv(REFERENCE / "tod_census_cases.csv").set_index("case")
    for c, r in share.iterrows():
        label = cases.loc[c, "label"] if c in cases.index else "Salt Lake City, TSA district"
        rows.append({"case": c, "label": label, "source": "census, area share, ½-mile ring (section 9)",
                     "adopted": cases.loc[c, "adopted"] if c in cases.index else "2010",
                     "difference_per_acre_decade": r["area_share_difference_per_acre_decade"], "low": r["area_share_low"],
                     "high": r["area_share_high"], "treated_acres": r["area_share_upzoned_acres"],
                     "treated_homes_2010": r["area_share_upzoned_homes_2010"], "treated_homes_2020": r["area_share_upzoned_homes_2020"],
                     "pre_density_homes_per_acre_2010": r["area_share_upzoned_homes_2010"] / r["area_share_upzoned_acres"]})
    m = pd.read_csv(REFERENCE / "tod_census_method_check.csv")
    for r in m.dropna(subset=["census_difference_per_acre_decade"]).itertuples():
        rows.append({"case": r.case, "label": r.case.replace("_", " "), "source": "census, centre point, ¼-mile ring (method check)",
                     "adopted": "2019 (land only)" if r.case.startswith("charlotte") else "",
                     "difference_per_acre_decade": r.census_difference_per_acre_decade, "low": r.census_low, "high": r.census_high,
                     "land_only": r.case.startswith("charlotte")})
    rows += nyc_members(rng)
    rv, rv_geom = roosevelt(rng)
    rows.append(rv)
    cs = pd.DataFrame(rows)
    pl = placebos(reform_geoms() + [rv_geom])
    pl.round(4).to_csv(REFERENCE / "tod_census_placebos.csv", index=False)
    vals = pl["difference_per_acre_decade"].dropna().to_numpy()
    cs["share_of_placebos_larger"] = [float((vals > v).mean()) if pd.notna(v) else np.nan for v in cs["difference_per_acre_decade"]]
    cs["beats_90pct_of_placebos"] = cs["share_of_placebos_larger"] < 0.10
    cs.round(4).to_csv(REFERENCE / "tod_census_set.csv", index=False)
    pd.set_option("display.width", 250)
    print(f"placebos: {len(vals)}; median {np.median(vals):.2f}; 5-95%: {np.quantile(vals, 0.05):.2f} to {np.quantile(vals, 0.95):.2f}")
    print(cs[["case", "adopted", "difference_per_acre_decade", "low", "high", "pre_density_homes_per_acre_2010",
              "share_of_placebos_larger"]].round(2).to_string())


if __name__ == "__main__":
    main()
