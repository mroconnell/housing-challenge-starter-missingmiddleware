"""Test 56 (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Test 56: one reading at lock"): the 2-4 unit checks that need more
than the batch pipeline. Run by scripts/run_parking_t56.sh on an outcome's working copy (MM_REFERENCE_DIR,
MM_BPS_OUTCOME set) after that copy's pipeline has run. Existing scripts are imported, never edited.

    uv run --all-extras python scripts/run_parking_t56_extras.py [--parts event,long,poisson,placebo_dates,pools]

Parts (each writes into MM_REFERENCE_DIR):
- event   Event study, years -5..+3 around the repeal year, reference year -1 (new code).
          main: the batch's recorded comparison pool and existing homes for each place (run_parking_t45_t46.collect),
                yearly rate gap (place minus pool) minus the year -1 gap; pool members missing a year are left out of
                that year (as comparison.event_path). Years are limited to the place's own before and after windows
                plus year 0 (a rescued place with trimmed windows gets no year 0). Weights: existing homes.
          D:    one fixed D pool per place over its 10-year before window, year 0 and its after-years (Test 49 rule),
                winsorised pool rate, pre-event homes; gap minus the year -1 gap; target-state mix (base = homes).
          Ranges: place bootstrap, 2,000 draws, seed 20261105 (places without a year drop out of that year's draw).
          -> parking_t56_event_places.csv, parking_t56_event_study.csv
- long    Long set (Test 49 style): places with 5+ after-years in the data (repeal year <= last year - 5; rescued
          places with trimmed windows left out). Place
          effect = mean over after-years 1..5 of the yearly gap minus the before-window gap. main: recorded pool and
          5-year before window, weights homes x 5; D: run_parking_t49_event_time.case_years (fixed long pool), mean
          of years 1..5, target-state mix (base = homes x 5). Same bootstrap. -> parking_t56_long_set.csv
- poisson Poisson count check (Tests 38-39 estimator run_parking_t3839.fit, alpha 0), labelled in its output as
          "stacked two-period per place (changed from Tests 38–39 panel)". One stack per repeal place:
          the place and its comparison pool (main: recorded pool, main windows, ACS homes; D: the batch D pool, D's
          windows, pre-event homes), permits summed over the before and after windows, exposure = homes x years.
          log(mean) = log(exposure) + group-in-stack effect + stack-after effect + theta x (place, after).
          Reported as theta and exp(theta) - 1 (the multiplicative effect); range from 2,000 stack resamples, seed
          20261105. Groups with no permits in either window are dropped (as Tests 38-39); a stack missing either
          group drops out. -> parking_t56_poisson.csv
- placebo_dates  run_parking_t52_placebos.py --variant timing4 with its SHIFT set to 2 and then 4 (repeal moved 2 or
          4 years early; main with its full stand-in spread, D with place bootstrap), outputs redirected to
          MM_REFERENCE_DIR/t56_placebo_shift{2,4}/ as parking_t56_placebo_shift{2,4}_{summary,places}.csv, with the D
          label set to "repeals moved 2 (or 4) years early" (the script itself always says 4).
- pools   run_parking_t52_pool_rules.py variants g_outmetro (52g spillover) and h1_dated (52h.1 date-aware pools),
          with its base check pointed at this working copy's D effects; outputs to MM_REFERENCE_DIR/t56_pool_rules/.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import parking_t56_common as c56  # noqa: E402
import run_parking_method2 as m  # noqa: E402
import run_parking_t45_t46 as t46  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

KS = (-5, -4, -3, -2, 0, 1, 2, 3)
REF_K = -1
LONG_K = 5
SEED, DRAWS = c56.SEED, c56.DRAWS
MIX = "target-state mix"
POISSON_DESIGN = "stacked two-period per place (changed from Tests 38–39 panel)"


# ------------------------------------------------------------------ data ----------------------------------------------
def load():
    m.SUF, m.CORRECTED = "_corrected", True
    c56.patch_method2(m)
    c56.patch_rebuild(t46)
    D = m.Data()
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].dropna(subset=["effect"]).reset_index(drop=True)
    assert len(real) == 74, len(real)
    with contextlib.redirect_stdout(io.StringIO()):
        R = t46.rebuild(real, t46.collect())
    assert R["found"].all()
    cases = []
    for i, x in R.iterrows():
        c = x["call"]
        cases.append(dict(i=i, key=c["key"], event_year=int(real.loc[i, "event_year"]), pre=tuple(c["pre"]), post=tuple(c["post"]),
                          scale=float(x["scale"]), pop=float(real.loc[i, "population"]) if pd.notna(real.loc[i, "population"]) else np.nan,
                          trimmed=real.loc[i, "source"] == "rescued" and not str(real.loc[i, "place"]).startswith("South Bend"),
                          homes=float(real.loc[i, "homes"]), n_post=int(real.loc[i, "n_post"]), state=real.loc[i, "state"],
                          place=real.loc[i, "place"], pool=list(c["pool"]), p=c["p"], call_homes=c["homes"]))
    ev = pd.DataFrame({"v": m.placebo_v(len(real)), "homes": real["homes"].values, "n_post": real["n_post"].values,
                       "band": m.band_of(real["population"].fillna(0)), "metro": [D.metro.get(c["key"], 0.0) for c in cases]})
    ev["base"] = ev["homes"] * ev["n_post"]
    wi = m.target_cells(D, "55")
    return D, real, cases, ev, wi


_complete_cache: dict = {}


def ok_year(p, y) -> set:
    k = (id(p), y)
    if k not in _complete_cache:
        _complete_cache[k] = cmp.complete(p, [y])
    return _complete_cache[k]


def main_rate(c, keys, y) -> float:
    ok = ok_year(c["p"], y)
    keys = [k for k in keys if k in ok]
    return cmp._rate(c["p"], keys, [y], "units_total", c["call_homes"]) if keys else np.nan


# ------------------------------------------------------------------ aggregation ---------------------------------------
def agg(kind: str, y: np.ndarray, ev: pd.DataFrame, wi) -> float:
    """main: weighted by ev['base'] (no winsorising, as the batch's main); D: method 2's target-state mix."""
    ok = np.isfinite(y)
    if ok.sum() == 0:
        return np.nan
    y, e = y[ok], ev[ok].reset_index(drop=True)
    if kind == "main":
        return float(np.average(y, weights=e["base"].values)) if e["base"].sum() > 0 else np.nan
    return m.weighted_avg(MIX, y, e, wi)


def boot(kind, y, ev, wi):
    rng = np.random.default_rng(SEED)
    n = len(y)
    out = []
    for _ in range(DRAWS):
        i = rng.integers(0, n, n)
        out.append(agg(kind, y[i], ev.iloc[i].reset_index(drop=True), wi))
    out = np.array(out, float)
    out = out[np.isfinite(out)]
    return (float(np.percentile(out, 5)), float(np.percentile(out, 95))) if len(out) else (np.nan, np.nan)


def summary_row(label, kind, y, ev, wi, **extra):
    a = agg(kind, y, ev, wi)
    lo, hi = boot(kind, y, ev, wi)
    return dict(check=label, method="main" if kind == "main" else "D", places=int(np.isfinite(y).sum()), estimate=a,
                p05=lo, p95=hi, excludes_0=bool(lo > 0 or hi < 0), **extra)


# ------------------------------------------------------------------ event study ---------------------------------------
def event_main(c) -> dict:
    ey = c["event_year"]
    allowed = set(c["pre"]) | set(c["post"]) | (set() if c["trimmed"] else {ey})
    if (ey + REF_K) not in allowed or c["key"] not in ok_year(c["p"], ey + REF_K) or not c["pool"]:
        return {k: np.nan for k in KS}
    gap = lambda y: main_rate(c, [c["key"]], y) - main_rate(c, c["pool"], y)  # noqa: E731
    ref = gap(ey + REF_K)
    out = {}
    for k in KS:
        y = ey + k
        out[k] = float((gap(y) - ref) / c["scale"]) if y in allowed and y <= cmp.LAST_YEAR and c["key"] in ok_year(c["p"], y) else np.nan
    return out


def event_d(D, c) -> dict:
    ey = c["event_year"]
    pl = m.long_pre(ey, list(c["pre"]), c["trimmed"])
    post = [y for y in c["post"]]
    yrs = sorted(set(pl) | set(post) | {ey})
    if not set(yrs) <= set(D.P.columns) or (ey + REF_K) not in pl:
        return {k: np.nan for k in KS}
    s = m.select_pool(D, c["key"], ey, pl, post + [ey], "A", m.OPT_MAIN)  # Test 49's fixed-pool rule
    if len(s["pool"]) < m.MIN_POOL:
        return {k: np.nan for k in KS}
    t = m.rates(D, [c["key"]], yrs, s["h"]).iloc[0]
    cp = m.pool_rate(D, s["pool"], yrs, s["h"], True)
    ref = t[ey + REF_K] - cp[ey + REF_K]
    return {k: float(((t[ey + k] - cp[ey + k]) - ref) / c["scale"]) if (ey + k) in yrs else np.nan for k in KS}


def part_event(D, cases, ev, wi):
    evh = ev.assign(base=ev["homes"])
    rows, places = [], []
    E = {"main": [event_main(c) for c in cases], "D": [event_d(D, c) for c in cases]}
    for meth, kind in (("main", "main"), ("D", "D")):
        for c, e in zip(cases, E[meth]):
            places.append(dict(method=meth, place=c["place"], state=c["state"], event_year=c["event_year"],
                               **{f"k{k}": e[k] for k in KS}))
        for k in KS:
            y = np.array([e[k] for e in E[meth]], float)
            rows.append(summary_row("event study", kind, y, evh, wi, year=k, reference_year=REF_K,
                                    weights="homes" if meth == "main" else "target-state mix (base = homes)"))
    pd.DataFrame(places).round(6).to_csv(REFERENCE / "parking_t56_event_places.csv", index=False)
    pd.DataFrame(rows).round(6).to_csv(REFERENCE / "parking_t56_event_study.csv", index=False)
    print(pd.DataFrame(rows).round(3).to_string(index=False), flush=True)


# ------------------------------------------------------------------ long set ------------------------------------------
def part_long(D, cases, ev, wi):
    import run_parking_t49_event_time as t49
    last = int(D.P.columns.max())
    # rescued places with trimmed windows have no unbroken run of after-years, so they are not in the long set
    idx = [j for j, c in enumerate(cases) if last - c["event_year"] >= LONG_K and not c["trimmed"]]
    t49.G.update(D=D, cases=cases)
    ym, yd = np.full(len(cases), np.nan), np.full(len(cases), np.nan)
    for j in idx:
        c = cases[j]
        ey = c["event_year"]
        post = [ey + k for k in range(1, LONG_K + 1)]
        if c["pool"] and all(c["key"] in ok_year(c["p"], y) for y in post):
            before = cmp._rate(c["p"], [c["key"]], list(c["pre"]), "units_total", c["call_homes"]) - \
                cmp._rate(c["p"], c["pool"], list(c["pre"]), "units_total", c["call_homes"])
            gaps = [main_rate(c, [c["key"]], y) - main_rate(c, c["pool"], y) for y in post]
            ym[j] = float((np.mean(gaps) - before) / c["scale"])
        r = t49.case_years(c, LONG_K)
        if r["effects"] is not None:
            yd[j] = float(np.mean([r["effects"][k] for k in range(1, LONG_K + 1)]))
    sel = np.zeros(len(cases), bool)
    sel[idx] = True
    e5 = ev.assign(n_post=LONG_K, base=ev["homes"] * LONG_K)
    rows = []
    for meth, y in (("main", ym), ("D", yd)):
        yy = np.where(sel, y, np.nan)
        rows.append(summary_row(f"long set (after-years 1-{LONG_K})", meth if meth == "main" else "D", yy, e5, wi,
                                places_in_set=int(sel.sum()),
                                weights="homes x 5" if meth == "main" else "target-state mix (base = homes x 5)"))
    pd.DataFrame(rows).round(6).to_csv(REFERENCE / "parking_t56_long_set.csv", index=False)
    pd.DataFrame(dict(place=[c["place"] for c in cases], in_long_set=sel, main=ym, D=yd)).round(6) \
        .to_csv(REFERENCE / "parking_t56_long_set_places.csv", index=False)
    print(pd.DataFrame(rows).round(3).to_string(index=False), flush=True)


# ------------------------------------------------------------------ Poisson -------------------------------------------
def stack_cells_main(c):
    p, h = c["p"], c["call_homes"]
    cells = []
    for grp, keys in (("place", [c["key"]]), ("pool", c["pool"])):
        for per, yrs in (("before", list(c["pre"])), ("after", list(c["post"]))):
            s = p[p["key"].isin(keys) & p["year"].isin(yrs)]["units_total"].sum()
            cells.append(dict(group=grp, period=per, count=float(s), exposure=float(h.reindex(keys).sum()) * len(yrs) / 1000))
    return cells


def stack_cells_d(D, c, pool):
    ey = c["event_year"]
    pl = m.long_pre(ey, list(c["pre"]), c["trimmed"])
    h = D.homes_pre(ey, False)
    cells = []
    for grp, keys in (("place", [c["key"]]), ("pool", list(pool))):
        for per, yrs in (("before", pl), ("after", list(c["post"]))):
            cells.append(dict(group=grp, period=per, count=float(D.P.loc[keys, yrs].sum().sum()),
                              exposure=float(h.reindex(keys).sum()) * len(yrs) / 1000))
    return cells


def poisson_theta(stacks: list[list[dict]]):
    import run_parking_t3839 as t3839
    rows = []
    for s, cells in enumerate(stacks):
        if not cells:
            continue
        # A stack with any zero cell (place or pool, before or after) has no finite Poisson estimate (separation),
        # so it is left out; the number of stacks used is reported beside the result (audit note, 2026-11-12).
        if min(x["count"] for x in cells) <= 0:
            continue
        for x in cells:
            rows.append(dict(stack=s, unit=f"{s}|{x['group']}", after=float(x["period"] == "after"),
                             treat=float(x["group"] == "place" and x["period"] == "after"), y=x["count"], off=np.log(x["exposure"])))
    d = pd.DataFrame(rows)
    if d.empty:
        return np.nan, 0
    stacks_used = sorted(d["stack"].unique())
    X = np.column_stack([((d["stack"] == s) & (d["after"] == 1)).values.astype(float) for s in stacks_used] + [d["treat"].values])
    unit, _ = pd.factorize(d["unit"])
    try:
        b, _, _ = t3839.fit(d["y"].values, d["off"].values, unit, X, 0.0)
    except np.linalg.LinAlgError:  # a bootstrap draw that does not converge counts as unused (draws_used is reported)
        return np.nan, len(stacks_used)
    return float(b[-1]), len(stacks_used)


def part_poisson(D, cases):
    out = []
    base = {"main": [stack_cells_main(c) if c["pool"] else [] for c in cases], "D": []}
    for c in cases:
        r = m.case_effect(D, c, "D", m.OPT_MAIN)
        base["D"].append(stack_cells_d(D, c, r["pool"]) if r.get("pool") and len(r["pool"]) >= m.MIN_POOL else [])
    for meth, stacks in base.items():
        th, n = poisson_theta(stacks)
        rng = np.random.default_rng(SEED)
        bt = []
        for _ in range(DRAWS):
            i = rng.integers(0, len(stacks), len(stacks))
            bt.append(poisson_theta([stacks[j] for j in i])[0])
        bt = np.array(bt, float)
        bt = bt[np.isfinite(bt)]
        lo, hi = np.percentile(bt, [5, 95])
        out.append(dict(check="Poisson count model", design=POISSON_DESIGN, method=meth, stacks_used=n, stacks=len(stacks), theta=th, theta_p05=lo,
                        theta_p95=hi, multiplicative_effect=np.expm1(th), mult_p05=np.expm1(lo), mult_p95=np.expm1(hi),
                        excludes_0=bool(lo > 0 or hi < 0), draws_used=len(bt)))
    pd.DataFrame(out).round(6).to_csv(REFERENCE / "parking_t56_poisson.csv", index=False)
    print(pd.DataFrame(out).round(3).to_string(index=False), flush=True)


# ------------------------------------------------------------------ placebo dates and pool rules ----------------------
def part_placebo_dates():
    import run_parking_t52_placebos as pl
    c56.patch_rebuild(pl.t46)
    for shift in (2, 4):
        pl.cmp.complete = pl._orig_complete  # fresh cache per run (panel ids from an earlier run could be reused)
        pl._cache.clear()
        pl.SHIFT = shift
        pl.OUT = REFERENCE / f"t56_placebo_shift{shift}"
        pl.PROC = pl.OUT / "standins"
        pl.OUT.mkdir(parents=True, exist_ok=True)
        # run_parking_t52_placebos.py hard-codes "moved 4 years early" in its D label and "timing4" in its file names;
        # relabel for this shift (its own behaviour for other tests is unchanged: nothing is patched outside this call)
        orig_ds = pl.d_summary

        def d_summary(D, y, ev, wi, label, seeds=(pl.SEED_D,), _s=shift):
            return orig_ds(D, y, ev, wi, label.replace("moved 4 years early", f"moved {_s} years early"), seeds=seeds)
        pl.d_summary = d_summary
        argv = sys.argv
        sys.argv = [argv[0], "--variant", "timing4"]
        try:
            pl.main()
        finally:
            sys.argv = argv
            pl.d_summary = orig_ds
        for kind in ("summary", "places"):
            src = pl.OUT / f"parking_t52_d_timing4_{kind}.csv"
            src.rename(pl.OUT / f"parking_t56_placebo_shift{shift}_{kind}.csv")
        S = pd.read_csv(pl.OUT / f"parking_t56_placebo_shift{shift}_summary.csv")
        d = S[S["estimator"].str.startswith("method 2, D (repeals moved")]
        assert len(d) and (d["estimator"] == f"method 2, D (repeals moved {shift} years early)").all(), d["estimator"].unique()
    pl.cmp.complete = pl._orig_complete


def part_pools():
    import run_parking_t52_pool_rules as pr
    pr.OUT = REFERENCE / "t56_pool_rules" / "places"
    pr.REF_OUT = REFERENCE / "t56_pool_rules"
    pr.BATCH = REFERENCE  # base check against this working copy's D effects (same outcome)
    pr.OUT.mkdir(parents=True, exist_ok=True)
    argv = sys.argv
    sys.argv = [argv[0], "g_outmetro", "h1_dated"]
    try:
        pr.main()
    finally:
        sys.argv = argv


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default="event,long,poisson,placebo_dates,pools")
    a = ap.parse_args()
    if not os.environ.get("MM_REFERENCE_DIR") or Path(os.environ["MM_REFERENCE_DIR"]).resolve() == (ROOT / "reference").resolve():
        raise SystemExit("run on an outcome working copy (scripts/run_parking_t56.sh)")
    parts = a.parts.split(",")
    c56.patch_method2(m)
    c56.patch_rebuild(t46)
    if {"event", "long", "poisson"} & set(parts):
        D, real, cases, ev, wi = load()
        if "event" in parts:
            part_event(D, cases, ev, wi)
        if "long" in parts:
            part_long(D, cases, ev, wi)
        if "poisson" in parts:
            part_poisson(D, cases)
    if "placebo_dates" in parts:
        part_placebo_dates()
    if "pools" in parts:
        part_pools()


if __name__ == "__main__":
    main()
