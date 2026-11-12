"""Test 58 (post hoc; CAUSAL_FRAMEWORK_PLAN.md "Test 58"): 1-4 unit homes, read from the units_1_4 run.

    uv run python scripts/summarise_parking_t58.py --first   # places with any 1-4 permits before, and MDE (no effect)
    uv run python scripts/summarise_parking_t58.py --all     # the 30 cells and the reading

Input: data/processed/t56/units_1_4_ref/ (scripts/run_parking_t56.sh units_1_4 extras). Reuses Test 56's audited
summary functions (scripts/summarise_parking_t56.py) unchanged; only the outcome and the output names differ.
Outputs: reference/parking_t58_{counts,mde,cells,reading}.csv.

Cells (30):
- read (8): overall effect main and D; size slope main and D (descriptive only, no reading rule);
  placebo dates (repeal moved 2 and 4 years early) main and D.
- read for the pre-trend label (16): event-study years -5..-2 and 0..+3 (reference -1), main and D.
- shown only (6): Poisson check main and D, long set main and D, spillover pools D, date-aware pools D.
Reading: the overall effect counts only if both ranges exclude 0 with the same sign. The pre-trend label is on if any
lead (-5..-2) or placebo date excludes 0 under both methods (Test 56's rule).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.pop("MM_BPS_OUTCOME", None)

import summarise_parking_t56 as s  # noqa: E402

O = "units_1_4"
s.OUT_LABEL[O] = "1-4 unit homes"
s.c56.OUTCOMES = (O,)  # mde_rows() loops over this
s.out = lambda name: s.REF / f"parking_t58_{name}.csv"  # noqa: E731
MIX = s.MIX
WI = 13343.385


def first() -> None:
    F = s.flags()
    big = (F["pop2010"] >= s.c56.SPLIT).values
    has = s.any_before(O)
    rows = [dict(sample=lab, places=int(sel.sum()), places_with_any_1_4_before=int(has[sel].sum()),
                 too_few_to_read=bool(int(has[sel].sum()) < s.THIN))
            for lab, sel in (("all 74 places", np.ones(74, bool)), ("under 25,000", ~big), ("25,000 or more", big))]
    pd.DataFrame(rows).to_csv(s.out("counts"), index=False)
    print(pd.DataFrame(rows).to_string(index=False))
    m = pd.DataFrame(s.mde_rows())
    m = m[m["weighting"] == "main weights"]
    m["mde_wisconsin_homes_5yr"] = m["mde"] * WI
    m.round(6).to_csv(s.out("mde"), index=False)
    print(m.round(3).to_string(index=False))


def all_cells() -> None:
    C = s.Ctx()
    C.has = s.any_before(O)
    m = C.m
    cells = []

    def add(cid, group, method, weighting, stat, est, lo, hi, read, **kw):
        cells.append(dict(cell=cid, group=group, outcome="1-4 unit homes (post hoc)", method=method, weighting=weighting,
                          statistic=stat, estimate=est, p05=lo, p95=hi,
                          excludes_0=bool(np.isfinite(lo) and np.isfinite(hi) and (lo > 0 or hi < 0)), use=read, **kw))

    yM, wM, yD = s.place_effects(O)
    ev = C.ev(O)
    draws = s.standin_draws(O)
    wD_mix, _ = m.mix_weights(ev, C.wi)
    all74 = np.ones(74, bool)
    for meth in ("main", "D"):
        a = s.overall_main(C, O, yM, wM, all74, False, draws) if meth == "main" else s.overall_d(C, O, yD, ev, all74, False)
        sl = s.slope_cell(C, yM, wM, False, all74) if meth == "main" else s.slope_cell(C, yD, wD_mix, True, all74)
        wname = "homes x after-years" if meth == "main" else MIX
        add(f"O-{meth}", "overall effect", meth, wname, "overall effect", *a, "read")
        add(f"S-{meth}", "size slope", meth, wname, "size slope (per 10x population)", *sl, "descriptive only")
    W = s.work(O)
    for shift in (2, 4):
        S = pd.read_csv(W / f"t56_placebo_shift{shift}" / f"parking_t56_placebo_shift{shift}_summary.csv")
        r = S[S["estimator"] == "main (real average, placebo spread)"].iloc[0]
        add(f"PD-main-{shift}", "placebo date", "main", "homes x after-years", f"repeal moved {shift} years early",
            r["estimate"], r["p05"], r["p95"], "read (pre-trend label)", places_used=r["places"])
        r = S[(S["estimator"] == f"method 2, D (repeals moved {shift} years early)") & (S["weights"] == MIX)].iloc[0]
        add(f"PD-D-{shift}", "placebo date", "D", MIX, f"repeal moved {shift} years early", r["estimate"], r["p05"], r["p95"],
            "read (pre-trend label)", places_used=r["places"])
    ES = pd.read_csv(W / "parking_t56_event_study.csv")
    for r in ES.itertuples():
        add(f"E-{r.method}-{r.year:+d}", "event study (reference year -1)", r.method, r.weights, f"year {r.year:+d}",
            r.estimate, r.p05, r.p95, "read (pre-trend label)" if r.year <= -2 else "shown only", places_used=r.places)
    P = pd.read_csv(W / "parking_t56_poisson.csv")
    for r in P.itertuples():
        add(f"P-{r.method}", f"Poisson count check ({s.POISSON_DESIGN})", r.method, "counts (Poisson)", "log rate ratio (theta)",
            r.theta, r.theta_p05, r.theta_p95, "shown only", multiplicative_effect=r.multiplicative_effect, mult_p05=r.mult_p05,
            mult_p95=r.mult_p95, places_used=r.stacks_used, status=getattr(r, "status", ""))
    L = pd.read_csv(W / "parking_t56_long_set.csv")
    for r in L.itertuples():
        add(f"L-{r.method}", "long set", r.method, r.weights, "long-set effect (after-years 1-5)", r.estimate, r.p05, r.p95,
            "shown only", places_used=r.places)
    G = pd.read_csv(W / "t56_pool_rules" / "parking_t52_g_summary.csv")
    r = G[G["variant"] == "g_outmetro"].iloc[0]
    add("SP-D", "spillover (out-of-metro pools)", "D", MIX, "overall effect", r["estimate"], r["p05"], r["p95"], "shown only")
    H = pd.read_csv(W / "t56_pool_rules" / "parking_t52_h_summary.csv")
    r = H[H["variant"] == "h1_dated"].iloc[0]
    add("DA-D", "date-aware pools (52h.1)", "D", MIX, "overall effect", r["estimate"], r["p05"], r["p95"], "shown only")

    Cdf = pd.DataFrame(cells)
    assert len(Cdf) == 30, len(Cdf)
    for c in ("estimate", "p05", "p95"):
        Cdf[f"{c}_wisconsin_homes_5yr"] = np.where(Cdf["group"].isin(["overall effect", "placebo date", "long set",
                                                                      "spillover (out-of-metro pools)", "date-aware pools (52h.1)"]),
                                                   Cdf[c] * WI, np.nan)
    Cdf.round(6).to_csv(s.out("cells"), index=False)

    def cell(cid):
        q = Cdf[Cdf["cell"] == cid]
        assert len(q) == 1, cid
        return q.iloc[0]
    sign = lambda r: 0 if not r["excludes_0"] else (1 if r["p05"] > 0 else -1)  # noqa: E731
    om, od = cell("O-main"), cell("O-D")
    lead = [k for k in (-5, -4, -3, -2) if cell(f"E-main-{k:+d}")["excludes_0"] and cell(f"E-D-{k:+d}")["excludes_0"]]
    pdates = [k for k in (2, 4) if cell(f"PD-main-{k}")["excludes_0"] and cell(f"PD-D-{k}")["excludes_0"]]
    rows = [dict(rule="overall 1-4 effect counts (both ranges exclude 0, same sign)", result=bool(sign(om) != 0 and sign(om) == sign(od))),
            dict(rule="pre-trend label (a lead -5..-2 or a placebo date excludes 0 under both methods)", result=bool(lead or pdates),
                 detail=f"leads {lead}; placebo dates {pdates}"),
            dict(rule="size slope", result="descriptive only (no reading rule)"),
            dict(rule="label", result="post hoc: planned after the 1-unit and 2-4 results were seen")]
    pd.DataFrame(rows).to_csv(s.out("reading"), index=False)
    pd.set_option("display.width", 250)
    print(Cdf[["cell", "method", "statistic", "estimate", "p05", "p95", "excludes_0", "use"]].round(3).to_string(index=False))
    print(pd.DataFrame(rows).to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--first", action="store_true")
    g.add_argument("--all", action="store_true")
    a = ap.parse_args()
    first() if a.first else all_cells()


if __name__ == "__main__":
    main()
