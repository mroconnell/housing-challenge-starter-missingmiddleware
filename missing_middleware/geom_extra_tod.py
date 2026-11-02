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
- min_rotated_rectangle / min_rect_widths: GEOS minimum rotated rectangle and its shorter side (lot width).
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


# ---------------------------------------------------------------------------------------------- buffered area of interest
# (scripts/fetch_tod_cases.py: which download tiles meet "these features buffered by r metres"; was a GEOS buffer union)
class BufferedAoi:
    """Union of GEOS buffers (quad_segs 16) of point sets and polygon features (projected, metres), held as
    (geometry, r) pairs rather than as one buffer polygon. bounds and outline_points reproduce the GEOS buffer's
    vertices (straight edges offset, convex corners filleted in round(angle / step) chords, after GEOS's buffer-input
    simplification of each ring); intersects_box tests a box against the same chorded shape. Checked against shapely
    on the Charlotte, Raleigh, Phoenix, Seattle and Los Angeles download areas (tests/test_geom_extra_tod.py)."""

    QUAD_SEGS = 16

    def __init__(self, items: list[tuple[object, float]] | None = None):
        self.points: list[tuple[np.ndarray, float]] = []      # (n, 2) array, r
        self.polys: list[tuple[list, float]] = []             # polygon feature, r
        for g, r in items or []:
            self.add(g, r)

    def add(self, geom, r: float) -> "BufferedAoi":
        """geom: an (n, 2) point array, an (x, y) pair of arrays, or a list of polygon features."""
        if isinstance(geom, tuple) and len(geom) == 2:
            geom = np.c_[np.asarray(geom[0], float), np.asarray(geom[1], float)]
        if isinstance(geom, np.ndarray):
            pts = geom[np.isfinite(geom).all(1)]
            if len(pts):
                self.points.append((pts, float(r)))
        else:
            self.polys += [(f, float(r)) for f in geom if f]
        return self

    @staticmethod
    def _circle(r: float) -> np.ndarray:
        q = np.pi / 2 / BufferedAoi.QUAD_SEGS
        t = -np.arange(4 * BufferedAoi.QUAD_SEGS) * q              # GEOS: from angle 0, clockwise
        return np.c_[r * np.cos(t), r * np.sin(t)]

    @staticmethod
    def _rings(f, r: float, shells_only: bool = False) -> list[np.ndarray]:
        """The feature's rings as GEOS offsets them: simplified, open, oriented with the buffer side on the right
        (shells counter-clockwise, holes clockwise)."""
        from missing_middleware.geom_extra_station import buffer_input_polys
        out = []
        for part in buffer_input_polys([f], r)[0]:
            for h, ring in enumerate(part):
                if h and shells_only:
                    break
                ring = np.asarray(ring, float)
                if len(ring) < 3:
                    continue
                ring = _closed(ring)[:-1]
                cw = _ring_area_geos(_closed(ring)) > 0              # GEOS sign: positive for clockwise
                if cw == (h == 0):
                    ring = ring[::-1]
                out.append(ring)
        return out

    @staticmethod
    def _fillets(ring: np.ndarray, r: float):
        """(vertex, fillet points) for each convex corner of an oriented ring (fillet ends included)."""
        q = np.pi / 2 / BufferedAoi.QUAD_SEGS
        prev, nxt = np.roll(ring, 1, axis=0), np.roll(ring, -1, axis=0)
        th_in = np.arctan2(ring[:, 1] - prev[:, 1], ring[:, 0] - prev[:, 0])
        th_out = np.arctan2(nxt[:, 1] - ring[:, 1], nxt[:, 0] - ring[:, 0])
        turn = (th_out - th_in + np.pi) % (2 * np.pi) - np.pi
        for v, a0, tot in zip(ring, th_in - np.pi / 2, turn):
            if tot <= 0:
                continue
            n = max(int(tot / q + 0.5), 1)
            a = a0 + np.arange(n + 1) * (tot / n)
            yield v, np.c_[v[0] + r * np.cos(a), v[1] + r * np.sin(a)]

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """Bounds of the buffered union, from the GEOS buffer's own vertices (outline_points)."""
        o = self.outline_points()
        if not len(o):
            return (np.nan,) * 4
        return float(o[:, 0].min()), float(o[:, 1].min()), float(o[:, 0].max()), float(o[:, 1].max())

    def outline_points(self) -> np.ndarray:
        """The outer vertices of the GEOS buffer: for points, the 64 circle vertices; for polygons, each convex shell
        corner's fillet. Every extreme vertex of the buffer is among them, so their extent (also after reprojection,
        up to the curvature of the reprojected edges) is the buffer's."""
        out = []
        for p, r in self.points:
            c = self._circle(r)
            out.append((p[:, None, :] + c[None, :, :]).reshape(-1, 2))
        for f, r in self.polys:
            for ring in self._rings(f, r, shells_only=True):
                out += [pts for _, pts in self._fillets(ring, r)]
        return np.concatenate(out) if out else np.zeros((0, 2))

    def intersects_box(self, x0: float, y0: float, x1: float, y1: float) -> bool:
        """Whether the box (x0 <= x <= x1, y0 <= y <= y1) meets the buffered union (as shapely's box.intersects)."""
        box = [[np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], float)]]
        q = np.pi / 2 / self.QUAD_SEGS
        for p, r in self.points:
            dx = np.maximum(np.maximum(x0 - p[:, 0], p[:, 0] - x1), 0.0)
            dy = np.maximum(np.maximum(y0 - p[:, 1], p[:, 1] - y1), 0.0)
            d = np.hypot(dx, dy)
            if (d <= r * np.cos(q / 2) - 1e-9).any():
                return True
            c = self._circle(r)
            for k in np.flatnonzero(d <= r):
                if polygon_distance(box, [[_closed(p[k] + c)]]) == 0:
                    return True
        for f, r in self.polys:
            v = _feature_vertices(f)
            if v[:, 0].min() - r > x1 or v[:, 0].max() + r < x0 or v[:, 1].min() - r > y1 or v[:, 1].max() + r < y0:
                continue
            d = polygon_distance(box, f)
            if d > r:
                continue
            if d <= r * np.cos(0.75 * q) - 1e-9:                     # inside every chord
                return True
            for ring in self._rings(f, r):                         # the chorded shape, piece by piece
                nxt = np.roll(ring, -1, axis=0)
                for a, b in zip(ring, nxt):
                    e = b - a
                    L = np.hypot(*e)
                    if L == 0:
                        continue
                    nrm = np.array([e[1], -e[0]]) / L * r              # right side: the buffer side
                    piece = [[np.array([a, b, b + nrm, a + nrm, a])]]
                    if polygon_distance(box, piece) == 0:
                        return True
                for vtx, pts in self._fillets(ring, r):
                    if polygon_distance(box, [[_closed(np.vstack([vtx, pts]))]]) == 0:
                        return True
        return False


