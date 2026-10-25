# Pooled multi-state model and statewide adoption curve for Wisconsin's with-law rate

> **Superseded numbers (2026-10-25, AQ-042):** the Wisconsin scenario totals in this document (4,780 / 9,518 / 18,387 direct; engine 4,789 / 9,526 / 18,398; Madison 351; adoption line 8,654) are no longer the adopted figures. The adopted run is [POOLED_REVISION.md](POOLED_REVISION.md) option (ii) "cap + A2", configuration A, with the vacant-lot factor, the Minneapolis adjustment, the 0.2345 Madison floor and Madison on the observed Madison-like path: lower 4,407, central 8,721, Strong adoption 16,853 additional second-home permits over 2027–2031, on a 645-permit baseline; adoption line 8,208. See the [Gate 3 packet](README.md). The model form, the within-state and between-state stages, and the validation method below are unchanged.
>
> **Status update (2026-10-24, AQ-038):** the owner adopted this model's central and between-state spread as the Gate 3 scenarios, with the statewide adoption path shown as a separate reference line (not the upper scenario). The engine now uses path-specific ramps and reproduces this document's direct totals (4,780 / 9,518 / 18,387); the earlier "engine gives 9,514" figure came from a rounded ramp. Madison's engine value is 351 additional permits. The "conductor must decide" section below is resolved.

Gate 3 revision, owner direction of 2026-10-24: put about 90% of the effort into the **statewide** rate, take that rate from a model or from measured data (never set it by judgment), and treat where units land inside Wisconsin as secondary. This work is **not** part of the pre-registered [CA_COMPARISON_PLAN.md](CA_COMPARISON_PLAN.md) and changes nothing in it.

**Units used throughout.** Unless a sentence says otherwise:
- a **rate** is second-home (ADU-type) permits issued in a year, divided by thousands of one-unit detached homes (ACS 2020–2024 B25024_002), so "permits per 1,000 single-family homes per year";
- a **five-year total** is the number of permits issued statewide in Wisconsin over the five forecast years 2027–2031 (law in force from the start of 2027);
- **additional** permits are the with-law permits minus the current-law baseline of 654 permits over 2027–2031 (125–133 permits a year, [WI_BASELINE.md](WI_BASELINE.md));
- Wisconsin has 1,839,569 one-unit detached homes.

**All results are descriptive associations across states and places, not causal effects.**

## Plain-language summary

