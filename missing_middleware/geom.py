"""Open-licence geometry for the build scripts: readers, map projections and the few spatial operations we use.

The contest accepts permissively licensed dependencies only (Official Rules 7(b)). The usual Python geo stack does not
qualify: shapely's wheels bundle GEOS (LGPL-2.1), and pyproj and pyogrio require certifi (MPL-2.0). This module needs
only numpy, scipy (both BSD-3-Clause) and the standard library.

Geometry model (kept deliberately small):
  - points: two float arrays x, y;
  - polygons: a list with one entry per feature; each entry is a list of parts; each part is a list of rings, the
    exterior ring first, then holes; each ring an (n, 2) float array (closed or not).
Coordinates are longitude/latitude (degrees) or projected x/y in metres, depending on the CRS.

Projections implemented from the published formulas (Snyder 1987, "Map Projections — A Working Manual", USGS PP 1395;
Krüger series for transverse Mercator per Karney 2011): Albers equal-area conic, Lambert conformal conic (one and two
standard parallels), transverse Mercator (including UTM), Mercator (ellipsoidal and the spherical web Mercator).
Datums: NAD83, NAD83(HARN), NAD83(CSRS) and WGS84 are treated as the same (they differ by about a metre or two in the
contiguous US); NAD27 is refused rather than silently shifted. tests/test_geom.py checks every CRS against values
recorded from PROJ before the geo stack was removed (tests/fixtures/geom_projections.json).
"""
from __future__ import annotations

import io
import json
import math
import re
import struct
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------------------------------- ellipsoids
GRS80 = (6378137.0, 1 / 298.257222101)
WGS84 = (6378137.0, 1 / 298.257223563)
US_FT = 1200 / 3937          # US survey foot in metres
INTL_FT = 0.3048


