"""Out-of-state ADU permit series (missing_middleware/comparison/other_cities.py).
Offline; small synthetic fixtures in tests/fixtures/other_cities/, plus consistency
checks on the committed reference/other_cities_*.csv aggregates."""
import unittest
from pathlib import Path

import pandas as pd

from missing_middleware.comparison import other_cities as oc

FIX = Path(__file__).parent / "fixtures" / "other_cities"
REF = Path(__file__).resolve().parent.parent / "reference"


def fx(name, **kw):
    return pd.read_csv(FIX / name, dtype=str, **kw)


class TestTextRules(unittest.TestCase):
    def test_adu_word_boundaries(self):
        s = pd.Series(["New DADU", "AADU conversion", "gradual slope", "ADULT daycare", "Accessory Dwelling Unit",
                       "backyard cottage", None])
        self.assertEqual(oc.mentions_adu(s).tolist(), [True, True, False, False, True, True, False])

    def test_legalization_ignores_minneapolis_boilerplate(self):
        s = pd.Series(["ADU ****THIS PERMIT DOES NOT AUTHORIZE EXISTING FINISHES IF BUILT WITHOUT A PERMIT",
                       "Legalize existing basement unit", "as-built ADU", "new DADU"])
        self.assertEqual(oc.is_legalization(s).tolist(), [False, True, True, False])


class TestSeattle(unittest.TestCase):
    def setUp(self):
        self.p = oc.classify_seattle(fx("seattle.csv"), fx("seattle_houses.csv")).set_index("permit_id")

    def test_rows_kept(self):
        # S6 canceled, S7 no ADU type, S8 not a building permit
        self.assertEqual(sorted(self.p.index), ["S1", "S2", "S3", "S4", "S5"])

    def test_units_and_categories(self):
        self.assertEqual(self.p.loc["S2", "adu_units"], 2)          # ADU-only permit adding 2 units
        self.assertEqual(self.p.loc["S3", "adu_units"], 2)          # AADU + DADU listed with a new house
        self.assertEqual(self.p.loc["S3", "category"], "attached_and_detached")
        self.assertEqual(self.p.loc["S1", "category"], "detached")

    def test_exclusions(self):
        self.assertTrue(self.p.loc["S3", "with_new_house"])         # house on the same permit
        self.assertTrue(self.p.loc["S4", "with_new_house"])         # house permit at same address within 365 days
        self.assertFalse(self.p.loc["S1", "with_new_house"])        # house 8 years earlier
        self.assertTrue(self.p.loc["S5", "legalization"])
        self.assertEqual(self.p["counted"].sum(), 2)

    def test_opcd_table(self):
        t = oc.seattle_opcd_table().set_index("year")
        self.assertEqual(t.loc[2022, "total_units"], 924)
        self.assertEqual(t.loc[2019, "total_units"], 283)


class TestPortland(unittest.TestCase):
    def test_classify(self):
        p = oc.classify_portland(fx("portland.csv")).set_index("permit_id")
        self.assertEqual(sorted(p.index), ["P1", "P2", "P3", "P4"])  # outside city, no ADU flag, no issue date dropped
        self.assertEqual(p.loc["P1", "category"], "detached")
        self.assertEqual(p.loc["P2", "category"], "attached_or_conversion")
        self.assertTrue(p.loc["P3", "with_new_house"])
        self.assertTrue(p.loc["P4", "legalization"])
        self.assertEqual(int(p.loc["P1", "year"]), 2016)


class TestAustin(unittest.TestCase):
    def test_main_rule(self):
        p = oc.classify_austin(fx("austin.csv"), fx("austin_houses.csv")).set_index("permit_id")
        # A3 zero units / non-dwelling, A4 void, A5-A6 other classes, A7 electrical permit
        self.assertEqual(sorted(p.index), ["A1", "A2"])
        self.assertTrue(p.loc["A2", "with_new_house"])               # same parcel, same day
        self.assertFalse(p.loc["A1", "with_new_house"])              # house 3 years earlier
        self.assertEqual(p.loc["A1", "category"], "detached")

    def test_text_sensitivity(self):
        p = oc.classify_austin(fx("austin.csv"), fx("austin_houses.csv"), include_text=True).set_index("permit_id")
        self.assertIn("A5", p.index)
        self.assertNotIn("A6", p.index)                              # 'gradual' is not an ADU
        self.assertEqual(p.loc["A5", "category"], "attached_or_conversion")


class TestDenver(unittest.TestCase):
    def test_classify(self):
        raw = fx("denver.csv")
        raw["DATE_ISSUED"] = pd.to_numeric(raw["DATE_ISSUED"])
        p = oc.classify_denver(raw).set_index("permit_id")
        self.assertEqual(sorted(p.index), ["D1", "D2", "D4"])       # contractor change, cancelled, no 026 dropped
        self.assertEqual(p.loc["D1", "category"], "detached")
        self.assertEqual(p.loc["D2", "category"], "attached_or_conversion")
        self.assertTrue(p.loc["D4", "with_new_house"])
        self.assertFalse(p["legalization"].any())                    # cannot be screened


