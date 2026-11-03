"""Causal framework, Test 2 expansion: the edge test on more upzoning maps, a census-block version and two placebos
(docs/tod/CAUSAL_FRAMEWORK_PLAN.md, section "Test 2 expansion", locked 2026-11-02 before any count).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/run_tod_causal_edge_expand.py --part lots      # original 11, E1, E2
    OMP_NUM_THREADS=1 .venv/bin/python scripts/run_tod_causal_edge_expand.py --part placebo   # P1, P2
    OMP_NUM_THREADS=1 .venv/bin/python scripts/run_tod_causal_edge_expand.py --part census    # E3
    OMP_NUM_THREADS=1 .venv/bin/python scripts/run_tod_causal_edge_expand.py --part combine   # pools, floors, CSV

The first three parts are independent (run them side by side); each keeps its rows and bootstrap draws in
data/processed/tod_causal_edge_expand/ (local). "combine" writes reference/tod_causal_edge_expand.csv (summaries only:
no lot rows, block ids or parcel ids). The tool and its reference lines are not touched.
"""
from __future__ import annotations

import argparse
import pickle
import re
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
from missing_middleware.paths import PROCESSED, RAW, REFERENCE  # noqa: E402
import run_tod_station_model as M  # noqa: E402
import run_tod_causal_edge as E  # noqa: E402
from run_tod_causal_citywide import places, cfg  # noqa: E402

OUT = M.OUT
CAND = OUT / "candidates"
WORK = PROCESSED / "tod_causal_edge_expand"
SEED = E.SEED
F_WI = E.WI_SHARE * E.WI_QUARTER_ACRES / 100 * E.YEARS * E.RAMP
STREETS = 0.75                       # block land (with streets) -> lot land
VARIANTS = {"main (91 m)": dict(h=E.H_MAIN), "46 m": dict(h=E.H_LO), "183 m": dict(h=E.H_HI),
            "donut 25 m (91 m)": dict(h=E.H_MAIN, donut=E.DONUT), "half mile only (91 m)": dict(h=E.H_MAIN, half=True),
            "lot-midway distance (91 m)": dict(h=E.H_MAIN, dist="s_lotmid"),
            "without arterial segments (91 m)": dict(h=E.H_MAIN, no_art=True)}

NEW = {  # case: (label, group, distance mode, county FIPS for water/arterial layers)
    "bellevue_belred_2009": ("Bellevue BelRed 2009", "broad", "midway", ["53033"]),
    "honolulu_2017": ("Honolulu 2017", "broad", "poly", ["15003"]),
    "la_toc_2017": ("Los Angeles TOC 2017", "broad", "poly", ["06037"]),
    "san_diego_2021": ("San Diego 2021", "broad", "poly", ["06073"]),
    "chicago_2022": ("Chicago 2022", "broad", "radius", ["17031"]),
    "seattle_roosevelt_2012": ("Seattle Roosevelt 2012", "district", "midway", ["53033"]),
}


def save(name, obj):
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / f"{name}.pkl").write_bytes(pickle.dumps(obj))


def load(name):
    return pickle.loads((WORK / f"{name}.pkl").read_bytes())


# ------------------------------------------------------------------ lot samples

def before_halves(case: str, D: pd.DataFrame, src: Path) -> pd.DataFrame:
    """pre1, pre2: new homes a year on each lot in the first and second halves of the before window (plan addition b),
    from the events with event_windows' date rule; hand-check-corrected lots scaled to their corrected total."""
    D["pre1"] = D["pre2"] = np.nan
    b0, b1 = cfg(case)["before"]
    k = (b1 - b0 + 1) // 2
    f = src / f"events_{case}.parquet"
    if k < 1 or not f.exists():
        return D
    Ev = pd.read_parquet(f)
    if "match" in Ev:
        Ev = Ev[Ev["match"] != "completed_only_near_permit"]
    elif Ev.completed_year.notna().any() and Ev.permit_year.notna().any():
        Ev = Ev[Ev.completed_year.notna()]
    if M.county_of(case) == "king" and Ev.permit_year.isna().all():
        Ev = Ev.copy()
        Ev["permit_year"] = M.king_permit_years(case, Ev, src)
    yr = M.permit_year_est(Ev, M.county_of(case))
    tot = Ev[yr.between(b0, b1)].groupby("lot_index").homes.sum().reindex(D.index).fillna(0)
    h1 = Ev[yr.between(b0, b0 + k - 1)].groupby("lot_index").homes.sum().reindex(D.index).fillna(0)
    h2 = Ev[yr.between(b1 - k + 1, b1)].groupby("lot_index").homes.sum().reindex(D.index).fillna(0)
    fac = (D.homes_before_win / tot.replace(0, np.nan)).fillna(1.0).clip(lower=0)
    fac[(tot > 0) & (D.homes_before_win == 0)] = 0.0
    D["pre1"], D["pre2"] = h1 * fac / k, h2 * fac / k
    return D


def read_case(case: str, src: Path = OUT) -> pd.DataFrame:
    D = pd.read_parquet(src / f"lots_{case}.parquet", columns=E.COLS + ["stop_id"])
    if (src / f"events_{case}.parquet").exists():
        D = M.event_windows(case, D, "permit_est", src)
    D = before_halves(case, D, src)
    D = D[~D.implausible.fillna(False).astype(bool)].copy()
    D["in_reform_area"] = D.in_reform_area.fillna(False).astype(bool)
    return D


def finish(D: pd.DataFrame, samp: np.ndarray, case: str, main: tuple, alt: tuple, water: list, art) -> pd.DataFrame:
    """As run_tod_causal_edge.case_sample after the distances: main/alt = (d, bx, by, ux, uy) unsigned."""
    d, bx, by, ux, uy = main
    dm, mx, my, mux, muy = alt
    S = D.iloc[samp].copy()
    sign = np.where(S.in_reform_area.to_numpy(), 1.0, -1.0)
    S["s"], S["s_lotmid"] = sign * d, sign * dm
    S["bx"], S["by"], S["bx_lm"], S["by_lm"] = bx, by, mx, my
    S["art"] = E.arterial_flag(bx, by, ux, uy, art)
    S["art_lm"] = E.arterial_flag(mx, my, mux, muy, art)
    S = S[(S.s.abs() <= 400) | (S.s_lotmid.abs() <= 400)]
    yb, ya = M.windows(case)
    eff = cfg(case)["before"][1] + 1
    S["chg"] = S.homes_after_win / ya - S.homes_before_win / yb
    S["pre"] = S.homes_before_win / yb
    S["post"] = S.homes_after_win / ya
    S["ptr"] = S.pre2 - S.pre1
    S["case"] = case
    S["log_lv_acre"] = np.log(S.land_value.where(S.land_value > 0) / S.acres_land)
    S["log_acres"] = np.log(S.acres_land)
    S["bldg_age"] = (eff - S.year_built.where(S.year_built > 1700)).astype(float)
    S["lot_vacant"] = (S.bldg_value.fillna(np.nan) <= 0).astype(float).where(S.bldg_value.notna())
    S["public"] = S.public.fillna(False).astype(bool)
    S["water"] = False
    if water and len(S):
        S["water"] = np.isfinite(G.distance_to_polygons(S.bx.values, S.by.values, water, E.WATER_M))
    S["half_mile"] = S.dist_m <= 805
    return S[["case", "s", "s_lotmid", "bx", "by", "bx_lm", "by_lm", "in_reform_area", "acres_land", "public", "water", "half_mile",
              "art", "art_lm", "chg", "pre", "post", "ptr", "pre1", "pre2", "log_lv_acre", "log_acres", "bldg_age", "lot_vacant", "v_h14_vacancy_rate",
              "x", "y", "dist_m", "band"]]


