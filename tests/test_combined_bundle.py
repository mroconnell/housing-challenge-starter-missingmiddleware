"""Combined TOD + parking bundle (scripts/build_combined_bundle.py; docs/shared/SCENARIO_CONTRACT.md section 9):
sums reconcile with each reform's own additions, rule (b) never exceeds rule (a), mismatched baselines are refused,
paths are paired by role, and the bundle carries the core manifest."""
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_combined_bundle as bc  # noqa: E402

PUBLIC = ROOT / "ui" / "public" / "scenarios"
RUNS = PUBLIC / "combined" / "runs"


def additions(reform: str) -> dict:
    run = json.loads((PUBLIC / reform / "runs" / "latest.json").read_text())["run_id"]
    return json.loads((PUBLIC / reform / "runs" / run / "additions_by_area.json").read_text())


def tiny(reform: str, paths: list[str], roles: dict, rows: list[dict], baseline="all-housing baseline v2") -> dict:
    return {"reform": reform, "baseline_version": baseline, "years": [2027, 2028], "roles": roles,
            "paths": [{"id": p, "label": p.title()} for p in paths], "areas": rows}


TOD = tiny("tod", ["little", "typical", "strong"], {"lower": "little", "central": "typical", "upper": "strong"},
           [{"area_id": "muni:1", "part": "near_stops", "little": [1, 1], "typical": [2, 2], "strong": [10, 4]}])
PARK = tiny("parking", ["central", "upper"], {"lower": "central", "central": "central", "upper": "upper"},
            [{"area_id": "muni:1", "part": "near_stops", "central": [0, 0], "upper": [3, 6]},
             {"area_id": "muni:1", "part": "elsewhere", "central": [0, 0], "upper": [5, 5]},
             {"area_id": "muni:2", "part": "elsewhere", "central": [0, 0], "upper": [7, 7]}])


class TestCombineRules(unittest.TestCase):
    def test_rules_on_a_small_case(self):
        c = bc.combine(TOD, PARK)
        up = c["areas"]["muni:1"]["upper"]
        self.assertEqual(up["near_a"], [13, 10])
        self.assertEqual(up["near_b"], [10, 6])  # larger of the two, per year
        self.assertEqual(up["total_a"], [18, 15])
        self.assertEqual(up["total_b"], [15, 11])
        self.assertEqual(c["areas"]["muni:2"]["upper"]["total_a"], [7, 7])  # elsewhere only: added, same under both rules
        self.assertEqual(c["areas"]["muni:2"]["upper"]["total_b"], [7, 7])
        self.assertEqual(c["areas"]["muni:1"]["central"]["total_a"], [2, 2])

    def test_paths_paired_by_role_never_crossed(self):
        c = bc.combine(TOD, PARK)
        self.assertEqual([(p["role"], p["tod_path"], p["parking_path"]) for p in c["pairing"]],
                         [("lower", "little", "central"), ("central", "typical", "central"), ("upper", "strong", "upper")])
        self.assertEqual(c["areas"]["muni:1"]["lower"]["tod"], [1, 1])
        self.assertEqual(c["areas"]["muni:1"]["upper"]["tod"], [10, 4])

    def test_refuses_mismatched_baseline(self):
        other = copy.deepcopy(PARK)
        other["baseline_version"] = "all-housing baseline v1"
        with self.assertRaisesRegex(bc.CombineError, "baseline_version"):
            bc.combine(TOD, other)
        none = copy.deepcopy(TOD)
        del none["baseline_version"]
        with self.assertRaises(bc.CombineError):
            bc.combine(none, PARK)

    def test_refuses_missing_role_or_bad_part_or_years(self):
        bad = copy.deepcopy(PARK)
        bad["roles"]["upper"] = "nonesuch"
        with self.assertRaisesRegex(bc.CombineError, "role"):
            bc.combine(TOD, bad)
        far = copy.deepcopy(TOD)
        far["areas"][0]["part"] = "elsewhere"
        with self.assertRaises(bc.CombineError):
            bc.combine(far, PARK)
        yrs = copy.deepcopy(PARK)
        yrs["years"] = [2027, 2029]
        with self.assertRaisesRegex(bc.CombineError, "years"):
            bc.combine(TOD, yrs)


