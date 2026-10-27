"""TOD comparison cases, batch 2 (Toronto, Ottawa, Minneapolis): rules on small synthetic fixtures, no network.

Fixtures: tests/fixtures/tod/cases_batch2/ (made-up permits; no real identifiers).
"""
from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.tod import case_minneapolis as MPL
from missing_middleware.tod import case_ottawa as OTT
from missing_middleware.tod import case_toronto as TOR
from missing_middleware.tod import cases as C

FIX = Path(__file__).resolve().parent / "fixtures" / "tod" / "cases_batch2"


class TestTorontoRules(unittest.TestCase):
    def test_exception_numbers_mark_the_bylaw_lands(self):
        self.assertEqual(TOR.exception_no("CR SS2  (x2631)"), 2631)
        self.assertIsNone(TOR.exception_no("RD (f14.0; a510)"))
        self.assertTrue(TOR.in_bylaw(2621) and TOR.in_bylaw(2648))
        self.assertFalse(TOR.in_bylaw(2620) or TOR.in_bylaw(2649) or TOR.in_bylaw(None))
        self.assertEqual(set(TOR.EXCEPTION_HEIGHT_M), set(TOR.EXCEPTIONS))

    def test_zone_classes(self):
        self.assertEqual(TOR.zone_class("RD"), "res")
        self.assertEqual(TOR.zone_class("CR"), "mixed")
        self.assertEqual(TOR.zone_class("CL"), "com")
        for z in ("O", "UT", "E", "EH", "IH", None):
            self.assertIsNone(TOR.zone_class(z))

    def test_permit_selection(self):
        p = TOR.select_new_permits(pd.read_csv(FIX / "toronto_permits.csv", dtype=str))
        self.assertEqual(sorted(p["PERMIT_NUM"]), ["10 000001 BLD", "10 000002 NH", "10 000003 BLD", "10 000008 BLD"])
        # revision 00 carries the permit's units and issue year; later revisions are dropped
        r = p.set_index("PERMIT_NUM").loc["10 000001 BLD"]
        self.assertEqual((r["units"], r["year"]), (120.0, 2010))
        self.assertEqual(p["units"].sum(), 120 + 1 + 3 + 45)

    def test_address_key(self):
        self.assertEqual(TOR.address_key("230-240", "Main", "East"), "230|MAIN|E")
        self.assertEqual(TOR.address_key("12", "O'Connor", None), "12|OCONNOR|")

    def test_nearest_number_same_side_within_gap(self):
        ref = pd.DataFrame({"street": ["MAIN|E"] * 4 + ["ELM|"], "num": [100, 104, 101, 160, 102]}, index=[10, 11, 12, 13, 14])
        want = pd.DataFrame({"street": ["MAIN|E", "MAIN|E", "MAIN|E", "OAK|"], "num": [106, 103, 135, 100]}, index=["a", "b", "c", "d"])
        got = TOR.nearest_number(ref, want, max_gap=20)
        self.assertEqual(got["a"], 11)          # 104: even side, nearest
        self.assertEqual(got["b"], 12)          # 101: odd side
        self.assertTrue(np.isnan(got["c"]))     # odd side: nearest is 101, 34 away
        self.assertTrue(np.isnan(got["d"]))     # street not in the reference

    def test_height_dose(self):
        self.assertAlmostEqual(TOR.height_dose_m(2631, 16.0), 6.5)
        self.assertTrue(np.isnan(TOR.height_dose_m(2621, 24.0)))   # exception sets no height
        self.assertTrue(np.isnan(TOR.height_dose_m(2628, 25.5)))   # overlay added by the by-law itself
        self.assertTrue(np.isnan(TOR.height_dose_m(2630, None)))
        self.assertTrue(np.isnan(TOR.height_dose_m(2630, -1.0)))


class TestOttawaRules(unittest.TestCase):
    def test_before_years_from_july_2011(self):
        self.assertEqual(OTT.full_before_years(2012), 0)
        self.assertEqual(OTT.full_before_years(2014), 2)
        self.assertEqual(OTT.full_before_years(2020), C.BEFORE_MAX)
        self.assertEqual(OTT.full_before_years(2014, "2011-01"), 3)

    def test_bylaw_step(self):
        self.assertEqual(OTT.bylaw_step("2012-406", " "), "2012-406")
        self.assertEqual(OTT.bylaw_step(" 2014-022, PL140185", ""), "2014-022")
        self.assertEqual(OTT.bylaw_step("2015-190", "2012-406"), "2012-406")
        self.assertIsNone(OTT.bylaw_step("2020-212", " "))


class TestMinneapolisRules(unittest.TestCase):
    def test_new_residential_permits(self):
        p = pd.read_csv(FIX / "minneapolis_permits.csv", dtype=str)
        q = MPL.new_res_permits(p)
        self.assertEqual(sorted(q["Permit_Number"]), ["1", "2", "5"])

    def test_station_names_merge_platforms(self):
        self.assertEqual(MPL.station_name("46th Street IB"), "46th Street")
        self.assertEqual(MPL.station_name("50th Street/Minnehaha Park OB"), "50th Street/Minnehaha Park")


class TestCasesWithoutEstimate(unittest.TestCase):
    """Ottawa and Minneapolis record why they have no estimate, through the shared estimate_case."""

    def _row(self, ci):
        return C.estimate_case(ci, draws=10)[1]

    def test_status_carried_and_no_estimate(self):
        for mod in (OTT, MPL):
            ci = C.CaseInputs(case="x", role="fit", effective_year=2012, first_year=2012, last_full_year=2025,
                              permits=pd.DataFrame(columns=["project", "area", "year", "units"]), acres={}, homes={},
                              dose_table=None, status_override="context_only: test")
            row = self._row(ci)
            self.assertEqual(row["status"], "context_only: test")
            self.assertIsNone(row["estimate_units_per_acre_yr"])
            self.assertTrue(callable(mod.build) and callable(mod.build_counts))

    def test_toronto_interface(self):
        self.assertTrue(callable(TOR.build))
        self.assertEqual(TOR.EFFECTIVE_YEAR, 2014)


if __name__ == "__main__":
    unittest.main()
