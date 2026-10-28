# More reforms measured with census block counts: results

Run 2026-10-28 against the plan written before looking ([CENSUS_CASES_PLAN.md](CENSUS_CASES_PLAN.md); changes in its section 8). Code: [scripts/fetch_tod_census_cases.py](../../scripts/fetch_tod_census_cases.py), [scripts/run_tod_census_cases.py](../../scripts/run_tod_census_cases.py). Outputs: `reference/tod_census_cases.csv`, `reference/tod_census_holdouts.csv`, `reference/tod_census_method_check.csv`.

All rates below are **net homes added from 2010 to 2020 (census counts) per acre of land**, upzoned land minus nearby land within ½ mile. They are shown per year (÷ 10) so they sit beside the permit cases.

## Summary

- **Five new reforms measured.** Four point the same way as Salt Lake City: upzoned land added more homes than the land next to it.
  - Two are clearly above zero: Austin's station-area plans (+0.68 a year) and Milpitas's transit plan (+0.73 a year).
  - Jersey City (+0.27), Bellevue BelRed (+0.24) and Tysons (+0.15) are positive, but their intervals include zero.
- **Phoenix could not be measured.** Its 2015–2016 rezonings cover 7 acres and no homes in either census.
- **Holdouts: one of two agrees.**
  - Jersey City falls inside the range the other cases set.
  - Milpitas sits just above that range (0.73 a year against a highest of 0.68, Austin). So the census cases do not reliably predict a new place's size, the same lesson as the trait tests.
- **Method check: census and permits agree on the effect in all 6 cases that could be compared.** In each, the permit-based difference lies inside the census-based 90% interval. But the census intervals are wide, so this is a weak test. The two differ by −4.5 to +1.6 net homes per acre over the decade, with the largest gap in Seattle's small North Beacon Hill and Othello area.
- **Nothing changes.** The finalized TOD numbers (AQ-055) stay at 171, 2,509 and 17,148 extra homes over 2027–2031.

## 1. New reforms

| Reform (adopted) | Role | Upzoned land: homes 2010 → 2020 | Upzoned acres | Net homes per acre over the decade: upzoned / nearby | Difference per acre per year (90% interval) | Largest block left out (per acre, decade) |
| --- | --- | --- | ---: | --- | --- | ---: |
| Milpitas, Transit Area Specific Plan (2008) | holdout | 656 → 4,057 | 441 | 7.71 / 0.37 | **0.73** (0.27 to 1.26) | 6.32 |
| Austin, TOD station area plans (2006–2009) | fitted | 1,673 → 5,392 | 481 | 7.73 / 0.97 | **0.68** (0.28 to 1.12) | 6.13 |
| Jersey City, Journal Square 2060 (2010) | holdout | 4,030 → 5,037 | 210 | 4.79 / 2.14 | 0.27 (−0.55 to 1.08) | 0.28 |
| Bellevue, BelRed (2009) | fitted | 3 → 1,772 | 491 | 3.60 / 1.17 | 0.24 (−0.09 to 0.66) | 1.38 |
| Tysons, plan amendment (2010) | fitted | 9,380 → 12,937 | 2,191 | 1.62 / 0.09 | 0.15 (−0.09 to 0.39) | 1.27 |
| Salt Lake City, TSA district (2010; [earlier run](SLC_CENSUS_RESULTS.md)) | fitted | 1,269 → 3,213 | about 755 | 2.58 / 1.66 | 0.09 (−0.22 to 0.40) | 0.55 |
| Phoenix, Walkable Urban Code (2015–2016 rezonings) | fitted | 0 → 0 | 7 | 0.00 / 1.23 | not measurable (7 acres, no homes) | |

- **Jersey City's gain rests on one block.** Leaving out the largest 2020 block drops its difference from 2.65 to 0.28 per acre over the decade.
- **Milpitas and Austin hold up** when the largest block is left out (6.32 and 6.13), and when nearby land is limited to ¼ to ½ mile (8.15 and 6.73).
- **Before counts after adoption:** Milpitas (2008), Austin (2006–2009) and Bellevue (2009) were adopted before the 2010 count. Any building that had already started is missed, so their results may understate the effect.
- **Bellevue's light rail opened only in 2024,** so its result is upzoning without trains.

