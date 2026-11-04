"""Trait ranking for the parking all-variables models, with and without San Francisco (check after the result, not a
new test; Ryan 2026-11-04 17:38 UTC). Registered set-up (docs/parking/ALLVARS_PLAN.md): the places and variables in
reference/parking_allvars_values.csv, 10-fold cross-validation repeated 20 times, seed 20261027, all six tools in the
loop so the random stream matches the registered run.

Importance: permutation importance on held-out folds, for the random forest and gradient boosting. In each fold, each
trait's column in the left-out places is shuffled (separate random stream, seed 20261104) and the rise in mean
absolute error is recorded. Scored with home weights (homes x after-years, as registered) and with equal weights
(fit and score with weight 1).

    uv run --all-extras python scripts/check_parking_allvars_importance.py
Outputs: reference/parking_allvars_importance.csv, reference/parking_allvars_importance_gains.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_allvars as ra  # noqa: E402
import run_parking_expanded as rpe  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

SF = "San Francisco, California, United States"
TOOLS = ["one average", "lasso", "elastic net", "random forest", "gradient boosting", "causal forest (honest)"]
RANKED = ("random forest", "gradient boosting")


def run(d: pd.DataFrame, feats: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(ra.SEED)
    prng = np.random.default_rng(20261104)
    per_repeat = {t: [] for t in TOOLS}
    imp = {t: np.zeros(len(feats)) for t in RANKED}
    total_w = 0.0
    y, w = d["effect"].values, d["weight"].values
    for _ in range(ra.REPEATS):
        perm = rng.permutation(len(d))
        errs, W = {t: 0.0 for t in TOOLS}, 0.0
        for f in range(ra.FOLDS):
            te = perm[f::ra.FOLDS]
            tr = np.setdiff1d(np.arange(len(d)), te)
            Xtr, Xte = rpe._impute(d.iloc[tr], d.iloc[te], feats)
            for t in TOOLS:
                if t in RANKED:
                    pr, model_predict = fit_predict(t, Xtr, y[tr], w[tr], Xte, rng)
                    base = (np.abs(pr - y[te]) * w[te]).sum()
                    for j in range(len(feats)):
                        Xp = Xte.copy()
                        Xp[:, j] = prng.permutation(Xp[:, j])
                        imp[t][j] += (np.abs(model_predict(Xp) - y[te]) * w[te]).sum() - base
                else:
                    pr = ra.predict(t, Xtr, y[tr], w[tr], Xte, rng)
                errs[t] += (np.abs(pr - y[te]) * w[te]).sum()
            W += w[te].sum()
        total_w += W
        for t in TOOLS:
            per_repeat[t].append(errs[t] / W)
    b = np.array(per_repeat["one average"])
    gains = pd.DataFrame([dict(model=t, error=np.mean(v), gain=1 - np.mean(v) / b.mean(),
                               repeats_beating_average=int((np.array(v) < b).sum())) for t, v in per_repeat.items()])
    rows = []
    for t in RANKED:
        s = pd.Series(imp[t] / total_w, index=feats).sort_values(ascending=False)
        for r, (f, v) in enumerate(s.items(), 1):
            rows.append(dict(model=t, trait=f, importance=v, rank=r))
    return gains, pd.DataFrame(rows)


def fit_predict(tool, Xtr, ytr, wtr, Xte, rng):
    """Same models and settings as ra.predict / rpe.predict, returning a predictor for shuffled copies too."""
    from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    sc = StandardScaler().fit(Xtr)
    A = sc.transform(Xtr)
    if tool == "random forest":
        m = RandomForestRegressor(n_estimators=500, min_samples_leaf=5, random_state=int(rng.integers(1e9)), n_jobs=-1)
    else:
        m = HistGradientBoostingRegressor(max_depth=2, learning_rate=0.05, max_iter=300, early_stopping=True,
                                          validation_fraction=0.2, n_iter_no_change=20, min_samples_leaf=5,
                                          random_state=int(rng.integers(1e9)))
    m.fit(A, ytr, sample_weight=wtr)
    pred = lambda X: m.predict(sc.transform(X))  # noqa: E731
    return pred(Xte), pred


def main() -> None:
    v = pd.read_csv(REFERENCE / "parking_allvars_values.csv")
    e = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    e = e[(e["status"] == "included") & (e["outcome"] == "all")][["prn_key", "effect", "weight"]]
    d0 = v.merge(e, on="prn_key").reset_index(drop=True)
    feats = [c for c in v.columns if c not in ("prn_key", "place", "state")]
    print(len(d0), "places,", len(feats), "variables")
    gains, imps = [], []
    for label, d in (("with SF", d0), ("without SF", d0[d0["prn_key"] != SF].reset_index(drop=True))):
        for wlab, dd in (("home weights", d), ("equal weights", d.assign(weight=1.0))):
            g, im = run(dd, feats)
            gains.append(g.assign(run=label, weights=wlab, places=len(dd)))
            imps.append(im.assign(run=label, weights=wlab))
            print(label, wlab, g[["model", "gain", "repeats_beating_average"]].round(3).to_string(index=False), flush=True)
    G, I = pd.concat(gains), pd.concat(imps)
    G.round(4).to_csv(REFERENCE / "parking_allvars_importance_gains.csv", index=False)
    I.round(5).to_csv(REFERENCE / "parking_allvars_importance.csv", index=False)
    for wlab in ("home weights", "equal weights"):
        for t in RANKED:
            a = I[(I.model == t) & (I.weights == wlab) & (I.run == "with SF")].set_index("trait")
            b = I[(I.model == t) & (I.weights == wlab) & (I.run == "without SF")].set_index("trait")
            top = a.sort_values("rank").head(10).index.union(b.sort_values("rank").head(10).index)
            tab = pd.DataFrame({"rank_with_sf": a.loc[top, "rank"], "rank_without_sf": b.loc[top, "rank"],
                                "imp_with": a.loc[top, "importance"], "imp_without": b.loc[top, "importance"]}).sort_values("rank_with_sf")
            print(f"\n{t}, {wlab}\n", tab.round(4).to_string())


if __name__ == "__main__":
    main()
