"""Causal framework, Test 2b-L: binding lines inside broad upzonings (docs/tod/CAUSAL_FRAMEWORK_PLAN.md, section
"Test 2b-L", locked 2026-11-02 machine clock 16:52, before any count).

Inside each broad upzoning map (Los Angeles TOC 2017, San Diego 2021, Chicago 2022, Bellevue BelRed 2009; Honolulu
2017 beside), candidate lines are drawn on a pre-reform demand score (main: distance to the nearest stop; S1:
before-window building rate in the lot's 400 m neighbourhood; S2: pre-reform land value per lot acre). Stops are split
into two halves at random; the line with the largest jump in one half is tested, with the Test 2 edge estimator, in
the other half (cross-fit: a line is never chosen with the half it is tested on). A placebo-years run replaces the
after window with the second half of the before window.

    OMP_NUM_THREADS=1 caffeinate -i .venv/bin/python scripts/run_tod_causal_binding_line.py

Writes reference/tod_causal_binding_line.csv (summaries only: no lot rows, parcel ids, stop ids or owner names).
Lot samples come from run_tod_causal_edge_expand.read_case (as E1); estimation reuses run_tod_causal_edge.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import fftconvolve

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware import geom as G  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

SEED = 20261103
QUANTS = [q / 10 for q in range(1, 10)]          # share of the map's inside lot acres on the high-demand side
NEIGH_M, NEIGH_CELL = 400.0, 20.0
DISTRICT_POOL = (88.2, 50.8, 129.1)              # Test 2 floor pool, extra homes per 100 lot acres a year (90%)
PLACES = {  # case: (label, pooled?)
    "la_toc_2017": ("Los Angeles TOC 2017", True),
    "san_diego_2021": ("San Diego 2021", True),
    "chicago_2022": ("Chicago 2022", True),
    "bellevue_belred_2009": ("Bellevue BelRed 2009", True),
    "honolulu_2017": ("Honolulu 2017", False),
}
# S2 needs land value from BEFORE the reform. Only Chicago 2022's table carries one (Cook certified 2016 values); the
# other tables hold the current roll (LA and San Diego: Proposition 13 roll, King and Honolulu: current assessment).
PRE_REFORM_LAND_VALUE = {"chicago_2022"}
SCORES = {"distance to stop (main)": "dist", "S1 neighbourhood before-window rate": "s1", "S2 land value per acre": "s2"}
WINDOWS = {"real": dict(chg="chg", pre="pre", post="post"),
           "placebo years": dict(chg="ptr", pre="pre1", post="pre2")}


# ------------------------------------------------------------------ cross-fit core (unit-tested)

def split_stops(stop_ids, seed: int = SEED) -> dict:
    """Stops split into halves A and B at random (sorted ids, one permutation; A gets the first floor(n/2))."""
    s = np.array(sorted(set(stop_ids)), dtype=object)
    p = np.random.default_rng(seed).permutation(len(s))
    k = len(s) // 2
    return {s[i]: ("A" if j < k else "B") for j, i in enumerate(p)}


def choose_line(jumps: dict):
    """Candidate with the largest finite jump (None if no candidate is estimable)."""
    ok = {c: j for c, j in jumps.items() if j is not None and np.isfinite(j)}
    return max(ok, key=ok.get) if ok else None


def cross_fit(candidates, train_jump) -> dict:
    """For each test half, the line chosen on the OTHER half: {test_half: (candidate, {candidate: jump in train half})}.
    train_jump(train_half, candidate) -> jump; it is never called with the test half."""
    out = {}
    for test, train in (("B", "A"), ("A", "B")):
        jumps = {c: train_jump(train, c) for c in candidates}
        out[test] = (choose_line(jumps), jumps)
    return out


def wquantile(v, w, q):
    o = np.argsort(v)
    cw = np.cumsum(w[o]) / w.sum()
    return v[o][min(np.searchsorted(cw, q), len(v) - 1)]


# ------------------------------------------------------------------ samples and scores

def neighbourhood_rate(x, y, num, acres, r=NEIGH_M, cell=NEIGH_CELL):
    """100 x sum(num) / sum(acres) over other lots within r (grid of `cell` m, disk kernel; own lot left out)."""
    ix = ((x - x.min()) / cell).astype(int); iy = ((y - y.min()) / cell).astype(int)
    Gn = np.zeros((ix.max() + 1, iy.max() + 1)); Ga = np.zeros_like(Gn)
    np.add.at(Gn, (ix, iy), num); np.add.at(Ga, (ix, iy), acres)
    k = int(np.ceil(r / cell))
    gx, gy = np.mgrid[-k:k + 1, -k:k + 1]
    K = (np.hypot(gx, gy) * cell <= r).astype(float)
    Cn, Ca = fftconvolve(Gn, K, "same"), fftconvolve(Ga, K, "same")
    n, a = Cn[ix, iy] - num, Ca[ix, iy] - acres
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(a > 1e-6, 100 * np.clip(n, 0, None) / a, np.nan)


def inside_lots(case: str):
    """Inside-map lots of the reform group, as E1 (read_case: event windows, before-window halves, implausible out)."""
    import run_tod_causal_edge as E
    import run_tod_causal_edge_expand as EX
    src = EX.CAND if case == "seattle_roosevelt_2012" else EX.OUT
    D = EX.read_case(case, src)
    st = EX.stop_xy(D[D.group.isin(["reform", "comparison"])])
    import run_tod_station_model as M
    yb, ya = M.windows(case)
    P = D[(D.group == "reform") & D.in_reform_area & (D.acres_land > 0) & D.stop_id.notna()].copy()
    P["chg"] = P.homes_after_win / ya - P.homes_before_win / yb
    P["pre"], P["post"] = P.homes_before_win / yb, P.homes_after_win / ya
    P["ptr"] = P.pre2 - P.pre1
    P["public"] = P.public.fillna(False).astype(bool)
    P = P[P.stop_id.isin(st.index)]
    P["sx"], P["sy"] = st.sx.reindex(P.stop_id).to_numpy(), st.sy.reindex(P.stop_id).to_numpy()
    xy = P[["x", "y"]].to_numpy()
    P["s1"] = neighbourhood_rate(xy[:, 0], xy[:, 1], P.pre.to_numpy(), P.acres_land.to_numpy())
    P["s1_pl"] = neighbourhood_rate(xy[:, 0], xy[:, 1], P.pre1.fillna(0).to_numpy(), P.acres_land.to_numpy())
    P["s2"] = (P.land_value.where(P.land_value > 0) / P.acres_land) if case in PRE_REFORM_LAND_VALUE else np.nan
    P["dist"] = P.dist_m
    P["w"] = 1.0
    return P.reset_index(drop=True), st, E


def line_frame(P: pd.DataFrame, score: str, cut: float, water: list, E) -> pd.DataFrame:
    """Lots within 200 m of the candidate line, as a Test 2 edge sample: in_reform_area = high-demand side, s = signed
    distance (+ high side), (bx, by) = the lot's boundary point, water = boundary point within 30 m of water."""
    if score == "dist":                                   # circle of radius cut around the nearest stop (exact)
        high = P.dist.to_numpy() <= cut
        d = np.abs(cut - P.dist.to_numpy())
        vx, vy = P.x.to_numpy() - P.sx.to_numpy(), P.y.to_numpy() - P.sy.to_numpy()
        n = np.hypot(vx, vy); n[n == 0] = np.nan
        bx, by = P.sx.to_numpy() + vx / n * cut, P.sy.to_numpy() + vy / n * cut
        Q = P
    else:                                                 # score level set: lot-midway line between the two sides
        Q = P[P[score].notna()].reset_index(drop=True)
        high = Q[score].to_numpy() > cut
        Z = Q.assign(in_reform_area=high)
        d, bx, by, _, _ = E.lot_midway(Z, np.arange(len(Z)))
    F = Q.assign(in_reform_area=high, s=np.where(high, d, -d), bx=bx, by=by)
    F = F[np.abs(F.s) <= 200].copy()
    F["water"] = False
    if water and len(F):
        F["water"] = np.isfinite(G.distance_to_polygons(F.bx.values, F.by.values, water, E.WATER_M))
    return F


