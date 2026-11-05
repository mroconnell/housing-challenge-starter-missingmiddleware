"""Test 52f: synthetic difference-in-differences (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Test 52", 52f and audit fix 12).

Run on the fixed 74-place sample through a working copy of reference/ (as scripts/run_parking_t51_lihtc.sh):
    rsync -a --exclude batch_2026-11-05/ reference/ data/processed/t52/f_ref/
    rsync -a reference/batch_2026-11-05/ data/processed/t52/f_ref/
    MM_REFERENCE_DIR=$PWD/data/processed/t52/f_ref MM_GATE_TIME=15:50 MM_BATCH_COMMITTED_DIR=reference/batch_2026-11-05 \
      uv run --all-extras python scripts/run_parking_t52_sdid.py --stage 1   # fake repeals scored against D, pick
    git add reference/parking_t52_f_pick.csv reference/parking_t52_f_fake_scoring.csv && git commit ...
    (same env) uv run --all-extras python scripts/run_parking_t52_sdid.py --stage 2   # real 74 (refuses unless pick committed)

SDID per Arkhangelsky et al. (2021), one fit per repeal place, written in numpy:
- Donors: the same matched pool method D uses for that case (corrected method-2 ladder + Mahalanobis nearest 10,
  D's before window back to 2012), with D's per-year 5/95 winsorising of pool rates. Only the weighting differs.
- Unit weights (with intercept): min_{w0, w in simplex} sum_{t pre} (w0 + w'Y_co,t - y_t)^2 + zeta^2 * T_pre * |w|^2.
- Time weights (with intercept): min_{l0, l in simplex} sum_{i co} (l0 + l'Y_i,pre - mean_post Y_i)^2 + (1e-6 sigma)^2 N_co |l|^2.
- Both on before-years only. zeta = (N_tr * T_post)^(1/4) * sigma; sigma = SD (ddof 1) of the pool places' year-to-year
  changes over the before-years (on the same winsorised donor rates that are weighted).
- Effect: (mean_post y - l'y_pre) - (w' mean_post Y_co - w' Y_co,pre l), divided by the case's scale as in D.
- N_tr: each fit has one repeal place, so the main uses N_tr = 1 (the paper's treated count within a fit). The literal
  reading "number of repeal places" = 74 is run beside as a labelled sensitivity ("SDID, N_tr = 74"), declared here
  before any run. The verdict is read on the main.
- Exact minimiser (accelerated projected gradient on the simplex), no "sparsify" step of the R package.

Fake repeals: method 3b's fresh draw (A/B split seed 20261104, draw seed 20261105, real cases' event years, size bands
and after-year counts; pools from B only), 200 sets of the 74. Scoring with method 2's _score (every weighting).
Pick rule (3b's, on random-effects scoring): paired bootstrap (2,000 resamples of the 200 sets, seed 20261105) of
MAE(SDID) - MAE(D) entirely below 0; gap >= 2% of D's MAE; SDID coverage 85-95%.
Outputs (new files only): reference/parking_t52_f_*.csv in the repo; the working copy's reference files are only read.
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
import run_parking_method2 as m  # noqa: E402
import run_parking_method3 as m3  # noqa: E402
import run_parking_method3b as m3b  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

SEED = 20261105
WORKERS = 3
OUT = ROOT / "reference"
PICK = OUT / "parking_t52_f_pick.csv"
SCORING = OUT / "parking_t52_f_fake_scoring.csv"
CANDS = ("SDID", "SDID, N_tr = 74", "D")
G: dict = {}


# ---------------------------------------------------------------- SDID ----------------------------------------------
def proj_simplex(v: np.ndarray) -> np.ndarray:
    u = np.sort(v)[::-1]
    css = np.cumsum(u) - 1.0
    k = np.arange(1, len(v) + 1)
    r = np.nonzero(u - css / k > 0)[0][-1]
    return np.maximum(v - css[r] / (r + 1), 0.0)


def simplex_ridge(A: np.ndarray, b: np.ndarray, eta: float, iters: int = 200_000, tol: float = 1e-13) -> np.ndarray:
    """argmin_{x in simplex} |A x - b|^2 + eta |x|^2 (A already centred for the intercept). FISTA with projection."""
    n = A.shape[1]
    Q = A.T @ A + eta * np.eye(n)
    c = A.T @ b
    L = 2 * np.linalg.eigvalsh(Q).max()
    if not np.isfinite(L) or L <= 0:
        return np.full(n, 1 / n)
    x = np.full(n, 1 / n)
    yv, tk = x.copy(), 1.0
    for _ in range(iters):
        xn = proj_simplex(yv - (2 * (Q @ yv - c)) / L)
        tn = (1 + np.sqrt(1 + 4 * tk * tk)) / 2
        yv = xn + ((tk - 1) / tn) * (xn - x)
        if np.abs(xn - x).max() < tol:
            x = xn
            break
        x, tk = xn, tn
    return x


def sdid(D, key, pre, post, pool, h, wins, scale, n_tr) -> dict:
    yrs = list(pre) + list(post)
    y = m.rates(D, [key], yrs, h).iloc[0].values.astype(float)
    Y = m.winsor_cols(m.rates(D, pool, yrs, h), wins).values.astype(float)  # donors x years
    T0 = len(pre)
    Ypre, Ypost = Y[:, :T0], Y[:, T0:]
    d = np.diff(Ypre, axis=1).ravel()
    sigma = float(d.std(ddof=1)) if d.size > 1 else 0.0
    zeta = (n_tr * len(post)) ** 0.25 * sigma
    # unit weights: rows = before-years, columns = donors; intercept by centring over years
    A = Ypre.T - Ypre.T.mean(axis=0)
    b = y[:T0] - y[:T0].mean()
    w = simplex_ridge(A, b, zeta ** 2 * T0)
    # time weights: rows = donors, columns = before-years; intercept by centring over donors
    A2 = Ypre - Ypre.mean(axis=0)
    b2 = Ypost.mean(axis=1) - Ypost.mean(axis=1).mean()
    lam = simplex_ridge(A2, b2, (1e-6 * sigma) ** 2 * Y.shape[0])
    tau = (y[T0:].mean() - lam @ y[:T0]) - (w @ Ypost.mean(axis=1) - w @ Ypre @ lam)
    gap = y[:T0] - w @ Ypre
    hw = h.reindex(pool).values / h.reindex(pool).values.sum()
    gap_d = y[:T0] - hw @ Ypre
    return dict(effect=float(tau / scale), sigma=sigma, zeta=zeta, eff_donors=float(1 / np.sum(w ** 2)), max_w=float(w.max()),
                eff_years=float(1 / np.sum(lam ** 2)), max_lambda=float(lam.max()), last_year_lambda=float(lam[-1]),
                prefit_rmse=float(np.sqrt(np.mean((gap - gap.mean()) ** 2))),
                prefit_rmse_D=float(np.sqrt(np.mean((gap_d - gap_d.mean()) ** 2))))


def both(D, case, n_cases) -> dict:
    """D's pool and D's effect (as m.case_effect, candidate D), then SDID on that pool."""
    key, ey, pre, post, scale = case["key"], case["event_year"], list(case["pre"]), list(case["post"]), case.get("scale", 1.0)
    pl = m.long_pre(ey, pre, case.get("trimmed", False))
    s = m.select_pool(D, key, ey, pl, post, "A", m.OPT_MAIN)
    out = {"n_pool": len(s["pool"]), "step": s["step"]}
    if len(s["pool"]) < m.MIN_POOL:
        return {**out, "D": np.nan, "SDID": np.nan, "SDID, N_tr = 74": np.nan}
    out["D"] = m.did(D, key, pl, post, s["pool"], s["h"], m.OPT_MAIN["wins"], scale)
    main = sdid(D, key, pl, post, s["pool"], s["h"], m.OPT_MAIN["wins"], scale, 1)
    alt = sdid(D, key, pl, post, s["pool"], s["h"], m.OPT_MAIN["wins"], scale, n_cases)
    out["SDID"], out["SDID, N_tr = 74"] = main.pop("effect"), alt["effect"]
    out.update(main)
    out["zeta_ntr74"] = alt["zeta"]
    return out


def _fake(chunk):
    D, B, n = G["D"], G["B"], G["n"]
    orig = m.eligible

    def elig(D_, target, years, mode_exc, shock_on, h):  # pools from B only (as 3b's _today_restricted)
        return [k for k in orig(D_, target, years, mode_exc, shock_on, h) if k in B]
    m.eligible = elig
    out = {}
    try:
        for (k, ey, pre, post) in chunk:
            case = dict(key=k, event_year=ey, pre=pre, post=post, pop=D.popn.get(k, np.nan))
            r = both(D, case, n)
            for c in CANDS:
                out[(k, ey, pre, post, c)] = r[c]
    finally:
        m.eligible = orig
    return out


def _real(c):
    return both(G["D"], c, G["n"])


def ev_for_set(D, row, v):
    ev = pd.DataFrame({"v": [v[i] for *_, i in row], "homes": [D.homes_pre(ey)[k] for (k, ey, *_r) in row],
                       "n_post": [len(post) for (_, _, _, post, _) in row],
                       "band": m.band_of([D.popn.get(k, 0) for (k, *_r) in row]),
                       "metro": [D.metro.get(k, 0.0) for (k, *_r) in row]})
    ev["base"] = ev["homes"] * ev["n_post"]
    return ev


# ---------------------------------------------------------------- stages --------------------------------------------
def stage1():
    D, F, today, A, B, ok = m3.setup()
    assert today == "D", today
    real, cases = m.real_cases()
    print(len(cases), "repeal places (the fixed sample)", flush=True)
    v = m.placebo_v(len(real))
    sets = m3b.draw_sets(D, cases, B, SEED)
    uniq = sorted({(k, ey, pre, post) for row in sets for (k, ey, pre, post, _) in row})
    print(len(uniq), "distinct fake cases in", len(sets), "sets", flush=True)
    G.update(D=D, B=B, n=len(cases))
    m3.G.update(D=D, today=today, B=B)
    ctx = mp.get_context("fork")
    eff = {}
    with cf.ProcessPoolExecutor(WORKERS, mp_context=ctx) as ex:
        for part in ex.map(_fake, [uniq[i::WORKERS] for i in range(WORKERS)]):
            eff.update(part)
    # check: D here equals 3b's D-on-B (m3._today_restricted) on a sample of fake cases
    for (k, ey, pre, post) in uniq[:: max(1, len(uniq) // 25)]:
        case = dict(key=k, event_year=ey, pre=pre, post=post, pop=D.popn.get(k, np.nan))
        a, b = eff[(k, ey, pre, post, "D")], m3._today_restricted(case, B)
        assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-9, (k, ey, a, b)
    cells = m.target_cells(D, "55")
    m._G = dict(D=D, eff=eff, sets=sets, v=v, cells=cells)
    with cf.ProcessPoolExecutor(WORKERS, mp_context=ctx) as ex:
        res = list(ex.map(m._score, [(c, w) for c in CANDS for w in m.WEIGHTS]))
    R = pd.DataFrame(res)
    # per-set averages for the paired bootstrap, every weighting (verdict on random effects, as 3b)
    per = {(c, w): [] for c in CANDS for w in m.WEIGHTS}
    for row in sets:
        ev = ev_for_set(D, row, v)
        for c in CANDS:
            y = np.array([eff[(k, ey, pre, post, c)] for (k, ey, pre, post, _) in row])
            okr = np.isfinite(y)
            for w in m.WEIGHTS:
                per[(c, w)].append(abs(m.weighted_avg(w, y[okr], ev[okr].reset_index(drop=True), cells)))
    per = {k: np.array(x) for k, x in per.items()}
    for (c, w), a in per.items():
        mae_R = float(R[(R.candidate == c) & (R.weights == w)]["mae"].iloc[0])
        assert abs(a.mean() - mae_R) < 1e-9, (c, w, a.mean(), mae_R)
    rng = np.random.default_rng(SEED)
    idx = [rng.integers(0, m.SETS, m.SETS) for _ in range(m.BOOT)]
    picks = []
    for c in ("SDID", "SDID, N_tr = 74"):
        for w in m.WEIGHTS:
            diffs = np.array([per[(c, w)][i].mean() - per[("D", w)][i].mean() for i in idx])
            lo, hi = np.percentile(diffs, 5), np.percentile(diffs, 95)
            p = R[(R.candidate == c) & (R.weights == w)].iloc[0]
            d = R[(R.candidate == "D") & (R.weights == w)].iloc[0]
            a_ok, b_ok, c_ok = hi < 0, (d["mae"] - p["mae"]) >= 0.02 * d["mae"], 0.85 <= p["coverage"] <= 0.95
            picks.append(dict(candidate=c, weights=w, verdict_basis=(w == "random effects"),
                              mae_sdid=p["mae"], cov_sdid=p["coverage"], cov_sdid_se=p["coverage_se"],
                              mae_D=d["mae"], cov_D=d["coverage"], diff=p["mae"] - d["mae"], diff_p05=lo, diff_p95=hi,
                              gap_pct_of_D=(d["mae"] - p["mae"]) / d["mae"] * 100,
                              rule_a=bool(a_ok), rule_b=bool(b_ok), rule_c=bool(c_ok),
                              wins=bool(a_ok and b_ok and c_ok)))
    P = pd.DataFrame(picks)
    main = P[(P.candidate == "SDID") & P.verdict_basis].iloc[0]
    P["pick_main"] = "SDID" if main["wins"] else "D"
    nan_share = {c: float(np.mean([np.isnan(eff[(*u, c)]) for u in uniq])) for c in CANDS}
    R = R.assign(fresh_cases=len(uniq), nan_share=R.candidate.map(nan_share))
    R.round(5).to_csv(SCORING, index=False)
    P.round(5).to_csv(PICK, index=False)
    print(R.round(4).to_string(index=False))
    print(P.round(4).to_string(index=False))
    print("PICK (main SDID, random effects):", P["pick_main"].iloc[0])


def stage2():
    r = subprocess.run(["git", "ls-files", "--error-unmatch", str(PICK)], cwd=ROOT, capture_output=True)
    dq = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", str(PICK)], cwd=ROOT)
    if r.returncode or dq.returncode:
        raise SystemExit("commit reference/parking_t52_f_pick.csv first")
    m.SUF, m.CORRECTED = "_corrected", True
    D = m.Data()
    real, cases = m.real_cases()
    G.update(D=D, n=len(cases))
    with cf.ProcessPoolExecutor(WORKERS, mp_context=mp.get_context("fork")) as ex:
        res = list(ex.map(_real, cases))
    places = pd.DataFrame([{"place": c["place"], "state": c["state"], "event_year": c["event_year"], **r} for c, r in zip(cases, res)])
    # check: D equals the batch's corrected method-2 D effects for the same places
    bd = pd.read_csv(REFERENCE / "parking_method2_corrected_places.csv")
    bd = bd[bd["variant"] == "method 2, D"].reset_index(drop=True)
    assert len(bd) == len(places), (len(bd), len(places))
    dd = np.abs(places["D"].values - bd["effect"].values)
    assert np.nanmax(dd) < 1e-3 and (np.isnan(places["D"].values) == bd["effect"].isna().values).all(), np.nanmax(dd)
    v = m.placebo_v(len(real))
    ev = pd.DataFrame({"v": v, "homes": real["homes"].values, "n_post": real["n_post"].values,
                       "band": m.band_of(real["population"].fillna(0)), "metro": [D.metro.get(c["key"], 0.0) for c in cases]})
    ev["base"] = ev["homes"] * ev["n_post"]
    wi = m.target_cells(D, "55")
    out = []
    for lab in CANDS:
        y = places[lab].values.astype(float)
        okr = np.isfinite(y)
        for kind in m.WEIGHTS:
            a = m.weighted_avg(kind, y[okr], ev[okr].reset_index(drop=True), wi)
            lo, hi = m.boot_range(kind, y[okr], ev[okr].reset_index(drop=True), wi, m.BOOT, SEED)
            out.append(dict(variant=lab, weights=kind, places=int(okr.sum()), average=a, p05=lo, p95=hi,
                            wi_homes=a * m.WI_K, wi_p05=lo * m.WI_K, wi_p95=hi * m.WI_K))
    # paired difference SDID - D (same place draws), every weighting
    for lab in ("SDID", "SDID, N_tr = 74"):
        ys, yd = places[lab].values.astype(float), places["D"].values.astype(float)
        okr = np.isfinite(ys) & np.isfinite(yd)
        e = ev[okr].reset_index(drop=True)
        for kind in m.WEIGHTS:
            rng = np.random.default_rng(SEED)
            n = int(okr.sum())
            dif = []
            for _ in range(m.BOOT):
                i = rng.integers(0, n, n)
                ei = e.iloc[i].reset_index(drop=True)
                dif.append(m.weighted_avg(kind, ys[okr][i], ei, wi) - m.weighted_avg(kind, yd[okr][i], ei, wi))
            a = m.weighted_avg(kind, ys[okr], e, wi) - m.weighted_avg(kind, yd[okr], e, wi)
            lo, hi = np.percentile(dif, 5), np.percentile(dif, 95)
            out.append(dict(variant=f"{lab} minus D (paired)", weights=kind, places=n, average=a, p05=lo, p95=hi,
                            wi_homes=a * m.WI_K, wi_p05=lo * m.WI_K, wi_p95=hi * m.WI_K))
    pd.DataFrame(out).round(4).to_csv(OUT / "parking_t52_f_results.csv", index=False)
    places.round(5).to_csv(OUT / "parking_t52_f_places.csv", index=False)
    print(pd.DataFrame(out).round(3).to_string(index=False))
    print(places.describe().round(3).to_string())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, required=True, choices=(1, 2))
    stage1() if ap.parse_args().stage == 1 else stage2()


if __name__ == "__main__":
    main()
