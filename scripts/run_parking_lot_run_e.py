"""Parking lot test redone TOD's run-E way (docs/parking/LOT_RUN_E_PLAN.md).

    uv run --all-extras python scripts/run_parking_lot_run_e.py

Outputs (aggregates only): reference/parking_lot_run_e_by_city.csv, reference/parking_lot_run_e_results.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.paths import REFERENCE  # noqa: E402
from scripts import run_parking_lot_all8 as A8  # noqa: E402
from scripts import run_parking_lot_test as LT  # noqa: E402
from scripts import run_tod_lot_model as TL  # noqa: E402

SEED, MAX_TRAIN = 20261028, 60000


def main() -> None:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    rng = np.random.default_rng(SEED)
    D = LT.lots()
    D = D[D["treated"] == 0].copy()
    cache = {k: TL.cost_per_home(k[0], int(k[1]) - 1) for k in set(zip(D["city"], D["eff_year"]))}
    D["cost_per_home"] = [cache[(c, y)] for c, y in zip(D["city"], D["eff_year"])]
    key = D["city"] + "|" + D["x5070"].round(1).astype(str) + "|" + D["y5070"].round(1).astype(str)
    D["w"] = 1.0 / key.map(key.value_counts())
    D = D.reset_index(drop=True)
    X = TL.features(D, True)
    vc = [c for c in D.columns if c.startswith("v_")]
    V = D[vc].replace([np.inf, -np.inf], np.nan)
    X = pd.concat([X, V.fillna(V.median())], axis=1)
    y1, y2 = D["builds_after"].values, np.log1p(D["units_after"].values)
    dy = (D["units_after"] - D["units_before"]).values
    cols = list(X.columns)
    rows = []
    for hold in A8.REFORM:
        other = [c for c in A8.REFORM if c != hold][0]
        te = D.index[(D["city"] == hold) & (D["parking"] == 1)].to_numpy()
        tr_r = D.index[(D["city"] == other) & (D["parking"] == 1)].to_numpy()
        pool = D.index[(D["city"] != hold) & (D["parking"] == 0)].to_numpy()
        tr_n = rng.choice(pool, min(MAX_TRAIN, len(pool)), replace=False)
        act, nt = A8.actual_extra(D[D["city"] == hold])
        oe, on = A8.actual_extra(D[D["city"] == other])
        base = oe / on * nt
        wt = D.loc[te, "w"].values
        for kind in A8.METHODS:
            if kind == "causal_forest":
                p = []
                for ix in (tr_r, tr_n):
                    m = RandomForestRegressor(n_estimators=200, min_samples_leaf=50, n_jobs=-1, random_state=SEED)
                    m.fit(X.loc[ix, cols], dy[ix], sample_weight=D.loc[ix, "w"])
                    p.append(m.predict(X.loc[te, cols]))
                ex = float((p[0] - p[1]) @ wt)
            else:
                preds = []
                for ix in (tr_r, tr_n):
                    c1, c2, scale = A8.makers(kind)
                    sc = StandardScaler().fit(X.loc[ix, cols]) if scale else None
                    T = (lambda Z, s=sc: s.transform(Z)) if scale else (lambda Z: Z.values)
                    w = D.loc[ix, "w"].values
                    m1 = c1()
                    try:
                        m1.fit(T(X.loc[ix, cols]), y1[ix], sample_weight=w)
                    except TypeError:
                        m1.fit(T(X.loc[ix, cols]), y1[ix])
                    b = y1[ix] == 1
                    m2 = c2()
                    if b.sum() >= 5:
                        try:
                            m2.fit(T(X.loc[ix, cols][b]), y2[ix][b], sample_weight=w[b])
                        except TypeError:
                            m2.fit(T(X.loc[ix, cols][b]), y2[ix][b])
                        cap = float(np.nanquantile(D.loc[ix, "units_after"].values[b], 0.99))
                        size = np.minimum(np.expm1(np.clip(m2.predict(T(X.loc[te, cols])), 0, 12)), cap).clip(min=1)
                    else:
                        size = np.ones(len(te))
                    preds.append(m1.predict_proba(T(X.loc[te, cols]))[:, 1] * size)
                # change in homes: after-period prediction minus the lot's own before-period homes is common to both
                # models, so extra homes = reform model - no-reform model
                ex = float((preds[0] - preds[1]) @ wt)
            rows.append(dict(method=kind, held_out=hold, reform_lots=nt, actual_extra_homes=act, baseline_extra=base,
                             model_extra=ex, error_baseline=abs(base - act), error_zero=abs(act), error_model=abs(ex - act)))
            print(kind, hold, round(act), round(base), round(ex), flush=True)
    E = pd.DataFrame(rows)
    S = E.groupby("method", sort=False).agg(mean_error_model=("error_model", "mean"), mean_error_baseline=("error_baseline", "mean"),
                                            mean_error_zero=("error_zero", "mean"),
                                            cities_beating_baseline=("error_model", lambda s: int((s.values < E.loc[s.index, "error_baseline"].values).sum()))).reset_index()
    S["passes"] = (S["mean_error_model"] < S["mean_error_baseline"]) & (S["mean_error_model"] < S["mean_error_zero"]) & (S["cities_beating_baseline"] == 2)
    E.round(3).to_csv(REFERENCE / "parking_lot_run_e_by_city.csv", index=False)
    S.round(3).to_csv(REFERENCE / "parking_lot_run_e_results.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
