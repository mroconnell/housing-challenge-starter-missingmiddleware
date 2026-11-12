# How sure: which what-if goes in which chart

Owner decision, 2026-11-11 23:41: each reform's How sure tab has two charts at the top.

Revised 2026-11-11: ADU thread review (3 ADU rows moved or noted, 5 How-sure side lines added); middle housing input what-ifs (bundle `middle-11f3a9b9cf`); parking measured averages (bundle `parking-6c6178ad60`).

- **Inputs**: "What moves the estimate: model inputs". A tornado. Each row changes one input of the main model.
- **Other ways**: "Other ways to estimate it". Other methods and robustness checks, as dots against the 90% range.

Rules used:

- Ambiguous rows go in Other ways. They are marked **flag**.
- A row with one alternative is a one-sided bar from the pivot.
- Inputs that leave the 2027–2031 total unchanged are listed under the bars ("Tested, no change").
- "Added" = not in the former single chart; added because it is an input.

Code: `ui/src/tornado.ts`; the splits are `aduWhatIfs` (`ui/src/screens/howsure.ts`), `todWhatIfs` (`ui/src/scenarios/tod/screens.ts`), `parkingWhatIfs` (`ui/src/scenarios/parking/index.ts`), `middleWhatIfs` (`ui/src/scenarios/middle/index.ts`). Tests: `ui/tests/howsure_tornado.spec.ts`.

## Pivots (the number each 90% range is built on)

| Reform | Pivot | What it is | Bundle field |
|---|---|---|---|
| ADUs | 10,492 added ADU permits, 2027–2031 | Typical adoption | `state.json` scenario `central` |
| Middle housing | 1,570 extra homes in 2–4 unit buildings, 2027–2031 | Four-state result | `statewide.json` `core.central` (= side line `four_state`) |
| TOD | 10,028 extra homes near stops, 2027–2031 | 11-place average | `howsure.json` `tornado.central` |
| Parking | −15,380 extra homes permitted, 2027–2031 | Measured average, 74 repeal places | `statewide.json` side line `measured_average` |

## ADUs (bundle `uncertainty.json`; values at typical adoption)

18 former rows: 15 Inputs, 3 Other ways (none flagged). Plus 9 added input cases (baseline group, local group, one unknown-rules variant) and 5 added Other ways (How-sure-only side lines in `state.json`).

| What-if (case id) | Chart | Reason |
|---|---|---|
| rural-places-and-small-communities-held- | Inputs | Assumed rate for rural places |
| madison-on-the-path-of-similar-cities-in | Inputs | Madison's with-law level |
| leave-california-out-of-the-typical-leve | Inputs | Data choice for the typical level |
| a-stricter-correction-for-california-s-a | Inputs | Data correction for one input |
| do-not-scale-up-states--counts-for-towns | Inputs | Scale-up setting; one row with the next |
| scale-up-for-non-reporting-towns-in-main | Inputs | Scale-up setting; same row |
| count-washington-s-law-years-from-enactm | Inputs | Timing coding |
| leave-out-vermont-s-2024-count--changed- | Inputs | Data-source choice |
| every-comparison-year-read-against-2020- | Inputs | Denominator year choice |
| law-years-coded-as-before-aq-065--vermon | Inputs | Coding of law years |
| maine-s-reporting-share-as-a-homes-share | Inputs | One input value |
| leave-vermont-out-of-the-comparison-stat | Inputs | Data choice |
| no-slow-start--full-effect-from-2027 | Inputs | Slow start on/off |
| places-with-uncoded-rules-behave-like-pr (added) | Inputs | Uncoded places; one row with `unknown:like_benchmark` |
| unknown:like_benchmark (added, `unknown_rules.json`) | Inputs | Uncoded places, other setting |
| madison-s-current-law-rate-… ×3 (added) | Inputs | Madison's rate; one row, three settings |
| no-ramp-for-recently-liberalized-places- (added) | Inputs | Baseline ramp on/off |
| milwaukee-rises-to-madison-s-rate-after- (added) | Inputs | Baseline assumption |
| wisconsin-s-baseline-rises-like-no-law-p (added) | Inputs | Baseline assumption |
| let-small-high-value-villages-keep-their (added) | Inputs (no change) | Coding; moves the total by 0 |
| lower-scenario-at-the-10th-percentile-of | Inputs (no change) | Note: "changes only the OR & RI side line (6,321 → 5,401)" |
| comparison-state-counts-and-coding-as-at | Inputs (one bundled bar) | "Three data settings at once (as at Gate 4)", 8,402. Note: "no scale-up for non-reporting towns, Washington from enactment, Massachusetts at 11/12" |
| count-per-eligible-property--not-per-sin | Other ways | Note: "a separate model with its own baseline (636)" |
| the-law-multiplies-today-s-rates--instea | Other ways | Different method (= side line `whatif_791`, not repeated) |
| predict-wisconsin-from-california-s-citi | Other ways | Different method (= side line `whatif_2255`, not repeated) |
| side:drift_main (added) | Other ways | Market-heat adjustment, 11,318 |
| side:drift_heat_only (added) | Other ways | Market heat, heat part only, 10,441; note "post hoc" |
| side:drift_equal_weight (added) | Other ways | Market heat, states weighted equally, 10,746; note "post hoc" |
| side:ca_high (added) | Other ways | 90th-percentile high, 19,784 |
| side:bias_corrected (added) | Other ways | Range 7,517 to 13,318, drawn as a bar from low to high |

