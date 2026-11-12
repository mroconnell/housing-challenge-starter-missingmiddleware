# Parking: dose-response plan, DRAFT (not locked)

**Status: DRAFT, 2026-11-12. Not locked. Feasibility and coding only.** Written by a parking-thread helper at Ryan's request. No permit outcome was read, no effect was computed, and no permits were counted by place or year for this plan. The only permit-file use was a yes/no check that a place has its own row in the 2024 Census permit place files (names only). Ryan must make the choices in section 10 before this is locked. After locking, changes go in the last section with a date and a reason.

**Files.**
- This plan: `docs/parking/DOSE_PLAN.md`.
- Every coded reform, with its dose status and sources: `reference/parking_dose_universe.csv` (238 rows).

**Reopens an earlier decision.** On 2026-11-04 Ryan chose "Stop at the pilot" for exempt-land map coding and clerk requests (WORK_SESSION_RESULTS.md, exempt-share pilot). This plan needs map coding again. Nothing in it runs until Ryan says so.

## 1. Question

- Does the effect of a parking reform grow with how much of the requirement it removed?
- If it does, what does a full citywide repeal (dose 100) do, estimated from full **and** partial reforms together?
- Why: today only full citywide repeals (74 places) feed the parking range. Partial reforms are left out or reported apart. Pooling them by dose could use more places.

**What kind of number this is.** A slope: the change in homes permitted per 1,000 existing homes a year, per 100 points of dose. At dose 100 it is the effect of a full citywide repeal, the same quantity as today's main estimate.

## 2. Dose definition

