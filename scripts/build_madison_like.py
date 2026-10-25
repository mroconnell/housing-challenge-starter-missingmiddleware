"""Build the Madison-like cities tables (Gate 3 add-on, owner question 2026-10-25).

    uv run python scripts/build_madison_like.py            # write reference/madison_like_*.csv
    uv run python scripts/build_madison_like.py --print    # also print the main tables

Inputs (read only):
    data/raw/census_acs5_2024_tbsf/acsdt5y2024-b25024.dat           one-unit detached homes
    data/raw/census_acs5_2024_tbsf_market/acsdt5y2024-b25077.dat    median home value
    data/raw/madison_like/census_place_codes/st*_place2020.txt     Census 2020 place codes
    data/raw/madison_like/ipeds/HD2023.csv                          IPEDS institutions (flag only)
    data/raw/statewide_states/wa/ofm_april1_postcensal_permits_1990-present.xlsx
    data/raw/statewide_states/or/hb4006_*.pdf                       DLCD HB 4006 (pdftotext -layout)
    data/processed/comparison_ca/hcd_apr_a2_juris_year_unitcat.csv  (scripts/build_ca_comparison_data.py)
    data/processed/comparison_ca/adu_compilation_2012_2019.csv      (same)
    data/raw/hcd_apr_a2/tablea2.csv                                 APN-level rows for the new-house share
    reference/other_cities_annual.csv                               five-city new-house counts
Outputs (aggregates only): reference/madison_like_*.csv
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from missing_middleware.comparison import madison_like as ml  # noqa: E402

RAW = ROOT / "data" / "raw"
REF = ROOT / "reference"
CA = ROOT / "data" / "processed" / "comparison_ca"
ML = RAW / "madison_like"

OFM = RAW / "statewide_states" / "wa" / "ofm_april1_postcensal_permits_1990-present.xlsx"
OFM_SRC = "OFM ofm_april1_postcensal_permits_1990-present.xlsx, 'Permitted Accessory Dwelling units', estimate year (Apr 2 prior year - Apr 1)"
DLCD_PDFS = ["hb4006_167053.pdf", "hb4006_167059.pdf", "hb4006_167065.pdf", "hb4006_167071.pdf",
             "hb4006_167078.pdf", "hb4006_274745.pdf"]
DLCD_YEARS = {"hb4006_167078.pdf": 2022, "hb4006_274745.pdf": 2023}  # from PDF titles
RI_EOH = {  # EOH annual ADU reports, municipal attachment (2026 report for 2024-2025; 2025 report for 2023)
    "Warwick": {2023: 2, 2024: 7, 2025: 13},
    "Cranston": {2023: 4, 2024: 4, 2025: 6},
}
RI_SRC = ("RI EOH ADU annual reports: 2026 (https://housing.ri.gov/media/3571/download, Attachment 1, 2024-2025) and "
          "2025 (housing.ri.gov ADU Report 2025.pdf, 2023); self-reported; 2024 differs between reports (Warwick 10 vs 7, Cranston 3 vs 4); later report used")

# Local ADU rule changes (research 2026-10-25; V = verified on an official page, L = source_lead).
# own = city's own initiative; state = state-compliance ordinance; mixed = both.
LOCAL_REFORMS = {
    "Spokane": dict(
        local_reform_in_window=True,
        own="2021-11-15 C36132 ADU permit fee waiver near Centers & Corridors (V vote, L amount; to 2024-12-31); "
            "2022-08-07 C36225 owner occupancy removed, detached cap 600->975 sq ft, no parking for studio/1-bed (V); "
            "2024-01-01 C36459 FAR removed, ADU footprint ~1,100 sq ft (V/L)",
        state="2025-07-11 C36696 HB 1337 compliance, 2 ADUs per lot, 1,000 sq ft (V); state deadline 2026-12-31",
        note="City reform came one year before HB 1337 year 1; rise in EY2023 precedes the state law"),
    "Spokane Valley": dict(
        local_reform_in_window=False,
        own="none liberalizing 2015-2026; 2023 proposal to drop owner occupancy recommended for denial 6-0 (V)",
        state="HB 1337 compliance pending (draft to council 2026-10-20; deadline 2026-12-31) (V)",
        note="Owner occupancy + deed restriction + 1 extra parking space still required; state law not yet binding"),
    "Tacoma": dict(
        local_reform_in_window=True,
        own="2019-05-01 Ord. 28576: detached ADUs in single-family zones, owner occupancy and parking removed (V); "
            "~2025-02 pre-approved DADU plans (V)",
        state="2025-02-01 Ord. 28986 Home in Tacoma Phase 2 (mixed own + HB 1110/1337) (V); state deadline 2025-06-30",
        note="Own 2019 reform falls in the before window; state-compliance code from EY2026"),
    "Vancouver": dict(
        local_reform_in_window=False,
        own="2017-09-06 M-4209 owner occupancy and parking removed (V dates; L details) - before the window; "
            "2022-07-27 M-4377 amended ch. 20.810, ADU content not found",
        state="2024-09-09 M-4455 interim HB 1337 compliance: 2 ADUs, 1,000 sq ft, no parking (V); permanent M-4533 2026-07-31",
        note="Rules were already liberal from 2017; the in-window change is the state-compliance interim ordinance"),
    "Yakima": dict(
        local_reform_in_window=True,
        own="2019-12-03 Ord. 2019-044 ADU allowed on all single-family lots, 1,000 sq ft (V); 2022-06-05 Ord. 2022-011 (V); "
            "2023-06 Ord. 2023-026 site-plan exemption (V/L)",
        state="HB 1337 compliance pending (deadline 2026-12-31) (V)",
        note="Own reforms 2019-2023; state law not yet binding"),
    "Eugene": dict(
        local_reform_in_window=True,
        own="2019-01-01 Res. 5254 100% transportation SDC credit for ADUs (V); ~2021-09 pre-approved plans (V/L); "
            "2023-09-20 credit cap removed (V)",
        state="2018-06-11 Ord. 20594 (remanded); 2020-02-22 Ord. 20625 owner occupancy and parking removed; "
              "2021-09-17 Ord. 20659 final SB 1051 compliance (V)",
        note="State compliance and own fee credit overlap in 2019-2021"),
    "Salem": dict(
        local_reform_in_window=True,
        own="2017-08-09 Ord. Bill 10-17 first allowed ADUs citywide, no parking (V); 2019-07-01 full SDC waiver for ADUs (V)",
        state="2022-03-16 Ord. 13-21 middle housing; city says ADU rules already compliant (V)",
        note="ADU rules are the city's own (2017); SDC waiver from 2019 = year 1"),
    "Medford": dict(
        local_reform_in_window=True,
        own="2020-12-01 50% ADU SDC cut (V)",
        state="2018-12-20 Ord. 2018-132 ADU rewrite, no added parking (mixed, V); 2022-06-30 Ord. 2022-60 middle housing (V)",
        note="SB 1051 compliance late 2018 plus own fee cut from Dec 2020"),
    "Gresham": dict(
        local_reform_in_window=False,
        own="2020-11-05 Ord. 1813 amended ADU section, content not read (V date)",
        state="2018-10-18 Ord. 1786 SB 1051 compliance, 1 extra parking space still required (V); 2022-06-16 Ord. 1830 (V)",
        note="State-compliance ordinances only (one 2020 amendment of unknown content)"),
    "Warwick": dict(
        local_reform_in_window=False,
        own="none found (EOH answers 'None' 2024, 'N/A' 2025) (V)",
        state="July 2024 zoning-board handout applying the 2024 state law by right (V)",
        note="State-driven only"),
    "Cranston": dict(
        local_reform_in_window=False,
        own="none before 2024 (legacy family-apartment special permit) (V)",
        state="2024-06-25 city guidance applying state law (V); 2026-01-21 Ord. 2026-2 code brought in line (V)",
        note="State-driven only"),
}
CA_REFORM_NOTE = ("California cities: post-2017 ADU ordinances are state-compliance ordinances; HCD received date where "
                  "known; own-initiative reforms not separately researched")


OTHER_HOMES = {"portland": 160807, "denver": 145528, "minneapolis": 84075}  # ACS 2020-2024 B25024_002 (OTHER_CITIES.md)
REFORM_TESTS = [  # (city, reform, kind, before years, after years)
    ("portland", "SDC waiver for ADUs (2010)", "local", (2005, 2009), (2011, 2015)),
    ("portland", "Residential Infill Project + HB 2001 rules (2021-22)", "local + state", (2019, 2020), (2022, 2025)),
    ("denver", "citywide ADUs (2024-12-16)", "local", (2016, 2023), (2025, 2025)),
    ("minneapolis", "owner occupancy removed (2021)", "local", (2017, 2020), (2021, 2025)),
    ("ca_madison_like_pooled", "2020 state ADU package (AB 68 / SB 13 / AB 881)", "state", (2018, 2019), (2020, 2025)),
]
SHARE_WINDOWS = dict(ml.OTHER_CITY_WINDOWS)


def lot_split_all(a2: pd.DataFrame, cac: pd.DataFrame, holdout: set, homes_by_geo: dict):
    """AQ-039 split for Portland, Denver, Minneapolis (permit + demolition open data) and the
    Madison-like California cities (APR demolished-units field)."""
    from missing_middleware.comparison import other_cities as oc
    pdx = pd.read_csv(RAW / "portland_res_permits" / "residential_building_permits.csv", dtype=str, encoding="utf-8-sig")
    pdx_demo = pd.read_csv(ML / "portland_demolition" / "residential_demolition_permits.csv", dtype=str, encoding="utf-8-sig")
    den = pd.read_csv(RAW / "denver_rescon_permits" / "residential_construction_permits.csv", dtype=str)
    den["DATE_ISSUED"] = pd.to_numeric(den["DATE_ISSUED"], errors="coerce")
    den_demo = pd.read_csv(ML / "denver_demolition" / "demolition_permits.csv", dtype=str)
    msp = pd.read_csv(RAW / "minneapolis_ccs_permits" / "ccs_permits_res_adu_text.csv", dtype=str)
    msp["issueDate"] = pd.to_numeric(msp["issueDate"], errors="coerce")
    msp_new = pd.read_csv(ML / "minneapolis_ccs" / "res_new_permits.csv", dtype=str)
    msp_wreck = pd.read_csv(ML / "minneapolis_ccs" / "wrecking_permits.csv", dtype=str)
    city_sets = {}
    p_adu = oc.classify_portland(pdx)
    city_sets["portland"] = (p_adu, *ml.lot_split_portland(p_adu, pdx, pdx_demo))
    d_adu = oc.classify_denver(den)
    city_sets["denver"] = (d_adu, *ml.lot_split_denver(d_adu, den, den_demo))
    m_adu = oc.classify_minneapolis(msp)
    city_sets["minneapolis"] = (m_adu, *ml.lot_split_minneapolis(m_adu, msp, msp_new, msp_wreck))
    series, rows = [], []
    for city, (adus, nh, houses) in city_sets.items():
        existing = adus[adus["counted"]].assign(units=adus["adu_units"])
        ser = ml.lot_series(nh, houses, existing, OTHER_HOMES[city]).assign(city=city)
        series.append(ser)
        y0, y1 = SHARE_WINDOWS[city]
        w = ser[ser["year"].between(y0, y1)]
        rows.append(_lot_row(city, y0, y1, w, "permit open data + demolition permits on the same parcel"
                             + (" or address" if city == "portland" else "")))
    # California Madison-like cities
    adu, sfd = ml.lot_split_apr(a2)
    adu = adu.assign(adu_units=adu["bp_units"])
    sfd = sfd.assign(house_units=sfd["bp_units"])
    name_geo = {n.upper(): g for n, g in zip(cac["name"], cac["geo_id"])}
    ca_series = []
    for j, g in adu.groupby("juris_name"):
        geo = name_geo[j]
        nh = g[g["lot"] != "existing"]
        ex = g[g["lot"] == "existing"].assign(units=lambda x: x["bp_units"])
        ser = ml.lot_series(nh, sfd[sfd["juris_name"] == j], ex, homes_by_geo[geo], house_units_col="house_units")
        ser["city"] = j.title()
        ser["ca_holdout"] = geo[-7:] in holdout
        ca_series.append(ser)
        rows.append(_lot_row(j.title(), 2018, 2025, ser, "HCD APR A2: demolished/destroyed units on the same APN within +/- 1 report year"))
    ca = pd.concat(ca_series, ignore_index=True)
    series.append(ca)
    pooled = ca[~ca["ca_holdout"]].groupby("year").sum(numeric_only=True).reset_index()
    pooled["homes"] = sum(homes_by_geo[name_geo[c.upper()]] for c in ca.loc[~ca["ca_holdout"], "city"].unique())
    keep = ~ca["ca_holdout"] & (ca["city"] != "Lancaster")
    pooled_ex = ca[keep].groupby("year").sum(numeric_only=True).reset_index()
    pooled_ex["homes"] = sum(homes_by_geo[name_geo[c.upper()]] for c in ca.loc[keep, "city"].unique())
    tests = []
    for city, reform, kind, before, after in REFORM_TESTS + [
            ("ca_madison_like_pooled_ex_lancaster", "2020 state ADU package (AB 68 / SB 13 / AB 881)", "state", (2018, 2019), (2020, 2025))]:
        ser = {"ca_madison_like_pooled": pooled, "ca_madison_like_pooled_ex_lancaster": pooled_ex}.get(city)
        if ser is None:
            ser = next(s for s in series if (s.get("city") == city).all())
        tests.append(dict(city=city, reform=reform, reform_kind=kind, **ml.reform_compare(ser, before, after)))
    return pd.DataFrame(rows), pd.concat(series, ignore_index=True), pd.DataFrame(tests)


def _lot_row(city, y0, y1, w, method):
    t, v, u = (w[f"new_house_adus_{k}"].sum() for k in ("teardown", "vacant", "unclassified"))
    e = w["existing_lot_adus"].sum()
    allu = t + v + u + e
    return dict(city=city, first_year=y0, last_year=y1, existing_lot_adus=e, new_house_adus_teardown=t,
                new_house_adus_vacant=v, new_house_adus_unclassified=u, all_adus=allu,
                vacant_share=v / allu if allu else float("nan"),
                vacant_share_upper=(v + u) / allu if allu else float("nan"),
                new_house_share=(t + v + u) / allu if allu else float("nan"),
                condo_driven=city in ml.CONDO_DRIVEN, method=method)


def pdf_text(pdf: Path) -> str:
    return subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True,
                          check=True).stdout


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", action="store_true")
    args = ap.parse_args()

    # --- 0. screen -----------------------------------------------------------
    places = ml.read_place_codes(sorted((ML / "census_place_codes").glob("st*_place2020.txt")))
    prefixes = tuple(f"1600000US{f}" for f in ml.STATES)
    homes = ml.read_acs_values(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25024.dat", "B25024_E002", prefixes)
    value = ml.read_acs_values(RAW / "census_acs5_2024_tbsf_market" / "acsdt5y2024-b25077.dat", "B25077_E001", prefixes)
    scr = ml.screen(places, homes, value)
    near = scr[scr["homes"] >= 15_000].copy()
    cities = scr[scr["madison_like"]].copy()
    flags = ml.university_flags(ML / "ipeds" / "HD2023.csv", cities)
    cities = cities.merge(flags, on="geo_id")
    homes_by_geo = dict(zip(scr["geo_id"], scr["homes"]))
    by_name = {(r.STATE, r.name): r.geo_id for r in cities.itertuples()}

    annual = []
    # --- 1. Washington -------------------------------------------------------
    wa = cities[cities["STATE"] == "WA"]["name"].tolist()
    ofm = ml.ofm_city_counts(ml.read_xlsx_sheet(OFM, "xl/worksheets/sheet2.xml"), wa)
    for r in ofm[ofm["year"] >= 2011].itertuples():
        annual.append(dict(state="WA", city=r.city, geo_id=by_name[("WA", r.city)], year=r.year,
                           year_basis="OFM estimate year", adu_permits=r.adu_permits, source=OFM_SRC,
                           check="", status="observed"))
    # --- 2. Oregon -----------------------------------------------------------
    orc = cities[cities["STATE"] == "OR"]["name"].tolist()
    for f in DLCD_PDFS:
        txt = pdf_text(RAW / "statewide_states" / "or" / f)
        yr = DLCD_YEARS.get(f) or ml.dlcd_year(txt)
        for c in orc:
            v, chk = ml.dlcd_adu_permitted(txt, c)
            annual.append(dict(state="OR", city=c, geo_id=by_name[("OR", c)], year=yr, year_basis="calendar year",
                               adu_permits=v, source=f"DLCD HB 4006 annual summary {yr} ({f}), ADU permitted",
                               check=chk, status="observed" if chk == "sf_total_check_ok" else "missing"))
    # --- 3. Rhode Island -----------------------------------------------------
    for c, ys in RI_EOH.items():
        if ("RI", c) not in by_name:
            continue
        for y, n in ys.items():
            annual.append(dict(state="RI", city=c, geo_id=by_name[("RI", c)], year=y, year_basis="calendar year",
                               adu_permits=float(n), source=RI_SRC, check="", status="observed"))
    # --- 4. California -------------------------------------------------------
    apr = pd.read_csv(CA / "hcd_apr_a2_juris_year_unitcat.csv")
    comp = pd.read_csv(CA / "adu_compilation_2012_2019.csv")
    cac = cities[cities["STATE"] == "CA"]
    holdout = set(pd.read_csv(ROOT / "reference" / "ca_holdout_jurisdictions.csv", dtype=str)
                  .query("holdout == 'True'")["census_geoid"])
    for r in cac.itertuples():
        j = r.name.upper()
        a = apr[(apr["juris_name"] == j) & (apr["unit_cat"] == "ADU")]
        a_years = set(apr.loc[apr["juris_name"] == j, "year"])
        for y in sorted(a_years):
            n = float(a.loc[a["year"] == y, "bp_units_primary"].sum())
            annual.append(dict(state="CA", city=r.name, geo_id=r.geo_id, year=int(y), year_basis="APR report year",
                               adu_permits=n, source="HCD APR Table A2, ADU bp_units_primary (CA study primary measure)",
                               check="", status="observed"))
        cmp_ = comp[(comp["juris_name"] == j) & comp["year"].between(2012, 2017)]
        for y, n in zip(cmp_["year"], cmp_["adu_permits"]):
            annual.append(dict(state="CA", city=r.name, geo_id=r.geo_id, year=int(y), year_basis="calendar year",
                               adu_permits=float(n), source="Building an ADU 2012-2019 compilation (HCD-reported)",
                               check="", status="observed"))
    ann = ml.add_rates(pd.DataFrame(annual), homes_by_geo)
    ann = ann.sort_values(["state", "city", "year"]).reset_index(drop=True)

    # --- 5. City table ---------------------------------------------------------
    bef = ml.before_rates(ann)
    city_tab = cities[["STATE", "name", "geo_id", "homes", "median_value", "state_capital", "universities_10k",
                       "university_or_capital"]].rename(columns={"STATE": "state", "name": "city"})
    city_tab = city_tab.merge(bef, on="geo_id", how="left")
    for y in range(1, 10):
        sub = ann[ann["year_since_law"] == y].set_index("geo_id")
        city_tab[f"rate_y{y}"] = city_tab["geo_id"].map(sub["rate_per_1000"])
        city_tab[f"permits_y{y}"] = city_tab["geo_id"].map(sub["adu_permits"])
    city_tab["law"] = city_tab["state"].map(ml.LAW_LABEL)
    for k in ("local_reform_in_window", "own", "state", "note"):
        col = {"own": "local_own_reforms", "state": "state_compliance_changes", "note": "reform_note"}.get(k, k)
        city_tab[col] = [LOCAL_REFORMS.get(c, {}).get(k, (CA_REFORM_NOTE if k == "own" else None)) if s != "CA"
                         else (CA_REFORM_NOTE if k == "own" else None) for c, s in zip(city_tab["city"], city_tab["state"])]
    city_tab["ca_holdout"] = city_tab["geo_id"].str[-7:].isin(holdout)
    city_tab["measure"] = city_tab["state"].map({
        "WA": "ADU permits (OFM), all ADUs incl. any built with a new house; estimate years",
        "OR": "ADUs permitted (DLCD HB 4006, self-reported), incl. any built with a new house; calendar years",
        "RI": "ADUs permitted (EOH, self-reported), incl. any built with a new house; calendar years",
        "CA": "ADU building-permit units (HCD APR A2), incl. most built with a new house; report years"})
    city_tab["coverage"] = city_tab["state"].map({
        "WA": "city reports every year EY2011-2026", "OR": "cities over 10,000; 2018-2023 (2023 only where reported); no pre-law year",
        "RI": "2023-2025 only; 2021-22 municipal counts not published", "CA": "compilation 2012-2017, APR 2018-2025"})
    city_tab["includes_new_house_adus"] = True

    # --- 6. Median paths -----------------------------------------------------
    main = ann[ann["state"].isin(ml.MAIN_STATES) & ann["state"].isin(["WA", "OR"])]
    noref = main[main["city"].map(lambda c: not LOCAL_REFORMS.get(c, {}).get("local_reform_in_window", True))]
    univ = main[main["geo_id"].isin(cities.loc[cities["university_or_capital"], "geo_id"])]
    ca_main = ann[(ann["state"] == "CA") & ~ann["geo_id"].str[-7:].isin(holdout)]
    paths = pd.concat([
        ml.median_path(main, "WA+OR Madison-like (main)"),
        ml.median_path(main[main["state"] == "WA"], "WA only"),
        ml.median_path(main[main["state"] == "OR"], "OR only"),
        ml.median_path(noref, "WA+OR, no own local reform in window"),
        ml.median_path(univ, "WA+OR, university or capital"),
        ml.median_path(ann[ann["state"] == "RI"], "RI (Warwick, Cranston)"),
        ml.median_path(ca_main, "CA Madison-like, non-holdout (mature-industry comparison)", 1, 9),
    ], ignore_index=True)
    v, why = ml.verdict(paths[paths["group"] == "WA+OR Madison-like (main)"])
    # post-compliance only: WA years before a city's state deadline excluded (only Tacoma EY2026 and
    # Vancouver EY2026 are partly after; Spokane/Spokane Valley/Yakima are before 2026-12-31)
    post = main[~((main["state"] == "WA") & ~(main["city"].isin(["Tacoma", "Vancouver"]) & (main["year"] == 2026)))]
    paths = pd.concat([paths, ml.median_path(post, "WA+OR, post-compliance years only")], ignore_index=True)
    v2, why2 = ml.verdict(paths[paths["group"] == "WA+OR, post-compliance years only"])
    verdicts = pd.DataFrame([dict(test="main (WA+OR, years since law)", verdict=v, reason=why),
                             dict(test="post-compliance years only", verdict=v2, reason=why2)])

    # --- 7. New-house share --------------------------------------------------
    oc = ml.other_cities_new_house(pd.read_csv(REF / "other_cities_annual.csv"))
    oc["source"] = "reference/other_cities_annual.csv (OTHER_CITIES.md city open permit data)"
    oc["definition"] = oc["city"].map({
        "seattle": "house on the same 'New' permit, or new house permit at the same address within 365 days",
        "portland": "new house permit flagged ADU", "austin": "house permit on the same parcel (tcad_id) within 365 days",
        "denver": "ADU code 026 alongside a dwelling code on the same permit",
        "minneapolis": "CCS permits whose comments name an ADU, on a new-house permit (text match; OTHER_CITIES.md)"})
    usecols = ["JURIS_NAME", "YEAR", "APN", "UNIT_CAT", "NO_BUILDING_PERMITS", "PROJECT_NAME", "DEM_DES_UNITS"]
    names = {c.upper() for c in cac["name"]}
    rows = []
    for chunk in pd.read_csv(RAW / "hcd_apr_a2" / "tablea2.csv", usecols=usecols, dtype=str, chunksize=200_000):
        chunk = chunk[chunk["JURIS_NAME"].str.strip().str.upper().isin(names)]
        rows.append(chunk)
    a2 = pd.concat(rows)
    a2 = pd.DataFrame(dict(juris_name=a2["JURIS_NAME"].str.strip().str.upper(), year=a2["YEAR"].astype(int),
                           apn=a2["APN"], project_name=a2["PROJECT_NAME"], dem_units=a2["DEM_DES_UNITS"], unit_cat=a2["UNIT_CAT"].str.strip(),
                           bp_units=pd.to_numeric(a2["NO_BUILDING_PERMITS"], errors="coerce")))
    a2 = a2[a2["year"].between(2018, 2025)]
    s0 = ml.apr_new_house_share(a2, 0)
    s1 = ml.apr_new_house_share(a2, 1).rename(columns={"adu_units_with_new_house": "adu_units_with_new_house_pm1yr",
                                                       "share_with_new_house": "share_with_new_house_pm1yr"})
    ca_sh = s0.merge(s1[["juris_name", "adu_units_with_new_house_pm1yr", "share_with_new_house_pm1yr"]], on="juris_name")
    ca_sh["city"] = ca_sh["juris_name"].str.title()
    ca_sh["first_year"], ca_sh["last_year"] = 2018, 2025
    ca_sh["source"] = "HCD APR Table A2 rows (data/raw/hcd_apr_a2/tablea2.csv)"
    ca_sh["definition"] = ("ADU permit units on a parcel (APN) that also has a single-family detached building permit in the "
                           "same APR report year; pm1yr = within +/- 1 report year")
    ca_sh["condo_driven"] = False
    ca_sh["condo_note"] = ["subdivision-driven: builder-installed ADUs on new tract-map homes (APR project names 'TR nnnnn')"
                           if x else "" for x in ca_sh["subdivision_driven"]]
    tac = pd.DataFrame([dict(city="tacoma", first_year=2019, last_year=2020, adu_units_total=148.0,
                             adu_units_with_new_house=8.0, share_with_new_house=8 / 148, condo_driven=False,
                             source="City of Tacoma ADU weekly letter 2020-09-09 (cms.tacoma.gov/Planning/DADU/ADU Weekly Letter 9.9.2020.pdf)",
                             definition="ADU building permit applications 2019-05-01 to 2020-08-12 that were 'New SFD built with an ADU' (applications, not issued units)")])
    share = pd.concat([oc.assign(group="other_cities", subdivision_driven=False), tac.assign(group="madison_like_WA", subdivision_driven=False),
                       ca_sh.rename(columns={"adu_units": "adu_units_total"}).assign(group="madison_like_CA")],
                      ignore_index=True)

    lots, lot_years, compare = lot_split_all(a2, cac, holdout, homes_by_geo)
    share["outlier"] = share["condo_driven"].fillna(False).astype(bool) | share["subdivision_driven"].fillna(False).astype(bool)
    summ = []
    for label, sub in [("main: excludes condo- and subdivision-driven cities", share[~share["outlier"]]),
                       ("sensitivity: including condo- and subdivision-driven cities", share),
                       ("main, five OTHER_CITIES + Tacoma only", share[~share["outlier"] & (share["group"] != "madison_like_CA")]),
                       ("main, Madison-like CA cities only", share[~share["outlier"] & (share["group"] == "madison_like_CA")])]:
        sh = sub["share_with_new_house"].dropna()
        summ.append(dict(set=label, n_cities=len(sh), median_share=sh.median(), min_share=sh.min(), max_share=sh.max(),
                         pooled_share=sub["adu_units_with_new_house"].sum() / sub["adu_units_total"].sum(),
                         cities=";".join(sub["city"])))
    summ = pd.DataFrame(summ)
    # AQ-039: vacant-lot share (the adjustment for comparison-state counts)
    lots["subdivision_driven"] = lots["city"].isin(share.loc[share["subdivision_driven"].fillna(False).astype(bool), "city"])
    lots["split"] = True
    unsplit = share[share["city"].isin(["seattle", "austin", "tacoma"])]
    lots = pd.concat([lots, pd.DataFrame(dict(
        city=unsplit["city"], first_year=unsplit["first_year"], last_year=unsplit["last_year"],
        all_adus=unsplit["adu_units_total"], new_house_adus_unclassified=unsplit["adu_units_with_new_house"],
        vacant_share_upper=unsplit["share_with_new_house"], new_house_share=unsplit["share_with_new_house"],
        condo_driven=unsplit["condo_driven"], subdivision_driven=False, split=False,
        method="not split (no demolition match done); total new-house share reported as an upper bound"))],
        ignore_index=True)
    vs = []
    main_l = lots[lots["split"] & ~lots["condo_driven"] & ~lots["subdivision_driven"]]
    for label, sub, col in [
            ("main: split cities, excl. condo- and subdivision-driven", main_l, "vacant_share"),
            ("upper bound: unclassified counted as vacant", main_l, "vacant_share_upper"),
            ("sensitivity: + Tacoma at its total new-house share (upper bound)",
             pd.concat([main_l, lots[lots["city"] == "tacoma"]]), "vacant_share_upper"),
            ("sensitivity: + Lancaster (subdivision-driven)", lots[lots["split"] & ~lots["condo_driven"]], "vacant_share"),
            ("main, Portland + Denver + Minneapolis only", main_l[main_l["city"].isin(["portland", "denver", "minneapolis"])], "vacant_share"),
            ("main, Madison-like CA cities only", main_l[~main_l["city"].isin(["portland", "denver", "minneapolis"])], "vacant_share")]:
        x = sub[col].dropna()
        vs.append(dict(set=label, measure=col, n_cities=len(x), median=x.median(), min=x.min(), max=x.max(),
                       pooled=(sub["new_house_adus_vacant"].fillna(0).sum() + (sub["new_house_adus_unclassified"].fillna(0).sum()
                                                                            if col == "vacant_share_upper" else 0)) / sub["all_adus"].sum(),
                       cities=";".join(sub["city"])))
    vs = pd.DataFrame(vs)

    REF.mkdir(exist_ok=True)
    vs.to_csv(REF / "madison_like_vacant_lot_share_summary.csv", index=False, float_format="%.4f")
    lots.to_csv(REF / "madison_like_new_house_lot_split.csv", index=False, float_format="%.4f")
    lot_years.to_csv(REF / "madison_like_new_house_lot_by_year.csv", index=False, float_format="%.4f")
    compare.to_csv(REF / "madison_like_vacant_lot_reform_test.csv", index=False, float_format="%.4f")
    summ.to_csv(REF / "madison_like_new_house_share_summary.csv", index=False, float_format="%.4f")
    near.to_csv(REF / "madison_like_screen.csv", index=False, float_format="%.0f")
    city_tab.to_csv(REF / "madison_like_cities.csv", index=False, float_format="%.3f")
    ann.to_csv(REF / "madison_like_annual.csv", index=False, float_format="%.3f")
    paths.to_csv(REF / "madison_like_median_path.csv", index=False, float_format="%.3f")
    verdicts.to_csv(REF / "madison_like_verdict.csv", index=False)
    share.to_csv(REF / "madison_like_new_house_share.csv", index=False, float_format="%.4f")

    if args.print:
        pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_colwidth", 40, "display.max_rows", 500)
        print(city_tab[["state", "city", "homes", "median_value", "university_or_capital", "before_window",
                        "before_permits", "before_rate_per_1000"] + [f"rate_y{y}" for y in range(1, 6)]
                       + [f"permits_y{y}" for y in range(1, 6)] + ["local_reform_in_window"]].to_string())
        print(paths.to_string())
        print(verdicts.to_string())
        print(share.drop(columns=["source", "definition", "condo_note"], errors="ignore").to_string())
        print(summ.drop(columns="cities").to_string())
        print(lots.drop(columns="method").to_string())
        print(vs.drop(columns="cities").to_string())
        print(compare.to_string())
        print(ann[ann["state"] == "OR"][["city", "year", "adu_permits", "check"]].to_string())


if __name__ == "__main__":
    main()
