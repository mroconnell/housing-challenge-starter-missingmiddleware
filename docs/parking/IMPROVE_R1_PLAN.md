# Parking improvement loop, round 1: data fixes, plan written before running

Written 2026-10-31 by the parking conductor, under Ryan's standing ask: improve the data and coding, rerun the simplest model, check flags, and repeat. The simplest model is the current one. Each repeal place is compared with similar places before and after, and the places are averaged with home weights. No result for the variants below has been computed before this file was committed.

## Problems found in the data (checked before this plan)

1. **Estimated permit months.** In the Census permit place files, a place-year with fewer than 12 months reported is partly estimated by the Census Bureau. 33 of the 76 repeal places have at least one such year in their before or after window. All 8 of Buffalo's window years are estimated.
2. **Partly reformed comparison places.** Comparison pools leave out places with a citywide removal at or near the benchmark. They keep places with weaker housing parking reforms in the Parking Reform Network data (4,648 entries), so some comparison places were partly treated.
3. **Traits from after the repeal.** Matching population and the homes denominator come from ACS 2020–2024, after most repeals (audit 2e).

## Variants, each against the current result (−1.14 permits per 1,000 existing homes per year, 76 places)

| Variant | Change |
| --- | --- |
| V1 reported months only | The permit count is the reported-only column (`units_total_rep`) instead of the Census estimate. |
| V2 drop estimated places | Repeal places with any estimated year in their window are left out. |
| V3 clean comparison pools | Any place with a Parking Reform Network housing entry (any rating) is left out of every comparison pool. |
| V4 pre-repeal traits | Homes = ACS 2020–2024 homes minus permits issued from the repeal year to 2024. Matching population is scaled by the same ratio. |
| V5 all fixes | V1 + V3 + V4. |

## Reported for each

- the home-weighted average and its 90% range from 2,000 resamples;
- the equal-weight average and the median;
- the number of places;
- the change from the current result;
- flags: places whose comparison pool is under 5; values outside unit ranges; and the place that moves most between the current result and V5, traced.

## Use

- If V5 differs from the current result by more than its own resampling noise, the placebo test is rerun on V5 and the high end is recomputed. Both go to Ryan as a proposal.
- Otherwise the current numbers stand, and V5's data checks become the standard.

## Changes after writing
- **2026-10-31, after the first run:** with clean comparison pools (V3, V5), Minneapolis and Austin had no comparison places, and 7 other big cities had fewer than 5. Dropping them would bias the average, because both have large negative effects. For V3 and V5 only, a place with fewer than 5 comparison places now also draws from the whole country at ½–2× population, as the placebo fix does. V3 and V5 are rerun; the first-run figures are kept in the results.
- **2026-10-31, audit round 1 asks (before these were computed):**
  - V1b: reported permits scaled by 12 ÷ months reported, with the Census estimate where no month was reported.
  - V3b: date-aware clean pools. A comparison place is left out only if its housing parking entry is undated or dated on or before the end of the case's after-window. National fallback as in V3.
  - V6 = V1b + V3b + V4. South Bend is not in any variant: its combined county row is not in the standard panel, so the scaling question does not arise here.
  - Extra lines for V0 and V6: without the 4 heaviest places (San Francisco, Austin, San Jose, Raleigh), and places with 3 after-years only.
  - Comparison pool sizes are reported for each variant.
  - The 90% resampling range is labelled separately from the placebo range.
- **2026-10-31, audit round 1 review (registered before computing):** two more lines for V0 and V6.
  - Places with fewer than 5 comparison places are dropped.
  - Pool-shrunk weights: homes × after-years × pool ÷ (pool + 5), so places with small comparison pools count less.
  - The comparison-pool label (state, division or nation, with its population window) is saved for each place-variant.
  - The placebo already draws stand-ins only from places with a computable effect: stand-ins with an empty pool, such as Nashville, are dropped before the sets are drawn.
- **2026-10-31, audit round 1 section E (registered before running):** V6u is the same as V6, except that undated Parking Reform Network housing entries (88% of them) do not remove a place from comparison pools. Dated entries stay date-aware, and repeals at or near the benchmark stay excluded. The rule, fixed now:
  - If every real place has at least 20 placebo stand-ins in V6u, V6u's placebo high end replaces 19,937, whatever it is (Ryan has the final call).
  - If not, 19,937 stays, and 49,700 and 38,300 are shown as sensitivity cases with a note that the high end is uncertain by about 2×.
