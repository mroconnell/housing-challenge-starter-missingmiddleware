"""Engine behavior: floor, spillover, unchanged-policy, ordering, and arithmetic."""
import unittest

import pandas as pd

from missing_middleware.model import engine as e

RAMP = (0.4, 0.7, 1, 1, 1)


def scenario(spill=0.2):
    return e.Scenario("adu_benchmark", {
        "lower": e.PathParams(level=0.25, floor_rate=0.25, spillover=0.0, ramp=(0.25, 0.5, 0.75, 1, 1)),
        "central": e.PathParams(level=0.3, floor_rate=0.25, spillover=spill, ramp=RAMP),
        "upper": e.PathParams(level=1.0, floor_rate=0.25, spillover=spill * 2, ramp=(0.6, 0.9, 1, 1, 1)),
    })


AREAS = pd.DataFrame([
    {"area_id": "restrictive", "homes": 10000, "x_rate": 0.02, "at_benchmark": False},
    {"area_id": "madison", "homes": 53292, "x_rate": 0.25, "at_benchmark": True},
    {"area_id": "unknown", "homes": 10000, "x_rate": 0.0, "at_benchmark": False},
])


class TestEngine(unittest.TestCase):
    def setUp(self):
        self.out = e.run(AREAS, scenario())

    def test_invariants_hold(self):
        self.assertEqual(e.check_invariants(self.out), [])

    def test_worked_example_restrictive_central(self):
        t = self.out[(self.out.area_id == "restrictive") & (self.out.path == "central")]
        self.assertAlmostEqual(t.additional_units.sum(), 10 * (0.3 - 0.02) * 4.1, places=6)
        self.assertAlmostEqual(t.baseline_units.sum(), 10 * 0.02 * 5, places=6)

    def test_benchmark_place_gets_spillover_only(self):
        m = self.out[(self.out.area_id == "madison") & (self.out.path == "central")]
        self.assertAlmostEqual(m.y_rate.iloc[0], 0.30, places=9)
        self.assertAlmostEqual(m.additional_units.sum(), 53.292 * 0.05 * 4.1, places=6)

    def test_benchmark_place_gets_at_least_statewide_level(self):
        out = e.run(AREAS, scenario(spill=0.0))
        m = out[(out.area_id == "madison") & (out.path == "central")]
        self.assertAlmostEqual(m.y_rate.iloc[0], 0.30, places=9)

    def test_no_change_when_benchmark_rate_already_above_level_and_no_spillover(self):
        areas = pd.DataFrame([{"area_id": "hot", "homes": 1000, "x_rate": 0.5, "at_benchmark": True}])
        out = e.run(areas, scenario(spill=0.0))
        self.assertEqual(out[out.path == "central"].additional_units.sum(), 0.0)

    def test_floor_applies_when_level_below_floor(self):
        p = e.PathParams(level=0.1, floor_rate=0.25, spillover=0, ramp=RAMP)
        self.assertEqual(e.y_rate(0.0, False, p), 0.25)

    def test_never_below_current_rate(self):
        p = e.PathParams(level=0.1, floor_rate=0.1, spillover=0, ramp=RAMP)
        self.assertEqual(e.y_rate(0.5, False, p), 0.5)

    def test_ramping_place_gap_uses_that_years_current_rate(self):
        areas = pd.DataFrame([{"area_id": "mke", "homes": 1000, "x_rate": 0.2, "at_benchmark": False}])
        growth = pd.DataFrame([{"area_id": "mke", "year": t, "g": g} for t, g in zip(e.YEARS, (0.5, 0.75, 1, 1, 1))])
        out = e.run(areas, scenario(), growth)
        c = out[out.path == "central"].sort_values("year")
        self.assertAlmostEqual(c.baseline_units.iloc[0], 1 * 0.1, places=9)
        self.assertAlmostEqual(c.additional_units.iloc[0], 1 * (0.3 - 0.1) * 0.4, places=9)

    def test_area_specific_levels_override_uniform_level(self):
        lv = pd.DataFrame([{"area_id": "restrictive", "y_central": 0.6}])
        out = e.run(AREAS, scenario(), area_levels=lv)
        r = out[(out.area_id == "restrictive") & (out.path == "central")]
        self.assertAlmostEqual(r.y_rate.iloc[0], 0.6, places=9)
        u = out[(out.area_id == "unknown") & (out.path == "central")]
        self.assertAlmostEqual(u.y_rate.iloc[0], 0.3, places=9)

    def test_bad_ramp_rejected(self):
        with self.assertRaises(ValueError):
            e.PathParams(level=0.3, floor_rate=0.2, spillover=0, ramp=(1, 0.5, 1, 1, 1))


if __name__ == "__main__":
    unittest.main()
