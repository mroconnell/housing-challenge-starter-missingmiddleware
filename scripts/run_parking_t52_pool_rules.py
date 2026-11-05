"""Test 52g and 52h (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Test 52"): method D reruns with changed pool rules.

    bash scripts/run_parking_t52_run.sh pool_rules        # sets MM_REFERENCE_DIR to the batch working copy

run_parking_method2.py is imported, not edited; each variant patches its pool functions and restores them after.
Variants (all method D = corrected method 2, candidate D, target-state mix, on the fixed 74-place batch sample):
  base        no change (must reproduce the batch's per-place D effects; it is the paired comparator)
  g_outmetro  52g: pool places in the repeal place's own metro (CBSA with LSAD M1) are ineligible; non-metro keep theirs
  h1_dated    52h.1: PRN places are excluded only if a PRN reform is dated on or before the last after-year;
              PRN places with any undated reform stay excluded (an undated reform cannot be placed after the window)
  h1_undated_in 52h.1 side reading: as h1_dated, but undated PRN reforms do not exclude
  h2_noland   52h.2: shock rule keeps test (a) (10%+ of homes lost) and drops test (b) (land area +-25%)
  h3_onemiss  52h.3: a pool place may miss one window year, filled with its own mean on the same side of the repeal
Per-variant place files go to data/processed/t52/; summaries to reference/parking_t52_g_*.csv and parking_t52_h_*.csv.
The base run also writes the per-place before-year gaps used by 52c (data/processed/t52/d_base_gaps.csv).
"""
from __future__ import annotations

import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
if not os.environ.get("MM_REFERENCE_DIR") or Path(os.environ["MM_REFERENCE_DIR"]).resolve() == (ROOT / "reference").resolve():
    raise SystemExit("set MM_REFERENCE_DIR to the batch working copy (scripts/run_parking_t52_run.sh)")

import run_parking_comparison as rpc  # noqa: E402
import run_parking_method2 as m  # noqa: E402
from missing_middleware.dbf import read_shapefile_attributes  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW  # noqa: E402

OUT = ROOT / "data" / "processed" / "t52"
REF_OUT = ROOT / "reference"
BATCH = ROOT / "reference" / "batch_2026-11-05"
PSEED, PDRAWS = 20261105, 2000
MIX = "target-state mix"
CUR: dict = {}
VARIANTS = ("base", "g_outmetro", "h1_dated", "h1_undated_in", "h2_noland", "h3_onemiss")


# ------------------------------------------------------------------ variant patches ---------------------------------
@contextmanager
def patched(name: str, D, aux: dict):
    saved = dict(eligible=m.eligible, rates=m.rates, case_effect=m.case_effect)
    shock0 = D.shock
    orig_elig, orig_rates, orig_case = saved["eligible"], saved["rates"], saved["case_effect"]
    try:
        if name == "g_outmetro":
            def elig(D_, target, years, mode_exc, shock_on, h):
                E = orig_elig(D_, target, years, mode_exc, shock_on, h)
                cb = aux["metro_cbsa"].get(target)
                return E if not cb else [k for k in E if aux["cbsa"].get(k) != cb]
            m.eligible = elig
        elif name in ("h1_dated", "h1_undated_in"):
            undated_in = name == "h1_undated_in"

            def elig(D_, target, years, mode_exc, shock_on, h):
                last = max(years)
                keep = D_.strict_exc
                D_.strict_exc = {k for k in keep if (aux["prn_first"].get(k, 9999) <= last)
                                 or (not undated_in and k in aux["prn_undated"]) or k not in aux["prn_any"]}
                try:
                    return orig_elig(D_, target, years, mode_exc, shock_on, h)
                finally:
                    D_.strict_exc = keep
            m.eligible = elig
        elif name == "h2_noland":
            D.shock = aux["shock_loss"]
        elif name == "h3_onemiss":
            def elig(D_, target, years, mode_exc, shock_on, h):
                ey = CUR["ey"]
                exc = (D_.strict_exc if mode_exc == "strict" else D_.main_exc) | m.m_cmp_spill(target)
                X = D_.P[list(years)]
                pre = [y for y in years if y < ey]
                post = [y for y in years if y > ey]
                ok = (X.isna().sum(axis=1) <= 1) & X[pre].notna().any(axis=1) & X[post].notna().any(axis=1)
                return sorted(k for k in X.index[ok] if k != target and k not in exc and (not shock_on or k not in D_.shock)
                              and k in h.index and np.isfinite(D_.popn.get(k, np.nan)))

            def rates(D_, keys, years, h):
                X = D_.P.loc[keys, list(years)].copy()
                ey = CUR.get("ey")
                if ey is not None and X.isna().values.any():
                    for side in ([y for y in years if y < ey], [y for y in years if y > ey]):
                        if side:
                            S = X[side]
                            X[side] = S.T.fillna(S.mean(axis=1)).T
                return X.div(h.reindex(keys), axis=0) * 1000

            def case_effect(D_, case, cand, opt):
                CUR["ey"] = case["event_year"]
                try:
                    return orig_case(D_, case, cand, opt)
                finally:
                    CUR.pop("ey", None)
            m.eligible, m.rates, m.case_effect = elig, rates, case_effect
        yield
    finally:
        m.eligible, m.rates, m.case_effect = saved["eligible"], saved["rates"], saved["case_effect"]
        D.shock = shock0