def poly_dist(D, samp, polys):
    bp = E.boundary_points(polys)
    dd, j = cKDTree(bp[:, :2]).query(D[["x", "y"]].to_numpy()[samp])
    return dd, bp[j, 0], bp[j, 1], bp[j, 2], bp[j, 3]


def reform_polys(case: str) -> list:
    RP = RAW / "tod_radius_programs"
    if case == "honolulu_2017":
        fs = [X.read_vector(RP / "honolulu" / f, dst=E.CRS) for f in ("tod_zone_change_waipahu_tc.geojson", "tod_zone_change_west_loch.geojson")]
        return [g for f in fs for g in f.geometry if g]
    if case == "la_toc_2017":
        return [g for g in X.read_vector(RP / "la" / "toc_tiers_oct2017.geojson", dst=E.CRS).geometry if g]
    if case == "san_diego_2021":
        return [g for g in X.read_vector(RP / "san_diego" / "transit_priority_areas_sandag_2022.geojson", dst=E.CRS).geometry if g]
    if case == "seattle_roosevelt_2012":
        from station_cases import cluster_north as CN
        return list(CN.roosevelt_polys().geometry)
    raise KeyError(case)


def new_sample(case: str, water: list, art) -> pd.DataFrame:
    src = CAND if case == "seattle_roosevelt_2012" else OUT
    D = read_case(case, src)
    samp = np.flatnonzero(((D.group == "reform") & (D.acres_land > 0)).to_numpy())
    mid = E.lot_midway(D, samp)
    mode = NEW[case][2]
    if mode == "poly":
        main, alt = poly_dist(D, samp, reform_polys(case)), mid
    elif mode == "radius":
        from station_cases import chicago as CH
        st = CH.stations().set_index("stop_id")
        T = D.iloc[samp]
        sx, sy = st.x.reindex(T.stop_id).to_numpy(), st.y.reindex(T.stop_id).to_numpy()
        vx, vy = T.x.to_numpy() - sx, T.y.to_numpy() - sy
        n = np.hypot(vx, vy)
        chk = np.nanmax(np.abs(n - T.dist_m.to_numpy()))
        print(f"  chicago_2022: stop recovery max error {chk:.2f} m", flush=True)
        n[n == 0] = np.nan
        d = np.abs(805.0 - T.dist_m.to_numpy())
        main = (d, sx + vx / n * 805.0, sy + vy / n * 805.0, -vy / n, vx / n)
        alt = mid
    else:
        main = mid
        alt = poly_dist(D, samp, reform_polys(case)) if case == "seattle_roosevelt_2012" else mid
    return finish(D, samp, case, main, alt, water, art)


def orig_sample(case: str, water, art) -> pd.DataFrame:
    """run_tod_causal_edge.case_sample, plus the before-window halves."""
    D = read_case(case)
    if not D.in_reform_area.any() or D.in_reform_area.all():
        return pd.DataFrame()
    samp = np.flatnonzero(((D.group == "reform") & (D.acres_land > 0)).to_numpy())
    mid = E.lot_midway(D, samp)
    if case in E.POLY_CASES:
        from station_cases import cluster_west as W
        main = poly_dist(D, samp, W.reform_area(case))
    else:
        main = mid
    return finish(D, samp, case, main, mid, water, art)


# ------------------------------------------------------------------ one unit (exactly the inner loop of Test 2)

def run_unit(S: pd.DataFrame, rng, alt: str | None, sa=np.nan, dshare=np.nan, water_on=False, art_on=False, label="") -> tuple[list, dict]:
    rows, draws = [], {}
    for vname, kw in VARIANTS.items():
        if vname.startswith("lot-midway") and alt is None:
            continue
        T = E.select(S, kw["h"], kw.get("dist", "s"), kw.get("donut", 0.0), kw.get("half", False), kw.get("no_art", False))
        nin, nout = (int(T.in_reform_area.sum()), int((~T.in_reform_area).sum())) if len(T) else (0, 0)
        vlab = vname.replace("lot-midway distance", alt) if alt and vname.startswith("lot-midway") else vname
        r = {"variant": vlab, "bandwidth_m": kw["h"], "lots_inside": nin, "lots_outside": nout,
             "segments": int(T.seg.nunique()) if len(T) else 0,
             "acres_inside": float((T.acres_land * T.w)[T.in_reform_area].sum()) if len(T) else 0.0,
             "acres_outside": float((T.acres_land * T.w)[~T.in_reform_area].sum()) if len(T) else 0.0,
             "water_layer": "TIGER 2024 area water" if water_on else "none on disk",
             "arterial_tag": "TIGER 2020 S1100/S1200" if art_on else "no road file",
             "arterial_segment_share": float((T.groupby("seg")["art" if kw.get("dist", "s") == "s" else "art_lm"].mean() >= E.ART_SHARE).mean()) if len(T) else np.nan}
        if nin < E.MIN_LOTS or nout < E.MIN_LOTS:
            r["status"] = f"too few lots (< {E.MIN_LOTS} a side)"; rows.append(r); continue
        pt, dr = E.boot(T, "chg", rng)
        r.update({"status": "estimated", "edge_effect_per_100_acres_per_year": pt,
                  "low": np.nanpercentile(dr, 5), "high": np.nanpercentile(dr, 95),
                  "inside_change_rate": 100 * (T.chg * T.w)[T.in_reform_area].sum() / (T.acres_land * T.w)[T.in_reform_area].sum(),
                  "outside_change_rate": 100 * (T.chg * T.w)[~T.in_reform_area].sum() / (T.acres_land * T.w)[~T.in_reform_area].sum()})
        draws[vname] = dr
        if vname == "main (91 m)":
            pb, pdr = E.boot(T, "pre", rng)
            plo, phi = np.nanpercentile(pdr, [5, 95])
            r.update({"balance_pre_gap_per_100_acres": pb, "balance_pre_gap_low": plo, "balance_pre_gap_high": phi,
                      "balance_pass": bool(plo <= 0 <= phi), "local_linear_estimate": E.local_linear(T, kw["h"])})
            # (b) pre-trend: second half minus first half of the before window, inside minus outside (own seed stream,
            # so the Test 2 draws are unchanged)
            if T.ptr.notna().all() and T.pre1.notna().all():
                rng_pt = np.random.default_rng([SEED, 4242, len(T)])
                tb, tdr = E.boot(T.assign(ptr=T.ptr.fillna(0)), "ptr", rng_pt)
                tlo, thi = np.nanpercentile(tdr, [5, 95])
                r.update({"pretrend_gap_per_100_acres": tb, "pretrend_low": tlo, "pretrend_high": thi, "pretrend_pass": bool(tlo <= 0 <= thi)})
            else:
                r.update({"pretrend_pass": np.nan, "pretrend_note": "not testable (one-year before window or no events file)"})
            for col, lab in (("log_lv_acre", "smd_log_land_value_per_acre"), ("log_acres", "smd_log_lot_acres"),
                             ("bldg_age", "smd_building_age"), ("lot_vacant", "smd_lot_vacant"), ("v_h14_vacancy_rate", "smd_tract_vacancy")):
                r[lab] = E.smd(T, col)
            r["imbalanced_traits"] = ";".join(k.removeprefix("smd_") for k in list(r) if k.startswith("smd_") and pd.notna(r[k]) and abs(r[k]) > 0.25)
            Sb = S[(S.s >= -200)]
            bs, bd = E.bunching(Sb, rng)
            r["bunching_stat"] = bs
            r["bunching_low"], r["bunching_high"] = (np.nanpercentile(bd, [5, 95]) if np.isfinite(bd).any() else (np.nan, np.nan))
            draws["bunching"] = bd
            r["station_area_quarter_effect_per_100_acres"] = sa
            r["district_share_of_quarter_band_acres"] = dshare
            r["implied_direct_per_100_band_acres"] = pt * dshare
        rows.append(r)
    return rows, draws


