# Baseline range, round 4: results (a *post hoc* round)

Written 2026-11-05 by the baseline thread.
- **Plan:** [BASELINE_RANGE_R4_PLAN.md](BASELINE_RANGE_R4_PLAN.md) (lock e3abe92b; script cb94f102; run 20:47:02 UTC).
- **Outputs:** `reference/baseline_range_r4_{checks,summary,wisconsin}.csv`.

**Status: for the audit and Ryan. The tool is not changed.**

**This round is post hoc.** Its methods were designed after round 3, and it is scored on checks already seen, so the winner's coverage is optimistic. No clean hold-out remains.

## Answer

1. **The LASSO could not be tuned down to 90%.** The recalibrated version (E2) still held 98.8% of checks (bootstrap 98.0–100%).
   - Capping its extreme widths did tame it: the mean width fell from 5.76 to 1.92.
   - But its typical (median) width, 1.56, is still wider than the all-states range's 1.44.
   - The likely reason is a guess. After the 2007–2011 crash, every state's swing trait is high, so the LASSO expects big misses everywhere. The post-2009 misses were smaller than that.
2. **None of the three ways to narrow the all-states range kept it at 90%.** Each was narrower, and each held less:

   | Variant | Held, other 50 states |
   | --- | ---: |
   | All states, round 4 version | 88.3% |
   | Drop extreme-swing states | 85.7% |
   | Weight recent years | 87.5% |
   | Around the higher central (L3) | 83.7% |
   | Both | 81.8% |

   For 2027–2031, the recent-years tuning chose "no decay", so it gives the same Wisconsin range as all states.
3. **By the locked rule, E2 wins.** It is the narrower of the two methods that reach 90%. Its Wisconsin 2027–2031 range is **74,119 to 207,450 homes**. Like E, that is narrower than any range it gave Wisconsin in 2009–2020: a log width of 1.03, against a mean Wisconsin check width of 1.97.

## Scores, check years 2009–2020

Coverage is the share of held-out target checks inside the range. Width is log(high ÷ low).

| Method | Other 50 | 90% bootstrap | Mean width | Median width | Wisconsin | Challenge states (120 checks) | Other 50, 2005–2020 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| A all states (round 4 quantiles) | 88.3% | 76.8–98.3% | 1.38 | 1.44 | 12 of 12 | 87.5% | 66.8% |
| A all states (round 3, for comparison) | 88.7% | 77.5–98.3% | 1.39 | — | 12 of 12 | 87.5% | 67.0% |
| AT drop extreme-swing states | 85.7% | 71.0–96.5% | 1.34 | 1.39 | 12 of 12 | 85.8% | 64.8% |
| AR weight recent years | 87.5% | 72.5–97.5% | 1.36 | 1.43 | 12 of 12 | 88.3% | 66.1% |
| AL3 around L3 | 83.7% | 66.5–95.9% | 1.36 | 1.41 | 12 of 12 | 83.3% | 63.1% |
| ARL3 both | 81.8% | 63.0–94.7% | 1.33 | 1.39 | 11 of 12 | 80.8% | 61.8% |
| E LASSO (round 3) | 99.0% | 98.3–100% | 5.76 | 1.56 | 12 of 12 | 100% | 81.9% |
| **E2 LASSO recalibrated (pick)** | **98.8%** | 98.0–100% | 1.92 | 1.56 | 12 of 12 | 100% | 81.0% |

**Two notes on reading the table:**
- **Noise:** A's 88.3% is consistent with a true 90% rate, because its bootstrap range includes 90%. E and E2's overshoots are not, because their bootstrap ranges sit above 90%.
- **The two A rows:** round 4 uses a different quantile function, so the two versions differ slightly.

## Wisconsin 2027–2031 (homes permitted)

| Method | Central | Low | High |
| --- | ---: | ---: | ---: |
| A all states (round 4 quantiles) | 124,000 | 56,500 | 218,865 |
| A all states (round 3) | 124,000 | 53,853 | 227,980 |
| AT drop extreme-swing states | 124,000 | 56,486 | 211,604 |
| AR weight recent years (chose no decay) | 124,000 | 56,500 | 218,865 |
| AL3 around L3 | 132,458 | 58,576 | 226,303 |
| E LASSO (round 3) | 124,000 | 75,099 | 204,744 |
| **E2 LASSO recalibrated (pick)** | 124,000 | **74,119** | **207,450** |
| v3 now (80% range) | 124,000 | 65,250 | 177,672 |

These are scaled to v3 (×124,000 ÷ 118,148, or ÷ 118,148 × the L3 central). AT dropped 1 training state at 2025.

## What this means

There are two honest options. Neither is a clean 90% that is also tight:
- **All states:** 56,500 to 218,865. It held 88.3% in past checks, within noise of 90%, and Wisconsin 12 of 12. Its width has been steady.
- **The LASSO (E2):** 74,119 to 207,450. It held about 99% in past checks, which is too wide on average, and Wisconsin 12 of 12. It is narrower for Wisconsin today than it ever was in the checks.

Picking a range for the tool is Ryan's call. A central other than 124,000 also needs his own OK.
