# Parking all-variables test: plan written before testing

Written 2026-10-27 by the parking conductor, at the owner's request ("run a big forest test with all the variables too. lasso too"). It mirrors TOD's [ALLVARS_PLAN.md](../tod/ALLVARS_PLAN.md), adapted to parking's 71 places. It is written before any of the new variables is joined to an effect. Changes go in section 5 with a date and a reason.

## 1. Question

With every relevant public variable we can attach to each repeal place, can a flexible model predict where removing parking minimums raised permits, for places it has not seen?

## 2. Places and outcome

The same as rounds 2 and 3:
- **Places:** the 71 US repeal places;
- **Effect:** permits per 1,000 existing homes per year, against comparison places;
- **Weight:** homes × after-years.

## 3. Variables (about 70)

Place level, ACS 2020–2024 5-year. Each variable is written to `reference/parking_allvars_values.csv` before any model is run.

- **Already built (31):** the trait test's T1–T6, round 3's V1–V22, population, metro setting, rent, and the permit rate before repeal.
- **Housing stock:** rooms per home (B25017 median band shares), crowding (B25014, more than 1 person per room), owner share.
- **Housing costs:** shares of rent bands (B25063), rent burden of 30% or more and of 50% or more (B25070), shares of value bands (B25075), share of owner homes with a mortgage (B25081).
- **People:**
  - average household size (B25010) and median age (B01002);
  - households with children (B11005);
  - adults with a bachelor's degree or more (B15003);
  - income distribution shares (B19001);
  - income below 1.5 times poverty (C17002);
  - labour-force participation and unemployment (B23025);
  - median earnings (B20002).
- **Mobility:** time leaving home (B08302: before 7 am, 7–9 am, after 9 am), on top of round 3's cars and commuting.

Race and ethnicity variables are left out on purpose, as in TOD's plan.

## 4. Models and the pass rule

- **Models:**
  - lasso and elastic net (penalty chosen inside each training fold);
  - random forest (500 trees, at least 5 places per leaf);
  - gradient boosting (shallow trees, early stopping inside each fold);
  - honest causal forest.
- **Score:** weighted mean absolute error on left-out places, from 10-fold cross-validation repeated 20 times, seed 20261027, against one average.
- **Pass rule:** at least 5% lower error than one average, the same rule as rounds 2 and 3. A model must also beat one average in at least 15 of the 20 repeats, so one lucky split cannot pass it.
- **Variable importance:** shown only for a model that passes.
- **Expectation, stated now:** 71 places and about 70 variables give a flexible model more room to fit chance than to find signal. A failure is a valid result.

## 5. Changes after writing

None yet.
