# TOD full model runs: plan (logged before any run, 2026-10-31)

Owner ask (18:18): after the clean fit-and-fix rounds, run each scenario's list of models (8–10, including the big causal forest runs) for the no-reform baseline and for each predictive model. Runs stay on the Mac. Results go to the audit as they come in. No tool numbers change.

## Methods (the 8 from the traits test, plus the true causal forest)

| # | Method | Settings |
| --- | --- | --- |
| 0 | Plain average (benchmark) | Training-weighted homes per lot |
| 1 | Weighted linear regression | Ridge, alpha 1, standardized traits, gaps filled with training medians |
| 2 | LASSO | Alpha 0.01, standardized |
| 3 | Regression tree | At least 200 lots per leaf |
| 4 | Random forest | 300 trees, at least 50 lots per leaf |
| 5 | Gradient boosting | Histogram gradient boosting (the loop's fast tool) |
| 6 | Nearest neighbours | 50 neighbours on 15 principal components of standardized traits |
| 7 | Multilevel model | Random intercept by city (statsmodels MixedLM) on 15 principal components; a held-out city gets the fixed part |
| 8 | Causal forest (EconML CausalForestDML, MIT licence) | Prediction model only: treatment = upzoned, outcome = homes per acre after; law-off level from gradient boosting, law-on = law-off + the forest's per-lot effect. Not used for the baseline, which has no treatment |

## Row thinning (the same for every method)

Every lot that built is kept. 10% of lots that built nothing are drawn (seed 20261031) and weighted ×10. Most lots build nothing, so this keeps the fits fast without changing the expected totals.

## Model 1: no-reform baseline (pace)

- **Rows and traits:** as in pace round 2 (`run_tod_pace_loop.py`): before windows of every city, plus no-reform cities' after windows. Traits any state has, plus the place's past permit pace from the permit survey. All 13 cities, now that the holdout read is done.
- **Outcome:** homes per lot over 5 years.
- **Tests:**
  - held-out city (leave one city out);
  - later years (fit on before windows; predict the no-reform cities' after windows).
- **Score:** median |log(predicted ÷ actual)| of city-window totals, with the permit-survey "same pace as before" as the benchmark.

## Model 2: TOD prediction (share model, round 8 design as in Wisconsin net round 4)

- **Two fits per method:**
  - law on: upzoned lots after the reform;
  - law off: all other lots before the reform, plus no-reform cities.
  - Outcome: homes per acre, with acres capped at 2.97 when predicting.
- **Leave one of the 9 reform cities out.** Scores:
  - median |log(predicted share after ÷ actual)| on upzoned lots, against "same share as before";
  - calibration K measured per method (as round 4).
- **Wisconsin:** statewide net. Bound A is 0; bound B is raw and calibrated with the method's own K. Variant a.

## Reported for each method

Scores on both tests, worst miss, fit time, and the Wisconsin numbers. One seed per method; gradient boosting's seed spread is known from round 4.
