"""Parking scenario model under option A (missing_middleware/parking/model.py). Offline."""
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.parking import model as pm

REF = Path(__file__).resolve().parent.parent / "reference"


class TestModel(unittest.TestCase):
    def setUp(self):
        self.areas = pd.DataFrame({"area_id": ["a", "b", "c"], "homes": [1000.0, 2000.0, 500.0],
                                   "muni_type": ["city", "town", "village"]})

    def test_benchmark_places_get_zero(self):
        h = pm.eligible_homes(self.areas, {"a"})
        self.assertEqual(h["a"], 0.0)
        self.assertEqual(h["b"], 2000.0)

    def test_towns_zero_case(self):
        h = pm.eligible_homes(self.areas, set(), ("town",))
        self.assertEqual(h["b"], 0.0)

    def test_additions_flat_and_never_negative(self):
        h = pm.eligible_homes(self.areas, set())
        add = pm.additions(h, 2.0)
        self.assertEqual(list(add.columns), list(pm.FORECAST_YEARS))
        self.assertAlmostEqual(add.loc["b", 2027], 4.0)          # 2,000 homes x 2 / 1,000
        self.assertAlmostEqual(add.values.sum(), 3500 * 2 / 1000 * 5)
        neg = pm.additions(h, pd.Series({"a": -3.0, "b": 1.0, "c": 0.0}))
        self.assertEqual(neg.loc["a"].sum(), 0.0)

    def test_size_metro_rate_floor(self):
        r = pm.size_metro_rate(pd.Series([1e3, 1e6]), pd.Series([1, 0]), (10.0, -3.0, 2.0))
        self.assertAlmostEqual(r.iloc[0], 3.0)   # 10 - 9 + 2
        self.assertEqual(r.iloc[1], 0.0)          # 10 - 18 -> floored


@unittest.skipUnless((REF / "parking_model_by_area.csv").exists(), "model not built")
class TestOutputs(unittest.TestCase):
    def test_statewide_equals_sum_of_areas_and_central_zero(self):
        a = pd.read_csv(REF / "parking_model_by_area.csv")
        s = pd.read_csv(REF / "parking_model_statewide_by_year.csv")
        self.assertAlmostEqual(a["addition_upper_five_year"].sum(), s["addition_upper"].sum(), delta=1.0)
        self.assertEqual(s["addition_central"].sum(), 0.0)
        self.assertTrue((a.loc[a["at_benchmark"], "addition_upper_five_year"] == 0).all())
        self.assertTrue((a["addition_upper_five_year"] >= 0).all())


if __name__ == "__main__":
    unittest.main()
