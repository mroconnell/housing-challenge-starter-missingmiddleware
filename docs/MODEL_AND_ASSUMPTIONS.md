# Model & Assumptions Overview

Missing Middleware: what three Wisconsin housing reforms would add to housing production over 2027–2031, how sure we are, and where the homes would go.

Assembled 2026-10-27 from the three reform sessions' adopted work. Part A (ADUs) is written for this document. Part B (parking) and Part C (transit-oriented density) are copied word for word from each reform session's own master copy, with only the heading levels changed, so they can be updated by the people who maintain them. Decision IDs in parentheses (for example AQ-043) point to the [assumptions log](ASSUMPTIONS_AND_QUESTIONS.md). Full source, licence and access details for every dataset are in [DATA_PROVENANCE.md](DATA_PROVENANCE.md) and are not repeated here. The plain-language ranking of the three reforms is in the [Policy Scenario Comparison](POLICY_SCENARIO_COMPARISON.md).

## About the tool as a whole

### The question

If Wisconsin passed one of the challenge's benchmark housing reforms, taking effect on a stylized date of 1 January 2027, how many more homes would be permitted over the five years 2027–2031 than under current law? How sure can we be, and where in the state would the extra homes be?

The tool is built for Wisconsin legislators, their staff and local officials. It covers the whole state and every one of its municipalities, and it reports results by county and by Assembly and Senate district.

### The three benchmark reforms

The challenge asks for a baseline and at least three of five benchmark reforms. The tool models three:

| Reform | What the modelled state law does | Part |
| --- | --- | --- |
| **Accessory dwelling units (ADUs)** | Allows one ADU on every lot with a single-family home, detached or attached, of at least 600 square feet, with no extra parking required. | A |
| **Parking requirement reduction** | Removes every minimum off-street parking requirement for housing, statewide. | B |
| **Transit-oriented density (TOD)** | Raises allowed heights and density near major transit stops, using California SB 79's minimum heights and densities. | C |

Missing Middle and development fee reduction are not modelled.

### What each reform counts

All three reforms count **housing units in issued building permits**, at the date the permit is issued, compared with current law over the same five years. A permit is not a finished home. The three reforms differ in which permits they count, so their numbers must be compared with care:

| Reform | Outcome counted | Current-law baseline, 2027–2031 | Rate denominator used inside the reform |
| --- | --- | --- | --- |
| ADUs | **Second homes on single-family lots**: ADUs plus single-family-to-duplex conversions on a lot that already has a home (AQ-032, AQ-039) | 530 permits statewide | Per 1,000 single-family (one-unit detached) homes: 1,839,569 homes (ACS 2020–2024, table B25024) |
| Parking | **All new housing units**, every building size | 122,619 permits statewide (the shared all-housing baseline, version 2) | Per 1,000 existing homes of all types (ACS 2020–2024, table B25002) |
| TOD | **All new housing units near major transit stops** | 14,464 permits in the station areas | Share of the 313,564 homes (2020 census) in the station areas |

The parking and TOD baselines come from one shared all-housing baseline built from the Census Building Permits Survey ([HOUSING_BASELINE.md](shared/HOUSING_BASELINE.md)). The ADU baseline comes from local permit records and coded local rules, because the Census survey does not say whether a new home was added to a lot that already had one. The [Policy Scenario Comparison](POLICY_SCENARIO_COMPARISON.md) puts all three on a common footing: additional permits over 2027–2031, as a share of the 122,619-permit all-housing baseline and per 1,000 existing Wisconsin homes.

### The five-year horizon

The forecast years are 2027, 2028, 2029, 2030 and 2031. Totals are summed over those five years unless a year is named. 2026 is shown in some tables as a bridge year but is not in any total. Each reform models a law in force from 1 January 2027. No reform models effects after 2031.

### What is common across the three reforms

- **Scenarios are named by what they mean, not by statistical confidence.** Each reform shows a lower, a central and an upper scenario, labelled by the real-world evidence they stand for: for ADUs, "sluggish adoption" (like the slowest statewide-law states), "typical adoption" and "strong adoption"; for parking, "no measurable change" and "high end of the evidence"; for TOD, "little", "typical" and "strong" response, each named after the study it uses. They are not confidence intervals. They show how much the real cases disagree.
- **A line drawn from real cases.** Each reform also shows the median of what real places actually did:
  - ADUs: the median observed path of the 8 states with a statewide ADU law (10,374 additional permits);
  - parking: the median repeal place, whose permit rate changed by −0.50 permits per 1,000 homes per year against similar places, which counts as 0 because a repeal is not modelled as removing homes;
  - TOD: the median of the three net-effect studies, which equals the typical scenario (2,509 additional permits).
- **Sensitivities are grouped by what they move.** Each sensitivity case changes one assumption and is labelled by whether it moves the statewide addition, only where the homes land, or only the current-law baseline.
- **Observed, calculated or assumed.** Each reform has a trace that says which numbers come from Wisconsin's own records, which are calculated from them, and which are assumed or transferred from elsewhere.
- **Everything reconciles.** Every reform's results are computed for each of Wisconsin's 1,925 municipality pieces and add up exactly to the 72 counties, the 99 Assembly districts, the 33 Senate districts and the state. Any part that cannot be placed is shown as an explicit "not allocated" row, never dropped.
- **Rebuildable.** Every number in this document is read from a committed table in `reference/`, written by a script in `scripts/` and checked by the automated tests.

### What the tool never claims

It does not forecast rents, prices, displacement, parking supply, traffic or transit ridership. It does not forecast any single lot or project. Its municipal and district figures are shares of a statewide estimate, not local forecasts. Every reform's response is transferred from places outside Wisconsin, because Wisconsin has not yet passed any of these laws.

---

## Part A. Accessory dwelling units (ADUs)

Written for this document from the final ADU packets: [Gate 3](gate3/README.md) (including its revision of 2026-10-26), [Gate 4](gate4/README.md), [Gate 5](gate5/README.md) and [Gate 5 model checks](gate5/MODEL_CHECKS.md). Adopted decisions: AQ-024 to AQ-043, AQ-058, AQ-061 (the ask-why fixes of 2026-10-28) and AQ-064 (the audit fixes of 2026-10-29). Engine outputs: [`reference/adu_model_statewide.csv`](../reference/adu_model_statewide.csv), [`adu_model_sensitivities.csv`](../reference/adu_model_sensitivities.csv) and [`adu_model_reference_lines.csv`](../reference/adu_model_reference_lines.csv).

### Purpose and Scope

**The question.** If Wisconsin passed the benchmark ADU law, in force from 1 January 2027, how many more second homes would be permitted on single-family lots over 2027–2031 than under current law?

**The answer.**
- Under current law, the model expects Wisconsin to permit **530 second homes on single-family lots over 2027–2031** (530.1 permits). That is about 106 permits a year. Divided by Wisconsin's 1,839.569 thousand single-family homes, it is 0.058 permits per 1,000 single-family homes per year.
- The law adds, over the same five years:

| Scenario | What it means | Additional permits, 2027–2031 | Total with the 530-permit baseline |
| --- | --- | ---: | ---: |
| Sluggish adoption (lower) | Like the average of the two slowest statewide-law states, Rhode Island and Oregon | **6,804** | 7,334 |
| **Like a typical statewide-law state (central)** | Like a typical statewide-law state | **10,679** | 11,209 |
| Strong adoption (upper) | The high end of what statewide-law states have reached; only California has gone higher | **19,535** | 20,065 |
| *Reference line* | The median path the 8 statewide-law states actually took, California included | **10,374** | 10,904 |

