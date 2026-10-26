# Parking scenario: Gate 3 packet (baseline, response, uncertainty)

Written 2026-10-26 by the parking conductor, for Ryan. Status: ready for review. It builds on AQ-046 and AQ-048 (Gates 1 and 2, approved "yes to all for now").

## 1. What this gate decides, and the answer

Gate 3 fixes the numbers the tool will show: the current-law baseline, the addition from the law, the range, and what moves them.

**If Wisconsin removed parking minimums for all housing on 1 January 2027:**

| Case (labelled by meaning) | Additional permits, 2027–2031 | What it means |
| --- | ---: | --- |
| **No measurable change** (central) | 0 | Like the 24 US places that repealed. In the three years after, their permit rate changed by 1.18 per 1,000 existing homes per year less than at similar places (likely range −3.57 to +2.21), which is not a measurable change. A repeal is assumed never to subtract, so this counts as 0. |
| **High end of the evidence** (upper) | 29,662 | If the true average effect is at the top of its likely range (the 95th percentile): +2.21 permits per 1,000 existing homes per year, applied to the 2,684,793 Wisconsin homes outside places already at the benchmark. |
| Median repeal place (reference) | 0 | The median repeal place changed by −0.50 permits per 1,000 homes per year against its comparison places. A repeal never subtracts, so this counts as 0. |

**Baseline (current law):** 122,619 permits over 2027–2031, with a range of 64,491 to 175,628 ([HOUSING_BASELINE.md](../shared/HOUSING_BASELINE.md), version 2 with the Milwaukee apartment fix). The upper case adds 24% to the central baseline (29,662 of 122,619).

Sources: `reference/parking_model_statewide_by_year.csv` and `reference/parking_model_by_area.csv`.

## 2. How the numbers are made

- **Baseline:** Census permits by municipality and building size; the flat 2023–2025 average, chosen by a held-out-year test; Milwaukee's apartments taken from the city's property file (AQ-048).
- **Addition:** the before/after comparison of 24 US repeal places against similar places ([COMPARISON_RESULTS.md](COMPARISON_RESULTS.md)). The central is the finding (no measurable change). The upper is the 95th percentile of the average from 2,000 resamples of the places.
- **Where:** the upper case is spread in proportion to existing homes. The 10 Wisconsin municipality pieces already at the benchmark get 0, because a statewide law adds nothing there. That covers 9 places, one of which (Brodhead) has two pieces; they are listed in `reference/parking_wi_benchmark_places.csv`.
- **Timing:**
  - The effect by year since repeal does not build up. Weighted by homes, it is +0.02, −1.29 and −2.26 permits per 1,000 homes per year in years 1, 2 and 3, across all 24 places.
  - In years 4 and 5 it is −6.50 and −6.12. Only 15 and 8 places reach those years, which were mostly 2022–2025. Weighted by homes, San Francisco is 41% of year 4 and 79% of year 5, but the unweighted medians are also negative (−5.95 and −5.06). Source: `reference/parking_comparison_event_path.csv`.
  - This path was computed after Gate 2. It was not pre-registered, and it is not used to change any number.
  - So there is no measured ramp to apply. The upper case is held flat for 2027–2031, which G2-2 labelled an assumption. The path suggests it is generous, not cautious.

## 3. Where the upper case would land (2027–2031)

The upper case follows homes, so it is largest where most people live:

| Counties | Upper-case permits |
| --- | ---: |
| Milwaukee County | 4,219 |
| Dane County | 2,669 |
| Waukesha County | 1,940 |
| Brown County | 1,276 |
| Racine County | 946 |

| Municipalities | Upper-case permits |
| --- | ---: |
| Milwaukee | 2,863 |
| Madison | 1,475 |
| Green Bay | 505 |
| Kenosha | 470 |
| Racine | 385 |

Towns hold 9,034 of the 29,662 upper-case permits (30%), villages 5,146 and cities 15,483. The county and district files carry the baseline by place, which sums to 122,711. The statewide 122,619 also includes the −92 "unallocated" row that reconciles to the state total. Files: `reference/parking_model_by_county.csv`, `reference/parking_model_by_assembly_district.csv` and `reference/parking_model_by_senate_district.csv`. Districts use the ADU tool's crosswalk, which splits places by detached homes. That is an approximation for apartments.

## 4. How sure: sensitivities grouped by what they move

Five-year totals, 2027–2031 (`reference/parking_model_sensitivities.csv`).

| Moves | Case | Additional permits |
| --- | --- | ---: |
| The addition | Upper case, all units (headline) | 29,662 |
| The addition | Units in buildings of 2 or more units only, at the high end of their range (+1.06 per 1,000 existing homes per year) | 14,237 |
| The addition | Leaving out San Francisco, a quarter of the weight (+3.11) | 41,771 |
| The addition and where it lands | Size-and-metro model, its own central prediction for each place, floored at 0 | 32,135 |
| The addition and where it lands | Upper case with towns at 0, for the case where most towns have few or no minimums today | 20,629 |
| The addition and where it lands | Upper case with the 9 places that nearly meet the benchmark also at 0 | 29,484 |
| The baseline only | Census as published for Milwaukee (no apartment fix) | baseline 118,822 |

