"""Parking natural experiment N3: San Diego 2019 transit priority areas (TPA), edge test as TOD T3.

Rules: docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Natural experiments N1-N4" (N3) and "2026-11-03, N3 lock additions".

- Line: City ParkingAmenityTPA layer 6, the non-Coastal "Transit Priority Area" features (2015 regional plan). The
  Coastal Overlay Zone is dropped (its lots, and boundary points inside it or within 30 m of it).
- Ordinance O-21057 effective 2019-04-24 (outside the Coastal Overlay Zone).
- Windows (application date = earlier of project and approval create dates, joined from the City's approvals files):
  before 2016-01-01 to 2019-04-23; after 2019-04-24 to 2020-11-30.
- Outcome: new homes per 100 lot acres a year, all homes (TOTAL_DU), ratio of sums within the band;
  (after - before) inside minus outside. Bands 91 m (main), 46 m, 183 m; 25 m donut; 400 m segments with lots on
  both sides (and < 50% public land on each side); segment cluster bootstrap, 2,000 draws, seed 20261104.
- T3 functions are imported from scripts/run_tod_causal_edge.py (not edited); land counted once by
  scripts/fix_tod_station_acres.land_once (San Diego polygon fill).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/run_parking_ne_n3.py

Writes reference/parking_ne_n3.csv (summary rows only; no parcel ids).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware import geom as G  # noqa: E402
import run_tod_causal_edge as E  # noqa: E402
import fix_tod_station_acres as F  # noqa: E402

RAW = ROOT / "data" / "raw"
NE = RAW / "parking_natural_experiments" / "san_diego"
TOD = RAW / "tod_radius_programs" / "san_diego"
OUT = ROOT / "reference" / "parking_ne_n3.csv"
CRS = E.CRS                                   # EPSG:5070, metres
SEED, DRAWS = 20261104, 2000
E.DRAWS = DRAWS                               # locked draws for N3 (T3's own default is 1,000)
EFF = pd.Timestamp("2019-04-24")
B0, A1 = pd.Timestamp("2016-01-01"), pd.Timestamp("2020-12-01")     # [B0, EFF) and [EFF, A1)
YB, YA = (EFF - B0).days / 365.25, (A1 - EFF).days / 365.25
COASTAL_EDGE_M = 30.0
LOT_SNAP_M = 30.48                            # 100 ft: permit point to parcel point when no APN match


# ------------------------------------------------------------------ inputs
def parcels() -> pd.DataFrame:
    d = pd.read_csv(TOD / "county_parcels.csv", dtype={"apn": str}, low_memory=False,
                    usecols=["apn", "situs_juris", "acreage", "taxstat", "x_coord", "y_coord"])
    d = d[d.x_coord.notna() & d.y_coord.notna()]
    x, y = G.transform(d.x_coord.values, d.y_coord.values, 2230, CRS)
    land, src, n = F.land_once(x, y, d.acreage.values, case="san_diego_2021", index=d.index.values)
    P = pd.DataFrame({"apn": d.apn.str.strip().values, "city": d.situs_juris.astype(str).values, "x": x, "y": y,
                      "acres_land": land, "public": d.taxstat.astype(str).str.upper().eq("E").values})
    return P[(P.city == "SD") & (P.acres_land > 0)].reset_index(drop=True)


def permits() -> pd.DataFrame:
    pm = pd.DataFrame(json.loads((TOD / "permits.json").read_text()))
    pm["APPROVAL_ID"] = pm.APPROVAL_ID.astype(str)
    pm["issue"] = pd.to_datetime(pd.to_numeric(pm.APPROVAL_ISSUE_DATE), unit="ms")
    ap = pd.read_csv(NE / "development_approvals_tod_subset.csv", dtype=str).drop_duplicates("APPROVAL_ID")
    ap = ap.rename(columns={"APPROVAL_DU_BONUS": "AP_DU_BONUS"})
    pm = pm.merge(ap.drop(columns=[c for c in ap.columns if c in pm.columns and c != "APPROVAL_ID"]), on="APPROVAL_ID", how="left")
    for c in ("PROJECT_CREATE_DATE", "APPROVAL_CREATE_DATE"):
        pm[c] = pd.to_datetime(pm[c], errors="coerce")
    pm["app"] = pm[["PROJECT_CREATE_DATE", "APPROVAL_CREATE_DATE"]].min(axis=1)
    pm["homes"] = pd.to_numeric(pm.TOTAL_DU, errors="coerce").fillna(0)
    bonus_num = pd.to_numeric(pm.get("AP_DU_BONUS", pd.Series(np.nan, index=pm.index)), errors="coerce").fillna(0) > 0
    scope = (pm.get("PROJECT_SCOPE", pd.Series("", index=pm.index)).fillna("") + " " +
             pm.get("APPROVAL_SCOPE", pd.Series("", index=pm.index)).fillna("")).str.lower()
    pm["bonus_field"] = bonus_num | (pd.to_numeric(pm.APPROVAL_DU_BONUS, errors="coerce").fillna(0) > 0)
    pm["bonus_text"] = scope.str.contains(r"density bonus|\bdb\b|affordable housing density", regex=True)
    pm["apn10"] = pm.get("GIS_APN", pd.Series(np.nan, index=pm.index)).astype(str).str.replace(r"\D", "", regex=True)
    return pm[(pm.homes > 0) & pm.LAT_JOB.notna()].copy()


def tpa_line(which: str) -> list:
    if which == "main":
        L = G.read_geojson(NE / "parking_amenity_tpa_rtp2050.geojson")
        L = L.subset(L.attrs["name"].values == "Transit Priority Area")
    else:
        L = G.read_geojson(TOD / "transit_priority_areas_sandag_2022.geojson")
    return [[part] for f in L.to_crs(CRS).polys for part in f if len(part)]


def coastal() -> list:
    L = G.read_geojson(NE / "coastal_overlay_zone.geojson").to_crs(CRS)
    return [[part] for f in L.polys for part in f if len(part)]


# ------------------------------------------------------------------ lot sample (as T3 case_sample, polygon cases)
def assign_lots(P: pd.DataFrame, pm: pd.DataFrame) -> np.ndarray:
    """Parcel row for each permit: APN match within the city's parcels, else nearest parcel point within 100 ft."""
    first = pd.Series(np.arange(len(P)), index=P.apn).groupby(level=0).first()
    row = pm.apn10.map(first)
    px, py = G.transform(pm.LNG_JOB.values, pm.LAT_JOB.values, 4326, CRS)
    i, d = G.nearest(px, py, P.x.values, P.y.values, max_distance=LOT_SNAP_M)
    out = np.where(row.notna(), row.fillna(-1).values, i).astype(int)
    return out


