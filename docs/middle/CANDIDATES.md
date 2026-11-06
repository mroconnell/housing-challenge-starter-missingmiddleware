# Middle housing: candidate reforms and data check (step 1)

Prepared 2026-11-06 at Ryan's request. **Research only.** No modeling, no plan lock, and no tool change. Nothing here estimates any reform's effect. The row-level table is [`reference/middle_housing_candidates.csv`](../../reference/middle_housing_candidates.csv).

**Status key:**
- **V (verified):** read on an official page (legislature, statute site, court, city or state agency, or a government data API).
- **S (source lead):** comes from news, a secondary source, or a search snippet. Some official sites blocked automated reads: leginfo.legislature.ca.gov, maine.gov, charlottenc.gov, durhamnc.gov and pew.org.

## What the handbook asks for

- **Reform:** allow 2–6 homes on lots now limited to one house.
- **Height:** up to 3 stories.
- **What counts:** townhouses and 2–6 unit buildings both count.
- **Lot rules:** setbacks and lot coverage may be assumed not to bind.
- **Results:** must add up to a statewide total over 5 years.
- **Bonus:** the rules score higher a method that also works in states with less complete data.

## What the ADU method needs from each candidate

From [CAUSAL_FRAMEWORK_PLAN.md](../adu/CAUSAL_FRAMEWORK_PLAN.md) and the pooled ADU model:

1. **Place-level counts each year.** Here that means permits by building size: 1 unit, 2 units, 3–4 units, 5+ units.
2. **Enough years.** For this check: at least 3 full years before the reform (the A4 feasibility rule), and at least 2 full years after it.
3. **A denominator.** Single-family homes per place. ACS 2020–2024 table B25024 (units in structure) is on disk for every US place.
4. **A comparison group.** Places with no reform in the same years: places below a law's size threshold, or places in states without such a law.
5. **A held-out test.** As in A3, enough treated states or cities that each can be hidden in turn.

**Data years used here:** Census data through 2025, the latest complete year.

## Main findings

- **Census permit counts cover every candidate.** The Census Building Permits Survey (BPS) reports permitted units by building size for about 20,000 places.
  - Annual place files for 2012–2025 are on disk (`data/raw/census_bps_place_us`).
  - Earlier years back to 1980 are free at the same Census site (checked 2026-11-06).
- **BPS misses part of the handbook's 2–6 range:**
  - It counts each townhouse as a 1-unit home.
  - It puts 5–6 unit buildings in "5+".
  - In California's progress reports, most SB 9 homes are filed as single-family homes or ADUs, not "2 to 4". In 2025, the progress reports flag 1,308 permitted units as "SB 9 duplex in a single-family zone". 785 of them are filed as detached single-family homes and 433 as "2 to 4".
  - Portland's city permits show the same pattern. In 2022–2025 its new-construction permits list 1,574 townhouse and rowhouse units against 152 units in 2–4 unit buildings.
  - So each candidate needs a second count that includes townhouses (city or state records), or a stated adjustment.
- **Washington has the best state data.** OFM's city file (`data/raw/statewide_states/wa/ofm_april1_postcensal_permits_1990-present.xlsx`) gives permits, completions and demolitions for 1-unit, duplex, 3–4 and 5+ buildings and ADUs, for every city and town plus each county's unincorporated area, 1990–2026.
  - OFM year 2026 runs from April 2025 to April 2026.
- **California is next.** HCD's progress report Table A2 (2018–2025, on disk) has "2 to 4", "5+", "single-family attached" (SFA) and ADU categories with coordinates, by jurisdiction.
  - It flags SB 9 projects in `APPROVE_SB35`. The flag covers 2022 (16 units) through 2025, but the form only added it with the 2023 report.
- **Four cities publish strong permit records** with a units field and a building type going back well before their reform: Austin, Raleigh, Charlotte (Mecklenburg County) and Portland (in repo).

## Verdicts