# ------------------------------------------------------------------------------------------ regions (census scripts)
# The census-block scripts (scripts/run_tod_census_*.py, run_tod_conversion.py) built areas with shapely as
# `zone.buffer(d).difference(other).difference(exclude)` and then asked which block points lie inside and how much
# of each block's land lies inside. A Region answers the same two questions without constructing the shape: it says
# whether points are inside, and lists segments that cover its boundary; overlap areas are then integrated over the
# boundary pieces of block-and-region (Green's theorem), a piece counting when the set lies on exactly one side of it.
import math  # noqa: E402


def feature_from_geo_interface(g) -> list:
    """A polygon feature (list of parts, each a list of rings) from a polygon feature already in that model, None,
    or any object with __geo_interface__ (Polygon, MultiPolygon or a GeometryCollection's polygons) - e.g. shapes
    pickled by earlier runs. Empty for anything without area."""
    if g is None:
        return []
    if isinstance(g, list):
        return g
    gi = getattr(g, "__geo_interface__", g)
    t, out = gi.get("type"), []
    if t == "Polygon":
        out = [[np.asarray(r, float)[:, :2] for r in gi["coordinates"]]] if gi["coordinates"] else []
    elif t == "MultiPolygon":
        out = [[np.asarray(r, float)[:, :2] for r in p] for p in gi["coordinates"] if p]
    elif t == "GeometryCollection":
        out = [p for sub in gi.get("geometries", []) for p in feature_from_geo_interface(sub)]
    return [p for p in out if p and len(p[0])]


class Region:
    """A planar point set. contains(px, py) -> bool array; edges() -> (m, 4) segments (x0, y0, x1, y1) that cover its
    boundary (extra segments are harmless). Combine with |, & and - (union, intersection, difference)."""

    def contains(self, px, py) -> np.ndarray:
        raise NotImplementedError

    def _edges(self) -> np.ndarray:
        raise NotImplementedError

    def edges(self) -> np.ndarray:
        if getattr(self, "_edge_cache", None) is None:
            self._edge_cache = self._edges()
        return self._edge_cache

    def __or__(self, other):
        return _Combined("or", self, other)

    def __and__(self, other):
        return _Combined("and", self, other)

    def __sub__(self, other):
        return _Combined("sub", self, other)


class Polygons(Region):
    """The union of polygon features. A point is in a feature as GEOS 'within' sees it (even-odd over the feature's
    rings, as geom.points_in_feature), or with union=True in any of its parts. Points on a boundary are not decided."""

    def __init__(self, polys, union: bool = False):
        self.polys = [f for f in polys if f]
        self.union = union

    def contains(self, px, py) -> np.ndarray:
        from missing_middleware.geom_extra_station import first_within
        px, py = np.asarray(px, float), np.asarray(py, float)
        if not self.polys or not len(px):
            return np.zeros(len(px), bool)
        return first_within(px, py, self.polys, self.union) >= 0

    def _edges(self) -> np.ndarray:
        from missing_middleware.geom_extra_station import _segments_of
        return _segments_of(self.polys)[0]


