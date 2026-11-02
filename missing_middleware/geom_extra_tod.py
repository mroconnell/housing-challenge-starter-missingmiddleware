"""Geometry the TOD chain needs beyond missing_middleware.geom (numpy, scipy and the standard library only).

Same geometry model as missing_middleware.geom: points are x, y arrays; a polygon feature is a list of parts, each
part a list of rings (exterior first, then holes), each ring an (n, 2) array; a line feature is a list of (n, 2)
arrays. Coordinates are projected, in metres.

- interior_points: the point GEOS (and so shapely's representative_point) returns for a polygon, reproduced from
  GEOS's InteriorPointArea algorithm (horizontal scan line through the middle of the envelope, nudged off vertex
  heights; midpoint of the widest interior section; widest polygon of a multipolygon). Kept so lots keep exactly
  the same reference point as before the port.
- feature_key: bytes identifying a geometry's exact coordinates and type (stands in for WKB when grouping identical
  outlines).
- points_near_lines: points within a distance of any line (a "dwithin" query).
- nearest_polygon / distance_to_polygons_exact: nearest polygon and exact distance with no cap (0 inside).
- polygon_distance, components_within: distance between polygon features; groups of features within a distance.
- min_area_rectangle_sides: sides of the minimum-area enclosing rectangle (GEOS minimum_rotated_rectangle).
- intersection_area: area shared by two polygon features (boundary integral; handles holes and shared edges).
"""
from __future__ import annotations

import numpy as np
from scipy.spatial import ConvexHull, cKDTree

from missing_middleware import geom as G


# ---------------------------------------------------------------------------------------------- interior point
def _scan_y(poly_rings: list) -> float:
    """GEOS ScanLineYOrdinateFinder: the middle of the gap between vertex heights around the envelope centre."""
    ext = poly_rings[0]
    lo, hi = float(ext[:, 1].min()), float(ext[:, 1].max())
    centre = (lo + hi) / 2.0
    for r in poly_rings:
        y = r[:, 1]
        below = y[(y <= centre) & (y > lo)]
        above = y[(y > centre) & (y < hi)]
        if len(below):
            lo = float(below.max())
        if len(above):
            hi = float(above.min())
    return (hi + lo) / 2.0


def _closed(r: np.ndarray) -> np.ndarray:
    return r if len(r) and np.array_equal(r[0], r[-1]) else np.vstack([r, r[:1]])


def _interior_point_polygon(rings: list) -> tuple[float, float, float]:
    """(x, y, width) for one polygon (exterior + holes), as GEOS InteriorPointPolygon."""
    Y = _scan_y(rings)
    crossings = []
    for r in rings:
        r = _closed(r)
        if not (r[:, 1].min() <= Y <= r[:, 1].max()):
            continue
        p0, p1 = r[:-1], r[1:]
        y0, y1, x0, x1 = p0[:, 1], p1[:, 1], p0[:, 0], p1[:, 0]
        hits = ~(((y0 > Y) & (y1 > Y)) | ((y0 < Y) & (y1 < Y)))
        hits &= y0 != y1                                   # horizontal segments skipped
        hits &= ~((y0 == Y) & (y1 < Y))                    # downward segment excludes its start point
        hits &= ~((y1 == Y) & (y0 < Y))                    # upward segment excludes its end point
        for a, b, c, d in zip(x0[hits], y0[hits], x1[hits], y1[hits]):
            if a == c:
                crossings.append(float(a))
            else:
                m = (d - b) / (c - a)
                crossings.append(float(a + (Y - b) / m))
    x, y, width = float(rings[0][0, 0]), float(rings[0][0, 1]), 0.0   # default (zero area): first vertex
    crossings.sort()
    for i in range(0, len(crossings) - 1, 2):
        w = crossings[i + 1] - crossings[i]
        if w > width:
            width, x, y = w, (crossings[i] + crossings[i + 1]) / 2.0, Y
    return x, y, width


