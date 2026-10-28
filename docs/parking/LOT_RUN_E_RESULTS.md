# Parking: lot test redone TOD's run-E way, results

Written 2026-10-28 by the parking conductor. Plan: [LOT_RUN_E_PLAN.md](LOT_RUN_E_PLAN.md), committed before counting. Script: `scripts/run_parking_lot_run_e.py`. Outputs: `reference/parking_lot_run_e_by_city.csv`, `reference/parking_lot_run_e_results.csv`.

## Answer

**One method, the random forest, passes, but narrowly and with a caveat that weakens it.** No other method passes.

## Results

Each figure is extra homes on the held-out city's parking-reform lots: 5 years after against before, compared with nearby lots without the reform.

| Method | Seattle predicted (actual +378) | Chicago predicted (actual −354) | Mean miss | Passes |
| --- | ---: | ---: | ---: | --- |
| Plain average (the other city's rate) | −26 | +5,189 | 2,973 | — |
| Guess zero | 0 | 0 | 366 | — |
| Weighted regression | +247 | +6,333 | 3,409 | No |
| Lasso | +165 | +5,294 | 2,930 | No |
| Elastic net | +340 | +4,274 | 2,333 | No |
| Depth-3 tree | +1,374 | +3,625 | 2,487 | No |
| **Random forest** | **+404** | **+232** | **306** | **Yes** |
| Boosting | +1,171 | +25,649 | 13,398 | No |
| Causal forest | +901 | +59,734 | 30,305 | No |
| 50 nearest neighbours | +475 | +2,323 | 1,387 | No |

To pass, a method's mean miss had to beat both the plain average and "guess zero", and it had to beat the plain average in both cities.

## Caveats

- **The margin is small.** The forest's mean miss is 306 homes, against 366 for guessing zero.
- **Only 2 held-out cities.** The reform model learns from one city each time.
- **The two models come from different cities.** The reform model is fitted on one city's reform lots. The no-reform model is fitted on non-reform lots in all other cities. So the gap between them can include differences between cities, not only the parking reform.
- **Most methods badly over-predict Chicago,** which has 33,719 reform lots.

## Reading

This is not yet a model to use for Wisconsin. It suggests that, with more reform cities, TOD's method might work for parking. The next step is to add San Francisco, Buffalo, Minneapolis and Hartford (owner approved, 2026-10-28).
