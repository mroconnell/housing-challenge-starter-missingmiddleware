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

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

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
    z = gpd.read_file(d / "zone_map_amendments.geojson").to_crs(CRS)
    r = z[(z.ORD_YEAR == 2018) & z.ORD_NUM.isin([15, 17])].copy()
    io_new = r.OVERLAY_DISTRICT.fillna("").str.contains("IO-1") & ~r.FROM_OVERLAY_DIST_1.fillna("").str.contains("IO-1")
    base_up = r.ZONE_DISTRICT.map(stories) > r.FROM_ZONE_1.map(stories)
    r["up"] = (io_new | base_up) if version == "main" else base_up
    st = gpd.read_file(d / "rail_stations.geojson").to_crs(CRS)
    yo = pd.to_numeric(st.YEAR_OPEN, errors="coerce")
    st = st[(st.STATUS == "Existing") & (yo <= 2018)]
    p = gpd.read_file(d / "parcels.geojson").to_crs(CRS)
    p = p[p.geometry.notna()].copy()
    p["pt"] = p.geometry.representative_point()
    pts = gpd.GeoDataFrame(p[["SCHEDNUM"]], geometry=p["pt"], crs=CRS)
    j = gpd.sjoin(pts, r[["up", "geometry"]], predicate="within", how="left")
    j = j[~j.index.duplicated()]
    inref = j.index_right.notna()
    up = j["up"].fillna(False).astype(bool) & inref
    area = r.geometry.union_all()
    dist_area = pts.distance(area)
    ring = (~inref) & (dist_area <= RING_M)
    dist_st = pts.geometry.apply(lambda g: st.distance(g).min())
    far = up & (dist_st > NEAR_M)   # item 48: upzoned lots more than 1/2 mile from rail open on the reform date
    lots = pd.DataFrame({"SCHEDNUM": p.SCHEDNUM.values, "acres": p.geometry.area.values / 4046.86,
                         "in_reform": inref.values, "upzoned": (up & ~far).values, "far_upzoned": far.values,
                         "study": (inref | ring).values})
    perm = pd.concat([gpd.read_file(d / "residential_permits.geojson").assign(src="residential"),
                      gpd.read_file(d / "commercial_permits.geojson").assign(src="commercial")], ignore_index=True)
    perm["UNITS"] = pd.to_numeric(perm.UNITS, errors="coerce").fillna(0)
    perm = perm[perm.CLASS.str.upper().eq("NEW BUILDING") & (perm.UNITS > 0) & perm.CANCEL.isna()].copy()
    perm["date"] = pd.to_datetime(perm.DATE_ISSUED, unit="ms")
    eff = pd.Timestamp("2018-02-12")
    windows = {"before": (pd.Timestamp("2012-07-11"), pd.Timestamp("2017-12-31")),
               "after": (pd.Timestamp("2019-01-01"), pd.Timestamp("2023-12-31"))}
    # permits are placed on the lot whose shape holds the permit point (schedule numbers change when lots are
    # merged or split after the permit; only 35% matched today's parcels by number); the number is the fallback
    perm = perm[perm.geometry.notna()].to_crs(CRS)
    pj = gpd.sjoin(perm[["geometry"]], gpd.GeoDataFrame({"lot": np.arange(len(p))}, geometry=p.geometry.values, crs=CRS),
                   predicate="within", how="left")
    pj = pj[~pj.index.duplicated()]
    perm["lot"] = pj["lot"].reindex(perm.index)
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


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True, choices=["denver_2018"])
    a = ap.parse_args(argv)
    rows = [denver_2018("main"), denver_2018("base_zone_only")]
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
