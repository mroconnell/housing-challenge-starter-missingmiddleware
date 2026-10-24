"""The hand-coded Wisconsin ADU rule tables pass their contract checks, and the checker catches bad rows."""
import subprocess
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_reference_rules as crr  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "reference_rules"


class TestReferenceRules(unittest.TestCase):
    def test_reference_tables_are_clean(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_reference_rules.py")],
            capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OK", result.stdout)

    def test_unknown_default_is_recorded(self):
        exp = pd.read_csv(ROOT / "reference" / "wi_rights_exposure.csv", dtype=str, keep_default_na=False)
        self.assertTrue((exp["aq023_default_class"] == "prohibited").all())
        matches = exp["default_matches_coded"] == "true"
        self.assertTrue((exp.loc[matches, "current_class"] == "prohibited").all())

    def test_mention_scan_matcher(self):
        import scan_adu_mentions as scan
        terms, ctx, sec = scan.find_terms(
            "Sec. 17.02 A single-family dwelling unit; a two-family dwelling unit.\n"
            "§ 275-42 C. Family dwelling unit. Detached accessory dwelling units (ADUs) are prohibited.")
        self.assertEqual(terms, ["accessory dwelling", "ADU", "family dwelling unit"])
        self.assertEqual(sec, "§ 275-42")
        self.assertIn("Family dwelling unit", ctx)
        self.assertEqual(scan.find_terms("One single-family dwelling unit per lot. Four family dwelling units.")[0], [])

    def test_every_coded_place_has_a_first_pass_mention_row(self):
        rules = pd.read_csv(ROOT / "reference" / "wi_adu_rules.csv", dtype=str, keep_default_na=False)
        exp = pd.read_csv(ROOT / "reference" / "wi_rights_exposure.csv", dtype=str, keep_default_na=False)
        mention = rules[rules["value"].str.startswith("mentions_adu: ")]
        self.assertTrue(set(mention["value"]) <= {"mentions_adu: yes", "mentions_adu: no", "mentions_adu: could_not_access"})
        primary = set(rules["jurisdiction_id"])
        self.assertEqual(set(mention["jurisdiction_id"]), primary)
        self.assertTrue(primary <= set(exp["jurisdiction_id"]))

    def test_bad_rows_are_reported(self):
        rules = pd.read_csv(FIX / "bad_rules.csv", dtype=str, keep_default_na=False)
        exposure = pd.read_csv(FIX / "bad_exposure.csv", dtype=str, keep_default_na=False)
        text = "\n".join(crr.check(rules, exposure))
        for expected in (
            "provision 'garage_color'", "value 'maybe'", "effective_from after effective_to",
            "not YYYY-MM-DD", "source_url", "verification", "reform_class must equal current_class",
            "not_found must go with current_class unknown", "after 2026-10-31",
            "rights_added_text is blank", "rule_ids not in rules table", "lacks a row for every scenario",
        ):
            self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()