def jump(F: pd.DataFrame, half: str, y: str, E, donut=0.0):
    """Edge estimate at the line in one half: Test 2 selection (91 m, usable 400 m segments) on the half's lots."""
    T = E.select(F[F.half == half], E.H_MAIN, "s", donut)
    if not len(T):
        return T, np.nan
    nin, nout = int(T.in_reform_area.sum()), int((~T.in_reform_area).sum())
    if nin < E.MIN_LOTS or nout < E.MIN_LOTS:
        return T, np.nan
    return T, float(E.diff_from(E.seg_sums(T, y).sum(0)))


def stop_boot(T: pd.DataFrame, y: str, rng, E):
    """Test 2 estimate with stop-cluster bootstrap draws (clusters = nearest stops)."""
    return E.boot(T.assign(seg=pd.factorize(T.stop_id)[0]), y, rng)


def bunching_stop(F: pd.DataFrame, half: str, post: str, pre: str, rng, E):
    """Low-demand side within the map: (after near - after far) - (before near - before far), near 0-100 m, far
    100-200 m from the line; stop-cluster draws."""
    O = F[(F.half == half) & (F.s < 0) & (F.s >= -200) & ~F.water.astype(bool)].copy()
    if len(O) < 2 * E.MIN_LOTS:
        return np.nan, np.full(E.DRAWS, np.nan)
    O["near"] = O.s >= -100
    O["_a"], O["_p"], O["_b"] = O.acres_land, O[post], O[pre]
    O["seg"] = pd.factorize(O.stop_id)[0]
    g = O.groupby(["seg", "near"])[["_p", "_b", "_a"]].sum().unstack("near").fillna(0)
    if ("_a", True) not in g or ("_a", False) not in g:
        return np.nan, np.full(E.DRAWS, np.nan)
    A = np.c_[g[("_p", True)], g[("_b", True)], g[("_a", True)], g[("_p", False)], g[("_b", False)], g[("_a", False)]]

    def stat(V):
        with np.errstate(divide="ignore", invalid="ignore"):
            return 100 * ((V[..., 0] - V[..., 1]) / V[..., 2] - (V[..., 3] - V[..., 4]) / V[..., 5])
    n = len(A)
    W = rng.multinomial(n, np.full(n, 1 / n), size=E.DRAWS)
    return stat(A.sum(0)), stat(W @ A)


