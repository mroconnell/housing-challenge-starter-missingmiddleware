# ADU improvement loop, round 1: results

Run 2026-10-31 under [IMPROVE_R1_PLAN.md](IMPROVE_R1_PLAN.md), which was committed before any result was computed. Code: [`scripts/run_adu_improve.py`](../../scripts/run_adu_improve.py) and [`scripts/run_adu_completion_lag.py`](../../scripts/run_adu_completion_lag.py). Outputs: `reference/adu_improve_r1_scores.csv`, `adu_improve_r1_by_state.csv`, `adu_improve_r1_flags.csv`, `adu_completion_lag.csv`.

**Units.**
- A **rate** is ADU permits ÷ thousands of single-family homes ÷ years: "permits per 1,000 homes per year".
- A **log error** is log(predicted rate ÷ observed rate) for a state the model never saw. +0.10 means about 10% too high.
- **RMS** is the root mean square of the 7 states' log errors. Lower is better.
- **Additional permits** are Wisconsin with-law permits minus current law, summed over 2027–2031.

## Answer

- **The adopted model predicts unseen states best.** On the current data its RMS is 0.168. The plain average scores 0.319 and the median 0.230. So the simpler models do not replace it.
- **One data fix helps a lot: Vermont by permit year (V1).** Vermont counts ADUs when they are built. Moving each count one year earlier, to its likely permit year, cuts Vermont's miss from +0.33 to +0.19 and the RMS from 0.168 to 0.135. A measured lag supports the one-year shift (section 3).
- **V1 would raise the central from 10,679 to 10,834 additional permits** (+155). The lower goes 6,804 → 6,790 and the upper 19,535 → 19,519. The reference line goes 10,374 → 10,849. **Ryan decides** whether to adopt it.
- **Maine's homes share (V2) is not adopted.** 0.62 is an estimate, not a town list. It makes Maine's miss worse (−0.15 → −0.32). It stays a sensitivity until Maine's town list arrives.
- **Rhode Island 2021–2022 (V3) barely matters.** It moves the central by +19 and the RMS by +0.001. It is not adopted, as there is no town list for those years.

## 1. Held-out test: every model, every variant

RMS of the 7 states' log errors (lower is better), and the adopted model's Wisconsin results.

| Variant | Plain average | Median | Adopted model | Worst state (adopted) | Lower | Central | Upper | Reference line |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| V0 current data | 0.319 | 0.230 | **0.168** | Vermont +0.33 | 6,804 | 10,679 | 19,535 | 10,374 |
| V1 Vermont by permit year | 0.309 | 0.216 | **0.135** | Oregon +0.24 | 6,790 | 10,834 | 19,519 | 10,849 |
| V2 Maine homes share 0.62 | 0.338 | 0.257 | 0.207 | Vermont +0.35 | 6,804 | 10,907 | 20,313 | 10,374 |
| V3 Rhode Island 2021–22 at 0.8704 | 0.319 | 0.230 | 0.170 | Vermont +0.33 | 6,893 | 10,699 | 19,458 | 10,374 |
| V4 all three | 0.327 | 0.244 | 0.179 | Maine −0.29 | 6,878 | 11,083 | 20,180 | 10,849 |

## 2. Held-out log error by state (adopted model)

| State | Observed rate | V0 current | V1 Vermont by permit year |
| --- | ---: | ---: | ---: |
| Washington | 0.77 | +0.07 | +0.10 |
| Oregon | 0.87 | +0.20 | +0.24 |
| Rhode Island | 1.13 | −0.12 | −0.09 |
| Massachusetts | 1.01 | +0.02 | +0.05 |
| Maine | 1.24 | −0.15 | −0.13 |
| Utah | 1.29 | −0.07 | −0.04 |
| Vermont | 0.90 | +0.33 | +0.19 |

Observed rate: permits per 1,000 homes per year over each state's law years in the current data. Under V0, 5 of 7 states come within about 15%.

## 3. How long an ADU takes from permit to completion

Measured from Austin's secondary-apartment permits issued since 2012 (3,104 permits; 2,950 completed). Austin is the only comparison city whose public permit file gives both dates.

| Measure | Value |
| --- | ---: |
| Median time from permit to completion | 0.97 years |
| Middle half of permits | 0.71–1.33 years |
| Completed in the same calendar year as the permit | 16% |
| Completed in the next calendar year | 63% |
| Completed two or more years later | 20% |
| Permits issued 2012–2021 that were completed | 97% |

So most ADUs are finished the calendar year after their permit, and almost all permits become homes. Counting Vermont's homes one year earlier is the best single-year match. This check was added after the V1 result was seen (see the plan's "Changes after writing").

## 4. Data checks (flags; nothing was stopped)

- **Outcome or year basis differs.**
  - Vermont: year built (V1 addresses this).
  - Utah: report years end in July, and counts are self-reported internal ADUs.
  - Washington: estimate years run April to March.
  These are coded in years since the law, so the year basis is handled. The outcome difference remains for Utah.
- **Reporting shares below 1:** Maine 0.73 (a share of people; no town list), Massachusetts 0.809, Rhode Island 0.81–0.87, Utah 0.80. All but Maine are homes shares from town lists.
- **Partial year:** Massachusetts 2025 counts as 11 of 12 months.
- **Rates above 10 permits per 1,000 homes per year:** 75 California city-years, the highest 26.2. These are real high-adoption cities; California's statewide rate is 2.4 to 3.6. Nothing outside 0–10 in the other states.
- **Worst miss traced.** Vermont was worst (+0.33); its year-built counts explain most of it (V1). With V1, Oregon is worst (+0.24). That is round 2's first trace.

## 5. Next round

1. **Trace Oregon.** Its early law years (2019–2022) may be weaker than the benchmark. Cities could keep owner-occupancy and parking rules until 2021 or later. Check the law's text and the city panel's coverage.
2. **Maine's town list.** Asked of the Maine Office of Community Affairs. It would replace the 0.73 population share.
3. **Wisconsin's current-law rates.** 73.6% of the central addition sits in places whose current rate is assumed. More Wisconsin city permit files would cut that. This moves where permits land more than the total.
