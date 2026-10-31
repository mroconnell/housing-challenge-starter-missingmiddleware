# ADU all-homes cross-check: plan written before running

Written 2026-10-31 by the ADU conductor, from Ryan's idea (relayed by the audit): measure ADU laws the same way as the other scenarios. Count all homes permitted before and after each state's law, per 1,000 existing homes, against states with no law. No result below had been computed when this file was committed.

## Why

- The ADU model counts ADU permits. The other two scenarios count all permitted homes.
- This check asks: did total home permits rise after a statewide ADU law, compared with states without one?
- It is a cross-check, not a replacement. The Census permit survey often misses ADUs: conversions and attached units are usually not counted as new homes. So the measured effect leans toward 0.

## Data

- **Census Building Permits Survey, state annual files, 2010–2025** (`data/raw/census_bps_state/`, already in the repository).
- **Two outcomes:** all units, and units in 1–4 unit buildings.
- **Denominator:** existing homes (ACS 2020–2024, B25024 total), the same for every year.
- **Rate:** permits per 1,000 existing homes per year.

## States and dates

The law year is the first calendar year with the law in force for most of the year, using the model's AQ-065 coding.

| State | First law year | After years in the data (to 2025) |
| --- | --- | --- |
| California | 2020 (2019 package) | 2020–2025 (6) |
| Oregon | 2020 (HB 2001 ADU rules) | 2020–2025 (6) |
| Vermont | 2021 | 2021–2025 (5) |
| Utah | 2022 | 2022–2025 (4) |
| Maine | 2025 | 2025 (1) |
| Massachusetts | 2025 | 2025 (1) |
| Rhode Island | 2025 | 2025 (1) |
| Washington | 2026 (local compliance) | none, so left out |

- **Comparison states:** the 50 states and DC, minus every state with a statewide ADU law (strong or weaker) in force by the end of the case's after-window.
- **Before window:** the 3 years before the law year.
- **After window:** up to the first 3 law years.

## Measure

For each law state:
- **change** = after-window rate minus before-window rate;
- **effect** = its change minus the median change of the comparison states over the same calendar years.

Summaries:
- the equal-weight average and the median of the 7 effects;
- a placebo: every comparison state given each law state's dates. That gives the spread of "effects" with no law. Report where the real average falls in it (the share of placebo averages at or above it).

**Wisconsin.** Effect (permits per 1,000 homes per year) × Wisconsin's 2,840,960 homes × 5 years ÷ 1,000, beside the model's central (10,349 ADU permits).

**Reading.** If the all-homes effect is near zero or inside the placebo spread, the check cannot see the ADU effect. That is expected given the survey's ADU blind spot. If it is clearly positive, compare its size with the model's.

## Changes after writing

None yet.
