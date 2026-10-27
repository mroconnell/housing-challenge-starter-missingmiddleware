"""Offline tests for the TOD Gate 3 model (docs/tod/GATE3_MODEL_SPEC.md section 8; docs/tod/MODEL.md).

Unit tests of the pure functions in missing_middleware/tod/model.py, plus checks on the committed
outputs in reference/: nothing negative, land at the law adds zero, areas add up to counties,
districts and the state, the baseline matches the shared baseline's near-stop split, the Madison
predictions exist and the run script never reads Madison permits, and no parcel ids are committed."""
import math
import re
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from missing_middleware.tod import model as M  # noqa: E402

REF = ROOT / "reference"
GAPS = [0.33, 0.31, 0.89, 1.61, 0.22]


class TestRamp(unittest.TestCase):
    def test_ramp_averages_one_and_keeps_shape(self):
        r = M.ramp_from_gaps(GAPS)
        self.assertAlmostEqual(sum(r) / 5, 1.0)
        for a, g in zip(r, GAPS):
            self.assertAlmostEqual(a * np.mean(GAPS), g)

    def test_year5_alternative_replaces_only_year5(self):
        base, alt = M.ramp_from_gaps(GAPS), M.ramp_year5_alternative(GAPS)
        self.assertEqual(base[:4], alt[:4])
        self.assertAlmostEqual(alt[4], np.mean(GAPS[2:5]) / np.mean(GAPS))


class TestMethodA(unittest.TestCase):
    def test_formula(self):
        # 10 eligible acres x 1.5 added FAR x r 0.5 x ramp 1 = 7.5 homes per year
        add = M.method_a_addition(10 * 1.5 * M.SQFT_PER_ACRE, 0.5, [1, 1, 1, 1, 1])
        self.assertTrue(np.allclose(add, 7.5))

    def test_land_at_the_law_adds_zero_and_never_negative(self):
        self.assertTrue(np.all(M.method_a_addition(0.0, 0.67, M.ramp_from_gaps(GAPS)) == 0))
        self.assertTrue(np.all(M.method_a_addition(-5e6, 0.67, M.ramp_from_gaps(GAPS)) == 0))

    def test_fallback_floor_area_identity(self):
        self.assertEqual(M.fallback_added_floor_area(100, 1467), 146_700)
        self.assertEqual(M.fallback_added_floor_area(-3, 1467), 0)


class TestMethodB(unittest.TestCase):
    P = M.FeasibilityParams(cap_rate=0.05, opex_ratio=0.4, cost_per_sqft=200, sqft_per_home=1000)

    def test_value_cost_and_break_even(self):
        self.assertAlmostEqual(M.value_per_home(2000, self.P), 12 * 2000 * 0.6 / 0.05)
        self.assertEqual(M.cost_per_home(self.P), 200_000)
        be = M.break_even_rent(self.P)
        self.assertAlmostEqual(M.value_per_home(be, self.P), M.cost_per_home(self.P))

    def test_feasibility_includes_land(self):
        # value 288,000 - cost 200,000 = 88,000 margin per home; 10 homes: 880,000
        f = M.is_feasible(np.array([10, 10, 0]), np.array([2000, 2000, 2000]), np.array([800_000, 900_000, 0]), self.P)
        self.assertEqual(f.tolist(), [True, False, False])

    def test_take_up_without_feasible_capacity_is_undefined(self):
        self.assertTrue(math.isnan(M.take_up_rate(100, 8, 0)))
        self.assertTrue(np.all(np.isnan(M.method_b_addition(500, float("nan"), [1] * 5))))
        self.assertAlmostEqual(M.take_up_rate(80, 8, 1000), 0.01)

    def test_bootstrap_brackets_point(self):
        lo, hi = M.bootstrap_take_up([10, 50, 200, 5], 8, 5000)
        tu = M.take_up_rate(265, 8, 5000)
        self.assertLessEqual(lo, tu)
        self.assertGreaterEqual(hi, tu)


def read(name):
    return pd.read_csv(REF / name, dtype={"area_id": str})


