"""Station-area model: three audit-requested checks of stage 0 (docs/tod/STATION_AREA_PLAN.md, LOCKED; audit section G).

1. Milwaukee placebo (pre-registered: no reform, so the method should show about 0). Pretend reform in 2019 at The Hop
   streetcar stops (opened November 2018). Reform lots: City of Milwaukee lots within 1 mile of a Hop stop. Comparison
   lots: City of Milwaukee lots within 1 mile of a Milwaukee County rapid-bus (BRT) stop and more than 1 mile from every
   Hop stop. Stops: reference/tod_stops.csv, flag_a_rapid == 1 (agency "City of Milwaukee" = The Hop; "Milwaukee
   County" = rapid bus); platforms within 150 m merged, as in the training builders. New homes: MPROP year built x
   units, residential land uses only (LAND_USE 88xx, not group 12; hotels 7011, rooming/dorm 7021/7041 and nursing
   8051/8052/8361 are not 88xx, so they are out), placed on the parcel outlines of data/raw/tod_capacity/
   v12_milwaukee.geojson by tax key; a tax key on two outlines counts once; stacked outlines are one lot. Existing homes:
   homes on records built before 2014 (unknown year counts as existing). Windows (year built): before 2014-2018; after
   2020-2024, and 2019-2023 as a second version. Owner fields are never read.
2. Comparison stops with their own TOD rezoning or TOD-type rule inside the case's windows: one row per comparison stop
   (yes / yes-late / yes-parking / no / unknown, with source), then stage 0 recomputed with comparison lots whose
   nearest stop is flagged "yes*" dropped (not reassigned), per affected case and the pooled average per band.
3. Honolulu comparison restricted to HART stations west of the downtown-Kaka'ako-Ala Moana core (Iwilei and every
   station east of it left out). The main run used all 19 other stations.

Effects are computed exactly as scripts/run_tod_station_model.py stage 0 (dates "permit_est": per-building events with
hand-check corrections): change in reform stops' rate minus change in comparison stops' rate, new homes per 1,000
existing homes a year and per 100 lot acres a year.

    .venv/bin/python scripts/run_tod_station_checks.py

Writes reference/tod_station_checks_*.csv (summaries, no parcel ids) and
data/processed/tod_station_area/checks_milwaukee_placebo_lots.parquet (local, lot level, no tax keys or owner fields).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware import geom_extra_station as X  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
import run_tod_station_model as M  # noqa: E402

CRS = 5070
QUARTER, HALF, MILE = 402.0, 805.0, 1609.0
OUT = ROOT / "data" / "processed" / "tod_station_area"
BANDS = M.BANDS
LOT_COLS = ["group", "band", "stop_id", "homes_existing", "homes_before_win", "homes_after_win", "in_reform_area",
            "implausible", "acres"]


# =========================================================================== shared: stage-0 effect for one case

def band_effects(D: pd.DataFrame, yb: int, ya: int) -> pd.DataFrame:
    """Same arithmetic as run_tod_station_model.case_effects, for one lot table already windowed."""
    D = D[~D.implausible.fillna(False).astype(bool)]
    g = D.groupby(["group", "band"]).agg(e=("homes_existing", "sum"), b=("homes_before_win", "sum"),
                                         a=("homes_after_win", "sum"), ac=("acres", "sum"), lots=("band", "size"))
    rows = []
    for band in BANDS:
        try:
            r, c = g.loc[("reform", band)], g.loc[("comparison", band)]
        except KeyError:
            rows.append({"band": band})
            continue
        dr = 1000 * (r.a / ya - r.b / yb) / r.e if r.e > 0 else np.nan
        dc = 1000 * (c.a / ya - c.b / yb) / c.e if c.e > 0 else np.nan
        pr = 100 * (r.a / ya - r.b / yb) / r.ac if r.ac > 0 else np.nan
        pc = 100 * (c.a / ya - c.b / yb) / c.ac if c.ac > 0 else np.nan
        rows.append({"band": band, "reform_change": dr, "comparison_change": dc, "effect_raw": dr - dc,
                     "effect_per_100_acres": pr - pc, "reform_homes": r.e, "comparison_homes": c.e,
                     "reform_lots": r.lots, "comparison_lots": c.lots,
                     "reform_new_before": r.b, "reform_new_after": r.a, "comparison_new_before": c.b, "comparison_new_after": c.a})
    return pd.DataFrame(rows)


_WIN: dict[str, pd.DataFrame] = {}


def windowed(case: str) -> pd.DataFrame:
    if case not in _WIN:
        D = pd.read_parquet(OUT / f"lots_{case}.parquet", columns=LOT_COLS)
        _WIN[case] = M.event_windows(case, D, "permit_est")
    return _WIN[case]


def case_effect(case: str, drop_stops: set | None = None) -> pd.DataFrame:
    D = windowed(case)
    if drop_stops:
        D = D[~((D.group == "comparison") & D.stop_id.isin(drop_stops))]
    yb, ya = M.windows(case)
    return band_effects(D, yb, ya).assign(case=case)


# =========================================================================== stop lists (rebuilt as in each builder)

def stops_for(case: str) -> pd.DataFrame:
    import build_tod_station_lot_table as B
    if case in ("la_toc_2017", "san_diego_2021"):
        box, st = ((-118.95, 33.70, -117.65, 34.35), "06") if case == "la_toc_2017" else ((-117.30, 32.53, -116.90, 32.95), "06")
        c = B.CASES[case]
        S = B.ntm_stations(box)
        S["place"] = B.place_of(S, st)
        S["group"] = np.where(S.place == c["reform_city"], "reform", np.where(S.place.isin(c["comparison_cities"]), "comparison", "other"))
        S = S[S.group != "other"].reset_index(drop=True)
        S["stop_id"] = np.arange(len(S))
        return S
    if case == "honolulu_2017":
        r = X.read_vector(B.RP / "honolulu" / "rail_stations.geojson", dst=CRS)
        S = pd.DataFrame({"stop_name": r.station_name_FEIS.values, "place": "Urban Honolulu", "x": r.x.values, "y": r.y.values})
        S["group"] = np.where(S.stop_name.str.contains("Waipahu Transit|West Loch"), "reform", "comparison")
        S["stop_id"] = np.arange(len(S))
        S["lon"] = X.transform(S.x.values, S.y.values, CRS, 4326)[0]
        return S
    if case.startswith("chicago"):
        from station_cases import chicago as CH
        return CH.stations()
    from station_cases import cluster_north as N, cluster_west as W
    if case in W.CASES:
        return W.stops(case, W.reform_area(case), W.coverage_poly(case))
    return N.stops_for(case)


def check_stops(case: str, S: pd.DataFrame) -> None:
    """The rebuilt list must give every lot's stop the same group as the stored lot table."""
    g = pd.read_parquet(OUT / f"lots_{case}.parquet", columns=["stop_id", "group"]).groupby("stop_id").group.first()
    bad = (S.set_index("stop_id").group.reindex(g.index) != g).sum()
    if bad:
        raise SystemExit(f"{case}: rebuilt stop list disagrees with the lot table on {bad} stops")


