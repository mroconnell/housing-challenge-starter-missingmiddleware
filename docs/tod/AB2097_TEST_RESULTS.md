# California AB 2097 test: results

The plan is [AB2097_TEST_PREREG.md](AB2097_TEST_PREREG.md), including its section 8 changes. Section 1 below was written on 2026-10-27 before any permit was counted by area; the rest was added after the run.

## 1. Lists fixed before counting

### 1a. Places coded "already no minimums"

Taken from `reference/parking_reform_taxonomy.csv` (California rows): records removing minimums rated "at" or "near" the benchmark and in force before 2023, plus records removing minimums near transit adopted before 2023. Each place is dropped whole from group P (near and ring), because the taxonomy has no boundaries for the downtown or transit-area records.

| Jurisdiction | Taxonomy record | Year | Why it is on the list |
|---|---|---|---|
| San Francisco | citywide, all uses, "at" | 2018 (adopted Dec 2018, in force 2019) | No minimums citywide before AB 2097 |
| Emeryville | citywide, all uses, "at" | 2019 | Same |
| Alameda | citywide, all uses, "at" | 2021 | Same |
| Culver City | citywide, all uses, "at" | 2022 | Same |
| Berkeley | citywide, residential, "at" | not dated in the taxonomy | A local citywide removal for all housing, not a restatement of AB 2097 |
| Pomona | downtown, all uses, "near" | 2019 (Downtown Pomona Specific Plan) | Rated "near"; downtown is Pomona's transit area |
| Eureka | districts, all uses, "near" | not dated | Rated "near" |
| San Diego | transit priority areas, all uses | 2019 | No minimums within ½ mile of major transit stops |
| Hayward | Mission Boulevard code area | 2020 | No minimums on a transit corridor |
| Fremont | Warm Springs/South Fremont plan area (BART) | 2015 | No minimums around a station |
| Oakland | CBD, S-2 and D-LM zones (downtown, BART) | not dated; local zones | No minimums in the downtown station area |
| Stockton | ¼ mile of the ACE station | not dated; local rule | No minimums near the station |

Kept as a sensitivity case only (dropped from the main estimate, prereg section 8 item 1): **San Jose** (adopted December 2022, in force spring 2023) and **Sacramento** (2024).

Not on the list:
- Santa Clara and Sunnyvale: undated records whose text repeats AB 2097's own rule (no minimums within ½ mile of a major transit stop), so they cannot be shown to predate it.
- Bakersfield, Mountain View and Long Beach (2024), and Modesto (2023, low-density only): adopted after AB 2097 took effect.
- Los Angeles and West Hollywood: proposals only.
- Records rated "weaker" for downtown business districts, fee-in-lieu programs and low-density or ADU-only exemptions: they did not remove minimums for apartments near transit.

### 1b. Areas upzoned before 2023

| Area | Source | Version |
|---|---|---|
| Los Angeles Transit Oriented Communities tiers 1–4 | LA City Planning, ArcGIS layer `TOC_Tiers_Oct2017_new` | Tiers as of October 2017 |

No other pre-2023 upzoned boundary is openly published. San Diego's Transit Priority Area and Complete Communities layers found online are later versions or private copies, so San Diego is not added (prereg section 2).

## 2. Answer in brief

- **Parking relief alone (group P): no measurable change.** Near transit, homes permitted rose from 10.9 to 12.6 a year per 1,000 existing homes; in the ring they rose from 7.2 to 8.7. The difference-in-differences is **+0.13 units a year per 1,000 existing homes, 90% interval −1.84 to +1.73**. For units in buildings of 2 or more units it is **+0.39 (−1.37 to +1.89)**. Both intervals include zero. They rule out a rise or a fall larger than about 1.8 units a year per 1,000 homes, about one-sixth of the near-transit rate before the law.
- **TOD plus parking (group T+P, Los Angeles only): −2.49 units a year per 1,000 existing homes (−5.50 to +0.52)**, and **−2.10 (−5.04 to +0.90)** for 2+ unit buildings. The interval includes zero, and it comes from resampling projects, because the group is one city.
- **Combination term (T+P − P): −2.62 (−6.07 to +0.98)** for all units and **−2.49 (−5.83 to +0.95)** for 2+ unit buildings. The interval includes zero, so there is no sign that parking relief added more where density had already been raised.
- **Displacement check: no sign of displacement.** The ring rose against land more than 1½ miles out, not fell.
- **Usable?** Group P passes the size rule (169 jurisdictions had near-transit permits in both periods; the rule needs about 10), so the P result can be used. It says California's statewide parking relief near transit had no effect large enough to see in three years. The T+P estimate and the combination term rest on one city. As the plan says, they are a sensitivity only.

