# ADU no-reform model, round 1: plan written before running

Written 2026-10-31 by the ADU conductor, under Ryan's ask of 2026-10-31: every scenario builds a "how much gets built with no reform" model and runs fast fit-and-fix rounds on it, judged as in the audit's no-reform judging plan. No result below had been computed when this file was committed.

## The question

With no statewide ADU law, how many ADU permits would Wisconsin issue in 2027–2031? The tool's answer today is **530 permits** (the current-law baseline). This round tests whether that holds up.

**Units.** A rate is ADU permits per 1,000 single-family homes per year. The Wisconsin total is permits over 2027–2031.

## Training data: places with no statewide ADU law

Owner's direction: use the years before each reform, and only data every place has. A city's own ADU reform is kept as a dated trait, not dropped.

| Series | Level | No-law years used | Local ADU reform (trait) |
| --- | --- | --- | --- |
| Washington cities and towns, excluding Seattle | state | 2011–2023 | not coded |
| Spokane, WA | city | 2011–2023 | not coded |
| Rhode Island | state | 2021–2023 | not coded |
| Honolulu, HI | city | 2016–2023 | not coded |
| Montgomery County, MD | county | 2019–2025 | not coded |
| Bozeman, MT | city | 2020–2023 | not coded |
| Austin, TX | city | 2005–2025 | from 2015 |
| Denver, CO | city | 2016–2023 | zone by zone (not citywide) |
| Minneapolis, MN | city | 2005–2025 | from 2014 |
| Seattle, WA | city | 2005–2023 | throughout |
| Portland, OR | city | 2005–2017 | throughout |
| Madison, WI | city | 2014–2025 | from 2021 |

**Left out, and why** (reported to Ryan):
- Vermont: ADUs allowed by right statewide since 2004, so it has no no-law years.
- Oregon's 32-city panel, Utah, Massachusetts and Maine: their counts start in or after the law year.
- California: before 2017 it has only period rates, not yearly counts.
- New Hampshire: its series counts all conversions, not ADUs.
- Phoenix, Tucson and Colorado Springs: one or two years each, from news reports.
- Other Wisconsin places with permit data: they have only 2022–2025, too short for the forward test. They remain in the Wisconsin baseline as measured.
- Traits that not every place has (local rules coding, parcel data): not used. The Census permit survey does not separate ADUs, so it cannot give an ADU "same pace" benchmark. Each series' own recent ADU pace stands in for it.

## Models, simplest first

| Model | How it predicts a series' rate in later years |
| --- | --- |
| B0 same pace as before | The series' average rate over its last 3 known years. This is how the tool's baseline works for measured places. |
| B1 long pace | The series' average over all its known years. |
| N1 same pace plus trend | B0 times the typical yearly growth of the other series, estimated from their own data up to the same year. |
| N2 pooled level | No own history: the median of the other series' last-3-year rates. This is the kind of rate used for places with no data. |

## Tests

1. **Forward (most weight).** For each series and each origin year Y from 2014 to 2020: fit on years up to Y; predict the average rate over Y+1 to Y+5; compare with the actual average over the years known (at least 3 of the 5).
2. **Held-out places.** Each series left out in turn: N2 predicts its last-3-year rate from the others.
3. **Score, fixed now:** median of |log((predicted + 0.05) ÷ (actual + 0.05))|. The 0.05 permits per 1,000 homes per year keeps places with zero permits from breaking the log.
4. **Spread:** the score's 5th–95th percentile over 1,000 resamples of the series.
5. **Placebo:** for N1, the predicted change over the window should match the actual change in no-law places; the earlier placebo test's no-law rise (ratio 1.52 per 4 years) is the check.
6. **Worst miss traced** before any change.

## Wisconsin

For each model, the Wisconsin 2027–2031 no-reform total, beside today's 530:
- B0 = 530 (the tool today);
- N1 = 530 times the trend over 2027–2031;
- N2 = the pooled no-law level × Wisconsin's 1,839,569 single-family homes × 5 years ÷ 1,000. This is a statewide level, not built place by place.

**Use.** A model replaces the tool's baseline only if it beats B0 clearly on the forward test (median score lower by more than 0.05) and outside the resampling spread. Ryan decides any change.

**Cross-scenario table.** The three Wisconsin no-reform totals (ADU, TOD, parking) go side by side in [POLICY_SCENARIO_COMPARISON.md](../POLICY_SCENARIO_COMPARISON.md). They should nest, not match.

## Changes after writing

None yet.
