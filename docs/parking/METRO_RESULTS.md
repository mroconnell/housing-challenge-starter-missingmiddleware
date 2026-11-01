# Parking: each repeal city against its own metro neighbours, results

Written 2026-11-01 by the parking conductor. Plan: [METRO_PLAN.md](METRO_PLAN.md). Script: `scripts/run_parking_metro.py`. Files: `reference/parking_metro_places.csv` and `reference/parking_metro_summary.csv`.

## Answer

**The regional-market theory is not supported for San Francisco and Minneapolis.** Their metro neighbours did not fall. San Francisco's dip grows slightly against Bay Area neighbours, and Minneapolis's stays about the same. So their drops were specific to those cities, not regional. They are still within the range that random cities show with no reform at all.

## Results

The unit is permits per 1,000 existing homes per year, as a home-weighted average with its 90% resampling range. Rows cover the 61 of 76 repeal places that have at least 5 metro neighbours.

| Comparison | Places | Average | 90% range | Median |
| --- | ---: | ---: | --- | ---: |
| Headline comparison (same 61 places) | 61 | −1.62 | −4.08 to 1.09 | −0.18 |
| Metro neighbours | 61 | −1.35 | −3.05 to 0.67 | 0.20 |
| Metro, without San Francisco | 60 | −0.87 | −2.75 to 1.24 | 0.23 |
| Metro, without San Francisco and Minneapolis | 59 | −0.11 | −1.80 to 1.78 | 0.27 |

**Noise check.** 76 never-reformed places, given the real repeal years, are compared with their own metro neighbours (5 seeds). The averages are 0.19, −2.48, −0.76, −0.56 and −2.40. So an average of −1.35 is what random places with no reform can show.

| City | Its rate before → after | Metro neighbours before → after | Metro effect | Headline effect |
| --- | --- | --- | ---: | ---: |
| San Francisco | 9.49 → 5.26 | 6.44 → 6.43 (51 places) | −4.22 | −3.28 |
| Minneapolis | 16.20 → 9.03 | 11.69 → 13.60 (147 places) | −9.09 | −8.52 |
| St. Paul | 8.41 → 6.96 | 11.69 → 13.60 | −3.37 | −2.22 |
| Austin | 34.30 → 18.98 | 52.26 → 41.82 | −4.89 | −12.33 |
| San Jose | 5.34 → 7.70 | 11.02 → 7.21 | +6.16 | +2.48 |
| Raleigh | 16.54 → 23.97 | 41.42 → 48.25 | +0.60 | +7.04 |
| Buffalo | 1.02 → 1.92 | 3.67 → 2.90 | +1.66 | +0.48 |

**No metro peers (left out):** Anchorage, Roanoke, Mount Pleasant, Branson, Richmond, Eugene, Bend, Springfield, Grants Pass, Ashland, Central Point and Saranac Lake.

## Reading

- **The overall average barely moves** (−1.62 to −1.35 on the same places), and the median turns slightly positive (+0.20).
- **Without San Francisco and Minneapolis, the metro average is about 0** (−0.11).
- **San Francisco and Minneapolis each fell while their metros held or rose.** Their declines were local. Plausible causes are city-specific: San Francisco's costs, approval times and post-2020 downtown slump; Minneapolis's simultaneous 2040 Plan changes. This comparison cannot separate those from parking.
- **Earlier peer ratios** (Oakland 0.27× its pace in 2020–2025) used a later and longer window than San Francisco's 2019 repeal window. Over the repeal window, the Bay Area metro as a whole was flat.
- **Use:** this does not justify narrowing the low line on regional grounds. It does show the negative average rests on two cities' local declines, within the range of random no-reform places.

## Audit count fixes (2026-11-01)

- **Places file: 73 rows (61 with peers, 12 without).** Three of the 76 are not in it, because the metro run uses the standard permit panel:
  - South Bend: its combined city-and-county row is not in the standard panel;
  - Gastonia and Avondale Estates: they are missing permit years in the standard panel, and were added to the 76 through the census route.
- **Why some places have no metro peers:**
  - Richmond, VA: its metro's other permit issuers are mostly Virginia counties. The panel drops county rows, so fewer than 5 places with 1,000+ homes and every year present remain.
  - Eugene and Springfield, OR: their metro has 12 permit-issuing places, 3 with apartment-scale repeals dated before the window ends, and most of the rest under 1,000 homes. Oregon's 2023 state rules are not applied in this run, so they are not the reason.
  - Bend and Anchorage, and the small towns, are the same story: too few qualifying neighbours.
- **The noise draws used 63–70 places,** not 76: draws without 5 qualifying neighbours, or with missing years, drop out.
- **A measured low-line figure:** the metro average, −1.35 × 13,424 homes per 1.0 = about −18,100 Wisconsin homes over 2027–2031. "Without San Francisco and Minneapolis (−0.11)" is a sensitivity only.
