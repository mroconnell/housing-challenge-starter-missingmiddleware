# ADU "ask why" review, 2026-10-28

A one-off review. It takes the biggest misses, outliers and surprises in the adopted ADU outputs and traces each to its inputs. Nothing was changed: no model file and no `reference/adu_model_*.csv`. The findings table is [`reference/adu_ask_why_findings.csv`](../../reference/adu_ask_why_findings.csv).

All rates are **second-home permits on single-family lots per 1,000 one-unit detached homes per year**. All permit changes are **totals over 2027–2031, statewide**. The adopted figures are: baseline 605 permits; addition 5,538 (lower), 8,757 (central) and 16,889 (upper) permits.

## Summary

- **One real mistake moves the total.**
- Maine, Massachusetts, Rhode Island: undercounted.
- Their counts cover only reporting towns.
- But the denominator is every home in the state.
- Fixing it: central **+818 permits** (8,757 → about 9,575).
- This explains Massachusetts' 20% held-out miss.
- **Washington's 18% miss is timing.**
- Its "law years" came before local compliance.
- Coding from compliance: central **+617 permits**.
- **Vermont's 2024 jump may be a source change.**
- Dropping it: central **−333 permits**.
- **One documentation error:** the allocation text is wrong.
- Places get levels from home value only.
- Income does not enter the allocation.
- **Small-village outliers** are extrapolations beyond California's range.
- Rural share, Madison vs suburbs: judgment calls, already disclosed.
- **Checked and correct:** Madison's 40 units, floor, never-below rule.
- Also correct: district split, table units, worked examples.
- **Milwaukee permit-vs-census issue:** does not touch ADU numbers.

### Findings ranked by impact

Changes are in permits over 2027–2031 against a rerun of the adopted model (the rerun gives 8,764.1 central permits, not 8,756.6, because it recomputes the ramp without rounding; differences are what matter). "—" = not computed.

| Rank | Finding | Verdict | Central change (permits) | Lower change (permits) | Upper change (permits) | Baseline change (permits) |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 1 | Partial reporting divided by all homes (Maine, Massachusetts, Rhode Island 2025) | Real mistake | +818 | +523 | +982 | 0 |
| 1b | Massachusetts' 11-month year counted as 12 months | Real mistake (small) | +109 more (+100 alone) | 0 | +160 more | 0 |
| 2 | Washington counted as in force before local compliance | Judgment call, leans mistake | +617 | +500 | +1,059 | 0 |
| 3 | Vermont 2024 from a changed source; completions, not permits | Judgment call | −333 (drop 2024) | −90 | −220 | 0 |
| 4 | Seasonal homes in the denominator | Judgment call | −1,036 if occupied homes only (not recommended) | — | — | 0 |
| 5 | Allocation text says value + income; code uses value only | Real mistake (documentation) | 0 | 0 | 0 | 0 |
| 6 | 8 high-value villages beyond the fitted value range | Real mistake (small) | about 0 (about 25 move between places) | about 0 | about 0 | 0 |
| 7 | Rural: 43% of addition, 39% of homes | Judgment call | 0 (about 350 move between groups) | 0 | 0 | 0 |
| 8 | Madison below all its suburbs | Judgment call | +191 if pooled level | +61 | +521 | 0 |
| 9 | 8 extra Wisconsin cities unused; Kaukauna coded "prohibited" with 7 permits | Real mistake (small) | about +55 | — | — | about −58 |
| 10 | Madison's 2026 pace above its 2027 with-law path | Judgment call | −129 (existing case) | — | — | +209 |
| 11–17 | Madison 40 units, floor, never-below rule, districts, units, California year 1, Milwaukee permits | Correct | 0 | 0 | 0 | 0 |

Ranks 1, 1b and 2 together (not additive, not run together): roughly +1,500 central permits, about 17% of 8,757.

## 1. Comparison states

### 1. Partial reporting divided by all homes (real mistake)

**What we see.** In the held-out test the model is 20% above Massachusetts (predicted 0.907, observed 0.751). Rhode Island (0.62) and Oregon (0.68) set the lower scenario. Maine's level is 1.00.

