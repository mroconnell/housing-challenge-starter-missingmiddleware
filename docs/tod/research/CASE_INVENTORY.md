# Transit-area upzonings with permits before and after: case inventory

Written 2026-10-26 for TOD Gate 2, work package 2. It answers owner decision AQ-047 item 1: the modelled law's height and density rules come from cities with permit data before and after a transit-area upzoning, keeping the strongest designs that are well measured. Research only: no permits were counted for this note. Scratch copies of sources are outside the repo.

The machine-readable version is [reference/tod_cases.csv](../../../reference/tod_cases.csv), one row per case. It has the same 58 cases in the same order, with every field and a `status` column that marks which values are observed and which are source leads.

**Labels used for every figure.**
- *observed*: read on an official government page, ordinance, open-data catalog or API, or in a peer-reviewed or working paper.
- *source_lead*: from news, advocacy, a secondary summary, or memory, or not yet confirmed. Use only as a pointer.
- *derived*: arithmetic done for this note.

**Ratings.**
- **Policy strength** is judged against the benchmark: a plain height or floor-area-ratio (FAR) increase, approved by right, with no affordability mandate. **Strong** means a large plain increase by right and no mandate. **Medium** means one shortfall: a modest increase, a discretionary path, a small or voluntary affordability string, or an opt-in. **Weak** means a bundled affordability mandate, an opt-in bonus, a plan without zoning, or rezoning case by case. Parking cuts do not lower the rating, because the owner wants them recorded and separated, not used to rank designs. They are flagged in their own column.
- **Data usability.** **A**: permit records with issue dates and unit counts are openly downloadable at parcel or address level, and the upzoned boundary is available as GIS. **B**: one of the two is missing or unconfirmed. **C**: a published study only, or neither.

**Market strength** is the city's median gross rent (dollars per month, renter-occupied units paying cash rent) and median home value (dollars, owner-occupied units), from the American Community Survey 2020 to 2024 5-year estimates, tables B25064 and B25077. These come from the files already in `data/raw/census_acs5_2024_tbsf_market` (observed). The national medians are $1,413 a month and $332,700. Madison is $1,413 and $372,900; Milwaukee is $1,059 and $184,000.

## Summary table

Ranked by data usability (A, then B, then C), then by policy strength. "Years before" counts full years of open unit-level permit data before the change year; "years after" counts full years from the change year to 2025. Rent is median gross rent in dollars a month.

