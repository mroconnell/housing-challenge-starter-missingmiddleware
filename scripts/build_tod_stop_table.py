"""Stop table for a stop-based reform model (owner, 2026-11-02): basic data by stop, with sanity checks. No models.

One row per stop per case:
  - the station-area lot study's cases (data/processed/tod_station_area/lots_*.parquet: 16 places, New York and
    Philadelphia with one case per rezoning), stops exactly as the lot tables were built
    (scripts/run_tod_station_checks.py stops_for(); New York and Philadelphia: station_cases/nyc_phl.stops() with the
    group each stop has in that case's lot table);
  - Seattle Roosevelt 2012 (candidate, data/processed/tod_station_area/candidates/);
  - Wisconsin's 266 rail/rapid stops (reference/tod_stops.csv flag_a_rapid == 1) merged into stations as in
    scripts/build_tod_station_wisconsin.py (Milwaukee and Madison: the lot table's stations; Kenosha and any other
    place: merged the same way, no lot table).

Station = stop points within 150 m merged (union of 75 m buffers; geom_extra_station.merge_within); station point = the
centroid of the merged part. For each station the member points are rebuilt from the same source the case used and
matched to the station point (match distance is a column, so a mismatch shows).

Columns are described in docs/tod/STOP_TABLE.md. Sources: lot tables (local), agency GTFS feeds and ridership files in
data/raw/tod_stop_table/ (manifest.json there and in ridership/), New York subway station layer (Construction_type),
Denver RTD station layer (YEAR_OPEN). OpenStreetMap is not used (ODbL share-alike, owner decision D5).

    .venv/bin/python scripts/build_tod_stop_table.py            # writes reference/tod_stop_table.csv
    .venv/bin/python scripts/build_tod_stop_table.py --checks   # prints the sanity checks from the written table
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import zipfile
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware import geom_extra_station as X  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

CRS = 5070
QUARTER, HALF, MILE = 402.0, 805.0, 1609.0
LOTDIR = ROOT / "data" / "processed" / "tod_station_area"
SRC = RAW / "tod_stop_table"
OUT = Path(os.environ.get("STOP_TABLE_OUT", REFERENCE / "tod_stop_table.csv"))
STAGE1 = Path(os.environ.get("STOP_TABLE_STAGE1", LOTDIR / "stop_table_stage1.pkl"))   # local cache (stops + surroundings)
BANDS = {"q1": "0-1/4", "q2": "1/4-1/2", "m1": "1/2-1"}
TARGET_DAY = date(2026, 11, 10)      # a Tuesday; each feed uses the nearest Tuesday it covers


# =========================================================================== cases and stops

def lot_cases() -> dict[str, Path]:
    out = {p.stem[5:]: p for p in sorted(LOTDIR.glob("lots_*.parquet"))}
    out["seattle_roosevelt_2012"] = LOTDIR / "candidates" / "lots_seattle_roosevelt_2012.parquet"
    only = [c for c in os.environ.get("STOP_TABLE_CASES", "").split(",") if c]     # quick test runs only
    return {k: v for k, v in out.items() if k in only} if only else out


def city_of(case: str) -> str:
    k = case.split("_")[0]
    return {"nyc": "New York", "phl": "Philadelphia", "la": "Los Angeles", "san": "San Diego", "honolulu": "Honolulu",
            "chicago": "Chicago", "denver": "Denver", "portland": "Portland", "austin": "Austin", "slc": "Salt Lake City",
            "seattle": "Seattle", "bellevue": "Bellevue", "stpaul": "Saint Paul", "charlotte": "Charlotte"}[k]


def eff_of(case: str):
    from station_cases import chicago as CH, cluster_north as N, cluster_west as W, nyc_phl as NP
    import build_tod_station_lot_table as B
    for d in (B.CASES, CH.CASES, N.CASES, NP.CASES):
        if case in d and "eff" in d[case]:
            return int(d[case]["eff"])
    if case in W.CASES:
        return int(W.CASES[case]["before"][1]) + 1
    return np.nan


def ntm() -> pd.DataFrame:
    s = pd.DataFrame(json.load(open(RAW / "tod_census_cases" / "ntm_rail_stops.json"))).dropna(subset=["stop_lat", "stop_lon"])
    s["x"], s["y"] = X.transform(s.stop_lon.values.astype(float), s.stop_lat.values.astype(float), 4326, CRS)
    return s


def ptype_of(loc) -> str:
    v = str(loc).strip()
    return {"1": "station (parent point)", "2": "entrance", "3": "generic node", "4": "boarding area"}.get(v, "platform/stop")


def members_frame(case: str) -> list[pd.DataFrame]:
    """Raw stop points for the case's stations, as a list of groups merged separately (columns x, y, name, ptype,
    ptype_src). Mirrors the stop builders named in the module docstring."""
    from station_cases import cluster_north as N, cluster_west as W
    if case in ("la_toc_2017", "san_diego_2021"):
        box = (-118.95, 33.70, -117.65, 34.35) if case == "la_toc_2017" else (-117.30, 32.53, -116.90, 32.95)
        s = ntm()
        s = s[s.stop_lon.between(box[0], box[2]) & s.stop_lat.between(box[1], box[3])]
        g = pd.DataFrame({"x": s.x, "y": s.y, "name": s.stop_name, "ptype": s.location_type.map(ptype_of),
                          "ptype_src": "NTM location_type", "type_text": s.stop_type_text.str.strip('"')})
        if case == "la_toc_2017":
            gl = pd.DataFrame(json.load(open(RAW / "tod_census_cases" / "ntm_la_g_line.json")))
            x, y = X.transform(gl.stop_lon.values.astype(float), gl.stop_lat.values.astype(float), 4326, CRS)
            g = pd.concat([g, pd.DataFrame({"x": x, "y": y, "name": gl.stop_name, "ptype": gl.get("location_type", pd.Series("", index=gl.index)).map(ptype_of),
                                            "ptype_src": "NTM location_type", "type_text": "G Line (rapid)"})], ignore_index=True)
        return [g.reset_index(drop=True)]
    if case == "honolulu_2017":
        import build_tod_station_lot_table as B
        r = X.read_vector(B.RP / "honolulu" / "rail_stations.geojson", dst=CRS)
        return [pd.DataFrame({"x": r.x.values, "y": r.y.values, "name": r.station_name_FEIS.values, "ptype": "station point (city layer)",
                              "ptype_src": "city layer", "type_text": "Skyline"}), "nomerge"]
    if case.startswith("chicago"):
        s = ntm()
        s = s[s.stop_lon.between(-88.4, -87.5) & s.stop_lat.between(41.4, 42.5) & s.ntd_id.astype(str).isin(["50066", "50118"])]
        out = []
        for t, gg in s.groupby(np.where(s.ntd_id.astype(str) == "50066", "CTA rail", "Metra")):
            out.append(pd.DataFrame({"x": gg.x, "y": gg.y, "name": gg.stop_name, "ptype": gg.location_type.map(ptype_of),
                                     "ptype_src": "NTM location_type", "type_text": t}).reset_index(drop=True))
        return out
    if case in W.CASES:
        poly = W.coverage_poly(case)
        if case == "slc_2010":
            s = ntm()
            s = s[s.stop_lon.between(-112.2, -111.7) & s.stop_lat.between(40.6, 40.9) & s.stop_type_text.str.contains("Light rail")]
            g = pd.DataFrame({"x": s.x, "y": s.y, "name": s.stop_name, "ptype": s.location_type.map(ptype_of),
                              "ptype_src": "NTM location_type", "type_text": "Light rail"})
        else:
            r = W.raw_stops(case)
            g = pd.DataFrame({"x": r.x, "y": r.y, "name": r.stop_name, "ptype": "station point (agency layer)",
                              "ptype_src": "agency layer", "type_text": r.stop_type_text})
            if case == "denver_2018":
                d = X.read_vector(W.NC / "denver" / "rail_stations.geojson", dst=CRS)
                d = d[d.STATUS == "Existing"]
                g["year_open"] = pd.to_numeric(d.YEAR_OPEN, errors="coerce").values
        g = g[poly.contains(g.x.values, g.y.values)]
        return [g.reset_index(drop=True)]
    if case.startswith(("nyc_", "phl_")):
        from station_cases import nyc_phl as NP
        if case.startswith("nyc_"):
            r = X.read_vector(NP.NYC_DIR / "subway_stations.geojson", dst=CRS)
            return [pd.DataFrame({"x": r.x.values, "y": r.y.values, "name": r.STATION.values, "ptype": "station-line point (city layer)",
                                  "ptype_src": "NYC subway station layer TYPE", "type_text": "Subway",
                                  "grade_raw": r.Construction_type.values, "line": r.LINE.astype(str).str.strip().values})]
        from missing_middleware import geom as GM
        g = X.read_vector(NP.PHL_DIR / "rail_stops.geojson", dst=CRS)
        g = g[g.location_type.astype(str).isin(["Null", "0", "None", "nan", ""])].copy()
        g["kind"] = g.stop_type_text.str.strip('"').replace({"Subway, Metro": "Subway/elevated", "Tram, Streetcar, Light rail": "Trolley"})
        p = X.read_vector(RAW / "census_cb_2024" / "cb_2024_us_place_500k.zip", dst=CRS, columns=["NAME", "STATEFP"])
        poly = list(p[(p.STATEFP == "42") & (p.NAME == "Philadelphia")].geometry)
        g = g[GM.points_in_any(g.x.values, g.y.values, poly, union=True)]
        return [pd.DataFrame({"x": gg.x.values, "y": gg.y.values, "name": gg.stop_name.values, "ptype": gg.location_type.map(ptype_of).values,
                              "ptype_src": "NTM location_type (platforms only kept by the builder)", "type_text": k})
                for k, gg in g.groupby("kind")]
    # cluster_north (Seattle, Bellevue, Saint Paul, Charlotte): the case's rail_stops.geojson (NTM extract)
    g = X.read_vector(N.TC / N.META[case]["stops"] / "rail_stops.geojson", dst=CRS)
    g = g[g.x.notna()].reset_index(drop=True)
    return [pd.DataFrame({"x": g.x.values, "y": g.y.values, "name": g.stop_name.values, "ptype": g.location_type.map(ptype_of).values,
                          "ptype_src": "NTM location_type", "type_text": g.stop_type_text.str.strip('"').values})]


def clusters(groups: list) -> list[pd.DataFrame]:
    """Merge each group (150 m) and return one frame of members per station: cx, cy, member rows."""
    nomerge = len(groups) == 2 and isinstance(groups[1], str)
    out = []
    for g in groups[:1] if nomerge else groups:
        if nomerge:
            for i in range(len(g)):
                out.append((float(g.x.iloc[i]), float(g.y.iloc[i]), g.iloc[[i]]))
            continue
        cx, cy, mem = X.merge_within(g.x.values, g.y.values, 75.0)
        for a, b, m in zip(cx, cy, mem):
            out.append((a, b, g.iloc[m]))
    return out


def attach_members(S: pd.DataFrame, cl: list) -> pd.DataFrame:
    """Match each station point to the rebuilt merged part (nearest centroid) and summarize its member points."""
    cxy = np.array([[a, b] for a, b, _ in cl])
    d, i = cKDTree(cxy).query(np.c_[S.x.values, S.y.values])
    rows = []
    for k, (dd, ii) in enumerate(zip(d, i)):
        m = cl[ii][2]
        pts = np.c_[m.x.values, m.y.values]
        foot = float(np.max(np.hypot(*(pts[:, None, :] - pts[None, :, :]).transpose(2, 0, 1)))) if len(pts) > 1 else 0.0
        pt = m.ptype.value_counts()
        r = {"member_match_m": round(float(dd), 2), "n_points_merged": len(m), "footprint_m": round(foot, 1),
             "n_platform_points": int(pt.get("platform/stop", 0) + pt.get("station-line point (city layer)", 0)
                                      + pt.get("station point (agency layer)", 0) + pt.get("station point (city layer)", 0)),
             "n_entrance_points": int(pt.get("entrance", 0)), "n_parent_points": int(pt.get("station (parent point)", 0)),
             "point_types": "; ".join(f"{a} {b}" for a, b in pt.items()), "point_type_source": m.ptype_src.iloc[0],
             "n_names_merged": m.name.astype(str).str.strip().nunique(),
             "names_merged": " | ".join(sorted(set(m.name.astype(str).str.strip())))[:300],
             "_mx": m.x.values, "_my": m.y.values}
        if "grade_raw" in m:
            gr = m.grade_raw.dropna().map({"Sub": "underground", "Elv": "elevated", "Via": "elevated", "Cut": "open cut",
                                           "Fil": "embankment"}).dropna()
            r["grade"] = "/".join(sorted(set(gr))) if len(gr) else "unknown"
            r["grade_source"] = "NYC subway station layer Construction_type" if len(gr) else ""
            r["lines"] = ", ".join(sorted(set(m.line)))
        if "year_open" in m:
            yo = m.year_open.dropna()
            if len(yo):
                r["opening_year"] = int(yo.min())
                r["opening_year_source"] = "RTD station layer YEAR_OPEN (earliest line at the station)"
        rows.append(r)
    return pd.concat([S.reset_index(drop=True), pd.DataFrame(rows)], axis=1)


def stops_for_case(case: str, lot_path: Path, cache: dict) -> pd.DataFrame:
    import run_tod_station_checks as C
    if case.startswith(("nyc_", "phl_")):
        from station_cases import nyc_phl as NP
        city = case.split("_")[0]
        S0 = NP.stops(city)
        g = pd.read_parquet(lot_path, columns=["stop_id", "group"]).groupby("stop_id").group.first()
        S = S0[S0.stop_id.isin(g.index)].copy()
        S["group"] = S.stop_id.map(g)
        key = city
    else:
        S = C.stops_for(case).copy()
        if case not in ("seattle_roosevelt_2012",):
            C.check_stops(case, S) if (LOTDIR / f"lots_{case}.parquet").exists() else None
        key = case if not case.startswith("chicago") else "chicago"
    if key not in cache:
        cache[key] = clusters(members_frame(case))
    return attach_members(S, cache[key])


# =========================================================================== Wisconsin

def wisconsin_stops() -> pd.DataFrame:
    W = __import__("build_tod_station_wisconsin")
    cs = X.read_vector(W.COUSUB, dst=W.CRS_M).reset_index(drop=True)
    st, allg = W.stations(cs)                      # lot-table station ids (Milwaukee + Madison), CRS 3071
    s = pd.read_csv(REFERENCE / "tod_stops.csv", dtype={"stop_id": str, "ntd_id": str})
    s = s[s.flag_a_rapid == 1].reset_index(drop=True)
    allg = allg.reset_index(drop=True)
    allg["lat"], allg["lon"], allg["ntd_id"] = s.lat.values, s.lon.values, s.ntd_id.values
    names = cs.set_index("GEOID").NAMELSAD
    keep = allg.muni.isin([W.MILWAUKEE_CITY, W.MADISON_CITY])
    rows = []
    parts = [(allg[keep].reset_index(drop=True), True)]
    other = allg[~keep].reset_index(drop=True)
    if len(other):
        parts.append((other, False))
    nid = int(st.stop_id.max()) + 1
    for g, in_lot in parts:
        cx, cy, mem = X.merge_within(g.x.values, g.y.values, 75.0)
        for a, b, m in zip(cx, cy, mem):
            mm = g.iloc[m]
            if in_lot:
                j = int(np.argmin(np.hypot(st.x.values - a, st.y.values - b)))
                sid, match = int(st.stop_id.iloc[j]), float(np.hypot(st.x.iloc[j] - a, st.y.iloc[j] - b))
            else:
                sid, match = nid, 0.0
                nid += 1
            pts = np.c_[mm.x.values, mm.y.values]
            foot = float(np.max(np.hypot(*(pts[:, None, :] - pts[None, :, :]).transpose(2, 0, 1)))) if len(pts) > 1 else 0.0
            x5, y5 = X.transform(np.array([a]), np.array([b]), W.CRS_M, CRS)
            mx, my = X.transform(mm.x.values, mm.y.values, W.CRS_M, CRS)
            ag = mm.agency.iloc[0]
            muni = names.get(mm.muni.iloc[0], mm.muni.iloc[0])
            rows.append({"case": "wi_milwaukee" if mm.muni.iloc[0] == W.MILWAUKEE_CITY else "wi_madison" if mm.muni.iloc[0] == W.MADISON_CITY else "wi_other",
                         "stop_id": sid, "stop_name": "", "group": "wisconsin", "place": muni, "agency": ag,
                         "stop_type_text": {"City of Madison": "Madison Metro rapid (BRT)", "Milwaukee County": "MCTS rapid (BRT)",
                                            "City of Milwaukee": "The Hop streetcar", "City of Kenosha": "Kenosha streetcar"}.get(ag, ag),
                         "x": float(x5[0]), "y": float(y5[0]), "member_match_m": round(match, 2), "n_points_merged": len(mm),
                         "footprint_m": round(foot, 1), "n_platform_points": len(mm), "n_entrance_points": 0, "n_parent_points": 0,
                         "point_types": f"platform/stop {len(mm)}", "point_type_source": "reference/tod_stops.csv (GTFS stop points)",
                         "n_names_merged": np.nan, "names_merged": "", "gtfs_stop_ids": " ".join(mm.stop_id.astype(str)),
                         "in_lot_table": in_lot, "_mx": mx, "_my": my})
    return pd.DataFrame(rows)


# =========================================================================== use classes (developable land)

# per city: regex on the lot table's `use` for park/open space, cemetery, utility/transport, right-of-way.
EXCLUDE = {
    "Seattle": r"^Park, Public|Cemetery|^Utility|Right of Way|Easement|Golf",
    "Bellevue": r"^Park, Public|Cemetery|^Utility|Right of Way|Easement|Golf",
    "Charlotte": r"CEMETER|RIGHT OF WAY|RR WITH RAIL ROW|UTILIT|^PARKS?\b|PUBLIC PARK|REC AREA|GOLF",
    "Chicago": r"^RR$|^EX$",
    "Denver": r"DENVER PARK|^PARKS?\b|GOLF|CEMETER|UTILIT|RAILROAD|RIGHT[- ]OF[- ]WAY",
    "Portland": r"^PARK$|GOLF|CEMETER|UTILIT|RAILROAD|RIGHT OF WAY",
    "Philadelphia": r"FAIRMNT PK|CITY PARK|PARK$|CEMETER|UTIL|RAILROAD|RIGHT OF WAY|GOLF",
    "New York": r"^0?7$|^0?9$",
    "Los Angeles": r"^Government$",
    "Salt Lake City": r"Tax Exempt - Government",
    "Saint Paul": r"CEMETER|GRAVEYARD|RAILROAD|UTILIT|\bPARKS?\b(?!ING)|GOLF|RIGHT OF WAY",
    "Madison": r"^Golf|Conservancy|Cemetery",
    "Milwaukee": r"^6553$|^40\d\d$|^41\d\d$|^46\d\d$|^49\d\d$",
    "San Diego": None, "Austin": None, "Honolulu": None,
}
USE_NOTE = {
    "Seattle": "King County present use (text): parks, cemeteries, utilities, right of way, golf removed",
    "Bellevue": "King County present use (text): as Seattle",
    "Charlotte": "Mecklenburg land use description (text): parks/rec areas, cemeteries, utilities, rail and road right of way, golf removed",
    "Chicago": "Cook County class codes: only RR (railroad) and EX (exempt) can be removed; parks and cemeteries are inside EX (also public); classes too coarse to split utilities",
    "Denver": "Denver assessor class (text): Denver parks, parks, golf, cemeteries, utilities, railroad, right of way removed",
    "Portland": "Multnomah property use (text): parks, golf, cemeteries, utilities, railroad, right of way removed",
    "Philadelphia": "OPA building description (text): Fairmount/city parks, cemeteries, utilities, railroad, right of way, golf removed; public = fully tax-exempt (includes non-profits)",
    "New York": "MapPLUTO LandUse: 07 transportation & utility, 09 open space & outdoor recreation removed; public = OwnerType C/M/O",
    "Los Angeles": "LA County UseType (8 classes): Government removed as the public stand-in (the AgencyType public flag is empty in the lot table); parks/cemeteries not separable (Recreational and Institutional mix private uses) - too coarse",
    "Salt Lake City": "Salt Lake County class (14 classes): Tax Exempt - Government removed; parks, utilities, cemeteries not separable - too coarse",
    "Saint Paul": "Ramsey County use (text): cemeteries, railroad, utilities, parks, golf, right of way removed",
    "Madison": "City property class (text): golf, conservancy, cemetery removed (as build_tod_station_areas MAD_USE park_open_space); exempt classes are public",
    "Milwaukee": "MPROP 4-digit land use: 6553 cemetery, 40xx-41xx rail/transit, 46xx pipelines, 49xx utilities removed; parks have no separate code in the lot table (land-use group not kept) - city parks fall out only as public (exempt)",
    "San Diego": "SANDAG/assessor asr_landuse codes: no code dictionary held - only tax-exempt (public) removed; cannot separate parks/cemeteries/utilities",
    "Austin": "Travis parcel file in the lot table has no use and no owner type - cannot separate public land or parks; developable = all lots",
    "Honolulu": "Honolulu parcels in the lot table have no use and no owner type - cannot separate public land or parks; developable = all lots",
}


def developable(L: pd.DataFrame, city: str) -> np.ndarray:
    pub = L.public.fillna(False).astype(bool).values
    rx = EXCLUDE.get(city)
    if rx is None:
        return ~pub
    u = L.use.astype(str).str.strip()
    if city == "New York":
        u = u.str.replace(r"\.0$", "", regex=True)
    exc = u.str.contains(rx, case=False, regex=True, na=False).values
    return ~pub & ~exc


# =========================================================================== per-stop surroundings

LOT_COLS = ["stop_id", "group", "dist_m", "band", "acres", "land_value", "bldg_value", "use", "public", "homes_existing",
            "implausible", "in_reform_area", "x", "y", "sld_transit_freq", "sld_jobs_per_acre", "sld_transit_job_access",
            "v_c04_median_value", "v_c01_median_rent"]


def wmean(v, w):
    m = np.isfinite(v) & np.isfinite(w) & (w > 0)
    return float(np.sum(v[m] * w[m]) / np.sum(w[m])) if m.any() else np.nan


def surroundings(L: pd.DataFrame, S: pd.DataFrame, city: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per stop: lot counts/acres by band (total, developable, vacant and underused developable), traits within 1/4
    and 1/2 mile, station-point SLD, and the centroid vs nearest-point distance check. L: one case's lots."""
    L = L.copy()
    L["acres"] = pd.to_numeric(L.acres, errors="coerce")
    lv, bv = L.land_value.astype(float).values, L.bldg_value.astype(float).values
    L["dev"] = developable(L, city)
    L["vac"] = L.dev & (bv == 0)
    L["und"] = L.dev & np.isfinite(bv) & np.isfinite(lv) & (lv > 0) & (bv < lv)
    # stacked records: same lot point and same acres (condo units each carrying the whole parcel's area)
    L["stk"] = pd.DataFrame({"x": L.x.round(0), "y": L.y.round(0), "a": L.acres.round(4)}).duplicated().values & L.acres.notna().values
    L["lv_acre"] = np.where((L.acres > 0) & (lv > 0), lv / L.acres.where(L.acres > 0), np.nan)
    pos = pd.Series(np.arange(len(S)), index=S.stop_id.values)
    L = L[L.stop_id.isin(pos.index)]
    k = L.stop_id.map(pos).values
    # recomputed distances: centroid (validation of dist_m) and nearest member point
    lx, ly = L.x.values, L.y.values
    dc = np.hypot(lx - S.x.values[k], ly - S.y.values[k])
    dn = np.full(len(L), np.nan)
    order = np.argsort(k, kind="stable")
    ks, starts = np.unique(k[order], return_index=True)
    ends = np.r_[starts[1:], len(order)]
    for kk, a, b in zip(ks, starts, ends):
        idx = order[a:b]
        mx, my = S._mx.iloc[kk], S._my.iloc[kk]
        dn[idx] = np.min(np.hypot(lx[idx, None] - mx[None, :], ly[idx, None] - my[None, :]), axis=1)
    bc = np.digitize(dc, [QUARTER, HALF, MILE])      # 0,1,2 = bands, 3 = beyond 1 mile
    bn = np.digitize(dn, [QUARTER, HALF, MILE])
    L["_dc"], L["_bc"], L["_bn"] = dc, bc, bn
    rows = []
    for kk, g in L.groupby(k):
        r = {"_k": kk, "dist_recomputed_max_diff_m": round(float(np.nanmax(np.abs(g._dc - g.dist_m))), 2)}
        for key, lab in BANDS.items():
            b = g[g.band == lab]
            r[f"lots_{key}"] = len(b)
            r[f"acres_{key}"] = round(b.acres.sum(), 2)
            for t, col in (("dev", "dev"), ("vacant_dev", "vac"), ("underused_dev", "und")):
                r[f"{t}_lots_{key}"] = int(b[col].sum())
                r[f"{t}_acres_{key}"] = round(b.acres[b[col]].sum(), 2)
                r[f"{t}_acres_dedup_{key}"] = round(b.acres[b[col] & ~b.stk].sum(), 2)
            r[f"stacked_dup_lots_{key}"] = int(b.stk.sum())
            r[f"acres_dedup_{key}"] = round(b.acres[~b.stk].sum(), 2)
        for key, labs in (("q", ["0-1/4"]), ("h", ["0-1/4", "1/4-1/2"])):
            b = g[g.band.isin(labs)]
            a = b.acres.values.astype(float)
            ad = b.acres[~b.stk].sum()          # stacked duplicate records counted once
            r[f"homes_per_acre_{key}"] = round(b.homes_existing.sum() / ad, 3) if ad > 0 else np.nan
            r[f"median_land_value_per_acre_{key}"] = round(float(b.lv_acre.median()), 0) if b.lv_acre.notna().any() else np.nan
            hasv = b.bldg_value.notna()
            r[f"share_lots_vacant_{key}"] = round(float((b.bldg_value[hasv] == 0).mean()), 4) if hasv.any() else np.nan
            r[f"tract_median_home_value_{key}"] = b.v_c04_median_value.median()
            r[f"tract_median_rent_{key}"] = b.v_c01_median_rent.median()
            r[f"jobs_per_acre_{key}"] = round(wmean(b.sld_jobs_per_acre.values.astype(float), a), 3)
            r[f"transit_job_access_{key}"] = round(wmean(b.sld_transit_job_access.values.astype(float), a), 1)
            r[f"share_lots_in_reform_area_{key}"] = round(float(b.in_reform_area.astype(bool).mean()), 4) if len(b) else np.nan
        # station-point SLD D4c: block group of the lot nearest the station point
        j = int(np.argmin(g._dc.values))
        r["sld_d4c_station_bg"] = g.sld_transit_freq.iloc[j]
        # distance-definition check
        ch = g._bc.values != g._bn.values
        r["distchk_lots_band_changed"] = int(ch.sum())
        r["distchk_acres_band_changed"] = round(float(np.nansum(g.acres.values[ch])), 2)
        for bi, key in enumerate(BANDS):
            r[f"distchk_lots_{key}_centroid"] = int((g._bc == bi).sum())
            r[f"distchk_lots_{key}_nearest"] = int((g._bn == bi).sum())
            r[f"distchk_acres_{key}_centroid"] = round(float(g.acres[g._bc == bi].sum()), 2)
            r[f"distchk_acres_{key}_nearest"] = round(float(g.acres[g._bn == bi].sum()), 2)
        rows.append(r)
    R = pd.DataFrame(rows)
    # the nearest-point shift (centroid distance minus nearest-point distance) per stop
    sh = pd.Series(dc - dn).groupby(k).max()
    R["distchk_max_shift_m"] = R._k.map(sh).round(1)
    return R, L


