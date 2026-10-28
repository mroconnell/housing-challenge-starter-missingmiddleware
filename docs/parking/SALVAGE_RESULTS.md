# Parking: rescuing dropped places, results

Written 2026-10-28 by the parking conductor. Plan: [SALVAGE_PLAN.md](SALVAGE_PLAN.md), committed before any of these results were computed. Scripts: `scripts/run_parking_salvage.py`, `scripts/fetch_parking_census_check.py`, `scripts/run_parking_census_check.py`. Outputs: `reference/parking_salvage_effects.csv`, `reference/parking_salvage_estimates.csv`, `reference/parking_census_check_places.csv`, `reference/parking_census_check_summary.csv`.

## Answer

- **Rescued:** three places, South Bend, Gastonia and Avondale Estates. With them the comparison has 74 places, and the average barely moves: −1.14 permits per 1,000 existing homes per year, against −1.10 for the 71.
- **Census counts are no substitute for permits in small towns.** In towns under 2,500 homes, the census change was a median of 27% of the permits issued. So the five dropped 2008–2013 repeals stay out, as the plan's rule requires.

## Places

All rates are permits per 1,000 existing homes per year.

| Place | What was wrong | Fix | Years used | Effect |
| --- | --- | --- | --- | ---: |
| South Bend, Indiana (repealed 2021) | No row of its own in the Census permit files | Its permits are in the "St. Joseph County Unincorporated Area" row: one building department serves the city and the unincorporated county, and the row's ZIP code is 46601, downtown South Bend. Measured as the combined area, then scaled to the city by its share of the area's homes (52.1%). | before 2016–2020, after 2022–2024 | −6.16 (combined area −3.21) |
| Gastonia, North Carolina (2021) | 0 months reported in 2023; no rows after | After-years cut at the first missing year | before 2016–2020, after 2022 | +8.00 |
| Avondale Estates, Georgia (2021) | Before-years 2012–2016 missing | Before-years trimmed to the unbroken run | before 2017–2020, after 2022–2024 | −0.73 |
| Calumet, Michigan (2022) | No permit rows after 2015 | None possible | — | stays out |
| Algoma, Wisconsin | No repeal date | Searched the city code on Municode, the city's ordinance list, council minutes from 2018 and local news. Today's zoning code, adopted in a 2020 recodification (Ord. 824-2020), has no per-home parking schedule. Neither did the code before it (Chapter 18, §18.07, whose parts carry over one for one). No ordinance removing minimums was found. Algoma probably never had residential minimums, which makes it a "no event" place. | — | stays out |

## Estimates

| Case | Places | Average | 90% range from resampling |
| --- | ---: | ---: | --- |
| Expanded 71 places (in the tool now) | 71 | −1.10 | −3.50 to +1.54 |
| 71 plus rescued places | 74 | −1.14 | −3.57 to +1.33 |
| 71 plus rescued, South Bend not scaled | 74 | −1.10 | −3.52 to +1.39 |

The tool's high end comes from the placebo test's spread centred on the real average. Applying the same spread (+2.07) to the 74-place average gives +0.92 permits per 1,000 existing homes per year, about 12,393 permits over 2027–2031, against 12,947 now. The placebo test itself was not rerun for 74 places.

## The census-count check

Cities, villages and boroughs in Wisconsin, Indiana, Minnesota and North Carolina with all 10 permit years and at least 100 homes in 2010. Both censuses' blocks were placed in 2020 boundaries.

| Size in 2010 | Places | Correlation, counts | Correlation, per 1,000 homes | Median of census change ÷ permits | Census change ÷ permits, all places summed |
| --- | ---: | ---: | ---: | ---: | ---: |
| All | 1,356 | 0.98 | 0.88 | 0.60 | 0.86 |
| Under 2,500 homes | 974 | 0.96 | 0.86 | 0.27 | 0.63 |
| 2,500–25,000 homes | 342 | 0.95 | 0.92 | 0.90 | 0.91 |
| Over 25,000 homes | 40 | 0.98 | 0.95 | 0.80 | 0.86 |

Permits are for 2010–2019. Shifting them a year earlier (2009–2018) changes little: the median ratio for all places is 0.64.

**Reading.**
- **Places of 2,500 homes or more:** the census change tracks permits well. It runs about 10–20% below them, which fits demolitions and permits never built. TOD's Salt Lake City method is sound at that scale.
- **Small towns:** many lose homes between censuses that permits never record, through demolitions, mobile homes removed, and vacant homes lost. All five dropped 2008–2013 repeal towns lost homes between 2010 and 2020 (Cowpens −16, Eastover −56, Philip −51, Laceyville −12, Meshoppen −50), while issuing 0 to 8 permits each.
- **Rule outcome:** the plan required a median ratio between 0.7 and 1.1. Overall it is 0.60, so the five towns are not added.
