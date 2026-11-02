"""Offline tests of missing_middleware/geom_extra_station.py (helpers for the TOD station-area chain and the lot-model
case modules; numpy/scipy only)."""
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from missing_middleware import geom_extra_station as XS  # noqa: E402


# ---- added for the case modules
class TestCaseModuleHelpers(unittest.TestCase):
    def test_extra_crs_against_proj(self):
        import json
        fx = json.loads((Path(__file__).resolve().parent / "fixtures" / "geom_extra_station_crs.json").read_text())
        for code, v in fx.items():
            x, y = XS.crs(int(code)).forward(np.array(v["lon"]), np.array(v["lat"]))
            self.assertLess(float(np.max(np.hypot(x - np.array(v["x"]), y - np.array(v["y"])))), 1e-6, code)

    def test_wgs84_to_csrs_matches_proj(self):
        # PROJ (EPSG:1946 inverse, coordinate frame) value for one Toronto point, recorded with pyproj before removal
        lo, la = XS.wgs84_to_csrs(np.array([-79.4]), np.array([43.7]))
        x, y = XS.crs(2952).forward(lo, la)
        mx, my = XS.crs(2952).forward(np.array([-79.4]), np.array([43.7]))
        self.assertAlmostEqual(float(x[0] - mx[0]), 0.2625, places=3)
        self.assertAlmostEqual(float(y[0] - my[0]), -0.9540, places=3)

    def test_point_poly_pairs_and_nearest(self):
        sq = lambda a, b, c, d: [[np.array([[a, b], [a, d], [c, d], [c, b], [a, b]], float)]]  # noqa: E731
        polys = [sq(0, 0, 10, 10), sq(5, 5, 15, 15), sq(100, 0, 110, 10)]
        pi, gi = XS.point_poly_pairs([7, 1, 50], [7, 1, 5], polys)
        self.assertEqual(list(zip(pi, gi)), [(0, 0), (0, 1), (1, 0)])
        self.assertEqual(list(XS.first_within([7, 1, 50], [7, 1, 5], polys)), [0, 0, -1])
        ix, d = XS.nearest_polygon([50, 95, 20], [5, 5, 5], polys, 30.0)
        self.assertEqual(list(ix), [-1, 2, 1])
        self.assertAlmostEqual(d[1], 5.0)
        self.assertAlmostEqual(d[2], 5.0)

    def test_make_valid_nested_turns_inner_shell_into_hole(self):
        sq = lambda a, b: np.array([[a, a], [a, b], [b, b], [b, a], [a, a]], float)  # noqa: E731
        f = XS.make_valid_nested([[[sq(0, 10)], [sq(2, 8)]]])[0]
        self.assertEqual(len(f), 1)
        self.assertEqual(len(f[0]), 2)
        self.assertEqual(list(XS.first_within([5, 1], [5, 1], [f])), [-1, 0])
        valid = [[sq(0, 10), sq(2, 8)]]
        self.assertIs(XS.make_valid_nested([valid])[0], valid)

    def test_within_point_buffers_is_the_64gon(self):
        r = 100.0
        # between two vertices the 64-gon edge lies r*cos(pi/64) from the centre
        a = np.pi / 64
        inside = r * np.cos(a) * 0.999999
        outside = r * np.cos(a) * 1.000001
        m = XS.within_point_buffers([inside * np.cos(a), outside * np.cos(a), 99.9999], [inside * np.sin(a), outside * np.sin(a), 0],
                                    [0.0], [0.0], r)
        self.assertEqual(list(m), [True, False, True])

    def test_wkb_multipolygon_z(self):
        import struct
        ring = [(0, 0, 1), (0, 1, 1), (1, 1, 1), (0, 0, 1)]
        poly = struct.pack("<BII", 1, 1003, 1) + struct.pack("<I", 4) + b"".join(struct.pack("<3d", *p) for p in ring)
        mp = struct.pack("<BII", 1, 1006, 1) + poly
        k, v = XS.wkb_feature(mp)
        self.assertEqual(k, "polygon")
        self.assertEqual(v[0][0].shape, (4, 2))

    def test_centroid_large_coordinates(self):
        o = 1.5e6
        f = [[np.array([[o, o], [o, o + 2], [o + 2, o + 2], [o + 2, o], [o, o]], float)]]
        x, y = XS.centroids_geos([f])
        self.assertAlmostEqual(x[0] - o, 1.0, places=9)
        self.assertAlmostEqual(y[0] - o, 1.0, places=9)


class TestGeosBuffer(unittest.TestCase):
    def test_corner_chord(self):
        sq = [[np.array([[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]], float)]]
        r = 100.0
        # beyond the corner (10, 10), half way along the first of GEOS's 16 chords (2.8125 degrees): the circle reaches r,
        # the chord only r * cos(2.8125 degrees) (shapely: outside); above the top edge: inside
        a = np.radians(2.8125)
        x, y = 10 + 99.95 * np.cos(a), 10 + 99.95 * np.sin(a)
        self.assertEqual(list(XS.within_buffer_geos([x, 5.0, 5.0], [y, 109.9, 5.0], [sq], r)), [False, True, True])
        self.assertTrue(XS.nearest_polygon([x], [y], [sq], r)[1][0] <= r)


