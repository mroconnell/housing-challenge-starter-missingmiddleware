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

**2026-10-27, robustness checks for any pass (written before any TOD result is seen, after the parking scenario's all-variables passes collapsed under checks).** A model that passes the rule is confirmed only if it also passes:
- **(a) Other seeds:** the same rule with 5 other random seeds (20261028 to 20261032), passing in at least 4 of the 5;
- **(b) Each large case left out:** the same rule with each fitted city's largest unit by acres removed, one at a time;
- **(c) Equal weights:** the same rule with every unit weighted equally instead of by acres.

A pass that fails any of these is reported as "not robust" and is not brought to the owner as a candidate.

**2026-10-27, how the variables are built and the models set (written while the Census files downloaded, before any variable was joined to any effect).**
1. **Census source.** The Census Data API refuses calls without a key (HTTP 302 to `missing_key.html`, checked 2026-10-27), and none is available. The same published estimates are read from the Census summary files instead: per-state, per-sequence files for the 2005–2009 to 2014–2018 releases, and the national table-based files for 2018–2022 (only the header and Wisconsin tract rows are kept; the hash of the whole file as served is recorded). Every file's URL, size and SHA-256 is in `data/raw/tod_allvars/manifest.json`. `scripts/run_tod_allvars.py --stage fetch` does this automatically.
2. **Which survey.** For each unit, the 5-year survey that ends the year before its reform year. Reforms of 2010 or earlier get 2005–2009, the first 5-year release; for New York's rezonings of 2003 to 2009 and Bellevue (2009) these values are from around or after the change, as in the trait test. Each release is read on its own tract boundaries: 2000 tracts for 2005–2009, 2010 tracts through 2015–2019, 2020 tracts for 2018–2022. The survey per unit is a column of `reference/tod_allvars_values.csv`.
3. **From tracts to a unit.** Each treatment lot takes the tract its representative point falls in, as in the trait test. Shares and rates are the acre-weighted sum of the tracts' numerators over the acre-weighted sum of their denominators (the rule of the net-effect car traits). Medians and other tract summaries are the acre-weighted mean of the tract values. ACS placeholder values (negative medians) are missing.
4. **Units of measure.** Dollar amounts are converted to 2024 dollars with CPI-U (BLS CUUR0000SA0) for the survey's last year. Income-bracket shares stay in the survey's own dollars (they cannot be converted). Year built and year moved in become years before the survey's last year. Year-built shares are read from the oldest categories at the end of table B25034, because the newest categories change between releases.
5. **The list.** 78 ACS variables in the plan's five groups, plus the 13 traits the plan names as already built (t02, t03, t07 to t12; n01 to n05), 91 in all. The map is `reference/tod_allvars_variable_map.csv` (table, cells, formula, group). Left out: the three ACS medians of the trait test (t01, t04, t06) and the three car traits (n06 to n08), which are here again at the plan's survey years (c04, p11, c01, m01, m06, m10); and city land area (t05), which is not on the plan's list. No race or ethnicity table is used (B02, B03 and the lettered race tables), as the plan says. Every release's line titles are checked against the lines used where the release publishes them (2005–2009 to 2014–2018).
6. **How variables enter.** Natural logarithms for dollar amounts, densities and tract land area; the built traits as entered in their own tests (log(value + 1) for density, island size, largest site and elongation). A missing value is filled with the training fold's acre-weighted mean, worked out inside each fold, as in the several-tools rerun; a variable with no spread in a training fold is dropped in that fold. Toronto has no ACS, so its ACS variables are all filled.
7. **Models.** Same units, folds, error, baseline and pass rule as the several-tools rerun (`traits.judge_tools`): six fold cities (New York, Philadelphia, Charlotte, Saint Paul, Los Angeles, Seattle), at least 4 better, lower mean error, and better on Chicago and on Madison; Bellevue and Toronto predicted and shown, not judged. Settings are those of that rerun: LASSO with 50 penalties chosen by leave-one-city-out among the training cities; random forest 500 trees, at least 5 units per leaf; gradient boosting depth 2, learning rate 0.05, up to 1,000 trees, stopped after 20 rounds with no gain on a 20% validation part; the honest causal forest of `traits.py` (500 trees). Elastic net: the same penalties and leave-one-city-out tuning, with the L1 share chosen from 0.1, 0.3, 0.5, 0.7, 0.9, 0.95 and 0.99. Seed 20261027.
8. **Variable importance (passing models only).** Impurity importance for the forest and boosting, absolute standardized coefficients for LASSO and elastic net, from the model fitted on all six fold cities; the 15 largest are listed. The causal forest has none.
