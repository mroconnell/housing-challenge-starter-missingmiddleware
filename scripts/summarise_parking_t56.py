"""Test 56 summary (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Test 56: one reading at lock"): the 4 headline and 70
sensitivity cells, read from the outcome working copies made by scripts/run_parking_t56.sh.

    uv run --all-extras python scripts/summarise_parking_t56.py --first   # step 1: before-window counts and MDE only
    uv run --all-extras python scripts/summarise_parking_t56.py --all     # every cell (after the counts are reported)

--first reads no repeal-place effect: only each repeal place's before-window 2-4 unit rate (whether it is above 0) and
the stand-in (never-repealed) places' placebo effects. Outputs reference/parking_t56_counts.csv, parking_t56_mde.csv.
--all writes reference/parking_t56_cells.csv (74 rows), parking_t56_places.csv, parking_t56_rtm.csv,
parking_t56_reading.csv (the lock's reading rules applied mechanically).

Inputs: data/processed/t56/<outcome>_ref/ for units_2_4, 1unit_units, 5plus_units, units_2_4_rep (pipeline outputs;
units_2_4 also the extras), reference/parking_t56_flags.csv (2010 population, flags, Oregon; committed first).

Conventions (as Test 53 unless said):
- Overall effect, main: the placebo summary's real average (homes x after-years) and range_from_placebo_low/high.
  Equal weight: plain mean of the place effects, range = mean + (5th - 50th, 95th - 50th percentile) of the same
  20,000 stand-in set draws (run_parking_placebo.py's seed 20261028, rebuilt from the saved stand-in effects), set
  averages unweighted. Subsets (flag/drop, no Oregon): the same draws restricted to the kept places' columns.
- Overall effect, D: run_parking_method2 results "method 2, D" with "target-state mix" (main) and "equal"; subsets use
  method 2's weighted_avg and boot_range (2,000 draws, seed 20261104) on the kept places.
- Size slope: weighted least-squares slope of the place effect on log10(2010 population), per 10x population;
  main weights homes x after-years (unwinsorised), D target-state mix weights (winsorised 5/95), equal weight
  winsorised for both (Test 53); 90% range from 2,000 place resamples, seed 20261105.
- 25,000 gap: (average for 25,000+) minus (average for under 25,000), 2010 population; each group's average as in
  Test 53's groups (main: homes x after-years; D: target-state mix within the group; equal: winsorised mean for main,
  method 2 "equal" for D); range from independent within-group resamples (2,000, seed 20261105), draw by draw.
  Same sign as the slope = agrees; 0 or opposite = does not agree.
- MDE (minimum detectable effect, 90% two-sided test, 80% power): 2.486 x the standard deviation of the stand-in set
  averages (or of the stand-in set slopes / gaps, computed with the real places' 2010 populations and weights). Main
  method only; D has no stand-in spread, so the main figure is shown beside D cells and labelled so.
- "Too few to read": fewer than 10 places with any 2-4 unit permits in the main before window (rate_before > 0 in the
  units_2_4 run), "overall or in a size group" (lock): every cell checks its sample overall; every size-slope and
  25,000-gap cell is also labelled "too few to read" when either size group (25,000+ / under 25,000) in its sample has
  fewer than 10. parking_t56_reading.csv shows the label beside each "counts" rule.
- Poisson cells are labelled "stacked two-period per place (changed from Tests 38–39 panel)".

--dryrun reads data/processed/t56/dryrun_allhomes_ref/ (scripts/run_parking_t56.sh all ..., MM_BPS_OUTCOME unset, the
already-seen all-homes outcome) for every outcome slot and writes to data/processed/t56/dryrun_allhomes_summary/ with
a _dryrun_allhomes suffix; nothing in reference/ is written. It checks that the chain runs, not any result.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.pop("MM_BPS_OUTCOME", None)
if os.environ.get("MM_REFERENCE_DIR"):
    raise SystemExit("run without MM_REFERENCE_DIR: outputs go to reference/, inputs are read from data/processed/t56/")

import parking_t56_common as c56  # noqa: E402

REF = ROOT / "reference"  # inputs (flag list); outputs too unless --dryrun
OUT = REF
SUFFIX = ""
DRYRUN = False
T56 = ROOT / "data" / "processed" / "t56"
SEED, DRAWS = c56.SEED, c56.DRAWS
PL_SEED, PL_SETS = 20261027 + 1, 20_000  # run_parking_placebo.py: set draws use SEED + 1, 20,000 sets with --full
Z_MDE = 1.6449 + 0.8416
THIN = 10
MIX = "target-state mix"
OUT_LABEL = {"units_2_4": "2-4 unit homes", "1unit_units": "1-unit homes", "5plus_units": "5+ unit homes",
             "units_2_4_rep": "2-4 unit homes, reported-only"}


def work(o: str) -> Path:
    return T56 / ("dryrun_allhomes_ref" if DRYRUN else f"{o}_ref")


def out(name: str) -> Path:
    """Output path: reference/parking_t56_<name>.csv, or the dry-run folder with the _dryrun_allhomes suffix."""
    return OUT / f"parking_t56_{name}{SUFFIX}.csv"


POISSON_DESIGN = "stacked two-period per place (changed from Tests 38–39 panel)"


def flags() -> pd.DataFrame:
    f = pd.read_csv(REF / "parking_t56_flags.csv", dtype={"key": str})
    assert len(f) == 74 and (f["i"].values == np.arange(74)).all()
    return f


def real_frame(o: str, cols) -> pd.DataFrame:
    """The 74 places in the batch order (expanded effects, included, outcome 'all'), selected columns only."""
    r = pd.read_csv(work(o) / "parking_expanded_effects.csv", usecols=list(set(cols) | {"key", "status", "outcome"}), dtype={"key": str})
    r = r[(r["status"] == "included") & (r["outcome"] == "all")].reset_index(drop=True)
    assert (r["key"].values == flags()["key"].values).all(), f"{o}: place order differs from the flag list"
    return r


# ------------------------------------------------------------------ stand-in draws ------------------------------------
def standin_draws(o: str):
    """Rebuild run_parking_placebo.py --full's 20,000 set draws from the saved stand-in effects (stand-ins only)."""
    pl = pd.read_csv(work(o) / "parking_placebo_full_places.csv")
    pl = pl.dropna(subset=["effect", "weight"])
    pl = pl[pl["weight"] > 0]
    groups = {i: g for i, g in pl.groupby("real_index")}
    rng = np.random.default_rng(PL_SEED)
    draws = np.column_stack([rng.integers(0, len(g), PL_SETS) for g in groups.values()])
    E = np.column_stack([g["effect"].values[draws[:, j]] for j, g in enumerate(groups.values())])
    W = np.column_stack([g["weight"].values[draws[:, j]] for j, g in enumerate(groups.values())])
    saved = pd.read_csv(work(o) / "parking_placebo_full_draws.csv", usecols=["placebo_average"])["placebo_average"].values
    check = float(np.max(np.abs((E * W).sum(1) / W.sum(1) - saved)))
    return np.array(list(groups)), E, W, check


