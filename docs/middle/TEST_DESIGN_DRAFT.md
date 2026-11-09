# Middle housing: proposed test design (draft v2, for audit)

Drafted 2026-11-06. v1 on 2026-11-09 followed the [measurement check](MEASUREMENT_CHECK_RESULTS.md) and the [power check](POWER_CHECK.md). **v2 on 2026-11-09 adds the weak-spot and backdoor fixes Ryan accepted** (see "Changes in v2").

**Not locked.** No count in this design has been run, and it states no expected results. The audit thread reviews it before any lock. Ryan decides any tool change. Candidates and data: [CANDIDATES.md](CANDIDATES.md). No-peeking rules and log: [MEASUREMENT_CHECK_LOG.md](MEASUREMENT_CHECK_LOG.md).

## The question

When a state makes 2–4 homes legal on lots that allowed one house, how many more homes get permitted each year in 1–4 unit buildings? The answer is per 1,000 single-family homes, compared with the same places without the law. (The handbook scenario allows 2–6 homes. See "What we count" for why we measure to 4.)

**Causal diagram:**
- **The path we want:** law → 2–4 homes legal on house lots → projects built → homes permitted.
- **Backdoors** (each is handled under "How backdoors are handled"):
  - city size, land and existing homes;
  - interest rates, costs and COVID;
  - pro-housing politics;
  - low building before the law;
  - a housing shortage that changes over time;
  - other housing reforms;
  - spillover to nearby places;
  - Census filing rules.

## Primary result (fixed now)

**Test 1, measure M1.** Every other test and measure supports it. No other result may be promoted to the headline after results are seen.

## What we count

- **Unit:** homes permitted, per 1,000 single-family homes, per year.
- **Denominator:** single-family homes, detached plus attached (ACS 2020–2024, table B25024, rows 2 and 3), adjusted to each year as in the ADU model (`homes_by_year.py`).
- **Source:** Census permits (Building Permits Survey) for every test and every state (Ryan, 2026-11-08). Homes are counted, not lots.

| Measure | What it counts | Role |
| --- | --- | --- |
| **M1: homes in 1–4 unit buildings** | Census 1-unit, 2-unit and 3–4 unit homes. Census files townhouses, side-by-side duplexes, split-lot and small-lot homes as 1-unit, so they are all inside | **Main** (Ryan, 2026-11-09: stop at 4) |
| M2: homes in 2–4 unit buildings | Census 2-unit and 3–4 unit homes | Second |
| M2 share: M2 ÷ M1 | Share of 1–4 unit homes that sit in 2–4 unit buildings | Second. Guards against ordinary house-building swings: in California, 2018–2021, detached houses were 195,736 of 233,636 homes in 1–4 unit buildings (84%) |
| M3: all homes | Every building size | Always published beside M1 |
| M4: homes in 5+ unit buildings | Census 5+ | Check (substitution) |
| M5: townhouse-inclusive counts | City records (Austin, Minneapolis; Portland if its licence passes) and California progress reports (SFA category) | Measurement check only (Test 6) |

- **Why stop at 4:** in the power check, leaving out 5+ buildings roughly halved the noise in every test. Census cannot cap at 10, 30 or 100 units; 5+ is its only size cut.
- **5–6 unit sensitivity:** M1 plus 3.0% of Census 5+ homes. That is the share of 5+ homes in projects of 5 or 6 homes in California's 2018–2021 progress reports. Reported beside M1 as a rough estimate.

## Reporting rules (fixed before any result)

- **M1 leads** every result, chart and tool line. **M3 is always published right beside it**, at the same size, labelled as the net effect on housing (Ryan, 2026-11-09).
- **If M1 and M3 point in different directions** under the reading rule, the headline says so in plain words.
- **"No detectable change" never means zero.** Every result is shown with its test's smallest detectable effect from the power check, in the same units.
- No measure or test is promoted or dropped after results are seen. Any later change is labelled post hoc.

## Test 1. State laws against similar places elsewhere (primary)

- **Treated states:** Oregon and California. Maine and Vermont are run as a sensitivity, because they have only 2 years after their laws.
- **California is labelled "California's 2022 package".** SB 9 arrived alongside other state housing laws, which this design cannot separate: ADU laws, AB 2011 (2023), SB 684 (operative 2024-07-01) and SB 1123 (2025-07-01).

| State | Before | After | Left out |
| --- | --- | --- | --- |
| Oregon | 2015–2019 | 2023–2025 | 2020–2022 (compliance years and COVID) |
| California | 2018–2021 | 2023–2025 | 2022 (first year, reported separately) |
| Maine | 2019–2023 | 2024–2025 | — |
| Vermont | 2019–2022 | 2024–2025 | 2023 |