All rates below are **units in issued building permits per year per 1,000 existing homes** (2020 census housing units in the same area), averaged over the years of the period, unless a row says per acre. "Before" is 2018–2022 (5 years) and "after" is 2023–2025 (3 years). Intervals are 90%.

## 3. Data kept

| Item | Value |
|---|---|
| Statewide units in issued building permits, Table A2 2018–2025 | 1,214,141 units (628,841 records) |
| Not geocoded to a street address (city or county fallback points, or no coordinates) | 88,546 units of 1,214,141 (7.3%) |
| Exact duplicate records dropped | 10,643 records, 30,547 units |
| Full-reporting jurisdictions (geocoded permits every year 2018–2025) | 360 of 531 jurisdictions that filed any year |
| **Share of statewide permits kept** | **1,005,786 of 1,214,141 units = 82.8%** (91.8% of geocoded, de-duplicated units) |
| Kept share by year (kept units ÷ geocoded units that year) | 2018 93.9%, 2019 91.5%, 2020 91.8%, 2021 91.5%, 2022 91.3%, 2023 89.7%, 2024 92.4%, 2025 93.4% |
| Existing major transit stops (Caltrans layer, current version) | 16,703 stops, of which 3,020 rail, bus rapid transit or ferry |
| Census 2020 blocks | 519,723 blocks, 14,392,140 homes |

Emeryville and Pomona, on the "already no minimums" list, are not full reporters, so they would have been left out anyway. The other ten places on the list are full reporters and are dropped from group P.

## 4. Group sizes

| | Group P | Group T+P |
|---|---|---|
| Jurisdictions | 185 | 1 (Los Angeles) |
| Jurisdictions with near-transit permits in both periods: all units | 169 of 185 | 1 |
| Same, units in 2+ unit buildings | 99 of 185 | 1 |
| Existing homes near transit (2020) | 1,276,507 | 747,147 |
| Land near transit | 252,772 acres | 74,837 acres |
| Existing homes in the ring | 2,695,619 | 345,201 |
| Land in the ring | 897,829 acres | 90,722 acres |
| Existing homes beyond 1½ miles (displacement check) | 3,256,007 | 146,275 |
| Projects with permits near transit, before / after | 14,042 / 11,687 | 10,052 / 8,267 |
| Of which with units in 2+ unit buildings, before / after | 1,746 / 879 | 2,123 / 1,532 |
| Projects with permits in the ring, before / after | 38,692 / 31,488 | 9,247 / 7,485 |
| Too-thin rule (needs about 10 jurisdictions with permits in both periods) | passes (169) | one city; jurisdiction interval not possible |

## 5. Main estimates

Units in issued permits per year per 1,000 existing homes. Each rate = units in the period ÷ years in the period ÷ existing homes in the area × 1,000.

| Group | Outcome | Near: before → after | Ring: before → after | Estimate (DiD) | 90% interval (method) |
|---|---|---|---|---|---|
| P | All units | 10.94 → 12.55 (69,812 units in 5 years and 48,068 in 3 years, ÷ 1,276,507 homes) | 7.22 → 8.71 (97,302 and 70,419 units ÷ 2,695,619 homes) | **+0.13** | −1.84 to +1.73 (jurisdictions) |
| P | 2+ unit buildings | 7.68 → 8.17 (49,019 and 31,297 units) | 3.18 → 3.28 (42,883 and 26,547 units) | **+0.39** | −1.37 to +1.89 (jurisdictions) |
| T+P | All units | 25.74 → 25.60 (96,140 and 57,375 units ÷ 747,147 homes) | 14.61 → 16.97 (25,219 and 17,571 units ÷ 345,201 homes) | **−2.49** | −5.50 to +0.52 (projects; one city) |
| T+P | 2+ unit buildings | 21.65 → 18.96 (80,888 and 42,506 units) | 5.20 → 4.61 (8,977 and 4,779 units) | **−2.10** | −5.04 to +0.90 (projects; one city) |
| T+P − P | All units | | | **−2.62** | −6.07 to +0.98 (T+P project draw minus P jurisdiction draw) |
| T+P − P | 2+ unit buildings | | | **−2.49** | −5.83 to +0.95 (same) |

