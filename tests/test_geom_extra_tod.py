"""missing_middleware/geom_extra_tod.py: the TOD chain's extra geometry (numpy/scipy only). Expected interior points
were recorded from GEOS 3.14 (shapely representative_point) before the geo stack was removed."""
from __future__ import annotations

import math
import unittest

import numpy as np
import pandas as pd

from missing_middleware import geom as G
from missing_middleware import geom_extra_tod as X


def poly(ext, *holes):
    return [[np.asarray(ext, float), *[np.asarray(h, float) for h in holes]]]


def box(x0, y0, x1, y1):
    return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])


L_SHAPE = poly([(0, 0), (10, 0), (10, 2), (2, 2), (2, 10), (0, 10), (0, 0)])
C_SHAPE = poly([(0, 0), (10, 0), (10, 3), (3, 3), (3, 7), (10, 7), (10, 10), (0, 10), (0, 0)])
HOLED = poly([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)], [(2, 2), (8, 2), (8, 8), (2, 8), (2, 2)])
MULTI = box(0, 0, 1, 1) + box(5, 5, 9, 6.5)
TRI = poly([(0, 0), (7, 1), (3, 9), (0, 0)])


class TestInteriorPoints(unittest.TestCase):
    def test_matches_geos(self):
        want = {"L": (1.0, 6.0), "C": (1.5, 5.0), "holed": (1.0, 5.0), "multi": (7.0, 5.75), "tri": (3.3333333333333335, 5.0)}
        x, y = X.interior_points([L_SHAPE, C_SHAPE, HOLED, MULTI, TRI])
        for k, (a, b, wx, wy) in zip(want, zip(x, y, *zip(*want.values()))):
            with self.subTest(shape=k):
                self.assertEqual((a, b), (wx, wy))

    def test_inside(self):
        polys = [L_SHAPE, C_SHAPE, HOLED, MULTI, TRI]
        x, y = X.interior_points(polys)
        for k, f in enumerate(polys):
            self.assertTrue(G.points_in_feature([x[k]], [y[k]], f)[0])


class TestAreasAndKeys(unittest.TestCase):
    def test_areas(self):
        np.testing.assert_allclose(X.areas([L_SHAPE, C_SHAPE, HOLED, MULTI, TRI]), [36, 72, 64, 7, 30])
        far = [[np.array([(600000.0, 300000.0), (600010.1, 300000.0), (600010.1, 300020.2), (600000.0, 300020.2)])]]
        self.assertAlmostEqual(X.areas([far])[0], 10.1 * 20.2, delta=1e-8)

    def test_feature_key(self):
        a, b = box(0, 0, 1, 1), box(0, 0, 1, 1)
        self.assertEqual(X.feature_key(a, "Polygon"), X.feature_key(b, "Polygon"))
        self.assertNotEqual(X.feature_key(a, "Polygon"), X.feature_key(a, "MultiPolygon"))
        self.assertNotEqual(X.feature_key(a), X.feature_key(box(0, 0, 1, 1.000001)))
        self.assertIsNone(X.feature_key([]))

    def test_polygons_to_crs_matches_layer(self):
        lay = G.Layer(pd.DataFrame(index=range(2)), "polygon", None, None,
                      [box(-89.4, 43.0, -89.3, 43.1), box(-87.9, 43.0, -87.8, 43.05)], G.crs(4326))
        want = lay.to_crs(3071).polys
        got = X.polygons_to_crs(lay.polys, 4326, 3071)
        for f, g in zip(want, got):
            np.testing.assert_array_equal(f[0][0], g[0][0])


class TestDistances(unittest.TestCase):
    def test_points_near_lines(self):
        line = [np.array([(0.0, 0.0), (100.0, 0.0), (100.0, 5000.0)])]
        got = X.points_near_lines([50, 50, 130, 100, 131, -30], [29.9, 30.1, 2500, 5030, 2500, 0], [line], 30.0)
        self.assertEqual(got.tolist(), [True, False, True, True, False, True])

    def test_nearest_polygon_and_distance(self):
        polys = [box(0, 0, 10, 10), box(100, 0, 110, 10)]
        ix, d = X.nearest_polygon([5, 20, 95, 50, 55], [5, 5, 5, 20, 5], polys)
        self.assertEqual(ix.tolist()[:3], [0, 0, 1])
        np.testing.assert_allclose(d[:4], [0, 10, 5, math.hypot(40, 10)])
        self.assertIn(ix[4], (0, 1))
        far = X.distance_to_polygons_exact([5000.0], [5.0], [box(0, 0, 10000, 1)] + polys)
        self.assertAlmostEqual(far[0], 4.0)

    def test_polygon_distance_and_components(self):
        a, b, c = box(0, 0, 100, 50), box(0, 65, 100, 115), box(500, 0, 600, 50)
        self.assertAlmostEqual(X.polygon_distance(a, b), 15.0)
        self.assertEqual(X.polygon_distance(a, box(50, 25, 60, 30)), 0.0)          # contained
        self.assertEqual(X.polygon_distance(a, box(100, 0, 150, 50)), 0.0)         # shared edge
        comps = sorted(sorted(g) for g in X.components_within([a, b, c], 30.0))
        self.assertEqual(comps, [[0, 1], [2]])
        self.assertEqual(len(X.components_within([a, b, c], 1.0)), 3)


