"""Export the transit-oriented density (TOD) scenario as a static JSON bundle for the tool (Gate 4).

The browser runs no model: every number it shows comes from this bundle, which is built only from
committed files:

- reference/tod_model_statewide.csv, _by_area.csv, _by_county.csv, _by_assembly_district.csv,
  _by_senate_district.csv, _sensitivities.csv, _checks.csv, _params.csv (the Gate 3 model, AQ-050, AQ-051)
- reference/tod_definition_summary.csv, tod_stops.csv, tod_station_areas.csv, tod_near_stop_homes_by_muni.csv
- reference/tod_case_estimates.csv, tod_cases.csv, tod_madison_test_results.csv, tod_madison_test_rates_by_year.csv,
  tod_madison_test_predictions.csv, tod_scale_check.csv, tod_scale_check_metro_years.csv
- reference/housing_baseline_statewide_by_year.csv, housing_baseline_by_area.csv (the shared all-housing baseline)
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
ADU_RUN = json.loads((ROOT / "ui" / "public" / "runs" / "latest.json").read_text())["run_id"]
GEO_MUNIS = f"ui/public/runs/{ADU_RUN}/geo_munis.json"

INPUTS = [
    "scripts/build_tod_bundle.py",
    "reference/tod_model_statewide.csv", "reference/tod_model_by_area.csv", "reference/tod_model_by_county.csv",
    "reference/tod_model_by_assembly_district.csv", "reference/tod_model_by_senate_district.csv",
    "reference/tod_model_sensitivities.csv", "reference/tod_model_checks.csv", "reference/tod_model_params.csv",
    "reference/tod_definition_summary.csv", "reference/tod_stops.csv", "reference/tod_station_areas.csv",
    "reference/tod_near_stop_homes_by_muni.csv",
    "reference/tod_case_estimates.csv", "reference/tod_cases.csv",
    "reference/tod_madison_test_results.csv", "reference/tod_madison_test_rates_by_year.csv",
    "reference/tod_madison_test_predictions.csv",
    "reference/tod_scale_check.csv", "reference/tod_scale_check_metro_years.csv",
    "reference/housing_baseline_statewide_by_year.csv", "reference/housing_baseline_by_area.csv",
    "reference/housing_baseline_history.csv",
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
    "little": {
        "label": "Little response", "evidence": "like Los Angeles's transit program",
        "info": "Like Los Angeles's Transit Oriented Communities program (2017), the only US transit program whose effect on a whole city's housing has been measured. It added 0.04 percentage points to the city's housing growth over six years, and it required affordable homes, which the modelled law does not.",
    },
    "typical": {
        "label": "Typical response", "evidence": "like the average loosening reform in 1,136 US cities",
        "info": "Like the average zoning reform that loosened rules in a study of 1,136 US cities (Stacy and others, 2023): about +0.8% more addresses three or more years after each reform. Most of those reforms were about accessory dwellings and lot sizes, not transit upzonings.",
    },
    "strong": {
        "label": "Strong response", "evidence": "like Auckland's 2016 upzoning",
        "info": "Like Auckland, New Zealand, which upzoned three-quarters of its residential land in 2016 and permitted 21,808 extra homes over 2016–2021, net of building moved from elsewhere in the city.",
    },
}
REF_LINE_INFO = "The median of the three studies. It equals the typical response, so it is drawn as a dotted line on top of it."
TIMING = ("The studies measured their effects three or more years after each reform. The model places that effect "
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
    ("law_addition", "typical_range"): ("Typical response at the low and high ends of its study's interval", "Stacy and others' 95% interval, +0.2% to +1.4%."),
    ("law_addition", "as_published"): ("Each study's effect as published", "Not adjusted for how much of each city the reform covered (Los Angeles about 61% of homes, Auckland 75.2% of residential land)."),
    ("law_addition", "ramp_year5_alt"): ("Smoother final year", "Year 2031 set to the average of 2029–2031 instead of the measured New York drop. Changes timing only; the five-year totals stay the same."),
    ("law_addition", "strong_ny_ramp"): ("Strong response timed like New York", "The strong response spread over the years like the New York rezonings instead of Auckland's own pattern. Same five-year total."),
    ("where_homes_land", "no_suburbs"): ("Only Milwaukee and Madison get homes", "The suburbs, whose zoning rules were not entered into the model, get none of the extra homes."),
    ("where_homes_land", "unscaled_suburbs"): ("Suburbs' estimated room not scaled down", "The suburbs' room for new homes is estimated from existing buildings and not scaled by 0.719."),
    ("where_homes_land", "rapid_only"): ("Only rail and rapid transit stations count", "Buses every 15 minutes do not qualify. Fewer homes are near stops, so fewer homes are expected near stops both with and without the law."),
    ("where_homes_land", "high"): ("Buses every 20 minutes count too", "Adds 20-minute bus routes within ¼ mile, including Eau Claire's."),
    ("where_homes_land", "b_half"): ("All 15-minute stops count within ½ mile", "Bus stops get the same ½ mile as stations."),
    ("baseline_only", "baseline_low"): ("Low current-law path", "Wisconsin's 10th-percentile five-year outcome since 1990."),
    ("baseline_only", "baseline_high"): ("High current-law path", "Wisconsin's 90th-percentile five-year outcome since 1990."),
    ("baseline_only", "census_as_published"): ("Milwaukee's apartments as the Census published them", "The Census permit file misses most of Milwaukee's apartments; the main case uses the city's property file instead."),
}
GROUPS = [("law_addition", "Cases that change the law's addition"),
          ("where_homes_land", "Cases that change where the homes land (and, for the stop rules, how many homes are near stops)"),
          ("baseline_only", "Cases that change current law only")]


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


def metro_of(county: str) -> str:
    for k, (_, counties) in METROS.items():
        if county in counties:
            return k
    return REST[0]


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
        if sid == "typical":
            row.update(range_low=r(f["addition_range_low"], 4), range_high=r(f["addition_range_high"], 4))
        scen.append(row)
    refl = five.loc["reference_line"]
    ref_years = yr[yr["scenario"] == "reference_line"].sort_values("year")
    # statewide all-housing baseline, for context (the TOD baseline is the part of it near qualifying stops)
    hb = pd.read_csv(REF / "housing_baseline_statewide_by_year.csv")
    hbp = hb[(hb["kind"] == "projected") & (hb["structure_type"] == "all") & hb["year"].isin(YEARS)]
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
    return {
        "state_homes": int(main_def.state_homes_2020), "stock_homes": int(t0["stock_homes_station_areas"]),
        "homes_two_cities": {"milwaukee": int(main_def.milwaukee_city_homes), "madison": int(main_def.madison_city_homes),
                             "share": r(main_def.share_in_two_cities, 4)},
        "ladder": ladder, "law": law, "agencies": agencies,
        "baseline": baseline, "state_baseline_total": r(hbp["central"].sum(), 4),
        "scenarios": scen,
        "reference_line": {"label": "Median of the three studies", "info": REF_LINE_INFO,
                           "additional_total": r(refl["addition"], 4), "by_year": [r(v, 4) for v in ref_years["addition"]]},
        "timing_caveat": TIMING,
    }


# ---- areas ------------------------------------------------------------------------------------
def by_years(row) -> list:
    return [r(row[f"add_{y}"], 4) for y in YEARS]


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

    def agg(file, key, name_fn):
        df = pd.read_csv(REF / file)
        out = {}
        for x in df.itertuples():
            k = getattr(x, key)
            o = out.setdefault(k, {"id": str(k), "name": name_fn(k), "baseline": r(x.baseline_near_central_2027_2031, 4), "add": {}})
            if x.scenario in SCEN:
                o["add"][x.scenario] = r(x.add_2027_2031, 4)
        rows = list(out.values())
        nonzero = [o for o in rows if o["baseline"] > 0 or any(v > 0 for v in o["add"].values())]
        return {"rows": sorted(nonzero, key=lambda o: -o["add"]["typical"]), "total_count": len(rows)}

    counties = agg("tod_model_by_county.csv", "county", lambda k: k)
    assembly = agg("tod_model_by_assembly_district.csv", "assembly_district", lambda k: f"Assembly District {k}")
    senate = agg("tod_model_by_senate_district.csv", "senate_district", lambda k: f"Senate District {k}")
    metros = []
    for mid, label in [(k, v[0]) for k, v in METROS.items()] + [REST]:
        ms = [m for m in munis if m["metro"] == mid]
        metros.append({"id": mid, "name": label, "places": len(ms),
                       "counties": sorted({m["county"] for m in ms}),
                       "homes_near": sum(m["homes_near"] for m in ms),
                       "baseline": r(sum(m["baseline"] for m in ms), 4),
                       "add": {sc: r(sum(m["add"][sc] for m in ms), 4) for sc in SCEN}})
    # places that get extra homes with few homes near stops today: homes are placed by land where the law adds room
    few = [m["name"] for m in munis if m["homes_near"] < 100 and m["add"]["typical"] >= 1]
    # places whose current-law figure rests on very few reported permits in 2021-2025 while the law adds many homes
    hist = pd.read_csv(REF / "housing_baseline_history.csv")
    low = []
    for m in munis:
        if m["add"]["typical"] >= 50 and m["baseline"] < 10:
            h = hist[(hist["area_id"] == m["id"]) & hist["year"].between(2021, 2025)].sort_values("year")
            low.append({"name": m["name"], "years": [int(y) for y in h["year"]], "units": [r(u, 0) for u in h["units_all"]],
                        "units_5plus": r(h["units_5plus"].sum(), 0)})
    return {"munis": munis, "metros": metros, "counties": counties, "assembly": assembly, "senate": senate,
            "few_homes_places": few, "low_permit_places": low}


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
            row = {"id": sens, "label": label, "text": text, "baseline": r(sg["baseline_near_stops_2027_2031"].iloc[0], 4), "add": {}}
            if sens == "typical_range":
                row["add"] = {"typical_low": r(sg.loc["typical_low", "addition_2027_2031"], 4), "typical_high": r(sg.loc["typical_high", "addition_2027_2031"], 4)}
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
         "text": "Each scenario's share of the homes near stops comes from a published study of a whole city's net gain in homes after upzoning (Los Angeles, 1,136 US cities, Auckland), divided by the study's coverage where it reports one."},
        {"part": "That those results carry over to Wisconsin", "status": "assumed",
         "text": "No Wisconsin outcome has tested the sizing. Milwaukee's and Madison's shares of homes near stops (68% and 63%) are close to Los Angeles's 61% coverage."},
        {"part": "Timing over 2027–2031", "status": "calculated",
         "text": "The little and typical responses follow the build-up measured after the New York rezonings; the strong response follows Auckland's own yearly pattern."},
        {"part": "Where homes land in Milwaukee and Madison", "status": "calculated",
         "text": f"From the two cities' zoning codes, entered rule by rule: the extra floor area the law allows on each piece of land. These two cities get {round(coded_typ / tot_typ * 100)}% of the typical response."},
        {"part": "Where homes land in the suburbs", "status": "assumed",
         "text": f"Their zoning rules were not entered, so the room for new homes is estimated from existing buildings and scaled by 0.719, the ratio measured in Milwaukee and Madison. The suburbs get {round(100 - coded_typ / tot_typ * 100)}% of the typical response."},
        {"part": "Split into legislative districts", "status": "assumed",
         "text": "Each place's numbers are split across districts in proportion to where its detached houses are (the same split the ADU screens use), not by homes near stops."},
    ]
    cannot = [
        {"title": "Whether Wisconsin will behave like the average city in these studies",
         "text": "Only 28 of the 96 loosening reforms in the typical study changed floor area, density or height; most were about accessory dwellings and lot sizes."},
        {"title": "Timing", "text": TIMING},
        {"title": "Transit-oriented density alone versus with parking reform",
         "text": "The cases cannot separate the two. The parking reform has its own scenario in this tool."},
        {"title": "Rents, displacement and transit ridership", "text": "These are not modelled."},
        {"title": "Lot-by-lot predictions", "text": "The model works by place. Nothing here says what will be built on any one lot."},
    ]
    return {"main_baseline": r(main.loc["typical", "baseline_near_stops_2027_2031"], 4), "groups": groups, "per_acre": per_acre,
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


def build_why() -> dict:
    ce = pd.read_csv(REF / "tod_case_estimates.csv")
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
            "annarbor_tc1_2021": "Kept aside to test the model (no usable permit data)", "auckland_aup_2016": "Strong scenario (whole-city result)",
            "la_toc_2017": "Little scenario (whole-city result)", "raleigh_new_bern_2024": "Left out: too new",
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
    sources = [
        {"scenario": "little", "study": "Los Angeles Transit Oriented Communities program (2017)",
         "citation": "Kestelman, Harvard Joint Center for Housing Studies working paper, 2025", "url": "https://www.jchs.harvard.edu/research-areas/working-papers/effects-transit-oriented-incentive-programs-evidence-los-angeles",
         "finding": "Housing growth rose 0.04 percentage points over six years (2017–2023), about 562 homes in a city of about 1.4 million homes. The program covered roughly 61% of the city's homes and required affordable units.",
         "status": "observed"},
        {"scenario": "typical", "study": "Zoning reforms in 1,136 US cities, 2005–2019",
         "citation": "Stacy and others, Urban Studies, 2023", "url": "https://doi.org/10.1177/00420980231159500",
         "finding": "Each reform that loosened land-use rules was followed by about 0.8% more postal addresses three or more years later (95% interval about +0.2% to +1.4%). Only 28 of the 96 loosening reforms changed floor area, density or height.",
         "status": "observed"},
        {"scenario": "strong", "study": "Auckland Unitary Plan (2016)",
         "citation": "Greenaway-McGrevy and Phillips, Journal of Urban Economics, 2023", "url": "https://doi.org/10.1016/j.jue.2023.103555",
         "finding": "21,808 extra homes permitted over 2016–2021, 4.1% of the city's 530,300 homes, after subtracting building moved from areas not upzoned. 75.2% of residential land was upzoned.",
         "status": "observed"},
    ]
    return {"cases": cases, "classification": classification, "strength_counts": {k: int(v) for k, v in counts.items()},
            "madison": madison, "sources": sources,
            "docs": [doc("docs/tod/GATE3_PACKET.md", "Gate 3 packet"), doc("docs/tod/MODEL.md", "Model"),
                     doc("docs/tod/CASE_RESULTS.md", "Comparison cases"), doc("docs/tod/MADISON_TEST_RESULTS.md", "Madison test"),
                     doc("docs/tod/research/NET_EFFECT_SOURCES.md", "Source check of the three studies")]}


# ---- pilots -------------------------------------------------------------------------------------
def corridor(agency_counties: list[str], areas: dict, sw: dict) -> dict:
    """Rail and rapid station areas in the given counties: their land, and their share of each place's addition.

    Within a place the model places homes in proportion to the extra floor area the law allows (coded cities) or
    to the estimated room for new homes (other places), so a corridor's share of a place's addition is its share
    of that measure."""
    sa = pd.read_csv(REF / "tod_station_areas.csv")
    m = sa[(sa["in_main"] == 1) & sa["county"].isin(agency_counties)]
    mt = {x["name"]: x for x in areas["munis"]}
    places = []
    add = {sc: [0.0] * 5 for sc in SCEN}
    for city, g in m.groupby("city"):
        if city not in mt:
            continue
        coded = bool(g["zoning_coded"].iloc[0])
        measure = "added_floor_area_sqft" if coded else "capacity_gain"
        rap = g[g["band"].str.startswith("rapid")]
        if rap.empty:
            continue
        share = float(rap[measure].sum() / g[measure].sum())
        mu = mt[city]
        for sc in SCEN:
            for i in range(5):
                add[sc][i] += mu["add_years"][sc][i] * share
        places.append({"name": city, "coded": coded, "acres": r(rap["acres"].sum(), 0), "eligible_acres": r(rap["eligible_acres"].sum(), 0),
                       "gain_acres": r(rap[rap[measure] > 0]["eligible_acres"].sum(), 0),
                       "existing_homes": r(rap["existing_homes"].sum(), 0), "share_of_place": r(share, 4),
                       "overlay_share": r(rap["acres_in_overlay"].sum() / rap["acres"].sum(), 4) if coded else None,
                       "add_typical": r(mu["add"]["typical"] * share, 4)})
    places.sort(key=lambda p: -p["acres"])
    return {"places": places, "add": {sc: r(sum(v), 4) for sc, v in add.items()}, "add_years": {sc: [r(v, 4) for v in vs] for sc, vs in add.items()},
            "acres": r(sum(p["acres"] for p in places), 0), "eligible_acres": r(sum(p["eligible_acres"] for p in places), 0),
            "gain_acres": r(sum(p["gain_acres"] for p in places), 0), "existing_homes": r(sum(p["existing_homes"] for p in places), 0)}


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
        "method": "The corridor figure is each place's extra homes times the corridor's share of the room the law adds in that place. Milwaukee's figure covers CONNECT 1 and The Hop streetcar together, because the land data do not separate the two lines.",
        "zoning_note": "Milwaukee's zoning rules near stops, including the 2025 \"Growing MKE\" changes, were entered rule by rule, so the extra floor area the law allows is measured for each piece of land.",
    })
    mad = mt["Madison city"]
    out.append({
        "slug": "madison-route-a", "title": "Madison: the Rapid Route A corridor", "view": "madison", "city": "Madison city",
        "line": "Madison Metro Rapid Route A (bus rapid transit, opened 22 September 2024)",
        "intro": "Rapid Route A is Madison's first bus rapid transit line, running east–west through downtown and the isthmus. Madison already has a transit-oriented development overlay (2023) along much of the route, so part of the corridor is close to what the modelled law would allow.",
        "stops": {"Rapid Route A stops": int(stops[(stops.agency == "City of Madison") & (stops.flag_a_rapid == 1)].shape[0])},
        "city_homes": int(nid.loc[mad["id"], "homes_2020"]), "city_homes_near": mad["homes_near"],
        "city_baseline": mad["baseline"], "city_add": mad["add"], "city_add_years": mad["add_years"],
        "corridor": corridor(["Dane County"], areas, sw),
        "method": "The corridor figure is each place's extra homes times the corridor's share of the room the law adds in that place: land within ½ mile of Rapid Route A's stations.",
        "zoning_note": "Madison's zoning rules, including its 2023 transit-oriented development overlay, were entered rule by rule. Where the overlay already allows as much as the law, the law adds nothing.",
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
        "intro": "Eau Claire is the check of whether the law transfers to Wisconsin's mid-size cities. Under the main definition the answer is no: no Eau Claire bus route runs every 15 minutes, so no Eau Claire home is near a qualifying stop and the law adds nothing there.",
        "stops": {"stops on 20-minute bus routes": int(((ecs.flag_c_20min == 1) & (ecs.flag_b_15min == 0)).sum()),
                  "stops on 15-minute bus routes or rapid transit": int(((ecs.flag_b_15min == 1) | (ecs.flag_a_rapid == 1)).sum())},
        "city_homes": int(nn["homes_2020"]), "city_homes_near": int(nn["homes_near_main"]), "homes_near_high": int(nn["homes_near_high"]),
        "city_baseline_all": r(ec["five_year_central"].sum(), 4),
        "high_case_acres": r(eca[eca["in_high"] == 1]["acres"].sum(), 0),
        "city_add": {sc: 0.0 for sc in SCEN},
        "reason": "No bus route in Eau Claire runs every 15 minutes at the morning peak, and the city has no rail or rapid transit. Its two busiest routes, 9 and 19, run every 20 minutes. They would count only if the law used the wider 20-minute definition.",
    })
    return out


# ---- validation ---------------------------------------------------------------------------------
def validate(sw: dict, areas: dict, pilots: list) -> dict:
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
    check("no addition below zero", all(v >= 0 for m in areas["munis"] for v in m["add"].values()), "every place and scenario")
    check("reference line equals the typical response", sw["reference_line"]["additional_total"] == next(x for x in sw["scenarios"] if x["id"] == "typical")["additional_total"], "AQ-051 G3-1")
    se = pd.read_csv(REF / "tod_model_sensitivities.csv")
    mm = se[(se["sizing"] == "net_effect") & (se["group"] == "main") & (se["scenario"] == "typical")].iloc[0]
    met = {m["id"]: m for m in areas["metros"]}
    check("Milwaukee metro matches the model", abs(met["milwaukee"]["add"]["typical"] - mm.milwaukee_metro_2027_2031) < 1, f"{mm.milwaukee_metro_2027_2031:,.1f}")
    check("Madison metro matches the model", abs(met["madison"]["add"]["typical"] - mm.madison_metro_2027_2031) < 1, f"{mm.madison_metro_2027_2031:,.1f}")
    for p in pilots[:2]:
        c = p["corridor"]
        check(f"{p['slug']}: corridor addition within its places' additions", all(0 <= x["share_of_place"] <= 1 for x in c["places"]), "shares between 0 and 1")
    check("Eau Claire has no homes near main-case stops", pilots[2]["city_homes_near"] == 0, "no 15-minute routes")
    return {"passed": sum(c["passed"] for c in checks), "failed": sum(not c["passed"] for c in checks), "checks": checks}


def main():
    hashes = [{"path": p, "sha256": sha256(ROOT / p)} for p in INPUTS]
    run_id = "tod-" + hashlib.sha256("".join(h["sha256"] for h in hashes).encode()).hexdigest()[:10]
    out = OUT_ROOT / run_id
    if OUT_ROOT.exists():
        for old in OUT_ROOT.iterdir():
            if old.is_dir() and old.name != run_id:
                shutil.rmtree(old)
    out.mkdir(parents=True, exist_ok=True)
    sw = build_statewide()
    areas = build_areas()
    pilots = build_pilots(areas, sw)
    val = validate(sw, areas, pilots)
    manifest = {
        "schema_version": 1, "run_id": run_id, "scenario_id": "tod", "title": "Wisconsin transit-oriented density law",
        "outcome": {"short": "Extra homes in issued building permits near major transit stops, compared with current law, Wisconsin, 2027–2031. Not completed homes.",
                    "long": "Housing units authorized by building permits, counted at permit issuance, all building sizes, in station areas: within ½ mile of rail and rapid transit stations and ¼ mile of bus routes running every 15 minutes. The law's addition is the number of extra homes permitted compared with current law.",
                    "rate_units": "extra homes permitted per 1,000 existing homes in the station areas", "count_units": "homes (housing units) in issued permits"},
        "dates": {"last_observed_year": 2025, "forecast_years": YEARS, "effective": "Stylized statewide law in effect 1 January 2027"},
        "vintages": [{"what": "National Transit Map (stops and routes)", "vintage": "compiled 23 September 2026"},
                     {"what": "Agency schedule files (frequencies)", "vintage": "2025–2026 service days"},
                     {"what": "Census 2020 homes by block", "vintage": "2020"},
                     {"what": "Census Building Permits Survey (current-law forecast)", "vintage": "2015–2025 annual"},
                     {"what": "Milwaukee and Madison parcels and zoning", "vintage": "2025–2026"}],
        "validation": val, "repo_url": REPO_URL, "inputs": hashes,
        "files": ["statewide.json", "areas.json", "map.json", "howsure.json", "why.json", "pilots.json"],
    }
    files = {"manifest.json": manifest, "statewide.json": sw, "areas.json": areas, "map.json": build_map(areas),
             "howsure.json": build_howsure(sw, areas), "why.json": build_why(), "pilots.json": pilots}
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
