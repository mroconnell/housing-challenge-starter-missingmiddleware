"""Wisconsin current-law rate x and baseline B (missing_middleware/model/baseline.py).
Offline; small synthetic fixtures in tests/fixtures/wi_baseline/."""
import unittest
from datetime import date
from pathlib import Path

import pandas as pd

from missing_middleware.model import baseline as bl

FIX = Path(__file__).parent / "fixtures" / "wi_baseline"
REF = Path(__file__).resolve().parent.parent / "reference"


def obs(key, units, homes, years, regime="restricted"):
    return bl.Observation(key, key, "55", "s", "w", units, homes, years, regime, "observed")


class TestRates(unittest.TestCase):
    def test_rate_per_1000(self):
        # Madison 2022-2025: 39 units, 53,292 homes, 4 years
        self.assertAlmostEqual(bl.rate_per_1000(39, 53292, 4), 0.18295, places=4)
        with self.assertRaises(ValueError):
            bl.rate_per_1000(1, 0, 4)

    def test_poisson_interval_known_values(self):
        lo, hi = bl.poisson_interval(0)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 3.6889, places=3)
        lo, hi = bl.poisson_interval(3)
        self.assertAlmostEqual(lo, 0.6187, places=3)
        self.assertAlmostEqual(hi, 8.7673, places=3)
        lo, hi = bl.poisson_interval(39)
        self.assertAlmostEqual(lo, 27.73, places=1)
        self.assertAlmostEqual(hi, 53.32, places=1)

    def test_observation_interval_scales_by_exposure(self):
        o = obs("x", 3, 6332, 12)
        lo, hi = o.interval
        self.assertAlmostEqual(o.rate, 3 / 75.984, places=6)
        self.assertLess(lo, o.rate)
        self.assertGreater(hi, o.rate)
        self.assertAlmostEqual(hi, 8.7673 / 75.984, places=4)

    def test_pooled(self):
        rate, lo, hi, k, e = bl.pooled([obs("a", 3, 1000, 2), obs("b", 1, 2000, 1)])
        self.assertEqual(k, 4)
        self.assertAlmostEqual(e, 4.0)
        self.assertAlmostEqual(rate, 1.0)
        self.assertLess(lo, 1.0)
        self.assertGreater(hi, 1.0)

    def test_years_between_inclusive(self):
        self.assertAlmostEqual(bl.years_between(date(2025, 1, 1), date(2025, 12, 31)), 365 / 365.25)


class TestSeries(unittest.TestCase):
    def setUp(self):
        self.cmp = pd.read_csv(FIX / "comparison_series.csv")

    def test_restrictive_period_only(self):
        n = bl.comparison_units(self.cmp, "second_home_sf_lot", date(2024, 1, 1), date(2026, 5, 4))
        self.assertEqual(n, 4)  # 1 + 2 + 1; the 4 units after the reform are excluded
        n_all = bl.comparison_units(self.cmp, "second_home_sf_lot", date(2024, 1, 1), date(2026, 12, 31),
                                    restrictive_only=False)
        self.assertEqual(n_all, 8)

    def test_window_bounds(self):
        self.assertEqual(bl.comparison_units(self.cmp, "second_home_sf_lot", date(2025, 1, 1), date(2025, 12, 31)), 2)

    def test_madison_units_requires_every_year(self):
        mad = pd.DataFrame({"year": [2022, 2023], "category": ["c", "c"], "units": [5.0, 9.0]})
        self.assertEqual(bl.madison_units(mad, "c", range(2022, 2024)), 14)
        with self.assertRaises(ValueError):
            bl.madison_units(mad, "c", range(2022, 2025))


class TestGroupRates(unittest.TestCase):
    def setUp(self):
        self.bench = obs("bench", 40, 50000, 4, "benchmark")         # 0.2
        self.proh = [obs("p1", 2, 10000, 10, "prohibited")]           # 0.02
        self.rest = [obs("r1", 10, 50000, 4)]                         # 0.05
        self.rest_hi = obs("rhi", 12, 50000, 2)                       # 0.12
        self.t = bl.group_rates(self.bench, self.proh, self.rest, self.rest_hi).set_index("group")

    def test_values(self):
        self.assertAlmostEqual(self.t.loc["benchmark", "x_central"], 0.2)
        self.assertAlmostEqual(self.t.loc["prohibited", "x_central"], 0.02)
        self.assertAlmostEqual(self.t.loc["restricted", "x_central"], 0.05)
        self.assertAlmostEqual(self.t.loc["restricted", "x_high"], 0.12)

    def test_undetermined_behaves_like_restricted(self):
        self.assertEqual(self.t.loc["undetermined", "x_central"], self.t.loc["restricted", "x_central"])
        self.assertEqual(self.t.loc["undetermined", "x_high"], self.t.loc["restricted", "x_high"])
        self.assertEqual(self.t.loc["undetermined", "x_low"], self.t.loc["prohibited", "x_central"])

    def test_order(self):
        for g, r in self.t.iterrows():
            self.assertLessEqual(r.x_low, r.x_central, g)
            self.assertLessEqual(r.x_central, r.x_high, g)

    def test_order_violation_raises(self):
        with self.assertRaises(ValueError):
            bl.group_rates(self.bench, self.proh, self.rest, obs("low_hi", 1, 50000, 4))


