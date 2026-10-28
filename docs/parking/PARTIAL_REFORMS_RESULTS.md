# Parking: older and partial reforms, 1998–2020, results

Written 2026-10-28 by the parking conductor. Plan: [PARTIAL_REFORMS_PLAN.md](PARTIAL_REFORMS_PLAN.md), committed before counting. Checks: `reference/parking_partial_checks.csv`. Script: `scripts/run_parking_partial.py`. Outputs: `reference/parking_partial_effects.csv`, `reference/parking_partial_estimates.csv`.

## Answer

- **Transit-area and district reforms lean positive, but the evidence is weak.** Across 6 cities, permits rose by +2.25 per 1,000 existing homes per year more than in comparison places (90% range −1.55 to +4.03). Each city's figure is diluted, since only part of the city was covered, and two of the large cities have very few comparison places.
- **Two more citywide repeals were found,** Maumee, Ohio (2020) and Saranac Lake, New York (2016). Both came out slightly negative. Adding them to the main comparison leaves the average at −1.14.

## Screening

Of 74 candidates (24 dated, 50 undated), most failed on the network's own summary:
- accessory dwelling units only (most of the California entries, which follow state ADU law);
- downtown or business district only;
- optional reductions: fee-in-lieu, EV chargers, land banking, travel-demand plans;
- affordable housing only.

The dates and coverage of those that passed were then looked up:

| Result | Places |
| --- | --- |
| Used: transit-area or district | Chicago (2015), San Diego (2019), Albuquerque (2018), Fremont (2015), Hayward (2011), Penndel (2020) |
| Used: citywide at the benchmark | Maumee (2020), Saranac Lake (2016) |
| Out: date or repeal not confirmed | Dover, NH (a 2026 city mailing shows minimums still apply); Thompson, CT; Gilman, WI ("since at least 2011", no repeal event); Newark, NJ; Atlanta |
| Out: no permit row of its own | Charlotte: its permits are filed under the Mecklenburg County row, as South Bend's are under St. Joseph County. Not rescued, because its reform covered only TOD districts, so a combined county area would dilute it twice. |
| Out: measured elsewhere | Seattle (OLDER_REFORMS_RESULTS.md), Salt Lake City (TOD) |
| Not resolved in this pass | Houston, Miami, Omaha, Cleveland, Stockton, Providence, Jersey City |

## Effects

All rates are permits per 1,000 existing homes per year. Each is the place's change from before to after, minus the change in its comparison places.

| Place | Reform | Before → after | Comparison places | Effect |
| --- | --- | --- | --- | ---: |
| Chicago | TOD ordinance, 2015 | 2012–14 → 2016–18 | 1 (Pacific–Midwest division, ⅓–3× size) | +3.38 |
| San Diego | Transit Priority Areas, 2019 | 2014–18 → 2020–22 | 3 | +2.11 |
| Albuquerque | Integrated Development Ordinance, 2018 | 2013–17 → 2019–21 | 5 | −6.00 |
| Fremont | Warm Springs plan, 2015 | 2012–14 → 2016–18 | 46 | +12.52 |
| Hayward | South Hayward BART code, 2011 | 2007–10 → 2012–14 | 89 | +0.97 |
| Penndel | TOD overlay, 2020 | 2015–19 → 2021–23 | 893 | +1.19 |
| **Group, weighted by homes × after-years** | | | | **+2.25 (−1.55 to +4.03)** |
| Maumee | Citywide, 2020 | 2015–19 → 2021–23 | 147 | −1.01 |
| Saranac Lake | Citywide, 2016 | 2012–15 → 2017–19 | 476 | −0.31 |
| **Main comparison with these two added** (76 places) | | | | **−1.14 (−3.47 to +1.43)** |

Homes come from the 2010 census for Hayward and from ACS 2020–2024 for the others.

**Reading.**
- **Chicago and San Diego:** they carry most of the weight but have only 1 and 3 comparison places, because few US cities are their size. Their figures are fragile.
- **Fremont:** its Warm Springs BART station opened in 2017, alongside a large jobs boom nearby. The +12.5 cannot be credited to parking.
- **The group leans positive, as Seattle and Portland did.** That fits the view that minimums matter most near good transit. The 90% range still includes zero.
- **Maumee and Saranac Lake behave like the other citywide repeals.** Adding them would barely change the tool: the average stays at −1.14.

## Changes from the plan

- **Charlotte:** dropped because its permits sit in a combined county row (see above). Found while running, before its effect was computed.
