# Parking reforms: which are real, and what the evidence says (Gate 1)

Written 2026-10-26 by the parking conductor. Status: Gate 1 research, for owner review. Figures marked "source lead" come from abstracts or secondary write-ups and still need checking against the full source.

## Answer so far

- **A usable classification exists.** The Parking Reform Network (PRN) reform map is a database of 6,610 places, kept on GitHub under the MIT licence. Each record gives the reform's scope, the land uses it covers, its conditions, an adoption date and citations to the code. We rate every US record against the benchmark with a written rule (below). That rule found 231 US cities that removed minimums for all housing, by right. 47 of them did so in 2022 or earlier, so they have at least three years of permits since.
- **No state law can supply post-law evidence yet.** Every statewide law is transit-only, small-project-only, capped rather than removed, or ADU-only. None was adopted before 2022, and none has had three full years of permits since taking effect. The evidence will come from cities that repealed minimums citywide.
- **Wisconsin already has cities at the benchmark.** According to PRN, 9 Wisconsin places have removed minimums for all housing: West Allis (2022), La Crosse (2024), Fitchburg (2025), Franklin (2025), Cottage Grove (2026), Omro, Brodhead, Algoma and Gilman. Another 9 nearly meet the benchmark, for example DeForest (multifamily only) and the City of Pewaukee. A statewide law adds nothing in those places, and West Allis is an in-state before/after case. Madison and Milwaukee have only partial reforms: downtown and some districts, a 25% cut near bus stops in Milwaukee, and houses and ADUs exempt.
- **Developers keep building parking, but less of it.** Every study found builds less than the old minimum on average, with a wide spread. Some projects build none, and some build more than the old minimum. That spread is the benchmark's "developer-provided parking" assumption, and it becomes a range.

## 1. The classification rule

Source: PRN `data/core.json` and `data/extended.json`, pinned to commit 3a62231 (fetched 2026-10-26 by `scripts/build_parking_taxonomy.py`). Code: `missing_middleware/parking/taxonomy.py`. Output: `reference/parking_reform_taxonomy.csv` (all 6,318 US city, county and state records) and `reference/parking_reform_cases.csv` (cities at or near the benchmark).

| Rating | Rule | Example |
| --- | --- | --- |
| **at** | Minimums removed citywide (or statewide) for all uses or all housing, by right, with no other condition | Buffalo 2017, Minneapolis 2021, West Allis 2022 |
| **near** | Removed citywide for housing, but with a condition: a project-size limit, an ADU part, a historic or "other" carve-out, or multifamily only | Connecticut PA 25-1 (up to 16 units); DeForest (multifamily only) |
| **weaker** | Removed only near transit, downtown, on main streets or in parts of a region; only for affordable housing; reduced but not removed; or only for houses and ADUs | California AB 2097, Oregon CFEC, Colorado HB24-1304, Illinois, Florida, Maryland |
| **plan_only** | The summary describes a plan or report recommendation and no code change, whatever the record's status | Ponca City, OK, and Rolling Meadows, IL (status adopted); Milwaukee's 2025 comprehensive plan (status proposed) |
| **not_housing** | Does not touch residential uses | many commercial-only downtown exemptions |

Counts of US cities with an adopted record (a city can have several records; each city is counted once per rating): 231 at, 98 near, 4,031 weaker, 6 plan_only and 1,185 not_housing. The comparison cases use adopted records only.

**Why the text checks matter.** PRN's tags sometimes say more than the reform did. Two checks read the summary text. The first flags plans and reports that recommend a repeal but describe no code change. The second rates a record "weaker" when it is tagged for all housing but its summary exempts only one- and two-family homes. Before that check, Monona, WI was rated "at", although only its one- and two-family homes are exempt. Both checks are text heuristics. They can still be wrong either way: Rockingham, NC and Conway, SC remain rated "at", although their summaries exempt only detached houses citywide. Every case used as evidence will be checked against the ordinance text before Gate 2 (step 3).

**Dates.** PRN records one date, usually the adoption date. It has no date for 103 of the 231 cities at the benchmark. Effective dates are not in PRN and will be recorded from the ordinance for each case we use.

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

