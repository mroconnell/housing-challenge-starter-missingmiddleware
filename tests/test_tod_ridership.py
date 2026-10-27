"""Offline tests for the Chicago "L" ridership test (missing_middleware/tod/ridership.py), on synthetic stations."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from missing_middleware.tod import ridership as R  # noqa: E402


def synth_daily(levels: dict[str, float], growth: dict[str, float], closed: dict[str, tuple[str, str]] | None = None,
                years=range(2009, 2020)) -> pd.DataFrame:
    """Daily entries: weekdays at `level`, weekends at half; after 2015 multiplied by exp(growth)."""
    rows = []
    dates = pd.date_range(f"{min(years)}-01-01", f"{max(years)}-12-31")
    for sid, lev in levels.items():
        for d in dates:
            wd = d.day_of_week < 5
            v = lev * (1 if wd else 0.5) * (np.exp(growth.get(sid, 0.0)) if d.year >= 2016 else 1.0)
            if closed and sid in closed and pd.Timestamp(closed[sid][0]) <= d <= pd.Timestamp(closed[sid][1]):
                v = 0
            rows.append({"station_id": sid, "stationname": f"S{sid}", "date": d.strftime("%Y-%m-%dT00:00:00.000"),
                         "daytype": "W" if wd else ("A" if d.day_of_week == 5 else "U"), "rides": round(v)})
    return pd.DataFrame(rows)


class TestRidership(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lv = {f"{i}": 1000.0 + 100 * i for i in range(1, 13)}
        # stations 1-4 treated (acres >= 5) grow 10%; others flat
        cls.growth = {f"{i}": np.log(1.10) for i in range(1, 5)}
        cls.daily = R.clean_daily(synth_daily(lv, cls.growth))
        cls.stations = pd.DataFrame({"station_id": list(lv), "treated_acres": [8, 6, 10, 5.5] + [0, 1, 2, 4.9, 0, 0, 3, 0],
                                     "homes_permitted": [50] * 4 + [0] * 8, "existing_homes": [5000] * 12})

    def test_clean_daily_averages_repeats(self):
        d = pd.DataFrame({"station_id": ["1", "1", "1"], "stationname": ["A"] * 3, "daytype": ["W"] * 3,
                          "date": ["2011-07-18T00:00:00.000", "2011-07-18T00:00:00.000", "2011-07-19T00:00:00.000"],
                          "rides": [100, 110, 50]})
        c = R.clean_daily(d)
        self.assertEqual(len(c), 2)
        self.assertAlmostEqual(c.loc[c["date"] == "2011-07-18", "rides"].iloc[0], 105.0)

    def test_drop_list_rules(self):
        lv = {"41000": 500.0, "40380": 500.0, "40540": 500.0, "90001": 500.0, "90002": 500.0, "90003": 500.0}
        d = R.clean_daily(synth_daily(lv, {}, closed={"90001": ("2012-06-01", "2012-06-30"),
                                                      "90002": ("2012-06-01", "2012-06-03")}))
        d = d[~((d["station_id"] == "90003") & (d["date"].dt.year == 2009))]   # opened 2010
        dr = R.drop_list(d).set_index("station_id")["reason"]
        self.assertIn("Red Line South", dr["41000"])
        self.assertIn("Loop", dr["40380"])
        self.assertIn("rebuilt", dr["40540"])
        self.assertIn("closed 30 days", dr["90001"])
        self.assertNotIn("90002", dr.index)       # 3-day closure is under the 7-day rule
        self.assertIn("10 of 11 years", dr["90003"])

    def test_did_recovers_known_effect(self):
        r = R.estimate(self.daily, self.stations, set(self.stations["station_id"]), draws=200)
        self.assertEqual((r["n_treated"], r["n_comparison"]), (4, 8))
        self.assertAlmostEqual(R.pct(r["did_log"]), 10.0, delta=0.2)
        lo, hi = r["did_log_ci"]
        self.assertLessEqual(lo, r["did_log"] + 1e-9)
        self.assertGreaterEqual(hi, r["did_log"] - 1e-9)
        self.assertGreater(r["dose_acres"], 0)
        self.assertGreater(r["dose_permitted"], 0)

    def test_weekend_and_change_year_specs(self):
        r = R.estimate(self.daily, self.stations, set(self.stations["station_id"]), daytypes=R.WEEKEND, draws=50)
        self.assertAlmostEqual(R.pct(r["did_log"]), 10.0, delta=0.5)
        r = R.estimate(self.daily, self.stations, set(self.stations["station_id"]), before=[2009, 2010, 2011, 2012],
                       after=list(range(2014, 2020)), draws=50)
        self.assertGreater(r["did_log"], 0)   # growth only from 2016: diluted by 2014-2015
        self.assertLess(R.pct(r["did_log"]), 10.0)

    def test_exclude_and_seed_reproducible(self):
        keep = set(self.stations["station_id"])
        a = R.estimate(self.daily, self.stations, keep, exclude={"1"}, draws=100)
        b = R.estimate(self.daily, self.stations, keep, exclude={"1"}, draws=100)
        self.assertEqual(a["n_treated"], 3)
        self.assertEqual(a["did_log_ci"], b["did_log_ci"])

    def test_slope(self):
        self.assertAlmostEqual(R.slope([0, 1, 2, 3], [1, 3, 5, 7]), 2.0)
        self.assertTrue(np.isnan(R.slope([1, 1, 1], [0, 1, 2])))


if __name__ == "__main__":
    unittest.main()
