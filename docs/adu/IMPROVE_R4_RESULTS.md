# ADU improvement loop, round 4: Washington's partial law year (results)

Run 2026-11-01 under [IMPROVE_R4_PLAN.md](IMPROVE_R4_PLAN.md), committed before running. Code: `scripts/run_adu_improve.py --round 4` and `run_pooled_revision.build(wa_partial=True)`. Outputs: `reference/adu_improve_r4_*.csv`.

**Units.** Rates are ADU permits per 1,000 single-family homes per year. Log error = log(predicted ÷ observed) for a state left out of the fit; RMS over the 7 states, lower is better. Wisconsin figures are additional ADU permits, 2027–2031.

## Answer

- **Counting only Washington's time under the law fixes Washington's miss:** +0.20 (20% too high) → −0.10.
- **Held-out RMS improves:** 0.130 → 0.121. Vermont (+0.22) is now the worst state.
- **Wisconsin rises:** lower 6,320 → 6,604; central 10,615 → 10,931; upper 19,925 → 20,761. Baseline (786) and reference line (10,142) unchanged.
- **Why it rises:** Washington's measured law-year rate goes from 0.77 to 0.98 permits per 1,000 single-family homes per year. The four counties issued 437 ADU permits in the estimate year, 9 months of it under the law, a higher rate than all Washington cities averaged over a full year. So the law's measured effect goes up.
- **Ryan decides** whether the tool adopts it.

## Detail

| | Adopted (AQ-066) | W1: four counties, 9 of 12 months |
| --- | ---: | ---: |
| Washington's 2026 law row | 888 permits, all cities outside Seattle, 1 full year | 437 permits, 81 cities in King, Pierce, Snohomish and Kitsap, 0.75 of a year |
| Washington held-out miss (adopted model) | +0.20 | −0.10 |
| Held-out RMS (7 states) | 0.130 | 0.121 |
| Worst state | Washington +0.20 | Vermont +0.22 |
| Lower / central / upper | 6,320 / 10,615 / 19,925 | 6,604 / 10,931 / 20,761 |

Held-out log error by state, adopted model:

| State | Adopted | W1 |
| --- | ---: | ---: |
| Washington | +0.20 | −0.10 |
| Oregon | +0.13 | +0.15 |
| Rhode Island | −0.08 | −0.08 |
| Massachusetts | +0.06 | +0.09 |
| Maine | −0.12 | −0.09 |
| Utah | −0.06 | −0.03 |
| Vermont | +0.19 | +0.22 |

Simple models score better too (plain average 0.27 → 0.23; median 0.19 → 0.14). The adopted model still scores best.

**Limits.** All 12 months' permits (437) are divided by 9 months of exposure, as Massachusetts' 2025 count is divided by 11 of 12. Permits from the 3 months before 2025-06-30 are counted as law-period permits, which slightly overstates the four counties' rate. Cities in counties that bound from about 2025-12-31 (3 months) are left out, not counted at a fraction.
