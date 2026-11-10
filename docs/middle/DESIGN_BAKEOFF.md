# Middle housing: which primary design can give an answer either way?

Run 2026-11-09 after Ryan asked for a primary test whose result is actionable whether it shows a rise or no rise ("just noisy is a useless test"). Research only. Same no-peeking limits as the power check: Census place permits 2012–2018 only, and never a law state or candidate city as a fake case. Code: [`scripts/middle_design_bakeoff.py`](../../scripts/middle_design_bakeoff.py); output: `reference/middle_design_bakeoff.csv`.

- **Unit:** homes permitted per 1,000 single-family homes per year.
- **"Bar":** the smallest effect detected with 80% power at the 90% level, from the spread of each design's statistic across fake law states.
- **Proposed decision threshold (for Ryan):** 1 per 1,000 per year, about 1,800 Wisconsin homes a year. An interval narrower than the threshold lets the result either clear it or rule it out.

## Results (Census fill-ins included; reported-only is in the CSV)

| Design | States pooled | Homes in 1–4 unit buildings | Homes in 2–4 unit buildings | All homes |
| --- | ---: | ---: | ---: | ---: |
| A. Law states vs places in the same Census region | 2 | 4.11 | **0.75** | 8.61 |
| A. Law states vs places in the same Census region | 4 | 2.67 | **0.43** | 5.42 |
| B. Within one state: cities of 10,000+ vs 2,500–9,999 | 1 | 7.93 | 1.25 | 21.98 |
| B. Within one state, pooled | 2 | 5.53 | 0.86 | 14.51 |
| B. Within one state, pooled | 4 | 3.66 | 0.60 | 10.14 |

## Reading

- **Only homes in 2–4 unit buildings get under a bar of 1 per 1,000**, in design A with 2 or 4 states.
- **Homes in 1–4 unit buildings never do.** The best is 2.67, with 4 states. Single-family house building swings too much from year to year.
- **The within-state design (B) is noisier, not quieter.** It also leans: across fake states, big cities' 1–4 unit rates changed by 1.31 per 1,000 less than small cities' (2012–2018). So the size line itself carries a trend.
- **Trade-off:** 2–4 unit homes answer "did the law produce more small multiplexes?" precisely. They miss townhouses and split-lot homes, which Census files as 1-unit, and they say nothing about whether other building fell. Those questions need the noisier 1–4 or all-homes counts.
