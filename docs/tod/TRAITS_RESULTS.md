# TOD trait test: results

Written 2026-10-27. The test follows [TRAITS_PLAN.md](TRAITS_PLAN.md) (commit `b053b2d`), which was written before any trait was compared with any effect. Every departure from it is in the plan's section 8, dated, and summarised under [Departures](#departures). The sections below were written in the order the plan sets: the unit list was fixed and written down first, then each trait's source, and only then were traits joined to effects.

**Files.**
- Code: [missing_middleware/tod/traits.py](../../missing_middleware/tod/traits.py) (rules and arithmetic), [scripts/run_tod_traits.py](../../scripts/run_tod_traits.py) (stages `fetch`, `units`, `traits`, `test`), tests in [tests/test_tod_traits.py](../../tests/test_tod_traits.py).
- Results: [reference/tod_trait_units.csv](../../reference/tod_trait_units.csv) (every candidate unit, kept or not), [reference/tod_trait_values.csv](../../reference/tod_trait_values.csv), [reference/tod_trait_results.csv](../../reference/tod_trait_results.csv), [reference/tod_trait_errors.csv](../../reference/tod_trait_errors.csv), [reference/tod_trait_heldout_units.csv](../../reference/tod_trait_heldout_units.csv).
- None of these files holds a parcel, permit, project or person identifier; a test checks this.
- The case files and adapters were imported, never edited.

**How to read the numbers.** The effect of a unit is a difference-in-differences: (treatment after − treatment before) − (comparison after − comparison before), each a mean yearly rate in **homes permitted per eligible acre per year**. Its 90% interval comes from redrawing whole projects, 2,000 draws, seed 20261026, as in the cases.

## Units, fixed before traits

Fixed 2026-10-27, before any trait value was computed. The full list, with each unit's eligible acres, effect, interval and dose, is [reference/tod_trait_units.csv](../../reference/tod_trait_units.csv).

**How units were cut** (plan section 2; details in section 8 of the plan):
- **New York:** each rezoning in the pooled set, built exactly as in the case (`case_nyc.build_member`). The pooled set has 17 measured rezonings.
- **Philadelphia:** each remapping bill with eligible treated land (`case_philadelphia.build_member`), 83 bills.
- **Charlotte, Chicago, Saint Paul:** each case was rebuilt with its own adapter, unchanged. Each treated lot was then given to its nearest station. Stops within 150 m of each other (platforms, two directions) count as one station. Saint Paul uses only Green Line stations in the city, as its case does.
- **Madison:** the overlay's treated land, split into corridor segments: the Isthmus core (within 1 mile of the State Capitol) and eight 45-degree sectors around it (north, northeast and so on). Seven of the nine segments hold treated land.
- **Each unit's comparison:** the case's own comparison lots within ¼ mile of that unit's treated lots. Neighbouring units can share comparison lots.
- **Periods:** the case's own (New York and Philadelphia by each member's effective year).
- **Kept:** at least 5 eligible acres in each of treatment and comparison.

**Counts.**

| City | Role in the test | Candidate units | Kept | Eligible treatment acres kept | Eligible comparison acres kept (shared lots counted once per unit) |
| --- | --- | --- | --- | --- | --- |
| New York | fit (one fold) | 17 | 11 | 558.3 | 2,114.8 |
| Philadelphia | fit (one fold) | 83 | 43 | 557.9 | 6,857.5 |
| Charlotte | fit (one fold) | 20 | 18 | 815.7 | 2,870.1 |
| Saint Paul | fit (one fold; its case is context only, 1 before year) | 9 | 7 | 206.2 | 560.3 |
| Chicago | always held out | 95 | 22 | 158.3 | 2,493.8 |
| Madison | always held out | 7 | 5 | 595.8 | 466.6 |
| **All** | | **231** | **106** | **2,892.0** | |

- **Why units were dropped:** 123 of the 125 dropped units had under 5 eligible treatment acres (73 of them Chicago station areas, where the reform touched only small -3 district strips). Two had under 5 comparison acres.
- **What the kept units show** (acre-weighted mean effect, homes permitted per eligible acre per year): New York +0.94 (11 units, 558.3 acres), Philadelphia +0.73 (43 units, 557.9 acres), Charlotte +0.13 (18 units, 815.7 acres), Saint Paul −0.10 (7 units, 206.2 acres), Chicago +0.13 (22 units, 158.3 acres), Madison +0.27 (5 units, 595.8 acres).
- **The spread is wide inside every city.** For example, New York runs from −0.94 (Special Forest Hills) to +13.31 (Downtown Brooklyn), and Madison from −1.27 (northeast of the core) to +11.29 (Isthmus core).
- **These are not the case estimates.** Small units are dropped, and each unit has its own comparison, so the acre-weighted mean of a city's units differs from its case estimate (for example Charlotte +0.13 here, +0.130 in the case; New York +0.94 here, +1.057 for the pooled set).