# =========================================================================== GTFS service

def _read(z: zipfile.ZipFile, name: str, usecols=None, chunks=False):
    names = {n.split("/")[-1]: n for n in z.namelist()}
    if name not in names:
        return None
    raw = z.open(names[name])
    kw = dict(dtype=str, skipinitialspace=True)
    if chunks:
        return pd.read_csv(raw, chunksize=500_000, **kw)
    d = pd.read_csv(raw, **kw)
    d.columns = d.columns.str.strip()
    d = d.apply(lambda c: c.str.strip())
    return d[usecols] if usecols else d


def active_services(z: zipfile.ZipFile, day: date) -> set:
    cal = _read(z, "calendar.txt")
    cd = _read(z, "calendar_dates.txt")
    ds = day.strftime("%Y%m%d")
    on = set()
    if cal is not None and len(cal):
        wd = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][day.weekday()]
        m = (cal.start_date <= ds) & (cal.end_date >= ds) & (cal[wd] == "1")
        on = set(cal.service_id[m])
    if cd is not None and len(cd):
        x = cd[cd.date == ds]
        on |= set(x.service_id[x.exception_type == "1"])
        on -= set(x.service_id[x.exception_type == "2"])
    return on


def pick_day(z: zipfile.ZipFile) -> tuple[date, set]:
    """The Tuesday with service nearest TARGET_DAY inside the feed's calendar range."""
    cal, cd = _read(z, "calendar.txt"), _read(z, "calendar_dates.txt")
    ds = []
    if cal is not None and len(cal):
        ds += list(cal.start_date) + list(cal.end_date)
    if cd is not None and len(cd):
        ds += list(cd.date)
    ds = pd.to_datetime(pd.Series(ds), format="%Y%m%d", errors="coerce").dropna()
    d0, d1 = ds.min().date(), ds.max().date()
    tues = [d0 + timedelta(days=k) for k in range((d1 - d0).days + 1) if (d0 + timedelta(days=k)).weekday() == 1]
    for d in sorted(tues, key=lambda d: abs((d - TARGET_DAY).days)):
        s = active_services(z, d)
        if s:
            return d, s
    raise RuntimeError("no service day found")


