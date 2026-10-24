"""Comparison-city permits (Pleasant Prairie, Sun Prairie): parsing, personal-data removal,
unit calculation, parcel-number matching and the permit-history ADU-equivalent rule.
Offline; synthetic fixtures only (tests/fixtures/permits/comparison/)."""
import gzip
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from missing_middleware import contracts
from missing_middleware.permits import comparison as cmp
from missing_middleware.permits import pipeline, pleasant_prairie as pp, sun_prairie as sp
from missing_middleware.permits.base import STANDARD_COLUMNS

FIX = Path(__file__).parent / "fixtures" / "permits" / "comparison"


def _tmp_with(src: Path, name: str, gz: bool = True) -> Path:
    tmp = Path(tempfile.mkdtemp())
    data = src.read_bytes()
    (tmp / name).write_bytes(gzip.compress(data) if gz else data)
    return tmp


class TestPleasantPrairieParsing(unittest.TestCase):
    def setUp(self):
        self.tmp = _tmp_with(FIX / "pp_permits_fixture.rtf", "permits_issued_2025.rtf.gz")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_rtf_records_parse_all_fields(self):
        recs = pp.parse_rtf_records((FIX / "pp_permits_fixture.rtf").read_text(encoding="cp1252"))
        self.assertEqual([r["permit_id"] for r in recs], ["SF25-01-001", "RZ2025-01-001", "SF25-02-002", "SF25-03-003"])
        r = recs[0]
        self.assertEqual(r["permit_type"], "NEW SINGLE FAMILY DWELLING")  # double space in source collapsed
        self.assertEqual(r["issue_date"], "01/15/2025")
        self.assertEqual(r["parcel"], "91-4-122-000-0100")
        self.assertEqual(r["est_cost"], "400,000.00")
        self.assertTrue(r["owner_name"].startswith("TESTOWNER"))  # present in raw parse only

    def test_ingestion_drops_owner_contractor_and_name_prefix(self):
        df = pp.load_raw_permits(self.tmp)
        self.assertEqual(len(df), 4)
        flat = " ".join(str(v) for v in df.to_numpy().ravel())
        for s in ("TESTOWNER", "OWNER LANE", "CONTRACTOR RD", "ACME", "WRECKERS"):
            self.assertNotIn(s, flat)
        self.assertEqual(df.loc[0, "description"], "NSFR 2400 SF")
        self.assertTrue(df.loc[0, "description_prefix_removed"])
        self.assertTrue(set(STANDARD_COLUMNS) <= set(df.columns))

    def test_units_and_addresses(self):
        df = pp.load_raw_permits(self.tmp).set_index("permit_id")
        self.assertEqual(df.loc["SF25-01-001", "units_raw"], 1)
        self.assertEqual(df.loc["RZ2025-01-001", "units_raw"], -1)       # raze of a home
        self.assertEqual(df.loc["SF25-03-003", "units_basis"], "conversion_text")
        self.assertEqual(df.loc["SF25-02-002", "address_raw"], "400 102ND AVE")
        self.assertEqual(df.loc["SF25-02-002", "address_unit"], "73")  # mobile-home lot number
        self.assertEqual(df.loc["SF25-03-003", "address_raw"], "300 EXAMPLE CT")  # city KENOSHA stripped

    def test_unit_rules(self):
        self.assertEqual(pp.units_from_record("RAZING PERMIT", "Razing Detached Garage")[0], 0)
        self.assertEqual(pp.units_from_record("RAZING PERMIT", "RAZE PRINCIPAL & GARAGE")[0], -1)
        self.assertEqual(pp.units_from_record("NEW TWO FAMILY DWELLING", "")[0], 2)
        self.assertEqual(pp.units_from_record("SINGLE FAMILY ADDITION/ALTERATION", "768SF ADDITION(IN LAW)")[0], 1)
        self.assertEqual(pp.units_from_record("SINGLE FAMILY PLUMBING", "WISCONSIN LAWN SPRINKLER")[0], 0)
        self.assertEqual(pp.units_from_record("NEW MULTI-FAMILY BUILDING", "33 UNIT MF BLDG")[0], 33)

    def test_name_prefix_rule_keeps_work_text(self):
        self.assertEqual(pp.strip_name_prefix("NEWMAN (HOMEOWNER) 2200SF NSFR")[0], "2200SF NSFR")
        self.assertEqual(pp.strip_name_prefix("Install outlets (2) in kitchen")[1], False)
        self.assertEqual(pp.strip_name_prefix("(141') 4' High fence")[1], False)


