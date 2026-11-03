# ADU causal framework: results (A3, A2, A4)

Run 2026-11-03 under [CAUSAL_FRAMEWORK_PLAN.md](CAUSAL_FRAMEWORK_PLAN.md), which was locked before any count. Nothing in the tool has changed. Ryan decides any tool change.

**Units.**
- Rates are ADU permits per 1,000 single-family homes per year.
- Wisconsin totals are extra ADU permits over 2027–2031.
- A ratio is the after rate divided by the before rate.

## Answer

- **A3. How far off the model was for a state it never saw: about 8,100 to 13,700 around the central of 10,492.** This covers only the law-side error. 74% of the central addition comes from Wisconsin's assigned current rates, and they are not in this range.
- **A2. California:** places already active under the 2017 law gained ×2.39 after the 2020 package (90% interval 2.01 to 3.49). Middle places gained ×7.16.
  - **The regression-to-the-mean check fails.** Places active in 2017 grew less than the rest from 2018 to 2019, with no new law in between.
  - So, by the locked rule, part of the gaps between groups is regression to the mean, not a different response to the law.
  - The sliding-scale check finds no slope once home value and size are controlled.
- **A4. Washington: feasible for activity groups, but no after-law years exist yet.**
  - OFM has ADU permits for all 289 incorporated cities, every year 2011–2023. Those cities hold about 58% of the state's single-family homes.
  - Washington cities cannot be no-law comparisons for A1. The state has required cities to allow ADUs since 1993 (RCW 43.63A.215), and SB 6617 (2020) barred ADU parking near transit from 2021-07-01.
- **A1 stays locked as not feasible.**

## A3. How far off the model was for a state it never saw

Code: [`scripts/run_adu_causal_a3.py`](../../scripts/run_adu_causal_a3.py). Outputs: `reference/adu_causal_a3_*.csv`. Adopted model (V6s rules, AQ-065 to AQ-067); each of the 7 non-California states is hidden in turn.

| State hidden | Actual rate | Predicted | Log error | Central if Wisconsin missed the same way |
| --- | ---: | ---: | ---: | ---: |
| WA | 0.770 | 0.928 | +0.187 | 8,705 |
| OR | 0.901 | 1.014 | +0.119 | 9,318 |
| RI | 1.126 | 1.031 | −0.088 | 11,456 |
| MA | 0.923 | 1.065 | +0.143 | 9,094 |
| ME | 1.244 | 1.094 | −0.129 | 11,936 |
| UT | 1.285 | 1.194 | −0.073 | 11,290 |
| VT | 0.984 | 1.172 | +0.174 | 8,813 |

| Range | Low | High |
| --- | ---: | ---: |
| Root mean square log error 0.136 × t (6 degrees of freedom, 90%) 1.943 | 8,055 | 13,666 |
| 1.645 × bootstrap 95th percentile of that error (0.157; 10,000 draws over states) | 8,098 | 13,594 |
| Each state's own miss, lowest to highest | 8,705 | 11,936 |

- The mean log error is +0.048: on average the model predicted about 5% too high for a hidden state.
- The range rests on 7 misses.

## A2. Within California

Code: [`scripts/run_adu_causal_a2.py`](../../scripts/run_adu_causal_a2.py). Outputs: `reference/adu_causal_a2_*.csv`.
- **Data.** The Gate 3 study panel: BuildinganADU for 2017, HCD APR Table A2 from 2018. 2025 is complete: 505 places filed Table A2 rows, against 504 in 2023.
- **Places.** Only places observed in all 6 years are kept, 428 in all.
- **Interval.** Bootstrap over places, 2,000 draws, seed 20261103.

