"""TOD all-variables test: can a flexible model, given every relevant public variable, predict where upzoning near
transit added homes, in cities it has not seen?

Implements docs/tod/ALLVARS_PLAN.md (written before any of these variables was joined to any effect). Results are in
docs/tod/ALLVARS_RESULTS.md; departures are in the plan's section 6.

- Units, outcome, folds and pass rule are those of the several-tools rerun of the trait test (TRAITS_PLAN.md section 8,
  latest entries), reused from missing_middleware/tod/traits.py: leave one city out over the six fitted cities,
  acre-weighted mean absolute error in homes permitted per eligible acre per year, Chicago and Madison never fitted.
- Variables (plan section 3): ACS 5-year tract tables for each unit's treatment area, from the survey that ends the year
  before the reform (2005-2009 for reforms of 2010 or earlier, the earliest 5-year release), plus the traits already
  built for the TOD tests. No race or ethnicity table is used (B02*, B03* and the lettered race iterations).
- Models (plan section 4): LASSO, elastic net, random forest, gradient boosting and the honest causal forest of
  traits.py, all tuned inside each training fold.

Pure arithmetic only (tables in, numbers out) so it can be tested without network or geography.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from missing_middleware.tod import traits as T

FIRST_END_YEAR = 2009        # the first ACS 5-year release covers 2005-2009
SQM_PER_SQMI = 2_589_988.110336

# CPI-U, U.S. city average, annual average (BLS CUUR0000SA0)
CPI_U = {2009: 214.537, 2010: 218.056, 2011: 224.939, 2012: 229.594, 2013: 232.957, 2014: 236.736, 2015: 237.017,
         2016: 240.007, 2017: 245.120, 2018: 251.107, 2019: 255.657, 2020: 258.811, 2021: 270.970, 2022: 292.655,
         2023: 304.702, 2024: 313.689}


def survey_end_year(effective_year: int) -> int:
    """Last year of the 5-year ACS that ends before the reform year; the first release (2005-2009) for earlier reforms."""
    return max(FIRST_END_YEAR, int(effective_year) - 1)


def survey_label(end_year: int) -> str:
    return f"{end_year - 4}-{end_year}"


def tract_vintage(end_year: int) -> str:
    """Tract boundaries the ACS release uses: 2000 tracts through 2005-2009, 2010 tracts through 2015-2019, then 2020."""
    if end_year <= 2009:
        return "2000"
    return "2010" if end_year <= 2019 else "2020"


def to_2024_dollars(value, end_year: int):
    """ACS dollar amounts are in dollars of the survey's last year; CPI-U to 2024 dollars."""
    return value * CPI_U[2024] / CPI_U[end_year]


# --------------------------------------------------------------------------- variables
# A cell is "TABLE_line". A negative line counts from the end of the table (B25034's newest categories change between
# releases; its oldest categories are the last lines in every release). "ALAND_SQMI" is the tract's land area.

def _cells(table: str, lines) -> dict:
    return {f"{table}_{ln}": 1.0 for ln in lines}


def _plus(*ds: dict) -> dict:
    out: dict = {}
    for d in ds:
        for k, v in d.items():
            out[k] = out.get(k, 0.0) + v
    return out


def _minus(a: dict, b: dict) -> dict:
    return _plus(a, {k: -v for k, v in b.items()})


# B23001 (sex by age by employment status): per sex, ten age groups 16-64 of 7 lines (age, in labour force, armed
# forces, civilian, employed, unemployed, not in labour force) then three groups 65+ of 5 lines (age, in labour force,
# employed, unemployed, not in labour force). Male groups start at line 3, female at line 89.
def _b23001(kind: str) -> list[int]:
    out = []
    for start in (3, 89):
        for k in range(10):
            g = start + 7 * k
            out.append({"in_lf": g + 1, "civ_lf": g + 3, "unemp": g + 5}[kind])
        for k in range(3):
            g = start + 70 + 5 * k
            out.append({"in_lf": g + 1, "civ_lf": g + 1, "unemp": g + 3}[kind])
    return out


B01001_MALE = {"u18": range(3, 7), "18_34": range(7, 13), "35_64": range(13, 20), "65p": range(20, 26)}
B01001_FEMALE = {k: range(r.start + 24, r.stop + 24) for k, r in B01001_MALE.items()}
YEAR_BUILT_OLD = {"b1940_59": (-2, -3), "b1960_79": (-4, -5), "b1980_99": (-6, -7), "pre1940": (-1,)}


