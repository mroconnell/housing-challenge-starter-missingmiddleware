# ADU predictive test: results

Run 2026-10-28 under [PREDICTIVE_PLAN.md](PREDICTIVE_PLAN.md), written before any outcome was computed. Changes made after it are in its section 10. Code: [`scripts/build_adu_predictive_panel.py`](../../scripts/build_adu_predictive_panel.py), [`scripts/run_adu_predictive.py`](../../scripts/run_adu_predictive.py); tests [`tests/test_adu_predictive.py`](../../tests/test_adu_predictive.py). The adopted ADU outputs (`reference/adu_model_*.csv`) are not touched.

**Units.**
- A **rate** is ADU permits in a year ÷ thousands of one-unit detached homes: "permits per 1,000 single-family homes per year".
- A **miss** is |predicted rate − observed rate|, in that unit.
- A **where-only miss** is the share of a unit's permits predicted in the wrong place (0 = every place right, 1 = all wrong).
- **Additional permits** are Wisconsin with-law permits minus the current-law baseline, summed over 2027–2031.

> **The adopted model changed during this run (AQ-061, committed 2026-10-28 17:35).** Central 8,757 → 10,788 additional permits over 2027–2031; baseline 605 → 530 permits; held-out error 0.113 → 0.180. The changes: reporting-share scale-ups for Maine, Massachusetts, Rhode Island and Utah; Massachusetts 2025 as 11 months; Washington coded from local compliance.
> - **Tests 1–3** were fitted and scored on the **pre-AQ-061** coding: no reporting-share scale-ups, Washington from enactment. The comparison is fair (every method saw the same rows), but it is not the AQ-061 version. Under AQ-061, Maine's, Massachusetts', Rhode Island's and Utah's observed rates would be 20–37% higher, which could change test 1.
> - **The Wisconsin step (section 5)** ran after the change. It uses the AQ-061 inputs and compares with the AQ-061 central (10,788) and AQ-061 county shares.
> - A rerun on AQ-061 coding is needed before any of this goes to the owner as a candidate.

## Flags (owner process rule of 2026-10-28; checked before the run, never stopping it)

All flags: [`reference/adu_predictive_flags.csv`](../../reference/adu_predictive_flags.csv) (27 rows). The rule arrived after the main model run had started; the flags were computed on the same panel and features before the run was rescored (section 10 of the plan).

