"""Round-3 variables V17-V18 (docs/parking/ROUND3_PLAN.md): surface parking inside each repeal place,
from OpenStreetMap. No effects are read.

Evaluated, not used (2026-10-27): OpenStreetMap is ODbL (share-alike), which the project does not distribute
(owner decision D5), and the variables failed the round-3 test. The output is written to data/processed/parking/
(git-ignored), not to reference/.

  V17 share of land area in surface parking lots
  V18 share of that parking in large contiguous sites (>= 2 acres after joining lots within 30 m)

    uv run --all-extras python scripts/build_parking_surface_lots.py
Raw Overpass extracts: data/raw/osm_parking_lots/ (with _downloads.json); output data/processed/parking/parking_surface_lots.csv

Geometry: missing_middleware.geom (open licence; docs/GEOMETRY.md) plus local helpers for what the script used from
shapely/GEOS before the port: each lot clipped to the place (exact, by boundary classification) and lots joined when
their 15 m buffers meet (boundaries within 30 m of each other, or one lot overlapping another).
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
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware import geom  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

OSM = RAW / "osm_parking_lots"
OVERPASS = "https://overpass-api.de/api/interpreter"
CB = RAW / "census_cb_2024"
ACRE_M2 = 4046.8564224
UA = {"User-Agent": "missing-middleware research (public data; contact via repository)"}


def query(key: str, bounds) -> list:
    OSM.mkdir(parents=True, exist_ok=True)
    f = OSM / f"{key.replace('|', '_')}.json"
    if not f.exists():
        s, w, n, e = bounds[1], bounds[0], bounds[3], bounds[2]
        q = (f'[out:json][timeout:120];(way["amenity"="parking"]({s},{w},{n},{e}););out geom;')
        data = None
        for attempt in range(6):
            try:
                req = urllib.request.Request(OVERPASS, data=urllib.parse.urlencode({"data": q}).encode(), headers=UA)
                data = urllib.request.urlopen(req, timeout=200).read()
                break
            except Exception:
                time.sleep(20 * (attempt + 1))
        if data is None:
            return None
        f.write_bytes(data)
        lp = OSM / "_downloads.json"
        log = json.loads(lp.read_text()) if lp.exists() else {}
        log[f.name] = {"accessed": dt.date.today().isoformat(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                       "url": OVERPASS, "query": q, "licence": "ODbL 1.0, (c) OpenStreetMap contributors"}
        lp.write_text(json.dumps(dict(sorted(log.items())), indent=2) + "\n")
        time.sleep(5)
    return json.loads(f.read_text()).get("elements", [])


def lots(elements) -> list:
    """Closed OpenStreetMap ways of surface parking, as (n, 2) longitude/latitude rings."""
    polys = []
    for el in elements:
        tags = el.get("tags", {})
        if tags.get("parking") in ("multi-storey", "underground", "rooftop", "street_side", "lane", "on_street"):
            continue
        g = el.get("geometry") or []
        if len(g) >= 4 and g[0] == g[-1]:
            polys.append(np.array([(p["lon"], p["lat"]) for p in g], float))
    return polys


# ------------------------------------------------------------------------------------- local geometry helpers
def _signed_area(ring: np.ndarray) -> float:
    """Shoelace area, with coordinates taken relative to the first vertex (as GEOS does) to keep precision."""
    x, y = ring[:, 0] - ring[0, 0], ring[:, 1] - ring[0, 1]
    return 0.5 * float(np.dot(x[:-1], y[1:]) - np.dot(y[:-1], x[1:]))


def _segs(ring: np.ndarray) -> np.ndarray:
    return np.c_[ring[:-1], ring[1:]]


def _crossings(a: np.ndarray, b: np.ndarray):
    """All proper crossings between segments a (n, 4) and b (m, 4): index in a, index in b, parameter along each,
    and the point (computed once, from a)."""
    rx, ry = (a[:, 2] - a[:, 0])[:, None], (a[:, 3] - a[:, 1])[:, None]
    sx, sy = (b[:, 2] - b[:, 0])[None], (b[:, 3] - b[:, 1])[None]
    qx, qy = b[None, :, 0] - a[:, 0, None], b[None, :, 1] - a[:, 1, None]
    d = rx * sy - ry * sx
    with np.errstate(divide="ignore", invalid="ignore"):
        t = (qx * sy - qy * sx) / d
        u = (qx * ry - qy * rx) / d
    i, j = np.nonzero((d != 0) & (t > 0) & (t < 1) & (u > 0) & (u < 1))
    t, u = t[i, j], u[i, j]
    return i, j, t, u, a[i, 0] + t * (a[i, 2] - a[i, 0]), a[i, 1] + t * (a[i, 3] - a[i, 1])


def _split(seg: np.ndarray, idx: np.ndarray, par: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    n = len(seg)
    sid = np.r_[np.arange(n), np.arange(n), idx]
    p = np.r_[np.zeros(n), np.ones(n), par]
    px, py = np.r_[seg[:, 0], seg[:, 2], x], np.r_[seg[:, 1], seg[:, 3], y]
    o = np.lexsort((p, sid))
    sid, px, py = sid[o], px[o], py[o]
    same = sid[:-1] == sid[1:]
    return np.c_[px[:-1], py[:-1], px[1:], py[1:]][same]


def _in_ring(px, py, seg: np.ndarray) -> np.ndarray:
    """Even-odd point-in-polygon against a set of boundary segments (rings in any order)."""
    y0, y1 = seg[:, 1], seg[:, 3]
    Y, X = np.asarray(py)[:, None], np.asarray(px)[:, None]
    c = (y0 > Y) != (y1 > Y)
    with np.errstate(divide="ignore", invalid="ignore"):
        xi = seg[:, 0] + (Y - y0) * (seg[:, 2] - seg[:, 0]) / (y1 - y0)
    return (np.count_nonzero(c & (X < xi), axis=1) % 2) == 1


def clip_lots(rings: list, feature: list, max_seg: float = 50.0):
    """Each lot ring (projected, closed) intersected with a polygon feature: whether it meets the polygon, the area
    of the intersection, and the intersection's separate pieces, each as boundary segments (inside on the left)."""
    psegs = []
    for part in feature:
        for k, ring in enumerate(part):
            ring = np.asarray(ring, float)
            if (_signed_area(ring) < 0) == (k == 0):
                ring = ring[::-1]
            pts = [ring[:1]]
            for p0, p1 in zip(ring[:-1], ring[1:]):
                n = int(np.ceil(np.hypot(*(p1 - p0)) / max_seg))
                if n > 1:
                    pts.append(p0 + np.arange(1, n)[:, None] / n * (p1 - p0))
                pts.append(p1[None])
            psegs.append(_segs(np.vstack(pts)))
    pseg = np.vstack(psegs)
    ptree = cKDTree((pseg[:, :2] + pseg[:, 2:]) / 2)
    lo = np.array([r.min(axis=0) for r in rings])
    hi = np.array([r.max(axis=0) for r in rings])
    cand = ptree.query_ball_point((lo + hi) / 2, np.hypot(*(hi - lo).T) / 2 + max_seg / 2 * (1 + 1e-9))
    first_in = geom.points_in_feature([r[0, 0] for r in rings], [r[0, 1] for r in rings], feature)
    meets, area, bnd = np.zeros(len(rings), bool), np.zeros(len(rings)), [None] * len(rings)
    for k, ring in enumerate(rings):
        a = _signed_area(ring)
        if a < 0:
            ring, a = ring[::-1], -a
        ls = _segs(ring)
        ps = pseg[cand[k]] if cand[k] else pseg[:0]
        i, j, t, u, x, y = _crossings(ls, ps) if len(ps) else (np.zeros(0, int),) * 6
        if not len(i):
            if first_in[k]:
                meets[k], area[k], bnd[k] = True, a, [ls]
            continue
        lsub = _split(ls, i, t, x, y)
        psub = _split(ps, j, u, x, y)
        lsub = lsub[geom.points_in_feature((lsub[:, 0] + lsub[:, 2]) / 2, (lsub[:, 1] + lsub[:, 3]) / 2, feature)]
        psub = psub[_in_ring((psub[:, 0] + psub[:, 2]) / 2, (psub[:, 1] + psub[:, 3]) / 2, ls)]
        b = np.vstack([lsub, psub])
        meets[k], bnd[k] = True, _pieces(b)
        x0, y0 = ring[0]
        area[k] = 0.5 * float(((b[:, 0] - x0) * (b[:, 3] - y0) - (b[:, 2] - x0) * (b[:, 1] - y0)).sum())
    return meets, area, bnd


