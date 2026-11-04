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

## Chicago B/C/D with home and acre denominators (*post hoc*; owner's ask; corrected after audit)

- **Sample:** B/C/D lots, 5,927 reform and 4,637 comparison, using November 2012 zoning.
- **Zone match fixed.** The zone match now includes DC (Downtown Core), using `^[BC]\d|^D[CXRS]` in both Chicago scripts. It adds 0 lots within 805 m of a station in the lot table, so the B/C/D rerun is unchanged.
- **Correction.** An earlier version used `units_before`, which counts homes permitted in the 6 years before, not homes that existed. It also said "only 201 and 290 homes stood on these lots", which is withdrawn. The lot table's existing-homes column is empty for Chicago, so existing homes now come from 2010 census blocks. Each block's housing units go to the nearest kept lot within 100 m.

| Denominator | Estimate (90%) | Unit |
| --- | --- | --- |
| Per lot acre (842 / 598 acres) | −6.19 (−17.02 to +3.72) | net new homes per 100 lot acres a year |
| Per existing home (2010 census; 97,917 / 66,295 homes) | −0.60 (−1.64 to +0.28) | net new homes per 1,000 existing homes a year |
| Per residential lot acre (lots in residential or mixed use: 33 / 32 acres) | −37 (−1,290 to +239) | per 100 residential lot acres; not usable, because the denominator is tiny |

- **Read.** On every usable denominator Chicago leans negative, with a range that includes 0.
- **Pedestrian Streets: not fixable.** Treated lots along Pedestrian Streets sit in the comparison band, and no 2015 layer exists to remove them. This pushes the estimate toward zero.
- **The home count is too wide (audit).** Every 2010 block within 100 m of a B/C/D lot is counted, so homes on nearby residential blocks are included. That gives 97,917 homes on 842 acres, about 116 per acre, which is high. The true per-home rate is likely further from 0. A cleaner version would count only blocks whose point falls inside a B/C/D polygon; it was not run.
- **The Loop is not covered.** The DC fix adds 0 lots, so the lot table likely doesn't reach the Loop.
- **Status:** a closed side result. Not in the 76, and no tool line or low line.

## Los Angeles Adaptive Reuse Ordinance (1999), census spot check (descriptive; Manville 2013)

- **What the ordinance did.** Ord. 172571 took effect on 1999-06-03 in the Downtown Project Area. For conversions of pre-1974 buildings it:
  - froze required parking at the spaces already on the site;
  - waived lot-area density limits;
  - kept existing floor area, height and yards.
  So this measures the whole package, not parking alone.
- **Tracts.** Chosen before any housing numbers were pulled:
  - **6 ordinance tracts:** Historic Core / Old Bank District (2073.04–.08) and Financial District (2077.12).
  - **3 contrast tracts:** Boyle Heights 2042 and 2060.53, and Westlake 2088.01. All are outside the Central City plan area and outside the 2003 incentive areas.
- **Method.** Housing units by year, from census blocks placed by internal point inside fixed 2020 tract outlines. Sources are official Census only:
  - 1990: STF1B;
  - 2000 and 2010: SF1;
  - 2020: PL 94-171.

| Year | Ordinance tracts: total (occupied) | Contrast tracts: total (occupied) |
| --- | --- | --- |
| 1990 | 2,374 (2,012) | 3,705 (3,400) |
| 2000 | 3,594 (2,976) | 3,137 (2,909) |
| 2010 | 7,596 (6,168) | 3,354 (3,136) |
| 2020 | 10,084 (8,747) | 3,411 (3,209) |

- **Read.** From 2000 to 2010 the ordinance tracts gained 4,002 homes (2.1 times), and the contrast tracts gained 217 (1.07 times). This fits Manville's finding that the ordinance unlocked thousands of downtown conversions. Manville counts over 6,000 ordinance units in old tract 2073.
- **Caveats:**
  - **Single tracts are noisy.** Large buildings shift between tiny tracts across census years, so read the group sums.
  - **2000 is not a clean "before" year.** The ordinance tracts had already gained 1,220 homes from 1990 to 2000, which these data don't explain.
  - **Not all 2010–2020 growth is conversions.** Some is new towers, especially in 2077.12.
  - **Contrast tracts could convert from December 2003,** under the citywide Zoning Administrator path.
- **More caveats (audit):**
  - **The contrast tracts are not a control.** Boyle Heights and Westlake are residential and have few old offices, so read them as "the rest of the area did not boom". A fairer contrast would be old commercial tracts that got the rule later (Hollywood or Wilshire Center), used for 1999–2003 only.
  - **Other downtown changes can't be separated out.** 2000–2010 also brought Staples Center, the redevelopment agency's programs and the wider return to downtowns.
  - **No proof the tracts were chosen first.** The tract list, script and results are in one commit, so git can't show the tracts were picked before any data was pulled. The order is the subagent's own account.
  - **No page reference.** "Over 6,000 units in old tract 2073" is from Manville's UCTC working paper (the same study as JAPA 2013); the page was not recorded.
- **Files:**
  - `scripts/fetch_parking_la_aro_tracts.py`
  - `reference/parking_la_aro_tracts.csv`
  - The Census API key was read from the environment only and is in no file.

## Test 35: city-limit edges after AB 2097, feasibility (counts only)

- **Ordinances:**
  - Culver City: Ord. 2022-008, citywide, all uses, adopted 2022-10-24. Effective date not found; 2022-11-23 is assumed.
  - San Jose: Ord. 30857, citywide for housing, effective 2023-04-10. An office minimum stays near SAP Center and Diridon.
  - Neither came with a zoning change.
- **Sacramento and Mountain View:** too new; recheck when 2027 permits exist.
  - Sacramento: the 2040 General Plan was adopted 2024-02-27 and took effect 2024-03-28; it bundles fourplex upzoning.
  - Mountain View: vote 2024-11-12, precise-plan areas only.
