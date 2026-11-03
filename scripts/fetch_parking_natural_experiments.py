"""Feasibility checks for parking natural experiments N3 (San Diego 2019 TPA) and N4 (New York 2016 Transit Zone).

Rules: docs/parking/CAUSAL_FRAMEWORK_PLAN.md, section "Natural experiments N1-N4". This script counts records, lots
and fields only. It computes no outcome comparison (no inside-vs-outside rates, no before/after rates, no effects).

    python scripts/fetch_parking_natural_experiments.py fetch      # downloads -> data/raw/parking_natural_experiments/
    python scripts/fetch_parking_natural_experiments.py n3         # San Diego feasibility counts
    python scripts/fetch_parking_natural_experiments.py n4         # New York feasibility counts

Geometry: missing_middleware.geom, numpy and pandas only (scipy's cKDTree as geom itself uses it).
"""
from __future__ import annotations

import argparse, hashlib, io, json, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from missing_middleware import geom as G  # noqa: E402

RAW = ROOT / "data" / "raw" / "parking_natural_experiments"
SD_RAW = RAW / "san_diego"
NY_RAW = RAW / "nyc"
TOD_SD = ROOT / "data" / "raw" / "tod_radius_programs" / "san_diego"
UA = {"User-Agent": "housing-policy-model/0.1 (research; public data)"}
BAND_M = 183.0
FT = 0.3048006096  # US survey foot in metres

# N3 dates
SD_EFFECTIVE = pd.Timestamp("2019-04-24")   # O-21057, final passage 2019-03-25; outside the Coastal Overlay Zone
SD_BEFORE = (pd.Timestamp("2016-01-01"), SD_EFFECTIVE)      # [start, end)
SD_AFTER = (SD_EFFECTIVE, pd.Timestamp("2020-12-01"))       # [effective, 2020-11-30]
# N4 dates
NY_EFFECTIVE = pd.Timestamp("2016-03-22")

SOURCES = {
    "san_diego/o-21057.pdf": dict(
        url="https://www.sandiego.gov/sites/default/files/o-21057.pdf",
        licence="City of San Diego public record", note="Ordinance O-21057 (N.S.), TPA parking regulations"),
    "san_diego/ccc_th20d_aug2019_lcp-6-san-19-0063-1.pdf": dict(
        url="https://documents.coastal.ca.gov/reports/2019/8/Th20d/Th20d-8-2019-report.pdf",
        licence="California Coastal Commission public record",
        note="CCC staff report: LCP-6-SAN-19-0063-1 (TPA) filed 2019-05-22; 60-day limit extended one year"),
    "san_diego/parking_amenity_tpa_rtp2050.geojson": dict(
        url="https://webmaps.sandiego.gov/arcgis/rest/services/Hosted/ParkingAmenityTPA/FeatureServer/6",
        arcgis=True, licence="SanGIS end user use agreement (http://www.sangis.org/Legal_Notice.htm)",
        note="City of San Diego ParkingAmenityTPA: TPA based on the adopted SANDAG 2050 RTP (2015); hybrid of TPA "
             "outside the Coastal Zone and 'Parking Standards TPA' (PSTPA) inside it; features edited 2022-05 and 2023-07"),
    "san_diego/development_approvals_tod_subset.csv": dict(
        url=["https://seshat.datasd.org/development_permits/approvals_issued_datasd.csv",
             "https://seshat.datasd.org/development_permits/approvals_closed_datasd.csv"],
        licence="City of San Diego Open Data (ODC-PDDL per data.sandiego.gov)",
        note="Rows of the City's development approvals files whose APPROVAL_ID is in the TOD Housing Element permit "
             "layer; adds PROJECT_CREATE_DATE, PROJECT_DEEMEDCOMPLETE_DATE, APPROVAL_CREATE_DATE, GIS_APN. Full files "
             "(~0.6 GB and ~0.4 GB) not stored", filter_sd=True),
    "nyc/nyctransitzones_201601.zip": dict(
        url="https://www.nyc.gov/assets/planning/download/zip/data-maps/open-data/nyctransitzones_201601.zip",
        licence="NYC Open Data terms of use (no restrictions)",
        note="DCP BYTES archive: Transit Zones as adopted with ZQA (item nyctransitzones_201601, created 2016-05-22, "
             "published 2016-07-07), EPSG:2263"),
    "nyc/transitzones_metadata_2016.pdf": dict(
        url="https://www.nyc.gov/assets/planning/download/pdf/data-maps/open-data/transitzones_metadata.pdf?r=0219",
        licence="NYC Open Data terms of use", note="metadata for the 2016 Transit Zones file"),
    "nyc/appendixi_transit_zones_current.geojson": dict(
        url="https://data.cityofnewyork.us/api/geospatial/dpnc-b2hd?method=export&format=GeoJSON",
        licence="NYC Open Data terms of use",
        note="Current Appendix I Transit Zones (appendixi_transitzones_20241121; City of Yes 2024-11-21); for comparison only"),
    "nyc/appendixi_transit_zones_metadata_2024.pdf": dict(
        url="https://s-media.nyc.gov/agencies/dcp/assets/files/pdf/data-tools/bytes/appendixi_transit_zones_metadata.pdf",
        licence="NYC Open Data terms of use", note="metadata for the current Appendix I file"),
    "nyc/zqa_adopted_text_a02c05.pdf": dict(
        url="https://www.nyc.gov/assets/planning/download/pdf/plans-studies/zqa/zoning-text/a02c05.pdf",
        licence="NYC public record", note="ZQA zoning text, Article II Chapter 5 (Sections 25-25, 25-251, 25-252)"),
    "nyc/hpd_affordable_housing_production_by_building.csv": dict(
        url="https://data.cityofnewyork.us/api/views/hg8x-zxpr/rows.csv?accessType=DOWNLOAD",
        licence="NYC Open Data terms of use", note="HPD Affordable Housing Production by Building (hg8x-zxpr)"),
}


