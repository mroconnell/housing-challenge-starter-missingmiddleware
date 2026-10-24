"""Offline tests for the California comparison inputs and step 0 reconciliation.

Fixtures in tests/fixtures/comparison_ca/ are tiny synthetic files in the layout of
the real sources (APR Table A2 header copied from the HCD file; addresses are fake).
"""
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.comparison import ca_crosswalk as X
from missing_middleware.comparison import ca_doc as D
from missing_middleware.comparison import ca_inputs as I
from missing_middleware.comparison import ca_step0 as Z

FX = Path(__file__).parent / "fixtures" / "comparison_ca"


class TestAprA2(unittest.TestCase):
    def setUp(self):
        self.rows = I.classify_permit_rows(I.read_apr_a2(FX / "apr_a2_tiny.csv"))
        self.agg = I.aggregate_apr(self.rows)

    def test_drops_identifying_fields(self):
        for col in ("APN", "STREET_ADDRESS", "JURS_TRACKING_ID", "apn", "street_address"):
            self.assertNotIn(col, self.rows.columns)
            self.assertNotIn(col, self.agg.columns)
        self.assertTrue(self.rows["permit_key"].str.fullmatch(r"[0-9a-f]{40}").all())

    def test_income_columns_sum_to_permit_total(self):
        self.assertTrue((self.rows["bp_units"] == self.rows["bp_income_sum"]).all())

    def test_date_classification(self):
        st = dict(zip(zip(self.rows["year"], self.rows["unit_cat"], self.rows["bp_units"]), self.rows["date_status"]))
        self.assertEqual(st[(2021, "5+", 10)], "date_earlier")
        self.assertEqual(st[(2021, "MH", 1)], "date_later")
        self.assertEqual(st[(2021, "SFD", 0)], "no_permit")
        rep = self.rows[(self.rows["unit_cat"] == "ADU") & self.rows["bp_issue_year"].eq(2020)]
        self.assertTrue(rep["repeat"].all())  # same permit listed in 2020 and 2021

    def test_measures(self):
        t = self.agg[self.agg["juris_name"] == "TESTVILLE"].set_index(["year", "unit_cat"])
        self.assertEqual(t.loc[(2021, "ADU"), "bp_units_reported"], 2)
        self.assertEqual(t.loc[(2021, "ADU"), "bp_units_primary"], 1)  # undated kept, repeat dropped
        self.assertEqual(t.loc[(2021, "ADU"), "bp_units_date_earlier_repeat"], 1)
        self.assertEqual(t.loc[(2021, "5+"), "bp_units_primary"], 0)
        self.assertEqual(t.loc[(2021, "5+"), "bp_units_date_earlier_late_first"], 10)
        self.assertEqual(t.loc[(2021, "SFD"), "ent_units"], 1)
        self.assertEqual(t.loc[(2021, "ADU"), "co_units"], 1)

    def test_issue_year_dedup(self):
        d = I.apr_by_issue_year(self.rows).set_index(["juris_name", "issue_year", "unit_cat"])["bp_units_issue_year_dedup"]
        self.assertEqual(d[("TESTVILLE", 2020, "ADU")], 1)   # counted once despite two listings
        self.assertEqual(d[("TESTVILLE", 2019, "5+")], 10)   # moved to its permit year
        self.assertEqual(d[("TESTVILLE", 2021, "ADU")], 1)   # undated row uses report year

    def test_issue_year_flag(self):
        d = I.apr_by_issue_year(self.rows).set_index(["juris_name", "issue_year", "unit_cat"])["issue_year_flag"]
        self.assertEqual(d[("ALAMEDA COUNTY", 2022, "MH")], "after_first_report_year")  # dated after its 2021 report
        self.assertEqual(d[("TESTVILLE", 2019, "5+")], "ok")

    def test_wide(self):
        w = I.wide_by_unit_cat(self.agg, "bp_units_primary")
        self.assertEqual(list(w.columns[3:]), ["sfd", "sfa", "u2_4", "u5plus", "adu", "mh"])


class TestCompilation(unittest.TestCase):
    def test_reads_main_block_only(self):
        long, side = I.read_compilation(FX / "compilation_tiny.csv")
        self.assertEqual(sorted(long["juris_name"].unique()), ["ALAMEDA COUNTY", "TESTVILLE"])
        self.assertEqual(long[long["juris_name"] == "TESTVILLE"]["adu_permits"].sum(), 21)
        blank = long[(long["juris_name"] == "ALAMEDA COUNTY") & (long["year"] == 2013)].iloc[0]
        self.assertTrue(np.isnan(blank["adu_permits"]))  # missing is not zero
        self.assertEqual(blank["value_status"], "missing")
        self.assertTrue(any("SIDE COUNTY" in r for r in side))