def dshare_of(cases, src=OUT):
    num = den = 0.0
    for c in cases:
        s = CAND if c == "seattle_roosevelt_2012" else src
        L = pd.read_parquet(s / f"lots_{c}.parquet", columns=["group", "band", "in_reform_area", "acres_land", "implausible"])
        L = L[(L.group == "reform") & (L.band == "0-1/4") & ~L.implausible.fillna(False).astype(bool)]
        num += L.acres_land[L.in_reform_area.fillna(False).astype(bool)].sum(); den += L.acres_land.sum()
    return num / den if den else np.nan


def k_weight(S: pd.DataFrame, ncases: int) -> pd.DataFrame:
    S = S.copy()
    S["w"] = 1.0 / S.groupby([S.x.round(1), S.y.round(1)]).case.transform("size") if ncases > 1 else 1.0
    return S


# ------------------------------------------------------------------ part: lots (original 11, E1, E2)

def part_lots() -> None:
    PL = places()
    SA = pd.read_csv(REFERENCE / "tod_station_area_effects_by_city.csv")
    SA = SA[SA.band == "0-1/4"].set_index("city").effect_per_100_acres
    units = []          # dicts: unit, group, section, city, rows, draws
    for pi, (place, cases) in enumerate(PL.items()):
        water, art = E.water_polys(place), E.arterials(place)
        parts = {c: orig_sample(c, water, art) for c in cases}
        S = pd.concat([p for p in parts.values() if len(p)], ignore_index=True)
        S = S[(S.s.abs() <= 200) | (S.s_lotmid.abs() <= 200)]
        S = k_weight(S, len(cases))
        rng = np.random.default_rng([SEED, pi])
        rows, dr = run_unit(S, rng, "lot-midway distance" if cases[0] in E.POLY_CASES else None,
                            SA.get(place if place in ("New York", "Philadelphia") else cases[0], np.nan), dshare_of(cases),
                            bool(water), art is not None)
        units.append({"unit": place, "section": "original 11 (place level, as Test 2)", "group": "district", "city": place,
                      "rows": rows, "draws": dr})
        if place in ("New York", "Philadelphia"):              # E2: each rezoning its own unit
            for k, c in enumerate(cases):
                P = parts[c]
                if not len(P) or not P.in_reform_area.any():
                    units.append({"unit": c, "section": "E2 per rezoning", "group": "district", "city": place,
                                  "rows": [{"variant": "main (91 m)", "status": "no inside lots in the reform group"}], "draws": {}})
                    continue
                P = P[(P.s.abs() <= 200)].assign(w=1.0)
                rng = np.random.default_rng([SEED, 1000 + 200 * pi + k])
                rows, dr = run_unit(P, rng, None, np.nan, np.nan, bool(water), art is not None)
                units.append({"unit": c, "section": "E2 per rezoning", "group": "district", "city": place, "rows": rows, "draws": dr})
        print(place, "done", flush=True)
    for i, (case, (label, grp, mode, cty)) in enumerate(NEW.items()):
        E.WATER[label] = cty
        water, art = E.water_polys(label), E.arterials(label)
        S = new_sample(case, water, art)
        S = S[(S.s.abs() <= 200) | (S.s_lotmid.abs() <= 200)].assign(w=1.0)
        alt = {"poly": "lot-midway distance", "radius": "lot-midway distance"}.get(mode)
        if case == "seattle_roosevelt_2012":
            alt = "polygon distance"
        rng = np.random.default_rng([SEED, 20 + i])
        rows, dr = run_unit(S, rng, alt, SA.get(case, np.nan), dshare_of([case]), bool(water), art is not None)
        units.append({"unit": label, "section": "E1 new place", "group": grp, "city": label, "rows": rows, "draws": dr,
                      "distance": mode})
        print(label, "done", flush=True)
    save("lots", units)


# ------------------------------------------------------------------ part: placebo (P1, P2)

def stop_xy(D: pd.DataFrame) -> pd.DataFrame:
    """Each stop's location from its lots' points and distances (Gauss-Newton least squares)."""
    out = {}
    for sid, g in D.groupby("stop_id"):
        g = g.nsmallest(300, "dist_m")
        P, d = g[["x", "y"]].to_numpy(float), g.dist_m.to_numpy(float)
        if len(g) < 3:
            continue
        p = P[0].copy() + 1.0
        for _ in range(30):
            v = p - P
            n = np.hypot(v[:, 0], v[:, 1]); n[n == 0] = 1e-6
            J = v / n[:, None]
            r = n - d
            step = np.linalg.lstsq(J, -r, rcond=None)[0]
            p += step
            if np.hypot(*step) < 0.01:
                break
        out[sid] = (p[0], p[1], float(np.sqrt(np.mean((np.hypot(*(p - P).T) - d) ** 2))))
    return pd.DataFrame.from_dict(out, orient="index", columns=["sx", "sy", "rmse"])


def placebo_p1_case(case: str, place: str, rng, water, art) -> tuple[pd.DataFrame, dict]:
    D = read_case(case)
    if "stop_id" not in D:
        return pd.DataFrame(), {}
    R = D[D.group == "reform"]
    C = D[(D.group == "comparison")]
    rs = np.unique(R.stop_id[R.in_reform_area])
    info = {"case": case, "reform_stops_with_district": len(rs), "comparison_stops": int(C.stop_id.nunique())}
    if not len(rs) or not len(C):
        return pd.DataFrame(), info
    st = stop_xy(D[D.group.isin(["reform", "comparison"])])
    info["stop_fit_rmse_median_m"] = float(st.rmse.median())
    comps = np.array(sorted(set(C.stop_id) & set(st.index)))
    rs = np.array([r for r in rs if r in st.index])
    order = np.concatenate([rng.permutation(rs) for _ in range(int(np.ceil(len(comps) / len(rs))))])[:len(comps)]
    real_in = D.loc[D.in_reform_area, ["x", "y"]].to_numpy()
    dreal, _ = cKDTree(real_in).query(C[["x", "y"]].to_numpy())
    C = C[(dreal > 200) & ~C.in_reform_area.to_numpy()]
    fake = pd.Series(np.nan, index=C.index)
    Rg = {k: g for k, g in R.groupby("stop_id")}
    Cg = {k: g for k, g in C.groupby("stop_id")}
    for c, r in zip(comps, order):
        if c not in Cg or r not in Rg:
            continue
        src, tgt = Rg[r], Cg[c]
        off = np.array([st.sx[c] - st.sx[r], st.sy[c] - st.sy[r]])
        dd, j = cKDTree(src[["x", "y"]].to_numpy() + off).query(tgt[["x", "y"]].to_numpy())
        fake.loc[tgt.index] = np.where(dd <= 100, src.in_reform_area.to_numpy()[j].astype(float), np.nan)
    C = C[fake.notna()].copy()
    C["in_reform_area"] = fake[fake.notna()].astype(bool)
    C["group"] = "reform"
    info["placebo_lots_inside"] = int(C.in_reform_area.sum()); info["placebo_lots_outside"] = int((~C.in_reform_area).sum())
    C = C[C.acres_land > 0]
    if not C.in_reform_area.any() or C.in_reform_area.all():
        return pd.DataFrame(), info
    C = C.reset_index(drop=True)
    samp = np.arange(len(C))
    mid = E.lot_midway(C, samp)
    return finish(C, samp, case, mid, mid, water, art), info


