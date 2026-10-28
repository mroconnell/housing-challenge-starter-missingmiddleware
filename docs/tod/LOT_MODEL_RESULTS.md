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

## Runs A, B and C (added 2026-10-28): Bellevue as a third holdout, all 91 census variables, all 8 methods

Plan changes: LOT_MODEL_PLAN section 9, items 8–11, each recorded before its run. Outputs: `reference/tod_lot_model_*` (run A), `*_allvars` (run B), `*_all8` (run C).

**No method passes.** Pass = lower mean error than the plain average across the 6 fold cities **and** a smaller error on each of Chicago, Madison and Bellevue.

| Method | Run | Fold mean error (plain average 1,791) | Fold cities closer (of 6) | Chicago | Madison | Bellevue | Passes |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| Boosting, 22 traits | A | 2,040 | 4 | closer | closer | closer | no |
| Boosting, all variables | B | 2,955 | 3 | closer | closer (by 5 homes) | closer | no |
| Weighted regression | C | over 1 million (Charlotte blow-up) | 3 | closer | not | closer | no |
| LASSO | C | over 1 million | 3 | closer | not | closer | no |
| Elastic net | C | over 1 million | 3 | closer | not | closer | no |
| Regression tree | C | 1,360 | 4 | closer | not | closer | no |
| Random forest | C | 1,355 | 4 | closer | not | closer | no |
| Causal forest (separate forests) | C | **1,126** | 4 | not | not | closer | no |
| Nearest neighbours | C | 1,363 | 4 | closer | not | closer | no |

**Predicted extra homes, run C, selected methods:**

| City | Actual | Plain average | Random forest | Causal forest | Boosting (B) |
| --- | ---: | ---: | ---: | ---: | ---: |
| New York | 3,763 | 823 | 95 | 4,170 | 1,806 |
| Philadelphia | 3,341 | 1,058 | 57 | 1,584 | 839 |
| Charlotte | 562 | 2,465 | 34 | 2,592 | 7,234 |
| Saint Paul | 106 | 407 | 1 | 512 | 87 |
| Seattle | −83 | 168 | 3 | 68 | 47 |
| Los Angeles | −358 | 2,709 | 101 | 1,648 | 6,090 |
| Chicago (holdout) | 144 | 601 | 3 | 1,249 | 107 |
| Madison (holdout) | 794 | 1,471 | −5 | 2,794 | 122 |
| Bellevue (holdout) | 336 | 1,207 | 38 | 1,159 | 203 |

- **The tree, random forest and nearest-neighbour models learned "almost nothing extra happens".** They predict close to zero everywhere. That beats the plain average on the fold mean only because the average overshoots Charlotte and Los Angeles: guessing zero gives a fold mean error of about 1,369 homes. It misses Madison's real gain.
- **The causal forest is the most interesting.**
  - It came closest overall (fold mean error 1,126) and nearly got New York right (4,170 against 3,763).
  - But it overshot Chicago (1,249 against 144) and Madison (2,794 against 794).
  - It is the only method that predicts sizeable effects where they happened. It also predicts them where they didn't.
- **The traits that helped most** (runs A and B):
  - building activity near the lot before the reform;
  - a cheap building on valuable land (New York and Chicago only);
  - rent compared with building cost;
  - the neighbourhood's share of homes built since 2000;
  - lot width.

  The two "many stalls" traits didn't rank high.
- **Conclusion:** after lot-level models with up to 100 traits and 8 methods, no method predicts a new city's total better than the plain average on every test. The city's market still decides most of the outcome. The finalized TOD numbers (AQ-055) stay at 171, 2,509 and 17,148.