- **Usable border at 183 m** (neighbour still has minimums; no freeway, rail or water):
  - Culver City: 21% of 35.8 km. Most of the LA border lies inside LA's own AB 2097 zones.
  - San Jose: 66% of 430 km, mostly unincorporated county land.
- **Lots with new homes, 25 m donut to 183 m** (inside before / inside after / outside before / outside after):
  - Culver City: 12 / **2** / 29 / 16. Fails.
  - San Jose: 82 / 69 / 101 / 125. Passes the 20-lot rule.
- **But most of those lots are ADUs.** Accessory dwelling units make up 13 of 16 to 72 of 86 records per San Jose cell. State ADU law already limits ADU parking, so these lots barely test the parking repeal.
  - Counting non-ADU lots only, San Jose has 14 inside before and 13 inside after. Both cities fail.
- **Verdict: not feasible as a parking test.** San Jose passes the count rule only through ADUs.
- **Already in the evidence:** both cities are among the 76, so this would have been a second look in any case.
- **Caveats:**
  - Zoning across the line could not be compared, so the counts are an upper bound.
  - Records are kept only where the filing city matches the side of the line. This was added after the first run.
  - The transit stop layer is today's.
- **Audit notes on test 35:**
  - **Post hoc.** No plan was committed before the counts. The ADU filter and the filing-city rule were both chosen after the counts were seen. If San Jose is ever run, the ADU choice is locked first.
  - **The ADU filter is fair on legal grounds,** because state law already capped ADU parking.
  - **San Jose's usable border is mostly unincorporated county land** with different zoning; the "zoning not compared" caveat covers this.
  - **Culver City's effective date** uses adoption + 30 days, the usual California rule.
- **Place count.** Each outcome in `parking_expanded_effects.csv` has 76 keys. Across both outcomes there are 77 keys and 75 place names, because there are two Cambridges (MA and MD). Runs that need a home count use 75 (South Bend has none).

## LA AB 2097 map change, feasibility: not feasible

The rule for this check was set by the learning thread for this check (it is not in the framework plan): a dated change, both maps, and 2+ after years.

- **A dated change: partly.** City Planning's 2024-04-16 memo adopted SCAG's stop method "effective immediately". It followed HCD letters of 2023-11-17, 2024-03-08 and 2024-03-28. No document dates a rebuild of the ZIMAS AB 2097 layer.
- **Both maps: no.** ZIMAS's public layer group is empty. No archived 2023 or 2024 version was found, and the only City map is a 2026 polygon. SCAG's stop lists are only proxies, and its 2022 and 2050 lists have been re-issued under the 20-minute rule (AB 2553, 2025).
- **2+ after years: no.** Permits run to 2025-12-31, about 1.7 years after the memo.
- **Bias even with maps:**
  - The same memo also changed TOC and Density Bonus eligibility.
  - Connect SoCal 2024 was adopted 12 days earlier, and AB 2553 and CHIP followed in 2025.
  - Planned stops were already eligible under state law, so the edge is soft.
  - Permit years lag applications.
- **What would change the verdict:** a dated copy of the ZIMAS layer from before and after the memo (e.g. through a Public Records Act request to City Planning), plus 2026 permit data.
- **Fetch headers (audit fix).** The script first sent a browser-style user agent. It now sends an honest one (`missing-middleware-research/1.0 (public data)`). With it, the City Planning documents downloaded normally. The same fix was made in `scripts/fetch_parking_la_toc.py`.
- **Files:**
  - `scripts/fetch_parking_la_ab2097_map.py`
  - `reference/parking_la_ab2097_map_counts.csv` (proxy area counts only)

## Tests 38/39: count models (negative binomial / Poisson), blind selection

- **Design.**
  - Panel: place-years, 2012–2025.
  - Units: the 76 repeal places within their before/after windows, plus the union of their matched pools.
  - Fixed effects: place (concentrated out) and year.
  - Offset: log existing homes. This is one ACS value per place, so the place effects absorb it.
- **Intervals.** 90% intervals from a 2,000-draw place bootstrap, with treated and pool places resampled separately. Checks use place-clustered SEs, because there are no stacks.
- **Places with all-zero counts dropped:**
  - 5+ series: 1,355 places;
  - all homes: 38;
  - 2–4 buildings: 1,205.
- **Usable repeal places:** 58 for the 5+ series, 74 for all homes.
- **Wisconsin conversion bases.** 46,905 (5+ homes) and 116,600 (all homes) are the sums of `five_year_central` in `reference/housing_baseline_by_area.csv`, by structure type, over areas with `eligible_homes > 0` in `reference/parking_model_by_area.csv`. They are computed in the shell, as in the grid. The 5+ candidates convert on 46,905 and hold other homes fixed, so they are narrower partly by assumption. The all-homes candidate is the like-for-like one.
- **Blind phase (choice committed before any centre was printed): no candidate passes.** Every candidate fails the pre-trend rule (all four leads must include 1). The Poisson 5+ candidate passes the width bar but also fails the T1 placebo. Calibration was not reached. **The lines stand.**

| Version | Rate ratio (90%) | Wisconsin homes 2027–31 (90%) | Width, homes | Width, log | Role |
| --- | --- | --- | --- | --- | --- |
| NB, 5+ homes | 0.90 (0.59 to 1.45) | −4,866 (−19,451 to +20,963) | 40,415 | 0.91 | candidate |
| Poisson, 5+ homes | 0.86 (0.69 to 1.17) | −6,661 (−14,724 to +8,090) | 22,814 | 0.54 | candidate |
| NB, all homes | 1.00 (0.82 to 1.23) | +204 (−20,800 to +27,166) | 47,967 | 0.41 | candidate |
| Poisson, all homes | 0.86 (0.71 to 1.12) | −16,584 (−34,014 to +13,588) | 47,602 | 0.46 | beside |
| NB, new 5+ unit buildings | 0.82 (0.62 to 1.08) | — | — | 0.55 | beside, never the lines |
| NB, new 2–4 unit buildings | 1.43 (0.98 to 2.03) | — | — | 0.73 | beside, never the lines |