def _sec(t: pd.Series) -> np.ndarray:
    p = t.str.split(":", expand=True)
    return (pd.to_numeric(p[0], errors="coerce") * 3600 + pd.to_numeric(p[1], errors="coerce") * 60).values


def feed_departures(path: Path, keep_route) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """(stop events on the chosen weekday: stop_id, trip_id, sec), stops (stop_id, lat, lon), day used."""
    with zipfile.ZipFile(path) as z:
        day, svc = pick_day(z)
        routes = _read(z, "routes.txt")
        routes = routes[routes.apply(keep_route, axis=1)]
        trips = _read(z, "trips.txt", ["route_id", "service_id", "trip_id"])
        trips = trips[trips.route_id.isin(routes.route_id) & trips.service_id.isin(svc)]
        tid = set(trips.trip_id)
        ev = []
        for ch in _read(z, "stop_times.txt", chunks=True):
            ch.columns = ch.columns.str.strip()
            ch = ch[["trip_id", "stop_id", "departure_time", "arrival_time"]]
            ch = ch[ch.trip_id.str.strip().isin(tid)]
            if len(ch):
                t = ch.departure_time.fillna(ch.arrival_time).str.strip()
                ev.append(pd.DataFrame({"stop_id": ch.stop_id.str.strip().values, "trip_id": ch.trip_id.str.strip().values, "sec": _sec(t)}))
        stops = _read(z, "stops.txt")[["stop_id", "stop_lat", "stop_lon"]]
    E = pd.concat(ev, ignore_index=True) if ev else pd.DataFrame(columns=["stop_id", "trip_id", "sec"])
    stops["stop_lat"], stops["stop_lon"] = stops.stop_lat.astype(float), stops.stop_lon.astype(float)
    return E, stops, day.isoformat()


