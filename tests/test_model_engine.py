"""Engine behavior: floor, spillover, unchanged-policy, ordering, and arithmetic."""
import unittest

import pandas as pd

from missing_middleware.model import engine as e

RAMP = (0.4, 0.7, 1, 1, 1)


def scenario(spill=0.2):
    return e.Scenario("adu_benchmark", {
        "lower": e.PathParams(level=0.25, floor_rate=0.25, spillover=0.0, ramp=(0.25, 0.5, 0.75, 1, 1)),
        "central": e.PathParams(level=0.3, floor_rate=0.25, spillover=spill, ramp=RAMP),
        "upper": e.PathParams(level=1.0, floor_rate=0.25, spillover=spill * 2, ramp=(0.6, 0.9, 1, 1, 1)),
    })


AREAS = pd.DataFrame([
    {"area_id": "restrictive", "homes": 10000, "x_rate": 0.02, "at_benchmark": False},
    {"area_id": "madison", "homes": 53292, "x_rate": 0.25, "at_benchmark": True},
    {"area_id": "unknown", "homes": 10000, "x_rate": 0.0, "at_benchmark": False},
])


class TestEngine(unittest.TestCase):
    def setUp(self):
        self.out = e.run(AREAS, scenario())

    def test_invariants_hold(self):
        self.assertEqual(e.check_invariants(self.out), [])

    def test_worked_example_restrictive_central(self):
        t = self.out[(self.out.area_id == "restrictive") & (self.out.path == "central")]
        self.assertAlmostEqual(t.additional_units.sum(), 10 * (0.3 - 0.02) * 4.1, places=6)
        self.assertAlmostEqual(t.baseline_units.sum(), 10 * 0.02 * 5, places=6)

    def test_benchmark_place_gets_spillover_only(self):
        m = self.out[(self.out.area_id == "madison") & (self.out.path == "central")]
        self.assertAlmostEqual(m.y_rate.iloc[0], 0.30, places=9)
        self.assertAlmostEqual(m.additional_units.sum(), 53.292 * 0.05 * 4.1, places=6)

    def test_benchmark_place_gets_at_least_statewide_level(self):
        out = e.run(AREAS, scenario(spill=0.0))
        m = out[(out.area_id == "madison") & (out.path == "central")]
        self.assertAlmostEqual(m.y_rate.iloc[0], 0.30, places=9)

    def test_no_change_when_benchmark_rate_already_above_level_and_no_spillover(self):
        areas = pd.DataFrame([{"area_id": "hot", "homes": 1000, "x_rate": 0.5, "at_benchmark": True}])
        out = e.run(areas, scenario(spill=0.0))
        self.assertEqual(out[out.path == "central"].additional_units.sum(), 0.0)

    def test_floor_applies_when_level_below_floor(self):
        p = e.PathParams(level=0.1, floor_rate=0.25, spillover=0, ramp=RAMP)
        self.assertEqual(e.y_rate(0.0, False, p), 0.25)

    def test_never_below_current_rate(self):
        p = e.PathParams(level=0.1, floor_rate=0.1, spillover=0, ramp=RAMP)
        self.assertEqual(e.y_rate(0.5, False, p), 0.5)

    def test_ramping_place_gap_uses_that_years_current_rate(self):
        areas = pd.DataFrame([{"area_id": "mke", "homes": 1000, "x_rate": 0.2, "at_benchmark": False}])
        growth = pd.DataFrame([{"area_id": "mke", "year": t, "g": g} for t, g in zip(e.YEARS, (0.5, 0.75, 1, 1, 1))])
        out = e.run(areas, scenario(), growth)
        c = out[out.path == "central"].sort_values("year")
        self.assertAlmostEqual(c.baseline_units.iloc[0], 1 * 0.1, places=9)
        self.assertAlmostEqual(c.additional_units.iloc[0], 1 * (0.3 - 0.1) * 0.4, places=9)

    def test_area_specific_levels_override_uniform_level(self):
        lv = pd.DataFrame([{"area_id": "restrictive", "y_central": 0.6}])
        out = e.run(AREAS, scenario(), area_levels=lv)
        r = out[(out.area_id == "restrictive") & (out.path == "central")]
        self.assertAlmostEqual(r.y_rate.iloc[0], 0.6, places=9)
        u = out[(out.area_id == "unknown") & (out.path == "central")]
        self.assertAlmostEqual(u.y_rate.iloc[0], 0.3, places=9)

    def test_area_path_replaces_level_and_ramp(self):
        # explicit observed path (AQ-042): rates per year, no ramp on top, every path alike
        ap = pd.DataFrame({"area_id": "madison", "year": list(e.YEARS), "rate": [0.452, 0.542, 0.601, 0.799, 1.076]})
        lv = pd.DataFrame([{"area_id": "madison", "y_lower": 0.9, "y_central": 1.6, "y_upper": 3.0}])
        out = e.run(AREAS, scenario(), area_levels=lv, area_paths=ap)
        self.assertEqual(e.check_invariants(out), [])
        for path in e.PATHS:
            m = out[(out.area_id == "madison") & (out.path == path)].sort_values("year")
            self.assertEqual(m.y_rate.round(3).tolist(), [0.452, 0.542, 0.601, 0.799, 1.076])
            self.assertAlmostEqual(m.additional_units.sum(), 53.292 * (3.47 - 5 * 0.25), places=6)
            self.assertTrue((m.y_source == "area_path").all())
        # other areas untouched
        r = out[(out.area_id == "restrictive") & (out.path == "central")]
        self.assertAlmostEqual(r.additional_units.sum(), 10 * (0.3 - 0.02) * 4.1, places=6)

    def test_area_path_keeps_floor_and_current_rate(self):
        ap = pd.DataFrame({"area_id": "madison", "year": list(e.YEARS), "rate": [0.1, 0.2, 0.3, 0.4, 0.5]})
        out = e.run(AREAS, scenario(), area_paths=ap)
        m = out[(out.area_id == "madison") & (out.path == "central")].sort_values("year")
        # floor 0.25 and current rate 0.25 bind in years 1-2
        self.assertEqual(m.y_rate.round(3).tolist(), [0.25, 0.25, 0.3, 0.4, 0.5])
        self.assertAlmostEqual(m.additional_units.iloc[0], 0.0, places=9)

    def test_area_path_needs_every_year(self):
        ap = pd.DataFrame({"area_id": "madison", "year": [1, 2], "rate": [0.4, 0.5]})
        with self.assertRaises(ValueError):
            e.run(AREAS, scenario(), area_paths=ap)

    def test_bad_ramp_rejected(self):
        with self.assertRaises(ValueError):
            e.PathParams(level=0.3, floor_rate=0.2, spillover=0, ramp=(1, 0.5, 1, 1, 1))



