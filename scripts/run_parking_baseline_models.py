"""Parking: full set of baseline (no-reform) models (docs/parking/BASELINE_MODELS_PLAN.md).

    uv run --all-extras python scripts/run_parking_baseline_models.py --round N

Uses the no-reform model's data (scripts/run_parking_no_reform.py, round 6). Outputs:
reference/parking_baseline_models_{scores,wisconsin,choices,checks}_rN.csv
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from econml.grf import RegressionForest
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import ElasticNet, Lasso, PoissonRegressor
from sklearn.model_selection import GroupKFold
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
ROUND = int(sys.argv[sys.argv.index("--round") + 1]) if "--round" in sys.argv else 1
_argv = sys.argv
sys.argv = [sys.argv[0], "--round", "6"]
import run_parking_no_reform as NR  # noqa: E402
sys.argv = _argv
from missing_middleware.parking import checks  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

warnings.filterwarnings("ignore")
TAG = f"_r{ROUND}"
COLS = NR.BASE + NR.ACS + ["fake_reform"]
CENTRAL, PUBLISHED = 122_619, 118_822

# model -> (constructor(setting, seed), grid)
MODELS = {
    "Weighted Poisson regression": (lambda g, s: make_pipeline(StandardScaler(), PoissonRegressor(alpha=g, max_iter=1000)), [1e-4, 1e-3, 1e-2, 1e-1]),
    "Lasso": (lambda g, s: make_pipeline(StandardScaler(), Lasso(alpha=g, max_iter=5000)), [0.01, 0.1, 0.5, 2.0]),
    "Elastic net": (lambda g, s: make_pipeline(StandardScaler(), ElasticNet(alpha=g, l1_ratio=0.5, max_iter=5000)), [0.01, 0.1, 0.5, 2.0]),
    "Depth-3 tree": (lambda g, s: DecisionTreeRegressor(max_depth=3, min_samples_leaf=g, random_state=s), [20, 100]),
    "Random forest": (lambda g, s: RandomForestRegressor(n_estimators=300, min_samples_leaf=g, max_features=0.5, n_jobs=-1, random_state=s), [5, 20]),
    "Boosted trees": (lambda g, s: HistGradientBoostingRegressor(loss="poisson", learning_rate=g[0], max_leaf_nodes=g[1], max_iter=300,
                                                                  min_samples_leaf=40, random_state=s), [(0.05, 15), (0.05, 31), (0.1, 15), (0.03, 31)]),
    "Honest forest (GRF)": (lambda g, s: RegressionForest(n_estimators=500, min_samples_leaf=g, honest=True, inference=False, n_jobs=-1, random_state=s), [5, 20]),
    "50 nearest neighbours": (lambda g, s: make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=50, weights=g)), ["uniform", "distance"]),
}
NO_WEIGHT = {"50 nearest neighbours"}


def xy(df, med):
    X = df[COLS].fillna(med)
    y = (df["actual"] / df["homes"] * 1000).clip(lower=0)
    return X, y


def fit(name, g, seed, df, med):
    ctor, _ = MODELS[name]
    m = ctor(g, seed)
    X, y = xy(df, med)
    w = (df["homes"] / 1000).values
    if name in NO_WEIGHT:
        m.fit(X, y)
    elif isinstance(m, RegressionForest):
        m.fit(X.values, y.values, sample_weight=w)
    elif hasattr(m, "steps"):
        m.fit(X, y, **{f"{m.steps[-1][0]}__sample_weight": w})
    else:
        m.fit(X, y, sample_weight=w)
    return m


def predict(m, df, med, flags_neg):
    X = df[COLS].fillna(med)
    r = np.asarray(m.predict(X.values if isinstance(m, RegressionForest) else X)).ravel()
    bad = ~np.isfinite(r) | (r < 0)
    flags_neg.append(int(bad.sum()))
    r = np.where(np.isfinite(r), np.clip(r, 0, None), 0.0)
    return r * df["homes"].values / 1000


def choose(name, df, seed):
    _, grid = MODELS[name]
    best, bs = grid[0], np.inf
    if len(grid) == 1:
        return best
    for g in grid:
        s = []
        for a, b in GroupKFold(n_splits=5).split(df, groups=df["key"]):
            fa, fb = df.iloc[a], df.iloc[b]
            med = fa[COLS].median()
            pr = predict(fit(name, g, seed, fa, med), fb, med, [])
            s.append(NR.score(pr, fb["actual"].values)["median_abs_log"])
        if np.mean(s) < bs:
            best, bs = g, float(np.mean(s))
    return best


def benchmarks(pool, new):
    return {"M0 same pace": new["units_3y"].values,
            "M1 same pace x state momentum": (new["units_3y"] * new["state_fips_momentum"].fillna(1)).values,
            "M2 shrunk 3-year": NR.m2_shrunk(pool, new)}


def main() -> None:
    R, reform_year, *_ = NR.prepare()
    train = R[R["no_reform"]].copy()
    real_years = [y for y in reform_year.values() if 2012 <= y <= 2022]
    places = train.drop_duplicates("key")[["key", "division", "state_fips"]]
    rows, choices, negs = [], [], {}
    for seed in NR.SEEDS:
        rng = np.random.default_rng(seed)
        nonwi = places[places["state_fips"] != NR.WI]
        held = set()
        for dv, g in nonwi.groupby("division"):
            held |= set(rng.choice(g["key"].values, size=max(1, int(round(0.2 * len(g)))), replace=False))
        tr_keys = sorted(set(nonwi["key"]) - held)
        fake_keys = sorted(rng.choice(tr_keys, size=int(0.1 * len(tr_keys)), replace=False))
        fake_year = {k: int(rng.choice(real_years)) for k in fake_keys}
        T = train.assign(fake_reform=[int(k in fake_year and o >= fake_year[k]) for k, o in zip(train["key"], train["origin"])])
        F = T[T["key"].isin(tr_keys) & T["origin"].isin(NR.FIT_ORIGINS) & T["actual"].notna()]
        pool = T[T["key"].isin(tr_keys)]
        med = F[COLS].median()
        tests = {"held-out places, later years": T[T["key"].isin(held) & T["origin"].isin(NR.TEST_ORIGINS)],
                 "training places, later years": T[T["key"].isin(tr_keys) & T["origin"].isin(NR.TEST_ORIGINS)],
                 "Wisconsin, later years": T[(T["state_fips"] == NR.WI) & T["origin"].isin(NR.TEST_ORIGINS)]}
        tests = {k: v[v["actual"].notna()] for k, v in tests.items()}
        fitted = {}
        for name in MODELS:
            g = choose(name, F, seed)
            choices.append(dict(seed=seed, model=name, setting=str(g)))
            fitted[name] = (fit(name, g, seed, F, med), g)
        for tname, te in tests.items():
            preds = benchmarks(pool, te)
            for name, (m, g) in fitted.items():
                nb = []
                preds[name] = predict(m, te, med, nb)
                negs[name] = negs.get(name, 0) + sum(nb)
                if tname == "held-out places, later years":
                    on = predict(m, te.assign(fake_reform=1), med, [])
                    off = predict(m, te.assign(fake_reform=0), med, [])
                    rows.append(dict(seed=seed, test="fake on-off", model=name, mean_on_minus_off=float(np.mean(on - off))))
            for name, pr in preds.items():
                rows.append(dict(seed=seed, test=tname, model=name, **NR.score(pr, te["actual"].values)))
                if tname == "training places, later years":
                    st = te.assign(pred=pr).groupby(["state_fips", "origin"])[["pred", "actual"]].sum()
                    rows.append(dict(seed=seed, test="state totals, later years", model=name, **NR.score(st["pred"].values, st["actual"].values)))
                if tname == "held-out places, later years":
                    k = te.assign(pred=pr, miss=pr - te["actual"].values)
                    w = k.loc[k["miss"].abs().idxmax()]
                    rows[-1].update(worst=f"{w['name']} {w['key']} origin {w['origin']}: predicted {w['pred']:.0f}, actual {w['actual']:.0f}")
        print("seed", seed, "done", flush=True)
    S = pd.DataFrame(rows)
    S.to_csv(REFERENCE / f"parking_baseline_models_scores{TAG}.csv", index=False)
    pd.DataFrame(choices).to_csv(REFERENCE / f"parking_baseline_models_choices{TAG}.csv", index=False)

    # Wisconsin: fit on all non-Wisconsin rows (origins 2016-2019), back-test origin 2019, forecast origin 2025
    allfit = train[(train["state_fips"] != NR.WI) & train["actual"].notna()].assign(fake_reform=0)
    med = allfit[COLS].median()
    seed = NR.SEEDS[0]
    W = []
    for o in (2019, 2025):
        te = R[(R["state_fips"] == NR.WI) & (R["origin"] == o)].assign(fake_reform=0)
        preds = benchmarks(train[train["state_fips"] != NR.WI], te)
        for name in MODELS:
            g = pd.DataFrame(choices).query("model == @name")["setting"].mode().iloc[0]
            g = MODELS[name][1][[str(x) for x in MODELS[name][1]].index(g)]
            preds[name] = predict(fit(name, g, seed, allfit, med), te, med, [])
        for name, pr in preds.items():
            row = dict(origin=o, model=name, places=len(te), five_year_total=float(pr.sum() * 5))
            if o == 2019:
                row.update(**NR.score(pr, te["actual"].values))
            W.append(row)
    W = pd.DataFrame(W)
    m0 = W.query("model == 'M0 same pace'").set_index("origin")["five_year_total"]
    W["vs_M0"] = W["five_year_total"] / W["origin"].map(m0)
    W["wisconsin_2027_2031_scaled_to_122619_central"] = np.where(W["origin"] == 2025, W["vs_M0"] * CENTRAL, np.nan)
    W["wisconsin_2027_2031_scaled_to_118822_as_published"] = np.where(W["origin"] == 2025, W["vs_M0"] * PUBLISHED, np.nan)
    W.to_csv(REFERENCE / f"parking_baseline_models_wisconsin{TAG}.csv", index=False)

    flags = [dict(check="negative or non-finite predictions clipped", where=n, value=v, note="held-out rows over 5 seeds")
             for n, v in negs.items() if v]
    far = W[(W["origin"] == 2025) & ((W["vs_M0"] - 1).abs() > 0.25)]
    flags += [dict(check="Wisconsin total more than 25% from same pace", where=r.model, value=round(r.vs_M0, 3)) for r in far.itertuples()]
    ws = S[S["test"] == "held-out places, later years"].query("seed == @NR.SEEDS[0]")
    flags += [dict(check="worst miss (seed 1)", where=r.model, note=r.worst) for r in ws.itertuples()]
    checks.report(flags, REFERENCE / f"parking_baseline_models_checks{TAG}.csv")

    pd.set_option("display.width", 220)
    T1 = S[S["test"] != "fake on-off"].groupby(["test", "model"])[["median_abs_log", "total_ratio"]].agg(["mean", "min", "max"]).round(3)
    print(T1.to_string())
    print(S[S["test"] == "fake on-off"].groupby("model")["mean_on_minus_off"].agg(["mean", "min", "max"]).round(2).to_string())
    print(W.round(3).to_string())


if __name__ == "__main__":
    main()