- **A. Statewide adoption (the owner's simple version, intended as the upper scenario).**
  - Across the seven states with post-law data, the median rate reached was:
    - **0.79** permits per 1,000 single-family homes per year in year 1 (6 states);
    - **0.90** in year 2 (4 states);
    - **0.88** in year 3 (4 states);
    - **1.24** in year 4 (3 states: Oregon, Utah, Vermont).
  - No state has a fifth year yet, so year 5 is held at the year-4 median of 1.24 permits per 1,000 single-family homes per year.
  - Applied to Wisconsin's 1,839,569 single-family homes, this gives **9,309 with-law permits statewide over 2027–2031**. That is **8,654 additional permits** over 2027–2031 after removing the 654-permit baseline.
- **B. Pooled regression (the central candidate).**
  - **The model.**
    - Inside each state, California's 457 jurisdictions and the other states' places and towns show how rates vary between places and how they rise year by year after a law.
    - Across states, each state counts once.
    - When one state is held out, the best predictor of its rate is the average level of the other states, adjusted only for the years since its law. Home value, income and price-to-income across states all predicted held-out states worse, especially Maine, the market closest to Wisconsin.
  - **Accuracy on held-out states.** The chosen specification predicts each held-out statewide-law state within about 12% (root-mean-square log error 0.11), with these errors in rate:
    - Maine 0.0%;
    - Oregon +4%;
    - Vermont +13%;
    - Washington +19%;
    - Massachusetts +20%;
    - Rhode Island −6%;
    - Utah −7%.
  - **Wisconsin's predicted path.** The rate rises from **0.83** permits per 1,000 single-family homes per year in 2027 to **1.03** (2028), **1.07** (2029) and **1.30** (2030 and 2031). That is **10,172 with-law permits** over 2027–2031, or **about 9,500 additional permits** over 2027–2031 (9,518 exactly).
  - **Model-uncertainty interval.** It is built from the scatter of state levels around the common level, not from sampling.
    - 80% interval: **4,780 to 18,387 additional permits** over 2027–2031.
    - 95% interval: 2,913 to 28,353 additional permits.
    - The scatter of held-out-state errors alone would give a narrower 80% range of 8,014 to 11,283 additional permits.
- **B is not lower than A.** The pooled model is the same evidence as A, organised as a model. It sits about 10% above A because its year-4-and-later level also counts California (as one of eight states) and Oregon, Utah and Vermont's later years.
  - The named measurement adjustments move both down. With ADUs built with a new house counted at 0.8, A is 6,793 and B is 7,814 additional permits over 2027–2031.
- **The California-only regression is the outlier.** Its central of 2,337 additional permits over 2027–2031 (2,119 under rule v1.1) is about a quarter of A and B.
  - Pooling California with the other states in one regression with one shared home-value slope still gives only 2,600–4,400 additional permits over 2027–2031.
  - That model still under-predicts Maine by a factor of about 3, because California's steep within-state value gradient sets the shared slope.
- **The strongest challenge: the Midwest places are low even after allowing for "no statewide law".**
  - **Minneapolis** (held out) permitted 0.26 per 1,000 single-family homes per year in 2017–2025. The model predicted 0.93 per 1,000 single-family homes per year for local rules without a statewide law.
  - **Madison** permitted 0.18 per 1,000 single-family homes per year.
  - **Wisconsin's current-law rate** is 0.072 per 1,000 single-family homes per year, against the model's no-law prediction of 0.52.
  - The statewide-law indicator (×2.5) explains only 24–42% of the log gap for Madison and Minneapolis. So **it does not explain their lower rates**; something Midwest-specific or demand-related is also at work.
  - Whether that persists once a statewide law is in force cannot be tested yet. No Midwest state has post-law data; Iowa's first full year is 2026.
  - The measured before/after pairs (California, Rhode Island, Washington, Vermont) show the year-1 rate does not depend on the pre-law rate (slope 0.01 ± 0.21). California went from 0.12 to 0.60 permits per 1,000 single-family homes per year in its first law year, from a base close to Wisconsin's 0.07.
  - If instead the law only multiplied Wisconsin's current rate by the pooled ×2.5, the result would be **758 additional permits** over 2027–2031. The before/after pairs contradict this, but it is the floor of the evidence.

## Headline table

| Version | Rate in 2027 / 2028 / 2029 / 2030 / 2031 (permits per 1,000 single-family homes per year) | With-law permits, 2027–2031 | Additional permits over the 654 baseline, 2027–2031 |
| --- | --- | ---: | ---: |
| **A. Statewide adoption, as reported** | 0.79 / 0.90 / 0.88 / 1.24 / 1.24 | 9,309 | **8,654** |
| A, new-house ADUs × 0.8 | 0.63 / 0.72 / 0.70 / 1.00 / 1.00 | 7,447 | 6,793 |
| A, coverage-adjusted (lower bounds raised) | 0.87 / 0.90 / 0.88 / 1.24 / 1.24 | 9,452 | 8,798 |
| A, both adjustments | 0.70 / 0.72 / 0.70 / 1.00 / 1.00 | 7,562 | 6,908 |
| A, chain-linked (same states each step) | 0.79 / 0.97 / 0.93 / 1.12 / 1.12 | 9,079 | 8,425 |
| A, Washington counted from local compliance | 0.82 / 0.98 / 0.91 / 1.24 / 1.24 | 9,562 | 8,908 |
| **B. Pooled two-stage model, central** | 0.83 / 1.03 / 1.07 / 1.30 / 1.30 | 10,172 | **9,518** |
| B, 80% model interval | 0.45–1.56 / … / 0.69–2.43 | 5,434–19,041 | 4,780–18,387 |
| B, 95% model interval | 0.29–2.38 / … / 0.46–3.70 | 3,567–29,007 | 2,913–28,353 |
| B, new-house ADUs × 0.8 | 0.67 / … / 1.09 | — | 7,814 |
| California-only regression, central (rule v1; v1.1) | plateau 0.49 with the restrictive ramp | — | 2,337 (2,119) |
| One-stage pooled regression, shared slope | 0.31–0.41 / … / 0.41–0.68 | — | 2,618–4,417 |
| Wisconsin's current rate × pooled law ratio | 0.12 / … / 0.18 | — | 758 |

By year, the additional permits are:

| Year | A: additional permits | B central: additional permits |
| ---: | ---: | ---: |
| 2027 | 1,330 | 1,408 |
| 2028 | 1,533 | 1,770 |
| 2029 | 1,479 | 1,831 |
| 2030 | 2,156 | 2,254 |
| 2031 | 2,156 | 2,254 |

Files: [`reference/statewide_adoption_curve.csv`](../../reference/statewide_adoption_curve.csv) (A, every adjustment, California for context) and [`reference/pooled_wi_statewide.csv`](../../reference/pooled_wi_statewide.csv) (B, central and intervals, by year).

## A. Statewide adoption curve

### Data and year coding

The series are the state-level ones in [STATEWIDE_STATES.md](STATEWIDE_STATES.md) (`reference/statewide_states_annual.csv`). Year 1 is the first (nearly) full year with the statewide law in force. Partial law years are dropped.

| State | Series | Year 1 | Years used (rate, permits per 1,000 single-family homes per year) |
| --- | --- | --- | --- |
| Washington | incorporated cities excl. Seattle | OFM EY2024 (8 of 12 months after enactment on 2023-07-23) | 0.68, 0.81, 0.84 (years 1–3) |
| Oregon | 32 cities over 10,000 excl. Portland | 2019 (law 2018-07-01; 2018 dropped) | 0.79, 0.98, 0.91, 0.92 (years 1–4) |
| Rhode Island | statewide, reporting towns | 2025 (law 2024-06-25; 2024 dropped) | 0.97 (year 1) |
| Massachusetts | statewide, 293 of 351 towns | 2025 (law 2025-02-02) | 0.79 (year 1) |
| Maine | statewide denominator, 182 towns reporting | 2025 (compliance 2024; 2024 transition) | 0.98 (year 1) |
| Utah | MIH reporters, statewide denominator | report year to July 2023 = year 2 (law 2021-10-01) | 1.11, 1.03, 1.25 (years 2–4) |
| Vermont | Chittenden County | 2021 (Act 179, 2020-10-12) | 0.67, 0.83, 0.80, 1.48 (years 1–4) |

Points: [`reference/pooled_adoption_points.csv`](../../reference/pooled_adoption_points.csv).

### Curve (level path, not a plateau times a ramp)

| Year since law | States | Median | Range (permits per 1,000 single-family homes per year) | California, years after its 2017 law (context) | California, years after its 2020 package (context) |
| ---: | --- | ---: | --- | ---: | ---: |
| 1 | MA, ME, OR, RI, VT, WA (6) | **0.79** | 0.67–0.98 | 0.60 | 1.55 |
| 2 | OR, UT, VT, WA (4) | **0.90** | 0.81–1.11 | 1.10 | 2.49 |
| 3 | OR, UT, VT, WA (4) | **0.88** | 0.80–1.03 | 1.55 | 3.09 |
| 4 | OR, UT, VT (3) | **1.24** | 0.92–1.48 | 1.55 | 3.43 |
| 5 | none; holds year 4 | **1.24** | — | 2.49 | 3.69 |

California is shown for context only and is not in the median. Its rates are all jurisdictions' permits per 1,000 single-family homes per year from the study panel. In its first law year California (0.60) was in the same range as the other states.

**Composition.** The jump from year 3 (0.88) to year 4 (1.24) is partly a change of states: Washington drops out, and Vermont's 2024 (1.48, 57 permits in one county) enters. The chain-linked version follows the same states from one year to the next and gives 0.79, 0.97, 0.93, 1.12, 1.12 permits per 1,000 single-family homes per year. That is 8,425 additional permits over 2027–2031.

### Measurement adjustments (named, optional, never applied silently)

- **New-house ADUs.** Most state series include ADUs built together with a new house; Wisconsin's outcome excludes them.
  - The shares measured in the cities are 36% (Seattle), 12% (Portland), 8% (Minneapolis) and 66% (Austin), per [OTHER_CITIES.md](OTHER_CITIES.md).
  - The adjustment multiplies every state rate by 0.8. A becomes 6,793 additional permits over 2027–2031.
- **Partial coverage (lower bounds).** The adjustment divides by the reporting share:
  - Maine by 0.73 (population reporting);
  - Massachusetts by 293/351 (towns reporting);
  - Rhode Island 2025 by 32/39 (towns reporting).
  - Only year 1 moves, from 0.79 to 0.87 permits per 1,000 single-family homes per year. A becomes 8,798 additional permits over 2027–2031.
  - Town shares are a crude stand-in for home shares.
- **Both together:** 6,908 additional permits over 2027–2031.
- **Timing.** Counting Washington from local compliance (EY2026 = year 1) gives 8,908 additional permits over 2027–2031.

### Application to Wisconsin

The calculation is:
- with-law permits in year t = 1,839,569 homes × rate(t) ÷ 1,000;
- additional permits = that minus the baseline for year t (125.5, 129.2, 132.8, 133.3, 133.3 permits).

So A is a pure level path: no ramp is applied on top, because the rates are already rates actually reached. The engine's per-area rule ("no area below its current rate") makes no difference to A, because A is a statewide rate.

## B. Pooled regression

### Data (one row per area-year)

Outcome: permits counted in the year. Exposure: one-unit detached homes ÷ 1,000. Rows by state:

| State (cluster) | Rows | What they are |
| --- | ---: | --- |
| California | 2,659 | 457 grouped jurisdictions (holdout included), 2020–2025, statewide law in force; year 1 = 2020 (the 2019 package) |
| Washington | 16 | incorporated cities excl. Seattle: EY2019–23 no law, EY2024–26 law (years 1–3); Seattle 2016–18 and 2020–23 local rules only, 2024 law + local (year 2) |
| Oregon | 11 | 32 cities 2019–22 (years 1–4); Portland 2019–25 law + local (2011–18 fee-waiver years not used: a fee programme, not a rules reform) |
| Rhode Island | 4 | 2021–23 no law; 2025 law (year 1) |
| Massachusetts, Maine | 1 each | 2025 law (year 1) |
| Utah | 3 | 2023–25 law (years 2–4) |
| Vermont | 4 | Chittenden 2021–24 (years 1–4). 2016–20 not used: Vermont has allowed ADUs by right since 2004, so it is not a no-law period |
| Texas (Austin) | 11 | 2012–14 no reform; 2016–23 local rules only |
| Colorado (Denver) | 9 | 2016–23 zone-by-zone (no reform); 2025 state law + citywide rules (year 1); 2024 dropped |
| Minnesota (Minneapolis) | 9 | 2017–25 local rules only |

Coding reasons are in `NOTES` in `pooled_regression.py`. Rows: [`reference/pooled_dataset_rows.csv`](../../reference/pooled_dataset_rows.csv). City counts include ADUs built with a new house, to match the state series; the main city measure is a sensitivity.

**Each row's market is its own distribution of places.** A state row's expected count is the sum, over its member geographies, of homes × the modelled rate. This is how Wisconsin's statewide rate is predicted from its 1,925 areas. The members are:
- **places:** Washington's 280 cities, Oregon's 32 cities, the five cities;
- **county subdivisions:** Maine's 525, Massachusetts's 351, Rhode Island's 39, Utah's 91, and Chittenden's 19.

**Market data per member.** Every member has median home value (B25077), **median household income (B19013)**, median rent (B25064) and renter share (B25003), from the same keyless ACS 2020–2024 summary files.
- This covers California jurisdictions (from `ca_regression`), the state members, the five cities and the 1,925 Wisconsin areas.
- Missing medians fall back to the county, then the state, and are flagged. Maine has the most fallbacks (168 of 525 small towns).
- Summary: [`reference/pooled_members_summary.csv`](../../reference/pooled_members_summary.csv).
- Homes-weighted typical value (geometric mean of medians): Wisconsin $260,900, Maine $288,100, the other states $434,000–$564,000, California's jurisdictions $728,800.

### Model: within states, then between states (each state counts once)

**Stage 1, within states.** A weighted Poisson regression with one intercept per state, plus terms that vary inside a state:
- a place's log value and log income relative to its state's homes-weighted mean;
- log size;
- statewide law in force;
- local reform;
- year-1, year-2 and year-3 indicators (years 4 and later are the reference, so the plateau).

Rows are weighted so every state's total home-years count the same. California's 457 places therefore teach this stage how rates vary between places and over time, without setting any state's level.

**Stage 2, between states.** Each state's intercept is its level at its own typical place, with no law and no local reform. These intercepts are regressed on the state's typical value, income or price-to-income, or on a constant. The eight statewide-law states (including California) count once each.
- The residual spread, τ (log scale), is the between-state uncertainty for a new state such as Wisconsin.
- Austin, Denver and Minneapolis inform stage 1 (the law and local-reform terms) but are not states with a statewide law. Including them in stage 2 is a sensitivity.

**Why this form and not one weighted regression or random effects in one step.**
- In a single pooled regression, one home-value slope has to serve both "between places in California" and "between states". California's within-state spread dominates it even with equal state weights.
- The result is a slope of 1.2–2.6 (log rate per log value). It under-predicts Maine by a factor of 2.6–4.1 in leave-one-state-out, the same failure as the California-only model.
- Splitting within from between is the standard within–between (Mundlak) random-intercept model. California's counts are over-dispersed (dispersion about 100), so a random intercept would be essentially free for each state. Fitting it in two steps gives the same answer and is easier to read.

### Which specification predicts held-out states best (leave one state out)

Method:
- Hold each state out of **both** stages.
- Predict its statewide-law rows from its own market and years since law.
- Compare predicted with observed permits per 1,000 single-family homes per year over its post-law years.

Error = log(predicted ÷ observed): +0.10 means predicted about 10% high. Headline = the seven statewide-law state series. Full results: [`reference/pooled_spec_comparison.csv`](../../reference/pooled_spec_comparison.csv) (82 specifications) and [`reference/pooled_loso.csv`](../../reference/pooled_loso.csv).

**Carried-forward California specifications (within-state form), each with a common between-state level:**

| Within-state form (California spec it carries) | RMS log error, 7 states | Maine | Oregon | Vermont | Wisconsin rate 2027 → 2030 | Wisconsin additional permits, 2027–2031 |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| none | 0.20 | −0.20 | +0.28 | +0.12 | 0.82 → 1.30 | 9,517 |
| value (group_value) | 0.17 | −0.12 | +0.19 | +0.09 | 0.85 → 1.33 | 9,740 |
| value + size (group_value_size) | 0.14 | −0.01 | −0.03 | +0.06 | 0.92 → 1.39 | 10,326 |
| value hinge at $700k + size (group_value_hinge_size, CA main) | 0.19 | +0.35 | −0.11 | −0.02 | 1.02 → 1.55 | 11,546 |
| **value + income + size (group_value_income_size, CA best CV)** | **0.11** | **0.00** | **+0.03** | **+0.12** | **0.83 → 1.30** | **9,518** |
| + renter share | 0.14 | −0.05 | +0.02 | +0.24 | 0.86 → 1.34 | 9,838 |
| + pre-law activity (group analogue, California places and Wisconsin areas) | 0.14 | −0.15 | +0.15 | +0.09 | 0.82 → 1.27 | 9,304 |
| value + income + size, event time (Los Angeles from 2017) | 0.11 | 0.00 | +0.06 | +0.10 | 0.84 → 1.29 | 9,395 |
| hinge + size, event time | 0.18 | +0.33 | −0.07 | −0.02 | 1.01 → 1.61 | 11,585 |

Rates are permits per 1,000 single-family homes per year.

**Between-state market terms (within form: value + income + size):**

| Between-state term (stage 2 on the 8 law states) | RMS log error, 7 states | Maine | Oregon | Vermont | Wisconsin rate 2030 | Wisconsin additional permits, 2027–2031 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **common level (no market term)** | **0.11** | 0.00 | +0.03 | +0.12 | 1.30 | 9,518 |
| home value | 0.53 | −1.31 | +0.05 | +0.03 | 0.78 | 5,437 |
| income | 0.24 | −0.35 | +0.04 | +0.18 | 1.16 | 8,417 |
| price-to-income (owner idea b) | 0.31 | −0.66 | +0.24 | −0.11 | 0.76 | 5,307 |
| value + income | 0.58 | −1.35 | +0.55 | −0.12 | 0.76 | 5,275 |
| common level, stage 2 on all 11 clusters | 0.18 | −0.11 | −0.16 | 0.00 | 1.18 | 8,561 |
| *one-stage pooled, shared slopes (8 forms)* | *0.53–0.64* | *−0.97 to −1.41* | *+0.25 to +0.64* | *−0.54 to +0.18* | *0.41–0.68* | *2,618–4,417* |

Rates are permits per 1,000 single-family homes per year.

**Reading.**
- The specification that predicts held-out states best, and Maine, Oregon and Vermont in particular, is the California CV winner (value + income + size) used **within** states, with a **common** level across states.
- Every between-state market term makes Maine worse. Maine is the lowest-value state with data ($288,100) and the closest to Wisconsin ($260,900). With a home-value slope, Maine is under-predicted by a factor of about 3.7 (error −1.31).
- **Owner idea (a):** a diminishing term at the high end, the $700k hinge, does not help. Across states the pattern is the reverse: flat from $288k to $564k, high only in California.
- **Owner idea (b):** price-to-income scores 0.31, three times the error of the common level.
- The event-time variant changes little (9,395 vs 9,518 additional permits over 2027–2031).

**Selection caveat.** 82 specifications were scored on the same seven held-out states, and the main one was picked on that score. Its 0.11 error is therefore optimistic. The interval below uses the stage-2 spread τ instead.

### Main fit

Coefficients: [`reference/pooled_coefficients.csv`](../../reference/pooled_coefficients.csv). Standard errors are cluster-robust by state.

| Term (stage 1, within states) | Estimate | Rate ratio | Reading |
| --- | ---: | ---: | --- |
| Statewide law in force | 0.92 (SE 0.33) | ×2.51 | WA, RI, Denver before/after; Seattle 2024 |
| Local reform (city rules) | 0.78 (0.33) | ×2.18 | Austin before/after; Seattle, Portland, Denver vs their states |
| Year 1 vs year 4+ | −0.44 (0.26) | ×0.64 | |
| Year 2 vs year 4+ | −0.23 (0.13) | ×0.80 | |
| Year 3 vs year 4+ | −0.20 (0.09) | ×0.82 | |
| Value relative to state | 2.68 (0.14) | | mostly California's places |
| Income relative to state | −2.97 (0.19) | | mostly California's places |
| Size | 0.10 (0.03) | | |

Stage 2: each state's level with the law, at year 4 or later, at its typical place. All levels are permits per 1,000 single-family homes per year:

| California | Washington | Utah | Maine | Vermont | Massachusetts | Oregon | Rhode Island | Common level |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2.60 | 1.28 | 1.14 | 1.07 | 0.96 | 0.92 | 0.73 | 0.68 | 1.07 (τ = 0.42) |

**Held-out predictions (main specification).** Observed and predicted rates are permits per 1,000 single-family homes per year over the years shown.

| Held out | Series | Years | Observed | Predicted | Error |
| --- | --- | --- | ---: | ---: | ---: |
| ME | statewide | 2025 | 0.98 | 0.98 | 0.00 |
| OR | 32 cities | 2019–22 | 0.90 | 0.93 | +0.03 |
| VT | Chittenden | 2021–24 | 0.94 | 1.06 | +0.12 |
| WA | cities excl. Seattle | EY2024–26 | 0.78 | 0.92 | +0.17 |
| MA | statewide | 2025 | 0.79 | 0.95 | +0.18 |
| RI | statewide | 2025 | 0.97 | 0.91 | −0.06 |
| UT | MIH reporters | 2023–25 | 1.13 | 1.05 | −0.07 |
| CA | 457 jurisdictions | 2020–25 | 3.06 | 1.22 | −0.92 |
| Denver | city | 2025 | 0.82 | 1.72 | +0.73 |
| Portland | city | 2019–25 | 1.46 | 4.96 | +1.22 |
| Seattle | city | 2024 | 6.20 | 2.80 | −0.80 |
| Austin (local only) | city | 2016–23 | 1.52 | 0.78 | −0.67 |
| Minneapolis (local only) | city | 2017–25 | 0.26 | 0.93 | +1.27 |

Notes on the large errors:
- **California is under-predicted by a factor of 2.5.** Its post-2020 level reflects three rounds of law and a mature ADU industry; no other state is there yet.
- **Within-state slopes cannot be estimated without California.** With California held out, only aggregated state rows remain, so the California row is a check of level only.
- **City errors are large in both directions.** City levels are where the California within-state gradient is extrapolated.

### Wisconsin prediction

Wisconsin's rate in each year is:
- the common level, plus the law term, plus the year terms;
- times Wisconsin's own spread of value and income across its 1,925 areas.

The second factor is how the prediction comes "from Wisconsin's own home value and income distribution". The statewide rate barely depends on it: with no within-state terms the total is 9,517 against 9,518 additional permits over 2027–2031.

| Year | Rate (permits per 1,000 single-family homes per year) | With-law permits | Baseline permits | Additional permits |
| ---: | ---: | ---: | ---: | ---: |
| 2027 | 0.83 | 1,533 | 125 | 1,408 |
| 2028 | 1.03 | 1,900 | 129 | 1,770 |
| 2029 | 1.07 | 1,964 | 133 | 1,831 |
| 2030 | 1.30 | 2,388 | 133 | 2,254 |
| 2031 | 1.30 | 2,388 | 133 | 2,254 |
| **2027–2031** | mean 1.11 | **10,172** | 654 | **9,518** |

**Ramp.** The year terms are the ramp the pooled data support: rates in years 1–3 are 0.64, 0.80 and 0.82 times the year-4+ level.
- In the engine's form (ramp applied to the increment over the current rate), the implied ramp is **0.62, 0.78, 0.81, 1.0, 1.0**.
- Running `engine.run` with each area's plateau rate, this ramp and the 0.229 floor gives **9,514** additional permits over 2027–2031, against 9,518 directly.
- Do not apply the California ramp on top: that would apply the ramp twice.

**Interval (model uncertainty).** A new state's level is the common level ± the between-state spread τ = 0.42 (log scale, 8 states), inflated by √(1 + 1/8) for estimating the mean. With t quantiles for 7 degrees of freedom:
- **80% interval: rate × or ÷ 1.87.** Rates run 0.45 to 2.43 permits per 1,000 single-family homes per year; additional permits over 2027–2031 run **4,780 to 18,387**.
- **95% interval: × or ÷ 2.85.** Additional permits over 2027–2031 run 2,913 to 28,353.
- **Alternative from held-out errors** (RMS 0.11, 7 states): × or ÷ 1.17, so 8,014 to 11,283 additional permits over 2027–2031. This is narrower but optimistic, because of the specification selection.
- None of these covers the Midwest question below.

**Sensitivities on the main specification** ([`reference/pooled_sensitivities.csv`](../../reference/pooled_sensitivities.csv)). "Additional" is additional permits over 2027–2031; rates are permits per 1,000 single-family homes per year.

| Change | Year-1 rate | Year-4+ rate | Additional permits |
| --- | ---: | ---: | ---: |
| Main | 0.83 | 1.30 | 9,518 |
| New-house ADUs × 0.8 (state series and city counts) | 0.67 | 1.09 | 7,814 |
| Coverage-adjusted (ME, MA, RI) | 0.92 | 1.42 | 10,495 |
| Both measurement adjustments | 0.75 | 1.20 | 8,629 |
| City counts excluding new-house ADUs | 0.86 | 1.37 | 9,904 |
| Washington from local compliance | 0.84 | 1.39 | 10,206 |
| California coded from the 2017 law (2017–2025 rows) | 0.80 | 1.38 | 9,384 |
| California plateau rows only (2023–25) | 0.99 | 1.10 | 8,873 |
| Event time, Los Angeles from 2017 | 0.84 | 1.29 | 9,395 |
| Stage-1 weights by homes (California dominates) | 0.64 | 1.43 | 9,832 |
| Stage-1 weights by √home-years | 0.70 | 1.39 | 9,792 |
| Stage 2 without California | 0.74 | 1.14 | 8,311 |
| Stage 2 with all 11 clusters | 0.76 | 1.18 | 8,561 |
| No within-state market terms | 0.82 | 1.30 | 9,517 |
| Between: home value | 0.50 | 0.78 | 5,437 |
| Between: price-to-income | 0.49 | 0.76 | 5,307 |
| Wisconsin's own current rate × law ratio 2.5 (multiplicative law) | 0.12 | 0.18 | 758 |

### Validation on local-only reforms (Madison, Minneapolis)

[`reference/pooled_validation_local.csv`](../../reference/pooled_validation_local.csv). Rates are permits per 1,000 single-family homes per year.

| Place | Observed | Predicted: local rules, no statewide law | Observed ÷ predicted | Share of the log gap the law indicator (×2.5) explains |
| --- | ---: | ---: | ---: | ---: |
| Minneapolis (held out), 2017–2025 | 0.26 | 0.93 (1.29 value-only within) | 0.28 | 42% (35%) |
| Madison, 2022–2025 (never fitted) | 0.18 | 3.44 (1.86 value-only within) | 0.05 | 24% (27%) |
| Wisconsin statewide, current law | 0.072 | 0.52 (no local reform) | 0.14 | — |

**Answer: the statewide-law indicator does not explain the low Midwest rates.**
- Both cities sit about 4–19 times below what the pooled model expects for local rules without a statewide law, and the law term accounts for only a quarter to two-fifths of the log gap.
- Wisconsin's own current rate is 7 times below the model's no-law level.
- What the data do show, from four measured before/after pairs ([`reference/pooled_convergence.csv`](../../reference/pooled_convergence.csv)), is that the first-year rate after a statewide law is unrelated to the rate before it (log-log slope 0.01, SE 0.21):

  | State | Before the law | Year 1 after the law |
  | --- | ---: | ---: |
  | California | 0.12 | 0.60 |
  | Rhode Island | 0.23 | 0.97 |
  | Washington | 0.39 | 0.68 |
  | Vermont | 0.62 | 0.67 |

- At Wisconsin's current 0.072 permits per 1,000 single-family homes per year, that line implies a year-1 rate of 0.70.
- None of the four is a Midwest state. Iowa (strong law, first full year 2026) is the test to watch.

### Per-area values (by-product, secondary)

[`reference/pooled_wi_y_by_area.csv`](../../reference/pooled_wi_y_by_area.csv) has one row per engine area (1,925). Columns:
- `y_k1_central` to `y_k5_central`: the rate in each forecast year, permits per 1,000 single-family homes per year;
- `y_plateau_central`, with `y_plateau_lower_80` and `y_plateau_upper_80`;
- `y_nolaw_model`;
- `additional_5yr_central`;
- the raw main-specification plateau (`y_plateau_main_spec_raw`) and a flat alternative (`y_plateau_flat`, every area at the statewide rate).

**Allocation choice (deviation).** The statewide rate by year is the main specification's. It is spread across areas with the gentler **value-only** within-state gradient (slope 1.02), scaled so the homes-weighted rate equals the statewide rate each year.
- **Why:** the main specification's California income gradient puts lake and resort towns at 6–23 permits per 1,000 single-family homes per year (Manitowish Waters 23) and Madison at 3.4–8.6.
- **Result:** Madison's year-4+ rate is 1.75 permits per 1,000 single-family homes per year, or 348 additional permits over 2027–2031 (3.7% of the statewide additional, with 2.9% of the homes).
- **By context:** rural areas hold 39% of homes and 43% of the additional permits; urban areas 23% and 18%; suburban 24% and 29%; small communities 14% and 10%.
- Municipal values are indicative only; group totals are reliable.

## Comparison of the three candidate levels

All figures are additional permits over 2027–2031, statewide.

| Source | Additional permits | What it says |
| --- | ---: | --- |
| California-only regression (rule v1 / v1.1) | 2,337 / 2,119 | California's within-state value slope applied across states; under-predicts Maine about 4× |
| Review's triangulated central (R2) | about 3,800 | Judgment-free routes averaged; superseded by models fitted to all states |
| One-stage pooled regression | 2,618–4,417 | Same slope problem as California-only |
| **B. Pooled two-stage (central)** | **9,518** (80%: 4,780–18,387) | Wisconsin behaves like an average statewide-law state, ramp from pooled data |
| **A. Statewide adoption, as reported** | **8,654** (named adjustments 6,793–8,908) | Median of states actually observed |
| Previous upper path | 5,936 | Below both A and B |

## Deviations (stated, with reasons)

1. **Not pre-registered.** Specification choice used leave-one-state-out on the same seven states (82 specifications), so the held-out error is optimistic. The interval uses the stage-2 spread τ, not the held-out error.
2. **Two-stage within/between form** instead of a single state-weighted regression. The single form is reported (one-stage rows of the comparison table) and fails Maine. The two-stage form is equivalent to a within–between random-intercept model.
3. **No between-state market term in the main specification.** The owner's predictors (log value with a high-end term; price-to-income or income) are carried inside states and tested between states. Between states they predict held-out states worse, so the statewide level is a common level.
4. **California rows are 2020–2025 by year** (years 1–6 after the 2019 package), not only the 2023–25 plateau, so the ramp is estimated. Plateau-only gives 8,873 additional permits over 2027–2031; coding from the 2017 law gives 9,384.
5. **Stage 2 uses the eight statewide-law states.** Austin, Denver and Minneapolis enter stage 1 only. Using all 11 gives 8,561 additional permits over 2027–2031.
6. **Pre-law activity** enters only within states (California's 2017–19 rate by place, Wisconsin's current rate by area). Most other states have no pre-law count. The between-state relation is shown separately (convergence table).
7. **Size** is the member geography's homes, centred within its state, so Wisconsin's many small towns do not lower its level.
8. **City counts include new-house ADUs** in the main fit, to match the state series. Excluding them is a sensitivity.
9. **Dropped rows:**
   - partial law years (Oregon 2018, Rhode Island 2024, Maine 2024, Denver 2024);
   - Portland's fee-waiver years;
   - Vermont 2016–20;
   - reform years (Seattle 2019, Austin 2015).
10. **Year 5 = year-4+ level in B, and = year 4 held in A.** No state has data for year 5 except California.
11. **Allocation** uses the value-only within gradient (see per-area section).
12. **Not used:** the Madison floor (0.229 permits per 1,000 single-family homes per year), in the direct calculation, because it never binds statewide. The engine check includes it.
13. **Not used:** Tucson, Spokane, New Hampshire, Honolulu, Montgomery County and Bozeman. They are local reforms, proxies or source leads.

## What the conductor must integrate or decide

- **Central and upper.** The owner framed A as the upper and B as the central. On the data, B (9,518) is slightly above A (8,654) in additional permits over 2027–2031: they measure the same thing. Options:
  - keep B central and A as a cross-check;
  - or use B's 80% interval ends (4,780 and 18,387) as lower and upper.
- **Measurement adjustments** are optional sensitivities. With new-house ADUs × 0.8, A is 6,793 and B is 7,814 additional permits over 2027–2031.
- **Midwest gap.** The packet should state that Madison, Minneapolis and Wisconsin's own current rate sit about 4–19 times below the pooled no-law expectation. The "multiplicative law" reading (758 additional permits over 2027–2031) is the low end of the evidence.
- **Engine.** Use `y_plateau_central` per area with the implied ramp 0.62, 0.78, 0.81, 1, 1. That gives 9,514 additional permits over 2027–2031 with the 0.229 floor. Do not apply the California ramp as well.
- **Docs to update (not mine):** README (R2 options), CA_REGRESSION.md (it is no longer the central), AQ-026/AQ-034.

## Reproduce

```
uv run python scripts/run_ca_regression.py --skip-fetch     # ca_dataset.parquet (if not already built)
uv run python scripts/run_pooled_regression.py              # writes the files below (about 1 minute)
bash scripts/test.sh                                        # offline, incl. tests/test_pooled_regression.py
```

- **Code:** `missing_middleware/comparison/pooled_regression.py`; runner `scripts/run_pooled_regression.py`; tests `tests/test_pooled_regression.py` (fixtures in `tests/fixtures/pooled_regression/`).
- **Outputs (`reference/`):**
  - `statewide_adoption_curve.csv`, `pooled_adoption_points.csv`;
  - `pooled_dataset_rows.csv`, `pooled_members_summary.csv`;
  - `pooled_spec_comparison.csv`, `pooled_loso.csv`, `pooled_coefficients.csv`;
  - `pooled_wi_statewide.csv`, `pooled_wi_y_by_area.csv`;
  - `pooled_sensitivities.csv`, `pooled_validation_local.csv`, `pooled_convergence.csv`.
- **Processed:** `data/processed/pooled_regression/summary.json`.
- **Inputs:** all local. They are the ACS 2020–2024 5-year table-based summary files already downloaded:
  - B25024 in `data/raw/census_acs5_2024_tbsf/`;
  - B25077, B19013, B25064 and B25003 in `data/raw/census_acs5_2024_tbsf_market/`.
  - No new downloads.
