"""reference/tod_places_for_parking_2x2.csv: loads, unique geoids per group, only allowed coded values."""
from __future__ import annotations

import unittest

import pandas as pd

from missing_middleware.paths import REFERENCE

CSV = REFERENCE / "tod_places_for_parking_2x2.csv"
COLUMNS = ["place_name", "state", "geo_type", "geoid", "tod_case_ids", "group", "upzoning_year",
           "parking_changed_with_upzoning", "separate_parking_reform", "parking_source", "notes"]
GEOID_LEN = {"place": 7, "county_subdivision": 10, "county": 5}


class TestPlacesForParking2x2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(CSV, dtype=str).fillna("")

    def test_columns(self):
        self.assertEqual(list(self.df.columns), COLUMNS)
        self.assertGreater(len(self.df), 0)

    def test_unique_geoids_per_group(self):
        for g, d in self.df.groupby("group"):
            self.assertFalse(d.geoid.duplicated().any(), g)
        # no place is in both groups
        self.assertFalse(self.df.geoid.duplicated().any())

    def test_allowed_values(self):
        df = self.df
        self.assertTrue(set(df.group) <= {"upzoned", "neither_candidate"})
        self.assertTrue(set(df.geo_type) <= set(GEOID_LEN))
        for _, r in df.iterrows():
            self.assertEqual(len(r.geoid), GEOID_LEN[r.geo_type], r.place_name)
            self.assertTrue(r.geoid.isdigit(), r.place_name)
        up, ne = df[df.group == "upzoned"], df[df.group == "neither_candidate"]
        self.assertTrue(set(up.parking_changed_with_upzoning) <= {"yes", "no", "partial", "unknown"})
        self.assertTrue(up.upzoning_year.str.fullmatch(r"(19|20)\d\d").all())
        self.assertTrue((up.tod_case_ids != "").all())
        self.assertTrue((ne.parking_changed_with_upzoning == "").all())
        self.assertTrue((ne.upzoning_year == "").all())


if __name__ == "__main__":
    unittest.main()
