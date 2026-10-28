# Adding the 2000 census: results

Run 2026-10-28 against [CENSUS2000_PLAN.md](CENSUS2000_PLAN.md). Code: [scripts/run_tod_census2000.py](../../scripts/run_tod_census2000.py). Outputs: `reference/tod_old_city_2006.csv`, `reference/tod_census2000_trends.csv`.

All figures are **net homes per acre over a decade**, upzoned (or capped) land minus comparison land, from census block counts (2000 Summary File 1; 2010 and 2020 block files).

## Summary

- **Old City's 2006 height cap shows no measurable effect.**
  - The capped district kept adding homes: 2,180 in 2000, 3,189 in 2010, 4,399 in 2020.
  - It grew a little faster than the land around it in both decades (+2.20 per acre in 2000–2010, +2.26 in 2010–2020).
  - **Change in change: +0.07 (90% interval −10.2 to +10.4)**, essentially zero.
  - The cap was aimed at one waterfront tower; the residential district under it didn't need the height.
- **Before-trends: 12 of 21 census reforms had a 2000–2010 gap within ±1 net home per acre.** In those places, the upzoned land and its comparison were moving together before the reform.
- **The strongest 2010–2020 results survive the before-trend check.** Their change in change is clearly above zero:
  - Seattle Roosevelt: +28.8 (8.1 to 51.7);
  - New York 161st Street: +43.1 (10.4 to 78.8);
  - Seattle North Beacon Hill and Othello: +17.3 (1.6 to 32.5);
  - Milpitas: +7.1 (1.2 to 13.1);
  - Austin: +6.3 (1.0 to 12.1).
- **Two weaker cases fade:** Chicago and Philadelphia.
  - Chicago's upzoned land was already outbuilding its surroundings in 2000–2010 (+6.6 per acre), so its change in change is −6.3 (−16.5 to +3.7).
  - Philadelphia: +3.9 before, change in change −1.4 (−4.8 to +2.0).
- **Nothing changes.** The TOD numbers (AQ-055) stay at 171, 2,509 and 17,148.

## Before-trends and change in change, every census reform

| Reform (adopted) | 2000–2010 gap (90% interval) | 2010–2020 gap | Change in change (90% interval) |
| --- | --- | ---: | --- |
| New York 090365ZMX (2009)* | −10.08 (−31.5 to 9.2) | 32.99 | **+43.08 (10.4 to 78.8)** |
| Seattle Roosevelt (2012) | −0.87 (−7.0 to 5.3) | 27.91 | **+28.78 (8.1 to 51.7)** |
| Seattle North Beacon Hill and Othello (2012) | −3.46 (−8.1 to 1.5) | 13.85 | **+17.30 (1.6 to 32.5)** |
| Milpitas (2008)* | 0.26 (−1.5 to 2.3) | 7.34 | **+7.08 (1.2 to 13.1)** |
| New York 090303ZMX (2009)* | −2.97 (−15.6 to 9.9) | 3.96 | +6.92 (−14.1 to 29.0) |
| Austin (2006–2009)* | 0.49 (−2.0 to 2.9) | 6.76 | **+6.27 (1.0 to 12.1)** |
| New York 100407ZMX (2010) | 4.87 (−4.7 to 14.6) | 8.82 | +3.95 (−15.0 to 23.6) |
| Jersey City (2010) | −0.42 (−6.7 to 6.1) | 2.65 | +3.07 (−9.5 to 15.0) |
| Bellevue BelRed (2009)* | 0.09 (−1.9 to 2.2) | 2.43 | +2.34 (−1.9 to 7.0) |
| Los Angeles Warner Center (2013) | −0.95 (−6.3 to 4.1) | 1.25 | +2.20 (−6.5 to 12.0) |
| Salt Lake City (2010) | −0.54 (−2.0 to 1.1) | 1.61 | +2.15 (−1.2 to 5.6) |
| New York 080099AZMM (2008)* | 0.74 (−13.6 to 15.9) | 2.58 | +1.84 (−25.0 to 28.7) |
| New York 090104ZMQ (2009)* | −0.58 (−76.5 to 92.2) | 1.05 | +1.63 (−110.6 to 97.2) |
| Tysons (2010) | 0.69 (−1.5 to 2.8) | 1.53 | +0.85 (−3.1 to 4.7) |
| Seattle Mount Baker (2014) | −0.73 (−8.6 to 7.2) | −0.15 | +0.58 (−12.9 to 13.6) |
| New York 090272ZMK (2009)* | −1.31 (−12.4 to 9.0) | −1.15 | +0.16 (−19.1 to 21.4) |
| Saint Paul (2011) | 1.68 (−1.4 to 5.0) | 1.32 | −0.36 (−6.5 to 5.5) |
| Phoenix (2015–2016, 7 acres) | −0.01 (−1.0 to 0.9) | −1.23 | −1.22 (−2.9 to 0.5) |
| Philadelphia (2012) | 3.93 (2.0 to 5.9) | 2.56 | −1.37 (−4.8 to 2.0) |
| Los Angeles Cornfield Arroyo Seco (2013) | 1.64 (−0.7 to 4.5) | 0.09 | −1.55 (−7.6 to 3.8) |
| Chicago (2013–2015) | **6.63 (1.5 to 12.0)** | 0.37 | −6.25 (−16.5 to 3.7) |

\* Adopted before 2010: the 2000–2010 decade is partly after adoption, which leans the change in change toward zero.

## What it adds

- **Placebo stations and before-trends point the same way.** The cases that beat 90% of placebo stations (CENSUS_CASES_RESULTS section 6) are mostly the ones whose gains also hold up against their own past. Chicago and Philadelphia did neither.
- **Chicago's result now looks like land that was already growing,** not a response to the 2013–2015 ordinances. That matches its weak permit result and the ridership test.

## Pasadena and Culver City: single-family caps (plan section 7)

Code: [scripts/run_tod_sf_caps.py](../../scripts/run_tod_sf_caps.py). Output: `reference/tod_sf_caps.csv`.

| Reform | Capped land: homes 2000 / 2010 / 2020 | Comparison: homes 2000 / 2010 / 2020 | 2000–2010 gap | 2010–2020 gap | Change in change (90% interval) |
| --- | --- | --- | ---: | ---: | --- |
| Pasadena, Lower Hastings Ranch (2016), 166 acres | 509 / 511 / 507 | 1,002 / 1,100 / 1,094 | −0.35 | 0.00 | +0.34 (−1.44 to +2.05) |
| Culver City, house-size limits (2015–2016), 1,226 acres | 10,170 / 10,346 / 9,477 | 17,859 / 17,478 / 18,971 | +0.30 | −1.34 | −1.64 (−5.58 to +2.10) |

- **Pasadena: no effect, as expected.** Lower Hastings Ranch had about 510 homes in all three counts. A ban on second storeys doesn't change the number of homes on finished single-family blocks.
- **Culver City: leans negative, but the interval includes zero.**
  - The census count on single-family land fell by 869 homes from 2010 to 2020, while the comparison land gained 1,493.
  - Part of the fall may come from how blocks were drawn in 2020: blocks are placed by centre point, and some 2010 blocks that held apartments next to single-family lots may fall differently in 2020.
  - It is not evidence that the size limit cut homes. It would be worth checking with Culver City's permits if the question matters.
- **Together with Old City,** none of the three tightening reforms from Stacy et al.'s list that could be measured shows a clear loss of homes. Their caps did not bind on the number of homes, which matches the New York pattern.
