# Market-adjusted California regression for Wisconsin's with-law rate

Gate 3 revision (AQ-034, owner decision 2026-10-24). This replaces the judgment-based California-to-Wisconsin transfer ratio (G3-1) with a regression fitted on California jurisdictions. The holdout test is published, so all California data is used, as the pre-registered plan allows. Fire-rebuild areas stay in; the owner deferred excluding them. Run with `uv run python scripts/run_ca_regression.py`. Code is in `missing_middleware/comparison/ca_regression.py` and the tests are in `tests/test_ca_regression.py`.

**All results describe associations across California places. They are not causal effects of home values or group membership.**

## Plain-language summary

- **California places with cheaper homes produced far fewer ADUs after the 2020 laws, given the same pre-2020 starting point.**
  - Below about $700,000, places with 10% higher median home values had about **17% higher ADU rates** [10–24%]. Halving home values cuts the rate by about 70%.
  - Above $700,000 the rate is flat (−2% per 10% [−6% to +3%]).
  - Size barely matters: +1% per 10% more homes [−2% to +2%].
  - The pre-2020 group still matters a great deal. Holding market and size equal, restrictive places run at **0.36×** the rate of active places [0.19–0.63], and middle places at **0.46×** [0.35–0.65].
- **Wisconsin's homes are cheap by California standards.** The homes-weighted median value is $278,000 in Wisconsin against $802,000 in California. 61% of Wisconsin's one-unit homes are in areas below California's 5th percentile ($300,000), and 11% are below its minimum or below its minimum rent.
- **Applied to every Wisconsin area, the model gives a homes-weighted with-law rate of about 0.45 per 1,000 homes a year** (after the Madison floor). The as-run central path used 1.23.
- **Statewide, 2027–2031: about 2,200 additional second homes** on single-family lots (range 1,400 to 5,200), on top of the 650 baseline.
  - The range is the 2.5% and 97.5% statewide draws of a jurisdiction bootstrap of the California fit.
  - That compares with the as-run paths of 900 / 6,500 / 23,300.
  - The model's central lands between the as-run lower and central paths. It sits inside the 1,500–4,500 band the validation review called "at least as defensible".
- **Cross-validation supports the market terms where it matters for Wisconsin.**
  - Across all California places, the market model and the group-only curve predict similarly in aggregate (−6% vs −3%), and the market model is somewhat better place by place.
  - In California's cheapest quarter of places, the group-only curve over-predicts total ADUs by **+87%**; the market model misses by **−2%**.
- **Sanity check, which fails: the model predicts Madison at 1.16 per 1,000 a year with the statewide law.** Madison's observed rate is 0.18 (2022–25) and 0.24 (2024–25).
  - The market terms do not explain Madison's low rate. Comparable California places, at Madison's price level and with some pre-2020 activity, reached 0.75–0.9 after 2020.
  - The remaining gap is what a statewide law, or a California-specific factor, would have to supply.
  - Madison's provisional 2026 rate (0.97 with the templated program, 0.30 without) is the only Wisconsin observation near the model.
- **Group mapping (owner rule).** I recommend **(a) absolute**: Madison-like places are California "middle", the rest "restrictive". The totals are 2,150 for (a), 2,580 for (b) relative and 2,530 for (c) rules-based. The mapping moves the state total by less than 20%, but it moves Madison by 2×. (c) predicts Madison at 2.5, ten times its observed rate.
- **Event time (benchmark adoption year)** changes the Wisconsin total by +14% (2,450). Los Angeles, the one documented early adopter, supplies 53% of the active group's 2017–2019 permits. Event time explains about half of that group's early rise; the rest is unexplained by documented local adoption.
- **Ramp:** the study's ramp is kept. Low-value California places ramped the same way as the group as a whole.

## 1. Data

### Outcome (California)

