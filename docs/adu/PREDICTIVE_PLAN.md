# ADU predictive test: does a more advanced model predict better? Plan written before any outcome is computed

Written 2026-10-28, at the owner's request (approved design relayed by the ADU conductor). No panel outcome, no model fit and no held-out error has been computed when this file is written. The yearly counts behind the panel are already published elsewhere in the repo (California study, [STATEWIDE_STATES.md](../gate3/STATEWIDE_STATES.md), [OTHER_CITIES.md](../gate3/OTHER_CITIES.md), Madison permits), so this is not a blind test. What this file fixes before running: the rows, the variables, the methods and their settings, the held-out units, the error measures and the pass rule. Changes go in section 10, each with its date and whether it came before or after results were seen. Results: [PREDICTIVE_RESULTS.md](PREDICTIVE_RESULTS.md).

**Units used throughout.**
- A **rate** is ADU permits issued in a year ÷ thousands of one-unit detached homes (ACS 2020–2024 B25024_002 for that geography), so "permits per 1,000 single-family homes per year".
- A **miss** is the absolute difference between a predicted and an observed rate, in the same unit.
- **Additional permits** (Wisconsin step only) are with-law permits minus the current-law baseline, summed over 2027–2031.

## 1. Question

The adopted ADU model (two-stage pooled model, [POOLED_MODEL.md](../gate3/POOLED_MODEL.md) and [POOLED_REVISION.md](../gate3/POOLED_REVISION.md)) predicts each held-out statewide-law state with a root-mean-square log error of 0.113 over 7 states. It uses three within-state terms (home value, income, size) and one common level across states.

Does a more flexible model, given about 100 census variables and finer rows (cities and census tracts), predict held-out places better than:
- (a) the plain average, and
- (b) the adopted model refitted on the same rows?

The owner expects any gain mainly in **where** permits go inside a state, not in **how much** a state permits. So the two are scored separately.

## 2. Panel rows

One row = one geography in one year. Outcome = ADU permits in that year. Exposure = one-unit detached homes ÷ 1,000.

| Level | Rows | Years | Source |
| --- | --- | --- | --- |
| California jurisdiction | The 457 grouped jurisdictions of the adopted model | 2018–2025 | HCD A2, the adopted "cap + A2" counts (`pooled_revision.adjust_ca_panel`, option ii) |
| Washington city | Every incorporated city and town except Seattle | OFM estimate years EY2019–EY2026 | OFM postcensal permits workbook, ADU column (in `data/raw/statewide_states/wa`) |
| Oregon city | The 32 cities of the adopted Oregon panel (excluding Portland) | 2019–2022 | DLCD HB 4006 summaries (in `data/raw/statewide_states/or`) |
| State or region aggregate | Rhode Island, Massachusetts, Maine, Utah, Chittenden County (Vermont) | as in the adopted model | `reference/statewide_states_annual.csv` |
| Other series in that file | Honolulu, Montgomery County (MD), Bozeman (MT) | as listed, before their state laws | same file |
| Census tract | Seattle, Portland, Austin, Denver, Minneapolis, Madison (2020 tracts) | each city's adopted years (section 3) | city permit caches in `data/raw`, Madison permits |

- Seattle and Portland enter as tracts, not as city rows, so no permit is counted twice.
- **Left out of the file's other series:** New Hampshire (conversions, not ADUs), Washington statewide and Spokane (already inside the Washington city rows), Portland ME (source lead; Maine already has a statewide row), and the single-year source leads (Tucson, Phoenix, Colorado Springs).
- **Tract location.** Each permit is placed in a 2020 census tract (TIGER/Line 2024 tract boundaries) from coordinates the city's own open data already carry:
  - Portland: the X/Y in the cached file;
  - Madison: the tract already joined to each permit in `data/processed/permits`;
  - Seattle, Austin: the latitude and longitude fields of the same Socrata datasets, refetched for the same permit numbers;
  - Denver, Minneapolis: the point geometry of the same ArcGIS layers, refetched for the same permit numbers.

  No geocoding service is used. Permits without coordinates are counted in a "no tract" remainder and reported.

## 3. Outcome and treatment

**Outcome.** ADU permits under the adopted outcome rules:
- **California:** the adopted cap + A2 counts (at most 2 ADU units per parcel, cumulated 2018–2025; definite multifamily-lot units removed).
- **Tract cities:** the classifier rules of `other_cities.py` (legalizations excluded). ADUs built together with a new house are kept (as in the adopted city counts), then:
  - at most 2 ADU units per parcel over the panel years, where the city data have a parcel key (Austin TCAD id, Denver schedule number, Minneapolis APN, Portland property id, Seattle site address);
  - × (1 − 0.049) for vacant-lot new-house ADUs (AQ-039), and Minneapolis also × (1 − 0.127) for duplex-lot ADUs, exactly as the adopted model does.
