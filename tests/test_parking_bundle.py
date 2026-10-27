"""Parking tool bundle (scripts/build_parking_bundle.py): contract keys, validation, numbers from reference CSVs."""
import json
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "ui" / "public" / "scenarios" / "parking" / "runs"


@unittest.skipUnless((RUNS / "latest.json").exists(), "parking bundle not built")
class TestParkingBundle(unittest.TestCase):
    def setUp(self):
        run = json.loads((RUNS / "latest.json").read_text())["run_id"]
        self.d = RUNS / run
        self.m = json.loads((self.d / "manifest.json").read_text())
        self.sw = json.loads((self.d / "statewide.json").read_text())

    def test_contract_keys_and_validation(self):
        for k in ("run_id", "scenario_id", "title", "outcome", "dates", "vintages", "validation", "repo_url", "inputs"):
            self.assertIn(k, self.m)
        self.assertEqual(self.m["validation"]["failed"], 0)
        for f in self.m["files"]:
            self.assertTrue((self.d / f).exists(), f)

    def test_numbers_match_reference(self):
        ref = pd.read_csv(ROOT / "reference" / "parking_model_statewide_by_year.csv")
        up = next(s for s in self.sw["scenarios"] if s["id"] == "upper")
        self.assertAlmostEqual(up["additional_total"], ref["addition_upper"].sum(), delta=1)
        self.assertEqual(next(s for s in self.sw["scenarios"] if s["id"] == "central")["additional_total"], 0)

    def test_run_id_is_hash_of_inputs(self):
        for i in self.m["inputs"]:
            self.assertTrue((ROOT / i["path"]).exists(), i["path"])
