"""Geometry operations the foundation, permits, district and UI-bundle builds need beyond missing_middleware.geom.

Same licence rule and geometry model as missing_middleware.geom (numpy, scipy, pandas, pyarrow and the standard library
only; polygon features are lists of parts, each part a list of rings, exterior first, each ring an (n, 2) array).
The functions reproduce what the replaced shapely/GEOS 3.14 and geopandas calls returned, so the outputs stay the same:

  interior_points          shapely representative_point (GEOS InteriorPointArea: widest horizontal run through the
                           polygon at a scan line next to the middle of its height)
  simplify_preserve        shapely simplify(tol, preserve_topology=True) (GEOS TopologyPreservingSimplifier:
                           Douglas-Peucker; a shortcut is refused if it would cross or overlap a ring of the feature,
                           or move another ring of the same polygon to its other side)
  set_precision_polygons   shapely set_precision(grid) for polygons in the common case: coordinates rounded to the
                           grid, repeated points dropped, collapsed rings removed, rings re-oriented and re-started as
                           GEOS OverlayNG returns them (exterior clockwise, holes counter-clockwise)
  intersection_areas       area of each overlap of two polygon layers (geopandas.overlay(how="intersection") + .area),
                           from the boundary integral of the overlap: the parts of each boundary inside the other
  nearest_polygon          geopandas.sjoin_nearest for points: the polygon with the nearest boundary
  WKB / GeoParquet / GeoJSON readers and writers for the files the builds exchange.

Exact arithmetic (fractions) settles orientation tests that floating point cannot, as GEOS's robust predicates do.
Projection differences (missing_middleware.geom treats NAD83(HARN) as NAD83; PROJ shifts it by about a metre) move
projected coordinates by a near-constant offset that cancels when a result is projected back.
"""
from __future__ import annotations

import json
import math
import struct
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware import geom as G

# ------------------------------------------------------------------------------------------------ predicates
def _sign(v) -> int:
    return 1 if v > 0 else (-1 if v < 0 else 0)


def _orient(ax, ay, bx, by, cx, cy) -> int:
    """Sign of the turn a -> b -> c (1 left/counter-clockwise, -1 right, 0 collinear), exact (floating-point filter
    as in GEOS, exact rational arithmetic when the filter cannot decide)."""
    detleft = (ax - cx) * (by - cy)
    detright = (ay - cy) * (bx - cx)
    det = detleft - detright
    if detleft > 0:
        if detright <= 0:
            return _sign(det)
        detsum = detleft + detright
    elif detleft < 0:
        if detright >= 0:
            return _sign(det)
        detsum = -detleft - detright
    else:
        return _sign(det)
    if abs(det) >= 1e-15 * detsum:
        return _sign(det)
    F = Fraction
    return _sign((F(ax) - F(cx)) * (F(by) - F(cy)) - (F(ay) - F(cy)) * (F(bx) - F(cx)))


def _env_point(ax, ay, bx, by, px, py) -> bool:
    return min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by)


def _interior_intersection(p1, p2, q1, q2) -> bool:
    """GEOS RobustLineIntersector: do segments p1p2 and q1q2 meet at a point interior to either of them?"""
    if (max(p1[0], p2[0]) < min(q1[0], q2[0]) or min(p1[0], p2[0]) > max(q1[0], q2[0])
            or max(p1[1], p2[1]) < min(q1[1], q2[1]) or min(p1[1], p2[1]) > max(q1[1], q2[1])):
        return False
    Pq1 = _orient(p1[0], p1[1], p2[0], p2[1], q1[0], q1[1])
    Pq2 = _orient(p1[0], p1[1], p2[0], p2[1], q2[0], q2[1])
    if (Pq1 > 0 and Pq2 > 0) or (Pq1 < 0 and Pq2 < 0):
        return False
    Qp1 = _orient(q1[0], q1[1], q2[0], q2[1], p1[0], p1[1])
    Qp2 = _orient(q1[0], q1[1], q2[0], q2[1], p2[0], p2[1])
    if (Qp1 > 0 and Qp2 > 0) or (Qp1 < 0 and Qp2 < 0):
        return False
    if Pq1 == 0 and Pq2 == 0 and Qp1 == 0 and Qp2 == 0:     # collinear
        q1inP = _env_point(*p1, *p2, *q1)
        q2inP = _env_point(*p1, *p2, *q2)
        p1inQ = _env_point(*q1, *q2, *p1)
        p2inQ = _env_point(*q1, *q2, *p2)
        if q1inP and q2inP:
            pts = (q1, q2)
        elif p1inQ and p2inQ:
            pts = (p1, p2)
        elif q1inP and p1inQ:
            pts = (q1, p1)
        elif q1inP and p2inQ:
            pts = (q1, p2)
        elif q2inP and p1inQ:
            pts = (q2, p1)
        elif q2inP and p2inQ:
            pts = (q2, p2)
        else:
            return False
        for pt in pts:
            if not (pt == p1 or pt == p2) or not (pt == q1 or pt == q2):
                return True
        return False
    if Pq1 == 0 or Pq2 == 0 or Qp1 == 0 or Qp2 == 0:
        if p1 == q1 or p1 == q2 or p2 == q1 or p2 == q2:
            return False                                   # shared endpoint
        return True                                        # an endpoint on the other segment's interior
    return True                                            # proper crossing


def _ray_crossings(px, py, segs) -> int:
    """GEOS RayCrossingCounter count for point (px, py) over segments [(x0, y0, x1, y1), ...]."""
    n = 0
    for x0, y0, x1, y1 in segs:
        if x0 < px and x1 < px:
            continue
        if px == x1 and py == y1:
            continue
        if y0 == py and y1 == py:
            continue
        if (y0 > py and y1 <= py) or (y1 > py and y0 <= py):
            o = _orient(x0, y0, x1, y1, px, py)
            if o == 0:
                continue
            if y1 < y0:
                o = -o
            if o > 0:
                n += 1
    return n


# GEOS ComponentJumpChecker: a shortcut must not move another ring of the same polygon from one side of the line to
# the other; each ring is represented by its second vertex. (Checked against GEOS 3.14 on every Wisconsin tract, block
# group, county subdivision and county: rings of other polygons in a MultiPolygon are not tested.)
_COMPONENT_POINT = 1


def _pt_seg_dist(ax, ay, bx, by, px, py):
    """GEOS Distance::pointToSegment, vectorised over p (same floating-point steps)."""
    if ax == bx and ay == by:
        return np.sqrt((px - ax) * (px - ax) + (py - ay) * (py - ay))
    len2 = (bx - ax) * (bx - ax) + (by - ay) * (by - ay)
    r = ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / len2
    s = ((ay - py) * (bx - ax) - (ax - px) * (by - ay)) / len2
    d = np.abs(s) * math.sqrt(len2)
    da = np.sqrt((px - ax) * (px - ax) + (py - ay) * (py - ay))
    db = np.sqrt((px - bx) * (px - bx) + (py - by) * (py - by))
    return np.where(r <= 0.0, da, np.where(r >= 1.0, db, d))


