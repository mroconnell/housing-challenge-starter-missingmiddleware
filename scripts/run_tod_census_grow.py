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

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware import geom_extra_foundation as GF  # noqa: E402
from missing_middleware import geom_extra_station as S  # noqa: E402
from missing_middleware import geom_extra_tod as X  # noqa: E402
from missing_middleware.paths import PROCESSED, RAW, REFERENCE  # noqa: E402
from missing_middleware.tod.control_cities import inventory_geoids, read_gazetteer  # noqa: E402
from scripts import run_tod_census_cases as R  # noqa: E402
from scripts.run_tod_census_share import slc_boundary  # noqa: E402

SEED = 20261032
MILE = 1609.344
STATES = ["34", "06", "04", "51", "48", "53", "39", "36", "17", "27", "37", "42", "49"]


def polys(st: str, year: int, boxes) -> pd.DataFrame:
    """A state's census blocks with land (m2 > 0) whose bounds meet any of the boxes (R.CRS): homes, land, "geometry"
    (polygon features in R.CRS) and bounds b0-b3. Cached per state as GeoParquet (all blocks)."""
    f = R.CACHE / f"polys_{st}_{year}.parquet"
    if not f.exists():
        if st == "49":
            src = RAW / "tod_slc" / ("tabblock2010_49_pophu.zip" if year == 2010 else "tl_2020_49_tabblock20.zip")
        else:
            src = R.D / (f"tabblock2010_{st}_pophu.zip" if year == 2010 else f"tl_2020_{st}_tabblock20.zip")
        col = "HOUSING10" if year == 2010 else "HOUSING20"
        b = S.read_vector(src, R.CRS, columns=[col])
        g = list(b["geometry"])
        out = pd.DataFrame({"homes": b[col].astype(float).values, "land": S.areas(g)})
        keep = out["land"].to_numpy() > 0
        g = [x for x, k in zip(g, keep) if k]
        GF.write_geoparquet(out[keep], g, ["Polygon" if len(x) == 1 else "MultiPolygon" for x in g], f, R.CRS)
    a, g, _ = GF.read_geoparquet_near(f, boxes)
    bb = S.feature_bounds(g)
    return a.assign(geometry=g, b0=bb[:, 0], b1=bb[:, 1], b2=bb[:, 2], b3=bb[:, 3])


def share_sums(b: pd.DataFrame, region, box) -> tuple[float, float]:
    """Homes and land of the blocks weighted by the share of each block's land inside the region (box: the region's
    bounds; blocks outside it share nothing)."""
    m = ((b["b0"] <= box[2]) & (b["b2"] >= box[0]) & (b["b1"] <= box[3]) & (b["b3"] >= box[1])).to_numpy()
    if not m.any():
        return 0.0, 0.0
    sub = b[m]
    s = np.clip(X.overlap_areas(list(sub["geometry"]), region) / sub["land"].values, 0, 1)
    return float((sub["homes"].values * s).sum()), float((sub["land"].values * s).sum())


def area_share_diff(b10, b20, treated, comp, tbox, cbox) -> dict:
    th10, tl10 = share_sums(b10, treated, tbox)
    th20, tl20 = share_sums(b20, treated, tbox)
    ch10, cl10 = share_sums(b10, comp, cbox)
    ch20, cl20 = share_sums(b20, comp, cbox)
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
        treated, upz = R.union(R.member_polys(m, "treated_union")), R.member_polys(m, "upzoned_union")
        ring = R.ring(upz, R.QUARTER, R.union(upz))
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
    z = R.layer(RAW / "tod_cases" / "seattle" / "zoning_current.geojson")
    rv = R.valid(z[z["ZONINGHISTORY"].astype(str).str.contains("ORD123816")])
    treated = X.Polygons(rv)
    ring = R.ring(rv, R.HALF, treated)
    p10, p20 = R.block_points("53", 2010), R.block_points("53", 2020)
    t10, t20, c10, c20 = p10[R.within(p10, treated)], p20[R.within(p20, treated)], p10[R.within(p10, ring)], p20[R.within(p20, ring)]
    est, lo, hi = R.diff_with_interval(t10, t20, c10, c20, rng)
    acres = (t10["land"].sum() + t20["land"].sum()) / 2 / R.ACRE
    return {"case": "seattle_roosevelt_2012", "label": "Seattle, Roosevelt rezone (2012)", "adopted": "2012",
            "source": "census, centre point, ½-mile ring (plan 10.1)", "difference_per_acre_decade": est, "low": lo, "high": hi,
            "treated_acres": acres, "treated_homes_2010": t10["homes"].sum(), "treated_homes_2020": t20["homes"].sum(),
            "pre_density_homes_per_acre_2010": t10["homes"].sum() / acres if acres else np.nan}, rv


