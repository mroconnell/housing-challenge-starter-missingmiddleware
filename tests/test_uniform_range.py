"""The uniform range display (docs/UNIFORM_DISPLAY_SPEC.md): TOD's 90% range and side lines in its bundle equal the
reference files, the ADU bundle carries the fields the screens read, and the UI's all-housing baseline constant equals
the shared baseline."""
import json
import re
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference"
TOD = ROOT / "ui" / "public" / "scenarios" / "tod" / "runs"
ADU = ROOT / "ui" / "public" / "runs"


def latest(root: Path) -> Path:
    return root / json.loads((root / "latest.json").read_text())["run_id"]


@unittest.skipUnless((TOD / "latest.json").exists(), "TOD bundle not built")
class TestTodRange(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sw = json.loads((latest(TOD) / "statewide.json").read_text())
        cls.R = cls.sw["range90"]

    def test_ends_are_the_widened_draws(self):
        cov = pd.read_csv(REF / "tod_coverage_test.csv").set_index("measure")
        wr = cov.loc["widened Wisconsin 90% range"]
        f = float(cov.loc["widening factor f", "value"])
        self.assertEqual(round(self.R["low"]), 3922)
        self.assertEqual(round(self.R["high"]), 16335)
        self.assertAlmostEqual(self.R["low"], wr["lo90"], delta=0.1)
        self.assertAlmostEqual(self.R["high"], wr["hi90"], delta=0.1)
        d = pd.read_csv(REF / "tod_line_draws.csv")["central_homes"]
        w = wr["value"] + f * (d - wr["value"])          # the CSV's rounded factor gives the same ends within 1 home
        self.assertAlmostEqual(float(np.percentile(w, 5)), self.R["low"], delta=1)
        self.assertAlmostEqual(float(np.percentile(w, 95)), self.R["high"], delta=1)
        self.assertIn("1.1827", self.R["method"])
        self.assertIn("84.5%", self.R["coverage"])
        self.assertIn("69%", self.R["coverage"])
        self.assertEqual(self.R["unit"], "extra homes permitted near major transit stops, Wisconsin, 2027–2031")

    def test_yearly_band_follows_the_central_profile(self):
        typ = next(s for s in self.sw["scenarios"] if s["id"] == "typical")
        tot = sum(typ["by_year"])
        self.assertEqual([y["year"] for y in self.R["years"]], [2027, 2028, 2029, 2030, 2031])
        for y, v in zip(self.R["years"], typ["by_year"]):
            self.assertAlmostEqual(y["low"], self.R["low"] * v / tot, delta=0.05)
            self.assertAlmostEqual(y["high"], self.R["high"] * v / tot, delta=0.05)
        # each end's yearly values add up to the five-year end (AQ-080: year 2's share is negative as measured)
        self.assertAlmostEqual(sum(y["low"] for y in self.R["years"]), self.R["low"], delta=0.1)
        self.assertAlmostEqual(sum(y["high"] for y in self.R["years"]), self.R["high"], delta=0.1)

    def test_side_lines_match_reference(self):
        want = {"average": ("tod_optiond_line.csv", "optiond_average", 10028), "edge": ("tod_causal_lines.csv", "causal_lower_edge", 3958),
                "scaled15": ("tod_causal_lines.csv", "upper_average_scaled_15", 12521),
                "new_lines_2x2": ("tod_causal_lines.csv", "causal_upper_2x2", 13451),
                "new_lines_trend": ("tod_causal_lines.csv", "whatif_2x2_trend_adjusted", 5624)}
        got = {s["id"]: s for s in self.sw["side_lines"]}
        self.assertEqual(list(got), list(want))
        for k, (f, line, shown) in want.items():
            v = pd.read_csv(REF / f).set_index("line").loc[line, "extra_homes_2027_2031"]
            self.assertAlmostEqual(got[k]["value"], v, delta=0.05)
            self.assertEqual(round(got[k]["value"]), shown)
            self.assertEqual(got[k]["where"], "chart")
            self.assertTrue(got[k]["label"] and got[k]["note"])
        self.assertEqual(got["average"]["label"], "Average district place, 11 places (the former central)")

    def test_record_check_at_high_end_scales_the_central_line(self):
        ck = pd.read_csv(REF / "tod_model_checks.csv")
        ck = ck[(ck["check"] == "scale") & (ck["sizing"] == "net_effect") & (ck["scenario"] == "typical")]
        typ = next(s for s in self.sw["scenarios"] if s["id"] == "typical")["additional_total"]
        for row in self.R["record_check_high"]:
            g = ck[ck["metro"].str.startswith(row["metro"].split(" ")[0])]
            tot = g["baseline_per_1000"] + g["extra_per_1000"] * self.R["high"] / typ
            self.assertAlmostEqual(row["peak_total_per_1000"], tot.max(), delta=0.01)


@unittest.skipUnless((ADU / "latest.json").exists(), "ADU bundle not built")
class TestAduRangeFields(unittest.TestCase):
    def test_adu_bundle_has_the_fields_the_screens_read(self):
        s = json.loads((latest(ADU) / "state.json").read_text())
        R = s["range90"]
        self.assertEqual((R["low"], R["high"]), (8055.0, 13666.0))
        for k in ("unit", "method", "coverage", "caveat", "source"):
            self.assertTrue(R[k], k)
        self.assertEqual(len(R["years"]), 5)
        for x in s["side_lines"]:
            self.assertIn(x["where"], ("chart", "howsure"))
            self.assertTrue(("value" in x) or ("low" in x and "high" in x), x["id"])


class TestBaselineConstant(unittest.TestCase):
    def test_ui_constant_equals_shared_baseline(self):
        hb = pd.read_csv(REF / "housing_baseline_statewide_by_year.csv")
        proj = hb[(hb["kind"] == "projected") & (hb["structure_type"] == "all") & hb["year"].between(2027, 2031)]
        src = (ROOT / "ui" / "src" / "range.ts").read_text()
        m = re.search(r"ALL_HOUSING_BASELINE_2027_2031 = (\d+)", src)
        self.assertIsNotNone(m)
        self.assertAlmostEqual(int(m.group(1)), proj["central"].sum(), delta=0.5)


if __name__ == "__main__":
    unittest.main()