## Trait sources, written before joining

Written 2026-10-27, after the unit list above was fixed and before any trait value was joined to an effect. Each trait is measured on a unit's treated lots (its eligible treatment land). "Acre-weighted" means each treated lot counts by its acres.

| # | Trait (plan section 4) | Source and how it is measured | Entered as |
| --- | --- | --- | --- |
| 1 | Median home value | American Community Survey (ACS) 5-year, table B25077, by census tract. Each treated lot takes the value of the tract holding its representative point; the unit's value is the acre-weighted mean. Vintage: 2006–2010 (2010 tracts) for every unit outside Madison; 2018–2022 (2020 tracts) for Madison. Dollars are put in 2024 dollars with the CPI-U annual average (BLS series CUUR0000SA0: 2010 = 218.056, 2022 = 292.655, 2024 = 313.689). Files: Census summary files, sequence-based for 2006–2010 and table-based for 2018–2022; tract shapes from TIGER/Line 2010 and 2024. | log |
| 2 | Average lot size of treatment parcels | The case's own lot layer: treated eligible acres ÷ number of treated lots. New York lots are from the MapPLUTO snapshot before each rezoning; the other cities use today's parcel layer (Chicago 2021). | acres per lot |
| 3 | Existing density | Homes before the change ÷ eligible treatment acres. New York: residential units on the lots in the MapPLUTO snapshot before the rezoning. Charlotte, Chicago, Philadelphia, Saint Paul: 2010 census block housing units whose block's internal point lies in a treated lot (the rule the cases use, `cases.homes_by_area`). Madison: dwelling units on today's parcel records, as in the Madison test. | log of (homes per acre + 1) |
| 4 | Median household income | ACS table B19013, as for trait 1. | log |
| 5 | Land area of the city | Census Gazetteer 2024, place land area (ALAND_SQMI), for New York city, Philadelphia city, Charlotte city, St. Paul city, Chicago city and Madison city. One value per city. | log |
| 6 | Median gross rent | ACS table B25064, as for trait 1. | log |
| 7 | Size of the upzoning | Added allowed floor area ratio (FAR) over the unit's treated lots, from the case's own district tables (`cases.dose`): New York, Chicago, Saint Paul (T4, with no FAR limit, left out) and Madison. Charlotte has only added height (feet) and Philadelphia has no dose, so they have no value; see section 8. | added FAR |
| 8 | Building rate before the change | The unit's own treatment rate in its before years, homes permitted per eligible acre per year (from the unit list). | as is |
| 9 | Share of treatment land vacant, parking or industrial | Land-use codes on the treated lots, acre-weighted. New York: MapPLUTO land use 06 (industrial and manufacturing), 10 (parking) and 11 (vacant) in the snapshot before. Charlotte: assessor land use "PARKING", "INDUSTRIAL", "WAREHOUSE" or vacant flag. Chicago: Cook County assessor classes 100, 190, 241 (vacant) and 550–599 (industrial and commercial minor improvements). Philadelphia: Water Department building descriptions starting "VAC", or naming parking, industry or warehouses. Saint Paul: land-use descriptions naming vacant land, parking, industry, manufacturing or warehouses. Madison: parcel use classes vacant, parking and industrial. Outside New York the land use is today's, so lots that received a new-housing permit in the unit's before or after years are left out of the share. | share |
| 10 | Distance to the city's downtown | Straight-line km from the acre-weighted centre of the treated lots to a written-down downtown point: City Hall in New York (Manhattan), Philadelphia, Saint Paul and Chicago; Trade and Tryon in Charlotte; the State Capitol in Madison. | km |
| 11 | Jobs within 30 minutes by transit | Not computable openly for each city before its change (it needs historical transit schedules and a routing run). The published index used instead is the U.S. EPA Smart Location Database v3, field D5BR: jobs within a 45-minute transit trip, weighted by travel time (2017 schedules and 2017 LEHD jobs), by 2010 block group, fetched from EPA's map service. Acre-weighted over treated lots. | jobs |
| 12 | Whether the reform also cut parking minimums | City level, from the case files: New York 0 (minimums kept), Philadelphia 0 (none code-wide), Charlotte 1, Saint Paul 1, Chicago 1 (reduced), Madison 1 (the overlay removed them). | 0 or 1 |

## Answer first

