"""Export the parking scenario as a static JSON bundle for the tool (Gate 4).

The browser runs no model: every number it shows comes from this bundle, which is built
only from committed reference files (option A, AQ-046 and AQ-048):

- reference/housing_baseline_statewide_by_year.csv, _by_area.csv, _history.csv, _sensitivity_published.csv
- reference/parking_model_*.csv, parking_wi_benchmark_places.csv
- reference/parking_comparison_effects.csv, _estimates.csv, _robustness.csv, _event_path.csv, _models.csv
- reference/parking_repeal_checks.csv, parking_reform_taxonomy.csv
- reference/adu_model_district_crosswalk.csv (district names come from the ids)

Output: ui/public/scenarios/parking/runs/<run_id>/*.json and latest.json. The run id hashes the
input files, so the same inputs give the same bundle byte for byte.

Run: uv run python scripts/build_parking_bundle.py
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
OUT_ROOT = ROOT / "ui" / "public" / "scenarios" / "parking" / "runs"
REPO_URL = "https://github.com/mroconnell/housing-challenge-starter-missingmiddleware"
DOC = REPO_URL + "/blob/main/"
YEARS = [2027, 2028, 2029, 2030, 2031]
PILOTS = {"milwaukee": "muni:5507953000", "west-allis": "muni:5507985300", "eau-claire": "muni:5503522300"}

INPUTS = [
    "scripts/build_parking_bundle.py",
    "reference/housing_baseline_statewide_by_year.csv", "reference/housing_baseline_by_area.csv",
    "reference/housing_baseline_history.csv", "reference/housing_baseline_sensitivity_published.csv",
    "reference/housing_baseline_band.csv",
    "reference/parking_model_by_area.csv", "reference/parking_model_statewide_by_year.csv",
    "reference/parking_model_by_county.csv", "reference/parking_model_by_assembly_district.csv",
    "reference/parking_model_by_senate_district.csv", "reference/parking_model_sensitivities.csv",
    "reference/parking_wi_benchmark_places.csv",
    "reference/parking_comparison_effects.csv", "reference/parking_comparison_estimates.csv",
    "reference/parking_comparison_robustness.csv", "reference/parking_comparison_event_path.csv",
    "reference/parking_comparison_models.csv", "reference/parking_repeal_checks.csv",
    "reference/parking_reform_taxonomy.csv", "reference/tod_near_stop_homes_by_muni.csv",
    "reference/tod_ab2097_results.csv", "reference/parking_traits_results.csv",
    "reference/parking_expanded_effects.csv", "reference/parking_expanded_estimates.csv", "reference/parking_expanded_tools.csv",
    "reference/parking_repeal_checks_expanded.csv", "reference/parking_placebo_summary.csv", "reference/parking_placebo_full_summary.csv", "reference/parking_partial_checks.csv",
]
BASELINE_VERSION = "all-housing baseline v2"


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


def s(v):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else str(v)


def doc(path: str, label: str) -> dict:
    return {"label": label, "url": DOC + path}


def expanded_included() -> pd.DataFrame:
    e = pd.read_csv(REF / "parking_expanded_effects.csv")
    return e[(e["status"] == "included") & (e["outcome"] == "all")]


def median_effect() -> float:
    return float(expanded_included()["effect"].median())


def ref_line() -> dict:
    """Median of real cases, applied to Wisconsin (AQ-054): the median repeal place's effect (floored at
    zero, since a repeal is not modelled as subtracting) times Wisconsin's eligible homes."""
    med = median_effect()
    homes = float(pd.read_csv(REF / "parking_model_by_area.csv")["eligible_homes"].sum())
    per_year = max(med, 0.0) * homes / 1000
    return {"label": "Median of real cases", "rate_per_1000_homes": r(med), "per_year": r(per_year, 1),
            "value": whole(per_year * len(YEARS)),
            "info": f"Median of real cases, applied to Wisconsin: the median of the 76 repeal places changed by {med:+.2f} permits per 1,000 existing homes per year against its comparison places. Applied to Wisconsin's {homes:,.0f} homes outside places already at the benchmark, " + (f"that is about {whole(per_year):,} extra permits a year, {whole(per_year * len(YEARS)):,} over 2027–2031: between the two cases." if med > 0 else "the median is below zero, so the line sits at 0, the same as the central case (a repeal is not modelled as reducing permits).")}


