# Census Building Permits Survey (BPS)

**Status:** Fetched (last fetch 2026-10-23)  
**Source id:** `census_bps`  
**Handbook listing:** Census Building Permits Survey

## Summary

| | |
|---|---|
| Publisher | U.S. Census Bureau |
| What it is | New privately owned housing units authorized by building permits, by building size (1, 2, 3-4, 5+ units). |
| Geography | Nation, region, state, metro, county, and about 20,000 permit-issuing places. |
| Time coverage and update frequency | Monthly and annual. Annual files about 3-4 months after year end. |
| Units | Bldgs = buildings, Units = housing units, Value = construction cost in dollars. 'rep' columns are reported only; 'est' columns include imputation for non-reporters. |
| Access method | Flat files at `https://www2.census.gov/econ/bps/{State\|County\|Place\|Metro}/{prefix}{YYYY}{a\|mm}.txt`. CSV with two header rows. |
| License | Public domain (U.S. federal government work). |
| Use in our model | The baseline: how many units get permitted per year, and the split by building size. The 2-4 unit columns are the closest public measure of missing-middle production. |
| Caveats | Permits are not completions; some permitted units are never built. ADUs are usually not split out and may be missing or counted as 1-unit. Some places do not report every month. |

## Access details

- Endpoint used for the sample: `https://www2.census.gov/econ/bps/State/st2025a.txt`

## Fields (32)

| Field | Type | Meaning |
|---|---|---|
| `geo_level` |  | state or county (added by our script). |
| `Survey Date` |  | Year, with 99 for the annual total (202599 = all of 2025). |
| `FIPS State` |  | 2-digit state FIPS code. |
| `Region Code` |  | Census region (1 Northeast, 2 Midwest, 3 South, 4 West). |
| `Division Code` |  | Census division (1-9). |
| `State Name` |  | State name. |
| `1-unit Bldgs` |  | Buildings permitted in 1-unit buildings. Includes Census imputation for non-reporting places. |
| `1-unit Units` |  | Housing units permitted in 1-unit buildings. Includes Census imputation for non-reporting places. |
| `1-unit Value` |  | Construction value in thousands of dollars permitted in 1-unit buildings. Includes Census imputation for non-reporting places. |
| `2-units Bldgs` |  | Buildings permitted in 2-units buildings. Includes Census imputation for non-reporting places. |
| `2-units Units` |  | Housing units permitted in 2-units buildings. Includes Census imputation for non-reporting places. |
| `2-units Value` |  | Construction value in thousands of dollars permitted in 2-units buildings. Includes Census imputation for non-reporting places. |
| `3-4 units Bldgs` |  | Buildings permitted in 3-4 units buildings. Includes Census imputation for non-reporting places. |
| `3-4 units Units` |  | Housing units permitted in 3-4 units buildings. Includes Census imputation for non-reporting places. |
| `3-4 units Value` |  | Construction value in thousands of dollars permitted in 3-4 units buildings. Includes Census imputation for non-reporting places. |
| `5+ units Bldgs` |  | Buildings permitted in 5+ units buildings. Includes Census imputation for non-reporting places. |
| `5+ units Units` |  | Housing units permitted in 5+ units buildings. Includes Census imputation for non-reporting places. |
| `5+ units Value` |  | Construction value in thousands of dollars permitted in 5+ units buildings. Includes Census imputation for non-reporting places. |
| `1-unit rep Bldgs` |  | Buildings permitted in 1-unit buildings. Reported only (no imputation for non-reporting places). |
| `1-unit rep Units` |  | Housing units permitted in 1-unit buildings. Reported only (no imputation for non-reporting places). |
| `1-unit rep Value` |  | Construction value in thousands of dollars permitted in 1-unit buildings. Reported only (no imputation for non-reporting places). |
| `2-units rep Bldgs` |  | Buildings permitted in 2-units buildings. Reported only (no imputation for non-reporting places). |
| `2-units rep Units` |  | Housing units permitted in 2-units buildings. Reported only (no imputation for non-reporting places). |
| `2-units rep Value` |  | Construction value in thousands of dollars permitted in 2-units buildings. Reported only (no imputation for non-reporting places). |
| `3-4 units rep Bldgs` |  | Buildings permitted in 3-4 units buildings. Reported only (no imputation for non-reporting places). |
| `3-4 units rep Units` |  | Housing units permitted in 3-4 units buildings. Reported only (no imputation for non-reporting places). |
| `3-4 units rep Value` |  | Construction value in thousands of dollars permitted in 3-4 units buildings. Reported only (no imputation for non-reporting places). |
| `5+ units rep Bldgs` |  | Buildings permitted in 5+ units buildings. Reported only (no imputation for non-reporting places). |
| `5+ units rep Units` |  | Housing units permitted in 5+ units buildings. Reported only (no imputation for non-reporting places). |
| `5+ units rep Value` |  | Construction value in thousands of dollars permitted in 5+ units buildings. Reported only (no imputation for non-reporting places). |
| `FIPS County` |  | 3-digit county FIPS code. |
| `County Name` |  | County name. |