class TestMinneapolis(unittest.TestCase):
    def test_classify(self):
        raw = fx("minneapolis.csv")
        raw["issueDate"] = pd.to_numeric(raw["issueDate"])
        p = oc.classify_minneapolis(raw).set_index("permit_id")
        # M2 duplicate parcel within 24 months, M4 abandoned ADU, M5 plumbing permit
        self.assertEqual(sorted(p.index), ["M1", "M3", "M6"])
        self.assertFalse(p.loc["M1", "legalization"])
        self.assertTrue(p.loc["M3", "legalization"])
        self.assertEqual(p.loc["M1", "category"], "detached")
        self.assertEqual(p.loc["M6", "category"], "attached_or_conversion")


class TestSeriesAndRates(unittest.TestCase):
    def test_annual_series_zero_fill_and_counting(self):
        p = oc.classify_seattle(fx("seattle.csv"), fx("seattle_houses.csv"))
        s = oc.annual_series(p, range(2017, 2022)).set_index("year")
        self.assertEqual(s.loc[2017, "adu_units"], 0)                # covered year without permits
        self.assertEqual(s.loc[2018, "adu_units"], 3)                # S1 (1) + S2 (2)
        self.assertEqual(s.loc[2021, "adu_units"], 0)
        self.assertEqual(s.loc[2021, "excluded_with_new_house"], 3)  # S3 (2) + S4 (1)
        self.assertEqual(s.loc[2021, "excluded_legalization"], 1)

    def test_period_rate_math_and_missing_years(self):
        series = pd.DataFrame({"city": ["x"] * 3, "year": [2020, 2021, 2022], "adu_units": [10.0, None, 30.0]})
        r = oc.period_rates(series, {"x": 20000}, [oc.Period("x", "p", 2020, 2022, "r")]).iloc[0]
        self.assertEqual(r.years_observed, 2)
        self.assertEqual(r.years_missing, 1)
        self.assertAlmostEqual(r.rate_per_1000_yr, 1.0)              # 40 / (20 x 2)
        self.assertLess(r.poisson95_lo, 1.0)
        self.assertGreater(r.poisson95_hi, 1.0)

    def test_poisson_interval_continuity(self):
        lo50, hi50 = oc.poisson_interval(50)
        lo51, hi51 = oc.poisson_interval(51)
        self.assertTrue(lo50 < lo51 < 51 < hi51 and hi50 < hi51)
        lo, hi = oc.poisson_interval(1000)
        self.assertAlmostEqual(lo, 938.97, delta=0.5)
        self.assertAlmostEqual(hi, 1063.95, delta=0.5)


class TestReference(unittest.TestCase):
    def test_reforms(self):
        r = pd.read_csv(REF / "other_cities_reforms.csv")
        sea = r[r.measure.str.contains("125854")].iloc[0]
        self.assertEqual(sea.effective, "2019-08-08")
        self.assertTrue({"seattle", "portland", "austin", "denver", "minneapolis", "washington", "oregon",
                         "colorado"} <= set(r.jurisdiction))
        self.assertTrue(r.source.str.len().gt(10).all())

    def test_seattle_open_data_matches_official_report(self):
        a = pd.read_csv(REF / "other_cities_annual.csv")
        s = a[(a.city == "seattle") & a.year.between(2010, 2024)]
        rel = (s.units_incl_new_house - s.published_units).abs() / s.published_units
        self.assertLess(rel.max(), 0.03)

    def test_missing_is_never_zero(self):
        a = pd.read_csv(REF / "other_cities_annual.csv")
        bad = a[a.status != "observed"]
        self.assertTrue(bad.adu_units.isna().all())
        self.assertTrue(a[a.status == "observed"].adu_units.notna().all())

    def test_points(self):
        p = pd.read_csv(REF / "other_cities_points.csv", dtype={"geoid": str})
        self.assertEqual(set(p.city), {"seattle", "portland", "austin", "denver", "minneapolis"})
        for c in ["plateau_rate", "value", "rent", "homes", "suggested_use", "caveat"]:
            self.assertTrue(p[c].notna().all(), c)
        row = p.set_index("city").loc["austin"]
        self.assertEqual(row.plateau_years_observed, 1)              # HOME category break

    def test_acs_denominators(self):
        acs = pd.read_csv(REF / "other_cities_acs.csv", dtype={"geoid": str}).set_index("city")
        self.assertEqual(acs.loc["madison", "homes"], 53292)          # same vintage as Wisconsin baseline
        self.assertTrue((acs.homes < acs.all_units).all())


if __name__ == "__main__":
    unittest.main()
