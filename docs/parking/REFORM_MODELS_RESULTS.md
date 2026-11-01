# Parking: full set of reform-prediction models, results (rounds 1–2)

Written 2026-11-01 by the parking conductor. Plan and changes: [REFORM_MODELS_PLAN.md](REFORM_MODELS_PLAN.md). Script: `scripts/run_parking_reform_models.py`. Files: `reference/parking_reform_models_*_r2.csv`. Round 2 rescored the round 1 fits from their checkpoints.

## Answer

- **No model finds a parking effect that stands out from noise.**
  - The tree models (random forest, honest forest, depth-3 tree) never split on the repeal trait. Their 0 means "no signal learned", not a measured 0.
  - The boosted trees give −398 homes (−1,674 to 0).
  - Every other model's Wisconsin net sits inside its own fake-repeal range.
- **Predicting held-out repeal cities,** the random forest is closest (0.404), about as close as same pace (0.410). It beats same pace in 59% of rows.
- **Where a negative comes from:** two big cities whose permits fell after repeal. San Francisco permitted 0.37–0.55 of its same pace in 2018–2019, and Minneapolis 0.52. Without San Francisco, the repeal places permitted 0.95 of same pace. The median repeal place permitted 1.14 times same pace.

## Scores

The 58 held-out repeal rows come from 28 repeal places, each left out in turn.

- **Summary score:** the median of |log(predicted ÷ actual)|, with the repeal switched on; lower is better.
- **Wisconsin net:** homes over 2027–2031, scaled to the 122,619 baseline. The range is the 5th to 95th percentile over the 28 leave-one-out fits.
- **Fake range:** the same net when 28 never-reformed places get a fake repeal (5 seeds).

| Model | Score | Total ratio | Beats same pace | Wisconsin net | 5th–95th | Fake range |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Same pace | 0.410 | 1.45 | – | 0 | – | – |
| Same pace × level | 0.416 | 1.83 | 50% | 0 | – | – |
| Same pace + route A high end | 0.484 | 1.71 | 50% | 19,953 | – | – |
| Poisson regression | 0.459 | 1.05 | 48% | −24,240 | −26,034 to −21,864 | −35,515 to 13,664 |
| Lasso | 0.465 | 1.06 | 55% | −23,461 | −25,224 to −22,371 | −24,460 to 11,913 |
| Elastic net | 0.464 | 1.06 | 55% | −23,504 | −25,262 to −22,416 | −23,665 to 10,297 |
| Depth-3 tree | 0.552 | 1.82 | 50% | 0 | 0 | 0 |
| Random forest | 0.404 | 1.30 | 59% | 0 | 0 | 0 |
| Boosted trees | 0.463 | 1.26 | 57% | −398 | −1,674 to 0 | −12,517 to 1,366 |
| Honest forest (econml, one-off) | 0.415 | 1.36 | 59% | 0 | 0 | 0 to 0 |
| 50 nearest neighbours | 1.033 | 1.77 | 29% | 26,562 | 18,410 to 33,198 | −37,960 to 5,130 |
| Causal forest (econml, one-off) | 0.724 | 1.07 | 36% | 11,660 | −7,557 to 26,982 | −55,827 to 22,158 |
| Causal forest (scikit-learn, round 3) | 0.582 | 0.99 | 40% | −20,825 | −35,715 to −2,558 | −57,786 to 16,754 |

## Reading

- **Audit (2026-11-01): clean, no coding error.** On the 28 held-out repeal places, same pace (0.410) beats the negative-effect regressions (0.459–0.465) and same pace + route A high end (0.484). So a central of about 0 is evidence-based, and 19,937 is labelled "placebo high end; held-out places fit 0 better".
- **Repeal places against other places:** the repeal places ran at 0.69 of same pace in total (0.95 without San Francisco). Places with no reform ran at about 1.2 (held-out ratio 0.82 = predicted ÷ actual). The noise check is the headline placebo, where the repeal average sits at the 22nd percentile of 20,000 fake-repeal sets.
- **The regressions' negative is about half San Francisco:**

| Wisconsin net, 2027–2031 | All 28 | San Francisco out | Minneapolis out | Both out |
| --- | ---: | ---: | ---: | ---: |
| Poisson regression | −24,240 | −15,419 | −22,624 | −8,942 |
| Lasso | −23,461 | −8,257 | −22,909 | −4,597 |
| Elastic net | −23,504 | −8,149 | −22,956 | −4,474 |
| Boosted trees | −398 | 0 | −316 | 0 |
| Causal forest (econml) | +11,660 | +13,665 | +34,989 | +34,861 |

The jackknife band above hides San Francisco, because its single leave-out sits at the band's edge. File: `reference/parking_reform_models_sf_mpls_out.csv` (script `scripts/check_parking_reform_sf_mpls.py`).

- **The regressions' −23,500 is driven by San Francisco and Minneapolis,** and lies within the fake range of the Poisson regression and the elastic net. Lasso's sits just inside its fake low (−24,460).
- **The causal forest** has a negative effect on the held-out repeal places (−63 homes per place per year) but a positive one for Wisconsin (+11,660). Its fake range is ±56,000, so it does not separate a repeal effect from noise.
- **50 nearest neighbours** scores worst (1.03) and shifts its neighbours with the trait.
- **Same pace overpredicted the repeal places by 45% in total,** almost all from San Francisco.

- **The scikit-learn causal forest (round 3)** gives −20,825 for Wisconsin, but its fake range (−57,786 to +16,754) covers it. It scores worse than same pace on held-out repeal places (0.582 against 0.410). The two causal forests disagree in sign (econml +11,660), which also says the signal is noise. It replaces econml for any future use.

## Possible tool lines (for Ryan, not applied)

None of these models gives a better line than the existing ones (central 0, high end 19,937). The random forest and honest forest support "about 0". The regressions' negative figure is a San Francisco and Minneapolis effect inside the noise.

## Flags

- **Worst miss in every model:** San Francisco, origin 2018 or 2019 (actual 1,577–1,689 a year).
- **Causal forest:** 3 held-out predictions below 0 were clipped for scoring (round 1's NaN score).
