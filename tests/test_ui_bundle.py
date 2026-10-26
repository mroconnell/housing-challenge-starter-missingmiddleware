"""Checks on the Gate 4 UI bundle (ui/public/runs/<run_id>/), built by scripts/build_ui_bundle.py.

The bundle is committed, so these run offline: it must equal the adopted reference CSVs, reconcile
counties and municipalities to the state, keep lower <= central <= upper, and never show missing as 0.
"""
import csv
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "ui" / "public" / "runs"
REF = ROOT / "reference"
PATHS = ("lower", "central", "upper")


def strict_load(path: Path):
    def bad(x):
        raise ValueError(f"non-finite number {x} in {path.name}")
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=bad)


def rows(name):
    with (REF / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class TestUIBundle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.run_id = json.loads((RUNS / "latest.json").read_text())["run_id"]
        d = RUNS / cls.run_id
        cls.dir = d
        cls.manifest = strict_load(d / "manifest.json")
        cls.state = strict_load(d / "state.json")
        cls.areas = strict_load(d / "areas.json")
        cls.unc = strict_load(d / "uncertainty.json")
        cls.pilots = strict_load(d / "pilots.json")
        cls.scen = {s["id"]: s for s in cls.state["scenarios"]}

    def test_files_and_size(self):
        for f in self.manifest["files"]:
            self.assertTrue((self.dir / f).exists(), f)
        size = sum(p.stat().st_size for p in self.dir.iterdir())
        self.assertLess(size, 5_000_000, "bundle should stay a few MB")
        self.assertEqual(self.manifest["validation"]["failed"], 0)
        self.assertEqual([p.name for p in RUNS.iterdir() if p.is_dir()], [self.run_id], "only the current run is kept")

    def test_state_equals_reference(self):
        ref = {r["path"]: r for r in rows("adu_model_statewide.csv")}
        for p in PATHS:
            self.assertAlmostEqual(self.scen[p]["additional_total"], float(ref[p]["additional_units"]), places=1)
            self.assertAlmostEqual(self.state["baseline"]["total"], float(ref[p]["baseline_units"]), places=1)
        by_year = rows("adu_model_statewide_by_year.csv")
        for r in by_year:
            i = int(r["year"]) - 1
            self.assertAlmostEqual(self.scen[r["path"]]["additional_by_year"][i], float(r["additional_units"]), places=1)
            self.assertAlmostEqual(self.state["baseline"]["by_year"][i], float(r["baseline_units"]), places=1)
        # the adopted reference line (the row marked adopted in adu_model_reference_lines.csv) and its yearly series
        line = next(r for r in rows("adu_model_reference_lines.csv") if r["adopted"] == "True")
        self.assertAlmostEqual(self.state["reference_line"]["additional_total"], float(line["additional_5yr"]), places=1)
        yearly = [r for r in rows("adu_model_reference_line_by_year.csv") if r["line"] == line["line_id"]]
        for r in yearly:
            i = int(r["forecast_year"]) - 2027
            self.assertAlmostEqual(self.state["reference_line"]["additional_by_year"][i], float(r["additional"]), places=1)
        self.assertEqual(self.state["reference_line"]["carried_forward_years"],
                         [int(r["forecast_year"]) for r in yearly if r["carried_forward"] == "True"])
        self.assertEqual(self.state["reference_line"]["label"], f"Median performance in {self.state['reference_line']['n_series']} examples of statewide ADU reform")

    def test_areas_reconcile_to_state(self):
        for level in ("counties", "munis"):
            for p in PATHS:
                for i in range(5):
                    tot = sum(a["add"][p][i] for a in self.areas[level])
                    self.assertAlmostEqual(tot, self.scen[p]["additional_by_year"][i], delta=0.5, msg=f"{level} {p} year {i + 1}")
            for i in range(5):
                tot = sum(a["base"][i] for a in self.areas[level])
                self.assertAlmostEqual(tot, self.state["baseline"]["by_year"][i], delta=0.5)
            self.assertEqual(sum(a["homes"] for a in self.areas[level]), 1_839_569)
        self.assertEqual(len(self.areas["counties"]), 72)
        self.assertEqual(len(self.areas["munis"]), 1925)

    def test_counties_equal_reference(self):
        ref = {(r["parent_county_id"], r["path"]): r for r in rows("adu_model_by_county.csv")}
        for c in self.areas["counties"]:
            for p in PATHS:
                self.assertAlmostEqual(sum(c["add"][p]), float(ref[(c["id"], p)]["additional_units"]), delta=0.05)
                self.assertAlmostEqual(sum(c["base"]), float(ref[(c["id"], p)]["baseline_units"]), delta=0.05)

    def test_paths_ordered(self):
        for level in ("counties", "munis"):
            for a in self.areas[level]:
                for i in range(5):
                    lo, ce, up = (a["add"][p][i] for p in PATHS)
                    self.assertLessEqual(lo, ce + 1e-6, a["id"])
                    self.assertLessEqual(ce, up + 1e-6, a["id"])
                    self.assertGreaterEqual(lo, 0)
        for i in range(5):
            self.assertLessEqual(self.scen["lower"]["additional_by_year"][i], self.scen["central"]["additional_by_year"][i])
            self.assertLessEqual(self.scen["central"]["additional_by_year"][i], self.scen["upper"]["additional_by_year"][i])

    def test_missing_is_not_zero(self):
        for a in self.areas["munis"]:
            if a["homes"] == 0:
                self.assertTrue(a.get("missing_reason"), a["id"])
        for c in self.unc["sensitivity_cases"]:
            if c["lower"] is None or c["upper"] is None:
                self.assertTrue(c["missing_reason"], c["label"])
        for p in self.pilots:
            for y in p["permits"]["years"]:
                if y["units"] is None:
                    self.assertEqual(y["status"], "missing")
                    self.assertTrue(y["reason"])
        # the reference file leaves these blank; the bundle must keep them null, not 0
        sens = {r["change"]: r for r in rows("adu_model_sensitivities.csv")}
        for c in self.unc["sensitivity_cases"]:
            blank = sens[c["change_as_recorded"]]["lower_additional_5yr"] == ""
            self.assertEqual(c["lower"] is None, blank, c["label"])

    def test_sensitivities_equal_reference(self):
        ref = {r["change"]: r for r in rows("adu_model_sensitivities.csv")}
        self.assertEqual(len(ref), len(self.unc["sensitivity_cases"]))
        for c in self.unc["sensitivity_cases"]:
            r = ref[c["change_as_recorded"]]
            self.assertAlmostEqual(c["central"], float(r["central_additional_5yr"]), places=1)
            self.assertAlmostEqual(c["difference_central"], float(r["difference_central"]), places=1)

    def test_pilots(self):
        slugs = {p["slug"]: p for p in self.pilots}
        self.assertEqual(set(slugs), {"madison", "pleasant-prairie", "sun-prairie"})
        mad = slugs["madison"]
        self.assertAlmostEqual(sum(mad["add"]["central"]), 134.92, delta=0.05)   # Gate 3 packet step 2
        self.assertEqual(mad["add"]["lower"], mad["add"]["upper"])               # Madison path in every scenario
        self.assertAlmostEqual(sum(mad["base"]), 50.0, delta=0.05)
        by_id = {a["id"]: a for a in self.areas["munis"]}
        for p in self.pilots:
            self.assertEqual(p["add"], by_id[p["area_id"]]["add"])
        self.assertEqual(slugs["sun-prairie"]["role"], "same_market_check")

    def test_no_lot_level_data(self):
        geo = strict_load(self.dir / "geo_munis.json")
        types = {f["geometry"]["type"] for f in geo["features"]}
        self.assertLessEqual(types, {"Polygon", "MultiPolygon"}, "area fills only, no points")
        text = (self.dir / "areas.json").read_text()
        for key in ("parcel", "address", "owner"):
            self.assertNotIn(f'"{key}', text)

    def test_county_whole_permits_equal_reference(self):
        # Gate 4 verification N4: rounded county figures must equal the rounded reference CSV
        ref = {(r["parent_county_id"], r["path"]): r for r in rows("adu_model_by_county.csv")}
        for c in self.areas["counties"]:
            for p in PATHS:
                r = ref[(c["id"], p)]
                self.assertEqual(round(sum(c["add"][p])), round(float(r["additional_units"])), (c["name"], p))
                self.assertEqual(round(sum(c["base"])), round(float(r["baseline_units"])), c["name"])

    def test_map_draws_no_water_areas(self):
        # Gate 4 verification S2: water-only areas are not drawn; every area with homes is
        geo = strict_load(self.dir / "geo_munis.json")
        drawn = {f["properties"]["id"] for f in geo["features"]}
        for a in self.areas["munis"]:
            if a.get("water"):
                self.assertNotIn(a["id"], drawn)
                self.assertEqual(a["homes"], 0)
            elif a["homes"] > 0:
                self.assertIn(a["id"], drawn)
        self.assertEqual(sum(1 for a in self.areas["munis"] if a.get("water")), 12)

    def test_madison_note_present(self):
        # Gate 4 verification B2: Madison's different treatment is explained wherever its numbers appear
        mad = next(p for p in self.pilots if p["slug"] == "madison")
        self.assertIn("Gate 5", mad["note"])
        self.assertEqual(sum(1 for a in self.areas["munis"] if a.get("note")), 1)

    def test_labels_come_from_the_bundle(self):
        # owner review 2026-10-26: one set of chart-key labels, used by every screen and the brief
        lab = self.state["labels"]
        self.assertEqual(lab["baseline"], "No statewide reform (baseline)")
        self.assertEqual(lab["band"], "Range from the lower to the strong adoption scenario")
        self.assertTrue(lab["reference"].startswith("Median performance in "))
        self.assertEqual(self.state["reference_line"]["label"], lab["reference"])
        want = {"lower": "Statewide ADU reform: lower scenario", "central": "Statewide ADU reform: central scenario",
                "upper": "Statewide ADU reform: strong adoption scenario"}
        for p in PATHS:
            self.assertEqual(self.scen[p]["chart_label"], want[p])
            self.assertTrue(self.scen[p]["title"] and self.scen[p]["text"] and self.scen[p]["info"])
        self.assertIn("California", self.scen["central"]["text"])
        self.assertNotIn("floor", " ".join(self.scen[p]["text"] for p in PATHS).lower())

    def test_baseline_only_effects(self):
        # baseline-only sensitivity cases: the engine baseline equals the baseline sensitivity table
        ref = {r["sensitivity"]: float(r["b5yr_central"]) for r in rows("wi_baseline_sensitivities.csv")}
        bo = {c["id"]: c for c in self.unc["baseline_only"]}
        self.assertAlmostEqual(bo["madison-2026"]["baseline"], ref["Madison x = 2026 provisional to date"], delta=0.1)
        self.assertAlmostEqual(bo["uncoded-prohibited"]["baseline"], ref["uncoded places behave like prohibited (old AQ-023 default)"], delta=0.1)
        self.assertEqual(len(rows("adu_model_sensitivities.csv")), len(self.unc["sensitivity_cases"]))
        for c in bo.values():
            # the with-law level does not depend on the current-law rate: a baseline change is mostly offset
            self.assertLessEqual(abs(c["d_with_law"]), abs(c["d_baseline"]) + 0.1, c["id"])
        groups = {"none (adopted)": "addition", "statewide addition": "addition", "baseline only": "baseline",
                  "local distribution": "local"}
        ref = {r["change"]: r for r in rows("adu_model_sensitivities.csv")}
        for c in self.unc["sensitivity_cases"]:
            self.assertEqual(c["group"], groups[ref[c["change_as_recorded"]]["moves"]], c["label"])
            self.assertEqual(c["what"], ref[c["change_as_recorded"]]["description"])
        # every baseline-only case in the effects table is also a recorded sensitivity case
        self.assertEqual(len(self.unc["baseline_only"]), sum(1 for c in self.unc["sensitivity_cases"] if c["group"] == "baseline"))

    def test_county_labels_are_points_inside_counties(self):
        lab = strict_load(self.dir / "geo_labels.json")
        self.assertEqual(len(lab["features"]), 72)
        self.assertEqual({f["geometry"]["type"] for f in lab["features"]}, {"Point"})
        self.assertTrue(all(f["properties"]["kind"] == "county" for f in lab["features"]))

    def test_pilot_texts(self):
        mad = next(p for p in self.pilots if p["slug"] == "madison")
        self.assertIn("Spokane", mad["like"]["text"])
        self.assertIn("0.45", mad["like"]["text"])
        self.assertIn("1.08", mad["like"]["text"])
        self.assertIn("29", mad["programme"]["text"])
        self.assertIn("13", mad["programme"]["text"])
        self.assertNotIn("floor", mad["description"].lower())
        self.assertIn("already inside the Wisconsin total", self.manifest["pilot_intro"]["how"])

    @unittest.skipUnless((ROOT / "data/processed/model_run/results_long.parquet").exists(), "needs the processed model run")
    def test_bundle_is_current(self):
        spec = importlib.util.spec_from_file_location("build_ui_bundle", ROOT / "scripts" / "build_ui_bundle.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _, run_id = mod.load_inputs()
        self.assertEqual(run_id, self.run_id, "bundle is stale: rerun scripts/build_ui_bundle.py")


if __name__ == "__main__":
    unittest.main()
