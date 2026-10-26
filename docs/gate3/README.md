# Gate 3 Packet (final): Baseline, Policy Response, and Uncertainty

Prepared 2026-10-25 by the conductor; numbers updated 2026-10-26. **Status: approved by the owner on 2026-10-25 (AQ-042), then revised on 2026-10-26 by three owner decisions from the Gate 4 review (AQ-043): a new lower scenario, Milwaukee's measured current-law rate, and a reference line across all 8 statewide-law states.** Every number below is the current adopted output. The approved 2026-10-25 numbers are in the section [Revision of 2026-10-26](#revision-of-2026-10-26-aq-043) and in git history. Decisions: AQ-034 to AQ-043 in the [assumptions log](../ASSUMPTIONS_AND_QUESTIONS.md).

**Units.** Every number below is one of two kinds:
- a **count of second-home permits**: ADUs plus single-family-to-duplex conversions on lots that already have a home (AQ-032), summed statewide over the five forecast years 2027–2031;
- a **rate**: second-home permits in a year ÷ thousands of one-unit detached homes, written "permits per 1,000 single-family homes per year".

Wisconsin has 1,839,569 single-family (one-unit detached) homes (ACS 2020–2024, B25024_002). Engine outputs: [`reference/adu_model_statewide.csv`](../../reference/adu_model_statewide.csv), by year in [`adu_model_statewide_by_year.csv`](../../reference/adu_model_statewide_by_year.csv).

## What this gate decides

Whether the statewide model is defensible enough to demonstrate in the Gate 4 pilot. That covers the current-law baseline, the response to a statewide benchmark ADU law, and the scenarios that express uncertainty.

## The answer the model gives

**Baseline.** Under current law, the model expects Wisconsin to permit 605 second homes on single-family lots over 2027–2031 (604.6 permits). That is about 121 permits a year. Divided by 1,839.569 thousand single-family homes, it is 0.066 permits per 1,000 single-family homes per year.

**With a statewide benchmark ADU law**, the model adds:

| Scenario | Info text in the tool | Statewide rate in 2027 → 2030–2031 | Additional permits, 2027–2031 | Total with the 605 baseline |
| --- | --- | --- | ---: | ---: |
| Like the slowest statewide-law states | Like the average of the two slowest statewide-law states, Rhode Island and Oregon. | 0.51 → 0.79 | **5,538** | 6,143 |
| **Like a typical statewide-law state** | Like a typical statewide-law state | 0.77 → 1.19 | **8,757** | 9,361 |
| Strong adoption | The high end of what statewide-law states have reached; only California has gone higher. | 1.45 → 2.22 | **16,889** | 17,494 |
| *Reference line: statewide adoption, all 8 states* | The median path statewide-law states actually reached, California included | 0.75 → 1.29 | **8,851** (2027–2030 observed: 6,594) | 9,456 |

How to read the table:
- **Rates** are the statewide with-law rate: (baseline permits + additional permits in the year) ÷ 1,839.569 thousand single-family homes. For example, the central's 2030 rate is (121 + 2,059 permits) ÷ 1,839.569 thousand homes = 1.19 permits per 1,000 single-family homes per year.
- **The central's additions by year** are 1,299, 1,632, 1,693, 2,059 and 2,074 permits in 2027–2031. They sum to 8,757.
- **Scenarios, not statistical confidence intervals.**
  - **The lower** is the average of the two slowest statewide-law states. Rhode Island's level is 0.62 and Oregon's 0.68 permits per 1,000 single-family homes per year at a typical place with the law in force 4 or more years; their mean is 0.65. That is 0.6497 of the central's common level of 1.0035, so every place's central level is multiplied by 0.6497. Places keep the same differences from one another, and the ramp is recomputed for that level the way the central's is (0.62, 0.79 and 0.82 of the year-4 increment in 2027–2029).
  - **The upper** is the 90th percentile of how much the eight states' levels differ from one another: the central's level multiplied by 1.885.
  - The lower is therefore no longer the mirror image of the upper: it is the central ÷ 1.54 at a typical place, against × 1.885 for the upper.
