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

## Trait ranking with and without San Francisco (2026-11-04; check after the result, not a new test)

Script `scripts/check_parking_allvars_importance.py`, committed before its run. Registered set-up: 71 places, 55 variables, 10-fold cross-validation × 20 repeats, seed 20261027, all six tools in the loop. The with-SF, home-weighted gains reproduce the registered run (forest +6.8%, boosting +8.4%). Importance: rise in held-out mean absolute error when one trait is shuffled within the left-out places (permits per 1,000 existing homes a year). Outputs: `reference/parking_allvars_importance.csv`, `reference/parking_allvars_importance_gains.csv`.

**Gain against one average** (share lower error; repeats beating the average, of 20)

| Model | With SF, home weights | Without SF, home weights | With SF, equal weights | Without SF, equal weights |
| --- | --- | --- | --- | --- |
| Random forest | +6.8% (19) | +2.7% (14) | −4.0% (0) | −4.4% (0) |
| Gradient boosting | +8.4% (17) | −1.6% (9) | −6.2% (3) | −7.9% (0) |

**Top 5 traits** (rank with SF → without SF)

| Model, weights | Top 5 with SF | Moves without SF |
| --- | --- | --- |
| Forest, homes | rent burden 30%+, unemployment, median age, renters in post-2000 homes, leave for work 7–9 am | rent burden stays 1st; leave 7–9 am 5→23; permit rate before 6→54; small homes (1–3 rooms) 49→2 |
| Boosting, homes | rent burden 30%+, crowding, labour-force participation, household size, median age | rent burden and crowding stay 1st–2nd; labour force 3→46; household size 4→34; near-transit share 7→52 |
| Forest, equal | small homes (1–3 rooms), vacancy, leave after 9 am, rent burden 30%+, unemployment | vacancy 2→53; the rest stay in the top 10 |
| Boosting, equal | small homes, vacancy, leave after 9 am, household size, permit volatility | mostly stable; rent burden 9→31; permit rate before 11→3 |

**Reading.**
- **Rent burden leads under home weights, with or without SF.** The models lean on it. But without SF they barely beat one average (forest +2.7%) or lose to it (boosting −1.6%), so leaning on it does not buy accurate predictions.
- **Under equal weights every model loses to one average,** with or without SF. The top traits there (small homes, vacancy, commute timing) describe what the models fitted to, not a pattern that predicts new places.
- **Ranks move a lot** (for example the before-repeal permit rate, 6th → 54th, and small homes, 49th → 2nd), partly because related traits share credit and each fold leaves out only about 7 places. The gains, not the ranks, show the models do not predict new places.
- **Why these gains differ from the earlier checks table** (forest +0.4% and boosting +3.7% without SF; −4.4% and −10.1% under equal weights): that check used seed 1, 10 repeats and three tools. This run uses the registered seed 20261027, 20 repeats and all six tools, so the folds and model seeds differ. Gains move by up to about 5 points with the split. Both runs agree on the direction.
- **Registered rule:** it was met in the registered run. The scenario keeps one average because the pass depends on San Francisco (post hoc checks).
- **Conclusion unchanged:** no trait reliably tells places apart, so the scenario keeps one average. Importances say what a model used, not what drives parking effects.

**Direction of the top traits (descriptive, added for Ryan 2026-11-04).** Average effect in the half of places above vs below each trait's median, in permits per 1,000 existing homes a year. The gap is above minus below, with a 90% place-bootstrap range (2,000 draws, seed 20261104, median split redone in each draw). Built by `scripts/check_parking_allvars_direction.py` → `reference/parking_allvars_direction.csv`. Shown with SF.

| Trait | Homes-weighted: above / below | Gap (90% range) | Equal weights: above / below | Gap (90% range) |
| --- | --- | --- | --- | --- |
| Permit rate before repeal | −2.41 / +1.47 | −3.88 (−7.47 to −0.00) | −0.32 / +1.21 | −1.53 (−6.00 to +1.23) |
| Rent burden 30%+ | +1.93 / −2.24 | +4.17 (+1.21 to +9.49) | +0.47 / +0.44 | +0.03 (−2.76 to +4.48) |
| Crowded homes | −3.31 / +3.37 | −6.67 (−10.15 to −1.04) | −0.77 / +1.65 | −2.43 (−5.30 to +2.10) |
| Labour-force participation | −1.85 / +1.17 | −3.02 (−6.31 to +0.77) | +0.68 / +0.24 | +0.44 (−3.42 to +3.78) |
| Small homes (1–3 rooms) | −1.20 / −0.78 | −0.42 (−4.65 to +3.34) | +1.93 / −0.98 | +2.91 (−1.58 to +5.62) |
| Vacancy | +0.02 / −2.59 | +2.61 (−2.86 to +7.22) | +0.41 / +0.50 | −0.09 (−3.76 to +2.90) |

- **Without SF,** most cells move by less than about 0.9. Three things change:
  - vacancy above the median goes from +0.02 to +0.91;
  - small homes flip order (−0.76 vs −0.83);
  - labour force under equal weights goes from +0.68 / +0.24 to +1.17 / −0.15.
  - Rent burden's homes-weighted gap stays clear of 0 (+0.58 to +10.19). Crowding's and the permit rate's ranges then touch 0.
- **Reading:**
  - Two traits keep their sign under both weightings: the before-repeal permit rate and crowding. Hotter or more crowded places show lower effects.
  - Under equal weights, no gap is larger than the noise.
  - Rent burden and crowding gaps exclude 0 only under home weights, so they rest on a few big places.
- **The permit-rate pattern may be regression to the mean,** not a weaker response to repeal. The market-heat bake-off in method 2 tests that. Test P3 found places rising into repeal, which points the same way.
- **Selection caveat:** these 6 traits were picked because they ranked high out of 55, so some patterns will appear by chance. The CSV has 24 ranges; at 90%, about 2 or 3 would exclude 0 by chance alone. With SF, 2 of 12 exclude 0 and the permit rate only touches 0, which is about what chance gives. These are associations, not causes.