class TestAdoptedParams(unittest.TestCase):
    """The adopted parameter file (AQ-042): Madison path, floor, area-level selector."""

    def test_madison_path_matches_median_path_table(self):
        from pathlib import Path

        from missing_middleware.model import params
        ref = Path(__file__).parent.parent / "reference"
        ap = params.area_paths()
        mad = ap[ap.area_id == "muni:5502548000"].sort_values("year")
        med = pd.read_csv(ref / "madison_like_median_path.csv")
        med = med[med.group == "WA+OR Madison-like (main)"].sort_values("year_since_law")
        self.assertEqual(mad.rate.round(3).tolist(), med.median_rate.round(3).tolist())
        self.assertEqual(sorted(set(ap.area_id)), ["muni:5502548000"])
        self.assertAlmostEqual(params.madison_floor(), 0.2345)
        spec = params.area_levels_spec()
        self.assertEqual((spec["option"], spec["config"]), ("cap_a2", "A_ca_in_common_level"))

    def test_adopted_ramps_match_revision_run(self):
        import json
        from pathlib import Path
        ref = Path(__file__).parent.parent / "reference"
        rev = ref / "pooled_revision_wi.csv"
        if not rev.exists():
            self.skipTest("run scripts/run_pooled_revision.py first")
        r = pd.read_csv(rev).query("option == 'cap_a2' and config == 'A_ca_in_common_level'").iloc[0]
        paths = json.loads((ref / "adu_model_params.json").read_text())["paths"]
        for p, c in (("central", "ramp_central"), ("upper", "ramp_upper_tau90")):
            got = paths[p]["ramp"]
            want = [float(v) for v in r[c].split("|")]
            for a, b in zip(got, want):
                self.assertAlmostEqual(a, b, places=4)
        self.assertEqual(paths["upper"]["label"], "Strong adoption")
        # the lower (AQ-043) is recomputed for its own level, so it climbs a little faster than the 10th percentile's
        low = paths["lower"]["ramp"]
        self.assertEqual(low[3:], [1.0, 1.0])
        self.assertEqual(low, sorted(low))
        for a, b in zip(low[:3], [float(v) for v in r["ramp_lower"].split("|")][:3]):
            self.assertGreaterEqual(a, b)

    def test_lower_is_mean_of_rhode_island_and_oregon(self):
        """AQ-043: lower level = mean of RI and OR stage-2 levels / the common level, applied to every area."""
        import json
        from pathlib import Path
        ref = Path(__file__).parent.parent / "reference"
        rule = json.loads((ref / "adu_model_params.json").read_text())["paths"]["lower"]["level_from"]
        self.assertEqual(sorted(rule["states"]), ["OR", "RI"])
        st2 = pd.read_csv(ref / "pooled_revision_stage2_levels.csv").query(
            "option == 'cap_a2' and config == 'A_ca_in_common_level'").set_index("cluster")["level_with_law_k4"]
        common = pd.read_csv(ref / "pooled_revision_wi.csv").query(
            "option == 'cap_a2' and config == 'A_ca_in_common_level'")["common_level_k4"].iloc[0]
        self.assertAlmostEqual((st2["RI"] + st2["OR"]) / 2, 0.6520, places=4)
        self.assertAlmostEqual(rule["factor"], (st2["RI"] + st2["OR"]) / 2 / common, places=4)
        # the lower sits between the two states: below Oregon and above Rhode Island at a typical place
        self.assertTrue(st2["RI"] < rule["factor"] * common < st2["OR"])


