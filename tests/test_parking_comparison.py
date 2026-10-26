"""Parking repeal comparison (missing_middleware/parking/comparison.py). Offline, synthetic data."""
import unittest

import numpy as np
import pandas as pd

from missing_middleware.parking import comparison as cmp


def synth_panel():
    """State 01: treated T (pop 10,000) jumps from 10 to 40 units/yr after 2019; controls
    C1..C6 (pop 8,000-12,000) go from 10 to 20; a big place B (pop 100,000) is outside the
    window; X is reformed (excluded)."""
    rows = []
    for y in range(2012, 2026):
        for key, pop, before, after in [("T", 10_000, 10, 40)] + [(f"C{i}", 8_000 + 800 * i, 10, 20) for i in range(1, 7)] \
                + [("B", 100_000, 100, 100), ("X", 10_000, 10, 90)]:
            rows.append(dict(key=f"01|{key}", state_fips="01", bps_id=key, name=key, county_fips="001",
                             fips_place="00100", fips_mcd="00000", acs_geoid="", year=y, pop=pop,
                             units_total=before if y <= 2019 else after, units_2plus=0))
    return pd.DataFrame(rows)


class TestEffects(unittest.TestCase):
    def setUp(self):
        self.p = synth_panel()
        self.homes = pd.Series({k: 1000.0 for k in self.p["key"].unique()})

    def test_windows(self):
        self.assertEqual(cmp.windows(2019), ([2014, 2015, 2016, 2017, 2018], [2020, 2021, 2022]))
        self.assertEqual(cmp.windows(2014)[0], [2012, 2013])   # too few: excluded later

    def test_controls_exclude_reformed_and_out_of_window(self):
        c, w = cmp.controls(self.p, "01|T", 2019, {"01|X"}, self.homes)
        self.assertEqual(sorted(c), [f"01|C{i}" for i in range(1, 7)])
        self.assertEqual(w, "state 0.50-2.00")

    def test_effect_is_difference_in_differences(self):
        cases = pd.DataFrame({"key": ["01|T"], "event_year": [2019]})
        e = cmp.effects(self.p, cases, {"01|X"}, self.homes)
        a = e[e["outcome"] == "all"].iloc[0]
        # treated 10 -> 40 per 1,000 homes; controls 10 -> 20: effect 30 - 10 = 20
        self.assertAlmostEqual(a["rate_before"], 10.0)
        self.assertAlmostEqual(a["rate_after"], 40.0)
        self.assertAlmostEqual(a["effect"], 20.0)

    def test_state_share_repealed(self):
        p = synth_panel()
        # B is the only place of 50,000+; repealed in 2018 -> share 1 in 2019, 0 in 2017
        self.assertEqual(cmp.state_share_repealed(p, "01", 2019, {"01|B": 2018}), 1.0)
        self.assertEqual(cmp.state_share_repealed(p, "01", 2017, {"01|B": 2018}), 0.0)

    def test_too_few_years_excluded(self):
        e = cmp.effects(self.p, pd.DataFrame({"key": ["01|T"], "event_year": [2014]}), set(), self.homes)
        self.assertTrue(e["status"].iloc[0].startswith("excluded"))


class TestMatch(unittest.TestCase):
    def test_match_prefers_exact_and_skips_county(self):
        p = pd.DataFrame([
            dict(key="26|A", state_fips="26", name="Kalkaska County", fips_place="00000", pop=np.nan, year=2025),
            dict(key="26|B", state_fips="26", name="Windham town", fips_place="00000", pop=18000, year=2025),
            dict(key="21|L", state_fips="21", name="Lexington-Fayette", fips_place="46027", pop=320000, year=2025),
        ])
        self.assertIsNone(cmp.match_place(p, "26", "Kalkaska", 2000))
        self.assertEqual(cmp.match_place(p, "26", "Windham", 18000), "26|B")
        self.assertEqual(cmp.match_place(p, "21", "Lexington", 340000), "21|L")


class TestModels(unittest.TestCase):
    def test_loo_picks_bands_when_effect_steps_with_size(self):
        rng = np.random.default_rng(1)
        pop = np.array([2e3, 4e3, 6e3, 8e3, 12e3, 15e3, 30e3, 60e3, 80e3, 150e3, 300e3, 500e3])
        eff = np.where(pop >= 50_000, 3.0, 0.0) + rng.normal(0, 0.05, len(pop))
        d = pd.DataFrame({"population": pop, "effect": eff, "homes": 1.0, "log_pop": cmp.log_pop(pop),
                          "rate_before": 1.0, "rel_rent": 1.0, "metro": 1.0})
        m = cmp.compare_models(d, cmp.candidate_specs(has_rent=False, has_metro=False, has_pre=False))
        self.assertEqual(m.loc[m["chosen"], "model"].iloc[0], "M1 bands at 50,000")

    def test_bootstrap_shape(self):
        d = pd.DataFrame({"population": [1e3, 1e4, 1e5, 1e6] * 3, "effect": np.arange(12.0), "homes": 1.0})
        d["log_pop"] = cmp.log_pop(d["population"])
        b = cmp.bootstrap(d, {"vars": ["log_pop"]}, draws=50)
        self.assertEqual(b.shape[1], 2)


if __name__ == "__main__":
    unittest.main()
