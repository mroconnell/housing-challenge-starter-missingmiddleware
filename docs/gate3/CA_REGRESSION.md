# Market-adjusted California regression for Wisconsin's with-law rate

> **Superseded for the statewide total (2026-10-24, AQ-036 to AQ-038):** this California-only regression no longer sets Wisconsin's scenarios. It is kept as a named downside sensitivity (about 2,300 additional second-home permits over 2027–2031) and as the within-state geography reference. The scenarios come from the pooled model in [POOLED_MODEL.md](POOLED_MODEL.md).

Gate 3 revision (AQ-034, owner decision 2026-10-24). This replaces the judgment-based California-to-Wisconsin transfer ratio (G3-1) with a regression fitted on California jurisdictions. The holdout test is published, so all California data is used, as the pre-registered plan allows. Fire-rebuild areas stay in; the owner deferred excluding them. Run with `uv run python scripts/run_ca_regression.py`. Code is in `missing_middleware/comparison/ca_regression.py` and the tests are in `tests/test_ca_regression.py`.

**All results describe associations across California places. They are not causal effects of home values or group membership.**

## Plain-language summary

- **California places with cheaper homes produced far fewer ADUs after the 2020 laws, given the same pre-2020 starting point.**
  - Below about $700,000, places with 10% higher median home values had about **17% higher ADU rates** [10–24%]. Halving home values cuts the rate by about 70%.
  - Above $700,000 the rate is flat (−2% per 10% [−6% to +3%]).
  - Size barely matters: +1% per 10% more homes [−1% to +2%].
  - Pre-2020 activity still matters a great deal. Holding market and size equal, restrictive places run at **0.36×** the rate of active places [0.19–0.63], and middle places at **0.46×** [0.35–0.64].
- **Wisconsin's homes are cheap by California standards.** The homes-weighted median value is $278,000 in Wisconsin against $802,000 in California. 61% of Wisconsin's one-unit homes are in areas below California's 5th percentile ($300,000), and 11% are below its minimum value or minimum rent.
- **Default group rule (owner decision G3-6): rule v1, state-relative.** California's own rule is applied to each state's distribution: top quarter of measured places with at least 3 permits = active; zero or unmeasured = restrictive; the rest = middle.
  - In Wisconsin (2022–2025), only four places are measured. **Madison is the only active place.** Sun Prairie (one application) is middle. Pleasant Prairie and Fitchburg (zero) and every estimated-only place, including Milwaukee, Wauwatosa and Appleton, are restrictive.
  - Applied to California's own 2017–2019 data, the rule reproduces the study's groups for all 372 jurisdictions.
- **Statewide, 2027–2031, rule v1: about 2,300 additional second homes** on single-family lots (lower about 1,000, upper about 5,900), on top of the 650 baseline. Ramps differ by path:
  - lower: slower Central Valley ramp;
  - central: California restrictive-group ramp;
  - upper: faster middle-group ramp.
  - The lower and upper levels are the 2.5% and 97.5% statewide draws of a jurisdiction bootstrap of the California fit.
  - The as-run paths were 900 / 6,500 / 23,300. The homes-weighted with-law rate is 0.49 per 1,000 homes a year after the Madison floor; the as-run central used 1.23.
  - The (a), (b) and (c) mappings give centrals of 2,150–2,580 (section 3).
- **Cross-validation supports the market terms where it matters for Wisconsin.** In California's cheapest quarter of places, the group-only curve over-predicts total ADUs by **+87%**; the market model misses by **−2%**. Across all places the two are similar in aggregate (−6% vs −3%).
- **The key sanity check fails under rule v1: the model predicts Madison at 2.50 per 1,000 a year with the statewide law.** That is 10–14× Madison's observed 0.18 (2022–25) and 0.24 (2024–25), and 378 of the 2,340 central units.
  - Even with Madison mapped to middle (version a), the prediction is 1.16, and with every place restrictive it is 0.91.
  - So the market terms do not carry Madison's low level. The gap is what a statewide law, or a California-specific factor, would have to supply.
  - Madison's provisional 2026 rate (0.97 with the templated program, 0.30 without) is the only Wisconsin observation near the model.
