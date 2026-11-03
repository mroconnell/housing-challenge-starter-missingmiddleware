# ADU causal framework: locked plan

Locked 2026-11-03 by the ADU conductor. It comes from the learning thread's draft v0 (Ryan approved sending it), and the tutor agreed every change below. No count in this plan had been run when this file was committed. Anything chosen after a result is seen is labelled **post hoc**. Nothing in the tool changes without Ryan's OK.

## Where the ADU model stands

- **Lines.** These are scenarios tied to real states, not confidence intervals.
  - Lower: 6,321.
  - Central: 10,492.
  - Upper: 19,784.
  - Baseline: 786.
  - Unit: extra ADU permits on single-family lots, Wisconsin, 2027–2031.
- **Evidence.** 8 statewide-law states. In the held-out test, each of the 7 non-California states is hidden in turn and predicted from the rest.
- **California (Gate 3).** Already-permissive cities rose ×2.39 (1.94 to 3.91) after the 2020 law. No comparison group.
- **Activity groups (rule v1, G3-6).** Each state's own pre-law window sorts places into three groups:
  - 0 permits: not adopted.
  - Top quarter of places with at least 3 permits: early adopter.
  - The rest: in between.

## Shared rules

- **Estimand.** Extra ADU permits caused by a statewide law, per 1,000 single-family homes per year. ADU permits here means second homes on single-family lots (AQ-032).
- **Groups.** Rule v1 as locked at G3-6. No new cutoffs, because those numbers have been seen.
- **Intervals.** Every estimate comes with:
  - a 90% interval, by bootstrap over cities (clustered by state when more than one state is involved), seed 20261103;
  - a leave-one-out range (city or state, as fits the test).
- **Main measure.** A pooled log rate ratio, weighted by exposure: sum of permits ÷ sum of (homes × years), in each group and window. It is not a mean of city ratios. The difference in permits per 1,000 single-family homes per year is reported second.

## A3. How far off the model was for a state it never saw (run first)

- **Data.** No new data. Recompute the held-out root mean square log error from the adopted run (V6s plus the trend baseline, AQ-065). The draft's 0.136 is not used.
- **Range.** central × exp(± t × error), with t at 6 degrees of freedom (1.943, 90%) for 7 misses.
- **Second version.** Bootstrap over the 7 states.
- **Label.** "How far off the model was for a state it never saw." It is shown beside the scenarios, not instead of them.
- **Caveat stated beside it.** It covers law-side error only. Wisconsin's assigned current rates carry 74% of the central addition, and they are not part of the 7 misses.
- **Pass rule.** None. Report only.

## A2. Within California: does being open before 2020 change the gain? (second)

- **Question.** Did cities already active under the 2017 law gain more or less from the 2020 package than other cities?
- **Data.** One source per year:
  - BuildinganADU for 2017;
  - HCD APR Table A2 (data/raw/hcd_apr_a2) from 2018 on.
  - For 2018–2019, the other source is reported as a check.
- **Before you count.** Confirm 2025 is complete in the APR file before using 2023–2025. If it is not complete, the after window is 2022–2024, and that is logged here before counting.
- **Windows.** Before is 2017–2019, averaged over three years to limit regression to the mean. After is 2023–2025.
- **Main display.** The three rule v1 groups.
- **No-cutoff check.**
  - X is each city's 2017–2019 rate, on a sliding scale.
  - Y is each city's after-minus-before change.
  - Report the slope of Y on X, controlling for home value and size as in CA_REGRESSION.
- **Regression-to-the-mean check.**
  - Groups are defined on 2017 only.
  - The slope compares 2018 with 2019. Both years fall under the 2017 law and before the 2020 package.
  - Each city's change is measured relative to statewide growth over 2018–2019, because the statewide ramp makes a raw slope of 0 the wrong yardstick.
- **Pass rule.** Report the slope with its 90% interval, and say whether the sliding scale agrees in direction with the groups. The regression-to-the-mean slope should have a 90% interval that includes 0. If it does not, the group gaps in the main display are read as partly regression to the mean.
- **Feeds Wisconsin.** It explains why the central uses the restrictive-group ramp. No new line.

## A4. Can rule v1 be applied outside California? (third; Washington first)