class TestAdoptedOutputs(unittest.TestCase):
    """Committed engine outputs after the 2026-10-26 owner decisions (AQ-043)."""

    @classmethod
    def setUpClass(cls):
        from pathlib import Path
        cls.ref = Path(__file__).parent.parent / "reference"

    def test_paths_ordered_and_baseline_shared(self):
        s = pd.read_csv(self.ref / "adu_model_statewide.csv").set_index("path")
        self.assertLess(s.loc["lower", "additional_units"], s.loc["central", "additional_units"])
        self.assertLess(s.loc["central", "additional_units"], s.loc["upper", "additional_units"])
        self.assertEqual(s["baseline_units"].nunique(), 1)
        by = pd.read_csv(self.ref / "adu_model_statewide_by_year.csv")
        for p, g in by.groupby("path"):
            self.assertAlmostEqual(g.additional_units.sum(), s.loc[p, "additional_units"], places=6)

    def test_milwaukee_at_measured_rate(self):
        m = pd.read_csv(self.ref / "wi_baseline_by_municipality.csv", dtype={"place_id": str})
        mk = m[m.place_id.astype(str).str.startswith("5507953000")]
        self.assertEqual(len(mk), 3)                      # three county pieces
        self.assertTrue((mk.x_status == "observed").all())
        self.assertTrue(mk.reform_date.isna().all())      # flat: no ramp
        self.assertAlmostEqual(mk.x_central.iloc[0], 35 / 405.608, places=4)
        sens = pd.read_csv(self.ref / "wi_baseline_sensitivities.csv").set_index("sensitivity")
        ramp = [k for k in sens.index if k.startswith("Milwaukee")]
        self.assertEqual(len(ramp), 1)
        self.assertGreater(sens.loc[ramp[0], "change_vs_main"], 0)

    def test_sensitivity_table_columns(self):
        s = pd.read_csv(self.ref / "adu_model_sensitivities.csv")
        self.assertTrue({"moves", "description"} <= set(s.columns))
        self.assertTrue(set(s.moves) <= {"none (adopted)", "statewide addition", "baseline only", "local distribution only"})
        self.assertFalse(s.description.isna().any())
        self.assertEqual((s.moves == "none (adopted)").sum(), 1)
        self.assertTrue(s.change.str.startswith("Lower as a statistical 10th percentile").any())
        self.assertTrue(s.change.str.startswith("Milwaukee rises to Madison's rate").any())
        # a baseline-only case leaves the with-law level alone, so the addition moves against the baseline
        adopted = s[s.moves.eq("none (adopted)")].iloc[0]
        for r in s[s.moves.eq("baseline only")].itertuples():
            db, da = r.baseline_5yr - adopted.baseline_5yr, r.difference_central
            self.assertLessEqual(db * da, 1e-9, r.change)

    def test_reference_line_8_states_carried_forward(self):
        lines = pd.read_csv(self.ref / "adu_model_reference_lines.csv")
        self.assertEqual(lines.adopted.sum(), 1)
        top = lines.iloc[0]
        self.assertTrue(bool(top.adopted))
        self.assertEqual(top.line_id, "8_state_median")
        by = pd.read_csv(self.ref / "adu_model_reference_line_by_year.csv").query("line == '8_state_median'")
        self.assertEqual(by.carried_forward.tolist(), [False, False, False, False, True])
        self.assertEqual(by.forecast_year[by.carried_forward].tolist(), [2031])
        self.assertAlmostEqual(by.median_rate.iloc[4], by.median_rate.iloc[3])
        self.assertAlmostEqual(by.additional.sum(), top.additional_5yr, places=0)
        self.assertIn("CA", by.states.iloc[0])


if __name__ == "__main__":
    unittest.main()
