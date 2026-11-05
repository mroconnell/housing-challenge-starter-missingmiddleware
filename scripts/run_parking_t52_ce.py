"""Test 52c and 52e (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Test 52"): pre-trend bounds, P2 trend-matched rerun,
leave-one-out and largest-3 shares, for the main matched DiD and method D, on the fixed 74-place batch sample.

    bash scripts/run_parking_t52_run.sh ce     # after pool_rules (reads data/processed/t52/d_base_*.csv)

Main: the 74 effects and pools are rebuilt from the batch working copy with run_parking_t45_t46 (writes off), and
must match the stored effects. Main range = real average with the batch placebo spread (set draws rebuilt exactly as in
run_parking_placebo.py --full; checked against the batch summary). D range = run_parking_method2.boot_range (as the batch).
52c bound (P3 form, relative magnitudes): range widened by M x G each side, G = the largest absolute weighted
before-year gap relative to year -1 (main: home x after-year weights; D: target-state mix). M = 0, 0.5, 1.
P2 on the 74: each place's batch pool cut to the 10 places with the nearest before-window OLS slope (all if 10 or fewer).
Paired shifts: rerun minus batch on the same places, paired place bootstrap, 2,000 draws, seed 20261105.
Outputs: reference/parking_t52_c_*.csv, parking_t52_e_*.csv
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
if not os.environ.get("MM_REFERENCE_DIR") or Path(os.environ["MM_REFERENCE_DIR"]).resolve() == (ROOT / "reference").resolve():
    raise SystemExit("set MM_REFERENCE_DIR to the batch working copy (scripts/run_parking_t52_run.sh)")

import run_parking_method2 as m  # noqa: E402
import run_parking_t45_t46 as t46  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

T52 = ROOT / "data" / "processed" / "t52"
OUT = ROOT / "reference"
WI_K = 2_668_677 * 5 / 1000
PSEED, PDRAWS = 20261105, 2000
PL_SEED, PL_SETS = 20261027, 20_000
MIX = "target-state mix"
UNIT = "homes permitted per 1,000 existing homes a year; WI homes = rate x 13,343.385"
MS = (0.0, 0.5, 1.0)


def wavg(y, w):
    k = np.isfinite(y)
    return float(np.sum(y[k] * w[k]) / np.sum(w[k]))


def boot_idx():
    rng = np.random.default_rng(PSEED)
    return [rng.integers(0, 74, 74) for _ in range(PDRAWS)]


def wi(d: dict) -> dict:
    return {f"{k}_wi": v * WI_K for k, v in d.items() if isinstance(v, float) and k in ("estimate", "p05", "p95", "shift", "shift_p05", "shift_p95")}


# ------------------------------------------------------------------ main estimator ----------------------------------
def placebo_avgs():
    pl = pd.read_csv(REFERENCE / "parking_placebo_full_places.csv")
    pl = pl.dropna(subset=["effect", "weight"])
    pl = pl[pl["weight"] > 0]
    rng = np.random.default_rng(PL_SEED + 1)
    groups = {i: g for i, g in pl.groupby("real_index")}
    draws = np.column_stack([rng.integers(0, len(g), PL_SETS) for g in groups.values()])
    E = np.column_stack([g["effect"].values[draws[:, j]] for j, g in enumerate(groups.values())])
    W = np.column_stack([g["weight"].values[draws[:, j]] for j, g in enumerate(groups.values())])
    return list(groups), E, W


def pl_range(real_avg, E, W, drop=None):
    if drop is not None:
        E, W = np.delete(E, drop, axis=1), np.delete(W, drop, axis=1)
    a = (E * W).sum(axis=1) / W.sum(axis=1)
    p05, p50, p95 = np.percentile(a, [5, 50, 95])
    return real_avg + (p05 - p50), real_avg + (p95 - p50)


def rate(p, keys, years, homes):
    a, h = t46.sums(p, list(keys), list(years), homes)
    return float(a.sum() / len(years) / h.sum() * 1000)


def ols_slope(p, k, yrs, homes):
    v = np.array([rate(p, [k], [y], homes) for y in yrs])
    return np.polyfit(np.array(yrs, float), v, 1)[0] if len(yrs) >= 3 and np.all(np.isfinite(v)) else np.nan


def main_parts():
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].reset_index(drop=True)
    assert len(real) == 74 and real["effect"].notna().all()
    y = real["effect"].values
    w = (real["homes"] * real["n_post"]).values
    reb = t46.rebuild(real, t46.collect())
    bad = (~reb["found"]) | ((reb["effect"] - real["effect"]).abs() > 1e-4)
    if bad.any():
        raise SystemExit("main rebuild does not match the batch effects")
    summ = pd.read_csv(REFERENCE / "parking_placebo_full_summary.csv").iloc[0]
    groups, E, W = placebo_avgs()
    base = wavg(y, w)
    lo0, hi0 = pl_range(base, E, W)
    assert abs(base - summ["real_average"]) < 1e-4 and abs(lo0 - summ["range_from_placebo_low"]) < 1e-3 \
        and abs(hi0 - summ["range_from_placebo_high"]) < 1e-3, (base, lo0, hi0, summ.to_dict())
    print(f"main reproduced: {base:.4f} [{lo0:.4f}, {hi0:.4f}]", flush=True)

    # ---- 52c gaps, P2 ----
    gaps, p2rows = [], []
    for i, x in reb.iterrows():
        c = x["call"]
        p, homes, pool, pre, post, e, sc = c["p"], c["homes"], c["pool"], c["pre"], c["post"], c["event_year"], x["scale"]
        k = c["key"]
        if (e - 1) in pre:
            ref = rate(p, [k], [e - 1], homes) - rate(p, pool, [e - 1], homes)
            for yr in pre:
                if yr != e - 1:
                    gaps.append(dict(i=i, place=real.loc[i, "place"], rel_year=yr - e,
                                     gap=(rate(p, [k], [yr], homes) - rate(p, pool, [yr], homes) - ref) / sc))
        s0 = ols_slope(p, k, pre, homes)
        cs = pd.Series({q: ols_slope(p, q, pre, homes) for q in pool}).dropna()
        near = list((cs - s0).abs().sort_values(kind="mergesort").index[:10]) if np.isfinite(s0) and len(cs) else list(pool)
        p2 = (x["own"] - t46.ctrl_change(p, near, pre, post, homes)) / sc
        early, late = [q for q in pre if q <= e - 3], [q for q in pre if q >= e - 2]

        def pt(pl_):
            if not (early and late):
                return np.nan
            return ((rate(p, [k], late, homes) - rate(p, [k], early, homes)) - (rate(p, pl_, late, homes) - rate(p, pl_, early, homes))) / sc
        p2rows.append(dict(place=real.loc[i, "place"], state=real.loc[i, "state"], main_effect=y[i], p2_effect=p2, pool=len(pool),
                           p2_pool=len(near), pool_cut=len(pool) > 10, pretrend_main=pt(pool), pretrend_p2=pt(near), weight=w[i]))
    G = pd.DataFrame(gaps)
    gk = G.groupby("rel_year").apply(lambda g: pd.Series(dict(places=len(g), gap=wavg(g["gap"].values, w[g["i"].values]))))
    Gmax = float(gk["gap"].abs().max())
    P2 = pd.DataFrame(p2rows)
    return dict(real=real, y=y, w=w, base=base, lo0=lo0, hi0=hi0, E=E, W=W, groups=groups, gk=gk, G=Gmax, P2=P2)


# ------------------------------------------------------------------ D ------------------------------------------------
def d_inputs():
    ev = pd.read_csv(T52 / "d_ev.csv")
    c = pd.read_csv(T52 / "d_wi_cells.csv")
    cells = pd.Series(c["h"].values, index=pd.MultiIndex.from_arrays([c["metro"].astype(float), c["band"].astype(int)]))
    b = pd.read_csv(T52 / "d_base_places.csv")
    g = pd.read_csv(T52 / "d_base_gaps.csv")
    return ev, cells, b, g


def mix(y, ev, cells):
    return m.weighted_avg(MIX, y, ev.reset_index(drop=True), cells)


def main() -> None:
    M = main_parts()
    ev, cells, db, dg = d_inputs()
    yd = db["effect"].values
    assert np.isfinite(yd).all() and len(yd) == 74 and (db["place"].values == M["real"]["place"].values).all()
    bres = pd.read_csv(REFERENCE / "parking_method2_corrected_results.csv")
    bres = bres[(bres["variant"] == "method 2, D") & (bres["weights"] == MIX)].iloc[0]
    d_est = mix(yd, ev, cells)
    d_lo, d_hi = m.boot_range(MIX, yd, ev, cells, m.BOOT, m.SEED)
    assert abs(d_est - bres["average"]) < 1e-3 and abs(d_lo - bres["p05"]) < 1e-3 and abs(d_hi - bres["p95"]) < 1e-3, (d_est, d_lo, d_hi)
    print(f"D reproduced: {d_est:.4f} [{d_lo:.4f}, {d_hi:.4f}]", flush=True)
    idx = boot_idx()
    y, w = M["y"], M["w"]

    # ---------------- 52c ----------------
    dgk = dg.groupby("rel_year").apply(lambda g: pd.Series(dict(places=len(g), gap=mix(g["gap"].values, ev.loc[g["i"].values], cells))))
    Gd = float(dgk["gap"].abs().max())
    gaps = pd.concat([M["gk"].assign(estimator="main"), dgk.assign(estimator="method D")]).reset_index()
    gaps["unit"] = "permits per 1,000 existing homes a year, repeal place minus pool, relative to year -1"
    gaps.round(4).to_csv(OUT / "parking_t52_c_gaps.csv", index=False)
    rows = []
    for est, a, lo, hi, G in (("main", M["base"], M["lo0"], M["hi0"], M["G"]), ("method D", d_est, d_lo, d_hi, Gd)):
        for Mv in MS:
            r = dict(part="52c bound", estimator=est, M=Mv, G=G, places=74, estimate=a, p05=lo - Mv * G, p95=hi + Mv * G)
            r.update(wi(r))
            r["range_includes_0"] = bool(r["p05"] <= 0 <= r["p95"])
            r["note"] = "breakdown M is 0 by definition: the M = 0 range already includes 0 (audit fix 3)" if est == "main" and Mv == 0 else ""
            rows.append(r)
    # P2 trend-matched rerun on the 74
    P2 = M["P2"]
    yp = P2["p2_effect"].values
    a2 = wavg(yp, w)
    bs = [wavg(yp[i], w[i]) for i in idx]
    sh = [wavg(yp[i], w[i]) - wavg(y[i], w[i]) for i in idx]
    r = dict(part="52c P2 trend-matched", estimator="main, P2 slope-matched pools", M=np.nan, G=np.nan, places=int(np.isfinite(yp).sum()),
             estimate=a2, p05=float(np.percentile(bs, 5)), p95=float(np.percentile(bs, 95)), shift=a2 - M["base"],
             shift_p05=float(np.percentile(sh, 5)), shift_p95=float(np.percentile(sh, 95)))
    r.update(wi(r))
    r["range_includes_0"] = bool(r["p05"] <= 0 <= r["p95"])
    r["shift_counts"] = bool(r["shift_p05"] > 0 or r["shift_p95"] < 0)
    r["note"] = (f"range = place bootstrap (2,000, seed 20261105), not the placebo spread; pools cut in {int(P2['pool_cut'].sum())} of 74 places "
                 f"(the rest had 10 or fewer pool places, so P2 leaves them unchanged)")
    rows.append(r)
    for col, lab in (("pretrend_main", "pre-trend check, batch main pools (-2..-1 vs -5..-3)"), ("pretrend_p2", "pre-trend check, P2 pools")):
        v = P2[col].values
        k = np.isfinite(v)
        bsv = [wavg(v[i], w[i]) for i in idx]
        r = dict(part="52c P2 trend-matched", estimator=lab, places=int(k.sum()), estimate=wavg(v, w),
                 p05=float(np.percentile(bsv, 5)), p95=float(np.percentile(bsv, 95)))
        r.update(wi(r))
        r["range_includes_0"] = bool(r["p05"] <= 0 <= r["p95"])
        rows.append(r)
    C = pd.DataFrame(rows)
    C["unit"] = UNIT
    C.round(4).to_csv(OUT / "parking_t52_c_summary.csv", index=False)
    P2.round(4).to_csv(OUT / "parking_t52_c_p2_places.csv", index=False)

    # ---------------- 52e ----------------
    real = M["real"]
    gpos = {g: j for j, g in enumerate(M["groups"])}
    full_main = np.array([wavg(y[i], w[i]) for i in idx])
    full_d = np.array([mix(yd[i], ev.iloc[i], cells) for i in idx])
    loo = []
    for j in range(74):
        keep = np.arange(74) != j
        am = wavg(y[keep], w[keep])
        lo, hi = pl_range(am, M["E"], M["W"], gpos.get(j))
        dm = np.array([wavg(y[i[i != j]], w[i[i != j]]) for i in idx]) - full_main
        ad = mix(yd[keep], ev[keep], cells)
        dlo, dhi = m.boot_range(MIX, yd[keep], ev[keep].reset_index(drop=True), cells, m.BOOT, m.SEED)
        dd = np.array([mix(yd[i[i != j]], ev.iloc[i[i != j]], cells) for i in idx]) - full_d
        loo.append(dict(place=real.loc[j, "place"], state=real.loc[j, "state"], event_year=int(real.loc[j, "event_year"]),
                        main_effect=y[j], main_weight_share=w[j] / w.sum(), main_loo=am, main_loo_p05=lo, main_loo_p95=hi,
                        main_shift=am - M["base"], main_shift_p05=float(np.percentile(dm, 5)), main_shift_p95=float(np.percentile(dm, 95)),
                        d_effect=yd[j], d_loo=ad, d_loo_p05=dlo, d_loo_p95=dhi, d_shift=ad - d_est,
                        d_shift_p05=float(np.percentile(dd, 5)), d_shift_p95=float(np.percentile(dd, 95))))
        if j % 10 == 0:
            print("loo", j, flush=True)
    L = pd.DataFrame(loo)
    L["main_shift_counts"] = (L["main_shift_p05"] > 0) | (L["main_shift_p95"] < 0)
    L["d_shift_counts"] = (L["d_shift_p05"] > 0) | (L["d_shift_p95"] < 0)
    for c in ("main_loo", "main_loo_p05", "main_loo_p95", "main_shift", "d_loo", "d_loo_p05", "d_loo_p95", "d_shift"):
        L[c + "_wi"] = L[c] * WI_K
    L.round(4).to_csv(OUT / "parking_t52_e_loo.csv", index=False)

    # largest-3: by weight (size) and by absolute contribution; contribution = weight share x effect (D: winsorised effect)
    wd, _ = m.mix_weights(ev.reset_index(drop=True), cells)
    ydw = m.winsor(yd)
    contrib = {"main": (w / w.sum()) * y, "method D": wd * ydw}
    wts = {"main": w / w.sum(), "method D": wd}
    tot = {"main": M["base"], "method D": d_est}
    full_draw = {"main": full_main, "method D": full_d}
    sh_rows = []
    for est in ("main", "method D"):
        for how, order in (("largest weight", np.argsort(-wts[est], kind="mergesort")),
                           ("largest absolute contribution", np.argsort(-np.abs(contrib[est]), kind="mergesort"))):
            top = order[:3]
            keep = ~np.isin(np.arange(74), top)
            if est == "main":
                a = wavg(y[keep], w[keep])
                lo, hi = pl_range(a, M["E"], M["W"], [gpos[t] for t in top if t in gpos])
                dd = np.array([wavg(y[i[np.isin(i, np.flatnonzero(keep))]], w[i[np.isin(i, np.flatnonzero(keep))]]) for i in idx]) - full_draw[est]
            else:
                a = mix(yd[keep], ev[keep], cells)
                lo, hi = m.boot_range(MIX, yd[keep], ev[keep].reset_index(drop=True), cells, m.BOOT, m.SEED)
                dd = np.array([mix(yd[i[np.isin(i, np.flatnonzero(keep))]], ev.iloc[i[np.isin(i, np.flatnonzero(keep))]], cells) for i in idx]) - full_draw[est]
            r = dict(part="52e largest 3", estimator=est, rule=how, places_dropped="; ".join(f"{real.loc[t, 'place']}, {real.loc[t, 'state']}" for t in top),
                     weight_share_of_3=float(wts[est][top].sum()), contribution_of_3=float(contrib[est][top].sum()),
                     share_of_result_from_3=float(contrib[est][top].sum() / tot[est]), full_estimate=tot[est], places=71,
                     estimate=a, p05=lo, p95=hi, shift=a - tot[est], shift_p05=float(np.percentile(dd, 5)), shift_p95=float(np.percentile(dd, 95)))
            r.update(wi(r))
            r["shift_counts"] = bool(r["shift_p05"] > 0 or r["shift_p95"] < 0)
            sh_rows.append(r)
    S = pd.DataFrame(sh_rows)
    S["unit"] = UNIT
    S.round(4).to_csv(OUT / "parking_t52_e_largest3.csv", index=False)
    # Bastrop, named in advance
    j = int(np.flatnonzero(real["place"].str.startswith("Bastrop").values)[0])
    bas = dict(place="Bastrop, Texas", event_year=int(real.loc[j, "event_year"]), pre_years=real.loc[j, "pre_years"], post_years=real.loc[j, "post_years"],
               homes=real.loc[j, "homes"], main_effect=y[j], main_weight_share=w[j] / w.sum(), main_contribution=contrib["main"][j],
               main_share_of_result=contrib["main"][j] / M["base"], d_effect=yd[j], d_effect_winsorised=ydw[j], d_weight_share=wd[j],
               d_contribution=contrib["method D"][j], d_share_of_result=contrib["method D"][j] / d_est,
               main_effect_rank_high=int((y > y[j]).sum() + 1), d_effect_rank_high=int((yd > yd[j]).sum() + 1))
    pd.DataFrame([bas]).round(4).to_csv(OUT / "parking_t52_e_bastrop.csv", index=False)
    pd.set_option("display.width", 250)
    print(C.round(3).to_string())
    print(S.round(3).T.to_string())
    print(pd.Series(bas).to_string())
    print(L.sort_values("main_shift").round(3).head(5).to_string())
    print(L.sort_values("d_shift").round(3).head(5).to_string())


if __name__ == "__main__":
    main()
