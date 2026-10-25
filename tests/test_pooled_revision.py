"""Offline tests for the pooled-model input options (missing_middleware.comparison.pooled_revision)
and the single-source Madison floor (missing_middleware.model.params)."""
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.comparison import pooled_revision as R
from missing_middleware.model import params

REF = Path(__file__).parent.parent / "reference"


def jy_fixture():
    return pd.DataFrame({
        "juris_name": ["A", "A", "B"], "year": [2019, 2024, 2024],
        "adu_units": [10.0, 20.0, 5.0], "units_cap_removed": [0.0, 2.0, 0.0],
        "units_kept_on_definite": [0.0, 2.0, 0.0], "units_kept_on_possible": [1.0, 4.0, 0.0],
        "units_cap_plus_mf_lower_removed": [0.0, 4.0, 0.0]})


BANDS = pd.DataFrame({"period": ["2018-2019"] * 3 + ["2023-2025"] * 3,
                      "cband": ["definite", "possible", "single"] * 2,
                      "p_mf": [0.0, 0.02, 0.02, 0.75, 0.4, 0.2]})
FITS = pd.DataFrame({"period": ["2018-2019", "2023-2025"], "a": [0.07, 0.06], "b": [-0.1, 0.3]})


class TestCaliforniaOptions(unittest.TestCase):
    def test_cap_a2_removed(self):
        r = R.removed_cap_a2(jy_fixture())
        self.assertEqual(r["removed"].tolist(), [0.0, 4.0, 0.0])

    def test_la_calibrated_rebuild(self):
        r = R.removed_cap_la_calibrated(jy_fixture(), BANDS, FITS, pd.Series({"A": 0.5, "B": np.nan}))
        # 2019: flat line (b < 0) -> pooled single 0.02; 1 possible x 0.02 + 9 single x 0.02
        self.assertAlmostEqual(r["removed"].iloc[0], 1 * 0.02 + 9 * 0.02)
        # 2024: cap 2 + 2 x 0.75 + 4 x 0.4 + 12 x (0.06 + 0.3 x 0.5)
        self.assertAlmostEqual(r["removed"].iloc[1], 2 + 1.5 + 1.6 + 12 * 0.21)
        # no ACS share -> pooled single share
        self.assertAlmostEqual(r["removed"].iloc[2], 5 * 0.2)

    def test_adjust_panel_jurisdiction_then_statewide(self):
        panel = pd.DataFrame({"census_geoid": ["g1", "g2", "g3", "g1"], "year": [2024, 2024, 2024, 2016],
                              "adu_main": [20.0, 10.0, np.nan, 3.0], "sf_detached": [1e4] * 4})
        rem = pd.DataFrame({"census_geoid": ["g1"], "year": [2024], "removed": [4.0]})
        p = R.adjust_ca_panel(panel, rem, pd.Series({2024: 0.9}))
        self.assertEqual(p["adu_main"].iloc[0], 16.0)
        self.assertAlmostEqual(p["adu_main"].iloc[1], 9.0)            # statewide factor
        self.assertTrue(np.isnan(p["adu_main"].iloc[2]))              # missing stays missing
        self.assertEqual(p["adu_main"].iloc[3], 3.0)                  # no factor before 2018
        self.assertEqual(p["ca_adjust_basis"].tolist(), ["jurisdiction-year", "statewide factor", "unchanged", "unchanged"])

    def test_reference_cap_a2_matches_statewide_table(self):
        jy = pd.read_csv(REF / "ca_mf_lot_adu_share_by_jurisdiction.csv")
        by = pd.read_csv(REF / "ca_mf_lot_adu_share_by_year.csv")
        by = by[by["is_main_cutoff"]].set_index("year")
        s = R.removed_cap_a2(jy).groupby("year")["removed"].sum()
        for y in range(2018, 2026):
            self.assertAlmostEqual(s[y], by.loc[y, "units_cap_plus_mf_lower_removed"], places=3)


class TestOtherRows(unittest.TestCase):
    def test_vacant_lot_and_minneapolis(self):
        rows = pd.DataFrame({"cluster": ["CA", "ME", "MN", "TX"], "series": ["CA_jurisdictions", "ME_statewide", "minneapolis", "austin"],
                             "count": [100.0] * 4, "incl_new_house": [True, True, True, False]})
        r = R.adjust_other_rows(rows)
        self.assertEqual(r["count"].iloc[0], 100.0)                                   # California unchanged
        self.assertAlmostEqual(r["count"].iloc[1], 100 * 0.951)
        self.assertAlmostEqual(r["count"].iloc[2], 100 * 0.951 * 0.873)
        self.assertEqual(r["count"].iloc[3], 100.0)                                   # excludes new-house ADUs
        self.assertTrue((R.adjust_other_rows(rows, False, False)["count"] == 100).all())


class TestScoring(unittest.TestCase):
    def test_bootstrap_dominant(self):
        err = pd.DataFrame({"A": [0.1, 0.1, 0.1], "B": [0.5, 0.5, 0.5]})
        w = R.paired_bootstrap_wins(err, n=200)
        self.assertEqual(w["A"], 1.0)
        self.assertAlmostEqual(R.rms([0.3, -0.4]), np.sqrt(0.125))

    def test_madison_like_screen(self):
        pl = pd.DataFrame({"name": ["Big", "Mad", "Cheap", "Small", "Town"], "muni_type": ["city", "city", "city", "village", "town"],
                           "homes": [100_000, 53_292, 25_000, 19_999, 30_000], "value": [300_000, 372_900, 207_000, 300_000, 300_000]})
        m = R.madison_like_wi(pl).set_index("name")["madison_like"]
        self.assertEqual(m.to_dict(), {"Big": False, "Mad": True, "Cheap": False, "Small": False})


class TestFloor(unittest.TestCase):
    def test_single_source(self):
        self.assertEqual(params.madison_floor("adopted_2026_10_24"), 0.229)
        self.assertEqual(params.madison_floor("g3f_revision_2026_10_25"), 0.2345)
        spec = json.loads(params.PARAMS.read_text())
        self.assertNotIn("floor_rate", json.dumps(spec["paths"]))       # paths read the shared floor
        v = spec["madison_floor"]["variants"]["g3f_revision_2026_10_25"]
        self.assertAlmostEqual(v["numerator_units"] / v["home_years_thousands"] / v["divisor"], v["rate"], places=3)
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "p.json"
            spec["madison_floor"]["in_use"] = "g3f_revision_2026_10_25"
            p.write_text(json.dumps(spec))
            self.assertEqual(params.madison_floor(path=p), 0.2345)


if __name__ == "__main__":
    unittest.main()
