"""Which traits matter most for development with no reform: permutation importance of the baseline random forest
(docs/tod/MODEL_MENU_RESULTS.md, round 3, all traits, Milwaukee survey fix).

    uv run --all-extras python scripts/run_tod_pace_importance.py

Fits the round-3 random forest on every row (thinned as in the menu), then shuffles one trait at a time on a held-back
sample of 60,000 lot-windows and records how much the weighted squared error rises (5 shuffles each).
Writes reference/tod_pace_importance.csv.
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
import run_tod_lot_model as L  # noqa: E402
import run_tod_model_menu as M  # noqa: E402
import run_tod_pace_loop as P  # noqa: E402


def main() -> None:
    from sklearn.inspection import permutation_importance
    D = pd.read_parquet(L.OUT / "lots_rebuilt_halfmile.parquet")
    D = L.five_year_basis(L.dedupe_lots(D)).reset_index(drop=True)
    R = P.long_rows(D)
    for c, v in {"Chicago": ("Chicago city", "17"), "Madison": ("Madison city", "55"), "Bellevue": ("Bellevue city", "53")}.items():
        P.PLACE.setdefault(c, v)
    series, hu = P.bps_series()
    M.milwaukee_fix(series)
    X = P.traits(R, 2, series, hu)
    y, w = R["y5"].clip(lower=0).values, R["w"].values
    rng = np.random.default_rng(M.SEED)
    hold = rng.random(len(R)) < 0.15   # held back from the fit, used for the shuffles
    keep, w2 = M.thin(y, w, ~hold)
    m = M.Method(4).fit(X[keep], y[keep], w2[keep])
    hk, hw = M.thin(y, w, hold)
    ix = np.flatnonzero(hk)
    ix = rng.choice(ix, size=min(60000, len(ix)), replace=False)
    Xh = X.iloc[ix].fillna(m.med).replace([np.inf, -np.inf], 0)
    r = permutation_importance(m.m, Xh, y[ix], sample_weight=hw[ix], n_repeats=5, random_state=M.SEED,
                               scoring="neg_mean_squared_error", n_jobs=4)
    base = float(np.average((m.m.predict(Xh) - y[ix]) ** 2, weights=hw[ix]))
    T = pd.DataFrame({"trait": X.columns, "error_rise": r.importances_mean, "error_rise_sd": r.importances_std})
    T["error_rise_pct"] = 100 * T["error_rise"] / base
    T = T.sort_values("error_rise", ascending=False)
    T.round(4).to_csv(REFERENCE / "tod_pace_importance.csv", index=False)
    print(T.head(25).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
