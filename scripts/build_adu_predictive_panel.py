"""ADU predictive test: build the panel (rows, outcome, treatment) and the census variables.

Plan: docs/adu/PREDICTIVE_PLAN.md (written before any outcome was computed). Results: docs/adu/PREDICTIVE_RESULTS.md.

    set -a; source .env; set +a                                   # CENSUS_API_KEY, never written to any file
    uv run --all-extras python scripts/build_adu_predictive_panel.py --fetch   # ACS API, TIGER tracts, permit points
    uv run --all-extras python scripts/build_adu_predictive_panel.py           # build from the caches

Fetch (network) writes only to data/raw/acs_api_adu/ (git-ignored), each folder with a _downloads.json that lists
the URL WITHOUT the key, the access date, bytes and SHA-256:
    acs/            Census Data API, ACS 2020-2024 5-year detailed tables (tracts in 6 states, all places,
                    counties and states, Wisconsin county subdivisions); groups/ holds the table metadata
    tiger/          TIGER/Line 2024 tract shapefiles for WA, OR, TX, CO, MN (WI is already in data/raw/tiger_wi)
    permit_points/  permit number + point only, from the same city open-data layers the repo already caches
                    (Seattle and Austin Socrata latitude/longitude; Denver and Minneapolis ArcGIS points).
                    No geocoding service is used; no names or addresses are requested.

Build writes data/processed/adu_predictive/ (panel.parquet, features.parquet, members.parquet, wi_features.parquet,
tract_assignment.json) and reference/adu_predictive_variables.csv, reference/adu_predictive_panel_summary.csv.

Units: a rate is ADU permits in a year / thousands of one-unit detached homes (ACS 2020-2024 B25024_002).
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REFERENCE = ROOT / "reference"
ADIR = RAW / "acs_api_adu"
OUT = PROCESSED / "adu_predictive"
UA = "missing-middleware-adu-predictive/0.1 (housing research; public open data)"
API = "https://api.census.gov/data/2024/acs/acs5"

TRACT_STATES = {"53": "WA", "41": "OR", "48": "TX", "08": "CO", "27": "MN", "55": "WI"}
CITY_PLACE = {"seattle": "5363000", "portland": "4159000", "austin": "4805000", "denver": "0820000",
              "minneapolis": "2743000", "madison": "5548000"}
CITY_STATE = {"seattle": "WA", "portland": "OR", "austin": "TX", "denver": "CO", "minneapolis": "MN", "madison": "WI"}

# ---------------------------------------------------------------------------
# 1. Treatment coding (PREDICTIVE_PLAN.md section 3)
# ---------------------------------------------------------------------------
STRONG = {"CA", "WA", "OR", "ME", "MA", "CO"}        # Mercatus 2025 strong (STATEWIDE_STATES.md)
WEAKER = {"RI", "UT", "VT"}
VACANT_LOT_FACTOR = 1 - 0.049                        # AQ-039, as pooled_revision.VACANT_LOT_SHARE
MINNEAPOLIS_FACTOR = 1 - 0.127                       # pooled_revision.MINNEAPOLIS_DUPLEX_SHARE
CA_LAW_YEAR1 = 2017                                  # first statewide law, effective 2017-01-01


def _span(a, b, law, local, k0=None):
    return {y: (law, local, None if k0 is None else k0 + (y - a)) for y in range(a, b + 1)}


TRACT_CODING = {   # city -> {year: (law, local, k)}; the adopted pooled_regression.CITY_CODING, Madison added
    "seattle": {**_span(2016, 2018, 0, 1), **_span(2020, 2023, 0, 1), **_span(2024, 2024, 1, 1, 2)},
    "portland": _span(2019, 2025, 1, 1, 1),
    "austin": {**_span(2012, 2014, 0, 0), **_span(2016, 2023, 0, 1)},
    "denver": {**_span(2016, 2023, 0, 0), **_span(2025, 2025, 1, 1, 1)},
    "minneapolis": _span(2017, 2025, 0, 1),
    "madison": _span(2014, 2025, 0, 1),
}
AGG_CODING = {   # statewide_states_annual series -> (cluster, feature geography, {year: (law, local, k)})
    "RI_statewide": ("RI", "state:44", {**_span(2021, 2023, 0, 0), **_span(2025, 2025, 1, 0, 1)}),
    "MA_statewide": ("MA", "state:25", _span(2025, 2025, 1, 0, 1)),
    "ME_statewide": ("ME", "state:23", _span(2025, 2025, 1, 0, 1)),
    "UT_mih": ("UT", "state:49", _span(2023, 2025, 1, 0, 2)),
    "VT_chittenden": ("VT", "county:50007", _span(2021, 2024, 1, 0, 1)),
    "HI_honolulu": ("HI", "county:15003", _span(2016, 2024, 0, 1)),
    "MD_montgomery": ("MD", "county:24031", _span(2019, 2025, 0, 1)),
    "MT_bozeman": ("MT", "place:3008950", _span(2020, 2023, 0, 1)),
}
WA_CODING = {**_span(2019, 2023, 0, 0), **_span(2024, 2026, 1, 0, 1)}
OR_CODING = _span(2019, 2022, 1, 0, 1)
DLCD_YEARS = {"hb4006_167078.txt": 2022, "hb4006_274745.txt": 2023}

# ---------------------------------------------------------------------------
# 2. ACS tables and variables (PREDICTIVE_PLAN.md section 4)
# ---------------------------------------------------------------------------
PARTIAL = {"B07001": ["B07001_001E", "B07001_017E"], "B17001": ["B17001_001E", "B17001_002E"]}
TABLES = ("B25024 B25034 B25035 B25002 B25003 B25018 B25017 B25041 B25014 B25039 B07001 B25064 B25057 B25059 "
          "B25077 B25076 B25078 B25070 B25071 B25081 B25088 B25092 B25105 B25010 B01002 B01001 B11005 B11001 "
          "B15002 B19013 B19301 B19001 B19083 B17001 B19058 B23025 B20002 B25044 B25046 B08301 B08013 B08303 "
          "B08302 B08008 B25001 B01003 B25032 B25004 B25021 B25075 B11007 B11016").split()
END_YEAR = 2024


def _s(c, *names):
    return sum(c[n] for n in names)


def _r(c, a, *b):
    return lambda c: _s(c, *a) / _s(c, *b)


def L(t, *lines):
    return [f"{t}_{i:03d}" for i in lines]


# kind: share / ratio / years / minutes / count (unit-free as entered) or dollar / density (rank and log ratio only)
VARIABLES = [
    # id, label, group, kind, formula(c)
    ("h01_share_1unit_detached", "Homes in 1-unit detached buildings", "stock", "share", lambda c: c.B25024_002 / c.B25024_001),
    ("h02_share_1unit_attached", "Homes in 1-unit attached buildings", "stock", "share", lambda c: c.B25024_003 / c.B25024_001),
    ("h03_share_2to4_units", "Homes in buildings of 2-4 units", "stock", "share", lambda c: (c.B25024_004 + c.B25024_005) / c.B25024_001),
    ("h04_share_5to19_units", "Homes in buildings of 5-19 units", "stock", "share", lambda c: (c.B25024_006 + c.B25024_007) / c.B25024_001),
    ("h05_share_20to49_units", "Homes in buildings of 20-49 units", "stock", "share", lambda c: c.B25024_008 / c.B25024_001),
    ("h06_share_50plus_units", "Homes in buildings of 50+ units", "stock", "share", lambda c: c.B25024_009 / c.B25024_001),
    ("h07_share_mobile_other", "Mobile homes and other", "stock", "share", lambda c: (c.B25024_010 + c.B25024_011) / c.B25024_001),
    ("h08_share_built_2000_on", "Homes built 2000 or later", "stock", "share", lambda c: (c.B25034_002 + c.B25034_003 + c.B25034_004) / c.B25034_001),
    ("h09_share_built_1980_99", "Homes built 1980-1999", "stock", "share", lambda c: (c.B25034_005 + c.B25034_006) / c.B25034_001),
    ("h10_share_built_1960_79", "Homes built 1960-1979", "stock", "share", lambda c: (c.B25034_007 + c.B25034_008) / c.B25034_001),
    ("h11_share_built_1940_59", "Homes built 1940-1959", "stock", "share", lambda c: (c.B25034_009 + c.B25034_010) / c.B25034_001),
    ("h12_share_built_pre1940", "Homes built before 1940", "stock", "share", lambda c: c.B25034_011 / c.B25034_001),
    ("h13_median_building_age", "Median building age (years before 2024)", "stock", "years", lambda c: END_YEAR - c.B25035_001),
    ("h14_vacancy_rate", "Vacant homes", "stock", "share", lambda c: c.B25002_003 / c.B25002_001),
    ("h15_owner_share", "Owner-occupied homes", "stock", "share", lambda c: c.B25003_002 / c.B25003_001),
    ("h16_median_rooms", "Median rooms", "stock", "count", lambda c: c.B25018_001),
    ("h17_share_1to3_rooms", "Homes with 1-3 rooms", "stock", "share", lambda c: (c.B25017_002 + c.B25017_003 + c.B25017_004) / c.B25017_001),
    ("h18_share_0to1_bedrooms", "Homes with 0-1 bedrooms", "stock", "share", lambda c: (c.B25041_002 + c.B25041_003) / c.B25041_001),
    ("h19_share_crowded", "Homes with more than 1 person per room", "stock", "share",
     lambda c: (c.B25014_005 + c.B25014_006 + c.B25014_007 + c.B25014_011 + c.B25014_012 + c.B25014_013) / c.B25014_001),
    ("h20_years_since_moved_in", "Median years since householder moved in", "stock", "years", lambda c: END_YEAR - c.B25039_001),
    ("h21_share_moved_last_year", "People who moved in the last year", "stock", "share", lambda c: (c.B07001_001 - c.B07001_017) / c.B07001_001),
    ("c01_median_rent", "Median gross rent", "costs", "dollar", lambda c: c.B25064_001),
    ("c02_rent_lower_quartile", "Lower contract rent quartile", "costs", "dollar", lambda c: c.B25057_001),
    ("c03_rent_upper_quartile", "Upper contract rent quartile", "costs", "dollar", lambda c: c.B25059_001),
    ("c04_median_value", "Median home value", "costs", "dollar", lambda c: c.B25077_001),
    ("c05_value_lower_quartile", "Lower home value quartile", "costs", "dollar", lambda c: c.B25076_001),
    ("c06_value_upper_quartile", "Upper home value quartile", "costs", "dollar", lambda c: c.B25078_001),
    ("c07_rent_burden_30", "Renters paying 30%+ of income", "costs", "share",
     lambda c: (c.B25070_007 + c.B25070_008 + c.B25070_009 + c.B25070_010) / (c.B25070_001 - c.B25070_011)),
    ("c08_rent_burden_50", "Renters paying 50%+ of income", "costs", "share", lambda c: c.B25070_010 / (c.B25070_001 - c.B25070_011)),
    ("c09_median_rent_pct_income", "Median rent as % of income", "costs", "ratio", lambda c: c.B25071_001),
    ("c10_share_with_mortgage", "Owner homes with a mortgage", "costs", "share", lambda c: c.B25081_002 / c.B25081_001),
    ("c11_owner_costs_mortgaged", "Median monthly owner costs, mortgaged", "costs", "dollar", lambda c: c.B25088_002),
    ("c12_owner_costs_pct_income", "Median owner costs as % of income", "costs", "ratio", lambda c: c.B25092_001),
    ("c13_median_housing_costs", "Median monthly housing costs", "costs", "dollar", lambda c: c.B25105_001),
    ("c14_value_to_annual_rent", "Median value / (12 x median rent)", "costs", "ratio", lambda c: c.B25077_001 / (12 * c.B25064_001)),
    ("p01_household_size", "Average household size", "people", "count", lambda c: c.B25010_001),
    ("p02_median_age", "Median age", "people", "years", lambda c: c.B01002_001),
    ("p03_share_under18", "People under 18", "people", "share",
     lambda c: _s(c, *L("B01001", 3, 4, 5, 6, 27, 28, 29, 30)) / c.B01001_001),
    ("p04_share_18to34", "People 18-34", "people", "share",
     lambda c: _s(c, *L("B01001", *range(7, 13), *range(31, 37))) / c.B01001_001),
    ("p05_share_35to64", "People 35-64", "people", "share",
     lambda c: _s(c, *L("B01001", *range(13, 20), *range(37, 44))) / c.B01001_001),
    ("p06_share_65plus", "People 65+", "people", "share",
     lambda c: _s(c, *L("B01001", *range(20, 26), *range(44, 50))) / c.B01001_001),
    ("p07_share_hh_children", "Households with children", "people", "share", lambda c: c.B11005_002 / c.B11005_001),
    ("p08_share_living_alone", "Householders living alone", "people", "share", lambda c: c.B11001_008 / c.B11001_001),
    ("p09_share_bachelors_plus", "Adults 25+ with a bachelor's degree or more", "people", "share",
     lambda c: _s(c, *L("B15002", 15, 16, 17, 18, 32, 33, 34, 35)) / c.B15002_001),
    ("p10_share_no_hs_diploma", "Adults 25+ without a high-school diploma", "people", "share",
     lambda c: _s(c, *L("B15002", *range(3, 11), *range(20, 28))) / c.B15002_001),
    ("p11_median_income", "Median household income", "people", "dollar", lambda c: c.B19013_001),
    ("p12_per_capita_income", "Per-capita income", "people", "dollar", lambda c: c.B19301_001),
    ("p13_share_income_under25k", "Households under $25k", "people", "share", lambda c: _s(c, *L("B19001", 2, 3, 4, 5)) / c.B19001_001),
    ("p14_share_income_25to50k", "Households $25-50k", "people", "share", lambda c: _s(c, *L("B19001", 6, 7, 8, 9, 10)) / c.B19001_001),
    ("p15_share_income_50to100k", "Households $50-100k", "people", "share", lambda c: _s(c, *L("B19001", 11, 12, 13)) / c.B19001_001),
    ("p16_share_income_100k_plus", "Households $100k+", "people", "share", lambda c: _s(c, *L("B19001", 14, 15, 16, 17)) / c.B19001_001),
    ("p17_gini", "Gini index", "people", "ratio", lambda c: c.B19083_001),
    ("p18_poverty_rate", "People below poverty", "people", "share", lambda c: c.B17001_002 / c.B17001_001),
    ("p19_share_snap", "Households with public assistance or SNAP", "people", "share", lambda c: c.B19058_002 / c.B19058_001),
    ("p20_labour_force_participation", "People 16+ in the labour force", "people", "share", lambda c: c.B23025_002 / c.B23025_001),
    ("p21_unemployment_rate", "Unemployed share of civilian labour force", "people", "share", lambda c: c.B23025_005 / c.B23025_003),
    ("p22_median_earnings", "Median earnings", "people", "dollar", lambda c: c.B20002_001),
    ("m01_share_no_vehicle", "Households with no vehicle", "mobility", "share", lambda c: (c.B25044_003 + c.B25044_010) / c.B25044_001),
    ("m02_share_2plus_vehicles", "Households with 2+ vehicles", "mobility", "share",
     lambda c: _s(c, *L("B25044", 5, 6, 7, 8, 12, 13, 14, 15)) / c.B25044_001),
    ("m03_vehicles_per_household", "Vehicles per household", "mobility", "count", lambda c: c.B25046_001 / c.B25044_001),
    ("m04_commute_drove_alone", "Workers who drove alone", "mobility", "share", lambda c: c.B08301_003 / c.B08301_001),
    ("m05_commute_carpool", "Workers who carpooled", "mobility", "share", lambda c: c.B08301_004 / c.B08301_001),
    ("m06_commute_transit", "Workers using transit", "mobility", "share", lambda c: c.B08301_010 / c.B08301_001),
    ("m07_commute_walk", "Workers who walked", "mobility", "share", lambda c: c.B08301_019 / c.B08301_001),
    ("m08_commute_bicycle", "Workers who cycled", "mobility", "share", lambda c: c.B08301_018 / c.B08301_001),
    ("m09_work_from_home", "Workers working from home", "mobility", "share", lambda c: c.B08301_021 / c.B08301_001),
    ("m10_mean_commute_minutes", "Mean commute (minutes)", "mobility", "minutes", lambda c: c.B08013_001 / (c.B08301_001 - c.B08301_021)),
    ("m11_share_commute_under15", "Commutes under 15 minutes", "mobility", "share", lambda c: _s(c, *L("B08303", 2, 3, 4)) / c.B08303_001),
    ("m12_share_commute_15to29", "Commutes 15-29 minutes", "mobility", "share", lambda c: _s(c, *L("B08303", 5, 6, 7)) / c.B08303_001),
    ("m13_share_commute_30to44", "Commutes 30-44 minutes", "mobility", "share", lambda c: _s(c, *L("B08303", 8, 9, 10)) / c.B08303_001),
    ("m14_share_commute_45plus", "Commutes 45+ minutes", "mobility", "share", lambda c: _s(c, *L("B08303", 11, 12, 13)) / c.B08303_001),
    ("m15_leave_before_7am", "Leave for work before 7am", "mobility", "share", lambda c: _s(c, *L("B08302", 2, 3, 4, 5, 6)) / c.B08302_001),
    ("m16_leave_7_to_9am", "Leave for work 7-9am", "mobility", "share", lambda c: _s(c, *L("B08302", 7, 8, 9, 10)) / c.B08302_001),
    ("m17_leave_9am_or_later", "Leave for work 9am or later", "mobility", "share", lambda c: _s(c, *L("B08302", 11, 12, 13, 14, 15)) / c.B08302_001),
    ("m18_work_in_home_place", "Workers working in their place of residence", "mobility", "share", lambda c: c.B08008_003 / c.B08008_001),
    ("l01_homes_per_sqmi", "Homes per square mile", "place", "density", lambda c: c.B25001_001 / c.land_sqmi),
    ("l02_people_per_sqmi", "People per square mile", "place", "density", lambda c: c.B01003_001 / c.land_sqmi),
    ("l03_land_sqmi", "Land area (square miles)", "place", "density", lambda c: c.land_sqmi),
    # ADU-relevant additions
    ("a01_owner_1unit_detached_share", "Homes that are owner-occupied 1-unit detached", "adu", "share", lambda c: c.B25032_003 / c.B25032_001),
    ("a02_owner_share_of_detached", "Owner share among occupied 1-unit detached homes", "adu", "share",
     lambda c: c.B25032_003 / (c.B25032_003 + c.B25032_014)),
    ("a03_renter_detached_share", "Renter-occupied 1-unit detached homes / all renter homes", "adu", "share", lambda c: c.B25032_014 / c.B25032_013),
    ("a04_owner_median_rooms", "Median rooms, owner homes", "adu", "count", lambda c: c.B25021_002),
    ("a05_share_4plus_bedrooms", "Homes with 4+ bedrooms", "adu", "share", lambda c: (c.B25041_006 + c.B25041_007) / c.B25041_001),
    ("a06_share_value_500k_plus", "Owner homes worth $500k+", "adu", "share", lambda c: _s(c, *L("B25075", *range(23, 28))) / c.B25075_001),
    ("a07_share_value_under200k", "Owner homes worth under $200k", "adu", "share", lambda c: _s(c, *L("B25075", *range(2, 19))) / c.B25075_001),
    ("a08_share_built_2010_on", "Homes built 2010 or later", "adu", "share", lambda c: (c.B25034_002 + c.B25034_003) / c.B25034_001),
    ("a09_seasonal_vacancy_share", "Homes vacant for seasonal use", "adu", "share", lambda c: c.B25004_006 / c.B25002_001),
    ("a10_share_65plus_alone", "Households of one person 65+", "adu", "share", lambda c: c.B11007_003 / c.B11007_001),
    ("a11_share_hh_with_65plus", "Households with someone 65+", "adu", "share", lambda c: c.B11007_002 / c.B11007_001),
    ("a12_share_hh_4plus_people", "Households of 4+ people", "adu", "share",
     lambda c: _s(c, *L("B11016", 5, 6, 7, 8, 13, 14, 15, 16)) / c.B11016_001),
    ("a13_value_to_income", "Median value / median household income", "adu", "ratio", lambda c: c.B25077_001 / c.B19013_001),
    ("a14_share_commute_60plus", "Commutes 60+ minutes", "adu", "share", lambda c: (c.B08303_012 + c.B08303_013) / c.B08303_001),
    ("a15_owner_household_size", "Average household size, owner homes", "adu", "count", lambda c: c.B25010_002),
    ("a16_renter_household_size", "Average household size, renter homes", "adu", "count", lambda c: c.B25010_003),
    ("a17_years_since_moved_owner", "Median years since moved in, owners", "adu", "years", lambda c: END_YEAR - c.B25039_002),
    ("a18_owner_costs_no_mortgage", "Median monthly owner costs, no mortgage", "adu", "dollar", lambda c: c.B25088_003),
    ("a19_median_earnings_male_over_female", "Median earnings, men / women", "adu", "ratio", lambda c: c.B20002_002 / c.B20002_003),
    ("a20_detached_homes_count", "One-unit detached homes", "adu", "density", lambda c: c.B25024_002),
]
UNIT_FREE = {"share", "ratio", "years", "minutes", "count"}


# ---------------------------------------------------------------------------
# 3. Network fetch (never logs or saves the key)
# ---------------------------------------------------------------------------

def _get(url: str, timeout: int = 300, tries: int = 4) -> bytes:
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as ex:  # noqa: BLE001
            if i == tries - 1:
                raise RuntimeError(re.sub(r"key=[^&\s]+", "key=REDACTED", str(ex))) from None
            time.sleep(3 * (i + 1))
    raise RuntimeError("unreachable")


def _record(folder: Path, name: str, url: str, extra: dict | None = None) -> None:
    assert "key=" not in url, "never record the API key"
    man_path = folder / "_downloads.json"
    man = json.loads(man_path.read_text()) if man_path.exists() else {}
    p = folder / name
    man[name] = {"url": url, "accessed": dt.date.today().isoformat(), "bytes": p.stat().st_size,
                 "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), **(extra or {})}
    man_path.write_text(json.dumps(man, indent=2, sort_keys=True))


def table_vars(t: str) -> list[str]:
    if t in PARTIAL:
        return PARTIAL[t]
    meta = json.loads((ADIR / "groups" / f"{t}.json").read_text())["variables"]
    return sorted(v for v in meta if re.fullmatch(rf"{t}_\d{{3}}E", v))


def acs_geos() -> list[tuple[str, str, str]]:
    """(level, 'for' clause, 'in' clause)."""
    g = [(f"tract{st}", "tract:*", f"state:{st}") for st in TRACT_STATES]
    g += [("place", "place:*", ""), ("county", "county:*", ""), ("state", "state:*", ""),
          ("cousub55", "county subdivision:*", "state:55")]
    return g


def fetch_acs(log=print) -> None:
    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        raise SystemExit("CENSUS_API_KEY is not set (run: set -a; source .env; set +a)")
    (ADIR / "groups").mkdir(parents=True, exist_ok=True)
    folder = ADIR / "acs"
    folder.mkdir(parents=True, exist_ok=True)
    for t in TABLES:
        p = ADIR / "groups" / f"{t}.json"
        if not p.exists():
            url = f"{API}/groups/{t}.json"
            p.write_bytes(_get(url))
            _record(ADIR / "groups", p.name, url, {"license": "Public domain (Census Bureau)"})
    jobs = []
    for t in TABLES:
        vs = table_vars(t)
        for i in range(0, len(vs), 48):
            chunk = vs[i:i + 48]
            for level, f, inn in acs_geos():
                name = f"{t}_{i // 48}_{level}.json"
                q = {"get": ",".join(chunk), "for": f}
                if inn:
                    q["in"] = inn
                jobs.append((name, f"{API}?{urllib.parse.urlencode(q, safe=':*,')}"))

    def run(job):
        name, url = job
        path = folder / name
        if path.exists() and path.stat().st_size > 0:
            return name, False
        path.write_bytes(_get(f"{url}&key={key}"))
        return name, True

    done = 0
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for name, new in ex.map(run, jobs):
            done += 1
            if done % 50 == 0:
                log(f"ACS {done}/{len(jobs)}")
    for name, url in jobs:      # manifest after the fact, URL without the key
        _record(folder, name, url, {"dataset": "ACS 2020-2024 5-year detailed tables (Census Data API)",
                                    "license": "Public domain (17 U.S.C. 105); Census API terms of service"})


def fetch_tiger(log=print) -> None:
    folder = ADIR / "tiger"
    folder.mkdir(parents=True, exist_ok=True)
    for st in ("53", "41", "48", "08", "27"):
        name = f"tl_2024_{st}_tract.zip"
        url = f"https://www2.census.gov/geo/tiger/TIGER2024/TRACT/{name}"
        if not (folder / name).exists():
            log(f"fetching {url}")
            (folder / name).write_bytes(_get(url))
        _record(folder, name, url, {"license": "Public domain (Census Bureau TIGER/Line 2024)"})
    name = "2024_Gaz_counties_national.zip"
    url = f"https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/{name}"
    if not (folder / name).exists():
        (folder / name).write_bytes(_get(url))
    _record(folder, name, url, {"license": "Public domain (Census Bureau Gazetteer 2024)"})


SEA = "https://data.seattle.gov/resource/76t5-zqzr.csv"
AUS = "https://data.austintexas.gov/resource/3syk-w9eu.csv"
DEN = "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_DEV_RESIDENTIALCONSTPERMIT_P/FeatureServer/316"
MSP = "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/CCS_Permits/FeatureServer/0"


def _socrata(base: str, select: str, where: str, page: int = 50000) -> pd.DataFrame:
    parts, offset = [], 0
    while True:
        q = urllib.parse.urlencode({"$select": select, "$where": where, "$order": ":id", "$limit": page, "$offset": offset})
        chunk = pd.read_csv(__import__("io").BytesIO(_get(f"{base}?{q}")), dtype=str)
        parts.append(chunk)
        if len(chunk) < page:
            break
        offset += page
    return pd.concat(parts, ignore_index=True)


def _arcgis_points(layer: str, where: str, id_field: str, page: int = 2000) -> pd.DataFrame:
    rows, offset = [], 0
    while True:
        q = urllib.parse.urlencode({"where": where, "outFields": id_field, "returnGeometry": "true", "outSR": "4326",
                                    "orderByFields": "OBJECTID", "resultOffset": offset, "resultRecordCount": page,
                                    "f": "json"})
        d = json.loads(_get(f"{layer}/query?{q}"))
        if "error" in d:
            raise RuntimeError(d["error"])
        feats = d.get("features", [])
        for f in feats:
            g = f.get("geometry") or {}
            rows.append({id_field: f["attributes"].get(id_field), "longitude": g.get("x"), "latitude": g.get("y")})
        if not feats or not d.get("exceededTransferLimit", len(feats) == page):
            break
        offset += len(feats)
    return pd.DataFrame(rows)


def fetch_points(log=print) -> None:
    """Permit number + point for the ADU permits the repo already classifies (same layers, same filters)."""
    import build_other_cities as boc
    from missing_middleware.comparison import other_cities as oc
    folder = ADIR / "permit_points"
    folder.mkdir(parents=True, exist_ok=True)
    jobs = {
        "seattle_adu_points.csv": (SEA, lambda: _socrata(SEA, "permitnum,latitude,longitude",
            f"permittypemapped='Building' AND (dwellingunittype like '%Accessory Dwelling%' OR {boc.soql_kw('description')})"),
            "Public Domain (data.seattle.gov)"),
        "austin_adu_points.csv": (AUS, lambda: _socrata(AUS, "permit_number,latitude,longitude",
            f"permittype='BP' AND permit_class='{oc.AUSTIN_ADU_CLASS}'"), "Public Domain U.S. Government (data.austintexas.gov)"),
        "denver_adu_points.csv": (DEN, lambda: _arcgis_points(DEN, "STAT_CODE_1='026' OR STAT_CODE_2='026' OR STAT_CODE_3='026'",
                                                               "PERMIT_NUM"), "City and County of Denver open data"),
        "minneapolis_adu_points.csv": (MSP, lambda: _arcgis_points(
            MSP, "permitType='Res' AND (UPPER(comments) LIKE '%ADU%' OR UPPER(comments) LIKE '%ACCESSORY DWELLING%')",
            "permitNumber"), "City of Minneapolis open data"),
    }
    for name, (url, fn, lic) in jobs.items():
        if (folder / name).exists():
            continue
        log(f"fetching points {name}")
        fn().to_csv(folder / name, index=False)
        _record(folder, name, url, {"fields": "permit number, latitude, longitude only", "license": lic})


# ---------------------------------------------------------------------------
# 4. ACS cells -> variables (pure functions, tested offline)
# ---------------------------------------------------------------------------

def geo_key(level: str, row: dict) -> str:
    if level.startswith("tract"):
        return f"tract:{row['state']}{row['county']}{row['tract']}"
    if level == "place":
        return f"place:{row['state']}{row['place']}"
    if level == "county":
        return f"county:{row['state']}{row['county']}"
    if level == "state":
        return f"state:{row['state']}"
    if level.startswith("cousub"):
        return f"cousub:{row['state']}{row['county']}{row['county subdivision']}"
    raise ValueError(level)


def read_acs_cells(folder: Path = ADIR / "acs") -> pd.DataFrame:
    """Every cached API response -> one wide frame (index geo key, columns like B25024_002).
    ACS placeholder values (negative) are missing."""
    frames: dict[str, list[pd.DataFrame]] = {}
    for p in sorted(folder.glob("*.json")):
        if p.name.startswith("_"):
            continue
        level = p.stem.split("_", 2)[2]
        d = json.loads(p.read_text())
        df = pd.DataFrame(d[1:], columns=d[0])
        df.index = [geo_key(level, r) for r in df.to_dict("records")]
        vals = df[[c for c in df.columns if re.fullmatch(r"B\d{5}_\d{3}E", c)]].apply(pd.to_numeric, errors="coerce")
        vals = vals.mask(vals < 0)
        vals.columns = [c[:-1] for c in vals.columns]
        frames.setdefault(level, []).append(vals)
    out = []
    for level, fs in frames.items():
        w = pd.concat(fs, axis=1)
        w = w.loc[:, ~w.columns.duplicated()]
        out.append(w)
    cells = pd.concat(out, axis=0)
    return cells[~cells.index.duplicated()]


def compute_variables(cells: pd.DataFrame) -> pd.DataFrame:
    """Raw cells (+ land_sqmi) -> the VARIABLES table (inf -> NaN)."""
    c = cells
    out = {}
    with np.errstate(divide="ignore", invalid="ignore"):
        for vid, _, _, _, f in VARIABLES:
            try:
                v = f(c)
            except AttributeError as e:
                raise KeyError(f"{vid}: missing ACS cell {e}") from None
            out[vid] = pd.to_numeric(v, errors="coerce").replace([np.inf, -np.inf], np.nan)
    return pd.DataFrame(out, index=cells.index)


def weighted_rank(x: pd.Series, w: pd.Series) -> pd.Series:
    """Homes-weighted mid-rank in [0, 1] within one context (ties share the mid-point); NaN stays NaN."""
    ok = x.notna()
    r = pd.Series(np.nan, index=x.index)
    if ok.sum() == 0:
        return r
    xs, ws = x[ok], w[ok].clip(lower=0).fillna(0) + 1e-9
    order = xs.sort_values(kind="mergesort")
    cw = ws[order.index].cumsum()
    tot = cw.iloc[-1]
    mid = (cw - ws[order.index] / 2) / tot
    # equal values get the mean mid-rank
    mid = mid.groupby(order.values).transform("mean")
    r[mid.index] = mid.values
    return r


def transform_features(vals: pd.DataFrame, context: pd.Series, homes: pd.Series,
                       aggregate: pd.Series | None = None) -> pd.DataFrame:
    """PREDICTIVE_PLAN section 4: unit-free kinds enter as they are; dollar and density kinds enter only as the
    homes-weighted rank within the row's context and the log ratio to the context's homes-weighted mean.
    An aggregate row (its own context) gets rank 0.5 and log ratio 0. Missing values take the context's
    homes-weighted mean (unit-free kinds) or rank 0.5 / ratio 0, with a per-variable missing flag."""
    kinds = {v[0]: v[3] for v in VARIABLES}
    agg = aggregate if aggregate is not None else pd.Series(False, index=vals.index)
    out = {}
    for vid in vals.columns:
        x = vals[vid].astype(float)
        miss = x.isna()
        if kinds[vid] in UNIT_FREE:
            fill = x.copy()
            for ctx, idx in vals.groupby(context).groups.items():
                xi, wi = x[idx], homes[idx].fillna(0)
                okk = xi.notna() & (wi > 0)
                m = np.average(xi[okk], weights=wi[okk]) if okk.any() else (xi.mean() if xi.notna().any() else np.nan)
                fill[idx] = xi.fillna(m)
            out[vid] = fill.fillna(fill.mean())
        else:
            rk = pd.Series(np.nan, index=x.index)
            lr = pd.Series(np.nan, index=x.index)
            lx = np.log(x.where(x > 0))
            for ctx, idx in vals.groupby(context).groups.items():
                rk[idx] = weighted_rank(x[idx], homes[idx].fillna(0))
                li, wi = lx[idx], homes[idx].fillna(0)
                okk = li.notna() & (wi > 0)
                m = np.average(li[okk], weights=wi[okk]) if okk.any() else np.nan
                lr[idx] = li - m
            rk[agg] = 0.5
            lr[agg] = 0.0
            out[f"{vid}__rank"] = rk.fillna(0.5)
            out[f"{vid}__logratio"] = lr.fillna(0.0)
        if miss.any() and not agg[miss].all():
            out[f"{vid}__missing"] = (miss & ~agg).astype(float)
    return pd.DataFrame(out, index=vals.index)


# ---------------------------------------------------------------------------
# 5. Outcome helpers (pure)
# ---------------------------------------------------------------------------

def cap_per_parcel(df: pd.DataFrame, key: str, units: str = "units", date: str = "issue_date", cap: int = 2) -> pd.Series:
    """Units kept after capping each parcel at `cap` ADU units cumulated over the rows given (earliest first).
    Rows with no parcel key are kept as they are."""
    d = df.sort_values(date, kind="mergesort")
    kept = pd.Series(d[units].astype(float).values, index=d.index)
    has = d[key].notna() & d[key].astype(str).str.strip().ne("")
    prior = d[has].groupby(d.loc[has, key].astype(str).str.strip().str.upper())[units].cumsum() - d.loc[has, units]
    kept[prior.index] = np.clip(cap - prior.values, 0, d.loc[prior.index, units].values)
    return kept.reindex(df.index)


# ---------------------------------------------------------------------------
# 6. Build
# ---------------------------------------------------------------------------

def land_areas() -> pd.Series:
    import geopandas as gpd
    import zipfile
    s = {}
    for st in TRACT_STATES:
        p = (RAW / "tiger_wi" / "tl_2024_55_tract.zip") if st == "55" else (ADIR / "tiger" / f"tl_2024_{st}_tract.zip")
        t = gpd.read_file(f"zip://{p}", columns=["GEOID", "ALAND"], ignore_geometry=True)
        s.update({f"tract:{g}": a / 2_589_988.11 for g, a in zip(t.GEOID, t.ALAND)})
    for name, prefix, col in (("census_gazetteer_2024/2024_Gaz_place_national.zip", "place", "GEOID"),
                              ("census_gazetteer_2024/2024_Gaz_cousubs_national.zip", "cousub", "GEOID"),
                              ("acs_api_adu/tiger/2024_Gaz_counties_national.zip", "county", "GEOID")):
        z = zipfile.ZipFile(RAW / name)
        g = pd.read_csv(z.open(z.namelist()[0]), sep="\t", dtype={col: str})
        g.columns = [c.strip() for c in g.columns]
        s.update({f"{prefix}:{a}": b for a, b in zip(g[col], g["ALAND_SQMI"])})
    return pd.Series(s, name="land_sqmi")


def tract_universe() -> pd.DataFrame:
    """2020 tracts whose internal point lies inside each city's 2024 boundary (cartographic boundary file)."""
    import geopandas as gpd
    pl = gpd.read_file(f"zip://{RAW / 'census_cb_2024' / 'cb_2024_us_place_500k.zip'}")
    out = []
    for city, place in CITY_PLACE.items():
        st = place[:2]
        p = (RAW / "tiger_wi" / "tl_2024_55_tract.zip") if st == "55" else (ADIR / "tiger" / f"tl_2024_{st}_tract.zip")
        t = gpd.read_file(f"zip://{p}")
        poly = pl[pl["GEOID"] == place].to_crs(4326)
        pts = gpd.GeoDataFrame(t[["GEOID"]], geometry=gpd.points_from_xy(t.INTPTLON.astype(float), t.INTPTLAT.astype(float)), crs=4326)
        inside = gpd.sjoin(pts, poly[["geometry"]], predicate="within")
        out.append(pd.DataFrame({"city": city, "tract": inside["GEOID"].values}))
    return pd.concat(out, ignore_index=True)


