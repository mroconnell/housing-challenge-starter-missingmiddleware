"""Five-city (now four-city) parking lot test (docs/parking/LOT_CITIES_PLAN.md).

    uv run python scripts/fetch_parking_lot_cities.py
    uv run --all-extras python scripts/run_parking_lot_cities.py

Outputs (aggregates only): reference/parking_lot_cities_effects.csv, reference/parking_lot_cities_predict.csv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull, cKDTree
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware import geom  # noqa: E402
from missing_middleware.parking import checks  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from scripts import run_parking_lot_test as LT  # noqa: E402

D = RAW / "parking_lot_cities"
SEED, DRAWS, CELL, CRS = 20261028, 2000, 500.0, 5070
SF_PINCHED = {"RH-2", "RH-3", "RM-1", "RM-2", "RM-3", "RM-4", "NC-1", "NC-2", "NC-3", "NC-S", "RC-3", "RC-4"}
SF_COMPARE = {"RH-1", "RH-1(D)"}
WIN = {"San Francisco": (range(2014, 2019), range(2020, 2025)), "Buffalo": (range(2012, 2017), range(2018, 2023)),
       "Chicago": (range(2009, 2013), range(2016, 2021))}


def rail_points() -> pd.DataFrame:
    """Rail stops (the parking block catalog's stop table, ntm_rail_stops.json) with x/y in EPSG:5070."""
    s = pd.DataFrame(json.load(open(RAW / "tod_census_cases" / "ntm_rail_stops.json")))
    s["x"], s["y"] = geom.transform(s["stop_lon"].values, s["stop_lat"].values, 4326, CRS)
    return s[s["stop_type_text"].astype(str).str.contains("rail|Rail|Tram|Subway|Metro")]


def dist_to(rail: pd.DataFrame, px, py) -> np.ndarray:
    """Distance (m) from each point to the nearest rail stop; NaN for points without coordinates."""
    px, py = np.asarray(px, float), np.asarray(py, float)
    out = np.full(len(px), np.nan)
    ok = np.isfinite(px) & np.isfinite(py)
    out[ok] = geom.nearest(px[ok], py[ok], rail["x"].values, rail["y"].values)[1]
    return out


def width_of(polys) -> np.ndarray:
    """Shorter side of each lot's minimum-area enclosing rectangle (as GEOS >= 3.12 minimum_rotated_rectangle)."""
    out = []
    for f in polys:
        pts = np.concatenate([r[:, :2] for part in f for r in part[:1]]) if f else np.zeros((0, 2))
        try:
            h = pts[ConvexHull(pts).vertices]
        except Exception:  # noqa: BLE001  (empty or degenerate lot)
            out.append(np.nan)
            continue
        h = h - h[0]                                  # local origin: no cancellation at 5070's large coordinates
        e = np.roll(h, -1, axis=0) - h
        e = e / np.hypot(e[:, 0], e[:, 1])[:, None]
        u = h @ e.T                                   # projections on each edge direction
        v = h @ np.c_[-e[:, 1], e[:, 0]].T            # and on its normal
        w, d = u.max(0) - u.min(0), v.max(0) - v.min(0)
        k = int(np.argmin(w * d))
        out.append(min(w[k], d[k]))
    return np.array(out)


def lot_areas(polys) -> np.ndarray:
    """Planar area of each lot (NaN when it has no geometry), shoelace about the first vertex of each ring, as GEOS
    does: about the projected origin, small lots at EPSG:5070's coordinates (millions of metres) lose precision."""
    out = np.full(len(polys), np.nan)
    for k, f in enumerate(polys):
        if not f:
            continue
        a = 0.0
        for part in f:
            for i, r in enumerate(part):
                x, y = r[:, 0] - r[0, 0], r[:, 1] - r[0, 1]
                ra = abs(0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))
                a += ra if i == 0 else -ra
        out[k] = a
    return out


def interior_points(polys) -> tuple[np.ndarray, np.ndarray]:
    """GEOS InteriorPointArea (shapely representative_point): per polygon, a horizontal scan line midway between the
    vertex heights nearest the envelope centre; the midpoint of the widest inside run; the widest over all parts."""
    xs, ys = np.full(len(polys), np.nan), np.full(len(polys), np.nan)
    for k, f in enumerate(polys):
        best_w = -1.0
        for part in f:
            shell = part[0]
            lo, hi = shell[:, 1].min(), shell[:, 1].max()
            centre = (lo + hi) / 2
            for r in part:
                y = r[:, 1]
                below, above = y[y <= centre], y[y > centre]
                if len(below) and below.max() > lo:
                    lo = below.max()
                if len(above) and above.min() < hi:
                    hi = above.min()
            sy = (lo + hi) / 2
            cross = []
            for r in part:
                if sy < r[:, 1].min() or sy > r[:, 1].max():
                    continue
                for (x0, y0), (x1, y1) in zip(r[:-1], r[1:]):
                    if (y0 > sy and y1 > sy) or (y0 < sy and y1 < sy) or y0 == y1:
                        continue
                    if (y0 == sy and y1 < sy) or (y1 == sy and y0 < sy):
                        continue
                    cross.append(x0 if x0 == x1 else x0 + (sy - y0) / ((y1 - y0) / (x1 - x0)))
            cross.sort()
            w, pt = 0.0, (shell[0, 0], shell[0, 1])
            for i in range(0, len(cross) - 1, 2):
                if cross[i + 1] - cross[i] > w:
                    w, pt = cross[i + 1] - cross[i], ((cross[i] + cross[i + 1]) / 2, sy)
            if w > best_w:
                best_w, (xs[k], ys[k]) = w, pt
    return xs, ys


