# Parking: census-only route, results

Written 2026-10-28 by the parking conductor. Plan: [CENSUS_ROUTE_PLAN.md](CENSUS_ROUTE_PLAN.md), committed before counting. Script: `scripts/run_parking_census_route.py`. Outputs: `reference/parking_census_route_places.csv` (2010 and 2020 homes and population for every 2020 place in 17 states), `reference/parking_census_route_cases.csv`, `reference/parking_census_route_results.csv`.

## Answer

**The census route does not give a clearer story. It gives a noisier one, and it does not point to more homes.**
- Repeal places grew slower over 2010–2020 than similar places in their states.
- The placebo test shows that this is ordinary: never-repealed places given the same exposures land on both sides of the real result.
- The main reason is timing. Most repeals came in 2020 or later, so for the places the census can see, the repeal covered only about a fifth of the decade on average. Pro-rating divides the whole decade's difference by that small share, which multiplies the noise about five times.

## Results

All figures are homes added per 1,000 existing homes per year. δ is the estimated effect for each year of repeal: the decade difference against comparison places, divided by the share of the decade under repeal, pooled across places and weighted by homes.

| Group | Places | Share of decade under repeal (weighted) | δ | Resampling 90% range | Placebo 5th / 50th / 95th | Share of placebos at or below |
| --- | ---: | ---: | ---: | --- | --- | ---: |
| Main: 2,500+ homes in 2010 | 7 | 0.19 | −15.4 | −27.0 to −12.2 | −22.2 / −1.1 / +29.8 | 17% |
| Small places (under 2,500 homes) | 13 | 0.81 | −5.7 | −10.3 to −1.2 | −7.7 / −2.4 / +13.6 | 17% |
| All sizes | 20 | 0.22 | −10.2 | −13.7 to −6.2 | −11.6 / −1.3 / +16.5 | 10% |

The main group's places are Hartford, Dunwoody, Mount Pleasant, Branson, Bastrop, Hudson and Saranac Lake. Under the plan, the resampling range alone is misleading here: with 7 places and small exposures it is very narrow. The placebo distribution is the fairer test, and the real result sits at its 17th percentile.

**Not included:**
- San Francisco and Buffalo: each has only 3 same-state places of ½–2× its population, against a minimum of 5.
- Windham, Maine: a town (a county subdivision), not a census place.

## Census route and permit route, side by side

For the places measured both ways, in per 1,000 existing homes per year:

| Place | Share of decade under repeal | Census: decade difference vs comparison | Permit route: effect after repeal |
| --- | ---: | ---: | ---: |
| Hartford | 0.23 | −2.85 | −0.25 |
| Dunwoody | 0.08 | −4.65 | +2.07 |
| Mount Pleasant | 0.21 | −2.85 | −1.41 |
| Branson | 0.20 | −5.31 | +3.16 |
| Bastrop | 0.04 | +23.23 | +30.65 |
| Seabrook | 0.08 | −1.83 | −1.92 |
| Hudson | 0.08 | −0.12 | −1.54 |
| Saranac Lake | 0.38 | −7.85 | −0.31 |

Most of the census difference was already there before the repeal. Branson and Dunwoody grew slower than their comparison places across the decade, yet their permits rose after the repeal. The census cannot tell before from after inside a decade. The permit route can.

## Seattle, block by block (section 5 of the plan)

Seattle's 2012 urban villages against the rest of the city, using 2010 and 2020 census blocks in today's village boundaries:
- **Villages:** 60,039 homes in 2010, 79,486 in 2020, so +32.4 per 1,000 homes per year.
- **Rest of the city:** 181,603 homes in 2010, 190,228 in 2020, so +4.7.
- **Difference:** +27.6 a year. The repeal covered 0.76 of the decade, so δ = +36.4.

This agrees with the permit route (+24.0 in 2013–2015) and carries the same caveat: the villages were already the city's growth areas, and 2000 block counts are not available to show their earlier trend.

## What it means

- **Where it helps:** the census route works when the repeal covers most of the decade and the place is large. That describes Seattle and TOD's Salt Lake City, not the citywide repeals, most of which came after 2020.
- **What would make it stronger:** a pre-reform decade. Census 2000 block counts come from a different source (Summary File 1), not the TIGER files used here. With them, a 2000–2010 vs 2010–2020 comparison would separate old trends from the repeal.
- **When it can be repeated:** the 2030 census will cover the 2020–2024 repeals, which are most of the 76 places.

The scenario does not change.