- **Order.** Washington first, from OFM city-level estimates (the source behind WA_inc_exSeattle, 2011–2023). Then Oregon, Massachusetts and Maine, if time allows.
  - Oregon: the 32-city panel starts at the law year, so only Portland has pre-law years.
  - Massachusetts: only a 2025 statewide count is in hand.
  - Maine: waits on the town list (Ryan's email to MOCA).
- **Check before Washington cities count as "no law".** Find out whether Washington's 2019–2020 ADU bills count as a state law inside 2017–2022. The tutor believes SB 6617 (2020) limited ADU parking near transit, and perhaps owner-occupancy rules too. Source the enacted text and effective date, and log the finding here before any count.
  - If they count: Washington cities are not no-law comparisons for A1 after that date.
  - Either way: they can still serve for rule v1 within Washington, using its own pre-law window.
- **Feasible if** a state has city-level counts for at least 3 pre-law years, covering most of its single-family homes. If feasible, rerun A2 in that state.

## A1. Statewide spillover: permissive cities with and without a state law (locked as not feasible)

- **Question.** Did California's 2020 package raise ADU permits in cities that were already active under the 2017 law, compared with similar cities in states with no law?
  - What it measures: the 2020 package's extra effect over the 2017 law, not law against no law. SB 1069 and AB 2299 took effect on 2017-01-01.
  - Caveat: early-adopter status in 2017–2019 is partly caused by the 2017 law.
- **Status: not feasible on data in hand.** The plan needs at least 5 clean comparison cities, and the data in hand give 3 at most. Checked against reference/other_cities_annual.csv, other_cities_reforms.csv and statewide_states_annual.csv:

| City | Why it is out, or what it can supply |
| --- | --- |
| Austin | Clean for 2017–2019. HOME phase 1 (Feb 2024) breaks 2024 and later, so its after window is 2023 only. |
| Minneapolis | Series starts in 2017. Its own reforms fall between the windows: the 2040 plan (2020-01) and the end of owner occupancy (2021-02). |
| Seattle | Its 2019 ordinance falls inside the before window. Washington's law (July 2023) and local compliance (2025) leave no clean after window. |
| Denver | Text amendment July 2023, citywide ADUs December 2024, Colorado law June 2025. Only 2021–2022 are clean after years. |
| Chicago | No data in the repository. Its 2021 ADU ordinance is itself a reform between the windows. |
| Portland | In Oregon, which has a statewide law. |
| Honolulu | Usable, 2016–2024. |
| Montgomery County, MD | Data start in 2019, the year of its own rule change. |
| Bozeman | Data start in 2020. |
| Spokane | Its own 2022 interim rules, then Washington's law in 2023. |

- **Data needed to reopen A1.**
  - At least 5 cities in no-law states.
  - Yearly ADU counts for 2017–2023.
  - No reform of their own between the windows.
  - A1 reopens only if A4 or new data supply them. The windows are then before 2017–2019 and after 2021–2023, fixed now.
- **Comparison rule, fixed now.** A comparison city qualifies if its 2017–2019 rate is at or above California's rule v1 early-adopter cutoff. That cutoff is taken from the G3-6 code as locked, not recomputed.
- **Measure if reopened.** The pooled log rate ratio is the main measure, and the difference is secondary. The pass rule is "spillover supported" if the 90% interval of the ratio excludes 1.
- **Pre-trend check if reopened.**
  - Compare 2014–2015 with 2016. 2012 is dropped as a likely reporting gap, and 2013 is dropped as thin.
  - It needs at least 4 comparison cities with counts in those years. Otherwise it is reported as "not testable", not as passed.
  - Why it is weak: BuildinganADU's statewide sums for 2012–2016 are 158, 745, 728, 1,109 and 1,269, and most places show 0. The source says early zeros are reported values, not proof of no construction.
- **Post hoc fallback (descriptive only, labelled post hoc).** Compare California early adopters' ×2.39 with the no-reform growth already measured in NO_REFORM_R1: 7.3% a year from the no-law series, about ×1.5 over the same span. Both numbers have been seen, so this is not a test.

## Run order

1. A3.
2. A2.
3. A4, Washington first, starting with the SB 6617 check.
4. A1 stays locked as not feasible unless A4 or new data supply 5 clean cities.

## Stage 2 (after Stage 1)

- Keep the three scenario lines.
- Candidates to add, each only by a rule fixed before it runs:
  - the A3 range beside the central;
  - an A1 spillover multiplier for early adopters (Madison), as a sensitivity case, only if A1 reopens and passes.
- The Madison check stays. Rule v1 puts Madison at 2.5 per 1,000 a year with the law, against about 0.2 today.
- Ryan sees any tool change before it is made.

## Changes after locking

Details fixed while coding, before each count was seen (2026-11-03):
- **A3.** The bootstrap version is 1.645 × the 95th percentile of the error, from 10,000 draws over states. Each state's own miss applied to the central is shown as well.
- **A2.**
  - Only places observed in all 6 window years are kept.
  - The regression-to-the-mean check also gets a group view: groups set on 2017 alone, with each group's 2019/2018 growth relative to the state.
  - The BuildinganADU 2018–2019 check reruns the whole of A2 on that measure.
- **A4.** SB 6617 is checked against the enacted text: parking only. The 1993 rule (RCW 43.63A.215) is found. Under both, Washington cities are not no-law comparisons for 2017–2022.
- **Post hoc, labelled in the results:** the no-control sliding-scale slope.

Results: [CAUSAL_FRAMEWORK_RESULTS.md](CAUSAL_FRAMEWORK_RESULTS.md).