class TestRectangleAndIntersection(unittest.TestCase):
    def test_min_area_rectangle(self):
        L, S = X.min_area_rectangle_sides(np.array([(0, 0), (4, 4), (5, 3), (1, -1)], float))
        self.assertAlmostEqual(L, math.sqrt(32))
        self.assertAlmostEqual(S, math.sqrt(2))
        self.assertEqual(X.min_area_rectangle_sides(np.array([(0, 0), (3, 4), (6, 8)], float)), (10.0, 0.0))

    def test_intersection_area(self):
        self.assertAlmostEqual(X.intersection_area(box(0, 0, 10, 10), box(5, 5, 15, 15)), 25.0)
        self.assertAlmostEqual(X.intersection_area(box(0, 0, 10, 10), box(0, 0, 10, 10)), 100.0)       # identical
        self.assertAlmostEqual(X.intersection_area(box(0, 0, 10, 10), box(0, 0, 5, 10)), 50.0)         # shared edges
        self.assertAlmostEqual(X.intersection_area(box(0, 0, 10, 10), box(10, 0, 20, 10)), 0.0)        # touching
        self.assertAlmostEqual(X.intersection_area(HOLED, box(0, 0, 5, 5)), 25.0 - 9.0)                # hole
        self.assertAlmostEqual(X.intersection_area(L_SHAPE, C_SHAPE), 20 + 2 + 8 + 6)                  # 36
        self.assertAlmostEqual(X.intersection_area(TRI, box(-100, -100, 100, 100)), 30.0)



class TestBufferedAoi(unittest.TestCase):
    """GEOS buffer (quad_segs 16) of features as tile tests use it; expected values recorded from shapely 2.2."""
    q = math.pi / 2 / 16

    def test_bounds(self):
        self.assertEqual(X.BufferedAoi([([L_SHAPE], 5.0)]).bounds, (-5.0, -5.0, 15.0, 15.0))
        b = X.BufferedAoi([(np.array([[3.0, 4.0]]), 5.0)]).bounds
        np.testing.assert_allclose(b, (-2.0, -1.0, 8.0, 9.0), atol=1e-12)
        both = X.BufferedAoi([([L_SHAPE], 5.0), ((np.array([30.0]), np.array([4.0])), 1.0)])
        self.assertEqual(both.bounds[2], 31.0)

    def test_chords(self):
        # a box whose corner lies between the chord and the true circle misses GEOS's buffer
        a = -math.pi / 2 + self.q / 2                     # middle of the first chord at the corner (10, 0)
        aoi = X.BufferedAoi([([L_SHAPE], 5.0)])
        for d, hit in ((4.995, False), (4.99, True)):
            x, y = 10 + d * math.cos(a), d * math.sin(a)
            self.assertEqual(aoi.intersects_box(x, y - 1, x + 1, y), hit, d)
        pts = X.BufferedAoi([(np.array([[3.0, 4.0]]), 5.0)])
        for d, hit in ((4.995, False), (4.99, True)):
            x, y = 3 + d * math.cos(self.q / 2), 4 + d * math.sin(self.q / 2)
            self.assertEqual(pts.intersects_box(x, y, x + 1, y + 1), hit, d)

    def test_inside_and_far(self):
        aoi = X.BufferedAoi([([L_SHAPE], 5.0)])
        self.assertTrue(aoi.intersects_box(4, 4, 6, 6))           # in the notch, within 5 m of the arms
        self.assertTrue(aoi.intersects_box(-100, -100, 100, 100))  # covers it all
        self.assertFalse(aoi.intersects_box(16, 16, 20, 20))
        self.assertFalse(X.BufferedAoi().intersects_box(0, 0, 1, 1))