# =========================================================================== task 2: own TOD rezoning flags

def _src(*u):
    return "; ".join(u)


# (case prefix or "*", place, stop-name substring or "*") -> (flag, note, source). First match wins.
# flag: yes = station-area rezoning or TOD-type rule adopted inside the case's windows; yes-late = adopted in the last
# year of the after window; yes-parking = parking rule only; no = checked, nothing in the windows; unknown = not verified.
SRC = {
    "inglewood": "https://ceqanet.lci.ca.gov/2016041011 (Downtown Inglewood and Fairview Heights TOD Plan, adopted 1 Nov 2016)",
    "inglewood_wv": "https://ceqanet.lci.ca.gov/2017101068 (Westchester/Veterans TOD plan: draft EIR 2021; adoption not found)",
    "santa_monica": "https://www.santamonicalookout.com/ssm_site/the_lookout/news/News-2013/September-2013/09_12_2013_Santa_Monica_City_Council_Adopts_Bergamot_Area_Plan.html; https://www.smdp.com/santa-monica-city-council-approves-downtown-community-plan/ (Bergamot Area Plan Sep 2013; Downtown Community Plan Jul 2017)",
    "lb_downtown": "https://www.gruenassociates.com/?p=15280 (Long Beach Downtown Plan 2012)",
    "lb_midtown": "https://placeworks.com/portfolio/midtown-specific-plan/; https://patch.com/california/belmontshore/midtown-specific-plan-wins-scag-sustainability-award (Midtown Specific Plan 2016, Long Beach Blvd Blue Line corridor)",
    "duarte": "https://foothillgoldline.org/duarte/ (Duarte Station Specific Plan adopted 10 Dec 2013; amended 2019)",
    "azusa": "https://ceqanet.lci.ca.gov/2015021018 (Azusa TOD Specific Plan, adopted Oct/Nov 2015, both stations rezoned)",
    "monrovia": "https://www.monroviaca.gov/your-government/community-development/planning/zoning/specific-plans/arroyo-at-monrovia-station-specific-plan (site specific plans in the Station Square Transit Village: Ord. 2019-11, 127 Pomona Jan 2020; Station Square SP 2008)",
    "hawthorne": "https://ceqanet.lci.ca.gov/2016061043 (Green Line Mixed Use Specific Plan, adopted 10 Oct 2017, Crenshaw station)",
    "lynwood": "https://ceqanet.lci.ca.gov/2015121020 (Lynwood Transit Area Specific Plan adopted Sep 2016)",
    "pasadena": "https://www.cityofpasadena.net/planning/planning-division/community-planning/specific-plans/east-colorado-boulevard/; .../south-fair-oaks/ (East Colorado SP Feb-Jun 2022; South Fair Oaks SP Jul-Oct 2022)",
    "compton": "https://ceqanet.lci.ca.gov/2021090474 (Compton Station TOD Specific Plan, notice of determination 17 Nov 2022)",
    "compton_artesia": "https://planetizen.com/node/107067 (Artesia Station specific plan begun 2018; adoption not found)",
    "glendale": "https://ceqanet.lci.ca.gov/2016091026 (South Glendale Community Plan / Tropico Center Plan Jul 2018 = plan; Tropico TOD zoning project 2023, after window)",
    "burbank": "https://ceqanet.lci.ca.gov/2021050436; https://urbanize.la/post/burbank-launches-zoning-update-airport-adjacent-district (Downtown TOD and Golden State specific plans still drafts after 2022)",
    "culver": "https://www.culvercityobserver.com/story/2012/11/14/news/council-takes-step-to-develop-transit-zone/2685.html (first council step 2012; adoption not found)",
    "el_cajon": "https://elcajon.gov/your-government/departments/community-development/planning/transit-district-specific-plan (Transit District Specific Plan adopted 8 May 2018)",
    "santee": "https://cityofsanteeca.gov/planning/town-center-specific-plan (Town Center Specific Plan update adopted 12 Mar 2025)",
    "lemon_grove": "https://www.lemongrove.ca.gov/our-government/community-development-department/planning-division/advanced-planning/update-downtown-specific-plan/ (2018 draft never adopted; Downtown Village SP 2005)",
    "la_mesa": "https://ceqanet.lci.ca.gov/Project/2019059095 (Alvarado Specific Plan near 70th St; adoption not found)",
    "national_city": "https://nationalcityca.gov/home/showpublisheddocument/15465/636434273338470000 (Downtown Specific Plan amendment 2017-24A; content and adoption not confirmed)",
    "evanston": "plan file (STATION_AREA_PLAN.md step C, Chicago): Evanston cut TOD parking Sept 2017",
    "brookfield": "https://nita.illinois.gov/blog/2017/01/25/rta-helps-brookfield-stay-on-track-with-zoning-updates (form-based code for the three Metra station areas adopted Jan 2017)",
    "seattle_dt": "https://sccinsight.com/2017/04/10/downtownslu-mha-upzone-passes-law/ (Ord. 125291, Downtown/SLU MHA upzone, Apr 2017)",
    "seattle_cid": "https://www.theurbanist.org/2017/08/01/council-signs-off-on-cid-rezone-and-tackles-tower-spacing/ (Ord. 125371, CID rezone, Aug 2017)",
    "seattle_mha": "https://www.theurbanist.org/2019/01/14/citywide-mha/ (citywide MHA urban-village rezones incl. Columbia City and Rainier Beach, Mar 2019)",
    "redmond": "cluster_north.OWN_TOD (Redmond Overlake plan and zoning 2007-2011)",
    "mercer": "https://www.mercerisland.gov/sites/default/files/fileattachments/community/page/9321/ordinance_16c-06.pdf (Town Center code Ord. 16C-06, 2016: after the 2003-2014 window)",
    "seatac": "https://www.seatacwa.gov/government/city-departments/community-and-economic-development/planning-division/long-range-planning/south-154th-street-station-area-plan (S 154th St station area action plan Dec 2006; zoning not confirmed)",
    "portland_cc": "https://www.portland.gov/bps/cc2035/news/2018/7/11/central-city-2035-plan-effect (Central City 2035 zoning in effect Jul 2018)",
    "slc_sugar": "https://www.valleyjournals.com/2016/07/13/116895/streetcar-corridor-plan-to-limit-building-height (FB-SC/FB-SE form-based zones 2016: after the 2004-2015 window)",
    "denver_fox": "https://denverite.com/2018/06/19/denver-council-sets-stage-for-density-on-fox-island-but-some-question-affordable-housing-strategy/ (41st & Fox site rezonings to 8-12 stories, 2018-2019)",
    "charlotte_unc": "https://ui.charlotte.edu/story/city-work-owners-station-area-properties/ (campus covered by UNC Charlotte master plan 2010; city petition 2019-102 stops at the campus)",
    "hnl_apc": "https://www.honolulu.gov/tod/neighborhoods/aiea-pearl-city/ (Aiea-Pearl City TOD special district and zoning, Ord. 22-29/22-30, Oct 2022)",
    "hnl_halawa": "https://files.amlegal.com/pdffiles/Honolulu/ORD23-032.pdf (Halawa TOD special district Ord. 23-32, 2023: after window)",
    "hnl_alamoana": "https://www.honolulu.gov/tod/zoning-policies/ (Ala Moana TOD plan Sep 2021; special district zoning not adopted by 2022)",
    "hnl_kakaako": "https://dbedt.hawaii.gov/hcda/files/2012/11/Chapter-217-Mauka-Area-Rules-EFF-2011.11.11.pdf (HCDA Kaka'ako Mauka Area Rules, form-based, effective 11 Nov 2011)",
}

