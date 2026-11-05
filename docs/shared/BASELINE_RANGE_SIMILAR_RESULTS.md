# Baseline range, round 3: learned "similar states" — results

Written 2026-11-05 by the baseline thread.
- **Plan:** [BASELINE_RANGE_SIMILAR_PLAN.md](BASELINE_RANGE_SIMILAR_PLAN.md) (locked; Ryan's go 19:24 UTC).
- **Script:** `scripts/run_baseline_range_similar.py` (07f3f92c, committed before the run).
- **Outputs:**
  - `reference/baseline_range_similar_checks.csv`
  - `reference/baseline_range_similar_summary.csv`
  - `reference/baseline_range_similar_wisconsin.csv`

**Status: for the audit and Ryan. The tool is not changed.**

## Answer

1. **By the locked rule, E wins, but on average it is by far the widest method (audit).** E is the LASSO miss-size range.
   - **Coverage:** it was the only method to reach 90% on the held-out states, at 99.0% over 2009–2020 (bootstrap 98.3–100%). That overshoots the target, just as A falls short of it.
   - **Width:** its mean width over the other 50 states is 5.76 log units, against 1.29 to 1.39 for A to D. Its mean Wisconsin check width is 2.07, against A's 1.39.
   - **Checks:** it held Wisconsin 12 of 12 times, and 100% of 120 challenge-state checks.
   - **Wisconsin 2027–2031:** only here is it the narrowest, at **75,099 to 204,743 homes** (log width 1.00). That is **outside E's own record**: every range E gave Wisconsin in 2009–2020 was wider (1.32 to 3.99).
2. **A caveat on E: that narrow range is out of line with E's own record on Wisconsin.**
   - In the past checks, E's Wisconsin ranges had log widths from 1.32 to 3.99 (2009–2020).
   - For 2027–2031, it gives a log width of 1.00, narrower than any it gave Wisconsin before.
   - This happens because Wisconsin's traits now look calm to the LASSO. Recent permits sit above the 10-year pace (tilt +0.10), which the model links to smaller misses.
   - E also over-covers (99% against a 90% target), because it gives some states extremely wide ranges. Its 99th-percentile width is 64.7 log units. So it reaches the target by being wide where it is unsure, and narrow where it thinks a state is calm.
3. **The pooled all-states range (A, now calibrated) just missed:** 88.7% (bootstrap 77.5–98.3%), Wisconsin 12 of 12, 87.5% of 120 challenge-state checks. Its Wisconsin 2027–2031 range is 53,853 to 227,980. The miss is within noise: the 12 overlapping years hold only 2–3 independent periods.
4. **Hand-free similarity (C and D) did not help.**
   - **C, nearest states:** 82.7% held, Wisconsin 8 of 12.
   - **D, weighted states:** 83.2% held, Wisconsin 9 of 12.
   - Picking "similar" states made the ranges narrower, but they then missed more.
5. **Wisconsin's own history alone (B) is worst:** 76.0% held, Wisconsin 7 of 12.

## Scores, check years 2009–2020

Coverage is the share of held-out target checks inside the range. Width is the mean log(high ÷ low); 1.39 means the high end is about 4 times the low end.

| Method | Other 50 states | 90% bootstrap | Width | Wisconsin | Challenge states (10) | Other 50, 2005–2020 |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| A all states, calibrated | 88.7% | 77.5–98.3% | 1.39 | 12 of 12 | 87.5% | 67.0% |
| B own history | 76.0% | 55.2–91.2% | 1.35 | 7 of 12 | 74.2% | 58.0% |
| C nearest states | 82.7% | 66.0–96.5% | 1.29 | 8 of 12 | 86.7% | 62.8% |
| D weighted states | 83.2% | 67.3–95.8% | 1.30 | 9 of 12 | 85.0% | 63.4% |
| **E LASSO miss size (pick)** | **99.0%** | 98.3–100% | 5.76 | 12 of 12 | 100% | 81.9% |

**Reading the challenge-states column:** these 10 states were each held out as usual, and the column is reported only.

**Optimism:** the pick uses the same 50 × 12 checks that are reported, so the winner's figure is a little optimistic (plan, audit 3).

**Over 2005–2020,** no method reaches 90%. E is closest, at 81.9%, and it held Wisconsin 13 of 16 times.

## Wisconsin 2027–2031 (homes permitted, around 124,000)

| Method | Low | High |
| --- | ---: | ---: |
| A all states, calibrated | 53,853 | 227,980 |
| B own history | 50,538 | 189,077 |
| C nearest states | 55,651 | 180,305 |
| D weighted states | 51,989 | 203,736 |
| **E LASSO (pick)** | **75,099** | **204,743** |
| Round 2, all states 2.5th–97.5th (for comparison) | 48,709 | 244,147 |
| v3 now (80% range) | 65,250 | 177,672 |

These are scaled to v3 (×124,000 ÷ 118,148). E's range is symmetric on the log scale around 124,000.

## What the LASSO learned (2025 fit, reported only)

The coefficients, on standardised traits, are for the log of the miss size. A positive coefficient means bigger misses.

| Trait | Coefficient |
| --- | ---: |
| Swing | +0.39 |
| Pace | +0.20 |
| Tilt | −0.20 |
| Own past miss | −0.26 |
| Apartment share | −0.09 |
| Region | about 0 |

Two of these look odd:
- **Own past miss is negative.** A state that missed more before is predicted to miss less.
- **Tilt is negative.** A state with recent permits above its 10-year pace is predicted to miss less.

A guess for the first: the LASSO may be trading off two traits that move together. Swing and own past miss are correlated at 0.88 in the training rows. Neither coefficient should be read as a cause.

## Choices for Ryan

| Option | Range, 2027–2031 | Case for | Case against |
| --- | --- | --- | --- |
| E (the locked rule's pick) | 75,099 to 204,743 | Passed the rule; held Wisconsin 12 of 12 and 100% of 120 challenge-state checks | Narrower for Wisconsin than any range it gave Wisconsin before; rests on Wisconsin "looking calm" now |
| A (all states, calibrated) | 53,853 to 227,980 | Simple; consistent width; Wisconsin 12 of 12 | 88.7% against the 90% target (within noise, as E's 99.0% overshoot is) |
| Round 2 B | 48,709 to 244,147 | 92.5% since 2009 (post hoc window) | Widest |