| Kind | What was found |
| --- | --- |
| Law coded before its date | **None.** Every "law in force" row is on or after the law's first full year. |
| More than 2 ADUs per parcel | Cap applied in the 6 tract cities: 4,693 → 4,437 kept units in Seattle, 1,647 → 1,551 in Portland, 2,811 → 2,661 in Austin, 564 → 533 in Denver, 198 → 164 in Minneapolis (with the vacant-lot and duplex factors). Not possible for Washington, Oregon and the state series (no parcel ids). |
| ADUs on apartment lots | Removed only in California (definite A2 cases) and Minneapolis (duplex factor). Elsewhere they cannot be identified and stay in the counts. |
| Permits with no tract | Austin: 343 of 2,661 kept units (13%) have no point or fall outside the city's tracts and are left out. Other cities: 0–9 units each. |
| Implausible rates | 4 tract-years above 50 permits per 1,000 single-family homes per year (Austin 3, Denver 1): tiny tracts with few detached homes. Kept. |
| Feature units | All shares are in 0–1, all ranks in 0–1, all dollars positive. 13 variable-geography cases have a log ratio below −6 (very small tracts' land area or detached-home count). Kept. |
| Missing inputs | 2–79 of the 1,682 panel geographies lack an ACS dollar median (small tracts, mostly lower rent quartile); filled with the context mean and flagged. |
| Held-out unit far from training | Austin tracts: 38% of home-years outside the training range on "work in place of residence". Oregon cities: 26% of home-years outside on relative detached-home count. No held-out unit's typical value is outside the training 1st–99th percentile on any variable. |

## Summary

- **Two methods pass at least one test; neither is a clear win.**
- **How much (statewide), test 1:** boosted trees pass narrowly, but not robustly.
  - Mean miss 0.123 against the adopted model's 0.127 (−3%) and the plain average's 0.237. It beats both in 4 of 7 states, the minimum.
  - But on log error it is worse than the adopted model (root-mean-square 0.205 against 0.157). It under-predicts **Maine by 33%** and Vermont by 27%. Maine is the state most like Wisconsin.
- **Where (place and tract rates), test 2:** boosted trees and regularised regression pass.
  - Mean miss 0.905 (boosted) and 0.932 (regression) against 1.060 (plain average) and 1.506 (adopted model). Each beats both in 6 of 10 units, the minimum.
  - The adopted model is the worst of all here, worse than guessing zero (1.140): its California-taught value and income slopes push Madison, Minneapolis and Portland tracts far too high.
- **Where only (shares), test 3:** regularised regression passes, barely: 0.367 of permits misplaced against 0.397 (adopted) and 0.411 (plain average); 6 of 10 units.
- **The causal forest fails all three tests.**
- **Nobody predicts Seattle.** Every method misses Seattle's tract rates by about 3 permits per 1,000 single-family homes per year (observed 3.8).
- **Robustness:** the boosted trees' "how much" pass fails with all 5 other seeds, so it is **not robust**. Their "where" pass holds with 4 of 5 seeds.
- **9 chances to pass** (3 methods × 3 tests); 4 passes, each by the smallest margin the rule allows. Some could be chance.
- **Wisconsin (extra lines, nothing replaced):** boosted trees 5,011 and regression 8,479 additional permits over 2027–2031, against the adopted central 10,788 (AQ-061; 8,757 before it). Both are "not validated" for the total. Both move part of the addition from Waukesha County to Milwaukee County (section 5).
- **Bottom line:** keep the adopted model for how much. A flexible model is a candidate only for where, and the two passing methods disagree with each other (Dane County).

## 1. Panel

[`reference/adu_predictive_panel_summary.csv`](../../reference/adu_predictive_panel_summary.csv). 14,224 rows; 210 variable columns built from 100 ACS variables ([`adu_predictive_variables.csv`](../../reference/adu_predictive_variables.csv)).

| Rows | Geographies | Years | Permits (after outcome rules) | Rate |
| --- | ---: | --- | ---: | ---: |
| California jurisdictions | 457 | 2018–2025 | 156,741 | 2.49 |
| Washington cities, before law | 279 | EY2019–2023 | 1,984 | 0.37 |
| Washington cities, law | 279 | EY2024–2026 | 2,345 | 0.74 |
| Oregon cities, law | 32 | 2019–2022 | 1,068 | 0.84 |
| Rhode Island before / law | 1 | 2021–23 / 2025 | 177 / 249 | 0.22 / 0.92 |
| Massachusetts, Maine, Utah, Vermont (law) | 1 each | as adopted | 1,164 / 491 / 2,617 / 139 | 0.75 / 0.93 / 1.07 / 0.90 |
| Honolulu, Montgomery County, Bozeman (no law) | 1 each | 2016–24 / 2019–25 / 2020–23 | 1,676 / 457 / 74 | 1.10 / 0.35 / 1.73 |
| Seattle tracts, before / law | 173 | 2016–23 / 2024 | 3,578 / 851 | 3.53 / 5.87 |
| Portland tracts, law | 162 | 2019–2025 | 1,548 | 1.37 |
| Austin tracts (no law) | 215 | 2012–2023 | 2,318 | 1.00 |
| Denver tracts, before / law | 172 | 2016–23 / 2025 | 418 / 111 | 0.36 / 0.76 |
| Minneapolis tracts (no law) | 121 | 2017–2025 | 164 | 0.22 |
| Madison tracts (no law) | 63 | 2014–2025 | 50 | 0.09 |

Rates are permits per 1,000 single-family homes per year. Washington city counts reproduce the adopted Washington series exactly in every year. Oregon: 18 of 128 city-years fail the DLCD row check and are left out (missing, not zero).

## 2. Test 1: how much (statewide level)

Each state held out of every fit; predicted rate over its law years. [`reference/adu_predictive_by_unit.csv`](../../reference/adu_predictive_by_unit.csv).

| Held-out state | Observed | Plain average | Adopted model (refit) | Causal forest | Boosted trees | Regularised regression |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Washington | 0.74 | 1.12 | 0.86 | 0.96 | **0.74** | 0.72 |
| Oregon | 0.84 | 1.10 | 1.06 | 1.03 | **0.91** | 1.18 |
| Rhode Island | 0.92 | 1.12 | 0.82 | 0.80 | **0.89** | 0.79 |
| Massachusetts | 0.75 | 1.14 | 0.92 | 1.10 | **0.81** | 0.83 |
| Maine | 0.93 | 1.12 | **0.96** | 0.64 | 0.63 | 0.23 |
| Utah | 1.07 | **1.10** | 0.88 | 0.73 | 0.91 | 0.61 |
| Vermont | 0.90 | 1.12 | 0.84 | **0.87** | 0.66 | 1.63 |
| **Mean miss** | | 0.237 | 0.127 | 0.219 | **0.123** | 0.352 |
| States beating both baselines (need 4 of 7) | | | | 2 | **4** | 2 |
| Root-mean-square log error | | 0.277 | **0.157** | 0.283 | 0.205 | 0.634 |
| **Passes** | | | | no | yes (narrowly; not robust: 0 of 5 other seeds) | no |

Rates in permits per 1,000 single-family homes per year. Guess zero misses by 0.880 on average. The adopted model refitted on these rows scores 0.157 rather than its published 0.113, because the rows changed (Washington and Oregon as cities, California coded from 2017, tracts added).

## 3. Tests 2 and 3: where (place and tract level)

| Held-out unit | Observed rate | Rate miss: plain / adopted / forest / boosted / regression / zero | Share misplaced: plain / adopted / forest / boosted / regression |
| --- | ---: | --- | --- |
| Seattle tracts | 3.82 | 3.15 / 2.89 / 3.05 / 3.16 / 3.01 / 3.82 | 0.19 / 0.26 / 0.27 / 0.35 / 0.32 |
| Portland tracts | 1.37 | 0.68 / 3.21 / 0.62 / 1.12 / 0.58 / 1.37 | 0.24 / 0.26 / 0.20 / 0.24 / 0.21 |
| Austin tracts | 1.00 | 1.24 / 1.65 / 1.14 / 0.86 / 0.98 / 1.00 | 0.72 / 0.65 / 0.63 / 0.44 / 0.56 |
| Denver tracts | 0.40 | 0.72 / 0.79 / 0.95 / 0.46 / 0.90 / 0.40 | 0.63 / 0.64 / 0.51 / 0.46 / 0.46 |
| Minneapolis tracts | 0.22 | 0.53 / 1.59 / 0.36 / 0.16 / 0.26 / 0.22 | 0.36 / 0.34 / 0.37 / 0.41 / 0.38 |
| Madison tracts | 0.09 | 0.65 / 1.94 / 0.52 / 0.24 / 0.51 / 0.09 | 0.60 / 0.62 / 0.52 / 0.52 / 0.48 |
| California jurisdictions | 2.49 | 1.87 / 1.71 / 1.75 / 1.69 / 1.83 / 2.48 | 0.38 / 0.29 / 0.29 / 0.29 / 0.34 |
| Washington cities | 0.51 | 0.51 / 0.35 / 0.34 / 0.28 / 0.31 / 0.51 | 0.36 / 0.33 / 0.32 / 0.28 / 0.32 |
| Oregon cities | 0.85 | 0.74 / 0.55 / 0.68 / 0.65 / 0.53 / 0.80 | 0.35 / 0.31 / 0.36 / 0.38 / 0.31 |
| Madison-like cities (24) | 0.70 | 0.54 / 0.38 / 0.40 / 0.43 / 0.41 / 0.71 | 0.29 / 0.28 / 0.30 / 0.36 / 0.30 |

Rate misses are homes-weighted mean |predicted − observed| over the unit's tracts or cities, in permits per 1,000 single-family homes per year.

| Test | Plain average | Adopted model | Causal forest | Boosted trees | Regularised regression | Guess zero |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2: mean rate miss | 1.060 | 1.506 | 0.980 (5 of 10) | **0.905 (6 of 10, passes)** | **0.932 (6 of 10, passes)** | 1.140 |
| 3: mean share misplaced | 0.411 | 0.397 | 0.377 (5 of 10) | 0.373 (5 of 10) | **0.367 (6 of 10, passes)** | — |

"(n of 10)" = units where the method beats both the plain average and the adopted model; 6 needed.

**Reading.**
- On test 2, most of the gain comes from the low-rate no-law cities (Minneapolis, Madison, Denver, Austin), where the adopted model's California slopes overshoot. Guessing zero also beats the adopted model there.
- On test 3 the gains are small: 3 percentage points of permits placed better than the adopted model.
- In the Madison-like cities, the cities most like Madison, the adopted model is the best on both rates and shares.

## 4. Placebo rows (no statewide law)

[`reference/adu_predictive_placebo.csv`](../../reference/adu_predictive_placebo.csv). Each no-law series is predicted from the fit that leaves out its own state.

| Series | Observed | Miss: plain / adopted / forest / boosted / regression | Law effect the two-part method would add: forest / boosted / regression |
| --- | ---: | --- | --- |
| Washington cities before the law | 0.37 | 0.26 / 0.03 / 0.11 / 0.26 / 0.22 | +0.70 / +0.81 / +0.95 |
| Seattle tracts before the law | 3.52 | 2.89 / 2.67 / 2.78 / 2.85 / 2.65 | +0.74 / +0.78 / +0.86 |
| Rhode Island before the law | 0.22 | 0.50 / 0.55 / 0.06 / 0.02 / 0.10 | +0.57 / +0.74 / +0.80 |
| Austin tracts | 1.00 | 0.39 / 0.56 / 0.28 / 0.80 / 0.43 | +0.38 / +0.35 / +1.29 |
| Denver tracts before 2024 | 0.36 | 0.34 / 0.07 / 0.82 / 0.14 / 0.86 | +0.58 / +0.80 / +0.61 |
| Minneapolis tracts | 0.22 | 0.50 / 1.59 / 0.31 / 0.07 / 0.19 | +0.56 / +0.50 / +0.29 |
| Madison tracts | 0.09 | 0.65 / 1.94 / 0.52 / 0.21 / 0.50 | +0.35 / +0.31 / +0.02 |
| Honolulu / Montgomery County / Bozeman | 1.10 / 0.35 / 1.73 | see file | see file |

Rates and effects in permits per 1,000 single-family homes per year; the law effect is at year 4 or later, strong law. None of the no-law parts misses the placebo places much worse than the plain average except the forest and regression in Denver. The effects the two-part methods assign (+0.3 to +1.3) are in the range of the adopted model's law term; Madison gets the smallest (+0.02 to +0.35).

## 5. Wisconsin line (extra, beside the adopted scenarios; nothing replaced)

Computed because methods passed (plan section 8). Files: [`adu_predictive_wi_by_county_boosted_trees.csv`](../../reference/adu_predictive_wi_by_county_boosted_trees.csv), [`adu_predictive_wi_by_county_regularised_regression.csv`](../../reference/adu_predictive_wi_by_county_regularised_regression.csv). Each method was refitted on all rows and applied to Wisconsin's 1,925 areas with a strong law, no local reform and law years 1–5.

**Robustness first (plan section 7).** The boosted trees' test-1 pass holds with **0 of 5** other seeds (mean miss 0.139–0.211 against the adopted model's 0.127), so it is **not robust** and is not brought to the owner. Its test-2 pass holds with 4 of 5 seeds: robust. The regression has no random seed. So both Wisconsin totals below are **"not validated"** for how much; only the "where" part passed.

