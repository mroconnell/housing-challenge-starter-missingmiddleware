"""Extra open-licence geometry for the TOD station-area chain (numpy, scipy and the standard library only).

missing_middleware/geom.py holds the shared readers, projections and operations. The station-area scripts
(scripts/build_tod_station_lot_table.py, scripts/station_cases/*, scripts/enrich_tod_station_lots.py,
scripts/build_tod_station_wisconsin.py and the run_tod_station_* scripts) also need a few things geom.py does not
have; they live here so geom.py stays untouched:

- interior_points: the point GEOS returns for `representative_point()` (InteriorPointArea, GEOS 3.8+): a horizontal
  scan line through the middle of each polygon's height, nudged off every vertex, and the middle of the widest
  stretch of that line inside the polygon; for a multi-part feature, the part with the widest stretch.
  geom.representative_points uses the centroid when it is inside, which is a different point; the lot tables were
  built with the GEOS point, so this port keeps it (checked against shapely on the real parcel files, see
  docs/GEOMETRY.md).
- merge_within: the "platforms within 150 m are one station" step (`buffer(75).union_all()`, one station per part,
  placed at the part's centroid, named after the nearest stop). GEOS draws a point buffer as a 64-sided polygon with
  a vertex at angle 0; the union of such polygons is computed exactly here (boundary pieces not covered by another
  polygon of the group, then Green's theorem for the centroid).
- nearest_lowest: nearest target point with ties broken by the lowest target position (geopandas.sjoin_nearest
  returns every tied target in tree order; the scripts keep the first, which is arbitrary).
- read_gdb: a reader for Esri File Geodatabase tables (.gdbtable/.gdbtablx; format as documented by the GDAL
  OpenFileGDB driver), from a folder or a zip, with an optional row filter on text fields; polygons decoded to the
  geom.py model.
- read_geoparquet_wkb: polygons from a GeoParquet file's WKB column (a cache written earlier with geopandas).
- outline_keys: a byte key per polygon feature, equal for identical outlines (stands in for grouping on WKB).
"""
from __future__ import annotations

import io
import json
import math
import re
import struct
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware import geom as G


# --------------------------------------------------------------------------------------- representative points
def _interior_point_part(part) -> tuple[float, float, float]:
    """GEOS InteriorPointPolygon for one polygon (exterior ring first, then holes): (x, y, width)."""
    shell = part[0]
    first = (float(shell[0, 0]), float(shell[0, 1]))
    ymin, ymax = float(shell[:, 1].min()), float(shell[:, 1].max())
    centre = (ymin + ymax) / 2.0
    lo, hi = ymin, ymax
    for r in part:
        ys = r[:, 1]
        below = ys[ys <= centre]
        if len(below):
            lo = max(lo, float(below.max()))
        above = ys[ys > centre]
        if len(above):
            hi = min(hi, float(above.min()))
    scan = (hi + lo) / 2.0
    cross = []
    for r in part:
        if not (r[:, 1].min() <= scan <= r[:, 1].max()):
            continue
        if not (r[0, 0] == r[-1, 0] and r[0, 1] == r[-1, 1]):
            r = np.vstack([r, r[:1]])
        x0, y0, x1, y1 = r[:-1, 0], r[:-1, 1], r[1:, 0], r[1:, 1]
        m = ~(((y0 > scan) & (y1 > scan)) | ((y0 < scan) & (y1 < scan)))     # touches the line
        m &= y0 != y1                                                        # not horizontal
        m &= ~((y0 == scan) & (y1 < scan))                                   # downward edge: start point not counted
        m &= ~((y1 == scan) & (y0 < scan))                                   # upward edge: end point not counted
        if not m.any():
            continue
        a, b, c, d = x0[m], y0[m], x1[m], y1[m]
        with np.errstate(divide="ignore", invalid="ignore"):
            slope = (d - b) / (c - a)
            xi = np.where(a == c, a, a + (scan - b) / slope)
        cross.extend(xi.tolist())
    if not cross:
        return first[0], first[1], 0.0
    cross.sort()
    best_w, px = 0.0, None
    for i in range(0, len(cross) - 1, 2):
        w = cross[i + 1] - cross[i]
        if w > best_w:
            best_w, px = w, (cross[i] + cross[i + 1]) / 2.0
    if px is None:
        return first[0], first[1], 0.0
    return px, scan, best_w


def interior_points(polys: list) -> tuple[np.ndarray, np.ndarray]:
    """GEOS `representative_point()` (InteriorPointArea) of each polygon feature; NaN for empty features."""
    xs = np.full(len(polys), np.nan)
    ys = np.full(len(polys), np.nan)
    for k, feat in enumerate(polys):
        best = -1.0
        for part in feat or []:
            if not len(part) or not len(part[0]):
                continue
            x, y, w = _interior_point_part(part)
            if w > best:
                best, xs[k], ys[k] = w, x, y
    return xs, ys


# --------------------------------------------------------------------------------------- areas (GEOS formula)
def _ring_area_geos(r: np.ndarray) -> float:
    """GEOS Area::ofRingSigned: shoelace with x taken relative to the first vertex (keeps precision for projected
    coordinates in the millions; geom.feature_area loses about 1e-6 of a small parcel's area to rounding)."""
    n = len(r)
    if n < 3:
        return 0.0
    x = r[:, 0] - r[0, 0]
    y = r[:, 1]
    return float(np.sum(x[1:n - 1] * (y[0:n - 2] - y[2:n]))) / 2.0


def areas(polys: list) -> np.ndarray:
    """Planar area of each polygon feature as GEOS computes it: |exterior| minus |holes|, per part."""
    out = np.zeros(len(polys))
    for k, f in enumerate(polys):
        a = 0.0
        for part in f or []:
            if not len(part):
                continue
            a += abs(_ring_area_geos(part[0])) - sum(abs(_ring_area_geos(h)) for h in part[1:])
        out[k] = a
    return out


# --------------------------------------------------------------------------------------- nearest with fixed ties
def nearest_lowest(px, py, tx, ty, max_distance: float | None = None, k: int = 16):
    """Nearest target for each point (index -1 and distance inf beyond max_distance). Exact ties go to the lowest
    target position. Points or targets without a location (NaN) never match, as geopandas skips empty geometry.
    Returns (index, distance)."""
    px, py = np.asarray(px, float), np.asarray(py, float)
    tx, ty = np.asarray(tx, float), np.asarray(ty, float)
    okp, okt = np.isfinite(px) & np.isfinite(py), np.isfinite(tx) & np.isfinite(ty)
    if not (okp.all() and okt.all()):
        ti = np.flatnonzero(okt)
        bi, bd = np.full(len(px), -1, dtype=np.int64), np.full(len(px), np.inf)
        if okp.any():
            b, d = nearest_lowest(px[okp], py[okp], tx[okt], ty[okt], max_distance, k)
            bi[okp] = np.where(b >= 0, ti[np.maximum(b, 0)], -1)
            bd[okp] = d
        return bi, bd
    from scipy.spatial import cKDTree
    n = len(px)
    if not len(tx) or not n:
        return np.full(n, -1, dtype=np.int64), np.full(n, np.inf)
    kk = int(min(k, len(tx)))
    ub = np.inf if max_distance is None else max_distance
    d, i = cKDTree(np.c_[tx, ty]).query(np.c_[px, py], k=kk, distance_upper_bound=ub)
    if kk == 1:
        d, i = d[:, None], i[:, None]
    i = np.where(np.isfinite(d), i, np.iinfo(np.int64).max)
    tie = d == d[:, :1]
    best = np.where(tie, i, np.iinfo(np.int64).max).min(axis=1)
    dist = d[:, 0]
    best = np.where(np.isfinite(dist), best, -1).astype(np.int64)
    # more than k tied targets: fall back to an exhaustive check for those points
    full = np.flatnonzero(tie.all(axis=1) & np.isfinite(dist) & (kk < len(tx)))
    if len(full):
        t = cKDTree(np.c_[tx, ty])
        for j in full:
            cand = t.query_ball_point([px[j], py[j]], dist[j] * (1 + 1e-12) + 1e-12)
            cd = np.hypot(tx[cand] - px[j], ty[cand] - py[j])
            best[j] = min(c for c, dd in zip(cand, cd) if dd == cd.min())
    return best, dist


# --------------------------------------------------------------------------------------- platforms -> stations
def _circle(cx: float, cy: float, r: float, n: int = 64) -> np.ndarray:
    """GEOS point buffer: n-gon with a vertex at angle 0, counter-clockwise, closed."""
    a = np.arange(n + 1) * (2 * math.pi / n)
    a[-1] = 0.0
    return np.c_[cx + r * np.cos(a), cy + r * np.sin(a)]


