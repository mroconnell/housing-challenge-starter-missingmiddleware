"""One round of the lot-model improvement loop (docs/tod/LOT_MODEL_PLAN.md item 49).

    uv run --all-extras python scripts/run_tod_lot_model_loop.py --round 1

Fast tool: two histogram gradient boosting models (upzoned lots under the rules after; every other lot under the rules
before). Round 1: outcome = change in homes per lot. From round 2 (item 51): outcome = homes after (5-year basis), Poisson
loss, homes before as a trait. Leave-one-city-out over the training and no-reform
cities only; Chicago, Madison and Bellevue are never fitted on and never predicted here.

Writes reference/tod_lot_model_loop_round{N}.csv (per city) and prints a summary.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import REFERENCE  # noqa: E402
import run_tod_lot_model as L  # noqa: E402


DOWNTOWN = {"Columbus placebo": (39.9612, -82.9988), "Kansas City placebo": (39.0997, -94.5786)}


def fake_area(d: pd.DataFrame, c: str) -> np.ndarray:
    """Item 58: the placebo's fake reform area: lots within 805 m of a rail or rapid stop, or of the downtown point."""
    import geopandas as gpd
    if c in DOWNTOWN:
        lat, lon = DOWNTOWN[c]
        p = gpd.GeoSeries(gpd.points_from_xy([lon], [lat]), crs=4326).to_crs(5070)
        dist = np.hypot(d["x5070"].values - p.x.iloc[0], d["y5070"].values - p.y.iloc[0])
        return dist <= 805
    return (d["dist_station_m"].fillna(1e9) <= 805).values


