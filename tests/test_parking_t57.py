"""Test 57 code checks on MADE-UP data only (no real panel, no network). Covers the estimator, ranges, split-cell
clusters, MDE, the too-few rule, the cell count, the reading rules, the summariser end to end, and the NY build's
MIH, placement and panel pieces.

    uv run python -m unittest tests.test_parking_t57 -v
"""
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import parking_t57_common as C  # noqa: E402


def synth(run: C.Run, first_year: int, effect=0.0, pretrend=0.0, n=60, split=20, jobs_before=5, seed=1,
          noise=0.3) -> pd.DataFrame:
    """Made-up panel: n clusters per arm (the first `split` T clusters also hold a C part, as split cells). Rates per
    100 acres = 2 + 0.1 x (year - first) + noise; T gets `effect` in years > wave and `pretrend` x (year - wave) before."""
    rng = np.random.default_rng(seed)
    yrs = range(first_year, max(run.after) + 1)
    rows = []
    for arm, ids in (("T", range(n)), ("C", list(range(split)) + list(range(n, 2 * n - split)))):
        for c in ids:
            acres = 10.0 + c % 7
            for y in yrs:
                rate = 2 + 0.1 * (y - first_year) + rng.normal(0, noise)
                if arm == "T":
                    rate += effect * (y > run.wave_year) + pretrend * min(y - run.wave_year, 0)
                rows.append(dict(cluster=c, arm=arm, year=y, units=max(rate, 0) * acres / 100, acres=acres,
                                 jobs=jobs_before if y in run.before else 1))
    return pd.DataFrame(rows)


class Estimator(unittest.TestCase):
    R = C.RUNS["ny_dob"]

    def test_effect_recovered_without_noise(self):
        p = synth(self.R, 2007, effect=1.5, noise=0.0)
        c = pd.DataFrame(C.cells(self.R, p, 2007)).set_index("cell")
        self.assertAlmostEqual(c.loc["ny_dob:main", "estimate"], 1.5, places=9)
        self.assertTrue(c.loc["ny_dob:main", "excludes_0"] or c.loc["ny_dob:main", "p05"] == c.loc["ny_dob:main", "p95"])
        for k in (-5, -4, -3, -2):
            self.assertAlmostEqual(c.loc[f"ny_dob:es{k:+d}", "estimate"], 0.0, places=9)
        self.assertAlmostEqual(c.loc["ny_dob:es+0", "estimate"], 0.0, places=9)    # effect starts after year 0
        self.assertAlmostEqual(c.loc["ny_dob:es+3", "estimate"], 1.5, places=9)
        self.assertAlmostEqual(c.loc["ny_dob:placebo-3", "estimate"], 0.0, places=9)

    def test_noise_range_and_pretrend(self):
        p = synth(self.R, 2007, effect=0.0, pretrend=0.4)
        c = pd.DataFrame(C.cells(self.R, p, 2007)).set_index("cell")
        self.assertTrue(c.loc["ny_dob:es-5", "excludes_0"])                       # planted pre-trend is seen
        self.assertLess(c.loc["ny_dob:es-5", "estimate"], 0)

    def test_cell_counts(self):
        self.assertEqual({k: r.n_cells for k, r in C.RUNS.items()},
                         dict(ny_dob=15, ny_dob_keepmih=15, ny_dob_samezone=15, ny_dob_legacy2020=12, ny_hpd=10,
                              ny_hpd_keepmih=10, sf_a=18))
        self.assertEqual(C.N_CELLS, 95)
        self.assertEqual(C.RUNS["ny_hpd"].es_years, (-2, 0, 1, 2, 3, 4, 5, 6, 7))
        self.assertEqual(C.RUNS["ny_dob"].placebo(3, 2007), (2013, (2008, 2009, 2010, 2011, 2012), (2014, 2015)))
        self.assertEqual(C.RUNS["ny_dob"].placebo(4, 2007), (2012, (2007, 2008, 2009, 2010, 2011), (2013, 2014, 2015)))
        self.assertEqual(C.RUNS["sf_a"].placebo(4, 2003), (2004, (2003,), (2005, 2006, 2007)))

    def test_split_cells_move_together(self):
        p = synth(self.R, 2007, n=30, split=30)                                  # every cluster split
        ar = C.arrays(p, range(2007, 2024))
        self.assertEqual(len(ar.clusters), 30)                                     # 30 clusters, 60 cell parts
        self.assertEqual(ar.parts, {"T": 30, "C": 30})
        W = C.boot_weights(len(ar.clusters), draws=50)
        self.assertTrue((W.sum(1) == 30).all())
        # the same weight row multiplies both arms' rows of a cluster: arm acres move in lockstep for split clusters
        np.testing.assert_allclose(W @ ar.A["T"][:, :1], W @ ar.A["C"][:, :1])

    def test_seed_and_draws(self):
        W1, W2 = C.boot_weights(40), C.boot_weights(40)
        np.testing.assert_array_equal(W1, W2)
        self.assertEqual(W1.shape, (C.DRAWS, 40))

    def test_mde_no_estimate(self):
        m = C.mde(self.R, synth(self.R, 2007))
        self.assertGreater(m["mde"], 0)
        self.assertNotIn("estimate", m)
        self.assertNotIn("p05", m)
        self.assertAlmostEqual(m["mde"], C.Z_MDE * m["bootstrap_sd"])

    def test_too_few(self):
        ok = C.counts(self.R, synth(self.R, 2007, n=25, split=0, jobs_before=5))
        self.assertFalse(ok["too_few_to_read"])
        few_cells = C.counts(self.R, synth(self.R, 2007, n=19, split=0))
        self.assertTrue(few_cells["too_few_to_read"])
        p = synth(self.R, 2007, n=25, split=0, jobs_before=0)
        p.loc[(p.arm == "C") & p.year.isin(self.R.before) & (p.cluster < 1025), "jobs"] = 1  # 25 C clusters x 5 years
        few_jobs = C.counts(self.R, p)
        self.assertEqual(few_jobs["before_jobs_T"], 0)
        self.assertTrue(few_jobs["too_few_to_read"])

    def test_empty_arm_draw_is_nan_not_crash(self):
        p = synth(self.R, 2007, n=3, split=0)
        c = C.cells(self.R, p, 2007)
        self.assertEqual(len(c), 15)


