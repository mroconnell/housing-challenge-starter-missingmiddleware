"""Parking edge test 35, FEASIBILITY ONLY (counts; no rates, no effect): Culver City and San Jose city limits.

    uv run python scripts/fetch_parking_ca_city_edges.py

Idea. Culver City (Ord. 2022-008, adopted 2022-10-24) and San Jose (Ord. 30857, council vote 2022-12-06, adopted
2023-01-10, effective 2023-04-10) removed parking minimums citywide. California's AB 2097 (from 2023-01-01) removed them
only within 1/2 mile of a major transit stop. So at the city limit, lots just inside have no minimums; lots just outside,
in a neighbour that has not repealed and beyond the neighbour's AB 2097 zones, still have them.

Locked rules (learning thread): main band 183 m, 92 m and 366 m sensitivities, 25 m donut; before 2018-2022; after from
each city's effective date to 2025; drop segments along freeways, rail or water and where zoning differs sharply;
feasible if 20+ lots with new homes in every cell (inside/outside x before/after) across the pooled segments.

Decisions written here before any permit was counted near the border:
 S1 City limits: TIGER/Line 2024 places (full resolution; the 1:500k cartographic file is generalised by up to ~100 m,
    too coarse for a 25-183 m band). Neighbours: incorporated places (CLASSFP C*); land in no incorporated place is
    "unincorporated <county>" (TIGER 2024 counties).
 S2 Segments: each city's boundary is cut into 100 m pieces. Outward side = the normal that leaves the city.
    Neighbour = jurisdiction 30 m out. Probes out at 25, 50, 92, 137, 183, 275, 366 m.
 S3 Drops, in this order (a piece is counted under its first reason):
    a. no neighbour (ocean or no land);
    b. neighbour repealed for housing citywide (taxonomy benchmark_rating "at", status adopted);
    c. along a freeway, rail line or water: a TIGER 2024 primary road (MTFCC S1100), any rail line, or a TIGER
       area/linear water feature within 50 m of the piece's midpoint;
    d. neighbour's AB 2097 zone: any outward probe up to the band within 1/2 mile (804.672 m) of an existing major
       transit stop (Caltrans layer, blank plan_name, as E1 and TOD). Band-specific.
    e. zoning differs sharply across the line: NOT APPLIED (no zoning layer for both sides on file; see caveats).
 S4 Permits: HCD APR Table A2, TOD/E1 cleaning (missing_middleware.tod.ab2097.is_geocoded; exact duplicates on
    jurisdiction, address, report year, unit category, units; plus the same permit re-reported in a later report year,
    same jurisdiction, address, unit category, units and BP_ISSUE_DT1). Date = BP_ISSUE_DT1, else report year.
 S5 Windows: before = 2018-01-01 to the day before the effective date, capped at 2022-12-31; after = effective date to
    2025-12-31. Undated records (report year only) in the effective year are "ambiguous" and not counted in a window.
    Culver City effective date: not stated in any source found; 2022-11-23 = adoption + 30 days (CA default) is used.
    San Jose: dated permits 2023-01-01 to 2023-04-09 fall between windows and are counted as "gap".
 S6 A permit is in the band if its distance to the city limit is >= 25 m and <= band, the nearest boundary piece is
    usable at that band, and (outside) it lies in that piece's neighbour and beyond 1/2 mile of every major stop.
 S7 Lots: distinct jurisdiction + APN from the A2 record (digits only; LA County APNs padded to 10, Santa Clara to 8);
    records without a usable APN fall back to their location rounded to 1e-5 degrees. Check for Culver City: the
    LA County Assessor 2022-roll parcel polygon containing the point, else the parcel whose representative point is
    nearest within 40 m (HCD points can sit on a street centreline) (eGIS Hub Terms of Use: licence to copy, adapt and
    exploit). Santa Clara County parcels carry no open licence ("all rights reserved"), so none is fetched.
 S8 Geometry: missing_middleware.geom, numpy, scipy only (EPSG:3310).

Outputs: reference/parking_ca_city_edges_feasibility.csv (counts only, no addresses, APNs or ids).
Raw files: data/raw/parking_ca_city_edges/ with manifest.json.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware import geom as G  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import ab2097 as ab  # noqa: E402

D = RAW / "parking_ca_city_edges"
OUT = REFERENCE / "parking_ca_city_edges_feasibility.csv"
CRS = 3310
HALF_MILE = 804.672
PIECE = 100.0
PROBES = [25, 50, 92, 137, 183, 275, 366]
BANDS = [92, 183, 366]
DONUT = 25.0
ALONG = 50.0
MIN_LOTS = 20
PUBLIC_DOMAIN = "US Census Bureau, public domain (17 U.S.C. 105)"

CITIES = {
    "Culver City": dict(geoid="0617568", juris="CULVER CITY", county="06037", eff="2022-11-23",
                        eff_note="not stated in any source found; adoption 2022-10-24 + 30 days (CA default)",
                        scope="citywide, all uses (Ord. 2022-008; only exception: a Comprehensive Plan may set parking)",
                        zoning="none in the ordinance; Housing Element adopted 2022, its rezoning came with General Plan 2045 (approved 2024-08-26)"),
    "San Jose": dict(geoid="0668000", juris="SAN JOSE", county="06085", eff="2023-04-10",
                     eff_note="Ord. 30857 text as quoted: effective 10 April 2023 (vote 2022-12-06, adopted 2023-01-10)",
                     scope="citywide for housing; office minimum kept within 1/2 mile of SAP Center / Diridon-Google DA area",
                     zoning="none found in Ord. 30857 (parking and TDM rewrite only)"),
}
UNINC_JURIS = {"06037": "LOS ANGELES COUNTY", "06085": "SANTA CLARA COUNTY"}
APN_LEN = {"06037": 10, "06085": 8}

TIGER = "https://www2.census.gov/geo/tiger/TIGER2024"
DOWNLOADS = {
    "tl_2024_06_prisecroads.zip": f"{TIGER}/PRISECROADS/tl_2024_06_prisecroads.zip",
    "tl_2024_us_rails.zip": f"{TIGER}/RAILS/tl_2024_us_rails.zip",
    **{f"tl_2024_{c}_areawater.zip": f"{TIGER}/AREAWATER/tl_2024_{c}_areawater.zip" for c in ("06037", "06085")},
    **{f"tl_2024_{c}_linearwater.zip": f"{TIGER}/LINEARWATER/tl_2024_{c}_linearwater.zip" for c in ("06037", "06085")},
}
LA_PARCELS = "https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Parcels_2022Roll/FeatureServer/0/query"
LA_TERMS = ("LA County eGIS Hub Terms of Use (https://egis-lacounty.hub.arcgis.com/pages/terms-of-use): licence to copy, "
            "publish, distribute, adapt and exploit the Data; no endorsement implied")


# ------------------------------------------------------------------------------------------------ downloads
def _manifest() -> dict:
    f = D / "manifest.json"
    return json.loads(f.read_text()) if f.exists() else {"source_id": "parking_ca_city_edges", "files": {}}


def _get(url: str, dest: Path, man: dict, licence: str) -> Path:
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "missing-middleware research (public data)"})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read()
    dest.write_bytes(data)
    man["files"][str(dest.relative_to(D))] = {
        "url": url, "accessed_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "licence": licence}
    (D / "manifest.json").write_text(json.dumps(man, indent=1))
    return dest


def fetch_la_parcels(bbox_ll, man) -> list[Path]:
    """LA County Assessor 2022-roll parcels intersecting the envelope (OBJECTID only), paged."""
    out, off = [], 0
    while True:
        q = {"where": "1=1", "geometry": ",".join(f"{v:.6f}" for v in bbox_ll), "geometryType": "esriGeometryEnvelope",
             "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "outFields": "OBJECTID", "returnGeometry": "true",
             "outSR": 4326, "orderByFields": "OBJECTID", "resultOffset": off, "resultRecordCount": 2000, "f": "geojson"}
        p = _get(f"{LA_PARCELS}?{urllib.parse.urlencode(q)}", D / "la_parcels" / f"culver_page_{off:06d}.geojson", man, LA_TERMS)
        out.append(p)
        n = len(json.loads(p.read_text()).get("features", []))
        if n < 2000:
            return out
        off += 2000
        time.sleep(0.5)


# ------------------------------------------------------------------------------------------------ geometry
def densify_lines(lines: list, step: float) -> np.ndarray:
    pts = []
    for a in lines:
        for p, q in zip(a[:-1], a[1:]):
            n = max(1, int(np.ceil(np.hypot(*(q - p)) / step)))
            t = np.linspace(0, 1, n, endpoint=False)[:, None]
            pts.append(p + t * (q - p))
        pts.append(a[-1:])
    return np.concatenate(pts) if pts else np.zeros((0, 2))


def city_pieces(feature) -> pd.DataFrame:
    """100 m pieces of every ring of the city: midpoint, unit tangent, length, plus 5 m boundary points per piece."""
    rows, bpts = [], []
    for part in feature:
        for ring in part:
            r = ring if np.allclose(ring[0], ring[-1]) else np.r_[ring, ring[:1]]
            seg = np.hypot(*np.diff(r, axis=0).T)
            s = np.r_[0, np.cumsum(seg)]
            L = s[-1]
            n = max(1, int(round(L / PIECE)))
            edges = np.linspace(0, L, n + 1)
            for k in range(n):
                ss = np.linspace(edges[k], edges[k + 1], max(2, int(np.ceil((edges[k + 1] - edges[k]) / 5)) + 1))
                xy = np.c_[np.interp(ss, s, r[:, 0]), np.interp(ss, s, r[:, 1])]
                m = len(xy) // 2
                tng = xy[-1] - xy[0]
                nrm = np.hypot(*tng)
                if nrm == 0:
                    continue
                rows.append({"mx": xy[m, 0], "my": xy[m, 1], "tx": tng[0] / nrm, "ty": tng[1] / nrm,
                             "length": edges[k + 1] - edges[k]})
                bpts.append(np.c_[xy, np.full(len(xy), len(rows) - 1)])
    return pd.DataFrame(rows), np.concatenate(bpts)


def classify_pieces(name, cfg, places, city_feat, counties, repealed, stops_xy, hazards):
    pc, bpts = city_pieces(city_feat)
    nx, ny = -pc.ty.values, pc.tx.values
    test_in = G.points_in_any(pc.mx + 10 * nx, pc.my + 10 * ny, [city_feat])
    sgn = np.where(test_in, -1.0, 1.0)               # outward = leaves the city
    ox, oy = nx * sgn, ny * sgn
    # neighbour 30 m out
    qx, qy = pc.mx.values + 30 * ox, pc.my.values + 30 * oy
    pi = G.points_in_polygons(qx, qy, places.polys)
    ci = G.points_in_polygons(qx, qy, counties.polys)
    nb = np.where(pi >= 0, places.attrs.NAME.values[np.clip(pi, 0, None)], "")
    cnty = np.where(ci >= 0, counties.attrs.GEOID.values[np.clip(ci, 0, None)], "")
    cname = np.where(ci >= 0, counties.attrs.NAME.values[np.clip(ci, 0, None)], "")
    nb = np.where((pi < 0) & (ci >= 0), np.char.add("unincorporated ", cname.astype(str)), nb)
    pc["neighbour"] = nb
    pc["neighbour_juris"] = [n.upper() if not n.startswith("unincorporated") else UNINC_JURIS.get(c, n.upper())
                             for n, c in zip(nb, cnty)]
    pc["neighbour_place_idx"] = pi
    pc["neighbour_county"] = cnty
    pc["drop_no_neighbour"] = nb == ""
    pc["drop_neighbour_repeal"] = pc.neighbour.isin(repealed)
    _, dh = G.nearest(pc.mx.values, pc.my.values, hazards[:, 0], hazards[:, 1])
    pc["drop_physical"] = dh <= ALONG
    near = {}
    for d in PROBES:
        _, ds = G.nearest(pc.mx.values + d * ox, pc.my.values + d * oy, stops_xy[:, 0], stops_xy[:, 1])
        near[d] = ds <= HALF_MILE
    for b in BANDS:
        pc[f"drop_ab2097_{b}"] = np.any([near[d] for d in PROBES if d <= b], axis=0)
        pc[f"usable_{b}"] = ~(pc.drop_no_neighbour | pc.drop_neighbour_repeal | pc.drop_physical | pc[f"drop_ab2097_{b}"])
    pc["city"] = name
    return pc, bpts


# ------------------------------------------------------------------------------------------------ permits
def load_permits(bbox_ll) -> pd.DataFrame:
    cols = ["JURIS_NAME", "CNTY_NAME", "YEAR", "APN", "UNIT_CAT", "NO_BUILDING_PERMITS", "BP_ISSUE_DT1", "LATITUDE",
            "LONGITUDE", "STD_ADDRESS", "STREET_ADDRESS"]
    a = pd.read_csv(RAW / "hcd_apr_a2" / "tablea2.csv", usecols=cols, low_memory=False)
    a["units"] = pd.to_numeric(a["NO_BUILDING_PERMITS"], errors="coerce").fillna(0.0)
    a = a[(a.units > 0) & a.YEAR.isin(range(2018, 2026))].copy()
    lat, lon = pd.to_numeric(a.LATITUDE, errors="coerce"), pd.to_numeric(a.LONGITUDE, errors="coerce")
    a = a[ab.is_geocoded(lat, lon, a.STD_ADDRESS)].copy()
    a["lat"], a["lon"] = pd.to_numeric(a.LATITUDE), pd.to_numeric(a.LONGITUDE)
    bp = pd.to_datetime(a.BP_ISSUE_DT1, errors="coerce")
    a["bp"] = bp
    a["permit_year"] = bp.dt.year.fillna(a.YEAR).astype(int)
    a["addr"] = ab._norm(a.STREET_ADDRESS).where(ab._norm(a.STREET_ADDRESS) != "", ab._norm(a.STD_ADDRESS))
    a["bp_date"] = bp.dt.strftime("%Y-%m-%d").fillna("")
    d1 = a.duplicated(["JURIS_NAME", "addr", "YEAR", "UNIT_CAT", "units"])
    d2 = ~d1 & (a.bp_date != "") & a[~d1].duplicated(["JURIS_NAME", "addr", "UNIT_CAT", "units", "bp_date"]).reindex(
        a.index, fill_value=False)
    a = a[~d1 & ~d2 & a.permit_year.between(2018, 2025)]
    keep = np.zeros(len(a), bool)
    for x0, y0, x1, y1 in bbox_ll:
        keep |= a.lon.between(x0, x1).values & a.lat.between(y0, y1).values
    a = a[keep].copy()
    a["juris"] = a.JURIS_NAME.astype(str).str.upper().str.strip()
    return a.reset_index(drop=True)


def window(p: pd.DataFrame, eff: pd.Timestamp) -> np.ndarray:
    dated = p.bp.notna().values
    bp = p.bp.values
    y = p.permit_year.values
    end = pd.Timestamp("2025-12-31")
    before_end = min(eff - pd.Timedelta(days=1), pd.Timestamp("2022-12-31"))
    w = np.full(len(p), "outside windows", dtype=object)
    w[dated & (bp >= np.datetime64("2018-01-01")) & (bp <= np.datetime64(before_end))] = "before"
    w[dated & (bp >= np.datetime64(eff)) & (bp <= np.datetime64(end))] = "after"
    w[dated & (bp > np.datetime64(before_end)) & (bp < np.datetime64(eff))] = "gap"
    w[~dated & (y < eff.year) & (y >= 2018) & (y <= 2022)] = "before"
    w[~dated & (y > eff.year) & (y <= 2025)] = "after"
    w[~dated & (y == eff.year)] = "ambiguous (undated, effective year)"
    return w


def lot_key(p: pd.DataFrame, county: pd.Series) -> pd.Series:
    digits = p.APN.fillna("").astype(str).str.replace(r"\D", "", regex=True)
    n = county.map(APN_LEN).fillna(0).astype(int)
    padded = pd.Series([d.zfill(k) if d else "" for d, k in zip(digits, n)], index=p.index)
    ok = padded.str.len().eq(n) & ~padded.str.fullmatch(r"0*")
    loc = "loc:" + p.lat.round(5).astype(str) + "," + p.lon.round(5).astype(str)
    return pd.Series(np.where(ok, p.juris + ":" + padded, loc), index=p.index), ok


# ------------------------------------------------------------------------------------------------ main
def main():
    D.mkdir(parents=True, exist_ok=True)
    man = _manifest()
    for f, u in DOWNLOADS.items():
        _get(u, D / f, man, PUBLIC_DOMAIN)

    places = G.read_shapefile(RAW / "census_tiger_2024_ca_place" / "tl_2024_06_place.zip",
                              columns=["GEOID", "NAME", "CLASSFP"]).to_crs(CRS)
    counties = G.read_shapefile(RAW / "census_tiger_2024" / "tl_2024_us_county.zip", columns=["GEOID", "NAME", "STATEFP"])
    counties = counties.subset(counties.attrs.STATEFP.eq("06").values).to_crs(CRS)
    inc = places.subset(places.attrs.CLASSFP.astype(str).str.startswith("C").values)

    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    tax = tax[tax.state.eq("California") & tax.status.eq("adopted") & tax.benchmark_rating.eq("at")]
    repealed_all = set(tax.place)

    s = G.read_geojson(RAW / "ab2097" / "major_transit_stops.geojson", columns=["plan_name"])
    s = s.subset(s.attrs["plan_name"].fillna("").str.strip().eq("").values).to_crs(CRS)
    stops_xy = np.c_[s.x, s.y]

    roads = G.read_shapefile(D / "tl_2024_06_prisecroads.zip", columns=["MTFCC"])
    roads = roads.subset(roads.attrs.MTFCC.eq("S1100").values).to_crs(CRS)
    rails = G.read_shapefile(D / "tl_2024_us_rails.zip", columns=["MTFCC"]).to_crs(CRS)
    lines = [a for f in roads.polys + rails.polys for a in f]
    for c in ("06037", "06085"):
        lw = G.read_shapefile(D / f"tl_2024_{c}_linearwater.zip", columns=["MTFCC"]).to_crs(CRS)
        lines += [a for f in lw.polys for a in f]
        aw = G.read_shapefile(D / f"tl_2024_{c}_areawater.zip", columns=["MTFCC"]).to_crs(CRS)
        lines += [r for f in aw.polys for part in f for r in part]
    hazards = densify_lines(lines, 5.0)

    rows, pieces, bboxes, cityinfo = [], {}, [], {}
    for name, cfg in CITIES.items():
        k = np.flatnonzero(inc.attrs.GEOID.eq(cfg["geoid"]).values)[0]
        feat = inc.polys[k]
        others = inc.subset(~inc.attrs.GEOID.eq(cfg["geoid"]).values)
        repealed = {n for n in others.attrs.NAME if n in repealed_all}
        pc, bpts = classify_pieces(name, cfg, others, feat, counties, repealed, stops_xy, hazards)
        pieces[name] = (pc, bpts, feat, others)
        allxy = np.concatenate([r for part in feat for r in part])
        x0, y0 = allxy.min(0) - 1500
        x1, y1 = allxy.max(0) + 1500
        lon, lat = G.transform(np.array([x0, x1, x0, x1]), np.array([y0, y0, y1, y1]), CRS, 4326)
        bboxes.append((lon.min(), lat.min(), lon.max(), lat.max()))
        lon5, lat5 = G.transform(np.array([x0, x1, x0, x1]) + np.array([1000, -1000, 1000, -1000]),
                                 np.array([y0, y0, y1, y1]) + np.array([1000, 1000, -1000, -1000]), CRS, 4326)
        cityinfo[name] = (lon5.min(), lat5.min(), lon5.max(), lat5.max())   # city extent + 500 m
        L = pc.length.sum()
        rem = pd.Series(True, index=pc.index)
        for reason, col in (("no neighbour (ocean / no land)", "drop_no_neighbour"),
                            ("neighbour repealed for housing citywide", "drop_neighbour_repeal"),
                            ("along freeway, rail or water (within 50 m)", "drop_physical")):
            m = rem & pc[col]
            rows.append(dict(city=name, section="border", band_m="", side="", window="", measure=f"dropped: {reason}",
                             value=round(m.mul(pc.length).sum() / 1000, 3), unit="km of city limit",
                             note=f"of {L/1000:.3f} km total; share {m.mul(pc.length).sum()/L:.3f}"))
            rem &= ~pc[col]
        for b in BANDS:
            m = rem & pc[f"drop_ab2097_{b}"]
            rows.append(dict(city=name, section="border", band_m=b, side="", window="",
                             measure="dropped: neighbour's AB 2097 1/2-mile zone reaches into the band",
                             value=round(m.mul(pc.length).sum() / 1000, 3), unit="km of city limit",
                             note=f"share {m.mul(pc.length).sum()/L:.3f}"))
            u = pc[f"usable_{b}"]
            rows.append(dict(city=name, section="border", band_m=b, side="", window="", measure="usable border",
                             value=round(u.mul(pc.length).sum() / 1000, 3), unit="km of city limit",
                             note=f"share of {L/1000:.3f} km = {u.mul(pc.length).sum()/L:.3f}"))
        nbl = pc.groupby("neighbour").length.sum().sort_values(ascending=False)
        nbu = pc[pc.usable_183].groupby("neighbour").length.sum()
        for n_, l_ in nbl.items():
            rows.append(dict(city=name, section="border by neighbour", band_m=183, side="", window="",
                             measure=f"neighbour: {n_ or '(none)'}", value=round(nbu.get(n_, 0.0) / 1000, 3),
                             unit="km usable at 183 m", note=f"of {l_/1000:.3f} km shared"))

    # Culver City lots from LA County parcels (check)
    pages = fetch_la_parcels(cityinfo["Culver City"], man)
    feats = [f for p in pages for f in json.loads(p.read_text())["features"]]
    parcels = G.read_geojson({"type": "FeatureCollection", "features": feats}, columns=["OBJECTID"]).to_crs(CRS)

    p = load_permits(bboxes)
    x, y = G.transform(p.lon.values, p.lat.values, 4326, CRS)
    _, dstop = G.nearest(x, y, stops_xy[:, 0], stops_xy[:, 1])
    for name, cfg in CITIES.items():
        pc, bpts, feat, others = pieces[name]
        eff = pd.Timestamp(cfg["eff"])
        bi, db = G.nearest(x, y, bpts[:, 0], bpts[:, 1])
        piece = bpts[bi, 2].astype(int)
        inside = G.points_in_any(x, y, [feat])
        pi_ = G.points_in_polygons(x, y, others.polys)
        q = p.copy()
        q["dist"], q["piece"], q["inside"], q["place_idx"] = db, piece, inside, pi_
        q["window"] = window(q, eff)
        q["county_fips"] = np.where(q.CNTY_NAME.astype(str).str.upper().str.contains("SANTA CLARA"), "06085", "06037")
        q["lot"], apn_ok = lot_key(q, q.county_fips)
        q["loc"] = q.lat.round(5).astype(str) + "," + q.lon.round(5).astype(str)
        if name == "Culver City":
            pp = G.points_in_polygons(x, y, parcels.polys)
            rx, ry = G.representative_points(parcels.polys)
            nn, dn = G.nearest(x, y, rx, ry, max_distance=40.0)
            pp = np.where(pp >= 0, pp, nn)          # points on a street centreline: nearest parcel within 40 m
            q["parcel"] = np.where(pp >= 0, pp.astype(str), "loc:" + q["loc"])
        nbp = pc.neighbour_place_idx.values[piece]
        nbj = pc.neighbour_juris.values[piece]
        same_nb = np.where(nbp >= 0, pi_ == nbp, pi_ < 0)
        for b in BANDS:
            band = (q.dist >= DONUT) & (q.dist <= b) & pc[f"usable_{b}"].values[piece]
            jok_in = (q.juris == cfg["juris"]).values
            jok_out = (q.juris.values == nbj)
            ok_in = band & q.inside & jok_in
            ok_out = band & ~q.inside & same_nb & (dstop > HALF_MILE) & jok_out
            dropped_zone = band & ~q.inside & same_nb & (dstop <= HALF_MILE) & jok_out
            for side, mm in (("inside", band & q.inside & ~jok_in), ("outside", band & ~q.inside & same_nb & ~jok_out)):
                rows.append(dict(city=name, section="counts", band_m=b, side=side, window="all (2018-2025)",
                                 measure="records dropped: filed by another jurisdiction than the side's (boundary or geocode mismatch)",
                                 value=int(mm.sum()), unit="records", note=""))
            grp = np.where(pd.Series(nbj).str.endswith("COUNTY").values, "unincorporated county", "neighbouring city")
            for side, m in (("inside", ok_in), ("outside", ok_out)):
                sub = q[m.values]
                for g_ in ("neighbouring city", "unincorporated county"):
                    for w in ("before", "after"):
                        t = sub[(sub.window == w).values & (grp[m.values] == g_)]
                        rows.append(dict(city=name, section="counts by neighbour type", band_m=b, side=side, window=w,
                                         measure=f"lots with new homes, segments facing {g_}", value=t.lot.nunique(),
                                         unit="lots", note=""))
                jm = (sub.juris != cfg["juris"]) if side == "inside" else (sub.juris != nbj[m.values])
                for w in ("before", "after", "gap", "ambiguous (undated, effective year)"):
                    t = sub[sub.window == w]
                    if w in ("gap", "ambiguous (undated, effective year)") and not len(t):
                        continue
                    base = dict(city=name, section="counts", band_m=b, side=side, window=w)
                    rows.append({**base, "measure": "lots with new homes (A2 APN; location if no APN)",
                                 "value": t.lot.nunique(), "unit": "lots",
                                 "note": f"{int((~apn_ok[t.index]).sum())} records without usable APN"})
                    na = t[~t.UNIT_CAT.astype(str).str.upper().str.contains("ADU")]
                    rows.append({**base, "measure": "lots with new homes, non-ADU records only (A2 APN)",
                                 "value": na.lot.nunique(), "unit": "lots",
                                 "note": f"ADU records = {int(len(t) - len(na))} of {len(t)}"})
                    rows.append({**base, "measure": "permit locations with new homes (proxy)",
                                 "value": t["loc"].nunique(), "unit": "locations", "note": "lat/long rounded to 1e-5"})
                    if name == "Culver City":
                        rows.append({**base, "measure": "LA County 2022-roll parcels with new homes",
                                     "value": t.parcel.nunique(), "unit": "parcels",
                                     "note": f"{int(t.parcel.str.startswith('loc:').sum())} records in no parcel"})
                    rows.append({**base, "measure": "permit records", "value": len(t), "unit": "records",
                                 "note": f"{int(jm[t.index].sum())} filed by another jurisdiction than the side's"})
                    rows.append({**base, "measure": "homes permitted", "value": float(t.units.sum()),
                                 "unit": "homes", "note": ""})
            rows.append(dict(city=name, section="counts", band_m=b, side="outside", window="all",
                             measure="records dropped: inside neighbour's AB 2097 zone (lot level)",
                             value=int(dropped_zone.sum()), unit="records", note=""))

    out = pd.DataFrame(rows).astype(object)
    # verdict
    lots = out[(out.section == "counts") & out.measure.str.startswith("lots with new homes") & out.window.isin(["before", "after"])]
    for b in BANDS:
        sub = lots[lots.band_m == b]
        for name in list(CITIES) + ["pooled (both cities)"]:
            s_ = sub if name.startswith("pooled") else sub[sub.city == name]
            cells = s_.groupby(["side", "window"]).value.sum()
            cells = cells.reindex(pd.MultiIndex.from_product([["inside", "outside"], ["before", "after"]]), fill_value=0)
            mn = int(cells.min())
            out.loc[len(out)] = dict(city=name, section="verdict", band_m=b, side="", window="",
                                     measure="smallest cell (lots with new homes)", value=mn, unit="lots",
                                     note=("feasible" if mn >= MIN_LOTS else "NOT feasible") + f" (rule: {MIN_LOTS}+ per cell); "
                                     + "; ".join(f"{s}/{w}={int(v)}" for (s, w), v in cells.items()))
    for name, cfg in CITIES.items():
        out.loc[len(out)] = dict(city=name, section="ordinance", band_m="", side="", window="", measure="effective date",
                                 value=cfg["eff"], unit="date", note=cfg["eff_note"])
        out.loc[len(out)] = dict(city=name, section="ordinance", band_m="", side="", window="", measure="scope",
                                 value="", unit="", note=cfg["scope"])
        out.loc[len(out)] = dict(city=name, section="ordinance", band_m="", side="", window="",
                                 measure="bundled zoning or density change", value="", unit="", note=cfg["zoning"])
    out.to_csv(OUT, index=False)
    print(out.to_string(max_colwidth=90))


if __name__ == "__main__":
    main()
