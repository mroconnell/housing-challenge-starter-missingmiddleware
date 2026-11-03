"""Parking work session backtest: boosted trees predict each repeal place's no-repeal path (D1 target, log change in 5+
unit permits), trained on comparison-pool places at the same windows. docs/parking/CAUSAL_FRAMEWORK_PLAN.md (Work session).

    uv run python scripts/run_parking_ws_backtest.py
Output: reference/parking_ws_backtest.csv, reference/parking_ws_backtest_places.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_parking_comparison as rpc  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

SEEDS = range(20261104, 20261109)


def main() -> None:
    bps = rpc.read_bps_us()
    p = cmp.panel(bps)
    b = bps.assign(key=bps["state_fips"].astype(str).str.strip() + "|" + bps["bps_id"].astype(str).str.strip()).drop_duplicates(["key", "year"])
    u5 = b.pivot_table(index="key", columns="year", values="5plus_units", aggfunc="sum")
    ut = p.pivot_table(index="key", columns="year", values="units_total", aggfunc="sum")
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001"))
    homes = homes[homes > 0]
    popn = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001"))
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    excluded = {k for r in tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
                .drop_duplicates("prn_key").itertuples() if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].copy()
    excluded |= set(real["key"])
    G = pd.read_csv(REFERENCE / "parking_ws_grid_places.csv").set_index("key")

    def m(tab, k, yrs):
        return float(np.nansum(tab.reindex(index=[k], columns=yrs).values)) / len(yrs)

    def unit(k, pre, post, e, d):
        if k not in homes.index or k not in geo.index:
            return None
        h = float(homes[k])
        yr = [m(ut, k, [y]) / h * 1000 for y in pre]
        b5, a5, bt = m(u5, k, pre), m(u5, k, post), m(ut, k, pre)
        return dict(key=k, D=d, group=e, y=np.log(a5 + 0.5) - np.log(b5 + 0.5), lb5=np.log(b5 + 0.5), lbt=np.log(bt + 0.5),
                    trend=(np.mean(yr[-2:]) - np.mean(yr[:3])) if len(yr) >= 4 else np.nan, lh=np.log(h),
                    share5=b5 / bt if bt > 0 else 0.0, div=str(geo.loc[k, "division"]), event=e)

    rows = []
    for r in real.itertuples():
        e = int(r.event_year)
        pre, post = cmp.windows(e)
        post = post[: int(r.n_post)]
        u = unit(r.key, pre, post, e, 1)
        if u:
            rows.append(u)
        ctrl, _ = cmp.controls(p, r.key, e, excluded - {r.key}, homes, popn)
        rows += [x for c in ctrl if (x := unit(c, pre, post, e, 0))]
    U = pd.DataFrame(rows).dropna(subset=["trend"])
    X = pd.concat([U[["lb5", "lbt", "trend", "lh", "share5", "event"]], pd.get_dummies(U["div"], prefix="d", dtype=float)], axis=1).values
    tr, te = (U["D"] == 0).values, (U["D"] == 1).values
    pred = np.mean([HistGradientBoostingRegressor(random_state=s).fit(X[tr], U["y"].values[tr]).predict(X[te]) for s in SEEDS], axis=0)
    R = U[te].assign(pred=pred, effect_bt=lambda d: d["y"] - d["pred"]).set_index("key")
    R = R.join(G[["weight", "effect_main", "rate5_before", "d1"]], how="inner").dropna(subset=["effect_main", "rate5_before", "d1"])
    R.reset_index().to_csv(REFERENCE / "parking_ws_backtest_places.csv", index=False)
    w, act, rate = R["weight"].values, R["effect_main"].values, R["rate5_before"].values
    n = len(R)
    out = []
    rng = np.random.default_rng(20261104)
    for col, lab in (("effect_bt", "backtest: boosted no-repeal path (D1)"), ("d1", "matched comparison (D1)")):
        v = R[col].values
        pr = np.array([(np.exp(np.average(np.delete(v, i), weights=np.delete(w, i))) - 1) * rate[i] for i in range(n)])
        f = lambda i: np.sum(v[i] * w[i]) / np.sum(w[i])  # noqa: E731
        bs = np.array([f(rng.integers(0, n, n)) for _ in range(2000)])
        out.append(dict(version=lab, places=n, estimate=f(np.arange(n)), pct=100 * (np.exp(f(np.arange(n))) - 1),
                        p05=np.percentile(bs, 5), p95=np.percentile(bs, 95), p0125=np.percentile(bs, 1.25), p9875=np.percentile(bs, 98.75),
                        heldout_error=np.average(np.abs(act - pr), weights=w), error_zero=np.average(np.abs(act), weights=w)))
    S = pd.DataFrame(out)
    S["training_units"] = int(tr.sum())
    S["unit"] = "estimate: log change in 5+ permits; errors: permits per 1,000 existing homes a year"
    S.to_csv(REFERENCE / "parking_ws_backtest.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.drop(columns="unit").round(3).to_string(index=False))


if __name__ == "__main__":
    main()
