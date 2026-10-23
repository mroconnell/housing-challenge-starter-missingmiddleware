"""The shared contracts catch missing columns, bad enum values, and duplicate keys."""
import unittest

import pandas as pd

from missing_middleware import contracts as c


class TestContracts(unittest.TestCase):
    def test_valid_table_has_no_problems(self):
        df = pd.DataFrame([{
            "jurisdiction_id": "5502548000", "scenario_id": "adu_benchmark",
            "current_class": "compliant", "reform_class": "compliant",
            "class_basis": "coded_verified", "rules_as_of": "2026-10-31",
            "rights_added_text": "none",
        }])
        self.assertEqual(c.validate(df, c.RIGHTS_EXPOSURE), [])

    def test_reports_bad_enum_missing_column_and_duplicates(self):
        row = {"area_id": "55", "level": "planet", "name": "WI"}
        problems = c.validate(pd.DataFrame([row, row]), c.AREAS)
        text = " ".join(problems)
        self.assertIn("missing columns", text)
        self.assertIn("planet", text)
        self.assertIn("duplicate", text)


if __name__ == "__main__":
    unittest.main()