def _pieces(b: np.ndarray) -> list:
    """Split boundary segments into connected loops; keep the outer ones (positive area): the separate polygons
    of a lot that the place boundary cuts in two (GEOS returns these as a MultiPolygon)."""
    _, key = np.unique(np.r_[b[:, :2], b[:, 2:]], axis=0, return_inverse=True)
    key = key.ravel()
    m = len(b)
    g = coo_matrix((np.ones(m), (key[:m], key[m:])), shape=(key.max() + 1,) * 2)
    lab = connected_components(g, directed=False)[1][key[:m]]
    x0, y0 = b[0, 0], b[0, 1]
    cr = (b[:, 0] - x0) * (b[:, 3] - y0) - (b[:, 2] - x0) * (b[:, 1] - y0)
    out = [b[lab == k] for k in np.unique(lab) if cr[lab == k].sum() > 0]
    return out or [b]


def _buffer_pieces(seg: np.ndarray, r: float, quad_segs: int = 16) -> list:
    """The polygon GEOS draws for buffer(r) around a loop of segments (inside on the left), as convex pieces: one
    rectangle per edge and one fan per convex corner, the fan's points on the circle at the angles GEOS uses
    (quadrant split into quad_segs; the turn divided into round(turn / quantum) equal steps)."""
    q = np.pi / 2 / quad_segs
    L = np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1])
    seg = seg[L > 0]
    L = L[L > 0]
    nx, ny = (seg[:, 3] - seg[:, 1]) / L * r, -(seg[:, 2] - seg[:, 0]) / L * r      # outward (right-hand) offsets
    out = [np.array([[s[0], s[1]], [s[2], s[3]], [s[2] + ax, s[3] + ay], [s[0] + ax, s[1] + ay]])
           for s, ax, ay in zip(seg, nx, ny)]
    start = {(s[0], s[1]): i for i, s in enumerate(seg)}
    for i, s in enumerate(seg):
        j = start.get((s[2], s[3]))
        if j is None:
            continue
        d0, d1 = (s[2] - s[0], s[3] - s[1]), (seg[j, 2] - seg[j, 0], seg[j, 3] - seg[j, 1])
        if d0[0] * d1[1] - d0[1] * d1[0] <= 0:                  # not a convex corner: the rectangles cover it
            continue
        a0, a1 = np.arctan2(ny[i], nx[i]), np.arctan2(ny[j], nx[j])
        if a1 <= a0:
            a1 += 2 * np.pi
        n = max(1, int((a1 - a0) / q + 0.5))
        ang = a0 + np.arange(n + 1) * (a1 - a0) / n
        out.append(np.vstack([[s[2], s[3]], np.c_[s[2] + r * np.cos(ang), s[3] + r * np.sin(ang)]]))
    return out


