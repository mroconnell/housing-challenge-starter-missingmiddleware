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
from missing_middleware.foundation import build as fbuild, crosswalk, parsers, tables
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


def _bps_rows(rows):
    """Minimal BPS place frame: (year, bps_id, name, county_fips, fips_mcd, fips_place, units)."""
    d = pd.DataFrame(rows, columns=["year", "bps_id", "name", "county_fips", "fips_mcd", "fips_place", "units_total"])
    d["1unit_units"] = d["units_total"]
    return d


class TestCrosswalkBlankCodes(unittest.TestCase):
    """Review item B1: blank-MCD village rows, town->village changes, county rows, overlap years."""

    def setUp(self):
        self.munis = pd.DataFrame([
            ("muni:5501532790", "5501532790", "32790", "55015", "village", "Harrison village", 300),
            ("muni:5508732790", "5508732790", "32790", "55087", "village", "Harrison village", 100),
            ("muni:5501532800", "5501532800", "32800", "55015", "town", "Harrison town", 50),
            ("muni:5501514000", "5501514000", "14000", "55015", "town", "Charlestown town", 60),
            ("muni:5501588000", "5501588000", "88000", "55015", "town", "Woodville town", 40),
            ("muni:5507367320", "5507367320", "67320", "55073", "village", "Rib Mountain village", 80),
            ("muni:5507322025", "5507322025", "22025", "55073", "town", "Easton town", 30),
            ("muni:5505971163", "5505971163", "71163", "55059", "village", "Salem Lakes village", 90),
        ], columns=["area_id", "geoid", "cousubfp", "county_geoid", "muni_type", "name", "homes_1unit_detached"])
        self.bps = _bps_rows([
            # Harrison village: MCD blank 2015-2016 (place code given), coded from 2017
            (2015, "376700", "Harrison village", "015", "", "32790", 45),
            (2016, "376700", "Harrison village", "015", "", "32790", 165),
            (2017, "376700", "Harrison village", "015", "32790", "32790", 87),
            # Rib Mountain: town with old code, then MCD 00000 and an unknown place code as a village
            (2016, "729500", "Rib Mountain town", "073", "67325", "00000", 7),
            (2017, "729500", "Rib Mountain village", "073", "00000", "67325", 13),
            # Silver Lake village merged into Salem Lakes
            (2016, "801000", "Silver Lake village", "059", "74025", "74025", 2),
            # county rows
            (2015, "150100", "Calumet County Part Unincorporated Area", "015", "00000", "99990", 10),
            (2016, "150100", "Calumet County Part Unincorporated Area", "015", "00000", "99990", 12),
            (2017, "150100", "Calumet County Part Unincorporated Area", "015", "00000", "99990", 14),
            (2017, "730100", "Marathon County Part Unincorporated Area", "073", "00000", "99990", 5),
            # Charlestown town reports on its own in 2016 only
            (2016, "160000", "Charlestown town", "015", "14000", "00000", 1),
        ])
        self.xw = crosswalk.build_crosswalk(self.bps, self.munis)

    def _ident(self, bps_id, mcd):
        return self.xw[(self.xw["bps_id"] == bps_id) & (self.xw["fips_mcd"] == mcd)]

    def test_blank_mcd_village_is_not_a_county_row(self):
        h = self._ident("376700", "")
        self.assertEqual(set(h["match_type"]), {"place_code"})
        self.assertEqual(sorted(h["wi_muni_id"]), ["5501532790", "5508732790"])  # both county pieces of the village
        self.assertTrue(h.set_index("wi_muni_id").loc["5501532790", "is_primary_piece"])
        self.assertEqual(set(self._ident("376700", "32790")["match_type"]), {"multi_county"})

    def test_town_to_village_by_name(self):
        old = self._ident("729500", "67325")
        new = self._ident("729500", "00000")
        self.assertEqual(old["wi_muni_id"].tolist(), ["5507367320"])
        self.assertEqual(new["wi_muni_id"].tolist(), ["5507367320"])
        self.assertEqual(set(old["match_type"]) | set(new["match_type"]), {"name_county"})

    def test_merged_place_alias(self):
        s = self.xw[self.xw["bps_id"] == "801000"].iloc[0]
        self.assertEqual((s["match_type"], s["wi_muni_id"]), ("name_alias", "5505971163"))

    def test_county_rows_only_by_name_and_only_towns_without_own_row(self):
        c = self.xw[self.xw["match_type"] == "county_unincorporated"]
        self.assertTrue(c["bps_name"].map(crosswalk.is_county_row).all())
        self.assertTrue(c["bps_name"].str.contains("County").all())
        cal = c[c["bps_id"] == "150100"].set_index("wi_muni_id")
        # villages never get county-row permits; Charlestown is covered in 2015 and 2017 only
        self.assertEqual(sorted(cal.index), ["5501514000", "5501532800", "5501588000"])
        self.assertEqual(cal.loc["5501514000", "county_years_covered"], "2015;2017")
        self.assertTrue(cal.loc["5501514000", "town_has_own_row_some_years"])
        # Rib Mountain's own rows mean Marathon's county row covers only Easton
        self.assertEqual(c[c["bps_id"] == "730100"]["wi_muni_id"].tolist(), ["5507322025"])

    def test_county_allocation_per_year(self):
        a = crosswalk.county_unincorporated_allocation(self.xw, self.bps, self.munis)
        a16 = a[(a["bps_id"] == "150100") & (a["year"] == 2016)].set_index("area_id")
        self.assertNotIn("muni:5501514000", a16.index)  # Charlestown has its own row in 2016
        self.assertAlmostEqual(a16.loc["muni:5501532800", "alloc_share"], 50 / 90)
        self.assertAlmostEqual(a16["allocated_units_total"].sum(), 12)
        for _, g in a.groupby(["bps_id", "year"]):
            self.assertAlmostEqual(g["alloc_share"].sum(), 1.0)
        self.assertTrue((a["status"] == "assumed").all())

    def test_is_county_row(self):
        self.assertTrue(crosswalk.is_county_row("Waukesha County Part Unincorporated Area"))
        self.assertFalse(crosswalk.is_county_row("Harrison village"))


