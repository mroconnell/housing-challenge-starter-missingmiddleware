# Parking: 8 methods on lots with all tract variables, results

Written 2026-10-28 by the parking conductor. Plan: [LOT_ALL8_PLAN.md](LOT_ALL8_PLAN.md), committed before counting. Script: `scripts/run_parking_lot_all8.py`. Outputs: `reference/parking_lot_all8_by_city.csv`, `reference/parking_lot_all8_results.csv`.

## Answer

**Six of the 8 methods pass the rule, but only by predicting about zero.** The rule compares them with a plain baseline that copies the other reform city's rate, and that baseline is far off. Predicting zero would do just as well. So the test supports the scenario's central estimate of no measurable change. It gives no positive number to use for Wisconsin.

## Results

The training data has 341,682 lots and 112 inputs. Each figure is extra homes on the held-out city's parking-reform lots (5 years after against before, compared with nearby lots without the reform).

| Method | Seattle: predicted (actual +378; baseline −26) | Chicago: predicted (actual −354; baseline +5,189) | Beats baseline in both? |
| --- | ---: | ---: | --- |
| Weighted regression | −44 | +200 | No |
| Lasso | −6 | +1,113 | Yes |
| Elastic net | −19 | +1,166 | Yes |
| Depth-3 tree | 0 | 0 | Yes |
| Random forest | −1 | +82 | Yes |
| Boosting | 0 | +598 | Yes |
| Causal forest | −662 | +59,988 | No |
| 50 nearest neighbours | +61 | +108 | Yes |
| *For reference: predict zero* | *0* | *0* | *Yes* |

The baselines come from the other city:
- **Seattle's baseline (−26):** Chicago's extra homes per reform lot, applied to Seattle's reform lots.
- **Chicago's baseline (+5,189):** Seattle's rate, applied to Chicago's 33,719 reform lots.

## Reading

- **The methods "pass" because they predict near zero.** The baseline copies a rate across two very different cities.
- **No method predicted Seattle's +378.** The best was +61 (nearest neighbours).
- **Two methods broke down on Chicago's 33,719 reform lots.** The causal forest predicted about +60,000, and the linear methods about +1,100.
- **This matches every earlier test.** Lot traits and tract data cannot predict where a parking repeal adds homes. The best guess is no change.
- **The tool does not change.**