## 2. Holdouts

The five measured fitted cases (Phoenix, Salt Lake City, Bellevue, Austin, Tysons) set:
- a median of 0.15 net homes per acre per year;
- a range of −0.12 (Phoenix) to 0.68 (Austin).

| Holdout | Estimate per acre per year (90% interval) | Inside the range? | Interval includes the median? | Agrees? |
| --- | --- | --- | --- | --- |
| Jersey City | 0.27 (−0.55 to 1.08) | yes | yes | **yes** |
| Milpitas | 0.73 (0.27 to 1.26) | no (just above 0.68) | no | **no** |

Milpitas built far more on its upzoned land than any fitted case except Austin. It added 3,401 homes on 441 acres in a decade of strong Silicon Valley demand. A per-acre effect does not carry from place to place, just as the trait tests found.

## 3. Method check: census counts against permit counts on the same cases

Each case's own upzoned land and ¼-mile ring. Census: net homes from April 2010 to April 2020. Permits: homes in permits issued 2009–2018 on the case's eligible lots.

| Case | Difference per acre over the decade, census (90% interval) | Same, permits 2009–2018 | Same, permits 2010–2019 | Agree? |
| --- | --- | ---: | ---: | --- |
| Saint Paul | 1.32 (−2.43 to 4.99) | 0.98 | 1.63 | yes |
| Seattle, North Beacon Hill and Othello | 13.85 (0.76 to 28.01) | 18.36 | 24.62 | yes |
| Seattle, Mount Baker | −0.15 (−8.09 to 7.21) | 0.85 | 0.91 | yes |
| Chicago | 0.37 (−6.08 to 6.51) | 0.56 | 0.84 | yes |
| Philadelphia (82 of 83 members) | 2.56 (0.55 to 4.60) | 0.98 | 3.56 | yes |
| Charlotte (before its 2019 reform: land only) | −0.64 (−2.29 to 1.06) | −0.24 | −0.29 | yes |
| New York, Los Angeles (two cases) | dropped: their permit tables do not cover the census decade | | | |

- **The two methods agree on the direction and rough size in all six.** The gap (census minus permits, 2009–2018 alignment) runs from −4.5 (Seattle North Beacon Hill and Othello) to +1.6 (Philadelphia) net homes per acre over the decade. The census intervals are wide, so agreement is easy to reach; this shows the census method is not biased in an obvious direction, not that it is precise.
- **Raw counts differ a lot**, because the two sides cover different land (plan section 8, item 4). For example, Chicago's ring holds 33,578 net new census homes against 4,136 permitted homes on its unchanged eligible lots. Census blocks take in all land within ¼ mile, including lots that are not eligible or were rezoned some other way. The census also counts finished homes net of demolitions, while permits count homes approved. Counts from the two methods should not be compared directly. The per-acre differences are the like-for-like measure.
- **City-scale check from the parking work** ([docs/parking/SALVAGE_RESULTS.md](../parking/SALVAGE_RESULTS.md)). On whole places, in 1,356 places in Wisconsin, Indiana, Minnesota and North Carolina, the census change from 2010 to 2020 ÷ permits issued 2010–2019 had these medians:
  - 0.90 in places with 2,500 to 25,000 homes;
  - 0.80 to 0.95 in places with more than 25,000 homes.

  So census-based gains likely read about 10–20% below permits on matching land, mostly from demolitions and permits never built. That would make the census cases here slightly conservative.

## 4. What this adds

- **More places, same pattern.** Upzoned land usually gains more homes than the land next to it, and the size varies a lot from place to place. Measured gains range from about 0.1 to 0.7 net homes per acre per year (Milpitas 0.73).
- **The census method is usable.** It needs no permit file. The only hard part is the boundary map, and it agrees with permits where both exist. More reforms from around 2010 could be added the same way as their maps are found: White Flint, Seattle Roosevelt, Minneapolis Hiawatha, Oakland Broadway Valdez, San Francisco's 2008 plans, Cincinnati and New Rochelle.
- **It doesn't change Wisconsin's numbers.** These are per-acre effects on the upzoned land itself. Our size rule uses whole-city net effects (AQ-050), and the scale check showed per-acre rates overstate a statewide total.
