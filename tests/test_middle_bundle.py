"""Checks the middle housing bundle (ui/public/scenarios/middle/) against the committed reference files.

Offline. Rebuild with: uv run python scripts/build_middle_bundle.py
"""
import json
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "ui" / "public" / "scenarios" / "middle" / "runs"
REF = ROOT / "reference"
CORE_MANIFEST_KEYS = {"run_id", "scenario_id", "title", "outcome", "dates", "vintages", "validation", "repo_url", "inputs"}


class MiddleBundleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run_id = json.loads((RUNS / "latest.json").read_text())["run_id"]
        cls.dir = RUNS / run_id
        cls.manifest = json.loads((cls.dir / "manifest.json").read_text())
        cls.sw = json.loads((cls.dir / "statewide.json").read_text())
        cls.areas = json.loads((cls.dir / "areas.json").read_text())
        cls.lines = pd.read_csv(REF / "middle_model_lines_2027_2031.csv").set_index("kind")

    def test_manifest_core_keys_and_input_hashes(self):
        import hashlib
        self.assertLessEqual(CORE_MANIFEST_KEYS, set(self.manifest))
        self.assertEqual(self.manifest["scenario_id"], "middle")
        for i in self.manifest["inputs"]:
            self.assertEqual(hashlib.sha256((ROOT / i["path"]).read_bytes()).hexdigest(), i["sha256"], i["path"])

    def test_core_matches_reference(self):
        for k in ("lower", "central", "upper"):
            self.assertAlmostEqual(self.sw["core"][k], self.lines.loc["core_2_4", k], delta=1)
            self.assertAlmostEqual(sum(y[k] for y in self.sw["core"]["by_year"]), self.sw["core"][k], delta=2)
        self.assertLess(self.sw["core"]["lower"], self.sw["core"]["central"])
        self.assertLess(self.sw["core"]["central"], self.sw["core"]["upper"])

    def test_side_measures_carry_the_noise_caveat(self):
        ids = {s["id"] for s in self.sw["side_measures"]}
        self.assertEqual(ids, {"1_4", "1_6", "all"})
        for s in self.sw["side_measures"]:
            self.assertTrue(s["caveat"].startswith("Too noisy to include in predicted range"))
            self.assertAlmostEqual(s["central"], self.lines.loc[{"1_4": "side_1_4", "1_6": "side_1_6", "all": "side_all"}[s["id"]], "central"], delta=1)

    def test_areas_add_up_to_statewide(self):
        self.assertEqual(sum(a["sf_homes"] for a in self.areas), 1_839_569)
        for k in ("lower", "central", "upper"):
            self.assertAlmostEqual(sum(a[k] for a in self.areas), self.sw["core"][k], delta=5)

    def test_slow_start_first_year(self):
        by = {y["year"]: y["central"] for y in self.sw["core"]["by_year"]}
        self.assertAlmostEqual(by[2027] / by[2028], -0.2136, places=3)
        self.assertEqual(by[2028], by[2031])


if __name__ == "__main__":
    unittest.main()