def _convex_overlap(p: np.ndarray, q: np.ndarray) -> bool:
    """Separating-axis test for two convex polygons (vertex arrays); touching counts as meeting."""
    for poly in (p, q):
        e = np.roll(poly, -1, axis=0) - poly
        ax = np.c_[-e[:, 1], e[:, 0]]
        ax = ax[(ax != 0).any(axis=1)]
        pp, qq = p @ ax.T, q @ ax.T
        if ((pp.max(axis=0) < qq.min(axis=0)) | (qq.max(axis=0) < pp.min(axis=0))).any():
            return False
    return True


def _buffers_meet(a: np.ndarray, b: np.ndarray, r: float) -> bool:
    """Whether the GEOS-style polygonal r-buffers of two loops meet, checking only the parts near each other."""
    d = _seg_dist(np.repeat(a, len(b), axis=0), np.tile(b, (len(a), 1))).reshape(len(a), len(b))
    a, b = a[d.min(axis=1) <= 2 * r + 1], b[d.min(axis=0) <= 2 * r + 1]
    pa, pb = _buffer_pieces(a, r), _buffer_pieces(b, r)
    return any(_convex_overlap(x, y) for x in pa for y in pb)


def _seg_dist(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Distance between segment pairs (rows of a and b); 0 where they cross."""
    def pt_seg(px, py, s):
        dx, dy = s[:, 2] - s[:, 0], s[:, 3] - s[:, 1]
        L = dx * dx + dy * dy
        t = np.clip(((px - s[:, 0]) * dx + (py - s[:, 1]) * dy) / np.where(L > 0, L, 1), 0, 1)
        return np.hypot(s[:, 0] + t * dx - px, s[:, 1] + t * dy - py)
    d = np.minimum.reduce([pt_seg(a[:, 0], a[:, 1], b), pt_seg(a[:, 2], a[:, 3], b),
                           pt_seg(b[:, 0], b[:, 1], a), pt_seg(b[:, 2], b[:, 3], a)])
    rx, ry, sx, sy = a[:, 2] - a[:, 0], a[:, 3] - a[:, 1], b[:, 2] - b[:, 0], b[:, 3] - b[:, 1]
    qx, qy = b[:, 0] - a[:, 0], b[:, 1] - a[:, 1]
    den = rx * sy - ry * sx
    with np.errstate(divide="ignore", invalid="ignore"):
        t, u = (qx * sy - qy * sx) / den, (qx * ry - qy * rx) / den
    return np.where((den != 0) & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1), 0.0, d)


def joined_groups(bnd: list, buffer_m: float, piece: float = 20.0) -> np.ndarray:
    """Group label per piece: pieces are joined when their buffer_m buffers meet, i.e. their boundaries come within
    2 * buffer_m of each other (exactly as drawn by GEOS near the threshold) or one lies inside another; groups are
    the connected components."""
    n = len(bnd)
    slack = np.cos(0.75 * np.pi / 32)            # within this, the drawn buffers surely meet (chord sag <= 0.75 step)
    seg = np.vstack(bnd)
    own = np.repeat(np.arange(n), [len(b) for b in bnd])
    # cut segments into short pieces only to find candidate pairs; distances use the whole segments
    L = np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1])
    k = np.maximum(1, np.ceil(L / piece)).astype(int)
    sid = np.repeat(np.arange(len(seg)), k)
    f = (np.arange(len(sid)) - np.repeat(np.cumsum(k) - k, k) + 0.5) / np.repeat(k, k)
    mid = seg[sid, :2] + f[:, None] * (seg[sid, 2:] - seg[sid, :2])
    pairs = cKDTree(mid).query_pairs(2 * buffer_m + piece * (1 + 1e-9), output_type="ndarray")
    links = []
    if len(pairs):
        sp = np.unique(np.sort(sid[pairs], axis=1), axis=0)
        sp = sp[own[sp[:, 0]] != own[sp[:, 1]]]
        for s in range(0, len(sp), 1_000_000):
            q = sp[s:s + 1_000_000]
            d = _seg_dist(seg[q[:, 0]], seg[q[:, 1]])
            links.append(np.c_[own[q[d <= 2 * buffer_m * slack, 0]], own[q[d <= 2 * buffer_m * slack, 1]]])
            near = np.unique(np.c_[own[q[:, 0]], own[q[:, 1]]][(d > 2 * buffer_m * slack) & (d <= 2 * buffer_m)], axis=0)
            # GEOS draws the rounded corners of a buffer as chords, so near the threshold test the drawn buffers
            for i, j in near:
                if _buffers_meet(bnd[i], bnd[j], buffer_m):
                    links.append(np.array([[i, j]]))
    # a lot lying wholly inside another (boundaries farther apart than 2 * buffer_m)
    lo = np.array([b[:, [0, 2]].min() for b in bnd]), np.array([b[:, [1, 3]].min() for b in bnd])
    hi = np.array([b[:, [0, 2]].max() for b in bnd]), np.array([b[:, [1, 3]].max() for b in bnd])
    fx, fy = np.array([b[0, 0] for b in bnd]), np.array([b[0, 1] for b in bnd])
    for j in range(n):
        c = np.flatnonzero((fx > lo[0][j]) & (fx < hi[0][j]) & (fy > lo[1][j]) & (fy < hi[1][j]))
        c = c[c != j]
        if len(c):
            c = c[_in_ring(fx[c], fy[c], bnd[j])]
            links.append(np.c_[c, np.full(len(c), j)])
    e = np.vstack(links) if links else np.zeros((0, 2), int)
    g = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    return connected_components(g, directed=False)[1]


def main() -> None:
    v = pd.read_csv(REFERENCE / "parking_round3_vars.csv", dtype={"acs_geoid": str})
    place = geom.read_shapefile(CB / "cb_2024_us_place_500k.zip", columns=["GEOID", "ALAND"])
    cous = geom.read_shapefile(CB / "cb_2024_us_cousub_500k.zip", columns=["GEOID", "ALAND"])
    # boundary and land area per area (NAD83 longitude/latitude, the same as EPSG:4326 for this purpose)
    poly = {**{"160|" + g: (f, a) for g, a, f in zip(place.attrs["GEOID"], place.attrs["ALAND"], place.polys)},
            **{"060|" + g: (f, a) for g, a, f in zip(cous.attrs["GEOID"], cous.attrs["ALAND"], cous.polys)}}
    rows = []
    for r in v.itertuples():
        if r.acs_geoid not in poly:
            rows.append(dict(prn_key=r.prn_key, place=r.place, note="no boundary"))
            continue
        shp, aland = poly[r.acs_geoid]
        allxy = np.concatenate([rg for part in shp for rg in part])
        els = query(r.key, (*allxy.min(axis=0), *allxy.max(axis=0)))
        if els is None:
            rows.append(dict(prn_key=r.prn_key, place=r.place, note="OpenStreetMap download failed"))
            continue
        g = lots(els)
        land_m2 = float(aland)
        if not g:
            rows.append(dict(prn_key=r.prn_key, place=r.place, lots=0, V17_share_land_surface_parking=0.0, V18_share_parking_in_large_sites=np.nan))
            continue
        g = [np.column_stack(geom.transform(q[:, 0], q[:, 1], 4326, 5070)) for q in g]
        boundary = geom.Layer(pd.DataFrame(index=[0]), "polygon", polys=[shp], crs=place.crs).to_crs(5070).polys[0]
        meets, lot_area, bnd = clip_lots(g, boundary)
        lot_area = lot_area[meets]
        bnd = [b for b, m in zip(bnd, meets) if m]
        area = lot_area.sum()
        # a lot cut into several pieces by the boundary counts in every joined site that one of its pieces is in
        node_lot = np.repeat(np.arange(len(bnd)), [len(b) for b in bnd])
        grp = joined_groups([p for b in bnd for p in b], 15.0)
        lg = np.unique(np.c_[node_lot, grp], axis=0)
        per = np.bincount(lg[:, 1], weights=lot_area[lg[:, 0]])
        big = float(per[per >= 2 * ACRE_M2].sum())
        rows.append(dict(prn_key=r.prn_key, place=r.place, lots=int(meets.sum()), parking_acres=area / ACRE_M2, land_acres=land_m2 / ACRE_M2,
                         V17_share_land_surface_parking=area / land_m2 if land_m2 else np.nan,
                         V18_share_parking_in_large_sites=big / area if area else np.nan))
    out = pd.DataFrame(rows)
    out_dir = REFERENCE.parent / "data" / "processed" / "parking"
    out_dir.mkdir(parents=True, exist_ok=True)
    out.round(5).to_csv(out_dir / "parking_surface_lots.csv", index=False)
    print(out[["lots", "V17_share_land_surface_parking", "V18_share_parking_in_large_sites"]].describe().round(4))


if __name__ == "__main__":
    main()
