"""Parking dose-response fit (docs/parking/DOSE_PLAN.md; "Ryan's choices", "C11 amended" and "Audit fixes" override the
text above them). Reads the dose working copies made by scripts/run_parking_dose.sh; writes reference/parking_dose_*.

    uv run --all-extras python scripts/run_parking_dose.py --identity  # (a) all 74 at dose 100 reproduce today's averages
    uv run --all-extras python scripts/run_parking_dose.py --first     # (a) again, then (b): gap MDE and counts, no effect of a new place
    uv run --all-extras python scripts/run_parking_dose.py --all       # (a) again, then (c): every cell and the reading

Order is enforced: every mode runs the identity check first and stops if it fails; --all refuses to start until the
--first outputs (identity, counts, MDE) are committed unchanged. Every mode refuses to start unless
reference/parking_doses.csv matches the frozen sha256 in docs/parking/DOSES_BUILT.md (audit fix 6).

Estimator (plan section 6): beta = sum(w d e) / sum(w d^2), through the origin, d = dose / 100.
- main: w = homes x after-years (the batch weight), effects not winsorised; 90% range = real beta + (p05 - p50,
  p95 - p50) of the same fit on 20,000 placebo sets (run_parking_placebo.py --full draws, seed 20261028), each stand-in
  taking its real place's dose and the stand-in's own homes x after-years.
- D: target-state mix weights (run_parking_method2.mix_weights, Wisconsin cells, base = homes x after-years) over the
  fit's places, effects winsorised 5/95 over the fit's places; 90% range from 2,000 place resamples, seed 20261105
  (weights and winsorising redone in each draw, as run_parking_method2.boot_range).
Cells (88, asserted): 2 outcomes x 2 methods x 22 statistics; see docs/parking/DOSE_CODE_NOTES.md for the map.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import parking_dose_common as dc  # noqa: E402

OUT = ROOT / "reference"
WORK = dc.WORK
DOSES, DOSES_DOC = dc.DOSES, dc.DOSES_DOC
CHECK_GIT = True
IDENTITY = dict(dc.IDENTITY)
OUT_LABEL = {"all_homes": "all new homes", "units_2_4": "2-4 unit homes"}
UNIT = "homes permitted per 1,000 existing homes a year, at dose 100 (a full citywide repeal)"
STATS = ("pooled", "full-repeal only", "low-dose only", "gap: full only minus low dose only", "intercept (dose 0)",
         "slope with intercept (per 100 dose points)", "fallback doses dropped", "fallback doses halved",
         "fallback doses doubled (cap 100)", "dose-0 places alone", "Brainerd alone", "zoned-land share doses",
         "2010-block doses (2015-2019 mapped reforms)", "partial-reform places dropped from pools",
         "lead -5", "lead -4", "lead -3", "lead -2", "placebo date -2", "placebo date -4",
         "C6 alternative: 6 discretion places at 15", "C4 alternative: citywide repeals at 100")
N_CELLS = len(dc.OUTCOMES) * len(dc.METHODS) * len(STATS)
assert N_CELLS == 88


def out(name: str) -> Path:
    return OUT / f"parking_dose_{name}.csv"


def wdir(o: str, variant: str = "") -> Path:
    return WORK / f"{o}{'_' + variant if variant else ''}_ref"


# ------------------------------------------------------------------ inputs --------------------------------------------
EFFECT_COLS = ("main_effect", "d_effect")


class Work:
    """One outcome working copy, joined to the frozen doses. With blind=True (--first) the new places' effects are
    blanked as they are read and never used."""

    def __init__(self, o: str, doses: pd.DataFrame, variant: str = "", blind: bool = False):
        self.o, self.dir = o, wdir(o, variant)
        P = pd.read_csv(self.dir / "dose_places.csv", dtype={"key": str})
        if blind:
            P.loc[P["group"] == "new", list(EFFECT_COLS)] = np.nan
        P = P.sort_values("col").reset_index(drop=True)
        P74 = P[P["group"] == "74"]
        assert len(P74) == 74 and (P74["col"].values == np.arange(74)).all(), f"{o}: the 74 rows are not cols 0-73"
        t = doses.set_index("reform_id")
        miss = set(P["reform_id"]) - set(t.index)
        assert not miss, f"{o}: places without a frozen dose: {sorted(miss)}"
        dcol = "d_24" if o == "units_2_4" else "d_all"
        for c in ("role", "role_note", "fallback", "placeholder", "type", "dose_source", "d_all", "d_24", "d_24_source",
                  "year_num", "coverage_homes_share", "coverage_homes_share_2010", "coverage_zoned_land_share", "removal_share"):
            P[c] = P["reform_id"].map(t[c]) if c in t.columns else np.nan
        P["d"] = P[dcol].astype(float)
        P["band"] = _m2().band_of(P["population"].fillna(0))
        P["base"] = P["homes"] * P["n_post"]
        P["main_ok"] = (P["main_status"] == "included") & np.isfinite(P["main_effect"]) if not blind else P["main_status"] == "included"
        self.P = P
        wi = pd.read_csv(self.dir / "dose_wi_cells.csv")
        self.wi = wi.set_index(["metro", "band"])["h"]
        st = pd.read_csv(self.dir / "dose_standins.csv")
        self.cols, self.E, self.W = dc.draw_matrix(st)
        self.summary = pd.read_csv(self.dir / "parking_placebo_full_summary.csv").iloc[0]
        r = pd.read_csv(self.dir / "parking_method2_corrected_results.csv")
        self.d74 = r[(r["variant"] == "method 2, D") & (r["weights"] == dc.MIX)].iloc[0]
        self.blind = blind

    def col_d(self, d: np.ndarray, members: np.ndarray):
        """Dose and membership of each stand-in column (the real place it stands in for)."""
        by = dict(zip(self.P["col"], range(len(self.P))))
        idx = np.array([by[c] for c in self.cols])
        return d[idx], members[idx]

    def ev(self, base=None) -> pd.DataFrame:
        P = self.P
        e = pd.DataFrame({"homes": P["homes"].values, "n_post": P["n_post"].values, "band": P["band"].values,
                          "metro": P["metro"].values, "v": 1.0})
        e["base"] = P["base"].values if base is None else np.asarray(base, float)
        return e

    def event(self) -> pd.DataFrame:
        return pd.read_csv(self.dir / "dose_event_places.csv")

    def shift(self, s: int):
        sp = pd.read_csv(self.dir / f"dose_shift{s}_places.csv")
        st = pd.read_csv(self.dir / f"dose_shift{s}_standins.csv")
        return sp, st


def _m2():
    import run_parking_method2 as m
    return m


# ------------------------------------------------------------------ cell machinery --------------------------------------
def main_cell(e, w, d, members, cols_d, cols_m, E, W):
    sel = members & np.isfinite(e)
    est = dc.beta(e[sel], d[sel], w[sel])
    draws = dc.set_betas(E, W, cols_d, cols_m)
    lo, hi = dc.placebo_range(est, draws)
    return est, lo, hi, draws


def d_cell(e, d, ev, wi, members, seed=dc.SEED):
    sel = members & np.isfinite(e)
    y, dd, evs = e[sel], d[sel], ev[sel].reset_index(drop=True)
    est = dc.d_point(y, dd, evs, wi)
    draws = dc.boot(lambda i: dc.d_point(y[i], dd[i], evs.iloc[i].reset_index(drop=True), wi), len(y), seed=seed)
    lo, hi = dc.pct_range(draws)
    return est, lo, hi, int(sel.sum())


def main_boot_cell(e, w, d, members, seed=dc.SEED):
    """Leads (Test 56 event study): main range from the place bootstrap, resampling all places (missing years drop)."""
    y, ww, dd = e[members], w[members], d[members]
    est = dc.beta(y, dd, ww)
    draws = dc.boot(lambda i: dc.beta(y[i], dd[i], ww[i]), len(y), seed=seed)
    lo, hi = dc.pct_range(draws)
    return est, lo, hi, int((np.isfinite(y) & (ww > 0)).sum())


def d_lead_cell(e, d, ev, wi, members, seed=dc.SEED):
    """Leads under D (Test 56 agg/boot): resample all places, then drop missing years, winsorise and weight."""
    y, dd, evs = e[members], d[members], ev[members].reset_index(drop=True)

    def fit(i):
        yi, di, ei = y[i], dd[i], evs.iloc[i].reset_index(drop=True)
        ok = np.isfinite(yi)
        return dc.d_point(yi[ok], di[ok], ei[ok].reset_index(drop=True), wi) if ok.any() else np.nan
    est = fit(np.arange(len(y)))
    lo, hi = dc.pct_range(dc.boot(fit, len(y), seed=seed))
    return est, lo, hi, int(np.isfinite(y).sum())


def boot_raw(fn, n, seed=dc.SEED):
    rng = np.random.default_rng(seed)
    return np.array([fn(rng.integers(0, n, n)) for _ in range(dc.DRAWS)], float)


def d_gap_cell(e, d, ev, wi, full, low):
    """Test 56 gap_cell for D: independent resamples within each group (rng restarted with the same seed), draw by draw."""
    res = {}
    for g, sel in (("full", full), ("low", low)):
        sel = sel & np.isfinite(e)
        y, dd, evs = e[sel], d[sel], ev[sel].reset_index(drop=True)
        fn = lambda i, y=y, dd=dd, evs=evs: dc.d_point(y[i], dd[i], evs.iloc[i].reset_index(drop=True), wi)  # noqa: E731
        res[g] = (fn(np.arange(len(y))), boot_raw(fn, len(y)) if len(y) else np.full(dc.DRAWS, np.nan))
    diff = res["full"][1] - res["low"][1]
    lo, hi = (np.nanpercentile(diff, [5, 95]) if np.isfinite(diff).any() else (np.nan, np.nan))
    return res["full"][0] - res["low"][0], float(lo), float(hi)


def d_line_cell(e, d, ev, wi, members):
    sel = members & np.isfinite(e)
    y, dd, evs = e[sel], d[sel], ev[sel].reset_index(drop=True)
    a, b = dc.d_point(y, dd, evs, wi, intercept=True)
    rng = np.random.default_rng(dc.SEED)
    A, B = [], []
    for _ in range(dc.DRAWS):
        i = rng.integers(0, len(y), len(y))
        ai, bi = dc.d_point(y[i], dd[i], evs.iloc[i].reset_index(drop=True), wi, intercept=True)
        A.append(ai), B.append(bi)
    return (a, *dc.pct_range(A)), (b, *dc.pct_range(B)), int(sel.sum())


# ------------------------------------------------------------------ (a) identity ----------------------------------------
def identity(doses: pd.DataFrame, blind: bool) -> pd.DataFrame:
    """Audit fix 7: all 74 at dose 100 (not the table's C4 increments) reproduce today's averages; stop if not."""
    rows = []

    def chk(o, what, got, want, tol):
        ok = bool(np.isfinite(got) and np.isfinite(want) and abs(got - want) <= tol)
        rows.append(dict(outcome=o, check=what, got=got, target=want, diff=got - want, tolerance=tol, passed=ok))

    for o in dc.OUTCOMES:
        Wk = Work(o, doses, blind=blind)
        P = Wk.P
        m74 = (P["group"] == "74").values
        one = np.ones(len(P))
        e, w = P["main_effect"].values.astype(float), P["main_weight"].values.astype(float)
        cd, cm = Wk.col_d(one, m74)
        est, lo, hi, draws = main_cell(e, w, one, m74, cd, cm, Wk.E, Wk.W)
        chk(o, "main average, 74 at dose 100 vs today's figure", est, IDENTITY[(o, "main")], dc.TOL_HARD)
        chk(o, "main average vs this copy's placebo summary", est, float(Wk.summary["real_average"]), dc.TOL_HARD)
        chk(o, "main range low vs placebo summary", lo, float(Wk.summary["range_from_placebo_low"]), dc.TOL_RANGE)
        chk(o, "main range high vs placebo summary", hi, float(Wk.summary["range_from_placebo_high"]), dc.TOL_RANGE)
        saved = pd.read_csv(Wk.dir / "parking_placebo_full_draws.csv", usecols=["placebo_average"])["placebo_average"].values
        chk(o, "placebo set draws rebuilt (max abs diff)", float(np.max(np.abs(draws - saved))), 0.0, dc.TOL_RANGE)
        ev = Wk.ev()
        yD = P["d_effect"].values.astype(float)
        dest, dlo, dhi, _ = d_cell(yD, one, ev, Wk.wi, m74, seed=dc.SEED_M2)
        chk(o, "D average, 74 at dose 100 vs today's figure", dest, IDENTITY[(o, "D")], dc.TOL_HARD)
        chk(o, "D average vs this copy's method 2 results", dest, float(Wk.d74["average"]), dc.TOL_HARD)
        chk(o, "D range low (seed 20261104) vs method 2 results", dlo, float(Wk.d74["p05"]), dc.TOL_RANGE)
        chk(o, "D range high (seed 20261104) vs method 2 results", dhi, float(Wk.d74["p95"]), dc.TOL_RANGE)
        # the lead and placebo-date machinery at dose 100 reproduces this copy's Test 56 extras
        es = pd.read_csv(Wk.dir / "parking_t56_event_study.csv")
        E = Wk.event()
        for meth in dc.METHODS:
            Em = E[E["method"] == meth].set_index("reform_id").reindex(P["reform_id"])
            for k in dc.LEADS:
                y = Em[f"k{k}"].values.astype(float)
                if meth == "main":
                    a, l, h, _ = main_boot_cell(y, P["homes"].values.astype(float), one, m74)
                else:
                    a, l, h, _ = d_lead_cell(y, one, Wk.ev(base=P["homes"].values), Wk.wi, m74)
                ref = es[(es["method"] == meth) & (es["year"] == k)].iloc[0]
                chk(o, f"lead {k} {meth} vs Test 56 event study", a, float(ref["estimate"]), dc.TOL_HARD)
                chk(o, f"lead {k} {meth} range low", l, float(ref["p05"]), dc.TOL_RANGE)
                chk(o, f"lead {k} {meth} range high", h, float(ref["p95"]), dc.TOL_RANGE)
        for s in dc.SHIFTS:
            sp, st = Wk.shift(s)
            S = pd.read_csv(Wk.dir / f"t56_placebo_shift{s}" / f"parking_t56_placebo_shift{s}_summary.csv")
            a, l, h = shifted_main(Wk, sp, st, one, m74)
            ref = S[S["estimator"] == "main (real average, placebo spread)"].iloc[0]
            chk(o, f"placebo date -{s} main vs Test 56", a, float(ref["estimate"]), dc.TOL_HARD)
            chk(o, f"placebo date -{s} main range low", l, float(ref["p05"]), dc.TOL_RANGE)
            chk(o, f"placebo date -{s} main range high", h, float(ref["p95"]), dc.TOL_RANGE)
            a, l, h, _ = shifted_d(Wk, sp, one, m74)
            ref = S[(S["estimator"] == f"method 2, D (repeals moved {s} years early)") & (S["weights"] == dc.MIX)].iloc[0]
            chk(o, f"placebo date -{s} D vs Test 56", a, float(ref["estimate"]), 2 * dc.TOL_HARD)
            chk(o, f"placebo date -{s} D range low", l, float(ref["p05"]), dc.TOL_RANGE)
            chk(o, f"placebo date -{s} D range high", h, float(ref["p95"]), dc.TOL_RANGE)
    R = pd.DataFrame(rows)
    R.round(6).to_csv(out("identity"), index=False)
    pd.set_option("display.width", 250)
    print(R.round(5).to_string(index=False))
    if not R["passed"].all():
        raise SystemExit("IDENTITY CHECK FAILED: the estimator does not reproduce today's averages; nothing else runs")
    return R


def shifted_arrays(Wk: Work, sp: pd.DataFrame):
    P = Wk.P
    s = sp.set_index("reform_id").reindex(P["reform_id"])
    inc = (s["main_status"] == "included").values
    e = np.where(inc, s["main_effect"].values.astype(float), np.nan)
    w = P["homes"].values * np.where(inc, s["main_n_post"].values.astype(float), 0.0)
    return e, w, s["d_effect"].values.astype(float), s["d_n_post"].values.astype(float)


def shifted_main(Wk: Work, sp, st, d, members):
    e, w, _, _ = shifted_arrays(Wk, sp)
    cols, E, W = dc.draw_matrix(st)
    by = dict(zip(Wk.P["col"], range(len(Wk.P))))
    idx = np.array([by[c] for c in cols])
    est = dc.beta(e[members], d[members], w[members])
    draws = dc.set_betas(E, W, d[idx], members[idx])
    return (est, *dc.placebo_range(est, draws))


def shifted_d(Wk: Work, sp, d, members):
    _, _, yd, dn = shifted_arrays(Wk, sp)
    return d_cell(yd, d, Wk.ev(base=Wk.P["homes"].values * dn), Wk.wi, members)


# ------------------------------------------------------------------ dose variants ---------------------------------------
def pooled_mask(P: pd.DataFrame) -> np.ndarray:
    return (P["role"].isin(["74", "pooled"]) & (P["d"] > 0)).values


def variant_doses(P: pd.DataFrame, name: str, o: str) -> tuple[np.ndarray, np.ndarray, str]:
    """(dose, pooled membership, note) for a dose variant; the main version is the frozen dose."""
    d = P["d"].values.astype(float).copy()
    mem = pooled_mask(P)
    note = ""
    fb = P["fallback"].fillna(False).astype(bool).values
    if name == "fallback doses dropped":
        mem = mem & ~fb
    elif name == "fallback doses halved":
        d = np.where(fb, d / 2, d)
    elif name == "fallback doses doubled (cap 100)":
        d = np.where(fb, np.minimum(d * 2, 1.0), d)
    elif name in ("zoned-land share doses", "2010-block doses (2015-2019 mapped reforms)"):
        cov = pd.to_numeric(P["coverage_zoned_land_share" if name.startswith("zoned") else "coverage_homes_share_2010"], errors="coerce")
        rem = pd.to_numeric(P["removal_share"], errors="coerce")
        alt = (cov * rem).values
        use = np.isfinite(alt) & ~fb
        if name.startswith("2010"):
            use &= P["year_num"].between(2015, 2019).values & P["type"].isin(dc.MAPPED_TYPES).values
        if o == "units_2_4":  # a use-type 2-4 dose is kept as it is (the alternative coverage is an all-homes measure)
            use &= np.isclose(P["d_24"].values.astype(float), P["d_all"].values.astype(float))
        d = np.where(use, alt, d)
        note = f"{int((use & mem).sum())} pooled places use the alternative coverage"
        mem = pooled_mask(P.assign(d=d)) & P["role"].isin(["74", "pooled"]).values
    elif name == "C6 alternative: 6 discretion places at 15":
        c6 = np.array([(p, s) in dc.C6_PLACES for p, s in zip(P["place"], P["state"])]) & (P["group"] == "74").values
        assert c6.sum() == 6, c6.sum()
        d = np.where(c6, 0.15, d)
    elif name == "C4 alternative: citywide repeals at 100":
        cw = (P["type"] == "citywide residential").values & P["role"].isin(["74", "pooled"]).values
        d = np.where(cw, 1.0, d)
        mem = (P["role"].isin(["74", "pooled"]) & (d > 0)).values
        note = f"{int((cw & (P['d'].values < 1)).sum())} citywide repeals moved back to 100"
    return d, mem, note


# ------------------------------------------------------------------ (b) --first -----------------------------------------
def first(doses: pd.DataFrame) -> None:
    identity(doses, blind=True)
    counts, mde = [], []
    for o in dc.OUTCOMES:
        Wk = Work(o, doses, blind=True)
        P = Wk.P
        mem = pooled_mask(P)
        for role in ("74", "pooled", "alone", "dose 0", "wait"):
            for b in dc.DOSE_BINS:
                sel = (P["role"] == role).values & (P["d"].map(dc.dose_bin) == b).values
                if role in ("74", "pooled") and b != "0":
                    sel &= mem
                if not sel.any():
                    continue
                counts.append(dict(outcome=OUT_LABEL[o], role=role, dose_group=b, places=int(sel.sum()),
                                   with_main_effect=int((sel & P["main_ok"].values).sum()),
                                   with_d_effect=int((sel & P["d_available"].fillna(False).astype(bool).values).sum()),
                                   fallback_dose=int((sel & P["fallback"].fillna(False).astype(bool).values).sum()),
                                   c3_placeholder_50=int((sel & P["placeholder"].fillna(False).astype(bool).values).sum()),
                                   with_any_2_4_before=int((sel & (P["rate_before"].values > 0)).sum()) if o == "units_2_4" else np.nan))
        d = P["d"].values.astype(float)
        mm = mem & P["main_ok"].values
        cd, cm = Wk.col_d(d, mm)
        full, low = cm & np.isclose(cd, 1.0), cm & (cd < 1) & (cd > 0)
        g = dc.set_betas(Wk.E, Wk.W, cd, full) - dc.set_betas(Wk.E, Wk.W, cd, low)
        bf = dc.set_betas(Wk.E, Wk.W, cd, full)
        bp = dc.set_betas(Wk.E, Wk.W, cd, cm)
        width = lambda v: float(np.percentile(v, 95) - np.percentile(v, 5))  # noqa: E731
        sd = float(np.std(g, ddof=1))
        w74 = float(Wk.summary["range_from_placebo_high"] - Wk.summary["range_from_placebo_low"])
        mde.append(dict(outcome=OUT_LABEL[o], statistic="gap: full only minus low dose only", method="main (placebo sets)",
                        placebo_sd=sd, mde=dc.Z_MDE * sd, full_only_range_width_main=width(bf),
                        low_power_main=bool(dc.Z_MDE * sd > width(bf)), pooled_range_width_main=width(bp),
                        range_width_74_main=w74, full_only_columns=int(full.sum()), low_dose_columns=int(low.sum()),
                        note="MDE = 2.486 x SD of the gap's placebo-set draws (audit fix 1); D has no stand-in spread, so this "
                             "main figure is shown beside D, whose full-only range width is known only at --all",
                        unit="homes permitted per 1,000 existing homes a year"))
    C = pd.DataFrame(counts)
    C.to_csv(out("counts"), index=False)
    M = pd.DataFrame(mde)
    M.round(6).to_csv(out("mde"), index=False)
    pd.set_option("display.width", 250)
    print(C.to_string(index=False))
    print(M.round(4).to_string(index=False))


# ------------------------------------------------------------------ (c) --all -------------------------------------------
def all_cells(doses: pd.DataFrame) -> None:
    for f in ("identity", "counts", "mde"):
        if not out(f).exists() or (CHECK_GIT and not dc.committed(out(f))):
            raise SystemExit(f"--all: run --first and commit {out(f).relative_to(ROOT) if CHECK_GIT else out(f)} unchanged first")
    identity(doses, blind=False)
    cells, places = [], []
    mde = pd.read_csv(out("mde"))
    for o in dc.OUTCOMES:
        Wk = Work(o, doses)
        Wd = Work(o, doses, variant="droppools")
        P = Wk.P
        ev = Wk.ev()
        eM, wM, eD = P["main_effect"].values.astype(float), P["main_weight"].values.astype(float), P["d_effect"].values.astype(float)
        okM = P["main_ok"].values
        mde_o = float(mde.loc[mde["outcome"] == OUT_LABEL[o], "mde"].iloc[0])
        Ev = Wk.event()
        res = {}

        def add(stat, meth, est, lo, hi, n, note="", **kw):
            cells.append(dict(cell=f"{o}|{meth}|{stat}", outcome=OUT_LABEL[o], method=meth, statistic=stat, estimate=est,
                              p05=lo, p95=hi, excludes_0=dc.excludes0(lo, hi), verdict=dc.verdict(lo, hi), places=n,
                              note=note, **kw))
            res[(meth, stat)] = cells[-1]

        for stat in STATS:
            for meth in dc.METHODS:
                d0, mem0, note = variant_doses(P, "pooled", o)
                if stat in ("pooled", "fallback doses dropped", "fallback doses halved", "fallback doses doubled (cap 100)",
                            "zoned-land share doses", "2010-block doses (2015-2019 mapped reforms)",
                            "C6 alternative: 6 discretion places at 15", "C4 alternative: citywide repeals at 100",
                            "full-repeal only", "low-dose only"):
                    d, mem, note = variant_doses(P, "pooled" if stat in ("full-repeal only", "low-dose only") else stat, o)
                    if stat == "full-repeal only":
                        mem = mem & np.isclose(d, 1.0)
                    elif stat == "low-dose only":
                        mem = mem & (d < 1) & (d > 0)
                    if meth == "main":
                        m = mem & okM
                        cd, cm = Wk.col_d(d, m)
                        est, lo, hi, _ = main_cell(eM, wM, d, m, cd, cm, Wk.E, Wk.W)
                        add(stat, meth, est, lo, hi, int(m.sum()), note)
                    else:
                        est, lo, hi, n = d_cell(eD, d, ev, Wk.wi, mem)
                        add(stat, meth, est, lo, hi, n, note)
                elif stat == "gap: full only minus low dose only":
                    full, low = mem0 & np.isclose(d0, 1.0), mem0 & (d0 < 1) & (d0 > 0)
                    if meth == "main":
                        m = mem0 & okM
                        cd, cm = Wk.col_d(d0, m)
                        bf = lambda msk: dc.beta(eM[msk & okM], d0[msk & okM], wM[msk & okM])  # noqa: E731
                        est = bf(full) - bf(low)
                        dr = dc.set_betas(Wk.E, Wk.W, cd, cm & np.isclose(cd, 1.0)) - dc.set_betas(Wk.E, Wk.W, cd, cm & (cd < 1) & (cd > 0))
                        lo, hi = dc.placebo_range(est, dr)
                        add(stat, meth, est, lo, hi, int(m.sum()), mde_main_placebo=mde_o)
                    else:
                        est, lo, hi = d_gap_cell(eD, d0, ev, Wk.wi, full, low)
                        add(stat, meth, est, lo, hi, int((mem0 & np.isfinite(eD)).sum()), "main placebo MDE shown beside D",
                            mde_main_placebo=mde_o)
                elif stat in ("intercept (dose 0)", "slope with intercept (per 100 dose points)"):
                    if (meth, "intercept (dose 0)") in res and stat.startswith("slope"):
                        continue  # filled with the intercept below
                    if meth == "main":
                        m = mem0 & okM
                        a, b = dc.wls_line(eM[m], d0[m], wM[m])
                        cd, cm = Wk.col_d(d0, m)
                        A, B = dc.set_lines(Wk.E[:, cm], Wk.W[:, cm], cd[cm])
                        add("intercept (dose 0)", meth, a, *dc.placebo_range(a, A), int(m.sum()))
                        add("slope with intercept (per 100 dose points)", meth, b, *dc.placebo_range(b, B), int(m.sum()))
                    else:
                        ra, rb, n = d_line_cell(eD, d0, ev, Wk.wi, mem0)
                        add("intercept (dose 0)", meth, *ra, n)
                        add("slope with intercept (per 100 dose points)", meth, *rb, n)
                elif stat in ("dose-0 places alone", "Brainerd alone"):
                    if stat == "Brainerd alone":
                        grp = (P["reform_id"] == "oth_brainerd_2023").values
                    else:
                        grp = (P["role"].isin(["alone", "dose 0"]) & (P["d"] == 0)).values
                    one = np.ones(len(P))  # an average, not a slope: dose 0 adds nothing through the origin
                    if meth == "main":
                        m = grp & okM
                        cd, cm = Wk.col_d(one, m)
                        est, lo, hi, _ = main_cell(eM, wM, one, m, cd, cm, Wk.E, Wk.W)
                        add(stat, meth, est, lo, hi, int(m.sum()), "average effect (homes x after-years); placebo range from its stand-ins")
                    else:
                        est, lo, hi, n = d_cell(eD, one, ev, Wk.wi, grp)
                        add(stat, meth, est, lo, hi, n, "average effect (target-state mix); place bootstrap" +
                            ("; one place: no range" if n < 2 else ""))
                elif stat == "partial-reform places dropped from pools":
                    Q = Wd.P
                    assert (Q["reform_id"].values == P["reform_id"].values).all(), "drop-pools copy: places differ"
                    if meth == "main":
                        e2, w2 = Q["main_effect"].values.astype(float), Q["main_weight"].values.astype(float)
                        m = mem0 & Q["main_ok"].values
                        cd, cm = Wd.col_d(d0, m)
                        est, lo, hi, _ = main_cell(e2, w2, d0, m, cd, cm, Wd.E, Wd.W)
                        add(stat, meth, est, lo, hi, int(m.sum()), "C5 check")
                    else:
                        est, lo, hi, n = d_cell(Q["d_effect"].values.astype(float), d0, Wd.ev(), Wd.wi, mem0)
                        add(stat, meth, est, lo, hi, n, "C5 check")
                elif stat.startswith("lead"):
                    k = int(stat.split()[-1])
                    Em = Ev[Ev["method"] == meth].set_index("reform_id").reindex(P["reform_id"])
                    y = Em[f"k{k}"].values.astype(float)
                    if meth == "main":
                        est, lo, hi, n = main_boot_cell(y, P["homes"].values.astype(float), d0, mem0)
                    else:
                        est, lo, hi, n = d_lead_cell(y, d0, Wk.ev(base=P["homes"].values), Wk.wi, mem0)
                    add(stat, meth, est, lo, hi, n, "reference year -1; place bootstrap")
                elif stat.startswith("placebo date"):
                    s = int(stat.split("-")[-1])
                    sp, st = Wk.shift(s)
                    if meth == "main":
                        e_s, w_s, _, _ = shifted_arrays(Wk, sp)
                        est, lo, hi = shifted_main(Wk, sp, st, d0, mem0)
                        add(stat, meth, est, lo, hi, int((mem0 & np.isfinite(e_s)).sum()), "placebo spread at the shifted date")
                    else:
                        est, lo, hi, n = shifted_d(Wk, sp, d0, mem0)
                        add(stat, meth, est, lo, hi, n, "place bootstrap")
        for r in P.itertuples():
            places.append(dict(outcome=OUT_LABEL[o], reform_id=r.reform_id, place=r.place, state=r.state, event_year=r.event_year,
                               role=r.role, role_note=r.role_note, dose=100 * r.d, dose_source=r.dose_source,
                               assumed_dose=bool(r.fallback), c3_placeholder_50=bool(r.placeholder), d_24_source=r.d_24_source,
                               main_status=r.main_status, main_effect=r.main_effect, main_weight=r.main_weight, d_effect=r.d_effect))
    Cdf = pd.DataFrame(cells)
    assert len(Cdf) == N_CELLS and Cdf["cell"].is_unique, (len(Cdf), N_CELLS)
    Cdf["unit"] = UNIT
    Cdf.round(6).to_csv(out("cells"), index=False)
    pd.DataFrame(places).round(6).to_csv(out("places"), index=False)
    reading(Cdf, doses)
    pd.set_option("display.width", 250)
    print(Cdf[["cell", "estimate", "p05", "p95", "verdict", "places", "note"]].round(4).to_string(index=False))


# ------------------------------------------------------------------ reading ---------------------------------------------
def reading(Cdf: pd.DataFrame, doses: pd.DataFrame) -> pd.DataFrame:
    """The four headline-switch conditions (C11 amended, audit fixes 1-4, 9), mechanically, per outcome and method."""
    def c(o, meth, stat):
        q = Cdf[(Cdf["outcome"] == OUT_LABEL[o]) & (Cdf["method"] == meth) & (Cdf["statistic"] == stat)]
        assert len(q) == 1, (o, meth, stat)
        return q.iloc[0]
    width = lambda r: float(r["p95"] - r["p05"])  # noqa: E731
    rows = []
    for o in dc.OUTCOMES:
        Wk_dir = wdir(o)
        summ = pd.read_csv(Wk_dir / "parking_placebo_full_summary.csv").iloc[0]
        r74 = pd.read_csv(Wk_dir / "parking_method2_corrected_results.csv")
        r74 = r74[(r74["variant"] == "method 2, D") & (r74["weights"] == dc.MIX)].iloc[0]
        w74 = {"main": float(summ["range_from_placebo_high"] - summ["range_from_placebo_low"]), "D": float(r74["p95"] - r74["p05"])}
        pre_items = [s for s in STATS if s.startswith(("lead", "placebo date"))]
        both = [s for s in pre_items if c(o, "main", s)["excludes_0"] and c(o, "D", s)["excludes_0"]]
        pretrend = bool(both)
        per = {}
        for meth in dc.METHODS:
            g, f, p = c(o, meth, "gap: full only minus low dose only"), c(o, meth, "full-repeal only"), c(o, meth, "pooled")
            fd = c(o, meth, "fallback doses dropped")
            c1 = not g["excludes_0"] and g["verdict"] != "no range"
            mde = float(g["mde_main_placebo"])
            low_power = bool(c1 and mde > width(f))
            c1_label = ("passed, low power" if low_power else "passed") if c1 else \
                "failed: the scaling assumption fails; the pooled estimate is not used and the full-repeal-only estimate stands"
            c2 = width(p) < w74[meth]
            c4 = fd["verdict"] == p["verdict"]
            per[meth] = (c1, c2, not pretrend, c4)
            iw = c(o, meth, "intercept (dose 0)")
            dp = c(o, meth, "partial-reform places dropped from pools")
            b10 = c(o, meth, "2010-block doses (2015-2019 mapped reforms)")
            rows += [
                dict(outcome=OUT_LABEL[o], method=meth, rule="condition 1: dose-proportional check (gap range includes 0)",
                     result=bool(c1), label=c1_label,
                     detail=f"gap {g['estimate']:.4f} [{g['p05']:.4f}, {g['p95']:.4f}]; gap MDE (main placebo) {mde:.4f} vs "
                            f"full-only range width {width(f):.4f}"),
                dict(outcome=OUT_LABEL[o], method=meth, rule="condition 2: pooled range narrower than the 74-place range",
                     result=bool(c2), label="near-automatic (audit fix 2): more places narrow a through-origin range even when the doses are wrong",
                     detail=f"pooled width {width(p):.4f} vs 74-place width {w74[meth]:.4f}"),
                dict(outcome=OUT_LABEL[o], method=meth, rule="condition 3: no pre-trend label (dose-fit leads -5..-2 and placebo dates -2, -4)",
                     result=not pretrend, label="pre-trend, not read as an effect" if pretrend else "",
                     detail=f"excluding 0 under both methods: {both}"),
                dict(outcome=OUT_LABEL[o], method=meth, rule="condition 4: reading unchanged with fallback doses dropped",
                     result=bool(c4), label="", detail=f"pooled: {p['verdict']}; fallback dropped: {fd['verdict']}"),
                dict(outcome=OUT_LABEL[o], method=meth, rule="intercept flag (intercept range excludes 0)", result=bool(iw["excludes_0"]),
                     label="the effect may not vanish at dose 0" if iw["excludes_0"] else "",
                     detail=f"intercept {iw['estimate']:.4f} [{iw['p05']:.4f}, {iw['p95']:.4f}]"),
                dict(outcome=OUT_LABEL[o], method=meth, rule="C5 label: partial-reform places left in comparison pools",
                     result=dp["verdict"] == p["verdict"],
                     label="C5: a place can be both treated and a comparison, which pulls effects toward 0; the drop-from-pools run is the check",
                     detail=f"pooled: {p['verdict']}; dropped from pools: {dp['verdict']} ({dp['estimate']:.4f})"),
                dict(outcome=OUT_LABEL[o], method=meth, rule="C10 label: 2020 blocks for all places",
                     result=b10["verdict"] == p["verdict"],
                     label="C10: for 2015-2019 reforms, 2020 blocks count homes built after the reform (partly post-treatment); 2010-block doses are the check",
                     detail=f"pooled: {p['verdict']}; 2010-block doses: {b10['verdict']} ({b10['note']})"),
            ]
        ok = all(all(v) for v in per.values())
        rows.append(dict(outcome=OUT_LABEL[o], method="both", rule="all four conditions hold under both main and D (audit fix 3)",
                         result=bool(ok), label="may be offered as the headline: Ryan decides, and the write-up says the switch came after the result"
                         if ok else "stays a sensitivity row (dose-pooled, beside the headline)",
                         detail="; ".join(f"{m}: " + ", ".join(f"c{i + 1}={'yes' if v else 'no'}" for i, v in enumerate(per[m])) for m in dc.METHODS)))
    pooled = doses[doses["role"].isin(["74", "pooled"])]
    rows.append(dict(outcome="both", method="both", rule="assumed doses in the pooled set (fallback)", result=int(pooled["fallback"].sum()),
                     label="every fallback place is marked 'assumed dose'", detail=f"C3 placeholder 50s: {int(pooled['placeholder'].sum())}"))
    rows.append(dict(outcome=OUT_LABEL["units_2_4"], method="both", rule="2-4 unit dose source",
                     result=int((pooled["d_24_source"] != "dose_units_2_4 column").sum()),
                     label="places whose 2-4 dose is the all-homes dose (the table gave no 2-4 dose)", detail=""))
    R = pd.DataFrame(rows)
    R.to_csv(out("reading"), index=False)
    print(R.to_string(index=False))
    return R


def main() -> None:
    global OUT, WORK, DOSES, DOSES_DOC, CHECK_GIT
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--identity", action="store_true")
    g.add_argument("--first", action="store_true")
    g.add_argument("--all", action="store_true")
    ap.add_argument("--work", help="(tests) folder holding <outcome>_ref working copies")
    ap.add_argument("--out", help="(tests) output folder")
    ap.add_argument("--doses", help="(tests) dose table")
    ap.add_argument("--doses-doc", help="(tests) DOSES_BUILT.md")
    ap.add_argument("--identity-targets", help="(tests) JSON {'outcome|method': value}")
    ap.add_argument("--no-git", action="store_true", help="(tests) skip the committed-file checks")
    a = ap.parse_args()
    if a.work:
        WORK = dc.WORK = Path(a.work)
    if a.out:
        OUT = Path(a.out)
        OUT.mkdir(parents=True, exist_ok=True)
    if a.doses:
        DOSES = Path(a.doses)
    if a.doses_doc:
        DOSES_DOC = Path(a.doses_doc)
    if a.identity_targets:
        IDENTITY.update({tuple(k.split("|")): v for k, v in json.loads(Path(a.identity_targets).read_text()).items()})
    CHECK_GIT = not a.no_git
    dc.require_frozen_doses(DOSES, DOSES_DOC, check_git=CHECK_GIT)
    doses = dc.load_doses(DOSES)
    dc.check_pooled(doses)
    if a.identity:
        identity(doses, blind=True)
    elif a.first:
        first(doses)
    else:
        all_cells(doses)


if __name__ == "__main__":
    main()
