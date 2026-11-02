"""Causal framework, Test 2 (learning plan T3): edge test, difference in discontinuities at reform-district boundaries
(docs/tod/CAUSAL_FRAMEWORK_PLAN.md, locked 2026-11-02 before any count).

Lots whose nearest stop is a reform stop (within 1 mile; sensitivity 1/2 mile), signed distance to the district
boundary (+ inside), inside-minus-outside change in new homes per 100 lot acres a year (after window minus before
window) within a bandwidth of the line; segment cluster bootstrap; balance, donut and bunching checks.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/run_tod_causal_edge.py

Writes reference/tod_causal_edge_test.csv (summaries only; no lot rows or ids).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware import geom as G  # noqa: E402
from missing_middleware import geom_extra_station as X  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
import run_tod_station_model as M  # noqa: E402
from run_tod_causal_citywide import places, cfg  # noqa: E402

OUT = M.OUT
CRS = 5070
H_MAIN, H_LO, H_HI = 91.44, 45.72, 182.88          # 300, 150, 600 ft
DONUT, SEG, PUBLIC_MAX, WATER_M, MIN_LOTS = 25.0, 400.0, 0.5, 30.0, 20
SEED, DRAWS = 20261103, 1000
POLY_CASES = {"denver_2018", "portland_2020", "austin_2009", "slc_2010"}
WATER = {"New York": ["36005", "36047", "36061", "36081", "36085"], "Philadelphia": ["42101"], "Charlotte 2019": ["37119"],
         "Chicago 2015": ["17031"], "Seattle Mount Baker 2014": ["53033"], "Seattle Othello 2012": ["53033"], "Saint Paul 2011": ["27123"]}
WI_QUARTER_ACRES, WI_SHARE, YEARS, RAMP = 4874.1, 0.15, 5, 1.2269
COLS = ["group", "dist_m", "band", "in_reform_area", "acres_land", "public", "land_value", "bldg_value", "year_built",
        "v_h14_vacancy_rate", "implausible", "homes_existing", "homes_before_win", "homes_after_win", "x", "y"]


# ------------------------------------------------------------------ boundary geometry

def boundary_points(polys: list, step: float = 5.0) -> np.ndarray:
    """Points every <= step metres along the edges of the union of polys (shared internal edges removed)."""
    seg, _ = G._segments(polys)
    seg = seg[np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1]) > 0]
    mx, my = (seg[:, 0] + seg[:, 2]) / 2, (seg[:, 1] + seg[:, 3]) / 2
    dx, dy = seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1]
    L = np.hypot(dx, dy)
    nx, ny = -dy / L * 0.5, dx / L * 0.5
    a = G.points_in_any(mx + nx, my + ny, polys, union=True)
    b = G.points_in_any(mx - nx, my - ny, polys, union=True)
    seg, L = seg[a != b], L[a != b]
    n = np.maximum(1, np.ceil(L / step)).astype(int)
    rep = np.repeat(np.arange(len(seg)), n + 1)
    t = np.concatenate([np.linspace(0, 1, k + 1) for k in n])
    s = seg[rep]
    return np.c_[s[:, 0] + t * (s[:, 2] - s[:, 0]), s[:, 1] + t * (s[:, 3] - s[:, 1])]


def lot_midway(D: pd.DataFrame, idx: np.ndarray):
    ins = D.in_reform_area.to_numpy()
    xy = D[["x", "y"]].to_numpy()
    d = np.full(len(idx), np.nan); bx = d.copy(); by = d.copy()
    for side in (True, False):
        opp = xy[ins != side]
        m = ins[idx] == side
        if not len(opp) or not m.any():
            continue
        dd, j = cKDTree(opp).query(xy[idx[m]])
        d[m] = dd / 2
        bx[m] = (xy[idx[m], 0] + opp[j, 0]) / 2; by[m] = (xy[idx[m], 1] + opp[j, 1]) / 2
    return d, bx, by


def water_polys(place: str) -> list:
    out = []
    for c in WATER.get(place, []):
        f = RAW / "tod_net_coverage" / "areawater" / f"tl_2024_{c}_areawater.zip"
        if f.exists():
            out += [g for g in X.read_vector(f, dst=CRS).geometry if g]
    return out


# ------------------------------------------------------------------ lot sample

def case_sample(case: str, place: str, water: list) -> pd.DataFrame:
    D = pd.read_parquet(OUT / f"lots_{case}.parquet", columns=COLS)
    if (OUT / f"events_{case}.parquet").exists():
        D = M.event_windows(case, D, "permit_est")
    D = D[~D.implausible.fillna(False).astype(bool)].copy()
    D["in_reform_area"] = D.in_reform_area.fillna(False).astype(bool)
    if not D.in_reform_area.any() or D.in_reform_area.all():
        return pd.DataFrame()
    samp = np.flatnonzero(((D.group == "reform") & (D.acres_land > 0)).to_numpy())
    dm, mx, my = lot_midway(D, samp)
    if case in POLY_CASES:
        from station_cases import cluster_west as W
        bp = boundary_points(W.reform_area(case))
        dd, j = cKDTree(bp).query(D[["x", "y"]].to_numpy()[samp])
        d, bx, by = dd, bp[j, 0], bp[j, 1]
    else:
        d, bx, by = dm, mx, my
    S = D.iloc[samp].copy()
    sign = np.where(S.in_reform_area.to_numpy(), 1.0, -1.0)
    S["s"], S["s_lotmid"] = sign * d, sign * dm
    S["bx"], S["by"], S["bx_lm"], S["by_lm"] = bx, by, mx, my
    S = S[(S.s.abs() <= 200) | (S.s_lotmid.abs() <= 200)]
    yb, ya = M.windows(case)
    c = cfg(case)
    eff = c["before"][1] + 1
    S["chg"] = S.homes_after_win / ya - S.homes_before_win / yb
    S["pre"] = S.homes_before_win / yb
    S["post"] = S.homes_after_win / ya
    S["case"] = case
    S["log_lv_acre"] = np.log(S.land_value.where(S.land_value > 0) / S.acres_land)
    S["log_acres"] = np.log(S.acres_land)
    S["bldg_age"] = (eff - S.year_built.where(S.year_built > 1700)).astype(float)
    S["lot_vacant"] = (S.bldg_value.fillna(np.nan) <= 0).astype(float).where(S.bldg_value.notna())
    S["public"] = S.public.fillna(False).astype(bool)
    S["water"] = False
    if water:
        S["water"] = np.isfinite(G.distance_to_polygons(S.bx.values, S.by.values, water, WATER_M))
    S["half_mile"] = S.dist_m <= 805
    return S[["case", "s", "s_lotmid", "bx", "by", "bx_lm", "by_lm", "in_reform_area", "acres_land", "public", "water", "half_mile",
              "chg", "pre", "post", "log_lv_acre", "log_acres", "bldg_age", "lot_vacant", "v_h14_vacancy_rate", "x", "y", "dist_m", "band"]]


# ------------------------------------------------------------------ estimation

def seg_ids(bx, by):
    return pd.Series(np.floor(bx / SEG).astype(np.int64) * 1_000_003 + np.floor(by / SEG).astype(np.int64)).to_numpy()


def select(S, h, dist="s", donut=0.0, half=False):
    """Lots within h of the line in usable segments (both sides present, public < 50% of either side, no water)."""
    s = S[dist].to_numpy()
    m = (np.abs(s) <= h) & (np.abs(s) >= donut)
    if half:
        m &= S.half_mile.to_numpy()
    T = S[m].copy()
    if not len(T):
        return T
    bx, by = (T.bx, T.by) if dist == "s" else (T.bx_lm, T.by_lm)
    T["seg"] = seg_ids(bx.to_numpy(), by.to_numpy())
    T["wa"] = T.acres_land * T.w
    T["wp"] = T.wa * T.public
    g = T.groupby(["seg", "in_reform_area"]).agg(n=("wa", "size"), ac=("wa", "sum"), pub=("wp", "sum"),
                                                  wat=("water", "max")).unstack("in_reform_area")
    ok = pd.Series(True, index=g.index)
    for side in (True, False):
        if ("n", side) not in g:
            return T.iloc[:0]
        ok &= g[("n", side)].fillna(0) > 0
        ok &= (g[("pub", side)].fillna(0) / g[("ac", side)].replace(0, np.nan)).fillna(1) < PUBLIC_MAX
        ok &= ~g[("wat", side)].fillna(False).astype(bool)
    return T[T.seg.isin(ok[ok].index)]


def seg_sums(T, y):
    T = T.assign(_n=T[y] * T.w, _a=T.acres_land * T.w)
    g = T.groupby(["seg", "in_reform_area"])[["_n", "_a"]].sum().unstack("in_reform_area").fillna(0)
    return np.c_[g[("_n", True)], g[("_a", True)], g[("_n", False)], g[("_a", False)]]


def diff_from(A):
    """A: [..., segs, 4] or weights-applied sums [..., 4] -> inside rate - outside rate per 100 acres."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return 100 * (A[..., 0] / A[..., 1] - A[..., 2] / A[..., 3])


