"""Permit pipeline: ingestion drops owner fields, dedupe, address parsing, matching,
text + parcel classification, contract output. Offline; synthetic fixtures only."""
import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from missing_middleware import contracts
from missing_middleware.permits import address, classify, madison, pipeline, report, second_homes
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


class TestAduEquivalentRule(unittest.TestCase):
    """Host must have been one unit; Dwell-0 SF->two-unit conversions; bundles and judged
    false positives held out (review item S3)."""

    @classmethod
    def setUpClass(cls):
        raw = load_fixture_raw()
        base = raw[raw.permit_id == "BLDNRC-2024-00003"].iloc[0]
        extra = [  # permit_id, address, units, description
            ("BLDNCC-2024-00010", "300 EXAMPLE ST", 1, "CONVERT FROM TWO APARTMENTS TO THREE APARTMENTS"),
            ("BLDRPR-2024-00011", "302 EXAMPLE ST", 0, "CONVERT SINGLE FAMILY HOME TO 2 UNIT"),
            ("BLDRPR-2024-00012", "304 EXAMPLE ST", 0, "CONVERT SINGLE FAMILY TO TWO UNIT, ADD DOOR"),
            ("BLDNRC-2024-00013", "304 EXAMPLE ST", 1, "ADDITION TO CONVERT SINGLE FAMILY TO DUPLEX"),
            ("BLDNRC-2024-00014", "306 EXAMPLE ST", 2, "NEW TWIN HOME ADU"),
            ("BLDNRC-2024-00015", "308 EXAMPLE ST", 1, "SF HOME FROM SF HOME W/DEPENDENCY LIVING ARRANGEMENT"),
        ]
        rows = []
        for i, (pid, addr, units, desc) in enumerate(extra):
            r = base.copy()
            r["permit_id"], r["address_raw"], r["units_raw"], r["description"] = pid, addr, units, desc
            r["permit_type"], r["source_row"] = pid[:6], 100 + i
            rows.append(r)
        raw = pd.concat([raw, pd.DataFrame(rows)], ignore_index=True)
        p = fixture_parcels()
        add = pd.DataFrame([  # parcels as the assessor shows them today (after the permit)
            ("P300", 300, "EXAMPLE ST", 3, 1920, "3 Unit", -89.41, 43.07),
            ("P302", 302, "EXAMPLE ST", 2, 1915, "2 Unit", -89.41, 43.07),
            ("P304", 304, "EXAMPLE ST", 2, 1915, "2 Unit", -89.41, 43.07),
            ("P306", 306, "EXAMPLE ST", 1, 1954, "Single family", -89.41, 43.07),
            ("P308", 308, "EXAMPLE ST", 1, 1950, "Single family", -89.41, 43.07),
        ], columns=["parcel_id", "house_nbr", "street_key", "dwelling_units", "year_built", "property_use", "x", "y"])
        add["parcel_address"] = add["house_nbr"].astype(str) + " " + add["street_key"].str.title()
        add["unit"], add["property_class"], add["zoning"] = "", "Residential", "TR-C2"
        p = pd.concat([p, add], ignore_index=True)
        cls.full = pipeline.build_permits_observed(
            raw, fixture_index(p), p, p[["parcel_id", "x", "y"]], fake_areas,
            host_uses=madison.MadisonAdapter.host_uses, dwell0_conversions=True,
            exclude_parcel_rule={"BLDNRC-2024-00015": "judged false positive"})

    def row(self, pid):
        return self.full[self.full.permit_id == pid].iloc[0]

    def test_multi_unit_host_excluded(self):
        r = self.row("BLDNCC-2024-00010")
        self.assertEqual((r.unit_category, r.parcel_rule_reason), ("other_residential", "host_not_one_unit_residential"))

    def test_dwell0_conversion_counted_once(self):
        r = self.row("BLDRPR-2024-00011")
        self.assertEqual((r.unit_category, r.units_added, r.adu_eq_series), ("adu_equivalent", 1, "duplex_conversion"))
        self.assertTrue(r.units_from_text and r.counted)
        dup = self.row("BLDRPR-2024-00012")  # same parcel already has a Dwell-1 conversion permit
        self.assertEqual(dup.parcel_rule_reason, "conversion_already_permitted")
        self.assertFalse(dup.in_scope)
        self.assertEqual(dup.units_added, 0)
        self.assertEqual(self.row("BLDNRC-2024-00013").unit_category, "adu_equivalent")

    def test_bundle_and_false_positive_held_out(self):
        b = self.row("BLDNRC-2024-00014")
        self.assertEqual((b.unit_category, b.parcel_rule_reason), ("other_residential", "adu_bundle_held_for_review"))
        fp = self.row("BLDNRC-2024-00015")
        self.assertEqual(fp.parcel_rule_reason, "judged_false_positive")
        self.assertFalse(fp.counted)


