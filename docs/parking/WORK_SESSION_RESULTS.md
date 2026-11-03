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
- **Comparison partly treated.** The 2015 ordinance itself reached ½ mile along Pedestrian Streets (corrected by the audit; an earlier version of this line said 2019). Some 402–805 m comparison lots were therefore treated for all of 2016–2020, which pushes the estimate toward zero.
- **Resolved by the audit sweep (2026-11-03): the 2015 relief applied only to B, C and D districts.** Earlier wording, kept for the record: if the 2015 parking relief applied only in business, commercial and downtown districts, then the lot tests' "reform" side (every lot within 402 m except TOD's density-bonus lots) is mostly residential lots that got no parking change. The Chicago lot tests would then not be parking tests. To verify against the 2015 ordinance (SO2015-...) before any further use.
- **Reading:** one city, so this is descriptive. The sign is opposite to the prediction, as in Chicago's other lot tests, which were not parking tests as run (see the Chicago B/C/D rerun). SF, Buffalo and Seattle have no usable multifamily zoning data on the lot table.

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
- **S1 status: skipped.** Only 6 of 68 places are eligible, under the locked minimum of 8, and the learning thread agreed to skip it. It still counts in the running test count.
- **Short-history places.** Cincinnati and San Diego had less than 2 years of the rule before the 2020 census. They are counted among the 6 eligible places but would have given little signal; with the skip, nothing is estimated for any place.

## Combo (a): parking removed vs not at TOD's district edge (*post hoc*)

- **Data:** TOD's "original 11" edge-test places at the main 91 m band, coded by whether parking minimums were removed with the rezoning. Places that fail TOD's balance rule are left out.
- **What's left:** only one "removed" place passes balance, Denver (+298.6 extra homes per 100 lot acres a year). Charlotte (+16.9) and Portland (+9.0) fail balance.
- **"Not removed" places passing balance:**
  - Philadelphia: +86.2;
  - Austin: +35.0;
  - Saint Paul: +14.8;
  - Chicago: +6.6.
- **Arithmetic difference:** +262.9.
- **Not usable as a comparison:** it rests on one place (Denver). The same caution applies as in the earlier station-area description.


## Chicago lot tests rerun on B/C/D lots only (*post hoc*; rule written first)

- **Why the rerun.** The audit confirmed from SO2015-5334 that Chicago's 2015 parking relief covered only B, C and D districts (cuts up to 50% within 1,320 ft of a station). The earlier Chicago lot tests (B1, FU7, the October test) mostly coded untreated residential lots as "reform".
- **Rerun design.** Reform side: B/C/D lots within 402 m. Comparison: B/C/D lots at 402–805 m. Zoning classes come from the November 2012 map, so classes match on both sides.

| Test | Density-bonus lots | Reform / comparison lots | Estimate (90%; 97.5%) | Unit |
| --- | --- | --- | --- | --- |
| FU7-style, all lots | kept (main) | 5,927 / 4,637 | −6.53 (−21.19 to +6.57; −28.06 to +11.04) | net new homes per 1,000 lots a year |
| B1 (FAR ≥ 1.2) | kept (main) | 5,905 / 4,622 | −6.24 (−17.28 to +3.77; −21.55 to +6.95) | net new homes per 100 lot acres a year |
| FU7-style | dropped | 4,502 / 4,637 | −14.28 (−27.47 to −2.44) | per 1,000 lots |
| B1 | dropped | 4,480 / 4,622 | −11.18 (−21.55 to −1.83) | per 100 lot acres |

- **Read.** With the right districts, Chicago's reform-ring estimate is still negative, but its interval includes 0 when the density-bonus lots are kept.
- **Pedestrian Streets.** The 2015 ordinance's 805 m reach along Pedestrian Streets is not applied (no layer on disk). Some treated lots therefore sit in the comparison, which pushes toward zero.
- **FU7's "does not generalise" leans on Chicago.** Chicago, on its correct scope, still points negative, so the reading stands. It now rests on a better-coded test.
- **Tool text (resolved).** Ryan: "remove the line and not consider that a relevant residential reform" (2026-11-03 14:24). The Chicago clause is removed from the Why card, and the Chicago lot tests are no longer used as evidence. The card had said "Chicago's largest lots lost homes". That came from the mis-scoped test. A caveat or rewording needs Ryan's OK.