def V(vid, label, group, unit, num, den=None, kind="ratio", dollars=False, log=False, years_since=False, cells_text=""):
    return {"id": vid, "label": label, "group": group, "unit": unit, "num": num, "den": den, "kind": kind,
            "dollars": dollars, "log": log, "years_since": years_since, "cells_text": cells_text}


_b25024 = lambda *l: _cells("B25024", l)  # noqa: E731
_yb_old = _cells("B25034", [-1, -2, -3, -4, -5, -6, -7])

VARIABLES: list[dict] = [
    # ---- housing stock
    V("h01_share_1unit_detached", "Homes in 1-unit detached buildings", "housing stock", "share of homes", _b25024(2), _b25024(1), cells_text="B25024 line 2 / line 1"),
    V("h02_share_1unit_attached", "Homes in 1-unit attached buildings", "housing stock", "share of homes", _b25024(3), _b25024(1), cells_text="B25024 line 3 / line 1"),
    V("h03_share_2to4_units", "Homes in buildings of 2 to 4 units", "housing stock", "share of homes", _b25024(4, 5), _b25024(1), cells_text="B25024 lines 4-5 / line 1"),
    V("h04_share_5to19_units", "Homes in buildings of 5 to 19 units", "housing stock", "share of homes", _b25024(6, 7), _b25024(1), cells_text="B25024 lines 6-7 / line 1"),
    V("h05_share_20to49_units", "Homes in buildings of 20 to 49 units", "housing stock", "share of homes", _b25024(8), _b25024(1), cells_text="B25024 line 8 / line 1"),
    V("h06_share_50plus_units", "Homes in buildings of 50 or more units", "housing stock", "share of homes", _b25024(9), _b25024(1), cells_text="B25024 line 9 / line 1"),
    V("h07_share_mobile_other", "Mobile homes, boats, RVs and vans", "housing stock", "share of homes", _b25024(10, 11), _b25024(1), cells_text="B25024 lines 10-11 / line 1"),
    V("h08_share_built_2000_on", "Homes built in 2000 or later", "housing stock", "share of homes", _minus(_cells("B25034", [1]), _yb_old), _cells("B25034", [1]),
      cells_text="(B25034 line 1 - the last 7 lines, i.e. all built 2000 or later) / line 1"),
    V("h09_share_built_1980_99", "Homes built 1980 to 1999", "housing stock", "share of homes", _cells("B25034", YEAR_BUILT_OLD["b1980_99"]), _cells("B25034", [1]), cells_text="B25034 7th- and 6th-last lines / line 1"),
    V("h10_share_built_1960_79", "Homes built 1960 to 1979", "housing stock", "share of homes", _cells("B25034", YEAR_BUILT_OLD["b1960_79"]), _cells("B25034", [1]), cells_text="B25034 5th- and 4th-last lines / line 1"),
    V("h11_share_built_1940_59", "Homes built 1940 to 1959", "housing stock", "share of homes", _cells("B25034", YEAR_BUILT_OLD["b1940_59"]), _cells("B25034", [1]), cells_text="B25034 3rd- and 2nd-last lines / line 1"),
    V("h12_share_built_pre1940", "Homes built 1939 or earlier", "housing stock", "share of homes", _cells("B25034", [-1]), _cells("B25034", [1]), cells_text="B25034 last line / line 1"),
    V("h13_median_building_age", "Median age of buildings (survey end year - median year built)", "housing stock", "years", _cells("B25035", [1]), kind="median", years_since=True, cells_text="end year - B25035 line 1"),
    V("h14_vacancy_rate", "Vacant homes", "housing stock", "share of homes", _cells("B25002", [3]), _cells("B25002", [1]), cells_text="B25002 line 3 / line 1"),
    V("h15_owner_share", "Owner-occupied homes", "housing stock", "share of occupied homes", _cells("B25003", [2]), _cells("B25003", [1]), cells_text="B25003 line 2 / line 1"),
    V("h16_median_rooms", "Median rooms per home", "housing stock", "rooms", _cells("B25018", [1]), kind="median", cells_text="B25018 line 1"),
    V("h17_share_1to3_rooms", "Homes with 1 to 3 rooms", "housing stock", "share of homes", _cells("B25017", [2, 3, 4]), _cells("B25017", [1]), cells_text="B25017 lines 2-4 / line 1"),
    V("h18_share_0to1_bedrooms", "Homes with no bedroom or 1 bedroom", "housing stock", "share of homes", _cells("B25041", [2, 3]), _cells("B25041", [1]), cells_text="B25041 lines 2-3 / line 1"),
    V("h19_share_crowded", "Occupied homes with more than 1 person per room", "housing stock", "share of occupied homes", _cells("B25014", [5, 6, 7, 11, 12, 13]), _cells("B25014", [1]),
      cells_text="B25014 lines 5-7 and 11-13 / line 1"),
    V("h20_years_since_moved_in", "Median years since the householder moved in", "housing stock", "years", _cells("B25039", [1]), kind="median", years_since=True, cells_text="end year - B25039 line 1"),
    V("h21_share_moved_last_year", "People who moved in the past year", "housing stock", "share of people aged 1+", _minus(_cells("B07001", [1]), _cells("B07001", [17])), _cells("B07001", [1]),
      cells_text="(B07001 line 1 - line 17) / line 1"),
    # ---- housing costs
    V("c01_median_rent", "Median gross rent", "housing costs", "2024 dollars per month", _cells("B25064", [1]), kind="median", dollars=True, log=True, cells_text="B25064 line 1"),
    V("c02_rent_lower_quartile", "Lower-quartile gross rent", "housing costs", "2024 dollars per month", _cells("B25057", [1]), kind="median", dollars=True, log=True, cells_text="B25057 line 1"),
    V("c03_rent_upper_quartile", "Upper-quartile gross rent", "housing costs", "2024 dollars per month", _cells("B25059", [1]), kind="median", dollars=True, log=True, cells_text="B25059 line 1"),
    V("c04_median_value", "Median home value (owner-occupied)", "housing costs", "2024 dollars", _cells("B25077", [1]), kind="median", dollars=True, log=True, cells_text="B25077 line 1"),
    V("c05_value_lower_quartile", "Lower-quartile home value", "housing costs", "2024 dollars", _cells("B25076", [1]), kind="median", dollars=True, log=True, cells_text="B25076 line 1"),
    V("c06_value_upper_quartile", "Upper-quartile home value", "housing costs", "2024 dollars", _cells("B25078", [1]), kind="median", dollars=True, log=True, cells_text="B25078 line 1"),
    V("c07_rent_burden_30", "Renters paying 30% or more of income on rent", "housing costs", "share of renter households (rent burden computed)", _cells("B25070", [7, 8, 9, 10]),
      _minus(_cells("B25070", [1]), _cells("B25070", [11])), cells_text="B25070 lines 7-10 / (line 1 - line 11)"),
    V("c08_rent_burden_50", "Renters paying 50% or more of income on rent", "housing costs", "share of renter households (rent burden computed)", _cells("B25070", [10]),
      _minus(_cells("B25070", [1]), _cells("B25070", [11])), cells_text="B25070 line 10 / (line 1 - line 11)"),
    V("c09_median_rent_pct_income", "Median gross rent as a share of household income", "housing costs", "percent", _cells("B25071", [1]), kind="median", cells_text="B25071 line 1"),
    V("c10_share_with_mortgage", "Owner homes with a mortgage", "housing costs", "share of owner-occupied homes", _cells("B25081", [2]), _cells("B25081", [1]), cells_text="B25081 line 2 / line 1"),
    V("c11_owner_costs_mortgaged", "Median monthly owner costs, homes with a mortgage", "housing costs", "2024 dollars per month", _cells("B25088", [2]), kind="median", dollars=True, log=True, cells_text="B25088 line 2"),
    V("c12_owner_costs_pct_income", "Median owner costs as a share of household income", "housing costs", "percent", _cells("B25092", [1]), kind="median", cells_text="B25092 line 1"),
    V("c13_median_housing_costs", "Median monthly housing costs (all occupied homes)", "housing costs", "2024 dollars per month", _cells("B25105", [1]), kind="median", dollars=True, log=True, cells_text="B25105 line 1"),
    V("c14_value_to_annual_rent", "Median home value / (12 x median gross rent)", "housing costs", "years of rent", _cells("B25077", [1]), _plus({"B25064_1": 12.0}), kind="median_ratio",
      cells_text="B25077 line 1 / (12 x B25064 line 1), per tract"),
    # ---- people and households
    V("p01_household_size", "Average household size", "people and households", "people per household", _cells("B25010", [1]), kind="median", cells_text="B25010 line 1"),
    V("p02_median_age", "Median age", "people and households", "years", _cells("B01002", [1]), kind="median", cells_text="B01002 line 1"),
    V("p03_share_under18", "People under 18", "people and households", "share of people", _plus(_cells("B01001", B01001_MALE["u18"]), _cells("B01001", B01001_FEMALE["u18"])), _cells("B01001", [1]),
      cells_text="B01001 lines 3-6 and 27-30 / line 1"),
    V("p04_share_18to34", "People aged 18 to 34", "people and households", "share of people", _plus(_cells("B01001", B01001_MALE["18_34"]), _cells("B01001", B01001_FEMALE["18_34"])), _cells("B01001", [1]),
      cells_text="B01001 lines 7-12 and 31-36 / line 1"),
    V("p05_share_35to64", "People aged 35 to 64", "people and households", "share of people", _plus(_cells("B01001", B01001_MALE["35_64"]), _cells("B01001", B01001_FEMALE["35_64"])), _cells("B01001", [1]),
      cells_text="B01001 lines 13-19 and 37-43 / line 1"),
    V("p06_share_65plus", "People aged 65 and over", "people and households", "share of people", _plus(_cells("B01001", B01001_MALE["65p"]), _cells("B01001", B01001_FEMALE["65p"])), _cells("B01001", [1]),
      cells_text="B01001 lines 20-25 and 44-49 / line 1"),
    V("p07_share_hh_children", "Households with children under 18", "people and households", "share of households", _cells("B11005", [2]), _cells("B11005", [1]), cells_text="B11005 line 2 / line 1"),
    V("p08_share_living_alone", "Householders living alone", "people and households", "share of households", _cells("B11001", [8]), _cells("B11001", [1]), cells_text="B11001 line 8 / line 1"),
    V("p09_share_bachelors_plus", "Adults 25+ with a bachelor's degree or more", "people and households", "share of adults 25+", _cells("B15002", [15, 16, 17, 18, 32, 33, 34, 35]), _cells("B15002", [1]),
      cells_text="B15002 lines 15-18 and 32-35 / line 1"),
    V("p10_share_no_hs_diploma", "Adults 25+ without a high-school diploma", "people and households", "share of adults 25+", _cells("B15002", list(range(3, 11)) + list(range(20, 28))), _cells("B15002", [1]),
      cells_text="B15002 lines 3-10 and 20-27 / line 1"),
    V("p11_median_income", "Median household income", "people and households", "2024 dollars per year", _cells("B19013", [1]), kind="median", dollars=True, log=True, cells_text="B19013 line 1"),
    V("p12_per_capita_income", "Income per person", "people and households", "2024 dollars per year", _cells("B19301", [1]), kind="median", dollars=True, log=True, cells_text="B19301 line 1"),
    V("p13_share_income_under25k", "Households with income under $25,000 (dollars of the survey years)", "people and households", "share of households", _cells("B19001", range(2, 6)), _cells("B19001", [1]),
      cells_text="B19001 lines 2-5 / line 1"),
    V("p14_share_income_25to50k", "Households with income $25,000 to $49,999 (dollars of the survey years)", "people and households", "share of households", _cells("B19001", range(6, 11)), _cells("B19001", [1]),
      cells_text="B19001 lines 6-10 / line 1"),
    V("p15_share_income_50to100k", "Households with income $50,000 to $99,999 (dollars of the survey years)", "people and households", "share of households", _cells("B19001", range(11, 14)), _cells("B19001", [1]),
      cells_text="B19001 lines 11-13 / line 1"),
    V("p16_share_income_100k_plus", "Households with income $100,000 or more (dollars of the survey years)", "people and households", "share of households", _cells("B19001", range(14, 18)), _cells("B19001", [1]),
      cells_text="B19001 lines 14-17 / line 1"),
    V("p17_gini", "Income inequality (Gini index)", "people and households", "index 0 to 1", _cells("B19083", [1]), kind="median", cells_text="B19083 line 1"),
    V("p18_poverty_rate", "People below the poverty line", "people and households", "share of people (poverty status known)", _cells("B17001", [2]), _cells("B17001", [1]), cells_text="B17001 line 2 / line 1"),
    V("p19_share_snap", "Households receiving food stamps / SNAP", "people and households", "share of households", _cells("B19058", [2]), _cells("B19058", [1]), cells_text="B19058 line 2 / line 1"),
    V("p20_labour_force_participation", "People 16+ in the labour force", "people and households", "share of people 16+", _cells("B23001", _b23001("in_lf")), _cells("B23001", [1]),
      cells_text="B23001 'In labor force' lines (4, 11, ..., 67, 74, 79, 84 and female equivalents) / line 1"),
    V("p21_unemployment_rate", "Unemployed, of the civilian labour force", "people and households", "share of civilian labour force", _cells("B23001", _b23001("unemp")), _cells("B23001", _b23001("civ_lf")),
      cells_text="B23001 'Unemployed' lines / civilian labour force lines"),
    V("p22_median_earnings", "Median earnings of people with earnings", "people and households", "2024 dollars per year", _cells("B20002", [1]), kind="median", dollars=True, log=True, cells_text="B20002 line 1"),
    # ---- mobility
    V("m01_share_no_vehicle", "Households with no vehicle", "mobility", "share of households", _cells("B25044", [3, 10]), _cells("B25044", [1]), cells_text="B25044 lines 3 and 10 / line 1"),
    V("m02_share_2plus_vehicles", "Households with 2 or more vehicles", "mobility", "share of households", _cells("B25044", [5, 6, 7, 8, 12, 13, 14, 15]), _cells("B25044", [1]),
      cells_text="B25044 lines 5-8 and 12-15 / line 1"),
    V("m03_vehicles_per_household", "Vehicles per household", "mobility", "vehicles per household", _cells("B25046", [1]), _cells("B25044", [1]), cells_text="B25046 line 1 / B25044 line 1"),
    V("m04_commute_drove_alone", "Workers who drive alone to work", "mobility", "share of workers", _cells("B08301", [3]), _cells("B08301", [1]), cells_text="B08301 line 3 / line 1"),
    V("m05_commute_carpool", "Workers who carpool", "mobility", "share of workers", _cells("B08301", [4]), _cells("B08301", [1]), cells_text="B08301 line 4 / line 1"),
    V("m06_commute_transit", "Workers who take public transit (not taxi)", "mobility", "share of workers", _cells("B08301", [10]), _cells("B08301", [1]), cells_text="B08301 line 10 / line 1"),
    V("m07_commute_walk", "Workers who walk", "mobility", "share of workers", _cells("B08301", [19]), _cells("B08301", [1]), cells_text="B08301 line 19 / line 1"),
    V("m08_commute_bicycle", "Workers who cycle", "mobility", "share of workers", _cells("B08301", [18]), _cells("B08301", [1]), cells_text="B08301 line 18 / line 1"),
    V("m09_work_from_home", "Workers who work at home", "mobility", "share of workers", _cells("B08301", [21]), _cells("B08301", [1]), cells_text="B08301 line 21 / line 1"),
    V("m10_mean_commute_minutes", "Mean travel time to work", "mobility", "minutes", _cells("B08013", [1]), _minus(_cells("B08301", [1]), _cells("B08301", [21])),
      cells_text="B08013 line 1 / (B08301 line 1 - line 21)"),
    V("m11_share_commute_under15", "Commutes under 15 minutes", "mobility", "share of workers not at home", _cells("B08303", [2, 3, 4]), _cells("B08303", [1]), cells_text="B08303 lines 2-4 / line 1"),
    V("m12_share_commute_15to29", "Commutes of 15 to 29 minutes", "mobility", "share of workers not at home", _cells("B08303", [5, 6, 7]), _cells("B08303", [1]), cells_text="B08303 lines 5-7 / line 1"),
    V("m13_share_commute_30to44", "Commutes of 30 to 44 minutes", "mobility", "share of workers not at home", _cells("B08303", [8, 9, 10]), _cells("B08303", [1]), cells_text="B08303 lines 8-10 / line 1"),
    V("m14_share_commute_45plus", "Commutes of 45 minutes or more", "mobility", "share of workers not at home", _cells("B08303", [11, 12, 13]), _cells("B08303", [1]), cells_text="B08303 lines 11-13 / line 1"),
    V("m15_leave_before_7am", "Workers leaving home before 7 a.m.", "mobility", "share of workers not at home", _cells("B08302", [2, 3, 4, 5, 6]), _cells("B08302", [1]), cells_text="B08302 lines 2-6 / line 1"),
    V("m16_leave_7_to_9am", "Workers leaving home 7:00 to 8:59 a.m.", "mobility", "share of workers not at home", _cells("B08302", [7, 8, 9, 10]), _cells("B08302", [1]), cells_text="B08302 lines 7-10 / line 1"),
    V("m17_leave_9am_or_later", "Workers leaving home at 9 a.m. or later", "mobility", "share of workers not at home", _cells("B08302", [11, 12, 13, 14, 15]), _cells("B08302", [1]),
      cells_text="B08302 lines 11-15 / line 1"),
    V("m18_work_in_home_place", "Workers working in their place (city) of residence", "mobility", "share of workers", _cells("B08008", [3]), _cells("B08008", [1]), cells_text="B08008 line 3 / line 1"),
    # ---- place
    V("l01_homes_per_sqmi", "Homes per square mile of tract land", "place", "homes per square mile", _cells("B25001", [1]), {"ALAND_SQMI": 1.0}, log=True,
      cells_text="B25001 line 1 / tract land area (TIGER)"),
    V("l02_people_per_sqmi", "People per square mile of tract land", "place", "people per square mile", _cells("B01003", [1]), {"ALAND_SQMI": 1.0}, log=True,
      cells_text="B01003 line 1 / tract land area (TIGER)"),
    V("l03_tract_land_sqmi", "Land area of the tracts the treatment lots sit in", "place", "square miles", {"ALAND_SQMI": 1.0}, kind="median", log=True,
      cells_text="tract land area (TIGER), acre-weighted mean"),
]
ACS_IDS = [v["id"] for v in VARIABLES]