def _clip_interval(p, q, poly) -> tuple[float, float] | None:
    """Parameter interval of segment p->q strictly inside a convex counter-clockwise polygon (Cyrus-Beck)."""
    t0, t1 = 0.0, 1.0
    d = q - p
    for i in range(len(poly) - 1):
        a, b = poly[i], poly[i + 1]
        e = b - a
        # inside: cross(e, x - a) > 0
        num = e[0] * (p[1] - a[1]) - e[1] * (p[0] - a[0])
        den = e[0] * d[1] - e[1] * d[0]
        if den == 0:
            if num <= 0:
                return None
            continue
        t = -num / den
        if den > 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 >= t1:
            return None
    return t0, t1


def _union_centroid(polys: list[np.ndarray]) -> tuple[float, float]:
    """Centroid of the union of convex counter-clockwise polygons (closed rings), computed in coordinates relative
    to the first vertex (projected coordinates in the millions lose centimetres otherwise)."""
    o = polys[0][0].copy()
    polys = [P - o for P in polys]
    A = Cx = Cy = 0.0
    for k, P in enumerate(polys):
        others = [Q for j, Q in enumerate(polys) if j != k]
        for i in range(len(P) - 1):
            p, q = P[i], P[i + 1]
            iv = []
            for Q in others:
                c = _clip_interval(p, q, Q)
                if c is not None:
                    iv.append(c)
            iv.sort()
            keep, t = [], 0.0
            for a, b in iv:
                if a > t:
                    keep.append((t, a))
                t = max(t, b)
            if t < 1.0:
                keep.append((t, 1.0))
            for a, b in keep:
                x0, y0 = p + a * (q - p)
                x1, y1 = p + b * (q - p)
                cr = x0 * y1 - x1 * y0
                A += cr / 2.0
                Cx += (x0 + x1) * cr / 6.0
                Cy += (y0 + y1) * cr / 6.0
    return Cx / A + o[0], Cy / A + o[1]


