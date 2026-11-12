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
- **Ryan's choice of bar (20:44 UTC):** "The like for like bar makes more sense." Method 2's 90% width, 43,357, is below 49,253 (25% narrower than today's 65,671), so it passes the bar as Ryan chose it. This bar was chosen after the result was seen (post hoc). Any tool change still needs Ryan's OK.
- **Why the sign depends on the weighting (method 2, D; effects winsorised; equal weight within band).**

| Size band | Places | Mean effect |
| --- | --- | --- |
| Under 10,000 people | 11 | −1.07 |
| 10,000–50,000 | 24 | −0.20 |
| 50,000–250,000 | 30 | +2.52 |
| 250,000+ | 11 | −0.66 (home-weighted −1.61) |

  - Wisconsin's eligible homes are about 37% in places under 10,000, 18% in places of 250,000+, and 12.5% in the 50,000–250,000 band. So the target-state mix leans on the bands that fall.
  - Random-effects, equal and square-root weights lean on the 30 mid-size places, which rise.
- **Double-dip, named.** Crowding, density, town age and the pre-repeal permit rate were added to the method-2 matching partly because the effect-size trait ranking flagged them. That ranking used the same 76 effects, so this is a mild double-dip. In principle, matching should use traits that predict building without repeal, ranked on comparison places only. The target-state mix should use traits that change the size of the effect. This was not done here and is noted as context.

## Method 2, corrected run (2026-11-04; correction lock in CAUSAL_FRAMEWORK_PLAN.md; provisional go by the learning thread, 21:02 UTC, under Ryan's 21:01 UTC delegation)

**Data fixes.**
- **Connecticut:** joined on state + county-subdivision code. "Not defined" placeholders (code 00000) were dropped; no real unit was dropped.
- **Wisconsin cells:** built on the tool's 2,668,677 eligible homes.
- **Missing-data table:** committed before stage 1. Connecticut is now at 0% missing, and the worst state is 2.1%.

**Heat method.**
- **Stage 1:** the corrected stage 1 scored A 0.900 / 0.88, B 0.873 / 0.855, C 0.921 / 0.865, D 0.917 / 0.86 (random-effects MAE / coverage).
- **Pick:** under the correction lock's rule (D or B+D; D wins ties at 5%; C out), B+D scored 0.895 / 0.885. That is 2.4% below D, so **D stands**.
- **Code gap:** stage 1's code had picked B by lowest MAE across A–D, which is not the lock's rule. This was fixed with `scripts/pick_parking_method2_corrected.py`. D reproduced exactly.

**Weight test (corrected).**

| Weighting | Error |
| --- | --- |
| Target-state mix | **3.065** |
| Random effects | 3.346 |
| Equal | 3.394 |
| Square root | 3.499 |
| Homes | 3.864 |

- Errors are permits per 1,000 existing homes a year, per state.
- The mix wins outright. Wisconsin's effective number of places is 19.6.

**Corrected result (D, target-state mix, Wisconsin):**
- **Rate:** −0.77 (−2.78 to +0.43).
- **Wisconsin:** −10,223 homes over 2027–2031 (−37,046 to +5,760).
- **Range width:** 42,806. That is under Ryan's like-for-like bar (49,253, post hoc) and over the locked bar (26,289).

| D under each weighting | Wisconsin homes (90%) |
| --- | --- |
| Target-state mix (main) | −10,223 (−37,046 to +5,760) |
| Random effects | +11,519 (−4,006 to +26,043) |
| Square root | +9,519 (−7,823 to +30,710) |
| Homes | +1,390 (−20,582 to +31,647) |
| Equal | +9,153 (−19,876 to +27,719) |

- **Switch-backs (mix):** −0.47 to −1.81. Turning off winsorising pulls most (−1.81).
- **Dropping the 2 shock-flagged repeal places:** −0.72.
- **Locked sensitivity, missing-trait candidates ineligible (mix):** −0.72, Wisconsin −9,546 (−36,361 to +6,240).
- **Backtest (mix):** −0.8154 (−3.387 to +0.0004), against the main −0.7661. The backtest has the same sign and about the same size as the main result, and it fails under square-root and home weights. So the mix's negative lean cannot be told apart from what the mix shows in years with no repeal.
- **San Francisco:** now matched to 10 dense places such as Weehawken, Mount Vernon and North Bergen, at step 5; 3 still lack density or crowding. It is no longer matched to rural Connecticut towns.

**City-size weighting test (post hoc, corrected data).** Leave-one-state-out error:

| Version | Error | Gap vs 4 bands (90%) | Wisconsin homes |
| --- | --- | --- | --- |
| (i) 4 bands (main) | 3.065 | — | −10,223 |
| (ii) 3 bands at terciles | 3.782 | +0.72 (−0.12 to +1.52) | −16,040 |
| (iii) smooth line on log population, edge-held | 2.635 | −0.43 (−1.05 to +0.22) | +33,909 |
| (iv) crowding terciles | 2.129 | −0.94 (−1.81 to +0.06) | −31,354 |

- **Verdict:** none beats the 4 bands by the rule (more than 10% lower and the range excludes 0), so the 4 bands stay.
- **Crowding came close:** 30.6% lower error, but its range (−1.811 to +0.055) includes 0.
- **Smooth line:** 14.0% lower error; its range also includes 0.
- **Spread:** the Wisconsin figure under these versions runs from −31,354 to +33,909. How the evidence is mapped onto Wisconsin is itself a large source of uncertainty, and it is not in the 90% range.

## Method 3: prognostic-score matching (2026-11-04; lock "Method 3", cleared by the audit 21:10/21:45/21:50 UTC; provisional go by the learning thread under Ryan's 21:01 UTC delegation; post hoc in origin)

**Score.**
- **Data:** 82 features, all measured before each event year: TOD's ACS traits (built-year traits limited to pre-2000 bands), the parking traits, permit history, size, 2010 density and town age. Method 2's town age covers 1990–2009, so "pre-2000 only" applies to the TOD traits; all are within the lock's pre-2010 rule.
- **Halves:** never-repealed places split 50/50. Half A has 6,339 places and 55,633 place-years; half B has 6,340 and 55,568.
- **Models chosen:** A chose gradient boosting (grouped CV error 10.10 vs lasso 10.13). B chose lasso (5.88 vs 6.31). A seems to hold more extreme small places.
- **Check on B:** the A model's error is 8.43 vs 9.46 for a plain average, 11.0% better, so it passes.
- **Mirror (B on A, reported only):** 22.0% better.

**Bake-off in B** (5,828 fake cases, pools from B only, random-effects scoring):

| Matching | MAE | Coverage |
| --- | --- | --- |
| Prognostic (P) | 0.877 | 0.92 |
| Today's (D) | 0.886 | 0.90 |

- P is 1.1% better, under the 5% margin, so today's matching stands.

**Real run.** The picked method (D) reproduces corrected method 2 exactly: mix −0.7661, Wisconsin −10,223 (−37,046 to +5,760), with the same weight-test errors (mix wins at 3.065) and the same size test (4 bands stay).

**Prognostic matching, evidence only:**

| Weighting | Rate (90%) | Wisconsin homes (90%) |
| --- | --- | --- |
| Target-state mix | +0.03 (−1.33 to +1.31) | +369 (−17,751 to +17,540) |
| Random effects | +1.15 (+0.07 to +2.25) | +15,400 (+980 to +30,024) |
| Square root | +0.82 (−0.67 to +2.58) | +10,950 |
| Homes | −0.31 (−2.40 to +2.43) | −4,191 |
| Equal | +1.35 (+0.24 to +2.56) | +18,009 (+3,227 to +34,144) |

**Reading.**
- The prognostic score does predict building without repeal (11% better than an average). But matching on it did not beat today's matching on fake repeals, so the main result is unchanged.
- **Comparison choice moves Wisconsin's mix result:** −10,223 under today's matching vs +369 under prognostic matching. That is one more sign that mapping and comparison choices move Wisconsin's number by more than the 90% range shows.
- Under random-effects and equal weights, prognostic matching's range excludes 0 on the positive side. This is evidence only and was not picked.
- **Beside the current tool lines.** The tool shows −15,234 / 0 / +19,818, and its 90% range under the uniform display spec is −45,853 to +19,818. Method 2/3 (D, mix) gives −10,223 (−37,046 to +5,760); prognostic matching gives +369 (−17,751 to +17,540). Any change to the tool lines needs Ryan's own OK, not a provisional one.
- **Double-dip and origin.** The choice to try method 3 is post hoc in origin, because method 2's real results had been seen. Method 2's matching traits were partly chosen from the effect-size ranking (the double-dip noted above). Method 3's score was fitted on never-repealed places only, which avoids that for the score itself.

## Method 3b (2026-11-05; lock "Method 3b", cleared by the audit 03:16 UTC; provisional go by the learning thread 03:14 UTC under Ryan's 21:01 UTC delegation; post hoc in origin)

**Stopped at the score check, as locked.**
- The score predicts each never-repealed place's change in permit rate (after mean minus D's 10-year before mean).
- Fitted on half A (54,167 place-years) and checked on half B (53,973). Its mean absolute error on B is 6.62, against 6.59 for a plain average of A's change. That is 0.5% worse, short of the required 5% better.
- Boosting's grouped-CV choice was a single iteration, so it found almost nothing to learn.

