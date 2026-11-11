"""Export the transit-oriented density (TOD) scenario as a static JSON bundle for the tool (Gate 4).

The browser runs no model: every number it shows comes from this bundle, which is built only from
committed files:

- reference/tod_model_statewide.csv, _by_area.csv, _by_county.csv, _by_assembly_district.csv,
  _by_senate_district.csv, _sensitivities.csv, _checks.csv, _params.csv (the Gate 3 model, AQ-050, AQ-051)
- reference/tod_definition_summary.csv, tod_stops.csv, tod_station_areas.csv, tod_near_stop_homes_by_muni.csv
- reference/tod_case_estimates.csv, tod_cases.csv, tod_madison_test_results.csv, tod_madison_test_rates_by_year.csv,
  tod_madison_test_predictions.csv, tod_scale_check.csv, tod_scale_check_metro_years.csv
- reference/housing_baseline_statewide_by_year.csv, housing_baseline_by_area.csv (the shared all-housing baseline)
- reference/tod_today_density.csv (the "today" snapshot: existing homes per acre of land within 1/4 and 1/2 mile of
  rail and rapid stops and in the 1/2-1 mile ring around them, 2020 census blocks; scripts/build_tod_today_density.py).
  The near-stops-vs-rest-of-city ratio (reference/tod_today_ratio.csv) is no longer on the screen (owner 2026-11-02).
- the municipality outlines already published in the ADU bundle (ui/public/runs/<run>/geo_munis.json), cut to the
  map views and rounded to about 100 m

Output: ui/public/scenarios/tod/runs/<run_id>/*.json and latest.json. The run id hashes the input files, so the
same inputs give the same bundle byte for byte. No parcel id, permit number or address is written: stops are
public transit data; station-area numbers are by municipality or by band of a municipality.

Run: uv run python scripts/build_tod_bundle.py
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
OUT_ROOT = ROOT / "ui" / "public" / "scenarios" / "tod" / "runs"
REPO_URL = "https://github.com/mroconnell/housing-challenge-starter-missingmiddleware"
DOC = REPO_URL + "/blob/main/"
YEARS = [2027, 2028, 2029, 2030, 2031]
SCEN = ["little", "typical", "strong"]
# Combined views (docs/shared/SCENARIO_CONTRACT.md section 9): the shared baseline this bundle is built on, and
# how its paths map to the roles that are paired with other reforms' paths.
BASELINE_VERSION = "all-housing baseline v4"
ROLES = {"lower": "little", "central": "typical", "upper": "strong"}
ADU_RUN = json.loads((ROOT / "ui" / "public" / "runs" / "latest.json").read_text())["run_id"]
GEO_MUNIS = f"ui/public/runs/{ADU_RUN}/geo_munis.json"
# The manifest names the ADU outline file through ADU's latest pointer, not its run id, so an ADU rebuild that leaves
# the outlines unchanged does not make this bundle stale (CI, 2026-11-06). The hash is still of the real file.
GEO_MUNIS_LISTED = "ui/public/runs/<latest>/geo_munis.json"


def resolve_input(path: str) -> Path:
    """An input path as listed in the manifest, on disk (<latest> = ADU's ui/public/runs/latest.json run id)."""
    return ROOT / path.replace("<latest>", ADU_RUN)

INPUTS = [
    "scripts/build_tod_bundle.py",
    "reference/tod_model_statewide.csv", "reference/tod_model_by_area.csv", "reference/tod_model_by_county.csv",
    "reference/tod_model_by_assembly_district.csv", "reference/tod_model_by_senate_district.csv",
    "reference/tod_model_sensitivities.csv", "reference/tod_model_checks.csv", "reference/tod_model_params.csv",
    "reference/tod_definition_summary.csv", "reference/tod_stops.csv", "reference/tod_station_areas.csv",
    "reference/tod_near_stop_homes_by_muni.csv", "reference/tod_optiond_line.csv", "reference/tod_causal_lines.csv",
    "reference/tod_case_estimates.csv", "reference/tod_cases.csv", "reference/tod_trait_pairs.csv", "reference/tod_trait_tools.csv",
    "reference/tod_allvars_models.csv", "reference/tod_allvars_variable_map.csv", "reference/tod_net_effect_by_case.csv",
    "reference/tod_control_cities_results.csv", "reference/tod_control_cities_pooled.csv",
    "reference/tod_madison_test_results.csv", "reference/tod_madison_test_rates_by_year.csv",
    "reference/tod_madison_test_predictions.csv",
    "reference/tod_scale_check.csv", "reference/tod_scale_check_metro_years.csv",
    "reference/housing_baseline_statewide_by_year.csv", "reference/housing_baseline_by_area.csv",
    "reference/housing_baseline_history.csv",
    "reference/gate5_housing_health.csv", "reference/adu_model_district_crosswalk.csv",
    "reference/tod_today_density.csv",
    "reference/tod_line_draws.csv", "reference/tod_coverage_test.csv",
    GEO_MUNIS,
]

# Metro areas as the scale check defines them (MODEL.md section 10; 2023 federal definitions).
METROS = {
    "milwaukee": ("Milwaukee metro", ["Milwaukee County", "Waukesha County", "Ozaukee County", "Washington County"]),
    "madison": ("Madison metro", ["Dane County", "Columbia County", "Green County", "Iowa County"]),
}
REST = ("rest", "Rest of Wisconsin")
SCALE_METRO = {"Milwaukee-Waukesha, WI": "milwaukee", "Madison, WI": "madison"}

SCEN_TEXT = {
    # Option D, the transit district mandate (owner 2026-11-02; AQ-071): every Wisconsin city with qualifying rail or
    # rapid stops zones a by-right multifamily district on 15% of the lot acres within 1/4 mile of them.
    "little": {
        "label": "Lower: the rezoned parcels' own gain only", "evidence": "edge test at district boundaries, 5 places",
        "info": "Just inside a district's boundary versus just outside it, before and after the rezoning, in the 5 places whose two sides were alike beforehand: about 88 extra new homes per 100 acres of district lots a year. Applied to a district of 15% of Wisconsin's land within ¼ mile of rail and rapid stops, for five years: about 3,960 extra homes over 2027–2031 (90% range about 2,280 to 5,790). It counts only the rezoned lots' own gain, not any lift to nearby lots, so it is a floor. Fake boundaries drawn where nothing changed show about zero. The former lower line (the best lot model, 824) is on How sure.",
    },
    "typical": {
        "label": "Central: the average district place, across about 12% of lots within ¼ mile of transit", "evidence": "measured near 11 US places' stops",
        "info": "The 11 places' districts covered on average about 12% of the land within ¼ mile (from 2% to 26%), a little less than the law's 15%; this line keeps their effect as measured, without scaling it to 15%. Their average measured effect within ¼ mile of their reform stops, compared with similar stops without reform, before and after: about 34 extra new homes per 100 acres of lots a year. Applied to Wisconsin's lots within ¼ mile of rail and rapid stops (about 4,870 acres in Milwaukee and Madison, scaled to the state by its share of that land, ×1.227) for five years: about 10,030 extra homes over 2027–2031 (range about 7,580 to 12,010, leaving out one place at a time). No model we tried beat this average on places it had not seen, so by the rule set before the results it is the central line. Caution: those cities chose their district land themselves, often land builders already wanted; a state mandate may do less. Land beyond ¼ mile counts zero. The earlier central line for the broader law (the average reform city at 71% coverage) is shown on How sure as a comparison.",
    },
    "strong": {
        "label": "Upper: the average district place, scaled up to 15% of lots within ¼ mile of transit", "evidence": "measured near 11 US places' stops, scaled to the law's 15%",
        "info": "",  # filled by upper_info() from reference/tod_causal_lines.csv (AQ-075)
    },
}


def upper_info() -> str:
    """The upper card's text (AQ-075, owner 2026-11-03 11:52), numbers read from reference/tod_causal_lines.csv."""
    cl = pd.read_csv(REF / "tod_causal_lines.csv").set_index("line")
    up, x2, ta = cl.loc["upper_average_scaled_15"], cl.loc["causal_upper_2x2"], cl.loc["whatif_2x2_trend_adjusted"]
    k = lambda v: f"{whole(round(v, -1)):,}"  # noqa: E731
    return ("Same 11 places as the central line. Their districts covered about 12% of the land within ¼ mile; the law asks for 15%. "
            "This line scales their effect up to 15%, in step with how much land each place zoned. "
            f"That is about {whole(up.effect_per_100_acres)} extra new homes per 100 lot acres a year. "
            "Applied to Wisconsin's lots within ¼ mile of rail and rapid stops, for five years: "
            f"about {k(up.extra_homes_2027_2031)} extra homes over 2027–2031 "
            f"(range about {k(up.range_low)} to {k(up.range_high)}, leaving out one place at a time). "
            "Caution: among the 11 places, bigger districts gained less per acre, so scaling up leans on the smallest districts. "
            f"Two other readings are what-ifs on How sure: rezoned stops on new transit lines ({whole(x2.extra_homes_2027_2031):,}), "
            f"and the same minus growth already under way before the reforms ({whole(ta.extra_homes_2027_2031):,}).")


# How each line's range was made (AQ-072).
RANGE_NOTE = {"little": "90% range from resampling stretches of district boundary",
              "typical": "leaving out one place at a time", "strong": "leaving out one place at a time"}


def trend_adjusted_text() -> str:
    """The trend-adjusted 2x2 what-if's note, from reference/tod_causal_line_age_pretrend.csv (T2b-PT; AQ-075)."""
    pt = pd.read_csv(REF / "tod_causal_line_age_pretrend.csv")
    fk = pt[(pt.version == "fake, same places") & (pt["row"] == "effect") & (pt["name"] == "law_near_new_lines")].iloc[0]
    ta = pt[(pt.version == "trend-adjusted") & (pt["row"] == "upper")].iloc[0]
    n = lambda v: f"{whole(v):,}".replace("-", "−")  # noqa: E731
    return (f"The before-reform check failed. Rezoned stops on new lines were already gaining {fk.value:.1f} extra new homes per 100 lot "
            f"acres a year before any reform (90% range {fk.lo90:.1f} to {fk.hi90:.1f}). Taking that out leaves {ta.value:.1f} a year: "
            f"about {n(ta.wisconsin)} homes over 2027–2031 (90% range {n(ta.wisconsin_lo90)} to {n(ta.wisconsin_hi90)}; "
            f"leaving out one place at a time, {n(ta.wisconsin_loo_low)} to {n(ta.wisconsin_loo_high)}).")
# The modelled law (AQ-071), for the screens.
DISTRICT = {"share": 0.15, "radius": "¼ mile", "min_homes_per_acre": 15,
            "text": "Every Wisconsin city with rail or rapid transit stops must zone a district where apartment buildings are allowed by right, at least 15 homes per acre, covering 15% of the land within ¼ mile of rail and rapid stops. The city picks the land. The model treats the district as spread at random over that land."}
# AQ-054: one median-line rule for every reform. A median line of real cases is shown only with at least
# MEDIAN_MIN_CASES comparable cases; TOD's scenarios rest on one whole-city study each.
MEDIAN_MIN_CASES = 4
TIMING = ("The places' effects were measured over the years after each reform. The model places that effect "
          "inside 2027–2031, the law's first five years. Much of a real law's effect may come after 2031, so the "
          "yearly path is the least certain part of these numbers.")

DEF_LABELS = {
    "rapid_half": "Rail and rapid transit only, within ½ mile",
    "main": "Main case: rail and rapid transit within ½ mile, plus buses every 15 minutes within ¼ mile",
    "high": "Wider: as the main case, plus buses every 20 minutes within ¼ mile",
    "b_half": "Rail, rapid transit and 15-minute buses, all within ½ mile",
    "c_half": "Rail, rapid transit and 20-minute buses, all within ½ mile",
    "any_half": "Any bus or train stop within ½ mile (for context, not \"major\" transit)",
}
BAND_LABELS = {"rapid_quarter": "Within ¼ mile of a rail or rapid transit station",
               "rapid_half": "¼ to ½ mile from a rail or rapid transit station",
               "bus15_quarter": "Within ¼ mile of a stop on a bus route every 15 minutes"}

AGENCY_LINES = {
    "Milwaukee County": "Milwaukee County Transit System: CONNECT 1 bus rapid transit (rapid) and the bus routes that run every 15 minutes at the morning peak",
    "City of Milwaukee": "The Hop streetcar (rail)",
    "City of Madison": "Madison Metro: Rapid Route A (rapid transit), plus Routes B, C, D and 80, which like Route A run at least every 15 minutes on weekdays",
    "City of Kenosha": "Kenosha streetcar (rail)",
    "City of Eau Claire": "Eau Claire Transit: Routes 9 and 19 run every 20 minutes, so they count only in the wider definitions",
}

SENS_LABELS = {
    ("law_addition", "typical_range"): ("Central line at the low and high ends of its range", "The 11 places' average recomputed 11 times, each time leaving one place out."),
    ("law_addition", "upper_2x2"): ("Upzoning with new transit lines", "Near lines that were new when the reform came, rezoned stops against new-line stops not rezoned (7 and 9 places). The upper line for part of 3 November 2026, until its before-reform check failed. Those cities chose to rezone around their new stations."),
    ("law_addition", "upper_2x2_trend_adjusted"): ("Upzoning with new transit lines, minus the growth already under way before the reforms (fake-years check)", None),
    ("law_addition", "optiond_lower"): ("Former lower: the best lot model", "The lower line before 3 November 2026: a model of each lot's new homes with lot and place traits. No model beat the plain average on places it had not seen."),
    ("law_addition", "line_age_matched"): ("Beside the central: compared with stops of a similar age", "Each reform stop compared only with stops on lines of a similar age, so new-line growth is not counted as the reform's. Denver and Charlotte fall most."),
    ("law_addition", "strong_range"): ("Upper line at the low and high ends of its range", "The 11 places' scaled average recomputed 11 times, each time leaving one place out."),
    ("law_addition", "little_range"): ("Lower line at the low and high ends of its range", "The 90% range of the edge test, from resampling stretches of boundary. Leaving out one place at a time gives about 1,600 to 4,870."),
    ("law_addition", "district_10"): ("District of 10% instead of 15%", "The upper line's method (the places' pooled effect per share of land zoned) at a 10% district."),
    ("law_addition", "district_25"): ("District of 25% instead of 15%", "The same at a 25% district. The places' effect fell as their district share grew, so this may overstate."),
    ("law_addition", "former_central_average_reform"): ("Former central line: average reform city, broader law", "The line used before 2 November 2026, for a law that upzoned about 71% of the land within ¼ mile: 16 places' pooled effect per share of land upzoned, applied at 71% (13,229 as shown then; recomputed with the corrected lot data)."),
    ("law_addition", "former_strong_auckland"): ("Former strong line: Auckland", "Auckland, New Zealand, upzoned three-quarters of its residential land in 2016 and permitted 21,808 extra homes over 2016–2021 (4.1% of its homes, per upzoned home). Timed like Auckland."),
    ("law_addition", "former_little_station_area"): ("Former little line: station-area model, broader law", "The station-area lot model's answer for the broader law (about 71% of the land within ¼ mile upzoned): 43 as shown then; recomputed with the corrected lot data, now slightly below zero."),
    ("law_addition", "la_toc_little"): ("Earlier little line: Los Angeles's transit program", "Los Angeles's Transit Oriented Communities program (2017) added 0.04 percentage points to the city's housing growth over six years (per upzoned home). It required affordable homes, which the modelled law does not."),
    ("law_addition", "drift_central"): ("Earlier central line: upzoned-share trend in 9 cities", "From our lot data on 9 US cities: upzoned lots' share of new homes rose after each reform, more where it started low (a rule found after seeing the results). About 1,200."),
    ("law_addition", "stacy_typical"): ("Earlier typical line: the average loosening reform", "Stacy and others (2023): about +0.8% more addresses after a loosening reform in 1,136 US cities. Most of those reforms were about accessory dwellings and lot sizes, not transit."),
    ("law_addition", "ramp_new_york"): ("Timing: New York rezonings' build-up (the former ramp)", "Each line spread over the years like the build-up measured after the New York rezonings, the timing used before 11 November 2026: most homes in 2030, few in 2031. Changes timing only; the five-year totals stay the same."),
    ("law_addition", "ramp_year5_alt"): ("Smoother final year (New York build-up)", "The former New York build-up with 2031 set to the average of 2029–2031 instead of its measured drop. Changes timing only; the five-year totals stay the same."),
    ("where_homes_land", "old_law_placement"): ("Homes placed as under the broader law", "Each place gets homes in proportion to the extra floor area the broader law would have allowed, not its land within ¼ mile of rail and rapid stops. Statewide totals are the same."),
    ("where_homes_land", "no_suburbs"): ("Only Milwaukee and Madison get homes", "Suburbs with rail or rapid stops (Wauwatosa, Kenosha, Shorewood Hills, Sun Prairie and others) get none of the extra homes. Statewide totals are the same."),
    ("where_homes_land", "rapid_only"): ("Only rail and rapid transit stations count as near stops", "Changes which homes count as near stops, so current law near stops changes. The law's extra homes stay the same: the district is within ¼ mile of rail and rapid stops either way."),
    ("where_homes_land", "high"): ("Buses every 20 minutes count as near stops too", "Adds 20-minute bus routes within ¼ mile, including Eau Claire's, to the area counted as near stops. The law's extra homes stay the same."),
    ("where_homes_land", "b_half"): ("All 15-minute stops count within ½ mile", "Bus stops get the same ½ mile as stations in the area counted as near stops. The law's extra homes stay the same."),
    ("baseline_only", "baseline_low"): ("Low current-law path", "The low end of a range that aims at 90%, built from all states' past five-year outcomes and set around Wisconsin's central (0.46 times the central)."),
    ("baseline_only", "baseline_high"): ("High current-law path", "The high end of a range that aims at 90%, built from all states' past five-year outcomes and set around Wisconsin's central (1.77 times the central)."),
    ("baseline_only", "census_as_published"): ("Milwaukee's apartments as the Census published them", "The Census permit file misses most of Milwaukee's apartments; the main case uses the city's property file instead."),
}
TORNADO = {
    "current": [
        ("Lower line", "main", "little"),
        ("Upper line", "main", "strong"),
        ("Central, one place left out: lowest", "typical_range", "typical_low"),
        ("Central, one place left out: highest", "typical_range", "typical_high"),
        ("Lower line, low end of its 90% range", "little_range", "little_low"),
        ("Lower line, high end of its 90% range", "little_range", "little_high"),
        ("Upper line, one place left out: lowest", "strong_range", "strong_low"),
        ("Upper line, one place left out: highest", "strong_range", "strong_high"),
        ("District of 10% of land instead of 15%", "district_10", "strong"),
        ("District of 25% of land instead of 15%", "district_25", "strong"),
        ("Compared with stops on lines of similar age", "line_age_matched", "typical"),
        ("Upzoning with new transit lines", "upper_2x2", "strong"),
        ("Upzoning with new transit lines, minus growth under way before the reforms", "upper_2x2_trend_adjusted", "strong"),
    ],
    "earlier": [
        ("Former lower: best lot model", "optiond_lower", "little"),
        ("Former central: average reform city, broader law", "former_central_average_reform", "typical"),
        ("Former strong: Auckland", "former_strong_auckland", "strong"),
        ("Former little: station-area model, broader law", "former_little_station_area", "little"),
        ("Earlier little: Los Angeles transit program", "la_toc_little", "little"),
        ("Earlier central: upzoned-share trend, 9 cities", "drift_central", "typical"),
        ("Earlier typical: average loosening reform", "stacy_typical", "typical"),
    ],
}
TIMING_ONLY = ("ramp_new_york", "ramp_year5_alt")   # what-ifs that change the yearly split only
GROUPS = [("law_addition", "What-ifs that change the law's addition"),
          ("where_homes_land", "What-ifs that change where the homes land (and, for the stop rules, how many homes are near stops)"),
          ("baseline_only", "What-ifs that change current law only")]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def r(v, nd=2):
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return v
    return None if math.isnan(f) else round(f, nd)


def whole(v) -> int:
    """Round half up to a whole number (display totals; avoids half-even surprises)."""
    return int(math.floor(float(v) + 0.5))


SCEN_TEXT["strong"]["info"] = upper_info()


def s(v):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else str(v)


def doc(path: str, label: str) -> dict:
    return {"label": label, "url": DOC + path}


def metro_of(county: str) -> str:
    for k, (_, counties) in METROS.items():
        if county in counties:
            return k
    return REST[0]


# ---- shared units (AQ-054) ----------------------------------------------------------------------
def acs_housing_units() -> int:
    """Wisconsin's total housing units, ACS 2020-2024 five-year (B25002), the home count for cross-reform figures."""
    h = pd.read_csv(REF / "gate5_housing_health.csv")
    return int(h[h["indicator"] == "total_housing_units_acs"]["value"].iloc[0])


def all_housing_baseline_by_area() -> pd.Series:
    """Each municipality piece's all-housing baseline, central, 2027-2031 (all building sizes)."""
    hb = pd.read_csv(REF / "housing_baseline_by_area.csv")
    return hb.groupby("area_id")["five_year_central"].sum()


# ---- statewide --------------------------------------------------------------------------------
def build_statewide() -> dict:
    st = pd.read_csv(REF / "tod_model_statewide.csv")
    st["year"] = st["year"].astype(str)
    five = st[st["year"] == "2027-2031"].set_index("scenario")
    yr = st[st["year"] != "2027-2031"].copy()
    yr["year"] = yr["year"].astype(int)
    t0 = five.loc["typical"]
    base_years = yr[yr["scenario"] == "typical"].sort_values("year")
    baseline = {
        "years": [{"year": int(x.year), "low": r(x.baseline_near_stops_low, 4), "central": r(x.baseline_near_stops_central, 4),
                   "high": r(x.baseline_near_stops_high, 4)} for x in base_years.itertuples()],
        "total": r(t0["baseline_near_stops_central"], 4), "low_total": r(t0["baseline_near_stops_low"], 4),
        "high_total": r(t0["baseline_near_stops_high"], 4),
    }
    scen = []
    for sid in SCEN:
        f = five.loc[sid]
        ys = yr[yr["scenario"] == sid].sort_values("year")
        row = {"id": sid, **SCEN_TEXT[sid], "share_of_stock": r(f["addition_share_of_stock"], 6),
               "additional_total": r(f["addition"], 4), "with_law_total": r(f["with_law_central"], 4),
               "by_year": [r(v, 4) for v in ys["addition"]], "source": s(f["source"])}
        if pd.notna(f["addition_range_low"]):
            row.update(range_low=r(f["addition_range_low"], 4), range_high=r(f["addition_range_high"], 4),
                       range_note=RANGE_NOTE[sid])
        scen.append(row)
    # statewide all-housing baseline (the TOD baseline is the part of it near qualifying stops), and the shared
    # cross-reform units (AQ-054): extra homes a year statewide against that baseline, and shares of Wisconsin's
    # ACS 2020-2024 home count. The station-area maths keeps 2020 census blocks.
    hb = pd.read_csv(REF / "housing_baseline_statewide_by_year.csv")
    hbp = hb[(hb["kind"] == "projected") & (hb["structure_type"] == "all") & hb["year"].isin(YEARS)]
    state_base = float(hbp["central"].sum())
    acs_homes = acs_housing_units()
    for row in scen:
        row["per_year"] = r(row["additional_total"] / len(YEARS), 4)
        row["share_of_state_baseline"] = r(row["additional_total"] / state_base, 6)
        row["share_of_acs_homes"] = r(row["additional_total"] / acs_homes, 6)
    d = pd.read_csv(REF / "tod_definition_summary.csv")
    ladder = []
    for x in d[d["definition"].isin(DEF_LABELS)].sort_values("homes").itertuples():
        ladder.append({"id": x.definition, "label": DEF_LABELS[x.definition], "stops": int(x.stops), "homes": int(x.homes),
                       "share_of_state": r(x.homes / x.state_homes_2020, 4), "main": x.definition == "main",
                       "context": x.definition == "any_half"})
    sa = pd.read_csv(REF / "tod_station_areas.csv")
    law = []
    for band, lab in BAND_LABELS.items():
        b = sa[sa["band"] == band].iloc[0]
        law.append({"band": band, "label": lab, "height_ft": int(b.law_height_ft), "homes_per_acre": int(b.law_homes_per_acre),
                    "far": r(b.law_far, 2)})
    stops = pd.read_csv(REF / "tod_stops.csv")
    agencies = []
    for ag, g in stops.groupby("agency", sort=True):
        agencies.append({"agency": ag, "lines": AGENCY_LINES.get(ag, ""), "rapid": int(g.flag_a_rapid.sum()),
                         "bus15": int(((g.flag_b_15min == 1) & (g.flag_a_rapid == 0)).sum()),
                         "bus20_only": int(((g.flag_c_20min == 1) & (g.flag_b_15min == 0)).sum()),
                         "main_case": int(((g.flag_a_rapid == 1) | (g.flag_b_15min == 1)).sum())})
    agencies.sort(key=lambda a: -a["main_case"])
    main_def = d.set_index("definition").loc["main"]
    ck = pd.read_csv(REF / "tod_model_checks.csv")
    ck = ck[(ck["check"] == "scale") & (ck["sizing"] == "net_effect") & ck["scenario"].isin(SCEN) & (ck["exceeds_own_max"] == True)]  # noqa: E712
    record = []
    for sc_, g in ck.groupby("scenario", sort=False):
        for metro, h in g.groupby("metro", sort=True):
            record.append({"scenario": sc_, "metro": METROS[SCALE_METRO[metro]][0], "years": [int(y) for y in sorted(h["year"])]})
    od = pd.read_csv(REF / "tod_optiond_line.csv").set_index("line")
    district = {**DISTRICT, "places": int(od.loc["optiond_average", "places"]),
                "places_mean_share": r(od.loc["optiond_average", "mean_district_share"], 3),
                "effect_per_100_acres": r(od.loc["optiond_average", "mean_effect_per_100_acres"], 2),
                "wi_acres_two_cities": r(od.loc["optiond_average", "wi_acres_quarter"], 1),
                "statewide_scale": r(od.loc["optiond_average", "statewide_scale"], 4),
                "linear_fit_15": r(od.loc["optiond_linear_fit_15", "extra_homes_2027_2031"], 1)}
    return {
        "state_homes": int(main_def.state_homes_2020), "stock_homes": int(t0["stock_homes_station_areas"]),
        "homes_two_cities": {"milwaukee": int(main_def.milwaukee_city_homes), "madison": int(main_def.madison_city_homes),
                             "share": r(main_def.share_in_two_cities, 4)},
        "ladder": ladder, "law": law, "district": district, "record_years": record, "agencies": agencies,
        "baseline": baseline, "state_baseline_total": r(state_base, 4), "state_baseline_per_year": r(state_base / len(YEARS), 4),
        "acs_homes": acs_homes,
        "scenarios": scen,
        "median_line": {"shown": len(scen) >= MEDIAN_MIN_CASES, "min_cases": MEDIAN_MIN_CASES, "n_studies": len(scen),
                        "note": f"A median line of real cases is shown only when there are at least {MEDIAN_MIN_CASES} comparable cases. "
                                f"Here the central line is already the average of the {district['places']} district places, so no separate median line is shown."},
        "timing_caveat": TIMING,
    }


# ---- the uniform range display (docs/UNIFORM_DISPLAY_SPEC.md) -------------------------------------
RANGE_UNIT = "extra homes permitted near major transit stops, Wisconsin, 2027–2031"
# Side lines across the range (spec, "Side lines"): label, the reference file and line, and one plain sentence.
TOD_SIDE_LINES = [
    ("average", "Average district place, 11 places (the former central)", "tod_optiond_line.csv", "optiond_average",
     "The average measured effect of the 11 places that zoned a district near their stops, applied to Wisconsin's land within ¼ mile."),
    ("edge", "Edge test, rezoned lots' own gain (5 places)", "tod_causal_lines.csv", "causal_lower_edge",
     "Only the gain on the rezoned lots themselves, just inside against just outside district boundaries."),
    ("scaled15", "Average scaled to a 15% district (11 places)", "tod_causal_lines.csv", "upper_average_scaled_15",
     "The same average, scaled up from the places' 12% of land to the law's 15%; bigger districts gained less per acre."),
    ("new_lines_2x2", "Rezoning near new transit lines, 2×2 (9 places)", "tod_causal_lines.csv", "causal_upper_2x2",
     "Rezoned stops on lines that were new at the time, against new-line stops that were not rezoned."),
    ("new_lines_trend", "Same minus the growth already under way before the reforms", "tod_causal_lines.csv", "whatif_2x2_trend_adjusted",
     "The 2×2 reading after taking out the faster growth those stops already had before any reform (its before-reform check failed)."),
]


def build_range90(sw: dict) -> tuple[dict, list]:
    """TOD's 90% range: the place bootstrap of the 11 district places (reference/tod_line_draws.csv, central_homes),
    widened about the bootstrap point by the coverage test's factor (reference/tod_coverage_test.csv). The yearly band
    applies each widened draw to the central line's yearly profile and takes each year's 5th to 95th percentiles."""
    cov = pd.read_csv(REF / "tod_coverage_test.csv")
    wid = cov[cov["check"] == "widening"].set_index("measure")
    f_csv = float(wid.loc["widening factor f", "value"])
    wr = wid.loc["widened Wisconsin 90% range"]
    point, w_lo, w_hi = float(wr["value"]), float(wr["lo90"]), float(wr["hi90"])
    cv = cov[(cov["check"] == "coverage") & cov["pool"].str.startswith("real")].iloc[0]
    fake = cov[(cov["check"] == "coverage") & cov["pool"].str.startswith("fake")].iloc[0]
    draws = pd.read_csv(REF / "tod_line_draws.csv")["central_homes"].astype(float)
    p5, p95 = float(draws.quantile(0.05)), float(draws.quantile(0.95))
    # The CSV prints f to 4 decimals; the factor that reproduces its widened ends exactly is read back from them.
    f = (point - w_lo) / (point - p5)
    assert abs(f - f_csv) < 5e-5 and abs((w_hi - point) / (p95 - point) - f) < 5e-5, (f, f_csv)
    widened = point + f * (draws - point)
    typ = next(x for x in sw["scenarios"] if x["id"] == "typical")
    shares = [v / sum(typ["by_year"]) for v in typ["by_year"]]
    lo_tot, hi_tot = float(widened.quantile(0.05)), float(widened.quantile(0.95))
    # Each end of the range follows the yearly shares (the 11 places' build-up, owner 2026-11-11), so each year's low and
    # high add up to the five-year ends. Year 2's share is negative as measured, so there its low end is above its high end.
    years = [{"year": y, "low": r(lo_tot * sh, 2), "high": r(hi_tot * sh, 2)} for y, sh in zip(YEARS, shares)]
    k = lambda v: f"{whole(v):,}"  # noqa: E731
    range90 = {
        "low": r(float(widened.quantile(0.05)), 1), "high": r(float(widened.quantile(0.95)), 1), "unit": RANGE_UNIT,
        "method": (f"Place bootstrap of the 11 district places ({len(draws):,} draws), widened ×{f_csv:.4f} about {k(point)} "
                   f"after a coverage test: the unwidened range was {k(p5)} to {k(p95)}."),
        "coverage": (f"The unwidened range held the true average in {cv['value'] * 100:.1f}% of test runs, below 90%, so it was widened. "
                     f"A check on fake effects held only {round(fake['value'] * 100):.0f}%, so the range may still be narrow."),
        "years_method": "Each end of the range is spread over the years by the same yearly shares as the lines, so each year's ends add up to the five-year ends.",
        "source": "reference/tod_line_draws.csv (central_homes), widened by reference/tod_coverage_test.csv; docs/UNIFORM_DISPLAY_SPEC.md",
        "years": years,
    }
    # The record-year warning, checked at the range's high end (spec): the tool spreads homes by fixed shares, so each
    # metro-year's extra apartment homes per 1,000 scale with the statewide total from the average district place's.
    ck = pd.read_csv(REF / "tod_model_checks.csv")
    ck = ck[(ck["check"] == "scale") & (ck["sizing"] == "net_effect") & (ck["scenario"] == "typical")]
    scale_hi = range90["high"] / typ["additional_total"]
    record = []
    for metro, g in ck.groupby("metro", sort=True):
        tot = g["baseline_per_1000"] + g["extra_per_1000"] * scale_hi
        over = sorted(int(y) for y, v in zip(g["year"], tot) if v > g["own_max"].iloc[0])
        k_ = tot.idxmax()
        record.append({"metro": METROS[SCALE_METRO[metro]][0], "years_above_own_record": over,
                       "peak_year": int(g.loc[k_, "year"]), "peak_total_per_1000": r(float(tot[k_]), 2),
                       "own_max": r(float(g["own_max"].iloc[0]), 2), "above_observed_max": bool((tot > g["observed_max"]).any()),
                       "observed_max": r(float(g["observed_max"].iloc[0]), 2)})
    range90["record_check_high"] = record
    side = []
    for sid, label, fname, line, note in TOD_SIDE_LINES:
        v = float(pd.read_csv(REF / fname).set_index("line").loc[line, "extra_homes_2027_2031"])
        side.append({"id": sid, "label": label, "value": r(v, 1), "where": "chart", "note": note,
                     "source": f"reference/{fname} ({line})"})
    return range90, side


# ---- areas ------------------------------------------------------------------------------------
def by_years(row) -> list:
    return [r(row[f"add_{y}"], 4) for y in YEARS]


def build_additions() -> dict:
    """additions_by_area.json for combined views (docs/shared/SCENARIO_CONTRACT.md section 9): each
    municipality's additions by year and path. TOD acts only near stops, so every row is part "near_stops"."""
    a = pd.read_csv(REF / "tod_model_by_area.csv")
    a = a[(a["sizing"] == "net_effect") & a["scenario"].isin(SCEN)]
    rows = {}
    for x in a.itertuples():
        row = rows.setdefault(x.area_id, {"area_id": x.area_id, "part": "near_stops"})
        row[x.scenario] = by_years(x._asdict())
    return {"reform": "tod", "baseline_version": BASELINE_VERSION, "years": YEARS,
            "paths": [{"id": k, "label": SCEN_TEXT[k]["label"]} for k in SCEN], "roles": ROLES,
            "split_source": "reference/tod_model_by_area.csv (net-effect sizing; all additions are near stops)",
            "areas": [rows[k] for k in sorted(rows)]}


def build_areas() -> dict:
    a = pd.read_csv(REF / "tod_model_by_area.csv")
    near = pd.read_csv(REF / "tod_near_stop_homes_by_muni.csv").set_index("area_id")
    coded = {"Milwaukee city", "Madison city"}
    munis = {}
    for x in a.itertuples():
        m = munis.setdefault(x.area_id, {
            "id": x.area_id, "name": x.name, "county": x.county, "metro": metro_of(x.county), "coded": x.name in coded,
            "homes_near": int(near.loc[x.area_id, "homes_near_main"]), "share_near": r(x.share_near_stops, 4),
            "eligible_acres": r(x.eligible_acres, 1), "baseline": r(x.baseline_near_central_2027_2031, 4),
            "baseline_low": r(x.baseline_near_low_2027_2031, 4), "baseline_high": r(x.baseline_near_high_2027_2031, 4),
            "add": {}, "add_years": {}})
        if x.scenario in SCEN:
            m["add"][x.scenario] = r(x.add_2027_2031, 4)
            m["add_years"][x.scenario] = by_years(x._asdict())
    munis = sorted(munis.values(), key=lambda m: -m["add"]["typical"])
    # option D placement land (AQ-071): lot acres within 1/4 mile of rail and rapid stops, by place
    sa = pd.read_csv(REF / "tod_station_areas.csv")
    qa = sa[(sa["band"] == "rapid_quarter") & (sa["in_main"] == 1)].groupby("city")["acres"].sum()
    for m in munis:
        m["quarter_acres"] = r(float(qa.get(m["name"], 0.0)), 1)
    # all-housing baseline by place, county and district (AQ-054 shared unit, by area); districts use the same
    # detached-home crosswalk as the TOD district figures
    allb = all_housing_baseline_by_area()
    for m in munis:
        m["all_baseline"] = r(allb.get(m["id"], 0.0), 4)
    allb_df = allb.rename("v").reset_index()
    by_county = allb_df.merge(near[["county"]], left_on="area_id", right_index=True, how="left").groupby("county")["v"].sum()
    cw = pd.read_csv(REF / "adu_model_district_crosswalk.csv")
    xw = allb_df.merge(cw[["area_id", "assembly_district", "senate_district", "share"]], on="area_id", how="inner")
    xw["v"] = xw["v"] * xw["share"]
    by_asm, by_sen = xw.groupby("assembly_district")["v"].sum(), xw.groupby("senate_district")["v"].sum()

    def agg(file, key, name_fn, all_base):
        df = pd.read_csv(REF / file)
        out = {}
        for x in df.itertuples():
            k = getattr(x, key)
            o = out.setdefault(k, {"id": str(k), "name": name_fn(k), "baseline": r(x.baseline_near_central_2027_2031, 4),
                                   "all_baseline": r(all_base.get(k, 0.0), 4), "add": {}})
            if x.scenario in SCEN:
                o["add"][x.scenario] = r(x.add_2027_2031, 4)
        rows = list(out.values())
        nonzero = [o for o in rows if o["baseline"] > 0 or any(v > 0 for v in o["add"].values())]
        return {"rows": sorted(nonzero, key=lambda o: -o["add"]["typical"]), "total_count": len(rows),
                "all_baseline_total": r(sum(o["all_baseline"] for o in rows), 4)}

    counties = agg("tod_model_by_county.csv", "county", lambda k: k, by_county)
    assembly = agg("tod_model_by_assembly_district.csv", "assembly_district", lambda k: f"Assembly District {k}", by_asm)
    senate = agg("tod_model_by_senate_district.csv", "senate_district", lambda k: f"Senate District {k}", by_sen)
    metros = []
    for mid, label in [(k, v[0]) for k, v in METROS.items()] + [REST]:
        ms = [m for m in munis if m["metro"] == mid]
        metros.append({"id": mid, "name": label, "places": len(ms),
                       "counties": sorted({m["county"] for m in ms}),
                       "homes_near": sum(m["homes_near"] for m in ms),
                       "baseline": r(sum(m["baseline"] for m in ms), 4),
                       "all_baseline": r(sum(by_county.get(c, 0.0) for c in METROS[mid][1]), 4) if mid in METROS else None,
                       "add": {sc: r(sum(m["add"][sc] for m in ms), 4) for sc in SCEN}})
    # places that get extra homes with few homes near stops today: homes are placed by land within 1/4 mile of rail
    # and rapid stops (AQ-071)
    few = [m["name"] for m in munis if m["homes_near"] < 100 and m["add"]["typical"] >= 1]
    # places whose current-law figure rests on very few reported permits in 2021-2025 while the law adds many homes
    hist = pd.read_csv(REF / "housing_baseline_history.csv")
    low = []
    for m in munis:
        if m["add"]["typical"] >= 50 and m["baseline"] < 10:
            h = hist[(hist["area_id"] == m["id"]) & hist["year"].between(2021, 2025)].sort_values("year")
            low.append({"name": m["name"], "years": [int(y) for y in h["year"]], "units": [r(u, 0) for u in h["units_all"]],
                        "units_5plus": r(h["units_5plus"].sum(), 0)})
    # the shared baseline keeps a small statewide row that is not allocated to any place (its reconciliation residual)
    unalloc = float(allb[~allb.index.str.startswith("muni:")].sum())
    return {"munis": munis, "metros": metros, "counties": counties, "assembly": assembly, "senate": senate,
            "all_baseline_unallocated": r(unalloc, 4), "few_homes_places": few, "low_permit_places": low}


# ---- map ---------------------------------------------------------------------------------------
def build_map(areas: dict) -> dict:
    stops = pd.read_csv(REF / "tod_stops.csv")
    ags = sorted(stops["agency"].unique())
    pts = []
    for x in stops.sort_values(["agency", "lat", "lon"]).itertuples():
        kind = "r" if x.flag_a_rapid else "b" if x.flag_b_15min else "c" if x.flag_c_20min else None
        if kind:
            pts.append([round(float(x.lon), 4), round(float(x.lat), 4), kind, ags.index(x.agency)])
    views = []
    for vid, label, agencies in [("milwaukee", "Milwaukee area", ["Milwaukee County", "City of Milwaukee"]),
                                 ("madison", "Madison area", ["City of Madison"]),
                                 ("kenosha", "Kenosha", ["City of Kenosha"]),
                                 ("eau-claire", "Eau Claire", ["City of Eau Claire"])]:
        g = stops[stops["agency"].isin(agencies)]
        pad = 0.02
        views.append({"id": vid, "label": label, "agencies": [ags.index(a) for a in agencies],
                      "bounds": [round(g.lon.min() - pad, 3), round(g.lat.min() - pad, 3), round(g.lon.max() + pad, 3), round(g.lat.max() + pad, 3)]})
    # municipality outlines (already public in the ADU bundle), clipped to views by bounding box, rounded to 3 decimals
    geo = json.loads((ROOT / GEO_MUNIS).read_text())
    near = pd.read_csv(REF / "tod_near_stop_homes_by_muni.csv").set_index("area_id")
    tod_ids = {m["id"] for m in areas["munis"]}
    outlines = []

    def rings_of(gm):
        polys = [gm["coordinates"]] if gm["type"] == "Polygon" else gm["coordinates"]
        return [ring for poly in polys for ring in poly[:1]]  # outer rings only

    for f in sorted(geo["features"], key=lambda f: f["properties"]["id"]):
        fid = f["properties"]["id"]
        rings = rings_of(f["geometry"])
        xs = [p[0] for rg in rings for p in rg]
        ys = [p[1] for rg in rings for p in rg]
        bb = (min(xs), min(ys), max(xs), max(ys))
        in_view = [v["id"] for v in views if not (bb[2] < v["bounds"][0] or bb[0] > v["bounds"][2] or bb[3] < v["bounds"][1] or bb[1] > v["bounds"][3])]
        if not in_view:
            continue
        simple = []
        for rg in rings:
            out = []
            for p in rg:
                q = [round(p[0], 3), round(p[1], 3)]
                if not out or out[-1] != q:
                    out.append(q)
            if len(out) >= 4:
                simple.append(out)
        if simple:
            outlines.append({"id": fid, "name": s(near["name"].get(fid)) if fid in near.index else None,
                             "tod": fid in tod_ids, "views": in_view, "rings": simple})
    return {"agencies": ags, "stops": pts, "views": views, "outlines": outlines,
            "radius_mi": {"r": 0.5, "b": 0.25, "c": 0.25}}


# ---- how sure ---------------------------------------------------------------------------------
def build_howsure(sw: dict, areas: dict) -> dict:
    se = pd.read_csv(REF / "tod_model_sensitivities.csv")
    ne = se[se["sizing"] == "net_effect"]
    main = ne[ne["group"] == "main"].set_index("scenario")
    groups = []
    for gid, glabel in GROUPS:
        rows = []
        g = ne[ne["group"] == gid]
        for sens in g["sensitivity"].drop_duplicates():
            sg = g[g["sensitivity"] == sens].set_index("scenario")
            label, text = SENS_LABELS[(gid, sens)]
            if sens == "upper_2x2_trend_adjusted":
                text = trend_adjusted_text()
            row = {"id": sens, "label": label, "text": text, "baseline": r(sg["baseline_near_stops_2027_2031"].iloc[0], 4), "add": {}}
            if sens == "typical_range":
                row["add"] = {"typical_low": r(sg.loc["typical_low", "addition_2027_2031"], 4), "typical_high": r(sg.loc["typical_high", "addition_2027_2031"], 4)}
                row["milwaukee_metro"] = None
            elif sens in ("little_range", "strong_range"):
                k = sens.removesuffix("_range")
                row["add"] = {f"{k}_low": r(sg.loc[f"{k}_low", "addition_2027_2031"], 4), f"{k}_high": r(sg.loc[f"{k}_high", "addition_2027_2031"], 4)}
                row["milwaukee_metro"] = None
            else:
                for sc in SCEN:
                    if sc in sg.index:
                        row["add"][sc] = r(sg.loc[sc, "addition_2027_2031"], 4)
                tsc = "typical" if "typical" in sg.index else sg.index[0]
                row["milwaukee_metro"] = r(sg.loc[tsc, "milwaukee_metro_2027_2031"], 4)
                row["madison_metro"] = r(sg.loc[tsc, "madison_metro_2027_2031"], 4)
                row["metro_scenario"] = tsc
                row["year_2031"] = {sc: r(sg.loc[sc, "add_2031"], 4) for sc in SCEN if sc in sg.index}
                if sens in TIMING_ONLY:
                    row["typical_by_year"] = [r(sg.loc["typical", f"add_{y}"], 4) for y in YEARS]
            rows.append(row)
        groups.append({"id": gid, "label": glabel, "rows": rows})
    pa = se[se["sizing"] == "per_acre"]
    pmain = pa[(pa["group"] == "per_acre: main") & pa["scenario"].isin(SCEN)].set_index("scenario")
    wis = pa[pa["group"] == "per_acre"].set_index("sensitivity")
    per_acre = {
        "add": {sc: r(pmain.loc[sc, "addition_2027_2031"], 4) for sc in SCEN},
        "wisconsin_uncapped": r(wis.loc["wisconsin_measured_uncapped", "addition_2027_2031"], 4),
        "wisconsin_capped": r(wis.loc["wisconsin_measured_capped", "addition_2027_2031"], 4),
    }
    # scale check: peak year of apartment permitting per metro and scenario
    ck = pd.read_csv(REF / "tod_model_checks.csv")
    sc_rows = ck[(ck["check"] == "scale") & (ck["sizing"] == "net_effect") & ck["scenario"].isin(SCEN)]
    my = pd.read_csv(REF / "tod_scale_check_metro_years.csv")
    bench = pd.read_csv(REF / "tod_scale_check.csv")
    obsmax = bench[bench["statistic"] == "observed_max_peer_metro_year"].iloc[0]
    p95 = bench[bench["statistic"] == "p95_peer_metro_years"].iloc[0]
    scale = []
    for metro, mid in SCALE_METRO.items():
        own = my[my["cbsa_name"] == metro].sort_values("rate_5plus_per_1000").iloc[-1]
        row = {"metro": mid, "name": METROS[mid][0], "own_max": r(own.rate_5plus_per_1000, 4), "own_max_year": int(own.year),
               "baseline_per_1000": None, "peak": {}}
        for sc in SCEN:
            g = sc_rows[(sc_rows["metro"] == metro) & (sc_rows["scenario"] == sc)].sort_values("total_per_1000")
            pk = g.iloc[-1]
            row["baseline_per_1000"] = r(pk.baseline_per_1000, 2)
            row["peak"][sc] = {"year": int(pk.year), "total_per_1000": r(pk.total_per_1000, 2), "exceeds_own_max": bool(pk.exceeds_own_max == True)}  # noqa: E712
        scale.append(row)
    msh = ck[ck["check"] == "madison_share"]
    measured = msh[(msh["sizing"] == "measured") & msh["basis"].str.startswith("judged")].iloc[0]
    measured_main = msh[(msh["sizing"] == "measured") & msh["basis"].str.startswith("main estimate x treated acres / all homes")].iloc[0]
    scen3 = msh[(msh["sizing"] == "net_effect") & msh["scenario"].isin(SCEN)].set_index("scenario")
    madison = {"judged": {"share": r(measured.share_3yr, 6), "low": r(measured.share_3yr_low, 6), "high": r(measured.share_3yr_high, 6),
                          "homes": r(measured.extra_homes_3yr, 0), "stock": int(measured.stock_homes)},
               "main": {"share": r(measured_main.share_3yr, 6)},
               "scenarios": {sc: r(scen3.loc[sc, "share_3yr"], 6) for sc in SCEN}}
    mt = {m["id"]: m for m in areas["munis"]}
    coded_typ = sum(m["add"]["typical"] for m in mt.values() if m["coded"])
    tot_typ = next(x for x in sw["scenarios"] if x["id"] == "typical")["additional_total"]
    trace = [
        {"part": "Bus and train stops, and how often buses come", "status": "observed",
         "text": "Stop locations from the federal National Transit Map; frequencies from each agency's own schedule file or, for Madison, its published route descriptions."},
        {"part": "Homes near qualifying stops", "status": "observed",
         "text": f"2020 census homes in blocks whose centre lies within the distance: {sw['stock_homes']:,} homes in the main case."},
        {"part": "Current-law homes permitted near stops", "status": "calculated",
         "text": "Each place's expected new homes under current law (Census building permits, 2023–2025 average, with Milwaukee's apartments counted from its property records), times its share of homes near stops."},
        {"part": "Size of the law's addition", "status": "calculated",
         "text": "All three lines come from our own lot-by-lot data on US places that zoned a district for denser housing near some of their rail or rapid stops (docs/tod/CAUSAL_FRAMEWORK_PLAN.md, docs/tod/OPTION_D_PLAN.md). Central: the 11 places' average effect within ¼ mile, against similar stops without reform (no model beat this average on places it had not seen). Lower: the edge test, inside versus just outside district boundaries in 5 places: the rezoned lots' own gain only. Upper: the same 11 places' effect scaled up to a district of 15% of the land. Rezoned stops on new lines (the 2×2) are a what-if. Land beyond ¼ mile counts zero. Earlier lines are shown as comparisons."},
        {"part": "That those results carry over to Wisconsin", "status": "assumed",
         "text": "No Wisconsin outcome has tested the sizing. The training cities chose their district land, often land builders already wanted; Wisconsin's district is modelled as spread at random over the ¼-mile land, and a mandate may do less than a city's own choice. A check near Milwaukee's streetcar, with no rezoning, found building rose about as much as in a typical reform place, so quarter-mile gains of that size can happen without zoning changes."},
        {"part": "Timing over 2027–2031", "status": "calculated",
         "text": "Every line follows the yearly build-up measured across the same 11 places behind the range (their average effect in each of the first five years after reform). The second year dips slightly below zero, as measured."},
        {"part": "Where homes land", "status": "assumed",
         "text": f"The district is spread at random over the land within ¼ mile of rail and rapid stops, so each place gets the statewide homes in proportion to its lot acres there. Milwaukee and Madison get {round(coded_typ / tot_typ * 100)}% of the central line's homes; suburbs with rail or rapid stops (Wauwatosa, Kenosha, Shorewood Hills, Sun Prairie and others) get the rest."},
        {"part": "Split into legislative districts", "status": "assumed",
         "text": "Each place's numbers are split across districts in proportion to where its detached houses are (the same split the ADU screens use), not by homes near stops."},
    ]
    pairs = pd.read_csv(REF / "tod_trait_pairs.csv")
    n_traits = len(set(pairs.trait_a) | set(pairs.trait_b))
    tools = pd.read_csv(REF / "tod_trait_tools.csv")
    n_tools = int(tools.loc[~tools["tool"].str.startswith("0."), "tool"].nunique())
    n_pass = int((pairs.verdict == "pass").sum()) + int((tools.get("verdict", pd.Series(dtype=str)) == "pass").sum())
    allvars = pd.read_csv(REF / "tod_allvars_models.csv")
    n_vars = len(pd.read_csv(REF / "tod_allvars_variable_map.csv"))
    n_cities = int(allvars["fold_cities"].dropna().iloc[0]) + 2   # fitted cities plus Chicago and Madison, held out
    n_pass += int((allvars["verdict"] == "pass").sum())
    trait_line = {"title": "Why the response differs from place to place",
                  "text": (f"We tested {n_traits} local traits (home values, incomes, rents, lot sizes, existing density, distance to "
                           f"downtown and others) and all {len(pairs)} pairs of them, then {n_vars} census variables (housing, incomes, "
                           f"commuting, car ownership and more), with {n_tools} prediction methods including random and causal forests, "
                           f"predicting each of {n_cities} cities from the others. "
                           + ("None reliably predicts where upzoning added more homes" if n_pass == 0 else f"{n_pass} passed")
                           + ", so the scenarios stay wide (docs/tod/TRAITS_RESULTS.md, docs/tod/ALLVARS_RESULTS.md).")}
    _cl = pd.read_csv(REF / "tod_causal_lines.csv").set_index("line")
    cannot = [
        {"title": "Whether a required district does as well as a chosen one",
         "text": "The lines rest on 11 US places that chose to zone a district near some of their stops, often on land builders already wanted. A state mandate makes every city act, on land it may pick less well, so it may do less. Near Milwaukee's new streetcar, building rose by a similar amount with no rezoning, so part of the measured gain may come from new transit or booming neighborhoods rather than zoning."},
        {"title": "Whether a bigger district adds proportionally more",
         "text": "The places' districts averaged about 12% of the land within ¼ mile; the law asks for 15%. The central line does not scale it. Among the 11 places the effect fell as the district share grew, so scaling up (the upper line, 12,521) leans on the smallest districts."},
        {"title": "How much comes from the new lines themselves",
         "text": "Stops on new lines gained about 18 extra homes per 100 lot acres a year with no rezoning (about 5,300 homes in Wisconsin over five years). That belongs to current law, not the law. Compared only with stops on lines of a similar age, the central falls to about 6,930. "
                 f"Rezoned stops on new lines were already gaining faster before any reform, so the new-lines reading ({whole(_cl.loc['causal_upper_2x2', 'extra_homes_2027_2031']):,}) "
                 f"shrinks to about {whole(_cl.loc['whatif_2x2_trend_adjusted', 'extra_homes_2027_2031']):,} once that is taken out. Massachusetts' district law shows no rise in its first year, and in Los Angeles a bigger density bonus at the tier lines did not add building."},
        {"title": "Whether a citywide upzoning would do the same",
         "text": "These results describe districts, not citywide upzoning. For the five broad upzonings left out (Bellevue's BelRed, Honolulu, Los Angeles, San Diego, Chicago 2022), the average rule missed by a median 43 extra homes per 100 lot acres a year, the scaled rule by 240, and simply predicting zero by 11. At their boundaries, too, these broad upzonings show no jump."},
        trait_line,
        {"title": "Timing", "text": TIMING},
        {"title": "Homes that would have been built elsewhere in the city anyway",
         "text": ("The tool has no case in which the extra homes near stops are simply moved from elsewhere in the same city. "
                  "Whole-city permit counts could only detect a change of about 4% to 5% of a city's homes over five years, "
                  "so they cannot rule a small shift in or out. At district edges, the lots just outside showed no drop in "
                  "building (the bunching check), which is where a shift would show first.")},
        {"title": "Transit-oriented density alone versus with parking reform",
         "text": "The cases cannot separate the two. The parking reform has its own scenario in this tool."},
        {"title": "Rents, displacement and transit ridership", "text": "These are not modelled."},
        {"title": "Lot-by-lot predictions", "text": "The model works by place. Nothing here says what will be built on any one lot."},
    ]
    # Tornado: each what-if's statewide extra homes minus the central line (owner request, 3 November 2026).
    # Timing-only (ramp_new_york, ramp_year5_alt), where-homes-land and baseline-only rows leave the statewide addition unchanged.
    central = float(main.loc["typical", "addition_2027_2031"])
    la = ne[ne["group"] == "law_addition"].set_index(["sensitivity", "scenario"])["addition_2027_2031"]
    tornado = []
    for kind, items in TORNADO.items():
        for label, sens, sc in items:
            v = float(main.loc[sc, "addition_2027_2031"]) if sens == "main" else float(la.loc[(sens, sc)])
            tornado.append({"kind": kind, "id": f"{sens}:{sc}", "label": label, "extra": r(v, 1), "vs_central": r(v - central, 1)})
    return {"main_baseline": r(main.loc["typical", "baseline_near_stops_2027_2031"], 4), "groups": groups, "per_acre": per_acre,
            "tornado": {"central": r(central, 1), "rows": tornado},
            "scale": scale, "scale_benchmarks": {"observed_max": r(obsmax.value, 2), "observed_max_metro": s(obsmax.metro),
                                                 "observed_max_year": int(obsmax.year), "p95": r(p95.value, 2)},
            "madison_share": madison, "trace": trace, "cannot_tell": cannot}


# ---- why ----------------------------------------------------------------------------------------
CASE_NAMES = {
    "charlotte_tod_2019": "Charlotte, 2019 transit-oriented districts",
    "stpaul_green_line_2011": "Saint Paul, Green Line rezoning, 2011",
    "nyc_park_slope_fourth_ave_2003": "New York, Fourth Avenue (Park Slope), 2003",
    "nyc_downtown_brooklyn_2004": "New York, Downtown Brooklyn, 2004",
    "nyc_pooled_2003_2013": "New York, 17 rezonings pooled, 2003–2013",
    "philadelphia_2012_remapping": "Philadelphia, remapping under the 2012 code, 2013–2019",
    "raleigh_tod_2021": "Raleigh, 2021 transit overlay",
    "phoenix_walkable_urban_code_2015": "Phoenix, 2015 Walkable Urban Code",
    "chicago_tod_2013_2015": "Chicago, 2015 transit-served locations",
    "annarbor_tc1_2021": "Ann Arbor, 2021 transit corridor district",
}
ROLE_LABELS = {"fit": "Used to place homes", "context": "Background only", "heldout": "Held out to test the model"}


def city_checks() -> list[dict]:
    """Two checks of the scenarios against our own cities (NET_EFFECT_RESULTS.md, CONTROL_CITIES_RESULTS.md)."""
    net = pd.read_csv(REF / "tod_net_effect_by_case.csv")
    summed = set(net.loc[net["level"].str.startswith("city"), "city"])
    cities = net[net["level"].str.startswith("city") | ~net["city"].isin(summed)]
    weak = cities[cities["city"] == "Saint Paul"]
    rest = cities[cities["city"] != "Saint Paul"]
    ring_fell = int((net.loc[net["level"] == "case", "borrowing_high"] < 0).sum())
    lo, hi = rest["net_share_5yr_pct"].min(), rest["net_share_5yr_pct"].max()
    out = [{"title": "Our own cities' whole-city gains",
            "text": (f"In {len(cities)} US cities that upzoned land near transit, we measured the extra homes permitted over five years, "
                     f"net of any building pulled from elsewhere in the city, as a share of all the city's homes. It ranged from "
                     f"{lo:.2f}% ({rest.loc[rest['net_share_5yr_pct'].idxmin(), 'city']}) to {hi:.2f}% "
                     f"({rest.loc[rest['net_share_5yr_pct'].idxmax(), 'city']}); Saint Paul, with one year of data before its reform, "
                     f"was {weak["net_share_5yr_pct"].iloc[0]:.2f}%. "
                     + ("In no city did building fall on the land next to the upzoned area." if ring_fell == 0 else
                        f"Building fell next to the upzoned area in {ring_fell} cases.")
                     + " These whole-city shares are small because each reform covered a small slice of its city."),
            "doc": doc("docs/tod/NET_EFFECT_RESULTS.md", "Net-effect results")}]
    res, pooled = REF / "tod_control_cities_results.csv", REF / "tod_control_cities_pooled.csv"
    if res.exists() and pooled.exists():
        m = pd.read_csv(res)
        m = m[m["check"] == "main"]
        p = pd.read_csv(pooled).iloc[0]
        n_cities = int(p["cities"])
        out.append({"title": "Matched cities with no transit reform",
                    "text": (f"We also compared each reform city's total building with 10 similar US cities that made no such reform, "
                             f"over the same years ({n_cities} cities; New York and Philadelphia rezoned in many steps, so they could not be "
                             f"compared this way). Whole-city building swings so much from city to city that this comparison can only "
                             f"detect a change of about {m['smallest_detectable_5yr_pct'].min():.0f}% to "
                             f"{m['smallest_detectable_5yr_pct'].max():.0f}% of a city's homes over five years, far more than the "
                             f"reforms added. {int(p['cities_agreeing'])} of the {n_cities} cities' own measurements fall inside its likely range, "
                             f"but it is too noisy to narrow Wisconsin's range."),
                    "doc": doc("docs/tod/CONTROL_CITIES_RESULTS.md", "Control-city results")})
    return out


def build_why() -> dict:
    ce = pd.read_csv(REF / "tod_case_estimates.csv")
    # Permit-count rows (Raleigh, Phoenix, Ann Arbor; context only, CASE_ANALYSIS_PLAN section 7) count permits, not
    # homes, so they are kept off the homes-per-acre case table; the documentation reports them.
    if "measure" in ce.columns:
        ce = ce[~ce["measure"].fillna("").str.startswith("permits")]
    ce = ce[~ce["status"].fillna("").str.startswith(("context_permit_count", "not_measurable"))
            & ~ce["case"].str.contains("_permit_count")]
    cases = []
    for x in ce.itertuples():
        cases.append({"id": x.case, "name": CASE_NAMES.get(x.case, x.case.replace("_", " ")), "role": x.role,
                      "role_label": ROLE_LABELS.get(x.role, x.role),
                      "note": "too few years of permit data" if str(x.status).startswith("context_only") else "no permit data with unit counts" if str(x.status).startswith("no_data") else None,
                      "estimate": r(x.estimate_units_per_acre_yr, 3), "low": r(x.interval90_low, 3), "high": r(x.interval90_high, 3),
                      "dose_far": r(x.dose_added_far, 4), "per_far": r(x.effect_per_dose, 3), "per_far_low": r(x.effect_per_dose_low, 3),
                      "per_far_high": r(x.effect_per_dose_high, 3), "parking": s(x.parking_change), "mandate": s(x.mandate)})
    inv = pd.read_csv(REF / "tod_cases.csv")
    import re as _re
    used = {"charlotte_tod_2019": "Measured: used to place homes", "nyc_bloomberg_rezonings_2003_2013": "Measured: used to place homes",
            "nyc_park_slope_fourth_ave_2003": "Measured: used to place homes", "nyc_downtown_brooklyn_2004": "Measured: used to place homes",
            "philadelphia_2012_code": "Measured: used to place homes", "stpaul_green_line_2011": "Measured, background only (too few years before)",
            "chicago_tod_2013_2015": "Measured: kept aside to test the model", "madison_tod_overlay_2023": "Measured: the Wisconsin test",
            "annarbor_tc1_2021": "Kept aside to test the model (no usable permit data)", "auckland_aup_2016": "Former strong scenario (comparison)",
            "la_toc_2017": "Earlier little scenario (comparison)", "raleigh_new_bern_2024": "Left out: too new",
            "phoenix_walkable_urban_code_2015": "Background only (no usable permit data)"}

    def plain_use(case_id, use, mandate):
        if case_id in used:
            return used[case_id]
        u = use.lower()
        if u.startswith("exclude"):
            why_ = "too new" if "new" in u else "mostly design rules" if "design" in u else "an optional bonus" if "opt-in" in u else "not a usable case"
            return f"Left out: {why_}"
        if "mandate" in u or mandate == "yes":
            return "Background: required affordable homes"
        if "lead" in u or "upgrade" in u or "candidate" in u:
            return "Not measured: data not found yet"
        if "upper bound" in u or "strong-response" in u:
            return "Background: strong-market example"
        return "Background only"

    def year_of(x):
        m_ = _re.search(r"(19|20)\d\d", f"{x.effective_date} {x.adoption_date}")
        return m_.group(0) if m_ else None
    classification = [{"city": x.city, "year": year_of(x), "strength": x.policy_strength, "data": x.data_usability,
                       "parking": x.parking_minimums_changed, "mandate": x.affordability_mandate,
                       "use": plain_use(x.case_id, x.recommended_use, x.affordability_mandate)}
                      for x in inv.sort_values("rank").itertuples()]
    counts = inv.groupby("policy_strength").size().to_dict()
    res = pd.read_csv(REF / "tod_madison_test_results.csv").set_index("estimate")
    judged = res[res.index.str.startswith("judged")].iloc[0]
    mainr = res[res.index.str.startswith("main")].iloc[0]
    pred = pd.read_csv(REF / "tod_madison_test_predictions.csv")
    pa = pred[(pred["method"] == "A") & pred["variant"].str.startswith("main")].iloc[0]
    rby = pd.read_csv(REF / "tod_madison_test_rates_by_year.csv")
    u = rby[rby["areas"] == "uniform rule"]
    years = []
    for y in sorted(u["year"].unique()):
        row = {"year": int(y)}
        for area in ("treatment", "comparison"):
            z = u[(u["year"] == y) & (u["area"] == area)].iloc[0]
            row[area] = {"units": int(z.units), "rate": r(z.rate_per_acre, 3), "acres": r(z.eligible_acres, 1)}
            row["period"] = z.period
        years.append(row)
    ramp = res[res.index.str.startswith("ramp check")]
    madison = {
        "prediction": {"value": r(pa.prediction, 3), "low": r(pa.interval90_low, 3), "high": r(pa.interval90_high, 3)},
        "measured": {"value": r(judged.value, 3), "low": r(judged.interval90_low, 3), "high": r(judged.interval90_high, 3)},
        "main": {"value": r(mainr.value, 3), "low": r(mainr.interval90_low, 3), "high": r(mainr.interval90_high, 3)},
        "per_far": {"measured": r(judged.per_added_far, 3), "low": r(judged.per_added_far_low, 3), "high": r(judged.per_added_far_high, 3),
                    "predicted": r(res.loc["info: r_method_a", "value"], 3)},
        "confirmed": bool(judged.interval90_low <= pa.prediction <= judged.interval90_high),
        "years": years,
        "ramp": [{"label": i.replace("ramp check: after = ", ""), "value": r(v, 3)} for i, v in ramp["value"].items()],
    }
    od = pd.read_csv(REF / "tod_optiond_line.csv").set_index("line")
    plan = DOC + "docs/tod/OPTION_D_PLAN.md"
    cl = pd.read_csv(REF / "tod_causal_lines.csv").set_index("line")
    cf = DOC + "docs/tod/CAUSAL_FRAMEWORK_PLAN.md"
    lo_, up_ = cl.loc["causal_lower_edge"], cl.loc["upper_average_scaled_15"]
    sources = [
        {"scenario": "little", "study": "Edge test at district boundaries, 5 places (our own lot data)",
         "citation": "docs/tod/CAUSAL_FRAMEWORK_PLAN.md (Test 2, T3) and reference/tod_causal_edge_test.csv", "url": cf,
         "finding": f"Lots just inside a district line against lots just outside (within 300 feet), after minus before, in the 5 places whose two sides were alike before the rezoning: {lo_.effect_per_100_acres:.1f} extra new homes per 100 acres of district lots a year. × 15% of Wisconsin's {od.loc['optiond_average', 'wi_acres_quarter']:,.0f} lot acres × 5 years × {od.loc['optiond_average', 'statewide_scale']:.3f}: {lo_.extra_homes_2027_2031:,.0f} extra homes (90% {lo_.range_low:,.0f} to {lo_.range_high:,.0f}). The rezoned lots' own gain only; fake lines show about zero.",
         "status": "calculated"},
        {"scenario": "typical", "study": "Average of 11 district places, across about 12% of lots within ¼ mile (our own lot data)",
         "citation": "docs/tod/OPTION_D_PLAN.md and reference/tod_optiond_line.csv", "url": plan,
         "finding": f"Within ¼ mile of reform stops, against similar stops without reform: on average {od.loc['optiond_average', 'mean_effect_per_100_acres']:.1f} extra new homes per 100 lot acres a year. Times Wisconsin's {od.loc['optiond_average', 'wi_acres_quarter']:,.0f} lot acres within ¼ mile of rail and rapid stops in Milwaukee and Madison, 5 years and the statewide scale (×{od.loc['optiond_average', 'statewide_scale']:.3f}, all ¼-mile land ÷ the two cities'): {od.loc['optiond_average', 'extra_homes_2027_2031']:,.0f} extra homes (range {od.loc['optiond_average', 'range_low']:,.0f} to {od.loc['optiond_average', 'range_high']:,.0f}, each place left out).",
         "status": "calculated"},
        {"scenario": "strong", "study": "Average of the same 11 district places, scaled up to a 15% district (our own lot data)",
         "citation": "docs/tod/OPTION_D_PLAN.md and reference/tod_optiond_line.csv (row optiond_average_scaled_15)", "url": plan,
         "finding": f"The 11 places' pooled effect per share of land zoned, × 15%: {up_.effect_per_100_acres:.1f} extra new homes per 100 lot acres a year within ¼ mile. × Wisconsin's ¼-mile lot acres, 5 years and the statewide scale: {up_.extra_homes_2027_2031:,.0f} extra homes (range {up_.range_low:,.0f} to {up_.range_high:,.0f}, each place left out). Bigger districts gained less per acre, so scaling up leans on the smallest ones.",
         "status": "calculated"},
    ]
    return {"cases": cases, "classification": classification, "strength_counts": {k: int(v) for k, v in counts.items()},
            "madison": madison, "sources": sources, "city_checks": city_checks(),
            "docs": [doc("docs/tod/CAUSAL_FRAMEWORK_PLAN.md", "Causal framework (lower and upper lines)"), doc("docs/tod/OPTION_D_PLAN.md", "Option D plan and log"), doc("docs/tod/GATE3_PACKET.md", "Gate 3 packet"), doc("docs/tod/MODEL.md", "Model"),
                     doc("docs/tod/CASE_RESULTS.md", "Comparison cases"), doc("docs/tod/MADISON_TEST_RESULTS.md", "Madison test"),
                     doc("docs/tod/research/NET_EFFECT_SOURCES.md", "Source check of the three studies")]}


# ---- pilots -------------------------------------------------------------------------------------
def corridor(agency_counties: list[str], areas: dict, sw: dict) -> dict:
    """Rail and rapid station areas in the given counties: their land, and their share of each place's addition.

    Option D (AQ-071): the district is spread at random over the land within 1/4 mile of rail and rapid stops, and each
    place's homes are placed by its lot acres there, so all of a place's extra homes are within 1/4 mile of its rail and
    rapid stops: share of the place = 1 wherever the place has such land. District acres = 15% of those lot acres."""
    sa = pd.read_csv(REF / "tod_station_areas.csv")
    m = sa[(sa["in_main"] == 1) & sa["county"].isin(agency_counties)]
    mt = {x["name"]: x for x in areas["munis"]}
    places = []
    add = {sc: [0.0] * 5 for sc in SCEN}
    for city, g in m.groupby("city"):
        if city not in mt:
            continue
        rap = g[g["band"] == "rapid_quarter"]
        if rap.empty or float(rap["acres"].sum()) <= 0:
            continue
        share = 1.0
        mu = mt[city]
        for sc in SCEN:
            for i in range(5):
                add[sc][i] += mu["add_years"][sc][i] * share
        acres = float(rap["acres"].sum())
        places.append({"name": city, "coded": bool(g["zoning_coded"].iloc[0]), "acres": r(acres, 0),
                       "district_acres": r(acres * DISTRICT["share"], 0),
                       "existing_homes": r(rap["existing_homes"].sum(), 0), "share_of_place": r(share, 4),
                       "add_typical": r(mu["add"]["typical"] * share, 4)})
    places.sort(key=lambda p: -p["acres"])
    return {"places": places, "add": {sc: r(sum(v), 4) for sc, v in add.items()}, "add_years": {sc: [r(v, 4) for v in vs] for sc, vs in add.items()},
            "acres": r(sum(p["acres"] for p in places), 0), "district_acres": r(sum(p["district_acres"] for p in places), 0),
            "existing_homes": r(sum(p["existing_homes"] for p in places), 0)}


def build_pilots(areas: dict, sw: dict) -> list:
    stops = pd.read_csv(REF / "tod_stops.csv")
    mt = {x["name"]: x for x in areas["munis"]}
    near = pd.read_csv(REF / "tod_near_stop_homes_by_muni.csv")
    nid = near.set_index("area_id")
    out = []
    mke = mt["Milwaukee city"]
    out.append({
        "slug": "milwaukee-connect-1", "title": "Milwaukee: the CONNECT 1 corridor", "view": "milwaukee", "city": "Milwaukee city",
        "line": "CONNECT 1 bus rapid transit, with The Hop streetcar downtown",
        "intro": "CONNECT 1 is Milwaukee County's bus rapid transit line, running east–west from downtown Milwaukee along Wisconsin Avenue to the Milwaukee Regional Medical Center in Wauwatosa. The station-area figures below cover the land near every rail and rapid transit station in Milwaukee County, which is CONNECT 1 plus The Hop streetcar downtown; the data do not split the two.",
        "stops": {"CONNECT 1 stops": int(stops[(stops.agency == "Milwaukee County") & (stops.flag_a_rapid == 1)].shape[0]),
                  "The Hop streetcar stops": int(stops[(stops.agency == "City of Milwaukee") & (stops.flag_a_rapid == 1)].shape[0])},
        "city_homes": int(nid.loc[mke["id"], "homes_2020"]), "city_homes_near": mke["homes_near"],
        "city_baseline": mke["baseline"], "city_add": mke["add"], "city_add_years": mke["add_years"],
        "corridor": corridor(["Milwaukee County"], areas, sw),
        "method": "The district is spread at random over the land within ¼ mile of rail and rapid stops, so all of each place's extra homes fall there. Milwaukee's figure covers CONNECT 1 and The Hop streetcar together, because the land data do not separate the two lines.",
        "zoning_note": "Existing zoning near stops does not change the district's size: the law asks for 15% of the land within ¼ mile, whatever is allowed there today.",
    })
    mad = mt["Madison city"]
    out.append({
        "slug": "madison-route-a", "title": "Madison: the Rapid Route A corridor", "view": "madison", "city": "Madison city",
        "line": "Madison Metro Rapid Route A (bus rapid transit, opened 22 September 2024)",
        "intro": "Rapid Route A is Madison's first bus rapid transit line, running east–west through downtown and the isthmus. Madison already has a transit-oriented development overlay (2023) along much of the route.",
        "stops": {"Rapid Route A stops": int(stops[(stops.agency == "City of Madison") & (stops.flag_a_rapid == 1)].shape[0])},
        "city_homes": int(nid.loc[mad["id"], "homes_2020"]), "city_homes_near": mad["homes_near"],
        "city_baseline": mad["baseline"], "city_add": mad["add"], "city_add_years": mad["add_years"],
        "corridor": corridor(["Dane County"], areas, sw),
        "method": "The district is spread at random over the land within ¼ mile of rail and rapid stops (in Dane County, Rapid Route A's stations), so all of each place's extra homes fall there.",
        "zoning_note": "Madison's 2023 transit-oriented development overlay already allows more along much of the route. The model does not credit it: the measured effect is for a new district, so the line may overstate Madison's gain.",
    })
    hb = pd.read_csv(REF / "housing_baseline_by_area.csv")
    ec = hb[hb["name"] == "Eau Claire city"]
    nn = near[near["name"] == "Eau Claire city"][["homes_2020", "homes_near_main", "homes_near_high"]].sum()
    ecs = stops[stops.agency == "City of Eau Claire"]
    sa = pd.read_csv(REF / "tod_station_areas.csv")
    eca = sa[sa["city"] == "Eau Claire city"]
    out.append({
        "slug": "eau-claire", "title": "Eau Claire: does the law reach a mid-size bus city?", "view": "eau-claire", "city": "Eau Claire city",
        "line": "Eau Claire Transit (no 15-minute routes; Routes 9 and 19 run every 20 minutes)",
        "intro": "Eau Claire is the check of whether the law transfers to Wisconsin's mid-size cities. The answer is no: Eau Claire has no rail or rapid transit stop, so it need not zone a district and the law adds nothing there.",
        "stops": {"stops on 20-minute bus routes": int(((ecs.flag_c_20min == 1) & (ecs.flag_b_15min == 0)).sum()),
                  "stops on 15-minute bus routes or rapid transit": int(((ecs.flag_b_15min == 1) | (ecs.flag_a_rapid == 1)).sum())},
        "city_homes": int(nn["homes_2020"]), "city_homes_near": int(nn["homes_near_main"]), "homes_near_high": int(nn["homes_near_high"]),
        "city_baseline_all": r(ec["five_year_central"].sum(), 4),
        "high_case_acres": r(eca[eca["in_high"] == 1]["acres"].sum(), 0),
        "city_add": {sc: 0.0 for sc in SCEN},
        "reason": "The law's district is tied to rail and rapid transit stops, and Eau Claire has none. Its two busiest bus routes, 9 and 19, run every 20 minutes.",
    })
    return out

# ---- today: homes per acre near rail and rapid stops (2020 snapshot) ----------------------------
# Wisconsin's systems in the order shown, with the operating agencies of tod_stops.csv behind each (as
# scripts/build_tod_today_density.py groups them).
TODAY_SYSTEMS = [("Milwaukee (BRT and streetcar)", "Milwaukee", "CONNECT 1 bus rapid transit and The Hop streetcar", ["Milwaukee County", "City of Milwaukee"]),
                 ("Madison (BRT)", "Madison", "Rapid Route A bus rapid transit", ["City of Madison"]),
                 ("Kenosha (streetcar)", "Kenosha", "Kenosha streetcar", ["City of Kenosha"])]
# The older reforms: case id -> plain place name, the area the reform covered, the year it was adopted, and whether it
# was an industrial rezone. BelRed (a former light-industrial district whose stops sat on industrial land) stays in the
# CSV but is left off the today screen (owner 2026-11-02): the comparison is the five non-industrial reforms.
TODAY_REFORMS = [("austin_2009", "Austin", None, 2009, False),
                 ("bellevue_belred_2009", "Bellevue", "BelRed", 2009, True),
                 ("slc_2010", "Salt Lake City", None, 2010, False),
                 ("stpaul_2011", "Saint Paul", None, 2011, False),
                 ("seattle_othello_2012", "Seattle", "Othello", 2012, False),
                 ("seattle_mount_baker_2014", "Seattle", "Mount Baker", 2014, False)]
TODAY_POOLED = "five older non-industrial reforms (pooled)"
TODAY_BANDS = (("quarter_mile", "quarter"), ("half_mile", "half"), ("ring_half_to_one_mile", "ring"))


def build_today() -> dict:
    d = pd.read_csv(REF / "tod_today_density.csv")

    def bands(rows: pd.DataFrame) -> dict:
        if len(rows) != len(TODAY_BANDS):
            raise SystemExit(f"today: expected {len(TODAY_BANDS)} bands, got {len(rows)}")
        out = {}
        for b, key in TODAY_BANDS:
            x = rows[rows["band"] == b].iloc[0]
            out[key] = {"stops": int(x.n_stops), "homes": int(x.homes_2020), "acres": r(x.land_acres, 1),
                        "homes_per_acre": r(x.homes_2020 / x.land_acres, 3)}
        # times as dense near the stops as in the ½–1 mile ring around the same stops
        ring = out["ring"]["homes"] / out["ring"]["acres"]
        out["vs_ring"] = {k: r(out[k]["homes"] / out[k]["acres"] / ring, 3) for k in ("quarter", "half")}
        return out

    wi = d[d["group"] == "wisconsin"]
    rf = d[d["group"] == "reform_stops"]
    state = bands(wi[wi["place"] == "Wisconsin (all)"])
    pooled = bands(rf[rf["place"] == TODAY_POOLED])
    stops = pd.read_csv(REF / "tod_stops.csv")
    rapid = stops[stops["flag_a_rapid"].astype(bool)]
    systems = [{"name": short, "label": label, "lines": lines, "agencies": ags,
                "stops_in_stop_file": int(rapid["agency"].isin(ags).sum()), **bands(wi[wi["place"] == label])}
               for label, short, lines, ags in TODAY_SYSTEMS]
    shown = [x for x in TODAY_REFORMS if not x[4]]
    reforms = [{"id": cid, "place": place, "area": area, "year": year, **bands(rf[rf["place"] == cid])}
               for cid, place, area, year, _ in shown]
    # Context: Wisconsin's land near stops at the five places' pooled density (homes per acre times Wisconsin's acres)
    context = {}
    for key in ("half", "quarter"):
        w, p = state[key], pooled[key]
        diff = p["homes_per_acre"] - w["homes_per_acre"]
        extra = (p["homes"] / p["acres"] - w["homes"] / w["acres"]) * w["acres"]
        context[key] = {"wisconsin": w["homes_per_acre"], "five_places": p["homes_per_acre"], "difference": r(diff, 3),
                        "acres": w["acres"], "homes": w["homes"], "extra_homes": r(extra, 1),
                        "extra_homes_rounded": int(round(extra, -2)), "extra_share": r(extra / w["homes"], 4)}
    return {
        "year": 2020,
        "stops_total": int(len(rapid)),
        "state": state, "systems": systems, "five_places": pooled, "reforms": reforms, "context": context,
        "reform_years": [min(x[3] for x in shown), max(x[3] for x in shown)],
        "stops_counted_twice": sum(x["half"]["stops"] for x in reforms) - pooled["half"]["stops"],
        "left_out": [{"id": cid, "place": place, "area": area, "year": year,
                      "reason": "a former light-industrial district; its stops sat on industrial land"}
                     for cid, place, area, year, ind in TODAY_REFORMS if ind],
        "ring_caveats": [
            "Ring: ½ to 1 mile from the stops.",
            "The same city's nearby neighborhoods.",
            "So city size and market mostly cancel out.",
            "Ring is not cut at city limits.",
        ],
        "source": "Census 2020 blocks (housing units and land area); a block counts if its centre point is within ¼ or ½ mile of a stop, or, for the ring, beyond ½ mile of every stop and within 1 mile of one. Land excludes water.",
        "caveats": [
            "Density reflects city size, age and market, not only zoning.",
            "A 2020 snapshot, not a reform effect.",
            "Industrial rezones left out (Bellevue's BelRed).",
        ],
    }


def validate_today(t: dict, check) -> None:
    st = t["state"]
    check("today: systems' stops add up to Wisconsin's rail and rapid stops",
          sum(x["half"]["stops"] for x in t["systems"]) == st["half"]["stops"] == t["stops_total"], f"{st['half']['stops']} stops")
    check("today: each system's stops match the stop file",
          all(x["half"]["stops"] == x["quarter"]["stops"] == x["ring"]["stops"] == x["stops_in_stop_file"] for x in t["systems"]),
          "flag_a_rapid by agency")
    for key in ("quarter", "half"):
        check(f"today: systems' homes and land add up to Wisconsin ({key} mile)",
              sum(x[key]["homes"] for x in t["systems"]) == st[key]["homes"]
              and abs(sum(x[key]["acres"] for x in t["systems"]) - st[key]["acres"]) < 0.5, f"{st[key]['homes']:,} homes")
    # the systems are far apart, so their rings do not overlap and add up too
    check("today: systems' ½–1 mile rings add up to Wisconsin's ring",
          sum(x["ring"]["homes"] for x in t["systems"]) == st["ring"]["homes"]
          and abs(sum(x["ring"]["acres"] for x in t["systems"]) - st["ring"]["acres"]) < 0.5, f"{st['ring']['homes']:,} homes")
    rows = [st, t["five_places"], *t["systems"], *t["reforms"]]
    check("today: homes per acre = homes / land acres (¼, ½ and ½–1 mile)",
          all(abs(x[k]["homes_per_acre"] - x[k]["homes"] / x[k]["acres"]) < 0.001 for x in rows for k in ("quarter", "half", "ring")), "every row")
    check("today: times as dense = near homes per acre ÷ ring homes per acre",
          all(abs(x["vs_ring"][k] - x[k]["homes_per_acre"] / x["ring"]["homes_per_acre"]) < 0.002 for x in rows for k in ("quarter", "half")),
          "every row, both bands")
    d = pd.read_csv(REF / "tod_today_density.csv").set_index(["place", "band"])
    check("today: ring homes, land and homes per acre match the density file",
          all(x["ring"]["homes"] == int(d.loc[(pl, "ring_half_to_one_mile"), "homes_2020"])
              and abs(x["ring"]["homes_per_acre"] - d.loc[(pl, "ring_half_to_one_mile"), "homes_per_acre"]) <= 0.006
              for pl, x in [("Wisconsin (all)", st), (TODAY_POOLED, t["five_places"])] + [(x["label"], x) for x in t["systems"]]
              + [(x["id"], x) for x in t["reforms"]]), "Wisconsin, systems, five places, pooled")
    check("today: five non-industrial reforms shown, adopted 2009-2014, BelRed left out",
          len(t["reforms"]) == 5 and t["reform_years"] == [2009, 2014] and all(x["id"] != "bellevue_belred_2009" for x in t["reforms"])
          and [x["id"] for x in t["left_out"]] == ["bellevue_belred_2009"], "Austin to Mount Baker")
    n_sum = sum(x["half"]["stops"] for x in t["reforms"])
    check("today: five places together count each stop once",
          t["five_places"]["half"]["stops"] == n_sum - t["stops_counted_twice"] and 0 <= t["stops_counted_twice"] <= 1
          and t["five_places"]["half"]["stops"] == int(d.loc[(TODAY_POOLED, "half_mile"), "n_stops"]),
          f"{t['five_places']['half']['stops']} stops ({n_sum} listed)")
    c = t["context"]["half"]
    check("today: context recomputes (½ mile, five places)", abs(c["extra_homes"] - c["difference"] * c["acres"]) < 0.01 * c["acres"] + 1
          and c["five_places"] == t["five_places"]["half"]["homes_per_acre"], f"{c['extra_homes']:,.0f} homes")


# ---- validation ---------------------------------------------------------------------------------
def validate(sw: dict, areas: dict, pilots: list, today: dict) -> dict:
    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
    for sc in sw["scenarios"]:
        tot = sum(m["add"][sc["id"]] for m in areas["munis"])
        check(f"{sc['id']}: places add up to the state", abs(tot - sc["additional_total"]) < 1, f"{tot:,.1f} vs {sc['additional_total']:,.1f}")
        check(f"{sc['id']}: years add up to the five-year total", abs(sum(sc["by_year"]) - sc["additional_total"]) < 1, "2027–2031")
        for lvl in ("counties", "assembly", "senate"):
            t = sum(o["add"][sc["id"]] for o in areas[lvl]["rows"])
            check(f"{sc['id']}: {lvl} add up to the state", abs(t - sc["additional_total"]) < 1, f"{t:,.1f}")
    check("baseline: places add up to the state", abs(sum(m["baseline"] for m in areas["munis"]) - sw["baseline"]["total"]) < 1,
          f"{sw['baseline']['total']:,.1f}")
    lines = {"little": ("tod_causal_lines.csv", "causal_lower_edge"), "typical": ("tod_optiond_line.csv", "optiond_average"),
             "strong": ("tod_causal_lines.csv", "upper_average_scaled_15")}
    for sid, (f, line) in lines.items():
        od = pd.read_csv(REF / f).set_index("line")
        sc = next(x for x in sw["scenarios"] if x["id"] == sid)
        check(f"{sid}: total and range match reference/{f} ({line}, AQ-072/AQ-075)",
              abs(sc["additional_total"] - od.loc[line, "extra_homes_2027_2031"]) < 0.1
              and abs(sc["range_low"] - od.loc[line, "range_low"]) < 0.1 and abs(sc["range_high"] - od.loc[line, "range_high"]) < 0.1,
              f"{sc['additional_total']:,.1f} ({sc['range_low']:,.1f} to {sc['range_high']:,.1f})")
    ck = pd.read_csv(REF / "tod_model_checks.csv")
    ck = ck[(ck["check"] == "scale") & (ck["sizing"] == "net_effect") & ck["scenario"].isin(SCEN)]
    check("no line passes the highest peer-metro year (compare-screen note)", not (ck["exceeds_observed_max"] == True).any(), "scale check")  # noqa: E712
    check("record-year note matches the scale check", sum(len(x["years"]) for x in sw["record_years"]) == int((ck["exceeds_own_max"] == True).sum()), "scenario-years")  # noqa: E712
    check("no addition below zero", all(v >= 0 for m in areas["munis"] for v in m["add"].values()), "every place and scenario")
    check("no median line with fewer than 4 comparable cases (AQ-054)", not sw["median_line"]["shown"] and "reference_line" not in sw,
          f"{sw['median_line']['n_studies']} studies")
    allb = all_housing_baseline_by_area()
    check("all-housing baseline: places add up to the state (AQ-054)", abs(allb.sum() - sw["state_baseline_total"]) < 1,
          f"{allb.sum():,.1f} vs {sw['state_baseline_total']:,.1f}")
    for lvl in ("counties", "assembly", "senate"):
        tot = areas[lvl]["all_baseline_total"] + areas["all_baseline_unallocated"]
        check(f"all-housing baseline: {lvl} plus the unallocated row add up to the state", abs(tot - sw["state_baseline_total"]) < 1,
              f"{areas[lvl]['all_baseline_total']:,.1f} + {areas['all_baseline_unallocated']:,.1f}")
    for sc in sw["scenarios"]:
        check(f"{sc['id']}: shared units recompute (AQ-054)",
              abs(sc["per_year"] * len(YEARS) - sc["additional_total"]) < 0.01
              and abs(sc["share_of_state_baseline"] * sw["state_baseline_total"] - sc["additional_total"]) < 0.5
              and abs(sc["share_of_acs_homes"] * sw["acs_homes"] - sc["additional_total"]) < 2, "per year, baseline share, ACS share")
    se = pd.read_csv(REF / "tod_model_sensitivities.csv")
    mm = se[(se["sizing"] == "net_effect") & (se["group"] == "main") & (se["scenario"] == "typical")].iloc[0]
    met = {m["id"]: m for m in areas["metros"]}
    check("Milwaukee metro matches the model", abs(met["milwaukee"]["add"]["typical"] - mm.milwaukee_metro_2027_2031) < 1, f"{mm.milwaukee_metro_2027_2031:,.1f}")
    check("Madison metro matches the model", abs(met["madison"]["add"]["typical"] - mm.madison_metro_2027_2031) < 1, f"{mm.madison_metro_2027_2031:,.1f}")
    for p in pilots[:2]:
        c = p["corridor"]
        check(f"{p['slug']}: corridor addition within its places' additions", all(0 <= x["share_of_place"] <= 1 for x in c["places"]), "shares between 0 and 1")
        check(f"{p['slug']}: district acres = 15% of the corridor's ¼-mile acres", abs(c["district_acres"] - 0.15 * c["acres"]) <= len(c["places"]), f"{c['district_acres']:,.0f} of {c['acres']:,.0f}")
    check("Eau Claire has no homes near main-case stops", pilots[2]["city_homes_near"] == 0, "no 15-minute routes")
    validate_today(today, check)
    rg = sw["range90"]
    wr = pd.read_csv(REF / "tod_coverage_test.csv").set_index("measure").loc["widened Wisconsin 90% range"]
    check("90% range ends equal the coverage test's widened range (spec)", abs(rg["low"] - wr["lo90"]) < 0.5 and abs(rg["high"] - wr["hi90"]) < 0.5,
          f"{rg['low']:,.1f} to {rg['high']:,.1f}")
    check("90% range: yearly bands add up to the ends (shares are fixed)", abs(sum(y["low"] for y in rg["years"]) - rg["low"]) < 1
          and abs(sum(y["high"] for y in rg["years"]) - rg["high"]) < 1, "2027–2031")
    byid = {x["id"]: x["additional_total"] for x in sw["scenarios"]}
    sl = {x["id"]: x["value"] for x in sw["side_lines"]}
    check("side lines equal the former scenario totals", abs(sl["average"] - byid["typical"]) < 0.1 and abs(sl["edge"] - byid["little"]) < 0.1
          and abs(sl["scaled15"] - byid["strong"]) < 0.1, "10,028 / 3,958 / 12,521")
    return {"passed": sum(c["passed"] for c in checks), "failed": sum(not c["passed"] for c in checks), "checks": checks}


def main():
    hashes = [{"path": GEO_MUNIS_LISTED if p == GEO_MUNIS else p, "sha256": sha256(ROOT / p)} for p in INPUTS]
    run_id = "tod-" + hashlib.sha256("".join(h["sha256"] for h in hashes).encode()).hexdigest()[:10]
    out = OUT_ROOT / run_id
    if OUT_ROOT.exists():
        for old in OUT_ROOT.iterdir():
            if old.is_dir() and old.name != run_id:
                shutil.rmtree(old)
    out.mkdir(parents=True, exist_ok=True)
    sw = build_statewide()
    sw["range90"], sw["side_lines"] = build_range90(sw)
    areas = build_areas()
    pilots = build_pilots(areas, sw)
    today = build_today()
    val = validate(sw, areas, pilots, today)
    manifest = {
        "schema_version": 1, "run_id": run_id, "scenario_id": "tod", "title": "Wisconsin transit-oriented density law",
        "outcome": {"short": "Extra homes in issued building permits near major transit stops, compared with current law, Wisconsin, 2027–2031. Not completed homes.",
                    "long": "Housing units authorized by building permits, counted at permit issuance, all building sizes, in station areas: within ½ mile of rail and rapid transit stations and ¼ mile of bus routes running every 15 minutes. The law's addition is the number of extra homes permitted compared with current law.",
                    "rate_units": "extra homes permitted per 1,000 existing homes in the station areas", "count_units": "homes (housing units) in issued permits"},
        "dates": {"last_observed_year": 2025, "forecast_years": YEARS, "effective": "Stylized statewide law in effect 1 January 2027"},
        "vintages": [{"what": "National Transit Map (stops and routes)", "vintage": "compiled 23 September 2026"},
                     {"what": "Agency schedule files (frequencies)", "vintage": "2025–2026 service days"},
                     {"what": "Census 2020 homes by block (station areas)", "vintage": "2020"},
                     {"what": "Census 2020 homes and land by block (homes per acre near rail and rapid stops, here and in five older non-industrial reform places)", "vintage": "2020"},
                     {"what": "Wisconsin's total homes for cross-reform shares (ACS B25002)", "vintage": "ACS 2020–2024 five-year"},
                     {"what": "Census Building Permits Survey (current-law forecast)", "vintage": "2015–2025 annual"},
                     {"what": "Milwaukee and Madison parcels and zoning", "vintage": "2025–2026"}],
        "validation": val, "repo_url": REPO_URL, "inputs": hashes,
        "files": ["statewide.json", "areas.json", "map.json", "howsure.json", "why.json", "pilots.json", "additions_by_area.json", "today.json"],
    }
    files = {"manifest.json": manifest, "statewide.json": sw, "areas.json": areas, "map.json": build_map(areas),
             "howsure.json": build_howsure(sw, areas), "why.json": build_why(), "pilots.json": pilots,
             "additions_by_area.json": build_additions(), "today.json": today}
    for name, obj in files.items():
        (out / name).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n")
    (OUT_ROOT / "latest.json").write_text(json.dumps({"run_id": run_id}) + "\n")
    size = sum(p.stat().st_size for p in out.iterdir())
    print(run_id, f"validation {val['passed']} passed, {val['failed']} failed; {size / 1e6:.2f} MB")
    for c in val["checks"]:
        if not c["passed"]:
            print("FAILED", c)


if __name__ == "__main__":
    main()