def build_statewide() -> dict:
    b = pd.read_csv(REF / "housing_baseline_statewide_by_year.csv")
    m = pd.read_csv(REF / "parking_model_statewide_by_year.csv").set_index("year")
    obs = b[(b["kind"] == "observed_adjusted_for_milwaukee") & (b["structure_type"] == "all")].set_index("year")["central"]
    pub = b[(b["kind"] == "observed_published_state_total") & (b["structure_type"] == "all")].set_index("year")["central"]
    proj = b[b["kind"].isin(["projected", "projected_bridge_year"]) & (b["structure_type"] == "all")].set_index("year")
    by_type = b[b["kind"].isin(["projected"]) & b["year"].isin(YEARS) & (b["structure_type"] != "all")] \
        .groupby("structure_type")[["low", "central", "high"]].sum()
    years = []
    for y in range(2015, 2032):
        row = {"year": y}
        if y in obs.index:
            row.update(observed=r(obs[y], 0), observed_published=r(pub[y], 0))
        if y in proj.index:
            row.update(baseline_low=r(proj.loc[y, "low"], 0), baseline=r(proj.loc[y, "central"], 0),
                       baseline_high=r(proj.loc[y, "high"], 0), bridge=bool(y == 2026))
        if y in YEARS:
            row.update(add_central=0.0, add_upper=r(m.loc[y, "addition_upper"], 0))
        years.append(row)
    base5 = whole(proj.loc[YEARS, "central"].sum())
    up5 = whole(m.loc[YEARS, "addition_upper"].sum())
    rate = float(m["upper_rate_per_1000_homes"].iloc[0])
    pubsens = pd.read_csv(REF / "housing_baseline_sensitivity_published.csv").set_index("structure_type")
    return {
        "years": years,
        "baseline_total": base5, "baseline_low_total": r(proj.loc[YEARS, "low"].sum(), 0),
        "baseline_high_total": r(proj.loc[YEARS, "high"].sum(), 0),
        "baseline_published_total": r(pubsens.loc["all", "central"], 0),
        "baseline_by_type": [{"type": t, "low": r(v["low"], 0), "central": r(v["central"], 0), "high": r(v["high"], 0)}
                             for t, v in by_type.iterrows()],
        "observed_2021_2025": r(obs[[2021, 2022, 2023, 2024, 2025]].sum(), 0),
        "scenarios": [
            {"id": "central", "label": "No measurable change",
             "info": "Like the 76 US places that removed parking minimums: in the one to three years after, their permit rates did not rise measurably compared with similar places that kept them.",
             "additional_total": 0.0, "with_law_total": r(base5, 0)},
            {"id": "upper", "label": "High end of the evidence",
             "info": f"If the true average effect is at the top of what the evidence allows (95 times in 100, the real average would be lower): {rate:.2f} more permits per 1,000 existing homes per year, everywhere except places that already have no parking minimums for housing.",
             "additional_total": up5, "with_law_total": base5 + up5, "rate_per_1000_homes": rate},
        ],
        "reference_line": ref_line(),
    }


def build_areas() -> dict:
    a = pd.read_csv(REF / "parking_model_by_area.csv", dtype={"county_id": str})
    munis = []
    for x in a.itertuples():
        munis.append({"id": x.area_id, "name": x.name, "county": s(x.county_name),
                      "type": s(x.muni_type), "homes": r(x.homes, 0), "eligible_homes": r(x.eligible_homes, 0),
                      "at_benchmark": bool(x.at_benchmark), "near_benchmark": bool(x.near_benchmark),
                      "baseline": r(x.baseline_five_year_central, 1), "add_upper": r(x.addition_upper_five_year, 2),
                      "acres": r(x.land_acres, 0)})
    c = pd.read_csv(REF / "parking_model_by_county.csv", dtype={"county_id": str})
    counties = [{"id": x.county_id, "name": x.county_name, "homes": r(x.eligible_homes, 0), "acres": r(x.land_acres, 0),
                 "baseline": r(x.baseline_five_year_central, 0), "add_upper": r(x.addition_upper_five_year, 0)}
                for x in c.itertuples()]
    dist = {}
    for kind in ("assembly", "senate"):
        d = pd.read_csv(REF / f"parking_model_by_{kind}_district.csv")
        col = d.columns[0]
        dist[kind] = [{"id": int(x[col]), "homes": r(x["eligible_homes"], 0), "baseline": r(x["baseline_five_year_central"], 0),
                       "add_upper": r(x["addition_upper_five_year"], 0)} for _, x in d.iterrows()]
    bench = pd.read_csv(REF / "parking_wi_benchmark_places.csv")
    return {"munis": munis, "counties": counties, "districts": dist,
            "benchmark_places": [{"name": x.name, "rating": x.benchmark_rating, "adopted": s(x.adopted_date)}
                                 for x in bench.drop_duplicates(["name", "benchmark_rating"]).itertuples()]}


