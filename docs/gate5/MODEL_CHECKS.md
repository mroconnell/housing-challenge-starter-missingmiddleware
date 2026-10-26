# Gate 5 Model Checks: unknown rules, legislative districts, self-checks

Prepared 2026-10-26 by the model and data agent for the Gate 5 review ([MVP_EXECUTION_PLAN.md](../MVP_EXECUTION_PLAN.md#gate-5--statewide-adu-mvp-and-the-good-enough-decision)). **No adopted number changed.** The adopted model is still AQ-043 ([ASSUMPTIONS_AND_QUESTIONS.md](../ASSUMPTIONS_AND_QUESTIONS.md)): a baseline of 604.6 permits and an addition of 5,538 / 8,757 / 16,889 permits (lower / central / strong adoption) over 2027–2031. What the UI should read is in [UI_CONTRACT.md](UI_CONTRACT.md).

**Units.** As in Gates 3 and 4:
- **permits** = second-home permits (ADUs, plus single-family-to-duplex conversions on lots that already have a home) at issuance, summed over 2027–2031 unless a year is named;
- **rate** = permits in a year ÷ thousands of one-unit detached ("single-family") homes, written "per 1,000 homes per year". Wisconsin has 1,839,569 such homes (ACS 2020–2024, B25024_002), the denominator of every statewide rate below.

"Current-law rate" is a place's rate without the statewide law; "with-law rate" is its rate with it. The model adds homes × (with-law rate − current-law rate) × ramp ÷ 1,000 in each area and year ([engine.py](../../missing_middleware/model/engine.py)).

## Summary

| Check | Result |
| --- | --- |
| Unknown-rules variants | Three full engine runs in one run group. If the 1,267,433 homes in places with uncoded rules (68.9% of 1,839,569) behaved like prohibited places, the baseline would be 186.4 permits lower, the central addition 158.6 higher, and the total with the law 27.8 lower (−0.3% of 9,361.3). If they behaved like places that already allow ADUs as the bill would, the baseline would be 804.7 higher, the addition 684.7 lower, and the total 120.0 higher (+1.3%). |
| Legislative districts | 99 Assembly and 33 Senate districts. Every path and year reconciles to the state; the largest gap is 4.5 × 10⁻¹³ permits, and the explicit "unallocated" row is 0. Central addition per Assembly district: 15.5 to 239.0 permits, median 86.6. |
| Pilot multiplier | The statewide method does not scale a pilot. The Madison floor sets the with-law rate in 1 area of 1,888 with homes (11 homes) and adds 0 permits there. Removing the floor and Madison's own path gives 8,948.0 (+191.4). Simple pilot multipliers would give 1,632 to 6,232. |
| Contexts | Central addition rates: urban 0.68, suburban 1.16, small communities 0.72 and rural 1.07 per 1,000 homes per year. The differences come from home values and incomes, not from the group labels. |
| Trace | 73.4% of the central addition (6,427.5 of 8,756.6 permits) is in places with an **assumed** current-law rate (uncoded rules), 21.1% (1,846.8) **estimated** from a coded rules group, and 5.5% (482.4) **observed** in the place's own permits. Every with-law rate is transferred from other states. |
| Groupings | Context groups do not enter the fit or the engine, so redrawing them moves no total. Pooling the prohibited and restricted evidence into one current-law group: baseline −30.9, addition +26.3, total −4.6. |
| Housing health | Stock, occupancy/vacancy, mix and permitted production all exist, with years and sources. There are 6 gaps for the UI agent (see [section 3e](#3e-landing-screen-housing-health-indicators)). |
| Tests | `bash scripts/test.sh`: 340 tests OK (20 new in `tests/test_gate5_model.py`). |

## 1. Unknown-rules variants

**What it is.** Of the 1,925 county-subdivision areas, 1,882 have no coded ADU rules (`x_basis` = `uncoded_like_restricted_AQ027`). They hold 1,267,433 of Wisconsin's 1,839,569 single-family homes (68.9%). Of those areas, 1,848 have homes. The adopted model gives them the restricted group's current-law rate (AQ-027). `scripts/run_unknown_rules_variants.py` reruns the adopted engine three times. Each run uses the same parameters, per-area levels, ramps and Madison path, and changes only those areas' current-law rate:

| `unknown_treatment` | DATA_CONTRACTS enum | Current-law rate given to uncoded places (per 1,000 homes per year) |
| --- | --- | --- |
| `like_restricted` (adopted) | replaces `sample_mix` (AQ-027) | 0.0607 = 34 permits ÷ 560.398 thousand home-years (Madison 2014–2023, Fitchburg 2022–July 2026) |
| `like_prohibited` | `all_prohibited` | 0.0313 = 5 ÷ 159.931 (Pleasant Prairie 2014–2025, Sun Prairie 2016–May 2026) |
| `like_benchmark` | `all_compliant` | 0.1876 = 40 ÷ 213.168 (Madison 2022–2025) |

The three runs share run group `adu-unk-<hash>`; each run is `<run_group_id>-<unknown_treatment>`. The hash covers the parameter file, the rate groups, the per-area levels, the engine inputs, the engine and the script. The manifest is `data/processed/model_run/unknown_rules/run_manifest.json`.

**Effect, 2027–2031, permits (difference from adopted in brackets).**

| Variant | Baseline | Lower addition | Central addition | Strong-adoption addition | Total with law, central |
| --- | --- | --- | --- | --- | --- |
| Like restricted (adopted) | 604.6 | 5,538.1 | 8,756.6 | 16,888.9 | 9,361.3 |
| Like prohibited | 418.3 (−186.4) | 5,695.7 (+157.6) | 8,915.2 (+158.6) | 17,048.3 (+159.4) | 9,333.5 (−27.8) |
| Like benchmark | 1,409.3 (+804.7) | 4,857.6 (−680.5) | 8,072.0 (−684.7) | 16,200.8 (−688.1) | 9,481.3 (+120.0) |

This reproduces the earlier finding (baseline −186, addition +159, total −28).

**Why the total barely moves.** The with-law rate comes from the statewide-law states and each place's market, not from its current rules. A different current-law rate therefore moves the baseline one way and the addition the other. Only the ramp years leave a gap: in a year where the law has reached a share r of its effect, the total is current-law rate × (1 − r) + with-law rate × r. In 2030 and 2031 the ramp is 1, so the three totals are identical (2,180.1 and 2,194.9 permits, central). In 2027 (r = 0.63) they differ: 1,405.8 (like prohibited), 1,419.5 (adopted) and 1,478.4 (like benchmark).

**By context (central, permits over 2027–2031).** Urban places are all coded, so none of their figures move. Rural (710,070 homes, all uncoded): baseline 111.0 / 215.4 / 666.2 and addition 3,889.8 / 3,801.0 / 3,417.4 (like prohibited / adopted / like benchmark). Small communities (251,345 homes, all uncoded): baseline 39.3 / 76.2 / 235.8. Suburban (306,018 of 450,535 homes uncoded): baseline 82.4 / 127.4 / 321.7.

**Checks in the script.**
- The adopted variant equals `data/processed/model_run/results_long.parquet` row for row: 28,875 rows, largest gap 0 permits.
- The like-prohibited baseline equals `wi_baseline_sensitivities.csv` (418.27).
- The adopted statewide rows equal `adu_model_statewide.csv`.
- County and context tables sum to the state for every variant and path; the largest gap is 9 × 10⁻¹³ permits.

**Outputs.** `reference/adu_model_unknown_rules_statewide.csv`, `_statewide_by_year.csv`, `_by_county.csv`, `_by_context.csv`, `_by_area.csv` (five-year, 1,925 areas × 3 variants), and the per-area-path-year rows in `data/processed/model_run/unknown_rules/results_long.parquet`.

## 2. Legislative districts

**Boundaries.** Wisconsin State Assembly (99) and Senate (33) districts of the 2024 plan (2023 Wisconsin Act 94), from the Legislative Technology Services Bureau's public ArcGIS layers. They were fetched in full by `scripts/fetch_legislative_districts.py`; provenance is in [DATA_PROVENANCE.md](../DATA_PROVENANCE.md) and the SHA-256 in each `data/raw/<source_id>/manifest.json`. The Assembly layer names each district's Senate district (SEN2024). Overlaying the two layers confirms that all 99 Assembly districts sit inside their named Senate district (smallest share of a district's area inside it: 1.0000), three per Senate district.

**Method: block-weighted shares of each area's single-family homes** (`scripts/build_district_allocation.py`). Block-level counts were cheap: the 2020 TIGER block file (291 MB) carries each block's 2020 housing units.
1. Each of the 203,059 census blocks of 2020 gets an estimate of single-family homes: its 2020 housing units × its block group's share of single-family homes in the ACS 2020–2024 (B25024_002 ÷ B25024_001). These estimates total 1,809,790 homes, 0.984 of the ACS state count of 1,839,569.
2. Each block's internal point is placed in a model area (2024 county subdivision) and in an Assembly district. 550 points fell on no district polygon (shoreline slivers) and took the nearest one.
3. An area's share in a district = its block weight in that district ÷ its total block weight. All 1,888 areas with homes got block shares; no area-weight fallback and no unallocated area were needed. 55 areas are split across districts, for example Milwaukee city across 14 and Madison city across 9; 1,842 lie in one district.
4. Each area's adopted baseline and addition (every path and year) is multiplied by its shares and summed by district. An explicit row `unallocated` = state − sum of districts is always written; it is 0 here.
5. Senate districts are the sum of their three Assembly districts.

**Reconciliation.**
- Assembly and Senate tables both reconcile to `adu_model_statewide.csv` and `adu_model_statewide_by_year.csv` for all 3 paths × (5 years + the 2027–2031 total). The largest gap is 4.5 × 10⁻¹³ permits.
- Homes sum to 1,839,569 in both.
- Tests check all of this in `tests/test_gate5_model.py`.

**Results (central, 2027–2031).**
- **Assembly.** Additional permits per district range from 15.5 (District 19, inside Milwaukee city, 5,147 single-family homes) to 239.0 (District 34, Northwoods lake towns such as Minocqua, 46,412 homes); the median is 86.6. The rate ranges from 0.51 per 1,000 homes per year (District 79, Madison, 14,790 homes on Madison's own path) to 1.69 (District 97, Waukesha lake towns, 21,365 homes).
- **Senate.** 100.6 permits (District 3) to 473.8 (District 33), median 260.3.
- **Why single-family homes vary so much.** Districts have equal populations but very different housing: from 5,147 single-family homes (District 19) to 46,412 (District 34); the median is 17,528.

**Weaknesses (say these with the numbers).**
- **Shares, not forecasts.** A district figure is each area's model result shared by where its single-family homes are. It is not a forecast of where in a city ADUs will be built.
- **2020 blocks against 2024 boundaries.**
  - Housing built since 2020 and annexations are not reflected in the split. They are in the area totals, which come from the model.
  - In 56 of the 775 areas with at least 500 homes, the block estimate differs from the ACS count by more than −20% or +25%; the median ratio is 0.98.
- **Even share within a block group.** The block group's single-family share is applied evenly to its blocks, so a block of apartments in a mostly single-family block group gets too many homes.
- **Plain area weights would move about 2.7% of the addition.** Using the share of each area's land in each district instead would move 237 of 8,757 central permits between districts: half the sum of absolute differences, 474.5 ÷ 2. The largest change is District 12 (Milwaukee's northwest edge and Brown Deer), 34.1 permits; the median change is 2.1. Block weights are better because homes are not spread evenly over land, which matters most in towns with large lakes or farmland.

**Outputs.**
- `reference/adu_model_by_assembly_district.csv` and `reference/adu_model_by_senate_district.csv`: 600 and 204 rows, (districts + 1) × 3 paths × 6 periods.
- `reference/adu_model_district_crosswalk.csv`: area × Assembly district shares, with method.
- `data/processed/districts/geo_assembly.geojson` (189 KB) and `geo_senate.geojson` (125 KB): simplified to 150 m in WGS84, valid polygons. Great Lakes waters are already excluded (144,741 km² against Wisconsin's 140,295 km² of land; inland lakes are included).
- `data/processed/districts/allocation_checks.json` and `area_weight_comparison.csv`.

## 3. Gate 5 self-checks

### 3a. The statewide method stands without a pilot multiplier

`reference/gate5_pilot_multiplier_check.csv`, central, permits over 2027–2031:

| Case | Addition | Share of adopted |
| --- | --- | --- |
| Adopted: sum over areas of homes × (with-law − current-law rate) × ramp ÷ 1,000 | 8,756.6 | 100% |
| Madison multiplier: Madison's addition per home (134.9 ÷ 53,292) × 1,839,569 homes | 4,657.4 | 53% |
| Three-pilot multiplier: pilots' addition (229.5) ÷ pilots' homes (67,742) × 1,839,569 | 6,232.1 | 71% |
| Madison ratio: state baseline 604.6 × (Madison with-law 184.9 ÷ Madison baseline 50.0 − 1) | 1,631.6 | 19% |
| Adopted method with **no** Madison floor and **no** Madison path | 8,948.0 | 102% |
| Addition in the 1 area (11 homes) where the Madison floor sets the with-law rate | 0.0 | 0% |
| Addition in the three pilot areas themselves | 229.5 | 2.6% |

**Reading.**
- The with-law rate comes from the pooled model of 8 statewide-law states and 5 cities (AQ-042), applied to each Wisconsin place's own market. No pilot enters it, with two exceptions:
  - The Madison floor (0.2345 per 1,000 homes per year) is now below the pooled level everywhere except one 11-home area.
  - Madison's own observed-path override is worth −191.4 permits, the sensitivity "Madison on the statewide estimate".
- The pilots' permit records do set the current-law rate groups, and so the baseline (section 1). As section 1 shows, that moves the total with the law by at most +120 permits (+1.3%).
- Simple pilot multipliers would give anything from 1,632 to 6,232. That spread is the reason the method does not use one.

### 3b. Urban, suburban, small-community and rural contexts

The groups ([FOUNDATION.md](../gate2/FOUNDATION.md)):
- **urban**: ≥ 20,000 housing units, or a regional city;
- **suburban**: in a metropolitan county and dense or large;
- **small community**: any other city or village;
- **rural**: any other town.

Table: `reference/gate5_context_contrast.csv`. Home values and incomes are homes-weighted geometric means of ACS 2020–2024 county-subdivision medians.

| | Urban | Suburban | Small community | Rural | Wisconsin |
| --- | --- | --- | --- | --- | --- |
| Areas with homes | 23 | 174 | 453 | 1,238 | 1,888 |
| Single-family homes (share of 1,839,569) | 427,619 (23%) | 450,535 (24%) | 251,345 (14%) | 710,070 (39%) | 1,839,569 |
| Median home value / income | $219,500 / $65,900 | $310,800 / $91,400 | $191,500 / $67,400 | $289,000 / $86,600 | $260,900 / $79,600 |
| Current-law rate (per 1,000 homes per year) | 0.087 | 0.057 | 0.061 | 0.061 | 0.066 |
| With-law rate in 2031, central | 0.92 | 1.42 | 0.90 | 1.32 | 1.19 |
| Baseline (permits) | 185.6 | 127.4 | 76.2 | 215.4 | 604.6 |
| Addition: lower / central / strong (permits) | 944 / 1,450 / 2,728 | 1,644 / 2,605 / 5,031 | 560 / 901 / 1,765 | 2,391 / 3,801 / 7,364 | 5,538 / 8,757 / 16,889 |
| Central addition rate (per 1,000 homes per year) | 0.68 | 1.16 | 0.72 | 1.07 | 0.95 |
| Share of the central addition | 16.6% | 29.7% | 10.3% | 43.4% | 100% |

**Examples** (`reference/gate5_context_examples.csv`: the three largest places in each group; central addition rate per 1,000 homes per year):
- **Urban.** Milwaukee 0.60 (101,402 homes, value $184,000, current-law rate observed 0.086). Madison 0.51 (53,292 homes, $372,900, observed 0.188, on its own path). Green Bay 0.71 (26,655 homes, $207,200, estimated 0.061).
- **Suburban.** Brookfield 1.63 ($443,900, prohibits ADUs, estimated 0.031). New Berlin 1.31 ($365,700). Menomonee Falls 1.34 ($368,000).
- **Small community.** Wisconsin Rapids 0.43 ($131,900). Marshfield 0.60 ($176,100). Beaver Dam 0.69 ($201,900). All three have uncoded rules (assumed 0.061).
- **Rural.** Stephenson town 0.59 ($174,600). Minocqua town 1.10 ($311,100, lake and seasonal homes). Oconomowoc town 1.68 ($466,300). All three are uncoded.

**What drives the differences** (`reference/gate5_model_drivers.csv`, the adopted pooled model refitted; within-state terms):
- **Home value.** A place with a 10% higher median home value than its state's average has a 29% higher with-law rate (coefficient 2.70 on the log scale, cluster SE 0.14).
- **Income.** At the same value, 10% higher income means a 25% lower rate (−3.03, SE 0.18). High value relative to income is what predicts ADU building.
- **Size.** Barely matters: 10% more homes means a 0.8% higher rate (0.08, SE 0.03).

So suburban and rural places, where values are higher relative to incomes (lake towns, exurbs), get higher with-law rates than urban places and small cities. Urban places also have the highest current-law rate (0.087, Milwaukee and Madison observed), which shrinks their addition. The context label itself plays no part in the model (section 3d).

**Unsupported contexts.** No Wisconsin rural town or small community has an observed permit series. Their current-law rate is the restricted group's (assumed), and their with-law rate is transferred from statewide-law states' places of similar value and income. The pooled model's members include rural and small places in Oregon, Washington, Maine, Vermont and the other law states, but their behaviour under a Wisconsin climate and market is untested. The sensitivity that puts rural places and small communities at the Madison floor shows how much rests on this: −3,991 permits.

### 3c. Trace of the state totals and ranges

`reference/gate5_trace.csv`, permits over 2027–2031. "Observed / estimated / assumed" is the basis of the **current-law** rate. The UI's "Calculated" is `estimated`. The **with-law** rate is transferred from other states for every area: from the pooled model, or for Madison from 9 Washington and Oregon cities.

| Current-law basis | Areas | Single-family homes (share) | Baseline (share) | Central addition (share) | Lower | Strong adoption |
| --- | --- | --- | --- | --- | --- | --- |
| Observed in the place's own permits (Milwaukee, Madison, Pleasant Prairie) | 3 | 161,026 (8.8%) | 95.0 (15.7%) | 482.4 (5.5%) | 346.0 | 827.3 |
| Estimated from a coded rules group | 37 | 411,110 (22.3%) | 125.1 (20.7%) | 1,846.8 (21.1%) | 1,155.4 | 3,593.7 |
| Assumed (uncoded, like restricted) | 1,848 | 1,267,433 (68.9%) | 384.5 (63.6%) | 6,427.5 (73.4%) | 4,036.7 | 12,467.9 |
| **Wisconsin** | 1,888 | 1,839,569 | 604.6 | 8,756.6 | 5,538.1 | 16,888.9 |

By context × basis (central addition):
- urban: observed 441.1 and estimated 1,008.4;
- suburban: observed 41.3, estimated 838.3 and assumed 1,725.2;
- small community: all assumed, 901.3;
- rural: all assumed, 3,801.0.

The lower and strong-adoption paths split the same way (assumed 72.9% and 73.8%), because every area's lower and strong-adoption levels are fixed multiples of its central level.

### 3d. Sensitivity: unknown rules, groupings, transferred response rates

`reference/gate5_sensitivity_summary.csv`, central, permits over 2027–2031. Differences are from the adopted baseline (604.6), addition (8,756.6) and total (9,361.3).

| Group | Case | Baseline Δ | Addition Δ | Total Δ |
| --- | --- | --- | --- | --- |
| Unknown rules | Uncoded like prohibited | −186.4 | +158.6 | −27.8 |
| Unknown rules | Uncoded like benchmark (Madison's rate) | +804.7 | −684.7 | +120.0 |
| Grouping | Context groups redrawn (any definition) | 0 | 0 | 0 |
| Grouping | Prohibited and restricted evidence pooled: 39 permits ÷ 720.33 thousand home-years = 0.0541, applied to the 1,909 areas on a group rate (1,555,488 homes) | −30.9 | +26.3 | −4.6 |
| Grouping | Rural towns only at the Madison floor | 0 | −3,275.9 | −3,275.9 |
| Grouping | Rural and small communities at the Madison floor (adopted case) | 0 | −3,991.3 | −3,991.3 |
| Response rate | Lower at the 10th percentile (changes the lower only: 4,443.1 instead of 5,538.1) | 0 | 0 | 0 |
| Response rate | California out of the between-state level | 0 | −1,100.0 | −1,100.0 |
| Response rate | LA-calibrated multifamily correction | 0 | −318.3 | −318.3 |
| Response rate | Eligible-property basis (Gate 3 run, own baseline 636.4) | +31.8 | −593.0 | −561.3 |
| Response rate | No ramp | 0 | +1,511.3 | +1,511.3 |
| Response rate | Madison on the statewide estimate | 0 | +191.4 | +191.4 |
| Response rate | Multiplicative law | 0 | −8,090.7 | −8,090.7 |
| Response rate | California-only market regression | 0 | −6,367.0 | −6,367.0 |

**Does grouping enter the model?** The context group is **not** an input:
- not to the pooled fit (`scripts/run_pooled_revision.py` uses home value, income, size, law, local reform and year terms);
- not to the engine (`engine.run` has no context argument).

It only labels results and selects the "rural at floor" sensitivity, so any redrawing of the four groups changes no area figure and no total, only the subtotals by group. The groupings that do enter are the **current-law evidence groups** (prohibited / restricted / benchmark). Pooling two of them moves the total by −4.6 permits. "Rural at floor" is a different kind of case: it does not regroup places, it replaces their with-law rate.

Response-rate cases come from `reference/adu_model_sensitivities.csv` (Gate 4, AQ-043). The largest are the two alternative model forms (multiplicative −8,091, California-only −6,367), followed by "no ramp" (+1,511) and "California out" (−1,100).

### 3e. Landing-screen "housing health" indicators

`reference/gate5_housing_health.csv`, Wisconsin, from `data/processed/foundation/state_conditions.parquet`:

| Theme | Indicator | Latest value | Period | Source | Uncertainty |
| --- | --- | --- | --- | --- | --- |
| Housing stock | Housing units | 2,840,960 | July 1 2025 (series 2020–2025) | Census PEP Vintage 2025 | none published |
| Housing stock | Housing units | 2,778,572 | ACS 2020–2024 | ACS B25024_001 | ± 1,533 (90%) |
| Occupancy | Occupied / vacant units | 2,479,480 / 299,092 | ACS 2020–2024 | ACS B25002 | ± 5,787 / ± 4,686 |
| Vacancy | Vacant ÷ all units | 10.76% (299,092 ÷ 2,778,572) | ACS 2020–2024 | ACS B25002 (calculated) | ± 0.17 points |
| Mix | Single-family detached / attached / 2–4 / 5+ / mobile homes | 1,839,569 / 120,679 / 260,128 / 472,263 / 84,807 | ACS 2020–2024 | ACS B25024 | MOEs in file |
| Age | Built 2020 or later | 38,983 | ACS 2020–2024 | ACS B25034 | ± 1,080 |
| Production | Permitted units, total / 1 unit / 2–4 / 5+ | 25,569 / 13,405 / 1,628 / 10,536 | 2025 (series 2015–2025) | Census BPS, final | 91.4% of units from reported (not imputed) data |
| Production | Permitted units per 1,000 housing units | 9.0 (25,569 ÷ 2,840,960) | 2025 | BPS ÷ PEP (calculated) | — |

All four themes exist with dates and sources, and the Gate 4 bundle already carries them (`state.json`: `homes`, `housing_units_pep`, `acs_total_units`, `occupied`, `vacant`, `vacancy_rate`, `mix`, `bps`).

**Gaps for the UI agent:**
1. **Vacancy includes seasonal homes.** The 10.76% counts every vacant unit, including seasonal and recreational cabins, which are a large share in Wisconsin. Label it "all vacant homes, including seasonal"; a for-rent/for-sale vacancy rate would need ACS B25004, which is not fetched.
2. **Production has no rate.** The bundle has counts only. If the screen shows a rate, show 9.0 permitted units per 1,000 housing units (2025) with its numerator and denominator, kept apart from the ADU rate (per 1,000 single-family homes).
3. **ACS figures are 5-year periods** (2020–2024), not a 2024 point. PEP is a July 1 estimate with no margin of error; say "no published margin".
4. **BPS rows in the bundle carry `vintage` and `reported_share` but no `source_id`.** Add "Census Building Permits Survey".
5. **No tenure or affordability indicator** (owner/renter share, home value or rent relative to income). The ACS market tables (B25003, B25077, B25064, B19013) are on disk if the owner wants one. Do not build a composite score (Gate 5 plan).
6. **Year built** (`built_2020_or_later`, 38,983 units) is available but not on the landing screen. It is optional.

## 4. Commands and tests

```
uv run python scripts/fetch_legislative_districts.py   # once: district layers and 2020 blocks into data/raw/
uv run python scripts/run_adu_model.py                 # adopted run (unchanged)
uv run python scripts/run_unknown_rules_variants.py    # section 1
uv run python scripts/build_district_allocation.py     # section 2
uv run python scripts/run_gate5_checks.py              # section 3
bash scripts/test.sh                                   # 340 tests OK
```

`tests/test_gate5_model.py` (20 tests, offline, reading the committed reference tables):
- **Variant functions:** the adopted variant changes nothing; the others change only uncoded areas; the contract enums are named.
- **Variant outputs:** one run group with three variants; the adopted variant equals `adu_model_statewide.csv`; like-prohibited gives −186.4 / +158.6 / −27.8; total = baseline + addition; the paths are in order; the baseline rises with the uncoded rate; county, context and area tables reconcile to the state.
- **`allocate()`:** splits and the unallocated row.
- **District outputs:** 99 + 1 and 33 + 1 rows per path and period; every path and year reconciles to the state; homes sum to 1,839,569; the unallocated row is 0; each Senate district is the sum of its three Assembly districts; crosswalk shares sum to 1; no owner or address fields; rates are consistent.
- **Trace and context tables** reconcile to the state.

## 5. Open items

- **Madison** stays on its observed path and is re-examined in December, when its 2026 count is final (owner decision).
- **Small, high-value villages**: no cap or pooling (owner decision); they keep high per-area rates. Example: Chenequa, 271 homes, 5.24 per 1,000 homes per year central.
- **Districts are shown for the adopted run only.** Unknown-rules variants by district were not computed; if the UI wants them, rerun `build_district_allocation.py` on `model_run/unknown_rules/results_long.parquet`.
- **DATA_COMPLIANCE.md** has no rows yet for the three new sources (LTSB districts, 2020 blocks), which are owned elsewhere. They are public and keyless, with terms recorded in DATA_PROVENANCE.md.