- **"Strong adoption", stated plainly.** At a typical place with the law in force for 4 or more years, the upper level is 1.89 permits per 1,000 single-family homes per year. The states' own levels at a typical place are, in permits per 1,000 single-family homes per year: California 2.45; Washington 1.19, Utah 1.08, Maine 1.00, Vermont 0.90, Massachusetts 0.85, Oregon 0.68, Rhode Island 0.62 ([`pooled_revision_stage2_levels.csv`](../../reference/pooled_revision_stage2_levels.csv)). Only California is above 1.89.
- **The adoption line** applies to Wisconsin the median observed statewide rate of all 8 statewide-law states in each year since their law, California included. California's rates use the cap and A2 rule with 2020 as year 1; the other seven states' rates are × 0.951 for vacant-lot ADUs.
  - The line's rates are 0.754, 0.931, 0.869 and 1.293 permits per 1,000 single-family homes per year in years 1–4 (2027–2030), the medians of 7, 5, 5 and 4 states.
  - Only California has a year 5, so 2031 repeats the 2030 median and is flagged `carried_forward`.
  - Wisconsin's addition on this line is 1,267, 1,593, 1,477, 2,257 and 2,257 permits in 2027–2031: 8,851 in all, 94 permits (1%) above the central's 8,757. Over the four observed years, 2027–2030, it is 6,594 permits, against the central's 6,683.
  - Sources: [`adu_model_reference_lines.csv`](../../reference/adu_model_reference_lines.csv), by year with the flag in [`adu_model_reference_line_by_year.csv`](../../reference/adu_model_reference_line_by_year.csv), points in [`scenario_options_reference_points.csv`](../../reference/scenario_options_reference_points.csv). The Gate 3 line without California (8,248 permits on the current baseline) is kept there as an alternative row.

**Terms.** Lower, central and Strong adoption are the **scenarios**. A **sensitivity case** changes one assumption and reruns the model; together the cases are the **sensitivity analysis**. A **robustness check** tests a methodological alternative against the hold-out states (below).

**Sensitivity analysis.** Each row is additional permits over 2027–2031. Source: [`reference/adu_model_sensitivities.csv`](../../reference/adu_model_sensitivities.csv), which also has a plain-language `description` of each case and a `moves` column naming the number the case changes:
- **statewide addition**: the permits the law adds statewide;
- **baseline only**: only the current-law rate changes. The rate with the law does not depend on current rules, so the addition moves the other way by about as much, and the total with the law barely moves;
- **local distribution only**: where permits land, with the statewide addition unchanged. No current case is of this kind.

The [tornado chart](sensitivity_tornado.png) shows each statewide-addition case's change from the central of 8,757 permits, sorted by size.

*Cases that change the statewide addition* (the adopted values are lower 5,538, central 8,757 and upper 16,889 on the 605-permit baseline):