CASE_LABELS = {"Upper case (headline)": "High end of the evidence (headline)",
               "Size and metro model (central)": "Prediction by city size and setting",
               "Towns at zero": "High end, with towns left out",
               "Near-benchmark places at zero": "High end, with places that partly removed minimums left out"}
MOVES_LABELS = {"statewide addition": "the statewide total", "statewide addition and where it lands": "the statewide total and where it lands",
                "baseline only": "current law only"}
CHECK_LABELS = {
    "main, weighted by homes": "Main result (weighted by homes)",
    "main, unweighted mean": "Unweighted average",
    "main, median": "Median place",
    "without San Francisco": "Without San Francisco",
    "without the two Texas places": "Without the two small Texas places",
    "without places that rewrote zoning at the same time": "Only places without a zoning rewrite at the same time",
    "main and near together": "Including the 6 places that removed minimums with conditions",
}
MODEL_LABELS = {"M4 log population + metro": "city size and metro setting", "M2 log population": "city size"}


def xest(outcome: str) -> dict:
    x = pd.read_csv(REF / "parking_expanded_estimates.csv").set_index("case")
    k = "Expanded, all units (headline candidate)" if outcome == "all" else "Expanded, units in buildings of 2+ units"
    return {"effect": r(x.loc[k, "effect"]), "p05": r(x.loc[k, "p05"]), "p95": r(x.loc[k, "p95"])}


def build_howsure() -> dict:
    sens = pd.read_csv(REF / "parking_model_sensitivities.csv")
    rob = pd.read_csv(REF / "parking_comparison_robustness.csv")
    rob = rob[(rob["outcome"] == "all") & ~rob["check"].str.startswith("leave out ")]
    los = pd.read_csv(REF / "parking_comparison_robustness.csv")
    los = los[(los["outcome"] == "all") & los["check"].str.startswith("leave out ")]
    ev = pd.read_csv(REF / "parking_comparison_event_path.csv")
    models = pd.read_csv(REF / "parking_comparison_models.csv")
    mm = models[(models["outcome"] == "all") & (models["sample"] == "main")]
    return {
        "sensitivities": [{"case": CASE_LABELS.get(x.case, x.case), "moves": MOVES_LABELS.get(x.moves, x.moves), "value": r(x.value, 0), "description": x.description} for x in sens.itertuples()],
        "robustness": [{"check": x.case.replace("Expanded, ", "").replace(" (headline candidate)", " (main result)"), "places": int(x.places), "effect": r(x.effect), "p05": r(x.p05), "p95": r(x.p95)}
                       for x in pd.read_csv(REF / "parking_expanded_estimates.csv").itertuples()],
        "placebo": {k: r(v, 3) for k, v in pd.read_csv(REF / "parking_placebo_full_summary.csv").iloc[0].items()},
        "tools": [{"tool": x.tool, "us_gain": r(x.us_gain, 3), "ca_gain": r(x.ca_gain, 3)} for x in pd.read_csv(REF / "parking_expanded_tools.csv").itertuples()],
        "leave_one_state": {"min": r(los["effect"].min()), "max": r(los["effect"].max()),
                            "min_state": los.loc[los["effect"].idxmin(), "check"].replace("leave out ", ""),
                            "max_state": los.loc[los["effect"].idxmax(), "check"].replace("leave out ", "")},
        "event_path": [{"year_since": int(x.k), "places": int(x.places), "effect": r(x.effect), "median": r(x.median)} for x in ev.itertuples()],
        "models": {"one_average": r(mm.loc[mm["model"] == "M0 one average", "loo_wmae"].iloc[0], 3),
                   "best": MODEL_LABELS.get(mm.loc[mm["chosen"], "model"].iloc[0], mm.loc[mm["chosen"], "model"].iloc[0]), "best_error": r(mm.loc[mm["chosen"], "loo_wmae"].iloc[0], 3),
                   "best_band": r(mm[mm["model"].str.startswith("M1")]["loo_wmae"].min(), 3)},
        "traits": [{"dataset": x.dataset, "label": x.label, "places": int(x.places), "gain": r(x.gain, 3), "passes": bool(x.passes)}
                   for x in pd.read_csv(REF / "parking_traits_results.csv").itertuples()],
        "trace": [
            {"part": "Current-law baseline", "status": "observed", "text": "Census building permits by municipality and building size, 2023–2025 average; Milwaukee's apartments estimated from the city's property file."},
            {"part": "No measurable change (central)", "status": "calculated", "text": f"From 76 US repeal places compared with similar places; point estimate {xest('all')['effect']:+.2f} permits per 1,000 homes per year, shown as 0."},
            {"part": "High end of the evidence (upper)", "status": "calculated", "text": "From 20,000 placebo studies of cities that never repealed: their spread, centred on the 76 real places' average (owner choice; the resampling high end is a sensitivity)."},
            {"part": "No case below zero", "status": "assumed", "text": "A judgment: the evidence leans slightly negative, but a repeal is not modelled as reducing permits."},
            {"part": "Years 4–5 and evidence carrying over to Wisconsin", "status": "assumed", "text": "The effect was measured over years 1–3 in other places; it is held flat for 2030–2031 and applied in Wisconsin."},
            {"part": "Where the upper case lands", "status": "assumed", "text": "Spread in proportion to existing homes; places that already have no minimums get none."},
        ],
    }


