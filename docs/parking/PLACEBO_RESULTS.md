# Parking placebo test: results

Written 2026-10-27 by the parking conductor. Plan: [PLACEBO_PLAN.md](PLACEBO_PLAN.md), with one computing-time change made before running. Script: `scripts/run_parking_placebo.py`. Outputs: `reference/parking_placebo_places.csv` and `reference/parking_placebo_summary.csv`.

## Answer

**The real repeal places did worse than almost any set of places that never repealed.**
- **The comparison:** 500 placebo sets were built from places that never removed their minimums. Each set was given the real places' repeal years and run through the same calculation. Only 3.2% of the sets came out at or below the real average of −1.10 permits per 1,000 existing homes per year.
- **No sign of a positive effect:** if anything, a repeal is followed by slightly fewer permits than in a typical place.
- **The scenario's caution is justified:** the scenario's choice not to model a reduction (floor at zero) is the cautious side.

## Numbers

All rates are permits per 1,000 existing homes per year.

| Measure | Value |
| --- | ---: |
| Real average, 71 repeal places | −1.10 |
| Placebo averages: 5th / 50th / 95th percentile | −0.84 / +1.52 / +3.53 |
| Share of placebo averages at or below the real average | 3.2% |
| Real places with placebo matches (same state, half to twice the population, same years) | 64 of 71 |
| Placebo places computed | 909 |
| Spread of single places' effects (weighted standard deviation): real / placebo | 6.4 / 8.1 |

## What it shows

1. **The method does not centre on zero for random places.** Places that never repealed come out at +1.52 on average against their own comparison places. A likely reason is that the comparison pools are spread differently from the placebo places. Whatever the cause, it means the comparison leans slightly *toward* finding growth. So the real places' −1.10 is, if anything, more negative than it looks.
2. **Single places are as noisy without a repeal as with one.** The spread of single placebo places (8.1) is at least as large as that of the real places (6.4). The place-to-place differences in the real sample look like ordinary noise, which fits the earlier rounds finding no variable that explains them.
3. **A placebo-based range.** Taking the spread of the placebo averages and centring it on the real average gives −3.47 to +0.91. That is narrower at the top than the current range from resampling the real places (−3.50 to +1.54). In Wisconsin terms, +0.91 would be about 12,184 extra permits over 2027–2031, against the current 20,672.

## Decision for Ryan

| Option | High end, 2027–2031 |
| --- | ---: |
| **A (recommended): keep the current high end; show the placebo test as supporting evidence and as a sensitivity case** | 20,672 |
| B: use the placebo-based high end | about 12,184 |

Option A keeps the headline from a method chosen before this test was run. It shows the placebo result openly as a reason to read the high end as generous.
