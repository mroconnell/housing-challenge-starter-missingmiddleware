"""Offline tests for the pooled multi-state regression and the statewide adoption curve
(missing_middleware.comparison.pooled_regression)."""
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.comparison import pooled_regression as pr

FIX = Path(__file__).parent / "fixtures" / "pooled_regression"
REF = Path(__file__).parent.parent / "reference"
PATHS = {t: FIX / f"acsdt5y2024-{t}.dat" for t in ("b25024", "b25077", "b19013", "b25064", "b25003")}


def synthetic(alpha, beta_dev=0.8, law=0.9, k1=-0.5, seed=1, n_places=30, years=range(1, 6)):
    """Clusters with known per-state intercepts. Cluster 'A' has many places (within-state value
    spread); the others are single-member states observed before and after a law."""
    rng = np.random.default_rng(seed)
    rows, mem = [], []
    for c, a in alpha.items():
        n = n_places if c == "A" else 1
        v = np.exp(rng.normal(np.log(400_000), 0.4 if n > 1 else 0.0, n))
        h = rng.integers(2_000, 20_000, n).astype(float)
        dev = np.log(v) - np.average(np.log(v), weights=h)
        for i in range(n):
            gid = f"{c}:{i}"
            mem.append(dict(group_id=gid, geoid=gid, sumlevel="160", homes=h[i], value=v[i], income=80_000.0,
                            rent=1200.0, renter_share=0.3, filled=""))
            for y in years:
                lw = 0 if (c != "A" and y <= 2) else 1
                k = y - 2 if c != "A" else y
                if lw == 1 and k < 1:
                    continue
                rate = np.exp(a + beta_dev * dev[i] + law * lw + k1 * (lw and k == 1))
                cnt = float(rng.poisson(rate * h[i] / 1000 * 5000) / 5000)    # low-noise counts
                rows.append(dict(cluster=c, series=c, group_id=gid, year=y, count=cnt, years=1.0, law=lw,
                                 local=0, k=(k if lw else np.nan), incl_new_house=True, coverage=1.0, pre_rate=np.nan))
    return pr.Pooled(pd.DataFrame(rows), pd.DataFrame(mem))


class TestACS(unittest.TestCase):
    def test_read_and_fallbacks(self):
        acs = pr.read_acs_members(PATHS, {"23", "53"})
        row = acs.set_index(["geoid", "sumlevel"])
        self.assertEqual(row.loc[("5363000", "160"), "value"], 2_000_000)      # top code minus one
        self.assertEqual(row.loc[("5363000", "160"), "income"], 250_000)
        self.assertTrue(np.isnan(row.loc[("2300100002", "060"), "value"]))      # special code -> missing, never zero
        self.assertAlmostEqual(row.loc[("2300100001", "060"), "renter_share"], 0.25)
        m = pr.members_for(acs, "cousubs", "23", "23").set_index("geoid")
        self.assertNotIn("2300100003", m.index)                                  # zero homes dropped
        self.assertEqual(m.loc["2300100002", "value"], 280_000)                  # county first
        self.assertIn("value_county", m.loc["2300100002", "filled"])
        self.assertEqual(m.loc["2300300001", "income"], 70_000)                  # county missing -> state
        self.assertIn("income_parent", m.loc["2300300001", "filled"])
        self.assertEqual(m["homes"].sum(), 600)                                  # members add up to the state


class TestCoding(unittest.TestCase):
    def test_partial_law_years_dropped(self):
        annual = pd.DataFrame({"series": "OR_panel32_exPortland", "year": [2018, 2019, 2020], "adu_count": [10, 20, 30]})
        r = pr.state_rows(annual, {"OR_panel32_exPortland": pr.STATE_CODING["OR_panel32_exPortland"]})
        self.assertEqual(r["year"].tolist(), [2019, 2020])
        self.assertEqual(r["k"].tolist(), [1, 2])
        self.assertTrue((r["law"] == 1).all())

    def test_measurement_adjustments_named(self):
        r = pd.DataFrame({"cluster": ["ME", "CA"], "count": [100.0, 100.0], "incl_new_house": [True, True],
                          "coverage": [0.5, 1.0]})
        a = pr.adjust_counts(r, new_house=True, coverage=True)
        self.assertAlmostEqual(a.loc[0, "count"], 100 * pr.NEW_HOUSE_FACTOR / 0.5)
        self.assertAlmostEqual(a.loc[1, "count"], 100.0)                        # California APR left as is
        self.assertTrue(pr.adjust_counts(r).equals(r))                           # nothing applied by default


