"""Frozen drift-rule test on new TOD reform cities (docs/tod/NEW_REFORM_CITIES_PLAN.md).

    uv run --all-extras python scripts/run_tod_new_city_test.py --case denver_2018

The drift rule is NOT refitted: change in the upzoned lots' share of new homes = A + B x (share before - 0.5),
with A, B from the existing 9 cities (reference/tod_lot_model_line.csv inputs). Benchmarks: average change (+0.040)
and same share. Shares are measured in the study area (reform lots + a 1/2-mile ring), all lots kept.
Writes reference/tod_new_city_test_<case>.csv. No lot-level rows or parcel ids are written.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from missing_middleware import geom_extra_station as X  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402


def read(path, **kw) -> pd.DataFrame:
    """A vector file in CRS 5070 (polygons in column geometry, points in x, y)."""
    return X.read_vector(path, dst=CRS, **kw)


def rep_xy(polys: list) -> tuple[np.ndarray, np.ndarray]:
    """GEOS representative points."""
    return X.interior_points(polys)


def first_in(px, py, layer: pd.DataFrame, col: str | None = None) -> pd.Series:
    """sjoin 'within' (left), first match: position of the polygon (or its column col), NaN where none."""
    k = X.first_within(np.asarray(px, float), np.asarray(py, float), list(layer.geometry))
    if col is None:
        return pd.Series(np.where(k >= 0, k, np.nan))
    return pd.Series(np.where(k >= 0, layer[col].values[np.maximum(k, 0)], None), dtype=object).where(k >= 0)

A, B, AVG = -0.038, -0.398, 0.0396   # frozen on the 9 cities (AQ-068); AVG = their mean change
RING_M, NEAR_M = 805.0, 805.0
CRS = 5070


def stories(zone: str | None) -> float:
    """Allowed stories from a Denver zone code's last number (C-MX-8 -> 8); industrial I-A / I-B allow no homes -> 0."""
    if not isinstance(zone, str):
        return np.nan
    z = zone.split(",")[0].strip()
    if z in ("I-A", "I-B") or z.startswith("I-A") or z.startswith("I-B"):
        return 0.0
    m = re.search(r"-(\d+(?:\.\d+)?)x?$", z)
    return float(m.group(1)) if m else np.nan


