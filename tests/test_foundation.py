"""Offline tests for the statewide foundation parsers and aggregation logic.

Fixtures in tests/fixtures/foundation/ are tiny synthetic files in the exact
layout of the Census sources (headers copied from the real files).
"""
import io
import math
import tempfile
import unittest
import zipfile
from pathlib import Path

import pandas as pd

from missing_middleware import contracts
from missing_middleware.foundation import crosswalk, parsers, tables
from missing_middleware.foundation.geo import assign_muni_context, muni_type

FX = Path(__file__).parent / "fixtures" / "foundation"


class TestAcsSummaryFile(unittest.TestCase):
    def setUp(self):
        self.df = parsers.read_acs_sf(FX / "acs_b25024_tiny.dat")

    def test_keeps_only_wisconsin_whole_geographies(self):
        self.assertEqual(sorted(self.df["level"].value_counts().items()),
                         [("block_group", 4), ("county", 2), ("municipality", 3), ("state", 1), ("tract", 3)])
        self.assertNotIn("04000A0US55", set(self.df["geo_id"]))  # urban/rural component skipped
        self.assertNotIn("0400000US27", set(self.df["geo_id"]))
        self.assertEqual(self.df.loc[self.df["level"] == "municipality", "geoid"].str.len().unique().tolist(), [10])

    def test_place_level_only_on_request(self):
        p = parsers.read_acs_sf(FX / "acs_b25024_tiny.dat", sumlevels=("160",))
        self.assertEqual(p["geoid"].tolist(), ["5548000"])

    def test_special_moe_codes(self):
        d = parsers.read_acs_sf(FX / "acs_b01003_tiny.dat").set_index("geoid")
        self.assertEqual(d.loc["55", "B01003_M001"], 0.0)  # controlled -> 0
        self.assertTrue(d.loc["55", "B01003_M001_controlled"])
        self.assertTrue(math.isnan(d.loc["5500100200", "B01003_M001"]))  # other negative code -> null
        self.assertEqual(d.loc["5500100100", "B01003_E001"], 1200)


class TestInventory(unittest.TestCase):
    def setUp(self):
        self.inv = tables.build_inventory(parsers.read_acs_sf(FX / "acs_b25024_tiny.dat"))

    def test_contract_and_ids(self):
        self.assertEqual(contracts.validate(self.inv, contracts.INVENTORY), [])
        self.assertIn("muni:5500100100", set(self.inv["area_id"]))
        self.assertIn("550010001001", set(self.inv["area_id"]))
        st = self.inv[self.inv["level"] == "state"].iloc[0]
        self.assertEqual((st["homes_1unit_detached"], st["homes_1unit_detached_moe"]), (200, 5))
        self.assertTrue((self.inv["status"] == "observed").all())

    def test_additivity_exact(self):
        add = tables.check_additivity(self.inv)
        self.assertEqual(set(add["check"]), {"block_group->tract", "tract->county", "municipality->county", "county->state"})
        self.assertEqual(add["diff"].abs().sum(), 0)

    def test_additivity_detects_difference(self):
        inv = self.inv.copy()
        inv.loc[inv["area_id"] == "550010001001", "homes_1unit_detached"] += 3
        add = tables.check_additivity(inv)
        bad = add[(add["diff"] != 0) & (add["column"] == "homes_1unit_detached")]
        self.assertEqual(bad[["check", "parent_geoid", "diff"]].values.tolist(),
                         [["block_group->tract", "55001000100", 3.0]])