- state file: `https://www2.census.gov/econ/bps/State/st2025a.txt`
- county file: `https://www2.census.gov/econ/bps/County/co2025a.txt`

The raw file has two header rows. Our script joins them into one name, for example `1-unit` + `Units` = `1-unit Units`.

## Sample rows

First 3 of 10 rows in [`data/sample/census_bps.csv`](../../data/sample/census_bps.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 | Row 6 | Row 7 | Row 8 | Row 9 | Row 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| `geo_level` | state | state | state | state | state | county | county | county | county | county |
| `Survey Date` | 202599 | 202599 | 202599 | 202599 | 202599 | 2025 | 2025 | 2025 | 2025 | 2025 |
| `FIPS State` | 01 | 02 | 04 | 05 | 06 | 01 | 01 | 01 | 01 | 01 |
| `Region Code` | 3 | 4 | 4 | 3 | 4 | 3 | 3 | 3 | 3 | 3 |
| `Division Code` | 6 | 9 | 8 | 7 | 9 | 6 | 6 | 6 | 6 | 6 |
| `State Name` | Alabama | Alaska | Arizona | Arkansas | California |  |  |  |  |  |
| `1-unit Bldgs` | 15402 | 573 | 33371 | 10298 | 57739 | 200 | 2517 | 14 | 5 | 16 |
| `1-unit Units` | 15402 | 573 | 33371 | 10298 | 57739 | 200 | 2517 | 14 | 5 | 16 |
| `1-unit Value` | 4547092 | 214651 | 10354124 | 2953067 | 18455202 | 82131895 | 848168534 | 4021800 | 1517215 | 3347083 |
| `2-units Bldgs` | 66 | 36 | 589 | 485 | 1748 | 0 | 6 | 0 | 0 | 0 |
| `2-units Units` | 132 | 72 | 1178 | 970 | 3496 | 0 | 12 | 0 | 0 | 0 |
| `2-units Value` | 24375 | 16546 | 161965 | 133627 | 722819 | 0 | 1754655 | 0 | 0 | 0 |
| `3-4 units Bldgs` | 60 | 13 | 79 | 92 | 330 | 0 | 1 | 0 | 0 | 1 |
| `3-4 units Units` | 228 | 44 | 292 | 310 | 1137 | 0 | 4 | 0 | 0 | 4 |
| `3-4 units Value` | 27906 | 8420 | 55005 | 23057 | 252973 | 0 | 388350 | 0 | 0 | 210000 |
| `5+ units Bldgs` | 197 | 14 | 509 | 188 | 1349 | 0 | 13 | 0 | 0 | 0 |
| `5+ units Units` | 3299 | 159 | 16691 | 3914 | 41484 | 0 | 132 | 0 | 0 | 0 |
| `5+ units Value` | 502911 | 26412 | 2840790 | 594780 | 7073052 | 0 | 19301135 | 0 | 0 | 0 |
| `1-unit rep Bldgs` | 13035 | 548 | 31858 | 8811 | 53501 | 200 | 2422 | 14 | 5 | 16 |
| `1-unit rep Units` | 13035 | 548 | 31858 | 8811 | 53501 | 200 | 2422 | 14 | 5 | 16 |
| `1-unit rep Value` | 3975707 | 207080 | 10001513 | 2648166 | 17121556 | 82131895 | 829953600 | 4021800 | 1517215 | 3347083 |
| `2-units rep Bldgs` | 48 | 36 | 566 | 406 | 1608 | 0 | 6 | 0 | 0 | 0 |
| `2-units rep Units` | 96 | 72 | 1132 | 812 | 3216 | 0 | 12 | 0 | 0 | 0 |
| `2-units rep Value` | 12446 | 16546 | 156344 | 116750 | 668793 | 0 | 1754655 | 0 | 0 | 0 |
| `3-4 units rep Bldgs` | 50 | 13 | 78 | 37 | 292 | 0 | 1 | 0 | 0 | 1 |
| `3-4 units rep Units` | 195 | 44 | 289 | 131 | 1023 | 0 | 4 | 0 | 0 | 4 |
| `3-4 units rep Value` | 22106 | 8420 | 54809 | 13587 | 226902 | 0 | 388350 | 0 | 0 | 210000 |
| `5+ units rep Bldgs` | 166 | 14 | 452 | 122 | 1172 | 0 | 13 | 0 | 0 | 0 |
| `5+ units rep Units` | 2726 | 159 | 14834 | 3342 | 38887 | 0 | 132 | 0 | 0 | 0 |
| `5+ units rep Value` | 397892 | 26412 | 2532752 | 549159 | 6619912 | 0 | 19301135 | 0 | 0 | 0 |
| `FIPS County` |  |  |  |  |  | 001 | 003 | 005 | 007 | 009 |
| `County Name` |  |  |  |  |  | Autauga County | Baldwin County | Barbour County | Bibb County | Blount County |

## Refresh

```sh
python3 scripts/fetch_samples.py census_bps
python3 scripts/build_data_dictionaries.py
```
