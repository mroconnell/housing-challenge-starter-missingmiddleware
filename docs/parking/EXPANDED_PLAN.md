# Parking: expanded comparison and prediction tools. Plan written before testing

Written 2026-10-27 by the parking conductor, after Ryan approved ("Yeah go for it"). It extends [COMPARISON_PLAN.md](COMPARISON_PLAN.md) and [TRAITS_PLAN.md](TRAITS_PLAN.md). Everything below is fixed before any new place's permits are compared. Later changes go in section 7 with a date and a reason.

## 1. Why

The high end of the parking range rests on 24 places, and single places swing a lot. More places should narrow the likely range. With more places, tools that look across many traits at once (lasso, random and causal forests) also become worth testing.

## 2. Sample

- **Kept from before:** the 30 included places (24 main, 6 with conditions).
- **Added: 131 places.** These are places the Parking Reform Network rates as removing minimums for all housing, not yet checked, either undated (86) or adopted in 2015–2024, and found in the Census permit files. Each gets the same ordinance check as the first 46: in force or not, adoption and effective dates, exceptions, other zoning changes within a year, sources and confidence. The checks are recorded in `reference/parking_repeal_checks.csv`.
- **Repeal year:** the effective year from the check, or the adoption year if there is none. A place with no date found after checking is dropped and listed.
- **After period:** years 1–3 after the repeal, as available, with **at least 1 year** (so 2023 and 2024 repeals count). The main estimate weights each place by its homes and by its number of after-years (1–3).
- **Places that removed minimums with conditions:** the main estimate includes them, flagged; a sensitivity case leaves them out. This changes the first plan, where they were reported separately, because the owner asked for more data.
- **Unchanged from the first plan:** comparison places, the effect formula, and ACS population for matching.

## 3. Second source: California AB 2097

- The near-transit effect for 154 California cities (TOD's group P), described in [TRAITS_PLAN.md](TRAITS_PLAN.md), dataset B.
- **Combined estimate:** reported alongside the US estimate, as a precision-weighted average of the two, each weighted by 1 ÷ (width of its 90% range)².
- **Headline:** stays the US estimate, because AB 2097 is a transit-area reform, not a statewide one. The combined figure is a sensitivity case.

## 4. Prediction tools (each scored on places left out of the fit)

Applied to the US places (main sample, and with California's cities as a second, separate test):

1. one average (the benchmark to beat);
2. a weighted regression on all traits together (T1–T6 from the trait plan, plus population, metro setting, rent and the permit rate before repeal);
3. lasso, with its penalty chosen by cross-validation inside each training fold;
4. random forest (500 trees; leaves of at least 5 places);
5. causal forest. Because each place's outcome is already a before/after difference against comparison places, a forest on that outcome is the causal forest here, with honest splitting (half of each training fold builds the trees, the other half estimates the leaves).

**Score:** the weighted mean absolute error on left-out places. For the US sample this is 10-fold cross-validation repeated 20 times, with seed 20261027.

**A tool is adopted only if both hold:**
- it beats one average by at least 5% on the US places;
- it beats one average on the California cities, when trained on the US places plus California and tested on left-out California cities.

**Library:** scikit-learn (BSD-3-Clause), checked by the licence test.

## 5. What could change in the tool

- **The range:** the likely range of the average is recomputed on the larger sample, and the high end updates if it changes. A shift of the central case above zero would go to Ryan as a decision.
- **City types:** if a tool passes, I propose to Ryan a version where each Wisconsin place gets its own predicted effect. It goes in front of him as a decision, not straight into the tool.

## 6. Reporting

- Every place added or dropped is listed, with the reason.
- Every tool's score is reported, including those that fail.

## 7. Changes after writing

- **2026-10-27, after the ordinance checks and before any outcome was computed.** Many of the added places, mostly small towns, never removed minimums: they had none, or no zoning, or the check could not show that the code they replaced had minimums. They have no repeal event, so they are dropped and listed. The 19 places are: Rutland VT, Saltillo MS, Fulton MS, Follansbee WV, Cave Spring GA, Franklin Springs GA, Marcus IA, Foreman AR, Whitewood SD, Richardton ND, Madison KS, La Barge WY, Sinclair WY, Norton KS, Nettleton MS, Leland Grove IL, Plantersville MS, Kadoka SD and Gambier OH. Places where a new code replaced an older one with minimums stay in, flagged as having a zoning rewrite at the same time (for example Portsmouth OH, Taylor TX and Social Circle GA). Undated places with no date found are dropped (section 2).
