"""Export the middle housing scenario as a static JSON bundle for the tool (in development).

The browser runs no model: every number comes from this bundle, built only from committed reference files:
- reference/middle_model_statewide_by_year.csv, middle_model_lines_2027_2031.csv, middle_model_stronger_band.csv,
  middle_model_by_area.csv (scripts/run_middle_wisconsin.py)
- reference/middle_test1_summary.csv (Test 1), reference/housing_baseline_statewide_by_year.csv (shared baseline v4)

Output: ui/public/scenarios/middle/runs/<run_id>/*.json and latest.json. The run id hashes the inputs.
Run: uv run python scripts/build_middle_bundle.py
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference"
OUT_ROOT = ROOT / "ui" / "public" / "scenarios" / "middle" / "runs"
REPO_URL = "https://github.com/mroconnell/housing-challenge-starter-missingmiddleware"
DOC = REPO_URL + "/blob/main/"
YEARS = [2027, 2028, 2029, 2030, 2031]
BASELINE_VERSION = "all-housing baseline v4"
INPUTS = [
    "scripts/build_middle_bundle.py", "scripts/run_middle_wisconsin.py",
    "reference/middle_model_statewide_by_year.csv", "reference/middle_model_lines_2027_2031.csv",
    "reference/middle_model_stronger_band.csv", "reference/middle_model_by_area.csv",
    "reference/middle_test1_summary.csv", "reference/housing_baseline_statewide_by_year.csv",
]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def whole(v) -> int:
    return int(math.floor(float(v) + 0.5))


def doc(path: str, label: str) -> dict:
    return {"label": label, "url": DOC + path}


def build() -> Path:
    yr = pd.read_csv(REF / "middle_model_statewide_by_year.csv")
    lines = pd.read_csv(REF / "middle_model_lines_2027_2031.csv").set_index("kind")
    band = pd.read_csv(REF / "middle_model_stronger_band.csv").set_index("item")["value"]
    areas = pd.read_csv(REF / "middle_model_by_area.csv")
    t1 = pd.read_csv(REF / "middle_test1_summary.csv")
    t1 = t1[(t1["data"].str.startswith("reported")) & (t1["measure"] == "M2") & (t1["set"] == "four states")].iloc[0]
    base = pd.read_csv(REF / "housing_baseline_statewide_by_year.csv")
    proj = base[base["kind"].isin(["projected", "projected_bridge_year"]) & (base["structure_type"] == "all")].set_index("year")

    def L(kind):  # five-year lower/central/upper
        r = lines.loc[kind]
        return {"lower": whole(r["lower"]), "central": whole(r["central"]), "upper": whole(r["upper"])}

    def by_year(kind):
        d = yr[yr["kind"] == kind].pivot(index="year", columns="line", values="value")
        return [{"year": int(y), **{k: round(float(d.loc[y, k]), 1) for k in ("lower", "central", "upper")}} for y in YEARS]

    core, s14, s16, sall = L("core_2_4"), L("side_1_4"), L("side_1_6"), L("side_all")
    statewide = {
        "headline": ("The evidence can't tell yet. We'll know more when we have a full five years in the other states. "
                     "Most of the range for 2–4 unit homes is above zero, but it includes a small fall, and there is "
                     "enough noise that we're not sure it's caused by this reform."),
        "core": {"label": "Homes in 2–4 unit buildings (predicted range)", **core, "by_year": by_year("core_2_4"),
                 "split": {"2_unit": L("core_2_unit"), "3_4_unit": L("core_3_4_unit")},
                 "rate_per_1000_sf_homes": {"lower": round(float(t1["range_diff_low"]), 3),
                                            "central": round(float(t1["real_diff_per_1000"]), 3),
                                            "upper": round(float(t1["range_diff_high"]), 3)}},
        "timing": {"label": "Measured slow start", "toggle_off_label": "Same effect every year",
                   "flat": L("core_flat_timing"),
                   "note": "2027 at the measured first-law-year share (about −21% of full size, from Oregon 2022, "
                           "California 2022 and Vermont 2023), full size from 2028. Three single years: the sign of "
                           "the 2027 share is not measured. With a negative share, the lower line's 2027 value sits "
                           "slightly above zero."},
        "side_measures": [
            {"id": "1_4", **s14, "by_year": by_year("side_1_4"),
             "label": f"About {s14['central']:+,} more homes over 5 years when we count all 1–4 unit buildings, including "
                      "1-unit homes on split lots and other single-unit types.",
             "caveat": "Too noisy to include in predicted range because Census mixes these single units with "
                       "conventional single-family homes."},
            {"id": "1_6", **s16, "by_year": by_year("side_1_6"),
             "label": f"About {s16['central']:+,} more homes over 5 years when we add our estimate for 5 and 6 unit buildings.",
             "caveat": "Too noisy to include in predicted range because Census mixes 5 and 6 unit projects with all "
                       "5+ unit projects."},
            {"id": "all", **sall, "by_year": by_year("side_all"),
             "label": f"About {sall['central']:+,} more homes over 5 years. Counts every building size, so swings in "
                      "house and apartment building swamp any change from this reform.",
             "caveat": "Too noisy to include in predicted range."},
        ],
        "extra_lines": [
            {"id": "with_addons", **L("with_addons"), "label": "With add-ons",
             "info": "The core plus estimated townhouses and split-lot homes (Census files them as 1-unit; records that "
                     "include them show 1.5–3× the Census 2–4 count, middle 2.25×) and 5–6 unit buildings. Estimated, not measured."},
            {"id": "stronger_reform", **L("stronger_reform"), "label": "Stronger reform (up to 6 homes per lot)",
             "info": "Possibility, not measured. Assumes that if 5–6 homes were allowed, new small buildings would split "
                     "between 2–4 and 5–6 units the way past building did in OR, CA, ME and VT. None of the tested laws "
                     "allowed 5–6 homes by right.",
             "share_band_central": {"low": whole(band["stronger_reform_central_share_low"]),
                                    "high": whole(band["stronger_reform_central_share_high"]),
                                    "portland_check": whole(band["stronger_reform_central_portland"])},
             "never_add_to": "1_6"},
        ],
        "baseline": {"version": BASELINE_VERSION, "total": whole(proj.loc[YEARS, "central"].sum()),
                     "low_total": whole(proj.loc[YEARS, "low"].sum()), "high_total": whole(proj.loc[YEARS, "high"].sum())},
        "years": YEARS,
    }
    area_rows = [{"area_id": a.area_id, "name": a.name, "sf_homes": int(a.homes),
                  "lower": round(a.add_lower_five_year, 2), "central": round(a.add_central_five_year, 2),
                  "upper": round(a.add_upper_five_year, 2)} for a in areas.itertuples()]
    howsure = {"bars": [
        {"id": "flat_timing", "label": "Same effect every year (timing toggle off)", "central": L("core_flat_timing")["central"]},
        {"id": "townhouses", "label": "Add townhouses and split-lot homes (×1.5–3)", "central": L("with_addons")["central"]},
        {"id": "five_six", "label": "Add 5–6 unit buildings (7–27% share)", "central": L("extra_5_6")["central"] + core["central"]},
        {"id": "stronger", "label": "Stronger reform, share 7.2%–26.6%", "low": whole(band["stronger_reform_central_share_low"]),
         "high": whole(band["stronger_reform_central_share_high"])},
        {"id": "m2_ratio", "label": "Core converted by ratio instead of rate", "central": 2790,
         "note": "+32.7% (−21.4% to +91.9%) on 8,546 baseline 2–4 unit homes (audit, 2026-11-10)."},
    ], "notes": [
        "Trend-adjusted view (post hoc): projecting each state's pre-law trend forward, the after-law years fall below it.",
        "Weakest point: the West comparison group is thin (85 places reporting every year) and lumpy.",
    ]}
    why = {"evidence": [
        doc("docs/middle/TEST_PLAN_LOCKED.md", "Locked test plan"),
        doc("docs/middle/TEST1_RESULTS.md", "Test 1: four law states vs similar places"),
        doc("docs/middle/TEST6_RESULTS.md", "Test 6: what Census misses"),
        doc("docs/middle/TEST4_RESULTS.md", "Test 4: fake reform years"),
        doc("docs/middle/WISCONSIN_PLAN_LOCKED.md", "Wisconsin plan (locked)"),
        doc("docs/middle/SCALING_LITERATURE.md", "How studies scale bigger upzonings"),
        doc("docs/middle/LAW_STRENGTH_CODING.md", "Law-strength coding"),
    ], "cannot_tell": [
        "Homes built, as opposed to permitted.",
        "Effects of a law broader than any tested (2–6 homes by right on every lot).",
        "A demand shock that starts in the same year as a law.",
    ]}
    inputs = [{"path": p, "sha256": sha256(ROOT / p)} for p in INPUTS]
    run_id = "middle-" + hashlib.sha256("".join(i["sha256"] for i in inputs).encode()).hexdigest()[:10]
    manifest = {"run_id": run_id, "scenario_id": "middle", "title": "Middle housing (2–6 homes per lot)",
                "outcome": {"short": "Extra homes permitted (Census permits), 2027–2031",
                            "long": "Extra homes permitted on top of the shared all-housing baseline; core counts homes in 2–4 unit buildings.",
                            "rate_units": "homes per 1,000 single-family homes per year", "count_units": "homes permitted"},
                "dates": {"last_observed_year": 2025, "forecast_years": YEARS,
                          "effective": "Stylized statewide law in effect 1 January 2027"},
                "vintages": {"census_permits": "2012–2025", "acs": "2020–2024", "baseline": BASELINE_VERSION},
                "validation": {"core_five_year_central": core["central"]},
                "repo_url": REPO_URL, "inputs": inputs, "baseline_version": BASELINE_VERSION,
                "files": ["statewide.json", "areas.json", "howsure.json", "why.json"]}
    if OUT_ROOT.exists():
        shutil.rmtree(OUT_ROOT)
    out = OUT_ROOT / run_id
    out.mkdir(parents=True)
    for name, obj in (("manifest.json", manifest), ("statewide.json", statewide), ("areas.json", area_rows),
                      ("howsure.json", howsure), ("why.json", why)):
        (out / name).write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n")
    (OUT_ROOT / "latest.json").write_text(json.dumps({"run_id": run_id}) + "\n")
    return out


if __name__ == "__main__":
    print(build())
