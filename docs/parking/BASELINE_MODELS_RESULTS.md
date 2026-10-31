# Parking: full set of baseline (no-reform) models, results (rounds 1–4)

Written 2026-10-31 by the parking conductor. Plan and every round's changes: [BASELINE_MODELS_PLAN.md](BASELINE_MODELS_PLAN.md). Script: `scripts/run_parking_baseline_models.py`. Files: `reference/parking_baseline_models_*_r4.csv`. Round 4 is reproducible: a rerun under a different Python hash seed matched to the 15th decimal place.

## Answer

- **No model clearly beats same pace.**
  - **Single places:** same pace (0.533) is about as good as anything. Lasso and elastic net on the log rate score 0.520, and the seed ranges overlap.
  - **State totals:** the forests (0.113–0.115) only match same pace times one national level factor (M0L, 0.121). The random forest beats M0L in 51% of state-origins; the honest forest in 47%. They learn the national level of the overlapping years, not better state predictions.
- **Recommendation (audit agrees; Ryan's call):**
  - Keep same pace, 122,619, as the central baseline.
  - An optional side line, "if recent strength continues", would sit at about 131,000–133,000 (the forests). M0L's 154,951 applies 2020–2025's full strength (1.26× the earlier pace) to every place.

## Scores (round 4)

The summary score is the median of |log(predicted ÷ actual)|; lower is better.
- **Places:** held-out places at the later origins, averaged over 5 seeds, with the seed range in brackets.
- **State totals:** 92 state × origin totals from 9 held-out Census divisions, with the 90% bootstrap range in brackets.
- **Wisconsin:** the 2019 back-test is fitted on origins 2016–2017. The 2027–2031 forecast is scaled to the 122,619 central.

| Model | Places | State totals | Beats M0L | Wisconsin back-test, predicted ÷ actual | Wisconsin 2027–2031 |
| --- | --- | --- | ---: | ---: | ---: |
| M0 same pace | 0.533 (0.521–0.555) | 0.227 (0.176–0.249) | 41% | 0.77 | 122,619 |
| M0L same pace × level | 0.548 | 0.121 (0.090–0.166) | – | 1.01 | 154,951 |
| M1 × state momentum | 0.537 | 0.186 | 41% | 0.78 | 123,202 |
| M2 shrunk | 0.528 | 0.266 | 36% | 0.69 | 103,795 |
| Poisson regression | 0.592 | 0.133 | 47% | 0.89 | 132,320 |
| Lasso (log rate) | 0.520 (0.505–0.532) | 0.174 | 41% | 0.72 | 108,916 |
| Elastic net (log rate) | 0.520 | 0.176 | 41% | 0.72 | 108,913 |
| Depth-3 tree | 0.692 | 0.145 | 40% | 1.04 | 151,349 |
| Random forest | 0.616 | 0.113 (0.090–0.150) | 51% | 0.95 | 132,827 |
| Boosted trees | 0.564 | 0.144 | 42% | 0.83 | 110,818 |
| Honest forest (GRF) | 0.609 | 0.115 (0.094–0.150) | 47% | 0.95 | 130,969 |
| 50 nearest neighbours | 0.637 | 0.177 | 33% | 1.01 | 144,655 |

## Caveats

- **Calendar overlap:** the fitted outcomes run to 2023, and the test outcomes to 2025. It cannot be removed with permit files that start in 2012.
- **Tuning:** the settings for the division runs were picked by cross-validation over places that included the held-out divisions (fitting origins only).
- **Boosting:** its largest setting (0.05, 127 leaves) was still chosen in 3 of 5 seeds. Going larger made state totals worse (0.125 in round 3, 0.144 in round 4), so the grid stops there.
- **Fake reform:** trees and forests stay near 0. The 50 nearest neighbours (±38) and the Poisson regression and elastic net (up to +46 and +51 homes per place per year) swing.

## Rounds

| Round | Fix |
| --- | --- |
| 1 | First run |
| 2 | Lasso and elastic net moved to the log rate; they had predicted below zero for 10,895 and 14,356 rows. Stopped before finishing. |
| 3 | State totals from held-out divisions; the earlier test reused training places. Wisconsin back-test fitted on 2016–2017 only. Grids extended. |
| 4 | M0L benchmark; share of state-origins beating M0L; grids extended again; reproducibility rerun |