def reform_geoms() -> list:
    """Every census-set reform's land: a list of polygon-feature lists in R.CRS."""
    g = [R.boundary(c)[0] for c in R.NEW_CASES] + [slc_boundary()[0]]
    for case in R.METHOD_CASES:
        for m in pickle.loads((PROCESSED / "tod_net_effect" / f"areas_{case}.pkl").read_bytes()):
            g.append(R.member_polys(m, "upzoned_union"))
    return g


def circle(x: float, y: float, r: float) -> list:
    """A point's GEOS buffer (64-gon) as a polygon feature."""
    return [[S._circle(x, y, r)]]


def placebos(extra_geoms) -> pd.DataFrame:
    s = pd.DataFrame(json.load(open(R.D / "ntm_rail_stops.json")))
    s = s.dropna(subset=["stop_lat", "stop_lon"])
    px, py = S.transform(s["stop_lon"].to_numpy(float), s["stop_lat"].to_numpy(float), 4326, R.CRS)
    pts = s.assign(gx=px, gy=py)
    # Merge same-name stops within ¼ mile (platforms of one station).
    pts["key"] = pts["stop_name"].str.lower().str.replace(r"\s*\(.*\)|\s+(platform|track|nb|sb|eb|wb)\b.*", "", regex=True).str.strip()
    pts["cell"] = (pts["gx"] // R.QUARTER).astype(int).astype(str) + "_" + (pts["gy"] // R.QUARTER).astype(int).astype(str)
    st = pts.groupby(["key", "cell"]).agg(name=("stop_name", "first"), x=("gx", lambda g: g.mean()),
                                         y=("gy", lambda g: g.mean())).reset_index()
    # Leave out inventory cities and anything within 1 mile of a reform in the census set.
    gaz = read_gazetteer(RAW / "tod_control_cities" / "Gaz_places_national.zip")
    inv = inventory_geoids(pd.read_csv(REFERENCE / "tod_cases.csv"), gaz)
    places = pd.concat([S.read_vector(R.D / f"tl_2020_{x}_place.zip", R.CRS, columns=["GEOID", "NAME"]) for x in STATES],
                       ignore_index=True)
    bad = R.union(list(places.loc[places["GEOID"].isin(inv), "geometry"]))
    near = X.Buffer([f for g in extra_geoms for f in g], MILE)
    sx, sy = st["x"].to_numpy(float), st["y"].to_numpy(float)
    st = st[~bad.contains(sx, sy) & ~near.contains(sx, sy)].reset_index(drop=True)
    k = S.first_within(st["x"].to_numpy(float), st["y"].to_numpy(float), list(places["geometry"]))
    st["place"] = np.where(k >= 0, places["NAME"].to_numpy(object)[np.maximum(k, 0)], np.nan)
    st["state"] = np.where(k >= 0, places["GEOID"].astype(str).to_numpy(object)[np.maximum(k, 0)], "nan")
    st["state"] = st["state"].str[:2]
    circles = [circle(x, y, R.HALF) for x, y in zip(st["x"], st["y"])]
    ctree = cKDTree(st[["x", "y"]].to_numpy(float))
    rows = []
    for x in STATES:
        sub = st[st["state"] == x]
        if not len(sub):
            continue
        boxes = np.c_[sub["x"] - MILE - 1, sub["y"] - MILE - 1, sub["x"] + MILE + 1, sub["y"] + MILE + 1]
        b10, b20 = polys(x, 2010, boxes), polys(x, 2020, boxes)
        for i, r in sub.iterrows():
            c = X.Polygons([circles[i]])
            # the ring: the 1-mile circle less every station's ½-mile circle (only circles that can reach it matter)
            others = X.Polygons([circles[j] for j in sorted(ctree.query_ball_point([r["x"], r["y"]], MILE + R.HALF + 1))])
            ring = X.Polygons([circle(r["x"], r["y"], MILE)]) - others
            tb = (r["x"] - R.HALF, r["y"] - R.HALF, r["x"] + R.HALF, r["y"] + R.HALF)
            cb = (r["x"] - MILE, r["y"] - MILE, r["x"] + MILE, r["y"] + MILE)
            d = area_share_diff(b10, b20, c, ring, tb, cb)
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