@dataclass
class Projection:
    """A projected or geographic CRS. kind: longlat, aea, lcc, tmerc, merc, webmerc."""
    kind: str
    p: dict = field(default_factory=dict)
    a: float = GRS80[0]
    f: float = GRS80[1]
    unit: float = 1.0            # metres per CRS unit
    name: str = ""

    @property
    def e(self) -> float:
        return math.sqrt(self.f * (2 - self.f))

    # ---- forward: lon/lat degrees -> x/y in CRS units
    def forward(self, lon, lat):
        lon, lat = np.asarray(lon, float), np.asarray(lat, float)
        if self.kind == "longlat":
            return lon.copy(), lat.copy()
        x, y = getattr(self, f"_fwd_{self.kind}")(np.radians(lon), np.radians(lat))
        return (x + self.p.get("x_0", 0.0)) / self.unit, (y + self.p.get("y_0", 0.0)) / self.unit

    def inverse(self, x, y):
        x, y = np.asarray(x, float) * self.unit, np.asarray(y, float) * self.unit
        if self.kind == "longlat":
            return x / self.unit, y / self.unit
        lam, phi = getattr(self, f"_inv_{self.kind}")(x - self.p.get("x_0", 0.0), y - self.p.get("y_0", 0.0))
        return np.degrees(lam), np.degrees(phi)

    # ---- helpers
    def _m(self, phi):
        e = self.e
        return np.cos(phi) / np.sqrt(1 - e * e * np.sin(phi) ** 2)

    def _q(self, phi):
        e = self.e
        s = np.sin(phi)
        return (1 - e * e) * (s / (1 - e * e * s * s) - 1 / (2 * e) * np.log((1 - e * s) / (1 + e * s)))

    def _t(self, phi):
        e = self.e
        s = np.sin(phi)
        return np.tan(np.pi / 4 - phi / 2) / ((1 - e * s) / (1 + e * s)) ** (e / 2)

    # ---- Albers equal-area conic (Snyder 14)
    def _aea_consts(self):
        p, e = self.p, self.e
        p1, p2, p0 = (math.radians(p[k]) for k in ("lat_1", "lat_2", "lat_0"))
        m1, m2 = self._m(p1), self._m(p2)
        q1, q2, q0 = self._q(p1), self._q(p2), self._q(p0)
        n = (m1 * m1 - m2 * m2) / (q2 - q1) if abs(p1 - p2) > 1e-12 else math.sin(p1)
        C = m1 * m1 + n * q1
        rho0 = self.a * math.sqrt(C - n * q0) / n
        return n, C, rho0, math.radians(p["lon_0"])

    def _fwd_aea(self, lam, phi):
        n, C, rho0, lam0 = self._aea_consts()
        rho = self.a * np.sqrt(C - n * self._q(phi)) / n
        th = n * (lam - lam0)
        return rho * np.sin(th), rho0 - rho * np.cos(th)

    def _inv_aea(self, x, y):
        n, C, rho0, lam0 = self._aea_consts()
        e = self.e
        rho = np.hypot(x, rho0 - y)
        th = np.arctan2(x * np.sign(n), (rho0 - y) * np.sign(n))
        q = (C - (rho * n / self.a) ** 2) / n
        phi = np.arcsin(np.clip(q / 2, -1, 1))
        for _ in range(15):
            s = np.sin(phi)
            phi = phi + (1 - e * e * s * s) ** 2 / (2 * np.cos(phi)) * (
                q / (1 - e * e) - s / (1 - e * e * s * s) + 1 / (2 * e) * np.log((1 - e * s) / (1 + e * s)))
        return lam0 + th / n, phi

    # ---- Lambert conformal conic (Snyder 15)
    def _lcc_consts(self):
        p = self.p
        p0 = math.radians(p["lat_0"])
        if "lat_2" in p:
            p1, p2 = math.radians(p["lat_1"]), math.radians(p["lat_2"])
            m1, m2, t1, t2 = self._m(p1), self._m(p2), self._t(p1), self._t(p2)
            n = (math.log(m1) - math.log(m2)) / (math.log(t1) - math.log(t2)) if abs(p1 - p2) > 1e-12 else math.sin(p1)
            F = m1 / (n * t1 ** n)
            k0 = 1.0
        else:                                   # one standard parallel (lat_1 = lat_0) with scale k_0
            p1 = math.radians(p.get("lat_1", p["lat_0"]))
            n = math.sin(p1)
            F = self._m(p1) / (n * self._t(p1) ** n)
            k0 = p.get("k_0", 1.0)
        rho0 = self.a * F * k0 * self._t(p0) ** n
        return n, F * k0, rho0, math.radians(p["lon_0"])

    def _fwd_lcc(self, lam, phi):
        n, F, rho0, lam0 = self._lcc_consts()
        rho = self.a * F * self._t(phi) ** n
        th = n * (lam - lam0)
        return rho * np.sin(th), rho0 - rho * np.cos(th)

    def _inv_lcc(self, x, y):
        n, F, rho0, lam0 = self._lcc_consts()
        e = self.e
        rho = np.sign(n) * np.hypot(x, rho0 - y)
        th = np.arctan2(x * np.sign(n), (rho0 - y) * np.sign(n))
        t = (rho / (self.a * F)) ** (1 / n)
        phi = np.pi / 2 - 2 * np.arctan(t)
        for _ in range(15):
            s = e * np.sin(phi)
            phi = np.pi / 2 - 2 * np.arctan(t * ((1 - s) / (1 + s)) ** (e / 2))
        return lam0 + th / n, phi

    # ---- transverse Mercator, Krüger series to 6th order (Karney 2011), sub-millimetre within a few zones
    def _tm_consts(self):
        f = self.f
        n = f / (2 - f)
        A = self.a / (1 + n) * (1 + n ** 2 / 4 + n ** 4 / 64 + n ** 6 / 256)
        al = [n / 2 - 2 * n ** 2 / 3 + 5 * n ** 3 / 16 + 41 * n ** 4 / 180 - 127 * n ** 5 / 288 + 7891 * n ** 6 / 37800,
              13 * n ** 2 / 48 - 3 * n ** 3 / 5 + 557 * n ** 4 / 1440 + 281 * n ** 5 / 630 - 1983433 * n ** 6 / 1935360,
              61 * n ** 3 / 240 - 103 * n ** 4 / 140 + 15061 * n ** 5 / 26880 + 167603 * n ** 6 / 181440,
              49561 * n ** 4 / 161280 - 179 * n ** 5 / 168 + 6601661 * n ** 6 / 7257600,
              34729 * n ** 5 / 80640 - 3418889 * n ** 6 / 1995840,
              212378941 * n ** 6 / 319334400]
        be = [n / 2 - 2 * n ** 2 / 3 + 37 * n ** 3 / 96 - n ** 4 / 360 - 81 * n ** 5 / 512 + 96199 * n ** 6 / 604800,
              n ** 2 / 48 + n ** 3 / 15 - 437 * n ** 4 / 1440 + 46 * n ** 5 / 105 - 1118711 * n ** 6 / 3870720,
              17 * n ** 3 / 480 - 37 * n ** 4 / 840 - 209 * n ** 5 / 4480 + 5569 * n ** 6 / 90720,
              4397 * n ** 4 / 161280 - 11 * n ** 5 / 504 - 830251 * n ** 6 / 7257600,
              4583 * n ** 5 / 161280 - 108847 * n ** 6 / 3991680,
              20648693 * n ** 6 / 638668800]
        k0 = self.p.get("k_0", 1.0)
        lam0, phi0 = math.radians(self.p["lon_0"]), math.radians(self.p.get("lat_0", 0.0))
        return A, al, be, k0, lam0, phi0

    def _tm_xy(self, lam, phi, A, al, k0, lam0):
        e = self.e
        t = np.sinh(np.arctanh(np.sin(phi)) - e * np.arctanh(e * np.sin(phi)))
        dl = lam - lam0
        xi = np.arctan2(t, np.cos(dl))
        eta = np.arctanh(np.sin(dl) / np.sqrt(1 + t * t))
        x, y = eta.copy(), xi.copy()
        for j, a_ in enumerate(al, start=1):
            x = x + a_ * np.cos(2 * j * xi) * np.sinh(2 * j * eta)
            y = y + a_ * np.sin(2 * j * xi) * np.cosh(2 * j * eta)
        return k0 * A * x, k0 * A * y

    def _fwd_tmerc(self, lam, phi):
        A, al, be, k0, lam0, phi0 = self._tm_consts()
        x, y = self._tm_xy(lam, phi, A, al, k0, lam0)
        _, y0 = self._tm_xy(np.array([lam0]), np.array([phi0]), A, al, k0, lam0)
        return x, y - y0[0]

    def _inv_tmerc(self, x, y):
        A, al, be, k0, lam0, phi0 = self._tm_consts()
        e = self.e
        _, y0 = self._tm_xy(np.array([lam0]), np.array([phi0]), A, al, k0, lam0)
        xi, eta = (y + y0[0]) / (k0 * A), x / (k0 * A)
        xp, ep = xi.copy(), eta.copy()
        for j, b_ in enumerate(be, start=1):
            xp = xp - b_ * np.sin(2 * j * xi) * np.cosh(2 * j * eta)
            ep = ep - b_ * np.cos(2 * j * xi) * np.sinh(2 * j * eta)
        tp = np.sin(xp) / np.sqrt(np.sinh(ep) ** 2 + np.cos(xp) ** 2)
        t = tp.copy()
        for _ in range(10):                       # Newton for t = tan(phi), Karney eq. (19)-(21)
            s = np.sinh(e * np.arctanh(e * t / np.sqrt(1 + t * t)))
            tpi = t * np.sqrt(1 + s * s) - s * np.sqrt(1 + t * t)
            dt = (tp - tpi) / np.sqrt(1 + tpi * tpi) * (1 + (1 - e * e) * t * t) / ((1 - e * e) * np.sqrt(1 + t * t))
            t = t + dt
        return lam0 + np.arctan2(np.sinh(ep), np.cos(xp)), np.arctan(t)

    # ---- Mercator
    def _fwd_merc(self, lam, phi):
        e, lam0 = self.e, math.radians(self.p.get("lon_0", 0.0))
        k0 = self.p.get("k_0", 1.0)
        s = np.sin(phi)
        return self.a * k0 * (lam - lam0), self.a * k0 * np.log(np.tan(np.pi / 4 + phi / 2) * ((1 - e * s) / (1 + e * s)) ** (e / 2))

    def _inv_merc(self, x, y):
        e, lam0 = self.e, math.radians(self.p.get("lon_0", 0.0))
        k0 = self.p.get("k_0", 1.0)
        t = np.exp(-y / (self.a * k0))
        phi = np.pi / 2 - 2 * np.arctan(t)
        for _ in range(15):
            s = e * np.sin(phi)
            phi = np.pi / 2 - 2 * np.arctan(t * ((1 - s) / (1 + s)) ** (e / 2))
        return lam0 + x / (self.a * k0), phi

    def _fwd_webmerc(self, lam, phi):
        R = 6378137.0
        return R * lam, R * np.log(np.tan(np.pi / 4 + phi / 2))

    def _inv_webmerc(self, x, y):
        R = 6378137.0
        return x / R, np.pi / 2 - 2 * np.arctan(np.exp(-y / R))