SP_HIGH = r"^(RT2|RM\d|TN\d|TN3M|B\d|BC|OS)$"; SP_LOW = r"^(R[1-4]|RL|RLL|RT1)$"
SEA_HIGH = {"Lowrise Multi-Family", "High-Density Multi-Family", "Neighborhood Commercial", "Commercial", "Seattle Mixed", "Downtown"}
SEA_LOW = {"Neighborhood Residential"}
CLT_HIGH = r"^(R-\d+MF|UR-|MUDD|UMUD|B-\d|B-D|O-\d|NS|CC|TOD-|MX-)"; CLT_LOW = r"^(R-[3-8]\b(?!MF)|R-[3-8]\(|R-[3-8] |RE-)"
PDX_HIGH = r"^(R[123]|RH|RX|C[A-Z]|CN\d|CO\d|EX)$"; PDX_LOW = r"^(R2\.5|R5|R7|R10|R20|RF)$"


def tier(z: pd.Series, hi: str, lo: str) -> pd.Series:
    z = z.astype(str).str.strip()
    return pd.Series(np.where(z.str.contains(hi, regex=True), 1.0, np.where(z.str.contains(lo, regex=True), 0.0, np.nan)), index=z.index)


def zone_at(x, y, layer: pd.DataFrame, col: str) -> pd.Series:
    k = X.first_within(x, y, list(layer.geometry))
    return pd.Series(np.where(k >= 0, layer[col].astype(str).values[np.maximum(k, 0)], None), dtype=object)


def placebo_p2_case(case: str, place: str, water, art) -> tuple[pd.DataFrame, dict]:
    D = read_case(case)
    C = D[(D.group == "comparison") & (D.acres_land > 0)].copy().reset_index(drop=True)
    x, y = C.x.to_numpy(), C.y.to_numpy()
    b0, a1 = cfg(case)["before"][0], cfg(case)["after"][1]
    Z = RAW / "tod_cases"
    note = ""
    if case == "stpaul_2011":
        z0 = zone_at(x, y, X.read_vector(Z / "stpaul" / "zoning_2010_11.geojson", dst=E.CRS), "Zoning")
        z1 = zone_at(x, y, X.read_vector(Z / "stpaul" / "zoning_2017_11.geojson", dst=E.CRS), "Zoning")
        same = (z0 == z1) & z0.notna()
        t = tier(z0, SP_HIGH, SP_LOW)
        note = "Nov 2010 and Nov 2017 layers, same zone"
    elif case.startswith("seattle"):
        s = X.read_vector(Z / "seattle" / "zoning_current.geojson", dst=E.CRS)
        yrs = s.ZONINGHISTORY.fillna("").apply(lambda h: [int(m) for m in re.findall(r"\d{2}/\d{2}/(\d{4})", str(h))])
        s["changed"] = [any(b0 <= v <= a1 for v in ys) for ys in yrs]
        k = X.first_within(x, y, list(s.geometry))
        same = pd.Series((k >= 0) & ~s.changed.to_numpy()[np.maximum(k, 0)])
        cat = pd.Series(np.where(k >= 0, s.CATEGORY_DESC.astype(str).to_numpy()[np.maximum(k, 0)], ""))
        t = pd.Series(np.where(cat.isin(SEA_HIGH), 1.0, np.where(cat.isin(SEA_LOW), 0.0, np.nan)))
        note = f"current layer, no ordinance dated {b0}-{a1} in ZONINGHISTORY"
    elif case == "charlotte_2019":
        z = X.read_vector(Z / "charlotte" / "pre_udo_zoning.geojson", dst=E.CRS)
        ry = pd.to_datetime(z.RezoneDate, unit="ms", errors="coerce").dt.year
        k = X.first_within(x, y, list(z.geometry))
        zz = pd.Series(np.where(k >= 0, z.ZoneDes.astype(str).to_numpy()[np.maximum(k, 0)], None), dtype=object)
        ryl = np.where(k >= 0, ry.to_numpy()[np.maximum(k, 0)], np.nan)
        h = X.read_vector(Z / "charlotte" / "rezoning_history.geojson", dst=E.CRS)
        hy = pd.to_datetime(h.Approved, unit="ms", errors="coerce").dt.year
        hw = h[hy.between(b0, a1)]
        inpet = X.first_within(x, y, [g for g in hw.geometry if g]) >= 0 if len(hw) else np.zeros(len(x), bool)
        same = pd.Series(zz.notna().to_numpy() & ~(ryl >= b0) & ~inpet)
        t = tier(zz.fillna(""), CLT_HIGH, CLT_LOW)
        note = f"pre-UDO layer, last rezone before {b0}, no petition approved {b0}-{a1}; UDO translation June 2023 in after window (flag)"
    elif case == "portland_2020":
        N = RAW / "tod_new_cities" / "portland"
        z0 = zone_at(x, y, X.read_vector(N / "zoning_pre_2018_05_24.geojson", dst=E.CRS), "ZONE")
        z1 = zone_at(x, y, X.read_vector(N / "zoning_2020_03_01.geojson", dst=E.CRS), "ZONE")
        same = (z0 == z1) & z0.notna()
        t = tier(z0.fillna(""), PDX_HIGH, PDX_LOW)
        note = "May 2018 and Mar 2020 layers, same zone; NOT POOLED (2021 Residential Infill Project in the after window)"
    else:
        return pd.DataFrame(), {}
    keep = same.to_numpy() & t.notna().to_numpy()
    info = {"case": case, "zoning_source": note, "comparison_lots": len(C), "unchanged_tiered_lots": int(keep.sum()),
            "high_tier_lots": int((t.to_numpy() == 1)[keep].sum())}
    C = C[keep].reset_index(drop=True)
    C["in_reform_area"] = t.to_numpy()[keep] == 1
    C["group"] = "reform"
    if not C.in_reform_area.any() or C.in_reform_area.all():
        return pd.DataFrame(), info
    samp = np.arange(len(C))
    mid = E.lot_midway(C, samp)
    return finish(C, samp, case, mid, mid, water, art), info


P2_PLACES = {"Saint Paul 2011": "stpaul_2011", "Seattle Othello 2012": "seattle_othello_2012",
             "Seattle Mount Baker 2014": "seattle_mount_baker_2014", "Charlotte 2019": "charlotte_2019", "Portland 2020": "portland_2020"}


