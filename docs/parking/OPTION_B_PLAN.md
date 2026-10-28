# Parking: option B, a narrower range, plan

Written 2026-10-28 by the parking conductor. Ryan said the current range (0 to 12,695 extra homes permitted, 2027–2031) is "the least helpful prediction possible" and asked to "try out B". The block-catalog and placebo numbers this plan uses were already known when it was written, so this is not a blind plan. The rules are fixed here before the Wisconsin total is computed. Nothing in the tool changes until Ryan approves.

## Idea

Split Wisconsin into two parts and set the high end for each from the evidence that fits it.

| Part of Wisconsin | Evidence | High end |
| --- | --- | --- |
| Homes away from major transit stops | 76 citywide repeals, with the placebo test used to remove the method's lean toward growth | 0, if the bias-checked upper bound is below zero |
| Homes near major transit stops | Block-by-block area reforms (Seattle urban villages, Minneapolis near rail, Hayward near BART), each measured against its own 2000–2010 trend | Their average gain |

The central case stays 0 everywhere.

## Rules

1. **Away from transit.** The placebo test gives 20,000 averages from cities that never repealed, so it shows how far the method strays when there is no effect. The largest effect still consistent with the real average is real average − 5th percentile of the placebo averages (a 95% one-sided bound). With 76 places this is −1.14 − (−0.79) = −0.35 permits per 1,000 existing homes per year. If it is below zero, this part's high end is 0.
2. **Near transit.** The rate is the home-weighted average of the block catalog's change in change, in homes per 1,000 existing homes per year. Weights are 2010 homes in each reform area. It uses the three cases measured that way: Seattle, Minneapolis and Hayward. Fremont and TOD's per-acre cases are left out. The rate is converted to permits by dividing by 0.86, the ratio of census change to permits found in the census-count check.
3. **Which homes.** Homes within TOD's main definition of near a major transit stop (2020 census, `reference/tod_near_stop_homes_by_muni.csv`), outside the places already at the benchmark. The rate is held flat over 2027–2031.
4. **Sensitivities.**
   - Seattle alone as the near-transit rate.
   - The current method (12,695).
   - The permit-based transit-area group (6 cities, +2.25 per 1,000 citywide homes per year), applied to all homes in Wisconsin places with a major transit stop.

## Caveats

- The near-transit rate comes from 3 areas, and its 90% ranges are wide.
- Those areas also had upzoning or new rail, so the rate is a generous high end for parking alone.
