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

**Headline (audit wording; share menu clean, audit section 7):** B is about 500–1,200 extra homes over 2027–2031 (no-model benchmark 797). Single fits range from about 30 to 2,500. The tool's typical figure is 2,509. (The earlier "0 if homes only move" floor is withdrawn by the owner's rule of 2026-11-01: no evidence-free floors.)

No tool change.

## Baseline round 4: forest grid (rule logged before running)

Random forest, leave one city out. Scores are median |log|. Wisconsin is near-stop homes with no reform, 2027–2031, statewide.

| Leaf | Traits | Matched (29) | City median | 2011+ (12) | Later years (4) | Wisconsin |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 50 | all | 0.364 | 0.380 | **0.221** | 0.139 | 16,588 |
| 50 | no lot size | 0.362 | **0.315** | 0.234 | 0.157 | **18,255** |
| 50 | no "no rail or rapid" flag | **0.358** | 0.380 | 0.227 | 0.140 | 16,562 |
| 200 | all | 0.518 | 0.536 | 0.418 | 0.210 | 11,602 |
| 200 | no lot size | 0.478 | 0.391 | 0.373 | 0.223 | 14,444 |
| 200 | no flag | 0.518 | 0.536 | 0.418 | 0.210 | 11,602 |
| 500 | all | 0.609 | 0.706 | 0.443 | 0.329 | 9,499 |
| 500 | no lot size | 0.520 | 0.505 | 0.472 | 0.185 | 11,258 |
| 500 | no flag | 0.609 | 0.706 | 0.443 | 0.329 | 9,498 |

**Pick, by the logged rule:**
1. The three leaf-50 cells tie on matched rows (0.358–0.364, within 0.02).
2. They also tie on the 2011+ windows (0.221–0.234, within 0.02).
3. The tie goes to fewer traits: **leaf 50, no lot size**. Its Wisconsin cross-check is **18,255**, within 0.4% of the central 18,322, and it replaces the provisional 16,588.

Other findings:
- Dropping the "no rail or rapid" flag changes almost nothing (Wisconsin 16,562 vs 16,588). Its large fit importance did not carry over to prediction, and the Wisconsin lots have it at 0 anyway (both cities have rapid stops).
- Larger leaves are worse on every test.

**Share-model check without Kansas City** (gradient boosting, menu version): K 0.079 (main 0.077); Wisconsin B raw 11,019 (main 11,921); calibrated 874 (main 920). Kansas City does not drive the result.

## Which traits matter, judged on held-out cities

Each trait group is shuffled jointly within the left-out city's rows; the score is the registered held-out score. Script `scripts/run_tod_heldout_importance.py`; tables `reference/tod_heldout_importance_{pace,share}.csv`.

**No-reform baseline** (forest, leaf 50, no lot size). Unshuffled score: 0.362 (matched rows). A rise means the group helps.

| Trait group | Traits | Score rise when shuffled |
| --- | ---: | ---: |
| Rents, values, incomes | 20 | +0.075 |
| Housing stock (age, type, vacancy) | 21 | +0.062 |
| People (age, households, education, poverty) | 19 | +0.056 |
| Commuting and cars | 18 | +0.034 |
| Place's past permit pace and size | 2 | +0.019 |
| Distance to rail or rapid stop | 1 | +0.006 |
| Density and tract size | 3 | +0.001 |
| City has no rail or rapid stop | 1 | 0.000 |
| Existing homes on the lot (2010 census) | 1 | −0.028 (shuffling helps) |

**TOD prediction** (gradient boosting, calibrated with K left out). Unshuffled score: 0.403; uplift-change correlation 0.25.

| Trait group | Score rise when shuffled |
| --- | ---: |
| Existing homes on the lot | +0.014 |
| People | +0.011 |
| Everything else | between −0.013 and +0.001 |
| Lot size and shape | −0.029 |
| Zoning level and change | −0.061 (shuffling helps; correlation rises to 0.33) |

Reading:
- **Without reform,** a place's market (rents, values, incomes), its housing stock and its people predict building in cities the model never saw. Within-city fit importance had pointed elsewhere: the no-rail flag (a city label) and existing homes (dated after many windows). Neither carries over.
- **With the reform,** no trait group helps the share model predict the size of the change in a new city. The zoning-change traits make it worse. This agrees with the menu: no method beats the no-model benchmark.

### Causal forest built from scikit-learn only (method 9, 2026-11-01)

The same double-machine-learning design as EconML, built from scikit-learn (BSD licence), so it passes the licence check:
1. Cross-fitted outcome and upzoning models (gradient boosting, 3 folds).
2. A random forest on the residual ratio, weighted by the squared treatment residual (R-learner).

Run once, reported as is (owner: "just run it and see what it says"):

| | Value |
| --- | ---: |
| Calibrated score, K left out | 0.429 (benchmark 0.345) |
| Raw score | 0.348 |
| Uplift vs actual-change correlation | −0.15 |
| K, all 9 cities (range by left-out city) | 0.146 (0.008–0.295) |
| Wisconsin B raw | 12,925 |
| Wisconsin B calibrated (range) | 1,882 (107–3,811) |

It does not beat the no-model benchmark. Its predicted uplift does not line up with the cities' actual change in share: it is highest in Saint Paul and Charlotte, and its correlation with the actual change is −0.15. Its Wisconsin figure is the highest of the calibrated methods. Its largest uplift is in Saint Paul, where upzoned lots already held 100% of new homes before the reform, so a rise was impossible. Audit (section 10): no error; a standard R-learner. Kept as a named comparison only, not a line.