| Rank | Case | Change year | Transit | What changed (typical) | Parking cut | Mandate | Path | Rent | Years before / after | Policy | Data |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Charlotte TOD Alignment Rezoning | 2019 | Light rail | 1,783 acres of mostly business and industrial land (about 40 ft) to 50 to 130 ft by right, no unit cap | Yes, minimums removed | No (voluntary bonus) | By right | 1,612 | 29 / 6 | Strong | A |
| 2 | New York Bloomberg-era upzonings (23 districts, pooled) | 2004 to 2013 | Subway | Capacity +20% or more; mean prior maximum FAR 1.375 | No | No (voluntary bonus in some) | By right | 1,821 | 4 to 13 / 12 to 21 | Strong | A |
| 3 | New York, Park Slope Fourth Avenue | 2003 | Subway | R6 (FAR 2.2 to 3.0) to R8A (FAR 6.02, 120 ft) | No | No | By right | 1,821 | 3 / 22 | Strong | A |
| 4 | New York, Downtown Brooklyn | 2004 | Subway hub | e.g. C6-1 (FAR 6.5) to C6-4 (up to 12) | No | No | By right | 1,821 | 4 / 21 | Strong | A |
| 5 | Saint Paul Green Line corridor | 2011 | Light rail | Commercial and industrial land without housing to T3 and T4 (FAR up to 3.0 or no maximum; 45 to 75 ft) | Yes, removed within ¼ mile | No | By right | 1,281 | 1 / 14 | Strong | A |
| 6 | Los Angeles Warner Center 2035 | 2013 | Bus rapid transit | About 960 acres; density limits removed; base FAR 4.5 in one district | Yes (reduced) | No | Mixed | 1,933 | 25 / 12 | Medium | A |
| 7 | Los Angeles Cornfield Arroyo Seco | 2013 | Light rail | About 650 acres of industrial land opened to housing | Yes, removed | No (bonus tied to affordable) | By right | 1,933 | 25 / 12 | Medium | A |
| 8 | Seattle North Beacon Hill and Othello | 2012 | Light rail | 12 and 29 acres rezoned; city capacity +617 and +304 units | Unknown | No (incentive) | By right | 2,030 | 6 / 13 | Medium | A |
| 9 | Seattle Mount Baker | 2014 | Light rail | 37 acres to 65 to 85 ft (two parcels 125 ft) | Unknown | No (incentive) | By right | 2,030 | 8 / 11 | Medium | A |
| 10 | Bellevue BelRed | 2009 | Light rail (opened 2024) | About 900 industrial acres; base FAR 1.0, to 4.0 with incentives | Unknown | No (bonus tied to affordable) | Mixed | 2,572 | 9 / 16 | Medium | A |
| 11 | Seattle Roosevelt | 2012 | Light rail | Small: capacity +79 units | Yes, optional | No (incentive) | By right | 2,030 | 6 / 13 | Weak | A |
| 12 | San Francisco Market and Octavia | 2008 | Subway | Density limits removed; FAR 6 to 9 in one district | Yes, removed | Yes (inclusionary plus fees) | Mixed | 2,476 | 27 / 17 | Weak | A |
| 13 | San Francisco Eastern Neighborhoods | 2008 | Partial rail | Industrial to mixed use | Yes | Yes | Mixed | 2,476 | 27 / 17 | Weak | A |
| 14 | Los Angeles TOC (existing) | 2017 | Rail and bus | Bonus 50% to 80% more units | Yes | Yes (8% to 25%) | Mostly by right | 1,933 | 29 / 8 | Weak | A |
| 15 | Los Angeles Expo Line plan | 2018 | Light rail | Bonus only with affordable units | Unknown | Yes | By right | 1,933 | 30 / 7 | Weak | A |
| 16 | Seattle U District | 2017 | Light rail | 65 to 85 ft to 85 to 320 ft | Unknown | Yes (MHA) | By right | 2,030 | 11 / 8 | Weak | A |
| 17 | Seattle MHA (existing) | 2017, 2019 | Mixed | One zoning step up in 33 areas | No | Yes | By right | 2,030 | 11 / 8 | Weak | A |
| 18 | New York de Blasio rezonings | 2016 to 2021 | Subway | Higher FAR with mandatory inclusionary | Some | Yes (20% to 30%) | By right | 1,821 | 16 / 9 | Weak | A |
| 19 | Kansas City Main Corridor Overlay | 2018 | Streetcar | Height bands, density left to base zoning | No | No | By right | 1,238 | 38 / 7 | Weak | A |
| 20 | Minneapolis 2040 (existing) | 2020 | Citywide | Triplexes, taller corridors | Yes | Yes | By right | 1,371 | 10 / 5 | Weak | A |
| 21 | Ann Arbor TC1 | 2021 to 2024 | Bus corridors | FAR 0.75 or 2.0 to no FAR limit, 120 ft | Yes, removed | No | By right | 1,649 | 17 / 3 | Strong | B |
| 22 | Ottawa TD zone | 2012 | Light rail | 20 to 90 m heights, minimum densities | Unknown | No | By right | n/a | 1 / 13 | Strong | B |
| 23 | Auckland Unitary Plan (existing) | 2016 | Citywide | Single house to up to 5 storeys | Yes | No | By right | n/a | 26 / 9 | Strong | B |
| 24 | Madison TOD overlay (existing, in state) | 2023 | Bus rapid transit | More units and storeys as permitted uses | Yes, removed | No | By right | 1,413 | 8 / 2 | Medium | B |
| 25 | Chicago TOD 2013 and 2015 (existing) | 2013, 2015 | Rail | +0.5 to +1.0 FAR | Yes | No (for base bonus) | Mixed | 1,440 | 7 / 12 | Medium | B |
| 26 | Toronto Eglinton Connects | 2014 | Light rail | +1 to +3 storeys on 5.0 km of frontage | Yes, small | No | By right | n/a | 14 / 11 | Medium | B |
| 27 | Phoenix Walkable Urban Code | 2015 | Light rail | Transect districts by city rezoning | Unknown | No | Mixed | 1,582 | 0 / 10 | Medium | B |
| 28 | Philadelphia 2012 code | 2012 | Citywide | Many block faces upzoned | No | No | By right | 1,397 | 5 / 13 | Medium | B |
| 29 | Raleigh New Bern Avenue | 2024 | Bus rapid transit (not open) | 726 acres, up to 5 to 7 storeys | Unknown | No | By right | 1,572 | n/a / 1 | Medium | B |
| 30 | San Diego Complete Communities (existing) | 2020 | Transit priority areas | Opt-in FAR bonus | Yes | Yes | By right | 2,313 | 2 / 5 | Weak | B |
| 31 | Austin TOD districts | 2005 to 2009 | Commuter rail | Bonus height only with affordable units | Yes | Yes | Mixed | 1,729 | 25 / 20 | Weak | B |
| 32 | Denver 38th and Blake | 2018 | Commuter rail | 8 storeys base, 16 with affordable units | Yes, removed | Yes | Mixed | 1,831 | 6 / 7 | Weak | B |
| 33 | Minneapolis Hiawatha station areas | 2008 to 2012 | Light rail | Industrial to mixed use | Unknown | No | By right | 1,371 | 0 / 17 | Weak | B |
| 34 | Montgomery County White Flint | 2010 | Heavy rail | Up to FAR 4.0 near Metro | Unknown | Yes (12.5%) | Discretionary | 2,068 | 10 / 15 | Weak | B |
| 35 | Cambridge Alewife | 2023 | Heavy rail | Housing-led mixed use | Unknown | Yes (20%) | Discretionary | 2,787 | 5 / 2 | Weak | B |
| 36 | Somerville 2019 code | 2019 | Rail | Form-based districts | Yes, removed | Yes (20%) | Mixed | 2,517 | 5 / 6 | Weak | B |
| 37 | Cincinnati form-based code | 2013 | Bus only | Form-based transects | Unknown | No | By right | 1,001 | 3 / 12 | Weak | B |
| 38 | Shoreline station subareas | 2015, 2016 | Light rail (opened 2024) | Single-family to 35 to 70 ft | Yes | Yes (10% to 20%) | By right | 1,985 | 25 / 10 | Weak | B |
| 39 | Portland Central City 2035 | 2018 | Light rail, streetcar | Higher FAR and heights | Yes | Yes | By right | 1,655 | 23 / 7 | Weak | B |
| 40 | São Paulo transit axes (existing) | 2016 | Rail and bus | Maximum built-area ratio to 4.0 | Yes | No (fee) | By right | n/a | n/a / 9 | Strong | C |
| 41 | New Rochelle Downtown Overlay Zone | 2015 | Commuter rail | Form-based, by right (lead) | Unknown | Unknown | By right | n/a | n/a / 10 | Strong | C |
| 42 | Salt Lake City TSA district | 2010 | Light rail | Core 75 to 90 ft, no density cap | Yes | No | Mixed | 1,414 | n/a / 15 | Medium | C |
| 43 | Lower Hutt plan changes | 2020 | Centres, partly rail | 2 storeys to 10 to 12 m | Yes, abolished | No | By right | n/a | 29 / 6 | Medium | C |
| 44 | Zurich canton (existing) | 1995 to 2020 | Not transit | Municipal FAR increases | Unknown | No | By right | n/a | n/a | Medium | C |
| 45 | MBTA Communities (existing) | 2023 to 2025 | Rail and bus | 15 units per acre average | No | No | By right | n/a | n/a / 2 | Medium | C |
| 46 | Milpitas Transit Area Specific Plan | 2008 | Light rail, BART | About 7,100-unit capacity on industrial land | Unknown | Unknown | Unknown | 3,120 | n/a / 17 | Medium | C |
| 47 | Bloomington (MN) HX-R | 2006, 2015 | Light rail | Minimum FAR 1.5, housing required | Unknown | No | By right | 1,561 | n/a / 19 | Medium | C |
| 48 | Jersey City Journal Square | 2010 | PATH rail | High-rise plan with bonuses | Yes | Yes | Mixed | 2,007 | n/a / 15 | Medium | C |
| 49 | Vancouver Broadway (existing) | 2022 | Subway | Large heights by rezoning | Unknown | Yes | Discretionary | n/a | 5 / 3 | Weak | C |
| 50 | Vancouver Cambie Corridor | 2011, 2018 | Rapid transit | Plan, then rezoning case by case | Unknown | Yes | Discretionary | n/a | 0 / 14 | Weak | C |
| 51 | Massachusetts 40R transit districts | 2006 to 2015 | Rail | 20 units per acre as of right | Unknown | Yes (20%) | By right | 1,641 | n/a | Weak | C |
| 52 | San Jose Urban Villages | 2011 | Rail and bus | Plan, often no zoning change | No | No | Discretionary | 2,669 | n/a / 14 | Weak | C |
| 53 | Brisbane densification areas | 2000 to 2020 | Some busway and rail | Capacity 0.9 to 1.4 times existing homes | Unknown | No | Mixed | n/a | n/a | Weak | C |
| 54 | Tysons (Fairfax County) | 2010 | Heavy rail | Rezoning per site | Unknown | Yes (20%) | Discretionary | 2,276 | n/a / 15 | Weak | C |
| 55 | Atlanta BeltLine overlay | 2007 | Trail, planned transit | Mainly design rules | Unknown | Yes (since 2018) | Mixed | 1,711 | n/a / 18 | Weak | C |
| 56 | Indianapolis TOD overlay | 2021 | Bus rapid transit | Mainly design rules | Unknown | No | By right | 1,156 | n/a / 4 | Weak | C |
| 57 | Oakland Broadway Valdez | 2014 | BART nearby | 95-acre specific plan | Yes | Yes (fee) | Mixed | 1,979 | n/a / 11 | Weak | C |
| 58 | Pittsburgh Uptown | 2019 | Bus rapid transit | 60 ft base to 180 ft by points | Unknown | No (points) | Mixed | 1,261 | n/a / 6 | Weak | C |