- **Comparison places:**
  - Census permit-issuing places in states with no statewide middle-housing law through 2025. Washington, Maine, Vermont, Montana and Arizona places are left out.
  - Leave out every candidate city.
  - Leave out any place found with its own 2–6 unit reform. Before lock, comparison places are screened against reform lists only, never outcomes: NYU Furman Land Use Reform Tracker, Pew, the Mercatus and Terner lists, and [CANDIDATES.md](CANDIDATES.md).
  - **Leave out places in counties that border Oregon or California** (Census county adjacency file), to avoid spillover.
- **Matching, fixed now:** for each treated place, comparison places from the same Census division, at ½–2× its population. Matching does not use outcomes.
- **Statistic:** pooled log rate ratio, weighted by homes. In treated places it is permits after ÷ (homes × years after), over the same before. That is divided by the same ratio in comparison places. The difference in homes per 1,000 single-family homes per year is reported second.
- **Main inference: rank against fake law states.**
  - Each untested state with comparison places in its division is treated as a fake law state and run through the same statistic. That gave 42 states in the power check.
  - Draws are made in pairs: one fake state takes Oregon's windows and one takes California's.
  - 10,000 pairs, seed 20261103.
  - The real Oregon–California average is placed in that spread.
- **Second inference:** 90% bootstrap over places, clustered by state, plus a leave-one-state-out range. With only 2 treated states, this can look too precise, so it is not the main reading.
- **Reading rule (symmetric):**
  - Above the fake pairs' 95th percentile: a rise.
  - Below their 5th percentile: a fall.
  - Otherwise: no detectable change.

## Test 2. Cities just above and below Oregon's 10,000 line (side check)

- **Why:** cities were sorted by the state's own population estimate (PSU certified July 2020), not by any choice of theirs. Three cities over 10,000 by the Census 2020 count were left out ([OREGON_CUTOFF_CHECK.md](OREGON_CUTOFF_CHECK.md)).
- **Groups (law's count, non-Metro):** covered cities over 10,000 (duplexes from 2021-06-30) against left-out cities up to 10,000.
- **Bands:** main 9,000–10,999 (5 covered, 6 left out); wider 5,000–14,999 reported second.
- **Windows:** before 2016–2018; after 2022–2024. HB 3395 (2023) extended duplexes to cities of 2,500+ from 2025-06-30, so 2025 is out.
- **Statistic:** covered cities' mean change in rate minus left-out cities' mean change. 90% bootstrap over cities, seed 20261103. Same symmetric reading rule.
- **Before lock:** check each left-out city's zoning code (documents only) for duplexes allowed before 2021.
- **Known limit:** housing production strategies (ORS 197A.100) use the same line. Their effect cannot be separated.
- **Later:** the same design for Montana (cutoff 5,000; in force 2024-09-03) and Washington (cutoff 25,000), when their data allow.

## Test 3. City reforms against stand-in cities

- **Cities and reform years:**
  - Minneapolis 2020, with 2022–2024 flagged as injunction years;
  - Raleigh 2022;
  - Spokane 2023;
  - Walla Walla 2019;
  - Portland 2022.
- **Windows:**
  - Before: the 3 full years before the city's first reform was adopted. Example: Raleigh adopted TC-5-20 in July 2021, so its before years are 2018–2020.
  - After: every full year from the first full reform year to 2025.
- **Stand-ins:** at least 20 cities per real city that never had such a reform, each given the real city's reform year.
  - Drawn from its own state, then its Census division, then the nation, at ½–2× its population (the parking rule).
  - Stand-ins are screened against the same reform lists as Test 1.
- **Data:** Census permits for all five cities. Census filled in Spokane's 2018, 2020 and 2021 rows entirely, so Spokane uses the filled-in columns, is flagged, and is checked against Washington's own (OFM) total permits. OFM counts are never pooled with Census counts.
- **Result:** each real city's percentile among its stand-ins, plus their middle-90% spread.
- **Reading rule:**
  - Above the stand-ins' 95th percentile: a rise.
  - Below the 5th: a fall.
  - Otherwise: no detectable change.

## Test 4. Fake reform years (pre-trend check)

- **What:** rerun Tests 1 and 3 with the reform moved 3 years earlier, using only years before the real reform.
- **Reading rule:** the fake-year result should read "no detectable change" under each test's own rule. If it does not, the main result is read as partly a trend that was already under way.
- **Limit:** Census place files on disk start in 2012, and earlier years are free online. Oregon's fake windows need 2012–2016.

## Test 5. Hide each case in turn (held-out test)

- **What:** as in the ADU A3 test, hide each treated state or city in turn, predict it from the rest, and record the miss.
- **Output:** "how far off the method was for a place it never saw", shown beside the result.
- **Limit:** with 7 cases (2 states, 5 cities), the range is rough.
- **Rule:** report only.

## Test 6. How much Census permits miss (measurement check)

- **What:** in places with both counts, compare M5 (townhouse-inclusive records) with Census M1 and M2, before and after each reform.
- **Places:** Austin, Minneapolis, California (progress reports), and Portland if its licence passes.
- **Output:** the ratio of each record count to the Census count, with a 90% bootstrap interval.
- **Rule:** report only.

## Test 7. Did other building fall? (substitution check)

- **What:** Tests 1 and 3 rerun on M3 (all homes), M4 (5+ unit homes) and one-unit homes.
- **Rule:** report each with the same reading rule as its test.

## Law strength (coded before lock, no outcomes)

For each treated state and city, record:
- homes allowed per lot;
- where the rule applies (city sizes, zones);
- the share of single-family homes covered;
- any carve-outs.

This shows how far each law falls short of the handbook scenario (2–6 homes, 3 stories). The Wisconsin plan can then scale results, and the scaling rule is set in that plan.

## How backdoors are handled

| Backdoor | How the design blocks it | Status |
| --- | --- | --- |
| City size, land, existing homes | Before/after within each place, so fixed traits cancel | Blocked |
| Interest rates, costs, COVID | Comparison places of similar size in the same division share the years | Blocked |
| Pro-housing politics | The fixed part cancels; Test 2 compares cities under the same state politics | Mostly blocked |
| Low building before the law (bounce-back) | Test 4; matching on size and region | Blocked only if Test 4 passes |
| Housing shortage changing over time | Test 4 catches trends already under way | **Partly open:** a shock starting the same year as the law is not caught |
| Other housing reforms | Reform-list screening; candidate cities left out; California labelled as a package | **Partly open:** California's package; Oregon's housing-plan rule at the same line |
| Spillover to nearby places | Counties bordering Oregon or California left out of comparisons | Blocked for neighbours; wider spillover open |
| Census filing rules | M1 includes townhouses and split-lot homes; Test 6 measures the remaining gap | Measured, not removed |

## Data rules

- **Census permits:** use the "reported" columns, and keep only places reporting all 12 months in every window year. Census's filled-in columns are a sensitivity case (and Spokane's main case).
- **Licences (Ryan, 2026-11-09):**
  - Out: Durham (ODbL), Raleigh, Mecklenburg County and Sacramento (no open licence). Census still covers those cities.
  - In: Austin (public domain) and Minneapolis (copyright waived).
  - Portland: checked before use.