def interior_points(polys: list) -> tuple[np.ndarray, np.ndarray]:
    """A point inside each polygon feature, identical to GEOS InteriorPointArea (shapely representative_point)."""
    xs = np.full(len(polys), np.nan)
    ys = np.full(len(polys), np.nan)
    for k, f in enumerate(polys):
        best = -1.0
        for part in f or []:
            if not len(part) or len(part[0]) == 0:
                continue
            x, y, w = _interior_point_polygon(part)
            if w > best:
                best, xs[k], ys[k] = w, x, y
    return xs, ys


# ------------------------------------------------------------------------------------------------- feature key
def feature_key(feature, gtype: str = "") -> bytes | None:
    """Exact identity of a geometry (type, part and ring structure, coordinates): equal keys = identical outlines."""
    if not feature:
        return None
    out = [gtype.encode()]
    for part in feature:
        rings = part if isinstance(part, list) else [part]
        out.append(b"P%d" % len(rings))
        for r in rings:
            a = np.ascontiguousarray(r, dtype="<f8")
            out.append(b"R%d" % len(a))
            out.append(a.tobytes())
    return b"".join(out)


# ------------------------------------------------------------------------------------------------ segments
def _split_long(seg: np.ndarray, owner: np.ndarray, max_len: float):
    """Split segments longer than max_len into equal pieces (distances are unchanged; the spatial index is tighter)."""
    L = np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1])
    n = np.maximum(1, np.ceil(L / max_len)).astype(int)
    if (n == 1).all():
        return seg, owner
    rep = np.repeat(np.arange(len(seg)), n)
    k = np.concatenate([np.arange(m) for m in n])
    nn = n[rep].astype(float)
    a, b = seg[rep, :2], seg[rep, 2:]
    t0, t1 = (k / nn)[:, None], ((k + 1) / nn)[:, None]
    p0 = a + (b - a) * t0
    p1 = np.where(t1 == 1.0, b, a + (b - a) * t1)
    return np.c_[p0, p1], owner[rep]


def _line_segments(lines: list):
    seg, owner = [], []
    for k, f in enumerate(lines):
        for part in f or []:
            part = np.asarray(part, float)
            if len(part) < 2:
                if len(part) == 1:
                    seg.append(np.c_[part, part]); owner.append([k])
                continue
            seg.append(np.c_[part[:-1], part[1:]])
            owner.append(np.full(len(part) - 1, k))
    if not seg:
        return np.zeros((0, 4)), np.zeros(0, int)
    return np.concatenate(seg), np.concatenate(owner).astype(int)


def _point_seg_dist(px, py, s):
    ax, ay, bx, by = s[:, 0], s[:, 1], s[:, 2], s[:, 3]
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / np.where(L > 0, L, 1), 0, 1)
    return np.hypot(ax + t * dx - px, ay + t * dy - py)


def _seg_index_len(seg: np.ndarray) -> float:
    L = np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1])
    return float(max(1.0, np.median(L) * 4)) if len(L) else 1.0


def points_near_segments(px, py, seg: np.ndarray, distance: float) -> np.ndarray:
    """True for points within `distance` (inclusive) of any segment (rows ax, ay, bx, by)."""
    px, py = np.asarray(px, float), np.asarray(py, float)
    hit = np.zeros(len(px), bool)
    if not len(px) or not len(seg):
        return hit
    seg, _ = _split_long(seg, np.zeros(len(seg), int), _seg_index_len(seg))
    tree = cKDTree(np.c_[px, py])
    mid = (seg[:, :2] + seg[:, 2:]) / 2
    half = np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1]) / 2
    cand = tree.query_ball_point(mid, r=half + distance + 1e-9)
    si = np.repeat(np.arange(len(seg)), [len(c) for c in cand])
    if not len(si):
        return hit
    pi = np.concatenate([np.asarray(c, int) for c in cand])
    s = seg[si]
    d = _point_seg_dist(px[pi], py[pi], s)
    hit[np.unique(pi[d <= distance])] = True
    return hit


def points_near_lines(px, py, lines: list, distance: float) -> np.ndarray:
    """True for points within `distance` (inclusive) of any line feature."""
    seg, _ = _line_segments(lines)
    return points_near_segments(px, py, seg, distance)