**Counts (derived from the table).** 20 cases rate A, 19 rate B and 19 rate C, out of 58. 14 of the 58 were already in [PRODUCTION_EVIDENCE.md](PRODUCTION_EVIDENCE.md); 44 are new. Among the 20 A cases, 5 are strong, 5 medium and 10 weak. Only 3 cases are strong, by right, without a mandate, and also have a published permit or unit outcome: the New York Bloomberg-era pool (Liao), Auckland and São Paulo. Charlotte and Saint Paul are strong with A data but have no study yet, so their effect would be our own estimate.

## What this means for Gate 3

1. **There are enough A-rated, strong cases to apply the owner's "drop the weaker designs" rule.** Five strong A cases come from three cities (Charlotte, New York, Saint Paul), with five medium A cases behind them. The weak A cases are almost all weak because of an affordability mandate (San Francisco, Los Angeles TOC and Expo, Seattle MHA and U District, New York after 2016). They make a ready mandate contrast but should not set the law's design.
2. **Two strong designs stand out.**
   - **Charlotte 2019** is the closest US match to the benchmark and to the proposed law. It was a city-initiated rezoning of 1,782.83 acres in 1,564 parcels around 20 light-rail stations (observed). Mostly business and industrial land went to by-right heights of 50 to 130 feet with no density cap, and no affordability requirement except a voluntary bonus for extra height. The county permit file has 482,250 permits with issue dates and unit counts from 1990 to 2026 (observed). The city's rezoning layer gives each polygon's zoning before and after. The confound is that parking minimums were removed at the same time.
   - **New York 2003 to 2013** gives the cleanest dose: plain FAR increases by right (for example Fourth Avenue, FAR 2.2 to 3.0 raised to 6.02), with parking minimums left in place, so no parking confound. Liao's parcel study already finds units on upzoned parcels up 4% after seven years, and up 7.9% where capacity rose by more than half (observed, working paper). The drawback is that New York's market and building types are far from Wisconsin's.
