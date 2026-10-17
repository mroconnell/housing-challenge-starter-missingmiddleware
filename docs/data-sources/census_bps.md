# Census Building Permits Survey (BPS)

**Status:** Fetched (last fetch 2026-10-17)  
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

| Field | Row 1 | Row 2 | Row 3 |
|---|---|---|---|
| `geo_level` | state | state | state |
| `Survey Date` | 202599 | 202599 | 202599 |
| `FIPS State` | 01 | 02 | 04 |
| `Region Code` | 3 | 4 | 4 |
| `Division Code` | 6 | 9 | 8 |
| `State Name` | Alabama | Alaska | Arizona |
| `1-unit Bldgs` | 15402 | 573 | 33371 |
| `1-unit Units` | 15402 | 573 | 33371 |
| `1-unit Value` | 4547092 | 214651 | 10354124 |
| `2-units Bldgs` | 66 | 36 | 589 |
| `2-units Units` | 132 | 72 | 1178 |
| `2-units Value` | 24375 | 16546 | 161965 |
| `3-4 units Bldgs` | 60 | 13 | 79 |
| `3-4 units Units` | 228 | 44 | 292 |
| `3-4 units Value` | 27906 | 8420 | 55005 |
| `5+ units Bldgs` | 197 | 14 | 509 |
| `5+ units Units` | 3299 | 159 | 16691 |
| `5+ units Value` | 502911 | 26412 | 2840790 |
| `1-unit rep Bldgs` | 13035 | 548 | 31858 |
| `1-unit rep Units` | 13035 | 548 | 31858 |
| `1-unit rep Value` | 3975707 | 207080 | 10001513 |
| `2-units rep Bldgs` | 48 | 36 | 566 |
| `2-units rep Units` | 96 | 72 | 1132 |
| `2-units rep Value` | 12446 | 16546 | 156344 |
| `3-4 units rep Bldgs` | 50 | 13 | 78 |
| `3-4 units rep Units` | 195 | 44 | 289 |
| `3-4 units rep Value` | 22106 | 8420 | 54809 |
| `5+ units rep Bldgs` | 166 | 14 | 452 |
| `5+ units rep Units` | 2726 | 159 | 14834 |
| `5+ units rep Value` | 397892 | 26412 | 2532752 |
| `FIPS County` |  |  |  |
| `County Name` |  |  |  |

## Refresh

```sh
python3 scripts/fetch_samples.py census_bps
python3 scripts/build_data_dictionaries.py
```
