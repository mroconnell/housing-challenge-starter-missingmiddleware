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
| A: keep the current high end; show the placebo test as supporting evidence and as a sensitivity case | 20,672 |
| **B (chosen): use the placebo-based high end** | about 12,184 |

I recommended A, because it keeps the headline from a method chosen before this test was run. **Ryan chose B on 2026-10-27** ("the data suggests B with a tighter ceiling"). The high end is now +0.91 permits per 1,000 existing homes per year, 12,184 permits over 2027–2031. The resampling high end (20,672) stays in the tool as a sensitivity case. The high end was first set to 12,184 (from the run below) and then to 12,947 after the full-pool rerun. The combined TOD + parking high case falls from 35,582 to 28,631 (headline, larger of the two near stops) and from 37,819 to 30,095 (sum, upper bound).

## Rerun with the full pool of cities (2026-10-27, owner request; used in the tool)

The first run drew 20 placebo cities per real place, so the 500 sets overlapped heavily. Ryan asked for a rerun drawing from every eligible city. Plan change logged in [PLACEBO_PLAN.md](PLACEBO_PLAN.md). Outputs: `reference/parking_placebo_full_places.csv` and `reference/parking_placebo_full_summary.csv`.

All rates are permits per 1,000 existing homes per year.

| Measure | First run (20 per place) | Full pool |
| --- | ---: | ---: |
| Placebo cities computed | 909 | 3,896 |
| Placebo averages: 5th / 50th / 95th percentile | −0.84 / +1.52 / +3.53 | −0.79 / +1.50 / +3.56 |
| Share of placebo averages at or below the real −1.10 | 3.2% | 2.0% |
| Spread of single places' effects: real / placebo | 6.4 / 8.1 | 6.4 / 9.0 |
| Placebo-based range, centred on the real average | −3.47 to +0.91 | −3.39 to +0.96 |
| Wisconsin high end, 2027–2031 | 12,184 | 12,947 |

**Reading:** the result holds. Using the full pool widens the high end slightly (+0.05). The real places now sit below 98% of placebo sets.

## Current run: 74 places, 20,000 sets (2026-10-28; used in the tool)

| Measure | Value |
| --- | ---: |
| Real average, 74 places | −1.14 |
| Placebo averages: 5th / 50th / 95th percentile | −0.83 / +1.52 / +3.61 |
| Share at or below the real average | 2.9% |
| Placebo cities computed | 4,004 |
| Placebo-based range | −3.48 to +0.95 |
| Wisconsin high end, 2027–2031 | 12,759 |

## Fixed run: at least 20 stand-ins per real place (2026-10-28, owner approved; used in the tool)

The Ask-why review ([ASK_WHY_REVIEW.md](ASK_WHY_REVIEW.md)) found that big real cities had only 1 to 4 stand-ins. San Jose had 2, averaging +5.5, and Raleigh had 1, at +3.6. Those few drove the placebo middle up to +1.5. Now each real place draws from its state, then its Census division, then the nation, until it has at least 20. Six stand-ins whose own comparison pools were empty are left out.

All rates are permits per 1,000 existing homes per year.

| Measure | Before the fix | Fixed |
| --- | ---: | ---: |
| Stand-in cities | 4,626 | 9,420 |
| Real places drawing beyond their state | 0 | 38 of 76 (27 from their division, 11 from the nation) |
| Placebo averages: 5th / 50th / 95th percentile | −0.79 / +1.51 / +3.59 | −2.28 / +0.01 / +2.64 |
| Share of placebo averages at or below the real −1.14 | 2.7% | 21.7% |
| Placebo-based range | −3.44 to +0.95 | −3.44 to +1.49 |
| Wisconsin high end, 2027–2031 | 12,695 | **19,937** |

**Reading:**
- **The lean toward growth is gone.** The placebo middle is now +0.01.
- **The real result is ordinary.** It is low but within the normal range, not "worse than 97%".
- **The high end goes up.** With more varied stand-ins, the spread is wider. It now agrees with resampling the real places (+1.43).
