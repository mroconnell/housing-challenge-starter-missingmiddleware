"""Near-transit prediction test (docs/parking/NEAR_TRANSIT_PREDICT_PLAN.md).

    uv run --all-extras python scripts/run_parking_near_transit_predict.py

Units: Seattle urban villages, Minneapolis light-rail station areas (census blocks 2000/2010/2020, via TOD's block
points) and California AB 2097 jurisdictions (reference/tod_ab2097_by_jurisdiction.csv).
Outputs: reference/parking_near_transit_units.csv, reference/parking_near_transit_predict.csv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from scripts import run_parking_block_catalog as B  # noqa: E402
from scripts import run_tod_census2000 as T  # noqa: E402
from scripts import run_tod_census_cases as R  # noqa: E402

SEED, FOLDS, REPEATS, MIN_GAIN = 20261028, 10, 20, 0.05
CENSUS_TO_PERMITS = 0.86
FEATURES = ["rail", "log_homes", "prior_gap"]


def growth(a, b):
    return (b["homes"].sum() - a["homes"].sum()) / a["homes"].sum() * 100 if a["homes"].sum() > 0 else np.nan


def city_units(st, region, units: dict, comp, rail_pts) -> list[dict]:
    pts = {y: (T.points_2000(st) if y == 2000 else R.block_points(st, y)) for y in (2000, 2010, 2020)}
    cm = {y: pts[y][R.within(pts[y], comp)] for y in pts}
    cg0, cg1 = growth(cm[2000], cm[2010]), growth(cm[2010], cm[2020])
    rows = []
    for name, geom in units.items():
        t = {y: pts[y][R.within(pts[y], geom)] for y in pts}
        if t[2010]["homes"].sum() < 100 or t[2000]["homes"].sum() < 100:
            continue
        g0, g1 = growth(t[2000], t[2010]), growth(t[2010], t[2020])
        rows.append(dict(region=region, unit=name, homes=t[2010]["homes"].sum(), rail=float(rail_pts.within(geom).any()),
                         prior_gap=(g0 - cg0) / CENSUS_TO_PERMITS, outcome=((g1 - cg1) - (g0 - cg0)) / CENSUS_TO_PERMITS))
    return rows


def build_units() -> pd.DataFrame:
    stops = B.stops()
    rail = stops[stops["stop_type_text"].astype(str).str.contains("rail|Rail|Tram|Subway|Metro")]
    rows = []
    # Seattle villages
    v = gpd.read_file(B.OLD / "seattle_urban_villages.geojson").to_crs(R.CRS)
    sea = B.place("53", "5363000")
    vil = v[v["UV_TYPE"].isin(["HUV", "RUV"])]
    other = v[v["UV_TYPE"].isin(["UC", "MIC"])].geometry.union_all()
    comp = sea.difference(vil.geometry.union_all()).difference(other)
    rows += city_units("53", "Seattle", {r.UV_NAME: r.geometry.intersection(sea) for r in vil.itertuples()}, comp, rail.geometry)
    # Minneapolis station areas (nearest-station assignment within 1/2 mile, downtown left out)
    mpls = B.place("27", "2743000")
    dt = B.pt(*B.MPLS_DOWNTOWN).buffer(1500)
    s = rail[rail.within(mpls)].copy()
    s["key"] = s["stop_name"].str.replace(r"\s*(Station|Platform).*$", "", regex=True).str.strip()
    s = s.dissolve("key").reset_index()
    s["geometry"] = s.geometry.centroid
    vor = s.geometry.voronoi_polygons() if hasattr(s.geometry, "voronoi_polygons") else None
    from shapely.ops import voronoi_diagram
    cells = gpd.GeoSeries(list(voronoi_diagram(s.geometry.union_all(), envelope=mpls.buffer(5000)).geoms), crs=R.CRS)
    units = {}
    for r in s.itertuples():
        cell = cells[cells.contains(r.geometry)].union_all()
        units[r.key] = r.geometry.buffer(B.MILE / 2).intersection(cell).intersection(mpls).difference(dt)
    near = gpd.GeoSeries(list(units.values()), crs=R.CRS).union_all()
    rows += city_units("27", "Minneapolis", units, mpls.difference(near).difference(dt), rail.geometry)
    # California AB 2097 jurisdictions
    ca = pd.read_csv(REFERENCE / "tod_ab2097_by_jurisdiction.csv")
    pl = gpd.read_file(f"zip://{B.TOD_DIR}/tl_2020_06_place.zip").to_crs(R.CRS)
    co = gpd.read_file(f"zip://{RAW / 'census_tiger_2024' / 'tl_2024_us_county.zip'}")
    co = co[co["STATEFP"] == "06"].to_crs(R.CRS)
    rca = rail[rail.geometry.y < 0] if False else rail
    for r in ca.itertuples():
        nm = r.jurisdiction
        if nm.endswith(" COUNTY"):
            g = co[co["NAME"].str.upper() == nm.replace(" COUNTY", "")]
        else:
            g = pl[pl["NAME"].str.upper() == nm]
        has_rail = float(rca.within(g.geometry.union_all()).any()) if len(g) else np.nan
        rows.append(dict(region="California", unit=nm, homes=r.homes_near_transit_2020, rail=has_rail,
                         prior_gap=r.near_rate_before - r.ring_rate_before, outcome=r.did_per_1000_homes_per_year))
    u = pd.DataFrame(rows)
    u["log_homes"] = np.log10(u["homes"])
    return u


def predict(tool, tr, te, rng):
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LassoCV, LinearRegression
    from sklearn.preprocessing import StandardScaler
    w = tr["homes"].values
    if tool == "one average":
        return np.full(len(te), np.average(tr["outcome"], weights=w))
    med = tr[FEATURES].median()
    X, Xt = tr[FEATURES].fillna(med).values, te[FEATURES].fillna(med).values
    sc = StandardScaler().fit(X)
    X, Xt = sc.transform(X), sc.transform(Xt)
    y = tr["outcome"].values
    if tool == "weighted regression":
        return LinearRegression().fit(X, y, sample_weight=w).predict(Xt)
    if tool == "lasso":
        return LassoCV(cv=min(5, len(tr)), random_state=int(rng.integers(1e9))).fit(X, y, sample_weight=w).predict(Xt)
    if tool == "random forest":
        return RandomForestRegressor(n_estimators=300, min_samples_leaf=5, random_state=int(rng.integers(1e9))).fit(X, y, sample_weight=w).predict(Xt)
    raise ValueError(tool)


def wmae(p, te):
    return float(np.average(np.abs(p - te["outcome"].values), weights=te["homes"].values))


def main() -> None:
    u = build_units()
    u.round(4).to_csv(REFERENCE / "parking_near_transit_units.csv", index=False)
    print(u.groupby("region").agg(units=("unit", "size"), homes=("homes", "sum"), rail=("rail", "mean"),
                                  outcome=("outcome", lambda s: np.average(s, weights=u.loc[s.index, "homes"]))).round(2))
    rng = np.random.default_rng(SEED)
    tools = ["one average", "weighted regression", "lasso", "random forest"]
    rows = []
    pooled = {t: [] for t in tools}
    for hold in ("Seattle", "Minneapolis", "California"):
        tr, te = u[u["region"] != hold], u[u["region"] == hold]
        errs = {t: wmae(predict(t, tr, te, rng), te) for t in tools}
        for t in tools:
            pooled[t].append(errs[t] * te["homes"].sum())
            rows.append(dict(test="leave one region out", held_out=hold, tool=t, error=errs[t],
                             gain=1 - errs[t] / errs["one average"]))
    tot = u["homes"].sum()
    for t in tools:
        rows.append(dict(test="leave one region out", held_out="all, pooled", tool=t, error=sum(pooled[t]) / tot,
                         gain=1 - sum(pooled[t]) / sum(pooled["one average"])))
    # within-region cross-validation
    for reg in ("Seattle", "Minneapolis", "California"):
        d = u[u["region"] == reg].reset_index(drop=True)
        k = min(FOLDS, len(d))
        per = {t: [] for t in tools}
        for _ in range(REPEATS):
            perm = rng.permutation(len(d))
            e = {t: 0.0 for t in tools}
            for f in range(k):
                te = d.iloc[perm[f::k]]
                tr = d.drop(te.index)
                for t in tools:
                    e[t] += wmae(predict(t, tr, te, rng), te) * te["homes"].sum()
            for t in tools:
                per[t].append(e[t] / d["homes"].sum())
        for t in tools:
            rows.append(dict(test="within region, 10-fold x 20", held_out=reg, tool=t, error=float(np.mean(per[t])),
                             gain=1 - np.mean(per[t]) / np.mean(per["one average"])))
    r = pd.DataFrame(rows)
    lo = r[(r["test"] == "leave one region out") & (r["held_out"] != "all, pooled")]
    passes = {t: bool(((lo[lo["tool"] == t]["gain"] >= MIN_GAIN).sum() >= 2)
                      and (r[(r["held_out"] == "all, pooled") & (r["tool"] == t)]["gain"].iloc[0] >= MIN_GAIN)) for t in tools[1:]}
    r["passes_rule"] = r["tool"].map(passes)
    r.round(4).to_csv(REFERENCE / "parking_near_transit_predict.csv", index=False)
    pd.set_option("display.width", 200)
    print(r.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