# ------------------------------------------------------------------------------------------- interior points
def _interior_point_polygon(part):
    """(x, y, width) for one polygon part, as GEOS InteriorPointArea's InteriorPointPolygon."""
    ext = part[0]
    miny, maxy = float(ext[:, 1].min()), float(ext[:, 1].max())
    centre = (miny + maxy) / 2.0
    hi, lo = maxy, miny
    for r in part:
        ys = r[:, 1]
        below = ys[ys <= centre]
        above = ys[ys > centre]
        if len(below):
            lo = max(lo, float(below.max()))
        if len(above):
            hi = min(hi, float(above.min()))
    scan_y = (hi + lo) / 2.0
    best = (float(ext[0, 0]), float(ext[0, 1]))
    crossings = []
    for r in part:
        if not (r[:, 1].min() <= scan_y <= r[:, 1].max()):
            continue
        for k in range(1, len(r)):
            x0, y0 = float(r[k - 1, 0]), float(r[k - 1, 1])
            x1, y1 = float(r[k, 0]), float(r[k, 1])
            if (y0 > scan_y and y1 > scan_y) or (y0 < scan_y and y1 < scan_y):
                continue
            if y0 == y1:
                continue
            if y0 == scan_y and y1 < scan_y:
                continue
            if y1 == scan_y and y0 < scan_y:
                continue
            if x0 == x1:
                crossings.append(x0)
            else:
                m = (y1 - y0) / (x1 - x0)
                crossings.append(x0 + (scan_y - y0) / m)
    width = 0.0
    if crossings:
        crossings.sort()
        for i in range(0, len(crossings) - 1, 2):
            w = crossings[i + 1] - crossings[i]
            if w > width:
                width = w
                best = ((crossings[i] + crossings[i + 1]) / 2.0, scan_y)
    return best[0], best[1], width


def interior_points(polys: list) -> tuple[np.ndarray, np.ndarray]:
    """A point inside each polygon feature, identical to shapely's representative_point (GEOS InteriorPointArea).
    Rings must be closed (first point repeated last), as read from shapefiles and GeoJSON."""
    xs, ys = np.full(len(polys), np.nan), np.full(len(polys), np.nan)
    for k, feat in enumerate(polys):
        best_w = -1.0
        for part in feat:
            if not len(part) or not len(part[0]):
                continue
            x, y, w = _interior_point_polygon(part)
            if w > best_w:
                best_w, xs[k], ys[k] = w, x, y
    return xs, ys


# ----------------------------------------------------------------------------------- topology-preserving simplify
class _Line:
    __slots__ = ("pts", "is_ring", "min_size", "result", "cid", "part")

    def __init__(self, pts, is_ring, cid, part=0):
        self.pts = [(float(x), float(y)) for x, y in pts]
        self.is_ring = is_ring
        self.min_size = 4 if is_ring else 2
        self.result = []          # list of [p0, p1]
        self.cid = cid
        self.part = part

    def result_size(self):
        return 0 if not self.result else len(self.result) + 1


class _SegIndex:
    """Segments with envelope queries (numpy filter over all live segments)."""

    def __init__(self):
        self.a = np.zeros((0, 4))
        self.cid = np.zeros(0, np.int64)
        self.idx = np.zeros(0, np.int64)
        self.live = np.zeros(0, bool)
        self._pending = []

    def add_many(self, arr, cid, idx):
        self.a = np.vstack([self.a, arr])
        self.cid = np.concatenate([self.cid, cid])
        self.idx = np.concatenate([self.idx, idx])
        self.live = np.concatenate([self.live, np.ones(len(arr), bool)])

    def add(self, p0, p1):
        self._pending.append((p0[0], p0[1], p1[0], p1[1]))

    def _flush(self):
        if self._pending:
            arr = np.array(self._pending, float)
            self._pending = []
            self.add_many(arr, np.full(len(arr), -1), np.full(len(arr), -1))

    def query(self, p0, p1):
        self._flush()
        a = self.a
        if not len(a):
            return []
        x0, x1 = min(p0[0], p1[0]), max(p0[0], p1[0])
        y0, y1 = min(p0[1], p1[1]), max(p0[1], p1[1])
        m = (self.live & (np.minimum(a[:, 0], a[:, 2]) <= x1) & (np.maximum(a[:, 0], a[:, 2]) >= x0)
             & (np.minimum(a[:, 1], a[:, 3]) <= y1) & (np.maximum(a[:, 1], a[:, 3]) >= y0))
        return np.flatnonzero(m)


def _invalid_intersection(s, p0, p1) -> bool:
    q0, q1 = (float(s[0]), float(s[1])), (float(s[2]), float(s[3]))
    if (q0 == p0 and q1 == p1) or (q0 == p1 and q1 == p0):
        return True
    return _interior_intersection(q0, q1, p0, p1)