**About the size-and-metro model.** It predicts positive effects for small places in metro areas and none for large cities. That is why its total (32,135) sits above the upper case. It predicted held-out places only 5% better than one average, and its terms are not distinguishable from zero, so it stays a sensitivity case. Most Wisconsin municipalities (median 929 people) are also smaller than nearly all 24 study places, so it extrapolates there.

**Trace: what rests on data and what on assumption.**
- **Baseline:** observed Census permits. Milwaukee's apartments are estimated from the city's property file, and towns covered by county rows are split by an assumed rule.
- **Central:** estimated from 24 places in other states and Wisconsin (West Allis is one), each checked against its ordinance. The point estimate is −1.18, set to 0.
- **Upper:** a statistical range, from resampling the 24 places.
- **Assumed:**
  - no case below zero. This is a judgment: the 6 places that did not rewrite zoning at the same time averaged −3.54 per 1,000 homes per year, with a range entirely below 0;
  - the out-of-state evidence carries over to Wisconsin;
  - the upper case applies in years 4–5;
  - the upper case is spread evenly across homes.

## 5. Combined view with TOD (draft contract text for SCENARIO_CONTRACT.md)

Owner direction (AQ-047): show parking alone, TOD alone and both together. Proposed text for TOD to review and add to the contract:

> **Combined reforms.**
> - **Additions.** Each reform publishes, in its bundle, `additions_by_area.json`. It gives, for each `area_id` (`muni:<geoid>`) and each forecast year 2027–2031, the additional permits under each of its scenario paths. An optional `part` key (`near_stops` or `elsewhere`) splits a municipality into the area near qualifying transit stops and the rest. TOD acts only near stops. Parking splits each municipality's additions by `share_near_main` in `reference/tod_near_stop_homes_by_muni.csv`.
> - **Same baseline.** Each bundle states its `baseline_version`, currently all-housing baseline v2. The combined builder refuses to combine bundles built on different baselines.
> - **Paths paired by meaning.** Lower is combined with lower, central with central and upper with upper. Paths are never crossed.
> - **Rules.** A combined view is a separate result set, with its own bundle and run id. Neither reform's own numbers change. Within each municipality, the `elsewhere` parts are added. The `near_stops` parts are combined by a rule the owner chooses:
>   - (a) sum, which double-counts any overlap;
>   - (b) the larger of the two;
>   - (c) sum minus an overlap term, measured from cases where both reforms happened together.
>
>   Until the owner chooses, the combined view shows (a) and (b) side by side, labelled. Rule (c) starts as a sensitivity case. The TOD cases give a first handle on it: New York kept parking minimums near transit, while Charlotte, Chicago and Saint Paul cut them. Their markets and decades differ, so (c) is not the main rule.

For parking, the central addition is 0 in every area, so the combined central equals TOD's central under any rule. Only the upper cases differ.

## 6. Owner review steps

1. Read section 1 and check that the labels say what you want a legislator to read.
2. Open `reference/parking_model_by_area.csv` and find a place you know (for example West Allis: at the benchmark, so 0). Check that its eligible homes and upper-case additions make sense.
3. Look at section 4 and decide whether "towns at 0" should be the headline upper case instead of a sensitivity (G3-2).
4. Decide G3-1 to G3-3.

**Self-assessment.** I walked steps 1–3. The statewide totals equal the sum of the places (a test checks this). Every place at the benchmark has 0, and no place is below 0. The event path was computed after Gate 2 and was not part of the pre-registered plan. It is reported, not used to change any number.

## 7. Decisions requested

| # | Decision | Recommendation |
| --- | --- | --- |
| G3-1 | Labels | "No measurable change" for the central and "High end of the evidence" for the upper, with the median place shown as a reference line at 0 |
| G3-2 | Towns in the upper case | Keep towns in the headline, and show "towns at 0" as a sensitivity. We have not checked town and county parking rules statewide, so excluding them would be an assumption |
| G3-3 | Combined view rule | Show the sum and the larger of the two side by side, near stops only (elsewhere is simply added), until there is evidence on overlap; adopt the contract text above, as reviewed by TOD |

## 8. Limitations

- **Central of zero:** it rests on 24 places and three years. A real but small effect, or one that takes longer, cannot be ruled out. The upper case is there for that reason.
- **Spreading:** the upper case is spread by homes, not by where minimums actually bind. The comparison could not tell those places apart.
- **Places already at the benchmark:** taken from the Parking Reform Network list. Their ordinances have not all been checked; West Allis has.
- **Milwaukee's apartments:** the baseline estimate misses condominiums, and the latest year may be incomplete.

## 9. Independent review

Done 2026-10-26. No bug changed a number.
- **Fixed:** the Milwaukee check file now shows Census as published; the upper-case rate is shown to 2 decimals.
- **Wording:** the case descriptions now state the estimate and its range; "apartments" is now "units in buildings of 2 or more units"; the trace says which parts are statistical and which are judgments; the event path is labelled as not pre-registered.
- **Added:** the towns' share, and the fact that the size model extrapolates.