def merge_within(x, y, r: float = 75.0) -> tuple[np.ndarray, np.ndarray, list[np.ndarray]]:
    """Stations from stop points: the parts of the union of 64-gon buffers of radius r (GEOS `buffer(r)`), each
    placed at the part's centroid. Returns (cx, cy, members): members[k] = positions of the stops in part k.
    Parts are ordered by centroid (y, then x); GEOS orders the parts of a union in its own way, so station numbers
    may differ from a run with shapely while the stations themselves are the same."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    from scipy.spatial import cKDTree
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    if n == 0:
        return np.zeros(0), np.zeros(0), []
    # two equal regular 64-gons (centrally symmetric) overlap when the offset between centres lies inside the
    # 64-gon of twice the radius
    big = _circle(0.0, 0.0, 2 * r)
    pairs = cKDTree(np.c_[x, y]).query_pairs(2 * r, output_type="ndarray")
    keep = []
    for a, b in pairs:
        dx, dy = x[b] - x[a], y[b] - y[a]
        if G.points_in_feature([dx], [dy], [[big]])[0]:
            keep.append((a, b))
    keep = np.array(keep, dtype=int).reshape(-1, 2)
    m = coo_matrix((np.ones(len(keep)), (keep[:, 0], keep[:, 1])), shape=(n, n))
    _, lab = connected_components(m, directed=False)
    groups = [np.flatnonzero(lab == g) for g in np.unique(lab)]
    cx, cy = [], []
    for g in groups:
        pts = np.unique(np.c_[x[g], y[g]], axis=0)        # identical stops give identical polygons
        c = _union_centroid([_circle(px, py, r) for px, py in pts])
        cx.append(c[0]); cy.append(c[1])
    cx, cy = np.array(cx), np.array(cy)
    order = np.lexsort((cx, cy))
    return cx[order], cy[order], [groups[i] for i in order]


def merge_stops(x, y, r: float = 75.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """merge_within plus the stop each station is named after (the nearest stop to the station point; ties go to
    the lowest position). Returns (cx, cy, stop position)."""
    cx, cy, _ = merge_within(x, y, r)
    i, _ = nearest_lowest(cx, cy, x, y)
    return cx, cy, i


# --------------------------------------------------------------------------------------- identical outlines
def outline_keys(polys: list) -> list:
    """A hashable key per polygon feature, equal exactly when the outlines are identical (same parts, rings and
    coordinates in the same order), as grouping on WKB does; None for empty features."""
    out = []
    for f in polys:
        if not f:
            out.append(None)
            continue
        parts = []
        for part in f:
            parts.append(b"P" + b"".join(b"R" + struct.pack("<i", len(r)) + np.ascontiguousarray(r, dtype="<f8").tobytes() for r in part))
        out.append(b"".join(parts))
    return out


# --------------------------------------------------------------------------------------- GeoParquet (WKB)
def _wkb_polygons(buf: bytes):
    """Polygon or MultiPolygon WKB -> list of parts (each a list of rings)."""
    def rd(pos):
        bo = "<" if buf[pos] == 1 else ">"
        t = struct.unpack(bo + "I", buf[pos + 1:pos + 5])[0]
        return bo, t & 0xFF if t < 1000 else t % 1000, pos + 5

    def poly(pos):
        bo, t, pos = rd(pos)
        nr = struct.unpack(bo + "I", buf[pos:pos + 4])[0]; pos += 4
        rings = []
        for _ in range(nr):
            npt = struct.unpack(bo + "I", buf[pos:pos + 4])[0]; pos += 4
            a = np.frombuffer(buf, dtype=bo + "f8", count=2 * npt, offset=pos).reshape(npt, 2).astype(float)
            pos += 16 * npt
            rings.append(a)
        return rings, pos
    bo, t, pos = rd(0)
    if t == 3:
        return [poly(0)[0]]
    if t == 6:
        n = struct.unpack(bo + "I", buf[pos:pos + 4])[0]; pos += 4
        out = []
        for _ in range(n):
            rings, pos = poly(pos)
            out.append(rings)
        return out
    raise ValueError(f"WKB type {t} not supported")


def read_geoparquet_wkb(path, columns: list[str] | None = None) -> G.Layer:
    """Polygons from a GeoParquet file (geometry column WKB) with its CRS from the 'geo' metadata."""
    import pyarrow.parquet as pq
    t = pq.read_table(path)
    meta = json.loads((t.schema.metadata or {}).get(b"geo", b"{}") or b"{}")
    gcol = meta.get("primary_column", "geometry")
    crs = meta.get("columns", {}).get(gcol, {}).get("crs")
    code = None
    if isinstance(crs, dict):
        code = (crs.get("id") or {}).get("code")
    df = t.drop([gcol]).to_pandas()
    if columns is not None:
        df = df[[c for c in columns if c in df.columns]]
    polys = [_wkb_polygons(b) if b is not None else [] for b in t.column(gcol).to_pylist()]
    return G.Layer(df.reset_index(drop=True), "polygon", None, None, polys, G.crs(code) if code else None)


# --------------------------------------------------------------------------------------- File Geodatabase
def _varuint(b: bytes, pos: int) -> tuple[int, int]:
    shift = ret = 0
    while True:
        c = b[pos]; pos += 1
        ret |= (c & 0x7F) << shift
        if not c & 0x80:
            return ret, pos
        shift += 7


def _varints(b: memoryview, pos: int, n: int) -> tuple[np.ndarray, int]:
    """n signed varints (Esri: first byte 6 value bits + sign bit 0x40) from pos, vectorised."""
    a = np.frombuffer(b, dtype=np.uint8, offset=pos, count=min(len(b) - pos, 10 * n + 16))
    ends = np.flatnonzero((a & 0x80) == 0)[:n]
    if len(ends) < n:
        raise ValueError("truncated varints")
    starts = np.r_[0, ends[:-1] + 1]
    last = int(ends[-1]) + 1
    a = a[:last].astype(np.int64)
    idx = np.arange(last)
    grp = np.repeat(np.arange(n), ends - starts + 1)
    k = idx - starts[grp]                                    # byte number within its varint
    first = k == 0
    val = np.where(first, a & 0x3F, a & 0x7F)
    shift = np.where(first, 0, 6 + 7 * (k - 1))
    out = np.zeros(n, dtype=np.int64)
    np.add.at(out, grp, val << shift)
    sign = np.where((a[starts] & 0x40) != 0, -1, 1)
    return out * sign, pos + last


class _GdbTable:
    def __init__(self, table: bytes, tablx: bytes):
        self.b = memoryview(table)
        self.raw = table
        h = struct.unpack("<iiii", tablx[:16])
        n1024, nrec, osz = h[1], h[2], h[3]
        offs = np.frombuffer(tablx, dtype=np.uint8, offset=16, count=n1024 * 1024 * osz).reshape(-1, osz)[:nrec]
        o = np.zeros(len(offs), dtype=np.int64)
        for i in range(osz):
            o |= offs[:, i].astype(np.int64) << (8 * i)
        self.offsets = o
        self.fields = []
        pos = struct.unpack("<Q", table[32:40])[0]
        _, version, flags, nf = struct.unpack("<iiiH", table[pos:pos + 14])
        pos += 14
        self.nullable = 0
        for _ in range(nf):
            nc = table[pos]; pos += 1
            name = table[pos:pos + 2 * nc].decode("utf-16-le"); pos += 2 * nc
            nc = table[pos]; pos += 1
            pos += 2 * nc                                   # alias
            ftype = table[pos]; pos += 1
            f = {"name": name, "type": ftype, "nullable": False}
            if ftype == 6:                                  # object id
                pos += 2
            elif ftype == 4:                                # string
                pos += 4
                fl = table[pos]; pos += 1
                f["nullable"] = bool(fl & 1)
                if fl & 4:
                    ln, pos = _varuint(table, pos); pos += ln
            elif ftype == 7:                                # geometry
                pos += 1
                fl = table[pos]; pos += 1
                f["nullable"] = bool(fl & 1)
                ln = struct.unpack("<H", table[pos:pos + 2])[0]; pos += 2
                f["wkt"] = table[pos:pos + ln].decode("utf-16-le"); pos += ln
                gf = table[pos]; pos += 1
                has_m, has_z = bool(gf & 2), bool(gf & 4)
                xo, yo, xys = struct.unpack("<ddd", table[pos:pos + 24]); pos += 24
                f.update(xorigin=xo, yorigin=yo, xyscale=xys, has_m=has_m, has_z=has_z)
                if has_m:
                    pos += 16
                if has_z:
                    pos += 16
                pos += 8                                    # xy tolerance
                if has_m:
                    pos += 8
                if has_z:
                    pos += 8
                pos += 32                                   # extent
                # then optional z/m ranges (doubles), a 0 byte and the spatial grid count (1 to 3), as GDAL reads it
                while not (table[pos] == 0 and 1 <= struct.unpack("<I", table[pos + 1:pos + 5])[0] <= 3):
                    pos += 8
                pos += 1
                ng = struct.unpack("<i", table[pos:pos + 4])[0]; pos += 4
                pos += 8 * ng
            elif ftype in (0, 1, 2, 3, 5, 10, 11, 12, 8):
                pos += 1
                fl = table[pos]; pos += 1
                f["nullable"] = bool(fl & 1)
                if fl & 4 and ftype in (0, 1, 2, 3, 5):
                    ln = table[pos]; pos += 1 + ln
            else:
                raise ValueError(f"File Geodatabase field type {ftype} not supported")
            if f["nullable"]:
                f["null_bit"] = self.nullable
                self.nullable += 1
            self.fields.append(f)
        self.nullbytes = (self.nullable + 7) // 8

    def geometry_field(self):
        return next((f for f in self.fields if f["type"] == 7), None)

    def rows(self, want: set[str], keep=None):
        """Yield (row number, {field: value}) for live rows; geometry as raw bytes (or None). keep(rowdict) filters
        once every wanted field is read."""
        b, raw = self.b, self.raw
        last = max((i for i, f in enumerate(self.fields) if f["name"] in want), default=-1)
        unpack_from = struct.unpack_from
        for rn, off in enumerate(self.offsets):
            if off <= 0:
                continue
            pos = int(off) + 4
            nb = b[pos:pos + self.nullbytes].tobytes(); pos += self.nullbytes
            row = {}
            for i, f in enumerate(self.fields):
                if i > last:
                    break
                t = f["type"]
                if t == 6:
                    continue
                if f["nullable"]:
                    bit = f["null_bit"]
                    if nb[bit >> 3] & (1 << (bit & 7)):
                        if f["name"] in want:
                            row[f["name"]] = None
                        continue
                if t == 4 or t == 12:
                    ln, pos = _varuint(raw, pos)
                    if f["name"] in want:
                        row[f["name"]] = raw[pos:pos + ln].decode("utf-8")
                    pos += ln
                elif t == 7 or t == 8:
                    ln, pos = _varuint(raw, pos)
                    if f["name"] in want:
                        row[f["name"]] = raw[pos:pos + ln]
                    pos += ln
                elif t == 3 or t == 5:
                    if f["name"] in want:
                        row[f["name"]] = unpack_from("<d", raw, pos)[0]
                    pos += 8
                elif t == 1:
                    if f["name"] in want:
                        row[f["name"]] = unpack_from("<i", raw, pos)[0]
                    pos += 4
                elif t == 0:
                    if f["name"] in want:
                        row[f["name"]] = unpack_from("<h", raw, pos)[0]
                    pos += 2
                elif t == 2:
                    if f["name"] in want:
                        row[f["name"]] = unpack_from("<f", raw, pos)[0]
                    pos += 4
                elif t in (10, 11):
                    pos += 16
            if keep is None or keep(row):
                yield rn, row

    def decode_polygon(self, blob: bytes) -> list:
        """Esri compressed shape buffer (polygon) -> parts (each a list of rings: exterior first, then holes)."""
        gf = self.geometry_field()
        mv = memoryview(blob)
        gtype, pos = _varuint(blob, 0)
        base = gtype & 0xFF
        if base == 0:
            return []
        general = base in (51, 50)
        has_curves = general and bool(gtype & 0x20000000)
        npts, pos = _varuint(blob, pos)
        if npts == 0:
            return []
        nparts, pos = _varuint(blob, pos)
        if has_curves:
            _, pos = _varuint(blob, pos)
        for _ in range(4):
            _, pos = _varuint(blob, pos)
        sizes = []
        for _ in range(nparts - 1):
            s, pos = _varuint(blob, pos)
            sizes.append(s)
        sizes.append(npts - sum(sizes))
        v, pos = _varints(mv, pos, 2 * npts)
        xy = np.cumsum(v.reshape(npts, 2), axis=0).astype(float)
        xy[:, 0] = xy[:, 0] / gf["xyscale"] + gf["xorigin"]
        xy[:, 1] = xy[:, 1] / gf["xyscale"] + gf["yorigin"]
        rings, s = [], 0
        for n in sizes:
            rings.append(xy[s:s + n])
            s += n
        # Esri: outer rings clockwise, holes counter-clockwise; a hole joins the outer ring that holds it
        outers, holes = [], []
        for r in rings:
            (outers if G._ring_area_signed(r) < 0 else holes).append(r)
        if not outers:
            outers, holes = holes, []
        grouped = [[o] for o in outers]
        for h in holes:
            k = next((i for i, o in enumerate(outers) if G._point_in_ring(np.array([h[0, 0]]), np.array([h[0, 1]]), o)[0]), 0)
            grouped[k].append(h)
        return grouped


def _gdb_files(path, name: str | None) -> tuple[bytes, bytes]:
    """(gdbtable, gdbtablx) bytes of the feature table (the largest a000000NN table, or the one whose name is given)."""
    path = str(path)
    if ".zip" in path.lower():
        zp, _, inner = path.partition(".zip")
        zp += ".zip"
        inner = inner.strip("/")
        z = zipfile.ZipFile(zp)
        names = [n for n in z.namelist() if n.startswith(inner) and n.endswith(".gdbtable")]
        big = max(names, key=lambda n: z.getinfo(n).file_size)
        return z.read(big), z.read(big[:-len(".gdbtable")] + ".gdbtablx")
    p = Path(path)
    tabs = sorted(p.glob("*.gdbtable"), key=lambda f: f.stat().st_size)
    big = tabs[-1]
    return big.read_bytes(), big.with_suffix(".gdbtablx").read_bytes()


def read_gdb_raw(path, columns: list[str], where: dict | None = None, contains: bytes | None = None):
    """Rows of a File Geodatabase feature table with the geometry left encoded: (attributes, blobs, decode, crs).
    decode(blob) -> polygon feature (list of parts). See read_gdb for the arguments."""
    table, tablx = _gdb_files(path, None)
    T = _GdbTable(table, tablx)
    gf = T.geometry_field()
    want = set(columns) | set(where or {})
    if gf is not None:
        want.add(gf["name"])
    cond = {k: (v if isinstance(v, (set, frozenset, list, tuple)) else {v}) for k, v in (where or {}).items()}

    def keep(row):
        return all(row.get(k) in v for k, v in cond.items())
    if contains is not None:
        hits, start = [], 0
        while True:
            i = table.find(contains, start)
            if i < 0:
                break
            hits.append(i)
            start = i + 1
        offs = np.sort(T.offsets[T.offsets > 0])
        live = np.unique(offs[np.searchsorted(offs, np.array(hits, dtype=np.int64), side="right") - 1]) if hits else np.zeros(0, np.int64)
        T.offsets = np.where(np.isin(T.offsets, live), T.offsets, 0)
    recs, geoms = [], []
    for _, row in T.rows(want, keep if cond else None):
        recs.append({c: row.get(c) for c in columns})
        geoms.append(row.get(gf["name"]) if gf is not None else None)
    df = pd.DataFrame(recs, columns=columns)
    crs = None
    if gf is not None:
        crs = G.from_wkt(gf["wkt"]) if "PROJCS" in gf["wkt"] else G.crs(4326)
    return df, geoms, (lambda b: T.decode_polygon(b) if b else []), crs


def read_gdb(path, columns: list[str], where: dict | None = None, geometry: bool = True,
             contains: bytes | None = None) -> G.Layer | pd.DataFrame:
    """Read the feature table (the largest table) of a File Geodatabase: a folder, or 'archive.zip/inner.gdb'.

    columns: attribute fields to return; where: {field: value or set of values} kept rows (equality); contains:
    optional byte string every kept row contains (a fast pre-filter on the raw row bytes; it must be implied by
    `where`). geometry=False returns a DataFrame; otherwise a geom.Layer of polygons in the table's CRS.
    Read speed: about 25 s for the 220,000 rows of the Smart Location Database v3 (pure Python row parsing)."""
    df, blobs, decode, crs = read_gdb_raw(path, columns, where, contains)
    if not geometry or crs is None:
        return df
    return G.Layer(df, "polygon", None, None, [decode(b) for b in blobs], crs)


# ---- added for the case modules
# The lot-model case modules (missing_middleware/tod/case_*.py, cases.py, traits.py) hold geometry in plain pandas
# frames: a polygon frame has a column "geometry" whose cells are geom.py polygon features (list of parts, each a list
# of rings) in the case's metre CRS; a point frame has columns "x" and "y". The helpers below read files into that
# shape and do the joins those modules need.

def _lcc_m(lat_0, lon_0, lat_1, lat_2, x_0, y_0, name):
    return G.Projection("lcc", {"lat_0": lat_0, "lon_0": lon_0, "lat_1": lat_1, "lat_2": lat_2, "x_0": x_0, "y_0": y_0}, name=name)


def _tm_m(lat_0, lon_0, k_0, x_0, y_0, name, ell=G.GRS80):
    return G.Projection("tmerc", {"lat_0": lat_0, "lon_0": lon_0, "k_0": k_0, "x_0": x_0, "y_0": y_0}, a=ell[0], f=ell[1], name=name)


# metre state planes and UTM zones of the case modules (EPSG parameters; tests/test_geom_extra_station.py checks
# them against PROJ values recorded before the geo stack was removed)
EXTRA_EPSG: dict[int, G.Projection] = {
    32148: _lcc_m(47, -120.833333333333, 48.7333333333333, 47.5, 500000, 0, "NAD83 / Washington North"),
    26971: _tm_m(36.6666666666667, -88.3333333333333, 0.999975, 300000, 0, "NAD83 / Illinois East"),
    32189: _tm_m(0, -76.5, 0.9999, 304800, 0, "NAD83 / MTM zone 9"),
    26945: _lcc_m(33.5, -118, 35.4666666666667, 34.0333333333333, 2000000, 500000, "NAD83 / California zone 5"),
    32610: _tm_m(0, -123, 0.9996, 500000, 0, "WGS 84 / UTM zone 10N", G.WGS84),
    32129: _lcc_m(39.3333333333333, -77.75, 40.9666666666667, 39.9333333333333, 600000, 0, "NAD83 / Pennsylvania South"),
    26949: _tm_m(31, -111.916666666667, 0.9999, 213360, 0, "NAD83 / Arizona Central"),
    32118: _lcc_m(40.1666666666667, -74, 41.0333333333333, 40.6666666666667, 300000, 0, "NAD83 / New York Long Island"),
    32119: _lcc_m(33.75, -79, 36.1666666666667, 34.3333333333333, 609601.22, 0, "NAD83 / North Carolina"),
}


def crs(code) -> G.Projection:
    """geom.crs plus the metre systems above."""
    if isinstance(code, G.Projection):
        return code
    if isinstance(code, (int, np.integer)) or (isinstance(code, str) and code.upper().replace("EPSG:", "").isdigit()):
        c = int(str(code).upper().replace("EPSG:", ""))
        if c in EXTRA_EPSG:
            return EXTRA_EPSG[c]
    return G.crs(code)


_PROJ_TO_METRE = {G.US_FT: 0.3048006096012192}   # PROJ's US survey foot factor (1200/3937 rounds differently)


def _same_but_unit(s: G.Projection, d: G.Projection) -> bool:
    if not (s.kind == d.kind and s.kind != "longlat" and s.a == d.a and s.f == d.f and set(s.p) == set(d.p)):
        return False
    sp, dp = dict(s.p), dict(d.p)
    if "lat_1" in sp and "lat_2" in sp:                 # standard parallels in either order
        a, b = sorted((sp.pop("lat_1"), sp.pop("lat_2"))), sorted((dp.pop("lat_1"), dp.pop("lat_2")))
        if abs(a[0] - b[0]) > 1e-9 or abs(a[1] - b[1]) > 1e-9:
            return False
    return all(abs(sp[k] - dp[k]) < 1e-6 for k in sp)


def transform(x, y, src, dst):
    """geom.transform with the extra systems; between two versions of one projection that differ only in unit (e.g.
    EPSG:2263 feet and EPSG:32118 metres) it scales, as PROJ's unitconvert step does (bit-identical results)."""
    s, d = crs(src), crs(dst)
    x, y = np.asarray(x, float), np.asarray(y, float)
    if s is d:
        return x.copy(), y.copy()
    if _same_but_unit(s, d):
        fs, fd = _PROJ_TO_METRE.get(s.unit, s.unit), _PROJ_TO_METRE.get(d.unit, d.unit)
        if fd == 1.0:
            return x * fs, y * fs
        return x * fs / fd, y * fs / fd
    lon, lat = s.inverse(x, y)
    return d.forward(lon, lat)


