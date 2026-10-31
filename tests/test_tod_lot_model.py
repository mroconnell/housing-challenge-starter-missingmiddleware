"""Small checks of the TOD lot model's rules (audit scorecard, round 1). Runs under unittest, as scripts/test.sh does."""
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import run_tod_lot_model as L  # noqa: E402


class TestLotModel(unittest.TestCase):
    def test_fold_excludes_own_placebo_and_itself(self):
        cities = ["Madison", "Madison placebo", "Milwaukee placebo", "New York", "Saint Paul"]
        self.assertEqual(L.training_cities(cities, "Madison"), ["Milwaukee placebo", "New York", "Saint Paul"])
        self.assertEqual(L.training_cities(cities, "Madison placebo"), ["Milwaukee placebo", "New York", "Saint Paul"])
        self.assertIn("Saint Paul", L.training_cities(cities + ["Saint Louis"], "Saint Louis"))

    def test_rezoned_later_is_zero_at_forecast_time(self):
        X = pd.DataFrame({"rezoned_later": [1.0, 0.0], "log_acres": [0.1, 0.2]})
        out = L.forecast_view(X)
        self.assertEqual(out["rezoned_later"].tolist(), [0.0, 0.0])
        self.assertEqual(X["rezoned_later"].tolist(), [1.0, 0.0])   # the input is not changed

    def test_units_table_gives_every_trait_a_unit(self):
        t = ROOT / "reference" / "tod_lot_model_trait_units_v37.csv"
        if not t.exists():
            self.skipTest("units table not built yet")
        T = pd.read_csv(t)
        if "trait" not in T.columns:
            self.skipTest("units table is the older wide layout; rebuilt by scripts/run_tod_lot_model_units.py")
        self.assertTrue({"trait", "city", "median", "p5", "p95", "unit"} <= set(T.columns))
        self.assertTrue(T["unit"].fillna("").str.len().gt(0).all(), sorted(set(T.loc[T["unit"].isna(), "trait"])))


if __name__ == "__main__":
    unittest.main()