**Dose = (share of the place's homes inside the reform area) × (share of the housing parking requirement removed there) × 100.**

| Reform | Coverage share | Removal share | Dose |
|---|---|---|---|
| Citywide residential repeal | 100% | 100% | 100 |
| Transit-area (TOD) repeal | homes inside the mapped buffer ÷ all homes | 100% | e.g. 30 |
| Commercial or downtown districts only | homes in those zones ÷ all homes | 100% | e.g. 5 |
| Citywide cut from 2 spaces per home to 1 | 100% | (2 − 1) ÷ 2 = 50% | 50 |
| Non-residential uses only | — | 0% for housing | 0 |

**Rules.**
- **Homes** = housing units in Census blocks, placed in or out of the area by block internal point (the method of the Seattle test, OLDER_REFORMS_PLAN.md). 2010 blocks for reforms in 2015–2019; 2020 blocks for 2020–2024.
- **Removal share** = (old − new) ÷ old, in spaces per home, for a standard 20-unit building with half 1-bedroom and half 2-bedroom homes (the pilot's rule, `reference/parking_dose_pilot.csv`). A full repeal is 100% whatever the old level.
- **Discretion.** If a reform leaves the number to an official (waivers, "realistic demand", demand studies), the removal share can't be read from the code. Those places take a fallback dose.
- **Use-type reforms.** If only some housing types lose their minimum (Norman: apartments yes, 1–2 family no), coverage is 100% and removal is computed per housing type. The all-homes dose weights types by their share of the existing stock (ACS table B25024, units in structure). The 2–4 unit outcome gets its own dose (section 7).
- **Fallback doses (Ryan's; assumptions, labelled as such everywhere):**

| Fallback class | Dose |
|---|---|
| Transit-area (TOD) reform | 25 |
| Weak repeal (discretion remains) | 15 |
| Commercial or downtown districts only | 10 |
| No change for housing | 0 |

- **No fallback was given** for broad mapped districts (Covington KY) or citywide reductions whose tables are not yet coded (Boise, Tulsa, Binghamton, Pomona 2024). Choice C3.
- **Dose is capped at 0–100.** A reform that **added** housing minimums (Brainerd 2023) is coded 0 in the main version. A negative dose is choice C7.

## 3. The coded reforms

**Sources searched:** `parking_repeal_checks.csv`, `_v2`, `_expanded`, `_dates33`; `parking_expanded_match.csv` (batch 2026-11-05, drop reasons); `parking_partial_checks.csv` and PARTIAL_REFORMS_*; OLDER_REFORMS_*; EDGE_TEST_FEASIBILITY.md (and its two addenda); CA_AB2097_*; TOD lists `tod_cases.csv` and `tod_reform_density.csv` (read only, not edited); the dose and exempt-share pilots.

**Size of the list.**
- 238 entries in all.
- **150 are coded reforms** with a scope and, for most, a year.
- **88 are not usable reforms:**
  - 51 have no date found;
  - 20 had no minimums before (no event);
  - 17 changed nothing dated for housing, or only for ADUs or affordable homes, or were never enacted. These include Fort Wayne (downtown, 2011) and Neptune NJ (2000), which are dated but before 2015.
  - They are listed in the CSV with the reason.

**The 150 coded reforms, by type and dose status** (counts of reforms):

| Type | Computable from data | Partly from data | Fallback only | All |
|---|---|---|---|---|
| Citywide residential repeal | 91 | 11 | 0 | 102 |
| TOD / transit area | 15 | 3 | 3 | 21 |
| Mapped district (broad) | 3 | 1 | 0 | 4 |
| Commercial or downtown only | 0 | 4 | 3 | 7 |
| Citywide reduction | 4 | 1 | 1 | 6 |
| Other: weak repeal (discretion) | 0 | 0 | 3 | 3 |
| Other: non-residential only (dose 0) | 3 | 0 | 0 | 3 |
| Other: multifamily only (Norman) | 1 | 0 | 0 | 1 |
| Other: unit-count and district exemptions (Eureka CA) | 0 | 0 | 1 | 1 |
| Other: affordable-only or tied incentive (fail the screen) | 2 | 0 | 0 | 2 |
| **All** | **119** | **20** | **11** | **150** |

- **"Computable"** means both factors can be set from public data: a map or ordinance for coverage and the code text for removal. For a citywide repeal both are 100% by definition.
- **"Partly"** means one factor comes from data and the other needs an assumption, such as a code that leaves the number to an official, or a district map that is only a PDF.
- **"Fallback"** means neither factor is available, so the fixed dose in section 2 is used.
- Many computable rows can't join, because their year is outside 2015–2024 or they have no permit row (section 5).
- **CA AB 2097** (state law, 2023) is listed as one row and flagged: **it is a separate study owned by the CA AB 2097 thread.** It is not pooled here unless Ryan asks. The Oregon state transit rule (OAR 660-012, from 2022-12-31) is listed the same way, with no owner.

## 4. Data for each factor

### 4.1 Coverage (share of homes inside the reform area)

| Input | Use | Source | Licence | On disk? |
|---|---|---|---|---|
| Census 2020 blocks with housing units (HOUSING20) and internal points | Homes in and out of the area, 2020–2024 reforms | Census TIGER/Line TABBLOCK20 (PL 94-171 counts) | Public domain | 15 states held (`data/raw/census_tiger_2020_tabblock`); others are one zip per state |
| Census 2010 blocks with housing units | Homes for 2015–2019 reforms | Census TIGER/Line TABBLOCK10 + 2010 SF1 H1 | Public domain | No |
| ACS 5-year B25001, B25024 by block group | Fallback homes; housing-type shares for use-type reforms | Census API | Public domain | Partly (place-level ACS held) |
| Transit stops | Buffers for TOD reforms (distance from the ordinance) | Agency GTFS feeds; Mobility Database stored copies (catalog CC0) | Each agency's terms; several state none (repo rule D1, public records). Recorded in `docs/DATA_PROVENANCE.md` | Some held (TOD and pilot fetches) |
| Archived GTFS for the reform year | Stops as they were, not today's | Mobility Database history (recent years); otherwise today's stops, flagged | As above | No |
| City or county zoning layers | District and overlay reforms | City open-data portals (e.g. Columbia SC, Covington KY via LINK-GIS, Denver, Albuquerque, Somerville, Waukegan); Madison TOD overlay | Often no licence stated; listed per layer; shipping a layer needs Ryan's OK (as in the pilot) | Madison overlay only (`data/raw/madison_tod/tod_boundary.geojson`) |
| State layers | San Diego Transit Priority Areas; California major transit stops | City/SANDAG; California open data | To check per layer | AB 2097 thread holds the state layer |
| Ordinance maps (PDF) | Small towns with no GIS (Camden ME, Watertown NY, Penndel PA, Lewisburg PA, Bloomsburg PA) | Town websites | Public record (D1) | No; hand digitising |

**Coverage rules.**
- Transit-area reforms use the ordinance's own distance and stop type (for example ¼ mile of CTA and Metra stations in Chicago, ½ mile on Pedestrian Streets; ½ mile of any transit stop in Spokane 2023).
- Districts use the boundary in force in the reform year where an archive exists. Otherwise today's boundary is used and flagged, because boundaries move (Reno and Davenport redrew theirs; EDGE_TEST_FEASIBILITY.md).
- **Blocks:** if a site refuses automated access (Cloudflare, 403, 429), it is cited as blocked and not worked around. No user-agent spoofing. Clerk requests only with Ryan's OK.

### 4.2 Removal share (old vs new minimum)

| Input | Use | Source | Licence |
|---|---|---|---|
| Old apartment minimums for the repeal places | Already coded for 53 of 71 places in `parking_old_minimums.csv`; 15 in the dose pilot | Ordinances, council packets, archived codes | Public record (D1) |
| Old and new tables for reductions | Bangor (1.5 → 1 per home, 33% removal), Boise, Tulsa, Binghamton, Pomona 2024, Waukegan L1–L3, Albuquerque centers and corridors | Municode, American Legal, eCode360, Legistar packets, city PDFs, Wayback Machine copies | Public record (D1) |

- For a full repeal the old level doesn't change the dose (100%). The old minimum is kept as a separate trait, as in Test 44.
- **Known blocks:** Municode refuses automated access (test 43; Covington GA; Cave Spring GA); Bakersfield's code site blocked direct reading. These are cited, not worked around.

### 4.3 Effort (from the pilots)

- Removal coding: about 3 minutes of AI time per place (dose pilot median). About 30 new places: roughly 2–3 AI-hours.
- Coverage maps: about 8 minutes of AI time per place for 15 places (exempt-share pilot). About 30 places: roughly 4–6 AI-hours, plus hand digitising for about 5 PDF-only towns.
- Clerk requests would be needed for some old codes. None will be sent without Ryan's OK.

## 5. Which reforms can join (sample rules unchanged)

**Rules (EXPANDED_PLAN.md, batch 2026-11-05):**
- reform year 2015–2024, so that at least 1 after-year exists (permit files run through 2025);
- the place has its own row in the Census permit place files (yes/no name check of the 2024 files);
- a dated reform that touches housing;
- same before window (5 years), after window (years 1–3, as available) and comparison pools as the main estimate.

**Who could join** (counts of places):

| Group | Places | Dose status (computable / partly / fallback) |
|---|---|---|
| Already in: the 74 citywide repeals | 74 | 64 / 10 / 0 |
| New, clearly eligible | 24 | 11 / 7 / 6 |
| New, eligible if one fact is confirmed | 5 | 3 / 1 / 1 |
| New, unsure (screen or date questions) | 5 | — |
| Dose-0 checks (housing untouched) | 2 | 2 / 0 / 0 |

- **So 98 places with a dose above 0 could join** (74 + 24). That rises to 103 if the 5 conditional places check out, and to 108 with the 5 unsure ones.
- **The 24 new places, by type:**
  - Transit area (7): Chicago 2015, San Diego 2019, Albuquerque 2018, Penndel 2020, Somerville 2019, Madison 2023, Denver 2018.
  - Citywide (2): Spokane 2024, Bakersfield 2024.
  - Mapped district (3): Covington KY 2020, Columbia SC 2021, Fremont 2015.
  - Commercial or downtown only (6): Camden ME 2021, Waukegan 2024, Watertown NY 2023, Bloomsburg 2024, Lewisburg 2023, Pomona 2019 (or its 2024 cut; one event per place).
  - Reductions (2): Boise 2023, Tulsa 2024.
  - Weak repeals (3): Maumee 2020, Dover NH 2015, Jackson TN 2021.
  - Multifamily only (1): Norman 2021.
- **Conditional (5):**
  - Central Falls 2022 (repeal reversed in 2025: allowed?);
  - North Canton 2023 (is the Main Street exemption new?);
  - Albany NY 2017 (exemption date);
  - Bangor 2024 (effective date);
  - Binghamton 2024 (effective in 2024 or 2025?).
- **Unsure (5):**
  - Charlottesville 2024 (its only after-year is under litigation);
  - Eureka CA 2019 (staged steps);
  - Shoreline 2022 (may be an optional reduction);
  - Portland OR 2018 (parking detail unknown);
  - Honolulu 2017 (parking change not verified).
- **Dose-0 checks:** Seabrook 2019 and Brainerd 2023 (non-residential only).
- **Only 1 after-year:** Spokane, Bakersfield, Waukegan, Bloomsburg, Tulsa and Pomona 2024, plus Bangor and Binghamton if they qualify.
- **Not joining:**
  - outside 2015–2024 (12 small places before 2015; Hayward, Seattle, Portland 2003 and Salt Lake City, which are older transit reforms; Somerville, Lake Oswego, Hillsboro, Chapel Hill, Greensboro and High Point, which are 2025 or later);
  - no permit row of their own (Bowling Green, Charlotte, Wilmington and 4 small Michigan places; Calumet's series is incomplete);
  - inside a later citywide repeal's before window (Minneapolis 2015, Ann Arbor 2021, Spokane 2023);
  - failing the existing screen (Los Angeles TOC 2017 is an incentive tied to affordable homes; New York's 2016 rule is affordable-only).

**Precision, stated before any result.** In a through-origin fit, each place adds information in proportion to weight × dose². A place at dose 25 adds 1/16 of what the same place adds at dose 100; at dose 10, 1/100. So most of the information still comes from the 74 full repeals and the few high-dose new places. This plan states no expected direction or size.

## 6. Estimator

**Inputs per place *i*:**
- *e_i*: its existing difference-in-differences effect (main method and method 2 D, unchanged code);
- *w_i*: its existing weight (main: homes × after-years; D: target-state mix);
- *d_i*: its dose, from 0 to 1.

**Main: weighted least squares through the origin.**
- β = Σ *w_i d_i e_i* ÷ Σ *w_i d_i²*.
- β is the effect of a full citywide repeal (dose 100). It is the same as a weighted mean of *e_i / d_i* with weights *w_i d_i²*.
- With only the 74 places at dose 100, β equals today's average exactly. That is a code check run before any new place is added.

**Assumption.** The effect is proportional to dose: no effect at dose 0, and half the effect at dose 50. This is checked, not assumed silently.

**Checks (pre-set reading rules):**
1. **Full vs partial.**
   - β from dose-100 places only, and β from places below dose 100 only (each through the origin);
   - the gap between them, with a placebo range (section 8).
   - If the gap's 90% range excludes 0, the scaling assumption fails. The pooled β is then not used, and the full-only estimate stands.
2. **Intercept.** The same fit with an intercept. If the intercept's range excludes 0, this is flagged: the effect may not vanish at dose 0.
3. **Fallback sensitivity:**
   - places with fallback doses dropped;
   - fallback doses halved and doubled;
   - main dose 15 instead of 100 for the 6 near-benchmark places with discretion.
4. **Dose-0 places** (Seabrook, Brainerd) are reported alone, like the non-residential placebo (T1). They add nothing to a through-origin slope.
5. **Coverage measure.** Homes share (main) vs apartment-zoned land share (the pilot's 25 m grid method), where both exist.
6. **Staged reforms.** In the main version, a citywide repeal is dose 100. A sensitivity uses the increment, 100 × (1 − share of homes already exempt before), where it can be measured (choice C4).

**Other rules:**
- No new trait search. The fit has no other variables.
- Method 2 D gets the same doses and its own weights.
- Pre-trend rule as in Test 56: a lead or placebo date excluding 0 under both methods turns on the "pre-trend, not read as an effect" label.

## 7. Outcomes

| Outcome | Unit | Dose used |
|---|---|---|
| All new homes (main) | homes permitted per 1,000 existing homes a year | all-homes dose |
| 2–4 unit homes (Test 56's outcome) | same unit | 2–4 dose: the same as the all-homes dose, except for use-type reforms (Norman: 100 for 3–4 unit buildings if O-2122-6 counts them as apartments, 0 for 2-unit buildings; weighted by the ACS 2-unit vs 3–4 unit shares) and for staged 2–4 reforms (Milwaukie 2022 already removed 2–4 parking) |

- **Wisconsin, for display only:** a full statewide repeal is dose 100, so Wisconsin homes over 2027–2031 = β × 13,343.385. Any use needs Ryan's OK.

## 8. Range (consistent with Test 56)

- **The same placebo sets as Test 56:** never-repealed places, given the real places' event years and matched to pools by the same rules.
- **Each placebo place inherits the dose of the real place it stands in for**, so every placebo fit has the same dose pattern as the real fit.
- For each placebo set, compute β the same way. **The 90% range is the real β, with its spread taken from the placebo β's 5th to 95th percentiles,** as in Test 56.
- The full-vs-partial gap and the intercept get placebo ranges the same way.
- **Pools.** Places that are new treated units (any dated partial reform) leave every comparison pool, as the 303 benchmark places already do. This shrinks some pools (test 45 lost 6 large-city pools under a strict rule). Choice C5.

## 9. What it can't say, and how it would be shown

**What it can't say:**
- **Whether minimums bound.** Dose measures what the code removed, not whether builders were held back (Madison, test 43: most large projects built above the minimum).
- **Where building happens.** A homes share understates reforms in areas with few homes now but much building later. Fremont's Warm Springs plan area was mostly industrial land, so its homes-share dose is near 0. Transit and downtown areas usually build faster than the rest of the city. Check 5 is the partial answer.
- **Bundled changes.** Several partial reforms came with upzoning or full code rewrites (Somerville 2019, Albuquerque 2018, Columbia 2021, Covington 2020, Denver 2018, Madison 2023). Their effects can't be split from parking.
- **Fallback doses are assumptions.** 6 of the 24 new places rely on them.
- **Low doses add little.** See the precision note in section 5.
- **Transfer to Wisconsin.** It assumes Wisconsin's effect equals the measured average (ATU = ATT), as before.

**How it would be shown:**
- A sensitivity row beside the headline: "dose-pooled, N places", in the same unit and with the same 90% range method.
- It replaces nothing unless Ryan decides so after an audit.
- Every fallback place is marked "assumed dose".
- The full-vs-partial check is shown next to it.
- Reforms in display order: ADUs, middle housing, TOD, parking (parking is the only one here).

## 10. Choices for Ryan

| # | Choice | Options |
|---|---|---|
| C1 | Go ahead with map and ordinance coding, reopening "stop at the pilot" (2026-11-04)? | yes / pilot-size subset / no |
| C2 | Coverage measure | homes share (main, as proposed) / apartment-zoned land share |
| C3 | Fallback doses for classes with none | broad districts (Covington KY); reductions with tables not yet coded |
| C4 | Citywide repeals with earlier partial exemptions | 100 (your definition; main) / increment net of exempt share (sensitivity) |
| C5 | Partial-reform places in comparison pools | drop from pools (proposed) / keep |
| C6 | Near-benchmark places with discretion (Canandaigua, Plainfield, Cambridge MD, Branson, Trenton, Duluth) | 100 (main) / weak-repeal 15 |
| C7 | Reforms that added minimums (Brainerd) | dose 0 / negative dose |
| C8 | Conditional and unsure places | which facts to check first; Central Falls (reversed repeal) in or out |
| C9 | Staged places (Pomona 2019 vs 2024; Spokane 2023 vs 2024) | earlier or later event |
| C10 | Block year | 2010 blocks for 2015–2019 reforms (proposed) / 2020 for all |
| C11 | Status of the result | sensitivity beside the headline (proposed) / candidate headline after audit |

## 11. Tables of all coded reforms

### 11.1 The 74 places already in the main estimate (all dose 100)

"Mapped carve-out": a near-benchmark place where a mapped district keeps a housing minimum, so a measured dose would be a little under 100. "Discretion remains": an official can still require parking (choice C6).

| Place | State | Repeal year | Old minimum (spaces per apartment) | Dose status | Main dose (0–100) | Notes |
|---|---|---|---|---|---|---|
| Berkeley | California | 2021 | 1.0 | partly | 100 | mapped carve-out |
| Plainfield | Indiana | 2022 | 2.0 | partly | 100 | discretion remains |
| Windham | Maine | 2018 | 2.0 | partly | 100 | mapped carve-out |
| Cambridge | Maryland | 2021 | 1.5 | partly | 100 | discretion remains |
| Duluth | Minnesota | 2023 | 1.25 | partly | 100 | discretion remains |
| Branson | Missouri | 2018 | 2.0 | partly | 100 | discretion remains |
| Trenton | New Jersey | 2023 | 1.5 | partly | 100 | discretion remains |
| Canandaigua | New York | 2020 | not coded | partly | 100 | discretion remains |
| Kingston | New York | 2023 | not coded | partly | 100 | mapped carve-out |
| Carrboro | North Carolina | 2023 | 2.25 | partly | 100 | mapped carve-out |
| Birmingham | Alabama | 2024 | 1.5 | computable | 100 |  |
| Anchorage | Alaska | 2023 | 1.6 | computable | 100 |  |
| Rogers | Arkansas | 2024 | not coded | computable | 100 |  |
| Alameda | California | 2021 | 2.0 | computable | 100 |  |
| Culver City | California | 2022 | 2.25 | computable | 100 |  |
| Emeryville | California | 2020 | 0.8 | computable | 100 |  |
| Sacramento | California | 2024 | 1.5 | computable | 100 |  |
| San Francisco | California | 2019 | 1.0 | computable | 100 |  |
| San Jose | California | 2023 | 1.7 | computable | 100 |  |
| Longmont | Colorado | 2024 | 2.0 | computable | 100 | earlier partial reform in before-window |
| Bridgeport | Connecticut | 2021 | 1.65 | computable | 100 |  |
| Hartford | Connecticut | 2017 | 1.0 | computable | 100 | earlier partial reform in before-window |
| Gainesville | Florida | 2022 | 2.0 | computable | 100 | earlier partial reform in before-window |
| Avondale Estates | Georgia | 2021 | not coded | computable | 100 |  |
| Dunwoody | Georgia | 2019 | 2.125 | computable | 100 |  |
| Social Circle | Georgia | 2023 | not coded | computable | 100 |  |
| South Bend | Indiana | 2021 | not coded | computable | 100 | earlier partial reform in before-window |
| Lansing | Kansas | 2024 | 2.0 | computable | 100 |  |
| Lexington | Kentucky | 2022 | 1.8 | computable | 100 |  |
| Hampden | Maine | 2022 | 2.0 | computable | 100 |  |
| Portland | Maine | 2024 | not coded | computable | 100 |  |
| Cambridge | Massachusetts | 2022 | 1.0 | computable | 100 |  |
| Ann Arbor | Michigan | 2022 | 1.5 | computable | 100 |  |
| Ecorse | Michigan | 2020 | not coded | computable | 100 |  |
| Kalamazoo | Michigan | 2023 | not coded | computable | 100 |  |
| Mount Pleasant | Michigan | 2018 | not coded | computable | 100 |  |
| River Rouge | Michigan | 2021 | not coded | computable | 100 |  |
| Minneapolis | Minnesota | 2021 | 1.0 | computable | 100 | earlier partial reform in before-window |
| Northfield | Minnesota | 2024 | not coded | computable | 100 |  |
| St. Paul | Minnesota | 2021 | 1.5 | computable | 100 |  |
| Hanover | New Hampshire | 2024 | not coded | computable | 100 | earlier partial reform in before-window |
| Buffalo | New York | 2017 | 1.0 | computable | 100 |  |
| Hudson | New York | 2019 | 1.0 | computable | 100 |  |
| Saranac Lake | New York | 2016 | not coded | computable | 100 |  |
| Durham | North Carolina | 2023 | 2.0 | computable | 100 | earlier partial reform in before-window |
| Gastonia | North Carolina | 2021 | not coded | computable | 100 |  |
| Raleigh | North Carolina | 2022 | 1.5 | computable | 100 | earlier partial reform in before-window |
| Portsmouth | Ohio | 2022 | not coded | computable | 100 |  |
| Albany | Oregon | 2023 | 1.0 | computable | 100 | Oregon state transit rule from 2022-12-31 |
| Ashland | Oregon | 2023 | 1.75 | computable | 100 | Oregon state transit rule from 2022-12-31 |
| Beaverton | Oregon | 2023 | 1.5 | computable | 100 | Oregon state transit rule from 2022-12-31 |
| Bend | Oregon | 2023 | 1.5 | computable | 100 | Oregon state transit rule from 2022-12-31 |
| Central Point | Oregon | 2023 | 1.75 | computable | 100 | Oregon state transit rule from 2022-12-31 |
| Corvallis | Oregon | 2022 | 1.0 | computable | 100 | Oregon state transit rule from 2022-12-31 |
| Eugene | Oregon | 2024 | 1.0 | computable | 100 | Oregon state transit rule from 2022-12-31 |
| Grants Pass | Oregon | 2024 | 1.0 | computable | 100 | Oregon state transit rule from 2022-12-31 |
| King City | Oregon | 2024 | 1.0 | computable | 100 | Oregon state transit rule from 2022-12-31 |
| Millersburg | Oregon | 2024 | not coded | computable | 100 | Oregon state transit rule from 2022-12-31 |
| Milwaukie | Oregon | 2024 | 1.0 | computable | 100 | earlier partial reform in before-window; Oregon state transit rule from 2022-12-31 |
| Salem | Oregon | 2023 | 1.5 | computable | 100 | Oregon state transit rule from 2022-12-31 |
| Springfield | Oregon | 2024 | 1.0 | computable | 100 | Oregon state transit rule from 2022-12-31 |
| Tigard | Oregon | 2022 | not coded | computable | 100 | earlier partial reform in before-window; Oregon state transit rule from 2022-12-31 |
| Tualatin | Oregon | 2024 | 1.5 | computable | 100 | Oregon state transit rule from 2022-12-31 |
| West Linn | Oregon | 2024 | 1.83 | computable | 100 | Oregon state transit rule from 2022-12-31 |
| Austin | Texas | 2023 | 2.0 | computable | 100 |  |
| Bandera | Texas | 2021 | 3.0 | computable | 100 |  |
| Bastrop | Texas | 2019 | not coded | computable | 100 |  |
| Taylor | Texas | 2023 | 2.25 | computable | 100 |  |
| Burlington | Vermont | 2023 | 2.0 | computable | 100 | earlier partial reform in before-window |
| Newport News | Virginia | 2024 | not coded | computable | 100 |  |
| Richmond | Virginia | 2023 | 1.0 | computable | 100 |  |
| Roanoke | Virginia | 2021 | 1.5 | computable | 100 |  |
| La Crosse | Wisconsin | 2024 | 1.5 | computable | 100 |  |
| West Allis | Wisconsin | 2022 | not coded | computable | 100 |  |

### 11.2 The other 76 coded reforms

"Could join?" applies the rules in section 5. Old and new minimums are in spaces per home where known; "?" means not yet coded. Sources and flags for every row are in `reference/parking_dose_universe.csv`.

| Place | State | Year | Type | Old → new minimum | Dose status | Dose value (0–100) | Could join? |
|---|---|---|---|---|---|---|---|
| Bakersfield | California | 2024 | citywide residential | ? → 0 (0.25 per unit for market-rate 20+ unit multifamily) | partly | from data; none needed: 75-100 by bounds (20+ unit market-rate apartments keep 0.25 per unit; removal there = (old-0.25)/old, at least 75% if the old rate was 1 or more) | yes (1 after-year) |
| Bowling Green | Ohio | 2023 | citywide residential | ? → 0 | computable | 100 (by definition) | no: no permit row |
| Brownville | Nebraska | 2004 | citywide residential | ? → 0 | computable | 100 (by definition) | no: year before 2015 |
| Calumet | Michigan | 2022 | citywide residential | ? → 0 | computable | 100 (by definition) | no: permit series missing |
| Central Falls | Rhode Island | 2022 | citywide residential | ? → 0 | computable | 100 (by definition) | yes, if Ryan allows a reversed repeal (after-years 2023-2024 only) |
| Chapel Hill | North Carolina | 2026 | citywide residential | ? → 0 | computable | 100 (by definition) | no: year after 2024 (permit data end 2025) |
| Charlottesville | Virginia | 2024 | citywide residential | ? → 0 | computable | 100 (by definition) | unsure: only after-year (2025) is disrupted by litigation |
| Coal Hill | Arkansas | 1999 | citywide residential | ? → 0 | computable | 100 (by definition) | no: year before 2015 |
| Cowpens | South Carolina | 2008 | citywide residential | ? → 0 | computable | 100 (by definition) | no: year before 2015 |
| Eastover | South Carolina | 2012 | citywide residential | ? → 0 | computable | 100 (by definition) | no: year before 2015 |
| Golf | Illinois | 1943 | citywide residential | ? → 0 | computable | 100 (by definition) | no: year before 2015 |
| Greensboro | North Carolina | 2027 | citywide residential | ? → 0 | computable | 100 (by definition) | no: year after 2024 (permit data end 2025) |
| High Point | North Carolina | 2027 | citywide residential | ? → 0 | computable | 100 (by definition) | no: year after 2024 (permit data end 2025) |
| Hillsboro | Oregon | 2025 | citywide residential | ? → 0 | computable | 100 (by definition) | no: year after 2024 (permit data end 2025) |
| Kalkaska | Michigan | 2022 | citywide residential | ? → 0 | computable | 100 (by definition) | no: no permit row |
| Laceyville | Pennsylvania | 2013 | citywide residential | ? → 0 | computable | 100 (by definition) | no: year before 2015 |
| Lake City | Michigan | 2022 | citywide residential | ? → 0 | computable | 100 (by definition) | no: no permit row |
| Lake Oswego | Oregon | 2025 | citywide residential | ? → 0 | computable | 100 (by definition) | no: year after 2024 (permit data end 2025) |
| Mackinac Island | Michigan | 1898 | citywide residential | ? → 0 | computable | 100 (by definition) | no: year before 2015 |
| Mancelona | Michigan | 2020 | citywide residential | ? → 0 | computable | 100 (by definition) | no: no permit row |
| Meshoppen | Pennsylvania | 2013 | citywide residential | ? → 0 | computable | 100 (by definition) | no: year before 2015 |
| New Rockford | North Dakota | 1983 | citywide residential | ? → 0 | computable | 100 (by definition) | no: year before 2015 |
| Ozawkie | Kansas | 2007 | citywide residential | ? → 0 | computable | 100 (by definition) | no: year before 2015 |
| Philip | South Dakota | 2009 | citywide residential | ? → 0 | computable | 100 (by definition) | no: year before 2015 |
| Sandusky | Michigan | 2021 | citywide residential | ? → 0 | computable | 100 (by definition) | no: no permit row |
| Somerville | Massachusetts | 2025 | citywide residential | ? → 0 | computable | 100 (by definition) | no: year after 2024 (permit data end 2025) |
| Spokane | Washington | 2024 | citywide residential | ? → 0 | computable | 100 (by definition) | yes (1 after-year) |
| Westmoreland | Kansas | 2007 | citywide residential | ? → 0 | computable | 100 (by definition) | no: year before 2015 |
| Albuquerque | New Mexico | 2018 | TOD/transit area | ? → 0 downtown and in TOD zones; reductions in centers/corridors | partly | from data; fallback 25 if data fail | yes |
| Ann Arbor | Michigan | 2021 | TOD/transit area | ? → 0 | computable | from data; fallback 25 if data fail | no: inside the 2022 citywide repeal's before-window (staged) |
| Atlanta | Georgia | none | TOD/transit area | ? → 0 | computable | from data; fallback 25 if data fail | no: no date |
| California (statewide) | California | 2023 | TOD/transit area | ? → 0 | computable | from data; fallback 25 if data fail | separate study: owned by the CA AB 2097 thread; not pooled here unless Ryan asks |
| Charlotte | North Carolina | 2019 | TOD/transit area | ? → 0 | computable | from data; fallback 25 if data fail | no: no own permit row |
| Chicago | Illinois | 2015 | TOD/transit area | B/C/D district residential table → 50% by right within 1/4 mile (1/2 mile on Pedestrian Streets); up to 100% by special use | partly | from data; fallback 25 if data fail | yes |
| Denver | Colorado | 2018 | TOD/transit area | ? → 0 | computable | from data; fallback 25 if data fail | yes |
| Hayward | California | 2011 | TOD/transit area | ? → 0 | computable | from data; fallback 25 if data fail | no: year before 2015 |
| Honolulu | Hawaii | 2017 | TOD/transit area | ? → unknown | fallback | fallback 25 (assumption) | unsure: parking change not verified |
| Madison | Wisconsin | 2023 | TOD/transit area | ? → 0 (maximum 1.5 per unit) | computable | from data; fallback 25 if data fail | yes |
| Minneapolis | Minnesota | 2015 | TOD/transit area | ? → 0 for 3-50 units; halved above 50 | computable | from data; fallback 25 if data fail | no: inside the 2021 repeal's before-window (staged) |
| Newark | New Jersey | none | TOD/transit area | ? → 0 | computable | from data; fallback 25 if data fail | no: no date |
| Oregon (CFEC, statewide rule) | Oregon | 2023 | TOD/transit area | ? → 0 near frequent transit; 1/unit cap for multifamily | computable | from data; fallback 25 if data fail | option: a state-rule study like AB 2097 (no owner) |
| Penndel | Pennsylvania | 2020 | TOD/transit area | ? → reduced (amount unknown) | fallback | fallback 25 (assumption) | yes (fallback dose) |
| Portland | Oregon | 2003 | TOD/transit area | ? → 0 | computable | from data; fallback 25 if data fail | no: year before 2015 |
| Portland | Oregon | 2018 | TOD/transit area | ? → unknown | fallback | fallback 25 (assumption) | unsure: parking detail unknown |
| Salt Lake City | Utah | 2010 | TOD/transit area | ? → 0 core; 50% transition | partly | from data; fallback 25 if data fail | no: year before 2015 |
| San Diego | California | 2019 | TOD/transit area | ? → 0 | computable | from data; fallback 25 if data fail | yes |
| Seattle | Washington | 2012 | TOD/transit area | ? → 0 | computable | from data; fallback 25 if data fail | no: year before 2015 |
| Somerville | Massachusetts | 2019 | TOD/transit area | ? → 0 | computable | from data; fallback 25 if data fail | yes |
| Spokane | Washington | 2023 | TOD/transit area | ? → 0 | computable | from data; fallback 25 if data fail | staged: overlaps the 2024 repeal's window; join as one event or the other |
| Albany | New York | 2017 | district | ? → 0 in MU-DT and on lots under 5,000 sq ft | partly | from data; fallback 10 if data fail | only if the exemption date is confirmed |
| Columbia | South Carolina | 2021 | district | ? → 0 in DAC, MC, NAC, CAC, RAC, MU-1, MU-2 | computable | from data; fallback 10 if data fail | yes |
| Covington | Kentucky | 2020 | district | ? → 0 in 10 of 16 primary districts; several housing types exempt elsewhere | computable | from data; none given (broad district; ask Ryan) | yes |
| Fremont | California | 2015 | district | ? → 0 | computable | from data; fallback 10 if data fail | yes |
| Bloomsburg | Pennsylvania | 2024 | commercial-only | ? → 0 in MX-1 | fallback | fallback 10 (assumption) | yes (1 after-year) |
| Camden | Maine | 2021 | commercial-only | 2 per unit → 0 in B-1 and B-TH | partly | from data; fallback 10 if data fail | yes |
| Lewisburg | Pennsylvania | 2023 | commercial-only | ? → 0 in Downtown Commercial | fallback | fallback 10 (assumption) | yes |
| North Canton | Ohio | 2023 | commercial-only | 2 enclosed per unit (Ch. 1133); 1 (Ch. 1135) → unchanged outside Main Street districts | fallback | fallback 10 (assumption) | yes, if the Main Street exemption is new in 2023 (else dose 0) |
| Pomona | California | 2019 | commercial-only | ? → 0 for first two floors in MU-CBD/MU-I | partly | from data; fallback 10 if data fail | staged with the 2024 cut; join one |
| Watertown | New York | 2023 | commercial-only | 1 per unit → 0 in D, C, UMU, NMU, PC, P&OS; R keeps 1/unit | partly | from data; fallback 10 if data fail | yes |
| Waukegan | Illinois | 2024 | commercial-only | ? → 0 in B4; reduced in L1-L3 | partly | from data; fallback 10 if data fail | yes (1 after-year) |
| Bangor | Maine | 2024 | reduction | 1.5 → 1.0 | computable | 33 (ordinance) | yes, once the effective date is confirmed (1 after-year) |
| Binghamton | New York | 2024 | reduction | ? → reduced; 0 for senior/affordable | computable | from data; none given for reductions (ask Ryan) | only if effective in 2024 (else 2025: too late) |
| Boise | Idaho | 2023 | reduction | old Title 11 table → Modern Zoning Code table; 0 in MX-5/downtown | computable | from data; none given for reductions (ask Ryan) | yes |
| Pomona | California | 2024 | reduction | ? → 0 for first 3 units, then 1 per unit | partly | from data; none given for reductions (ask Ryan) | staged with 2019; join one |
| Shoreline | Washington | 2022 | reduction | ? → cuts up to 50% with demand management | fallback | fallback 25 (assumption) | unsure: may fail the optional-reduction screen |
| Tulsa | Oklahoma | 2024 | reduction | old Ch. 55 table → ZCA-25 table | computable | from data; none given for reductions (ask Ryan) | yes (1 after-year) |
| New York City | New York | 2016 | other (affordable/senior only) | ? → 0 for affordable/senior in Transit Zone | computable | 0 (by definition) | no: affordable-only (fails screen) |
| Los Angeles | California | 2017 | other (incentive tied to affordable units) | ? → reductions by tier | computable | from data | no: optional incentive tied to affordable units (fails the partial-reform screen) |
| Norman | Oklahoma | 2021 | other (multifamily only) | apartment table (ratios not coded) → recommended only; 1-2 family keep 2/unit | computable | from data | yes |
| Brainerd | Minnesota | 2023 | other (non-residential only) | ? → residential kept; new minimums added in Town Center and Main Street | computable | 0 (by definition) | yes as a dose-0 check; negative dose if Ryan wants increases coded |
| Seabrook | New Hampshire | 2019 | other (non-residential only) | ? → unchanged for housing | computable | 0 (by definition) | yes as a dose-0 check (adds nothing to a through-origin slope) |
| Wilmington | North Carolina | 2021 | other (non-residential only) | ? → unchanged outside CBD/historic | computable | 0 (by definition) | no: no permit row |
| Eureka | California | 2019 | other (unit-count and district exemptions) | ? → 1 per unit default; first 4-8 units exempt by district; small units exempt | fallback | fallback 10 (assumption) | unsure: staged steps, pick a year |
| Dover | New Hampshire | 2015 | other (weak repeal) | 2010 site-plan table minimums → maximums; Planning Director sets a minimum per project; 3-4 family keep 2/unit | fallback | fallback 15 (assumption) | yes (fallback dose; low confidence) |
| Jackson | Tennessee | 2021 | other (weak repeal) | ? → demand estimate approved by Planning (ITE or study) | fallback | fallback 15 (assumption) | yes (fallback dose) |
| Maumee | Ohio | 2020 | other (weak repeal) | 1 per bedroom (multifamily); 2 per 1-2 family → same numbers renamed maximums; fewer needs Zoning Administrator discretion | fallback | fallback 15 (assumption) | yes (fallback dose) |

### 11.3 The 88 entries with no usable reform

Listed in the CSV with the reason (51 no date found, 20 no minimums before, 17 no dated housing reform). They can't join.

## Changes after writing

(none yet)

## Ryan's choices (2026-11-12 16:31:12 UTC, cmsg_01C3Z6G8h32D4UwCcjcGMM7q4365kbjpRFj6rsC56u2uz8: "okay" to the proposed picks)

These go to the audit before any count.

- **C1. Ryan's 2026-11-04 stop on map coding:** reopened for this test.
- **C2. Coverage:** share of the place's homes (2020 blocks). Share of land zoned for apartments is reported as a check.
- **C3. Fallback doses:**
  - Broad mapped districts: 25.
  - Citywide reductions whose old and new tables are not yet coded: 50 until they are.
  - Ryan's other fallbacks are unchanged: TOD 25, weak repeal 15, commercial-only 10, no repeal 0.
- **C4. Citywide repeals that followed an earlier partial reform:** the dose is the increment (what that repeal removed), not 100.
- **C5. Partial-reform places in comparison pools:** pools are left as they are. Dropping those places is a check.
- **C6. The 6 near-benchmark places with discretion left:** dose 100, as in today's sample.
- **C7. Brainerd (added minimums):** reported alone, not pooled.
- **C8. Central Falls (reversed in 2025):** kept, flagged.
- **C9. Two-step reforms (Pomona, Spokane):** the event is the first step that touched housing.
- **C10. Census blocks:** 2020 boundaries for all places.
- **C11. Display:** a sensitivity row beside the headline, not the headline.

**Status:** locked pending audit. Map coding and dose computation may start, because they read no outcomes. No effect is computed until the audit clears the plan.

**C11 amended (Ryan, 16:31:36 UTC, cmsg_01C3Z6G8h32D4UwCcjcGMM7qPd32REjtrj3L7AXp4W2aFq):** "reserve the right to make this the headline if it says something clear and useful, and we just have to be transparent about how we got here."

- The default stays a sensitivity row.
- To keep a headline switch from being chosen after seeing the result, the dose estimate **may be offered as the headline only if all of these hold**. They are set now, before any count:
  1. The dose-proportional check passes: the 90% range of (full-repeal-only estimate − low-dose-only estimate) includes 0.
  2. Its 90% range is narrower than the 74-place range for the same outcome.
  3. No pre-trend label is on, using Test 56's lead and placebo-date rule applied to the dose estimate.
  4. Its result is not driven by fallback doses: with fallback doses dropped, the estimate keeps the same sign, or keeps a range including 0 if the main result's does.
- If all four hold, Ryan decides. The tool and the write-up then say that the headline was switched after the result, and why.
- If any one fails, the dose estimate stays a sensitivity row.

**Ryan go (16:33:27 UTC, cmsg_01C3Z6G8h32D4UwCcjcGMM7qPm2E6o1f1WAc7nHqrxMKSp):** "when you get the okay from audit run these tests". He also wants the result explainable whatever it shows, and notes the benchmark policy could be changed (for example TOD only, or small cities only) and tested separately.

## Audit fixes (16:33 UTC review of a87a1d50 / c66db18 / 3977f76). These override the text above.

1. **Power of condition 1.** Before any effect, the MDE of the gap (full-only minus low-dose-only) is reported, as 2.486 × the SD of the gap's placebo draws. If that MDE is wider than the full-only estimate's 90% range, condition 1 is labelled **"passed, low power"**. That cut is a convention.
2. **Condition 2 is near-automatic.** More places narrow a through-origin range even when the doses are wrong. The condition is kept, and the write-up says this.
3. **Which outcome can switch.** Each outcome is judged on its own: all homes against the 74-place all-homes line, and 2–4 units against Test 56. All four conditions must hold under **both** main and D.
4. **Condition 4 reworded.** With fallback doses dropped, the reading must be unchanged under both methods. That means the same verdict, and, where the range excludes 0, the same sign.
5. **C10 is partly post-treatment.** For 2015–2019 reforms, 2020 blocks count homes built after the reform. Ryan's pick is kept and labelled. A check recomputes the doses from 2010 blocks for the 2015–2019 transit and district places.
6. **Doses frozen before any effect.** The full dose table, including fallbacks and the C3 placeholder 50s, is committed with its sha256 before any effect is computed. Any dose coded later is a sensitivity only.
7. **Identity check first.** With all 74 places at dose 100, the estimator must reproduce today's averages. This runs before the C4 increment doses are applied.
8. **C5 label.** Leaving partial-reform places in the comparison pools lets a place be both treated and a comparison, which pulls effects toward 0. This is labelled, and the drop-from-pools run is the check.
9. **Condition 3 defined in code before any count.** It covers:
   - the dose-fit leads (years −5 to −2, reference −1);
   - placebo dates −2 and −4, using the same through-origin fit on lead or shifted-date effects.
   
   The pre-trend label is on if any lead or placebo date excludes 0 under both methods.