class _Simplifier:
    def __init__(self, lines, tol):
        self.lines, self.tol = lines, tol
        self.inp, self.out = _SegIndex(), _SegIndex()
        self.offset = {}
        for ln in lines:
            p = np.array(ln.pts)
            if len(p) < 2:
                continue
            self.offset[ln.cid] = len(self.inp.a)
            self.inp.add_many(np.c_[p[:-1], p[1:]], np.full(len(p) - 1, ln.cid), np.arange(len(p) - 1))
        self.comp = [(ln.cid, ln.part, ln.pts[_COMPONENT_POINT][0], ln.pts[_COMPONENT_POINT][1]) for ln in lines if len(ln.pts) > 1]

    # ---- checks
    def _has_output_x(self, p0, p1):
        for k in self.out.query(p0, p1):
            if _invalid_intersection(self.out.a[k], p0, p1):
                return True
        return False

    def _has_input_x(self, line, i, j, p0, p1):
        for k in self.inp.query(p0, p1):
            if _invalid_intersection(self.inp.a[k], p0, p1):
                if line is not None and self.inp.cid[k] == line.cid:
                    si = self.inp.idx[k]
                    if i <= j:
                        if i <= si < j:
                            continue
                    elif si >= i or si <= j:
                        continue
                return True
        return False

    def _has_jump(self, line, segs, env, p0, p1):
        for cid, part, cx, cy in self.comp:
            if cid == line.cid or part != line.part:
                continue
            if env[0] <= cx <= env[2] and env[1] <= cy <= env[3]:
                if _ray_crossings(cx, cy, segs) % 2 != _ray_crossings(cx, cy, [(p0[0], p0[1], p1[0], p1[1])]) % 2:
                    return True
        return False

    def _valid_section(self, line, i, j, p0, p1):
        if self._has_output_x(p0, p1):
            return False
        if self._has_input_x(line, i, j, p0, p1):
            return False
        if len(self.comp) > 1:
            pts = line.pts[i:j + 1]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            env = (min(xs), min(ys), max(xs), max(ys))
            segs = [(pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1]) for k in range(len(pts) - 1)]
            if self._has_jump(line, segs, env, p0, p1):
                return False
        return True

    def _valid_endpoint(self, line, s1, s2, p0, p1):
        if _orient(p0[0], p0[1], p1[0], p1[1], s1[0][0], s1[0][1]) == 0:
            return True
        if self._has_output_x(p0, p1):
            return False
        if self._has_input_x(None, -1, -1, p0, p1):
            return False
        if len(self.comp) > 1:
            pts = [s1[0], s1[1], s2[0], s2[1]]
            env = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
            segs = [(s1[0][0], s1[0][1], s1[1][0], s1[1][1]), (s2[0][0], s2[0][1], s2[1][0], s2[1][1])]
            if self._has_jump(line, segs, env, p0, p1):
                return False
        return True

    # ---- Douglas-Peucker with topology checks
    def simplify_line(self, line):
        pts = line.pts
        if len(pts) < 2:
            return
        P = np.array(pts)
        stack = [(0, len(pts) - 1, 0)]
        while stack:
            i, j, depth = stack.pop()
            depth += 1
            if i + 1 == j:
                line.result.append([pts[i], pts[j]])
                continue
            ok = True
            if line.result_size() < line.min_size and depth + 1 < line.min_size:
                ok = False
            d = _pt_seg_dist(pts[i][0], pts[i][1], pts[j][0], pts[j][1], P[i + 1:j, 0], P[i + 1:j, 1])
            far = i + 1 + int(np.argmax(d))
            if d[far - i - 1] > self.tol:
                ok = False
            if ok:
                ok = self._valid_section(line, i, j, pts[i], pts[j])
            if ok:
                off = self.offset[line.cid]
                self.inp.live[off + i: off + j] = False
                self.out.add(pts[i], pts[j])
                line.result.append([pts[i], pts[j]])
                continue
            stack.append((far, j, depth))
            stack.append((i, far, depth))
        if line.is_ring and pts[0] == pts[-1] and line.result_size() > line.min_size:
            first, last = line.result[0], line.result[-1]
            p0, p1 = last[0], first[1]
            dist = float(_pt_seg_dist(p0[0], p0[1], p1[0], p1[1], np.array([first[0][0]]), np.array([first[0][1]]))[0])
            if dist <= self.tol and self._valid_endpoint(line, first, last, p0, p1):
                first[0] = last[0]
                line.result.pop()


def simplify_preserve(polys: list, tol: float) -> list:
    """shapely simplify(tol, preserve_topology=True) for each polygon feature (rings closed)."""
    out = []
    for feat in polys:
        lines, cid = [], 0
        for pi, part in enumerate(feat):
            for r in part:
                lines.append(_Line(r, True, cid, pi))
                cid += 1
        s = _Simplifier(lines, tol)
        for ln in lines:
            s.simplify_line(ln)
        res, k = [], 0
        for part in feat:
            rings = []
            for _ in part:
                ln = lines[k]
                k += 1
                if ln.result:
                    coords = [seg[0] for seg in ln.result] + [ln.result[-1][1]]
                else:
                    coords = ln.pts
                rings.append(np.array(coords, float))
            res.append(rings)
        out.append(res)
    return out


# ------------------------------------------------------------------------------------------------- precision
def _round_half_up(v: np.ndarray) -> np.ndarray:
    """GEOS util::round (Java Math.round): halves round towards +infinity."""
    f = np.floor(v)
    return np.where(v - f >= 0.5, f + 1.0, f)


def _signed_area(r: np.ndarray) -> float:
    x, y = r[:, 0], r[:, 1]
    return 0.5 * float(np.dot(x[:-1], y[1:]) - np.dot(y[:-1], x[1:]))


def _pixel_hits(px, py, qx, qy, hx, hy) -> bool:
    """GEOS/JTS HotPixel.intersectsScaled: does segment p-q (grid units) touch the unit pixel centred on (hx, hy)?
    The pixel's top and right sides are open."""
    if px > qx:
        px, py, qx, qy = qx, qy, px, py
    maxx, minx, maxy, miny = hx + 0.5, hx - 0.5, hy + 0.5, hy - 0.5
    if min(px, qx) >= maxx or max(px, qx) < minx or min(py, qy) >= maxy or max(py, qy) < miny:
        return False
    if px == qx or py == qy:
        return True
    ul = _orient(px, py, qx, qy, minx, maxy)
    if ul == 0:
        return not (py < qy)
    ur = _orient(px, py, qx, qy, maxx, maxy)
    if ur == 0:
        return not (py > qy)
    if ul != ur:
        return True
    ll = _orient(px, py, qx, qy, minx, miny)
    if ll == 0 or ll != ul:
        return True
    lr = _orient(px, py, qx, qy, maxx, miny)
    if lr == 0:
        return not (py < qy)
    return ll != lr or lr != ur


def _snap_ring(Q: list, H: np.ndarray) -> list:
    """Insert into each segment of ring Q (closed list of integer grid points) the hot pixels H (all vertices of
    the feature) that the segment passes through, as snap rounding nodes them."""
    out = [Q[0]]
    for k in range(len(Q) - 1):
        (ax, ay), (bx, by) = Q[k], Q[k + 1]
        m = ((H[:, 0] >= min(ax, bx) - 0.5) & (H[:, 0] <= max(ax, bx) + 0.5)
             & (H[:, 1] >= min(ay, by) - 0.5) & (H[:, 1] <= max(ay, by) + 0.5))
        hits = []
        for hx, hy in H[m]:
            hx, hy = int(hx), int(hy)
            if (hx, hy) == (ax, ay) or (hx, hy) == (bx, by):
                continue
            if _pixel_hits(ax, ay, bx, by, hx, hy):
                hits.append(((hx - ax) * (bx - ax) + (hy - ay) * (by - ay), (hx, hy)))
        out += [h for _, h in sorted(hits)]
        out.append((bx, by))
    return out


def _area2(pts: list) -> int:
    """Twice the signed area of a closed walk of integer points (exact)."""
    return sum(pts[k][0] * pts[k + 1][1] - pts[k + 1][0] * pts[k][1] for k in range(len(pts) - 1))


