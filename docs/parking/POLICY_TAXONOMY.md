# Parking reforms: which are real, and what the evidence says (Gate 1)

Written 2026-10-26 by the parking conductor. Status: Gate 1 research, for owner review. Figures marked "source lead" come from abstracts or secondary write-ups and still need checking against the full source.

## Answer so far

- **A usable classification exists.** The Parking Reform Network (PRN) reform map is a database of 6,610 places, kept on GitHub under the MIT licence. Each record gives the reform's scope, the land uses it covers, its conditions, an adoption date and citations to the code. We rate every US record against the benchmark with a written rule (below). That rule found 235 US cities that removed minimums for all housing, by right. 49 of them did so in 2022 or earlier, so they have at least three years of permits since.
- **No state law can supply post-law evidence yet.** Every statewide law is transit-only, small-project-only, capped rather than removed, or ADU-only, and none is older than 2023. The evidence will come from cities that repealed minimums citywide.
- **Wisconsin already has cities at the benchmark.** West Allis (2022), La Crosse (2024), Fitchburg (2025), Franklin (2025), Monona, Cottage Grove (2026) and several villages have removed minimums for all housing, according to PRN. A statewide law adds nothing in those places, and West Allis is an in-state before/after case. Madison and Milwaukee have only partial reforms: downtown and some districts, a 25% cut near bus stops in Milwaukee, and houses and ADUs exempt.
- **Developers keep building parking, but less of it.** Every study found builds less than the old minimum on average, with a wide spread. Some projects build none, and some build more than the old minimum. That spread is the benchmark's "developer-provided parking" assumption, and it becomes a range.

## 1. The classification rule

Source: PRN `data/core.json` and `data/extended.json`, pinned to commit 3a62231 (fetched 2026-10-26 by `scripts/build_parking_taxonomy.py`). Code: `missing_middleware/parking/taxonomy.py`. Output: `reference/parking_reform_taxonomy.csv` (all 6,318 US city, county and state records) and `reference/parking_reform_cases.csv` (cities at or near the benchmark).

| Rating | Rule | Example |
| --- | --- | --- |
| **at** | Minimums removed citywide (or statewide) for all uses or all housing, by right, with no other condition | Buffalo 2017, Minneapolis 2021, West Allis 2022 |
| **near** | Removed citywide for housing, but with a condition: a project-size limit, an ADU part, a historic or "other" carve-out, or multifamily only | Connecticut PA 25-1 (up to 16 units); Madison multifamily (per PRN) |
| **weaker** | Removed only near transit, downtown, on main streets or in parts of a region; only for affordable housing; reduced but not removed; or only for houses and ADUs | California AB 2097, Oregon CFEC, Colorado HB24-1304, Illinois, Florida, Maryland |
| **plan_only** | PRN marks a plan or report recommendation "adopted", and the summary describes no code change | Milwaukee's comprehensive plan (2025) |
| **not_housing** | Does not touch residential uses | many commercial-only downtown exemptions |

Counts of US cities (a city can have several records; each city counted once per rating): 246 at, 108 near, 4,026 weaker, 60 plan_only and 1,186 not_housing.

**Why the plan_only rule matters.** PRN's status field calls a plan "adopted" when the plan was adopted, even if no code changed. Without the text check, Milwaukee, Appleton and Waukesha would have counted as full repeals. The rule flags records whose summary says "recommend" and has no word of enactment. It is a text heuristic. Every case used as evidence will be checked against the ordinance text before Gate 2 (step 3).

**Dates.** PRN records one date, usually the adoption date. It has no date for 105 of the 235 cities at the benchmark. Effective dates are not in PRN and will be recorded from the ordinance for each case we use.

## 2. State laws (all weaker than or near the benchmark)

