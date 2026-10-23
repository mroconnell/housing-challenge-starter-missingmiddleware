# American Community Survey (ACS) 5-year estimates

**Status:** Fetched (last fetch 2026-10-23)  
**Source id:** `acs`  
**Handbook listing:** U.S. Census Bureau/American Community Survey (ACS)

## Summary

| | |
|---|---|
| Publisher | U.S. Census Bureau |
| What it is | Survey-based estimates of population, households, housing stock, tenure, rents, values and incomes. |
| Geography | Nation, state, county, place, tract, block group (5-year). 1-year only for areas of 65,000+ people. |
| Time coverage and update frequency | 5-year rolling period (for example 2020-2024). Released every December. |
| Units | Counts are housing units or people. Dollar fields are inflation-adjusted to the last year of the period. Every estimate has a margin of error field (suffix M instead of E). |
| Access method | Census Data API, `https://api.census.gov/data/{year}/acs/acs5?get=...&for=...`, now needs a free key (https://api.census.gov/data/key_signup.html). No-key option: table-based summary files at `https://www2.census.gov/programs-surveys/acs/summary_file/{year}/table-based-SF/data/5YRData/acsdt5y{year}-{table}.dat` (pipe-delimited, all geographies). Our sample uses the summary file for table B25024 (Units in Structure). |
| License | Public domain (U.S. federal government work). |
| Use in our model | Baseline housing stock and mix (units in structure), vacancy, tenure, rents and incomes for feasibility and demand. Base for all five scenarios. |
| Caveats | Estimates, not counts. Small areas have large margins of error. Not a measure of new production; pair with Building Permits Survey. |

## Access details

- Endpoint used for the sample: `https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-b25024.dat`
- Vintage: ACS 5-year, table B25024 (Units in Structure)
- The Census Data API now answers 'Missing Key' without a free key (https://api.census.gov/data/key_signup.html). Without a key our script reads the table-based summary file, which needs none. Set CENSUS_API_KEY to use the API.

## Fields (23)

| Field | Type | Meaning |
|---|---|---|
| `GEO_ID` | string | Census GEO_ID. 0400000US + 2-digit FIPS = state; 0500000US + 5-digit FIPS = county. |
| `B25024_E001` | int | Units in structure: Total housing units, estimate |
| `B25024_M001` | int | Units in structure: Total housing units, margin of error (90%) |
| `B25024_E002` | int | Units in structure: 1, detached, estimate |
| `B25024_M002` | int | Units in structure: 1, detached, margin of error (90%) |
| `B25024_E003` | int | Units in structure: 1, attached, estimate |
| `B25024_M003` | int | Units in structure: 1, attached, margin of error (90%) |
| `B25024_E004` | int | Units in structure: 2 units, estimate |
| `B25024_M004` | int | Units in structure: 2 units, margin of error (90%) |
| `B25024_E005` | int | Units in structure: 3 or 4 units, estimate |
| `B25024_M005` | int | Units in structure: 3 or 4 units, margin of error (90%) |
| `B25024_E006` | int | Units in structure: 5 to 9 units, estimate |
| `B25024_M006` | int | Units in structure: 5 to 9 units, margin of error (90%) |
| `B25024_E007` | int | Units in structure: 10 to 19 units, estimate |
| `B25024_M007` | int | Units in structure: 10 to 19 units, margin of error (90%) |
| `B25024_E008` | int | Units in structure: 20 to 49 units, estimate |
| `B25024_M008` | int | Units in structure: 20 to 49 units, margin of error (90%) |
| `B25024_E009` | int | Units in structure: 50 or more units, estimate |
| `B25024_M009` | int | Units in structure: 50 or more units, margin of error (90%) |
| `B25024_E010` | int | Units in structure: Mobile home, estimate |
| `B25024_M010` | int | Units in structure: Mobile home, margin of error (90%) |
| `B25024_E011` | int | Units in structure: Boat, RV, van, etc., estimate |
| `B25024_M011` | int | Units in structure: Boat, RV, van, etc., margin of error (90%) |

## Sample rows

First 3 of 5 rows in [`data/sample/acs.csv`](../../data/sample/acs.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 |
|---|---|---|---|
| `GEO_ID` | 0400000US01 | 0400000US02 | 0400000US04 |
| `B25024_E001` | 2337265 | 328491 | 3192839 |
| `B25024_M001` | 430 | 442 | 631 |
| `B25024_E002` | 1615503 | 207626 | 2048854 |
| `B25024_M002` | 5711 | 1932 | 5988 |
| `B25024_E003` | 44189 | 25701 | 165025 |
| `B25024_M003` | 1627 | 1103 | 3278 |
| `B25024_E004` | 41971 | 17246 | 42794 |
| `B25024_M004` | 1764 | 1003 | 1545 |
| `B25024_E005` | 69408 | 23573 | 104146 |
| `B25024_M005` | 2547 | 1252 | 3226 |
| `B25024_E006` | 96496 | 15445 | 113424 |
| `B25024_M006` | 2770 | 1058 | 3856 |
| `B25024_E007` | 75131 | 9265 | 119556 |
| `B25024_M007` | 2779 | 677 | 3860 |
| `B25024_E008` | 43111 | 10637 | 80415 |
| `B25024_M008` | 1965 | 718 | 2856 |
| `B25024_E009` | 59026 | 5592 | 209693 |
| `B25024_M009` | 2174 | 582 | 3957 |
| `B25024_E010` | 286771 | 12962 | 297009 |
| `B25024_M010` | 4000 | 946 | 3833 |
| `B25024_E011` | 5659 | 444 | 11923 |
| `B25024_M011` | 632 | 156 | 883 |

## Refresh

```sh
python3 scripts/fetch_samples.py acs
python3 scripts/build_data_dictionaries.py
```
