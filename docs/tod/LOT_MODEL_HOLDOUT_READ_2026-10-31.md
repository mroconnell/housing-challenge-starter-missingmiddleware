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

**Score:** |log(predicted ÷ actual share)|. Bellevue cannot be scored this way, because its actual share is 0.

| City | Raw | Calibrated | Same share as before |
| --- | ---: | ---: | ---: |
| Chicago | 0.79 | 0.32 | 0.92 |
| Madison | 0.45 | 0.22 | 0.45 |
| Median of the two | 0.62 | 0.27 | 0.69 |

**What it says**
- **Direction is right in Chicago and Madison.** The upzoned share rose after reform, and the model predicted a rise.
- **The raw model overstates the rise** about fivefold, as it did in the training cities (k = 0.18). The calibrated version is the closest of the three in both cities.
- **Bellevue fails.** Almost nothing was built in BelRed in the window (466 homes citywide in the study area, none on upzoned lots), and the raw model put 96% of new homes there.
  - In Bellevue the model has learned "upzoned = where building goes" even when nothing is built.
  - The calibrated version cuts that to 17%, still wrong.
- **Extra homes (net addition):**
  - A, pure relocation: 0, by construction.
  - B, pure addition: Chicago 629, Madison 400 and Bellevue 18 homes over 5 years (raw, before calibration).

**Limits stated with it**
- Two of the three holdouts can be scored.
- The calibration factor comes from 6 cities.
- Wisconsin's law covers about 8 times the training cases' upzoned lots (plan item 50.3).
- Many rules changed after results were seen. The locked item-36 result is reported beside this one in [LOT_MODEL_LOCKED_VS_FINAL.md](LOT_MODEL_LOCKED_VS_FINAL.md).
