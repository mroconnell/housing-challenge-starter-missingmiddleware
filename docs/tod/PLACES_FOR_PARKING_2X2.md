# TOD places for the parking 2×2

The parking thread's 2×2 test needs two lists: places that upzoned near transit, and places that did neither.
This file gives both, built from the TOD records only.

- **Table:** [reference/tod_places_for_parking_2x2.csv](../../reference/tod_places_for_parking_2x2.csv)
- **Script:** [scripts/build_tod_places_for_parking_2x2.py](../../scripts/build_tod_places_for_parking_2x2.py)
- **Test:** [tests/test_tod_places_for_parking_2x2.py](../../tests/test_tod_places_for_parking_2x2.py)

## Sources

| Source file | What it gives | Columns read |
|---|---|---|
| `reference/tod_cases.csv` (US rows) | upzoned places, year, parking | case, city, state, dates, parking flag and detail |
| `reference/tod_census_set.csv` | station-area reforms (case ids only) | case, label, adopted |
| `reference/tod_control_cities_controls.csv` | matched comparison cities | test, method, place, state |
| LOT_MODEL_PLAN item 46 | no-reform placebo cities | names only |
| `reference/parking_reform_cases.csv` | PRN parking record | all (rule columns) |
| `reference/parking_reform_taxonomy.csv` | weaker PRN records, notes only | rule columns |
| 2024 Census gazetteer (places, county subdivisions) | GEOIDs | name, state, GEOID |
| `data/raw/census_bps_county/co2020a.txt` | county GEOIDs | county name and FIPS only |

- No permit, home, effect, weight or status column was loaded.
- Each table is read with a fixed column list.

## Coding rules

- **Upzoned:** every US place in `tod_cases.csv`.
- **Year:** earliest clear year in adoption or effective date.
- "About" years count only if no other year.
- One fix: San Francisco Market-Octavia uses 2008, not plan approval (late 2007).
- **Place year:** earliest year across the place's TOD cases.
- **Parking (per case):**
  - Record flag `no` → `no`; `unknown` → `unknown`.
  - Flag `yes`, detail says removal → `yes`.
  - Flag `yes`, detail says cuts, tiers, fees, or part of area → `partial`.
  - Philadelphia: flag `no`, but its /TOD overlay cuts minimums → `partial`.
- **Parking (per place):** the case(s) at the first upzoning year.
  - Mixed `yes` and `partial` → `partial`.
  - Mixed with `unknown` → `unknown` (Seattle 2012).
- **Census set:** adds case ids only; all its places are already in `tod_cases.csv`.
- **Sub-city areas → zoning jurisdiction:**
  - New York (Brooklyn) → New York city.
  - Fairfax County (Tysons) → Fairfax County, VA.
  - Montgomery County (North Bethesda) → Montgomery County, MD.
- **Multi-place cases:**
  - `ma_40r_transit_districts`: rows for Brockton, Haverhill, Lowell. "Smaller towns" not named, so not rows.
  - `mbta_communities_2021`: 177 towns not listed in the record. No rows.
  - Zurich and other non-US cases: skipped.
- **Neither candidates:** every place in `tod_control_cities_controls.csv`.
  - Plus the lot model's no-reform placebo cities (Columbus, Kansas City, Milwaukee).
  - Any place in the upzoned list is dropped.
- **PRN record:** matched on place name plus state.
  - Format: policy; status; year; scope.
  - A neither candidate with a PRN reform stays in. The parking thread picks its cell.
- **GEOIDs:** exact name plus state in the gazetteer. No fuzzy match.

## Counts

| Group | Places (count) | With a PRN record in parking_reform_cases.csv (count) |
|---|---|---|
| upzoned | 38 | 11 |
| neither_candidate | 67 | 5 |
| **all** | **105** | **16** |

Parking change with the upzoning, upzoned places only (count of 38 places):

| Parking with upzoning | Places (count) | Places |
|---|---|---|
| yes | 9 | San Diego, San Francisco, Denver, Somerville, Ann Arbor, Jersey City, Charlotte, Portland, Madison |
| partial | 8 | Los Angeles, Oakland, Chicago, St. Paul, Philadelphia, Austin, Salt Lake City, Shoreline |
| no | 3 | San Jose, Kansas City, New York |
| unknown | 18 | the rest |

- Neither candidates with no PRN record in the cases file: 62 of 67 places.
- The 5 with one: Alameda (2021), Baltimore (2025), Durham (2023), Grand Rapids (year blank), Greensboro (year blank).
- Unmatched places: none. All 105 got a GEOID.
- Dropped from neither: Kansas City (it is an upzoned TOD case).
- Placebo cities added no new places. Columbus and Milwaukee were already comparison cities.

## Caveats

- **Unknown is common.** 18 of 38 upzoned places have no clear parking record.
- **The PRN cases file is narrow.** It holds only full removals rated at or near the benchmark.
- **No PRN record ≠ no parking reform.** 55 of 67 neither candidates have weaker PRN records (downtown-only, cuts). These are in `notes`.
- **Comparison cities were matched on size and growth, not checked for upzoning.** "Neither" is a candidate label only.
- **Timing notes matter.** Some parking changes came later and separately:
  - Minneapolis: removal May 2021, after the 2020 plan.
  - San Diego: separate 2019 parking reform.
  - Shoreline: parking cut 2022, after 2015 upzoning.
  - New York Downtown Brooklyn: minimums cut 2013, not 2004.
- **Flag "yes" with unknown detail:** Jersey City, Portland. Coded `yes` as the record says.
- **Place-wide rows for area reforms.** A station-area upzoning marks the whole city or county.
- **MBTA towns are missing.** The record does not name them.
- **Austin's year is 2005** (district ordinance). Station plans came 2008–2009.
- **Raleigh's year is 2024** from the dates. The reform name also cites a 2021 overlay.
- **Bloomington uses 2015.** The record also says "about 2006" for HX-R.
