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
        self.assertTrue((exp["aq023_default_class"] == "undetermined").all())
        matches = exp["default_matches_coded"] == "true"
        self.assertTrue(exp.loc[matches, "current_class"].isin(["prohibited_explicit", "prohibited_implicit"]).all())
        self.assertTrue(exp.loc[~matches, "current_class"].isin(["restricted", "scenario_benchmark", "no_zoning"]).all())

    def test_mention_scan_matcher(self):
        import scan_adu_mentions as scan
        terms, ctx, sec = scan.find_terms(
            "Sec. 17.02 A single-family dwelling unit; a two-family dwelling unit.\n"
            "§ 275-42 C. Family dwelling unit. Detached accessory dwelling units (ADUs) are prohibited.")
        self.assertEqual(terms, ["accessory dwelling", "ADU", "family dwelling unit"])
        self.assertEqual(sec, "§ 275-42")
        self.assertIn("Family dwelling unit", ctx)
        self.assertEqual(scan.find_terms("One single-family dwelling unit per lot. Four family dwelling units.")[0], [])
        # older second-dwelling vocabulary added after the Gate 2 review
        terms = scan.find_terms("A. Residential quarters for domestic help. B. Private guest houses. "
                                "C. Dependency living arrangements. D. Accessory apartment. E. accessory living quarters")[0]
        self.assertEqual(sorted(terms), sorted(["domestic help/servant quarters", "guest house", "dependency living",
                                                "accessory apartment", "accessory living"]))
        self.assertEqual(scan.find_terms("Family means persons related by blood (not including domestic employees).")[0], [])

    def test_every_coded_place_has_first_pass_and_pathway_rows(self):
        from missing_middleware import contracts as c
        rules = pd.read_csv(ROOT / "reference" / "wi_adu_rules.csv", dtype=str, keep_default_na=False)
        exp = pd.read_csv(ROOT / "reference" / "wi_rights_exposure.csv", dtype=str, keep_default_na=False)
        status = rules[rules["provision"] == "ordinance_status"]
        self.assertTrue(set(status["value"]) <= c.ORDINANCE_STATUS)
        primary = set(rules["jurisdiction_id"])
        self.assertEqual(sorted(status["jurisdiction_id"]), sorted(primary))
        self.assertFalse(rules["value"].str.startswith("mentions_adu").any())
        path = rules[(rules["provision"] == "approval_pathway") & (rules["effective_to"] == "")]
        self.assertEqual(sorted(path["jurisdiction_id"]), sorted(primary))
        self.assertTrue(primary <= set(exp["jurisdiction_id"]))

    def test_flags_follow_classes(self):
        from missing_middleware import contracts as c
        exp = pd.read_csv(ROOT / "reference" / "wi_rights_exposure.csv", dtype=str, keep_default_na=False)
        restricted = exp[exp["current_class"] == "restricted"]
        self.assertTrue((restricted["restrictions"] != "").all())
        self.assertTrue((exp.loc[exp["current_class"] != "restricted", "restrictions"] == "").all())
        flags = {f for v in exp["restrictions"] for f in v.split(";") if f}
        self.assertTrue(flags <= c.RESTRICTION_FLAGS)
        form = exp[exp["scenario_id"] == "adu_form_only"]
        kept = form[form["reform_class"] == "restricted"]
        self.assertTrue(all(set(v.split(";")) <= {"owner_occupancy", "related_occupant"} for v in kept["reform_restrictions"]))
        self.assertTrue((exp.loc[exp["scenario_id"] == "adu_full", "reform_class"] == "scenario_benchmark").all())

    def test_bad_rows_are_reported(self):
        rules = pd.read_csv(FIX / "bad_rules.csv", dtype=str, keep_default_na=False)
        exposure = pd.read_csv(FIX / "bad_exposure.csv", dtype=str, keep_default_na=False)
        text = "\n".join(crr.check(rules, exposure))
        for expected in (
            "provision 'garage_color'", "value 'maybe'", "effective_from after effective_to",
            "not YYYY-MM-DD", "source_url", "verification", "reform_class must equal current_class",
            "not_found must go with current_class undetermined", "after 2026-10-31",
            "rights_added_text is blank", "rule_ids not in rules table", "lacks a row for every scenario",
            "value 'mentions_adu: yes'", "value 'by_right' not in ['discretionary'", "not in RESTRICTION_FLAGS",
            "reform_restrictions must be non-empty", "must be scenario_benchmark", "may keep only the place's own",
            "current_class: values not allowed ['compliant', 'prohibited']", "approval_pathway 'sometimes'",
        ):
            self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()