- The central's additions by year are 1,547, 2,048, 2,118, 2,475 and 2,490 permits in 2027–2031. The central adds 10,679.2 permits ÷ 1,839.569 thousand single-family homes ÷ 5 years = 1.16 permits per 1,000 single-family homes per year.
- **Revised 2026-10-28 (AQ-061, the ask-why fixes).** Before: baseline 605; lower 5,538, central 8,757, upper 16,889; reference line 8,851 permits. The changes: comparison-state counts are scaled up for towns that did not report; Massachusetts' 11-month first year counts as 11 months; Washington's law years start when its cities had to comply; seven more measured Wisconsin cities and villages join the current-law group rates; and the value gap of a few small, very high-value villages is capped at California's largest.
- **Revised 2026-10-29 (AQ-064, fixes from the independent audit).** Before: lower 6,734, central 10,788, upper 20,057; reference line 10,558 permits. After: lower 6,804, central 10,679, upper 19,535; reference line 10,374. The baseline stays 530. The changes:
  - Rhode Island's reporting share is now its share of single-family homes in the towns that reported: 0.8704 in 2023–2024 and 0.8099 in 2025, instead of 32 of 39 towns. Rhode Island 2021–2022 stay at 1.0, because there is no town list for those years, so they are likely under-corrected.
  - Massachusetts 2025 now comes from the state's official ADU tracker file: 1,230 permits in the 294 towns that answered (was 1,224). It is divided by those towns' share of single-family homes, 0.8090: 0.7208 for the 225 towns that answered for the full year, plus half of 0.1764 for the 69 that answered mid-year only. Before, the share was 293 of 351 towns (0.8348).
  - Maine keeps its published share (0.73, a share of people), because its file has no permit counts. A sensitivity case uses an estimated homes share (0.62).
  - Each comparison-state rate now divides by single-family homes in that year. Homes are ACS 2020–2024 homes moved back or forward by one-unit building permits. Before, every year was divided by 2020–2024 homes. A new sensitivity case shows the old way.
  - A note on mixed geographies was added to [PREDICTIVE_RESULTS.md](adu/PREDICTIVE_RESULTS.md) (audit item 7). It does not change any number.

**The outcome counted (AQ-032, AQ-039).** A *second home on a single-family lot* is any permanent dwelling with its own kitchen, legally permitted on a lot that already has a single-family home. That includes ADUs, single-family-to-duplex conversions and California's SB 9 second homes. Two rules keep the count honest:
- an ADU built together with a new house counts when the lot had a home before (a teardown and rebuild), but not when the lot was vacant, because that is ordinary new construction;
- the same definition is applied in every comparison state, so the comparison is not inflated.

**The law modelled.** The challenge benchmark: one ADU on every parcel with an existing single-family building; detached and semi-detached ADUs of at least 600 square feet; no extra parking. It is read narrowly (AQ-030): the law applies to single-family lots only, and it adds no right to an ADU on apartment or other multifamily lots.

**Geography.** The engine works on Wisconsin's 1,925 municipality pieces (cities, villages and towns, with a municipality split where it crosses a county line). Results add up to the 72 counties, the 99 Assembly districts, the 33 Senate districts and the state.

**In scope:** the statewide current-law baseline; the statewide addition from the law with three scenarios and a reference line; where the additions land; sensitivity cases and robustness checks; a Madison pilot.

**Out of scope:**
- completed homes, net additions after demolitions, rents and prices;
- a scenario in which localities act on their own without a state law (removed as outside the challenge, AQ-036);
- second homes on multifamily lots or on vacant lots;
- any effect after 2031.

### Core Assumptions and Their Rationale