FLAGS = [
    # ---- Los Angeles County comparison cities (LA TOC windows 2011-2016 / 2018-2022)
    ("la_toc", "Inglewood", "Westchester", "unknown", "TOD plan drafted 2021; adoption not found", SRC["inglewood_wv"]),
    ("la_toc", "Inglewood", "*", "yes", "Downtown Inglewood & Fairview Heights TOD plan and zoning, Nov 2016", SRC["inglewood"]),
    ("la_toc", "Santa Monica", "Downtown", "yes", "Downtown Community Plan Jul 2017", SRC["santa_monica"]),
    ("la_toc", "Santa Monica", "Bergamot", "yes", "Bergamot Area Plan Sep 2013", SRC["santa_monica"]),
    ("la_toc", "Santa Monica", "*", "unknown", "", ""),
    ("la_toc", "Long Beach", "Wardlow", "unknown", "", ""),
    ("la_toc", "Long Beach", "Anaheim", "yes", "Midtown Specific Plan 2016", SRC["lb_midtown"]),
    ("la_toc", "Long Beach", "Pacific Coast", "yes", "Midtown Specific Plan 2016", SRC["lb_midtown"]),
    ("la_toc", "Long Beach", "Willow", "yes", "Midtown Specific Plan 2016", SRC["lb_midtown"]),
    ("la_toc", "Long Beach", "*", "yes", "Downtown Plan 2012", SRC["lb_downtown"]),
    ("la_toc", "Duarte", "*", "yes", "Duarte Station Specific Plan Dec 2013 (amended 2019)", SRC["duarte"]),
    ("la_toc", "Azusa", "*", "yes", "Azusa TOD Specific Plan 2015", SRC["azusa"]),
    ("la_toc", "Monrovia", "*", "yes", "site specific plans in the station's transit village 2019-2020", SRC["monrovia"]),
    ("la_toc", "Hawthorne", "*", "yes", "Green Line Mixed Use Specific Plan Oct 2017", SRC["hawthorne"]),
    ("la_toc", "Lynwood", "*", "yes", "Lynwood Transit Area Specific Plan Sep 2016", SRC["lynwood"]),
    ("la_toc", "Pasadena", "Allen", "yes-late", "East Colorado Specific Plan 2022", SRC["pasadena"]),
    ("la_toc", "Pasadena", "Fillmore", "yes-late", "South Fair Oaks Specific Plan 2022", SRC["pasadena"]),
    ("la_toc", "Pasadena", "*", "unknown", "", ""),
    ("la_toc", "Compton", "Artesia", "unknown", "specific plan begun 2018; adoption not found", SRC["compton_artesia"]),
    ("la_toc", "Compton", "*", "yes-late", "Compton Station TOD Specific Plan, Nov 2022", SRC["compton"]),
    ("la_toc", "Glendale", "*", "no", "Tropico plan 2018 is a plan; TOD zoning 2023", SRC["glendale"]),
    ("la_toc", "Burbank", "*", "no", "TOD specific plans still drafts", SRC["burbank"]),
    ("la_toc", "Culver City", "*", "unknown", "TOD zone begun 2012; adoption not found", SRC["culver"]),
    ("la_toc", "*", "*", "unknown", "", ""),
    # ---- San Diego County comparison cities (2015-2020 / 2021-2025)
    ("san_diego", "El Cajon", "El Cajon Station", "yes", "Transit District Specific Plan May 2018", SRC["el_cajon"]),
    ("san_diego", "Santee", "*", "yes-late", "Town Center Specific Plan update Mar 2025", SRC["santee"]),
    ("san_diego", "Lemon Grove", "Depot", "no", "2018 downtown plan never adopted", SRC["lemon_grove"]),
    ("san_diego", "La Mesa", "70th", "unknown", "Alvarado Specific Plan; adoption not found", SRC["la_mesa"]),
    ("san_diego", "National City", "8th", "unknown", "downtown plan amendment 2017; content unclear", SRC["national_city"]),
    ("san_diego", "*", "*", "unknown", "", ""),
    # ---- Cook County suburbs (chicago_2015: 2009-2020; chicago_2022: 2016-2025)
    ("chicago", "Evanston", "*", "yes-parking", "TOD parking cut Sept 2017 (parking only)", SRC["evanston"]),
    ("chicago", "Brookfield", "*", "yes", "form-based code for its three Metra station areas, Jan 2017", SRC["brookfield"]),
    ("chicago", "*", "*", "unknown", "", ""),
    # ---- Seattle (Othello 2006-2017; Mount Baker 2008-2019) and Bellevue (2003-2014)
    ("seattle", "Seattle", "Westlake", "yes", "Downtown MHA upzone Apr 2017", SRC["seattle_dt"]),
    ("seattle", "Seattle", "Symphony", "yes", "Downtown MHA upzone Apr 2017", SRC["seattle_dt"]),
    ("seattle", "Seattle", "Pioneer Square", "yes", "Downtown MHA upzone Apr 2017", SRC["seattle_dt"]),
    ("seattle", "Seattle", "Int'l Dist", "yes", "CID rezone Aug 2017", SRC["seattle_cid"]),
    ("seattle_mount_baker", "Seattle", "Columbia City", "yes-late", "MHA urban-village rezone Mar 2019", SRC["seattle_mha"]),
    ("seattle_mount_baker", "Seattle", "Rainier Beach", "yes-late", "MHA urban-village rezone Mar 2019", SRC["seattle_mha"]),
    ("seattle_othello", "Seattle", "Columbia City", "no", "MHA rezone Mar 2019, after window", SRC["seattle_mha"]),
    ("seattle_othello", "Seattle", "Rainier Beach", "no", "MHA rezone Mar 2019, after window", SRC["seattle_mha"]),
    ("seattle", "SeaTac", "*", "unknown", "", ""),
    ("seattle", "Tukwila", "*", "unknown", "SeaTac's S 154th St station area plan Dec 2006; zoning not confirmed", SRC["seatac"]),
    ("bellevue", "Redmond", "*", "yes", "Overlake plan and zoning 2007-2011", SRC["redmond"]),
    ("bellevue", "Mercer Island", "*", "unknown", "Town Center code 2016 is after window; earlier not checked", SRC["mercer"]),
    ("*", "*", "*", "unknown", "", ""),
]
# in-city comparison cases (one place): stop-name rules
CITY_FLAGS = {
    "portland_2020": [(n, "yes", "Central City 2035 zoning Jul 2018", SRC["portland_cc"]) for n in
                      ("Yamhill", "Union Station", "NW 5th", "NW 6th & Davis", "Oak/", "Pioneer Courthouse", "Skidmore", "Old Town")],
    "slc_2010": [(n, "no", "Sugar House form-based zones 2016, after window", SRC["slc_sugar"]) for n in ("Fairmont", "Sugarmont")],
    "denver_2018": [("41st & Fox", "yes", "site rezonings to 8-12 stories 2018-2019", SRC["denver_fox"])],
    "charlotte_2019": [("UNC Charlotte", "no", "campus master plan 2010; outside city TOD petition", SRC["charlotte_unc"])],
    "honolulu_2017": [("Kalauao", "yes-late", "Aiea-Pearl City TOD zoning Oct 2022", SRC["hnl_apc"]),
                      ("Pearl Highlands", "yes-late", "Aiea-Pearl City TOD zoning Oct 2022", SRC["hnl_apc"]),
                      ("Hālawa", "no", "Halawa TOD district 2023, after window", SRC["hnl_halawa"]),
                      ("Ala Moana", "no", "TOD plan 2021; zoning not adopted by 2022", SRC["hnl_alamoana"]),
                      ("Kaka'ako", "yes", "HCDA Mauka Area Rules Nov 2011", SRC["hnl_kakaako"]),
                      ("Civic Center", "yes", "HCDA Mauka Area Rules Nov 2011", SRC["hnl_kakaako"])],
}


