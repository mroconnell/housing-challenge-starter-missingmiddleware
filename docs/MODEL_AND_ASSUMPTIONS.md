# Model & Assumptions Overview

Missing Middleware: what three Wisconsin housing reforms would add to housing production over 2027–2031, how sure we are, and where the homes would go.

Assembled 2026-10-27 from the three reform sessions' adopted work. Part A (ADUs) is written for this document. Part B (parking) and Part C (transit-oriented density) are copied word for word from each reform session's own master copy, with only the heading levels changed, so they can be updated by the people who maintain them. Decision IDs in parentheses (for example AQ-043) point to the [assumptions log](ASSUMPTIONS_AND_QUESTIONS.md). Full source, licence and access details for every dataset are in [DATA_PROVENANCE.md](DATA_PROVENANCE.md) and are not repeated here. The plain-language ranking of the three reforms is in the [Policy Scenario Comparison](POLICY_SCENARIO_COMPARISON.md).

## About the tool as a whole

### The question

If Wisconsin passed one of the challenge's benchmark housing reforms, taking effect on a stylized date of 1 January 2027, how many more homes would be permitted over the five years 2027–2031 than under current law? How sure can we be, and where in the state would the extra homes be?

The tool is built for Wisconsin legislators, their staff and local officials. It covers the whole state and every one of its municipalities, and it reports results by county and by Assembly and Senate district.

### The three benchmark reforms

The challenge asks for a baseline and at least three of five benchmark reforms. The tool models four. Reforms are listed in the owner's order (2026-11-10):

| Reform | What the modelled state law does | Part |
| --- | --- | --- |
| **Accessory dwelling units (ADUs)** | Allows one ADU on every lot with a single-family home, detached or attached, of at least 600 square feet, with no extra parking required. | A |
| **Middle housing** | Allows 2–6 homes on every parcel now limited to one house, up to 3 stories, statewide. | Its locked plan ([WISCONSIN_PLAN_LOCKED.md](middle/WISCONSIN_PLAN_LOCKED.md)) |
| **Transit-oriented density (TOD)** | Every city with qualifying rail or rapid-bus stops zones a by-right multifamily district (at least 15 homes per acre) on 15% of the lot acres within ¼ mile of those stops (option D, AQ-071). | C |
| **Parking requirement reduction** | Removes every minimum off-street parking requirement for housing, statewide. | B |

Development fee reduction is not modelled. The parts below keep their original letters (A ADUs, B parking, C TOD).

### What each reform counts

All three reforms count **housing units in issued building permits**, at the date the permit is issued, compared with current law over the same five years. A permit is not a finished home. The three reforms differ in which permits they count, so their numbers must be compared with care:

