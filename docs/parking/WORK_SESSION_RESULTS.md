# Parking work session results (natural experiments, denominators, grid)

Plans: `docs/parking/CAUSAL_FRAMEWORK_PLAN.md`, sections "Natural experiments N1–N4" and "Work session" (locked 2026-11-03 before any count). **Running test count: 32** (27 after N1–N4; the grid, S1, B1, the combination and the backtest make 32). Nothing in the tool changes without Ryan's OK.

## N2, Minneapolis step 2 (first stage)

- **Contrast:** outside the 2015 areas minus inside, May 2021 on vs 2016–May 2021, in car spaces per home.
- **Result:** +0.03 (90% −0.16 to +0.29; 97.5% −0.24 to +0.36). MDE 0.22.
- **Cells:**
  - outside 0.68 → 0.61 (72 → 30 projects);
  - inside 0.71 → 0.61 (104 → 54 projects).
- **Reading:** not supported. The prediction was negative.
- **Power:** an MDE of 0.22 is about the whole citywide drop after 2015 (0.24, F1). N2 cannot rule out an effect of the size seen elsewhere.
- **Partial treatment:** the inside group was only partly treated before 2021. The 2015 rule removed minimums for 3–50 home projects and halved them for 51+, and 2021 removed the rest. That shrinks the expected gap.
- **Balance:** not feasible. The cells are 33 / 8 / 20 / 8 projects, below the 20-per-side rule, so balance is not used.

## D1 and the six-version grid

- **Common error unit:** permits per 1,000 existing homes a year.
- **Scoring:** each version's leave-one-place-out prediction is scored against the place's measured main effect. Lower error is better.
- **D1 zero counts:** 33 of 75 places had zero 5+ permits in a window, and 0.5 was added to every place.

| Places | Version | Estimate (90%; 97.5%) | Estimate unit | Held-out error | Predict zero | Beats zero | Beats main |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all 76 (75 usable) | per 1,000 homes (main) | −1.07 (−3.44 to +1.54; −4.28 to +2.52) | permits per 1,000 homes a year | 5.31 | 5.05 | no | — |
| all 76 | D1 log change, 5+ permits | −0.088 (−0.350 to +0.193; −0.451 to +0.311) | log change (≈ −8%) | **4.95** | 5.05 | yes | yes |
| all 76 | D2 per 1,000 existing 5+ homes | −1.59 (−5.91 to +3.79) | per 1,000 existing 5+ homes | 5.17 | 5.05 | no | yes |
| S2 (37 usable) | per 1,000 homes | −0.92 (−3.03 to +1.85) | permits per 1,000 homes a year | 4.65 | 4.40 | no | — |
| S2 | D1 | −0.147 (−0.528 to +0.278) | log change (≈ −14%) | **4.34** | 4.40 | yes | yes |
| S2 | D2 | −3.48 (−8.63 to +2.18) | per 1,000 existing 5+ homes | 4.33 | 4.40 | yes | yes |

- **Selection:** by the locked rule, the winner is D1 on all 76 places. It beats both "predict zero" and the main version on the same places.
- **The win comes from Austin.** Austin accounts for +0.21 of the 0.105 margin. Without Austin, predicting zero does better than D1 (audit).
- ***Post hoc*** (`reference/parking_ws_grid_posthoc.csv`). Error difference D1 minus predict-zero; negative means D1 is better.

| D1 version | Places | Estimate | Error difference (90%) | Share of resamples where D1 wins |
| --- | --- | --- | --- | --- |
| add 0.5 (locked) | 75 | −8.5% | −0.11 (−0.48 to +0.28) | 64% |
| add 1 | 75 | −7.2% | −0.06 (−0.37 to +0.25) | 59% |
| drop places with a zero window | 42 | +0.7% | +0.30 (+0.14 to +0.44) | 0% |

- **Read:** D1's edge over "predict zero" is within noise and depends on how zeros are handled. When the places with zero counts are dropped, zero wins clearly.
- **The margin is small:** 4.95 against 5.05, a 2% lower error.
- **D1 in Wisconsin** (5+ unit current-law permits in eligible places, 46,905 over 2027–2031): exp(−0.088) − 1 = −8.4%, about −3,965 apartment homes (90%: −13,863 to +9,999).
  - The interval includes 0 and the estimate is not supported.
  - It would replace the per-1,000 lines only with Ryan's OK.
- **S2:** both S2 log and per-1,000-5+ versions beat zero on their 37 places. Applied to all eligible Wisconsin homes, S2-D1 would be about −13.7% of 5+ permits, about −6,412 homes over 2027–2031.

## N1, Oregon's state rule (intent-to-treat)

- **Treated:** DLCD's 48 covered cities (table as of 2023-07-24), with Portland dropped, leaving 47. Of those, 39 are usable.
  - An earlier run used a 45-city list built from MPO membership (38 usable). It gave +1.28 against Washington, almost the same.
- **Windows:** event 2023; before 2018–2022, after 2023–2025.
- **Comparison places dropped:** 14 Washington and Idaho places that had their own 2018–2025 parking reform.

| Comparison | Effect (90%; 97.5%) | MDE | Median comparison places |
| --- | --- | --- | --- |
| Washington (main) | +1.26 (−0.66 to +2.87; −1.36 to +3.36) | 1.75 | 46 |
| Idaho | +0.97 (−4.71 to +5.46) | 5.18 | 12 |

Unit: permits per 1,000 existing homes a year.

- **Reading:** not supported (the 97.5% interval includes 0). The point estimate is positive, as predicted.
- **Washington is partly treated after 2024.** Washington's 2024 and 2025 state laws cut parking for middle housing near transit. That pushes N1 toward zero.
- **Self-selection check:**
  - 16 covered cities are also among the 76. In N1 they average +3.17; in the 76-place comparison they average +1.64.
  - The 76-place figure (+1.64) sits inside N1's 90% interval (−0.66 to +2.87), so there is no sign that self-selection biased the 76. But this check could only detect a large gap (MDE 1.75).
  - Part of the gap may come from the 76-place comparison places in Oregon, which CFEC also covered.
