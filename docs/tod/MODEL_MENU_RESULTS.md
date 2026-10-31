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

## No-reform baseline, round 3 (audit checks 1 and 2)

Changes:
1. **Milwaukee survey fix** (shared baseline rule P8): permit years 2015–2024 use survey 1–2 unit permits plus property-file 3+ unit homes built the next year. This applies to both the benchmark and the place-pace trait.
2. **Timing check:** each method was rerun without 2010 census homes and without ACS traits, which are dated after many windows start.

Scores are median |log|. "Matched" covers the 29 city-windows where the survey exists. "City median" is the median across cities of each city's median. "2011+" is the 12 windows starting in 2011 or later, where 2010 census homes predate the window.

| Method | Traits | Held-out city (matched) | City median | 2011+ windows | Later years (4) | Wisconsin near stops |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Survey, same pace | — | 0.55 | 0.52 | 0.54 | 0.38 | — |
| Random forest | all | 0.36 | 0.38 | 0.22 | 0.14 | 16,588 |
| Gradient boosting | all | 0.37 | 0.35 | 0.24 | 0.20 | 25,078 |
| Random forest | no dated traits | 0.76 | 0.67 | 0.69 | 0.22 | 13,254 |
| Gradient boosting | no dated traits | 0.81 | 0.78 | 0.79 | 0.11 | 17,517 |
| Regression tree | no dated traits | 0.57 | 0.69 | 0.36 | 0.55 | 13,351 |
| LASSO | no dated traits | 0.93 | 0.83 | 0.80 | 0.61 | 12,209 |
| Linear | no dated traits | 0.67 | 0.87 | 0.80 | 0.83 | 10,737 |
| Plain average | — | 0.97 | 0.90 | 0.70 | 0.39 | 8,875 |

Reading:
- **The forests' edge depends on existing homes and census traits.** Without them, no method beats the survey on held-out cities.
- **Where the census homes predate the window** (12 windows from 2011), the forests with all traits still beat the survey (0.22–0.24 vs 0.54). The ACS traits are still dated at the reform year there, so a small timing leak cannot be ruled out.
- **For Wisconsin 2027–2031** every trait predates the window (2020 census, ACS 2018–2022), so the full-trait models are usable there.

Flags and open items:
- **Wisconsin, Madison:** the place-pace trait (25.7 permits per 1,000 homes per year) is above every training city-window (top 16.8). Madison is building faster than any training city. Trees read it as the top value.
- **Kansas City, open:** forest and boosting predict about 29,000 homes vs 8,842 (2013–2015) and 3,650 (2006–2011). Most of the excess is on lots over 1 acre. Kansas City's permit file holds 61–72% of survey permits, which explains part of it, not 3–8×. Being traced.
- **Gradient boosting, Milwaukee:** still overshoots (12,880 near stops vs a recent 5,197 per 5 years), and the back-test shows the same. The identical Milwaukee totals across windows in round 2 no longer occur with the fixed place trait.
- **Item 63 is in:** Columbus and Kansas City census homes × weight = 540,432 (2010 homes 592,825).
- **Lot file vs city-wide survey** (`reference/tod_menu_pace_lotfile_vs_survey.csv`): flagged where the study area built more than the whole city. Milwaukee is 3.1× and 6.8× the uncorrected survey (the survey under-count, now fixed). Saint Paul 2010 is 50 vs 22, a single year of small numbers.

Kansas City trace:
- Lots over 1 acre hold 77% of the sample's acres, against 62% in Columbus and 51% in Milwaukee. They did build: 3,290 of 5,305 sample homes in 2013–2015.
- Kansas City is the lowest-density city in the sample, with the most land per home.
- The per-lot models learn homes per large lot from cities where large lots in the study areas built more. The place-pace trait does not pull Kansas City's total down enough.

So this is a weakness of the model form, not a data error: lot sums are not tied to the place's own pace. It is the same finding as pace rounds 1–4. The fix that matches it is to take the place total from the survey and use the lot model only to split it (two-part design).