def flag_of(case: str, place: str, name: str) -> tuple[str, str, str]:
    for n, f, note, src in CITY_FLAGS.get(case, []):
        if n in name:
            return f, note, src
    for cp, pl, nm, f, note, src in FLAGS:
        if (cp == "*" or case.startswith(cp)) and (pl == "*" or pl == place) and (nm == "*" or nm in name):
            return f, note, src
    return "unknown", "", ""


FLAG_CASES = ["la_toc_2017", "san_diego_2021", "honolulu_2017", "chicago_2015", "chicago_2022", "seattle_othello_2012",
              "seattle_mount_baker_2014", "bellevue_belred_2009", "stpaul_2011", "charlotte_2019", "denver_2018",
              "portland_2020", "austin_2009", "slc_2010"]


def task2() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    for case in FLAG_CASES:
        S = stops_for(case)
        check_stops(case, S)
        lots = pd.read_parquet(OUT / f"lots_{case}.parquet", columns=["stop_id", "group"])
        n = lots[lots.group == "comparison"].stop_id.value_counts()
        for sid, k in n.items():
            s = S.set_index("stop_id").loc[sid]
            place = str(s.get("place", "")) if pd.notna(s.get("place", "")) else ""
            f, note, src = flag_of(case, place, str(s.stop_name))
            rows.append({"case": case, "stop_id": int(sid), "stop_name": s.stop_name, "place": place,
                         "comparison_lots": int(k), "own_tod_rule_in_window": f, "note": note, "source": src})
    T = pd.DataFrame(rows)
    T.drop(columns="stop_id").to_csv(REFERENCE / "tod_station_checks_comparison_flags.csv", index=False)

    eff = []
    for case, g in T.groupby("case"):
        drop_all = set(g.loc[g.own_tod_rule_in_window.str.startswith("yes"), "stop_id"])
        drop_core = set(g.loc[g.own_tod_rule_in_window == "yes", "stop_id"])
        if not drop_all:
            continue
        for ver, ds in (("main run", None), ("drop yes (all kinds)", drop_all), ("drop yes (core only)", drop_core)):
            if ver != "main run" and not ds:
                continue
            eff.append(case_effect(case, ds).assign(version=ver, stops_dropped=len(ds or ())))
    E = pd.concat(eff, ignore_index=True)

    # pooled per band: the 16 places of the main run, the affected cases replaced
    base = pd.read_csv(REFERENCE / "tod_station_area_effects_by_city.csv")
    pooled = []
    for ver in ("main run", "drop yes (all kinds)", "drop yes (core only)"):
        C = base.copy()
        if ver != "main run":
            for case, g in E[E.version == ver].groupby("case"):
                for _, r in g.iterrows():
                    m = (C.city == case) & (C.band == r.band)
                    C.loc[m, ["effect_raw", "effect_per_100_acres"]] = [r.effect_raw, r.effect_per_100_acres]
        for col in ("effect_raw", "effect_per_100_acres"):
            P = M.pooled(C, col)
            pooled.append(P.assign(version=ver, measure=col))
    P = pd.concat(pooled, ignore_index=True)
    return T, E, P


