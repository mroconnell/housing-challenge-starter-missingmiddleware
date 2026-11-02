"""Offline tests of missing_middleware.geom_extra_foundation (operations the foundation, permits, district and UI-bundle
builds need beyond missing_middleware.geom). Shapes with known answers; the GEOS-matching behaviour was checked on the
Wisconsin TIGER/Line and cartographic files against shapely 2.2 / GEOS 3.14 before the geo stack was removed
(docs/GEOMETRY.md, port log)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from missing_middleware import geom_extra_foundation as X  # noqa: E402


def ring(*pts):
    a = np.array(pts, float)
    return np.vstack([a, a[:1]])


SQUARE = [[ring((0, 0), (10, 0), (10, 10), (0, 10))]]
HOLED = [[ring((0, 0), (10, 0), (10, 10), (0, 10)), ring((2, 2), (2, 4), (4, 4), (4, 2))]]


class TestInteriorPoint(unittest.TestCase):
    def test_square_and_u_shape(self):
        x, y = X.interior_points([SQUARE])
        self.assertEqual((x[0], y[0]), (5.0, 5.0))
        # U shape: the centre (5, 5) is outside; GEOS picks the widest run at the scan line next to mid-height
        u = [[ring((0, 0), (10, 0), (10, 10), (7, 10), (7, 3), (3, 3), (3, 10), (0, 10))]]
        x, y = X.interior_points([u])
        self.assertEqual(y[0], 6.5)              # midway between the vertex heights 3 and 10 around the centre 5
        self.assertIn(x[0], (1.5, 8.5))

    def test_hole_avoided(self):
        donut = [[ring((0, 0), (10, 0), (10, 10), (0, 10)), ring((1, 1), (1, 9), (9, 9), (9, 1))]]
        x, y = X.interior_points([donut])
        self.assertTrue(x[0] < 1 or x[0] > 9)


class TestSimplify(unittest.TestCase):
    def test_collinear_and_small_wiggles_removed(self):
        r = ring((0, 0), (5, 0.1), (10, 0), (10, 10), (5, 10.1), (0, 10))
        out = X.simplify_preserve([[[r]]], 1.0)[0][0][0]
        self.assertEqual(len(out), 5)            # a ring keeps at least 4 distinct points
        self.assertTrue(np.array_equal(out[0], out[-1]))

    def test_hole_not_jumped(self):
        # flattening (5, 4.2)-(4, 10)-(0, 10) would put the hole's second vertex outside the polygon; GEOS keeps (4, 10)
        shell = ring((0, 0), (10, 0), (10, 10), (6, 10), (5, 4.2), (4, 10), (0, 10))
        hole = ring((4.5, 5), (4.5, 6), (5.5, 6), (5.5, 5))
        out = X.simplify_preserve([[[shell, hole]]], 5.0)[0][0]
        self.assertEqual(out[0].tolist(), [[0, 0], [10, 0], [10, 10], [5, 4.2], [4, 10], [0, 10], [0, 0]])
        self.assertEqual(out[1].tolist(), hole.tolist())


class TestPrecision(unittest.TestCase):
    def test_round_orient_restart(self):
        p = [[ring((0.00001, 0.00002), (1.00004, 0.00003), (1.00002, 1.00001), (0.50003, 1.40002), (0.00001, 1.00004))]]
        out = X.set_precision_polygons([p], 1e-4)[0][0][0]
        # as shapely.set_precision: clockwise, starting at the second vertex of the clockwise ring
        self.assertEqual(out.tolist(), [[0, 1], [0.5, 1.4], [1, 1], [1, 0], [0, 0], [0, 1]])

    def test_spike_through_pixel_removed(self):
        # after rounding, segment (0.8, 0.5001)-(0.4, 0.5) passes through the grid pixel of (0.6, 0.5): snap rounding
        # nodes it there and the zero-area spike to (0.8, 0.5001) disappears (GEOS gives the same five corners)
        p = [[ring((0, 0), (1, 0), (1, 0.5), (0.6, 0.5), (0.8, 0.50006), (0.4, 0.50002), (0, 0.5))]]
        out = X.set_precision_polygons([p], 1e-4)[0][0][0]
        self.assertEqual({tuple(v) for v in out.tolist()}, {(1, 0.5), (1, 0), (0, 0), (0, 0.5), (0.4, 0.5), (0.6, 0.5)})
        self.assertEqual(len(out), 7)
        self.assertTrue(X.rings_are_simple([[out]]))

    def test_validity_check(self):
        bow = [[ring((0, 0), (1, 1), (1, 0), (0, 1))]]
        self.assertFalse(X.rings_are_simple(bow))
        self.assertTrue(X.rings_are_simple(HOLED))


class TestOverlay(unittest.TestCase):
    def test_intersection_areas(self):
        a = [SQUARE, HOLED]
        b = [[[ring((5, -5), (15, -5), (15, 5), (5, 5))]],          # overlaps a quarter of each
             [[ring((10, 0), (20, 0), (20, 10), (10, 10))]],         # shares an edge only
             [[ring((0, 0), (10, 0), (10, 10), (0, 10))]]]           # identical to the square
        got = X.intersection_areas(a, b).set_index(["i", "j"])["area"]
        self.assertAlmostEqual(got[(0, 0)], 25.0, places=9)
        self.assertAlmostEqual(got[(1, 0)], 25.0, places=9)        # the hole lies outside the overlap
        self.assertAlmostEqual(got[(0, 2)], 100.0, places=9)
        self.assertAlmostEqual(got[(1, 2)], 96.0, places=9)
        self.assertNotIn((0, 1), got.index)                         # touching is not overlapping

    def test_nearest_polygon(self):
        polys = [SQUARE, [[ring((20, 0), (30, 0), (30, 10), (20, 10))]]]
        k = X.nearest_polygon([5, 12, 19, np.nan], [5, 5, 5, 5], polys)
        self.assertEqual(k.tolist(), [0, 0, 1, -1])


class TestFiles(unittest.TestCase):
    def test_wkb_round_trip_and_geoparquet(self):
        feats = [SQUARE, [SQUARE[0], [ring((20, 0), (30, 0), (30, 10))]]]
        kinds = ["Polygon", "MultiPolygon"]
        for f, k in zip(feats, kinds):
            g, kk = X.from_wkb(X.to_wkb(f, k))
            self.assertEqual(kk, k)
            self.assertEqual(X.to_wkb(g, kk), X.to_wkb(f, k))
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.parquet"
            X.write_geoparquet(pd.DataFrame({"GEOID": ["a", "b"], "area_id": ["x", "y"]}), feats, kinds, p, 4269,
                               geometry_position=1)
            attrs, polys, kk, epsg = X.read_geoparquet(p)
            self.assertEqual(list(attrs.columns), ["GEOID", "area_id"])
            self.assertEqual((kk, epsg), (kinds, 4269))
            self.assertTrue(all(X.to_wkb(a, k) == X.to_wkb(b, k) for a, b, k in zip(polys, feats, kinds)))

    def test_geojson_writer(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.geojson"
            X.write_geojson_gdal(p, "t", pd.DataFrame({"district": [1]}), [SQUARE], ["Polygon"])
            obj = json.loads(p.read_text())
            self.assertEqual(obj["name"], "t")
            self.assertEqual(obj["features"][0]["properties"], {"district": 1})
            self.assertEqual(X.geojson_kinds(p), ["Polygon"])


class TestGeoParquetCaches(unittest.TestCase):
    """Census-script caches: GeoParquet points and a selective polygon read."""

    def test_points_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "pts.parquet"
            x, y = np.array([1.5e6, -2.25, np.pi]), np.array([2.0e6, 7.0, -1.0])
            X.write_geoparquet_points(pd.DataFrame({"homes": [1.0, 2.0, 3.0], "land": [4.0, 5.0, 6.0]}), x, y, p, 5070)
            a, xx, yy, epsg = X.read_geoparquet_points(p)
            self.assertEqual(list(a.columns), ["homes", "land"])
            np.testing.assert_array_equal(xx, x)
            np.testing.assert_array_equal(yy, y)
            self.assertEqual(epsg, 5070)

    def test_read_near(self):
        feats = [SQUARE, [[ring((20, 0), (30, 0), (30, 10))]], HOLED]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "polys.parquet"
            X.write_geoparquet(pd.DataFrame({"homes": [1.0, 2.0, 3.0]}), feats, ["Polygon"] * 3, p, 4269)
            a, f, epsg = X.read_geoparquet_near(p, [(25, 5, 40, 40)], batch_rows=2)
            self.assertEqual(list(a["homes"]), [2.0])
            self.assertEqual(X.to_wkb(f[0], "Polygon"), X.to_wkb(feats[1], "Polygon"))
            a, f, _ = X.read_geoparquet_near(p, [(-1, -1, 0, 0), (100, 100, 101, 101)])
            self.assertEqual(list(a["homes"]), [1.0, 3.0])        # touching boxes count; row order kept
            self.assertEqual(epsg, 4269)
            a, f, _ = X.read_geoparquet_near(p, [])
            self.assertEqual((len(a), len(f)), (0, 0))


if __name__ == "__main__":
    unittest.main()