def bbox_to(bbox, src, dst) -> tuple[float, float, float, float]:
    """Bounds, in dst, of a box given in src (its four corners transformed, as geopandas does for a box)."""
    x = np.array([bbox[0], bbox[2], bbox[2], bbox[0]], float)
    y = np.array([bbox[1], bbox[1], bbox[3], bbox[3]], float)
    xx, yy = transform(x, y, src, dst)
    return float(xx.min()), float(yy.min()), float(xx.max()), float(yy.max())


def polys_to_crs(polys: list, src, dst) -> list:
    """Polygon (or line) features from src to dst, all vertices transformed in one call."""
    s, d = crs(src), crs(dst)
    if s is d:
        return polys
    arrs = [r for f in polys for part in (f or []) for r in (part if isinstance(part, list) else [part])]
    if not arrs:
        return polys
    allxy = np.concatenate(arrs)
    xx, yy = transform(allxy[:, 0], allxy[:, 1], s, d)
    T = np.c_[xx, yy]
    pos, out = 0, []
    for f in polys:
        parts = []
        for part in f or []:
            if isinstance(part, np.ndarray):        # line part
                parts.append(T[pos:pos + len(part)]); pos += len(part)
            else:
                rings = []
                for r in part:
                    rings.append(T[pos:pos + len(r)]); pos += len(r)
                parts.append(rings)
        out.append(parts)
    return out


def feature_bounds(polys: list) -> np.ndarray:
    """(n, 4) array of minx, miny, maxx, maxy per feature (NaN for empty features)."""
    out = np.full((len(polys), 4), np.nan)
    for k, f in enumerate(polys):
        if not f:
            continue
        rs = [r for p in f for r in (p if isinstance(p, list) else [p])]
        a = np.concatenate(rs) if rs else None
        if a is None or not len(a):
            continue
        out[k] = (a[:, 0].min(), a[:, 1].min(), a[:, 0].max(), a[:, 1].max())
    return out


def nonempty(polys) -> np.ndarray:
    return np.array([bool(f) and any(len(p) and len(p[0]) for p in f) for f in polys], bool)


# ------------------------------------------------------------------- WKB (full) and GeoPackage
def _wkb_read(buf: bytes, pos: int = 0):
    """One WKB geometry from pos -> (kind, value, new pos). kind: point (x, y), line (list of arrays), polygon (list of
    parts). ISO (1000/2000/3000) and EWKB (high-bit) Z/M flags are read and dropped."""
    bo = "<" if buf[pos] == 1 else ">"
    t = struct.unpack_from(bo + "I", buf, pos + 1)[0]
    pos += 5
    hz = bool(t & 0x80000000)
    hm = bool(t & 0x40000000)
    if t & 0x20000000:                                   # EWKB SRID
        pos += 4
    t &= 0x0FFFFFFF
    base = t % 1000
    dim = t // 1000
    if dim in (1, 2):
        hz, hm = (dim == 1) or hz, (dim == 2) or hm
    elif dim == 3:
        hz = hm = True
    nd = 2 + hz + hm

    def pts(p):
        n = struct.unpack_from(bo + "I", buf, p)[0]
        a = np.frombuffer(buf, dtype=bo + "f8", count=n * nd, offset=p + 4).reshape(n, nd)[:, :2].astype(float)
        return a, p + 4 + 8 * n * nd

    if base == 1:
        a = np.frombuffer(buf, dtype=bo + "f8", count=nd, offset=pos)
        return "point", (float(a[0]), float(a[1])), pos + 8 * nd
    if base == 2:
        a, pos = pts(pos)
        return "line", [a], pos
    if base == 3:
        nr = struct.unpack_from(bo + "I", buf, pos)[0]; pos += 4
        rings = []
        for _ in range(nr):
            a, pos = pts(pos)
            rings.append(a)
        return "polygon", [rings] if rings else [], pos
    if base in (4, 5, 6, 7):
        n = struct.unpack_from(bo + "I", buf, pos)[0]; pos += 4
        kinds, vals = [], []
        for _ in range(n):
            k, v, pos = _wkb_read(buf, pos)
            kinds.append(k); vals.append(v)
        if base == 4:
            return "multipoint", vals, pos
        if base == 5:
            return "line", [a for v in vals for a in v], pos
        return "polygon", [p for v in vals if isinstance(v, list) for p in v], pos
    raise ValueError(f"WKB type {t} not supported")


