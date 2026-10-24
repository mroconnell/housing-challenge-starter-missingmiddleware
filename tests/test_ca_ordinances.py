"""Offline tests for California pre-2020 ADU rules vs activity (missing_middleware.comparison.ca_ordinances)."""
import csv
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.comparison import ca_ordinances as co

FIX = Path(__file__).parent / "fixtures" / "ca_ordinances"
REF = Path(__file__).resolve().parent.parent / "reference"

XW = pd.DataFrame({"juris_name": ["ADELANTO", "ALAMEDA", "ALAMEDA COUNTY", "BERKELEY", "VENTURA", "ANAHEIM",
                                  "BAKERSFIELD", "ALPINE COUNTY"],
                   "census_geoid": ["0600296", "0600562", "06001_UNINC", "0606000", "0665042", "0602000",
                                    "0603526", "06003_UNINC"]})


class TestNames(unittest.TestCase):
    def test_norm_name(self):
        self.assertEqual(co.norm_name("Alpine County Unincorporated"), "ALPINE COUNTY")
        self.assertEqual(co.norm_name("BERKELEY update"), "BERKELEY")
        self.assertEqual(co.norm_name("GLENDALE (AMENDED)"), "GLENDALE")
        self.assertEqual(co.norm_name("RIVERSIDE, CITY"), "RIVERSIDE")
        self.assertEqual(co.norm_name("SAN LUIS OBISPO CO."), "SAN LUIS OBISPO COUNTY")
        self.assertEqual(co.norm_name("SAN BUENAVENTURA"), "VENTURA")
        self.assertEqual(co.norm_name("BURLINGAME -"), "BURLINGAME")


class TestSources(unittest.TestCase):
    def test_scorecard(self):
        s = co.parse_scorecard_table((FIX / "scorecard_appendix_c.md").read_text()).set_index("juris_name")
        self.assertEqual(len(s), 4)                          # criteria table before Appendix C ignored
        self.assertFalse(s.loc["ADELANTO", "cci_graded"])
        self.assertTrue(np.isnan(s.loc["ADELANTO", "cci_adus_2018"]))   # '-' is missing, never zero
        self.assertEqual(s.loc["BERKELEY", "cci_grade"], "B-")
        self.assertEqual(s.loc["BERKELEY", "cci_grade_points"], co.GRADE_POINTS["B-"])
        self.assertEqual(s.loc["ALAMEDA COUNTY", "cci_year_adopted"], 2017)

    def test_hcd_xlsx(self):
        rows = co.read_xlsx_rows(FIX / "hcd_received_small.xlsx")
        h, as_of = co.parse_hcd_received(rows)
        self.assertEqual(as_of, "May 1, 2019")
        h = h.set_index("juris_name")
        self.assertFalse(h.loc["ADELANTO", "hcd_received"])
        self.assertEqual(h.loc["BERKELEY", "hcd_n_filings"], 2)          # update + original collapse to one row
        self.assertEqual(h.loc["BERKELEY", "hcd_ordinance_date"], "2018-06-06")  # latest filing kept
        self.assertIn("VENTURA", h.index)
        g = co.attach_geoid(h.reset_index(), XW)
        self.assertEqual(g["census_geoid"].isna().sum(), 0)

    def test_tcrlus_codes(self):
        t = co.tcrlus_codes(pd.read_csv(FIX / "tcrlus_small.csv")).set_index("juris_name")
        self.assertEqual(t.loc["ALAMEDA", "tcrlus_ordinance"], "adopted")
        self.assertFalse(t.loc["ALAMEDA", "lot_minimum"])                # -97 (N/A, blank or zero) -> False
        self.assertFalse(t.loc["ALAMEDA", "extra_parking"])
        self.assertTrue(t.loc["ANAHEIM", "lot_minimum"])
        self.assertTrue(t.loc["ANAHEIM", "size_below_benchmark"])        # 500 < 600
        self.assertTrue(pd.isna(t.loc["ANAHEIM", "fees"]))               # -99 not answered stays missing
        self.assertTrue(pd.isna(t.loc["BAKERSFIELD", "extra_parking"]))
        self.assertTrue(t.loc["BAKERSFIELD", "fees"])                    # 25,000 >= 10,000
        self.assertEqual(t.loc["BAKERSFIELD", "tcrlus_ordinance"], "no_local_ordinance")
        self.assertTrue(pd.isna(t.loc["ALPINE COUNTY", "fees"]))         # -96 inconsistent stays missing
        self.assertEqual(t.loc["ALPINE COUNTY", "tcrlus_type"], "county")


