# ADU no-reform model, round 1: results

Run 2026-10-31 under [NO_REFORM_R1_PLAN.md](NO_REFORM_R1_PLAN.md), committed before any result was computed. Code: [`scripts/run_adu_no_reform.py`](../../scripts/run_adu_no_reform.py). Outputs: `reference/adu_no_reform_r1b_*.csv` (adopted cleaning) and `adu_no_reform_r1_*.csv` (first run).

**Units.**
- A **rate** is ADU permits per 1,000 single-family homes per year.
- The **score** is the median of |log((predicted + 0.05) ÷ (actual + 0.05))|. 0.10 is about 10% off. Lower is better.
- **Bias** is the mean of log(predicted ÷ actual). Below 0 means the model predicts too low.
- **Wisconsin totals** are ADU permits over 2027–2031.

## Answer

- **The tool's no-reform baseline (530 permits) holds up as the main case.** No model beat "same pace as before" by the plan's rule.
- **It probably runs a little low.** With no statewide law, the comparison places' ADU permits kept rising. "Same pace" predicted 29% too low on average (bias −0.35).
- **Adding the other places' trend (N1) fit better:** score 0.28 against 0.51. Its resampling range overlaps "same pace" (0.21–0.42 against 0.24–0.59), so it does not pass the pre-set bar.
- **With that trend, Wisconsin's baseline would be about 758 permits** instead of 530 (+228). The tool already shows a similar case among its sensitivities: "Wisconsin's baseline rises like no-law places", with a baseline of 950.
- **A statewide pooled level does not work for ADUs.** It predicts held-out places with a score of 0.67, and it would give Wisconsin 4,390 permits. The comparison places are active ADU cities, far above typical Wisconsin places (Wisconsin's statewide current rate is about 0.06). So ADU's baseline has to be built place by place, unlike a statewide total.

## 1. Scores

Forward test: fit on years up to Y; predict the average over Y+1 to Y+5. 34 cases from 8 series (cleaned).

| Model | Score | 5th–95th percentile (1,000 resamples) | Bias |
| --- | ---: | --- | ---: |
| B0 same pace as before (last 3 years) | 0.507 | 0.24–0.59 | −0.35 |
| B1 long pace (all past years) | 0.716 | 0.50–0.89 | −0.63 |
| **N1 same pace plus trend** | **0.281** | 0.21–0.42 | +0.01 |
| N2 pooled level (no own history) | 0.475 | 0.13–1.85 | −0.50 |

Held-out places (each place's last-3-year rate from the others' median): N2 scores 0.667.

## 2. Wisconsin, 2027–2031, no statewide law

| Model | Permits | How |
| --- | ---: | --- |
| **B0 same pace (the tool today)** | **530** | Measured and assigned current rates by place |
| N1 same pace plus trend | 758 | Growth of 7.3% a year, from places with no reform in their latest years |
| N2 pooled level, statewide | 4,390 | Median no-law rate 0.477 × 1,839,569 homes × 5 years ÷ 1,000 |

## 3. Fit and fix (change made after the first run)

- **First run:** the worst miss was Madison, from 2020: same pace predicted 0.02, actual 0.15. Madison's own ADU reform came in 2021, inside the forecast window. That is a reform, not a no-reform year.
- **Fix:** no training or test window may span a city's own reform. This follows the plan's rule (train on years before each reform), but was added after the result was seen. It is logged in the plan.
- **Effect:** the trend fell from 20.9% to 7.3% a year, and N1's Wisconsin total from 1,422 to 758. Without the fix, a reform's jump is read as a no-reform trend.

**Worst misses after the fix, traced.**
- **Seattle from 2018 and 2019:** same pace 1.4, actual 3.0–3.4. Seattle's 2019 ordinance (two ADUs per lot, no owner-occupancy or parking rules) is a reform. Our trait marks Seattle as "reformed" in every year, so it missed this second step.
- **Portland from 2014:** same pace 0.88, actual 2.54. A development-charge waiver ran out in 2018, and builders rushed before it ended. That is a fee policy.

So the biggest no-reform misses are reforms our coding did not mark. A finer reform trait (each ordinance, not just "reformed or not") is the next round's fix.

## 4. Data left out (Ryan asked to see it)

- **Vermont:** ADUs have been allowed by right since 2004, so there are no no-law years.
- **Oregon's 32-city panel, Utah, Massachusetts and Maine:** their counts start in or after the law year.
- **California before 2017:** only period rates, not yearly counts.
- **New Hampshire:** counts all conversions, not ADUs.
- **Phoenix, Tucson, Colorado Springs:** one or two years each, from news reports.
- **Wisconsin places other than Madison:** only 2022–2025, too short for the forward test. They stay measured in the baseline.
- **Traits not every place has** (local rules coding, parcel data) are not used.
- **A "same pace" benchmark from the Census permit survey** is not possible for ADUs: the survey does not count them separately. Each place's own ADU pace stands in for it.

## 5. Next round

1. Code each local ordinance as its own dated reform (Seattle 2019, Portland's fee waiver and its end, Austin 2015, Minneapolis 2014 and 2021), then retest.
2. Rerun the forward test with year-matched homes.
3. Check Wisconsin's assumed current rates (74% of the central addition) against the 2022–2025 permits now in hand for other Wisconsin places.
