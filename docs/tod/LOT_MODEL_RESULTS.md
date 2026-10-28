# Lot-level model: results

Run 2026-10-28 against [LOT_MODEL_PLAN.md](LOT_MODEL_PLAN.md) (changes in its section 9; pass rule = regional total only, owner's decision recorded before results). Code: [scripts/run_tod_lot_model.py](../../scripts/run_tod_lot_model.py). Outputs: `reference/tod_lot_model_by_city.csv`, `reference/tod_lot_model_results.csv`. The lot table (about 356,000 lots in 8 cities) is local only.

## Summary

- **Neither model passes.**
  - The boosted-tree model predicts the two held-out cities better than the plain average: Chicago's error is 103 homes against 457, Madison's 443 against 677.
  - But across the six cities taken in turn it does worse on average (mean error 2,362 homes against 1,791), winning in only 2 of 6.
- **The simpler model (logistic plus linear) breaks down.** Its size equation blows up on Charlotte's large lots (more than 7 million homes predicted), even with the lot ceiling. It wins in 3 of 6 cities, and it predicts about zero extra homes for both holdouts.
- **Lot ranking is weak:** a lot that built is ranked above one that didn't 55–70% of the time. That is no longer part of passing.
- **Nothing changes.** The TOD numbers (AQ-055) stay at 171, 2,509 and 17,148.

## Extra homes on upzoned land, by city (5 years after against before, against comparison lots)

| City | Role | Upzoned acres | Actual extra homes | Plain average predicted | Boosted model predicted |
| --- | --- | ---: | ---: | ---: | ---: |
| New York | fold | 574 | 3,763 | 823 | 1,055 |
| Philadelphia | fold | 642 | 3,341 | 1,058 | 354 |
| Charlotte | fold | 818 | 562 | 2,465 | 5,560 |
| Saint Paul | fold | 163 | 106 | 407 | 51 |
| Seattle | fold | 68 | −83 | 168 | 248 |
| Los Angeles | fold | 798 | −358 | 2,709 | 2,735 |
| **Chicago** | holdout | 251 | 144 | 601 | **42** |
| **Madison** | holdout | 615 | 794 | 1,471 | **351** |

## Reading it

- **Cities still differ more than lot traits explain.** New York and Philadelphia built far more than any model expected. Charlotte and Los Angeles built far less. The same kinds of lots behaved very differently in different markets.
- **The boosted model's holdout wins are real but not enough.** It was closer for Chicago and Madison, both cities with modest responses. It missed badly on the big responders, the cities where the total matters most.
- **The plain average is itself poor here.** It misses every city by hundreds to thousands of homes. That is the same lesson as before: a single per-acre rate doesn't carry from city to city.
- **What might help next:**
  - city-level market heat (recent price or rent growth) as a lot trait;
  - a feasibility measure with comparable land values. Only New York and Chicago have pre-reform values here.

  Both would be new tests, written down first.
