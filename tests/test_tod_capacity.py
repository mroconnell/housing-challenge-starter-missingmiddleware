"""Offline tests for the TOD station-area capacity method (no network).

Fixtures in tests/fixtures/tod/capacity/ are synthetic: a small zoning rule table, three stops and
one-acre square lots in EPSG:3071 metres. The committed outputs in reference/ are checked for privacy
and for totals that reconcile."""
import csv
import math
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.tod import capacity as C  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "tod" / "capacity"
REF = ROOT / "reference"


def read(path: Path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


class TestCapacityFormula(unittest.TestCase):
    def test_basic_gain(self):
        # 2 acres, law 80/acre, current 10/acre, 3 existing homes: 160 - max(20, 3) = 140
        self.assertEqual(C.capacity_gain(2.0, 80, 10, 3), 140)

    def test_no_double_subtraction(self):
        # Existing homes above the current allowance: subtract the larger of the two, once.
        # 80 - max(40, 50) = 30, not 80 - 40 - 50.
        self.assertEqual(C.capacity_gain(1.0, 80, 40, 50), 30)
        self.assertEqual(C.capacity_gain(1.0, 80, 40, 10), 40)

    def test_already_at_or_above_law_gives_zero(self):
        self.assertEqual(C.capacity_gain(1.0, 80, 80, 0), 0)
        self.assertEqual(C.capacity_gain(1.0, 80, 124, 0), 0)
        self.assertEqual(C.capacity_gain(1.0, 80, 10, 200), 0)

    def test_existing_is_rule(self):
        self.assertEqual(C.capacity_gain(1.0, 80, None, 12), 68)

    def test_law_parameters_in_one_place(self):
        self.assertEqual(C.MODELLED_LAW["rapid_quarter"], C.LawRule(65, 3.0, 100))
        self.assertEqual(C.MODELLED_LAW["rapid_half"], C.LawRule(55, 2.5, 80))
        self.assertEqual(C.MODELLED_LAW["bus15_quarter"], C.LawRule(55, 2.5, 80))
        # At 1,000 sq ft per home FAR 3.0 allows 130.7 homes per acre, so the density binds
        self.assertEqual(C.law_homes_per_acre("rapid_quarter", sqft_per_home=1000), 100)
        self.assertEqual(C.law_homes_per_acre("bus15_quarter", sqft_per_home=1000), 80)
        # At Madison's measured 1,512 sq ft the FAR binds: 3.0 x 43,560 / 1,512 = 86.4
        self.assertAlmostEqual(C.law_homes_per_acre("rapid_quarter", sqft_per_home=1512), 3.0 * 43560 / 1512)

    def test_measured_floor_area(self):
        self.assertEqual(C.sqft_per_home_for("Madison city"), C.MEASURED_SQFT_PER_HOME["Madison city"])
        self.assertEqual(C.sqft_per_home_for("Wauwatosa city"), C.MEASURED_SQFT_PER_HOME["pooled"])
        self.assertEqual(C.SENSITIVITY_SQFT_PER_HOME, 1000)
        path = REF / "tod_floor_area_per_home.csv"
        if path.exists():  # the constants match the committed measurement
            for r in read(path):
                self.assertAlmostEqual(float(r["median_sqft_per_home"]), C.MEASURED_SQFT_PER_HOME[r["area"]], delta=1)
                self.assertGreater(int(r["buildings"]), 50)

    def test_fallback_capacity(self):
        r = C.fallback_capacity(2.0, "bus15_quarter", "single_family_est", 6, sqft_per_home=1000)
        self.assertTrue(r.eligible)
        self.assertEqual(r.capacity_gain, 160 - 6)  # current allowance = existing homes
        self.assertEqual(r.current_allowed_homes, 6)
        self.assertFalse(C.fallback_capacity(2.0, "bus15_quarter", "institutional", 0).eligible)
        self.assertEqual(C.fallback_capacity(1.0, "bus15_quarter", "commercial", 500).capacity_gain, 0)


class TestBands(unittest.TestCase):
    Q, H = C.QUARTER_M, C.HALF_M

    def test_band_order(self):
        inf = math.inf
        self.assertEqual(C.assign_band(100, 100, 100), "rapid_quarter")
        self.assertEqual(C.assign_band(self.Q + 1, 50, 50), "rapid_half")  # rapid outer ring beats bus
        self.assertEqual(C.assign_band(inf, self.Q, self.Q), "bus15_quarter")
        self.assertEqual(C.assign_band(inf, self.Q + 1, self.Q), "bus20_quarter")
        self.assertEqual(C.assign_band(inf, self.H, inf), "bus15_half")
        self.assertEqual(C.assign_band(inf, inf, self.H), "bus20_half")
        self.assertIsNone(C.assign_band(self.H + 1, self.H + 1, self.H + 1))

    def test_definitions(self):
        self.assertEqual(C.DEFINITION_BANDS["main"], {"rapid_quarter", "rapid_half", "bus15_quarter"})
        self.assertTrue(C.DEFINITION_BANDS["main"] < C.DEFINITION_BANDS["high"])
        self.assertTrue(C.DEFINITION_BANDS["main"] < C.DEFINITION_BANDS["b_half"])
        self.assertEqual(C.DEFINITION_BANDS["c_half"], set(C.BANDS))


class TestDistrictRules(unittest.TestCase):
    def setUp(self):
        self.rows = read(FIX / "rules_small.csv")
        self.base = C.rule_table(self.rows, sqft_per_home=1000)
        self.over = C.rule_table(self.rows, tod_overlay=True, sqft_per_home=1000)

    def test_lot_area_per_home(self):
        self.assertAlmostEqual(self.base["LOW"].homes_per_acre, 10.0)

    def test_far_cap(self):
        # 40 homes per acre printed; 3 stories x 50% coverage = FAR 1.5 = 65.3 homes per acre, so 40 binds
        self.assertAlmostEqual(self.base["MID"].homes_per_acre, 40.0)
        self.assertAlmostEqual(self.base["MID"].far, 1.5)

    def test_far_only_and_overlay(self):
        self.assertAlmostEqual(self.base["TALL"].homes_per_acre, 1.0 * C.SQFT_PER_ACRE / 1000)
        self.assertAlmostEqual(self.over["TALL"].far, 4.0)
        self.assertEqual(self.over["LOW"], self.base["LOW"])  # no overlay column: unchanged

    def test_eligibility(self):
        self.assertTrue(C.is_eligible("residential", "single_family", "density"))  # single-family counts
        for use in ("institutional", "park_open_space", "cemetery", "utility_transport", "water"):
            self.assertFalse(C.is_eligible("residential", use, "density"))
        self.assertFalse(C.is_eligible("industrial", "vacant", "not_eligible"))

    def test_committed_rule_tables_parse_and_cite(self):
        for city in ("milwaukee", "madison"):
            rows = read(REF / f"tod_zoning_rules_{city}.csv")
            self.assertGreater(len(rows), 30)
            seen = set()
            for r in rows:
                self.assertNotIn(r["district"], seen)
                seen.add(r["district"])
                self.assertIn(r["status"], {"verified", "source_lead"}, r)
                self.assertTrue(r["source_url"].startswith("https://") or r["rule_type"] == "not_coded", r)
                self.assertTrue(r["code_section"] or r["rule_type"] == "not_coded", r)
                rule = C.district_rule(r)
                if r["rule_type"] in ("density", "far"):
                    self.assertGreater(rule.homes_per_acre, 0)
        mke = C.rule_table(read(REF / "tod_zoning_rules_milwaukee.csv"), sqft_per_home=1000)
        self.assertAlmostEqual(mke["RT5"].homes_per_acre, 43560 / 800)  # file 240997
        self.assertAlmostEqual(mke["RT4"].homes_per_acre, 43560 / 1200)
        mad = C.rule_table(read(REF / "tod_zoning_rules_madison.csv"), sqft_per_home=1000)
        self.assertEqual(mad["TR-U2"].homes_per_acre, 124)  # 6 stories: printed density binds
        self.assertAlmostEqual(mad["TSS"].homes_per_acre, 3 * C.DEFAULT_LOT_COVERAGE * 43.56)  # 3 stories: FAR binds


class TestSyntheticBuild(unittest.TestCase):
    """End to end on synthetic lots: bands, per-lot capacity, aggregation and reconciliation."""

    @classmethod
    def setUpClass(cls):
        import geopandas as gpd
        import pandas as pd
        from shapely.geometry import box

        import build_tod_station_areas as B

        cls.B = B
        s = pd.read_csv(FIX / "stops_small.csv")
        g = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.x, s.y), crs=3071)
        stops = {"rapid": g[g.flag_a_rapid == 1], "bus15": g[g.flag_b_15min == 1], "bus20": g[g.flag_c_20min == 1]}
        p = pd.read_csv(FIX / "parcels_small.csv", dtype={"expect_band": str}, keep_default_na=False)
        cls.expect = dict(zip(p.lot, p.expect_band))
        geom = [box(x - h / 2, y - h / 2, x + h / 2, y + h / 2) for x, y, h in zip(p.x, p.y, p.side_m)]
        p = gpd.GeoDataFrame(p, geometry=geom, crs=3071)
        p["pt"] = p.geometry.representative_point()
        p["in_overlay"] = p.in_overlay.astype(bool)
        p["homes"] = p.homes.astype(float)
        cls.parcels = B.compute(p, "Test city", read(FIX / "rules_small.csv"), stops, sqft_per_home=1000)
        # Same lots as a not-coded place: current allowance = existing homes
        cls.fallback = B.compute(p.assign(use_class=p.use_class.replace({"single_family": "single_family_est",
                                                                          "multifamily": "residential"})),
                                 "Fallback town", None, stops, sqft_per_home=1000)
        cls.agg = B.aggregate(cls.parcels)

    def by_lot(self):
        return {r.lot: r for r in self.parcels.itertuples(index=False)}

    def test_bands(self):
        got = {r.lot: r.band for r in self.parcels.itertuples(index=False)}
        want = {k: v for k, v in self.expect.items() if v}
        self.assertEqual(got, want)  # lot n (beyond 1/2 mile) is dropped

    def test_per_lot_capacity(self):
        L = self.by_lot()
        expected = {"a": 90, "b": 70, "c": 30, "d": 0, "e": 0, "g": 70, "h": 68, "i": 80, "j": 0}
        for lot, gain in expected.items():
            self.assertAlmostEqual(L[lot].capacity_gain, gain, places=1, msg=lot)
        self.assertAlmostEqual(L["f"].capacity_gain, 80 - C.SQFT_PER_ACRE / 1000, places=1)
        self.assertAlmostEqual(L["f"].added_floor_area_sqft, 1.5 * C.SQFT_PER_ACRE, delta=50)
        for lot in "klmo":  # industrial zoning, institution, park, uncoded zoning
            self.assertFalse(L[lot].eligible, lot)
            self.assertEqual(L[lot].capacity_gain, 0)
        self.assertEqual(L["o"].rule_type, "not_coded")

    def test_aggregate_reconciles(self):
        a, p = self.agg, self.parcels
        self.assertAlmostEqual(a.capacity_gain.sum(), p.capacity_gain.sum(), places=0)
        self.assertAlmostEqual(a.acres.sum(), p.acres.sum(), places=2)
        main = a[a.in_main == 1]
        self.assertAlmostEqual(main.capacity_gain.sum(), 90 + 70 + 30 + (80 - 43.56), places=0)
        self.assertAlmostEqual(main.eligible_acres.sum(), 7.0, places=2)
        for keys in (["band"], ["district"], ["use_class"], ["band", "district", "use_class"]):
            self.assertAlmostEqual(a.groupby(keys).capacity_gain.sum().sum(), a.capacity_gain.sum(), places=6)
        self.assertAlmostEqual(a.eligible_acres_in_overlay.sum(), 1.0, places=2)

    def test_sensitivities(self):
        L = self.by_lot()
        # sensitivity column equals the main value when the main run already uses 1,000 sq ft
        self.assertAlmostEqual(L["a"].capacity_gain_sqft1000, L["a"].capacity_gain)
        a = self.agg
        sf = a[a.use_class == "single_family"]
        self.assertTrue((sf.capacity_gain_excl_single_family == 0).all())
        self.assertAlmostEqual(a.capacity_gain_excl_single_family.sum(), a.capacity_gain.sum() - sf.capacity_gain.sum())

    def test_fallback_rows(self):
        F = {r.lot: r for r in self.fallback.itertuples(index=False)}
        self.assertAlmostEqual(F["a"].capacity_gain, 100 - 1, places=2)      # single family, law 100, existing 1
        self.assertAlmostEqual(F["c"].capacity_gain, 80 - 50, places=2)      # current = existing 50
        self.assertAlmostEqual(F["d"].capacity_gain, 80 - 30, places=2)      # coded HIGH zoning ignored when not coded
        self.assertFalse(F["l"].eligible)
        self.assertTrue((self.fallback.zoning_coded == 0).all())
        agg = self.B.aggregate(self.fallback)
        self.assertEqual(set(agg.rule_type), {"existing_density_fallback"})
        self.assertAlmostEqual(agg.capacity_gain.sum(), self.fallback.capacity_gain.sum(), places=3)

    def test_madison_test_land(self):
        import pandas as pd

        p = self.parcels.copy()
        p["dist_overlay_m"] = [0.0 if o else 1000.0 for o in p.in_overlay]
        t = self.B.madison_test_land(p, read(FIX / "rules_small.csv"))
        self.assertEqual(list(t.area), ["overlay", "ring_quarter_mile_outside", "rest_of_city"])
        self.assertTrue((t.eligible_acres <= t.eligible_acres_incl_single_family + 1e-9).all())
        # single-family lots a and b are excluded from the pre-registered definition
        self.assertAlmostEqual(float(t.single_family_acres_excluded.sum()), 2.0, places=2)
        self.assertNotIn("permits", " ".join(t.columns))
        self.assertIsInstance(t, pd.DataFrame)