# ------------------------------------------------------------------ one place

def pct(d):
    return (np.nanpercentile(d, 5), np.nanpercentile(d, 95)) if np.isfinite(d).any() else (np.nan, np.nan)


def run_place(pi: int, case: str, label: str, water: list, E):
    P, st, _ = inside_lots(case)
    halves = split_stops(P.stop_id)
    P["half"] = P.stop_id.map(halves)
    tot_ac = P.acres_land.sum()
    info = {"place": label, "stops_inside_map": int(P.stop_id.nunique()), "stops_half_A": sum(v == "A" for v in halves.values()),
            "stops_half_B": sum(v == "B" for v in halves.values()), "inside_lots": len(P), "inside_lot_acres": float(tot_ac),
            "stop_fit_rmse_median_m": float(st.rmse.median())}
    print(label, info, flush=True)
    rows, draws = [], {}
    for si, (sname, sc) in enumerate(SCORES.items()):
        for wi, (wname, Wc) in enumerate(WINDOWS.items()):
            col = "s1_pl" if (sc == "s1" and wname == "placebo years") else sc
            base = {"place": label, "score": sname, "window": wname, "pooled_group": "main pool" if PLACES[case][1] else "beside (not pooled)"}
            if P[col].notna().sum() == 0:
                note = ("not run: lot table's land value is the current roll, not pre-reform" if sc == "s2" else "not run: no score")
                rows.append({**base, "level": "place", "status": note}); continue
            Q = P[P[col].notna()]
            v, w = Q[col].to_numpy(float), Q.acres_land.to_numpy(float)
            cands = {}
            for q in QUANTS:                                     # cut putting share q of acres on the high side
                c = wquantile(v, w, q) if sc == "dist" else wquantile(v, w, 1 - q)
                cands.setdefault(float(c), q)
            frames = {c: line_frame(P.assign(**{sc: P[col]}) if col != sc else P, sc, c, water, E) for c in cands}
            cf = cross_fit(list(cands), lambda train, c: jump(frames[c], train, Wc["chg"], E)[1])
            hd = {}
            for hi, test in enumerate(("A", "B")):
                c, jumps = cf[test]
                train = "B" if test == "A" else "A"
                r = {**base, "level": "half", "half_tested": test, "line_chosen_on_half": train,
                     "stops_in_test_half": sum(v_ == test for v_ in halves.values()),
                     "candidates_estimable_in_train_half": int(sum(np.isfinite(j) for j in jumps.values())),
                     "candidate_jumps_train_half": "; ".join(f"{int(round(100 * cands[k]))}%: {j:.1f}" for k, j in jumps.items() if np.isfinite(j))}
                if c is None:
                    rows.append({**r, "status": "no estimable candidate line in the training half"}); continue
                F = frames[c]
                hs = F.half == test
                shr = float(Q.acres_land[(Q[col] <= c) if sc == "dist" else (Q[col] > c)].sum() / Q.acres_land.sum())
                T, _ = jump(F, test, Wc["chg"], E)
                near = T if len(T) else F[hs & (F.s.abs() <= E.H_MAIN)]
                r.update({"line_nominal_share": cands[c], "line_share_of_map_acres": shr, "line_cut_value": c,
                          "line_cut_unit": {"dist": "metres from nearest stop", "s1": "new homes per 100 lot acres a year (400 m)",
                                            "s2": "dollars of 2016 certified land value per lot acre"}[sc],
                          "line_distance_to_stop_m": float(c) if sc == "dist" else (float(np.average(near.dist, weights=near.acres_land)) if len(near) else np.nan),
                          "line_distance_note": "radius of the line (exact)" if sc == "dist" else "acre-weighted mean distance to stop of lots within 91 m of the line",
                          "train_half_jump": jumps[c],
                          "lots_high_side": int(T.in_reform_area.sum()) if len(T) else 0, "lots_low_side": int((~T.in_reform_area).sum()) if len(T) else 0,
                          "acres_high_side": float(T.acres_land[T.in_reform_area].sum()) if len(T) else 0.0,
                          "acres_low_side": float(T.acres_land[~T.in_reform_area].sum()) if len(T) else 0.0,
                          "segments": int(T.seg.nunique()) if len(T) else 0, "stop_clusters": int(T.stop_id.nunique()) if len(T) else 0})
                if r["lots_high_side"] < E.MIN_LOTS or r["lots_low_side"] < E.MIN_LOTS:
                    rows.append({**r, "status": f"too few lots at the chosen line in the test half (< {E.MIN_LOTS} a side)"}); continue
                rng = np.random.default_rng([SEED, pi, si, wi, hi])
                pt, dr = stop_boot(T, Wc["chg"], rng, E)
                pb, pdr = stop_boot(T, Wc["pre"], rng, E)
                Td = E.select(F[hs], E.H_MAIN, "s", E.DONUT)
                ok_d = len(Td) and Td.in_reform_area.sum() >= E.MIN_LOTS and (~Td.in_reform_area).sum() >= E.MIN_LOTS
                dpt, ddr = stop_boot(Td, Wc["chg"], rng, E) if ok_d else (np.nan, np.full(E.DRAWS, np.nan))
                bs, bd = bunching_stop(F, test, Wc["post"], Wc["pre"], rng, E)
                (lo, hi_), (plo, phi), (dlo, dhi), (blo, bhi) = pct(dr), pct(pdr), pct(ddr), pct(bd)
                r.update({"status": "estimated", "effect_per_100_lot_acres_per_year": pt, "low": lo, "high": hi_,
                          "balance_pre_gap_per_100_acres": pb, "balance_low": plo, "balance_high": phi, "balance_pass": bool(plo <= 0 <= phi),
                          "donut_25m_effect": dpt, "donut_low": dlo, "donut_high": dhi,
                          "bunching_stat": bs, "bunching_low": blo, "bunching_high": bhi,
                          "cluster_note": "1 stop cluster: interval degenerate" if r["stop_clusters"] < 2 else ""})
                hd[test] = (pt, dr, pb, pdr, dpt, ddr, bs, bd)
                rows.append(r)
            # place = mean of the two halves (draw by draw)
            pr = {**base, "level": "place", "half_tested": "A and B" if len(hd) == 2 else "+".join(hd) or "none"}
            if not hd:
                rows.append({**pr, "status": "not estimable in either half"}); continue
            K = list(hd)
            m = lambda i: np.nanmean([hd[k][i] for k in K])  # noqa: E731
            md = lambda i: np.nanmean(np.stack([hd[k][i] for k in K]), axis=0)  # noqa: E731
            dr, pdr, ddr, bd = md(1), md(3), md(5), md(7)
            (lo, hi_), (plo, phi), (dlo, dhi), (blo, bhi) = pct(dr), pct(pdr), pct(ddr), pct(bd)
            hr = [x for x in rows if x.get("level") == "half" and x["score"] == sname and x["window"] == wname and x["place"] == label and x.get("status") == "estimated"]
            pr.update({"status": "estimated" if len(K) == 2 else "estimated from one half only (deviation)",
                       "effect_per_100_lot_acres_per_year": m(0), "low": lo, "high": hi_,
                       "balance_pre_gap_per_100_acres": m(2), "balance_low": plo, "balance_high": phi, "balance_pass": bool(plo <= 0 <= phi),
                       "donut_25m_effect": m(4), "donut_low": dlo, "donut_high": dhi, "bunching_stat": m(6), "bunching_low": blo, "bunching_high": bhi,
                       "lots_high_side": sum(x["lots_high_side"] for x in hr), "lots_low_side": sum(x["lots_low_side"] for x in hr),
                       "line_share_of_map_acres": np.mean([x["line_share_of_map_acres"] for x in hr]),
                       "line_distance_to_stop_m": np.mean([x["line_distance_to_stop_m"] for x in hr]),
                       "halves_line_gap_share": abs(hr[0]["line_share_of_map_acres"] - hr[1]["line_share_of_map_acres"]) if len(hr) == 2 else np.nan})
            rows.append(pr)
            draws[(label, sname, wname)] = (dr, ddr, bd)
    return rows, draws, info


