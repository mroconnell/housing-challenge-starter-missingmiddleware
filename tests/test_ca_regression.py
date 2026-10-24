"""Offline tests for the market-adjusted California regression (missing_middleware.comparison.ca_regression)."""
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.comparison import ca_regression as cr

FIX = Path(__file__).parent / "fixtures" / "ca_regression"
PATHS = {t: FIX / f"acsdt5y2024-{t}.dat" for t in cr.MARKET_TABLES}


def tiny_panel():
    """Three CA jurisdictions plus a county remainder, 2014-2025."""
    rows = []
    series = {
        "0600001": (1000, {y: 5 for y in range(2017, 2026)}),            # active from 2017
        "0600002": (2000, {**{y: 0 for y in range(2014, 2020)}, **{y: 2 for y in range(2020, 2026)}}),
        "0600003": (3000, {**{y: 0 for y in range(2014, 2017)}, 2017: 1, 2018: 0, 2019: 1,
                           2020: 3, 2021: 3, 2022: 3, 2023: 6, 2024: np.nan, 2025: 6}),  # middle, 2024 missing
        "06001_UNINC": (500, {y: 0 for y in range(2014, 2026)}),
    }
    for g, (homes, vals) in series.items():
        for y in range(2014, 2026):
            v = vals.get(y, 0)
            rows.append({"census_geoid": g, "year": y, "sf_detached": float(homes), "adu_main": v, "adu_issue": v,
                         "name": g, "juris_type": "county_unincorporated" if g.endswith("_UNINC") else "city",
                         "in_holdout": g == "0600003"})
    return pd.DataFrame(rows)


class TestMarket(unittest.TestCase):
    def test_read_market_codes(self):
        m = cr.read_market(PATHS, "06", ("050", "160")).set_index("geoid")
        self.assertEqual(m.loc["0600001", "value"], 2_000_000)      # top-coded 2,000,001 -> 2,000,000
        self.assertTrue(m.loc["0600001", "value_topcoded"])
        self.assertEqual(m.loc["0600001", "rent"], 3500)
        self.assertTrue(np.isnan(m.loc["0600003", "value"]))         # special code -> missing, never zero
        self.assertAlmostEqual(m.loc["0600002", "renter_share"], 0.5)

    def test_ca_jurisdiction_market_and_fallback(self):
        m = cr.read_market(PATHS, "06", ("050", "160"))
        j = pd.Series(["0600002", "0600003", "06001_UNINC"])
        mk = cr.ca_jurisdiction_market(j, m)
        self.assertEqual(mk.set_index("census_geoid").loc["06001_UNINC", "market_basis"], "county_proxy")
        self.assertEqual(mk.set_index("census_geoid").loc["06001_UNINC", "value"], 900000)
        filled = cr.fill_from_county(mk, m, pd.Series({"0600003": "06001"})).set_index("census_geoid")
        self.assertEqual(filled.loc["0600003", "value"], 900000)
        self.assertIn("value_county", filled.loc["0600003", "filled"])

    def test_wi_market_fallbacks(self):
        m = cr.read_market(PATHS, "55", ("050", "060"))
        areas = pd.DataFrame({"area_id": ["muni:5502548000", "muni:5502599999", "muni:5502588888"], "homes": [53292, 10, 5]})
        w = cr.wi_market(areas, m).set_index("area_id")
        self.assertEqual(w.loc["muni:5502548000", "value_basis"], "cousub")
        self.assertEqual(w.loc["muni:5502599999", "value"], 210000)       # same municipality, other county piece
        self.assertEqual(w.loc["muni:5502599999", "value_basis"], "other_county_piece")
        self.assertEqual(w.loc["muni:5502588888", "value"], 350000)       # county fallback
        self.assertEqual(w.loc["muni:5502588888", "value_basis"], "county_fallback")
        self.assertEqual(w.loc["muni:5502588888", "rent_basis"], "county_fallback")