| Reform | Outcome counted | Current-law baseline, 2027–2031 | Rate denominator used inside the reform |
| --- | --- | --- | --- |
| ADUs | **Second homes on single-family lots**: ADUs plus single-family-to-duplex conversions on a lot that already has a home (AQ-032, AQ-039) | 786 permits statewide (today's rates, rising 7.3% a year; AQ-065) | Per 1,000 single-family (one-unit detached) homes: 1,839,569 homes (ACS 2020–2024, table B25024) |
| Middle housing | **Extra homes in 2–4 unit buildings** (the range); other building sizes as side lines | 124,000 permits statewide (the shared all-housing baseline) | Per 1,000 single-family homes (1,839,569) |
| TOD | **All new housing units near major transit stops** | 14,654 permits in the station areas | Share of the 313,564 homes (2020 census) in the station areas |
| Parking | **All new housing units**, every building size | 124,000 permits statewide, range 56,500 to 218,865 (aims at 90%; shared all-housing baseline v4). It held 12 of 12 Wisconsin checks and 88.3% of other-state checks for 2009–2020, a window chosen after the results. It missed the 2005–08 run-up to the crash, like every method tested. Only the statewide total was tested. | Per 1,000 existing homes of all types (ACS 2020–2024, table B25002) |

The parking and TOD baselines come from one shared all-housing baseline built from the Census Building Permits Survey ([HOUSING_BASELINE.md](shared/HOUSING_BASELINE.md)). The ADU baseline comes from local permit records and coded local rules, because the Census survey does not say whether a new home was added to a lot that already had one. The [Policy Scenario Comparison](POLICY_SCENARIO_COMPARISON.md) puts all three on a common footing: additional permits over 2027–2031, as a share of the 124,000-permit all-housing baseline and per 1,000 existing Wisconsin homes.

### The five-year horizon

The forecast years are 2027, 2028, 2029, 2030 and 2031. Totals are summed over those five years unless a year is named. 2026 is shown in some tables as a bridge year but is not in any total. Each reform models a law in force from 1 January 2027. No reform models effects after 2031.

### What is common across the reforms

- **Every reform shows a 90% range, not a central line** (uniform display, owner 2026-11-05; [UNIFORM_DISPLAY_SPEC.md](UNIFORM_DISPLAY_SPEC.md)).
  - ADUs: 8,055 to 13,666 extra ADU permits over 2027–2031. It comes from the model's held-out prediction error on 7 statewide-law states, and covers law-side error only.
  - Middle housing: −482 to 4,515 extra homes in 2–4 unit buildings. It comes from the four-state result placed against 10,000 sets of fake law states.
  - TOD: 3,922 to 16,335 extra homes near stops. It comes from a bootstrap of 11 district places, widened ×1.1827 after a coverage test.
  - Parking: −46,268 to +19,649 extra homes. It comes from the measured average of 74 repeal places plus the placebo spread; it spans both a loss and a gain.
  - No single number stands for a reform's result. Labelled side lines give context: the former lower, central and upper scenarios, and the median of real cases. For ADUs these are typical adoption (the former central) 10,492; the 8-state median path 10,038; like Rhode Island and Oregon 6,321; high end, near California 19,784. TOD's are listed in Part C.
- **Parking's side lines** are the former lines, named by what they mean: the measured average of 74 repeal places −15,380; the median repeal place −1,557 (−311 a year; no floor at zero, AQ-074); Oregon's state mandate about +16,848.
- **Sensitivities are grouped by what they move.** Each sensitivity case changes one assumption and is labelled by whether it moves the statewide addition, only where the homes land, or only the current-law baseline.
- **Observed, calculated or assumed.** Each reform has a trace that says which numbers come from Wisconsin's own records, which are calculated from them, and which are assumed or transferred from elsewhere.
- **Everything reconciles.** Every reform's results are computed for each of Wisconsin's 1,925 municipality pieces and add up exactly to the 72 counties, the 99 Assembly districts, the 33 Senate districts and the state. Any part that cannot be placed is shown as an explicit "not allocated" row, never dropped.
- **Rebuildable.** Every number in this document is read from a committed table in `reference/`, written by a script in `scripts/` and checked by the automated tests.

### What the tool never claims

It does not forecast rents, prices, displacement, parking supply, traffic or transit ridership. It does not forecast any single lot or project. Its municipal and district figures are shares of a statewide estimate, not local forecasts. Every reform's response is transferred from places outside Wisconsin, because Wisconsin has not yet passed any of these laws.

---

## Part A. Accessory dwelling units (ADUs)

Written for this document from the final ADU packets: [Gate 3](gate3/README.md) (including its revision of 2026-10-26), [Gate 4](gate4/README.md), [Gate 5](gate5/README.md) and [Gate 5 model checks](gate5/MODEL_CHECKS.md). Adopted decisions: AQ-024 to AQ-043, AQ-058, AQ-061 (the ask-why fixes of 2026-10-28), AQ-064 (the audit fixes of 2026-10-29), AQ-065 (one law-year rule and a no-reform trend, 2026-10-31), AQ-066 (Madison on the statewide model, 2026-11-01) and AQ-067 (Massachusetts 2025 counted as a full year, 2026-11-01). Engine outputs: [`reference/adu_model_statewide.csv`](../reference/adu_model_statewide.csv), [`adu_model_sensitivities.csv`](../reference/adu_model_sensitivities.csv) and [`adu_model_reference_lines.csv`](../reference/adu_model_reference_lines.csv).

### Purpose and Scope

**The question.** If Wisconsin passed the benchmark ADU law, in force from 1 January 2027, how many more second homes would be permitted on single-family lots over 2027–2031 than under current law?

**The answer.**
- Under current law, the model expects Wisconsin to permit **786 second homes on single-family lots over 2027–2031** (785.9 permits). That is about 157 permits a year. Divided by Wisconsin's 1,839.569 thousand single-family homes, it is 0.085 permits per 1,000 single-family homes per year.
- By year: 135, 145, 157, 168 and 181 permits in 2027–2031. The baseline rises because every place's current rate grows 7.3% a year from mid-2023. That is the trend of ADU permits in places with no statewide law, measured outside the years of their own local reforms (AQ-065; [`adu_no_reform_trend.csv`](../reference/adu_no_reform_trend.csv)). Today's rates held flat would give 530 permits (0.058 per 1,000 single-family homes per year).
- **The law adds 8,055 to 13,666 second homes over 2027–2031 (90% range)** (uniform display, owner 2026-11-05).
  - The range is the model's held-out prediction error: the 7 non-California statewide-law states were each hidden in turn. The root mean square log miss was 0.136; × t at 6 degrees of freedom (1.943) gives the range. All 7 hidden states fell inside ranges built from the other 6.
  - It covers law-side error only. It leaves out Wisconsin-side inputs: today's rates where they are assumed (74% of the addition is in such places; the codings tested move the result from 9,319 to 10,734), and how the with-law level is spread across places ([CAUSAL_FRAMEWORK_RESULTS.md](adu/CAUSAL_FRAMEWORK_RESULTS.md)).
- Side lines, for context (the former scenarios; none is the result):

| Side line | What it means | Additional permits, 2027–2031 | Total with the 786-permit baseline |
| --- | --- | ---: | ---: |
| Like Rhode Island and Oregon (the former lower) | Like the average of the two slowest statewide-law states, Rhode Island and Oregon | **6,321** | 7,107 |
| Typical adoption (the former central) | Like a typical statewide-law state | **10,492** | 11,278 |
| High end, near California (the former upper) | The high end of what statewide-law states have reached; only California has gone higher | **19,784** | 20,570 |
| Median path of the 8 statewide-law states | The median path the 8 statewide-law states actually took, California included | **10,038** | 10,824 |

- The central's additions by year are 1,602, 1,972, 2,318, 2,306 and 2,294 permits in 2027–2031. The central adds 10,492.0 permits ÷ 1,839.569 thousand single-family homes ÷ 5 years = 1.14 permits per 1,000 single-family homes per year.
- **Revised 2026-10-28 (AQ-061, the ask-why fixes).** Before: baseline 605; lower 5,538, central 8,757, upper 16,889; reference line 8,851 permits. The changes: comparison-state counts are scaled up for towns that did not report; Massachusetts' 2025 count is divided by 11/12 of a year (reversed by AQ-067: now a full year); Washington's law years start when its cities had to comply; seven more measured Wisconsin cities and villages join the current-law group rates; and the value gap of a few small, very high-value villages is capped at California's largest.
- **Revised 2026-10-29 (AQ-064, fixes from the independent audit).** Before: lower 6,734, central 10,788, upper 20,057; reference line 10,558 permits. After: lower 6,804, central 10,679, upper 19,535; reference line 10,374. The baseline stays 530. The changes:
  - Rhode Island's reporting share is now its share of single-family homes in the towns that reported: 0.8704 in 2023–2024 and 0.8099 in 2025, instead of 32 of 39 towns. Rhode Island 2021–2022 stay at 1.0, because there is no town list for those years, so they are likely under-corrected.
  - Massachusetts 2025 now comes from the state's official ADU tracker file: 1,230 permits in the 294 towns that answered (was 1,224). It is divided by those towns' share of single-family homes, 0.8090: 0.7208 for the 225 towns that answered for the full year, plus half of 0.1764 for the 69 that answered mid-year only. Before, the share was 293 of 351 towns (0.8348).
  - Maine keeps its published share (0.73, a share of people), because its file has no permit counts. A sensitivity case uses an estimated homes share (0.62).
  - Each comparison-state rate now divides by single-family homes in that year. Homes are ACS 2020–2024 homes moved back or forward by one-unit building permits. Before, every year was divided by 2020–2024 homes. A new sensitivity case shows the old way.
  - A note on mixed geographies was added to [PREDICTIVE_RESULTS.md](adu/PREDICTIVE_RESULTS.md) (audit item 7). It does not change any number.
- **Revised 2026-10-31 (AQ-065, one law-year rule and a no-reform trend).** Before: baseline 530; lower 6,804, central 10,679, upper 19,535; reference line 10,374 permits. After: baseline 786; lower 6,223, central 10,349, upper 19,294; reference line 10,142. Held-out average log error 0.168 → 0.130. The changes:
  - One rule for law years: a law year starts only where the state law changed that place's rules. Vermont counts homes by year built, so each Vermont count moves one year earlier, to its permit year. Oregon's law years count from 2020; 2019 is a transition year. Seattle's 2024 counts as local rules only.
  - The current-law baseline rises 7.3% a year from mid-2023, the trend of places with no statewide law ([NO_REFORM_R1_RESULTS.md](adu/NO_REFORM_R1_RESULTS.md)). The "rises like no-law places (×1.11 a year)" sensitivity case now replaces this trend instead of adding to it.
  - The reference line needs at least 4 states in a year, the rule used for all three reforms (AQ-054). It was 2. Years 4 and 5 now repeat year 3.
- **Revised 2026-11-01 (AQ-066, Madison on the statewide model).** Before: lower 6,223, central 10,349, upper 19,294 additional permits. After: lower 6,321, central 10,615, upper 19,925. The baseline stays 786 permits and the reference line 10,142. The held-out average log error stays 0.130. The change:
  - Madison follows the statewide model like every other place. Its central addition rises from 111 to 377 permits over 2027–2031 (lower 209, upper 742).
  - Why: Madison's rules are not at the benchmark. Parking rules and excluded neighbourhoods remain.
  - California's 91 already-permissive cities rose several-fold after the state law: 0.40 permits per 1,000 single-family homes per year in 2016, 5.33 in 2022 and 5.84 in 2025. Without Los Angeles the rise is about 3-fold.
  - Madison's former path, from 9 similar cities in Washington and Oregon, is now a sensitivity case.
- **Revised 2026-11-01 (AQ-067, Massachusetts 2025 counted as a full year).** Before: lower 6,321, central 10,615, upper 19,925; reference line 10,142 permits. After: lower 6,321, central 10,492, upper 19,784; reference line 10,038. The baseline stays 786 permits. Held-out average log error 0.130 → 0.136. The change:
  - Massachusetts' 2025 count is divided by a full year, not 11/12 of a year. Its survey covers January too, so 11/12 overstated its rate by about 9%.
  - The lower factor moves from 0.6228 to 0.6296 and the upper factor from 1.818 to 1.825. The ramps change slightly.
  - Madison's central addition moves from 377 to 372 permits.
  - Washington's partial law year was tested in the same round and not changed ([IMPROVE_R4_RESULTS.md](adu/IMPROVE_R4_RESULTS.md)).

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
| Current-law rate in places with their own permit data | Milwaukee 0.0863 (35 candidate permits ÷ 405.608 thousand home-years, 2022–2025, rising only with the no-reform trend); Madison 0.188 (40 permits ÷ 213.168 thousand home-years, 2022–2025); Pleasant Prairie 0.039 (3 permits ÷ 76.0 thousand home-years, 2014–2025). All in permits per 1,000 single-family homes per year, before the 7.3% a year no-reform trend (AQ-065). | Measured in the place's own records. Milwaukee's open permit data have no unit counts, so its 35 permits are unverified candidates (quality C). Its file through 2026-06-15 shows no clear rise after its August 2025 reform. | AQ-043; [WI_BASELINE.md](gate3/WI_BASELINE.md) |
| Current-law rate by coded rules group | Prohibited 0.023 (5 permits ÷ 214.274 thousand home-years), restricted 0.051 (36 permits ÷ 699.350 thousand home-years), already at the benchmark 0.188 (40 ÷ 213.168) permits per 1,000 single-family homes per year | Measured in Wisconsin places with each kind of rule. Prohibited: Pleasant Prairie, Sun Prairie, Howard, Neenah, and De Pere and Waunakee for their prohibited months. Restricted: Madison 2014–2023, Fitchburg, Green Bay, Verona, Watertown, and De Pere and Waunakee for their restricted months. Benchmark: Madison 2022–2025. These seven places joined on 2026-10-28 (AQ-061); Kaukauna and Milwaukee are left out. Rules are coded for the 37 largest municipalities. | AQ-026, AQ-027, AQ-037, AQ-061 |
| No-reform trend | Every place's current-law rate × 1.0732 a year from mid-2023: × 1.28 in 2027 up to × 1.70 in 2031 | Places with no statewide law kept issuing more ADU permits. Same pace alone predicted about 30% too low in past forecasts. The trend is measured outside the years of each place's own local reform. | AQ-065; [`adu_no_reform_trend.csv`](../reference/adu_no_reform_trend.csv) |
| Places whose rules are not coded | Treated like places that restrict ADUs (0.051) | 1,267,433 of the 1,839,569 single-family homes (69%) are in such places. The middle choice; prohibited and already-allowed are both sensitivity cases. | AQ-023, AQ-027 |
| Rate with the law | From a pooled model of 8 statewide-law states and 5 cities. Once a statewide law is in force, one common level across states fits best. Two fits are used. A fit on home value, household income and number of homes sets Wisconsin's **statewide** rate. A fit on home value alone (slope about 1.03) **spreads that total across places**. Income and size do not move one Wisconsin place against another. | The with-law rate must come from measured data, not judgment (AQ-036). No Midwest state yet has data after a statewide law. | AQ-034, AQ-036, AQ-042, AQ-061, AQ-064; [POOLED_REVISION.md](gate3/POOLED_REVISION.md) |
| Places beyond California's value range | Each place's value gap is capped at the largest gap seen among California places (+1.01 in log terms, about 2.7 times its state's typical value) before allocation | 8 areas (7 villages and towns, 2,852 homes) sit further above Wisconsin's typical value than any California place sits above California's. Their uncapped levels were extrapolations. The cap moves about 16 central permits to other places; the statewide total does not change. Flagged places: [`adu_model_value_capped_places.csv`](../reference/adu_model_value_capped_places.csv). | AQ-061 |
| California in the common level | Yes (configuration A) | Predicts the 7 other statewide-law states better when each is held out: average log error 0.136 with California, 0.150 without (after AQ-067; 0.130 and 0.145 after AQ-065; 0.168 and 0.182 after AQ-064; 0.180 and 0.198 after AQ-061; 0.113 and 0.132 before AQ-061) | AQ-040, AQ-042, AQ-061, AQ-064, AQ-065, AQ-067 |
| Comparison counts cover all of each state | Counts divided by the reporting share: Maine 2025 ÷ 0.73 (share of people in 182 reporting towns), Massachusetts 2025 ÷ 0.8090 (share of Massachusetts' single-family homes in the 294 towns that answered the official tracker, mid-year-only towns at half weight), Rhode Island ÷ 0.8704 in 2023–2024 and 0.8099 in 2025 (share of Rhode Island's single-family homes in the 33 and then 32 of 39 towns that reported), Utah ÷ 0.795, 0.803 and 0.804 (2023–2025; share of Utah's single-family homes in the cities and counties that answered). Rhode Island 2021–2022 stay at 1.0 (no town list). Massachusetts 2025 counts as a full year (AQ-067): the law took effect on 2 February, but its survey covers January too. | Each count covers only reporting towns, but the rate divides it by every single-family home in the state. Maine's file has no permit counts, so its published share of people is used. Reporting towns are mostly larger, so Maine's homes share is likely lower (about 0.62; a sensitivity case). The uncorrected case gives a central of 9,084. | AQ-061, AQ-064, AQ-067; [`pooled_revision_coverage.csv`](../reference/pooled_revision_coverage.csv) |
| Comparison-state homes by year | Each comparison rate divides permits by single-family homes in that year: ACS 2020–2024 homes moved back or forward by one-unit building permits | Before AQ-064 every year used 2020–2024 homes, so early years read a little low and 2025–2026 a little high. Reading every year against 2020–2024 homes gives a central of 10,781 (a sensitivity case). | AQ-064 |
| Law years: one rule | A law year starts only where the state law changed that place's rules. Vermont counts move one year earlier, from year built to permit year. Oregon's law years count from 2020 (2019 is a transition year). Seattle's 2024 counts as local rules only. | Most ADUs are finished the calendar year after their permit (63% of Austin's). Oregon's HB 2001 barred owner-on-site and parking rules from 2020. Seattle met HB 1337 before 2024. Coded as before, the central is 10,593. | AQ-065 |
| Washington's law years | Counted from local compliance: estimate year 2026 (April 2025–March 2026) is year 1; 2024–2025 are left out | HB 1337 was enacted in July 2023, but cities had to adopt compliant rules only from 30 June 2025 (four largest counties) or later | AQ-061 |
| Comparison counts cleaned to the same outcome | California: at most 2 ADUs per parcel, and ADUs on multifamily parcels removed (87,303 → 81,368 units in 2023–2025). Other series × 0.951 for vacant-lot ADUs. Minneapolis × 0.873 for duplex-lot ADUs. | The benchmark law covers single-family lots with existing homes only. 0.951 = 1 − 0.049, where 4.9% is the median vacant-lot share of ADUs in 17 cities with demolition records. | AQ-039, AQ-041 |
| Ramp-up | The law's addition reaches 0.685 and 0.847 of its full size in 2027 and 2028, and its full size from 2029 (central) | Measured in the pooled model's year-since-law terms | [Gate 3 packet](gate3/README.md), step 4 |
| Madison | Follows the statewide model like every other place (AQ-066, 2026-11-01). Its central level is 1.822 permits per 1,000 single-family homes per year. | Madison's rules are not at the benchmark: parking rules and excluded neighbourhoods remain. California's 91 already-permissive cities rose from 0.40 permits per 1,000 single-family homes per year in 2016 to 5.33 in 2022 and 5.84 in 2025 (about 3-fold without Los Angeles). The former path of 9 similar cities in Washington and Oregon (0.452, 0.542, 0.601, 0.799 and 1.076 in 2027–2031) is a sensitivity case. | AQ-040, AQ-042, AQ-066; [MADISON_LIKE_CITIES.md](gate3/MADISON_LIKE_CITIES.md) |
| Madison floor | No place's with-law rate is below 0.2345 permits per 1,000 single-family homes per year | Madison's 2022–2025 rate (40 permits ÷ 213.168 thousand home-years = 0.1876) divided by 0.8, because Madison's rules are about 80% of the benchmark | AQ-029, AQ-030, AQ-042 |
| No negative additions | The addition is never below zero | A law that adds a right does not remove permits | Engine rule |
| Lower scenario | Every place's central level × 0.6296 | The mean of Rhode Island's 0.7545 and Oregon's 0.6450 permits per 1,000 single-family homes per year (at a typical place, law in force 4+ years) is 0.6997, which is 0.6296 of the central's common level of 1.1114 | AQ-043, AQ-061, AQ-064, AQ-065, AQ-067 |
| Upper scenario | Every place's central level × 1.825 | The 90th percentile of how much the 8 states' levels differ from one another. At a typical place it is 2.03 permits per 1,000 single-family homes per year (1.1114 × 1.825); only California (2.30) is higher. | AQ-040, AQ-042, AQ-061, AQ-064, AQ-065, AQ-067 |
| Reference line | The median observed statewide rate of all 8 statewide-law states, by year since their law: 0.9511, 1.0888 and 1.2814 permits per 1,000 single-family homes per year in years 1–3 (from 7, 4 and 4 states); 2030 and 2031 repeat the 2029 value | Shows what real states did, with no model in between. A year needs at least 4 states; only Utah and California have a fourth year. Uses the same reporting shares, year-matched homes and law-year coding as the model (AQ-061, AQ-064, AQ-065, AQ-067). | AQ-043, AQ-061, AQ-064, AQ-065, AQ-067 |

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

**In one sentence.** For each of Wisconsin's 1,925 municipality pieces, the law adds that place's single-family homes times the gap between its rate with the law and its current-law rate, phased in over the first two years.

**The equations.** For area *a* and year *t* in 2027–2031:

```
baseline[a, t] = H[a] × x[a] × g[t] / 1000
addition[a, t] = max(0, H[a] × (y[a] − x[a] × g[t]) × ramp[t] / 1000)
g[t]           = 1.0732 ^ (t − 2023.5)
y[a]           = max(level from the pooled model for a, 0.2345)
```

where *H* is the number of one-unit detached homes, *x* the current-law rate and *y* the with-law rate, both in permits per 1,000 single-family homes per year. *g* is the no-reform trend (AQ-065): 1.28, 1.37, 1.47, 1.58 and 1.70 in 2027–2031. For the few places that loosened their rules recently, *g* also holds their short rise to their new group's rate. Since AQ-066 Madison uses the same equations as every other place.

**Step by step.**
1. **Current-law rate (x).** Measured where a place has its own permit records (Milwaukee, Madison, Pleasant Prairie). Otherwise taken from the place's coded rules group, or, where rules are not coded, from the "restricted" group. The group rates pool every measured Wisconsin city whose rules in its measurement window are coded (AQ-061). Each rate then rises 7.3% a year from mid-2023 (AQ-065).
2. **Rate with the law (y).** A pooled model is fitted to California's 457 jurisdictions, the seven other statewide-law states (each labelled by the area actually measured: Washington outside Seattle, Oregon in 32 cities outside Portland, Vermont's Chittenden County, Utah's reporting cities, and Maine, Massachusetts and Rhode Island statewide) and five cities (Seattle, Portland, Austin, Denver, Minneapolis). Counts are divided by each state's reporting share, and Washington's law years start at local compliance (AQ-061). Vermont is counted by permit year, Oregon's law years start in 2020, and Seattle's 2024 counts as local rules (AQ-065). Each year's count is divided by that year's single-family homes (AQ-064). Across states, one common level fits best once the law is in force. Two fits then do two jobs:
   - **The statewide rate** comes from the fit on home value, household income and number of homes. Within a state, a place whose median home value is 10% above its state's average has about a 29% higher rate; at the same value, 10% higher household income goes with about a 25% lower rate; size barely matters. Applied to Wisconsin's 1,925 areas, this fit gives the statewide rate for each year.
   - **Each place's share** comes from the fit on home value alone (slope 1.03 on the log scale, `W_ALLOC` in `scripts/run_pooled_revision.py`). A place whose median home value is 10% above Wisconsin's average gets about a 10% higher level. The levels are then scaled so they add up to the statewide rate. Income and size do not enter this step. Each place's value gap is capped at California's largest (+1.01 in log terms) first.
3. **Ramp.** The addition is phased in at 0.685 and 0.847 of its full size in 2027 and 2028, and is at full size from 2029 (central).
4. **Scenarios.** The lower multiplies each place's central level by 0.6296 and the upper by 1.825. Each has its own ramp, recomputed the same way.
5. **Sum and reconcile.** Areas are summed to counties and the state. Districts are shares of each municipality's result by where its single-family homes were in 2020 census blocks, with an explicit "not allocated" row (0.0 permits).

**Worked example 1, Madison (central).** Madison has 53,292 single-family homes. Its current-law rate is 0.1877 permits per 1,000 per year. The trend factors sum to 7.411 over the five years (1.28 + 1.37 + 1.47 + 1.58 + 1.70). So its baseline is 53.292 thousand homes × 0.1877 × 7.411 = 74.1 permits. Since AQ-066 its central level comes from the statewide model: 1.822 permits per 1,000 per year (since AQ-067). Each year's addition is 53.292 × (1.822 − 0.1877 × that year's trend factor) × that year's ramp. By year that is 57.7, 70.6, 82.3, 81.3 and 80.1 permits. Summed over 2027–2031 it is 372.1 permits (lower 208.5, upper 736.7). On its former path it was 110.8 permits.

**Worked example 2, Christiana town, Vernon County (central).** It has 389 single-family homes and a current-law rate of 0.0515 permits per 1,000 per year. Its central level is 1.753. The central ramp is 0.6850, 0.8469, 1, 1 and 1. Each year's addition is 0.389 thousand homes × (1.773 − 0.0515 × that year's trend factor) × that year's ramp. Summed over 2027–2031 it is 2.95 permits. Its baseline is 0.389 × 0.0515 × 7.411 = 0.15 permits.

