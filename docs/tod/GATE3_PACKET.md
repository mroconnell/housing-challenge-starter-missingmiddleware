# Transit-oriented density: Gate 3 packet (baseline, response and uncertainty)

Written 2026-10-27 by the TOD conductor, for Ryan. Status: approved (AQ-051), with two amendments from the independent check sent to the owner the same day (section 9).

## 1. The answer

If Wisconsin passed the benchmark TOD law on 1 January 2027, the model expects about **2,509 extra homes permitted over 2027–2031** in the typical scenario. The range runs from about 171 (little) to about 17,148 (strong).

For comparison:
- About **14,464 homes** would be permitted in the same station areas without the law (range 8,386 to 21,874).
- The ADU law's central scenario adds 8,757 second-home permits. That is statewide and a different kind of permit, so it is context, not a like-for-like comparison.

| Scenario (named after the evidence it uses) | Extra homes permitted, 2027–2031 | As a share of the 313,564 homes in the station areas (2020 census) |
| --- | --- | --- |
| Little response, like Los Angeles's transit program | 171 | 0.05% |
| Typical response, like the average loosening reform across 1,136 US cities (Stacy et al. 2023; mostly ADU and lot-size rules) | 2,509 (range 665 to 4,352) | 0.8% |
| Strong response, like Auckland's 2016 upzoning | 17,148 | 5.5% |

**By year:**

| Scenario | 2027 | 2028 | 2029 | 2030 | 2031 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Typical | 245 | 233 | 663 | 1,202 | 166 |
| Strong | 833 | 2,417 | 3,186 | 4,304 | 6,408 |

The typical scenario's 2031 drop comes from the measured New York build-up, which was fixed in advance. A smoothed version (562 homes in 2031) is a sensitivity.

**Where, typical scenario:**
- Milwaukee metro: 1,637 homes. Madison metro: 827. Kenosha County: 45.
- By city: Milwaukee 516, Madison 501, Wauwatosa 293, West Allis 198, Verona 130.

## 2. How the numbers are made

1. **Where the law applies.** Land within ½ mile of streetcar and rapid bus stations, and within ¼ mile of 15-minute bus routes. That holds 313,564 homes (2020 census).
2. **The law.** California SB 79's minimum heights and densities (65 feet near stations; 55 feet further out and along 15-minute buses). No parking change, no affordability mandate.
3. **Baseline.** The shared all-housing baseline (v2, with the Milwaukee correction), split by each city's share of homes near stops: 14,464 homes over 2027–2031.
4. **How big.** Each scenario is a share of the homes in the station areas, taken from a study that measured whole-city net effects after rezoning (AQ-050). The source check is in [NET_EFFECT_SOURCES.md](research/NET_EFFECT_SOURCES.md).
   - **Los Angeles:** 0.04 percentage points of extra stock growth over six years. That is about 0.033% over five years. It is then divided by the program's coverage (about 61% of homes; a figure built from rounded published numbers), giving 0.055%.
   - **Stacy et al.:** +0.8% of postal address counts, 3 or more years after a loosening reform. The interval is about +0.2% to +1.4%. No coverage adjustment, since the study did not measure coverage.
   - **Auckland:** 21,808 extra consents over 2016–2021, 4.1% of its 2016 stock. Divided by 75.2%, the share of residential land upzoned, this gives 5.5%. Land is used as a stand-in for homes, which probably overstates the strong scenario.
5. **Where.** Each area's share follows its eligible acres times the density the law adds. For suburbs whose zoning is not coded, that density is estimated from existing buildings and scaled by 0.719. That is the ratio of coded to estimated capacity measured in Milwaukee and Madison, where the estimate overstated capacity by 41–55%.
6. **When.** Little and typical follow the New York rezonings' measured build-up by year since the change. Strong follows Auckland's own yearly pattern.
7. **Never subtracts.** Places already at or above the law get none of the placement. This affects where homes go, not the statewide total.

**Worked example (Madison city, typical scenario):**
- Madison has 5,840 of the 11,848 added-density acres in the coded cities. With the suburbs scaled in, its share of the statewide total is 20.0% (501 of 2,509).
- Spread over years by the New York build-up, that is 49, 47, 132, 240 and 33 homes in 2027–2031.
- That sits on top of Madison's baseline near stops of 9,220 homes.

**One thing the model has not been able to test in Wisconsin.** The sizing chosen in AQ-050 has no Wisconsin hold-out test of its own. The Madison test checked the per-acre method, which now only decides where homes go. One point in the sizing's favour: Milwaukee (68%) and Madison (63%) have shares of homes near stops close to Los Angeles's 61% coverage. Unlike the modelled law, though, Los Angeles required affordable units.

## 3. Why the method changed during Gate 3

- **The Madison test** ([MADISON_TEST_RESULTS.md](MADISON_TEST_RESULTS.md)). The per-acre method's blind prediction for Madison's 2023 overlay was 0.25 extra homes per acre per year. The measured effect was 0.08, with a 90% interval from −0.17 to +0.31. That passes the rule written in advance, but only weakly. Chicago, the other case never used for fitting, came out just as small.
- **The scale check** ([MODEL.md](MODEL.md), section 10). Spread over all eligible land near stops, per-acre rates gave 14,212 to 151,973 extra homes. Even the smallest would have taken Madison's apartment permitting above its own record. Upzoning a block partly moves building there from nearby blocks rather than adding new homes.
- **The cost-based method could not be computed.** Census rents near stops are below what a new mid-rise building costs. Yet Milwaukee built 2,923 homes in 34 such buildings in 2018–2025.

