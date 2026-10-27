"""Bellevue BelRed adapter (missing_middleware/tod/case_bellevue.py): helpers on small synthetic inputs, no network."""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from missing_middleware.tod import case_bellevue as B


class TestBellevueHelpers(unittest.TestCase):
    def test_zoning_classes(self):
        self.assertEqual(B.zclass("LI"), "ind")
        self.assertEqual(B.zclass("BR-GC"), "ind")       # BelRed general commercial does not allow housing
        self.assertEqual(B.zclass("BR-MO"), "ind")
        self.assertEqual(B.zclass("BR-RC-1"), "com")
        self.assertEqual(B.zclass("R-3.5"), "res")
        self.assertEqual(B.zclass("LDR-2"), "res")
        self.assertEqual(B.zclass("PO"), "com")
        self.assertTrue({"BR-R", "BR-CR"} <= B.BR_HOUSING)
        self.assertFalse(B.BR_HOUSING & B.BR_NO_HOUSING)

    def test_ordinance_year_interpolation(self):
        z = pd.DataFrame({"ORDNUM": ["ORD.5000", "ORD.6000", "ORD.1200"],
                          "ORDDATE": [pd.Timestamp("2000-06-01").value // 10**6, pd.Timestamp("2010-06-01").value // 10**6,
                                      pd.Timestamp("1900-01-01").value // 10**6]})
        f = B.ord_year_map(z)
        self.assertAlmostEqual(f(5500), 2005.0)
        self.assertTrue(np.isnan(f(np.nan)))
        self.assertEqual(B.ord_number("ORD.5875"), 5875.0)

    def test_staged_permits_kept_once(self):
        p = pd.DataFrame({"PARCELNUMBER": ["a", "a", "a", "b"], "units": [100, 100, 100, 100],
                          "date": pd.to_datetime(["2014-01-01", "2014-08-01", "2017-01-01", "2014-01-01"])})
        d = B.dedupe_staged(p)
        self.assertEqual(len(d), 3)  # second 'a' permit within 18 months is a stage; the 2017 one is a new building

    def test_staged_names(self):
        self.assertTrue(B.STAGED.search("Bellevue Station Below Grade/ Garage"))
        self.assertFalse(B.STAGED.search("Bellevue Station Tower Permit"))


if __name__ == "__main__":
    unittest.main()
