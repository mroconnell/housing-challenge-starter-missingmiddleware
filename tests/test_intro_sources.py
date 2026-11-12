"""The Introduction (ui/src/screens/intro.ts) and the Brief estimate cards (ui/src/estimate.ts): the numbers come from
the bundles and shared reference files, and those sources give exactly the owner-approved copy's numbers. Since the
owner's change of 2026-11-12 the four ranges sit on each reform's Brief tab, not on the Introduction.
ui/tests/intro.spec.ts and ui/tests/brief_estimate.spec.ts check the rendered pages against the same sources."""
import json
import re
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference"
PUB = ROOT / "ui" / "public"
INTRO = ROOT / "ui" / "src" / "screens" / "intro.ts"


def latest(root: Path) -> Path:
    return root / json.loads((root / "latest.json").read_text())["run_id"]


@unittest.skipUnless((PUB / "runs" / "latest.json").exists() and (PUB / "scenarios" / "parking" / "runs" / "latest.json").exists()
                     and (PUB / "scenarios" / "tod" / "runs" / "latest.json").exists(), "bundles not built")
class TestIntroSources(unittest.TestCase):
    def test_adu_range(self):
        r = json.loads((latest(PUB / "runs") / "state.json").read_text())["range90"]
        self.assertEqual((round(r["low"]), round(r["high"])), (8055, 13666))

    def test_tod_range(self):
        r = json.loads((latest(PUB / "scenarios" / "tod" / "runs") / "statewide.json").read_text())["range90"]
        self.assertEqual((round(r["low"]), round(r["high"])), (3922, 16335))

    def test_parking_range(self):
        base = latest(PUB / "scenarios" / "parking" / "runs")
        r = json.loads((base / "statewide.json").read_text())["range90"]
        self.assertEqual((round(r["low"]), round(r["high"])), (-46268, 19649))
        # the bundle's range is the placebo summary's rates times the eligible homes over five years
        homes = sum(m["eligible_homes"] or 0 for m in json.loads((base / "areas.json").read_text())["munis"])
        s = pd.read_csv(REF / "parking_placebo_full_summary.csv").iloc[0]
        k = homes * 5 / 1000
        self.assertEqual((round(s["range_from_placebo_low"] * k), round(s["range_from_placebo_high"] * k)), (round(r["low"]), round(r["high"])))
        up = next(x for x in json.loads((base / "statewide.json").read_text())["scenarios"] if x["id"] == "upper")
        self.assertEqual(up["additional_total"], round(r["high"]))

    def test_middle_range(self):
        core = json.loads((latest(PUB / "scenarios" / "middle" / "runs") / "statewide.json").read_text())["core"]
        self.assertEqual((round(core["lower"]), round(core["upper"])), (-482, 4515))
        self.assertEqual(core["label"], "Homes in 2–4 unit buildings (predicted range)")

    def test_no_ranges_table_on_intro(self):
        src = INTRO.read_text()
        self.assertNotIn("<table", src)
        self.assertNotIn("Wisconsin, extra permits 2027–2031, 90% range", src)
        self.assertNotIn("HOW_WE_COUNT", src)
        self.assertNotIn("Measure the effect where it really happened", src)
        self.assertNotIn("Test the method", src)
        self.assertNotIn("stronger", src.lower())

    def test_estimate_card_on_every_brief(self):
        est = (ROOT / "ui" / "src" / "estimate.ts").read_text()
        self.assertIn('ESTIMATE_TITLE = "The estimate, 2027–2031 (90% range)"', est)
        self.assertIn("HOW_WE_COUNT[id]", est)
        S = ROOT / "ui" / "src"
        calls = {
            "adu": (S / "screens" / "brief.ts", 'estimateCardHTML("adu", s.range90,'),
            "middle": (S / "scenarios" / "middle" / "index.ts", 'estimateCardHTML("middle", { low: c.lower, high: c.upper }, unit)'),
            "tod": (S / "scenarios" / "tod" / "screens.ts", 'estimateCardHTML("tod", s.range90,'),
            "parking": (S / "scenarios" / "parking" / "index.ts", 'estimateCardHTML("parking", R,'),
        }
        for k, (f, call) in calls.items():
            src = f.read_text()
            self.assertIn(call, src, k)
            for n in ("8,055", "13,666", "3,922", "16,335", "46,268", "19,649", "4,515"):
                self.assertNotIn(f"estimateCardHTML(\"{k}\", {{ low: {n}", src)
        self.assertIsNone(re.search(r"\b(8055|13666|3922|16335|46268|19649|482|4515)\b", est))
        self.assertIn('{ path: "/brief", label: "Brief"', (S / "scenarios" / "middle" / "index.ts").read_text())

    def test_baseline(self):
        y = pd.read_csv(REF / "housing_baseline_statewide_by_year.csv")
        y = y[(y.structure_type == "all") & (y.kind == "projected") & y.year.between(2027, 2031)]
        self.assertEqual(len(y), 5)
        central = float(y.central.sum())
        band = pd.read_csv(REF / "housing_baseline_band.csv")
        self.assertEqual(band[["low", "high"]].drop_duplicates().shape[0], 1)   # one multiplier pair for every size
        b = band[band.structure_type == "1unit"].iloc[0]
        self.assertEqual((round(central), round(central * b.low), round(central * b.high)), (124000, 56500, 218865))

    def test_intro_reads_these_sources(self):
        src = INTRO.read_text()
        for f in ("housing_baseline_band.csv", "housing_baseline_statewide_by_year.csv"):
            self.assertIn(f"reference/{f}?raw", src)
        for n in ("8,055", "13,666", "3,922", "16,335", "46,268", "19,649", "124,000", "56,500", "218,865", "4,515"):
            self.assertFalse(n in src, f"{n} is typed into intro.ts")   # numbers are never typed into the page
        self.assertIsNone(re.search(r"\b(8055|13666|3922|16335|46268|19649|124000|56500|218865|482|4515)\b", src))


