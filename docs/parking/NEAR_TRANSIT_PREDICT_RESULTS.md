# Parking: near-transit prediction test, results

Written 2026-10-28 by the parking conductor. Plan: [NEAR_TRANSIT_PREDICT_PLAN.md](NEAR_TRANSIT_PREDICT_PLAN.md), committed before counting. Script: `scripts/run_parking_near_transit_predict.py`. Outputs: `reference/parking_near_transit_units.csv` (each area's inputs and outcome), `reference/parking_near_transit_predict.csv` (scores).

## Answer

**No tool predicted held-out regions. Option B and the Seattle-only rate are not supported for prediction.**

## Areas

| Region | Areas | Homes in areas | Share with rail | Average extra homes permitted per 1,000 existing homes per year (home-weighted) |
| --- | ---: | ---: | ---: | ---: |
| Seattle urban villages | 24 | 60,039 | 29% | +0.06 |
| Minneapolis rail station areas | 12 | 16,913 | 92% | +3.46 |
| California near major transit stops | 185 | 1,276,507 | 57% | −0.09 |

Single areas swing widely, from −164 to +453 per 1,000 homes per year. Areas that grew fast before the reform often grew less fast after it, for example Greenwood-Phinney Ridge, Lake City and Minneapolis's West Bank.

## Test: fit on two regions, predict the third

Change in prediction error compared with using one average. Positive means better.

| Held-out region | Weighted regression | Lasso | Random forest |
| --- | ---: | ---: | ---: |
| Seattle | +3.5% | +3.8% | −9.7% |
| Minneapolis | +22.8% | +22.0% | +8.7% |
| California | −85.7% | −131.8% | −98.7% |
| All held-out areas, pooled | −69.5% | −107.8% | −82.6% |

The pass rule needed a 5% gain in at least 2 of the 3 regions and in the pooled total. No tool passes.

Within a single region (10-fold cross-validation, 20 repeats):
- **Seattle and Minneapolis:** no tool beats one average.
- **California:** the regression and lasso do 19% better, but the same patterns fail in Seattle and Minneapolis.

## What it means

- Near-transit gains in one region do not carry over to another.
- The near-transit rate in option B rests on areas whose results cannot be predicted from rail, size or past growth.
- The tool keeps its current range unless Ryan decides otherwise.

## Changes from the plan

- **Minneapolis station areas:** platforms were merged by station name and areas with fewer than 100 homes were dropped. That left 12 areas instead of one for each station.
- **California rail:** marked from rail stops inside each city's or county's boundary, not only inside its near-transit land.