def build_why() -> dict:
    inc = expanded_included()
    pc = pd.read_csv(REF / "parking_partial_checks.csv", dtype=str)
    pc = pc.assign(prn_key=pc["place"] + ", " + pc["state"] + ", United States", evidence=pc["coverage"] + ". " + pc["date_basis"] + ".")
    ck = pd.concat([pd.read_csv(REF / "parking_repeal_checks.csv", dtype=str), pd.read_csv(REF / "parking_repeal_checks_expanded.csv", dtype=str),
                    pc[["prn_key", "evidence", "confidence"]]]).drop_duplicates("prn_key").set_index("prn_key")
    places = []
    for x in inc.sort_values("population", ascending=False).itertuples():
        c = ck.loc[x.prn_key]
        places.append({"place": x.place, "state": x.state, "group": "main" if x.rating == "at" else "with conditions",
                       "year": int(x.event_year), "population": r(x.population, 0), "comparisons": int(x.n_controls),
                       "after_years": int(x.n_post),
                       "before": r(x.rate_before), "after": r(x.rate_after), "cmp_before": r(x.ctrl_before), "cmp_after": r(x.ctrl_after),
                       "effect": r(x.effect), "rewrite": bool(x.simultaneous_rewrite),
                       "evidence": s(c["evidence"]), "confidence": s(c["confidence"])})
    est = pd.read_csv(REF / "parking_comparison_estimates.csv")
    m0 = est[(est["model"] == "M0 one average")].set_index("outcome")
    ab = pd.read_csv(REF / "tod_ab2097_results.csv")
    ab = ab[(ab["case"] == "main") & (ab["group"] == "P") & (ab["measure"] == "per_1000_homes")].set_index("outcome")
    ca = {o: {"effect": r(ab.loc[o, "estimate"]), "p05": r(ab.loc[o, "interval90_low"]), "p95": r(ab.loc[o, "interval90_high"])}
          for o in ("all_units", "units_2plus")}
    ca["jurisdictions"] = int(ab.loc["all_units", "n_jurisdictions"])
    return {
        "places": places,
        "california": {**ca, "text": "California's AB 2097 removed parking minimums within half a mile of major transit stops from 1 January 2023. Comparing permits near transit with permits half a mile to a mile and a half away, in jurisdictions that had not already removed minimums or raised density near transit, gives the same answer as the city repeals: no measurable change in 2023–2025.",
                       "caveats": "Transit stops are from today's map, not a pre-2023 one; and the comparison ring itself rose against land farther away, which could pull the estimate down. Analysis by the transit-oriented density work (docs/tod/AB2097_TEST_RESULTS.md)."},
        "average": {o: xest(o) for o in ("all", "2plus")},
        "studies": [
            {"case": "Buffalo, citywide repeal (2017)", "finding": "36 major projects provided 1,942 parking spaces against 2,444 under the old minimums (79%). Mixed-use projects built 47% of the old minimum; stand-alone apartment buildings built 117% of it.", "status": "observed",
             "source": "Hess and Rehler, Journal of the American Planning Association, 2021", "url": "https://doi.org/10.1080/01944363.2020.1864225"},
            {"case": "Seattle, near frequent transit (2012)", "finding": "Reported as about 18,000 fewer parking spaces over five years than the old rules required.", "status": "source lead",
             "source": "Gabbe, Pierce and Clowers, Land Use Policy, 2020", "url": "https://doi.org/10.1016/j.landusepol.2019.104053"},
            {"case": "Los Angeles adaptive reuse (1999)", "finding": "Exempting old downtown buildings from parking helped convert them into thousands of homes.", "status": "source lead",
             "source": "Manville, Journal of the American Planning Association, 2013", "url": "https://ideas.repec.org/a/taf/rjpaxx/v79y2013i1p49-66.html"},
            {"case": "Denver simulation (2025)", "finding": "A financial model estimates about 12.5% more market-rate apartments; a model, not observed results.", "status": "source lead",
             "source": "University of Denver with the Terner Center's housing simulator", "url": "https://theconversation.com/denver-study-shows-removing-parking-requirements-results-in-more-affordable-housing-being-built-263889"},
        ],
        "developer_parking": "Assumption about parking developers build without mandates: developers keep building the parking that renters, buyers and lenders want, so a repeal adds homes only where a minimum forced more parking than the market wanted. In Buffalo after its 2017 repeal, major projects provided 79% of the old minimum (mixed-use 47%; stand-alone apartments 117%). The scenario sets no parking ratio itself: it uses the permit outcomes of places that repealed, so whatever parking their developers chose is already built in.",
        "north_carolina": "North Carolina's HB 162, signed 6 July 2026, removes minimum parking for new projects statewide from 1 January 2027 (the 20 coastal counties are exempt). It is the closest real law to this scenario; it has no permit data yet.",
        "docs": [doc("docs/parking/EXPANDED_RESULTS.md", "Expanded comparison (76 places, with 5 added)"), doc("docs/parking/COMPARISON_RESULTS.md", "First comparison (24 places)"), doc("docs/parking/COMPARISON_PLAN.md", "Pre-registered plan"),
                 doc("docs/parking/POLICY_TAXONOMY.md", "Which reforms were real"), doc("docs/parking/GATE3_PACKET.md", "Gate 3 packet")],
    }