Per acre of land (second measure; units in issued permits per acre per year; denominators: the land areas in section 4):

| Group | All units | 2+ unit buildings |
|---|---|---|
| P | +0.0037 (−0.0056 to +0.0115) | +0.0022 (−0.0059 to +0.0094) |
| T+P | −0.0103 (−0.0364 to +0.0154) | −0.0246 (−0.0503 to +0.0009) |
| T+P − P | −0.0140 (−0.0407 to +0.0133) | −0.0268 (−0.0530 to −0.0002) |

Only the per-acre combination term for 2+ unit buildings has an interval that just excludes zero, and only by 0.0002 units per acre a year. It is the same direction as every other T+P result, and it is not robust (see section 6).

Rates by year, all units per 1,000 existing homes (`reference/tod_ab2097_rates_by_year.csv` has units, homes, acres, projects and both outcomes):

| Group, area | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|
| P near | 9.4 | 11.0 | 10.9 | 10.3 | 13.1 | 13.3 | 10.1 | 14.2 |
| P ring | 5.2 | 7.0 | 6.4 | 8.2 | 9.2 | 9.1 | 7.8 | 9.2 |
| P beyond 1½ mi | 8.2 | 8.7 | 8.4 | 10.9 | 9.0 | 9.0 | 7.7 | 7.2 |
| T+P near (LA TOC) | 16.3 | 25.6 | 27.1 | 29.0 | 30.7 | 23.2 | 27.3 | 26.3 |
| T+P ring (LA) | 11.7 | 15.3 | 13.7 | 14.4 | 17.9 | 14.7 | 16.4 | 19.8 |

The P near-transit and ring lines move together before the law (both rise from 2018 to 2022), and keep moving together after it.

## 6. Sensitivities

Estimates in units a year per 1,000 existing homes, with 90% intervals (jurisdiction resampling for P; project resampling for T+P and its part of the combination term).

| Case | P, all units | P, 2+ units | T+P, all units | T+P, 2+ units | T+P − P, all units | T+P − P, 2+ units |
|---|---|---|---|---|---|---|
| **Main** | +0.13 (−1.84 to +1.73) | +0.39 (−1.37 to +1.89) | −2.49 (−5.50 to +0.52) | −2.10 (−5.04 to +0.90) | −2.62 (−6.07 to +0.98) | −2.49 (−5.83 to +0.95) |
| Project resampling instead of jurisdictions | +0.13 (−1.27 to +1.57) | +0.39 (−1.00 to +1.81) | same as main | same as main | −2.62 (−5.94 to +0.63) | −2.49 (−5.77 to +0.75) |
| After = 2023 only | +0.51 (−1.80 to +2.75) | +0.88 (−1.29 to +2.94) | −2.58 (−6.71 to +1.66) | −3.27 (−7.38 to +0.85) | −3.09 (−7.86 to +1.66) | −4.14 (−8.70 to +0.44) |
| After = 2024 only | −1.43 (−4.09 to +0.57) | −1.25 (−3.64 to +0.60) | −0.24 (−4.31 to +3.50) | +0.08 (−3.92 to +3.71) | +1.20 (−3.32 to +5.71) | +1.33 (−3.08 to +5.70) |
| After = 2025 only | +1.30 (−1.48 to +3.96) | +1.54 (−1.11 to +4.17) | −4.66 (−9.09 to −0.26) | −3.12 (−7.60 to +1.20) | −5.96 (−11.24 to −0.81) | −4.67 (−9.96 to +0.27) |
| Dropping 2023 (after = 2024–2025) | −0.07 (−2.30 to +1.79) | +0.15 (−1.94 to +1.94) | −2.45 (−5.86 to +0.86) | −1.52 (−4.81 to +1.66) | −2.38 (−6.18 to +1.50) | −1.67 (−5.39 to +2.05) |
| ¼-mile near-transit distance (P: 170 jurisdictions, 493,523 near homes) | −0.50 (−3.81 to +2.76) | −0.28 (−3.67 to +2.88) | −2.79 (−6.65 to +1.30) | −2.26 (−6.19 to +1.72) | −2.29 (−7.24 to +3.20) | −1.98 (−7.06 to +3.44) |
| Los Angeles city only (P = LA near transit outside TOC areas, 174,255 homes) | +2.97 (−0.24 to +6.24) | +3.11 (−0.00 to +6.30) | −2.49 (−5.50 to +0.52) | −2.10 (−5.04 to +0.90) | −5.46 (−10.15 to −1.09) | −5.22 (−9.90 to −0.87) |
| Leaving out the largest project in each group, area and period | +0.05 (−1.69 to +1.52) | +0.32 (−1.25 to +1.67) | −2.15 (−4.90 to +0.53) | −1.76 (−4.45 to +0.92) | −2.20 (−5.27 to +1.11) | −2.08 (−5.13 to +1.09) |
| San Jose and Sacramento kept in group P (187 jurisdictions) | +0.20 (−1.41 to +1.68) | +0.62 (−0.89 to +2.00) | −2.49 (−5.50 to +0.52) | −2.10 (−5.04 to +0.90) | −2.69 (−6.01 to +0.75) | −2.72 (−5.96 to +0.61) |
| Added check, not in the plan: rail, BRT and ferry stops only | −0.05 (−3.67 to +3.19) | +0.35 (−3.13 to +3.53) | −6.04 (−11.31 to −0.78) | −5.53 (−10.83 to −0.42) | −5.99 (−11.93 to +0.40) | −5.88 (−11.78 to +0.55) |