def wkb_feature(buf: bytes):
    k, v, _ = _wkb_read(buf, 0)
    if k == "multipoint":
        return "point", (v[0] if v else (np.nan, np.nan))
    return k, v


def _gpkg_geom(blob: bytes):
    """GeoPackage binary -> (kind, value, envelope or None)."""
    if blob is None or len(blob) < 8:
        return None, None, None
    flags = blob[3]
    bo = "<" if flags & 1 else ">"
    env_n = {0: 0, 1: 4, 2: 6, 3: 6, 4: 8}[(flags >> 1) & 7]
    env = struct.unpack_from(bo + f"{env_n}d", blob, 8) if env_n else None
    if flags & 0x10:
        return None, None, env
    k, v = wkb_feature(blob[8 + 8 * env_n:])
    return k, v, (env[0], env[2], env[1], env[3]) if env else None   # minx, miny, maxx, maxy


def read_gpkg(path, columns: list[str] | None = None, bbox=None) -> tuple[pd.DataFrame, list, str, G.Projection]:
    """The (single) feature table of a GeoPackage: (attributes, geometries, kind, CRS). bbox (file CRS) keeps
    features whose envelope intersects it (GDAL's bbox semantics)."""
    import sqlite3
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    t, gcol, srs = con.execute("select table_name, column_name, srs_id from gpkg_geometry_columns").fetchone()
    wkt = con.execute("select definition from gpkg_spatial_ref_sys where srs_id=?", (srs,)).fetchone()[0]
    cols = [r[1] for r in con.execute(f'pragma table_info("{t}")')]
    want = [c for c in (columns if columns is not None else cols) if c in cols and c != gcol]
    q = ", ".join(f'"{c}"' for c in want + [gcol])
    rows = con.execute(f'select {q} from "{t}"').fetchall()
    con.close()
    recs, geoms, kind = [], [], None
    for r in rows:
        k, v, env = _gpkg_geom(r[-1])
        if bbox is not None:
            if env is None and v is not None:
                b = feature_bounds([v])[0] if k == "polygon" else (v[0], v[1], v[0], v[1])
                env = tuple(b)
            if env is None or env[0] > bbox[2] or env[2] < bbox[0] or env[1] > bbox[3] or env[3] < bbox[1]:
                continue
        kind = kind or k
        recs.append(r[:-1])
        geoms.append(v)
    if srs in EXTRA_EPSG:
        p = EXTRA_EPSG[srs]
    elif srs in G.EPSG:
        p = G.EPSG[srs]
    else:
        p = G.from_wkt(wkt) if "PROJCS" in wkt else crs(4326)
    return pd.DataFrame(recs, columns=want), geoms, kind or "polygon", p


# ------------------------------------------------------------------- shapefile (fast, selected columns)
def _dbf_columns(data: bytes, columns: list[str] | None, encoding: str) -> pd.DataFrame:
    n_rec, header_len, rec_len = struct.unpack("<IHH", data[4:12])
    fields, pos, off = [], 32, 1
    while data[pos] != 0x0D:
        name = data[pos:pos + 11].split(b"\x00")[0].decode("ascii")
        ftype, flen, fdec = chr(data[pos + 11]), data[pos + 16], data[pos + 17]
        fields.append((name, ftype, off, flen, fdec))
        off += flen
        pos += 32
    raw = np.frombuffer(data, dtype=np.uint8, count=n_rec * rec_len, offset=header_len).reshape(n_rec, rec_len)
    live = raw[:, 0] != ord("*")
    out = {}
    for name, ftype, o, ln, dec in fields:
        if columns is not None and name not in columns and name.lower() not in {c.lower() for c in columns}:
            continue
        b = np.ascontiguousarray(raw[:, o:o + ln]).view(f"S{ln}").ravel()
        s = pd.Series(b).str.decode(encoding, errors="replace").str.strip()
        if ftype in ("N", "F"):
            v = pd.to_numeric(s.where(s != ""), errors="coerce")
            out[name] = v
        elif ftype == "D":
            out[name] = s.where(s != "")
        elif ftype == "L":
            out[name] = s.str.upper().map({"T": True, "Y": True, "F": False, "N": False})
        else:
            out[name] = s.where(s != "", None)      # GDAL reads blank text as null
    df = pd.DataFrame(out)
    return df[live].reset_index(drop=True), live


def _shp_record(rec: bytes):
    """One .shp record's content -> (kind, value)."""
    st = struct.unpack_from("<i", rec, 0)[0]
    if st == 0:
        return None, None
    if st in (1, 11, 21):
        x, y = struct.unpack_from("<dd", rec, 4)
        return "point", (x, y)
    nparts, npts = struct.unpack_from("<ii", rec, 36)
    parts = list(struct.unpack_from(f"<{nparts}i", rec, 44)) + [npts]
    pts = np.frombuffer(rec, dtype="<f8", count=2 * npts, offset=44 + 4 * nparts).reshape(npts, 2).astype(float)
    rings = [pts[parts[i]:parts[i + 1]] for i in range(nparts)]
    if st in (3, 13, 23):
        return "line", rings
    outers, holes = [], []
    for r in rings:
        (outers if G._ring_area_signed(r) < 0 else holes).append(r)
    if not outers:
        outers, holes = holes, []
    grouped = [[o] for o in outers]
    for h in holes:
        k = next((i for i, o in enumerate(outers) if G._point_in_ring(np.array([h[0, 0]]), np.array([h[0, 1]]), o)[0]), 0)
        grouped[k].append(h)
    return "polygon", grouped


def _shapefile_bytes(path: str) -> dict:
    """{'.shp': bytes, '.shx':, '.dbf':, '.prj':, '.cpg':} from 'zip://a.zip!inner.shp', 'a.zip' (one layer) or a .shp."""
    path = str(path)
    if path.startswith("zip://"):
        path = path[6:]
    zp, _, inner = path.partition("!")
    files = {}
    if zp.lower().endswith(".zip"):
        with zipfile.ZipFile(zp) as z:
            names = z.namelist()
            if inner:
                stem = inner[:-4] if inner.lower().endswith((".shp", ".dbf", ".shx")) else inner
            else:
                stem = next(n[:-4] for n in names if n.lower().endswith(".shp"))
            for ext in (".shp", ".shx", ".dbf", ".prj", ".cpg"):
                nm = next((n for n in names if n.lower() == (stem + ext).lower()), None)
                if nm:
                    files[ext] = z.read(nm)
    else:
        stem = zp[:-4] if zp.lower().endswith((".shp", ".dbf", ".shx")) else zp
        for ext in (".shp", ".shx", ".dbf", ".prj", ".cpg"):
            f = Path(stem + ext)
            if f.exists():
                files[ext] = f.read_bytes()
    return files


def shapefile_fields(path) -> list[str]:
    """Field names of a shapefile's .dbf (as pyogrio.read_info(path)['fields'])."""
    d = _shapefile_bytes(path)[".dbf"]
    out, pos = [], 32
    while d[pos] != 0x0D:
        out.append(d[pos:pos + 11].split(b"\x00")[0].decode("ascii"))
        pos += 32
    return out


def shapefile_crs(path) -> G.Projection:
    f = _shapefile_bytes(path)
    return G.from_wkt(f[".prj"].decode("latin-1")) if ".prj" in f else crs(4269)


def read_shapefile(path, columns: list[str] | None = None, bbox=None, geometry: bool = True):
    """(attributes, geometries, kind, CRS) of a shapefile; bbox (file CRS) keeps records whose bounds intersect it.
    Text is decoded with the .cpg encoding (UTF-8 when absent and the file looks like a recent Census/Esri export,
    else Latin-1); numbers become floats or integers as in GDAL."""
    f = _shapefile_bytes(path)
    enc = f[".cpg"].decode("ascii").strip() if ".cpg" in f else "latin-1"
    if enc.upper() in ("UTF-8", "UTF8", "65001"):
        enc = "utf-8"
    attrs, live = _dbf_columns(f[".dbf"], columns, enc) if ".dbf" in f else (pd.DataFrame(), None)
    p = G.from_wkt(f[".prj"].decode("latin-1")) if ".prj" in f else crs(4269)
    if not geometry:
        return attrs, None, None, p
    shp, shx = f[".shp"], f[".shx"]
    n = (len(shx) - 100) // 8
    idx = np.frombuffer(shx, dtype=">i4", count=2 * n, offset=100).reshape(n, 2).astype(np.int64)
    offs, lens = idx[:, 0] * 2 + 8, idx[:, 1] * 2
    keep = np.ones(n, bool) if live is None else live.copy()
    shape_type = struct.unpack_from("<i", shp, 32)[0]
    if bbox is not None:
        if shape_type in (1, 11, 21):
            xy = np.array([struct.unpack_from("<idd", shp, o)[1:] if lens[k] >= 20 else (np.nan, np.nan) for k, o in enumerate(offs)])
            bb = np.c_[xy, xy]
        else:
            bb = np.array([struct.unpack_from("<4d", shp, o + 4) if lens[k] >= 36 else (np.nan,) * 4 for k, o in enumerate(offs)])
        keep &= ~((bb[:, 0] > bbox[2]) | (bb[:, 2] < bbox[0]) | (bb[:, 1] > bbox[3]) | (bb[:, 3] < bbox[1]))
    rows = np.flatnonzero(keep)
    geoms, kind = [], None
    for k in rows:
        kk, v = _shp_record(shp[offs[k]:offs[k] + lens[k]])
        kind = kind or kk
        geoms.append(v)
    a_rows = np.cumsum(live)[rows] - 1 if live is not None else rows
    return attrs.iloc[a_rows].reset_index(drop=True), geoms, kind or "polygon", p