class TestFits(unittest.TestCase):
    def test_one_stage_recovers_single_member(self):
        rng = np.random.default_rng(3)
        v = np.exp(rng.normal(np.log(400_000), 0.5, 200))
        h = np.full(200, 5000.0)
        rate = np.exp(-0.5 + 0.7 * np.log(v / 500_000))
        mem = pd.DataFrame({"group_id": [f"g{i}" for i in range(200)], "geoid": [f"g{i}" for i in range(200)],
                            "homes": h, "value": v, "income": 80_000.0, "rent": 1.0, "renter_share": 0.3})
        rows = pd.DataFrame({"cluster": "X", "series": "X", "group_id": mem["group_id"], "year": 2020,
                             "count": rate * h / 1000, "years": 1.0, "law": 1, "local": 0, "k": 4,
                             "pre_rate": np.nan})
        f = pr.fit_pooled(pr.Pooled(rows, mem), pr.PSpec("t", ("log_value",)))
        np.testing.assert_allclose(f.coef()[["intercept", "log_value"]].to_numpy(), [-0.5, 0.7], atol=1e-6)

    def test_two_stage_levels_and_loso(self):
        alpha = {"A": -0.5, "B": -1.0, "C": -0.7, "D": -0.9}
        p = synthetic(alpha)
        sp = pr.TSpec("t", ("value_dev", "law", "k1"), ())
        f = pr.fit_two_stage(p, sp)
        b = dict(zip(f.within_names, f.beta))
        self.assertAlmostEqual(b["value_dev"], 0.8, delta=0.05)
        self.assertAlmostEqual(b["law"], 0.9, delta=0.08)
        # stage 2 with a common level = mean of the state intercepts, every state once
        self.assertAlmostEqual(f.gamma[0], f.alpha.mean(), places=10)
        self.assertAlmostEqual(f.tau, np.std(f.alpha.to_numpy(), ddof=1), places=10)
        np.testing.assert_allclose(f.alpha.sort_index().to_numpy(), [alpha[c] for c in sorted(alpha)], atol=0.08)
        lo = pr.loso_ts(p, sp)
        self.assertEqual(set(lo["held_out"]), set(alpha))
        # held-out state predicted from the others' mean level
        bpred = lo.set_index("held_out").loc["B", "pred_rate"]
        others = np.mean([alpha[c] for c in ("A", "C", "D")])
        self.assertAlmostEqual(np.log(bpred), others + 0.9 - 0.5 * 1 / 3, delta=0.15)  # k1 in 1 of 3 law years

    def test_centering_makes_state_mean_zero(self):
        m = pd.DataFrame({"cluster": ["W", "W", "W"], "geoid": ["a", "b", "c"], "homes": [1.0, 2.0, 1.0],
                          "value": [200_000.0, 300_000.0, 400_000.0], "income": [5e4, 6e4, 7e4], "law": 1, "local": 0,
                          "k": 1.0, "pre_rate": np.nan})
        for c, v in pr.context(m["homes"], m["value"], m["income"]).items():
            m[c] = v
        X, names = pr.design(m, ("value_dev", "log_homes", "law"))
        Xc = pr.center_within(X, names, m)
        for j, nm in enumerate(names):
            if nm in pr.MARKET_TERMS:
                self.assertAlmostEqual(np.average(Xc[:, j], weights=m["homes"]), 0.0, places=12)
        self.assertTrue((Xc[:, names.index("law")] == 1).all())               # indicators untouched

    def test_cluster_weights_equal_states(self):
        rows = pd.DataFrame({"cluster": ["CA"] * 3 + ["ME"], "years": 1.0})
        homes = pd.Series([1000.0, 2000.0, 7000.0, 500.0])
        w = pr.cluster_weights(rows, homes)
        hy = homes.to_numpy() * w
        self.assertAlmostEqual(hy[:3].sum(), hy[3])                             # each state's home-years weigh the same


