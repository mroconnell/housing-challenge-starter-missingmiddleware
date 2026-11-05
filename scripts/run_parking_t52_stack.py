"""Test 52i (CAUSAL_FRAMEWORK_PLAN.md, "52i" and its audit fixes): weighting bake-off, then stacking if no clear winner.

Final estimator = method D (corrected method 2) as in the batch (no Test 52 change accepted by Ryan yet). Per-place D
effects are read from the batch (`reference/batch_2026-11-05/parking_method2_corrected_places.csv`, variant
"method 2, D"); the weights and the leave-one-state-out test follow run_parking_method2.stage2.

    MM_REFERENCE_DIR=<batch working copy> uv run --all-extras python scripts/run_parking_t52_stack.py
Outputs: reference/parking_t52_i_*.csv (written to the real reference/ folder via ROOT, never to the working copy).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import run_parking_method2 as m  # noqa: E402

SEED, DRAWS = 20261105, 2000
OUT = ROOT / "reference"
K = list(m.WEIGHTS)


def setup():
    m.SUF, m.CORRECTED = "_corrected", True
    D = m.Data()
    real, cases = m.real_cases()
    pl = pd.read_csv(ROOT / "reference" / "batch_2026-11-05" / "parking_method2_corrected_places.csv")
    pl = pl[pl["variant"] == "method 2, D"].reset_index(drop=True)
    assert (pl["place"].values == np.array([c["place"] for c in cases])).all(), "place order"
    y = pl["effect"].values.astype(float)
    ev = pd.DataFrame({"v": m.placebo_v(len(real)), "homes": real["homes"].values, "n_post": real["n_post"].values,
                       "band": m.band_of(real["population"].fillna(0)), "metro": [D.metro.get(c["key"], 0.0) for c in cases]})
    ev["base"] = ev["homes"] * ev["n_post"]
    ok = np.isfinite(y)
    return D, real.loc[ok].reset_index(drop=True), y[ok], ev[ok].reset_index(drop=True)


def fold_preds(real, y, ev, idx=None):
    """Leave-one-state-out: truth and each weighting's prediction per held-out state (states with 3+ places).
    idx: optional resampled place indices (within-state resampling for the paired bootstrap)."""
    if idx is not None:
        real, y, ev = real.iloc[idx].reset_index(drop=True), y[idx], ev.iloc[idx].reset_index(drop=True)
    st = real["state"].values
    rows = []
    for s in STATES:
        hold, train = st == s, st != s
        truth = float(np.average(y[hold], weights=ev["base"].values[hold]))
        hc = ev[hold].groupby(["metro", "band"])["base"].sum()
        et = ev[train].reset_index(drop=True)
        rows.append([truth] + [m.weighted_avg(k, y[train], et, hc) for k in K])
    return pd.DataFrame(rows, index=STATES, columns=["truth"] + K)


def strat_idx(rng, st):
    """Resample places within states (audit fix 4): every state keeps its size."""
    out = []
    for s in np.unique(st):
        g = np.flatnonzero(st == s)
        out.append(rng.choice(g, len(g), replace=True))
    return np.concatenate(out)


def fit_shares(P, t):
    """Non-negative shares summing to 1 that minimise the mean absolute error of P @ s against t (an LP)."""
    n, k = P.shape
    c = np.r_[np.zeros(k), np.ones(n) / n]
    A = np.block([[P, -np.eye(n)], [-P, -np.eye(n)]])
    b = np.r_[t, -t]
    r = linprog(c, A_ub=A, b_ub=b, A_eq=np.r_[np.ones(k), np.zeros(n)][None, :], b_eq=[1.0],
                bounds=[(0, None)] * (k + n), method="highs")
    assert r.success, r.message
    return np.clip(r.x[:k], 0, None) / np.clip(r.x[:k], 0, None).sum()


def blend_draws(y, ev, cells, shares, rng_seed):
    """Paired sum (main) and mixture (beside it) of the weightings' bootstrap draws on the same place draws."""
    rng = np.random.default_rng(rng_seed)
    n = len(y)
    per = np.empty((DRAWS, len(K)))
    for d in range(DRAWS):
        i = rng.integers(0, n, n)
        ei = ev.iloc[i].reset_index(drop=True)
        per[d] = [m.weighted_avg(k, y[i], ei, cells) for k in K]
    paired = per @ shares
    mix_rng = np.random.default_rng(rng_seed + 1)
    pick = mix_rng.choice(len(K), DRAWS, p=shares)
    mixture = per[np.arange(DRAWS), pick]
    return paired, mixture