| Sensitivity case | Lower | Central | Upper | What it shows |
| --- | ---: | ---: | ---: | --- |
| Lower as a statistical 10th percentile (the Gate 3 lower: every central level ÷ 1.885) | 4,443 | 8,757 | 16,889 | The lower before AQ-043. Its level, 0.53 permits per 1,000 single-family homes per year at a typical place, is below every statewide-law state's. Only the lower changes (−1,095 permits). |
| Eligible-property basis without one-unit attached homes: permits per 1,000 properties eligible under each state's own law | — | 8,164 | 15,318 | The owner's reframing ([ELIGIBLE_BASIS.md](ELIGIBLE_BASIS.md)). A separate model with its own 636-permit baseline, run at Gate 3 (Milwaukee on its ramp) and not rerun. Its 10th-percentile lower (4,254) is left out because the adopted lower is defined differently. |
| LA-calibrated multifamily correction to California's counts (option iii) | 5,446 | 8,438 | 15,206 | The more accurate, but data-hungrier, multifamily-lot removal (AQ-041). Its lower is the Rhode Island and Oregon average from that fit. |
| Multiplicative law: each place's current rate × the pooled statewide-law factor | — | 666 | — | A downside. Before-and-after pairs in other states contradict it, but no Midwest state has post-law data yet. Recomputed on the new baseline (722 at Gate 3). |
| California-only market regression, refitted on the adopted California counts | — | 2,390 | — | A downside: Wisconsin stays near the response of Madison-like markets. Recomputed on the new baseline (2,361 at Gate 3). |
| No ramp: full rate from 2027 | — | 10,268 | — | How much the ramp-up removes (1,511 permits) |
| Rural and small-community places at the Madison floor (0.2345) | — | 4,765 | — | How much of the addition comes from places with no measured activity (3,991 permits) |
| Madison at its pooled level instead of the Madison-like path | 5,599 | 8,948 | 17,410 | The effect of the Madison decision. It changes Madison's addition only (+191 permits in the central). |
| California out of the between-state common level (configuration B) | 5,538 | 7,657 | 11,226 | The G3F-2 alternative, which predicted held-out states less well. Its Rhode Island and Oregon lower is almost the same as the adopted one. |

*Cases that change only the current-law baseline* (central; baseline, addition and total with the law over 2027–2031; also in [`adu_model_baseline_only_effects.csv`](../../reference/adu_model_baseline_only_effects.csv)):

| Sensitivity case | Baseline | Change in baseline | Change in addition | Change in total with the law |
| --- | ---: | ---: | ---: | ---: |
| **Milwaukee on the assumed ramp to Madison's rate** (the Gate 3 treatment) | 644.9 | +40.2 | −36.0 | +4.2 |
| Places with uncoded rules behave like prohibited places | 418.3 | −186.4 | +158.6 | −27.8 |
| No ramp for recently liberalized places | 606.3 | +1.6 | −1.2 | +0.5 |
| Madison's current-law rate = its 2026 pace so far (provisional) | 813.8 | +209.1 | −129.4 | +79.7 |
| Madison's current-law rate from 2024–2025 only | 617.1 | +12.5 | −12.5 | 0.0 |
| Madison's 2022–2025 rate without the templated builder programme | 595.9 | −8.8 | +8.8 | 0.0 |

With Milwaukee on its ramp, the scenarios return exactly to the Gate 3 values on the new lower: 5,502 / 8,721 / 16,853 on a 644.9-permit baseline. The "no ramp for recently liberalized places" case moved from +12.8 to +1.6 permits of baseline because Milwaukee no longer ramps.

**Robustness checks** (methodological alternatives scored on the 7 held-out non-California statewide-law states; root-mean-square log error, lower is better; [POOLED_REVISION.md](POOLED_REVISION.md) section 2 and [ELIGIBLE_BASIS.md](ELIGIBLE_BASIS.md) section 3):

| Alternative | RMS log error, California in (A) | California out (B) | Result |
| --- | ---: | ---: | --- |
| **Adopted: ADU units per one-unit detached home, cap + A2** | **0.113** | 0.132 | Best |
| Permits (one per parcel per year) instead of units, per one-unit detached home | 0.132 | 0.150 | Worse |
| Eligible-property basis without one-unit attached homes | 0.168 | 0.184 | Worse |
| Eligible-property basis, full (attached homes included) | 0.202 | 0.217 | Worse |
| California in or out of the common level | see columns | | In is better under every option, but within noise (66% of 5,000 resamples) |

## How the central is built