# =========================================================================== task 3: Honolulu west-of-core comparison

def task3() -> pd.DataFrame:
    S = stops_for("honolulu_2017")
    check_stops("honolulu_2017", S)
    cut = S.loc[S.stop_name.str.startswith("Iwilei"), "lon"].iloc[0]
    core = set(S.loc[(S.group == "comparison") & (S.lon >= cut - 1e-9), "stop_id"])
    names = sorted(S.loc[S.stop_id.isin(core), "stop_name"].str.replace(" Station", ""))
    out = pd.concat([case_effect("honolulu_2017").assign(version="main run: all 19 other stations"),
                     case_effect("honolulu_2017", core).assign(version=f"west of core only ({19 - len(core)} stations; drops {', '.join(names)})")])
    return out


# =========================================================================== task 1: Milwaukee placebo

def mke_stops() -> tuple[np.ndarray, np.ndarray]:
    """Station points ((n, 2), CRS 5070) of the Hop streetcar and the BRT line, platforms within 150 m merged."""
    s = pd.read_csv(REFERENCE / "tod_stops.csv", dtype={"stop_id": str})
    s = s[s.flag_a_rapid == 1]

    def merged(agency: str) -> np.ndarray:
        a = s[s.agency == agency]
        x, y = X.transform(a.lon.values, a.lat.values, 4326, CRS)
        cx, cy, _ = X.merge_within(x, y, 75.0)
        return np.c_[cx, cy]
    return merged("City of Milwaukee"), merged("Milwaukee County")


