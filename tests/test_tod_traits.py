"""TOD trait test (missing_middleware/tod/traits.py; docs/tod/TRAITS_PLAN.md): rules on small synthetic tables, no
network. The committed outputs are checked for identifiers and for the plan's fixed rules when they exist."""
from __future__ import annotations

import math
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.tod import cases as C
from missing_middleware.tod import traits as T

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference"


def synthetic(slope: float = 1.0, noise: float = 0.0, seed: int = 1) -> pd.DataFrame:
    """Units in six cities whose effect is slope * x (+ noise); weights 10 acres each."""
    rng = np.random.default_rng(seed)
    rows = []
    for k, c in enumerate(T.CITY_ORDER):
        for i in range(5):
            x = k + i * 0.5
            rows.append({"city": c, "x": x, "effect": slope * x + noise * rng.normal(), "weight": 10.0})
    return pd.DataFrame(rows)


class TestUnits(unittest.TestCase):
    def test_five_acre_rule(self):
        self.assertEqual(T.keep_unit(5.0, 5.0), (True, "kept"))
        self.assertFalse(T.keep_unit(4.99, 100.0)[0])
        self.assertFalse(T.keep_unit(100.0, 4.0)[0])
        self.assertFalse(T.keep_unit(float("nan"), 10.0)[0])
        self.assertIn("both", T.keep_unit(1.0, 1.0)[1])

    def test_unit_estimate_matches_case_did(self):
        p = pd.DataFrame({"project": ["a", "b", "c", "d"], "area": [C.TREAT, C.TREAT, C.COMP, C.COMP],
                          "year": [2014, 2018, 2014, 2018], "units": [10, 40, 20, 20]})
        acres = {C.TREAT: 10.0, C.COMP: 20.0}
        e = T.unit_estimate(p, acres, [2013, 2014], [2017, 2018], draws=200)
        # treatment: 10/10/2 = 0.5 before, 40/10/2 = 2.0 after; comparison 20/20/2 = 0.5 both
        self.assertAlmostEqual(e["did"], 1.5)
        self.assertLessEqual(e["low"], e["high"])
        self.assertTrue(math.isnan(T.unit_estimate(p, acres, [], [2018])["did"]))

    def test_sector_labels(self):
        self.assertEqual(T.sector_label(10, 10, 100), "core")
        self.assertEqual(T.sector_label(0, 5000, 100), "north")
        self.assertEqual(T.sector_label(5000, 0, 100), "east")
        self.assertEqual(T.sector_label(0, -5000, 100), "south")
        self.assertEqual(T.sector_label(-5000, 0, 100), "west")
        self.assertEqual(T.sector_label(3000, 3000, 100), "northeast")
        self.assertEqual(T.sector_label(-3000, -3000, 100), "southwest")

    def test_station_clusters_merge_platforms(self):
        import geopandas as gpd
        from shapely.geometry import Point
        s = gpd.GeoSeries([Point(0, 0), Point(50, 0), Point(1000, 0), Point(5000, 0)], crs=32616)
        names = pd.Series(["Main St Station", "Main St Station Platform 2", "Oak Ave Station", "Main St Station"])
        g = T.cluster_stations(s, names)
        self.assertEqual(len(g), 3)
        self.assertEqual(sorted(g["station"]), ["Main St (1)", "Main St (2)", "Oak Ave"])

    def test_comparison_for_unit_uses_quarter_mile(self):
        import geopandas as gpd
        from shapely.geometry import box
        lots = gpd.GeoDataFrame(geometry=[box(0, 0, 10, 10), box(300, 0, 310, 10), box(1000, 0, 1010, 10)], crs=32616)
        ix = T.comparison_for_unit(lots, pd.Index([0]), pd.Index([1, 2]))
        self.assertEqual(list(ix), [1])


class TestTraits(unittest.TestCase):
    def test_logs_where_the_plan_says(self):
        logged = {k for k, v in T.TRAITS.items() if v["log"]}
        self.assertEqual(logged, {"t01_home_value", "t03_existing_density", "t04_income", "t05_city_land_area", "t06_rent"})
        self.assertEqual(len(T.TRAITS), 12)
        d = pd.DataFrame({"t06_rent": [1000.0, 0.0], "t03_existing_density": [0.0, np.e - 1]})
        r = T.transform(d, "t06_rent")
        self.assertAlmostEqual(r.iloc[0], math.log(1000))
        self.assertTrue(math.isnan(r.iloc[1]))
        self.assertAlmostEqual(T.transform(d, "t03_existing_density").iloc[1], 1.0)

    def test_cpi(self):
        self.assertAlmostEqual(T.cpi_to_2024(218.056, 2010), 313.689)

    def test_weighted_mean(self):
        self.assertAlmostEqual(T.weighted_mean(pd.Series([1.0, 3.0, np.nan]), pd.Series([1.0, 3.0, 5.0])), 2.5)