- **One trait passes the pre-set test: whether the reform also cut parking minimums (trait 12).** Units in cities that cut parking minimums (Charlotte, Saint Paul) had *smaller* effects than units in cities that kept them (New York, Philadelphia).
- **It is a weak pass, and should not be read as "parking cuts lower the response".**
  - It is a city-level 0/1 trait. With four fitting cities it can only tell "New York and Philadelphia" apart from "Charlotte and Saint Paul". Any difference between those two pairs (market, decade, building type, data) would look the same.
  - It lowers the held-out error in exactly 2 of the 4 fold cities (Charlotte and Saint Paul) and raises it in the other 2.
  - It does not survive dropping Saint Paul, whose case is context only (1 before year): then it fails, and the vacant/parking/industrial share passes instead. That check is not part of the pre-set rule; it is shown so the pass is not over-read.
- **Three traits are near-misses** (better in one held-out city only): lot size, size of the upzoning (added FAR) and distance to downtown. **Eight fail**, including the market traits (rent, home value, income).
- **Chicago and Madison:** no trait predicts both well. The parking trait predicts Chicago better than the baseline does and Madison about as well.
- **For Wisconsin:** the result does not narrow the range (171 to 17,148 extra homes over 2027–2031). It is shown as a sensitivity only.

## Held-out test (plan section 5)

**Setup.**
- **Fitting units:** 79 units in New York (11), Philadelphia (43), Charlotte (18) and Saint Paul (7).
- **Always predicted, never fitted:** 27 units in Chicago (22) and Madison (5).
- **Baseline:** the acre-weighted mean effect of the fitting units, with no trait.
- **Error:** acre-weighted mean absolute error, in extra homes permitted per eligible acre per year. For a fold city, the model is fitted on the other three cities. "Mean" is the simple mean of the four fold cities' errors.
- **Pass rule:** lower mean error than the baseline, and lower error in at least half of the fold cities (and in more than one). Lower in exactly one fold city = near-miss.

**Results, one trait at a time.** Errors in extra homes permitted per eligible acre per year. "Cities better" = fold cities (of 4) where the trait's error is below the baseline's.

| # | Trait | Verdict | Cities better | Mean error, baseline | Mean error, with trait | Error in Chicago, baseline → with trait | Error in Madison, baseline → with trait |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Median home value (log) | fail | 2 of 4 | 0.875 | 0.889 | 0.581 → 0.656 | 1.475 → 1.407 |
| 2 | Average lot size | near-miss | 1 of 4 (Charlotte) | 0.875 | 0.886 | 0.581 → 0.643 | 1.475 → 1.502 |
| 3 | Existing density (log) | fail | 2 of 4 | 0.875 | 0.904 | 0.581 → 0.586 | 1.475 → 1.423 |
| 4 | Median household income (log) | fail | 2 of 4 | 0.875 | 0.883 | 0.581 → 0.547 | 1.475 → 1.627 |
| 5 | City land area (log) | fail | 2 of 4 | 0.875 | 1.048 | 0.581 → 0.588 | 1.475 → 1.472 |
| 6 | Median gross rent (log) | fail | 2 of 4 | 0.875 | 0.905 | 0.581 → 0.567 | 1.475 → 1.448 |
| 7 | Added FAR (45 units with a FAR dose; 2 fold cities) | near-miss | 1 of 2 (Saint Paul) | 1.074 | 1.017 | 0.696 → 1.262 | 1.519 → 1.728 |
| 8 | Building rate before | fail | 0 of 4 | 0.875 | 1.002 | 0.581 → 0.586 | 1.475 → 1.476 |
| 9 | Vacant, parking or industrial share | fail | 2 of 4 | 0.875 | 0.889 | 0.580 → 1.163 | 1.474 → 1.525 |
| 10 | Distance to downtown | near-miss | 1 of 4 (Charlotte) | 0.875 | 1.051 | 0.581 → 0.657 | 1.475 → 1.634 |
| 11 | Transit jobs access (EPA D5BR) | fail | 3 of 4 | 0.877 | 1.226 | 0.582 → 0.637 | 1.475 → 1.458 |
| 12 | Parking minimums also cut | **pass** | 2 of 4 (Charlotte, Saint Paul) | 0.875 | 0.832 | 0.582 → 0.386 | 1.475 → 1.467 |