class TestMinRotatedRectangle(unittest.TestCase):
    # widths recorded from shapely 2.2 / GEOS 3.14: min side of minimum_rotated_rectangle
    def test_widths_match_geos(self):
        q = [(498297.0131, 4978939.9955), (498296.8986, 4978902.0803), (498284.7140, 4978902.1173),
             (498286.1, 4978925.3), (498284.8283, 4978940.0321)]
        w = X.min_rect_widths([poly(q + [q[0]]), TRI, L_SHAPE, box(0, 0, 5, 20)])
        self.assertEqual(w[0], 12.184845337653298)            # bit-identical at UTM-sized coordinates
        self.assertAlmostEqual(w[1], 7.071067811865472, places=12)
        self.assertEqual(list(w[2:]), [10.0, 5.0])

    def test_degenerate(self):
        line = poly([(0, 0), (1, 1), (2, 2), (0, 0)])
        w = X.min_rect_widths([[], line])
        self.assertTrue(np.isnan(w).all())
        self.assertIsNone(X.min_rotated_rectangle(np.array([(0.0, 0.0), (1.0, 1.0)])))

    def test_rectangle_is_minimum_area(self):
        c = X.min_rotated_rectangle(np.concatenate(TRI[0]))
        e = np.diff(np.vstack([c, c[:1]]), axis=0)
        sides = np.hypot(e[:, 0], e[:, 1])
        self.assertAlmostEqual(sides[0] * sides[1], 60.0, places=6)    # twice the triangle's area (30)


class TestRegions(unittest.TestCase):
    """Regions and overlap areas (census scripts). A GEOS buffer of an a x a square by r (16 chords per quarter turn)
    has area a^2 + 4ar + 32 r^2 sin(pi/32): the square, four edge bands and a 64-gon split over the corners."""

    def test_buffer_area_and_points(self):
        a, r = 10.0, 3.0
        B = X.Buffer([box(0, 0, a, a)], r)
        want = a * a + 4 * a * r + 32 * r * r * math.sin(math.pi / 32)
        self.assertAlmostEqual(X.overlap_areas([box(-50, -50, 50, 50)], B)[0], want, places=6)
        self.assertAlmostEqual(X.overlap_areas([box(5, 5, 6, 6)], B)[0], 1.0, places=9)             # inside
        self.assertEqual(X.overlap_areas([box(20, 20, 30, 30)], B)[0], 0.0)                         # outside
        self.assertEqual(list(B.contains([5, 12.9, 13.1, 12.0, 12.2], [5, 5, 5, 12.0, 12.2])),
                         [True, True, False, True, False])          # band edge at 13; corner chord near (12.12, 12.12)
        right = a * a + 3 * a * r + 16 * r * r * math.sin(math.pi / 32)       # x >= 0: no left band or corners
        self.assertAlmostEqual(X.overlap_areas([box(0, -50, 50, 50)], B)[0], right, places=6)

    def test_difference_union_and_shared_edges(self):
        ring = X.Buffer([box(0, 0, 10, 10)], 3) - X.Polygons([box(0, 0, 10, 10)])
        a = X.overlap_areas([box(-50, -50, 50, 50), box(0, 0, 10, 10), box(5, 0, 15, 10)], ring)
        self.assertAlmostEqual(a[0], 4 * 10 * 3 + 32 * 9 * math.sin(math.pi / 32), places=6)
        self.assertAlmostEqual(a[1], 0.0, places=6)             # the hole exactly (shared edges)
        self.assertAlmostEqual(a[2], 30.0, places=6)            # half outside the square, all within 3 of it
        u = X.Polygons([box(0, 0, 2, 2)]) | X.Polygons([box(1, 1, 3, 3)])
        self.assertAlmostEqual(X.overlap_areas([box(0, 0, 3, 3)], u)[0], 7.0, places=9)
        both = X.Polygons([box(0, 0, 2, 2)]) & X.Polygons([box(1, 1, 3, 3)])
        self.assertAlmostEqual(X.overlap_areas([box(0, 0, 3, 3), HOLED], both)[0], 1.0, places=9)
        self.assertAlmostEqual(X.overlap_areas([HOLED], X.Polygons([box(0, 0, 5, 5)]))[0], 25.0 - 9.0, places=9)
        self.assertEqual(list(X.points_in_region([1, 2.5], [1, 2.5], u - X.Polygons([box(0, 0, 1.5, 1.5)]))), [False, True])
        self.assertEqual(list(X.points_in_region([1], [1], None)), [False])

    def test_shared_and_nearly_coincident_edges(self):
        # neighbouring zones sharing an edge with a T-junction, and one whose edge runs a micrometre off it: the
        # block's overlap is its area outside the zones however their edges duplicate each other
        zones = X.Polygons([box(0, 0, 10, 4), box(0, 4, 5, 10), box(5, 4, 10, 10),
                            poly([(10, 0), (20, 0), (20, 10), (10 + 1e-6, 10), (10, 0)])])
        self.assertAlmostEqual(X.overlap_areas([box(-5, -5, 25, 15)], zones)[0], 200.0 - 5e-6, places=6)
        hole = X.Buffer([box(0, 0, 20, 10)], 2) - zones
        self.assertAlmostEqual(X.overlap_areas([box(-5, -5, 25, 15)], hole)[0],
                               (20 + 10) * 2 * 2 + 32 * 4 * math.sin(math.pi / 32) + 5e-6, places=6)

    def test_large_coordinates(self):
        o = 1.5e6                                                # Albers-sized coordinates keep their precision
        sq = [[np.array([(o, o), (o + 10, o), (o + 10, o + 10), (o, o + 10), (o, o)])]]
        B = X.Buffer([sq], 3)
        want = 100 + 120 + 32 * 9 * math.sin(math.pi / 32)
        self.assertAlmostEqual(X.overlap_areas([box(o - 50, o - 50, o + 50, o + 50)], B)[0], want, places=5)

    def test_feature_from_geo_interface(self):
        class G:
            __geo_interface__ = {"type": "MultiPolygon", "coordinates": [[[(0, 0), (1, 0), (1, 1), (0, 0)]], []]}
        f = X.feature_from_geo_interface(G())
        self.assertEqual(len(f), 1)
        self.assertAlmostEqual(X.areas([f])[0], 0.5)
        self.assertEqual(X.feature_from_geo_interface(None), [])
        self.assertIs(X.feature_from_geo_interface(HOLED), HOLED)
        gc = {"type": "GeometryCollection", "geometries": [{"type": "Point", "coordinates": (0, 0)},
                                                           {"type": "Polygon", "coordinates": [[(0, 0), (2, 0), (2, 2), (0, 0)]]}]}
        self.assertAlmostEqual(X.areas([X.feature_from_geo_interface(gc)])[0], 2.0)