class EndToEnd(unittest.TestCase):
    def test_summariser_first_then_all(self):
        import summarise_parking_t57 as S
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            for j, (k, r) in enumerate(C.RUNS.items()):
                eff, noise = (2.0, 0.0) if k == "ny_dob" else (0.0, 0.3)   # ny_dob: exact, so leads are exactly 0
                synth(r, C.FIRST_YEAR[r.city] if not k.startswith("ny_hpd") else 2014, effect=eff, noise=noise,
                      seed=j).to_csv(td / f"panel_{k}.csv", index=False)
            S.main(["--first", "--panels", str(td), "--out", str(td), "--tag", "_synthetic"])
            cnt = pd.read_csv(td / "parking_t57_counts_synthetic.csv")
            self.assertEqual(len(cnt), 7)
            self.assertNotIn("estimate", pd.read_csv(td / "parking_t57_mde_synthetic.csv").columns)
            S.main(["--all", "--panels", str(td), "--out", str(td), "--tag", "_synthetic"])
            cells = pd.read_csv(td / "parking_t57_cells_synthetic.csv")
            self.assertEqual(len(cells), 95)
            rd = pd.read_csv(td / "parking_t57_reading_synthetic.csv").set_index("run")
            self.assertTrue(rd.loc["ny_dob", "headline"])
            self.assertIn("counts", rd.loc["ny_dob", "reading"])                   # planted effect counts
            self.assertIn("diluted", rd.loc["ny_dob", "labels"])
            self.assertIn("imbalance", rd.loc["ny_dob", "balance"])
            self.assertIn("112-08", rd.loc["sf_a", "labels"])
            self.assertEqual(rd.loc["ny_hpd", "placebo_dates_read"], "none (cannot run)")

    def test_reading_rules(self):
        run = C.RUNS["ny_dob"]
        base = pd.DataFrame(C.cells(run, synth(run, 2007, effect=2.0), 2007))
        others = pd.concat([pd.DataFrame(C.cells(r, synth(r, C.FIRST_YEAR[r.city] if not k.startswith("ny_hpd") else 2014), C.FIRST_YEAR[r.city]))
                            for k, r in C.RUNS.items() if k != "ny_dob"])
        cells = pd.concat([base, others], ignore_index=True)
        cnt = pd.DataFrame([dict(run=k, too_few_to_read=False) for k in C.RUNS])
        mde = pd.DataFrame([dict(run=k, mde=1.0) for k in C.RUNS])
        r = C.reading(cells, cnt, mde).set_index("run")
        self.assertTrue(r.loc["ny_dob", "reading"].startswith("counts"))
        # a lead excluding 0 overrides
        cells.loc[cells.cell == "ny_dob:es-3", ["excludes_0"]] = True
        r = C.reading(cells, cnt, mde).set_index("run")
        self.assertEqual(r.loc["ny_dob", "reading"], "pre-trend, not read as an effect")
        # too few overrides everything
        cnt.loc[cnt.run == "ny_dob", "too_few_to_read"] = True
        r = C.reading(cells, cnt, mde).set_index("run")
        self.assertEqual(r.loc["ny_dob", "reading"], "too few to read")
        # lags never set the pre-trend label
        cells.loc[cells.cell == "ny_dob:es-3", ["excludes_0"]] = False
        cells.loc[cells.cell == "ny_dob:es+1", ["excludes_0"]] = True
        cnt.loc[cnt.run == "ny_dob", "too_few_to_read"] = False
        self.assertFalse(C.reading(cells, cnt, mde).set_index("run").loc["ny_dob", "pre_trend"])