3. **Saint Paul 2011 is the best Midwest analogue to Wisconsin.** Its rent ($1,281 a month) is closer to Madison's ($1,413) than any other strong case, and the city keeps 39 zoning snapshots from 2007 to 2026 (observed). Its weakness is only two pre-years of unit-level permits (2010 and 2011) and the same parking confound as Charlotte.
4. **Recommended case set for Gate 3.**
   - **Fit the response rate on:** Charlotte 2019, the New York Bloomberg-era pool (with Fourth Avenue and Downtown Brooklyn as named members), and Saint Paul 2011.
   - **Medium-design comparison (to test whether dropping them changes the answer):** Los Angeles Warner Center 2013, Bellevue BelRed 2009, Seattle North Beacon Hill and Othello 2012, and Seattle Mount Baker 2014.
   - **Hold out:** Madison 2023 as the in-state test, and Chicago 2013 and 2015 as the Midwest fallback, as AQ-047 item 4 already decides. Ann Arbor TC1 is a third hold-out if its permit archive turns out to have unit counts, because it is the plainest by-right design on bus corridors, which is what most Wisconsin coverage is.
   - **Mandate contrast only:** Los Angeles TOC, Seattle MHA, San Francisco Market and Octavia, New York 2016 to 2021.
   - **Upper bound, not fitted:** Auckland and São Paulo, as the packet already plans.
   - **Parking separation.** Charlotte and Saint Paul removed parking minimums; New York, Chicago (2013 base) and Kansas City did not. Comparing the two groups on the same per-acre, per-added-FAR rate is the only internal way to see whether the parking cut drove the result. The parking scenario's own finding (no measurable average rise in permits in the 3 years after a repeal, across 24 US places) suggests it did not.
5. **Added FAR is the main gap.** Only New York (from yearly PLUTO maximum FAR from 2002) and Bellevue (base FAR from 0 to 1.0) give added FAR directly. Charlotte needs the pre-2019 base-district FAR tables; Saint Paul needs the pre-2011 B and I district limits. Both are code lookups, not new data.

## Spillover question: how many of the state's large cities had adopted

The owner asked, for each case, how many of its state's cities of 50,000 or more people had adopted a transit-area upzoning in the change year and each later year, and what share of the state's large-city population they held. The CSV gives the full series by year for every US case. Large cities and their populations are from the Census Bureau's Vintage 2024 city estimates, April 2020 base, incorporated places of 50,000 or more (observed; fetched to scratch from https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/cities/totals/sub-est2024.csv). The list of which cities adopted, and when, is a source lead built from the five research passes, so every count is source_lead. Using 2020 populations for earlier years is a simplification.