class TestUseClasses(unittest.TestCase):
    def test_milwaukee(self):
        import build_tod_station_areas as B

        self.assertEqual(B.mke_use_class("1", "8810"), "single_family")
        self.assertEqual(B.mke_use_class("11", "6553"), "cemetery")
        self.assertEqual(B.mke_use_class("9", "7523"), "parking")
        self.assertEqual(B.mke_use_class("9", "4010"), "utility_transport")
        self.assertEqual(B.mke_use_class("12", "8870"), "park_open_space")

    def test_madison(self):
        import build_tod_station_areas as B

        self.assertEqual(B.mad_use_class("Single family"), "single_family")
        self.assertEqual(B.mad_use_class("Commercial exempt"), "institutional")
        self.assertEqual(B.mad_use_class("C-2 parking lot"), "parking")
        self.assertEqual(B.mad_use_class("Condominium"), "condominium")
        self.assertEqual(B.mad_base_district("WP-13, SR-V2", {"SR-V2"}), "SR-V2")


class TestCommittedOutputs(unittest.TestCase):
    FILES = ("tod_station_areas.csv", "tod_madison_test_land.csv", "tod_zoning_rules_milwaukee.csv",
             "tod_zoning_rules_madison.csv", "tod_station_area_summary.csv", "tod_floor_area_per_home.csv")
    ID_LIKE = re.compile(r"(?<![\d.])\d{8,}(?![\d.])")  # Milwaukee tax keys are 10 digits, Madison parcels 12

    def test_no_parcel_ids(self):
        for name in self.FILES:
            path = REF / name
            if not path.exists():
                self.skipTest(f"{name} not built")
            rows = read(path)
            for col in rows[0]:
                for bad in ("parcel", "taxkey", "owner", "address", "geometry", "lat", "lon"):
                    self.assertNotEqual(col.lower(), bad, name)
                    self.assertFalse(col.lower().startswith(bad + "_"), (name, col))
            for r in rows:
                for col, cell in r.items():
                    if cell.startswith("https://") or col in ("added_floor_area_sqft", "source"):
                        continue  # URLs carry capture timestamps; floor area is a large sum, not an id
                    self.assertIsNone(self.ID_LIKE.search(cell), (name, col, cell))

    def test_station_areas_reconcile(self):
        import pandas as pd

        path = REF / "tod_station_areas.csv"
        if not path.exists():
            self.skipTest("not built")
        a = pd.read_csv(path)
        self.assertTrue({"Milwaukee city", "Madison city"} <= set(a.city))
        self.assertEqual(set(a[a.zoning_coded == 1].city), {"Milwaukee city", "Madison city"})
        self.assertTrue((a[a.zoning_coded == 0].rule_type == "existing_density_fallback").all())
        self.assertTrue((a.capacity_gain_excl_single_family <= a.capacity_gain + 0.5).all())
        s = pd.read_csv(REF / "tod_station_area_summary.csv")
        main = s[s.definition == "main"].set_index("area")
        parts = main.loc[["Milwaukee city", "Madison city", "Not coded (fallback places)"], "capacity_gain"].sum()
        self.assertAlmostEqual(parts, main.loc["State total", "capacity_gain"], delta=1)
        self.assertAlmostEqual(main.loc["State total", "capacity_gain"], a[a.in_main == 1].capacity_gain.sum(), delta=1)
        self.assertTrue((a.eligible_acres <= a.acres + 1e-6).all())
        self.assertTrue((a.capacity_gain >= 0).all())
        self.assertTrue((a[a.eligible == 0].capacity_gain == 0).all())
        self.assertTrue((a.capacity_gain <= a.law_allowed_homes + 0.5).all())
        for d, bands in C.DEFINITION_BANDS.items():
            self.assertTrue(((a[f"in_{d}"] == 1) == a.band.isin(bands)).all(), d)
        m = a[a.in_main == 1]
        total = m.groupby("city").capacity_gain.sum()
        for keys in (["city", "band"], ["city", "district"], ["city", "use_class"], ["city", "zoning_class"]):
            g = m.groupby(keys).capacity_gain.sum().groupby(level=0).sum()
            pd.testing.assert_series_equal(g.sort_index(), total.sort_index(), check_names=False)
        self.assertEqual(a[a.city == "Milwaukee city"].acres_in_overlay.sum(), 0)
        t = pd.read_csv(REF / "tod_madison_test_land.csv")
        self.assertEqual(list(t.area), ["overlay", "ring_quarter_mile_outside", "rest_of_city"])
        self.assertFalse(any("permit" in c for c in t.columns))


if __name__ == "__main__":
    unittest.main()
