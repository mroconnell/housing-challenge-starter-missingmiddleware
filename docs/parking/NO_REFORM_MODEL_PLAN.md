# Parking: a model of homes permitted with no parking reform, plan written before running

Written 2026-10-31 by the parking conductor. Ryan asked each scenario to predict "how many homes would have been developed in the same state without ANY reform", trained for parking on places with no parking reform, and to run fast fit-and-fix rounds. The coordinator asked that the three scenarios agree on Wisconsin's no-reform total, or explain why not. No outcome below has been computed before this file was committed. Changes go in the last section with a date and a reason.

## 1. Question

For a place with no parking reform, how many homes will it permit per year over the next five years, given only data that every state has?

- **Unit:** housing units authorized by building permits, per place per year (Census Building Permits Survey, BPS), averaged over the five years after an origin year.
- **Same unit as the shared baseline** (`docs/shared/HOUSING_BASELINE.md`): 122,619 units over 2027–2031 for Wisconsin, with Milwaukee's apartments added; 118,822 with Census as published.

## 2. Data (public, any state)

| Input | Source | Years |
| --- | --- | --- |
| Permits by place, year and building size | BPS place files, whole country (`data/raw/census_bps_place_us`), scaled reported months as in V6 | 2012–2025 |
| Homes at the origin | ACS 2020–2024 homes (B25002) minus permits issued from the origin year to 2024, as in V4 | – |
| Population at the origin | BPS place population for the origin year | 2012–2025 |
| Place traits | ACS 2020–2024: median household income, share renting, vacancy, share of homes built before 1980 | 2020–2024 (after the origins; flagged, see 7) |
| Reform coding | `reference/parking_reform_material.csv` (V7 coding) and the V7s state laws | – |

## 3. Training and test places

- **No-reform places:** places with no material parking entry at any date, outside California, Oregon and Washington from the year their state law applies. Undated material entries count as reformed.
- **Repeal places before their repeal:** an origin is used only if its five outcome years all end before the repeal year.
- **Origins:** 2016 to 2020. Features use the origin year and the four before it. The outcome is the average of the five years after (2017–2021 up to 2021–2025).
- **Places:** every place with all years present and at least 1,000 homes. County balance rows are left out.

## 4. Holdouts

Two holdouts, both set now:
1. **Held-out places:** 20% of places drawn at random within each Census division (seed 20261031). They are never used to fit or choose.
2. **Held-out years:** fitting and choosing use origins 2016–2018. Scoring uses origins 2019–2020.

The score is reported on held-out places at held-out origins. **Wisconsin** is held out whole, in addition: no Wisconsin place is used to fit or choose.

## 5. Models, simplest first

| Model | What it predicts |
| --- | --- |
| M0 flat 3-year | The place's average over the origin year and the two before. This is the shared baseline's rule. |
| M1 flat 3-year × state momentum | M0 times the state's own 3-year over 5-year ratio. |
| M2 shrunk 3-year | M0's rate per 1,000 homes, pulled toward the average of places of the same size class in the same division, by how noisy the place's own years are (empirical Bayes). |
| M3 regression | Poisson regression of the five-year average on log homes, past rates (1, 3 and 5 years, per 1,000 homes), share in 2+ unit buildings, the place's trend, state and division momentum, and size class. M3a without the ACS traits; M3b with them. |
| M4 boosted trees | Gradient-boosted trees (Poisson loss, scikit-learn) on the M3b inputs. |

Settings for M2–M4 are chosen by 5-fold cross-validation over places within the fitting origins, grouped by place.

## 6. Scores and pass rule

- **Main score:** error per unit permitted, the shared baseline's score: the sum over places of |predicted − actual| ÷ the sum of actual units. M0 scored 0.526 in Wisconsin's own test.
- **Also:** the state total's error (predicted ÷ actual), for every state and for Wisconsin.
- **90% range:** 2,000 resamples of held-out places.
- **Pass rule:** a model passes if it beats M0 on the main score in held-out places at held-out years, with the 90% range of the difference above zero, and does not do worse than M0 in Wisconsin. If several pass, the one with the best cross-validation score is chosen, not the best test score.

## 7. Flags (flag only, never stop)

- Places with estimated permit months in the window.
- Homes back-cast below half of ACS homes.
- ACS traits come from after every origin (audit 2e); M3a has none, so the gap between M3a and M3b shows how much this matters.
- The worst-missed place in each round, traced.
- Milwaukee's apartments are under-counted in BPS, so the Wisconsin comparison is shown both against Census as published and with the baseline's Milwaukee adjustment.

## 8. Use

- **Comparison with the baseline:** the chosen model is run from origin 2025 on every Wisconsin place. Its five-year total is set beside 122,619 and 118,822.
- **If a model passes:** it goes to Ryan as a candidate for the shared baseline and for the parking scenario's comparison side, after TOD and ADU report theirs.
- **If none passes:** the flat 3-year baseline stands, with the test as evidence.
- **Rounds:** each round's fixes are logged below before the round is run. Rounds go to the audit through the coordinator.

## Changes after writing
- **2026-10-31, audit judging plan (`audit/no_reform_model_judging_plan_2026-10-31.md`), before any outcome was computed:**
  - **One summary score, fixed now:** the median over held-out places of |log((predicted + 0.5) ÷ (actual + 0.5))|, with both in units per place per year. The 0.5 keeps places with no permits in. Error per unit permitted stays as a second score, for comparison with the baseline's 0.526.
  - **Benchmark:** M0 ("same pace as before", from the national permit survey). A model must beat it on both held-out tests (places, and later years).
  - **Seed spread:** the place holdout is redrawn with 5 seeds (20261031 to 20261035). M2–M4 are refit on each. A model passes only if it beats M0 under all 5.
  - **Fake-reform placebo:** 10% of no-reform training places get a fake reform year, drawn from the real repeal years. M3 and M4 get a trait "fake reform in effect". The prediction with it on, minus with it off, should be about 0, and is reported in units per place per year.
  - **Training set:** as section 3, never-reformed places in all years, and reformed places only in years before their reform, so reform status is a dated trait, not a reason to drop a place.