1. **Pooled model.** The data are California's 457 jurisdictions, seven other statewide-law states and five cities ([POOLED_MODEL.md](POOLED_MODEL.md), revised in [POOLED_REVISION.md](POOLED_REVISION.md)). The seven states are each labelled by the area actually measured:
   - Washington law, measured in its cities excluding Seattle;
   - Oregon law, measured in 32 cities excluding Portland;
   - Vermont law, measured in Chittenden County;
   - Utah law, measured in reporting cities;
   - Maine law, Massachusetts law (293 of 351 towns reporting) and Rhode Island law, each measured statewide.

   The five cities are Seattle, Portland, Austin, Denver and Minneapolis.
2. **Outcome rules applied to the comparison data:**
   - **California:** at most 2 ADUs per parcel, plus the definite multifamily rule on Table A2 parcel numbers (AQ-041). This takes California 2023–2025 from 87,303 to 81,368 ADU units. Over 23,543,548 single-family home-years, that is 3.71 → 3.46 permits per 1,000 single-family homes per year.
   - **Every non-California series:** × (1 − 0.049) for ADUs built with a new house on a vacant lot (AQ-039).
   - **Minneapolis:** × (1 − 0.127) for ADUs on duplex lots.
3. **Within each state**, places differ by home value, household income and size. **Across states**, one common level fits best once a statewide law is in force; California is in that common level (G3F-2, configuration A). Market terms across states made predictions worse.
4. **Ramp-up** from the pooled year terms. In years 1–3, the increment reaches 0.63, 0.80 and 0.82 of its year-4 size (central; lower 0.62, 0.79, 0.82; upper 0.64, 0.80, 0.83).
5. **Milwaukee** (AQ-043): its current-law rate is its measured 2022–2025 rate, held flat. That is 35 candidate second-home permits ÷ 405.608 thousand home-years (101,402 single-family homes × 4 years) = 0.0863 permits per 1,000 single-family homes per year (95% interval 0.060–0.120). Its status is *observed*, quality C: the open permit data have no description or unit count, so these are unverified candidates. The permit file through 2026-06-15 shows no clear rise after the August 2025 reform (8 candidates ÷ 88.3 thousand home-years = 0.091). Its baseline is 43.8 permits over 2027–2031 and its central addition 306 permits. The Gate 3 ramp to Madison's 0.1876 is a baseline-only sensitivity case.
6. **Madison** is the only Wisconsin place that meets the Madison-like definition: a city or village with 20,000–120,000 single-family homes, median value $250,000–$500,000, not the largest city. It follows the observed median path of Madison-like cities in Washington and Oregon instead of its pooled level. That path is 0.452, 0.542, 0.601, 0.799 and 1.076 permits per 1,000 single-family homes per year in 2027–2031. It is the same in every scenario and has no ramp on top.
7. **Engine.** For each of 1,925 areas, the addition = single-family homes × (with-law rate − current rate) × ramp ÷ 1,000. It is never below zero, and the with-law rate is never below the Madison floor of 0.2345. Check: on the Gate 3 current-law rates (Milwaukee on its ramp), with the 10th-percentile lower and without Madison's path, the engine reproduces the pooled revision's totals to within 0.1 permit (4,424 / 8,912 / 17,374).

## Revision of 2026-10-26 (AQ-043)

The owner approved this packet on 2026-10-25 with lower 4,407, central 8,721 and Strong adoption 16,853 additional permits over 2027–2031, on a baseline of 645 permits, and a reference line of 8,208. In the Gate 4 review (2026-10-26, [SCENARIO_OPTIONS.md](../gate4/SCENARIO_OPTIONS.md)) the owner made three changes. Additional permits are statewide, over 2027–2031:

| Change | Baseline | Lower | Central | Strong adoption | Reference line |
| --- | ---: | ---: | ---: | ---: | ---: |
| Approved 2026-10-25 | 644.9 | 4,407 | 8,721 | 16,853 | 8,208 (7 states) |
| 1. Lower = mean of Rhode Island and Oregon (0.65 per 1,000 single-family homes per year at a typical place, instead of 0.53) | 644.9 | 5,502 (+1,095) | 8,721 | 16,853 | — |
| 2. Milwaukee at its measured 2022–2025 rate, flat (0.0863 instead of a ramp to 0.1876) | 604.6 (−40.2) | 5,538 (+36) | 8,757 (+36) | 16,889 (+36) | — |
| 3. Reference line = median of all 8 states, California included; 2031 carried forward | — | — | — | — | 8,851 (2027–2030: 6,594) |
| **Adopted now** | **604.6** | **5,538** | **8,757** | **16,889** | **8,851** |

- The Milwaukee change lowers the baseline by 40.2 permits but raises each scenario's addition by only 36, because the addition is ramped in its first three years and the baseline is not. The total with the law in the central moves from 9,365.5 to 9,361.3 permits (−4.2).
- The reference line would be 8,811 permits on the 644.9-permit baseline. On the 604.6-permit baseline it is 40 permits higher, 8,851, because the line fixes the with-law total and the addition is that total minus the baseline.
- Unchanged: the central and Strong adoption definitions, Madison on the Madison-like path, the Madison floor of 0.2345 and California in the common level.

## What changed since the 2026-10-24 packet

That packet had lower 4,789, central 9,526 and upper 18,398 additional permits over 2027–2031, plus an adoption line of 8,654. The central fell by 805 permits, to 8,721:

| Change | Decision | Effect on the central (additional permits, 2027–2031) |
| --- | --- | --- |
| **Teardown and vacant-lot rule.** An ADU built with a new house counts when the lot had a home before (teardown-rebuild). It does not count when the lot was vacant. In 17 cities split by demolition records, vacant-lot new-house ADUs were a median 4.9% of ADUs. So every non-California series is × 0.951, replacing the withdrawn 80% placeholder. | AQ-039, G3F-3 | −406 (9,318 → 8,912). Wisconsin's own counts add teardown-rebuild ADUs; Madison's 2022–2025 count went from 39 to 40. |
| **Multifamily-lot and cap rule** for California, as in step 2 above. California's level at a typical place, law in force 4+ years, fell from 2.61 to 2.45 permits per 1,000 single-family homes per year. | AQ-041 | −205 (9,523 → 9,318, other rules off) |
| **Wisconsin baseline update** after the AQ-039 rerun: 654 → 645 permits over 2027–2031 | AQ-039 | −3 |
| **Madison-like test and path** (see below) | AQ-040 follow-up, AQ-042 | −191 (8,912 → 8,721). Madison's own addition went from 326 to 135 permits. |
| **G3F-2 test:** keep California in the between-state common level, or take it out? | AQ-040 | Kept in, so no change. Out would give 7,621. |
| **Madison floor:** 40 second-home units ÷ 213.168 thousand home-years (53,292 single-family homes × 4 years, 2022–2025) = 0.1876, ÷ 0.8 = 0.2345 (was 0.229) | AQ-042 | under 1 |
| **Minneapolis** duplex-lot ADUs, × 0.873 | AQ-041 | under 1. Minneapolis has no statewide law, so it enters only the within-state terms. |

The lower fell from 4,789 to 4,407 permits, and the upper from 18,398 to 16,853. The upper fell most in permits for two reasons. It scales the central by 1.89, so it carries the central's drop almost twice over. And Madison's pooled upper addition (656 permits) is replaced by its path (135). The adoption line fell from 8,654 to 8,208, from the vacant-lot factor and the 645 baseline.

**The Madison-like test** ([MADISON_LIKE_CITIES.md](MADISON_LIKE_CITIES.md)). The question: have Madison-like cities in statewide-law states climbed to the model's rates? The definition was fixed before any outcome was read.
- **Years 1–3, 9 Washington and Oregon cities:** the median city ran at 0.45, 0.54 and 0.60 permits per 1,000 single-family homes per year. That is about half the 2026-10-24 model's typical-state path (0.83, 1.03, 1.07). By the pre-registered rule, this contradicts the model for those years.
- **Years 4–5, 4 Oregon cities only:** 0.80 and 1.08. Four cities are too few to test.
- Six of the nine cities made their own ADU reforms in the same window.
- **The owner's decision:** Madison follows that observed median path.