| Assumption | Value or choice | Rationale | Source |
| --- | --- | --- | --- |
| Outcome | Second-home permits on single-family lots, at permit issuance (AQ-032) | Counts what the law changes, the same way in every comparison state; permits are the earliest well-recorded milestone | [Gate 3 packet](gate3/README.md) |
| Denominator for every ADU rate | 1,839,569 one-unit detached ("single-family") homes in Wisconsin | Each one is a lot the law makes eligible; the same measure exists in every state | ACS 2020–2024, table B25024_002 |
| Law in force | 1 January 2027 (stylized) | The challenge's five-year horizon starts in 2027; the same date is used for all three reforms | [Challenge spec](CHALLENGE_SPEC.md) |
| Current-law rate in places with their own permit data | Milwaukee 0.0863 (35 candidate permits ÷ 405.608 thousand home-years, 2022–2025, held flat); Madison 0.188 (40 permits ÷ 213.168 thousand home-years, 2022–2025); Pleasant Prairie 0.039 (3 permits ÷ 76.0 thousand home-years, 2014–2025). All in permits per 1,000 single-family homes per year. | Measured in the place's own records. Milwaukee's open permit data have no unit counts, so its 35 permits are unverified candidates (quality C). Its file through 2026-06-15 shows no clear rise after its August 2025 reform. | AQ-043; [WI_BASELINE.md](gate3/WI_BASELINE.md) |
| Current-law rate by coded rules group | Prohibited 0.023 (5 permits ÷ 214.274 thousand home-years), restricted 0.051 (36 permits ÷ 699.350 thousand home-years), already at the benchmark 0.188 (40 ÷ 213.168) permits per 1,000 single-family homes per year | Measured in Wisconsin places with each kind of rule. Prohibited: Pleasant Prairie, Sun Prairie, Howard, Neenah, and De Pere and Waunakee for their prohibited months. Restricted: Madison 2014–2023, Fitchburg, Green Bay, Verona, Watertown, and De Pere and Waunakee for their restricted months. Benchmark: Madison 2022–2025. These seven places joined on 2026-10-28 (AQ-061); Kaukauna and Milwaukee are left out. Rules are coded for the 37 largest municipalities. | AQ-026, AQ-027, AQ-037, AQ-061 |
| Places whose rules are not coded | Treated like places that restrict ADUs (0.051) | 1,267,433 of the 1,839,569 single-family homes (69%) are in such places. The middle choice; prohibited and already-allowed are both sensitivity cases. | AQ-023, AQ-027 |
| Rate with the law | From a pooled model of 8 statewide-law states and 5 cities. Once a statewide law is in force, one common level across states fits best. Two fits are used. A fit on home value, household income and number of homes sets Wisconsin's **statewide** rate. A fit on home value alone (slope about 1.03) **spreads that total across places**. Income and size do not move one Wisconsin place against another. | The with-law rate must come from measured data, not judgment (AQ-036). No Midwest state yet has data after a statewide law. | AQ-034, AQ-036, AQ-042, AQ-061, AQ-064; [POOLED_REVISION.md](gate3/POOLED_REVISION.md) |
| Places beyond California's value range | Each place's value gap is capped at the largest gap seen among California places (+1.01 in log terms, about 2.7 times its state's typical value) before allocation | 8 areas (7 villages and towns, 2,852 homes) sit further above Wisconsin's typical value than any California place sits above California's. Their uncapped levels were extrapolations. The cap moves about 16 central permits to other places; the statewide total does not change. Flagged places: [`adu_model_value_capped_places.csv`](../reference/adu_model_value_capped_places.csv). | AQ-061 |
| California in the common level | Yes (configuration A) | Predicts the 7 other statewide-law states better when each is held out: average log error 0.168 with California, 0.182 without (after AQ-064; 0.180 and 0.198 after AQ-061; 0.113 and 0.132 before AQ-061) | AQ-040, AQ-042, AQ-061, AQ-064 |
| Comparison counts cover all of each state | Counts divided by the reporting share: Maine 2025 ÷ 0.73 (share of people in 182 reporting towns), Massachusetts 2025 ÷ 0.8090 (share of Massachusetts' single-family homes in the 294 towns that answered the official tracker, mid-year-only towns at half weight), Rhode Island ÷ 0.8704 in 2023–2024 and 0.8099 in 2025 (share of Rhode Island's single-family homes in the 33 and then 32 of 39 towns that reported), Utah ÷ 0.795, 0.803 and 0.804 (2023–2025; share of Utah's single-family homes in the cities and counties that answered). Rhode Island 2021–2022 stay at 1.0 (no town list). Massachusetts 2025 counts as 11/12 of a year (law in force from 2 February). | Each count covers only reporting towns, but the rate divides it by every single-family home in the state. Maine's file has no permit counts, so its published share of people is used. Reporting towns are mostly larger, so Maine's homes share is likely lower (about 0.62; a sensitivity case). The uncorrected case gives a central of 9,397. | AQ-061, AQ-064; [`pooled_revision_coverage.csv`](../reference/pooled_revision_coverage.csv) |
| Comparison-state homes by year | Each comparison rate divides permits by single-family homes in that year: ACS 2020–2024 homes moved back or forward by one-unit building permits | Before AQ-064 every year used 2020–2024 homes, so early years read a little low and 2025–2026 a little high. Reading every year against 2020–2024 homes gives a central of 10,872 (a sensitivity case). | AQ-064 |
| Washington's law years | Counted from local compliance: estimate year 2026 (April 2025–March 2026) is year 1; 2024–2025 are left out | HB 1337 was enacted in July 2023, but cities had to adopt compliant rules only from 30 June 2025 (four largest counties) or later | AQ-061 |
| Comparison counts cleaned to the same outcome | California: at most 2 ADUs per parcel, and ADUs on multifamily parcels removed (87,303 → 81,368 units in 2023–2025). Other series × 0.951 for vacant-lot ADUs. Minneapolis × 0.873 for duplex-lot ADUs. | The benchmark law covers single-family lots with existing homes only. 0.951 = 1 − 0.049, where 4.9% is the median vacant-lot share of ADUs in 17 cities with demolition records. | AQ-039, AQ-041 |
| Ramp-up | The law's addition reaches 0.63, 0.83 and 0.86 of its full size in 2027, 2028 and 2029, and its full size from 2030 (central) | Measured in the pooled model's year-since-law terms | [Gate 3 packet](gate3/README.md), step 4 |
| Madison's own path | 0.452, 0.542, 0.601, 0.799 and 1.076 permits per 1,000 single-family homes per year in 2027–2031, in every scenario | Madison is the only Wisconsin place that meets the "Madison-like" definition, fixed before outcomes were read. The 9 Madison-like cities in Washington and Oregon ran at about half the model's rate in years 1–3. | AQ-040, AQ-042; [MADISON_LIKE_CITIES.md](gate3/MADISON_LIKE_CITIES.md) |
| Madison floor | No place's with-law rate is below 0.2345 permits per 1,000 single-family homes per year | Madison's 2022–2025 rate (40 permits ÷ 213.168 thousand home-years = 0.1876) divided by 0.8, because Madison's rules are about 80% of the benchmark | AQ-029, AQ-030, AQ-042 |
| No negative additions | The addition is never below zero | A law that adds a right does not remove permits | Engine rule |
| Lower scenario | Every place's central level × 0.6486 | The mean of Rhode Island's 0.8358 and Oregon's 0.7086 permits per 1,000 single-family homes per year (at a typical place, law in force 4+ years) is 0.7722, which is 0.6486 of the central's common level of 1.1905 | AQ-043, AQ-061, AQ-064 |
| Upper scenario | Every place's central level × 1.803 | The 90th percentile of how much the 8 states' levels differ from one another. At a typical place it is 2.15 permits per 1,000 single-family homes per year (1.1905 × 1.803); only California (2.41) is higher. | AQ-040, AQ-042, AQ-061, AQ-064 |
| Reference line | The median observed statewide rate of all 8 statewide-law states, by year since their law: 1.0073, 1.1255, 1.0231 and 1.3860 permits per 1,000 single-family homes per year in years 1–4 (from 7, 4, 4 and 4 states); 2031 repeats the 2030 value | Shows what real states did, with no model in between. Only California has a fifth year. Uses the same reporting shares, year-matched homes and Washington coding as the model (AQ-061, AQ-064). | AQ-043, AQ-061, AQ-064 |

### Data Sources and Cleaning Steps

Full source details, versions, access dates and licences are in [DATA_PROVENANCE.md](DATA_PROVENANCE.md). In summary:

- **Wisconsin homes and markets:** ACS 2020–2024 five-year tables (one-unit detached homes, B25024; median home value, household income, tenure and rent) by county subdivision; Census TIGER/Line 2024 boundaries; 2024 legislative district plans and 2020 census blocks for the district split.
- **Wisconsin permits:** local permit records from 13 Wisconsin places (Madison, Milwaukee, Pleasant Prairie, Sun Prairie, Fitchburg, Green Bay, De Pere, Howard, Kaukauna, Neenah, Verona, Watertown and Waunakee), with parcel and raze records used to apply the lot rules. Milwaukee's open permit data are combined with its Master Property file.
- **Wisconsin rules:** ADU ordinances of the 37 largest municipalities, coded by hand; the Wisconsin Department of Administration's land-regulation inventory and county and town zoning pages, to find towns with no general zoning.
- **Comparison states and cities:** California's Housing Element Annual Progress Reports (including project-level Table A2 with parcel numbers) and pre-2020 ADU counts; state ADU series for Washington, Oregon, Vermont (Chittenden County), Utah, Maine, Massachusetts and Rhode Island; permit files for Seattle, Portland, Austin, Denver and Minneapolis; statute and ordinance texts for each law.
- **Cleaning:**
  - every comparison series is cut to the same outcome (second homes on lots with an existing single-family home), using the cap and multifamily-parcel rule for California and the vacant-lot and duplex-lot factors elsewhere (Core Assumptions, above);
  - permit records are deduplicated, and twin-home and new-house permits are resolved with parcel year-built and raze records;
  - years run from each law's effective date, so year 1 is the first full year in force;
  - every download is fetched by script with its URL, date and checksum recorded. Raw files are not committed; the committed tables in `reference/` are aggregates.

### Methodological Approach

**In one sentence.** For each of Wisconsin's 1,925 municipality pieces, the law adds that place's single-family homes times the gap between its rate with the law and its rate today, phased in over the first three years.

**The equations.** For area *a* and year *t* in 2027–2031:

```
baseline[a, t] = H[a] × x[a] / 1000
addition[a, t] = max(0, H[a] × (y[a] − x[a]) × ramp[t] / 1000)
y[a]           = max(level from the pooled model for a, 0.2345)
```

where *H* is the number of one-unit detached homes, *x* the current-law rate and *y* the with-law rate, both in permits per 1,000 single-family homes per year. Madison uses its own yearly path for *y* with no ramp on top.

**Step by step.**
1. **Current-law rate (x).** Measured where a place has its own permit records (Milwaukee, Madison, Pleasant Prairie). Otherwise taken from the place's coded rules group, or, where rules are not coded, from the "restricted" group. The group rates pool every measured Wisconsin city whose rules in its measurement window are coded (AQ-061).
2. **Rate with the law (y).** A pooled model is fitted to California's 457 jurisdictions, the seven other statewide-law states (each labelled by the area actually measured: Washington outside Seattle, Oregon in 32 cities outside Portland, Vermont's Chittenden County, Utah's reporting cities, and Maine, Massachusetts and Rhode Island statewide) and five cities (Seattle, Portland, Austin, Denver, Minneapolis). Counts are divided by each state's reporting share, and Washington's law years start at local compliance (AQ-061). Each year's count is divided by that year's single-family homes (AQ-064). Across states, one common level fits best once the law is in force. Two fits then do two jobs:
   - **The statewide rate** comes from the fit on home value, household income and number of homes. Within a state, a place whose median home value is 10% above its state's average has about a 29% higher rate; at the same value, 10% higher household income goes with about a 25% lower rate; size barely matters. Applied to Wisconsin's 1,925 areas, this fit gives the statewide rate for each year.
   - **Each place's share** comes from the fit on home value alone (slope 1.03 on the log scale, `W_ALLOC` in `scripts/run_pooled_revision.py`). A place whose median home value is 10% above Wisconsin's average gets about a 10% higher level. The levels are then scaled so they add up to the statewide rate. Income and size do not enter this step. Each place's value gap is capped at California's largest (+1.01 in log terms) first.
3. **Ramp.** The addition is phased in at 0.63, 0.83 and 0.86 of its full size in 2027–2029 (central).
4. **Scenarios.** The lower multiplies each place's central level by 0.6486 and the upper by 1.803. Each has its own ramp, recomputed the same way.
5. **Sum and reconcile.** Areas are summed to counties and the state. Districts are shares of each municipality's result by where its single-family homes were in 2020 census blocks, with an explicit "not allocated" row (0.0 permits).

**Worked example 1, Madison (central).** Madison has 53,292 single-family homes. Its current-law rate is 0.188 permits per 1,000 per year, so its baseline is 53.292 thousand homes × 0.188 × 5 years = 50.0 permits. Its path sums to 0.452 + 0.542 + 0.601 + 0.799 + 1.076 = 3.470 permits per 1,000 homes over the five years. Its addition is 53.292 × (3.470 − 5 × 0.188) = 134.9 permits, in every scenario.

**Worked example 2, Christiana town, Vernon County (central).** It has 389 single-family homes and a current-law rate of 0.051 permits per 1,000 per year. Its central level is 1.869, and the central ramp sums to 0.6275 + 0.8305 + 0.8580 + 1 + 1 = 4.316. Its addition is 0.389 thousand homes × (1.869 − 0.051) × 4.316 = 3.05 permits over 2027–2031.

**Checks the model must pass to run.** The engine stops with an error if it fails to reproduce the pooled model's own totals to within 2 permits, or if a stored scenario factor or ramp does not follow from its source files. Lower ≤ central ≤ upper holds in every area and year. The 99 Assembly districts and the 33 Senate districts each add up to the statewide 530 baseline and 10,679 central additional permits.

**What rests on what (trace).** Of the 10,679 central additional permits:
- 559 (5.2%) are in the 3 places whose current-law rate is observed in their own permits;
- 2,261 (21.2%) are in the 37 places whose rate is calculated from a coded rules group;
- 7,859 (73.6%) are in the 1,848 places whose rules are not coded, so their current-law rate is assumed.

Every place's rate with the law is transferred from other states.

### Limitations and Known Edge Cases

1. **No Midwest state has data after a statewide ADU law.** The model contains no Wisconsin data after a law. Wisconsin permits 0.06 per 1,000 single-family homes per year today, where the pooled model's no-law level for Wisconsin would be 0.47. States with before-and-after data (California, Rhode Island, Washington, Vermont) reached similar first-year levels however low they started, but they are coastal or New England markets. Iowa's first full year (2026) will be the first Midwest test.
2. **Mid-size cities may be slower.** Madison-like cities in Washington and Oregon ran at a median 0.45, 0.54 and 0.60 permits per 1,000 single-family homes per year in years 1–3, about half the model's earlier path. Only Madison is moved onto that path. If Wisconsin's other mid-size markets behave the same way, the central is too high in its first three years.
3. **The hold-out test rests on 7 states.** California stays in the common level because it predicts the others better. That win holds in 64% of 5,000 resamples and in 6 of the 7 checks that drop one state (not when Washington is dropped). After AQ-064 the average log error is 0.168 (0.180 after AQ-061; 0.113 before AQ-061). Massachusetts and Washington are predicted closely (errors 0.02 and 0.07), but Vermont is over-predicted by about 39% (0.33) and Oregon by about 23% (0.20).
4. **Most current-law rates are assumed.** 73.6% of the central addition (7,859 of 10,679 permits) is in places with uncoded rules. This mostly moves the split between baseline and addition, not the total with the law (see Sensitivity Notes).
5. **Milwaukee's count is unverified.** Its 35 candidate permits come from open data with no description or unit count.
6. **Small, very high-value villages are capped.** 8 areas (7 villages and towns, 2,852 single-family homes) have home values further above Wisconsin's average than any California place is above California's. Their value gap is capped at California's largest before allocation (AQ-061; the owner had chosen no cap at Gate 4). For example, Chenequa (271 single-family homes) gets 3.79 permits per 1,000 single-family homes per year in the central, instead of 7.54 uncapped. The cap moves about 16 of the 10,679 central permits to other places. The flagged places are listed in [`adu_model_value_capped_places.csv`](../reference/adu_model_value_capped_places.csv).
7. **Rural areas get a large share.** Rural areas get 4,654 of the 10,679 central permits (43.6%) with 710,070 of the 1,839,569 single-family homes (38.6%), partly because a rural home's value includes its land.
8. **Districts are shares, not forecasts.** District figures share each municipality's result by where its single-family homes were in 2020. Homes built since 2020 and annexations are not reflected. At Gate 5, plain land-area weights would have moved 237 of the 8,757 central permits (2.7%) between districts (not rerun).
9. **Permits are not homes.** Not every permit becomes a finished home, and some second homes are built without permits.
10. **Associations, not proven causes.** Results describe what other states experienced after their laws.
11. **The before-and-after evidence is thin.** In the placebo test ([PLACEBO_RESULTS.md](adu/PLACEBO_RESULTS.md)) the strong-law and weaker-law groups have only 2 series each (California and Washington; Rhode Island and Chittenden County, Vermont). Against placebo groups of the same size (2 no-law series per draw), the strong-law group's change of +0.75 ADU permits per 1,000 one-unit detached homes per year is matched or beaten in 16% of draws (316 of 2,000), and the weaker-law group's +0.45 in 26% (about 520 of 2,000).
12. **Reporting shares are rough.** Maine's share is of people, not of homes. Massachusetts' and Rhode Island's are of homes since AQ-064, but Rhode Island's 2021–2022 counts have no town list and are not scaled up. Reporting towns are mostly larger. Using an estimated homes share for Maine (0.62) raises the central to 10,907 (+228). Without any scale-up the central would be 9,397 (−1,282).
13. **Vermont's counts are by year built.** Every Vermont count is by the year a unit was built or first occupied, not the permit year. Its 2024 count (57 ADUs) comes from the state's housing layer, not the regional planning commission's own series. Dropping 2024 lowers the central by 431 permits. Not adopted (AQ-062).

### Sensitivity Notes

Each case changes one assumption and reruns the model. Additional permits over 2027–2031 unless noted. Source: [`reference/adu_model_sensitivities.csv`](../reference/adu_model_sensitivities.csv); tornado chart: [sensitivity_tornado.png](gate3/sensitivity_tornado.png).

**Cases that move the statewide addition** (adopted: lower 6,804, central 10,679, upper 19,535):

| Case | Lower | Central | Upper |
| --- | ---: | ---: | ---: |
| Multiplicative law: each place's current rate × one statewide factor | — | 870 | — |
| California-only market regression | — | 2,435 | — |
| Rural and small-community places at the Madison floor (0.2345) | — | 5,687 | — |
| Lower as a statistical 10th percentile (every central level ÷ 1.803) | 5,768 | 10,679 | 19,535 |
| Eligible-property basis (its own 636-permit baseline; Gate 3 run, not rerun) | — | 8,164 | 15,318 |
| Comparison-state counts and coding as at Gate 4 (all three AQ-061 changes undone) | 5,609 | 8,769 | 16,756 |
| No scale-up for towns that did not report | 6,103 | 9,397 | 17,773 |
| California out of the common level | 6,804 | 9,623 | 15,285 |
| Washington's law years from enactment, not local compliance | 6,204 | 9,929 | 18,313 |
| Vermont 2024 left out (not adopted, AQ-062) | 6,658 | 10,249 | 19,384 |
| Los Angeles-calibrated multifamily correction | 6,675 | 10,280 | 17,685 |
| Scale-up for Maine, Massachusetts and Rhode Island only (Utah not) | 6,810 | 10,386 | 19,092 |
| Every comparison year read against 2020–2024 homes, not year-matched homes (as before AQ-064) | 6,838 | 10,872 | 20,091 |
| Maine's reporting share as a homes share (0.62, not 0.73; Maine's file has no permit counts to check it) | 6,804 | 10,907 | 20,314 |
| Madison at its pooled level instead of its path | 6,915 | 10,948 | 20,164 |
| Vermont left out of the comparison states (counts by year built, not permit year; not adopted, AQ-062). Reference line 11,071 permits (adopted 10,374) | 6,730 | 11,016 | 20,922 |
| No ramp: full rate from 2027 | — | 12,351 | — |

**A case that moves only where permits land:** without the cap on the value gap, small very high-value villages keep their extrapolated levels. The statewide central barely moves (10,679.2 → 10,679.9); about 16 permits move back to the 8 capped areas.

**Cases that move only the current-law baseline** (central). Because the rate with the law does not depend on today's rules, the addition moves the other way by about as much, and the total with the law barely moves:

| Case | Baseline | Change in addition | Change in total with the law |
| --- | ---: | ---: | ---: |
| Uncoded places behave like places that prohibit ADUs | 351.7 | +153.9 | −24.4 (−0.2%) |
| Uncoded places behave like places that already allow ADUs as the bill would | 1,393.0 | −744.9 | +118.0 (+1.1%) |
| Milwaukee rises to Madison's rate after its 2025 reform | 570.3 | −36.5 | +3.7 |
| Madison's rate = its 2026 pace so far (provisional) | 739.2 | −129.4 | +79.7 |
| Madison's rate from 2024–2025 only | 542.6 | −12.5 | 0.0 |
| Madison's rate without one builder's templated programme | 521.3 | +8.8 | 0.0 |
| Wisconsin's baseline rises like no-law places (×1.11 a year) | 949.7 | −383.8 (lower −382.9, upper −384.4) | +35.8 (+0.3%) |

Percentages are of the adopted central total with the law, 11,209.3 permits.

- **Placebo test and the rising-baseline check (AQ-058).** Rates are ADU permits per 1,000 one-unit detached homes per year, after the law (3 years) minus before it (3 years). Strong-law places changed by +0.75, weaker-law places by +0.45 and no-law places by +0.25 (median of 2,000 placebo draws; ratio 1.52, from 0.53 to 0.75), so the order is strong > weak > none ([PLACEBO_RESULTS.md](adu/PLACEBO_RESULTS.md)). The no-law rise disappears (change −0.04) once windows holding a local reform are removed. The last row lets every Wisconsin place's rate rise like the no-law places anyway: baseline 949.7 instead of 530.1 permits over 2027–2031; addition 6,421.1 / 10,295.4 / 19,150.5 instead of 6,804.0 / 10,679.2 / 19,534.9 (lower / central / upper); central total with the law 11,245.1 instead of 11,209.3 (+35.8 of 11,209.3). It is a check, not the main case, because Wisconsin's main local reform (Madison 2021) is already in the measured baseline.

**Reading.** What we do not know about local rules moves the split between baseline and addition, not the total. What moves the total is how Wisconsin responds compared with the eight states, how the comparison states' counts are read, and the model form. The two alternative model forms (multiplicative law 870; California-only regression 2,435) are the largest downside cases. The AQ-061 comparison-state changes together add 1,910 central permits (8,769 → 10,679). Without the ramp, the central would be 1,671 permits higher. Redrawing the urban, suburban, small-community and rural groups moves nothing, because the groups are labels only.

**Robustness checks** (alternative methods scored on the 7 held-out non-California statewide-law states; average log error, lower is better): the adopted measure, ADU units per one-unit detached home, scores 0.168 after AQ-064 (0.180 after AQ-061; 0.113 before AQ-061). The alternatives were scored at Gate 3 and not rerun: permits instead of units 0.132; the eligible-property basis 0.168 without and 0.202 with attached homes.

#### Held-out test: predicting a state the model never saw

Each of the 7 non-California statewide-law states is left out in turn. The model is refitted on the rest and predicts the left-out state's ADU permits per 1,000 single-family homes per year over its law years. Log error = log(predicted ÷ observed); +0.10 is about 10% too high. Details: [IMPROVE_R1_RESULTS.md](adu/IMPROVE_R1_RESULTS.md).

| State | Observed rate | Adopted model | Plain average of the other states | Median of the other states |
| --- | ---: | ---: | ---: | ---: |
| Washington | 0.77 | +0.07 | +0.52 | +0.37 |
| Oregon | 0.87 | +0.20 | +0.42 | +0.31 |
| Rhode Island | 1.13 | −0.12 | +0.16 | +0.04 |
| Massachusetts | 1.01 | +0.02 | +0.28 | +0.16 |
| Maine | 1.24 | −0.15 | +0.05 | −0.11 |
| Utah | 1.29 | −0.07 | +0.01 | −0.14 |
| Vermont | 0.90 | +0.33 | +0.41 | +0.28 |
| **Root mean square** | | **0.168** | 0.319 | 0.230 |

- **Vermont's outcome differs.** It counts ADUs when built, not when permitted. Most ADUs are finished the calendar year after their permit (63% of Austin's; median 0.97 years). Counted one year earlier, Vermont's miss falls to +0.19, the root mean square to 0.135, and the central rises from 10,679 to 10,834 additional permits. Left out entirely, the central is 11,016. Not adopted; awaiting the owner's decision (improvement loop round 1).
- **Maine's reporting share is a share of people** (0.73), because its town list is not published. A homes share of about 0.62 is likely; it would raise the central to 10,907 and the upper to 20,313.

