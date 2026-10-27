"""ADU placebo test (scripts/run_adu_placebo.py; plan docs/adu/PLACEBO_PLAN.md). Offline: synthetic series for the
window rules, plus consistency checks on the committed reference/adu_placebo_*.csv files. The Wisconsin engine
cases need data/processed and are only checked through their committed output."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference"
sys.path.insert(0, str(ROOT / "scripts"))
import run_adu_placebo as pl  # noqa: E402


def toy(counts, homes=10000.0, nolaw=None):
    return pl.Series("toy", "C", "toy", "toy", members=[pl.Member(homes, counts)], nolaw=nolaw)


class TestWindows(unittest.TestCase):
    def test_rate_is_per_1000_homes_per_year(self):
        s = toy({2020: 10, 2021: 20})
        w = s.window([2020, 2021, 2022])          # 2022 missing: not counted as zero
        self.assertEqual(w["years"], [2020, 2021])
        self.assertAlmostEqual(w["rate"], 30 / (10000 * 2 / 1000))

    def test_year0_dropped_and_both_windows_needed(self):
        s = toy({y: 1 for y in range(2010, 2020)})
        s.members[0].counts[2015] = 999           # year 0 must not enter either window
        ba = pl.before_after(s, 2015)
        self.assertEqual(ba["before"]["years"], [2012, 2013, 2014])
        self.assertEqual(ba["after"]["years"], [2016, 2017, 2018])
        self.assertAlmostEqual(ba["D"], 0.0)
        self.assertIsNone(pl.before_after(s, 2019, limit=(2010, 2019)))   # no after year inside the limit

    def test_ratio_undefined_when_before_zero(self):
        s = toy({2010: 0, 2012: 3})
        ba = pl.before_after(s, 2011)
        self.assertTrue(np.isnan(ba["R"]))
        self.assertAlmostEqual(ba["D"], 0.3)

    def test_calendar_rule_uses_real_year0s_only(self):
        s = toy({y: 1 for y in range(2014, 2026)}, nolaw=(2014, 2025))
        self.assertEqual(pl.eligible_years(s, "calendar"), list(pl.CAL_YEARS))
        s2 = toy({y: 1 for y in range(2005, 2018)}, nolaw=(2005, 2017))
        self.assertEqual(pl.eligible_years(s2, "calendar"), [2016])

    def test_group_ratio_is_ratio_of_means(self):
        rows = [{"before": {"rate": 0.0, "count": 0, "home_years_k": 10}, "after": {"rate": 1.0, "count": 10, "home_years_k": 10}, "D": 1.0},
                {"before": {"rate": 1.0, "count": 30, "home_years_k": 30}, "after": {"rate": 1.0, "count": 30, "home_years_k": 30}, "D": 0.0}]
        g = pl.group_stats(rows)
        self.assertAlmostEqual(g["D"], 0.5)
        self.assertAlmostEqual(g["ratio"], 1.0 / 0.5)
        w = pl.group_stats(rows, weighted=True)
        self.assertAlmostEqual(w["ratio"], (40 / 40) / (30 / 40))

    def test_resample_deterministic(self):
        s = toy({y: y - 2000 for y in range(2010, 2026)}, nolaw=(2010, 2025))
        d1, _ = pl.resample([s], "every", draws=50)
        d2, _ = pl.resample([s], "every", draws=50)
        pd.testing.assert_frame_equal(d1, d2)


class TestCommittedOutputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summ = pd.read_csv(REF / "adu_placebo_summary.csv")
        cls.ser = pd.read_csv(REF / "adu_placebo_series.csv")
        cls.elig = pd.read_csv(REF / "adu_placebo_eligible.csv")
        cls.wi = pd.read_csv(REF / "adu_placebo_wi.csv")

    def test_rerun_reproduces_summary(self):
        res = pl.main(write=False, with_engine=False)
        pd.testing.assert_frame_equal(res["summary"].round(4).reset_index(drop=True),
                                      self.summ.reset_index(drop=True), check_dtype=False, atol=1e-4)

    def test_percentiles_ordered_and_cases_present(self):
        need = {"main", "S1_never_law_states", "S2_drop_local_reform_windows", "S3_oregon_in_A",
                "S4_every_year_rule", "S5_home_weighted", "S6_CA_madison_like"}
        self.assertTrue(need <= set(self.summ.case))
        self.assertTrue((self.summ.C_p05 <= self.summ.C_p50 + 1e-9).all())
        self.assertTrue((self.summ.C_p50 <= self.summ.C_p95 + 1e-9).all())

    def test_group_A_is_mean_of_its_series(self):
        a = self.ser.set_index("series").loc[["CA_nonholdout", "WA_inc_exSeattle"], "D"].mean()
        main_d = self.summ[(self.summ.case == "main") & (self.summ.statistic == "D")].iloc[0]
        self.assertAlmostEqual(main_d["A"], a, places=3)

    def test_placebo_windows_stay_in_no_law_years(self):
        lim = {"denver": 2023, "portland": 2017, "seattle": 2022, "austin": 2023, "HI_honolulu": 2023,
               "MD_montgomery": 2024, "madison": 2025}
        for sid, last in lim.items():
            for yrs in self.elig.loc[self.elig.series.eq(sid), "after_years"].astype(str):
                self.assertLessEqual(max(int(float(y)) for y in yrs.split("|")), last, sid)

    def test_wisconsin_adopted_rows_match_model_and_total_moves_little(self):
        st = pd.read_csv(REF / "adu_model_statewide.csv").set_index("path")
        ad = self.wi[self.wi.case.eq("adopted")].set_index("path")
        for p in ("lower", "central", "upper"):
            self.assertAlmostEqual(ad.loc[p, "additional_5yr"], st.loc[p, "additional_units"], delta=0.1)
            self.assertAlmostEqual(ad.loc[p, "baseline_5yr"], st.loc[p, "baseline_units"], delta=0.1)
        prop = self.wi[self.wi.trend_kind.eq("ratio")]
        self.assertTrue((prop.d_baseline > 0).all())
        self.assertTrue((prop.d_additional < 0).all())
        # the with-law total moves by under 2% of itself; the baseline gain mostly comes out of the addition
        self.assertTrue((prop.d_with_law.abs() < 0.02 * prop.with_law_5yr).all())


if __name__ == "__main__":
    unittest.main()