def denver_2018(version: str) -> dict:
    d = RAW / "tod_new_cities" / "denver"
    z = read(d / "zone_map_amendments.geojson")
    r = z[(z.ORD_YEAR == 2018) & z.ORD_NUM.isin([15, 17])].reset_index(drop=True).copy()
    io_new = r.OVERLAY_DISTRICT.fillna("").str.contains("IO-1") & ~r.FROM_OVERLAY_DIST_1.fillna("").str.contains("IO-1")
    base_up = r.ZONE_DISTRICT.map(stories) > r.FROM_ZONE_1.map(stories)
    r["up"] = (io_new | base_up) if version == "main" else base_up
    st = read(d / "rail_stations.geojson")
    yo = pd.to_numeric(st.YEAR_OPEN, errors="coerce")
    st = st[(st.STATUS == "Existing") & (yo <= 2018)]
    p = read(d / "parcels.geojson")
    p = p[X.nonempty(list(p.geometry))].reset_index(drop=True)
    px, py = rep_xy(list(p.geometry))
    k = first_in(px, py, r)
    inref = k.notna()
    up = pd.Series(r.up.values[k.fillna(0).astype(int)], dtype=bool).where(inref, False).astype(bool) & inref
    area = list(r.geometry)
    dist_area = pd.Series(X.distance_within(px, py, area, RING_M + 1.0))
    ring = (~inref) & (dist_area <= RING_M)
    from scipy.spatial import cKDTree
    dist_st = pd.Series(cKDTree(np.c_[st.x, st.y]).query(np.c_[px, py])[0])
    far = up & (dist_st > NEAR_M)   # item 48: upzoned lots more than 1/2 mile from rail open on the reform date
    lots = pd.DataFrame({"SCHEDNUM": p.SCHEDNUM.values, "acres": X.areas(list(p.geometry)) / 4046.86,
                         "in_reform": inref.values, "upzoned": (up & ~far).values, "far_upzoned": far.values,
                         "study": (inref | ring).values})
    perm = pd.concat([read(d / "residential_permits.geojson").assign(src="residential"),
                      read(d / "commercial_permits.geojson").assign(src="commercial")], ignore_index=True)
    perm["UNITS"] = pd.to_numeric(perm.UNITS, errors="coerce").fillna(0)
    perm = perm[perm.CLASS.str.upper().eq("NEW BUILDING") & (perm.UNITS > 0) & perm.CANCEL.isna()].copy()
    perm["date"] = pd.to_datetime(perm.DATE_ISSUED, unit="ms")
    eff = pd.Timestamp("2018-02-12")
    windows = {"before": (pd.Timestamp("2012-07-11"), pd.Timestamp("2017-12-31")),
               "after": (pd.Timestamp("2019-01-01"), pd.Timestamp("2023-12-31"))}
    # permits are placed on the lot whose shape holds the permit point (schedule numbers change when lots are
    # merged or split after the permit; only 35% matched today's parcels by number); the number is the fallback
    perm = perm[perm.x.notna()]
    perm["lot"] = first_in(perm.x.values, perm.y.values, p).values
    num = pd.Series(np.arange(len(p)), index=p.SCHEDNUM.values)
    num = num[~num.index.duplicated()]
    perm["lot"] = perm["lot"].fillna(perm.SCHEDNUM.map(num))
    matched = perm["lot"].notna()
    u = {}
    for w, (a, b) in windows.items():
        x = perm[(perm.date >= a) & (perm.date <= b) & matched].groupby("lot").UNITS.sum()
        u[w] = pd.Series(np.arange(len(p))).map(x).fillna(0).values
    s = lots.study.values
    out = {"case": f"denver_2018_{version}", "reform_date": str(eff.date()),
           "before_years": round((windows["before"][1] - windows["before"][0]).days / 365.25, 2), "after_years": 5.0,
           "study_lots": int(s.sum()), "study_acres": float(lots.acres[s].sum()), "upzoned_lots": int((s & lots.upzoned).sum()),
           "upzoned_acres": float(lots.acres[s & lots.upzoned].sum()), "relabelled_far_from_rail": int((s & lots.far_upzoned).sum()),
           "permits_matched_to_parcels_share": float(matched.mean())}
    for w in windows:
        tot, upz = float(u[w][s].sum()), float(u[w][s & lots.upzoned.values].sum())
        out[f"homes_{w}"], out[f"homes_{w}_upzoned"] = tot, upz
        out[f"share_{w}"] = upz / tot if tot > 0 else np.nan
    return out


PDX_HPA = {"R5": 8.7, "R3": 14.5, "R2": 21.8, "R1": 43.6, "RH": 87.1, "RM1": 43.6, "RM2": 65.3, "RM3": 87.1, "RM4": 174.2}


def share_case(case: str, reform: pd.DataFrame, parcels: pd.DataFrame, stations: pd.DataFrame,
               permits: pd.DataFrame, eff: pd.Timestamp, windows: dict, ring_masks: dict | None = None) -> dict:
    """Generic frozen-test case: reform polygons (column up; CRS 5070 features in column geometry), parcels, rapid
    stops open on the reform date (x, y), permits (columns date, units, x, y). Lots in the reform area and a
    1/2-mile ring; permits placed by point."""
    p = parcels[X.nonempty(list(parcels.geometry))].reset_index(drop=True)
    reform = reform.reset_index(drop=True)
    px, py = rep_xy(list(p.geometry))
    pts = pd.DataFrame({"x": px, "y": py})
    k = first_in(px, py, reform)
    inref = k.notna().values
    up = np.where(inref, reform.up.values[k.fillna(0).astype(int)], False).astype(bool) & inref
    area = list(reform.geometry)
    ring = (~inref) & (X.distance_within(px, py, area, RING_M + 1.0) <= RING_M)
    from scipy.spatial import cKDTree
    sx = np.c_[stations.x, stations.y]
    dist_st = cKDTree(sx).query(np.c_[px, py])[0]
    far = up & (dist_st > NEAR_M)
    study = inref | ring
    upz = up & ~far
    permits = permits[permits.x.notna()].copy()
    permits["lot"] = first_in(permits.x.values, permits.y.values, p).values
    permits["in_study"] = X.within_buffer_geos(permits.x.values, permits.y.values, area, RING_M)
    acres = X.areas(list(p.geometry)) / 4046.86
    out = {"case": case, "reform_date": str(eff.date()), "study_lots": int(study.sum()), "study_acres": float(acres[study].sum()),
           "upzoned_lots": int((study & upz).sum()), "upzoned_acres": float(acres[study & upz].sum()),
           "relabelled_far_from_rail": int((study & far).sum())}
    for w, (a, b) in windows.items():
        x = permits[(permits.date >= a) & (permits.date <= b)]
        out[f"{w}_years"] = round((b - a).days / 365.25, 2)
        inside = x[x.in_study.values]
        out[f"permit_homes_in_study_{w}"] = float(inside.units.sum())
        out[f"permit_homes_not_placed_{w}"] = float(inside.units[inside.lot.isna()].sum())
        per = x.dropna(subset=["lot"]).groupby("lot").units.sum()
        u = pd.Series(np.arange(len(p))).map(per).fillna(0).values
        tot, uz = float(u[study].sum()), float(u[study & upz].sum())
        out[f"homes_{w}"], out[f"homes_{w}_upzoned"] = tot, uz
        for name, mk in (ring_masks or {}).items():   # e.g. ring homes on Infill-Project (single-dwelling) lots
            out[f"homes_{w}_ring_{name}"] = float(u[ring & mk(pts)].sum())
        out[f"share_{w}"] = uz / tot if tot > 0 else np.nan
    return out