## Middle housing (bundle `howsure.json` `bars`)

10 rows: 6 Inputs, 4 Other ways (3 flagged). The bundle marks inputs with `"chart": "Inputs"`. Units: extra homes in 2–4 unit buildings, 2027–2031; pivot 1,570.

| What-if | Chart | Reason |
|---|---|---|
| flat_timing | Inputs | Timing: slow start on/off |
| match_nationally | Inputs | Comparison group; 1,560 |
| oregon_before | Inputs | Oregon's before years; 1,454 |
| census_filled | Inputs | Filled-in permit counts; −382. Note: failed the fake-years check, so read as partly trend |
| leave_one_state | Inputs | Leave one law state out; 788 to 1,984 |
| first_year_share | Inputs | 2027 share; 1,515 to 1,658 |
| townhouses | Other ways, **flag** | Counts more kinds of homes than the range |
| five_six | Other ways, **flag** | Counts 5–6 unit buildings |
| stronger | Other ways, **flag** | Stronger law; 5–6 unit share band |
| m2_ratio | Other ways | Other conversion method |

## TOD (bundle `howsure.json` `tornado.rows`)

20 former rows: 2 Inputs (one row), 18 Other ways (1 flagged). Plus 10 added inputs that leave the total unchanged.

| What-if | Chart | Reason |
|---|---|---|
| district_10:strong, district_25:strong | Inputs (one row) | District share 10% / 25% (15% used). Run on the upper line only |
| ramp_new_york, ramp_year5_alt (added) | Inputs (no change) | Timing; same five-year total |
| old_law_placement, no_suburbs, rapid_only, high, b_half (added) | Inputs (no change) | Placement and stop rules; same total |
| baseline_low, baseline_high, census_as_published (added) | Inputs (no change) | Current law only |
| main:little, main:strong | Other ways | Other lines |
| typical_range:typical_low / _high | Other ways | Leave-one-place-out check |
| strong_range:strong_low / _high | Other ways | Leave-one-place-out check |
| little_range:little_low / _high | Other ways | Another line's range |
| line_age_matched:typical | Other ways, **flag** | Other comparison group (could be an input) |
| upper_2x2:strong, upper_2x2_trend_adjusted:strong | Other ways | 2×2 readings |
| 7 rows of kind `earlier` | Other ways | Earlier methods |

## Parking (bundle `howsure.json` `sensitivities`)

13 former rows: 7 Inputs (6 bars), 6 Other ways (none flagged). Plus 3 added current-law inputs that leave the total unchanged. Every input bar runs from the pivot to the bundle's `measured_average` for that case.

| What-if | Chart | Reason |
|---|---|---|
| High end, with towns left out | Inputs | Coverage input; −10,760 |
| Near-benchmark places at the full rate | Inputs | Coding input; −15,472 |
| Baseline: … ×3 (added) | Inputs (no change) | Current law only; bundle says the addition does not change |
| Cleaned data, undated reforms kept as comparisons (placebo) | Inputs | Data-cleaning round; −11,035; earlier 76-place sample (73 matched) |
| Cleaned data, strict comparison cleaning (placebo) | Inputs (one bar with the next) | Data-cleaning round; −3,691; earlier 76-place sample (73 matched) |
| Cleaned data, strict comparison cleaning (resampling) | Inputs (same bar) | Same round, same measured average (−3,691) |
| Cleaned data, only apartment-scale reforms disqualify comparisons (placebo) | Inputs | Data-cleaning round; −5,389; earlier 76-place sample (73 matched) |
| As above, plus state laws in California, Oregon and Washington (placebo) | Inputs | Data-cleaning round; −7,073; earlier 76-place sample (73 matched). Labelled in full, not "As above" |
| Resampling the real places (earlier high end) | Other ways | Other estimator |
| Buildings of 2 or more units only | Other ways | Other outcome |
| Without San Francisco | Other ways | Robustness check |
| Combined with California's transit-area law | Other ways | Other evidence |
| First 24 places only (earlier estimate) | Other ways | Earlier estimate |
| Prediction by city size and setting | Other ways | Other model |

## Missing numbers (for the reform threads)

- **TOD**: district share 10% and 25% on the 11-place average (only the upper line was run).
