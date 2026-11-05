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
