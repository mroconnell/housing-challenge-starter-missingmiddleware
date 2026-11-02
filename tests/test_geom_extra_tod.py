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


if __name__ == "__main__":
    unittest.main()
