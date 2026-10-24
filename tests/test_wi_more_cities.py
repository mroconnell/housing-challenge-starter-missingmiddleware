"""Offline tests for the more-Wisconsin-places measurement and the rules-vs-activity test."""
from __future__ import annotations

import importlib
import unittest
from pathlib import Path

import pandas as pd

from missing_middleware.permits import wi_more_cities as wm

ROOT = Path(__file__).resolve().parent.parent
FIX = Path(__file__).resolve().parent / "fixtures" / "wi_more_cities"
REF = ROOT / "reference"


def fixture_measured() -> pd.DataFrame:
    py = pd.read_csv(FIX / "place_years.csv")
    homes = pd.read_csv(FIX / "homes.csv", dtype={"geoid": str})
    return wm.measured_table(py, homes, quality={"alpha": ("A", ""), "beta": ("B", ""), "gamma": ("C", "")})


class MeasuredTable(unittest.TestCase):
    def test_rates_and_years(self):
        m = fixture_measured().set_index("slug")
        self.assertEqual(m.loc["alpha", "permits"], 20)
        self.assertEqual(m.loc["alpha", "years_observed"], 4)
        self.assertAlmostEqual(m.loc["alpha", "rate_per_1000_homes_yr"], 20 / (4 * 10))
        # gamma: 2022 incomplete, so 3 complete years and not measured over the whole window
        self.assertEqual(m.loc["gamma", "years_observed"], 3)
        self.assertFalse(m.loc["gamma", "measured_full_window"])
        self.assertEqual(m.loc["gamma", "permits"], 2)
        self.assertEqual(m.loc["gamma", "permits_upper"], 3)
        self.assertEqual(m.loc["gamma", "partial_months_not_used"], "2022:5")
        self.assertEqual(m.loc["beta", "rate_per_1000_homes_yr"], 0)
        self.assertEqual(m.loc["beta", "permits_upper"], 1)

    def test_groups_v1_and_v11(self):
        m = fixture_measured()
        g = wm.groups(m, "measured_full_window").set_index("slug")
        self.assertEqual(g.loc["alpha", "group_v1"], "active")       # top quarter, >= 3 permits
        self.assertEqual(g.loc["beta", "group_v1"], "restrictive")   # zero
        self.assertEqual(g.loc["gamma", "group_v1"], "restrictive")  # unmeasured over the window
        self.assertEqual(g.loc["alpha", "group_v1_1"], "middle")     # fewer than 20 measured places
        m["measured_2plus"] = m["years_observed"].ge(2)
        g2 = wm.groups(m, "measured_2plus").set_index("slug")
        self.assertEqual(g2.loc["gamma", "group_v1"], "middle")


class Helpers(unittest.TestCase):
    def test_poisson_ci(self):
        lo, hi = wm.poisson_ci(0)
        self.assertEqual(lo, 0)
        self.assertAlmostEqual(hi, 3.6889, places=3)
        lo, hi = wm.poisson_ci(5)
        self.assertAlmostEqual(lo, 1.6235, places=3)
        self.assertAlmostEqual(hi, 11.6683, places=3)

    def test_strictness(self):
        self.assertEqual(wm.strictness("scenario_benchmark", ""), 0)
        self.assertEqual(wm.strictness("restricted", "size_below_benchmark"), 1)
        self.assertEqual(wm.strictness("restricted", "size_below_benchmark;owner_occupancy"), 2)
        self.assertEqual(wm.strictness("prohibited_implicit", ""), 3)

    def test_spearman(self):
        r = wm.spearman(pd.Series([1, 2, 3, 4, 5]), pd.Series([2, 4, 6, 8, 10]), n_perm=2000)
        self.assertAlmostEqual(r["rho"], 1.0)
        self.assertLess(r["p_perm"], 0.05)
        self.assertTrue(pd.isna(wm.spearman(pd.Series([1, 1, 1]), pd.Series([1, 2, 3]))["rho"]))

    def test_crosstab_and_rates(self):
        m = wm.groups(fixture_measured(), "measured_full_window")
        m["rights_group"] = ["scenario_benchmark", "prohibited", "restricted"]
        xt = wm.crosstab_long(m, "rights_group", "group_v1", "fx")
        self.assertEqual(int(xt["places"].sum()), 3)
        r = wm.rate_by_rule(m, "rights_group", "fx").set_index("rule_value")
        self.assertAlmostEqual(r.loc["scenario_benchmark", "pooled_rate_per_1000_homes_yr"], 0.5)


class CodedRules(unittest.TestCase):
    def test_coded_rules_cover_37_places(self):
        r = wm.coded_rules(REF)
        coded = r[r["rules_source"].str.startswith("coded")]
        self.assertEqual(len(coded), 37)
        self.assertTrue(coded["ordinance_status"].notna().all())
        self.assertEqual(set(coded["current_class"]) - {"scenario_benchmark", "restricted", "prohibited_explicit",
                                                        "prohibited_implicit"}, set())
        mad = r.set_index("jurisdiction_name").loc["Madison city"]
        self.assertEqual(mad["strictness"], 0)
        self.assertEqual(mad["window_class"], "restricted")
        # restricted places: tier labels follow the flags
        for _, x in coded[coded["current_class"].eq("restricted")].iterrows():
            self.assertEqual(x["tier"] == "tier-1 flag", x["n_tier1"] > 0)

    def test_window_rules_name_coded_places(self):
        names = set(wm.coded_rules(REF)["jurisdiction_name"])
        self.assertTrue(set(wm.WINDOW_RULES) <= names)


class Adapters(unittest.TestCase):
    def test_adapter_interface(self):
        mun = pd.read_csv(REF / "wi_baseline_by_municipality.csv", dtype={"geoid": str})
        for s in wm.ADAPTERS:
            m = importlib.import_module(f"missing_middleware.permits.wimc_{s}")
            for f in ("fetch", "load", "coverage", "classify_records"):
                self.assertTrue(callable(getattr(m, f)), f"{s}.{f}")
            self.assertIn(m.META["stage"], ("issued", "application"))
            self.assertTrue(set(m.META["geoids"]) <= set(mun["geoid"]), s)
            self.assertIn(s, wm.QUALITY)


if __name__ == "__main__":
    unittest.main()