## N3, San Diego 2019 TPA edge test

- **Outcome:** new homes per 100 lot acres a year, (after − before) inside minus outside, 91 m band, application dates.
- **Main estimate:** +1.26 (90% −1.34 to +4.63; 97.5% −1.92 to +6.34). MDE 3.10.
- **Balance passes:** before-window gap +0.05 (−1.21 to +1.33). Bunching is not flagged.
- **Reading:** not supported. The sign is as predicted, but the result is fragile:

| Check | Estimate (90%) |
| --- | --- |
| 46 m band | +2.01 (−2.99 to +9.40) |
| 183 m band | −4.41 (−14.62 to +1.84) |
| 25 m donut | −0.03 (−1.85 to +1.94) |
| Issue dates | −0.20 (−1.58 to +1.11) |

- **Deviation: the line is not a 2019 line.** Outside the Coastal Zone, layer 6's TPA features are the SANDAG 2022 polygons. The "SANDAG 2022 sensitivity" is therefore the same line and adds nothing.
- **Counts versus feasibility.** The feasibility count of lots with new homes within 183 m (159 / 105 before) used every permit point near the line. The run counts fewer (102 / 81 at 183 m) because it:
  - keeps only permits matched to a City parcel (85%);
  - drops the Coastal Zone and edges within 30 m of it;
  - keeps only 400 m segments with lots on both sides. No 2019 TPA layer exists. Stops added after 2019 count as treated, which pulls toward 0.
- **No density bonus:** +1.26. Only 1 flagged lot is in the sample, so this check is weak.
- **Coastal Zone:** the Coastal Commission approved with modifications on 2019-10-16, and the City adopted O-21164, effective 2020-02-09. This most likely certified the change before 2020-11-30, but that is inferred. The Coastal Zone is dropped, so this does not affect the estimate.
- **Projects with 2+ homes (counts only, 91 m band):** 6 / 5 before, 10 / 8 after.
- **Parcels:** SANDAG and SanGIS data under the SanGIS end-user agreement.

## Combo (b): TOD + parking combined band from paired draws

- **Unit:** Wisconsin extra homes, 2027–2031.
- **Parking draws:** placebo set averages centred on the real average. Positive draws are multiplied by 0.900, the off-TOD share from the combined bundle after TOD's AQ-075: (30,355 − 12,521) ÷ 19,818.
- **TOD draws:** `reference/tod_line_draws.csv`, with upper 12,521 (AQ-075).

