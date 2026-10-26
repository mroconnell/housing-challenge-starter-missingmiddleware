"""Philadelphia: the remapping that followed the 2012 zoning code (City Planning Commission district plans), fit set.

Inputs (data/raw/tod_cases/philadelphia/, fetched by scripts/fetch_tod_cases.py):
- permits_new_construction.csv: L&I permits of the new-construction types, with issue date, number of units and point.
- remapping.geojson: every zoning map change the City tracks, with existing and proposed district, bill number,
  enactment date, status and origination ("DistrictPlan" = the city's remapping of the 2012 code by district plan).
- zoning_basedistricts_<mmyyyy>.geojson: base-district snapshots March 2015 to December 2025.
- zoning_code_characteristics.json: the City's table of maximum height and FAR by district.
- parcels.geojson: Philadelphia Water Department parcels (land base).
- rail_stops.geojson: SEPTA rail, subway and trolley stops (BTS National Transit Map).
- ../census_2010_blocks/tabblock2010_42_pophu.zip.

Rules (uniform area rule, cases.uniform_areas, applied to each remapping bill, then stacked in event time):
- Members: remapping bills of origination DistrictPlan, enacted 2013-2020 (so that each has 6 before years from 2007,
  the first permit year, and 5 after years to 2025). Event year 0 is the bill's enactment year.
- Treatment: parcels inside a member's enacted polygons whose allowed residential intensity rose (PHL_LEVEL, an
  ordering built from the City's own height and FAR table), unless already at the law.
- Lots in any other enacted zoning change during the member's window (applicant, council or other district-plan
  bills), or whose base district differs between the March 2015 snapshot and the first snapshot after the window,
  are in no area.
- Outcome: units in new-construction permits (whole-building types only: ENTIRE, NEWCON, New Construction, New
  Construction (Stand Alone)); foundation, shell, fit-out and site permits are left out so a building is not counted
  twice. One record per permit number, and one per address point, unit count and 18 months (case_chicago.dedupe_staged),
  because the 2019-2020 change of permit system left some buildings in both systems. Project = parcel id (or point).
- Dose: most of the remapped districts have a height limit and no FAR (RSA-5, RM-1, CMX-2, CMX-2.5), so there is no
  defensible FAR dose: the case reports no effect per dose and stays out of per-FAR pooling. The share of treated
  acres where the City's table gives a FAR both before and after is reported.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from missing_middleware.paths import RAW
from missing_middleware.tod import cases as C

DIR = RAW / "tod_cases" / "philadelphia"
CRS_M = 32129  # NAD83 / Pennsylvania South (metres)
FIRST_YEAR, LAST_FULL_YEAR = 2007, 2025
MEMBER_YEARS = (2013, 2020)
WHOLE_BUILDING = {"ENTIRE", "NEWCON", "New Construction", "New Construction (Stand Alone)"}
# Allowed residential intensity, in order (City table: 38 ft single-family and rowhouse districts by lot size; RM-1
# and CMX-2 38 ft multi-family/mixed; CMX-2.5 55 ft; RM-2 FAR 0.7; RM-3 1.5; RMX-2 2.5; RM-4 3.5; CMX-3, CMX-4, RMX-3
# and IRMX FAR 5.0; CMX-5 FAR 12). The values are an ordering, not a dose. Industrial, parks and institutional: 0.
PHL_LEVEL = {"RSD-1": 1, "RSD-2": 2, "RSD-3": 3, "RSA-1": 4, "RSA-2": 5, "RSA-3": 6, "RTA-1": 6.5, "RSA-4": 7, "RSA-5": 8,
             "CA-1": 8, "CA-2": 8, "CMX-1": 8.5, "RM-2": 8.5, "RM-1": 9, "CMX-2": 9.5, "RM-3": 10, "RMX-1": 10, "CMX-2.5": 11,
             "SP-STA": 12, "RMX-2": 12, "RM-4": 13, "CMX-3": 14, "RMX-3": 14, "IRMX": 14, "CMX-4": 15, "SP-ENT": 15, "CMX-5": 16,
             "I-1": 0, "I-2": 0, "I-3": 0, "I-P": 0, "ICMX": 0, "SP-PO-A": 0, "SP-PO-P": 0, "SP-INS": 0, "SP-AIR": 0}
CODE_FAR = {"RM-2": 0.7, "RM-3": 1.5, "RM-4": 3.5, "RMX-1": 1.5, "RMX-2": 2.5, "RMX-3": 5.0, "CMX-3": 5.0, "CMX-4": 5.0,
            "CMX-5": 12.0, "IRMX": 5.0}


def norm(z) -> str | None:
    if not isinstance(z, str) or not z.strip():
        return None
    return re.sub(r"\s+", "", z.upper())


def zclass(z) -> str | None:
    z = norm(z)
    if z is None:
        return None
    if z.startswith(("RSD", "RSA", "RTA", "RM-")):
        return "res"
    if z.startswith(("RMX", "CMX", "IRMX")):
        return "mixed"
    if z.startswith(("CA-", "SP-STA", "SP-ENT")):
        return "com"
    if z.startswith(("I-", "ICMX")):
        return "ind"
    if z.startswith("SP-PO"):
        return "park"
    if z.startswith(("SP-INS", "SP-AIR")):
        return "inst"
    return None


def level(z) -> float:
    return float(PHL_LEVEL.get(norm(z) or "", np.nan))


def _snapshots():
    import glob
    out = {}
    for f in glob.glob(str(DIR / "zoning_basedistricts_*.geojson")):
        mm = re.search(r"_(\d{2})(\d{4})\.geojson$", f)
        out[pd.Timestamp(f"{mm.group(2)}-{mm.group(1)}-01")] = f
    return dict(sorted(out.items()))


_cache: dict = {}


def _load():
    import geopandas as gpd
    if _cache:
        return _cache
    parcels = gpd.read_file(DIR / "parcels.geojson").to_crs(CRS_M)
    parcels = parcels[parcels.geometry.notna() & ~parcels.geometry.is_empty].reset_index(drop=True)
    parcels["acres"] = parcels.geometry.area / C.SQM_PER_ACRE
    pts = gpd.GeoDataFrame(geometry=parcels.geometry.representative_point(), crs=CRS_M)
    snaps = _snapshots()
    zcols = {}
    for t, f in snaps.items():
        z = gpd.read_file(f).to_crs(CRS_M)
        col = "long_code" if "long_code" in z.columns else next(c for c in z.columns if c.lower() in ("zoning", "code", "zone"))
        j = gpd.sjoin(pts, z[[col, "geometry"]], how="left", predicate="within")
        zcols[t] = j[~j.index.duplicated()].reindex(pts.index)[col].map(norm)
    rm = gpd.read_file(DIR / "remapping.geojson").to_crs(CRS_M)
    rm["enacted"] = pd.to_datetime(rm["Enacted_Date"], errors="coerce", format="mixed")
    rm = rm[rm["ReMap_Status"].astype(str).str.startswith("Enacted") & rm["enacted"].notna()].reset_index(drop=True)
    rm["changes"] = rm["ExistCode"].map(norm) != rm["PropZone"].map(norm)
    p = pd.read_csv(DIR / "permits_new_construction.csv", dtype=str).drop_duplicates("permitnumber")
    p = p[p["typeofwork"].isin(WHOLE_BUILDING)].copy()
    p["units"] = pd.to_numeric(p["numberofunits"], errors="coerce").fillna(0)
    p["year"] = pd.to_numeric(p["permitissuedate"].str[:4], errors="coerce")
    p = p[(p["units"] > 0) & p["year"].notna()].dropna(subset=["lat", "lon"])
    pg = gpd.GeoDataFrame(p, geometry=gpd.points_from_xy(p["lon"].astype(float), p["lat"].astype(float)), crs=4326).to_crs(CRS_M)
    # the permit system changed in 2019-2020: the same building can appear in both systems, and staged permits remain;
    # keep one record per address point, unit count and 18-month window (as for Chicago)
    from missing_middleware.tod.case_chicago import dedupe_staged
    pg["x"], pg["y"], pg["issue_date"] = pg.geometry.x, pg.geometry.y, pg["permitissuedate"]
    n0 = len(pg)
    pg = dedupe_staged(pg)
    pg.attrs["merged"] = n0 - len(pg)
    pg["pix"] = C.locate_points(pg, parcels)
    pg["project"] = pg["parcel_id_num"].fillna(pg.geometry.x.round().astype(int).astype(str) + "_" + pg.geometry.y.round().astype(int).astype(str))
    stops = gpd.read_file(DIR / "rail_stops.geojson").to_crs(CRS_M).geometry
    _cache.update(parcels=parcels, pts=pts, snaps=snaps, zcols=zcols, rm=rm, permits=pg, stops=stops)
    return _cache


def build_member(bill: str) -> dict:
    d = _load()
    parcels, pts, zcols, rm, pg = d["parcels"], d["pts"], d["zcols"], d["rm"], d["permits"]
    mem = rm[rm["Bill_Number_TXT"].astype(str) == bill]
    eff = mem["enacted"].min()
    per = C.period_years(eff.year, FIRST_YEAR, LAST_FULL_YEAR)
    lo, hi = pd.Timestamp(f"{per['before'][0]}-01-01"), pd.Timestamp(f"{per['after'][-1]}-12-31")
    import geopandas as gpd
    j = gpd.sjoin(pts, mem[["ExistCode", "PropZone", "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated()].reindex(pts.index)
    in_mem = j["PropZone"].notna()
    snaps = list(zcols)
    first = zcols[snaps[0]]
    end_t = next((t for t in snaps if t > hi), snaps[-1])
    before_t = max([t for t in snaps if t <= eff] or [snaps[0]])
    z_before = np.where(in_mem, j["ExistCode"].map(norm), zcols[before_t])
    z_before = pd.Series(z_before, index=parcels.index)
    z_after = pd.Series(np.where(in_mem, j["PropZone"].map(norm), z_before), index=parcels.index)
    lv_b, lv_a = z_before.map(level), z_after.map(level)
    rose = in_mem & (lv_a > lv_b)
    other = rm[(rm["Bill_Number_TXT"].astype(str) != bill) & rm["changes"] & rm["enacted"].between(lo, hi)]
    oj = gpd.sjoin(pts, other[["geometry"]], how="inner", predicate="within")
    in_other = pd.Series(False, index=parcels.index)
    in_other.loc[oj.index.unique()] = True
    snap_change = (first.notna() & zcols[end_t].notna() & (first != zcols[end_t]))
    changed = in_other | (~in_mem & snap_change)
    eligible = z_before.map(zclass).isin(["res", "mixed", "com"])
    # restrict the work to 2 km around the member
    near = pts.geometry.within(mem.geometry.union_all().buffer(2000))
    sub = parcels[near].copy()
    area, rule = C.uniform_areas(sub, in_mem[near], rose[near], lv_b[near], lv_a[near], pd.Series(True, index=sub.index),
                                 changed[near], eligible[near], stations=d["stops"])
    sub["area"], sub["eligible"] = area, eligible[near]
    el = sub[sub["area"].notna() & sub["eligible"]]
    q = pg[pg["year"].between(per["before"][0], per["after"][-1])]
    q = q.assign(area=sub["area"].reindex(q["pix"]).values, eligible=sub["eligible"].reindex(q["pix"]).fillna(False).astype(bool).values)
    permits = q[q["area"].notna() & q["eligible"]][["project", "area", "year", "units"]].copy()
    permits["year"] = permits["year"].astype(int)
    oa = C.assign_areas(sub, in_mem[near], stations=None)
    q2 = q.assign(area=oa.reindex(q["pix"]).values)
    orig = (q2[q2["area"].notna() & q2["eligible"]][["project", "area", "year", "units"]].astype({"year": int}),
            sub[oa.notna() & sub["eligible"]].groupby(oa)["acres"].sum().to_dict())
    tr = el[el["area"] == C.TREAT]
    far_b, far_a = z_before.reindex(tr.index).map(CODE_FAR), z_after.reindex(tr.index).map(CODE_FAR)
    return {"bill": bill, "name": str(mem["Remapping_Name"].iloc[0]), "effective": eff, "per": per, "permits": permits,
            "acres": el.groupby("area")["acres"].sum().to_dict(), "original": orig, "treated": tr,
            "far_coverage": float(tr.loc[far_b.notna() & far_a.notna(), "acres"].sum() / tr["acres"].sum()) if len(tr) else np.nan,
            "rule": rule, "changes": pd.crosstab(z_before.reindex(tr.index), z_after.reindex(tr.index)).stack().loc[lambda s: s > 0].to_dict() if len(tr) else {}}


def build() -> tuple[C.CaseInputs, dict]:
    import geopandas as gpd
    d = _load()
    rm = d["rm"]
    dp = rm[(rm["Origination"] == "DistrictPlan") & rm["changes"] & rm["enacted"].dt.year.between(*MEMBER_YEARS)]
    bills = sorted(dp["Bill_Number_TXT"].astype(str).unique())
    allp, acres, orig_p, orig_a, diag, tr_all = [], {}, [], {}, {"members": {}}, []
    for b in bills:
        m = build_member(b)
        ok = m["acres"].get(C.TREAT, 0) > 0
        diag["members"][b] = {"name": m["name"], "enacted": str(m["effective"].date()), "acres": {k: round(v, 1) for k, v in m["acres"].items()},
                              "included": bool(ok), "far_coverage": None if np.isnan(m["far_coverage"]) else round(m["far_coverage"], 3)}
        if not ok:
            continue
        e0 = m["effective"].year
        for src, dst in ((m["permits"], allp), (m["original"][0], orig_p)):
            q = src.copy()
            q["year"] -= e0
            q["project"] = b + ":" + q["project"].astype(str)
            dst.append(q)
        for k, v in m["acres"].items():
            acres[k] = acres.get(k, 0.0) + v
        for k, v in m["original"][1].items():
            orig_a[k] = orig_a.get(k, 0.0) + v
        tr_all.append(m["treated"].assign(bill=b))
    tr = pd.concat(tr_all) if tr_all else pd.DataFrame()
    homes = {}
    bz = RAW / "tod_cases" / "census_2010_blocks" / "tabblock2010_42_pophu.zip"
    diag["included_members"] = sum(1 for v in diag["members"].values() if v["included"])
    diag["permits_merged_as_duplicates"] = int(d["permits"].attrs.get("merged", 0))
    diag["treated_acres_with_code_far_before_and_after_share"] = round(float(
        np.nansum([v["far_coverage"] * v["acres"].get(C.TREAT, 0) for v in diag["members"].values() if v["far_coverage"] is not None])
        / max(acres.get(C.TREAT, 0), 1e-9)), 3)
    if bz.exists() and len(tr):
        diag["homes_note"] = "per-1,000-homes sensitivity not computed for the stacked members (comparison areas overlap)"
    ci = C.CaseInputs(case="philadelphia_2012_remapping", role="fit", effective_year=0, first_year=-C.BEFORE_MAX,
                      last_full_year=max(C.AFTER_YEARS), permits=pd.concat(allp, ignore_index=True), acres=acres, homes=homes,
                      dose_table=None, parking_change="none code-wide (the /TOD overlay cuts minimums but was rarely mapped)",
                      mandate="no", dose_unit="none", original_spec=(pd.concat(orig_p, ignore_index=True), orig_a),
                      notes="district-plan remapping bills 2013-2020 stacked in event time; no FAR dose (height-only districts)")
    return ci, diag