def _drop_collapsed_loops(Q: list) -> list:
    """Remove zero-area excursions (spikes and doubled-back loops) from a closed walk, keeping its start."""
    changed = True
    while changed and len(Q) >= 4:
        changed = False
        dedup = [Q[0]]
        for p in Q[1:]:
            if p != dedup[-1]:
                dedup.append(p)
        Q = dedup
        seen = {}
        for k, p in enumerate(Q[:-1]):
            if p in seen:
                i = seen[p]
                if _area2(Q[i:k + 1]) == 0:
                    Q = Q[:i + 1] + Q[k + 1:]
                    changed = True
                    break
            seen[p] = k
    return Q


def set_precision_polygons(polys: list, grid: float) -> list:
    """shapely set_precision(grid) for polygon features (GEOS snap-rounding precision reduction), for outlines where
    rounding does not make rings cross or merge: coordinates rounded to the grid (exact for grid = 10^-k), each
    segment noded at the grid pixels of other vertices it passes through, zero-area spikes and repeated points
    removed, collapsed rings dropped (a part whose exterior collapses is dropped), exteriors clockwise and holes
    counter-clockwise, each ring starting at its second vertex (the order GEOS OverlayNG rebuilds rings in)."""
    scale = round(1.0 / grid)
    out = []
    for feat in polys:
        rings_q = []
        for part in feat:
            rings_q.append([])
            for r in part:
                q = _round_half_up(np.asarray(r, float) * scale)
                rings_q[-1].append([(int(x), int(y)) for x, y in q])
        allv = [p for part in rings_q for r in part for p in r]
        H = np.unique(np.array(allv, dtype=np.int64).reshape(-1, 2), axis=0)
        parts = []
        for part in rings_q:
            rings = []
            for h, Q in enumerate(part):
                if Q and Q[0] != Q[-1]:
                    Q = Q + [Q[0]]
                Q = _drop_collapsed_loops(_snap_ring(Q, H)) if len(Q) >= 4 else Q
                a2 = _area2(Q) if len(Q) >= 4 else 0
                if len(Q) < 4 or a2 == 0:
                    if h == 0:
                        break
                    continue
                if (h == 0) != (a2 < 0):           # exterior clockwise, holes counter-clockwise
                    Q = Q[::-1]
                Q = Q[1:] + Q[1:2]
                rings.append(np.array(Q, float) / scale)
            else:
                if rings:
                    parts.append(rings)
        out.append(parts)
    return out


def rings_are_simple(feature) -> bool:
    """Basic validity check standing in for shapely is_valid on simplified outlines: every ring closed with at least
    4 points, no two segments crossing or overlapping, and no ring touching itself; rings may share single vertices
    with other rings."""
    segs, owner = [], []
    for pi, part in enumerate(feature):
        for ri, r in enumerate(part):
            r = np.asarray(r, float)
            if len(r) < 4 or not np.array_equal(r[0], r[-1]):
                return False
            n = len(r) - 1
            for k in range(n):
                segs.append((float(r[k, 0]), float(r[k, 1]), float(r[k + 1, 0]), float(r[k + 1, 1])))
                owner.append((pi, ri, k, n))
    if not segs:
        return False
    a = np.array(segs)
    lo_x, hi_x = np.minimum(a[:, 0], a[:, 2]), np.maximum(a[:, 0], a[:, 2])
    lo_y, hi_y = np.minimum(a[:, 1], a[:, 3]), np.maximum(a[:, 1], a[:, 3])
    for m in range(len(segs)):
        cand = np.flatnonzero((lo_x <= hi_x[m]) & (hi_x >= lo_x[m]) & (lo_y <= hi_y[m]) & (hi_y >= lo_y[m]))
        s1 = segs[m]
        p0, p1 = (s1[0], s1[1]), (s1[2], s1[3])
        for k in cand[cand > m]:
            s2 = segs[k]
            q0, q1 = (s2[0], s2[1]), (s2[2], s2[3])
            if _interior_intersection(p0, p1, q0, q1):
                return False
            (pa, ra, ia, n), (pb, rb, ib, _) = owner[m], owner[k]
            if (pa, ra) == (pb, rb):
                adjacent = abs(ia - ib) == 1 or abs(ia - ib) == n - 1
                if not adjacent and ({p0, p1} & {q0, q1}):
                    return False                     # the ring touches itself at a vertex
    return True


# -------------------------------------------------------------------------------------------- overlay areas
def _oriented_edges(feature) -> np.ndarray:
    """Edges (x0, y0, x1, y1) with the interior on the left: exteriors counter-clockwise, holes clockwise."""
    out = []
    for part in feature:
        for h, r in enumerate(part):
            r = np.asarray(r, float)
            if len(r) < 3:
                continue
            if not np.array_equal(r[0], r[-1]):
                r = np.vstack([r, r[:1]])
            a = _signed_area(r)
            if (h == 0 and a < 0) or (h > 0 and a > 0):
                r = r[::-1]
            e = np.c_[r[:-1], r[1:]]
            e = e[(e[:, 0] != e[:, 2]) | (e[:, 1] != e[:, 3])]
            out.append(e)
    return np.concatenate(out) if out else np.zeros((0, 4))


