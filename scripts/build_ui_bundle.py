"""Export the adopted ADU model outputs as a static JSON bundle for the ADU tool (ui/; Gates 4 and 5).

The browser runs no model. Every number the tool shows is read from this bundle, and the
bundle is built only from the adopted outputs:

- reference/adu_model_*.csv and adu_model_params.json (engine, scripts/run_adu_model.py);
- data/processed/model_run/results_long.parquet (the same engine run, per area, year and path);
- reference/wi_baseline_*.csv, wi_measured_permits_2022_2025.csv (current-law baseline);
- reference/pooled_revision_*.csv, eligible_basis_g3f2.csv (scenarios, robustness checks);
- reference/wi_adu_rules.csv, wi_rights_exposure.csv, wi_town_zoning_status.csv (rules, coverage);
- reference/madison_adu_permits_by_year.csv, pleasant_prairie_/sun_prairie_adu_equivalent_by_year.csv (pilots);
- reference/statewide_states_annual.csv, pooled_adoption_points.csv, madison_like_*.csv (charts);
- reference/adu_model_baseline_only_effects.csv (scripts/run_baseline_only_effects.py), pooled_convergence.csv (text);
- data/processed/foundation/state_conditions.parquet, areas.parquet, geo/*.parquet (context, area list);
- data/raw/census_cb_2024/ (Census cartographic boundary files, shoreline-clipped, for the map drawing only);
- Gate 5: reference/adu_model_unknown_rules_*.csv and data/processed/model_run/unknown_rules/results_long.parquet
  (unknown-rules switch), reference/adu_model_by_{assembly,senate}_district.csv, adu_model_district_crosswalk.csv and
  data/processed/districts/geo_{assembly,senate}.geojson (legislative districts; the simplified outlines are copied
  into the committed bundle, so a fresh clone draws them without data/processed), reference/gate5_trace.csv.

Output: ui/public/runs/<run_id>/*.json and ui/public/runs/latest.json. The run id is a hash of the
input files, so the same inputs give the same bundle byte for byte (no timestamps).

Run: uv run --all-extras python scripts/build_ui_bundle.py
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference"
PROC = ROOT / "data" / "processed"
OUT_ROOT = ROOT / "ui" / "public" / "runs"
REPO_URL = "https://github.com/mroconnell/housing-challenge-starter-missingmiddleware"
DOC = REPO_URL + "/blob/main/"
WI_HOMES = 1_839_569
YEARS = [2027, 2028, 2029, 2030, 2031]
PATHS = ["lower", "central", "upper"]

INPUTS = [
    "scripts/build_ui_bundle.py", "reference/adu_model_params.json", "reference/adu_model_statewide.csv", "reference/adu_model_statewide_by_year.csv",
    "reference/adu_model_by_county.csv", "reference/adu_model_by_context.csv", "reference/adu_model_by_rights_basis.csv",
    "reference/adu_model_sensitivities.csv", "reference/adu_model_reference_lines.csv",
    "reference/pooled_revision_adoption_line.csv", "reference/pooled_revision_stage2_levels.csv",
    "reference/adu_model_reference_line_by_year.csv",
    "reference/pooled_revision_g3f2.csv", "reference/eligible_basis_g3f2.csv",
    "reference/wi_baseline_statewide.csv", "reference/wi_baseline_by_municipality.csv",
    "reference/wi_baseline_sensitivities.csv", "reference/wi_measured_permits_2022_2025.csv",
    "reference/wi_adu_rules.csv", "reference/wi_rights_exposure.csv", "reference/wi_town_zoning_status.csv",
    "reference/madison_adu_permits_by_year.csv", "reference/pleasant_prairie_adu_equivalent_by_year.csv",
    "reference/sun_prairie_adu_equivalent_by_year.csv", "reference/statewide_states_annual.csv",
    "reference/adu_model_baseline_only_effects.csv", "reference/pooled_convergence.csv", "reference/madison_like_cities.csv",
    "reference/pooled_adoption_points.csv", "reference/statewide_adoption_curve.csv",
    "reference/madison_like_annual.csv", "reference/madison_like_median_path.csv",
    "data/processed/model_run/results_long.parquet", "data/processed/foundation/areas.parquet",
    "data/processed/foundation/state_conditions.parquet", "data/processed/foundation/geo/areas_county.parquet",
    "data/processed/foundation/geo/areas_municipality.parquet",
    "data/raw/census_cb_2024/cb_2024_55_cousub_500k.zip", "data/raw/census_cb_2024/cb_2024_us_county_500k.zip",
    # Gate 5: unknown-rules variants (scripts/run_unknown_rules_variants.py) and legislative districts
    # (scripts/build_district_allocation.py); the district outlines are copied into the committed bundle.
    "reference/adu_model_unknown_rules_statewide.csv", "reference/adu_model_unknown_rules_statewide_by_year.csv",
    "reference/adu_model_unknown_rules_by_county.csv", "reference/adu_model_unknown_rules_by_context.csv",
    "data/processed/model_run/unknown_rules/results_long.parquet",
    "reference/adu_model_by_assembly_district.csv", "reference/adu_model_by_senate_district.csv",
    "reference/adu_model_district_crosswalk.csv", "reference/gate5_trace.csv",
    "data/processed/districts/geo_assembly.geojson", "data/processed/districts/geo_senate.geojson",
    # Gate 5 owner decision: "why areas differ" on the comparison screen (docs/gate5/MODEL_CHECKS.md, section 3b)
    "reference/gate5_context_contrast.csv", "reference/gate5_model_drivers.csv", "reference/gate5_context_examples.csv",
]
# Unknown-rules switch (docs/gate5/UI_CONTRACT.md section 1): screen labels, in switch order.
UNKNOWN = [("like_restricted", "Like places that restrict ADUs (adopted)"),
           ("like_prohibited", "Like places that prohibit ADUs"),
           ("like_benchmark", "Like places that already allow ADUs as the bill would")]
DISTRICT_CAVEAT = ("District figures share each municipality's result by where its single-family homes are (2020 census "
                   "blocks). They are not forecasts for any neighbourhood or lot.")
DISTRICT_METHOD = ("Each city, village and town's result is split across the districts it touches in proportion to its "
                   "single-family homes in each one. Homes are placed with the 2020 census blocks: each block's 2020 housing "
                   "units × its block group's share of single-family homes (ACS 2020–2024). 55 areas are split across "
                   "districts (Milwaukee across 14, Madison across 9); 1,842 lie in one district. Senate districts are the "
                   "sum of their three Assembly districts. Boundaries: the 2024 legislative districts (2023 Wisconsin Act 94), "
                   "Legislative Technology Services Bureau.")
CB_URL = "https://www2.census.gov/geo/tiger/GENZ2024/shp/"

PILOTS = {
    "madison": {"area_ids": ["muni:5502548000"], "jurisdiction_id": "5502548000", "role": "pilot",
                "permit_file": "reference/madison_adu_permits_by_year.csv", "stage": "issued"},
    "pleasant-prairie": {"area_ids": ["muni:5505963300"], "jurisdiction_id": "5505963300", "role": "pilot",
                         "permit_file": "reference/pleasant_prairie_adu_equivalent_by_year.csv", "stage": "issued"},
    "sun-prairie": {"area_ids": ["muni:5502578600"], "jurisdiction_id": "5502578600", "role": "same_market_check",
                    "permit_file": "reference/sun_prairie_adu_equivalent_by_year.csv", "stage": "application"},
}

STATE_NAMES = {"WA": "Washington", "OR": "Oregon", "VT": "Vermont", "UT": "Utah", "MA": "Massachusetts",
               "ME": "Maine", "RI": "Rhode Island", "CA": "California"}
SERIES_NAMES = {"WA_inc_exSeattle": "Washington law, measured in its cities excluding Seattle",
                "OR_panel32_exPortland": "Oregon law, measured in 32 cities excluding Portland",
                "VT_chittenden": "Vermont law, measured in Chittenden County",
                "UT_mih": "Utah law, measured in reporting cities",
                "MA_statewide": "Massachusetts law, measured statewide", "ME_statewide": "Maine law, measured statewide",
                "RI_statewide": "Rhode Island law, measured statewide"}

X_STATUS_TEXT = {
    "observed": "Observed: the place's own permit records",
    "estimated": "Calculated: a rules-group rate or a stated ramp, not the place's own permit records",
    "assumed": "Assumed: local ADU rules not coded; treated like places with restricted rules",
}
# ---------------------------------------------------------------------------------------------
# DISPLAY: the one place for scenario names, chart-key labels and scenario descriptions. Every screen
# and the brief read these from state.json ("labels" and each scenario), so renaming a scenario or
# swapping the reference line is a change here only.
# Owner review 2026-10-26: plain, editorial descriptions on top; the method in a "details" disclosure.
SCEN_NAME = {"lower": "Lower", "central": "Central", "upper": "Strong adoption"}
LABELS = {
    "baseline": "No statewide reform (baseline)",
    "scenario_chart": "Statewide ADU reform: {name} scenario",   # {name} = scenario name in lower case
    "band": "Range from the lower to the strong adoption scenario",
    "reference": "Median performance in {n} examples of statewide ADU reform",   # {n} = states in the line
    "added": "added permits",
}
# Scenario titles (editorial). The params file's lower label is the same ("Sluggish adoption").
SCEN_TITLE = {"lower": "Sluggish adoption", "central": "Typical adoption after a statewide ADU law",
              "upper": "The high end of what statewide-law states have reached"}
# Values used in the scenario explanations, read from the adopted fit (reference/pooled_revision_wi.csv, cap_a2 x A;
# AQ-061 refit): the common level at a typical place, law in force 4+ years (permits per 1,000 SF homes per year), and
# the 80% between-state factor (upper = central x SPREAD).
def _adopted_fit_value(col: str) -> float:
    rev = pd.read_csv(REF / "pooled_revision_wi.csv")
    return float(rev[rev.option.eq("cap_a2") & rev.config.eq("A_ca_in_common_level")][col].iloc[0])


COMMON_LEVEL = _adopted_fit_value("common_level_k4")
SPREAD = _adopted_fit_value("factor80")
# Reference line (owner decision 2026-10-26): median across all 8 statewide-law states, California included, observed
# through 2030, 2031 carried forward (dashed). Series: REFERENCE_FILE rows with line == REFERENCE_LINE.
REFERENCE_FILE = "reference/adu_model_reference_line_by_year.csv"
REFERENCE_LINE = "8_state_median"
# Madison's 2026 templated builder programme (docs/gate2/MADISON_PERMITS.md, section 5b)
PROGRAMME = {"units_2026": 29, "permits_2026": 20, "units_2026_without": 13, "two_unit_buildings": 9,
             "detached": 3, "conversions": 8, "sqft_unit": 998, "sqft_two_unit": 2994, "units_2025": 7, "total_2025": 14}
MADISON_IDS = {"muni:5502548000"}
MADISON_PROVISIONAL_THROUGH = "23 October 2026"   # docs/gate2/MADISON_PERMITS.md: permits downloaded to 2026-10-23
WATER_REASON = "Water area (Great Lakes or Green Bay): no homes, not drawn on the map"
PIECE_REASON = "No single-family homes in this piece of the area (a sliver across a county line)"


def madison_like() -> dict:
    """The Washington and Oregon cities like Madison (reference/madison_like_cities.csv) and their median path."""
    c = pd.read_csv(REF / "madison_like_cities.csv")
    c = c[c.state.isin(["WA", "OR"])]
    med = pd.read_csv(REF / "madison_like_median_path.csv")
    med = med[med.group.eq("WA+OR Madison-like (main)")].sort_values("year_since_law")
    by_state = {st: sorted(c[c.state.eq(st)].city) for st in ("WA", "OR")}
    return {"n": int(len(c)), "by_state": by_state, "median": [round(float(v), 3) for v in med.median_rate],
            "n_by_year": [int(v) for v in med.n_cities],
            "own_reform": int(c.local_reform_in_window.fillna(False).astype(bool).sum())}


def madison_texts(p: dict) -> dict:
    ml = madison_like()
    r = p["area_paths"]["madison_like_path"]["rates"]
    assert [round(x, 3) for x in r] == [round(x, 3) for x in ml["median"]], "Madison's path should be the WA+OR median"
    names = (f"{', '.join(ml['by_state']['WA'][:-1])} and {ml['by_state']['WA'][-1]} in Washington; "
             f"{', '.join(ml['by_state']['OR'][:-1])} and {ml['by_state']['OR'][-1]} in Oregon")
    last_n = ml["n_by_year"][-1]
    sens = pd.read_csv(REF / "adu_model_sensitivities.csv")
    pooled = float(sens[sens.change.str.startswith("Madison at its pooled")].difference_central.iloc[0])
    return {
        "title": "Cities like Madison",
        "text": (f"In Washington and Oregon, {ml['n']} cities similar to Madison in size and home values ({names}) had a "
                 f"median of {r[0]:.2f} permits per 1,000 single-family homes per year in the first year after their "
                 f"statewide ADU law, rising to {r[-1]:.2f} by year 5. Madison is modelled the same way: with the law, "
                 f"its rate follows that path in every scenario, while every other Wisconsin place, Madison's suburbs "
                 "included, follows the statewide estimate. This choice is being reviewed."),
        "detail": (f"Cities like Madison are defined in docs/gate3/MADISON_LIKE_CITIES.md: 20,000–120,000 single-family "
                   "homes, median home value $250,000–$500,000, not the state's largest city; the definition was fixed "
                   "before any city's permits were read. Path, years 1–5 (2027–2031 for Madison): "
                   + ", ".join(f"{x:.2f}" for x in r) + f" permits per 1,000 single-family homes per year; years 4 and 5 "
                   f"rest on the {last_n} Oregon cities only, as Washington's law is newer. {ml['own_reform']} of the "
                   f"{ml['n']} cities also changed their own ADU rules in the same window. The path replaces Madison's "
                   "statewide-model level (owner decision AQ-042, 2026-10-25); with the statewide-model level instead, "
                   f"Madison would add {pooled:,.0f} more permits over 2027–2031 (central scenario). The choice is under review at Gate 5."),
        # one short sentence, used in the map details panel and the brief
        "note": (f"Madison follows the observed path of {ml['n']} similar cities in Washington and Oregon ({r[0]:.2f} rising "
                 f"to {r[-1]:.2f} permits per 1,000 single-family homes per year, 2027–2031) in every scenario, so the law "
                 "adds less here per 1,000 homes than in its suburbs. This choice will be looked at again in December "
                 "2026, when Madison's 2026 permit count is final."),
    }


def basis_text(status: str, basis: str) -> str:
    """Plain words for wi_baseline_by_municipality.csv x_basis (the current-law rate's basis)."""
    b = str(basis)
    since = b.split("since ")[-1] if "since " in b else None
    if status == "observed":
        w = b.replace("observed ", "").split(" ")[0].replace("-", "–")
        if "candidate" in b:
            return (f"the place's own measured permits, {w} (candidate second-home records from city open data, matched by "
                    "rule and not checked one by one), held flat with no assumed rise after its 2025 ADU reform")
        return f"the place's own issued permits, {w}"
    if b.startswith("assumed ramp from Milwaukee"):
        return (f"an assumed ramp from Milwaukee's observed rate before its {since} ADU reform up to Madison's rate "
                "by mid-2029, because the new rules (ADUs by right, no parking) are close to Madison's; Milwaukee is coded "
                "restricted, so this is not the restricted-group rate")
    if b.startswith("benchmark group rate, ramping"):
        return f"the rate of places with benchmark-like rules (Madison's), ramping up from the prohibited-group rate since its rules changed on {since}"
    if b == "benchmark_group_rate":
        return "the rate of places with benchmark-like rules (Madison's observed rate)"
    if b == "prohibited_group_rate":
        return "the prohibited-group rate (Pleasant Prairie and Sun Prairie before reform, pooled)"
    if b.startswith("restricted group rate, ramping from its observed"):
        return f"the restricted-group rate, ramping up from its own observed prohibited-period rate since {since}"
    if b.startswith("restricted group rate, ramping"):
        return f"the restricted-group rate, ramping up from the prohibited-group rate since its rules changed on {since}"
    if b == "restricted_group_rate":
        return "the restricted-group rate (Madison 2014–2023 and Fitchburg, pooled)"
    if b == "uncoded_like_restricted_AQ027":
        return "rules not coded, so the restricted-group rate is assumed"
    return b
CLASS_TEXT = {
    "scenario_benchmark": "Already allows ADUs much like the benchmark law",
    "restricted": "Allows ADUs with restrictions",
    "prohibited_explicit": "Prohibits ADUs (explicitly)",
    "prohibited_implicit": "Prohibits ADUs (no provision allows them)",
    "undetermined": "Rules not coded (assumed restricted)",
}
CLASS_SHORT = {"scenario_benchmark": "Benchmark-like", "restricted": "Restricted", "prohibited_explicit": "Prohibited",
               "prohibited_implicit": "Prohibited", "undetermined": "Not coded"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def r(v, nd=4):
    """Round for JSON; NaN/None become null (missing is never zero)."""
    if v is None:
        return None
    try:
        if isinstance(v, float) and math.isnan(v):
            return None
    except TypeError:
        pass
    if pd.isna(v):
        return None
    return round(float(v), nd)


def s(v):
    return None if v is None or (not isinstance(v, str) and pd.isna(v)) else str(v)


def doc(path: str, label: str) -> dict:
    return {"label": label, "path": path, "url": DOC + path}


# --------------------------------------------------------------------------------------------
def load_inputs():
    missing = [p for p in INPUTS if not (ROOT / p).exists()]
    if missing:
        raise SystemExit("missing inputs (run the Gate 2-3 builds first, see README):\n  " + "\n  ".join(missing))
    hashes = [{"path": p, "sha256": sha256(ROOT / p)} for p in INPUTS]
    run_hash = hashlib.sha256("".join(h["sha256"] for h in hashes).encode()).hexdigest()[:10]
    return hashes, f"adu-{run_hash}"


def params():
    return json.loads((REF / "adu_model_params.json").read_text())


def stage2_levels() -> dict:
    s2 = pd.read_csv(REF / "pooled_revision_stage2_levels.csv")
    s2 = s2[s2.option.eq("cap_a2") & s2.config.eq("A_ca_in_common_level") & s2.in_stage2]
    return {row.cluster: round(float(row.level_with_law_k4), 2) for row in s2.itertuples()}


def scenario_defs(p: dict) -> list[dict]:
    lv = stage2_levels()
    lo, up = COMMON_LEVEL / SPREAD, COMMON_LEVEL * SPREAD
    others = sorted(((k, v) for k, v in lv.items() if k != "CA"), key=lambda kv: -kv[1])
    typical = ", ".join(f"{STATE_NAMES[k]} {v:.2f}" for k, v in others if 0.8 * COMMON_LEVEL <= v <= 1.25 * COMMON_LEVEL)
    unit = "permits per 1,000 single-family homes per year"
    # editorial text: what the scenario means (top level)
    text = {
        # Owner decision 2026-10-26 (AQ-043): lower = the average of the two slowest states, Rhode Island and Oregon.
        "lower": (f"Wisconsin performs like the slowest statewide reforms so far, Rhode Island and Oregon (average about "
                  f"{(lv['RI'] + lv['OR']) / 2:.2f} {unit} once the law is fully in force)."),
        "central": (f"Wisconsin performs like most of the eight states with a statewide ADU law: about {COMMON_LEVEL:.2f} "
                    f"permits per 1,000 single-family homes per year once the law has been in force 4 years ({typical}). "
                    f"California is one of the eight and counts toward this typical level, yet the level sits far below "
                    f"California's own {lv['CA']:.2f}."),
        "upper": (f"Wisconsin does better than every statewide-law state except California: about {up:.2f} {unit} once "
                  f"the law has been in force 4 years. Only California has gone higher ({lv['CA']:.2f}), and its laws "
                  "go beyond the benchmark in several ways (ADUs on apartment properties, more than one ADU per lot), "
                  "so this is the high end of the expected range."),
    }
    # method (for the details disclosure)
    method = {
        "lower": (f"The average of the two slowest statewide-law states, Rhode Island ({lv['RI']:.2f}) and Oregon "
                  f"({lv['OR']:.2f}): about {(lv['RI'] + lv['OR']) / 2:.2f} {unit} at a typical place once the law is fully "
                  f"in force (4 years or more), {p['paths']['lower']['level_from']['factor']:.4f} of the central level. Every "
                  "Wisconsin place's central level is multiplied by that factor, so the differences between places stay "
                  "the same. Rhode Island has only one year of data after its law (2025), so its level rests on one year. "
                  f"At Gate 3 the lower was the 10th percentile of the states' spread (central ÷ {SPREAD:.2f}); that is now a "
                  "sensitivity case."),
        "central": (f"The common level of the eight statewide-law states (California included), about {COMMON_LEVEL:.2f} "
                    f"{unit} at a typical place once the law has been in force 4 years. Wisconsin's statewide rate comes "
                    "from that level and Wisconsin's mix of home values, incomes and sizes; it is then spread across places "
                    "by home value alone, as places differ within the eight states."),
        "upper": (f"The central level times {SPREAD:.2f}: the 90th percentile of how much the eight states differ, "
                  f"about {up:.2f} {unit} at a typical place."),
    }
    out = []
    for k in PATHS:
        ramp = p["paths"][k]["ramp"]
        common = (f" In 2027–2029 the addition reaches {', '.join(f'{x:.2f}' for x in ramp[:3])} of its full size; full "
                  "from 2030. No Wisconsin place goes below a minimum rate set from Madison's own permits "
                  "(0.2345 per 1,000 single-family homes per year: Madison's 2022–2025 rate of 0.1876 divided by 0.8). "
                  "Madison itself follows the path of similar cities in Washington and Oregon in every scenario.")
        out.append({"id": k, "label": SCEN_NAME[k], "name": f"{SCEN_NAME[k].lower()} scenario",
                    "chart_label": LABELS["scenario_chart"].format(name=SCEN_NAME[k].lower()),
                    "title": SCEN_TITLE[k], "description": SCEN_TITLE[k], "text": text[k], "info": method[k] + common,
                    "todo": None,
                    "gate3_label": p["paths"][k]["label"], "basis": p["paths"][k]["basis"], "ramp": ramp})
    return out


# --------------------------------------------------------------------------------------------
def build_state(p: dict) -> dict:
    sc = pd.read_parquet(PROC / "foundation/state_conditions.parquet")
    st = sc[sc.area_id.astype(str).eq("55")]

    def ind(name, year=None):
        d = st[st.indicator.eq(name)]
        if year is not None:
            d = d[d.year.eq(year)]
        return d

    def one(name):
        row = ind(name).iloc[0]
        return {"value": r(row.value, 4), "moe": r(row.moe, 4), "status": row.status, "vintage": row.source_vintage,
                "source_id": row.source_id}

    homes = one("units_1_detached")
    assert int(homes["value"]) == WI_HOMES, "ACS one-unit detached homes changed; update WI_HOMES"
    mix = [{"id": k, "label": lab, **one(k)} for k, lab in (
        ("units_1_detached", "Single-family, detached"), ("units_1_attached", "Single-family, attached (townhouses)"),
        ("units_2_4", "Buildings with 2–4 homes"), ("units_5_plus", "Buildings with 5 or more homes"),
        ("mobile_home", "Mobile homes"))]
    pep = [{"year": int(x.year), "value": r(x.value, 0), "status": x.status, "vintage": x.source_vintage, "source_id": x.source_id}
           for x in ind("housing_units").sort_values("year").itertuples()]
    bps = []
    for y in range(2015, 2026):
        row = {"year": y}
        for k in ("permitted_units_total", "permitted_units_1unit", "permitted_units_2_4", "permitted_units_5plus"):
            d = ind(k, y)
            row[k.replace("permitted_units_", "")] = r(d.value.iloc[0], 0) if len(d) else None
            if len(d):
                row["reported_share"] = r(d.reporting_coverage.iloc[0], 4)
                row["vintage"] = d.source_vintage.iloc[0]
                row["source_id"] = d.source_id.iloc[0]
                row["source"] = "Census Building Permits Survey"
        bps.append(row)
    # General housing production as a rate (docs/gate5/MODEL_CHECKS.md section 3e): all homes permitted in the last
    # BPS year per 1,000 housing units (PEP, 1 July of the same year). A different denominator from the ADU rates.
    b_last = next(b for b in reversed(bps) if b.get("total") is not None)
    pep_same = next(x for x in pep if x["year"] == b_last["year"])
    production_rate = {"year": b_last["year"], "value": r(b_last["total"] / pep_same["value"] * 1000, 2),
                       "numerator": b_last["total"], "denominator": pep_same["value"], "status": "calculated",
                       "units": "homes permitted per 1,000 housing units",
                       "source": f"Census Building Permits Survey {b_last['year']} (final) ÷ Census Population Estimates, "
                                 f"1 July {b_last['year']} ({pep_same['vintage']})",
                       "source_id": f"{b_last['source_id']}; {pep_same['source_id']}"}

    st_tot = pd.read_csv(REF / "adu_model_statewide.csv").set_index("path")
    by_year = pd.read_csv(REF / "adu_model_statewide_by_year.csv")
    base_rng = pd.read_csv(REF / "wi_baseline_statewide.csv").set_index("year")
    cen = by_year[by_year.path.eq("central")].sort_values("year")
    baseline = {"by_year": [r(v, 2) for v in cen.baseline_units], "total": r(st_tot.loc["central", "baseline_units"], 2),
                "low_total": r(base_rng.loc["2027-2031", "low"], 2), "high_total": r(base_rng.loc["2027-2031", "high"], 2),
                "low_by_year": [r(base_rng.loc[str(y), "low"], 2) for y in YEARS],
                "high_by_year": [r(base_rng.loc[str(y), "high"], 2) for y in YEARS],
                "bridge_2026": {"low": r(base_rng.loc["2026", "low"], 2), "central": r(base_rng.loc["2026", "central"], 2),
                                "high": r(base_rng.loc["2026", "high"], 2)},
                "rate_per_1000_per_year": r(st_tot.loc["central", "baseline_units"] / 5 / WI_HOMES * 1000, 4),
                "source": "reference/adu_model_statewide.csv, adu_model_statewide_by_year.csv; range from reference/wi_baseline_statewide.csv"}
    scen = []
    for d in scenario_defs(p):
        yy = by_year[by_year.path.eq(d["id"])].sort_values("year")
        add = [r(v, 2) for v in yy.additional_units]
        rate = [r((b + a) / WI_HOMES * 1000, 4) for b, a in zip(yy.baseline_units, yy.additional_units)]
        scen.append({**d, "additional_by_year": add, "additional_total": r(st_tot.loc[d["id"], "additional_units"], 2),
                     "with_law_total": r(st_tot.loc[d["id"], "additional_units"] + st_tot.loc[d["id"], "baseline_units"], 2),
                     "with_law_rate_by_year": rate})
    al = pd.read_csv(ROOT / REFERENCE_FILE)
    al = al[al.line.eq(REFERENCE_LINE)].sort_values("forecast_year")
    rl = pd.read_csv(REF / "adu_model_reference_lines.csv").set_index("line_id").loc[REFERENCE_LINE]
    n_states = 8 if REFERENCE_LINE.startswith("8_") else 7
    cf = [int(y) for y in al[al.carried_forward.astype(bool)].forecast_year]
    last_drawn = min(cf) - 1 if cf else YEARS[-1]
    with_ca = "California" if REFERENCE_LINE.startswith("8_") else None
    ref_line = {"label": LABELS["reference"].format(n=n_states), "n_series": n_states,
                "carried_forward_years": cf,
                "info": (f"The middle (median) of what the {n_states} states with a statewide ADU law"
                         f"{', California included,' if with_ca else ' (not California)'} actually permitted in each year "
                         "after their law, applied to Wisconsin's single-family homes. It is a check on the scenarios, "
                         "not a scenario."),
                "detail": ("States with data in each year after the law: "
                           + "; ".join(f"year {int(x.year_since_law)} ({int(x.forecast_year)}): {int(x.n_states)}"
                                       + (f", {x.states}" if isinstance(x.states, str) and x.states else "")
                                       for x in al.itertuples())
                           + f". Drawn through {last_drawn}"
                           + (f"; {', '.join(map(str, cf))} carries {last_drawn} forward (dashed), because only one state "
                              "has that many years of data. " if cf else ". ")
                           + "Non-California series leave out ADUs built with a new house on an empty lot (× 0.951); "
                           "California's counts use the cap of 2 ADUs per parcel and the multifamily-lot rule. Median "
                           "rates: " + ", ".join(f"{v:.2f}" for v in al.median_rate) + " permits per 1,000 single-family "
                           f"homes per year in 2027–2031. Added permits over the observed years only ({rl.observed_years}): "
                           f"{float(rl.additional_observed_years):,.0f}. Series: {REFERENCE_FILE} ({REFERENCE_LINE})."),
                "why_central_differs": (f"The central scenario ({st_tot.loc['central', 'additional_units']:,.0f} added permits) "
                                        f"and this line ({al.additional.sum():,.0f}) are built differently. The line applies "
                                        "one median state rate to every Wisconsin home. The central scenario gives each place "
                                        "the level that similar places reached in the eight states (by home values, incomes "
                                        "and size), with a ramp-up in the first three years, and no place below a minimum rate "
                                        "set from Madison's permits."),
                "rate_by_year": [r(v, 4) for v in al.median_rate], "additional_by_year": [r(v, 2) for v in al.additional],
                "additional_total": r(al.additional.sum(), 1),
                "with_law_by_year": [r(v, 2) for v in al.with_law_total],
                "source": f"{REFERENCE_FILE} ({REFERENCE_LINE}), reference/adu_model_reference_lines.csv"}
    ctx = pd.read_csv(REF / "adu_model_by_context.csv")
    contrast = pd.read_csv(REF / "gate5_context_contrast.csv").set_index("context")
    homes_ctx = pd.read_csv(REF / "wi_baseline_by_municipality.csv").groupby("context_group").homes.sum()
    contexts = []
    for g, lab in (("urban", "Urban"), ("suburban", "Suburban"), ("small_community", "Small communities"), ("rural", "Rural")):
        d = ctx[ctx.context_group.eq(g)].set_index("path")
        cc = contrast.loc[g]
        contexts.append({"id": g, "label": lab, "homes": int(homes_ctx.get(g, 0)), "baseline": r(d.loc["central", "baseline_units"], 2),
                         **{f"additional_{k}": r(d.loc[k, "additional_units"], 2) for k in PATHS},
                         # reference/gate5_context_contrast.csv: homes-weighted geometric means of ACS 2020-2024 medians;
                         # rates in permits per 1,000 single-family homes per year
                         "median_home_value": r(cc.median_home_value_homes_weighted_geomean, 0),
                         "median_income": r(cc.median_income_homes_weighted_geomean, 0),
                         "x_rate": r(cc.x_current_law_rate, 4), "y_rate_2031_central": r(cc.y_with_law_rate_2031_central, 4),
                         "additional_rate_central": r(cc.additional_rate_central_per_1000_per_year, 4)})
    cs = contrast.loc["state"]
    drv = pd.read_csv(REF / "gate5_model_drivers.csv").set_index("term")
    context_why = {
        "state": {"median_home_value": r(cs.median_home_value_homes_weighted_geomean, 0),
                  "median_income": r(cs.median_income_homes_weighted_geomean, 0), "x_rate": r(cs.x_current_law_rate, 4),
                  "y_rate_2031_central": r(cs.y_with_law_rate_2031_central, 4),
                  "additional_rate_central": r(cs.additional_rate_central_per_1000_per_year, 4)},
        # the adopted pooled model refitted, within-state terms: rate ratio for a place 10% above its state's average.
        # alloc_value_dev (value-only fit) spreads the statewide total across places; value_dev, income_dev and log_homes
        # (value-income-size fit) set only the statewide rate (AQ-061)
        "drivers": [{"term": t, "role": drv.loc[t, "role"], "coefficient": r(drv.loc[t, "coefficient_log_scale"], 4),
                     "se": r(drv.loc[t, "se_cluster"], 4),
                     "ratio_10pct": r(drv.loc[t, "rate_ratio_for_10pct_higher"], 4), "meaning": drv.loc[t, "meaning"]}
                    for t in ("alloc_value_dev", "value_dev", "income_dev", "log_homes")],
        # the three largest places in each group (reference/gate5_context_examples.csv)
        "examples": [{"context": x.context_group, "name": x.name, "homes": int(x.homes),
                      "median_home_value": r(x.median_home_value, 0), "median_income": r(x.median_income, 0),
                      "additional_rate_central": r(x.additional_rate_central_per_1000_per_year, 4)}
                     for x in pd.read_csv(REF / "gate5_context_examples.csv").itertuples()],
        "source": ("reference/gate5_context_contrast.csv and reference/gate5_model_drivers.csv "
                   "(docs/gate5/MODEL_CHECKS.md, section 3b); examples from reference/gate5_context_examples.csv"),
    }
    return {"homes": homes, "housing_units_pep": pep, "production_rate": production_rate,
            "acs_period": "ACS 2020–2024 5-year estimates: an average over the five years 2020–2024, not a 2024 count",
            "pep_note": "Census Population Estimates for 1 July each year; no published margin of error", "acs_total_units": one("total_housing_units_acs"),
            "occupied": one("occupied_units"), "vacant": one("vacant_units"), "vacancy_rate": one("vacancy_rate"),
            "mix": mix, "bps": bps, "baseline": baseline, "scenarios": scen, "reference_line": ref_line, "contexts": contexts,
            "context_why": context_why,
            "labels": {"baseline": LABELS["baseline"], "band": LABELS["band"], "reference": ref_line["label"],
                       "added": LABELS["added"]},
            "page_intro": {
                "compare": ("This page shows how many permits for second homes on single-family lots (accessory dwelling "
                            "units, or ADUs, and conversions of a house into a duplex) Wisconsin can expect if the "
                            "statewide benchmark ADU law takes effect on 1 January 2027. It shows a baseline of how many "
                            "would be permitted without the law, and then three scenarios for the bottom, middle and top "
                            "of what we expect, based on how statewide reform has rolled out in other states. They are "
                            "scenarios, not confidence intervals: each one describes a way Wisconsin could respond, "
                            "not a statistical probability."),
            }}


# --------------------------------------------------------------------------------------------
def build_areas(p: dict) -> tuple[list, list, dict]:
    res = pd.read_parquet(PROC / "model_run/results_long.parquet")
    areas = pd.read_parquet(PROC / "foundation/areas.parquet")
    munis = pd.read_csv(REF / "wi_baseline_by_municipality.csv")
    rx = pd.read_csv(REF / "wi_rights_exposure.csv", dtype={"jurisdiction_id": str})
    rx = rx[rx.scenario_id.eq("adu_full")].drop_duplicates("jurisdiction_id").set_index("jurisdiction_id")
    zon = pd.read_csv(REF / "wi_town_zoning_status.csv").set_index("area_id")
    counties = areas[areas.level.eq("county")].set_index("area_id")
    geo = areas[areas.level.eq("municipality")].set_index("area_id")
    pilot_of = {aid: slug for slug, d in PILOTS.items() for aid in d["area_ids"]}

    piv_add = res.pivot_table(index="area_id", columns=["path", "year"], values="additional_units", aggfunc="sum")
    piv_base = res[res.path.eq("central")].pivot_table(index="area_id", columns="year", values="baseline_units", aggfunc="sum")
    yrate = res.pivot_table(index="area_id", columns=["path", "year"], values="y_rate", aggfunc="first")

    rows = []
    for m in munis.itertuples(index=False):
        aid = m.area_id
        cid = str(geo.loc[aid, "parent_county_id"])
        jid = None if pd.isna(m.place_id) else str(int(m.place_id))
        ex = rx.loc[jid] if jid is not None and jid in rx.index else None
        if ex is not None:
            rights_status = "verified" if ex.class_basis == "coded_verified" else "source_lead"
        else:
            rights_status = "assumed"
        name = m.name
        n_same = (munis.name == name).sum()
        label = name if n_same == 1 else f"{name} ({m.county})"
        homes = int(m.homes)
        row = {
            "id": aid, "name": label, "county_id": cid, "county": m.county, "type": m.muni_type,
            "context": s(m.context_group), "homes": homes,
            "x_rate": r(m.x_central, 4), "x_low": r(m.x_low, 4), "x_high": r(m.x_high, 4), "x_status": m.x_status,
            "x_basis": m.x_basis, "basis_text": basis_text(m.x_status, m.x_basis), "current_class": m.current_class, "rights_status": rights_status,
            "rights_added_text": s(ex.rights_added_text) if ex is not None else None,
            "zoning_status": s(zon.loc[aid, "zoning_status"]) if aid in zon.index else None,
            # 4 decimals per year so that sums of many areas stay within 0.01 permits of the engine
            "base": [r(piv_base.loc[aid, i], 4) for i in range(1, 6)],
            "base_low_5yr": r(m.b5yr_low, 3), "base_high_5yr": r(m.b5yr_high, 3),
            "add": {k: [r(piv_add.loc[aid, (k, i)], 4) for i in range(1, 6)] for k in PATHS},
            "y_rate_y5": {k: r(yrate.loc[aid, (k, 5)], 4) for k in PATHS},
            "pilot": pilot_of.get(aid),
        }
        if homes == 0:
            water = name.startswith("County subdivisions not defined")
            row["missing_reason"] = WATER_REASON if water else PIECE_REASON
            row["water"] = water
        if aid in MADISON_IDS:
            row["note"] = madison_texts(p)["note"]
        rows.append(row)

    # counties = sums of their municipality pieces, summed unrounded and then rounded
    # (checked against reference/adu_model_by_county.csv)
    crow = []
    df = pd.DataFrame(rows)
    for cid, g in df.groupby("county_id"):
        ids = list(g.id)
        crow.append({
            "id": cid, "name": counties.loc[cid, "name"], "homes": int(g.homes.sum()), "n_areas": int(len(g)),
            "base": [r(piv_base.loc[ids, i].sum(), 6) for i in range(1, 6)],
            "add": {k: [r(piv_add.loc[ids, (k, i)].sum(), 6) for i in range(1, 6)] for k in PATHS},
            "homes_by_status": {st: int(g[g.x_status.eq(st)].homes.sum()) for st in ("observed", "estimated", "assumed")},
            "context": s(counties.loc[cid, "context_group"]),
        })
    crow.sort(key=lambda c: c["name"])
    rows.sort(key=lambda a: (-a["homes"], a["name"]))
    return crow, rows, {"n_munis": len(rows), "n_counties": len(crow)}


# --------------------------------------------------------------------------------------------
def build_unknown_rules(munis: list, counties: list) -> dict:
    """The three precomputed unknown-rules runs (one run group) for the switch on "How sure" and the Where map.

    Statewide, by-year and by-context figures come from the reference CSVs. Per-area and per-county yearly values
    come from the variant engine run (model_run/unknown_rules/results_long.parquet) and are written only where a
    variant differs from the adopted run (uncoded places); every other area keeps its adopted values.
    """
    st = pd.read_csv(REF / "adu_model_unknown_rules_statewide.csv")
    by = pd.read_csv(REF / "adu_model_unknown_rules_statewide_by_year.csv")
    ctx = pd.read_csv(REF / "adu_model_unknown_rules_by_context.csv")
    res = pd.read_parquet(PROC / "model_run/unknown_rules/results_long.parquet")
    assert st.run_group_id.nunique() == 1 and res.run_group_id.nunique() == 1 and st.run_group_id.iloc[0] == res.run_group_id.iloc[0]
    by_id = {a["id"]: a for a in munis}
    county_of = {a["id"]: a["county_id"] for a in munis}
    variants, areas_v, counties_v = [], {}, {}
    for vid, label in UNKNOWN:
        s = st[st.unknown_treatment.eq(vid)].set_index("path")
        b = by[by.unknown_treatment.eq(vid)]
        cx = ctx[ctx.unknown_treatment.eq(vid)]
        yr = lambda p, col: [r(v, 2) for v in b[b.path.eq(p)].sort_values("forecast_year")[col]]
        variants.append({
            "id": vid, "label": label, "adopted": bool(s.adopted.iloc[0]), "contract_enum": s.contract_enum.iloc[0],
            "run_id": s.run_id.iloc[0], "x_rate_uncoded": r(s.x_rate_uncoded.iloc[0], 4),
            "baseline_total": r(s.loc["central", "baseline_units"], 2),
            "additional_total": {p: r(s.loc[p, "additional_units"], 2) for p in PATHS},
            "with_law_total": {p: r(s.loc[p, "total_with_law"], 2) for p in PATHS},
            "d_baseline": r(s.loc["central", "d_baseline_units"], 2),
            "d_additional": {p: r(s.loc[p, "d_additional_units"], 2) for p in PATHS},
            "d_with_law": {p: r(s.loc[p, "d_total_with_law"], 2) for p in PATHS},
            "baseline_by_year": yr("central", "baseline_units"),
            "additional_by_year": {p: yr(p, "additional_units") for p in PATHS},
            "with_law_by_year": {p: yr(p, "total_with_law") for p in PATHS},
            "contexts": [{"id": g, "homes": int(d.homes.iloc[0]), "uncoded_homes": int(d.uncoded_homes.iloc[0]),
                          "baseline": r(d[d.path.eq("central")].baseline_units.iloc[0], 2),
                          **{f"additional_{p}": r(d[d.path.eq(p)].additional_units.iloc[0], 2) for p in PATHS}}
                         for g, d in cx.groupby("context_group", sort=False)],
        })
        v = res[res.unknown_treatment.eq(vid)]
        pa = v.pivot_table(index="area_id", columns=["path", "year"], values="additional_units", aggfunc="sum")
        pb = v[v.path.eq("central")].pivot_table(index="area_id", columns="year", values="baseline_units", aggfunc="sum")
        diff = {}
        for aid in pb.index:
            a = by_id[aid]
            base = [r(pb.loc[aid, i], 4) for i in range(1, 6)]
            add = {k: [r(pa.loc[aid, (k, i)], 4) for i in range(1, 6)] for k in PATHS}
            if base != a["base"] or add != a["add"]:
                diff[aid] = {"base": base, "add": add}
        if vid == "like_restricted":
            assert not diff, f"adopted variant differs from the adopted run in {len(diff)} areas"
            continue
        areas_v[vid] = diff
        cty = {}
        for cid in sorted({county_of[aid] for aid in diff}):
            ids = [a for a in pb.index if county_of[a] == cid]
            cty[cid] = {"base": [r(pb.loc[ids, i].sum(), 6) for i in range(1, 6)],
                        "add": {k: [r(pa.loc[ids, (k, i)].sum(), 6) for i in range(1, 6)] for k in PATHS}}
        counties_v[vid] = cty
    first = st.iloc[0]
    return {"run_group_id": first.run_group_id, "uncoded_areas": int(first.uncoded_areas),
            "uncoded_homes": int(first.uncoded_homes), "state_homes": int(first.state_homes),
            "default": "like_restricted", "variants": variants, "areas": areas_v, "counties": counties_v,
            "district_note": ("Districts are shown for the adopted assumption only (uncoded places like places that "
                              "restrict ADUs). The other two assumptions were not split by district."),
            "source": "reference/adu_model_unknown_rules_*.csv; data/processed/model_run/unknown_rules/results_long.parquet"}


def build_districts(out: Path) -> dict:
    """Assembly and Senate district tables, area lists and (copied, simplified) outlines for the Where screen."""
    import geopandas as gpd
    cw = pd.read_csv(REF / "adu_model_district_crosswalk.csv", dtype={"assembly_district": str, "senate_district": str})
    levels, label_feats, sizes = {}, [], {}
    for level, prefix, f in (("assembly", "asm:", "adu_model_by_assembly_district.csv"),
                             ("senate", "sen:", "adu_model_by_senate_district.csv")):
        d = pd.read_csv(REF / f, dtype={"district": str})
        rows_, unalloc = [], None
        keys = sorted(d.district.unique(), key=lambda x: (x == "unallocated", int(x) if x.isdigit() else 0))
        for dist in keys:
            g = d[d.district.eq(dist)]
            yr = lambda p, col: [r(v, 6) for v in g[g.path.eq(p) & g.forecast_year.ne("2027-2031")].sort_values("forecast_year")[col]]
            row = {"id": f"{prefix}{dist}", "district": dist, "name": g.district_label.iloc[0],
                   "homes": r(g.homes.iloc[0], 1), "base": yr("central", "baseline_units"),
                   "add": {p: yr(p, "additional_units") for p in PATHS}}
            if dist == "unallocated":
                unalloc = row
                continue
            col = "assembly_district" if level == "assembly" else "senate_district"
            parts = cw[cw[col].eq(dist)].groupby(["area_id", "name"], as_index=False).agg(
                homes_allocated=("homes_allocated", "sum"), area_homes=("area_homes", "first"))
            parts = parts.sort_values("homes_allocated", ascending=False)
            row["n_areas"] = int(len(parts))
            row["places"] = [{"id": x.area_id, "name": x.name, "homes": r(x.homes_allocated, 0),
                              "share_of_place": r(x.homes_allocated / x.area_homes, 3) if x.area_homes else None}
                             for x in parts.head(8).itertuples()]
            if level == "senate":
                row["assembly"] = sorted({int(a) for a in cw[cw.senate_district.eq(dist)].assembly_district})
            rows_.append(row)
        assert unalloc is not None, f"{f}: the unallocated row must stay in the table"
        levels[level] = {"rows": rows_, "unallocated": unalloc}

        g = gpd.read_file(PROC / f"districts/geo_{level}.geojson").to_crs(4326)
        g["id"] = prefix + g.district.astype(int).astype(str)
        pts = g.to_crs(3071).geometry.representative_point().to_crs(4326)
        for aid, pt, num in sorted(zip(g.id, pts, g.district.astype(int)), key=lambda t: t[2]):
            label_feats.append({"type": "Feature", "properties": {"id": aid, "name": str(num), "kind": level},
                                "geometry": {"type": "Point", "coordinates": [round(pt.x, 4), round(pt.y, 4)]}})
        g["geometry"] = g.geometry.set_precision(1e-4)
        g = g[~g.geometry.is_empty]
        assert g.geometry.is_valid.all(), f"invalid {level} polygons after rounding"
        fc = json.loads(g[["id", "geometry"]].to_json(drop_id=True))
        fc.pop("bbox", None)
        for feat in fc["features"]:
            feat["properties"] = {"id": feat["properties"]["id"]}
            feat.pop("bbox", None)
        (out / f"geo_{level}.json").write_text(json.dumps(fc, separators=(",", ":")))
        sizes[level] = len(fc["features"])
    (out / "geo_district_labels.json").write_text(json.dumps({"type": "FeatureCollection", "features": label_feats},
                                                             separators=(",", ":")))
    return {"levels": levels, "caveat": DISTRICT_CAVEAT, "method": DISTRICT_METHOD,
            "homes_range": [min(x["homes"] for x in levels["assembly"]["rows"]), max(x["homes"] for x in levels["assembly"]["rows"])],
            "boundaries": "Wisconsin State Assembly (99) and Senate (33) districts, 2024 plan (2023 Wisconsin Act 94), Legislative Technology Services Bureau",
            "source": "reference/adu_model_by_assembly_district.csv, adu_model_by_senate_district.csv, adu_model_district_crosswalk.csv",
            "sizes": sizes}


def build_trace() -> list:
    """How much of the central addition rests on observed, estimated and assumed current-law rates (gate5_trace.csv)."""
    t = pd.read_csv(REF / "gate5_trace.csv")
    t = t[t.context.eq("all")] if "all" in set(t.context) else t.groupby("x_status", as_index=False).sum(numeric_only=True)
    out = []
    for stt in ("observed", "estimated", "assumed"):
        x = t[t.x_status.eq(stt)].iloc[0]
        out.append({"status": stt, "areas": int(x.areas), "homes": int(x.homes), "baseline": r(x.baseline_5yr, 2),
                    **{f"additional_{p}": r(x[f"additional_{p}_5yr"], 2) for p in PATHS}})
    return out


# --------------------------------------------------------------------------------------------
def model_facts() -> dict:
    """Numbers quoted in running text (cards, challenges), read from the adopted outputs so the text follows a rerun."""
    st = pd.read_csv(REF / "adu_model_statewide.csv").set_index("path")
    by = pd.read_csv(REF / "adu_model_statewide_by_year.csv")
    sens = pd.read_csv(REF / "adu_model_sensitivities.csv")
    ctx = pd.read_csv(REF / "adu_model_by_context.csv")
    homes = pd.read_csv(REF / "wi_baseline_by_municipality.csv").groupby("context_group").homes.sum()
    p = params()

    def case(prefix):
        return float(sens[sens.change.str.startswith(prefix)].central_additional_5yr.iloc[0])

    def bcase(prefix):
        return float(sens[sens.change.str.startswith(prefix)].baseline_5yr.iloc[0])
    cen = by[by.path.eq("central")].sort_values("year")
    rural = ctx[ctx.context_group.eq("rural") & ctx.path.eq("central")].additional_units.iloc[0]
    return {"base": float(st.loc["central", "baseline_units"]), "cen": float(st.loc["central", "additional_units"]),
            "base_rate": float(st.loc["central", "baseline_units"]) / 5 / WI_HOMES * 1000,
            "cen_rate_y": [(b + a) / WI_HOMES * 1000 for b, a in zip(cen.baseline_units, cen.additional_units)],
            "no_ramp": case("no ramp"), "rural_floor": case("rural and small"),
            "uncoded_base": bcase("Places with uncoded rules"), "ramp": p["paths"]["central"]["ramp"],
            "rural": float(rural), "rural_homes": int(homes.get("rural", 0))}


def build_uncertainty(areas: list) -> dict:
    df = pd.DataFrame(areas)
    cov = []
    for st in ("observed", "estimated", "assumed"):
        g = df[df.x_status.eq(st)]
        cov.append({"status": st, "label": X_STATUS_TEXT[st], "areas": int(len(g)), "homes": int(g.homes.sum()),
                    "baseline": round(sum(sum(b) for b in g.base), 2),
                    **{f"additional_{k}": round(sum(sum(a[k]) for a in g["add"]), 2) for k in PATHS}})
    rights = []
    for st, lab in (("verified", "Coded from the local ordinance, every provision checked"),
                    ("source_lead", "Coded from the local ordinance, some provisions from a source lead not yet checked"),
                    ("assumed", "Not coded: treated like places with restricted rules (assumed)")):
        g = df[df.rights_status.eq(st)]
        rights.append({"status": st, "label": lab, "areas": int(len(g)), "homes": int(g.homes.sum()),
                       "additional_central": round(sum(sum(a["central"]) for a in g["add"]), 2)})
    classes = []
    rb = pd.read_csv(REF / "adu_model_by_rights_basis.csv")
    for c in ("scenario_benchmark", "restricted", "prohibited_explicit", "prohibited_implicit", "undetermined"):
        d = rb[rb.rights_basis.eq(c)].set_index("path")
        g = df[df.current_class.eq(c)]
        classes.append({"id": c, "label": CLASS_TEXT[c], "areas": int(len(g)), "homes": int(g.homes.sum()),
                        "baseline": r(d.loc["central", "baseline_units"], 2),
                        **{f"additional_{k}": r(d.loc[k, "additional_units"], 2) for k in PATHS}})

    sens = pd.read_csv(REF / "adu_model_sensitivities.csv")
    # Each recorded case carries `moves` (which number it changes) and a plain `description`
    # (reference/adu_model_sensitivities.csv, scripts/run_adu_model.py). Groups: "addition" = the statewide addition from
    # the law; "baseline" = the current-law baseline only; "local" = where permits land, not the state total.
    GROUP = {"none (adopted)": "addition", "statewide addition": "addition", "baseline only": "baseline",
             "local distribution": "local", "local distribution only": "local"}
    # Short plain names for the technical `change` text (display only); unknown cases fall back to the recorded text.
    SHORT = [("adopted", "Adopted model (the scenarios)"),
             ("Lower as a statistical 10th percentile", "Lower scenario at the 10th percentile of the state spread (Gate 3 definition)"),
             ("California out", "Leave California out of the typical level"),
             ("no ramp", "No slow start: full effect from 2027"),
             ("multiplicative", "The law multiplies today's rates (instead of lifting places to other states' levels)"),
             ("California-only", "Predict Wisconsin from California's cities only"),
             ("eligible-property", "Count per eligible property, not per single-family home"),
             ("LA-calibrated", "A stricter correction for California's ADUs on apartment properties"),
             ("rural and small", "Rural places and small communities held at the minimum rate"),
             ("Madison at its pooled", "Madison on the statewide estimate, like every other place"),
             ("no reporting-share", "Do not scale up states' counts for towns that did not report"),
             ("reporting-share correction for Maine", "Scale up for non-reporting towns in Maine, Massachusetts, Rhode Island only"),
             ("Washington's law years", "Count Washington's law years from enactment, not local compliance"),
             ("Vermont 2024 dropped", "Leave out Vermont's 2024 count (changed source)"),
             ("Vermont dropped", "Leave Vermont out of the comparison states"),
             ("all three AQ-061", "Comparison-state counts and coding as at Gate 4"),
             ("no top-code", "Let small high-value villages keep their extrapolated rates")]
    cases = []
    for row in sens.itertuples(index=False):
        if row.moves not in GROUP:
            raise SystemExit(f"unknown `moves` value in adu_model_sensitivities.csv: {row.moves!r}")
        lab = next((v for k, v in SHORT if row.change.startswith(k)), row.change[:1].upper() + row.change[1:])
        cases.append({"id": "".join(c if c.isalnum() else "-" for c in lab.lower()).strip("-")[:40], "group": GROUP[row.moves],
                      "label": lab, "what": row.description, "change_as_recorded": row.change,
                      "lower": r(row.lower_additional_5yr, 1), "central": r(row.central_additional_5yr, 1),
                      "upper": r(row.upper_additional_5yr, 1), "difference_central": r(row.difference_central, 1),
                      "baseline": r(row.baseline_5yr, 1), "kind": row.kind, "source": row.source,
                      "missing_reason": None if not pd.isna(row.lower_additional_5yr) else "central only"})

    # Baseline-only cases: their effect on the baseline, the addition and the total with the law
    # (reference/adu_model_baseline_only_effects.csv, scripts/run_baseline_only_effects.py).
    bo = pd.read_csv(REF / "adu_model_baseline_only_effects.csv")
    baseline_only = []
    for x in bo.itertuples(index=False):
        if x.case == "adopted":
            continue
        baseline_only.append({"id": x.case, "label": x.label, "what": x.description,
                              "baseline": r(x.baseline_central, 1), "d_baseline": r(x.d_baseline_central, 1),
                              "d_additional": r(x.d_additional_central, 1), "d_with_law": r(x.d_with_law_central, 1),
                              "d_additional_lower": r(x.d_additional_lower, 1), "d_additional_upper": r(x.d_additional_upper, 1)})
    unc_case = bo[bo.case.eq("uncoded-prohibited")].iloc[0]
    tot0 = float(bo[bo.case.eq("adopted")].with_law_central.iloc[0])
    local = {
        "text": ("Each place's rate with the law comes from what similar places reached in the statewide-law states (by home "
                 "value), not from its current local rules. So if a city's rules are coded wrong, its "
                 "current-law baseline is wrong, and the law's addition there moves by about the same amount the other way; "
                 "the total with the law barely moves. Coding errors change the split between baseline and addition much "
                 "more than the number of permits expected with the law."),
        "example": (f"Example: if every place with uncoded rules behaved like places that prohibit ADUs, the baseline would "
                    f"fall by {abs(unc_case.d_baseline_central):,.0f} permits over 2027–2031, the addition would rise by "
                    f"{unc_case.d_additional_central:,.0f}, and the total with the law would fall by "
                    f"{abs(unc_case.d_with_law_central):,.0f} ({abs(unc_case.d_with_law_central) / tot0 * 100:.1f}% of "
                    f"{tot0:,.0f}; central scenario)."),
        "not_computed": "Re-coding individual places one at a time has not been run as separate cases.",
    }
    g3 = pd.read_csv(REF / "pooled_revision_g3f2.csv")
    eb = pd.read_csv(REF / "eligible_basis_g3f2.csv")

    def g3v(opt, cfg, col="rms_log_error"):
        return r(g3[g3.option.eq(opt) & g3.config.eq(cfg)][col].iloc[0], 3)

    def ebv(run, cfg):
        return r(eb[eb.run.eq(run) & eb.config.eq(cfg)].rms_log_error.iloc[0], 3)

    robust = [
        {"label": "Adopted: ADU units per one-unit detached home, cap + A2", "adopted": True,
         "a": g3v("cap_a2", "A_ca_in_common_level"), "b": g3v("cap_a2", "B_ca_out_of_common_level"), "result": "Best"},
        {"label": "Permits (one per parcel per year) instead of units, per one-unit detached home", "adopted": False,
         "a": ebv("numerator_only_permits_per_sf_home", "A_ca_in_common_level"),
         "b": ebv("numerator_only_permits_per_sf_home", "B_ca_out_of_common_level"), "result": "Worse"},
        {"label": "Eligible-property basis without one-unit attached homes", "adopted": False,
         "a": ebv("eligible_permits_no_one_unit_attached", "A_ca_in_common_level"),
         "b": ebv("eligible_permits_no_one_unit_attached", "B_ca_out_of_common_level"), "result": "Worse"},
        {"label": "Eligible-property basis, full (attached homes included)", "adopted": False,
         "a": ebv("eligible_permits", "A_ca_in_common_level"), "b": ebv("eligible_permits", "B_ca_out_of_common_level"),
         "result": "Worse"},
    ]
    win = g3v("cap_a2", "A_ca_in_common_level", "bootstrap_win_share_abc")
    F = model_facts()
    bsens = pd.read_csv(REF / "wi_baseline_sensitivities.csv")
    return {"coverage_rates": cov, "coverage_rights": rights, "classes": classes, "sensitivity_cases": cases,
            "baseline_only": baseline_only, "local_effects": local,
            "sensitivity_groups": {
                "addition": {"title": "Cases that change what the law adds statewide",
                             "intro": "Each changes one part of how the law's effect is estimated from other states."},
                "baseline": {"title": "Cases that change only today's rates (the baseline)",
                             "intro": "Each changes the current-law rate of some places. A higher baseline means a smaller addition by nearly the same amount, so the total with the law moves much less."},
                "local": {"title": "How individual cities' rules are coded: shifts permits between baseline and addition, not the total with the law",
                          "intro": "Being wrong about a city's current ADU rules changes its baseline, not its rate with the law."},
            },
            "robustness": {"rows": robust, "a_win_share": win, "n_states": 7,
                           "units": "root-mean-square log error predicting each of the 7 held-out non-California statewide-law states (lower is better)",
                           "source": "reference/pooled_revision_g3f2.csv, reference/eligible_basis_g3f2.csv"},
            "baseline_sensitivities": [{"label": x.sensitivity, "total": r(x.b5yr_central, 2), "change": r(x.change_vs_main, 2)}
                                       for x in bsens.itertuples()],
            "challenges": [
                {"title": "No Midwest state has data after a statewide law",
                 "text": f"Under current law the model expects Wisconsin to permit {F['base_rate']:.2f} per 1,000 single-family homes per year in 2027–2031 ({F['base']:,.0f} permits ÷ 1,839.569 thousand homes ÷ 5 years); there is no observed statewide ADU series. States with before-and-after data (California, Rhode Island, Washington, Vermont) reached similar first-year levels however low they started, but they are coastal or New England markets. Iowa's first full year (2026) will be the first Midwest test."},
                {"title": "Cities like Madison grew at a little over half the central scenario's rate in their first three years",
                 "text": "Medians of 0.45, 0.54 and 0.60 permits per 1,000 single-family homes per year in 9 Washington and Oregon cities similar to Madison, against the central scenario's statewide " + ", ".join(f"{v:.2f}" for v in F["cen_rate_y"][:3]) + ". Only Madison is put on that path, so Madison's rate with the law sits below its suburbs'. If Wisconsin's other mid-size cities behave like those cities, the central is too high in its first three years; if Madison behaves like the statewide estimate, Madison is too low. This is being reviewed."},
                {"title": "The hold-out test rests on 7 states",
                 "text": f"Keeping California in the eight states' typical level predicts the 7 other states better in {win * 100:.0f}% of resamples of those 7 states, which is within noise. The lower and strong adoption scenarios rest on how 8 states differ, one of them California."},
            ]}


# --------------------------------------------------------------------------------------------
def permits_series(slug: str) -> dict:
    d = PILOTS[slug]
    f = pd.read_csv(ROOT / d["permit_file"])
    col = "category" if "category" in f.columns else "series"
    sel = f[f[col].eq("second_home_sf_lot")].sort_values("year")
    first = int(sel.year.min())
    years = []
    for y in range(2014 if slug != "sun-prairie" else 2016, 2027):
        row = sel[sel.year.eq(y)]
        if len(row) == 0:
            years.append({"year": y, "units": None, "status": "missing", "reason": f"Series starts in {first}"})
        else:
            x = row.iloc[0]
            prov = x.value_status == "provisional"
            n_permits = r(x["count"] if "count" in x.index else x["permits"], 0)
            years.append({"year": y, "units": r(x.units, 0), "permits": n_permits, "status": "provisional" if prov else "observed",
                          "reason": "2026 is a partial, provisional year" if prov else None})
    return {"label": "Second homes permitted on single-family lots (ADUs plus single-family-to-duplex conversions), in units",
            "stage": d["stage"], "source": d["permit_file"], "years": years}


def build_pilots(areas: list) -> list:
    rules = pd.read_csv(REF / "wi_adu_rules.csv", dtype={"jurisdiction_id": str})
    meas = pd.read_csv(REF / "wi_measured_permits_2022_2025.csv", dtype={"GEOID": str})
    rx = pd.read_csv(REF / "wi_rights_exposure.csv", dtype={"jurisdiction_id": str})
    by_id = {a["id"]: a for a in areas}
    conv = pd.read_csv(REF / "pooled_convergence.csv")
    conv_txt = ", ".join(f"{STATE_NAMES[x.state]} {x.pre_rate:.2f} before → {x.year1_rate:.2f} in year 1" for x in conv.itertuples())
    desc = {
        "madison": ("Madison already allows ADUs much like the benchmark law, with a few exceptions (its rules are below). "
                    "In other states, places that already allowed ADUs still saw more permits when a statewide law passed, "
                    "but they gained less than places that had no ADU rules before. So the law is expected to add fewer "
                    "permits per 1,000 single-family homes in Madison than in its neighbours."),
        "pleasant-prairie": ("Pleasant Prairie, a village in Kenosha County, prohibits ADUs today: its own permit records show "
                             "{n} second homes on single-family lots in 2014–2025. The law would allow one ADU on every lot "
                             "with a single-family home, so here it starts from almost nothing."),
        "sun-prairie": ("Madison's neighbour, used as a check from the same housing market. It began allowing ADUs in May "
                        "2026, so even without the law its permits are expected to rise for a few years. Its records are "
                        "applications, not issued permits."),
    }
    mt = madison_texts(params())
    mt["detail"] += (" Why places that already allow ADUs gain less: in the four states with counts before and after their "
                     f"law, the first-year rate after it was about the same however high it was before ({conv_txt}; permits "
                     "per 1,000 single-family homes per year, docs/gate3/POOLED_MODEL.md).")
    P = PROGRAMME
    programme = {
        "title": "Why 2026 is so high so far",
        "text": (f"Of Madison's 42 second homes permitted from 1 January to {MADISON_PROVISIONAL_THROUGH}, {P['units_2026']} come "
                 "from one builder's 2025–26 programme of second homes behind existing houses: two-unit detached ADU "
                 "buildings (\"twin home ADU\", two homes in one building), single detached ADUs, and additions that turn a "
                 f"house into a duplex, all built to repeated plans of about {P['sqft_unit']} sq ft per home. Without the "
                 f"programme, 2026 has {P['units_2026_without']}. These are second homes on single-family lots that Madison's "
                 "October 2025 ordinance allows (up to two ADUs per lot, which may share one detached building). A two-unit "
                 "ADU building goes beyond the benchmark law, which allows one ADU per lot."),
        "detail": (f"Programme in 2026 to date: {P['permits_2026']} permits, {P['units_2026']} homes ({P['two_unit_buildings']} "
                   f"two-unit ADU buildings = {2 * P['two_unit_buildings']} homes, {P['detached']} detached ADUs, "
                   f"{P['conversions']} house-to-duplex additions). Its permits share template specifications: {P['sqft_unit']} "
                   f"sq ft at $80,000–$90,000, or {P['sqft_two_unit']:,} sq ft (3 × {P['sqft_unit']}) at $200,000 for a "
                   f"two-unit building. In 2025 it added {P['units_2025']} of Madison's {P['total_2025']} second homes. "
                   "The model's current-law rate for Madison uses the complete years 2022–2025 only; 2026 and the "
                   "programme enter as sensitivity cases (docs/gate2/MADISON_PERMITS.md, section 5b)."),
    }
    out = []
    for slug, d in PILOTS.items():
        a = by_id[d["area_ids"][0]]
        jr = rules[rules.jurisdiction_id.eq(d["jurisdiction_id"])]
        rl = [{"provision": x.provision, "value": s(x.value), "from": s(x.effective_from), "to": s(x.effective_to),
               "source_url": s(x.source_url), "section": s(x.source_section), "retrieved": s(x.retrieved),
               "verification": x.verification, "current": pd.isna(x.effective_to)} for x in jr.itertuples()]
        m = meas[meas.GEOID.eq(d["jurisdiction_id"])]
        mrow = None
        if len(m):
            x = m.iloc[0]
            mrow = {"window": "2022–2025", "permits": r(x.permits, 0), "homes": int(x.homes),
                    "thousand_home_years": r(x.thousand_home_years, 3), "rate": r(x.rate_per_1000_homes_yr, 4),
                    "lo": r(x.rate_poisson95_lo, 4), "hi": r(x.rate_poisson95_hi, 4), "stage": x.stage,
                    "used_by_model": a["x_status"] == "observed" and "2022" in a["x_basis"]}
        if a["x_status"] == "observed" and "2014" in a["x_basis"]:
            # the model's window for this place is 2014-2025: show that window, not the recent one
            yrs = [y for y in permits_series(slug)["years"] if 2014 <= y["year"] <= 2025 and y["status"] == "observed"]
            n_units = sum(y["units"] for y in yrs)
            thy = a["homes"] * len(yrs) / 1000
            mrow = {"window": "2014–2025", "permits": n_units, "homes": a["homes"], "thousand_home_years": r(thy, 3),
                    "rate": r(n_units / thy, 4), "lo": None, "hi": None, "stage": d["stage"], "used_by_model": True}
        ex = rx[rx.jurisdiction_id.eq(d["jurisdiction_id"]) & rx.scenario_id.eq("adu_full")]
        out.append({"slug": slug, "area_id": a["id"], "name": a["name"], "county": a["county"], "role": d["role"],
                    "description": desc[slug].format(n=int(sum(y["units"] or 0 for y in permits_series(slug)["years"] if y["status"] == "observed"))), "homes": a["homes"], "x_rate": a["x_rate"], "x_low": a["x_low"],
                    "x_high": a["x_high"], "x_status": a["x_status"], "x_basis": a["x_basis"],
                    "current_class": a["current_class"],
                    "reform_class": s(ex.reform_class.iloc[0]) if len(ex) else None,
                    "rights_added_text": s(ex.rights_added_text.iloc[0]) if len(ex) else None,
                    "base": a["base"], "base_low_5yr": a["base_low_5yr"], "base_high_5yr": a["base_high_5yr"],
                    "add": a["add"], "y_rate_y5": a["y_rate_y5"],
                    "basis_text": a["basis_text"], "note": a.get("note"),
                    "like": {k: mt[k] for k in ("title", "text", "detail")} if slug == "madison" else None,
                    "programme": programme if slug == "madison" else None,
                    "provisional_through": MADISON_PROVISIONAL_THROUGH if slug == "madison" else None,
                    # docs/gate2/MADISON_PERMITS.md: 29 of the 42 provisional 2026 units are one templated builder programme
                    "provisional_detail": (f"{PROGRAMME['units_2026']} of them from one builder's programme" if slug == "madison" else None),
                    "permits": permits_series(slug), "measured": mrow, "rules": rl})
    return out


# --------------------------------------------------------------------------------------------
def build_evidence(p: dict) -> dict:
    lv = stage2_levels()
    F = model_facts()
    states = [{"state": STATE_NAMES[k], "level": v} for k, v in sorted(lv.items(), key=lambda kv: -kv[1])]
    annual = pd.read_csv(REF / "statewide_states_annual.csv")
    pts = pd.read_csv(REF / "pooled_adoption_points.csv")
    k1 = pts[pts.k.eq(1)].set_index("series")["year"]
    lines = []
    for series, g in annual[annual.series.isin(k1.index)].groupby("series"):
        k = g.year - k1[series] + 1
        g = g.assign(k=k)[(k >= -5) & (k <= 5)].sort_values("k")
        lines.append({"name": SERIES_NAMES.get(series, series), "kind": "state",
                      "points": [{"k": int(a), "rate": r(b, 3)} for a, b in zip(g.k, g.per_1000_homes)]})
    curve = pd.read_csv(REF / "statewide_adoption_curve.csv").dropna(subset=["ca_rate_k_from_2017_law"])
    lines.append({"name": "California (2017 law)", "kind": "california",
                  "points": [{"k": int(a), "rate": r(b, 3)} for a, b in zip(curve.k, curve.ca_rate_k_from_2017_law)]})
    obs = pts.groupby("k")["rate"].agg(n="count", median="median").reset_index()
    lines.append({"name": "Median across states (California not included)", "kind": "median",
                  "points": [{"k": int(a), "rate": r(b, 3), "n": int(n)} for a, b, n in zip(obs.k, obs["median"], obs.n)]})
    by_year = pd.read_csv(REF / "adu_model_statewide_by_year.csv")
    for path in PATHS:
        q = by_year[by_year.path.eq(path)].sort_values("year")
        lab = "Wisconsin, " + LABELS["scenario_chart"].format(name=SCEN_NAME[path].lower())
        lines.append({"name": lab, "kind": f"wi_{path}",
                      "points": [{"k": int(y), "rate": r((b + a) / WI_HOMES * 1000, 3)}
                                 for y, b, a in zip(q.year, q.baseline_units, q.additional_units)]})
    wi_now = by_year[by_year.path.eq("central")].baseline_units.iloc[0] / WI_HOMES * 1000
    lines.append({"name": "Wisconsin under current law (model baseline for 2027)", "kind": "wi_today",
                  "points": [{"k": k, "rate": r(wi_now, 3)} for k in range(-5, 1)]})

    cities = pd.read_csv(REF / "madison_like_annual.csv")
    cities = cities[cities.state.isin(["WA", "OR", "RI"]) & cities.year_since_law.between(-5, 5)]
    clines = []
    for (stt, city), g in cities.groupby(["state", "city"]):
        g = g.sort_values("year_since_law")
        clines.append({"name": f"{city}, {stt}", "kind": "city",
                       "points": [{"k": int(a), "rate": r(b, 3)} for a, b in zip(g.year_since_law, g.rate_per_1000)]})
    med = pd.read_csv(REF / "madison_like_median_path.csv")
    med = med[med.group.eq("WA+OR Madison-like (main)")].sort_values("year_since_law")
    clines.append({"name": "Median of cities like Madison in Washington and Oregon", "kind": "median",
                   "points": [{"k": int(a), "rate": r(b, 3), "n": int(n)} for a, b, n in zip(med.year_since_law, med.median_rate, med.n_cities)]})
    mad = pd.read_csv(REF / "madison_adu_permits_by_year.csv")
    mad = mad[mad.category.eq("second_home_sf_lot") & mad.year.between(2021, 2025)]
    clines.append({"name": "Madison, observed 2021–2025 (plotted as if a law took effect in 2027)", "kind": "wi_today",
                   "points": [{"k": int(y - 2026), "rate": r(u / 53292 * 1000, 3)} for y, u in zip(mad.year, mad.units)]})
    ap = p["area_paths"]["madison_like_path"]["rates"]
    clines.append({"name": "Madison's adopted path (all three scenarios)", "kind": "wi_central",
                   "points": [{"k": i + 1, "rate": v} for i, v in enumerate(ap)]})

    E = "evidence"
    A = "assumption"
    cards = [
        {"kind": E, "title": "What statewide ADU laws did elsewhere", "type": "transferred", "status": "calculated",
         "text": "Eight states with statewide ADU laws were measured. At a typical place with the law in force 4 or more years, their levels range from Rhode Island to California (permits per 1,000 single-family homes per year). The central scenario sits near the typical state; the lower and upper scenarios are the 10th and 90th percentiles of this spread.",
         "table": states, "table_units": "permits per 1,000 single-family homes per year, typical place, law in force 4+ years",
         "links": [doc("docs/gate3/POOLED_REVISION.md", "Pooled model revision"), doc("docs/gate3/STATEWIDE_STATES.md", "Statewide-law states"),
                   doc("reference/pooled_revision_stage2_levels.csv", "State levels (CSV)")]},
        {"kind": E, "title": "California's counts, corrected for multifamily lots", "type": "transferred", "status": "calculated",
         "text": "California 2023–2025: 87,303 ADU units reported, 81,368 after the cap of 2 ADUs per parcel and the multifamily-lot rule. California is used for the shape of the response and stays in the common level because it predicts the other states better; Wisconsin's numbers are never a ratio of California's.",
         "links": [doc("docs/gate3/MULTIFAMILY_LOT_ADUS.md", "Multifamily-lot ADUs"), doc("docs/gate3/CA_STUDY_RESULTS.md", "California study")]},
        {"kind": E, "title": "Cities like Madison after a statewide law", "type": "descriptive", "status": "observed",
         "text": "Nine Washington and Oregon cities similar to Madison in size and home values ran at 0.45, 0.54 and 0.60 permits per 1,000 single-family homes per year in years 1–3 after their statewide law, a little over half the central scenario's statewide rate (" + ", ".join(f"{v:.2f}" for v in F["cen_rate_y"][:3]) + "). Madison alone follows this observed path in every scenario; every other place follows the statewide estimate. This choice is being reviewed.",
         "links": [doc("docs/gate3/MADISON_LIKE_CITIES.md", "Cities like Madison")]},
        {"kind": E, "title": "Wisconsin today: measured permits", "type": "descriptive", "status": "observed",
         "text": "Observed: Madison issued 40 second-home permits on single-family lots in 2022–2025 (0.19 per 1,000 single-family homes per year). Calculated, not observed: under current law the model expects " + f"{F['base_rate']:.2f}" + " per 1,000 per year statewide in 2027–2031; there is no statewide ADU series. Most places have no record-level permit data, so their rates come from their rules group.",
         "links": [doc("docs/gate3/WI_BASELINE.md", "Wisconsin baseline"), doc("reference/wi_measured_permits_2022_2025.csv", "Measured permits (CSV)")]},
        {"kind": E, "title": "Local ADU rules coded so far", "type": "descriptive", "status": "observed",
         "text": "The largest jurisdictions' ADU rules were coded from their ordinances, with section and retrieval date for each provision. Every other place is treated as restricted.",
         "links": [doc("reference/wi_adu_rules.csv", "Coded rules (CSV)"), doc("docs/gate3/WI_RULES_VS_ACTIVITY.md", "Rules versus activity"),
                   doc("docs/gate3/WI_UNZONED_TOWNS.md", "Unzoned towns")]},
        {"kind": A, "title": "Places with uncoded rules behave like restricted places", "type": "judgment", "status": "assumed",
         "text": "1,882 of 1,925 areas (69% of single-family homes) have no coded rules. They get the restricted-group rate. If they behaved like prohibited places instead, the baseline would be " + f"{F['uncoded_base']:,.0f} permits over 2027–2031 instead of {F['base']:,.0f}." + "",
         "challenge": "Is a rural town under county zoning really like a city with restricted ADU rules?",
         "links": [doc("docs/ASSUMPTIONS_AND_QUESTIONS.md", "AQ-023 and AQ-027"), doc("docs/gate3/WI_BASELINE.md", "Wisconsin baseline")]},
        {"kind": A, "title": "Wisconsin will respond like the statewide-law states", "type": "transferred", "status": "assumed",
         "text": "No Midwest state has post-law data yet. The model assumes Wisconsin's places respond like comparable places in the eight states, after adjusting for home value, income and size within each state.",
         "challenge": "Iowa's first full year (2026) will be the first Midwest test.",
         "links": [doc("docs/gate3/README.md", "Gate 3 packet")]},
        {"kind": A, "title": "The law takes effect on 1 January 2027 and ramps up", "type": "judgment", "status": "assumed",
         "text": "Stylized start date. In years 1–3 the addition reaches " + ", ".join(f"{v:.2f}" for v in F["ramp"][:3]) + f" of its year-4 size (central). Without the ramp, the central would be {F['no_ramp']:,.0f} permits instead of {F['cen']:,.0f}.",
         "challenge": "A real bill would have its own effective date and local compliance deadline.",
         "links": [doc("docs/gate3/POOLED_REVISION.md", "Pooled model revision")]},
        {"kind": A, "title": "With the law, every place reaches at least a minimum rate set from Madison", "type": "judgment", "status": "assumed",
         "text": "With the law, every area's rate is at least 0.2345 permits per 1,000 single-family homes per year: Madison's 2022–2025 rate (40 permits ÷ 213.168 thousand home-years = 0.1876) divided by 0.8.",
         "links": [doc("docs/gate3/POOLED_REVISION.md", "Pooled model revision")]},
        {"kind": A, "title": "ADUs built with a new house on a vacant lot do not count", "type": "descriptive", "status": "calculated",
         "text": "In 17 cities split by demolition records, vacant-lot new-house ADUs were a median 4.9% of ADUs, so every non-California series is multiplied by 0.951.",
         "links": [doc("docs/gate3/MADISON_LIKE_CITIES.md", "Cities like Madison (vacant-lot share)")]},
        {"kind": A, "title": "Rural home values include acreage", "type": "judgment", "status": "assumed",
         "text": f"Rural areas get {F['rural']:,.0f} of the {F['cen']:,.0f} central permits ({F['rural'] / F['cen'] * 100:.0f}%) with {F['rural_homes']:,} of the 1,839,569 single-family homes ({F['rural_homes'] / WI_HOMES * 100:.0f}%), partly because rural median home values include land. Holding rural places and small communities at the minimum rate set from Madison (0.2345) gives {F['rural_floor']:,.0f}.",
         "challenge": "Septic limits and lower demand could make rural uptake lower than this.",
         "links": [doc("docs/gate3/README.md", "Gate 3 packet")]},
    ]
    return {"cards": cards, "spaghetti_states": {"lines": lines, "units": "ADU permits per 1,000 single-family homes per year",
                                                 "x_label": "Years before (0 and below) and after (1 and above) the statewide law; Wisconsin's year 1 is 2027",
                                                 "png": doc("docs/gate3/adoption_spaghetti_states.png", "Gate 3 chart (PNG)")},
            "spaghetti_cities": {"lines": clines, "units": "ADU permits per 1,000 single-family homes per year",
                                 "x_label": "Years before (0 and below) and after (1 and above) the statewide law; Madison's year 1 is 2027",
                                 "png": doc("docs/gate3/adoption_spaghetti_cities.png", "Gate 3 chart (PNG)")},
            "docs": [doc("docs/gate3/README.md", "Gate 3 packet (adopted model)"), doc("docs/MODEL_AND_ASSUMPTIONS.md", "Model and assumptions"),
                     doc("docs/DATA_PROVENANCE.md", "Data provenance"), doc("docs/ASSUMPTIONS_AND_QUESTIONS.md", "Assumptions log"),
                     doc("docs/gate4/README.md", "Gate 4 packet")]}


# --------------------------------------------------------------------------------------------
def build_geo(out: Path, munis: list, county_names: dict | None = None) -> dict:
    """Map drawing from the Census cartographic boundary files (shoreline-clipped), so lakes are not coloured.

    The areas themselves (ids, homes, results) come from the TIGER/Line foundation; the cartographic file only supplies
    the outline drawn on screen. Water-only areas ("County subdivisions not defined") are not in it and are not drawn.
    """
    import geopandas as gpd
    sizes = {}
    raw = ROOT / "data/raw/census_cb_2024"
    known = {a["id"] for a in munis}
    water = {a["id"] for a in munis if a.get("water")}
    for name, f, tol, prefix in (("counties", "cb_2024_us_county_500k.zip", 600, ""),
                                 ("munis", "cb_2024_55_cousub_500k.zip", 120, "muni:")):
        g = gpd.read_file(raw / f)
        g = g[g.STATEFP.eq("55")].copy()
        g["area_id"] = prefix + g.GEOID
        if name == "munis":
            missing = known - set(g.area_id) - water
            assert not missing, f"areas with homes missing from the cartographic file: {sorted(missing)[:5]}"
            g = g[g.area_id.isin(known)]
        g = g[["area_id", "geometry"]].to_crs(3071)
        if name == "counties" and county_names:
            # label anchors: one point inside each county (text labels only, never a marker), for the optional
            # "County names" layer; further label sets (e.g. transit stations) can be added the same way
            pts = g.assign(geometry=g.geometry.representative_point()).to_crs(4326)
            labels = {"type": "FeatureCollection", "features": [
                {"type": "Feature", "properties": {"id": a, "name": county_names[a].removesuffix(" County"), "kind": "county"},
                 "geometry": {"type": "Point", "coordinates": [round(pt.x, 4), round(pt.y, 4)]}}
                for a, pt in sorted(zip(pts.area_id, pts.geometry))]}
            (out / "geo_labels.json").write_text(json.dumps(labels, separators=(",", ":")))
            sizes["labels"] = len(labels["features"])
        g["geometry"] = g.geometry.simplify(tol, preserve_topology=True)
        g = g.to_crs(4326)
        g["geometry"] = g.geometry.set_precision(1e-4)
        g = g[~g.geometry.is_empty]
        fc = json.loads(g.to_json(drop_id=True))
        fc.pop("bbox", None)
        for feat in fc["features"]:
            feat["properties"] = {"id": feat["properties"]["area_id"]}
            feat.pop("bbox", None)
        path = out / f"geo_{name}.json"
        path.write_text(json.dumps(fc, separators=(",", ":")))
        sizes[name] = len(fc["features"])
    return sizes


def validate(state: dict, counties: list, munis: list, unc: dict, unk: dict | None = None, dist: dict | None = None) -> dict:
    """Reconciliation and ordering checks recorded in the manifest; raise on failure."""
    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})

    for sc in state["scenarios"]:
        k = sc["id"]
        mun = sum(sum(a["add"][k]) for a in munis)
        cty = sum(sum(c["add"][k]) for c in counties)
        check(f"municipalities sum to state ({k})", abs(mun - sc["additional_total"]) < 0.5,
              f"{mun:.2f} vs {sc['additional_total']:.2f} additional permits 2027-2031")
        check(f"counties sum to state ({k})", abs(cty - sc["additional_total"]) < 0.5,
              f"{cty:.2f} vs {sc['additional_total']:.2f} additional permits 2027-2031")
    b = sum(sum(a["base"]) for a in munis)
    check("baseline municipalities sum to state", abs(b - state["baseline"]["total"]) < 0.5,
          f"{b:.2f} vs {state['baseline']['total']:.2f} permits 2027-2031")
    ref = pd.read_csv(REF / "adu_model_by_county.csv", dtype={"parent_county_id": str}).set_index(["parent_county_id", "path"])
    worst = max(abs(sum(c["add"][k]) - ref.loc[(c["id"], k), "additional_units"]) for c in counties for k in PATHS)
    worstb = max(abs(sum(c["base"]) - ref.loc[(c["id"], "central"), "baseline_units"]) for c in counties)
    check("counties equal reference/adu_model_by_county.csv", worst < 0.005 and worstb < 0.005,
          f"largest difference {max(worst, worstb):.4f} permits")
    flips = [c["name"] for c in counties for k in PATHS
             if round(sum(c["add"][k])) != round(ref.loc[(c["id"], k), "additional_units"])
             or round(sum(c["base"])) != round(ref.loc[(c["id"], k), "baseline_units"])]
    check("county whole-permit figures equal the reference CSV after rounding", not flips, f"{len(flips)} differences")
    bad = [a["id"] for a in munis for i in range(5)
           if not (a["add"]["lower"][i] <= a["add"]["central"][i] + 1e-6 <= a["add"]["upper"][i] + 2e-6)]
    check("lower <= central <= upper in every area and year", not bad, f"{len(bad)} violations")
    homes = sum(a["homes"] for a in munis)
    check("single-family homes sum to the state", homes == WI_HOMES, f"{homes:,} vs {WI_HOMES:,}")
    if unk is not None:
        # unknown-rules variants: adopted = the adopted run; each variant's areas and counties sum to its statewide row
        ad = next(v for v in unk["variants"] if v["adopted"])
        gap = max([abs(ad["additional_total"][k] - sc["additional_total"]) for sc in state["scenarios"] for k in [sc["id"]]]
                  + [abs(ad["baseline_total"] - state["baseline"]["total"])])
        check("unknown rules: adopted variant equals the adopted run", gap < 0.01, f"largest difference {gap:.4f} permits")
        worst = 0.0
        for v in unk["variants"]:
            if v["adopted"]:
                continue
            ov = unk["areas"][v["id"]]
            for k in PATHS:
                for i in range(5):
                    tot = sum((ov[a["id"]]["add"][k] if a["id"] in ov else a["add"][k])[i] for a in munis)
                    worst = max(worst, abs(tot - v["additional_by_year"][k][i]))
            for i in range(5):
                tot = sum((ov[a["id"]]["base"] if a["id"] in ov else a["base"])[i] for a in munis)
                worst = max(worst, abs(tot - v["baseline_by_year"][i]))
            cv = unk["counties"][v["id"]]
            ref = pd.read_csv(REF / "adu_model_unknown_rules_by_county.csv", dtype={"parent_county_id": str})
            ref = ref[ref.unknown_treatment.eq(v["id"])].set_index(["parent_county_id", "path"])
            for c in counties:
                cc = cv.get(c["id"], c)
                for k in PATHS:
                    worst = max(worst, abs(sum(cc["add"][k]) - ref.loc[(c["id"], k), "additional_units"]))
                worst = max(worst, abs(sum(cc["base"]) - ref.loc[(c["id"], "central"), "baseline_units"]))
        check("unknown rules: each variant's areas and counties reconcile to its statewide and county rows", worst < 0.01,
              f"largest gap {worst:.4f} permits (every path and year)")
    if dist is not None:
        worst = 0.0
        for level, L in dist["levels"].items():
            for k in PATHS:
                sc = next(x for x in state["scenarios"] if x["id"] == k)
                for i in range(5):
                    tot = sum(d["add"][k][i] for d in L["rows"]) + L["unallocated"]["add"][k][i]
                    worst = max(worst, abs(tot - sc["additional_by_year"][i]))
            for i in range(5):
                tot = sum(d["base"][i] for d in L["rows"]) + L["unallocated"]["base"][i]
                worst = max(worst, abs(tot - state["baseline"]["by_year"][i]))
        check("Assembly and Senate districts plus the unallocated row reconcile to the state", worst < 0.01,
              f"largest gap {worst:.4f} permits (every path and year); unallocated rows kept")
        asm = {int(d["district"]): d for d in dist["levels"]["assembly"]["rows"]}
        nest = 0.0
        for sd in dist["levels"]["senate"]["rows"]:
            for k in PATHS:
                nest = max(nest, abs(sum(sum(asm[a]["add"][k]) for a in sd["assembly"]) - sum(sd["add"][k])))
        check("each Senate district equals the sum of its three Assembly districts", nest < 0.01 and
              all(len(sd["assembly"]) == 3 for sd in dist["levels"]["senate"]["rows"]), f"largest gap {nest:.4f} permits")
    failed = [c for c in checks if not c["passed"]]
    if failed:
        raise SystemExit(f"bundle validation failed: {failed}")
    return {"passed": len(checks), "failed": 0, "checks": checks}


