"""Place-level versions of TOD's ACS traits (reference/tod_allvars_variable_map.csv) for every place and county
subdivision, one row per acs_geoid and release end year (2013-2023), from data/raw/parking_acs_tod_traits.
Method 3 trait rules (CAUSAL_FRAMEWORK_PLAN.md, "Method 3"): built-year traits limited to pre-2010 categories;
median-year-built / building-age, post-2010 bands, tract-only and TOD-only traits left out.

    uv run python scripts/build_parking_acs_tod_traits.py
Output: data/raw/parking_acs_tod_traits/traits_by_release.csv.gz (not committed; rebuilt from the raw tables)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import RAW  # noqa: E402

IN = RAW / "parking_acs_tod_traits"
YEARS = range(2013, 2024)


def L(t, *lines):
    return [f"{t}_{i:03d}E" for i in lines]


def rng(a, b):
    return list(range(a, b + 1))


# male / female age-group starts in B23001 (7 lines per group under 65, 5 lines for 65+)
M_U65 = [3, 10, 17, 24, 31, 38, 45, 52, 59, 66]
M_65 = [73, 78, 83]
F_U65 = [g + 86 for g in M_U65]
F_65 = [g + 86 for g in M_65]
U65 = M_U65 + F_U65
O65 = M_65 + F_65
SHARE = {  # name: (numerator cells, denominator cells)
    "h01_share_1unit_detached": (L("B25024", 2), L("B25024", 1)),
    "h02_share_1unit_attached": (L("B25024", 3), L("B25024", 1)),
    "h03_share_2to4_units": (L("B25024", 4, 5), L("B25024", 1)),
    "h04_share_5to19_units": (L("B25024", 6, 7), L("B25024", 1)),
    "h05_share_20to49_units": (L("B25024", 8), L("B25024", 1)),
    "h06_share_50plus_units": (L("B25024", 9), L("B25024", 1)),
    "h07_share_mobile_other": (L("B25024", 10, 11), L("B25024", 1)),
    "h14_vacancy_rate": (L("B25002", 3), L("B25002", 1)),
    "h15_owner_share": (L("B25003", 2), L("B25003", 1)),
    "h17_share_1to3_rooms": (L("B25017", 2, 3, 4), L("B25017", 1)),
    "h18_share_0to1_bedrooms": (L("B25041", 2, 3), L("B25041", 1)),
    "h19_share_crowded": (L("B25014", 5, 6, 7, 11, 12, 13), L("B25014", 1)),
    "c10_share_with_mortgage": (L("B25081", 2), L("B25081", 1)),
    "p03_share_under18": (L("B01001", *rng(3, 6), *rng(27, 30)), L("B01001", 1)),
    "p04_share_18to34": (L("B01001", *rng(7, 12), *rng(31, 36)), L("B01001", 1)),
    "p05_share_35to64": (L("B01001", *rng(13, 19), *rng(37, 43)), L("B01001", 1)),
    "p06_share_65plus": (L("B01001", *rng(20, 25), *rng(44, 49)), L("B01001", 1)),
    "p07_share_hh_children": (L("B11005", 2), L("B11005", 1)),
    "p08_share_living_alone": (L("B11001", 8), L("B11001", 1)),
    "p09_share_bachelors_plus": (L("B15002", *rng(15, 18), *rng(32, 35)), L("B15002", 1)),
    "p10_share_no_hs_diploma": (L("B15002", *rng(3, 10), *rng(20, 27)), L("B15002", 1)),
    "p13_share_income_under25k": (L("B19001", *rng(2, 5)), L("B19001", 1)),
    "p14_share_income_25to50k": (L("B19001", *rng(6, 10)), L("B19001", 1)),
    "p15_share_income_50to100k": (L("B19001", *rng(11, 13)), L("B19001", 1)),
    "p16_share_income_100k_plus": (L("B19001", *rng(14, 17)), L("B19001", 1)),
    "p18_poverty_rate": (L("B17001", 2), L("B17001", 1)),
    "p19_share_snap": (L("B19058", 2), L("B19058", 1)),
    "p20_labour_force_participation": (L("B23001", *[g + 1 for g in U65 + O65]), L("B23001", 1)),
    "p21_unemployment_rate": (L("B23001", *[g + 5 for g in U65], *[g + 3 for g in O65]),
                              L("B23001", *[g + 3 for g in U65], *[g + 1 for g in O65])),
    "m01_share_no_vehicle": (L("B25044", 3, 10), L("B25044", 1)),
    "m02_share_2plus_vehicles": (L("B25044", *rng(5, 8), *rng(12, 15)), L("B25044", 1)),
    "m03_vehicles_per_household": (L("B25046", 1), L("B25044", 1)),
    "m04_commute_drove_alone": (L("B08301", 3), L("B08301", 1)),
    "m05_commute_carpool": (L("B08301", 4), L("B08301", 1)),
    "m06_commute_transit": (L("B08301", 10), L("B08301", 1)),
    "m07_commute_walk": (L("B08301", 19), L("B08301", 1)),
    "m08_commute_bicycle": (L("B08301", 18), L("B08301", 1)),
    "m09_work_from_home": (L("B08301", 21), L("B08301", 1)),
    "m11_share_commute_under15": (L("B08303", 2, 3, 4), L("B08303", 1)),
    "m12_share_commute_15to29": (L("B08303", 5, 6, 7), L("B08303", 1)),
    "m13_share_commute_30to44": (L("B08303", 8, 9, 10), L("B08303", 1)),
    "m14_share_commute_45plus": (L("B08303", 11, 12, 13), L("B08303", 1)),
    "m15_leave_before_7am": (L("B08302", *rng(2, 6)), L("B08302", 1)),
    "m16_leave_7_to_9am": (L("B08302", *rng(7, 10)), L("B08302", 1)),
    "m17_leave_9am_or_later": (L("B08302", *rng(11, 15)), L("B08302", 1)),
    "m18_work_in_home_place": (L("B08008", 3), L("B08008", 1)),
}
VALUE = {"h16_median_rooms": "B25018_001E", "c01_median_rent": "B25064_001E", "c02_rent_lower_quartile": "B25057_001E",
         "c03_rent_upper_quartile": "B25059_001E", "c04_median_value": "B25077_001E", "c05_value_lower_quartile": "B25076_001E",
         "c06_value_upper_quartile": "B25078_001E", "c09_median_rent_pct_income": "B25071_001E",
         "c11_owner_costs_mortgaged": "B25088_002E", "c12_owner_costs_pct_income": "B25092_001E",
         "c13_median_housing_costs": "B25105_001E", "p01_household_size": "B25010_001E", "p02_median_age": "B01002_001E",
         "p11_median_income": "B19013_001E", "p12_per_capita_income": "B19301_001E", "p17_gini": "B19083_001E",
         "p22_median_earnings": "B20002_001E"}


def build_year(y: int) -> pd.DataFrame:
    frames = {}
    for p in IN.glob(f"acs5_{y}_*.csv.gz"):
        frames[p.name.split("_")[2].split(".")[0]] = pd.read_csv(p, index_col=0)
    X = pd.concat(frames.values(), axis=1)
    X = X.where(X >= 0)  # Census special codes are negative
    out = pd.DataFrame(index=X.index)
    for k, (num, den) in SHARE.items():
        cols_n, cols_d = [c for c in num if c in X], [c for c in den if c in X]
        if cols_n and cols_d:
            d = X[cols_d].sum(axis=1, min_count=1)
            out[k] = (X[cols_n].sum(axis=1, min_count=1) / d).where(d > 0)
    for k, c in VALUE.items():
        if c in X:
            out[k] = X[c]
    # rent burden: lines 7-10 / (line 1 - line 11)
    if "B25070_001E" in X:
        den = X["B25070_001E"] - X["B25070_011E"]
        out["c07_rent_burden_30"] = (X[L("B25070", 7, 8, 9, 10)].sum(axis=1) / den).where(den > 0)
        out["c08_rent_burden_50"] = (X["B25070_010E"] / den).where(den > 0)
    out["c14_value_to_annual_rent"] = (out.get("c04_median_value") / (12 * out.get("c01_median_rent"))).replace([np.inf, -np.inf], np.nan)
    out["h20_years_since_moved_in"] = y - X["B25039_001E"] if "B25039_001E" in X else np.nan
    if "B07001_001E" in X:
        out["h21_share_moved_last_year"] = ((X["B07001_001E"] - X["B07001_017E"]) / X["B07001_001E"]).where(X["B07001_001E"] > 0)
    if "B08013_001E" in X:
        den = X["B08301_001E"] - X["B08301_021E"]
        out["m10_mean_commute_minutes"] = (X["B08013_001E"] / den).where(den > 0)
    # built-year shares, pre-2000 categories (TOD's definitions): in every release layout the last 7 lines of B25034
    # are 1990-99, 1980-89, 1970-79, 1960-69, 1950-59, 1940-49 and 1939 or earlier (newer bands are added at the top)
    if "B25034_001E" in X:
        cols = sorted(c for c in X.columns if c.startswith("B25034_") and c != "B25034_001E")
        tot = X["B25034_001E"]
        last7 = cols[-7:]

        def sh(cs):
            return (X[cs].sum(axis=1) / tot).where(tot > 0)
        out["h09_share_built_1980_99"] = sh(last7[0:2])
        out["h10_share_built_1960_79"] = sh(last7[2:4])
        out["h11_share_built_1940_59"] = sh(last7[4:6])
        out["h12_share_built_pre1940"] = sh(last7[6:7])
    out["release_end"] = y
    out.index.name = "acs_geoid"
    return out.reset_index()


def main() -> None:
    T = pd.concat([build_year(y) for y in YEARS], ignore_index=True)
    T.to_csv(IN / "traits_by_release.csv.gz", index=False, compression="gzip")
    print(T.shape, T.notna().mean().round(3).to_dict())


if __name__ == "__main__":
    main()