class TestKnownBpsGaps(unittest.TestCase):
    """Review item S2: Milwaukee multifamily years are nulled, not replaced; totals footnoted."""

    def test_gap_rows(self):
        rows = []
        for aid, src in (("muni:5507953000", "census_bps_place"), ("55079", "census_bps_county"), ("55", "census_bps_state")):
            for y in (2023, 2024):
                for ind, v in (("permitted_units_total", 97.0), ("permitted_units_1unit", 61.0), ("permitted_units_5plus", 0.0)):
                    rows.append(dict(area_id=aid, year=y, indicator=ind, value=v, source_id=src, coverage_basis="x",
                                     geography_note=""))
        sc = pd.DataFrame(rows)
        xw = pd.DataFrame([dict(bps_id="572000", area_id="muni:5507953000", is_primary_piece=True)])
        out = fbuild.apply_known_bps_gaps(sc, xw)
        mke = out[(out["area_id"] == "muni:5507953000") & (out["year"] == 2023)].set_index("indicator")
        self.assertTrue(math.isnan(mke.loc["permitted_units_total", "value"]))
        self.assertEqual(mke.loc["permitted_units_total", "value_as_published"], 97.0)
        self.assertEqual(mke.loc["permitted_units_5plus", "missing_reason"], "not_reported")
        self.assertEqual(mke.loc["permitted_units_1unit", "value"], 61.0)  # one-unit series kept
        self.assertIsNone(mke.loc["permitted_units_1unit", "missing_reason"])
        ok24 = out[(out["area_id"] == "muni:5507953000") & (out["year"] == 2024)]
        self.assertFalse(ok24["value"].isna().any())
        cty = out[(out["area_id"] == "55079") & (out["year"] == 2023) & (out["indicator"] == "permitted_units_total")].iloc[0]
        self.assertEqual(cty["value"], 97.0)  # published county total kept, with a footnote
        self.assertIn("lower bound", cty["geography_note"])
        self.assertEqual(contracts.validate(out.assign(moe=None, period_type="annual", status="observed",
                                                       source_vintage="v"), contracts.STATE_CONDITIONS), [])


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
    def _m(self, rows):
        return pd.DataFrame(rows, columns=["muni_type", "hu_total_whole", "density_whole", "metro_main", "largest_in_county"])

    def test_rule(self):
        m = self._m([
            ("city", 30000, 1500, True, True),     # big city -> urban
            ("city", 23000, 1800, True, False),    # big inner suburb (Wauwatosa) -> urban by size
            ("city", 12776, 349, True, True),      # Superior: regional city, largest in county -> urban
            ("city", 11614, 671, False, True),     # Stevens Point (micro county) -> urban
            ("city", 10078, 218, True, True),      # Mequon: largest in county but too sparse -> suburban
            ("village", 10499, 232, True, False),  # Caledonia: big metro village -> suburban by size
            ("village", 2000, 900, True, False),   # small dense metro village -> suburban by density
            ("village", 2000, 300, True, False),   # small sparse metro village -> small_community
            ("city", 9722, 704, False, True),      # Marshfield (non-metro, under 10,000) -> small_community
            ("town", 11192, 501, True, False),     # Grand Chute town -> suburban by density
            ("town", 4049, 146, True, False),      # big sparse metro town -> rural (no size route for towns)
            ("town", 1000, 50, False, False),
            ("not_defined", 0, None, False, False),
        ])
        self.assertEqual(assign_muni_context(m).tolist(),
                         ["urban", "urban", "urban", "urban", "suburban", "suburban", "suburban", "small_community",
                          "small_community", "suburban", "rural", "rural", None])

    def test_muni_type(self):
        self.assertEqual(muni_type("C5", "Madison city"), "city")
        self.assertEqual(muni_type("T1", "Madison town"), "town")
        self.assertEqual(muni_type("Z9", "County subdivisions not defined"), "not_defined")


if __name__ == "__main__":
    unittest.main()
