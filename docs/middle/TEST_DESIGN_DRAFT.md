# Middle housing: proposed test design (draft v0)

Drafted 2026-11-06 for Ryan's review. **Not locked.** No count in this design has been run. It states no expected results. The audit thread reviews it before any lock, and Ryan decides any tool change. Candidates and data come from [CANDIDATES.md](CANDIDATES.md).

## The question

If a state allows 2–6 homes on lots now limited to one house, how many extra homes get permitted each year, per 1,000 single-family homes?

## What we count

- **Unit:** homes permitted, per 1,000 single-family homes, per year.
- **Denominator:** single-family homes, detached plus attached (ACS 2020–2024, table B25024, rows 2 and 3), adjusted to each year as in the ADU model (`homes_by_year.py`).
- **Three measures, all reported:**

| Measure | What it counts | Where it exists |
| --- | --- | --- |
| M1: midsized | Homes in 2-unit and 3–4-unit buildings (Census permits) | Every US place |
| M2: midsized plus townhouses | M1 plus townhouses, from city or state records | Portland, California (progress reports), Austin, Raleigh and Charlotte (if their licences pass) |
| M3: all homes | All permitted homes, every building size | Every US place |

- **Why three.**
  - M1 is the only measure that exists everywhere, which suits the thin-data bonus.
  - M2 shows how much M1 misses.
  - M3 shows whether middle housing adds homes or only replaces houses and apartments that would have been built anyway.
- **Ryan decides** which measure feeds the tool (question 1 below).

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

## Test 2. Cities just above and below a law's size cutoff (Oregon)

- **Why:** Oregon's law covers cities of 10,000 or more people, so cities just under the cutoff are a comparison inside the same state.
- **Groups:**
  - Cities of 10,000–25,000 (duplexes from 2021-06-30);
  - Cities of 25,000 or more (2–4 units from 2022-06-30);
  - Cities of 2,500–9,999 (not covered).
- **Same measure, intervals and reading rule as Test 1.**
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
- **Data:**
  - Spokane and Walla Walla use Washington state agency (OFM) permits.
  - The others use Census permits.
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

- **What:** in places that have both counts, compare M2 with M1 before and after each reform.
- **Places:** Portland, California, Austin, and Raleigh and Charlotte if their licences pass.
- **Output:** the ratio of M2 to M1, with a 90% bootstrap interval.
- **Rule:** report only. It sets how much a state with Census data only may be understated.

## Test 7. Did other building fall? (substitution check)

- **What:** Tests 1 and 3 rerun on one-unit homes and on 5+ unit homes, and on M3 (all homes).
- **Rule:** report each with its interval, read with the same rule as Test 1.

## Data rules

- **Census permits:** use the "reported" columns, and keep only places reporting all 12 months in every window year. Census's filled-in columns are a sensitivity case.
- **Licences:** Durham city data is out (ODbL). Raleigh, Charlotte (Mecklenburg County) and Sacramento wait for Ryan's answer.
- **Data needed:** everything is on disk except the Raleigh and Mecklenburg permit tables.

## Run order

1. Test 6 (measurement), so the gap is known before any effect is counted.
2. Test 4 (fake years).
3. Test 1, then Test 2.
4. Test 3.
5. Tests 5 and 7.

## What this design cannot tell us

- The effect on homes built, rather than permitted.
- Effects of the 5–6 unit part of the handbook range, unless city records separate it.
- Effects in states whose laws are newer than the data (Washington, Montana, Arizona).
- Whether a state's result transfers to Wisconsin. The Wisconsin step (which places, which groups) is a separate plan.

## Decisions for Ryan before lock

1. **Tool measure:** M1 (midsized), M2 (with townhouses) or M3 (all homes)?
2. **Townhouses:** count them where records exist?
3. **5–6 unit buildings:** leave them out, or estimate them from city records?
4. **Washington:** use Spokane and Walla Walla now, and add the state law in 2027–2028?
5. **Licences:** use Raleigh, Mecklenburg and Sacramento permit data, which state no clear licence?