**Reading.** Building levels are predictable (method 3's score beat an average by 11%), but the change in building after a given year is not. That change is what the effect measures. No fake-repeal bake-off was run, and D (corrected method 2) stands.
- **Loss note.** The models fit squared error but are judged on mean absolute error, and the change has heavy tails. A retry with another loss would need a new lock and Ryan's call; none is proposed here.
- **Across methods.** None of the methods tested on fake repeals beat D: the method-2 candidates, method 3's prognostic matching, and 3b, which stopped before its bake-off. The gap between D (−10,223) and prognostic matching (+369) under the Wisconsin mix is the best sign of how much the comparison choice moves Wisconsin's number.

## Test 49: does the effect build, hold or fade? (2026-11-05; lock "Test 49", cleared by the audit; Ryan's ask is the go)

Method D on corrected method-2 data, with one pool per case held fixed across years. Units: permits per 1,000 pre-event existing homes a year, Wisconsin homes = rate × 13,343. The first run stopped in the long set on an empty bootstrap year; a guard was added, then everything was rerun. No case was dropped for a small pool. Outputs: `reference/parking_t49_*.csv`; per-place, per-year export `reference/parking_byyear_place_effects.csv`.

**Main reading: target-state mix (90% ranges).**

| After-year | 38-place set | Long set (15 places; fewer after year 5) |
| --- | --- | --- |
| 0 (repeal year, context) | +0.88 (−0.53 to +4.58) | +0.60 (−1.60 to +10.10) |
| 1 | +0.02 (−1.42 to +2.72) | +0.20 (−2.07 to +7.11) |
| 2 | −1.52 (−3.69 to +2.33) | −0.24 (−4.07 to +12.56) |
| 3 | −0.98 (−3.16 to +0.86) | −1.36 (−4.01 to +2.40) |
| 4 | — | −1.47 (−6.55 to +11.05) |
| 5 | — | −2.68 (−7.03 to +9.79) |
| 6 (11 places) | — | +5.87 (−4.50 to +28.73) |
| 7 (6 places) | — | −0.88 (−2.18 to +7.41) |
| 8 (3 places) | — | +0.54 |
| 9 (1 place) | — | −0.97 |

**Slopes over the balanced years.**

| Check, years | Mix | Random effects | Equal |
| --- | --- | --- | --- |
| 38 places, 1–3 | −0.50 (−2.13 to +0.24) | −0.54 (−1.30 to +0.23) | −1.01 (−2.40 to +0.18) |
| 15 places, 1–5 | −0.70 (−1.81 to +0.52) | **−0.60 (−1.09 to −0.20)** | −1.06 (−1.77 to +1.02) |
| Long-set leads, last 3 before-years (12 places) | −0.61 (−5.93 to +1.08) | **−2.11 (−5.43 to −0.15)** | −2.50 (−6.49 to +0.01) |
| 38-place leads, last 3 before-years (34 places) | −0.48 (−2.85 to +0.57) | +0.12 (−1.89 to +1.12) | −0.37 (−2.23 to +0.71) |

**Reading (neutral rule).**
- **Main reading:** under the mix, "no clear change over time" in either set.
- **The 38 places already ran below their pools before repeal.** Under the mix, their last three before-years were −0.18 (ey−3), −1.83 (ey−2) and −1.14 (ey−1). That is about as negative as after-years 2–3 (−1.52, −0.98), and consistent with the method-2 mix backtest caveat (−0.82). A negative after-effect already present before repeal is not good evidence that repeal caused it.
- **Random effects, long set:** "changes with time", with the effect drifting downward. But the same places' last three before-years slope downward even more steeply under random effects (−2.11 against −0.60 after). The drift was already under way before repeal. A downward pre-trend also means the before-window mean overstates what would have happened without repeal, which pushes the effect level down too.
- **Chance:** 2 of 12 slopes exclude 0, not far from chance at 90% (about 1 in 10, and the slopes are not independent).
- **Thin data:** 15 places is thin, and years 6+ rest on 11, 6, 3 and 1 places.
- **Consistency check:** the 38 places' years 1–3 average (−1.003) equals corrected method 2's result for the same places exactly, so the fixed long pools match method 2's.

## Reform-type coding for the 15 long-set places (2026-11-05; plan in CAUSAL_FRAMEWORK_PLAN.md; coding committed cf4388cc before any join)

Five helpers coded three places each from public sources, following a written brief: `reference/parking_reform_type_15.csv`, 40 fields, with source URLs and Wayback capture dates. Blocked sites (parkingreform.org, Municode, eCode360, amlegal, Planetizen) are cited, not worked around. This is descriptive only.

**Do approval path and dose vary? Yes, both.**
- **Repeal type:**
  - 11 places are plain full repeals of residential minimums, citywide.
  - Windham: full removal for uses under site plan review (3+ units); its village district keeps 1 per unit for houses and duplexes.
  - Branson: "near". The table was retitled a maximum, but the text still says spaces "shall be provided".
  - Maumee: unclear. The required number is also the maximum, and providing fewer needs administrator discretion.
  - Seabrook: not a residential repeal. Only non-residential minimums were cut; housing never had a number (see the flag below).
- **Old minimum for a 20-unit building:** 16 (Emeryville) to 42.5 (Dunwoody) where found; 20 in San Francisco (Sec. 151 districts), Buffalo, Hudson and Hartford. Not found for 6 places.
- **Approval path for 5+ units after repeal:**
  - by right: Branson, Ecorse, Hartford;
  - mixed by zone or size: San Francisco, Buffalo, Dunwoody, Maumee, Mount Pleasant, Bastrop, Canandaigua;
  - board review with a hearing at the board's discretion: Hudson, Windham, Saranac Lake;
  - design-review hearing: Emeryville;
  - not allowed: Seabrook.
- **Did the repeal change the approval path?**
  - yes: Buffalo (the hearing threshold moved from about $50,000 of project value to 5,000 sq ft);
  - partly: San Francisco, Emeryville, Bastrop, Windham, Mount Pleasant, Saranac Lake, mostly through whole-code rewrites;
  - no: Hudson, Canandaigua, Hartford, Seabrook, Dunwoody, Branson, Maumee;
  - unknown: Ecorse.
- **Small groups:** each group holds 1–7 places, so no group difference is a finding. A test by type needs its own lock.

**Audit corrections (16:30 UTC):** San Francisco's Prop E entry was removed (it came from memory, not a source), and SF's approval-path confidence is now low. The search-summary items for Hudson and Canandaigua are marked as low-confidence inferences. `reference/parking_old_minimums.csv` is updated for Hudson (1 per unit, Wayback) and Emeryville (about 0.80 per unit for 5+ units, 2017 code).

**Sample flags found by the coding:** Canandaigua is a data fix and can be self-approved. Seabrook waits on Ryan. Branson and Maumee are a sensitivity, not a fix. All of them go into one batched rerun, with old and new side by side.
1. **Canandaigua:** the repeal is the Town of Canandaigua's (Local Law 3-2020), but the permit series in the 76 is the City's (BPS key 36|103000, place 12144). The town has its own series (36|103500).
2. **Seabrook:** its 2019 change cut only non-residential minimums, so it is not a residential repeal.
3. **Maumee:** coded "unclear".
4. **Other files to update:** `reference/parking_old_minimums.csv` has Hudson as not found (the old rate is 1 per unit, from a Wayback copy) and Emeryville as 1.75 per unit (the 2017 code says 1 per unit plus guest parking, at 67% of demand).

## Batch rerun after the sample fixes (2026-11-05; lock "Batch rerun after the sample fixes"; Ryan 15:50/15:54 UTC)

**Fixes.**
- Canandaigua is now on the Town's permit series (the City is kept out of the Town's pools).
- Seabrook is removed (not a residential repeal).
- Maumee is removed (a reform, not a repeal; Ryan 15:54 UTC).
- That leaves 74 repeal places.