- **Data needed:** Census permits and ACS are on disk. Also needed: the Census county adjacency file, Census place files for 2010–2011 (Test 4), and Austin and Minneapolis records from open APIs.

## Run order

1. Before lock: reform-list screening, border list, Test 2 zoning check, law strength coding. None uses outcomes.
2. Test 6 (measurement).
3. Test 4 (fake years).
4. Test 1 (primary), then Test 2.
5. Test 3.
6. Tests 5 and 7.

## Smallest detectable effects (power check, 2012–2018 permits only)

| Test | M1: homes in 1–4 unit buildings |
| --- | --- |
| 1. Oregon and California together | about +66% against comparison places (about +4.4 per 1,000 single-family homes per year) |
| 2. Oregon line, 9,000–10,999 | about 8.4 per 1,000 per year (about 26 homes per city per year) |
| 3. One city | 7.5 to 15 per 1,000 per year, depending on the city |

Full tables: [POWER_CHECK.md](POWER_CHECK.md). Test 1's main inference is now the fake-state ranking. The power check used the same fake-state spread.

## What this design cannot tell us

- The effect on homes built, rather than permitted.
- Effects on 5–6 unit buildings: M1 stops at 4, and Census cannot separate 5–6 from larger buildings.
- Small effects: each test can only detect effects at least as large as the power check shows.
- SB 9's effect apart from California's other 2022–2025 housing laws.
- A demand shock that starts in the same year as a law.
- Effects in states whose laws are newer than the data (Washington, Montana, Arizona). Washington's state law is added as a test when OFM's 2027–2028 data arrive.
- Whether a state's result transfers to Wisconsin. That is a separate plan, started in parallel, using no results from these tests.

## Changes in v2 (accepted by Ryan, 2026-11-09)

| # | Weak spot | Change |
| --- | --- | --- |
| 1 | Two treated states make a state-clustered bootstrap look too precise | Main inference is the rank among fake law-state pairs; the bootstrap is second |
| 2 | California passed many housing laws at once | Result labelled "California's 2022 package" |
| 3 | M1 is mostly ordinary houses | M2 share (2–4 unit homes ÷ M1) added as a fixed side line |
| 4 | City tests can only see big effects | "Not detectable" never means zero; detection bar shown beside every result |
| 5 | Many tests and measures | One primary result named: Test 1, M1 |
| 6 | Comparison places may have reformed, or caught spillover | Reform-list screening before lock; counties bordering Oregon or California left out |
| 7 | Laws differ in strength | Law strength coded before lock |
| 8 | No bridge to Wisconsin | Wisconsin plan started in parallel, using no results |
| 9 | Spokane fill-ins; few fake years; rough held-out range | Spokane checked against OFM totals; limits stated |
| — | Open decisions from v1 | Licences settled (see Data rules); Test 2 is a side check; Washington state law added when its data arrive |