def read_vector(path, dst=None, columns: list[str] | None = None, bbox=None, geometry: bool = True) -> pd.DataFrame:
    """A vector file as a frame: attributes plus "geometry" (polygon or line features) or "x"/"y" (points), in dst
    (EPSG code or Projection; the file's CRS when None). GeoJSON, shapefile (folder, .shp, .zip or 'zip://a.zip!b.shp')
    and GeoPackage. bbox, given in dst (or the file CRS), keeps features whose bounds meet it, after reprojection of the
    box to the file CRS (the box's corners, as geopandas does). df.attrs: kind, crs."""
    s = str(path)
    low = s.lower()
    if low.endswith((".geojson", ".json")):
        L = G.read_geojson(s, columns=columns)
        attrs, kind, src = L.attrs, L.kind, L.crs
        geoms = list(zip(L.x, L.y)) if kind == "point" else L.polys
        if bbox is not None:
            fb = bbox if dst is None else bbox_to(bbox, dst, src)
            b = np.array([(x, y, x, y) for x, y in geoms]) if kind == "point" else feature_bounds(geoms)
            m = ~((b[:, 0] > fb[2]) | (b[:, 2] < fb[0]) | (b[:, 1] > fb[3]) | (b[:, 3] < fb[1]))
            attrs, geoms = attrs[m].reset_index(drop=True), [g for g, k in zip(geoms, m) if k]
    elif low.endswith(".gpkg"):
        fb = None
        if bbox is not None:
            import sqlite3
            con = sqlite3.connect(f"file:{s}?mode=ro", uri=True)
            srs = con.execute("select srs_id from gpkg_geometry_columns").fetchone()[0]
            con.close()
            fb = bbox if dst is None else bbox_to(bbox, dst, srs)
        attrs, geoms, kind, src = read_gpkg(s, columns, fb)
    else:
        fb = None
        if bbox is not None:
            fb = bbox if dst is None else bbox_to(bbox, dst, shapefile_crs(s))
        attrs, geoms, kind, src = read_shapefile(s, columns, fb, geometry)
        if not geometry:
            attrs.attrs.update(kind=None, crs=src)
            return attrs
    d = crs(dst) if dst is not None else src
    df = attrs.copy()
    if kind == "point":
        xy = np.array([g if g is not None else (np.nan, np.nan) for g in geoms], float).reshape(-1, 2)
        x, y = transform(xy[:, 0], xy[:, 1], src, d)
        df["x"], df["y"] = x, y
    else:
        df["geometry"] = polys_to_crs([g if g is not None else [] for g in geoms], src, d) if geoms else []
    df.attrs.update(kind=kind, crs=d)
    return df


# ------------------------------------------------------------------- joins
def point_poly_pairs(px, py, polys: list, union: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """Every (point, polygon) pair with the point inside the polygon: a spatial join 'within' that keeps all matches,
    sorted by point, then polygon. Point location as geom.points_in_feature: the even-odd rule over a feature's rings
    (GEOS's prepared-geometry locator, which sjoin uses), or union=True for membership of the union of its parts."""
    px, py = np.asarray(px, float), np.asarray(py, float)
    pi, gi = [], []
    if not len(px):
        return np.zeros(0, int), np.zeros(0, int)
    order = np.argsort(px, kind="stable")
    sx = px[order]
    for k, feat in enumerate(polys):
        if not feat:
            continue
        b = feature_bounds([feat])[0]
        if not np.isfinite(b[0]):
            continue
        lo, hi = np.searchsorted(sx, b[0], "left"), np.searchsorted(sx, b[2], "right")
        if lo >= hi:
            continue
        cand = order[lo:hi]
        cand = cand[(py[cand] >= b[1]) & (py[cand] <= b[3])]
        if not len(cand):
            continue
        hit = G.points_in_feature(px[cand], py[cand], feat, union=union)
        pi.append(cand[hit]); gi.append(np.full(int(hit.sum()), k))
    if not pi:
        return np.zeros(0, int), np.zeros(0, int)
    pi, gi = np.concatenate(pi), np.concatenate(gi)
    o = np.lexsort((gi, pi))
    return pi[o], gi[o]


def first_within(px, py, polys: list, union: bool = False) -> np.ndarray:
    """Position of the first polygon containing each point, or -1 (sjoin 'within', first match kept)."""
    out = np.full(len(px), -1, dtype=np.int64)
    pi, gi = point_poly_pairs(px, py, polys, union)
    if len(pi):
        first = np.r_[True, pi[1:] != pi[:-1]]
        out[pi[first]] = gi[first]
    return out


def _segments_of(polys: list):
    seg, own = [], []
    for k, f in enumerate(polys):
        for part in f or []:
            for r in (part if isinstance(part, list) else [part]):
                if len(r) < 2:
                    continue
                a, b = r[:-1], r[1:]
                if not (r[0, 0] == r[-1, 0] and r[0, 1] == r[-1, 1]) and isinstance(part, list):
                    a, b = r, np.roll(r, -1, axis=0)
                seg.append(np.c_[a, b]); own.append(np.full(len(a), k))
    if not seg:
        return np.zeros((0, 4)), np.zeros(0, int)
    return np.concatenate(seg), np.concatenate(own)


def nearest_polygon(px, py, polys: list, max_distance: float, inside_first: bool = True, union: bool = False):
    """Nearest polygon feature to each point within max_distance (0 inside; the first containing polygon wins), with
    the distance: (position or -1, distance or inf). Ties go to the lowest position."""
    from scipy.spatial import cKDTree
    px, py = np.asarray(px, float), np.asarray(py, float)
    idx = np.full(len(px), -1, dtype=np.int64)
    dist = np.full(len(px), np.inf)
    fb = feature_bounds(polys) if len(polys) else np.zeros((0, 4))
    if not len(fb) or not np.isfinite(fb).any():
        return idx, dist
    near_box = (px >= np.nanmin(fb[:, 0]) - max_distance) & (px <= np.nanmax(fb[:, 2]) + max_distance) & \
        (py >= np.nanmin(fb[:, 1]) - max_distance) & (py <= np.nanmax(fb[:, 3]) + max_distance)
    box = np.flatnonzero(near_box)
    if inside_first and len(box):
        idx[box] = first_within(px[box], py[box], polys, union)
        dist[idx >= 0] = 0.0
    seg, own = _segments_of(polys)
    todo = np.flatnonzero((idx < 0) & near_box)
    if not len(seg) or not len(todo):
        return idx, dist
    # split segments into short pieces (at most `step` long): the nearest piece midpoint is then within step / 2 of
    # the true nearest distance, which bounds a small exact search around each point
    L = np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1])
    step = min(max(max_distance, 1.0), 5.0)
    k = np.maximum(1, np.ceil(L / step).astype(int))
    rep = np.repeat(np.arange(len(seg)), k)
    t0 = np.concatenate([np.arange(n) / n for n in k])
    t1 = np.concatenate([np.arange(1, n + 1) / n for n in k])
    s = seg[rep]
    sub = np.c_[s[:, 0] + t0 * (s[:, 2] - s[:, 0]), s[:, 1] + t0 * (s[:, 3] - s[:, 1]),
                s[:, 0] + t1 * (s[:, 2] - s[:, 0]), s[:, 1] + t1 * (s[:, 3] - s[:, 1])]
    so = own[rep]
    half = np.hypot(sub[:, 2] - sub[:, 0], sub[:, 3] - sub[:, 1]).max() / 2
    tree = cKDTree((sub[:, :2] + sub[:, 2:]) / 2)
    dm, _ = tree.query(np.c_[px[todo], py[todo]], distance_upper_bound=max_distance + half + 1e-9)
    ok = np.isfinite(dm)
    todo, dm = todo[ok], dm[ok]
    for c0 in range(0, len(todo), 5000):
        tj = todo[c0:c0 + 5000]
        near = tree.query_ball_point(np.c_[px[tj], py[tj]], r=dm[c0:c0 + 5000] + 2 * half + 1e-9)
        lens = np.fromiter((len(c) for c in near), dtype=np.int64, count=len(near))
        if not lens.sum():
            continue
        cand = np.fromiter((i for c in near for i in c), dtype=np.int64, count=int(lens.sum()))
        who = np.repeat(np.arange(len(tj)), lens)
        q = sub[cand]
        x, y = px[tj][who], py[tj][who]
        ax, ay, bx, by = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
        dx, dy = bx - ax, by - ay
        LL = dx * dx + dy * dy
        t = np.clip(((x - ax) * dx + (y - ay) * dy) / np.where(LL > 0, LL, 1), 0, 1)
        d = np.hypot(ax + t * dx - x, ay + t * dy - y)
        o = np.lexsort((so[cand], d, who))            # per point: nearest first, ties to the lowest polygon
        first = np.r_[True, who[o][1:] != who[o][:-1]]
        w, dd, oo = who[o][first], d[o][first], so[cand][o][first]
        ok = dd <= max_distance
        dist[tj[w[ok]]] = dd[ok]
        idx[tj[w[ok]]] = oo[ok]
    return idx, dist