def sample(P, pm, line_polys, coz, datecol, drop_lot_mask=None):
    bp = E.boundary_points(line_polys)
    keep = ~G.points_in_any(bp[:, 0], bp[:, 1], coz, union=True)
    keep &= ~np.isfinite(G.distance_to_polygons(bp[:, 0], bp[:, 1], coz, COASTAL_EDGE_M))
    bp = bp[keep]
    xy = P[["x", "y"]].to_numpy()
    dd, j = cKDTree(bp[:, :2]).query(xy, distance_upper_bound=250)
    near = np.isfinite(dd)
    S = P[near].copy()
    S["d"], S["bx"], S["by"] = dd[near], bp[j[near], 0], bp[j[near], 1]
    S = S[~G.points_in_any(S.x.values, S.y.values, coz, union=True)]
    S["in_reform_area"] = G.points_in_any(S.x.values, S.y.values, line_polys, union=True)
    S["s"] = np.where(S.in_reform_area, 1.0, -1.0) * S.d
    S = S[S.s.abs() <= 200]
    lot = pm["lot"].to_numpy()
    dt = pm[datecol]
    hb = pd.Series(pm.homes.values[(dt >= B0) & (dt < EFF)]).groupby(lot[(dt >= B0).values & (dt < EFF).values]).sum()
    ha = pd.Series(pm.homes.values[(dt >= EFF) & (dt < A1)]).groupby(lot[(dt >= EFF).values & (dt < A1).values]).sum()
    S["homes_before_win"] = S.index.map(hb).fillna(0).values
    S["homes_after_win"] = S.index.map(ha).fillna(0).values
    if drop_lot_mask is not None:
        S = S[~S.index.isin(drop_lot_mask)]
    S["pre"], S["post"] = S.homes_before_win / YB, S.homes_after_win / YA
    S["chg"] = S.post - S.pre
    S["w"], S["water"], S["half_mile"], S["art"] = 1.0, False, True, False
    return S


