"""Year-matched homes index for the ADU comparison rows (AQ-064). No network, no data files."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from missing_middleware.comparison import homes_by_year as hb  # noqa: E402


class HomesByYear(unittest.TestCase):
    def test_index_is_one_in_reference_year_and_moves_with_permits(self):
        permits = pd.DataFrame({"geo": "53", "year": range(2018, 2026), "units_1": [100.0] * 8})
        ix = hb.stock_index(permits, {"53": 10_000.0}, range(2018, 2027)).set_index("year")["index"]
        self.assertAlmostEqual(ix[2022], 1.0)
        # mid-2020 to mid-2022: half of 2020, all of 2021, half of 2022 = 200 homes
        self.assertAlmostEqual(ix[2020], 1 - 200 / 10_000)
        self.assertAlmostEqual(ix[2025], 1 + 300 / 10_000)
        self.assertAlmostEqual(ix[2026], 1 + 400 / 10_000)     # no 2026 file: repeats 2025

    def test_apply_scales_exposure_city_by_place_state_by_cluster(self):
        ix = pd.DataFrame({"geo": ["53", "5363000"], "year": [2020, 2020], "index": [0.9, 0.8]})
        rows = pd.DataFrame({"cluster": ["WA", "WA", "OR"], "group_id": ["WA_inc_exSeattle", "place:5363000", "x"],
                             "year": [2020, 2020, 2020], "years": [1.0, 0.5, 1.0]})
        r = hb.apply_homes_index(rows, ix, {"WA": "53", "OR": "41"})
        for got, want in zip(r["years"], [0.9, 0.4, 1.0]):
            self.assertAlmostEqual(got, want)
        for got, want in zip(r["homes_index"], [0.9, 0.8, 1.0]):
            self.assertAlmostEqual(got, want)


if __name__ == "__main__":
    unittest.main()