- **Reading:**
  - None of the count models moves past the current lines.
  - The like-for-like all-homes negative binomial is centred near zero (+204), wider than the current range.
  - Buildings: 5+ buildings lean down and 2–4 unit buildings lean up. Both intervals include 1, and neither was checked for pre-trends, so this is a lean, not a finding.
  - **Model choice moves the all-homes centre a lot:** negative binomial gives +204, Poisson −16,584. Poisson gives big places more pull, like the home-weighted main estimate, so the sign depends on how much weight big cities get.
  - **The 5+ negative binomial's α landed at the top of the grid** (3.0; the grid ran 0.05–3.0, though the first lock said 0.05–5). The best α may be higher, so that width is uncertain. It fails the pre-trend check anyway.
  - **Coverage of the 5+ series:** 18 of the 76 repeal places drop for all-zero counts, so those results cover 58 places.
- **The comparison bar.** The current range (−15,234 to +19,818, width 35,052) runs from the real average to the placebo 95th percentile. It is not a 90% interval.
- **Homes width vs log width.** Homes width shrinks as the rate ratio falls, so "narrowest" tilts toward a more negative centre. The log width is shown beside it for that reason.
- **The pre-trend rule is strict.** It needs all four leads to include 1, so even a clean version would fail by chance about 1 time in 4. That is the rule as locked.

## Milwaukee and Madison project parking records (feasibility; records discovery only)

- **Madison: feasible, mostly for 2015–2022.**
  - **Source.** Legistar "Conditional Use" files carry staff comments with a standard Zoning table ("Required | Proposed", with a parking stalls row). 224 files from 2015–2025 have 5+ homes in the title.
  - **Sample of 26 files:**
    - 2023–2025: all 16 state the rule. Only 2 faced a positive minimum; the rest sit in the Central Area (no minimum since the 2013 code), the TOD overlay (passed 2023-01-17) or a planned development.
    - 2015 to mid-2022: 5 of 10 had a positive minimum with both numbers stated.
  - **Estimate.** About 150 files from 2015–2022. "5 of 10" is a small sample, so the true share facing a minimum could be about 20–80%, roughly 30–120 projects. 30+ looks reachable but is not certain.
  - **If Madison goes ahead,** code the rule in force for each file's date and location: Central Area none since 2013, TOD overlay since 2023-01-17.
  - **Effort.** About 10–14 hours: 4 of code, plus checking each project by hand.
- **Milwaukee: not feasible from public automated sources.**
  - **Legistar.** City Plan Commission files sampled from 2023–2025 state proposed parking in 6 of 11, but a code-required number in none. Planned developments set their own parking.
  - **Blocked.** The Board of Zoning Appeals pages are behind a Cloudflare challenge; cited, not worked around.
  - **MPROP.** PARKING_SPACES is empty in every row.
  - **Path forward.** A public-records request.
- **Biases for a later bunching test:**
  - Only conditional-use and planned-development projects appear, so large projects are over-represented and by-right projects never appear.
  - The numbers are proposed parking, not built.
  - One project can have several files.
  - Projects asking for reductions are over-represented.
  - Mixed-use buildings may combine commercial and residential requirements.
- **Files.** `scripts/fetch_parking_wi_project_parking.py`. Samples are in `data/raw/` (git-ignored; titles contain addresses).

## Test 42: triple difference by Census size class

- **Outcome:** (5+ unit homes − 1-unit homes) per 1,000 existing homes a year, in the main matched comparison (75 places).

| Version | Estimate (90%) |
| --- | --- |
| Main, place bootstrap | −1.01 (−2.29 to +0.47); equal-weight +0.26 |
| Main, metro-clustered bootstrap | −1.01 (−2.27 to +0.79) |
| Beside: 2–4 unit homes | −0.06 (−0.15 to +0.03) |
| Backtest, years −2 and −1 vs −5 to −3 | **+2.66 (+0.77 to +4.26): fails** |

- **Reading: not supported.**
  - **The backtest fails.** The apartment-minus-single-family gap was already rising before repeal, against the comparison places. This agrees with P3: repeal places' 5+ permits were rising into repeal, and the triple difference does not remove that pre-trend.
  - **Weighting decides the sign again:** equal weight gives +0.26, home weight −1.01.
  - **Width.** Converted to Wisconsin homes, the width is 36,780, above the 26,289 bar. That conversion is rough, because this outcome is a relative shift between classes, not added homes.
- **The lines stand.**

## Test 41: two-year totals with an imputation estimator

- **Design.**
  - Untreated model: place and year effects fitted on never-treated pool places plus repeal places before their event. Year 0 is left out everywhere.
  - Effect: actual minus imputed permits, summed over years +1 and +2 after the event.
  - Interval: 90%, from 1,000 county-cluster resamples, each refitting the fixed effects.
- **Coverage.** 57 places (75%) with both years observed, holding 82% of the homes.

| Version | Estimate, cumulative per 1,000 existing homes over 2 years (90%) |
| --- | --- |
| Main, home-weighted | −6.18 (−10.76 to −0.82) |
| Equal-weight | −1.50 (−5.51 to +2.90) |
| Leave one city / county / metro out | −7.30 to −3.66 / −7.30 to −3.66 / −7.30 to −3.82 |
| Pre-trend (mean imputed residual, years −3 to −1) | +0.47 (−1.98 to +2.81): passes |
| **Placebo: single-family homes** | **−4.60 (−6.68 to −2.32): fails** |
| Placebo: T1 non-residential places | +1.23 (−1.57 to +7.50): passes |

