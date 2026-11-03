"""TOD line draws (scripts/export_tod_line_draws.py): the CSV exists, medians sit near the tool's point values, and the
lower line's published 90% interval (2,279 to 5,791) is reproduced."""
import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

REF = Path(__file__).resolve().parent.parent / "reference"
CSV, META = REF / "tod_line_draws.csv", REF / "tod_line_draws_meta.json"


class TestTodLineDraws(unittest.TestCase):
    def setUp(self):
        self.assertTrue(CSV.exists(), "run scripts/export_tod_line_draws.py")
        self.D = pd.read_csv(CSV)
        self.meta = json.loads(META.read_text())

    def test_columns_and_counts(self):
        self.assertEqual(list(self.D.columns), ["draw", "lower_homes", "central_homes", "upper_homes",
                                                "lower_per100ac", "central_per100ac"])
        self.assertEqual(len(self.D), self.meta["draws"]["central"])
        self.assertEqual(self.D.draw.tolist(), list(range(1, len(self.D) + 1)))
        self.assertFalse(self.D.isna().any().any())

    def test_medians_near_points(self):
        for line, point in (("lower", 3958), ("central", 10028), ("upper", 12521)):
            med = self.D[f"{line}_homes"].median()
            self.assertLess(abs(med / point - 1), 0.05, (line, med))

    def test_upper_tied_to_central(self):
        np.testing.assert_allclose(self.D.upper_homes, self.D.central_homes * 12521 / 10028, rtol=1e-6)

    def test_lower_interval_reproduces_published(self):
        first = self.D.lower_homes.iloc[:1000]           # the published 1,000 draws
        self.assertEqual((round(np.percentile(first, 5)), round(np.percentile(first, 95))), (2279, 5791))
        lo, hi = np.percentile(self.D.lower_homes, [5, 95])   # all 2,000 draws
        self.assertAlmostEqual(lo, 2279, delta=30)
        self.assertAlmostEqual(hi, 5791, delta=30)

    def test_central_interval_reproduces_published(self):
        lo, hi = np.quantile(self.D.central_per100ac, [.05, .95])
        self.assertEqual((round(lo, 1), round(hi, 1)), (16.3, 51.4))


if __name__ == "__main__":
    unittest.main()