def portland_2020(version: str) -> dict:
    d = RAW / "tod_new_cities" / "portland"
    r = read(d / "bhd_zone_changes.geojson")
    ex, pr = r.ex_zone.map(PDX_HPA), r.pr_zone.map(PDX_HPA)
    r["up"] = (pr > ex).fillna(False)
    if version == "no_rh_rm4":   # RH mapped at 4:1 before in some central areas: RH->RM4 may not be a raise
        r.loc[(r.ex_zone == "RH") & (r.pr_zone == "RM4"), "up"] = False
    if version == "no_r1_rm2":   # at about 1,500 sq ft per home RM2 allows about what R1 did
        r.loc[(r.ex_zone == "R1") & (r.pr_zone == "RM2"), "up"] = False
    st = pd.concat([read(d / "max_stops.geojson"), read(d / "streetcar_stops.geojson")], ignore_index=True)
    parcels = read(d / "taxlots.geojson")
    perm = pd.concat([read(d / "residential_permits.geojson"), read(d / "commercial_permits.geojson")], ignore_index=True)
    perm["date"] = pd.to_datetime(perm.ISSUED, unit="ms")
    perm["units"] = pd.to_numeric(perm.NUMNEWUNITS, errors="coerce").fillna(0)
    perm = perm[perm.units > 0]
    eff = pd.Timestamp("2020-03-01")
    windows = {"before": (pd.Timestamp("2014-01-01"), pd.Timestamp("2019-12-31")),
               "after": (pd.Timestamp("2021-01-01"), pd.Timestamp("2025-12-31"))}
    z20 = read(d / "zoning_2020_03_01.geojson")
    single = z20[z20.ZONE.isin(["RF", "R20", "R10", "R7", "R5", "R2.5"])].reset_index(drop=True)

    def on_single(pts):
        return first_in(pts.x.values, pts.y.values, single).notna().values
    return share_case(f"portland_2020_{version}", r, parcels, st, perm, eff, windows, {"single_dwelling": on_single})


PDX18_FAR = {"CN1": 0.75, "CN2": 0.75, "CO1": 0.75, "CO2": 2.0, "CM": 1.0, "CS": 3.0, "CG": 3.0, "CX": 4.0, "EX": 3.0,
             "CM1": 1.5, "CM2": 2.5, "CM3": 3.0, "CE": 2.5}
PDX18_RES = {"RF": 0.4, "R20": 2.2, "R10": 4.4, "R7": 6.2, "R5": 8.7, "R2.5": 17.4, "R3": 14.5, "R2": 21.8, "R1": 43.6,
             "RH": 87.1, "RX": 174.2}
MIXED_NEW = {"CM1", "CM2", "CM3", "CE"}


def pdx18_hpa(z) -> float:
    """Homes per acre allowed by a 2017/2018 Portland zone (plan's 2018 table); zones allowing no homes -> 0."""
    if not isinstance(z, str):
        return np.nan
    z = z.strip().upper()
    if z in PDX18_FAR:
        return PDX18_FAR[z] * 43.56
    if z in PDX18_RES:
        return PDX18_RES[z]
    return 0.0 if z[:1] in ("I", "E", "O") or z.startswith("IR") else np.nan