**The G3F-2 test** ([POOLED_REVISION.md](POOLED_REVISION.md) section 2). Each of the 7 non-California statewide-law states was held out in turn and predicted from the rest.
- With California in the common level (A), the root-mean-square log error is 0.113. Out (B), it is 0.132. With the best covariate weighting (C, household income), it is 0.243.
- A has the lower error in 66% of 5,000 resamples of the 7 states.
- A is about 6% too high on average (mean log error +0.055). B is about 8% too low (−0.087).
- By the owner's rule (keep California if it predicts the others better), California stays in.

## Owner review: step by step, with my self-assessment

I re-walked every step on 2026-10-25 against the files named. For steps 1 and 2, I recomputed Madison and one rural town by hand from the engine inputs, not through the engine.

| Step | What you do | What you should see | My result |
| --- | --- | --- | --- |
| 1 | Open [`adu_model_statewide.csv`](../../reference/adu_model_statewide.csv) | Three rows. The baseline is 604.6 permits on each; additional permits are lower 5,538.1, central 8,756.6, upper 16,888.9 (2026-10-26). | **Pass.** The numbers match this packet. The rows are ordered lower ≤ central ≤ upper in every area and year (engine invariant check). |
| 2 | Follow Madison: open `area_paths` in [`adu_model_params.json`](../../reference/adu_model_params.json) | Madison has 53,292 single-family homes and a current rate of 0.188 permits per 1,000 per year (40 units ÷ 213.168 thousand home-years). Its baseline is 53.292 × 0.188 × 5 = 50.0 permits. Its path sums to 0.452 + 0.542 + 0.601 + 0.799 + 1.076 = 3.470. Its addition is 53.292 × (3.470 − 5 × 0.188) = 53.292 × 2.532 = **134.9 permits** in every scenario. | **Pass.** My hand result is 134.92 for lower, central and upper; the engine gives 134.92 for each. |
| 3 | Follow a rural town: Christiana town, Vernon County (`muni:5512314675`), in [`pooled_revision_wi_y_by_area.csv`](../../reference/pooled_revision_wi_y_by_area.csv), rows `cap_a2`, `A_ca_in_common_level` | The town has 389 single-family homes and a current rate of 0.061 permits per 1,000 per year. Its central level is 1.5669, and the central ramp sums to 0.6339 + 0.7958 + 0.8247 + 1 + 1 = 4.2544. Its addition is 0.389 × (1.5669 − 0.0607) × 4.2544 = **2.49 permits**. Lower is 1.58 (level 1.5669 × 0.6497 = 1.0181, ramp sum 4.2283); upper is 4.81 (level 2.9537). | **Pass.** My hand result matches the engine to 0.01 permit on all three paths (2026-10-26 lower included). Its baseline is 0.12 permits. |
| 4 | Check current activity reduces the change | Each place's current rate is subtracted each year: Madison's 0.188, Christiana's 0.061 | **Pass.** It is visible in both hand calculations. |
| 5 | Read the source of the central | `area_levels` in the params file points to option `cap_a2`, configuration `A_ca_in_common_level`. [POOLED_REVISION.md](POOLED_REVISION.md) sections 1–3 explain it. | **Pass.** On the Gate 3 current-law rates, with the 10th-percentile lower and without Madison's path, the engine reproduces `pooled_revision_wi.csv` (4,423.9 / 8,912.1 / 17,373.9) to within 0.1 permit. `run_adu_model.py` stops with an error if they differ by more than 2 permits. It also stops if the stored lower factor (0.6497) or any stored ramp does not follow from the files. |
| 6 | Check what separates lower and upper, and the upper's label | The lower: Rhode Island 0.6214 and Oregon 0.6826, mean 0.6520, ÷ common level 1.0035 = 0.6497 (`paths.lower.level_from` in the params file). The upper: the factor 1.885 (the 80% range of state levels). [`pooled_revision_stage2_levels.csv`](../../reference/pooled_revision_stage2_levels.csv) shows California at 2.45, the only state above the upper's 1.89 at a typical place. | **Pass.** The label "Strong adoption" and its info text match the data: the next state below 1.89 is Washington at 1.19. |
| 7 | Validation and strongest challenge | Held-out state errors in [`pooled_revision_g3f2.csv`](../../reference/pooled_revision_g3f2.csv): A 0.113, B 0.132. The challenges below. | **Pass, with the noise caveat.** A beats B by 0.019 log points, which is within noise (66% of resamples). |
| 8 | Look at the charts | [States](adoption_spaghetti_states.png): the Wisconsin central sits on the states' median, and Strong adoption sits between Vermont's last year and California. [Cities](adoption_spaghetti_cities.png): Madison's adopted path is the Madison-like median; its pooled level is the dashed line, about twice as high. | **Pass.** Both charts were regenerated from the adopted outputs. |
| 9 | Read the sensitivity analysis and robustness checks | The tables and the [tornado chart](sensitivity_tornado.png) above, from [`adu_model_sensitivities.csv`](../../reference/adu_model_sensitivities.csv) | **Pass.** The engine-run and baseline-only rows were recomputed on 2026-10-26. The multiplicative and California-only rows were recomputed from a refit of the adopted model on the new current-law rates (on the Gate 3 rates the refit reproduces 722.3 and 2,361.0). The eligible-basis row is read from its own Gate 3 run. |
| 10 | Decide | Below | Decided: G3F-1 to G3F-4 closed; advance to Gate 4 |