def part_placebo() -> None:
    PL = places()
    units, infos = [], []
    for pi, (place, cases) in enumerate(PL.items()):
        ck = WORK / f"placebo_place_{pi}.pkl"                  # per-place checkpoint (a rerun skips finished places)
        if ck.exists():
            u_, i_ = pickle.loads(ck.read_bytes())
            units += u_; infos += i_
            continue
        n0, m0 = len(units), len(infos)
        water, art = E.water_polys(place), E.arterials(place)
        rng = np.random.default_rng([20261107, pi])
        parts = []
        for c in cases:
            S, info = placebo_p1_case(c, place, rng, water, art)
            infos.append({"placebo": "P1", "place": place, **info})
            if len(S):
                parts.append(S)
        if parts:
            S = pd.concat(parts, ignore_index=True)
            S = S[S.s.abs() <= 200]
            S = k_weight(S, len(cases))
            rows, dr = run_unit(S, np.random.default_rng([SEED, 500 + pi]), None, water_on=bool(water), art_on=art is not None)
        else:
            rows, dr = [{"variant": "main (91 m)", "status": "no placebo district"}], {}
        units.append({"unit": place, "section": "P1 placebo (fake district on comparison stops)", "group": "placebo P1", "city": place,
                      "rows": rows, "draws": dr})
        if place in P2_PLACES:
            S, info = placebo_p2_case(P2_PLACES[place], place, water, art)
            infos.append({"placebo": "P2", "place": place, **info})
            if len(S):
                S = S[S.s.abs() <= 200].assign(w=1.0)
                rows, dr = run_unit(S, np.random.default_rng([SEED, 600 + pi]), None, water_on=bool(water), art_on=art is not None)
            else:
                rows, dr = [{"variant": "main (91 m)", "status": "no unchanged zoning line"}], {}
            units.append({"unit": place, "section": "P2 placebo (unchanged zoning line near comparison stops)", "group": "placebo P2",
                          "city": place, "rows": rows, "draws": dr, "pooled": place != "Portland 2020"})
        ck.write_bytes(pickle.dumps((units[n0:], infos[m0:])))
        print(place, "placebo done", flush=True)
    save("placebo", {"units": units, "infos": infos})


# ------------------------------------------------------------------ part: census blocks (E3)

H_B, H_B_LO, H_B_HI, MIN_BLOCKS, CSEED = 150.0, 100.0, 300.0, 10, 20261106


def census_units():
    """(case, state, adopted, mode, polys, inside Region, excluded Region or None) for the 21 census-set reforms
    (+ New York 2013, which had no measurable blocks), areas as run_tod_census2000.census_set_areas."""
    from scripts import run_tod_census_cases as R
    from scripts.run_tod_census_share import slc_boundary
    from missing_middleware import geom_extra_tod as XT
    out = []
    geoms = {c: R.boundary(c) for c in R.NEW_CASES}
    geoms["salt_lake_city_tsa_2010"] = slc_boundary()
    every = XT.Polygons([f for g in geoms.values() for f in g[1]])
    adopted = {"jersey_city_journal_square_2010": 2010, "milpitas_tasp_2008": 2008, "phoenix_wu_2015_2016": 2015,
               "bellevue_belred_2009": 2009, "austin_tod_station_plans": 2007, "tysons_2010": 2010, "salt_lake_city_tsa_2010": 2010}
    for c, (t, ex) in geoms.items():
        st = "49" if c == "salt_lake_city_tsa_2010" else R.NEW_CASES[c][0]
        out.append((c, st, adopted[c], "poly", t, XT.Polygons(t), every))
    cases = {"stpaul_green_line_2011": ("27", 2011), "seattle_nbh_othello_2012": ("53", 2012), "seattle_mount_baker_2014": ("53", 2014),
             "la_warner_center_2013": ("06", 2013), "la_cornfield_arroyo_seco_2013": ("06", 2013), "chicago_tod_2013_2015": ("17", 2013),
             "philadelphia_2012_remapping": ("42", 2012)}
    for c, (st, yr) in cases.items():
        mem = pickle.loads((PROCESSED / "tod_net_effect" / f"areas_{c}.pkl").read_bytes())
        u = [f for m in mem for f in R.member_polys(m, "upzoned_union")]
        out.append((c, st, yr, "midway", u, R.union(u), None))
    for m in pickle.loads((PROCESSED / "tod_net_effect" / "areas_nyc_pooled_2003_2013.pkl").read_bytes()):
        if 2008 <= m["effective_year"] <= 2013:
            u = R.member_polys(m, "upzoned_union")
            out.append((f"nyc_{m.get('id')}", "36", m["effective_year"], "midway", u, R.union(u), None))
    z = R.layer(RAW / "tod_cases" / "seattle" / "zoning_current.geojson")
    rv = R.valid(z[z["ZONINGHISTORY"].astype(str).str.contains("ORD123816")])
    out.append(("seattle_roosevelt_2012", "53", 2012, "poly", rv, XT.Polygons(rv), None))
    return out


_PTS: dict = {}


def pts(st: str, year: int) -> pd.DataFrame:
    from scripts import run_tod_census_cases as R
    from scripts import run_tod_census2000 as C2
    if (st, year) not in _PTS:
        _PTS[(st, year)] = C2.points_2000(st) if year == 2000 else R.block_points(st, year)
    return _PTS[(st, year)]


def block_sample(st, mode, polys, inside, excl) -> pd.DataFrame:
    b = X.feature_bounds(polys)
    x0, y0 = np.nanmin(b[:, 0]) - 1500, np.nanmin(b[:, 1]) - 1500
    x1, y1 = np.nanmax(b[:, 2]) + 1500, np.nanmax(b[:, 3]) + 1500
    bp = E.boundary_points(polys) if mode == "poly" else None
    out = []
    for yr in (2000, 2010, 2020):
        p = pts(st, yr)
        p = p[p.x.between(x0, x1) & p.y.between(y0, y1)].copy()
        if not len(p):
            continue
        xy = p[["x", "y"]].to_numpy(float)
        ins = inside.contains(xy[:, 0], xy[:, 1])
        if excl is not None:
            drop = ~ins & excl.contains(xy[:, 0], xy[:, 1])
            p, xy, ins = p[~drop], xy[~drop], ins[~drop]
        p["inside"] = ins
        if mode == "poly":
            d, j = cKDTree(bp[:, :2]).query(xy)
            p["bx"], p["by"] = bp[j, 0], bp[j, 1]
        else:
            d = np.full(len(p), np.inf); bx = np.full(len(p), np.nan); by = bx.copy()
            for side in (True, False):
                m, o = ins == side, ins != side
                if m.any() and o.any():
                    dd, j = cKDTree(xy[o]).query(xy[m])
                    d[m] = dd / 2
                    bx[m] = (xy[m, 0] + xy[o][j, 0]) / 2; by[m] = (xy[m, 1] + xy[o][j, 1]) / 2
            p["bx"], p["by"] = bx, by
        p["s"] = np.where(ins, d, -d)
        p["year"] = yr
        out.append(p[np.abs(p.s) <= 2 * H_B_HI])
    if not out:
        return pd.DataFrame()
    B = pd.concat(out, ignore_index=True)
    B["seg"] = E.seg_ids(B.bx.to_numpy(), B.by.to_numpy())
    return B


