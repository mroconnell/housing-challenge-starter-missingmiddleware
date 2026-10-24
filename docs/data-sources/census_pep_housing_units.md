# Census annual housing-unit estimates (Population Estimates Program)

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `census_pep_housing_units`  
**Handbook listing:** Not in the handbook. Used by the Wisconsin foundation build.

## Summary

| | |
|---|---|
| Publisher | U.S. Census Bureau, Population Estimates Program |
| What it is | Estimated total housing units on July 1 of each year, by county. The pipeline reads the Wisconsin county table CO-EST2025-HU-55. |
| Geography | State and county. Sub-county PEP files have population only, not housing units. |
| Time coverage and update frequency | Vintage 2025: April 1, 2020 base, then July 1, 2020-2025. Each new vintage revises all earlier years. |
| Units | Housing units. |
| Access method | Excel table: https://www2.census.gov/programs-surveys/popest/tables/2020-2025/housing/totals/CO-EST2025-HU-55.xlsx (no key). |
| License | Public domain (U.S. federal government work). |
| Use in our model | Existing housing stock and annual net change by county, for the baseline. |
| Caveats | Net stock change, not gross new construction. Keep one vintage for the whole series, because each vintage revises prior years. |

## Access details

- Endpoint used for the sample: `https://www2.census.gov/programs-surveys/popest/tables/2020-2025/housing/totals/CO-EST2025-HU-55.xlsx`
- County rows: 73
- Table title: table with row headers in column A and column headers in rows 3 through 4 (leading dots indicate sub-parts)
- Rows are Wisconsin, then its counties. Sub-county PEP files hold population only, not housing units.

## Fields (8)

| Field | Type | Meaning |
|---|---|---|
| `Geographic Area` | string | State or county name (counties start with a dot). |
| `April 1, 2020 Estimates Base` | string |  |
| `2020` | int |  |
| `2021` | int |  |
| `2022` | int |  |
| `2023` | int |  |
| `2024` | int |  |
| `2025` | int |  |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Sample rows

First 3 of 6 rows in [`data/sample/census_pep_housing_units.csv`](../../data/sample/census_pep_housing_units.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 | Row 6 |
|---|---|---|---|---|---|---|
| `Geographic Area` | Wisconsin | .Adams County, Wisconsin | .Ashland County, Wisconsin | .Barron County, Wisconsin | .Bayfield County, Wisconsin | .Brown County, Wisconsin |
| `April 1, 2020 Estimates Base` | 2727726 | 16692 | 9407 | 23780 | 13238 | 112908 |
| `2020` | 2732728 | 16715 | 9411 | 23809 | 13247 | 113253 |
| `2021` | 2756457 | 16839 | 9418 | 23950 | 13285 | 114776 |
| `2022` | 2781518 | 16965 | 9457 | 24050 | 13354 | 115638 |
| `2023` | 2802492 | 17077 | 9510 | 24193 | 13413 | 116615 |
| `2024` | 2820234 | 17180 | 9539 | 24354 | 13481 | 117326 |
| `2025` | 2840960 | 17316 | 9559 | 24495 | 13574 | 118788 |

## Refresh

```sh
python3 scripts/fetch_samples.py census_pep_housing_units
python3 scripts/build_data_dictionaries.py
```