def _nearest_segment(px, py, seg, owner):
    """Exact distance to, and owner of, the nearest segment for each point."""
    px, py = np.asarray(px, float), np.asarray(py, float)
    dist = np.full(len(px), np.inf)
    own = np.full(len(px), -1, dtype=np.int64)
    if not len(seg) or not len(px):
        return dist, own
    seg, owner = _split_long(seg, owner, _seg_index_len(seg))
    mid = (seg[:, :2] + seg[:, 2:]) / 2
    halfmax = float(np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1]).max() / 2)
    tree = cKDTree(mid)
    d0, _ = tree.query(np.c_[px, py])          # distance to a point on some segment: an upper bound
    cand = tree.query_ball_point(np.c_[px, py], r=d0 + halfmax + 1e-9)
    for j, c in enumerate(cand):
        c = np.asarray(c, int)
        d = _point_seg_dist(px[j], py[j], seg[c])
        k = int(np.argmin(d))
        dist[j], own[j] = d[k], owner[c[k]]
    return dist, own


def nearest_polygon(px, py, polys: list) -> tuple[np.ndarray, np.ndarray]:
    """Index of the polygon feature containing each point, else of the nearest one; and the distance (0 inside)."""
    idx = G.points_in_polygons(px, py, polys)
    dist = np.zeros(len(idx))
    out = np.flatnonzero(idx < 0)
    if len(out):
        seg, owner = G._segments(polys)
        d, o = _nearest_segment(np.asarray(px, float)[out], np.asarray(py, float)[out], seg, owner)
        idx[out], dist[out] = o, d
    return idx, dist


def distance_to_polygons_exact(px, py, polys: list) -> np.ndarray:
    """Distance from each point to the nearest polygon feature, no cap (0 inside, as shapely's distance)."""
    return nearest_polygon(px, py, polys)[1]


# ------------------------------------------------------------------------------------ polygon to polygon
def _feature_segments(feature) -> np.ndarray:
    return G._segments([feature])[0]


def _feature_vertices(feature) -> np.ndarray:
    return np.concatenate([r for part in feature for r in part]) if feature else np.zeros((0, 2))


def _segments_cross(s: np.ndarray, t: np.ndarray) -> bool:
    """Whether any segment of s intersects any segment of t (inclusive)."""
    if not len(s) or not len(t):
        return False
    a, b = s[:, None, :2], s[:, None, 2:]
    c, d = t[None, :, :2], t[None, :, 2:]

    def orient(p, q, r):
        return np.sign((q[..., 0] - p[..., 0]) * (r[..., 1] - p[..., 1]) - (q[..., 1] - p[..., 1]) * (r[..., 0] - p[..., 0]))
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    proper = (o1 != o2) & (o3 != o4) & ~((o1 == 0) & (o2 == 0))
    col = (o1 == 0) & (o2 == 0)                                   # collinear: do the extents overlap?
    ov = (np.maximum(a[..., 0], b[..., 0]) >= np.minimum(c[..., 0], d[..., 0])) & \
         (np.maximum(c[..., 0], d[..., 0]) >= np.minimum(a[..., 0], b[..., 0])) & \
         (np.maximum(a[..., 1], b[..., 1]) >= np.minimum(c[..., 1], d[..., 1])) & \
         (np.maximum(c[..., 1], d[..., 1]) >= np.minimum(a[..., 1], b[..., 1]))
    return bool(proper.any() or (col & ov).any())


def polygon_distance(fa, fb) -> float:
    """Distance between two polygon features (0 when they touch, overlap or one contains the other)."""
    va, vb = _feature_vertices(fa), _feature_vertices(fb)
    if not len(va) or not len(vb):
        return float("inf")
    if G.points_in_feature(va[:, 0], va[:, 1], fb).any() or G.points_in_feature(vb[:, 0], vb[:, 1], fa).any():
        return 0.0
    sa, sb = _feature_segments(fa), _feature_segments(fb)
    if _segments_cross(sa, sb):
        return 0.0
    d1 = min(_point_seg_dist(x, y, sb).min() for x, y in va)
    d2 = min(_point_seg_dist(x, y, sa).min() for x, y in vb)
    return float(min(d1, d2))