def block_matrix(B, h, y0, y1, near=None):
    """Per segment: [H0 in, H1 in, L0 in, L1 in, H0 out, H1 out, L0 out, L1 out] for segments with both sides in both
    vintages; and the block counts a side. near: (lo, hi) on s for the outside-only bunching split."""
    T = B[(B.s.abs() <= h) & B.year.isin([y0, y1])] if near is None else B[B.year.isin([y0, y1]) & (B.s < 0) & (B.s >= -2 * h)]
    if not len(T):
        return np.zeros((0, 8)), (0, 0)
    side = T.inside if near is None else (T.s >= -h)
    g = T.assign(side=side.to_numpy()).groupby(["seg", "side", "year"]).agg(H=("homes", "sum"), L=("land", "sum"), n=("homes", "size"))
    g = g.unstack(["side", "year"])
    cols = [(True, y0), (True, y1), (False, y0), (False, y1)]
    for c in cols:
        for k in ("H", "L", "n"):
            if (k, *c) not in g:
                g[(k, *c)] = np.nan
    ok = np.ones(len(g), bool)
    for c in cols:
        ok &= g[("n", *c)].fillna(0).to_numpy() > 0
    g = g[ok]
    A = np.c_[g[("H", True, y0)], g[("H", True, y1)], g[("L", True, y0)], g[("L", True, y1)],
              g[("H", False, y0)], g[("H", False, y1)], g[("L", False, y0)], g[("L", False, y1)]].astype(float)
    nin = int(min(g[("n", True, y0)].sum(), g[("n", True, y1)].sum())) if len(g) else 0
    nout = int(min(g[("n", False, y0)].sum(), g[("n", False, y1)].sum())) if len(g) else 0
    return A, (nin, nout)


def bstat(V):
    """Inside minus outside net homes per acre per decade."""
    with np.errstate(divide="ignore", invalid="ignore"):
        ri = (V[..., 1] - V[..., 0]) / ((V[..., 2] + V[..., 3]) / 2 / 4046.8564)
        ro = (V[..., 5] - V[..., 4]) / ((V[..., 6] + V[..., 7]) / 2 / 4046.8564)
    return ri - ro


def bboot(A, rng, draws=E.DRAWS):
    n = len(A)
    W = rng.multinomial(n, np.full(n, 1 / n), size=draws)
    return bstat(A.sum(0)), bstat(W @ A)


def part_census() -> None:
    units = []
    for i, (c, st, yr, mode, polys, inside, excl) in enumerate(census_units()):
        rng = np.random.default_rng([CSEED, i])
        B = block_sample(st, mode, polys, inside, excl)
        rows, draws = [], {}
        base = {"distance": "polygon boundary" if mode == "poly" else "block midway (upzoned lots' union)", "adopted": yr,
                "pre_decade_partly_after_adoption": yr < 2010}
        if not len(B):
            units.append({"unit": c, "section": "E3 census blocks", "group": "census", "city": c, "rows": [{**base, "variant": "main (150 m)", "status": "no blocks"}], "draws": {}})
            continue
        for vname, h in (("main (150 m)", H_B), ("100 m", H_B_LO), ("300 m", H_B_HI)):
            A, (nin, nout) = block_matrix(B, h, 2010, 2020)
            r = {**base, "variant": vname, "bandwidth_m": h, "blocks_inside": nin, "blocks_outside": nout, "segments": len(A)}
            if nin < MIN_BLOCKS or nout < MIN_BLOCKS:
                r["status"] = f"too few blocks (< {MIN_BLOCKS} a side)"; rows.append(r); continue
            pt, dr = bboot(A, rng)
            r.update({"status": "estimated", "net_homes_per_acre_decade": pt, "low_per_acre_decade": np.nanpercentile(dr, 5),
                      "high_per_acre_decade": np.nanpercentile(dr, 95),
                      "edge_effect_per_100_acres_per_year": pt * 10, "low": np.nanpercentile(dr, 5) * 10, "high": np.nanpercentile(dr, 95) * 10})
            draws[vname] = dr * 10
            if vname.startswith("main"):
                A0, (n0i, n0o) = block_matrix(B, h, 2000, 2010)
                r["blocks_inside_2000_2010"], r["blocks_outside_2000_2010"] = n0i, n0o
                if n0i >= MIN_BLOCKS and n0o >= MIN_BLOCKS:
                    pb, pdr = bboot(A0, rng)
                    plo, phi = np.nanpercentile(pdr, [5, 95])
                    r.update({"balance_pre_gap_per_100_acres": pb * 10, "balance_pre_gap_low": plo * 10, "balance_pre_gap_high": phi * 10,
                              "balance_pass": bool(plo <= 0 <= phi)})
                    # change in change on segments usable in all three vintages
                    T = B[(B.s.abs() <= h)]
                    g = T.groupby(["seg", "inside", "year"]).agg(H=("homes", "sum"), L=("land", "sum")).unstack(["inside", "year"])
                    need = [(k, s_, y) for k in ("H", "L") for s_ in (True, False) for y in (2000, 2010, 2020)]
                    if all(n in g for n in need):
                        g = g.dropna(subset=[n for n in need if n[0] == "L"])
                        A1 = np.c_[[g[(k, s_, y)] for s_ in (True, False) for (k, y) in (("H", 2010), ("H", 2020), ("L", 2010), ("L", 2020))]].T.astype(float)
                        A0j = np.c_[[g[(k, s_, y)] for s_ in (True, False) for (k, y) in (("H", 2000), ("H", 2010), ("L", 2000), ("L", 2010))]].T.astype(float)
                        n = len(g)
                        if n >= 3:
                            W = rng.multinomial(n, np.full(n, 1 / n), size=E.DRAWS)
                            cic = bstat(W @ A1) - bstat(W @ A0j)
                            r.update({"change_in_change_per_100_acres": (bstat(A1.sum(0)) - bstat(A0j.sum(0))) * 10,
                                      "change_in_change_low": np.nanpercentile(cic, 5) * 10, "change_in_change_high": np.nanpercentile(cic, 95) * 10})
                else:
                    r["balance_pass"] = np.nan
                    r["balance_note"] = "too few 2000-2010 blocks"
                # bunching: outside 0-150 vs 150-300, 2010-20 gap minus 2000-10 gap
                Bn1, _ = block_matrix(B, h, 2010, 2020, near=True)
                Bn0, _ = block_matrix(B, h, 2000, 2010, near=True)
                if len(Bn1) >= 3 and len(Bn0) >= 3:
                    r["bunching_stat"] = (bstat(Bn1.sum(0)) - bstat(Bn0.sum(0))) * 10
                r["pre_density_inside_2010_homes_per_acre"] = float(B[(B.year == 2010) & B.inside & (B.s <= h)].homes.sum() /
                                                                   (B[(B.year == 2010) & B.inside & (B.s <= h)].land.sum() / 4046.8564 or np.nan))
            rows.append(r)
        units.append({"unit": c, "section": "E3 census blocks", "group": "census", "city": "New York (census)" if c.startswith("nyc_") else c,
                      "rows": rows, "draws": draws})
        print(c, "census done", flush=True)
    save("census", units)


# ------------------------------------------------------------------ part: combine

def main_row(u, v="main (91 m)"):
    return next((r for r in u["rows"] if r.get("variant") == v), {})


def pool(entries: dict, v: str = "main (91 m)") -> dict:
    """entries: name -> (estimate, draws). Equal-weight mean, 90% interval of the mean of draws, leave one out."""
    entries = {k: e for k, e in entries.items() if e is not None and np.isfinite(e[0])}
    if not entries:
        return {}
    est = np.array([e[0] for e in entries.values()])
    dm = np.nanmean(np.stack([e[1] for e in entries.values()]), axis=0)
    loo = [np.delete(est, i).mean() for i in range(len(est))] if len(est) > 1 else [np.nan]
    return {"edge_effect_per_100_acres_per_year": est.mean(), "low": np.nanpercentile(dm, 5), "high": np.nanpercentile(dm, 95),
            "loo_low": min(loo), "loo_high": max(loo), "n_units": len(est), "units_in_pool": ";".join(entries), "_draws": dm}


