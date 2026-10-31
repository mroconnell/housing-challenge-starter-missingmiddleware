# ADU improvement loop, round 1: plan written before running

Written 2026-10-31 by the ADU conductor, under Ryan's standing ask: improve the data and coding, rerun the simplest models, check for bad data, fix, and repeat. It also answers the ADU items of the audit's round 1 scorecard. No result for the variants below had been computed when this file was committed.

## What is tested

**The question.** How well does each model predict a statewide-law state it has never seen? This is the held-out test: each of the 7 non-California states is left out in turn, the model is refitted on the rest, and it predicts the left-out state's ADU permits per 1,000 single-family homes per year over its own law years.

**Score.** The log error for each state: log(predicted ÷ observed). 0.10 means about 10% too high. The summary is the root mean square over the 7 states (RMS). Lower is better.

**Models, simplest first.**

| Model | How it predicts the left-out state |
| --- | --- |
| M1 plain average | The equal-weight average of the other 7 states' observed post-law rates (California included). |
| M2 median | The median of the same 7 rates. |
| M3 adopted model | The two-stage model in the tool: a common level for all states, a phase-in by year since the law, and home value, income and size within each state. |

## Data and coding problems found before this plan

1. **Vermont counts homes by year built, not permit year** (audit item 1). A permit becomes a finished home about a year later. So each Vermont count sits about one year late against its law year.
2. **Maine's reporting share is a share of people, not homes** (0.73). Its town list is not published. The largest towns holding 73% of Maine's people hold 62% of its single-family homes.
3. **Rhode Island 2021–2022 are not corrected for missing towns.** No town list was found for those years. In 2023–2025, 6 or 7 of 39 towns did not report each year.

## Variants, each against the current data (V0)

| Variant | Change |
| --- | --- |
| V1 Vermont by permit year | Each Vermont count moves one year earlier (built in 2022 → permitted in 2021), so years since the law fall by one. The first year (built 2021) falls before the law and is dropped. |
| V2 Maine homes share | Maine's 2025 count is divided by 0.62 instead of 0.73. |
| V3 Rhode Island early years | Rhode Island 2021 and 2022 are divided by 0.8704, the homes share of the towns that reported in 2023 and 2024. |
| V4 all three | V1 + V2 + V3. |

## Reported for each variant

- M1, M2 and M3 held-out log errors by state, and the RMS;
- M3's Wisconsin results: lower, central, upper and the reference line (additional permits 2027–2031);
- flags: series whose outcome is not permits at issuance, partial years, reporting shares below 1, rates outside 0–10 permits per 1,000 homes per year, and the worst-predicted state, traced.

## How results are used

- **V1–V3 are data corrections.** Each is judged on whether the data are more correct, not on whether the score improves. The held-out score is reported, not used to pick.
- **The model choice (M1–M3)** is judged on the held-out RMS. A simpler model replaces M3 only if it wins clearly (RMS lower by more than 0.05) on V0 and V4 alike.
- **Ryan decides any change to the tool's numbers.** Until then the tool keeps 6,804 / 10,679 / 19,535.
- **The next round** starts from what this round's flags and worst miss show.

## Changes after writing

None yet.
