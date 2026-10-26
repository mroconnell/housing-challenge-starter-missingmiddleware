"""TOD comparison cases (missing_middleware/tod/cases.py): arithmetic on small synthetic fixtures, no network."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.tod import cases as C

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "tod" / "cases"
ACRES = {"treatment": 10.0, "comparison": 20.0, "second_comparison": 5.0}
BEFORE, AFTER = [2013, 2014, 2015], [2017, 2018]


def permits() -> pd.DataFrame:
    return pd.read_csv(FIX / "permits.csv")


class TestPeriods(unittest.TestCase):
    def test_period_years_limits(self):
        p = C.period_years(2019, 1990, 2025)
        self.assertEqual(p["before"], list(range(2013, 2019)))
        self.assertEqual(p["after"], list(range(2020, 2025)))
        p = C.period_years(2011, 2010, 2025)
        self.assertEqual(p["before"], [2010])
        self.assertEqual(C.period_years(2016, 2013, 2018)["after"], [2017, 2018])

    def test_context_only_rules(self):
        self.assertEqual(C.case_status([2010], [2012]), "context_only: 1 before years (plan needs 3)")
        self.assertEqual(C.case_status([2010, 2011, 2012], [2014]), "measured")
        self.assertTrue(C.case_status([2010, 2011, 2012], [2014], has_units=False).startswith("context_only"))
        self.assertTrue(C.case_status([2010, 2011, 2012], [2014], is_permits=False).startswith("context_only"))


class TestDiD(unittest.TestCase):
    def test_rates_fill_zero_years(self):
        r = C.rates_by_year(permits(), ACRES, BEFORE)
        t = r[r.area == "treatment"].set_index("year")["rate"]
        self.assertEqual(list(t), [1.0, 0.0, 2.0])

    def test_did_by_hand(self):
        # T before (10+0+20)/3/10 = 1.0; T after (40+60)/2/10 = 5.0; C before 30/3/20 = 0.5; C after 60/2/20 = 1.5
        d = C.did(permits(), ACRES, BEFORE, AFTER)
        self.assertAlmostEqual(d["treat_before"], 1.0)
        self.assertAlmostEqual(d["treat_after"], 5.0)
        self.assertAlmostEqual(d["comp_before"], 0.5)
        self.assertAlmostEqual(d["comp_after"], 1.5)
        self.assertAlmostEqual(d["did"], 3.0)

    def test_year0_not_used(self):
        p = permits()
        p.loc[p.project == "p8", "units"] = 10_000
        self.assertAlmostEqual(C.did(p, ACRES, BEFORE, AFTER)["did"], 3.0)

    def test_second_comparison_and_per_homes(self):
        # second comparison: before 5/3/5 = 1/3, after 25/2/5 = 2.5 -> (5-1) - (2.5-1/3)
        d = C.did(permits(), ACRES, BEFORE, AFTER, comp="second_comparison")
        self.assertAlmostEqual(d["did"], 4.0 - (2.5 - 1 / 3))
        homes = {"treatment": 1000.0, "comparison": 4000.0}
        h = C.did(permits(), homes, BEFORE, AFTER, scale=1000.0)
        # T 10/yr -> 10 per 1,000 homes; after 50 -> 50; C 10 -> 2.5; 30 -> 7.5
        self.assertAlmostEqual(h["did"], (50 - 10) - (7.5 - 2.5))

    def test_drop_largest_project(self):
        d = C.did(C.drop_largest_project(permits(), BEFORE, AFTER), ACRES, BEFORE, AFTER)["did"]
        self.assertAlmostEqual(d, (2.0 - 1 / 3) - (0.5 - 0.0))


class TestBootstrap(unittest.TestCase):
    def test_deterministic_with_seed(self):
        a = C.bootstrap_did(permits(), ACRES, BEFORE, AFTER, draws=500, seed=7)
        b = C.bootstrap_did(permits(), ACRES, BEFORE, AFTER, draws=500, seed=7)
        self.assertEqual(a[:2], b[:2])
        np.testing.assert_array_equal(a[2], b[2])
        c = C.bootstrap_did(permits(), ACRES, BEFORE, AFTER, draws=500, seed=8)
        self.assertFalse(np.array_equal(a[2], c[2]))

    def test_default_draws_and_interval(self):
        lo, hi, draws = C.bootstrap_did(permits(), ACRES, BEFORE, AFTER)
        self.assertEqual(len(draws), C.N_DRAWS)
        self.assertEqual(C.N_DRAWS, 2000)
        self.assertLessEqual(lo, hi)
        self.assertAlmostEqual(lo, float(np.quantile(draws, 0.05)))
        self.assertAlmostEqual(hi, float(np.quantile(draws, 0.95)))

    def test_whole_projects_resampled(self):
        # A single project in each area: every draw reproduces the point estimate exactly.
        p = pd.DataFrame({"project": ["a", "a", "b", "b"], "area": ["treatment", "treatment", "comparison", "comparison"],
                          "year": [2013, 2017, 2014, 2018], "units": [3.0, 9.0, 6.0, 6.0]})
        lo, hi, draws = C.bootstrap_did(p, ACRES, BEFORE, AFTER, draws=50)
        point = C.did(p, ACRES, BEFORE, AFTER)["did"]
        np.testing.assert_allclose(draws, point)


class TestDose(unittest.TestCase):
    def test_dose_area_weighted(self):
        d = C.dose(pd.read_csv(FIX / "dose.csv"))
        self.assertAlmostEqual(d, (2 * 3.0 + 6 * 2.0 + 2 * 0.0) / 10)

    def test_conversions(self):
        self.assertAlmostEqual(C.far_from_height(120, 6.02 / 120), 6.02)
        self.assertAlmostEqual(C.far_from_density(22, 680), 22 * 680 / 43560)

    def test_charlotte_districts(self):
        from missing_middleware.tod import case_charlotte as CL
        self.assertEqual(CL.base_district("B-1(CD)"), "B-1")
        self.assertEqual(CL.base_district("MUDD-O"), "MUDD")
        self.assertEqual(CL.base_district("R-12MF(CD)"), "R-12MF")
        self.assertEqual(CL.zoning_class("I-2"), "ind")
        self.assertEqual(CL.height_before("B-2"), 40.0)
        self.assertTrue(CL.capped_before("B-2"))
        self.assertFalse(CL.capped_before("TOD-CC"))
        self.assertEqual(CL.height_before("UMUD"), float("inf"))
        self.assertEqual(CL.height_after("TOD-UC"), 130.0)

    def test_height_dose_has_no_far_effect(self):
        ci = C.CaseInputs(case="t", role="fit", effective_year=2016, first_year=2013, last_full_year=2018,
                          permits=permits(), acres=ACRES, homes={}, dose_unit="height_ft",
                          dose_table=pd.DataFrame({"acres": [1.0], "old_far": [40.0], "new_far": [100.0]}))
        _, row = C.estimate_case(ci, draws=50)
        self.assertIsNone(row["effect_per_dose"])
        self.assertAlmostEqual(row["dose_added_height_ft"], 60.0)
        self.assertAlmostEqual(row["effect_per_added_ft"], round(3.0 / 60.0, 5))

    def test_chicago_unit_parsing_and_staged_dedupe(self):
        from missing_middleware.tod import case_chicago as CH
        self.assertEqual(CH.parse_units("ERECT NEW 6 STORY, 41 UNIT APARTMENT BUILDING"), 41)
        self.assertEqual(CH.parse_units("ADDRESS INCLUDES 4302 S. DREXEL UNITS A & B"), 0)
        self.assertEqual(CH.parse_units("REVISION TO PERMIT 1 FOR 8 DWELLING UNITS"), 0)
        p = pd.DataFrame({"x": [0.0, 0.2, 0.0, 30.0, 0.0], "y": [0.0, 0.1, 0.0, 0.0, 0.0], "units": [40, 40, 40, 1, 1],
                          "issue_date": ["2016-01-01", "2016-09-01", "2019-01-01", "2016-01-01", "2016-02-01"]})
        d = CH.dedupe_staged(p)
        # stage merged (same point, same units, 8 months); the 2019 permit is a new building; homes at other points kept
        self.assertEqual(sorted(d["issue_date"].tolist()), ["2016-01-01", "2016-01-01", "2016-02-01", "2019-01-01"])

    def test_effect_per_dose_in_estimate(self):
        ci = C.CaseInputs(case="t", role="fit", effective_year=2016, first_year=2013, last_full_year=2018,
                          permits=permits(), acres=ACRES, homes={}, dose_table=pd.read_csv(FIX / "dose.csv"))
        rates, row = C.estimate_case(ci, draws=200)
        self.assertEqual(row["status"], "measured")
        self.assertAlmostEqual(row["estimate_units_per_acre_yr"], 3.0)
        self.assertAlmostEqual(row["effect_per_dose"], round(3.0 / 1.8, 4))
        self.assertEqual(set(rates["period"]), {"before", "year0", "after"})


class TestUniformAreas(unittest.TestCase):
    def test_rule(self):
        import geopandas as gpd
        from shapely.geometry import box
        # a row of 100 m lots: 0-2 in the reform; lot 2 already at the law; lot 4 changed outside the reform
        lots = gpd.GeoDataFrame(geometry=[box(i * 100, 0, i * 100 + 90, 90) for i in range(8)], crs=32119)
        in_reform = pd.Series([True, True, True] + [False] * 5)
        before = pd.Series([1.0, 1.0, 6.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        after = pd.Series([6.0, 3.0, 7.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        changed = pd.Series([False] * 4 + [True] + [False] * 3)
        area, info = C.uniform_areas(lots, in_reform, after > before, before, after, pd.Series(True, index=lots.index),
                                     changed, pd.Series(True, index=lots.index))
        self.assertEqual(info["median_new_level_on_rising_land"], 6.0)
        # lot 1 rose (1.0 -> 3.0) and was below the median before: treated; lot 2 (6.0 before) was already at the law
        self.assertEqual(list(area[:3]), ["treatment", "treatment", None])
        self.assertIsNone(area[4])
        self.assertEqual(area[3], "comparison")


class TestFitSetExcludesHeldOut(unittest.TestCase):
    def test_fit_set(self):
        e = pd.read_csv(FIX / "estimates.csv")
        f = C.fit_set(e)
        self.assertEqual(list(f["case"]), ["a_fit", "b_fit"])
        s = C.fit_set_summary(e)
        self.assertEqual(s["median_effect_per_dose"], 2.0)
        self.assertNotIn("c_heldout", s["cases"])

    def test_pooled_ramp_ignores_heldout(self):
        e = pd.read_csv(FIX / "estimates.csv")
        ev = pd.DataFrame({"case": ["a_fit", "c_heldout"], "event_year": [1, 1], "gap_minus_before": [1.0, 99.0]})
        r = C.pooled_ramp(ev, e)
        self.assertEqual(float(r["mean"].iloc[0]), 1.0)

    def test_committed_estimates_fit_rows(self):
        path = ROOT / "reference" / "tod_case_estimates.csv"
        if not path.exists():
            self.skipTest("estimates not built yet")
        e = pd.read_csv(path)
        self.assertTrue(set(e["role"]) <= set(C.ROLES))
        held = e[e["role"] == "heldout"]["case"]
        self.assertFalse(set(held) & set(C.fit_set(e)["case"]))
        if "chicago_tod_2013_2015" in set(e["case"]):
            self.assertEqual(e.loc[e.case == "chicago_tod_2013_2015", "role"].iloc[0], "heldout")


class TestNoIdsCommitted(unittest.TestCase):
    ID_COLS = re.compile(r"parcel|permit_?num|project|pin|bbl|bin|job|address|owner|objectid", re.I)
    ID_VALUES = re.compile(r"\b\d{8,}\b|\bB\d{7}\b|\b\d{2}-\d{6}\b")

    def check(self, path: Path, allowed_cols: set[str]):
        if not path.exists():
            self.skipTest(f"{path.name} not built yet")
        d = pd.read_csv(path, dtype=str)
        bad = [c for c in d.columns if self.ID_COLS.search(c) and c not in allowed_cols]
        self.assertEqual(bad, [], f"{path.name} has id-like columns {bad}")
        for c in d.columns:
            if c in ("notes",):
                continue
            hits = d[c].dropna().astype(str).str.contains(self.ID_VALUES)
            self.assertFalse(hits.any(), f"{path.name}.{c} has id-like values")

    def test_rates_by_year(self):
        self.check(ROOT / "reference" / "tod_case_rates_by_year.csv", set())

    def test_estimates(self):
        self.check(ROOT / "reference" / "tod_case_estimates.csv", set())

    def test_fixture_has_no_real_ids(self):
        self.assertTrue(pd.read_csv(FIX / "permits.csv")["project"].str.fullmatch(r"p\d+").all())


if __name__ == "__main__":
    unittest.main()