#### Testing more advanced models

We tested whether flexible models predict ADU permits better than this model. The test was written down before any results were seen ([PREDICTIVE_PLAN.md](adu/PREDICTIVE_PLAN.md), [PREDICTIVE_RESULTS.md](adu/PREDICTIVE_RESULTS.md)).

- **Data:** 13,666 place-years and census-tract-years.
  - California towns and cities, 2018–2025.
  - Washington and Oregon cities.
  - Other statewide-law states.
  - Census tracts in Seattle, Portland, Austin, Denver, Minneapolis and Madison.
  - About 100 Census variables for each row.
- **Methods:** a two-part causal forest, boosted trees and a penalised regression. Each was compared with the plain average and with this model refitted on the same rows.
- **Pass rule:** beat both, on most held-out states and cities, and hold up with other random seeds.
- **Result on the final data:**
  - **How much:** this model missed least, by 0.19 permits per 1,000 single-family homes per year, against 0.27 for the plain average. Every flexible method failed.
  - **Where:** boosted trees passed with one random seed only and failed the repeat runs. No method passed reliably.
- **Decision (owner, 2026-10-29):** keep this model, and add no extra "where" line.

### Intended Users and Appropriate Use Cases

**Intended users:** Wisconsin legislators and their staff, and local officials and planners.

