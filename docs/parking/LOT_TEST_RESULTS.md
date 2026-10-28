# Parking: lot-level test, results

Written 2026-10-28 by the parking conductor. Plan: [LOT_TEST_PLAN.md](LOT_TEST_PLAN.md), committed before counting. Script: `scripts/run_parking_lot_test.py`, on TOD's lot table. Outputs (aggregates only): `reference/parking_lot_effects.csv`, `reference/parking_lot_predict.csv`.

## Answer

- **Seattle:** after the 2012 reform, fewer lots in the urban villages got new homes, but more homes were permitted. The gains came on larger lots. Small and narrow lots did worse, not better.
- **Chicago:** no change on lots near stations after the 2015 ordinance.
- **Prediction:** knowing a lot was covered by a parking reform did not improve predictions in an unseen city. It fails the rule.

## Effects

All figures are per 1,000 lots per year: reform lots' change (after minus before) minus comparison lots' change. Lots TOD marks as upzoned are left out.

| City | Lots | Reform lots / comparison lots | Lots built | 90% range | New homes permitted | 90% range |
| --- | --- | --- | ---: | --- | ---: | --- |
| Seattle | All | 2,450 / 1,547 | −4.9 | −11.6 to +0.3 | **+35.7** | **+7.9 to +74.0** |
| Seattle | Narrow (under 10 m wide) | 341 / 33 | −12.8 | −23.3 to −3.5 | −35.7 | −62.1 to −13.3 |
| Seattle | Small (under 0.1 acre) | 958 / 444 | −14.5 | −28.0 to −3.9 | −13.8 | −32.7 to +5.1 |
| Seattle | Larger (0.1 acre or more) | 1,492 / 1,103 | +1.6 | −2.8 to +6.2 | **+67.8** | **+24.8 to +131.0** |
| Chicago | All | 33,719 / 31,613 | −0.1 | −0.6 to +0.5 | −2.6 | −5.2 to −0.3 |
| Chicago | Narrow | 22,860 / 22,145 | −0.0 | −0.7 to +0.6 | −1.2 | −2.6 to +0.1 |
| Chicago | Larger | 9,845 / 8,647 | +0.1 | −0.6 to +0.9 | −6.8 | −14.7 to −0.2 |

The before and after years:
- **Seattle:** 2006–2011 and 2013–2019.
- **Chicago:** 2009–2012 and 2016–2020.

Seattle's narrow-lot comparison group is only 33 lots.

## Prediction on unseen cities

A gradient-boosting model predicts whether each lot is built after the reform, with and without a parking-reform flag. It is trained on every other city.

| Held-out city | Brier score, without → with the flag | Error in predicted count of reform lots built, without → with | Passes (5% better on both) |
| --- | --- | --- | --- |
| Seattle | 0.019 → 0.019 (0.1% better) | 79% → 78% (2% better) | No |
| Chicago | 0.015 → 0.015 (0.1% worse) | 54% → 11% (80% better) | No |

The Brier score is the average squared error of the predicted chance that a lot is built.

## Reading

- **Seattle's gain looks like larger apartment projects** on bigger village lots, not small lots that newly pencilled.
- **Chicago shows nothing.** This matches TOD's finding that Chicago's station areas were already growing.
- **The flag does not travel between cities,** so it cannot be used to predict Wisconsin lots.
- **The tool does not change.**
