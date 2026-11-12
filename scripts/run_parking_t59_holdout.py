"""Test 59 (post hoc; CAUSAL_FRAMEWORK_PLAN.md "Test 59"): hold one place out, 2-4 unit homes.

    uv run --all-extras python scripts/run_parking_t59_holdout.py

Reads Test 56's saved per-place outputs (data/processed/t56/units_2_4_ref) through summarise_parking_t56's audited
helpers; runs no pipeline. Outputs reference/parking_t59_drop_one.csv and reference/parking_t59_predict.csv.

Part 1: each place dropped in turn; overall effect recomputed (main: weighted average with the placebo spread rebuilt
without the place; D: target-state mix and method 2's bootstrap on the other 73).
Part 2: predict each hidden place's after-repeal rate. A = its own before rate plus its comparison towns' change (no
reform effect), so A's miss is the place's effect. B = A plus the other 73 places' weighted average effect, so B's miss
is the effect minus that average. Score = weighted root mean square miss (headline weights); weighted mean absolute miss
beside it. B beats A only if its score is lower and the 90% range of (A - B) over 2,000 place resamples excludes 0.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.pop("MM_BPS_OUTCOME", None)

import summarise_parking_t56 as s  # noqa: E402

O = "units_2_4"
WI = 13343.385
SEED, DRAWS = 20261105, 2000


def loo_means(y: np.ndarray, w: np.ndarray) -> np.ndarray:
    tot, wt = np.sum(w * y), np.sum(w)
    return (tot - w * y) / (wt - w)


def scores(y: np.ndarray, w: np.ndarray) -> dict:
    missA = y
    missB = y - loo_means(y, w)
    wn = w / w.sum()
    return dict(rmsA=float(np.sqrt(np.sum(wn * missA ** 2))), rmsB=float(np.sqrt(np.sum(wn * missB ** 2))),
                maeA=float(np.sum(wn * np.abs(missA))), maeB=float(np.sum(wn * np.abs(missB))))


def main() -> None:
    C = s.Ctx()
    m = C.m
    yM, wM, yD = s.place_effects(O)
    ev = C.ev(O)
    draws = s.standin_draws(O)
    wD, _ = m.mix_weights(ev, C.wi)
    wD = np.asarray(wD, float)
    places = C.F["place"].values
    all74 = np.ones(74, bool)
    full = {"main": s.overall_main(C, O, yM, wM, all74, False, draws), "D": s.overall_d(C, O, yD, ev, all74, False)}

    rows = []
    for i in range(74):
        sel = all74.copy()
        sel[i] = False
        for meth in ("main", "D"):
            a, lo, hi = s.overall_main(C, O, yM, wM, sel, False, draws) if meth == "main" else s.overall_d(C, O, yD, ev, sel, False)
            rows.append(dict(method=meth, dropped=places[i], estimate=a, p05=lo, p95=hi,
                             excludes_0=bool(lo > 0 or hi < 0), shift=a - full[meth][0],
                             sign_flip=bool(np.sign(a) != np.sign(full[meth][0])),
                             estimate_wisconsin_homes_5yr=a * WI))
    d1 = pd.DataFrame(rows)
    d1.round(6).to_csv(s.REF / "parking_t59_drop_one.csv", index=False)

    out = []
    for meth, y, w in (("main", yM, wM), ("D", yD, wD)):
        ok = np.isfinite(y) & (w > 0)
        y, w = y[ok], w[ok]
        sc = scores(y, w)
        # misses fixed once on the real places (audit: recomputing leave-one-out means inside a resample lets a
        # duplicated place help predict itself); the resample draws those fixed misses with their weights
        mA, mB = y, y - loo_means(y, w)
        rng = np.random.default_rng(SEED)
        diff = []
        for _ in range(DRAWS):
            j = rng.integers(0, len(y), len(y))
            wn = w[j] / w[j].sum()
            diff.append(float(np.sqrt(np.sum(wn * mA[j] ** 2)) - np.sqrt(np.sum(wn * mB[j] ** 2))))
        lo, hi = np.percentile(diff, [5, 95])
        beats = bool(sc["rmsB"] < sc["rmsA"] and (lo > 0 or hi < 0))
        out.append(dict(method=meth, places=int(ok.sum()), rms_miss_A_no_effect=sc["rmsA"], rms_miss_B_learned_effect=sc["rmsB"],
                        mae_miss_A=sc["maeA"], mae_miss_B=sc["maeB"], A_minus_B=sc["rmsA"] - sc["rmsB"], A_minus_B_p05=float(lo),
                        A_minus_B_p95=float(hi), B_beats_A=beats,
                        reading="the learned effect improves prediction of a hidden place" if beats else
                        "the learned effect does not improve prediction of a hidden place",
                        note="B carries a leave-one-out penalty, so with an average near 0 it can score slightly worse than A",
                        unit="homes per 1,000 existing homes a year"))
    d2 = pd.DataFrame(out)
    d2.round(6).to_csv(s.REF / "parking_t59_predict.csv", index=False)

    pd.set_option("display.width", 250)
    for meth in ("main", "D"):
        q = d1[d1["method"] == meth]
        print(f"{meth}: full {full[meth][0]:.4f} ({full[meth][1]:.4f} to {full[meth][2]:.4f}); leave-one-out min {q.estimate.min():.4f} "
              f"max {q.estimate.max():.4f}; any range excluding 0: {int(q.excludes_0.sum())}; sign flips: {int(q.sign_flip.sum())}")
        print(q.reindex(q["shift"].abs().sort_values(ascending=False).index).head(5)[["dropped", "estimate", "p05", "p95", "shift"]]
              .round(4).to_string(index=False))
    print(d2.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
