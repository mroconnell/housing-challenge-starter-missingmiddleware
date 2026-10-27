"""Checks the reform registry used by the multi-reform tool shell (docs/shared/SCENARIO_CONTRACT.md).

Offline: reads ui/src/scenarios/registry.json and the committed bundles under ui/public/.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "ui" / "src" / "scenarios" / "registry.json"
PUBLIC = ROOT / "ui" / "public"
# first path segments the ADU screens use; a reform id must never equal one of them (URL prefixes would collide)
ADU_SEGMENTS = {"today", "compare", "where", "how-sure", "why", "pilot", "brief"}
# Reforms that are not a challenge benchmark, so their `benchmark` is a short plain description, not spec text.
# `combined` is TOD and parking together (docs/shared/SCENARIO_CONTRACT.md section 9, AQ-047); it must say so in
# `benchmark_note`, which the holding page shows in place of "Benchmark text from the challenge specification."
NOT_A_BENCHMARK = {"combined"}
CORE_MANIFEST_KEYS = {"run_id", "scenario_id", "title", "outcome", "dates", "vintages", "validation", "repo_url", "inputs"}


class ReformRegistryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = json.loads(REGISTRY.read_text())

    def test_ids_unique_and_default_registered(self):
        ids = [r["id"] for r in self.reg["reforms"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn(self.reg["default"], ids)
        default = next(r for r in self.reg["reforms"] if r["id"] == self.reg["default"])
        self.assertEqual(default["status"], "ready")

    def test_entries_follow_the_contract(self):
        for r in self.reg["reforms"]:
            with self.subTest(reform=r["id"]):
                self.assertRegex(r["id"], r"^[a-z][a-z0-9-]*$")
                self.assertNotIn(r["id"], ADU_SEGMENTS)
                self.assertIn(r["status"], {"ready", "in_development"})
                for k in ("label", "subtitle", "benchmark", "owner", "bundle_root"):
                    self.assertTrue(r[k].strip(), k)
                self.assertTrue(r["bundle_root"].endswith("/"))
                if r["plan_doc"]:
                    self.assertTrue((ROOT / r["plan_doc"]["path"]).is_file(), r["plan_doc"]["path"])

    def test_benchmarks_are_verbatim_from_the_challenge_spec(self):
        spec = re.sub(r"\s+", " ", (ROOT / "docs" / "CHALLENGE_SPEC.md").read_text())
        for r in self.reg["reforms"]:
            with self.subTest(reform=r["id"]):
                if r["id"] in NOT_A_BENCHMARK:
                    self.assertNotIn(r["benchmark"], spec)
                    self.assertTrue(r.get("benchmark_note", "").strip(), "a non-benchmark entry must say so")
                    continue
                self.assertIn(r["benchmark"], spec)
                self.assertNotIn("benchmark_note", r)

    def test_ready_reforms_have_a_bundle_with_the_core_manifest(self):
        for r in self.reg["reforms"]:
            if r["status"] != "ready":
                continue
            with self.subTest(reform=r["id"]):
                root = PUBLIC / r["bundle_root"]
                run_id = json.loads((root / "latest.json").read_text())["run_id"]
                manifest = json.loads((root / run_id / "manifest.json").read_text())
                self.assertEqual(manifest["run_id"], run_id)
                self.assertLessEqual(CORE_MANIFEST_KEYS, set(manifest))


if __name__ == "__main__":
    unittest.main()