- **Unzoned towns (G3-5):** applied since the town list landed (239 unzoned towns, about 76,600 homes); they add about 58 to the central path. *(Updated by the conductor 2026-10-24.)*
- **Event time (benchmark adoption year)** raises the Wisconsin total by 12% (2,620). Los Angeles, the one documented early adopter, supplies 53% of the active group's 2017–2019 permits. Event time explains about half of that group's early rise.
- **Ramp:** the study's ramp shapes are kept. Low-value California places ramped like the group as a whole.

## 1. Data

### Outcome (California)

- **Measure:** ADU-type second homes per 1,000 one-unit detached homes per year, averaged over the 2023–2025 plateau.
- **Source and sample:** the study's main measure, from `study_panel.parquet`, for all 536 jurisdictions, holdout included.
- **Missing years:** a missing year (filed with no A2 rows, or no record) is dropped from the average, not counted as zero.
- **Groups:** the study's wave-3 groups (pre-period 2017–2019).
  - **Active:** rate ≥ 1.0379 per 1,000 a year (the study's non-holdout cutoff at full precision; published rounded as 1.038) and ≥ 3 permits.
  - **Restrictive:** zero permits in every pre-period year.
  - **Middle:** the rest.
  - **Excluded:** places missing a pre-period year.
  - The non-holdout cutoff is applied to all jurisdictions, as the holdout test did.
- **Result:** 459 grouped jurisdictions; 457 have complete market data (105 active, 262 middle, 90 restrictive).
- **Pre-2020 activity is the primary proxy for early local adoption** (owner follow-up). Hand-coded adoption years are tested separately in section 5.

### Market variables

The market variables come from the ACS 2020–2024 5-year table-based summary file. It is keyless, read with `foundation.parsers.read_acs_sf`, and stored in `data/raw/census_acs5_2024_tbsf_market/`. URLs, bytes and SHA-256 are recorded in `_downloads.json`; access date 2026-10-24.

| Table | Variable | Use |
| --- | --- | --- |
| B25077 | Median value, owner-occupied units | main predictor |
| B25064 | Median gross rent | alternative predictor |
| B19013 | Median household income | alternative predictor (price-to-income) |
| B25003 | Tenure (renter share) | carried for reference, not used |

- **Coded values.** Top-coded medians (value "2,000,000+", rent "3,500+", income "250,000+") are set to the code minus one and flagged. California has 134 top-coded places. Negative special codes are treated as missing.
- **California cities:** the place row (summary level 160).
- **California county unincorporated remainders (50 in the fit).** ACS medians cannot be differenced, so a remainder takes the whole county's median as a proxy (`market_basis = county_proxy`). This is defensible for rural counties, where the remainder is most of the county. It is weaker in urban counties, where the cities hold most homes. Dropping all remainders raises the Wisconsin central from 2,340 to 2,850 (section 4).
- **California cities with a missing median** fall back to their county (rent for 4 places, value for 1). Two jurisdictions are dropped because a median is still missing.
- **Wisconsin areas** (1,925 county-subdivision pieces in `engine_areas.parquet`): the county-subdivision row (060) is used.
  - Value is missing for 46 pieces. The fallback is first the same municipality's largest other county piece (30 pieces), then the county (16 pieces).
  - Rent is missing far more often, because small towns have few renters. 42 pieces use another county piece and 269 use the county.
  - The source of each value is recorded in `wi_y_by_area.csv` (`value_basis`, `rent_basis`).

## 2. Model choice

- **Model:** Poisson regression of plateau permits (count over the observed years), with log exposure (homes × observed years ÷ 1,000) as the offset.
- **Why Poisson rather than a log-linear model of rates:**
  - It handles the 21% of restrictive places with zero permits without adding an arbitrary constant.
  - With an exposure offset, the Poisson fit is the homes-weighted rate regression, so each home-year counts once.
  - Its coefficients read directly as percentage changes in the rate.
- **Over-dispersion.** California counts are over-dispersed (dispersion about 100), so intervals come from a jurisdiction bootstrap: 1,000 draws, resampling within each group, seed 20261024. Robust sandwich SEs are in the CSV. The Poisson variance is never used.
- **What this weighting implies.** The largest places weigh most; Los Angeles is about a quarter of the plateau permits (21,015 of 87,303). Section 4 shows the fit without Los Angeles.

### Specifications compared

These are 10-fold cross-validation results (seed 20261024, folds by jurisdiction, the same 457 rows and folds for every specification). Errors are per 1,000 homes per year; totals are summed over the held-out places of each fold.

| Specification | Place MAE | Median abs. error | Mean abs. fold-total error | Total error | Cheapest quarter: MAE | Cheapest quarter: total error |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Group only (the study's curve) | 2.05 | 1.36 | 27% | −3% | 1.46 | **+87%** |
| Group + log value | 2.03 | 1.30 | 28% | −3% | 1.31 | +65% |
| Group + log rent | 2.08 | 1.42 | 28% | −4% | 1.56 | +93% |
| Group + log value + log size | 1.89 | 1.12 | 27% | −6% | 1.07 | +49% |
| Group + log rent + log size | 1.94 | 1.20 | 28% | −6% | 1.26 | +79% |
| Group + value + rent + size | 1.91 | 1.21 | 26% | −8% | 1.25 | +63% |
| **Group + log value with a second slope below $700k + log size (main)** | **1.86** | 1.18 | 24% | −6% | **0.90** | **−2%** |
| Group + log value + log income + log size | 1.75 | 1.06 | 16% | −4% | 1.16 | +43% |

**Reading the comparison:**

- **Every single-slope model over-predicts California's cheapest places.** Binned rates show why: the value gradient is steep below about $700,000 and flat above it.
  - For restrictive places, the rate is about 1.0 below $300,000 and 0.65 at $300–400k.
  - For middle places, it is 0.7–1.3 below $500,000 and 2.2–3.4 above $500,000.
- **The two-slope (hinge) model fixes this with one extra term.** It is the best model in the cheapest quarter, which is the part of California closest to Wisconsin. It is close to the best overall.
- **The price-to-income model** (value +1.92, income −2.43) is the best overall, with the lowest deviance and fold errors. It gives a nearly identical Wisconsin total (2,290). It is kept as the main functional-form alternative rather than the main model for two reasons:
  - Its signs are harder to explain.
  - Wisconsin's homes-weighted price-to-income ratio (3.35) is below California's minimum (3.47), so nearly every Wisconsin area is an extrapolation.
- **Region dummies were not added.** The hinge already separates the coastal and inland markets, and 457 places do not support many more terms.
- **Deviation (post hoc, disclosed).** The second slope and its knot ($700,000, about California's median place value of $714,500) were chosen after seeing the binned rates and the first cross-validation table. Knot sensitivity, total in Wisconsin: $500k gives 2,120, $600k gives 2,100, $800k gives 2,590.

### Main coefficients (plain language)

| Term | Estimate [bootstrap 95%] | Reading |
| --- | --- | --- |
| Value, below $700k | +17.5% per 10% higher value [+10% to +24%] | Halving value cuts the rate to 0.31× [0.20–0.48] |
| Value, above $700k | −1.7% per 10% [−6.2% to +2.8%] | Flat |
| Size (one-unit homes) | +1.1% per 10% more homes [−1.5% to +2.0%] | Negligible |
| Middle vs active (same market and size) | 0.46× [0.35–0.64] | |
| Restrictive vs active | 0.36× [0.19–0.63] | |
| Intercept | 6.4 per 1,000 a year | An active place at $500k value and 10,000 homes |

**Predicted with-law rate for a 5,000-home place:**

| Median value | Active | Middle | Restrictive |
| --- | ---: | ---: | ---: |
| $150k | 0.41 | 0.19 | 0.15 |
| $250k | 0.97 | 0.45 | 0.35 |
| $373k (Madison) | 1.91 | 0.89 | 0.69 |
| $500k | 3.15 | 1.46 | 1.14 |
| $700k | 5.57 | 2.58 | 2.02 |

Every coefficient is in `reference/ca_regression_coefficients.csv`; the CV table is in `reference/ca_regression_cv.csv`.

## 3. Wisconsin application

### Group rule v1: state-relative activity groups (default; owner decision G3-6)

**Rule v1, to be made robust when building for other states.** The owner did not want a state-specific cutoff. The rule is California's own grouping rule, applied to each state's own distribution of observed second-home permits. The function is `ca_regression.state_relative_groups(obs, top_share=0.25, min_permits=3)`; its input is one row per jurisdiction with permits, observed years, homes, and whether the whole reference window is observed.

- **Active:** rate in the top quarter of measured jurisdictions (by rank, ties at the cut included) **and** at least 3 permits in the window.
- **Restrictive:** zero permits, or unmeasured (owner rule).
- **Middle:** everyone else.
- **Validation.** On California's non-holdout 2017–2019 data, the function gives the study's cutoff (1.0379) and the same group for all 372 measured jurisdictions.
  - Writing this check exposed one fix: the regression had used the rounded published cutoff (1.038). That misgrouped one place sitting exactly at the cut (0611040, now active).
  - The cutoff is now recomputed at full precision. Results moved by less than 0.1%.

**Wisconsin application** (reference window 2022–2025; `reference/ca_regression_wi_activity_groups.csv`):

| Place | Permits 2022–25 | Rate | Group | Source |
| --- | ---: | ---: | --- | --- |
| Madison | 39 | 0.183 | **active** (top quarter of 4 = rank 1; ≥ 3 permits) | issued permits |
| Sun Prairie | 1 | 0.031 | middle | applications |
| Pleasant Prairie | 0 | 0 | restrictive | issued permits |
| Fitchburg | 0 | 0 | restrictive | text rule, 2022 to 2026-07 |
| Everyone else (1,921 areas), including Milwaukee, Wauwatosa and Appleton | not measured | — | restrictive | Milwaukee's open data gives unverified candidates over other windows only |

**Quirks of v1 to fix when it is made robust:**

- With four measured places, "top quarter" is one place. That place is always active, whatever its level: Madison's 0.18 is a sixth of California's active cutoff.
- One application makes Sun Prairie middle (y 0.91). Wauwatosa, which has benchmark rules but no measured permits, is restricted-like (y 0.66).
- Possible fixes: a minimum number of measured places; pooling across states; adding a rules-based floor such as version (c).

### Group mapping versions side by side

Market terms adjust the level in every version. Paths use the path-specific ramps (section 4).

| Version | Rule | Lower | Central | Upper | Madison y (central) | Madison additional |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| **v1 state-relative (default)** | California's rule on Wisconsin's own 2022–25 data: Madison active, Sun Prairie middle, all else restrictive | **1,020** | **2,340** | **5,940** | 2.50 | 378 |
| (a) absolute | California thresholds: Madison-like x ≥ 0.1 (Madison, Wauwatosa, Appleton, Milwaukee) → middle; others restrictive | 920 | 2,150 | 5,670 | 1.16 | 159 |
| (b) relative | The same 4 places → active; others restrictive | 1,090 | 2,580 | 6,480 | 2.50 | 378 |
| (c) rules | `scenario_benchmark` → active; `restricted` (24 places, including Milwaukee) → middle; prohibited and undetermined → restrictive | 1,110 | 2,530 | 6,290 | 2.50 | 378 |
| Sensitivity: v1 with unmeasured → middle | | | 2,910 | | 2.50 | |
| Sensitivity: (a) with unmeasured → middle | | | 2,570 | | 1.16 | |
| Sensitivity: (c) with unmeasured → middle | | | 2,950 | | 2.50 | |
| Sensitivity: every area restrictive | | | 2,070 | | 0.91 | |

**What the comparison shows:**

- **The mapping moves the state total by less than 25%** (2,070–2,950). Few homes change group.
- **It moves Madison by a factor of 2–3.** v1, (b) and (c) all make Madison active-like and predict 2.5, 10–14× its observed rate. My earlier recommendation was (a), which predicts 1.16 (5–6× too high), because California's active group carries a pre-2020 head start (Los Angeles's 2017 adoption, plus early production) that the market terms do not remove.
- **The owner chose v1 as the general rule.** The Madison check should be presented next to it.

### Unzoned towns (G3-5): hook

- `ca_regression.load_zoning_status` reads `reference/wi_town_zoning_status.csv` (`zoning_status` = unzoned / county_general / town_own / unknown, keyed by `area_id` or a 10-digit geoid) when it exists.
- The result is carried into `wi_y_by_area.csv` (`zoning_status`), and `summary.json` reports areas, homes and central additional units per status.
- **Treatment:** unzoned towns already allow ADUs legally, so they are mapped by the same state-relative activity rule. With no measured permits they are restrictive-like, and they get their own market-based predicted rate.
- **Status:** the file did not exist when this ran (every area shows `file_missing`), so no town is reported separately yet. Rerunning `scripts/run_ca_regression.py` after the file lands produces the split with no code change.
- **Open question for the owner:** AQ-026 still says `no_zoning` places add 0. This treatment gives them an addition of homes × (y − x); x for unzoned towns is still the estimated restricted-like rate.

### Per-area output: `reference/wi_y_by_area.csv`

There is one row per engine area (1,925). Columns:

- `area_id`, name, county, context group, homes, `x_rate`, rights basis, `zoning_status`;
- California group under the default (`ca_group`) and under each version;
- median value, rent and income, each with its source;
- an `extrapolation` flag;
- `y_lower`, `y_central`, `y_upper` (default rule v1);
- `y_{v1_state_relative,a_absolute,b_relative,c_rules}_{lower,central,upper}`;
- `y_engine_central` = max(floor 0.229, y_central, x);
- alternatives: `y_alt_single_slope`, `y_alt_price_income`, `y_event_time`.

**How the per-area values are defined:**

- **Central** is the point prediction of the main model.
- **Lower and upper** are one coherent statewide draw each: the bootstrap draw whose Wisconsin five-year total (at the central ramp) sits at the 2.5th or 97.5th percentile of 1,000 draws. These totals are 1,490 and 5,280 at the central ramp. Each path then runs with its own ramp.
- Where a draw crosses the point prediction in one area, that area keeps the point prediction, so lower ≤ central ≤ upper holds everywhere.
- In the upper draw, Madison's y is 5.7, so Madison alone is 1,010 of the upper path.
- **These are statistical intervals for California's fitted relationship only.** They exclude the transfer uncertainty that the Madison check exposes.

### Extrapolation

| Wisconsin areas | Areas | One-unit homes | Central additional |
| --- | ---: | ---: | ---: |
| Inside California's range (value ≥ $300k California p5, rent ≥ $1,093) | 284 | 514,680 | 1,345 |
| California tail (below p5, above the minimum) | 1,183 | 1,123,457 | 865 |
| Outside the range (value < $157,200 or rent < $745) | 458 | 201,432 | 127 |

**Functional-form sensitivity for extrapolation** (central, five-year):

| Form | Total |
| --- | ---: |
| Main: log-linear below $700k, extrapolated | 2,340 |
| Clamp Wisconsin values at California's minimum ($157k) | 2,340 (unchanged: the Madison floor already binds there) |
| Clamp Wisconsin values at California's 5th percentile ($300k), so no extrapolation into the tail | 2,950 |
| Single slope fitted on California places valued ≤ $700k | 4,950 |
| Single slope fitted on all places | 4,370 (over-predicts cheap California places by about 50% in cross-validation) |
| Price-to-income form | 2,290 |

**Where the floor binds.** The Madison floor (0.229, AQ-024) binds in 842 areas holding 434,000 homes. It adds 80 units: 2,260 without the floor.

## 4. Statewide five-year additional units (engine)

The engine is `missing_middleware.model.engine.run`, with `area_levels` taken from `wi_y_by_area.csv`. Settings follow the owner decisions of 2026-10-24.

- **Floor:** 0.229 (AQ-024).
- **Spillover: none.** Benchmark places get their own regression rate (G3-2 option (a)).
- **Ramps by path (G3-3 accepted):**

| Path | Ramp | Basis |
| --- | --- | --- |
| Lower | 0.10, 0.19, 0.25, 0.55, 1.0 | Central Valley after 2017. Year 1 is held to the central 0.10 instead of 0.12, so the paths stay ordered. |
| Central | 0.10, 0.53, 0.58, 0.85, 1.0 | California restrictive group |
| Upper | 0.24, 0.54, 0.77, 0.89, 1.0 | California middle-group increment share (as run) |

The engine invariants pass. The baseline is 654 on every path. These are scenario paths: one model and ramp per path, applied to all areas together.

| Path | Regression, rule v1 | As run | Difference |
| --- | ---: | ---: | ---: |
| Lower | **1,020** | 880 | +130 |
| Central | **2,340** | 6,520 | −4,180 |
| Upper | **5,940** | 23,280 | −17,340 |

**By context group:**

| Context | Lower | Central | Upper |
| --- | ---: | ---: | ---: |
| Rural | 317 | 816 | 2,062 |
| Suburban | 280 | 707 | 1,571 |
| Urban | 323 | 633 | 1,831 |
| Small community | 96 | 182 | 472 |

**Homes-weighted y by rights basis:**

| Rights basis | y |
| --- | ---: |
| Benchmark | 1.70 (Madison 2.50; Wauwatosa and Appleton restricted-like) |
| Prohibited (implicit) | 0.49 |
| Restricted | 0.40 |
| Undetermined | 0.41 |
| Prohibited (explicit) | 0.31 |

**Sensitivities on the central path** (from `reference/ca_regression_sensitivities.csv`):

| Change | Total |
| --- | ---: |
| As fitted (rule v1) | 2,340 |
| Without Los Angeles | 3,200 |
| Without county remainders | 2,850 |
| Without Lancaster (post hoc) | 1,820 |
| HCD issue-year measure | 2,410 |
| Event-time plateau (LA 2017) | 2,620 |
| Event-time plateau (LA 2017, San Diego 2018) | 2,500 |
| Central path with middle-group ramp | 2,630 |
| Central path with Central Valley ramp | 1,610 |
| No ramp | 3,830 |
| No Madison floor | 2,260 |
| Knot at $500k / $600k / $800k | 2,120 / 2,100 / 2,590 |
| Group-only (no market terms) | 7,500 |

**Madison sanity check.**

- Under rule v1 the model gives Madison y = 2.50 (lower draw 2.06, upper draw 5.70). That is 378 additional units over the five years (171 as run), 16% of the state's central.
- Madison's observed rates are 0.18 (2022–25) and 0.24 (2024–25). The 2026 provisional rate is 0.97, or 0.30 without the templated program.
- The check fails under every mapping: 2.50 under v1, (b) and (c); 1.16 under (a); 0.91 with every place restrictive.
- California evidence at Madison's price: the 31 middle places valued under $400,000 reached 0.75 after 2020, and the 48 restrictive ones reached 0.73. California's single active place below $400,000 reached 5.6.

## 5. Benchmark adoption year and event time (owner input)

`reference/ca_regression_adoption_years.csv`: the default adoption year is 2020. The list is kept small and evidenced.

| Jurisdiction | Year | Status | Basis |
| --- | --- | --- | --- |
| Los Angeles city | **2017** | documented | Its second-unit ordinance became null and void on 2017-01-01 (SB 1069/AB 2299), and the City applied the state default standards: ministerial approval, no owner occupancy, parking waived within ½ mile of transit (most of the city). Permits went from 80 (2016) to 2,342 (2017). Sources: LA City Planning ADU information sheet (rev. Jan 2017); Sightline Institute, 2019-04-05. |
| San Diego city | 2020 (sensitivity 2018) | source lead, partial | 2017 compliance amendments and an ADU fee waiver around 2018 (R-311730, superseded 2022). Owner-occupancy and parking terms are not verified. Its big rise is in 2023. |
| San Jose | 2020 | documented, not near-benchmark | Local amendments effective 2018-07-27 kept one parking space. |
| All others | 2020 | undocumented default | |

The LA City Planning ADU FAQ returned HTTP 403, and San Diego's 2017 ordinance text could not be read (scanned or oversized PDF). Both stay leads.

**Event-time model.**

- **Specification:** outcome = rate in event years 4–6 after the jurisdiction's own adoption (2020–2022 for Los Angeles); group = activity in the three years before adoption; same market and size terms.
- **Effect on coefficients and Wisconsin:** coefficients barely move (below-$700k slope 1.65 vs 1.69; restrictive 0.35× vs 0.36×). The Wisconsin central rises to **2,620** (+12%, rule v1; 2,450 under (a)), mainly because Los Angeles's event-time plateau (2020–2022, 9.3 per 1,000) is lower than its 2023–2025 level (12.5), which flattens the size term (0.11 → 0.05) and so raises predictions for Wisconsin's many small places. Both versions are reported. The change is well inside the bootstrap range.
- **Which predicts better:** in cross-validation, the event-time model's place-level deviance is 85 against 107 for the calendar model (overall), and 38 in both for the cheapest quarter. The improvement is almost all Los Angeles. The two models predict different targets (LA's outcome window differs), so this is not a clean comparison. Pre-2020 activity remains the primary proxy, as the owner asked.
- **Does event time explain the active group's earlier rise? About half of it.**
  - Los Angeles supplies 53% of the active group's 2017–2019 permits; San Diego supplies 4%.
  - Without Los Angeles, the active group's 2017–2019 rate is 1.84 per 1,000 a year instead of 2.99.
  - The other 103 active places still rose early under the 2017 state law, with no documented local near-benchmark adoption.
- **Event-time curves** are in `reference/ca_regression_event_time.csv`.
- **California alone cannot separate industry maturity from calendar time** (section 6). California's statewide ADU industry already existed by 2020 because of the 2017–2019 waves, and every 2020 adopter faced the same industry at the same calendar time. Only places with different adoption dates under different statewide timing can separate the two.

## 6. Owner experience on industry formation, and what the data show

**Owner experience (recorded as experience, not a finding).**

- California's specialized ADU industry (builders, lenders, plan sets; firms such as Abodu, United Dwelling, Samara, Villa) mostly formed after the 2019 package took effect in 2020. Before that it was a small, beginner market.
- If so, the post-2020 restrictive-group response includes industry formation alongside the law, which makes it a closer analogue to a single Wisconsin statewide law.

**Evidence in the data** (all grouped jurisdictions, average yearly change in the pooled rate; `reference/ca_regression_industry_check.csv`):

| Group | 2017–2019 | 2021–2025 | Reading |
| --- | ---: | ---: | --- |
| Active | +1.28 a year (+0.81 without LA) | +0.81 (+0.61 without LA) | No acceleration after 2020 |
| Middle | +0.15 | +0.34 | Accelerated after 2020 |
| Restrictive | 0 | +0.26 | Started after 2020 |

**How this bears on the owner's view.**

- Against it, for active places: their growth slowed after 2020 rather than accelerating. Their industry, or local capacity, was already in place by 2018–2019.
- Consistent with it, for the places Wisconsin resembles: middle and restrictive places accelerated or started only after 2020.
- The data cannot separate industry formation from the stronger 2020 law (exemption floor, fee caps, owner-occupancy pause), because both arrived at the same time.
- Out-of-state cities with other timing are the test.

**Out-of-state cities (Seattle 2019, Portland, Austin, Denver 2023): how they would enter.** Another agent is collecting them, and none had arrived when this ran.

- **As extra rows in the regression:**
  - same outcome (ADU-type second homes per 1,000 one-unit detached homes, ACS B25024);
  - market terms from the same ACS tables;
  - group from their own pre-reform activity;
  - a `state` indicator for each non-California state, with "statewide law in effect" coded separately from local adoption year.
- **As an identification test:** a city reforming locally before its state (Seattle 2019, Portland 2010s) versus California places reforming with their state separates local rules from statewide-industry effects. That speaks directly to the AQ-024 mechanism and to Madison's gap.
- **As validation:** predict each city's post-reform rate from the California fit with its own market values. A model that over-predicts these cities as it over-predicts Madison would confirm a California-specific level. Accurate predictions would support the transfer.

## 7. Ramp

The study's ramp shapes are kept, by path as the owner decided (section 4; `reference/ca_regression_ramp_by_market.csv`). Restrictive places valued at $700,000 or less reached 0.08, 0.50, 0.56, 0.86, 1.01, 1.14 of their plateau in years 1–6. That is the same as the group as a whole (0.10, 0.53, 0.58, 0.85, 1.03, 1.12). The regression gives no reason to change the ramp. The G3-3 slower ramp is now the lower path's ramp.

## 8. Limitations

- The paths are California associations transferred with Wisconsin's market values. Lower and upper reflect California sampling uncertainty only.
- The Madison check shows that a transfer gap of 5× (version a) to 14× (rule v1) remains at Madison's market level. Whether a statewide law closes it is the AQ-024 question, which this model does not settle.
- Most Wisconsin homes sit in California's thinnest tail of values (18 restrictive and 5 middle places below $300k). The low-value slope rests on about 130 places below $500k.
- County-remainder market values are county-wide proxies.
- Fire-rebuild places are not excluded (deferred).
- Los Angeles dominates the Poisson fit. Excluding it raises the Wisconsin total to 3,200. The reason was not investigated further; it is shown as a sensitivity.
- Rents are often missing for small Wisconsin towns (county fallback for 269 pieces); rent is not in the main model.
- Interior conversions (junior ADUs) are in California's outcome and get no uplift under AQ-030, so y is slightly overstated.

## Files

- Code: `missing_middleware/comparison/ca_regression.py`; runner `scripts/run_ca_regression.py`; tests `tests/test_ca_regression.py` (fixtures in `tests/fixtures/ca_regression/`).
- Reference (committed): `wi_y_by_area.csv` and the `ca_regression_*.csv` files:
  - `coefficients`, `cv`, `sensitivities`, `wi_statewide`, `wi_mappings`, `wi_by_context`, `wi_activity_groups`;
  - `extrapolation`, `adoption_years`, `event_time`, `industry_check`, `ramp_by_market`;
  - `ca_jurisdictions` (California jurisdiction outcome, group and market values).
- Processed (git-ignored): `data/processed/ca_regression/` (`ca_dataset`, `cv_predictions`, `results_long`, `summary.json`).