# Traits already built for the TOD tests (plan section 3, last bullet), as entered in those tests.
BUILT = {
    "t02_lot_size": ("tod_trait_values.csv", "value"),
    "t03_existing_density": ("tod_trait_values.csv", "log(value + 1)"),
    "t07_added_far": ("tod_trait_values.csv", "value"),
    "t08_rate_before": ("tod_trait_values.csv", "value"),
    "t09_vacant_parking_industrial_share": ("tod_trait_values.csv", "value"),
    "t10_km_to_downtown": ("tod_trait_values.csv", "value"),
    "t11_transit_jobs_access": ("tod_trait_values.csv", "value"),
    "t12_parking_cut": ("tod_trait_values.csv", "value"),
    "n01_island_acres": ("tod_coverage_traits.csv", "log(value + 1)"),
    "n02_largest_site_acres": ("tod_coverage_traits.csv", "log(value + 1)"),
    "n03_elongation": ("tod_coverage_traits.csv", "log(value + 1)"),
    "n04_corridor_share": ("tod_coverage_traits.csv", "value"),
    "n05_binding_ratio": ("tod_coverage_traits.csv", "value"),
}
ALL_IDS = ACS_IDS + list(BUILT)

# No race or ethnicity variable (plan section 3). Tables B02*/B03* and lettered race iterations (B19013A..I etc.)
RACE_TABLE = re.compile(r"^(B0[23]\d{3}|[BC]\d{5}[A-I])$")