# ------------------------------------------------------------------ pools and reading

def reading(lo, hi):
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return "not estimable"
    if lo <= 0 <= hi:
        return "No binding line found"
    if hi < DISTRICT_POOL[1]:
        return "Jump, but smaller"
    if lo <= DISTRICT_POOL[2] and hi >= DISTRICT_POOL[1]:
        return "Supports the idea"
    return "Jump above the district interval (no locked label)"


def pool_rows(R: pd.DataFrame, draws: dict, f_wi: float) -> list:
    out = []
    for sname in SCORES:
        for wname in WINDOWS:
            V = R[(R.level == "place") & (R.score == sname) & (R.window == wname) & (R.pooled_group == "main pool")
                  & R.status.str.startswith("estimated", na=False)]
            for filt, U in (("balance-passing places (locked)", V[V.balance_pass.astype(bool)]), ("all estimable places (no balance filter; beside)", V)):
                base = {"place": f"POOLED ({filt})", "level": "pooled", "score": sname, "window": wname, "pooled_group": "main pool",
                        "places_in_pool": ";".join(U.place), "n_places": len(U)}
                if not len(U):
                    out.append({**base, "status": "no places"}); continue
                e = U.set_index("place").effect_per_100_lot_acres_per_year
                dm = np.nanmean(np.stack([draws[(p, sname, wname)][0] for p in U.place]), axis=0)
                dd = np.nanmean(np.stack([draws[(p, sname, wname)][1] for p in U.place]), axis=0)
                bd = np.nanmean(np.stack([draws[(p, sname, wname)][2] for p in U.place]), axis=0)
                lo, hi = pct(dm)
                loo = [e.drop(p).mean() for p in e.index] if len(e) > 1 else [np.nan]
                blo, bhi = pct(bd)
                r = {**base, "status": "pooled", "effect_per_100_lot_acres_per_year": e.mean(), "low": lo, "high": hi,
                     "loo_low": min(loo), "loo_high": max(loo),
                     "donut_25m_effect": U.donut_25m_effect.mean(), "donut_low": pct(dd)[0], "donut_high": pct(dd)[1],
                     "bunching_stat": U.bunching_stat.mean(), "bunching_low": blo, "bunching_high": bhi, "bunching_flag": bool(bhi < 0),
                     "lots_high_side": int(U.lots_high_side.sum()), "lots_low_side": int(U.lots_low_side.sum()),
                     "wisconsin_extra_homes_2027_2031": e.mean() * f_wi, "wisconsin_low": lo * f_wi, "wisconsin_high": hi * f_wi,
                     "wisconsin_loo_low": min(loo) * f_wi, "wisconsin_loo_high": max(loo) * f_wi,
                     "reading": reading(lo, hi) + (" (placebo years: should include 0)" if wname == "placebo years" else "")}
                out.append(r)
    return out


