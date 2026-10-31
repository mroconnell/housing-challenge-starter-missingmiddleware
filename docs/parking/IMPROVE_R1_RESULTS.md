# Parking improvement loop, round 1: results

Written 2026-10-31 by the parking conductor. Plan: [IMPROVE_R1_PLAN.md](IMPROVE_R1_PLAN.md), committed before running, with changes logged. Script: `scripts/run_parking_improve_r1.py`. Outputs: `reference/parking_improve_r1_places.csv`, `reference/parking_improve_r1_summary.csv`, `reference/parking_improve_r1_checks.csv`.

All rates are permits per 1,000 existing homes per year. The range shown is the 90% range from resampling places. It is not the placebo range that sets the tool's high end.

The variants use 73 of the tool's 76 places. South Bend (combined county row), Gastonia (trimmed years) and Avondale Estates (trimmed years) need special handling that the standard panel does not have. V0 reproduces the current method on those 73: −1.10, against −1.14 for all 76.

## Results

| Variant | Places | Home-weighted average | 90% resampling range | Equal weight | Median | Median comparison places |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| V0 current method | 73 | −1.10 | −3.59 to +1.53 | +0.42 | −0.05 | 28 |
| V1 reported months only | 73 | −0.64 | −3.24 to +2.33 | +0.65 | +0.04 | 28 |
| V1b reported months scaled to 12 | 73 | −1.26 | −3.77 to +1.45 | +0.32 | −0.08 | 28 |
| V2 drop places with estimated years | 41 | −1.20 | −5.55 to +3.93 | +0.78 | +0.33 | 34 |
| V3 clean pools (any reform ever), national fallback | 73 | −0.82 | −3.98 to +2.78 | −0.06 | −0.03 | 31 |
| V3a clean pools, no fallback (first run) | 71 | +1.17 | −1.45 to +3.73 | +0.34 | +0.44 | 31 |
| V3b date-aware clean pools, national fallback | 73 | −0.15 | −2.78 to +2.87 | +0.04 | −0.06 | 31 |
| V4 pre-repeal homes and population | 73 | −0.91 | −3.53 to +1.89 | +0.70 | −0.16 | 27 |
| V5 V1 + V3 + V4 | 73 | −0.25 | −3.63 to +3.68 | +0.25 | −0.13 | 37 |
| **V6 V1b + V3b + V4 (all fixes)** | 73 | **−0.28** | **−3.00 to +2.85** | +0.04 | −0.37 | 37 |
| V0 without the 4 heaviest places | 69 | −0.17 | −1.99 to +2.00 | +0.54 | −0.05 | 34 |
| V0, 3 after-years only | 36 | −0.92 | −3.06 to +1.67 | +0.36 | −0.28 | 35 |
| V6 without the 4 heaviest places | 69 | +0.01 | −1.87 to +2.19 | −0.03 | −0.37 | 40 |
| V6, 3 after-years only | 36 | −1.37 | −4.05 to +2.19 | +0.43 | −0.79 | 44.5 |

The 4 heaviest places are San Francisco, Austin, San Jose and Raleigh.

## Flags (flag-only checks)

- **Fewer than 5 comparison places:** 17 place-variant rows, mostly in V3a, which has no fallback.
- **No effect computed:** 2 rows, Minneapolis and Austin in V3a. Their clean pools were empty.
- **Largest move from V0 to V6:** Bastrop, Texas, from +30.6 to +49.0. Bastrop grew fast, so subtracting post-repeal permits shrinks its pre-repeal homes and raises its rate. Its weight is small (about 3,000 homes).
- **Placebo blanks named (audit item 1):** the 6 blank rows in the placebo test are all one stand-in, Nashville-Davidson (Tennessee, BPS 47|605000). It was drawn for San Jose, San Francisco, Raleigh, Minneapolis, Austin and Sacramento, and had no comparison places of its own.

## Reading

- **The fixes move the home-weighted average toward zero:** −1.10 under the current method, −0.28 with all fixes.
- **The move is well inside the noise.** Both 90% ranges span zero by about 3 points either way.
- **The biggest single driver is the comparison pools.** Leaving out places with any recorded housing parking reform takes the average from −1.10 to between −0.82 and −0.15, depending on how dates are handled.
- **Estimated permit months matter less.** Scaled reported counts give −1.26.
- **The conclusion is unchanged:** about zero, with a range that includes modest gains and modest losses.

## Next

Per the audit, if V6's data become the standard, the placebo test and high end must be rerun on V6. They are being run so that Ryan can compare. The tool does not change unless Ryan approves.
