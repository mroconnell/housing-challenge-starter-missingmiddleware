"""One round of the lot-model improvement loop (docs/tod/LOT_MODEL_PLAN.md item 49).

    uv run --all-extras python scripts/run_tod_lot_model_loop.py --round 1

Fast tool: two histogram gradient boosting models (upzoned lots under the rules after; every other lot under the rules
before), outcome = change in homes per lot on the 5-year basis. Leave-one-city-out over the training and no-reform
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


def main(argv=None) -> None:
    from sklearn.ensemble import HistGradientBoostingRegressor
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    a = ap.parse_args(argv)
    L.FIT.update(item25=True, item32=True, item34=True, item37=True, item46=True)
    D = pd.read_parquet(L.OUT / "lots_rebuilt_halfmile.parquet")
    D = D[~D["city"].isin(L.HOLD)].reset_index(drop=True)          # item 49.2: holdouts never touched here
    cache = {k: L.cost_per_home(k[0], int(k[1]) - 1) for k in set(zip(D["city"], D["eff_year"]))}
    D["cost_per_home"] = [cache[(c, y)] for c, y in zip(D["city"], D["eff_year"])]
    D = L.five_year_basis(L.dedupe_lots(D)).reset_index(drop=True)
    Xa, Xb = L.features(D, True), L.features(D, False)
    vc = [c for c in D.columns if c.startswith("v_")]
    V = D[vc].replace([np.inf, -np.inf], np.nan)
    Xa, Xb = pd.concat([Xa, V], axis=1), pd.concat([Xb, V], axis=1)
    dy = (D["ua5"] - D["ub5"]).values
    w = D["w"].values
    up = (D["treated"] == 1).values
    rows = []
    for c in sorted(D["city"].unique()):
        te = (D["city"] == c).values
        base_c = c.removesuffix(" placebo")
        tr = ~te & ~D["city"].str.removesuffix(" placebo").eq(base_c).values
        pred = np.zeros(len(D))
        for g, X in ((True, Xa), (False, Xb)):
            fit = tr & (up == g)
            if fit.sum() < 50:
                continue
            m = HistGradientBoostingRegressor(random_state=20261031)
            m.fit(X[fit], dy[fit], sample_weight=w[fit])
            pm = te & (up == g)
            if pm.any():
                Xp = X[pm].copy()
                if "rezoned_later" in Xp:
                    Xp["rezoned_later"] = 0.0
                pred[pm] = m.predict(Xp)
        ub, ua = D.loc[te, "ub5"].values, D.loc[te, "ua5"].values
        wt, u = w[te], up[te]
        rows.append({"city": c, "lots": int(te.sum()), "upzoned_lots": int(u.sum()),
                     "before": float(ub @ wt), "actual_after": float(ua @ wt), "model_after": float((ub + pred[te]) @ wt),
                     "upzoned_before": float(ub[u] @ wt[u]), "upzoned_actual_after": float(ua[u] @ wt[u]),
                     "upzoned_model_after": float((ub[u] + pred[te][u]) @ wt[u])})
        print(rows[-1], flush=True)
    R = pd.DataFrame(rows)
    R["actual_change"] = R["actual_after"] - R["before"]
    R["model_change"] = R["model_after"] - R["before"]
    R["error_after_pct"] = 100 * (R["model_after"] - R["actual_after"]) / R["actual_after"].where(R["actual_after"] != 0)
    R["error_vs_same_pace_pct"] = 100 * (R["before"] - R["actual_after"]) / R["actual_after"].where(R["actual_after"] != 0)
    R.round(1).to_csv(REFERENCE / f"tod_lot_model_loop_round{a.round}.csv", index=False)
    pd.set_option("display.width", 250)
    print(R[["city", "before", "actual_after", "model_after", "error_after_pct", "error_vs_same_pace_pct",
             "upzoned_actual_after", "upzoned_model_after"]].round(0).to_string(index=False))


if __name__ == "__main__":
    main()