def mke_lots() -> pd.DataFrame:
    cols = ["TAXKEY", "YR_BUILT", "NR_UNITS", "LAND_USE", "LAND_USE_GP"]          # no owner fields
    m = pd.read_csv(RAW / "milwaukee_mprop" / "mprop.csv", dtype=str, usecols=cols).drop_duplicates("TAXKEY")
    res = m.LAND_USE.fillna("").str.startswith("88") & (m.LAND_USE_GP != "12")
    homes = np.where(res, pd.to_numeric(m.NR_UNITS, errors="coerce").fillna(0), 0.0)
    yb = pd.to_numeric(m.YR_BUILT, errors="coerce")
    yb = yb.where(yb > 1800)
    m = pd.DataFrame({"TAXKEY": m.TAXKEY, "homes": homes, "yb": yb.values})
    v = X.read_vector(RAW / "tod_capacity" / "v12_milwaukee.geojson", dst=CRS, columns=["PARCELID", "PLACENAME"])
    v = v[v.PLACENAME == "CITY OF MILWAUKEE"]
    v = v.merge(m, left_on="PARCELID", right_on="TAXKEY", how="left")
    v.loc[v.TAXKEY.notna() & v.duplicated("PARCELID"), "homes"] = 0.0          # a tax key on two outlines counts once
    v["homes"] = v.homes.fillna(0.0)
    log = {"mprop_res_homes_2014_2024": float(m.homes[m.yb.between(2014, 2024)].sum()),
           "placed_res_homes_2014_2024": float(v.homes[v.yb.between(2014, 2024)].sum())}
    cols = {"existing": ~(v.yb >= 2014), "b1418": v.yb.between(2014, 2018), "a2024": v.yb.between(2020, 2024),
            "a1923": v.yb.between(2019, 2023)}
    for k, msk in cols.items():
        v[k] = np.where(msk, v.homes, 0.0)
    v["_wkb"] = X.outline_keys(list(v.geometry))          # equal exactly when the outlines are (as WKB)
    v = v[v._wkb.notna()]
    L = v.groupby("_wkb", sort=False).agg(**{k: (k, "sum") for k in cols}, geometry=("geometry", "first")).reset_index(drop=True)
    L["acres"] = X.areas(list(L.geometry)) / 4046.8564224
    L["ptx"], L["pty"] = X.interior_points(list(L.geometry))
    return L, log


