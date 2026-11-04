"""Parking method 3: prognostic-score matching (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Method 3", cleared by the audit
21:10 UTC; provisional go by the learning thread under Ryan's 21:01 UTC delegation). Post hoc in origin.

    uv run --all-extras python scripts/run_parking_method3.py --stage 1   # split, fit A and B, check, bake-off in B, pick
    git add reference/parking_method3_pick.csv && git commit ...           # the pick must be committed first
    uv run --all-extras python scripts/run_parking_method3.py --stage 2   # real 76, weightings, weight test, size check

Corrected method-2 data (Connecticut join, Wisconsin tool cells). All places included (no with/without-SF runs).
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
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

SEED = 20261104
PICK = REFERENCE / "parking_method3_pick.csv"
TRAITS = RAW / "parking_acs_tod_traits" / "traits_by_release.csv.gz"
EXCLUDE_ALLVARS = ("V1_", "V2_", "V11_", "V12_", "V13_", "V14_")  # repeal-specific (never-repealed places lack them)
G: dict = {}


# ---------------------------------------------------------------- features ------------------------------------------
class Feat:
    def __init__(self, D: m.Data):
        T = pd.read_csv(TRAITS, dtype={"acs_geoid": str})
        T["acs_geoid"] = T["acs_geoid"].map(m.ct_norm)
        T = T.drop_duplicates(["acs_geoid", "release_end"])
        self.cols = [c for c in T.columns if c not in ("acs_geoid", "release_end")]
        ag = D.geo["acs_geoid"].map(m.ct_norm)
        self.by_year = {y: g.set_index("acs_geoid")[self.cols] for y, g in T.groupby("release_end")}
        self.ag = ag
        self.D = D
        self.div_code = {d: i for i, d in enumerate(sorted(D.division.dropna().unique()))}

    def rows(self, keys, ey, pre):
        """Feature matrix for keys at event year ey: ACS traits from the release ending ey-1, permit history in pre."""
        D = self.D
        keys = list(keys)
        acs = self.by_year.get(ey - 1)
        X = acs.reindex(self.ag.reindex(keys).values).set_axis(keys) if acs is not None else pd.DataFrame(index=keys, columns=self.cols)
        h = D.homes_pre(ey)
        r = m.rates(D, keys, pre, h)
        x = np.array(pre, float) - np.mean(pre)
        X = X.copy()
        X["rate_before"] = r.mean(axis=1).values
        X["trend_before"] = (r.values * x).sum(axis=1) / (x ** 2).sum()
        X["volatility_before"] = r.std(axis=1).values
        X["log_pop"] = np.log((D.popn.reindex(keys) * h.reindex(keys) / D.homes.reindex(keys)).values)
        X["log_density_2010"] = D.density.reindex(keys).values
        X["town_age_1990_2009"] = D.age.reindex(keys).values
        X["metro"] = D.metro.reindex(keys).values
        X["division"] = D.division.reindex(keys).map(self.div_code).values
        X["event_year"] = ey
        return X.astype(float).replace([np.inf, -np.inf], np.nan)  # e.g. log of 0 population or density


def target(D, keys, ey, post) -> np.ndarray:
    h = D.homes_pre(ey)
    return m.rates(D, keys, post, h).mean(axis=1).values


# ---------------------------------------------------------------- models --------------------------------------------
DIV_IDX: int | None = None  # column index of "division" (set from the feature columns)


def _lasso_X(X, med):
    """Missing indicator + training median; division one-hot (it is a category, not a line)."""
    Z = np.where(np.isnan(X), med, X)
    parts = [Z, np.isnan(X).astype(float)]
    if DIV_IDX is not None:
        d = X[:, DIV_IDX]
        parts[0] = np.delete(Z, DIV_IDX, axis=1)
        parts[1] = np.delete(parts[1], DIV_IDX, axis=1)
        parts.append(np.column_stack([(d == c).astype(float) for c in range(9)]))
    return np.column_stack(parts)


def fit(kind, X, y, seed, groups=None):
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.linear_model import LassoCV
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    if kind == "gradient boosting":
        mdl = HistGradientBoostingRegressor(max_depth=2, learning_rate=0.05, max_iter=300, early_stopping=True,
                                            validation_fraction=0.2, n_iter_no_change=20, min_samples_leaf=5, random_state=seed)
        return mdl.fit(X, y)
    from sklearn.model_selection import GroupKFold
    med = np.nanmedian(X, axis=0)
    Xi = _lasso_X(X, med)
    cv = list(GroupKFold(n_splits=5).split(Xi, y, groups)) if groups is not None else 5
    mdl = make_pipeline(StandardScaler(), LassoCV(cv=cv, random_state=seed, max_iter=20000)).fit(Xi, y)
    return ("lasso", mdl, med)


def predict(model, X):
    if isinstance(model, tuple):
        _, mdl, med = model
        return mdl.predict(_lasso_X(X, med))
    return model.predict(X)


def choose(X, y, groups, seed) -> tuple[str, dict]:
    from sklearn.model_selection import GroupKFold
    err = {}
    for kind in ("gradient boosting", "lasso"):
        e = []
        for tr, te in GroupKFold(n_splits=5).split(X, y, groups):
            mdl = fit(kind, X[tr], y[tr], seed, groups[tr])
            e.append(np.mean(np.abs(predict(mdl, X[te]) - y[te])))
        err[kind] = float(np.mean(e))
    return min(err, key=err.get), err


# ---------------------------------------------------------------- matching ------------------------------------------
def ladder(D, target_key, ey, pre, post, E, h):
    pop = D.popn.reindex(E) * (h.reindex(E) / D.homes.reindex(E))
    tpop = D.popn.get(target_key, np.nan) * h.get(target_key, np.nan) / D.homes.get(target_key, np.nan)
    st_, dv = D.state.get(target_key), D.division.get(target_key, "")
    for i, (scope, lo, hi) in enumerate([("state", 0.5, 2.0), ("division", 0.5, 2.0), ("nation", 0.5, 2.0), ("nation", 1 / 3, 3.0)], 1):
        w = pop[(pop >= lo * tpop) & (pop <= hi * tpop)].index
        if scope == "state":
            w = [k for k in w if D.state.get(k) == st_]
        elif scope == "division":
            w = [k for k in w if dv not in ("", None) and D.division.get(k) == dv]
        if len(w) >= m.N_MATCH:
            return list(w), i, pop, tpop
    return None, 5, pop, tpop


def prog_pool(D, key, ey, pre, post, score_of, allowed) -> tuple[list, int]:
    h = D.homes_pre(ey)
    E = [k for k in m.eligible(D, key, list(pre) + list(post), "strict", True, h) if k in allowed]
    chosen, step, pop, tpop = ladder(D, key, ey, pre, post, E, h)
    s_t = score_of(key, ey, pre)
    if chosen is None:  # step 5: nationwide, nearest 10 on score and log population (z-scored over E)
        sc = pd.Series({k: score_of(k, ey, pre) for k in E})
        lp = np.log(pop.reindex(E))
        z1 = (sc - sc.mean()) / sc.std()
        z2 = (lp - lp.mean()) / lp.std()
        t1 = (s_t - sc.mean()) / sc.std()
        t2 = (np.log(tpop) - lp.mean()) / lp.std()
        dist = np.sqrt((z1 - t1) ** 2 + (z2 - t2) ** 2)
    else:
        sc = pd.Series({k: score_of(k, ey, pre) for k in chosen})
        dist = (sc - s_t).abs()
    return m.nearest(dist, pop, tpop, m.N_MATCH), step


# score cache: (key, ey, pre) -> score, filled before matching
def score_of(key, ey, pre):
    """Prognostic score for key at event year ey; features always use the standard 5-year before window."""
    return G["scores"][(key, ey)]


def case_effect(case, cand, allowed):
    D = G["D"]
    key, ey, pre, post, scale = case["key"], case["event_year"], list(case["pre"]), list(case["post"]), case.get("scale", 1.0)
    pl = m.long_pre(ey, pre, case.get("trimmed", False))
    if cand == "today":
        return _today_restricted(case, allowed)
    pool, _ = prog_pool(D, key, ey, pl, post, score_of, allowed if allowed is not None else G["all_allowed"])
    if len(pool) < m.MIN_POOL:
        return np.nan
    h = D.homes_pre(ey)
    return m.did(D, key, pl, post, pool, h, True, scale)


def _today_restricted(case, allowed):
    """Today's corrected pick (D) with pools restricted to the allowed half."""
    D = G["D"]
    orig = m.eligible

    def elig(D_, target, years, mode_exc, shock_on, h):
        return [k for k in orig(D_, target, years, mode_exc, shock_on, h) if k in allowed]
    m.eligible = elig
    try:
        return m.case_effect(D, case, G["today"], m.OPT_MAIN)["effect"]
    finally:
        m.eligible = orig