**Why.**
- The counts cover reporting towns only:
  - Maine: 182 towns, about 73% of people;
  - Massachusetts: 293 of 351 towns;
  - Rhode Island 2025: 32 of 39 towns.
- The denominator is every one-unit detached home in the state: `SERIES[...]["denominator"] = ("state", ...)` in `missing_middleware/comparison/statewide_states.py`.
- `COVERAGE` in `missing_middleware/comparison/pooled_regression.py` holds the reporting shares, but they are only a "named sensitivity, never applied silently". The adopted fit never uses them, and the adopted sensitivity table does not list the case.
- Dividing Massachusetts by 293/351 alone moves its observed rate from 0.751 to 0.900. That is within 1% of the prediction, so the 20% miss is the undercount.

**Size** (refit of the adopted pooled model, configuration A, cap + A2):

| Correction | Central (permits) | Lower (permits) | Upper (permits) | Common level (per 1,000 homes per year) |
| --- | ---: | ---: | ---: | ---: |
| None (rerun of adopted) | 8,764 | 5,545 | 16,896 | 1.0035 |
| Rhode Island 2025 ÷ 32/39 | 8,981 | 6,068 | 16,776 | 1.0261 |
| Massachusetts ÷ 293/351 | 8,974 | 5,545 | 17,151 | 1.0264 |
| Maine ÷ 0.73 | 9,133 | 5,545 | 17,976 | 1.0438 |
| All three | **9,582** | **6,068** | **17,878** | 1.0917 |
| All three + Massachusetts 12/11 | 9,691 | 6,068 | 18,038 | 1.1036 |

- The lower rises because Rhode Island's level rises (0.62 → 0.73).
- The reference line's year 1 rises too:
  - median 0.754 → 0.900;
  - +269 permits in 2027.
- Utah has the same problem: about 90 reporting cities and counties, divided by all of Utah. It has no coverage share in the code. At an assumed 85% coverage, central rises about +200 more permits. This figure is unverified.
- The town share is a crude stand-in. Non-reporting towns are probably smaller and quieter, so the true change is between 0 and these figures.

**Fix.** Use homes in the reporting towns as the denominator where the town lists exist. Otherwise apply `COVERAGE` in the main fit. Count Massachusetts 2025 as 11/12 of a year. Then rerun the pooled revision and the engine.

### 2. Washington before local compliance (judgment call, leans mistake)

**What we see.** The model is 18% above Washington (predicted 0.878, observed 0.738).

**Why.**
- `STATE_CODING["WA_inc_exSeattle"]` treats the OFM estimate years 2024–2026 (April 2023 to March 2026) as years 1–3 of the law.
- HB 1337 was enacted on 2023-07-23. But cities had to adopt compliant rules only from 2025-06-30 (King, Pierce, Snohomish and Kitsap counties) or later (all other counties).
- So most of these "law years" ran under old local rules. Estimate year 2024 also includes 3.7 months before the law was enacted.
- Gate 3 already built `WA_COMPLIANCE` (estimate year 2026 = year 1) as a sensitivity. The adopted sensitivity table does not show it.

**Size.** Central +617, lower +500, upper +1,059 permits. Washington's own level rises from 1.19 to 1.55. Only one partly post-compliance year exists, so this rests on 1 data point.

**Fix.** Show it in the adopted sensitivity table at least. The owner decides between it and the main case.

### 3. Vermont 2024 and completions (judgment call)

**What we see.** Vermont's rate jumps to 1.40 in 2024 (57 ADUs), from 0.64–0.79 in 2021–2023. This one county-year sets half of the year-4 reference median (1.293), which is also used for 2031.

**Why.**
- The series is Chittenden County only (38,653 homes).
- Its 2024 count comes from DHCD records, while earlier years come from CCRPC (`statewide_states.py`, `VT_chittenden` source note).
- Units are counted by the year they were built or first occupied, not the year they were permitted. Every other state counts permits.

**Size.**
- Dropping Vermont 2024:
  - central −333, lower −90, upper −220 permits;
  - reference line −402 permits (year-4 median 1.293 → 1.184 in 2030 and 2031).