**Checks the model must pass to run.** The engine stops with an error if it fails to reproduce the pooled model's own totals to within 2 permits, or if a stored scenario factor or ramp does not follow from its source files. Lower ≤ central ≤ upper holds in every area and year. The 99 Assembly districts and the 33 Senate districts each add up to the statewide 786 baseline and 10,492 central additional permits.

**What rests on what (trace).** Of the 10,492 central additional permits:
- 764 (7.3%) are in the 3 places whose current-law rate is observed in their own permits;
- 2,165 (20.6%) are in the 37 places whose rate is calculated from a coded rules group;
- 7,563 (72.1%) are in the 1,848 places whose rules are not coded, so their current-law rate is assumed.

The no-reform trend (7.3% a year) is assumed everywhere. It is transferred from places outside Wisconsin.

Every place's rate with the law is transferred from other states.

### Limitations and Known Edge Cases

1. **No Midwest state has data after a statewide ADU law.** The model contains no Wisconsin data after a law. Wisconsin permits 0.06 per 1,000 single-family homes per year today, where the pooled model's no-law level for Wisconsin would be 0.50. States with before-and-after data (California, Rhode Island, Washington, Vermont) reached similar first-year levels however low they started, but they are coastal or New England markets. Iowa's first full year (2026) will be the first Midwest test.
2. **Mid-size cities may be slower.** Madison-like cities in Washington and Oregon ran at a median 0.45, 0.54 and 0.60 permits per 1,000 single-family homes per year in years 1–3, about half the model's earlier path. Since AQ-066 no Wisconsin place is put on that path; Madison follows the statewide model. On that path Madison would add 111 permits instead of 372, and the central would be 10,231 (a sensitivity case). If Wisconsin's mid-size markets behave like those cities, the central is too high in its first three years.
3. **The hold-out test rests on 7 states.** California stays in the common level because it predicts the others better. That win holds in 62% of 5,000 resamples and in all 7 checks that drop one state. After AQ-067 the average log error is 0.136 (0.130 after AQ-065; 0.168 after AQ-064; 0.180 after AQ-061; 0.113 before AQ-061). Utah and Rhode Island are predicted most closely (errors −0.07 and −0.09). Washington is over-predicted by about 21% (+0.19), Vermont by about 19% (+0.17) and Massachusetts by about 15% (+0.14).
4. **Most current-law rates are assumed.** 72.1% of the central addition (7,563 of 10,492 permits) is in places with uncoded rules. This mostly moves the split between baseline and addition, not the total with the law (see Sensitivity Notes).
5. **Milwaukee's count is unverified.** Its 35 candidate permits come from open data with no description or unit count.
6. **Small, very high-value villages are capped.** 8 areas (7 villages and towns, 2,852 single-family homes) have home values further above Wisconsin's average than any California place is above California's. Their value gap is capped at California's largest before allocation (AQ-061; the owner had chosen no cap at Gate 4). For example, Chenequa (271 single-family homes) gets 3.58 permits per 1,000 single-family homes per year in the central, instead of 7.17 uncapped. The cap moves about 16 of the 10,492 central permits to other places. The flagged places are listed in [`adu_model_value_capped_places.csv`](../reference/adu_model_value_capped_places.csv).
7. **Rural areas get a large share.** Rural areas get 4,486 of the 10,492 central permits (42.8%) with 710,070 of the 1,839,569 single-family homes (38.6%), partly because a rural home's value includes its land.
8. **Districts are shares, not forecasts.** District figures share each municipality's result by where its single-family homes were in 2020. Homes built since 2020 and annexations are not reflected. At Gate 5, plain land-area weights would have moved 237 of the 8,757 central permits (2.7%) between districts (not rerun).
9. **Permits are not homes.** Not every permit becomes a finished home, and some second homes are built without permits.
10. **Associations, not proven causes.** Results describe what other states experienced after their laws.
11. **The before-and-after evidence is thin.** In the placebo test ([PLACEBO_RESULTS.md](adu/PLACEBO_RESULTS.md)) the strong-law and weaker-law groups have only 2 series each (California and Washington; Rhode Island and Chittenden County, Vermont). Against placebo groups of the same size (2 no-law series per draw), the strong-law group's change of +0.75 ADU permits per 1,000 one-unit detached homes per year is matched or beaten in 16% of draws (316 of 2,000), and the weaker-law group's +0.45 in 26% (about 520 of 2,000).
12. **Reporting shares are rough.** Maine's share is of people, not of homes. Massachusetts' and Rhode Island's are of homes since AQ-064, but Rhode Island's 2021–2022 counts have no town list and are not scaled up. Reporting towns are mostly larger. Using an estimated homes share for Maine (0.62) raises the central to 10,724 (+232). Without any scale-up the central would be 9,084 (−1,408).
13. **Vermont's counts are by year built.** Every Vermont count is by the year a unit was built or first occupied. Since AQ-065 each count is moved one year earlier to stand for the permit year. Its 2024 count (57 ADUs) comes from the state's housing layer, not the regional planning commission's own series. Dropping 2024 lowers the central by 568 permits. Not adopted (AQ-062).
14. **The no-reform trend is transferred.** The 7.3% a year comes from 8 places outside Wisconsin. It scored better than same pace in past forecasts (0.28 against 0.51), but the two ranges overlap. Before AQ-066, without it the baseline would have been 530 and the central 10,591, 242 higher (not rerun since; [NO_REFORM_R1_RESULTS.md](adu/NO_REFORM_R1_RESULTS.md)).

