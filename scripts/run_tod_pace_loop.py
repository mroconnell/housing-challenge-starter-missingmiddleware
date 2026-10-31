"""TOD no-reform pace model loop (docs/tod/PACE_MODEL_PLAN.md; plan item 62).

    uv run --all-extras python scripts/run_tod_pace_loop.py --round 1 [--seed N]

Predicts homes built on each lot over 5 years with no TOD rules in force, from traits any state has. Two parts: chance the
lot builds, times homes per acre if built, times acres. Scored on city-window totals against the national permit survey's
"same pace as before". Holdouts (Chicago, Madison, Bellevue) are never fitted on or scored.
Writes reference/tod_pace_loop_round{N}[_seedS].csv.
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
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
import run_tod_lot_model as L  # noqa: E402

PLACE = {"New York": ("New York city", "36"), "Philadelphia": ("Philadelphia city", "42"), "Charlotte": ("Charlotte city", "37"),
         "Saint Paul": ("St. Paul city", "27"), "Seattle": ("Seattle city", "53"), "Los Angeles": ("Los Angeles city", "06"),
         "Madison placebo": ("Madison city", "55"), "Milwaukee placebo": ("Milwaukee city", "55"),
         "Columbus placebo": ("Columbus city", "39"), "Kansas City placebo": ("Kansas City city", "29")}


def bps_series() -> tuple[dict, dict]:
    from missing_middleware.tod import control_cities as cc
    bps = cc.read_bps(RAW / "tod_control_cities" / "bps")
    gaz = cc.read_gazetteer(RAW / "tod_control_cities" / "Gaz_places_national.zip")
    panel, places = cc.link(bps, gaz, cc.read_county_hu(RAW / "tod_control_cities" / "Gaz_counties_national.zip"))
    s, hu = {}, {}
    for c, (n, st) in PLACE.items():
        p = places[(places.place_name == n) & (places.geoid.str[:2] == st)].iloc[0]
        s[c] = panel[panel.geoid == p.geoid].set_index("year")["units"]
        hu[c] = float(p.hu10)
    return s, hu


def long_rows(D: pd.DataFrame) -> pd.DataFrame:
    """One row per lot-window with no TOD rules in force: every lot's before window; no-reform cities' after window."""
    b = D.assign(window="before", start=D["window_first"], end=D["eff_year"] - 1, y5=D["ub5"])
    a = D[D["placebo"] == 1]
    a = a.assign(window="after", start=a["eff_year"] + 1, end=a["window_last"], y5=a["ua5"])
    return pd.concat([b, a], ignore_index=True)


def traits(R: pd.DataFrame, rnd: int, series: dict, hu: dict) -> pd.DataFrame:
    X = pd.DataFrame(index=R.index)
    X["log_acres"] = np.log(R["acres"].clip(lower=0.005))
    X["log_width"] = np.log(R["width_m"].clip(lower=1))
    X["log_census_homes"] = np.log1p(R["census_homes"].clip(lower=0))
    X["log_dist_stop"] = np.log1p(R["dist_station_m"]).fillna(-1.0)
    X["no_rail_rapid"] = R["dist_station_m"].isna().astype(float)
    for c in ("rent", "home_value", "income"):
        X[f"log_{c}"] = np.log(R[c].clip(lower=1))
    V = R[[c for c in R.columns if c.startswith("v_")]].replace([np.inf, -np.inf], np.nan)
    X = pd.concat([X, V], axis=1)
    if rnd >= 2:   # place pace from the national permit survey, years before the window, per 2010 home
        key = R[["city", "start"]].drop_duplicates()
        rate = {}
        for c, s0 in key.itertuples(index=False):
            yrs = [y for y in range(int(s0) - 5, int(s0)) if y >= 2000]
            v = series[c].reindex(yrs).mean() if (c in series and yrs) else np.nan
            rate[(c, s0)] = v / hu[c] * 1000 if c in hu else np.nan
        X["place_permits_per_1000_prior"] = [rate[k] for k in zip(R["city"], R["start"])]
        X["log_place_homes"] = np.log(R["city"].map(hu))
    return X


def bps_baseline(R: pd.DataFrame, series: dict, hu: dict) -> pd.DataFrame:
    """Same pace as before (national permit survey): place permits/yr in the 5 years before the window x 5 x study-area share of homes."""
    out = []
    for (c, w, s0), g in R.groupby(["city", "window", "start"]):
        yrs = [y for y in range(int(s0) - 5, int(s0)) if y >= 2000]
        pace = series[c].reindex(yrs).mean() if yrs else np.nan
        homes = float((g["census_homes"] * g["w"]).sum())
        out.append({"city": c, "window": w, "start": s0, "bps_same_pace": pace * 5 * homes / hu[c], "bps_years": len(yrs)})
    return pd.DataFrame(out)


def fit_predict(X, R, fit, pred_mask, seed, offset=None, per_lot=False):
    """offset (round 3): log of the place's prior permit pace; the size part learns homes per acre relative to it."""
    from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
    y, w, ac = R["y5"].clip(lower=0).values, R["w"].values, R["acres"].clip(lower=0.01).values
    off = np.zeros(len(R)) if offset is None else offset
    built = y > 0
    clf = HistGradientBoostingClassifier(random_state=seed).fit(X[fit], built[fit], sample_weight=w[fit])
    fb = fit & built
    # round 4: the size part predicts homes per lot (acres is a trait), not homes per acre times acres, which
    # extrapolated to hundreds of homes on 600-acre farm and park parcels in Kansas City (round 3 worst miss)
    unit = np.ones(len(R)) if per_lot else ac
    t = np.log(y[fb] / unit[fb]) - off[fb]
    reg = HistGradientBoostingRegressor(random_state=seed).fit(X[fb], t, sample_weight=w[fb])
    resid = t - reg.predict(X[fb])
    smear = float(np.average(np.exp(resid), weights=w[fb]))   # Duan smearing back from logs
    cap = float(np.quantile(y[fb] / unit[fb], 0.99))
    p = clf.predict_proba(X[pred_mask])[:, 1]
    hpa = np.clip(np.exp(reg.predict(X[pred_mask]) + off[pred_mask]) * smear, 0, cap)
    return p * hpa * unit[pred_mask]


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--seed", type=int, default=20261031)
    a = ap.parse_args(argv)
    D = pd.read_parquet(L.OUT / "lots_rebuilt_halfmile.parquet")
    D = D[~D["city"].isin(L.HOLD)].reset_index(drop=True)
    D = L.five_year_basis(L.dedupe_lots(D)).reset_index(drop=True)
    R = long_rows(D)
    series, hu = bps_series()
    X = traits(R, a.round, series, hu)
    off = None
    if a.round >= 3:   # place pace as an offset, not just a trait; missing (New York before 2000) -> median
        pr = X["place_permits_per_1000_prior"]
        off = np.log(pr.fillna(pr.median()).clip(lower=0.1)).values
    pred_loco = np.full(len(R), np.nan)
    cities = sorted(R["city"].unique())
    for c in cities:
        te = (R["city"] == c).values
        tr = R["city"].isin(L.training_cities(cities, c)).values
        pred_loco[te] = fit_predict(X, R, tr, te, a.seed, off, a.round >= 4)
    # forward test: fit on before windows only; predict the no-reform cities' after windows
    fwd = (R["window"] == "after").values
    pred_fwd = np.full(len(R), np.nan)
    pred_fwd[fwd] = fit_predict(X, R, (R["window"] == "before").values, fwd, a.seed, off, a.round >= 4)
    R["pred_loco"], R["pred_fwd"] = pred_loco, pred_fwd
    acres_rate = None
    rows = []
    for (c, w, s0), g in R.groupby(["city", "window", "start"]):
        wt = g["w"]
        tr = (R["city"].isin(L.training_cities(cities, c)))
        flat = float((R.loc[tr, "y5"] * R.loc[tr, "w"]).sum() / (R.loc[tr, "acres"].clip(lower=0.01) * R.loc[tr, "w"]).sum())
        rows.append({"city": c, "window": w, "start": int(s0), "end": int(g["end"].iloc[0]), "lots": len(g),
                     "homes_2010": float((g["census_homes"] * wt).sum()), "actual": float((g["y5"] * wt).sum()),
                     "model_place_out": float((g["pred_loco"] * wt).sum()),
                     "model_forward": float((g["pred_fwd"] * wt).sum()) if w == "after" else np.nan,
                     "flat": flat * float((g["acres"].clip(lower=0.01) * wt).sum())})
    T = pd.DataFrame(rows).merge(bps_baseline(R, series, hu), on=["city", "window", "start"])
    for col in ("actual", "model_place_out", "model_forward", "bps_same_pace", "flat"):
        T[f"{col}_per1000_yr"] = T[col] / 5 / (T["homes_2010"] / 1000)
    for col in ("model_place_out", "model_forward", "bps_same_pace", "flat"):
        ok = (T[col] > 0) & (T["actual"] > 0)
        T[f"abslog_{col}"] = np.abs(np.log(T[col] / T["actual"])).where(ok)
    tag = "" if a.seed == 20261031 else f"_seed{a.seed}"
    T.round(3).to_csv(REFERENCE / f"tod_pace_loop_round{a.round}{tag}.csv", index=False)
    pd.set_option("display.width", 250)
    print(T[["city", "window", "start", "end", "actual", "model_place_out", "model_forward", "bps_same_pace", "flat",
             "actual_per1000_yr", "bps_same_pace_per1000_yr"]].round(1).to_string(index=False))
    af = T["window"] == "after"
    print("median |log|, held-out place (all city-windows): model", round(T["abslog_model_place_out"].median(), 3),
          " permit-survey same pace", round(T["abslog_bps_same_pace"].median(), 3), " flat", round(T["abslog_flat"].median(), 3))
    print("median |log|, forward (no-reform after windows): model", round(T.loc[af, "abslog_model_forward"].median(), 3),
          " permit-survey same pace", round(T.loc[af, "abslog_bps_same_pace"].median(), 3))


if __name__ == "__main__":
    main()
