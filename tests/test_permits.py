"""Permit pipeline: ingestion drops owner fields, dedupe, address parsing, matching,
text + parcel classification, contract output. Offline; synthetic fixtures only."""
import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from missing_middleware import contracts
from missing_middleware.permits import address, classify, madison, pipeline
from missing_middleware.permits.match import AddressIndex

FIX = Path(__file__).parent / "fixtures" / "permits"


def load_fixture_raw() -> pd.DataFrame:
    tmp = Path(tempfile.mkdtemp())
    try:
        shutil.copy(FIX / "construction_summary_fixture.txt", tmp / "construction_summary_2024.csv")
        return madison.load_raw_permits(tmp)
    finally:
        shutil.rmtree(tmp)


def fixture_parcels() -> pd.DataFrame:
    rows = [  # parcel_id, house, street_key, du, year_built, use, x, y
        ("P100", 100, "EXAMPLE ST", 2, 1925, "Single family", -89.400, 43.070),
        ("P102", 102, "EXAMPLE ST", 2, 1950, "Single family", -89.401, 43.070),
        ("P104", 104, "EXAMPLE ST", 1, 1960, "Single family", -89.402, 43.070),
        ("P106", 106, "EXAMPLE ST", 1, 1910, "Single family", -89.403, 43.070),
        ("P108", 108, "EXAMPLE ST", 1, 1930, "Single family", -89.404, 43.070),
        ("P200", 200, "N SAMPLE AVE", 1, 2024, "Single family", -89.500, 43.080),
    ]
    df = pd.DataFrame(rows, columns=["parcel_id", "house_nbr", "street_key", "dwelling_units", "year_built",
                                     "property_use", "x", "y"])
    df["parcel_address"] = df["house_nbr"].astype(str) + " " + df["street_key"].str.title()
    df["unit"] = ""
    df["property_class"] = "Residential"
    df["zoning"] = "TR-C2"
    return df


def fixture_index(parcels: pd.DataFrame) -> AddressIndex:
    ref = parcels.rename(columns={"parcel_address": "address_full"})[
        ["house_nbr", "street_key", "unit", "parcel_id", "address_full", "x", "y"]]
    return AddressIndex(ref)


def fake_areas(xy: pd.DataFrame) -> pd.DataFrame:
    tract = ["55025000100" if x > -89.45 else "55025000200" for x in xy["x"]]
    return pd.DataFrame({"tract_geoid": tract, "bg_geoid": [t + "1" for t in tract]}, index=xy.index)


class TestIngestion(unittest.TestCase):
    def test_owner_fields_dropped_and_summary_rows_skipped(self):
        raw = load_fixture_raw()
        self.assertEqual(len(raw), 8)
        flat = " ".join(raw.astype(str).agg(" ".join, axis=1))
        self.assertNotIn("TESTOWNER", flat)
        self.assertNotIn("FAKE RD", flat)
        self.assertEqual(raw.loc[0, "units_raw"], 1)
        self.assertEqual(raw.loc[0, "est_cost"], 180000)

    def test_dedupe_keeps_first_issue_date(self):
        d = pipeline.dedupe(load_fixture_raw())
        self.assertEqual(len(d), 7)
        r = d[d.permit_id == "BLDNRC-2024-00001"].iloc[0]
        self.assertEqual(str(r.issue_date.date()), "2024-03-01")
        self.assertEqual(r.n_source_rows, 2)


class TestAddress(unittest.TestCase):
    def test_parse_unit_and_direction(self):
        keys = {"N SAMPLE AVE", "MAPLE GROVE DR"}
        p = address.parse("4101 Maple Grove Dr. #201", keys)
        self.assertEqual((p.house_nbr, p.street_key, p.unit), (4101, "MAPLE GROVE DR", "201"))
        p = address.parse("200 N SAMPLE AVE REAR", keys)
        self.assertEqual((p.street_key, p.unit), ("N SAMPLE AVE", "REAR"))
        p = address.parse("101-103 MAPLE GROVE DR", keys)
        self.assertEqual(p.house_alt, (101, 103))

    def test_street_key_from_parts(self):
        self.assertEqual(address.street_key_from_parts("N", "Sample", "Avenue"), "N SAMPLE AVE")


class TestClassify(unittest.TestCase):
    def test_text_rules(self):
        self.assertEqual(classify.text_class("NEW DETACHED ADU")[0], "adu_detached")
        self.assertEqual(classify.text_class("CONVERT BASEMENT TO ACCESSORY DWELLING UNIT")[0], "adu_conversion")
        self.assertEqual(classify.text_class("ATTACHED ADU ADDITION")[0], "adu_attached")
        cat, note = classify.text_class("CONVERT COACH HOUSE TO SINGLE FAMILY HOME")
        self.assertIsNone(cat)
        self.assertTrue(note.startswith("near_miss"))
        self.assertIsNone(classify.text_class("BADUM STREET GARAGE")[0])


class TestPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parcels = fixture_parcels()
        cls.full = pipeline.build_permits_observed(
            load_fixture_raw(), fixture_index(parcels), parcels, parcels[["parcel_id", "x", "y"]], fake_areas)
        cls.obs = pipeline.to_contract(cls.full, madison.SOURCE_ID, madison.JURISDICTION_ID)

    def row(self, pid):
        return self.full[self.full.permit_id == pid].iloc[0]

    def test_categories(self):
        self.assertEqual(self.row("BLDNRC-2024-00001").unit_category, "adu_detached")
        r2 = self.row("BLDNRC-2024-00002")
        self.assertEqual((r2.unit_category, r2.classification_method), ("adu_equivalent", "parcel_rule"))
        self.assertEqual(r2.match_quality, "confirmed")  # REAR suffix does not block the match
        r3 = self.row("BLDNRC-2024-00003")
        self.assertEqual(r3.unit_category, "other_residential")
        self.assertEqual(r3.parcel_rule_reason, "first_dwelling_on_parcel")
        r4 = self.row("BLDRPR-2024-00004")
        self.assertEqual(r4.unit_category, "adu_conversion")
        self.assertFalse(r4.counted)  # Dwell 0: in scope, not counted
        r5 = self.row("BLDNRC-2024-00005")
        self.assertEqual((r5.match_method, r5.match_quality), ("unmatched", "none"))
        self.assertTrue(pd.isna(r5.tract_geoid))
        self.assertFalse(self.row("BLDRPR-2024-00006").in_scope)
        self.assertFalse(self.row("BLDRPR-2024-00007").in_scope)

    def test_contract_valid_and_hashed_keys(self):
        self.assertEqual(contracts.validate(self.obs, contracts.PERMITS_OBSERVED), [])
        self.assertFalse(self.obs["record_key"].str.startswith("BLD").any())
        self.assertEqual(len(self.obs), 5)

    def test_area_year(self):
        agg = pipeline.by_area_year(self.obs, "muni:5502548000")
        self.assertEqual(contracts.validate(agg, contracts.PERMITS_BY_AREA_YEAR), [])
        city = agg[agg.area_id == "muni:5502548000"].set_index("unit_category")["units"]
        self.assertEqual(int(city["other_residential"]), 2)
        tr = agg[agg.level == "tract"]
        self.assertTrue(tr["suppressed"].all())  # every tract count is below the threshold


if __name__ == "__main__":
    unittest.main()