| Group (rule v1, 2017–2019) | Places | Rate before 2017–19 | Rate after 2023–25 | Difference | Ratio | 90% interval | Leave-one-out range |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Not adopted (0 before) | 72 | 0.00 | 1.26 | +1.26 | none (0 before) | | |
| In between | 251 | 0.33 | 2.38 | +2.05 | 7.16 | 6.41–8.10 | 7.04–7.32 |
| Early adopter | 105 | 3.02 | 7.19 | +4.18 | 2.39 | 2.01–3.49 | 2.18–2.97 |
| All | 428 | 1.11 | 3.73 | +2.62 | 3.36 | 2.68–5.01 | 3.23–4.51 |

**Checks.**

| Check | Places | Slope | 90% interval | Reading |
| --- | ---: | ---: | --- | --- |
| Sliding scale: change (after minus before) on the 2017–19 rate, controlling for home value and size | 426 | +0.02 | −0.25 to +0.41 | No slope. Does not confirm the groups' rising differences. |
| Regression to the mean: 2019 rate minus statewide growth × 2018 rate, on the 2017 rate | 426 | −0.63 | −1.10 to −0.19 | **Fails**: the interval excludes 0. |

- Groups set on 2017 alone, growth from 2018 to 2019 relative to the state (statewide ×1.40):
  - not adopted: 1.31;
  - in between: 1.29;
  - early adopter: 0.92.
- BuildinganADU check for 2018–2019 (`_adu_comp1819` files): the same pattern.
  - Early adopters ×2.23 (1.81–3.55).
  - Sliding scale −0.05 (−0.30 to +0.28).
  - Regression to the mean −0.77 (−1.37 to −0.23).
- **Post hoc (not in the plan):** with no controls, the sliding-scale slope is +0.26. Home value is correlated with the 2017–19 rate (0.39), so the controls absorb the slope.

**Reading.**
- The places that started high rose less in proportion and more in permits.
- The no-new-law check shows that high starters fall back even without a law. So the early adopters' ×2.39 is not clean evidence of a smaller or larger law effect for them.
- This does not change why the central uses the restrictive-group ramp. Wisconsin's places start near 0.

## A4. Can rule v1 be applied outside California?

**Washington's ADU laws before 2023** (enacted text checked; [SB 6617 session law](https://lawfilesext.leg.wa.gov/biennium/2019-20/Htm/Bills/Session%20Laws/Senate/6617-S.SL.htm)):
- **SB 6617 (Chapter 217, Laws of 2020).**
  - Effective 2020-06-11; cities had to comply by 2021-07-01.
  - It bars off-street parking rules for ADUs within ¼ mile of a major transit stop. A city can keep them with evidence that street parking is infeasible.
  - Cities that changed their ADU rules in the 4 years before are exempt.
  - Nothing on owner occupancy.
- **RCW 43.63A.215 (1993, repealed 2023).** It already required cities to allow ADUs.
- **Consequence for A1:** Washington cities are not no-law comparisons for any year in 2017–2022.
- **Consequence for the pooled model:** none. It treats Washington's 2023 law (EHB 1337) as the treatment, and these earlier rules as background.

**Washington data.**
- OFM reports permitted ADUs for all 289 incorporated cities in every estimate year 2011–2023, totalling 234 to 1,564 a year. No city has a missing year.
- Incorporated cities hold about 1.2 million of Washington's 2,047,311 single-family detached homes (ACS 2020–2024), about 58%. Unincorporated areas are not in the city rows.
- So rule v1 groups can be built from Washington's own pre-law window.
- **A2 cannot be rerun there yet.** The law's first local-rule year is 2026, and OFM has at most one estimate year after it. A rerun needs 2027 and later.

**Other states** (unchanged from the plan):
- Oregon: only Portland has pre-law years.
- Massachusetts: a 2025 statewide count only.
- Maine: waits on the town list.

## A1

Still locked as not feasible. A4 added no clean comparison cities, because Washington cities had state ADU rules throughout.

## What could feed the tool (Ryan decides)

- **A3 range beside the central:** "how far off the model was for a state it never saw: 8,100 to 13,700", with the law-side-only caveat.
- **Nothing from A2 or A4.** No new lines and no spillover multiplier.
