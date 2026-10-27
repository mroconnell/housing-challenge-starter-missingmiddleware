# TOD all-variables test: plan written before looking

Written 2026-10-27 by the TOD conductor, at the owner's request: "look through the rest of the census data and see what might be relevant ... run it with ALL the data". Written before any of these variables are joined to any effect. The commit that adds this file is the timestamp. Changes go in section 6 with a date and a reason.

## 1. Question

With every relevant public variable we can attach to each rezoned unit, can a flexible model predict where upzoning near transit added homes, in cities it has not seen?

## 2. Units, folds and outcome

Exactly as in [TRAITS_PLAN.md](TRAITS_PLAN.md), latest section 8 entry:
- **Units:** the same rezoned units.
- **Outcome:** extra homes permitted per eligible acre per year, acre-weighted.
- **Folds:** leave one city out, over the fitted cities.
- **Held out:** Chicago and Madison are never fitted.

## 3. Variables

For each unit's treatment area, from the 5-year American Community Survey by tract closest before the reform (2005–2009 for earlier reforms). Every variable is written to `reference/tod_allvars_values.csv` with its table and year before any model is run. Expected groups (about 60 to 100 variables):
- **Housing stock:** units in structure, year built, vacancy, owner and renter shares, rooms, persons per room.
- **Housing costs:** gross rent and value distributions, rent burden, mortgage status.
- **People and households:** household size, age bands, households with children, education, income distribution, poverty, labour-force participation, median earnings.
- **Mobility:** vehicles available, means of commute, travel time, time leaving home, work in the place of residence.
- **Place:** density of homes and people, land area.
- **Already built for the TOD tests:** existing density, building rate before, lot size, vacant, parking or industrial share, distance to downtown, transit jobs access, island size, largest continuous site, elongation, corridor share, binding-limit ratio, size of the upzoning, parking cut.

Race and ethnicity variables are left out on purpose. A model that sized a law by a neighbourhood's racial make-up would be inappropriate for a policy tool, whatever its fit.

## 4. Models and the pass rule

- **Models:** LASSO, elastic net, random forest (500 trees, minimum 5 per leaf), gradient boosting (shallow trees, early stopping inside each fold) and an honest causal forest. All tuning happens inside each training fold.
- **Pass rule (as strict as before):** a model passes only if it beats the plain average in at least two-thirds of the fitted cities, on the mean error, and on Chicago and on Madison separately.
- **Reporting:** every model is reported.
- **Variable importance:** shown only for a model that passes. Otherwise it would describe noise.

## 5. Expectations, stated now

More variables help a forest only when there are enough separate cases to learn from. Here there are six to eight cities, and the test predicts whole cities. With dozens of variables and few cities, a flexible model can fit the training cities very well and still predict a new city badly. That is the pattern seen so far. A failure is a valid result and will be reported as such.

## 6. Changes after writing

None yet.