class TestHeldOut(unittest.TestCase):
    def test_baseline_is_weighted_mean_of_other_cities(self):
        d = synthetic()
        e = T.heldout_errors(d, [], y="effect", w="weight")
        ny = e[e.city == "New York"].iloc[0]
        others = d[d.city.isin([c for c in T.FIT_CITIES if c != "New York"])]
        self.assertAlmostEqual(ny.predicted_mean_baseline, others.effect.mean())
        self.assertEqual(set(e[e.role == "always held out"].city), set(T.TEST_CITIES))
        self.assertEqual(int(e[e.city == "Chicago"].fit_units.iloc[0]), 20)  # all four fitting cities, never Chicago or Madison

    def test_held_out_cities_never_fitted(self):
        d = synthetic()
        d.loc[d.city.isin(T.TEST_CITIES), "effect"] = 1e6   # if these were fitted, every fold would be ruined
        e = T.heldout_errors(d, ["x"])
        self.assertTrue((e[e.role == "fold"].error_model < 1e-6).all())

    def test_true_trait_passes_and_noise_does_not(self):
        d = synthetic()
        j = T.judge(T.heldout_errors(d, ["x"]))
        self.assertEqual(j["verdict"], "pass")
        rng = np.random.default_rng(3)
        d2 = synthetic(slope=0.0, noise=1.0)
        d2["z"] = rng.normal(size=len(d2))
        self.assertIn(T.judge(T.heldout_errors(d2, ["z"]))["verdict"], {"fail", "near-miss"})

    def test_judge_rules(self):
        e = pd.DataFrame({"role": ["fold"] * 4, "error_baseline": [1.0, 1.0, 1.0, 1.0], "error_model": [0.5, 0.9, 1.2, 1.1]})
        self.assertEqual(T.judge(e)["verdict"], "pass")            # mean 0.925 < 1 and 2 of 4 cities better
        e["error_model"] = [0.1, 1.2, 1.2, 1.2]
        self.assertEqual(T.judge(e)["verdict"], "near-miss")       # better on average but in one city only
        e["error_model"] = [0.9, 0.9, 1.5, 1.5]
        self.assertEqual(T.judge(e)["verdict"], "fail")            # 2 cities better but worse on average
        e["error_model"] = [1.1, 1.2, 1.2, 1.2]
        self.assertEqual(T.judge(e)["verdict"], "fail")
        two = pd.DataFrame({"role": ["fold"] * 2, "error_baseline": [1.0, 1.0], "error_model": [0.5, 1.01]})
        self.assertEqual(T.judge(two)["verdict"], "near-miss")      # half of two folds is one city: a near-miss

    def test_missing_trait_units_dropped_from_both(self):
        d = synthetic()
        d.loc[d.city == "Charlotte", "x"] = np.nan
        e = T.heldout_errors(d, ["x"])
        self.assertNotIn("Charlotte", set(e.city))

    def test_two_trait_sets(self):
        self.assertEqual(T.two_trait_sets(["a", "b", "c"]), [("a", "b"), ("a", "c"), ("b", "c")])
        self.assertEqual(T.two_trait_sets(["a"]), [])


class TestOutputs(unittest.TestCase):
    def test_no_identifiers(self):
        for name in ("tod_trait_units.csv", "tod_trait_values.csv", "tod_trait_results.csv", "tod_trait_errors.csv",
                     "tod_trait_heldout_units.csv", "tod_trait_wisconsin.csv"):
            f = REF / name
            if not f.exists():
                continue
            d = pd.read_csv(f)
            self.assertEqual(T.check_private(d, allowed={"t02_lot_size", "treatment_lot_count"}), [], name)

    def test_units_follow_the_plan(self):
        f = REF / "tod_trait_units.csv"
        if not f.exists():
            self.skipTest("units not built")
        u = pd.read_csv(f)
        k = u[u.kept]
        self.assertTrue((k.treatment_acres >= T.MIN_ACRES).all() and (k.comparison_acres >= T.MIN_ACRES).all())
        self.assertTrue(set(u.city) <= set(T.CITY_ORDER))
        self.assertTrue((u[u.city.isin(T.TEST_CITIES)].role == "always held out").all())
        self.assertTrue(u.unit_id.is_unique)


if __name__ == "__main__":
    unittest.main()