# ------------------------------------------------------------------------------------------------ CRS registry
def _lcc(lat_0, lon_0, lat_1, lat_2, x_0, y_0, unit, name):
    return Projection("lcc", {"lat_0": lat_0, "lon_0": lon_0, "lat_1": lat_1, "lat_2": lat_2, "x_0": x_0, "y_0": y_0}, unit=unit, name=name)


def _tm(lat_0, lon_0, k_0, x_0, y_0, unit, name):
    return Projection("tmerc", {"lat_0": lat_0, "lon_0": lon_0, "k_0": k_0, "x_0": x_0, "y_0": y_0}, unit=unit, name=name)


def _utm(zone, name):
    return _tm(0, -183 + 6 * zone, 0.9996, 500000, 0, 1.0, name)


EPSG: dict[int, Projection] = {
    4326: Projection("longlat", a=WGS84[0], f=WGS84[1], name="WGS 84"),
    4269: Projection("longlat", name="NAD83"),
    4152: Projection("longlat", name="NAD83(HARN)"),
    5070: Projection("aea", {"lat_0": 23, "lon_0": -96, "lat_1": 29.5, "lat_2": 45.5}, name="NAD83 / Conus Albers"),
    3310: Projection("aea", {"lat_0": 0, "lon_0": -120, "lat_1": 34, "lat_2": 40.5, "y_0": -4000000}, name="NAD83 / California Albers"),
    3071: _tm(0, -90, 0.9996, 520000, -4480000, 1.0, "NAD83(HARN) / Wisconsin Transverse Mercator"),
    2952: _tm(0, -79.5, 0.9999, 304800, 0, 1.0, "NAD83(CSRS) / MTM zone 10"),
    2264: _lcc(33.75, -79, 36.1666666666667, 34.3333333333333, 609601.219202438, 0, US_FT, "NAD83 / North Carolina (ftUS)"),
    2263: _lcc(40.1666666666667, -74, 41.0333333333333, 40.6666666666667, 300000, 0, US_FT, "NAD83 / New York Long Island (ftUS)"),
    2230: _lcc(32.1666666666667, -116.25, 33.8833333333333, 32.7833333333333, 2000000.0001016, 500000.0001016, US_FT, "NAD83 / California zone 6 (ftUS)"),
    2285: _lcc(47, -120.833333333333, 48.7333333333333, 47.5, 500000.0001016, 0, US_FT, "NAD83 / Washington North (ftUS)"),
    2926: _lcc(47, -120.833333333333, 48.7333333333333, 47.5, 500000.0001016, 0, US_FT, "NAD83(HARN) / Washington North (ftUS)"),
    2232: _lcc(37.8333333333333, -105.5, 39.75, 38.45, 914401.828803658, 304800.609601219, US_FT, "NAD83 / Colorado Central (ftUS)"),
    2913: _lcc(43.6666666666667, -120.5, 46, 44.3333333333333, 2500000.0001424, 0, INTL_FT, "NAD83(HARN) / Oregon North (ft)"),
    2271: _lcc(40.1666666666667, -77.75, 41.95, 40.8833333333333, 600000, 0, US_FT, "NAD83 / Pennsylvania North (ftUS)"),
    3362: _lcc(40.1666666666667, -77.75, 41.95, 40.8833333333333, 600000, 0, 1.0, "NAD83(HARN) / Pennsylvania North"),
    3361: _lcc(31.8333333333333, -81, 34.8333333333333, 32.5, 609600, 0, INTL_FT, "NAD83(HARN) / South Carolina (ft)"),
    3435: _tm(36.6666666666667, -88.3333333333333, 0.999975, 300000, 0, US_FT, "NAD83 / Illinois East (ftUS)"),
    26912: _utm(12, "NAD83 / UTM zone 12N"),
    26915: _utm(15, "NAD83 / UTM zone 15N"),
    26916: _utm(16, "NAD83 / UTM zone 16N"),
    32616: Projection("tmerc", {"lat_0": 0, "lon_0": -87, "k_0": 0.9996, "x_0": 500000, "y_0": 0}, a=WGS84[0], f=WGS84[1], name="WGS 84 / UTM zone 16N"),
    3857: Projection("webmerc", name="WGS 84 / Pseudo-Mercator"),
    102100: Projection("webmerc", name="WGS 84 / Pseudo-Mercator (Esri 102100)"),
}