- **In Wisconsin** (yearly rate = two-year total ÷ 2, through the Stage 2 path): −41,243 homes (−71,801 to −5,485). Width 66,316, far above the 26,289 bar.
- **Reading: not supported.** The single-family placebo fails. Single-family permits in repeal places also fell well below the imputed path, and parking rules for apartments cannot explain that. The imputation compares big repeal cities with the national pattern of all never-treated places, not with matched similar places, so it picks up a general slowdown in those cities (2022–24). Austin and Raleigh are the most influential. The matched comparison remains the better design. The lines stand.
- **Event path beside it** (main design, years 1–4): +0.02, −1.29, −2.26, −6.50. This two-year total covers years 1–2 only.
- **Audit notes:**
  - **The slowdown is likely, not shown.** The 2022–24 slowdown in big repeal cities is the likely explanation; it was not tested by calendar year.
  - **Not a shift from houses to apartments.** All homes and single-family homes both fell, so a shock to the repeal cities as a whole fits best. The matched design passed its single-family placebo in 38/39, so the matching is doing real work.
  - **The comparison group decides the pre-trend again.** Against national places the pre-trend passes here; against matched places it failed (P3).
  - **Leave-one-metro-out:** all non-metro places form one "none" group.
  - **Weighting matters again.** The equal-weight estimate is −1.50, with an interval that includes 0.
  - **Timing.** The runs started around 08:07, and the script was committed at 08:21:59. It was not edited between the run and the commit, but git can't show that.

## Dose-coding pilot (15 of the 76; coding only, no outcomes read)

- **File:** `reference/parking_dose_pilot.csv`, with sample draw `scripts/draw_parking_dose_pilot.py`.
- **After the repeal:** 0 required spaces in all 15. The variation is all on the "before" side.
- **Before, for a 20-unit building** (spaces required):
  - 20 in 7 places: the five Oregon cities (state cap of 1 per unit from 2022-12-31), Cambridge and South Bend;
  - St. Paul 25, Bridgeport 33, Austin 35, Bandera 45;
  - uncodable in 4 (Saranac Lake, Kingston, Ecorse, Rogers): the old codes sit behind blocked code sites or aren't public.
  - Spaces per home before ranged from 1.0 to 2.25.
- **Oregon.** All five took OAR 660-012-0420(1), repealing all mandates. Their "day before" is the state cap (4 / 20 / 100 spaces). Local tables would have given more, for example 30 and 150 in Central Point and Albany; those figures are in the notes.
- **Scope.** 13 repeals were citywide. Two were partial:
  - Kingston: about 86–92% of apartment land, from its acreage-by-zone table.
  - South Bend: the study unit includes unincorporated county land, which kept 1 per unit.
