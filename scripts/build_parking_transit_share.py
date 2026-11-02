"""Round-3 variable V16 (docs/parking/ROUND3_PLAN.md): share of each repeal place's homes in census block
groups whose centre lies within half a mile of a fixed-route transit stop in the federal National Transit Map.
No effects are read.

    uv run python scripts/build_parking_transit_share.py [--fetch]

Inputs (fetched; public domain or CC BY 3.0 US):
  data/raw/census_cb_2024/cb_2024_us_{place,cousub,bg}_500k.zip   Census cartographic boundaries
  NTAD National Transit Map stops (BTS ArcGIS service), queried by each place's bounding box
  data/raw/census_acs5_2024_tbsf/acsdt5y2024-b25002.dat            homes per block group
Output: reference/parking_transit_share.csv; raw stop extracts in data/raw/ntm_stops_parking/

Geometry: missing_middleware.geom (open licence; docs/GEOMETRY.md) plus two local helpers that reproduce what the
script used from shapely/GEOS before the port: the representative point of a polygon (GEOS InteriorPointArea) and the
largest connected piece of (union of half-mile stop buffers) intersected with the place, in square metres.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware import geom  # noqa: E402
from missing_middleware.foundation import parsers  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

CB = RAW / "census_cb_2024"
CB_URL = "https://www2.census.gov/geo/tiger/GENZ2024/shp/{f}"
CB_FILES = ["cb_2024_us_place_500k.zip", "cb_2024_us_cousub_500k.zip", "cb_2024_us_bg_500k.zip"]
NTM = "https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_National_Transit_Map_Stops/FeatureServer/0/query"
STOPS = RAW / "ntm_stops_parking"
HALF_MILE_M = 804.672
UA = {"User-Agent": "missing-middleware research (public data)"}


def _log(path: Path, name: str, url: str, data: bytes) -> None:
    lp = path / "_downloads.json"
    log = json.loads(lp.read_text()) if lp.exists() else {}
    log[name] = {"accessed": dt.date.today().isoformat(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "url": url}
    lp.write_text(json.dumps(dict(sorted(log.items())), indent=2) + "\n")


def fetch_cb() -> None:
    CB.mkdir(parents=True, exist_ok=True)
    for f in CB_FILES:
        if (CB / f).exists():
            continue
        url = CB_URL.format(f=f)
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read()
        (CB / f).write_bytes(data)
        _log(CB, f, url, data)


def stops_in_bbox(key: str, bounds) -> pd.DataFrame:
    """Stops in a bounding box (lon/lat), cached per place."""
    STOPS.mkdir(parents=True, exist_ok=True)
    f = STOPS / f"{key.replace('|', '_')}.json"
    if not f.exists():
        feats, off = [], 0
        while True:
            p = dict(where="1=1", geometry=",".join(f"{b:.5f}" for b in bounds), geometryType="esriGeometryEnvelope",
                     inSR=4326, spatialRel="esriSpatialRelIntersects", outFields="OBJECTID", returnGeometry="true",
                     outSR=4326, f="json", resultOffset=off, resultRecordCount=2000)
            url = NTM + "?" + urllib.parse.urlencode(p)
            d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read())
            if "error" in d:
                raise RuntimeError(d["error"])
            fs = d.get("features", [])
            feats += [{"x": x["geometry"]["x"], "y": x["geometry"]["y"]} for x in fs if x.get("geometry")]
            if not d.get("exceededTransferLimit") and len(fs) < 2000:
                break
            off += len(fs)
        data = json.dumps(feats).encode()
        f.write_bytes(data)
        _log(STOPS, f.name, NTM + " (envelope query; see bounds in reference/parking_transit_share.csv)", data)
    return pd.DataFrame(json.loads(f.read_text()), columns=["x", "y"])


# ------------------------------------------------------------------------------------- local geometry helpers
def _closed(r: np.ndarray) -> np.ndarray:
    return r if len(r) and (r[0] == r[-1]).all() else np.vstack([r, r[:1]])


def interior_points(polys: list) -> tuple[np.ndarray, np.ndarray]:
    """shapely's representative_point (GEOS InteriorPointArea, GEOS >= 3.8), per polygon feature: for each part, a
    horizontal scan line midway between the vertex heights nearest the middle of the part's envelope; the point is
    the middle of the widest interior run along it; the part with the widest run wins (first part on ties)."""
    out = np.full((len(polys), 2), np.nan)
    for k, feat in enumerate(polys):
        best_w = -1.0
        for part in feat:
            rings = [_closed(np.asarray(r, float)) for r in part]
            lo, hi = rings[0][:, 1].min(), rings[0][:, 1].max()
            centre = (lo + hi) / 2.0
            ys = np.concatenate([r[:, 1] for r in rings])
            below, above = ys[ys <= centre], ys[ys > centre]
            lo_y = max(lo, below.max()) if below.size else lo
            hi_y = min(hi, above.min()) if above.size else hi
            scan = (hi_y + lo_y) / 2.0
            xs = []
            for r in rings:
                if scan < r[:, 1].min() or scan > r[:, 1].max():
                    continue
                x0, y0, x1, y1 = r[:-1, 0], r[:-1, 1], r[1:, 0], r[1:, 1]
                m = ~((y0 > scan) & (y1 > scan)) & ~((y0 < scan) & (y1 < scan)) & (y0 != y1)
                m &= ~((y0 == scan) & (y1 < scan)) & ~((y1 == scan) & (y0 < scan))
                x0, y0, x1, y1 = x0[m], y0[m], x1[m], y1[m]
                with np.errstate(divide="ignore", invalid="ignore"):
                    xi = np.where(x0 == x1, x0, x0 + (scan - y0) / ((y1 - y0) / (x1 - x0)))
                xs.append(xi)
            pt, w = rings[0][0].copy(), 0.0
            c = np.sort(np.concatenate(xs)) if xs else np.zeros(0)
            for i in range(0, len(c) - 1, 2):
                if c[i + 1] - c[i] > w:
                    w, pt = c[i + 1] - c[i], np.array([(c[i] + c[i + 1]) / 2.0, scan])
            if w > best_w:
                best_w, out[k] = w, pt
    return out[:, 0], out[:, 1]


def _seg_intersections(seg: np.ndarray, pairs: np.ndarray):
    """Proper crossings of segment pairs (i < j): parameter along i, along j, and the crossing point (computed once,
    from segment i, so both segments split at bit-identical coordinates)."""
    a, b = seg[pairs[:, 0]], seg[pairs[:, 1]]
    rx, ry = a[:, 2] - a[:, 0], a[:, 3] - a[:, 1]
    sx, sy = b[:, 2] - b[:, 0], b[:, 3] - b[:, 1]
    qx, qy = b[:, 0] - a[:, 0], b[:, 1] - a[:, 1]
    d = rx * sy - ry * sx
    with np.errstate(divide="ignore", invalid="ignore"):
        t = (qx * sy - qy * sx) / d
        u = (qx * ry - qy * rx) / d
    ok = (d != 0) & (t > 0) & (t < 1) & (u > 0) & (u < 1)
    t, u, a, rx, ry = t[ok], u[ok], a[ok], rx[ok], ry[ok]
    return pairs[ok], t, u, a[:, 0] + t * rx, a[:, 1] + t * ry


def _buffer_ring(cx: float, cy: float, r: float, quad_segs: int = 16) -> np.ndarray:
    """The polygon shapely/GEOS uses for buffer(r) of a point (64 vertices on the circle), counter-clockwise, closed."""
    n = 4 * quad_segs
    inc = 2.0 * np.pi / n
    ang = -np.arange(n) * inc                      # GEOS walks clockwise from angle 0
    ring = np.c_[cx + r * np.cos(ang), cy + r * np.sin(ang)][::-1]
    return np.vstack([ring, ring[:1]])


def largest_covered_piece(cx: np.ndarray, cy: np.ndarray, r: float, feature: list, max_seg: float = 100.0) -> float:
    """Area of the largest connected piece of (union of r-buffers of the points) intersected with a polygon feature
    (planar CRS units squared). Exact polygon overlay by boundary classification: the result's boundary is made of
    buffer edges inside the polygon and outside every other buffer, and polygon edges inside some buffer; the
    pieces are chained into loops, holes are given to the smallest outer loop around them, and areas come from
    the shoelace formula (Green's theorem)."""
    c = np.unique(np.c_[cx, cy], axis=0)
    nb = len(c)
    if nb == 0 or not feature:
        return 0.0
    # polygon rings oriented with the inside on the left (exterior counter-clockwise, holes clockwise),
    # long edges cut into pieces of at most max_seg so every segment is short (candidate search radius)
    psegs = []
    for part in feature:
        for i, ring in enumerate(part):
            ring = _closed(np.asarray(ring, float))
            area = 0.5 * float(np.dot(ring[:-1, 0], ring[1:, 1]) - np.dot(ring[:-1, 1], ring[1:, 0]))
            if (area < 0) == (i == 0):
                ring = ring[::-1]
            pts = [ring[:1]]
            for p0, p1 in zip(ring[:-1], ring[1:]):
                n = int(np.ceil(np.hypot(*(p1 - p0)) / max_seg))
                if n > 1:
                    f = np.arange(1, n)[:, None] / n
                    pts.append(p0 + f * (p1 - p0))
                pts.append(p1[None])
            ring = np.vstack(pts)
            psegs.append(np.c_[ring[:-1], ring[1:]])
    pseg = np.vstack(psegs)
    pminx, pminy = pseg[:, [0, 2]].min(), pseg[:, [1, 3]].min()
    pmaxx, pmaxy = pseg[:, [0, 2]].max(), pseg[:, [1, 3]].max()
    # buffer polygons; their edges, dropping any edge wholly inside another buffer (both ends within the
    # inscribed circle of the same other buffer: convex, so the whole edge is inside) or outside the polygon's box
    rings = np.stack([_buffer_ring(x, y, r) for x, y in c])            # (nb, 65, 2)
    nv = rings.shape[1] - 1
    bseg = np.concatenate([rings[:, :-1], rings[:, 1:]], axis=2).reshape(-1, 4)
    bown = np.repeat(np.arange(nb), nv)
    tree = cKDTree(c)
    r_in = r * np.cos(np.pi / nv) * (1 - 1e-9)
    vtx = rings[:, :-1].reshape(-1, 2)
    near = tree.query_ball_point(vtx, r_in)
    keep = np.ones(len(bseg), bool)
    for e in range(len(bseg)):
        i = bown[e]
        v0 = e
        v1 = i * nv + (e - i * nv + 1) % nv
        s0 = near[v0]
        if len(s0) > 1 or (s0 and s0[0] != i):
            s = set(s0) & set(near[v1])
            s.discard(i)
            if s:
                keep[e] = False
    keep &= (np.maximum(bseg[:, 0], bseg[:, 2]) >= pminx) & (np.minimum(bseg[:, 0], bseg[:, 2]) <= pmaxx)
    keep &= (np.maximum(bseg[:, 1], bseg[:, 3]) >= pminy) & (np.minimum(bseg[:, 1], bseg[:, 3]) <= pmaxy)
    bseg, bown = bseg[keep], bown[keep]
    seg = np.vstack([bseg, pseg])
    own = np.r_[bown, np.full(len(pseg), -1)]                          # -1 = the polygon
    nseg = len(seg)
    if not len(bseg):
        # no buffer edge on the result's boundary: the polygon is wholly inside the union, or the union misses it
        x0, y0 = pseg[0, 0], pseg[0, 1]
        inside = len(tree.query_ball_point([x0, y0], r_in)) > 0
        return float(geom.feature_area(feature)) if inside else 0.0
    # crossings between segments of different owners (not polygon with polygon)
    mid = (seg[:, :2] + seg[:, 2:]) / 2
    half = np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1]).max()
    pairs = cKDTree(mid).query_pairs(half * (1 + 1e-9), output_type="ndarray")
    if len(pairs):
        pairs = np.sort(pairs, axis=1)
        pairs = pairs[(own[pairs[:, 0]] != own[pairs[:, 1]])]
    pr, t, u, ix, iy = _seg_intersections(seg, pairs) if len(pairs) else (np.zeros((0, 2), int), *[np.zeros(0)] * 4)
    # split every segment at its crossings: rows (segment, parameter, x, y), endpoints included
    sid = np.r_[np.arange(nseg), np.arange(nseg), pr[:, 0], pr[:, 1]]
    par = np.r_[np.zeros(nseg), np.ones(nseg), t, u]
    px = np.r_[seg[:, 0], seg[:, 2], ix, ix]
    py = np.r_[seg[:, 1], seg[:, 3], iy, iy]
    o = np.lexsort((par, sid))
    sid, px, py = sid[o], px[o], py[o]
    same = sid[:-1] == sid[1:]
    sub = np.c_[px[:-1], py[:-1], px[1:], py[1:]][same]
    sown = own[sid[:-1][same]]
    mx, my = (sub[:, 0] + sub[:, 2]) / 2, (sub[:, 1] + sub[:, 3]) / 2
    # classify sub-segments by their midpoints
    in_poly = geom.points_in_feature(mx, my, feature)
    cand = tree.query_ball_point(np.c_[mx, my], r * (1 + 1e-9))
    qi = np.repeat(np.arange(len(sub)), [len(x) for x in cand])
    qj = np.fromiter((j for x in cand for j in x), int, len(qi))
    ex, ey = rings[qj, :-1, 0], rings[qj, :-1, 1]
    fx, fy = rings[qj, 1:, 0] - ex, rings[qj, 1:, 1] - ey
    strictly_in = ((fx * (my[qi, None] - ey) - fy * (mx[qi, None] - ex)) > 0).all(axis=1)
    in_other = np.zeros(len(sub), bool)
    in_any = np.zeros(len(sub), bool)
    np.logical_or.at(in_any, qi[strictly_in], True)
    np.logical_or.at(in_other, qi[strictly_in & (qj != sown[qi])], True)
    keep = np.where(sown >= 0, in_poly & ~in_other, in_any)
    sub = sub[keep]
    if not len(sub):
        return 0.0
    # loops: follow each kept sub-segment (inside on its left) to the next one leaving its end point; where several
    # leave the same point (pieces touching at a corner) take the sharpest left turn, so touching pieces stay
    # separate loops, as GEOS keeps them separate polygons
    ends = np.r_[sub[:, :2], sub[:, 2:]]
    _, key = np.unique(ends, axis=0, return_inverse=True)
    key = key.ravel()
    m = len(sub)
    a, b = key[:m], key[m:]
    order = np.argsort(a, kind="stable")
    start = np.searchsorted(a[order], np.arange(key.max() + 2))
    succ = np.empty(m, int)
    for e in range(m):
        outs = order[start[b[e]]:start[b[e] + 1]]
        if len(outs) == 1:
            succ[e] = outs[0]
            continue
        dx, dy = sub[e, 2] - sub[e, 0], sub[e, 3] - sub[e, 1]
        ox, oy = sub[outs, 2] - sub[outs, 0], sub[outs, 3] - sub[outs, 1]
        succ[e] = outs[np.argmax(np.arctan2(dx * oy - dy * ox, dx * ox + dy * oy))]
    g = coo_matrix((np.ones(m), (np.arange(m), succ)), shape=(m, m))
    _, loop = connected_components(g, directed=False)
    x0, y0 = c[0]                                   # shoelace relative to a nearby origin, for precision
    cross = 0.5 * ((sub[:, 0] - x0) * (sub[:, 3] - y0) - (sub[:, 2] - x0) * (sub[:, 1] - y0))
    nl = loop.max() + 1
    larea = np.bincount(loop, weights=cross, minlength=nl)
    outers = np.flatnonzero(larea > 0)
    comp = {k: larea[k] for k in outers}
    first = np.full(nl, -1)
    first[loop[::-1]] = np.arange(m)[::-1]
    for h in np.flatnonzero(larea < 0):
        e = first[h]
        hx, hy = (sub[e, 0] + sub[e, 2]) / 2, (sub[e, 1] + sub[e, 3]) / 2
        best = None
        for k in outers:
            if larea[k] <= -larea[h]:
                continue
            s = sub[loop == k]
            y0, y1 = s[:, 1], s[:, 3]
            cnd = (y0 > hy) != (y1 > hy)
            xi = s[cnd, 0] + (hy - y0[cnd]) * (s[cnd, 2] - s[cnd, 0]) / (y1[cnd] - y0[cnd])
            if np.count_nonzero(hx < xi) % 2 and (best is None or larea[k] < larea[best]):
                best = k
        if best is not None:
            comp[best] += larea[h]
    return float(max(comp.values())) if comp else 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    fetch_cb()
    v = pd.read_csv(REFERENCE / "parking_round3_vars.csv", dtype={"acs_geoid": str})
    place = geom.read_shapefile(CB / "cb_2024_us_place_500k.zip", columns=["GEOID"])
    cous = geom.read_shapefile(CB / "cb_2024_us_cousub_500k.zip", columns=["GEOID"])
    # boundary per area (NAD83 longitude/latitude, the same as EPSG:4326 for this purpose)
    poly = {**dict(zip("160|" + place.attrs["GEOID"], place.polys)), **dict(zip("060|" + cous.attrs["GEOID"], cous.polys))}
    bg = geom.read_shapefile(CB / "cb_2024_us_bg_500k.zip", columns=["GEOID", "STATEFP"])
    states = {k.split("|")[1][:2] for k in v["acs_geoid"].dropna()}
    bg = bg.subset(bg.attrs["STATEFP"].isin(states)).to_crs(5070)
    bx, by = interior_points(bg.polys)
    h = parsers.read_acs_sf(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", state_fips="", sumlevels=("150",))
    homes = h.set_index("geoid")["B25002_E001"]
    bg_homes = bg.attrs["GEOID"].map(homes).fillna(0).to_numpy()
    rows = []
    for r in v.itertuples():
        if r.acs_geoid not in poly:
            rows.append(dict(prn_key=r.prn_key, place=r.place, V16_share_homes_near_transit=np.nan, note="no boundary"))
            continue
        shp = poly[r.acs_geoid]
        shp5070 = geom.Layer(pd.DataFrame(index=[0]), "polygon", polys=[shp], crs=place.crs).to_crs(5070).polys[0]
        inside = geom.points_in_feature(bx, by, shp5070)
        ix, iy, ih = bx[inside], by[inside], bg_homes[inside]
        allxy = np.concatenate([rg for part in shp for rg in part])
        minx, miny = allxy.min(axis=0)
        maxx, maxy = allxy.max(axis=0)
        pad = 0.012
        st = stops_in_bbox(r.key, (minx - pad, miny - pad, maxx + pad, maxy + pad))
        tot = ih.sum()
        if st.empty or tot == 0:
            share = 0.0 if tot else np.nan
            n_stops = 0
            island = 0.0
        else:
            sx, sy = geom.transform(st["x"].to_numpy(), st["y"].to_numpy(), 4326, 5070)
            _, dist = geom.nearest(ix, iy, sx, sy)
            near = dist <= HALF_MILE_M
            share = float(ih[near].sum() / tot)
            n_stops = len(st)
            # island size (owner, 2026-10-27, from the TOD work): the largest continuous patch of land within
            # half a mile of a stop, inside the place, in acres
            island = largest_covered_piece(sx, sy, HALF_MILE_M, shp5070) / 4046.8564224
        rows.append(dict(prn_key=r.prn_key, place=r.place, block_groups=int(inside.sum()), homes_in_bgs=tot, stops_in_bbox=n_stops,
                         bounds=f"{minx:.4f},{miny:.4f},{maxx:.4f},{maxy:.4f}", V16_share_homes_near_transit=share,
                         V19_log_island_acres=float(np.log10(island + 1))))
    out = pd.DataFrame(rows)
    out.round(4).to_csv(REFERENCE / "parking_transit_share.csv", index=False)
    print(out["V16_share_homes_near_transit"].describe().round(3).to_dict(), (out["V16_share_homes_near_transit"] == 0).sum())

if __name__ == "__main__":
    main()
