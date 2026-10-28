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
        cls.unk = strict_load(d / "unknown_rules.json")
        cls.dist = strict_load(d / "districts.json")

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
        self.assertIn("December 2026", mad["note"])
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
                  "local distribution": "local", "local distribution only": "local"}   # AQ-061 value top-code case
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

    # ---- Gate 5: unknown-rules switch -------------------------------------------------------
    def test_unknown_rules_switch_equals_csv(self):
        st = {(r["unknown_treatment"], r["path"]): r for r in rows("adu_model_unknown_rules_statewide.csv")}
        by = {(r["unknown_treatment"], r["path"], int(r["forecast_year"])): r for r in rows("adu_model_unknown_rules_statewide_by_year.csv")}
        ids = [v["id"] for v in self.unk["variants"]]
        self.assertEqual(ids, ["like_restricted", "like_prohibited", "like_benchmark"])
        self.assertEqual(self.unk["uncoded_homes"], 1_267_433)
        self.assertEqual(self.unk["state_homes"], 1_839_569)
        self.assertEqual(len({r["run_group_id"] for r in st.values()} | {self.unk["run_group_id"]}), 1)
        for v in self.unk["variants"]:
            for p in PATHS:
                r = st[(v["id"], p)]
                self.assertAlmostEqual(v["additional_total"][p], float(r["additional_units"]), places=1)
                self.assertAlmostEqual(v["with_law_total"][p], float(r["total_with_law"]), places=1)
                self.assertAlmostEqual(v["d_with_law"][p], float(r["d_total_with_law"]), places=1)
                self.assertAlmostEqual(v["baseline_total"], float(r["baseline_units"]), places=1)
                for i, y in enumerate(range(2027, 2032)):
                    self.assertAlmostEqual(v["additional_by_year"][p][i], float(by[(v["id"], p, y)]["additional_units"]), places=1)
                    self.assertAlmostEqual(v["with_law_by_year"][p][i], float(by[(v["id"], p, y)]["total_with_law"]), places=1)
            self.assertLessEqual(v["additional_total"]["lower"], v["additional_total"]["central"])
            self.assertLessEqual(v["additional_total"]["central"], v["additional_total"]["upper"])
        # the adopted variant is every other number in the tool
        ad = self.unk["variants"][0]
        self.assertTrue(ad["adopted"])
        self.assertAlmostEqual(ad["baseline_total"], self.state["baseline"]["total"], places=1)
        for p in PATHS:
            self.assertAlmostEqual(ad["additional_total"][p], self.scen[p]["additional_total"], places=1)
        self.assertNotIn("like_restricted", self.unk["areas"])
        # the plain-language figures quoted on screen (docs/gate5/UI_CONTRACT.md)
        pro, ben = self.unk["variants"][1], self.unk["variants"][2]
        self.assertEqual((round(pro["baseline_total"]), round(pro["additional_total"]["central"]), round(pro["with_law_total"]["central"])), (352, 10940, 11292))
        self.assertEqual((round(ben["baseline_total"]), round(ben["additional_total"]["central"]), round(ben["with_law_total"]["central"])), (1393, 10051, 11444))

    def test_unknown_rules_areas_and_counties_reconcile(self):
        munis = {a["id"]: a for a in self.areas["munis"]}
        ref = {(r["unknown_treatment"], r["parent_county_id"], r["path"]): r for r in rows("adu_model_unknown_rules_by_county.csv")}
        for v in self.unk["variants"][1:]:
            ov = self.unk["areas"][v["id"]]
            # only places with uncoded rules change
            self.assertTrue(ov)
            self.assertTrue(all(munis[a]["x_status"] == "assumed" for a in ov))
            for p in PATHS:
                for i in range(5):
                    tot = sum((ov[a["id"]]["add"][p] if a["id"] in ov else a["add"][p])[i] for a in self.areas["munis"])
                    self.assertAlmostEqual(tot, v["additional_by_year"][p][i], delta=0.05, msg=f"{v['id']} {p} {i}")
            for i in range(5):
                tot = sum((ov[a["id"]]["base"] if a["id"] in ov else a["base"])[i] for a in self.areas["munis"])
                self.assertAlmostEqual(tot, v["baseline_by_year"][i], delta=0.05)
            cv = self.unk["counties"][v["id"]]
            for c in self.areas["counties"]:
                cc = cv.get(c["id"], c)
                for p in PATHS:
                    self.assertAlmostEqual(sum(cc["add"][p]), float(ref[(v["id"], c["id"], p)]["additional_units"]), delta=0.01)

    # ---- Gate 5: legislative districts ------------------------------------------------------
    def test_districts_reconcile_to_state(self):
        for level, n in (("assembly", 99), ("senate", 33)):
            L = self.dist["levels"][level]
            self.assertEqual(len(L["rows"]), n)
            un = L["unallocated"]
            self.assertEqual(un["name"], "Not allocated to a district")   # kept, never dropped
            for p in PATHS:
                for i in range(5):
                    tot = sum(d["add"][p][i] for d in L["rows"]) + un["add"][p][i]
                    self.assertAlmostEqual(tot, self.scen[p]["additional_by_year"][i], delta=0.01, msg=f"{level} {p} {i}")
            for i in range(5):
                self.assertAlmostEqual(sum(d["base"][i] for d in L["rows"]) + un["base"][i], self.state["baseline"]["by_year"][i], delta=0.01)
            self.assertAlmostEqual(sum(d["homes"] for d in L["rows"]) + un["homes"], 1_839_569, delta=5)
            # each district equals its reference row (five-year totals)
            ref = {(r["district"], r["path"]): r for r in rows(f"adu_model_by_{level}_district.csv") if r["forecast_year"] == "2027-2031"}
            for d in L["rows"] + [un]:
                for p in PATHS:
                    self.assertAlmostEqual(sum(d["add"][p]), float(ref[(d["district"], p)]["additional_units"]), delta=0.001)
                self.assertAlmostEqual(sum(d["base"]), float(ref[(d["district"], "central")]["baseline_units"]), delta=0.001)
        asm = {int(d["district"]): d for d in self.dist["levels"]["assembly"]["rows"]}
        for sd in self.dist["levels"]["senate"]["rows"]:
            self.assertEqual(len(sd["assembly"]), 3)
            for p in PATHS:
                self.assertAlmostEqual(sum(sum(asm[a]["add"][p]) for a in sd["assembly"]), sum(sd["add"][p]), delta=0.01)
        self.assertIn("2020 census blocks", self.dist["caveat"])
        self.assertIn("not forecasts", self.dist["caveat"])

    def test_district_geometry_is_in_the_bundle(self):
        # copied from data/processed (git-ignored) so a fresh clone draws districts; polygons only, small
        for level, n in (("assembly", 99), ("senate", 33)):
            g = strict_load(self.dir / f"geo_{level}.json")
            self.assertEqual(len(g["features"]), n)
            self.assertLessEqual({f["geometry"]["type"] for f in g["features"]}, {"Polygon", "MultiPolygon"})
            ids = {f["properties"]["id"] for f in g["features"]}
            self.assertEqual(ids, {d["id"] for d in self.dist["levels"][level]["rows"]})
            self.assertLess((self.dir / f"geo_{level}.json").stat().st_size, 250_000)
        lab = strict_load(self.dir / "geo_district_labels.json")
        self.assertEqual({f["geometry"]["type"] for f in lab["features"]}, {"Point"})
        self.assertEqual(sum(f["properties"]["kind"] == "assembly" for f in lab["features"]), 99)
        self.assertEqual(sum(f["properties"]["kind"] == "senate" for f in lab["features"]), 33)

    def test_landing_screen_indicators(self):
        pr = self.state["production_rate"]
        self.assertEqual((pr["numerator"], pr["denominator"], pr["value"]), (25569, 2840960, 9.0))
        self.assertTrue(all(b["source_id"] == "census_bps_state" for b in self.state["bps"] if b["total"] is not None))
        self.assertIn("five years", self.state["acs_period"])
        tr = {t["status"]: t for t in self.unc["trace"]}
        tot = sum(t["additional_central"] for t in tr.values())
        self.assertAlmostEqual(tot, self.scen["central"]["additional_total"], delta=0.05)
        self.assertEqual([round(tr[k]["additional_central"] / tot * 100, 1) for k in ("observed", "estimated", "assumed")], [5.2, 21.2, 73.6])  # AQ-061 (was 5.5, 21.1, 73.4)


    def test_context_why_equals_csv(self):
        """'Why places differ' (comparison screen): context rates, values and incomes, and the driver terms equal the CSVs."""
        con = {r["context"]: r for r in rows("gate5_context_contrast.csv")}
        for c in self.state["contexts"]:
            r = con[c["id"]]
            self.assertAlmostEqual(c["additional_rate_central"], float(r["additional_rate_central_per_1000_per_year"]), places=4)
            self.assertAlmostEqual(c["x_rate"], float(r["x_current_law_rate"]), places=4)
            self.assertAlmostEqual(c["y_rate_2031_central"], float(r["y_with_law_rate_2031_central"]), places=4)
            self.assertAlmostEqual(c["median_home_value"], float(r["median_home_value_homes_weighted_geomean"]), delta=0.5)
            self.assertEqual(c["homes"], int(r["homes"]))
            # the rate is the addition over five years per 1,000 homes
            self.assertAlmostEqual(c["additional_rate_central"], c["additional_central"] / c["homes"] / 5 * 1000, places=3)
        why = self.state["context_why"]
        self.assertAlmostEqual(why["state"]["additional_rate_central"], float(con["state"]["additional_rate_central_per_1000_per_year"]), places=4)
        drv = {r["term"]: r for r in rows("gate5_model_drivers.csv")}
        for d in why["drivers"]:
            self.assertAlmostEqual(d["ratio_10pct"], float(drv[d["term"]]["rate_ratio_for_10pct_higher"]), places=4)
            self.assertAlmostEqual(d["coefficient"], float(drv[d["term"]]["coefficient_log_scale"]), places=4)
        ratios = {d["term"]: d["ratio_10pct"] for d in why["drivers"]}
        # AQ-061: places differ by home value only (allocation fit, slope about 1.02: +10% value -> +10% rate);
        # the value-income-size terms set the statewide rate only
        self.assertEqual(round((ratios["alloc_value_dev"] - 1) * 100), 10)
        self.assertEqual(round((ratios["value_dev"] - 1) * 100), 29)
        self.assertEqual(round((1 - ratios["income_dev"]) * 100), 25)
        self.assertEqual(len(why["examples"]), len(rows("gate5_context_examples.csv")))


if __name__ == "__main__":
    unittest.main()
