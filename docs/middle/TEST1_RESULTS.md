# Test 1 results (primary): four law states against similar places elsewhere

Locked plan: [TEST_PLAN_LOCKED.md](TEST_PLAN_LOCKED.md). Code: [`scripts/middle_test1_states.py`](../../scripts/middle_test1_states.py), committed before the run (04eb535d). One bug fix was made after a crash that produced no output. Outputs:
- `reference/middle_test1_summary.csv`
- `reference/middle_test1_states.csv`
- `reference/middle_test1_fakestates.csv`
- `reference/middle_test1_bootstrap.csv`

Run 2026-11-09.

## Headline

**We do not know whether the four states' laws changed homes permitted in 2–4 unit buildings, relative to comparison places.**
- **Estimate:** +33% against comparison places (log ratio +0.28), about +0.23 per 1,000 single-family homes per year.
- **90% range:** −21% to +92%. In rate terms that is −0.07 to +0.65 per 1,000 per year. It includes 0.
- **Rank:** the four-state result sits at the 85th percentile of 10,000 sets of fake law states. A reading needs the 95th.
- **This is not "no effect".** The range still allows a fall of about a fifth, or nearly a doubling.

Required beside the headline (locked plan, audit fixes):
- **(a) Disclosure:** the measure (2–4 unit homes) and the four states were chosen after raw state trends in this measure had been seen for these states (October inventory; see the plan).
- **(b) Oregon + California alone:** +0.30 per 1,000 per year (−0.23 to +1.02); +32% (−53% to +163%); 77th percentile. **We do not know.** It reads the same as the four-state result.
- **(c) Comparison places' own change:** 2–4 unit homes in comparison places changed by −0.19 per 1,000 per year (four-state average), against +0.04 in the law states.
- **(d) Open backdoors:**
  - a housing shortage or other shock that starts in the same year as a law;
  - California's other 2022–2025 housing laws (the result is labelled "California's 2022 package");
  - local reforms in comparison places that are on no list;
  - state housing funding programs;
  - ADUs (mostly outside this measure).

## Main result by measure (reported-only Census data, four states)

| Measure | Estimate vs comparison | 90% range | Rate difference per 1,000 per year (range) | Percentile | Reading |
| --- | --- | --- | --- | ---: | --- |
| **M2: 2–4 unit homes (lead)** | **+33%** | **−21% to +92%** | **+0.23 (−0.07 to +0.65)** | 85 | **We do not know** |
| M1: 1–4 unit homes | +7% | −18% to +29% | +2.5 (+1.0 to +5.1) | 85 | We do not know |
| M3: all homes | +8% | −14% to +32% | +3.6 (+1.1 to +7.6) | 80 | We do not know |

- **The locked reading uses the log ratio.** For M1 and M3, the rate-difference range excludes 0, but the locked ratio reading does not. **Under the plan, M1 and M3 read "we do not know".** Their rate-difference ranges are not a finding and must not be quoted as one (audit, 2026-11-10).
- **Why the two units disagree there:** comparison places in the West build at about twice the law states' rate. Their 1–4 unit rate fell from 28 to 22 per 1,000 per year, so a difference in rates looks large even where the ratio is ordinary.
- **Per the plan, the ratio governs.** Both are shown.

## Each state, M2 (homes in 2–4 unit buildings per 1,000 single-family homes per year)

| State | Places | Law state before → after | Comparison before → after | Difference |
| --- | ---: | --- | --- | ---: |
| Oregon | 66 | 0.69 → 0.77 | 1.39 → 0.91 | +0.56 |
| California | 224 | 0.66 → 0.53 | 0.86 → 0.68 | +0.05 |
| Maine | 85 | 0.85 → 0.94 | 0.29 → 0.25 | +0.12 |
| Vermont | 75 | 0.63 → 0.76 | 0.29 → 0.24 | +0.17 |

- **Leave-one-state-out mean differences:** +0.11 to +0.28, all positive.
- **California's unmatched share:** 18% of single-family homes had no comparison place at ½–2× their size. Oregon, Maine and Vermont had none unmatched.

## Sensitivities (M2 unless stated; all read "we do not know")

| Version | Estimate | 90% range | Percentile |
| --- | --- | --- | ---: |
| Unmatched places matched nationally | +32% | −22% to +91% | 84.5 |
| Oregon before 2015–2018 | +32% | −23% to +89% | 83.7 |
| Census filled-in columns | −6% | −46% to +25% | 39 |
| M1, California without progress-report ADUs (a bound) | +1% | −23% to +22% | 69.7 |
| Second inference (bootstrap over places, M2; 1,000 draws, although the code's constant says 2,000, which the plan did not fix) | rate difference −0.13 to +0.45 | log −0.13 to +0.54 | — |

- **The filled-in version failed Test 4** (it showed a rise in fake years). It is read as partly a trend.
- **Test 7 (substitution):** 5+ unit homes and one-unit homes also read "we do not know" (61st and 81st percentiles). The 5+ check failed Test 4, so it is partly trend.

## What this means

- The primary test was designed to give a usable answer either way. It gives "we do not know", with a range from about −21% to +92% for 2–4 unit homes.
- In homes, the range is −0.07 to +0.65 per 1,000 single-family homes per year. For Wisconsin's 1,839,569 single-family homes, that is about −130 to +1,200 homes a year in 2–4 unit buildings, before the Census gap (Test 6: Census sees about 1/1.5 to 1/3 of townhouse-inclusive middle housing).
- Every state's own difference is positive, but no more than fake law states produce by chance one time in seven.