class TestAdoptionAndWisconsin(unittest.TestCase):
    def test_curve_median_and_hold(self):
        pts = pd.DataFrame({"cluster": ["A", "B", "C", "A", "B"], "k": [1, 1, 1, 2, 2], "rate": [0.6, 0.8, 1.0, 0.9, 1.1],
                            "incl_new_house": True, "coverage": [1.0, 0.5, 1.0, 1.0, 1.0]})
        c = pr.adoption_curve(pts, max_k=3)
        self.assertEqual(c["median_rate"].tolist(), [0.8, 1.0, 1.0])
        self.assertEqual(c["n_states"].tolist(), [3, 2, 2])
        self.assertIn("holds year 2", c.loc[2, "basis"])
        cc = pr.adoption_curve(pts, max_k=1, coverage=True)
        self.assertAlmostEqual(cc.loc[0, "median_rate"], 1.0)                   # B: 0.8 / 0.5 = 1.6 -> median 1.0
        app = pr.apply_curve(np.array([1.0, 2.0]), np.array([100.0, 100.0]), homes=1_000_000)
        self.assertEqual(app["additional"].tolist(), [900.0, 1900.0])

    def test_additional_never_below_current_rate(self):
        wi = pd.DataFrame({"homes": [1000.0, 1000.0], "x_rate": [0.5, 0.1]})
        Y = np.array([[0.2, 1.0], [0.3, 1.1]])
        self.assertEqual(pr.additional(wi, Y, None).round(6).tolist(), [0.2, 1.5])   # area 0 adds 0 in year 1, not negative
        # homes-weighted rates 0.25 and 1.05 against a mean current rate of 0.3: ramp 0 (clipped), then 1
        np.testing.assert_allclose(pr.implied_ramp(wi, Y), [0.0, 1.0])


class TestReferenceOutputs(unittest.TestCase):
    """Consistency of committed outputs (skipped before the first run)."""

    def test_adoption_curve_arithmetic(self):
        f = REF / "statewide_adoption_curve.csv"
        if not f.exists():
            self.skipTest("run scripts/run_pooled_regression.py first")
        c = pd.read_csv(f)
        np.testing.assert_allclose(c["with_law_total_as_reported"], pr.WI_HOMES * c["rate_as_reported"] / 1000, rtol=1e-3)
        np.testing.assert_allclose(c["additional_as_reported"], c["with_law_total_as_reported"] - c["baseline"], atol=0.01)
        self.assertTrue((c["n_states"] >= 3).all())

    def test_statewide_paths_ordered(self):
        f = REF / "pooled_wi_statewide.csv"
        if not f.exists():
            self.skipTest("run scripts/run_pooled_regression.py first")
        t = pd.read_csv(f, dtype={"year": str}).query("year == '1-5'").set_index("path")["additional"]
        self.assertLess(t["lower_95"], t["lower_80"])
        self.assertLess(t["lower_80"], t["central"])
        self.assertLess(t["central"], t["upper_80"])
        self.assertLess(t["upper_80"], t["upper_95"])

    def test_by_area_matches_statewide(self):
        fa, fs = REF / "pooled_wi_y_by_area.csv", REF / "pooled_wi_statewide.csv"
        if not (fa.exists() and fs.exists()):
            self.skipTest("run scripts/run_pooled_regression.py first")
        a = pd.read_csv(fa)
        s = pd.read_csv(fs, dtype={"year": str})
        s = s[(s.path == "central") & (s.year != "1-5")]
        for k in range(1, 6):
            rate = (a["homes"] * a[f"y_k{k}_central"]).sum() / a["homes"].sum()
            self.assertAlmostEqual(rate, float(s[s.year == str(k)]["rate"].iloc[0]), places=3)
        self.assertEqual(len(a), 1925)


if __name__ == "__main__":
    unittest.main()