def main() -> None:
    global STATES
    D, real, y, ev = setup()
    vc = real["state"].value_counts()
    STATES = list(vc[vc >= 3].index)
    st = real["state"].values
    F = fold_preds(real, y, ev)
    E = F[K].sub(F["truth"], axis=0).abs()
    mae = E.mean()
    best = mae.idxmin()
    runner = mae.drop(best).idxmin()
    # paired bootstrap of the error difference, resampling places within states
    rng = np.random.default_rng(SEED)
    boots = []
    for _ in range(DRAWS):
        Fb = fold_preds(real, y, ev, strat_idx(rng, st))
        boots.append(Fb[K].sub(Fb["truth"], axis=0).abs().mean())
    B = pd.DataFrame(boots)
    rows = []
    clear = True
    for k in K:
        if k == best:
            continue
        d = B[best] - B[k]
        lo, hi = np.percentile(d, [5, 95])
        rows.append(dict(best=best, other=k, mae_best=mae[best], mae_other=mae[k], diff=mae[best] - mae[k],
                         diff_p05=lo, diff_p95=hi, below_zero=hi < 0))
        clear &= hi < 0
    gap = (mae[runner] - mae[best]) / mae[runner]
    clear &= gap >= 0.02
    bake = pd.DataFrame(rows)
    bake["gap_vs_runner_up_pct"] = 100 * gap
    bake["clear_winner"] = clear
    bake.round(4).to_csv(OUT / "parking_t52_i_bakeoff.csv", index=False)
    E.assign(truth=F["truth"]).round(4).to_csv(OUT / "parking_t52_i_fold_errors.csv")
    print("MAE", mae.round(4).to_dict(), "best", best, "gap %", round(100 * gap, 2), "clear", clear)
    print(bake.round(3).to_string(index=False))
    wi = m.target_cells(D, "55")
    res = []
    if clear:
        a = m.weighted_avg(best, y, ev, wi)
        lo, hi = m.boot_range(best, y, ev, wi, DRAWS, SEED)
        res.append(dict(result=f"clear winner: {best}", rate=a, p05=lo, p95=hi))
    else:
        # nested stacking: shares fit on the other states, scored on the held-out one
        P, t = F[K].values, F["truth"].values
        fold_rows, nested_err, covered = [], [], []
        for j, s in enumerate(STATES):
            keep = np.arange(len(STATES)) != j
            sh = fit_shares(P[keep], t[keep])
            pred = float(P[j] @ sh)
            nested_err.append(abs(pred - t[j]))
            # held-out coverage: the blend's 90% range from the training places (paired sum), cells of the held-out state
            hold, train = st == s, st != s
            hc = ev[hold].groupby(["metro", "band"])["base"].sum()
            paired, _ = blend_draws(y[train], ev[train].reset_index(drop=True), hc, sh, SEED + j)
            lo, hi = np.percentile(paired, [5, 95])
            covered.append(lo <= t[j] <= hi)
            fold_rows.append(dict(held_out=s, **{f"share_{k}": v for k, v in zip(K, sh)}, pred=pred, truth=t[j],
                                  abs_error=abs(pred - t[j]), range_p05=lo, range_p95=hi, covered=lo <= t[j] <= hi))
        folds = pd.DataFrame(fold_rows)
        folds.round(4).to_csv(OUT / "parking_t52_i_folds.csv", index=False)
        shares = fit_shares(P, t)
        cov = float(np.mean(covered))
        a = float(sum(s_ * m.weighted_avg(k, y, ev, wi) for s_, k in zip(shares, K)))
        paired, mixture = blend_draws(y, ev, wi, shares, SEED)
        # effective number of places of the blended place weights
        w = np.zeros(len(y))
        for s_, k in zip(shares, K):
            if k == "random effects":
                wk, _ = m.dl_weights(m.winsor(y), ev["v"].values)
            elif k == "target-state mix":
                wk, _ = m.mix_weights(ev, wi)
            elif k == "square root":
                wk = np.sqrt(ev["homes"].values) * ev["n_post"].values
            elif k == "homes":
                wk = ev["homes"].values * ev["n_post"].values
            else:
                wk = np.ones(len(y))
            w += s_ * wk / wk.sum()
        n_eff = float(w.sum() ** 2 / (w ** 2).sum())
        passes = 0.85 <= cov <= 0.95
        res.append(dict(result="stacked blend" + ("" if passes else " (coverage test failed: target-state mix stays)"),
                        rate=a, p05=float(np.percentile(paired, 5)), p95=float(np.percentile(paired, 95)),
                        mixture_p05=float(np.percentile(mixture, 5)), mixture_p95=float(np.percentile(mixture, 95)),
                        nested_mae=float(np.mean(nested_err)), single_pick_mae=float(mae[best]), coverage=cov,
                        states=len(STATES), effective_places=n_eff, passes=passes,
                        **{f"share_{k}": v for k, v in zip(K, shares)},
                        **{f"share_{k}_fold_min": folds[f"share_{k}"].min() for k in K},
                        **{f"share_{k}_fold_max": folds[f"share_{k}"].max() for k in K}))
        print(folds.round(3).to_string(index=False))
    for k in K:  # every weighting beside it
        a = m.weighted_avg(k, y, ev, wi)
        lo, hi = m.boot_range(k, y, ev, wi, DRAWS, SEED)
        res.append(dict(result=f"single: {k}", rate=a, p05=lo, p95=hi))
    R = pd.DataFrame(res)
    for c in ("rate", "p05", "p95", "mixture_p05", "mixture_p95"):
        if c in R:
            R[c.replace("rate", "wi_homes").replace("p05", "wi_p05").replace("p95", "wi_p95") if c in ("rate", "p05", "p95")
              else "wi_" + c] = R[c] * m.WI_K
    R.round(4).to_csv(OUT / "parking_t52_i_results.csv", index=False)
    pd.set_option("display.width", 250)
    print(R.round(3).T.to_string())


if __name__ == "__main__":
    main()
