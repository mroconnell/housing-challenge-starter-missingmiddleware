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
    "reference/middle_in_out.csv", "reference/middle_test1_states.csv",
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
    flat = L("core_flat_timing")
    years_m = [{"year": y["year"], "low": y["lower"], "high": y["upper"]} for y in by_year("core_2_4")]
    years_f = [{"year": y, "low": round(flat["lower"] / 5, 1), "high": round(flat["upper"] / 5, 1)} for y in YEARS]
    method = ("The real four-state result (Oregon, California, Maine and Vermont against similar places in the same "
              "regions) placed against 10,000 sets of 4 fake law states drawn from 34 comparison states: the 5th to 95th "
              "percentile of their spread around the real result, in extra 2–4 unit homes per 1,000 single-family homes a "
              "year, times Wisconsin's 1,839,569 single-family homes.")
    coverage = ("Built from fake-law estimates, so it already carries their spread and is not widened (shared rule 5). "
                "Most of the range is above zero, but it includes a small fall.")
    side_lines = [
        {"id": "four_state", "label": "Four-state measured result", "value": core["central"], "where": "chart",
         "note": "The real result in Oregon, California, Maine and Vermont against similar places, applied to Wisconsin."},
        {"id": "1_4", "label": "All 1–4 unit buildings", "value": s14["central"], "where": "chart",
         "note": "Includes 1-unit homes on split lots and other single-unit types. Too noisy to include in predicted range "
                 "because Census mixes these single units with conventional single-family homes."},
        {"id": "1_6", "label": "Adding 5 and 6 unit buildings", "value": s16["central"], "where": "chart",
         "note": "Our estimate for 5 and 6 unit buildings added to all 1–4 unit buildings. Too noisy to include in predicted "
                 "range because Census mixes 5 and 6 unit projects with all 5+ unit projects."},
        {"id": "all", "label": "All building sizes", "value": sall["central"], "where": "chart",
         "note": f"Its own range is {sall['lower']:,} to {sall['upper']:,}. Counts every building size, so swings in house and "
                 "apartment building swamp any change from this reform. Too noisy to include in predicted range."},
        {"id": "with_addons", "label": "With townhouses, split-lot homes and 5–6 unit buildings", "value": L("with_addons")["central"],
         "where": "howsure", "note": "Estimated, not measured: Census files townhouses as 1-unit."},
        {"id": "stronger", "label": "Stronger reform (up to 6 homes per lot)", "low": whole(band["stronger_reform_central_share_low"]),
         "high": whole(band["stronger_reform_central_share_high"]), "where": "howsure",
         "note": "Possibility, not measured. Assumes new small buildings would split between 2–4 and 5–6 units the way past "
                 "building did in OR, CA, ME and VT."},
    ]
    b24 = base[base["kind"].isin(["projected", "projected_bridge_year"]) & base["structure_type"].isin(["2units", "3_4units"])].groupby("year")[["low", "central", "high"]].sum()
    base_years = {"central": [round(float(proj.loc[y, "central"]), 1) for y in YEARS],
                  "low": [round(float(proj.loc[y, "low"]), 1) for y in YEARS],
                  "high": [round(float(proj.loc[y, "high"]), 1) for y in YEARS]}
    KIND = {"Law states": "state", "Law-state places": "places", "Comparison places": "comparison places",
            "States left out": "state", "Places left out": "places", "Fake law states": "states"}
    ROLE = {"Law states": "law state: sets the measured effect", "Comparison places": "comparison: similar places without a law"}
    scope = {"in": [], "out": [], "source": "reference/middle_in_out.csv; docs/middle/TEST_PLAN_LOCKED.md; docs/middle/TEST1_RESULTS.md"}
    for r in pd.read_csv(REF / "middle_in_out.csv").itertuples():
        kind = KIND.get(r.group, "places")
        if r.status.startswith("in"):
            role = "test only" if "test only" in r.status else ROLE.get(r.group, r.group)
            scope["in"].append({"name": r.name, "kind": kind, "area": r.places, "role": role, "note": r.reason})
        else:
            scope["out"].append({"name": r.name, "kind": kind, "reason": f"{r.places}: {r.reason}"})
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
        "range90": {"low": core["lower"], "high": core["upper"], "unit": "extra homes in 2–4 unit buildings permitted, 2027–2031",
                    "method": method, "coverage": coverage, "source": "reference/middle_test1_summary.csv (Test 1, M2, four states)",
                    "years": years_m, "years_method": "Measured slow start: 2027 at about −21% of full size, full size from 2028."},
        "range90_flat": {"low": flat["lower"], "high": flat["upper"], "unit": "extra homes in 2–4 unit buildings permitted, 2027–2031",
                         "method": method, "coverage": coverage, "source": "reference/middle_test1_summary.csv (Test 1, M2, four states)",
                         "years": years_f, "years_method": "Same effect every year."},
        "side_lines": side_lines,
        "baseline_by_year": base_years,
        "evidence_scope": scope,
        "baseline_2_4_by_year": {k: [round(float(b24.loc[y, k]), 1) for y in YEARS] for k in ("central", "low", "high")},
        "baseline_2_4_note": "Homes in 2–4 unit buildings (2-unit plus 3–4 unit) expected under current law, shared baseline v4.",
    }
    area_rows = [{"area_id": a.area_id, "name": a.name, "sf_homes": int(a.homes),
                  "lower": round(a.add_lower_five_year, 2), "central": round(a.add_central_five_year, 2),
                  "upper": round(a.add_upper_five_year, 2)} for a in areas.itertuples()]
    # Input what-ifs (Test 1 choices), each as the five-year central for Wisconsin: rate difference x homes x timing.
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("rmw", ROOT / "scripts" / "run_middle_wisconsin.py")
    rmw = _ilu.module_from_spec(_spec); _spec.loader.exec_module(rmw)
    homes = float(areas["homes"].sum())
    ra = rmw.ramp()
    factor = homes * sum(ra.values())                     # homes x (4 full years + the 2027 share)
    st = pd.read_csv(REF / "middle_test1_states.csv")
    st = st[(st["mode"] == "real") & (st["measure"] == "M2") & st["data"].str.startswith("reported")]
    main_d = st[st["version"] == "main"].set_index("state")["diff"]
    nat = st[st["version"] == "unmatched matched nationally"]["diff"].mean()
    or_alt = main_d.copy(); or_alt["Oregon"] = st[st["version"] == "Oregon before 2015-2018"]["diff"].iat[0]
    t1all = pd.read_csv(REF / "middle_test1_summary.csv")
    filled = t1all[(t1all["data"].str.startswith("Census")) & (t1all["measure"] == "M2") & (t1all["set"] == "four states")]["real_diff_per_1000"].iat[0]
    loo = {k: main_d.drop(k).mean() for k in main_d.index}
    lo_k, hi_k = min(loo, key=loo.get), max(loo, key=loo.get)
    annual = float(t1["real_diff_per_1000"]) * homes / 1000
    or_share = rmw.FIRST_YEAR["Oregon"][0] / rmw.FIRST_YEAR["Oregon"][1]
    inputs = [
        {"id": "match_nationally", "chart": "Inputs", "label": "Match unmatched places nationally (comparison group)", "central": whole(nat * factor / 1000)},
        {"id": "oregon_before", "chart": "Inputs", "label": "Oregon's before years 2015–2018 instead of 2015–2019", "central": whole(or_alt.mean() * factor / 1000)},
        {"id": "census_filled", "chart": "Inputs", "label": "Census filled-in permit counts instead of reported only", "central": whole(filled * factor / 1000),
         "note": "This version failed the fake-years check (it showed a rise before any law), so it is read as partly a trend."},
        {"id": "leave_one_state", "chart": "Inputs", "label": f"Leave one law state out ({lo_k} out to {hi_k} out)",
         "low": whole(loo[lo_k] * factor / 1000), "high": whole(loo[hi_k] * factor / 1000)},
        {"id": "first_year_share", "chart": "Inputs", "label": f"2027 share: Oregon's alone ({or_share:.0%}) to none (0%)",
         "low": whole(annual * (4 + or_share)), "high": whole(annual * 4)},
    ]
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
    howsure["bars"] = howsure["bars"] + inputs
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