- **Madison:** the ADU components of the Wisconsin second-home outcome (single-family-to-duplex conversions are left out, because they are Wisconsin-only).
- **Washington, Oregon and the aggregates:** the series counts × (1 − 0.049), as in the adopted model.

**Treatment.**
- **Statewide law in force** (yes/no), coded as the adopted model codes it, except California, which is coded from its first law (2017-01-01, year 1 = 2017), so all its 2018–2025 rows are law years 2–9. The adopted model codes California from 2020; the refitted adopted model gets the same coding as every other method.
- **Strong or weaker law:** Mercatus 2025 class, as in [STATEWIDE_STATES.md](../gate3/STATEWIDE_STATES.md): strong = CA, WA, OR, ME, MA, CO; weaker = RI, UT, VT.
- **Years since the law:** 1, 2, 3, and 4 or more.
- **Local reform** (the city's own ADU rules): as the adopted model codes it for Seattle, Portland, Austin, Denver and Minneapolis; Madison = 1 (citywide ADU rules throughout 2014–2025); Honolulu, Montgomery County and Bozeman = 1.

| Series | Years used | Law | Local | Year since law |
| --- | --- | --- | --- | --- |
| California | 2018–2025 | 1 | 0 | 2–9 |
| Washington cities | EY2019–2023 / EY2024–2026 | 0 / 1 | 0 | – / 1–3 |
| Seattle tracts | 2016–2018, 2020–2023 / 2024 | 0 / 1 | 1 | – / 2 |
| Oregon 32 cities | 2019–2022 | 1 | 0 | 1–4 |
| Portland tracts | 2019–2025 | 1 | 1 | 1–7 |
| Rhode Island | 2021–2023 / 2025 | 0 / 1 | 0 | – / 1 |
| Massachusetts, Maine | 2025 | 1 | 0 | 1 |
| Utah | 2023–2025 | 1 | 0 | 2–4 |
| Chittenden County, VT | 2021–2024 | 1 | 0 | 1–4 |
| Austin tracts | 2012–2014 / 2016–2023 | 0 | 0 / 1 | – |
| Denver tracts | 2016–2023 / 2025 | 0 / 1 | 0 / 1 | – / 1 |
| Minneapolis tracts | 2017–2025 | 0 | 1 | – |
| Madison tracts | 2014–2025 | 0 | 1 | – |
| Honolulu, Montgomery County, Bozeman | listed years before their state laws | 0 | 1 | – |

**Placebo rows.** The no-law rows are the owner's placebos ([PLACEBO_PLAN.md](PLACEBO_PLAN.md)): Minneapolis, Denver before 2024, Austin, Wisconsin (Madison), Washington before its law, Honolulu, Montgomery County and Bozeman. California has no row before its law in 2018–2025. Section 7 says how they are used.

## 4. Variables

**Source.** The Census Data API, ACS 2020–2024 5-year detailed tables, for tracts (states 53, 41, 48, 08, 27, 55), places, counties, county subdivisions (Wisconsin, for the Wisconsin step) and states. The key is read from the environment and never written to any file. Raw responses go to `data/raw/acs_api_adu/` with a `_downloads.json` (URL without the key, date, bytes, SHA-256).

**The list (about 100).** The 78 ACS variables of the TOD all-variables test (`reference/tod_allvars_variable_map.csv`: housing stock, housing costs, people and households, mobility, place), plus about 20 ADU-relevant ones:
- one-unit detached homes that are owner-occupied, and their share of all homes;
- median rooms and bedrooms of owner homes; share of homes with 4+ bedrooms;
- share of owner homes worth $500,000 or more, and under $200,000;
- share of homes built 2010 or later;
- seasonal-use vacancy share;
- households 65+ living alone; multigenerational proxies (household size 4+);
- owner share among one-unit detached homes;
- median value of owner homes ÷ median household income;
- share of workers commuting 60+ minutes.

No race or ethnicity variable is used, as in the TOD test. The full list with tables and formulas is written to `reference/adu_predictive_variables.csv` before any model is run.

**Units lesson from TOD (no mixed units).**
- Shares, rates and ratios enter as they are: they are unit-free and mean the same thing everywhere.
- Dollar amounts, densities and counts enter only in unit-free forms:
  - the rank within the row's own context (0 to 1): tracts ranked within their city, places within their state;
  - the log ratio to the context's homes-weighted mean.

  So no variable compares Seattle dollars with Wisconsin dollars directly. An aggregate row (a state or county) is its own context: its rank is 0.5 and its log ratio is 0.
- No geography-size or row-type indicator enters the flexible methods (a tract is not a city, and size would sort rows by type).
- Missing values (small tracts) take the context's homes-weighted mean, with a "missing" flag per variable where any are missing.

## 5. Methods

All methods predict a row's rate; weights are home-years with every state (cluster) carrying the same total weight, as in the adopted model. Seed 20261028.

1. **Plain average.** For a held-out row: the equal-weighted mean, over training states, of each state's pooled rate (permits ÷ home-years) in rows with the same law status (law in force or not).
2. **Guess zero** (reported, not part of the pass rule): rate 0 everywhere.
3. **Adopted model, refitted on the same rows.** `pooled_regression.fit_two_stage`: within-state terms value, income and size relative to the state, law in force, local reform, year 1–3 terms; one common level over the statewide-law states in the training data; equal state weights. Each row's members are its own geography (a tract, a city), and for the aggregate rows the adopted member geographies.
4. **Causal forest, built in two parts** (the TOD lesson, run E): one random forest fitted on law-in-force rows, one on no-law rows. A held-out row is predicted by the part matching its law status. The law's effect for a row = law part minus no-law part. Settings: 500 trees, at least 20 rows per leaf, a third of the variables tried at each split. The law part also sees strong/weaker, years since law and local reform; the no-law part sees local reform.
5. **Boosted trees, built in two parts** the same way: scikit-learn `HistGradientBoostingRegressor`, Poisson loss, depth 3, learning rate 0.05, up to 500 rounds, stopped after 20 rounds with no gain on a 20% validation part of the training rows, at least 20 rows per leaf.
6. **Regularised regression, built in two parts:** Poisson regression with an L2 penalty (`PoissonRegressor`) on standardised variables; the penalty is chosen from 10 values (10⁻⁴ to 10) by leave-one-state-out cross-validation inside the training rows.

Methods 4–6 are built in two parts so that none can ignore the law (the TOD run C lesson: single models learned "nothing extra happens").

## 6. Held-out units and error measures

**Folds.** Each fit leaves out a whole state (every row from it):
- one fold per statewide-law state: California, Washington, Oregon, Rhode Island, Massachusetts, Maine, Utah, Vermont;
- one fold per no-law state: Texas (Austin), Colorado (Denver), Minnesota (Minneapolis), Wisconsin (Madison), Hawaii, Maryland, Montana;
- a **final holdout fit** that leaves out Washington and Oregon together and predicts every Washington and Oregon city row.

**Test 1: how much (statewide level).** Held-out units: the 7 non-California statewide-law states, the same as the adopted model's 0.113. Each is predicted from its own fold. Target: the state series' post-law rate over its post-law years (Washington: cities excluding Seattle, EY2024–2026; Oregon: 32 cities, 2019–2022; Rhode Island, Massachusetts, Maine 2025; Utah 2023–2025; Vermont 2021–2024). For Washington and Oregon, the predicted rate is the sum of predicted city permits ÷ home-years. Miss = |predicted − observed| rate. The log error is also reported, to compare with 0.113.

**Test 2: where (place and tract level).** 10 held-out units:

| Unit | Rows scored | Predicted from |
| --- | --- | --- |
| Seattle tracts | all Seattle tract rows | Washington fold |
| Portland tracts | all Portland tract rows | Oregon fold |
| Austin tracts | all | Texas fold |
| Denver tracts | all | Colorado fold |
| Minneapolis tracts | all | Minnesota fold |
| Madison tracts | all | Wisconsin fold |
| California jurisdictions | all 2018–2025 rows | California fold |
| Washington cities | all EY2019–2026 rows | final holdout fit |
| Oregon cities | all 2019–2022 rows | final holdout fit |
| Madison-like cities | the 24 Madison-like cities with city counts (15 CA, 4 OR, 5 WA; [MADISON_LIKE_CITIES.md](../gate3/MADISON_LIKE_CITIES.md)), their law years | California fold or final holdout fit |

- Each geography's observed and predicted rates are pooled over its scored years (permits ÷ home-years).
- **Rate miss** of a unit = the homes-weighted mean, over its geographies, of |predicted − observed| rate.
- **Where-only miss** of a unit = the share of the unit's permits that sit in the wrong place: ½ × Σ |predicted share − observed share|, where a geography's share is its permits ÷ the unit's permits over the scored years. The plain average's shares are the homes shares. This ignores how much and scores only where.

**Test 3: where only.** The same 10 units, scored on the where-only miss. Guess zero has no shares, so it is not shown here.

## 7. Pass rule (fixed now)

A method **passes a test** only if both hold:
1. its mean miss across that test's held-out units is lower than the plain average's **and** lower than the refitted adopted model's;
2. its miss is lower than both of theirs in **most** of the test's units: at least 4 of 7 states (test 1), at least 6 of 10 units (tests 2 and 3).

- Each method and each test is judged separately. The tests are reported separately: a method can pass "where" and fail "how much".
- **Guess zero** is shown beside every test as a floor. It is not in the rule, but a method that loses to guessing zero on a test is flagged.
- **Robustness of a pass (forests and boosting):** the pass must hold with at least 4 of 5 other seeds (20261029–20261033). A pass that fails this is reported as "not robust" and not brought to the owner.
- **Multiple testing:** 3 methods × 3 tests = 9 chances. Some pass could come by chance; this is stated next to any pass.
- **Placebo check (reported, not in the rule):** on the no-law rows (section 3), each method's rate miss in its own held-out fold, and the law effect each two-part method would assign to those places. A method whose no-law part misses the placebo places much worse than the plain average is flagged.

## 8. If something passes: Wisconsin

Computed as an extra line beside the adopted scenarios. Nothing adopted is replaced; `reference/adu_model_*.csv` is not touched.

- Each Wisconsin engine area (1,925 county subdivisions) gets the method's law-part rate for law years 1 to 5, with "strong" law and no local reform, fitted on all rows. Its ACS variables are built the same way (ranks and log ratios within Wisconsin).
- **Additional permits by area and year** = homes × max(predicted rate − current-law rate × baseline growth, 0) ÷ 1,000, the adopted engine's rule.
- **Reported:** the statewide additional permits over 2027–2031 and the distribution by county (permits and share of the state total).
- **If the method passes test 1 (how much):** its statewide total is the extra line.
- **If it passes only test 2 or 3 (where):** its statewide total is shown but marked "not validated". The county distribution is also shown with the method's area shares applied to the adopted central total (8,757 additional permits over 2027–2031).
- **If nothing passes:** no Wisconsin line is computed.

## 9. Known limits, stated now

- **Few states with a law.** The level of the law's effect still rests on 8 statewide-law states, and the "how much" test has only 7 held-out units. A flexible model cannot learn more about the level than those states contain.
- **Tracts in only 6 cities,** all large cities (Madison the smallest). Their markets are far stronger than most of Wisconsin.
- **Data types differ:**
  - estimate years (Washington) against calendar years;
  - self-reported (Utah, Oregon, Rhode Island) against permit records;
  - units against permits;
  - Massachusetts and Maine are undercounts.
- **One ACS snapshot** (2020–2024) for every year; an earlier vintage for pre-periods is used only if feasible (it would need 2010 tracts for tract rows).
- **Many variables, few states.** As in the TOD and parking tests, a flexible model can fit the training states well and predict a new state badly.

## 10. Changes after writing

All dated 2026-10-28.

1. **While building, before any model was fitted: Oregon city-years.** 18 of 128 Oregon city-years fail the DLCD row check (the table row does not add up) and are left out as missing, not zero. Test 1's Oregon target is the rate over the city-years that remain, for observed and predicted alike.
2. **While building, before any model was fitted: no earlier ACS vintage.** Pre-period variables would need 2010 tracts for the tract rows; not done. Every year uses ACS 2020–2024 (section 9 allowed this).
3. **While building, before any model was fitted: California's unincorporated balances** (50 of 457 jurisdictions) take their county's ACS variables, flagged in the panel. The refitted adopted model keeps the adopted `ca_dataset` market values for all California jurisdictions.
4. **While building: where permit points are stored.** The permit-number-and-point files for Seattle, Austin, Denver and Minneapolis are kept under `data/raw/acs_api_adu/permit_points/` (the one raw folder this work may write), not in each city's own raw folder.
5. **After the main run had started, before its results were read: owner process rule.** Flags are computed before each run and listed at the top of the results (unit checks, law-date checks, 2-per-parcel and apartment-lot handling, held-out units outside the training range), with a trace of the worst-missed unit after each run. They never stop a run. For this run they were computed on the same panel just after the run started.
6. **After the main results were read: how the robustness step was run.** The first run stalled in the robustness step (machine load about 190), so it was stopped. The main-seed predictions it had saved were rescored unchanged (`--reuse`). The robustness step then refitted only the seeded method for each other seed, reusing the plain average and adopted-model predictions, which do not depend on a seed. Nothing in the pass rule changed.
7. **After the results: the adopted model changed mid-run (AQ-061, 17:35).** Tests 1–3 used the pre-AQ-061 coding. The Wisconsin step (run later) used AQ-061 inputs and the AQ-061 central (10,788, not the 8,757 named in section 8). A rerun on AQ-061 coding is needed before the owner uses any result. The pass rule is unchanged.