# ------------------------------------------------------------------ estimation
def estimate(S, h, rng, donut=0.0, label="", line="", dates="", extra=None):
    T = E.select(S, h, "s", donut)
    nin = int(T.in_reform_area.sum()) if len(T) else 0
    nout = int((~T.in_reform_area).sum()) if len(T) else 0
    r = {"line": line, "dates": dates, "variant": label, "bandwidth_m": h, "donut_m": donut,
         "lots_inside": nin, "lots_outside": nout, "segments": int(T.seg.nunique()) if len(T) else 0,
         "lots_with_new_homes_inside_before": int(((T.homes_before_win > 0) & T.in_reform_area).sum()) if len(T) else 0,
         "lots_with_new_homes_outside_before": int(((T.homes_before_win > 0) & ~T.in_reform_area).sum()) if len(T) else 0,
         "lots_with_new_homes_inside_after": int(((T.homes_after_win > 0) & T.in_reform_area).sum()) if len(T) else 0,
         "lots_with_new_homes_outside_after": int(((T.homes_after_win > 0) & ~T.in_reform_area).sum()) if len(T) else 0,
         "acres_inside": float(T.acres_land[T.in_reform_area].sum()) if len(T) else 0.0,
         "acres_outside": float(T.acres_land[~T.in_reform_area].sum()) if len(T) else 0.0}
    r.update(extra or {})
    if nin < E.MIN_LOTS or nout < E.MIN_LOTS:
        r["status"] = f"too few lots (< {E.MIN_LOTS} a side)"
        return r, T
    pt, dr = E.boot(T, "chg", rng)
    r.update({"status": "estimated", "edge_effect_homes_per_100_acres_per_year": pt,
              "low_90": np.nanpercentile(dr, 5), "high_90": np.nanpercentile(dr, 95),
              "low_97_5": np.nanpercentile(dr, 1.25), "high_97_5": np.nanpercentile(dr, 98.75),
              "boot_sd": np.nanstd(dr, ddof=1), "mde_1_645_sd": 1.645 * np.nanstd(dr, ddof=1)})
    return r, T


def balance(T, rng):
    pb, pdr = E.boot(T, "pre", rng)
    lo, hi = np.nanpercentile(pdr, [5, 95])
    return {"balance_pre_gap_per_100_acres": pb, "balance_low_90": lo, "balance_high_90": hi,
            "balance_pass": bool(lo <= 0 <= hi)}


def mf_counts(T, pm, datecol):
    """Lots in the main sample with a 2+ home project, per side and window (counts only)."""
    out = {}
    mf = pm[pm.homes >= 2]
    for w, (a, b) in (("before", (B0, EFF)), ("after", (EFF, A1))):
        lots = set(mf.lot[(mf[datecol] >= a) & (mf[datecol] < b)])
        for side, m in (("inside", T.in_reform_area), ("outside", ~T.in_reform_area)):
            out[f"lots_2plus_projects_{side}_{w}"] = int(T.index[m].isin(lots).sum())
    return out