def build_aux(D) -> dict:
    aux = {}
    # 52g: CBSA code per BPS key; metro = LSAD M1
    bps = rpc.read_bps_us()
    bcb = bps.assign(key=lambda d: d["state_fips"].astype(str).str.strip() + "|" + d["bps_id"].astype(str).str.strip()) \
        .drop_duplicates("key", keep="last").set_index("key")["cbsa"].astype(str).str.strip()
    lsad = read_shapefile_attributes(RAW / "census_cbsa_cb_2024" / "cb_2024_us_cbsa_20m.zip").set_index("CBSAFP")["LSAD"]
    aux["cbsa"] = {k: bcb.get(k, "") for k in D.geo.index}
    aux["metro_cbsa"] = {k: c for k, c in aux["cbsa"].items() if lsad.get(c, "") == "M1"}
    # 52h.1: PRN city reforms by BPS key, earliest dated year and whether any row is undated
    tax = pd.read_csv(m.REFERENCE / "parking_reform_taxonomy.csv")
    cities = tax[tax["place_type"] == "city"]
    first, undated, anyk = {}, set(), set()
    for r in cities.itertuples():
        k = cmp.match_place(D.p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population)
        if not k:
            continue
        anyk.add(k)
        if pd.notna(r.adopted_year):
            first[k] = min(first.get(k, 9999), int(r.adopted_year))
        else:
            undated.add(k)
    assert anyk <= D.strict_exc, "PRN city keys not all in the strict list"
    aux["prn_first"], aux["prn_undated"], aux["prn_any"] = first, undated, anyk
    # 52h.2: shock test (a) only, rebuilt as in Data (corrected joins)
    ag = D.geo["acs_geoid"].map(m.ct_norm)
    g10 = pd.concat([m.gaz(RAW / "parking_older_reforms" / "Gaz_places_national.zip", "Gaz_places_national.txt", "160"),
                     m.gaz(RAW / "census_gazetteer_2010" / "Gaz_cousubs_national.zip", "Gaz_cousubs_national.txt", "060")])
    g24 = pd.concat([m.gaz(RAW / "census_gazetteer_2024" / "2024_Gaz_place_national.zip", "2024_Gaz_place_national.txt", "160"),
                     m.gaz(RAW / "census_gazetteer_2024" / "2024_Gaz_cousubs_national.zip", "2024_Gaz_cousubs_national.txt", "060")])
    g10, g24 = g10[~g10.index.str.endswith("00000")], g24[~g24.index.str.endswith("00000")]
    g10.index, g24.index = g10.index.map(m.ct_norm), g24.index.map(m.ct_norm)
    g10, g24 = g10[~g10.index.duplicated()], g24[~g24.index.duplicated()]
    hu10 = ag.map(g10["HU10"].astype(float))
    al10, al24 = ag.map(g10["ALAND"].astype(float)), ag.map(g24["ALAND"].astype(float))
    # Data's homes before the >0 filter: only places with homes <= 0 differ, and they are never eligible
    loss = (hu10 >= 1000) & (D.homes.reindex(hu10.index).fillna(0) <= 0.9 * hu10)
    land = ((al24 / al10) - 1).abs() >= 0.25
    sl = set(hu10.index[loss.fillna(False)])
    sland = set(al10.index[land.fillna(False)])
    aux["shock_loss"], aux["shock_land_only"] = sl, sland - sl
    aux["shock_check"] = (sl | sland) == D.shock
    return aux