def _get(url: str, tries: int = 4) -> bytes:
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 ** (i + 1))
    raise RuntimeError(url)


def _arcgis_geojson(layer: str) -> dict:
    q = urllib.parse.urlencode({"where": "1=1", "outFields": "*", "outSR": 4326, "f": "geojson"})
    return json.loads(_get(f"{layer}/query?{q}"))


def _filter_sd(urls: list[str], out: Path) -> int:
    ids = {str(r["APPROVAL_ID"]) for r in json.loads((TOD_SD / "permits.json").read_text())}
    keep = ["DEVELOPMENT_ID", "PROJECT_ID", "PROJECT_STATUS", "PROJECT_PROCESSING_CODE", "PROJECT_CREATE_DATE",
            "PROJECT_DEEMEDCOMPLETE_DATE", "GIS_APN", "GIS_LATITUDE", "GIS_LONGITUDE", "JOB_BC_CODE", "APPROVAL_ID",
            "APPROVAL_TYPE", "APPROVAL_STATUS", "APPROVAL_CREATE_DATE", "APPROVAL_ISSUE_DATE", "APPROVAL_CLOSE_DATE",
            "APPROVAL_DU_NET_CHANGE", "APPROVAL_ADU_TOTAL"]
    parts = []
    for u in urls:
        req = urllib.request.Request(u, headers=UA)
        with urllib.request.urlopen(req, timeout=600) as r:
            for ch in pd.read_csv(r, usecols=keep, dtype=str, chunksize=200_000):
                ch = ch[ch["APPROVAL_ID"].isin(ids)].copy()
                ch["source_file"] = u.rsplit("/", 1)[-1]
                parts.append(ch)
    df = pd.concat(parts, ignore_index=True)
    df.to_csv(out, index=False)
    return len(df)