def tables_used() -> list[str]:
    out = set()
    for v in VARIABLES:
        for part in (v["num"], v["den"] or {}):
            for k in part:
                if k != "ALAND_SQMI":
                    out.add(k.rsplit("_", 1)[0])
    return sorted(out)


def resolve_line(line: int, n_cells: int) -> int:
    """Line number in a table of n_cells lines; negative lines count from the end (-1 = last line)."""
    return line if line > 0 else n_cells + 1 + line


def resolve(combo: dict, n_cells: dict) -> dict:
    """{'B25034_-1': 1} -> {'B25034_10': 1} given the table lengths of a release."""
    out: dict = {}
    for k, c in combo.items():
        if k == "ALAND_SQMI":
            out[k] = out.get(k, 0.0) + c
            continue
        t, ln = k.rsplit("_", 1)
        key = f"{t}_{resolve_line(int(ln), n_cells[t])}"
        out[key] = out.get(key, 0.0) + c
    return out


def combo_value(cells: pd.DataFrame, combo: dict) -> pd.Series:
    """Linear combination of cell columns; NaN where any cell is missing."""
    s = pd.Series(0.0, index=cells.index)
    for k, c in combo.items():
        s = s + c * pd.to_numeric(cells[k], errors="coerce") if k in cells else s + np.nan
    return s