def set_avgs(cols, E, W, equal: bool, mask=None):
    sel = np.ones(len(cols), bool) if mask is None else mask
    if equal:
        return E[:, sel].mean(axis=1)
    return (E[:, sel] * W[:, sel]).sum(axis=1) / W[:, sel].sum(axis=1)


def set_slopes(cols, E, x, w):
    """WLS slope of each set's stand-in effects on the real places' log10 2010 population, real places' weights."""
    xx, ww = x[cols], w[cols]
    xm = np.sum(ww * xx) / ww.sum()
    ym = (E * ww).sum(axis=1) / ww.sum()
    return ((E - ym[:, None]) * (ww * (xx - xm))).sum(axis=1) / np.sum(ww * (xx - xm) ** 2)


def set_gaps(cols, E, big, w):
    b, s = big[cols], ~big[cols]
    ww = w[cols]
    return (E[:, b] * ww[b]).sum(1) / ww[b].sum() - (E[:, s] * ww[s]).sum(1) / ww[s].sum()


# ------------------------------------------------------------------ step 1: counts and MDE ----------------------------
def any_before(o="units_2_4") -> np.ndarray:
    return (real_frame(o, ["rate_before"])["rate_before"].values > 0)


def first() -> None:
    F = flags()
    big = (F["pop2010"] >= c56.SPLIT).values
    has = any_before()
    rows = []
    for lab, sel in (("all 74 places", np.ones(74, bool)), ("under 25,000", ~big), ("25,000 or more", big),
                     ("without flagged places", ~F["flag_plex"].values), ("without Oregon", ~F["oregon"].values)):
        n = int(has[sel].sum())
        rows.append(dict(sample=lab, places=int(sel.sum()), places_with_any_2_4_before=n,
                         too_few_to_read=bool(n < THIN), rule=f"fewer than {THIN} places with any 2-4 unit permits in the before window"))
    pd.DataFrame(rows).to_csv(out("counts"), index=False)
    print(pd.DataFrame(rows).to_string(index=False))
    pd.DataFrame(mde_rows()).round(6).to_csv(out("mde"), index=False)
    print(pd.read_csv(out("mde")).to_string(index=False))


