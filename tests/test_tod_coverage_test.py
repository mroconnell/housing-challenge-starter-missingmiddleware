"""TOD coverage test (docs/UNIFORM_DISPLAY_SPEC.md): the simulation, the widening factor and the widening (offline)."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_tod_coverage_test as T  # noqa: E402


class TestTodCoverage(unittest.TestCase):
    def test_simulation_is_seeded_and_ranges_bracket_the_point(self):
        pool = np.array([1.0, 5.0, -3.0, 20.0, 7.0, 2.5, 11.0])
        a, b = T.simulate(pool, runs=50, draws=200), T.simulate(pool, runs=50, draws=200)
        pd.testing.assert_frame_equal(a, b)
        self.assertTrue((a.lo <= a.point + 1e-9).all() and (a.point <= a.hi + 1e-9).all())

    def test_constant_shift_does_not_change_coverage(self):
        pool = np.array([1.0, 5.0, -3.0, 20.0, 7.0, 2.5, 11.0])
        a, b = T.simulate(pool, runs=200, draws=300), T.simulate(pool + 100, runs=200, draws=300)
        self.assertEqual(T.coverage(a, pool.mean()), T.coverage(b, pool.mean() + 100))

    def test_needed_factor_is_the_smallest_reaching_target(self):
        pool = np.array([0.0, 0.0, 0.0, 1.0, 50.0, 2.0, 3.0, -4.0])     # skewed: under-covers
        sim = T.simulate(pool, runs=400, draws=300)
        truth = pool.mean()
        self.assertLess(T.coverage(sim, truth), 0.9)
        f = T.needed_factor(sim, truth)
        self.assertGreater(f, 1.0)
        self.assertGreaterEqual(T.coverage(sim, truth, f), 0.9)
        self.assertLess(T.coverage(sim, truth, f * (1 - 1e-9)), 0.9)

    def test_needed_factor_hand_case(self):
        sim = pd.DataFrame({"point": [10.0] * 10, "lo": [8.0] * 10, "hi": [11.0] * 10})
        truths_need = {13.0: 3.0, 7.0: 1.5, 10.5: 1.0}
        for truth, need in truths_need.items():
            self.assertAlmostEqual(T.needed_factor(sim, truth), need)

    def test_widen(self):
        self.assertEqual(T.widen(10.0, 6.0, 15.0, 1.5), (4.0, 17.5))
        self.assertEqual(T.widen(10.0, 6.0, 15.0, 1.0), (6.0, 15.0))

    def test_fake_pool_reads_ten_places(self):
        s = T.fake_pool()
        self.assertEqual(len(s), 10)
        self.assertAlmostEqual(s.mean(), 14.5076, places=3)
        self.assertAlmostEqual(s.drop("Seattle Othello").mean(), 1.72, places=2)

    def test_output_csv_shape(self):
        if not T.OUT_CSV.exists():
            self.skipTest("run scripts/run_tod_coverage_test.py first")
        t = pd.read_csv(T.OUT_CSV)
        self.assertEqual(set(t.check), {"coverage", "bias", "widening"})
        cov = t[t.check == "coverage"].value
        self.assertTrue(((cov >= 0) & (cov <= 1)).all())
        self.assertFalse(any(c in t.columns for c in ("parcel_id", "lot_index")))


if __name__ == "__main__":
    unittest.main()