| State | Law | PRN rating | Why |
| --- | --- | --- | --- |
| California | AB 2097 (2022, effective 2023) | weaker | only within ½ mile of high-quality transit |
| Oregon | CFEC rules (2022–2023) | weaker | near frequent transit; elsewhere caps; cities could choose full repeal (Portland, Eugene did) |
| Colorado | HB24-1304 (2024, effective mid-2025) | weaker | multifamily near transit in metro areas only |
| Connecticut | PA 25-1 (2025) | near | removed for projects of up to 16 units; larger ones may submit a needs study |
| Washington | SB 5184 (2025) | near (removal) / weaker (caps) | removal for small units, affordable housing and others; caps of 0.5 per multifamily unit |
| Illinois, Florida, Maryland | 2024–2026 | weaker | transit areas only |
| Maine | 2022 | weaker | ADUs only; affordable housing capped |
| North Carolina | HB 162 (2027; from the cross-scenario scan, not in PRN) | to verify | reported as no minimums for any use, coastal counties exempt |

## 3. Comparison cases for Gate 2

Cities rated **at**, adopted in 2022 or earlier, with population of 20,000 or more (25 cities, PRN populations): San Francisco (2018), Buffalo (2017), Hartford (2017), Mount Pleasant MI (2018), Dunwoody GA (2019), South Bend (2021), Minneapolis (2021), St. Paul (2021), Gastonia (2021), Roanoke (2021), Bridgeport (2021), Alameda (2021), Raleigh (2022), West Allis (2022), Ann Arbor (2022), Cambridge (2022), Culver City (2022), Central Falls (2022), Lexington (2022), Wilmington NC (2022), Anchorage (2022), Gainesville (2022), Corvallis (2022), San Jose (2022) and Tigard (2022). Each will be checked against the ordinance text (status, effective date, any later carve-outs), and against other reforms passed at the same time. Minneapolis's 2040 plan, for example, also upzoned, so its permits cannot be credited to parking alone.

The proposed test, to be pre-registered at Gate 2: permits by building size from the Census Building Permits Survey place files (public domain), for each case city and for comparison cities without reform matched on size, region and pre-reform permit trend. The outcome is units per 1,000 existing homes per year, by year since reform.

## 4. Developer-provided parking: evidence leads

| Case | Finding | Status |
| --- | --- | --- |
| Buffalo, 2017 citywide repeal (Hess and Rehler, *JAPA* 2021) | 47% of 36 major developments in the first two years built fewer spaces than the old minimum. 14 mixed-use projects built 53% fewer spaces than required. Single-use projects in total built more than the old minimum. | source lead (abstract and authors' summary) |
| Seattle, 2012 removal near frequent transit (Gabbe, Pierce and Clowers, *Land Use Policy* 2020) | About 18,000 fewer spaces were built over five years than the old rules required. The "40% fewer spaces" figure often quoted is not confirmed. | source lead |
| Minneapolis, 2015 transit cut | Median 0.82 spaces per unit in 2015–2017 new development, and 0.42 for 10–50 unit projects, where the old rule was about 1 per unit (Metropolitan Council case study) | source lead |
| Champaign, IL (Sohoni and Lee, 2023) | On-site parking built in deregulated zones fell about 60% | source lead |
| Denver (Terner Center / Rocky Mountain Land Use Institute, 2025) | Pro forma simulation, assuming developers choose 0.5 spaces per unit near light rail and 1.0 elsewhere: removing minimums raises market-rate multifamily output about 12.5%, or about 460 homes per year | source lead; a model, not an observation |
| Cost per space | Structured parking up to about $50,000 per space (Denver planning office, cited above) | source lead; Wisconsin costs to find |

**What this means for the model.** Removing a minimum matters only where it bound. The studies suggest it binds for about half of larger projects, more for mixed-use and infill, and little for single-family homes. The Denver study is the closest published example of the cost-times-supply-response method (method B in the [Gate 1 plan](GATE1_PLAN.md)). Its 12.5% for a much stronger market is an upper reference point for Wisconsin, not a value to borrow.

## 5. Next steps

1. Read the full Buffalo, Seattle and Champaign papers and the Denver white paper; record spaces per unit by project type, with numerator and denominator.
2. Check the 25 comparison cities' ordinances, and the Wisconsin cities' (West Allis, La Crosse, Fitchburg, Franklin, Monona, Madison, Milwaukee).
3. Fetch the BPS place files for the other Census regions (Northeast, South, West) for the comparison test.
4. Find Wisconsin parking cost per space and typical minimums (spot checks only).