def mde_rows() -> list[dict]:
    F = flags()
    lp = np.log10(F["pop2010"].values)
    big = (F["pop2010"] >= c56.SPLIT).values
    out = []
    for o in c56.OUTCOMES:
        if not (work(o) / "parking_placebo_full_places.csv").exists():
            continue
        cols, E, W, check = standin_draws(o)
        r = real_frame(o, ["homes", "n_post"])
        w = (r["homes"] * r["n_post"]).values.astype(float)
        for wt, ww, eq in (("main weights", w, False), ("equal weight", np.ones(74), True)):
            for stat, v in (("overall effect", set_avgs(cols, E, W, eq)), ("size slope", set_slopes(cols, E, lp, ww)),
                            ("25,000 gap", set_gaps(cols, E, big, ww))):
                sd = float(np.std(v, ddof=1))
                out.append(dict(outcome=o, statistic=stat, weighting=wt, standin_sd=sd, mde=Z_MDE * sd,
                                placebo_half_width=float((np.percentile(v, 95) - np.percentile(v, 5)) / 2),
                                draw_rebuild_max_diff=check,
                                unit="homes per 1,000 existing homes a year" + (" per 10x population" if stat == "size slope" else "")))
    return out


# ------------------------------------------------------------------ step 2: every cell --------------------------------
class Ctx:
    def __init__(self):
        import run_parking_method2 as m
        m.SUF, m.CORRECTED = "_corrected", True
        self.m = m
        self.D = m.Data()
        self.F = flags()
        self.lp = np.log10(self.F["pop2010"].values)
        self.big = (self.F["pop2010"] >= c56.SPLIT).values
        self.wi = m.target_cells(self.D, "55")
        self.has = any_before()

    def ev(self, o) -> pd.DataFrame:
        r = real_frame(o, ["homes", "n_post", "population"])
        ev = pd.DataFrame({"homes": r["homes"].values, "n_post": r["n_post"].values, "band": self.m.band_of(r["population"].fillna(0)),
                           "metro": [self.D.metro.get(k, 0.0) for k in self.F["key"]]})
        ev["base"] = ev["homes"] * ev["n_post"]
        ev["v"] = 1.0  # random-effects weights are not used in Test 56
        return ev