You chose citywide net-effect sizing on 27 October (AQ-050).

## 4. Checks

- **Madison comparison** (not pre-registered, no pass rule). On the judged basis, Madison's measured extra homes in 2023–2025 were 1.8% of homes on overlay lots, with an interval from −3.7% to +6.8%. On the main estimate they were 1.0%. Over their first three years, the scenarios give 0.02%, 0.36% and 2.05% of station-area homes. Madison's interval includes zero and all three.
- **Scale check.** This is apartment homes permitted (5 or more units) per 1,000 existing homes per year, in the peak year, baseline plus addition.

  | Metro | Little | Typical | Strong | The metro's own record |
  | --- | ---: | ---: | ---: | --- |
  | Milwaukee | 1.87 | 2.90 | 7.68 | 3.44 (2016) |
  | Madison | 13.5 | 14.6 | 19.8 | 16.9 (2021) |

  The highest year any comparable US metro has recorded is Austin's 25.7 (2021); no scenario reaches it. Only the strong scenario beats the metros' own records.
- **Arithmetic.** Areas add up to cities, counties, legislative districts and the state. The baseline matches the shared baseline's split. No addition is negative. 499 tests pass. The independent check reproduced every output byte for byte, and recomputed every total by hand.
- **Order of steps.** Commit history shows the Madison plan (4a6e3b9) came before the spec (df1ad94), then the blind prediction (bf6d347), then the count (9ee72bb). Commit order shows the sequence but cannot by itself prove the prediction was made without knowledge of the outcome.

## 5. Sensitivities, grouped by what they move (2027–2031, extra homes)

**The law's addition:**
- Typical at the ends of Stacy et al.'s interval: 665 to 4,352.
- As published, without the coverage adjustment: little 105, strong 12,895.
- Year 5 smoothed (the mean of years 3–5): same totals; typical 2031 rises to 562.
- Per-acre sizing as first built: 14,212 / 39,767 / 151,973. These fail the scale check.
- Per-acre sizing at the rate measured in Madison and Chicago (0.23 extra homes per acre per year per unit of added floor area ratio): 13,477. Capped at the 95th percentile of comparable metros, it falls to 6,834, all in Milwaukee. Madison gets none under the cap because its baseline alone is already above that level.

**Where homes land:**
- No suburbs: Milwaukee metro 1,272, Madison metro 1,237.
- Unscaled suburbs: Milwaukee metro 1,683, Madison metro 774.
- Stops limited to rail and rapid transit (typical): 716 statewide.
- 20-minute high case: 2,813. All 15-minute stops within ½ mile: 3,226.

**Baseline only:** 8,386 to 21,874; 11,875 with Milwaukee's apartments as the Census published them.

## 6. What the model cannot tell policymakers

- **Whether Wisconsin will behave like the average city in these studies.** Only 28 of Stacy et al.'s 96 loosening reforms changed floor area, density or height.
- **Timing.** The studies measure effects 3 to 9 years out. Much of a TOD law's effect may fall after 2031; the tool will say so (G3-4).
- **TOD alone versus TOD with parking reform.** The cases cannot separate them. The combined view uses the parking scenario's own evidence.
- **Rents, displacement and transit ridership.** These are not modelled.

## 7. Decisions (approved 2026-10-27, AQ-051)

| # | Decision | Outcome |
| --- | --- | --- |
| G3-1 | Three scenarios; the reference line equals typical and is shown dotted | Approved |
| G3-2 | Place additions in suburbs near stops too | Approved; amended after the check to scale the suburbs' estimated capacity by 0.719 (awaiting your confirmation) |
| G3-3 | Final year of the build-up | Approved as smoothing, then reversed after the check: the measured build-up was fixed in advance, so smoothing would be after-the-fact tuning. Smoothing is now a sensitivity (awaiting your confirmation) |
| G3-4 | Tool states the timing caveat | Approved |
| G3-5 | Go to Gate 4 | Approved. Eau Claire has no main-case station areas (no 15-minute routes), so its pilot will show zero additions with the reason. That makes it the "does it transfer" example of a city the law barely touches |

## 8. Owner review steps

1. Read section 1.
2. Open `reference/tod_model_by_area.csv`, filter to the typical scenario, and find Madison city. Check:
   - its baseline near stops, 9,220;
   - its five-year addition, 501;
   - its yearly path.
3. Read section 4 of [MADISON_TEST_RESULTS.md](MADISON_TEST_RESULTS.md).

**Self-assessment.** The numbers reconcile. The spread from little to strong is about a hundredfold. That reflects disagreement among the cases, not noise added by the model.

## 9. Independent check (2026-10-27)

The checker reran every script in a separate copy of the repo and got identical outputs. It recomputed every total by hand and found no arithmetic errors.

**Changes it asked for:**
- **Keep the measured build-up** (G3-3 reversed).
- **Scale the suburbs' placement** (G3-2 amended).
- **Restore the corrected wording** for Stacy et al. and the coverage shares.
- **Label the Madison comparison** as not pre-registered.
- **Replace a meaningless benchmark:** Madison's baseline already exceeds the 95th percentile of comparable metros, so the scale check now compares with each metro's own record.
- **State plainly** that the adopted sizing has no Wisconsin hold-out test.
- **Add** a worked example and the coverage argument.

All are done.

**Its strongest challenge:** the typical scenario rests on a study of mostly ADU and lot-size reforms, not transit upzonings. Los Angeles is the only US transit program with a measured citywide net effect.
