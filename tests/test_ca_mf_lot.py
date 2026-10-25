"""Offline tests for missing_middleware.comparison.ca_mf_lot on synthetic fixtures (no network).

The fixture tests/fixtures/ca_mf_lot/apr_a2_mf_tiny.csv is a synthetic Table A2 with made-up
APNs (999...), built to exercise each rule: APN-year bands before and after the cutoff, the
cumulative benchmark cap, the unit-category flag, placeholder APNs, text exclusions and dates.
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from missing_middleware.comparison import ca_mf_lot as M  # noqa: E402

FX = ROOT / "tests/fixtures/ca_mf_lot"


def rows_frame(recs):
    df = pd.DataFrame(recs, columns=["juris_name", "year", "apn", "units", "issue_date"])
    df["cnty_name"] = "Testcounty"
    df["issue_date"] = pd.to_datetime(df["issue_date"])
    df["permit_key"] = [f"k{i}" for i in range(len(df))]
    df["apn"] = df["apn"].astype(object).where(df["apn"].notna(), None)
    return df


class TestNormalizeApn(unittest.TestCase):
    def test_placeholders_and_formats(self):
        s = pd.Series(["123-456-7890", "123 456 7890", "0", "", None, "TBD", "0000000000", "999999", "12ab-34", "JADU"])
        out = M.normalize_apn(s)
        self.assertEqual(out[0], "1234567890")
        self.assertEqual(out[1], "1234567890")
        self.assertTrue(out[2:9].drop(index=8).isna().all())
        self.assertEqual(out[8], "12AB34")
        self.assertTrue(pd.isna(out[9]))


class TestRules(unittest.TestCase):
    def setUp(self):
        self.rows = rows_frame([
            ("A", 2021, "X", 1, "2021-01-05"), ("A", 2021, "X", 1, "2021-02-05"), ("A", 2021, "X", 1, "2021-03-05"),
            ("A", 2021, "Y", 2, "2021-04-05"),
            ("A", 2023, "X", 1, "2023-01-05"),
            ("A", 2023, "W", 3, "2023-02-05"),
            ("A", 2023, "V", 4, "2023-02-05"),
            ("A", 2023, None, 1, "2023-03-05"),
            ("B", 2021, "X", 1, "2021-01-05"),
        ])

    def test_band_by_cutoff(self):
        b = M.apn_year_band(self.rows, pd.Timestamp("2023-01-01"))
        self.assertEqual(b.loc[0, "band"], "definite")      # 3 in 2021: definite before the cutoff
        self.assertEqual(b.loc[3, "band"], "possible")      # 2 in 2021: possible before the cutoff
        self.assertEqual(b.loc[4, "band"], "single")        # 1 in 2023
        self.assertEqual(b.loc[5, "band"], "possible")      # 3 in 2023: ambiguous after the cutoff
        self.assertEqual(b.loc[6, "band"], "definite")      # 4 in 2023
        self.assertEqual(b.loc[7, "band"], "unknown_apn")
        self.assertEqual(b.loc[8, "band"], "single")        # same APN, other jurisdiction
        b21 = M.apn_year_band(self.rows, pd.Timestamp("2021-01-01"))
        self.assertEqual(b21.loc[0, "band"], "possible")    # 3 in 2021 under a 2021 cutoff
        self.assertEqual(b21.loc[3, "band"], "single")

    def test_order_and_cap_cumulate_across_years(self):
        o = M.add_order(self.rows)
        x = o[(o["juris_name"] == "A") & (o["apn"] == "X")].sort_values(["year", "issue_date"])
        self.assertEqual(x["u_order1"].tolist(), [1, 0, 0, 0])
        self.assertEqual(x["u_order2"].tolist(), [0, 1, 0, 0])
        self.assertEqual(x["u_order3p"].tolist(), [0, 0, 1, 1])
        self.assertEqual(x["u_order3"].tolist(), [0, 0, 1, 0])
        self.assertEqual(x["cap_removed"].tolist(), [0, 0, 1, 1])  # the 2023 ADU is the 4th: removed
        w = o.loc[5]
        self.assertEqual((w["u_order1"], w["u_order2"], w["u_order3p"], w["cap_kept"]), (1, 1, 1, 2))
        v = o.loc[6]
        self.assertEqual((v["u_order3"], v["u_order4p"], v["cap_removed"]), (1, 1, 2))
        self.assertEqual(o.loc[7, "cap_kept"], 1)   # unknown APN cannot be capped
        self.assertEqual(o.loc[8, "cap_removed"], 0)
        self.assertEqual(float(o["units"].sum()), float((o["cap_kept"] + o["cap_removed"]).sum()))
        np.testing.assert_allclose(o["u_order1"] + o["u_order2"] + o["u_order3p"], o["units"])

    def test_summarize_bounds(self):
        r = M.annotate(self.rows, {("A", "V")}, M.MAIN_CUTOFF)
        s = M.summarize(r, ["year"]).set_index("year")
        self.assertEqual(s.loc[2021, "adu_units"], 6)
        self.assertEqual(s.loc[2021, "units_lower_definite"], 3)
        self.assertEqual(s.loc[2021, "units_upper_definite_plus_possible"], 5)
        self.assertEqual(s.loc[2023, "units_unitcat_mf"], 4)
        self.assertEqual(s.loc[2023, "units_cap_removed"], 1 + 1 + 2)
        # cap + MF lower removes the cap units plus kept units on definite APNs (V: 2 kept)
        self.assertEqual(s.loc[2023, "units_cap_plus_mf_lower_removed"], 4 + 2)
        self.assertEqual(s.loc[2023, "units_cap_plus_mf_upper_removed"], 4 + 2 + 2)  # + W's 2 kept (possible)
        self.assertLessEqual(s["units_lower_definite"].max(), s["units_upper_definite_plus_possible"].max())


class TestReadFixture(unittest.TestCase):
    def test_read_and_annotate(self):
        rows, keys = M.read_a2_adu_rows(FX / "apr_a2_mf_tiny.csv")
        # excluded: the 2 to 4 row (not ADU), the text-flagged legalization, the permit dated before its report year
        self.assertEqual(len(rows), 10)
        self.assertNotIn("STREET_ADDRESS", rows.columns)
        self.assertIn(("ALPHA", "9990000005"), keys)
        r = M.annotate(rows, keys)
        s = M.summarize(r, ["year"]).set_index("year")
        self.assertEqual(s.loc[2021, "units_apn_year_definite"], 3)   # three formats of one APN
        self.assertEqual(s.loc[2021, "units_apn_year_possible"], 2)
        self.assertEqual(s.loc[2023, "units_unknown_apn"], 1)
        self.assertEqual(s.loc[2023, "units_unitcat_mf"], 1)
        self.assertEqual(s.loc[2023, "units_cap_removed"], 1 + 1)     # 4th ADU on ...0001, 3rd of the 3-unit row


class TestPanelAndRates(unittest.TestCase):
    def test_variants_and_plateau(self):
        panel = pd.DataFrame({"census_geoid": ["g1", "g1", "g2"], "year": [2023, 2024, 2023],
                              "adu_main": [10.0, 20.0, np.nan], "sf_detached": [1000.0, 1000.0, 500.0]})
        rem = pd.DataFrame({"census_geoid": ["g1"], "year": [2023], "removed_mf_lower": [1.0], "removed_mf_upper": [2.0],
                            "removed_cap": [3.0], "removed_cap_mf_lower": [4.0], "removed_cap_mf_upper": [5.0],
                            "removed_order2p": [6.0]})
        p = M.panel_with_variants(panel, rem)
        self.assertTrue(np.isnan(p.loc[2, "adu_cap"]))
        r = M.rate_by_year(p).set_index("year")
        self.assertAlmostEqual(r.loc[2023, "rate_cap"], 7.0)
        self.assertAlmostEqual(r.loc[2024, "rate_cap"], 20.0)
        pr = M.pooled_rate(p, ["g1", "g2"], (2023, 2024))
        self.assertAlmostEqual(pr["as_reported"]["rate"], 15.0)
        self.assertEqual(pr["as_reported"]["denominator"], 2000.0)

    def test_order_decomposition(self):
        rates = pd.DataFrame({"year": [2018, 2023, 2024], "rate_order1": [1.0, 3.0, 3.0],
                              "rate_order2": [0.0, 0.5, 0.5], "rate_order3p": [0.0, 0.5, 0.5]})
        d = M.order_decomposition(rates, (2018,), (2023, 2024)).set_index("order")
        self.assertAlmostEqual(d.loc["order1", "share_of_rise"], 2 / 3)
        self.assertAlmostEqual(d["share_of_rise"].sum(), 1.0)


class TestAcsAndEcological(unittest.TestCase):
    def test_mf_share_remainder(self):
        acs = pd.DataFrame({"sumlevel": ["050", "155", "160"], "geoid": ["06001", "0600100001", "0600100"]})
        for i in range(1, 10):
            acs[f"B25024_E00{i}"] = 0.0
        acs.loc[0, ["B25024_E001", "B25024_E004", "B25024_E009"]] = [1000, 100, 200]
        acs.loc[1, ["B25024_E001", "B25024_E004"]] = [400, 100]
        acs.loc[2, ["B25024_E001", "B25024_E004"]] = [400, 100]
        places = pd.DataFrame({"placefp": ["00100"], "incorporated": [True]})
        m = M.acs_mf_share(acs, places).set_index("census_geoid")
        self.assertAlmostEqual(m.loc["0600100", "mf_share"], 0.25)
        self.assertAlmostEqual(m.loc["06001_UNINC", "mf_share"], 200 / 600)

    def test_ecological_recovers_positive_effect(self):
        rng = np.random.default_rng(1)
        n = 300
        df = pd.DataFrame({"value": rng.uniform(3e5, 1.5e6, n), "income": rng.uniform(5e4, 2e5, n),
                           "homes": rng.uniform(2e3, 5e4, n), "mf_share": rng.uniform(0, 0.6, n)})
        df["exposure"] = df["homes"] * 3 / 1000
        mu = df["exposure"] * np.exp(0.5 + 0.8 * np.log(df["value"] / 5e5) + 1.5 * df["mf_share"])
        df["adu"] = rng.poisson(mu)
        f = M.ecological_fit(df, M.ECO_SPECS["value_income_size"], n_draws=200)
        self.assertGreater(f["coef_mf_share"], 1.0)
        self.assertLess(f["coef_mf_share"], 2.0)
        self.assertTrue(0 < f["implied_share_p10"] < f["implied_share"] < f["implied_share_p90"] < 1)


class TestCalibration(unittest.TestCase):
    def test_band_shares_line_and_application(self):
        # two LA jurisdictions in 2023: low-MF place 10% of single-band units on MF lots, high-MF place 30%
        la = pd.DataFrame({
            "juris_name": ["L"] * 10 + ["H"] * 10 + ["L", "H"],
            "year": [2023] * 22,
            "units": [10] * 20 + [5, 5],
            "mf_share": [0.1] * 10 + [0.5] * 10 + [0.1, 0.5],
            "is_mf": [True] + [False] * 9 + [True] * 3 + [False] * 7 + [True, True],
            "definite_any": [False] * 20 + [True, True],
            "possible_only": [False] * 22,
        })
        probs, fits = M.la_calibration(la, min_units=30)
        pd_ = probs.set_index("cband")["p_mf"]
        self.assertAlmostEqual(pd_["definite"], 1.0)
        self.assertAlmostEqual(pd_["single"], 0.2)
        f = fits.iloc[0]
        self.assertAlmostEqual(f["a"] + f["b"] * 0.1, 0.1)
        self.assertAlmostEqual(f["a"] + f["b"] * 0.5, 0.3)
        r = pd.DataFrame({"year": [2023, 2023, 2019], "mf_share": [0.3, 0.3, 0.3], "units": [1, 1, 1],
                          "definite_any": [False, True, False], "possible_only": [False, False, False]})
        p = M.calibrated_mf(r, probs, fits)
        self.assertAlmostEqual(p[0], 0.2)       # line at 0.3
        self.assertAlmostEqual(p[1], 1.0)       # definite band share
        self.assertEqual(p[2], 0.0)             # no 2018-2019 calibration in this fixture
        per = M.period_of(pd.Series([2018, 2021, 2025, 2026]))
        self.assertEqual(per[:3].tolist(), ["2018-2019", "2020-2022", "2023-2025"])
        self.assertTrue(pd.isna(per[3]))


class TestLaAssessor(unittest.TestCase):
    def test_classify(self):
        codes = pd.Series(["0100", "0101", "0200", "0300", "0400", "0500", "05A6", "010C", "1100", None, "010V", "0800", "0700"])
        desc = pd.Series(["Single Family Residence", "", "Double, Duplex, or Two Units", "", "", "", "",
                          "Single Family Residence", "Store", "", "", "Rooming/Boarding House", "Manufactured Home"])
        c = M.classify_la_use(codes, desc).tolist()
        self.assertEqual(c, ["single_family", "single_family", "two_units", "three_four_units", "three_four_units",
                             "five_plus_units", "five_plus_units", "condo_or_pud", "other_use",
                             "unmatched", "vacant", "other_use", "mobile_home"])

    def test_ain(self):
        a = M.la_ain(pd.Series(["1234567890", "12345", None]))
        self.assertEqual(a[0], "1234567890")
        self.assertTrue(a[1:].isna().all())


if __name__ == "__main__":
    unittest.main()