def build_pilots(areas: dict) -> list:
    h = pd.read_csv(REF / "housing_baseline_history.csv")
    tax = pd.read_csv(REF / "parking_reform_taxonomy.csv")
    by_id = {m["id"]: m for m in areas["munis"]}
    out = []
    for slug, aid in PILOTS.items():
        m = by_id[aid]
        hh = h[h["area_id"] == aid].sort_values("year")
        place = m["name"].rsplit(" ", 1)[0]
        rules = tax[(tax["state"] == "Wisconsin") & (tax["place"] == place) & tax["land_use"].str.contains("resid|all uses", na=False)]
        out.append({
            "slug": slug, "id": aid, "name": m["name"], "homes": m["homes"], "at_benchmark": m["at_benchmark"],
            "baseline": m["baseline"], "add_upper": m["add_upper"],
            "history": [{"year": int(x.year), "units_1": r(x.units_1unit, 0), "units_2": r(x.units_2units, 0), "units_3_4": r(x.units_3_4units, 0),
                         "units_5": r(x.units_5plus, 0), "adjusted": "adjusted_milwaukee_mprop" in str(x.allocation),
                         "split": "assumed_split_by_homes" in str(x.allocation)} for x in hh.itertuples()],
            "rules": [{"rating": x.benchmark_rating, "date": s(x.adopted_date), "summary": s(x.summary)} for x in rules.itertuples()][:6],
        })
    return out


def build_additions() -> dict:
    """additions_by_area.json for combined views (docs/shared/SCENARIO_CONTRACT.md section 9): each
    municipality's additions by year and path, split into near_stops and elsewhere by TOD's share of
    homes near qualifying stops (main definition)."""
    a = pd.read_csv(REF / "parking_model_by_area.csv")
    share = pd.read_csv(REF / "tod_near_stop_homes_by_muni.csv").set_index("area_id")["share_near_main"]
    rows = []
    for x in a.itertuples():
        per_year = float(x.addition_upper_per_year)
        sh = float(share.get(x.area_id, 0.0))
        for part, f in (("near_stops", sh), ("elsewhere", 1.0 - sh)):
            if f <= 0 and part == "near_stops":
                continue
            rows.append({"area_id": x.area_id, "part": part, "central": [0.0] * len(YEARS),
                         "upper": [round(per_year * f, 4)] * len(YEARS)})
    return {"reform": "parking", "baseline_version": BASELINE_VERSION, "years": YEARS,
            "paths": [{"id": "central", "label": "No measurable change"}, {"id": "upper", "label": "High end of the evidence"}],
            "roles": {"lower": "central", "central": "central", "upper": "upper"},
            "split_source": "reference/tod_near_stop_homes_by_muni.csv, share_near_main", "areas": rows}