| Line | Additional permits, 2027–2031 | Rate in 2027 → 2030–31 (per 1,000 single-family homes per year) | Status |
| --- | ---: | --- | --- |
| Adopted central (AQ-061; 8,757 before it) | 10,788 | (adopted) | adopted |
| Boosted trees | 5,011 | 0.55 → 0.65 | not validated (how-much pass not robust) |
| Regularised regression | 8,479 | 0.72 → 1.21 | not validated (passed where only) |

By year, additional permits: boosted 910, 959, 954, 1,095, 1,095; regression 1,218, 1,588, 1,435, 2,119, 2,119.

**Where the additional permits go (share of the state total, central-path county shares).** "At adopted central" = the method's county share × the AQ-061 adopted central, 10,788.

| County | Share of Wisconsin's single-family homes | Adopted model | Boosted trees: share (permits at adopted central) | Regression: share (permits at adopted central) |
| --- | ---: | ---: | --- | --- |
| Milwaukee | 10.5% | 9.1% | 14.2% (1,538) | 17.5% (1,884) |
| Dane | 7.2% | 8.2% | 9.2% (993) | 4.4% (470) |
| Waukesha | 6.6% | 10.3% | 5.9% (640) | 3.0% (323) |
| Brown | 4.0% | 4.1% | 3.7% (397) | 3.6% (386) |
| Racine | 3.3% | 3.2% | 3.2% (345) | 4.0% (436) |
| Kenosha | 2.6% | 2.7% | 3.2% (349) | 2.7% (287) |
| Rock | 2.9% | 2.6% | 3.0% (320) | 3.0% (320) |

