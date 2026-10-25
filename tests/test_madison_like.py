"""Madison-like cities (missing_middleware/comparison/madison_like.py).
Offline; tiny synthetic fixtures in tests/fixtures/madison_like/, plus consistency checks on the
committed reference/madison_like_*.csv aggregates."""
import tempfile
import unittest
import zipfile
from pathlib import Path

import pandas as pd

from missing_middleware.comparison import madison_like as ml

FIX = Path(__file__).parent / "fixtures" / "madison_like"
REF = Path(__file__).resolve().parent.parent / "reference"


class TestScreen(unittest.TestCase):
    def setUp(self):
        places = ml.read_place_codes([FIX / "places.txt"])
        pre = ("1600000US53", "1600000US41")
        homes = ml.read_acs_values(FIX / "b25024.dat", "B25024_E002", pre)
        value = ml.read_acs_values(FIX / "b25077.dat", "B25077_E001", pre)
        self.s = ml.screen(places, homes, value).set_index("name")

    def test_rule(self):
        like = set(self.s.index[self.s["madison_like"]])
        self.assertEqual(like, {"Midtown", "Edge"})  # Edge sits exactly on both upper bounds (inclusive)

    def test_reasons_and_cdp_excluded(self):
        self.assertNotIn("Bigsprawl", self.s.index)
        self.assertIn("largest_city", self.s.loc["Seattle", "fail_reason"])
        self.assertEqual(self.s.loc["Richville", "fail_reason"], "value")
        self.assertEqual(self.s.loc["Tiny", "fail_reason"], "size")


class TestDlcd(unittest.TestCase):
    def test_parse_with_check(self):
        txt = (FIX / "dlcd_2019.txt").read_text()
        self.assertEqual(ml.dlcd_year(txt), 2019)
        self.assertEqual(ml.dlcd_adu_permitted(txt, "Eugene"), (10.0, "sf_total_check_ok"))
        v, chk = ml.dlcd_adu_permitted(txt, "Gresham")
        self.assertTrue(pd.isna(v))
        self.assertEqual(chk, "row_incomplete_or_check_failed")
        self.assertEqual(ml.dlcd_adu_permitted(txt, "Salem")[1], "city_not_reported")


class TestXlsx(unittest.TestCase):
    def test_reader_and_ofm(self):
        ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
        heads = ["County Name", "City Name", "Estimate Year", ml.OFM_SFD_COL, ml.OFM_ADU_COL]
        sst = "".join(f"<si><t>{h}</t></si>" for h in heads + ["Spokane", "Pierce", "Tacoma"])
        def cell(ref, v, s=False):
            return f'<c r="{ref}" t="s"><v>{v}</v></c>' if s else f'<c r="{ref}"><v>{v}</v></c>'
        rows = ['<row r="1">' + "".join(cell(f"{c}1", i, True) for i, c in enumerate("ABCDE")) + "</row>",
                '<row r="2">' + cell("A2", 5, True) + cell("B2", 5, True) + cell("C2", 2024) + cell("D2", 300) + cell("E2", 24) + "</row>",
                '<row r="3">' + cell("A3", 6, True) + cell("B3", 7, True) + cell("C3", 2024) + cell("D3", 200) + "</row>"]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.xlsx"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("xl/sharedStrings.xml", f"<sst {ns}>{sst}</sst>")
                z.writestr("xl/worksheets/sheet1.xml", f"<worksheet {ns}><sheetData>{''.join(rows)}</sheetData></worksheet>")
            got = ml.read_xlsx_sheet(p, "xl/worksheets/sheet1.xml")
        self.assertEqual(got[0], heads)
        df = ml.ofm_city_counts(got, ["Spokane", "Tacoma"]).set_index("city")
        self.assertEqual(df.loc["Spokane", "adu_permits"], 24)
        self.assertTrue(pd.isna(df.loc["Tacoma", "adu_permits"]))  # blank is missing, not zero


class TestPathsAndVerdict(unittest.TestCase):
    def rates(self, vals):
        rows = []
        for i, path in enumerate(vals):
            for y, r in enumerate(path, start=1):
                rows.append(dict(geo_id=f"g{i}", state="WA", year=2023 + y, adu_permits=r * 10, homes=10_000,
                                 rate_per_1000=r, year_since_law=y))
        return pd.DataFrame(rows)

    def test_year_coding(self):
        a = pd.DataFrame(dict(geo_id=["x", "x", "y"], state=["WA", "OR", "CA"], year=[2026, 2018, 2018],
                              adu_permits=[10.0, 5.0, 1.0]))
        r = ml.add_rates(a, {"x": 10_000, "y": 1_000})
        self.assertEqual(r["year_since_law"].tolist(), [3, 0, 2])
        self.assertAlmostEqual(r["rate_per_1000"].iloc[0], 1.0)

    def test_median_and_pooled(self):
        p = ml.median_path(self.rates([[0.2, 0.4], [1.0, 2.0], [0.6, 0.6]]), "t")
        self.assertAlmostEqual(p.loc[0, "median_rate"], 0.6)
        self.assertAlmostEqual(p.loc[1, "pooled_rate"], (4 + 20 + 6) / 30_000 * 1000)
        self.assertEqual(p["model_typical_state"].tolist(), [0.83, 1.03])

    def test_verdicts(self):
        self.assertEqual(ml.verdict(ml.median_path(self.rates([[0.5, 0.6, 0.7]] * 5), "t"))[0], "contradicts")
        self.assertEqual(ml.verdict(ml.median_path(self.rates([[0.9, 1.1, 1.2]] * 5), "t"))[0], "supports")
        self.assertEqual(ml.verdict(ml.median_path(self.rates([[0.9, 1.1, 1.2]] * 4), "t"))[0], "cannot_yet_test")
        self.assertEqual(ml.verdict(ml.median_path(self.rates([[0.9, 0.9, 0.9]] * 5), "t"))[0], "cannot_yet_test")


