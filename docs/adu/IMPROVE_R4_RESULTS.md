# ADU improvement loop, round 4: Washington's partial law year (results)

Run 2026-11-01 under [IMPROVE_R4_PLAN.md](IMPROVE_R4_PLAN.md). The first run (W1) had an error the audit caught: it divided 12 months of permits by 9 months of time. The corrected variants (W2, W3) and the Massachusetts check (M) were written into the plan before the rerun. Code: `scripts/run_adu_improve.py --round 4`, `run_pooled_revision.build(wa_partial=..., ma_full_year=...)`. Outputs: `reference/adu_improve_r4_*.csv`.

**Units.** Rates are ADU permits per 1,000 single-family homes per year. Log error = log(predicted ÷ observed) for a state left out of the fit; RMS over 7 states, lower is better. Wisconsin figures are additional ADU permits, 2027–2031.

## Answer

- **Correctly counted, the partial law year does not fix Washington's miss.** With the pre-law months removed (W2), Washington is still predicted 24% too high; spread over the full year (W3), 19% too high.
- **The first run's gain was arithmetic, not evidence.** W1's +0.20 → −0.10 came from dividing 12 months of permits by 9 months.
- **Why it doesn't help:** the four counties under the law (King, Pierce, Snohomish, Kitsap) issued 502 ADU permits in estimate year 2025 and 437 in 2026, the year the law began. Their rate did not rise in the first months under the law, so it is about the same as Washington's overall rate.
- **Massachusetts counted over the full year (M)** lowers its observed rate from 1.01 to 0.92 and the central by 123 permits.
- **Recommendation: no change to the tool.** The corrected versions move the central by −123 to +117 permits (about 1%) and none improves the held-out RMS. Washington's over-prediction stays a known limit: its law is too new to show.

## Results

| Variant | Washington's 2026 law row | Massachusetts 2025 | Held-out RMS | Washington miss | Lower | Central | Upper |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| A0 adopted | all cities outside Seattle (888), 1 year | 11/12 year | 0.130 | +0.20 | 6,320 | 10,615 | 19,925 |
| W1 (error) | four counties (437), over 0.75 year | 11/12 | 0.121 | −0.10 | 6,604 | 10,931 | 20,761 |
| W2 | four counties, 437 − 125.5 pre-law, over 0.75 year | 11/12 | 0.143 | +0.24 | 6,408 | 10,732 | 20,299 |
| W3 | four counties (437), over 1 year | 11/12 | 0.130 | +0.19 | 6,333 | 10,654 | 20,120 |
| M | as adopted | full year | 0.136 | +0.19 | 6,320 | 10,492 | 19,784 |
| W2 + M | as W2 | full year | 0.149 | +0.22 | 6,408 | 10,608 | 20,166 |
| W3 + M | as W3 | full year | 0.137 | +0.17 | 6,333 | 10,530 | 19,983 |

Washington's observed law-year rate: 0.77 (adopted), 0.70 (W2), 0.74 (W3); W1's 0.98 was the error.

The four counties' ADU permits by estimate year (incorporated cities, Seattle excluded): 167 (2019), 158 (2020), 180 (2021), 192 (2022), 329 (2023), 407 (2024), 502 (2025), 437 (2026).

**Check:** no city is split by OFM between one of the four counties and another county.
