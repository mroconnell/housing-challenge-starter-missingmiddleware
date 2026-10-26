# State adoption inventory: the four non-ADU benchmark scenarios

Prepared 2026-10-26, at the owner's request. For the ADU scenario, the most useful evidence was other states' statewide laws plus their permit data after the law, measured per 1,000 eligible homes ([../gate3/STATEWIDE_STATES.md](../gate3/STATEWIDE_STATES.md)). This document builds the same inventory for the other four benchmark scenarios in [../CHALLENGE_SPEC.md](../CHALLENGE_SPEC.md):

- missing middle;
- transit-oriented density (TOD);
- parking requirement reduction;
- development fee reduction.

It is research only. Nothing here changes the model or any pre-registered plan. The row-level table is [`reference/state_adoption_inventory.csv`](../../reference/state_adoption_inventory.csv), with 52 laws and local cases.

**Status convention** (as in STATEWIDE_STATES.md):
- **Verified:** the key facts were read on an official page (statute, legislature, state agency or court), and the URL is in the CSV.
- **Source_lead:** the facts come from news, a secondary source, or an official page that could not be opened. Several official sites blocked automated reads:
  - leginfo.legislature.ca.gov and hcd.ca.gov (HTTP 403);
  - oregonlegislature.gov (connection refused);
  - data.capitol.hawaii.gov (HTTP 403).

  Those facts were read through a text-fetch service or are marked source_lead.

**All rates are descriptive.** Each law arrived while interest rates, building costs and local rules were also changing. A rate that rose after a law is associated with the law; it is not an estimate of the law's effect.

## Plain-language summary

- **Missing middle has the most usable evidence.** Four state laws are at or near the benchmark of 2–6 homes on single-family lots: Washington, Oregon, Maine and Vermont. California SB 9 is weaker, but it has four post-law years.
  - The common data source is the Census Building Permits Survey (BPS). It counts units permitted in 2-unit and 3–4-unit buildings by state and place, and is already in the repo.
  - Four states have 2 or more full years of BPS data after the law took effect or bound cities: Oregon, California, Maine and Vermont. Montana reaches 2 years when the 2026 data arrive.
  - **The state rates barely moved.** Oregon's rate stayed at 0.59 units in 2–4-unit buildings per 1,000 one-unit detached homes per year, both before (2019–21) and after (2023–25) its compliance dates. Wisconsin, which has no such law, rose from 0.74 to 0.93 over similar years.
  - The visible responses are local: Portland's 2021 Residential Infill Project permitted 271 middle-housing units in its first year.
- **TOD has strong laws but almost no production data yet.**
  - Four laws are at or near the benchmark: California SB 79, Washington HB 1491, Colorado HB24-1313 and Oregon's climate-friendly-area rules. All bind in 2024–2029.
  - Massachusetts's MBTA Communities law is older but weaker (15 homes per acre). Its only outcome series is a project pipeline: 6,898 units in 102 developments in 34 communities by January 2026 (source_lead).
  - The best measured precedent is a city program: Los Angeles's Transit Oriented Communities (TOC) program. About 50,000 units were proposed under it from late 2017 to about 2023, roughly one-third of all units proposed in the city (source_lead).
  - Wisconsin's transit data are ready: GTFS feeds for Milwaukee and Madison, two BRT lines, and Madison's own TOD overlay boundary is already in the repo.
- **Parking has the most state laws (15 at or near the benchmark) and no production data tied to any of them.**
  - The two oldest are California AB 2097 (2023-01-01) and Oregon's CFEC parking rules (2023). Most of the rest bind in 2025–2028.
  - No state dataset flags projects that used a parking exemption. The evidence is city studies, and they measure parking built, not homes built. For example, Seattle projects approved in 2012–2017 built 40% fewer spaces than the old minimums required.