- **Many places were already partly exempt before the repeal:** Oregon's transit areas, Cambridge's affordable overlay, downtown districts. This was not measured on maps.
- **Effort.** About 1 hour of AI time (median 3 minutes per place). A person would likely need 30–90 minutes per place.
- **Coding all 76.** It looks worthwhile at roughly 4–8 hours, plus clerk requests for about a quarter of places. A yes/no "repealed" flag hides a 2.25-fold spread in what was required before, and large existing exemptions.
- **Sources were second-hand for some places:** Austin (2015 amending ordinance), Bridgeport (third-party table), Bandera (earlier read) and Beaverton (2016 table).
- **Audit fixes to the pilot file:**
  - **Oregon rows.** Each now has three fields:
    - the local table during the before window (20 units: Central Point and Albany 30, Beaverton 28; 100 units: 150, 150 and 138);
    - the day-before state cap (20);
    - the share of apartment land already at 0 under OAR 660-012-0440, not measured on maps (Albany staff say "most" of the city).
    Coding the "before" as the state cap is the rule for all Oregon rows, which is why Beaverton was switched to it.
  - **Bedroom rule.** Bedroom-based schedules assume half 1-bedroom and half 2-bedroom units. This choice matters: it moves Austin's 20-unit figure between 30 and 40.
  - **New field.** A "share where the requirement changed" field sits beside "share covered", naming the exempt areas (downtown, transit, Austin's CBD/DMU and urban core). It is not measured on maps.
- **Waiting on Ryan:** whether to code all 76 places, and any clerk requests.

## Test 40: power and coverage simulation

- **Design.** 200 simulations. Each gives 75 never-repealed places fake repeal years, matches them to comparison pools as in the main estimate, and injects extra permits sized to Wisconsin gains.
  - The interval is 90%, from 1,000 county-cluster resamples.
  - The shift is added per place inside every resample, so the shortcut is exact.
  - Simulation error is about ±2 points on coverage and ±3.5 on power near 50%.

| Injected Wisconsin gain, 2027–31 | Constant | Ramp | Early then fade |
| --- | --- | --- | --- |
| 0 (false-positive rate; nominal 10%) | 16% | 16% | 16% |
| 5,000 homes (power) | 11% | 9% | 11% |
| 10,000 homes | 16% | 11% | 14% |
| 20,000 homes | 36% | 20% | 30% |

- **Coverage of the true effect:** 84% (nominal 90%) in every cell.
- **Mean 90% width:** 4.9 permits per 1,000 existing homes a year. This matches the spread of the 20,000 placebo sets (−2.28 to +2.64, width 4.9).
- **Reading.** The main comparison cannot reliably detect even a gain the size of the current high line. A true gain of about 20,000 homes would show up as "measurable" only about a third of the time. Its intervals are also somewhat too narrow (84% coverage, 16% false positives). So "no measurable change" across the parking tests means the data cannot tell, not that the effect is zero. This supports keeping a wide two-sided range centred on 0.
- **Audit notes:**
  - **One coverage check, not twelve.** The shift moves each resample and the truth together, so the 84% is a single check.
  - **The intervals are too narrow.** The main bootstrap intervals are about 17% too narrow (roughly 10–25% given simulation error).
  - **The tool's lines don't need widening.** They come from placebo percentiles, which already carry the true spread.
  - **The How sure intervals are narrow.** The bootstrap intervals on How sure (−3.47 to +1.43, and the AQ-076 row) are narrow. Any change is Ryan's call.
  - **Timing.** The run started around 08:07, and the script was committed at 08:21:59. It was not edited in between, but git can't show that (same as test 41).

## Test 43: do Madison's minimums bind? (project records 2015–2022)

**Status: spot-checked, 5 of 5 correct.** Ryan checked all 5 seeded rows against the staff reports on 2026-11-03:

| File | Required | Proposed |
| --- | --- | --- |
| 45249 | 44 homes + 13 commercial = 57 | 43 |
| 67515 | 72 | 85 |
| 67284 | 41 | 62 |
| 58489 | 59 | 70 |
| 62084 | 11 homes + 20 commercial = 31 | 25 |

All match the hand-read values.

- ***Post hoc*, prompted by that check: mixed-use projects against the homes-only minimum.** The 15 mixed-use projects come out 7 above, 2 at and 6 below. All 30 together come out 20 above, 4 at and 6 below. For example, file 45249 has 43 stalls for 44 homes, which is at the homes minimum, but below the combined figure. Either way, the reading holds: most projects sit above the minimum, with little bunching at it.
- **Where the rule did bind.** 6 of the 30 projects, all mixed-use, went below even the homes-only minimum through reductions or shared parking: for example, 0 stalls for 75 homes, and 14 for 24. For those projects the rule was binding enough to seek relief. So the reading is "mostly didn't bind, but bound for some mixed-use projects", not simply "didn't bind".
- **Residential-only vs mixed-use read differently** (Ryan, 2026-11-03).
  - **Residential-only (15):** 13 above, 2 at, 0 below. The rule did not bind.
  - **Mixed-use (15):** 11 below the combined requirement. Against the homes-only rule, 7 above, 2 at, 6 below.
  - **Reading (*post hoc*, Madison only, 30 projects).** Residential-only projects mostly sat above the minimum. Six of the 15 mixed-use projects went below even the homes-only rule.
  - **The commercial requirement rarely bound** (corrected after the audit). 12 of the 15 mixed-use projects have a known commercial requirement, and in 11 of them the proposed stalls covered the commercial part alone; the exception is file 62082, with 0 stalls. So the part that bound looks like the homes part, which a housing-only repeal removes.
  - **For the model.** Most evidence repeals covered all uses, while the Wisconsin law covers housing only. In these records the remaining commercial requirement rarely bound, so the difference likely matters little.
  - **Limits.** One city, and only discretionary projects.
  - **Competing explanation (Ryan).** These projects needed a public hearing, so residential builders may add parking to answer neighbours' objections. Commercial and mixed-use projects face less organised opposition. If so, parking above the minimum is partly the price of approval, not market demand. A state repeal would remove the legal floor but not that pressure, and would matter more where projects are approved by right. A possible check: code whether staff reports or public comments raised parking for the 30 projects. By-right projects aren't in these records.

- **Projects.**
  - 395 files (2+ homes; conditional use, planned development and site plan) became 287 projects.
  - Coded in random order until 30 had a positive minimum and both numbers: 116 coded.
  - The other 86 lacked a staff report, had no code minimum (planned development, Central Area, or a no-minimum district), or were not housing.
- **Parser check: failed.** 36 of 50 were correct (72%; the bar was 45). Every project was then hand-read from its PDF.

| Group (share of projects) | At the minimum (±0.05 per home) | 0.05–0.10 above | Above | Below | Median proposed spaces per home |
| --- | --- | --- | --- | --- | --- |
| All 30 | 3 (10%; 90%: 3–20%) | 0 | 16 (53%) | 11 (37%) | 1.24 |
| 15 not mixed-use | 2 (13%) | 0 | 13 (87%) | 0 | 1.44 |

- **Lead result, residential-only projects:** 13 of 15 above the minimum, 2 at, 0 below.
- **Reading: no bunching at the minimum.**
  - Among residential-only projects, 13 of 15 proposed more than the minimum, a median of 1.44 spaces per home against a minimum of about 1.
  - All 11 "below" projects are mixed-use, compared with combined requirements.
  - Projects with no minimum also built parking: a median of 0.76 per home in the Central Area and 1.97 in other no-minimum districts.
  - So in these large Madison projects, the 1-per-home minimum mostly did not bind. That fits the national result of no measurable change.
- **Caveats:**
  - Only conditional-use and planned-development projects (large, discretionary); by-right projects are missing.
  - The numbers are proposed, not built.
  - n = 15 residential-only.
  - 10 of 30 are from 2020.
  - The code text could not be verified (Municode refused automated access).
  - "Location only" two-family rules were excluded.
- **Audit notes:**
  - **The minimum is the staff table's Required cell,** because the code text could not be read (Municode refused automated access).
  - **"Hand-read" means Claude read each PDF.** No check of that read is reported. Before the result is cited, a person should spot-check 5 of the 30 rows, drawn with seed 20261104: Legistar files 45249 (2016), 67515 (2021), 67284 (2021), 58489 (2019) and 62084 (2020).
  - **The 11 "below" projects are mixed-use with shared parking,** so they may not be variances. The residential-only group leads for that reason.
  - **Don't compare the medians as an effect.** The 1.97 median in no-minimum districts against 1.44 is likely a difference of location, not of rules.
  - **Consistent with, but not a confirmation of,** the national result, given test 40's low power.
  - **Limit.** Bunching can't see projects that never applied because the minimum made them unworkable.
  - **The script came in the same commit as the results.**
- **Files:**
  - `scripts/run_parking_t43_madison.py`;
  - `reference/parking_t43_madison.csv`, `parking_t43_projects.csv` (id = Legistar file number; no addresses), and `parking_t43_parser_check.csv`.

## Test 44: does the old single-family minimum change the single-family effect?

- **Groups.** By the old single-family minimum: high = 2.0 spaces per house (29 places); low = 1.0 or less (19). The groups differ by city type, as `reference/parking_t44_groups.csv` shows: high is smaller and later on average.
- **Unit.** 1-unit homes permitted per 1,000 existing homes a year, as high minus low.

| Version | Estimate (90%; 97.5%) | MDE |
| --- | --- | --- |
| Main, home-weighted | −0.80 (−2.78 to +0.94; −3.33 to +1.40) | 1.81 |
| Equal-weight | −3.39 (−6.11 to −1.02) | 2.58 |
| Without Austin | +0.32 (−1.40 to +1.30) | 1.41 |
| Without Raleigh | −1.49 (−3.11 to +0.35) | 1.72 |
| High-confidence codes only | +0.00 (−2.77 to +1.40) | 2.05 |
| Backtest (years −2, −1 vs −5 to −3) | −0.83 (−1.91 to +0.36): passes | — |
| Same contrast, 5+ unit homes | +0.76 (−3.68 to +4.61) | — |

- **Reading: not supported.** Places with a higher old single-family minimum did not gain more single-family homes after repeal.
- **The equal-weight result points the wrong way.** At −3.39 it excludes 0 even at 97.5% (−7.43 to −0.39). It likely reflects city type: the high group is smaller and later, with short Oregon after-windows. The home-weighted sign also flips without Austin (+0.32).
- **The placebo use stands as before,** but test 44 can't rule out a single-family effect smaller than its MDE (about 1.8 per 1,000 homes a year).
- **Context.** Detached houses usually meet 2 spaces anyway; townhouses are where the rule more likely bound. Townhouses can't be separated in the permit data.

## Exempt-share pilot (15 places; coding only)

- **File:** `reference/parking_dose_exempt_pilot.csv`.
- **Share of apartment-eligible land already exempt the day before repeal.** Exempt means zero, or 50% or less of the base rate. Measured by 25 m grid sampling on current zoning, with documented reversals.
  - **10 places measured by GIS:**
    - Albany 0.95, Central Point 0.75, King City 0.72, Beaverton 0.65, Springfield 0.56;
    - Austin 0.02 (main; 0.51 upper-bound sensitivity, which counts a corridor ordinance a court voided five weeks after repeal);
    - South Bend 0.50 (city only), St. Paul 0.17, Bridgeport 0.12, Cambridge 0.05.
  - Bandera: "none", by text.
  - Kingston: "none found", by text. The 2005 Mixed Use Overlay text (read in full from the Pace Land Use Law Center copy) gives no parking relief. The old ratio table is still unread.
  - 3 not found (Saranac Lake, Ecorse, Rogers): the old code is not online or is blocked. Leads are noted in the file: Saranac Lake's waterfront plan recommended a village-wide minimum; Rogers' downtown exemptions covered non-residential uses only, per the Parking Reform Network.
- **The median share "on the day before repeal" is 0.53 overall but 0.12 outside Oregon** (the 5 places measured by GIS; counting Bandera's and Kingston's text "none found" as 0 gives 0.05, the median of 7; "none found" is not a measured 0, since Kingston's ratio table is unread). Oregon's high shares come from the state transit rule (OAR 660-012-0440), which started 2022-12-31. Most of Oregon's before window ran without it.
  - **Before-window, local exemptions only:** Albany 0.04, Central Point 0, King City 0. Springfield and Beaverton have no public map of their local districts (Beaverton's Regional Center zones over-count at 0.13).
  - **Central Point and King City, two readings of the state rule:** broad 0.75 and 0.72; narrow 0 for both.
  - The grid script is `scripts/run_parking_dose_exempt_grid.py`, and the fetch script is `scripts/fetch_parking_dose_exempt.py`. Layers stay out of git; their sources and terms are listed in `docs/DATA_PROVENANCE.md`. Shipping any layer needs Ryan's OK.
- **Caveats:**
  - Oregon bus frequencies use 2024–26 timetables.
  - South Bend's county part is not measured.
  - Nearly no layers state a licence.
- **Effort.** About 1.9 AI-hours in all. Clerk requests would be needed to finish or firm up 9 places; none were sent.
- **Closed 2026-11-04.** Ryan chose "Stop at the pilot" (17:12 UTC). The 15-place pilot stays as evidence only; it feeds no line and no test. No more map coding and no clerk requests. The last 4 places were tried once more from public sources only.
- **Read.** The dose varies widely: some repeals changed rules on most apartment land, others on little. A dose-weighted test is possible once the 76 are coded, which needs Ryan's decision and some clerk requests.

## Tests 45–46: who the comparison places are (2026-11-04; lock in CAUSAL_FRAMEWORK_PLAN.md, commit 20fea8f6)

Script `scripts/run_parking_t45_t46.py`, committed before its first run (20cef909). The first run stopped at the rebuild step on a column-name bug, before any new number was computed; the fix (South Bend's scale) also added a check of each comparison change. The rebuild matched all 76 stored effects and comparison changes to 1e-4. Units: permits per 1,000 existing homes a year; averages weighted by homes × after-years; 90% ranges from 2,000 place resamples (seed 20261104).

**Answers to Ryan's two direct questions.**
- **TOD-upzoned places are not dropped from the main comparison pools.** The main pools leave out only the benchmark repeal list (303 matched cities). The 38 TOD upzoned places were left out of pools only in test E2 (the 2×2), so that its "neither" group was places that did neither reform.
- **The 9 places that widened the size window** (same state, 1/3–3× population): San Jose, San Francisco, Corvallis, Tigard, Austin, Birmingham, Springfield (OR), Albany (OR) and South Bend. Another 12 left the state for the Census division (0.5–2×): Raleigh, Minneapolis, Lexington, St. Paul, Anchorage, Durham, Salem, Eugene, Bend, Beaverton, Portland (ME) and Burlington.

### Test 45: strict pools (no parking-reform record at all)

- **Leaving out every city with any record** (removal or reduction, any rating) matches 4,591 cities. That removes 35% of comparison-pool places (25 a pool on average). 37 of the 76 move to a wider window, and 6 have no strict pool at all: Austin, Minneapolis, San Francisco, San Jose, Sacramento and Birmingham. These 6 hold 39% of the weight.

| Version | Places | Average | 90% range |
| --- | --- | --- | --- |
| Main | 76 | −1.14 | −3.39 to +1.38 |
| Main, same 70 places | 70 | +1.38 | −0.39 to +3.31 |
| Strict | 70 | +2.43 | +0.73 to +4.03 |
| Main, 67 places with a strict pool of 5+ (beside, not locked) | 67 | +1.50 | — |
| Strict, pool of 5+ (beside, not locked) | 67 | +1.07 | −0.21 to +2.37 |

- **Locked reading: not consistent with the main.** The strict average (+2.43) lies outside the main's 90% range.
- **Why (a reading made after the result, not the locked rule):** about 70% of the gap comes from the set change. Dropping the 6 big cities moves the main from −1.14 to +1.38. The pool rule adds the rest, +1.38 to +2.43, which is inside the main's same-set range. With pools of 5+, strict is below the main (+1.07 vs +1.50), so the pool rule has no consistent direction.
- **Caveats:**
  - 3 strict pools have 1 or 2 places: Raleigh (2 places, +7.04 to +9.34), and the 1-place pools of Lexington (−5.08 to +5.09) and St. Paul (−2.22 to +2.84).
  - **Oregon.** In the main, Oregon comparison cities were under the same state rules from 2022-12-31, so the main Oregon effects measure the local repeal beyond the state rule. Strict moves 14 of 16 Oregon places to other Pacific states. Their mean falls from +1.33 to −2.66 (median +2.09 to −0.73; e.g. West Linn +9.5 to +0.7, Milwaukie −0.3 to −8.1). So strict asks a different question for Oregon: the state rule plus local repeal, against places with neither.
  - Most of the 4,591 records are "weaker" reforms (small cuts or commercial-only), so the strict pool also drops places whose housing rules did not change.

### Test 46: comparison-place influence

- **Pools saved:** `reference/parking_t46_pools.csv` (one row per repeal place and comparison place, with its share of pool homes).
- **Reuse:** the most-used comparison places are Oregon cities (Forest Grove, Woodburn, Happy Valley, Redmond, McMinnville, Newberg, Oregon City: 10 repeal places each, 2 of them outliers each), because the Oregon repeal places share one state pool.
- **Not independent:** 7 Oregon comparison cities are each shared by 10 repeal places, so those Oregon effects move together. The statewide effect of that is small (each moves the average by 0.04 or less).
- **Leave one out** (drop a comparison place from every pool it is in, no re-matching): no single place moves the average by more than 0.25. Top 10 by size of change (`reference/parking_t46_loo_top10.csv`):

| Comparison place | Used by | Outliers among them | Average without it | Change |
| --- | --- | --- | --- | --- |
| San Diego | 2 | 0 | −0.89 | +0.25 |
| Washington, DC | 1 | 0 | −1.33 | −0.19 |
| Oakland | 4 | 0 | −1.32 | −0.18 |
| Atlanta | 2 | 0 | −0.97 | +0.18 |
| Irvine | 5 | 0 | −1.28 | −0.13 |
| San Antonio | 1 | 1 | −1.24 | −0.10 |
| Miami | 2 | 0 | −1.05 | +0.09 |
| Omaha | 2 | 1 | −1.05 | +0.09 |
| Kansas City, MO | 2 | 1 | −1.22 | −0.08 |
| Fort Worth | 1 | 1 | −1.08 | +0.06 |

- **Regression (reading only, 76 places, robust errors, 90% intervals):** pool size, a widened window and the largest comparison place's share of pool homes do not predict being an outlier or the size of the effect. All their intervals include 0.
  - The size of the comparison change does predict both: +0.05 outlier probability per permit (+0.02 to +0.08), and +1.06 in |effect| (+0.47 to +1.65). This is partly mechanical, because the comparison change is part of each effect.
- **Correlations:** each effect tracks the place's own change (r 0.89) far more than its comparison change (r −0.16).
- **Reading:** no comparison place, or kind of pool, drives the outliers. Outliers come mostly from the repeal places' own swings.

## Test 47: big-city vs same-state comparison places (2026-11-04; lock 4446b84a, script committed before its run)

- **Targets:** 71 never-repealed US places with 250,000+ people (72 locked; Nashville-Davidson dropped because the current rule found no pool even at the division and 1/3–3×), 5 fake repeal years each (2017–2021), 355 target-years. True effect 0. Units: permits per 1,000 existing homes a year.

| Score (big-city minus current; below 0 favours big-city) | Equal weight | Home-weighted |
| --- | --- | --- |
| Size of fake-repeal effect: current 3.81 / 2.18, big-city 3.68 / 2.11 | −0.13 (−0.48 to +0.19) | −0.07 (−0.29 to +0.14) |
| Year-by-year fit (RMSE of the gap): current 3.97 / 2.42, big-city 3.81 / 2.26 | −0.16 (−0.34 to +0.01) | −0.16 (−0.31 to −0.06) |

- **Locked verdict: no clear difference**, under both weightings. Big-city pools track slightly better (fit errors about 4–7% lower, clear only with home weights), but fake-repeal estimates are no closer to 0. The spread of fake effects is about the same (SD 5.23 current, 5.16 big-city).
- **Follow-up not run:** the locked rerun of the 76 with big-city pools needed a "better" verdict.
- **Pool rule vs Ryan's ask:** Ryan asked for no-record pools; the lock used the main list, because a no-record big-city pool would be too small. Test 45 covers the no-record question.
- **Post hoc reading (after the result, not locked):** only 33 of 71 targets had same-state current pools; 38 already used the Census division. For same-state targets the big-city rule did better (|fake effect| −0.44, RMSE −0.25); for division targets, |fake effect| +0.14 and RMSE −0.08. Pool sizes differ (median 7 current vs 68 big-city), so part of the lower RMSE may come from pool size. This does not change the verdict; a new locked test with a pool-size control would be Ryan's call.
- **Reading:** Ryan's idea gets weak support on fit, but not enough to change how the main estimate is built. Big cities' permits swing a lot either way, about ±5 per 1,000 homes on a fake repeal, so no comparison rule removes much of that noise.

## Method 2 results (2026-11-04; lock in CAUSAL_FRAMEWORK_PLAN.md, "Method 2")

Units: permits per 1,000 existing homes a year; Wisconsin homes over 2027–2031 = rate × 13,343. 90% ranges are place bootstraps (2,000 draws, seed 20261104). Method 2's own coverage check: D under the target-state mix covered 0 in 90.0% of fake sets (87.5% on the common cases).

**Order of steps.**
1. Stage 1 bake-off (pick committed, d65040cb).
2. Audit rescore on common cases, then a fair rescore with C falling back to B (both post hoc).
3. B+D side check under Ryan's tie rule (written 9fbad5d7, before B+D was seen).
4. Stage 2 was run after the stage 1 pick was committed, and read only after the B+D decision.

**Heat method: D (10-year before window).**

| Version (random-effects scoring) | A | B | C | D | B+D |
| --- | --- | --- | --- | --- | --- |
| Stage 1 as locked (MAE / coverage) | 0.857 / 0.88 | 0.850 / 0.86 | 0.906 / 0.875 | **0.849 / 0.915** | — |
| Common cases (30 dropped) | 0.927 / 0.90 | 0.918 / 0.87 | 0.906 / 0.875 | 0.915 / 0.91 | 0.910 / 0.90 |
| C falls back to B (all cases) | 0.857 / 0.88 | 0.850 / 0.86 | 0.835 / 0.87 | 0.849 / 0.915 | — |

- **All candidates are within about 2% of each other** in every version, which is inside the noise.
- **Ryan's calls:** C out; "either D or combo B+D"; D wins ties.
- **B+D vs D:** B+D's MAE is 0.6% lower than D's. That is below the 5% bar, so D stands. The margin was committed at 20:01:22 UTC (9fbad5d7); the B+D scores were written at 20:06 UTC. The margin did not decide anything here.
- **C:** under the fair rescore, C scored best (within about 2%). Ryan chose D: "I dont think C looks that much better after the rescore. It's either D or combo B+D" (about 20:00 UTC). That quote refers to the common-case rescore (C 0.906 vs D 0.915); the fair rescore was written at 20:06 UTC.

**Main weight: target-state mix (weight test).** Leave one state out over 10 states; mean absolute error of the held-out state's mean:

| Weighting | Error (equal per state) |
| --- | --- |
| Target-state mix | **3.14** |
| Random effects | 3.42 |
| Equal | 3.47 |
| Square root | 3.61 |
| Homes | 4.01 |

- Target-state mix had the lowest error outright; the tie rule was not needed.
- The errors (3.1 to 4.0 permits per 1,000 existing homes a year, per state) are several times the size of any estimate, so the weightings differ by less than the noise.
- Effective number of places: Wisconsin 30.9, Tennessee 50.9. No empty cells.

**Method 2 result (D, target-state mix aimed at Wisconsin):**
- **Rate:** −0.53 (−2.36 to +0.89).
- **Wisconsin:** −7,012 homes over 2027–2031, 90% range −31,512 to +11,845.
- **The sign depends on the weighting:** −7,012 under the mix, but +8,800 to +11,500 under random effects, square root or equal weights.

| D under each weighting | Rate (90%) | Wisconsin homes (90%) |
| --- | --- | --- |
| Target-state mix (main) | −0.53 (−2.36 to +0.89) | −7,012 (−31,512 to +11,845) |
| Random effects | +0.86 (−0.31 to +1.95) | +11,501 (−4,080 to +25,992) |
| Square root | +0.66 (−0.71 to +2.25) | +8,765 (−9,444 to +30,071) |
| Homes | −0.03 (−1.81 to +2.37) | −416 (−24,131 to +31,606) |
| Equal | +0.68 (−1.48 to +2.06) | +9,089 (−19,690 to +27,527) |

- **Switch-backs (D, target-state mix):** each item 2–6 switched back alone gives −0.32 to −1.36. Turning off winsorising has the biggest pull (−1.36). Dropping the 2 shock-flagged repeal places gives −0.46.
- **Backtest (D, target-state mix):** −0.57 (−2.67 to +0.33). The range includes 0, so it passes. Under home and square-root weights the backtest fails (ranges above 0).
- **Side line, B+D (post hoc), random effects:** +0.73 (−0.45 to +1.81), Wisconsin +9,690.
- **Big cities and C:** 11 real repeal places used synthetic control under C, and none failed.

**Reading.**
- Method 2 again finds no measurable effect: every main range includes 0.
- The sign depends on the weighting. Weighting toward Wisconsin's mix of places leans negative; random-effects and equal weights lean positive.
- **The replacement bar, two readings (Ryan's choice).** The method-2 range (−31,512 to +11,845) is 43,357 wide. The current 90% range (−45,853 to +19,818) is 65,671 wide.
  - **As locked, method 2 fails.** The bar is 26,289, which is 75% of 35,052. But 35,052 was the old span from the measured average up to the placebo 95th percentile, not a 90% width.
  - **Like for like, method 2 passes.** 25% narrower than today's 90% width is 49,253 or less.
  - Changing the bar now would be post hoc, so the choice is Ryan's. Until he decides, method 2 is evidence beside the current lines, and any tool change needs his OK.