def crs(code) -> Projection:
    """A Projection from an EPSG code (int or 'EPSG:5070'), a Projection, or WKT/.prj text."""
    if isinstance(code, Projection):
        return code
    if isinstance(code, str) and not code.upper().startswith("EPSG:") and ("PROJCS" in code or "GEOGCS" in code):
        return from_wkt(code)
    c = int(str(code).upper().replace("EPSG:", ""))
    if c not in EPSG:
        raise ValueError(f"EPSG:{c} is not in missing_middleware.geom's registry; add its parameters (and a test)")
    return EPSG[c]


_ESRI_PARAMS = {"false_easting": "x_0", "false_northing": "y_0", "central_meridian": "lon_0", "longitude_of_center": "lon_0",
                "standard_parallel_1": "lat_1", "standard_parallel_2": "lat_2", "latitude_of_origin": "lat_0",
                "latitude_of_center": "lat_0", "scale_factor": "k_0"}


def from_wkt(wkt: str) -> Projection:
    """Projection from ESRI .prj / WKT1 text (the projections listed in the module docstring)."""
    if "NAD_1927" in wkt or "NAD27" in wkt:
        raise ValueError("NAD27 coordinates need a datum grid shift, which this module does not do")
    if not wkt.strip().upper().startswith("PROJCS"):
        return Projection("longlat", name="geographic")
    proj = re.search(r'PROJECTION\["([^"]+)"\]', wkt).group(1).lower()
    p = {}
    for k, v in re.findall(r'PARAMETER\["([^"]+)",\s*([-0-9.eE+]+)\]', wkt):
        if k.lower() in _ESRI_PARAMS:
            p[_ESRI_PARAMS[k.lower()]] = float(v)
    unit_m = float(re.findall(r'UNIT\["[^"]+",\s*([0-9.eE+-]+)\]', wkt)[-1])
    if "standard_parallel_1" not in wkt.lower() and "lcc" in proj:
        p.setdefault("lat_1", p.get("lat_0"))
    # false easting/northing in WKT are in the CRS's linear unit
    p["x_0"], p["y_0"] = p.get("x_0", 0.0) * unit_m, p.get("y_0", 0.0) * unit_m
    ell = WGS84 if "WGS_1984" in wkt and "NAD" not in wkt else GRS80
    if "mercator_auxiliary_sphere" in proj or "pseudo" in proj:
        return Projection("webmerc", name="web mercator")
    kind = {"albers": "aea", "albers_conic_equal_area": "aea", "lambert_conformal_conic": "lcc",
            "lambert_conformal_conic_2sp": "lcc", "lambert_conformal_conic_1sp": "lcc", "transverse_mercator": "tmerc",
            "mercator": "merc"}.get(proj)
    if kind is None:
        raise ValueError(f"projection {proj} not supported")
    if kind == "lcc" and "lat_2" not in p and "lat_1" in p and abs(p["lat_1"] - p.get("lat_0", p["lat_1"])) < 1e-12:
        pass
    return Projection(kind, p, a=ell[0], f=ell[1], unit=unit_m, name=re.search(r'PROJCS\["([^"]+)"', wkt).group(1))