def place_effects(o: str):
    r = real_frame(o, ["effect", "weight", "place"])
    bp = pd.read_csv(work(o) / "parking_method2_corrected_places.csv")
    bp = bp[bp["variant"] == "method 2, D"].reset_index(drop=True)
    assert (bp["place"].values == r["place"].values).all(), "method-2 rows out of order"
    return r["effect"].values.astype(float), r["weight"].values.astype(float), bp["effect"].values.astype(float)


def wslope(y, x, w):
    ok = np.isfinite(y) & np.isfinite(x) & (w > 0)
    y, x, w = y[ok], x[ok], w[ok]
    xm = np.average(x, weights=w)
    return float(np.sum(w * (x - xm) * (y - np.average(y, weights=w))) / np.sum(w * (x - xm) ** 2))


def wins_finite(m, y):
    y = y.copy()
    f = np.isfinite(y)
    y[f] = m.winsor(y[f])
    return y


def slope_cell(C, y, w, wins, sel):
    """Test 53's slope and bootstrap on the places in sel."""
    m = C.m
    y, x, w = y[sel], C.lp[sel], w[sel]
    a = wslope(wins_finite(m, y) if wins else y, x, w)
    rng = np.random.default_rng(SEED)
    b = []
    for _ in range(DRAWS):
        i = rng.integers(0, len(y), len(y))
        yi = wins_finite(m, y[i]) if wins else y[i]
        try:
            b.append(wslope(yi, x[i], w[i]))
        except ZeroDivisionError:
            pass
    lo, hi = np.nanpercentile(b, [5, 95])
    return a, float(lo), float(hi)


def group_avg_fn(C, meth, eq, y, ev):
    m = C.m
    if meth == "D":
        kind = "equal" if eq else MIX
        return lambda i: m.weighted_avg(kind, y[i], ev.iloc[i].reset_index(drop=True), C.wi)
    if eq:
        return lambda i: float(np.mean(m.winsor(y[i])))
    return lambda i: float(np.average(y[i], weights=ev["base"].values[i]))


def gap_cell(C, meth, eq, y, ev):
    out = {}
    for g, sel in (("big", C.big), ("small", ~C.big)):
        idx = np.flatnonzero(sel & np.isfinite(y))
        yy, ee = y[idx], ev.iloc[idx].reset_index(drop=True)
        fn = group_avg_fn(C, meth, eq, yy, ee)
        a = fn(np.arange(len(yy)))
        rng = np.random.default_rng(SEED)
        b = np.array([fn(rng.integers(0, len(yy), len(yy))) for _ in range(DRAWS)])
        out[g] = (a, b)
    d = out["big"][1] - out["small"][1]
    lo, hi = np.nanpercentile(d, [5, 95])
    return out["big"][0] - out["small"][0], float(lo), float(hi)


def overall_main(C, o, y, w, sel, eq, draws):
    cols, E, W, _ = draws
    mask = sel[cols]
    if eq:
        a = float(np.mean(y[sel]))
    elif sel.all():
        s = pd.read_csv(work(o) / "parking_placebo_full_summary.csv").iloc[0]
        return float(s["real_average"]), float(s["range_from_placebo_low"]), float(s["range_from_placebo_high"])
    else:
        a = float(np.average(y[sel], weights=w[sel]))
    v = set_avgs(cols, E, W, eq, mask)
    p05, p50, p95 = np.percentile(v, [5, 50, 95])
    return a, float(a + p05 - p50), float(a + p95 - p50)


def overall_d(C, o, yD, ev, sel, eq):
    m = C.m
    kind = "equal" if eq else MIX
    if sel.all():
        r = pd.read_csv(work(o) / "parking_method2_corrected_results.csv")
        r = r[(r["variant"] == "method 2, D") & (r["weights"] == kind)].iloc[0]
        return float(r["average"]), float(r["p05"]), float(r["p95"])
    ok = sel & np.isfinite(yD)
    e = ev[ok].reset_index(drop=True)
    a = m.weighted_avg(kind, yD[ok], e, C.wi)
    lo, hi = m.boot_range(kind, yD[ok], e, C.wi, m.BOOT, m.SEED)
    return a, lo, hi