- Both methods move permits **toward Milwaukee County and away from Waukesha County** compared with the adopted model, which follows home value more.
- They disagree with each other on Dane County (9.2% against 4.4%).
- Share of the statewide addition that sits in a different county from the adopted model: 11% (boosted) and 22% (regression).
- The adopted county shares are from `reference/adu_model_by_county.csv`, central path, after AQ-061.
- All 72 counties are in the files.

## 6. Why the worst-missed unit was missed (owner process rule)

**Seattle tracts (test 2; every method misses by about 3 permits per 1,000 single-family homes per year).**
- **What happened:** Seattle's rate rose from 1.4–1.7 (2016–2018) to 4.3–5.5 (2021–2023) and 4.8 in 2024. Every method predicts a flat line: the boosted trees give 0.8 in every no-law year and 1.1 in 2024.
- **Missing input:** the strength and date of a city's own reform. Seattle's 2019 ordinance (two ADUs per lot, no owner occupancy, no parking) is coded only as "local reform = 1", the same value it had in 2016. So nothing in the inputs changes in 2019. The same flag covers Minneapolis's and Madison's much weaker rules.
- **Unusual inputs:** compared with the no-law places the models learn from (Austin, Denver, Minneapolis, Madison and the state rows), Seattle's tracts have far more transit commuting (1.6 standard deviations above their typical value), more homes worth $500,000 or more (1.5) and a high value-to-rent ratio (1.2). No training place has Seattle's market, so the models cannot reach its level.
- **Fix to test, written down first:** code local reforms by strength and year (for example the Mercatus or owner-occupancy/parking provisions), as for state laws.

