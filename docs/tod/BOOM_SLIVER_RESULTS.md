# Boom-and-bust placebo cities, and a sliver-sized Wisconsin law: results

Run 2026-10-28 against [BOOM_SLIVER_PLAN.md](BOOM_SLIVER_PLAN.md). Code: [scripts/run_tod_boom_sliver.py](../../scripts/run_tod_boom_sliver.py). Outputs: `reference/tod_boom_placebos.csv`, `reference/tod_sliver_law.csv`.

## 1. Boom-and-bust placebo cities

Each reform city is compared with cities that had about the same building rate before (within ±25%) and no reform. Effect = the reform city's change minus the boom cities' median change, as a share of the city's homes over five years.

| | Seattle (2019) | Minneapolis (2020) | Portland (2021) |
| --- | --- | --- | --- |
| Boom cities used | 13 | 37 | 18 |
| Reform city's change (homes permitted per 1,000 homes per year) | −4.2 | −5.6 | −10.3 |
| Boom cities' median change (same unit) | +6.6 | +1.3 | −0.3 |
| Effect, % of city homes over 5 years (90% interval) | −5.4 (−15.1 to +0.3) | −3.4 (−12.3 to +1.3) | −5.0 (−7.9 to −1.3) |
| Boom cities that fell as much | 8% | 22% | 6% |

- **Seattle and Minneapolis:** the intervals now include zero. Their drops sit within what similar boom cities did, so there's no measurable reform effect either way.
- **Portland fell more than 94% of boom cities.** The 2021 reform covered 58% of its homes, but Portland's 2021–2025 slump also coincided with its downtown and office collapse and Oregon's statewide rules for every city. This can't be pinned on the reform.
- **The boom cities are mostly Sunbelt cities** (Huntsville, Chandler, Mesa, Tempe) that kept booming. They are not great twins for expensive West Coast cities. A whole-city comparison still can't measure broad reforms reliably.

## 2. A sliver-sized Wisconsin law

**Response** = whole-city gain over five years (% of the city's homes) ÷ share of the city's homes upzoned (%). One point of coverage means upzoning 1% of the city's homes.

| Sliver cities | Number | 25th percentile | Median | 75th percentile |
| --- | ---: | ---: | ---: | ---: |
| All 14 | 14 | 0.19 | 0.36 | 0.68 |
| Without Milpitas and Bellevue | 12 | 0.16 | 0.26 | 0.51 |

Madison's own response is 0.50, against a median of 0.30 for the other 13.

**Extra homes over five years, Milwaukee and Madison together** (Milwaukee 257,614 homes in 2020; Madison 128,430):

| Law upzones this share of each city's homes | Little (25th percentile) | Typical (median) | Strong (75th percentile) |
| --- | ---: | ---: | ---: |
| 3%, all 14 cities | 2,185 | 4,222 | 7,931 |
| 3%, without Milpitas and Bellevue | 1,822 | 3,018 | 5,853 |
| 6%, all 14 cities | 4,369 | 8,443 | 15,863 |
| 6%, without Milpitas and Bellevue | 3,645 | 6,036 | 11,705 |

**Which station areas would make a 3–6% sliver?** Rail and rapid-bus stations within ¼ mile already cover 9.4% of Milwaukee's homes and 25.3% of Madison's. A 3–6% law would have to pick a subset, for example the busiest stations or the land nearest the platforms.

## 3. Reading it

- **The sliver law rests directly on measured cities, with no stretching.** A 3% law in Milwaukee and Madison gives roughly 3,000–4,200 extra homes over five years as typical. A 6% law gives roughly 6,000–8,400.
- **These are above today's typical scenario** (2,509 homes statewide), although they cover far fewer homes. That is because sliver reforms draw building from the surrounding region. Whether that would hold if both cities did it at once is the remaining uncertainty.
- **This is a different policy choice.** Upzone the best few station areas, not all of them. The owner decides the definition (the open definition question) and the typical value (AQ-059).