def _box_pairs(A: np.ndarray, B: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Index pairs (i, j) of segments of A and B whose bounding boxes overlap (grid hashing)."""
    if not len(A) or not len(B):
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    def boxes(S):
        return (np.minimum(S[:, 0], S[:, 2]), np.minimum(S[:, 1], S[:, 3]),
                np.maximum(S[:, 0], S[:, 2]), np.maximum(S[:, 1], S[:, 3]))
    ax0, ay0, ax1, ay1 = boxes(A)
    bx0, by0, bx1, by1 = boxes(B)
    ext = np.r_[ax1 - ax0, ay1 - ay0, bx1 - bx0, by1 - by0]
    cell = max(float(np.percentile(ext, 90)) * 2.0, 1e-9)
    ox, oy = min(ax0.min(), bx0.min()), min(ay0.min(), by0.min())

    def cells(x0, y0, x1, y1):
        i0, i1 = np.floor((x0 - ox) / cell).astype(np.int64), np.floor((x1 - ox) / cell).astype(np.int64)
        j0, j1 = np.floor((y0 - oy) / cell).astype(np.int64), np.floor((y1 - oy) / cell).astype(np.int64)
        nx, ny = i1 - i0 + 1, j1 - j0 + 1
        cnt = nx * ny
        idx = np.repeat(np.arange(len(x0)), cnt)
        start = np.repeat(np.cumsum(cnt) - cnt, cnt)
        k = np.arange(cnt.sum()) - start
        ci = i0[idx] + k % nx[idx]
        cj = j0[idx] + k // nx[idx]
        return ci * 4_000_003 + cj, idx
    ka, ia = cells(ax0, ay0, ax1, ay1)
    kb, ib = cells(bx0, by0, bx1, by1)
    ob = np.argsort(kb, kind="stable")
    kb, ib = kb[ob], ib[ob]
    lo, hi = np.searchsorted(kb, ka, "left"), np.searchsorted(kb, ka, "right")
    cnt = hi - lo
    pa = np.repeat(ia, cnt)
    start = np.repeat(lo - (np.cumsum(cnt) - cnt), cnt)
    pb = ib[np.arange(cnt.sum()) + start]
    key = np.unique(pa * len(B) + pb)
    pa, pb = key // len(B), key % len(B)
    ok = (ax0[pa] <= bx1[pb]) & (ax1[pa] >= bx0[pb]) & (ay0[pa] <= by1[pb]) & (ay1[pa] >= by0[pb])
    return pa[ok], pb[ok]


def _split_records(E: np.ndarray, params: list, cover: list):
    """Split edges at parameters; return sub-segment arrays and, per sub-segment, coincident partner info.
    params: arrays (edge, t); cover: arrays (edge, t_lo, t_hi, partner, same_direction)."""
    n = len(E)
    if n == 0:
        z = np.zeros((0, 2))
        return (np.zeros(0, np.int64), z, z, z,
                (np.zeros(0, np.int64), np.zeros(0, np.int64), np.zeros(0, bool)))
    pe = np.concatenate([np.asarray(p[0], np.int64) for p in params] + [np.arange(n), np.arange(n)])
    pt = np.concatenate([np.asarray(p[1], float) for p in params] + [np.zeros(n), np.ones(n)])
    keep = (pt >= 0) & (pt <= 1)
    pe, pt = pe[keep], pt[keep]
    o = np.lexsort((pt, pe))
    pe, pt = pe[o], pt[o]
    dup = np.r_[False, (pe[1:] == pe[:-1]) & (pt[1:] - pt[:-1] <= 1e-12)]
    pe, pt = pe[~dup], pt[~dup]
    same_edge = pe[1:] == pe[:-1]
    se = pe[:-1][same_edge]
    t0, t1 = pt[:-1][same_edge], pt[1:][same_edge]
    tm = (t0 + t1) / 2
    d = E[se, 2:] - E[se, :2]
    P0 = E[se, :2] + d * t0[:, None]
    P1 = E[se, :2] + d * t1[:, None]
    # exact ends for whole-edge ends
    P0[t0 == 0] = E[se[t0 == 0], :2]
    P1[t1 == 1] = E[se[t1 == 1], 2:]
    M = E[se, :2] + d * tm[:, None]
    # coincidence: (sub-segment, partner, same)
    if cover and sum(len(c[0]) for c in cover):
        ce = np.concatenate([c[0] for c in cover])
        clo = np.concatenate([c[1] for c in cover])
        chi = np.concatenate([c[2] for c in cover])
        cpart = np.concatenate([c[3] for c in cover])
        csame = np.concatenate([c[4] for c in cover])
        first = np.searchsorted(se, ce, "left")
        last = np.searchsorted(se, ce, "right")
        cnt = last - first
        rec = np.repeat(np.arange(len(ce)), cnt)
        sub = np.arange(cnt.sum()) + np.repeat(first - (np.cumsum(cnt) - cnt), cnt)
        m = (tm[sub] >= clo[rec] - 1e-12) & (tm[sub] <= chi[rec] + 1e-12)
        co = (sub[m], cpart[rec[m]], csame[rec[m]])
    else:
        co = (np.zeros(0, np.int64), np.zeros(0, np.int64), np.zeros(0, bool))
    return se, P0, P1, M, co


def _overlap_one(EA: np.ndarray, EB: np.ndarray, owner: np.ndarray, featA, featsB: dict, eps: float) -> dict:
    """Area of A ∩ B_k for every candidate k (featsB: k -> feature), from oriented edges (interior on the left)."""
    ia, ib = _box_pairs(EA, EB)
    A0, A1 = EA[ia, :2], EA[ia, 2:]
    B0, B1 = EB[ib, :2], EB[ib, 2:]
    dA, dB = A1 - A0, B1 - B0
    LA, LB = np.hypot(dA[:, 0], dA[:, 1]), np.hypot(dB[:, 0], dB[:, 1])

    def cross(u, v):
        return u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0]
    sB0 = cross(dA, B0 - A0) / LA          # signed distances of B's ends from line A
    sB1 = cross(dA, B1 - A0) / LA
    sA0 = cross(dB, A0 - B0) / LB          # of A's ends from line B
    sA1 = cross(dB, A1 - B0) / LB
    col = (np.abs(sB0) < eps) & (np.abs(sB1) < eps) | (np.abs(sA0) < eps) & (np.abs(sA1) < eps)
    pa_params, pb_params, ca, cb = [], [], [], []
    # collinear overlaps
    if col.any():
        c = np.flatnonzero(col)
        tB0 = np.einsum("ij,ij->i", B0[c] - A0[c], dA[c]) / LA[c] ** 2
        tB1 = np.einsum("ij,ij->i", B1[c] - A0[c], dA[c]) / LA[c] ** 2
        uA0 = np.einsum("ij,ij->i", A0[c] - B0[c], dB[c]) / LB[c] ** 2
        uA1 = np.einsum("ij,ij->i", A1[c] - B0[c], dB[c]) / LB[c] ** 2
        lo, hi = np.maximum(0, np.minimum(tB0, tB1)), np.minimum(1, np.maximum(tB0, tB1))
        ulo, uhi = np.maximum(0, np.minimum(uA0, uA1)), np.minimum(1, np.maximum(uA0, uA1))
        ov = (hi - lo) * LA[c] > eps
        c, lo, hi, ulo, uhi = c[ov], lo[ov], hi[ov], ulo[ov], uhi[ov]
        tB0, tB1, uA0, uA1 = tB0[ov], tB1[ov], uA0[ov], uA1[ov]
        same = np.einsum("ij,ij->i", dA[c], dB[c]) > 0
        pa_params += [(ia[c], tB0), (ia[c], tB1)]
        pb_params += [(ib[c], uA0), (ib[c], uA1)]
        ca.append((ia[c], lo, hi, owner[ib[c]], same))
        cb.append((ib[c], ulo, uhi, np.zeros(len(c), np.int64), same))
    # crossings and touches
    nc = np.flatnonzero(~col)
    if len(nc):
        a0, a1, b0, b1 = sA0[nc], sA1[nc], sB0[nc], sB1[nc]
        za0, za1, zb0, zb1 = np.abs(a0) < eps, np.abs(a1) < eps, np.abs(b0) < eps, np.abs(b1) < eps
        hitA = za0 | za1 | (np.sign(a0) != np.sign(a1))
        hitB = zb0 | zb1 | (np.sign(b0) != np.sign(b1))
        h = hitA & hitB
        k = nc[h]
        with np.errstate(divide="ignore", invalid="ignore"):
            t = np.where(za0[h], 0.0, np.where(za1[h], 1.0, a0[h] / (a0[h] - a1[h])))
            u = np.where(zb0[h], 0.0, np.where(zb1[h], 1.0, b0[h] / (b0[h] - b1[h])))
        pa_params.append((ia[k], np.clip(t, 0, 1)))
        pb_params.append((ib[k], np.clip(u, 0, 1)))
    out = {}
    # A's boundary pieces
    _, P0, P1, M, (cs, cp, csm) = _split_records(EA, pa_params, ca)
    contrib = 0.5 * (P0[:, 0] * P1[:, 1] - P1[:, 0] * P0[:, 1])
    for k, fb in featsB.items():
        same_k = np.zeros(len(M), bool)
        coin_k = np.zeros(len(M), bool)
        sel = cp == k
        coin_k[cs[sel]] = True
        same_k[cs[sel & csm]] = True
        test = ~coin_k
        inside = np.zeros(len(M), bool)
        if test.any():
            inside[test] = G.points_in_feature(M[test, 0], M[test, 1], fb)
        out[k] = float(contrib[same_k | inside].sum())
    # B's boundary pieces
    sub_edge, P0, P1, M, (cs, _, _) = _split_records(EB, pb_params, cb)
    contrib = 0.5 * (P0[:, 0] * P1[:, 1] - P1[:, 0] * P0[:, 1])
    coin = np.zeros(len(M), bool)
    coin[cs] = True
    inside = np.zeros(len(M), bool)
    if (~coin).any():
        inside[~coin] = G.points_in_feature(M[~coin, 0], M[~coin, 1], featA)
    for k in featsB:
        m = (owner[sub_edge] == k) & inside
        out[k] += float(contrib[m].sum())
    return out


def _feature_bounds(polys):
    b = np.full((len(polys), 4), np.nan)
    for k, f in enumerate(polys):
        rings = [r for p in f for r in p[:1] if len(r)]
        if rings:
            a = np.concatenate(rings)
            b[k] = a[:, 0].min(), a[:, 1].min(), a[:, 0].max(), a[:, 1].max()
    return b


def intersection_areas(polys_a: list, polys_b: list, eps: float = 1e-6, min_area: float = 0.0) -> pd.DataFrame:
    """Planar area of every overlap of a feature of A with a feature of B (columns i, j, area), as the area of
    geopandas.overlay(A, B, how="intersection") pieces summed per pair. Coordinates must be projected (metres);
    eps (CRS units) is the distance under which two edges count as the same line. Pairs whose overlap area is not
    above min_area (only touching, or numerical noise) are left out."""
    ba, bb = _feature_bounds(polys_a), _feature_bounds(polys_b)
    rows = []
    edges_b = {}
    for i, fa in enumerate(polys_a):
        if not fa or np.isnan(ba[i, 0]):
            continue
        cand = np.flatnonzero((bb[:, 0] <= ba[i, 2]) & (bb[:, 2] >= ba[i, 0]) & (bb[:, 1] <= ba[i, 3]) & (bb[:, 3] >= ba[i, 1]))
        if not len(cand):
            continue
        org = ba[i, :2]
        EA = _oriented_edges(fa) - np.r_[org, org]
        eb, own = [], []
        for j in cand:
            if j not in edges_b:
                edges_b[j] = _oriented_edges(polys_b[j])
            e = edges_b[j]
            m = ((np.maximum(e[:, 0], e[:, 2]) >= ba[i, 0]) & (np.minimum(e[:, 0], e[:, 2]) <= ba[i, 2])
                 & (np.maximum(e[:, 1], e[:, 3]) >= ba[i, 1]) & (np.minimum(e[:, 1], e[:, 3]) <= ba[i, 3]))
            eb.append(e[m] - np.r_[org, org])
            own.append(np.full(int(m.sum()), j))
        EB = np.concatenate(eb)
        owner = np.concatenate(own)
        shift = lambda f: [[np.asarray(r, float) - org for r in p] for p in f]  # noqa: E731
        res = _overlap_one(EA, EB, owner, shift(fa), {int(j): shift(polys_b[j]) for j in cand}, eps)
        for j, a in res.items():
            if a > min_area:
                rows.append((i, j, a))
    return pd.DataFrame(rows, columns=["i", "j", "area"])


# --------------------------------------------------------------------------------------------- nearest polygon
def nearest_polygon(px, py, polys: list) -> np.ndarray:
    """Index of the polygon nearest to each point (distance to its boundary; 0 inside), as geopandas.sjoin_nearest
    keeping the first match. Points with NaN coordinates get -1."""
    from scipy.spatial import cKDTree
    px, py = np.asarray(px, float), np.asarray(py, float)
    out = np.full(len(px), -1, np.int64)
    ok = np.isfinite(px) & np.isfinite(py)
    if not ok.any():
        return out
    inside = G.points_in_polygons(px, py, polys)
    out[ok & (inside >= 0)] = inside[ok & (inside >= 0)]
    todo = np.flatnonzero(ok & (inside < 0))
    if not len(todo):
        return out
    seg, own = G._segments(polys)
    ax, ay, bx, by = seg[:, 0], seg[:, 1], seg[:, 2], seg[:, 3]
    tree = cKDTree(np.c_[(ax + bx) / 2, (ay + by) / 2])
    half = float(np.hypot(bx - ax, by - ay).max()) / 2
    for j in todo:
        # the nearest segment midpoint bounds the answer: any closer segment has its midpoint within r0 + 2 * half
        r0, _ = tree.query([px[j], py[j]])
        cand = np.array(tree.query_ball_point([px[j], py[j]], r=r0 + 2 * half), dtype=np.int64)
        dx, dy = bx[cand] - ax[cand], by[cand] - ay[cand]
        L = dx * dx + dy * dy
        t = np.clip(((px[j] - ax[cand]) * dx + (py[j] - ay[cand]) * dy) / np.where(L > 0, L, 1), 0, 1)
        d = np.hypot(ax[cand] + t * dx - px[j], ay[cand] + t * dy - py[j])
        dmin = d.min()
        out[j] = int(own[cand[d <= dmin]].min())
    return out


# ------------------------------------------------------------------------------------------- WKB and files
def to_wkb(feature, kind: str) -> bytes:
    """ISO WKB, little-endian, 2D: kind 'Polygon' (one part) or 'MultiPolygon'."""
    def poly(part):
        b = [struct.pack("<BII", 1, 3, len(part))]
        for r in part:
            r = np.ascontiguousarray(r, dtype="<f8")
            b.append(struct.pack("<I", len(r)))
            b.append(r.tobytes())
        return b"".join(b)
    if kind == "Polygon":
        return poly(feature[0]) if feature else struct.pack("<BII", 1, 3, 0)
    return struct.pack("<BII", 1, 6, len(feature)) + b"".join(poly(p) for p in feature)


def from_wkb(b: bytes):
    """(feature, kind) from 2D little- or big-endian WKB Polygon / MultiPolygon."""
    def rd(fmt, pos, end):
        return struct.unpack_from(end + fmt, b, pos)

    def poly(pos):
        end = "<" if b[pos] == 1 else ">"
        (t,) = rd("I", pos + 1, end)
        (nr,) = rd("I", pos + 5, end)
        pos += 9
        rings = []
        for _ in range(nr):
            (n,) = rd("I", pos, end)
            pos += 4
            rings.append(np.frombuffer(b, dtype=end + "f8", count=2 * n, offset=pos).reshape(n, 2).astype(float))
            pos += 16 * n
        return rings, pos
    end = "<" if b[0] == 1 else ">"
    (t,) = rd("I", 1, end)
    if t == 3:
        rings, _ = poly(0)
        return ([rings] if rings else []), "Polygon"
    if t == 6:
        (n,) = rd("I", 5, end)
        pos, parts = 9, []
        for _ in range(n):
            rings, pos = poly(pos)
            parts.append(rings)
        return parts, "MultiPolygon"
    raise ValueError(f"WKB geometry type {t} not supported")


def _group_rings(rings: list) -> list:
    """Group a shapefile record's rings into polygon parts as GDAL does (clockwise rings are exteriors, in file
    order; each counter-clockwise ring is a hole of the exterior holding most of its vertices, the smallest such
    exterior on a tie), keeping holes in file order."""
    outers = [k for k, r in enumerate(rings) if _signed_area(np.vstack([r, r[:1]]) if not np.array_equal(r[0], r[-1]) else r) < 0]
    if not outers:
        return [[r] for r in rings]
    areas = {k: abs(_signed_area(rings[k])) for k in outers}
    groups = {k: [rings[k]] for k in outers}
    for k, r in enumerate(rings):
        if k in groups:
            continue
        best, best_n = outers[0], -1
        for o in outers:
            ext = rings[o]
            if (r[:, 0].min() < ext[:, 0].min() or r[:, 0].max() > ext[:, 0].max()
                    or r[:, 1].min() < ext[:, 1].min() or r[:, 1].max() > ext[:, 1].max()):
                continue
            n = int(G._point_in_ring_fast(r[:, 0], r[:, 1], ext).sum())
            if n > best_n or (n == best_n and areas[o] < areas[best]):
                best, best_n = o, n
        groups[best].append(r)
    return [groups[k] for k in outers]


def _shapefile_files(path, layer: str | None = None, exts=(".shp", ".dbf", ".prj", ".cpg")) -> dict:
    import zipfile
    path = Path(path)
    files = {}
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            stem = next((n[:-4] for n in names if n.lower().endswith((".shp", ".dbf"))
                         and (layer is None or Path(n).stem == layer)), None)
            if stem is None:
                raise FileNotFoundError(f"no layer {layer} in {path}")
            for ext in exts:
                nm = next((n for n in names if n.lower() == (stem + ext).lower()), None)
                if nm:
                    files[ext] = z.read(nm)
    else:
        stem = path.with_suffix("")
        for ext in exts:
            f = Path(str(stem) + ext)
            if f.exists():
                files[ext] = f.read_bytes()
    return files


def _dbf_encoding(files: dict) -> str:
    cpg = files.get(".cpg", b"").decode("ascii", "ignore").strip().lower()
    return "utf-8" if cpg in ("utf-8", "utf8", "65001") else "latin-1"


def read_attributes(path, layer: str | None = None) -> pd.DataFrame:
    """A shapefile's attribute table (folder, .shp/.dbf path or .zip), decoded as its .cpg file says (TIGER: UTF-8),
    without geometry (as pyogrio read_dataframe(read_geometry=False) / geopandas ignore_geometry=True)."""
    from missing_middleware.dbf import read_dbf_bytes
    files = _shapefile_files(path, layer, exts=(".dbf", ".cpg"))
    return read_dbf_bytes(files[".dbf"], encoding=_dbf_encoding(files))


def read_shapefile_polygons(path, layer: str | None = None) -> tuple[G.Layer, list[str]]:
    """A polygon shapefile (folder, .shp or .zip) as a geom.Layer, with holes grouped as GDAL groups them, and the
    geometry type GDAL reports for each record (MultiPolygon when a record has several exteriors)."""
    from missing_middleware.dbf import read_dbf_bytes
    files = _shapefile_files(path, layer)
    data = files[".shp"]
    pos, feats = 100, []
    while pos < len(data):
        _, clen = struct.unpack(">ii", data[pos:pos + 8])
        rec = data[pos + 8: pos + 8 + clen * 2]
        pos += 8 + clen * 2
        st = struct.unpack("<i", rec[:4])[0]
        if st == 0:
            feats.append([])
            continue
        if st not in (5, 15, 25):
            raise ValueError("read_shapefile_polygons reads polygon shapefiles only")
        nparts, npts = struct.unpack("<ii", rec[36:44])
        parts = list(struct.unpack(f"<{nparts}i", rec[44:44 + 4 * nparts])) + [npts]
        pts = np.frombuffer(rec[44 + 4 * nparts: 44 + 4 * nparts + 16 * npts], dtype="<f8").reshape(npts, 2)
        feats.append(_group_rings([pts[parts[i]:parts[i + 1]].astype(float) for i in range(nparts)]))
    attrs = (read_dbf_bytes(files[".dbf"], encoding=_dbf_encoding(files)) if ".dbf" in files
             else pd.DataFrame(index=range(len(feats))))
    proj = G.from_wkt(files[".prj"].decode("latin-1")) if ".prj" in files else G.crs(4269)
    return G.Layer(attrs.reset_index(drop=True), "polygon", None, None, feats, proj), polygon_kinds_from_shapefile(feats)


def polygon_kinds_from_shapefile(polys: list) -> list[str]:
    """Geometry type GDAL reports for shapefile polygon records: MultiPolygon when there are several outer rings."""
    return ["MultiPolygon" if len(f) > 1 else "Polygon" for f in polys]


def geojson_kinds(path) -> list[str]:
    obj = json.loads(Path(path).read_text())
    return [(f.get("geometry") or {}).get("type") for f in obj.get("features", [])]


_PROJJSON = {
    4269: {"$schema": "https://proj.org/schemas/v0.7/projjson.schema.json", "type": "GeographicCRS", "name": "NAD83",
           "datum": {"type": "GeodeticReferenceFrame", "name": "North American Datum 1983",
                     "ellipsoid": {"name": "GRS 1980", "semi_major_axis": 6378137, "inverse_flattening": 298.257222101}},
           "coordinate_system": {"subtype": "ellipsoidal", "axis": [
               {"name": "Geodetic latitude", "abbreviation": "Lat", "direction": "north", "unit": "degree"},
               {"name": "Geodetic longitude", "abbreviation": "Lon", "direction": "east", "unit": "degree"}]},
           "id": {"authority": "EPSG", "code": 4269}},
    4326: {"$schema": "https://proj.org/schemas/v0.7/projjson.schema.json", "type": "GeographicCRS", "name": "WGS 84",
           "datum_ensemble": {"name": "World Geodetic System 1984 ensemble", "members": [
               {"name": "World Geodetic System 1984 (Transit)"}, {"name": "World Geodetic System 1984 (G730)"},
               {"name": "World Geodetic System 1984 (G873)"}, {"name": "World Geodetic System 1984 (G1150)"},
               {"name": "World Geodetic System 1984 (G1674)"}, {"name": "World Geodetic System 1984 (G1762)"},
               {"name": "World Geodetic System 1984 (G2139)"}, {"name": "World Geodetic System 1984 (G2296)"}],
               "ellipsoid": {"name": "WGS 84", "semi_major_axis": 6378137, "inverse_flattening": 298.257223563},
               "accuracy": "2.0", "id": {"authority": "EPSG", "code": 6326}},
           "coordinate_system": {"subtype": "ellipsoidal", "axis": [
               {"name": "Geodetic latitude", "abbreviation": "Lat", "direction": "north", "unit": "degree"},
               {"name": "Geodetic longitude", "abbreviation": "Lon", "direction": "east", "unit": "degree"}]},
           "id": {"authority": "EPSG", "code": 4326}},
}


def write_geoparquet(attrs: pd.DataFrame, polys: list, kinds: list[str], path, epsg: int,
                     geometry_position: int | None = None) -> None:
    """GeoParquet 1.1 (WKB geometry column 'geometry') readable by geopandas.read_parquet and by read_geoparquet.
    geometry_position: where the geometry column goes among the attribute columns (default last)."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    df = pd.DataFrame(attrs).reset_index(drop=True).copy()
    pos = len(df.columns) if geometry_position is None else geometry_position
    df.insert(pos, "geometry", None)
    table = pa.Table.from_pandas(df, preserve_index=None)
    wkb = [to_wkb(f, k) for f, k in zip(polys, kinds)]
    crs = _PROJJSON[epsg]
    field = pa.field("geometry", pa.binary(), nullable=True, metadata={
        "ARROW:extension:name": "geoarrow.wkb", "ARROW:extension:metadata": json.dumps({"crs": crs})})
    table = table.set_column(pos, field, pa.array(wkb, type=pa.binary()))
    allx = [r[:, 0] for f in polys for p in f for r in p]
    ally = [r[:, 1] for f in polys for p in f for r in p]
    bbox = ([float(np.min([a.min() for a in allx])), float(np.min([a.min() for a in ally])),
             float(np.max([a.max() for a in allx])), float(np.max([a.max() for a in ally]))] if allx else [])
    geo = {"primary_column": "geometry", "columns": {"geometry": {
        "encoding": "WKB", "crs": crs, "geometry_types": sorted(set(kinds)), "bbox": bbox}},
        "version": "1.1.0", "creator": {"library": "missing_middleware.geom_extra_foundation", "version": "1"}}
    md = dict(table.schema.metadata or {})
    md[b"geo"] = json.dumps(geo).encode("utf-8")
    pq.write_table(table.replace_schema_metadata(md), path)