def rt(*types):
    return lambda r: str(r.get("route_type", "")).strip() in types


FEEDS = {   # city -> list of (file, route filter, label)
    "New York": [(SRC / "gtfs" / "new_york_mta_subway.zip", rt("1"), "MTA subway")],
    "Philadelphia": [(SRC / "gtfs" / "philadelphia_septa_rail.zip", rt("2"), "SEPTA Regional Rail"),
                     (RAW / "tod_net_coverage" / "gtfs" / "philadelphia_septa_bus.zip",
                      lambda r: str(r.get("route_type")).strip() in ("0", "1") and not re.search(r"OWL|_BUS", str(r.get("route_id"))),
                      "SEPTA metro/trolley")],
    "Chicago": [(RAW / "tod_net_coverage" / "gtfs" / "chicago_cta.zip", rt("1"), "CTA rail"),
                (SRC / "gtfs" / "chicago_metra.zip", rt("2"), "Metra")],
    "Los Angeles": [(SRC / "gtfs" / "los_angeles_la_metro_rail.zip", rt("0", "1"), "LA Metro rail"),
                    (RAW / "tod_net_coverage" / "gtfs" / "los_angeles_la_metro_bus.zip",
                     lambda r: str(r.get("route_short_name", "")).strip() in ("901",) or str(r.get("route_id", "")).split("-")[0] == "901", "LA Metro G Line")],
    "San Diego": [(SRC / "gtfs" / "san_diego_mts.zip", rt("0"), "MTS Trolley")],
    "Honolulu": [(SRC / "gtfs" / "honolulu_thebus.zip", rt("1"), "Skyline")],
    "Denver": [(SRC / "gtfs" / "denver_rtd.zip", rt("0", "2"), "RTD rail")],
    "Portland": [(SRC / "gtfs" / "portland_trimet.zip", rt("0", "2"), "TriMet MAX/Streetcar/WES")],
    "Salt Lake City": [(SRC / "gtfs" / "salt_lake_uta.zip", rt("0"), "UTA TRAX/S-Line")],
    "Austin": [(SRC / "gtfs" / "austin_capmetro.zip", lambda r: str(r.get("route_id", "")).strip() == "550", "CapMetro MetroRail")],
    "Seattle": [(SRC / "gtfs" / "seattle_sound_transit.zip", rt("0"), "Sound Transit Link")],
    "Bellevue": [(SRC / "gtfs" / "seattle_sound_transit.zip", rt("0"), "Sound Transit Link")],
    "Saint Paul": [(RAW / "tod_net_coverage" / "gtfs" / "saint_paul_metro_transit.zip", rt("0"), "Metro Transit light rail")],
    "Charlotte": [(RAW / "tod_net_coverage" / "gtfs" / "charlotte_cats.zip", rt("0"), "CATS LYNX/CityLYNX")],
}
WI_FEEDS = {"Milwaukee County": RAW / "tod_transit" / "gtfs" / "50008_mcts.zip", "City of Milwaukee": RAW / "tod_transit" / "gtfs" / "55312_hop.zip",
            "City of Kenosha": RAW / "tod_transit" / "gtfs" / "50003_kenosha.zip"}