# ------------------------------------------------------------------ helpers -----------------------------------------
def mix_avg(y, ev, cells):
    return m.weighted_avg(MIX, y, ev.reset_index(drop=True), cells)


def paired(y_new, y_old, ev, cells):
    ok = np.isfinite(y_new) & np.isfinite(y_old)
    a, b, e = y_new[ok], y_old[ok], ev[ok].reset_index(drop=True)
    shift = mix_avg(a, e, cells) - mix_avg(b, e, cells)
    rng = np.random.default_rng(PSEED)
    n = len(a)
    d = []
    for _ in range(PDRAWS):
        i = rng.integers(0, n, n)
        ei = e.iloc[i].reset_index(drop=True)
        d.append(mix_avg(a[i], ei, cells) - mix_avg(b[i], ei, cells))
    lo, hi = np.percentile(d, [5, 95])
    return shift, float(lo), float(hi), int(ok.sum())


def mean_dist(D, case, pool, E_ref, h):
    """Mean Mahalanobis distance of pool members to the repeal place, on the base run's eligible set (crowding,
    density, age; log population left out so every pool is scored on the same three traits)."""
    if not pool:
        return np.nan
    pl = m.long_pre(case["event_year"], list(case["pre"]), case.get("trimmed", False))
    T = m.traits(D, sorted(set(E_ref) | set(pool)) + [case["key"]], pl, case["event_year"], h, False, False)
    dist, _ = m.mahal(T, case["key"], list(pool))
    return float(dist.replace(np.inf, np.nan).mean())


def run_variant(name, D, cases, aux):
    rows = []
    with patched(name, D, aux):
        for c in cases:
            if name == "h3_onemiss":
                CUR["ey"] = c["event_year"]
            pl = m.long_pre(c["event_year"], list(c["pre"]), c.get("trimmed", False))
            h = D.homes_pre(c["event_year"], False)
            E = m.eligible(D, c["key"], list(pl) + list(c["post"]), "strict", True, h)
            CUR.pop("ey", None)
            r = m.case_effect(D, c, "D", m.OPT_MAIN)
            rows.append(dict(i=c["i"], place=c["place"], state=c["state"], key=c["key"], event_year=c["event_year"],
                             effect=r["effect"], step=r["step"], n_pool=r["n_pool"], n_eligible=len(E),
                             pool=";".join(r.get("pool", [])), pre_first=min(pl), pre_last=max(pl),
                             post_first=min(c["post"]), post_last=max(c["post"]), scale=c.get("scale", 1.0)))
    return pd.DataFrame(rows)


def gaps_d(D, cases, base):
    """52c: per place, the D comparison's before-year gap relative to year -1 (target minus winsorised pool rate)."""
    out = []
    for c, r in zip(cases, base.itertuples()):
        pool = r.pool.split(";") if isinstance(r.pool, str) and r.pool else []
        ey = c["event_year"]
        pl = m.long_pre(ey, list(c["pre"]), c.get("trimmed", False))
        if len(pool) < m.MIN_POOL or (ey - 1) not in pl:
            continue
        h = D.homes_pre(ey, False)
        yrs = list(pl) + list(c["post"])
        t = m.rates(D, [c["key"]], yrs, h).iloc[0]
        cr = m.pool_rate(D, pool, yrs, h, True)
        ref = t[ey - 1] - cr[ey - 1]
        for y in pl:
            if y != ey - 1:
                out.append(dict(i=c["i"], place=c["place"], rel_year=y - ey, gap=float((t[y] - cr[y] - ref) / c.get("scale", 1.0))))
    return pd.DataFrame(out)