### Sensitivity Notes

Each case changes one assumption and reruns the model. Additional permits over 2027–2031 unless noted. Source: [`reference/adu_model_sensitivities.csv`](../reference/adu_model_sensitivities.csv); tornado chart: [sensitivity_tornado.png](gate3/sensitivity_tornado.png).

**Cases that move the statewide addition** (adopted: lower 6,321, central 10,492, upper 19,784):

| Case | Lower | Central | Upper |
| --- | ---: | ---: | ---: |
| Multiplicative law: each place's current rate × one statewide factor | — | 791 | — |
| California-only market regression | — | 2,255 | — |
| Rural and small-community places at the Madison floor (0.2345) | — | 5,649 | — |
| Lower as a statistical 10th percentile (every central level ÷ 1.825) | 5,401 | 10,492 | 19,784 |
| Eligible-property basis (its own 636-permit baseline; Gate 3 run, not rerun) | — | 8,164 | 15,318 |
| Comparison-state counts and coding as at Gate 4 (all three AQ-061 changes undone; Massachusetts a full year) | 5,060 | 8,402 | 17,158 |
| No scale-up for towns that did not report | 5,562 | 9,084 | 18,076 |
| California out of the common level | 6,321 | 9,382 | 15,217 |
| Washington's law years from enactment, not local compliance | 5,648 | 9,621 | 18,546 |
| Los Angeles-calibrated multifamily correction | 6,069 | 9,901 | 17,639 |
| Vermont 2024 left out (not adopted, AQ-062) | 6,086 | 9,924 | 19,277 |
| Scale-up for Maine, Massachusetts and Rhode Island only (Utah not) | 6,304 | 10,157 | 19,253 |
| Madison on the path of similar cities in Washington and Oregon (before AQ-066) | 6,223 | 10,231 | 19,159 |
| Law years coded as before AQ-065 (Vermont by year built; Oregon and Seattle years not cut to the state law) | 6,684 | 10,593 | 19,766 |
| Maine's reporting share as a homes share (0.62, not 0.73; Maine's file has no permit counts to check it) | 6,320 | 10,724 | 20,544 |
| Vermont left out of the comparison states (not adopted, AQ-062). Reference line 8,767 permits (adopted 10,038) | 6,337 | 10,772 | 21,540 |
| Every comparison year read against 2020–2024 homes, not year-matched homes (as before AQ-064) | 6,432 | 10,781 | 20,464 |
| No ramp: full rate from 2027 | — | 11,585 | — |