def tph(E: pd.DataFrame, key: np.ndarray) -> pd.DataFrame:
    """Unique trips per hour per station key: peak 07-09 (/2), midday 10-14 (/4), both directions, all lines."""
    E = E.assign(k=key)
    E = E[E.k >= 0]
    pk = E[(E.sec >= 7 * 3600) & (E.sec < 9 * 3600)].groupby("k").trip_id.nunique() / 2
    md = E[(E.sec >= 10 * 3600) & (E.sec < 14 * 3600)].groupby("k").trip_id.nunique() / 4
    return pd.DataFrame({"tph_peak": pk, "tph_midday": md}).fillna(0)


def service(T: pd.DataFrame, log: list) -> pd.DataFrame:
    """Trips per hour at each unique station (by city and rounded station point)."""
    T = T.copy()
    T["tph_peak"], T["tph_midday"], T["tph_source"], T["gtfs_stops_matched"] = np.nan, np.nan, "", np.nan
    for city, feeds in FEEDS.items():
        sel = np.flatnonzero((T.city == city).values)
        if not len(sel):
            continue
        U = T.iloc[sel].drop_duplicates("_skey")
        acc = pd.DataFrame(0.0, index=np.arange(len(U)), columns=["tph_peak", "tph_midday"])
        nmatch = np.zeros(len(U))
        srcs = []
        for path, filt, lab in feeds:
            if not path.exists():
                log.append(f"{city}: {path.name} missing")
                continue
            E, st, day = feed_departures(path, filt)
            st = st[st.stop_id.isin(set(E.stop_id))]
            sx, sy = X.transform(st.stop_lon.values, st.stop_lat.values, 4326, CRS)
            d, i = cKDTree(np.c_[U.x.values, U.y.values]).query(np.c_[sx, sy], distance_upper_bound=200.0)
            m = pd.Series(np.where(np.isfinite(d), i, -1), index=st.stop_id.values)
            key = E.stop_id.map(m).fillna(-1).astype(int).values
            t = tph(E, key)
            acc.loc[t.index, ["tph_peak", "tph_midday"]] += t.values
            nmatch += np.bincount(m.values[m.values >= 0], minlength=len(U))
            srcs.append(f"{lab} GTFS {path.name}, weekday {day}")
            log.append(f"{city} {lab}: day {day}; rail stop points {len(st)}, matched to a station within 200 m {int((m >= 0).sum())}")
        if not srcs:
            continue
        val = acc.where(pd.Series(nmatch > 0, index=acc.index), axis=0)
        mp = dict(zip(U._skey, range(len(U))))
        r = T._skey.iloc[sel].map(mp).values
        T.iloc[sel, T.columns.get_loc("tph_peak")] = val.tph_peak.values[r]
        T.iloc[sel, T.columns.get_loc("tph_midday")] = val.tph_midday.values[r]
        T.iloc[sel, T.columns.get_loc("gtfs_stops_matched")] = nmatch[r]
        T.iloc[sel, T.columns.get_loc("tph_source")] = "; ".join(srcs)
    # Wisconsin: exact GTFS stop ids of the station's members (all routes stopping there)
    wi = np.flatnonzero((T.group == "wisconsin").values)
    for ag, path in WI_FEEDS.items():
        rows = [i for i in wi if T.agency.iloc[i] == ag]
        if not rows:
            continue
        E, st, day = feed_departures(path, lambda r: True)
        for i in rows:
            ids = set(T.gtfs_stop_ids.iloc[i].split())
            e = E[E.stop_id.isin(ids)]
            T.iloc[i, T.columns.get_loc("tph_peak")] = e[(e.sec >= 7 * 3600) & (e.sec < 9 * 3600)].trip_id.nunique() / 2
            T.iloc[i, T.columns.get_loc("tph_midday")] = e[(e.sec >= 10 * 3600) & (e.sec < 14 * 3600)].trip_id.nunique() / 4
            T.iloc[i, T.columns.get_loc("gtfs_stops_matched")] = int(st.stop_id.isin(ids).sum())
            T.iloc[i, T.columns.get_loc("tph_source")] = f"{ag} GTFS {path.name}, weekday {day}, all routes at the stop ids"
        log.append(f"Wisconsin {ag}: day {day}")
    mad = (T.group == "wisconsin") & (T.agency == "City of Madison")
    T.loc[mad, "tph_source"] = "not computed: Madison Metro GTFS not allowed (AQ-045); use sld_d4c_station_bg"
    return T


# =========================================================================== ridership

RID = SRC / "ridership"


def _match(U: pd.DataFrame, lon, lat, maxd=250.0) -> np.ndarray:
    x, y = X.transform(np.asarray(lon, float), np.asarray(lat, float), 4326, CRS)
    d, i = cKDTree(np.c_[U.x.values, U.y.values]).query(np.c_[x, y], distance_upper_bound=maxd)
    return np.where(np.isfinite(d), i, -1)


