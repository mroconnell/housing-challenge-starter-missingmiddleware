"""Baseline bake-off Part 1 (missing_middleware/baseline_bakeoff.py). Offline, synthetic inputs only."""
import unittest

import numpy as np
import pandas as pd

from missing_middleware import baseline_bakeoff as bb


def synthetic(n_states=4, growth=0.0, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(n_states):
        for y in range(1990, 2026):
            for z, base in zip(bb.SIZES, (1000, 100, 20, 300)):
                rows.append(dict(state=f"{s:02d}", year=y, size=z,
                                 units=base * (1 + growth) ** (y - 1990) * (1 + 0.1 * rng.standard_normal())))
    u = pd.DataFrame(rows)
    census = pd.DataFrame([dict(state=f"{s:02d}", year=c, homes=100_000.0) for s in range(n_states)
                           for c in bb.CENSUS_YEARS])
    allu = u.groupby(["state", "year"], as_index=False)["units"].sum()
    homes = bb.homes_by_year(census, allu, range(1990, 2026))
    division = pd.Series({f"{s:02d}": s % 2 for s in range(n_states)})
    return u, homes, division


class TestBakeoff(unittest.TestCase):
    def test_homes_use_census_from_year_after(self):
        u, homes, _ = synthetic()
        allu = u.groupby(["state", "year"])["units"].sum()
        h2000 = homes[(homes.state == "00") & (homes.year == 2000)]["homes"].iloc[0]
        expect = 100_000 + allu.loc["00"].loc[1991:2000].sum()       # 2000 census not usable in 2000
        self.assertAlmostEqual(h2000, expect, places=6)
        h2001 = homes[(homes.state == "00") & (homes.year == 2001)]["homes"].iloc[0]
        self.assertAlmostEqual(h2001, 100_000 + allu.loc["00"].loc[2001], places=6)

    def test_flat_is_window_mean(self):
        u, homes, div = synthetic()
        p = bb.predict("L0", u, homes, 2010, div)
        w = u[(u.state == "01") & (u["size"] == "5plus") & u.year.between(2008, 2010)]["units"].mean()
        self.assertAlmostEqual(p.loc[("01", "5plus")], w)

    def test_l3_endpoints(self):
        u, homes, div = synthetic()
        l0, l2 = bb.predict("L0", u, homes, 2010, div), bb.predict("L2", u, homes, 2010, div)
        pd.testing.assert_series_equal(bb.predict("L3", u, homes, 2010, div, 0.0), l0, check_names=False)
        np.testing.assert_allclose(bb.predict("L3", u, homes, 2010, div, 1.0).values, l2.reindex(l0.index).values)

    def test_l5_w1_is_own_rate_not_l0(self):
        u, homes, div = synthetic()
        own = bb.at_homes(bb.per_home_rate(u, homes, 2010, 3), homes, 2010)
        l5 = bb.predict("L5", u, homes, 2010, div, 1.0)
        np.testing.assert_allclose(l5.values, own.reindex(l5.index).values)

    def test_trend_exact_on_line(self):
        u = pd.DataFrame([dict(state="00", year=y, size=z, units=10.0 * (y - 1989)) for y in range(1990, 2026)
                          for z in bb.SIZES])
        p = bb.trend_five(u, 2010, 10)
        self.assertAlmostEqual(p.loc[("00", "1unit")], 10.0 * np.mean(np.arange(2011, 2016) - 1989), places=6)

    def test_fit_uses_only_finished_starts(self):
        u, homes, div = synthetic(growth=0.03)
        # changing outcomes after the fit window's last outcome year (t) must not change the fitted value
        t = 2005
        b1 = bb.fit_param("L3", u, homes, t, div)
        u2 = u.copy()
        u2.loc[u2.year > t, "units"] *= 5
        self.assertEqual(b1, bb.fit_param("L3", u2, homes, t, div))

    def test_bootstrap_blocks(self):
        d = bb.block_bootstrap_starts(bb.SCORE_STARTS, n_draws=50)
        self.assertEqual(d.shape, (50, 21))
        for row in d:
            for j in range(0, 20, 5):
                blk = row[j:j + 5]
                self.assertTrue((np.diff(blk) == 1).all())
        self.assertTrue(np.isin(d, bb.SCORE_STARTS).all())

    def test_pick_rule(self):
        s = pd.DataFrame([dict(candidate="L0", score=0.20, wi_score=0.20, boot_hi=0.0),
                          dict(candidate="L1a", score=0.19, wi_score=0.20, boot_hi=-0.001),
                          dict(candidate="L2", score=0.1905, wi_score=0.20, boot_hi=-0.001),
                          dict(candidate="L3", score=0.15, wi_score=0.30, boot_hi=-0.01)])
        self.assertEqual(bb.pick(s), "L1a")      # L3 fails the Wisconsin check; L1a/L2 tie -> table order
        s.loc[s.candidate == "L1a", "boot_hi"] = 0.001
        self.assertEqual(bb.pick(s), "L2")
        s["boot_hi"] = 0.001
        self.assertEqual(bb.pick(s), "L0")

    def test_coverage_uses_past_only(self):
        r = pd.DataFrame([dict(start=s, size=z, ratio=1.0 + 0.01 * (s - 2000)) for s in range(1992, 2021)
                          for z in bb.SIZES])
        tot = pd.DataFrame([dict(start=s, size=z, pred=100.0, actual=100.0) for s in range(2005, 2021)
                            for z in bb.SIZES])
        c = bb.coverage_check(r, tot)
        self.assertTrue(set(c.start) <= set(range(2005, 2021)))
        self.assertIn((0.025, 0.975), set(zip(c.lo, c.hi)))


if __name__ == "__main__":
    unittest.main()


class TestShares(unittest.TestCase):
    def setUp(self):
        from missing_middleware import baseline_bakeoff_shares as sh
        self.sh = sh
        rng = np.random.default_rng(1)
        self.a = rng.integers(0, 20, size=(6, len(sh.YEARS))).astype(float)
        self.county = np.array(["A", "A", "A", "B", "B", "B"])
        self.h = np.full(6, 1000.0)

    def test_lumpy_cap(self):
        a = np.zeros((1, len(self.sh.YEARS)))
        a[0, self.sh.YEARS == 2010] = 100.0
        a[0, (self.sh.YEARS >= 2006) & (self.sh.YEARS <= 2009)] = 10.0
        # the 100 counts at most 2 x 10 = 20; mean of (10, 10, 10, 10, 20) = 12
        self.assertAlmostEqual(self.sh.lumpy_cap(a, 2010)[0], 12.0)

    def test_county_pace_keeps_county_totals(self):
        p = self.sh.county_pace(self.a, self.county, 2010, 3, 10, self.h)
        own = self.sh.nanmean_win(self.a, 2010, 3)
        for c in ("A", "B"):
            self.assertAlmostEqual(p[self.county == c].sum(), own[self.county == c].sum())

    def test_shrink_endpoints(self):
        own = self.sh.nanmean_win(self.a, 2010, 3)
        np.testing.assert_allclose(self.sh.shrink(self.a, self.county, 2010, self.h, 1e-9), own, rtol=1e-6)
        big = self.sh.shrink(self.a, self.county, 2010, self.h, 1e12)
        self.assertAlmostEqual(big[:3].std(), 0.0, places=6)    # all pieces at the county rate

    def test_score_is_scale_free(self):
        arrays = {z: self.a for z in self.sh.SIZES}
        p = {z: self.sh.nanmean_win(self.a, 2010, 3) for z in self.sh.SIZES}
        p2 = {z: 7 * v for z, v in p.items()}
        self.assertAlmostEqual(self.sh.score_start(p, arrays, 2010), self.sh.score_start(p2, arrays, 2010))

    def test_homes_backcast(self):
        census = {1990: np.array([np.nan]), 2000: np.array([1000.0])}
        perm = np.zeros((1, len(self.sh.YEARS)))
        perm[0, (self.sh.YEARS > 1995) & (self.sh.YEARS <= 2000)] = 10.0
        self.assertAlmostEqual(self.sh.homes_at(census, perm, 1995, np.array([5.0]))[0], 950.0)