def transform(x, y, src, dst):
    """Reproject coordinate arrays from src to dst (codes, WKT or Projections)."""
    s, d = crs(src), crs(dst)
    if s is d:
        return np.asarray(x, float).copy(), np.asarray(y, float).copy()
    lon, lat = s.inverse(x, y)
    return d.forward(lon, lat)


# -------------------------------------------------------------------------------------------------- readers
@dataclass
class Layer:
    """Attributes plus geometry. kind: 'point' (x, y arrays) or 'polygon' (list of features -> parts -> rings) or
    'line' (list of features -> list of (n, 2) arrays). crs: the Projection of the coordinates."""
    attrs: pd.DataFrame
    kind: str
    x: np.ndarray | None = None
    y: np.ndarray | None = None
    polys: list | None = None
    crs: Projection | None = None

    def __len__(self) -> int:
        return len(self.attrs)

    def to_crs(self, dst) -> "Layer":
        d = crs(dst)
        if self.kind == "point":
            x, y = transform(self.x, self.y, self.crs, d)
            return Layer(self.attrs, "point", x, y, None, d)
        out = []
        for feat in self.polys:
            parts = []
            for part in feat:
                if self.kind == "line":
                    xx, yy = transform(part[:, 0], part[:, 1], self.crs, d)
                    parts.append(np.c_[xx, yy])
                else:
                    rings = []
                    for r in part:
                        xx, yy = transform(r[:, 0], r[:, 1], self.crs, d)
                        rings.append(np.c_[xx, yy])
                    parts.append(rings)
            out.append(parts)
        return Layer(self.attrs, self.kind, None, None, out, d)

    def subset(self, mask) -> "Layer":
        idx = np.flatnonzero(np.asarray(mask))
        a = self.attrs.iloc[idx].reset_index(drop=True)
        if self.kind == "point":
            return Layer(a, "point", self.x[idx], self.y[idx], None, self.crs)
        return Layer(a, self.kind, None, None, [self.polys[i] for i in idx], self.crs)


