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

### Baseline decision (provisional; owner 23:27: "follow the auditor's recommendations for now")

- Round 3 is clean (audit; no coding error).
- **Central no-reform baseline near stops, 2027–2031: 18,322.** This is the survey pace re-based on new-home shares, the same rule as parking's central; it nests inside 122,619.
- **Cross-check (provisional, lot-size fix pending):** random forest with all traits gives 16,588, so the lot model agrees within 10%. Madison's place pace (25.7) is above every training window (top 16.8), so trees likely under-predict Madison.
- **Side line, "recent strength continues"** (parking's factor ×1.07–1.26): 19,605–23,086.
- Not candidates: gradient boosting, and the versions without dated traits.
- Kansas City is not a blocker. The share runs add one check with Kansas City left out of training.

### Which traits matter most for development with no reform (owner ask, 23:53)

Method: permutation importance of the baseline random forest. The forest is round 3, with all traits and the Milwaukee fix, fitted on 85% of lot-windows. Each trait is shuffled on a held-back 60,000 lot-windows, 5 times. The score is the rise in weighted squared error, as a percent of the unshuffled error. Script: `scripts/run_tod_pace_importance.py`. Table: `reference/tod_pace_importance.csv`.

| Rank | Trait | Error rise when shuffled | Plain meaning |
| ---: | --- | ---: | --- |
| 1 | City has no rail or rapid stop | 34% | In practice this marks Columbus and Kansas City, so it acts as a city label more than a lot trait |
| 2 | Distance to the nearest rail or rapid stop | 14% | A real lot trait |
| 3 | Upper-quartile rent in the tract | 11% | Market strength |
| 4 | Existing homes on the lot (2010 census) | 9% | How built-up the lot already is |
| 5+ | Tract land area, share of homes built before 1940, density, walking commute, … | under 0.5% each | Little weight |
| — | Place's past permit pace | 0.05% | Barely used |
| last | **Lot acres and lot width** | **−11% and −6%** | Shuffling them makes predictions better |

Reading: lot size is used in a way that hurts. The forest learns "big lot → big project" from a few large builds, and that does not carry over. This matches the Kansas City over-prediction, where most of the excess sits on lots over 1 acre. Candidate fix for a baseline round 4: predict homes per acre with a cap on acres, as the share model does, or leave out lot size. Not run yet; for the audit.

## TOD prediction (share model), all methods (2026-10-31/11-01)

Leave one of the 9 reform cities out. Scores are median |log(predicted ÷ actual)| of the upzoned lots' share of new homes after the reform.
- Raw: the model's own law-on share.
- Calibrated: share before + K × model uplift, where K is each method's own.
- Benchmark "same share as before": 0.69.

Wisconsin is the statewide net (bound B) for 2027–2031, variant a; bound A is 0. Tables: `reference/tod_menu_share_*.csv`.

| Method | Raw | Calibrated | K | Wisconsin B raw | Wisconsin B calibrated |
| --- | ---: | ---: | ---: | ---: | ---: |
| Plain average | 0.53 | 0.39 | 0.081 | 7,088 | 573 |
| Linear regression | 0.56 | 0.48 | 0.153 | 2,976 | 455 |
| LASSO | 0.64 | 0.44 | 0.147 | 3,483 | 511 |
| Regression tree | 0.75 | 0.48 | 0.181 | 3,806 | 689 |
| Random forest | 0.30 | 0.53 | 0.166 | 7,214 | 1,198 |
| Gradient boosting | 0.84 | 0.37 | 0.077 | 11,921 | 920 |
| Nearest neighbours | 0.25 | 0.53 | 0.147 | 3,399 | 499 |
| Multilevel | 0.32 | 0.36 | 0.264 | −3,105 | −819 |
| Causal forest (EconML) | 1.09 | 0.31 | 0.048 | 14,549 | 700 |

First read (before the audit):
- Calibrated, every method lands between about 450 and 1,200 extra homes statewide, except multilevel.
- Raw, the methods spread from about 3,000 to 14,500.
- Multilevel's negative Wisconsin figure is an outlier to trace: its law-on share in Wisconsin is below its law-off share.
- The causal forest has the best calibrated score after multilevel (0.31), but its raw shares are far off (Chicago 0.99 vs 0.10).
- Gradient boosting here is the menu version (rows thinned). Its K of 0.077 differs from Wisconsin net round 4 (0.110–0.120, no thinning).

### Share menu, re-scored with the audit's fixes (2026-11-01)

Script `scripts/run_tod_share_menu_score.py` → `reference/tod_menu_share_rescored.csv`. No refits.

What changed:
- K for each scored city is now computed leaving that city out. Before, it used all 9 cities, which leaked.
- A no-model benchmark is added: share before + the other cities' average change.
- The table now shows the correlation of each method's predicted uplift with the actual change.
- K's range by left-out city is shown.

Wisconsin calibrated B uses K from all 9 cities, since Wisconsin is never scored. Its range uses the left-out K's.

| Method | Calibrated (K left out) | Uplift vs actual change (correlation) | K, all 9 (range by left-out city) | Wisconsin B calibrated (range) |
| --- | ---: | ---: | --- | --- |
| **Benchmark: same share + others' average change (+0.040)** | **0.345** | — | — | **797** |
| Benchmark: same share as before | 0.686 | — | — | 0 |
| Causal forest | 0.335 | 0.57 | 0.048 (0.003–0.093) | 700 (40–1,357) |
| Gradient boosting | 0.403 | 0.25 | 0.077 (0.005–0.147) | 920 (55–1,758) |
| Multilevel | 0.425 | 0.33 | 0.264 | −819: **dropped** (see below) |
| Plain average | 0.432 | −0.22 | 0.081 (0.005–0.163) | 573 (33–1,154) |
| LASSO | 0.495 | 0.37 | 0.147 (0.010–0.310) | 511 (36–1,081) |
| Regression tree | 0.505 | −0.01 | 0.181 (0.012–0.412) | 689 (45–1,568) |
| Linear regression | 0.527 | 0.47 | 0.153 (0.011–0.316) | 455 (32–940) |
| Nearest neighbours | 0.553 | 0.14 | 0.147 (0.009–0.277) | 499 (30–943) |
| Random forest | 0.579 | −0.24 | 0.166 (0.009–0.350) | 1,198 (65–2,527) |

Findings:
- **No method beats the no-model benchmark.** The causal forest ties it (0.335 vs 0.345). The lot models get the direction right, not the size.
- **Raw scores track the level of the after-share, not the change.** The causal forest's raw law-on share is about 0.99 everywhere, which is broken, so only its calibrated version is usable.
- **K swings up to about 30× depending on which city is left out.**
- **Multilevel is dropped.** Its law-on and law-off models are separate linear fits that can cross. In Wisconsin it predicts 0 or fewer homes per acre on 77–78% of law-on lots, against under 1% for law-off on the same lots. Its law-on share therefore falls below its law-off share (Milwaukee 0.665 vs 0.725; Madison 0.454 vs 0.643).

**Wisconsin, extra homes from the law, 2027–2031:**
- If homes only move: 0.
- Pure addition: about 500–1,200 (methods, calibrated), with the no-model benchmark at about 800.
- The tool's typical figure is 2,509.

No tool change.
