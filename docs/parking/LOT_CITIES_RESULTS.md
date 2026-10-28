# Parking: lot-level test with four reform cities, results

Written 2026-10-28 by the parking conductor. Plan: [LOT_CITIES_PLAN.md](LOT_CITIES_PLAN.md), committed before counting, with changes logged before outcomes. Scripts: `scripts/fetch_parking_lot_cities.py`, `scripts/run_parking_lot_cities.py`. Outputs (aggregates only): `reference/parking_lot_cities_effects.csv`, `reference/parking_lot_cities_predict.csv`, `reference/parking_lot_cities_predict_summary.csv`.

## Answer

- **Effects on lots, by city:** two cities near zero (San Francisco, Chicago), one small and uncertain gain (Buffalo), and one clear gain (Seattle).
- **Prediction:** no method predicted the held-out cities better than guessing zero. None passes.

## Effects

Net new homes permitted per 1,000 lots per year. The effect is the pinched lots' change (after minus before) minus the comparison lots' change.

| City | Pinched lots / comparison lots | Pinched, before → after | Comparison, before → after | Effect (90% range) | Extra homes per year, whole city |
| --- | --- | --- | --- | --- | ---: |
| San Francisco (2019) | 81,080 / 73,544 | 4.1 → 4.5 | 0.2 → 0.3 | +0.3 (−3.3 to +3.9) | +21 |
| San Francisco, with accessory-unit alterations | same | 9.3 → 14.1 | 1.8 → 2.7 | +4.0 (−0.2 to +8.6) | +322 |
| Buffalo (2017) | 36,326 / 37,971 | 4.0 → 6.9 | −0.2 → 0.2 | +2.5 (−0.8 to +6.3) | +90 |
| Chicago (2015) | 33,719 / 31,613 | 2.1 → 7.0 | 3.7 → 11.2 | −2.6 (−5.2 to −0.2) | −86 |
| Seattle (2012) | 2,450 / 1,547 | 20.8 → 58.2 | 3.0 → 4.7 | +35.7 (+6.5 to +75.7) | +87 |

## Prediction on unseen cities

Each city is held out in turn. Separate models are fitted for pinched and comparison lots on the other three cities. The predicted extra homes are the pinched model minus the comparison model, over the held-out city's pinched lots.

| Method | Mean miss, extra homes per year | Cities beating plain average (of 4) | Passes |
| --- | ---: | ---: | --- |
| Plain average | 465 | — | — |
| Guess zero | 71 | — | — |
| Weighted regression | 188 | 3 | No |
| Lasso | 211 | 3 | No |
| Elastic net | 125 | 3 | No |
| Depth-3 tree | 360 | 2 | No |
| Random forest | 589 | 2 | No |
| Boosting | 283 | 4 | No |
| Causal forest | 185 | 4 | No |
| 50 nearest neighbours | 281 | 4 | No |

Every method misses by more than guessing zero.

## Reading

- **In San Francisco, parking repeal added almost nothing on new buildings.** The accessory-unit gain comes from a separate program that started in 2014.
- **Buffalo's small gain came with its full rezoning.**
- **Seattle is still the outlier.**
- **No lot model carries a gain from one city to another,** so there is no lot-level predictor for Wisconsin.
- **The tool does not change.**