def portland_2018(version: str) -> dict:
    d = RAW / "tod_new_cities" / "portland"
    parcels = read(d / "taxlots.geojson")
    parcels = parcels[X.nonempty(list(parcels.geometry))].reset_index(drop=True)
    px, py = rep_xy(list(parcels.geometry))
    zone = {}
    for k, f in (("old", "zoning_pre_2018_05_24.geojson"), ("new", "zoning_2018_05_25.geojson")):
        z = read(d / f)
        zone[k] = first_in(px, py, z, "ZONE")
    changed = zone["old"].notna() & zone["new"].notna() & (zone["old"].str.upper() != zone["new"].str.upper())
    up = zone["new"].map(pdx18_hpa) > zone["old"].map(pdx18_hpa)
    if version == "to_mixed_from_other":   # only lots moved into a mixed-use zone from residential, employment or industrial
        up = up & zone["new"].str.upper().isin(MIXED_NEW) & ~zone["old"].str.upper().isin(list(PDX18_FAR))
    reform = pd.DataFrame({"up": up[changed].fillna(False).values, "geometry": parcels.geometry[changed].values})
    st = pd.concat([read(d / "max_stops.geojson"), read(d / "streetcar_stops.geojson")], ignore_index=True)
    perm = pd.concat([read(d / "residential_permits.geojson"), read(d / "commercial_permits.geojson")], ignore_index=True)
    perm["date"] = pd.to_datetime(perm.ISSUED, unit="ms")
    perm["units"] = pd.to_numeric(perm.NUMNEWUNITS, errors="coerce").fillna(0)
    perm = perm[perm.units > 0]
    eff = pd.Timestamp("2018-05-24")
    windows = {"before": (pd.Timestamp("2012-01-01"), pd.Timestamp("2017-12-31")),
               "after": (pd.Timestamp("2019-01-01"), pd.Timestamp("2023-12-31"))}
    out = share_case(f"portland_2018_{version}", reform, parcels, st, perm, eff, windows)
    out["lots_zone_changed"] = int(changed.sum())
    return out


def austin(version: str) -> dict:
    """Austin TOD regulating plans (Plaza Saltillo, MLK, Lamar/Justin) as one case; day-one maps in
    reference/tod_austin_dayone_regulating_plans.geojson (committed before permits were loaded)."""
    d = RAW / "tod_new_cities" / "austin"
    r = read(REFERENCE / "tod_austin_dayone_regulating_plans.geojson")
    r = r[r.SUBDISTRICT_MAP != "TROW"].copy()
    r["up"] = True
    if version.endswith("no_ldr"):
        r.loc[r.SUBDISTRICT_MAP == "TODLDR", "up"] = False
    st = read(d / "metrorail_stations.geojson")
    st = st[st.NAME.str.contains("Saltillo|MLK|Crestview", case=False, na=False)]
    parcels = read(d / "tcad_parcels.geojson")
    pm = pd.read_json(d / "permits.json")
    pm = pm.dropna(subset=["latitude", "longitude"])
    perm = pm.copy()
    perm["x"], perm["y"] = X.transform(pm.longitude.values.astype(float), pm.latitude.values.astype(float), 4326, CRS)
    perm["date"] = pd.to_datetime(perm.issue_date)
    perm["units"] = pd.to_numeric(perm.housing_units, errors="coerce").fillna(0)
    perm = perm[perm.units > 0]
    if version.startswith("2005"):
        eff, windows = pd.Timestamp("2005-05-01"), {"before": (pd.Timestamp("1999-01-01"), pd.Timestamp("2004-12-31")),
                                                     "after": (pd.Timestamp("2006-01-01"), pd.Timestamp("2010-12-31"))}
    else:
        eff, windows = pd.Timestamp("2009-03-01"), {"before": (pd.Timestamp("2003-01-01"), pd.Timestamp("2008-12-31")),
                                                     "after": (pd.Timestamp("2010-01-01"), pd.Timestamp("2014-12-31"))}
    out = share_case(f"austin_{version}", r, parcels, st, perm, eff, windows)
    out["stop_open_at_reform"] = "no (MetroRail opened March 2010)"
    return out