- **Traits 1, 3–6, 9 and 11 help in some cities and hurt badly in others.** For example, transit jobs access lowers Charlotte's error from 0.691 to 0.255 but raises New York's from 1.174 to 3.224: New York's access values are far beyond anything the other cities show, so the fitted line breaks there.
- **Rent, the market trait the cases flagged** (CASE_ANALYSIS_PLAN section 5), fails: it helps Charlotte and Saint Paul but makes New York's error rise from 1.174 to 1.866.
- **Added FAR** can only be tested in two fold cities (New York and Saint Paul), each fitted on the other alone. It predicts negative effects for Chicago (−1.05) and Madison (−0.20) against measured +0.13 and +0.27. Its slope on all fitting units is positive (+1.76 per added FAR), as expected, but it does not travel.
- **Two-trait models:** only one trait passed, so there is no pair to test.
- Per-city errors for every model are in [reference/tod_trait_errors.csv](../../reference/tod_trait_errors.csv).

## Chicago and Madison (always predicted)

Acre-weighted means over each city's kept units, extra homes permitted per eligible acre per year.

| | Chicago (22 units, 158.3 acres) | Madison (5 units, 595.8 acres) |
| --- | --- | --- |
| Measured | +0.134 | +0.268 |
| Baseline prediction (mean of the 79 fitting units) | +0.477 | +0.477 |
| Parking-cut trait prediction | +0.083 | +0.083 |
| Error, baseline → parking trait | 0.582 → 0.386 | 1.475 → 1.467 |

- **Chicago:** the parking trait’s prediction (+0.08) is closer to the measured mean (+0.13) than the baseline's (+0.48).
- **Madison:** both predictions are about as far off unit by unit (errors 1.475 and 1.467), because Madison's segments range from −1.27 (northeast) to +11.29 (Isthmus core). The parking trait's mean (+0.08) is below the measured mean (+0.27); the baseline's (+0.48) is above it.
- Unit-by-unit predictions for every model are in [reference/tod_trait_heldout_units.csv](../../reference/tod_trait_heldout_units.csv).

## What it means for Wisconsin (plan section 6)

- **The sensitivity table** is [reference/tod_trait_wisconsin.csv](../../reference/tod_trait_wisconsin.csv): 90 Wisconsin station areas (city × band, from `reference/tod_station_areas.csv`), 57,533.8 eligible acres.
- **Parking is a property of the law, not of the station area,** so the trait gives every Wisconsin area the same rate. It cannot place or size the response area by area, which is what section 6 hoped a passing trait would do.
- **The two rates,** from the model fitted on the 79 fitting units (90% interval from redrawing units within each city, 2,000 draws):
  - **law without parking cuts** (the current model: parking is left to the parking scenario): +0.84 extra homes permitted per eligible upzoned acre per year (0.29 to 1.61);
  - **law with parking cuts** (Gate 1 benchmark T5): +0.08 (−0.06 to +0.23).
- **These are not a new estimate.** The first is the New York–Philadelphia average and the second the Charlotte–Saint Paul average. The trait cannot separate parking from everything else that differs between those cities, and it fails without Saint Paul.
- **Decision:** the range (171 to 17,148 extra homes, 2027–2031) and the model's main outputs stay as they are. The result can be shown on the "Why" screen as: "Across 106 rezonings and station areas in six cities, no neighbourhood trait (rent, home value, income, density, lot size, vacant land, distance to downtown, transit jobs access, size of the upzoning) predicted where upzoning added homes better than a plain average. The one city-level trait that passed, whether parking minimums were also cut, separates two pairs of cities and does not hold up without Saint Paul."

## Departures

All are in the plan's section 8 with their reasons:
1. How station areas and Madison's segments are cut, and each unit's comparison (item 1).
2. New York has 11 units, not 17, because of the plan's own 5-acre rule (item 2).
3. Saint Paul units are fitted (item 3).
4. The pass rule counts the four fold cities; Chicago and Madison are reported separately (item 4).
5. ACS 2006–2010 (2018–2022 for Madison) in 2024 dollars; New York's are not all before its rezonings (item 5).
6. Density enters as log(homes per acre + 1) (item 6).
7. Added FAR only; Charlotte and Philadelphia have no value (item 7).
8. Density, vacant land, jobs access and land area sources (items 8–11).
9. The near-miss rule is applied before the half-of-cities rule (item 13).

## Limits

- **Small units are noisy.** Many units have a handful of projects; one building moves a unit's rate. Acre weighting limits this but does not remove it. Saint Paul units have 1 before year, so their intervals often collapse to a point.
- **Traits travel together.** Rent, income and home value are correlated, and every city-level trait is confounded with everything else about its city.
- **Before-the-change values** exist only for New York lots (land use, homes). Elsewhere, parcels, land use and the jobs index are later than the change.
- **Data:** EPA's D5BR is missing for 1 Charlotte unit (no transit in its block groups in 2017), and the vacant share for 1 Philadelphia unit whose lots were all built on.