## Strongest remaining challenges

1. **No Midwest state has post-law data.** The model contains no Wisconsin data in its fit.
   - Wisconsin permits 0.07 per 1,000 single-family homes per year today, where the pooled model's no-law level for Wisconsin is 0.50.
   - The case for the model: states with before-and-after data (California, Rhode Island, Washington, Vermont) reached similar first-year levels however low they started.
   - The case against: those are coastal or New England markets. Iowa's first full year (2026) will be the first Midwest test.
2. **Madison-like cities ran at about half the model in years 1–3.** The medians were 0.45, 0.54 and 0.60 permits per 1,000 single-family homes per year in 9 Washington and Oregon cities, against the 2026-10-24 model's 0.83, 1.03 and 1.07.
   - The adopted central's statewide rates are 0.77, 0.95 and 0.99 in 2027–2029, still well above those city medians.
   - Only Madison is moved onto the observed path. If Wisconsin's other mid-size markets behave like those cities, the central is too high in its first three years.
3. **The hold-out test rests on 7 states.**
   - The A-over-B choice flips when Washington or Rhode Island is removed (A wins 5 of 7 drop-one reruns).
   - The best configuration's 0.113 is the best of five scored on the same 7 states, so it is optimistic.
   - The lower and upper rest on how 8 states differ, one of them California.

## What a legislator might misread, stated in the tool

- Totals are over five years: the central is about 1,751 permits a year (8,757 ÷ 5). They are permits, not completed or net new homes, and they come on top of the baseline.
- The range shows how states differ, not statistical certainty.
- Town figures are rough shares of the statewide result, not local forecasts. Rural areas get 3,801 of the 8,757 central permits (43%) with 710,070 of the 1,839,569 single-family homes (39%), partly because rural home values include acreage.
- Results describe what other states experienced after their laws. They are associations, not proven causal effects.

## Decisions recorded

