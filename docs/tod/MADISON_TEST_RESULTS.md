# Madison TOD overlay test: results

Written 2026-10-26 by TOD Gate 3 stage 2. The test follows [MADISON_TEST_PREREG.md](MADISON_TEST_PREREG.md), with the area rule of [CASE_ANALYSIS_PLAN.md](CASE_ANALYSIS_PLAN.md) section 7 and the judging rule of [GATE3_MODEL_SPEC.md](GATE3_MODEL_SPEC.md) sections 4 and 9.

- **Order of work.** Method A's prediction was committed in `bf6d347` before any permit was counted by overlay.
- **Changes to the plan.** Every change made while counting is in the plan's section 8, dated 2026-10-26.

## Answer first

- **Method A passes the pre-set test, but only weakly.**
  - **The pre-set rule:** method A is confirmed if its committed prediction lies inside the measured 90% interval.
  - **The prediction:** 0.251 extra homes permitted per eligible overlay acre per year (90% interval 0.136 to 0.382).
  - **The measurement, on the same basis:** 0.080 extra homes per eligible overlay acre per year (90% interval −0.167 to +0.309). The prediction lies inside that interval.
  - **Why "weakly":**
    - The interval also contains zero, so the test cannot show that the overlay did anything.
    - The point estimate is about a third of the prediction.
- **Per unit of added density.** The measured effect is 0.215 extra homes permitted per eligible acre per year per 1.0 of added floor area ratio (FAR), with a 90% interval of −0.448 to +0.826. Method A used 0.671 per 1.0 of added FAR, the New York pooled value. That value lies inside the measured interval too.
- **Method B** was not computable, as recorded in GATE3_MODEL_SPEC.md section 9.
  - So there is no head-to-head contest.
  - The Chicago fallback in section 4.4 is for the case where both methods fall inside the interval. It is not triggered.
