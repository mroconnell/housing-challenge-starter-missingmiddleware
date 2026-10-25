"""Export the adopted ADU model outputs as a static JSON bundle for the Gate 4 tool (ui/).

The browser runs no model. Every number the tool shows is read from this bundle, and the
bundle is built only from the adopted outputs:

- reference/adu_model_*.csv and adu_model_params.json (engine, scripts/run_adu_model.py);
- data/processed/model_run/results_long.parquet (the same engine run, per area, year and path);
- reference/wi_baseline_*.csv, wi_measured_permits_2022_2025.csv (current-law baseline);
- reference/pooled_revision_*.csv, eligible_basis_g3f2.csv (scenarios, robustness checks);
- reference/wi_adu_rules.csv, wi_rights_exposure.csv, wi_town_zoning_status.csv (rules, coverage);
- reference/madison_adu_permits_by_year.csv, pleasant_prairie_/sun_prairie_adu_equivalent_by_year.csv (pilots);
- reference/statewide_states_annual.csv, pooled_adoption_points.csv, madison_like_*.csv (charts);
- data/processed/foundation/state_conditions.parquet, areas.parquet, geo/*.parquet (context, area list);
- data/raw/census_cb_2024/ (Census cartographic boundary files, shoreline-clipped, for the map drawing only).

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
    "reference/pooled_revision_g3f2.csv", "reference/eligible_basis_g3f2.csv",
    "reference/wi_baseline_statewide.csv", "reference/wi_baseline_by_municipality.csv",
    "reference/wi_baseline_sensitivities.csv", "reference/wi_measured_permits_2022_2025.csv",
    "reference/wi_adu_rules.csv", "reference/wi_rights_exposure.csv", "reference/wi_town_zoning_status.csv",
    "reference/madison_adu_permits_by_year.csv", "reference/pleasant_prairie_adu_equivalent_by_year.csv",
    "reference/sun_prairie_adu_equivalent_by_year.csv", "reference/statewide_states_annual.csv",
    "reference/pooled_adoption_points.csv", "reference/statewide_adoption_curve.csv",
    "reference/madison_like_annual.csv", "reference/madison_like_median_path.csv",
    "data/processed/model_run/results_long.parquet", "data/processed/foundation/areas.parquet",
    "data/processed/foundation/state_conditions.parquet", "data/processed/foundation/geo/areas_county.parquet",
    "data/processed/foundation/geo/areas_municipality.parquet",
    "data/raw/census_cb_2024/cb_2024_55_cousub_500k.zip", "data/raw/census_cb_2024/cb_2024_us_county_500k.zip",
]
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
    "assumed": "Assumed: local ADU rules not coded; treated like places with restricted rules (AQ-027)",
}
# Display names for the three scenarios: one short name used everywhere, plus a description.
SCEN_NAME = {"lower": "Lower", "central": "Central", "upper": "Strong adoption"}
SCEN_DESC = {"lower": "Slower than any statewide-law state so far", "central": "Like a typical statewide-law state",
             "upper": "The high end of what statewide-law states have reached"}
# Gate 3 values used in the scenario explanations (docs/gate3/POOLED_REVISION.md, sections 2-3):
COMMON_LEVEL = 1.00   # common level at a typical place, law in force 4+ years, permits per 1,000 SF homes per year
SPREAD = 1.89         # 80% between-state factor: lower = central / 1.89, upper = central x 1.89
CA_OUT_CENTRAL = 7621 # central with California out of the common level (sensitivity case)
MADISON_IDS = {"muni:5502548000"}
MADISON_PROVISIONAL_THROUGH = "23 October 2026"   # docs/gate2/MADISON_PERMITS.md: permits downloaded to 2026-10-23
WATER_REASON = "Water area (Great Lakes or Green Bay): no homes, not drawn on the map"
PIECE_REASON = "No single-family homes in this piece of the area (a sliver across a county line)"


def madison_note(p: dict) -> str:
    r = p["area_paths"]["madison_like_path"]["rates"]
    return (f"Madison alone follows the observed path of Madison-like cities in Washington and Oregon: {r[0]:.2f} rising to "
            f"{r[-1]:.2f} permits per 1,000 single-family homes per year in years 1–5 (2027–2031), the same in every scenario. "
            "Every other place, including Madison's suburbs, is on the statewide model, so Madison's with-law rate is below "
            "its neighbours' and does not move with the scenario. This owner decision (AQ-042) is under review at Gate 5.")


def basis_text(status: str, basis: str) -> str:
    """Plain words for wi_baseline_by_municipality.csv x_basis (the current-law rate's basis)."""
    b = str(basis)
    since = b.split("since ")[-1] if "since " in b else None
    if status == "observed":
        w = b.replace("observed ", "").split(" ")[0].replace("-", "–")
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
        return "rules not coded, so the restricted-group rate is assumed (AQ-027)"
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
    info = {
        "lower": (f"The central level divided by {SPREAD:.2f}, about {lo:.2f} permits "
                  f"per 1,000 single-family homes per year at a typical place once the law has been in force 4 years. "
                  f"The slowest states are Rhode Island ({lv['RI']:.2f}) and Oregon ({lv['OR']:.2f})."),
        "central": (f"Wisconsin at the common level of the eight statewide-law states, about {COMMON_LEVEL:.2f} permit per 1,000 "
                    f"single-family homes per year at a typical place once the law has been in force 4 years (Washington "
                    f"{lv['WA']:.2f}, Utah {lv['UT']:.2f}, Maine {lv['ME']:.2f}, Vermont {lv['VT']:.2f})."),
        "upper": (f"The central level times {SPREAD:.2f}, about {up:.2f} "
                  f"at a typical place; only California ({lv['CA']:.2f}) has gone higher."),
    }
    out = []
    for k in PATHS:
        out.append({"id": k, "label": SCEN_NAME[k], "description": SCEN_DESC[k], "gate3_label": p["paths"][k]["label"],
                    "info": info[k], "basis": p["paths"][k]["basis"], "ramp": p["paths"][k]["ramp"]})
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
    pep = [{"year": int(x.year), "value": r(x.value, 0), "status": x.status, "vintage": x.source_vintage}
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
        bps.append(row)

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
    al = pd.read_csv(REF / "pooled_revision_adoption_line.csv")
    al = al[al.variant.eq("vacant_lot_x0.951")].sort_values("year")
    ref_line = {"label": "Reference line: statewide adoption",
                "info": "The median path statewide-law states actually reached (California not included).",
                "why_central_differs": (f"The central ({st_tot.loc['central', 'additional_units']:,.0f}) sits above this line "
                                        f"({al.additional.sum():,.0f}) because it is the pooled model, not a plain median: California "
                                        f"is one of the eight states that set its common level (with California out, the central "
                                        f"would be {CA_OUT_CENTRAL:,}), and no place may fall below the Madison floor. The line "
                                        "is the median of the seven other states' observed paths."),
                "rate_by_year": [r(v, 4) for v in al.median_rate], "additional_by_year": [r(v, 2) for v in al.additional],
                "additional_total": r(al.additional.sum(), 1),
                "with_law_by_year": [r(v, 2) for v in al.with_law_total],
                "source": "reference/pooled_revision_adoption_line.csv (variant vacant_lot_x0.951)"}
    ctx = pd.read_csv(REF / "adu_model_by_context.csv")
    homes_ctx = pd.read_csv(REF / "wi_baseline_by_municipality.csv").groupby("context_group").homes.sum()
    contexts = []
    for g, lab in (("urban", "Urban"), ("suburban", "Suburban"), ("small_community", "Small communities"), ("rural", "Rural")):
        d = ctx[ctx.context_group.eq(g)].set_index("path")
        contexts.append({"id": g, "label": lab, "homes": int(homes_ctx.get(g, 0)), "baseline": r(d.loc["central", "baseline_units"], 2),
                         **{f"additional_{k}": r(d.loc[k, "additional_units"], 2) for k in PATHS}})
    return {"homes": homes, "housing_units_pep": pep, "acs_total_units": one("total_housing_units_acs"),
            "occupied": one("occupied_units"), "vacant": one("vacant_units"), "vacancy_rate": one("vacancy_rate"),
            "mix": mix, "bps": bps, "baseline": baseline, "scenarios": scen, "reference_line": ref_line, "contexts": contexts}


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
            row["note"] = madison_note(p)
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
                    ("assumed", "Not coded: the AQ-023/AQ-027 default applies")):
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
    plain = {
        "adopted": ("Adopted model (the scenarios)", "The three scenarios as adopted at Gate 3."),
        "eligible-property": ("Eligible-property basis without one-unit attached homes",
                              "Permits per 1,000 properties eligible under each state's own law. Its own baseline is 636 permits."),
        "LA-calibrated": ("LA-calibrated multifamily correction to California's counts",
                          "A more accurate but data-hungrier removal of California ADUs on multifamily lots (AQ-041)."),
        "multiplicative": ("Multiplicative law",
                           "Each place's current rate × the pooled statewide-law factor. A downside: before-and-after pairs in other states contradict it, but no Midwest state has post-law data yet."),
        "California-only": ("California-only market regression",
                            "A downside: Wisconsin stays near the response of Madison-like markets."),
        "no ramp": ("No ramp-up: full rate from 2027", "How much the ramp-up in the first three years removes."),
        "rural and small": ("Rural and small-community places at the Madison floor (0.2345)",
                            "How much of the addition comes from places with no measured activity."),
        "Madison at its pooled": ("Madison at its pooled level instead of the Madison-like path", "The effect of the Madison decision."),
        "California out": ("California out of the between-state common level (configuration B)",
                           "The alternative that predicted held-out states less well (robustness checks below)."),
    }
    cases = []
    for row in sens.itertuples(index=False):
        key = next(k for k in plain if row.change.startswith(k) or k in row.change)
        lab, what = plain[key]
        cases.append({"id": key.lower().replace(" ", "-"), "label": lab, "what": what, "change_as_recorded": row.change,
                      "lower": r(row.lower_additional_5yr, 1), "central": r(row.central_additional_5yr, 1),
                      "upper": r(row.upper_additional_5yr, 1), "difference_central": r(row.difference_central, 1),
                      "baseline": r(row.baseline_5yr, 1), "kind": row.kind, "source": row.source,
                      "missing_reason": None if not pd.isna(row.lower_additional_5yr) else
                      "central only"})

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
    bsens = pd.read_csv(REF / "wi_baseline_sensitivities.csv")
    return {"coverage_rates": cov, "coverage_rights": rights, "classes": classes, "sensitivity_cases": cases,
            "robustness": {"rows": robust, "a_win_share": win, "n_states": 7,
                           "units": "root-mean-square log error predicting each of the 7 held-out non-California statewide-law states (lower is better)",
                           "source": "reference/pooled_revision_g3f2.csv, reference/eligible_basis_g3f2.csv"},
            "baseline_sensitivities": [{"label": x.sensitivity, "total": r(x.b5yr_central, 2), "change": r(x.change_vs_main, 2)}
                                       for x in bsens.itertuples()],
            "challenges": [
                {"title": "No Midwest state has data after a statewide law",
                 "text": "Under current law the model expects Wisconsin to permit 0.07 per 1,000 single-family homes per year in 2027–2031 (645 permits ÷ 1,839.569 thousand homes ÷ 5 years); there is no observed statewide ADU series. States with before-and-after data (California, Rhode Island, Washington, Vermont) reached similar first-year levels however low they started, but they are coastal or New England markets. Iowa's first full year (2026) will be the first Midwest test."},
                {"title": "Madison-like cities ran at a little over half the central scenario's rate in years 1–3",
                 "text": "Medians of 0.45, 0.54 and 0.60 permits per 1,000 single-family homes per year in 9 Washington and Oregon cities, against the central scenario's statewide 0.77, 0.95 and 0.99. Only Madison is moved onto that path, so Madison's with-law rate sits below its suburbs'. If Wisconsin's other mid-size markets behave like those cities, the central is too high in its first three years; if Madison behaves like the statewide model, Madison is too low. Gate 5 will review this."},
                {"title": "The hold-out test rests on 7 states",
                 "text": f"California in the common level wins in {win * 100:.0f}% of resamples of the 7 states, which is within noise. The lower and upper scenarios rest on how 8 states differ, one of them California."},
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
    desc = {
        "madison": "Wisconsin's largest ADU market and the source of the Madison floor. It already allows ADUs much like the benchmark law, so the law adds less here than in most places.",
        "pleasant-prairie": "A Kenosha County village that prohibits ADUs: the restrictive pilot. Its own issued-permit records show {n} second-home permits on single-family lots in 2014–2025.",
        "sun-prairie": "Madison's neighbour, used as a same-market check. It legalised ADUs in May 2026, so its baseline is still ramping up; its records are applications, not issued permits.",
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
                    "provisional_through": MADISON_PROVISIONAL_THROUGH if slug == "madison" else None,
                    # docs/gate2/MADISON_PERMITS.md: 29 of the 42 provisional 2026 units are one templated builder programme
                    "provisional_detail": "29 of them from one builder's templated programme" if slug == "madison" else None,
                    "permits": permits_series(slug), "measured": mrow, "rules": rl})
    return out


# --------------------------------------------------------------------------------------------
def build_evidence(p: dict) -> dict:
    lv = stage2_levels()
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
        lab = {k: f"Wisconsin: {SCEN_NAME[k].lower()} scenario" for k in PATHS}[path]
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
    clines.append({"name": "Median of Madison-like cities in Washington and Oregon", "kind": "median",
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
        {"kind": E, "title": "Madison-like cities after a statewide law", "type": "descriptive", "status": "observed",
         "text": "Nine Washington and Oregon cities like Madison ran at 0.45, 0.54 and 0.60 permits per 1,000 single-family homes per year in years 1–3, a little over half the central scenario's statewide rate (0.77, 0.95, 0.99). Madison alone follows this observed path in every scenario; every other place is on the statewide model. Under review at Gate 5.",
         "links": [doc("docs/gate3/MADISON_LIKE_CITIES.md", "Madison-like cities")]},
        {"kind": E, "title": "Wisconsin today: measured permits", "type": "descriptive", "status": "observed",
         "text": "Observed: Madison issued 40 second-home permits on single-family lots in 2022–2025 (0.19 per 1,000 single-family homes per year). Calculated, not observed: under current law the model expects 0.07 per 1,000 per year statewide in 2027–2031; there is no statewide ADU series. Most places have no record-level permit data, so their rates come from their rules group.",
         "links": [doc("docs/gate3/WI_BASELINE.md", "Wisconsin baseline"), doc("reference/wi_measured_permits_2022_2025.csv", "Measured permits (CSV)")]},
        {"kind": E, "title": "Local ADU rules coded so far", "type": "descriptive", "status": "observed",
         "text": "The largest jurisdictions' ADU rules were coded from their ordinances, with section and retrieval date for each provision. Every other place is treated as restricted.",
         "links": [doc("reference/wi_adu_rules.csv", "Coded rules (CSV)"), doc("docs/gate3/WI_RULES_VS_ACTIVITY.md", "Rules versus activity"),
                   doc("docs/gate3/WI_UNZONED_TOWNS.md", "Unzoned towns")]},
        {"kind": A, "title": "Places with uncoded rules behave like restricted places", "type": "judgment", "status": "assumed",
         "text": "1,882 of 1,925 areas (69% of single-family homes) have no coded rules. They get the restricted-group rate. If they behaved like prohibited places instead, the baseline would be 459 permits over 2027–2031 instead of 645.",
         "challenge": "Is a rural town under county zoning really like a city with restricted ADU rules?",
         "links": [doc("docs/ASSUMPTIONS_AND_QUESTIONS.md", "AQ-023 and AQ-027"), doc("docs/gate3/WI_BASELINE.md", "Wisconsin baseline")]},
        {"kind": A, "title": "Wisconsin will respond like the statewide-law states", "type": "transferred", "status": "assumed",
         "text": "No Midwest state has post-law data yet. The model assumes Wisconsin's places respond like comparable places in the eight states, after adjusting for home value, income and size within each state.",
         "challenge": "Iowa's first full year (2026) will be the first Midwest test.",
         "links": [doc("docs/gate3/README.md", "Gate 3 packet")]},
        {"kind": A, "title": "The law takes effect on 1 January 2027 and ramps up", "type": "judgment", "status": "assumed",
         "text": "Stylized start date. In years 1–3 the addition reaches 0.63, 0.80 and 0.82 of its year-4 size (central). Without the ramp, the central would be 10,228 permits instead of 8,721.",
         "challenge": "A real bill would have its own effective date and local compliance deadline.",
         "links": [doc("docs/gate3/POOLED_REVISION.md", "Pooled model revision")]},
        {"kind": A, "title": "No place falls below the Madison floor", "type": "judgment", "status": "assumed",
         "text": "With the law, every area's rate is at least 0.2345 permits per 1,000 single-family homes per year: Madison's 2022–2025 rate (40 permits ÷ 213.168 thousand home-years = 0.1876) divided by 0.8.",
         "links": [doc("docs/gate3/POOLED_REVISION.md", "Pooled model revision")]},
        {"kind": A, "title": "ADUs built with a new house on a vacant lot do not count", "type": "descriptive", "status": "calculated",
         "text": "In 17 cities split by demolition records, vacant-lot new-house ADUs were a median 4.9% of ADUs, so every non-California series is multiplied by 0.951.",
         "links": [doc("docs/gate3/MADISON_LIKE_CITIES.md", "Madison-like cities (vacant-lot share)")]},
        {"kind": A, "title": "Rural home values include acreage", "type": "judgment", "status": "assumed",
         "text": "Rural areas get 3,801 of the 8,721 central permits (44%) with 710,070 of the 1,839,569 single-family homes (39%), partly because rural median home values include land. Setting rural and small-community places to the Madison floor gives 4,729.",
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
def build_geo(out: Path, munis: list) -> dict:
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


def validate(state: dict, counties: list, munis: list, unc: dict) -> dict:
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
    geo_n = build_geo(out, munis)
    val = validate(state, counties, munis, unc)
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
            {"what": "Single-family (one-unit detached) homes, housing mix, occupancy", "vintage": "ACS 2020–2024 5-year (B25024, B25002)"},
            {"what": "Housing units by year", "vintage": "Census Population Estimates, Vintage 2025 (2020–2025)"},
            {"what": "Homes permitted by year", "vintage": "Census Building Permits Survey, annual 2015–2025 (final)"},
            {"what": "Areas", "vintage": "Census TIGER/Line 2024 (counties, county subdivisions)"},
            {"what": "Map outlines", "vintage": "Census cartographic boundary files 2024, 1:500,000, shoreline-clipped (water areas not drawn)"},
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
                  "geo_counties.json", "geo_munis.json"],
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
    (OUT_ROOT / "latest.json").write_text(json.dumps({"run_id": run_id}) + "\n")
    total = sum(f.stat().st_size for f in out.iterdir())
    print(f"bundle {run_id}: {len(list(out.iterdir()))} files, {total / 1e6:.2f} MB -> {out.relative_to(ROOT)}")
    for c in val["checks"]:
        print(f"  ok  {c['check']}: {c['detail']}")


if __name__ == "__main__":
    sys.exit(main())
