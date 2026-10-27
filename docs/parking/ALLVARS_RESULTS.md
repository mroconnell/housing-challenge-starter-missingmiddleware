# Parking all-variables test: results

Written 2026-10-27 by the parking conductor. Plan: [ALLVARS_PLAN.md](ALLVARS_PLAN.md), written before any model ran. Script: `scripts/run_parking_allvars.py`. Values: `reference/parking_allvars_values.csv` (55 variables kept, each with values for at least 15 places; rerun 2026-10-27 without the two OpenStreetMap surface-parking variables, which the project does not distribute). Scores: `reference/parking_allvars_models.csv`.

## Answer

**Three tree models passed the registered rule, but only just, and they do not survive simple checks.** I recommend not using them.

## The registered test

71 places, 55 variables. Each score is the error on left-out places, against one average for all places, from 10-fold cross-validation repeated 20 times with seed 20261027.

| Model | Change in error vs one average | Repeats beating the average (of 20) | Passes the rule |
| --- | ---: | ---: | --- |
| Lasso | −1.6% (worse) | 8 | No |
| Elastic net | −1.0% (worse) | 5 | No |
| Random forest | +6.8% | 19 | Yes |
| Gradient boosting | +8.4% | 17 | Yes |
| Honest causal forest | +6.4% | 17 | Yes |

## Checks after the result

These checks were not in the plan; they were run because the result was a close pass.

| Check | Random forest | Gradient boosting |
| --- | ---: | ---: |
| Registered run (seed 20261027, 20 repeats) | +6.8% | +8.4% |
| Other random splits: seeds 1, 2 and 3 (10 repeats each) | +5.0%, +1.7%, +3.0% | +6.3%, +5.3%, +6.9% |
| Without San Francisco | +0.4% | +3.7% |
| Each place weighted equally (not by homes) | −4.4% | −10.1% |

- **Different splits:** the random forest falls below the 5% bar on two of three other seeds. Gradient boosting stays at 5–7%.
- **San Francisco:** it carries 13% of the weight. Without it, the forest's gain disappears and boosting's falls to 3.7%, under the bar.
- **Equal weights:** both models predict worse than one average.

**What the forest leaned on.** The share of renters paying 30% or more of income in rent accounted for about half of the forest's splits. The share of small homes (1–3 rooms) came next. Both are high in San Francisco, where the effect was strongly negative.

## Reading

The models "pass" because they learned San Francisco, not because they found a pattern that holds across places. A model that sizes Wisconsin's effect by rent burden, on the strength of one city, would not be defensible. The finding of the three earlier rounds stands: no variable or model reliably tells places apart, so the scenario keeps one average.

## Side by side with TOD

TOD's island-size result, labelled "TOD: frequent-service coverage, per rezoned unit": it failed, beating the plain average in 1 of 6 fitted cities and losing on both held-out cities (`docs/tod/NET_EFFECT_RESULTS.md`). TOD's all-variables test used 91 variables: 78 from the Census survey across 46 tables, plus 13 TOD traits. Every model failed. Mean error over 6 fitted cities, against 0.856 for the plain average (extra homes per eligible acre per year): lasso 1.134, elastic net 1.075, random forest 1.136, gradient boosting 1.046, causal forest 0.884 (`docs/tod/`; variable map in `reference/tod_allvars_variable_map.csv`). Both scenarios reach the same conclusion: the data do not support different effects for different kinds of place.