def fetch(only: list[str] | None = None) -> None:
    man_p = RAW / "_sources.json"
    man = json.loads(man_p.read_text()) if man_p.exists() else {}
    for name, s in SOURCES.items():
        if only and not any(o in name for o in only):
            continue
        p = RAW / name
        p.parent.mkdir(parents=True, exist_ok=True)
        t = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if s.get("arcgis"):
            gj = _arcgis_geojson(s["url"])
            p.write_text(json.dumps(gj))
            rows = len(gj.get("features", []))
        elif s.get("filter_sd"):
            rows = _filter_sd(s["url"], p)
        else:
            p.write_bytes(_get(s["url"]))
            rows = None
        man[name] = {"url": s["url"], "licence": s["licence"], "accessed": t, "rows": rows,
                     "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "note": s["note"]}
        man_p.write_text(json.dumps(man, indent=1))
        print(f"{name}: {p.stat().st_size:,} bytes, rows={rows}")


# ------------------------------------------------------------------------------------------------- geometry helpers
def _flatten_parts(polys: list) -> list:
    """Every part of every feature as its own single-part feature."""
    return [[part] for f in polys for part in f if len(part)]


def signed_edge_distance(px, py, polys: list, max_d: float):
    """(distance to the boundary of the union of the polygons, up to max_d; inf beyond) and inside flag.
    Segments lying inside another part are dropped so overlapping buffers give the union's outline."""
    from scipy.spatial import cKDTree
    parts = _flatten_parts(polys)
    px, py = np.asarray(px, float), np.asarray(py, float)
    inside = G.points_in_any(px, py, parts, union=True)
    seg, owner = G._segments(parts)
    mx, my = (seg[:, 0] + seg[:, 2]) / 2, (seg[:, 1] + seg[:, 3]) / 2
    drop = np.zeros(len(seg), bool)
    for k, part in enumerate(parts):
        other = owner != k
        hit = G.points_in_feature(mx[other], my[other], part, union=True)
        drop[np.flatnonzero(other)[hit]] = True
    seg = seg[~drop]
    out = np.full(len(px), np.inf)
    if not len(seg):
        return out, inside
    mid = (seg[:, :2] + seg[:, 2:]) / 2
    half = np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1]).max() / 2
    tree = cKDTree(mid)
    near = tree.query_ball_point(np.c_[px, py], r=max_d + half)
    for j, cand in enumerate(near):
        if not cand:
            continue
        s = seg[cand]
        ax, ay, bx, by = s[:, 0], s[:, 1], s[:, 2], s[:, 3]
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        t = np.clip(((px[j] - ax) * dx + (py[j] - ay) * dy) / np.where(L > 0, L, 1), 0, 1)
        d = np.hypot(ax + t * dx - px[j], ay + t * dy - py[j]).min()
        if d <= max_d:
            out[j] = d
    return out, inside


# ------------------------------------------------------------------------------------------------------------- N3
def _ms(s):
    return pd.to_datetime(pd.to_numeric(s, errors="coerce"), unit="ms", utc=True).dt.tz_localize(None)