def tracts_for_points(pts: pd.DataFrame, state: str, x: str = "longitude", y: str = "latitude", crs: int = 4326) -> pd.Series:
    import geopandas as gpd
    p = (RAW / "tiger_wi" / "tl_2024_55_tract.zip") if state == "55" else (ADIR / "tiger" / f"tl_2024_{state}_tract.zip")
    t = gpd.read_file(f"zip://{p}", columns=["GEOID"]).to_crs(4326)
    xs, ys = pd.to_numeric(pts[x], errors="coerce"), pd.to_numeric(pts[y], errors="coerce")
    ok = xs.notna() & ys.notna() & (xs != 0) & (ys != 0)
    g = gpd.GeoDataFrame(index=pts.index[ok], geometry=gpd.points_from_xy(xs[ok], ys[ok]), crs=crs).to_crs(4326)
    j = gpd.sjoin(g, t, predicate="within", how="left")
    j = j[~j.index.duplicated()]
    return j["GEOID"].reindex(pts.index)


def city_permits() -> tuple[pd.DataFrame, dict]:
    """Per-permit ADU rows for the five comparison cities with a parcel key and a 2020 tract."""
    import build_other_cities as boc
    permits, _ = boc.load_permits()
    p = permits[~permits["legalization"]].copy()          # units_incl_new_house: counted + with-new-house
    raw = RAW
    sea = pd.read_csv(raw / "seattle_permits_socrata" / "building_permits_adu_subset.csv", dtype=str)
    pdx = pd.read_csv(raw / "portland_res_permits" / "residential_building_permits.csv", dtype=str, encoding="utf-8-sig")
    aus = pd.read_csv(raw / "austin_permits_socrata" / "bp_adu_candidates.csv", dtype=str)
    den = pd.read_csv(raw / "denver_rescon_permits" / "residential_construction_permits.csv", dtype=str)
    msp = pd.read_csv(raw / "minneapolis_ccs_permits" / "ccs_permits_res_adu_text.csv", dtype=str)
    pts = ADIR / "permit_points"
    keys = {
        "seattle": sea.drop_duplicates("permitnum").set_index("permitnum")["originaladdress1"],
        "portland": pdx.drop_duplicates("FOLDERNUMB").set_index("FOLDERNUMB")["PROPGISID1"],
        "austin": aus.drop_duplicates("permit_number").set_index("permit_number")["tcad_id"],
        "denver": den.drop_duplicates("PERMIT_NUM").set_index("PERMIT_NUM")["SCHEDNUM"],
        "minneapolis": msp.drop_duplicates("permitNumber").set_index("permitNumber")["APN"],
    }
    p["parcel_key"] = [keys[c].get(i) for c, i in zip(p["city"], p["permit_id"])]
    p["tract"] = pd.NA
    info = {}
    # Portland: X/Y in the cache are Web Mercator (EPSG:3857)
    m = p["city"].eq("portland")
    xy = pdx.drop_duplicates("FOLDERNUMB").set_index("FOLDERNUMB")[["X", "Y"]]
    q = pd.DataFrame({"x": p.loc[m, "permit_id"].map(xy["X"]), "y": p.loc[m, "permit_id"].map(xy["Y"])}, index=p.index[m])
    p.loc[m, "tract"] = tracts_for_points(q, "41", "x", "y", crs=3857)
    for city, fname, idc, st in (("seattle", "seattle_adu_points.csv", "permitnum", "53"),
                                 ("austin", "austin_adu_points.csv", "permit_number", "48"),
                                 ("denver", "denver_adu_points.csv", "PERMIT_NUM", "08"),
                                 ("minneapolis", "minneapolis_adu_points.csv", "permitNumber", "27")):
        m = p["city"].eq(city)
        pt = pd.read_csv(pts / fname, dtype=str).dropna(subset=["latitude", "longitude"]).drop_duplicates(idc).set_index(idc)
        q = pd.DataFrame({"longitude": p.loc[m, "permit_id"].map(pt["longitude"]),
                          "latitude": p.loc[m, "permit_id"].map(pt["latitude"])}, index=p.index[m])
        p.loc[m, "tract"] = tracts_for_points(q, st)
    for city in CITY_PLACE:
        if city == "madison":
            continue
        g = p[p["city"].eq(city)]
        info[city] = {"permits": int(len(g)), "with_tract": int(g["tract"].notna().sum())}
    return p, info


