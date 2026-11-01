"""Re-score the TOD share-model menu with the audit's fixes (docs/tod/MODEL_MENU_RESULTS.md; audit review 2026-11-01).

    uv run --all-extras python scripts/run_tod_share_menu_score.py

No refits: reads each method's per-city table (reference/tod_menu_share_{method}.csv) and the Wisconsin raw B from
the menu summaries. Fixes:
1. K for a scored city is computed leaving that city out (no leak).
2. No-model benchmark: share before + the other cities' average change in share.
3. Correlation of predicted uplift with the actual change in share (does the model rank the change?).
4. K's spread by left-out city.
5. Wisconsin calibrated B with K from all 9 cities (Wisconsin is never scored), the range of left-out K's, and the
   benchmark B = average change x the Wisconsin table totals x the statewide scale.
Writes reference/tod_menu_share_rescored.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from missing_middleware.paths import REFERENCE  # noqa: E402

METHODS = ["plain_average", "linear_regression", "lasso", "regression_tree", "random_forest", "gradient_boosting",
           "nearest_neighbours", "multilevel", "causal_forest", "causal_forest_sklearn", "causal_forest_sklearn_honest"]
WI_TABLE_TOTAL = 4738.918 + 12838.593   # Milwaukee + Madison table totals 2027-2031 (Wisconsin net rounds)
SCALE = 14463.78 / (9220.49 + 3393.66)


def abslog(p, a):
    p, a = np.asarray(p, float), np.asarray(a, float)
    return np.where((p > 0) & (a > 0), np.abs(np.log(np.where(p > 0, p, 1) / np.where(a > 0, a, 1))), np.nan)


def main() -> None:
    S = pd.concat([pd.read_csv(f) for f in sorted(REFERENCE.glob("tod_menu_share_summary*.csv"))
                   if "without" not in f.name and "rescored" not in f.name]).drop_duplicates("method", keep="last").set_index("method")
    rows = []
    bench_done = False
    for m in METHODS:
        R = pd.read_csv(REFERENCE / f"tod_menu_share_{m}.csv")
        k_loo = np.array([R.loc[R.city != c, "actual_change"].sum() / R.loc[R.city != c, "model_uplift"].sum() for c in R.city])
        cal = R["share_before"] + k_loo * R["model_uplift"]
        k_all = R["actual_change"].sum() / R["model_uplift"].sum()
        if not bench_done:   # the no-model benchmark is the same for every method
            avg_other = np.array([R.loc[R.city != c, "actual_change"].mean() for c in R.city])
            bench = abslog(R["share_before"] + avg_other, R["share_after"])
            avg_change = R["actual_change"].mean()
            rows.append({"method": "benchmark: same share + others' average change", "calibrated_K_left_out": np.nanmedian(bench),
                         "WI_B_calibrated": avg_change * WI_TABLE_TOTAL * SCALE, "avg_change": avg_change})
            rows.append({"method": "benchmark: same share as before",
                         "calibrated_K_left_out": np.nanmedian(abslog(R["share_before"], R["share_after"]))})
            bench_done = True
        braw = float(S.loc[m, "WI_B_raw"])
        rows.append({"method": m, "raw": np.nanmedian(abslog(R["model_on"], R["share_after"])),
                     "calibrated_K_left_out": np.nanmedian(abslog(cal, R["share_after"])),
                     "uplift_vs_change_corr": float(np.corrcoef(R["model_uplift"], R["actual_change"])[0, 1]),
                     "K_all9": k_all, "K_left_out_min": k_loo.min(), "K_left_out_max": k_loo.max(),
                     "WI_B_raw": braw, "WI_B_calibrated": k_all * braw,
                     "WI_B_cal_low": k_loo.min() * braw, "WI_B_cal_high": k_loo.max() * braw})
    T = pd.DataFrame(rows)
    T.round(4).to_csv(REFERENCE / "tod_menu_share_rescored.csv", index=False)
    pd.set_option("display.width", 250)
    print(T.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
