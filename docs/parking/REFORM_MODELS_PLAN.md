# Parking: full set of reform-prediction models, plan written before running

Written 2026-10-31 by the parking conductor. Ryan: choose a baseline, then "run all the models for each reform prediction, aiming to successfully predict citywide homes resulting from reform incremental to the baseline or including the baseline", then look for errors, fix and rerun, and finally compare the models as possible lines for the tool. Ryan, 2026-10-31: "follow the auditor's recommendations for now". So the central baseline is same pace (122,619), with a side line "if recent strength continues" (130,969). The tool does not change from these runs without Ryan's approval. No result below has been computed before this file was committed.

## Data

- **Rows:** the no-reform model's round 6 data (homes from the ACS release ending at the origin). Never-reformed place-origins are included, as are reformed places' place-origins whose window ends before the repeal.
- **Reform rows:** a dated, apartment-scale repeal (V7 coding) from 1 year before to 2 years after the origin, as in the Wisconsin net rounds. That gives 28 places and 58 rows, outside Wisconsin.
- **Origins:** 2016–2019, with outcomes in years 2–6 after the origin. Wisconsin is excluded from fitting.

## Models (12)

Each of the eight machine-learning models gets the repeal trait as an input, alongside the baseline models' inputs.

| # | Model | Reform effect |
| --- | --- | --- |
| 1 | M0 same pace | none (the baseline) |
| 2 | M0L same pace × level | none |
| 3 | M0 + route A high end | +1.49 permits per 1,000 homes per year |
| 4–11 | Poisson regression, lasso, elastic net, depth-3 tree, random forest, boosted trees, honest forest, 50 nearest neighbours | prediction with the trait on, minus off |
| 12 | Causal forest (`econml` CausalForestDML) | effect of the trait given the place's inputs; outcome and trait models are boosted trees |

The baseline round 4 settings are used (each model's most common cross-validated choice). There is no retuning, which keeps the 28 refits affordable.

## Test: leave one reform place out

For each of the 28 reform places:
1. Every model is fitted on all rows except that place's.
2. The place's actual permits (years 2–6 after the origin) are predicted with the trait on. This is the "including the baseline" prediction.
3. The incremental prediction is on minus off.

Reported for each model:
- the summary score (median |log|) over the 58 held-out reform rows;
- the total ratio (predicted ÷ actual);
- the share of rows where it beats M0;
- the mean on−off, in homes per place per year.

## Wisconsin net, 2027–2031

For each model and each of the 28 refits, the sum over Wisconsin places that still have minimums of (on − off) × 5, scaled to the state by 122,619 ÷ same pace. Reported as the median and the 5th–95th percentile of the 28 refits: the jackknife spread.

## Fake-reform placebo

28 never-reformed places get a fake repeal year, drawn from the real ones, with the same window. Every model is fitted and read out for Wisconsin in the same way, with 5 seeds. A real net inside the fake range is noise.

## Checks after each run (flag, never stop)

- Negative or non-finite predictions.
- The worst held-out miss per model, traced.
- Wisconsin nets more than 25% of the baseline, traced to their places.
- A rerun under a different Python hash seed.

## Changes after writing
- **2026-11-01, dependency note:** econml is no longer a project dependency. The causal forest (CausalForestDML) and the honest forest are imported only when used. Their results are a one-off comparison, as in TOD.