- Reading year built as permit year + 1 instead: central −448 permits.

**Fix.** Check the 2024 count against CCRPC's own series. Drop it if the two are not comparable.

### Other comparison-state checks (correct or minor)

| Item | Finding | Verdict |
| --- | --- | --- |
| California level 2.45 (per 1,000 homes per year, typical place) | Two laws (2017 and 2020) plus SB 9 in high-value markets. Keeping California in the common level is supported by the held-out test (log error 0.113 with it vs 0.132 without). | Judgment call (adopted) |
| California year 1 in the reference line | 2020 = year 1 is year 4 of the 2017 law. The 1.52 rate is not a first-year rate; Gate 3 quotes 0.60 for 2017. The year-1 median barely moves (0.754 with California, 0.7526 without). | Judgment call; label it |
| Utah report-year basis | A report year runs August to July. Report year 2023 = months 10–21 after the October 2021 law, so coding it as year 2 is right. | Correct |
| Utah internal-only law | Utah's law covers internal ADUs only, but its counts include detached ADUs. The benchmark allows both, so the counts fit the outcome; Utah is a weaker law in the common level. | Judgment call |
| Rhode Island coverage | 32 of 39 towns in 2025 (see rank 1). Coverage for 2021–2023 is not stated. | See rank 1 |
| Maine and Massachusetts single years | One year each (2025), both year 1. Massachusetts' year is 11 months (rank 1b). | See rank 1 |
| Oregon | SB 1051 in force 2018-07-01; 2018 dropped; 32 cities with their own denominator. | Correct |
| Extra-unit types | Washington counts tiny homes used as housing. Most series include ADUs built with a new house (× 0.951 applied). California includes JADUs; the outcome includes any unit with its own kitchen. | Judgment calls (adopted, AQ-039) |

## 2. Wisconsin places

### 4. Seasonal homes (judgment call)

- Engine homes are ACS B25024_002: every one-unit detached home, seasonal cabins included.
- 1,060 of the 8,757 central permits (12.1%) fall in places where over 30% of homes are vacant (ACS B25002). Most are seasonal.
- Example: Presque Isle town (77% vacant) gets 8.9 permits.
- Using occupied homes only would cut central by 1,036 permits.
- **Not a mistake:** comparison states use the same denominator, and Maine and Vermont are seasonal too. Disclose it.

### 5. Allocation described wrongly (real mistake, documentation)

- `docs/MODEL_AND_ASSUMPTIONS.md` Part A, step 2, says that within a state +10% home value means +29% rate and +10% income means −25%, and that each place's level comes from "home value, income and size".
- Those are the slopes of the value–income–size fit (2.70 and −3.03). That fit sets only the statewide rate.
- Places are allocated by the value-only fit (slope 1.01; `W_ALLOC` in `scripts/run_pooled_revision.py`, a deviation disclosed in `docs/gate3/POOLED_MODEL.md`).
- **Check:** central level ÷ value is nearly constant:
  - Chenequa: 6.22 per $1.40 million;
  - Shorewood Hills: 4.15 per $0.94 million.
- **Fix:** correct the text. No permits change.

### 6. Small high-value villages (real mistake, small)

| Place | One-unit detached homes | Median value (dollars) | Central level (per 1,000 homes per year) | Central addition (permits, 2027–2031) |
| --- | ---: | ---: | ---: | ---: |
| Chenequa village | 271 | 1,402,800 | 6.22 | 7.1 |
| Lac La Belle village | 110 + 1 | 1,343,800 | 5.95 | 2.8 |
| Oconomowoc Lake village | 300 | 1,210,900 | 5.36 | 6.8 |
| Shorewood Hills village | 560 | 939,900 | 4.15 | 9.7 |
| Manitowish Waters town | 1,020 | 762,100 | 3.35 | 14.3 |

- **Why so high:** these values are 2.9 to 5.4 times the Wisconsin average.
- In log terms, 8 places (2,852 homes) sit further above their state's average than any California place (+1.01).
- California's top is cut off because ACS records values above $2,000,000 only as "$2,000,000+".
- So their rates are extrapolated.
- **Size:** these 8 places hold about 50 permits; capping moves about 25 to other places, with the statewide total unchanged.
- **Fix:** cap the value gap at +1.01 before allocating.
- No value or income in Wisconsin is top-coded, except 1 income.

