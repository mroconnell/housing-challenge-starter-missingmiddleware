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
    "Weighted Poisson regression": (lambda g, s: make_pipeline(StandardScaler(), PoissonRegressor(alpha=g, max_iter=1000)), [1e-5, 1e-4, 1e-3, 1e-2, 1e-1]),
    "Lasso": (lambda g, s: make_pipeline(StandardScaler(), Lasso(alpha=g, max_iter=5000)), [1e-5, 1e-4, 1e-3, 0.01, 0.1, 0.5]),
    "Elastic net": (lambda g, s: make_pipeline(StandardScaler(), ElasticNet(alpha=g, l1_ratio=0.5, max_iter=5000)), [1e-5, 1e-4, 1e-3, 0.01, 0.1, 0.5]),
    "Depth-3 tree": (lambda g, s: DecisionTreeRegressor(max_depth=3, min_samples_leaf=g, random_state=s), [1, 5, 20, 100]),
    "Random forest": (lambda g, s: RandomForestRegressor(n_estimators=300, min_samples_leaf=g, max_features=0.5, n_jobs=-1, random_state=s), [2, 5, 20]),
    "Boosted trees": (lambda g, s: HistGradientBoostingRegressor(loss="poisson", learning_rate=g[0], max_leaf_nodes=g[1], max_iter=300,
                                                                  min_samples_leaf=40, random_state=s), [(0.05, 15), (0.05, 31), (0.1, 15), (0.03, 31), (0.05, 63), (0.1, 31), (0.05, 127)]),
    "Honest forest (GRF)": (lambda g, s: RegressionForest(n_estimators=500, min_samples_leaf=g, honest=True, inference=False, n_jobs=-1, random_state=s), [1, 2, 5, 20]),
    "50 nearest neighbours": (lambda g, s: make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=50, weights=g)), ["uniform", "distance"]),
}
NO_WEIGHT = {"50 nearest neighbours"}


LOG_TARGET = {"Lasso", "Elastic net"}  # round 2: fitted on log(1 + rate), so predictions cannot go negative


def xy(df, med, name=""):
    X = df[COLS].fillna(med)
    y = (df["actual"] / df["homes"] * 1000).clip(lower=0)
    if ROUND >= 2 and name in LOG_TARGET:
        y = np.log1p(y)
    return X, y


def fit(name, g, seed, df, med):
    ctor, _ = MODELS[name]
    m = ctor(g, seed)
    X, y = xy(df, med, name)
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


def predict(m, df, med, flags_neg, name=""):
    X = df[COLS].fillna(med)
    r = np.asarray(m.predict(X.values if isinstance(m, RegressionForest) else X)).ravel()
    if ROUND >= 2 and name in LOG_TARGET:
        r = np.expm1(r)
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
            pr = predict(fit(name, g, seed, fa, med), fb, med, [], name)
            s.append(NR.score(pr, fb["actual"].values)["median_abs_log"])
        if np.mean(s) < bs:
            best, bs = g, float(np.mean(s))
    return best


def level(fitted):
    """M0L's level factor: permits actually issued over same pace, summed over the fitted rows (no test data)."""
    f = fitted[fitted["actual"].notna()]
    return float(f["actual"].sum() / f["units_3y"].sum())


