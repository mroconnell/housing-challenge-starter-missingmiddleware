# TOD all-variables test: results

Run 2026-10-27 under [ALLVARS_PLAN.md](ALLVARS_PLAN.md). The plan was written before any of these variables was joined to any effect. Every departure is listed in the plan's section 6 with its date. All variable values were written to file before any model was fitted.

Outputs:
- [reference/tod_allvars_variable_map.csv](../../reference/tod_allvars_variable_map.csv): each variable's table, cells and formula
- [reference/tod_allvars_values.csv](../../reference/tod_allvars_values.csv): each unit's values and the survey years used
- [reference/tod_allvars_models.csv](../../reference/tod_allvars_models.csv): each model's errors by city and its verdict

Code:
- [allvars.py](../../missing_middleware/tod/allvars.py)
- [run_tod_allvars.py](../../scripts/run_tod_allvars.py)
- Units, folds, error and pass rule are imported from [traits.py](../../missing_middleware/tod/traits.py) and [run_tod_traits.py](../../scripts/run_tod_traits.py).

## Summary

**No model passes.** Given 91 variables for each rezoned unit, none of the five models predicts a new city's added homes better than the plain average. The plain average is the acre-weighted mean effect of the training cities' units.
- **LASSO** and **elastic net** usually shrink to the plain average. In the folds where they keep variables, they predict worse.
- **Random forest** beats the plain average in 2 of 6 fitted cities. **Gradient boosting** beats it in 1 of 6. The **causal forest** beats it in none.
- Every model's mean error across the six fitted cities is higher than the plain average's.
- No model beats the plain average on both Chicago and Madison.

With six fitted cities and 91 variables, the flexible models learn the training cities and predict new cities worse. The plan's section 5 expected this, and it is a valid result.

The robustness checks of section 6 (other seeds, largest unit left out, equal weights) apply only to a model that passes. None did, so they were not run. The code runs them for any pass.

## 1. What went in

The test uses 125 units in 10 cities, the same units as the trait test's several-tools rerun:

| City | Units | ACS survey used |
| --- | --- | --- |
| New York | 11 | 2005–2009 |
| Philadelphia | 43 | 2008–2012 to 2014–2018 (by rezoning year) |
| Charlotte | 18 | 2014–2018 |
| Saint Paul | 7 | 2006–2010 |
| Los Angeles | 7 | 2008–2012 |
| Seattle | 3 | 2007–2011 and 2009–2013 |
| Chicago (held out) | 22 | 2010–2014 |
| Madison (held out) | 5 | 2018–2022 |
| Bellevue (shown, not judged) | 3 | 2005–2009 |
| Toronto (shown, not judged) | 6 | none (no ACS in Canada) |

Each unit uses the 5-year survey that ends the year before its reform.
- New York's rezonings (2003 to 2010) and Bellevue's (2009) get the first 5-year release, 2005–2009.
- For all of New York's rezonings except the 2010 one, and for Bellevue's, those values come from around or after the change.

**The 91 variables:**
- **78 from the American Community Survey (46 tables, by tract):**

  | Group | Variables |
  | --- | --- |
  | Housing stock | 21 |
  | Housing costs | 14 |
  | People and households | 22 |
  | Mobility | 18 |
  | Place | 3 |

- **13 traits already built for the TOD tests:** existing density, building rate before, lot size, vacant or parking or industrial share, distance to downtown, transit jobs access, island size, largest continuous site, elongation, corridor share, binding-limit ratio, size of the upzoning, and parking cut.
- **No race or ethnicity variable is used.**
- **How the census values reach a unit:** each treatment lot takes its tract's numbers. Shares are summed over the lots, weighted by acres.
- **Dollars** are in 2024 dollars.

**Missing values:**
- Only Toronto lacks census values (6 units).
- Added floor area ratio is missing for 74 of 125 units, and the binding-limit ratio for 77 of 125. They exist only where the case has a floor-area dose.
- Inside each fold, a missing value is filled with the training cities' acre-weighted mean.

## 2. Held-out errors