- **No state comes close to the fee benchmark for all housing.** The benchmark is a 50% cut of $50,000 per unit.
  - The closest laws cover ADUs only: California (no impact fees under 750 sq ft since 2020), Montana (no ADU impact fees) and Washington (ADU impact fees at most 50% of the house's). Washington also cuts fees 50% for one narrow group of station-area projects.
  - Wisconsin's own fee reports show far lower fees than the benchmark assumes. Franklin collected $1,023,028 for 74 new units in 2025 ($13,825 per unit). New Berlin collected $156,969 for 33 new homes ($4,757 per home).
- **Recommendation: (1) missing middle, (2) transit-oriented density.** Parking is best folded into TOD as an assumption, as the challenge spec allows. Fees should be modeled from a cost pass-through rather than from other states (section 6).

## 1. Missing middle (2–6 units on single-family lots, up to 3 stories)

### 1.1 Laws

| State | Law and citation | Effective (local compliance) | What it requires | Closeness | Status |
| --- | --- | --- | --- | --- | --- |
| Washington | HB 1110 (2023), RCW 36.70A.635 | 2023-07-23 (at each city's periodic plan update; about 2025-06-30 for King, Pierce, Snohomish and Kitsap cities) | 4 units per lot in cities of 75,000+ (6 near major transit or with 2 affordable units); 2 in cities of 25,000–75,000 (4 near transit or with 1 affordable) | **at** (large cities); weaker (others) | verified |
| Oregon | HB 2001 (2019), OAR 660-046; statute ORS 197.758 (may now be 197A.420, unconfirmed) | 2019 (2021-06-30 for cities of 10,000–25,000; 2022-06-30 for cities over 25,000 and Portland Metro) | Duplexes in mid-size cities; 2–4 units, cottage clusters and townhouses in large cities | **near** (up to 4) | verified (DLCD) |
| Maine | LD 2003 (PL 2021 c. 672), 30-A M.R.S. §4364-A; LD 1829 (PL 2025 c. 385) | 2022 (2024-01-01 / 2024-07-01; new LD 1829/LD 2173 dates of July 2026 and 2027-07-01 are source_lead) | 2 units per lot; 4 in growth areas or with public water and sewer; LD 1829 raises the floor to 3 per lot, counting ADUs | **near** | verified |
| Vermont | Act 47 of 2023 (HOME Act), 24 V.S.A. §4412(1)(D) | 2023-07-01 | Duplexes wherever housing is allowed; up to 4 units on a single-family-size lot where there is municipal water and sewer | **near** (sewered areas); weaker elsewhere | verified |
| California | SB 9 (2021, Stats. ch. 162); SB 450 (2024, ch. 286); Gov. Code §65852.21, §66411.7 (sections source_lead) | 2022-01-01 (self-executing) | Ministerial approval of 2 units per lot and/or a lot split: up to 4 homes on the original lot; no height change | weaker | verified (Senate committee fact sheet) |
| Montana | SB 323 (2023), MCA 76-2-304(3) | 2024-01-01; enjoined 2023-12-29 until the state Supreme Court reversed on 2024-09-03 (2024 MT 200) | Duplexes on single-family lots in cities of 5,000+ | weaker (2 units) | verified |
| Montana | SB 382 (2023), Land Use Planning Act (MCA Title 76, ch. 25) | 2023 (dates unconfirmed) | Choose 5 of 14 strategies; duplexes or triplexes/fourplexes are options | weaker (menu) | verified (Legislative Services summary) |
| Arizona | HB 2721 (2024), A.R.S. §9-462.10 | 2024-09-14 (source_lead) (2026-01-01) | Cities of 75,000+: 2–4 units on single-family lots within 1 mile of downtown and on 20% of new developments over 10 acres | weaker (small area) | verified |
| Hawaii (adjacent) | Act 39 (2024), HRS §46-4.8 (source_lead) | 2024 (2026-12-31) | At least 2 ADUs on urban residential lots: 3 homes per lot, but as ADUs | near on count; ADUs | source_lead |
| Kansas (adjacent) | SB 418 (2026), By-Right Housing Development Act | 2026-07-01 (source_lead) | By-right approval for small projects that already comply with zoning; does not upzone | weaker | source_lead |

**Checked; no statewide mandate found:**
- Connecticut: the 2025 bill was vetoed. PA 25-1 has an opt-in transit district only (TOD table).
- New Hampshire: the 2025 laws are ADUs and housing on commercial land.
- Rhode Island: the 2026 middle-housing bill was only introduced.
- Texas: SB 15 and SB 840 do not cover single-family lots.
- Colorado: SB23-213 failed.
- Minnesota: the 2024 and 2025 bills failed.
- Also checked, none found: Massachusetts, North Carolina, Iowa, Utah, Florida, Nevada, New York, Idaho, Virginia.
- These searches were not exhaustive for 2026 sessions.

### 1.2 Production after the law

No state publishes a count of homes built under its middle-housing law. The usable common series is BPS: units in 2-unit and 3–4-unit buildings by state and place. The annual state files for 2015–2025 are already in `data/raw/census_bps_state`. BPS has three limits:
- It counts these buildings in every zone, not just former single-family lots.
- Townhouses and California SB 9 lot splits are counted as one-unit homes.
- It omits most conversions.

The rates below were computed for this inventory from those files. The denominator is ACS 2020–2024 one-unit detached homes (B25024_002), the same one used in STATEWIDE_STATES.md.

| State | Before (years) | After (years) | Rate before → after | Full years after binding date |
| --- | --- | --- | --- | ---: |
| Oregon | 2019–21 | 2023–25 | 0.59 → 0.59 | 3 |
| California (BPS) | 2018–21 | 2022–25 | 0.50 → 0.52 | 4 |
| California (HCD APR Table A2, "2 to 4" category) | 2018–21 | 2022–25 | 0.60 → 0.64 | 4 |
| Maine | 2019–23 | 2024–25 | 0.56 → 0.70 | 2 |
| Vermont | 2019–22 | 2024–25 | 0.62 → 0.69 | 2 |
| Montana | 2019–23 | 2024–25 | 1.71 → 1.97 (volatile) | 1 (2025) |
| Washington | 2019–23 | 2025 | 1.23 → 1.04 | 0 (2025 is only partly post-compliance) |
| **Wisconsin (no law)** | 2019–21 | 2022–25 | **0.74 → 0.93** | — |

All rates in the table are units permitted in 2–4-unit buildings per 1,000 one-unit detached homes per year.

**What the rates mean in counts:**
- **Oregon:** permitted an average of 691 such units a year in 2019–21 and 684 a year in 2023–25. That is 0.59 per 1,000 of its 1,164,457 one-unit detached homes in both periods.
- **Maine:** rose from 293 to 367 units a year, against 526,150 homes.
- **Wisconsin:** rose from 1,362 to 1,717 units a year, against 1,839,569 homes, without a state law.
- **California's HCD Annual Progress Report data:** 5,042 such units a year in 2018–21 and 5,355 a year in 2022–25, against 8,354,468 homes. The repo's Table A2 export has no SB 9 flag; SB 9 counts sit in a separate part of the progress report not yet obtained.

**Other official series:**
- **Maine (verified):** MOCA's first statewide housing data collection counted 308 units in 2-unit buildings and 136 units in 3–4-unit buildings among 7,499 units permitted in 2025, in 182 reporting towns.
- **Washington:** OFM publishes permits by structure type (1, 2, 3–4 and 5+ units) by city. This is the best future test. Re-check when the 2027–28 estimate files arrive.

**Local cases with post-reform counts (all source_lead):**
- **Portland, Oregon (Residential Infill Project, from August 2021):** 271 middle-housing units on 81 lots in the first year; fourplexes were 76% of those units. About 1,400 ADU and middle-housing units were permitted from August 2021 to June 2024.
- **Spokane:** middle housing was about 20% of permitted units in 2025, against 3–4% in 2020–22, after the city's own 2022–23 reform.
- **Minneapolis 2040:** about 1% of the roughly 21,000 units permitted in 2017–2022 were in 2–4-unit buildings.
- **Arlington, Virginia:** 45 permits approved by fall 2024, followed by litigation.
- **Durham, North Carolina:** 150 permits through Q2 2021, including 13 duplexes and 41 lot splits.

### 1.3 Scenario summary

- **States at or near the benchmark:** 4 (Washington, Oregon, Maine, Vermont).
- **States with 2+ full post-law years of data:** 4 (Oregon, California, Maine and Vermont); Montana reaches 2 years with the 2026 data. In every case the data are BPS units in 2–4-unit buildings, which are not specific to the law, plus Maine's single MOCA year.
- **How the ADU approach transfers:** mechanically, well. A pooled post-law rate per 1,000 one-unit detached homes can be computed the same way and applied to Wisconsin.
  - **The pooled evidence says the statewide effect is small.** The four states with comparable before-and-after windows changed by between 0.00 and +0.14 per 1,000. Wisconsin's own rate rose by +0.19 per 1,000 over similar years without any law, so a simple before/after would overstate the law's effect. A Wisconsin comparison series is needed.
  - The responses that are visible come from large, high-cost cities (Portland, Spokane) with their own reforms. That argues for transferring a city-level rate weighted by market strength, as the ADU model already does for contexts, rather than one statewide rate.
- **Wisconsin data needed:**
  - **Already in the repo:**
    - the BPS place files, for the baseline 2–4-unit series;
    - the Wisconsin DOA Comp Plan and Land Regs Inventory, which shows which towns have zoning at all;
    - V12 statewide parcels;
    - Madison zoning districts.
  - **Missing:**
    - **zoning districts by municipality**, with whether each allows a duplex or more units by right. The State Cartographer's Office collects zoning separately from parcels; that layer has not been fetched;
    - lot sizes on single-family-zoned land.

## 2. Transit-oriented density

### 2.1 Laws

| State | Law and citation | Effective (local compliance) | Station definition and requirement | Closeness | Status |
| --- | --- | --- | --- | --- | --- |
| California | SB 79 (2025, ch. 512), amended by SB 722 (2026); Gov. Code §§65912.155–.162 | 2026-01-01 (cities 2026-07-01; unincorporated areas from the 7th housing-element cycle) | Counties with more than 15 rail stations only. Tier 1 (heavy rail; busy commuter rail): within ¼ mile, 75 ft, 120 homes/acre, floor-area ratio 3.5; ¼–½ mile, 65 ft, 100 homes/acre, 3.0. Tier 2 (light rail, BRT): within ¼ mile, 65 ft, 100 homes/acre; ¼–½ mile, 55 ft, 80 homes/acre, 2.5 | **at / stronger** | verified |
| Washington | 3SHB 1491 (2025, ch. 267) | 2025-07-27 (by 2029-12-31 or later, depending on plan cycle) | Average floor-area ratio of at least 3.5 within ½-mile walk of light or commuter rail; at least 2.5 within ¼ mile of BRT stops | **at / near** | verified |
| Colorado | HB24-1313, C.R.S. 29-35-201 et seq. | 2024 (goal report due 2026-12-31; goal met by 2027-12-31) | 32 jurisdictions must zone capacity for an average of 40 homes per acre across transit areas: ½ mile of rail or commuter BRT, ¼ mile of frequent bus | **near** (zoned capacity, not a parcel floor) | verified |
| Oregon | CFEC rules, OAR 660-012-0310 to -0320 (2022) | 2022-07-21 (climate-friendly-area zoning due 2024-12-31, many extended to 2025–26) | Centers and corridors in 8 metro areas: minimum 15–25 homes/acre and maximum heights of at least 50–85 ft, by city size | near / weaker | verified |
| Massachusetts | MBTA Communities, M.G.L. c.40A §3A (2021) | 2021 (deadlines 2023-12-31, 2024-12-31, 2025-07-14 and 2025-12-31 by community type) | 177 communities: an as-of-right multifamily district of at least 15 homes/acre and 50 acres, within ½ mile of a station where applicable | weaker | verified |
| Utah | HB 462 (2022), Utah Code 10-9a-403.1 | 2022 (plans due 2025-12-31) | Station-area plans and zoning within ½ mile of rail and ¼ mile of BRT; no numeric density floor | weaker | source_lead |
| Maryland | HB 538 (2024, ch. 122), Land Use §7-503; HB 894 (2026, ch. 592) | 2024; 2026-10-01 | A 30% density bonus for 15%-affordable projects within ¾ mile of rail; mixed use near stations; no density floor | weaker | verified |
| Connecticut | PA 25-1 §11 (HB 8002, November 2025) | 2026-01-01 | Opt-in transit districts with 2–9-unit housing as of right | weaker | verified |
| Los Angeles (local) | TOC program (Measure JJJ) | 2017-09-22 | Tiered density, floor-area and height bonuses within ½ mile of major transit stops, with affordable set-asides | at (local) | source_lead |

**Checked; ruled out:**
- Montana SB 243 (2025) and SB 245 (2023): no transit test in the enacted text.
- Hawaii Act 159 (2025): funding only.
- New York, Minnesota and New Jersey: bills failed or are pending.
- Virginia and Rhode Island 2026: parking only (section 3).
- Arizona, Texas and New Hampshire 2025: housing on commercial land, not transit.

### 2.2 Production after the law

- **No state TOD law has a production series that counts permits.**
- **Massachusetts:** the state's 3A Development Tracker lists projects in the new districts. Boston Indicators counted 102 developments with 6,898 units in 34 communities by January 2026, about 30% of them within ½ mile of a station (source_lead). These are pipeline units over about two years after the first deadline, not permits. The 3A District Atlas holds zoned capacity.
- **Colorado and Utah:** report zoned or planned capacity. Utah's regional planning agency (WFRC) says 72 certified plans "pave the way" for 75,000+ homes; that is capacity, not production.
- **California SB 79:** can later be measured from the progress-report Table A2, which is geocoded. It has been in force under 4 months.
- **Los Angeles TOC:** the best-measured precedent. It drew 5,571 proposed units (1,145 of them affordable) in its first 9 months and about 50,000 by about 2023. The source is LA City Planning's quarterly Housing Progress Reports (source_lead). It was a high-cost market with a large affordable-housing incentive, so it is an upper bound for Wisconsin.

### 2.3 Scenario summary

- **States at or near the benchmark:** 4 (California, Washington, Colorado, Oregon). Massachusetts is weaker but the furthest along.
- **States with 2+ years of post-law production data:** 0. Massachusetts has about 2 years of pipeline units; Utah and Colorado have capacity only. The one long series is a city: Los Angeles TOC, with 8 years of proposed units.
- **How the ADU approach transfers:** poorly as a pooled statewide rate. There are no state post-law rates to pool, and TOD affects a small, specific area.
  - The denominator should change from one-unit detached homes to **parcels (or acres) within the station buffer**.
  - The evidence then becomes per-acre yields from Los Angeles TOC and Massachusetts 3A projects, plus Wisconsin's own Madison TOD overlay as an in-state check. The overlay boundary is in `data/raw/madison_tod` and Madison permits are in the repo; the overlay was adopted around December 2022 (source_lead).
  - A capacity-plus-feasibility (pro forma) model fits better than a rate transfer.
- **Wisconsin data needed:**
  - **GTFS stops:**
    - Milwaukee County Transit System, including the CONNECT 1 BRT line (opened 2023-06-04).
    - Madison Metro, including Rapid Route A (opened 2024-09-22).
    - Other systems from the Mobility Database or Transitland.
  - **NTD service levels** to set the "major transit stop" frequency test. These are already fetched (`docs/data-sources/ntd.md`).
  - **Parcels, zoning and current density inside ½-mile buffers:** V12 parcels plus municipal zoning.
  - **Madison's TOD overlay and permits**, as the in-state before/after.
  - **Proximity threshold to justify:** ½ mile for rail and BRT and ¼ mile for frequent bus, matching Colorado, Washington and California.

## 3. Parking requirement reduction

### 3.1 Laws (at or near the benchmark first)

| State | Law and citation | Effective (local compliance) | What it requires | Closeness | Status |
| --- | --- | --- | --- | --- | --- |
| North Carolina | HB 162, S.L. 2026-39, G.S. 160D-702(c)(2a) | 2027-01-01 | No parking minimums for any use; coastal counties exempt | **at / stronger** | verified |
| Washington | ESSB 5184 (2025, ch. 204) | 2025-07-27 (about 2027-01-27 for places of 50,000+; about 2028-07-27 for 30,000–50,000) | Caps of 0.5 spaces per apartment and 1 per house; zero for homes under 1,200 sq ft and for affordable housing | **near / at** | verified |
| Connecticut | PA 25-1 §§18–20, 53; CGS §8-3n | 2026-07-01 | No denial for lack of parking for projects of 16 units or fewer; caps for larger projects | **near / at** (small projects) | verified |
| Montana | HB 492 (2025), MCA 76-2-304 | 2026-10-01 | At most 1 space per unit; 0.5 for units under 1,200 sq ft | near | verified |
| New Hampshire | SB 284 (2025, ch. 258), RSA 674:16, VII | 2025-09-13 | At most 1 space per unit statewide | near | verified |
| Maine | PL 2025 c. 374, 30-A §4364-F | 2025 (date source_lead) | At most 1 space per unit in growth areas | near | verified |
| Vermont | Act 47 (2023), 24 V.S.A. §4414 | 2024-12-01 | At most 1 space per unit where there is water and sewer | near | source_lead |
| California | AB 2097 (2022, ch. 459), Gov. Code §65863.2 | 2023-01-01 | No minimums within ½ mile of a major transit stop | near | verified |
| Oregon | CFEC parking rules, OAR 660-012-0400 to -0450 | 2023-01-01 (codes due 2023-06-30, some later) | None near frequent transit; at most 1 per unit for multi-unit housing; or full repeal (Portland and Eugene chose repeal) | near | verified |
| Colorado | HB24-1304 | 2024-08-07 (2025-06-30) | No minimums for multifamily housing in transit service areas | near | verified |
| Illinois | People Over Parking Act, P.A. 104-0457, 50 ILCS 845 | 2026-06-01 | No minimums within ½ mile of a transit hub or ⅛ mile of a frequent bus corridor | near | verified |
| Virginia | HB 888 (2026), Va. Code §15.2-2209.4 | 2026-07-01 | Caps of 0.5 per apartment and 1 per house within ½ mile of transit | near | verified |
| Maryland | HB 894 (2026, ch. 592) | 2026-10-01 | None within ¼ mile of rail stations | near (small area) | verified |
| Rhode Island | P.L. 2026 chs. 329–330, §45-24-33(a)(28) | 2026-06-23 | At most 1 per apartment near mobility hubs and frequent stops | near (small area) | verified |
| Texas | SB 840 (2025), Local Gov't Code ch. 218 | 2025-09-01 | At most 1 per unit for housing in commercial zones of large cities | near within its zone | verified |

**Weaker laws:**
- Florida's Live Local Act (§166.04151(7)): 15% reductions for affordable projects.
- Arizona HB 2721 (middle housing only).
- Maine LD 2003 (affordable projects only).
- Montana SB 245 (2023; commercial zones).
- Washington HB 1110 (middle housing only).
- ADU-only parking bans in many states.

**Checked; nothing enacted:** Hawaii, Minnesota, Utah, New York, Massachusetts (beyond ADUs).

The Parking Reform Network counts at least 14 states with 34 laws since 2019 (via Stateline, 2026-07-08; source_lead).

### 3.2 Production after the law

- **None that can be tied to a parking law.** No state flags projects that used a parking exemption.
- California and Oregon each have about 3 post-law years in general permit series. California's Table A2 is geocoded, so units inside AB 2097's ½-mile areas could be compared with units outside, before and after 2023. That has not been done.
- **City studies measure parking provided, not homes:**
  - **Seattle:** 868 projects with 60,361 units approved in 2012–2017 provided 40% fewer spaces than the old minimums would have required (Gabbe, Pierce and Clowers 2020).
  - **Buffalo:** 47% of 36 major developments in the 2 years after its 2017 citywide repeal provided fewer spaces than the old minimum (Hess and Rehler 2021).
  - **Minneapolis:** average spaces per new apartment fell from about 1.0 to under 0.75 after its 2015 and 2021 reforms (source_lead).
  - **Housing output:** one national working paper (Tanrisever, 2025) reports more permits in the first 2 years after reforms; it is unpublished.

### 3.3 Scenario summary

- **States at or near the benchmark:** 15, the most of any scenario. Only California and Oregon have been in force 2+ years.
- **States with 2+ years of post-law production data in law-specific form:** 0.
- **How the ADU approach transfers:** poorly. Parking minimums are a cost that binds only where developers would otherwise build less parking. The effect runs through project cost per unit, so a pro forma (spaces saved × cost per space × share of projects where the minimum binds) fits better than a permit rate. The Seattle and Buffalo shares of projects building below the old minimum can calibrate the "binding" share.
- **Wisconsin data needed:**
  - **Parking minimums by municipality.** These are not compiled statewide. The Parking Reform Network map has Madison and Milwaukee:
    - Madison: no minimums downtown since 2013; TOD overlay around December 2022.
    - Milwaukee: none downtown; 1 or ⅔ space per unit elsewhere.
  - Structured and surface parking cost per space.
  - Multifamily permits by place (BPS, in the repo).

## 4. Development fee reduction (benchmark: 50% of $50,000 per unit)

### 4.1 Laws

| State | Law and citation | Effective | What it requires | Closeness | Status |
| --- | --- | --- | --- | --- | --- |
| California | SB 13 (2019) → Gov. Code §66311.5 (renumbered by SB 543, 2025; amended by SB 1117, 2026) | 2020-01-01 | No impact fees for ADUs of 750 sq ft or less; proportional above | stronger in percent; **ADUs only** | verified |
| Montana | SB 528 (2023), MCA 76-2-345 | 2024-01-01 (in force 2024-09-03) | No impact fees on ADUs; $250 application cap | stronger in percent; ADUs only | verified |
| Washington | HB 1337 (2023), RCW 36.70A.681(1)(a) | 2023-07-23 (local compliance later) | ADU impact fees at most 50% of the house's | **at (50%)**, ADUs only | verified |
| Washington | RCW 82.02.060(10) (2025 c 267) | 2025-07-27 (local compliance later) | 50% impact-fee cut for station-area projects using the multifamily tax exemption | at (50%), narrow | verified |
| California | AB 602 (2021), Gov. Code §66016.5; SB 937 (2024); AB 1820 (2024) | 2022–2025 | Fees scaled to unit size; payment deferred to occupancy; fee estimates | weaker | verified |
| Florida | HB 337 (2021), §163.31801(6) | 2021 | Caps fee increases | weaker | verified |
| Montana | SB 133 (2025) | 2025 | Drops up to a 5% administration charge; caps increases at producer-price inflation | weaker | verified (bill text) |
| North Carolina | S.L. 2017-138, G.S. 162A-200 to -215 | 2017-10-01 | Rules for water and sewer development fees, after the 2016 *Quality Built Homes* ruling | weaker | verified |
| Virginia | Va. Code §15.2-2303.4 (2016, 2019) | 2016 (source_lead) | Limits cash proffers at rezoning | weaker | verified (statute) |
| Oregon | HB 2968, HB 3639 (2025) | 2026 (source_lead) | Deferral of system development charges | weaker | source_lead |
| Colorado | SB24-194; C.R.S. 29-20-104.5(5) | 2024-08-07 | Local waivers allowed for affordable housing | weaker | verified (fiscal note) |
| Texas; Arizona | Local Gov't Code ch. 395; A.R.S. §9-463.05 | long-standing | Limit which facilities fees may fund | weaker | verified |
| Portland, Oregon (local) | ADU system development charge waiver, City Code 17.14.070(F) | 2010-03 (permanent from 2018-08-01) | 100% waiver, about $7,000–$15,000 per ADU | stronger in percent; ADUs only | verified (code) |

The common lead that Portland's waiver "expired" is wrong. It was extended in 2012 and 2016 and made permanent in 2018.

### 4.2 Production after the law

- **No state law cuts fees for all housing, so no post-law series exists for the benchmark.**
- California's ADU fee exemption has 6 post-law years in Table A2. It came in the same 2020 package as approval reforms, so its effect cannot be separated.
- **Portland's ADU waiver** is the cleanest natural experiment, though it coincided with recovery from the recession. ADU permit applications rose from 25 in 2009 to 92 in 2010 and 314 in 2015 (through September 4), per city figures reported in the press (source_lead).
- **The literature disagrees on direction:**
  - Burge and Ihlanfeldt (2006) found that Florida impact fees other than water and sewer *raised* construction in some suburbs, while water and sewer fees lowered it.
  - Terner Center (2018) found California fees of $12,000–$75,000 per multifamily unit across 7 cities.

### 4.3 Scenario summary

- **States at the benchmark for all housing:** 0. Three states are at or above 50% for ADUs only (California, Montana, Washington), and Washington has one narrow 50% cut.
- **States with 2+ years of post-law production data:** 1 (California, ADUs only, not separable).
- **How the ADU approach transfers:** it does not. There is nothing to pool.
  - The scenario should be modeled as a cost change, run through a pro forma or a supply elasticity: $25,000 less per unit, as a share of total development cost, times an assumed price elasticity of supply.
  - **Calibration warning:** Wisconsin's posted fees appear to be a fraction of the $50,000 benchmark. The two 2025 reports read were Franklin ($13,825 per unit) and New Berlin ($4,757 per home). The spec fixes $50,000 for comparability, so the tool should show both the benchmark and Wisconsin's observed fee levels.
- **Wisconsin data needed:**
  - **Local fee schedules.** Wis. Stat. §66.10014 (2017 Act 243) requires every city and village of 10,000+ to post a "New Housing Fee Report": fees collected in the prior year ÷ new units approved, by fee type. Scraping those pages gives an empirical distribution of fees per unit.
  - §66.10013 housing affordability reports add approval times.
  - The impact-fee law itself is Wis. Stat. §66.0617, with optional reductions for low-cost housing.

## 5. Cross-scenario summary

| Scenario | States at or near the benchmark | States with 2+ full years of post-law production data | Form of the data | Transfer of the ADU method | Key Wisconsin data |
| --- | ---: | ---: | --- | --- | --- |
| Missing middle | 4 (WA, OR, ME, VT) | 4 (OR, CA, ME, VT; three of them at or near the benchmark); MT reaches 2 with 2026 data | BPS units permitted in 2–4-unit buildings (not law-specific); Maine MOCA 1 year; city reports | **Good mechanically**; evidence points to a small statewide effect; needs a Wisconsin comparison trend | Zoning districts by municipality; BPS place (in repo); parcels |
| TOD | 4 (CA, WA, CO, OR) | 0 states (Massachusetts has about 2 years of pipeline units); Los Angeles TOC city program has 8 | Pipeline units, zoned capacity, city proposals | Weak as a rate; strong as station-area capacity × per-acre yield | GTFS (MCTS, Madison Metro), NTD (in repo), parcels in buffers, Madison TOD overlay and permits (in repo) |
| Parking | 15 | 0 law-specific (CA and OR have 3 general years) | City studies of parking built | Weak; use a pro forma cost model | Minimums by municipality (not compiled); cost per space |
| Fees | 0 for all housing (3 ADU-only, 1 narrow) | 1 (CA ADUs, bundled) | ADU permits; Portland applications | None; use a cost/elasticity model | §66.10014 fee reports (scrapeable) |

## 6. Recommendation for the next MVP cycle

**1. Missing middle: best supported.**
- It has the most at-or-near laws with 2+ post-law years: Oregon, Maine and Vermont, plus California's weaker SB 9 with 4 years.
- One consistent cross-state series (BPS) is already in the repo for every state and Wisconsin place.
- Washington's OFM structure-type data will provide a strong test within two years.
- The ADU machinery (rates per 1,000 one-unit detached homes, contexts, district allocation) carries over directly.
- The honest headline is likely "a small statewide effect, concentrated in strong markets." That is policy-relevant and defensible.
- **Main gap:** a statewide map of which Wisconsin lots are zoned single-family only.

**2. Transit-oriented density: second, with parking folded in.**
- The state laws are too new for production data, but the Wisconsin data are unusually ready: GTFS for both BRT systems, NTD, parcels, and an in-state precedent (Madison's TOD overlay with Madison permits in the repo).
- The challenge spec explicitly allows TOD to assume parking minimums are removed. That covers most of the parking scenario's content without needing the uncompiled municipal parking inventory.
- Evidence would be per-acre yields from Los Angeles TOC (upper bound), Massachusetts 3A projects and Madison, applied to Wisconsin station-area capacity.

**Not recommended next:**
- **3. Parking as a stand-alone scenario.** It has the most laws but no production data tied to them, and Wisconsin parking minimums are not compiled.
- **4. Fees.** There is no state analog at the benchmark. It is best modeled as a cost-elasticity sensitivity, with the §66.10014 reports used to show how far $50,000 per unit sits above observed Wisconsin fees.

## 7. Unverified items and re-checks

- **California:** Gov. Code sections for SB 9 (leginfo blocked). No statewide SB 9 total; the SB 9 table is not in the repo's Table A2 export. AB 1308, SB 423, AB 894 and SB 341 parking claims are unverified.
- **Oregon:** current ORS number for HB 2001; status of the proposed August 2026 OAR 660-046 revision; HB 2968 and HB 3639 final text.
- **Washington:**
  - HB 1110 compliance timing in the current RCW text versus "six months after the periodic update";
  - HB 1491 codified sections and its parking terms;
  - the ESSB 5184 referendum (RM-109) outcome.
- **Maine:** LD 1829 and LD 2173 implementation dates; the conflicting versions of §4364-A(1); the LD number and effective date of §4364-F.
- **Vermont:** Act 47 parking text read from an agency memo only.
- **Montana:** SB 382 sections and deadlines; outcome of the merits case against SB 323 and SB 528; SB 133 effective date.
- **Arizona:** the 2024-09-14 effective date.
- **Hawaii:** Act 39 text (blocked) and the repeal bill's status.
- **Kansas:** SB 418 enrolled text.
- **Colorado:** HB24-1313 signing date; HB24-1304 C.R.S. section.
- **Utah:** station-area plan status from an official state source.
- **Massachusetts:** official compliance count and statewide zoned capacity; the pipeline figures are from Boston Indicators.
- **Local figures:** Los Angeles TOC, Portland RIP, Portland ADU waiver, Spokane, Minneapolis, Durham and the San Diego parking figures are source_lead.
- **Madison TOD overlay:** adoption date (about December 2022) is source_lead.
- **Re-check later:**
  - Washington OFM EY2027–28, for the HB 1110 test;
  - Maine MOCA 2026;
  - Massachusetts 3A tracker;
  - California SB 79 in Annual Progress Reports from 2027;
  - Arizona HB 2721 after 2026.

## Reproduce

- **Table rows:** `reference/state_adoption_inventory.csv`. Each row has its law URL, verification status and access date (2026-10-26).
- **BPS rates (section 1.2):**
  - Source: `data/raw/census_bps_state/st{2015..2025}a.txt`.
  - Numerator: 2-unit units plus 3–4-unit units (imputed totals).
  - Denominator: one-unit detached homes from `reference/statewide_states_acs.csv`.
- **California Annual Progress Report rates:** `data/raw/hcd_apr_a2/tablea2.csv`, UNIT_CAT "2 to 4", summing BP_ income columns by YEAR.
- These were one-off calculations for this inventory; no script or test was added.