def madison_permits() -> pd.DataFrame:
    d = pd.read_parquet(PROCESSED / "permits" / "permits_observed.parquet")
    d = d[(d["source_id"] == "madison_permits") & (d["second_home_units"] > 0)
          & d["second_home_component"].ne("sf_to_duplex") & (d["counted"].fillna(True))].copy()
    d["issue_date"] = pd.to_datetime(d["stage_date"], errors="coerce")
    return pd.DataFrame({"city": "madison", "year": d["year"].astype(int), "adu_units": d["second_home_units"].astype(float),
                         "parcel_key": d["parcel_id"], "tract": d["tract_geoid"], "issue_date": d["issue_date"]})


def tract_rows(cells: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    uni = tract_universe()
    p, info = city_permits()
    mad = madison_permits()
    p = p.rename(columns={"adu_units": "units"})
    mad = mad.rename(columns={"adu_units": "units"})
    allp = pd.concat([p[["city", "year", "units", "parcel_key", "tract", "issue_date"]], mad], ignore_index=True)
    rows = []
    for city, coding in TRACT_CODING.items():
        g = allp[allp["city"].eq(city) & allp["year"].isin(list(coding))].copy()
        g["kept"] = cap_per_parcel(g, "parcel_key", "units", "issue_date")
        g["kept"] *= VACANT_LOT_FACTOR if city != "madison" else 1.0
        if city == "minneapolis":
            g["kept"] *= MINNEAPOLIS_FACTOR
        tracts = uni.loc[uni["city"].eq(city), "tract"].tolist()
        inside = g["tract"].isin(tracts)
        info.setdefault(city, {})
        info[city].update({"units_in_years": float(g["units"].sum()), "kept_after_cap_and_factors": float(g["kept"].sum()),
                           "kept_in_city_tracts": float(g.loc[inside, "kept"].sum()),
                           "kept_no_tract_or_outside": float(g.loc[~inside, "kept"].sum()), "n_tracts": len(tracts)})
        cnt = g[inside].groupby(["tract", "year"])["kept"].sum()
        homes = cells["B25024_002"].reindex([f"tract:{t}" for t in tracts]).to_numpy()
        st = CITY_STATE[city]
        for t, h in zip(tracts, homes):
            if not (h and h > 0):
                continue
            for y, (law, local, k) in coding.items():
                rows.append(dict(cluster=st, series=f"{city}_tracts", unit_group=f"{city} tracts", level="tract",
                                 geo=f"tract:{t}", context=f"tract:{city}", year=y, count=float(cnt.get((t, y), 0.0)),
                                 homes=float(h), law=law, local=local, k=k))
    return pd.DataFrame(rows), info


def wa_rows(cells: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    from missing_middleware.comparison import madison_like as ml
    rows = ml.read_xlsx_sheet(RAW / "statewide_states" / "wa" / "ofm_april1_postcensal_permits_1990-present.xlsx",
                              "xl/worksheets/sheet2.xml")
    h = rows[0]
    df = pd.DataFrame([r + [""] * (len(h) - len(r)) for r in rows[1:]], columns=h)
    df["year"] = pd.to_numeric(df["Estimate Year"], errors="coerce")
    df["adu"] = pd.to_numeric(df[ml.OFM_ADU_COL], errors="coerce")
    df = df[df["year"].isin(list(WA_CODING)) & ~df["City Name"].str.contains("Unincorporated", case=False, na=False)]
    by = df.groupby(["City Name", "year"])["adu"].sum(min_count=1).reset_index()
    codes = pd.read_csv(RAW / "statewide_states" / "census_place_codes" / "st53_wa_place2020.txt", sep="|", dtype=str)
    codes = codes[codes["CLASSFP"].str.startswith("C")]
    base = codes["PLACENAME"].str.replace(r" (city|town)$", "", regex=True)
    name2geo = dict(zip(base, codes["STATEFP"] + codes["PLACEFP"]))
    by["geoid"] = by["City Name"].map(name2geo)
    unmatched = sorted(by.loc[by["geoid"].isna(), "City Name"].unique().tolist())
    by = by.dropna(subset=["geoid", "adu"])
    by = by[by["geoid"] != "5363000"]
    out = []
    for r in by.itertuples():
        hm = cells["B25024_002"].get(f"place:{r.geoid}", np.nan)
        if not (hm and hm > 0):
            continue
        law, local, k = WA_CODING[int(r.year)]
        out.append(dict(cluster="WA", series="WA_cities", unit_group="Washington cities", level="place",
                        geo=f"place:{r.geoid}", context="place:WA", year=int(r.year), count=float(r.adu) * VACANT_LOT_FACTOR,
                        homes=float(hm), law=law, local=local, k=k, name=r._1))
    return pd.DataFrame(out), {"wa_unmatched_names": unmatched}


def or_rows(cells: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    from missing_middleware.comparison import madison_like as ml
    from missing_middleware.comparison import statewide_states as ss
    names = ss.SERIES["OR_panel32_exPortland"]["denominator"][1][1]
    geos = ss.places_by_name(RAW / "statewide_states" / "census_place_codes" / "st41_or_place2020.txt", names)
    out, checks = [], []
    for f in sorted((RAW / "statewide_states" / "or").glob("hb4006_*.txt")):
        txt = f.read_text(errors="ignore")
        yr = DLCD_YEARS.get(f.name) or ml.dlcd_year(txt)
        if yr not in OR_CODING:
            continue
        for n, g in zip(names, geos):
            v, chk = ml.dlcd_adu_permitted(txt, n)
            checks.append(chk)
            if np.isnan(v):
                continue
            hm = cells["B25024_002"].get(f"place:{g}", np.nan)
            law, local, k = OR_CODING[yr]
            out.append(dict(cluster="OR", series="OR_cities", unit_group="Oregon cities", level="place", geo=f"place:{g}",
                            context="place:OR", year=yr, count=v * VACANT_LOT_FACTOR, homes=float(hm), law=law, local=local,
                            k=k, name=n))
    return pd.DataFrame(out), {"or_checks": pd.Series(checks).value_counts().to_dict()}


def ca_rows(cells: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    import run_pooled_regression as rp  # noqa: F401  (import path side effects only)
    from missing_middleware.comparison import pooled_revision as R
    panel = pd.read_parquet(PROCESSED / "comparison_ca" / "study" / "study_panel.parquet")
    ca = pd.read_parquet(PROCESSED / "ca_regression" / "ca_dataset.parquet")
    jy = pd.read_csv(REFERENCE / "ca_mf_lot_adu_share_by_jurisdiction.csv")
    xw = pd.read_parquet(PROCESSED / "comparison_ca" / "ca_jurisdiction_crosswalk.parquet")
    rem = R.removed_cap_a2(jy)
    adj = R.adjust_ca_panel(panel, R.to_geoid(rem, xw), R.statewide_factor(rem))
    adj = adj[adj["census_geoid"].isin(ca["census_geoid"]) & adj["year"].between(2018, 2025)].dropna(subset=["adu_main"])
    homes = ca.set_index("census_geoid")["homes"]
    out = []
    for r in adj.itertuples():
        g = r.census_geoid
        geo = f"county:{g[:5]}" if g.endswith("_UNINC") else f"place:{g}"
        out.append(dict(cluster="CA", series="CA_jurisdictions", unit_group="California jurisdictions", level="place",
                        geo=geo, context="place:CA", year=int(r.year), count=float(r.adu_main), homes=float(homes[g]),
                        law=1, local=0, k=int(r.year) - CA_LAW_YEAR1 + 1, name=r.name, ca_geoid=g,
                        geo_note="county values for the unincorporated balance" if g.endswith("_UNINC") else ""))
    return pd.DataFrame(out), {"ca_rows": len(out), "ca_units_2018_2025": float(adj["adu_main"].sum())}


def agg_rows(cells: pd.DataFrame) -> pd.DataFrame:
    annual = pd.read_csv(REFERENCE / "statewide_states_annual.csv")
    out = []
    for sid, (cl, geo, coding) in AGG_CODING.items():
        a = annual[annual["series"].eq(sid)].set_index("year")
        hm = float(a["homes"].dropna().iloc[0]) if a["homes"].notna().any() else float(cells["B25024_002"].get(geo, np.nan))
        for y, (law, local, k) in coding.items():
            if y not in a.index or pd.isna(a.loc[y, "adu_count"]):
                continue
            out.append(dict(cluster=cl, series=sid, unit_group=sid, level="aggregate", geo=geo, context=f"agg:{sid}",
                            year=int(y), count=float(a.loc[y, "adu_count"]) * VACANT_LOT_FACTOR, homes=hm,
                            law=law, local=local, k=k))
    return pd.DataFrame(out)


def wi_areas() -> pd.DataFrame:
    a = pd.read_parquet(PROCESSED / "model_baseline" / "engine_areas.parquet")
    a["geo"] = "cousub:" + a["area_id"].str.replace("muni:", "", regex=False)
    return a


def build(log=print) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cells = read_acs_cells()
    cells = cells.join(land_areas(), how="left")
    info = {"acs_geographies": int(len(cells))}
    t, ti = tract_rows(cells)
    w, wi_ = wa_rows(cells)
    o, oi = or_rows(cells)
    c, ci = ca_rows(cells)
    a = agg_rows(cells)
    info.update({"tract_cities": ti, **wi_, **oi, **ci})
    panel = pd.concat([c, w, o, a, t], ignore_index=True)
    panel["strong"] = np.where(panel["law"].eq(1), panel["cluster"].isin(STRONG).astype(int), 0)
    panel["k"] = pd.to_numeric(panel["k"], errors="coerce")
    panel["row_id"] = np.arange(len(panel))
    # ---- features: per distinct geography, context = state (places) / city (tracts) / itself (aggregates)
    geos = panel.drop_duplicates("geo")[["geo", "context", "level"]].set_index("geo")
    wi = wi_areas()
    wi_geo = pd.DataFrame({"context": "cousub:WI", "level": "wi_area"}, index=wi["geo"])
    allg = pd.concat([geos, wi_geo])
    allg = allg[~allg.index.duplicated()]
    vals = compute_variables(cells.reindex(allg.index))
    homes = cells["B25024_002"].reindex(allg.index)
    feats = transform_features(vals, allg["context"], homes, allg["level"].eq("aggregate"))
    feats.index.name = "geo"
    vals.index.name = "geo"
    panel.to_parquet(OUT / "panel.parquet", index=False)
    feats.loc[geos.index].reset_index().to_parquet(OUT / "features.parquet", index=False)
    vals.reset_index().to_parquet(OUT / "values.parquet", index=False)
    wf = feats.loc[wi_geo.index].reset_index()
    wf.to_parquet(OUT / "wi_features.parquet", index=False)
    # current-model inputs: value, income, rent, renter share per geography (members = the row's own geography)
    mk = pd.DataFrame({"homes": homes, "value": cells["B25077_001"].reindex(allg.index),
                       "income": cells["B19013_001"].reindex(allg.index), "rent": cells["B25064_001"].reindex(allg.index),
                       "renter_share": (cells["B25003_003"] / cells["B25003_001"]).reindex(allg.index)})
    mk.index.name = "geo"
    mk.reset_index().to_parquet(OUT / "market.parquet", index=False)
    (OUT / "build_info.json").write_text(json.dumps(info, indent=2, default=str))
    # ---- reference tables (aggregates only)
    pd.DataFrame([{"variable_id": v[0], "label": v[1], "group": v[2], "kind": v[3],
                   "entered_as": "value" if v[3] in UNIT_FREE else "rank within context; log ratio to context mean",
                   "source": "ACS 2020-2024 5-year, Census Data API"} for v in VARIABLES]) \
        .to_csv(REFERENCE / "adu_predictive_variables.csv", index=False)
    s = panel.groupby(["unit_group", "cluster", "level", "law"]).agg(
        rows=("row_id", "size"), geographies=("geo", "nunique"), years=("year", lambda y: f"{y.min()}-{y.max()}"),
        permits=("count", "sum"), home_years_thousands=("homes", lambda h: h.sum() / 1000)).reset_index()
    s["rate_per_1000_homes_per_year"] = s["permits"] / s["home_years_thousands"]
    s.round(4).to_csv(REFERENCE / "adu_predictive_panel_summary.csv", index=False)
    log(json.dumps(info, indent=1, default=str)[:3000])
    log(f"panel rows {len(panel)}; features {feats.shape[1]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    if a.fetch:
        fetch_tiger()
        fetch_points()
        fetch_acs()
    build()


if __name__ == "__main__":
    main()