def benchmarks(pool, new, lev=None):
    out = {"M0 same pace": new["units_3y"].values,
            "M1 same pace x state momentum": (new["units_3y"] * new["state_fips_momentum"].fillna(1)).values,
            "M2 shrunk 3-year": NR.m2_shrunk(pool, new)}
    if lev is not None:  # round 4 (audit): same pace times one national level factor from the fitted rows
        out["M0L same pace x level"] = new["units_3y"].values * lev
    return out


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
            preds = benchmarks(pool, te, level(F))
            for name, (m, g) in fitted.items():
                nb = []
                preds[name] = predict(m, te, med, nb, name)
                negs[name] = negs.get(name, 0) + sum(nb)
                if tname == "held-out places, later years":
                    on = predict(m, te.assign(fake_reform=1), med, [], name)
                    off = predict(m, te.assign(fake_reform=0), med, [], name)
                    rows.append(dict(seed=seed, test="fake on-off", model=name, mean_on_minus_off=float(np.mean(on - off))))
            for name, pr in preds.items():
                rows.append(dict(seed=seed, test=tname, model=name, **NR.score(pr, te["actual"].values)))
                if tname == "held-out places, later years":
                    k = te.assign(pred=pr, miss=pr - te["actual"].values)
                    w = k.loc[k["miss"].abs().idxmax()]
                    rows[-1].update(worst=f"{w['name']} {w['key']} origin {w['origin']}: predicted {w['pred']:.0f}, actual {w['actual']:.0f}")
        print("seed", seed, "done", flush=True)
    S = pd.DataFrame(rows)
    S.to_csv(REFERENCE / f"parking_baseline_models_scores{TAG}.csv", index=False)
    pd.DataFrame(choices).to_csv(REFERENCE / f"parking_baseline_models_choices{TAG}.csv", index=False)

    # round 3 (audit): state totals from whole held-out Census divisions. Each division is predicted from the others,
    # fitted on origins 2016-2017, scored on its states' totals at origins 2018-2019. Settings: each model's most common
    # cross-validated choice above. Calendar years still overlap: fitted outcomes run to 2023, test outcomes 2020-2025.
    C = pd.DataFrame(choices)
    pick = {n: MODELS[n][1][[str(x) for x in MODELS[n][1]].index(C.query("model == @n")["setting"].mode().iloc[0])] for n in MODELS}
    T0 = train[train["state_fips"] != NR.WI].assign(fake_reform=0)
    st_rows = []
    for dv in sorted(T0["division"].unique()):
        F = T0[(T0["division"] != dv) & T0["origin"].isin(NR.FIT_ORIGINS) & T0["actual"].notna()]
        te = T0[(T0["division"] == dv) & T0["origin"].isin(NR.TEST_ORIGINS) & T0["actual"].notna()]
        if te.empty:
            continue
        med = F[COLS].median()
        preds = benchmarks(T0[T0["division"] != dv], te, level(F))
        for name in MODELS:
            preds[name] = predict(fit(name, pick[name], NR.SEEDS[0], F, med), te, med, [], name)
        for name, pr in preds.items():
            st_rows.append(te.assign(pred=pr, model=name)[["model", "division", "state_fips", "origin", "pred", "actual"]])
        print("division", dv, "done", flush=True)
    ST = pd.concat(st_rows).groupby(["model", "division", "state_fips", "origin"], as_index=False)[["pred", "actual"]].sum()
    ST.to_csv(REFERENCE / f"parking_baseline_models_state_totals{TAG}.csv", index=False)
    ref = ST[ST["model"] == "M0L same pace x level"].set_index(["state_fips", "origin"])
    ref_lg = np.abs(np.log((ref["pred"] + 0.5) / (ref["actual"] + 0.5)))
    for name, g in ST.groupby("model"):
        sc = NR.score(g["pred"].values, g["actual"].values)
        lg = np.abs(np.log((g["pred"].values + 0.5) / (g["actual"].values + 0.5)))
        # round 4 (audit): share of state-origins where this model is closer than M0L
        sc["beats_M0L_share"] = float(np.mean(lg < ref_lg.reindex(pd.MultiIndex.from_frame(g[["state_fips", "origin"]])).values))
        brng = np.random.default_rng(20261031)
        bs = [np.median(lg[brng.integers(0, len(lg), len(lg))]) for _ in range(2000)]
        rows.append(dict(seed=0, test="state totals, held-out divisions", model=name, **sc,
                         p05=float(np.percentile(bs, 5)), p95=float(np.percentile(bs, 95))))
    S = pd.DataFrame(rows)
    S.to_csv(REFERENCE / f"parking_baseline_models_scores{TAG}.csv", index=False)

    # Wisconsin: fit on all non-Wisconsin rows (origins 2016-2019), back-test origin 2019, forecast origin 2025
    allfit = train[(train["state_fips"] != NR.WI) & train["actual"].notna()].assign(fake_reform=0)
    med = allfit[COLS].median()
    seed = NR.SEEDS[0]
    W = []
    allfit_all = allfit
    for o in (2019, 2025):
        # round 3 (audit): the 2019 back-test is fitted on origins 2016-2017 only (outcomes to 2023 still overlap 2021-2025)
        allfit = allfit_all[allfit_all["origin"].isin(NR.FIT_ORIGINS)] if o == 2019 else allfit_all
        med = allfit[COLS].median()
        te = R[(R["state_fips"] == NR.WI) & (R["origin"] == o)].assign(fake_reform=0)
        preds = benchmarks(train[train["state_fips"] != NR.WI], te, level(allfit))
        for name in MODELS:
            g = pick[name]
            preds[name] = predict(fit(name, g, seed, allfit, med), te, med, [], name)
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