class TestRamp(unittest.TestCase):
    def test_ramp_share(self):
        rd = date(2025, 8, 2)
        self.assertEqual(bl.ramp_share(2025, rd, 4), 0.0)       # mid-2025 is before the reform
        self.assertAlmostEqual(bl.ramp_share(2027, rd, 4), ((date(2027, 7, 1) - rd).days / 365.25) / 4)
        self.assertEqual(bl.ramp_share(2031, rd, 4), 1.0)
        self.assertEqual(bl.ramp_share(2027, None, 4), 1.0)

    def test_ramped_rate_moves_from_pre_to_target(self):
        rd = date(2025, 8, 2)
        xs = [bl.ramped_rate(y, 0.05, 0.18, rd, 4) for y in bl.ALL_YEARS]
        self.assertEqual(xs, sorted(xs))
        self.assertGreaterEqual(xs[0], 0.05)
        self.assertAlmostEqual(xs[-1], 0.18)

    def test_liberalizations(self):
        rules = pd.read_csv(FIX / "rules.csv", dtype={"jurisdiction_id": str})
        lib = bl.liberalizations(rules)
        self.assertEqual(lib["jurisdiction_id"].tolist(), ["5500000001"])   # only prohibited -> allowed
        self.assertEqual(lib["reform_date"].iloc[0], date(2025, 8, 2))


class TestBaseline(unittest.TestCase):
    def setUp(self):
        self.rates = bl.group_rates(obs("bench", 40, 50000, 4, "benchmark"), [obs("p", 2, 10000, 10)],
                                    [obs("r", 10, 50000, 4)], obs("rhi", 12, 50000, 2))
        self.areas = pd.DataFrame({
            "area_id": ["muni:A", "muni:B", "muni:C", "muni:D"], "place_id": ["A", None, "C", "D"],
            "name": ["A", "B", "C", "D"], "homes": [10000, 2000, 5000, 1000],
            "current_class": ["scenario_benchmark", None, "restricted", "prohibited_implicit"]})
        self.observed = {"A": {"low": 0.1, "central": 0.3, "high": 0.4, "basis": "obs"}}
        self.over = {"C": {"target": {"low": 0.02, "central": 0.05, "high": 0.12},
                           "pre": {"low": 0.0, "central": 0.02, "high": 0.04},
                           "reform_date": date(2025, 8, 2), "basis": "ramp"}}

    def test_assign(self):
        a = bl.assign_rates(self.areas, self.rates, self.observed, self.over).set_index("area_id")
        self.assertEqual(a.loc["muni:A", "x_status"], "observed")
        self.assertEqual(a.loc["muni:B", "rate_group"], "undetermined")
        self.assertEqual(a.loc["muni:B", "x_status"], "assumed")
        self.assertAlmostEqual(a.loc["muni:B", "x_central"], 0.05)
        self.assertAlmostEqual(a.loc["muni:D", "x_central"], 0.02)

    def test_unchanged_policy_baseline_is_h_times_x(self):
        a = bl.assign_rates(self.areas, self.rates, self.observed)
        b = bl.baseline(a)
        self.assertTrue((b["g"] == 1.0).all())
        r = b[(b.area_id == "muni:A") & (b.path == "central") & (b.year == 2027)].iloc[0]
        self.assertAlmostEqual(r.baseline_units, 10000 * 0.3 / 1000)
        self.assertEqual(bl.check_baseline(b, state_homes=18000), [])

    def test_ramp_g_and_five_year_excludes_bridge(self):
        a = bl.assign_rates(self.areas, self.rates, self.observed, self.over)
        b = bl.baseline(a)
        c = b[(b.area_id == "muni:C") & (b.path == "central")].set_index("year")
        self.assertLess(c.loc[2026, "g"], 1.0)
        self.assertTrue((c["g"].diff().dropna() >= -1e-12).all())
        self.assertAlmostEqual(c.loc[2031, "g"], 1.0)
        f = bl.five_year(b, ["area_id"]).set_index("area_id")
        self.assertAlmostEqual(f.loc["muni:A", "central"], 5 * 10000 * 0.3 / 1000)
        self.assertEqual(bl.check_baseline(b), [])

    def test_area_sum_equals_state(self):
        b = bl.baseline(bl.assign_rates(self.areas, self.rates, self.observed, self.over))
        st = b.groupby(["year", "path"]).baseline_units.sum()
        per = b.groupby(["area_id", "year", "path"]).baseline_units.sum().groupby(["year", "path"]).sum()
        pd.testing.assert_series_equal(st, per)
        self.assertEqual(bl.check_baseline(b, state_homes=17999), ["area homes 18000 != state 17999"])

    def test_check_flags_bad_order(self):
        b = bl.baseline(bl.assign_rates(self.areas, self.rates, self.observed))
        b.loc[(b.path == "low") & (b.area_id == "muni:A"), "baseline_units"] = 99
        self.assertIn("paths out of order", bl.check_baseline(b))