### 7. Rural share (judgment call)

| Group | Homes | Share of homes | Central addition (permits) | Share of addition | Homes-weighted central level (per 1,000 homes per year) | Typical median value (dollars) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Rural | 710,070 | 38.6% | 3,801 | 43.4% | 1.32 | 288,957 |
| Suburban | 450,535 | 24.5% | 2,605 | 29.7% | 1.42 | 310,826 |
| Urban | 427,619 | 23.2% | 1,450 | 16.6% | 0.99 | 219,515 |
| Small community | 251,345 | 13.7% | 901 | 10.3% | 0.90 | 191,544 |

- **Why:** the allocation uses home value only, and rural values include land (acreage).
- **Not a mistake:** it is already disclosed (Limitation 7).
- It moves about 350 permits between groups and leaves the state total unchanged.
- **Optional test:** for towns, use the value of the nearest city instead.

### 8. Madison below its suburbs (judgment call)

| Place | Central addition (permits per 1,000 homes per year) |
| --- | ---: |
| Madison city | 0.51 |
| Sun Prairie city | 1.31 |
| Fitchburg city | 1.50 |
| Middleton city | 1.75 |

- **Why:** only Madison is put on the slower "Madison-like" path (0.452–1.076). The suburbs keep their pooled levels from home value.
- Madison's own pooled level would be 1.63.
- **Size:** putting Madison on its pooled level adds 191 central permits (existing sensitivity).
- **Fix:** none needed; say plainly that the slow path applies to Madison only.

### 9. Unused city data; Kaukauna (real mistake, small)

- The eight extra city adapters measured rates (`reference/wi_rules_vs_activity_places.csv`). None of them feed the group rates.
- Restricted places measured: Green Bay 0, De Pere 0, Verona 0 and Watertown 2 permits.
  - Adding them lowers the restricted rate from 0.0607 to about 0.0515.
  - That changes the baseline by about −58 permits and the central addition by about +55.
- **Kaukauna** is provisionally coded "prohibited" (no ADU text found). But it issued 7 "Additional dwelling unit" permits in 2023–2025, a rate of 0.432 per 1,000 homes per year. That is the highest measured rate in Wisconsin.
  - In the engine it is uncoded (0.0607).
  - Using its measured rate: baseline +10, addition −8 permits.
- **Fix:**
  - re-check Kaukauna's rules and what its permits are;
  - pool the measured restricted cities.

### 10. Madison 2026 (judgment call)

- Madison's provisional 2026 rate is 0.97 (42 units to 2026-10-23, of which 29 are from one templated programme). That is above its 2027 with-law path value (0.452).
- The existing sensitivity covers it: baseline +209, addition −129 permits.
- Revisit when 2026 is final.

### Places with odd values (checked)

- **1,882 uncoded areas vs "1,848 places":** 34 uncoded areas have 0 homes (county pieces). Both counts are right.
- **Zero-home pieces:** 37 areas with 0 homes get 0 permits. They are correct (municipality pieces in a second county).
- **Lowest level:** Kingston town, 11 homes, value $46,000, level 0.196.
- **Value fallbacks:** 30 areas use another county piece's value and 16 use the county's. Together they hold 1.4 central permits.
- **Small-place homes counts:** for places under 300 homes, the ACS margin of error is a median 21% of the count. That is noisy, but no bias was found.

## 3. Wisconsin pipelines (checked)