def tract_parts(cells: pd.DataFrame, n_cells: dict, end_year: int) -> pd.DataFrame:
    """Per tract and variable: numerator and denominator (ratio variables) or the tract value (medians).

    Columns '<id>__num' and '<id>__den'. For a 'median' kind the value sits in __num and __den is 1 where present. ACS
    jam values (negative medians) are treated as missing. Dollars are converted to 2024 dollars."""
    out: dict = {}
    for v in VARIABLES:
        num = combo_value(cells, resolve(v["num"], n_cells))
        if v["kind"] == "ratio":
            den = combo_value(cells, resolve(v["den"], n_cells))
            ok = num.notna() & den.notna() & (den > 0) & (num >= 0)
            out[v["id"] + "__num"], out[v["id"] + "__den"] = num.where(ok), den.where(ok)
            continue
        if v["kind"] == "median_ratio":
            den = combo_value(cells, resolve(v["den"], n_cells))
            val = (num.where(num > 0) / den.where(den > 0))
        else:
            val = num.where(num > 0)
        if v["dollars"]:
            val = to_2024_dollars(val, end_year)
        if v["years_since"]:
            val = (end_year - val).where(lambda x: x >= 0)
        out[v["id"] + "__num"], out[v["id"] + "__den"] = val, val.notna().astype(float).where(val.notna())
    return pd.DataFrame(out, index=cells.index)