def ridership(T: pd.DataFrame, log: list) -> pd.DataFrame:
    T = T.copy()
    for c in ("ridership_weekday_2019", "ridership_weekday_latest"):
        T[c] = np.nan
    T["ridership_year_latest"], T["ridership_measure"], T["ridership_note"] = np.nan, "", ""

    def put(city, U, vals19, valsl, year_l, measure, note):
        mp = dict(zip(U._skey, range(len(U))))
        sel = np.flatnonzero((T.city == city).values)
        r = T._skey.iloc[sel].map(mp).values
        for col, v in (("ridership_weekday_2019", vals19), ("ridership_weekday_latest", valsl)):
            if v is not None:
                T.iloc[sel, T.columns.get_loc(col)] = np.where(np.isfinite(v[r]) & (v[r] > 0), v[r], np.nan)
        T.iloc[sel, T.columns.get_loc("ridership_year_latest")] = year_l
        T.iloc[sel, T.columns.get_loc("ridership_measure")] = measure
        T.iloc[sel, T.columns.get_loc("ridership_note")] = note

    def uniq(city):
        return T[T.city == city].drop_duplicates("_skey").reset_index(drop=True)

    # New York: average weekday entries per station complex, split equally over the stations a complex matches
    U = uniq("New York")
    st = pd.read_csv(RID / "mta_subway_stations.csv")
    st["k"] = _match(U, st.gtfs_longitude, st.gtfs_latitude)
    cx = st[st.k >= 0].assign(complex_id=st.complex_id.astype(str).str.strip()).groupby("complex_id").k.apply(lambda s: sorted(set(s)))
    out = {}
    for yr in (2019, 2024):
        d = pd.read_csv(RID / f"mta_subway_weekday_daily_by_complex_{yr}.csv")
        d = d[d.transit_mode == "subway"]
        nd = d.service_date.nunique()
        avg = d.groupby(d.station_complex_id.astype(str).str.strip()).entries.sum() / nd
        v = np.zeros(len(U))
        for cid, ks in cx.items():
            if cid in avg.index:
                for k in ks:
                    v[k] += avg[cid] / len(ks)
        out[yr] = v
    shared = cx[cx.map(len) > 1]
    log.append(f"New York: MTA stations matched {int((st.k >= 0).sum())}/{len(st)}; complexes split over >1 station: {len(shared)}")
    put("New York", U, out[2019], out[2024], 2024, "average weekday entries (MTA hourly ridership, subway, weekdays incl. holidays)",
        "complex entries split equally where a complex matches several stations")
    # Chicago CTA: average weekday ('W') entries 2019 by map_id; Metra none
    U = uniq("Chicago")
    ls = pd.read_csv(RAW / "cta_ridership" / "l_stops.csv")
    ll = ls.location.str.extract(r"\(?(-?\d+\.\d+),\s*(-?\d+\.\d+)\)?").astype(float)
    ls["lat"], ls["lon"] = ll[0], ll[1]
    ls = ls.dropna(subset=["lat"]).groupby("map_id")[["lat", "lon"]].mean()
    e = pd.read_csv(RAW / "cta_ridership" / "l_station_entries_daily_2009_2019.csv", usecols=["station_id", "date", "daytype", "rides"])
    e = e[(e.daytype == "W") & e.date.str.startswith("2019")]
    avg = e.groupby("station_id").rides.mean()
    k = _match(U, ls.lon.values, ls.lat.values)
    v = np.zeros(len(U))
    for mid, kk in zip(ls.index, k):
        if kk >= 0 and mid in avg.index:
            v[kk] += avg[mid]
    v[(U.stop_type_text != "CTA rail").values] = np.nan
    put("Chicago", U, v, None, np.nan, "average weekday entries 2019 (CTA 'L'; Metra: none published as open data)", "Metra stations blank")
    # Philadelphia: SEPTA Regional Rail 2019 weekday boardings (all lines, both directions); trolley summer 2025 ons
    U = uniq("Philadelphia")
    g = pd.DataFrame([f["properties"] for f in json.load(open(RID / "septa_regional_rail_station_ridership_2017_2024.geojson"))["features"]])
    v19 = np.full(len(U), np.nan)
    vl = np.full(len(U), np.nan)
    for yr, arr in (("2019", v19), ("2024", vl)):
        w = g[(g.Year.astype(str) == yr) & g.Service_Ty.astype(str).str.contains("Weekday", case=False)]
        s = w.groupby("Stop_ID").agg(b=("Boards", "sum"), lat=("Latitude", "first"), lon=("Longitude", "first"))
        k = _match(U[U.stop_type_text == "Rail"], s.lon.values, s.lat.values)
        idx = np.flatnonzero((U.stop_type_text == "Rail").values)
        for kk, b in zip(k, s.b.values):
            if kk >= 0:
                arr[idx[kk]] = np.nansum([arr[idx[kk]], b])
    tr = pd.DataFrame([f["properties"] for f in json.load(open(RID / "septa_trolley_stop_summary_summer2025.geojson"))["features"]])
    idx = np.flatnonzero((U.stop_type_text == "Trolley").values)
    k = _match(U[U.stop_type_text == "Trolley"], tr.Lon.values, tr.Lat.values, 150.0)
    for kk, b in zip(k, pd.to_numeric(tr.Weekdays_O, errors="coerce").values):
        if kk >= 0:
            vl[idx[kk]] = np.nansum([vl[idx[kk]], b])
    put("Philadelphia", U, v19, vl, 2024, "Regional Rail: average weekday boardings (2019 census, 2024 SEPTA estimate); trolley: average weekday ons summer 2025 (in 'latest'); Market-Frankford/Broad Street: none (licence bars copying)",
        "mixed measures by mode; compare within mode")
    # Saint Paul: Metro Transit weekday ons, both directions, by station group
    U = uniq("Saint Paul")
    m = json.load(open(RID / "metc_rail_stop_boardings.json"))
    m = pd.DataFrame([a["attributes"] for a in (m["features"] if "features" in m else m)])
    m = m[(m.Schedule == "Weekday") & (m.Route.astype(str).str.contains("Green"))]
    s = m.groupby("Name").agg(b=("Ons", "sum"), lat=("Latitude", "mean"), lon=("Longitude", "mean"))
    v = np.full(len(U), np.nan)
    for kk, b in zip(_match(U, s.lon.values, s.lat.values), s.b.values):
        if kk >= 0:
            v[kk] = np.nansum([v[kk], b])
    put("Saint Paul", U, None, v, 2025, "average weekday boardings, Green Line (Metro Transit rail stop boardings, latest release, period not stated)", "")
    # Salt Lake City: UTA average weekday boardings, mean of months, summed over lines
    U = uniq("Salt Lake City")
    r = pd.read_csv(RID / "uta_rail_stop_ridership_weekday_monthly_2017_on.csv")
    loc = pd.read_csv(RID / "uta_rail_stops_locations.csv").drop_duplicates("stopabbr").set_index("stopabbr")
    r = r[r["mode"].astype(str).str.contains("Light|Streetcar|TRAX|S-Line", case=False)]
    vv = {}
    for yr in (2019, 2025):
        w = r[r.year_ == yr].groupby(["stopabbrone", "route"]).avgboardings.mean().groupby("stopabbrone").sum()
        w = w[w.index.isin(loc.index)]
        v = np.full(len(U), np.nan)
        for kk, b in zip(_match(U, loc.loc[w.index].longitude.values, loc.loc[w.index].latitude.values), w.values):
            if kk >= 0:
                v[kk] = np.nansum([v[kk], b])
        vv[yr] = v
    put("Salt Lake City", U, vv[2019], vv[2025], 2025, "average weekday boardings (UTA open data, mean of monthly averages, summed over lines)", "")
    for city, why in {"Seattle": "Sound Transit: dashboard and PDF reports only", "Bellevue": "Sound Transit: dashboard and PDF reports only",
                      "Denver": "RTD: dashboard only", "Portland": "TriMet: PDF reports only", "Los Angeles": "LA Metro: line and system totals only",
                      "Charlotte": "CATS: 2018 PDF (records request) only", "San Diego": "MTS: no open station file",
                      "Austin": "CapMetro: raw passenger-counter files only, no station summary", "Honolulu": "Skyline: system totals only",
                      "Milwaukee": "MCTS/The Hop: system totals only", "Madison": "Madison Metro: none open (and GTFS barred, AQ-045)",
                      "Kenosha": "Kenosha: none found"}.items():
        T.loc[T.city == city, "ridership_note"] = "blank: " + why
    return T