def slc_2010(version: str) -> dict:
    """Salt Lake City TSA district (Ordinance 59 of 2010, effective 11 Aug 2010). Map: 2020 zoning snapshot
    (hindsight risk). Homes: Utah Housing Unit Inventory, units by approximate year built (completions)."""
    st = slc_stations()
    tsa_names = slc_tsa_stations()
    z = read(RAW / "tod_slc" / "slc_zoning_2020_jacobs.geojson")
    tsa = z[z["ZONING"].str.startswith("TSA")].copy()
    rx, ry = rep_xy(list(tsa.geometry))
    ni, _ = X.nearest_lowest(rx, ry, st.x.values, st.y.values)
    tsa["station"] = st.name.values[ni]
    reform = tsa[tsa["station"].isin(tsa_names)].copy()
    reform["up"] = True
    if version == "core_only":
        reform["up"] = reform["ZONING"].str.endswith("-C")
    stops = st[st["name"].isin(tsa_names)]
    h = read(RAW / "tod_new_cities" / "slc" / "housing_unit_inventory.geojson")
    h = h[X.nonempty(list(h.geometry))].reset_index(drop=True)
    yr = pd.to_numeric(h.APX_BLT_YR, errors="coerce")
    hx, hy = rep_xy(list(h.geometry))
    homes = pd.DataFrame({"units": pd.to_numeric(h.UNIT_COUNT, errors="coerce").fillna(0),
                          "date": pd.to_datetime(yr.fillna(0).astype(int).astype(str) + "-07-01", errors="coerce"),
                          "x": hx, "y": hy})
    homes = homes[homes.units > 0]
    eff = pd.Timestamp("2010-08-11")
    windows = {"before": (pd.Timestamp("2004-01-01"), pd.Timestamp("2009-12-31")),
               "after": (pd.Timestamp("2011-01-01"), pd.Timestamp("2015-12-31"))}
    out = share_case(f"slc_2010_{version}", reform[["up", "geometry"]], h[["geometry"]], stops, homes, eff, windows)
    out["stop_open_at_reform"] = "no (opened April 2013)"
    out["map"] = "2020 boundary, hindsight risk"
    out["homes_source"] = "Utah Housing Unit Inventory (completions by approximate year built; standing homes only)"
    return out


def slc_stations() -> pd.DataFrame:
    """run_tod_slc_census.stations() (that script still loads the geo stack at import): UTA rail stops by name, the
    mean of their platforms' coordinates, as x, y in CRS 5070."""
    import json
    s = pd.DataFrame(json.load(open(RAW / "tod_slc" / "uta_stops.json")))
    s = s[s["stop_type_text"].str.contains("rail", case=False, na=False)]
    s["name"] = s["stop_name"].str.strip()
    s.loc[s["name"].str.upper() == "RIVER TRAIL STATION", "name"] = "River Trail Station"
    s = s.groupby("name", as_index=False)[["stop_lat", "stop_lon"]].mean()
    s["x"], s["y"] = X.transform(s.stop_lon.values, s.stop_lat.values, 4326, CRS)
    return s


def slc_tsa_stations() -> list[str]:
    """run_tod_slc_census.TSA_STATIONS, read from that script's source (importing it would load the geo stack)."""
    import ast
    tree = ast.parse((ROOT / "scripts" / "run_tod_slc_census.py").read_text())
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "TSA_STATIONS" for t in n.targets):
            return ast.literal_eval(n.value)
    raise KeyError("TSA_STATIONS")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True, choices=["denver_2018", "portland_2020", "portland_2018", "austin", "slc_2010"])
    a = ap.parse_args(argv)
    rows = ([denver_2018("main"), denver_2018("base_zone_only")] if a.case == "denver_2018"
            else [portland_2020("main"), portland_2020("no_rh_rm4"), portland_2020("no_r1_rm2")] if a.case == "portland_2020"
            else [portland_2018("main"), portland_2018("to_mixed_from_other")] if a.case == "portland_2018"
            else [austin("2009_main"), austin("2009_no_ldr"), austin("2005_main")] if a.case == "austin"
            else [slc_2010("main"), slc_2010("core_only")])
    T = pd.DataFrame(rows)
    sb, sa = T.share_before, T.share_after
    T["pred_drift"] = sb + A + B * (sb - 0.5)
    T["pred_average_change"] = sb + AVG
    T["pred_same_share"] = sb
    for k in ("drift", "average_change", "same_share"):
        p = T[f"pred_{k}"]
        T[f"abslog_{k}"] = np.abs(np.log(p / sa)).where((p > 0) & (sa > 0))
    T.round(4).to_csv(REFERENCE / f"tod_new_city_test_{a.case}.csv", index=False)
    pd.set_option("display.width", 250)
    print(T.round(3).T.to_string())


if __name__ == "__main__":
    main()