def unit_values(lots: pd.DataFrame, parts: pd.DataFrame) -> pd.Series:
    """One unit's values from its treatment lots (columns 'tract' and 'acres') and the tract parts.

    Ratio variables: acre-weighted sum of tract numerators / acre-weighted sum of tract denominators (the rule of the
    net-effect car traits). Median-type variables: acre-weighted mean of the tract values."""
    j = lots[["tract", "acres"]].merge(parts, left_on="tract", right_index=True, how="left")
    w = j["acres"].astype(float)
    res = {}
    for v in VARIABLES:
        n, d = j[v["id"] + "__num"], j[v["id"] + "__den"]
        ok = n.notna() & d.notna() & (w > 0)
        if not ok.any():
            res[v["id"]] = np.nan
        elif v["kind"] == "ratio":
            res[v["id"]] = float((n[ok] * w[ok]).sum() / (d[ok] * w[ok]).sum()) if (d[ok] * w[ok]).sum() > 0 else np.nan
        else:
            res[v["id"]] = float((n[ok] * w[ok]).sum() / w[ok].sum())
    return pd.Series(res)


def entered(values: pd.DataFrame) -> pd.DataFrame:
    """Variables as entered in the models: natural logs for dollar amounts and densities (log(value) for positive
    values); built traits as entered in their own tests (log(value + 1) where stated)."""
    out = pd.DataFrame(index=values.index)
    for v in VARIABLES:
        x = pd.to_numeric(values[v["id"]], errors="coerce").astype(float)
        out[v["id"]] = np.log(x.where(x > 0)) if v["log"] else x
    for t, (_, how) in BUILT.items():
        x = pd.to_numeric(values[t], errors="coerce").astype(float)
        out[t] = np.log(x + 1.0) if how == "log(value + 1)" else x
    return out


