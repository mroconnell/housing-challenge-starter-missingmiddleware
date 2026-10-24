"""Readers for the California comparison inputs (HCD APR A2, the 2012-2019 ADU
compilation, ACS B25024 denominators, TIGER place classes, PEP housing units).

All readers are pure functions of file paths so tests run them on tiny fixtures.
Personal or locational fields in APR Table A2 (APN, prior APN, street address,
standardized address, project name, tracking id, notes, latitude/longitude) are
used only transiently, to detect repeated listings of the same permit, and never
leave this module. See docs/gate2/CA_COMPARISON_DATA.md.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.foundation.parsers import read_acs_sf, read_pep_housing_units

# ---------------------------------------------------------------------------
# HCD APR Table A2
# ---------------------------------------------------------------------------

UNIT_CATS = ("SFD", "SFA", "2 to 4", "5+", "ADU", "MH")
UNIT_CAT_CODE = {"SFD": "sfd", "SFA": "sfa", "2 to 4": "u2_4", "5+": "u5plus", "ADU": "adu", "MH": "mh"}
INCOME = ("ACUTELY_LOW_INCOME_DR", "ACUTELY_LOW_INCOME_NDR", "EXTREMELY_LOW_INCOME_DR",
          "EXTREMELY_LOW_INCOME_NDR", "VLOW_INCOME_DR", "VLOW_INCOME_NDR", "LOW_INCOME_DR",
          "LOW_INCOME_NDR", "MOD_INCOME_DR", "MOD_INCOME_NDR", "ABOVE_MOD_INCOME")
BP_INCOME_COLS = tuple(f"BP_{c}" for c in INCOME)
# Fields read from the raw file. The identifying ones (_KEY_COLS) are hashed
# into a project key and dropped immediately.
_KEY_COLS = ("APN", "STREET_ADDRESS", "JURS_TRACKING_ID")
APR_READ_COLS = ("JURIS_NAME", "CNTY_NAME", "YEAR", "UNIT_CAT", "NO_ENTITLEMENTS", "NO_BUILDING_PERMITS",
                 "NO_OTHER_FORMS_OF_READINESS", "BP_ISSUE_DT1", "DEM_DES_UNITS") + BP_INCOME_COLS + _KEY_COLS
DROPPED_APR_FIELDS = ("PRIOR_APN", "APN", "STREET_ADDRESS", "PROJECT_NAME", "JURS_TRACKING_ID", "NOTES",
                      "LATITUDE", "LONGITUDE", "STD_ADDRESS", "SCORE", "FIN_ASSIST_NAME")


def read_apr_a2(path: str | Path) -> pd.DataFrame:
    """Read Table A2 to a de-identified project-row frame.

    Returns one row per source row with: juris_name, cnty_name, year, unit_cat,
    ent_units, bp_units (NO_BUILDING_PERMITS), co_units (NO_OTHER_FORMS_OF_READINESS),
    bp_income_sum (sum of the 11 BP_* income columns), bp_issue_year, dem_units,
    and permit_key (SHA-1 of jurisdiction, tracking id, APN, address, permit date and
    unit category; not reversible to an address in practice and never written to
    processed outputs).
    """
    d = pd.read_csv(path, usecols=list(APR_READ_COLS), dtype=str, low_memory=False)
    for c in ("NO_ENTITLEMENTS", "NO_BUILDING_PERMITS", "NO_OTHER_FORMS_OF_READINESS", "DEM_DES_UNITS") + BP_INCOME_COLS:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    norm = {c: d[c].fillna("").str.strip().str.upper() for c in _KEY_COLS}
    raw_key = (d["JURIS_NAME"].fillna("") + "|" + norm["JURS_TRACKING_ID"] + "|" + norm["APN"] + "|"
               + norm["STREET_ADDRESS"] + "|" + d["BP_ISSUE_DT1"].fillna("") + "|" + d["UNIT_CAT"].fillna(""))
    out = pd.DataFrame({
        "juris_name": d["JURIS_NAME"].str.strip().str.upper(),
        "cnty_name": d["CNTY_NAME"].str.strip(),
        "year": pd.to_numeric(d["YEAR"], errors="coerce").astype("Int64"),
        "unit_cat": d["UNIT_CAT"].str.strip(),
        "ent_units": d["NO_ENTITLEMENTS"],
        "bp_units": d["NO_BUILDING_PERMITS"],
        "co_units": d["NO_OTHER_FORMS_OF_READINESS"],
        "bp_income_sum": d[list(BP_INCOME_COLS)].fillna(0).sum(axis=1),
        "bp_issue_year": pd.to_datetime(d["BP_ISSUE_DT1"], errors="coerce").dt.year.astype("Int64"),
        "dem_units": d["DEM_DES_UNITS"],
        "permit_key": raw_key.map(lambda s: hashlib.sha1(s.encode()).hexdigest()),
    })
    return out


def classify_permit_rows(rows: pd.DataFrame) -> pd.DataFrame:
    """Flag each row with permitted units by how its permit date relates to its report year.

    - date_in_year: permit issue date falls in the reporting year (the APR definition
      of "units issued building permits" this year).
    - date_missing: units reported with no permit date; kept in the primary measure.
    - date_earlier: permit date before the reporting year. `repeat` marks rows whose
      permit_key was also reported in another reporting year (a re-listing of a permit
      already counted); the rest are first reports of earlier permits (late reports).
    - date_later: permit date after the reporting year (data-entry errors).
    """
    r = rows.copy()
    has_bp = r["bp_units"].fillna(0) > 0
    r["date_status"] = np.select(
        [~has_bp.to_numpy(), r["bp_issue_year"].isna().to_numpy(),
         (r["bp_issue_year"] == r["year"]).fillna(False).to_numpy(dtype=bool),
         (r["bp_issue_year"] < r["year"]).fillna(False).to_numpy(dtype=bool)],
        ["no_permit", "date_missing", "date_in_year", "date_earlier"], default="date_later")
    years_per_key = r[has_bp].groupby("permit_key")["year"].nunique()
    r["repeat"] = has_bp & r["permit_key"].map(years_per_key).fillna(0).gt(1)
    return r


def aggregate_apr(rows: pd.DataFrame) -> pd.DataFrame:
    """Jurisdiction x reporting year x UNIT_CAT aggregate with three permit measures.

    bp_units_primary   = units with a permit date in the reporting year or no date
                         (pre-declared primary measure; avoids re-listed permits).
    bp_units_reported  = NO_BUILDING_PERMITS summed over all rows of the report (as published).
    bp_units_date_earlier / _repeat / _late_first, bp_units_date_later, bp_units_date_missing:
                         the components that separate the two.
    ent_units, co_units: entitlements and certificates of occupancy as reported (all rows).
    """
    r = classify_permit_rows(rows) if "date_status" not in rows else rows
    bp = r["bp_units"].fillna(0)
    earlier = r["date_status"] == "date_earlier"
    r = r.assign(
        bp_units_reported=bp,
        bp_units_primary=bp.where(r["date_status"].isin(["date_in_year", "date_missing"]), 0),
        bp_units_date_missing=bp.where(r["date_status"] == "date_missing", 0),
        bp_units_date_earlier=bp.where(earlier, 0),
        bp_units_date_earlier_repeat=bp.where(earlier & r["repeat"], 0),
        bp_units_date_earlier_late_first=bp.where(earlier & ~r["repeat"], 0),
        bp_units_date_later=bp.where(r["date_status"] == "date_later", 0),
        project_rows=1,
    )
    cols = ["project_rows", "bp_units_primary", "bp_units_reported", "bp_units_date_missing",
            "bp_units_date_earlier", "bp_units_date_earlier_repeat", "bp_units_date_earlier_late_first",
            "bp_units_date_later", "ent_units", "co_units", "dem_units"]
    g = r.groupby(["juris_name", "cnty_name", "year", "unit_cat"], dropna=False)[cols].sum(min_count=1).reset_index()
    g["source_id"] = "hcd_apr_a2"
    g["value_status"] = "observed"
    return g


def apr_by_issue_year(rows: pd.DataFrame) -> pd.DataFrame:
    """Alternative measure: permitted units assigned to the permit's issue year, each
    permit_key counted once (first report kept). Rows without a date use the report year.

    issue_year_flag marks dates that cannot be right as entered: 'after_first_report_year'
    (the permit is dated after the report year it was first listed in, e.g. 2109) and
    'before_2000' (e.g. 1916). They are kept and flagged, not corrected. Step 0 reads only
    issue years 2018-2025, so the flagged rows outside that window are ignored there."""
    r = rows[rows["bp_units"].fillna(0) > 0].sort_values("year")
    r = r.drop_duplicates("permit_key", keep="first")
    yr = r["bp_issue_year"].fillna(r["year"]).astype(int)
    flag = np.select([yr > r["year"].astype(int), yr < 2000], ["after_first_report_year", "before_2000"], default="ok")
    return (r.assign(issue_year=yr, issue_year_flag=flag)
            .groupby(["juris_name", "cnty_name", "issue_year", "unit_cat", "issue_year_flag"])["bp_units"]
            .sum().rename("bp_units_issue_year_dedup").reset_index())


def wide_by_unit_cat(agg: pd.DataFrame, value: str) -> pd.DataFrame:
    w = agg.pivot_table(index=["juris_name", "cnty_name", "year"], columns="unit_cat", values=value,
                        aggfunc="sum", fill_value=0)
    w = w.reindex(columns=list(UNIT_CATS), fill_value=0).rename(columns=UNIT_CAT_CODE).reset_index()
    w.columns.name = None
    return w


# ---------------------------------------------------------------------------
# Building an ADU 2012-2019 compilation
# ---------------------------------------------------------------------------

COMPILATION_YEARS = tuple(range(2012, 2020))


def read_compilation(path: str | Path) -> tuple[pd.DataFrame, list[list[str]]]:
    """Parse Sheet1 columns A-I (jurisdiction + 2012..2019) to long form.

    Returns (long frame: juris_name, year, adu_permits, value_status) and the
    non-empty cells to the right of column I (a side block on the sheet), which
    are reported separately and not used as data.
    """
    raw = pd.read_csv(path, header=None, dtype=str, keep_default_na=False)
    head = [h.strip() for h in raw.iloc[0, :9]]
    if head[0].lower() != "jurisdiction" or [int(float(h)) for h in head[1:9]] != list(COMPILATION_YEARS):
        raise ValueError(f"unexpected compilation header: {head}")
    main = raw.iloc[1:, :9].copy()
    main.columns = ["juris_name"] + list(COMPILATION_YEARS)
    main["juris_name"] = main["juris_name"].str.strip().str.upper()
    main = main[main["juris_name"] != ""]
    long = main.melt(id_vars="juris_name", var_name="year", value_name="adu_permits")
    long["year"] = long["year"].astype(int)
    long["adu_permits"] = pd.to_numeric(long["adu_permits"].str.replace(",", "").str.strip(), errors="coerce")
    long["value_status"] = np.where(long["adu_permits"].isna(), "missing", "observed")
    long["source_id"] = "buildinganadu_ca_2012_2019"
    side = [[c for c in row if str(c).strip()] for row in raw.iloc[:, 9:].values.tolist()]
    side = [r for r in side if r]
    return long.sort_values(["juris_name", "year"]).reset_index(drop=True), side


# ---------------------------------------------------------------------------
# TIGER place classes and ACS B25024 denominators
# ---------------------------------------------------------------------------

def read_tiger_places(path: str | Path) -> pd.DataFrame:
    import pyogrio

    t = pyogrio.read_dataframe(path, read_geometry=False, columns=["GEOID", "PLACEFP", "NAME", "NAMELSAD",
                                                                     "CLASSFP", "FUNCSTAT"])
    t = pd.DataFrame(t)
    t["incorporated"] = t["CLASSFP"].str.startswith("C") & (t["FUNCSTAT"] == "A")
    return t.rename(columns=str.lower)


def read_acs_b25024_ca(path: str | Path) -> pd.DataFrame:
    """B25024 rows for California state (040), counties (050), places (160) and
    place-within-county parts (155). Values: total units (E001), one-unit detached (E002)."""
    df = read_acs_sf(path, state_fips="06", sumlevels=("040", "050", "155", "160"))
    df["level"] = df["sumlevel"].map({"040": "state", "050": "county", "155": "place_county_part", "160": "place"})
    keep = ["geo_id", "sumlevel", "level", "geoid", "B25024_E001", "B25024_M001", "B25024_E002", "B25024_M002"]
    out = df[keep].rename(columns={"B25024_E001": "hu_total", "B25024_M001": "hu_total_moe",
                                   "B25024_E002": "sf_detached", "B25024_M002": "sf_detached_moe"})
    out["county_fips"] = np.select([out.sumlevel == "050", out.sumlevel == "155"],
                                   [out.geoid.str[2:5], out.geoid.str[7:10]], default=None)
    out["placefp"] = np.where(out.sumlevel.isin(["155", "160"]), out.geoid.str[2:7], None)
    return out


def ca_denominators(acs: pd.DataFrame, places: pd.DataFrame) -> pd.DataFrame:
    """One row per HCD-style jurisdiction: incorporated places and county remainders.

    County remainder = county total minus the sum of incorporated-place parts in
    that county (sumlevel 155). Remainder MOE is the root-sum-of-squares
    approximation (Census ACS handbook formula; overstates nothing but ignores
    covariance). San Francisco is a consolidated city-county: remainder is zero
    and the jurisdiction is the city row. Status: observed for places and counties,
    calculated for remainders.
    """
    inc = set(places.loc[places["incorporated"], "placefp"])
    names = places.set_index("placefp")["name"]
    pl = acs[(acs.sumlevel == "160") & acs.placefp.isin(inc)].copy()
    parts = acs[(acs.sumlevel == "155") & acs.placefp.isin(inc)]
    pl = pl.merge(parts.groupby("placefp")["county_fips"].first().rename("county_fips_part"),
                  left_on="placefp", right_index=True, how="left")
    pl["county_fips"] = pl["county_fips_part"]
    pl = pl.assign(geo_type="place", name=pl.placefp.map(names), value_status="observed")
    co = acs[acs.sumlevel == "050"].set_index("county_fips")
    sums = parts.groupby("county_fips")[["hu_total", "sf_detached"]].sum()
    moes = parts.groupby("county_fips")[["hu_total_moe", "sf_detached_moe"]].agg(lambda s: float(np.sqrt((s ** 2).sum())))
    rem = pd.DataFrame(index=co.index)
    rem["hu_total"] = co["hu_total"] - sums["hu_total"].reindex(co.index).fillna(0)
    rem["sf_detached"] = co["sf_detached"] - sums["sf_detached"].reindex(co.index).fillna(0)
    rem["hu_total_moe"] = np.sqrt(co["hu_total_moe"] ** 2 + moes["hu_total_moe"].reindex(co.index).fillna(0) ** 2)
    rem["sf_detached_moe"] = np.sqrt(co["sf_detached_moe"] ** 2 + moes["sf_detached_moe"].reindex(co.index).fillna(0) ** 2)
    rem = rem.reset_index()
    rem["geoid"] = "06" + rem["county_fips"] + "_UNINC"
    rem = rem.assign(geo_type="county_remainder", placefp=None, value_status="calculated")
    rem = rem[rem.county_fips != "075"]  # San Francisco: no unincorporated area
    cols = ["geo_type", "geoid", "placefp", "county_fips", "name", "hu_total", "hu_total_moe",
            "sf_detached", "sf_detached_moe", "value_status"]
    rem["name"] = None
    out = pd.concat([pl[cols], rem[cols]], ignore_index=True)
    out["source_id"] = "census_acs5_2024_tbsf"
    out["vintage"] = "ACS 2020-2024 5-year"
    return out


# ---------------------------------------------------------------------------
# PEP housing units (state rows), 2010-2025
# ---------------------------------------------------------------------------

def read_pep_v2020_state(path: str | Path) -> pd.DataFrame:
    d = pd.read_csv(path, dtype=str, encoding="latin-1")
    st = d[d["SUMLEV"] == "040"].iloc[0]
    rows = [{"name": st["STNAME"], "year": y, "housing_units": float(st[f"HUESTIMATE{y}"])}
            for y in range(2010, 2021)]
    return pd.DataFrame(rows)


def read_pep_v2025_state(path: str | Path) -> pd.DataFrame:
    d = read_pep_housing_units(path)
    state = d["name"].iloc[0]
    return d[d["name"] == state].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Names
# ---------------------------------------------------------------------------

def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = re.sub(r"\s+", " ", s.upper().replace(".", "").replace("-", " ")).strip()
    s = re.sub(r"^CITY OF ", "", s)
    s = re.sub(r"^ST ", "SAINT ", s)
    return s