**Appropriate uses:**
- judging the likely statewide size of a benchmark ADU law over five years, with the range across real statewide-law states;
- seeing which kinds of places and which counties and districts would get the most, as shares of the statewide estimate;
- seeing which parts of the estimate rest on Wisconsin's own records and which are assumed or transferred;
- comparing the ADU law with the parking and TOD reforms on a common basis (see the [Policy Scenario Comparison](POLICY_SCENARIO_COMPARISON.md)).

**Not appropriate:**
- forecasting a single lot, neighbourhood or project;
- treating a municipal or district figure as a local forecast or a target;
- reading the scenarios as statistical confidence intervals;
- counting the results as completed or net new homes, or as an effect on rents or prices;
- forecasting beyond 2031, or a law that differs from the benchmark (for example one that allows ADUs on multifamily lots).

---

## Part B. Parking requirement reduction

> **Maintained by the parking session.** This part is a word-for-word copy of [docs/parking/MODEL_AND_ASSUMPTIONS_PARKING.md](parking/MODEL_AND_ASSUMPTIONS_PARKING.md) as of 2026-10-27, with only its heading levels changed. Edit the master copy, not this one. Its links are rewritten to resolve from `docs/` by `scripts/sync_model_doc.py`.

### Model & Assumptions: parking requirement reduction

Written 2026-10-27 by the parking conductor. Status: the parking section for the project's [Model & Assumptions Overview](MODEL_AND_ASSUMPTIONS.md), which is a shared file. It follows that file's headings, so the coordinator can merge it there.

#### Purpose and scope

**The question.** If Wisconsin removed minimum parking requirements for all housing from 1 January 2027, how many more homes would be permitted over 2027–2031 than under current law, how sure are we, and where would they be?

**The outcome.** New housing units authorized by building permits, counted at permit issuance, in all building sizes. The unit is the same as in the ADU scenario.

**The law modelled.** No minimum off-street parking may be required for any housing, statewide. This matches the challenge benchmark ("Reduce or eliminate minimum parking requirements"), read as "eliminate". North Carolina's HB 162 (signed 6 July 2026, in effect 1 January 2027) is the closest real law. It has no permit data yet.

#### Core assumptions and their rationale

