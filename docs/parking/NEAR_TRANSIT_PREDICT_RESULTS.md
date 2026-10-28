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

## Added after the result (not in the plan): hold out 10% of each region

Ryan asked: "why not just hold out 10% of the data from each region?" Each fold held out 10% of every region's areas (10 folds, 20 repeats, seed 20261028).

| Tool | All areas | Seattle | Minneapolis | California | Repeats beating one average |
| --- | ---: | ---: | ---: | ---: | ---: |
| Weighted regression | +10.4% | +5.4% | +21.5% | +10.4% | 20 of 20 |
| Lasso | +11.8% | +6.0% | +20.3% | +12.1% | 20 of 20 |
| Random forest | +12.0% | −9.4% | +8.9% | +15.2% | 20 of 20 |

**What the models learned.** Fitted on all 221 areas, the regression gives the following weights, in extra homes permitted per 1,000 existing homes per year:
- **Prior gap:** −0.57 per 1 unit of prior gap. Areas that outgrew their surroundings before the reform outgrew them by less afterwards. The same sign holds in each region: −0.97 in Seattle, −1.94 in Minneapolis, −0.65 in California.
- **Rail:** +1.98.
- **Size:** −2.59 for each tenfold increase in homes.

**Reading.** The models predict well mainly because fast growers slow down. That pattern would also appear without any reform, so it is not a parking effect. Telling the two apart needs the same test on near-transit areas that did not reform.
