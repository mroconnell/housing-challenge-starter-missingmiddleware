# TOD lot model: the one-time holdout read

Written 2026-10-31, right after the read. Chicago, Madison and Bellevue were never used to train, tune or choose the model (plan items 42, 49, 59). This is the single read declared in plan item 59.5; the results are reported as they came out.

**Model:** round 8 of the loop (plan item 57.5).
- Each city's total is "same pace as before".
- Histogram gradient boosting predicts each lot's homes per acre: one model for upzoned lots with the rules after, one for all other lots with the rules before. These become each lot's share of the city's new homes.
- The model was trained on the 6 training cities and the 4 no-reform cities.
- The calibration factor k = 0.18 comes from the 6 training cities (plan item 59.4).

**Upzoned lots' share of homes permitted after the reform (5-year basis)**

| City | Share before | Actual share after | Model (raw) | Model (calibrated) | Same share as before |
| --- | ---: | ---: | ---: | ---: | ---: |
| Chicago | 4.0% | 9.9% | 21.8% | 7.2% | 4.0% |
| Madison | 12.1% | 19.0% | 29.7% | 15.3% | 12.1% |
| Bellevue | 0.0% | 0.0% | 95.6% | 17.2% | 0.0% |

**Score:** |log(predicted ÷ actual share)|. For comparison, the 6 training cities scored 0.31–0.47 (model) vs 0.65 (same share as before) across 6 seeds; those are training cities, not holdouts. Bellevue cannot be scored this way, because its actual share is 0.

| City | Raw | Calibrated | Same share as before |
| --- | ---: | ---: | ---: |
| Chicago | 0.79 | 0.32 | 0.92 |
| Madison | 0.45 | 0.22 | 0.45 |
| Median of the two | 0.62 | 0.27 | 0.69 |

**What it says**
- **Direction (clean evidence: 2 cities).** In Chicago and Madison, cities never used for training, the upzoned share rose after reform and the model predicted a rise. New York, Charlotte and Philadelphia show the same pattern, but they are training cities, so they are not independent evidence.
- **Size.** The raw model overstates the rise about fivefold, as in the training cities (k = 0.18). In the two scorable holdout cities, a small rise above the before-share (the calibrated model) predicted better than both "no change" and the raw model. This rests on 2 cities.
- **Bellevue fails.** Almost nothing was built in BelRed in the window: 466 homes in the study area, none on upzoned lots. The raw model put 96% of new homes on upzoned lots; the calibrated one put 17%. Both are wrong.
- **Part of the overshoot may be a data problem.** In New York, a training city, 28 lots still show more than 1,000 homes per acre, holding 5,510 homes. These are fragments of assembled sites. They can inflate what the model learns about upzoned lots, so k partly absorbs a data problem, not only a model one.
- **Extra homes over 5 years (net addition).** A, pure relocation: 0, by construction. B, pure addition, a labelled sensitivity only:

| City | B, calibrated (main) | B, raw |
| --- | ---: | ---: |
| Chicago | 113 | 629 |
| Madison | 72 | 400 |
| Bellevue | 3 | 18 |

- **Upper Wisconsin cross-check, rough.** It applies only if every extra home on upzoned lots is new (bound B); if homes only move (bound A), the figure is 0.
  - As a share of the homes on each scorable holdout's upzoned lots (2010 census), calibrated B is 1.2% (Chicago) and 3.4% (Madison) over 5 years. Bellevue, which failed the read, is not used.
  - Applied to the 313,564 homes in Wisconsin's station areas, that range gives about 3,900 to 10,600 homes. That sits between the tool's typical (2,509) and strong (17,148) scenarios.
  - It extrapolates from slivers to a law covering most station areas (about 8 times the training scale), so it is a cross-check, not an estimate.

**Limits stated with it**
- Two of the three holdouts can be scored.
- The calibration factor comes from 6 cities.
- Wisconsin's law covers about 8 times the training cases' upzoned lots (plan item 50.3).
- Many rules changed after results were seen. The locked item-36 result is reported beside this one in [LOT_MODEL_LOCKED_VS_FINAL.md](LOT_MODEL_LOCKED_VS_FINAL.md).

## Where the tool's numbers come from (unchanged)

The tool's TOD scenarios do not use this lot model.
- **Little, 171 extra homes over 2027–2031:** Los Angeles's Transit Oriented Communities result. That is 0.04 percentage points over 6 years, scaled to 5 years and divided by the 61% of homes the program covered, giving 0.055% of the 313,564 homes in Wisconsin's station areas.
- **Typical, 2,509:** Stacy et al. (2023), 0.8% per loosening reform, applied to the same homes. Its critique by AEI is open in AQ-059.
- **Strong, 17,148:** Auckland's 2016 upzoning. That is 21,808 extra permits, or 4.11% of the city's homes, divided by the 75.2% of residential land it covered, giving 5.47%.

These were finalized in AQ-055 and are checked against the city cases ([NET_EFFECT_RESULTS.md](NET_EFFECT_RESULTS.md)) and the census cases ([CENSUS_CASES_RESULTS.md](CENSUS_CASES_RESULTS.md)).
