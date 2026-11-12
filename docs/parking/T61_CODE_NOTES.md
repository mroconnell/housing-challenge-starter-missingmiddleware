# Test 61 code notes

Script: `scripts/run_parking_t61_forest.py`. Tests (made-up data only): `tests/test_parking_t61.py`.
Plan: CAUSAL_FRAMEWORK_PLAN.md, "Test 61" and "Test 61 audit fixes" (the fixes override the text above them).

## What it reuses, unchanged

| Piece | Source |
|---|---|
| Forest | `run_parking_expanded.predict("causal forest (honest)")`: 500 trees, leaf 5, honest halves |
| Fold scheme and seeds | Test 54: 10 folds x 20 repeats; fold order seed 20261105 + repeat; forest seed 20261105 + 1000 x repeat + fold |
| Dose freeze | `parking_dose_common.require_frozen_doses` (and the hash must start 39a33135) |
| Places, effects, weights | `run_parking_dose.Work` (data/processed/dose/<outcome>_ref) and `run_parking_dose.pooled_mask` |
| Dose fit | `parking_dose_common.beta`: sum(w d e) / sum(w d^2), through the origin |
| 2010 population | Test 53 / Test 54 Gazetteer lookup; ACS population (working copy) as fallback |
| Area class | `reference/parking_place_ruca_traits.csv`, `area_class6` (Test 53's six classes) |

## Choices

1. **Places per cell.** The dose fit set: the 74 plus pooled new places with dose above 0 for that outcome.
   - Main also needs an included main effect (as the dose fit). D needs a finite D effect.
   - Dose-0, alone and wait places are out. Rows with weight 0 are dropped (they score nothing).
   - The same list goes to the forest and both benchmarks. Places used are reported per cell.
   - `reference/parking_t61_places.csv` lists every place, cell and reason (no effects in it).
2. **Missing traits.** Filled with the training-fold median (audit fix 4). No place is dropped for a missing trait.
   - Population: Gazetteer 2010, else ACS population; the source is listed per place.
   - Area class not known: all 5 indicators are missing, then median-filled.
3. **Area class coding.** One-hot, 5 columns, main city is the base (as Test 54).
4. **Trait sets.**
   - 3 traits (judged): dose, log10 2010 population, area class.
   - 4 traits (extra): adds rate before repeal. It is inside the effect too (Test 54's denominator caveat).
5. **D weights.** D effects winsorised 5/95 and target-state mix weights, both computed once over the cell's places.
   - They are not redone inside each training fold. This follows Test 54.
6. **Dose-scaled benchmark.** Beta refitted through the origin on each training fold, same effects and weights.
   - Prediction for a held-out place: beta x its dose.
7. **Per-repeat MAE.** Pools all 10 folds' held-out places: sum(w |error|) / sum(w).
   - This equals Test 54's test-weight-weighted average of fold MAEs.
8. **Gain.** Per repeat: 1 − MAE_forest / MAE_benchmark.
   - `mean_gain` (the mean of 20 per-repeat gains) is the number judged.
   - `gain_of_mean_maes` (Test 54's form) is shown beside it.
9. **Pass rule.** Mean gain at least 5% and gain above 0 in at least 80% of repeats.
   - Judged only for 2–4 units, 3 traits, against one weighted average.
   - Two chances: main and D. Either passing is a pass.
   - All other cells are reported only.
10. **Shuffle check.** 20 shuffles of the trait rows across places (seed 20261105 + 6100 + shuffle).
    - Shuffle s uses repeat s's folds and forest seeds. 3 traits, against one average.
    - Reported: the mean, range and share above 0 of the 20 chance-alone gains.
    - Also: the share of shuffles whose gain is at least the observed mean gain.
    - Dose in the benchmark is not shuffled. Only the forest's inputs are.
11. **Permutation importance.** Only if the judged rule passes, for the passing cells.
    - Second pass with the same seeds, so the same forests. The check asserts the MAE matches.
    - In each test fold, each trait's columns are permuted together (seed 20261105 + 6161 + 1000 x repeat + fold).
    - Area class's 5 columns move as one trait.
    - Permuted rows are stacked under the real test rows in one predict call. Predictions are row by row, so the fit is unchanged.
    - Reported: share increase in held-out MAE, mean and range over repeats.

## Outputs

| File | Rows |
|---|---|
| `reference/parking_t61_results.csv` | 16 cells (2 outcomes x 2 methods x 2 trait sets x 2 benchmarks) + 4 shuffle rows; asserted |
| `reference/parking_t61_reading.csv` | 8 rows (outcome x trait set x benchmark): main, D, verdict |
| `reference/parking_t61_repeats.csv` | per repeat and per shuffle MAEs |
| `reference/parking_t61_places.csv` | every place in each cell, with status and trait sources |
| `reference/parking_t61_importance.csv` | only when the judged rule passes |

Units: MAE in homes permitted per 1,000 existing homes a year. Gains are shares (0.05 = 5%).