class TestOutputs(unittest.TestCase):
    """Per-acre sizing (method A), now a sensitivity: reference/tod_model_per_acre_*.csv."""

    @classmethod
    def setUpClass(cls):
        cls.area = read("tod_model_per_acre_by_area.csv")
        cls.state = read("tod_model_per_acre_statewide.csv")
        cls.add_cols = [f"add_{y}" for y in range(2027, 2032)] + ["add_2027_2031"]

    def test_no_negative_additions(self):
        for df, cols in ((self.area, self.add_cols), (self.state, ["addition"])):
            self.assertTrue(M.check_no_negative(df[cols].to_numpy().ravel()))

    def test_land_at_the_law_adds_zero(self):
        a = self.area[self.area.method == "A"]
        z = a[a.added_far_acres <= 0]
        self.assertTrue((z.add_2027_2031.fillna(0) == 0).all())
        b = self.area[self.area.method == "B"]
        self.assertTrue((b[b.feasible_capacity_gain <= 0].add_2027_2031.fillna(0) == 0).all())

    def test_areas_add_to_state(self):
        tot = self.state[self.state.year == "2027-2031"].set_index(["method", "scenario"])
        s = self.area.groupby(["method", "scenario"]).add_2027_2031.sum(min_count=1)
        for k, v in s.items():
            exp = tot.loc[k, "addition"]
            if pd.isna(exp):
                self.assertTrue(pd.isna(v) or v == 0)
            else:
                self.assertAlmostEqual(v, exp, delta=0.01 * len(self.area))
        # years add to the five-year total
        yrs = self.state[self.state.year != "2027-2031"].groupby(["method", "scenario"]).addition.sum(min_count=1)
        for k, v in yrs.items():
            if pd.notna(v):
                self.assertAlmostEqual(v, tot.loc[k, "addition"], delta=0.01)

    def test_counties_and_districts_add_to_state(self):
        tot = self.state[self.state.year == "2027-2031"].set_index(["method", "scenario"]).addition
        for name in ("tod_model_per_acre_by_county.csv",):
            df = read(name)
            s = df.groupby(["method", "scenario"]).add_2027_2031.sum(min_count=1)
            for k, v in s.items():
                if pd.notna(tot.loc[k]):
                    self.assertAlmostEqual(v, tot.loc[k], delta=max(1.0, 1e-5 * tot.loc[k]), msg=f"{name} {k}")
            b = df.groupby(["method", "scenario"]).baseline_near_central_2027_2031.sum()
            for v in b:
                self.assertAlmostEqual(v, 14_463.78, delta=1.0, msg=name)

    def test_baseline_matches_shared_near_stop_split(self):
        b = pd.read_csv(REF / "housing_baseline_by_area.csv", dtype={"area_id": str})
        s = pd.read_csv(REF / "tod_near_stop_homes_by_muni.csv", dtype={"area_id": str})
        t = b.groupby("area_id").five_year_central.sum().reset_index().merge(s[["area_id", "share_near_main"]], on="area_id", how="left")
        expected = float((t.five_year_central * t.share_near_main.fillna(0)).sum())
        row = self.state[(self.state.year == "2027-2031") & (self.state.method == "A") & (self.state.scenario == "typical")]
        self.assertAlmostEqual(float(row.baseline_near_stops_central.iloc[0]), expected, delta=0.5)
        self.assertAlmostEqual(expected, 14_464, delta=1)

    def test_capacity_matches_station_area_table(self):
        st = pd.read_csv(REF / "tod_station_area_summary.csv")
        cap = st[(st.definition == "main") & (st.area == "State total")].capacity_gain.iloc[0]
        row = self.state[(self.state.year == "2027-2031") & (self.state.method == "A")].iloc[0]
        self.assertAlmostEqual(row.capacity_gain, cap, delta=1.0)
        sa = pd.read_csv(REF / "tod_station_areas.csv")
        coded_dose = sa[(sa.in_main == 1) & (sa.zoning_coded == 1)].added_floor_area_sqft.sum() / M.SQFT_PER_ACRE
        a = self.area[(self.area.method == "A") & (self.area.scenario == "typical")]
        coded = a[a.name.isin(["Milwaukee city", "Madison city"])].added_far_acres.sum()
        self.assertAlmostEqual(coded, coded_dose, delta=1.0)

    def test_scenarios_ordered(self):
        t = self.state[(self.state.year == "2027-2031") & (self.state.method == "A")].set_index("scenario").addition
        self.assertLess(t["little"], t["reference_line"])
        self.assertLess(t["reference_line"], t["typical"])
        self.assertLess(t["typical"], t["strong"])


