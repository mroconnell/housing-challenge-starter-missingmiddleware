"""Offline tests for the pre-registered California comparison study (ca_study.py).

Fixture tests/fixtures/ca_study/apr_adu_rows_tiny.csv is invented: it mimics the
de-identified rows of ca_inputs.classify_permit_rows plus a free-text column.
"""
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.comparison import ca_study as S

FX = Path(__file__).parent / "fixtures" / "ca_study"
ROOT = Path(__file__).resolve().parent.parent


def _rows():
    r = pd.read_csv(FX / "apr_adu_rows_tiny.csv", dtype={"text": str})
    r["year"] = r["year"].astype("Int64")
    r["bp_issue_year"] = r["bp_issue_year"].astype("Int64")
    return r.drop(columns="text"), S.classify_adu_text(r["text"])


def _panel(spec_rows):
    """Synthetic panel: rows of (geoid, homes, holdout, {year: adu or None})."""
    out = []
    for geo, homes, hold, vals in spec_rows:
        for y in S.YEARS:
            v = vals.get(y, 0.0)
            out.append({"census_geoid": geo, "year": y, "sf_detached": float(homes), "in_holdout": hold,
                        "adu_main": np.nan if v is None else float(v), "name": geo})
    p = pd.DataFrame(out)
    p["adu_issue"] = p["adu_main"]
    p["adu_comp1819"] = p["adu_main"]
    return p


class TestOutcome(unittest.TestCase):
    def test_text_rules(self):
        t = pd.Series(["Legalize garage conversion", "new SFD with ADU", "ADU in apartment complex",
                       "detached ADU", "JADU", None, "abate code enforcement case"])
        self.assertEqual(list(S.classify_adu_text(t)),
                         ["legalization", "new_house", "multifamily_lot", "kept", "kept", "kept", "legalization"])

    def test_outcome_measures(self):
        rows, flag = _rows()
        o, exc = S.hcd_adu_outcome(rows, flag)
        o = o.set_index(["juris_name", "year"])
        # ALPHA 2018: k1 kept; k2 legalization excluded
        self.assertEqual(o.loc[("ALPHA", 2018), "adu_main"], 1)
        self.assertEqual(o.loc[("ALPHA", 2018), "adu_main_unadjusted"], 2)
        # ALPHA 2019 main: k3 (2) + undated k5 (1); k2 repeat and k4 earlier date dropped; SFD ignored
        self.assertEqual(o.loc[("ALPHA", 2019), "adu_main"], 3)
        # issue year: k4 (2017) is outside 2018-2025; k2 excluded at key level (its 2019 listing has no text)
        self.assertEqual(o.loc[("ALPHA", 2018), "adu_issue"], 1)
        self.assertEqual(o.loc[("ALPHA", 2019), "adu_issue"], 3)
        # BETA: new house and multifamily excluded, JADU kept
        self.assertEqual(o.loc[("BETA", 2018), "adu_main"], 0)
        self.assertEqual(o.loc[("BETA", 2019), "adu_main"], 1)
        self.assertEqual(int(exc[exc.year == 2019]["multifamily_lot"].iloc[0]), 3)
        self.assertNotIn("text", o.reset_index().columns)

    def test_build_panel_missing_and_sources(self):
        rows, flag = _rows()
        o, _ = S.hcd_adu_outcome(rows, flag)
        comp = pd.DataFrame({"juris_name": ["ALPHA"] * 8 + ["BETA"] * 8, "year": list(range(2012, 2020)) * 2,
                             "adu_permits": [1] * 8 + [0] * 8, "value_status": "observed"})
        filing = pd.DataFrame({"census_geoid": ["A", "A", "B"], "year": [2018, 2019, 2019], "filing_status": ["a2_rows"] * 3})
        xw = pd.DataFrame({"juris_name": ["ALPHA", "BETA"], "census_geoid": ["A", "B"], "juris_type": "city",
                           "in_holdout": [False, True], "bps_may_include_cities": False})
        den = pd.DataFrame({"geoid": ["A", "B"], "sf_detached": [1000.0, 500.0], "name": ["Alpha", "Beta"]})
        p = S.build_panel(o, comp, filing, xw, den).set_index(["census_geoid", "year"])
        self.assertEqual(p.loc[("A", 2017), "adu_main"], 1)          # compilation through 2017
        self.assertEqual(p.loc[("A", 2019), "adu_main"], 3)          # HCD from 2018
        self.assertEqual(p.loc[("A", 2019), "adu_comp1819"], 1)      # compilation sensitivity
        self.assertTrue(np.isnan(p.loc[("B", 2018), "adu_main"]))    # not filed: missing, not zero
        self.assertTrue(np.isnan(p.loc[("A", 2020), "adu_main"]))
        self.assertTrue(bool(p.loc[("B", 2019), "in_holdout"]))