The error is the acre-weighted mean absolute error, in homes permitted per eligible acre per year. Lower is better. Each fitted city is predicted from the other five. Chicago, Madison, Bellevue and Toronto are predicted from all six.

| City | Plain average | LASSO | Elastic net | Random forest | Gradient boosting | Causal forest |
| --- | --- | --- | --- | --- | --- | --- |
| New York | 1.15 | 1.15 | 1.33 | 1.49 | 1.24 | 1.24 |
| Philadelphia | 0.88 | 0.88 | 0.88 | **0.88** | 0.92 | 0.89 |
| Charlotte | 0.52 | 0.52 | 0.52 | 0.66 | **0.41** | 0.53 |
| Saint Paul | 0.67 | 0.67 | 0.67 | 0.83 | 0.70 | 0.72 |
| Los Angeles | 0.52 | 0.52 | 0.52 | 1.56 | 1.59 | 0.52 |
| Seattle | 1.41 | 3.07 | 2.53 | **1.39** | 1.43 | 1.41 |
| **Mean of the six fitted cities** | **0.856** | 1.134 | 1.075 | 1.136 | 1.046 | 0.884 |
| Chicago (held out) | 0.54 | 0.54 | 0.54 | 0.68 | 0.86 | 0.59 |
| Madison (held out) | 1.47 | 1.47 | 1.47 | 1.48 | 1.69 | **1.46** |
| Bellevue (shown) | 0.46 | 0.46 | 0.46 | 1.26 | 1.07 | 0.58 |
| Toronto (shown) | 0.42 | 0.42 | 0.42 | 0.14 | 0.12 | 0.46 |

Bold marks a model error below the plain average's. The table rounds to two decimals. The random forest's Philadelphia error is 0.880 against the plain average's 0.881.

## 3. Verdicts

A model passes only if it does all three:
- beats the plain average in at least 4 of the 6 fitted cities;
- beats it on the mean error;
- beats it on Chicago and on Madison, each by itself.

| Model | Fitted cities better (of 6) | Mean error (plain average 0.856) | Beats on Chicago | Beats on Madison | Verdict |
| --- | --- | --- | --- | --- | --- |
| LASSO | 0 | 1.134 | no | no | fail |
| Elastic net | 0 | 1.075 | no | no | fail |
| Random forest (500 trees, ≥5 units per leaf) | 2 | 1.136 | no | no | fail |
| Gradient boosting (depth 2, early stopping) | 1 | 1.046 | no | no | fail |
| Honest causal forest (500 trees) | 0 | 0.884 | no | yes (1.458 vs 1.472) | fail |

**Notes on the models:**
- **LASSO.** Leave-one-city-out tuning inside the training cities chose a penalty that removes every variable in 9 of 10 fits. LASSO then predicts exactly the plain average, so it ties and is not "better". The one fit that kept variables (2 kept, Seattle held out) predicted Seattle at +2.69 homes per eligible acre per year against a measured −0.13.
- **Elastic net** behaves the same way. It kept 30 variables when New York was held out and 35 when Seattle was, and both predictions were worse than the average. When every candidate removes all variables, the L1 share is the first one tried (0.1); this has no effect.
- **Random forest and gradient boosting** predicted Los Angeles at about +1.7 against a measured +0.24.
- **Causal forest.** Its predictions stay near the average, between +0.38 and +0.54 for every city, so it errs little either way.
- **Toronto.** The tree models do well on Toronto (0.12 to 0.14 against 0.42), but Toronto is not judged and has no census values.

Variable importance is not shown, because no model passes (plan section 4).

## 4. What this means

Adding every relevant public variable does not let a model tell, before the fact, which city's upzoning near transit will add many homes. This is the same finding as the trait test's 12 traits and the net-effect test's coverage and car traits. The best predictor of a new city's effect remains the plain average of the measured cities. The spread between cities is still the honest uncertainty.

Limits:
- Six fitted cities is very few. A model that needs many separate cases cannot be judged fairly on six, so the test asks only whether the variables help here. They do not.
- The census values for New York's earlier rezonings and Bellevue's are from around or after the change.
- Toronto has no census values.
