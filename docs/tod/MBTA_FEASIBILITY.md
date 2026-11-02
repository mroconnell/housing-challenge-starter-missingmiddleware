# Massachusetts MBTA Communities: feasibility scan (T5)

2026-11-02. Locked rule: [CAUSAL_FRAMEWORK_PLAN.md](CAUSAL_FRAMEWORK_PLAN.md), "Test 5 (T5)".
Script: `scripts/run_tod_causal_mbta.py`. Numbers: `reference/tod_causal_mbta_event.csv`.

## Verdict

- **Feasibility: GO.** It passes the locked rule by a wide margin.
  - Rule: at least 20 compliant towns with at least one full post-deadline year of permit data.
  - Found: 104 towns. They are Compliant or Conditionally compliant and kept an original deadline of 12/31/2023 or 12/31/2024.
- **Year-1 direction: no sign of a rise.** The year-1 change is slightly negative. But the same test run one year early is also negative, so this reads as a trend gap, not an effect.
- **Use for Wisconsin: narrative only.** No size is carried over.

## The data

| Question | Answer | Source |
| --- | --- | --- |
| Does the Census permit survey cover MA towns every year? | Yes. All 351 cities and towns appear in every annual file, 2015–2025, as county subdivisions. | Census BPS Northeast place files `ne2015a`–`ne2025a` (on disk in `data/raw/tod_control_cities/bps`) |
| Is 2025 available? | Yes. The 2025 annual file was posted 2026-05-14. 2026 has monthly files only. | www2.census.gov/econ/bps/Place/Northeast Region/ |
| Gaps | 74–95 MA towns a year report 0 months; their counts are estimated. In 2025 this includes Somerville and Andover. | BPS "months reported" field |
| Licence | US federal government work: public domain (17 U.S.C. §105). | — |
| Which towns are covered, deadlines, status | 177 communities. Rapid transit deadline 12/31/2023. Commuter rail and adjacent 12/31/2024. Adjacent small towns 12/31/2025. Towns that missed: 7/14/2025. | State (EOHLC) compliance status sheet dated 2025-09-18, saved in `data/raw/tod_mbta/` |
| Adoption dates | **Not on the state sheet.** It gives status, not when. A timeline needs dated snapshots or town meeting records. | Same sheet |
| mass.gov reuse terms | Not verified (the site blocks automated reading; the sheet was read through a fetch service). | — |

Deadlines were checked against the official sheet:
- 11 towns are listed at 12/31/2023, plus Milton (a rapid-transit town now listed 7/14/2025 after its 2024 referendum).
- 103 towns at 12/31/2024.
- 35 adjacent small towns at 12/31/2025.
- 28 towns that missed a deadline at 7/14/2025.

### Status on the 2025-09-18 sheet (towns)

| Group (by original deadline) | Towns | Compliant or conditional |
| --- | --- | --- |
| 2023 (rapid transit, incl. Milton) | 12 | 12 |
| 2024 (commuter rail and adjacent, incl. late towns) | 130 | 95 |
| 2025 (adjacent small towns) | 35 | 9 |

Other counts, from news and the state, not re-checked here:
- 21 applications were in by the end of 2023.
- 116 towns had adopted zoning by 2025-01-14.
- 133 had adopted by May 2025.

## Year-1 check (only because feasibility passed)

**Method.**
- Outcome: units permitted per 1,000 homes. Homes are from the ACS 2015–2019.
- Each group's year after its deadline is compared with its own 3 earlier years.
- Comparison towns are those not yet due:
  - for the 2023 group in 2024: the 2024 and 2025 groups;
  - for the 2024 group in 2025: the 2025 group.
- Intervals are 90%, from resampling towns.

| Version | Year-1 change (units per 1,000 homes a year; 90% interval) | Same test one year early (pre-trend) |
| --- | --- | --- |
| Main, all units, towns equal | −2.6 (−5.1 to −0.4) | −1.5 (−4.0 to +1.0) |
| 5+ unit buildings only | −1.7 (−4.0 to +0.1) | −2.2 (−4.6 to −0.2) |
| Compliant towns only | −2.7 (−5.1 to −0.6) | −2.0 (−4.8 to +0.5) |
| Reported months only, towns with 0 months dropped | −4.5 (−8.6 to −0.8) | −2.3 (−6.7 to +1.3) |
| Weighted by homes | −2.2 (−4.6 to −0.2) | −1.5 (−3.9 to +0.9) |

Per group (main):
- 2023 group in 2024: −2.3 (−8.6 to +2.4), 12 towns.
- 2024 group in 2025: −2.6 (−5.3 to −0.3), 125 towns against 35.

Average units per 1,000 homes a year:

| Group | 2021–2023 average | 2024 | 2025 |
| --- | --- | --- | --- |
| 2023 group | 7.5 | 5.3 | 5.5 |
| 2024 group | 5.8 | 5.2 | 4.2 |
| 2025 group (comparison) | 5.7 | 6.5 | 6.8 |

**Reading (locked rule).**
- The main year-1 figure is "negative": its interval is below 0.
- But the one-year-early test points the same way. In 5+ unit buildings it is itself negative.
- So the gap was already opening before the deadlines. The comparison towns are small, mostly rural towns whose permits rose in 2024–2025.
- Honest reading: **no sign that the mandate raised permits in its first year.** The data cannot separate a small negative effect from a pre-existing gap.
- One year is also short. Most 3A projects were still in the pipeline in early 2026 (Boston Indicators: 6,898 homes in 34 towns).

**Compared with D-11.** Per the learning plan, a zero or negative mandated effect adds a "mandated district" sensitivity at the edge-test floor.
- The units differ: this is a whole-town rate; D-11 is per 100 station-area lot acres.
- So the comparison is in words only: a mandate that towns met on paper has shown no first-year rise in permits.

## Go / no-go

- **Go for a follow-up** once 2026 annual permits are published (around May 2027). That gives a 2-year read for the 2024 group.
- **Best design for that follow-up:**
  - Drop or reweight the rural 2025 group as the only comparison.
  - Add matched non-MBTA Massachusetts towns (174 are outside the law).
  - Add district maps, so building can be counted inside the districts, not just town-wide.
- **No-go for any number in the Wisconsin tool now.**
