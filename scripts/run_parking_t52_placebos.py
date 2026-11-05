"""Test 52d placebo runs (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Test 52", 52d and audit fixes 4, 5, 9, 10).

Run on a working copy of reference/ with the batch 2026-11-05 outputs laid over it (MM_REFERENCE_DIR), as in
scripts/run_parking_t51_lihtc.sh; nothing under reference/ is changed except the new parking_t52_d_* outputs.

    uv run --all-extras python scripts/run_parking_t52_placebos.py --variant check     # shift 0, all units: reproduces the batch
    uv run --all-extras python scripts/run_parking_t52_placebos.py --variant timing4   # 52d.1: repeals moved 4 years early
    uv run --all-extras python scripts/run_parking_t52_placebos.py --variant houses    # 52d.2: 1-unit permits, houses list

Estimators (same pipeline as the batch):
- main: real average (weights homes x after-years) with the full placebo spread (run_parking_placebo.py --full logic:
  every eligible stand-in place at 0.5-2x population, state -> division -> nation until 20, 20,000 sets, seed 20261028),
  range = real average + (placebo p05 - p50, p95 - p50).
- D: corrected method 2, candidate D, OPT_MAIN, target-state mix (Wisconsin cells), winsorised; 90% range from a place
  bootstrap, 2,000 draws, seed 20261105.
timing4: event year = repeal year - 4 (after-years E-3..E-1, all before the real repeal); pools re-chosen for that year.
houses: same event years, windows and pools as the batch; outcome = 1-unit permits (all units minus units in 2+ unit
buildings) per 1,000 homes; homes (and D's pre-event homes) unchanged.
Outputs: reference/parking_t52_d_<variant>_{places,summary}.csv; stand-in effects in data/processed/t52/.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import os
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_parking_comparison as rpc  # noqa: E402
import run_parking_method2 as m2  # noqa: E402
import run_parking_salvage as rps  # noqa: E402
import run_parking_t45_t46 as t46  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

OUT = ROOT / "reference"
PROC = ROOT / "data" / "processed" / "t52"
SEED_D = 20261105
BOOT = 2000
SETS_FULL, PL_SEED, MIN_STANDINS = 20_000, 20261027, 20
WI_K = m2.WI_K  # 2,668,677 x 5 / 1000 = 13,343.385
SHIFT = 4

_orig_windows = cmp.windows
_orig_complete = cmp.complete
_cache: dict = {}


def fast_complete(p, years):
    """cmp.complete with a cache (same result; the panel object is fixed within a run)."""
    k = (id(p), tuple(years))
    if k not in _cache:
        _cache[k] = _orig_complete(p, years)
    return _cache[k]


def one_unit(p: pd.DataFrame) -> pd.DataFrame:
    q = p.copy()
    q["units_total"] = q["units_total"] - q["units_2plus"]
    return q


def load():
    """Data (corrected method 2) and the 74 cases with their recorded windows and pools."""
    m2.SUF, m2.CORRECTED = "_corrected", True
    pick = pd.read_csv(REFERENCE / "parking_method2_corrected_pick.csv")["candidate"].iloc[0]
    assert pick == "D", pick
    D = m2.Data()
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].dropna(subset=["effect"]).reset_index(drop=True)
    assert len(real) == 74, len(real)
    with contextlib.redirect_stdout(io.StringIO()):
        m = t46.rebuild(real, t46.collect())
    assert m["found"].all()
    cases = []
    for i, x in m.iterrows():
        c = x["call"]
        cases.append(dict(i=i, key=c["key"], event_year=int(real.loc[i, "event_year"]), pre=tuple(c["pre"]), post=tuple(c["post"]),
                          scale=float(x["scale"]), pop=float(real.loc[i, "population"]) if pd.notna(real.loc[i, "population"]) else np.nan,
                          trimmed=real.loc[i, "source"] == "rescued" and not str(real.loc[i, "place"]).startswith("South Bend"),
                          homes=float(real.loc[i, "homes"]), n_post=int(real.loc[i, "n_post"]), state=real.loc[i, "state"],
                          place=real.loc[i, "place"], prn_key=real.loc[i, "prn_key"], pool=list(c["pool"]),
                          call_homes=c["homes"], batch_effect=float(real.loc[i, "effect"])))
    return D, real, cases


# ------------------------------------------------------------------ main estimator ------------------------------------
def pool_change(p, keys, pre, post, homes) -> float:
    s = p[p["key"].isin(keys) & p["year"].isin(list(pre) + list(post))].groupby(["key", "year"])["units_total"].sum()
    h = homes.reindex(list(keys)).sum()
    a0 = s[s.index.get_level_values("year").isin(pre)].sum()
    a1 = s[s.index.get_level_values("year").isin(post)].sum()
    return float(a1 / len(post) / h * 1000 - a0 / len(pre) / h * 1000)


def main_real_recorded(p, cases) -> list[dict]:
    """Effects on the recorded batch windows and pools (houses variant and its all-units check)."""
    out = []
    for c in cases:
        own = pool_change(p, [c["key"]], c["pre"], c["post"], c["call_homes"])
        ctrl = pool_change(p, c["pool"], c["pre"], c["post"], c["call_homes"]) if c["pool"] else np.nan
        out.append(dict(i=c["i"], place=c["place"], state=c["state"], key=c["key"], event_year=c["event_year"],
                        n_post=len(c["post"]), homes=c["homes"], effect=(own - ctrl) / c["scale"], n_controls=len(c["pool"]),
                        status="included" if c["pool"] else "no pool"))
    return out


def main_real_shifted(p, cases, excluded, homes, popn, shift) -> list[dict]:
    """Effects with the event year moved `shift` years early; pools re-chosen by cmp.controls for that year."""
    out = []
    for c in cases:
        ey = c["event_year"] - shift
        e = cmp.effects(p, pd.DataFrame([{"key": c["key"], "event_year": ey}]), excluded - {c["key"]}, homes, popn, min_post=1)
        r = e.iloc[0].to_dict()
        row = dict(i=c["i"], place=c["place"], state=c["state"], key=c["key"], event_year=ey, real_event_year=c["event_year"],
                   status=r["status"])
        if r["status"] == "included":
            r = e[e["outcome"] == "all"].iloc[0]
            row.update(n_post=int(r["n_post"]), homes=c["homes"], effect=float(r["effect"]) / c["scale"],
                       n_controls=int(r["n_controls"]), pre_years=r["pre_years"], post_years=r["post_years"], pop_window=r["pop_window"])
        out.append(row)
    return out


def placebo_spread(p, real_rows, cases, excluded, homes, popn_plain, geo, shift, tag) -> dict:
    """run_parking_placebo.py --full logic on the variant's real places (stand-ins get the variant's event year)."""
    rng = np.random.default_rng(PL_SEED)
    rows, scopes = [], []
    byi = {c["i"]: c for c in cases}
    for r in real_rows:
        c = byi[r["i"]]
        ey = int(r["event_year"])
        st = c["key"].split("|")[0]
        pre, post = _orig_windows(ey)
        post = post[: int(r["n_post"])]
        ok = cmp.complete(p, pre + post) & set(homes.index)
        pop0 = popn_plain.get(c["key"], np.nan)
        if pd.isna(pop0):
            pop0 = c["pop"]
        size_ok = [k for k in ok if k not in excluded and 0.5 * pop0 <= popn_plain.get(k, np.nan) <= 2 * pop0]
        cand = [k for k in size_ok if k.startswith(st + "|")]
        scope = "state"
        if len(cand) < MIN_STANDINS:
            div = geo["division"].get(c["key"], "")
            cand, scope = [k for k in size_ok if geo["division"].get(k, "") == div], "division"
            if len(cand) < MIN_STANDINS:
                cand, scope = size_ok, "nation"
        scopes.append(dict(real_place=c["place"], scope=scope, standins=len(cand)))
        if not cand:
            continue
        print(tag, r["i"], c["place"], len(cand), flush=True)
        pick = list(rng.choice(sorted(cand), size=len(cand), replace=False))
        eff = cmp.effects(p, pd.DataFrame({"key": pick, "event_year": ey}), excluded | {c["key"]}, homes, popn_plain, min_post=1)
        eff = eff[(eff["status"] == "included") & (eff["outcome"] == "all")]
        eff = eff[eff["n_post"] == r["n_post"]]
        for x in eff.itertuples():
            rows.append(dict(real_index=r["i"], real_place=c["place"], placebo_key=x.key, event_year=ey,
                             n_post=int(x.n_post), homes=x.homes, effect=x.effect))
    pl = pd.DataFrame(rows)
    pl["weight"] = pl["homes"] * pl["n_post"]
    PROC.mkdir(parents=True, exist_ok=True)
    pl.round(4).to_csv(PROC / f"d_{tag}_standins.csv", index=False)
    pd.DataFrame(scopes).to_csv(PROC / f"d_{tag}_scopes.csv", index=False)
    pl = pl.dropna(subset=["effect", "weight"])
    pl = pl[pl["weight"] > 0]
    rng = np.random.default_rng(PL_SEED + 1)
    groups = {i: g for i, g in pl.groupby("real_index")}
    draws = np.column_stack([rng.integers(0, len(g), SETS_FULL) for g in groups.values()])
    eff_m = np.column_stack([g["effect"].values[draws[:, j]] for j, g in enumerate(groups.values())])
    w_m = np.column_stack([g["weight"].values[draws[:, j]] for j, g in enumerate(groups.values())])
    avgs = (eff_m * w_m).sum(axis=1) / w_m.sum(axis=1)
    y = np.array([r["effect"] for r in real_rows])
    w = np.array([r["homes"] * r["n_post"] for r in real_rows])
    real_avg = float(np.average(y, weights=w))
    p05, p50, p95 = (float(np.percentile(avgs, q)) for q in (5, 50, 95))
    return dict(estimator="main (real average, placebo spread)", weights="homes x after-years", places=len(real_rows),
                places_matched=len(groups), standin_places=len(pl), estimate=real_avg, p05=real_avg + (p05 - p50),
                p95=real_avg + (p95 - p50), placebo_p05=p05, placebo_p50=p50, placebo_p95=p95,
                share_placebo_at_or_below=float((avgs <= real_avg).mean()))


# ------------------------------------------------------------------ method D ------------------------------------------
def d_summary(D, y, ev, wi, label, seeds=(SEED_D,)) -> list[dict]:
    ok = np.isfinite(y)
    out = []
    for kind in m2.WEIGHTS:
        a = m2.weighted_avg(kind, y[ok], ev[ok].reset_index(drop=True), wi)
        for s in seeds:
            lo, hi = m2.boot_range(kind, y[ok], ev[ok].reset_index(drop=True), wi, BOOT, s)
            out.append(dict(estimator=label, weights=kind, places=int(ok.sum()), estimate=a, p05=lo, p95=hi, seed=s))
    return out


def d_ev(D, cases, n_post, v) -> pd.DataFrame:
    ev = pd.DataFrame({"v": [v[c["i"]] for c in cases], "homes": [c["homes"] for c in cases], "n_post": n_post,
                       "band": m2.band_of([c["pop"] if np.isfinite(c["pop"]) else 0 for c in cases]),
                       "metro": [D.metro.get(c["key"], 0.0) for c in cases]})
    ev["base"] = ev["homes"] * ev["n_post"]
    return ev


def d_band_pop(real, cases):
    # stage 2 bands by real["population"].fillna(0); keep that exactly
    for c in cases:
        c["pop_band"] = float(real.loc[c["i"], "population"]) if pd.notna(real.loc[c["i"], "population"]) else 0.0


def use_one_unit_in_D(D):
    P_all = D.P
    p1 = one_unit(D.p)
    P1 = p1[p1["year"].between(m2.FIRST, m2.LAST)].pivot_table(index="key", columns="year", values="units_total", aggfunc="sum")
    D.P = P1.reindex(index=P_all.index, columns=P_all.columns)

    @lru_cache(maxsize=None)
    def homes_pre(ey: int, fixed: bool = False) -> pd.Series:  # pre-event homes from all units, as in the batch
        if fixed:
            return D.homes
        since = P_all[[y for y in P_all.columns if ey <= y <= 2024]].sum(axis=1).reindex(D.homes.index).fillna(0)
        return (D.homes - since).clip(lower=D.homes * 0.5)
    D.homes_pre = homes_pre
    D.complete = lru_cache(maxsize=None)(lambda years: frozenset(P_all.index[P_all[list(years)].notna().all(axis=1)]))


# ------------------------------------------------------------------ driver --------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=("check", "timing4", "houses"), required=True)
    ap.add_argument("--no-placebo", action="store_true", help="skip the main estimator's stand-in spread")
    a = ap.parse_args()
    assert os.environ.get("MM_REFERENCE_DIR"), "run on a working copy (MM_REFERENCE_DIR)"
    D, real, cases = load()
    cmp.complete = fast_complete  # after load(): the recorded runs' panels are gone, so no stale ids in the cache
    d_band_pop(real, cases)
    for c in cases:
        c["pop"] = c["pop_band"]
    v = m2.placebo_v(len(real))
    wi = m2.target_cells(D, "55")
    geo = D.geo
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    reformed = tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
    p = D.p
    excluded = {k for r in reformed.drop_duplicates("prn_key").itertuples()
                if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    excluded |= {c["key"] for c in cases}
    homes, popn = D.homes, D.popn
    popn_plain = popn.drop(index=rps.SJ_KEY, errors="ignore")
    summ, places = [], []
    tag = a.variant

    if a.variant == "check":
        rec = main_real_recorded(p, cases)
        sh = main_real_shifted(p, cases, excluded, homes, popn, 0)
        for r0, r1, c in zip(rec, sh, cases):
            places.append(dict(place=c["place"], state=c["state"], batch_effect=c["batch_effect"], recorded_pool_effect=r0["effect"],
                               reselected_pool_effect=r1.get("effect", np.nan), reselected_status=r1["status"]))
        y = np.array([c["batch_effect"] for c in cases])
        w = np.array([c["homes"] * c["n_post"] for c in cases])
        summ.append(dict(estimator="main, batch file", weights="homes x after-years", places=len(y), estimate=float(np.average(y, weights=w))))
        y = np.array([r["effect"] for r in rec])
        summ.append(dict(estimator="main, recorded pools (houses path)", weights="homes x after-years", places=len(y),
                         estimate=float(np.average(y, weights=w))))
        ok = [r for r in sh if r["status"] == "included"]
        summ.append(dict(estimator="main, re-chosen pools (timing path, shift 0)", weights="homes x after-years", places=len(ok),
                         estimate=float(np.average([r["effect"] for r in ok], weights=[r["homes"] * r["n_post"] for r in ok]))))
        yd = np.array([m2.case_effect(D, c, "D", m2.OPT_MAIN)["effect"] for c in cases])
        evd = d_ev(D, cases, [c["n_post"] for c in cases], v)
        summ += d_summary(D, yd, evd, wi, "method 2, D (shift 0, all units)", seeds=(m2.SEED, SEED_D))
        # shift-0 D through the timing path (standard windows, trimmed off) for comparison
        yd2 = []
        for c in cases:
            pre, post = _orig_windows(c["event_year"])
            post = post[: c["n_post"]]
            yd2.append(m2.case_effect(D, dict(c, pre=tuple(pre), post=tuple(post), trimmed=False), "D", m2.OPT_MAIN)["effect"])
        summ += d_summary(D, np.array(yd2), evd, wi, "method 2, D (shift 0 via timing path)", seeds=(SEED_D,))
        for pl, a1, a2 in zip(places, yd, yd2):
            pl.update(d_effect=a1, d_effect_timing_path=a2)

    elif a.variant == "timing4":
        sh = main_real_shifted(p, cases, excluded, homes, popn, SHIFT)
        inc = [r for r in sh if r["status"] == "included"]
        if not a.no_placebo:
            summ.append(placebo_spread(p, inc, cases, excluded, homes, popn_plain, geo, SHIFT, tag))
        else:
            y = np.array([r["effect"] for r in inc]); w = np.array([r["homes"] * r["n_post"] for r in inc])
            summ.append(dict(estimator="main (real average, no spread)", places=len(inc), estimate=float(np.average(y, weights=w))))
        yd, npd = [], []
        for c in cases:
            ey = c["event_year"] - SHIFT
            pre, post = _orig_windows(ey)
            if len(pre) < cmp.PRE_YEARS_MIN or not post:
                yd.append(np.nan); npd.append(len(post)); continue
            r = m2.case_effect(D, dict(c, event_year=ey, pre=tuple(pre), post=tuple(post), trimmed=False), "D", m2.OPT_MAIN)
            yd.append(r["effect"]); npd.append(len(post))
        yd = np.array(yd)
        summ += d_summary(D, yd, d_ev(D, cases, npd, v), wi, "method 2, D (repeals moved 4 years early)")
        for r, c, e in zip(sh, cases, yd):
            places.append({**r, "batch_effect": c["batch_effect"], "d_effect": e})

    else:  # houses
        hl = pd.read_csv(OUT / "parking_t52_d_houses_list.csv")
        keep = set(hl.loc[hl["in_list"], "prn_key"])
        sub = [c for c in cases if c["prn_key"] in keep]
        assert len(sub) == len(keep), (len(sub), len(keep))
        p1 = one_unit(p)
        rec = main_real_recorded(p1, sub)
        rec_all = main_real_recorded(p, sub)
        inc = [r for r in rec if r["status"] == "included"]
        if not a.no_placebo:
            summ.append(placebo_spread(p1, inc, sub, excluded, homes, popn_plain, geo, 0, tag))
        y = np.array([r["effect"] for r in rec_all]); w = np.array([r["homes"] * r["n_post"] for r in rec_all])
        summ.append(dict(estimator="context: main, all units, same places", weights="homes x after-years", places=len(y),
                         estimate=float(np.average(y, weights=w))))
        yd_all = np.array([m2.case_effect(D, c, "D", m2.OPT_MAIN)["effect"] for c in sub])
        ev = d_ev(D, sub, [c["n_post"] for c in sub], v)
        summ += d_summary(D, yd_all, ev, wi, "context: method 2, D, all units, same places")
        use_one_unit_in_D(D)
        yd = np.array([m2.case_effect(D, c, "D", m2.OPT_MAIN)["effect"] for c in sub])
        summ += d_summary(D, yd, ev, wi, "method 2, D, 1-unit permits")
        for r, ra, e, ea in zip(rec, rec_all, yd, yd_all):
            places.append({**r, "effect_all_units": ra["effect"], "d_effect": e, "d_effect_all_units": ea})

    S = pd.DataFrame(summ)
    for col in ("estimate", "p05", "p95"):
        if col in S:
            S["wi_" + col.replace("estimate", "homes")] = S[col] * WI_K
    S.round(4).to_csv(OUT / f"parking_t52_d_{tag}_summary.csv", index=False)
    pd.DataFrame(places).round(4).to_csv(OUT / f"parking_t52_d_{tag}_places.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.round(3).to_string())


if __name__ == "__main__":
    main()