def distance_within(px, py, polys: list, max_distance: float) -> np.ndarray:
    """Distance from each point to the union of the polygons (0 inside), inf beyond max_distance."""
    return nearest_polygon(px, py, polys, max_distance, union=True)[1]


def within_point_buffers(px, py, sx, sy, r: float) -> np.ndarray:
    """True where a point lies inside the union of GEOS point buffers of radius r (64-gons with a vertex at angle 0)
    around (sx, sy): the exact polygon test, not the circle."""
    from scipy.spatial import cKDTree
    px, py = np.asarray(px, float), np.asarray(py, float)
    out = np.zeros(len(px), bool)
    if not len(sx) or not len(px):
        return out
    hits = cKDTree(np.c_[sx, sy]).query_ball_point(np.c_[px, py], r)
    sx, sy = np.asarray(sx, float), np.asarray(sy, float)
    step = 2 * math.pi / 64
    for i, h in enumerate(hits):
        for s in h:
            dx, dy = px[i] - sx[s], py[i] - sy[s]
            a = math.atan2(dy, dx) % (2 * math.pi)
            k = math.floor(a / step)
            mid = (k + 0.5) * step
            if dx * math.cos(mid) + dy * math.sin(mid) <= r * math.cos(step / 2):
                out[i] = True
                break
    return out


def convex_hull_feature(polys: list):
    """Convex hull of all vertices of the features, as a polygon feature."""
    from scipy.spatial import ConvexHull
    pts = np.concatenate([r for f in polys if f for p in f for r in (p if isinstance(p, list) else [p])])
    h = ConvexHull(pts)
    ring = pts[h.vertices]
    return [[np.vstack([ring, ring[:1]])]]


def centroids_geos(polys: list) -> tuple[np.ndarray, np.ndarray]:
    """Area-weighted centroid of each polygon feature, computed relative to its first vertex (as GEOS does, keeping
    precision for large projected coordinates)."""
    xs, ys = np.full(len(polys), np.nan), np.full(len(polys), np.nan)
    for k, f in enumerate(polys):
        if not f or not len(f[0]):
            continue
        o = f[0][0][0]
        A = cx = cy = 0.0
        for part in f:
            for i, r in enumerate(part):
                x, y = r[:, 0] - o[0], r[:, 1] - o[1]
                x1, y1 = np.roll(x, -1), np.roll(y, -1)
                cr = x * y1 - x1 * y
                a = 0.5 * cr.sum()
                if a == 0:
                    continue
                sgn = 1.0 if i == 0 else -1.0
                w = sgn * abs(a)
                cx += w * ((x + x1) * cr).sum() / (6 * a)
                cy += w * ((y + y1) * cr).sum() / (6 * a)
                A += w
        if A:
            xs[k], ys[k] = cx / A + o[0], cy / A + o[1]
    return xs, ys


def point_feature_distances(px, py, feats: list) -> np.ndarray:
    """Distance from point i to feature i (0 inside; NaN for an empty feature): GeoSeries.distance(other, align=True)."""
    out = np.full(len(px), np.nan)
    for i, (x, y, f) in enumerate(zip(px, py, feats)):
        if not f or not np.isfinite(x):
            continue
        if G.points_in_feature([x], [y], f)[0]:
            out[i] = 0.0
            continue
        seg, _ = _segments_of([f])
        ax, ay, bx, by = seg[:, 0], seg[:, 1], seg[:, 2], seg[:, 3]
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        t = np.clip(((x - ax) * dx + (y - ay) * dy) / np.where(L > 0, L, 1), 0, 1)
        out[i] = float(np.hypot(ax + t * dx - x, ay + t * dy - y).min())
    return out


def _geod_to_cart(lon, lat, ell):
    a, f = ell
    e2 = f * (2 - f)
    lam, phi = np.radians(lon), np.radians(lat)
    N = a / np.sqrt(1 - e2 * np.sin(phi) ** 2)
    return N * np.cos(phi) * np.cos(lam), N * np.cos(phi) * np.sin(lam), N * (1 - e2) * np.sin(phi)


def _cart_to_geod(X, Y, Z, ell):
    a, f = ell
    e2 = f * (2 - f)
    lam = np.arctan2(Y, X)
    p = np.hypot(X, Y)
    phi = np.arctan2(Z, p * (1 - e2))
    for _ in range(8):
        N = a / np.sqrt(1 - e2 * np.sin(phi) ** 2)
        h = p / np.cos(phi) - N
        phi = np.arctan2(Z, p * (1 - e2 * N / (N + h)))
    return np.degrees(lam), np.degrees(phi)


# EPSG:1946 "NAD83(CSRS) to WGS 84 (2)" (position vector given as coordinate frame in PROJ), the transformation PROJ
# picks for WGS 84 -> NAD83(CSRS) / MTM zone 10 (EPSG:2952) in Toronto: about 1 m
CSRS_WGS84_2 = dict(tx=-0.991, ty=1.9072, tz=0.5129, rx=-0.0257899075194932, ry=-0.0096500989602704, rz=-0.0116599432323421, s=0.0)


def wgs84_to_csrs(lon, lat, h=CSRS_WGS84_2) -> tuple[np.ndarray, np.ndarray]:
    """Longitude/latitude on WGS 84 -> NAD83(CSRS), by the inverse of the coordinate-frame Helmert above (as PROJ's
    pipeline does), so data published in WGS 84 line up with NAD83(CSRS) layers as they did with pyproj."""
    lon, lat = np.asarray(lon, float), np.asarray(lat, float)
    X, Y, Z = _geod_to_cart(lon, lat, G.WGS84)
    X, Y, Z = X - h["tx"], Y - h["ty"], Z - h["tz"]
    sec = math.pi / (180 * 3600)
    rx, ry, rz = h["rx"] * sec, h["ry"] * sec, h["rz"] * sec
    m = 1 + h["s"] * 1e-6
    # coordinate frame: R = [[1, rz, -ry], [-rz, 1, rx], [ry, -rx, 1]]; inverse = R^T / m
    Xo = (X - rz * Y + ry * Z) / m
    Yo = (rz * X + Y - rx * Z) / m
    Zo = (-ry * X + rx * Y + Z) / m
    return _cart_to_geod(Xo, Yo, Zo, G.GRS80)


def polys_wgs84_to(polys: list, dst, datum_fn) -> list:
    """Polygon features in WGS 84 lon/lat -> dst, through a datum function on lon/lat (e.g. wgs84_to_csrs)."""
    d = crs(dst)
    out = []
    for f in polys:
        parts = []
        for part in f or []:
            rings = []
            for r in part:
                lo, la = datum_fn(r[:, 0], r[:, 1])
                xx, yy = d.forward(lo, la)
                rings.append(np.c_[xx, yy])
            parts.append(rings)
        out.append(parts)
    return out