def boot(T, y, rng):
    A = seg_sums(T, y)
    n = len(A)
    W = rng.multinomial(n, np.full(n, 1 / n), size=DRAWS)
    return diff_from(A.sum(0)), diff_from(W @ A)


def local_linear(T, h):
    out = []
    for side in (True, False):
        U = T[T.in_reform_area == side]
        if len(U) < 3:
            return np.nan
        w = U.acres_land * U.w * np.clip(1 - U.s.abs() / h, 0, None)
        yv = 100 * U.chg / U.acres_land
        Xm = np.c_[np.ones(len(U)), U.s]
        sw = np.sqrt(w.to_numpy())
        beta = np.linalg.lstsq(Xm * sw[:, None], yv.to_numpy() * sw, rcond=None)[0]
        out.append(beta[0])
    return out[0] - out[1]


def smd(T, col):
    a, b = T.loc[T.in_reform_area, col].dropna(), T.loc[~T.in_reform_area, col].dropna()
    if len(a) < 5 or len(b) < 5:
        return np.nan
    sd = np.sqrt((a.var() + b.var()) / 2)
    return (a.mean() - b.mean()) / sd if sd > 0 else np.nan


def bunching(S, rng):
    """Outside lots: (after near - after far) - (before near - before far), near = 0-100 m, far = 100-200 m outside."""
    O = S[(S.s < 0) & (S.s >= -200)].copy()
    if len(O) < 2 * MIN_LOTS:
        return np.nan, np.full(DRAWS, np.nan)
    O["seg"] = seg_ids(O.bx.to_numpy(), O.by.to_numpy())
    O = O[~O.water]
    O["near"] = O.s >= -100
    O["_a"] = O.acres_land * O.w
    O["_p"], O["_b"] = O.post * O.w, O.pre * O.w
    g = O.groupby(["seg", "near"])[["_p", "_b", "_a"]].sum().unstack("near").fillna(0)
    if ("_a", True) not in g or ("_a", False) not in g:
        return np.nan, np.full(DRAWS, np.nan)
    A = np.c_[g[("_p", True)], g[("_b", True)], g[("_a", True)], g[("_p", False)], g[("_b", False)], g[("_a", False)]]

    def stat(V):
        with np.errstate(divide="ignore", invalid="ignore"):
            return 100 * ((V[..., 0] - V[..., 1]) / V[..., 2] - (V[..., 3] - V[..., 4]) / V[..., 5])
    n = len(A)
    W = rng.multinomial(n, np.full(n, 1 / n), size=DRAWS)
    return stat(A.sum(0)), stat(W @ A)


