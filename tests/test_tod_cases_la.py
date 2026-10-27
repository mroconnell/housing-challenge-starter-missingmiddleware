"""Los Angeles case adapter (missing_middleware/tod/case_la.py): helpers on synthetic data, no network."""
from __future__ import annotations

import unittest

import pandas as pd

from missing_middleware.tod import case_la as L


class TestZones(unittest.TestCase):
    def test_base_zone(self):
        self.assertEqual(L.base_zone("(T)(Q)C2-1VL-CDO"), "C2")
        self.assertEqual(L.base_zone("[Q]R1-1D"), "R1")
        self.assertEqual(L.base_zone("UV(CA)"), "UV")
        self.assertEqual(L.base_zone("RD1.5-1-HPOZ"), "RD")
        self.assertEqual(L.base_zone("MR2-1"), "MR2")
        self.assertEqual(L.base_zone("C1.5-1"), "C1.5")
        self.assertEqual(L.base_zone("WC"), "WC")
        self.assertIsNone(L.base_zone(None))

    def test_levels_and_classes(self):
        self.assertGreater(L.level("UV(CA)"), L.level("M2-1"))   # industrial to urban village: rose
        self.assertGreater(L.level("UC(CA)"), L.level("C2-1"))
        self.assertLess(L.level("UI(CA)"), L.level("C2-1"))      # urban innovation: live/work only
        self.assertEqual(L.zclass("M2-1"), "ind")
        self.assertEqual(L.zclass("[Q]C4-1XL-CDO"), "com")
        self.assertEqual(L.zclass("PF-1XL"), "inst")

    def test_zone_changed(self):
        a = pd.Series(["C2-1", "M2-1", None, "R3-1"])
        b = pd.Series(["C2-1", "UV(CA)", "R1-1", "R3-1 "])
        self.assertEqual(list(L.zone_changed(a, b)), [False, True, False, False])

    def test_new_housing_filter(self):
        p = pd.DataFrame({"permit_type": ["Bldg-New", "Bldg-New", "Bldg-New", "Bldg-Alter/Repair"],
                          "du_changed": ["40", "0", "12", "3"],
                          "work_desc": ["NEW 5-STORY APARTMENT", "PATIO COVER", "SUPPLEMENTAL PERMIT TO 12345", "REMODEL"]})
        self.assertEqual(list(L.is_new_housing(p)), [True, False, False, False])

    def test_cases_match_inventory_ids(self):
        inv = pd.read_csv(L.RAW.parent.parent / "reference" / "tod_cases.csv", dtype=str)
        self.assertTrue(set(L.CASES) <= set(inv["case_id"]))


if __name__ == "__main__":
    unittest.main()
