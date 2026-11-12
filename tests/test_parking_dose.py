"""Parking dose-response code checks on MADE-UP data only (no permit file, no working copy, no network).
Covers the dose freeze, the pooled-set rule, the identity check (and that it stops), recovery of a planted dose slope,
the blind --first step, the --all order rule, the 88-cell map and the reading rules.

    uv run --all-extras python -m unittest tests.test_parking_dose -v
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import parking_dose_common as dc  # noqa: E402
import run_parking_dose as rd  # noqa: E402

dc.DRAWS, dc.PL_SETS = 200, 2000  # small for speed; the code reads both at call time
MIX = dc.MIX


def m2():
    import run_parking_method2 as m
    return m


def synth_doses(rng) -> pd.DataFrame:
    """A dose table shaped like scripts/build_parking_doses.py's output, over the real universe's reform_ids."""
    u = pd.read_csv(dc.UNIVERSE, dtype=str).fillna("")
    u = u[~u["could_join"].str.lower().str.startswith("no") & ~u["reform_id"].str.startswith(("oth_california_statewide", "oth_oregon_cfec"))]
    rows = []
    for r in u.itertuples():
        in74 = r.in_main_74.lower() == "yes"
        dose, src, cz, c10, rem = 100.0, "computable", "", "", 1.0
        if in74 and r.reform_id in ("rep_raleigh_2022", "rep_minneapolis_2021"):
            dose = 70.0  # a C4 increment
            rem, cz = 0.7, 1.0
        elif not in74:
            fb = r.fallback_dose.strip()
            if r.reform_id in ("oth_seabrook_2019", "oth_brainerd_2023"):
                dose = 0.0
            elif r.type == "citywide residential":
                dose = 100.0
            elif fb.replace(".", "").isdigit():
                dose, src = float(fb), "fallback"
            else:
                dose = float(rng.uniform(15, 60))
                rem = 1.0
                cz, c10 = round(dose / 100 * 1.3, 4), round(dose / 100 * 0.8, 4)
        used = "no" if r.reform_id in ("oth_spokane_2023", "oth_pomona_2024") else "yes"
        rows.append(dict(reform_id=r.reform_id, place=r.place, state=r.state, event_year=r.year, type=r.type, event_used=used,
                         eligibility=r.could_join, coverage_homes_share=dose / 100 if src != "fallback" else "",
                         coverage_homes_share_2010=c10, coverage_zoned_land_share=cz, removal_share=rem if src != "fallback" else "",
                         dose=dose, dose_source=src, fallback_class="", prior_exempt_homes_share="", homes_2020="", sources="",
                         licences="", notes=""))
    return pd.DataFrame(rows)


def write_freeze(d: Path, doses: pd.DataFrame, bad_hash=False):
    p = d / "parking_doses.csv"
    doses.to_csv(p, index=False)
    h = "0" * 64 if bad_hash else dc.sha256(p)
    (d / "DOSES_BUILT.md").write_text(f"# Doses built\n\n- `reference/parking_doses.csv` sha256 {h}\n")
    return p, d / "DOSES_BUILT.md"


def synth_work(root: Path, o: str, beta: float, seed: int, variant="", low_const=None, shock74=0.0):
    """One made-up working copy. Effects = beta x dose + noise (low-dose places get low_const instead, if given);
    stand-ins are pure noise. The Test 56 / batch summary files are computed here with independent code (the batch
    scripts' own formulas), so the identity check is a real reproduction test."""
    rng = np.random.default_rng(seed)
    m = m2()
    import run_parking_t56_extras as ex
    ex.DRAWS = dc.DRAWS
    W = root / f"{o}{'_' + variant if variant else ''}_ref"
    W.mkdir(parents=True)
    t = dc.load_doses(root.parent / "parking_doses.csv")  # root = <tmp>/work, the table is <tmp>/parking_doses.csv
    ids74 = list(dc.main74()["reform_id"])
    new = t[(t["role"] != "74") & t["event_used_yes"]]
    ids = ids74 + list(new["reform_id"])
    n = len(ids)
    d = np.array([float(t.set_index("reform_id").loc[i, "d_all"]) for i in ids])
    homes = rng.uniform(2_000, 200_000, n)
    n_post = rng.integers(1, 4, n)
    pop = homes * 2.3
    eff = beta * d + rng.normal(0, 0.05, n)
    if low_const is not None:
        eff = np.where((d < 1) & (d > 0), low_const, eff)
    effD = eff + rng.normal(0, 0.05, n)
    eff[:74] += shock74
    P = pd.DataFrame(dict(reform_id=ids, group=["74"] * 74 + ["new"] * (n - 74), col=np.arange(n), key=[f"99|{i}" for i in range(n)],
                          place=[str(t.set_index("reform_id").loc[i, "place"]) for i in ids],
                          state=[str(t.set_index("reform_id").loc[i, "state"]) for i in ids],
                          event_year=2020, homes=homes, n_post=n_post, population=pop, metro=(rng.uniform(size=n) < 0.6).astype(float),
                          main_status="included", main_effect=eff, main_weight=homes * n_post, d_effect=effD,
                          rate_before=rng.uniform(0, 2, n), d_available=True))
    P.loc[P["reform_id"] == "oth_dover_2015", "main_status"] = "excluded: too few years"  # a new place with no effect
    P.loc[P["reform_id"] == "oth_dover_2015", ["main_effect", "d_effect"]] = np.nan
    P.loc[P["reform_id"] == "oth_dover_2015", "d_available"] = False
    P.to_csv(W / "dose_places.csv", index=False)
    wi = pd.Series({(0.0, 0): 5e5, (0.0, 1): 3e5, (0.0, 2): 1e5, (0.0, 3): 0.0, (1.0, 0): 4e5, (1.0, 1): 6e5, (1.0, 2): 5e5, (1.0, 3): 3e5})
    wi.index.names = ["metro", "band"]
    wi.rename("h").reset_index().to_csv(W / "dose_wi_cells.csv", index=False)

    def standins(cols_ok, nst=30):
        rows = []
        for c in cols_ok:
            for k in range(int(rng.integers(5, nst))):
                h = rng.uniform(2_000, 200_000)
                rows.append(dict(col=c, placebo_key=f"98|{c}_{k}", event_year=2020, n_post=int(n_post[c]), homes=h,
                                 effect=rng.normal(0, 0.8), weight=h * n_post[c]))
        return pd.DataFrame(rows)
    ok_cols = [c for c in range(n) if P.loc[c, "main_status"] == "included" and c != 5]  # col 5: a real place with no stand-ins
    S = standins(ok_cols)
    S.to_csv(W / "dose_standins.csv", index=False)

    def saved_draws(S74, real_y, real_w):
        """run_parking_placebo.py --full: rng(SEED + 1), one integers call per real place in real_index order."""
        g = {i: x for i, x in S74.groupby("col")}
        r = np.random.default_rng(dc.PL_SEED)
        dr = np.column_stack([r.integers(0, len(x), dc.PL_SETS) for x in g.values()])
        E = np.column_stack([x["effect"].values[dr[:, j]] for j, x in enumerate(g.values())])
        Wt = np.column_stack([x["weight"].values[dr[:, j]] for j, x in enumerate(g.values())])
        avgs = (E * Wt).sum(1) / Wt.sum(1)
        ra = float(np.average(real_y, weights=real_w))
        p05, p50, p95 = np.percentile(avgs, [5, 50, 95])
        return avgs, ra, ra + p05 - p50, ra + p95 - p50

    avgs, ra, lo, hi = saved_draws(S[S["col"] < 74], eff[:74], homes[:74] * n_post[:74])
    pd.DataFrame({"set": np.arange(len(avgs)), "placebo_average": avgs}).to_csv(W / "parking_placebo_full_draws.csv", index=False)
    pd.DataFrame([dict(real_average=ra, range_from_placebo_low=lo, range_from_placebo_high=hi)]).to_csv(W / "parking_placebo_full_summary.csv", index=False)
    ev = pd.DataFrame(dict(homes=homes[:74], n_post=n_post[:74], band=m.band_of(pop[:74]), metro=P["metro"].values[:74], v=1.0))
    ev["base"] = ev["homes"] * ev["n_post"]
    a = m.weighted_avg(MIX, effD[:74], ev, wi)
    l, h = m.boot_range(MIX, effD[:74], ev, wi, dc.DRAWS, dc.SEED_M2)
    pd.DataFrame([dict(variant="method 2, D", weights=MIX, places=74, average=a, p05=l, p95=h)]).to_csv(
        W / "parking_method2_corrected_results.csv", index=False)
    # event study: leads / lags, planted pre-trend 0
    rows, es = [], []
    K = (-5, -4, -3, -2, 0, 1, 2, 3)
    for meth in ("main", "D"):
        vals = {k: rng.normal(0, 0.05, n) for k in K}
        vals[-5][3] = np.nan  # a place without year -5
        for i in range(n):
            rows.append(dict(method=meth, place=P.loc[i, "place"], state=P.loc[i, "state"], event_year=2020, reform_id=ids[i],
                             **{f"k{k}": vals[k][i] for k in K}))
        evh = ev.assign(base=ev["homes"])
        for k in K:
            es.append(ex.summary_row("event study", "main" if meth == "main" else "D", vals[k][:74], evh, wi, year=k))
    pd.DataFrame(rows).to_csv(W / "dose_event_places.csv", index=False)
    pd.DataFrame(es).to_csv(W / "parking_t56_event_study.csv", index=False)
    for s in dc.SHIFTS:
        inc = np.ones(n, bool)
        inc[7] = False
        se = rng.normal(0, 0.1, n)
        sd_ = rng.normal(0, 0.1, n)
        dn = np.full(n, 3)
        pd.DataFrame(dict(reform_id=ids, col=np.arange(n), shifted_event_year=2020 - s,
                          main_status=np.where(inc, "included", "excluded: too few years"), main_effect=np.where(inc, se, np.nan),
                          main_n_post=np.where(inc, n_post, np.nan), d_effect=sd_, d_n_post=dn)).to_csv(W / f"dose_shift{s}_places.csv", index=False)
        Ss = standins([c for c in range(n) if inc[c]])
        Ss.to_csv(W / f"dose_shift{s}_standins.csv", index=False)
        inc74 = inc[:74]
        _, ra_s, lo_s, hi_s = saved_draws(Ss[Ss["col"] < 74], se[:74][inc74], (homes * n_post)[:74][inc74])
        evs = pd.DataFrame(dict(homes=homes[:74], n_post=dn[:74], band=m.band_of(pop[:74]), metro=P["metro"].values[:74], v=1.0))
        evs["base"] = evs["homes"] * evs["n_post"]
        aD = m.weighted_avg(MIX, sd_[:74], evs, wi)
        lD, hD = m.boot_range(MIX, sd_[:74], evs, wi, dc.DRAWS, dc.SEED)
        dd = W / f"t56_placebo_shift{s}"
        dd.mkdir()
        pd.DataFrame([dict(estimator="main (real average, placebo spread)", weights="homes x after-years", estimate=ra_s, p05=lo_s, p95=hi_s),
                      dict(estimator=f"method 2, D (repeals moved {s} years early)", weights=MIX, estimate=aD, p05=lD, p95=hD)]).to_csv(
            dd / f"parking_t56_placebo_shift{s}_summary.csv", index=False)
    return W


class Base(unittest.TestCase):
    beta = -1.5

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        rng = np.random.default_rng(3)
        self.doses = synth_doses(rng)
        self.dpath, self.doc = write_freeze(self.root, self.doses)
        self.work = self.root / "work"
        self.work.mkdir()
        self.outd = self.root / "out"
        self.make()

    def make(self, **kw):
        targets = {}
        for j, o in enumerate(dc.OUTCOMES):
            for v in ("", "droppools"):
                W = synth_work(self.work, o, self.beta, seed=10 + j + (5 if v else 0), variant=v, **kw)
                if not v:
                    s = pd.read_csv(W / "parking_placebo_full_summary.csv").iloc[0]
                    r = pd.read_csv(W / "parking_method2_corrected_results.csv").iloc[0]
                    targets[f"{o}|main"], targets[f"{o}|D"] = float(s["real_average"]), float(r["average"])
        (self.root / "targets.json").write_text(json.dumps(targets))

    def tearDown(self):
        self.tmp.cleanup()

    def run_mode(self, mode):
        argv = sys.argv
        sys.argv = ["run_parking_dose.py", f"--{mode}", "--work", str(self.work), "--out", str(self.outd), "--doses", str(self.dpath),
                    "--doses-doc", str(self.doc), "--identity-targets", str(self.root / "targets.json"), "--no-git"]
        try:
            rd.main()
        finally:
            sys.argv = argv


class Freeze(Base):
    def test_hash_mismatch_refused(self):
        write_freeze(self.root, self.doses, bad_hash=True)
        with self.assertRaises(SystemExit):
            self.run_mode("identity")

    def test_c9_two_spokane_events_refused(self):
        d = self.doses.copy()
        d.loc[d["reform_id"] == "oth_spokane_2023", "event_used"] = "yes"
        self.dpath, self.doc = write_freeze(self.root, d)
        with self.assertRaises(SystemExit):
            self.run_mode("identity")

    def test_pooled_set_is_24_plus_central_falls(self):
        t = dc.load_doses(self.dpath)
        dc.check_pooled(t)
        self.assertEqual(int((t["role"] == "pooled").sum()), 25)
        self.assertEqual(int((t["role"] == "74").sum()), 74)
        self.assertEqual(set(t.loc[t["role"] == "alone", "reform_id"]), {"oth_seabrook_2019", "oth_brainerd_2023"})


class Identity(Base):
    def test_identity_passes(self):
        self.run_mode("identity")
        R = pd.read_csv(self.outd / "parking_dose_identity.csv")
        self.assertTrue(R["passed"].all())
        self.assertGreaterEqual(len(R), 2 * (9 + 24 + 12))

    def test_identity_stops_when_targets_differ(self):
        t = json.loads((self.root / "targets.json").read_text())
        t["all_homes|main"] += 0.01
        (self.root / "targets.json").write_text(json.dumps(t))
        with self.assertRaises(SystemExit):
            self.run_mode("first")
        self.assertFalse((self.outd / "parking_dose_mde.csv").exists())


class FirstAndAll(Base):
    def test_first_is_blind_and_all_needs_first(self):
        with self.assertRaises(SystemExit):
            self.run_mode("all")  # --first outputs missing
        self.run_mode("first")
        M1 = pd.read_csv(self.outd / "parking_dose_mde.csv")
        C1 = pd.read_csv(self.outd / "parking_dose_counts.csv")
        self.assertEqual(int(C1[(C1["role"] == "pooled")].groupby("outcome")["places"].sum().iloc[0]), 25)
        # change every new place's effect: --first must not move
        for o in dc.OUTCOMES:
            p = self.work / f"{o}_ref" / "dose_places.csv"
            P = pd.read_csv(p)
            P.loc[P["group"] == "new", ["main_effect", "d_effect"]] += 50.0
            P.to_csv(p, index=False)
        self.run_mode("first")
        M2 = pd.read_csv(self.outd / "parking_dose_mde.csv")
        pd.testing.assert_frame_equal(M1, M2)
        self.assertTrue((M1["mde"] > 0).all())

    def test_all_cells_recover_planted_slope(self):
        self.run_mode("first")
        self.run_mode("all")
        C = pd.read_csv(self.outd / "parking_dose_cells.csv").set_index("cell")
        self.assertEqual(len(C), 88)
        for o in dc.OUTCOMES:
            for meth in dc.METHODS:
                self.assertAlmostEqual(C.loc[f"{o}|{meth}|pooled", "estimate"], self.beta, delta=0.06)
                self.assertAlmostEqual(C.loc[f"{o}|{meth}|full-repeal only", "estimate"], self.beta, delta=0.06)
                self.assertAlmostEqual(C.loc[f"{o}|{meth}|low-dose only", "estimate"], self.beta, delta=0.25)
                self.assertAlmostEqual(C.loc[f"{o}|{meth}|intercept (dose 0)", "estimate"], 0.0, delta=0.1)
                self.assertAlmostEqual(C.loc[f"{o}|{meth}|slope with intercept (per 100 dose points)", "estimate"], self.beta, delta=0.15)
                self.assertTrue(C.loc[f"{o}|{meth}|pooled", "p05"] <= C.loc[f"{o}|{meth}|pooled", "estimate"] <= C.loc[f"{o}|{meth}|pooled", "p95"])
        R = pd.read_csv(self.outd / "parking_dose_reading.csv")
        self.assertIn("passed", " ".join(R["label"].fillna("").astype(str)))
        self.assertTrue(R["rule"].str.startswith("condition 1").sum() == 4 and R["rule"].str.startswith("condition 4").sum() == 4)
        self.assertTrue(R["label"].fillna("").str.contains("C5:").any() and R["label"].fillna("").str.contains("C10:").any())
        self.assertTrue(R["label"].fillna("").str.contains("near-automatic").any())


class ScalingFails(Base):
    beta = -3.0

    def make(self, **kw):
        super().make(low_const=-3.0)  # low-dose places as big as full repeals: not proportional to dose

    def test_condition1_fails(self):
        self.run_mode("first")
        self.run_mode("all")
        C = pd.read_csv(self.outd / "parking_dose_cells.csv").set_index("cell")
        g = C.loc["all_homes|main|gap: full only minus low dose only"]
        self.assertTrue(g["excludes_0"] and g["estimate"] > 0)
        R = pd.read_csv(self.outd / "parking_dose_reading.csv")
        r = R[(R["outcome"] == "all new homes") & (R["method"] == "main") & R["rule"].str.startswith("condition 1")].iloc[0]
        self.assertEqual(str(r["result"]), "False")
        self.assertIn("full-repeal-only estimate stands", r["label"])
        h = R[(R["outcome"] == "all new homes") & (R["method"] == "both") & R["rule"].str.startswith("all four")].iloc[0]
        self.assertIn("stays a sensitivity row", h["label"])


if __name__ == "__main__":
    unittest.main()