- **What this means for the scenarios.**
  - Madison does not reject the typical response (0.671).
  - Madison also cannot tell the typical response from the little response (Chicago's 0.24) or from no response.
  - Its measured value, 0.215 per 1.0 of added FAR, sits close to Chicago's.

## Files

- **Code:** [missing_middleware/tod/madison_test.py](../../missing_middleware/tod/madison_test.py) and [scripts/run_tod_madison_test.py](../../scripts/run_tod_madison_test.py).
- **Tests:** [tests/test_tod_madison_test.py](../../tests/test_tod_madison_test.py).
- **Results:**
  - [reference/tod_madison_test_results.csv](../../reference/tod_madison_test_results.csv): estimates, intervals, judgment, sensitivities and match rate.
  - [reference/tod_madison_test_rates_by_year.csv](../../reference/tod_madison_test_rates_by_year.csv): units, projects, acres and rates by area and year, 2017–2026, under both area rules.
  - [reference/tod_madison_test_unmatched.csv](../../reference/tod_madison_test_unmatched.csv): unmatched permits with 10+ units, by street name and year.
  - None of these files holds a permit number, parcel id, house number or name. A test checks this.
- **To run:** `uv run --all-extras python scripts/run_tod_madison_test.py --fetch` once, then without `--fetch`. It takes about 30 seconds.

## How it was measured

### Permits

- **Source:** Madison's Construction Summary report (BLDNRC and BLDNCC permit types).
- **What counts:** the Dwell field (dwelling units added), where it is above 0.
- **Year:** the issue year.
- **Duplicates:** one row per permit number, keeping the earliest issue date. This uses the ADU pipeline's `dedupe`.

### Placing permits on lots

- **Address matching:** the ADU pipeline's `AddressIndex`, against Madison address points and parcel addresses.
- **Lot:** each permit is placed on the lot that holds its matched parcel's point.
- **Ambiguous matches:** placed only when every candidate parcel lies on the same lot.
- **Match rate:** 3,578 of the 3,587 permits issued 2017–2025 were placed on a lot (99.7%). They hold 23,615 of the 23,894 units (98.8%).
- **Unmatched permits with 10 or more units, 2017–2026:** five permits, 303 units. Their streets:

  | Year | Street | Units |
  | --- | --- | --- |
  | 2022 | University Ave | 66 |
  | 2023 | East Springs Dr | 120 |
  | 2025 | Stones Throw Loop | 40 |
  | 2025 | Stones Throw Loop | 35 |
  | 2026 | Blissful Ave | 42 (shown year only) |

  - In all five, the house number does not exist in the current address layers.
  - East Springs Drive is in the East Towne area. Lots there were rezoned in the window (GETAP areas), so they are in no area anyway.
  - Stones Throw Loop and Blissful Avenue are new streets at the city's edge, far from the overlay.
  - The University Avenue permit (66 units, 2022) is the only one that could have fallen in the treatment or the ring. It is a before-year permit.

### Lots, eligible land and the dose

- **Lots and eligibility:** the same as in the land layer the prediction used (`scripts/build_tod_station_areas.py`):
  - parcels with identical outlines are counted once;
  - eligible land is residential, mixed-use or commercial zoning (including planned development);
  - parks, water, institutional campuses and cemeteries are left out;
  - single-family use is left out.
- **Check:** the script reproduces `reference/tod_madison_test_land.csv` exactly: 2,931.7 eligible acres in the overlay, 1,226.3 in the ¼-mile ring and 7,107.2 in the rest of the city.
- **Dose:** the overlay's allowed FAR minus the base district's, from `reference/tod_zoning_rules_madison.csv`. It is the same coding used for the prediction.

### Areas: the uniform rule

The uniform rule is CASE_ANALYSIS_PLAN.md section 7, run through `cases.uniform_areas`.

- **Treatment:** eligible overlay lots whose allowed FAR rose with the overlay. That is land in five districts: CC, RMX, TSS, TR-V2 and NMX. In the other districts, the overlay changes building types or parking but not the coded density.
  - **Size:** 614.7 acres.
  - **Dose:** 0.977 added FAR.
- **Comparison:** eligible lots outside the overlay, within ¼ mile of treated land, whose zoning did not change in 2017–2025.
  - **Size:** 457.5 acres.
- **Second comparison:** every other eligible Madison lot not excluded below.
  - **Size:** 6,607.1 acres.
- **In no area:**
  - **Overlay lots whose density did not rise:** 2,317.0 eligible acres.
  - **Land already at the law:** 180.4 acres, all downtown districts. "At the law" means no homes-per-acre cap and allowed FAR at least the median new level on rising land, 4.2.
  - **Lots whose zoning changed in 2017–2025:** 1,583.5 eligible acres, counted as follows.
    - **Rezoning ordinances:** the City's zoning map amendments (MGO 28.022) passed and enacted 2017–2025, 278 ordinances in all, from the Legistar web API.
    - **Address-matched:** the addresses in 264 titles were matched, placing 247 of those ordinances on lots.
    - **Retired addresses:** when a rezoning's address no longer exists, often because the site was redeveloped, the nearest house number on the same street within 50 numbers is used. That was needed for 137 addresses.
    - **Ordinances without street addresses:** 14 ordinances have none. They are the Town of Madison attachment areas, two other attachments and the UW campus master plan. For the attachments, every lot outside the City's 1 January 2016 boundary (TIGER 2016) counts as rezoned. Its zoning was assigned during the window, and the City's permit report does not cover it before attachment.

## Results

All rates are housing units in permits ÷ eligible acres ÷ years. The estimate is a difference-in-differences (DiD):

(treatment after − treatment before) − (comparison after − comparison before)

The 90% interval comes from redrawing whole projects (permits at the same address in the same year count as one project), 2,000 draws, seed 20261026.

### Rates by year (uniform rule)

Each cell gives units permitted (projects) and units per eligible acre that year.

| Year | Period | Treatment, 614.7 acres | Comparison, 457.5 acres | Second comparison, 6,607.1 acres |
| --- | --- | --- | --- | --- |
| 2017 | before | 171 (4), 0.278 | 236 (3), 0.516 | 756 (68), 0.114 |
| 2018 | before | 115 (3), 0.187 | 5 (2), 0.011 | 467 (82), 0.071 |
| 2019 | before | 133 (2), 0.216 | 80 (1), 0.175 | 489 (77), 0.074 |
| 2020 | before | 44 (1), 0.072 | 0 (0), 0.000 | 750 (100), 0.114 |
| 2021 | before | 229 (4), 0.373 | 570 (9), 1.246 | 819 (61), 0.124 |
| 2022 | before | 150 (3), 0.244 | 341 (1), 0.745 | 896 (68), 0.136 |
| 2023 | after | 222 (2), 0.361 | 343 (2), 0.750 | 222 (18), 0.034 |
| 2024 | after | 251 (5), 0.408 | 399 (3), 0.872 | 399 (22), 0.060 |
| 2025 | after | 572 (7), 0.931 | 50 (1), 0.109 | 536 (22), 0.081 |
| 2026 | shown only (partial) | 1 (1), 0.002 | 47 (1), 0.103 | 713 (23), 0.108 |

- **Treatment:** the mean rate rose from 0.228 units per acre per year in 2017–2022 to 0.567 in 2023–2025. That is 842 units before and 1,045 after.
- **Comparison:** the mean rate rose from 0.449 to 0.577. That is 1,232 units before and 792 after.
- **Few projects:** each area holds only a handful of projects a year: 17 before and 14 after in the treatment, 16 and 6 in the comparison. One building moves a year's rate a lot, which is why the interval is wide.

### Estimates

| Estimate | Homes per eligible acre per year | 90% interval | Per 1.0 added FAR | 90% interval |
| --- | --- | --- | --- | --- |
| **Main** (uniform rule, treatment minus comparison) | +0.210 | −0.437 to +0.807 | +0.215 | −0.448 to +0.826 |
| **Judged** (main, per eligible overlay acre at the overlay dose 0.374) | +0.080 | −0.167 to +0.309 | +0.215 | −0.448 to +0.826 |
| Method A's prediction (committed) | 0.251 | 0.136 to 0.382 | 0.671 | 0.365 to 1.020 |
| Plan's areas as written (all eligible overlay land vs ¼-mile ring of the overlay, no rezoning drop) | +0.003 | −0.348 to +0.340 | +0.009 | −0.932 to +0.908 |
| Second comparison area | +0.385 | +0.079 to +0.706 | +0.394 | +0.081 to +0.723 |
| Plan's areas as written, rest of city as comparison | +0.261 | +0.096 to +0.434 | +0.699 | +0.257 to +1.161 |
| Largest project left out in each area and period | +0.226 | not computed | +0.231 | |
| After = 2024–2025 only (Rapid Route A opened 22 September 2024) | +0.399 | −0.280 to +1.040 | +0.409 | −0.286 to +1.065 |
| Per 1,000 existing homes instead of per acre (4,461 homes in the treatment, 4,399 in the comparison) | +33.3 per 1,000 homes per year | −38.8 to +101.3 | | |

- **How the judged row is computed.** The prediction was written per acre of all eligible overlay land (2,931.7 acres, mean dose 0.374). The uniform rule measures on the 614.7 acres whose density rose (dose 0.977). Method A predicts nothing on land whose density did not rise. So the main estimate is converted to the prediction's basis by multiplying by 0.374 ÷ 0.977. This is the same as comparing the per-FAR effects.
- **The plan's areas as written** give a measured estimate of almost exactly zero, +0.003 (−0.348 to +0.340). The prediction is also inside that interval.
- **Against the rest of the city:** both area rules give a positive effect whose interval excludes zero:
  - +0.385 per treated acre (+0.079 to +0.706) under the uniform rule;
  - +0.261 per eligible overlay acre (+0.096 to +0.434) under the plan's areas as written.

  The second figure is close to the prediction, 0.251. But the rest of the city is less like the overlay than the ring is. Its building dropped from 2023 while the ring's did not, so these are sensitivities, not the main result.

### Ramp check (uniform rule, each after year alone against 2017–2022)

| After year | DiD, homes per eligible acre per year | Per 1.0 added FAR |
| --- | --- | --- |
| 2023 | −0.168 | −0.172 |
| 2024 | −0.243 | −0.249 |
| 2025 | +1.042 | +1.066 |
| 2026 (partial, shown only) | +0.119 | +0.122 |

- **Shape:** the gap is negative in the first two years and large and positive in the third.
- **The comparison cases:** they also show little in years 1 and 2 (the New York pooled ramp is 0.33, 0.31 and 0.89 times r in years 1 to 3).
- **2025's jump:** it comes from seven treatment projects (572 units) in one year, while the ring had one project (50 units).
- **Not enough years:** three after-years are not enough to tell a ramp from noise.

## Threats (plan section 7) as they turned out

- **Rapid Route A** opened 22 September 2024. With 2024–2025 as the after period, the estimate rises to +0.399 (−0.280 to +1.040). That is larger, but just as uncertain.
- **The bundle:** the overlay also removed parking minimums and some conditional-use hearings. The estimate is for the bundle on land whose density rose.
- **Interest rates:** the rest of the city fell from 0.11 units per acre per year (2017–2022) to 0.06 (2023–2025). The ring did not fall. So the ring and the rest of the city do not absorb the rate shock alike, and the main comparison is the ring, as planned.
- **Three after years:** too few. See the ramp check.
- **Address matching:** 98.8% of units were placed. The five large unmatched permits are listed above. Only one, a 2022 permit, could have fallen in the main areas.
- **Rezonings:** the rule takes out lots rezoned in the window. Most large Madison apartment buildings go through a site rezoning, so many big projects leave both areas. That is the rule (the same as in Charlotte, Saint Paul and New York), but it leaves few projects in each area.
- **Placing rezonings:** 137 rezoning addresses were placed by the nearest house number on the street. A wrong placement drops a lot that should stay or keeps one that should go.

## What carries forward

- **The record:** method A is the main method, as GATE3_MODEL_SPEC.md section 9 already set out after method B could not be computed.
- **The brief should say all of these:**
  - the Madison test did not reject method A;
  - the test's interval also contains zero;
  - Madison's measured value per 1.0 of added FAR, 0.215, is nearer the little response than the typical one.
- **For the scenario review:** under the spec, the typical scenario uses "Madison's measured value if the test shows one with a usable dose". The owner should decide whether a value whose interval includes zero is usable. This document does not change the scenarios.
