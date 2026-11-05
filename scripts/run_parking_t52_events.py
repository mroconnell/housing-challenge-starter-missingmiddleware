"""Test 52b (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Test 52", 52b and audit fix 13): the events table of other
housing reforms, built before any join to outcomes.

    uv run --all-extras python scripts/run_parking_t52_events.py

Reads only names, dates and places (no permit counts). Lists used, as named in the plan:
  reference/statewide_states_laws.csv          state ADU laws (effective_date); every BPS place in the state
  reference/tod_cases.csv                      TOD upzonings (effective_date, else adoption_date)
  reference/tod_reform_density.csv             TOD reforms (reform_year), deduplicated against tod_cases
  reference/other_cities_reforms.csv           ADU and zoning ordinances (effective, else adopted); state rows -> state
  reference/parking_reform_taxonomy.csv        PRN parking reforms, repeal places only ("prior parking dose")
  reference/ca_ab2097_rail_openings.csv        CA rail openings, station point-in-place (Census 2024 cartographic files)
  data/raw/tod_mbta/compliance_status_2025-09-18.csv   MBTA Communities: deadline year, compliant or conditional towns
  reference/tod_optiond_stopmodel_places.csv   Option D places (D-11, D-B); dates from tod_cases
  reference/tod_causal_edge_test.csv           edge-test places; dates from tod_cases
  reference/wi_adu_rules.csv                   earliest ADU-allowing effective_from per WI place
  repeal-place coding (+-3 years): reference/parking_reform_type_15.csv and the in-repo ordinance checks
      (reference/parking_repeal_checks.csv, parking_repeal_checks_expanded.csv: simultaneous_zoning_changes and
      prior_partial_reforms, with their source_urls); hand-coded below, separate acts only (the repeal ordinance's own
      changes are part of the treatment and are not events).
Places: cmp.match_place on the BPS panel (name and state). A name that matches more than one BPS place with no unique
exact name is "ambiguous" and left out (audit addition 4). Repeal places come from the batch effects (key, event year
only). Output: reference/parking_t52_b_events.csv (one row per place-event).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_parking_comparison as rpc  # noqa: E402
from missing_middleware import geom  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402

REF = ROOT / "reference"   # always the committed lists (never a working copy)
RAW = ROOT / "data" / "raw"
OUT = REF / "parking_t52_b_events.csv"
ABBR = {"AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado",
        "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia",
        "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky",
        "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
        "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
        "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota",
        "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia",
        "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"}
# other_cities_reforms.csv has no state column; its jurisdictions are one city or state each
OTHER_CITIES_STATE = {"seattle": "Washington", "portland": "Oregon", "austin": "Texas", "denver": "Colorado",
                      "minneapolis": "Minnesota", "washington": "Washington", "oregon": "Oregon", "colorado": "Colorado"}
# TOD place labels without a state (tod_reform_density, Option D, edge test) -> (BPS name to match, state)
TOD_LABELS = {"austin": ("Austin", "Texas"), "belred (bellevue)": ("Bellevue", "Washington"),
              "salt lake city": ("Salt Lake City", "Utah"), "slc": ("Salt Lake City", "Utah"),
              "saint paul": ("Saint Paul", "Minnesota"), "stpaul": ("Saint Paul", "Minnesota"),
              "seattle othello": ("Seattle", "Washington"), "seattle_othello": ("Seattle", "Washington"),
              "seattle mount baker": ("Seattle", "Washington"), "seattle_mount_baker": ("Seattle", "Washington"),
              "chicago": ("Chicago", "Illinois"), "honolulu": ("Honolulu", "Hawaii"),
              "los angeles toc": ("Los Angeles", "California"), "denver": ("Denver", "Colorado"),
              "charlotte": ("Charlotte", "North Carolina"), "portland": ("Portland", "Oregon"),
              "san diego": ("San Diego", "California"), "new york": ("New York", "New York"),
              "new york (22 rezonings)": ("New York", "New York"), "philadelphia": ("Philadelphia", "Pennsylvania"),
              "philadelphia (64 remappings)": ("Philadelphia", "Pennsylvania")}
YEAR = re.compile(r"\b(19[5-9]\d|20[0-4]\d)\b")
DATE = re.compile(r"\b((?:19|20)\d{2})(?:-(\d{2}))?(?:-(\d{2}))?\b")


# ---------------------------------------------------------------- helpers -------------------------------------------
def first_date(s) -> str | None:
    m = DATE.search(str(s or ""))
    return "-".join(x for x in m.groups() if x) if m else None


def years_in(s) -> list[int]:
    """Years named in a date field, with 'X to Y' ranges expanded (one event per year)."""
    s = str(s or "")
    out = set(int(y) for y in YEAR.findall(s))
    for a, b in re.findall(r"\b((?:19|20)\d{2})\s*(?:to|–|-)\s*((?:19|20)\d{2})\b", s):
        out |= set(range(int(a), int(b) + 1))
    return sorted(out)


def date_for_year(s, y: int) -> str:
    for m in DATE.finditer(str(s or "")):
        if int(m.group(1)) == y:
            return "-".join(x for x in m.groups() if x)
    return str(y)


class Matcher:
    def __init__(self, p: pd.DataFrame):
        last = p.sort_values("year").drop_duplicates("key", keep="last")
        self.p, self.last = p, last
        self.name = last.set_index("key")["name"]
        self.keys_by_state = {st: g for st, g in last.groupby("state_fips")}

    def candidates(self, st: str, name: str) -> pd.DataFrame:
        n = cmp.ALIASES.get((st, name.strip().lower()), name.strip().lower())
        s = self.keys_by_state.get(st, self.last.iloc[0:0])
        low = s["name"].str.lower()
        low = low.astype(object).fillna("").to_numpy()
        exact = low == n
        starts = pd.Series(low).str.startswith(n + " ").to_numpy(dtype=bool)
        bad = pd.Series(low).str.contains("county|balance").to_numpy(dtype=bool)
        # a prefix match must end in a jurisdiction word ("Windham town", "Kansas City MO"), never another name
        # ("New York" must not become "New York Mills village")
        suffix = pd.Series(low).str.slice(len(n) + 1).to_numpy()
        typed = np.array([bool(re.fullmatch(r"(town|city|village|township|borough|charter township|plantation|[a-z]{2})", x)) for x in suffix])
        m = (exact | (starts & typed)) & ~bad
        return s[m].assign(exact=exact[m])

    def match(self, state: str, name: str, population=None) -> tuple[str | None, str, str]:
        """(key, status, name tried). Tries the name, then 'Saint' -> 'St.', then a trailing ' city/village/town' cut."""
        st = rpc.STATE_FIPS.get(state)
        if st is None:
            return None, "not a US state", name
        tries = [name.strip()]
        if re.match(r"(?i)saint ", name.strip()):
            tries.append(re.sub(r"(?i)^saint ", "St. ", name.strip()))
        cut = re.sub(r"(?i)\s+(city|village|town)$", "", name.strip())
        if cut != name.strip():
            tries.append(cut)
        for nm in tries:
            c = self.candidates(st, nm)
            if c.empty:
                continue
            ex = c[c["exact"]]
            if len(ex) > 1 or (len(ex) == 0 and len(c) > 1):
                return None, f"ambiguous ({len(c)} BPS places: " + "; ".join(str(x) for x in c["name"].head(4).tolist()) + ")", nm
            k = cmp.match_place(self.p, st, nm, population)
            return k, "matched", nm
        return None, "unmatched (no BPS place of that name)", tries[-1]


def row(**k) -> dict:
    base = dict(bps_key=None, bps_name=None, place=None, state=None, scope="place", event_type=None, description=None,
                date_used=None, event_year=np.nan, date_field_used=None, date_raw=None, source_file=None, source_row=None,
                source_url=None, match_status=None, repeal_place=False, repeal_event_year=np.nan,
                prior_parking_dose=False, counted=True, note=None)
    base.update(k)
    return base


# ---------------------------------------------------------------- hand-coded repeal-place reforms ---------------------
# (place as in the batch, state, date used, event type, counted?, prior parking dose?, description, source, field)
# Separate acts only, within about 3 years either side of the repeal; same-ordinance changes are the treatment.
RT15 = "reference/parking_reform_type_15.csv"
CHK = "reference/parking_repeal_checks.csv"
CHX = "reference/parking_repeal_checks_expanded.csv"
CODED = [
    ("San Francisco", "California", "2018-08-27", "approval process reform", True, False,
     "Ord. 179-18 Process Improvements (notice and review changes; Sec. 312 repeal operative 2019-01-01)", RT15, "same_time_changes_within_1yr"),
    ("San Francisco", "California", "2018-12-04", "area upzoning", True, False,
     "Central SoMa Plan adopted (heights raised in one area)", RT15, "same_time_changes_within_1yr"),
    ("Raleigh", "North Carolina", "2021-07", "middle-housing upzoning", True, False,
     "Missing Middle text change TC-5-20 adopted (duplexes/townhouses by right in most residential districts)", CHK, "simultaneous_zoning_changes"),
    ("Raleigh", "North Carolina", "2022-08-08", "middle-housing upzoning", True, False,
     "Follow-up TC-20-21 (adopted 2022-05-10, effective 2022-08-08)", CHK, "simultaneous_zoning_changes"),
    ("Raleigh", "North Carolina", "2020", "parking reduction (partial)", False, True,
     "2020 parking reduction, mainly downtown", CHK, "prior_partial_reforms"),
    ("Minneapolis", "Minnesota", "2021-01-01", "zoning rewrite (built form)", True, False,
     "Built Form zoning regulations effective", CHK, "simultaneous_zoning_changes"),
    ("Minneapolis", "Minnesota", "2015", "parking reduction (partial)", False, True,
     "Residential minimums removed for 3-50 unit buildings near high-frequency transit", CHK, "prior_partial_reforms"),
    ("Minneapolis", "Minnesota", "2016", "parking reduction (partial)", False, True,
     "Nonresidential minimums removed on select corridors", CHK, "prior_partial_reforms"),
    ("Lexington", "Kentucky", "2018", "parking reduction (partial)", False, True,
     "B-6P commercial center zone parking requirements dropped (about 2018)", CHK, "prior_partial_reforms"),
    ("St. Paul", "Minnesota", "2023", "middle-housing upzoning", True, False,
     "1-4 unit housing changes (2023-2024)", CHK, "simultaneous_zoning_changes"),
    ("Anchorage", "Alaska", "2024-01-01", "other (site access/bicycle code; not a housing reform)", False, False,
     "AO 2023-50 site access ordinance and bicycle provisions", CHK, "simultaneous_zoning_changes"),
    ("Gainesville", "Florida", "2022-10", "middle-housing upzoning", True, False,
     "Neighborhood Residential upzoning ending single-family-only zoning (repealed 2023)", CHK, "simultaneous_zoning_changes"),
    ("Hartford", "Connecticut", "2016-01-19", "comprehensive zoning rewrite", True, False,
     "New citywide form-based code (Zone Hartford); also removed minimums downtown and for retail/service uses", RT15, "rewrite_density_height_uses"),
    ("Alameda", "California", "2020-11", "upzoning (multifamily ban repealed)", True, False,
     "Measure Z repealed charter Article 26 ban on multifamily", CHK, "simultaneous_zoning_changes"),
    ("Alameda", "California", "2022", "housing element rezoning", True, False,
     "Housing Element rezoning (late 2022)", CHK, "simultaneous_zoning_changes"),
    ("Tigard", "Oregon", "2022", "middle-housing upzoning", True, False,
     "Housing-type chapters amended (Ord. 22-06), likely HB 2001 work (not verified)", CHK, "simultaneous_zoning_changes"),
    ("Tigard", "Oregon", "2017", "parking reduction (partial)", False, True,
     "Tigard Triangle lean code with no minimum parking", CHK, "prior_partial_reforms"),
    ("Dunwoody", "Georgia", "2018-12", "other (overlay amendment, content not coded)", False, False,
     "Dunwoody Village Overlay amendments", RT15, "same_time_changes_within_1yr"),
    ("Dunwoody", "Georgia", "2019-01", "other (overlay amendment, content not coded)", False, False,
     "Perimeter Center Overlay and SLUP-procedure text amendments", RT15, "same_time_changes_within_1yr"),
    ("Emeryville", "California", "2019-08-22", "height/development bonus amendment", True, False,
     "Ord. 19-009 height and development bonus sections 9-4.202/9-4.204 (content not read)", RT15, "same_time_changes_within_1yr"),
    ("Emeryville", "California", "2019-06-20", "other (use table, content not coded)", False, False,
     "Ord. 19-006 use table", RT15, "same_time_changes_within_1yr"),
    ("Emeryville", "California", "2020-12-15", "ADU ordinance", True, False,
     "ADU ordinance 20-027 (state ADU bills, no ADU parking)", CHK, "simultaneous_zoning_changes"),
    ("Emeryville", "California", "2013-03-07", "parking reduction (partial)", False, True,
     "2013 Planning Regulations (Ord. 13-001): minimums 33% below demand, TH overlay halved", CHK, "prior_partial_reforms"),
    ("Branson", "Missouri", "2017-02", "comprehensive zoning rewrite", True, False,
     "Zoning rewrite Ord. 2016-0193 (Dec 2016, effective Feb 2017)", RT15, "same_time_changes_within_1yr"),
    ("Canandaigua", "New York", "2020-03-16", "other (district amendments, content not read)", False, False,
     "L.L. 1-2020 amended AR-1, SCR-1, R-1-30, RLD districts", RT15, "same_time_changes_within_1yr"),
    ("Hudson", "New York", "2018-11-20", "other (commercial uses in R-2)", False, False,
     "L.L. 9-2018 commercial uses as conditional uses in R-2/R-2H", RT15, "same_time_changes_within_1yr"),
    ("Windham", "Maine", "2019-01-15", "other (cluster density bonus removed)", False, False,
     "Order 18-257 removed cluster density bonus in F/FR", RT15, "same_time_changes_within_1yr"),
    ("Sacramento", "California", "2024-09-17", "middle-housing upzoning", True, False,
     "Missing Middle interim ordinance 2024-0027", CHX, "simultaneous_zoning_changes"),
    ("Durham", "North Carolina", "2019", "middle-housing upzoning", True, False,
     "Expanding Housing Choices amendment", CHX, "prior_partial_reforms"),
    ("Richmond", "Virginia", "2023-09-25", "ADU ordinance", True, False, "ADUs permitted citywide", CHX, "simultaneous_zoning_changes"),
    ("Richmond", "Virginia", "2024-01-08", "TOD district amendment", True, False, "TOD-1 district amendments", CHX, "simultaneous_zoning_changes"),
    ("Salem", "Oregon", "2022", "middle-housing upzoning", True, False,
     "Our Salem comprehensive plan/rezoning and HB 2001 middle-housing code", CHX, "simultaneous_zoning_changes"),
    ("Salem", "Oregon", "2022-12-31", "parking reduction (state CFEC rule)", False, True,
     "Oregon CFEC Parking A rules applied", CHX, "prior_partial_reforms"),
    ("Eugene", "Oregon", "2022", "middle-housing upzoning", True, False, "HB 2001 middle-housing code", CHX, "simultaneous_zoning_changes"),
    ("Eugene", "Oregon", "2022-12-31", "parking reduction (state CFEC rule)", False, True,
     "CFEC Parking A: no minimums within 1/2 mile of frequent transit", CHX, "prior_partial_reforms"),
    ("Bend", "Oregon", "2022", "middle-housing upzoning", True, False, "HB 2001 middle-housing code", CHX, "simultaneous_zoning_changes"),
    ("Bend", "Oregon", "2022-12-31", "parking reduction (state CFEC rule)", False, True, "CFEC Parking A applied", CHX, "prior_partial_reforms"),
    ("Beaverton", "Oregon", "2022", "middle-housing upzoning", True, False, "HB 2001 middle-housing code", CHX, "simultaneous_zoning_changes"),
    ("Beaverton", "Oregon", "2022-12-31", "parking reduction (state CFEC rule)", False, True, "CFEC Parking A applied", CHX, "prior_partial_reforms"),
    ("Longmont", "Colorado", "2022", "parking reduction (partial)", False, True,
     "Multifamily in MU-D and MU-C exempted", CHX, "prior_partial_reforms"),
    ("Longmont", "Colorado", "2014", "parking reduction (partial)", False, True,
     "Commercial/industrial minimums removed", CHX, "prior_partial_reforms"),
    ("Springfield", "Oregon", "2022-12-31", "parking reduction (state CFEC rule)", False, True, "CFEC Parking A", CHX, "prior_partial_reforms"),
    ("Albany", "Oregon", "2022-12-31", "parking reduction (state CFEC rule)", False, True, "CFEC Parking A applied", CHX, "prior_partial_reforms"),
    ("La Crosse", "Wisconsin", "2022-03-10", "parking reduction (partial)", False, True,
     "Nonresidential uses in Local Business/Commercial/Community Business zones", CHX, "prior_partial_reforms"),
    ("Burlington", "Vermont", "2021", "parking reduction (partial)", False, True,
     "Minimums eliminated downtown / Multimodal Mixed Use district (about 2020-2021)", CHX, "prior_partial_reforms"),
    ("Grants Pass", "Oregon", "2023", "parking reduction (state CFEC rule)", False, True, "State CFEC rules", CHX, "prior_partial_reforms"),
    ("Tualatin", "Oregon", "2023-01-01", "parking reduction (state CFEC rule)", False, True, "State CFEC rules", CHX, "prior_partial_reforms"),
    ("West Linn", "Oregon", "2023", "parking reduction (state CFEC rule)", False, True, "State CFEC rules", CHX, "prior_partial_reforms"),
    ("Ashland", "Oregon", "2023-01-01", "parking reduction (state CFEC rule)", False, True, "State CFEC rules", CHX, "prior_partial_reforms"),
    ("Milwaukie", "Oregon", "2022", "middle-housing upzoning", True, False,
     "Middle housing code (Ord. 2218; also removed parking for duplex-to-quadplex and ADUs)", CHX, "prior_partial_reforms"),
    ("Milwaukie", "Oregon", "2023", "parking reduction (state CFEC rule)", False, True, "CFEC transit-area removal", CHX, "prior_partial_reforms"),
    ("Central Point", "Oregon", "2023-01-01", "parking reduction (state CFEC rule)", False, True, "State CFEC rules", CHX, "prior_partial_reforms"),
    ("Hanover", "New Hampshire", "2023-05-09", "parking reduction (partial)", False, True,
     "Town meeting cut minimums for ADUs, multifamily, PRDs and student residences", CHX, "prior_partial_reforms"),
    ("King City", "Oregon", "2023-10", "area plan upzoning", True, False,
     "Kingston Terrace Master Plan code, comp plan and TSP amendments (fall 2023)", CHX, "simultaneous_zoning_changes"),
    ("King City", "Oregon", "2023-10", "parking reduction (state CFEC rule)", False, True,
     "CDC amendments Ord. O-2023-04 removed some minimums under CFEC", CHX, "prior_partial_reforms"),
    ("South Bend (with unincorporated St. Joseph County)", "Indiana", "2019", "comprehensive zoning rewrite", True, False,
     "Citywide form-based zoning ordinance rewrite (missing-middle district, ADUs)", CHX, "simultaneous_zoning_changes"),
    ("South Bend (with unincorporated St. Joseph County)", "Indiana", "2017", "parking reduction (partial)", False, True,
     "Minimums removed in traditional business districts and downtown", CHX, "prior_partial_reforms"),
    ("Gastonia", "North Carolina", "2021-06-15", "middle-housing upzoning", True, False,
     "UDO amendments to R2D2 Revised Residential Development District (Jun 15 and Oct 19, 2021)", CHX, "simultaneous_zoning_changes"),
    ("Gastonia", "North Carolina", "2021-08-10", "middle-housing upzoning", True, False,
     "Multifamily allowances Ord. 21-742", CHX, "simultaneous_zoning_changes"),
    ("Cambridge", "Maryland", "2016-06-30", "parking reduction (partial)", False, True,
     "Ord. 1076: no parking in other downtown subdistricts if no neighborhood impact", CHK, "prior_partial_reforms"),
    ("Hampden", "Maine", "2025", "upzoning (multifamily/use table)", True, False, "Multifamily/use-table changes", CHX, "simultaneous_zoning_changes"),
]
NOT_CODED = {  # repeal places whose coding names reforms without a usable date (stated as gaps)
    "Culver City": "General Plan 2045 and 2021-2029 Housing Element rezoning around 2022-2023 (dates not verified)",
    "Corvallis": "HB 2001 middle-housing code implementation due mid-2022 (adoption date not verified)",
    "Northfield": "comprehensive plan update under way 2024 (no adoption date)",
    "Lexington": "ADU rules adopted separately (dates not verified)",
    "Anchorage": "earlier by-right parking reductions under Title 21 (dates not verified)",
}


def urls_of(text, n=3) -> str:
    u = re.findall(r"https?://[^\s;,\"]+", str(text or ""))
    return " ; ".join(list(dict.fromkeys(u))[:n])


def main() -> None:
    p = cmp.panel(rpc.read_bps_us())[["key", "state_fips", "name", "fips_place", "fips_mcd", "acs_geoid", "year", "pop"]]
    M = Matcher(p)
    states_fips = {v: k for k, v in rpc.STATE_FIPS.items()}
    rows: list[dict] = []

    # repeal places (the batch's 74): key and event year only
    b = pd.read_csv(REF / "batch_2026-11-05" / "parking_expanded_effects.csv", usecols=["prn_key", "place", "state", "key", "event_year", "status", "outcome"])
    rep = b[(b["status"] == "included") & (b["outcome"] == "all")].drop_duplicates("key")[["prn_key", "place", "state", "key", "event_year"]]
    rep_year = dict(zip(rep["key"], rep["event_year"].astype(int)))
    assert len(rep) == 74, len(rep)

    def place_row(state, name, **k):
        key, status, tried = M.match(state, name, k.pop("population", None))
        return row(bps_key=key, bps_name=M.name.get(key) if key else None, place=name, state=state, match_status=status,
                   note=(k.pop("note", None) or "") + ("" if tried == name else f" [matched as '{tried}']") or None, **k)

    # 1. state ADU laws -> every BPS place in the state
    s = pd.read_csv(REF / "statewide_states_laws.csv")
    for r in s.itertuples():
        st = ABBR[r.abbr]
        d = first_date(r.effective_date) or first_date(r.adopted_date)
        fld = "effective_date" if first_date(r.effective_date) else "adopted_date"
        for k in M.last.loc[M.last["state_fips"] == rpc.STATE_FIPS[st], "key"]:
            rows.append(row(bps_key=k, bps_name=M.name[k], place=M.name[k], state=st, scope="state", event_type="state ADU law",
                            description=str(r.key_laws)[:160], date_used=d, event_year=int(d[:4]), date_field_used=fld,
                            date_raw=str(r.effective_date), source_file="reference/statewide_states_laws.csv",
                            source_row=r.abbr, source_url=str(r.law_source)[:200], match_status="state law (all BPS places)"))

    # 2. tod_cases
    tc = pd.read_csv(REF / "tod_cases.csv")
    tod_years = {}   # (match name, state) -> {year: (date, field)}
    for r in tc.itertuples():
        fld, raw = ("effective_date", r.effective_date) if years_in(r.effective_date) else ("adoption_date", r.adoption_date)
        ys = years_in(raw)
        if r.country != "US":
            rows.append(row(place=r.city, state=r.state_or_province, event_type="TOD upzoning", description=r.reform_name,
                            date_used=first_date(raw), date_field_used=fld, date_raw=str(raw), source_file="reference/tod_cases.csv",
                            source_row=r.case_id, match_status="not US (no BPS place)", counted=False))
            continue
        names = [re.sub(r"\s*\(.*\)$", "", r.city).strip()]
        note = None
        if r.case_id == "ma_40r_transit_districts":
            names, note = ["Brockton", "Haverhill", "Lowell"], "named places only; 'smaller towns' not named in the list"
        if r.case_id == "mbta_communities_2021":
            rows.append(row(place=r.city, state=r.state_or_province, event_type="TOD upzoning", description=r.reform_name,
                            date_raw=str(raw), date_field_used=fld, source_file="reference/tod_cases.csv", source_row=r.case_id,
                            match_status="multi-place row; coded town by town from the MBTA compliance file", counted=False))
            continue
        if not ys:
            rows.append(row(place=r.city, state=r.state_or_province, event_type="TOD upzoning", description=r.reform_name,
                            date_raw=str(raw), date_field_used=fld, source_file="reference/tod_cases.csv", source_row=r.case_id,
                            match_status="no usable date", counted=False))
            continue
        for nm in names:
            for y in ys:
                d = date_for_year(raw, y)
                rr = place_row(r.state_or_province, nm, event_type="TOD upzoning", description=r.reform_name, date_used=d,
                               event_year=y, date_field_used=fld + (" (range expanded, one event per year)" if len(ys) > 1 else ""),
                               date_raw=str(raw), source_file="reference/tod_cases.csv", source_row=r.case_id, note=note)
                rows.append(rr)
                tod_years.setdefault((nm.lower(), r.state_or_province), {})[y] = (d, fld, r.case_id)

    # 3. tod_reform_density, deduplicated against tod_cases (same place and year)
    td = pd.read_csv(REF / "tod_reform_density.csv").drop_duplicates(["group", "place", "reform_year"])
    for r in td.itertuples():
        lab = str(r.place).strip()
        if "pooled" in lab.lower() and lab.lower() not in TOD_LABELS:
            continue  # pooled summary rows, not places
        nm, st = TOD_LABELS.get(lab.lower(), (lab, None))
        ys = years_in(r.reform_year)
        if st is None or not ys:
            rows.append(row(place=lab, event_type="TOD reform", date_raw=str(r.reform_year), source_file="reference/tod_reform_density.csv",
                            source_row=lab, match_status="no state or year", counted=False))
            continue
        tcases = tod_years.get((nm.lower(), st), {})
        if len(ys) > 1 and tcases:
            continue  # pooled multi-year rows (New York, Philadelphia): the tod_cases rows carry the dates
        for y in ys:
            if y in tcases:
                continue  # duplicate of a tod_cases row
            rows.append(place_row(st, nm, event_type="TOD reform", description=f"{lab} ({r.group})", date_used=str(y), event_year=y,
                                  date_field_used="reform_year", date_raw=str(r.reform_year),
                                  source_file="reference/tod_reform_density.csv", source_row=lab))

    # 4. other_cities_reforms
    oc = pd.read_csv(REF / "other_cities_reforms.csv")
    for i, r in oc.iterrows():
        st = OTHER_CITIES_STATE[r["jurisdiction"]]
        d = first_date(r["effective"]) or first_date(r["adopted"])
        fld = "effective" if first_date(r["effective"]) else "adopted"
        kind = "ADU or zoning ordinance"
        if r["level"] == "state":
            for k in M.last.loc[M.last["state_fips"] == rpc.STATE_FIPS[st], "key"]:
                rows.append(row(bps_key=k, bps_name=M.name[k], place=M.name[k], state=st, scope="state", event_type="state housing law",
                                description=r["measure"], date_used=d, event_year=int(d[:4]), date_field_used=fld, date_raw=str(r[fld]),
                                source_file="reference/other_cities_reforms.csv", source_row=f"row {i}", source_url=urls_of(r["source"]),
                                match_status="state law (all BPS places)"))
            continue
        rows.append(place_row(st, r["jurisdiction"].title(), event_type=kind, description=f"{r['measure']}: {str(r['change'])[:140]}",
                              date_used=d, event_year=int(d[:4]), date_field_used=fld, date_raw=str(r[fld]),
                              source_file="reference/other_cities_reforms.csv", source_row=f"row {i}", source_url=urls_of(r["source"])))

    # 5. PRN parking reforms, repeal places only (prior parking dose)
    tax = pd.read_csv(REF / "parking_reform_taxonomy.csv")
    own = dict(zip(rep["key"], rep["prn_key"]))
    rep_names = {(st, str(pl_).split(" (")[0].strip().lower()) for pl_, st in zip(rep["place"], rep["state"])}
    near = tax["prn_key"].isin(rep["prn_key"]).to_numpy() | np.array([(st, str(pl_).strip().lower()) in rep_names for pl_, st in zip(tax["place"], tax["state"])])
    for i, r in tax[near].iterrows():
        k = cmp.match_place(p, rpc.STATE_FIPS.get(r["state"], "??"), r["place"], r["population"])
        if k not in rep_year:
            continue
        if r["prn_key"] == own.get(k) and r["policy"] == "rm_min":
            continue  # the repeal itself
        d = first_date(r["adopted_date"])
        rows.append(row(bps_key=k, bps_name=M.name.get(k), place=r["place"], state=r["state"], event_type=f"PRN parking reform ({r['policy']}, {r['scope']})",
                        description=str(r["summary"])[:160], date_used=d, event_year=int(d[:4]) if d else np.nan,
                        date_field_used="adopted_date" if d else "none (undated in PRN)", date_raw=str(r["adopted_date"]),
                        source_file="reference/parking_reform_taxonomy.csv", source_row=r["prn_key"], source_url=urls_of(r["citation_urls"]),
                        match_status="matched", prior_parking_dose=True, counted=False,
                        note=None if d else "undated: cannot be placed before or after the repeal"))

    # 6. California rail openings, station point-in-place
    ro = pd.read_csv(REF / "ca_ab2097_rail_openings.csv")
    cb = RAW / "census_cb_2024"
    pl = geom.read_shapefile(cb / "cb_2024_us_place_500k.zip", columns=["GEOID"])
    ip = geom.points_in_polygons(ro["lon"].values, ro["lat"].values, pl.polys)
    cs = geom.read_shapefile(cb / "cb_2024_us_cousub_500k.zip", columns=["GEOID"])
    ic = geom.points_in_polygons(ro["lon"].values, ro["lat"].values, cs.polys)
    geo = M.last.set_index("acs_geoid")["key"]
    for j, r in ro.iterrows():
        pg = pl.attrs["GEOID"].values[ip[j]] if ip[j] >= 0 else None
        cg = cs.attrs["GEOID"].values[ic[j]] if ic[j] >= 0 else None
        k = geo.get("160|" + pg) if pg else None
        how = "matched (station point in place)" if k else None
        if k is None and cg:
            k = geo.get("060|" + cg)
            how = "matched (station point in county subdivision)" if k else None
        if how is None:
            how = "unmatched (station outside any BPS-reporting place)" if pg is None else f"unmatched (place {pg} not in BPS)"
        rail = r["mode"] != "ferry"
        rows.append(row(bps_key=k, bps_name=M.name.get(k) if k else None, place=f"{r['station_name']} station", state="California",
                        event_type=f"rail station {r['event']} ({r['mode']})", description=f"{r['system']}: {r['station_name']}",
                        date_used=first_date(r["date"]), event_year=int(str(r["date"])[:4]), date_field_used="date", date_raw=str(r["date"]),
                        source_file="reference/ca_ab2097_rail_openings.csv", source_row=f"row {j}", source_url=r["source_url"],
                        match_status=how, counted=bool(r["event"] == "opened" and rail),
                        note=None if (r["event"] == "opened" and rail) else ("ferry, not rail" if not rail else "closure, not an opening")))

    # 7. MBTA Communities: deadline year for compliant or conditional towns
    mb = pd.read_csv(RAW / "tod_mbta" / "compliance_status_2025-09-18.csv")
    for i, r in mb.iterrows():
        status = str(r["Compliance Status"]).strip()
        use = status in ("Compliant", "Conditional Compliance")
        d = pd.to_datetime(r["Compliance Deadlines"], format="%m/%d/%Y").date().isoformat()
        rows.append(place_row("Massachusetts", r["Municipality"].strip(), event_type="MBTA Communities multifamily zoning",
                              description=f"compliance status {status}", date_used=d, event_year=int(d[:4]),
                              date_field_used="Compliance Deadlines", date_raw=str(r["Compliance Deadlines"]),
                              source_file="data/raw/tod_mbta/compliance_status_2025-09-18.csv", source_row=r["Municipality"].strip(),
                              counted=use, note=None if use else f"status '{status}': not an event under the plan"))

    # 8. TOD Option D places and edge-test places; dates from tod_cases
    def label_rows(lab, src):
        m = re.match(r"^(.*?)[ _](\d{4})$", lab.strip())
        base, y = (m.group(1), int(m.group(2))) if m else (lab.strip(), None)
        nm, st = TOD_LABELS.get(base.lower(), (base, None))
        if st is None:
            return [row(place=lab, event_type="TOD reform", source_file=src, source_row=lab, match_status="no state", counted=False)]
        tcy = tod_years.get((nm.lower(), st), {})
        out = []
        ys = [y] if y else sorted(tcy)
        for yy in ys:
            if yy in tcy:
                d, fld, cid = tcy[yy]
                out.append(place_row(st, nm, event_type="TOD reform", description=lab, date_used=d, event_year=yy,
                                     date_field_used=f"tod_cases.csv {fld} ({cid})", source_file=src, source_row=lab))
            else:
                out.append(place_row(st, nm, event_type="TOD reform", description=lab, date_used=str(yy), event_year=yy,
                                     date_field_used="year in the place label (no tod_cases row with that year)", source_file=src,
                                     source_row=lab, note="date not in tod_cases"))
        return out
    so = pd.read_csv(REF / "tod_optiond_stopmodel_places.csv")
    for lab in so.loc[so["set"].isin(["D-11", "D-B"]), "city"].unique():
        rows.extend(label_rows(lab, "reference/tod_optiond_stopmodel_places.csv"))
    et = pd.read_csv(REF / "tod_causal_edge_test.csv")
    for lab in et["place"].unique():
        if re.match(r"(?i)^(pooled|all estimable|locked)", lab):
            continue
        rows.extend(label_rows(lab, "reference/tod_causal_edge_test.csv"))

    # 9. Wisconsin ADU rules: earliest ADU-allowing effective_from per place
    w = pd.read_csv(REF / "wi_adu_rules.csv", dtype={"jurisdiction_id": str})
    a = w[w["provision"].isin(["detached_allowed", "attached_allowed"]) & w["value"].isin(["by_right", "conditional"])]
    for jid, g in a.groupby("jurisdiction_id"):
        nm = g["jurisdiction_name"].iloc[0]
        g = g.dropna(subset=["effective_from"])
        if g.empty:
            rows.append(row(place=nm, state="Wisconsin", event_type="WI ADU rule", source_file="reference/wi_adu_rules.csv", source_row=jid,
                            match_status="no dated ADU-allowing rule", counted=False))
            continue
        g = g.sort_values("effective_from").iloc[0]
        rr = place_row("Wisconsin", nm, event_type="WI ADU rule", description=f"{g['provision']} = {g['value']}",
                       date_used=g["effective_from"], event_year=int(g["effective_from"][:4]), date_field_used="effective_from (earliest ADU-allowing)",
                       date_raw=g["effective_from"], source_file="reference/wi_adu_rules.csv", source_row=g["rule_id"], source_url=g["source_url"])
        if rr["bps_key"] and M.last.set_index("key").loc[rr["bps_key"], "fips_place"] != jid[-5:]:
            rr["note"] = (rr["note"] or "") + f" [check: BPS place code differs from jurisdiction_id {jid}]"
        if nm == "West Allis city":
            rr["note"] = (rr["note"] or "") + " same ordinance as the repeal (Ch. 19 rewrite O-2022-0024): part of the treatment"
            rr["counted"] = False
        rows.append(rr)

    # 10. hand-coded repeal-place reforms
    srcs = {}
    for f in (CHK, CHX):
        c = pd.read_csv(ROOT / f, dtype=str)
        srcs.update({(f, x.place): x.source_urls for x in c.itertuples()})
    t15 = pd.read_csv(ROOT / RT15, dtype=str)
    srcs.update({(RT15, x.place): x.sources for x in t15.itertuples()})
    by_place = {(x.place, x.state): x.key for x in rep.itertuples()}
    for (pl_, st, d, kind, counted, dose, desc, f, fld) in CODED:
        k = by_place[(pl_, st)]
        u = srcs.get((f, pl_)) or srcs.get((f, pl_.split(" (")[0]))
        rows.append(row(bps_key=k, bps_name=M.name.get(k), place=pl_, state=st, event_type=kind, description=desc, date_used=d,
                        event_year=int(d[:4]), date_field_used=f"coded from {fld}", date_raw=d, source_file=f, source_row=pl_,
                        source_url=urls_of(u), match_status="matched (repeal place)", prior_parking_dose=dose, counted=counted))

    ev = pd.DataFrame(rows)
    rep_name = dict(zip(rep["key"], rep["place"]))
    ev["bps_name"] = ev["bps_name"].where(ev["bps_name"].notna(), ev["bps_key"].map(rep_name))  # South Bend's combined area
    ev["repeal_place"] = ev["bps_key"].isin(rep_year)
    ev["repeal_event_year"] = ev["bps_key"].map(rep_year)
    # PRN parking reforms enter for repeal places only (audit addition 1); any other list's row for a repeal place keeps
    # its own label, and the repeal-place rows say where they fall against the repeal
    yr = ev["event_year"]
    E = ev["repeal_event_year"]
    ev["timing_vs_own_repeal"] = np.select(
        [~ev["repeal_place"], yr.isna(), yr < E - 3, yr < E, yr <= E + 3],
        ["", "undated", "before, more than 3 years", "before, within 3 years", "at or after, within 3 years"], "after, more than 3 years")
    ev["state_fips"] = ev["state"].map(rpc.STATE_FIPS)
    cols = ["bps_key", "bps_name", "place", "state", "state_fips", "scope", "event_type", "description", "date_used", "event_year",
            "date_field_used", "date_raw", "source_file", "source_row", "source_url", "match_status", "counted", "prior_parking_dose",
            "repeal_place", "repeal_event_year", "timing_vs_own_repeal", "note"]
    ev = ev[cols].sort_values(["scope", "state", "bps_key", "event_year", "source_file"], na_position="last").reset_index(drop=True)
    ev["event_year"] = ev["event_year"].astype("Int64")
    ev["repeal_event_year"] = ev["repeal_event_year"].astype("Int64")
    ev.to_csv(OUT, index=False)

    # report
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 80)
    plc = ev[ev["scope"] == "place"]
    print("rows", len(ev), "| place rows", len(plc), "| state-law rows", int((ev["scope"] == "state").sum()))
    print(ev.groupby(["source_file", "scope"]).agg(rows=("event_type", "size"), matched=("bps_key", lambda s: int(s.notna().sum()))).to_string())
    print(plc["match_status"].str.replace(r" \(.*", "", regex=True).value_counts().to_string())
    um = plc[plc["bps_key"].isna()]
    print("UNMATCHED / AMBIGUOUS / LEFT OUT place rows:")
    print(um[["source_file", "place", "state", "match_status", "event_year"]].drop_duplicates().to_string())
    print("repeal places with a counted separate reform within 3 years before:",
          sorted(set(map(str, plc[plc["repeal_place"] & plc["counted"] & (plc["timing_vs_own_repeal"] == "before, within 3 years")]["bps_name"]))))
    print("not coded (no usable date):", NOT_CODED)


if __name__ == "__main__":
    main()