class TestDataset(unittest.TestCase):
    def setUp(self):
        self.m = cr.read_market(PATHS, "06", ("050", "160"))
        self.county = pd.Series({"0600001": "06001", "0600002": "06001", "0600003": "06001"})

    def test_groups_and_plateau(self):
        d = cr.build_ca_dataset(tiny_panel(), self.m, self.county).set_index("census_geoid")
        self.assertEqual(d.loc["0600001", "group"], "active")      # 5/yr on 1,000 homes >= 1.038
        self.assertEqual(d.loc["0600002", "group"], "restrictive")
        self.assertEqual(d.loc["0600003", "group"], "middle")
        self.assertIn("0600003", d.index)                          # holdout jurisdictions are now used
        self.assertEqual(d.loc["0600003", "n_years"], 2)            # 2024 missing, not zero
        self.assertAlmostEqual(d.loc["0600003", "rate"], 12 / 2 / 3000 * 1000)
        self.assertAlmostEqual(d.loc["06001_UNINC", "rate"], 0.0)

    def test_event_time(self):
        adopt = pd.Series({"0600001": 2017})
        d = cr.build_ca_dataset(tiny_panel(), self.m, self.county, adoption=adopt).set_index("census_geoid")
        # event years 4-6 for a 2017 adopter are 2020-2022
        self.assertEqual(d.loc["0600001", "n_years"], 3)
        self.assertAlmostEqual(d.loc["0600001", "rate"], 5.0)
        # pre-adoption (2014-2016) activity is zero -> restrictive under the event-time grouping
        self.assertEqual(d.loc["0600001", "group"], "restrictive")
        self.assertEqual(d.loc["0600002", "group"], "restrictive")


class TestPoisson(unittest.TestCase):
    def test_recovers_coefficients(self):
        rng = np.random.default_rng(1)
        n = 400
        df = pd.DataFrame({"group": rng.choice(["active", "middle", "restrictive"], n),
                           "value": np.exp(rng.uniform(np.log(2e5), np.log(2e6), n)),
                           "homes": np.exp(rng.uniform(np.log(1e3), np.log(1e5), n))})
        spec = cr.SPEC_BY_NAME["group_value_size"]
        X, _ = cr.design(df, spec.terms)
        beta = np.array([1.0, -0.8, -1.5, 0.6, 0.1])
        df["exposure"] = df["homes"] * 3 / 1000
        df["adu"] = df["exposure"] * np.exp(X @ beta)   # expected counts: exact recovery
        f = cr.fit(df, spec)
        np.testing.assert_allclose(f.beta, beta, atol=1e-6)

    def test_group_only_reproduces_pooled_rates(self):
        df = pd.DataFrame({"group": ["active", "active", "middle", "restrictive", "restrictive"],
                           "adu": [30, 10, 6, 0, 2], "exposure": [3.0, 2.0, 6.0, 1.0, 3.0],
                           "value": 5e5, "homes": 1e4})
        f = cr.fit(df, cr.SPEC_BY_NAME["group_only"])
        r = f.predict_rate(df)
        self.assertAlmostEqual(r[0], 40 / 5, places=6)
        self.assertAlmostEqual(r[2], 1.0, places=6)
        self.assertAlmostEqual(r[3], 0.5, places=6)

    def test_hinge_zero_above_knot(self):
        df = pd.DataFrame({"group": ["active"] * 3, "value": [3.5e5, 7e5, 1.4e6], "homes": 1e4})
        X, names = cr.design(df, ("log_value_below_knot",))
        np.testing.assert_allclose(X[:, 1], [np.log(0.5), 0.0, 0.0])

    def test_kfold_deterministic_and_balanced(self):
        a, b = cr.kfold_ids(95), cr.kfold_ids(95)
        np.testing.assert_array_equal(a, b)
        counts = np.bincount(a)
        self.assertEqual(len(counts), cr.K_FOLDS)
        self.assertLessEqual(counts.max() - counts.min(), 1)


class TestWisconsinMapping(unittest.TestCase):
    def setUp(self):
        self.a = pd.DataFrame({"x_rate": [0.183, 0.183, 0.0625, 0.031, 0.0625],
                               "rights_basis": ["scenario_benchmark", "restricted", "restricted",
                                                "prohibited_explicit", "undetermined"]})

    def test_rules(self):
        self.assertEqual(list(cr.wi_group(self.a, "absolute")), ["middle", "middle", "restrictive", "restrictive", "restrictive"])
        self.assertEqual(list(cr.wi_group(self.a, "relative")), ["active", "active", "restrictive", "restrictive", "restrictive"])
        self.assertEqual(list(cr.wi_group(self.a, "rules")), ["active", "middle", "middle", "restrictive", "restrictive"])
        self.assertEqual(list(cr.wi_group(self.a, "rules_unmeasured_middle"))[-1], "middle")
        self.assertEqual(list(cr.wi_group(self.a, "unmeasured_middle"))[-1], "middle")

    def test_extrapolation_flags(self):
        ca = pd.DataFrame({"value": np.linspace(2e5, 2e6, 100), "rent": np.linspace(800, 3500, 100), "homes": 1000.0})
        wi = pd.DataFrame({"value": [1.5e5, 2.05e5, 9e5], "rent": [900, 900, 2000], "homes": [500, 2000, 2000]})
        f = cr.extrapolation_flags(wi, ca)
        self.assertEqual(list(f["extrapolation"]), ["outside_ca_range+size_below_ca_min", "ca_tail", "inside"])