class TestAcsConditions(unittest.TestCase):
    def test_vacancy_and_mix(self):
        u = parsers.read_acs_sf(FX / "acs_b25024_tiny.dat")
        o = u[["geo_id", "geoid", "level", "sumlevel"]].copy()
        o["B25002_E001"], o["B25002_M001"] = 100.0, 10.0
        o["B25002_E002"], o["B25002_M002"] = 90.0, 8.0
        o["B25002_E003"], o["B25002_M003"] = 10.0, 4.0
        sc = tables.acs_conditions(u, o)
        self.assertEqual(contracts.validate(sc, contracts.STATE_CONDITIONS), [])
        vr = sc[(sc["indicator"] == "vacancy_rate") & (sc["area_id"] == "55")].iloc[0]
        self.assertAlmostEqual(vr["value"], 0.10)
        self.assertAlmostEqual(vr["moe"], math.sqrt(16 - 0.01 * 100) / 100)
        self.assertEqual(vr["status"], "calculated")
        two4 = sc[(sc["indicator"] == "units_2_4") & (sc["area_id"] == "55")].iloc[0]
        self.assertEqual(two4["value"], 80)  # 300 - 200 - 20 sits in line 004 in the fixture
        # tracts and block groups are not in state_conditions
        self.assertFalse(sc["area_id"].str.len().isin([11, 12]).any())

    def test_proportion_moe_falls_back_to_ratio(self):
        m = tables.proportion_moe([5], [1], [10], [10])  # under-root negative
        self.assertAlmostEqual(m.iloc[0], math.sqrt(1 + 0.25 * 100) / 10)

    def test_rss(self):
        self.assertAlmostEqual(tables.rss([3], [4]).iloc[0], 5.0)


class TestBps(unittest.TestCase):
    def test_place_file(self):
        p = parsers.read_bps(FX / "bps_place_tiny.txt", "place")
        self.assertEqual(len(p), 6)  # Minnesota row dropped
        a = p[p["bps_id"] == "000100"].iloc[0]
        self.assertEqual((a["year"], a["fips_mcd"], a["months_reported"]), (2025, "00100", 12))
        self.assertEqual((a["1unit_units"], a["2units_units"], a["5plus_units"], a["units_total"], a["units_2_4"]), (10, 2, 6, 18, 2))
        b = p[p["bps_id"] == "000200"].iloc[0]
        self.assertEqual((b["units_total"], b["units_total_rep"]), (4, 2))

    def test_county_and_state_files(self):
        c = parsers.read_bps(FX / "bps_county_tiny.txt", "county")
        self.assertEqual(c["county_fips"].tolist(), ["001", "003"])
        self.assertEqual(c["units_total"].sum(), 31)
        cov = tables.units_reported_share(c)
        self.assertAlmostEqual(cov.iloc[0], 21 / 23)
        s = parsers.read_bps(FX / "bps_state_tiny.txt", "state")
        self.assertEqual(s["name"].tolist(), ["Wisconsin"])
        self.assertEqual(s["year"].iloc[0], 2025)
        self.assertEqual(s["units_total"].iloc[0], 25569)  # published 2025 WI total

    def test_bps_conditions_rows(self):
        c = parsers.read_bps(FX / "bps_county_tiny.txt", "county")
        sc = tables.bps_conditions(c, "55" + c["county_fips"], "census_bps_county", tables.units_reported_share(c), "x")
        self.assertEqual(contracts.validate(sc, contracts.STATE_CONDITIONS), [])
        self.assertEqual(len(sc), 8)


class TestCrosswalk(unittest.TestCase):
    def setUp(self):
        self.bps = parsers.read_bps(FX / "bps_place_tiny.txt", "place")
        self.munis = pd.DataFrame([
            # area_id, geoid, cousubfp, county_geoid, muni_type, name, homes
            ("muni:5500100100", "5500100100", "00100", "55001", "city", "Alpha city", 70),
            ("muni:5500300100", "5500300100", "00100", "55003", "city", "Alpha city", 30),  # 2nd county piece
            ("muni:5500100200", "5500100200", "00200", "55001", "town", "Beta town", 50),
            ("muni:5500300300", "5500300300", "00300", "55003", "town", "Gamma town", 60),
            ("muni:5500300350", "5500300350", "00350", "55003", "town", "Zeta town", 20),
            ("muni:5500300400", "5500300400", "00400", "55003", "village", "Delta village", 20),
            ("muni:5500100560", "5500100560", "00560", "55001", "village", "Epsilon village", 10),
        ], columns=["area_id", "geoid", "cousubfp", "county_geoid", "muni_type", "name", "homes_1unit_detached"])
        self.xw = crosswalk.build_crosswalk(self.bps, self.munis)

    def test_match_types(self):
        t = self.xw.groupby("bps_id")["match_type"].first().to_dict()
        self.assertEqual(t, {"000100": "multi_county", "000200": "exact", "000300": "county_unincorporated",
                             "000400": "exact", "000500": "name_county", "000600": "unmatched"})

    def test_multi_county_shares_and_primary(self):
        a = self.xw[self.xw["bps_id"] == "000100"].set_index("wi_muni_id")
        self.assertAlmostEqual(a.loc["5500100100", "alloc_share"], 0.7)
        self.assertTrue(a.loc["5500100100", "is_primary_piece"])
        self.assertFalse(a.loc["5500300100", "is_primary_piece"])

    def test_county_unincorporated_links_towns_without_own_row(self):
        g = self.xw[self.xw["bps_id"] == "000300"]
        self.assertEqual(sorted(g["wi_muni_id"]), ["5500300300", "5500300350"])  # towns only, not the village
        self.assertAlmostEqual(g["alloc_share"].sum(), 1.0)

    def test_name_fallback(self):
        e = self.xw[self.xw["bps_id"] == "000500"].iloc[0]
        self.assertEqual(e["wi_muni_id"], "5500100560")
        self.assertIn("not in TIGER 2024", e["match_note"])

    def test_match_summary(self):
        s = crosswalk.match_summary(self.xw, self.bps, 2025)
        self.assertEqual(s["jurisdictions"], 6)
        self.assertEqual(s["by_type"]["unmatched"], 1)
        self.assertAlmostEqual(s["matched_to_municipality_pct"], round(100 * 4 / 6, 2))
        self.assertEqual(s["units_unmatched"], 0.0)

    def test_base_name(self):
        self.assertEqual(crosswalk.base_name("Greenville town"), "greenville")
        self.assertEqual(crosswalk.base_name("Fond du Lac"), "fond du lac")


