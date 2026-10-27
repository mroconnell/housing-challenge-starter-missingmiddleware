"""TOD net effect, borrowing and coverage (missing_middleware/tod/net_effect.py; docs/tod/NET_EFFECT_PLAN.md): rules on
small synthetic tables and shapes, no network. Committed outputs are checked for identifiers when they exist."""
from __future__ import annotations

import math
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.tod import cases as C
from missing_middleware.tod import net_effect as NE
from missing_middleware.tod import traits as T

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference"


def grid(n: int = 30, size: float = 100.0):
    """n x n square lots of size metres, as a GeoDataFrame in a metre CRS."""
    import geopandas as gpd
    from shapely.geometry import box
    geoms = [box(i * size, j * size, (i + 1) * size, (j + 1) * size) for j in range(n) for i in range(n)]
    return gpd.GeoDataFrame(geometry=geoms, crs=32616)


class TestAreas(unittest.TestCase):
    def setUp(self):
        self.lots = grid()
        n = len(self.lots)
        c = self.lots.geometry.centroid
        self.in_reform = pd.Series((c.x < 300) & (c.y < 300), index=self.lots.index)
        self.rose = self.in_reform.copy()
        self.lb = pd.Series(1.0, index=self.lots.index)
        self.la = pd.Series(np.where(self.in_reform, 3.0, 1.0), index=self.lots.index)
        self.unc = pd.Series(True, index=self.lots.index)
        self.changed = pd.Series(False, index=self.lots.index)
        self.changed.iloc[n - 1] = True           # one lot rezoned elsewhere
        self.elig = pd.Series(True, index=self.lots.index)
        self.elig.iloc[n - 2] = False              # one ineligible lot

    def test_excluded_matches_uniform_rule(self):
        area, _ = C.uniform_areas(self.lots, self.in_reform, self.rose, self.lb, self.la, self.unc, self.changed, self.elig)
        ex = NE.excluded_by_uniform_rule(self.lots, self.in_reform, self.rose, self.lb, self.la, self.unc, self.changed, self.elig)
        self.assertTrue(area[ex].isna().all())
        self.assertTrue(ex.iloc[-1])
        self.assertEqual(int((area == C.TREAT).sum()), 9)

    def test_far_band(self):
        area, _ = C.uniform_areas(self.lots, self.in_reform, self.rose, self.lb, self.la, self.unc, self.changed, self.elig)
        ex = NE.excluded_by_uniform_rule(self.lots, self.in_reform, self.rose, self.lb, self.la, self.unc, self.changed, self.elig)
        far, dist = NE.far_land(self.lots, area, ex, self.elig)
        self.assertTrue((dist[far] > NE.FAR_MIN_M).all() and (dist[far] <= NE.FAR_MAX_M).all())
        self.assertFalse(far[area.isin([C.TREAT, C.COMP])].any())
        self.assertFalse(far.iloc[-1] or far.iloc[-2])   # rezoned elsewhere, ineligible
        lab = NE.three_areas(area, far)
        self.assertEqual(set(lab.dropna()), {C.TREAT, C.COMP, NE.FAR})

    def test_bind_args(self):
        a = NE.bind_uniform_args(self.lots, self.in_reform, self.rose, self.lb, self.la, self.unc, self.changed, self.elig)
        self.assertIs(a["parcels"], self.lots)
        self.assertIsNone(a["in_city"])


def permits_table():
    # treatment: +2 homes/yr per 1 acre; ring: -1 home/yr on 2 acres (-0.5/acre); far: flat on 10 acres
    rows = []
    for y in (1, 2):
        rows += [("t1", NE.TREAT, y, 1.0), ("r1", NE.RING, y, 3.0), ("f1", NE.FAR, y, 5.0)]
    for y in (3, 4):
        rows += [("t2", NE.TREAT, y, 3.0), ("r2", NE.RING, y, 2.0), ("f2", NE.FAR, y, 5.0)]
    return pd.DataFrame(rows, columns=["project", "area", "year", "units"]), {NE.TREAT: 1.0, NE.RING: 2.0, NE.FAR: 10.0}