def main() -> None:
    import run_tod_causal_edge as E
    import run_tod_causal_edge_expand as EX
    rows, draws, infos = [], {}, []
    for pi, case in enumerate(PLACES):
        label = PLACES[case][0]
        E.WATER[label] = EX.NEW[case][3]
        water = E.water_polys(label)
        r, d, info = run_place(pi, case, label, water, E)
        info["water_layer"] = "TIGER 2024 area water" if water else "none on disk"
        for x in r:
            x.setdefault("water_layer", info["water_layer"])
            x["stops_inside_map"] = info["stops_inside_map"]
        rows += r; draws.update(d); infos.append(info)
    R = pd.DataFrame(rows)
    P = pd.DataFrame(pool_rows(R, draws, EX.F_WI))
    I = pd.DataFrame(infos).assign(level="place info", status="info")
    out = pd.concat([R, P, I], ignore_index=True)
    out["unit"] = "extra new homes per 100 lot acres a year (high-demand side minus low-demand side, after minus before)"
    out.loc[out.window == "placebo years", "unit"] = ("new homes per 100 lot acres a year (high minus low side, second half of "
                                                      "the before window minus first half)")
    out["wisconsin_factor"] = EX.F_WI
    out["district_pool_reference"] = f"{DISTRICT_POOL[0]} ({DISTRICT_POOL[1]} to {DISTRICT_POOL[2]})"
    out["deviations"] = ("S1 neighbourhood on a 20 m grid (distances within about 15 m); placebo-years S1 uses the first half of the "
                         "before window only; S2 run only where pre-reform land value is on disk (Chicago 2022, 2016 values); "
                         "no arterial tag (beside item in E1); place balance = mean of the two halves' gaps")
    first = ["place", "level", "score", "window", "half_tested", "line_chosen_on_half", "status", "effect_per_100_lot_acres_per_year", "low", "high",
             "balance_pass", "balance_pre_gap_per_100_acres", "balance_low", "balance_high", "line_share_of_map_acres", "line_nominal_share",
             "line_distance_to_stop_m", "line_cut_value", "line_cut_unit", "lots_high_side", "lots_low_side", "reading",
             "wisconsin_extra_homes_2027_2031", "wisconsin_low", "wisconsin_high"]
    out = out[first + [c for c in out.columns if c not in first]]
    out.to_csv(REFERENCE / "tod_causal_binding_line.csv", index=False, float_format="%.4f")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 60)
    show = out[out.level.isin(["half", "place", "pooled"])]
    print(show[["place", "level", "score", "window", "half_tested", "status", "effect_per_100_lot_acres_per_year", "low", "high", "balance_pass",
                "line_share_of_map_acres", "line_distance_to_stop_m", "lots_high_side", "lots_low_side", "reading"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
