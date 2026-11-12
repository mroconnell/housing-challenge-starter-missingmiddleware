"""Test 61 code checks on MADE-UP data only (no permit file, no working copy, no dose table).
A planted trait effect is detected (passes the rule against one average and the dose-scaled average); pure noise fails;
the shuffle check removes a planted effect; permutation importance points at the planted trait; the cell map and the
pass rule are as the plan says.

    uv run --all-extras python -m unittest tests.test_parking_t61 -v
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_parking_t61_forest as t61  # noqa: E402

REPEATS, FOLDS = 5, 5  # small for speed; the real run uses 20 x 10


def synth(planted: bool, n: int = 90, seed: int = 1):
    """3-trait matrix as the script builds it: dose, log10 population, 5 class indicators (some NaN), y, w, d."""
    rng = np.random.default_rng(seed)
    d = rng.choice([0.2, 0.5, 1.0], n)
    lp = rng.uniform(3.5, 6.0, n)
    cls = pd.Series(rng.choice(t61.CLASSES, n))
    cls.iloc[:3] = "unknown"  # missing class -> NaN -> training-fold median
    X = np.column_stack([d, lp, t61.one_hot(cls).values])
    X[5, 1] = np.nan          # a missing population
    w = rng.uniform(0.5, 3.0, n)
    noise = rng.normal(0, 0.3, n)
    y = (2.0 * (lp > 4.75) - 1.0) * 2.0 + noise if planted else noise  # a strong population step, unrelated to dose
    return X, y, w, d


class TestT61(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.planted = t61.score_cell(*synth(True), repeats=REPEATS, folds=FOLDS)
        cls.null = t61.score_cell(*synth(False), repeats=REPEATS, folds=FOLDS)

    def test_cell_map(self):
        self.assertEqual(t61.N_CELLS, 16)
        self.assertEqual(t61.N_SHUFFLE_ROWS, 4)
        cols, groups = t61.columns_for(t61.TRAITS3)
        self.assertEqual(len(cols), 7)
        self.assertEqual(groups["area class"], [2, 3, 4, 5, 6])
        cols4, g4 = t61.columns_for(t61.TRAITS4)
        self.assertEqual(cols4[:7], cols)
        self.assertEqual(g4["rate before repeal"], [7])
        self.assertEqual(t61.JUDGED, ("units_2_4", "3 traits (judged)", "one weighted average"))
        self.assertEqual((t61.SEED, t61.REPEATS, t61.FOLDS), (20261105, 20, 10))

    def test_pass_rule(self):
        self.assertTrue(t61.passes([0.07] * 8 + [-0.01] * 2))        # mean 5.4%, 80% above 0
        self.assertFalse(t61.passes([0.06] * 8 + [-0.01] * 2))       # mean 4.6%
        self.assertFalse(t61.passes([0.09] * 7 + [-0.01] * 3))       # mean 6.0%, only 70% above 0
        self.assertFalse(t61.passes([0.04] * 10))                     # mean under 5%
        self.assertTrue(t61.passes([0.05] * 10))

    def test_median_fill(self):
        Xtr = np.array([[1.0, np.nan], [3.0, np.nan], [np.nan, np.nan]])
        Xte = np.array([[np.nan, np.nan]])
        a, b = t61.median_fill(Xtr, Xte)
        self.assertEqual(a[2, 0], 2.0)
        self.assertEqual(b[0, 0], 2.0)
        self.assertEqual(b[0, 1], 0.0)

    def test_planted_effect_detected(self):
        for bench in t61.BENCHMARKS:
            s = t61.summarise(self.planted, bench)
            self.assertTrue(s["meets_rule"], (bench, s))
            self.assertGreater(s["mean_gain"], 0.2)

    def test_no_effect_fails(self):
        s = t61.summarise(self.null, t61.BENCHMARKS[0])
        self.assertFalse(s["meets_rule"], s)
        self.assertLess(s["mean_gain"], 0.05)

    def test_dose_benchmark_refits_beta(self):
        # y = 3 x dose exactly: the dose-scaled benchmark is perfect, the one average is not
        X, _, w, d = synth(False)
        r = t61.score_repeat(X, 3 * d, w, d, 0, folds=FOLDS)
        self.assertAlmostEqual(r["mae_dose"], 0.0, places=10)
        self.assertGreater(r["mae_one"], 0.1)

    def test_shuffle_removes_effect(self):
        X, y, w, d = synth(True)
        sh = pd.DataFrame([t61.score_repeat(X, y, w, d, s, folds=FOLDS, shuffle_seed=t61.SHUFFLE_SEED)
                           for s in range(3)])
        self.assertLess(t61.gains(sh, "mae_one").mean(), 0.05)

    def test_importance_points_at_planted_trait(self):
        X, y, w, d = synth(True)
        _, groups = t61.columns_for(t61.TRAITS3)
        r = t61.score_repeat(X, y, w, d, 0, folds=FOLDS, importance_groups=groups)
        base = t61.score_repeat(X, y, w, d, 0, folds=FOLDS)
        self.assertAlmostEqual(r["mae_forest"], base["mae_forest"], places=12)  # stacking leaves the fit unchanged
        inc = {g: r[f"mae_permuted|{g}"] / r["mae_forest"] - 1 for g in groups}
        self.assertEqual(max(inc, key=inc.get), "log10 population 2010")
        self.assertGreater(inc["log10 population 2010"], 0.5)


if __name__ == "__main__":
    unittest.main()