def _ring_area_signed(r: np.ndarray) -> float:
    x, y = r[:, 0], r[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def _shp_polygons(data: bytes) -> tuple[str, list]:
    """Parse a .shp file: points or polygons/polylines. Polygon rings are grouped into parts: in a shapefile, outer
    rings run clockwise and holes counter-clockwise; each hole joins the outer ring that contains it."""
    shape_type = struct.unpack("<i", data[32:36])[0]
    pos, feats, xs, ys = 100, [], [], []
    while pos < len(data):
        _, clen = struct.unpack(">ii", data[pos:pos + 8])
        rec = data[pos + 8: pos + 8 + clen * 2]
        pos += 8 + clen * 2
        st = struct.unpack("<i", rec[:4])[0]
        if st == 0:
            if shape_type in (1, 11, 21):
                xs.append(np.nan); ys.append(np.nan)
            else:
                feats.append([])
            continue
        if st in (1, 11, 21):
            x, y = struct.unpack("<dd", rec[4:20])
            xs.append(x); ys.append(y)
            continue
        nparts, npts = struct.unpack("<ii", rec[36:44])
        parts = list(struct.unpack(f"<{nparts}i", rec[44:44 + 4 * nparts])) + [npts]
        pts = np.frombuffer(rec[44 + 4 * nparts: 44 + 4 * nparts + 16 * npts], dtype="<f8").reshape(npts, 2)
        rings = [pts[parts[i]:parts[i + 1]].copy() for i in range(nparts)]
        if st in (3, 13, 23):
            feats.append(rings)
            continue
        outers, holes = [], []
        for r in rings:
            (outers if _ring_area_signed(r) < 0 else holes).append(r)   # clockwise (negative) = outer
        if not outers:                                                # badly oriented file: treat all as outers
            outers, holes = holes, []
        grouped = [[o] for o in outers]
        for h in holes:
            hx, hy = h[0]
            k = next((i for i, o in enumerate(outers) if _point_in_ring(np.array([hx]), np.array([hy]), o)[0]), 0)
            grouped[k].append(h)
        feats.append(grouped)
    if shape_type in (1, 11, 21):
        return "point", (np.array(xs), np.array(ys))
    return ("line" if shape_type in (3, 13, 23) else "polygon"), feats


def read_shapefile(path, layer: str | None = None, columns: list[str] | None = None) -> Layer:
    """A shapefile from a folder path, a .shp path, or a .zip (optionally naming the layer stem)."""
    from missing_middleware.dbf import read_dbf_bytes
    path = Path(path)
    files: dict[str, bytes] = {}
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            shps = [n for n in z.namelist() if n.lower().endswith(".shp")]
            stem = next((n[:-4] for n in shps if layer is None or Path(n).stem == layer), None)
            if stem is None:
                raise FileNotFoundError(f"no layer {layer} in {path}")
            for ext in (".shp", ".dbf", ".prj"):
                name = next((n for n in z.namelist() if n.lower() == (stem + ext).lower()), None)
                if name:
                    files[ext] = z.read(name)
    else:
        stem = path.with_suffix("")
        for ext in (".shp", ".dbf", ".prj"):
            f = Path(str(stem) + ext)
            if f.exists():
                files[ext] = f.read_bytes()
    attrs = read_dbf_bytes(files[".dbf"]) if ".dbf" in files else pd.DataFrame()
    if columns is not None:
        attrs = attrs[[c for c in columns if c in attrs.columns]]
    kind, geo = _shp_polygons(files[".shp"])
    proj = from_wkt(files[".prj"].decode("latin-1")) if ".prj" in files else crs(4269)
    if kind == "point":
        return Layer(attrs.reset_index(drop=True), "point", geo[0], geo[1], None, proj)
    return Layer(attrs.reset_index(drop=True), kind, None, None, geo, proj)


def _gj_coords(g: dict):
    t = g["type"]
    c = g["coordinates"]
    if t == "Point":
        return "point", c
    if t == "MultiPoint":
        return "point", c[0] if c else [np.nan, np.nan]
    if t == "Polygon":
        return "polygon", [[np.asarray(r, float)[:, :2] for r in c]]
    if t == "MultiPolygon":
        return "polygon", [[np.asarray(r, float)[:, :2] for r in p] for p in c]
    if t == "LineString":
        return "line", [np.asarray(c, float)[:, :2]]
    if t == "MultiLineString":
        return "line", [np.asarray(r, float)[:, :2] for r in c]
    raise ValueError(f"geometry type {t} not supported")


def read_geojson(path_or_obj, columns: list[str] | None = None) -> Layer:
    """GeoJSON FeatureCollection (WGS 84 longitude/latitude, per RFC 7946; a 'crs' member naming EPSG is honoured)."""
    obj = path_or_obj if isinstance(path_or_obj, dict) else json.loads(Path(path_or_obj).read_text())
    feats = obj.get("features", [])
    attrs = pd.DataFrame([f.get("properties") or {} for f in feats])
    if columns is not None:
        attrs = attrs[[c for c in columns if c in attrs.columns]]
    src = 4326
    name = ((obj.get("crs") or {}).get("properties") or {}).get("name", "")
    m = re.search(r"EPSG:+(\d+)", name)
    if m and int(m.group(1)) != 4326:
        src = int(m.group(1))
    kinds, geoms = [], []
    for f in feats:
        g = f.get("geometry")
        if not g:
            kinds.append(None); geoms.append(None); continue
        k, c = _gj_coords(g)
        kinds.append(k); geoms.append(c)
    kset = {k for k in kinds if k}
    kind = kset.pop() if len(kset) == 1 else ("polygon" if "polygon" in kset else "point")
    if kind == "point":
        xy = np.array([c if c is not None else [np.nan, np.nan] for c in geoms], float).reshape(-1, 2)[:, :2] if geoms else np.zeros((0, 2))
        return Layer(attrs, "point", xy[:, 0], xy[:, 1], None, crs(src))
    return Layer(attrs, kind, None, None, [g if g is not None else [] for g in geoms], crs(src))


def read_any(path, **kw) -> Layer:
    p = str(path).lower()
    if p.endswith((".geojson", ".json")):
        return read_geojson(path, **kw)
    return read_shapefile(path, **kw)


# ------------------------------------------------------------------------------------------------ operations
def _point_in_ring(px: np.ndarray, py: np.ndarray, ring: np.ndarray) -> np.ndarray:
    """Even-odd rule for one ring (vectorised over points)."""
    x0, y0 = ring[:, 0], ring[:, 1]
    x1, y1 = np.roll(x0, -1), np.roll(y0, -1)
    inside = np.zeros(len(px), bool)
    for a, b, c, d in zip(x0, y0, x1, y1):
        if b == d:
            continue
        cond = (b > py) != (d > py)
        if not cond.any():
            continue
        xint = a + (py - b) * (c - a) / (d - b)
        inside ^= cond & (px < xint)
    return inside


def _point_in_ring_fast(px: np.ndarray, py: np.ndarray, ring: np.ndarray) -> np.ndarray:
    """Same rule, vectorised over edges in chunks (faster for rings with many vertices)."""
    x0, y0 = ring[:, 0], ring[:, 1]
    x1, y1 = np.roll(x0, -1), np.roll(y0, -1)
    keep = y0 != y1
    x0, y0, x1, y1 = x0[keep], y0[keep], x1[keep], y1[keep]
    out = np.zeros(len(px), bool)
    step = max(1, 2_000_000 // max(1, len(x0)))
    for s in range(0, len(px), step):
        X, Y = px[s:s + step, None], py[s:s + step, None]
        cond = (y0 > Y) != (y1 > Y)
        xint = x0 + (Y - y0) * (x1 - x0) / (y1 - y0)
        out[s:s + step] = (np.count_nonzero(cond & (X < xint), axis=1) % 2) == 1
    return out


def points_in_feature(px, py, feature) -> np.ndarray:
    """True for points inside a polygon feature (any part; holes excluded)."""
    px, py = np.asarray(px, float), np.asarray(py, float)
    res = np.zeros(len(px), bool)
    for part in feature:
        ext = part[0]
        bx = (px >= ext[:, 0].min()) & (px <= ext[:, 0].max()) & (py >= ext[:, 1].min()) & (py <= ext[:, 1].max())
        if not bx.any():
            continue
        ix = np.flatnonzero(bx)
        f = _point_in_ring_fast if len(ext) > 64 else _point_in_ring
        ins = f(px[ix], py[ix], ext)
        for hole in part[1:]:
            if ins.any():
                ins &= ~f(px[ix], py[ix], hole)
        res[ix[ins]] = True
    return res


def points_in_polygons(px, py, polys: list) -> np.ndarray:
    """Index of the first polygon feature containing each point, or -1 (a spatial join 'within')."""
    px, py = np.asarray(px, float), np.asarray(py, float)
    out = np.full(len(px), -1, dtype=np.int64)
    if not len(px):
        return out
    order = np.argsort(px)
    sx = px[order]
    for k, feat in enumerate(polys):
        if not feat:
            continue
        allx = np.concatenate([p[0][:, 0] for p in feat])
        ally = np.concatenate([p[0][:, 1] for p in feat])
        lo, hi = np.searchsorted(sx, allx.min(), "left"), np.searchsorted(sx, allx.max(), "right")
        if lo >= hi:
            continue
        cand = order[lo:hi]
        cand = cand[(py[cand] >= ally.min()) & (py[cand] <= ally.max()) & (out[cand] < 0)]
        if not len(cand):
            continue
        hit = points_in_feature(px[cand], py[cand], feat)
        out[cand[hit]] = k
    return out


def points_in_any(px, py, polys: list) -> np.ndarray:
    return points_in_polygons(px, py, polys) >= 0


def feature_area(feature) -> float:
    """Planar area (CRS units squared) of a polygon feature: exteriors minus holes."""
    a = 0.0
    for part in feature:
        a += abs(_ring_area_signed(part[0])) - sum(abs(_ring_area_signed(h)) for h in part[1:])
    return a


def areas(polys: list) -> np.ndarray:
    return np.array([feature_area(f) for f in polys])


def feature_centroid(feature) -> tuple[float, float]:
    """Area-weighted centroid of a polygon feature (holes subtracted)."""
    A = cx = cy = 0.0
    for part in feature:
        for i, r in enumerate(part):
            x, y = r[:, 0], r[:, 1]
            x1, y1 = np.roll(x, -1), np.roll(y, -1)
            cr = x * y1 - x1 * y
            a = 0.5 * cr.sum()
            sgn = 1.0 if i == 0 else -1.0
            a_abs = abs(a) * sgn
            if a != 0:
                cx += sgn * abs(a) * ((x + x1) * cr).sum() / (6 * a)
                cy += sgn * abs(a) * ((y + y1) * cr).sum() / (6 * a)
            A += a_abs
    return (cx / A, cy / A) if A else (np.nan, np.nan)


def centroids(polys: list) -> tuple[np.ndarray, np.ndarray]:
    c = np.array([feature_centroid(f) if f else (np.nan, np.nan) for f in polys], float).reshape(-1, 2)
    return c[:, 0], c[:, 1]


def representative_points(polys: list) -> tuple[np.ndarray, np.ndarray]:
    """A point guaranteed inside each polygon: the centroid when it is inside, otherwise the middle of the widest
    horizontal run through the largest part at its middle height."""
    xs, ys = centroids(polys)
    for k, f in enumerate(polys):
        if not f or (np.isfinite(xs[k]) and points_in_feature([xs[k]], [ys[k]], f)[0]):
            continue
        part = max(f, key=lambda p: abs(_ring_area_signed(p[0])))
        ext = part[0]
        yy = (ext[:, 1].min() + ext[:, 1].max()) / 2
        best = None
        xs_cross = []
        for r in part:
            a, b = r[:, 0], r[:, 1]
            c, d = np.roll(a, -1), np.roll(b, -1)
            m = (b > yy) != (d > yy)
            xs_cross += list(a[m] + (yy - b[m]) * (c[m] - a[m]) / (d[m] - b[m]))
        xs_cross = sorted(xs_cross)
        for i in range(0, len(xs_cross) - 1, 2):
            w = xs_cross[i + 1] - xs_cross[i]
            if best is None or w > best[0]:
                best = (w, (xs_cross[i] + xs_cross[i + 1]) / 2)
        if best is not None:
            xs[k], ys[k] = best[1], yy
    return xs, ys


def nearest(px, py, tx, ty, max_distance: float | None = None):
    """For each point, the index of the nearest target point and the distance (index -1 beyond max_distance)."""
    from scipy.spatial import cKDTree
    t = cKDTree(np.c_[tx, ty])
    d, i = t.query(np.c_[px, py], distance_upper_bound=np.inf if max_distance is None else max_distance)
    i = np.where(np.isfinite(d), i, -1)
    return i, d


def _segments(polys: list):
    seg = []
    owner = []
    for k, f in enumerate(polys):
        for part in f:
            for r in (part if isinstance(part, list) else [part]):
                a = r
                b = np.roll(r, -1, axis=0)
                if np.allclose(r[0], r[-1]):
                    a, b = r[:-1], r[1:]
                seg.append(np.c_[a, b])
                owner.append(np.full(len(a), k))
    if not seg:
        return np.zeros((0, 4)), np.zeros(0, int)
    return np.concatenate(seg), np.concatenate(owner)


def distance_to_polygons(px, py, polys: list, max_distance: float) -> np.ndarray:
    """Distance from each point to the nearest polygon (0 inside), up to max_distance (inf beyond)."""
    from scipy.spatial import cKDTree
    px, py = np.asarray(px, float), np.asarray(py, float)
    out = np.full(len(px), np.inf)
    out[points_in_any(px, py, polys)] = 0.0
    seg, _ = _segments(polys)
    if not len(seg):
        return out
    mid = (seg[:, :2] + seg[:, 2:]) / 2
    half = np.hypot(seg[:, 2] - seg[:, 0], seg[:, 3] - seg[:, 1]).max() / 2
    tree = cKDTree(mid)
    todo = np.flatnonzero(out > 0)
    near = tree.query_ball_point(np.c_[px[todo], py[todo]], r=max_distance + half)
    for j, cand in zip(todo, near):
        if not cand:
            continue
        s = seg[cand]
        ax, ay, bx, by = s[:, 0], s[:, 1], s[:, 2], s[:, 3]
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        t = np.clip(((px[j] - ax) * dx + (py[j] - ay) * dy) / np.where(L > 0, L, 1), 0, 1)
        d = np.hypot(ax + t * dx - px[j], ay + t * dy - py[j]).min()
        if d <= max_distance:
            out[j] = d
    return out


def bbox(layer: Layer) -> tuple[float, float, float, float]:
    if layer.kind == "point":
        return float(np.nanmin(layer.x)), float(np.nanmin(layer.y)), float(np.nanmax(layer.x)), float(np.nanmax(layer.y))
    xs = np.concatenate([r[:, 0] for f in layer.polys for p in f for r in (p if isinstance(p, list) else [p])])
    ys = np.concatenate([r[:, 1] for f in layer.polys for p in f for r in (p if isinstance(p, list) else [p])])
    return float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())