1. **Developer-provided parking without mandates (the benchmark's required assumption).** We assume developers keep building the parking that renters, buyers and lenders want. A repeal adds homes only where a minimum forced more parking than the market wanted. The evidence:
   - **Buffalo**, after its 2017 citywide repeal (Hess, D. B., and Rehler, J. (2021), "Minus Minimums: Development Response to the Removal of Minimum Parking Requirements in Buffalo (NY)", *Journal of the American Planning Association* 87(3), 396–408, doi:10.1080/01944363.2020.1864225; read in full): 36 major projects provided 79% of the spaces the old minimums required. Mixed-use projects provided 47%. Stand-alone apartment buildings provided 117%, or 1.34 spaces per unit against a minimum of 1.
   - **Seattle, Minneapolis and Champaign:** similar reductions in parking built. These are source leads, not yet checked against the full papers.

   The scenario does not set a parking ratio itself. It uses the permit outcomes of places that repealed, so whatever parking their developers chose is already built into the result. As an illustration, for Wisconsin we assume developers would build about four-fifths of the spaces today's minimums require, and about all of them for stand-alone apartment buildings, as in Buffalo (79% and 117%). The permit numbers do not depend on this illustration.
2. **Evidence from cities and villages, not states.** No state has removed minimums for all housing long enough to measure. The response comes from 76 US places that did, between 2016 and 2024 (expanded from a first set of 24, then 71; on 2026-10-28 three dropped places were rescued, South Bend, Gastonia and Avondale Estates, and two more were found, Maumee and Saranac Lake; [EXPANDED_RESULTS.md](parking/EXPANDED_RESULTS.md), [SALVAGE_RESULTS.md](parking/SALVAGE_RESULTS.md), [PARTIAL_REFORMS_RESULTS.md](parking/PARTIAL_REFORMS_RESULTS.md)):
   - each checked against its ordinance;
   - each compared with similar places in its own state (falling back to its Census division when the state has too few) that kept their minimums.
   A second, independent check agrees. California's AB 2097 removed minimums within ½ mile of major transit stops in 2023. Near transit, permits changed by +0.13 permits per 1,000 existing homes per year against areas ½ to 1½ miles away (90% interval −1.84 to +1.73, 185 jurisdictions); see [COMPARISON_RESULTS.md](parking/COMPARISON_RESULTS.md).
3. **Central case, "No measurable change" (0 added).** In the one to three years after repeal, the repeal places' permit rate changed by −1.14 permits per 1,000 existing homes per year compared with similar places. The 90% range (5th to 95th percentile of 2,000 resamples) is −3.47 to +1.43 permits per 1,000 existing homes per year. A repeal is not modelled as reducing permits, so the central case is 0.
4. **Upper case, "High end of the evidence".** +1.49 permits per 1,000 existing homes per year (owner decision, 2026-10-27, option B; placebo fix approved 2026-10-28). It comes from the control-city (placebo) test. 9,420 cities that never repealed were given the real places' repeal years, with at least 20 stand-ins for each real place, drawn from its state, then its Census division, then the nation, at ½–2× population. Their 20,000 set averages run from −2.28 to +2.64 (middle 90%), around a middle of +0.01. Centred on the real average of −1.14, that spread runs from −3.44 to +1.49. This agrees with resampling the 76 places (95th percentile +1.43, 19,186 permits). An earlier version gave big cities only 1 to 4 stand-ins, which gave a lumpy spread and a false lean toward growth; it gave +0.95 (12,695 permits). The first 24 places' +2.21 is kept as a sensitivity. The rate is applied to the 2,684,793 existing Wisconsin homes outside the 9 places that already have no minimums (10 municipality pieces, because Brodhead spans two counties). That gives 19,937 permits over 2027–2031, 16.3% above current law (19,937 of 122,619).
   **Shared reporting (AQ-054).** In additional homes permitted per year against the shared all-housing baseline, the central case adds 0 a year and the upper case about 3,987 a year. Home counts that compare reforms use ACS 2020–2024 total housing units: 2,778,572 statewide, of which 2,684,793 are outside places already at the benchmark. The median of real cases, applied to Wisconsin, is shown as a reference line: the median repeal place changed by −0.12 permits per 1,000 existing homes per year. Since a repeal is not modelled as reducing permits, the line sits at 0, the same as the central case.
   **Control-city (placebo) check.** 9,420 cities that kept their minimums were given the real places' repeal years and run through the same calculation, 20,000 times. 21.7% of these placebo studies came out as low as the real places. The real result is ordinary, with no sign that a repeal raised or lowered permits. Their spread sets the upper case ([PLACEBO_RESULTS.md](parking/PLACEBO_RESULTS.md); review in [ASK_WHY_REVIEW.md](parking/ASK_WHY_REVIEW.md)).
   **Near-transit evidence (owner decision, 2026-10-28: reported, not used in the totals).**
   - **What was compared:** reform areas, Seattle's 2012 urban villages and Minneapolis's 2015 near-rail cut (36 areas, census blocks 2000–2020), against 1,040 rail station areas in cities with no parking reform. Each area was measured against the rest of its own city.
   - **Result:** with the same growth before and the same size, reform areas gained +18.8 extra homes per 1,000 existing homes per year (90% range +9.3 to +28.2).
   - **Why it is not used:** Seattle holds 78% of the reform-area homes and had light rail, upzoning and a jobs boom in the same years. Without adjusting for earlier growth, the gap is only +3.9. No model predicted held-out regions.
   - **Effect on the tool:** none. The scenario keeps its range, and this is reported as the strongest evidence that removing parking minimums near rail can add homes.
   - Details: [NEAR_TRANSIT_PLACEBO_RESULTS.md](parking/NEAR_TRANSIT_PLACEBO_RESULTS.md), [NEAR_TRANSIT_PREDICT_RESULTS.md](parking/NEAR_TRANSIT_PREDICT_RESULTS.md), [BLOCK_CATALOG_RESULTS.md](parking/BLOCK_CATALOG_RESULTS.md).
5. **Timing.** The effect was measured over years 1–3, and it does not build up over time. The upper case is held flat through 2031. That is an assumption, and the measured path suggests it is generous.
6. **Where the upper case lands.** It is spread in proportion to existing homes, because the comparison could not tell which kinds of places respond more (owner decision AQ-046; no size split beat one average).

#### Data sources and cleaning steps

| Data | Use | Licence |
| --- | --- | --- |
| Census Building Permits Survey: Wisconsin places 2015–2025; all US places 2012–2025; state totals 1990–2025 | Baseline; repeal comparison; baseline range | Public domain |
| ACS 2020–2024 (housing units, population, rent) | Existing homes; matching comparison places | Public domain |
| Milwaukee Master Property file | Milwaukee's apartment permits, which the Census file under-counts | CC-BY |
| Parking Reform Network reform map (pinned commit) | Which places removed minimums, and how fully | MIT |
| Municipal codes and ordinances (46 places) | Checking each repeal: in force, dates, exceptions, other zoning changes | Public records, cited |

Cleaning is recorded in [HOUSING_BASELINE.md](shared/HOUSING_BASELINE.md), [POLICY_TAXONOMY.md](parking/POLICY_TAXONOMY.md) and [COMPARISON_PLAN.md](parking/COMPARISON_PLAN.md) (deviations 1–4). Every download is fetched by script, with URL, date and SHA-256 recorded.

#### Methodological approach

**Baseline.**
- Census permits are allocated to the 1,925 municipality pieces, and reconciled to the state through an explicit unallocated row.
- Each place is held at its 2023–2025 average. That window was chosen by a held-out-year test against trend and other window lengths.
- The range is Wisconsin's 10th–90th percentile five-year outcomes since 1990.

**Response.** A pre-registered before/after comparison, a difference in differences:
- each place's change in permits per 1,000 existing homes, minus the same change in its comparison places;
- averaged with each place weighted by its homes;
- tested by leaving one place out at a time, resampling, leaving one state out, and other checks.

**Scenario.** Option A (owner, 2026-10-26): central 0, upper at the high end of the likely range. Places already at the benchmark get 0.

#### Limitations and known edge cases

- The sample is 76 places, and most repealed as part of a wider zoning rewrite. Parking's own effect cannot be fully separated out. Some places have only one or two years since repeal.
- No prediction tool (weighted regression, lasso, random or causal forest) and no city trait beat one average on places left out of the fit, so every Wisconsin place gets the same rate.
- The after period is three years. Larger projects may take longer to reach a permit.
- The places chose to repeal, so they may differ from places that did not.
- The Census permit data have reporting gaps. Milwaukee's apartments are estimated, and its 2025 figure is missing.
- The upper case is spread by homes, not by where minimums actually bind. Rural towns with few minimums get a share.
- The tool does not estimate rents, parking supply, traffic or street-parking spillover.
- **Timing of place traits (audit 2e, 2026-10-29):** population (used to match comparison places), existing homes (the rate's denominator), relative rent and the metro flag all come from ACS 2020–2024. That is after most repeals (2016–2024). If a repeal raised a place's growth, its 2020–2024 homes and population are a little higher, which lowers its measured rate slightly and can shift its comparison window. The trait tests that used rent and metro (none passed) share this caveat. Pre-repeal values would need ACS 5-year tables from before each repeal.
- Whether evidence from cities that repealed by choice may stand in for a statewide law is still open: office-hours question 26.
- The baseline and the bundle rebuild exactly from the committed reference tables. A full rebuild from raw data follows the order in [REBUILD.md](parking/REBUILD.md).

#### Sensitivity notes

Five-year totals, 2027–2031, in additional permits unless noted. All are in the tool under "How sure".

| Changes | Case | Value |
| --- | --- | ---: |
| The statewide total | Resampling the 76 real places (earlier high end) | 19,186 |
| The statewide total | Only buildings of 2 or more units counted (resampling) | 10,373 |
| The statewide total | Without San Francisco (resampling) | 24,520 |
| The statewide total | Combined with California's transit-area law | 15,138 |
| The statewide total | First 24 places only (earlier estimate) | 29,662 |
| The statewide total and where it lands | Prediction by city size and setting (first 24 places) | 32,135 |
| The statewide total and where it lands | Towns left out | 13,866 |
| The statewide total and where it lands | Places that partly removed minimums left out | 19,818 |
| Current law only | Census as published for Milwaukee | 118,822 permits under current law |

Stability (first 24 places): leaving one state out at a time gave an average effect of −2.47 to +0.09 permits per 1,000 homes per year.

#### Intended users and appropriate use cases

Wisconsin legislators and staff asking whether a statewide parking repeal would raise housing production.
- **Appropriate:** reading the result as "little or no measurable change within five years, with a stated high end", and seeing where that high end would fall.
- **Not appropriate:** reading municipal figures as local forecasts; using them to judge a parking repeal's effect on rents or parking supply.

## Part C. Transit-oriented density (TOD)

> **Maintained by the TOD session.** This part is a word-for-word copy of [docs/tod/MODEL_AND_ASSUMPTIONS_TOD.md](tod/MODEL_AND_ASSUMPTIONS_TOD.md) at commit 935edaf (2026-10-27), with only its heading levels changed. Edit the master copy, not this one. Its links are rewritten to resolve from `docs/` by `scripts/sync_model_doc.py`. Two changes made after the TOD Gate 3 check await the owner's confirmation; neither changes the statewide totals: keeping the measured New York build-up unsmoothed, and scaling the suburbs' share of the placement by 0.719.

### Transit-oriented density (TOD): model and assumptions

Master copy for the TOD section of [MODEL_AND_ASSUMPTIONS.md](MODEL_AND_ASSUMPTIONS.md). Last updated 2026-10-27 (AQ-053, AQ-054, AQ-057). Decisions: AQ-044 to AQ-051 in [ASSUMPTIONS_AND_QUESTIONS.md](ASSUMPTIONS_AND_QUESTIONS.md). Detail: [GATE3_PACKET.md](tod/GATE3_PACKET.md), [MODEL.md](tod/MODEL.md).

#### 1. Purpose and scope

The tool estimates how many more homes would be permitted in Wisconsin over 2027–2031 if the state passed the challenge's transit-oriented density benchmark: higher allowed heights and floor area near major transit stops.

- **Outcome:** housing units in issued building permits, compared with current law in the same places. Not completed homes.
- **Law start:** a stylized 1 January 2027.
- **Scope of the reform:** the reform is modelled on its own. Parking minimums are not changed; they belong to the parking scenario. A separate combined view shows the two together.
- **Where it applies:** within ½ mile of streetcar and rapid bus stations, and within ¼ mile of bus routes with service every 15 minutes or better at the morning peak.
  - That covers 313,564 of Wisconsin's 2,727,726 homes in the 2020 census (11.5%).
  - 98.7% of those homes are in Milwaukee County and Dane County.

**Shared reporting units (AQ-054).** For comparison across reforms, the TOD scenarios are restated against the statewide all-housing baseline and on Wisconsin's ACS 2020–2024 home count. These figures are not stacked or added to the other reforms.

| Scenario | Extra homes permitted a year, statewide | As a share of the statewide all-housing baseline (122,619 homes over 2027–2031) | As a share of Wisconsin's 2,778,572 homes (ACS 2020–2024) |
| --- | --- | --- | --- |
| Little | about 34 | 0.14% | 0.006% |
| Typical | about 502 | 2.0% | 0.09% |
| Strong | about 3,430 | 14.0% | 0.62% |

The station-area share in section 2 (0.055%, 0.8% or 5.5% of the 313,564 homes near stops) stays on the 2020 census count, because the station areas are built from census blocks.

**No median line for TOD.** A median line of real cases is shown only when a reform has at least 4 comparable cases. TOD's scenarios rest on 3 whole-city studies, so it has none.

#### 2. Core assumptions and their rationale

- **What counts as a "major transit stop" (AQ-044, AQ-047).** The main definition is rail and rapid bus (the Hop and Kenosha streetcars, Milwaukee's CONNECT 1, Madison's Rapid Route A) plus any stop on a route running 4 or more trips an hour in one direction at 7:00–8:59 on weekdays.
  - The 15-minute test matches California, Colorado and most state laws, and every Wisconsin agency's own schedule can measure it.
  - Amtrak stations are excluded: they run far fewer than the 48 trains a day that California's SB 79 requires for commuter rail.
  - The distances (½ mile for rail and rapid bus, ¼ mile for bus) follow the state laws reviewed. No study measures how the building response falls off with distance.
- **The law (AQ-047, AQ-049).** We use California SB 79's minimums for light rail and dedicated-lane bus:
  - 65 feet, floor area ratio (FAR) 3.0 and 100 homes per acre within ¼ mile of a station;
  - 55 feet, FAR 2.5 and 80 homes per acre from ¼ to ½ mile;
  - the same 55-foot standard within ¼ mile of 15-minute buses. This last one is our extension: no law sets a floor for ordinary buses.

  The law is by right, with no opt-outs and no affordability mandate. We looked for a better design in the evidence, but no measured design outperformed the others once held-out cases were checked.
- **Size of the effect (AQ-050).** Each scenario is a share of the homes in the station areas, taken from a study of the whole-city net effect after upzoning:
  - Little response, like Los Angeles's Transit Oriented Communities program: 0.055% over five years.
  - Typical response, like the average loosening reform across 1,136 US cities (Stacy et al. 2023): 0.8%.
  - Strong response, like Auckland's 2016 upzoning: 5.5%.

  The Los Angeles and Auckland figures are divided by the share of each city the reform covered (61% of homes and 75.2% of residential land), so they apply per upzoned home.
- **Never subtracts.** Places already at or above the law get no addition. No addition is negative.
- **Timing.**
  - Little and typical follow the yearly build-up measured after 17 New York City rezonings in 2003–2013.
  - Strong follows Auckland's own yearly pattern.
  - The build-up was fixed before the results were seen, and is not smoothed.

#### 3. Data sources and cleaning steps

All data are fetched by script, with the source, date, size and checksum recorded. Raw files are not committed ([DATA_PROVENANCE.md](DATA_PROVENANCE.md)).

- **Transit stops and routes:** the U.S. DOT National Transit Map (BTS, compiled 23 September 2026; 27 Wisconsin agencies, 13,052 stops).
  - Route frequency comes from 16 agencies' own GTFS schedules. Milwaukee's official file timed out, so a May 2025 copy from the Mobility Database is used.
  - Madison's frequency comes from its route descriptions in the National Transit Map. Madison Metro's own file is not used while its licence is an open question for office hours (AQ-045).
  - Amtrak stations come from the BTS Amtrak Stations layer.
- **Homes near stops:** 2020 census blocks (housing units), with a block counted when its internal point lies within the distance.
- **Land and zoning:**
  - Wisconsin statewide parcels (V12) for the six counties with qualifying stops.
  - Milwaukee zoning: 52 districts, including the 2025 RT5 district.
  - Madison zoning: 44 districts, plus the 2023 TOD overlay.
  - Existing homes: Milwaukee's property file and Madison's assessor data.
  - Suburbs' zoning is not coded. Their room to build is estimated from existing density, then scaled by 0.719, the ratio of coded to estimated capacity measured in Milwaukee and Madison.
- **Floor area per home:** measured from permits for new buildings of 5 or more homes, 2018–2025:
  - Madison: 1,512 sq ft;
  - Milwaukee: 1,192 sq ft;
  - pooled: 1,467 sq ft.
- **Baseline:** the shared all-housing baseline (Census Building Permits Survey, with Milwaukee's apartments taken from the city's property file, AQ-048). Each place's baseline is split by its share of homes near stops.
- **Comparison cases:** city permit files with unit counts and dates, matched to parcels and zoning before and after the reform.
  - Cases: Charlotte, New York (Park Slope, Downtown Brooklyn and 17 rezonings pooled), Philadelphia, Chicago, Saint Paul and Madison.
  - Cleaning: duplicate and staged permits are removed, and the per-year counts are checked against the Census survey.
  - Privacy: no parcel or permit numbers are committed.

#### 4. Methodological approach

1. **Policy research.** Ten state laws were classified against the benchmark from their statute text. None fully meets it; California SB 79, Washington HB 1491, British Columbia Bill 47 and Massachusetts's MBTA Communities law come nearest. 58 city upzonings were inventoried.
2. **Comparison cases, against a plan written beforehand** ([CASE_ANALYSIS_PLAN.md](tod/CASE_ANALYSIS_PLAN.md)).
   - Method: difference-in-differences of homes permitted per eligible acre per year, comparing lots whose allowed density rose with lots whose zoning did not change.
   - Results, in extra homes per acre per year for each 1.0 of added floor area ratio:
     - Park Slope 2.93;
     - Downtown Brooklyn 2.20;
     - the New York pooled set 0.67;
     - Chicago, held out, 0.24.
   - Charlotte and Philadelphia are small or have no floor-area measure.
3. **A held-out Wisconsin test** ([MADISON_TEST_PREREG.md](tod/MADISON_TEST_PREREG.md)). The per-acre method predicted, in advance, that Madison's 2023 overlay would add 0.25 homes per acre per year. The measured effect was 0.08 (90% interval −0.17 to +0.31): it passed, but only weakly.
4. **A scale check.** Spread over all land near Wisconsin stops, per-acre rates gave 14,212 to 151,973 extra homes. That would take Madison's apartment permitting beyond its own record. A block-level gain partly moves building from neighbouring blocks.
5. **Sizing.** The adopted method (AQ-050) takes the statewide total from whole-city net effects (section 2). The per-acre response is used only to place homes across station areas, in proportion to eligible acres times added floor area.
6. **Aggregation.** Station areas add up to municipalities, counties, Assembly and Senate districts, and the state.

#### 5. Limitations and known edge cases

- **No Wisconsin test of the adopted sizing.** The Madison test checked the per-acre method, which now only places homes.
- **The typical scenario rests on a general study.** Only 28 of Stacy et al.'s 96 loosening reforms changed floor area, density or height. It is measured 3 or more years after reform, but is placed here inside five years. A 2025–2026 review by the AEI Housing Center found most of the study's 180 reforms were minor, misplaced or misclassified, which would pull its 0.8% toward zero; the authors reply that it measures the modest reforms cities actually passed ([research/STACY_AEI_REVIEW.md](tod/research/STACY_AEI_REVIEW.md), AQ-059).
- **Why places differ.** A pre-registered effect-heterogeneity analysis tested 12 local traits (such as home values, incomes, rents, lot sizes, existing density and distance to downtown) on rezonings and station areas in six cities, using leave-one-city-out cross-validation. Eight methods were tried: weighted regression, LASSO, a regression tree, a random forest, gradient boosting, a causal forest, nearest neighbours and a multilevel model. All 66 pairs of traits were also tested. None predicted where upzoning added more homes better than a plain average, so the scenarios stay wide ([TRAITS_RESULTS.md](tod/TRAITS_RESULTS.md)). A second test entered 91 census variables (housing, incomes, commuting, car ownership and more) for 8 cities; again nothing beat the plain average ([ALLVARS_RESULTS.md](tod/ALLVARS_RESULTS.md)).
- **Checks against our own cities.** In 8 US cities that upzoned land near transit, the extra homes permitted over five years, net of building moved within the city, came to 0.04% (Los Angeles) to 1.24% (Madison) of the city's homes. Saint Paul, with one year of data before its reform, was −0.12%. In no city did building fall next to the upzoned area ([NET_EFFECT_RESULTS.md](tod/NET_EFFECT_RESULTS.md)). A comparison of six of these cities with 10 matched US cities that made no such reform agreed in 5 of 6. But it can only detect changes of about 4% to 5% of a city's homes over five years, so it cannot narrow the range ([CONTROL_CITIES_RESULTS.md](tod/CONTROL_CITIES_RESULTS.md)).
- **TOD alone versus TOD with parking reform.** The cases cannot separate the two.
- **Concentration.** Almost all extra homes land in Milwaukee County and Dane County.
- **Edge cases:**
  - Places with few homes but eligible vacant or commercial land, such as River Hills, get additions.
  - Wauwatosa's Census permit counts are low, which may be an under-count like Milwaukee's.
- **Data gaps:**
  - Green Bay has no current schedule, so none of its routes counts as frequent.
  - Superior and Metra's Kenosha station are missing.
  - Milwaukee's schedule is from 2025.
- **Not modelled:** rents, displacement, transit ridership and completions.

#### 6. Sensitivity notes (extra homes 2027–2031, typical unless stated)

- **The law's addition:**
  - Stacy et al.'s 95% interval: 665 to 4,352.
  - Without the coverage adjustment: little 105, strong 12,895.
  - Final year smoothed: same totals, with 562 homes in 2031 instead of 166.
  - Per-acre sizing: 14,212, 39,767 and 151,973. These fail the scale check.
  - Per-acre sizing at the Madison and Chicago rate (0.23): 13,477. Capped at the 95th percentile of comparable metro-years (9.06 apartment permits per 1,000 homes), it falls to 6,834.
- **Where homes land:**
  - Rail and rapid stops only: 716.
  - 20-minute service: 2,813.
  - All 15-minute stops within ½ mile: 3,226.
  - Placement without suburbs: Milwaukee metro 1,272 and Madison metro 1,237 (main: 1,637 and 827).
- **Baseline only:** 8,386 to 21,874, or 11,875 with Milwaukee's apartments as the Census published them. The addition is unchanged.

#### 7. Intended users and appropriate use cases

- **Intended users:** Wisconsin legislators and staff, and local officials in Milwaukee, Madison and other cities with frequent transit.
- **Good uses:**
  - comparing the likely size of a TOD law with current law;
  - seeing where the extra homes would go;
  - understanding why the evidence disagrees (a hundredfold spread between scenarios);
  - comparing TOD with ADU and parking reform.
- **Not appropriate for:**
  - parcel-level forecasts;
  - predicting a specific project;
  - setting housing targets;
  - forecasting effects after 2031;
  - judging rents or displacement.

Read the scenarios as different bodies of evidence, not as a statistical confidence interval.