def main() -> None:
    P = parcels()
    pm = permits()
    pm["lot"] = assign_lots(P, pm)
    pm = pm[pm.lot >= 0]
    coz = coastal()
    lines = {"main": ("ParkingAmenityTPA layer 6, non-Coastal TPA (2015 RTP)", tpa_line("main")),
             "sandag": ("SANDAG 2022 TPA (TOD line), Coastal Zone dropped", tpa_line("sandag"))}
    rng = np.random.default_rng(SEED)
    rows = []
    # bonus flags available?
    yrs = pm.app.between(B0, A1 - pd.Timedelta(days=1)) | pm.issue.between(B0, A1 - pd.Timedelta(days=1))
    bonus_lots = set(pm.lot[(pm.bonus_field | pm.bonus_text) & yrs])
    flag_note = (f"APPROVAL_DU_BONUS>0 in window: {int((pm.bonus_field & yrs).sum())} permits; "
                 f"scope text 'density bonus': {int((pm.bonus_text & yrs).sum())} permits")
    print(flag_note)

    Sm = sample(P, pm, lines["main"][1], coz, "app")
    lname, dname = lines["main"][0], "application (earlier of project/approval create)"
    for vname, kw in (("main (91 m)", dict(h=E.H_MAIN)), ("46 m", dict(h=E.H_LO)), ("183 m", dict(h=E.H_HI)),
                      ("donut 25 m (91 m)", dict(h=E.H_MAIN, donut=E.DONUT))):
        r, T = estimate(Sm, rng=rng, label=vname, line=lname, dates=dname, **kw)
        if vname == "main (91 m)" and r["status"] == "estimated":
            r.update(balance(T, rng))
            r.update(mf_counts(T, pm, "app"))
            bs, bd = E.bunching(Sm, rng)
            r["bunching_stat"] = bs
            r["bunching_low_90"], r["bunching_high_90"] = (np.nanpercentile(bd, [5, 95]) if np.isfinite(bd).any() else (np.nan, np.nan))
            r["bunching_flag"] = bool(r["bunching_high_90"] < 0)
        rows.append(r)
    # sensitivities at 91 m (balance shown for each)
    sens = [("SANDAG 2022 line", sample(P, pm, lines["sandag"][1], coz, "app"), lines["sandag"][0], dname),
            ("issue dates (flagged)", sample(P, pm, lines["main"][1], coz, "issue"), lname, "issue"),
            ("no density bonus lots", sample(P, pm, lines["main"][1], coz, "app", drop_lot_mask=bonus_lots), lname, dname)]
    xm, ym = Sm.x.values, Sm.y.values
    same = int((G.points_in_any(xm, ym, lines["main"][1], union=True) != G.points_in_any(xm, ym, lines["sandag"][1], union=True)).sum())
    notes = {"SANDAG 2022 line": f"lots within 200 m whose side differs between the two lines outside the Coastal Zone: {same} "
                                 "(the non-Coastal ParkingAmenityTPA features are the SANDAG 2022 polygons)",
             "issue dates (flagged)": "issue date instead of application date",
             "no density bonus lots": flag_note + f"; bonus lots in the 200 m sample: {int(Sm.index.isin(list(bonus_lots)).sum())}; "
                                      "APPROVAL_DU_BONUS is filled almost only from 2019 on, so before-window bonus use is mostly unflagged"}
    for vname, S, ln, dn in sens:
        r, T = estimate(S, E.H_MAIN, rng, label=f"sensitivity: {vname} (91 m)", line=ln, dates=dn,
                        extra={"note": notes[vname]})
        if r["status"] == "estimated":
            r.update(balance(T, rng))
        rows.append(r)
    R = pd.DataFrame(rows)
    R.insert(0, "test", "N3 San Diego 2019 TPA")
    R["windows"] = f"before {B0.date()}..{(EFF - pd.Timedelta(days=1)).date()} ({YB:.3f} yr); after {EFF.date()}..2020-11-30 ({YA:.3f} yr)"
    R["seed_draws"] = f"{SEED}; {DRAWS}"
    R["coastal_commission"] = ("LCP-6-SAN-19-0063-1: filed 2019-05-22; approved with suggested modifications 2019-10-16 (TPA "
                               "exemption kept out of the Beach Impact Area); City O-21164 adopted 2020-01-08, effective "
                               "2020-02-09; coastal lots (outside the Beach Impact Area) treated for part of the after window; "
                               "Coastal Overlay Zone dropped here")
    R["parcel_source_licence"] = ("SANDAG hosted Parcels FeatureServer (SanGIS/Assessor): county_parcels.csv and parcel_area.csv; "
                                  "manifest.json records no licence field, only 'no owner names; local only'; SanGIS end user "
                                  "use agreement applies")
    R.to_csv(OUT, index=False, float_format="%.4f")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
    print(R.T.to_string())


if __name__ == "__main__":
    main()
