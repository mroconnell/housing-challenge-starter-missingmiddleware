# Parking all-variables test: results

Written 2026-10-27 by the parking conductor. Plan: [ALLVARS_PLAN.md](ALLVARS_PLAN.md), written before any model ran. Script: `scripts/run_parking_allvars.py`. Values: `reference/parking_allvars_values.csv` (57 variables kept, each with values for at least 15 places). Scores: `reference/parking_allvars_models.csv`.

## Answer

**Three tree models passed the registered rule, but only just, and they do not survive simple checks.** I recommend not using them.

## The registered test

71 places, 57 variables. Each score is the error on left-out places, against one average for all places, from 10-fold cross-validation repeated 20 times with seed 20261027.

| Model | Change in error vs one average | Repeats beating the average (of 20) | Passes the rule |
| --- | ---: | ---: | --- |
| Lasso | −1.7% (worse) | 7 | No |
| Elastic net | −0.9% (worse) | 6 | No |
| Random forest | +6.3% | 18 | Yes |
| Gradient boosting | +8.2% | 17 | Yes |
| Honest causal forest | +6.2% | 17 | Yes |

## Checks after the result

These checks were not in the plan; they were run because the result was a close pass.

| Check | Random forest | Gradient boosting |
| --- | ---: | ---: |
| Registered run (seed 20261027, 20 repeats) | +6.3% | +8.2% |
| Other random splits: seeds 1, 2 and 3 (10 repeats each) | +4.4%, +1.5%, +2.3% | +3.9%, +3.9%, +4.0% |
| Without San Francisco | −0.6% | +1.3% |
| Each place weighted equally (not by homes) | −4.8% | −10.4% |

- **Different splits:** the gain falls below the 5% bar for both models.
- **San Francisco:** it carries 13% of the weight. Without it, the gain all but disappears.
- **Equal weights:** the models predict worse than one average.

**What the forest leaned on.** The share of renters paying 30% or more of income in rent accounted for about half of the forest's splits. The share of small homes (1–3 rooms) came next. Both are high in San Francisco, where the effect was strongly negative.

## Reading

The models "pass" because they learned San Francisco, not because they found a pattern that holds across places. A model that sizes Wisconsin's effect by rent burden, on the strength of one city, would not be defensible. The finding of the three earlier rounds stands: no variable or model reliably tells places apart, so the scenario keeps one average.

## Side by side with TOD

TOD's island-size result, labelled "TOD: frequent-service coverage, per rezoned unit": it failed, beating the plain average in 1 of 6 fitted cities and losing on both held-out cities (`docs/tod/NET_EFFECT_RESULTS.md`). TOD's all-variables test is still running, and its result will be added here when it lands.