def make_valid_nested(polys: list) -> list:
    """Stand-in for GEOS make_valid on polygon features whose rings do not cross: every ring of a feature is placed by
    how many other rings of the feature contain it (even depth: an outer ring, odd: a hole of the smallest ring
    around it). This is GEOS's result for nested shells (a shell inside another becomes a hole), holes listed as
    shells and overlapping parts' interiors as the even-odd rule sees them. Rings that cross themselves or each other
    are not repaired (none in the case layers checked). Valid features come back unchanged in shape."""
    out = []
    for f in polys:
        rings = [r for part in (f or []) for r in part if len(r) >= 4]
        if len(rings) <= 1:
            out.append(f)
            continue
        shell_of, k = [], 0
        for part in f:
            s0 = None
            for h, r in enumerate(part):
                if len(r) < 4:
                    continue
                if h == 0:
                    s0 = k
                shell_of.append(s0 if h > 0 else -1)
                k += 1
        ar = np.array([abs(_ring_area_geos(r)) for r in rings])
        depth = np.zeros(len(rings), int)
        parent = np.full(len(rings), -1)
        for i, r in enumerate(rings):
            best = None
            for j, o in enumerate(rings):
                if i == j or ar[j] <= ar[i]:
                    continue
                if G._point_in_ring(np.array([r[0, 0]]), np.array([r[0, 1]]), o)[0] or \
                        G._point_in_ring(np.array([r[len(r) // 2, 0]]), np.array([r[len(r) // 2, 1]]), o)[0]:
                    depth[i] += 1
                    if best is None or ar[j] < ar[best]:
                        best = j
            parent[i] = -1 if best is None else best
        ok = all((depth[i] % 2 == 0) if shell_of[i] < 0 else (depth[i] % 2 == 1 and parent[i] == shell_of[i]) for i in range(len(rings)))
        if ok:
            out.append(f)
            continue
        parts, where = [], {}
        for i in np.argsort(-ar, kind="stable"):
            if depth[i] % 2 == 0:
                where[i] = len(parts)
                parts.append([rings[i]])
        for i in range(len(rings)):
            if depth[i] % 2 == 1 and parent[i] in where:
                parts[where[parent[i]]].append(rings[i])
        out.append(parts)
    return out


def within_buffer_geos(px, py, polys: list, r: float, quad_segs: int = 16, simplify: bool = False) -> np.ndarray:
    """`point.within(union_all(polys).buffer(r))` as GEOS draws the buffer: straight edges offset exactly, and round
    corners drawn as chords (each outside corner's arc split into round(angle / (pi / 2 / quad_segs)) equal steps).
    Points nearer than the shortest possible chord are inside at once; for the rest the corner is found among the
    polygon edges that meet at the nearest vertex (the outside wedge around the point's direction). GEOS also
    smooths shallow concave bends of the union's rings before buffering (BufferInputLineSimplifier); simplify=True
    applies that ring by ring to the given polygons instead of their union, which is not the same, so it is off by
    default. Checked against shapely on St. Paul, Charlotte and Seattle parcel clusters: 0 to 2 points differ per
    cluster of about 1,000, all within half a metre of the buffer edge."""
    from scipy.spatial import cKDTree
    px, py = np.asarray(px, float), np.asarray(py, float)
    out = np.zeros(len(px), bool)
    if not polys or not len(px):
        return out
    q = math.pi / 2 / quad_segs
    idx, dist = nearest_polygon(px, py, polys, r, union=True)
    polys = buffer_input_polys(polys, r) if simplify else polys
    sure = dist <= r * math.cos(0.75 * q) - 1e-9
    out[sure] = True
    band = np.flatnonzero((dist <= r) & ~sure)
    if not len(band):
        return out
    seg, _ = _segments_of(polys)
    mid = (seg[:, :2] + seg[:, 2:]) / 2
    half = np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1]).max() / 2
    tree = cKDTree(mid)
    # edges by endpoint, to find every edge meeting at a vertex
    ends = np.r_[seg[:, :2], seg[:, 2:]]
    other = np.r_[seg[:, 2:], seg[:, :2]]
    etree = cKDTree(ends)
    for j in band:
        x, y = px[j], py[j]
        cand = np.asarray(tree.query_ball_point([x, y], r + half + 1e-9))
        s = seg[cand]
        ax, ay, bx, by = s[:, 0], s[:, 1], s[:, 2], s[:, 3]
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        t = ((x - ax) * dx + (y - ay) * dy) / np.where(L > 0, L, 1)
        tc = np.clip(t, 0, 1)
        d = np.hypot(ax + tc * dx - x, ay + tc * dy - y)
        if np.any((t > 0) & (t < 1) & (d <= r)):
            out[j] = True
            continue
        # vertices within r: chord test of the corner's fillet
        verts = np.unique(np.r_[s[:, :2], s[:, 2:]][np.r_[np.hypot(ax - x, ay - y), np.hypot(bx - x, by - y)] <= r], axis=0)
        for vx, vy in verts:
            k = etree.query_ball_point([vx, vy], 1e-9)
            th = np.unique(np.arctan2(other[k, 1] - vy, other[k, 0] - vx))
            phi = math.atan2(y - vy, x - vx)
            if len(th) < 2:
                continue
            rel = np.sort((th - phi) % (2 * math.pi))
            hi = phi + rel[0]                    # next edge counter-clockwise from the point's direction
            lo = phi + rel[-1] - 2 * math.pi     # previous edge (clockwise)
            wedge = hi - lo
            if wedge <= math.pi:                 # a concave corner: no fillet, the point is not in its sector
                continue
            a0, a1 = lo + math.pi / 2, hi - math.pi / 2          # the two edge normals bounding the arc
            total = a1 - a0
            n = int(total / q + 0.5)
            n = max(n, 1)
            inc = total / n
            kk = min(int((phi - a0) // inc), n - 1) if phi >= a0 else 0
            m = a0 + (kk + 0.5) * inc
            if (x - vx) * math.cos(m) + (y - vy) * math.sin(m) <= r * math.cos(inc / 2) + 1e-9:
                out[j] = True
                break
    return out


def _orient(p0, p1, p2) -> int:
    v = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0])
    return 1 if v > 0 else (-1 if v < 0 else 0)


def _pt_seg(p, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    if L == 0:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.hypot(a[0] + t * dx - p[0], a[1] + t * dy - p[1])


def simplify_buffer_input(ring: np.ndarray, tol: float) -> np.ndarray:
    """GEOS/JTS BufferInputLineSimplifier: drop vertices that make shallow concavities (seen from the buffer side)
    before a ring is offset. tol > 0 for the left side, < 0 for the right (as GEOS passes it)."""
    c = [tuple(p) for p in ring]
    n = len(c)
    dist = abs(tol)
    ao = -1 if tol < 0 else 1
    deleted = [False] * n

    def nxt(i):
        i += 1
        while i < n and deleted[i]:
            i += 1
        return i

    def shallow_sampled(p0, p2, i0, i2):
        inc = (i2 - i0) // 10
        if inc <= 0:
            inc = 1
        i = i0
        while i < i2:
            if not _pt_seg(p2, p0, c[i]) < dist:
                return False
            i += inc
        return True

    changed = True
    while changed:
        changed = False
        i, m = 1, nxt(1)
        last = nxt(m)
        while last < n:
            p0, p1, p2 = c[i], c[m], c[last]
            gone = False
            if _orient(p0, p1, p2) == ao and _pt_seg(p1, p0, p2) < dist and shallow_sampled(p0, p1, i, last):
                deleted[m] = True
                gone = changed = True
            i = last if gone else m
            m = nxt(i)
            last = nxt(m)
    return np.array([p for p, d in zip(c, deleted) if not d], float)


def buffer_input_polys(polys: list, r: float, factor: float = 0.01) -> list:
    """Each ring simplified as GEOS does before buffering by r > 0 (tolerance r * factor; shells and holes on the side
    the buffer grows). Applied ring by ring to the given features (GEOS applies it to their union's rings)."""
    tol = r * factor
    out = []
    for f in polys:
        parts = []
        for part in f or []:
            rings = []
            for h, ring in enumerate(part):
                if len(ring) < 4:
                    rings.append(ring)
                    continue
                keep = np.r_[True, np.any(np.diff(ring, axis=0) != 0, axis=1)]
                ring = ring[keep]                                   # repeated points removed first
                ccw = _ring_area_geos(ring) > 0
                side_left = (h == 0) != ccw                         # shell: LEFT, flipped if CCW; hole: RIGHT, flipped if CCW
                rings.append(simplify_buffer_input(ring, -tol if side_left else tol))
            parts.append(rings)
        out.append(parts)
    return out


# --------------------------------------------------------------------------------------- point-buffer join (pairs)
def point_buffer_pairs(px, py, sx, sy, r: float) -> tuple[np.ndarray, np.ndarray]:
    """Every (point, centre) pair with the point inside the GEOS point buffer of radius r (64-gon, vertex at angle 0)
    around the centre: sjoin(points, buffers, predicate='within'), all matches, sorted by point then centre. The
    polygon test is the one within_point_buffers uses."""
    from scipy.spatial import cKDTree
    px, py = np.asarray(px, float), np.asarray(py, float)
    sx, sy = np.asarray(sx, float), np.asarray(sy, float)
    pi, si = [], []
    if not len(sx) or not len(px):
        return np.zeros(0, int), np.zeros(0, int)
    ok = np.isfinite(px) & np.isfinite(py)
    step = 2 * math.pi / 64
    apothem = r * math.cos(step / 2)
    tree = cKDTree(np.c_[sx, sy])
    for i in np.flatnonzero(ok):
        for s in sorted(tree.query_ball_point([px[i], py[i]], r)):
            dx, dy = px[i] - sx[s], py[i] - sy[s]
            a = math.atan2(dy, dx) % (2 * math.pi)
            mid = (math.floor(a / step) + 0.5) * step
            if dx * math.cos(mid) + dy * math.sin(mid) <= apothem:
                pi.append(i); si.append(s)
    return np.asarray(pi, int), np.asarray(si, int)