# =========================================================================== reform history (New York, Philadelphia)

def reform_history(rh: dict, T: pd.DataFrame) -> pd.DataFrame:
    """rh[city][stop_id] = list of (case, eff) whose reform-area lots lie within 1/4 mile of the stop."""
    T = T.copy()
    T["rezonings_within_quarter"] = ""
    T["n_rezonings_within_quarter"] = np.nan
    for city in ("nyc", "phl"):
        m = T.case.str.startswith(city + "_")
        lst = T.loc[m, "stop_id"].map(lambda s: sorted(rh.get(city, {}).get(s, []), key=lambda z: (z[1], z[0])))
        T.loc[m, "rezonings_within_quarter"] = lst.map(lambda l: "; ".join(f"{c} ({e})" for c, e in l))
        T.loc[m, "n_rezonings_within_quarter"] = lst.map(len)
    return T


# =========================================================================== mode, grade, opening year

def mode_of(r) -> str:
    t, city = str(r.stop_type_text), r.city
    if city == "New York":
        return "heavy rail"
    if city == "Philadelphia":
        return {"Rail": "commuter rail", "Subway/elevated": "heavy rail", "Trolley": "light rail/trolley"}.get(t, t)
    if city == "Chicago":
        return "heavy rail" if t == "CTA rail" else "commuter rail"
    if "G Line" in t:
        return "BRT"
    if "Subway, Metro" in t or city == "Honolulu":
        return "heavy rail"
    if "Tram, Streetcar, Light rail" in t:
        return "light rail"
    if False:
        return "heavy rail"
    if t == "Rail" or "WES" in t or "MetroRail" in t:
        return "commuter rail"
    if city == "Denver":
        return "commuter rail" if re.search(r"\((A|B|G|N) Line|East Rail|Gold|Northwest|North Metro|University of Colorado A", t) else "light rail"
    if "streetcar" in t.lower() or "Street Car" in t or "CityLYNX" in t:
        return "streetcar"
    if "BRT" in t:
        return "BRT"
    return "light rail"


def grade_and_year(T: pd.DataFrame) -> pd.DataFrame:
    T = T.copy()
    for c in ("grade", "grade_source", "opening_year", "opening_year_source"):
        if c not in T:
            T[c] = np.nan if c == "opening_year" else ""
    T["grade"] = T.grade.fillna("").replace("", "unknown")
    la_sub = (T.city == "Los Angeles") & T.stop_type_text.str.contains("Subway, Metro", na=False)
    T.loc[la_sub, ["grade", "grade_source"]] = ["underground", "NTM mode 'Subway, Metro' (LA B/D Lines are fully underground)"]
    T.loc[T.city == "Honolulu", ["grade", "grade_source"]] = ["elevated", "Skyline is fully elevated (system design; city layer)"]
    T.loc[T["mode"].isin(["BRT", "streetcar"]) & T.grade.eq("unknown"), ["grade", "grade_source"]] = ["at grade", "mode (street-running)"]
    from station_cases import cluster_north as N
    nm = T.stop_name.astype(str).str.replace(" Station", "", regex=False)
    sea = T.city.eq("Seattle")
    T.loc[sea, "opening_year"] = nm[sea].map({**N.LINK_OPENED, "Roosevelt": 2021}).values
    T.loc[sea & T.opening_year.notna(), "opening_year_source"] = "cluster_north.LINK_OPENED (Sound Transit service changes)"
    T.loc[T.city.eq("Saint Paul"), ["opening_year", "opening_year_source"]] = [2014, "Green Line opening (cluster_north notes)"]
    T.loc[T.city.eq("Austin"), ["opening_year", "opening_year_source"]] = [2010, "MetroRail opening (cluster_west stop type)"]
    T["opening_year"] = pd.to_numeric(T.opening_year, errors="coerce")
    T["opening_year_source"] = T.opening_year_source.fillna("")
    T.loc[T.opening_year.isna() & T.opening_year_source.eq(""), "opening_year_source"] = "unknown (no open agency field held)"
    T.loc[T.city.eq("Bellevue"), "opening_year_source"] = "unknown: East Link approved 2008, stations opened 2024 or later"
    return T


# =========================================================================== main build

def build() -> pd.DataFrame:
    log: list[str] = []
    cache: dict = {}
    rh: dict = {"nyc": {}, "phl": {}}
    parts = []
    cases = lot_cases()
    for n, (case, path) in enumerate(cases.items()):
        city = city_of(case)
        S = stops_for_case(case, path, cache)
        L = pd.read_parquet(path, columns=[c for c in LOT_COLS if c != "in_reform_area"] + ["in_reform_area"])
        R, Lx = surroundings(L, S, city)
        S = S.reset_index(drop=True)
        S["_k"] = np.arange(len(S))
        S = S.merge(R, on="_k", how="left")
        S["case"], S["city"], S["reform_year"] = case, city, eff_of(case)
        S["role"] = S.group
        if case.startswith(("nyc_", "phl_")):
            tr = L[L.in_reform_area.astype(bool)]
            if len(tr):
                d, _ = cKDTree(np.c_[tr.x.values, tr.y.values]).query(np.c_[S.x.values, S.y.values])
                for sid in S.stop_id.values[d <= QUARTER]:
                    rh[case[:3]].setdefault(int(sid), []).append((case, eff_of(case)))
        parts.append(S)
        print(f"[{n + 1}/{len(cases)}] {case}: stops {len(S)}, lots {len(L):,}", flush=True)
        del L, Lx
    # Wisconsin
    W = wisconsin_stops()
    L = pd.read_parquet(LOTDIR / "wi_lots_station.parquet", columns=LOT_COLS + ["case"])
    W["_k"] = np.arange(len(W))
    # developable classes differ by city: one pass per city
    Rm, _ = surroundings(L[L.case == "wi_milwaukee"].drop(columns=["case"]), W[W.in_lot_table].reset_index(drop=True), "Milwaukee")
    Rd, _ = surroundings(L[L.case == "wi_madison"].drop(columns=["case"]), W[W.in_lot_table].reset_index(drop=True), "Madison")
    WL = W[W.in_lot_table].reset_index(drop=True)
    WL["_k"] = np.arange(len(WL))
    WL = pd.concat([WL[WL.case == "wi_milwaukee"].merge(Rm, on="_k", how="left"),
                    WL[WL.case == "wi_madison"].merge(Rd, on="_k", how="left")], ignore_index=True)
    WO = W[~W.in_lot_table].drop(columns=["_k"])
    W = pd.concat([WL.drop(columns=["_k"]), WO], ignore_index=True)
    W["city"] = W.place.str.replace(r" (city|village|town)$", "", regex=True)
    W["role"], W["reform_year"] = "wisconsin", 2025
    parts.append(W)
    T = pd.concat(parts, ignore_index=True)
    T.to_pickle(STAGE1)
    pd.to_pickle(rh, STAGE1.with_suffix(".rh.pkl"))
    return finish(T, log, rh)


def finish(T: pd.DataFrame, log: list, rh: dict) -> pd.DataFrame:
    T["mode"] = T.apply(mode_of, axis=1)
    lon, lat = X.transform(T.x.values, T.y.values, CRS, 4326)
    T["lon"], T["lat"] = np.round(lon, 6), np.round(lat, 6)
    T["_skey"] = T.city + "|" + T.x.round(0).astype(str) + "|" + T.y.round(0).astype(str)
    T = grade_and_year(T)
    T = reform_history(rh, T)
    T = service(T, log)
    T = ridership(T, log)
    T["stop_key"] = T._skey
    for line in log:
        print("  " + line)
    return T