class TestPepXlsx(unittest.TestCase):
    def _xlsx(self, path):
        ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
        shared = ["Wisconsin", "Geographic Area", ".Adams County, Wisconsin"]
        sst = f'<sst {ns}>' + "".join(f"<si><t>{s}</t></si>" for s in shared) + "</sst>"
        rows = [
            '<row r="1"><c r="A1" t="s"><v>1</v></c><c r="C1"><v>2020</v></c><c r="D1"><v>2021</v></c></row>',
            '<row r="2"><c r="A2" t="s"><v>0</v></c><c r="B2"><v>99</v></c><c r="C2"><v>100</v></c><c r="D2"><v>110</v></c></row>',
            '<row r="3"><c r="A3" t="s"><v>2</v></c><c r="B3"><v>9</v></c><c r="C3"><v>10</v></c><c r="D3"><v>11</v></c></row>',
        ]
        sheet = f'<worksheet {ns}><sheetData>' + "".join(rows) + "</sheetData></worksheet>"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("xl/sharedStrings.xml", sst)
            z.writestr("xl/worksheets/sheet1.xml", sheet)

    def test_parse_and_map(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "pep.xlsx"
            self._xlsx(p)
            pep = parsers.read_pep_housing_units(p)
        self.assertEqual(pep.values.tolist(), [["Wisconsin", 2020, 100.0], ["Wisconsin", 2021, 110.0],
                                              ["Adams County, Wisconsin", 2020, 10.0], ["Adams County, Wisconsin", 2021, 11.0]])
        sc, unmatched = tables.pep_conditions(pep, {"Adams County": "55001"})
        self.assertEqual(unmatched, [])
        self.assertEqual(sorted(sc["area_id"].unique()), ["55", "55001"])
        self.assertEqual(contracts.validate(sc, contracts.STATE_CONDITIONS), [])


class TestContextRule(unittest.TestCase):
    def test_rule(self):
        m = pd.DataFrame({
            "muni_type": ["city", "city", "village", "village", "town", "town", "not_defined"],
            "hu_total_whole": [30000, 30000, 2000, 2000, 1000, 1000, 0],
            "density_whole": [1500, 600, 900, 900, 50, 500, None],
            "density": [1500, 600, 900, 900, 50, 500, None],
            "metro": [True, True, True, False, True, True, False],
        })
        self.assertEqual(assign_muni_context(m).tolist(),
                         ["urban", "suburban", "suburban", "small_community", "rural", "suburban", None])

    def test_muni_type(self):
        self.assertEqual(muni_type("C5", "Madison city"), "city")
        self.assertEqual(muni_type("T1", "Madison town"), "town")
        self.assertEqual(muni_type("Z9", "County subdivisions not defined"), "not_defined")


if __name__ == "__main__":
    unittest.main()