| Case | State | Change year | Large cities adopted (of all large cities) | Share of large-city population |
|---|---|---|---|---|
| Charlotte 2019 | North Carolina | 2019 | 1 of 21 (Raleigh joins in 2024: 2 of 21) | 24.1%, then 36.9% from 2024 |
| New York 2003 | New York | 2003 | 1 of 13 (New Rochelle joins 2015: 2 of 13) | 86.2%, then 87.0% |
| Saint Paul 2011 | Minnesota | 2011 | 3 of 20 (Brooklyn Park joins 2018: 4 of 20) | 40.8%, then 45.1% |
| Los Angeles Warner Center 2013 | California | 2013 | 6 of 181, rising to 11 of 181 by 2019 | 20.5%, rising to 28.8% |
| Seattle North Beacon Hill 2012 | Washington | 2012 | 3 of 25, rising to 7 of 25 by 2022 | 32.3%, rising to 47.5% |
| Chicago 2013 | Illinois | 2013 | 1 of 30 | 53.0% |
| Kansas City 2018 | Missouri | 2018 | 2 of 13 | 45.4% |
| Ann Arbor 2022 | Michigan | 2022 | 2 of 24 | 12.1% |
| Madison 2023 | Wisconsin | 2023 | 1 of 12 | 17.2% |

Two cautions. First, a single very large city dominates the share in New York (86.2%) and Illinois (53.0%), so share and count tell different stories there. Second, the lists are surely incomplete for California and Washington, where many suburbs rezoned station areas. No multi-city database of transit-area upzonings by date was found. The closest, the UC Berkeley Othering and Belonging Institute's Zoning Reform Tracker (172 reform efforts in 114 municipalities, 2007 to 2026), has no download and an "All rights reserved" licence (observed). A hand build will be needed if the spillover test goes ahead. Massachusetts towns all had to comply with MBTA Communities from 2023 to 2025, which is not counted in the series above.

## Case notes (new cases with A or B data)

### Charlotte TOD Alignment Rezoning, 2019
- **Reform.** Text amendment Petition 2018-169 created four transit districts (TOD-UC, TOD-NC, TOD-CC, TOD-TR), adopted 15 April 2019. City-initiated map rezoning Petition 2019-102 approved 18 November 2019 (observed). The districts carried into the Unified Development Ordinance on 1 June 2023 (source_lead).
- **Area.** 1,782.83 acres in 1,564 parcels along the LYNX Blue Line; uptown excluded. Prior zoning by acres: business 37.81%, industrial 36.75%, multifamily 9.45%, older transit districts 8.01%, office 5.42% (observed).
- **Heights after, by right:** TOD-UC 130 ft, TOD-NC 75 ft, TOD-CC 90 ft, TOD-TR 50 ft; capped at 65 ft within 200 ft of single-family zoning (observed). Before: about 40 ft in most base districts (source_lead).
- **Parking:** "No vehicle parking is required for any use in any TOD District," with maximums of 0.9 to 1.1 spaces per bedroom (observed).
- **Data.** Mecklenburg County Building Permit Locations (482,250 records, issue dates 1990 to 2026, unit field filled in 481,672 records; observed via Hub metadata). The server blocks scripted queries, so Gate 2 may need the Hub download. City Rezoning History layer, 360 polygons for this petition (observed).
- **To do before Gate 3:** decide whether to drop the 8.01% of acres already zoned for transit; find pre-2019 base-district FAR.