**A case that moves only where permits land:** without the cap on the value gap, small very high-value villages keep their extrapolated levels. The statewide central does not move (10,492.0 → 10,491.9); about 16 permits move back to the 8 capped areas.

**Cases that move only the current-law baseline** (central). Because the rate with the law does not depend on today's rules, the addition moves the other way by about as much, and the total with the law barely moves. Every baseline below includes the 7.3% a year no-reform trend, except the last row, which replaces it:

| Case | Baseline | Change in addition | Change in total with the law |
| --- | ---: | ---: | ---: |
| Uncoded places behave like places that prohibit ADUs | 521.6 | +242.5 | −21.9 (−0.2%) |
| Uncoded places behave like places that already allow ADUs as the bill would | 2,065.0 | −1,173.2 | +105.9 (+0.9%) |
| Milwaukee rises to Madison's rate after its 2025 reform | 847.4 | −58.8 | +2.7 |
| Madison's rate = its 2026 pace so far (provisional) | 1,095.9 | −284.3 | +25.7 (+0.2%) |
| Madison's rate from 2024–2025 only | 804.4 | −17.0 | +1.5 |
| Madison's rate without one builder's templated programme | 773.0 | +11.9 | −1.1 |
| Wisconsin's baseline rises like no-law places (×1.11 a year, in place of the 7.3% trend) | 949.7 | −154.9 (lower −154.7, upper −155.1) | +8.9 (+0.1%) |

Percentages are of the adopted central total with the law, 11,277.9 permits.

- **Placebo test and the rising-baseline check (AQ-058).** Rates are ADU permits per 1,000 one-unit detached homes per year, after the law (3 years) minus before it (3 years). Strong-law places changed by +0.75, weaker-law places by +0.45 and no-law places by +0.25 (median of 2,000 placebo draws; ratio 1.52, from 0.53 to 0.75), so the order is strong > weak > none ([PLACEBO_RESULTS.md](adu/PLACEBO_RESULTS.md)). The no-law rise disappears (change −0.04) once windows holding a local reform are removed. The last row lets every Wisconsin place's rate rise like the no-law places, about ×1.11 a year, in place of the adopted 7.3% trend: baseline 949.7 instead of 785.9 permits over 2027–2031; addition 6,166.2 / 10,337.1 / 19,629.4 instead of 6,320.9 / 10,492.0 / 19,784.4 (lower / central / upper); central total with the law 11,286.8 instead of 11,277.9 (+8.9). It is an upper check, not the main case. The ×1.11 counts local reforms as part of the trend, and Wisconsin's main local reform (Madison 2021) is already in the measured baseline. The adopted 7.3% is measured outside the years of each place's own reform (AQ-065).

**Reading.** What we do not know about local rules moves the split between baseline and addition, not the total. What moves the total is how Wisconsin responds compared with the eight states, how the comparison states' counts are read, and the model form. The two alternative model forms (multiplicative law 791; California-only regression 2,255) are the largest downside cases. The AQ-061 comparison-state changes together add 2,090 central permits (8,402 → 10,492). Without the ramp, the central would be 1,093 permits higher. Redrawing the urban, suburban, small-community and rural groups moves nothing, because the groups are labels only.

**Robustness checks** (alternative methods scored on the 7 held-out non-California statewide-law states; average log error, lower is better): the adopted measure, ADU units per one-unit detached home, scores 0.136 after AQ-067 (0.130 after AQ-065; 0.168 after AQ-064; 0.180 after AQ-061; 0.113 before AQ-061). The alternatives were scored at Gate 3 and not rerun: permits instead of units 0.132; the eligible-property basis 0.168 without and 0.202 with attached homes.

#### Held-out test: predicting a state the model never saw

Each of the 7 non-California statewide-law states is left out in turn. The model is refitted on the rest and predicts the left-out state's ADU permits per 1,000 single-family homes per year over its law years. Log error = log(predicted ÷ observed); +0.10 is about 10% too high. Source: [`pooled_revision_loso.csv`](../reference/pooled_revision_loso.csv) (adopted model, AQ-065 coding, Massachusetts 2025 as a full year since AQ-067). Details: [IMPROVE_R1_RESULTS.md](adu/IMPROVE_R1_RESULTS.md), [IMPROVE_R2_RESULTS.md](adu/IMPROVE_R2_RESULTS.md).

| State | Years | Observed rate | Predicted rate | Log error |
| --- | --- | ---: | ---: | ---: |
| Washington | 2026 | 0.77 | 0.93 | +0.19 |
| Oregon | 2020–2022 | 0.90 | 1.01 | +0.12 |
| Rhode Island | 2025 | 1.13 | 1.03 | −0.09 |
| Massachusetts | 2025 | 0.92 | 1.07 | +0.14 |
| Maine | 2025 | 1.24 | 1.09 | −0.13 |
| Utah | 2023–2025 | 1.29 | 1.19 | −0.07 |
| Vermont | 2021–2023 | 0.98 | 1.17 | +0.17 |
| **Root mean square** | | | | **0.136** |