def _buffer_ring(r: float) -> np.ndarray:
    """The 64-sided polygon GEOS draws for a point buffer of radius r (quadrant segments 16), centred on 0, 0."""
    n = 64
    a = -np.arange(n) * (2 * np.pi / n)
    ring = np.c_[r * np.cos(a), r * np.sin(a)]
    return np.vstack([ring, ring[:1]])


def near_sum(x, y, val, r: float) -> np.ndarray:
    """Sum of val over points strictly inside each point's 250 m buffer polygon (itself included), as a shapely
    buffer + 'contains' join: every point within the polygon's inscribed radius counts; the few in the thin band
    between the inscribed radius and r are tested against the 64-gon itself."""
    xy = np.c_[x, y]
    tree = cKDTree(xy)
    inner = r * np.cos(np.pi / 64)
    ring = _buffer_ring(r)
    out = np.zeros(len(x))
    for i, nb in enumerate(tree.query_ball_point(xy, r)):
        nb = np.asarray(nb, dtype=np.int64)
        if not len(nb):
            continue
        d = np.hypot(x[nb] - x[i], y[nb] - y[i])
        edge = nb[d >= inner]
        keep = nb[d < inner]
        if len(edge):
            ins = geom.points_in_feature(x[edge] - x[i], y[edge] - y[i], [[ring]])
            keep = np.concatenate([keep, edge[ins]])
        out[i] = val[np.sort(keep)].sum()
    return out


def per_lot_years(perm: pd.DataFrame, key: str) -> dict:
    return {k: g.groupby("year")["net"].sum().to_dict() for k, g in perm.groupby(key)}


def sf() -> pd.DataFrame:
    lay = geom.read_geojson(D / "sf_parcels.geojson")
    lay = lay.subset(lay.attrs["zoning_code"].isin(SF_PINCHED | SF_COMPARE)).to_crs(CRS)
    g = lay.attrs.copy()
    g["pinched"] = g["zoning_code"].isin(SF_PINCHED).astype(float)
    g["acres"] = lot_areas(lay.polys) / 4046.8564
    g["width_m"] = width_of(lay.polys)
    px, py = interior_points(lay.polys)
    p = pd.DataFrame(json.load(open(D / "sf_permits.json")))
    p = p[p["status"] != "cancelled"]
    p["year"] = pd.to_datetime(p["issued_date"]).dt.year
    for c in ("existing_units", "proposed_units"):
        p[c] = pd.to_numeric(p[c], errors="coerce").fillna(0)
    # gross new homes, the same measure as TOD's Seattle and Chicago permit years (audit 2e, 2026-10-29): demolitions are not subtracted
    p["net"] = np.where(p["permit_type"].isin(["1", "2"]), p["proposed_units"],
                        np.where(p["permit_type"] == "6", 0.0, (p["proposed_units"] - p["existing_units"]).clip(lower=0)))
    p["kind"] = np.where(p["permit_type"].isin(["1", "2", "6"]), "new or demolition", "alteration")
    p["blklot"] = p["block"].astype(str) + p["lot"].astype(str)
    out = pd.DataFrame({"city": "San Francisco", "pinched": g["pinched"], "acres": g["acres"], "width_m": g["width_m"],
                        "x5070": px, "y5070": py, "key": g["blklot"]})
    out["permits_main"] = out["key"].map(per_lot_years(p[p["kind"] == "new or demolition"], "blklot"))
    out["permits_all"] = out["key"].map(per_lot_years(p, "blklot"))
    out["dist_station_m"] = dist_to(rail_points(), px, py)
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
    px, py = geom.transform(r["longitude"].values, r["latitude"].values, 4326, CRS)
    p = pd.DataFrame(json.load(open(D / "buffalo_permits.json")))
    p["year"] = pd.to_datetime(p["issued"]).dt.year
    p["net"] = pd.to_numeric(p["units_added"], errors="coerce").fillna(0)  # gross new homes, as for Seattle and Chicago (audit 2e)
    yrs = per_lot_years(p, "sbl")
    acres = r["acres"].where(r["acres"] > 0, pd.to_numeric(r["front"], errors="coerce") * pd.to_numeric(r["depth"], errors="coerce") / 43560)
    out = pd.DataFrame({"city": "Buffalo", "pinched": r["pinched"].values, "acres": acres.values, "width_m": (r["front"] * 0.3048).values,
                        "x5070": px, "y5070": py, "key": r["sbl"].values})
    out["permits_main"] = out["key"].map(yrs)
    out["permits_all"] = out["permits_main"]
    out["dist_station_m"] = dist_to(rail_points(), px, py)
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
    near = "--near-transit" in sys.argv
    tag = "_near_transit" if near else ""
    if near:  # added test, owner 2026-10-28: only lots within 805 m of a rail station
        lots = lots[lots["dist_station_m"] <= 805].reset_index(drop=True)
        print("near-transit lots:", lots.groupby(["city", "pinched"]).size().to_dict(), flush=True)
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
    E.round(3).to_csv(REFERENCE / f"parking_lot_cities_effects{tag}.csv", index=False)

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
        near.append(pd.Series(near_sum(g["x5070"].values, g["y5070"].values, g["before_py"].values, 250.0), index=g.index))
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
    checks.report(flags, REFERENCE / f"parking_lot_cities_checks{tag}.csv")
    P.round(3).to_csv(REFERENCE / f"parking_lot_cities_predict{tag}.csv", index=False)
    S.round(3).to_csv(REFERENCE / f"parking_lot_cities_predict_summary{tag}.csv", index=False)
    pd.set_option("display.width", 250)
    print(E.round(2).to_string(index=False))
    print(P.round(1).to_string(index=False))
    print(S.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