What holds across cases: the P estimate stays within about ±1.5 of zero, and every interval for P includes zero. The T+P estimate is negative in every case except 2024 alone. Its interval excludes zero only with 2025 alone or with rail, BRT and ferry stops only. The Los Angeles-only case is one city and P there fails the size rule.

## 7. Displacement check

If projects moved from the ring into the near-transit area, the ring would fall relative to land more than 1½ miles from any stop. It did not.

| Group | Outcome | Ring: before → after | Beyond 1½ mi: before → after | Ring minus beyond (DiD) | 90% interval |
|---|---|---|---|---|---|
| P | All units | 7.22 → 8.71 (÷ 2,695,619 homes) | 9.05 → 7.96 (147,398 and 77,732 units ÷ 3,256,007 homes) | +2.58 | +1.58 to +3.61 (jurisdictions) |
| P | 2+ unit buildings | 3.18 → 3.28 | 2.13 → 2.04 | +0.20 | −0.50 to +0.97 |
| T+P | All units | 14.61 → 16.97 (÷ 345,201 homes) | 14.26 → 13.93 (÷ 146,275 homes) | +2.69 | −0.11 to +5.90 (projects) |
| T+P | 2+ unit buildings | 5.20 → 4.61 | 3.91 → 1.97 | +1.35 | −1.41 to +4.43 (projects) |

The ring gained against land farther out, mostly in all units, not in 2+ unit buildings, which points to small infill such as ADUs rather than displaced apartments. So the near-versus-ring difference is not inflated by projects moving out of the ring.

## 8. What limits the result

- **Stop layer.** Only today's Caltrans layer could be fetched. It uses the 20-minute bus definition adopted after AB 2097, so some "near transit" land was not near a major stop in 2023 (prereg section 8 item 6). With rail, BRT and ferry stops only, P is still about zero (−0.05 a year per 1,000 homes, −3.67 to +3.19).
- **T+P is one city.** Los Angeles had partial parking relief in TOC areas before 2023, so T+P is a lower bound on the combination (prereg section 6). Other Los Angeles changes over the same years (for example the city's 2023 transfer tax on sales over $5 million and its December 2022 affordable-housing streamlining order) fall on TOC areas and cannot be separated from AB 2097 with one city. The T+P interval reflects project-to-project noise only, not city-to-city differences.
- **Three years after.** Projects permitted in 2023–2025 were mostly designed before or just after the law. Year by year the P estimate goes +0.51 (2023), −1.43 (2024), +1.30 (2025), with no trend.
- **Interest rates** rose in 2022–2023 everywhere. The ring comparison absorbs this as long as near and ring land were hit alike.
- **Self-reported data.** Keeping only full reporters keeps 82.8% of statewide permitted units. The kept share is steady across years (89.7% to 93.9%), so reporting changes do not look like an effect.

## 9. Files

- Code: `missing_middleware/tod/ab2097.py`, `scripts/fetch_ab2097_inputs.py`, `scripts/run_ab2097_test.py`; tests `tests/test_tod_ab2097.py` (synthetic fixtures).
- Outputs: `reference/tod_ab2097_results.csv` (every estimate: case, group, outcome, measure, rates, units, denominators, interval and method, jurisdiction counts) and `reference/tod_ab2097_rates_by_year.csv`.
- No addresses, APNs or tracking ids are committed. Project ids are one-way hashes kept in git-ignored files under `data/processed/ab2097/`.