**How the run was done.** Outputs are in `reference/batch_2026-11-05/`: 22 changed or new files, all under 1 MB, with no lot, address or GIS files. The committed originals feeding the tool are untouched, and the TOD files' SHA-256 hashes match. The run stopped twice, at the method-2 gate and at the interim commit. Each time it was fixed and resumed from that step, without redoing earlier steps. The driver's final status check failed only on a pre-existing untracked local file (parking_acs_crowding.csv), so the last commit was made by hand after the diff and TOD hash checks passed (audit accepted).

**Main estimate (the tool's method: real average with the placebo spread), extra homes in Wisconsin 2027–2031:**

| Version | Low | Measured average | High | Width |
| --- | --- | --- | --- | --- |
| Old (76 places) | −45,853 | −15,234 | +19,818 | 65,671 |
| New (74 places) | −46,268 | −15,380 | +19,649 | 65,918 |
| New, Branson also out (sensitivity) | −46,429 | −15,540 | +19,489 | 65,918 |
| New, Maumee kept in (approximate side run, 75) | −46,265 | −15,376 | +19,653 | 65,918 |

73 of 74 places are matched. Gastonia is again the one place without placebo stand-ins; its trimmed windows never match its stand-ins' after-year count.

**Corrected method 2 on 74 places:**
- **Stage 1:** D 0.859 / 0.91, E (B+D) 0.857 / 0.91, so D wins the tie. The fake sets changed with 74 places, as noted in the lock.
- **Weight test:** mix 3.06 against random effects 3.39 (9.7% lower), which counts as a tie; the mix wins ties, so the outcome is the same.

| D, target-state mix | Rate (90%) | Wisconsin homes (90%) | Width |
| --- | --- | --- | --- |
| Old (76) | −0.77 (−2.78 to +0.43) | −10,223 (−37,046 to +5,760) | 42,806 |
| New (74) | −0.96 (−3.34 to +0.36) | −12,873 (−44,571 to +4,854) | 49,426 |
| New, Branson out (pre-registered sensitivity) | −1.01 | −13,415 (−44,174 to +3,872) | 48,047 |
| New, Maumee in (approximate side run) | −0.98 | −13,127 (−41,802 to +3,688) | 45,489 |

- **Other weightings (new):** random effects +8,780, square root +9,261, homes +1,479, equal +8,270.
- **Like-for-like bar (49,253):** the bar itself is post hoc (Ryan, Nov 4 20:44 UTC). The main 74-place result misses it by 173 homes (width 49,426). Branson out (48,047) is a pre-registered sensitivity (lock item 5) and Maumee in (45,489) is approximate; neither is used to say method 2 passes. The locked bar (26,289) is missed in every version.
- **Backtest (D, mix):** −1.19 (−3.92 to −0.14). The range now excludes 0 and is larger than the main −0.96, so the backtest fails. The negative lean can't be told apart from no-repeal years; it is not evidence of cause.

**Test 49 (event time, new sample):**
- **38-place set:** now 36 places with complete data. Mix slope −0.45 (−2.24 to +0.51), "no clear change over time" under every weighting.
- **Long set:** 13 places. Mix slope −0.75 (−2.05 to +1.08), and random effects −0.30 (−0.92 to +0.06), both "no clear change". Random effects no longer shows a change.
- **Long-set leads:** random effects (−4.31) and equal weights (−4.34) slope downward before repeal (ranges exclude 0), so these places were already falling. Under the mix the lead slope is +0.85 (−8.23 to +1.30), near the top of its range and unstable with 10 places.

**Missing-data table (record only).** `--corrected --missing-only`, rerun against a temporary copy of the batch inputs, gives a byte-identical copy of the committed `reference/parking_method2_missing_by_state.csv`. The sample fixes do not change it.

**Audit.** Reviewed by the coordinator's audit (parking_batch_rerun_2026-11-05_review.md): numbers match the CSVs; results stand.

**Reading.**
- The sample fixes barely move the main estimate.
- They widen method 2's range, so it now just misses the like-for-like bar.
- Its mix backtest now fails, which strengthens the earlier caveat. The lines are unchanged, and any tool change needs Ryan's own OK.

## Test 50: San Francisco and Emeryville project parking (2026-11-05; lock "Test 50", with the reading change)

**Descriptive only. Nothing changes in the tool. Not to be cited until Ryan spot-checks 5 rows.**

**Files.**
- `reference/parking_t50_sf_projects.csv` has 31 rows. 2018-016535PRJ stays in the file but is excluded here: it documents units, not a new project. That leaves 30.
- `reference/parking_t50_emeryville_projects.csv` has 15 rows.
- `reference/parking_t50_sf_frame_counts.csv` and `reference/parking_t50_sf_sample.csv` hold the frame and the draw.

**Frame caveats (San Francisco).**
- **Approved before-151 pool:** only 10 records, so it was fully drawn and is effectively a census. With the dropped record, 9 remain.
- **Blank decisions:** 55 before-151 records are "Closed" with no decision. Their outcome isn't known, so approval rates are not computed.
- **Section mismatches:** the frame's section (from current parcel zoning) matches the case report for 26 of 30. It differs for 2 and is unclear for 2. The case report wins.

**San Francisco, three groups (residential stalls; homes as approved):**

| Group | Projects | Stalls per home, proposed | Stalls per home, approved | Median project, approved | Projects approved with 0 stalls |
| --- | --- | --- | --- | --- | --- |
| Filed and approved before repeal | 1 | 0.00 | 0.00 | 0.00 | 1 of 1 |
| Filed before, approved after ("switchers") | 13 | 0.54 (11 with counts) | 0.46 | 0.25 | 4 of 13 |
| Filed after | 16 | 0.19 | 0.16 | 0.05 | 8 of 16 |

- **Filed after:** 1,780 homes proposed and 1,900 approved, with 346 stalls proposed and 310 approved. Four of the 8 zero-stall projects are 100% affordable.
- **Before/before (2017-007542PRJ):** one project only, so it can't be compared with the other groups. It had a 17-stall minimum, met under Sec. 150(e) by swapping in bike parking.
- **Switchers, Sec. 151 (minimums at filing), required minimum against approved stalls:**
  - 2018-009081PRJ: 49 required, 0 approved. It first sought a PUD exception; none was needed by approval.
  - 2016-013012PRJ: 9 required, 9 proposed, 0 approved.
  - 2018-000468PRJ: 20 required, 7 approved.
  - 2016-002874PRJ: 6 required, 6 approved.
  - 2018-007380PRJ: 25 required, 25 approved.
  - 2017-003559PRJ: 240 required, 416 approved.
  - 2018-007883PRJ: P district, no minimum, 550 approved.
  - 2016-012545PRJ: minimum not found, 24 proposed, 39 approved.
  - Bunching against the old minimum: 3 below, 2 at, 1 above, 2 unknown or no minimum.
- **Switchers, Sec. 151.1 (no minimums), proposed to approved:**
  - 2016-014802PRJ: 152 to 86.
  - 2017-000275PRJ: 13 to 3.
  - 2017-002951PRJ: 32 to 0.
  - 2018-014727PRJ: 0 to 0.
  - 2017-008051PRJ: not found to 83.
- **Big projects:** the switcher ratios are pulled up by two of them (2018-007883PRJ with 1,100 homes and 550 stalls, and 2017-003559PRJ with 273 homes and 416 stalls). The median is the better summary.
- **Commercial:** 19 of 30 projects are mixed use. Commercial minimums found are 0 in every row with a value. 558 commercial stalls were approved, all among the switchers.
- **Old minimum for filed-after projects:** not coded, so bunching against it is not computed for that group.

**Emeryville (repeal 2020-05-21), shown as a list of cases:**
- **Filed before:**
  - FDP17-001: 500 homes, 335 stalls approved, equal to the 335 minimum (2018).
  - UPDR17-009: 33 homes, 23 required, 15 proposed, approved count not found.
  - UPDR18-002: 6 homes, 5 required, 7 proposed and 7 approved (approved 2020-10-06, after repeal; high confidence).
  - UPDR17-002: 6 homes, counts not found.
  - Two were withdrawn: UPDR17-011 (259 homes, 98 required, 195 proposed) and the Onni Christie project (638 homes, 256 required).
- **Filed after:**
  - ZC20-002: 90 homes, 42 to 30 stalls.
  - ZC22-001: 68 homes, 22 to 21.
  - FDP21-001: 22 stalls proposed, 0 approved, with 0 homes approved.
  - ZC23-008: 364 to 362 homes, 263 stalls proposed, approved count not found.
  - Five were not approved: withdrawn, abandoned or still in process.

**Reading.**
- **After the repeal:** most San Francisco projects proposed and got far fewer stalls than the old minimums. Half of the filed-after projects (8 of 16) had none. Four of those 8 are 100% affordable; whether they would have had a reduced or zero minimum before the repeal anyway (for example, under affordable-housing reductions) is not known, because the old minimum was not coded for this group.
- **Switchers:** under Sec. 151, half went below the old minimum (3 of 6 with a known minimum) and several dropped stalls between proposal and approval (9 to 0, 32 to 0, 152 to 86).
- **Large market-rate projects:** some still chose more parking than the minimum.
- **What this does not show:** whether more homes were built. It is consistent with the old minimum binding for some switchers (3 of 6 with a known minimum went below it). This is a description, not a test.

**Audit.** Accepted (coordinator's audit, 2026-11-05 about 16:57 UTC); all figures recomputed from the CSV and match. Wording fixes applied.

**Spot-check rows for Ryan (seed 20261105, drawn from the 30 kept SF rows):** 2017-002951PRJ, 2022-012441PRJ, 2020-006679PRJ, 2021-000947PRJ, 2018-014727PRJ.

**Spot-check passed (Ryan, 17:19 UTC):** "these SF projects look correctly coded". The Test 50 result can now be cited, as a description.

## Test 51: does subsidized building drive the result? LIHTC check (2026-11-05; lock "Test 51" with audit fixes and the cut-off, Ryan 17:14 UTC)

**Evidence and sensitivity only. Nothing in the tool changes.**

**History.** A first version (afb465b2) subtracted every LIHTC project, including acquisition/rehab and existing-building projects, which need no new building permit. The audit caught this at 18:05 UTC and the version was withdrawn.
- **Fix:** only new-construction projects (TYPE 1) are subtracted (fa8f82fd, 18:06:41 UTC). This was a self-approved data fix.
- **Reruns:** every configuration was rerun after the fix; the TYPE-1 runs started at 18:06:55.
- **Upper bound:** a TYPE 1 + 3 + blank sensitivity was added (d0605d56; run started 18:16:26).

**What was done.**
- **Data:** HUD's LIHTC database (lihtcpub.zip, hand-downloaded by Ryan; SHA-256 e07acee7…). Projects are assigned to BPS places by location (fix 1).
- **Adjustment:** each place-year's new-construction tax-credit units are subtracted from total and 5+ unit permits, for repeal and comparison places alike. Permit year = allocation year + 1. The result is floored at 0.
- **Runs:** each configuration reran the whole pipeline on the fixed 74-place sample.
- **Results file:** `reference/parking_t51_results.csv`.
- **Outcome:** "all units" only.
- **Projects outside the test:** those in places with no BPS series (some Michigan and Minnesota cities, unorganized territories).
- **5+ count:** all LIHTC units come out of the 5+ count, so tax-credit homes in 2–4 unit buildings are taken from the 5+ count, not the 2–4 count.

**Share of permits removed, main configuration (home-weighted).** The removed share rises more after repeal in the repeal places than in the comparison places:

| Places | Before repeal | After repeal |
| --- | --- | --- |
| Repeal places | 10.0% | 25.9% |
| Comparison pools | 5.2% | 8.8% |

**Results.** Wisconsin homes over 2027–2031. The unadjusted and adjusted columns use the tool's method (the real average with the placebo spread). The paired difference is adjusted minus unadjusted on the same places (2,000-draw paired place bootstrap, seed 20261105).

| Version | Places | Unadjusted (90% range) | Adjusted (90% range) | Paired difference (90% range) |
| --- | --- | --- | --- | --- |
| **Main: 2020 cut-off, new construction, 100% affordable** | 13 | −13,497 (−101,833 to +91,560) | −19,021 (−103,247 to +86,312) | −5,524 (−10,288 to +2,945) |
| All LIHTC low-income units (fix 5) | 13 | same | −19,048 (−103,439 to +84,963) | −5,551 (−9,641 to +2,355) |
| Permit year = allocation year | 13 | same | −13,383 (−100,436 to +89,917) | +114 (−663 to +2,912) |
| Upper bound: TYPE 1 + 3 + blank | 13 | same | −19,927 (−105,565 to +81,332) | −6,430 (−9,530 to +1,729) |
| 2021 cut-off (sensitivity) | 25 paired | −13,866 (−77,516 to +62,709) | −14,768 (−76,261 to +58,904) | −903 (−5,038 to +4,478) |
| Full window to 2025 (descriptive only; recent years undercounted) | 74 | −15,380 (−46,268 to +19,649) | −11,762 (−42,311 to +23,083) | +3,618 (−72 to +7,669) |

**Reading.**
- **Main version:** the adjustment moves the Wisconsin figure by −5,524 homes (paired range −10,288 to +2,945). With 13 places, this test says little either way.
- **Direction:** the sensitivities differ in sign (−6,430 to +114 at the 2020 cut-off, and −903 at 2021), so the direction of the adjustment is not stable.
- **Blank construction type:** the blank-TYPE share of matched units falls from 19.2% (2012) to 6.9% (2021), so blanks sit mostly in the before-years. The TYPE-1-only main therefore removes relatively fewer units before repeal than after, which pulls the adjusted after-period down more than the before-period. The upper bound, which counts blanks, moves the figure by −6,430 (−9,530 to +1,729).
- **Full window:** not read, because the database misses most projects funded after 2021. The removed share in repeal places falls from 7.6% before to 4.3% after, and that asymmetry pushes the difference up.
- **Method 2 (D, target-state mix), shown and not read:** it is unstable with 13 places.
  - 2020 cut-off: +39,994 unadjusted, +41,324 adjusted.
  - 2021 cut-off: −4,537 → −4,721.
  - Full window: −12,873 → −10,741.

**Checks, main configuration:**
- **The 0 floor binds** in 1,072 of 3,424 place-years with LIHTC units (31%; the withdrawn version had 46%). 80,317 of 380,147 units (21%) could not be removed (the withdrawn version had 30%). The share fell, as expected once rehab projects were removed.
- **Timing check:** 69.1% of LIHTC units fall in a permit year with at least that many BPS permits (58.1% before the fix).
- **What these mean:** the adjustment is rough. Even with new construction only, in 31% of LIHTC place-years (1,072 of 3,424) the projects hold more units than the permits Census shows that year. Those place-years account for 21% of LIHTC units (80,317 of 380,147), so the adjustment is understated wherever the floor binds. The allocation + 1 proxy also often puts a project's units in a different year from its permits.

## Test 52: causal diagram, back doors and unseen back doors (2026-11-05; lock "Test 52" with all audit fixes; Ryan's go 17:58 UTC)

**Evidence only. Nothing in the tool changes. D is unchanged because Ryan has accepted no Test 52 change.**

**How to read this section.**
- **Units:** rates are homes permitted per 1,000 existing homes a year. WI homes = rate × 13,343.385, over 2027–2031.
- **Shift:** a rerun minus the batch on the same places, with a paired place-bootstrap 90% range (2,000 draws, seed 20261105).
- **Reading line (fix 9):** one test moving alone is not evidence, with the same bar for both signs.
- **Batch reference:** main −1.1526 (WI −15,380; −46,268 to +19,649); D −0.9647 (WI −12,873; −44,571 to +4,854).
- **Reproduction:** every part first reproduced these exactly.

**Bottom line.**
- For the back doors we could measure, no shift's paired range excludes 0, except h1: −3,409 homes (−6,682 to −219). The tested back doors are market demand, other reforms, pre-repeal trends, pool rules, spillover and the 2010 homes denominator.
- No placebo shows an effect after repeal that is absent before it.
- **Influence (52e):** the main estimate's negative lean comes from a few big cities. Dropping San Francisco, Austin and San Jose moves it by +21,353 homes, to +5,973. D's lean does not depend on them. Main is also out of balance on crowding (−0.35) and density (0.31), which it does not match on. Both points support reading D over main.
- **Alternatives:** synthetic DiD loses to D.
- **The sign depends on the weighting:** the mix gives −12,873 WI homes; the other four give +1,479 to +9,261. The mix stays because stacking failed, not because it clearly won.

**52a. Market demand (D read; main exploratory).**
- **Traits:** ACS rent growth (window ending the year before repeal against the window ending 6 years before) and QCEW county job growth.
- **Coverage:** the margin-of-error fallback (20% is a convention) uses county rent for 6 of 74 repeal places. 136 Connecticut place-years have no county fallback and go missing.
- **Balance:** rent and job growth were already balanced (standardised difference 0.10–0.12).
- **D + market traits:** −8,082 (−49,290 to +9,166). Shift +4,791 (−10,101 to +9,701).
- **Main + market (exploratory):** the "10 nearest on market traits" rule is not in the plan. It also cut pools from a median of 27 places to 10, so the shift mixes two changes. Shift +2,062 (−734 to +5,978).
- **2010 homes denominator (fix 8):**
  - D: shift +1,539 (−15,412 to +4,123).
  - Main: shift −2,824 (−8,913 to +2,242); with batch weights held, −5,393 (−16,372 to +4,857).
- Code: e07ff5df, 0973c006, 6aa23b42. Results: cc86b0ca.

**52b. Other housing reforms as dated events.**
- **Events table:** 5,292 rows, committed in c1eedd17 (18:16:27) before the first join (18:18:30).
  - 4,772 state ADU-law rows; 520 place rows, 500 of them matched.
  - Lists used: statewide_states_laws, other_cities_reforms, tod_cases, tod_reform_density, CA rail openings, MBTA Communities, Option D sets, edge-test places, WI ADU rules, PRN (repeal places only, as `prior parking dose`), and the repeal places' own ordinance checks.
  - Coverage outside these lists is partial. State parking laws are not in the list; rail openings are CA only; some reforms are undated.
- **Order:** the rerun script was committed with the results (e896e48), not before the run. One edit at 18:19:12, 41 seconds after the first join, changed only the summary section. No output had been read. This is the helper's account and can only be checked against file times.
- **Deviations:**
  - D was recomputed with method 2's functions; the base reproduces.
  - MM_BPS_LAST_YEAR = 2025 was set.
  - The pool-drop rule was also applied to the placebo pools. This was not in the plan, but it is the same rule on both sides.
  - Timing is at year precision.

| Variant | Main shift (WI homes) | D shift (WI homes) |
| --- | --- | --- |
| Drop pool place-years with a reform 1–3 years before | +5,337 (−614 to +15,050) | +80 |
| Drop repeal places with a separate earlier reform (58 places) | −4,017 (−28,555 to +25,353) | +1,668 |
| Drop division/nation pools in states with a law | +53 | −987 |
| Indicator, everyone kept (fallback on main, where the repeal drop worsens balance) | −4,017 | −974 (−10,808 to +5,070) |
| After-repeal reforms, pool drop (post-treatment sensitivity) | +27 | +387 |
| After-repeal reforms, repeal drop (post-treatment sensitivity) | +22,004 (−12,409 to +52,973) | +1,561 |

- No shift excludes 0. The main pool drop is the closest call, and it is not a finding.

**52c. Pre-repeal trends (bounds).**
- The main range includes 0, so the breakdown M is 0 by definition.

| Estimator | Largest pre-gap G | M = 0.5 range (WI homes) | M = 1 range (WI homes) |
| --- | --- | --- | --- |
| Main | 1.9451 (year −5) | −59,246 to +32,627 | −72,223 to +45,605 |
| D (G at year −9, available for 59 of 74) | 5.0763 | −78,438 to +38,722 | −112,306 to +72,589 |
| D (G from years −5 to −2) | 3.0425 | — | M = 1 rate range −6.38 to +3.41 |

- **P2 trend-matched rerun (main):** −13,969 (−44,316 to +21,678). Shift +1,410 (−1,334 to +4,744). Its range is a place bootstrap, so its width is not comparable with the placebo range.
- **52d.4:** a hidden factor would need to produce a post-repeal gap of 0.59 times the largest pre-gap (main) or 0.19 times (D).

**52d. Placebos.** Lists were committed in fdb9c5f0 before any join.

| Placebo | Estimator | Places | WI homes (90% range) |
| --- | --- | --- | --- |
| Repeals moved 4 years early | Main | 67 | +23,443 (−7,936 to +56,969) |
| Repeals moved 4 years early | D | 67 | −29,082 (−78,740 to +22,466) |
| 2 years early (batch backtest, cited) | D | 74 | −15,904 (−52,339 to −1,925) |
| Houses (1-unit permits), house minimum ≤ 2 | Main | 52 | −1,484 (−13,124 to +13,443) |
| Houses (1-unit permits), house minimum ≤ 2 | D | 52 | −23,991 (−41,694 to +13,216) |

- **ADU-only reform places:** not run. The Mercatus copy on disk is a Cloudflare block page; it is cited, not worked around.
- **D seed:** D here uses seed 20261105, against the batch's 20261104. D's upper end moves from +0.364 to +0.471 in rate.
- **Pools at −4 years:** the −4-year path re-chose pools with untrimmed windows, because a moved repeal year needs fresh pools. Gastonia and Avondale Estates drop out.
- **Reading:** the −4-year estimates lean in opposite directions, and both include 0. D's −2-year dip excludes 0, so D's negative lean also appears before the repeal. Neither is evidence of cause.

**52e. Influence (sizes only).**
- **Design change:** the leave-one-out paired design was changed after the first run's results had been seen (post hoc; the first run's log is kept). Under the new design even trivial shifts would "count", so no count wording is used here.
- **Main, dropping the 3 largest by weight** (San Francisco, Austin, San Jose; 127% of the result): +5,973 (−20,438 to +35,123), a move of +21,353.
- **Main, dropping the 3 largest by contribution** (Austin, Minneapolis, Raleigh): a move of +17,683.
- **D, dropping the 3 largest by weight** (Hudson, Saranac Lake, Ecorse): a move of −1,429. By contribution (Ecorse, Saranac Lake, Burlington): a move of −5,094.
- **Leave-one-out:**
  - Main ranges from −23,518 (without Raleigh) to +1,054 (without Austin).
  - D ranges from −20,011 (without Hudson) to −6,781 (without Ecorse).
  - One D range out of 74 excludes 0 (without Burlington). There is no count reading, because leave-one-out ranges are not independent.
- **Bastrop:** its own effect is the highest of the 74. Dropping it moves main by −669 and D by −2,244.
  - Verified: the 2011 fire and the 2015 flood happened in the county.
  - Not verified: that their rebuilding fell inside the city, in its windows.

**52f. Synthetic DiD.**
- **Result:** loses to D on 3b's fake repeals.
  - Random effects: MAE 1.289 against 0.852, paired difference +0.437 (+0.332 to +0.537). Coverage 82.0% against 93.5%.
  - It also loses under every other weighting.
- **Real 74, evidence only:** SDID (mix) −18,874 (−49,394 to −4,081).
- **Fit versus prediction:** SDID fits the before-years better for 72 of 74 places, but predicts the fake repeals worse. A closer before-fit did not give a better after-prediction.
- **Zeta:** a treated count of 1 per fit (the interpretation) is the main reading; the literal 74 reading is a sensitivity, and it fails too.
- **Fix after a look:** dfdb16dd (skipping unreported before-years) came after one stage-1 look whose verdict was D. The verdict did not change.

**52g. Spillover, out-of-metro pools (D).** −12,402 (−39,417 to +6,329). Shift +471 (−3,048 to +8,997). 11 pools changed; on those pools, the mean Mahalanobis distance rose from 0.63 to 0.76.

**52h. Pool rules that may filter on after-repeal outcomes (D).**
- **h1, date-aware "never reformed":** shift −3,409 (−6,682 to −219).
  - The paired design is a full resample, unchanged from the code commit.
  - Only 11% of PRN rows carry a date, so it changed 9 pools.
  - With undated reforms admitted as well: −3,071 (−14,974 to +9,935).
- **h2, shock rule without the land test:** shift −2,772 (−11,666 to +2,459).
- **h3, one missing year filled:** shift −984 (−4,627 to +526). 0 filled years before repeal, 1 after.
- **Reading:** removing the possible collider rules moves D slightly more negative. Only h1's range excludes 0, and h1 is small.

**52i. Weighting bake-off, then stacking** (1569cd60, committed 19:47:54; run 19:47:56).
- **Bake-off:** leave one state out, over 10 states. Held-out MAE:

  | Weighting | MAE |
  | --- | --- |
  | target-state mix | 3.0603 |
  | random effects | 3.3893 |
  | equal | 3.3907 |
  | square root | 3.4822 |
  | homes | 3.8385 |

  - The mix is 9.7% better than the runner-up, and the 2% gap is a convention fixed in the plan.
  - Against every other weighting, the paired error difference (places resampled within states) has a 90% range that includes 0. So there is **no clear winner**.
- **Stacking:**
  - Final shares: mix 0.752, random effects 0.248, others 0.
  - Fold shares vary: mix 0.34–1.00, random effects 0–0.66, equal 0–0.66.
  - Nested held-out MAE is 3.460, worse than the single mix (3.060).
  - Held-out coverage is 30% (3 of 10 states). The pass band 85–95% means exactly 9 of 10, a knife edge.
  - **Stacking fails, so the target-state mix stays.**
- **Blend, shown for the record:** −7,507 (paired-sum range −32,173 to +9,604; mixture range −39,898 to +18,832); effective places 27.0.
- **Spread across weightings (WI homes):**

  | Weighting | WI homes |
  | --- | --- |
  | mix | −12,873 |
  | random effects | +8,780 |
  | square root | +9,261 |
  | homes | +1,479 |
  | equal | +8,270 |

- **Why coverage is so low (post hoc explanation):** held-out state results run from −3.745 to +7.536 per 1,000 homes, so states differ from each other, not just by noise. The blend's range is the range of an average effect, and one state's own result can fall well outside it; 7 of 10 held-out states did. The Wisconsin range is likewise the range of an average effect.
- **Tie rule:** this replaces "ties go to the state mix" for this test only (Ryan's go, 17:58 UTC).

## Test 53: six city classes, population and held-out prediction (2026-11-05; lock "Test 53" with its revision and audit fixes; Ryan's go 21:53 UTC)

**Evidence only. No tool change.**
- **Origin:** prompted by results already seen (52e; the CA post hoc large-vs-small pattern).
- **Code:** 970037ea; run started 21:53:33 UTC, after Ryan's go was recorded (d6b69d07).
- **Outputs:** `reference/parking_t53_groups.csv`, `_prediction.csv`, `_class_matched.csv` and `_class_matched_places.csv`.
- **Units:** rates are homes permitted per 1,000 existing homes a year; ranges are 90% place-bootstrap ranges.
- **Population:** 2010 census population was found for 73 of 74 places (1 ACS fallback).

**Group averages (rate, with n):**

| Class | n | D, mix | Main, homes-weighted | D, equal weight | Main, equal weight |
| --- | --- | --- | --- | --- | --- |
| Main city | 31 | +7.67 (+2.06 to +10.80) | −1.32 (−4.16 to +1.87) | +2.55 (+0.68 to +4.46) | +1.52 (−0.40 to +3.35) |
| Secondary principal city | 8 | +0.31 (−2.10 to +2.50) | −0.93 (−3.16 to +2.19) | −0.09 | −0.20 |
| Suburb | 22 | +0.05 (−2.45 to +2.46) | +0.03 (−2.48 to +3.02) | +0.23 | +0.32 |
| Exurb (thin) | 4 | −0.88 (−43.1 to +41.2) | +8.89 (−9.59 to +27.70) | −3.95 | +2.61 |
| Outside metro (thin) | 7 | −4.01 (−6.24 to −1.92) | −0.98 (−3.56 to +1.04) | −4.39 | −1.71 |
| Rural (thin) | 2 | −2.29 | −2.47 | −2.32 | −3.85 |

- **D's mix within a group:** the mix re-aims each group's places at Wisconsin's size and metro cells. A likely reason (a guess; the cell weights were not examined) why D and main differ in sign for main cities is that the mix puts weight on cells that main's homes weighting does not.

**Differences (main city minus …):**

| Difference | D | Main | Counts? |
| --- | --- | --- | --- |
| Minus secondary, weighted | +7.36 (+1.31 to +11.22) | −0.39 (−4.54 to +3.59) | no: methods disagree in sign |
| Minus suburb, weighted | +7.62 (+1.64 to +11.51) | −1.35 (−5.41 to +2.58) | no: methods disagree in sign |
| Minus secondary, equal | +2.64 (−0.24 to +5.31) | +1.72 (−2.15 to +5.30) | no: ranges include 0 |
| Minus suburb, equal | +2.32 (−0.73 to +8.91) | +1.20 (−2.61 to +6.27) | no: ranges include 0 |
| Gap differences (weighted minus equal) | D vs secondary +4.72 (+0.29 to +7.38); other D/main pairs include 0 | | no: methods disagree in sign |

**Population, continuous (slope per 10× population, 2010 count):**

| Population slope | D, mix | D, equal | Main, homes-weighted | Main, equal |
| --- | --- | --- | --- | --- |
| All 74 | +1.11 (−0.44 to +4.70) | +1.18 (−0.91 to +7.19) | −4.19 (−8.28 to +0.66) | +0.50 (−1.71 to +2.78) |
| Within main cities (31) | **−9.25 (−13.59 to −4.65)** | — | **−7.34 (−14.33 to −0.95)** | — |
| Within suburbs (22) | +1.35 (−3.25 to +18.59) | — | +5.42 (−1.57 to +14.26) | — |

- **Within main cities:** this is the only result that meets the reading rule. Both ranges exclude 0, and both methods agree: among main cities, larger ones had lower estimated effects.
  - About 14 comparisons were made, so 1–2 such results by chance are plausible.
  - The test was prompted by SF, Austin and San Jose, which are the largest main cities.
  - So it is a hint, not a finding, and class and size cannot be separated outside these two classes.
  - **Leaving out SF, Austin and San Jose** (post hoc, reported only; 28 main cities): D −8.33 (−15.28 to −1.06); main −5.73 (−15.07 to +2.79). D's slope survives without them, but main's range then includes 0. Without SF, Austin and San Jose, the within-main-city slope no longer meets the reading rule, because main's range includes 0 and the rule needs both methods.

**Held-out prediction (log10 2010 population + six-class indicators; 20 repeats of 10-fold; the 5% bar is the locked convention):**
- **No tool passes,** under either estimator or weighting.
- **Best gains over "one average":** random forest +3.7% (D, equal; repeats +0.9% to +6.6%) and +3.2% (D, mix). Main's best is +2.2%. Most tools do worse than one average. The repeats are not independent.
- **Reading:** city type and size do not predict held-out cities' effects better than one average, the same as the 55 earlier traits.

**Thin groups, read both ways:** outside metro's D mix, −4.01 (−6.24 to −1.92), also excludes 0, but main's range includes 0. With n = 7 and no difference read, it is not a finding. Rural (n = 2) and exurb (n = 4) are too thin to read.

**Class-matched pools (D):** −12,443 WI homes (−45,347 to +11,783). Shift +430 (−24,343 to +28,543); no change. 51 of 74 pools left ladder step 1. The median number of eligible same-class places is 88. Rural and exurb pools used the ladder fallback.

**Bottom line.**
- City type does not reliably sort parking effects. The group differences depend on the method, and the type-plus-size model does not predict held-out cities.
- The one consistent pattern, larger main cities having lower estimated effects, is post hoc and may be chance. Without SF, Austin and San Jose it holds under D but not main.
- A guess, not tested: it may reflect the 2022–23 boom-end timing seen in the winners-vs-losers comparison.

## Test 54: nested single/pair trait screen, then an honest regression forest (2026-11-05; lock "Test 54" with audit fixes; Ryan 22:32 UTC "yeah try it out")

**Evidence only.**
- **Origin:** prompted by earlier results; several traits are here because earlier looks at these 74 places showed 3–7% gains, so a pass would have been optimistic.
- **Code:** be43a217; run started 22:36:49 UTC.
- **Outputs:** `reference/parking_t54_results.csv`, `_selection.csv` and `_top_pairs.csv`.
- **Traits:** about 90, all measured before repeal: 10 pre-repeal non-ACS items, 73 ACS traits from the release before repeal, 2 market traits, 5 class indicators and 2010 population.
- **Procedure:** each of 200 outer folds (10 × 20) screened about 4,000 singles and pairs on its own training places, kept the top 5 traits, and fit the honest regression forest (primary) and a weighted regression on them.

**Held-out gain over "one average"** (the 5% bar is the convention; two chances to pass, main or D-mix):

| Outcome | Forest gain (range over repeats) | Regression gain (range over repeats) | Passes? |
| --- | --- | --- | --- |
| Main (homes × after-years) | +0.9% (−10.2% to +11.7%) | −12.6% (−31.9% to +4.4%) | no |
| D (target-state mix) | −5.6% (−13.1% to +3.2%) | −23.0% (−34.1% to −3.3%) | no |
| D (equal) | −2.5% (−7.7% to +4.5%) | −13.1% (−22.6% to −1.8%) | no |

- The repeats are not independent.

**Selection stability.** The traits chosen differ by outcome, and none is chosen in most folds for all three. Most often chosen:
- **Main:** labour-force participation (71% of folds), share with a mortgage (44%), rent burden 30%+ (42%).
- **D (mix):** rate before repeal (73%), permit volatility (57%), share with a mortgage (44%).
- **D (equal):** outside-metro class (89%), share under 18 (65%).

**Reading.**
- Nothing passes. Once the trait choice itself is tested on held-out cities, no combination of the roughly 90 pre-repeal traits predicts a city's parking effect better than one average. Most versions do worse.
- The 3–7% gains seen before did not survive this guard.
- With 74 places and a very noisy screen, the fail means traits can't be shown to predict held-out cities here. It does not show that no trait matters.
- Main's best repeat reached +11.7%, but the mean is +0.9%. That one repeat is noise, not a partial pass.
- As locked, the write-up recommends ending the trait search. The parking estimate stays one average for all places.

## Test 56: small projects (2–4 unit homes), place size, 74 places (run 2026-11-12, commits 068e3648 code, 22bb77d2 outputs)

Locked in CAUSAL_FRAMEWORK_PLAN.md ("Test 56: one reading at lock"). Ryan's go was at 01:40 UTC. The code audit cleared it, with a dry run on all homes. The counts and MDE were committed first (72df2af5) and cleared before any result was opened. The overall cells repeat earlier work on a new outcome; only the size-slope cells are new. Method 2 D has no pace trait, so "matches on pace" applies to the main method only.

Units are homes per 1,000 existing homes a year. 90% ranges. Wisconsin homes = rate × 13,343.385 (2027–2031; display only).

**Can the test see an effect?** Yes. 53 of 74 places had some 2–4 permits before repeal (14 of 26 under 25,000; 39 of 48 at 25,000+). The minimum detectable overall effect is 0.354 (4,727 Wisconsin homes over 5 years).

| Headline cell | Estimate | 90% range | Excludes 0 |
|---|---|---|---|
| H1 main, overall 2–4 effect | −0.067 (−899 homes) | −0.295 to +0.177 (−3,930 to +2,360) | No |
| H7 D, overall 2–4 effect | −0.007 (−91 homes) | −0.230 to +0.376 (−3,065 to +5,016) | No |
| H2 main, size slope (per 10× population) | −0.278 | −0.440 to −0.104 | Yes |
| H8 D, size slope | +0.119 | −0.230 to +0.392 | No |

**Reading (mechanical, parking_t56_reading.csv):**
- **Overall 2–4 effect:** does not count. Neither range excludes 0.
- **Size slope:** does not count. Main is negative and excludes 0 (smaller places did relatively better on 2–4 homes). D points the other way and includes 0, so the slope does not count. Main's 25,000 gap agrees with its slope (−0.241 vs −0.278); D's does not (gap −0.168, slope +0.119).
- **Headline cells excluding 0:** 1 of 4, which is plausible by chance.
- **Pre-trend label: ON.** Lead −4 excludes 0 under both methods (main +0.079, +0.018 to +0.149). Relative to year −1, all of D's event-study years sit about +0.24 to +0.49 higher, the after-years included. The after-years look like the before-years. That fits a low year −1 as well as a pre-repeal trend; the label stays on either way.
- **Scale rule:**
  - Main: no flag.
  - D: "don't know". Its level range includes 0, but the Poisson check excludes 0: ×1.88, range ×1.30 to ×2.64, 64 stacks. Main's Poisson is ×0.97, range ×0.75 to ×1.38, 60 stacks.
- **"Too few to read":** not triggered for any group.

**Checks:**
- The main size slope holds without flagged places (−0.308, −0.491 to −0.086), without Oregon (−0.280, −0.451 to −0.096) and on reported-only data (−0.252, −0.411 to −0.081). D's slope includes 0 in all three.
- Placebo dates (−2 and −4 years) include 0 under both methods.
- Long set (13 places): main −0.013 (−0.104 to +0.514); D +0.655 (−0.216 to +2.945).
- Spillover pools (D +0.002) and date-aware pools (D −0.006) leave D's overall effect unchanged.
- 1-unit and 5+ outcomes: no overall effect excludes 0. Three non-headline 5+ D cells exclude 0: the target-state gap (+3.048) and the equal-weight slope (+1.737) and gap (+4.222). They are not headline and not read.

**Plain reading:**
- We can't tell whether removing parking minimums changed 2–4 unit building in these 74 places. Both ranges include 0, and a pre-repeal lead failed, so the result is not read as an effect either way.
- The test could have seen an effect of about 4,700 Wisconsin homes over 5 years or more. The range runs from about 3,900 fewer to 2,400 more (main), or 3,100 fewer to 5,000 more (D).
- Whether small places gained more depends on the method, so it is not a finding.
- The scenario line is unchanged.