# ---- station-area chain helpers (interior points, station merging, ties, outlines, WKB, File Geodatabase varints)
def _sq(x0, y0, x1, y1):
    return np.array([[x0, y0], [x0, y1], [x1, y1], [x1, y0], [x0, y0]], float)


class TestStationHelpers(unittest.TestCase):
    def test_interior_point_is_geos_scanline_midpoint(self):
        # square with a central hole: scan line at y = 5 (between the vertex heights 4 and 6), widest run 0..4
        x, y = XS.interior_points([[[_sq(0, 0, 10, 10), _sq(4, 4, 6, 6)]]])
        self.assertEqual((x[0], y[0]), (2.0, 5.0))
        # L shape: GEOS takes the middle of the widest run on the scan line, not the centroid
        L = np.array([[0, 0], [0, 10], [2, 10], [2, 2], [10, 2], [10, 0], [0, 0]], float)
        x, y = XS.interior_points([[[L]]])
        self.assertEqual((x[0], y[0]), (1.0, 6.0))
        # multipart feature: the part with the widest run
        x, y = XS.interior_points([[[_sq(0, 0, 1, 1)], [_sq(100, 0, 110, 10)]]])
        self.assertEqual((x[0], y[0]), (105.0, 5.0))

    def test_areas_keep_precision_far_from_origin(self):
        a = XS.areas([[[_sq(2_000_000, 1_000_000, 2_000_000.1, 1_000_000.1)]]])
        self.assertAlmostEqual(a[0], 0.01, places=9)   # coordinates themselves round at 2e-10 m

    def test_merge_within_unions_64gons(self):
        cx, cy, mem = XS.merge_within([0.0, 100.0, 1000.0], [0.0, 30.0, 0.0], 75.0)
        self.assertEqual(len(cx), 2)
        k = int(np.argmin(cx))
        self.assertAlmostEqual(cx[k], 50.0, places=9)
        self.assertAlmostEqual(cy[k], 15.0, places=9)
        self.assertEqual(sorted(mem[k].tolist()), [0, 1])
        # 150 m apart along x: the 64-gons touch only at a vertex (no overlap of interiors beyond it) -> GEOS merges
        # them when they overlap; 149.9 m overlaps, 151 m does not
        self.assertEqual(len(XS.merge_within([0.0, 149.9], [0.0, 0.0])[0]), 1)
        self.assertEqual(len(XS.merge_within([0.0, 151.0], [0.0, 0.0])[0]), 2)
        # a lone stop stays where it is (centroid computed relative to the ring, no rounding loss)
        cx, cy, _ = XS.merge_within([1_811_324.15618239], [2_152_591.93716431])
        self.assertAlmostEqual(cx[0], 1_811_324.15618239, places=6)
        self.assertAlmostEqual(cy[0], 2_152_591.93716431, places=6)

    def test_nearest_lowest_breaks_ties_by_position(self):
        i, d = XS.nearest_lowest([0.0, 50.0], [0.0, 0.0], [10.0, 10.0, -10.0, 500.0], [0.0, 0.0, 0.0, 0.0], 100.0)
        self.assertEqual(i.tolist(), [0, 0])
        self.assertEqual(d.tolist(), [10.0, 40.0])
        i, d = XS.nearest_lowest([1000.0], [0.0], [0.0], [0.0], 100.0)
        self.assertEqual((int(i[0]), float(d[0])), (-1, float("inf")))

    def test_outline_keys(self):
        a, b, c = [[_sq(0, 0, 1, 1)]], [[_sq(0, 0, 1, 1)]], [[_sq(0, 0, 1, 2)]]
        k = XS.outline_keys([a, b, c, []])
        self.assertEqual(k[0], k[1])
        self.assertNotEqual(k[0], k[2])
        self.assertIsNone(k[3])

    def test_wkb_polygon(self):
        import struct
        r = _sq(0, 0, 2, 3)
        buf = struct.pack("<BII", 1, 3, 1) + struct.pack("<I", len(r)) + r.astype("<f8").tobytes()
        parts = XS._wkb_polygons(buf)
        self.assertEqual(len(parts), 1)
        np.testing.assert_array_equal(parts[0][0], r)

    def test_gdb_varints(self):
        # Esri signed varint: first byte 6 value bits + sign bit 0x40 + continuation 0x80; then 7 bits a byte
        raw = bytes([0x05, 0x45, 0x80 | 0x01, 0x02, 0xC0 | 0x3F, 0x7F])
        v, end = XS._varints(memoryview(raw), 0, 4)
        self.assertEqual(v.tolist(), [5, -5, 1 + (2 << 6), -(0x3F + (0x7F << 6))])
        self.assertEqual(end, len(raw))
        self.assertEqual(XS._varuint(bytes([0x96, 0x01]), 0), (150, 2))