class TestHoldout(unittest.TestCase):
    def test_draw_is_reproducible_and_excludes_pilots(self):
        ids = [f"55{i:08d}" for i in range(34)] + list(bl.FIT_PLACE_IDS)
        h1, h2 = bl.draw_holdout(ids), bl.draw_holdout(ids)
        pd.testing.assert_frame_equal(h1, h2)
        self.assertEqual(int(h1.holdout.sum()), round(0.2 * 34))
        self.assertFalse(h1[h1.jurisdiction_id.isin(bl.FIT_PLACE_IDS)].holdout.any())

    def test_committed_holdout_reproduces(self):
        ref = pd.read_csv(REF / "wi_holdout_coded_places.csv", dtype={"jurisdiction_id": str})
        h = bl.draw_holdout(ref["jurisdiction_id"].tolist())
        self.assertEqual(set(h[h.holdout].jurisdiction_id), set(ref[ref.holdout].jurisdiction_id))
        self.assertEqual(len(ref), 37)

    def test_status_rule(self):
        c = pd.DataFrame({"ordinance_status": ["mentioned_allowed", "unmentioned", "unmentioned", "could_not_access"],
                          "current_class": ["restricted", "prohibited_implicit", "restricted", "restricted"]})
        out = bl.holdout_status_check(c)
        self.assertEqual(out["correct"].tolist(), [True, True, False, False])


class TestEvidence(unittest.TestCase):
    def test_parse_address(self):
        self.assertEqual(bl.parse_milwaukee_address("1234 N 35TH ST, MILWAUKEE, WI 532100000"), (1234, "N", "35TH"))
        self.assertEqual(bl.parse_milwaukee_address("10 W GARFIELD AV, MILWAUKEE"), (10, "W", "GARFIELD"))
        self.assertIsNone(bl.parse_milwaukee_address("no number"))

    def test_milwaukee_candidates(self):
        p = pd.read_csv(FIX / "mke_permits.csv", parse_dates=["issued"])
        m = pd.read_csv(FIX / "mke_mprop.csv", dtype=str)
        c = bl.milwaukee_candidates(p, m).set_index("record_id")
        self.assertEqual(sorted(c.index), ["R1", "R2", "R3", "R4", "R7", "R8"])
        self.assertTrue(c.loc["R1", "central"])                       # alteration on a 1-unit 1951 home
        self.assertFalse(c.loc["R2", "upper"])                        # new house on a vacant lot
        self.assertEqual(c.loc["R3", "component"], "detached_garage_unit")
        self.assertTrue(c.loc["R3", "central"])
        self.assertFalse(c.loc["R4", "central"])                      # record already shows 2 units
        self.assertTrue(c.loc["R4", "upper"])
        self.assertEqual(c.loc["R7", "parcel_matches"], 0)
        self.assertFalse(c.loc["R8", "central"])                      # new dwelling: upper only
        self.assertTrue(c.loc["R8", "upper"])
        self.assertEqual(int(c.central.sum()), 2)
        self.assertEqual(int(c.upper.sum()), 4)

    def test_adu_text_hits(self):
        yes = ["Detached ADU above garage", "Convert single family to duplex", "basement apartment for in-law"]
        no = ["Great old windowed carriage house doors", "REPLACE 120V DUPLEX RECEPTACLE", "Carriage House/Pole Barn Addition",
              "Finish basement, add bedroom"]
        self.assertEqual(bl.adu_text_hits(yes + no), yes)


if __name__ == "__main__":
    unittest.main()
