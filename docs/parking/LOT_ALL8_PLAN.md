# Parking: 8 methods on lots with all tract variables, plan written before counting

Written 2026-10-28 by the parking conductor, at Ryan's request ("sure", answering whether to run all 8 methods with the 90+ tract variables on the lot data). The parking lot test ([LOT_TEST_RESULTS.md](LOT_TEST_RESULTS.md)) is known. This test is new. Changes go in the last section with a date and a reason.

## Setup

- **Lots:** TOD's lot table (`data/processed/tod_lot_model/lots.parquet`), with lots TOD marks as upzoned left out.
- **Parking reform lots:** as in the lot test.
  - Seattle: inside a hub or residential urban village.
  - Chicago: within 402 m of a station.
  - Every other lot has 0.
- **Inputs:**
  - TOD's lot traits: size, width, prior floor area, use, distance to station, homes on the lot, built before, tract rent, value and income, building-to-land value where available, and the two nearby-transit counts;
  - TOD's 91 tract variables (`v_` columns);
  - city indicators;
  - the parking flag.
- **Model:** two parts, as in TOD's run C. Part 1 is the chance a lot gets new homes after the reform (`builds_after`). Part 2 is homes if it builds (log of `units_after`).
- **Predicted extra homes in a city:** the sum over its reform lots of predicted homes with the flag set to 1, minus predicted homes with the flag set to 0.
- **Actual extra homes:** reform lots' homes after minus before, minus the same change for comparison lots scaled to the reform lots' count. TOD's `units_before` and `units_after` are used, with each lot weighted by 1 ÷ its appearances.

## Methods

The same 8 as TOD:
- weighted regression;
- lasso;
- elastic net;
- a depth-3 tree;
- random forest;
- boosting;
- causal forest (separate forests for reform and comparison lots, predicting each lot's change);
- 50 nearest neighbours.

Two changes to keep run time reasonable:
- **Boosting:** histogram gradient boosting.
- **Training lots:** at most 60,000 per fit, drawn at random with seed 20261028. All lots of the training reform city are always kept.

## Test

- **Held out:** Seattle, then Chicago. Each is predicted from every other city, so the parking flag varies only in the other reform city.
- **Plain baseline:** the training reform city's actual extra homes per reform lot × the held-out city's reform lots.
- **Pass rule:** a method passes if its error in extra homes is below the baseline's in both held-out cities.

## Use

- **If a method passes:** it goes to Ryan as a candidate for predicting Wisconsin lots near transit.
- **If none passes:** this is reported, and the tool keeps its range.

## Changes after writing