def read_geoparquet(path) -> tuple[pd.DataFrame, list, list[str], int | None]:
    """(attributes, polygon features, geometry types, EPSG code) from a GeoParquet file with WKB polygons."""
    import pyarrow.parquet as pq
    t = pq.read_table(path)
    geo = json.loads((t.schema.metadata or {}).get(b"geo", b"{}"))
    col = geo.get("primary_column", "geometry")
    crs = (geo.get("columns", {}).get(col, {}) or {}).get("crs") or {}
    epsg = (crs.get("id") or {}).get("code") if isinstance(crs, dict) else None
    wkb = t.column(col).to_pylist()
    feats, kinds = [], []
    for b in wkb:
        if b is None:
            feats.append([]); kinds.append(None)
            continue
        f, k = from_wkb(b)
        feats.append(f); kinds.append(k)
    attrs = t.drop([col]).to_pandas()
    return attrs, feats, kinds, (int(epsg) if epsg else 4326)


def _num(v) -> str:
    if isinstance(v, (bool, np.bool_)):
        return "true" if v else "false"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (float, np.floating)):
        return repr(float(v))
    return json.dumps(v, ensure_ascii=False)


def geometry_dict(feature, kind: str) -> dict:
    """GeoJSON geometry (as geopandas/shapely `__geo_interface__` gives it) for a polygon feature."""
    def ring(r):
        return [[float(x), float(y)] for x, y in r]
    if kind == "Polygon":
        return {"type": "Polygon", "coordinates": [ring(r) for r in (feature[0] if feature else [])]}
    return {"type": "MultiPolygon", "coordinates": [[ring(r) for r in p] for p in feature]}


def write_geojson_gdal(path, name: str, props: pd.DataFrame, polys: list, kinds: list[str]) -> None:
    """GeoJSON in the layout GDAL's GeoJSON driver writes (geopandas to_file(driver="GeoJSON") in WGS 84)."""
    def coords(obj):
        if isinstance(obj, (list, tuple)) and obj and isinstance(obj[0], (int, float)):
            return "[ " + ", ".join(repr(float(c)) for c in obj) + " ]"
        return "[ " + ", ".join(coords(o) for o in obj) + " ]"
    lines = ["{", '"type": "FeatureCollection",', f'"name": "{name}",',
             '"crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },', '"features": [']
    feats = []
    for k, (f, kind) in enumerate(zip(polys, kinds)):
        g = geometry_dict(f, kind)
        pr = ", ".join(f'"{c}": {_num(props.iloc[k][c])}' for c in props.columns)
        feats.append('{ "type": "Feature", "properties": { ' + pr + ' }, "geometry": { "type": "' + g["type"]
                     + '", "coordinates": ' + coords(g["coordinates"]) + " } }")
    lines.append(",\n".join(feats))
    lines += ["]", "}"]
    Path(path).write_text("\n".join(lines) + "\n")