class NYBuildPieces(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import build_parking_t57_ny_panel as B
        cls.B = B

    def test_mih_share(self):
        s = self.B.year_share_before(pd.Series(pd.to_datetime([None, "2017-07-02", "2015-01-01", "2019-01-01"])), 2017)
        np.testing.assert_allclose(s, [1.0, 182 / 365, 0.0, 1.0])

    def test_place(self):
        G = self.B.G
        lots = pd.DataFrame({"bbl": [1000010001, 1000010002, 1000020001]})
        lots["XCoord"], lots["YCoord"] = G.transform(np.array([-74.0, -74.001, -73.99]), np.array([40.7, 40.7, 40.71]), 4326, 2263)
        rec = pd.DataFrame({"bbl": [1000010001, 1000010001, np.nan, 9999999999, np.nan],
                            "lat": [40.7, 40.71, 40.70001, 40.5, np.nan], "lon": [-74.0, -73.99, -74.001, -74.2, np.nan]})
        i, d = self.B.place(rec, lots)
        self.assertEqual(i.tolist(), [0, 2, 1, -1, -1])   # bbl; bbl too far -> point (lot 2); point; nothing; nothing
        self.assertEqual(d["bbl_rejected_far"], 1)

    def test_panel_mih_drop(self):
        lots = pd.DataFrame({"cluster": [1, 1, 2], "arm": ["T", "C", "C"], "acres": [1.0, 2.0, 4.0],
                             "mih_date": pd.to_datetime([None, "2018-01-01", None])})
        rec = pd.DataFrame({"lot": [0, 1, 1, 2], "units": [5.0, 7.0, 3.0, 2.0],
                            "date": pd.to_datetime(["2017-05-01", "2017-12-31", "2018-02-01", "2018-03-03"])})
        keep = np.array([True, True, True])
        P = self.B.panel(lots, rec, range(2017, 2019), True, keep).set_index(["cluster", "arm", "year"])
        self.assertEqual(P.loc[(1, "C", 2017), "units"], 7.0)
        self.assertEqual(P.loc[(1, "C", 2018), "units"], 0.0)                     # filed after adoption: dropped
        self.assertEqual(P.loc[(1, "C", 2018), "acres"], 0.0)
        self.assertEqual(P.loc[(1, "C", 2017), "acres"], 2.0)
        Pk = self.B.panel(lots, rec, range(2017, 2019), False, keep).set_index(["cluster", "arm", "year"])
        self.assertEqual(Pk.loc[(1, "C", 2018), "units"], 3.0)
        self.assertEqual(Pk.loc[(1, "C", 2018), "acres"], 2.0)


if __name__ == "__main__":
    unittest.main()