def components_within(polys: list, distance: float) -> list[list[int]]:
    """Groups of polygon features linked by chains of features at most `distance` apart (connected components)."""
    n = len(polys)
    if not n:
        return []
    boxes = np.array([[*_feature_vertices(f).min(0), *_feature_vertices(f).max(0)] for f in polys])
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    cx, cy = (boxes[:, 0] + boxes[:, 2]) / 2, (boxes[:, 1] + boxes[:, 3]) / 2
    hr = np.hypot(boxes[:, 2] - boxes[:, 0], boxes[:, 3] - boxes[:, 1]) / 2
    tree = cKDTree(np.c_[cx, cy])
    pairs = tree.query_pairs(r=2 * hr.max() + distance + 1e-9, output_type="ndarray")
    for i, j in pairs:
        if (boxes[i, 0] - distance > boxes[j, 2] or boxes[j, 0] - distance > boxes[i, 2]
                or boxes[i, 1] - distance > boxes[j, 3] or boxes[j, 1] - distance > boxes[i, 3]):
            continue
        ri, rj = find(i), find(j)
        if ri != rj and polygon_distance(polys[i], polys[j]) <= distance:
            parent[ri] = rj
    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def min_area_rectangle_sides(points: np.ndarray) -> tuple[float, float]:
    """(long side, short side) of the minimum-area rectangle enclosing the points (rotating calipers)."""
    pts = np.unique(np.asarray(points, float), axis=0)
    if len(pts) < 2:
        return 0.0, 0.0
    try:
        hull = pts[ConvexHull(pts).vertices]
    except Exception:                                   # collinear points: a segment
        d = pts - pts[0]
        L = float(np.hypot(d[:, 0], d[:, 1]).max())
        return L, 0.0
    e = np.roll(hull, -1, axis=0) - hull
    ang = np.arctan2(e[:, 1], e[:, 0])
    best = None
    for a in ang:
        c, s = np.cos(a), np.sin(a)
        u = hull[:, 0] * c + hull[:, 1] * s
        v = -hull[:, 0] * s + hull[:, 1] * c
        w, h = u.max() - u.min(), v.max() - v.min()
        if best is None or w * h < best[0]:
            best = (w * h, max(w, h), min(w, h))
    return float(best[1]), float(best[2])


# ------------------------------------------------------------------------------------------- intersection
def _oriented_rings(feature) -> list[np.ndarray]:
    """Closed rings, exteriors counter-clockwise and holes clockwise."""
    out = []
    for part in feature or []:
        for i, r in enumerate(part):
            r = _closed(np.asarray(r, float))
            if len(r) < 4:
                continue
            a = G._ring_area_signed(r[:-1])
            if (i == 0 and a < 0) or (i > 0 and a > 0):
                r = r[::-1]
            out.append(r)
    return out


