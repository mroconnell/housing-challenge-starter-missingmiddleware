"""Parking: 8 methods on lots with all tract variables (docs/parking/LOT_ALL8_PLAN.md).

    uv run --all-extras python scripts/run_parking_lot_all8.py

Reuses TOD's lot table and feature builder (scripts/run_tod_lot_model.py). Outputs (aggregates only):
reference/parking_lot_all8_by_city.csv, reference/parking_lot_all8_results.csv
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
from scripts import run_parking_lot_test as LT  # noqa: E402
from scripts import run_tod_lot_model as TL  # noqa: E402

SEED, MAX_TRAIN = 20261028, 60000
REFORM = ("Seattle", "Chicago")
METHODS = ("wls", "lasso", "elastic_net", "tree", "forest", "boosting", "causal_forest", "knn")


def makers(kind):
    from sklearn.ensemble import (HistGradientBoostingClassifier, HistGradientBoostingRegressor, RandomForestClassifier,
                                  RandomForestRegressor)
    from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, LogisticRegression
    from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
    from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
    return {
        "wls": (lambda: LogisticRegression(max_iter=2000), lambda: LinearRegression(), True),
        "lasso": (lambda: LogisticRegression(penalty="l1", solver="saga", C=0.1, max_iter=500), lambda: Lasso(alpha=0.01), True),
        "elastic_net": (lambda: LogisticRegression(penalty="elasticnet", l1_ratio=0.5, solver="saga", C=0.1, max_iter=500),
                        lambda: ElasticNet(alpha=0.01, l1_ratio=0.5), True),
        "tree": (lambda: DecisionTreeClassifier(max_depth=3, min_samples_leaf=200), lambda: DecisionTreeRegressor(max_depth=3, min_samples_leaf=200), False),
        "forest": (lambda: RandomForestClassifier(n_estimators=200, min_samples_leaf=50, n_jobs=-1, random_state=SEED),
                   lambda: RandomForestRegressor(n_estimators=200, min_samples_leaf=50, n_jobs=-1, random_state=SEED), False),
        "boosting": (lambda: HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200, random_state=SEED),
                     lambda: HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=200, random_state=SEED), False),
        "knn": (lambda: KNeighborsClassifier(n_neighbors=50, n_jobs=-1), lambda: KNeighborsRegressor(n_neighbors=50, n_jobs=-1), True),
    }[kind]


def actual_extra(d: pd.DataFrame) -> tuple[float, float]:
    t, c = d[d["parking"] == 1], d[d["parking"] == 0]
    nt, nc = t["w"].sum(), c["w"].sum()
    ext = ((t.units_after * t.w).sum() - nt * (c.units_after * c.w).sum() / nc) - \
          ((t.units_before * t.w).sum() - nt * (c.units_before * c.w).sum() / nc)
    return float(ext), float(nt)


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
    for c in D["city"].unique():
        X[f"city_{c}"] = (D["city"] == c).astype(float)
    X["parking"] = D["parking"].values
    y1 = D["builds_after"].values
    y2 = np.log1p(D["units_after"].values)
    dy = (D["units_after"] - D["units_before"]).values
    print(len(D), "lots,", X.shape[1], "inputs", flush=True)

    rows = []
    for hold in REFORM:
        other = [c for c in REFORM if c != hold][0]
        te = D.index[(D["city"] == hold) & (D["parking"] == 1)].to_numpy()
        keep = D.index[D["city"] == other].to_numpy()
        rest = D.index[~D["city"].isin([hold, other])].to_numpy()
        n_rest = max(0, MAX_TRAIN - len(keep))
        tr = np.concatenate([keep, rng.choice(rest, min(n_rest, len(rest)), replace=False)]) if n_rest else rng.choice(keep, MAX_TRAIN, replace=False)
        cols = [c for c in X.columns if c != f"city_{hold}"]
        act, nt = actual_extra(D[D["city"] == hold])
        oe, on = actual_extra(D[D["city"] == other])
        base = oe / on * nt
        X1, X0 = X.loc[te, cols].copy(), X.loc[te, cols].copy()
        X0["parking"] = 0.0
        w = D.loc[tr, "w"].values
        for kind in METHODS:
            if kind == "causal_forest":
                out = []
                for g in (1.0, 0.0):
                    ix = tr[(X.loc[tr, "parking"] == g).values]
                    m = RandomForestRegressor(n_estimators=200, min_samples_leaf=50, n_jobs=-1, random_state=SEED)
                    m.fit(X.loc[ix, cols], dy[ix], sample_weight=D.loc[ix, "w"])
                    out.append(m.predict(X1))
                ex = float((out[0] - out[1]) @ D.loc[te, "w"].values)
            else:
                c1, c2, scale = makers(kind)
                sc = StandardScaler().fit(X.loc[tr, cols]) if scale else None
                T = (lambda Z: sc.transform(Z)) if scale else (lambda Z: Z.values)  # noqa: E731
                m1 = c1()
                try:
                    m1.fit(T(X.loc[tr, cols]), y1[tr], sample_weight=w)
                except TypeError:
                    m1.fit(T(X.loc[tr, cols]), y1[tr])
                b = y1[tr] == 1
                m2 = c2()
                try:
                    m2.fit(T(X.loc[tr, cols][b]), y2[tr][b], sample_weight=w[b])
                except TypeError:
                    m2.fit(T(X.loc[tr, cols][b]), y2[tr][b])
                cap = float(np.nanquantile(D.loc[tr, "units_after"].values[b], 0.99))

                def homes(Z):
                    size = np.minimum(np.expm1(np.clip(m2.predict(T(Z)), 0, 12)), cap).clip(min=1)
                    return m1.predict_proba(T(Z))[:, 1] * size
                ex = float((homes(X1) - homes(X0)) @ D.loc[te, "w"].values)
            rows.append(dict(method=kind, held_out=hold, reform_lots=nt, actual_extra_homes=act, baseline_extra=base, model_extra=ex,
                             error_baseline=abs(base - act), error_model=abs(ex - act)))
            print(kind, hold, round(act), round(base), round(ex), flush=True)
    E = pd.DataFrame(rows)
    S = E.assign(better=E["error_model"] < E["error_baseline"]).groupby("method", sort=False).agg(
        cities_better=("better", "sum"), mean_error_model=("error_model", "mean"), mean_error_baseline=("error_baseline", "mean")).reset_index()
    S["passes"] = S["cities_better"] == len(REFORM)
    E.round(3).to_csv(REFERENCE / "parking_lot_all8_by_city.csv", index=False)
    S.round(3).to_csv(REFERENCE / "parking_lot_all8_results.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
