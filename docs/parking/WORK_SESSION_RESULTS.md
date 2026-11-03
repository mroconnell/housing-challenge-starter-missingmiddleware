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

## B1, multifamily-zoned lots (Chicago only)

- **Design:** Chicago lots zoned for multifamily (allowed FAR 1.2 or more before the reform). Reform lots are within 402 m of a station, under the 2015 rule. Comparison lots are 402–805 m away.
- **Lots:** 20,344 reform, 18,854 comparison.
- **Change in net new homes** per 100 multifamily-zoned lot acres a year: reform lots +6.86, comparison lots +11.45.
- **Effect:** −4.59 (90% −8.49 to −1.07; 97.5% −9.77 to +0.19).
- **What "dropped TOD lots" means.** TOD's `treated` lots for Chicago are lots eligible for the 2015 ordinance's density bonus, coded from the November 2012 zoning map within the station distance. They are not after-window rezonings. Dropping them removes eligible reform-ring lots from one side only.
  - *Post hoc*, with those lots kept: −2.95 (90% −7.24 to +0.95; 97.5% −8.91 to +2.55).
- **Comparison partly treated.** In 2019 Chicago extended the rule to ½ mile along Pedestrian Streets. Some 402–805 m comparison lots were therefore treated in 2019–2020, which pushes the estimate toward zero.
- **Open question for all Chicago lot results (B1, FU7 −11.2, October −2.6).** If the 2015 parking relief applied only in business, commercial and downtown districts, then the lot tests' "reform" side (every lot within 402 m except TOD's density-bonus lots) is mostly residential lots that got no parking change. The Chicago lot tests would then not be parking tests. To verify against the 2015 ordinance (SO2015-...) before any further use.
- **Reading:** one city, so this is descriptive. The sign is opposite to the prediction, as in Chicago's other lot tests (FU7: large lots −11.2). SF, Buffalo and Seattle have no usable multifamily zoning data on the lot table.

## Backtest: boosted trees as the no-repeal path (D1 target)

- **Training:** boosted trees on 5,478 comparison-place windows predict each repeal place's log change in 5+ permits had it not repealed. The effect is the actual change minus the prediction.

| Version | Estimate (90%; 97.5%) | Held-out error | Predict zero |
| --- | --- | --- | --- |
| Boosted no-repeal path | +0.289 log, +34% (+0.021 to +0.606; −0.069 to +0.734) | 6.86 | 5.05 |
| Matched comparison (D1, for reference) | −0.088, −8% (−0.350 to +0.193) | 4.95 | 5.05 |

Error unit: permits per 1,000 existing homes a year.

- **Read:** the boosted path does much worse than predicting zero on held-out places (6.86 against 5.05). Its large positive estimate is not credible as an effect. Its 97.5% interval includes 0 (not supported), and the model likely under-predicts the after window for places that built many apartments before.
- **Result:** the matched comparison stays the better comparison path.
- **The no-repeal path decides the sign.** Matched gives −8%, boosted +34%. The boosted model expects big apartment cities to fall anyway; Minneapolis, for example, is predicted at −0.44 log.
- **The interval understates uncertainty.** It resamples places but does not refit the model.

## N3 and N4 feasibility (counts only; `scripts/fetch_parking_natural_experiments.py`)

**N3, San Diego 2019 TPA: feasible under the locked rule.**
- **Ordinance:** O-21057, passed 2019-03-19. In effect 2019-04-24 outside the Coastal Overlay Zone; inside it, pending Coastal Commission certification for at least a year.
- **Application dates:** the permit layer has issue dates only. Application dates come from joining the City's development-approvals files (the earlier of the project and approval create dates). Every record issued in 2016–2020 matched.
- **Line:** no 2019-dated layer exists. The nearest is the City's ParkingAmenityTPA layer 6 (based on the 2015 regional plan; edited 2022–23). TOD's San Diego case uses SANDAG 2022, which adds about 8 sq mi that were not TPA in 2019.
- **Lots with new homes within 183 m** (inside / outside):
  - before: 159 / 105;
  - after: 177 / 116.
  - Smallest cell: 61 on any line.
- **Lots with 2+ new homes:** 24 / 18 before, 29 / 16 after. The rule covers multifamily only, and the outside side falls below 20.

**N4, New York 2016 Transit Zone: not feasible.**
- **Rule:** confirmed in ZR 25-251 and 25-252.
- **Data:** HPD new-construction buildings within 183 m of the line.
  - Outside: 4 before (2014–2015) and 14 after (2017–2019).
  - Inside: 18 before.
- Both sides fall below 20.

## S1 eligibility (census-block edge design; count only)

- **Candidates:** 68 places. The eligibility list is `reference/parking_ws_s1_eligibility.csv`.
- **Eligible: 6**, short of the 8 the locked rule needs, so S1 can only be descriptive.
  - Aledo IL (2015), Champaign IL (2015), Minneapolis (2015), Sacramento (2012), Cincinnati (about 2018) and San Diego (2019).
  - Only the first 4 had 2 or more years in force before the April 2020 census.
- **Main reasons the other 62 failed:**
  - the date could not be confirmed (about 17, including Seattle, whose housing part probably dates from 2010);
  - the rule is older than 2011;
  - zoning changed along the same line;
  - the district is too small for 10 blocks a side;
  - the reform was not district-only.
- Several code sites blocked automated access, so some dates come from secondary copies (flagged in the file).
