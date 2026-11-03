"""US places from the TOD records for the parking thread's 2x2 test (docs/tod/PLACES_FOR_PARKING_2X2.md).

    .venv/bin/python scripts/build_tod_places_for_parking_2x2.py

Codes places from rules and records only. Outcome columns (permits, homes, effects, weights, status) are never
loaded: every table is read with an explicit list of rule columns.
Writes reference/tod_places_for_parking_2x2.csv.
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

OUT = REFERENCE / "tod_places_for_parking_2x2.csv"
GAZ = RAW / "census_gazetteer_2024"
BPS_COUNTY = RAW / "census_bps_county" / "co2020a.txt"  # county names and FIPS only (permit columns not read)

STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado",
    "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan",
    "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "PR": "Puerto Rico",
}
NEW_ENGLAND = {"Connecticut", "Maine", "Massachusetts", "New Hampshire", "Rhode Island", "Vermont"}

# Sub-city or county areas: the jurisdiction that controls zoning (record city text -> (name, geo_type)).
ZONING_JURISDICTION = {
    "New York (Brooklyn)": ("New York", "place"),
    "Fairfax County (Tysons)": ("Fairfax County", "county"),
    "Montgomery County (North Bethesda)": ("Montgomery County", "county"),
}
# Multi-place records that name their places (case_id -> places). Others go to notes only.
MULTI_PLACE = {"ma_40r_transit_districts": ["Brockton", "Haverhill", "Lowell"]}
MULTI_PLACE_UNLISTED = {
    "mbta_communities_2021": "177 MBTA communities (MA); the record does not list the towns, so none are rows",
}
# Gazetteer spellings that differ from the record's city name.
GAZ_ALIAS = {"Saint Paul": "St. Paul", "Indianapolis": "Indianapolis city (balance)"}
# PRN spellings for consolidated governments (gazetteer name -> PRN place).
PRN_ALIAS = {
    "Nashville-Davidson metropolitan government (balance)": ["Nashville", "Nashville-Davidson"],
    "Louisville/Jefferson County metro government (balance)": ["Louisville", "Louisville/Jefferson County"],
    "Indianapolis city (balance)": ["Indianapolis"],
    "St. Paul city": ["Saint Paul", "St. Paul"],
    "Washington city": ["Washington"],
}
# tod_census_set case -> tod_cases case_id (same reform, different label); new ids keep their own row.
CENSUS_TO_CASE = {
    "phoenix_wu_2015_2016": "phoenix_walkable_urban_code_2015",
    "austin_tod_station_plans": "austin_tod_2005",
    "philadelphia_2012_remapping": "philadelphia_2012_code",
}
CENSUS_PLACE = {"nyc_": ("New York", "New York")}  # prefix -> (city, state) for the per-rezoning NYC rows
SUFFIXES = ["city", "town", "village", "borough", "city (balance)", "municipality", "township"]

# Parking coding. The record's flag decides yes/no/unknown; a "yes" whose detail describes cuts, tiers, partial
# areas or fees (not removal across the reform area) becomes "partial". Ambiguous detail is kept in notes.
PARTIAL_WORDS = re.compile(r"reduc|cut|lower|up to|some |in-lieu|shared|50%|by tier|transition", re.I)
FULL_WORDS = re.compile(r"no minimum|eliminated|removed|abolished|optional|replaced by maximums", re.I)
# Hand rules from reading the record text (rules only), each kept in notes.
PARKING_OVERRIDE = {
    "philadelphia_2012_code": ("partial", "flag says no, but the reform includes the /TOD overlay, which the detail says cuts minimums"),
}
PARKING_NOTE = {
    "minneapolis_2040": "detail: minimums removed May 2021, after the 2020-01-01 effective date (a later, separate step)",
    "san_diego_complete_communities_2020": "detail: the parking change is a separate 2019 reform in Transit Priority Areas",
    "nyc_downtown_brooklyn_2004": "detail: minimums cut later (2013), not with the 2004 upzoning",
    "jersey_city_journal_square_2010": "flag yes but parking detail unknown",
    "portland_central_city_2035": "flag yes but parking detail unknown",
    "stpaul_green_line_2011": "removal within 1/4 mile of stations, 25% cut elsewhere in T3/T4",
    "salt_lake_city_tsa_2010": "removal in core only; 50% of standard in transition areas",
    "shoreline_station_subareas_2015": "detail dates the parking cut to 2022, after the 2015-2016 upzonings",
}
# Year rules from the date text (rules only), each kept in notes.
YEAR_OVERRIDE = {
    "sf_market_octavia_2008": (2008, "record: plan approved late 2007, zoning ordinance 2008; 2008 used"),
}
YEAR_NOTE = {
    "austin_tod_2005": "TOD district ordinance 2005; station regulating plans 2008-2009 (effective 2009-03)",
    "raleigh_new_bern_2024": "reform name also cites the 2021 TOD overlay text (TC-17A-20); dates give 2024",
    "nyc_bloomberg_rezonings_2003_2013": "one date per rezoning, 2004 to 2013",
}


def years(text) -> tuple[list[int], list[int]]:
    """(clear years, approximate years) in a date text; 'about'/'source_lead' marks a year approximate."""
    if not isinstance(text, str):
        return [], []
    clear, approx = [], []
    for m in re.finditer(r"(about\s+)?\b(19[5-9]\d|20[0-4]\d)\b", text):
        (approx if m.group(1) else clear).append(int(m.group(2)))
    return clear, approx


def case_year(adoption, effective) -> tuple[int | None, str]:
    c1, a1 = years(adoption)
    c2, a2 = years(effective)
    clear = c1 + c2
    if clear:
        note = f"approximate year also in record: {min(a1 + a2)}" if (a1 + a2) and min(a1 + a2) < min(clear) else ""
        return min(clear), note
    if a1 + a2:
        return min(a1 + a2), "year approximate ('about' in record)"
    return None, "no clear year in record"


def code_parking(case_id: str, flag, detail) -> tuple[str, str]:
    flag = str(flag).strip().lower() if isinstance(flag, str) else "unknown"
    detail = detail if isinstance(detail, str) else ""
    notes = []
    if case_id in PARKING_OVERRIDE:
        value, why = PARKING_OVERRIDE[case_id]
        notes.append(why)
    elif flag == "yes":
        if PARTIAL_WORDS.search(detail):
            value = "partial"
        elif FULL_WORDS.search(detail):
            value = "yes"
        else:
            value = "yes"
    elif flag in ("no", "unknown"):
        value = flag
    else:
        value = "unknown"
        notes.append(f"flag text '{flag}'")
    if case_id in PARKING_NOTE:
        notes.append(PARKING_NOTE[case_id])
    return value, "; ".join(notes)


def load_gazetteer() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    def read(name):
        z = zipfile.ZipFile(GAZ / name)
        g = pd.read_csv(z.open(z.namelist()[0]), sep="\t", dtype=str)
        g.columns = g.columns.str.strip()
        g["state"] = g.USPS.map(STATES)
        return g[["USPS", "GEOID", "NAME", "state"]]
    county = pd.read_csv(BPS_COUNTY, skiprows=3, header=None, dtype=str, usecols=[1, 2, 5])
    county.columns = ["st", "co", "NAME"]
    county["NAME"] = county.NAME.str.strip()
    county["GEOID"] = county.st.str.zfill(2) + county.co.str.zfill(3)
    st_fips = read("2024_Gaz_place_national.zip").assign(st=lambda d: d.GEOID.str[:2]).drop_duplicates("st")
    county["state"] = county.st.str.zfill(2).map(dict(zip(st_fips.st, st_fips.state)))
    return read("2024_Gaz_place_national.zip"), read("2024_Gaz_cousubs_national.zip"), county[["GEOID", "NAME", "state"]]


def match(name: str, state: str, geo_type: str, gaz) -> tuple[str, str, str] | None:
    """(geo_type, geoid, gazetteer name) on exact name plus state, else None. Never fuzzy."""
    place, cousub, county = gaz
    if geo_type == "county":
        hit = county[(county.NAME == name) & (county.state == state)]
        return ("county", hit.GEOID.iloc[0], name) if len(hit) == 1 else None
    base = GAZ_ALIAS.get(name, name)
    names = [base] + [f"{base} {s}" for s in SUFFIXES]
    hit = place[(place.state == state) & place.NAME.isin(names)]
    if len(hit) == 1:
        return "place", hit.GEOID.iloc[0], hit.NAME.iloc[0]
    if state in NEW_ENGLAND:
        hit = cousub[(cousub.state == state) & cousub.NAME.isin(names)]
        if len(hit) == 1:
            return "county_subdivision", hit.GEOID.iloc[0], hit.NAME.iloc[0]
    return None


def base_name(gaz_name: str) -> str:
    for s in sorted(SUFFIXES, key=len, reverse=True):
        if gaz_name.endswith(" " + s):
            return gaz_name[: -len(s) - 1]
    return gaz_name


def prn_lookup(gaz_name: str, state: str, cases: pd.DataFrame, taxonomy: pd.DataFrame) -> tuple[str, str]:
    """(separate_parking_reform from parking_reform_cases.csv, note on weaker PRN records in the taxonomy)."""
    names = {base_name(gaz_name), gaz_name, *PRN_ALIAS.get(gaz_name, [])}
    hit = cases[cases.place.isin(names) & (cases.state == state)]
    parts = []
    for _, r in hit.iterrows():
        yr = "" if pd.isna(r.adopted_year) else str(int(r.adopted_year))
        parts.append(f"{r.policy}; {r.status}; {yr or 'year unknown'}; {r.scope}")
    tax = taxonomy[taxonomy.place.isin(names) & (taxonomy.state == state)]
    key = lambda d: d.prn_key + "|" + d.adopted_date.fillna("") + "|" + d.scope.fillna("")  # noqa: E731
    tax = tax[~key(tax).isin(set(key(hit)))]
    extra = []
    for _, r in tax.iterrows():
        yr = str(r.adopted_date)[:4] if isinstance(r.adopted_date, str) else "year unknown"
        extra.append(f"{r.policy}; {r.status}; {yr}; {r.scope}; rated {r.benchmark_rating}")
    note = ("other PRN records (parking_reform_taxonomy.csv, not in cases file): " + " | ".join(extra)) if extra else ""
    return " | ".join(parts), note


def main() -> None:
    gaz = load_gazetteer()
    # Rule columns only. Outcome columns are not loaded.
    tod = pd.read_csv(REFERENCE / "tod_cases.csv", usecols=[
        "case_id", "city", "state_or_province", "country", "reform_name", "adoption_date", "effective_date",
        "parking_minimums_changed", "parking_detail"])
    tod = tod[tod.country == "US"]
    census = pd.read_csv(REFERENCE / "tod_census_set.csv", usecols=["case", "label", "adopted"])
    controls = pd.read_csv(REFERENCE / "tod_control_cities_controls.csv", usecols=["test", "method", "place", "state"])
    prn = pd.read_csv(REFERENCE / "parking_reform_cases.csv")
    taxonomy = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv", usecols=[
        "prn_key", "place", "state", "policy", "status", "adopted_date", "scope", "benchmark_rating"])

    unmatched: list[str] = []
    entries = []  # one per (case, place)
    case_notes_global = []
    for _, r in tod.iterrows():
        yr, ynote = case_year(r.adoption_date, r.effective_date)
        if r.case_id in YEAR_OVERRIDE:
            yr, ynote = YEAR_OVERRIDE[r.case_id]
        if r.case_id in YEAR_NOTE:
            ynote = "; ".join(x for x in (ynote, YEAR_NOTE[r.case_id]) if x)
        park, pnote = code_parking(r.case_id, r.parking_minimums_changed, r.parking_detail)
        if r.case_id in MULTI_PLACE_UNLISTED:
            case_notes_global.append(f"{r.case_id}: {MULTI_PLACE_UNLISTED[r.case_id]}")
            continue
        notes = []
        if r.case_id in MULTI_PLACE:
            places = [(p, "place") for p in MULTI_PLACE[r.case_id]]
            notes.append(f"{r.case_id}: record lists '{r.city}'; only the named places are rows")
        elif r.city in ZONING_JURISDICTION:
            j, gt = ZONING_JURISDICTION[r.city]
            places = [(j, gt)]
            notes.append(f"{r.case_id}: record area '{r.city}' mapped to the zoning jurisdiction {j}")
        else:
            places = [(r.city, "place")]
        detail = r.parking_detail if isinstance(r.parking_detail, str) else "blank"
        for p, gt in places:
            entries.append(dict(case_id=r.case_id, name=p, state=r.state_or_province, gt=gt, year=yr,
                                parking=park, src="tod_cases.csv", notes=notes + [
                                    f"{r.case_id}: {yr} parking={park} (flag '{r.parking_minimums_changed}', "
                                    f"detail '{detail}'){'; ' + pnote if pnote else ''}{'; ' + ynote if ynote else ''}"]))
    known = set(tod.case_id)
    by_case = {e["case_id"]: e for e in entries}
    for _, r in census.iterrows():
        cid = CENSUS_TO_CASE.get(r.case, r.case)
        if cid in known:
            if cid != r.case:  # same reform under another id: list the census id too
                base = by_case[cid]
                yr, _ = case_year(str(r.adopted), None)
                entries.append(dict(case_id=r.case, name=base["name"], state=base["state"], gt=base["gt"],
                                    year=yr, parking=None, src="tod_census_set.csv",
                                    notes=[f"{r.case}: census-set id for {cid} (adopted '{r.adopted}')"]))
            continue
        prefix = next((k for k in CENSUS_PLACE if r.case.startswith(k)), None)
        if prefix is None:
            unmatched.append(f"census set case {r.case} (no place rule)")
            continue
        city, st = CENSUS_PLACE[prefix]
        yr, _ = case_year(str(r.adopted), None)
        entries.append(dict(case_id=r.case, name=city, state=st, gt="place", year=yr, parking=None,
                            src="tod_census_set.csv", notes=[f"{r.case}: census-set station-area rezoning, {yr}; "
                                                              "parking not coded in the census set"]))

    rows = {}
    for e in entries:
        m = match(e["name"], e["state"], e["gt"], gaz)
        if m is None:
            unmatched.append(f"{e['name']}, {e['state']} ({e['case_id']})")
            continue
        gt, geoid, gname = m
        rows.setdefault(geoid, dict(gname=gname, state=e["state"], gt=gt, entries=[]))["entries"].append(e)

    out = []
    for geoid, d in rows.items():
        es = d["entries"]
        first = min(e["year"] for e in es if e["year"] is not None and e["src"] == "tod_cases.csv")
        coded = [e for e in es if e["parking"] is not None]
        at_first = sorted({e["parking"] for e in coded if e["year"] == first})
        if len(at_first) == 1:
            park = at_first[0]
            pnote = ""
        elif set(at_first) == {"yes", "partial"}:
            park, pnote = "partial", f"cases in first year {first} are yes and partial: coded partial"
        elif not at_first:
            park, pnote = "unknown", f"no parking-coded case in first year {first}"
        else:
            park, pnote = "unknown", f"cases in first year {first} disagree: {', '.join(at_first)}"
        sep, tnote = prn_lookup(d["gname"], d["state"], prn, taxonomy)
        notes = []
        for e in sorted(es, key=lambda e: (e["year"] or 0, e["case_id"])):
            notes += [n for n in e["notes"] if n not in notes]
        if len(coded) > 1:
            notes.insert(0, f"place value taken from the case(s) at the first upzoning year {first}")
        notes += [n for n in (pnote, tnote) if n]
        out.append(dict(place_name=d["gname"], state=d["state"], geo_type=d["gt"], geoid=geoid,
                        tod_case_ids=";".join(sorted({e["case_id"] for e in es})), group="upzoned",
                        upzoning_year=str(first), parking_changed_with_upzoning=park, separate_parking_reform=sep,
                        parking_source="tod_cases.csv parking_minimums_changed + parking_detail"
                        + ("; PRN parking_reform_cases.csv" if sep else ""),
                        notes=" || ".join(notes)))
    upz = {r["geoid"] for r in out}

    # Neither candidates: matched comparison cities, plus the lot model's no-reform placebo cities.
    neither: dict[str, dict] = {}
    excluded = []
    st_name = {f: s for f, s in zip(gaz[0].GEOID.str[:2], gaz[0].state)}
    for _, r in controls.iterrows():
        state = st_name[str(int(r.state)).zfill(2)]
        hit = gaz[0][(gaz[0].NAME == r.place) & (gaz[0].state == state)]
        if len(hit) != 1:
            unmatched.append(f"{r.place}, {state} (control for {r.test})")
            continue
        geoid = hit.GEOID.iloc[0]
        if geoid in upz:
            excluded.append(f"{r.place}, {state}")
            continue
        neither.setdefault(geoid, dict(name=r.place, state=state, tests=set()))["tests"].add(f"{r.test} ({r.method})")
    placebo = [("Columbus city", "Ohio"), ("Kansas City city", "Missouri"), ("Milwaukee city", "Wisconsin")]
    for name, state in placebo:
        hit = gaz[0][(gaz[0].NAME == name) & (gaz[0].state == state)]
        geoid = hit.GEOID.iloc[0]
        if geoid in upz:
            excluded.append(f"{name}, {state} (lot-model no-reform placebo)")
            continue
        neither.setdefault(geoid, dict(name=name, state=state, tests=set()))["tests"].add(
            "lot-model no-reform placebo city (LOT_MODEL_PLAN item 46)")
    for geoid, d in neither.items():
        sep, tnote = prn_lookup(d["name"], d["state"], prn, taxonomy)
        notes = ["comparison place in: " + "; ".join(sorted(d["tests"]))]
        if not sep:
            notes.append("no PRN record in parking_reform_cases.csv")
        if tnote:
            notes.append(tnote)
        out.append(dict(place_name=d["name"], state=d["state"], geo_type="place", geoid=geoid, tod_case_ids="",
                        group="neither_candidate", upzoning_year="", parking_changed_with_upzoning="",
                        separate_parking_reform=sep,
                        parking_source="PRN parking_reform_cases.csv" if sep else "PRN parking_reform_cases.csv (no record)",
                        notes=" || ".join(notes)))

    df = pd.DataFrame(out).sort_values(["group", "state", "place_name"], ascending=[False, True, True])
    df.to_csv(OUT, index=False)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(df)} rows")
    print(df.groupby("group").size().to_string())
    up = df[df.group == "upzoned"]
    print("upzoned parking:", up.parking_changed_with_upzoning.value_counts().to_dict())
    print("upzoned with separate PRN:", (up.separate_parking_reform != "").sum())
    ne = df[df.group == "neither_candidate"]
    print("neither with PRN:", (ne.separate_parking_reform != "").sum(), "without:", (ne.separate_parking_reform == "").sum())
    print("excluded controls (upzoned):", sorted(set(excluded)))
    print("unmatched:", unmatched)
    print("multi-place notes:", case_notes_global)


if __name__ == "__main__":
    main()