class TestGroupsAndStats(unittest.TestCase):
    def setUp(self):
        hi = {y: 10 for y in S.YEARS}
        self.panel = _panel([
            ("P1", 1000, False, {**hi}),                                     # permissive
            ("P2", 1000, False, {**{y: 5 for y in S.YEARS}, 2024: None}),     # permissive, one missing post year
            ("M1", 1000, False, {2017: 1, 2018: 0, 2019: 1, 2023: 2, 2024: 2, 2025: 2}),
            ("M2", 2000, False, {2018: 1, 2025: 4}),
            ("R1", 1000, False, {2021: 1, 2023: 1, 2024: 1, 2025: 1}),        # restrictive
            ("R2", 1000, False, {2023: 2, 2024: 2, 2025: 2}),
            ("X1", 1000, False, {2018: None}),                                # excluded (missing pre year)
            ("H1", 1000, True, {2017: 0, 2018: 0, 2019: 0, 2023: 3, 2024: 3, 2025: 3}),  # holdout restrictive
            ("H2", 500, True, {y: 10 for y in S.YEARS}),                       # holdout permissive
        ])
        self.res = S.run_spec(self.panel, S.Spec("t", top_share=0.25))

    def test_groups(self):
        g = self.res["groups"][3]
        self.assertEqual(g["P1"], "permissive")
        self.assertEqual(g["R1"], "restrictive")
        self.assertEqual(g["R2"], "restrictive")
        self.assertEqual(g["X1"], "excluded_missing")
        self.assertIn(g["M1"], ("middle",))
        self.assertNotIn("H1", g.index)      # holdout never in fitting groups
        # ceil(0.25 * 6 complete) = 2 -> P1, P2 are the top two
        self.assertEqual(g["P2"], "permissive")

    def test_missing_is_not_zero_in_stats(self):
        st = self.res["stats"][3]
        # P2 missing in 2024: permissive 2024 rate is P1 alone (10 per 1,000)
        self.assertAlmostEqual(st["permissive_y2024"], 10.0)
        ev = self.res["event"].set_index(["wave", "group", "year"])
        self.assertAlmostEqual(ev.loc[(3, "permissive", 2024), "rate_pooled"], 10.0)
        # restrictive plateau: (1+2)*3 / (2000*3) * 1000 = 1.5
        self.assertAlmostEqual(st["restrictive_plateau"], 1.5)
        self.assertAlmostEqual(st["ramp_k2"], (1 / 2000 * 1000) / 1.5)
        self.assertAlmostEqual(st["did_restrictive_minus_permissive"],
                               st["restrictive_change"] - st["permissive_change"])

    def test_bootstrap_reproducible(self):
        b1 = S.bootstrap(self.res, n_boot=50)[3]
        b2 = S.bootstrap(self.res, n_boot=50)[3]
        pd.testing.assert_frame_equal(b1, b2)
        lo, hi = S.interval(b1, "restrictive_plateau")
        self.assertLessEqual(lo, 1.5)
        self.assertGreaterEqual(hi, 1.5)

    def test_holdout_uses_non_holdout_curve(self):
        glev, j, mets, counts = S.holdout_test(self.panel, self.res, n_boot=50)
        j = j.set_index("census_geoid")
        self.assertEqual(j.loc["H1", "group"], "restrictive")
        self.assertEqual(j.loc["H2", "group"], "permissive")
        ev = self.res["event"]
        curve = ev[(ev.wave == 3) & (ev.group == "restrictive") & ev.year.isin(S.WAVE3.post)]["rate_pooled"].mean()
        self.assertAlmostEqual(j.loc["H1", "pred_curve_rate"], curve)
        self.assertEqual(set(mets["predictor"]), {"curve", "persist"})


class TestShareModel(unittest.TestCase):
    def test_share_and_wi_volume(self):
        row = pd.Series({"adu": 20.0, "bps_total": 80.0})
        v = S.wi_share_volume(row, wi_bps_total=40.0, wi_homes=1000.0)
        same = v[v.overlap_s_ca == v.overlap_s_wi]
        # equal overlap in both states cancels: A_WI = B_WI * A/B = 10
        self.assertTrue(np.allclose(same["wi_adu_per_year"], 10.0))
        s0 = v[(v.overlap_s_ca == 0) & (v.overlap_s_wi == 0)].iloc[0]
        self.assertAlmostEqual(s0["ca_share"], 20 / 100)
        self.assertGreater(v["wi_adu_per_year"].max(), 10.0)
        self.assertLess(v["wi_adu_per_year"].min(), 10.0)

    def test_share_model_excludes_holdout_and_flagged(self):
        p = _panel([("A", 1000, False, {2023: 10}), ("B", 1000, True, {2023: 99}), ("C", 1000, False, {2023: 50})])
        bps = pd.DataFrame({"census_geoid": ["A", "B", "C"], "year": 2023, "bps_total": [90.0, 1.0, 1.0],
                            "bps_1unit": 0.0, "bps_months_min": 12})
        xw = pd.DataFrame({"census_geoid": ["A", "B", "C"], "bps_may_include_cities": [False, False, True]})
        sh = S.share_model(p, bps, xw).set_index("period")
        self.assertEqual(sh.loc["2023", "adu"], 10)
        self.assertAlmostEqual(sh.loc["2023", "share_s0.00"], 10 / 100)


class TestPublishedOutputs(unittest.TestCase):
    def test_doc_matches_outputs(self):
        ref = ROOT / "reference" / "ca_study_wave_stats.csv"
        study = ROOT / "data" / "processed" / "comparison_ca" / "study" / "holdout_jurisdictions.csv"
        if not (ref.exists() and study.exists()):
            self.skipTest("study outputs not built")
        self.assertEqual(S.update_doc(check=True), [])

    def test_reference_has_no_jurisdiction_or_text_fields(self):
        for f in (ROOT / "reference").glob("ca_study_*.csv"):
            cols = set(pd.read_csv(f, nrows=1).columns)
            self.assertFalse(cols & {"census_geoid", "juris_name", "NOTES", "notes", "text", "permit_key"}, f.name)
            self.assertNotIn("in_holdout", cols)


if __name__ == "__main__":
    unittest.main()
