"""Five-city (now four-city) parking lot test (docs/parking/LOT_CITIES_PLAN.md).

    uv run python scripts/fetch_parking_lot_cities.py
    uv run --all-extras python scripts/run_parking_lot_cities.py

Outputs (aggregates only): reference/parking_lot_cities_effects.csv, reference/parking_lot_cities_predict.csv
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

from missing_middleware.parking import checks  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from scripts import run_parking_block_catalog as B  # noqa: E402
from scripts import run_parking_lot_test as LT  # noqa: E402

D = RAW / "parking_lot_cities"
SEED, DRAWS, CELL, CRS = 20261028, 2000, 500.0, 5070
SF_PINCHED = {"RH-2", "RH-3", "RM-1", "RM-2", "RM-3", "RM-4", "NC-1", "NC-2", "NC-3", "NC-S", "RC-3", "RC-4"}
SF_COMPARE = {"RH-1", "RH-1(D)"}
WIN = {"San Francisco": (range(2014, 2019), range(2020, 2025)), "Buffalo": (range(2012, 2017), range(2018, 2023)),
       "Chicago": (range(2009, 2013), range(2016, 2021))}


def rail_points():
    s = B.stops()
    return s[s["stop_type_text"].astype(str).str.contains("rail|Rail|Tram|Subway|Metro")]


def dist_to(rail, pts):
    j = gpd.sjoin_nearest(pts[["geometry"]], rail[["geometry"]], how="left", distance_col="d")
    return j.groupby(level=0)["d"].min().reindex(pts.index).values


def width_of(geoms):
    out = []
    for g in geoms:
        try:
            r = g.minimum_rotated_rectangle
            xs, ys = r.exterior.coords.xy
            e = [((xs[i + 1] - xs[i]) ** 2 + (ys[i + 1] - ys[i]) ** 2) ** 0.5 for i in range(2)]
            out.append(min(e))
        except Exception:  # noqa: BLE001
            out.append(np.nan)
    return np.array(out)


def per_lot_years(perm: pd.DataFrame, key: str) -> dict:
    return {k: g.groupby("year")["net"].sum().to_dict() for k, g in perm.groupby(key)}


def sf() -> pd.DataFrame:
    g = gpd.read_file(D / "sf_parcels.geojson")
    g = g[g["zoning_code"].isin(SF_PINCHED | SF_COMPARE)].to_crs(CRS).reset_index(drop=True)
    g["pinched"] = g["zoning_code"].isin(SF_PINCHED).astype(float)
    g["acres"] = g.geometry.area / 4046.8564
    g["width_m"] = width_of(g.geometry)
    pts = gpd.GeoDataFrame(g[["blklot"]], geometry=g.geometry.representative_point(), crs=CRS)
    p = pd.DataFrame(json.load(open(D / "sf_permits.json")))
    p = p[p["status"] != "cancelled"]
    p["year"] = pd.to_datetime(p["issued_date"]).dt.year
    for c in ("existing_units", "proposed_units"):
        p[c] = pd.to_numeric(p[c], errors="coerce").fillna(0)
    p["net"] = np.where(p["permit_type"] == "6", -p["existing_units"], p["proposed_units"] - p["existing_units"])
    p["kind"] = np.where(p["permit_type"].isin(["1", "2", "6"]), "new or demolition", "alteration")
    p["blklot"] = p["block"].astype(str) + p["lot"].astype(str)
    out = pd.DataFrame({"city": "San Francisco", "pinched": g["pinched"], "acres": g["acres"], "width_m": g["width_m"],
                        "x5070": pts.geometry.x, "y5070": pts.geometry.y, "key": g["blklot"]})
    out["permits_main"] = out["key"].map(per_lot_years(p[p["kind"] == "new or demolition"], "blklot"))
    out["permits_all"] = out["key"].map(per_lot_years(p, "blklot"))
    out["dist_station_m"] = dist_to(rail_points(), pts)
    return out


def buffalo() -> pd.DataFrame:
    r = pd.DataFrame(json.load(open(D / "buffalo_roll.json")))
    for c in ("front", "acres", "latitude", "longitude"):
        r[c] = pd.to_numeric(r[c], errors="coerce")
    cls = pd.to_numeric(r["property_class_code"], errors="coerce")
    prev = pd.to_numeric(r["previous_property_class"], errors="coerce")
    use = prev.where(prev.notna() & (prev != cls), cls)
    pinched = use.between(220, 289) | use.between(400, 499)
    compare = use == 210
    r = r[(pinched | compare) & r["latitude"].notna()].copy()
    r["pinched"] = pinched[r.index].astype(float)
    pts = gpd.GeoDataFrame(r[["sbl"]], geometry=gpd.points_from_xy(r["longitude"], r["latitude"]), crs=4326).to_crs(CRS)
    p = pd.DataFrame(json.load(open(D / "buffalo_permits.json")))
    p["year"] = pd.to_datetime(p["issued"]).dt.year
    p["net"] = pd.to_numeric(p["units_added"], errors="coerce").fillna(0) - pd.to_numeric(p["units_lost"], errors="coerce").fillna(0)
    yrs = per_lot_years(p, "sbl")
    acres = r["acres"].where(r["acres"] > 0, pd.to_numeric(r["front"], errors="coerce") * pd.to_numeric(r["depth"], errors="coerce") / 43560)
    out = pd.DataFrame({"city": "Buffalo", "pinched": r["pinched"].values, "acres": acres.values, "width_m": (r["front"] * 0.3048).values,
                        "x5070": pts.geometry.x.values, "y5070": pts.geometry.y.values, "key": r["sbl"].values})
    out["permits_main"] = out["key"].map(yrs)
    out["permits_all"] = out["permits_main"]
    out["dist_station_m"] = dist_to(rail_points(), pts.reset_index(drop=True))
    return out


def tod_cities() -> pd.DataFrame:
    d = LT.lots()
    d = d[(d["treated"] == 0) & d["city"].isin(["Seattle", "Chicago"])].copy()
    d["pinched"] = d["parking"]
    d["permits_main"] = d["permits"]
    d["permits_all"] = d["permits"]
    return d[["city", "pinched", "acres", "width_m", "x5070", "y5070", "dist_station_m", "permits_main", "permits_all", "window_first", "window_last"]]


def windows(d: pd.DataFrame, city: str):
    if city == "Seattle":
        return list(range(int(d["window_first"].min()), 2012)), list(range(2013, int(d["window_last"].max()) + 1))
    a, b = WIN[city]
    return list(a), list(b)


def add_rates(d: pd.DataFrame, col: str) -> pd.DataFrame:
    rows = []
    for city, g in d.groupby("city"):
        pre, post = windows(g, city)
        g = g.copy()
        P = g[col].map(lambda x: x if isinstance(x, dict) else {})
        g["before_py"] = P.map(lambda x: sum(x.get(y, 0.0) for y in pre)) / len(pre)
        g["after_py"] = P.map(lambda x: sum(x.get(y, 0.0) for y in post)) / len(post)
        g["built_before"] = P.map(lambda x: float(any(x.get(y, 0) > 0 for y in pre)))
        rows.append(g)
    return pd.concat(rows)


def effect(g: pd.DataFrame) -> float:
    t, c = g[g["pinched"] == 1], g[g["pinched"] == 0]
    return float(((t["after_py"] - t["before_py"]).mean() - (c["after_py"] - c["before_py"]).mean()) * 1000)


def extra_total(g: pd.DataFrame) -> float:
    return effect(g) / 1000 * (g["pinched"] == 1).sum()


def main() -> None:
    rng = np.random.default_rng(SEED)
    lots = pd.concat([sf(), buffalo(), tod_cities()], ignore_index=True)
    lots["cell"] = lots["city"] + ":" + (lots["x5070"] // CELL).astype(int).astype(str) + "_" + (lots["y5070"] // CELL).astype(int).astype(str)
    eff_rows = []
    for col, lab in (("permits_main", "main"), ("permits_all", "including alterations (San Francisco ADUs)")):
        L = add_rates(lots, col)
        for city, g in L.groupby("city"):
            if lab != "main" and city != "San Francisco":
                continue
            cells = g["cell"].unique()
            grp = {c: x for c, x in g.groupby("cell")}
            bs = [effect(pd.concat([grp[c] for c in rng.choice(cells, len(cells))])) for _ in range(DRAWS)]
            t, c = g[g["pinched"] == 1], g[g["pinched"] == 0]
            eff_rows.append(dict(city=city, outcome=lab, pinched_lots=len(t), comparison_lots=len(c),
                                 pinched_before=t["before_py"].mean() * 1000, pinched_after=t["after_py"].mean() * 1000,
                                 comparison_before=c["before_py"].mean() * 1000, comparison_after=c["after_py"].mean() * 1000,
                                 effect=effect(g), p05=np.percentile(bs, 5), p95=np.percentile(bs, 95), extra_homes_per_year=extra_total(g)))
    E = pd.DataFrame(eff_rows)
    E.round(3).to_csv(REFERENCE / "parking_lot_cities_effects.csv", index=False)

    # prediction: separate models for pinched and comparison lots, outcome = change in homes per year on the lot
    from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import ElasticNet, Lasso, LinearRegression
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.tree import DecisionTreeRegressor
    L = add_rates(lots, "permits_main").reset_index(drop=True)
    L["dy"] = L["after_py"] - L["before_py"]
    # homes permitted within 250 m before (per year), from the same lot table
    near = []
    for city, g in L.groupby("city"):
        pts = gpd.GeoDataFrame(g[["before_py"]], geometry=gpd.points_from_xy(g["x5070"], g["y5070"]), crs=CRS)
        j = gpd.sjoin(pts.assign(geometry=pts.buffer(250))[["geometry"]], pts[["before_py", "geometry"]], predicate="contains")
        near.append(j.groupby(level=0)["before_py"].sum())
    L["near_before"] = pd.concat(near).reindex(L.index).fillna(0)
    # light checks (flags only, owner 2026-10-28)
    flags = checks.trait_range(L, "city", ["acres", "width_m", "dist_station_m", "near_before", "before_py"])
    flags += checks.unit_ranges(L)
    flags += checks.definition(L, "Chicago pinched lots farther than 402 m", (L["city"] == "Chicago") & (L["pinched"] == 1) & (L["dist_station_m"] > 402.4))
    flags += checks.definition(L, "Chicago comparison lots outside 402-805 m", (L["city"] == "Chicago") & (L["pinched"] == 0) & ~L["dist_station_m"].between(402.3, 805))
    flags += checks.definition(L, "lots with no area or width", L["acres"].isna() | L["width_m"].isna())
    X = pd.DataFrame({"log_acres": np.log(L["acres"].clip(lower=0.005)), "log_width": np.log(L["width_m"].clip(lower=1)),
                      "log_dist": np.log1p(L["dist_station_m"].fillna(L["dist_station_m"].median())),
                      "near_before": np.log1p(L["near_before"].clip(lower=0)), "built_before": L["built_before"]}).fillna(0)
    models = {"wls": (lambda: LinearRegression(), True), "lasso": (lambda: Lasso(alpha=0.001), True),
              "elastic_net": (lambda: ElasticNet(alpha=0.001, l1_ratio=0.5), True),
              "tree": (lambda: DecisionTreeRegressor(max_depth=3, min_samples_leaf=200), False),
              "forest": (lambda: RandomForestRegressor(n_estimators=200, min_samples_leaf=50, n_jobs=-1, random_state=SEED), False),
              "boosting": (lambda: HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=200, random_state=SEED), False),
              "causal_forest": (lambda: RandomForestRegressor(n_estimators=200, min_samples_leaf=200, max_features=0.5, n_jobs=-1, random_state=SEED), False),
              "knn": (lambda: KNeighborsRegressor(n_neighbors=50, n_jobs=-1), True)}
    cities = sorted(L["city"].unique())
    rows = []
    for hold in cities:
        tr = L["city"] != hold
        te_p = (L["city"] == hold) & (L["pinched"] == 1)
        act = extra_total(L[L["city"] == hold])
        others = [extra_total(L[L["city"] == c]) / max((L.loc[L["city"] == c, "pinched"] == 1).sum(), 1) for c in cities if c != hold]
        base = float(np.mean(others)) * te_p.sum()
        for kind, (mk, scale) in models.items():
            preds = []
            for grp in (1.0, 0.0):
                ix = tr & (L["pinched"] == grp)
                ix = ix[ix].index.to_numpy()
                if len(ix) > 60000:
                    ix = rng.choice(ix, 60000, replace=False)
                sc = StandardScaler().fit(X.loc[ix]) if scale else None
                T = (lambda Z, s=sc: s.transform(Z)) if scale else (lambda Z: Z.values)
                m = mk().fit(T(X.loc[ix]), L.loc[ix, "dy"].values)
                preds.append(m.predict(T(X.loc[te_p])))
            ex = float((preds[0] - preds[1]).sum())
            rows.append(dict(method=kind, held_out=hold, pinched_lots=int(te_p.sum()), actual_extra_per_year=act, baseline=base,
                             model=ex, error_model=abs(ex - act), error_baseline=abs(base - act), error_zero=abs(act)))
    P = pd.DataFrame(rows)
    S = P.groupby("method", sort=False).apply(lambda g: pd.Series(dict(
        mean_error_model=g["error_model"].mean(), mean_error_baseline=g["error_baseline"].mean(), mean_error_zero=g["error_zero"].mean(),
        cities_beating_baseline=int((g["error_model"] < g["error_baseline"]).sum())))).reset_index()
    S["passes"] = (S["mean_error_model"] < S["mean_error_baseline"]) & (S["mean_error_model"] < S["mean_error_zero"]) & (S["cities_beating_baseline"] >= 3)
    best = S.sort_values("mean_error_model").iloc[0]["method"]
    flags += checks.worst_miss(P[P["method"] == best], "held_out", "actual_extra_per_year", "model")
    checks.report(flags, REFERENCE / "parking_lot_cities_checks.csv")
    P.round(3).to_csv(REFERENCE / "parking_lot_cities_predict.csv", index=False)
    S.round(3).to_csv(REFERENCE / "parking_lot_cities_predict_summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(E.round(2).to_string(index=False))
    print(P.round(1).to_string(index=False))
    print(S.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