def main():
    hashes, run_id = load_inputs()
    p = params()
    out = OUT_ROOT / run_id
    if OUT_ROOT.exists():
        for old in OUT_ROOT.iterdir():   # keep only the current run
            if old.is_dir() and old.name != run_id:
                shutil.rmtree(old)
    out.mkdir(parents=True, exist_ok=True)

    state = build_state(p)
    counties, munis, n = build_areas(p)
    unc = build_uncertainty(munis)
    pilots = build_pilots(munis)
    ev = build_evidence(p)
    geo_n = build_geo(out, munis, {c["id"]: c["name"] for c in counties})
    unk = build_unknown_rules(munis, counties)
    dist = build_districts(out)
    unc["trace"] = build_trace()
    val = validate(state, counties, munis, unc, unk, dist)
    geo_n.update(dist.pop("sizes"))
    rules = pd.read_csv(REF / "wi_adu_rules.csv")

    manifest = {
        "schema_version": 1, "run_id": run_id, "scenario_id": p["scenario_id"], "model_status": p["status"],
        "title": "Wisconsin ADU law: statewide estimates",
        "outcome": {
            "short": "Second-home permits at issuance on lots that already have a single-family home. Not completed homes. Results are for areas, never individual lots.",
            "long": "The outcome is permits for a second home on a lot that already has a single-family home: accessory dwelling units (ADUs) plus single-family-to-duplex conversions (AQ-032), counted when the permit is issued. They are not completed homes and not net new housing. Every result is for an area (the state, a county, or a city, village or town); the tool never predicts which lot will build.",
            "rate_units": "permits per 1,000 single-family homes per year",
            "count_units": "permits over 2027–2031",
        },
        "dates": {"last_observed_year": 2025, "bridge_year": 2026, "forecast_years": YEARS,
                  "effective": "Stylized: the statewide law takes effect on 1 January 2027 (forecast year 1)"},
        "vintages": [
            {"what": "Single-family (one-unit detached) homes, housing mix, occupancy", "vintage": "ACS 2020–2024 5-year (B25024, B25002): five-year averages, not a 2024 count"},
            {"what": "Housing units by year", "vintage": "Census Population Estimates, Vintage 2025 (1 July 2020–2025; no published margin of error)"},
            {"what": "Homes permitted by year", "vintage": "Census Building Permits Survey, annual 2015–2025 (final)"},
            {"what": "Areas", "vintage": "Census TIGER/Line 2024 (counties, county subdivisions)"},
            {"what": "Map outlines", "vintage": "Census cartographic boundary files 2024, 1:500,000, shoreline-clipped (water areas not drawn)"},
            {"what": "Legislative districts", "vintage": "Wisconsin State Assembly and Senate districts, 2024 plan (2023 Wisconsin Act 94), LTSB; homes split with 2020 census blocks"},
            {"what": "Local ADU rules", "vintage": f"Ordinances retrieved {rules.retrieved.min()} to {rules.retrieved.max()}"},
            {"what": "Town zoning status", "vintage": "Wisconsin DOA land-regulation inventory, 2025-01-30"},
            {"what": "Wisconsin permit records", "vintage": "Madison and Pleasant Prairie issued permits, Sun Prairie applications, through 2025 (2026 provisional)"},
            {"what": "Comparison states and cities", "vintage": "State and city permit series through 2025 (see Gate 3 packet)"},
        ],
        "terms": {
            "scenarios": "Lower, central and Strong adoption: how Wisconsin could respond, based on how much the statewide-law states differ from one another. Not statistical confidence intervals.",
            "sensitivity_case": "Changes one assumption and reruns the model. Together the cases are the sensitivity analysis.",
            "robustness_check": "Tests a methodological alternative by predicting held-out states.",
            "baseline": "What the model expects under current law, with no statewide ADU law.",
            "additional": "Permits the statewide law adds on top of the baseline.",
            "never_subtracts": ("A statewide law never subtracts permits. Where a place already permits more than the law's "
                                "expected rate for it, for example because its own rules go further than the benchmark "
                                "(Madison's two-unit ADU buildings, or San Diego's bonus ADU programme in California), the law "
                                "adds nothing there and the place keeps its current-law permits: each place's addition is "
                                "floored at zero, never negative."),
        },
        "pilot_intro": {
            "title": "What is a pilot page?",
            "text": ("This pilot page allows you to see a few of the steps we took on the way to building the statewide "
                     "model. The work started here: real permit records from Wisconsin places, above all these three "
                     "(Madison, Pleasant Prairie and Sun Prairie), measure how many second homes places permit today under their current "
                     "rules, and Madison's level sets the minimum rate every Wisconsin place reaches with the law."),
            "how": ("The statewide estimate itself is built top-down, from how eight other states responded to their "
                    "statewide ADU laws. Each pilot page then shows how that statewide result is shared out to one real "
                    "place, and acts as a spot check on it. The pilots are not a separate, bottom-up model: their figures "
                    "are already inside the Wisconsin total and are never added to it."),
        },
        "status_pills": {
            "observed": "Observed: counted in a published source or permit record.",
            "calculated": "Calculated: computed by the model from observed inputs and stated rules.",
            "assumed": "Assumed: a judgment or default where no local data exist.",
        },
        "limitations": [
            "Permits, not completed homes; some permitted ADUs are never built.",
            "No Midwest state has data after a statewide law; Wisconsin's response is transferred from eight other states.",
            "69% of single-family homes are in places whose ADU rules are not coded; they are treated as restricted.",
            "Town and village figures are rough shares of the statewide result, not local forecasts.",
            "Results are associations observed after other states' laws, not proven causal effects.",
            "Pilot pages are examples; they are never added up into a Wisconsin total.",
        ],
        "inputs": hashes, "validation": val, "counts": {**n, **{f"geo_{k}": v for k, v in geo_n.items()}},
        "repo_url": REPO_URL,
        "files": ["manifest.json", "state.json", "areas.json", "uncertainty.json", "pilots.json", "evidence.json",
                  "geo_counties.json", "geo_munis.json", "geo_labels.json", "unknown_rules.json", "districts.json",
                  "geo_assembly.json", "geo_senate.json", "geo_district_labels.json"],
    }

    def dump(name, obj):
        (out / name).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False))

    dump("manifest.json", manifest)
    dump("state.json", state)
    dump("areas.json", {"counties": counties, "munis": munis, "class_short": CLASS_SHORT, "class_text": CLASS_TEXT,
                        "x_status_text": X_STATUS_TEXT})
    dump("uncertainty.json", unc)
    dump("pilots.json", pilots)
    dump("evidence.json", ev)
    dump("unknown_rules.json", unk)
    dump("districts.json", dist)
    (OUT_ROOT / "latest.json").write_text(json.dumps({"run_id": run_id}) + "\n")
    total = sum(f.stat().st_size for f in out.iterdir())
    print(f"bundle {run_id}: {len(list(out.iterdir()))} files, {total / 1e6:.2f} MB -> {out.relative_to(ROOT)}")
    for c in val["checks"]:
        print(f"  ok  {c['check']}: {c['detail']}")


if __name__ == "__main__":
    sys.exit(main())