**Maine (test 1; the passing boosted trees' worst state, 0.63 predicted against 0.93 observed).**
- Maine's seasonal-vacancy share (15.3% of homes) is above 97% of the law-in-force training rows; its share of homes worth under $200,000 (30%) is above 95% of them. The law-part training rows are mostly Californian. The trees treat seasonal, lower-value housing as low-ADU housing.
- This matters for Wisconsin, whose seasonal and lower-value housing is closer to Maine's than to California's.

## 7. What this means

- **For "how much":** the adopted model stays. The boosted-tree pass is 3% on the plan's measure, fails with every other seed and reverses on log error, driven by under-predicting Maine and Vermont.
- **For "where":** there is a modest, real-looking gain over the adopted model in low-rate, no-law cities and in where permits go. It comes from not extrapolating California's slopes. The adopted model's statewide total does not use those slopes much (its allocation already uses a gentler value-only gradient).
- **Limits (plan section 9):** the level still rests on 8 statewide-law states; tracts exist for 6 large cities only; data types differ (estimate years, self-reports, undercounts); one ACS snapshot for all years.

## Reproduce

```
set -a; source .env; set +a
uv run --all-extras python scripts/build_adu_predictive_panel.py --fetch   # once: ACS API, TIGER tracts, permit points
uv run --all-extras python scripts/build_adu_predictive_panel.py
uv run --all-extras python scripts/run_adu_predictive.py                   # add --reuse to rescore saved predictions
bash scripts/test.sh
```