def task1() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    hop, brt = mke_stops()
    L, log = mke_lots()
    xy = np.c_[L.ptx.values, L.pty.values]
    dh = pd.Series(cKDTree(hop).query(xy)[0], index=L.index)
    db = pd.Series(cKDTree(brt).query(xy)[0], index=L.index)
    grp = np.where(dh <= MILE, "reform", np.where(db <= MILE, "comparison", ""))
    dist = np.where(grp == "reform", dh, db)
    D = pd.DataFrame({"group": grp, "dist_m": dist, "homes_existing": L.existing, "acres": L.acres,
                      "b": L.b1418, "a2024": L.a2024, "a1923": L.a1923, "x": L.ptx, "y": L.pty})
    D = D[D.group != ""].copy()
    D["band"] = pd.cut(D.dist_m, [-1, QUARTER, HALF, MILE], labels=BANDS).astype(str)
    D["implausible"] = False
    D.reset_index(drop=True).to_parquet(OUT / "checks_milwaukee_placebo_lots.parquet")
    log.update({"hop_stations": len(hop), "brt_stations": len(brt), "lots": len(D)})
    R = []
    for ver, col in (("after 2020-2024", "a2024"), ("after 2019-2023", "a1923")):
        X = D.assign(homes_before_win=D.b, homes_after_win=D[col])
        R.append(band_effects(X, 5, 5).assign(version=ver))
    R = pd.concat(R, ignore_index=True)

    # spread of the 16 training places' effects (main run)
    base = pd.read_csv(REFERENCE / "tod_station_area_effects_by_city.csv")
    spread = []
    for band, g in base.groupby("band"):
        for col in ("effect_raw", "effect_per_100_acres"):
            v = g[col].dropna()
            mk = R[(R.version == "after 2020-2024") & (R.band == band)][col].iloc[0]
            spread.append({"band": band, "measure": col, "places": len(v), "min": v.min(), "p25": v.quantile(.25),
                           "median": v.median(), "p75": v.quantile(.75), "max": v.max(), "sd": v.std(),
                           "milwaukee": mk, "milwaukee_share_of_places_below": (v < mk).mean(),
                           "milwaukee_in_sd_units": mk / v.std()})
    return R, pd.DataFrame(spread), log