class TestSecondHomes(unittest.TestCase):
    """AQ-032 headline: second homes on single-family lots, components, judgments."""

    @classmethod
    def setUpClass(cls):
        TestAduEquivalentRule.setUpClass()
        full = TestAduEquivalentRule.full.copy()
        # a counted legalization (excluded from the headline) and a second judged bundle
        leg = full[full.permit_id == "BLDNRC-2024-00001"].copy()
        leg["permit_id"], leg["unit_category"] = "BLDNRC-2024-00090", "adu_legalization"
        full = pd.concat([full, leg], ignore_index=True)
        cls.before = full.copy()
        judgments = {
            "BLDNRC-2024-00014": {"counts": True, "units": 2, "component": "adu_two_unit",
                                  "judgment": "added_beside_existing_home", "evidence": "1954 host"},
            "BLDNRC-2024-00003": {"counts": False, "units": 0, "component": None,
                                  "judgment": "new_construction_cleared_lot", "evidence": "new house"},
        }
        cls.full = second_homes.assign(full, judgments).set_index("permit_id")

    def test_components(self):
        f = self.full
        self.assertEqual(f.loc["BLDNRC-2024-00001", "second_home_component"], "adu_detached")
        self.assertEqual(f.loc["BLDNRC-2024-00013", "second_home_component"], "sf_to_duplex")
        self.assertEqual(f.loc["BLDRPR-2024-00011", "second_home_component"], "sf_to_duplex")  # Dwell-0 path
        self.assertTrue(pd.isna(f.loc["BLDNRC-2024-00090", "second_home_component"]))  # legalization
        self.assertEqual(f.loc["BLDNRC-2024-00090", "second_home_note"], "excluded:legalization")
        self.assertTrue(pd.isna(f.loc["BLDNRC-2024-00015", "second_home_component"]))  # judged false positive

    def test_judgments_resolve_bundles_without_changing_categories(self):
        b = self.full.loc["BLDNRC-2024-00014"]
        self.assertEqual((b.second_home_component, b.second_home_units), ("adu_two_unit", 2))
        self.assertEqual(b.unit_category, "other_residential")  # category columns are unchanged
        self.assertEqual(b.second_home_note, "judged:added_beside_existing_home")
        n = self.full.loc["BLDNRC-2024-00003"]
        self.assertTrue(pd.isna(n.second_home_component))
        self.assertEqual(n.second_home_units, 0)
        before = self.before.set_index("permit_id").loc[self.full.index, "unit_category"]
        self.assertTrue(self.full["unit_category"].fillna("-").equals(before.fillna("-")))

    def test_by_year_and_reference_rows(self):
        f = self.full.reset_index()
        y = second_homes.by_year(f, [2024]).iloc[0]
        comps = sum(int(y[c]) for c in second_homes.COMPONENTS)
        self.assertEqual(int(y[second_homes.HEADLINE]), comps)
        self.assertEqual(int(y["adu_two_unit"]), 2)
        ref = report.reference_by_year(f)
        head = ref[(ref.year == 2024) & (ref.category == second_homes.HEADLINE)].iloc[0]
        self.assertEqual(int(head["units"]), int(y[second_homes.HEADLINE]))
        self.assertEqual(ref[ref.category == "adu_detached"]["units"].sum(),
                         report.reference_by_year(self.before)[lambda d: d.category == "adu_detached"]["units"].sum())

    def test_unknown_component_rejected(self):
        with self.assertRaises(ValueError):
            second_homes.assign(self.before, {"BLDNRC-2024-00014": {"counts": True, "units": 1, "component": "x",
                                                                    "judgment": "j", "evidence": ""}})

    def test_madison_judgments_cover_the_held_bundles(self):
        j = madison.SECOND_HOME_JUDGMENTS
        self.assertIs(madison.MadisonAdapter.second_home_judgments, j)
        bundles = [p for p, v in j.items() if v["component"] == "adu_two_unit" or p == "BLDNRC-2022-06192"]
        self.assertEqual(len(bundles), 10)
        self.assertFalse(j["BLDNRC-2022-06192"]["counts"])
        for p, v in j.items():
            self.assertNotRegex(v["evidence"], r"\b\d{12}\b", p)  # no parcel numbers in committed text


if __name__ == "__main__":
    unittest.main()
