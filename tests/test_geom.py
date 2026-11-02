"""Offline tests of missing_middleware.geom (the open-licence geometry used in place of shapely/GEOS, pyproj, pyogrio).

Projections are checked against values recorded from PROJ 9 (via pyproj) before the geo stack was removed
(tests/fixtures/geom_projections.json): NAD83-based systems must match to a centimetre; HARN/CSRS systems differ by
about a metre because PROJ applies a datum shift that this module deliberately ignores. Operations are checked on
shapes with known answers. On Wisconsin's 2024 Census places, the operations matched shapely/GEOS exactly when
compared on 2026-11-02 (areas to 5e-9 relative, centroids to 3 mm, 50,000-point within-join 100% agreement,
distances to 6e-9 m); that comparison is recorded in docs/GEOMETRY.md.
"""
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from missing_middleware import geom as G  # noqa: E402

FIX = json.loads((ROOT / "tests" / "fixtures" / "geom_projections.json").read_text())
SHIFTED = {3071, 2952, 2926, 2913, 3361, 3362}   # HARN / CSRS: PROJ shifts the datum, we do not (about 1 m)
NAD27 = {32054}


class TestProjections(unittest.TestCase):
    def test_forward_inverse_against_proj(self):
        for code, v in FIX.items():
            c = int(code)
            if c in NAD27:
                continue
            P = G.crs(c)
            x, y = P.forward(v["lon"], v["lat"])
            err = np.hypot(np.array(x) - v["x_nad83"], np.array(y) - v["y_nad83"]) * P.unit
            tol = 1.5 if c in SHIFTED else 0.01
            self.assertLess(float(np.max(err)), tol, f"EPSG:{c} forward")
            lon, lat = P.inverse(x, y)
            self.assertLess(float(np.max(np.abs(lon - np.array(v["lon"])))), 1e-9, f"EPSG:{c} round trip")
            self.assertLess(float(np.max(np.abs(lat - np.array(v["lat"])))), 1e-9, f"EPSG:{c} round trip")

    def test_wkt_matches_registry(self):
        for code, v in FIX.items():
            c = int(code)
            if c in NAD27:
                with self.assertRaises(ValueError):
                    G.from_wkt(v["wkt"])
                continue
            W, P = G.from_wkt(v["wkt"]), G.crs(c)
            xw, yw = W.forward(v["lon"], v["lat"])
            xp, yp = P.forward(v["lon"], v["lat"])
            self.assertLess(float(np.max(np.hypot(np.array(xw) * W.unit - np.array(xp) * P.unit,
                                                  np.array(yw) * W.unit - np.array(yp) * P.unit))), 0.01, f"EPSG:{c} WKT")


class TestOperations(unittest.TestCase):
    def setUp(self):
        sq = np.array([[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]], float)
        hole = np.array([[4, 4], [6, 4], [6, 6], [4, 6], [4, 4]], float)
        far = np.array([[20, 0], [30, 0], [30, 5], [20, 5], [20, 0]], float)
        self.polys = [[[sq, hole]], [[far]]]

    def test_area_and_centroid(self):
        self.assertAlmostEqual(G.feature_area(self.polys[0]), 96.0)
        self.assertAlmostEqual(G.feature_area(self.polys[1]), 50.0)
        cx, cy = G.feature_centroid(self.polys[1])
        self.assertAlmostEqual(cx, 25.0)
        self.assertAlmostEqual(cy, 2.5)

    def test_points_in_polygons(self):
        px = np.array([1, 5, 25, 15, 9.99])
        py = np.array([1, 5, 2, 2, 9.99])
        self.assertEqual(G.points_in_polygons(px, py, self.polys).tolist(), [0, -1, 1, -1, 0])

    def test_distance_to_polygons(self):
        d = G.distance_to_polygons(np.array([15.0, 1.0, 40.0]), np.array([2.0, 1.0, 2.0]), self.polys, 6.0)
        self.assertAlmostEqual(d[0], 5.0)
        self.assertEqual(d[1], 0.0)
        self.assertTrue(np.isinf(d[2]))

    def test_representative_point_inside(self):
        u = np.array([[0, 0], [10, 0], [10, 10], [8, 10], [8, 2], [2, 2], [2, 10], [0, 10], [0, 0]], float)  # U shape
        rx, ry = G.representative_points([[[u]]])
        self.assertTrue(G.points_in_feature([rx[0]], [ry[0]], [[u]])[0])

    def test_nearest(self):
        i, d = G.nearest([0, 100], [0, 0], [1, 50], [0, 0], max_distance=10)
        self.assertEqual(i.tolist(), [0, -1])
        self.assertAlmostEqual(d[0], 1.0)


if __name__ == "__main__":
    unittest.main()
