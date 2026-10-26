"""Parking benchmark classification (missing_middleware/parking/taxonomy.py). Offline."""
import unittest
from pathlib import Path

import pandas as pd

from missing_middleware.parking import taxonomy as tx

REF = Path(__file__).resolve().parent.parent / "reference"


class TestRate(unittest.TestCase):
    def test_full_citywide_repeal_is_at(self):
        self.assertEqual(tx.rate("rm_min", ["citywide"], ["all uses"], ["by right"])[0], "at")

    def test_transit_only_is_weaker(self):
        self.assertEqual(tx.rate("rm_min", ["transit-oriented"], ["all uses"], ["by right"])[0], "weaker")
        self.assertEqual(tx.rate("rm_min", ["citywide"], ["all uses"], ["by right", "frequent transit"])[0], "weaker")

    def test_reduce_is_weaker(self):
        self.assertEqual(tx.rate("reduce_min", ["citywide"], ["all uses"], ["by right"])[0], "weaker")

    def test_affordable_only_is_weaker(self):
        self.assertEqual(tx.rate("rm_min", ["citywide"], ["residential, all uses"], ["affordable housing"])[0], "weaker")

    def test_low_density_only_is_weaker_multifamily_only_is_near(self):
        self.assertEqual(tx.rate("rm_min", ["citywide"], ["residential, low-density"], ["accessory dwelling units", "by right"])[0], "weaker")
        self.assertEqual(tx.rate("rm_min", ["citywide"], ["residential, multi-family"], ["by right"])[0], "near")

    def test_project_size_limit_is_near(self):
        self.assertEqual(tx.rate("rm_min", ["citywide"], ["all uses"], ["by right", "size of project"])[0], "near")

    def test_non_residential(self):
        self.assertEqual(tx.rate("rm_min", ["citywide"], ["commercial"], ["by right"])[0], "not_housing")

    def test_plan_recommendation_is_plan_only(self):
        s = "The Comprehensive Plan recommends reducing or eliminating minimum parking requirements."
        self.assertEqual(tx.rate("rm_min", ["citywide"], ["all uses"], ["by right"], s)[0], "plan_only")
        s2 = "The plan recommended it, and the council repealed all parking mandates in 2024."
        self.assertEqual(tx.rate("rm_min", ["citywide"], ["all uses"], ["by right"], s2)[0], "at")

    def test_classify_skips_non_us_and_keeps_dates(self):
        core = {"A": {"place": {"name": "A", "state": "X", "country": "United States", "type": "city", "pop": 1},
                      "rm_min": [{"status": "adopted", "scope": ["citywide"], "land": ["all uses"], "date": "2021-05-14"}]},
                "B": {"place": {"name": "B", "state": "Y", "country": "Canada", "type": "city", "pop": 1},
                      "rm_min": [{"status": "adopted", "scope": ["citywide"], "land": ["all uses"], "date": None}]}}
        ext = {"A": {"rm_min": [{"requirements": ["by right"], "summary": "Removed.", "reporter": "Someone",
                                 "citations": [{"url": "https://example.org"}]}]}}
        df = tx.classify(core, ext)
        self.assertEqual(list(df["place"]), ["A"])
        self.assertEqual(int(df["adopted_year"].iloc[0]), 2021)
        self.assertNotIn("reporter", df.columns)


@unittest.skipUnless((REF / "parking_reform_taxonomy.csv").exists(), "taxonomy not built")
class TestCommitted(unittest.TestCase):
    def test_no_reporter_names_and_known_cases(self):
        d = pd.read_csv(REF / "parking_reform_taxonomy.csv")
        self.assertNotIn("reporter", d.columns)
        c = pd.read_csv(REF / "parking_reform_cases.csv")
        at = set(c.loc[c["benchmark_rating"] == "at", "place"])
        self.assertTrue({"Buffalo", "Minneapolis", "West Allis"} <= at)