- **Measure:** ADU-type second homes per 1,000 one-unit detached homes per year, averaged over the 2023–2025 plateau.
- **Source and sample:** the study's main measure, from `study_panel.parquet`, for all 536 jurisdictions, holdout included.
- **Missing years:** a missing year (filed with no A2 rows, or no record) is dropped from the average, not counted as zero.
- **Groups:** the study's wave-3 groups (pre-period 2017–2019).
  - **Active:** rate ≥ 1.038 per 1,000 a year and ≥ 3 permits.
  - **Restrictive:** zero permits in every pre-period year.
  - **Middle:** the rest.
  - **Excluded:** places missing a pre-period year.
  - The published non-holdout cutoff (1.038) is applied to all jurisdictions, as the holdout test did.
- **Result:** 459 grouped jurisdictions; 457 have complete market data (104 active, 263 middle, 90 restrictive).
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
- **California county unincorporated remainders (50 in the fit).** ACS medians cannot be differenced, so a remainder takes the whole county's median as a proxy (`market_basis = county_proxy`). This is defensible for rural counties, where the remainder is most of the county. It is weaker in urban counties, where the cities hold most homes. Dropping all remainders raises the Wisconsin central from 2,150 to 2,620 (section 4).
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
- **The price-to-income model** (value +1.92, income −2.43) is the best overall, with the lowest deviance and fold errors. It gives a nearly identical Wisconsin total (2,260). It is kept as the main functional-form alternative rather than the main model for two reasons:
  - Its signs are harder to explain.
  - Wisconsin's homes-weighted price-to-income ratio (3.35) is below California's minimum (3.47), so nearly every Wisconsin area is an extrapolation.