# =========================================================================== main

def main() -> None:
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 70)
    keep = ["band", "reform_change", "comparison_change", "effect_raw", "effect_per_100_acres"]

    R, Sp, log = task1()
    R.round(3).to_csv(REFERENCE / "tod_station_checks_milwaukee_placebo.csv", index=False)
    Sp.round(3).to_csv(REFERENCE / "tod_station_checks_milwaukee_vs_training.csv", index=False)
    print("== Task 1: Milwaukee placebo", json.dumps(log))
    print(R[["version"] + keep + ["reform_homes", "comparison_homes", "reform_new_before", "reform_new_after",
                                  "comparison_new_before", "comparison_new_after"]].round(2).to_string(index=False))
    print(Sp.round(2).to_string(index=False))

    H = task3()
    H.round(3).to_csv(REFERENCE / "tod_station_checks_honolulu_comparison.csv", index=False)
    print("\n== Task 3: Honolulu")
    print(H[["version"] + keep + ["comparison_homes", "comparison_lots"]].round(2).to_string(index=False))

    T, E, P = task2()
    E.round(3).to_csv(REFERENCE / "tod_station_checks_flagged_comparison_effects.csv", index=False)
    P.round(3).to_csv(REFERENCE / "tod_station_checks_flagged_comparison_pooled.csv", index=False)
    print("\n== Task 2: flags (comparison stops by case)")
    print(T.groupby(["case", "own_tod_rule_in_window"]).agg(stops=("stop_name", "size"), lots=("comparison_lots", "sum")).to_string())
    print(T[T.own_tod_rule_in_window != "unknown"][["case", "place", "stop_name", "own_tod_rule_in_window", "note"]].to_string(index=False))
    print(E[["case", "version", "stops_dropped"] + keep].round(2).to_string(index=False))
    print(P[["version", "measure", "band", "cities", "average", "loo_low", "loo_high", "median"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
