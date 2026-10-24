"""Build Wisconsin current-law ADU rates x and baseline B for every municipality (Gate 3, WP B).

    uv run python scripts/build_wi_baseline.py            # from local raw caches
    uv run python scripts/build_wi_baseline.py --fetch    # download Milwaukee and Fitchburg sources first

Inputs:
    data/processed/foundation/{areas,inventory}.parquet           (statewide foundation build)
    reference/wi_rights_exposure.csv, wi_adu_rules.csv           (37 coded places)
    reference/madison_adu_permits_by_year.csv, pleasant_prairie_*.csv, sun_prairie_*.csv
    reference/wi_holdout_coded_places.csv                        (drawn before estimation; verified here)
    data/raw/milwaukee_permits/buildingpermits.csv               (data.milwaukee.gov, CC-BY)
    data/raw/milwaukee_mprop/mprop.csv                           (Master Property file; owner fields never loaded)
    data/raw/fitchburg_permits/permits_<year>.bin (xlsx)         (applicant fields never loaded)
Outputs:
    reference/wi_baseline_*.csv (aggregate, area level), data/processed/model_baseline/* (local)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.model import baseline as bl  # noqa: E402
from missing_middleware.paths import PROCESSED, RAW, REFERENCE, processed_dir  # noqa: E402
from missing_middleware.permits.fetch_util import sha256_file  # noqa: E402

UA = "missing-middleware research (public records; contact via repository)"
MKE_PERMITS_URL = ("https://data.milwaukee.gov/dataset/9bada2e0-fad5-4545-8674-1b2c8c4e9f2f/resource/"
                   "828e9630-d7cb-42e4-960e-964eae916397/download/buildingpermits.csv")
MKE_MPROP_URL = ("https://data.milwaukee.gov/dataset/562ab824-48a5-42cd-b714-87e205e489ba/resource/"
                 "0a2c7f31-cd15-4151-8222-09dd57d5f16d/download/mprop.csv")
FITCHBURG_FILES = {  # https://www.fitchburgwi.gov/3007/Building-Permit-Reports
    2019: "29332/AllPermits_2019", 2020: "29331/PermitsIssued2020", 2021: "29330/2021AllPermits",
    2022: "29329/2022ALLbuildingPermits", 2023: "29222/AllPermits_2023", 2024: "29221/AllPermits2024",
    2025: "29467/2025_PermitsIssued", 2026: "29220/All-Permits-Issued-Year-to-Date-Updated-Monthly",
}
FITCHBURG_DATA_END = date(2026, 7, 31)    # the year-to-date file covers 2026-01-01 to 2026-07-31
FITCHBURG_FIRST = date(2022, 1, 1)        # 2019-2021 files carry generic descriptions only
MADISON_DATA_END = date(2026, 10, 23)     # docs/gate2/MADISON_PERMITS.md
ADU_TYPE = ["second_home_sf_lot:adu_detached", "second_home_sf_lot:adu_attached",
            "second_home_sf_lot:adu_conversion", "second_home_sf_lot:adu_two_unit"]
# Permit sources for a later rate test of each held-out place (docs/gate2/COMPARISON_CITY_SEARCH.md).
HOLDOUT_SOURCES = {
    "5500919775": "De Pere: monthly valuation PDFs ~2014-2026 (PARTIAL->GOOD; site blocks scripts)",
    "5503178650": "Superior: no record-level source found in the Gate 2 search",
    "5507927300": "Franklin: NONE (no public list)",
    "5507984675": "Wauwatosa: NONE (EnerGov unreachable)",
    "5508702375": "Appleton: PARTIAL, weak (short windows)",
    "5510154875": "Mount Pleasant: NONE",
    "5510166000": "Racine: NONE (Cityworks login)",
}


def log(msg: str) -> None:
    print(msg, flush=True)


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, "wb") as f:
        f.write(r.read())
    log(f"downloaded {dest.relative_to(RAW)} ({dest.stat().st_size:,} bytes)")


def fetch_all() -> None:
    download(MKE_PERMITS_URL, RAW / "milwaukee_permits" / "buildingpermits.csv")
    download(MKE_MPROP_URL, RAW / "milwaukee_mprop" / "mprop.csv")
    for y, path in FITCHBURG_FILES.items():
        download(f"https://www.fitchburgwi.gov/DocumentCenter/View/{path}",
                 RAW / "fitchburg_permits" / f"permits_{y}.bin")


# --------------------------------------------------------------------------- xlsx (stdlib)
_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
       "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


def read_xlsx_rows(path: Path) -> dict[str, list[list]]:
    """Minimal xlsx reader: sheet name -> rows of cell strings (stdlib only)."""
    z = zipfile.ZipFile(path)
    ss = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", _NS):
            ss.append("".join(t.text or "" for t in si.iter(f"{{{_NS['m']}}}t")))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    out = {}
    for sh in wb.find("m:sheets", _NS):
        tgt = rels[sh.get(f"{{{_NS['r']}}}id")].lstrip("/")
        tgt = tgt if tgt.startswith("xl/") else "xl/" + tgt
        rows = []
        for row in ET.fromstring(z.read(tgt)).iter(f"{{{_NS['m']}}}row"):
            vals = {}
            for c in row.findall("m:c", _NS):
                col = 0
                for ch in re.match(r"[A-Z]+", c.get("r")).group(0):
                    col = col * 26 + ord(ch) - 64
                v, t = c.find("m:v", _NS), c.get("t")
                if t == "s" and v is not None:
                    val = ss[int(v.text)]
                elif t == "inlineStr":
                    val = "".join(x.text or "" for x in c.iter(f"{{{_NS['m']}}}t"))
                else:
                    val = v.text if v is not None else None
                vals[col - 1] = val
            if vals:
                rows.append([vals.get(i) for i in range(max(vals) + 1)])
        out[sh.get("name")] = rows
    return out


# --------------------------------------------------------------------------- evidence
def fitchburg_evidence(homes: float) -> tuple[bl.Observation, dict]:
    """Scan every Fitchburg permit description 2022-01-01..2026-07-31 for ADU-type second homes.
    Only cells with descriptions are read; applicant names, e-mails and phones are never kept."""
    hits, n_cells = [], 0
    for y in range(FITCHBURG_FIRST.year, FITCHBURG_DATA_END.year + 1):
        p = RAW / "fitchburg_permits" / f"permits_{y}.bin"
        for rows in read_xlsx_rows(p).values():
            texts = [str(c) for r in rows for c in r if c and len(str(c)) > 12 and "@" not in str(c)]
            n_cells += len(texts)
            hits += bl.adu_text_hits(texts)
    # The 2025 hits are a shed with 'carriage house doors' and a 'Carriage House/Pole Barn
    # Addition'; neither names a dwelling unit, and the pattern excludes 'carriage house'.
    obs = bl.Observation(
        key="fitchburg_2022_2026jul", place="Fitchburg city", jurisdiction_id=bl.FITCHBURG,
        series="ADU-type second homes (description text)", window="2022-01-01 to 2026-07-31",
        units=len(set(hits)), homes=homes, years=bl.years_between(FITCHBURG_FIRST, FITCHBURG_DATA_END),
        regime="restricted", status="observed",
        note=("Restricted throughout: attached owner-occupied dependency unit by conditional use to "
              "2025-09-09, then ADUs by right with a size cap (size_below_benchmark). Text rule only, "
              "no parcel check, so duplex conversions without ADU wording would be missed."))
    return obs, {"description_cells_scanned": n_cells, "hits": sorted(set(hits))}


def milwaukee_evidence(homes: float) -> tuple[list[bl.Observation], pd.DataFrame, dict]:
    raw = pd.read_csv(RAW / "milwaukee_permits" / "buildingpermits.csv", low_memory=False)
    permits = pd.DataFrame({
        "record_id": raw["Record ID"], "issued": pd.to_datetime(raw["Date Issued"], errors="coerce"),
        "permit_type": raw["Permit Type"].astype(str), "use": raw["Use of Building"],
        "units_impact": raw["Dwelling units impact"], "address": raw["Address"]})
    cols = ["HOUSE_NR_LO", "HOUSE_NR_HI", "SDIR", "STREET", "NR_UNITS", "YR_BUILT"]
    mp = pd.read_csv(RAW / "milwaukee_mprop" / "mprop.csv", usecols=cols, dtype=str)
    mp.columns = ["house_lo", "house_hi", "sdir", "street", "nr_units", "yr_built"]
    cand = bl.milwaukee_candidates(permits, mp)
    data_end = permits["issued"].max().date()
    reform = date(2025, 8, 2)
    windows = {"pre": (date(2017, 1, 1), date(2025, 8, 1)), "post": (reform, data_end)}
    obs = []
    for w, (s, e) in windows.items():
        c = cand[(cand["issued"].dt.date >= s) & (cand["issued"].dt.date <= e)]
        yrs = bl.years_between(s, e)
        for level in ("central", "upper"):
            obs.append(bl.Observation(
                key=f"milwaukee_{w}_{level}", place="Milwaukee city", jurisdiction_id=bl.MILWAUKEE,
                series=f"candidate second homes ({level} rule)", window=f"{s} to {e}",
                units=int(c[level].sum()), homes=homes, years=yrs,
                regime="restricted" if w == "post" else "pre-reform (RS prohibited, RT two-family by right)",
                status="observed_candidate",
                note="Open permit data has no description or unit count; counts are unverified candidates."))
    comp = (cand.assign(window=["post" if d.date() >= reform else "pre" for d in cand["issued"]])
            .query("issued >= '2017-01-01'")
            .groupby(["window", "component"])[["central", "upper"]].sum().reset_index())
    meta = {"data_end": str(data_end), "rows": int(len(raw)),
            "added_units_residential_rows": int(len(cand)),
            "post_reform_new_dwelling_on_occupied_lot_upper": int(cand[(cand.issued.dt.date >= reform) & (cand.component == "new_dwelling_on_occupied_lot")]["upper"].sum())}
    return obs, comp, meta


# --------------------------------------------------------------------------- main build
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    args = ap.parse_args()
    if args.fetch:
        fetch_all()

    fnd = PROCESSED / "foundation"
    areas = pd.read_parquet(fnd / "areas.parquet")
    inv = pd.read_parquet(fnd / "inventory.parquet")
    muni = areas[areas["level"] == "municipality"][["area_id", "geoid", "name", "muni_type",
                                                    "parent_county_id", "context_group"]]
    muni = muni.merge(inv[["area_id", "homes_1unit_detached"]], on="area_id").rename(
        columns={"homes_1unit_detached": "homes"})
    counties = areas[areas["level"] == "county"].set_index("geoid")["name"]
    state_homes = float(inv.loc[inv["level"] == "state", "homes_1unit_detached"].iloc[0])

    rules = pd.read_csv(REFERENCE / "wi_adu_rules.csv", dtype={"jurisdiction_id": str})
    rx = pd.read_csv(REFERENCE / "wi_rights_exposure.csv", dtype={"jurisdiction_id": str})
    rx = rx[rx["scenario_id"] == "adu_full"]
    status = (rules[rules["provision"] == "ordinance_status"][["jurisdiction_id", "jurisdiction_name", "value"]]
              .rename(columns={"value": "ordinance_status"}))
    place_by_fp = {pid[-5:]: pid for pid in status["jurisdiction_id"]}
    rx = rx.assign(place_id=rx["jurisdiction_id"].str[-5:].map(place_by_fp))

    # 1. Hold-out: verify the committed draw (made before any estimate) reproduces.
    hpath = REFERENCE / "wi_holdout_coded_places.csv"
    held = pd.read_csv(hpath, dtype={"jurisdiction_id": str})
    redraw = bl.draw_holdout(status["jurisdiction_id"].tolist())
    if set(redraw.loc[redraw.holdout, "jurisdiction_id"]) != set(held.loc[held.holdout, "jurisdiction_id"]):
        raise SystemExit("hold-out draw does not reproduce reference/wi_holdout_coded_places.csv")
    held_ids = set(held.loc[held.holdout, "jurisdiction_id"])
    literal = bl.draw_holdout(status["jurisdiction_id"].tolist(), exclude=())
    literal_names = status.set_index("jurisdiction_id").loc[
        literal.loc[literal.holdout, "jurisdiction_id"], "jurisdiction_name"].tolist()

    H = muni.set_index("geoid")["homes"]
    hm, hpp, hsp, hfb, hmk = (float(H[i]) for i in (bl.MADISON, bl.PLEASANT_PRAIRIE, bl.SUN_PRAIRIE,
                                                     bl.FITCHBURG, bl.MILWAUKEE))

    # 2. Observed rates.
    mad = pd.read_csv(REFERENCE / "madison_adu_permits_by_year.csv")
    pp = pd.read_csv(REFERENCE / "pleasant_prairie_adu_equivalent_by_year.csv")
    sp = pd.read_csv(REFERENCE / "sun_prairie_adu_equivalent_by_year.csv")
    y2225 = range(2022, 2026)
    O = bl.Observation
    madison = O("madison_2022_2025", "Madison city", bl.MADISON, "second homes on SF lots", "2022-2025",
                bl.madison_units(mad, "second_home_sf_lot", y2225), hm, 4, "benchmark", "observed",
                "Floor window per G2-9; includes 7 templated-programme units in 2025. Owner occupancy "
                "applied until 2024-04-25, so 2022-2023 were restricted years.")
    adu_type = sum(bl.madison_units(mad, c, y2225) for c in ADU_TYPE)
    obs = [
        madison,
        O("madison_2022_2025_adu_type", "Madison city", bl.MADISON, "ADU-type component", "2022-2025",
          adu_type, hm, 4, "benchmark", "observed", "Detached, attached, conversion, two-unit ADU (cross-state measure)"),
        O("madison_2022_2025_excl_templated", "Madison city", bl.MADISON, "second homes excl. templated programme",
          "2022-2025", bl.madison_units(mad, "second_home_sf_lot_excl_templated_programme", y2225), hm, 4,
          "benchmark", "observed", "Sensitivity"),
        O("madison_2024_2025", "Madison city", bl.MADISON, "second homes on SF lots", "2024-2025",
          bl.madison_units(mad, "second_home_sf_lot", range(2024, 2026)), hm, 2, "benchmark", "observed",
          "Years after owner occupancy was removed (2024-04-26)"),
        O("madison_2026_provisional", "Madison city", bl.MADISON, "second homes on SF lots (provisional)",
          f"2026-01-01 to {MADISON_DATA_END}", bl.madison_units(mad, "second_home_sf_lot", [2026]), hm,
          bl.years_between(date(2026, 1, 1), MADISON_DATA_END), "benchmark", "observed",
          "Sensitivity only (G2-9): provisional, 29 of 42 units from one templated programme"),
        O("madison_2014_2021", "Madison city", bl.MADISON, "second homes on SF lots", "2014-2021",
          bl.madison_units(mad, "second_home_sf_lot", range(2014, 2022)), hm, 8, "restricted", "observed",
          "Conditional use (discretionary) and ongoing owner occupancy"),
        O("madison_2022_2023", "Madison city", bl.MADISON, "second homes on SF lots", "2022-2023",
          bl.madison_units(mad, "second_home_sf_lot", range(2022, 2024)), hm, 2, "restricted", "observed",
          "By right, owner occupancy still required"),
    ]
    pp_s, pp_e = date(2014, 1, 1), date(2025, 12, 31)
    sp_s, sp_e = date(2016, 1, 1), date(2026, 5, 4)
    pleasant = O("pleasant_prairie_2014_2025", "Pleasant Prairie village", bl.PLEASANT_PRAIRIE,
                 "second homes on SF lots", "2014-2025", bl.comparison_units(pp, "second_home_sf_lot", pp_s, pp_e),
                 hpp, 12, "prohibited", "observed", "Issued permits; read as 0-3 (2 uncertain second dwellings, 1 attached in-law unit)")
    sun = O("sun_prairie_2016_2026may", "Sun Prairie city", bl.SUN_PRAIRIE, "second homes on SF lots",
            f"{sp_s} to {sp_e}", bl.comparison_units(sp, "second_home_sf_lot", sp_s, sp_e), hsp,
            bl.years_between(sp_s, sp_e), "prohibited", "observed",
            "Submitted applications; prohibited until Ord. 984 (ADUs by right from 2026-05-08)")
    obs += [
        pleasant,
        O("pleasant_prairie_2014_2025_upper", "Pleasant Prairie village", bl.PLEASANT_PRAIRIE,
          "second homes, unconfirmed upper bound", "2014-2025",
          bl.comparison_units(pp, "second_home_sf_lot_upper_bound", pp_s, pp_e), hpp, 12, "prohibited", "observed",
          "Restores 3 parcel-rule hits judged likely false"),
        O("pleasant_prairie_2014_2025_adu_type", "Pleasant Prairie village", bl.PLEASANT_PRAIRIE,
          "ADU-type component", "2014-2025",
          sum(bl.comparison_units(pp, c, pp_s, pp_e) for c in ADU_TYPE), hpp, 12, "prohibited", "observed", ""),
        sun,
        O("sun_prairie_2016_2026may_adu_type", "Sun Prairie city", bl.SUN_PRAIRIE, "ADU-type component",
          f"{sp_s} to {sp_e}", sum(bl.comparison_units(sp, c, sp_s, sp_e) for c in ADU_TYPE), hsp,
          bl.years_between(sp_s, sp_e), "prohibited", "observed", ""),
    ]
    fitch, fitch_meta = fitchburg_evidence(hfb)
    mke_obs, mke_comp, mke_meta = milwaukee_evidence(hmk)
    obs += [fitch] + mke_obs
    ob = {o.key: o for o in obs}

    # 3. Group rates (fitting set: Madison, Pleasant Prairie, Sun Prairie, plus Fitchburg, which
    # is not held out; Milwaukee candidates are a check only).
    rates = bl.group_rates(benchmark=madison, prohibited=[pleasant, sun],
                           restricted=[ob["madison_2014_2021"], ob["madison_2022_2023"], fitch],
                           restricted_high=ob["madison_2022_2023"])
    R = rates.set_index("group")

    def grp(g):
        return {p: float(R.loc[g, f"x_{p}"]) for p in bl.PATHS}

    def own(o: bl.Observation, basis):
        lo, hi = o.interval
        return {"low": lo, "central": o.rate, "high": hi, "basis": basis}

    observed = {bl.MADISON: own(madison, "observed 2022-2025 (G2-9)"),
                bl.PLEASANT_PRAIRIE: own(pleasant, "observed 2014-2025")}

    # 4. Recently liberalized places ramp from their pre-reform rate to their class rate.
    lib = bl.liberalizations(rules)
    cls_by_place = rx.drop_duplicates("place_id").set_index("place_id")["current_class"]
    overrides = {}
    for r in lib.itertuples(index=False):
        if r.jurisdiction_id == bl.MADISON:
            continue
        target = grp(bl.RIGHTS_GROUP[cls_by_place[r.jurisdiction_id]])
        pre = grp("prohibited")
        basis = f"{bl.RIGHTS_GROUP[cls_by_place[r.jurisdiction_id]]} group rate, ramping from prohibited since {r.reform_date}"
        if r.jurisdiction_id == bl.SUN_PRAIRIE:
            pre = {k: v for k, v in own(sun, "").items() if k in bl.PATHS}
            basis = f"restricted group rate, ramping from its observed prohibited-period rate since {r.reform_date}"
        if r.jurisdiction_id == bl.MILWAUKEE:
            pre_o = ob["milwaukee_pre_central"]
            lo, hi = pre_o.interval
            pre = {"low": lo, "central": pre_o.rate, "high": ob["milwaukee_pre_upper"].rate}
            m_hi = madison.interval[1]
            target = {"low": float(R.loc["restricted", "x_central"]), "central": madison.rate, "high": m_hi}
            basis = ("assumed ramp from Milwaukee's observed pre-reform candidate rate to a Madison-like "
                     f"level (by right, no parking, owner occupancy only at application) since {r.reform_date}")
        for p in bl.PATHS:   # a ramp never starts above its own target
            pre[p] = min(pre[p], target[p])
        overrides[r.jurisdiction_id] = {"target": target, "pre": pre, "reform_date": r.reform_date,
                                        "basis": basis, "status": "estimated"}

    # 5. Assign every municipality piece.
    pieces = muni.merge(rx[["jurisdiction_id", "place_id", "current_class"]],
                        left_on="geoid", right_on="jurisdiction_id", how="left")
    pieces["current_class"] = pieces["current_class"].fillna("undetermined")
    assigned = bl.assign_rates(pieces[["area_id", "place_id", "name", "homes", "current_class"]],
                               rates, observed, overrides)
    assigned = assigned.merge(pieces[["area_id", "geoid", "parent_county_id", "context_group", "muni_type"]],
                              on="area_id")
    assigned["county"] = assigned["parent_county_id"].map(counties)
    assigned["holdout"] = assigned["place_id"].isin(held_ids)
    B = bl.baseline(assigned)
    problems = bl.check_baseline(B, state_homes)
    if problems:
        raise SystemExit(f"baseline checks failed: {problems}")

    # 6. Aggregates.
    out = processed_dir("model_baseline")
    B.to_parquet(out / "baseline_long.parquet", index=False)
    assigned.to_parquet(out / "assigned_rates.parquet", index=False)
    central = B[B.path == "central"]
    engine_areas = assigned.assign(
        x_rate=assigned["x_central"], at_benchmark=assigned["rate_group"].eq("benchmark"),
        rights_basis=assigned["current_class"])[["area_id", "homes", "x_rate", "x_low", "x_high",
                                                 "at_benchmark", "x_basis", "x_status", "rights_basis"]]
    engine_areas.to_parquet(out / "engine_areas.parquet", index=False)
    yidx = {y: i + 1 for i, y in enumerate(bl.FORECAST_YEARS)}
    growth = central[central.year.isin(bl.FORECAST_YEARS) & (central.g < 1 - 1e-12)]
    growth.assign(year=growth.year.map(yidx))[["area_id", "year", "g"]].to_parquet(
        out / "engine_baseline_growth.parquet", index=False)

    ref_obs = pd.DataFrame([o.row() for o in obs])
    ref_obs.to_csv(REFERENCE / "wi_baseline_observed.csv", index=False, float_format="%.4f")
    rates.to_csv(REFERENCE / "wi_baseline_rates_by_group.csv", index=False, float_format="%.4f")

    five = bl.five_year(B, ["area_id"])
    b26 = B[(B.year == bl.BRIDGE_YEAR)].pivot_table(index="area_id", columns="path", values="baseline_units")
    m = assigned.merge(five, on="area_id").merge(b26.add_prefix("b2026_").reset_index(), on="area_id")
    m = m.rename(columns={p: f"b5yr_{p}" for p in bl.PATHS})
    cols = ["area_id", "geoid", "name", "county", "muni_type", "context_group", "homes", "place_id",
            "current_class", "rate_group", "x_status", "x_basis", "x_low", "x_central", "x_high",
            "reform_date", "holdout", "b2026_central", "b5yr_low", "b5yr_central", "b5yr_high"]
    m[cols].sort_values("homes", ascending=False).to_csv(
        REFERENCE / "wi_baseline_by_municipality.csv", index=False, float_format="%.4f")

    yearly = B.groupby(["year", "path"])["baseline_units"].sum().unstack("path")[list(bl.PATHS)]
    yearly.index = yearly.index.astype(str)
    tot = yearly.loc[[str(y) for y in bl.FORECAST_YEARS]].sum().rename("2027-2031")
    statewide = pd.concat([yearly, tot.to_frame().T])
    statewide.index.name = "year"
    statewide = statewide.reset_index()
    statewide["homes"] = state_homes
    statewide["rate_per_1000_yr_central"] = [
        1000 * v / state_homes / (5 if y == "2027-2031" else 1) for y, v in zip(statewide.year, statewide.central)]

    # Sensitivities (central path, five-year totals).
    sens = []

    def central5(asg):
        return bl.baseline(asg).query("in_five_year_total and path == 'central'")["baseline_units"].sum()

    base5 = statewide.loc[statewide.year == "2027-2031", "central"].iloc[0]
    sens.append({"sensitivity": "main (central path)", "b5yr_central": base5})
    a2 = assigned.copy()
    und = a2.rate_group.eq("undetermined")
    a2.loc[und, "x_central"] = float(R.loc["prohibited", "x_central"])
    sens.append({"sensitivity": "uncoded places behave like prohibited (old AQ-023 default)", "b5yr_central": central5(a2)})
    a3 = assigned.copy()
    a3["reform_date"] = None
    sens.append({"sensitivity": "no ramp: liberalized places at their class rate at once (g = 1)", "b5yr_central": central5(a3)})
    for key, label in [("madison_2026_provisional", "Madison x = 2026 provisional to date"),
                       ("madison_2024_2025", "Madison x = 2024-2025"),
                       ("madison_2022_2025_excl_templated", "Madison x excludes templated programme")]:
        a4 = assigned.copy()
        a4.loc[a4.place_id == bl.MADISON, "x_central"] = ob[key].rate
        sens.append({"sensitivity": label, "b5yr_central": central5(a4)})
    sens = pd.DataFrame(sens)
    sens["change_vs_main"] = sens["b5yr_central"] - base5
    statewide.to_csv(REFERENCE / "wi_baseline_statewide.csv", index=False, float_format="%.2f")
    sens.to_csv(REFERENCE / "wi_baseline_sensitivities.csv", index=False, float_format="%.2f")

    top = m.sort_values("b5yr_central", ascending=False).head(20)
    top = top.assign(share_of_state_central=top.b5yr_central / base5)
    top[["name", "county", "context_group", "homes", "current_class", "x_status", "x_central",
         "b5yr_low", "b5yr_central", "b5yr_high", "share_of_state_central"]].to_csv(
        REFERENCE / "wi_baseline_top20.csv", index=False, float_format="%.4f")

    for key, fname in [("county", "wi_baseline_by_county.csv"), ("context_group", "wi_baseline_by_context.csv"),
                       ("x_status", "wi_baseline_by_x_status.csv")]:
        g = m.groupby(key).agg(areas=("area_id", "size"), homes=("homes", "sum"),
                               b5yr_low=("b5yr_low", "sum"), b5yr_central=("b5yr_central", "sum"),
                               b5yr_high=("b5yr_high", "sum")).reset_index()
        g["rate_per_1000_yr_central"] = 1000 * g.b5yr_central / g.homes / 5
        g.sort_values("b5yr_central", ascending=False).to_csv(REFERENCE / fname, index=False, float_format="%.3f")

    mk = B[B.area_id == "muni:" + bl.MILWAUKEE].pivot_table(index="year", columns="path", values=["x_year", "g", "baseline_units"])
    mk.columns = [f"{a}_{b}" for a, b in mk.columns]
    mk.reset_index().to_csv(REFERENCE / "wi_baseline_milwaukee_ramp.csv", index=False, float_format="%.4f")
    mke_comp.to_csv(REFERENCE / "wi_baseline_milwaukee_candidates.csv", index=False)

    # 7. Hold-out check (first-pass status vs second-pass class); rate test where observable.
    coded = status.merge(rx.drop_duplicates("place_id")[["place_id", "current_class"]],
                         left_on="jurisdiction_id", right_on="place_id")
    hc = bl.holdout_status_check(coded)
    hc["holdout"] = hc["jurisdiction_id"].isin(held_ids)
    hc["fitting_set"] = hc["jurisdiction_id"].isin(bl.FIT_PLACE_IDS + (bl.FITCHBURG,))
    pred_rate = {"allowed": float(R.loc["restricted", "x_central"]), "prohibited": float(R.loc["prohibited", "x_central"])}
    hc["rate_predicted_from_status"] = hc["predicted"].map(pred_rate)
    hc["rate_observed"] = hc["jurisdiction_id"].map({bl.MILWAUKEE: ob["milwaukee_post_central"].rate})
    hc["later_rate_source"] = hc["jurisdiction_id"].map(HOLDOUT_SOURCES)
    hc[["jurisdiction_id", "jurisdiction_name", "holdout", "fitting_set", "ordinance_status", "current_class",
        "predicted", "actual", "correct", "rate_predicted_from_status", "rate_observed", "later_rate_source"]].to_csv(
        REFERENCE / "wi_baseline_holdout_check.csv", index=False, float_format="%.4f")

    manifest = {
        "run_date": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "state_homes": state_homes, "areas": int(len(assigned)),
        "holdout_literal_all37_draw_would_be": literal_names,
        "fitchburg": fitch_meta, "milwaukee": mke_meta,
        "liberalizations": [{**r._asdict(), "reform_date": str(r.reform_date)} for r in lib.itertuples(index=False)],
        "sources": [
            {"file": str(p.relative_to(RAW)), "sha256": sha256_file(p)}
            for p in sorted((RAW / "milwaukee_permits").glob("*.csv")) + sorted((RAW / "milwaukee_mprop").glob("*.csv"))
            + sorted((RAW / "fitchburg_permits").glob("*.bin"))],
        "source_urls": {"milwaukee_permits": MKE_PERMITS_URL, "milwaukee_mprop": MKE_MPROP_URL,
                        "fitchburg": "https://www.fitchburgwi.gov/3007/Building-Permit-Reports"},
        "licenses": {"milwaukee": "Creative Commons Attribution (data.milwaukee.gov)",
                     "fitchburg": "public record posted by the City; no license stated"},
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n")

    log(rates.to_string())
    log(ref_obs[["key", "units", "thousand_home_years", "rate_per_1000_yr", "poisson95_lo", "poisson95_hi"]].to_string())
    log(statewide.to_string())
    log(sens.to_string())
    log(mk.to_string())
    log(f"Milwaukee components:\n{mke_comp}")
    log(f"Fitchburg: {fitch_meta}")


if __name__ == "__main__":
    main()