class TestRegionPolygons(unittest.TestCase):
    """Parts of a union of GEOS point buffers clipped to a polygon (scripts/build_tod_net_coverage.py); reference values
    recorded from shapely 2.2 (union_all of buffer(quad_segs=16), intersection, parts by area) before the geo stack
    was removed."""

    def test_buffers_in_strip(self):
        x = np.array([0.0, 600.0, 2500.0, 5000.0, 5000.0 + 804.672])
        r = np.array([402.336, 402.336, 804.672, 402.336, 402.336])
        strip = [[np.array([(-500, -300), (5500, -300), (5500, 300), (-500, 300), (-500, -300)], float)]]
        ps = X.region_polygons(X.PointBuffers(x, np.zeros(5), r) & X.Polygons([strip]))
        want = [941935.8526801761, 790829.131260289, 432851.8624618945, 34962.91716736643]
        self.assertEqual(len(ps), 4)            # the last two circles touch at a point: two parts, as GEOS
        np.testing.assert_allclose(X.areas(ps), want, rtol=1e-9)
        self.assertTrue(X.PointBuffers(x, np.zeros(5), r).contains([0.0, 402.0, 0.0], [0.0, 0.0, 402.0]).tolist() == [True, True, True])
        self.assertFalse(X.PointBuffers([0.0], [0.0], [402.336]).contains([300.0], [300.0])[0])

    def test_hole(self):
        sq = [np.array([(-1000, -1000), (1000, -1000), (1000, 1000), (-1000, 1000), (-1000, -1000)], float),
              np.array([(-200, -200), (-200, 200), (200, 200), (200, -200), (-200, -200)], float)]
        reg = X.PointBuffers([-700.0, 700.0, 0.0, 0.0], [0.0, 0.0, 700.0, -700.0], 500.0) & X.Polygons([[sq]])
        ps = X.region_polygons(reg)
        self.assertEqual(len(ps), 1)
        self.assertEqual(len(ps[0][0]), 2)       # shell and one hole
        self.assertAlmostEqual(float(X.areas(ps)[0]), 2687370.770617211, delta=1e-4)
        a = X.region_area_by_tiles([[sq]], X.PointBuffers([-700.0, 700.0, 0.0, 0.0], [0.0, 0.0, 700.0, -700.0], 500.0), tile=300.0)
        self.assertAlmostEqual(float(a[0]), 2687370.770617211, delta=1e-3)

    def test_utm(self):
        for lon, lat, epsg in ((-74.0, 40.7, 32618), (-118.4, 34.0, 32611), (-89.4, 43.07, 32616), (151.0, -33.9, 32756)):
            p = X.utm_for_lonlat(lon, lat)
            self.assertEqual(p.p["lon_0"], -183.0 + 6 * (epsg % 100))
            self.assertEqual(p.p["y_0"], 10000000.0 if epsg // 100 == 327 else 0.0)
        x, y = X.utm_for_lonlat(-89.4, 43.07).forward(-87.0, 0.0)
        self.assertAlmostEqual(float(x), 500000.0, places=6)


if __name__ == "__main__":
    unittest.main()