def main() -> None:
    PL = places()
    SA = pd.read_csv(REFERENCE / "tod_station_area_effects_by_city.csv")
    SA = SA[SA.band == "0-1/4"].set_index("city").effect_per_100_acres
    sa_key = {"New York": "New York", "Philadelphia": "Philadelphia"}
    rows, draws = [], {}
    variants = {"main (91 m)": dict(h=H_MAIN), "46 m": dict(h=H_LO), "183 m": dict(h=H_HI),
                "donut 25 m (91 m)": dict(h=H_MAIN, donut=DONUT), "half mile only (91 m)": dict(h=H_MAIN, half=True),
                "lot-midway distance (91 m)": dict(h=H_MAIN, dist="s_lotmid")}
    for pi, (place, cases) in enumerate(PL.items()):
        water = water_polys(place)
        parts = [case_sample(c, place, water) for c in cases]
        S = pd.concat([p for p in parts if len(p)], ignore_index=True) if any(len(p) for p in parts) else pd.DataFrame()
        if not len(S):
            rows.append({"place": place, "variant": "main (91 m)", "status": "no district lots"}); continue
        k = S.groupby([S.x.round(1), S.y.round(1)]).case.transform("size") if len(cases) > 1 else 1
        S["w"] = 1.0 / k
        # district share of the 1/4-mile reform band's land (for the implied direct contribution)
        q = S  # within 200 m only; recompute from full tables below
        sh_num = sh_den = 0.0
        for c in cases:
            L = pd.read_parquet(OUT / f"lots_{c}.parquet", columns=["group", "band", "in_reform_area", "acres_land", "implausible"])
            L = L[(L.group == "reform") & (L.band == "0-1/4") & ~L.implausible.fillna(False).astype(bool)]
            sh_num += L.acres_land[L.in_reform_area.fillna(False).astype(bool)].sum(); sh_den += L.acres_land.sum()
        dshare = sh_num / sh_den if sh_den else np.nan
        sa = SA.get(sa_key.get(place, cases[0]), np.nan)
        rng = np.random.default_rng([SEED, pi])
        for vname, kw in variants.items():
            if vname.startswith("lot-midway") and cases[0] not in POLY_CASES:
                continue
            T = select(S, kw["h"], kw.get("dist", "s"), kw.get("donut", 0.0), kw.get("half", False))
            nin, nout = int(T.in_reform_area.sum()) if len(T) else 0, int((~T.in_reform_area).sum()) if len(T) else 0
            r = {"place": place, "variant": vname, "bandwidth_m": kw["h"], "lots_inside": nin, "lots_outside": nout,
                 "segments": int(T.seg.nunique()) if len(T) else 0,
                 "acres_inside": float((T.acres_land * T.w)[T.in_reform_area].sum()) if len(T) else 0.0,
                 "acres_outside": float((T.acres_land * T.w)[~T.in_reform_area].sum()) if len(T) else 0.0,
                 "distance_method": "polygon union boundary" if (cases[0] in POLY_CASES and kw.get("dist", "s") == "s") else "lot midway",
                 "water_layer": "TIGER 2024 area water" if water else "none on disk", "arterial_tag": "not done (no road layer on disk)"}
            if nin < MIN_LOTS or nout < MIN_LOTS:
                r["status"] = f"too few lots (< {MIN_LOTS} a side)"; rows.append(r); continue
            pt, dr = boot(T, "chg", rng)
            r.update({"status": "estimated", "edge_effect_per_100_acres_per_year": pt,
                      "low": np.nanpercentile(dr, 5), "high": np.nanpercentile(dr, 95),
                      "inside_change_rate": 100 * (T.chg * T.w)[T.in_reform_area].sum() / (T.acres_land * T.w)[T.in_reform_area].sum(),
                      "outside_change_rate": 100 * (T.chg * T.w)[~T.in_reform_area].sum() / (T.acres_land * T.w)[~T.in_reform_area].sum()})
            draws[(place, vname)] = dr
            if vname == "main (91 m)":
                pb, pdr = boot(T, "pre", rng)
                plo, phi = np.nanpercentile(pdr, [5, 95])
                r.update({"balance_pre_gap_per_100_acres": pb, "balance_pre_gap_low": plo, "balance_pre_gap_high": phi,
                          "balance_pass": bool(plo <= 0 <= phi), "local_linear_estimate": local_linear(T, kw["h"])})
                for col, lab in (("log_lv_acre", "smd_log_land_value_per_acre"), ("log_acres", "smd_log_lot_acres"),
                                 ("bldg_age", "smd_building_age"), ("lot_vacant", "smd_lot_vacant"), ("v_h14_vacancy_rate", "smd_tract_vacancy")):
                    r[lab] = smd(T, col)
                flags = [lab.removeprefix("smd_") for lab in r if lab.startswith("smd_") and pd.notna(r[lab]) and abs(r[lab]) > 0.25]
                r["imbalanced_traits"] = ";".join(flags)
                bs, bd = bunching(S, rng)
                r["bunching_stat"] = bs
                r["bunching_low"], r["bunching_high"] = (np.nanpercentile(bd, [5, 95]) if np.isfinite(bd).any() else (np.nan, np.nan))
                draws[(place, "bunching")] = bd
                r["station_area_quarter_effect_per_100_acres"] = sa
                r["district_share_of_quarter_band_acres"] = dshare
                r["implied_direct_per_100_band_acres"] = pt * dshare
                r["implied_direct_share_of_station_area"] = pt * dshare / sa if sa and np.isfinite(sa) else np.nan
            rows.append(r)
        print(place, "done", flush=True)
    R = pd.DataFrame(rows)
    main_ = R[(R.variant == "main (91 m)") & (R.status == "estimated")].set_index("place")
    passing = list(main_.index[main_.balance_pass.astype(bool)])
    pooled = []
    for vname in variants:
        V = R[(R.variant == vname) & (R.status == "estimated") & R.place.isin(passing)].set_index("place")
        if not len(V):
            continue
        v = V.edge_effect_per_100_acres_per_year
        dm = np.nanmean(np.stack([draws[(p, vname)] for p in V.index]), axis=0)
        loo = [v.drop(p).mean() for p in v.index] if len(v) > 1 else [np.nan]
        pooled.append({"place": f"POOLED ({len(V)} places passing balance)", "variant": vname, "status": "pooled",
                       "edge_effect_per_100_acres_per_year": v.mean(), "low": np.nanpercentile(dm, 5), "high": np.nanpercentile(dm, 95),
                       "loo_low": min(loo), "loo_high": max(loo), "places_in_pool": ";".join(V.index)})
    # all estimable places, ignoring the balance rule (shown, not used)
    V = main_
    dm = np.nanmean(np.stack([draws[(p, "main (91 m)")] for p in V.index]), axis=0)
    pooled.append({"place": f"ALL ESTIMABLE ({len(V)} places, balance rule ignored; not used)", "variant": "main (91 m)", "status": "pooled",
                   "edge_effect_per_100_acres_per_year": V.edge_effect_per_100_acres_per_year.mean(),
                   "low": np.nanpercentile(dm, 5), "high": np.nanpercentile(dm, 95)})
    # pooled bunching (passing places)
    bp = [p for p in passing if np.isfinite(main_.loc[p, "bunching_stat"])]
    if bp:
        bd = np.nanmean(np.stack([draws[(p, "bunching")] for p in bp]), axis=0)
        bst = main_.loc[bp, "bunching_stat"].mean()
        blo, bhi = np.nanpercentile(bd, [5, 95])
        pooled.append({"place": f"POOLED BUNCHING ({len(bp)} places)", "variant": "bunching check", "status": "pooled",
                       "bunching_stat": bst, "bunching_low": blo, "bunching_high": bhi,
                       "bunching_flag": bool(bhi < 0)})
    P = pd.DataFrame(pooled)
    # locked pass rule and Wisconsin floor
    pm = P[(P.variant == "main (91 m)") & P.place.str.startswith("POOLED (")]
    verdict = {}
    if len(pm):
        m = pm.iloc[0]
        get = lambda vn: P[(P.variant == vn) & P.place.str.startswith("POOLED (")].edge_effect_per_100_acres_per_year  # noqa: E731
        lo_ok = len(get("46 m")) and m.low <= get("46 m").iloc[0] <= m.high
        hi_ok = len(get("183 m")) and m.low <= get("183 m").iloc[0] <= m.high
        n_ok = len(passing) >= 5
        bflag = bool(P.loc[P.variant == "bunching check", "bunching_flag"].any()) if "bunching_flag" in P else False
        use = "donut 25 m (91 m)" if bflag else "main (91 m)"
        u = P[(P.variant == use) & P.place.str.startswith("POOLED (")].iloc[0]
        f = WI_SHARE * WI_QUARTER_ACRES / 100 * YEARS * RAMP
        verdict = {"place": "LOCKED RULE", "variant": f"floor uses: {use}", "status": "PASS" if (n_ok and lo_ok and hi_ok) else "FAIL",
                   "rule_places_passing_balance": len(passing), "rule_46m_inside_main_interval": bool(lo_ok),
                   "rule_183m_inside_main_interval": bool(hi_ok), "bunching_flag": bflag,
                   "edge_effect_per_100_acres_per_year": u.edge_effect_per_100_acres_per_year, "low": u.low, "high": u.high,
                   "wisconsin_direct_only_floor_2027_2031": u.edge_effect_per_100_acres_per_year * f,
                   "wisconsin_floor_low": u.low * f, "wisconsin_floor_high": u.high * f,
                   "wisconsin_floor_loo_low": u.get("loo_low", np.nan) * f, "wisconsin_floor_loo_high": u.get("loo_high", np.nan) * f}
    R = pd.concat([R, P, pd.DataFrame([verdict])], ignore_index=True)
    R.to_csv(REFERENCE / "tod_causal_edge_test.csv", index=False, float_format="%.4f")
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40)
    print(R[["place", "variant", "status", "lots_inside", "lots_outside", "segments", "edge_effect_per_100_acres_per_year", "low", "high"]].round(2).to_string(index=False))
    print(main_[["balance_pre_gap_per_100_acres", "balance_pre_gap_low", "balance_pre_gap_high", "balance_pass", "imbalanced_traits",
                 "smd_log_land_value_per_acre", "smd_log_lot_acres", "smd_building_age", "smd_lot_vacant", "smd_tract_vacancy",
                 "local_linear_estimate", "bunching_stat", "bunching_low", "bunching_high", "station_area_quarter_effect_per_100_acres",
                 "district_share_of_quarter_band_acres", "implied_direct_per_100_band_acres"]].round(2).to_string())
    print(verdict)


if __name__ == "__main__":
    main()