class Buffer(Region):
    """`union_all(polys).buffer(r)` as GEOS draws it: the polygons, a band of half-width r along every edge, and at each
    outside corner a fan of chords, quad_segs per quarter turn (round(angle / step) chords from one edge normal to the
    other; the corner model of geom_extra_station.within_buffer_geos). simplify: GEOS's smoothing of shallow bends
    before buffering (BufferInputLineSimplifier), applied ring by ring. Membership is decided on exactly this union of
    polygons, so its boundary lies on the listed edges (offset edges, end caps and chords)."""

    def __init__(self, polys, r: float, quad_segs: int = 16, simplify: bool = True):
        from missing_middleware.geom_extra_station import _segments_of, buffer_input_polys
        self.polys = [f for f in polys if f]
        self.r, self.quad_segs = float(r), quad_segs
        self.input = buffer_input_polys(self.polys, self.r) if simplify else self.polys
        seg = _segments_of(self.input)[0] if self.polys else np.zeros((0, 4))
        d = seg[:, 2:] - seg[:, :2]
        L = np.hypot(d[:, 0], d[:, 1])
        self.seg = seg[L > 0]
        self.fans = self._fans()

    def _fans(self) -> np.ndarray:
        """One row per corner arc: vertex x, y, start angle a0, sweep, chord count."""
        seg = self.seg
        if not len(seg):
            return np.zeros((0, 5))
        q = math.pi / 2 / self.quad_segs
        a, b = seg[:, :2], seg[:, 2:]
        ends, other = np.r_[a, b], np.r_[b, a]
        v, inv = np.unique(ends, axis=0, return_inverse=True)
        inv = np.asarray(inv).ravel()
        th = np.arctan2(other[:, 1] - ends[:, 1], other[:, 0] - ends[:, 0])
        order = np.lexsort((th, inv))
        inv_s, th_s = inv[order], th[order]
        starts = np.r_[0, np.flatnonzero(np.diff(inv_s)) + 1]
        stops = np.r_[starts[1:], len(inv_s)]
        rows = []
        for s0, s1 in zip(starts, stops):
            t = np.unique(th_s[s0:s1])
            if len(t) < 2:
                continue
            gaps = np.r_[t[1:] - t[:-1], t[0] + 2 * math.pi - t[-1]]
            for i in np.flatnonzero(gaps > math.pi):
                a0 = t[i] + math.pi / 2
                total = gaps[i] - math.pi
                vx, vy = v[inv_s[s0]]
                rows.append((vx, vy, a0, total, max(int(total / q + 0.5), 1)))
        return np.array(rows, float).reshape(-1, 5)

    def contains(self, px, py) -> np.ndarray:
        from missing_middleware.geom_extra_station import nearest_polygon
        px, py = np.asarray(px, float), np.asarray(py, float)
        out = np.zeros(len(px), bool)
        if not self.polys or not len(px) or not len(self.seg):
            return out
        r = self.r
        q = math.pi / 2 / self.quad_segs
        _, dist = nearest_polygon(px, py, self.input, r, union=True)
        # within r * cos(0.75 q) of the polygons: inside every band or fan (a fan's chords are no wider than 1.5 q)
        out[dist <= r * math.cos(0.75 * q) - 1e-9] = True
        todo = np.flatnonzero((dist <= r) & ~out)
        # bands along edges (edges cut into short pieces for the index): projection inside, distance at most r
        if len(todo):
            if getattr(self, "_pieces", None) is None:
                seg = self.seg
                L = np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1])
                k = np.maximum(1, np.ceil(L / 25.0).astype(int))
                rep = np.repeat(np.arange(len(seg)), k)
                t0 = np.concatenate([np.arange(m) / m for m in k])
                t1 = np.concatenate([np.arange(1, m + 1) / m for m in k])
                s = seg[rep]
                pc = np.c_[s[:, 0] + t0 * (s[:, 2] - s[:, 0]), s[:, 1] + t0 * (s[:, 3] - s[:, 1]),
                           s[:, 0] + t1 * (s[:, 2] - s[:, 0]), s[:, 1] + t1 * (s[:, 3] - s[:, 1])]
                self._pieces = (rep, cKDTree((pc[:, :2] + pc[:, 2:]) / 2),
                                float(np.hypot(pc[:, 2] - pc[:, 0], pc[:, 3] - pc[:, 1]).max()) / 2)
            rep, tree, half = self._pieces
            for c0 in range(0, len(todo), 5000):
                tj = todo[c0:c0 + 5000]
                cand = tree.query_ball_point(np.c_[px[tj], py[tj]], r + half + 1e-9)
                lens = np.fromiter((len(c) for c in cand), np.int64, len(cand))
                if not lens.sum():
                    continue
                ci = np.fromiter((i for c in cand for i in c), np.int64, int(lens.sum()))
                who = np.repeat(np.arange(len(tj)), lens)
                sg = self.seg[rep[ci]]                   # tested against the whole edge, not the index piece
                x, y = px[tj][who], py[tj][who]
                dx, dy = sg[:, 2] - sg[:, 0], sg[:, 3] - sg[:, 1]
                LL = dx * dx + dy * dy
                t = ((x - sg[:, 0]) * dx + (y - sg[:, 1]) * dy) / LL
                dd = np.abs((x - sg[:, 0]) * dy - (y - sg[:, 1]) * dx) / np.sqrt(LL)
                hit = (t >= 0) & (t <= 1) & (dd <= r)
                out[tj[np.unique(who[hit])]] = True
            todo = todo[~out[todo]]
        # corner fans: the chord triangle of the sector the point's direction falls in
        if len(todo) and len(self.fans):
            F = self.fans
            if getattr(self, "_fan_tree", None) is None:
                self._fan_tree = cKDTree(F[:, :2])
            cand = self._fan_tree.query_ball_point(np.c_[px[todo], py[todo]], r + 1e-9)
            lens = np.fromiter((len(c) for c in cand), np.int64, len(cand))
            if lens.sum():
                ci = np.fromiter((i for c in cand for i in c), np.int64, int(lens.sum()))
                who = np.repeat(np.arange(len(todo)), lens)
                f = F[ci]
                x, y = px[todo][who] - f[:, 0], py[todo][who] - f[:, 1]
                rel = (np.arctan2(y, x) - f[:, 2]) % (2 * math.pi)
                inc = f[:, 3] / f[:, 4]
                k = np.minimum(np.floor(rel / inc), f[:, 4] - 1)
                m = f[:, 2] + (k + 0.5) * inc
                hit = (rel <= f[:, 3]) & (x * np.cos(m) + y * np.sin(m) <= r * np.cos(inc / 2))
                out[todo[np.unique(who[hit])]] = True
        return out

    def _edges(self) -> np.ndarray:
        """Offset edges, end caps and corner chords, cut into pieces at most 25 m long; pieces that lie wholly where
        every point is inside (within r cos(0.75 q) of the polygons) are left out."""
        from missing_middleware.geom_extra_station import nearest_polygon
        seg = self.seg
        if not len(seg):
            return np.zeros((0, 4))
        d = seg[:, 2:] - seg[:, :2]
        L = np.hypot(d[:, 0], d[:, 1])
        a, b = seg[:, :2], seg[:, 2:]
        n = np.c_[-d[:, 1], d[:, 0]] / L[:, None] * self.r
        out = [np.c_[a + n, b + n], np.c_[a - n, b - n],                     # offset edges on both sides
               np.c_[a, a + n], np.c_[a, a - n], np.c_[b, b + n], np.c_[b, b - n]]   # end caps
        for vx, vy, a0, total, k in self.fans:                                 # corner chords
            ang = a0 + np.arange(int(k) + 1) * (total / k)
            cx, cy = vx + self.r * np.cos(ang), vy + self.r * np.sin(ang)
            out.append(np.c_[cx[:-1], cy[:-1], cx[1:], cy[1:]])
        E = _cut(np.concatenate(out), 25.0)
        half = np.hypot(E[:, 2] - E[:, 0], E[:, 3] - E[:, 1]) / 2
        mid = (E[:, :2] + E[:, 2:]) / 2
        _, dist = nearest_polygon(mid[:, 0], mid[:, 1], self.input, self.r, union=True)
        q = math.pi / 2 / self.quad_segs
        return E[dist + half >= self.r * math.cos(0.75 * q) - 1e-6]