- **Region dummies were not added.** The hinge already separates the coastal and inland markets, and 457 places do not support many more terms.
- **Deviation (post hoc, disclosed).** The second slope and its knot ($700,000, about California's median place value of $714,500) were chosen after seeing the binned rates and the first cross-validation table. Knot sensitivity, total in Wisconsin: $500k gives 1,890, $600k gives 1,900, $800k gives 2,420.

### Main coefficients (plain language)

| Term | Estimate [bootstrap 95%] | Reading |
| --- | --- | --- |
| Value, below $700k | +17.5% per 10% higher value [+10% to +24%] | Halving value cuts the rate to 0.31× [0.20–0.48] |
| Value, above $700k | −1.7% per 10% [−6.2% to +2.8%] | Flat |
| Size (one-unit homes) | +1.1% per 10% more homes [−1.5% to +2.0%] | Negligible |
| Middle vs active (same market and size) | 0.46× [0.35–0.65] | |
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

### Group mapping (owner rule, 2026-10-24)

Wisconsin places with current ADU activity behave like California's already-active places. Places at zero or unmeasured activity behave like California's restrictive places in 2020. Market terms adjust the level in every version.

| Version | Rule | Lower | Central | Upper | Madison y (central) | Madison additional |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| **(a) absolute (recommended)** | California thresholds: Madison-like x ≥ 0.1 (Madison, Wauwatosa, Appleton, Milwaukee) is non-zero but far below the 1.04 active cutoff → **middle**; all others → restrictive | **1,370** | **2,150** | **5,210** | 1.16 | 159 |
| (b) relative | Ranked within Wisconsin: the same 4 places → **active**; others restrictive | 1,600 | 2,580 | 5,710 | 2.50 | 378 |
| (c) rules | Coded rights: `scenario_benchmark` → active; `restricted` (24 places, including Milwaukee) → middle; prohibited and undetermined → restrictive | 1,620 | 2,530 | 5,620 | 2.50 | 378 |
| Sensitivity: (a) with unmeasured → middle | | | 2,570 | | 1.16 | |
| Sensitivity: (c) with unmeasured → middle | | | 2,950 | | 2.50 | |
| Sensitivity: every area restrictive | | | 2,070 | | 0.91 | |

**Why I recommend (a):**

- California's groups are defined by observed production, not by rules. "Active" means at least 1.04 a year before 2020, a level no Wisconsin place has ever reached; Madison's 0.18 sits inside California's middle range.
- In California, the active group's coefficient carries a pre-2020 head start: Los Angeles's 2017 adoption, plus whatever made those places produce early. Under (b) and (c), Madison would inherit that head start, even though the market terms already price its cheaper homes.
- **The owner's key sanity test, Madison's own rate.**
  - (c) predicts 2.5 against 0.18–0.24 observed, 10–14× too high.
  - (a) predicts 1.16, 5–6× too high, but it is the closest of the three.
  - No mapping with market terms brings Madison near its observed rate. Even mapping every place restrictive gives 0.91.
  - So the market term does *not* carry Madison's lower level by itself. What remains is either the statewide-law mechanism (AQ-024, AQ-027) or a California-specific level the market variables do not capture.
- Rules-based mapping (c) is the right idea once Wisconsin has a with-law observation to calibrate on, or if out-of-state cities (section 6) show that rules, not production, predict the post-law level.
- The state total is not sensitive to the choice (2,150–2,580). Only the eight Madison-like areas, and the 24 restricted places under (c), change group.

### Per-area output: `reference/wi_y_by_area.csv`

There is one row per engine area (1,925). Columns:

- `area_id`, name, county, context group, homes, `x_rate`, rights basis;
- California group under the recommended mapping and under each version;
- median value, rent and income, each with its source;
- an `extrapolation` flag;
- `y_lower`, `y_central`, `y_upper` (recommended mapping);
- `y_{a_absolute,b_relative,c_rules}_{lower,central,upper}`;
- `y_engine_central` = max(floor 0.229, y_central, x);
- alternatives: `y_alt_single_slope`, `y_alt_price_income`, `y_event_time`.

**How the per-area values are defined:**

- **Central** is the point prediction of the main model.
- **Lower and upper** are one coherent statewide draw each: the jurisdiction-bootstrap draw whose Wisconsin five-year total sits at the 2.5th and 97.5th percentile of 1,000 draws. Each path is therefore one model applied to all areas together (AQ-027), not an independent per-area quantile. Where that draw crosses the point prediction in a single area, the area keeps the point prediction, so lower ≤ central ≤ upper holds everywhere.
- **These are statistical intervals for California's fitted relationship only.** They exclude the transfer uncertainty that the Madison check exposes. They are narrower than the as-run scenario paths for that reason, and should not be presented as the whole uncertainty.

### Extrapolation

| Wisconsin areas | Areas | One-unit homes | Central additional |
| --- | ---: | ---: | ---: |
| Inside California's range (value ≥ $300k California p5, rent ≥ $1,093) | 284 | 514,680 | 1,129 |
| California tail (below p5, above the minimum) | 1,183 | 1,123,457 | 896 |
| Outside the range (value < $157,200 or rent < $745) | 458 | 201,432 | 127 |

**Functional-form sensitivity for extrapolation** (central, five-year):

| Form | Total |
| --- | ---: |
| Main: log-linear below $700k, extrapolated | 2,150 |
| Clamp Wisconsin values at California's minimum ($157k) | 2,150 (unchanged: the Madison floor already binds there) |
| Clamp Wisconsin values at California's 5th percentile ($300k), so no extrapolation into the tail | 2,800 |
| Single slope fitted on California places valued ≤ $700k | 4,580 |
| Single slope fitted on all places | 4,200 (the cross-validation shows this form over-predicts cheap California places by about 50%) |
| Price-to-income form | 2,260 |

**Where the floor binds.** The Madison floor (0.229, AQ-024) binds in 841 areas holding 434,000 homes. It adds 80 units: 2,070 without the floor, 2,150 with it.

## 4. Statewide five-year additional units (engine)

The engine is `missing_middleware.model.engine.run`, with `area_levels` taken from `wi_y_by_area.csv` and three settings:

- floor 0.229 (AQ-024);
- spillover 0 (G3-2 option (a): the statewide level, here the regression, drives benchmark places, and the group term already includes California's spillover; AQ-027, no double counting);
- ramp 0.10, 0.53, 0.58, 0.85, 1.0 on every path.

The engine invariants pass. The baseline is 654 on every path.

| Path | Regression (recommended mapping) | As run | Difference |
| --- | ---: | ---: | ---: |
| Lower | **1,370** | 880 | +490 |
| Central | **2,150** | 6,520 | −4,370 |
| Upper | **5,210** | 23,280 | −18,070 |

**By context group (central):**

| Context | Additional |
| --- | ---: |
| Rural | 816 |
| Suburban | 702 |
| Urban | 453 |
| Small community | 182 |

**Homes-weighted y by rights basis:**

| Rights basis | y |
| --- | ---: |
| Benchmark | 0.94 |
| Restricted | 0.42 |
| Undetermined | 0.41 |
| Prohibited (implicit) | 0.49 |
| Prohibited (explicit) | 0.31 |

The undetermined places hold 1.27M homes, so they weigh most.

**Sensitivities on the central path** (from `reference/ca_regression_sensitivities.csv`):

| Change | Total |
| --- | ---: |
| As fitted | 2,150 |
| Without Los Angeles | 3,070 |
| Without county remainders | 2,620 |
| Without Lancaster (post hoc) | 1,660 |
| HCD issue-year measure | 2,220 |
| Event-time plateau (LA 2017) | 2,450 |
| Event-time plateau (LA 2017, San Diego 2018) | 2,370 |
| Middle-group ramp | 2,420 |
| Central Valley 2017 ramp (G3-3) | 1,480 |
| No ramp | 3,520 |
| No Madison floor | 2,070 |
| Group-only (no market terms) | 7,170 |

**Madison sanity check.**

- The model gives Madison y = 1.16 [1.12–1.18]. That is 159 additional units over five years (171 as run).
- Madison's observed rates are 0.18 (2022–25) and 0.24 (2024–25). The 2026 provisional rate is 0.97, or 0.30 without the templated program. The check fails as a level check, as described in section 3.
- California evidence at Madison's price: the 31 middle places valued under $400,000 reached 0.75 after 2020, and the 48 restrictive ones reached 0.73.

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
- **Effect on coefficients and Wisconsin:** coefficients barely move (below-$700k slope 1.65 vs 1.69; restrictive 0.35× vs 0.36×). The Wisconsin central rises to **2,450** (+14%), mainly because Los Angeles's event-time plateau (2020–2022, 9.3 per 1,000) is lower than its 2023–2025 level (12.5), which flattens the size term (0.11 → 0.05) and so raises predictions for Wisconsin's many small places. Both versions are reported. The change is below the bootstrap range.
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

The study's ramp shapes are kept (`reference/ca_regression_ramp_by_market.csv`). Restrictive places valued at $700,000 or less reached 0.08, 0.50, 0.56, 0.86, 1.01, 1.14 of their plateau in years 1–6. That is the same as the group as a whole (0.10, 0.53, 0.58, 0.85, 1.03, 1.12). The regression gives no reason to change the ramp. The G3-3 slower ramp remains an owner decision (central: 1,480 with it).

## 8. Limitations

- The paths are California associations transferred with Wisconsin's market values. Lower and upper reflect California sampling uncertainty only.
- The Madison check shows that a transfer gap of about 5× remains at Madison's market level. Whether a statewide law closes it is the AQ-024 question, which this model does not settle.
- Most Wisconsin homes sit in California's thinnest tail of values (18 restrictive and 5 middle places below $300k). The low-value slope rests on about 130 places below $500k.
- County-remainder market values are county-wide proxies.
- Fire-rebuild places are not excluded (deferred).
- Los Angeles dominates the Poisson fit. Excluding it raises the Wisconsin total to 3,070. The reason was not investigated further; it is shown as a sensitivity.
- Rents are often missing for small Wisconsin towns (county fallback for 269 pieces); rent is not in the main model.
- Interior conversions (junior ADUs) are in California's outcome and get no uplift under AQ-030, so y is slightly overstated.

## Files

- Code: `missing_middleware/comparison/ca_regression.py`; runner `scripts/run_ca_regression.py`; tests `tests/test_ca_regression.py` (fixtures in `tests/fixtures/ca_regression/`).
- Reference (committed): `wi_y_by_area.csv` and the `ca_regression_*.csv` files:
  - `coefficients`, `cv`, `sensitivities`, `wi_statewide`, `wi_mappings`, `wi_by_context`;
  - `extrapolation`, `adoption_years`, `event_time`, `industry_check`, `ramp_by_market`;
  - `ca_jurisdictions` (California jurisdiction outcome, group and market values).
- Processed (git-ignored): `data/processed/ca_regression/` (`ca_dataset`, `cv_predictions`, `results_long`, `summary.json`).