def n3() -> dict:
    res: dict = {}
    pm = pd.DataFrame(json.loads((TOD_SD / "permits.json").read_text()))
    pm["issue"] = _ms(pm["APPROVAL_ISSUE_DATE"])
    pm["APPROVAL_ID"] = pm["APPROVAL_ID"].astype(str)
    res["fields_tod_layer"] = list(pm.columns)
    res["records_by_issue_year_2016_2020"] = pm[pm.issue.dt.year.between(2016, 2020)].issue.dt.year.value_counts().sort_index().to_dict()

    ap_p = SD_RAW / "development_approvals_tod_subset.csv"
    if ap_p.exists():
        ap = pd.read_csv(ap_p, dtype=str).drop_duplicates("APPROVAL_ID")
        pm = pm.merge(ap[["APPROVAL_ID", "PROJECT_CREATE_DATE", "PROJECT_DEEMEDCOMPLETE_DATE", "APPROVAL_CREATE_DATE",
                          "GIS_APN"]], on="APPROVAL_ID", how="left")
        for c in ("PROJECT_CREATE_DATE", "PROJECT_DEEMEDCOMPLETE_DATE", "APPROVAL_CREATE_DATE"):
            pm[c] = pd.to_datetime(pm[c], errors="coerce")
        res["join_matched"] = int(pm["APPROVAL_CREATE_DATE"].notna().sum())
        res["join_matched_project_create"] = int(pm["PROJECT_CREATE_DATE"].notna().sum())
        y = pm[pm.issue.dt.year.between(2016, 2020)]
        res["match_by_issue_year"] = y.groupby(y.issue.dt.year)["PROJECT_CREATE_DATE"].apply(lambda s: f"{s.notna().sum()}/{len(s)}").to_dict()
    else:
        pm["PROJECT_CREATE_DATE"] = pd.NaT
        pm["GIS_APN"] = np.nan
    # application date: the earlier of project creation and approval creation. Records migrated to Accela carry a
    # PROJECT_CREATE_DATE of the migration (e.g. 2024) but keep the original APPROVAL_CREATE_DATE.
    pm["app"] = pm[["PROJECT_CREATE_DATE", "APPROVAL_CREATE_DATE"]].min(axis=1) if "APPROVAL_CREATE_DATE" in pm else pd.NaT
    res["unmatched_by_source"] = pm[pm["app"].isna()].RECORD_DATA_SOURCE.value_counts().to_dict()
    res["records_by_application_year_2016_2020"] = pm[pm.app.dt.year.between(2016, 2020)].app.dt.year.value_counts().sort_index().to_dict()

    # new homes: TOTAL_DU > 0 net of ADU/JADU-only permits
    adu = pm["TOTAL_ADU"].fillna(0) + pm["TOTAL_JADU"].fillna(0)
    pm["new_homes"] = (pm["TOTAL_DU"].fillna(0) - adu) > 0
    pm["mf2"] = (pm["TOTAL_DU"].fillna(0) - adu) >= 2
    pm = pm[pm.new_homes & pm.LAT_JOB.notna()].copy()

    # lots: GIS_APN from the approvals join; else nearest parcel centroid within 100 ft; else rounded coordinates
    x, y = G.transform(pm.LNG_JOB.values, pm.LAT_JOB.values, 4326, 2230)
    pm["x"], pm["y"] = x, y
    par = pd.read_csv(TOD_SD / "county_parcels.csv", usecols=["apn", "x_coord", "y_coord"], dtype={"apn": str})
    par = par.dropna(subset=["x_coord", "y_coord"])
    i, d = G.nearest(x, y, par.x_coord.values, par.y_coord.values, max_distance=100)
    near_apn = np.where(i >= 0, par.apn.values[np.clip(i, 0, None)], None)
    apn = pm["GIS_APN"].astype(str).str.replace(r"\D", "", regex=True).str[:8]
    near8 = pd.Series(near_apn, index=pm.index).astype(str).str[:8]
    pm["lot"] = np.where(apn.str.len() == 8, "apn:" + apn, np.where(pd.notna(near_apn), "apn:" + near8,
                         "xy:" + pm.LAT_JOB.round(4).astype(str) + "," + pm.LNG_JOB.round(4).astype(str)))
    res["lot_key_source"] = {"GIS_APN (approvals join)": int((apn.str.len() == 8).sum()),
                             "nearest parcel <=100 ft": int(((apn.str.len() != 8) & pd.notna(near_apn)).sum()),
                             "rounded coords": int(((apn.str.len() != 8) & pd.isna(near_apn)).sum())}

    lines = {
        "A_rtp2050_TPA_non_coastal (2019-era line)": (SD_RAW / "parking_amenity_tpa_rtp2050.geojson", "Transit Priority Area"),
        "A2_rtp2050_TPA_plus_PSTPA (whole hybrid layer)": (SD_RAW / "parking_amenity_tpa_rtp2050.geojson", None),
        "B_sandag_2022 (TOD line)": (TOD_SD / "transit_priority_areas_sandag_2022.geojson", None),
        "C_city_current_2026": (TOD_SD / "transit_priority_areas.geojson", None),
    }
    max_ft = BAND_M / FT
    tables = {}
    for name, (path, keep) in lines.items():
        if not path.exists():
            continue
        L = G.read_geojson(path)
        if keep is not None:
            nm = L.attrs.get("name", L.attrs.get("NAME"))
            L = L.subset(nm.values == keep)
        L = L.to_crs(2230)
        dist, inside = signed_edge_distance(pm.x.values, pm.y.values, L.polys, max_ft)
        sub = pm.assign(dist_m=dist * FT, inside=inside)
        sub = sub[np.isfinite(sub.dist_m)]
        rows = []
        for datecol, dlabel in (("app", "application (earliest project/approval create)"), ("issue", "issue (flagged)")):
            for wname, (a, b) in (("before 2016-01-01..2019-04-23", SD_BEFORE), ("after 2019-04-24..2020-11-30", SD_AFTER)):
                w = sub[(sub[datecol] >= a) & (sub[datecol] < b)]
                for side, m in (("inside", w.inside), ("outside", ~w.inside)):
                    ww = w[m]
                    rows.append({"date": dlabel, "window": wname, "side": side, "records": len(ww),
                                 "lots": ww.lot.nunique(), "lots_25m_donut_dropped": ww[ww.dist_m > 25].lot.nunique(),
                                 "lots_2plus_homes": ww[ww.mf2].lot.nunique()})
        tables[name] = pd.DataFrame(rows)
    res["tables"] = tables
    return res