def _cut(E: np.ndarray, max_len: float) -> np.ndarray:
    """Segments cut into equal pieces at most max_len long."""
    if not len(E):
        return E
    L = np.hypot(E[:, 2] - E[:, 0], E[:, 3] - E[:, 1])
    k = np.maximum(1, np.ceil(L / max_len).astype(int))
    rep = np.repeat(np.arange(len(E)), k)
    t0 = np.concatenate([np.arange(m) / m for m in k])
    t1 = np.concatenate([np.arange(1, m + 1) / m for m in k])
    s = E[rep]
    return np.c_[s[:, 0] + t0 * (s[:, 2] - s[:, 0]), s[:, 1] + t0 * (s[:, 3] - s[:, 1]),
                 s[:, 0] + t1 * (s[:, 2] - s[:, 0]), s[:, 1] + t1 * (s[:, 3] - s[:, 1])]


class _Combined(Region):
    def __init__(self, op: str, a: Region, b: Region):
        self.op, self.a, self.b = op, a, b

    def contains(self, px, py) -> np.ndarray:
        px, py = np.asarray(px, float), np.asarray(py, float)
        ia = self.a.contains(px, py)
        if self.op == "or":
            rest = ~ia
            out = ia.copy()
            if rest.any():
                out[rest] = self.b.contains(px[rest], py[rest])
            return out
        out = ia.copy()
        if ia.any():
            ib = self.b.contains(px[ia], py[ia])
            out[ia] = ib if self.op == "and" else ~ib
        return out

    def _edges(self) -> np.ndarray:
        return np.concatenate([self.a.edges(), self.b.edges()])


def points_in_region(px, py, region) -> np.ndarray:
    """Boolean mask of points inside a Region (None or an empty region: none)."""
    if region is None:
        return np.zeros(len(px), bool)
    return region.contains(px, py)


def _clip_segments(S: np.ndarray, box) -> np.ndarray:
    """Segments clipped to an axis-aligned box (Liang-Barsky); segments missing the box are dropped."""
    x0, y0, x1, y1 = box
    ax, ay = S[:, 0], S[:, 1]
    dx, dy = S[:, 2] - ax, S[:, 3] - ay
    t0, t1 = np.zeros(len(S)), np.ones(len(S))
    ok = np.ones(len(S), bool)
    for p, q in ((-dx, ax - x0), (dx, x1 - ax), (-dy, ay - y0), (dy, y1 - ay)):
        par = p == 0
        ok &= ~(par & (q < 0))
        with np.errstate(divide="ignore", invalid="ignore"):
            r = q / p
        t0 = np.where(~par & (p < 0), np.maximum(t0, r), t0)
        t1 = np.where(~par & (p > 0), np.minimum(t1, r), t1)
    ok &= t0 <= t1
    S, t0, t1, dx, dy = S[ok], t0[ok], t1[ok], dx[ok], dy[ok]
    return np.c_[S[:, 0] + t0 * dx, S[:, 1] + t0 * dy, S[:, 0] + t1 * dx, S[:, 1] + t1 * dy]


def _split_at_crossings(S: np.ndarray, tol: float, chunk: int = 400) -> tuple[np.ndarray, np.ndarray]:
    """Pieces of the segments between every crossing with another segment and every other segment's endpoint lying on
    them (within tol): (start points, end points)."""
    A = S[:, :2]
    D = S[:, 2:] - A
    L2 = (D * D).sum(1)
    keep = L2 > 0
    A, D, L2 = A[keep], D[keep], L2[keep]
    n = len(A)
    E = A + D
    P0, P1 = [], []
    for c0 in range(0, n, chunk):
        i = slice(c0, min(n, c0 + chunk))
        Ai, Di, L2i = A[i], D[i], L2[i]
        den = Di[:, None, 0] * D[None, :, 1] - Di[:, None, 1] * D[None, :, 0]
        qx, qy = A[None, :, 0] - Ai[:, None, 0], A[None, :, 1] - Ai[:, None, 1]
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (qx * D[None, :, 1] - qy * D[None, :, 0]) / den
            u = (qx * Di[:, None, 1] - qy * Di[:, None, 0]) / den
        hit = (den != 0) & (t > 0) & (t < 1) & (u >= 0) & (u <= 1)
        ts = [t[hit], ]
        rows = [np.nonzero(hit)[0]]
        Ln = np.sqrt(L2i)[:, None]
        for P in (A, E):
            ex, ey = P[None, :, 0] - Ai[:, None, 0], P[None, :, 1] - Ai[:, None, 1]
            tv = (ex * Di[:, None, 0] + ey * Di[:, None, 1]) / L2i[:, None]
            off = np.abs(ex * Di[:, None, 1] - ey * Di[:, None, 0]) / Ln
            m = (off < tol) & (tv > 0) & (tv < 1)
            ts.append(tv[m]); rows.append(np.nonzero(m)[0])
        tt, rr = np.concatenate(ts), np.concatenate(rows)
        cnt = np.bincount(rr, minlength=len(Ai))
        cuts = np.split(tt[np.argsort(rr, kind="stable")], np.cumsum(cnt)[:-1])
        for k, c in enumerate(cuts):
            tk = np.unique(np.r_[0.0, c, 1.0])
            p = Ai[k] + tk[:, None] * Di[k]
            P0.append(p[:-1]); P1.append(p[1:])
    if not P0:
        return np.zeros((0, 2)), np.zeros((0, 2))
    return np.concatenate(P0), np.concatenate(P1)


def _slab_gaps(P0: np.ndarray, P1: np.ndarray):
    """Vertical-slab decomposition of non-crossing pieces: the plane is cut at every piece end's x; within a slab the
    pieces spanning it are ordered by height, and each gap between two consecutive pieces is a trapezoid. Returns the
    trapezoids' test points (slab middle, half-way between the two pieces) and areas. Coincident or nearly coincident
    pieces only make gaps of (nearly) no area, so no piece needs to be deduplicated."""
    xs = np.unique(np.r_[P0[:, 0], P1[:, 0]])
    lo, hi = np.minimum(P0[:, 0], P1[:, 0]), np.maximum(P0[:, 0], P1[:, 0])
    i0, i1 = np.searchsorted(xs, lo), np.searchsorted(xs, hi)
    cnt = np.where(hi > lo, i1 - i0, 0)
    if not cnt.sum():
        return np.zeros((0, 2)), np.zeros(0)
    rep = np.repeat(np.arange(len(P0)), cnt)
    slab = np.repeat(i0, cnt) + (np.arange(int(cnt.sum())) - np.repeat(np.cumsum(cnt) - cnt, cnt))
    xa, xb = xs[slab], xs[slab + 1]
    p, q = P0[rep], P1[rep]
    dx = q[:, 0] - p[:, 0]
    ya = p[:, 1] + (xa - p[:, 0]) / dx * (q[:, 1] - p[:, 1])
    yb = p[:, 1] + (xb - p[:, 0]) / dx * (q[:, 1] - p[:, 1])
    ym = (ya + yb) / 2
    o = np.lexsort((ym, slab))
    same = slab[o][1:] == slab[o][:-1]
    l, u = o[:-1][same], o[1:][same]
    area = ((ya[u] - ya[l]) + (yb[u] - yb[l])) / 2 * (xb[l] - xa[l])
    pts = np.c_[(xa[l] + xb[l]) / 2, (ym[l] + ym[u]) / 2]
    return pts, np.maximum(area, 0.0)