def all_cells() -> None:
    C = Ctx()
    m = C.m
    mde = pd.DataFrame(mde_rows())
    cells, places = [], {}
    all74 = np.ones(74, bool)

    def add(cid, group, outcome, method, weighting, stat, est, lo, hi, sample="all 74 places", sel=all74, headline=False, **kw):
        n_any = int(C.has[sel].sum())
        n_big, n_small = int(C.has[sel & C.big].sum()), int(C.has[sel & ~C.big].sum())
        thin = n_any < THIN
        if stat in ("size slope", "25,000 gap"):  # lock: "overall or in a size group"
            thin = thin or n_big < THIN or n_small < THIN
        mm = mde[(mde["outcome"] == (outcome if outcome in c56.OUTCOMES else "units_2_4")) &
                 (mde["statistic"] == {"25,000 gap": "25,000 gap", "size slope": "size slope"}.get(stat, "overall effect")) &
                 (mde["weighting"] == ("equal weight" if weighting == "equal" else "main weights"))]
        cells.append(dict(cell=cid, headline=headline, group=group, outcome=OUT_LABEL.get(outcome, outcome), method=method,
                          weighting=weighting, statistic=stat, sample=sample, estimate=est, p05=lo, p95=hi,
                          excludes_0=bool(np.isfinite(lo) and np.isfinite(hi) and (lo > 0 or hi < 0)),
                          places_with_any_2_4_before=n_any, places_with_any_2_4_before_25000_plus=n_big,
                          places_with_any_2_4_before_under_25000=n_small, too_few_to_read=bool(thin),
                          reading_label="too few to read" if thin else "",
                          mde_main_placebo=float(mm["mde"].iloc[0]) if len(mm) and stat in ("overall effect", "size slope", "25,000 gap") else np.nan,
                          **kw))

    wname = {("main", False): "homes x after-years", ("main", True): "equal", ("D", False): "target-state mix", ("D", True): "equal"}
    # outcomes x (effect, slope, gap) x method x weighting
    n = 0
    for o in ("units_2_4", "1unit_units", "5plus_units"):
        yM, wM, yD = place_effects(o)
        ev = C.ev(o)
        draws = standin_draws(o)
        wD_mix, _ = m.mix_weights(ev, C.wi)
        places[o] = (yM, yD)
        for meth in ("main", "D"):
            for eq in (False, True):
                hl = o == "units_2_4" and not eq
                if meth == "main":
                    a = overall_main(C, o, yM, wM, all74, eq, draws)
                    s = slope_cell(C, yM, np.ones(74) if eq else wM, eq, all74)
                    g = gap_cell(C, "main", eq, yM, ev)
                else:
                    a = overall_d(C, o, yD, ev, all74, eq)
                    s = slope_cell(C, yD, np.ones(74) if eq else wD_mix, True, all74)
                    g = gap_cell(C, "D", eq, yD, ev)
                for stat, (est, lo, hi) in (("overall effect", a), ("size slope", s), ("25,000 gap", g)):
                    is_h = hl and stat != "25,000 gap"
                    n += 1
                    add(f"H{n}" if is_h else f"S{n}", "headline" if is_h else "outcome x statistic x method x weighting",
                        o, meth, wname[(meth, eq)], stat, est, lo, hi, headline=is_h)
    # reported-only: 2-4 effect and slope x 2 methods (main weights)
    o = "units_2_4_rep"
    yM, wM, yD = place_effects(o)
    ev = C.ev(o)
    draws = standin_draws(o)
    wD_mix, _ = m.mix_weights(ev, C.wi)
    places[o] = (yM, yD)
    for meth in ("main", "D"):
        a = overall_main(C, o, yM, wM, all74, False, draws) if meth == "main" else overall_d(C, o, yD, ev, all74, False)
        s = slope_cell(C, yM, wM, False, all74) if meth == "main" else slope_cell(C, yD, wD_mix, True, all74)
        for stat, (est, lo, hi) in (("overall effect", a), ("size slope", s)):
            add(f"R-{meth}-{stat}", "reported-only columns", o, meth, wname[(meth, False)], stat, est, lo, hi)
    # flag/drop and no-Oregon: 2-4 effect and slope x 2 methods x 2 variants
    o = "units_2_4"
    yM, wM, yD = place_effects(o)
    ev = C.ev(o)
    draws = standin_draws(o)
    for vname, sel in (("without flagged places", ~C.F["flag_plex"].values), ("without Oregon", ~C.F["oregon"].values)):
        evs = ev[sel].reset_index(drop=True)
        wmix_s, _ = m.mix_weights(evs, C.wi)
        wD_sub = np.zeros(74)
        wD_sub[sel] = wmix_s
        for meth in ("main", "D"):
            a = overall_main(C, o, yM, wM, sel, False, draws) if meth == "main" else overall_d(C, o, yD, ev, sel, False)
            s = slope_cell(C, yM, wM, False, sel) if meth == "main" else slope_cell(C, yD, wD_sub, True, sel)
            for stat, (est, lo, hi) in (("overall effect", a), ("size slope", s)):
                add(f"F-{vname}-{meth}-{stat}", "flag/drop and no-Oregon", o, meth, wname[(meth, False)], stat, est, lo, hi,
                    sample=vname, sel=sel)
    # Poisson, long set, event study, placebo dates, spillover, date-aware (units_2_4 extras)
    W = work("units_2_4")
    P = pd.read_csv(W / "parking_t56_poisson.csv")
    for r in P.itertuples():
        add(f"P-{r.method}", f"Poisson count check ({POISSON_DESIGN})", o, r.method, "counts (Poisson)", "log rate ratio (theta)", r.theta, r.theta_p05,
            r.theta_p95, design=POISSON_DESIGN, multiplicative_effect=r.multiplicative_effect, mult_p05=r.mult_p05, mult_p95=r.mult_p95, places_used=r.stacks_used)
    L = pd.read_csv(W / "parking_t56_long_set.csv")
    for r in L.itertuples():
        add(f"L-{r.method}", "long set", o, r.method, r.weights, "long-set effect (after-years 1-5)", r.estimate, r.p05, r.p95,
            places_used=r.places)
    ES = pd.read_csv(W / "parking_t56_event_study.csv")
    for r in ES.itertuples():
        add(f"E-{r.method}-{r.year:+d}", "event study (reference year -1)", o, r.method, r.weights, f"year {r.year:+d}",
            r.estimate, r.p05, r.p95, places_used=r.places)
    for shift in (2, 4):
        S = pd.read_csv(W / f"t56_placebo_shift{shift}" / f"parking_t56_placebo_shift{shift}_summary.csv")
        r = S[S["estimator"] == "main (real average, placebo spread)"].iloc[0]
        add(f"PD-main-{shift}", "placebo date", o, "main", "homes x after-years", f"repeal moved {shift} years early",
            r["estimate"], r["p05"], r["p95"], places_used=r["places"])
        r = S[(S["estimator"] == f"method 2, D (repeals moved {shift} years early)") & (S["weights"] == MIX)].iloc[0]
        add(f"PD-D-{shift}", "placebo date", o, "D", MIX, f"repeal moved {shift} years early", r["estimate"], r["p05"], r["p95"],
            places_used=r["places"])
    G = pd.read_csv(W / "t56_pool_rules" / "parking_t52_g_summary.csv")
    r = G[G["variant"] == "g_outmetro"].iloc[0]
    add("SP-D", "spillover (out-of-metro pools)", o, "D", MIX, "overall effect", r["estimate"], r["p05"], r["p95"],
        shift_from_base=r["shift"], shift_p05=r["shift_p05"], shift_p95=r["shift_p95"])
    H = pd.read_csv(W / "t56_pool_rules" / "parking_t52_h_summary.csv")
    r = H[H["variant"] == "h1_dated"].iloc[0]
    add("DA-D", "date-aware pools (52h.1)", o, "D", MIX, "overall effect", r["estimate"], r["p05"], r["p95"],
        shift_from_base=r["shift"], shift_p05=r["shift_p05"], shift_p95=r["shift_p95"])

    Cdf = pd.DataFrame(cells)
    assert len(Cdf) == 74 and int(Cdf["headline"].sum()) == 4, (len(Cdf), int(Cdf["headline"].sum()))
    Cdf["unit"] = ["log of the rate ratio" if "theta" in st else "homes permitted per 1,000 existing homes a year" +
                   (" per 10x population (2010)" if st == "size slope" else "") for st in Cdf["statistic"]]
    Cdf.round(6).to_csv(out("cells"), index=False)
    # per-place effects and the regression-to-the-mean report (main: place vs its pool before the repeal)
    PL = C.F[["i", "place", "state", "event_year", "pop2010", "size_group", "oregon", "flag_plex"]].copy()
    PL["any_2_4_before"] = C.has
    for o, (yM, yD) in places.items():
        PL[f"main_{o}"], PL[f"D_{o}"] = yM, yD
    PL.round(6).to_csv(out("places"), index=False)
    rt = real_frame("units_2_4", ["place", "rate_before", "ctrl_before"])
    rt["place_minus_pool_before"] = rt["rate_before"] - rt["ctrl_before"]
    rt[["place", "rate_before", "ctrl_before", "place_minus_pool_before"]].round(6).to_csv(out("rtm"), index=False)
    reading(Cdf)
    pd.set_option("display.width", 250)
    print(Cdf[["cell", "group", "outcome", "method", "weighting", "statistic", "sample", "estimate", "p05", "p95",
               "excludes_0", "too_few_to_read", "mde_main_placebo"]].round(3).to_string(index=False))