def _fake(chunk):
    out = {}
    for (k, ey, pre, post) in chunk:
        case = dict(key=k, event_year=ey, pre=pre, post=post, pop=G["D"].popn.get(k, np.nan))
        out[(k, ey, pre, post, "P")] = case_effect(case, "P", G["B"])
        out[(k, ey, pre, post, "today")] = case_effect(case, "today", G["B"])
    return out


def _real(c):
    return dict(P=case_effect(c, "P", None), today=m.case_effect(G["D"], c, G["today"], m.OPT_MAIN)["effect"])


# ---------------------------------------------------------------- stages --------------------------------------------
def setup():
    m.SUF, m.CORRECTED = "_corrected", True
    D = m.Data()
    F = Feat(D)
    today = str(pd.read_csv(REFERENCE / "parking_method2_corrected_pick.csv")["candidate"].iloc[0])
    ok = D.complete(tuple(range(m.FIRST, m.LAST + 1)))
    never = sorted(k for k in D.homes.index if k not in D.strict_exc and k not in D.shock and np.isfinite(D.popn.get(k, np.nan)))
    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(never))
    A = set(never[i] for i in perm[: len(never) // 2])
    B = set(never) - A
    return D, F, today, A, B, ok


def training_rows(D, F, keys):
    rows_X, rows_y, groups, idx = [], [], [], []
    for ey in range(2016, 2025):
        pre, post = m.cmp.windows(ey)
        comp = D.complete(tuple(pre + post))
        ks = [k for k in keys if k in comp]
        if not ks:
            continue
        X = F.rows(ks, ey, pre)
        y = target(D, ks, ey, post)
        okr = np.isfinite(y)
        rows_X.append(X.values[okr])
        rows_y.append(y[okr])
        groups += [k for k, o in zip(ks, okr) if o]
        idx += [(k, ey, tuple(pre)) for k, o in zip(ks, okr) if o]
    global DIV_IDX
    XX = np.vstack(rows_X)
    cols = list(X.columns)
    empty = [c for j, c in enumerate(cols) if np.isnan(XX[:, j]).all()]
    if empty:  # entirely empty in this half: the median is undefined; replace with 0 and report (audit, 21:50 UTC)
        print("empty trait columns in this half (set to 0, listed in the report):", empty, flush=True)
        for c in empty:
            XX[:, cols.index(c)] = 0.0
    DIV_IDX = cols.index("division")
    return XX, np.concatenate(rows_y), np.array(groups), idx, cols


def stage1():
    D, F, today, A, B, ok = setup()
    XA, yA, gA, iA, cols = training_rows(D, F, A)
    XB, yB, gB, iB, _ = training_rows(D, F, B)
    kindA, errA = choose(XA, yA, gA, SEED)
    kindB, errB = choose(XB, yB, gB, SEED)
    mA, mB = fit(kindA, XA, yA, SEED, gA), fit(kindB, XB, yB, SEED, gB)
    check = dict(model_A=kindA, model_B=kindB, cv_A=errA, cv_B=errB,
                 mae_A_on_B=float(np.mean(np.abs(predict(mA, XB) - yB))), mae_mean_A_on_B=float(np.mean(np.abs(yA.mean() - yB))),
                 mae_B_on_A=float(np.mean(np.abs(predict(mB, XA) - yA))), mae_mean_B_on_A=float(np.mean(np.abs(yB.mean() - yA))),
                 rows_A=len(yA), rows_B=len(yB), places_A=len(set(gA)), places_B=len(set(gB)), traits=";".join(cols))
    check["gain_A_on_B"] = 1 - check["mae_A_on_B"] / check["mae_mean_A_on_B"]
    check["gain_B_on_A_mirror"] = 1 - check["mae_B_on_A"] / check["mae_mean_B_on_A"]
    pd.DataFrame([check]).to_csv(REFERENCE / "parking_method3_score_check.csv", index=False)
    print({k: v for k, v in check.items() if k != "traits"}, flush=True)
    if check["gain_A_on_B"] < 0.05:
        pd.DataFrame([dict(candidate="today", rule="score failed the B check (<5% better than a plain average); method 3 dropped")]).to_csv(PICK, index=False)
        print("score failed the B check; method 3 dropped")
        return
    # scores for B places at every fake window: A model (B places never seen by it)
    G.update(D=D, today=today, B=B, all_allowed=A | B)
    scores = {}
    for ey in range(2016, 2025):
        pre, _ = m.cmp.windows(ey)
        ks = sorted(B)
        X = F.rows(ks, ey, list(pre))
        for k, s in zip(ks, predict(mA, X.values)):
            scores[(k, ey)] = float(s)
    G["scores"] = scores
    # fake sets: the bake-off's strata, targets drawn from B only
    real, cases = m.real_cases()
    v = m.placebo_v(len(real))
    rng = np.random.default_rng(SEED)
    strata = {}
    sets = []
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
    uniq = sorted({(k, ey, pre, post) for row in sets for (k, ey, pre, post, _) in row})
    print(len(uniq), "fake cases in B", flush=True)
    ctx = mp.get_context("fork")
    eff = {}
    with cf.ProcessPoolExecutor(m.WORKERS, mp_context=ctx) as ex:
        for part in ex.map(_fake, [uniq[i::m.WORKERS] for i in range(m.WORKERS)]):
            eff.update(part)
    m._G = dict(D=D, eff=eff, sets=sets, v=v, cells=m.target_cells(D, "55"))
    with cf.ProcessPoolExecutor(m.WORKERS, mp_context=ctx) as ex:
        res = list(ex.map(m._score, [(c, w) for c in ("P", "today") for w in m.WEIGHTS]))
    R = pd.DataFrame(res)
    R.round(4).to_csv(REFERENCE / "parking_method3_bakeoff.csv", index=False)
    print(R.round(4).to_string(index=False))
    p = R[(R.candidate == "P") & (R.weights == "random effects")].iloc[0]
    t = R[(R.candidate == "today") & (R.weights == "random effects")].iloc[0]
    use_p = p["mae"] < 0.95 * t["mae"] and 0.85 <= p["coverage"] <= 0.95
    pd.DataFrame([dict(candidate="P" if use_p else "today", p_mae=p["mae"], p_coverage=p["coverage"], today_mae=t["mae"],
                       today_coverage=t["coverage"], today_method=today,
                       rule="P: MAE >5% below today's with coverage 85-95%" if use_p else "today's matching (tie or P not better)")]).to_csv(PICK, index=False)
    print("PICK", "P" if use_p else "today")


def require_pick() -> str:
    r = subprocess.run(["git", "ls-files", "--error-unmatch", str(PICK)], cwd=ROOT, capture_output=True)
    d = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", str(PICK)], cwd=ROOT)
    if r.returncode or d.returncode:
        raise SystemExit("commit reference/parking_method3_pick.csv first")
    return str(pd.read_csv(PICK)["candidate"].iloc[0])


def stage2():
    pick = require_pick()
    D, F, today, A, B, ok = setup()
    real, cases = m.real_cases()
    XA, yA, gA, _, _ = training_rows(D, F, A)
    XB, yB, gB, _, _ = training_rows(D, F, B)
    ck = pd.read_csv(REFERENCE / "parking_method3_score_check.csv").iloc[0]
    mA, mB = fit(ck["model_A"], XA, yA, SEED, gA), fit(ck["model_B"], XB, yB, SEED, gB)
    G.update(D=D, today=today, B=B, all_allowed=A | B)
    # cross-fitted scores: A places by the B model, B places by the A model, real places by the average
    scores = {}
    for ey in sorted({c["event_year"] for c in cases}):
        pre, _ = m.cmp.windows(ey)
        for half, mdl in ((sorted(A), mB), (sorted(B), mA)):
            X = F.rows(half, ey, list(pre))
            for k, s in zip(half, predict(mdl, X.values)):
                scores[(k, ey)] = float(s)
        rk = [c["key"] for c in cases if c["event_year"] == ey]
        Xr = F.rows(rk, ey, list(pre))
        for k, s in zip(rk, (predict(mA, Xr.values) + predict(mB, Xr.values)) / 2):
            scores[(k, ey)] = float(s)
    G["scores"] = scores
    with cf.ProcessPoolExecutor(m.WORKERS, mp_context=mp.get_context("fork")) as ex:
        res = list(ex.map(_real, cases))
    yP = np.array([r["P"] for r in res])
    yT = np.array([r["today"] for r in res])
    y = yP if pick == "P" else yT
    ev = pd.DataFrame({"v": m.placebo_v(len(real)), "homes": real["homes"].values, "n_post": real["n_post"].values,
                       "band": m.band_of(real["population"].fillna(0)), "metro": [D.metro.get(c["key"], 0.0) for c in cases]})
    ev["base"] = ev["homes"] * ev["n_post"]
    wi = m.target_cells(D, "55")
    out = []
    for lab, yy in ((f"method 3 picked ({pick})", y), ("prognostic matching (P)", yP), (f"today's matching ({today})", yT)):
        okr = np.isfinite(yy)
        for kind in m.WEIGHTS:
            a = m.weighted_avg(kind, yy[okr], ev[okr].reset_index(drop=True), wi)
            lo, hi = m.boot_range(kind, yy[okr], ev[okr].reset_index(drop=True), wi, m.BOOT, SEED)
            out.append(dict(variant=lab, weights=kind, places=int(okr.sum()), average=a, p05=lo, p95=hi,
                            wi_homes=a * m.WI_K, wi_p05=lo * m.WI_K, wi_p95=hi * m.WI_K))
    pd.DataFrame(out).round(4).to_csv(REFERENCE / "parking_method3_results.csv", index=False)
    pd.DataFrame({"place": real["place"], "state": real["state"], "P": yP, "today": yT}).round(4).to_csv(REFERENCE / "parking_method3_places.csv", index=False)
    # weight test (same candidates and tie rule)
    states = real["state"].value_counts()
    states = list(states[states >= 3].index)
    okr = np.isfinite(y)
    errs = {k: [] for k in m.WEIGHTS}
    errs_eq = {k: [] for k in m.WEIGHTS}
    for s in states:
        hold = (real["state"] == s).values & okr
        tr = (~(real["state"] == s).values) & okr
        truth = float(np.average(y[hold], weights=ev["base"].values[hold]))
        truth_eq = float(np.mean(y[hold]))
        hc = ev[hold].groupby(["metro", "band"])["base"].sum()
        for kind in m.WEIGHTS:
            pred = m.weighted_avg(kind, y[tr], ev[tr].reset_index(drop=True), hc)
            errs[kind].append(abs(pred - truth))
            errs_eq[kind].append(abs(pred - truth_eq))
    E = pd.DataFrame(errs, index=states)
    mae = E.mean()
    best = mae.idxmin()
    r2 = np.random.default_rng(SEED)
    diffs = [E["target-state mix"].values[i].mean() - E[best].values[i].mean() for i in (r2.integers(0, len(E), len(E)) for _ in range(m.BOOT))]
    lo, hi = np.percentile(diffs, 5), np.percentile(diffs, 95)
    winner = "target-state mix" if (mae["target-state mix"] <= 1.10 * mae[best] or lo <= 0 <= hi) else best
    E.loc["mean absolute error"] = mae
    E.round(4).to_csv(REFERENCE / "parking_method3_weight_test.csv")
    Eq = pd.DataFrame(errs_eq, index=states)
    Eq.loc["mean absolute error"] = Eq.mean()
    Eq.round(4).to_csv(REFERENCE / "parking_method3_weight_test_equal_truth.csv")
    pd.DataFrame([dict(winner=winner, lowest=best, p05=lo, p95=hi)]).to_csv(REFERENCE / "parking_method3_weight_pick.csv", index=False)
    # size-band check on the picked effects (reuses the correction lock's size test)
    st.run(y, "parking_method3_size_test")
    print(pd.DataFrame(out).round(2).to_string(index=False))
    print(E.round(3).to_string(), "\nWEIGHT WINNER", winner, best)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, required=True, choices=(1, 2))
    stage1() if ap.parse_args().stage == 1 else stage2()


if __name__ == "__main__":
    main()
