"""TOD tool bundle (scripts/build_tod_bundle.py): contract keys, validation, numbers equal the reference CSVs,
byte-for-byte rebuild, and no parcel ids."""
import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference"
RUNS = ROOT / "ui" / "public" / "scenarios" / "tod" / "runs"


@unittest.skipUnless((RUNS / "latest.json").exists(), "TOD bundle not built")
class TestTodBundle(unittest.TestCase):
    def setUp(self):
        self.run = json.loads((RUNS / "latest.json").read_text())["run_id"]
        self.d = RUNS / self.run
        self.m = json.loads((self.d / "manifest.json").read_text())
        self.sw = json.loads((self.d / "statewide.json").read_text())
        self.areas = json.loads((self.d / "areas.json").read_text())

    def test_contract_keys_and_validation(self):
        for k in ("run_id", "scenario_id", "title", "outcome", "dates", "vintages", "validation", "repo_url", "inputs"):
            self.assertIn(k, self.m)
        for k in ("short", "long", "rate_units", "count_units"):
            self.assertIn(k, self.m["outcome"])
        self.assertEqual(self.m["run_id"], self.run)
        self.assertEqual(self.m["validation"]["failed"], 0)
        self.assertGreater(self.m["validation"]["passed"], 0)
        for f in self.m["files"]:
            self.assertTrue((self.d / f).exists(), f)
        self.assertEqual([p.name for p in RUNS.iterdir() if p.is_dir()], [self.run], "only the current run is kept")

    def test_run_id_is_hash_of_inputs(self):
        hs = []
        for i in self.m["inputs"]:
            p = ROOT / i["path"]
            self.assertTrue(p.exists(), i["path"])
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), i["sha256"], i["path"])
            hs.append(i["sha256"])
        self.assertEqual(self.run, "tod-" + hashlib.sha256("".join(hs).encode()).hexdigest()[:10])

    def test_statewide_numbers_match_reference(self):
        st = pd.read_csv(REF / "tod_model_statewide.csv")
        five = st[st["year"].astype(str) == "2027-2031"].set_index("scenario")
        for sc in self.sw["scenarios"]:
            self.assertAlmostEqual(sc["additional_total"], five.loc[sc["id"], "addition"], delta=0.01)
            self.assertAlmostEqual(sc["with_law_total"], five.loc[sc["id"], "with_law_central"], delta=0.01)
            yrs = st[(st["scenario"] == sc["id"]) & (st["year"].astype(str) != "2027-2031")].sort_values("year")["addition"].tolist()
            for a, b in zip(sc["by_year"], yrs):
                self.assertAlmostEqual(a, b, delta=0.01)
        self.assertAlmostEqual(self.sw["baseline"]["total"], five.loc["typical", "baseline_near_stops_central"], delta=0.01)
        # AQ-054: no median line with fewer than 4 comparable cases (TOD has one whole-city study per scenario)
        self.assertNotIn("reference_line", self.sw)
        self.assertFalse(self.sw["median_line"]["shown"])
        self.assertEqual(self.sw["median_line"]["n_studies"], len(self.sw["scenarios"]))
        self.assertLess(self.sw["median_line"]["n_studies"], self.sw["median_line"]["min_cases"])
        self.assertEqual(self.sw["stock_homes"], int(five.loc["typical", "stock_homes_station_areas"]))
        d = pd.read_csv(REF / "tod_definition_summary.csv").set_index("definition")
        for row in self.sw["ladder"]:
            self.assertEqual(row["homes"], int(d.loc[row["id"], "homes"]))
        homes = [r["homes"] for r in self.sw["ladder"]]
        self.assertEqual(homes, sorted(homes), "ladder runs narrowest to widest")

    def test_shared_units_match_reference(self):
        """AQ-054: extra homes a year statewide against the shared all-housing baseline, and shares of Wisconsin's ACS
        2020-2024 home count, all from the reference files."""
        hb = pd.read_csv(REF / "housing_baseline_statewide_by_year.csv")
        proj = hb[(hb["kind"] == "projected") & (hb["structure_type"] == "all") & hb["year"].between(2027, 2031)]
        state_base = proj["central"].sum()
        self.assertAlmostEqual(self.sw["state_baseline_total"], state_base, delta=0.01)
        self.assertAlmostEqual(self.sw["state_baseline_per_year"], state_base / 5, delta=0.01)
        hh = pd.read_csv(REF / "gate5_housing_health.csv")
        acs = int(hh[hh["indicator"] == "total_housing_units_acs"]["value"].iloc[0])
        self.assertEqual(self.sw["acs_homes"], acs)
        for sc in self.sw["scenarios"]:
            self.assertAlmostEqual(sc["per_year"], sc["additional_total"] / 5, delta=0.001)
            self.assertAlmostEqual(sc["share_of_state_baseline"], sc["additional_total"] / state_base, delta=1e-6)
            self.assertAlmostEqual(sc["share_of_acs_homes"], sc["additional_total"] / acs, delta=1e-6)
        # by area: each place's all-housing baseline, and every level plus the unallocated row adds up to the state
        ab = pd.read_csv(REF / "housing_baseline_by_area.csv").groupby("area_id")["five_year_central"].sum()
        for m in self.areas["munis"]:
            self.assertAlmostEqual(m["all_baseline"], ab[m["id"]], delta=0.001, msg=m["name"])
        unalloc = ab[~ab.index.str.startswith("muni:")].sum()
        self.assertAlmostEqual(self.areas["all_baseline_unallocated"], unalloc, delta=0.001)
        for lvl in ("counties", "assembly", "senate"):
            self.assertAlmostEqual(self.areas[lvl]["all_baseline_total"] + self.areas["all_baseline_unallocated"], state_base, delta=1, msg=lvl)

    def test_areas_match_reference(self):
        a = pd.read_csv(REF / "tod_model_by_area.csv")
        for m in self.areas["munis"]:
            for sc, v in m["add"].items():
                ref = a[(a["area_id"] == m["id"]) & (a["scenario"] == sc)]["add_2027_2031"].iloc[0]
                self.assertAlmostEqual(v, ref, delta=0.01)
        c = pd.read_csv(REF / "tod_model_by_county.csv")
        for row in self.areas["counties"]["rows"]:
            ref = c[(c["county"] == row["name"]) & (c["scenario"] == "typical")]["add_2027_2031"].iloc[0]
            self.assertAlmostEqual(row["add"]["typical"], ref, delta=0.01)
        se = pd.read_csv(REF / "tod_model_sensitivities.csv")
        mm = se[(se["sizing"] == "net_effect") & (se["group"] == "main") & (se["scenario"] == "typical")].iloc[0]
        met = {m["id"]: m for m in self.areas["metros"]}
        self.assertAlmostEqual(met["milwaukee"]["add"]["typical"], mm["milwaukee_metro_2027_2031"], delta=0.5)
        self.assertAlmostEqual(met["madison"]["add"]["typical"], mm["madison_metro_2027_2031"], delta=0.5)

    def test_today_density_matches_reference(self):
        """Today screen: homes per acre of land within 1/4 and 1/2 mile of rail and rapid stops and in the 1/2-1 mile ring
        (2020 snapshot), Wisconsin beside the five older non-industrial reforms (BelRed left out), from the reference CSV."""
        self.assertIn("today.json", self.m["files"])
        t = json.loads((self.d / "today.json").read_text())
        d = pd.read_csv(REF / "tod_today_density.csv").set_index(["place", "band"])
        bands = {"quarter": "quarter_mile", "half": "half_mile", "ring": "ring_half_to_one_mile"}
        pooled = "five older non-industrial reforms (pooled)"
        rows = [("Wisconsin (all)", t["state"]), (pooled, t["five_places"])] + \
            [(x["label"], x) for x in t["systems"]] + [(x["id"], x) for x in t["reforms"]]
        for place, got in rows:
            for k, band in bands.items():
                ref = d.loc[(place, band)]
                self.assertEqual(got[k]["homes"], int(ref["homes_2020"]), place)
                self.assertEqual(got[k]["stops"], int(ref["n_stops"]), place)
                self.assertAlmostEqual(got[k]["homes_per_acre"], ref["homes_per_acre"], delta=0.006, msg=place)
            ring = d.loc[(place, "ring_half_to_one_mile")]
            for k, band in (("quarter", "quarter_mile"), ("half", "half_mile")):
                near = d.loc[(place, band)]
                want = (near["homes_2020"] / near["land_acres"]) / (ring["homes_2020"] / ring["land_acres"])
                self.assertAlmostEqual(got["vs_ring"][k], want, delta=0.002, msg=place)
        # systems' rings do not overlap, so they add up to Wisconsin's
        self.assertEqual(sum(x["ring"]["homes"] for x in t["systems"]), t["state"]["ring"]["homes"])
        stops = pd.read_csv(REF / "tod_stops.csv")
        self.assertEqual(t["stops_total"], int(stops["flag_a_rapid"].astype(bool).sum()))
        self.assertEqual([x["half"]["stops"] for x in t["systems"]], [106, 138, 22])
        self.assertEqual([x["place"] for x in t["reforms"]], ["Austin", "Salt Lake City", "Saint Paul", "Seattle", "Seattle"])
        self.assertEqual([x["id"] for x in t["left_out"]], ["bellevue_belred_2009"])
        self.assertEqual(t["reform_years"], [2009, 2014])
        # five together counts each stop once (Beacon Hill is in both Seattle reforms)
        self.assertEqual(t["five_places"]["half"]["stops"], 34)
        self.assertEqual(sum(x["half"]["stops"] for x in t["reforms"]) - t["stops_counted_twice"], 34)
        # BelRed stays in the file, flagged; the five-place pool has no industrial rezone in it
        self.assertEqual(int(d.loc[("bellevue_belred_2009", "half_mile"), "industrial_rezone"]), 1)
        self.assertEqual(int(d.loc[(pooled, "half_mile"), "industrial_rezone"]), 0)
        # context: Wisconsin's 1/2-mile land at the five places' pooled density
        w, p = d.loc[("Wisconsin (all)", "half_mile")], d.loc[(pooled, "half_mile")]
        extra = (p["homes_2020"] / p["land_acres"] - w["homes_2020"] / w["land_acres"]) * w["land_acres"]
        c = t["context"]["half"]
        self.assertAlmostEqual(c["extra_homes"], extra, delta=0.1)
        self.assertEqual(c["extra_homes_rounded"], round(extra, -2))
        self.assertAlmostEqual(c["extra_share"], extra / w["homes_2020"], delta=1e-4)
        self.assertNotIn("ratio", t, "the rest-of-city ratio is no longer on the screen")

    def test_option_d_labels(self):
        # owner 2026-11-02 22:29: central and upper labels name the district share of lots within 1/4 mile
        lab = {s["id"]: s["label"] for s in self.sw["scenarios"]}
        self.assertIn("about 12% of lots within ¼ mile of transit", lab["typical"])
        # AQ-072 (owner 2026-11-03 00:17): lower and upper from the causal framework
        self.assertEqual(lab["little"], "Lower: the rezoned parcels' own gain only")
        self.assertTrue(lab["strong"].startswith("Upper: upzoning together with new transit lines"))
        tot = {s["id"]: s["additional_total"] for s in self.sw["scenarios"]}
        for k, v in (("little", 3958.0), ("typical", 10028.1), ("strong", 13450.6)):
            self.assertAlmostEqual(tot[k], v, delta=0.05)

    def test_eau_claire_pilot_adds_nothing(self):
        p = {x["slug"]: x for x in json.loads((self.d / "pilots.json").read_text())}
        self.assertEqual(p["eau-claire"]["city_homes_near"], 0)
        self.assertTrue(all(v == 0 for v in p["eau-claire"]["city_add"].values()))
        for slug in ("milwaukee-connect-1", "madison-route-a"):
            c = p[slug]["corridor"]
            self.assertLessEqual(c["add"]["typical"], self.sw["scenarios"][1]["additional_total"])
            for pl in c["places"]:
                # option D (AQ-071): the district is 15% of the place's land within 1/4 mile of rail and rapid stops
                self.assertAlmostEqual(pl["district_acres"], 0.15 * pl["acres"], delta=1.0, msg=pl["name"])
                self.assertEqual(pl["share_of_place"], 1.0, pl["name"])

    def test_no_parcel_ids_and_small(self):
        size = 0
        for f in self.d.iterdir():
            text = f.read_text()
            size += len(text.encode())
            self.assertNotRegex(text, r'"(parcel|parcel_id|pin|taxkey|tax_key|parcelnum|bbl)"', f.name)
            # no long digit strings other than municipality ids (muni:55...) and hashes
            for n in re.findall(r"(?<![\w:./-])\d{10,}(?![\w.])", text):
                self.fail(f"{f.name}: long number {n}")
        self.assertLess(size, 5_000_000)

    def test_tornado_matches_sensitivities(self):
        hs = json.loads((self.d / "howsure.json").read_text())
        se = pd.read_csv(REF / "tod_model_sensitivities.csv")
        ne = se[se["sizing"] == "net_effect"]
        central = ne[(ne["group"] == "main") & (ne["scenario"] == "typical")]["addition_2027_2031"].iloc[0]
        self.assertAlmostEqual(hs["tornado"]["central"], central, delta=0.1)
        rows = hs["tornado"]["rows"]
        self.assertEqual(len(rows), 19)
        for row in rows:
            sens, sc = row["id"].split(":")
            src = ne[(ne["group"] == ("main" if sens == "main" else "law_addition")) & (ne["sensitivity"] == sens) & (ne["scenario"] == sc)]
            self.assertEqual(len(src), 1, row["id"])
            self.assertAlmostEqual(row["extra"], src["addition_2027_2031"].iloc[0], delta=0.1)
            self.assertAlmostEqual(row["vs_central"], row["extra"] - central, delta=0.2)
        ids = {x["id"].split(":")[0] for x in rows}
        self.assertNotIn("ramp_year5_alt", ids)   # timing only: the five-year total is unchanged

    def test_rebuild_is_byte_identical(self):
        before = {f.name: f.read_bytes() for f in self.d.iterdir()}
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_tod_bundle.py")], check=True, capture_output=True)
        after = {f.name: f.read_bytes() for f in self.d.iterdir()}
        self.assertEqual(before, after)
        self.assertEqual(json.loads((RUNS / "latest.json").read_text())["run_id"], self.run)


if __name__ == "__main__":
    unittest.main()
