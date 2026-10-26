"""Offline tests for the TOD scale check (missing_middleware/tod/scale_check.py; docs/tod/MODEL.md section 10).

Unit tests of the conversion arithmetic, plus consistency checks on the committed
reference/tod_scale_check.csv (no network)."""
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from missing_middleware.tod import scale_check as S  # noqa: E402

OUT = ROOT / "reference" / "tod_scale_check.csv"


class TestArithmetic(unittest.TestCase):
    def test_per_1000(self):
        self.assertAlmostEqual(S.per_1000(18_000, 845_070), 21.2999, places=3)
        with self.assertRaises(ValueError):
            S.per_1000(10, 0)

    def test_scenario_check_adds_and_flags(self):
        r = S.scenario_check(addition=3_000, housing_units=300_000, baseline_per_1000=5.0,
                             observed_max=20.0, p95=9.0, own_max=12.0)
        self.assertAlmostEqual(r["extra_per_1000"], 10.0)
        self.assertAlmostEqual(r["total_per_1000"], 15.0)
        self.assertEqual((r["exceeds_observed_max"], r["exceeds_p95"], r["exceeds_own_max"]), (False, True, True))
        z = S.scenario_check(0, 300_000, 5.0, 20.0, 9.0, 12.0)
        self.assertEqual(z["total_per_1000"], 5.0)
        self.assertFalse(z["exceeds_p95"])
        with self.assertRaises(ValueError):
            S.scenario_check(-1, 300_000, 5.0, 20.0, 9.0, 12.0)

    def test_benchmarks_and_own_history(self):
        p = pd.DataFrame({"cbsa_name": ["A"] * 5 + ["B"] * 5, "year": list(range(2021, 2026)) * 2,
                          "rate_5plus_per_1000": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10.0]})
        b = S.benchmarks(p)
        self.assertEqual((b.observed_max, b.observed_max_metro, b.observed_max_year), (10.0, "B", 2025))
        self.assertAlmostEqual(b.p95, 9.55)
        self.assertEqual((b.n_metro_years, b.n_metros), (10, 2))
        h = S.own_history(p[p["cbsa_name"] == "A"], (2021, 2022, 2023, 2024, 2025))
        self.assertEqual((h["own_max"], h["own_max_year"], h["recent_mean"]), (5.0, 2025, 3.0))
        with self.assertRaises(ValueError):
            S.own_history(p[p["cbsa_name"] == "A"], (2020, 2021))


@unittest.skipUnless(OUT.exists(), "reference/tod_scale_check.csv not built")
class TestCommittedOutput(unittest.TestCase):
    def setUp(self):
        self.df = pd.read_csv(OUT)

    def test_totals_and_flags_consistent(self):
        sc = self.df[self.df["kind"] == "scenario"]
        self.assertGreater(len(sc), 0)
        for r in sc.itertuples():
            self.assertAlmostEqual(r.total_per_1000, r.baseline_per_1000 + r.extra_per_1000, places=3)
            self.assertAlmostEqual(r.extra_per_1000, 1000 * r.addition_homes / r.housing_units, places=3)
            self.assertEqual(bool(r.exceeds_observed_max), r.total_per_1000 > r.observed_max)
            self.assertEqual(bool(r.exceeds_p95), r.total_per_1000 > r.p95)
            self.assertEqual(bool(r.exceeds_own_max), r.total_per_1000 > r.own_max)

    def test_metro_shares_do_not_exceed_state(self):
        sc = self.df[(self.df["kind"] == "scenario") & (self.df["statistic"] == "year")]
        share = sc.groupby(["scenario", "year"])["metro_share_of_statewide"].sum()
        self.assertTrue((share <= 1.0 + 1e-6).all())

    def test_only_method_a(self):
        sc = self.df[self.df["kind"] == "scenario"]
        self.assertEqual(set(sc["method"]), {"A"})


if __name__ == "__main__":
    unittest.main()