### New York City upzonings, 2003 to 2013
- Liao (2026, *Regional Science and Urban Economics* 117, 104188; working paper at https://papers.hsilingliao.com/Upzoning_Liao_JMP.pdf) lists 23 city-initiated upzonings from 2004 to 2013, defined as a rise of 20% or more in aggregate residential capacity (observed). Upzoned parcels: 21,242. Mean maximum FAR before: 1.375 on upzoned parcels against 1.755 in the 1,000 ft control ring (observed).
- **Results (observed, working paper):** total residential units on the parcel +4% seven years after upzoning; +2.6% where capacity rose up to 50%; +7.9% where it rose more than 50%. 47% of heavily upzoned parcels received a new-building, alteration or demolition permit, against 25% of control parcels (shares of parcels).
- **Fourth Avenue, Park Slope (adopted 30 April 2003):** 39 blockfronts from R6 and R7A to R8A, FAR 6.02 and 120 ft, with no affordability condition on the 2003 portion (observed in the City Planning plan document). Over 70% of the wider 110-block rezoning was contextual downzoning, so treatment must be limited to the R8A blockfronts (observed).
- **Data.** Department of Buildings job filings with proposed and existing dwelling units from 2000 (observed); City Planning Housing Database with net units from 2010 (observed); zoning map amendments with effective dates and PLUTO archives from 2002 (observed). Only 3 to 4 pre-years exist for the 2003 and 2004 rezonings.

### Saint Paul Green Line corridor, 2011
- The Central Corridor Zoning Study created the T4 and IT districts and rezoned University Avenue to T1 to T4; the City Council adopted it in April 2011 (observed). The city's zoning archive shows T4 first in the November 2012 snapshot, so the effective map date needs checking against the ordinance (observed discrepancy).
- Before, "most of the area within a block or two of the corridor did not allow residential uses" (observed, Metropolitan Council case study). After: T3 45 to 55 ft and FAR 0.5 to 3.0; T4 75 ft with no maximum FAR (observed). Parking minimums were removed within ¼ mile of stations (observed).
- Data: Housing Production layer with parcel ID, permit issue date and new dwelling units, 1,413 projects, 2010 to 2025 (observed). Example citywide totals: 184 new units permitted in 2010, 180 in 2011 and 1,273 in 2012 (counts, derived from the layer by the research worker).
- Study: Cao and Porter-Nelson (2016, *Transport Policy* 51) find the light-rail funding agreement associated with about 24% more permits and 80% more permit value in the corridor than in control corridors (observed abstract). This is the rail effect, not the rezoning alone.

### Los Angeles Warner Center 2035, 2013
- Ordinance 182,766, effective 25 December 2013 (ordinance observed; date source_lead). About 960 acres served by the Metro G Line bus rapid transit, which makes it the closest A-rated match to Wisconsin's bus-based coverage. Residential density limits removed (source_lead). Los Angeles publishes permits from 1988 with a dwelling-unit change field and annual zoning snapshots from 2003 (observed).

### Seattle station-area rezones, 2012 to 2014
- North Beacon Hill (85 parcels on 12 acres) and Othello (29 acres) were rezoned on 2 April 2012, after the stations opened in 2009 (observed). City capacity estimates rose from 677 to 1,294 units and from 6,046 to 6,350 units (observed). Mount Baker (81 parcels on about 37 acres) followed in June 2014 (source_lead).
- Seattle's permit file has units added and removed, issue dates and the zoning at permit, from 2006, Public Domain (observed). There is no historical zoning layer, so boundaries must be rebuilt from ordinance maps.

### Bellevue BelRed, 2009
- About 900 acres of light-industrial land rezoned around three future light-rail nodes; residential FAR 0.75 to 4.0 and heights up to 150 ft in nodes (observed). Extra floor area is earned mainly through affordable housing or a fee (observed), so this is medium, not strong. By June 2016, nearly 1,700 housing units had been issued or were pending, 94 of them affordable (observed, city report). Bellevue's permit service has a subarea field from 2000, but unit counts repeat across permits and must be de-duplicated (observed).

### Ann Arbor TC1, 2021 to 2024
- ORD-21-19 created the district (effective 25 July 2021); map rezonings followed in April 2022, November 2022, about 2023 and September 2024 (observed). Before: FAR 0.75 or 2.0 and heights 35 to 55 ft. After: no FAR limit and 120 ft (observed). About 819 acres are now zoned TC1 (observed). No parking minimum and no mandate. Permit data with units is not confirmed, and only 3 post-years exist, so B.

### Ottawa TD zone, 2012, and Toronto Eglinton Connects, 2014
- Ottawa By-law 2012-406 created TD zones of 20, 60 and 90 m around light-rail stations with minimum densities of 150 to 350 units per hectare (observed). Ottawa permit files with unit counts start July 2011, giving only about 16 months before (observed).
- Toronto's 2014 Eglinton rezoning raised heights by 1 to 3 storeys on 5.0 km of frontage (26% of the corridor) and removed density limits (observed). Toronto permits with dwelling units created are open from 2000 under the Open Government Licence (observed). The boundary must be rebuilt from the address list in the 2014 notice.

### Other B cases
- **Philadelphia 2012:** an Urban Institute study (Su, Curran-Groome and Freemark 2026) reports +0.17 permitted units per upzoned block face per year at the 2021 peak, about 4,000 extra permitted units that year (source_lead; urban.org blocks automated access). The city permit file's unit field is nearly empty before about 2018 (observed by query), so this is not transit-specific and hard to replicate.
- **Austin, Denver, Shoreline, Somerville, Cambridge, Portland Central City:** good permit data but weak designs (affordability strings), or too new.

## Cases screened out, with reasons

- **Milwaukee:** no transit-area upzoning found near the Hop streetcar or CONNECT 1 (source_lead, absence after search). Its historical property file (1975 to 2025, CC BY) is still useful for the Wisconsin baseline.
- **Too new for 3 post-years:** Raleigh New Bern (2024), Cambridge Alewife (2023), Kitchener (2024), Cincinnati Connected Communities (2024), Columbus Zone In (2024 to 2025), Edmonton (2024), New South Wales transport-oriented development program (2024), Auckland walkable catchments (not yet operative).
- **Design rules, plans or parking only:** Indianapolis 2021, Cleveland 2023, Detroit 2019, Evanston, Grand Rapids, Kansas City's 2017 TOD policy, New Jersey Transit Villages, San Jose Urban Villages, Toronto station-area plans (2022), Melbourne's 2014 zones, Tokyo's 2002 urban renaissance areas, Seoul's station-area youth housing.
- **No unit-level permits found:** Montgomery County, Tysons, Arlington, Washington DC, Jersey City, Prince George's County, Salt Lake City (unconfirmed), Milpitas, Atlanta.

## Further studies found (beyond PRODUCTION_EVIDENCE.md)

| Study | Setting | Method | Result | Status |
|---|---|---|---|---|
| Liao (2026), RSUE 117 | New York, 23 upzonings 2004 to 2013 | Parcel difference-in-differences | Units +4% after 7 years; +7.9% where capacity rose over 50% | Observed |
| Su, Curran-Groome and Freemark (2026), Urban Institute | New York (7 rezonings, mandatory inclusionary) and Philadelphia 2012 | Matched difference-in-differences | New York about +1.1 completed units per upzoned parcel after 4 years (about 4,100 in total); Philadelphia +0.17 permitted units per block face per year at 2021 peak | Source lead |
| Tanrisever (2026, job market paper) | Los Angeles TOC | Parcel event study | +0.06 units per parcel by 2021, about +2% on a mean of 2.6 units per parcel | Observed |
| Maltman and Greenaway-McGrevy (2024 working paper; 2025 Journal of Housing Economics) | Lower Hutt, New Zealand | Synthetic control | Consents per person up 3 to 4 times; about 3,260 extra units consented 2018 to 2023, 66% of the 4,867 issued | Observed (working paper) |
| Gabbe, Kevane and Sundstrom (2021), RSUE 88 | San Jose Urban Villages | Treated versus comparison parcels | Effects on permits not distinguishable from zero | Observed |
| Cao and Porter-Nelson (2016), Transport Policy 51 | Saint Paul Green Line | Difference-in-differences on permits | About +24% permit count after the federal funding agreement (rail, not zoning) | Observed abstract |
| Limb and Murray (working paper) | Brisbane, 19 areas, 25,775 sites | Site panel | About 2% of zoned capacity taken up per interval; 78% of sites with capacity undeveloped | Observed |
| Dong (2024), JPER 44(1) | Portland parcels upzoned 2000 to 2017 | Propensity matching | Upzoned parcels produced about 3 times the units of controls, but only 5.1% developed | Source lead |
| Goetz et al. (2010), CTS 10-09 | Minneapolis Hiawatha line | Hedonic and land-use comparison | About +4.2% single-family prices west of the line; no detected land-use change | Source lead |
| Atkinson-Palombo and Kuby (2011), J Transport Geography 19(2) | Phoenix light rail, 2000 to 2007 | Descriptive typology | About $1 billion of pre-opening development; overlays used most in low-income station areas | Source lead |

## Sources

Official and data sources (observed unless marked):
- Charlotte Petition 2018-169: https://ww.charmeck.org/Planning/Rezoning/2018/153-169/2018-169%20Approved%20Transit%20Oriented%20Development%20Regulations.pdf
- Charlotte Petition 2019-102 staff analysis: https://ww.charmeck.org/planning/rezoning/2019/086-104/2019-102%20staff%20analysis%20final.pdf
- Charlotte Rezoning History layer: https://gis.charlottenc.gov/arcgis/rest/services/PLN/RezoningHistory/MapServer/0
- Mecklenburg County Building Permit Locations: https://hub.arcgis.com/datasets/fc9d171ecd4d44a58c7dad840cd58aa2_0
- New York DOB job filings: https://data.cityofnewyork.us/d/ic3t-wcy2 ; Housing Database: https://data.cityofnewyork.us/d/6umk-irkx ; zoning GIS: https://data.cityofnewyork.us/d/mm69-vrje ; PLUTO: https://data.cityofnewyork.us/d/64uk-42ks
- Park Slope rezoning: https://www.nyc.gov/assets/planning/download/pdf/plans/park-slope/parkslope.pdf
- Saint Paul Housing Production: https://services1.arcgis.com/9meaaHE3uiba0zr8/arcgis/rest/services/Housing_Production_Q3_2024/FeatureServer/73 ; zoning over time: https://services1.arcgis.com/9meaaHE3uiba0zr8/arcgis/rest/services/PrincipalZoning_OverTime/FeatureServer ; Metropolitan Council case study: https://metrocouncil.org/Communities/Planning/TOD/Files/Case-Study-St-Paul-Central-Corridor-Zoning.aspx
- Los Angeles permits: https://data.lacity.org/resource/e67z-kt2n.json (1988 to 2009), dyxf-7hc4 (2010 to 2019), pi9x-tg5x (2020 on); Zoning Archive: https://services5.arcgis.com/7nsPwEMP38bSkCjy/arcgis/rest/services/Zoning_Archive/FeatureServer
- Seattle permits: https://data.seattle.gov/Permitting/Building-Permits/76t5-zqzr ; station area overlay: https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services/Station_Area_Overlay_(light_rail)/FeatureServer/23 ; 2012 rezones: https://council.seattle.gov/2012/04/03/north-beacon-hill-and-othello-rezones/
- Bellevue permits: https://services1.arcgis.com/EYzEZbDhXZjURPbP/arcgis/rest/services/Bellevue_Permit/FeatureServer/0 ; BelRed: https://www.fhwa.dot.gov/ipd/value_capture/case_studies/belred_subarea_bellevue_washington_impact_fees.aspx
- San Francisco permits: https://data.sfgov.org/Housing-and-Buildings/Building-Permits/i98e-djp9 ; 2000 zoning: https://data.sfgov.org/d/prs8-k8k3 ; monitoring report: https://sfplanning.org/sites/default/files/documents/reports/momr_2015-2019.pdf
- Ann Arbor TC1 staff report: https://a2gov.org/media/lflhgfbr/staff-report-4-6-21-new-district-tc1.pdf ; zoning: https://services2.arcgis.com/cenCPuKxOZuq6BCE/arcgis/rest/services/Zoning/FeatureServer/0
- Kansas City permits: https://data.kcmo.org/d/ntw8-aacc
- Chicago permits: https://data.cityofchicago.org/d/ydr8-5enu
- Austin permits: https://data.austintexas.gov/Building-and-Development/Issued-Construction-Permits/3syk-w9eu
- Denver permits: https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/ArcGIS/rest/services/ODC_DEV_RESIDENTIALCONSTPERMIT_P/FeatureServer/316
- Salt Lake City Ordinance 59 of 2010: http://www.slcinfobase.com/Ord_by_Chron_2010-2019/Documents/ordinance59of2010.htm
- Toronto Eglinton staff report: https://www.toronto.ca/legdocs/mmis/2014/pg/bgrd/backgroundfile-72097.pdf ; permits: https://open.toronto.ca/dataset/building-permits-cleared-permits/
- Ottawa TD zone: https://documents.ottawa.ca/sites/default/files/zoning_bylaw_part10_section195-196_en.pdf
- Massachusetts 40R activity table (2017): https://www.winthropma.gov/DocumentCenter/View/601/40R-Districts-Activity-09-11-17-1-PDF
- Census Vintage 2024 city population estimates: https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/cities/totals/sub-est2024.csv
- ACS 2020 to 2024 5-year tables B25064 and B25077: the files in `data/raw/census_acs5_2024_tbsf_market` (URLs in its `_downloads.json`).
- UC Berkeley Zoning Reform Tracker: https://belonging.berkeley.edu/zoning-reform-tracker

Studies:
- Liao, H. (2026). The effect of rezoning on local housing supply and demand: Evidence from New York City. *Regional Science and Urban Economics* 117. https://doi.org/10.1016/j.regsciurbeco.2025.104188
- Su, Y., Curran-Groome, W., Freemark, Y. (2026). How Big Upzonings Affect Housing Supply. Urban Institute. https://www.urban.org/research/publication/how-big-upzonings-affect-housing-supply (source_lead; summary at https://nlihc.org/resource/upzoning-new-york-city-and-philadelphia-associated-meaningful-increases-housing-production)
- Tanrisever, I. (2026). Upzoning and Neighborhood Change: Evidence from Los Angeles. AEA 2026 program. https://www.aeaweb.org/conference/2026/program/paper/5D39BQyY
- Maltman, M., Greenaway-McGrevy, R. (2024). Going it Alone: The Impact of Upzoning on Housing Construction in Lower Hutt. EPC Working Paper 018. https://auckland.ac.nz/assets/business/our-research/docs/economic-policy-centre/EPC-WP-018-going-it-alone-the-impact-of-upzoning-on-housing-construction-in-lower-hutt.pdf
- Gabbe, C.J., Kevane, M., Sundstrom, W.A. (2021). The effects of an "urban village" planning and zoning strategy in San Jose, California. *Regional Science and Urban Economics* 88, 103648. https://doi.org/10.1016/j.regsciurbeco.2021.103648
- Cao, X., Porter-Nelson, D. (2016). Real estate development in anticipation of the Green Line light rail transit in St. Paul. *Transport Policy* 51, 24 to 32. Open report: https://cts-d10resmod-prd.oit.umn.edu/pdf/cts-15-09.pdf
- Limb, M., Murray, C. We zoned for density and got higher house prices. OSF working paper. https://doi.org/10.31219/osf.io/zkt7v
- Dong, H. (2024). Exploring the impacts of zoning and upzoning on housing development. *Journal of Planning Education and Research* 44(1). https://doi.org/10.1177/0739456X21990728
- Goetz, E. et al. (2010). The Hiawatha Line: Impacts on Land Use and Residential Housing Value. CTS 10-09. https://conservancy.umn.edu/bitstream/handle/11299/101325/CTS%2010-09.pdf
- Atkinson-Palombo, C., Kuby, M. (2011). The geography of advance transit-oriented development in metropolitan Phoenix, Arizona, 2000 to 2007. *Journal of Transport Geography* 19(2), 189 to 199.
- Thill, J.-C. et al. (2023). Economic Impacts of Transit Investments, Part II. NCDOT RP 2020-37. https://connect.ncdot.gov/projects/research/RNAProjDocs/RP%202020-37%20-%20Final%20Report%20-%20Part%20II.pdf
- Cases already in [PRODUCTION_EVIDENCE.md](PRODUCTION_EVIDENCE.md) keep their sources there.