FRONT = ["case", "city", "role", "stop_id", "stop_name", "place", "lat", "lon", "stop_key", "mode", "stop_type_text",
         "n_points_merged", "n_platform_points", "n_entrance_points", "n_parent_points", "point_types", "point_type_source",
         "footprint_m", "n_names_merged", "names_merged", "member_match_m", "grade", "grade_source", "lines", "opening_year",
         "opening_year_source", "tph_peak", "tph_midday", "tph_source", "gtfs_stops_matched", "sld_d4c_station_bg",
         "ridership_weekday_2019", "ridership_weekday_latest", "ridership_year_latest", "ridership_measure", "ridership_note",
         "reform_year", "rezonings_within_quarter", "n_rezonings_within_quarter"]


def write(T: pd.DataFrame) -> pd.DataFrame:
    rest = [c for c in T.columns if c not in FRONT and not c.startswith("_") and c not in
            ("x", "y", "group", "agency", "gtfs_stop_ids", "in_lot_table", "dist_upzoned_m", "comparison_kind",
             "excluded_reason", "own_tod_rezoning", "downtown")]
    keep = [c for c in FRONT if c in T] + ["comparison_kind", "excluded_reason", "downtown", "agency", "gtfs_stop_ids", "in_lot_table"] + rest
    keep = list(dict.fromkeys(c for c in keep if c in T))
    out = T[keep]
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT} ({len(out):,} rows, {len(keep)} columns)")
    return out


# =========================================================================== sanity checks

def checks(T: pd.DataFrame) -> None:
    pd.set_option("display.width", 220, "display.max_columns", 30, "display.max_colwidth", 60)
    print("\n== rows by city and role")
    print(T.groupby(["city", "role"]).size().unstack(fill_value=0))
    print("\n== duplicates: (case, stop_id)", int(T.duplicated(["case", "stop_id"]).sum()),
          "; (case, stop_key)", int(T.duplicated(["case", "stop_key"]).sum()))
    u = T.drop_duplicates("stop_key")
    xy = np.c_[*X.transform(u.lon.values, u.lat.values, 4326, CRS)]
    pairs = cKDTree(xy).query_pairs(200.0, output_type="ndarray")
    print(f"unique stations {len(u):,}; pairs of distinct stations closer than 200 m: {len(pairs)}")
    if len(pairs):
        P = pd.DataFrame({"a": u.stop_name.fillna("").values[pairs[:, 0]], "b": u.stop_name.fillna("").values[pairs[:, 1]],
                          "city": u.city.values[pairs[:, 0]], "mode_a": u["mode"].values[pairs[:, 0]], "mode_b": u["mode"].values[pairs[:, 1]],
                          "m": np.hypot(*(xy[pairs[:, 0]] - xy[pairs[:, 1]]).T).round(0)})
        print(P.sort_values("m").head(40).to_string(index=False))
    print("\n== member match (rebuilt merge vs stored station point), max m by city")
    print(T.groupby("city").member_match_m.max().round(2).to_string())
    print("\n== distance recomputed vs lot table dist_m, max abs diff m by city")
    print(T.groupby("city").dist_recomputed_max_diff_m.max().to_string())
    print("\n== footprint > 400 m or > 6 merged points")
    f = u[(u.footprint_m > 400) | (u.n_points_merged > 6)]
    print(f[["city", "stop_name", "mode", "n_points_merged", "footprint_m", "point_types", "names_merged"]].sort_values("footprint_m", ascending=False).head(40).to_string(index=False))
    print("\n== footprint and points merged by city (unique stations): median / max")
    print(u.groupby("city").agg(n=("stop_key", "size"), fp_med=("footprint_m", "median"), fp_max=("footprint_m", "max"),
                                pts_med=("n_points_merged", "median"), pts_max=("n_points_merged", "max"),
                                names_gt1=("n_names_merged", lambda s: int((s > 1).sum()))).to_string())
    print("\n== ridership vs trips per hour (unique stations): Spearman by city")
    for c, g in u.groupby("city"):
        for rc in ("ridership_weekday_2019", "ridership_weekday_latest"):
            h = g[[rc, "tph_peak", "tph_midday"]].dropna()
            if len(h) >= 5:
                print(f"  {c:15s} {rc:26s} n={len(h):4d} rho(peak)={h[rc].corr(h.tph_peak, method='spearman'):.2f} "
                      f"rho(midday)={h[rc].corr(h.tph_midday, method='spearman'):.2f}")
    print("\n== distance-definition check: top 10 stops by lots changing band (centroid -> nearest merged point)")
    top = u.sort_values("distchk_lots_band_changed", ascending=False).head(10)
    print(top[["city", "case", "stop_name", "n_points_merged", "footprint_m", "distchk_lots_band_changed", "distchk_acres_band_changed",
               "distchk_lots_q1_centroid", "distchk_lots_q1_nearest", "distchk_max_shift_m"]].to_string(index=False))
    rf = T[T.role == "reform"]
    print(f"reform stops: {len(rf):,}; with any lot changing band {int((rf.distchk_lots_band_changed > 0).sum())}; "
          f"lots changing band {rf.distchk_lots_band_changed.sum():,.0f} of {rf[[f'lots_{k}' for k in BANDS]].sum().sum():,.0f}")
    print("\n== developable acres <= total acres (violations)")
    for k in BANDS:
        bad = (T[f"dev_acres_{k}"] > T[f"acres_{k}"] + 1e-6).sum() + (T[f"vacant_dev_acres_{k}"] > T[f"dev_acres_{k}"] + 1e-6).sum() \
            + (T[f"underused_dev_acres_{k}"] > T[f"dev_acres_{k}"] + 1e-6).sum()
        print(f"  {k}: {int(bad)}")
    print("\n== developable share of acres within 1/4 mile by city (sum over stops)")
    g = T.groupby("city")[["acres_q1", "dev_acres_q1", "vacant_dev_acres_q1", "underused_dev_acres_q1"]].sum()
    g = g.round(0)
    g["dev_share"] = (g.dev_acres_q1 / g.acres_q1).round(3)
    g["vacant_share_of_dev"] = (g.vacant_dev_acres_q1 / g.dev_acres_q1).round(3)
    g["underused_share_of_dev"] = (g.underused_dev_acres_q1 / g.dev_acres_q1).round(3)
    print(g.to_string())
    print("\n== lot acres within 1/4 mile vs the 1/4-mile circle (125.7 acres): ratio by city, before and after removing stacked records")
    c = T.assign(r=T.acres_q1 / 125.66, rd=T.acres_dedup_q1 / 125.66, sd=T.stacked_dup_lots_q1 / T.lots_q1.where(T.lots_q1 > 0))
    print(c.groupby("city").agg(ratio_med=("r", "median"), ratio_max=("r", "max"), dedup_med=("rd", "median"), dedup_max=("rd", "max"),
                                stacked_share_lots=("sd", "median"), stops_ratio_over_2=("rd", lambda z: int((z > 2).sum()))).round(2).to_string())
    print(c.nlargest(10, "rd")[["case", "stop_name", "lots_q1", "acres_q1", "acres_dedup_q1", "stacked_dup_lots_q1"]].to_string(index=False))
    print("\n== missing values by city (share of rows blank), selected columns")
    cols = ["stop_name", "grade", "opening_year", "tph_peak", "tph_midday", "sld_d4c_station_bg", "ridership_weekday_2019",
            "ridership_weekday_latest", "lots_q1", "homes_per_acre_q", "median_land_value_per_acre_q", "tract_median_home_value_q",
            "tract_median_rent_q", "jobs_per_acre_q", "transit_job_access_q", "reform_year"]
    M = T[cols].copy()
    M["stop_name"] = M.stop_name.replace("", np.nan)
    M["grade"] = M.grade.replace("unknown", np.nan)
    print(M.isna().groupby(T.city).mean().round(2).T.to_string())


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checks", action="store_true", help="only print the checks from the written table")
    a = ap.parse_args(argv)
    if a.checks:
        checks(pd.read_csv(OUT, low_memory=False))
        return
    if os.environ.get("STOP_TABLE_REUSE") and STAGE1.exists():
        T = finish(pd.read_pickle(STAGE1), [], pd.read_pickle(STAGE1.with_suffix(".rh.pkl")) if STAGE1.with_suffix(".rh.pkl").exists() else {})
    else:
        T = build()
    out = write(T)
    checks(out)


if __name__ == "__main__":
    main()