class TestNewHouseShare(unittest.TestCase):
    def test_apn_match(self):
        rows = pd.read_csv(FIX / "hcd_rows.csv", dtype={"apn": str})
        s0 = ml.apr_new_house_share(rows, 0).set_index("juris_name")
        s1 = ml.apr_new_house_share(rows, 1).set_index("juris_name")
        self.assertEqual(s0.loc["A", "adu_units"], 4)
        self.assertEqual(s0.loc["A", "adu_units_blank_apn"], 1)
        self.assertEqual(s0.loc["A", "adu_units_with_new_house"], 1)  # 111-222 == 111222, same year
        self.assertEqual(s1.loc["A", "adu_units_with_new_house"], 3)  # 333 matches SFD a year later
        self.assertFalse(s0.loc["A", "subdivision_driven"])
        self.assertTrue(s0.loc["B", "subdivision_driven"])

    def test_other_cities(self):
        a = pd.DataFrame(dict(city=["seattle", "seattle", "denver"], year=[2021, 2020, 2023],
                              adu_units=[60, 999, 10], excluded_with_new_house=[40, 999, 0]))
        o = ml.other_cities_new_house(a, {"seattle": (2021, 2024), "denver": (2023, 2025)}).set_index("city")
        self.assertAlmostEqual(o.loc["seattle", "share_with_new_house"], 0.4)
        self.assertTrue(o.loc["seattle", "condo_driven"])
        self.assertFalse(o.loc["denver", "condo_driven"])


class TestLotSplit(unittest.TestCase):
    def test_classify_lot(self):
        new = pd.DataFrame(dict(date=["2020-06-01", "2020-06-01", "2020-06-01", "2016-01-01", "2020-06-01", "2020-06-01"],
                                parcel=["P-1", "P2", "", "P1", "P9", "P8"],
                                addr=["", "", "12 Main Street", "", "", ""],
                                dem_units=[0, 0, 0, 0, 0, 1]))
        demos = pd.DataFrame(dict(date=["2019-01-01", "2015-01-01", "2020-01-01"], parcel=["P1", "P2", ""],
                                  addr=["", "", "12 MAIN ST"]))
        got = ml.classify_lot(new, demos, pd.Timestamp("2015-01-01")).tolist()
        # P1: demo 17 months before -> teardown; P2: demo 5 years before -> vacant; address match ->
        # teardown; 2016 permit whose 2-year look-back starts before the demo data -> unclassified;
        # P9 no demo -> vacant; P8 reports a demolished unit itself -> teardown
        self.assertEqual(got, ["teardown", "vacant", "teardown", "unclassified", "vacant", "teardown"])

    def test_reform_compare(self):
        ser = pd.DataFrame(dict(year=[2018, 2019, 2020, 2021], vacant_new_house_adus=[1, 1, 4, 6],
                                vacant_new_houses=[100, 100, 100, 100], had_home_adus=[10, 10, 30, 30],
                                homes=[10_000] * 4))
        r = ml.reform_compare(ser, (2018, 2019), (2020, 2021))
        self.assertAlmostEqual(r["before_a_per_100"], 1.0)
        self.assertAlmostEqual(r["after_a_per_100"], 5.0)
        self.assertAlmostEqual(r["ratio_b"], 3.0)


class TestCommittedOutputs(unittest.TestCase):
    def test_cities(self):
        c = pd.read_csv(REF / "madison_like_cities.csv")
        self.assertTrue(c["homes"].between(ml.HOMES_MIN, ml.HOMES_MAX).all())
        self.assertTrue(c["median_value"].between(ml.VALUE_MIN, ml.VALUE_MAX).all())
        self.assertFalse(c["city"].isin(["Seattle", "Portland", "Los Angeles", "Providence"]).any())
        self.assertEqual(set(c["state"]), {"WA", "OR", "RI", "CA"})

    def test_share_flags(self):
        s = pd.read_csv(REF / "madison_like_new_house_share.csv")
        flagged = set(s.loc[s["outlier"], "city"])
        self.assertTrue({"seattle", "austin"} <= flagged)
        summ = pd.read_csv(REF / "madison_like_new_house_share_summary.csv")
        main = summ[summ["set"].str.startswith("main: ")].iloc[0]
        self.assertNotIn("seattle", main["cities"].split(";"))
        self.assertNotIn("austin", main["cities"].split(";"))


if __name__ == "__main__":
    unittest.main()
