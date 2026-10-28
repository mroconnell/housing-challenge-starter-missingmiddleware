# Parking: lot test redone TOD's "run E" way, plan written before counting

Written 2026-10-28 by the parking conductor, at Ryan's request to check TOD's lot-model fixes against the parking lot runs and decide whether a parking test can run the same way.

## Problems found in the parking 8-method run ([LOT_ALL8_RESULTS.md](LOT_ALL8_RESULTS.md))

1. **Mixed density units.** The run used TOD's feature builder before TOD fixed the density column. That column held feet of height in Charlotte and a district ordering in Philadelphia and Los Angeles. Upzoned lots were left out, so this affected only the density level, but that level is an input in every city.
2. **"Guess zero."** The tree, forest and boosting methods predicted 0 or close to it. The parking flag is rare and they ignored it, so the reform's effect was never estimated. Those "passes" came from predicting zero against a poor baseline.

## Redo

- **Features:** TOD's fixed builder (`features()` in `scripts/run_tod_lot_model.py`, with density ranked within each city). The inputs are otherwise as in [LOT_ALL8_PLAN.md](LOT_ALL8_PLAN.md).
- **Two models for every method:**
  - one fitted only on parking-reform lots;
  - one fitted only on lots without the reform.

  A held-out reform lot's extra homes = reform model's prediction − no-reform model's prediction. Each model has two parts (the chance of building, then homes if built), except the causal forest, which predicts each lot's change directly as before.
- **Methods:** the same 8 as before.
- **Training:**
  - the reform model uses the other reform city's reform lots, the only reform lots available;
  - the no-reform model uses all non-reform lots in every city except the held-out one, capped at 60,000 at random (seed 20261028).
- **Held out:** Seattle, then Chicago.
- **Pass rule (TOD's new rule, adapted to 2 cities):**
  - beat the plain average on mean miss;
  - beat "guess zero" on mean miss;
  - beat the plain average in both held-out cities.
- **Plain average:** the other reform city's actual extra homes per reform lot.

## Expected limit

The reform model learns from one city each time, so it is close to copying that city. A pass would therefore show a pattern that carries from Seattle to Chicago and back.

## Changes after writing