def est_of(u, v, scale=1.0):
    r = main_row(u, v)
    if r.get("status") != "estimated" or v not in u["draws"]:
        return None
    return (r["edge_effect_per_100_acres_per_year"] * scale, u["draws"][v] * scale)




FILTERS = {"a": "level balance (a)", "b": "pre-trend (b)", "none": "no filter"}


def passes(u, v_main, filt="a"):
    r = main_row(u, v_main)
    if r.get("status") != "estimated":
        return False
    if filt == "none":
        return True
    k = "balance_pass" if filt == "a" else "pretrend_pass"
    return r.get(k) is True or r.get(k) is np.True_


def city_unit(members: list, name: str, filt: str) -> dict | None:
    """Pool a city's passing rezonings into one unit (per variant, mean of estimates and draws)."""
    ok = [u for u in members if passes(u, "main (91 m)", filt)]
    if not ok:
        return None
    rows, draws = [], {}
    for v in VARIANTS:
        es = [est_of(u, v) for u in ok]
        es = [e for e in es if e is not None]
        if not es:
            continue
        draws[v] = np.nanmean(np.stack([e[1] for e in es]), axis=0)
        r = {"variant": v, "status": "estimated", "edge_effect_per_100_acres_per_year": float(np.mean([e[0] for e in es])),
             "n_rezonings": len(es), "low": np.nanpercentile(draws[v], 5), "high": np.nanpercentile(draws[v], 95)}
        if v == "main (91 m)":
            r["balance_pass"] = r["pretrend_pass"] = True          # passes the filter it was built under
            bs = [(main_row(u).get("bunching_stat"), u["draws"].get("bunching")) for u in ok]
            bs = [b for b in bs if b[0] is not None and np.isfinite(b[0]) and b[1] is not None]
            if bs:
                r["bunching_stat"] = float(np.mean([b[0] for b in bs]))
                draws["bunching"] = np.nanmean(np.stack([b[1] for b in bs]), axis=0)
        rows.append(r)
    return {"unit": f"{name} (city pool, {len(ok)} rezonings, filter {filt})", "section": f"E2 city pool, filter {FILTERS[filt]}",
            "group": "district", "city": name, "rows": rows, "draws": draws}


def group_pool(units: list, label: str, filt: str, vmain="main (91 m)", vlo="46 m", vhi="183 m", bunch=True):
    use = [u for u in units if passes(u, vmain, filt)]
    out, pm = [], {}
    lab = f"{label} [filter: {FILTERS[filt]}]"
    for v in (vmain, vlo, vhi) + (("donut 25 m (91 m)",) if vmain == "main (91 m)" else ()):
        # donut: units without a donut estimate (census blocks) enter with their main estimate
        P = pool({u["unit"]: est_of(u, vmain if (v.startswith("donut") and v not in u["draws"]) else v) for u in use})
        if P:
            pm[v] = P
            out.append({"unit": f"POOLED {lab}", "variant": v, "status": "pooled", "filter": FILTERS[filt],
                        **{k: x for k, x in P.items() if k != "_draws"}})
    bl = [u for u in use if "bunching" in u["draws"] and np.isfinite(main_row(u, vmain).get("bunching_stat", np.nan))]
    bflag = False
    if bunch and bl:
        bd = np.nanmean(np.stack([u["draws"]["bunching"] for u in bl]), axis=0)
        blo, bhi = np.nanpercentile(bd, [5, 95])
        bflag = bool(bhi < 0)
        out.append({"unit": f"POOLED {lab}", "variant": "bunching check", "status": "pooled", "filter": FILTERS[filt], "n_units": len(bl),
                    "bunching_stat": float(np.mean([main_row(u, vmain)["bunching_stat"] for u in bl])), "bunching_low": blo,
                    "bunching_high": bhi, "bunching_flag": bflag})
    if vmain in pm:
        m = pm[vmain]
        lo_ok = vlo in pm and m["low"] <= pm[vlo]["edge_effect_per_100_acres_per_year"] <= m["high"]
        hi_ok = vhi in pm and m["low"] <= pm[vhi]["edge_effect_per_100_acres_per_year"] <= m["high"]
        out.append({"unit": f"RULE {lab}", "variant": f"{vlo} and {vhi} inside main interval; >= 5 units", "filter": FILTERS[filt],
                    "status": "PASS" if (m["n_units"] >= 5 and lo_ok and hi_ok) else "FAIL", "n_units": m["n_units"],
                    "rule_low_bw_inside": bool(lo_ok), "rule_high_bw_inside": bool(hi_ok), "bunching_flag": bflag})
    return out, pm, bflag


def floor_row(label, pm, bflag, filt, vmain="main (91 m)"):
    use = "donut 25 m (91 m)" if bflag and "donut 25 m (91 m)" in pm else vmain
    if use not in pm:
        return None
    p = pm[use]
    return {"unit": f"WISCONSIN FLOOR {label} [filter: {FILTERS[filt]}]", "variant": f"uses {use}", "status": "floor", "filter": FILTERS[filt],
            "n_units": p["n_units"], "edge_effect_per_100_acres_per_year": p["edge_effect_per_100_acres_per_year"], "low": p["low"],
            "high": p["high"], "loo_low": p["loo_low"], "loo_high": p["loo_high"],
            "wisconsin_direct_only_floor_2027_2031": p["edge_effect_per_100_acres_per_year"] * F_WI,
            "wisconsin_floor_low": p["low"] * F_WI, "wisconsin_floor_high": p["high"] * F_WI,
            "wisconsin_floor_loo_low": p["loo_low"] * F_WI, "wisconsin_floor_loo_high": p["loo_high"] * F_WI,
            "units_in_pool": p["units_in_pool"], "_draws": p["_draws"]}


def as_lot(u):
    """A census unit in lot-test variant names, rates ÷ 0.75 (block land -> lot land)."""
    m = {"main (91 m)": "main (150 m)", "46 m": "100 m", "183 m": "300 m"}
    rows_ = []
    for lv, cv in m.items():
        r = dict(main_row(u, cv)); r["variant"] = lv
        if r.get("status") == "estimated":
            for k in ("edge_effect_per_100_acres_per_year", "low", "high"):
                r[k] = r[k] / STREETS
        rows_.append(r)
    return {**u, "rows": rows_, "draws": {lv: u["draws"][cv] / STREETS for lv, cv in m.items() if cv in u["draws"]}}


def census_ny_pool(Cn, filt):
    nyp = [u for u in Cn if u["unit"].startswith("nyc_") and passes(u, "main (150 m)", filt)]
    if not nyp:
        return None
    rr, d = [], {}
    for v in ("main (150 m)", "100 m", "300 m"):
        us = [u for u in nyp if v in u["draws"]]
        if not us:
            continue
        d[v] = np.nanmean(np.stack([u["draws"][v] for u in us]), axis=0)
        rr.append({"variant": v, "status": "estimated", "edge_effect_per_100_acres_per_year": float(np.mean([main_row(u, v)["edge_effect_per_100_acres_per_year"] for u in us])),
                   "low": np.nanpercentile(d[v], 5), "high": np.nanpercentile(d[v], 95), "balance_pass": True, "pretrend_pass": True})
    return {"unit": f"New York census (pool of {len(nyp)} rezonings, filter {filt})", "section": f"E3 census city pool, filter {FILTERS[filt]}",
            "group": "census", "city": "New York (census)", "rows": rr, "draws": d}


