"""All-housing baseline (missing_middleware/housing_baseline.py). Offline: synthetic inputs,
plus checks on the committed reference/housing_baseline_*.csv outputs."""
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware import housing_baseline as hb

REF = Path(__file__).resolve().parent.parent / "reference"


def bps_rows():
    """Two years; place A exact, place B split across two county pieces, a county row for
    two towns, and an unmatched place C. Place A has a known gap in 2021."""
    base = dict(reporting_status="reported_12_months")
    rows = []
    for y in (2020, 2021):
        rows += [
            dict(bps_id="A", county_fips="001", fips_mcd="1", fips_place="1", year=y, name="A",
                 **{"1unit_units": 10, "2units_units": 2, "3_4units_units": 4, "5plus_units": 100 if y == 2020 else 0}, **base),
            dict(bps_id="B", county_fips="001", fips_mcd="2", fips_place="2", year=y, name="B",
                 **{"1unit_units": 20, "2units_units": 0, "3_4units_units": 0, "5plus_units": 50}, **base),
            dict(bps_id="CO", county_fips="001", fips_mcd="0", fips_place="99990", year=y, name="County",
                 **{"1unit_units": 8, "2units_units": 0, "3_4units_units": 0, "5plus_units": 0}, **base),
            dict(bps_id="C", county_fips="001", fips_mcd="9", fips_place="9", year=y, name="C",
                 **{"1unit_units": 1, "2units_units": 0, "3_4units_units": 0, "5plus_units": 0}, **base),
        ]
    return pd.DataFrame(rows)


def crosswalk():
    return pd.DataFrame([
        dict(bps_id="A", bps_county_fips="001", fips_mcd="1", fips_place="1", match_type="exact",
             area_id="muni:A", alloc_share=1.0, n_pieces=1),
        dict(bps_id="B", bps_county_fips="001", fips_mcd="2", fips_place="2", match_type="multi_county",
             area_id="muni:B1", alloc_share=0.75, n_pieces=2),
        dict(bps_id="B", bps_county_fips="001", fips_mcd="2", fips_place="2", match_type="multi_county",
             area_id="muni:B2", alloc_share=0.25, n_pieces=2),
        dict(bps_id="CO", bps_county_fips="001", fips_mcd="0", fips_place="99990", match_type="county_unincorporated",
             area_id="muni:T1", alloc_share=np.nan, n_pieces=2),
        dict(bps_id="C", bps_county_fips="001", fips_mcd="9", fips_place="9", match_type="unmatched",
             area_id=None, alloc_share=np.nan, n_pieces=0),
    ])


def county_alloc():
    return pd.DataFrame([dict(year=y, bps_id="CO", bps_county_fips="001", fips_mcd="0", fips_place="99990",
                              area_id=a, alloc_share=s) for y in (2020, 2021) for a, s in (("muni:T1", 0.5), ("muni:T2", 0.5))])


def state(extra=0.0):
    b = bps_rows()
    rows = []
    for t, c in hb.BPS_UNIT_COLS.items():
        for y, g in b.groupby("year"):
            rows.append(dict(year=y, structure_type=t, units=float(g[c].sum()) + (extra if t == "1unit" else 0.0)))
    return pd.DataFrame(rows)


class TestAllocation(unittest.TestCase):
    def setUp(self):
        self.long = hb.long_bps(bps_rows(), {("A", 2021): True})
        self.alloc = hb.allocate(self.long, crosswalk(), county_alloc())

    def test_gap_is_null_not_zero(self):
        a = self.alloc[(self.alloc["area_id"] == "muni:A") & (self.alloc["year"] == 2021)].set_index("structure_type")["units"]
        self.assertTrue(np.isnan(a["5plus"]))
        self.assertTrue(np.isnan(a["3_4units"]))
        self.assertEqual(a["2units"], 2.0)   # 2-unit kept in gap years
        self.assertEqual(a["1unit"], 10.0)

    def test_split_and_county_rows(self):
        g = self.alloc[(self.alloc["year"] == 2020) & (self.alloc["structure_type"] == "5plus")].set_index("area_id")["units"]
        self.assertAlmostEqual(g["muni:B1"], 37.5)
        self.assertAlmostEqual(g["muni:B2"], 12.5)
        one = self.alloc[(self.alloc["year"] == 2020) & (self.alloc["structure_type"] == "1unit")].set_index("area_id")["units"]
        self.assertAlmostEqual(one["muni:T1"], 4.0)
        self.assertAlmostEqual(one["muni:T2"], 4.0)
        self.assertAlmostEqual(one[hb.UNALLOCATED], 1.0)   # unmatched place

    def test_reconciles_to_state(self):
        r = hb.reconcile(self.alloc, state(extra=5.0))
        tot = r.groupby(["year", "structure_type"])["units"].sum()
        s = state(extra=5.0).set_index(["year", "structure_type"])["units"]
        for k in s.index:
            self.assertAlmostEqual(tot[k], s[k])
        un = r[(r["area_id"] == hb.UNALLOCATED) & (r["year"] == 2020) & (r["structure_type"] == "1unit")]["units"].sum()
        self.assertAlmostEqual(un, 6.0)   # 1 unmatched + 5 state excess