Cities rated **at**, adopted in 2022 or earlier, with population of 20,000 or more (26 cities, PRN populations): San Francisco (2018), Buffalo (2017), Hartford (2017), Norman OK (2021; required spaces became recommended), Mount Pleasant MI (2018), Dunwoody GA (2019), South Bend (2021), Minneapolis (2021), St. Paul (2021), Gastonia (2021), Roanoke (2021), Bridgeport (2021), Alameda (2021), Raleigh (2022), West Allis (2022), Ann Arbor (2022), Cambridge (2022), Culver City (2022), Central Falls (2022), Lexington (2022), Wilmington NC (2022), Anchorage (2022), Gainesville (2022), Corvallis (2022), San Jose (2022) and Tigard (2022). Each will be checked against the ordinance text (status, effective date, any later carve-outs), and against other reforms passed at the same time. Minneapolis's 2040 plan, for example, also upzoned, so its permits cannot be credited to parking alone.

The proposed test, to be pre-registered at Gate 2: permits by building size from the Census Building Permits Survey place files (public domain), for each case city and for comparison cities without reform matched on size, region and pre-reform permit trend. The outcome is units per 1,000 existing homes per year, by year since reform.

## 4. Developer-provided parking: evidence leads

| Case | Finding | Status |
| --- | --- | --- |
| Buffalo, 2017 citywide repeal (Hess and Rehler, *JAPA* 87(3), 2021; read in full) | 36 major developments approved April 2017 to April 2019 provided 1,942 parking spaces, against 2,444 under the old minimums: 79% of the old minimum, or 21% fewer. 17 of the 36 developments (47%) provided fewer spaces than the old minimum. The other 19 provided the same or more. **Mixed-use** projects (14 projects, 1,034 housing units) provided 726 spaces, against 1,539 required: 47% of the old minimum. **Residential-only** projects (14 projects, 566 units) provided 760 spaces, against 652 required: 117% of the old minimum of 1 space per unit, or 1.34 spaces per unit. In the 5 months before the repeal, 16 comparable projects provided 122% of the minimum. | observed (published table; article CC BY-NC-ND, cited, not redistributed) |
| Seattle, 2012 removal near frequent transit (Gabbe, Pierce and Clowers, *Land Use Policy* 2020) | About 18,000 fewer spaces were built over five years than the old rules required. The "40% fewer spaces" figure often quoted is not confirmed. | source lead |
| Minneapolis, 2015 transit cut | Median 0.82 spaces per unit in 2015–2017 new development, and 0.42 for 10–50 unit projects, where the old rule was about 1 per unit (Metropolitan Council case study) | source lead |
| Champaign, IL (Sohoni and Lee, 2023) | On-site parking built in deregulated zones fell about 60% | source lead |
| Denver (Terner Center / Rocky Mountain Land Use Institute, 2025) | Pro forma simulation, assuming developers choose 0.5 spaces per unit near light rail and 1.0 elsewhere: removing minimums raises market-rate multifamily output about 12.5%, or about 460 homes per year | source lead; a model, not an observation |
| Cost per space | Structured parking up to about $50,000 per space (Denver planning office, cited above) | source lead; Wisconsin costs to find |

**What this means for the model.** Removing a minimum matters only where it bound. In Buffalo it bound for mixed-use infill, which built under half the old minimum. It did not bind on average for stand-alone apartment buildings, which built 1.34 spaces per unit against a minimum of 1. Across the studies the pattern is the same: the minimum binds for about half of larger projects, more often for mixed-use, small-lot and transit-served infill, and rarely for single-family homes. The Denver study is the closest published example of the cost-times-supply-response method (method B in the [Gate 1 plan](GATE1_PLAN.md)). Its 12.5% for a much stronger market is an upper reference point for Wisconsin, not a value to borrow.

## 5. Next steps

1. Read the full Seattle (paywalled; look for an author copy) and Champaign papers and the Denver white paper; record spaces per unit by project type, with numerator and denominator.
2. Check the 26 comparison cities’ ordinances, and the Wisconsin places’ (the 18 rated at or near, plus Madison and Milwaukee).
3. Fetch the BPS place files for the other Census regions (Northeast, South, West) for the comparison test.
4. Find Wisconsin parking cost per space and typical minimums (spot checks only).

## 6. Places under 50,000 people: quick look (2026-10-26)

No published study measures housing after a repeal in a place under 50,000 people. A quick look, not pre-registered, compared 16 US repeal places of 5,000–50,000 people with same-state places of half to twice their population and no PRN reform record. The comparison covers the 5 years before adoption and the 3 years after, in units permitted per 1,000 residents (Census building permits).
- 7 of the 16 places rose faster than their comparison places, 8 rose slower, and 1 permitted nothing in either period.
- The median place's after/before ratio was 0.84 times its comparison places' ratio.
- Most of these places permit a few dozen homes a year, and most had no permits in buildings of 2+ units before or after.

The result is noise, not a signal. Script: `scripts/parking_small_places_quicklook.py`. Table: `reference/parking_small_places_quicklook.csv`.