# ------------------------------------------------------------------ main --------------------------------------------
def main() -> None:
    names = sys.argv[1:] or list(VARIANTS)
    OUT.mkdir(parents=True, exist_ok=True)
    m.SUF, m.CORRECTED = "_corrected", True
    t0 = time.time()
    D = m.Data()
    real, cases = m.real_cases()
    assert len(cases) == 74, len(cases)
    v = m.placebo_v(len(real))
    ev = pd.DataFrame({"v": v, "homes": real["homes"].values, "n_post": real["n_post"].values,
                       "band": m.band_of(real["population"].fillna(0)), "metro": [D.metro.get(c["key"], 0.0) for c in cases]})
    ev["base"] = ev["homes"] * ev["n_post"]
    wi = m.target_cells(D, "55")
    ev.to_csv(OUT / "d_ev.csv", index=False)
    wi.rename("h").reset_index().to_csv(OUT / "d_wi_cells.csv", index=False)
    aux = build_aux(D)
    print(f"data ready {time.time() - t0:.0f}s; shock rebuild matches Data: {aux['shock_check']}", flush=True)
    if not aux["shock_check"]:
        raise SystemExit("shock rebuild does not match Data.shock")
    names = ["base"] + [n for n in names if n != "base"]
    res = {}
    for n in names:
        t1 = time.time()
        res[n] = run_variant(n, D, cases, aux)
        res[n].to_csv(OUT / f"d_{n}_places.csv", index=False)
        print(n, f"{time.time() - t1:.0f}s", "estimate", round(mix_avg(res[n]["effect"].values, ev, wi), 4), flush=True)
    # base must reproduce the batch per-place D effects
    bp = pd.read_csv(BATCH / "parking_method2_corrected_places.csv")
    bp = bp[bp["variant"] == "method 2, D"].reset_index(drop=True)
    dif = np.abs(bp["effect"].values - res["base"]["effect"].values)
    print("base vs batch max |diff|", float(np.nanmax(dif)), flush=True)
    if not (np.nanmax(dif) < 1e-3 and (bp["place"].values == res["base"]["place"].values).all()):
        raise SystemExit("base run does not reproduce the batch D effects")
    gaps_d(D, cases, res["base"]).to_csv(OUT / "d_base_gaps.csv", index=False)

    yb = res["base"]["effect"].values
    summ, place_rows = [], []
    for n in names:
        y = res[n]["effect"].values
        ok = np.isfinite(y)
        a = mix_avg(y[ok], ev[ok], wi)
        lo, hi = m.boot_range(MIX, y[ok], ev[ok].reset_index(drop=True), wi, m.BOOT, m.SEED)
        s, slo, shi, npair = paired(y, yb, ev, wi) if n != "base" else (0.0, 0.0, 0.0, int(ok.sum()))
        row = dict(part="52g" if n.startswith("g") else "52h" if n.startswith("h") else "base", variant=n, places=int(ok.sum()),
                   estimate=a, p05=lo, p95=hi, wi_homes=a * m.WI_K, wi_p05=lo * m.WI_K, wi_p95=hi * m.WI_K,
                   paired_places=npair, shift=s, shift_p05=slo, shift_p95=shi, shift_wi=s * m.WI_K, shift_wi_p05=slo * m.WI_K,
                   shift_wi_p95=shi * m.WI_K, shift_counts=bool(n != "base" and (slo > 0 or shi < 0)),
                   unit="homes permitted per 1,000 existing homes a year; WI homes = rate x 13,343.385")
        # pool diagnostics against base
        bpools = [set(p.split(";")) if isinstance(p, str) and p else set() for p in res["base"]["pool"]]
        npools = [set(p.split(";")) if isinstance(p, str) and p else set() for p in res[n]["pool"]]
        row["pools_changed"] = int(sum(a_ != b_ for a_, b_ in zip(bpools, npools)))
        row["mean_pool_size"] = float(res[n]["n_pool"].mean())
        row["mean_eligible"] = float(res[n]["n_eligible"].mean())
        row["mean_eligible_base"] = float(res["base"]["n_eligible"].mean())
        if n == "g_outmetro":
            lost, dist0, dist1, metro_places = [], [], [], 0
            for c, b_, n_, br, nr in zip(cases, bpools, npools, res["base"].itertuples(), res[n].itertuples()):
                cb = aux["metro_cbsa"].get(c["key"])
                in_m = sum(aux["cbsa"].get(k) == cb for k in b_) if cb else 0
                metro_places += bool(cb)
                h = D.homes_pre(c["event_year"], False)
                pl = m.long_pre(c["event_year"], list(c["pre"]), c.get("trimmed", False))
                E0 = m.eligible(D, c["key"], list(pl) + list(c["post"]), "strict", True, h)
                d0, d1 = mean_dist(D, c, sorted(b_), E0, h), mean_dist(D, c, sorted(n_), E0, h)
                lost.append(in_m)
                dist0.append(d0)
                dist1.append(d1)
                place_rows.append(dict(variant=n, place=c["place"], state=c["state"], metro_cbsa=cb or "",
                                       base_pool_in_metro=in_m, eligible_base=br.n_eligible, eligible_rerun=nr.n_eligible,
                                       eligible_lost=br.n_eligible - nr.n_eligible, step_base=br.step, step_rerun=nr.step,
                                       pool_base=br.n_pool, pool_rerun=nr.n_pool, mean_mahal_base=d0, mean_mahal_rerun=d1,
                                       effect_base=br.effect, effect_rerun=nr.effect))
            row.update(repeal_places_in_metro=metro_places, base_pool_members_in_metro=int(np.sum(lost)),
                       pools_losing_members=int(np.sum(np.array(lost) > 0)),
                       mean_eligible_lost=float((res["base"]["n_eligible"] - res[n]["n_eligible"]).mean()),
                       mean_mahal_base=float(np.nanmean(dist0)), mean_mahal_rerun=float(np.nanmean(dist1)))
        if n.startswith("h1"):
            entered = [k for b_, n_ in zip(bpools, npools) for k in (n_ - b_)]
            row.update(prn_places_entering_pools=len(set(entered)), prn_pool_slots_added=len(entered),
                       repeal_places_entering_pools=len(set(entered) & {c["key"] for c in cases}),
                       prn_city_keys=len(aux["prn_any"]), prn_keys_with_dated_reform=len(aux["prn_first"]),
                       prn_keys_with_undated_reform=len(aux["prn_undated"]))
        if n == "h2_noland":
            entered = [k for b_, n_ in zip(bpools, npools) for k in (n_ - b_)]
            row.update(land_only_flags_readmitted=len(aux["shock_land_only"]), readmitted_places_in_pools=len(set(entered) & aux["shock_land_only"]),
                       pool_slots_added=len(entered))
        if n == "h3_onemiss":
            fb = fa = gain = 0
            for c, b_, n_ in zip(cases, bpools, npools):
                pl = m.long_pre(c["event_year"], list(c["pre"]), c.get("trimmed", False))
                yrs = list(pl) + list(c["post"])
                X = D.P.loc[sorted(n_), yrs] if n_ else pd.DataFrame(columns=yrs)
                miss = X.isna()
                fb += int(miss[[y for y in yrs if y < c["event_year"]]].values.sum())
                fa += int(miss[[y for y in yrs if y > c["event_year"]]].values.sum())
                gain += bool(miss.any(axis=1).any())
            row.update(filled_years_before=fb, filled_years_after=fa, pools_gaining_filled_places=gain,
                       share_pools_gaining=gain / len(cases))
        summ.append(row)
    S = pd.DataFrame(summ)
    for part, pre in (("52g", "g"), ("52h", "h")):
        sub = S[S["part"].isin(["base", part])].dropna(axis=1, how="all")
        if (sub["part"] == part).any():
            sub.round(4).to_csv(REF_OUT / f"parking_t52_{pre}_summary.csv", index=False)
    if place_rows:
        pd.DataFrame(place_rows).round(4).to_csv(REF_OUT / "parking_t52_g_places.csv", index=False)
    allp = pd.concat([res[n].assign(variant=n) for n in names], ignore_index=True)
    allp[allp["variant"].str.startswith("h") | (allp["variant"] == "base")].drop(columns=["pool"]).round(4) \
        .to_csv(REF_OUT / "parking_t52_h_places.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.round(3).T.to_string())


if __name__ == "__main__":
    main()
