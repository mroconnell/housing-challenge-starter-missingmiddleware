# TOD full model runs: results

Plan: [MODEL_MENU_PLAN.md](MODEL_MENU_PLAN.md). Script: `scripts/run_tod_model_menu.py`. Tables: `reference/tod_menu_pace_*.csv`.

## No-reform baseline, round 2 (2026-10-31)

Score: median |log(predicted ÷ actual)| of 5-year homes over city-windows; lower is better.
- **Held-out city:** 39 city-windows in 13 cities.
- **Later years:** the 4 no-reform cities' after windows, too few to weigh alone.

Wisconsin column: homes on main-case near-stop lots in Milwaukee and Madison, 2027–2031, scaled to the state by the near-stop baseline (×1.147, an assumption).

| Method | Held-out city | Later years | Wisconsin near stops 2027–2031 (Milwaukee + Madison → state) |
| --- | ---: | ---: | ---: |
| **Benchmark: same pace as before (permit survey)** | 0.59 | 0.38 | — |
| Plain average | 0.92 | 0.39 | 8,875 |
| Linear regression | 0.60 | 0.60 | 17,149 |
| LASSO | 0.43 | 0.59 | 13,545 |
| Regression tree | 0.73 | 0.31 | 12,855 |
| **Random forest** | **0.36** | **0.14** | **16,741** |
| Gradient boosting | 0.41 | 0.19 | 25,524 |
| Nearest neighbours | 1.18 | 1.72 | 99,218 |
| Multilevel | 1.77 | 2.76 | 181,357 |
| Causal forest | n/a (no treatment in a no-reform model) | | |

Reference points for Wisconsin near stops, 2027–2031:
- tool today: 14,464;
- re-based: 18,322;
- recent pace: Milwaukee and Madison built 14,980 homes near stops over 2019–2024 on a 5-year basis, which is about 17,180 scaled to the state.

### Checks so far

- **Leak check on the best scores.** The single-part model (homes per lot) beats the permit survey, while pace rounds 1–4 (two-part, per acre) did not. Re-run on the pace loop's 10 cities, gradient boosting still scores 0.49 / 0.23 against 0.58 / 0.38. The trait list has no outcome-window values, and the training-city rule leaves out each city's own twin. So the gain comes from the model form, not a leak.
- **Worst misses traced:**
  - Kansas City 2006–2011 is a forecast across the housing crash. The permit survey also misses it (12,145 vs 3,650), and Kansas City's permit file holds about 60% of the survey's count.
  - Bellevue 2003–2008: the study area is tiny (26 homes).
  - Saint Paul: one before year.
- **Nearest neighbours and multilevel fail both tests and blow up in Wisconsin.** They extrapolate per-lot homes linearly from 15 principal components. These are method failures, not data errors; they are not usable as lines.
- **Gradient boosting:** Milwaukee 12,724 vs a recent 5,197 per 5 years (2.4×). This is to be traced in the next round.
