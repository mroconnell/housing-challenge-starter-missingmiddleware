# Salt Lake City's 2010 station-area districts, measured with census block counts: results

Run 2026-10-28 against the plan written before looking ([SLC_CENSUS_PLAN.md](SLC_CENSUS_PLAN.md); changes in its section 8). Code: [scripts/fetch_tod_slc.py](../../scripts/fetch_tod_slc.py), [scripts/run_tod_slc_census.py](../../scripts/run_tod_slc_census.py). Output: `reference/tod_slc_census_results.csv`.

## Summary

- **The district land gained homes, but so did the land around it.**
  - **District land:** 1,269 homes in 2010 and 3,213 in 2020, a net gain of 1,944 homes on about 755 acres. That is 2.58 net homes per acre over the decade.
  - **Nearby land on the same new rail line, outside the district:** 2,541 homes in 2010 and 4,343 in 2020, a net gain of 1,802 homes on about 1,088 acres. That is 1.66 net homes per acre over the decade.
- **Extra gain from the district (main estimate):** 0.92 more net homes per acre over the decade, or 0.09 a year. The 90% interval is −2.15 to +3.97 per acre over the decade (−0.22 to +0.40 a year), so it **includes zero**.
- **In homes:** 0.92 per acre on about 755 acres is about 700 extra homes over 10 years. That is about 0.9% of Salt Lake City's 80,724 homes in 2010, but the interval includes no gain at all.
- **This fits the other cases.** Per acre per year it sits beside Madison's overlay (0.08) and Chicago's ordinances (0.24, held out), far below the New York cases (Park Slope 2.93 per 1.0 of added floor area ratio).
- **Nothing changes.** The finalized TOD numbers (AQ-055) stay at 171, 2,509 and 17,148 extra homes over 2027–2031.

## Results

Net homes added from 2010 to 2020 per acre of land, from census block counts (blocks placed by their internal point).

| Estimate | District land | Comparison land | Difference over the decade (90% interval) | Per year |
| --- | ---: | ---: | --- | ---: |
| **Main:** against nearby land on the same line (within ½ mile, outside the district) | 2.58 | 1.66 | **0.92** (−2.15 to 3.97) | 0.09 |
| Against new stations elsewhere (15 TRAX stations opened 2011–2013 outside Salt Lake City) | 2.58 | 0.60 | 1.98 (−0.39 to 4.77) | 0.20 |
| District "core" zones only | 2.94 | 1.66 | 1.28 (−2.82 to 6.35) | 0.13 |
| Comparison limited to ¼ to ½ mile | 2.58 | 1.85 | 0.73 (−2.45 to 3.91) | 0.07 |
| Largest 2020 block left out of each group | | | 0.55 | 0.06 |

Group sizes (2010 and 2020 blocks): district land 58 and 46; nearby land 113 and 84; new stations elsewhere 466 and 475.

## Reading it

- **Every version points the same way, and none clears zero.** The district land added more homes per acre than any comparison, but by an amount the block-to-block spread cannot separate from chance. Against new stations elsewhere it comes closest (interval −0.39 to 4.77).
- **Much of the district's gain sits in a few blocks.** Leaving out the largest 2020 block in each group cuts the difference from 0.92 to 0.55 per acre over the decade.
- **The nearby comparison land grew fast too**, by 71% in homes over the decade (2,541 to 4,343). Some of that may itself respond to the new line, or to other rezonings near North Temple that we cannot see. If so, the main estimate understates the district's effect.

## Limits

- No before-trend: the 2000 block counts were not used.
- The district boundary comes from a 2020 zoning snapshot. The ordinance's own 2010 map is no longer online.
- The rail line opened in 2013, so the decade mixes the zoning change with the line's arrival. Both groups got the line.
- Census counts are net of demolitions and come only every 10 years, so the timing within the decade is unknown.

## Could it go further?

- **Floor area from the state parcel map** (year built and floor area for every building) could extend the comparison past 2020. It counts floor space, not homes.
- **The same census method could measure other reforms adopted around 2010** that lack permit files (for example in the 58-case inventory). That would widen the case set, with the same limits.