class TestMadisonPredictions(unittest.TestCase):
    def test_file_and_rows(self):
        p = read("tod_madison_test_predictions.csv")
        self.assertIn("A", set(p.method))
        self.assertIn("B", set(p.method))
        a = p[(p.method == "A") & p.variant.str.startswith("main")].iloc[0]
        self.assertLessEqual(a.interval90_low, a.prediction)
        self.assertLessEqual(a.prediction, a.interval90_high)
        b = p[(p.method == "B") & p.variant.str.startswith("main")].iloc[0]
        self.assertTrue(pd.notna(b.prediction) or b.status.startswith("not computable"))

    def test_blind_no_madison_permits_read(self):
        src = (ROOT / "scripts" / "run_tod_model.py").read_text() + (ROOT / "missing_middleware" / "tod" / "model.py").read_text()
        for bad in ("madison_permits", "construction_summary", "madison_new_multifamily", "floor_area_per_home("):
            self.assertNotIn(bad, src)


class TestNetSizing(unittest.TestCase):
    """Sizing by citywide net effect (spec section 9, proposed): the switch and its outputs."""

    def test_timing_and_total(self):
        e = M.NetEffect(0.008, M.timing_from_ramp(M.ramp_from_gaps(GAPS)))
        tot = M.net_effect_total(100_000, e)
        self.assertAlmostEqual(tot.sum(), 800.0)
        self.assertTrue((tot >= 0).all())
        with self.assertRaises(ValueError):
            M.timing_from_profile([-2.63, 2.34, 6.79, 8.95, 12.09])  # a negative year would subtract

    def test_switch(self):
        df = pd.DataFrame({"area_id": ["a", "b", "c"], **{f"add_y{k}": [3.0 * k, 1.0 * k, 0.0] for k in M.YEARS}})
        self.assertTrue(M.size_additions(df, "per_acre").equals(df))
        e = M.NetEffect(0.01, (0.2,) * 5)
        out = M.size_additions(df, "net_effect", 10_000, e)
        ycols = [f"add_y{k}" for k in M.YEARS]
        self.assertAlmostEqual(out[ycols].sum().sum(), 100.0)
        self.assertAlmostEqual(out.loc[0, ycols].sum() / out[ycols].sum().sum(), 0.75)
        self.assertEqual(out.loc[2, ycols].sum(), 0.0)
        with self.assertRaises(ValueError):
            M.size_additions(df, "other")

    def test_cap_by_group(self):
        df = pd.DataFrame({"add_y1": [60.0, 60.0, 10.0], **{f"add_y{k}": [1.0, 1.0, 1.0] for k in (2, 3, 4, 5)}})
        out = M.cap_by_group(df, pd.Series(["m", "m", "x"]), {"m": 30.0})
        self.assertAlmostEqual(out.add_y1[:2].sum(), 30.0)
        self.assertEqual(out.add_y1[2], 10.0)
        self.assertEqual(out.add_y2.tolist(), [1.0, 1.0, 1.0])

    def test_outputs(self):
        st = read("tod_model_statewide.csv")
        area = read("tod_model_by_area.csv")
        self.assertEqual(set(st.sizing), {"net_effect"})
        self.assertTrue(M.check_no_negative(st.addition))
        self.assertTrue(M.check_no_negative(st.addition_range_low.dropna()))
        add_cols = [f"add_{y}" for y in range(2027, 2032)] + ["add_2027_2031"]
        self.assertTrue(M.check_no_negative(area[add_cols].to_numpy().ravel()))
        net = st[st.year == "2027-2031"].set_index("scenario")
        # totals reconcile: state = share x stock; areas, counties and districts add to the state
        for sid, r in net.iterrows():
            self.assertAlmostEqual(r.addition, r.parameter * r.stock_homes_station_areas, delta=1e-4 * r.addition + 0.01)
            self.assertAlmostEqual(area[area.scenario == sid].add_2027_2031.sum(), r.addition, delta=0.05)
            for name in ("tod_model_by_county.csv", "tod_model_by_assembly_district.csv", "tod_model_by_senate_district.csv"):
                d = read(name)
                self.assertAlmostEqual(d[d.scenario == sid].add_2027_2031.sum(), r.addition, delta=1.0, msg=name)
                self.assertAlmostEqual(d[d.scenario == sid].baseline_near_central_2027_2031.sum(), 14_463.78, delta=1.0, msg=name)
        yrs = st[st.year != "2027-2031"].groupby("scenario").addition.sum()
        for sid, v in yrs.items():
            self.assertAlmostEqual(v, net.loc[sid, "addition"], delta=0.01)
        t = net.addition
        self.assertLess(t["little"], t["typical"])
        self.assertLess(t["typical"], t["strong"])
        self.assertLessEqual(t["little"], t["reference_line"])
        self.assertLessEqual(t["reference_line"], t["strong"])
        self.assertLess(net.loc["typical", "addition_range_low"], t["typical"])
        self.assertLess(t["typical"], net.loc["typical", "addition_range_high"])
        self.assertAlmostEqual(float(net.stock_homes_station_areas.iloc[0]), 313_564, delta=0.5)
        # corrected values (AQ-050): LA over six years, coverage shares
        self.assertAlmostEqual(net.loc["little", "parameter"], 0.0004 * 5 / 6 / 0.61, places=7)
        self.assertAlmostEqual(net.loc["strong", "parameter"], 21_808 / 530_300 / 0.752, places=6)
        self.assertAlmostEqual(net.loc["typical", "parameter"], 0.008, places=7)
        # per-acre sizing still in the sensitivity file and ordered
        pa = read("tod_model_per_acre_statewide.csv")
        pa = pa[(pa.year == "2027-2031") & (pa.method == "A")].set_index("scenario").addition
        self.assertLess(pa["little"], pa["typical"])
        self.assertLess(pa["typical"], pa["strong"])

    def test_auckland_rescaled_profile(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import importlib.util
        spec = importlib.util.spec_from_file_location("rtm", ROOT / "scripts" / "run_tod_model.py")
        rtm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rtm)
        prof = rtm.auckland_profile_rescaled()
        self.assertEqual(sorted(prof), [2017, 2018, 2019, 2020, 2021])
        self.assertAlmostEqual(sum(prof.values()), 21_808, delta=0.01)
        self.assertTrue(all(v > 0 for v in prof.values()))

    def test_capped_sensitivity_within_cap(self):
        ck = read("tod_model_checks.csv")
        c = ck[(ck.check == "scale") & (ck.scenario == "wisconsin_measured_capped")]
        for r in c.itertuples():
            self.assertLessEqual(r.total_per_1000, max(r.p95, r.baseline_per_1000) + 1e-6)


class TestPrivacy(unittest.TestCase):
    def test_no_parcel_ids(self):
        long_num = re.compile(r"(?<![\w.:/-])\d{8,}(?![\w.])")
        for f in sorted(REF.glob("tod_model*.csv")) + [REF / "tod_madison_test_predictions.csv"]:
            text = f.read_text()
            head = text.splitlines()[0].lower()
            for bad in ("parcel", "taxkey", "pin"):
                self.assertNotIn(bad, head.split(","), f.name)
            stripped = re.sub(r"https?://\S+", "", text)
            stripped = re.sub(r"muni:\d+", "", stripped)
            self.assertIsNone(long_num.search(stripped), f"{f.name}: long number {long_num.search(stripped)}")


if __name__ == "__main__":
    unittest.main()
