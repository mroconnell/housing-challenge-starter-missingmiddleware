"""Parking method 3b (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Method 3b"; post hoc in origin).

    uv run --all-extras python scripts/run_parking_method3b.py --stage 1   # fit score on A, B check, fresh bake-off in B, pick
    git add reference/parking_method3b_pick.csv && git commit ...           # the pick must be committed first
    uv run --all-extras python scripts/run_parking_method3b.py --stage 2   # real 76 (cross-fitted), every weighting

One candidate: target = no-repeal change in rate (after mean minus D's 10-year before mean); score = average of boosting
(iteration count chosen on mean absolute error by 5-fold grouped CV by place, then refitted fixed) and lasso (grouped inner CV); match = method-2 ladder, then nearest 10 on
sqrt(z_score^2 + z_trend^2) (z over the chosen step's candidates; step 5 adds log population). Fresh fake repeals in B
(seed 20261105, real cases' event years). Pick: paired bootstrap of MAE(3b) - MAE(D) entirely below 0, gap >= 2% of D's
MAE (the learning thread's provisional call), coverage 85-95%.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import multiprocessing as mp
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import check_parking_method2_size_test as st  # noqa: E402
import run_parking_method2 as m  # noqa: E402
import run_parking_method3 as m3  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

SEED_SPLIT, SEED = 20261104, 20261105
PICK = REFERENCE / "parking_method3b_pick.csv"
G: dict = {}


# ---------------------------------------------------------------- score ---------------------------------------------
def rows(D, F, keys):
    Xs, ys, gs = [], [], []
    for ey in range(2016, 2025):
        pre, post = m.cmp.windows(ey)
        pl = m.long_pre(ey, pre, False)
        comp = D.complete(tuple(pl + post))
        ks = [k for k in keys if k in comp]
        if not ks:
            continue
        X = F.rows(ks, ey, pre)
        h = D.homes_pre(ey)
        r = m.rates(D, ks, pl + post, h)
        y = (r[post].mean(axis=1) - r[pl].mean(axis=1)).values
        ok = np.isfinite(y)
        Xs.append(X.values[ok])
        ys.append(y[ok])
        gs += [k for k, o in zip(ks, ok) if o]
    m3.DIV_IDX = list(X.columns).index("division")
    XX = np.vstack(Xs)
    for j in range(XX.shape[1]):
        if np.isnan(XX[:, j]).all():
            XX[:, j] = 0.0
    return XX, np.concatenate(ys), np.array(gs)


def fit_boost(X, y, groups, seed):
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.model_selection import GroupKFold
    err = np.zeros(300)
    for tr, te in GroupKFold(n_splits=5).split(X, y, groups):
        mdl = HistGradientBoostingRegressor(max_depth=2, learning_rate=0.05, max_iter=300, early_stopping=False,
                                            min_samples_leaf=5, random_state=seed).fit(X[tr], y[tr])
        for i, p in enumerate(mdl.staged_predict(X[te])):
            err[i] += np.mean(np.abs(p - y[te])) / 5
    best = int(np.argmin(err)) + 1
    mdl = HistGradientBoostingRegressor(max_depth=2, learning_rate=0.05, max_iter=best, early_stopping=False,
                                        min_samples_leaf=5, random_state=seed).fit(X, y)
    return mdl, best


class Score:
    def __init__(self, X, y, groups, seed):
        self.boost, self.iters = fit_boost(X, y, groups, seed)
        self.lasso = m3.fit("lasso", X, y, seed, groups)

    def predict(self, X):
        return (self.boost.predict(X) + m3.predict(self.lasso, X)) / 2


# ---------------------------------------------------------------- matching ------------------------------------------
def trend(D, keys, pre, h):
    r = m.rates(D, list(keys), pre, h)
    x = np.array(pre, float) - np.mean(pre)
    return pd.Series((r.values * x).sum(axis=1) / (x ** 2).sum(), index=list(keys))


def pool_3b(key, ey, pre5, pl, post, allowed):
    D = G["D"]
    h = D.homes_pre(ey)
    E = [k for k in m.eligible(D, key, list(pl) + list(post), "strict", True, h) if k in allowed]
    chosen, step, pop, tpop = m3.ladder(D, key, ey, pl, post, E, h)
    cands = E if chosen is None else chosen
    sc = pd.Series({k: G["scores"][(k, ey)] for k in cands + [key]})
    tr = trend(D, cands + [key], pre5, h)
    def z(s):
        sd = s[cands].std()
        return (s - s[cands].mean()) / (sd if sd > 0 else 1.0)
    zs, zt = z(sc), z(tr)
    d2 = (zs[cands] - zs[key]) ** 2 + (zt[cands] - zt[key]) ** 2
    if chosen is None:
        lp = np.log(pop.reindex(cands))
        lpt = np.log(tpop)
        sd = lp.std()
        d2 = d2 + ((lp - lpt) / (sd if sd > 0 else 1.0)) ** 2
    return m.nearest(np.sqrt(d2), pop, tpop, m.N_MATCH), step


def effect_3b(case, allowed):
    D = G["D"]
    key, ey = case["key"], case["event_year"]
    pre5 = list(m.cmp.windows(ey)[0])
    pl = m.long_pre(ey, list(case["pre"]), case.get("trimmed", False))
    post = list(case["post"])
    pool, _ = pool_3b(key, ey, pre5, pl, post, allowed)
    if len(pool) < m.MIN_POOL:
        return np.nan
    return m.did(D, key, pl, post, pool, D.homes_pre(ey), True, case.get("scale", 1.0))


def _fake(chunk):
    out = {}
    for (k, ey, pre, post) in chunk:
        case = dict(key=k, event_year=ey, pre=pre, post=post, pop=G["D"].popn.get(k, np.nan))
        out[(k, ey, pre, post, "3b")] = effect_3b(case, G["B"])
        out[(k, ey, pre, post, "D")] = m3._today_restricted(case, G["B"])
    return out


def _real(c):
    return effect_3b(c, G["all"])


# ---------------------------------------------------------------- stages --------------------------------------------
def draw_sets(D, cases, B, seed):
    rng = np.random.default_rng(seed)
    strata, sets = {}, []
    for _ in range(m.SETS):
        row = []
        for c in cases:
            pre, post = m.cmp.windows(c["event_year"])
            post = post[: c["n_post"]]
            band = int(m.band_of([c["pop"] if np.isfinite(c["pop"]) else D.popn.get(c["key"], 0)])[0])
            sk = (c["event_year"], band, c["n_post"])
            if sk not in strata:
                comp = D.complete(tuple(pre + post))
                strata[sk] = sorted(k for k in B if k in comp and int(m.band_of([D.popn.get(k, 0)])[0]) == band)
            s = strata[sk]
            row.append((s[rng.integers(0, len(s))], c["event_year"], tuple(pre), tuple(post), c["i"]))
        sets.append(row)
    return sets


def setup():
    D, F, today, A, B, ok = m3.setup()
    return D, F, today, A, B


def stage1():
    D, F, today, A, B = setup()
    XA, yA, gA = rows(D, F, A)
    XB, yB, gB = rows(D, F, B)
    sA = Score(XA, yA, gA, SEED_SPLIT)
    pB = sA.predict(XB)
    check = dict(boost_iterations=sA.iters, rows_A=len(yA), rows_B=len(yB), mae_score_on_B=float(np.mean(np.abs(pB - yB))),
                 mae_mean_on_B=float(np.mean(np.abs(yA.mean() - yB))))
    check["gain"] = 1 - check["mae_score_on_B"] / check["mae_mean_on_B"]
    pd.DataFrame([check]).to_csv(REFERENCE / "parking_method3b_score_check.csv", index=False)
    print(check, flush=True)
    if check["gain"] < 0.05:
        pd.DataFrame([dict(candidate="D", rule="3b score failed the B check (<5% better than a plain average); stopped")]).to_csv(PICK, index=False)
        print("STOP: score failed the B check")
        return
    scores = {}
    for ey in range(2016, 2025):
        pre, _ = m.cmp.windows(ey)
        ks = sorted(B)
        for k, s in zip(ks, sA.predict(F.rows(ks, ey, pre).values)):
            scores[(k, ey)] = float(s)
    G.update(D=D, B=B, scores=scores)
    corr = []
    for ey in range(2016, 2025):
        pre, _ = m.cmp.windows(ey)
        ks = [k for k in sorted(B) if k in D.complete(tuple(pre))]
        tr = trend(D, ks, pre, D.homes_pre(ey))
        sc = pd.Series({k: scores[(k, ey)] for k in ks})
        corr.append(float(sc.corr(tr)))
    check["corr_score_trend_by_year"] = ";".join(f"{c:.3f}" for c in corr)
    pd.DataFrame([check]).to_csv(REFERENCE / "parking_method3b_score_check.csv", index=False)
    print("score-trend correlation by event year 2016-2024:", check["corr_score_trend_by_year"], flush=True)
    m3.G.update(D=D, today=today, B=B)
    real, cases = m.real_cases()
    v = m.placebo_v(len(real))
    sets = draw_sets(D, cases, B, SEED)
    old = {(k, ey, pre, post) for row in draw_sets(D, cases, B, SEED_SPLIT) for (k, ey, pre, post, _) in row}  # method 3's draw
    uniq = sorted({(k, ey, pre, post) for row in sets for (k, ey, pre, post, _) in row})
    overlap = len(set(uniq) & old)
    print(len(uniq), "fresh fake cases;", overlap, "also in method 3's draw", flush=True)
    ctx = mp.get_context("fork")
    eff = {}
    with cf.ProcessPoolExecutor(m.WORKERS, mp_context=ctx) as ex:
        for part in ex.map(_fake, [uniq[i::m.WORKERS] for i in range(m.WORKERS)]):
            eff.update(part)
    # correlation of score and trend across the fake cases (reported)
    m._G = dict(D=D, eff=eff, sets=sets, v=v, cells=m.target_cells(D, "55"))
    with cf.ProcessPoolExecutor(m.WORKERS, mp_context=ctx) as ex:
        res = list(ex.map(m._score, [(c, w) for c in ("3b", "D") for w in m.WEIGHTS]))
    R = pd.DataFrame(res)
    # per-set random-effects averages for the paired bootstrap
    per = {}
    for cand in ("3b", "D"):
        a = []
        for row in sets:
            y = np.array([eff[(k, ey, pre, post, cand)] for (k, ey, pre, post, _) in row])
            ev = pd.DataFrame({"v": [v[i] for *_, i in row], "homes": [D.homes_pre(ey)[k] for (k, ey, *_r) in row],
                               "n_post": [len(post) for (_, _, _, post, _) in row]})
            okr = np.isfinite(y)
            a.append(abs(m.weighted_avg("random effects", y[okr], ev[okr].reset_index(drop=True), None)))
        per[cand] = np.array(a)
    rng = np.random.default_rng(SEED)
    diffs = []
    for _ in range(m.BOOT):
        i = rng.integers(0, m.SETS, m.SETS)
        diffs.append(per["3b"][i].mean() - per["D"][i].mean())
    lo, hi = np.percentile(diffs, 5), np.percentile(diffs, 95)
    p = R[(R.candidate == "3b") & (R.weights == "random effects")].iloc[0]
    d = R[(R.candidate == "D") & (R.weights == "random effects")].iloc[0]
    a_ok, b_ok, c_ok = hi < 0, (d["mae"] - p["mae"]) >= 0.02 * d["mae"], 0.85 <= p["coverage"] <= 0.95
    pick = "3b" if (a_ok and b_ok and c_ok) else "D"
    R = R.assign(fresh_cases=len(uniq), overlap_with_method3=overlap)
    R.round(4).to_csv(REFERENCE / "parking_method3b_bakeoff.csv", index=False)
    pd.DataFrame([dict(candidate=pick, mae_3b=p["mae"], cov_3b=p["coverage"], mae_D=d["mae"], cov_D=d["coverage"],
                       paired_diff_p05=lo, paired_diff_p95=hi, rule_a=bool(a_ok), rule_b=bool(b_ok), rule_c=bool(c_ok))]).to_csv(PICK, index=False)
    print(R.round(4).to_string(index=False))
    print("paired", lo, hi, "PICK", pick)


def stage2():
    r = subprocess.run(["git", "ls-files", "--error-unmatch", str(PICK)], cwd=ROOT, capture_output=True)
    dq = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", str(PICK)], cwd=ROOT)
    if r.returncode or dq.returncode:
        raise SystemExit("commit reference/parking_method3b_pick.csv first")
    pick = str(pd.read_csv(PICK)["candidate"].iloc[0])
    D, F, today, A, B = setup()
    real, cases = m.real_cases()
    XA, yA, gA = rows(D, F, A)
    XB, yB, gB = rows(D, F, B)
    sA, sB = Score(XA, yA, gA, SEED_SPLIT), Score(XB, yB, gB, SEED_SPLIT)
    scores = {}
    for ey in sorted({c["event_year"] for c in cases}):
        pre, _ = m.cmp.windows(ey)
        for half, s in ((sorted(A), sB), (sorted(B), sA)):
            for k, v in zip(half, s.predict(F.rows(half, ey, pre).values)):
                scores[(k, ey)] = float(v)
        rk = [c["key"] for c in cases if c["event_year"] == ey]
        Xr = F.rows(rk, ey, pre).values
        for k, v in zip(rk, (sA.predict(Xr) + sB.predict(Xr)) / 2):
            scores[(k, ey)] = float(v)
    G.update(D=D, scores=scores, all=A | B)
    with cf.ProcessPoolExecutor(m.WORKERS, mp_context=mp.get_context("fork")) as ex:
        y3 = np.array(list(ex.map(_real, cases)))
    yD = pd.read_csv(REFERENCE / "parking_method3_places.csv")["today"].values
    ev = pd.DataFrame({"v": m.placebo_v(len(real)), "homes": real["homes"].values, "n_post": real["n_post"].values,
                       "band": m.band_of(real["population"].fillna(0)), "metro": [D.metro.get(c["key"], 0.0) for c in cases]})
    ev["base"] = ev["homes"] * ev["n_post"]
    wi = m.target_cells(D, "55")
    out = []
    for lab, yy in ((f"method 3b picked ({pick})", y3 if pick == "3b" else yD), ("3b matching", y3), ("D (corrected method 2)", yD)):
        okr = np.isfinite(yy)
        for kind in m.WEIGHTS:
            a = m.weighted_avg(kind, yy[okr], ev[okr].reset_index(drop=True), wi)
            lo, hi = m.boot_range(kind, yy[okr], ev[okr].reset_index(drop=True), wi, m.BOOT, SEED)
            out.append(dict(variant=lab, weights=kind, places=int(okr.sum()), average=a, p05=lo, p95=hi,
                            wi_homes=a * m.WI_K, wi_p05=lo * m.WI_K, wi_p95=hi * m.WI_K))
    pd.DataFrame(out).round(4).to_csv(REFERENCE / "parking_method3b_results.csv", index=False)
    pd.DataFrame({"place": real["place"], "state": real["state"], "3b": y3, "D": yD}).round(4).to_csv(REFERENCE / "parking_method3b_places.csv", index=False)
    if pick == "3b":
        st.run(y3, "parking_method3b_size_test")
    print(pd.DataFrame(out).round(2).to_string(index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, required=True, choices=(1, 2))
    stage1() if ap.parse_args().stage == 1 else stage2()


if __name__ == "__main__":
    main()