# ------------------------------------------------------------------------------------------------------------- N4
def n4() -> dict:
    res: dict = {}
    h = pd.read_csv(NY_RAW / "hpd_affordable_housing_production_by_building.csv", dtype=str)
    res["fields"] = list(h.columns)
    res["rows"] = len(h)
    h["start"] = pd.to_datetime(h["Project Start Date"], errors="coerce")
    res["construction_type"] = h["Reporting Construction Type"].value_counts(dropna=False).to_dict()
    for c in ("Latitude", "Longitude", "Latitude (Internal)", "Longitude (Internal)", "Total Units"):
        h[c] = pd.to_numeric(h[c], errors="coerce")
    h["lat"] = h["Latitude"].fillna(h["Latitude (Internal)"])
    h["lon"] = h["Longitude"].fillna(h["Longitude (Internal)"])
    nc = h[h["Reporting Construction Type"].str.lower().eq("new construction")].copy()
    yr = nc.start.dt.year
    res["new_construction_by_start_year"] = yr[yr.between(2014, 2019)].value_counts().sort_index().to_dict()
    res["new_construction_missing_coords_by_year"] = nc[yr.between(2014, 2019) & nc.lat.isna()].start.dt.year.value_counts().sort_index().to_dict()
    res["start_date_range"] = (str(h.start.min().date()), str(h.start.max().date()))
    nc = nc[nc.lat.notna() & yr.between(2014, 2019)].copy()
    x, y = G.transform(nc.lon.values, nc.lat.values, 4326, 2263)
    tables = {}
    for name, path in (("2016_nyctransitzones_201601", NY_RAW / "nyctransitzones_201601.zip"),
                       ("current_appendixI_2024", NY_RAW / "appendixi_transit_zones_current.geojson")):
        if not path.exists():
            continue
        L = G.read_any(path).to_crs(2263)
        dist, inside = signed_edge_distance(x, y, L.polys, BAND_M / FT)
        sub = nc.assign(dist_m=dist * FT, inside=inside)
        sub = sub[np.isfinite(sub.dist_m)]
        rows = []
        for yv in range(2014, 2020):
            for side, m in (("inside", sub.inside), ("outside", ~sub.inside)):
                w = sub[m & (sub.start.dt.year == yv)]
                rows.append({"start_year": yv, "side": side, "buildings": len(w), "projects": w["Project ID"].nunique(),
                             "homes_total_units": int(w["Total Units"].fillna(0).sum())})
        t = pd.DataFrame(rows)
        win = []
        for wname, ys in (("before 2014-2015", (2014, 2015)), ("after 2017-2019", (2017, 2019))):
            for side in ("inside", "outside"):
                s = t[(t.side == side) & t.start_year.between(*ys)]
                win.append({"window": wname, "side": side, "buildings": int(s.buildings.sum()),
                            "homes_total_units": int(s.homes_total_units.sum())})
        tables[name] = (t, pd.DataFrame(win))
    res["tables"] = tables
    return res


def _print(res: dict) -> None:
    for k, v in res.items():
        if k == "tables":
            for name, t in v.items():
                print(f"\n=== {name}")
                for tt in (t if isinstance(t, tuple) else (t,)):
                    print(tt.to_string(index=False))
        else:
            print(f"{k}: {v}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["fetch", "n3", "n4"])
    ap.add_argument("--only", nargs="*", help="fetch: substrings of source names to fetch")
    a = ap.parse_args()
    if a.step == "fetch":
        fetch(a.only)
    elif a.step == "n3":
        _print(n3())
    else:
        _print(n4())


if __name__ == "__main__":
    main()