def overlap_areas(polys: list, region: Region, max_piece: float = 50.0) -> np.ndarray:
    """Area of each polygon feature lying inside the region: `polygon.intersection(shape).area` for the shape the
    region stands for (0 for features that miss it). Projected units. Each feature's edges and the region's boundary
    segments near it are cut at their crossings; the strips between them (vertical-slab trapezoids) are tested at
    one point each, so the error is at most the area of strips thinner than rounding (the sliver between two
    edges that nearly coincide)."""
    from missing_middleware.geom_extra_station import _segments_of, feature_bounds
    out = np.zeros(len(polys))
    if not len(polys):
        return out
    fb = feature_bounds(polys)
    live = np.flatnonzero(np.isfinite(fb[:, 0]))
    if not len(live):
        return out
    E = region.edges()
    if len(E):
        lo, hi = np.nanmin(fb[live, :2], axis=0), np.nanmax(fb[live, 2:], axis=0)
        eb = np.c_[np.minimum(E[:, 0], E[:, 2]), np.minimum(E[:, 1], E[:, 3]), np.maximum(E[:, 0], E[:, 2]), np.maximum(E[:, 1], E[:, 3])]
        E = E[(eb[:, 2] >= lo[0]) & (eb[:, 0] <= hi[0]) & (eb[:, 3] >= lo[1]) & (eb[:, 1] <= hi[1])]
    if len(E):
        E = _cut(E, max_piece)
        half = float(np.hypot(E[:, 2] - E[:, 0], E[:, 3] - E[:, 1]).max()) / 2
        tree = cKDTree((E[:, :2] + E[:, 2:]) / 2)
    whole, centres, jobs = [], [], []
    for k in live:
        f = polys[k]
        x0, y0, x1, y1 = fb[k]
        local = np.zeros((0, 4))
        if len(E):
            cand = tree.query_ball_point([(x0 + x1) / 2, (y0 + y1) / 2], math.hypot(x1 - x0, y1 - y0) / 2 + half + 1e-9)
            if cand:
                pad = 1e-9 * max(1.0, abs(x0), abs(y0), abs(x1), abs(y1))
                local = _clip_segments(E[np.asarray(cand)], (x0 - pad, y0 - pad, x1 + pad, y1 + pad))
        if not len(local):
            whole.append(k)
            centres.append(((x0 + x1) / 2, (y0 + y1) / 2))
            continue
        o = np.array([x0, y0])
        S = np.r_[_segments_of([f])[0], local] - np.r_[o, o]
        P0, P1 = _split_at_crossings(S, 1e-9)
        pts, ar = _slab_gaps(P0, P1)
        jobs.append((k, pts + o, ar))
    if whole:
        c = np.array(centres)
        inside = region.contains(c[:, 0], c[:, 1])
        w = np.asarray(whole)[inside]
        out[w] = areas([polys[i] for i in w])
    if jobs:
        allp = np.concatenate([j[1] for j in jobs])
        rin = region.contains(allp[:, 0], allp[:, 1])
        pos = 0
        for k, pts, ar in jobs:
            n = len(pts)
            inside = rin[pos:pos + n] & G.points_in_feature(pts[:, 0], pts[:, 1], polys[k]) if n else np.zeros(0, bool)
            pos += n
            out[k] = float(ar[inside].sum())
    return out


# ------------------------------------------------------------------------------- GEOS minimum rotated rectangle
# Lot width in the lot model (scripts/run_tod_lot_model.py, run_tod_lot_model_wisconsin.py) was the shorter side of
# shapely's minimum_rotated_rectangle, i.e. GEOS (>= 3.12) MinimumAreaRectangle on the GEOS convex hull. Reproduced
# step by step (rotating calipers on the clockwise hull from its lowest point; rectangle corners from line
# intersections) so the same rectangle is chosen even among near-ties. Checked against shapely 2.2 / GEOS 3.14 on
# 120,000 St Paul, Charlotte and Chicago lots: 119,995 widths bit-identical, the other 5 within 3e-4 m.
def _rect_hull_cw(pts: np.ndarray):
    pts = np.unique(np.asarray(pts, float)[:, :2], axis=0)
    if len(pts) < 3:
        return None
    try:
        h = pts[ConvexHull(pts).vertices][::-1]           # scipy: counter-clockwise; GEOS: clockwise
    except Exception:                                      # collinear: GEOS returns a line (no rectangle)
        return None
    k = min(range(len(h)), key=lambda i: (h[i, 1], h[i, 0]))
    h = np.roll(h, -k, axis=0)
    return [tuple(map(float, p)) for p in np.vstack([h, h[:1]])]


def _rect_perp(p, a, b) -> float:
    if a[0] == b[0] and a[1] == b[1]:
        return float(np.hypot(a[0] - p[0], a[1] - p[1]))
    len2 = (b[0] - a[0]) * (b[0] - a[0]) + (b[1] - a[1]) * (b[1] - a[1])
    s = ((a[1] - p[1]) * (b[0] - a[0]) - (a[0] - p[0]) * (b[1] - a[1])) / len2
    return abs(s) * float(np.sqrt(len2))


