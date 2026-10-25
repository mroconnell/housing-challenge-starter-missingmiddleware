# ADUs on multifamily lots, the benchmark cap, and ADU order on the parcel

Prepared 2026-10-25. Status: analysis for the owner. It does not change the pooled model or the engine. It gives adjusted California inputs to use if the owner adopts them.

**The question.** California's ADU counts (HCD APR Table A2, `UNIT_CAT == "ADU"`) can include ADUs on multifamily lots. Gov. Code 66323 (SB 13/AB 68, from 2020) lets a multifamily property convert non-living space into ADUs (up to 25% of its existing units) and add two detached ADUs. The challenge benchmark is one ADU on a parcel with an existing single-family home. The pooled model divides ADUs by one-unit detached homes, so ADUs on multifamily lots inflate California's rate. The current study (`TEXT_RULES` in `ca_study.py`) removes only the ADUs whose text names a multifamily lot, under 1% of units.

**Owner decisions applied here:**
- Use A2, ACS and Census data already in the repo: (a) APN rules within A2 and (b) an ACS ecological check. No text matching beyond `TEXT_RULES`.
- Use one Los Angeles County Assessor check, as validation only. It is not a pipeline input, and no other assessor is used.
- Rule cutoff **2023-01-01**, when HCD began saying a single-family lot could have three ADUs (owner-provided: the owner's report, https://youtube.com/shorts/fiYxXHoHpLQ, January 2023). 2021-01-01 and 2022-01-01 are sensitivities.
- **Benchmark cap:** count at most 2 ADU units per parcel, cumulated across 2018–2025. Anything beyond is outside the benchmark, whatever the lot type.

**Units and base.** Every count is **ADU building-permit units** in the study's main measure (`adu_main`): A2 rows with `UNIT_CAT` ADU and building-permit units above 0, the permit dated in the report year or undated, and the permit not excluded by `TEXT_RULES`.
- That base is 170,482 units over 2018–2025. It reproduces `hcd_adu_outcome.parquet` exactly (0 units' difference in every jurisdiction-year).
- Rates are ADU units per 1,000 one-unit detached homes (ACS 2020–2024 B25024) per year, summed over jurisdictions with an observed count, as in the study panel.
- "Share" always means ADU units in the group ÷ all ADU units in the base for that year or place.

Code: [`missing_middleware/comparison/ca_mf_lot.py`](../../missing_middleware/comparison/ca_mf_lot.py), [`scripts/run_ca_mf_lot.py`](../../scripts/run_ca_mf_lot.py), [`scripts/fetch_la_assessor_validation.py`](../../scripts/fetch_la_assessor_validation.py). Tests: [`tests/test_ca_mf_lot.py`](../../tests/test_ca_mf_lot.py), on a synthetic A2 fixture. APNs are read only in memory; every committed file is a count by jurisdiction and year.

## Headline

- **About a fifth of California's recent ADU permits are on multifamily lots, far more than the A2-only rules can see.**
  - **Los Angeles County Assessor check** (validation only): 14,056 of 76,197 matched ADU units in 2018–2025 (18.4%) were on parcels with 2 or more existing units, at the roll before the permit. The match rate is 76,197 of 77,516 = 98.3%.
    - 2018: 86 of 4,898 = 1.8%. 2025: 3,109 of 13,433 = 23.1%. The peak is 2023, at 3,032 of 12,127 = 25.0%.
    - City of Los Angeles, 2023–2025: 5,609 of 20,824 = 26.9%.
  - **A2 APN rule alone** (3+ ADU units on one APN-year before 2023, 4+ from 2023):
    - Lower bound 7,094 of 170,482 statewide units = 4.2%, rising from 1.6% (2018) to 5.9% (2025).
    - Upper bound 16,682 = 9.8%.
    - In LA County, 2023–2025, the rule's lower bound is 1,651 of 39,080 = 4.2% against the assessor's 24.0%. It finds only 11% of the multifamily-lot units, though 80% of what it flags is right.
  - **Statewide estimate**, 2023–2025: **21.3%** of ADU units (19,297 of 90,539), range 13.8% to 24.1%. This uses LA County as measured, plus the rest of the state calibrated to LA's results by A2 flag and local multifamily housing share. It is validation-informed, not an A2-only number.
- **The benchmark cap** (at most 2 ADU units per parcel, cumulated) removes 6,237 of 170,482 units (3.7%), and 4,749 of 90,539 (5.2%) in 2023–2025. 78% of what it removes is on APNs the A2 rule already calls multifamily.
  - Outside California the cap removes under 1% (Seattle 0.6%, Portland 0.3%, Austin 0.25%, Denver 0.6%, Minneapolis 0, Madison 1.0%).
- **Adjusted California plateau** (all grouped non-holdout jurisdictions, 2023–2025; was 3.84 ADU units per 1,000 one-unit detached homes per year):
  - Cap only: **3.63** (72,635 ÷ 20.01 million home-years).
  - Cap + A2 multifamily lower bound: **3.57**.
  - Cap + A2 upper bound: **3.42**.
  - Cap + LA-calibrated central: **2.93** (58,565 ÷ 20.01 million).
  - Statewide, all jurisdictions: 3.67 → 3.48 (cap) → **2.82** (cap + calibrated).
- **Uplift by ADU order:** of the rise from 2018 (1.10) to 2023–2025 (3.67 per 1,000 homes a year), 77% is parcels' 1st ADUs, 15% 2nd ADUs (some may be JADUs) and 7% 3rd-or-later.
- **Outside California:**
  - Minneapolis counts ADUs on duplex lots (about 13%).
  - Rhode Island's law allows ADUs with multi-unit dwellings but its data cannot show them.
  - The other sources are within 0–4%.
- **The ACS ecological check cannot settle this.** It finds a multifamily-share effect that was already there in 2018–2019 and that barely changes after 2020 (implied 3%, 80% range −29% to +25%). That contradicts the LA measurement, which jumps from 2% to 24%.

## 1. APN rules within Table A2 (method a)

**Rules** (`apn_year_band`, `mf_unitcat`). APNs are normalized to letters and digits. Placeholders are treated as unknown: fewer than 5 characters, one repeated character (`0`, `0000000000`), no digit, or words such as `TBD`. That is 1,028 units (0.6%). The rules count ADU units on one APN in one jurisdiction-year:

| Report year | "Possible" multifamily lot | "Definite" multifamily lot | Why |
| --- | --- | --- | --- |
| Before the cutoff | 2 units | 3 or more | A single-family lot could hold an ADU plus a JADU from 2020, so 2 is ambiguous |
| From the cutoff (2023) | 3 units | 4 or more | From 2023 HCD read the law to allow up to 3 ADUs on a single-family lot |

A second, independent rule counts as **possible**: **the same APN appears in A2, in any year, with `UNIT_CAT` "2 to 4" or "5+"**. It was planned as definite, but the LA check (§5) shows only 31–44% of the units it flags are on multifamily lots. Many are single-family lots where the house, an ADU and a JADU were also listed as a 2-to-4 project.
- **Lower bound** = definite units (APN-year rule).
- **Upper bound** = definite plus possible units (either rule).

**Statewide, main cutoff 2023-01-01** ([`reference/ca_mf_lot_adu_share_by_year.csv`](../../reference/ca_mf_lot_adu_share_by_year.csv)). All columns are ADU units:

| Year | All ADU units | APN-year definite | APN-year possible | Same APN has a 2-to-4 or 5+ listing | **Lower bound (definite)** | **Upper bound (definite + possible)** |
| --- | --- | --- | --- | --- | --- | --- |
| 2018 | 8,863 | 144 | 198 | 57 | 144 = **1.6%** | 385 = **4.3%** |
| 2019 | 12,616 | 247 | 474 | 107 | 247 = **2.0%** | 780 = **6.2%** |
| 2020 | 12,650 | 229 | 540 | 183 | 229 = **1.8%** | 868 = **6.9%** |
| 2021 | 20,482 | 790 | 1,448 | 455 | 790 = **3.9%** | 2,421 = **11.8%** |
| 2022 | 25,332 | 921 | 2,172 | 614 | 921 = **3.6%** | 3,513 = **13.9%** |
| 2023 | 28,256 | 1,195 | 327 | 789 | 1,195 = **4.2%** | 2,175 = **7.7%** |
| 2024 | 30,338 | 1,693 | 507 | 1,055 | 1,693 = **5.6%** | 3,049 = **10.1%** |
| 2025 | 31,945 | 1,875 | 681 | 1,339 | 1,875 = **5.9%** | 3,491 = **10.9%** |
| 2018–2025 | 170,482 | 7,094 | 6,347 | 4,599 | 7,094 = **4.2%** | 16,682 = **9.8%** |

The upper bound counts a unit once even when both rules flag it, so the columns do not add. The upper bound drops in 2023 because the rule changes: from 2023, 2 units on one APN no longer count as possible.

**Cutoff sensitivity** (lower / upper bound, as a share of ADU units). Changing the cutoff moves only the years between the alternatives:

| Cutoff | 2021 | 2022 | 2023–2025 and 2018–2020 |
| --- | --- | --- | --- |
| 2021-01-01 | 592 / 1,067 of 20,482 = 2.9% / 5.2% | 633 / 1,441 of 25,332 = 2.5% / 5.7% | as in the main table |
| 2022-01-01 | 790 / 2,421 = 3.9% / 11.8% (as main) | 633 / 1,441 = 2.5% / 5.7% | as in the main table |
| **2023-01-01 (main)** | 790 / 2,421 = 3.9% / 11.8% | 921 / 3,513 = 3.6% / 13.9% | as in the main table |

Over 2018–2025 the lower / upper bound is 6,608 / 13,256 units (3.9% / 7.8%) with a 2021 cutoff, 6,806 / 14,610 (4.0% / 8.6%) with 2022, and 7,094 / 16,682 (4.2% / 9.8%) with 2023.

**Cumulative view.** Counting each APN's ADU units across all of 2018–2025, units on APNs with 4 or more ADU units over the period are 7,097 of 170,482 = 4.2%. Units on APNs with 3 or more are 10,901 = 6.4%. By year, the 4-or-more share rises from 103 of 8,863 = 1.2% (2018) to 1,989 of 31,945 = 6.2% (2025).

**What the APN rule cannot see:**
- 1–2 ADUs on a multifamily lot (the two detached ADUs SB 13 allows, or a small conversion). This is the main gap, and the LA check measures it.
- A jurisdiction that lists one ADU per row under an old master APN for a subdivision. Those are ADUs built with new houses, still outside the benchmark, but not on a multifamily lot.
- APNs typed differently in different years. These go undetected, so the rule is conservative.

**Largest jurisdictions** (2018–2025; lower / upper bound as a share of ADU units, in [`reference/ca_mf_lot_adu_share_by_jurisdiction.csv`](../../reference/ca_mf_lot_adu_share_by_jurisdiction.csv)):

| Jurisdiction | ADU units | Lower bound | Upper bound | Cap removes |
| --- | --- | --- | --- | --- |
| Los Angeles (city) | 45,522 | 1,634 = 3.6% | 5,801 = 12.7% | 1,651 = 3.6% |
| San Diego (city) | 9,126 | 2,005 = 22.0% | 2,646 = 29.0% | 1,552 = 17.0% |
| Los Angeles County (unincorporated) | 5,831 | 73 = 1.3% | 344 = 5.9% | 94 = 1.6% |
| Long Beach | 3,493 | 105 = 3.0% | 353 = 10.1% | 91 = 2.6% |
| San Jose | 3,317 | 44 = 1.3% | 91 = 2.7% | 39 = 1.2% |
| Santa Maria | 2,494 | 0 | 214 = 8.6% | 49 = 2.0% |
| San Francisco | 2,356 | 755 = 32.0% | 1,255 = 53.3% | 448 = 19.0% |
| Garden Grove | 2,341 | 15 = 0.6% | 77 = 3.3% | 12 = 0.5% |
| San Diego County (unincorporated) | 2,313 | 0 | 37 = 1.6% | 1 = 0.0% |
| Glendale | 1,714 | 7 = 0.4% | 119 = 6.9% | 12 = 0.7% |
| Burbank | 1,637 | 14 = 0.9% | 83 = 5.1% | 19 = 1.2% |
| Sacramento (city) | 1,587 | 136 = 8.6% | 275 = 17.3% | 97 = 6.1% |

By the A2 rule, multifamily-lot ADUs are concentrated in San Francisco, San Diego and Sacramento, where several ADUs are permitted on one APN at once. That is the pattern of the 25% conversion route. The LA check (§5) shows the rule sees only a small part of the multifamily-lot ADUs in places like Los Angeles, where they come one or two per parcel.

## 2. ACS ecological check (method b)

**Specification** ([`reference/ca_mf_lot_adu_share_acs_ecological.csv`](../../reference/ca_mf_lot_adu_share_acs_ecological.csv)):
- Across the 457 California jurisdictions, a Poisson model of ADU units, with exposure = one-unit detached home-years.
- Regressors: the share of housing units in 2-or-more-unit structures (ACS B25024 E004–E009 ÷ E001; median 22%), plus the pooled model's within-state terms (log value, log income, log size), optionally with the study's pre-law group.
- If ADUs on multifamily lots are in the numerator, places with more multifamily housing should have higher rates.
- Implied multifamily-lot share = 1 − (predicted units with the multifamily share set to 0) ÷ (predicted units).

| Window | Coefficient on multifamily share (robust SE) | Implied share of ADU units | 80% range |
| --- | --- | --- | --- |
| 2014–2016 (before the 2017 law; ADUs were for single-family lots only) | −2.59 (1.77) | negative | — |
| 2018–2019 (before SB 13 opened multifamily structures) | +1.00 (0.42) | 34% | 18% to 47% |
| 2020–2022 | +1.11 (0.32) | 34% | 23% to 43% |
| 2023–2025 | +1.07 (0.39) | 32% | 19% to 43% |
| **2023–2025 minus 2018–2019** (the change after multifamily lots opened) | **+0.07 (0.57)** | **3%** | **−29% to +25%** |

The rows use the value + income + size specification and all jurisdictions. With the pre-law group added, or Los Angeles city left out, the 2023–2025 level is 24–30% and the change is 5–12%, with similar ranges.

**How weak this is: very.** The LA County Assessor check (§5) confirms it:
- The level coefficient is already +1.0 in 2018–2019. At that time A2 flags only 1.6–2.0% of units as definitely multifamily, the LA County Assessor shows 1.8–2.1%, and SB 13 had not yet opened multifamily structures. So the level mostly measures something else that comes with multifamily housing: older, denser, urban neighbourhoods, smaller lots near transit, and Los Angeles's early start.
- The only part attributable to multifamily lots is the **change** after 2020. It is +0.07 ± 0.57 on the log scale, an implied 3% with an 80% range from −29% to +25%. In LA County the measured share went from 2% to 24% over the same years, so the ecological change misses a real, large effect. Across jurisdictions, multifamily-lot ADUs grew while other ADUs in multifamily-heavy places grew more slowly, and the two cancel in the cross-section.
- The fit is also over-dispersed (dispersion 34–86), and the multifamily share is an ACS 2020–2024 snapshot.
- **Use:** none. The ecological check is reported because the owner asked for it, and it is not used in the adjusted inputs.

## 3. Benchmark cap: at most 2 ADU units per parcel

**Rule** (`add_order`):
- ADU units are ordered on their parcel (jurisdiction + APN) by report year, permit date and permit, cumulated across 2018–2025.
- The 1st and 2nd units are kept; the 3rd and later are removed.
- A permit with 3 units on a fresh parcel keeps 2 and loses 1.
- Units with an unknown APN cannot be ordered. They are kept and counted as 1st ADUs.

| Year | ADU units | (1) Removed by the cap | (2) Share removed | (3) Of the removed, on APNs the A2 rules call definite multifamily | Kept 1st–2nd ADUs on definite APNs (still multifamily) | Kept 1st–2nd ADUs on "possible" APNs |
| --- | --- | --- | --- | --- | --- | --- |
| 2018 | 8,863 | 76 | 0.9% | 76 | 68 | 241 |
| 2019 | 12,616 | 145 | 1.1% | 130 | 117 | 523 |
| 2020 | 12,650 | 136 | 1.1% | 131 | 98 | 636 |
| 2021 | 20,482 | 513 | 2.5% | 485 | 305 | 1,609 |
| 2022 | 25,332 | 618 | 2.4% | 543 | 378 | 2,542 |
| 2023 | 28,256 | 1,127 | 4.0% | 864 | 331 | 849 |
| 2024 | 30,338 | 1,743 | 5.7% | 1,261 | 432 | 1,136 |
| 2025 | 31,945 | 1,879 | 5.9% | 1,358 | 517 | 1,322 |
| 2018–2025 | 170,482 | 6,237 | 3.7% | 4,848 | 2,246 | 8,858 |

All columns are ADU units. The share in (2) is removed ÷ ADU units. (Source: [`reference/ca_mf_lot_adu_share_by_year.csv`](../../reference/ca_mf_lot_adu_share_by_year.csv), main cutoff.)

**Overlap.** 4,848 of the 6,237 units the cap removes (78%) are on APNs the A2 rule already calls definitely multifamily. After the cap, the remaining multifamily question is only about the 1st and 2nd ADUs on each parcel:
- **2,246 units** on APNs flagged definite (3+/4+ in one year, with the excess removed by the cap).
- **8,858 units** on "possible" APNs: 2-unit APN-years before 2023, 3-unit APN-years from 2023, or a 2-to-4/5+ listing on the APN.
- Plus the 1–2-ADU multifamily lots the A2 rules cannot see. In LA County these are most of them (§5): of the units the cap keeps, 8,044 of 36,623 matched units (22.0%) were on multifamily lots in 2023–2025.

**Other places with parcel-level data, same rule** ([`reference/ca_mf_lot_adu_share_other_sources.csv`](../../reference/ca_mf_lot_adu_share_other_sources.csv)). All figures are counted ADU units removed ÷ counted ADU units over all data years.

| Place | Removed by the cap | Note |
| --- | --- | --- |
| Seattle | 29 of 4,788 = 0.6% | Peak years: 2022 10 of 546 = 1.8%; 2023 12 of 627 = 1.9%. The removed units are unit-lot and redevelopment permits listing 3–6 ADUs. Keyed by address, because the extract has no parcel number. |
| Portland | 13 of 4,090 = 0.3% | 1 of 4,090 once parent parcels of land divisions are split by address |
| Austin | 3 of 1,199 = 0.25% | 1 of 1,199 split by address |
| Denver | 5 of 782 = 0.6% | 0 of 782 split by address; the removals come from master parcels |
| Minneapolis | 0 of 201 | Its classifier already allows one ADU per APN per 24 months |
| Madison | 1 of 102 = 1.0% | The one removal is in the 2026 templated twin-home programme; 0 of 40 in 2022–2025 |
| Sun Prairie, Pleasant Prairie, Kaukauna, Watertown, Milwaukee | 0 of 69 | Other Wisconsin cities have 0 counted units |

The cap matters only in California, where it removes 4.0–5.9% of 2023–2025 units. Everywhere else it is under 1% overall and mostly data artifacts.

## 4. How much of the uplift comes from parcels getting more than one ADU

The same ordering splits ADU units into each parcel's 1st, 2nd, and 3rd-or-later ADU ([`reference/ca_mf_lot_adu_share_rates_by_year.csv`](../../reference/ca_mf_lot_adu_share_rates_by_year.csv), [`reference/ca_mf_lot_adu_share_order_decomposition.csv`](../../reference/ca_mf_lot_adu_share_order_decomposition.csv)). Rates are ADU units per 1,000 one-unit detached homes per year; the denominator is 8.06–8.24 million homes.

| Year | 1st ADU: units (share), rate | 2nd ADU: units (share), rate | 3rd: units, rate | 4th or later: units, rate |
| --- | --- | --- | --- | --- |
| 2018 | 8,654 (97.6%), 1.07 | 133 (1.5%), 0.02 | 34, 0.004 | 42, 0.005 |
| 2019 | 12,083 (95.8%), 1.48 | 388 (3.1%), 0.05 | 72, 0.009 | 73, 0.009 |
| 2020 | 11,995 (94.8%), 1.47 | 519 (4.1%), 0.06 | 53, 0.006 | 83, 0.010 |
| 2021 | 18,761 (91.6%), 2.28 | 1,208 (5.9%), 0.15 | 180, 0.022 | 333, 0.040 |
| 2022 | 22,950 (90.6%), 2.80 | 1,764 (7.0%), 0.22 | 250, 0.030 | 368, 0.045 |
| 2023 | 24,297 (86.0%), 2.95 | 2,832 (10.0%), 0.34 | 387, 0.047 | 740, 0.090 |
| 2024 | 25,191 (83.0%), 3.06 | 3,404 (11.2%), 0.41 | 637, 0.077 | 1,106, 0.134 |
| 2025 | 26,089 (81.7%), 3.19 | 3,977 (12.4%), 0.49 | 719, 0.088 | 1,160, 0.142 |

The 1st-ADU column includes units with an unknown APN, which cannot be ordered: 6 (2018), 28, 34, 177, 99, 647, 12 and 25 (2025).

**Decomposition of the rise** (rate per 1,000 one-unit detached homes per year):

| From → to | Total rise | From 1st ADUs | From 2nd ADUs | From 3rd-or-later ADUs |
| --- | --- | --- | --- | --- |
| 2018 (1.10) → 2023–2025 mean (3.67) | +2.57 | +1.99 = **77%** | +0.40 = **15%** | +0.18 = **7%** |
| 2014–2016 mean (0.12) → 2023–2025 mean (3.67) | +3.55 | +2.94 = **83%** | +0.42 = **12%** | +0.19 = **5%** |

The 2014–2016 base comes from the 2012–2019 compilation, which has no APNs. It assumes all of those units were 1st ADUs, so it slightly overstates the 1st-ADU share of the rise.

**Reading it with and without the 2023 rule change:**
- **Without the rule change in mind** (a single-family lot holds 1 ADU, plus a JADU from 2020):
  - Every 3rd-or-later ADU is outside a single-family allowance.
  - A 2nd ADU is within it only if it is a JADU. A2's `ADU` category can include JADUs and does not separate them, so a 2nd ADU is either a JADU on a single-family lot or a 2nd ADU on a multifamily lot.
  - Then 15% of the 2018 → 2023–2025 rise is "maybe a JADU" and 7% is outside the allowance.
- **With the rule change in mind** (3 ADUs per single-family lot from 2023):
  - The 3rd ADUs of 2023–2025 (0.07 per 1,000 a year on average) become single-family-compatible.
  - Only 4th-or-later ADUs (0.12 per 1,000 a year) are clearly outside.
  - The benchmark cap ignores this, by the owner's direction, and removes every 3rd ADU.

**Other cities**, from the cap run (counted ADU units; share of the rise in units per year between the windows shown):

| City (windows) | 1st ADUs | 2nd ADUs | 3rd-or-later ADUs |
| --- | --- | --- | --- |
| Seattle (2016–18 → 2021–24) | 89.1% | 8.9% | 1.9% |
| Portland (2012–14 → 2016–18; parent parcels split by address) | 99.7% | 0.3% | 0% |
| Austin (2012–14 → 2016–19) | 99.8% | 0.2% | 0% |
| Denver (2016–22 → 2023–25; split by address) | 94.1% | 5.9% | 0% |
| Madison (2014–19 → 2023–25) | 96.2% | 3.8% | 0% |
| Minneapolis (2017–20 → 2021–25) | the count fell, by 12.65 units a year; 1st ADUs fell 14.05 a year and 2nd ADUs rose 1.4 a year | | |

Outside California, the rise is almost all 1st ADUs. In California, 1st ADUs account for 77–83% of the rise. The rest comes from parcels that add a second or third ADU, increasingly so after 2023.

## 5. Los Angeles County Assessor check (validation only)

**Source.** LA County Assessor parcel rolls 2018–2025, from the county open-data hub. The query asked only for the 67,735 distinct 10-digit AINs that carry an A2 ADU permit in an LA County jurisdiction, and only for use-code and building fields; the AINs are LA County's 10-digit APNs. It is a one-time download, owner-approved as **validation only** ([`DATA_PROVENANCE.md`](../DATA_PROVENANCE.md); raw files in git-ignored `data/raw/la_county_assessor_rolls/` with `_downloads.json`).
- Each permit's parcel is classed by the **roll of its report year** (lien date 1 January, before the permit is issued).
- Use code 01xx = single-family residence; 02xx = two units; 03xx/04xx = three/four units; 05xx = five or more (all three are "multifamily lot"); 010C/01DC = condominium; a trailing V = vacant; 07xx = manufactured home; anything else = other use. The inventory is in [`reference/ca_mf_lot_adu_share_la_use_codes.csv`](../../reference/ca_mf_lot_adu_share_la_use_codes.csv).
- **Recoding check:** an ADU added to a single-family parcel could have recoded it to "two units" before a later permit. Classing every parcel by its **2018** roll instead, before almost all of these ADUs, gives 9,062 of 38,436 = 23.6% on multifamily lots in 2023–2025, against 24.0% at the permit-year roll. So recoding does not drive the result.

**Single-family vs multifamily lot, LA County** ([`reference/ca_mf_lot_adu_share_la_assessor.csv`](../../reference/ca_mf_lot_adu_share_la_assessor.csv); by jurisdiction and year, and 2018–2025 for each of the 88 LA County jurisdictions). Shares are of matched ADU units:

| Year | ADU units | Matched (match rate) | Single-family lot | Multifamily lot (2+ units) | of which 2 units / 3–4 / 5+ | Other or unknown (vacant, condo, other use) |
| --- | --- | --- | --- | --- | --- | --- |
| 2018 | 4,951 | 4,898 (98.9%) | 4,786 = 97.7% | 86 = 1.8% | 68 / 14 / 4 | 26 = 0.5% |
| 2019 | 6,767 | 6,723 (99.3%) | 6,523 = 97.0% | 141 = 2.1% | 126 / 14 / 1 | 59 = 0.9% |
| 2020 | 5,618 | 5,507 (98.0%) | 4,925 = 89.4% | 528 = 9.6% | 276 / 87 / 165 | 54 = 1.0% |
| 2021 | 9,167 | 8,811 (96.1%) | 7,112 = 80.7% | 1,490 = 16.9% | 614 / 377 / 499 | 209 = 2.4% |
| 2022 | 11,933 | 11,822 (99.1%) | 9,000 = 76.1% | 2,586 = 21.9% | 1,002 / 614 / 970 | 236 = 2.0% |
| 2023 | 12,246 | 12,127 (99.0%) | 8,705 = 71.8% | 3,032 = 25.0% | 1,134 / 727 / 1,171 | 390 = 3.2% |
| 2024 | 13,133 | 12,876 (98.0%) | 9,381 = 72.9% | 3,084 = 24.0% | 1,123 / 791 / 1,170 | 411 = 3.2% |
| 2025 | 13,701 | 13,433 (98.0%) | 10,013 = 74.5% | 3,109 = 23.1% | 1,220 / 849 / 1,040 | 311 = 2.3% |
| 2018–2025 | 77,516 | 76,197 (98.3%) | 60,445 = 79.3% | 14,056 = 18.4% | 5,563 / 3,473 / 5,020 | 1,696 = 2.2% |

**By jurisdiction, 2023–2025** (multifamily-lot units ÷ matched units):
- City of Los Angeles: 5,609 of 20,824 = 26.9%. By year from 2018: 1.4%, 1.4%, 11.2%, 20.1%, 26.2%, 30.1%, 27.0%, 24.1%.
- Long Beach: 701 of 2,048 = 34.2%.
- Glendale: 238 of 860 = 27.7%.
- Pasadena: 129 of 603 = 21.4%.
- Other LA County cities together: 1,764 of 9,272 = 19.0%.
- LA County unincorporated: 639 of 3,453 = 18.5%.
- Burbank: 120 of 802 = 15.0%.
- Lancaster: 25 of 574 = 4.4%. Lancaster's match rate is only 73%, because new tract parcels are not yet on the roll, and 243 of its units are on vacant lots (ADUs built with new houses).

Excluding duplexes (counting only 3+ unit lots), LA County 2023–2025 is 5,748 of 38,436 = 15.0%. Two-unit lots alone are 3,477 = 9.0%. A two-unit code can be a house plus an older legal second unit or two houses on one lot. Neither is the benchmark's "one ADU on a parcel with an existing single-family home", but the owner may want to see the 3+ figure separately.

**How well the A2 APN rule agrees** ([`reference/ca_mf_lot_adu_share_la_rule_check.csv`](../../reference/ca_mf_lot_adu_share_la_rule_check.csv)). Matched LA County units, by ADU units on the APN in that year, shown as single-family-lot units ÷ matched units (and multifamily-lot share):

| Year | 1 unit on the APN | 2 units | 3 units | 4+ units |
| --- | --- | --- | --- | --- |
| 2018 | 4,735/4,843 SF (98%); MF 2% | 48/52 SF (92%); MF 0% | 3/3 SF; MF 0% | — |
| 2019 | 6,350/6,548 SF (97%); MF 2% | 152/154 SF (99%); MF 1% | 21/21 SF; MF 0% | — |
| 2020 | 4,767/5,220 SF (91%); MF 8% | 144/220 SF (65%); MF 34% | 3/18 SF (17%); MF 67% | 11/49 SF (22%); MF 78% |
| 2021 | 6,750/7,876 SF (86%); MF 13% | 318/668 SF (48%); MF 49% | 9/75 SF (12%); MF 76% | 35/192 SF (18%); MF 44% |
| 2022 | 8,584/10,464 SF (82%); MF 16% | 360/1,044 SF (34%); MF 63% | 24/135 SF (18%); MF 76% | 32/179 SF (18%); MF 77% |
| 2023 | 8,040/9,785 SF (82%); MF 16% | 580/1,740 SF (33%); MF 57% | 30/150 SF (20%); MF 76% | 55/452 SF (12%); MF 80% |
| 2024 | 8,148/9,708 SF (84%); MF 14% | 1,126/2,350 SF (48%); MF 48% | 63/297 SF (21%); MF 67% | 44/521 SF (8%); MF 71% |
| 2025 | 8,561/10,119 SF (85%); MF 14% | 1,188/2,334 SF (51%); MF 46% | 186/393 SF (47%); MF 47% | 78/587 SF (13%); MF 77% |

**What this says about the rule:**
- **Before 2020, 2–3 ADUs on one APN were single-family lots** (92–100%): ADU + JADU, or ADUs built with new houses. SB 13 opened multifamily structures in 2020; from then on, 3 and 4+ per APN-year are 67–80% multifamily.
- **The 2023 cutoff shows in the data.** 3-unit APNs on single-family lots went from 12–21% (2021–2024) to 47% in 2025, as the three-ADU reading spread. So "3 = possible from 2023" is right, and "3 = definite before 2023" is right from 2020.
- **A 2-unit APN is a coin toss from 2021** (46–63% multifamily). "Possible" is the right label.
- **Precision is good, recall is poor.**
  - The definite band is right 72% (2018–2022: 328 of 456) and 80% (2023–2025: 1,038 of 1,295) of the time.
  - But it catches only 328 of 4,831 multifamily-lot units in 2018–2022 (7%) and 1,038 of 9,225 in 2023–2025 (11%).
  - Most multifamily-lot ADUs are 1 per APN-year: 7,001 of 9,225 in 2023–2025. That is 20.5% of all single-unit APN-years.
- **The unit-category flag is weak.** Of units on APNs that also have a 2-to-4 or 5+ listing, only 410 of 940 (2018–2022) and 751 of 2,420 (2023–2025) are on multifamily lots. It is therefore treated as "possible".
- **As a statewide fallback, the APN rule is a firm lower bound but not an estimate.** It understates the LA County share by a factor of about 6: 1,651 of 39,080 = 4.2% against 24.0%. For the City of Los Angeles it is 1,218 of 21,015 = 5.8% against 26.9%.

**The 1–2-ADU group the cap keeps.** Of matched units kept by the cap in LA County, the share on multifamily lots by year is: 2018 86 of 4,897 = 1.8%; 2019 141 of 6,706 = 2.1%; 2020 492 of 5,461 = 9.0%; 2021 1,412 of 8,622 = 16.4%; 2022 2,456 of 11,627 = 21.1%; 2023 2,711 of 11,707 = 23.2%; 2024 2,670 of 12,163 = 22.0%; 2025 2,663 of 12,753 = 20.9%. Leaving out those on APNs flagged definite, it is 7,110 of 34,135 = 20.8% (2023–2025). **So the cap removes little of the multifamily-lot problem in LA County; most of it is 1–2 ADUs on a multifamily parcel.**

**Against (a) and (b) for the same places**, 2023–2025 (shares of ADU units):

| | A2 lower bound | A2 upper bound | ACS ecological, change after 2020 | ACS ecological, level | Assessor |
| --- | --- | --- | --- | --- | --- |
| LA County, all jurisdictions | 1,651 of 39,080 = 4.2% | 4,483 = 11.5% | 3% statewide (80% range −29% to +25%) | 32% statewide (19% to 43%) | 9,225 of 38,436 matched = 24.0% |
| City of Los Angeles | 1,218 of 21,015 = 5.8% | 3,488 = 16.6% | — | — | 5,609 of 20,824 = 26.9% |

The assessor result is above the A2 upper bound. It matches the ecological *level*, but that is chance: the level was already 34% in 2018–2019, when the assessor shows 2%.

## 6. Statewide multifamily-lot share, with a range

**Method** ([`reference/ca_mf_lot_adu_share_statewide_range.csv`](../../reference/ca_mf_lot_adu_share_statewide_range.csv); calibration in [`reference/ca_mf_lot_adu_share_la_calibration_bands.csv`](../../reference/ca_mf_lot_adu_share_la_calibration_bands.csv) and [`ca_mf_lot_adu_share_la_calibration_fit.csv`](../../reference/ca_mf_lot_adu_share_la_calibration_fit.csv)):
- **LA County** (77,516 of 170,482 statewide units, 45.5%): the assessor-measured multifamily share of matched units, applied to all its units.
- **Rest of the state**, by A2 flag and period (2018–2019, 2020–2022, 2023–2025), using LA County's measured multifamily shares:
  - **definite** APN-years: 2023–2025: 1,181 of 1,560 = 75.7%; 2020–2022: 431 of 648 = 66.5%; 2018–2019: 0 of 24.
  - **possible** (2-unit before 2023, 3-unit from 2023, or a 2-to-4/5+ listing): 2023–2025: 1,043 of 2,776 = 37.6%; 2020–2022: 1,288 of 2,468 = 52.2%; 2018–2019: 5 of 272 = 1.8%.
  - **single** APN-years (one ADU unit, or an unknown APN). The share follows a unit-weighted line across LA County jurisdictions in the jurisdiction's ACS share of housing units in 2+-unit structures (*m*):
    - 2023–2025: 0.063 + 0.305 × *m* (69 jurisdictions, 33,910 units).
    - 2020–2022: 0.026 + 0.203 × *m* (57 jurisdictions, 22,697 units).
    - 2018–2019: LA's pooled 222 of 11,325 = 2.0%.
  - The rest of the state's ADU-weighted *m* is 30%, against LA County's 48%. At *m* = 30%, a single 2023–2025 APN-year is 15.5% multifamily.
- **Low** = LA measured + rest at the A2 lower bound (or the calibrated value, if smaller).
- **Central** = LA measured + rest calibrated.
- **High** = LA measured + rest at LA's pooled single-band share (20.5% in 2023–2025), not scaled down for less multifamily housing.

Multifamily-lot share of all statewide ADU units (ADU units):

| Year | ADU units | A2 only: lower – upper | **Low** | **Central** | **High** |
| --- | --- | --- | --- | --- | --- |
| 2018 | 8,863 | 1.6% – 4.3% | 161 = 1.8% | 161 = 1.8% | 228 = 2.6% |
| 2019 | 12,616 | 2.0% – 6.2% | 252 = 2.0% | 252 = 2.0% | 368 = 2.9% |
| 2020 | 12,650 | 1.8% – 6.9% | 694 = 5.5% | 1,380 = 10.9% | 1,637 = 12.9% |
| 2021 | 20,482 | 3.9% – 11.8% | 2,056 = 10.0% | 3,148 = 15.4% | 3,558 = 17.4% |
| 2022 | 25,332 | 3.6% – 13.9% | 3,196 = 12.6% | 4,588 = 18.1% | 5,082 = 20.1% |
| 2023 | 28,256 | 4.2% – 7.7% | 3,786 = 13.4% | 6,001 = 21.2% | 6,801 = 24.1% |
| 2024 | 30,338 | 5.6% – 10.1% | 4,287 = 14.1% | 6,536 = 21.5% | 7,368 = 24.3% |
| 2025 | 31,945 | 5.9% – 10.9% | 4,418 = 13.8% | 6,761 = 21.2% | 7,682 = 24.0% |
| 2018–2025 | 170,482 | 4.2% – 9.8% | 18,849 = 11.1% | 28,825 = 16.9% | 32,724 = 19.2% |
| 2023–2025 | 90,539 | 5.3% – 9.6% | 12,490 = 13.8% | 19,297 = 21.3% | 21,851 = 24.1% |

**Caveats:**
- The calibration assumes LA County's relationship between A2 flags, local multifamily stock and multifamily-lot ADUs holds elsewhere. San Francisco and San Diego, where the A2 rule alone already flags 22–32%, enter through the band shares.
- The A2-only figures (columns 3–4) use no assessor data and are the owner's chosen pipeline basis. The low/central/high figures are **validation-informed**.
- 2017 has no APNs (it comes from the compilation). LA County's 2018–2019 share (1.8–2.1%) suggests a similar 2% then, since multifamily structures could not add ADUs before 2020.

## 7. Adjusted California inputs for the pooled model

Rates are ADU units per 1,000 one-unit detached homes per year, summed over jurisdictions with an observed count, as in `ca_context` ([`reference/ca_mf_lot_adu_share_rates_by_year.csv`](../../reference/ca_mf_lot_adu_share_rates_by_year.csv), [`reference/ca_mf_lot_adu_share_plateau.csv`](../../reference/ca_mf_lot_adu_share_plateau.csv)). The pooled model is not rerun.

**`ca_rate_k_from_2017_law`** in `reference/statewide_adoption_curve.csv` (k = 1–5 is 2017–2021). Later years are shown for context and for `ca_rate_k_from_2020_package` (k = 1–5 is 2020–2024):

| Year (k from 2017) | One-unit detached homes | As used | Cap only | Cap + A2 lower | Cap + A2 upper | **Cap + calibrated central** | Cap + calibrated high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2017 (1) | 8,323,006 | 0.598 | 0.598 | 0.598 | 0.598 | 0.598 (about 0.586 at a 2% share; no APNs) | 0.598 |
| 2018 (2) | 8,057,229 | 1.100 | 1.091 | 1.082 | 1.052 | **1.069** | 1.069 |
| 2019 (3) | 8,146,808 | 1.549 | 1.531 | 1.516 | 1.452 | **1.501** | 1.501 |
| 2020 (4) | 8,187,302 | 1.545 | 1.528 | 1.516 | 1.439 | **1.331** | 1.300 |
| 2021 (5) | 8,235,880 | 2.487 | 2.425 | 2.388 | 2.192 | **2.075** | 2.023 |
| 2022 (6) | 8,198,841 | 3.090 | 3.014 | 2.968 | 2.658 | **2.550** | 2.489 |
| 2023 (7) | 8,238,501 | 3.430 | 3.293 | 3.253 | 3.150 | **2.676** | 2.577 |
| 2024 (8) | 8,223,723 | 3.689 | 3.477 | 3.425 | 3.286 | **2.813** | 2.711 |
| 2025 (9) | 8,178,290 | 3.906 | 3.676 | 3.613 | 3.451 | **2.972** | 2.859 |

Numerators (ADU units) for the central: 8,616 (2018), 12,229, 10,901, 17,093, 20,911, 22,050, 23,136 and 24,308 (2025). The as-used numerators are 8,863, 12,616, 12,650, 20,482, 25,332, 28,256, 30,338 and 31,945.

**California 2023–2025 plateau** (pooled 2023–2025 rate):

| Set | Denominator (home-years) | As used | Cap only | Cap + A2 lower | Cap + A2 upper | **Cap + calibrated central** | Cap + calibrated high | 1st ADUs only |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| All grouped non-holdout jurisdictions (the 3.84 in `CA_STUDY_RESULTS.md`, used as California's "upper `y`") | 20,009,419 | 3.845 (76,927) | 3.630 (72,635) | 3.570 (71,441) | 3.416 (68,354) | **2.927 (58,565)** | 2.826 (56,538) | 3.186 (63,746) |
| All jurisdictions (statewide) | 24,640,514 | 3.674 (90,539) | 3.482 (85,790) | 3.430 (84,510) | 3.296 (81,203) | **2.820 (69,494)** | 2.715 (66,907) | 3.067 (75,577) |
| Restrictive group, non-holdout | 1,826,446 | 1.235 | 1.182 | 1.178 | 1.172 | **1.034** | 0.936 | 1.073 |
| Middle group, non-holdout | 11,845,856 | 2.394 | 2.319 | 2.302 | 2.264 | **1.956** | 1.827 | 2.099 |
| Permissive group, non-holdout | 6,337,117 | 7.308 | 6.786 | 6.630 | 6.217 | **5.287** | 5.236 | 5.826 |

(ADU units in parentheses.)

**What this means for the pooled model:**
- The cap alone, the owner's rule, lowers California's 2023–2025 level by 5.6% (3.845 → 3.630).
- With the A2-only multifamily bounds the cut is 7–11% (3.57–3.42).
- With the LA-validated estimate it is 24% (2.93; 2.83 at the high end).
- California is one of eight states in stage 2, and its 457 jurisdictions mainly shape the within-state slopes. A cut of 5–24% in its level would lower the common between-state level less than proportionally. The direction is down, and the size is to be measured by rerunning `scripts/run_pooled_regression.py` with these numerators.
- **Which inputs to use is the owner's decision:**
  - A2-only (cap, or cap + A2 lower/upper) keeps to the no-new-data rule.
  - Cap + calibrated central is the best estimate of the benchmark-comparable rate, but it rests on the validation-only LA data.
- Pre-law rates (2014–2016) are unchanged. ADUs on multifamily structures were not allowed then.

## 8. Outside California

Findings on whether each non-California source counts ADUs on multifamily lots ([`reference/ca_mf_lot_adu_share_other_sources.csv`](../../reference/ca_mf_lot_adu_share_other_sources.csv)). Every share is counted ADU units flagged ÷ counted ADU units.

| Source | Multifamily-lot ADUs allowed in the data years? | Can the data identify them? | Measured | Verdict |
| --- | --- | --- | --- | --- |
| Washington OFM | Partly. HB 1337 ([RCW 36.70A.696](https://app.leg.wa.gov/RCW/default.aspx?cite=36.70A.696)) defines an ADU on a lot with a single-family home, duplex, triplex or townhome, binding from 2025-06-30 in the Puget Sound counties | No. OFM's definition is an ADU "on a single-family lot", and the counts are by structure type only | Not measurable; Seattle proxy ~3.5% (below) | Small through estimate year 2025 |
| Oregon DLCD | No under state law. [ORS 197A.425](https://oregon.public.law/statutes/ors_197A.425) requires an ADU "for each detached single-family dwelling". Portland has allowed an ADU with a duplex since 2021 | No | Not measurable | Negligible for the 32-city panel |
| Rhode Island EOH | Yes since 2022. RIGL 45-24-31 defines ADUs with a single-unit or multi-unit dwelling | No; counts by town only | Not measurable | Possibly material; treat Rhode Island's 0.97 as an upper bound |
| Utah DWS | No under the state mandate. [HB 82 (2021)](https://le.utah.gov/~2021/bills/hbillenr/HB0082.htm) covers internal ADUs in owner-occupied detached single-family homes | No | Not measurable | Small; definition noise matters more |
| Seattle | Mostly no before 2025-06-30 | Partly: zoning and description | Lowrise/multifamily zone or conversion: 2016–18 27 of 608 = 4.4%; 2021–24 78 of 2,210 = 3.5%. Strictly ADUs on an existing 2+-unit building: 9 of 3,399 = 0.3% (2016–24) | Small |
| Portland | Yes from 2021 (an ADU with a duplex) | Partly: truncated description, no zoning field | 2016–18 7 of 1,415 = 0.5%; 2022–25 4 of 746 = 0.5% (lower bound) | Negligible as measured |
| Austin | No before HOME (2024) | Partly: description | No ADU on an existing duplex found; 6 of 466 = 1.3% (2016–19) are new duplexes miscoded as secondary apartments | Not inflated |
| Denver | Not before 2025 (not checked after) | Weak: parcel shared with a two-family permit | 2016–22 1 of 380 = 0.3%; 2025 7 of 117 = 6.0% (upper bound) | Probably small |
| Minneapolis | Yes. The 2014 ordinance allows ADUs with single- and two-family homes | Yes: occupancy type TFD plus text | Duplex lot: 2017–20 13 of 103 = 12.6%; 2021–25 9 of 71 = 12.7% | **Inflated about 13%**: single-family-lot rate about 0.28 (not 0.32) for 2017–20, 0.15 (not 0.17) for 2021–25 |

Side finding: the Minneapolis classifier counts 8 of 201 permits (2016–2026) whose text says no ADU is created ("eliminate internal ADU", "not creating … an ADU"). They are worth removing from `other_cities.py` in a later pass. This document does not change it.

## Files

- [`reference/ca_mf_lot_adu_share_by_year.csv`](../../reference/ca_mf_lot_adu_share_by_year.csv): statewide counts and shares by year, for the three cutoffs. It holds every rule, the cap, order counts, and the cumulative 3+/4+ counts.
- [`reference/ca_mf_lot_adu_share_by_jurisdiction.csv`](../../reference/ca_mf_lot_adu_share_by_jurisdiction.csv): the same, by jurisdiction and year (main cutoff).
- [`reference/ca_mf_lot_adu_share_rates_by_year.csv`](../../reference/ca_mf_lot_adu_share_rates_by_year.csv): California numerators, the denominator and rates for each variant, and order rates, 2014–2025.
- [`reference/ca_mf_lot_adu_share_plateau.csv`](../../reference/ca_mf_lot_adu_share_plateau.csv): 2023–2025 plateaus for each variant (all grouped non-holdout, statewide, and by group).
- [`reference/ca_mf_lot_adu_share_order_decomposition.csv`](../../reference/ca_mf_lot_adu_share_order_decomposition.csv): the rise split by ADU order.
- [`reference/ca_mf_lot_adu_share_acs_ecological.csv`](../../reference/ca_mf_lot_adu_share_acs_ecological.csv): ecological fits.
- [`reference/ca_mf_lot_adu_share_statewide_range.csv`](../../reference/ca_mf_lot_adu_share_statewide_range.csv): the statewide low/central/high share by year.
- LA County validation (validation only):
  - [`reference/ca_mf_lot_adu_share_la_assessor.csv`](../../reference/ca_mf_lot_adu_share_la_assessor.csv): by lot class, jurisdiction and year.
  - [`reference/ca_mf_lot_adu_share_la_rule_check.csv`](../../reference/ca_mf_lot_adu_share_la_rule_check.csv): the APN rule, cap and ADU order against the assessor class.
  - [`reference/ca_mf_lot_adu_share_la_use_codes.csv`](../../reference/ca_mf_lot_adu_share_la_use_codes.csv): use-code inventory.
  - [`reference/ca_mf_lot_adu_share_la_calibration_bands.csv`](../../reference/ca_mf_lot_adu_share_la_calibration_bands.csv) and [`reference/ca_mf_lot_adu_share_la_calibration_fit.csv`](../../reference/ca_mf_lot_adu_share_la_calibration_fit.csv): the calibration.
- [`reference/ca_mf_lot_adu_share_other_sources.csv`](../../reference/ca_mf_lot_adu_share_other_sources.csv): the cap and multifamily-lot checks outside California.
