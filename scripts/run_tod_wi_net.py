"""TOD Wisconsin statewide net: homes with the law minus without, 2027-2031 (docs/tod/WI_NET_PLAN.md; plan item 65).

    uv run --all-extras python scripts/run_tod_wi_net.py --round 1 --variant a|b [--seed N]

Round-8 share model (plan items 57-59) fitted on every training and no-reform city, applied to the Wisconsin lot table.
variant a: every Wisconsin upzoned lot gets the law; b: only upzoned lots within 1/2 mile of rail or rapid (as in training).
Writes reference/tod_wi_net_round{N}{variant}[_seedS].csv (city rows) and ..._lots_top.csv (largest per-lot effects).
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

K = 0.18                     # item 59 calibration
NEAR_STATE = {"today": 14463.78, "rebased": 18322.0}     # statewide near-stop baseline 2027-2031
CITY_NAME = {"Milwaukee": "Milwaukee city", "Madison": "Madison city"}


def city_totals() -> pd.DataFrame:
    """All-housing no-reform baseline 2027-2031 per city (shared baseline v2, central) and its near-stop part."""
    A = pd.read_csv(REFERENCE / "tod_model_by_area.csv")
    a = A[(A.sizing == "net_effect") & (A.scenario == "typical")].groupby("name").agg(
        share=("share_near_stops", "first"), near=("baseline_near_central_2027_2031", "sum"))
    a["all_housing"] = a["near"] / a["share"]
    R = pd.read_csv(REFERENCE / "tod_rebase_check.csv").set_index("name")
    a["near_rebased"] = R["rebased_central"]
    H = pd.read_csv(REFERENCE / "tod_near_stop_homes_by_muni.csv").groupby("name")["homes_2020"].sum()
    a["homes_2020"] = H
    return a


def main(argv=None) -> None:
    from sklearn.ensemble import HistGradientBoostingRegressor
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--variant", choices=["a", "b"], required=True)
    ap.add_argument("--seed", type=int, default=20261031)
    a = ap.parse_args(argv)
    L.FIT.update(item25=True, item32=True, item34=True, item37=True, item46=True)
    T = pd.read_parquet(L.OUT / "lots_rebuilt_halfmile.parquet")
    cache = {k: L.cost_per_home(k[0], int(k[1]) - 1) for k in set(zip(T["city"], T["eff_year"]))}
    T["cost_per_home"] = [cache[(c, y)] for c, y in zip(T["city"], T["eff_year"])]
    T = L.five_year_basis(L.dedupe_lots(T))
    W = pd.read_parquet(L.OUT / "wi_lots.parquet")
    L.BPS_NAME.setdefault("Milwaukee", ("55", "Milwaukee"))
    L.BPS_NAME.setdefault("Madison", ("55", "Madison"))
    wc = {c: L.cost_per_home(c, 2022) for c in W["city"].unique()}   # one lookup per city, not per lot
    W["cost_per_home"] = W["city"].map(wc)
    W = W.assign(w=1.0, placebo=0.0, rezoned_later=0.0, window_first=2019, ub5=W["units_before"] * 5 / 6, ua5=0.0)
    far = (W["treated"] == 1) & ~(W["dist_station_m"] <= 805)
    W["bus_only_upzoned"] = far
    if a.variant == "b":   # item 48 as in training: upzoned lots far from rail/rapid are not law-on lots
        W.loc[far, "lot_group"] = "upzoned_not_near_transit"
        W.loc[far, "treated"] = 0.0
    if a.round >= 3:   # round 3: training labels upzoned industrial-use lots "upzoned_from_industrial" (lot model line ~110);
        # the Wisconsin table had labelled them plain "upzoned" (222 lots)
        W.loc[(W["lot_group"] == "upzoned") & (W["use"] == "ind"), "lot_group"] = "upzoned_from_industrial"
    W["city"] = "WI " + W["city"]
    W["unit"] = "wi|" + W["unit"].astype(str)
    A = pd.concat([T.assign(_wi=0), W.assign(_wi=1)], ignore_index=True)
    # Wisconsin lots carry "WI " city names, so rank keys never mix with training cities (item 25.3)
    Xa, Xb = L.features(A, True), L.features(A, False)
    vc = [c for c in A.columns if c.startswith("v_")]
    V = A[vc].replace([np.inf, -np.inf], np.nan)
    Xa, Xb = pd.concat([Xa, V], axis=1), pd.concat([Xb, V], axis=1)
    from scipy.spatial import cKDTree
    wa = A["w"] * A["acres"].clip(lower=0.01)
    area_rate = (A["ub5"] * A["w"]).groupby(A["unit"]).transform("sum") / wa.groupby(A["unit"]).transform("sum")
    near = np.zeros(len(A))
    for u, ix in A.groupby("unit").groups.items():
        d = A.loc[ix]
        xy = d[["x5070", "y5070"]].to_numpy()
        nb = cKDTree(xy).query_ball_point(xy, r=400)
        h, ac = (d["ub5"] * d["w"]).to_numpy(), (d["acres"].clip(lower=0.01) * d["w"]).to_numpy()
        near[A.index.get_indexer(ix)] = [h[n].sum() / ac[n].sum() for n in nb]
    for X in (Xa, Xb):
        X["log_before5"] = np.log1p(A["ub5"].values)
        X["log_area_rate_before"] = np.log1p(area_rate.values)
        X["log_near400_rate_before"] = np.log1p(near)
        X.drop(columns=[c for c in X.columns if c.startswith("reform_share_")], inplace=True)
    if a.round >= 3:   # standing checks (flag only, never stop): units, policy, out of range
        from missing_middleware.tod import sanity as SN
        fl = SN.unit_flags(A, L.FAR_CITIES) + SN.policy_flags(A[A["_wi"] == 1]) + SN.range_flags(Xa, A["city"])
        fl = [f for f in fl if str(f.get("city", "")).startswith("WI") or f.get("kind") != "out of range"]
        SN.report(fl, REFERENCE / f"tod_wi_net_round{a.round}{a.variant}_flags.csv")
        print("flags:", pd.Series([f.get("kind") for f in fl]).value_counts().to_dict(), flush=True)
    y = A["ua5"].clip(lower=0).values
    w = A["w"].values
    ac = A["acres"].clip(lower=0.01).values
    up = (A["treated"] == 1).values
    tr = (A["_wi"] == 0).values
    models, cap = {}, {}
    for g, X in ((True, Xa), (False, Xb)):
        fit = tr & (up == g)
        m = HistGradientBoostingRegressor(random_state=a.seed)
        m.fit(X[fit], y[fit] / ac[fit], sample_weight=w[fit] * ac[fit])
        built = fit & (y > 0)
        models[g], cap[g] = m, float(np.quantile(y[built] / ac[built], 0.99))
    wi = ~tr
    if a.round >= 2:   # round 2: per-acre predictions times acres extrapolated on the airport (1,504 acres) and the
        # West Towne Mall lots (37 acres: 1,939 homes in 5 years). Acres used are capped at the largest building lot
        # in training (99th percentile of lots that built), the size of project the model has seen.
        bl = tr & (y > 0)
        acap = float(np.quantile(ac[bl], 0.99))
        print(f"acre cap (99th percentile of training lots that built): {acap:.2f}; Wisconsin lots above it: {int((wi & (ac > acap)).sum())}", flush=True)
        ac = np.where(wi, np.minimum(ac, acap), ac)
    p_on = np.zeros(len(A))
    p_off = np.clip(models[False].predict(L.forecast_view(Xb[wi])), 0, cap[False]) * ac[wi]
    p_off_all = np.zeros(len(A)); p_off_all[wi] = p_off
    p_on[wi] = p_off
    u = wi & up
    p_on[u] = np.clip(models[True].predict(L.forecast_view(Xa[u])), 0, cap[True]) * ac[u]
    tot = city_totals()
    rows, lots = [], []
    for c in ("Milwaukee", "Madison"):
        m = (A["city"] == "WI " + c).values
        so = p_on[m] / p_on[m].sum()
        sf = p_off_all[m] / p_off_all[m].sum()
        uu = up[m]
        t = tot.loc[CITY_NAME[c]]
        homes_tab = float(A.loc[m, "census_homes"].sum())
        total = float(t["all_housing"]) * min(1.0, homes_tab / float(t["homes_2020"]))
        d_share = float(so[uu].sum() - sf[uu].sum())
        rows.append({"city": c, "variant": a.variant, "seed": a.seed, "lots": int(m.sum()), "law_on_lots": int(uu.sum()),
                     "table_homes_2020": homes_tab, "city_homes_2020": float(t["homes_2020"]),
                     "city_all_housing_2027_2031": float(t["all_housing"]), "table_total_2027_2031": total,
                     "near_baseline_today": float(t["near"]), "near_baseline_rebased": float(t["near_rebased"]),
                     "law_on_share_with": float(so[uu].sum()), "law_on_share_without": float(sf[uu].sum()),
                     "share_change": d_share, "B_raw": d_share * total, "B_calibrated": K * d_share * total,
                     "before_homes_2019_2024_5yr": float(A.loc[m, "ub5"].sum()),
                     "model_homes_law_off_raw_5yr": float(p_off_all[m].sum()), "model_homes_law_on_raw_5yr": float(p_on[m].sum())})
        e = (so - sf) * total
        dl = A.loc[m, ["city", "acres", "census_homes", "dist_station_m", "lot_group", "far_before", "far_gain", "ub5"]].copy()
        dl["p_on"], dl["p_off"], dl["effect_B_raw"] = p_on[m], p_off_all[m], e
        lots.append(dl.reindex(dl["effect_B_raw"].abs().sort_values(ascending=False).index[:20]))
        bands = pd.cut(A.loc[m, "dist_station_m"], [-1, 402, 805, 1609, 1e9], labels=["rail/rapid <=1/4", "1/4-1/2", "1/2-1 mi", ">1 mi"])
        print(c, "B raw by distance to rail/rapid:", pd.Series(e).groupby(bands.values, observed=False).sum().round(1).to_dict(), flush=True)
    R = pd.DataFrame(rows)
    s_today = NEAR_STATE["today"] / R["near_baseline_today"].sum()
    s_reb = NEAR_STATE["rebased"] / R["near_baseline_rebased"].sum()
    R["statewide_scale_today"], R["statewide_scale_rebased"] = s_today, s_reb
    tag = f"round{a.round}{a.variant}" + ("" if a.seed == 20261031 else f"_seed{a.seed}")
    R.round(4).to_csv(REFERENCE / f"tod_wi_net_{tag}.csv", index=False)
    pd.concat(lots).round(3).to_csv(REFERENCE / f"tod_wi_net_{tag}_lots_top.csv")
    pd.set_option("display.width", 250)
    print(R[["city", "law_on_lots", "table_total_2027_2031", "law_on_share_without", "law_on_share_with", "share_change",
             "B_raw", "B_calibrated", "before_homes_2019_2024_5yr", "model_homes_law_off_raw_5yr", "model_homes_law_on_raw_5yr"]].round(3).to_string(index=False))
    br, bc = R["B_raw"].sum(), R["B_calibrated"].sum()
    print(f"STATEWIDE B raw {br * s_today:,.0f} (rebased scale {br * s_reb:,.0f}); B calibrated {bc * s_today:,.0f} ({bc * s_reb:,.0f}); A = 0")


if __name__ == "__main__":
    main()