def reading(Cdf: pd.DataFrame) -> None:
    """The lock's reading rules, applied mechanically to the cells (the write-up states them in words)."""
    def cell(**kw):
        q = Cdf
        for k, v in kw.items():
            q = q[q[k] == v]
        assert len(q) == 1, kw
        return q.iloc[0]
    sign = lambda r: 0 if not r["excludes_0"] else (1 if r["p05"] > 0 else -1)  # noqa: E731
    o = OUT_LABEL["units_2_4"]
    # group= keeps the spillover and date-aware D cells (also D, target-state mix, overall effect) out of the match
    H, G = "headline", "outcome x statistic x method x weighting"
    hm, hd = cell(group=H, outcome=o, method="main", weighting="homes x after-years", statistic="overall effect", sample="all 74 places"), \
        cell(group=H, outcome=o, method="D", weighting=MIX, statistic="overall effect", sample="all 74 places")
    sm, sd = cell(group=H, outcome=o, method="main", weighting="homes x after-years", statistic="size slope", sample="all 74 places"), \
        cell(group=H, outcome=o, method="D", weighting=MIX, statistic="size slope", sample="all 74 places")
    gm, gd = cell(group=G, outcome=o, method="main", weighting="homes x after-years", statistic="25,000 gap"), \
        cell(group=G, outcome=o, method="D", weighting=MIX, statistic="25,000 gap")
    eff_counts = sign(hm) != 0 and sign(hm) == sign(hd)
    gap_agrees = all(g["estimate"] != 0 and np.sign(g["estimate"]) == np.sign(s["estimate"]) for g, s in ((gm, sm), (gd, sd)))
    slope_counts = sign(sm) != 0 and sign(sm) == sign(sd) and gap_agrees
    lead = [k for k in (-5, -4, -3, -2) if cell(group="event study (reference year -1)", method="main", statistic=f"year {k:+d}")["excludes_0"]
            and cell(group="event study (reference year -1)", method="D", statistic=f"year {k:+d}")["excludes_0"]]
    pdates = [s for s in (2, 4) if cell(cell=f"PD-main-{s}")["excludes_0"] and cell(cell=f"PD-D-{s}")["excludes_0"]]
    pretrend = bool(lead or pdates)
    scale = {}
    for meth, lev in (("main", hm), ("D", hd)):
        p = cell(cell=f"P-{meth}")
        if not lev["excludes_0"] and p["excludes_0"]:
            scale[meth] = "don't know (levels include 0, Poisson excludes 0)"
        elif lev["excludes_0"] and p["excludes_0"] and sign(lev) != sign(p):
            scale[meth] = "scale-dependent"
        else:
            scale[meth] = "no scale flag"
    too_few = bool(hm["too_few_to_read"])
    thin_lab = lambda *rs: "too few to read" if any(bool(r["too_few_to_read"]) for r in rs) else ""  # noqa: E731
    n_groups = f"25,000+: {int(sm['places_with_any_2_4_before_25000_plus'])}; under 25,000: {int(sm['places_with_any_2_4_before_under_25000'])}"
    rows = [
        dict(rule="overall 2-4 effect counts (both headline ranges exclude 0, same sign)", result=bool(eff_counts),
             too_few_to_read=thin_lab(hm, hd)),
        dict(rule="size slope counts (both slope ranges exclude 0, same sign, and both 25,000 gaps agree in sign)", result=bool(slope_counts),
             too_few_to_read=thin_lab(sm, sd, gm, gd), detail=f"places with any 2-4 permits before, {n_groups}"),
        dict(rule="25,000 gap agrees in sign with the slope (main gap vs main slope, D gap vs D slope)", result=bool(gap_agrees),
             too_few_to_read=thin_lab(gm, gd)),
        dict(rule="pre-trend label (a lead -5..-2 or a placebo date excludes 0 under both methods)", result=pretrend,
             detail=f"leads {lead}; placebo dates {pdates}"),
        dict(rule="scale rule, main", result=scale["main"]), dict(rule="scale rule, D", result=scale["D"]),
        dict(rule=f"too few to read overall (fewer than {THIN} of the 74 places with any 2-4 permits before)", result=too_few,
             detail=f"{int(hm['places_with_any_2_4_before'])} places"),
        dict(rule=f"too few to read in a size group (fewer than {THIN} places with any 2-4 permits before in 25,000+ or under 25,000)",
             result=bool(min(int(sm["places_with_any_2_4_before_25000_plus"]), int(sm["places_with_any_2_4_before_under_25000"])) < THIN),
             detail=n_groups),
        dict(rule="headline cells excluding 0 (of 4; one by chance is plausible)", result=int(Cdf[Cdf["headline"]]["excludes_0"].sum())),
    ]
    pd.DataFrame(rows).to_csv(out("reading"), index=False)
    print(pd.DataFrame(rows).to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--first", action="store_true", help="before-window counts and MDE only (no repeal-place effect)")
    g.add_argument("--all", action="store_true", help="every cell")
    ap.add_argument("--dryrun", action="store_true", help="read the all-homes dry run; write to data/processed/t56/dryrun_allhomes_summary/")
    a = ap.parse_args()
    if a.dryrun:
        global OUT, SUFFIX, DRYRUN
        DRYRUN, SUFFIX = True, "_dryrun_allhomes"
        OUT = T56 / "dryrun_allhomes_summary"
        OUT.mkdir(parents=True, exist_ok=True)
        for k in OUT_LABEL:
            OUT_LABEL[k] = f"all homes (dry run, in the {k} slot)"
    first() if a.first else all_cells()


if __name__ == "__main__":
    main()