class TestNet(unittest.TestCase):
    def test_arithmetic(self):
        p, a = permits_table()
        e = NE.net_estimate(p, a, [1, 2], [3, 4])
        self.assertAlmostEqual(e["treat_vs_far"], 2.0)
        self.assertAlmostEqual(e["ring_vs_far"], -0.5)        # borrowing: building moved out of the ring
        self.assertAlmostEqual(e["treat_vs_ring"], 2.5)
        self.assertAlmostEqual(e["net_homes_per_year"], 2.0 * 1.0 - 0.5 * 2.0)

    def test_bootstrap(self):
        p, a = permits_table()
        b1 = NE.bootstrap_net(p, a, [1, 2], [3, 4], draws=200)
        b2 = NE.bootstrap_net(p, a, [1, 2], [3, 4], draws=200)
        np.testing.assert_array_equal(b1["net_homes_per_year"], b2["net_homes_per_year"])
        lo, hi = NE.interval(b1["net_homes_per_year"])
        self.assertLessEqual(lo, hi)
        self.assertTrue(np.isfinite(lo))

    def test_stack(self):
        p, a = permits_table()
        m1 = {"id": "x", "effective_year": 2010, "permits": p.assign(year=p["year"] + 2008), "acres": a}
        m2 = {"id": "y", "effective_year": 2015, "permits": p.assign(year=p["year"] + 2013), "acres": a}
        s, acres = NE.stack_members([m1, m2])
        self.assertEqual(sorted(s["year"].unique()), [-1, 0, 1, 2])
        self.assertEqual(acres[NE.FAR], 20.0)
        self.assertEqual(s["project"].nunique(), 12)
        e = NE.net_estimate(s, acres, [-1, 0], [1, 2])
        self.assertAlmostEqual(e["net_homes_per_year"], 2 * (2.0 * 1.0 - 0.5 * 2.0))


class TestShapes(unittest.TestCase):
    def test_elongation(self):
        from shapely.geometry import Point, box
        self.assertAlmostEqual(NE.elongation(Point(0, 0).buffer(400, 64)), 4 / math.pi, places=2)
        self.assertAlmostEqual(NE.elongation(box(0, 0, 1000, 100)), 10.0, places=6)

    def test_corridor_share_and_sites(self):
        from shapely.geometry import box
        strip = [box(i * 100, 0, (i + 1) * 100, 50) for i in range(10)]          # 1,000 m long, touching lots
        node = [box(5000, 5000, 5200, 5200)]                                     # 200 m square
        share = NE.corridor_share(strip + node)
        self.assertAlmostEqual(share, 50000 / (50000 + 40000))
        self.assertEqual(NE.corridor_label(share), "corridor")
        self.assertEqual(NE.corridor_label(0.2), "nodes")
        self.assertAlmostEqual(NE.largest_contiguous_site_acres(strip + node), 50000 / C.SQM_PER_ACRE)
        across = [box(0, 0, 100, 50), box(0, 65, 100, 115)]                     # facing lots across a 15 m street
        self.assertEqual(len(NE.patches(across)), 1)
        self.assertEqual(len(NE.patches(across, close_m=NE.TOUCH_M)), 2)

    def test_island(self):
        import geopandas as gpd
        from shapely.geometry import box
        pc = gpd.GeoDataFrame({"patch_acres": [10.0, 99.0]}, geometry=[box(0, 0, 100, 100), box(500, 0, 2000, 1000)], crs=32616)
        self.assertEqual(NE.island_acres(box(600, 10, 700, 50), pc), 99.0)
        self.assertEqual(NE.island_acres(box(5000, 5000, 5100, 5100), pc), 0.0)

    def test_binding(self):
        acres = pd.Series([1.0, 1.0, 2.0])
        far = pd.Series([1.0, 1.0, np.inf])
        # allowed homes per acre at FAR 1 and 1,000 sq ft a home = 43.56; built 21.78 -> 0.5
        self.assertAlmostEqual(NE.binding_ratio(21.78, far, acres, 1000.0), 0.5)
        self.assertTrue(math.isnan(NE.binding_ratio(10.0, pd.Series([np.nan]), pd.Series([1.0]), 1000.0)))


class TestDistant(unittest.TestCase):
    def test_check(self):
        beyond = {1: 100.0, 2: 100.0, 3: 120.0, 4: 120.0}
        region = {1: 1000.0, 2: 1000.0, 3: 1500.0, 4: 1500.0}
        c = NE.distant_check(beyond, region, [1, 2], [3, 4])
        self.assertAlmostEqual(c["beyond_growth"], 1.2)
        self.assertAlmostEqual(c["region_growth"], 1.5)
        self.assertAlmostEqual(c["relative_growth_minus_1"], 1.2 / 1.5 - 1)
        self.assertTrue(math.isnan(NE.distant_check(beyond, {1: 5.0}, [1, 2], [3, 4])["region_growth"]))


class TestOutputs(unittest.TestCase):
    def test_no_identifiers(self):
        for f in ("tod_net_effect_by_case.csv", "tod_coverage_traits.csv", "tod_net_traits_test.csv"):
            p = REF / f
            if p.exists():
                self.assertEqual(T.check_private(pd.read_csv(p)), [], f)

    def test_by_case_rules(self):
        p = REF / "tod_net_effect_by_case.csv"
        if not p.exists():
            self.skipTest("not built")
        d = pd.read_csv(p)
        c = d[d["level"] == "case"].dropna(subset=["net_extra_homes_per_year"])
        net = c["did_treatment_vs_far"] * c["treatment_acres"] + c["borrowing_did_ring_vs_far"] * c["ring_acres"]
        np.testing.assert_allclose(net, c["net_extra_homes_per_year"], atol=0.05)
        self.assertTrue((c["net_low"] <= c["net_high"]).all())


if __name__ == "__main__":
    unittest.main()