def _rect_orient(a, b, p) -> int:
    from fractions import Fraction as F
    d = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    if abs(d) > 1e-9 * (abs(b[0] - a[0]) + abs(b[1] - a[1])) * (abs(p[0] - a[0]) + abs(p[1] - a[1])) + 1e-300:
        return 1 if d > 0 else -1
    e = (F(b[0]) - F(a[0])) * (F(p[1]) - F(a[1])) - (F(b[1]) - F(a[1])) * (F(p[0]) - F(a[0]))
    return (e > 0) - (e < 0)


def _rect_odist(a, b, p, orient: int) -> float:
    d = _rect_perp(p, a, b)
    if orient and not (a[0] == b[0] and a[1] == b[1]) and _rect_orient(a, b, p) < 0:
        return -d
    return d


def _rect_furthest(ring, a, b, start: int, orient: int) -> int:
    n = len(ring)
    mx = _rect_odist(a, b, ring[start], orient)
    nd, mi, ni = mx, start, start
    while (nd >= mx) if orient >= 0 else (nd <= mx):
        mx, mi = nd, ni
        ni = mi + 1 if mi + 1 < n - 1 else 0
        if ni == start:
            break
        nd = _rect_odist(a, b, ring[ni], orient)
    return mi


def _rect_line(a: float, b: float, c: float):
    if abs(b) > abs(a):
        return (0.0, c / b), (1.0, c / b - a / b)
    return (c / a, 0.0), (c / a - b / a, 1.0)


def _rect_intersection(p1, p2, q1, q2):
    """Intersection of the lines through p1-p2 and q1-q2, computed exactly and rounded once (GEOS uses double-double
    arithmetic here; exact rounding reproduces its corners bit for bit in the checks)."""
    from fractions import Fraction as F
    p1, p2, q1, q2 = [(F(a), F(b)) for a, b in (p1, p2, q1, q2)]
    px, py, pw = p1[1] - p2[1], p2[0] - p1[0], p1[0] * p2[1] - p2[0] * p1[1]
    qx, qy, qw = q1[1] - q2[1], q2[0] - q1[0], q1[0] * q2[1] - q2[0] * q1[1]
    x, y, w = py * qw - qy * pw, qx * pw - px * qw, px * qy - qx * py
    return float(x / w), float(y / w)


def min_rotated_rectangle(points: np.ndarray):
    """Corners (4, 2) of GEOS's minimum rotated (minimum-area) rectangle of the points; None where GEOS returns a
    point or line (fewer than three non-collinear points)."""
    ring = _rect_hull_cw(points)
    if ring is None or len(ring) < 4:
        return None
    best, sel = np.inf, None
    diam, left, right = 1, 1, -1
    for i in range(len(ring) - 1):
        b0, b1 = ring[i], ring[i + 1]
        diam = _rect_furthest(ring, b0, b1, diam, 0)
        dp = ring[diam]
        if (dp[0] == b0[0] and dp[1] == b0[1]) or (dp[0] == b1[0] and dp[1] == b1[1]):
            db = dp
        else:
            dx, dy = b1[0] - b0[0], b1[1] - b0[1]
            r = ((dp[0] - b0[0]) * dx + (dp[1] - b0[1]) * dy) / (dx * dx + dy * dy)
            db = (b0[0] + r * dx, b0[1] + r * dy)
        left = _rect_furthest(ring, db, dp, left, 1)
        if i == 0:
            right = diam
        right = _rect_furthest(ring, db, dp, right, -1)
        area = float(np.sqrt((db[0] - dp[0]) ** 2 + (db[1] - dp[1]) ** 2)) * (_rect_perp(ring[left], db, dp) + _rect_perp(ring[right], db, dp))
        if area < best:
            best, sel = area, (i, diam, left, right)
    i, di, li, ri = sel
    brp, blp, opp, lsp, rsp = ring[i], ring[i + 1], ring[di], ring[li], ring[ri]
    dx, dy = blp[0] - brp[0], blp[1] - brp[1]
    base, oppl = _rect_line(-dy, dx, dx * brp[1] - dy * brp[0]), _rect_line(-dy, dx, dx * opp[1] - dy * opp[0])
    leftl, rightl = _rect_line(-dx, -dy, -dy * lsp[1] - dx * lsp[0]), _rect_line(-dx, -dy, -dy * rsp[1] - dx * rsp[0])
    p0 = brp if rsp == brp else _rect_intersection(*base, *rightl)
    p1 = blp if lsp == blp else _rect_intersection(*base, *leftl)
    p2 = opp if lsp == opp else _rect_intersection(*oppl, *leftl)
    p3 = opp if rsp == opp else _rect_intersection(*oppl, *rightl)
    return np.array([p0, p1, p2, p3], float)


def min_rect_widths(polys: list) -> np.ndarray:
    """Shorter side of each polygon feature's minimum rotated rectangle (metres; NaN for empty or degenerate
    features), as min(side lengths) of shapely's minimum_rotated_rectangle."""
    out = np.full(len(polys), np.nan)
    for k, f in enumerate(polys):
        rings = [r for part in (f or []) for r in part if len(r)]
        if not rings:
            continue
        c = min_rotated_rectangle(np.concatenate(rings))
        if c is None:
            continue
        c = np.vstack([c, c[:1]])
        out[k] = float(min(((c[i + 1, 0] - c[i, 0]) ** 2 + (c[i + 1, 1] - c[i, 1]) ** 2) ** 0.5 for i in range(4)))
    return out


# ------------------------------------------------------------------------- overlay pieces (city coverage, net effect)
# scripts/build_tod_net_coverage.py built a city's covered area as shapely.union_all of point buffers, intersected it
# with the city and kept the parts as polygons ("patches"), later intersected with units' lots. region_polygons
# returns those parts for any Region: the region's boundary segments are cut at their crossings, each piece is kept
# when the region lies on exactly one side of it, and the kept pieces are linked into rings (at a vertex shared by
# two parts the sharpest left turn is taken, so parts touching at a point stay separate, as GEOS returns them).