# --------------------------------------------------------------------------- models

MODELS = {
    "baseline": "0. plain average (acre-weighted mean of the training units)",
    "lasso": "1. LASSO (penalty by leave-one-city-out CV inside each training fold)",
    "elastic_net": "2. elastic net (penalty and L1 mix by leave-one-city-out CV inside each training fold)",
    "forest": "3. random forest (500 trees, at least 5 units per leaf)",
    "boosting": "4. gradient boosting (depth-2 trees, early stopping inside each training fold)",
    "causal_forest": "5. honest causal forest (treated and comparison land as treated and control observations)",
}
ENET_L1 = (0.1, 0.3, 0.5, 0.7, 0.9, 0.95, 0.99)
N_ALPHAS = 50


def city_splits(cities: np.ndarray) -> list[tuple[np.ndarray, np.ndarray]]:
    """Leave-one-city-out splits among the training rows (for tuning inside a training fold)."""
    return [(np.where(cities != c)[0], np.where(cities == c)[0]) for c in pd.unique(cities)]


def predict(model: str, train: pd.DataFrame, test: pd.DataFrame, cols: list[str], seed: int = T.TOOL_SEED) -> tuple[np.ndarray, dict]:
    """Predictions (homes per eligible acre per year) of one model fitted on the training fold only.

    Missing values are filled with the training fold's acre-weighted means (traits.weighted_fill); linear models
    standardize on the training fold. train/test need columns effect, weight, city, d_treat, d_comp, comparison_acres."""
    y, w = train["effect"].values.astype(float), train["weight"].values.astype(float)
    if model == "baseline":
        return T.fit_predict(train, test, []), {}
    Xtr, Xte, keep = T.weighted_fill(train, test, cols)
    # a variable with no spread in the training fold carries nothing
    sd = Xtr.std(axis=0)
    Xtr, Xte, keep = Xtr[:, sd > 0], Xte[:, sd > 0], [k for k, s in zip(keep, sd) if s > 0]
    if model in ("lasso", "elastic_net"):
        from sklearn.linear_model import ElasticNetCV, LassoCV
        Ztr, Zte = T.standardize(Xtr, Xte)
        splits = city_splits(train["city"].values)
        if model == "lasso":
            m = LassoCV(alphas=N_ALPHAS, cv=splits, max_iter=200000)
        else:
            m = ElasticNetCV(l1_ratio=list(ENET_L1), alphas=N_ALPHAS, cv=splits, max_iter=200000)
        m.fit(Ztr, y, sample_weight=w)
        info = {"alpha": float(m.alpha_), "kept": int(np.sum(np.abs(m.coef_) > 1e-10))}
        if model == "elastic_net":
            info["l1_ratio"] = float(m.l1_ratio_)
        return m.predict(Zte), {**info, "_coef": dict(zip(keep, m.coef_))}
    if model == "forest":
        from sklearn.ensemble import RandomForestRegressor
        m = RandomForestRegressor(n_estimators=500, min_samples_leaf=5, random_state=seed, n_jobs=-1)
        m.fit(Xtr, y, sample_weight=w)
        return m.predict(Xte), {"_importance": dict(zip(keep, m.feature_importances_))}
    if model == "boosting":
        from sklearn.ensemble import GradientBoostingRegressor
        m = GradientBoostingRegressor(max_depth=2, learning_rate=0.05, n_estimators=1000, validation_fraction=0.2,
                                      n_iter_no_change=20, random_state=seed)
        m.fit(Xtr, y, sample_weight=w)
        return m.predict(Xte), {"trees": int(m.n_estimators_), "_importance": dict(zip(keep, m.feature_importances_))}
    if model == "causal_forest":
        p = T.causal_forest_predict(Xtr, train["d_treat"].values.astype(float), w, train["d_comp"].values.astype(float),
                                    train["comparison_acres"].values.astype(float), Xte, seed=seed)
        return p, {}
    raise ValueError(model)