@unittest.skipUnless((RUNS / "latest.json").exists(), "combined bundle not built")
class TestCombinedBundle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.run_id = json.loads((RUNS / "latest.json").read_text())["run_id"]
        cls.d = RUNS / cls.run_id
        cls.m = json.loads((cls.d / "manifest.json").read_text())
        cls.sw = json.loads((cls.d / "statewide.json").read_text())
        cls.areas = json.loads((cls.d / "areas.json").read_text())
        cls.tod, cls.park = additions("tod"), additions("parking")

    def test_core_manifest_and_validation(self):
        for k in ("run_id", "scenario_id", "title", "outcome", "dates", "vintages", "validation", "repo_url", "inputs"):
            self.assertIn(k, self.m)
        self.assertEqual(self.m["run_id"], self.run_id)
        self.assertEqual(self.m["validation"]["failed"], 0)
        self.assertEqual(self.m["baseline_version"], self.tod["baseline_version"])
        self.assertEqual(self.tod["baseline_version"], self.park["baseline_version"])
        for f in self.m["files"]:
            self.assertTrue((self.d / f).exists(), f)
        self.assertEqual([p.name for p in RUNS.iterdir() if p.is_dir()], [self.run_id], "only the current run is kept")

    def test_run_id_is_hash_of_current_inputs(self):
        hs = []
        for i in self.m["inputs"]:
            p = ROOT / i["path"]
            self.assertTrue(p.exists(), i["path"])
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), i["sha256"], f"{i['path']} changed: rebuild")
            hs.append(i["sha256"])
        self.assertEqual(self.run_id, "combined-" + hashlib.sha256("".join(hs).encode()).hexdigest()[:10])

    def test_sums_reconcile_with_each_reform(self):
        for role in bc.ROLES:
            x = next(r for r in self.sw["roles"] if r["role"] == role)
            tp, pp = self.tod["roles"][role], self.park["roles"][role]
            self.assertEqual((x["tod_path"], x["parking_path"]), (tp, pp), "paired by role")
            tod_tot = sum(sum(a[tp]) for a in self.tod["areas"])
            park_near = sum(sum(a[pp]) for a in self.park["areas"] if a["part"] == "near_stops")
            park_else = sum(sum(a[pp]) for a in self.park["areas"] if a["part"] == "elsewhere")
            t = x["total"]
            self.assertAlmostEqual(t["tod"], tod_tot, delta=0.05)
            self.assertAlmostEqual(t["parking"], park_near + park_else, delta=0.05)
            self.assertAlmostEqual(t["both_a"], tod_tot + park_near + park_else, delta=0.1)
            self.assertAlmostEqual(t["both_a"] - t["near_a"], park_else, delta=0.1, msg="elsewhere is added")
            self.assertAlmostEqual(t["both_b"] - t["near_b"], park_else, delta=0.1, msg="elsewhere is the same under both rules")
            self.assertAlmostEqual(x["overlap_counted_twice"], t["both_a"] - t["both_b"], delta=0.05)
            for k, v in t.items():
                self.assertAlmostEqual(sum(x["by_year"][k]), v, delta=0.1, msg=f"{role} {k}: years add to the total")
            ia, ib = self.areas["cols"].index("total_a"), self.areas["cols"].index("total_b")
            self.assertAlmostEqual(sum(m[role][ia] for m in self.areas["munis"]), t["both_a"], delta=1)
            self.assertAlmostEqual(sum(m[role][ib] for m in self.areas["munis"]), t["both_b"], delta=1)
            self.assertAlmostEqual(sum(c[role][ia] for c in self.areas["counties"]), t["both_a"], delta=1)

    def test_rule_b_at_most_rule_a_and_at_least_each_alone(self):
        for x in self.sw["roles"]:
            t = x["total"]
            self.assertLessEqual(t["both_b"], t["both_a"] + 1e-6)
            self.assertGreaterEqual(t["both_b"] + 1e-6, max(t["tod"], t["parking"]))
            for a, b in zip(x["by_year"]["both_a"], x["by_year"]["both_b"]):
                self.assertLessEqual(b, a + 1e-6)
        cols = self.areas["cols"]
        for m in self.areas["munis"]:
            for role in bc.ROLES:
                v = dict(zip(cols, m[role]))
                self.assertLessEqual(v["total_b"], v["total_a"] + 0.02, m["id"])
                self.assertGreaterEqual(v["total_b"] + 0.02, max(v["tod"], v["parking_near"]) + v["parking_elsewhere"], m["id"])

    def test_parking_central_is_zero_so_central_equals_tod(self):
        x = next(r for r in self.sw["roles"] if r["role"] == "central")
        self.assertEqual(x["total"]["parking"], 0)
        self.assertEqual(x["total"]["both_a"], x["total"]["tod"])
        self.assertEqual(x["total"]["both_b"], x["total"]["tod"])

    def _parking_displayed(self):
        run = json.loads((PUBLIC / "parking" / "runs" / "latest.json").read_text())["run_id"]
        sw = json.loads((PUBLIC / "parking" / "runs" / run / "statewide.json").read_text())
        up = next(x for x in self.sw["roles"] if x["role"] == "upper")
        return sw, up

    def test_parking_alone_years_equal_the_parking_bundle_display(self):
        sw, up = self._parking_displayed()
        shown = [y["add_upper"] for y in sw["years"] if y["year"] in self.sw["years"]]
        self.assertEqual(up["display"]["by_year"]["parking"], [round(v) for v in shown])

    def test_parking_alone_total_equals_the_parking_bundle_display(self):
        sw, up = self._parking_displayed()
        self.assertEqual(up["display"]["total"]["parking"], next(x for x in sw["scenarios"] if x["id"] == "upper")["additional_total"])

    def test_display_values_are_rounded_once_half_up(self):
        for x in self.sw["roles"]:
            for k, v in x["total"].items():
                self.assertLessEqual(abs(x["display"]["total"][k] - v), 0.5 + 0.01, f"{x['role']} {k}")
        self.assertEqual(bc.whole(29662.5), 29663)
        self.assertEqual(bc.whole(2.5), 3)
        self.assertEqual(self.sw["rounding_note"], "Each figure is rounded on its own, so columns may differ from sums by one home.")

    def test_rule_c_has_no_number(self):
        self.assertFalse(any(ch.isdigit() for ch in self.sw["rule_c"]))
        self.assertNotIn("c", self.sw["rules"])

    def test_rebuilds_byte_for_byte(self):
        before = {p.name: p.read_bytes() for p in self.d.iterdir()}
        bc.main()
        self.assertEqual(json.loads((RUNS / "latest.json").read_text())["run_id"], self.run_id)
        self.assertEqual({p.name: p.read_bytes() for p in self.d.iterdir()}, before)


@unittest.skipUnless((PUBLIC / "tod" / "runs" / "latest.json").exists(), "TOD bundle not built")
class TestTodAdditions(unittest.TestCase):
    def test_tod_additions_match_reference(self):
        import pandas as pd
        t = additions("tod")
        self.assertEqual(t["roles"], {"lower": "little", "central": "typical", "upper": "strong"})
        self.assertTrue(all(a["part"] == "near_stops" for a in t["areas"]))
        ref = pd.read_csv(ROOT / "reference" / "tod_model_by_area.csv")
        ref = ref[ref["sizing"] == "net_effect"].set_index(["area_id", "scenario"])
        for a in t["areas"]:
            for sc in ("little", "typical", "strong"):
                self.assertAlmostEqual(sum(a[sc]), ref.loc[(a["area_id"], sc), "add_2027_2031"], delta=0.001)


if __name__ == "__main__":
    unittest.main()