if __name__ == "__main__":
    unittest.main()


class TestSharedSummarySources(unittest.TestCase):
    """The Summary tab (ui/src/summary.ts) and the Brief estimate card (ui/src/estimate.ts) read the "How we count" lines from one module, and the
    per-1,000 base is the ACS home count the tool already stores (ADU state.json acs_total_units)."""

    def test_how_we_count_has_one_source(self):
        hwc = (ROOT / "ui" / "src" / "howwecount.ts").read_text()
        for k in ("adu", "middle", "tod", "parking"):
            self.assertRegex(hwc, rf"\n  {k}: \"")
        self.assertIn('REFORM_ORDER: ReformKey[] = ["adu", "middle", "tod", "parking"]', hwc)
        est, summary = (ROOT / "ui" / "src" / "estimate.ts").read_text(), (ROOT / "ui" / "src" / "summary.ts").read_text()
        self.assertIn('from "./howwecount"', est)
        self.assertIn('from "./howwecount"', summary)
        self.assertIn("HOW_WE_COUNT[o.id]", summary)
        for f in (INTRO, ROOT / "ui" / "src" / "estimate.ts"):
            self.assertNotIn("We hid 7 of the states", f.read_text())   # the copy lives in howwecount.ts only
        # TOD's line is the owner's text of 2026-11-11 20:33 as changed at 20:37, word for word
        self.assertIn("tod: \"Extra homes permitted near transit. We compared permits within ¼ mile of rail and rapid-bus stops in 11 places that adopted upzoning near transit. In each place, we found some stops with an upzoned apartment district nearby, and other similar stops in the same transit network that weren't rezoned. We looked at permits before and after the reforms, across both kinds of stops. The whole range is above zero, so the evidence points to extra homes permitted.\"", hwc)

    @unittest.skipUnless((PUB / "runs" / "latest.json").exists(), "bundles not built")
    def test_per_1000_base(self):
        st = json.loads((latest(PUB / "runs") / "state.json").read_text())
        self.assertEqual(st["acs_total_units"]["value"], 2778572)
        self.assertTrue(st["acs_total_units"]["vintage"].startswith("ACS 2020-2024"))
        tod = json.loads((latest(PUB / "scenarios" / "tod" / "runs") / "statewide.json").read_text())
        self.assertEqual(tod["acs_homes"], st["acs_total_units"]["value"])
        summary = (ROOT / "ui" / "src" / "summary.ts").read_text()
        self.assertIn("acs_total_units", summary)
        self.assertNotRegex(summary, r"2,?778,?572")   # read from the bundle, never typed

    @unittest.skipUnless((PUB / "scenarios" / "middle" / "runs" / "latest.json").exists(), "bundles not built")
    def test_middle_flat_timing_is_the_bundles(self):
        sw = json.loads((latest(PUB / "scenarios" / "middle" / "runs") / "statewide.json").read_text())
        self.assertIn("range90_flat", sw)
        self.assertEqual(len(sw["range90_flat"]["years"]), 5)
        self.assertIn("rangeFlat: s.range90_flat", (ROOT / "ui" / "src" / "scenarios" / "middle" / "index.ts").read_text())