def heldout(d: pd.DataFrame, model: str, cols: list[str], fit_cities=T.WIDE_FIT_CITIES,
            order=T.WIDE_CITY_ORDER, seed: int = T.TOOL_SEED) -> pd.DataFrame:
    """Leave-one-city-out over the fit cities; every other city predicted from all fit cities, never fitted."""
    rows = []
    for c in order:
        test = d[d["city"] == c]
        train = d[d["city"].isin([f for f in fit_cities if f != c])]
        if test.empty or train.empty:
            continue
        pm, info = predict(model, train, test, cols, seed=seed)
        pb = T.fit_predict(train, test, [])
        ob, ww = test["effect"].values.astype(float), test["weight"].values.astype(float)
        rows.append({"city": c, "role": T.role_of(c) if c in T.WIDE_CITY_ORDER else ("fold" if c in fit_cities else "context"),
                     "units": len(test), "treatment_acres": float(ww.sum()), "fit_units": len(train),
                     "error_baseline": T.weighted_mae(pb, ob, ww), "error_model": T.weighted_mae(pm, ob, ww),
                     "measured_mean": float(np.sum(ob * ww) / ww.sum()), "predicted_mean_baseline": float(np.sum(pb * ww) / ww.sum()),
                     "predicted_mean_model": float(np.sum(pm * ww) / ww.sum()),
                     "note": "; ".join(f"{k} {v:.4g}" for k, v in info.items() if not k.startswith("_"))})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- robustness (plan section 6, 2026-10-27)
# A model that passes counts only if it also passes (a) in at least 4 of 5 other seeds, (b) with each fitted city's
# largest unit by acres left out, one at a time, and (c) with equal unit weights. Otherwise it is "not robust".

ROBUST_SEEDS = (20261028, 20261029, 20261030, 20261031, 20261032)
ROBUST_SEEDS_NEEDED = 4


def largest_units(d: pd.DataFrame, fit_cities=T.WIDE_FIT_CITIES) -> list:
    """Index of each fitted city's largest unit by eligible treatment acres."""
    f = d[d["city"].isin(fit_cities)]
    return [g["weight"].idxmax() for _, g in f.groupby("city", sort=False)]


def robustness(d: pd.DataFrame, model: str, cols: list[str], judge=T.judge_tools) -> dict:
    """The three checks. Returns per-check results and the overall label."""
    seeds = [judge(heldout(d, model, cols, seed=s))["verdict"] == "pass" for s in ROBUST_SEEDS]
    drop = {}
    for ix in largest_units(d):
        drop[str(d.loc[ix, "city"])] = judge(heldout(d.drop(index=ix), model, cols))["verdict"] == "pass"
    eq = judge(heldout(d.assign(weight=1.0), model, cols))["verdict"] == "pass"
    ok = sum(seeds) >= ROBUST_SEEDS_NEEDED and all(drop.values()) and eq
    return {"seeds_passed": int(sum(seeds)), "seeds": len(seeds), "largest_unit_out_passed": int(sum(drop.values())),
            "largest_unit_out": len(drop), "largest_unit_out_detail": "; ".join(f"{c}: {'pass' if v else 'fail'}" for c, v in drop.items()),
            "equal_weights_passed": bool(eq), "label": "robust pass" if ok else "not robust"}