class TestDenominators(unittest.TestCase):
    def test_county_remainder(self):
        acs = I.read_acs_b25024_ca(FX / "acs_b25024_ca_tiny.dat")
        self.assertNotIn("5500001", set(acs["placefp"].dropna()))
        places = pd.DataFrame({"placefp": ["00001", "00002"], "name": ["Testville", "Cdp"],
                               "incorporated": [True, False]})
        den = I.ca_denominators(acs, places).set_index("geoid")
        self.assertEqual(den.loc["0600001", "sf_detached"], 400)
        self.assertNotIn("0600002", den.index)  # CDPs are inside the county remainder
        self.assertEqual(den.loc["06001_UNINC", "hu_total"], 300)
        self.assertEqual(den.loc["06001_UNINC", "sf_detached"], 200)
        self.assertEqual(den.loc["06001_UNINC", "value_status"], "calculated")
        self.assertAlmostEqual(den.loc["06001_UNINC", "sf_detached_moe"], 5.0)


class TestCrosswalkAndHoldout(unittest.TestCase):
    def setUp(self):
        self.places = pd.DataFrame({"placefp": ["00001", "65042", "67000"],
                                    "name": ["Testville", "San Buenaventura (Ventura)", "San Francisco"],
                                    "incorporated": [True, True, True]})
        self.pc = pd.DataFrame({"placefp": ["00001", "65042", "67000"], "county_fips": ["001", "111", "075"]})
        pep = pd.read_csv(FX / "pep_v2020_tiny.csv", dtype=str)
        self.counties = pd.concat([X.county_lookup(pep), pd.DataFrame(
            {"county_fips": ["111", "075"], "county_name": ["Ventura County", "San Francisco County"],
             "county_key": ["VENTURA", "SAN FRANCISCO"]})], ignore_index=True)
        self.bps = pd.DataFrame({"bps_id": ["1", "2", "3"], "fips_place": ["00001", "99990", "65042"],
                                 "county_fips": ["001", "001", "111"]})

    def test_matches(self):
        names = pd.DataFrame({"juris_name": ["TESTVILLE", "ALAMEDA COUNTY", "VENTURA", "SAN FRANCISCO", "NOWHERE"],
                              "cnty_name": ["Alameda", "Alameda", "Ventura", "San Francisco", "Alameda"]})
        xw = X.build_crosswalk(names, self.places, self.pc, self.counties, self.bps).set_index("juris_name")
        self.assertEqual(xw.loc["TESTVILLE", "census_geoid"], "0600001")
        self.assertEqual(xw.loc["TESTVILLE", "bps_ids"], "1")
        self.assertEqual(xw.loc["ALAMEDA COUNTY", "census_geoid"], "06001_UNINC")
        self.assertEqual(xw.loc["ALAMEDA COUNTY", "bps_ids"], "2")
        self.assertEqual(xw.loc["VENTURA", "match_method"], "alias")
        self.assertEqual(xw.loc["SAN FRANCISCO", "juris_type"], "city_county")
        self.assertFalse(xw.loc["NOWHERE", "matched_census"])

    def test_holdout_is_deterministic(self):
        u = X.holdout_universe(self.places, self.pc, self.counties)
        self.assertIn("0649582", set(u["census_geoid"]))  # Mountain House added
        self.assertNotIn("06075_UNINC", set(u["census_geoid"]))
        a, b = X.draw_holdout(u), X.draw_holdout(u.sample(frac=1, random_state=1))
        self.assertEqual(set(a.loc[a.holdout, "census_geoid"]), set(b.loc[b.holdout, "census_geoid"]))
        self.assertEqual(int(a["holdout"].sum()), round(0.2 * len(u)))


def _toy_panel(share=0.5, base=1.2):
    """Synthetic full-reporting panel: BPS 1-unit = base x SF + share x ADU, exactly."""
    rows = []
    for j in range(12):
        for y in range(2018, 2026):
            adu = 0 if j < 4 else 5 * (j + y - 2017)
            sf = 100 + 10 * j + (y - 2018)
            rows.append({"census_geoid": f"06{j:05d}", "year": y, "hcd_sf": sf, "adu": adu, "hcd_sf_reported": sf,
                         "adu_reported": adu, "hcd_sf_dedup": sf, "adu_dedup": adu,
                         "bps_1unit_units": base * sf + share * adu, "both_full": True,
                         "sf_detached_acs": 30_000, "in_holdout": j == 11})
    p = pd.DataFrame(rows)
    p.loc[p["census_geoid"] == "0600011", "bps_1unit_units"] *= 5  # holdout place: wildly different
    return p


