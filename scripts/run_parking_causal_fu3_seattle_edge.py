"""Parking causal plan, follow-up FU3: Seattle edge test at the urban village / urban center boundaries
(docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Stage 1 follow-ups", bullet FU3; locked before counting).

Difference in discontinuities around Seattle's 2012 parking reform (no minimums in urban villages / centers near
frequent transit): lots just inside vs just outside the boundary of the union of the urban village and urban center
polygons, change in new homes per 100 lot acres a year (after 2013-2017 minus before 2007-2011; 2012 left out).
Center City (UVDA "Center_City": Downtown, Uptown, South Lake Union) and the manufacturing/industrial centers (UV_TYPE
"MIC") are left out.

Method = TOD Test 2 (T3, docs/tod/CAUSAL_FRAMEWORK_PLAN.md; scripts/run_tod_causal_edge.py), whose functions are
imported unchanged: boundary of the polygon union (shared internal edges removed, points every 5 m, k-d tree),
ratio of sums within the band (main), 91 m main band, 46 m and 183 m, 25 m donut, before-window balance at 91 m,
400 m segments with lots on both sides, public land >= 50% of either side dropped, segments within 30 m of TIGER
area water dropped, cluster bootstrap over segments (1,000 draws, seed 20261103).

Lots and permits follow TOD's Seattle case adapter (missing_middleware/tod/case_seattle.py, _load): the City's 2010
Zoned Development Capacity parcels (Seattle only, one row per PIN, nested rings repaired, GEOS-style interior point);
SDCI building permits of type "New" adding homes, one record per permit number, by issue year, placed on the parcel
that contains the permit point (else the nearest parcel within 30 m).

    uv run --all-extras python scripts/run_parking_causal_fu3_seattle_edge.py

Writes reference/parking_causal_fu3_seattle_edge.csv (summary rows only; no parcel ids).
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
from missing_middleware.tod import case_seattle as CS  # noqa: E402
import run_tod_causal_edge as E  # noqa: E402

CRS = E.CRS                                   # 5070, as T3
H_MAIN, H_LO, H_HI, DONUT = E.H_MAIN, E.H_LO, E.H_HI, E.DONUT
SEED, MIN_LOTS = E.SEED, E.MIN_LOTS
BEFORE, AFTER = (2007, 2011), (2013, 2017)
ZONES = RAW / "parking_first_stage" / "seattle_zones" / "urban_centers_villages.geojson"
TIGER_KEY = "Seattle Othello 2012"            # T3's key for King County (53033) water and roads
OUT = REFERENCE / "parking_causal_fu3_seattle_edge.csv"
CENTER_CITY_2010 = {"Belltown", "Commercial Core", "Denny Triangle", "Pioneer Square", "Chinatown-International District",
                    "South Lake Union", "Uptown"}


def zones():
    Z = X.read_vector(ZONES, dst=CRS)
    drop = (Z.UVDA.astype(str) == "Center_City") | (Z.UV_TYPE.astype(str) == "MIC")
    return Z[~drop].reset_index(drop=True), Z[drop].reset_index(drop=True)


def lots_and_permits():
    d = CS._load()
    p = d["parcels"].copy()
    x, y = X.transform(p.rx.to_numpy(float), p.ry.to_numpy(float), CS.CRS_M, CRS)
    pg = d["permits"]
    n_all = len(pg)
    pg = pg[pg["pix"].notna()]
    units = {}
    for lab, (a, b) in (("before", BEFORE), ("after", AFTER)):
        w = pg[pg.year.between(a, b)]
        units[lab] = w.groupby(w.pix.astype(int)).units.sum().reindex(p.index).fillna(0).to_numpy()
    yrs = pd.read_csv(CS.DIR / "permits_new_units.csv", dtype=str)
    win = d["permits"].year.between(*BEFORE) | d["permits"].year.between(*AFTER)
    located = {"permits_new_in_windows": int(win.sum()),
               "permits_new_in_windows_located": int((win & d["permits"].pix.notna()).sum()),
               "homes_new_in_windows": float(d["permits"].units[win].sum()),
               "homes_new_in_windows_located": float(d["permits"].units[win & d["permits"].pix.notna()].sum()),
               "permits_file_rows": len(yrs), "permits_new_all_years": n_all}
    zb = p["ZONING"].astype(str).str.upper()
    use = (p["LAND_USE_DESC"].astype(str) + " " + p["PRES_USE"].astype(str)).str.upper()
    eligible = ~zb.str.match(r"^(IG|IB|IC|MIO|PARK|SF? ?PARK)") & ~use.str.contains(
        r"PARK|CEMETER|SCHOOL|CHURCH|RELIG|UTILIT|GOVERN|RIGHT.OF.WAY|WATER|HOSPITAL|COLLEGE|UNIVERS")
    L = pd.DataFrame({"x": x, "y": y, "acres_land": p.acres.to_numpy(float),
                      "public": p.PUB_OWN_TYPE.astype(str).str.upper().isin(["PUBLIC", "CITY OF SEATTLE"]).to_numpy(),
                      "eligible": eligible.to_numpy(), "village_2010": p.VILLAGE_NAME.astype(str).to_numpy(),
                      "nr_units": pd.to_numeric(p.NR_UNITS, errors="coerce").to_numpy(float),
                      "maxfar": pd.to_numeric(p.MAXFAR, errors="coerce").to_numpy(float),
                      "vacant": use.str.contains("VACANT").to_numpy(float),
                      "homes_before_win": units["before"], "homes_after_win": units["after"]})
    return L, located


def implausible(L):
    """T3 lot-table rule without the building-value exemption (no value in the 2010 capacity parcels): > 2,000 new homes
    per acre and 20+ homes. Flagged and counted; see main()."""
    new = L[["homes_before_win", "homes_after_win"]].max(axis=1)
    return ((new / L.acres_land.where(L.acres_land > 0)) > 2000).fillna(False) & (new >= 20)


def sample(L, keep, excl):
    inside = G.points_in_any(L.x.values, L.y.values, list(keep.geometry), union=True)
    in_excl = G.points_in_any(L.x.values, L.y.values, list(excl.geometry), union=True)
    bp = E.boundary_points(list(keep.geometry))
    # boundary pieces that face Center City or a MIC are not reform edges (both sides lacked a minimum, or industry)
    nx, ny = -bp[:, 3], bp[:, 2]
    side = np.zeros(len(bp), bool)
    for s in (1.0, -1.0):
        side |= G.points_in_any(bp[:, 0] + s * 2.0 * nx, bp[:, 1] + s * 2.0 * ny, list(excl.geometry), union=True)
    tree = cKDTree(bp[:, :2])
    dd, j = tree.query(L[["x", "y"]].to_numpy())
    S = L.assign(in_reform_area=inside, s=np.where(inside, 1.0, -1.0) * dd, bx=bp[j, 0], by=bp[j, 1],
                 excl_area=in_excl, excl_edge=side[j])
    S["art"] = E.arterial_flag(S.bx.values, S.by.values, bp[j, 2], bp[j, 3], E.arterials(TIGER_KEY))
    counts = {"lots_in_center_city_or_mic_dropped": int((in_excl & (np.abs(S.s) <= 200)).sum()),
              "lots_nearest_edge_faces_excluded_area_dropped": int((~in_excl & side[j] & (np.abs(S.s) <= 200)).sum())}
    S = S[~in_excl & ~side[j] & (S.acres_land > 0) & (np.abs(S.s) <= 200)].copy()
    water = E.water_polys(TIGER_KEY)
    S["water"] = np.isfinite(G.distance_to_polygons(S.bx.values, S.by.values, water, E.WATER_M)) if water else False
    yb, ya = BEFORE[1] - BEFORE[0] + 1, AFTER[1] - AFTER[0] + 1
    S["pre"], S["post"] = S.homes_before_win / yb, S.homes_after_win / ya
    S["chg"] = S.post - S.pre
    S["w"] = 1.0
    S["half_mile"] = True
    S["log_acres"] = np.log(S.acres_land)
    S["units_per_acre"] = S.nr_units / S.acres_land
    # lot-midway distance (T3 sensitivity for polygon places)
    dm, mx, my, _, _ = E.lot_midway(S.reset_index(drop=True), np.arange(len(S)))
    S["s_lotmid"] = np.where(S.in_reform_area, 1.0, -1.0) * dm
    S["bx_lm"], S["by_lm"], S["art_lm"] = mx, my, False
    return S, counts, water


def estimate(S, rng, vname, h, dist="s", donut=0.0, no_art=False, eligible_only=False):
    U = S[S.eligible] if eligible_only else S
    T = E.select(U, h, dist, donut, False, no_art)
    nin, nout = (int(T.in_reform_area.sum()), int((~T.in_reform_area).sum())) if len(T) else (0, 0)
    r = {"row": "estimate", "variant": vname, "bandwidth_m": round(h, 2), "lots_inside": nin, "lots_outside": nout,
         "segments": int(T.seg.nunique()) if len(T) else 0,
         "acres_inside": float(T.acres_land[T.in_reform_area].sum()) if len(T) else 0.0,
         "acres_outside": float(T.acres_land[~T.in_reform_area].sum()) if len(T) else 0.0,
         "homes_before_inside": float(T.homes_before_win[T.in_reform_area].sum()) if len(T) else 0.0,
         "homes_after_inside": float(T.homes_after_win[T.in_reform_area].sum()) if len(T) else 0.0,
         "homes_before_outside": float(T.homes_before_win[~T.in_reform_area].sum()) if len(T) else 0.0,
         "homes_after_outside": float(T.homes_after_win[~T.in_reform_area].sum()) if len(T) else 0.0}
    if nin < MIN_LOTS or nout < MIN_LOTS:
        r["status"] = f"too few lots (< {MIN_LOTS} a side)"
        return r, T
    pt, dr = E.boot(T, "chg", rng)
    ins, out = T.in_reform_area, ~T.in_reform_area
    r.update({"status": "estimated", "edge_effect_per_100_acres_per_year": pt,
              "low_90": np.nanpercentile(dr, 5), "high_90": np.nanpercentile(dr, 95),
              "inside_change_rate": 100 * T.chg[ins].sum() / T.acres_land[ins].sum(),
              "outside_change_rate": 100 * T.chg[out].sum() / T.acres_land[out].sum(),
              "inside_before_rate": 100 * T.pre[ins].sum() / T.acres_land[ins].sum(),
              "outside_before_rate": 100 * T.pre[out].sum() / T.acres_land[out].sum(),
              "inside_after_rate": 100 * T.post[ins].sum() / T.acres_land[ins].sum(),
              "outside_after_rate": 100 * T.post[out].sum() / T.acres_land[out].sum()})
    return r, T


def main() -> None:
    keep, excl = zones()
    L, located = lots_and_permits()
    imp = implausible(L)
    S, counts, water = sample(L, keep, excl)
    S_imp = imp.reindex(S.index).fillna(False)
    rng = np.random.default_rng(SEED)
    variants = {"main (91 m)": dict(h=H_MAIN), "46 m": dict(h=H_LO), "183 m": dict(h=H_HI),
                "donut 25 m (91 m)": dict(h=H_MAIN, donut=DONUT),
                "lot-midway distance (91 m)": dict(h=H_MAIN, dist="s_lotmid"),
                "without arterial segments (91 m)": dict(h=H_MAIN, no_art=True),
                "TOD-eligible lots only (91 m)": dict(h=H_MAIN, eligible_only=True)}
    rows, Tmain = [], None
    for vname, kw in variants.items():
        r, T = estimate(S, rng, vname, **kw)
        if vname == "main (91 m)":
            Tmain = T
            pb, pdr = E.boot(T, "pre", rng)
            plo, phi = np.nanpercentile(pdr, [5, 95])
            r.update({"balance_pre_gap_per_100_acres": pb, "balance_pre_gap_low_90": plo, "balance_pre_gap_high_90": phi,
                      "balance_pass": bool(plo <= 0 <= phi), "local_linear_estimate": E.local_linear(T, kw["h"])})
            for col, lab in (("log_acres", "smd_log_lot_acres"), ("units_per_acre", "smd_existing_homes_per_acre_2010"),
                             ("vacant", "smd_lot_vacant_2010"), ("maxfar", "smd_max_far_2010")):
                r[lab] = E.smd(T, col)
            r["imbalanced_traits"] = ";".join(k.removeprefix("smd_") for k, v in r.items()
                                              if k.startswith("smd_") and pd.notna(v) and abs(v) > 0.25)
            bs, bd = E.bunching(S, rng)
            r["bunching_stat"] = bs
            r["bunching_low_90"], r["bunching_high_90"] = np.nanpercentile(bd, [5, 95]) if np.isfinite(bd).any() else (np.nan, np.nan)
            r["arterial_segment_share"] = float((T.groupby("seg").art.mean() >= E.ART_SHARE).mean())
        rows.append(r)
    # largest-lot sensitivity: drop the single lot with the most new homes in either window (within the main band)
    big = Tmain[["homes_before_win", "homes_after_win"]].max(axis=1).idxmax()
    r, _ = estimate(S.drop(index=big), rng, "drop largest lot (91 m)", H_MAIN)
    rows.append(r)
    # T3's implausible-lot rule (without its building-value exemption, which needs values this layer lacks)
    r, _ = estimate(S[~S_imp], rng, "implausible lots dropped (91 m)", H_MAIN)
    rows.append(r)
    # post hoc: current polygons vs the 2010 capacity parcels' VILLAGE_NAME; keep lots whose status agrees
    agree = S.in_reform_area == (S.village_2010 != "Outside Villages")
    for vname, h in (("2010 village status agrees (91 m)", H_MAIN), ("2010 village status agrees (183 m)", H_HI)):
        r, Ta = estimate(S[agree], rng, vname, h)
        if r["status"] == "estimated":
            pb, pdr = E.boot(Ta, "pre", rng)
            plo, phi = np.nanpercentile(pdr, [5, 95])
            r.update({"balance_pre_gap_per_100_acres": pb, "balance_pre_gap_low_90": plo, "balance_pre_gap_high_90": phi,
                      "balance_pass": bool(plo <= 0 <= phi)})
        rows.append(r)
    R = pd.DataFrame(rows)
    # pass rule (as T3): 46 m and 183 m estimates inside the main 90% interval
    m = R.set_index("variant")
    info = {"row": "checks", "variant": "data and rule checks", "status": "info",
            "rule_46m_inside_main_interval": bool(m.loc["main (91 m)", "low_90"] <= m.loc["46 m", "edge_effect_per_100_acres_per_year"] <= m.loc["main (91 m)", "high_90"]),
            "rule_183m_inside_main_interval": bool(m.loc["main (91 m)", "low_90"] <= m.loc["183 m", "edge_effect_per_100_acres_per_year"] <= m.loc["main (91 m)", "high_90"]),
            "implausible_lots_flagged_in_200m": int(S_imp.sum()), "implausible_rule_applied": False,
            "water_layer": "TIGER 2024 area water, King County" if water else "none on disk",
            "largest_lot_homes_before": float(Tmain.loc[big, "homes_before_win"]), "largest_lot_homes_after": float(Tmain.loc[big, "homes_after_win"]),
            "largest_lot_side": "inside" if bool(Tmain.loc[big, "in_reform_area"]) else "outside",
            # 2010 village membership (capacity parcels' VILLAGE_NAME) vs current polygons, main band
            "main_band_inside_lots_outside_2010_villages": int((Tmain.in_reform_area & (Tmain.village_2010 == "Outside Villages")).sum()),
            "main_band_outside_lots_inside_2010_villages": int((~Tmain.in_reform_area & (Tmain.village_2010 != "Outside Villages")).sum()),
            "main_band_outside_lots_in_2010_center_city": int((~Tmain.in_reform_area & Tmain.village_2010.isin(CENTER_CITY_2010)).sum()),
            "parcels_2010_seattle": len(L), **counts, **located}
    R = pd.concat([R, pd.DataFrame([info])], ignore_index=True)
    R.insert(0, "test", "FU3 Seattle urban village edge, 2012 reform; before 2007-2011, after 2013-2017")
    R.insert(1, "unit", "new homes per 100 lot acres a year; effect = (after - before) inside minus outside")
    R.to_csv(OUT, index=False, float_format="%.4f")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 50)
    print(R[R.row == "estimate"][["variant", "status", "lots_inside", "lots_outside", "segments", "acres_inside", "acres_outside",
                                  "edge_effect_per_100_acres_per_year", "low_90", "high_90", "inside_change_rate", "outside_change_rate"]].round(2).to_string(index=False))
    print(R.iloc[0].dropna().to_string())
    print(pd.Series(info).to_string())
    # top lots in the main band (no ids printed): new homes and side
    t = Tmain.assign(new=Tmain[["homes_before_win", "homes_after_win"]].max(axis=1)).nlargest(8, "new")
    print(t[["in_reform_area", "s", "acres_land", "homes_before_win", "homes_after_win"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