| Item | What was checked | Verdict |
| --- | --- | --- |
| Madison 2022–2025 (40 units) | 5 + 10 + 11 + 14 units by year. Detached 30, conversion 4, teardown 2, single-family-to-duplex 4. Templated programme 7 (2025). ÷ 213.168 thousand home-years = 0.1876. | Correct |
| Pleasant Prairie (3 units, 2014–2025) | 2020–2024 homes used for all 12 years. Pleasant Prairie grew fast, so its early home-years are overstated and its rate slightly low. Affects the baseline only (< 1 permit). | Correct (minor) |
| Sun Prairie (2 units) | Counts are applications, not issued permits; labelled in the `stage` column. | Correct (labelled) |
| Milwaukee (35 candidates) | Quality C (no unit counts). Its own open permits, not the Census permit survey. | Correct (disclosed) |
| Eight city adapters | Results exist but are unused (rank 9). | See rank 9 |
| Floor 0.2345 | Binds for 1 place (11 homes) in central and 11 places (1,182 homes) in the lower. Adds 0.0 and 0.1 permits. | Correct; almost never active |
| Ramp 0.63 / 0.80 / 0.82 | From the pooled year terms. California's year 1 (2020) followed its 2017 law, so the ramp may be fast for a first law. | Judgment call |
| District split | 2020 block housing units × block-group detached share. Districts add up to the state within 0.0 permits. 56 of 775 areas over 500 homes have block weights outside 0.8–1.25 × ACS, but shares within each area still sum to 1. | Correct |
| Never below the current rate | Never binds: the highest current rate (0.188) is below the lowest with-law level (0.196). | Correct |

## 4. Units

Checks run on the adopted tables:

| Table and column | Stated unit | Check | Result |
| --- | --- | --- | --- |
| `adu_model_statewide*.csv` `baseline_units`, `additional_units` | Permits, five-year total (by year: one year) | Years add up to the five-year totals | Gap below 0.000001 permits |
| `adu_model_by_county / context / x_basis / rights_basis.csv` | Permits, five-year total | Each adds up to the statewide total | Gap below 0.000001 permits |
| `adu_model_by_assembly_district.csv` `additional_per_1000_homes_per_year` | Per 1,000 homes per year | Equals the five-year total ÷ homes × 1,000 ÷ 5 | Gap below 0.0001 |
| `adu_model_district_crosswalk.csv` `share` | Share, 0–1 | Range, and sum per area | 0.000015–1.0; sums to 1 |
| `pooled_revision_wi_y_by_area.csv` `y_*` | Per 1,000 homes per year | Range | 0.10–11.7 (upper); values are plausible |
| `statewide_states_annual.csv` `adu_count` | Mixed | Vermont counts completions; Sun Prairie applications; other series permits. The year column mixes calendar, OFM April–March and Utah August–July years (documented in `year_basis`). | **Mixed units**: see rank 3 |
| `wi_rules_vs_activity_places.csv` `permits` | Mixed | Issued vs application (`stage` column) | Labelled |

The TOD sanity checks (`missing_middleware/tod/sanity.py`) are lot-table specific. The checks above follow the same idea (unit ranges, rule-definition checks, out-of-range flags) without reusing that code. The out-of-range flag found rank 6.

## 5. Milwaukee permits vs census growth (from the TOD review)

- In 2010–2019, Milwaukee's census home growth was 0.46× its Census permit count (`reference/tod_audit_permits_census.csv`), probably because of demolitions.
- **The ADU numbers do not use that permit count.**
  - Milwaukee's current-law rate is its own candidate permits on lots with an existing home.
  - All ADU outputs are gross permits, labelled "permits are not homes" (Limitation 9).
- The only link is in `docs/POLICY_SCENARIO_COMPARISON.md`, which shows the ADU addition as a share of the all-housing baseline (122,619 permits, 7.1% and 13.8%).
  - The Milwaukee adjustment changes only that denominator.
  - It changes no ADU permit count.
- **Verdict:** it does not matter for the ADU numbers.

## How the sizes were computed

- Each comparison-state case refits the adopted pooled model with one change and recomputes:
  - the allocation;
  - the ramp for each path;
  - the Rhode Island and Oregon lower factor;
  - Madison's path, the floor and the never-below rule.
- These runs used scripts in the session scratchpad. No repository code was changed.
- The rerun of the adopted model gives 8,764.1 central permits against the published 8,756.6, because it does not round the ramp. Changes are measured against the rerun.
- Seasonal shares come from ACS 2020–2024 B25002 (vacant ÷ total housing units) by county subdivision.
