# Oregon's 10,000-person line: the law's own count vs Census

Checked 2026-11-06 at Ryan's request. Research only. No permit counts were looked at for these cities; only data coverage (months reported).

## How the law counted population

- **Rule (V):** OAR 660-046-0020(11) defines a "Medium City" by its "certified Portland State University Population Research Center estimated population", more than 10,000 and less than 25,000, outside Metro. Source: OAR 660-046-0020 (Cornell LII mirror of the Oregon Administrative Rules).
- **Statute (V), 2019 text:** "more than 10,000 and less than 25,000" (ORS 197.758(3), 2021 edition). Exactly 10,000 was out.
- **Which year (V):** DLCD's February 2021 map of affected cities ([HB2001_Map.pdf](https://www.oregon.gov/lcd/UP/Documents/HB2001_Map.pdf)) includes Baker City. Baker City was under 10,000 in PSU's 2019 certified estimate (9,965) and over in the 2020 one (10,010). So DLCD used the 2020 certified estimate (certified 2020-12-15).

## The two counts near the line

| City | PSU certified July 2020 (the law's count) | Census, April 2020 count (base) | Covered in 2021? | Census months reported, 2015–2020 |
| --- | ---: | ---: | --- | --- |
| Silverton | 10,520 | 10,475 | Yes | 12 every year |
| Newport | 10,400 | 10,250 | Yes | 0 in 2017 |
| Cottage Grove | 10,155 | 10,594 | Yes | 12 every year |
| Baker City | 10,010 | 10,099 | Yes | 0 in 2015, 2018, 2019, 2020 |
| North Bend | 9,975 | 10,317 | **No** | 12 every year |
| Molalla | 9,910 | 10,231 | **No** | No Census permit rows for 2015–2019 |
| Astoria | 9,675 | 10,186 | **No** | 12 every year |
| Independence | 9,675 | 9,824 | No | 0 in 2016 |
| Sweet Home | 9,415 | 9,837 | No | 12 every year |

Sources: PSU [2020 certified estimates](https://www.pdx.edu/population-research/sites/g/files/znldhr3261/files/2020-12/Certified%20Population%20Estimates_2020_2.pdf); League of Oregon Cities copy of the [2019 certified list](https://www.orcities.org/application/files/9615/7800/7129/2019CertifiedPopulations-Numerical.pdf); Census [sub-est2023_41.csv](https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/cities/totals/sub-est2023_41.csv) (ESTIMATESBASE2020).

**Reading:** by the Census 2020 count, North Bend (10,317), Molalla (10,231) and Astoria (10,186) were bigger than Baker City (10,099), but the law left them out and covered Baker City. The split came from the estimate the law used, not from any choice by the cities.

## Limits found

- **The gap closed in 2025.** HB 3395 (Or Laws 2023 ch 223, effective 2023-06-30; V) lowered the duplex line to 2,500 people, with a compliance date of 2025-06-30. So the left-out cities were untreated only until mid-2025. The clean after-years are 2022–2024.
- **Another rule uses the same line.** ORS 197A.100 (HB 2003, 2019) requires housing production strategies in cities of 10,000 or more. Its effects would mix with the duplex rule's.
- **Very few cities.** Three left-out cities with Census counts over 10,000, against four covered cities near the line. Molalla has no usable Census permit rows. Baker City's before-years are mostly Census fill-ins.
- **Rules already in place not yet checked.** Some left-out cities may already have allowed duplexes. Each city's code would need checking.
- **So this is a case comparison, not a statistical test.** It could sit beside Test 2 as a labelled side check.

## Smallest gap the cutoff could detect

Computed 2026-11-06 with [`scripts/middle_or_cutoff_mde.py`](../../scripts/middle_or_cutoff_mde.py). It reads only pre-law years (2012–2019), and it takes the spread only from cities outside 9,000–10,999. No post-law year and no result was seen.

- **Unit:** homes in 2- and 3–4-unit buildings (Census permits, including Census fill-ins) per 1,000 single-family homes (ACS 2020–2024, detached plus attached) per year.
- **Spread:** standard deviation of each city's no-law change, 2017–2019 mean minus 2012–2016 mean: 1.33 per 1,000 per year (26 non-Metro cities of 5,000–24,999 by the state estimate).
- **Rule:** smallest detectable gap = (1.645 + 0.842) × spread × √(1/covered + 1/left out). That gives an 80% chance of detection, at the 90% intervals used elsewhere.

| Band (state estimate) | Covered | Left out | Smallest detectable gap (per 1,000 single-family homes per year) | In homes per city per year |
| --- | ---: | ---: | ---: | ---: |
| 9,500–10,499 | 4 | 4 | 2.33 | 7.4 |
| 9,000–10,999 | 5 | 6 | 2.00 | 6.3 |
| 7,500–12,499 | 7 | 11 | 1.60 | 5.0 |
| 5,000–14,999 | 9 | 20 | 1.32 | 3.8 |

- **For scale:** Oregon statewide permitted 0.59 such homes per 1,000 one-unit detached homes per year in 2019–2021 ([STATE_ADOPTION_INVENTORY.md](../scenarios/STATE_ADOPTION_INVENTORY.md)).
- **Small-sample bar:** with groups this small, a t-based bar is about 10% higher.
- **Fully reported years only:** 18 cities qualify, which leaves 1 covered and 3 left-out cities in 9,000–10,999. That is too few to test.