class TestRuleV1(unittest.TestCase):
    def test_wisconsin_like(self):
        obs = pd.DataFrame({"jurisdiction": ["mad", "pp", "sp", "fit", "mke"],
                            "permits": [39, 0, 1, 0, 20], "years": [4, 4, 4, 4, 2],
                            "homes": [53292, 6332, 8118, 5999, 101402],
                            "measured": [True, True, True, True, False]})
        g = cr.state_relative_groups(obs).set_index("jurisdiction")["group"]
        self.assertEqual(g.to_dict(), {"mad": "active", "pp": "restrictive", "sp": "middle", "fit": "restrictive",
                                       "mke": "restrictive"})   # unmeasured -> restrictive (owner rule)

    def test_ties_and_min_permits(self):
        obs = pd.DataFrame({"jurisdiction": list("abcdefgh"), "permits": [6, 6, 2, 1, 1, 1, 1, 0],
                            "years": 3, "homes": [1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000], "measured": True})
        o = cr.state_relative_groups(obs).set_index("jurisdiction")
        # top quarter of 8 = 2nd-ranked rate; a and b tie at the top and both qualify; c (2 permits)
        # is below the cut; h has zero permits
        self.assertEqual(o.loc[["a", "b"], "group"].tolist(), ["active", "active"])
        self.assertEqual(o.loc["c", "group"], "middle")
        self.assertEqual(o.loc["h", "group"], "restrictive")
        few = obs.assign(permits=[2, 2, 1, 1, 1, 1, 1, 0])
        self.assertNotIn("active", cr.state_relative_groups(few)["group"].tolist())  # under 3 permits never active

    def test_matches_ca_study_rule(self):
        rng = np.random.default_rng(3)
        n = 60
        homes = rng.integers(500, 50000, n).astype(float)
        permits = rng.poisson(homes * 3 / 1000 * rng.choice([0, 0.2, 1.5], n))
        obs = pd.DataFrame({"jurisdiction": [f"j{i}" for i in range(n)], "permits": permits, "years": 3,
                            "homes": homes, "measured": True})
        v1 = cr.state_relative_groups(obs)
        long = pd.DataFrame([{"census_geoid": j, "year": y, "homes": h, "adu": p if y == 2017 else 0}
                             for j, h, p in zip(obs.jurisdiction, homes, permits) for y in cr.WAVE3_PRE])
        cut = v1["cutoff"].iloc[0]
        ref = cr.jurisdiction_groups(long, cr.WAVE3_PRE, cut)["group"].map(cr.GROUP_NAMES)
        self.assertEqual(v1.set_index("jurisdiction")["group"].to_dict(), ref.to_dict())

    def test_zoning_hook(self):
        import tempfile
        ids = pd.Series(["muni:5500100001", "muni:5500100002"])
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(cr.load_zoning_status(Path(t), ids).tolist(), ["file_missing"] * 2)
            pd.DataFrame({"geoid": ["5500100001"], "zoning_status": ["unzoned"]}).to_csv(Path(t) / cr.ZONING_FILE, index=False)
            self.assertEqual(cr.load_zoning_status(Path(t), ids).tolist(), ["unzoned", "not_listed"])


if __name__ == "__main__":
    unittest.main()


class TestRuleV11(unittest.TestCase):
    def test_too_few_measured_places_means_no_active(self):
        import pandas as pd
        from missing_middleware.comparison import ca_regression as cr
        obs = pd.DataFrame([
            {"jurisdiction": "a", "permits": 39, "years": 4, "homes": 53000, "measured": True},
            {"jurisdiction": "b", "permits": 1, "years": 4, "homes": 8000, "measured": True},
            {"jurisdiction": "c", "permits": 0, "years": 4, "homes": 6000, "measured": True},
        ])
        g11 = cr.state_relative_groups(obs, min_measured=20).set_index("jurisdiction").group
        self.assertEqual(g11["a"], "middle")
        g1 = cr.state_relative_groups(obs).set_index("jurisdiction").group
        self.assertEqual(g1["a"], "active")