class TestSunPrairieParsing(unittest.TestCase):
    def setUp(self):
        self.tmp = _tmp_with(FIX / "sp_querydata_fixture.json", "permits_submitted_2019.json.gz")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_dsr_decoding_repeat_null_and_literals(self):
        d = json.loads((FIX / "sp_querydata_fixture.json").read_text())
        rows = sp.decode_dsr(d["responses"][0]["results"][0]["result"]["data"]["dsr"]["DS"][0])
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[1][4], "C")          # status repeated from row 1
        self.assertEqual(rows[1][5], 200)
        self.assertIsNone(rows[2][3])              # parcel null bit
        self.assertEqual(rows[2][2], "Mother-in-law Suite, addition")  # literal, not a dictionary index
        self.assertEqual(rows[2][4], "W")

    def test_load_scrubs_names_and_classifies(self):
        df = sp.load_raw_permits(self.tmp).set_index("permit_id")
        flat = " ".join(str(v) for v in df.to_numpy().ravel())
        self.assertNotIn("TESTBUILDER", flat)
        self.assertEqual(df.loc["20190001", "record_kind"], "new_sf")
        self.assertEqual(df.loc["20190001", "units_raw"], 1)
        self.assertEqual(df.loc["20190002", "record_kind"], "existing_work")
        self.assertTrue(df.loc["20190003", "withdrawn"])
        self.assertEqual(df.loc["20190003", "units_raw"], 0)  # withdrawn submissions add nothing
        self.assertEqual(df.loc["20190001", "address_raw"], "100 EXAMPLE CT")

    def test_new_dwelling_text_rule(self):
        yes = ["SINGLE FAMILY NEW CONSTRUCTION", "Construct / Build a new single family detached home",
               "TWIN FAMILY HOME, NEW CONSTRUCTION", "New 2-flat home with detached garage"]
        no = ["New deck on single family home", "New Deck to existing house", "Basement finish in single family home",
              "Kitchen and bathroom remodeling, add new recessed lights throughout the house"]
        for d in yes:
            self.assertTrue(sp.is_new_dwelling_text(d), d)
        for d in no:
            self.assertFalse(sp.is_new_dwelling_text(d), d)
        mw = "MWOT - One and two-family homes Minor Work permit"
        self.assertEqual(sp.classify_record(mw, "Single Family Home")[0], "existing_work")
        self.assertEqual(sp.classify_record("DEMO - Demolition Permit", "Raze single family home")[0], "raze")