def validate(sw: dict, areas: dict) -> dict:
    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
    tot = sum(m["add_upper"] or 0 for m in areas["munis"])
    up = next(x for x in sw["scenarios"] if x["id"] == "upper")["additional_total"]
    check("upper case equals the sum of places", abs(tot - up) < 2, f"{tot:,.0f} vs {up:,.0f}")
    check("with-law total equals its displayed parts", all(x["with_law_total"] == sw["baseline_total"] + x["additional_total"] for x in sw["scenarios"]), "central and upper")
    check("central addition is zero", all((y.get("add_central") or 0) == 0 for y in sw["years"]), "every forecast year")
    check("no place below zero", all((m["add_upper"] or 0) >= 0 for m in areas["munis"]), "upper case")
    check("places at the benchmark get nothing", all((m["add_upper"] or 0) == 0 for m in areas["munis"] if m["at_benchmark"]),
          f"{sum(m['at_benchmark'] for m in areas['munis'])} places")
    base_ref = pd.read_csv(REF / "housing_baseline_statewide_by_year.csv")
    bref = base_ref[(base_ref["kind"] == "projected") & (base_ref["structure_type"] == "all") & base_ref["year"].isin(YEARS)]["central"].sum()
    check("baseline matches the shared baseline", abs(bref - sw["baseline_total"]) < 2, f"{bref:,.0f}")
    return {"passed": sum(c["passed"] for c in checks), "failed": sum(not c["passed"] for c in checks), "checks": checks}


def main():
    hashes = [{"path": p, "sha256": sha256(ROOT / p)} for p in INPUTS]
    run_id = "parking-" + hashlib.sha256("".join(h["sha256"] for h in hashes).encode()).hexdigest()[:10]
    out = OUT_ROOT / run_id
    if OUT_ROOT.exists():
        for old in OUT_ROOT.iterdir():
            if old.is_dir() and old.name != run_id:
                shutil.rmtree(old)
    out.mkdir(parents=True, exist_ok=True)
    sw = build_statewide()
    areas = build_areas()
    val = validate(sw, areas)
    manifest = {
        "schema_version": 1, "run_id": run_id, "scenario_id": "parking", "title": "Wisconsin parking requirement reduction",
        "outcome": {"short": "Housing units authorized by building permits (all building sizes), at issuance, Wisconsin, 2027–2031.",
                    "long": "New housing units authorized by building permits, counted at permit issuance, all building sizes (1, 2, 3–4 and 5+ units), from the Census Building Permits Survey.",
                    "rate_units": "permits per 1,000 existing homes per year", "count_units": "permits"},
        "dates": {"last_observed_year": 2025, "forecast_years": YEARS, "effective": "Stylized statewide law in effect 1 January 2027"},
        "vintages": [{"what": "Census Building Permits Survey (Wisconsin places)", "vintage": "2015–2025 annual"},
                     {"what": "Census Building Permits Survey (all US places, comparison)", "vintage": "2012–2025 annual"},
                     {"what": "ACS homes and population", "vintage": "2020–2024 5-year"},
                     {"what": "Milwaukee Master Property file (apartment adjustment)", "vintage": "as of October 2026"},
                     {"what": "Parking Reform Network reform map", "vintage": "commit 3a62231, 26 October 2026"}],
        "validation": val, "repo_url": REPO_URL, "inputs": hashes,
        "status_pills": {"observed": "Observed: counted in a published source.", "calculated": "Calculated: computed from observed inputs and stated rules.",
                         "assumed": "Assumed: a judgment where no data decide it."},
        "files": ["statewide.json", "areas.json", "howsure.json", "why.json", "pilots.json", "additions_by_area.json"],
        "baseline_version": BASELINE_VERSION,
    }
    files = {"manifest.json": manifest, "statewide.json": sw, "areas.json": areas, "howsure.json": build_howsure(),
             "why.json": build_why(), "pilots.json": build_pilots(areas), "additions_by_area.json": build_additions()}
    for name, obj in files.items():
        (out / name).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n")
    (OUT_ROOT / "latest.json").write_text(json.dumps({"run_id": run_id}) + "\n")
    print(run_id, f"validation {val['passed']} passed, {val['failed']} failed")


if __name__ == "__main__":
    main()