class TestStep0(unittest.TestCase):
    def test_share_sensitivity_recovers_share_and_excludes_holdout(self):
        s = Z.table_b_share_sensitivity(_toy_panel(), draws=50)
        nh = s[(s["jurisdiction_sample"] == "non_holdout") & s["analysis"].isin(
            ["baseline_adjusted", "bootstrap_jurisdiction_cluster", "by_year"])]
        self.assertTrue(np.allclose(nh["estimate"], 0.5))
        self.assertTrue(np.allclose(nh.dropna(subset=["ci_low"])[["ci_low", "ci_high"]], 0.5))
        al = s[(s["jurisdiction_sample"] == "all") & (s["analysis"] == "baseline_adjusted")]
        self.assertFalse(np.allclose(al["estimate"], 0.5))  # the holdout place changes the pooled figure

    def test_bps_missing_city_fold(self):
        xw = pd.DataFrame({"juris_name": ["SMALLTOWN", "BIG COUNTY"], "census_geoid": ["0600009", "06013_UNINC"],
                           "juris_type": ["city", "county_unincorporated"], "county_fips": ["013", "013"],
                           "matched_bps": [False, True], "in_hcd_apr": [True, True]})
        p = pd.DataFrame({"census_geoid": ["0600009", "06013_UNINC"] * 2, "year": [2020, 2020, 2021, 2021],
                          "county_fips": ["013"] * 4, "hcd_nonadu": [50, 100, 50, 100], "hcd_sf": [50, 100, 50, 100],
                          "adu": [0, 0, 0, 0], "bps_units_total": [np.nan, 150, np.nan, 150],
                          "bps_1unit_units": [np.nan, 150, np.nan, 150], "hcd_present": True,
                          "bps_present": [False, True, False, True], "both_full": [False, True, False, True],
                          "in_holdout": False})
        miss = Z.bps_missing_cities(xw)
        p["bps_missing_city"] = p["census_geoid"].isin(miss["census_geoid"])
        p["bps_may_include_cities"] = p["census_geoid"].eq("06013_UNINC")
        cm = p[p["bps_missing_city"]].groupby("year")[["hcd_nonadu", "hcd_sf", "adu"]].sum().add_suffix("_bps_missing_cities")
        p = p.merge(cm.reset_index().assign(census_geoid="06013_UNINC"), on=["census_geoid", "year"], how="left")
        counties = pd.DataFrame({"county_fips": ["013"], "county_name": ["Big County"]})
        f = Z.table_c_bps_missing_cities_fold(p, counties, xw).iloc[0]
        self.assertAlmostEqual(f["ratio_hcd_to_bps_before"], 100 / 150)
        self.assertAlmostEqual(f["ratio_hcd_to_bps_folded"], 1.0)
        self.assertTrue(f["fold_supported"])
        self.assertEqual(f["bps_missing_cities"], "SMALLTOWN")

    def test_holdout_flag(self):
        hold = pd.DataFrame({"census_geoid": ["0600001", "0600002"], "holdout": [True, False]})
        self.assertEqual(list(X.holdout_flag(pd.Series(["0600001", "0600002", "0699999"]), hold)), [True, False, False])

    def test_doc_table_renderer(self):
        t = D.table(["A", "B"], [["x", D.n0(1234.0)], ["y", D.r2(0.456)]])
        self.assertEqual(t.splitlines()[2], "| x | 1,234 |")
        self.assertEqual(t.splitlines()[3], "| y | 0.46 |")
        self.assertEqual(D.r2(float("nan")), "—")

    def test_doc_block_markers_parse_when_empty(self):
        text = "x\n<!-- generated:a -->\n<!-- /generated:a -->\ny\n<!-- generated:b -->\nold\n<!-- /generated:b -->\n"
        names = [m.group("name") for m in D._RE.finditer(text)]
        self.assertEqual(names, ["a", "b"])

    @unittest.skipUnless(D.available(Path(__file__).parents[1] / "data" / "processed" / "comparison_ca"),
                         "California build outputs not present (git-ignored); run scripts/build_ca_comparison_data.py")
    def test_doc_numbers_match_outputs(self):
        changed = D.update_doc(Path(__file__).parents[1] / "data" / "processed" / "comparison_ca", check=True)
        self.assertEqual(changed, [], f"CA_COMPARISON_DATA.md is stale in blocks {changed}; run --doc-only")

    def test_ols_recovers_coefficients(self):
        rng = np.random.default_rng(0)
        X_ = rng.uniform(0, 100, size=(200, 2))
        y = 1.0 * X_[:, 0] + 0.25 * X_[:, 1]
        res, r2, n = Z._ols(y, X_, ["sf", "adu"])
        self.assertAlmostEqual(res["adu"][0], 0.25, places=6)
        self.assertEqual(n, 200)

    def test_filing_status(self):
        agg = pd.DataFrame({"juris_name": ["TESTVILLE"], "year": [2020]})
        xw = pd.DataFrame({"juris_name": ["TESTVILLE"], "census_geoid": ["0600001"], "juris_type": ["city"],
                           "in_hcd_apr": [True]})
        f = Z.filing_status(agg, xw, [{"JURIS_NAME": "Testville", "YEAR": 2021}], [])
        st = f.set_index("year")["filing_status"]
        self.assertEqual(st[2020], "a2_rows")
        self.assertEqual(st[2021], "filed_no_a2_rows")
        self.assertEqual(st[2022], "no_record")

    def test_pep_v2020_reader(self):
        d = I.read_pep_v2020_state(FX / "pep_v2020_tiny.csv")
        self.assertEqual(d.set_index("year")["housing_units"][2015], 150)
        self.assertEqual(len(d), 11)


if __name__ == "__main__":
    unittest.main()