def utm_for_lonlat(lon: float, lat: float) -> G.Projection:
    """WGS 84 / UTM zone (EPSG:326zz north, 327zz south) holding a longitude/latitude: geopandas' estimate_utm_crs,
    which queries the zone at the centre of the data's bounds."""
    zone = int(math.floor((lon + 180.0) / 6.0)) % 60 + 1
    south = lat < 0
    return G.Projection("tmerc", {"lat_0": 0.0, "lon_0": -183.0 + 6 * zone, "k_0": 0.9996, "x_0": 500000.0,
                                  "y_0": 10000000.0 if south else 0.0}, a=G.WGS84[0], f=G.WGS84[1],
                        name=f"WGS 84 / UTM zone {zone}{'S' if south else 'N'}")


class PointBuffers(Region):
    """Union of GEOS point buffers (regular n-gons, n = 4 * quad_segs, a vertex at angle 0; geom_extra_station._circle)
    of radius r[i] around (x[i], y[i]). Identical buffers count once. Chords lying inside another buffer are not
    boundary and are left out of edges()."""

    def __init__(self, x, y, r, quad_segs: int = 16):
        x, y = np.asarray(x, float), np.asarray(y, float)
        r = np.broadcast_to(np.asarray(r, float), x.shape)
        u = np.unique(np.c_[x, y, r], axis=0) if len(x) else np.zeros((0, 3))
        self.x, self.y, self.r = u[:, 0], u[:, 1], u[:, 2]
        self.n = 4 * quad_segs
        self.tree = cKDTree(np.c_[self.x, self.y]) if len(u) else None
        self.rmax = float(self.r.max()) if len(u) else 0.0

    def _pairs(self, px, py):
        """(point, buffer) candidate pairs within rmax of the centre."""
        cand = self.tree.query_ball_point(np.c_[px, py], self.rmax + 1e-9)
        lens = np.fromiter((len(c) for c in cand), np.int64, len(cand))
        pi = np.repeat(np.arange(len(px)), lens)
        bi = np.fromiter((i for c in cand for i in c), np.int64, int(lens.sum()))
        return pi, bi

    def _inside(self, dx, dy, r) -> np.ndarray:
        step = 2 * math.pi / self.n
        a = np.arctan2(dy, dx) % (2 * math.pi)
        mid = (np.floor(a / step) + 0.5) * step
        return dx * np.cos(mid) + dy * np.sin(mid) <= r * math.cos(step / 2)

    def contains(self, px, py) -> np.ndarray:
        px, py = np.asarray(px, float), np.asarray(py, float)
        out = np.zeros(len(px), bool)
        if self.tree is None or not len(px):
            return out
        for c0 in range(0, len(px), 200_000):
            sl = slice(c0, min(len(px), c0 + 200_000))
            pi, bi = self._pairs(px[sl], py[sl])
            hit = self._inside(px[sl][pi] - self.x[bi], py[sl][pi] - self.y[bi], self.r[bi])
            out[np.arange(len(px))[sl][np.unique(pi[hit])]] = True
        return out

    def _edges(self) -> np.ndarray:
        from missing_middleware.geom_extra_station import _circle
        if self.tree is None:
            return np.zeros((0, 4))
        V = np.stack([_circle(cx, cy, r, self.n) for cx, cy, r in zip(self.x, self.y, self.r)])  # (m, n+1, 2)
        seg = np.concatenate([V[:, :-1], V[:, 1:]], axis=2).reshape(-1, 4)
        own = np.repeat(np.arange(len(self.x)), self.n)
        # a chord lies inside another (convex) buffer when both its ends do
        inside_other = np.zeros(len(seg), bool)
        for c0 in range(0, len(seg), 200_000):
            s = seg[c0:c0 + 200_000]
            o = own[c0:c0 + 200_000]
            ok = np.ones(len(s), bool)
            for k in (0, 2):
                pi, bi = self._pairs(s[:, k], s[:, k + 1])
                keep = bi != o[pi]
                pi, bi = pi[keep], bi[keep]
                hit = self._inside(s[pi, k] - self.x[bi], s[pi, k + 1] - self.y[bi], self.r[bi])
                if k == 0:
                    first = set(zip(pi[hit].tolist(), bi[hit].tolist()))
                else:
                    both = [p for p, b in zip(pi[hit].tolist(), bi[hit].tolist()) if (p, b) in first]
                    ok[np.unique(np.asarray(both, int))] = False
            inside_other[c0:c0 + 200_000] = ~ok
        return seg[~inside_other]


def _cut_cross(S: np.ndarray, tol: float) -> tuple[np.ndarray, np.ndarray]:
    """Pieces of short segments between their crossings and other segments' ends lying on them (within tol), found
    through a k-d tree of segment midpoints (all segments must be short): (start points, end points)."""
    A, B = S[:, :2], S[:, 2:]
    D = B - A
    L = np.hypot(D[:, 0], D[:, 1])
    if not len(S):
        return np.zeros((0, 2)), np.zeros((0, 2))
    pairs = cKDTree((A + B) / 2).query_pairs(float(L.max()) + 2 * tol, output_type="ndarray")
    seg_i, ts = [np.arange(len(S)), np.arange(len(S))], [np.zeros(len(S)), np.ones(len(S))]
    for c0 in range(0, len(pairs), 1_000_000):
        i, j = pairs[c0:c0 + 1_000_000, 0], pairs[c0:c0 + 1_000_000, 1]
        Di, Dj = D[i], D[j]
        den = Di[:, 0] * Dj[:, 1] - Di[:, 1] * Dj[:, 0]
        qx, qy = A[j, 0] - A[i, 0], A[j, 1] - A[i, 1]
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (qx * Dj[:, 1] - qy * Dj[:, 0]) / den
            u = (qx * Di[:, 1] - qy * Di[:, 0]) / den
        ok = (den != 0) & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)
        m = ok & (t > 0) & (t < 1)
        seg_i.append(i[m]); ts.append(t[m])
        m = ok & (u > 0) & (u < 1)
        seg_i.append(j[m]); ts.append(u[m])
        for a, b in ((i, j), (j, i)):                 # ends of b lying on a
            Da, La = D[a], L[a]
            for P in (A[b], B[b]):
                ex, ey = P[:, 0] - A[a, 0], P[:, 1] - A[a, 1]
                with np.errstate(divide="ignore", invalid="ignore"):
                    tv = (ex * Da[:, 0] + ey * Da[:, 1]) / (La * La)
                    off = np.abs(ex * Da[:, 1] - ey * Da[:, 0]) / La
                m = (off < tol) & (tv > 0) & (tv < 1)
                seg_i.append(a[m]); ts.append(tv[m])
    si, tt = np.concatenate(seg_i), np.concatenate(ts)
    o = np.lexsort((tt, si))
    si, tt = si[o], tt[o]
    keep = np.r_[True, (si[1:] != si[:-1]) | (tt[1:] != tt[:-1])]
    si, tt = si[keep], tt[keep]
    P = A[si] + tt[:, None] * D[si]
    P[tt == 1.0] = B[si[tt == 1.0]]
    nxt = np.flatnonzero(si[1:] == si[:-1])
    return P[nxt], P[nxt + 1]