def history_fixture() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Synthetic Pleasant Prairie-style permit histories on eight parcels."""
    rows = [  # permit_id, type, description, date, parcel
        ("A1", "SINGLE FAMILY ROOFING/SIDING", "REROOF", "2010-05-01", "P1"),
        ("A2", "NEW SINGLE FAMILY DWELLING", "NSFR 900 SF", "2015-06-01", "P1"),         # second dwelling
        ("B1", "NEW SINGLE FAMILY DWELLING", "NSFR", "2015-06-01", "P2"),                # first on vacant lot
        ("C1", "SINGLE FAMILY ROOFING/SIDING", "REROOF", "2010-05-01", "P3"),
        ("C2", "RAZING PERMIT", "Razing Home", "2014-09-01", "P3"),
        ("C3", "NEW SINGLE FAMILY DWELLING", "NSFR", "2015-06-01", "P3"),                # teardown-rebuild
        ("D1", "SINGLE FAMILY ADDITION/ALTERATION", "Convert home to a duplex", "2016-03-01", "P4"),
        ("E1", "NEW SINGLE FAMILY DWELLING", "NSFR", "2012-04-01", "P5"),
        ("E2", "NEW SINGLE FAMILY DWELLING", "NSFR", "2013-04-01", "P5"),                # re-issue
        ("F1", "NEW MANUFACTURED HOME", "New Manufactured Home", "2011-01-01", "P6"),
        ("F2", "NEW MANUFACTURED HOME", "New Manufactured Home", "2012-01-01", "P6"),
        ("F3", "NEW MANUFACTURED HOME", "New Manufactured Home", "2013-01-01", "P6"),     # park
        ("G1", "SINGLE FAMILY HVAC", "FURNACE", "2010-05-01", "P7"),
        ("G2", "NEW SINGLE FAMILY DWELLING", "NSFR", "2016-06-01", "P7"),
        ("G3", "RAZING PERMIT", "RAZING 1200SF HOME", "2018-01-01", "P7"),              # old house razed later
        ("H1", "SINGLE FAMILY HVAC", "FURNACE", "2010-05-01", "P8"),
        ("H2", "NEW SINGLE FAMILY DWELLING", "NSFR", "2016-06-01", "P8"),                # commercial parcel
    ]
    raw = pd.DataFrame(rows, columns=["permit_id", "permit_type", "description", "issue_date", "parcel_key"])
    raw["issue_date"] = pd.to_datetime(raw["issue_date"])
    u = [pp.units_from_record(t, d) for t, d in zip(raw["permit_type"], raw["description"])]
    raw["units_raw"] = [x[0] for x in u]
    raw["units_basis"] = [x[1] for x in u]
    raw["use_class"] = raw["permit_type"]
    raw["address_raw"] = ""
    raw["est_cost"] = float("nan")
    raw["bldg_sqft"] = float("nan")
    raw["jurisdiction_id"] = pp.JURISDICTION_ID
    raw["source_id"] = pp.SOURCE_ID
    raw["source_file"] = "fixture"
    raw["source_row"] = range(len(raw))
    pids = [f"P{i}" for i in range(1, 9)]
    parcels = pd.DataFrame({"parcel_id": pids, "stateid": pids, "parcel_address": "", "house_nbr": range(1, 9),
                            "street_key": "EXAMPLE CT", "unit": "", "dwelling_units": float("nan"),
                            "property_class": ["1"] * 7 + ["2"], "property_use": None, "zoning": None,
                            "year_built": float("nan"), "x": -87.9, "y": 42.55})
    return raw, parcels


def fake_areas(xy: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({"tract_geoid": "55059002605", "bg_geoid": "550590026052"}, index=xy.index)


class TestPriorDwellingRule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw, parcels = history_fixture()
        a = pp.PleasantPrairieAdapter()
        full = pipeline.build_permits_observed(
            raw, None, parcels, parcels[["parcel_id", "x", "y"]], fake_areas, raze_types=a.raze_types,
            match_fn=cmp.parcel_match_fn(set(parcels["parcel_id"])), parcel_rule_fn=cmp.prior_dwelling_rule(a))
        full = cmp.recount(full)
        full["series"] = cmp.series_label(full)
        cls.full = full.set_index("permit_id")
        cls.obs = pipeline.to_contract(full, a.source_id, a.jurisdiction_id)

    def reason(self, pid):
        return self.full.loc[pid, "parcel_rule_reason"]

    def test_outcomes(self):
        self.assertEqual(self.full.loc["A2", "series"], "adu_equivalent:second_dwelling")
        self.assertEqual(self.full.loc["A2", "prior_evidence_permit"], "A1")
        self.assertEqual(self.reason("B1"), "no_prior_dwelling_evidence")
        self.assertEqual(self.full.loc["C3", "series"], "teardown_rebuild")
        self.assertEqual(self.full.loc["D1", "series"], "adu_equivalent:duplex_conversion")
        self.assertEqual(self.reason("E2"), "possible_reissue_of_earlier_dwelling_permit")
        self.assertEqual(self.reason("F3"), "multi_dwelling_site")
        self.assertEqual(self.reason("G2"), "teardown_rebuild_raze")  # raze 19 months after the new house
        self.assertEqual(self.reason("H2"), "host_not_residential")

    def test_match_and_contract(self):
        self.assertTrue((self.full["match_method"] == "parcel_id").all())
        self.assertEqual(contracts.validate(self.obs, contracts.PERMITS_OBSERVED), [])
        counted = self.full[self.full["counted"]]
        self.assertEqual(int(counted[counted["unit_category"] == "adu_equivalent"]["units_added"].sum()), 2)
        self.assertFalse(self.full.loc["C2", "in_scope"])  # razes are never counted

    def test_second_home_series(self):
        from missing_middleware.permits import second_homes

        f = second_homes.assign(self.full.reset_index()).set_index("permit_id")
        self.assertEqual(f.loc["A2", "second_home_component"], "second_dwelling")
        self.assertEqual(f.loc["D1", "second_home_component"], "sf_to_duplex")
        self.assertTrue(pd.isna(f.loc["C3", "second_home_component"]))  # teardown-rebuild is excluded
        self.assertEqual(int(f["second_home_units"].sum()), 2)

    def test_pleasant_prairie_likely_false_hits_leave_headline(self):
        j = pp.SECOND_HOME_JUDGMENTS
        self.assertIs(pp.PleasantPrairieAdapter.second_home_judgments, j)
        self.assertEqual(sorted(j), ["SF1710-020", "SF2110-077", "SF2203-055"])
        self.assertTrue(all(not v["counts"] and v["upper_bound"] for v in j.values()))

    def test_sun_prairie_reform_year_is_split(self):
        a = sp.SunPrairieAdapter()
        self.assertEqual(cmp.restrictive_periods(a, 2025), [("2025-01-01", "2025-12-31", True)])
        self.assertEqual(cmp.restrictive_periods(a, 2026), [("2026-01-01", "2026-05-04", True),
                                                            ("2026-05-05", "2026-12-31", False)])
        self.assertEqual(cmp.restrictive_periods(a, 2027), [("2027-01-01", "2027-12-31", False)])
        flag = cmp.restrictive_flag(a, pd.Series(pd.to_datetime(["2026-04-30", "2026-05-05", "2024-01-01"])))
        self.assertEqual(list(flag), [True, False, True])
        self.assertTrue(cmp.restrictive_flag(pp.PleasantPrairieAdapter(), pd.Series(["2026-09-01"])).all())

    def test_parcel_id_normalized_match(self):
        fn = cmp.parcel_match_fn({"91-4-122-000-0706"})
        m = fn(pd.DataFrame({"parcel_key": ["914122000 0706", "91-4-122-000-0706", None],
                             "address_raw": ["", "", ""]}))
        self.assertEqual(list(m["match_quality"]), ["probable", "confirmed", "none"])


if __name__ == "__main__":
    unittest.main()
