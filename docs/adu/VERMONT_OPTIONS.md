# ADU model: three Vermont options

Run 2026-10-28. Code: `scripts/run_adu_vermont_options.py`. Table: `reference/adu_vermont_options.csv`.
The adopted outputs (`reference/adu_model_*.csv`, `reference/pooled_revision_*.csv`) are unchanged.

## Why this exists

- Vermont is predicted 40% too high.
- Its held-out log error is 0.34.
- Vermont counts homes by year built.
- Every other state counts permits.
- Its 2024 count uses a new source.

## The options

- **A:** as adopted (AQ-061).
- **B:** drop Vermont 2024 only.
- **C:** drop Vermont from everything.
  - Out of the within-state stage.
  - Out of the common level.
  - Out of the lower and upper spread.
  - Out of the reference-line median.

All three use adopted coverage and Washington coding.

## Units

- **Permits:** additional ADU permits in Wisconsin, 2027–2031 total.
- **Rate / level:** permits per 1,000 one-unit detached homes per year.
- **Typical level:** a typical place, law in force 4+ years.
- **Factor:** a multiplier on every place's central level.
- **Log error:** ln(predicted rate ÷ observed rate).
  - Positive means predicted too high.
  - 0.34 means 1.40 times too high.
- **RMS:** root of the mean squared log error, across states.
- **Held-out:** each state predicted with itself left out.
- **CA in / CA out:** California in or out of the common level.

## Results

| Measure | Unit | A: adopted | B: drop VT 2024 | C: drop VT |
| --- | --- | ---: | ---: | ---: |
| States in model | states, incl. California | 8 | 8 | 7 |
| Baseline | permits, 2027–2031 | 530 | 530 | 530 |
| Lower addition | permits, 2027–2031 | 6,735 | 6,590 | 6,659 |
| Central addition | permits, 2027–2031 | 10,788 | 10,360 | 11,133 |
| Upper addition | permits, 2027–2031 | 20,057 | 19,881 | 21,514 |
| Reference line | permits, 2027–2031 | 10,558 | 10,685 | 11,497 |
| Typical level | per 1,000 homes per year | 1.217 | 1.132 | 1.215 |
| Lower factor | × central level | 0.636 | 0.648 | 0.610 |
| Upper factor | × central level | 1.832 | 1.889 | 1.904 |
| RMS, states left in | log error | 0.180 (7 states) | 0.223 (7 states) | 0.154 (6 states) |
| RMS, same 6 states | log error | **0.138** | **0.136** | 0.154 |
| California in wins? | yes / no | yes | yes | yes |

- Same 6 states: WA, OR, RI, MA, ME, UT.
- Central change vs A: B −428, C +346 permits.
- Upper change vs A: B −176, C +1,456 permits.
- Lower change vs A: B −145, C −75 permits.
- Reference line change vs A: B +128, C +939 permits.

### Held-out log error by state (CA in)

| State | A: adopted | B: drop VT 2024 | C: drop VT |
| --- | ---: | ---: | ---: |
| Washington | 0.032 | 0.032 | 0.093 |
| Oregon | 0.230 | 0.198 | **0.311** |
| Rhode Island | −0.114 | −0.113 | −0.061 |
| Massachusetts | 0.051 | 0.051 | 0.110 |
| Maine | −0.186 | −0.186 | −0.132 |
| Utah | −0.104 | −0.144 | −0.055 |
| Vermont | **0.336** | **0.487** | not in model |

Bold = worst miss in that option.

### California in or out (RMS log error)

| Option | CA in | CA out | Winner |
| --- | ---: | ---: | --- |
| A, 7 states | 0.180 | 0.198 | CA in |
| B, 7 states | 0.223 | 0.236 | CA in |
| C, 6 states | 0.154 | 0.179 | CA in |
| A, same 6 | 0.138 | 0.193 | CA in |
| B, same 6 | 0.136 | 0.204 | CA in |

### Reference line by year

Median rate across states, per 1,000 homes per year.

| Option | 2027 | 2028 | 2029 | 2030 | 2031 | States per year |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| A | 0.982 | 1.129 | 1.043 | 1.437 | 1.437 | 7, 4, 4, 4, 1 |
| B | 0.982 | 1.129 | 1.043 | 1.472 | 1.472 | 7, 4, 4, 3, 1 |
| C | 1.052 | 1.327 | 1.216 | 1.472 | 1.472 | 6, 3, 3, 3, 1 |

- 2031 carries 2030 forward (California only).
- C keeps 7 states overall.
- So the 4-case median rule holds.
- But 2028–2030 rest on 3 states.

## What the numbers say

- **Dropping Vermont 2024 makes Vermont worse.**
  - 2024 was Vermont's high year (1.40).
  - Without it, Vermont averages 0.73, not 0.90.
  - Its miss grows from 0.34 to 0.49.
  - Central falls 428 permits.
- **Dropping Vermont only looks better.**
  - RMS falls 0.180 → 0.154.
  - That is only because Vermont is gone.
  - On the same 6 states it rises 0.138 → 0.154.
  - So Vermont helps predict the others.
- **Dropping Vermont widens the range.**
  - Upper rises 1,456 permits.
  - Lower falls 75 permits.
  - Reference line rises 939 permits.
- **California stays in under every option.**

## Light checks

- **Reproduction.** Option A matches the adopted run.
  - Central 10,787.6 vs 10,787.6 permits.
  - Lower 6,734.6 vs 6,734.3 permits (ramp rounding).
  - Upper 20,057.4 vs 20,057.4 permits.
  - Reference line 10,557.9 vs 10,557.9 permits.
  - RMS 0.1803 vs 0.1803 (`pooled_revision_g3f2.csv`).
- **Option B** matches the existing sensitivity row.
  - 6,589.9 / 10,359.6 / 19,881.5 permits.
  - `adu_model_sensitivities.csv`, "Vermont 2024 dropped".
- **Flags.**
  - C's reference line: 3 states in 2028–2030.
  - B: Vermont's own miss gets worse.
  - B's reference line was not refitted before; now it is (+128 permits).
- **Worst miss, option A: Vermont.**
  - Observed 0.898 per 1,000 homes per year (2021–2024).
  - Predicted 1.257 per 1,000 homes per year.
  - 1.40 times too high.
  - Chittenden County only, 38,653 homes.
  - 2021–2023 run 0.64–0.79; 2024 is 1.40.
  - Year-built counting lags permits.
  - That may make early law years look low.
- **Worst miss, option C: Oregon.**
  - Observed 0.857; predicted 1.169 per 1,000 homes per year.
  - 1.36 times too high (log error 0.31).
  - Without low Vermont, others' level sits higher.

## Recommendation

- **Keep A, as adopted.**
- B drops only Vermont's highest year.
- B makes Vermont's miss worse.
- C hides the miss, doesn't fix it.
- C predicts the other six worse.
- Year-built lag may explain part of the miss.
- Disclose that lag beside the result.
- Show C as a named sensitivity.
  - Central 11,133; upper 21,514 permits.
- Don't adopt B.
