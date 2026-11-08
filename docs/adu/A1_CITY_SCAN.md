# A1 data scan: no-law cities with ADU permit counts

Run 2026-11-07 for [CAUSAL_FRAMEWORK_PLAN.md](CAUSAL_FRAMEWORK_PLAN.md) test A1, at Ryan's request ("check for non reform cities with data existing and run that past audit").

This is a data-availability scan only. No effect was computed. The only rates computed are each candidate's own 2017–2019 rate, checked against A1's locked comparison rule.

## The locked A1 rules

- **No-law state:** the city's state had no statewide ADU law in force by the end of 2023. Arizona, Colorado and Montana qualify, because their laws came in 2024.
- **No local reform:** the city's own ADU rules did not change between 2017 and 2023. The windows are before 2017–2019 and after 2021–2023.
- **Yearly counts:** ADU permit counts for every year 2017–2023.
- **Comparison rule:** the city's 2017–2019 rate is at or above California's early-adopter cutoff. That cutoff is 1.038 ADU permits per 1,000 single-family homes a year (from the Gate 3 study code, top quarter, 2017–2019).
- **Minimum:** 5 cities.

## Method

Three research helpers checked 43 cities. For each city they looked at:
- whether it has a public permit dataset;
- whether ADUs can be identified in it, and how;
- the yearly counts, from one small query each;
- the city's own ADU rule changes, from official pages where possible.

Counts are permit records, mostly from text matches in permit descriptions. They are not unit counts.

## Result: A1 stays not feasible

**Two cities pass every rule: Asheville and Honolulu.** The minimum is 5.

| City | Data, 2017–2023 | Own ADU rule changes, 2017–2023 | 2017–2019 rate (ADU permits per 1,000 single-family homes a year) | Passes the 1.038 rule | Verdict |
| --- | --- | --- | ---: | --- | --- |
| Asheville NC | Accela permit layer. ADU type codes from 2022; text before that. 63, 50, 32, 30, 35, 35, 51 (records opened per year) | None found, but the code's amendment notes could not be read | 1.71 (48.3 a year ÷ 28,212 homes) | Yes | Tentatively clean |
| Honolulu HI | Series in the repository, 2016–2024 | None in the series coding | 1.42 | Yes | Clean (already in hand) |
| Austin TX | Series in the repository, 2005–2023 | 2015 reform is before the window; HOME phase 1 (Feb 2024) is after it | 0.59 (122.7 a year ÷ 209,772 homes) | No | Fails the rate rule |
| Fort Worth TX | ArcGIS, `Use_Type='Accessory Dwelling'`: 25, 45, 20, 61, 58, 71, 57 (by filing date) | None found; the code's history notes not read | 0.12 (30.0 a year ÷ 242,351) | No | Fails the rate rule |
| Charlotte NC | Mecklenburg permits, text match: 7, 15, 22, 32, 28, 32, 49 | New development code (UDO) effective 2023-06-01 | 0.07 (14.7 a year ÷ 203,927) | No | Fails the rule (and its 2023) |
| Boulder CO | ArcGIS, two layers that disagree by about 2× | Ordinances 2018-12 and 2023 | — | — | Out (rule changes) |
| Phoenix AZ | Search tool with CSV export only; "guest houses" class, not ADUs | Text amendment effective 2023-11-06 | — | — | Out (no counts; 2023 change) |
| San Antonio TX | Open data from July 2020 | Code change effective about 2023-01-01 | — | — | Out (no 2017–2019) |

**The other 35 cities are out.** The reasons:
- **Own ADU rule change in 2017–2023:** Raleigh, Durham, Nashville, Memphis, Atlanta, Kansas City, Dallas, Orlando, St. Petersburg, Chicago, Philadelphia, Pittsburgh, Louisville, Lexington, Tucson, Flagstaff, Colorado Springs, Bozeman, Missoula, Albuquerque, Boise, Ann Arbor, Grand Rapids, Richmond, Arlington County. Houston also changed (effective 2023-11-27) and has no permit-level data.
- **ADUs not legal, so counts are about zero:** St. Louis, Columbus, Cincinnati, Omaha, Oklahoma City, Tulsa.
- **No usable permit-level data:** Tampa, Miami, Indianapolis, Fort Collins, New Orleans (counts of 1 to 5 a year).

The full tables, query strings and sources are in the helpers' reports, summarised here.

## Why the rate rule binds

- A1 compares California's early adopters with similar no-law cities. Their 2017–2019 rates were 3.02 ADU permits per 1,000 single-family homes a year (A2).
- The cities with clean rules and data mostly permit far fewer ADUs: Austin 0.59, Fort Worth 0.12, Charlotte 0.07.
- Comparing California's busy cities with quiet ones would break the like-for-like assumption a comparison needs.

## Options for Ryan and the audit (none run)

1. **Keep A1 closed (recommended).** Only 2 cities pass; the minimum is 5.
2. **Records requests.** Fort Collins, Tampa and Houston (before November 2023) had stable rules but no public permit-level data. All three would still need to pass the rate rule.
3. **A different comparison, which would need a new locked plan.** Match each California activity group to no-law cities with similar 2017–2019 rates. Austin, Fort Worth and Charlotte sit near California's "in between" group (0.33).
   - That is a new test, not A1.
   - Its windows and cities would be chosen after this scan, so it would be labelled as designed after seeing which data exist (no effect seen).
