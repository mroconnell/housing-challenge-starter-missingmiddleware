# Middle housing: proposed test design (draft v1)

Drafted 2026-11-06; v1 on 2026-11-09 after the [measurement check](MEASUREMENT_CHECK_RESULTS.md) and the [power check](POWER_CHECK.md), for Ryan's review. **Not locked.** No count in this design has been run. It states no expected results. The audit thread reviews it before any lock, and Ryan decides any tool change. Candidates and data come from [CANDIDATES.md](CANDIDATES.md).

## The question

If a state allows 2–6 homes on lots now limited to one house, how many extra homes get permitted each year, per 1,000 single-family homes?

## What we count

- **Unit:** homes permitted, per 1,000 single-family homes, per year.
- **Denominator:** single-family homes, detached plus attached (ACS 2020–2024, table B25024, rows 2 and 3), adjusted to each year as in the ADU model (`homes_by_year.py`).
- **Source:** Census permits (Building Permits Survey) for every test and every state (Ryan, 2026-11-08). Homes are counted, not lots.
- **Measures:**

| Measure | What it counts | Role |
| --- | --- | --- |
| **M1: homes in 1–4 unit buildings** | Census 1-unit, 2-unit and 3–4 unit homes. Census files townhouses, side-by-side duplexes, split-lot and small-lot homes as 1-unit, so they are all inside | **Main** (Ryan's proposal, 2026-11-09: stop at 4) |
| M2: homes in 2–4 unit buildings | Census 2-unit and 3–4 unit homes | Second: the part Census sees as multi-unit |
| M3: all homes | Every building size | Check |
| M4: homes in 5+ unit buildings | Census 5+ | Check (substitution) |
| M5: townhouse-inclusive counts | City records (Austin, Minneapolis; Portland if its licence passes) and California progress reports (SFA category) | Measurement check only (Test 6) |

- **Why stop at 4:** the power check found that leaving out 5+ buildings roughly halves the noise in every test. Census cannot cap at 10, 30 or 100 units; 5+ is its only size cut.
- **Cost:** 5–6 unit buildings fall outside M1 (handbook range goes to 6). Stated under "what this design cannot tell us".
- **5–6 unit sensitivity:** M1 plus 3.0% of Census 5+ homes, the share of 5+ homes in projects of 5 or 6 homes in California's 2018–2021 progress reports ([MEASUREMENT_CHECK_RESULTS.md](MEASUREMENT_CHECK_RESULTS.md)). Reported beside M1 as a rough estimate.

## Reporting rule (fixed before any result; Ryan, 2026-11-09)

- **M1 (homes in 1–4 unit buildings) leads** every result, chart and tool line.
- **M3 (all homes) is always published right beside it**, at the same size, labelled as the net effect on housing.
- **If M1 and M3 point in different directions** (one reads as a rise, the other as a fall, under the symmetric rule), the headline says so in plain words.
- No measure is promoted or dropped after results are seen. Any later change is labelled post hoc.

## Test 1. State laws against similar places elsewhere (main test)

- **Treated states:** Oregon and California. Maine and Vermont are run as a sensitivity, because they have only 2 years after their laws.
- **Windows:**

| State | Before | After | Left out |
| --- | --- | --- | --- |
| Oregon | 2015–2019 | 2023–2025 | 2020–2022 (compliance years and COVID) |
| California | 2018–2021 | 2023–2025 | 2022 (first year, reported separately) |
| Maine | 2019–2023 | 2024–2025 | — |
| Vermont | 2019–2022 | 2024–2025 | 2023 |

- **Comparison places:**
  - Census permit-issuing places in states with no statewide middle-housing law through 2025.
  - Washington places count only for years up to 2024.
  - Leave out every city on the candidate list, and any other place found with its own 2–6 unit reform.
- **Matching, fixed now:** for each treated place, comparison places from the same Census division, at ½–2× its population. Matching does not use outcomes.
- **Measure:** pooled log rate ratio, weighted by homes: permits after ÷ homes × years after, against the same before, in treated places, divided by the same ratio in comparison places. The difference in permits per 1,000 single-family homes per year is reported second.
- **Intervals:**
  - 90% bootstrap, resampling places clustered by state, seed 20261103.
  - A leave-one-state-out range.
- **Reading rule (symmetric):**
  - The interval is entirely above 1: a rise, compared with similar places.
  - The interval is entirely below 1: a fall.
  - The interval includes 1: no detectable change.

## Test 2. Cities just above and below Oregon's 10,000 line (side check)

- **Why:** cities were sorted by the state's own population estimate (PSU certified July 2020), not by any choice of theirs. Three cities over 10,000 by the Census 2020 count were left out ([OREGON_CUTOFF_CHECK.md](OREGON_CUTOFF_CHECK.md)).
- **Groups (law's count, non-Metro):** covered cities over 10,000 (duplexes from 2021-06-30) against left-out cities up to 10,000.
- **Bands:** main 9,000–10,999 (5 covered, 6 left out); wider 5,000–14,999 reported second.
- **Windows:** before 2016–2018; after 2022–2024. HB 3395 (2023) extended duplexes to cities of 2,500+ from 2025-06-30, so 2025 is out.
- **Statistic:** covered cities' mean change in rate minus left-out cities' mean change. 90% bootstrap over cities, seed 20261103. Same symmetric reading rule.
- **Known limits:** housing production strategies (ORS 197A.100) use the same line; whether left-out cities already allowed duplexes is unchecked. Smallest detectable gap: about 8.4 per 1,000 single-family homes per year for M1.
- **Later:** the same design for Montana (cutoff 5,000; in force 2024-09-03) and Washington (cutoff 25,000). Montana needs its 2026 data; Washington needs its 2027–2028 files.

## Test 3. City reforms against stand-in cities (placebo test)

- **Cities:** Minneapolis, Raleigh, Spokane, Walla Walla, Portland.
- **Reform years:**
  - Minneapolis 2020, with 2022–2024 flagged as injunction years;
  - Raleigh 2022;
  - Spokane 2023;
  - Walla Walla 2019;
  - Portland 2022.
- **Windows:**
  - Before: the 3 full years before the city's first reform was adopted. For example, Raleigh adopted TC-5-20 in July 2021, so its before years are 2018–2020.
  - After: every full year from the first full reform year to 2025.
- **Stand-ins:** at least 20 cities for each real city that never had such a reform, given the real city's reform year.
  - Drawn from its own state, then its Census division, then the nation.
  - ½–2× its population.
  - This is the rule already used for parking.
- **Data:** Census permits for all five cities. Spokane's Census rows are fully filled in by Census for 2018, 2020 and 2021, so Spokane uses the filled-in columns and is flagged. Washington's own counts are a check only, never pooled (they count townhouses as multi-unit).
- **Result:** where each real city's change falls among its stand-ins' changes (a percentile), plus the stand-ins' middle-90% spread.
- **Reading rule:**
  - Above the stand-ins' 95th percentile: a rise.
  - Below the 5th: a fall.
  - Otherwise: no detectable change.

## Test 4. Fake reform years (pre-trend check)

- **What:** rerun Tests 1 and 3 with the reform moved 3 years earlier, using only years before the real reform.
- **Reading rule:**
  - The 90% interval should include 1, or the city should sit inside its stand-ins' 5th–95th band.
  - If it does not, the main result is read as partly a trend that was already under way.

## Test 5. Hide each case in turn (held-out test)

- **What:** as in the ADU A3 test, hide each treated state or city in turn, predict it from the rest, and record the miss.
- **Output:** "how far off the method was for a place it never saw", as a range beside the result.
- **Rule:** report only.

## Test 6. How much Census permits miss (measurement check)

- **What:** in places that have both counts, compare M5 (townhouse-inclusive records) with Census M1 and M2, before and after each reform.
- **Places:** Austin, Minneapolis, California (progress reports), and Portland if its licence passes.
- **Output:** the ratio of each record count to the Census count, with a 90% bootstrap interval.
- **Rule:** report only. It sets how much a state with Census data only may be understated.

## Test 7. Did other building fall? (substitution check)

- **What:** Tests 1 and 3 rerun on M3 (all homes), M4 (5+ unit homes) and one-unit homes.
- **Rule:** report each with its interval, read with the same rule as Test 1.

## Data rules

- **Census permits:** use the "reported" columns, and keep only places reporting all 12 months in every window year. Census's filled-in columns are a sensitivity case.
- **Licences:** Durham city data is out (ODbL). Raleigh, Mecklenburg County and Sacramento terms grant no open licence, so they are proposed out; Census covers those cities. Austin (public domain) and Minneapolis (copyright waived) are in.
- **Data needed:** Census permits and ACS are on disk; Austin and Minneapolis records come from open APIs.

## Run order

1. Test 6 (measurement), so the gap is known before any effect is counted.
2. Test 4 (fake years).
3. Test 1, then Test 2.
4. Test 3.
5. Tests 5 and 7.

## Smallest detectable effects (power check, 2012–2018 permits only)

| Test | M1: homes in 1–4 unit buildings |
| --- | --- |
| 1. Oregon and California together | about +66% against comparison places (about +4.4 per 1,000 single-family homes per year) |
| 2. Oregon line, 9,000–10,999 | about 8.4 per 1,000 per year (about 26 homes per city per year) |
| 3. One city | 7.5 to 15 per 1,000 per year, depending on the city |

Full tables: [POWER_CHECK.md](POWER_CHECK.md).

## What this design cannot tell us

- The effect on homes built, rather than permitted.
- Effects on 5–6 unit buildings: M1 stops at 4, and Census cannot separate 5–6 from larger buildings.
- Small effects: each test can only detect effects at least as large as the power check shows.
- Effects in states whose laws are newer than the data (Washington, Montana, Arizona).
- Whether a state's result transfers to Wisconsin. The Wisconsin step (which places, which groups) is a separate plan.

## Decisions for Ryan before lock

Settled so far: Census data; count homes, not lots; power check first (done).

1. **Main measure:** confirm M1, homes in 1–4 unit buildings.
2. **Licences:** confirm Raleigh, Mecklenburg and Sacramento city records are out.
3. **Test 2:** keep the Oregon line as a labelled side check?
4. **Washington state law:** add it as a test when its 2027–2028 data arrive?
