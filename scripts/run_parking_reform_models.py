"""Parking: full set of reform-prediction models (docs/parking/REFORM_MODELS_PLAN.md).

    uv run --all-extras python scripts/run_parking_reform_models.py --round N

Leave-one-reform-place-out over 28 repeal places, 12 models, Wisconsin net with a jackknife spread, fake-reform placebo.
Outputs: reference/parking_reform_models_{heldout,scores,wisconsin,fake,checks}_rN.csv
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from econml.dml import CausalForestDML
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
ROUND = int(sys.argv[sys.argv.index("--round") + 1]) if "--round" in sys.argv else 1
_argv = sys.argv
sys.argv = [sys.argv[0], "--round", "1"]
import run_parking_baseline_models as BM  # noqa: E402  (loads the no-reform model's round 6 data path)
sys.argv = _argv
NR = BM.NR
from missing_middleware.parking import checks  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

warnings.filterwarnings("ignore")
TAG = f"_r{ROUND}"
BM.COLS = NR.BASE + NR.ACS + ["reform"]
BM.ROUND = 4  # baseline round 4 behaviour (log target for lasso and elastic net)
HIGH_END = 1.49  # route A high end, permits per 1,000 existing homes per year
CENTRAL = 122_619
CHOICES = pd.read_csv(REFERENCE / "parking_baseline_models_choices_r4.csv")
PICK = {n: BM.MODELS[n][1][[str(x) for x in BM.MODELS[n][1]].index(CHOICES.query("model == @n")["setting"].mode().iloc[0])]
        for n in BM.MODELS}
SEED = NR.SEEDS[0]


def cf_fit(df):
    X = df[NR.BASE + NR.ACS].fillna(df[NR.BASE + NR.ACS].median())
    y = (df["actual"] / df["homes"] * 1000).clip(lower=0)
    m = CausalForestDML(model_y=HistGradientBoostingRegressor(max_leaf_nodes=31, learning_rate=0.05, random_state=SEED),
                        model_t=HistGradientBoostingClassifier(max_leaf_nodes=15, learning_rate=0.05, random_state=SEED),
                        discrete_treatment=True, n_estimators=400, min_samples_leaf=10, random_state=SEED, cv=3)
    m.fit(y.values, df["reform"].values, X=X.values, sample_weight=(df["homes"] / 1000).values)
    return m, X.median()


def cf_effect(mm, df):
    m, med = mm
    X = df[NR.BASE + NR.ACS].fillna(med)
    return np.asarray(m.effect(X.values)).ravel() * df["homes"].values / 1000  # homes per place per year


def all_models(fitdf, te, wi):
    """{model: (pred_on_test, pred_off_test, wi_on_minus_off)}; predictions in homes per place per year."""
    med = fitdf[BM.COLS].median()
    lev = BM.level(fitdf)
    out = {"M0 same pace": (te["units_3y"].values, te["units_3y"].values, np.zeros(len(wi))),
           "M0L same pace x level": (te["units_3y"].values * lev, te["units_3y"].values * lev, np.zeros(len(wi))),
           "M0 + route A high end": (te["units_3y"].values + HIGH_END * te["homes"].values / 1000, te["units_3y"].values,
                                     HIGH_END * wi["homes"].values / 1000)}
    for name in BM.MODELS:
        m = BM.fit(name, PICK[name], SEED, fitdf, med)
        on = BM.predict(m, te.assign(reform=1), med, [], name)
        off = BM.predict(m, te.assign(reform=0), med, [], name)
        w = BM.predict(m, wi.assign(reform=1), med, [], name) - BM.predict(m, wi.assign(reform=0), med, [], name)
        out[name] = (on, off, w)
    cf = cf_fit(fitdf)
    eff = cf_effect(cf, te)
    base = BM.predict(BM.fit("Boosted trees", PICK["Boosted trees"], SEED, fitdf.assign(reform=0), med), te.assign(reform=0), med, [], "Boosted trees")
    out["Causal forest (DML)"] = (base + eff, base, cf_effect(cf, wi))
    return out


def main() -> None:
    R, reform_year, *_ = NR.prepare()
    ry, o = R["reform_year"].values, R["origin"].values
    R["reform"] = ((ry >= o - 1) & (ry <= o + 2) & (ry != 9999) & (ry > 0)).astype(int)
    data = R[(R["no_reform"] | (R["reform"] == 1)) & R["actual"].notna() & (R["state_fips"] != NR.WI)].copy()
    reform_keys = sorted(data.loc[data["reform"] == 1, "key"].unique())
    wi_all = R[(R["state_fips"] == NR.WI) & (R["origin"] == 2025)]
    wi = wi_all[wi_all["key"].map(lambda k: reform_year.get(k, 9999) == 9999)].copy()
    scale = CENTRAL / (5 * float(wi_all["units_3y"].sum()))

    held, nets = [], []
    for i, k in enumerate(reform_keys):
        fitdf = data[data["key"] != k]
        te = data[(data["key"] == k) & (data["reform"] == 1)]
        res = all_models(fitdf, te, wi)
        for name, (on, off, w) in res.items():
            held.append(te[["key", "name", "origin", "reform_year", "homes", "units_3y", "actual"]].assign(model=name, pred_on=on, pred_off=off))
            nets.append(dict(left_out=k, model=name, wi_net_2027_2031=float(np.sum(w) * 5 * scale)))
        print(i + 1, "of", len(reform_keys), te["name"].iloc[0], flush=True)
    H = pd.concat(held, ignore_index=True)
    H.to_csv(REFERENCE / f"parking_reform_models_heldout{TAG}.csv", index=False)
    N = pd.DataFrame(nets)

    ref = H[H["model"] == "M0 same pace"].set_index(["key", "origin"])
    lg = lambda d: np.abs(np.log((d["pred_on"] + 0.5) / (d["actual"] + 0.5)))  # noqa: E731
    rows = []
    for name, g in H.groupby("model", sort=False):
        sc = NR.score(g["pred_on"].values, g["actual"].values)
        b = lg(g).values < lg(ref.reindex(pd.MultiIndex.from_frame(g[["key", "origin"]]))).values
        rows.append(dict(model=name, **sc, beats_M0_share=float(np.mean(b)), mean_on_minus_off=float((g["pred_on"] - g["pred_off"]).mean()),
                         wi_net_median=float(N.query("model == @name")["wi_net_2027_2031"].median()),
                         wi_net_p05=float(N.query("model == @name")["wi_net_2027_2031"].quantile(0.05)),
                         wi_net_p95=float(N.query("model == @name")["wi_net_2027_2031"].quantile(0.95))))
    S = pd.DataFrame(rows)

    # fake-reform placebo: 28 never-reformed places, real repeal years, 5 seeds
    fakes = []
    real_y = data.loc[data["reform"] == 1, "reform_year"].astype(int).values
    nr_keys = sorted(data.loc[data["reform"] == 0, "key"].unique())
    for seed in NR.SEEDS:
        rng = np.random.default_rng(seed)
        fk = sorted(rng.choice(nr_keys, size=len(reform_keys), replace=False))
        fy = {k: int(rng.choice(real_y)) for k in fk}
        fd = data[data["reform"] == 0].copy()
        fd["reform"] = [int(k in fy and oo - 1 <= fy[k] <= oo + 2) for k, oo in zip(fd["key"], fd["origin"])]
        res = all_models(fd, fd.head(1), wi)
        for name, (_, _, w) in res.items():
            fakes.append(dict(seed=seed, model=name, fake_rows=int(fd["reform"].sum()), wi_net_2027_2031=float(np.sum(w) * 5 * scale)))
        print("fake seed", seed, "done", flush=True)
    Fk = pd.DataFrame(fakes)
    Fk.to_csv(REFERENCE / f"parking_reform_models_fake{TAG}.csv", index=False)
    fr = Fk.groupby("model")["wi_net_2027_2031"].agg(fake_min="min", fake_max="max")
    S = S.merge(fr, left_on="model", right_index=True, how="left")
    S.to_csv(REFERENCE / f"parking_reform_models_scores{TAG}.csv", index=False)
    N.to_csv(REFERENCE / f"parking_reform_models_wisconsin{TAG}.csv", index=False)

    flags = []
    for name, g in H.groupby("model", sort=False):
        w = g.assign(miss=g["pred_on"] - g["actual"]).sort_values("miss", key=abs).iloc[-1]
        flags.append(dict(check="worst held-out miss", where=name, value=round(float(w["miss"])),
                          note=f"{w['name']} origin {w['origin']} repeal {int(w['reform_year'])}: on {w['pred_on']:.0f}, off {w['pred_off']:.0f}, actual {w['actual']:.0f}, same pace {w['units_3y']:.0f}"))
    big = S[S["wi_net_median"].abs() > 0.25 * CENTRAL]
    flags += [dict(check="Wisconsin net more than 25% of baseline", where=r.model, value=round(r.wi_net_median)) for r in big.itertuples()]
    checks.report(flags, REFERENCE / f"parking_reform_models_checks{TAG}.csv")
    pd.set_option("display.width", 250)
    print(S.round(3).to_string(index=False))
    print(f"reform places {len(reform_keys)}, reform rows {int(data['reform'].sum())}, Wisconsin places with minimums {len(wi)}, scale {scale:.3f}")


if __name__ == "__main__":
    main()