def main(argv=None) -> None:
    from sklearn.ensemble import HistGradientBoostingRegressor
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--seed", type=int, default=20261031, help="random seed (item 57: seed spread of a round)")
    ap.add_argument("--holdouts", action="store_true", help="item 59.5: the one-time read of Chicago, Madison and Bellevue")
    a = ap.parse_args(argv)
    L.FIT.update(item25=True, item32=True, item34=True, item37=True, item46=True)
    D = pd.read_parquet(L.OUT / "lots_rebuilt_halfmile.parquet")
    if not a.holdouts:
        D = D[~D["city"].isin(L.HOLD)].reset_index(drop=True)          # item 49.2: holdouts never touched here
    cache = {k: L.cost_per_home(k[0], int(k[1]) - 1) for k in set(zip(D["city"], D["eff_year"]))}
    D["cost_per_home"] = [cache[(c, y)] for c, y in zip(D["city"], D["eff_year"])]
    D = L.five_year_basis(L.dedupe_lots(D)).reset_index(drop=True)
    Xa, Xb = L.features(D, True), L.features(D, False)
    vc = [c for c in D.columns if c.startswith("v_")]
    V = D[vc].replace([np.inf, -np.inf], np.nan)
    Xa, Xb = pd.concat([Xa, V], axis=1), pd.concat([Xb, V], axis=1)
    y = D["ua5"].clip(lower=0).values   # item 51: homes after, with homes before as a trait
    Xa["log_before5"] = np.log1p(D["ub5"].values)
    Xb["log_before5"] = np.log1p(D["ub5"].values)
    # item 53: the place's own pace before the reform (study area, and within 400 m of the lot)
    from scipy.spatial import cKDTree
    wa = D["w"] * D["acres"].clip(lower=0.01)
    area_rate = (D["ub5"] * D["w"]).groupby(D["unit"]).transform("sum") / wa.groupby(D["unit"]).transform("sum")
    near = np.zeros(len(D))
    for u, ix in D.groupby("unit").groups.items():
        d = D.loc[ix]
        xy = d[["x5070", "y5070"]].to_numpy()
        nb = cKDTree(xy).query_ball_point(xy, r=400)
        h, ac = (d["ub5"] * d["w"]).to_numpy(), (d["acres"].clip(lower=0.01) * d["w"]).to_numpy()
        near[D.index.get_indexer(ix)] = [h[n].sum() / ac[n].sum() for n in nb]
    for X in (Xa, Xb):
        X["log_area_rate_before"] = np.log1p(area_rate.values)
        X["log_near400_rate_before"] = np.log1p(near)
    if a.round >= 5:   # item 54: reform-level shares act as city labels and extrapolate; dropped
        Xa = Xa.drop(columns=[c for c in Xa.columns if c.startswith("reform_share_")])
        Xb = Xb.drop(columns=[c for c in Xb.columns if c.startswith("reform_share_")])
    w = D["w"].values
    up = (D["treated"] == 1).values
    # item 56: each city's whole-city permit-survey trend (after vs before, homes per year) over its windows
    trend = {}
    if a.round >= 7:
        from missing_middleware.paths import RAW
        from missing_middleware.tod import control_cities as cc
        bps = cc.read_bps(RAW / "tod_control_cities" / "bps")
        gaz = cc.read_gazetteer(RAW / "tod_control_cities" / "Gaz_places_national.zip")
        panel, places = cc.link(bps, gaz, cc.read_county_hu(RAW / "tod_control_cities" / "Gaz_counties_national.zip"))
        names = {"New York": ("New York city", "36"), "Philadelphia": ("Philadelphia city", "42"), "Charlotte": ("Charlotte city", "37"),
                 "Saint Paul": ("St. Paul city", "27"), "Seattle": ("Seattle city", "53"), "Los Angeles": ("Los Angeles city", "06"),
                 "Madison placebo": ("Madison city", "55"), "Milwaukee placebo": ("Milwaukee city", "55"),
                 "Columbus placebo": ("Columbus city", "39"), "Kansas City placebo": ("Kansas City city", "29")}
        series = {}
        for c, (n, st) in names.items():
            g = places[(places.place_name == n) & (places.geoid.str[:2] == st)].geoid.iloc[0]
            series[c] = panel[panel.geoid == g].set_index("year")["units"]
        for c in names:
            d = D[D["city"] == c]
            ratios, wts = [], []
            for (ef, wf, wl), n in d.groupby(["eff_year", "window_first", "window_last"]).size().items():
                s_ = series[c]
                b = s_.reindex(range(int(wf), int(ef))).mean()
                aft = s_.reindex(range(int(ef) + 1, int(wl) + 1)).mean() if c != "Madison placebo" else s_.reindex(range(int(ef) + 1, int(wl) + 1)).mean()
                if b and b == b and aft == aft:
                    ratios.append(aft / b)
                    wts.append(n)
            trend[c] = float(np.average(ratios, weights=wts)) if ratios else np.nan
        print("market trend (after / before, whole city):", {k: round(v, 2) for k, v in trend.items()}, flush=True)
    rows = []
    targets = list(L.HOLD) if a.holdouts else sorted(D["city"].unique())
    for c in targets:
        te = (D["city"] == c).values
        pool = [x for x in D["city"].unique() if x not in L.HOLD]
        tr = D["city"].isin(L.training_cities(pool, c)).values
        pred = np.zeros(len(D))
        models = {}
        ac = D["acres"].clip(lower=0.01).values
        for g, X in ((True, Xa), (False, Xb)):
            fit = tr & (up == g)
            if fit.sum() < 50:
                continue
            m = HistGradientBoostingRegressor(random_state=a.seed)   # item 52: squared error on the level
            ac = D["acres"].clip(lower=0.01).values
            if a.round >= 6:   # item 55: homes per acre, weighted by acres
                m.fit(X[fit], y[fit] / ac[fit], sample_weight=w[fit] * ac[fit])
            else:
                m.fit(X[fit], y[fit], sample_weight=w[fit])
            models[g] = m
            pm = te & (up == g)
            if pm.any():
                built = fit & (y > 0)
                if a.round >= 6:   # item 55: density capped at the 99th percentile of building lots, times acres
                    hpa = float(np.quantile(y[built] / ac[built], 0.99))
                    pred[pm] = np.clip(m.predict(L.forecast_view(X[pm])), 0, hpa) * ac[pm]
                else:
                    hpa = float(np.quantile(y[built] / D.loc[built, "acres"].clip(lower=0.01).values, 0.999))
                    cap = D.loc[pm, "acres"].clip(lower=0.01).values * hpa
                    pred[pm] = np.clip(m.predict(L.forecast_view(X[pm])), 0, cap)   # item 52: 0 to a physical ceiling
        ub, ua = D.loc[te, "ub5"].values, D.loc[te, "ua5"].values
        wt, u = w[te], up[te]
        if a.round >= 8:   # item 57.5: two-part design: city total = same pace; lots get shares
            total = float(ub @ wt)
            p_on = np.clip(pred[te], 0, None)
            share_on = p_on * wt / max(float(p_on @ wt), 1e-9)
            # law off on upzoned lots too
            p_off = p_on.copy()
            if u.any():
                m_off = models[False]
                p_off[u] = np.clip(m_off.predict(L.forecast_view(Xb[te][u])), 0, None) * ac[te][u]
            share_off = p_off * wt / max(float(p_off @ wt), 1e-9)
            fake = fake_area(D[te], c) if c.endswith("placebo") else np.zeros(int(te.sum()), bool)
            grp = u if u.any() else fake
            act_share_after = float(ua[grp] @ wt[grp]) / max(float(ua @ wt), 1e-9)
            act_share_before = float(ub[grp] @ wt[grp]) / max(float(ub @ wt), 1e-9)
            rows.append({"city": c, "group": "upzoned" if u.any() else "fake area (placebo)", "group_lots": int(grp.sum()),
                         "city_total_same_pace": total, "actual_total_after": float(ua @ wt),
                         "share_before": act_share_before, "share_after_actual": act_share_after,
                         "share_after_model": float(share_on[grp].sum()), "share_after_model_law_off": float(share_off[grp].sum()),
                         "tod_effect_homes": float((share_on[grp].sum() - share_off[grp].sum()) * total) if u.any() else 0.0})
            print(rows[-1], flush=True)
            continue
        if a.round >= 7 and trend.get(c) == trend.get(c):   # item 56: scale to before x market trend on non-upzoned lots
            p_te = pred[te]
            denom = float(p_te[~u] @ wt[~u])
            if denom > 0:
                k = float(ub[~u] @ wt[~u]) * trend[c] / denom
                pred[te] = p_te * k
        rows.append({"city": c, "lots": int(te.sum()), "upzoned_lots": int(u.sum()),
                     "before": float(ub @ wt), "actual_after": float(ua @ wt), "model_after": float(pred[te] @ wt),
                     "upzoned_before": float(ub[u] @ wt[u]), "upzoned_actual_after": float(ua[u] @ wt[u]),
                     "upzoned_model_after": float(pred[te][u] @ wt[u])})
        print(rows[-1], flush=True)
    R = pd.DataFrame(rows)
    if a.round >= 8:
        ok = (R["share_after_model"] > 0) & (R["share_after_actual"] > 0)
        R["abs_log_model"] = np.abs(np.log(R["share_after_model"] / R["share_after_actual"])).where(ok)
        R["abs_log_same_share"] = np.abs(np.log(R["share_before"] / R["share_after_actual"])).where(ok & (R["share_before"] > 0))
        tag = "" if a.seed == 20261031 else f"_seed{a.seed}"
        if a.holdouts:   # item 59.4: calibration from the main-seed round-8 training cities
            T = pd.read_csv(REFERENCE / "tod_lot_model_loop_round8_shares.csv")
            T = T[T["group"] == "upzoned"]
            k = float((T["share_after_actual"] - T["share_before"]).sum() / (T["share_after_model"] - T["share_before"]).sum())
            R["calibration_k"] = k
            R["share_after_calibrated"] = R["share_before"] + k * (R["share_after_model"] - R["share_before"])
            okc = (R["share_after_calibrated"] > 0) & (R["share_after_actual"] > 0)
            R["abs_log_calibrated"] = np.abs(np.log(R["share_after_calibrated"] / R["share_after_actual"])).where(okc)
            R["net_addition_A_relocation"] = 0.0
            R["net_addition_B_addition"] = R["tod_effect_homes"]
            tag = "_holdouts"
        R.round(4).to_csv(REFERENCE / f"tod_lot_model_loop_round{a.round}{tag}_shares.csv", index=False)
        pd.set_option("display.width", 250)
        print(R.round(3).to_string(index=False))
        print("median |log| model:", round(R["abs_log_model"].median(), 3), " same share as before:", round(R["abs_log_same_share"].median(), 3))
        return
    R["actual_change"] = R["actual_after"] - R["before"]
    R["model_change"] = R["model_after"] - R["before"]
    R["error_after_pct"] = 100 * (R["model_after"] - R["actual_after"]) / R["actual_after"].where(R["actual_after"] != 0)
    R["error_vs_same_pace_pct"] = 100 * (R["before"] - R["actual_after"]) / R["actual_after"].where(R["actual_after"] != 0)
    if trend:
        R["market_trend"] = R["city"].map(trend)
        R["error_before_x_trend_pct"] = 100 * (R["before"] * R["market_trend"] - R["actual_after"]) / R["actual_after"]
    tag = "" if a.seed == 20261031 else f"_seed{a.seed}"
    R.round(1).to_csv(REFERENCE / f"tod_lot_model_loop_round{a.round}{tag}.csv", index=False)
    pd.set_option("display.width", 250)
    print(R[["city", "before", "actual_after", "model_after", "error_after_pct", "error_vs_same_pace_pct"] + (["error_before_x_trend_pct"] if trend else []) + [
             "upzoned_actual_after", "upzoned_model_after"]].round(0).to_string(index=False))


if __name__ == "__main__":
    main()