### Causal forest from scikit-learn, with honesty (method 10, 2026-11-01)

The same as method 9, plus honesty. Half the lots grow the trees. The other half re-estimate each leaf's effect by solving the local R-learner equation: effect = Σ w·(t−e)·(y−m) ÷ Σ w·(t−e)². This is how GRF/EconML estimate leaves. The splitting rule still differs from EconML's.

| | Method 10 (honest) | Method 9 | EconML | No-model benchmark |
| --- | ---: | ---: | ---: | ---: |
| Calibrated score, K left out | 0.516 | 0.429 | 0.335 | 0.345 |
| Raw score | 0.313 | 0.348 | 1.092 | — |
| Uplift vs actual change (correlation) | −0.32 | −0.15 | 0.57 | — |
| Wisconsin B calibrated (range) | 1,708 (98–3,410) | 1,882 | 700 | 797 |
| Wisconsin B raw | 12,150 | 12,925 | 14,549 | — |

Per city, the honest forest's predicted rise in share vs the actual change:
- **Five cities where the share had room to rise and something was built** track closely: Charlotte 0.25 vs 0.26, Chicago 0.11 vs 0.06, Madison 0.13 vs 0.07, New York 0.33 vs 0.34, Philadelphia 0.10 vs 0.12.
- **The misses are four cities where a rise was impossible or nothing was measured:**
  - Los Angeles and Saint Paul: upzoned lots already held 99–100% of new homes before the reform.
  - Bellevue: almost nothing was built.
  - Seattle: share before 0.43, with a small change.

These four pull the correlation negative and K down. Picking cities after seeing results would be cherry-picking. A rule such as "leave out cities where the share before is over 90% or no homes were built" would need to be logged before any rerun. This is for the audit.

### Post-hoc sensitivity: mean reversion (audit section 11; not the headline)

Ceiling cities are **not dropped**:
- Los Angeles and Saint Paul's shares fell from 99–100% to 72–79%. That is evidence (mean reversion on small before-counts), not an impossible rise.
- Dropping them after seeing results would be cherry-picking.
- Bellevue is left out of scoring only because 0 homes before and after (0/0) cannot be scored.

Instead, every city is kept and calibrated with: actual change = a + K × uplift + b × (share before − 0.5), fitted leaving the scored city out. This was logged after the results, so it is a sensitivity. The headline stays K-only scoring.

| Method | K-only (headline) | With mean reversion | K under reversion (range by left-out city) |
| --- | ---: | ---: | --- |
| **Reversion only, no model (a + b × (share before − 0.5))** | — | **0.160** | — |
| Gradient boosting | 0.403 | 0.138 | −0.07 to 0.52 |
| Random forest | 0.579 | 0.148 | −0.16 to 0.23 |
| Multilevel (dropped) | 0.425 | 0.150 | −0.05 to 0.30 |
| Regression tree | 0.505 | 0.166 | −0.07 to 0.21 |
| Causal forest, scikit-learn (method 9) | 0.429 | 0.167 | 0.34 to 0.58 |
| Nearest neighbours | 0.553 | 0.183 | −0.10 to 0.70 |
| Causal forest, honest (method 10) | 0.516 | 0.220 | −0.16 to 0.82 |
| EconML causal forest | 0.335 | 0.264 | −0.68 to 0.05 |
| Plain average | 0.432 | 0.271 | 0.01 to 0.62 |
| Linear regression | 0.527 | 0.284 | −0.11 to 0.35 |
| LASSO | 0.494 | 0.296 | −0.12 to 0.29 |

Note on the fitted form: an intercept is included here. The audit's version without one gives other numbers (for example, boosting 0.311 and LASSO 0.272); without an intercept, reversion alone scores 0.248 and boosting 0.205.

Reading:
- Mean reversion plus the average rise explains most of the change. A no-model reversion rule (0.160) is about as good as the best models (0.138–0.150), and K swings around 0.
- The lot models add little beyond that, which supports a line built on the benchmarks.
- **Wisconsin under the reversion rule:** fitted on all 9 cities, a = −0.038 and b = −0.398. Milwaukee's and Madison's share before on law-on lots is about 25% (2019–2024 actual), which gives a predicted rise of 0.06. That is 300 + 730 homes, about **1,180** statewide over 2027–2031. The average-change benchmark gives 797.
  - **Where the share before comes from:** the actual 2019–2024 homes on Wisconsin law-on lots (variant a) as a share of all homes in each city's lot table (`wi_lots.parquet`). This uses each city's own figure: Milwaukee 0.245 (predicted rise 0.063 × table total 4,739 = 300 homes) and Madison 0.261 (rise 0.057 × 12,839 = 730). Then ×1.147 to the state, giving 1,181. Using 0.25 for both, as the audit did, gives 0.0615 × 17,578 × 1.147 ≈ 1,240; the difference is only the per-city shares.
  - **Range from the 9 left-out fits:** 601 (without New York) to 1,662 (without Bellevue). The other fits: Charlotte 867, Saint Paul 1,077, Philadelphia 1,213, Seattle 1,195, Los Angeles 1,296, Madison 1,299, Chicago 1,429.

**Two views on the line (owner's call):**
- **Audit lean:** central about 1,200 (reversion rule: best held-out score, 0.160 vs 0.345; keeps every city; range 601–1,662), with 797 shown beside it as the pre-registered figure, labelled.
- **Mine:** about 800 as the line, because it was pre-registered, with about 1,200 as its upper sensitivity, because the reversion rule was found after seeing results.
