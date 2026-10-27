"""TOD all-variables test (missing_middleware/tod/allvars.py; docs/tod/ALLVARS_PLAN.md): rules on small synthetic
tables, no network. Committed outputs are checked for identifiers and race variables when they exist."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.tod import allvars as A
from missing_middleware.tod import traits as T

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference"
HAS_SKLEARN = importlib.util.find_spec("sklearn") is not None


class TestSurvey(unittest.TestCase):
    def test_end_year_before_reform(self):
        self.assertEqual(A.survey_end_year(2003), 2009)   # no 5-year release before 2005-2009
        self.assertEqual(A.survey_end_year(2010), 2009)
        self.assertEqual(A.survey_end_year(2011), 2010)
        self.assertEqual(A.survey_end_year(2019), 2018)
        self.assertEqual(A.survey_end_year(2023), 2022)
        self.assertEqual(A.survey_label(2009), "2005-2009")

    def test_tract_vintage(self):
        self.assertEqual(A.tract_vintage(2009), "2000")
        self.assertEqual(A.tract_vintage(2010), "2010")
        self.assertEqual(A.tract_vintage(2019), "2010")
        self.assertEqual(A.tract_vintage(2022), "2020")

    def test_dollars(self):
        self.assertAlmostEqual(A.to_2024_dollars(100.0, 2024), 100.0)
        self.assertAlmostEqual(A.to_2024_dollars(100.0, 2010), 100.0 * 313.689 / 218.056)


class TestVariables(unittest.TestCase):
    def test_count_ids_and_groups(self):
        self.assertTrue(60 <= len(A.ALL_IDS) <= 100)
        self.assertEqual(len(A.ALL_IDS), len(set(A.ALL_IDS)))
        self.assertEqual({v["group"] for v in A.VARIABLES}, {"housing stock", "housing costs", "people and households", "mobility", "place"})

    def test_no_race_or_ethnicity(self):
        self.assertFalse([t for t in A.tables_used() if A.RACE_TABLE.match(t)])
        self.assertTrue(A.RACE_TABLE.match("B02001") and A.RACE_TABLE.match("B03002") and A.RACE_TABLE.match("B19013H"))
        for v in A.VARIABLES:
            self.assertNotRegex(v["label"].lower(), r"race|hispanic|latino|white|black|asian")

    def test_negative_lines(self):
        self.assertEqual(A.resolve_line(-1, 10), 10)
        self.assertEqual(A.resolve_line(-7, 11), 5)
        self.assertEqual(A.resolve({"B25034_-1": 1.0, "B25034_1": 1.0}, {"B25034": 11}), {"B25034_11": 1.0, "B25034_1": 1.0})

    def test_b23001_lines(self):
        lf = A._b23001("in_lf")
        self.assertEqual(lf[:2], [4, 11])
        self.assertEqual(lf[9:13], [67, 74, 79, 84])
        self.assertEqual(lf[13], 90)
        self.assertEqual(lf[-1], 170)
        self.assertEqual(A._b23001("unemp")[-1], 172)


def cells_fixture(ncells_b25034: int) -> pd.DataFrame:
    """Two tracts with every cell 0 except the ones the checks below set."""
    cols = {}
    lens = {t: 200 for t in A.tables_used()}
    lens["B25034"] = ncells_b25034
    for t, n in lens.items():
        for ln in range(1, n + 1):
            cols[f"{t}_{ln}"] = [0.0, 0.0]
    c = pd.DataFrame(cols, index=["t1", "t2"])
    c["B25024_1"], c["B25024_2"] = [100.0, 300.0], [50.0, 30.0]           # 50% and 10% detached
    c["B25034_1"] = [100.0, 100.0]
    c[f"B25034_{ncells_b25034}"] = [40.0, 10.0]                           # built 1939 or earlier
    c["B25064_1"] = [1000.0, -666666666.0]                               # second tract: jam value
    c["B25035_1"] = [1950.0, 1990.0]
    c["ALAND_SQMI"] = [1.0, 2.0]
    c["B25001_1"] = [1000.0, 1000.0]
    return c, lens


class TestTractAndUnit(unittest.TestCase):
    def setUp(self):
        self.cells, self.lens = cells_fixture(10)
        self.parts = A.tract_parts(self.cells, self.lens, 2010)

    def test_ratio_of_weighted_sums(self):
        lots = pd.DataFrame({"tract": ["t1", "t2"], "acres": [1.0, 1.0]})
        v = A.unit_values(lots, self.parts)
        self.assertAlmostEqual(v["h01_share_1unit_detached"], 80 / 400)      # not the mean of 0.5 and 0.1
        self.assertAlmostEqual(v["h12_share_built_pre1940"], 50 / 200)
        self.assertAlmostEqual(v["h08_share_built_2000_on"], 150 / 200)      # total minus the older lines (all zero but pre-1940)
        self.assertAlmostEqual(v["l01_homes_per_sqmi"], 2000 / 3)

    def test_medians_dollars_and_jams(self):
        lots = pd.DataFrame({"tract": ["t1", "t2", "t2"], "acres": [1.0, 2.0, 1.0]})
        v = A.unit_values(lots, self.parts)
        self.assertAlmostEqual(v["c01_median_rent"], A.to_2024_dollars(1000.0, 2010))   # jam value left out
        self.assertAlmostEqual(v["h13_median_building_age"], (60 * 1 + 20 * 3) / 4)
        self.assertAlmostEqual(v["l03_tract_land_sqmi"], (1 + 2 * 3) / 4)

    def test_newer_release_year_built(self):
        cells, lens = cells_fixture(11)
        parts = A.tract_parts(cells, lens, 2018)
        v = A.unit_values(pd.DataFrame({"tract": ["t1"], "acres": [1.0]}), parts)
        self.assertAlmostEqual(v["h12_share_built_pre1940"], 0.4)

    def test_no_tract_gives_missing(self):
        v = A.unit_values(pd.DataFrame({"tract": ["zz"], "acres": [1.0]}), self.parts)
        self.assertTrue(np.isnan(v["h01_share_1unit_detached"]))

    def test_entered(self):
        vals = pd.DataFrame({k: [np.e] for k in A.ALL_IDS})
        x = A.entered(vals)
        self.assertAlmostEqual(x["c01_median_rent"].iloc[0], 1.0)
        self.assertAlmostEqual(x["h01_share_1unit_detached"].iloc[0], np.e)
        self.assertAlmostEqual(x["n01_island_acres"].iloc[0], np.log(np.e + 1))


def synthetic_units(seed: int = 0, signal: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for c in T.WIDE_FIT_CITIES + T.TEST_CITIES:
        for i in range(8):
            x1, x2 = rng.normal(), rng.normal()
            eff = (1.5 * x1 if signal else 0.0) + rng.normal(scale=0.3)
            dc = rng.normal(scale=0.1)
            rows.append({"unit_id": f"{c}_{i}", "city": c, "effect": eff, "weight": float(rng.uniform(5, 50)),
                         "comparison_acres": float(rng.uniform(5, 50)), "d_treat": eff + dc, "d_comp": dc,
                         "v_a": x1, "v_b": x2 if i else np.nan, "v_const": 1.0})
    return pd.DataFrame(rows)


class TestModels(unittest.TestCase):
    def test_city_splits_inside_training(self):
        s = A.city_splits(np.array(["a", "a", "b", "c"]))
        self.assertEqual(len(s), 3)
        for tr, te in s:
            self.assertEqual(len(set(tr) & set(te)), 0)

    def test_baseline_equals_weighted_mean(self):
        d = synthetic_units()
        e = A.heldout(d, "baseline", [])
        self.assertTrue(np.allclose(e["error_model"], e["error_baseline"]))
        self.assertEqual(set(e["role"]), {"fold", "always held out"})

    @unittest.skipUnless(HAS_SKLEARN, "ml extra not installed")
    def test_models_run_and_judge(self):
        d = synthetic_units(signal=True)
        for m in ("lasso", "elastic_net", "forest", "boosting"):
            e = A.heldout(d, m, ["v_a", "v_b", "v_const"])
            self.assertEqual(len(e), 8)
            j = T.judge_tools(e)
            self.assertIn(j["verdict"], ("pass", "fail"))
        # a strong signal on one variable: the linear models should beat the plain average
        self.assertEqual(T.judge_tools(A.heldout(d, "lasso", ["v_a", "v_b"]))["verdict"], "pass")

    def test_causal_forest_runs(self):
        d = synthetic_units(signal=True)
        tr, te = d[d["city"] != "Chicago"], d[d["city"] == "Chicago"]
        p, _ = A.predict("causal_forest", tr, te, ["v_a", "v_b"])
        self.assertEqual(len(p), len(te))
        self.assertTrue(np.isfinite(p).all())

    def test_largest_units(self):
        d = synthetic_units()
        ix = A.largest_units(d)
        self.assertEqual(len(ix), len(T.WIDE_FIT_CITIES))
        for i in ix:
            c = d.loc[i, "city"]
            self.assertEqual(d.loc[i, "weight"], d[d["city"] == c]["weight"].max())

    def test_robust_seeds_fixed(self):
        self.assertEqual(A.ROBUST_SEEDS, (20261028, 20261029, 20261030, 20261031, 20261032))
        self.assertEqual(A.ROBUST_SEEDS_NEEDED, 4)


class TestOutputs(unittest.TestCase):
    @unittest.skipUnless((REF / "tod_allvars_values.csv").exists(), "values not built")
    def test_values(self):
        v = pd.read_csv(REF / "tod_allvars_values.csv")
        self.assertFalse(T.check_private(v, allowed={"t02_lot_size"}))
        self.assertTrue(set(A.ALL_IDS) <= set(v.columns))
        self.assertFalse([c for c in v.columns if any(w in c.lower() for w in ("race", "hispanic", "white", "black", "asian"))])
        m = pd.read_csv(REF / "tod_allvars_variable_map.csv")
        self.assertEqual(list(m["variable_id"]), A.ALL_IDS)

    @unittest.skipUnless((REF / "tod_allvars_models.csv").exists(), "models not run")
    def test_models_file(self):
        m = pd.read_csv(REF / "tod_allvars_models.csv")
        self.assertFalse(T.check_private(m))
        self.assertEqual(len(m), len(A.MODELS))
        fails = m[m["verdict"] == "fail"]
        self.assertTrue(fails["detail"].str.contains("not shown").all())


if __name__ == "__main__":
    unittest.main()