- **The Vermont and Oregon corrections are now adopted (AQ-065).** Vermont counts ADUs when built, not when permitted. Most ADUs are finished the calendar year after their permit (63% of Austin's; median 0.97 years). Each Vermont count now moves one year earlier, and its miss fell from +0.33 to +0.19 (+0.17 since AQ-067). Oregon's law years now count from 2020, when HB 2001 barred owner-on-site and parking rules, and its miss fell from +0.20 to +0.13 (+0.12 since AQ-067). Left out entirely, Vermont would give a central of 10,772.
- **Washington is now the largest miss** (+0.19, about 21% too high; it was +0.07).
- **Massachusetts is now missed by +0.14** (about 15% too high; it was +0.06). Its observed rate fell from 1.01 to 0.92 when its 2025 count was divided by a full year (AQ-067).
- California out of the common level scores 0.150 instead of 0.136.
- **Maine's reporting share is a share of people** (0.73), because its town list is not published. A homes share of about 0.62 is likely; it would raise the central to 10,724 and the upper to 20,544.

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
3. **Central case, "No measurable change" (0 added).** In the one to three years after repeal, the repeal places' permit rate changed by −1.15 permits per 1,000 existing homes per year compared with similar places (74 places). The 90% range (5th to 95th percentile of 2,000 resamples) is −3.63 to +1.45 permits per 1,000 existing homes per year. Held-out repeal places are predicted best by no effect (REFORM_MODELS_RESULTS.md), so the central case is 0. The measured average is the low end (below).
3a. **Low end, "Low end of the evidence" (owner, 2026-11-01).** No logical floor at zero. The low end is the measured average of the 74 repeal places against similar places, −1.15 permits per 1,000 existing homes per year (sample corrected 2026-11-05: Canandaigua's town series, Seabrook and Maumee removed; owner OK 23:16 UTC). Applied unfloored to the same 2,668,677 eligible homes, it gives −15,380 permits over 2027–2031 (12.4% below current law, of 124,000). This is the same comparison as the high end. It is pulled down mostly by Austin, Minneapolis and San Francisco; the median repeal place is −0.12. Other measured low figures agree:
   - metro neighbours −18,100;
   - traits-adjusted −16,400 to −19,100;
   - regressions without San Francisco −8,100 to −15,400.

   **Where the low end lands (audit, 2026-11-01):** in proportion to each eligible place's current-law permits, not its existing homes, because a reduction cuts what would have been built. It is about 13.1% of each eligible place's baseline, so no place goes below zero, and no floor is applied.
   The combined TOD + parking view carries it in its low pairing (rule (b) passes reductions through, TOD commit 097718a).
4. **Upper case, "High end of the evidence".** +1.47 permits per 1,000 existing homes per year (owner decision, 2026-10-27, option B; placebo fix approved 2026-10-28; 74-place sample from 2026-11-05). It comes from the control-city (placebo) test. 9,185 cities that never repealed were given the real places' repeal years, with at least 20 stand-ins for each real place, drawn from its state, then its Census division, then the nation, at ½–2× population. Their 20,000 set averages run from −2.31 to +2.63 (middle 90%), around a middle of +0.00. Centred on the real average of −1.15, that spread runs from −3.47 to +1.47. This agrees with resampling the 74 places (95th percentile +1.45, 19,328 permits). An earlier version gave big cities only 1 to 4 stand-ins, which gave a lumpy spread and a false lean toward growth; it gave +0.95 (12,695 permits). The first 24 places' +2.21 is kept as a sensitivity. The rate is applied to the 2,668,677 existing Wisconsin homes outside the 9 places that already have no minimums (10 municipality pieces, because Brodhead spans two counties) and the 9 that removed them with conditions (Stage 2, owner OK 2026-11-03). That gives 19,649 permits over 2027–2031, 15.8% above current law (19,649 of 124,000, baseline v4).
   **Shared reporting (AQ-054).** In additional homes permitted per year against the shared all-housing baseline, the central case adds 0 a year and the upper case about 3,930 a year. Home counts that compare reforms use ACS 2020–2024 total housing units: 2,778,572 statewide, of which 2,668,677 are outside the 18 places that already removed minimums (9 fully, 9 with conditions). The median of real cases, applied to Wisconsin, is shown as a reference line: the median repeal place changed by −0.12 permits per 1,000 existing homes per year. Applied to Wisconsin without a floor at zero (owner, 2026-11-03), that is −1,557 permits over 2027–2031 (−311 a year), slightly below the central case.
   **Control-city (placebo) check.** 9,420 cities that kept their minimums were given the real places' repeal years and run through the same calculation, 20,000 times. 21.7% of these placebo studies came out as low as the real places. The real result is ordinary, with no sign that a repeal raised or lowered permits. Their spread sets the upper case ([PLACEBO_RESULTS.md](parking/PLACEBO_RESULTS.md); review in [ASK_WHY_REVIEW.md](parking/ASK_WHY_REVIEW.md)).
   **Near-transit evidence (owner decision, 2026-10-28: reported, not used in the totals).**
   - **What was compared:** reform areas, Seattle's 2012 urban villages and Minneapolis's 2015 near-rail cut (36 areas, census blocks 2000–2020), against 1,040 rail station areas in cities with no parking reform. Each area was measured against the rest of its own city.
   - **Result:** with the same growth before and the same size, reform areas gained +18.8 extra homes per 1,000 existing homes per year (90% range +9.3 to +28.2).
   - **Why it is not used:** Seattle holds 78% of the reform-area homes and had light rail, upzoning and a jobs boom in the same years. Without adjusting for earlier growth, the gap is only +3.9. No model predicted held-out regions.
   - **Effect on the tool:** none. The scenario keeps its range, and this is reported as the strongest evidence that removing parking minimums near rail can add homes.
   - Details: [NEAR_TRANSIT_PLACEBO_RESULTS.md](parking/NEAR_TRANSIT_PLACEBO_RESULTS.md), [NEAR_TRANSIT_PREDICT_RESULTS.md](parking/NEAR_TRANSIT_PREDICT_RESULTS.md), [BLOCK_CATALOG_RESULTS.md](parking/BLOCK_CATALOG_RESULTS.md).
5. **Timing (measured flat).** Each scenario uses its own measured timing (owner, 2026-11-10). For parking the measured timing is flat. Year 1 after repeal can't be told apart from years 2–3: with method 2's mix weights, −0.42 against a −1.44 average over 36 places, and every year's range includes 0 (exploratory check, 2026-11-10). The by-year test found no build-up or fade over up to 9 years (Test 49). So the same yearly rate applies in every year 2027–2031. Holding it flat in years 4–5 is still an assumption.
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

- The sample is 74 places, and most repealed as part of a wider zoning rewrite. Parking's own effect cannot be fully separated out. Some places have only one or two years since repeal.
- No prediction tool (weighted regression, lasso, random or causal forest) and no city trait beat one average on places left out of the fit, so every Wisconsin place gets the same rate.
- The after period is three years. Larger projects may take longer to reach a permit.
- The places chose to repeal, so they may differ from places that did not.
- The Census permit data have reporting gaps. Milwaukee's apartments are estimated, and its 2025 figure is missing.
- The upper case is spread by homes, not by where minimums actually bind. Rural towns with few minimums get a share.
- The tool does not estimate rents, parking supply, traffic or street-parking spillover.
- **The high end may be understated (improvement round 1, 2026-10-31):** after data fixes, three versions of the high end (29,843, 38,230 and 49,712 permits over 2027–2031; [IMPROVE_R1_RESULTS.md](parking/IMPROVE_R1_RESULTS.md)) all exceed the headline (19,818 then; 19,649 on the 74-place sample). The headline is kept by a rule set before running, but it is the lowest of the four, and the high end is uncertain by about 2×. The central case, about zero, holds in every version. Round 2 (only apartment-scale reforms disqualify comparison places, V7: 29,307; plus California, Oregon and Washington state laws, V7s: 27,671; [IMPROVE_R2_RESULTS.md](parking/IMPROVE_R2_RESULTS.md)) also exceeds it. San Jose and Austin fell 1–3 short of 20 stand-ins, and the owner kept 19,818 (2026-10-31).
- **Timing of place traits (audit 2e, 2026-10-29):** population (used to match comparison places), existing homes (the rate's denominator), relative rent and the metro flag all come from ACS 2020–2024. That is after most repeals (2016–2024). If a repeal raised a place's growth, its 2020–2024 homes and population are a little higher, which lowers its measured rate slightly and can shift its comparison window. The trait tests that used rent and metro (none passed) share this caveat. Pre-repeal values would need ACS 5-year tables from before each repeal.
- Whether evidence from cities that repealed by choice may stand in for a statewide law is still open: office-hours question 26.
- **The current-law baseline may run low (no-reform model, 2026-10-31; [NO_REFORM_MODEL_RESULTS.md](parking/NO_REFORM_MODEL_RESULTS.md)):** a "same pace as before" baseline was tested on places with no parking reform nationwide, on places and years held out. It is the best predictor for single places, but its totals came out at 0.83 of what was actually permitted, and at 0.78 in Wisconsin's 2021–2025 back-test. The test years include the 2020–2022 boom. In the full model runs ([BASELINE_MODELS_RESULTS.md](parking/BASELINE_MODELS_RESULTS.md)) no model beat same pace on held-out cities, and on held-out state totals tree models only matched same pace with a national level adjustment. A boosted-trees model gives 118,417 for Wisconsin (round 6, after an audit-found leak and unreliable permit-file population were fixed; earlier rounds gave 114,042 and 124,582). It is shown as a sensitivity.
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
| The statewide total and where it lands | Places that partly removed minimums left out | 19,649 |
| The statewide total | Cleaned data, undated reforms kept as comparisons (placebo, round 1) | 29,843 |
| The statewide total | Cleaned data, strict comparison cleaning (resampling, round 1) | 38,230 |
| The statewide total | Cleaned data, strict comparison cleaning (placebo, round 1) | 49,712 |
| The statewide total | Cleaned data, only apartment-scale reforms disqualify comparisons (placebo, round 2, V7) | 29,307 |
| The statewide total | As above, plus CA, OR and WA state laws (placebo, round 2, V7s) | 27,671 |
| Current law only | Census as published for Milwaukee | 118,822 permits under current law |
| Current law only | Boosted-trees no-reform model (round 6: homes from the ACS release ending at each origin; scaled to the v3 central) | 119,750 permits under current law |
| Current law only | If recent strength continues (random forest, scikit-learn; full 2020–2025 level higher) | 134,323 permits under current law |

Stability (first 24 places): leaving one state out at a time gave an average effect of −2.47 to +0.09 permits per 1,000 homes per year.

#### Intended users and appropriate use cases

Wisconsin legislators and staff asking whether a statewide parking repeal would raise housing production.
- **Appropriate:** reading the result as "little or no measurable change within five years, with a stated high end", and seeing where that high end would fall.
- **Not appropriate:** reading municipal figures as local forecasts; using them to judge a parking repeal's effect on rents or parking supply.

## Part C. Transit-oriented density (TOD)

> **Maintained by the TOD session.** This part is a word-for-word copy of [docs/tod/MODEL_AND_ASSUMPTIONS_TOD.md](tod/MODEL_AND_ASSUMPTIONS_TOD.md) at commit 935edaf (2026-10-27), with only its heading levels changed. Edit the master copy, not this one. Its links are rewritten to resolve from `docs/` by `scripts/sync_model_doc.py`. Two changes made after the TOD Gate 3 check await the owner's confirmation; neither changes the statewide totals: keeping the measured New York build-up unsmoothed, and scaling the suburbs' share of the placement by 0.719.

### Transit-oriented density (TOD): model and assumptions

Master copy for the TOD section of [MODEL_AND_ASSUMPTIONS.md](MODEL_AND_ASSUMPTIONS.md). Last updated 2026-11-03 (AQ-075, upper back to the average scaled to 15%, the 2×2 readings as what-ifs; AQ-072, lines from the causal framework; AQ-071, option D; earlier AQ-068 to AQ-070, AQ-053, AQ-054, AQ-057). Option D plan and log: [OPTION_D_PLAN.md](tod/OPTION_D_PLAN.md); causal framework: [CAUSAL_FRAMEWORK_PLAN.md](tod/CAUSAL_FRAMEWORK_PLAN.md). Decisions: AQ-044 to AQ-051 in [ASSUMPTIONS_AND_QUESTIONS.md](ASSUMPTIONS_AND_QUESTIONS.md). Detail: [GATE3_PACKET.md](tod/GATE3_PACKET.md), [MODEL.md](tod/MODEL.md).

#### 1. Purpose and scope

The tool estimates how many more homes would be permitted in Wisconsin over 2027–2031 if the state passed a transit-oriented density law. Since AQ-071 (owner, 2026-11-02) the modelled law is **option D, the transit district mandate**: every Wisconsin city with qualifying rail or rapid stops zones a by-right multifamily district (at least 15 homes per acre) covering 15% of the lot acres within ¼ mile of those stops. It replaces the earlier benchmark law (SB 79-style heights and floor area on about 71% of the lots within ¼ mile), whose lines are kept as what-ifs.

- **Outcome:** housing units in issued building permits, compared with current law in the same places. Not completed homes.
- **Law start:** a stylized 1 January 2027.
- **Scope of the reform:** the reform is modelled on its own. Parking minimums are not changed; they belong to the parking scenario. A separate combined view shows the two together.
- **Where it applies:** the district is within ¼ mile of streetcar and rapid bus stations (6,394 lot acres: Madison 3,647, Milwaukee 1,564, Wauwatosa 614, Kenosha 265, Shorewood Hills 161, Sun Prairie 93, Burke 47, Blooming Grove 2). Results are counted, against current law, in the station areas: within ½ mile of streetcar and rapid bus stations, and within ¼ mile of bus routes with service every 15 minutes or better at the morning peak.
  - That covers 313,564 of Wisconsin's 2,727,726 homes in the 2020 census (11.5%).
  - 98.7% of those homes are in Milwaukee County and Dane County.

**Shared reporting units (AQ-054).** For comparison across reforms, the TOD scenarios are restated against the statewide all-housing baseline and on Wisconsin's ACS 2020–2024 home count. These figures are not stacked or added to the other reforms.

| Scenario | Extra homes permitted a year, statewide | As a share of the statewide all-housing baseline (124,000 homes over 2027–2031) | As a share of Wisconsin's 2,778,572 homes (ACS 2020–2024) |
| --- | --- | --- | --- |
| Lower: the rezoned parcels' own gain only (3,958 over five years) | about 792 | 3.2% | 0.14% |
| Central: the average district place, across about 12% of lots within ¼ mile of transit (10,028) | about 2,006 | 8.1% | 0.36% |
| Upper: the average district place, scaled up to 15% of lots within ¼ mile of transit (12,521) | about 2,504 | 10.1% | 0.45% |

The station-area shares (1.3%, 3.2% and 4.0% of the 313,564 homes near stops) stay on the 2020 census count, because the station areas are built from census blocks.

**No median line for TOD.** A median line of real cases is shown only when a reform has at least 4 comparable cases. TOD shows none: its central is already the average of the 11 district places.

#### 2. Core assumptions and their rationale

- **What counts as a "major transit stop" (AQ-044, AQ-047).** The main definition is rail and rapid bus (the Hop and Kenosha streetcars, Milwaukee's CONNECT 1, Madison's Rapid Route A) plus any stop on a route running 4 or more trips an hour in one direction at 7:00–8:59 on weekdays.
  - The 15-minute test matches California, Colorado and most state laws, and every Wisconsin agency's own schedule can measure it.
  - Amtrak stations are excluded: they run far fewer than the 48 trains a day that California's SB 79 requires for commuter rail.
  - The distances (½ mile for rail and rapid bus, ¼ mile for bus) follow the state laws reviewed. No study measures how the building response falls off with distance.
- **The law (AQ-071; replaces AQ-047, AQ-049).** Option D: every city with rail or rapid stops (The Hop, the Kenosha streetcar, CONNECT 1, Rapid Route A) zones a by-right multifamily district, at least 15 homes per acre, on **15% of the lot acres within ¼ mile** of those stops. No affordability mandate; parking unchanged. The 15% follows what the training places used (owner: "base the district size on the benchmark policy which is based on what we have good data for ... 15% of lot acres within .25 miles of the stops is a good start", 2026-11-02). No site is picked: the district is spread at random over the ¼-mile land (owner: "I'd rather not pick specific sites but instead just show density in a radius of the TOD. But random is fine too."), so each lot there is in the district with probability 0.15. Land beyond ¼ mile counts zero. The former law (65 feet, FAR 3.0 and 100 homes per acre within ¼ mile of a station; 55 feet beyond) is kept only for the what-ifs.
- **Evidence (AQ-071).** 11 US places whose reform covered under 30% of the lots within ¼ mile (Philadelphia, Chicago 2015, Seattle Mount Baker, Denver, Seattle Othello, New York, Salt Lake City, Saint Paul, Charlotte, Portland 2020, Austin), each measured as reform stops against similar comparison stops, before and after. Their districts averaged 12% of the ¼-mile lots. By the rule fixed before results, the central is the best model only if it beats the other places' average on hidden places; no model did (median error within ¼ mile: average 19.3, zero 28.1, best model 22.3; extra homes per 100 lot acres a year).
- **Size of the effect (AQ-071).** Extra homes near stops over 2027–2031, Wisconsin (`reference/tod_optiond_line.csv`; ranges = each place left out in turn):
  - **Lower: the rezoned parcels' own gain only, 3,958 (90% range 2,280 to 5,791; leave one place out 1,600 to 4,873)** (AQ-072). The edge test: lots just inside a district boundary against lots just outside (91 m), after minus before, in the 5 places whose two sides were alike before the reform (Philadelphia, Austin, Chicago 2015, Denver, Saint Paul), pooled 88.2 extra homes per 100 lot acres a year of district land × 15% × 4,874 lot acres ÷ 100 × 5 years × 1.227. It counts only the rezoned lots' own gain, so it is a floor; fake boundaries show about zero, and broad upzonings show no jump ([CAUSAL_FRAMEWORK_PLAN.md](tod/CAUSAL_FRAMEWORK_PLAN.md), Test 2 and its expansion).
  - **Central: the average district place, across about 12% of lots within ¼ mile of transit, 10,028 (range 7,580 to 12,010).** The places' mean effect within ¼ mile, 33.54 extra homes per 100 lot acres a year × 4,874 lot acres within ¼ mile of rail and rapid stops (Milwaukee and Madison) × 5 years × 1.227 for the rest of the state.
  - **Statewide scale (owner 2026-11-02 14:54, "You can switch.").** All Wisconsin lot acres within ¼ mile of rail and rapid stops ÷ those in the cities of Milwaukee and Madison: 6,394 ÷ 5,212 = 1.227, computed from `reference/tod_station_areas.csv` (the same land the placement uses). It replaced homes within ½ mile, 89,528 ÷ 80,930 = 1.106.
  - **Upper: the average district place, scaled up to 15% of lots within ¼ mile of transit, 12,521 (leave one place out 9,089 to 16,771)** (AQ-075; the option D upper of AQ-071). The 11 places' pooled effect per share of land zoned × 15%: 41.9 extra homes per 100 lot acres a year within ¼ mile, × the same acres, years and scale (`reference/tod_optiond_line.csv` row `optiond_average_scaled_15`, copied to `reference/tod_causal_lines.csv` row `upper_average_scaled_15`). Caveat: among the 11 places the effect fell as the district share grew (rank correlation −0.32; a straight line at 15% gives 8,143), so scaling up leans on the smallest districts. Owner: "good catch - yes to all three", 2026-11-03 11:52.
  - **The 2×2 readings, now what-ifs (AQ-075).** Upzoning with new transit lines (T2b; the upper under AQ-072): near lines 0–3 years old at the reform, rezoned stops gained 44.99 extra homes per 100 lot acres a year more than new-line stops not rezoned: 13,451 (leave one place out 10,431 to 15,049). Its before-reform check (T2b-PT) failed: rezoned stops on new lines were already gaining 30.2 per 100 lot acres a year before any reform (90% 12.0 to 50.7). Upzoning with new transit lines, minus the growth already under way before the reforms (fake-years check): 18.8 per 100 lot acres a year, 5,624 homes (paired place bootstrap 90% −2,776 to 13,666; leave one place out 2,340 to 9,684), read from `reference/tod_causal_line_age_pretrend.csv`.
  - **Beside the central:** line-age matched 6,932 (90% 2,717 to 14,147); Massachusetts MBTA Communities, first year: no rise; Los Angeles TOC tier cutoffs: a bigger bonus did not add building. Transit alone (new lines, no rezoning): +17.8 per 100 lot acres a year, about 5,315 homes, which belongs in the baseline, not the law.
  - Former option D lower (AQ-071), now a what-if: 824 (best lot model, −90 to 1,006). The option D upper (12,521) is the upper line again (AQ-075).
  - Former lines (broader law), now what-ifs: central 13,229 as shown then, 13,686 recomputed with the corrected lot data (average reform city at 71% coverage, AQ-070); strong 17,148 (Auckland); little 43 as shown then, −70 recomputed (station-area model, AQ-069).
  - **Labels (owner 2026-11-02 22:29):** "approve the TOD lines. I think Central should say (average, across 12% of lots within .25 miles of transit) and Upper should say (scaled to 15% of lots within .25 miles of transit)". The tool now reads "Central: the average district place, across about 12% of lots within ¼ mile of transit" and "Upper: the average district place, scaled up to 15% of lots within ¼ mile of transit".
  - **Data fixes behind these lines (2026-11-02).** Lot land counted once; missing lot sizes filled from each city's own Census land share; New York hotel, condo-hotel, care-home and superseded-job rule rows and Philadelphia double counts removed (3,929 rule rows plus 45 hand rows); Seattle corrections. Before the fixes the lines were 499 / 9,822 / 12,264.
- **Where homes land (AQ-071).** Each place's share of the statewide total = its share of the lot acres within ¼ mile of rail and rapid stops (central: Madison 5,721, Milwaukee 2,453, Wauwatosa 964, Kenosha 416, Shorewood Hills 252, Sun Prairie 145, Burke 73, Blooming Grove 4). The former placement by the old law's added floor area (AQ-051) is a what-if.
- **No floor at zero.** Places already at or above the law get no addition, but a measured line may be below zero where the evidence says so (owner rule against evidence-free floors).
- **Timing (AQ-080, owner 2026-11-11 00:07).**
  - Every line, and the range's two ends, follow the yearly build-up measured across the same 11 district places behind the range: their average effect in each of the first five years after reform, each place weighted equally (`reference/tod_first_year_check.csv`, rows "by year (place-equal weight)", from `scripts/run_tod_first_year_check.py`).
  - Measured effects, extra homes per 100 lot acres a year within ¼ mile: 25.6, −5.2, 85.9, 42.3 and 19.1 in years 1 to 5. As shares of their five-year sum: 15.3%, −3.1%, 51.2%, 25.2% and 11.4% for 2027–2031.
  - Year 2 (2028) is slightly negative and is used as measured (no zero floor). The script reads the shares from the CSV (`eleven_place_build_up()` in `scripts/run_tod_model.py`).
  - Only the yearly split changed. The five-year totals are unchanged: range 3,922 to 16,335; side lines 10,028 / 3,958 / 12,521 / 13,451 / 5,624.
  - Central line (10,028) by year, 2027–2031: 1,530, −312, 5,138, 2,532, 1,141. Range low end: 598, −122, 2,010, 990, 446. Range high end: 2,492, −509, 8,369, 4,125, 1,858.
  - Before AQ-080 the lines followed the build-up after 17 New York City rezonings in 2003–2013 (shares 9.8%, 9.3%, 26.4%, 47.9%, 6.6%). It is kept as the What-if "Timing: New York rezonings' build-up (the former ramp)", beside the existing smoothed-2031 what-if.
  - The former strong line (Auckland) keeps Auckland's own yearly pattern in its what-if.
  - The per-acre method A (a sensitivity) still uses the New York ramp, because its *r* is New York's per-FAR rate.

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
5. **Sizing.** Since AQ-071 the statewide total comes from the 11 district places' measured station-area effects (section 2), and homes are placed across places in proportion to lot acres within ¼ mile of rail and rapid stops. The per-acre response from the cases above no longer sizes or places the line.
6. **Aggregation.** Station areas add up to municipalities, counties, Assembly and Senate districts, and the state.

#### 5. Limitations and known edge cases

- **No Wisconsin test of the adopted sizing.** The Madison test checked the per-acre method, which no longer sizes or places homes.
- **Chosen land versus a mandate.** The 11 places chose their district land, often land builders already wanted (old industrial land, low-value lots). A state mandate makes every city act, on land it may pick less well, so it may do less; the random placement does not capture this. Near Milwaukee's new streetcar, building rose by a similar amount with no rezoning, so part of the measured gain may come from new transit or booming neighbourhoods.
- **District size.** The places averaged 12% districts; the law asks for 15%. The upper line (12,521) assumes the effect grows in proportion; the central does not scale it.
- **No model beat the average.** Lot, stop-level, place, tract and affordability-rule models were all tried (OPTION_D_PLAN.md log); none beat the plain average on hidden places, so the lines carry no Wisconsin-specific trait adjustment.
- **Districts, not citywide upzoning.** For the 5 broad upzonings left out of training (BelRed, Honolulu, Los Angeles TOC, San Diego, Chicago 2022; measured −13.3 to +29.4 extra homes per 100 lot acres a year within ¼ mile), the average rule predicts +33.5 for each (median miss 42.9), the scaled rule 139 to 279 (median miss 240), and zero misses by a median 10.6 (`reference/tod_optiond_broad_check.csv`). The lines describe districts, not citywide upzoning.
- **Record years.** The lower line takes the Madison metro's apartment permitting above its own record year in 2030; the central and the upper in 2029–2030 (Madison) and 2030 (Milwaukee). No line passes the highest peer-metro year. The compare screen says so beside the lines.
- **Baseline and new-line growth.** The near-stop baseline (14,654) spreads each place's 2023–2025 permits by its share of homes near stops; it includes years after The Hop and most of CONNECT 1's first year but not Rapid Route A, and does not concentrate growth near the new stops. Its ¼-mile part is about 4,250 over five years, against about 5,315 for transit-alone growth; in Milwaukee recent building within ¼ mile (about 200 homes a year in new 5+ unit buildings, 2018–2025) is about twice the baseline's ¼-mile share (about 94 a year). So current law near stops may be understated; the law's lines exclude transit-alone growth (AQ-072).
- **Madison's 2023 overlay** already allows more along much of Rapid Route A; the model does not credit it, so Madison's share may be overstated.
- **Former typical line (Stacy et al. 2023, now a what-if).** Only 28 of Stacy et al.'s 96 loosening reforms changed floor area, density or height; a 2025–2026 AEI Housing Center review found most of its 180 reforms minor, misplaced or misclassified ([research/STACY_AEI_REVIEW.md](tod/research/STACY_AEI_REVIEW.md), AQ-059).
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

#### 6. Sensitivity notes (extra homes 2027–2031, central unless stated)

- **The law's addition:**
  - Lower at the ends of its range: 2,280 to 5,791 (90%). Central: 7,580 to 12,010 (each place left out). Upper: 9,089 to 16,771 (each place left out).
  - Upzoning with new transit lines (the 2×2): 13,451; minus the growth already under way before the reforms: 5,624 (AQ-075). Former option D lower 824 (best lot model). Line-age matched: 6,932.
  - District of 10%: 8,347; of 25%: 20,868 (the upper line's method). Straight line through the places at 15%: 8,143.
  - Former lines for the broader law, recomputed with the corrected lot data: central 13,686 (shown as 13,229, AQ-070), strong 17,148 (Auckland, its own yearly pattern), little −70 (shown as 43, AQ-069). Earlier: Los Angeles TOC 171, drift rule 1,196 (AQ-068), Stacy et al. 2,509.
  - Final year smoothed: same totals, with 2,248 homes in 2031 instead of 664 (central).
- **Where homes land (totals unchanged):**
  - Placed by the broader law's added floor area (AQ-051): Milwaukee metro 6,542 and Madison metro 3,305 (main: 3,417 and 6,195).
  - Only Milwaukee and Madison cities get homes: Milwaukee metro 3,010 and Madison metro 7,018.
  - Stop definitions change only current law near stops: rail and rapid only 6,206; 20-minute buses 15,984; all 15-minute stops within ½ mile 18,676 (main 14,654). The law's addition is the same.
- **Baseline only:** 6,677 to 25,865 (v4 statewide pair applied to this area; aims at 90% for the state total, not tested for this area; the pair is built from all states' past five-year outcomes), or 11,503 with Milwaukee's apartments as the Census published them. The addition is unchanged.

#### 7. Intended users and appropriate use cases

- **Intended users:** Wisconsin legislators and staff, and local officials in Milwaukee, Madison and other cities with frequent transit.
- **Good uses:**
  - comparing the likely size of a TOD law with current law;
  - seeing where the extra homes would go;
  - understanding the range of the evidence (the upper line is about 3.2 times the lower one);
  - comparing TOD with ADU and parking reform.
- **Not appropriate for:**
  - parcel-level forecasts;
  - predicting a specific project;
  - setting housing targets;
  - forecasting effects after 2031;
  - judging rents or displacement.

Read the scenarios as different readings of the same 11 district places (best model, plain average, average scaled to 15%), not as a statistical confidence interval.