| Band | Index pairing (errors unrelated) | Sorted pairing (errors move together) |
| --- | --- | --- |
| **One combined band: TOD central + parking draws** | **−35,057 to +26,876** | −40,074 to +32,650 |
| Lower line: TOD lower + parking draws | −40,551 to +21,185 | −42,665 to +23,084 |
| Central line: TOD only (parking's central is 0) | 4,866 to 15,361 | same |
| Upper line: TOD upper + parking draws | −33,039 to +29,520 | −38,865 to +36,468 |

- **Reading the upper row.** It shows the spread of the draws, not a band around the 30,355 line; its median is −3,616. The single combined band in the first row is the better summary.
- **Read.** Parking's uncertainty dominates. Its spread is about ten times TOD's.
- **Evidence only;** no tool change.

## T1, non-residential placebo

- **Places.** 51 PRN entries rated "not_housing", adopted 2013–2024, were coded before any outcome was seen.
  - 12 were dropped for a housing reform within 3 years, and 5 because they are not in the permit files. 34 were kept.
  - 31 are estimable.
- **Results** (permits per 1,000 existing homes a year; 90% intervals):
  - All homes: +0.40 (−0.64 to +2.94); equal-weight +0.75.
  - 5+ unit homes: +0.10 (−0.29 to +1.51).
- **Reading: passes.** The 90% interval includes 0. The comparison method does not manufacture an effect where housing rules did not change, which supports the near-placebo (FU6) and the method behind the 76-place result.

## T2, staggered event study (Sun and Abraham), cross-check

- **Sample:** 75 repeal places, with 3,048 never-treated places (the union of their comparison places), 2012–2025.
- **Specification:** cohort × relative-year cells; place and year fixed effects; SEs clustered by place.

| Outcome | Post effect, years 1–3 (90%) | Weighting |
| --- | --- | --- |
| Permits per 1,000 existing homes a year | +0.44 (−0.62 to +1.50) | treated place-years |
| same | +0.02 (−1.19 to +1.22) | homes |
| log(yearly permits + 0.5) | +0.19 (−0.02 to +0.41) | treated place-years |
| same | +0.11 (−0.11 to +0.32) | homes |

- **Pre-trend fails, against the 3,048 never-treated places.** In the rate outcome, leads −5 and −3 are +2.58 (+0.87 to +4.30) and +2.63 (+0.90 to +4.36) against year −1. In the log outcome, lead −3 is +0.34 (+0.16 to +0.51). Against never-treated places, repeal places were building faster 3–5 years before repeal than just before it. Against the matched comparison the main estimate uses, the opposite holds: repeal places were rising into repeal (home-weighted gaps against year −1 of −2.09, −1.81, −1.62 and −1.20; audit). The direction depends on the comparison group.
- **Read.** The event-study post effect sits near zero to slightly positive, beside the main −1.14. With a failing pre-trend, it cannot be read as causal. Against the matched comparison, the 5-year before window does not drag the main estimate down (consistent with P1). The low line stays at −15,234. This is a cross-check, not a replacement.

## P1–P3, pre-trend follow-ups

Unit: permits per 1,000 existing homes a year. These runs use 75 places (South Bend has no home count), so the main estimate here is −1.07, not the 76-place −1.14.

| Version | Estimate (90%) |
| --- | --- |
| Main (5-year before window) | −1.07 (−3.44 to +1.54) |
| P1, short before window (years −2, −1) | −1.81 (−4.39 to +0.98) |
| P2, also matched on before-trend | −0.96 (−3.27 to +1.83) |
| P2 pre-trend check (years −2, −1 vs −5 to −3) | +1.60 (−0.12 to +3.28): passes, but only just; read as "not clearly failing" |
| P3 bound (M = 1; largest before-year gap 2.09) | −5.52 to +3.63 |

- **Pass rule: not met.** P1 moves the estimate further below 0, not toward it. So the lines stand, and the pre-trend issue goes into the how-it-works text.
- **Read.** The short window doesn't support the idea that the 5-year window dragged the estimate down. Trend matching barely moves it, but that is mostly built in: P2 equals the main estimate for the 20 places with 10 or fewer comparison places, which hold 69% of the home weight. Allowing for trend gaps as large as those seen before repeal widens the honest range to about −5.5 to +3.6.
- **Chicago in the 76:** not in the 76-place set (neither its 2013 nor its 2015 rule), so no "without Chicago" version is needed.
- **Chicago and T1:** Chicago 2015 cut housing parking in B/C/D districts, so it breaks T1's locked "no housing change" rule and is not added to the placebo.
- **Suggested how-it-works line (needs Ryan's OK).** "Before repeal, repeal places did not move in step with their comparison places (a gap of about 2 per 1,000 homes a year over 5 years). Allowing for that, the range is about −5.5 to +3.6, wider than −3.4 to +1.5."

## Chicago B/C/D with home and acre denominators (*post hoc*; owner's ask)

- **Sample:** the same B/C/D lots, 5,927 reform and 4,637 comparison, from the November 2012 zoning map.
- **Denominators:**
  - Per lot acre (842 reform acres, 598 comparison): −6.19 net new homes per 100 lot acres a year (90% −17.02 to +3.72).
  - Per existing home: +107 per 1,000 existing homes a year (90% −364 to +649). Not usable: only 201 and 290 homes stood on these lots before. Business-district lots were mostly non-residential, so a home denominator explodes.
- **Pedestrian Streets: not fixable for now.** B/C/D lots on Pedestrian Streets 402–805 m from a station were treated in 2015 but sit in the comparison band, and no 2015 layer is on disk. That pushes every Chicago estimate toward zero.
- **Read:** on the right lots and the acre denominator, Chicago is about −6 per 100 lot acres a year, with a range that includes 0. It stays a side result; it is not in the 76 and does not feed a tool line.