- **2026-10-31, owner on the level (before running):** Ryan: parking should line up with TOD (city level) or ADU (possibly statewide), not a third level. Every model is also scored on **state totals** (the sum of a state's places, at the later origins), with the same summary score across states. A flat statewide average gives the same total as summing flat city averages, so the level matters only for models that are not flat. The Wisconsin comparison is against 118,822 (Census as published), since the Milwaukee property-file fix uses city-only data that not every state has.
- **2026-10-31, audit review of this plan (before any outcome was computed; a first run stopped on a code error before scoring):**
  - **No pass bar.** This follows Ryan's earlier rule against "beat the baseline" bars. The model is chosen by cross-validation on the fitting origins, as planned. The held-out score, the seed spread and the difference from M0 (with its 90% range) are reported side by side. The 90% range and the 5 seeds measure noise; they are not a gate.
  - **Horizon:** the outcome is years 2–6 after the origin, so that origin 2025 predicts the tool's 2027–2031. The fitting origins become 2016–2017 and the test origins 2018–2019 (outcomes up to 2025). The Wisconsin back-test uses origin 2019 (outcomes 2021–2025).
  - **COVID:** the held-out outcomes include 2020–2021. There is no adjustment; it is noted.
- **2026-10-31, round 2 fixes (after round 1, before round 2 was run).** Round 1 results are kept in `reference/parking_no_reform_*_r1.csv`.
  - **Data fix:** 11 groups of BPS keys share one ACS geography. Each of New York City's five boroughs was given all 3.7 million of the city's homes; Staten Island was round 1's second-worst miss for M4. These keys are left out and listed in the checks.
  - **Coding fix:** the flag rows wrote to the wrong columns and printed blank.
  - **Regression inputs:** the M3 regressions were unstable. Their fake-reform on-minus-off ranged from −62 to +50 units per place per year, and they had the worst scores. Rates now enter as log(1 + rate), and the trend is clipped at its 1st and 99th percentiles. M0, M1 and M2 do not use these inputs.
  - **Wisconsin coverage:** the 331 Wisconsin places with at least 1,000 homes and every year present hold about 70% of the state's permits. Each model's Wisconsin total is also shown as its ratio to M0, times 118,822.
- **2026-10-31, audit review of round 1 (logged while round 2 ran; these go into round 3):**
  - **Fix the shared-geography keys instead of dropping them:**
    - New York City's five boroughs get their own county's ACS homes (Bronx, Kings, New York, Queens and Richmond counties).
    - Pieces of one town or village split across counties or parts are summed into one place (Bellmont NY, Danville GA, Rushville NY, Red Springs NC, Rutherford College NC).
    - Rows with no geography of their own are dropped and named: Alaska's balance-of-state parts, Ohio's county "Part" and "Unincorporated" rows, and Cabot village, VT, which sits inside Cabot town.
    - Round 2 dropped all 11 groups. It is kept as a check.
  - **General land-mismatch flag:** a place-origin whose 3-year rate (permits per 1,000 homes per year) is outside the national 1st–99th percentile is flagged. The 10 largest by homes are traced. Consolidated city-counties are also listed (Nashville-Davidson, Indianapolis, Louisville, Honolulu and others).
  - **Main baseline:** place-level same pace (M0) stays the main rule, consistent with TOD and ADU. It is shown beside its past bias: totals ran 17% low on held-out places, and 22% low in Wisconsin's 2021–2025 back-test. Boosted trees' state total is a sensitivity for Ryan. There is no ad-hoc correction.
  - Seed spread is reported for every score.
- **2026-10-31, audit basic-error sweep §5 (round 4, before running):**
  - **Leak:** homes at the origin were ACS 2020–2024 homes minus permits issued after the origin. For origins 2018–2019 that subtracts the outcome years' own permits, so future data entered the rate inputs and the weights. M0 and M1 are not affected. M2–M4 and the 114,042 side case are.
  - **Fix:** homes at the origin are now the Census population estimate for the origin year (in the permit file) times the place's homes per resident in ACS 2020–2024. Household size changes slowly, so this uses no outcome-year permits. Rows with no valid population (missing, 0 or the 99999 placeholder) are dropped and counted. New York City's boroughs use their county population.
  - **Labels:** the Wisconsin file now has two columns, one scaled to the 122,619 central and one to the 118,822 as-published sensitivity. In GATE2_PACKET, 118,822 is now labelled as baseline version 1.
  - Round 4 reruns the no-reform model, and the 114,042 side case is recomputed from it. The net Wisconsin rounds use round 4 data.
- **2026-10-31, round 5 (found while tracing the net round 5 fake-reform outlier; before running):**
  - **Data finding:** the permit file's population is the last census count, not a yearly estimate. 94% of places show the same figure in every year from 2013 to 2021, and it changes in 2022. Example: Hardeeville, SC shows 2,952 people (the 2010 count) until 2021 and 8,438 from 2022, while its permits rose from 209 a year in 2016 to 800 in 2021.
  - **Effect:** round 4's homes at the origin were 2010-sized for the 2016–2019 origins, so fast-growing places looked even faster.
  - **Fix:** homes at the origin = census-year population × the place's ACS homes per resident, plus permits issued from the census year (2010, or 2020 from 2022) up to the origin. The permit files start in 2012, so 2010–2011 permits are missing; this is noted. No outcome-year data are used.