def synthetic_hist(levels, years=range(2015, 2026)):
    rows = [dict(area_id=a, year=y, structure_type=t, units=float(v(y) if callable(v) else v))
            for a, v in levels.items() for y in years for t in hb.TYPES]
    return pd.DataFrame(rows)


class TestProjection(unittest.TestCase):
    def test_flat_mean_skips_nulls(self):
        h = synthetic_hist({"a": 10})
        h.loc[(h["year"] == 2025) & (h["structure_type"] == "5plus"), "units"] = np.nan
        h.loc[(h["year"] == 2024) & (h["structure_type"] == "5plus"), "units"] = 40
        m = hb.flat_mean(h, 2025, 3)
        self.assertAlmostEqual(m[("a", "5plus")], 25.0)   # (10 + 40) / 2, not / 3
        self.assertAlmostEqual(m[("a", "1unit")], 10.0)

    def test_holdout_perfect_on_constant_series(self):
        h = synthetic_hist({"a": 10, "b": 30})
        s = hb.holdout_scores(h)
        flat = s[s["candidate"].str.startswith("flat")]
        self.assertTrue(np.allclose(flat["area_wape"], 0.0))
        self.assertTrue(np.allclose(flat["state_ratio"], 1.0))

    def test_trend_candidate_wins_on_linear_growth(self):
        h = synthetic_hist({"a": lambda y: 10 * (y - 2010), "b": lambda y: 20 * (y - 2010)})
        best, summ = hb.choose(hb.holdout_scores(h))
        self.assertTrue(best.startswith("trend"))
        self.assertEqual(int(summ["chosen"].sum()), 1)

    def test_project_band_contains_central(self):
        h = synthetic_hist({"a": 10})
        bands = pd.DataFrame({"structure_type": list(hb.TYPES), "low": 0.5, "high": 1.4})
        p = hb.project(h, "flat_3y", bands)
        self.assertEqual(sorted(p["year"].unique()), [hb.BRIDGE_YEAR] + list(hb.FORECAST_YEARS))
        self.assertTrue((p["low"] <= p["central"]).all() and (p["central"] <= p["high"]).all())
        self.assertAlmostEqual(p[p["in_five_year_total"]]["central"].sum(), 10 * 4 * 5)

    def test_long_run_band(self):
        st = pd.DataFrame([dict(year=y, structure_type=t, units=100.0 if y < 2010 else 50.0)
                           for y in range(2000, 2020) for t in hb.TYPES])
        r = hb.state_long_run_ratios(st, 3)
        b = hb.long_run_band(r).set_index("structure_type")
        self.assertAlmostEqual(b.loc["5plus", "worst"], 0.5)
        self.assertLessEqual(b.loc["5plus", "low"], 1.0)
        self.assertGreaterEqual(b.loc["5plus", "high"], 1.0)


@unittest.skipUnless((REF / "housing_baseline_reconciliation.csv").exists(), "baseline not built")
class TestCommittedOutputs(unittest.TestCase):
    def test_history_reconciles_to_state(self):
        r = pd.read_csv(REF / "housing_baseline_reconciliation.csv")
        self.assertTrue(np.allclose(r["check_sum"], r["state_published"]))
        h = pd.read_csv(REF / "housing_baseline_history.csv")
        for t in hb.TYPES:
            s = h.groupby("year")[f"units_{t}"].sum()
            pub = r[r["structure_type"] == t].set_index("year")["state_published"]
            self.assertTrue(np.allclose(s.loc[pub.index], pub, atol=0.01), t)

    def test_milwaukee_gaps_are_null(self):
        h = pd.read_csv(REF / "housing_baseline_history.csv", dtype={"area_id": str})
        m = h[(h["area_id"] == "muni:5507953000") & h["year"].isin([2020, 2023, 2025])]
        self.assertTrue(m["units_5plus"].isna().all())
        self.assertTrue(m["units_1unit"].notna().all())

    def test_statewide_projection_is_sum_of_areas(self):
        a = pd.read_csv(REF / "housing_baseline_by_area.csv")
        s = pd.read_csv(REF / "housing_baseline_statewide_by_year.csv")
        five = s[s["year"].isin(hb.FORECAST_YEARS) & (s["structure_type"] == "all")]["central"].sum()
        self.assertAlmostEqual(a["five_year_central"].sum(), five, delta=1.0)
        self.assertTrue((a["five_year_low"] <= a["five_year_central"] + 1e-6).all())
        self.assertTrue((a["five_year_central"] <= a["five_year_high"] + 1e-6).all())

    def test_chosen_candidate_recorded(self):
        w = pd.read_csv(REF / "housing_baseline_window_choice.csv")
        self.assertEqual(int(w["chosen"].sum()), 1)
        a = pd.read_csv(REF / "housing_baseline_by_area.csv")
        self.assertEqual(set(a["method"]), set(w.loc[w["chosen"], "candidate"]))


if __name__ == "__main__":
    unittest.main()