| Candidate | Reform in force (first full year) | Years before (on disk / free) | Full years after (to 2025) | Comparison group | Townhouse count available | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| **Oregon HB 2001** | 2021-06-30 mid cities; 2022-06-30 large cities and Metro (2023) | 2012–2019 / 1980+ | 3 large (2023–25); 4 mid | Yes: cities under 10,000; non-law states | Portland only (in repo) | **Usable** |
| **California SB 9** | 2022-01-01 (2022) | BPS 2012–2021; progress reports 2018–2021 | 4 (2022–25) | Out of state only (every single-family zone treated) | Yes: SFA category plus SB 9 flag | **Usable** |
| **Washington HB 1110** | 2025-06-30 King, Pierce, Snohomish and Kitsap cities; 2025-12-31 next group; 2026-12-31 Spokane group | OFM 1990–2024 | 0–1 | Yes: cities under 25,000; later groups | No (OFM has no townhouse split) | **Not yet.** Re-check with OFM 2027–2028 |
| **Maine LD 2003** | 2024-01-01 council towns; 2024-07-01 town-meeting towns (2024 / 2025) | 2012–2023 | 2 (council towns); 1 (others) | Out of state only (all towns treated) | No | **Borderline:** just meets 2 years |
| **Montana SB 323** | Enjoined 2023-12-29; in force 2024-09-03 (2025) | 2012–2023 | 1 | Yes: cities under 5,000 | No | **Not yet.** 2026 data due spring 2027 |
| Vermont Act 47 (not on Ryan's list) | 2023-07-01 (2024) | 2012–2022 | 2 | Partial: towns without water and sewer | No | Borderline |
| Arizona HB 2721 (not on list) | 2026-01-01 | — | 0 | — | — | Not yet |
| **Minneapolis 2040 plan** | 2020-01-01 (2020) | BPS 2012–2019; city permits from 2016-12 | 6, but a court injunction ran June 2022 to May 2024 | Yes: other Twin Cities places (BPS) | City permits (units field), from 2016-12 | **Usable, with the injunction years flagged** |
| **Austin HOME** | Phase 1 2024-02-05; Phase 2 2024-08-16 (2025) | City 1921+ | 1 | Yes: other Texas places | Yes: classes 101–105 with units, public domain | **Not yet** for the method; data excellent |
| **Houston lot size** | 1998 inside Loop 610; 2013-05-24 citywide, phased in 2014–2015 | BPS 1980+ | Many | Yes: other Texas places | No open permit records | **Not usable here:** its homes are small-lot single-family, which BPS counts as 1-unit |
| **Durham EHC** | 2019-10-01 (2020) | BPS 2012–2018, but Census filled in 2016–2018 (8, 3 and 0 of 12 months reported) | 6 (2023–25 partly filled in) | Yes: other NC places | City table 2007-10 to 2024-02, ODbL 1.0 licence | **Borderline:** gaps in reported years; licence question |
| **Raleigh missing middle** | TC-5-20 adopted 2021-07-06; TC-20-21 in force 2022-08-08 (2022) | BPS 2012–2020; city 2000+ | 4 | Yes: other NC places | Yes: units, building type and a "missing middle" flag | **Usable** |
| **Walla Walla** | Ord. 2018-53, 2019-01-02 (2019) | OFM 1990–2018 | 7 | Yes: other Washington cities (OFM) | No | **Usable, but small:** 0–64 duplex units a year |
| **Spokane** | Interim Ord. C36232, about August 2022 (2023); permanent C36459, 2024-01-01 | OFM 1990–2022 | 3 (OFM adds 2026) | Yes: other Washington cities | No | **Usable.** Use OFM: Census filled in Spokane's 2018, 2020 and 2021 |
| **Charlotte UDO** | 2023-06-01 (2024) | County permits 1990+ | 2 | Yes: other NC places | Yes: Census building codes incl. townhouse (102) | **Borderline:** 2 years; BPS covers the whole county only |
| **Sacramento** | General Plan 2024-03-28; interim ordinance adopted 2024-09-17 (2025) | Progress reports 2018+; city permits 2016+ | 1 | Partial: other California places (all under SB 9) | Yes: progress reports | **Not yet** |
| **Arlington VA EHO** | 2023-07-01; voided 2024-09-27; reopened 2025-10-01 | BPS 2012–2022 | under 1 in force | Yes | No | **Not usable now:** 45 permits (186 units), court case open, and BPS puts its 5–6 unit buildings in "5+" |
| Auckland (optional) | Unitary Plan, 2016-11-15 (2017) | Stats NZ consents (not checked) | 9 | Published study compares upzoned and other areas | Stats NZ has a townhouse type (not checked) | **Outside evidence only**; not a US state |
| Portland RIP (extra) | 2021-08-01 (2022) | City permits 1995+ (in repo) | 4 | Yes: other Oregon places | Yes (in repo) | Usable, but also inside Oregon HB 2001 |

**Count of usable candidates now:** 2 state laws (Oregon, California) and 5 cities (Minneapolis, Raleigh, Walla Walla, Spokane, Portland). Borderline: Maine, Vermont, Durham, Charlotte.

## Reform dates and sources

### State laws

| Law | Signed | Effective / binds | Units allowed | Status | Source |
| --- | --- | --- | --- | --- | --- |
| Oregon HB 2001 (Or Laws 2019 ch 639); now ORS 197A.420 (formerly 197.758) | 2019-08-08 | Effective 2019-08-08. Cities 10,000–25,000 (duplexes): 2021-06-30. Cities 25,000+ and Metro: 2022-06-30 | Duplex; 2–4 units, cottage clusters and townhouses in large cities | V | oregonlegislature.gov/bills_laws/lawsstatutes/2019orlaw0639.pdf; ors197A.html |
| OAR 660-046 (state model code) | — | Medium cities 2020-08-03; large cities 2020-12-31 | — | S | oregon.gov/lcd |
| California SB 9 (Stats. 2021 ch 162); Gov. Code 65852.21, 66411.7 | 2021-09-16 | 2022-01-01 | 2 units per lot plus a lot split: up to 4 homes | V | gov.ca.gov press release 2021-09-16; HCD SB 9 fact sheet (April 2026) |
| California SB 450 (2024 ch 286); AB 1061 (2025) | 2024-09-19 | 2025-01-01 (SB 450) | Removes some local limits; AB 1061 covers historic districts | S; V (AB 1061) | HCD fact sheet |
| Washington HB 1110 (Laws 2023 ch 332); RCW 36.70A.635 | 2023-05-08 | Effective 2023-07-23. SSB 5558 (2025 ch 148, effective 2025-07-27) moved compliance to the plan update itself: 2025-06-30 (King, Pierce, Snohomish, Kitsap), 2025-12-31 (Clark, Thurston, Whatcom and 7 others), 2026-12-31 (Spokane, Walla Walla, Yakima and 7 others), 2027-06-30 (15 small counties) | 4 per lot in cities 75,000+ (6 near transit); 2 in cities 25,000–75,000 (4 near transit) | V (laws); S (date reading) | lawfilesext.leg.wa.gov; app.leg.wa.gov RCW 36.70A.635 and .130 |
| Maine LD 2003 (PL 2021 c 672); 30-A M.R.S. 4364-A | 2022-04-27 | Delayed by PL 2023 c 192 to 2024-01-01 (council towns) and 2024-07-01 (town-meeting towns) | 2 per lot; 4 in growth areas | V (signed); S (delay dates) | mainelegislature.org |
| Maine LD 1829 (PL 2025 c 385); LD 2173 (PL 2026 c 733) | 2025-06-20; 2026-04-16 | 2026-07-01 / 2027-07-01 | 3 per lot, counting ADUs | V | mainelegislature.org |
| Montana SB 323 (2023); MCA 76-2-304(3) | 2023-05-04 (S) | 2024-01-01; enjoined 2023-12-29; injunction lifted 2024-09-03 (2024 MT 200); upheld by the state Supreme Court about 2026-03-17 (S) | Duplex on single-family lots in cities 5,000+ | V (injunction scope); S (dates) | archive.legmt.gov; Governor's release |
| Vermont Act 47 of 2023; 24 V.S.A. 4412(1)(D) | 2023-06-05 | 2023-07-01 | Duplex wherever housing is allowed; up to 4 with water and sewer | V | outside.vermont.gov |
| Arizona HB 2721 (2024); A.R.S. 9-462.13 | 2024-05-21 (S) | Cities must comply by 2026-01-01 | 2–4 units and townhomes near downtown in cities 75,000+ | V | azleg.gov |

**Correction to the October inventory:** the Arizona section is 9-462.13, not 9-462.10, and Washington compliance is now at the plan update, not six months after.

### Cities

| City | Reform | Adopted | In force | Allows | Later events | Status | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minneapolis | 2040 plan plus triplex zoning (file 2019-00217) | Plan 2019-10-25; zoning 2019-11-08 | 2020-01-01 | Up to 3 units per lot | Court injunction June 2022; reversed 2024-05-13; state fix signed 2024-05-24 (2024 Minn. Laws ch 127) | S (dates); V (state law) | minneapolis2040.com; revisor.mn.gov |
| Austin | HOME Phase 1, Ord. 20231207-001 | 2023-12-07 | Applications from 2024-02-05 | 3 units per lot | — | V | austintexas.gov |
| Austin | HOME Phase 2, Ord. 20240516-006 | 2024-05-16 | 2024-08-16; whole city 2024-11-16 | Minimum lot 1,800 sq ft | — | V | austintexas.gov |
| Houston | Chapter 42 rewrite | 1998 | Not found | 1,400 sq ft lots inside Loop 610 | 2013 amendment in force 2013-05-24; phased in 2014-04-24 and 2015-04-24 | S (1998); V (2013) | houstontx.gov |
| Durham | Expanding Housing Choices, TC1800007 | September 2019 | 2019-10-01 | Duplexes, small and flag lots in the urban tier | Final report Oct 2023 | S | durhamnc.gov (blocked) |
| Raleigh | TC-5-20; TC-20-21 | 2021-07-06; 2022-05-10 | TC-5-20 not found; TC-20-21 2022-08-08 | Duplexes in most residential zones; townhouses; 3-unit buildings on small lots | — | S / V | raleighnc.gov |
| Walla Walla | Ord. 2018-53 | 2018-12-19 | 2019-01-02 | Up to 4 units per lot; no minimum lot size | — | V (number); S (dates) | wallawallawa.gov |
| Spokane | Interim C36232; permanent C36459 | 2022-07-18; 2023-11-20 | About August 2022; 2024-01-01 | Duplex to fourplex, townhouses; no density cap on lots under 2 acres | Interim rules expired 2023-12-18 | V | my.spokanecity.org |
| Charlotte | Unified Development Ordinance | 2022-08-22 | 2023-06-01 | Duplex and triplex on N1 lots | Corner-lot triplex limit, possibly adopted 2026-03-23 (unconfirmed) | S | charlottenc.gov (blocked) |
| Sacramento | 2040 General Plan; interim ordinance ORD2024-0027 | 2024-02-27; 2024-09-17 | 2024-03-28; interim date unconfirmed | No unit cap; size set by floor-area ratio | Permanent ordinance in drafting | S | cityofsacramento.gov |
| Arlington VA | Expanded Housing Options | 2023-03-22 | 2023-07-01 | 2–6 units per lot; 58 permits a year | Voided 2024-09-27; Court of Appeals reversed 2025-09-05; reopened 2025-10-01; Supreme Court of Virginia heard argument about 2026-10-28; no decision found | V (most); S (argument) | arlingtonva.us; vacourts.gov |
| Auckland NZ | Unitary Plan operative in part | — | 2016-11-15 | Upzoned most residential land | — | S | aucklandcouncil.govt.nz |

## Published counts and studies

These are other people's counts, reported as published. They are context, not inputs.

| Source | Reform | Count | Data and method | Status |
| --- | --- | --- | --- | --- |
| Raleigh Missing Middle Metrics (city) | Raleigh, 2021-07-06 to 2026-07-14 | 3,180 units approved (1,714 townhouse units); 966 built | City permits | V |
| Austin HOME tracker (city, 2026-11-04) | Austin Phase 1 | 767 of 954 applications approved; 1,529 new units approved | City permits | V |
| Durham EHC final report (city) | Durham, Oct 2019 to Oct 2023 | 365 EHC permits, of which 19 duplexes | City permits | S |
| Arlington County (2024-09-27) | Arlington EHO | 45 permits approved, 186 units | County permits | V |
| Spokane BOCA tracker (Oct 2023) | Spokane interim rules | 76 units approved since 2022-07-01 | City permits | V |
| Portland Bureau of Planning and Sustainability (Jan 2025) | Portland RIP | Over 1,400 ADU and middle-housing units permitted, Aug 2021 to June 2024 | City permits | S |
| Dong (JAPA, 2025) | Portland RIP | Middle housing went from 13.4% to 44.7% of new units in single-family zones | City permits, before and after | S |
| Terner Center (2021) | California SB 9 | About 714,000 new homes would be market-feasible; 6.1 million of 7.5 million single-family lots eligible | Feasibility model; no permits, no comparison group | S |
| Terner Center (2023), "SB 9 turns one" | California SB 9 | Survey of 13 cities; Los Angeles had 211 unit applications in 2022, 38 approved | City survey | S |
| Greenaway-McGrevy and Phillips (J. Urban Economics, 2023) | Auckland | About 21,808 extra homes permitted over 5 years, about 4.1% of the region's homes (stated as a lower bound) | Geocoded permits; upzoned vs other areas | S |
| Pew and UT Austin (2023) | Houston | Over 34,000 townhouses built 2007–2020; 0.5% of single-family lots converted | Parcel records | S |
| Pew (2024) | Minneapolis | Homes +12% and rents +1%, 2017–2022 | Descriptive | S |
| Kuhlmann (JAPA, 2021) | Minneapolis | Single-family prices +3% to +5% | Prices, not permits | S |
| Freemark (Urban Affairs Review, 2020) | Chicago transit upzoning | No change in permitted homes within 5 years; land values rose | Parcels and permits, comparison areas | S |
| Stacy et al. (Urban Studies, 2023) | Many local reforms | Loosening linked to +0.8% housing supply 3–9 years later; disputed | Census units, many places | S |

No study found releases its data under a clear open licence. Mercatus work found is about Houston and Texas lot sizes (Hamilton; Gray and Furth); no Mercatus study of Austin HOME was found. Pew pages on Spokane, Portland, Arlington and the Research Triangle may exist, but pew.org blocked automated reads.

## Data sources checked

| Source | What it has | Years | Licence | On disk |
| --- | --- | --- | --- | --- |
| Census BPS, place annual files | Units and buildings permitted: 1, 2, 3–4, 5+; months reported | 2012–2025 on disk; 1980+ online | Public domain | Yes |
| Census BPS, state files | Same, by state | 1990–2025 | Public domain | Yes |
| ACS 2020–2024, B25024 and B25034 | Homes by units in structure and year built, every place | 5-year | Public domain | Yes |
| WA OFM postcensal permits | City permits, completions, demolitions: 1-unit, duplex, 3–4, 5+, ADU | 1990–2026 | State public data | Yes |
| CA HCD progress reports, Table A2 | Project rows: 2 to 4, 5+, SFA, SFD, ADU; SB 9 flag from 2022; coordinates | 2018–2025 | "License not specified" | Yes |
| Portland residential permits | Permit type incl. townhouse, rowhouse, duplex; new units | 1995–2026 | No licence stated | Yes |
| Austin permits (data.austintexas.gov 3syk-w9eu) | Class 101–105, housing units | 1921–2026 | Public domain | Subset only |
| Raleigh permits (ArcGIS) | Units, Census land-use code, missing-middle flag | 2000–2026 | Open Raleigh data policy | No |
| Mecklenburg County permits (ArcGIS) | Units, Census building code incl. townhouse | 1990–2026 | Disclaimer only | No |
| Durham permits (ArcGIS table) | Units, Census structure type | 2007-10 to 2024-02 | ODbL 1.0 | No |
| Minneapolis CCS permits (ArcGIS) | New dwelling units | 2016-12 to 2026 | City waives copyright | Subset only |
| Sacramento permits (ArcGIS) | Unit count, subtype | 2016–2026 | Not stated | No |
| Maine MOCA housing data | Units by building size, towns of 4,000+ | 2025 only | — | Yes (summary) |

## Open questions for Ryan

- **Licences.** Durham's permit table is ODbL 1.0, the same licence as OpenStreetMap, which the project avoids. Raleigh, Mecklenburg, Sacramento and the California progress reports state no clear licence. Should these be used, and if so how?
- **Townhouse gap.** Should the measure be BPS 2–4 units only, or BPS plus a townhouse count where one exists?
- **5–6 unit buildings.** BPS cannot separate them from larger buildings. Leave them out, or estimate them from city records?
- **Washington.** Wait for OFM's 2027–2028 files, or use only its earlier city reforms (Spokane, Walla Walla) for now?

## Not found or could not open

- Houston's 1998 and 2013 ordinance numbers and the 1998 effective date.
- The effective dates of Raleigh TC-5-20, Spokane C36232 (exact day) and Sacramento's interim ordinance.
- A DLCD list of which Oregon cities adopted their own code and which use the state model code.
- Stats NZ consent data (licence and townhouse type) was not opened.