def part_combine() -> None:
    L, Pb, Cn = load("lots"), load("placebo"), load("census")
    rows = []

    def emit(u):
        for r in u["rows"]:
            rows.append({"section": u["section"], "group": u["group"], "unit": u["unit"], "city": u.get("city"), **r})

    for u in L + Pb["units"] + Cn:
        emit(u)
    orig = [u for u in L if u["section"].startswith("original")]
    e2 = [u for u in L if u["section"] == "E2 per rezoning"]
    e1 = [u for u in L if u["section"] == "E1 new place"]
    rv = [u for u in e1 if u["group"] == "district"]
    broad = [u for u in e1 if u["group"] == "broad"]
    others9 = [u for u in orig if u["unit"] not in ("New York", "Philadelphia")]
    for city in ("New York", "Philadelphia"):
        m = [u for u in e2 if u["city"] == city]
        est = [u for u in m if main_row(u).get("status") == "estimated"]
        rows.append({"section": "E2 per rezoning", "unit": f"COUNT {city}", "status": "count", "n_rezonings_on_disk": len(m),
                     "n_estimable": len(est), "n_passing_balance_a": sum(passes(u, "main (91 m)", "a") for u in est),
                     "n_passing_pretrend_b": sum(passes(u, "main (91 m)", "b") for u in est),
                     "n_passing_both": sum(passes(u, "main (91 m)", "a") and passes(u, "main (91 m)", "b") for u in est)})
    cest = [u for u in Cn if main_row(u, "main (150 m)").get("status") == "estimated"]
    rows.append({"section": "E3 census blocks", "unit": "COUNT census reforms", "status": "count", "n_rezonings_on_disk": len(Cn),
                 "n_estimable": len(cest), "n_passing_balance_a": sum(passes(u, "main (150 m)", "a") for u in cest),
                 "n_passing_pretrend_b": 0})
    out, floors = [], []
    p1 = [u for u in Pb["units"] if u["group"] == "placebo P1"]
    p2 = [u for u in Pb["units"] if u["group"] == "placebo P2" and u.get("pooled", True)]
    for filt in FILTERS:
        cityp = [city_unit([u for u in e2 if u["city"] == c], c, filt) for c in ("New York", "Philadelphia")]
        cityp = [u for u in cityp if u]
        for u in cityp:
            emit(u)
        oa, pa, ba = group_pool(orig, "(a) original 11 places, place level", filt)
        dist_b = others9 + cityp + rv
        ob, pb_, bb = group_pool(dist_b, "(b) district-type, NY/PHL city pools", filt)
        ob2, pb2, bb2 = group_pool(others9 + e2 + rv, "(b2) district-type, rezonings separate", filt)
        obr, _, _ = group_pool(broad, "broad upzonings", filt)
        ocn, _, _ = group_pool(Cn, "census-block reforms, each one unit", filt, "main (150 m)", "100 m", "300 m", bunch=False)
        nyu = census_ny_pool(Cn, filt)
        cn_city = [u for u in Cn if not u["unit"].startswith("nyc_")] + ([nyu] if nyu else [])
        if nyu:
            emit(nyu)
        occ, _, _ = group_pool(cn_city, "census-block reforms, New York pooled first", filt, "main (150 m)", "100 m", "300 m", bunch=False)
        cl = [as_lot(u) for u in cn_city]
        for u in cl:
            u["draws"].pop("bunching", None)
        oc, pc, bc = group_pool(dist_b + broad + cl, "(c) everything passing, census ÷ 0.75 to lot acres", filt)
        oc2, pc2, bc2 = group_pool(dist_b + broad, "(c2) everything passing, lot-based only", filt)
        out += oa + ob + ob2 + obr + ocn + occ + oc + oc2
        for lab, pm_, bf in (("(a) original places", pa, ba), ("(b) district-type (NY/PHL city pools)", pb_, bb),
                             ("(b2) district-type (rezonings separate)", pb2, bb2), ("(c) everything passing", pc, bc),
                             ("(c2) everything passing, lot-based only", pc2, bc2)):
            f = floor_row(lab, pm_, bf, filt)
            if f:
                floors.append(f)
        o1, pp1, _ = group_pool(p1, "P1 placebo", filt)
        o2, pp2, _ = group_pool(p2, "P2 placebo (Portland not pooled)", filt)
        out += o1 + o2
        for nm, pm_ in (("P1", pp1), ("P2", pp2)):
            if "main (91 m)" in pm_:
                m = pm_["main (91 m)"]
                out.append({"unit": f"PLACEBO {nm} READING [filter: {FILTERS[filt]}]", "variant": "main (91 m)", "filter": FILTERS[filt],
                            "status": "PASS (interval includes 0)" if m["low"] <= 0 <= m["high"] else "SIZEABLE GAP (interval excludes 0)",
                            "edge_effect_per_100_acres_per_year": m["edge_effect_per_100_acres_per_year"], "low": m["low"], "high": m["high"],
                            "n_units": m["n_units"], "units_in_pool": m["units_in_pool"]})
                for f in [f for f in floors if f["filter"] == FILTERS[filt]]:
                    dd = f["_draws"] - m["_draws"]
                    e = f["edge_effect_per_100_acres_per_year"] - m["edge_effect_per_100_acres_per_year"]
                    out.append({"unit": f"{f['unit']} MINUS PLACEBO {nm}", "variant": "edge effect minus placebo (draw by draw)",
                                "status": "net", "filter": FILTERS[filt], "edge_effect_per_100_acres_per_year": e,
                                "low": np.nanpercentile(dd, 5), "high": np.nanpercentile(dd, 95),
                                "wisconsin_direct_only_floor_2027_2031": e * F_WI, "wisconsin_floor_low": np.nanpercentile(dd, 5) * F_WI,
                                "wisconsin_floor_high": np.nanpercentile(dd, 95) * F_WI})
    out += [{k: v for k, v in f.items() if k != "_draws"} for f in floors]
    for o in out:
        o.setdefault("section", "pooled")
        o.pop("_draws", None)
    info_rows = [{"section": f"placebo setup {r['placebo']}", "unit": r.get("case"), "city": r.get("place"), "status": "setup",
                  **{k: v for k, v in r.items() if k not in ("placebo", "case", "place")}} for r in Pb["infos"]]
    R = pd.DataFrame(rows + out + info_rows)
    R.to_csv(REFERENCE / "tod_causal_edge_expand.csv", index=False, float_format="%.4f")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 1000)
    pd.set_option("display.max_colwidth", 90)
    show = ["unit", "variant", "status", "edge_effect_per_100_acres_per_year", "low", "high", "loo_low", "loo_high", "n_units",
            "wisconsin_direct_only_floor_2027_2031", "wisconsin_floor_low", "wisconsin_floor_high", "wisconsin_floor_loo_low", "wisconsin_floor_loo_high"]
    print(pd.DataFrame(out).reindex(columns=show).round(1).to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["lots", "placebo", "census", "combine", "all"], default="all")
    a = ap.parse_args()
    for p in (["lots", "placebo", "census", "combine"] if a.part == "all" else [a.part]):
        {"lots": part_lots, "placebo": part_placebo, "census": part_census, "combine": part_combine}[p]()


if __name__ == "__main__":
    main()
