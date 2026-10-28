"""Offline tests for the ADU predictive test (docs/adu/PREDICTIVE_PLAN.md): variable formulas, unit-free feature
transforms, the 2-per-parcel cap, the plain average, unit scoring and the pass rule. No network, no data files."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_adu_predictive_panel as B  # noqa: E402
import run_adu_predictive as R  # noqa: E402


def _cells(n=3):
    cols = sorted({tok for v in B.VARIABLES for tok in __import__("re").findall(r"B\d{5}_\d{3}", __import__("inspect").getsource(v[4]))}
                  | {f"B01001_{i:03d}" for i in range(1, 50)} | {f"B15002_{i:03d}" for i in range(1, 36)}
                  | {f"B19001_{i:03d}" for i in range(1, 18)} | {f"B25044_{i:03d}" for i in range(1, 16)}
                  | {f"B08303_{i:03d}" for i in range(1, 14)} | {f"B08302_{i:03d}" for i in range(1, 16)}
                  | {f"B25075_{i:03d}" for i in range(1, 28)} | {f"B11016_{i:03d}" for i in range(1, 17)})
    c = pd.DataFrame(10.0, index=[f"place:{i}" for i in range(n)], columns=cols)
    c["land_sqmi"] = 2.0
    return c


class TestVariables(unittest.TestCase):
    def test_about_100_variables_no_race(self):
        ids = [v[0] for v in B.VARIABLES]
        self.assertGreaterEqual(len(ids), 95)
        self.assertEqual(len(ids), len(set(ids)))
        for v in B.VARIABLES:   # no race or ethnicity tables (B02, B03, lettered tables)
            self.assertNotRegex(__import__("inspect").getsource(v[4]), r"B0[23]\d{3}")

    def test_formulas(self):
        c = _cells()
        c["B25024_001"], c["B25024_002"] = 200.0, 50.0
        c["B25077_001"], c["B25064_001"] = 300000.0, 1250.0
        v = B.compute_variables(c)
        self.assertAlmostEqual(v["h01_share_1unit_detached"].iloc[0], 0.25)
        self.assertAlmostEqual(v["c14_value_to_annual_rent"].iloc[0], 20.0)
        self.assertAlmostEqual(v["l01_homes_per_sqmi"].iloc[0], 5.0)       # B25001 10 / 2 sq mi
        self.assertAlmostEqual(v["h13_median_building_age"].iloc[0], 2024 - 10)

    def test_division_by_zero_is_missing(self):
        c = _cells()
        c["B25024_001"] = 0.0
        v = B.compute_variables(c)
        self.assertTrue(v["h01_share_1unit_detached"].isna().all())


class TestTransforms(unittest.TestCase):
    def test_weighted_rank(self):
        r = B.weighted_rank(pd.Series([1.0, 2.0, 3.0, np.nan]), pd.Series([1.0, 1.0, 2.0, 1.0]))
        self.assertAlmostEqual(r.iloc[0], 0.125, places=6)
        self.assertAlmostEqual(r.iloc[2], 0.75, places=6)
        self.assertTrue(np.isnan(r.iloc[3]))

    def test_dollars_unit_free_and_aggregates_neutral(self):
        idx = ["a", "b", "c", "d"]
        vals = pd.DataFrame({"c04_median_value": [100.0, 200.0, 1000.0, 5000.0],
                             "h01_share_1unit_detached": [0.2, 0.4, 0.6, np.nan]}, index=idx)
        ctx = pd.Series(["s1", "s1", "s2", "agg"], index=idx)
        homes = pd.Series([1.0, 1.0, 1.0, 1.0], index=idx)
        f = B.transform_features(vals, ctx, homes, pd.Series([False, False, False, True], index=idx))
        self.assertNotIn("c04_median_value", f.columns)            # never the raw dollar level
        self.assertIn("c04_median_value__rank", f.columns)
        self.assertAlmostEqual(f.loc["c", "c04_median_value__logratio"], 0.0)   # alone in its context
        self.assertAlmostEqual(f.loc["d", "c04_median_value__rank"], 0.5)        # aggregate row
        self.assertAlmostEqual(f.loc["d", "c04_median_value__logratio"], 0.0)
        self.assertAlmostEqual(f.loc["b", "c04_median_value__logratio"], np.log(200) - np.log(np.sqrt(100 * 200)))
        self.assertAlmostEqual(f.loc["a", "h01_share_1unit_detached"], 0.2)      # shares enter as they are


class TestOutcome(unittest.TestCase):
    def test_cap_two_per_parcel(self):
        d = pd.DataFrame({"parcel": ["A", "A", "A", "B", None], "units": [1, 1, 1, 3, 2],
                          "issue_date": pd.to_datetime(["2020-01-01", "2021-01-01", "2022-01-01", "2020-01-01", "2020-01-01"])})
        k = B.cap_per_parcel(d, "parcel", "units")
        self.assertEqual(k.tolist(), [1, 1, 0, 2, 2])

    def test_coding(self):
        self.assertEqual(B.TRACT_CODING["seattle"][2024], (1, 1, 2))
        self.assertNotIn(2019, B.TRACT_CODING["seattle"])          # reform year dropped, as adopted
        self.assertNotIn(2024, B.TRACT_CODING["denver"])           # partial law year dropped
        self.assertEqual(B.AGG_CODING["RI_statewide"][2][2025], (1, 0, 1))
        self.assertEqual(B.WA_CODING[2026], (1, 0, 3))
        self.assertEqual(B.STRONG & B.WEAKER, set())

    def test_run2_coding(self):
        # AQ-061: Washington from local compliance (EY2024-2025 dropped, EY2026 = year 1)
        self.assertEqual(B.WA_CODING_AQ061[2026], (1, 0, 1))
        self.assertNotIn(2024, B.WA_CODING_AQ061)
        self.assertNotIn(2025, B.WA_CODING_AQ061)
        # local strength (PLAN s10 item 9): reform counts from its effective year if by 1 April, else the next year
        ls = B.LOCAL_STRENGTH
        self.assertEqual(ls["seattle"][2018], (1, 4))
        self.assertEqual(ls["seattle"][2020], (3, 1))              # Ord. 125854 2019-08-08 -> 2020
        self.assertEqual(ls["seattle"][2024], (3, 4))
        self.assertEqual(ls["minneapolis"][2017], (1, 3))          # 2014-12-05 -> 2015
        self.assertEqual(ls["minneapolis"][2021], (2, 1))          # 2021-02-26 (by 1 April)
        self.assertEqual(ls["madison"][2022], (2, 1))              # 2021-12-16 -> 2022
        self.assertEqual(ls["madison"][2025], (3, 1))              # 2024-04-25 -> 2025
        self.assertEqual(ls["denver"][2023], (0, 0))
        self.assertEqual(ls["denver"][2025], (2, 1))
        self.assertEqual(ls["austin"][2019], (2, 4))
        self.assertEqual(ls["portland"][2020], (3, 1))
        for city, years in B.TRACT_CODING.items():                 # strength 0 exactly where the adopted local = 0
            for y, (law, local, k) in years.items():
                self.assertEqual(ls[city][y][0] > 0, local == 1, (city, y))

    def test_manifest_never_records_key(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "x.json"
            p.write_text("{}")
            with self.assertRaises(AssertionError):
                B._record(Path(t), "x.json", "https://api.census.gov/data?get=X&key=abc")
            B._record(Path(t), "x.json", "https://api.census.gov/data?get=X")
            self.assertNotIn("key=", (Path(t) / "_downloads.json").read_text())


class TestMethodsAndRule(unittest.TestCase):
    def test_plain_average_equal_state_weights(self):
        tr = pd.DataFrame({"cluster": ["A", "A", "B"], "law": [1, 1, 1], "count": [10.0, 0.0, 1.0],
                           "homes": [1000.0, 9000.0, 1000.0]})
        te = pd.DataFrame({"law": [1, 0]})
        p = R.plain_average(tr, te)
        self.assertAlmostEqual(p[0], (1.0 + 1.0) / 2)                 # A: 10/10k = 1.0; B: 1/1k = 1.0
        self.assertEqual(p[1], 0.0)                                   # no no-law training rows

    def test_score_unit(self):
        g = pd.DataFrame({"geo": ["t1", "t1", "t2"], "homes": [1000.0, 1000.0, 1000.0], "rate": [2.0, 0.0, 1.0],
                          "m": [1.0, 1.0, 1.0]})
        s = R.score_unit(g, ["m"])
        # t1 observed 1.0, t2 observed 1.0; predictions 1.0 each -> rate miss 0; shares equal -> where miss 0
        self.assertAlmostEqual(s["rate_miss__m"], 0.0)
        self.assertAlmostEqual(s["where_miss__m"], 0.0)
        g["m"] = [2.0, 2.0, 0.0]
        s = R.score_unit(g, ["m"])
        self.assertAlmostEqual(s["rate_miss__m"], 1.0)
        # observed shares 2/3 (t1, 2 permits) and 1/3 (t2, 1 permit); predicted 1 and 0 -> 1/3 of permits misplaced
        self.assertAlmostEqual(s["where_miss__m"], 1 / 3)

    def test_pass_rule(self):
        units = [f"u{i}" for i in range(7)]
        bu = pd.DataFrame({"test": "1_how_much", "unit": units, "miss__plain_average": 1.0,
                           "miss__current_model": 0.5, "miss__guess_zero": 2.0,
                           "miss__causal_forest": [0.4, 0.4, 0.4, 0.4, 0.6, 0.6, 0.6],     # wins 4 of 7, mean 0.486
                           "miss__boosted_trees": [0.1, 0.1, 0.1, 2.0, 2.0, 2.0, 2.0],     # wins 3: fails
                           "miss__regularised_regression": 0.49})
        j = R.judge(bu).set_index("method")
        self.assertTrue(j.loc["causal_forest", "passes"])
        self.assertFalse(j.loc["boosted_trees", "passes"])
        self.assertTrue(j.loc["regularised_regression", "passes"])

    def test_strength_columns(self):
        rows = pd.DataFrame({"law": [1, 0], "local": [1.0, 0.0], "k": [2.0, np.nan], "strong": [1, 0],
                             "local_strength": [3, 0], "local_years": [2, 0]})
        old = R.STRENGTH
        try:
            R.STRENGTH = True
            self.assertEqual(R.treat_cols(rows, "law").shape, (2, 9))
            self.assertEqual(R.treat_cols(rows, "nolaw")[0].tolist(), [1.0, 3.0, 0.0, 1.0, 0.0])
            R.STRENGTH = False
            self.assertEqual(R.treat_cols(rows, "law").shape, (2, 5))
        finally:
            R.STRENGTH = old

    def test_design_wrapper_adds_strength_terms(self):
        m = pd.DataFrame({"value": [1e5, 2e5], "law": [1.0, 0.0], "k": [1.0, np.nan], "local": [1, 0],
                          "local_strength": [2.0, 0.0], "ly1": [1.0, 0.0], "ly2": 0.0, "ly3": 0.0})
        X, names = R.pr.design(m, ("law", "local", "local_strength", "ly1"))
        self.assertEqual(names, ["intercept", "law", "local", "local_strength", "ly1"])
        self.assertEqual(X[:, 3].tolist(), [2.0, 0.0])

    def test_home_years_rate(self):
        tr = pd.DataFrame({"cluster": ["A"], "law": [1], "count": [11.0], "homes": [1000.0], "years": [11 / 12]})
        self.assertAlmostEqual(R.plain_average(tr, pd.DataFrame({"law": [1]}))[0], 12.0)

    def test_two_part_uses_law_status(self):
        rows = pd.DataFrame({"law": [1] * 40 + [0] * 40, "local": 0.0, "k": [4.0] * 40 + [np.nan] * 40,
                             "strong": [1] * 40 + [0] * 40, "cluster": (["A", "B"] * 40), "homes": 1000.0,
                             "rate": [2.0] * 40 + [0.2] * 40})
        F = np.zeros((80, 2))
        tp = R.TwoPart("causal_forest").fit(rows, F)
        p = tp.predict(rows, F)
        self.assertAlmostEqual(float(p[:40].mean()), 2.0, places=6)
        self.assertAlmostEqual(float(p[40:].mean()), 0.2, places=6)


if __name__ == "__main__":
    unittest.main()