def _boundary_pieces_inside(rings_a, rings_b, feature_b, keep_shared: bool, eps: float) -> float:
    """Sum of x dy - y dx over the pieces of A's boundary lying inside B (Green's theorem). Pieces on B's boundary
    count only when keep_shared and B's coincident edge runs the same way."""
    sb = np.concatenate([np.c_[r[:-1], r[1:]] for r in rings_b]) if rings_b else np.zeros((0, 4))
    vb = sb[:, :2]
    total = 0.0
    for r in rings_a:
        for (ax, ay), (bx, by) in zip(r[:-1], r[1:]):
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            if L2 == 0:
                continue
            ts = [0.0, 1.0]
            # crossings with B's segments
            ex, ey = sb[:, 2] - sb[:, 0], sb[:, 3] - sb[:, 1]
            den = dx * ey - dy * ex
            ok = np.abs(den) > 0
            qx, qy = sb[:, 0] - ax, sb[:, 1] - ay
            with np.errstate(divide="ignore", invalid="ignore"):
                t = (qx * ey - qy * ex) / den
                u = (qx * dy - qy * dx) / den
            m = ok & (t > 0) & (t < 1) & (u >= 0) & (u <= 1)
            ts += list(t[m])
            # B's vertices lying on this edge (collinear overlaps)
            tv = ((vb[:, 0] - ax) * dx + (vb[:, 1] - ay) * dy) / L2
            off = np.abs((vb[:, 0] - ax) * dy - (vb[:, 1] - ay) * dx) / np.sqrt(L2)
            ts += list(tv[(off < eps) & (tv > 0) & (tv < 1)])
            ts = np.unique(ts)
            p = np.c_[ax + ts * dx, ay + ts * dy]
            p0, p1 = p[:-1], p[1:]
            mid = (p0 + p1) / 2
            inside = G.points_in_feature(mid[:, 0], mid[:, 1], feature_b) if feature_b else np.zeros(len(mid), bool)
            if len(sb):
                for k, (mx, my) in enumerate(mid):
                    d = _point_seg_dist(mx, my, sb)
                    j = int(np.argmin(d))
                    if d[j] < eps:                                  # on B's boundary
                        same = (sb[j, 2] - sb[j, 0]) * dx + (sb[j, 3] - sb[j, 1]) * dy > 0
                        inside[k] = keep_shared and same
            q0, q1 = p0[inside], p1[inside]
            total += float((q0[:, 0] * q1[:, 1] - q1[:, 0] * q0[:, 1]).sum())
    return total


def intersection_area(fa, fb, eps: float = 1e-7) -> float:
    """Area of the intersection of two polygon features (CRS units squared). Parts of one feature should not overlap
    each other (as in valid polygons)."""
    ra, rb = _oriented_rings(fa), _oriented_rings(fb)
    if not ra or not rb:
        return 0.0
    va, vb = np.concatenate(ra), np.concatenate(rb)
    if va[:, 0].max() < vb[:, 0].min() or vb[:, 0].max() < va[:, 0].min() or \
            va[:, 1].max() < vb[:, 1].min() or vb[:, 1].max() < va[:, 1].min():
        return 0.0
    s = _boundary_pieces_inside(ra, rb, fb, True, eps) + _boundary_pieces_inside(rb, ra, fa, False, eps)
    return max(0.0, 0.5 * s)


# ------------------------------------------------------------------------------------------ areas, transforms
def _ring_area_geos(r: np.ndarray) -> float:
    """Signed ring area by GEOS's formula (shoelace relative to the first x; stable for large coordinates)."""
    r = _closed(np.asarray(r, float))
    if len(r) < 3:
        return 0.0
    x = r[1:-1, 0] - r[0, 0]
    return float((x * (r[:-2, 1] - r[2:, 1])).sum() / 2.0)


def areas(polys: list) -> np.ndarray:
    """Planar area of each polygon feature as GEOS computes it: exteriors minus holes, parts summed."""
    out = np.zeros(len(polys))
    for k, f in enumerate(polys):
        a = 0.0
        for part in f or []:
            if not len(part):
                continue
            a += abs(_ring_area_geos(part[0])) - sum(abs(_ring_area_geos(h)) for h in part[1:])
        out[k] = a
    return out


def polygons_to_crs(polys: list, src, dst) -> list:
    """Reproject polygon features in one batched transform (same result as geom.Layer.to_crs, faster for many
    small features)."""
    rings = [r for f in polys for part in f for r in part]
    if not rings:
        return [[[] for _ in f] for f in polys] if polys else []
    n = np.array([len(r) for r in rings])
    xy = np.concatenate(rings)
    x, y = G.transform(xy[:, 0], xy[:, 1], src, dst)
    pts = np.c_[x, y]
    cut = np.split(pts, np.cumsum(n)[:-1])
    out, i = [], 0
    for f in polys:
        nf = []
        for part in f:
            nf.append(cut[i:i + len(part)])
            i += len(part)
        out.append(nf)
    return out
