"""Out-of-state ADU permit series (Gate 3, owner request 2026-10-24).

Annual ADU permits issued in Seattle, Portland (OR), Austin, Denver and Minneapolis,
built from each city's official open permit data (plus Seattle's official OPCD annual
report), with ACS 2020-2024 5-year denominators and market variables, dated reform
timelines, and before/after rates per 1,000 one-unit detached homes per year.

Outcome definition (matches the California / Wisconsin ADU-type component):
  * counted: detached ADUs, attached ADUs and conversions (basement, garage, attic)
    added to a lot that already has a house, at permit issuance, by issue year;
  * excluded where identifiable: legalizations of existing unpermitted units
    (fixed text rule `LEGALIZATION_RE`), ADUs permitted together with a new primary
    house ("with new house"), voided/withdrawn/cancelled permits;
  * every city has its own fields, so each classifier records which fields and
    filters it used (see `METHODS`). Where a rule cannot be applied the gap is
    flagged, never silently filled.

Descriptive only. Before/after differences are associations around dated reforms in
places with strong and changing housing markets; they are not causal effects.
Everything except the `fetch_*` functions is a pure function of data frames so the
tests run offline on fixtures.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from missing_middleware.foundation.parsers import read_acs_sf
from missing_middleware.model.baseline import poisson_interval as _exact_poisson_interval

UA = "missing-middleware-other-cities/0.1 (housing research; public open data)"

# ---------------------------------------------------------------------------
# Places, ACS geographies
# ---------------------------------------------------------------------------

PLACES = {
    # city key: (display name, state fips, ACS place GEOID (sumlevel 160))
    "seattle": ("Seattle city, WA", "53", "5363000"),
    "portland": ("Portland city, OR", "41", "4159000"),
    "austin": ("Austin city, TX", "48", "4805000"),
    "denver": ("Denver city, CO", "08", "0820000"),
    "minneapolis": ("Minneapolis city, MN", "27", "2743000"),
    "madison": ("Madison city, WI", "55", "5548000"),
}

# ---------------------------------------------------------------------------
# Reform timeline (dated; status verified = read on an official/primary page,
# source_lead = secondary or not confirmed). Researched 2026-10-24.
# ---------------------------------------------------------------------------

REFORMS = [
    # city/state, level, id, adopted, effective, change, source, status
    ("seattle", "city", "Ord. 123141", "2009-11-02", "2009-12-04",
     "Detached ADUs (backyard cottages) allowed in all single-family zones; owner occupancy kept",
     "https://library.municode.com/wa/seattle/codes/municipal_code (SMC 23.44.041 history); DPD Backyard Cottages Annual Report", "source_lead (effective date)"),
    ("seattle", "city", "Ord. 125854 (CB 119544)", "2019-07-01", "2019-08-08",
     "Owner occupancy and off-street parking removed; 2 ADUs per lot (AADU+DADU or 2 AADUs; second needs green building or <=80% AMI); DADU cap 800->1,000 sq ft; min lot 4,000->3,200 sq ft",
     "https://seattle.legistar.com (CB 119544); https://seattle.gov/council/issues/past-issues/backyard-cottages-and-basement-units", "verified"),
    ("seattle", "city", "Ord. 127211 (CB 120949), HB 1337 compliance", "2025-05-06", "2025-06-30",
     "Two ADUs in any configuration incl. two DADUs; rules moved to SMC 23.42.022",
     "https://seattle.legistar.com (CB 120949)", "verified"),
    ("seattle", "city", "Ord. 127376 (CB 120993), HB 1110 permanent", "2025-12-16", "2026-01-21",
     "Neighborhood Residential zones rewritten: 4-6 units per lot; ADUs count toward density",
     "https://seattle.legistar.com (CB 120993)", "verified"),
    ("washington", "state", "EHB 1337 (Ch. 334, Laws of 2023)", "2023-05-08", "2023-07-23",
     "Cities in UGAs must allow 2 ADUs per lot, no owner occupancy, >=1,000 sq ft cap, impact fee <=50%; local rules due 6 months after next periodic plan update (King County cities: 2025-06-30)",
     "https://lawfilesext.leg.wa.gov/biennium/2023-24/Pdf/Bills/Session%20Laws/House/1337.SL.pdf", "verified"),
    ("portland", "city", "Res. 36766 (SDC waiver)", "2010-03-03", "2010-04-01",
     "System development charges waived for ADUs (to 2013-06-30); extended by Res. 36980 (to 2016-07-31) and Res. 37201 (to 2018-07-31)",
     "https://efiles.portlandoregon.gov (Ord. 189050 findings)", "verified (adoption); source_lead (start date)"),
    ("portland", "city", "Ord. 187471", "2015-12-02", "2016-01-01",
     "ADU siting/design relaxed (side/rear setbacks like garages)",
     "https://www.portland.gov/sites/default/files/code/205-acc-dwelling-unit.pdf", "verified (effective date)"),
    ("portland", "city", "Ord. 189050 (SDC exemption made permanent)", "2018-06-27", "2018-08-01",
     "Permanent SDC exemption only with a 10-year covenant against short-term rental",
     "https://www.portland.gov/code/17/14/070", "verified"),
    ("portland", "city", "Ord. 190093 (Residential Infill Project 1)", "2020-08-12", "2021-08-01",
     "Up to 4 units (6 affordable) in R7/R5/R2.5; a house may have 2 ADUs",
     "https://www.portland.gov/sites/default/files/2020-08/ordinance-190093-as-amended_final.pdf", "verified"),
    ("portland", "city", "Ord. 190851 (Residential Infill Project 2)", "2022-06-01", "2022-06-30",
     "RIP allowances extended to R10/R20; HB 2001 compliance",
     "https://www.portland.gov/bps/planning/rip2", "verified"),
    ("oregon", "state", "SB 1051 (2017)", "2017-08-15", "2018-07-01",
     "Cities >2,500 must allow an ADU with each detached house (reasonable siting/design rules)",
     "https://olis.oregonlegislature.gov (SB 1051 enrolled, 2017)", "verified"),
    ("oregon", "state", "HB 2001 (2019)", "2019-08-08", "2020-01-01",
     "ADU owner occupancy and off-street parking barred from 2020-01-01; middle housing in large cities by 2022-06-30",
     "https://www.oregon.gov/lcd/UP/Pages/Housing-Choices.aspx", "verified"),
    ("austin", "city", "Ord. 20151119-080", "2015-11-19", "2015-11-30",
     "ADU min lot 7,000 sq ft -> standard lot (5,750); size cap 850 -> 1,100 sq ft/0.15 FAR; no parking near transit corridors; separation 15->10 ft",
     "https://services.austintexas.gov/edims/document.cfm?id=243658", "verified"),
    ("austin", "city", "Ord. 20231207-001 (HOME phase 1)", "2023-12-07", "2024-02-05",
     "Up to 3 units per SF-1/2/3 lot; ADU uses replaced by two-unit / three-unit residential (permit category break)",
     "https://www.austintexas.gov/development-services/home-amendments", "verified"),
    ("austin", "city", "Ord. 20240516-006 (HOME phase 2)", "2024-05-16", "2024-08-16",
     "Small-lot single-family on lots 1,800-5,750 sq ft",
     "https://www.austintexas.gov/development-services/home-amendments", "verified"),
    ("denver", "city", "ADUs in Denver text amendment", "2023-06-05", "2023-07-05",
     "Form standards only (size, height, garage conversions); no rezoning, ADUs still needed zone-by-zone rezonings; owner occupancy kept",
     "https://www.denvergov.org (Community Planning and Development, Text Amendments, ADUs in Denver)", "verified"),
    ("denver", "city", "Citywide ADUs (HB24-1152 implementation)", "2024-11-18", "2024-12-16",
     "ADUs allowed in all residential areas (about 70% of land, up from 36%); owner-occupancy rule relaxed",
     "https://www.denvergov.org (Text Amendments, Citywide ADUs)", "verified"),
    ("colorado", "state", "HB24-1152", "2024-05-13", "2025-06-30",
     "Subject jurisdictions (MPO cities >=1,000) must allow 1 ADU where single-unit homes allowed, administrative approval, no new parking or owner-occupancy rules (compliance from 2025-06-30)",
     "https://leg.colorado.gov/bills/hb24-1152", "verified"),
    ("minneapolis", "city", "Ord. 2014-Or-116 to -122", "2014-12-05", "2014-12-05",
     "ADUs (internal, attached, detached) allowed with single- and two-family homes citywide; owner occupancy required",
     "https://www.minneapolismn.gov (Approved zoning code amendments)", "verified (adoption); source_lead (effective)"),
    ("minneapolis", "city", "Minneapolis 2040 / up to 3 units", "2019-11-08", "2020-01-01",
     "Up to 3 units on lower-density residential lots",
     "https://minneapolis2040.com/implementation/built-form-regulations/", "verified"),
    ("minneapolis", "city", "File 2019-01207 (owner occupancy removed)", "2021-02-26", "2021-02-26",
     "Owner occupancy removed for attached and detached ADUs (internal ADUs keep it)",
     "https://www.minneapolismn.gov (Approved zoning code amendments)", "verified (adoption); source_lead (effective)"),
]
REFORM_COLUMNS = ["jurisdiction", "level", "measure", "adopted", "effective", "change", "source", "status"]


def reforms_table() -> pd.DataFrame:
    return pd.DataFrame(REFORMS, columns=REFORM_COLUMNS)


# ---------------------------------------------------------------------------
# Shared text rules
# ---------------------------------------------------------------------------

ADU_TEXT_RE = re.compile(
    r"\bA?D?ADUS?\b|ACCESSORY\s+DWELLING|BACKYARD\s+COTTAGE|MOTHER[- ]IN[- ]LAW|SECONDARY\s+(?:APARTMENT|DWELLING|UNIT)|GARAGE\s+APARTMENT|GUEST\s+HOUSE",
    re.I)
# Legalization of an existing unpermitted unit. Minneapolis boilerplate ("this permit does
# not authorize existing finishes if built without a permit") is stripped first.
LEGALIZATION_RE = re.compile(
    r"LEGALI[SZ]|AS[- ]BUILT|UNPERMITTED|UN-PERMITTED|RETROACTIV|CODE\s+ENFORCEMENT|VIOLATION|WORK\s+DONE\s+WITHOUT",
    re.I)
_BOILERPLATE_RE = re.compile(r"THIS PERMIT DOES NOT AUTHORIZE[^*]*", re.I)
VOID_STATUS_RE = re.compile(r"VOID|WITHDRAWN|CANCEL", re.I)


def is_legalization(text: pd.Series) -> pd.Series:
    t = text.fillna("").astype(str).str.replace(_BOILERPLATE_RE, " ", regex=True)
    return t.str.contains(LEGALIZATION_RE)


def mentions_adu(text: pd.Series) -> pd.Series:
    return text.fillna("").astype(str).str.contains(ADU_TEXT_RE)


def _norm_addr(a: pd.Series) -> pd.Series:
    return (a.fillna("").astype(str).str.upper().str.replace(r"[^A-Z0-9 ]", " ", regex=True)
            .str.replace(r"\s+", " ", regex=True).str.strip())


def _same_site_within(d: pd.DataFrame, houses: pd.DataFrame, id_col: str, site_col: str,
                      date_col: str, days: int) -> pd.Series:
    """True where another permit in `houses` (same id/site/date column names) is at the
    same normalised site and issued within `days` of the ADU permit."""
    a = d[[id_col, site_col, date_col]].copy()
    h = houses[[id_col, site_col, date_col]].copy()
    for x in (a, h):
        x["_site"] = _norm_addr(x[site_col])
        x["_dt"] = pd.to_datetime(x[date_col], errors="coerce", utc=True)
    a, h = a[a["_site"].ne("") & a["_dt"].notna()], h[h["_site"].ne("") & h["_dt"].notna()]
    m = a.merge(h[["_site", "_dt", id_col]], on="_site", suffixes=("", "_h"))
    m = m[(m[id_col] != m[id_col + "_h"]) & ((m["_dt_h"] - m["_dt"]).abs() <= pd.Timedelta(days=days))]
    return d[id_col].isin(set(m[id_col]))


# Output columns of every classifier (one row per permit kept as an ADU candidate)
PERMIT_COLS = ["city", "permit_id", "issue_date", "year", "category", "adu_units",
               "legalization", "with_new_house", "counted"]
CATEGORIES = ("detached", "attached_or_conversion", "attached_and_detached", "unknown_type")


def _finish(df: pd.DataFrame, city: str) -> pd.DataFrame:
    df = df.copy()
    df["city"] = city
    df["issue_date"] = pd.to_datetime(df["issue_date"], errors="coerce", utc=True).dt.tz_localize(None)
    df = df[df["issue_date"].notna()]
    df["year"] = df["issue_date"].dt.year.astype(int)
    df["counted"] = ~df["legalization"] & ~df["with_new_house"]
    return df[PERMIT_COLS].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Seattle: SDCI Building Permits (Socrata 76t5-zqzr) + OPCD annual report
# ---------------------------------------------------------------------------

def classify_seattle(raw: pd.DataFrame, houses: pd.DataFrame | None = None) -> pd.DataFrame:
    """Rows: permittypemapped == 'Building', dwellingunittype lists an 'Accessory Dwelling'
    type, issued, not void. ADU units = number of ADU types listed (1 or 2); on ADU-only
    permits raised to housingunitsadded when larger (e.g. 2 AADUs). With new house =
    'Detached Single-Family' (or townhouse/rowhouse) also listed on a permittypedesc 'New'
    permit, or (needs `houses`) a separate new single-family permit at the same site
    address issued within 365 days (redevelopment: house and ADU on separate permits)."""
    d = raw[raw["permittypemapped"].eq("Building")].copy()
    dut = d["dwellingunittype"].fillna("")
    d = d[dut.str.contains("Accessory Dwelling")]
    d = d[d["issueddate"].notna()]
    d = d[~d["statuscurrent"].fillna("").str.contains(VOID_STATUS_RE)]
    types = d["dwellingunittype"].str.split(r",\s*")
    n_att = types.apply(lambda t: sum(x == "Accessory Dwelling Attached" for x in t))
    n_det = types.apply(lambda t: sum(x == "Accessory Dwelling Detached" for x in t))
    n_other = types.apply(lambda t: sum(not x.startswith("Accessory Dwelling") for x in t))
    added = pd.to_numeric(d["housingunitsadded"], errors="coerce").fillna(0)
    listed = n_att + n_det
    d["adu_units"] = listed.where(n_other.gt(0) | (listed >= added), added).clip(lower=1).astype(int)
    d["category"] = "attached_or_conversion"
    d.loc[n_det.gt(0) & n_att.eq(0), "category"] = "detached"
    d.loc[n_det.gt(0) & n_att.gt(0), "category"] = "attached_and_detached"
    principal = types.apply(lambda t: any(x in ("Detached Single-Family", "Townhouse", "Rowhouse") for x in t))
    d["with_new_house"] = principal & d["permittypedesc"].eq("New")
    if houses is not None and len(houses):
        d["with_new_house"] = d["with_new_house"] | _same_site_within(
            d, houses, "permitnum", "originaladdress1", "issueddate", days=365)
    d["legalization"] = is_legalization(d["description"])
    d = d.rename(columns={"permitnum": "permit_id", "issueddate": "issue_date"})
    return _finish(d, "seattle")


# Seattle OPCD 2024 ADU Annual Report (Nov 2025), Exhibit 10: units permitted by year
# issued (SDCI Accela data). 2025 is through Q2 only. Transcribed by the team.
SEATTLE_OPCD = {
    2010: (89, 55), 2011: (64, 43), 2012: (69, 46), 2013: (75, 50), 2014: (92, 63),
    2015: (104, 86), 2016: (154, 120), 2017: (137, 115), 2018: (126, 119), 2019: (155, 128),
    2020: (230, 246), 2021: (338, 424), 2022: (407, 517), 2023: (447, 458), 2024: (448, 465),
}
SEATTLE_OPCD_CONDO_SHARE = {2019: 0.10, 2020: 0.25, 2021: 0.45, 2022: 0.57, 2023: 0.58, 2024: 0.32}
SEATTLE_OPCD_URL = ("https://seattle.gov/documents/Departments/OPCD/OngoingInitiatives/"
                    "EncouragingBackyardCottages/OPCD-ADUAnnualReport2024.pdf")


def seattle_opcd_table() -> pd.DataFrame:
    rows = [{"year": y, "aadu_units": a, "dadu_units": b, "total_units": a + b,
             "condo_parcel_share": SEATTLE_OPCD_CONDO_SHARE.get(y)} for y, (a, b) in SEATTLE_OPCD.items()]
    out = pd.DataFrame(rows)
    out["source"] = "OPCD 2024 ADU Annual Report, Exhibit 10 (units permitted, by year issued)"
    return out


# ---------------------------------------------------------------------------
# Portland: BDS Residential Building Permits (PortlandMaps open data, layer 89)
# ---------------------------------------------------------------------------

def classify_portland(raw: pd.DataFrame) -> pd.DataFrame:
    """Rows: IS_ADU true, inside the city (PDXBND == YES), ISSUEDATE present, status
    not application/void. Detached = NEWCLASS 'New Construction' and NEWTYPE 'Accessory
    Dwelling Unit'; attached/conversion = NEWCLASS Alteration or Addition; with new house =
    New Construction of a Single Family Dwelling / Townhouse / Rowhouse / Duplex flagged
    IS_ADU (house + ADU on one permit). 'Move' permits (relocated structures) are
    unknown_type. ADU units = 1 per permit (NEW_UNITS counts the house too on combined
    permits; for ADU-only permits it is 1 in nearly all rows)."""
    d = raw[raw["IS_ADU"].astype(str).str.lower().eq("true")].copy()
    d = d[d["PDXBND"].astype(str).str.upper().eq("YES")]
    d = d[d["ISSUEDATE"].notna() & ~d["STATUS"].fillna("").str.contains(r"Application|VOID|Cancel", case=False)]
    cls = d["NEWCLASS"].fillna("")
    typ = d["NEWTYPE"].fillna("")
    d["category"] = "unknown_type"
    d.loc[cls.eq("New Construction") & typ.eq("Accessory Dwelling Unit"), "category"] = "detached"
    d.loc[cls.isin(["Alteration", "Addition"]), "category"] = "attached_or_conversion"
    d["with_new_house"] = cls.eq("New Construction") & ~typ.eq("Accessory Dwelling Unit")
    d["adu_units"] = 1
    d["legalization"] = is_legalization(d["FOLDER_DES"])
    d = d.rename(columns={"FOLDERNUMB": "permit_id", "ISSUEDATE": "issue_date"})
    d["issue_date"] = d["issue_date"].astype(str).str[:10].str.replace("/", "-")
    return _finish(d, "portland")


# ---------------------------------------------------------------------------
# Austin: Issued Construction Permits (Socrata 3syk-w9eu)
# ---------------------------------------------------------------------------

AUSTIN_ADU_CLASS = "R- 102 Secondary Apartment"
AUSTIN_TEXT_CLASSES = ("R- 101 Single Family Houses", "R- 434 Addition & Alterations",
                       "R- 435 Renovations/Remodel", "R- 330  Accessory Use to Primary")
AUSTIN_HOME_BREAK = 2024
NON_DWELLING_RE = r"NOT AN ADU|NON-DWELLING|NON DWELLING|NOT A DWELLING|NO KITCHEN"  # HOME phase 1 (2024-02-05) retired the secondary-apartment category


def classify_austin(raw: pd.DataFrame, houses: pd.DataFrame | None = None, include_text: bool = False) -> pd.DataFrame:
    """Main rule: building permits (permittype BP) in permit_class 'R- 102 Secondary
    Apartment' (the city's ADU class), status not VOID/Withdrawn, inside Austin full or
    limited purpose, housing_units not 0 and not described as a non-dwelling structure. ADU units = housing_units (min 1). With new house = a 'R- 101 Single
    Family Houses' permit on the same TCAD parcel issued within 365 days (needs `houses`;
    otherwise False). Detached vs attached is not coded: category unknown_type unless
    the description says garage conversion / attached / above garage.
    include_text=True also counts permits in AUSTIN_TEXT_CLASSES whose description
    mentions an ADU (sensitivity; those coded R-101 are treated as with-new-house when
    the description also mentions a new single family home)."""
    d = raw[raw["permittype"].eq("BP") & raw["issue_date"].notna()].copy()
    d = d[~d["status_current"].fillna("").str.contains(VOID_STATUS_RE)]
    d = d[d["jurisdiction"].fillna("").str.contains("AUSTIN FULL PURPOSE|AUSTIN LTD")]
    main = d["permit_class"].eq(AUSTIN_ADU_CLASS)
    keep = main
    if include_text:
        keep = main | (d["permit_class"].isin(AUSTIN_TEXT_CLASSES) & mentions_adu(d["description"]))
    d = d[keep].copy()
    hu0 = pd.to_numeric(d["housing_units"], errors="coerce")
    nondwelling = d["description"].fillna("").str.upper().str.contains(NON_DWELLING_RE)
    d = d[~(hu0.eq(0) | nondwelling)].copy()
    d["source_rule"] = d["permit_class"].where(d["permit_class"].eq(AUSTIN_ADU_CLASS), "text")
    hu = pd.to_numeric(d["housing_units"], errors="coerce").fillna(1)
    d["adu_units"] = hu.clip(lower=1, upper=2).astype(int)
    desc = d["description"].fillna("").str.upper()
    d["category"] = "unknown_type"
    d.loc[desc.str.contains(r"DETACHED|BACKYARD|BEHIND"), "category"] = "detached"
    d.loc[desc.str.contains(r"CONVER|ATTACHED|ABOVE (?:THE )?GARAGE|OVER (?:THE )?GARAGE|BASEMENT"), "category"] = "attached_or_conversion"
    d["with_new_house"] = False
    if houses is not None and len(houses):
        d["with_new_house"] = _same_site_within(d, houses, "permit_number", "tcad_id", "issue_date", days=365)
    text_new = d["source_rule"].eq("text") & d["permit_class"].eq("R- 101 Single Family Houses") & \
        desc.str.contains(r"NEW .{0,40}(?:SINGLE FAMILY|SFR|HOME|RESIDENCE)")
    d["with_new_house"] = d["with_new_house"] | text_new
    d["legalization"] = is_legalization(d["description"])
    d = d.rename(columns={"permit_number": "permit_id"})
    return _finish(d, "austin")


# ---------------------------------------------------------------------------
# Denver: Residential Construction Permits (ArcGIS ODC_DEV_RESIDENTIALCONSTPERMIT_P/316)
# ---------------------------------------------------------------------------

DENVER_ADU_CODE = "026"  # building statistics code for an accessory dwelling unit
DENVER_HOUSE_CODES = ("001", "002")  # one-family / two-family dwelling


def classify_denver(raw: pd.DataFrame) -> pd.DataFrame:
    """Rows: STAT_CODE_1 (or _2/_3) == '026' (ADU statistics code; confirmed by addresses
    such as '... 1/2', '... ADU'), CANCEL empty, CLASS not 'change of contractor' or
    'repair/replace' (those re-permit an existing ADU). Detached = CLASS 'New Building';
    attached/conversion = Addition, Alteration/Tenant Finish, Change of Use. With new
    house = '026' together with a dwelling code (001/002) on the same permit. The layer has
    no description text, so legalizations cannot be identified (flagged False)."""
    d = raw.copy()
    codes = d[["STAT_CODE_1", "STAT_CODE_2", "STAT_CODE_3"]].fillna("").astype(str)
    has_adu = codes.eq(DENVER_ADU_CODE).any(axis=1)
    has_house = codes.isin(DENVER_HOUSE_CODES).any(axis=1)
    d = d[has_adu & d["DATE_ISSUED"].notna()].copy()
    if "CANCEL" in d:
        d = d[d["CANCEL"].isna()]
    cls = d["CLASS"].fillna("").str.upper().str.replace(r"^\d+\s*-\s*", "", regex=True)
    d = d[~cls.str.contains("CONTRACTOR|REPAIR|WRECK|MOVE")]
    cls = cls.loc[d.index]
    d["category"] = "unknown_type"
    d.loc[cls.str.contains("NEW BUILDING"), "category"] = "detached"
    d.loc[cls.str.contains("ADDITION|ALTERATION|CHANGE OF USE"), "category"] = "attached_or_conversion"
    d["with_new_house"] = has_house.loc[d.index]
    d["adu_units"] = 1
    d["legalization"] = False
    d["issue_date"] = pd.to_datetime(d["DATE_ISSUED"], unit="ms", utc=True).dt.tz_convert("America/Denver")
    d["issue_date"] = d["issue_date"].dt.tz_localize(None)
    d = d.rename(columns={"PERMIT_NUM": "permit_id"})
    return _finish(d, "denver")


# ---------------------------------------------------------------------------
# Minneapolis: CCS Permits (ArcGIS CCS_Permits/0); records start Dec 2016
# ---------------------------------------------------------------------------

def classify_minneapolis(raw: pd.DataFrame) -> pd.DataFrame:
    """Rows: permitType 'Res' whose comments mention an ADU and do not say it is
    abandoned ('no longer will become ADU'). Several permits are often issued for one ADU
    (foundation, shell, finish), so permits are de-duplicated to one ADU per parcel (APN)
    per 24 months, keeping the first issued. Detached = occupancyType 'Accessory' or the
    text says detached/garage; otherwise attached_or_conversion. With new house = workType
    'New' on an SFD/TFD occupancy (house + ADU)."""
    d = raw[raw["permitType"].eq("Res") & raw["issueDate"].notna()].copy()
    d = d[mentions_adu(d["comments"])]
    txt = d["comments"].fillna("").str.upper()
    d = d[~txt.str.contains(r"NO LONGER (?:WILL )?(?:BE(?:COME)? )?(?:AN )?ADU|NOT AN ADU|REMOVE (?:THE )?ADU")]
    txt = txt.loc[d.index]
    d["issue_date"] = pd.to_datetime(d["issueDate"], unit="ms", utc=True).dt.tz_convert("America/Chicago").dt.tz_localize(None)
    d = d.sort_values("issue_date")
    key = d["APN"].fillna(d["Display"] if "Display" in d else d["permitNumber"])
    keep, last = [], {}
    for idx, k, t in zip(d.index, key, d["issue_date"]):
        if k in last and (t - last[k]) <= pd.Timedelta(days=730):
            continue
        last[k] = t
        keep.append(idx)
    d = d.loc[keep]
    txt = txt.loc[d.index]
    occ = d["occupancyType"].fillna("").str.strip()
    d["category"] = "attached_or_conversion"
    d.loc[occ.eq("Accessory") | txt.str.contains(r"DETACHED|GARAGE (?:WITH|W/) |ABOVE (?:A |THE )?(?:NEW )?(?:DETACHED )?GARAGE|OVER (?:A |THE )?GARAGE"), "category"] = "detached"
    d["with_new_house"] = d["workType"].eq("New") & occ.isin(["SFD", "TFD"])
    d["adu_units"] = 1
    d["legalization"] = is_legalization(d["comments"])
    d = d.rename(columns={"permitNumber": "permit_id"})
    return _finish(d, "minneapolis")


# ---------------------------------------------------------------------------
# Annual series and period rates
# ---------------------------------------------------------------------------

def annual_series(permits: pd.DataFrame, years: range) -> pd.DataFrame:
    """One row per city-year: counted ADU units by category, plus excluded units."""
    rows = []
    for (city, year), g in permits.groupby(["city", "year"]):
        c = g[g["counted"]]
        r = {"city": city, "year": year,
             "adu_units": int(c["adu_units"].sum()), "adu_permits": int(len(c)),
             "excluded_legalization": int(g.loc[g["legalization"], "adu_units"].sum()),
             "excluded_with_new_house": int(g.loc[g["with_new_house"] & ~g["legalization"], "adu_units"].sum())}
        for cat in CATEGORIES:
            r[f"units_{cat}"] = int(c.loc[c["category"].eq(cat), "adu_units"].sum())
        rows.append(r)
    out = pd.DataFrame(rows)
    full = pd.MultiIndex.from_product([sorted(permits["city"].unique()), list(years)], names=["city", "year"])
    # a covered year with no qualifying permit is a zero; callers mask years the source
    # does not cover (missing is never zero)
    out = out.set_index(["city", "year"]).reindex(full).fillna(0).astype(int).reset_index()
    return out


@dataclass(frozen=True)
class Period:
    city: str
    label: str
    first: int
    last: int
    regime: str
    note: str = ""


PERIODS = [
    Period("seattle", "pre_2019_reform", 2016, 2018, "DADUs citywide since 2009; owner occupancy + parking required"),
    Period("seattle", "long_pre", 2010, 2018, "same, longer window"),
    Period("seattle", "post_2019_ramp", 2020, 2020, "year 1 after Ord. 125854"),
    Period("seattle", "post_2019_plateau", 2021, 2024, "Ord. 125854 in force (before HB 1337 compliance 2025-06-30)"),
    Period("portland", "pre_sdc_waiver", 2007, 2009, "ADUs allowed, SDCs charged"),
    Period("portland", "sdc_waiver_ramp", 2011, 2015, "SDC waiver (from 2010)"),
    Period("portland", "sdc_deadline_peak", 2016, 2018, "waiver expiry deadline 2018-07-31"),
    Period("portland", "permanent_exemption_pre_rip", 2019, 2020, "exemption permanent with STR covenant; HB 2001 ADU rules 2020"),
    Period("portland", "post_rip", 2022, 2025, "Residential Infill Project (2021-08-01, 2022-06-30)"),
    Period("austin", "pre_2015_reform", 2012, 2014, "secondary apartments on 7,000 sq ft lots"),
    Period("austin", "post_2015_early", 2016, 2019, "Ord. 20151119-080"),
    Period("austin", "post_2015_late", 2020, 2023, "Ord. 20151119-080, before HOME"),
    Period("denver", "pre_2023", 2016, 2022, "ADUs only where zoning allowed (about 36% of land); owner occupancy"),
    Period("denver", "form_standards_2023", 2023, 2024, "2023 form-standard amendment; still zone-by-zone"),
    Period("denver", "citywide_2025", 2025, 2025, "citywide ADUs from 2024-12-16 (one year observed)"),
    Period("minneapolis", "post_2014_owner_occ", 2017, 2020, "2014 ordinance, owner occupancy (data start Dec 2016)"),
    Period("minneapolis", "post_owner_occ_removed", 2021, 2025, "owner occupancy removed 2021 (detached/attached)"),
]

# Comparable window used for regression/validation points
PLATEAU = (2023, 2025)
PRE_WAVE3 = (2017, 2019)


def poisson_interval(k: int, z: float = 1.959964) -> tuple[float, float]:
    """95% interval for a Poisson count: exact (Garwood, baseline.poisson_interval) up to
    k = 50, Wilson-Hilferty cube-root approximation above (relative error < 0.1%)."""
    if k <= 50:
        return _exact_poisson_interval(int(k))
    lo = k * (1 - 1 / (9 * k) - z / (3 * k ** 0.5)) ** 3
    k1 = k + 1
    hi = k1 * (1 - 1 / (9 * k1) + z / (3 * k1 ** 0.5)) ** 3
    return lo, hi


def period_rates(series: pd.DataFrame, homes: dict[str, float], periods=PERIODS, measure: str = "adu_units") -> pd.DataFrame:
    rows = []
    for p in periods:
        s = series[(series["city"] == p.city) & series["year"].between(p.first, p.last)]
        n_years = p.last - p.first + 1
        obs = s[measure].notna()
        missing = n_years - int(obs.sum())
        units = float(s.loc[obs, measure].sum())
        yrs = int(obs.sum())
        h = homes.get(p.city)
        if yrs == 0 or not h:
            rate = lo = hi = float("nan")
        else:
            rate = 1000.0 * units / (h * yrs)
            plo, phi = poisson_interval(int(round(units)))
            lo, hi = 1000.0 * plo / (h * yrs), 1000.0 * phi / (h * yrs)
        rows.append({"city": p.city, "period": p.label, "first_year": p.first, "last_year": p.last,
                     "years_observed": yrs, "years_missing": missing, "measure": measure,
                     "adu_units": units, "homes": h, "rate_per_1000_yr": rate,
                     "poisson95_lo": lo, "poisson95_hi": hi, "regime": p.regime})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# ACS denominators and market variables (ACS 2020-2024 5-year, place level)
# ---------------------------------------------------------------------------

def acs_places(b25024: Path, market: dict[str, Path]) -> pd.DataFrame:
    """One row per city: one-unit detached homes (B25024_E002), median home value
    (B25077), median gross rent (B25064), median household income (B19013) with MOEs."""
    rows = []
    for city, (name, st, geoid) in PLACES.items():
        r = {"city": city, "place": name, "geoid": geoid}
        d = read_acs_sf(b25024, state_fips=st, sumlevels=("160",))
        d = d[d["geoid"] == geoid]
        r["homes"], r["homes_moe"] = float(d["B25024_E002"].iloc[0]), float(d["B25024_M002"].iloc[0])
        r["all_units"] = float(d["B25024_E001"].iloc[0])
        for t, col, key in (("b25077", "B25077", "value"), ("b25064", "B25064", "rent"), ("b19013", "B19013", "income")):
            if t not in market:
                continue
            m = read_acs_sf(market[t], state_fips=st, sumlevels=("160",))
            m = m[m["geoid"] == geoid]
            r[key], r[f"{key}_moe"] = float(m[f"{col}_E001"].iloc[0]), float(m[f"{col}_M001"].iloc[0])
        rows.append(r)
    out = pd.DataFrame(rows)
    out["vintage"] = "ACS 2020-2024 5-year (table-based summary file)"
    return out


# ---------------------------------------------------------------------------
# Downloads (network; not used by tests)
# ---------------------------------------------------------------------------

def _record(folder: Path, name: str, url: str, extra: dict | None = None) -> None:
    man_path = folder / "_downloads.json"
    man = json.loads(man_path.read_text()) if man_path.exists() else {}
    p = folder / name
    man[name] = {"url": url, "accessed": dt.date.today().isoformat(), "bytes": p.stat().st_size,
                 "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), **(extra or {})}
    man_path.write_text(json.dumps(man, indent=2, sort_keys=True))


def _get(url: str, timeout: int = 300) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_socrata_csv(folder: Path, name: str, base: str, select: str, where: str,
                      license_: str, page: int = 50000, log=print) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    parts, offset = [], 0
    while True:
        q = urllib.parse.urlencode({"$select": select, "$where": where, "$order": ":id",
                                    "$limit": page, "$offset": offset})
        url = f"{base}?{q}"
        log(f"fetching {base} offset {offset}")
        chunk = pd.read_csv(io.BytesIO(_get(url)), dtype=str)
        parts.append(chunk)
        if len(chunk) < page:
            break
        offset += page
    pd.concat(parts, ignore_index=True).to_csv(path, index=False)
    _record(folder, name, base, {"select": select, "where": where, "license": license_})
    return path


def fetch_arcgis(folder: Path, name: str, layer: str, where: str, fields: str, license_: str,
                 page: int = 2000, log=print) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    rows, offset = [], 0
    while True:
        q = urllib.parse.urlencode({"where": where, "outFields": fields, "returnGeometry": "false",
                                    "orderByFields": "OBJECTID", "resultOffset": offset,
                                    "resultRecordCount": page, "f": "json"})
        d = json.loads(_get(f"{layer}/query?{q}"))
        if "error" in d:
            raise RuntimeError(d["error"])
        feats = [f["attributes"] for f in d.get("features", [])]
        rows += feats
        log(f"fetched {layer} {len(rows)}")
        if not feats or not d.get("exceededTransferLimit", len(feats) == page):
            break
        offset += len(feats)
    pd.DataFrame(rows).to_csv(path, index=False)
    _record(folder, name, layer, {"where": where, "fields": fields, "license": license_})
    return path


def fetch_url(folder: Path, name: str, url: str, license_: str, log=print) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    log(f"fetching {url}")
    path.write_bytes(_get(url, timeout=600))
    _record(folder, name, url, {"license": license_})
    return path


# Suitability of each city as a point for the market-adjusted California regression
# (ca_regression.py) or as an out-of-sample check. Judgement recorded with reasons.
POINT_SUITABILITY = {
    "seattle": ("validation", "strong",
                "Official series; open data within 2% of OPCD every year. Plateau 2023-2024 only (field stops 2025-07). "
                "Reform was a city rights change in 2019, not a state mandate; market far above Wisconsin."),
    "portland": ("validation", "strong",
                 "Clean flagged open data since 1995. Changes were fee-driven (SDC waiver) then RIP; the 2023-2025 level is "
                 "after a peak-and-decline, so it is not a post-mandate plateau comparable with California's."),
    "austin": ("validation_weak", "weak",
               "ADU category retired by HOME on 2024-02-05, so the 2023-2025 window has one year (2023). Most secondary "
               "apartments are built with a new house (same-parcel match, a heuristic). Attached vs detached not coded."),
    "denver": ("validation", "moderate",
               "Statistics code 026 is reliable for detached ADUs; conversions/attached are under-identified and "
               "legalizations cannot be screened (no text). 2023-2025 mixes zone-by-zone legality with one citywide year."),
    "minneapolis": ("validation", "moderate",
                    "Closest Midwest analogue. Text-matched permits, de-duplicated per parcel; data start Dec 2016 so no "
                    "pre-2014 baseline. Small counts (13-16 a year)."),
}


METHODS = {
    "seattle": ("Primary: OPCD 2024 ADU Annual Report Exhibit 10 (official; units permitted by issue year, "
                "AADU+DADU, includes ADUs built with new houses and on condo parcels; no legalization screen). "
                "Cross-check: SDCI Building Permits (data.seattle.gov 76t5-zqzr), permittypemapped=Building, "
                "dwellingunittype contains 'Accessory Dwelling', issued, not void; units = ADU types listed / "
                "housingunitsadded; with-new-house = SFD/townhouse also listed on a 'New' permit; legalization by text."),
    "portland": ("BDS Residential Building Permits (PortlandMaps open data layer 89: permits creating >=1 unit since 1995), "
                 "IS_ADU=True, PDXBND=YES, ISSUEDATE year; detached = New Construction of NEWTYPE ADU; conversion/attached = "
                 "Alteration/Addition; with-new-house = New Construction of a house flagged IS_ADU; 1 ADU per permit; legalization by text (FOLDER_DES)."),
    "austin": ("Issued Construction Permits (data.austintexas.gov 3syk-w9eu), permittype BP, permit_class 'R- 102 Secondary Apartment', "
               "full/limited purpose, not VOID/Withdrawn, calendar issue year; units = housing_units (1-2); with-new-house = R-101 permit "
               "on the same TCAD parcel within 365 days; legalization by text. Category retired by HOME (2024-02-05): 2024+ not comparable."),
    "denver": ("Residential Construction Permits (Denver Open Data, Accela RESCON, ArcGIS layer 316), building statistics code 026 (ADU) "
               "on any of STAT_CODE_1-3, not cancelled, excluding change-of-contractor/repair/move; detached = New Building, "
               "attached/conversion = Addition/Alteration/Change of Use; with-new-house = 026 with a dwelling code 001/002; "
               "no description field, so no legalization screen. Complete from 2016 (Accela went live 2015-06-07)."),
    "minneapolis": ("CCS Permits (opendata.minneapolismn.gov, ArcGIS CCS_Permits/0), permitType Res whose comments mention an ADU, "
                    "one ADU per parcel (APN) per 24 months; records start 2016-12; legalization by text; with-new-house = New SFD/TFD."),
}
