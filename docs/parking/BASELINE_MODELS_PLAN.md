# Parking: full set of baseline (no-reform) models, plan written before running

Written 2026-10-31 by the parking conductor. Ryan: "run several models (I think we had a list of 8-10 including big causal forest runs) ... for baseline and each predictive model", then look for mistakes, fix, rerun until a clean run, and then choose a baseline. The tool's numbers do not change without Ryan's approval. No result below has been computed before this file was committed.

## Data and tests (as the no-reform model, round 6)

- **Rows:** never-reformed places, plus reformed places in years before their reform. The unit is homes permitted per place per year, averaged over years 2–6 after the origin. Homes at the origin come from the ACS release ending at the origin.
- **Inputs:** log homes, past rates (1, 3 and 5 years), share in 2+ unit buildings, trend, population change, state and division momentum, size class, and ACS traits (income, renter share, vacancy, share built before 1980). Plus the fake-reform trait.
- **Held-out places:** 20% per Census division, with 5 seeds (20261031–35).
- **Held-out years:** fit on origins 2016–2017, score on 2018–2019.
- **Wisconsin:** held out whole. Back-test from origin 2019; forecast from origin 2025, scaled to the 122,619 central (and 118,822 as published).
- **Settings:** chosen by 5-fold cross-validation over places within the fitting origins, using the summary score.

## Models (11)

| # | Model | Notes |
| --- | --- | --- |
| 1 | M0 same pace | flat 3-year average (the current baseline) |
| 2 | M1 same pace × state momentum | |
| 3 | M2 shrunk 3-year | empirical Bayes toward division × size class |
| 4 | Weighted Poisson regression | the round 6 M3b |
| 5 | Lasso | rate per 1,000 homes, home-weighted |
| 6 | Elastic net | as lasso |
| 7 | Depth-3 tree | |
| 8 | Random forest | 300 trees |
| 9 | Boosted trees | the round 6 M4 |
| 10 | Honest forest (generalized random forest) | `econml.grf.RegressionForest`, honest splitting, 500 trees; the causal-forest family, used here without a treatment because the baseline has none (the reform runs use the causal forest with the repeal trait) |
| 11 | 50 nearest neighbours | standardized inputs |

## Reported for each (no pass bar)

- Summary score (median |log|) on held-out places at later years, with the seed range.
- The same on state totals.
- Total ratio.
- Wisconsin back-test: predicted ÷ actual.
- Wisconsin 2027–2031, scaled.
- Fake-reform on−off, for the models that use the trait.

## Checks after each run (flag, never stop)

- Negative or non-finite predictions, counted and clipped.
- The worst miss per model, traced.
- Models whose Wisconsin total is more than 25% from same pace, traced to the places that drive the gap.
- Rerun under a different Python hash seed, to confirm reproducibility.

## Use

The audit reviews each round. Once a round is clean, a baseline is chosen with Ryan and the audit, and then the reform-prediction runs start.

## Changes after writing
- **2026-10-31, round 1 checks → round 2 (before round 2 ran):**
  - **Coding/model error:** lasso and elastic net were fitted on the raw rate and predicted below zero for 10,895 and 14,356 held-out rows. Clipping those to 0 skewed them, and lasso's Wisconsin total came out 1.25× same pace. In round 2 both are fitted on log(1 + rate) and back-transformed, as the other regressions already were in spirit.
  - **Outliers traced:**
    - The worst miss is Nashville-Davidson for most models: actual 12,408 a year against 4,573–7,755 predicted. This is a real boom (see NO_REFORM_MODEL_RESULTS).
    - Brooklyn is the worst for M1 and elastic net: actual 10,493 against 3,633–5,297. Brooklyn's 2019–2022 permits rose ahead of the 421-a tax break's expiry. This is a real surge, not a data error.
    - The depth-3 tree (1.23×) and 50 nearest neighbours (1.18×) are far from same pace in Wisconsin. They are coarse, and their held-out place scores are the worst (0.69 and 0.64).
  - **Fake reform:** the 50 nearest neighbours swing ±38 homes per place, because the trait shifts which neighbours are chosen. Elastic net and the Poisson regression swing as before. The trees and forests stay near 0.
  - Round 2 also reruns under a different Python hash seed, to check that it reproduces.
- **2026-10-31, audit review of round 1 → round 3 (round 2 was stopped before finishing; its log fix is kept):**
  - **Main issue (test design):** the "state totals" score summed training places at the later origins. For those places, the models had already seen 4 of the 5 outcome years, through the fitting origins' outcomes. So the trees' win there (0.105 against 0.221) is not a fair held-out result. The same applied to the no-reform rounds, and to the claim in the tool's trees sensitivity note.
  - **Fix:** state totals come from whole held-out Census divisions. Each of the 9 divisions is predicted from the other 8 (fitted on origins 2016–2017, Wisconsin excluded), and each of its states' totals is scored at origins 2018–2019. A 90% range comes from 2,000 resamples of state totals. Settings: each model's most common cross-validated choice.
  - **Calendar overlap:** the fitted outcomes run to 2023 and the test outcomes to 2025, so the years overlap. It cannot be removed with permit data starting in 2012. Stated.
  - **Wisconsin 2019 back-test:** now fitted on origins 2016–2017 only.
  - **Grids extended by one step where the choice sat at an edge:**
    - Poisson regression from 1e-5;
    - lasso and elastic net (log target) 1e-4 to 0.5;
    - depth-3 tree leaf 5;
    - random forest and honest forest leaf 2;
    - boosting adds (0.05, 63) and (0.1, 31).
  - **Rule (audit):** if the held-out state totals show no clear model win, same pace stays as the simplest baseline.
