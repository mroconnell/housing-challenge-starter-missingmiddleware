"""The Introduction (ui/src/screens/intro.ts): its numbers come from the bundles and shared reference files, and those
sources give exactly the owner-approved copy's numbers. ui/tests/intro.spec.ts checks the rendered page against the
same sources."""
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
        # parking's range is read from the bundle's range90, not recomputed from a CSV
        self.assertNotRegex(src, r"import .*parking_(uniform_range|placebo_full_summary)")
        self.assertIn("${pkBase}statewide.json", src)
        for n in ("8,055", "13,666", "3,922", "16,335", "46,268", "19,649", "124,000", "56,500", "218,865"):
            self.assertFalse(n in src, f"{n} is typed into intro.ts")   # numbers are never typed into the page
        self.assertIsNone(re.search(r"\b(8055|13666|3922|16335|46268|19649|124000|56500|218865)\b", src))


if __name__ == "__main__":
    unittest.main()
