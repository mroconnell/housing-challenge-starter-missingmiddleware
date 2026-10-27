"""Seattle case adapter (missing_middleware/tod/case_seattle.py): zoning-history parsing, no network."""
from __future__ import annotations

import unittest

import pandas as pd

from missing_middleware.tod import case_seattle as S

HIST = "NC3P-85 (5.75),ORD125791,04/19/2019; NC3P-85,ORD123853,05/10/2012; NC3P-65,ORD123000,01/01/2005; NC2-40"


class TestZoningHistory(unittest.TestCase):
    def test_parse(self):
        h = S.parse_history(HIST)
        self.assertEqual([z for z, _, _ in h], ["NC3P-85 (5.75)", "NC3P-85", "NC3P-65", "NC2-40"])
        self.assertEqual(h[1][1], "123853")
        self.assertEqual(h[1][2], pd.Timestamp("2012-05-10"))
        self.assertIsNone(h[-1][1])
        self.assertEqual(S.parse_history(""), [])

    def test_zone_at(self):
        h = S.parse_history(HIST)
        self.assertEqual(S.zone_at(h, pd.Timestamp("2012-05-09")), "NC3P-65")
        self.assertEqual(S.zone_at(h, pd.Timestamp("2012-12-31")), "NC3P-85")
        self.assertEqual(S.zone_at(h, pd.Timestamp("2000-01-01")), "NC2-40")   # before every dated change
        self.assertEqual(S.zone_at(h, pd.Timestamp("2020-01-01")), "NC3P-85 (5.75)")

    def test_changes_between_skips_reform_and_citywide(self):
        h = S.parse_history(HIST)
        lo, hi = pd.Timestamp("2006-01-01"), pd.Timestamp("2019-12-31")
        self.assertEqual(S.changes_between(h, lo, hi, {"123853"} | S.CITYWIDE_ORDS), [])
        self.assertEqual(S.changes_between(h, pd.Timestamp("2004-01-01"), hi, {"123853"} | S.CITYWIDE_ORDS), ["123000"])

    def test_base_zone(self):
        self.assertEqual(S.base_zone("NC3P-85 (5.75)"), "NC3P-85")
        self.assertEqual(S.base_zone("LR3 RC"), "LR3")
        self.assertEqual(S.base_zone(None), "")

    def test_cases(self):
        self.assertEqual(set(S.CASES), {"seattle_nbh_othello_2012", "seattle_mount_baker_2014"})


if __name__ == "__main__":
    unittest.main()
