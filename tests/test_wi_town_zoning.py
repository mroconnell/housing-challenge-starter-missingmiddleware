"""Wisconsin town general-zoning status (missing_middleware/foundation/town_zoning.py).
Offline; tiny synthetic DOA workbook and town list in tests/fixtures/wi_town_zoning/
(FIPS codes partly invented). Checks the shipped reference table if present."""
import unittest
from pathlib import Path

import pandas as pd

from missing_middleware.foundation import town_zoning as tz

FIX = Path(__file__).parent / "fixtures" / "wi_town_zoning"
REF = Path(__file__).resolve().parent.parent / "reference" / "wi_town_zoning_status.csv"


def load():
    inv = tz.read_doa_inventory(FIX / "doa_inventory_sample.xlsx")
    towns = pd.read_csv(FIX / "towns_sample.csv", dtype=str)
    towns["homes_1unit_detached"] = towns["homes_1unit_detached"].astype(int)
    out = tz.classify_towns(inv, towns, strict=False)
    return inv, towns, out.set_index("name")


class TestParse(unittest.TestCase):
    def test_norm_fips(self):
        self.assertEqual(tz.norm_fips(8350.0), "08350")
        self.assertEqual(tz.norm_fips("2025"), "02025")
        self.assertIsNone(tz.norm_fips(None))

    def test_read_inventory(self):
        inv, _, _ = load()
        self.assertEqual(set(inv["gov_type"]), {"County", "Town", "Village"})  # trailing blank row dropped
        self.assertIn("08350", set(inv["fips5"]))
        c = tz.county_status(inv).set_index("county")["county_general_zoning"]
        self.assertEqual(c["Crawford"], "no")
        self.assertEqual(c["Grant"], "county")


class TestClassify(unittest.TestCase):
    def setUp(self):
        _, self.towns, self.out = load()

    def test_one_row_per_town_and_vocab(self):
        self.assertEqual(len(self.out), len(self.towns))
        self.assertTrue(self.out["zoning_status"].isin(tz.STATUSES).all())
        self.assertTrue(self.out["verification"].isin(tz.VERIFICATION).all())

    def test_doa_codes_map(self):
        self.assertEqual(self.out.loc["Bridgeport town", "zoning_status"], "town_own")
        self.assertEqual(self.out.loc["Beetown town", "zoning_status"], "unzoned")
        self.assertEqual(self.out.loc["Beetown town", "verification"], "source_lead")
        self.assertEqual(self.out.loc["Blooming Grove town", "zoning_status"], "county_general")  # float FIPS

    def test_unknown_never_guessed(self):
        # blank DOA code and a town missing from the inventory both stay unknown
        for n in ("Nowhere town", "Missing town"):
            self.assertEqual(self.out.loc[n, "zoning_status"], "unknown")
            self.assertEqual(self.out.loc[n, "verification"], "unknown")

    def test_overrides(self):
        o = self.out
        self.assertEqual(o.loc["Eastman town", "zoning_status"], "unzoned")  # county has no general zoning
        self.assertEqual(o.loc["Platteville town", "zoning_status"], "unknown")
        self.assertEqual(o.loc["Angelo town", "zoning_status"], "town_own")
        self.assertEqual(o.loc["Angelo town", "source_date"], "2026-06-30")
        self.assertEqual(o.loc["Cameron town", "zoning_status"], "town_own")
        self.assertEqual(o.loc["Arpin town", "zoning_status"], "unknown")
        self.assertIn("1934", o.loc["Arpin town", "notes"])

    def test_verified_upgrade(self):
        self.assertEqual(self.out.loc["Boscobel town", "verification"], "verified")
        self.assertEqual(self.out.loc["Dexter town", "verification"], "verified")

    def test_type_mismatch_still_matched(self):
        r = self.out.loc["Rib Falls town"]
        self.assertEqual(r["zoning_status"], "county_general")
        self.assertIn("village", r["notes"])

    def test_county_general_requires_county_zoning(self):
        inv = tz.read_doa_inventory(FIX / "doa_inventory_sample.xlsx")
        inv.loc[inv["place_name"] == "Bridgeport", "general_zoning"] = "county"  # Crawford has none
        with self.assertRaises(ValueError):
            tz.classify_towns(inv, self.towns, strict=False)

    def test_strict_requires_listed_towns(self):
        inv = tz.read_doa_inventory(FIX / "doa_inventory_sample.xlsx")
        with self.assertRaises(KeyError):
            tz.classify_towns(inv, self.towns, strict=True)

    def test_summarize(self):
        s = tz.summarize(self.out.reset_index(), self.towns).set_index("zoning_status")
        self.assertEqual(s.loc["total", "towns"], len(self.towns))
        self.assertEqual(s.loc["total", "homes_1unit_detached"], self.towns["homes_1unit_detached"].sum())


@unittest.skipUnless(REF.exists(), "reference table not built")
class TestReferenceTable(unittest.TestCase):
    def test_shape_and_keys(self):
        r = pd.read_csv(REF, dtype={"geoid": str})
        self.assertEqual(len(r), 1243)
        self.assertTrue(r["geoid"].str.fullmatch(r"55\d{8}").all())
        self.assertTrue((r["area_id"] == "muni:" + r["geoid"]).all())
        self.assertFalse(r["geoid"].duplicated().any())
        self.assertTrue(r["zoning_status"].isin(tz.STATUSES).all())
        self.assertTrue(r["verification"].isin(tz.VERIFICATION).all())
        self.assertTrue((r.loc[r["zoning_status"] != "unknown", "source_url"].str.startswith("https://")).all())
        # unknown rows carry verification unknown
        self.assertTrue((r.loc[r["zoning_status"] == "unknown", "verification"] == "unknown").all())


if __name__ == "__main__":
    unittest.main()