| ID | Decision | Outcome |
| --- | --- | --- |
| G3F-1 | Upper scenario label | **Decided:** "Strong adoption", the configuration's 90th percentile (16,853), with the info text "The high end of what statewide-law states have reached; only California has gone higher." Wisconsin at California's own level would be 22,694 (with Madison at its pooled level); that is not shown as a scenario. |
| G3F-2 | California in the common level | **Decided by the hold-out test:** keep California in (RMS log error 0.113 against 0.132 without it). "Without California" is a sensitivity case (7,621). |
| G3F-3 | New-house ADUs | **Decided:** the measured vacant-lot share, × (1 − 0.049), in the headline (AQ-039), replacing the 80% placeholder |
| G3F-4 | Advance to Gate 4 | **Decided: advance**, with the scenarios, labels, sensitivity cases and robustness checks above (AQ-042) |
| AQ-041 | Multifamily-lot ADUs in California's counts | Cap of 2 per parcel plus the A2 rule in the headline; the LA-calibrated correction as a sensitivity case |
| AQ-042 | Adopted basis | Option (ii) configuration A; Madison floor 0.2345; Madison on the Madison-like path; eligible-property basis as a sensitivity case and a robustness check |
| AQ-043 | Gate 4 review changes (2026-10-26) | Lower = mean of Rhode Island and Oregon (5,538); Milwaukee at its measured 2022–2025 rate (baseline 605); reference line = median of all 8 states with 2031 carried forward (8,851); the 10th-percentile lower and the Milwaukee ramp kept as sensitivity cases |

## Reproduce

```
uv run python scripts/run_pooled_revision.py     # pooled revision; writes reference/pooled_revision_*.csv incl. per-area levels
uv run python scripts/build_wi_baseline.py       # current-law rates and baseline (Milwaukee measured; ramp variant kept)
uv run python scripts/run_adu_model.py           # engine; writes reference/adu_model_*.csv
uv run python scripts/run_baseline_only_effects.py
uv run --with matplotlib python scripts/plot_adoption_spaghetti.py
uv run --with matplotlib python scripts/plot_sensitivity_tornado.py
uv run --with pytest python -m pytest -q
```

## Supporting documents

- **Adopted model:** [POOLED_REVISION.md](POOLED_REVISION.md) (adopted basis and the G3F-2 test) · [POOLED_MODEL.md](POOLED_MODEL.md) (model form; its totals are superseded)
- **Outcome rules:** [MULTIFAMILY_LOT_ADUS.md](MULTIFAMILY_LOT_ADUS.md) (California multifamily-lot ADUs and the cap) · [ELIGIBLE_BASIS.md](ELIGIBLE_BASIS.md) (eligible-property reframing; sensitivity case and robustness check)
- **Madison and charts:** [MADISON_LIKE_CITIES.md](MADISON_LIKE_CITIES.md) (Madison-like test, vacant-lot share) · [spaghetti chart, states](adoption_spaghetti_states.png) · [spaghetti chart, Madison-like cities](adoption_spaghetti_cities.png) · [tornado chart of sensitivity cases](sensitivity_tornado.png)
- **Comparison data:** [STATEWIDE_STATES.md](STATEWIDE_STATES.md) · [OTHER_CITIES.md](OTHER_CITIES.md) · [CA_STUDY_RESULTS.md](CA_STUDY_RESULTS.md) · [CA_REGRESSION.md](CA_REGRESSION.md) (now a sensitivity case)
- **Wisconsin:** [WI_BASELINE.md](WI_BASELINE.md) · [WI_UNZONED_TOWNS.md](WI_UNZONED_TOWNS.md) · [WI_RULES_VS_ACTIVITY.md](WI_RULES_VS_ACTIVITY.md) · [CA_RULES_VS_ACTIVITY.md](CA_RULES_VS_ACTIVITY.md)
- **Data rules:** [DATA_COMPLIANCE.md](../DATA_COMPLIANCE.md)