class TestAnalysis(unittest.TestCase):
    def test_flag_counts(self):
        df = pd.DataFrame({f: pd.array([None, None], dtype="boolean") for f in co.FLAGS})
        df.loc[0, "owner_occupancy"] = True
        df.loc[0, "extra_parking"] = True
        df.loc[0, "fees"] = True
        df.loc[1, "owner_occupancy"] = False
        fc = co.flag_counts(df)
        self.assertEqual(fc.loc[0, "n_tier1"], 2)
        self.assertEqual(fc.loc[0, "n_tier2"], 1)
        self.assertEqual(fc.loc[1, "n_flags"], 0)
        self.assertEqual(fc.loc[1, "n_unknown"], 9)

    def test_spearman_and_auc(self):
        x = pd.Series([1, 2, 3, 4, 5, np.nan])
        y = pd.Series([2, 4, 6, 8, 10, 1])
        r, n = co.spearman(x, y)
        self.assertAlmostEqual(r, 1.0)
        self.assertEqual(n, 5)
        auc, p, q = co.ordered_logit_free_auc(pd.Series([0.1, 0.2, 0.8, 0.9]), pd.Series([False, False, True, True]))
        self.assertEqual((auc, p, q), (1.0, 2, 2))
        auc, _, _ = co.ordered_logit_free_auc(pd.Series([1, 1]), pd.Series([True, False]))
        self.assertEqual(auc, 0.5)                                       # ties count one half

    def test_poisson_rate_ratio_recovers_ratio(self):
        rng = np.random.default_rng(1)
        n = 400
        flag = rng.integers(0, 2, n)
        expo = rng.uniform(1, 5, n)
        y = rng.poisson(2.0 * expo * np.where(flag == 1, 0.5, 1.0))
        df = pd.DataFrame({"y": y, "e": expo, "f": flag, "z": rng.normal(size=n)})
        r = co.poisson_rate_ratio(df, "y", "e", "f", ("z",), n_boot=200)
        self.assertAlmostEqual(r["rate_ratio"], 0.5, delta=0.08)
        self.assertLess(r["rr_lo95"], 0.5)
        self.assertGreater(r["rr_hi95"], 0.5)
        self.assertEqual(r["n_places"], n)

    def test_cv_auc_separable_and_noise(self):
        rng = np.random.default_rng(2)
        x = rng.normal(size=200)
        y = (x > 0).astype(float)
        X = np.column_stack([np.ones(200), x])
        self.assertGreater(co.cv_auc(X, y, repeats=3), 0.95)
        noise = np.column_stack([np.ones(200), rng.normal(size=200)])
        self.assertLess(abs(co.cv_auc(noise, y, repeats=5) - 0.5), 0.12)

    def test_hand_sample_draw_is_deterministic(self):
        rng = np.random.default_rng(3)
        rows = []
        for i in range(120):
            rows.append({"census_geoid": f"06{i:05d}", "holdout": i % 10 == 0, "value": rng.uniform(2e5, 2e6),
                         "group": ["active", "middle", "restrictive"][i % 3]})
        base = pd.DataFrame(rows)
        a = co.draw_hand_sample(base)
        b = co.draw_hand_sample(base)
        self.assertEqual(list(a["census_geoid"]), list(b["census_geoid"]))
        self.assertFalse(a["holdout"].any())
        self.assertEqual(a["census_geoid"].nunique(), len(a))


class TestHandCodingFile(unittest.TestCase):
    """Data-quality checks on the committed hand coding (reference/ca_ordinances_2019.csv)."""

    @classmethod
    def setUpClass(cls):
        with open(REF / "ca_ordinances_2019.csv", newline="") as f:
            cls.rows = list(csv.DictReader(f))

    def test_header_and_vocab(self):
        self.assertTrue(set(co.HAND_COLUMNS) <= set(self.rows[0].keys()))
        for r in self.rows:
            for fl in co.FLAGS:
                self.assertIn(r[fl], ("true", "false", "unknown"), (r["juris_name"], fl))
            self.assertIn(r["ordinance_status"], ("mentions_allows", "prohibits", "not_mentioned", "could_not_access"))
            self.assertIn(r["rights_class"], ("scenario_benchmark", "restricted", "prohibited_explicit",
                                              "prohibited_implicit", "undetermined", "no_zoning"))

    def test_coded_rows_have_dated_pre2020_sources(self):
        for r in self.rows:
            if r["ordinance_status"] == "could_not_access":
                self.assertEqual(r["rights_class"], "undetermined")
                continue
            self.assertTrue(r["source_url"].startswith("http"), r["juris_name"])
            self.assertTrue(r["rules_as_of"] and r["rules_as_of"] < "2020-01-01", r["juris_name"])
            if r["source_type"].startswith("wayback"):
                self.assertIn("web.archive.org", r["source_url"], r["juris_name"])
                self.assertTrue(r["snapshot_date"], r["juris_name"])

    def test_benchmark_rows_have_no_true_flags(self):
        for r in self.rows:
            if r["rights_class"] == "scenario_benchmark":
                self.assertFalse(any(r[f] == "true" for f in co.FLAGS), r["juris_name"])
            if r["rights_class"] == "restricted":
                self.assertTrue(any(r[f] == "true" for f in co.FLAGS), r["juris_name"])


if __name__ == "__main__":
    unittest.main()