def region_polygons(region: Region, max_piece: float = 100.0, tol: float = 1e-6) -> list:
    """The parts of a Region as polygon features (one part each: shell, then holes), largest first; parts touching
    only at points are separate (GEOS's union / intersection output, split into its polygons). The boundary is
    drawn from region.edges(); coordinates are worked relative to the edges' lower-left corner."""
    E = region.edges()
    if not len(E):
        return []
    o = np.array([E[:, [0, 2]].min(), E[:, [1, 3]].min()])
    S = _cut(E - np.r_[o, o], max_piece)
    S = S[np.hypot(S[:, 2] - S[:, 0], S[:, 3] - S[:, 1]) > 0]
    P0, P1 = _cut_cross(S, tol)
    d = P1 - P0
    L = np.hypot(d[:, 0], d[:, 1])
    m = L > tol
    P0, P1, d, L = P0[m], P1[m], d[m], L[m]
    nrm = np.c_[-d[:, 1], d[:, 0]] / L[:, None]
    eps = np.clip(0.01 * L, 1e-6, 1e-3)[:, None]
    mid = (P0 + P1) / 2
    tp = np.r_[mid + eps * nrm, mid - eps * nrm] + o
    ins = region.contains(tp[:, 0], tp[:, 1])
    left, right = ins[:len(mid)], ins[len(mid):]
    b = left != right
    P0, P1 = np.where(right[:, None], P1, P0)[b], np.where(right[:, None], P0, P1)[b]   # region on the left
    if not len(P0):
        return []
    # vertices: piece ends snapped together within tol
    V = np.r_[P0, P1]
    parent = np.arange(len(V))
    for a, c in cKDTree(V).query_pairs(tol * 10, output_type="ndarray"):
        ra, rc = a, c
        while parent[ra] != ra:
            ra = parent[ra]
        while parent[rc] != rc:
            rc = parent[rc]
        if ra != rc:
            parent[max(ra, rc)] = min(ra, rc)
    for k in range(len(V)):
        r = k
        while parent[r] != r:
            r = parent[r]
        parent[k] = r
    u, v = parent[:len(P0)], parent[len(P0):]
    ok = u != v
    uv = np.unique(np.c_[u[ok], v[ok]], axis=0)
    fw = {(a, c) for a, c in uv.tolist()}
    uv = np.array([(a, c) for a, c in uv.tolist() if (c, a) not in fw], int).reshape(-1, 2)
    out_edges: dict[int, list[int]] = {}
    for e, a in enumerate(uv[:, 0].tolist()):
        out_edges.setdefault(a, []).append(e)
    used = np.zeros(len(uv), bool)
    rings = []
    for e0 in range(len(uv)):
        if used[e0]:
            continue
        ring, e = [], e0
        for _ in range(len(uv) + 1):
            used[e] = True
            a, c = uv[e]
            ring.append(a)
            din = V[c] - V[a]
            best, be = -9.0, -1
            for f in out_edges.get(c, []):
                if used[f] and f != e0:
                    continue
                w = uv[f, 1]
                dout = V[w] - V[c]
                ang = math.atan2(din[0] * dout[1] - din[1] * dout[0], din[0] * dout[0] + din[1] * dout[1])
                if ang > best:
                    best, be = ang, f
            if be < 0 or be == e0:
                break
            e = be
        if len(ring) >= 3:
            R = V[ring] + o
            rings.append(np.vstack([R, R[:1]]))
    sa = np.array([_ring_area_signed_local(r) for r in rings])
    shells = [k for k in range(len(rings)) if sa[k] > 0]
    holes = [k for k in range(len(rings)) if sa[k] < 0]
    feats = {k: [rings[k]] for k in shells}
    for h in holes:
        r = rings[h]
        dd = r[1] - r[0]
        ll = math.hypot(*dd)
        pt = (r[0] + r[1]) / 2 + min(1e-3, 0.01 * ll) * np.array([-dd[1], dd[0]]) / ll
        cands = [k for k in shells if G.points_in_feature([pt[0]], [pt[1]], [[rings[k]]])[0]]
        if cands:
            feats[min(cands, key=lambda k: sa[k])].append(r)
    polys = [[feats[k]] for k in sorted(shells, key=lambda k: -sa[k])]
    return polys


def _ring_area_signed_local(r: np.ndarray) -> float:
    x, y = r[:, 0] - r[0, 0], r[:, 1] - r[0, 1]
    return 0.5 * float(np.sum(x[:-1] * y[1:] - x[1:] * y[:-1]))


def region_area_by_tiles(polys: list, region: Region, tile: float = 1000.0) -> np.ndarray:
    """Area of each polygon feature lying inside the region (overlap_areas on square tiles over the feature, so that
    each tile only sees the edges near it; large features with many edges stay tractable)."""
    from missing_middleware.geom_extra_station import feature_bounds
    out = np.zeros(len(polys))
    fb = feature_bounds(polys) if len(polys) else np.zeros((0, 4))
    for k, f in enumerate(polys):
        if not f or not np.isfinite(fb[k, 0]):
            continue
        x0, y0, x1, y1 = fb[k]
        xs = np.arange(x0, x1, tile)
        ys = np.arange(y0, y1, tile)
        tiles = [[[np.array([(a, c), (min(a + tile, x1), c), (min(a + tile, x1), min(c + tile, y1)),
                             (a, min(c + tile, y1)), (a, c)])]] for a in xs for c in ys]
        out[k] = float(overlap_areas(tiles, Polygons([f]) & region).sum())
    return out
