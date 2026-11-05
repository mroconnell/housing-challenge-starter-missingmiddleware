# Parking causal framework: locked plan

Owner approved the framework on 2026-11-03 at 01:03 UTC ("send that off to the parking session and let's go for the
gold"). The learning thread's draft is `learning/parking_causal_framework_plan_v0.md` (project library). Its last two
sections, Ryan's answers of 00:58 and 01:02 UTC, override the earlier draft text where they differ. This file is the
locked version, written **before the first count of any test below** (2026-11-03). Anything chosen after seeing a
result is labelled *post hoc* and shown beside the locked version. Nothing in the tool changes from these tests without
Ryan's OK. Stage 2 (carrying results to Wisconsin) stays unlocked until Stage 1 is done and Ryan has reviewed it.

## The law to model: P-c, every piece matched to a real example

| Piece | What it does | Real examples with data |
| --- | --- | --- |
| P-b, near transit and jobs | No parking minimums within ½ mile of frequent transit or in job centres | California AB 2097 (2023); Minneapolis 2015; Seattle frequent-transit areas (2012, 2018) |
| P-a, citywide multifamily | No minimums for buildings of 2+ homes, citywide | Buffalo 2017, Minneapolis 2021, St. Paul 2021, San Jose 2022, and the other 76 repeal places |

- **Data-first rule (Ryan, 2026-11-03):** a piece of the Wisconsin law stays only if it matches a real example with data. A piece without one is dropped, or shown only as a labelled sensitivity.
- **City size:** no cutoff. Size is tested as a trait (moderator M3 below). Wisconsin cities smaller than every evidence place are flagged "extrapolated".
- **ADUs:** excluded, so there is no double count with the ADU scenario.
- **Combined view with TOD:** on (owner, 2026-11-03). Where both laws cover a lot, the TOD effect counts first; parking adds only what TOD's effect does not already contain.
- **Wisconsin today** (checked 2026-11-03, `reference/parking_reform_taxonomy.csv`):
  - Madison has no minimums in its Central District and several mixed-use and TOD districts. A citywide multifamily repeal is only recommended (2024 Housing Affordability Report).
  - Milwaukee has none downtown (C9A) or in redevelopment districts, a 25% cut near bus stops, and no minimums for 1–2 family homes.
  - West Allis, La Crosse, Franklin, Fitchburg and Cottage Grove have removed them for all housing.
  - The state law's added effect is therefore partial in these places. Stage 2 must account for that.

## Shared rules (all tests)

- **Size classes (Ryan):** mid-sized = 2–4 homes; large = 5+ homes. These match the Census Building Permits Survey (BPS). A 5–19 vs 20+ split needs city project lists, so it is done only where they exist.
- **Lot-size thresholds:** where lot data exist (the edge-test cities), thresholds come from natural breaks in homes against lot acres (Jenks breaks, k = 3), not picked by hand.
- **Outcome:** additional homes. Affordability appears only as a labelled tornado sensitivity in Stage 2 ("$X cheaper per home → Y% more homes, Y from an outside supply-response figure → Z homes").
- **Places:** the 76 repeal places of the expanded comparison (`reference/parking_expanded_effects.csv`), with the same matched comparison places and windows (5 years before; 1–3 after). A place is dropped only by a rule written here.
- **Intervals:** 90%. Report per place where the test is per place, the pooled estimate, the leave-one-place-out range, and the **minimum detectable effect** beside every result (1.645 × the standard error of the pooled estimate).
- **Outputs:** summaries in `reference/parking_causal_*.csv`; no addresses or parcel ids.

## Stage 1 tests (locked before counting)

### F1. First stage: did projects build less parking after repeal?

- **Estimand:** parking spaces per new home in projects approved after a repeal, against before; by year since repeal.
- **Data, feasibility first:**
  - Minneapolis Planning Commission approvals 2011–2024 (car spaces and homes per project; repeal near transit 2015, citywide 2021);
  - Buffalo after the 2017 repeal (Hess and Rehler 2021: per-project spaces against the old minimum);
  - Los Angeles projects after AB 2097 (`docs/parking/LA_TOC_RESULTS.md`);
  - Seattle SDCI near-transit projects, if obtainable.
  Feasibility passes for a city with 20+ projects on each side of the repeal.
- **Reading rule:** "binding" if the after mean of spaces per home is below the before mean, with the 90% interval of the difference (bootstrap over projects) below 0.
- **Ramp vs floor (Ryan):** by year since repeal. If the drop keeps growing, builders were timid. If it levels off above 0, a lender floor is at work.

### H1. Bigger buildings: homes per new 5+ unit building (intensive margin)

- **Estimand:** change in homes per new 5+ unit building after repeal. A difference-in-differences: the place's after minus before, minus the same for its matched comparison places.
- **Data:** BPS place files 2012–2025, `5plus_units ÷ 5plus_bldgs`, pooled over each window. Places with no 5+ building in either window are left out of H1 and counted.
- **Pooled estimate:** weighted by the place's 5+ buildings in both windows. Percent change = pooled difference ÷ the pooled before level.
- **Reading rule:** "supported" if the 90% interval (2,000 resamples of places) is above 0.

### H2. More buildings by size (extensive margin), read together with H1

- **Estimand:** change in new 2–4 unit buildings, and in new 5+ unit buildings, per 1,000 existing homes a year. Same difference-in-differences and comparison places as H1.
- **Reading rule:** each class reported with its 90% interval; "supported" for a class if its interval is above 0.
- **Reading H1 and H2 together:** more mid-sized buildings can lower the average 5+ building size. So H1 and H2 are always shown side by side, never one without the other.

### E1. AB 2097 triple difference (direct effect at a line)

- **Groups:**
  - inside vs outside ½ mile of a major transit stop (`data/raw/ab2097/major_transit_stops.geojson`);
  - before (permits 2018–2022) vs after (2023–2025);
  - 2–4 home projects (not eligible for California's density-bonus parking relief, which needs 5+ homes) vs 5+ home projects.
- **Data:** HCD annual progress report Table A2 (`data/raw/hcd_apr_a2/tablea2.csv`). These are project rows with unit category, permit year, latitude/longitude and density-bonus fields. The 185 jurisdictions are those of the AB 2097 test, with places that removed minimums earlier dropped, as in that test.
- **Main estimand:** for 2–4 home projects (no earlier relief), the change in homes permitted per year inside the line against outside, per 1,000 existing homes in each zone. The triple difference (2–4 minus 5+) is reported beside it.
- **Sensitivity:** 5+ home projects that did not use the density bonus (`DENSITY_BONUS_TOTAL` = 0) as their own group. The density-bonus field is filled for most rows; the parking-reduction field for few, so it is not used.
- **Reading rule:** the main estimand's 90% interval (2,000 resamples of jurisdictions). A pre-trend check runs 2018–2020 against 2021–2022 with the same contrast; the result is "balanced" if its interval includes 0, otherwise reported but flagged.
- **Lot size:** where a city's parcel layer is on disk, lot-acre breaks per the shared rule; otherwise not used.

### E2. Repeal alone vs repeal inside a zoning rewrite

- **Groups:** the 76 places split by `simultaneous_rewrite` (taxonomy coding, already on file). A "rewrite only" group (zoning rewrite with no parking repeal) has no list on file. It is a feasibility step, and the 2×2 is completed only if 10+ such places can be coded from PRN and news without looking at outcomes.
- **Reading rule:** the difference between "repeal alone" and "repeal + rewrite", with its 90% interval.

### T. Transit × repeal 2×2 ("invest in both")

- **Groups:** repeal places and their comparison places, each split by "good transit": a rail or bus rapid transit stop inside the place (National Transit Map stops on disk). This gives 4 cells.
- **Estimand:** the repeal effect with good transit minus the effect without (the interaction), with its 90% interval.

### M. Moderators (pre-registered; four, because Ryan named them)

| Moderator | Coding |
| --- | --- |
| M1 | Old minimum level, spaces per home (`reference/parking_old_minimums.csv`; places without a coded value left out of M1) |
| M2 | Repeal alone vs rewrite (= E2) |
| M3 | City size, log existing homes, continuous (Ryan: tested as a trait, not a cutoff) |
| M4 | Good transit (= T) |

- **Reading rule:** a moderator is "material" only if its interval excludes 0 on held-out places (5-fold by place, seed 20261103).
- **Multiple tests:** four are tested, so one false "material" in four is plausible. This is stated beside the results.

### R. Ramp (event study)

- **What it shows:** the effect by year since repeal, k = 1–5, as in the existing event path.
- **Use:** described only, with the number of places at each year.

### H3. Bunching at the old minimum (feasibility only)

- **What it needs:** project-level required and built parking.
- **Feasibility:** passes if 2+ cities have 50+ projects on each side. If it passes, report the before share at exactly the minimum and the after share, with affordable projects as their own group.

### H4. Market floor

- A stated assumption, not a test: lenders and buyers still want parking.
- Used in Stage 2 to keep the high case from assuming parking falls to zero.

## Run order

1. H1 and H2 (BPS; data in hand).
2. E1 (HCD A2; data in hand).
3. F1 feasibility, then F1.
4. E2 and T.
5. Moderators M1–M4.
6. R.
7. H3 feasibility.
8. Report Stage 1 to Ryan and the audit.
9. Stage 2, after Ryan's review.

## Changes after writing
- **2026-11-03, T and E2 implementation details (decided before their first count):**
  - **"Good transit"** means at least one stop from the National Transit Map rail-stop extract on disk (`data/raw/tod_census_cases/ntm_rail_stops.json`: light rail, streetcar, subway, commuter and intercity rail) inside the place's 2024 Census boundary (place, or county subdivision for town-type permit offices). That boundary is the place's ACS geography; joins use `missing_middleware/geom.py`. Bus rapid transit is not in this extract, so it counts as "no rail". That is a narrower test than the locked wording, stated rather than changed.
  - **T, per place:** the repeal place's difference-in-differences is recomputed with its matched comparison places restricted to those with the same transit status, when at least 5 remain; otherwise all comparison places are used, and that is counted. The interaction is the home-weighted mean effect for repeal places with rail minus the mean for those without, with its 90% interval (2,000 resamples of places, stratified by group).
  - **E2:** the main outcome (permits per 1,000 existing homes a year, `parking_expanded_effects.csv`) and H1 are each split by `simultaneous_rewrite`. The difference is "repeal alone" minus "repeal + rewrite", with its 90% interval. Building the "rewrite only" group is deferred as feasibility; until then the 2×2 is incomplete, and that is stated.
- **2026-11-03, T result handling (after its first run, a mechanical fix):** one repeal place (South Bend) has no comparison place with a computable rate, so its matched effect is blank. It is left out of T and counted in the note. No estimate was chosen by this.
- **2026-11-03, E1 implementation details (decided before its first count, written in `scripts/run_parking_causal_e1.py`):** jurisdictions are TOD's 185 (group P); inside = under ½ mile of a major transit stop, outside = ½ to 1½ miles in the same jurisdiction (TOD's comparison zone); Los Angeles's 2017 transit-oriented upzoning areas are left out of both zones; existing homes from TOD's cached 2020 census counts; TOD's cleaning rules plus dropping a permit re-reported in a later year; permit year = year of `BP_ISSUE_DT1`, else report year; homes-weighted main, equal-weight beside it; paired resamples across size classes.
- **2026-11-03, E1 post hoc:** after the first count, late reporting was found to cut off the after years when permits are dated by issue date (18–24% of 2018–2022 homes first appear in a later report; about 0% for 2025). A report-year dating sensitivity (TOD's rule) is added and labelled *post hoc*. Which dating is main is Ryan's call; both are shown.
- **2026-11-03, F1 feasibility (before any before/after mean):** Minneapolis passes (Planning Commission approvals sheet compiled by A. Schieferdecker, 2011–2025: 2015 transit cut 120 projects before / 433 after; 2021 citywide repeal 430 / 123). Seattle passes on row counts but parking sits in free-text descriptions, so it needs a validated parser. Buffalo fails (16 projects before). St. Paul, Anchorage and Duluth have no project list. F1 counting rules, fixed before counting: projects with 5+ homes; rows flagged "Later Resubmitted" keep only the latest submission of the same address; downtown rows (no minimum before either repeal) are shown separately and left out of the main 2021 contrast; split dates are the ordinances' effective dates; the xlsx is read with a standard-library reader (no new dependency).
- **2026-11-03, M and R implementation details (decided before their first count):**
  - **M1 and M3 (continuous):** for each of 5 folds of the 76 places (seed 20261103), the split point is the home-weighted median of the moderator in the other 4 folds; each held-out place is labelled "high" or "low" by it. The moderator's held-out contrast is the home-weighted mean effect of "high" minus "low" over all held-out places, with a 90% interval from 2,000 resamples of places stratified by label. "Material" if that interval excludes 0. The full-sample weighted slope is shown beside it, described only.
  - **M2 and M4 (binary):** the label does not depend on training folds, so the held-out contrast equals E2 and T; they are reported from those tests.
  - **R:** for each place and each year k = 1-5 after repeal with BPS data, the one-year rate minus the before-window rate, minus the same for its matched comparison places (all comparison places, as in the main estimate). Home-weighted mean by k, with the number of places at each k. Described only.
- **2026-11-03, owner allows plan changes ("feel free to push back and change the plan"), POST HOC additions after Stage 1:**
  - M3 also with an unweighted median split (39 large vs 37 small), because the home-weighted split put only 6 places in "large".
  - T also without Austin and Minneapolis (the two rail places with the largest weight × effect), and unweighted.
  - Limits stated rather than fixed: T covers rail only (no BRT in the stop data); F1 rests on one city; E2's rewrite-only group is not built.
- **2026-11-03, audit fixes (audit/parking_causal_stage1_review_2026-11-03.md):** E1 is labelled a re-check of the AB 2097 test; issue-date dating stays main, with the bias direction stated; F1 adds downtown as a comparison group and is labelled "suggestive, single source" until 20 random rows are checked against city records; the M3 weighted split stays main; T gets a leave-one-place-out range.
- **2026-11-03, F1b (added with owner's OK to change the plan; locked before counting):** Minneapolis 2015 cut, inside vs outside the areas it covered.
  - Projects: same rows and rules as F1 (5+ homes, latest submission, downtown left out).
  - Locations: each address geocoded with the US Census Geocoder (public, no key); unmatched addresses are counted and left out.
  - Zones: the 2015 ordinance's transit areas as the city mapped them (or, if no map exists, the ordinance's distance rule applied to the high-frequency network of 2015). The source is recorded before any project is placed.
  - Estimand: (inside after minus before) minus (outside after minus before) in car spaces per home, before = up to 2015-04-30, after = 2015-05-01 to 2021-05-13. 90% interval from 2,000 resamples of projects within each of the 4 cells.
  - Reading: "binding" if the interval is below 0. The F1 downtown comparison stays beside it.
- **2026-11-03, more mid-sized and large repeal cities (owner: "grab the mid sized cities and more large cities"), locked before coding:**
  - Candidates: Parking Reform Network places rated at or near the benchmark (`parking_reform_taxonomy.csv`: rm_min, city) with 25,000+ people, not yet checked (35 places), whose adoption year is 2015-2024 or unknown.
  - Coding: same fields and rules as `parking_repeal_checks_expanded.csv` (in force, applies to all housing, adoption and effective dates, prior partial reforms, simultaneous zoning changes, benchmark check), from ordinances and news only, without looking at permits. Written to `reference/parking_repeal_checks_v2.csv`.
  - Kept if the checked rating is "at" or "near" and the effective year is 2015-2024 (at least one after year in the permit data).
  - Use: Stage 1 tests (H1/H2, E2, T, M1-M4, R) are rerun on the 76 places plus the new ones and shown beside the 76-place results. The tool's numbers keep using the 76 places unless Ryan approves a change.
- **2026-11-03, F1c Seattle (second city for F1; locked before counting):**
  - Data: SDCI land-use permits (data.seattle.gov ht3q-kdvx, public domain); new housing projects with 5+ homes; canceled and withdrawn rows dropped; one row per address (latest application).
  - Parser: homes from `HousingUnitsAdded`, else the description ("N units", "N-unit", "N small efficiency dwelling units"); car spaces from "parking for N vehicles", "N parking spaces/stalls", "no parking" = 0; number words read. Rows without both numbers are left out and counted. 50 random parsed rows are hand-checked against their descriptions before any mean is computed; the parser passes if 45+ are right.
  - Zones: Urban Centers and Urban Villages (Seattle Planning GIS, "Urban Centers and Villages Growth Monitoring"); the Downtown and Uptown/South Lake Union center-city areas are left out (no minimum before either reform). Outside = the rest of the city.
  - Splits by application date: 2012 reform 2012-06-01, 2018 reform 2018-05-01 (approximate; council action May 2012 and April 2018).
  - Estimand and reading as F1b: (inside after minus before) minus (outside after minus before), car spaces per home, for each reform. Caveat stated: descriptions give the whole project's parking, including shops.
- **2026-11-03, E2 completed as a 2×2 with TOD's place list (`reference/tod_places_for_parking_2x2.csv`, commit eaf0898; locked before counting):**
  - "Rewrite only" = TOD upzoned places with an upzoning year 2013-2024 that are not among the 76 repeal places and whose parking at the upzoning was "no", "partial" or "unknown" (no removal coded). That gives 11 places, which passes the 10+ rule. Places whose upzoning came with parking removal ("yes") are reported apart as "upzoning + station-area parking removal".
  - "Neither" = the matched comparison places, as in every other test; the comparison pools exclude the 76 repeal places, the benchmark repeal list and all 38 TOD upzoned places. TOD's 67 "neither" candidates are not needed as a separate cell, because each cell's effect is already measured against places that did neither.
  - Each rewrite-only place's effect is the same difference-in-differences as the main estimate (permits per 1,000 existing homes a year, 5 years before, up to 3 after, `cmp.controls`), with the upzoning year as the event.
  - Interaction = (repeal + rewrite) − (repeal alone) − (rewrite only), home-weighted cell means, 90% interval from 2,000 resamples of places within each cell.
  - Caveat stated: TOD upzonings are mostly station-area rezonings, while the "rewrite" in repeal places is often citywide. The cells measure different kinds of rezoning.
- **2026-11-03, audit round 2 (post hoc additions, main results unchanged):** E2 2×2 marked below the 10-place rule, with an equal-weight sensitivity; F1c gets a 2009 start for the before window and the yearly share of projects with no car parking.
- **2026-11-03, F1b decisions after building inputs, before any F1b parking mean:**
  - Split date: the 2015 ordinance (2015-Or-061) took effect 2015-07-18 (adopted 2015-07-10). F1's rule says splits are the ordinances' effective dates; 2015-05-01 was an approximation. F1b uses 2015-07-18. F1's 2015 contrasts are rerun with it, and the earlier figures are kept beside them as a correction.
  - Zones: the city's June 2015 map "Residential Off-Street Parking Requirements", digitised and fitted to the city boundary (`scripts/fetch_parking_mpls_zones.py`).
  - Outside = all non-downtown land not covered, including the University Area overlay, which kept its own minimum (½ space per bedroom) and was excluded from the cut by name. A sensitivity drops University Area projects.
  - Unmatched addresses (23 of 359 eligible projects) are left out and counted. The 22 projects within 33 m of a zone edge stay in the main result; a sensitivity drops them.
- **2026-11-03, audit round 3:** F1b also shown at the locked 2015-05-01 split. For the 4 added cities, H1/H2, T, M1, M2/M4 and R are not rerun: the cities are 5% of the places, two have one after year, and M1 needs uncoded old minimums. Only the averages, E2 and M3 were rerun.
- **2026-11-03, T data fix and bus rapid transit (owner asked; decided before the recount):**
  - The rail-stop file used for T (`data/raw/tod_census_cases/ntm_rail_stops.json`) covered only 41 agencies fetched for TOD's case cities. Rail cities were mislabelled "no rail" (e.g. Cambridge MA, Beaverton OR). T and M4 are rerun with the national National Transit Map stop layer, all stops served by light rail, streetcar, subway or commuter rail (`data/raw/parking_transit/ntm_rail_stops_national.json`, 12,452 stops, 72 agencies). Amtrak is not in that layer, so Amtrak-only cities count as no rail; stated.
  - "Good transit" (the locked wording: rail or bus rapid transit) adds BRT: places with a BRT line (dedicated stations and branded all-day frequent service) open before the repeal year, hand-coded from agency opening dates: Hartford CT (CTfastrak, 2015), Richmond VA (GRTC Pulse, 2018), Eugene and Springfield OR (EmX, 2007), Birmingham AL (Birmingham Xpress, 2022). Results are shown for rail only and for rail or BRT; rail or BRT is the main version, as locked.

## Stage 1 follow-ups from Ryan's theory chat (owner OK 2026-11-03 02:15; all *post hoc* to the Stage 1 results; locked before each count)

- **FU1, apartment-share matching.**
  - Each repeal place's comparison pool (`cmp.controls`, unchanged) is narrowed to places whose before-window share of permitted homes in 5+ unit buildings (BPS `5plus_units ÷ units_total`, pooled over the before window) is within ±10 percentage points of the repeal place's.
  - If fewer than 5 remain, the 5 nearest by share are used, and that is counted.
  - Same outcome, windows and difference-in-differences as the main estimate.
  - Results: home-weighted and equal-weight averages, each with a 90% interval from 2,000 resamples of places, beside the main −1.14 / +0.42. A one-line year-effect check is also reported: the mean before-window 5+ share of repeal places against their matched places, before and after narrowing.
- **FU2, Austin against Sun Belt boom peers.**
  - Comparison set, fixed before counting: the principal cities of Dallas, Houston, San Antonio, Fort Worth, Phoenix, Nashville, Atlanta, Tampa, Orlando, Jacksonville and Las Vegas, as found in the BPS place files.
  - Any city among the repeal places or on the benchmark repeal list is dropped.
  - Same windows (2018–2022 before; 2024–2025 after) and outcome. Austin's effect is reported against the pooled set, with each peer's own before/after rates.
- **FU3, Seattle edge test at the urban village boundaries (counting homes).**
  - Difference in discontinuities: lots just inside vs just outside urban village / urban center boundaries, (after − before) homes per 100 lot acres a year, around the 2012 reform (before 2007–2011, after 2013–2017; 2012 left out).
  - Center City (Downtown, Uptown, South Lake Union) and manufacturing/industrial centers are left out.
  - Method follows TOD T3 (`docs/tod/CAUSAL_FRAMEWORK_PLAN.md`, Test 2): ratio of sums within the band (main); 91 m (300 ft) main band, 46 m and 183 m sensitivities; 25 m donut; before-window balance check; 400 m boundary segments with lots on both sides; cluster bootstrap over segments, 1,000 draws, seed 20261103.
  - Lots and permits come from TOD's Seattle case files (`data/raw/tod_cases/seattle`). Caveat stated: urban villages also had different zoning, but that is constant across the reform. The difference in differences removes it unless zoning changed at the boundary in the same years.
- **FU4, double machine learning (optional).** Effect of repeal on the place-level change in permits per 1,000 homes, partialling out the before-window 5+ share, job growth, census region and before-window growth. Cross-fitted, 5 folds by place, seed 20261103, random-forest nuisance models (scikit-learn). Repeal places against all comparison-pool places, each at its own window. Run only after FU1–FU3.
- **2026-11-03, FU4 timing:** FU4 has no dependency on FU3, so it runs while FU3 runs (owner: "run concurrently when you can"); its rules are unchanged.
- **2026-11-03, FU audit fixes:** FU2 adds Nashville (in the permit files as "Nashville-Davidson"; it was on the locked list but missed by the name match). FU4 inputs differ from the locked wording, logged here: census division is used for "region" (finer), and the before-window trend and event year were added to "prior growth"; 6 repeal places lack a control and are left out (named in the results).
- **FU5, apartment-only outcome (owner OK 2026-11-03 02:29; post hoc; locked before counting).**
  - The main city difference-in-differences (same 76 places, comparison places and windows) with the outcome narrowed to homes permitted in 5+ unit buildings (BPS `5plus_units`).
  - Two denominators:
    - (a) existing homes in 5+ unit buildings (ACS 2024 5-year B25024, units in structure 5–9, 10–19, 20–49, 50+);
    - (b) all existing homes, the main denominator.
  - Home-weighted and equal-weight averages, each with a 90% interval from 2,000 resamples of places. Shown beside the total-homes headline, which stays the headline because narrowing can hide substitution between building types.
- **FU6, single-family near-placebo.**
  - The same comparison with homes permitted in 1-unit buildings (BPS `1unit_units`) per 1,000 existing homes as the outcome.
  - Called a near-placebo, because single-family homes can have minimums too.
  - A clearly non-zero result (90% interval excluding 0) is read as a sign that the method picks up market swings.
- **FU7, lot-size bands on the lot table** (San Francisco, Buffalo, Chicago, Seattle; `scripts/run_parking_lot_cities.py` data and outcome, net new homes per 1,000 lots a year, pinched minus comparison change).
  - Per city, Jenks natural breaks with k = 3 on log lot acres over all of the city's lots in the test, giving small, middle and large bands. The breaks are computed by an exact Fisher–Jenks fit on 1,000 quantile points (standard library and numpy only).
  - Each band's effect has a 90% interval from 2,000 resamples of 500 m grid cells, the existing test's clustering.
  - Pooled bands: band k = the equal-weight mean across cities of each city's band k, with leave-one-city-out results.
  - The October 0.1-acre split is shown beside it for reference.

## Stage 2 plan: carrying Stage 1 to Wisconsin (locked 2026-11-03, before any Stage 2 count)

Agreed between the parking and learning threads in two rounds (learning draft v0, `learning/parking_stage2_plan_v0.md`). Owner: "go back and forth with the learning session and, when you've agreed, move on to stage 2" (2026-11-03 02:47). No tool change without Ryan's OK.

1. **Law.** No minimum off-street parking may be required for any housing, statewide. This is the tool's law (`MODEL_AND_ASSUMPTIONS_PARKING.md`), covering every Wisconsin permit office (cities, villages and towns).
   - **Logged change:** P-c (near transit plus citywide for 2+ homes) is retired. The 76 evidence places were coded "at benchmark" on this same all-housing rule, so the data-first rule is met.
   - Near-transit only (P-b) is a described sensitivity, not a line. ADUs are excluded.
2. **Places already reformed.**
   - "At" places get 0, as now. "Near" places also get 0 in the main lines (new).
   - The full-rate version for "near" places is shown as one sensitivity figure in the doc.
   - Madison and Milwaukee keep the full rate, with a "may overstate" note: their reformed districts are a small share of homes, and no partial fraction is invented.
3. **Lines.** Central 0, low and high as computed now (−15,326 / +19,937 before item 2), recomputed only for item 2. Two-sided, no floor.
   - Low-end wording: "the data can't rule out a drop this size."
   - Note beside the high end: "about 27,700–49,700 in the improvement rounds (IMPROVE_R1, IMPROVE_R2)".
4. **One pre-chosen trait (sensitivity only).**
   - **Trait.** Excess-parking cost as a share of home value = max(0, old minimum − 0.6) × cost per space ÷ ACS 2024 median home value.
   - **Old minimum:** spaces per apartment, from `reference/parking_old_minimums.csv` for evidence places; places without a coded value are left out, as in M1. For Wisconsin, the Mankato 16-city comparison (`run_parking_mechanism.MINIMUMS`); other Wisconsin places get the median of the 16, flagged.
   - **Market floor:** 0.6 spaces per home, one constant: the after-repeal level in Minneapolis (0.63) and Seattle reform areas (0.59).
   - **Excess:** where the old minimum was below 0.6, the rule did not bind, so excess = 0.
   - **Cost per space:** reuses the cost chain's central values: structured $40,950 (midpoint of $29,900–$52,000) if the place's ACS median home value is at or above the US median, else surface $5,750 (midpoint of $1,500–$10,000).
   - **Test.** 5 folds by place, seed 20261103. Main estimate (permits per 1,000 existing homes a year) regressed on the trait with home weights, against the plain home-weighted average. Error = home-weighted mean absolute error on held-out places.
   - **Kept only if** the trait's held-out error is strictly below the plain average's on the same places; otherwise not shown. It is expected to fail, because M1 (old minimum alone) was not material. The test is reported either way.
5. **Beside the lines (labelled, not lines).**
   - Cost chain on the tornado chart: +581 homes (233 to 1,257), "if each home is about $9,900 (3.9%) cheaper".
   - "Bigger projects only" (18,972) moves into the how-it-works text only, with the contradiction stated: it assumes the number of buildings holds, but that number fell 35%.
   - How repeal works:
     - Projects build less parking than the old rule required, but how much of the fall the reform caused is unclear. Zero-parking projects appear only where the rule was lifted (Seattle).
     - Bigger 5+ unit buildings: +37% (H1, 42 places) and +43% (mechanism, 38 places), with fewer of them.
     - Lot-size gains in Seattle and Buffalo, reversed in Chicago and absent in San Francisco.
6. **Combination with TOD.** Additive, with no interaction bonus; TOD counts first where both apply (as built).
7. **After launch.** West Allis (2022) and La Crosse (2024) are already in the evidence. Later Wisconsin repeals are added when two full years of permits exist, and the average is recomputed.

**Run order:** (0) this lock; (1) trait test; (2) item 2 recount and side figures; (3) wording; (4) Ryan reviews before any tool change.
- **2026-11-03, Stage 2 run log (audit):** the lock was committed at 02:48:10 UTC. `run_parking_stage2_trait.py` and `run_parking_stage2_near.py` were written after that commit and run once each, in the minutes that followed; the outputs reported are those first runs. No evidence place had an old minimum below 0.6, so the 0.6 floor never set excess to 0. Owner OK for the tool change: "okay" (02:50), covering the new lines −15,234 / 0 / +19,818 and the wording.

## Natural experiments N1–N4 (locked 2026-11-03, before any count; agreed with the learning thread, owner: "run the three two steps")

**Running count of parking tests.** 23 in this framework since 2026-11-03: H1, H2, E1, F1, F1b, F1c, E2, the E2 2×2, T, M1–M4, R, FU1–FU7, the Stage 2 trait test, and the station-area description. Adding N1–N4 makes 27. Earlier rounds (the comparison, placebo and lot tests) came before these and are not in the count.

**Shared rules**
- Each test reports its 90% interval and the minimum detectable effect (MDE).
- "Supported" requires all three:
  - the 97.5% interval excludes 0 (Bonferroni: 10% across these four tests);
  - balance passes (the before-window gap's 90% interval includes 0);
  - the sign matches the prediction written here.
- Seed 20261104; 2,000 resamples unless stated.
- Feasibility: at least 20 projects, lots or places on each side of each comparison. Below that the result is "not feasible" and no estimate is reported.
- Nothing in the tool changes without Ryan's OK.

**N1. Oregon's state rule (CFEC, OAR 660-012), intent-to-treat**
- **Treated:** every city in the 8 covered metro areas (Portland metro, Salem-Keizer, Eugene-Springfield, Albany, Bend, Corvallis, Grants Pass, Medford-Ashland), whatever it chose. The list is verified against OAR 660-012 before counting. Portland is dropped, because it repealed in 2021–22 before CFEC.
- **Event:** 2023 (parking rules effective 2023-01-01).
- **Outcome:** permits per 1,000 existing homes a year, the main difference-in-differences. Before window 2018–2022, after 2023–2025.
- **Main comparison:** Washington places matched at ½–2× population (`cmp.controls` logic restricted to Washington). Any Washington place with its own parking repeal or cut in the windows (taxonomy rm_min or reduce_min with a 2018–2025 date, e.g. Spokane 2024) is dropped.
- **Second comparison:** Idaho, same rule. Uncovered Oregon cities are a descriptive third comparison.
- **Prediction:** more homes (effect > 0).
- **Reading rule:**
  - N1 re-uses the covered cities that are also among the 76, so it is not a second vote.
  - For those cities, N1's estimate is set beside their 76-place estimate. If the two are close (difference inside N1's 90% interval), city self-selection is not driving the 76-place result. If N1 is clearly higher, self-selection was biasing the 76 toward zero.

**N2. Minneapolis step 2, first stage only**
- **Data:** the approvals sheet and the 2015-zone tags (F1b).
- **Groups:** newly treated in 2021 = outside the 2015 covered areas (University Area included); already treated = inside.
- **Estimand:** (outside 2021-05-14 to 2025 minus outside 2016-01-01 to 2021-05-13) minus (the same for inside), in car spaces per home, 5+ home projects, downtown dropped.
- **Prediction:** negative (fewer spaces where minimums newly lifted).
- **Interval:** 2,000 resamples of projects within the 4 cells.
- **Balance:** the same contrast for 2011–2013 vs 2014–2015, before either reform. This is coarse.
- **Homes outcome:** not tested. Shown only as descriptive, labelled "confounded by the 2040 plan" (built form districts effective 2021-01-01).

**N3. San Diego 2019 transit priority areas (TPA), feasibility first**
- **Line:** the same TPA line as AB 2097 and TOD's San Diego case, at an earlier date.
- **Dates:** application date if the permit layer has one; otherwise issue date, flagged.
- **Windows:** before 2016-01-01 to the 2019 effective date; after, from the effective date to 2020-11-30 (before Complete Communities).
- **Method:** TOD T3 edge test at the TPA line: 91 m band (46 and 183 m), 25 m donut, balance, bunching. Outcome is homes per 100 lot acres a year.
- **Prediction:** positive.
- **Feasibility:** 20+ lots with new homes on each side within 183 m.

**N4. New York 2016 Transit Zone (ZQA), feasibility first**
- **Rule:** to verify in ZR 25-25 and Appendix I. No parking for new income-restricted affordable and affordable senior homes inside the Transit Zone, effective 2016-03-22.
- **Outcome:** HPD "Affordable Housing Production by Building" homes by start date, inside vs outside the Transit Zone line, within 183 m.
- **Windows:** before 2014–2015 (short; stated), after 2017–2019.
- **Prediction:** positive.
- **Downtown Brooklyn's 2013 text amendment** is noted but not a separate test.
- **Philadelphia:** not clean (its remapping bills change parking and density together).

**Run order:** N2, N1, then N3 and N4 feasibility.

## Work session: denominators, subsets, grid, combination and backtest (locked 2026-11-03, before any count; agreed with the learning thread)

Owner: "conduct a session where the parking thread tests through each idea, fits them, works on data, fits them again until they're clean, then considers if it would make sense to combine different choices" (2026-11-03 13:56). The shared rules of N1–N4 apply: 90% and 97.5% intervals, MDE, balance where defined, at least 20 per side, seed 20261104. **Running count: 27 + grid + S1 + B1 + combo + backtest = 32.** Nothing in the tool changes without Ryan's OK.

- **D1, log change in apartment permits.**
  - Each place and its pooled comparison places: log(mean yearly 5+ unit permits + 0.5), after minus before. Effect = place minus comparison.
  - 0.5 is added for every place, so none is dropped, and the number of places with zero counts is reported.
  - Weights as the main estimate.
- **D2, per 1,000 existing homes in 5+ unit buildings.** Already run as FU5a; reused, not recounted.
- **S2, longer after-windows.** The 38 places with 3 after years (event years 2016–2022).
- **The grid.** {all 76, S2} × {per 1,000 existing homes, D1, D2}, six versions, all reported.
  - **Common unit.** Each version's held-out prediction for a place (the mean of the other places' effects, home-weighted) is converted to permits per 1,000 existing homes a year:
    - D1 via the place's before-window 5+ permit rate: exp(effect) − 1 times that rate;
    - D2 via the place's existing 5+ homes ÷ all existing homes.
  - **Error.** Home-weighted mean absolute error against the place's actual effect in that same unit.
  - **Selection.** A new main version must have lower held-out error than both "predict zero" and the current main version, on the same places. S2 versions are compared on S2 places only.
  - If an S2 version wins, the plan reports how its Wisconsin line would change when applied to all eligible homes. S2 chooses which evidence to use, not which Wisconsin places get the effect.
  - N1's intent-to-treat estimate is also run through the winning version.
- **S1, transit-area and district-only reforms.** Feasibility first.
  - **Pool:**
    - the 26 district-only or weaker cities from `parking_repeal_checks_v2.csv`;
    - Seattle 2012, Minneapolis 2015 and San Diego 2019;
    - CFEC near-transit cities not among the 76.
    - Portland 2002 is before the permit window, so it is out.
  - **Kept:** a place with a mapped reform area, lot or geocoded permit data, and 3+ after years.
  - **Design:** TOD T2/T3 at the station-area or edge scale, in homes per 100 lot acres a year. Otherwise citywide, labelled "diluted".
  - **Rule:** at least 8 places must pass balance, or S1 is descriptive only.
- **B1, multifamily-zoned lots.**
  - In the 4 lot-table cities (FU7 data), the denominator is lots and acres zoned for multifamily inside and outside the reform areas.
  - **Outcome:** net new homes per 100 multifamily-zoned lot acres a year, reform minus comparison change, with intervals from 500 m cells.
  - **Prediction:** positive.
- **Combination with TOD.**
  - **(a) Station-area pairing.** Parking status at the rezoning for TOD's edge-test places is coded from `tod_cases.csv` and `tod_places_for_parking_2x2.csv` before any effect is joined. The comparison is then rerun: removed vs not removed. It stays labelled post hoc, because TOD's edge results are already published.
  - **(b) Combination band.** Built from paired TOD and parking bootstrap draws, if TOD can supply its draws. Otherwise not done.
- **Backtest.**
  - The round-6 boosted-trees no-reform model (`run_parking_no_reform.py`) predicts each repeal place's comparison path. Under D1, the effect is the actual log change minus the predicted log change.
  - It is scored on held-out repeal places in the common unit, against "predict zero" and the main matched comparison.
- **Grid implementation detail (added after the lock; written before the first grid run, committed later in 9cf85ea):** the actual value each version is scored against is the place's measured main effect, in all homes per 1,000 existing homes a year, because that is what the tool predicts. D1 and D2 predict 5+ unit permits only, and other building types are taken as unchanged (FU5 found the total and the apartment change nearly equal). Held-out means leave one place out.
- **2026-11-03, run log (audit):** `run_parking_ne_n2.py` was written after the N1–N4 lock commit (52a6e15) and run once; the reported result is that first run. `run_parking_ws_grid.py` was written after the work-session lock (ffe40cf) and the grid detail line, and run once.
- **2026-11-03, B1 data detail (before counting):**
  - **SF:** comparison lots are all RH-1 (single-family), so it has no multifamily-zoned comparison.
  - **Buffalo:** its lot data carry land use, not zoning.
  - **Seattle:** the lot table's allowed FAR is filled only on upzoned lots.
  - **Chicago:** B1 runs in Chicago only, which is one city and so is described, not "supported". Multifamily-zoned = allowed FAR of 1.2 or more before the reform (RT-4 and denser; Chicago's FAR schedule), from the TOD lot table's `far_before`.
- **2026-11-03, N1 deviation (audit):** the covered list was not checked against OAR 660-012 before the first count. The first run used 45 cities built from MPO membership. DLCD's 48-city table (as of 2023-07-24, saved in `data/raw/parking_natural_experiments/`) was obtained afterwards. N1 was rerun on it (47 after dropping Portland; 39 usable), as the "verify and rerun" step, and both runs are reported.
- **2026-11-03, N1 comparison contamination (audit):** Washington's 2024 and 2025 state laws on parking for middle housing near transit (taxonomy: reduce_min 2024-03-27; rm_min and reduce_min 2025-07-27) partly treat the Washington comparison in the 2023–2025 after window. That pushes N1 toward zero. An after = 2023-only run was optional and is not done.
- **2026-11-03, backtest implementation (before counting):**
  - **Why not reuse the round-6 model as is:** it predicts 5-year totals two years after an origin year, which doesn't match the repeal windows. So the backtest refits the same model family (scikit-learn HistGradientBoostingRegressor) at each repeal place's own windows.
  - **Training units:** every comparison-pool place of every repeal place, at that repeal place's windows, as in FU4.
  - **Target:** log(mean after-window 5+ permits + 0.5) − log(mean before-window 5+ permits + 0.5).
  - **Features:**
    - log(mean before-window 5+ permits + 0.5);
    - log(mean before-window total permits + 0.5);
    - the before-window trend (last 2 years minus first 3, total permits per 1,000 homes);
    - log existing homes;
    - before-window 5+ share;
    - census division;
    - event year.
  - **Fit settings:** seeds 20261104 to 20261108, averaged; the repeal places are never in training.
  - **Each repeal place's D1 effect** = its actual target minus its prediction.
  - **Scoring:** leave one place out in the common unit, against "predict zero" and against the matched D1 version, on the same places.
- **2026-11-03, N3 lock additions (agreed with the learning thread and the audit, before the N3 count):**
  - **Already seen.** Feasibility counts by line were seen before these choices. Counts of lots with new homes rose about 11% inside and 10% outside, a rough first look at the outcome. Stated plainly.
  - **Line.** The main line is the City's ParkingAmenityTPA layer 6 (based on the 2015 regional plan, in force in 2019; edited in 2022–23). TOD's SANDAG 2022 line is a labelled sensitivity.
  - **Coastal Zone.** The Coastal Overlay Zone and boundary segments along it are dropped, because the rule there awaited Coastal Commission certification. The certification date is logged with the result. If it fell before 2020-11-30, coastal lots were treated for part of the window, and the doc says so.
  - **Outcome.** Homes per 100 lot acres a year, all homes, as locked. Projects with 2+ homes are below 20 on the outside (18 before, 16 after), so for them counts only are shown, with no estimate.
  - **Dates.** Application date (the earlier of the project and approval create dates, joined from the City's approvals files) is a change from the locked fallback, logged here. Issue date is a sensitivity.
  - **Density bonus.** Since 2016 the state density bonus (AB 744) has cut parking near major transit for bonus projects on a line close to the TPA edge, weakening the 2019 contrast. If the approvals files flag density bonus use, a "no density bonus" sensitivity is run.
  - **Parcels.** Lot acres come from the public San Diego parcel files already on disk (`data/raw/tod_radius_programs/san_diego/`); their licence is logged. No OpenStreetMap, no shapely or GEOS beyond `missing_middleware/geom.py`.
  - **Checks.** Balance (before-window gap), 25 m donut, 46 / 91 / 183 m bands and bunching, as TOD T3. If balance fails, the result is reported as "fails balance" and not pooled. The MDE is reported beside the result.
  - **After window.** About 19 months (2019-04-24 to 2020-11-30), including early COVID.
  - **Prediction:** positive.
- **2026-11-03, combo (a) detail (before joining effects; post hoc as locked, because TOD's edge results are published):**
  - **Places.** TOD's "original 11" edge-test places, using the main 91 m rows of `reference/tod_causal_edge_expand.csv`.
  - **Parking coding.** Taken from `tod_places_for_parking_2x2.csv`:
    - "removed" = Charlotte, Denver and Portland;
    - "not removed" = New York, Philadelphia, Austin, Chicago, Saint Paul and Salt Lake City;
    - Seattle's two cases are "unknown" and dropped.
  - **Exclusions.** Places failing TOD's balance rule are reported but left out of the comparison.
  - **Statistic.** Equal-weight mean of "removed" minus "not removed", with a place bootstrap and a leave-one-place-out range.
- **2026-11-03, S1 skipped:** only 6 of 68 places are eligible, under the locked 8. The learning thread agreed. S1 stays in the running count.
- **2026-11-03, Chicago lot scope (pending the audit's ordinance check):** no Chicago lot result is used until checked. If the 2015 relief covered only B, C and D districts, B1, FU7 and the October lot test are rerun on B/C/D lots only. That rule will be written here before the rerun.
- **2026-11-03, combo (b) lock (before counting):**
  - **Pairing.** TOD's line draws (`reference/tod_line_draws.csv`) are paired with parking's draws for the same line, by index.
  - **Parking draws.** Lower and upper: the 20,000 placebo set averages, centred on the real average (−1.14) and scaled to Wisconsin eligible homes. Central is 0 in every draw.
  - **Overlap rule (TOD counts first, as built).** Positive parking draws are multiplied by the share of parking's upper addition that falls off TOD-covered lots in the combined bundle (17,819 ÷ 19,818 = 0.899). Negative draws pass through unchanged, as rule (b) does.
  - **Two bands.** Each line reports a 90% band under (i) index pairing, which assumes TOD and parking errors are unrelated (stated beside it), and (ii) sorted pairing, low with low and high with high, the widest case if the errors move together.
  - **Evidence only;** no tool change.
- **2026-11-03, Chicago lot rerun rule (post hoc; written before the rerun; audit confirmed the scope from SO2015-5334, Sec. 17-10-0102-B.1):**
  - **Lots.** Each Chicago lot in the TOD lot table is tagged with its November 2012 zoning class (`data/raw/tod_cases/chicago/zoning_nov2012.zip`).
  - **Reform side.** Lots zoned B, C or D (classes starting B, C or D; not PD) within 402 m of a station. The Pedestrian Street extension to 805 m is not applied, because no 2015 Pedestrian Streets layer is on disk; some treated B/C/D lots at 402–805 m therefore sit in the comparison, which pushes toward zero.
  - **Comparison side.** B, C and D lots at 402–805 m, so zoning classes match.
  - **TOD's density-bonus lots** are kept on the reform side (main), because they also got the parking relief. A sensitivity drops them.
  - **What is rerun.** Outcomes as before: FU7's per-lot rate and B1's per-100-acre rate. B1 also keeps its FAR ≥ 1.2 filter. 90% intervals from 500 m cells.
  - **Wording.** FU7's "does not generalise" leans on Chicago. That is stated beside the rerun.

## T1 non-residential placebo and T2 staggered event-study cross-check (locked 2026-11-03, before any count; owner liked the placebo)

**Running count: 34** (32 + T1 + T2; the Chicago B/C/D rerun is a rerun, not a new test).

- **T1, non-residential placebo.**
  - **Places.** PRN taxonomy entries rated "not_housing" (minimums cut or removed for non-residential uses only), place type city, adoption year 2013–2024. That is the window the permit files allow (5 before years from 2012, at least 1 after). The adoption year is the event year.
  - **Exclusions.**
    - Places that also have a housing-covering PRN entry (rated at, near or weaker) dated within 3 years of the event.
    - Places already among the 76 or on the benchmark repeal list.
    - The list is coded from the taxonomy before any outcome is seen.
  - **Outcome.** The main difference-in-differences (permits per 1,000 existing homes a year, all homes; 5+ unit homes as a second series), with the same `cmp.controls` comparison and windows, and at least 1 after year.
  - **Expected:** about 0.
  - **Pass:** the 90% interval includes 0 (2,000 place resamples, seed 20261104).
  - **Feasibility:** 8+ places with Census permit files, else "not feasible".
- **T2, staggered event-study cross-check (Sun and Abraham 2021, interaction-weighted).**
  - **Units.** Cohorts are the 76 places grouped by event year. The never-treated units are the union of all their `cmp.controls` comparison places, which excludes every repeal place.
  - **Panel.** 2012–2025 place-years. Outcomes: permits per 1,000 existing homes a year, and log(yearly permits + 0.5).
  - **Estimation.** Two-way fixed effects (place, year), with cohort × relative-year dummies for leads −5 to −2 and lags 0 to 3. Relative year −1 is the reference; leads beyond −5 are binned into the earliest lead. Estimated by OLS after a two-way within transformation; standard errors clustered by place.
  - **Aggregation.** Each cohort's lags 1–3 are averaged with weights equal to each cohort's share of treated place-years, giving one post effect, beside the main −1.14. The leads are reported as a pre-trend check. Home-weighted and unweighted versions are both shown.
  - **Role:** a cross-check, not a replacement.

## Pre-trend follow-ups P1–P3 (locked 2026-11-03, before any count; from the learning thread after T2)

**Running count: 37.** Evidence only. Ryan's lines don't change without his OK.

- **P1, short before window.** The main matched difference-in-differences (76 places, the same `cmp.controls` comparison, after years and weights), with the before window cut to years −2 and −1 only. The interval comes from 2,000 place resamples, seed 20261104.
- **P2, matching on before-trend as well as level.**
  - **Slope.** Each place's before-window slope is the OLS slope of its yearly permits per 1,000 homes on year, over years −5 to −1 (as available).
  - **Controls.** From each repeal place's `cmp.controls` pool, keep the 10 places with the nearest slope (all of them if fewer than 10). Effect and interval as in the main estimate.
  - **Pre-trend check.** The same matched comparison with "after" = years −2 to −1 and "before" = years −5 to −3. It passes if the home-weighted mean's 90% interval includes 0.
- **P3, bound in the spirit of honest DiD** (hand-written; no GPL packages; relative-magnitude form, M = 1).
  - **Before-window gaps.** From the main matched comparison, the home-weighted place-minus-comparison gap in each before year, relative to year −1.
  - **G** = the largest absolute gap.
  - **Bound.** [main p05 − G, main p95 + G], reported beside the main estimate.
- **Pass rule.** If P1 and P2 both move the central estimate toward 0 or above, and P2's pre-trend check passes, the result goes to Ryan as a candidate low-line update. Otherwise the lines stand, and the pre-trend issue is noted in the how-it-works text.
- **2026-11-03, Chicago scope (audit sweep):** the locked Stage 2 text "Lot-size gains in Seattle and Buffalo, reversed in Chicago and absent in San Francisco" rests on a mis-scoped Chicago lot test. The 2015 relief covered B/C/D districts only, and its Pedestrian Street reach was in the 2015 ordinance itself. On B/C/D lots Chicago is still negative, but its range includes 0. The locked text is left as written; the tool's wording waits for Ryan.
- **2026-11-03, T1 run log (audit):** the coded list (`reference/parking_t1_coded.csv`) was produced by the same script run, and in the same commit, as the result. Its coding rules come only from taxonomy columns; no outcome is read before the list is fixed.
- **2026-11-03, Chicago B/C/D with home and acre denominators** (owner: "we can still use Chicago, we just need to make sure that we have the right denominator based on how many homes or residential acres existed in the business districts"; post hoc; written before the run):
  - **Sample.** Same B/C/D lots as the B/C/D rerun (reform within 402 m, comparison 402–805 m, Nov 2012 zoning, density-bonus lots kept).
  - **Outcomes,** both as (after − before) reform minus comparison:
    - net new homes per 1,000 existing homes on those lots a year (`units_before`);
    - net new homes per 100 lot acres a year, over all B/C/D lot acres.
  - **Interval:** 90% and 97.5%, from 2,000 resamples of 500 m cells.
  - **Counts as a rerun,** not a new test.
  - **Timing (stated plainly):** this rule was written into the plan file before the run but committed together with the result. It is post hoc in any case, because the B/C/D result (−6.24) had been seen.
  - **Pedestrian Streets (learning thread):** B/C/D lots on Pedestrian Streets 402–805 m from a station were treated in 2015 and sit in the comparison band. No 2015 Pedestrian Streets layer is on disk, so this is "not fixable" for now. Every Chicago B/C/D result carries that contamination, which pushes toward zero.
  - **Use:** Chicago stays a lot-level side result. It is not in the 76 and does not feed a tool line without Ryan's OK.
- **2026-11-03, test 35 closed: not feasible as a parking test** (agreed with the learning thread).
  - Culver City's border lies mostly inside LA's AB 2097 zones (21% usable) and has 2 lots with new homes inside the line after the repeal.
  - San Jose's lots are mostly ADUs, whose parking state law already caps; it has 14 / 13 non-ADU lots inside before / after.
  - No descriptive San Jose run.
  - Recheck Sacramento and Mountain View when 2027 permits exist.

## C1 count model and C2 building counts (locked 2026-11-03, before any count; owner: "No harm in running the negative binomial version of the Poisson and also trying a small version with building counts instead of homes")

**Running count: 39** (37 + C1 + C2; test 35 counted, and closed as not feasible). Evidence only; the tool lines don't change.

- **C1, count model of new 5+ unit buildings.**
  - **Stacked design.** One stack per repeal place: that place plus its `cmp.controls` comparison places, each with two periods (the place's before and after windows, as in the main estimate).
  - **Outcome.** Count of new 5+ unit buildings (BPS `5plus_bldgs`) summed over each period.
  - **Offset.** log(existing homes × years in the period).
  - **Model.** Negative binomial GLM with unit-by-stack fixed effects and stack-by-period fixed effects. The treatment term is repeal place × after.
  - **Overdispersion.** α is chosen by maximum likelihood on a grid (0.05–5).
  - **Reference.** A Poisson version with the same terms is reported beside it.
  - **Weights.**
    - Main: none.
    - Second version, weighted by series steadiness: 1 ÷ (1 + coefficient of variation of the unit's yearly before-window 5+ building counts), so steadier places count more.
  - **Inference.** Standard errors clustered by repeal stack.
  - **Report.** Rate ratio (exp of the coefficient) with 90% and 97.5% intervals.
  - **Prediction:** above 1. "Supported" only if the 97.5% interval excludes 1.
- **C2, building counts in the main design.** The main matched difference-in-differences (76 places, same comparison, windows and weights), with the outcome changed to new buildings of all sizes per 1,000 existing homes a year (BPS 1-unit + 2-unit + 3–4 unit + 5+ unit buildings). 90% interval from 2,000 place resamples, seed 20261104. Prediction: above 0.
- **C1/C2 additions from the learning thread (before any count; my lock kept, its checks added):**
  - **C1 series.** Run on three outcomes:
    - new 5+ unit buildings (main);
    - homes in 5+ unit buildings;
    - all homes.
    Each in negative binomial, with Poisson beside it. 2–4 unit buildings are shown beside the main.
  - **Checks:**
    - **(a) Pre-trend:** the same stacked model with "before" = years −5 to −3 and "after" = years −2 to −1. Its 90% interval should include 1.
    - **(b) Single-family placebo:** new 1-unit buildings as the outcome. Its 90% interval should include 1.
    - **(c) Fake reforms:** T1's 31 non-residential places, with their own comparison pools, as fake reforms. Their 90% interval should include 1.
  - **Pass rule.** "Supported" only if all three hold:
    - the main 97.5% interval excludes 1 (stricter than the tutor's 90%, matching N1–N4);
    - placebos (b) and (c) include 1;
    - pre-trend (a) includes 1.
  - **Reporting.**
    - Places dropped for all-zero counts.
    - The MDE (1.645 × SE on the log scale).
    - The rate ratio converted to permits per 1,000 existing homes a year at the before-period mean.
  - **Intervals.** From stack-clustered standard errors. A 2,000-draw place bootstrap was proposed but would need 2,000 negative binomial refits with thousands of fixed effects, so it is not run (stated).
- **2026-11-03, C1/C2 final rules (replace the C1/C2 design above; agreed by Ryan with the learning thread, 25% bar chosen 15:36:54 UTC; tests 38 and 39; written before any count):**
  - **Setup.**
    - Units: the 76 repeal places plus the union of their matched pools.
    - Panel: 2012–2025 place-years.
    - Offset: log existing homes.
    - Fixed effects: place (concentrated out) and calendar year.
    - Treatment: repeal place × years after its event, within its after window. A repeal place's years outside its before/after windows are dropped.
    - Output: rate ratios.
    - Width: a 2,000-draw place bootstrap (seed 20261104). Refits are warm-started, and the negative binomial α is held at its full-sample value (stated).
    - Fitting: statsmodels-style negative binomial and Poisson, with a hand-written IRLS on the small year/treatment design.
  - **Versions, listed before running:**
    - **38a:** homes in 5+ unit buildings, negative binomial (Poisson beside).
    - **38b:** all homes, negative binomial (Poisson beside).
    - **39:** new 5+ unit buildings, negative binomial (2–4 unit buildings beside). Shown beside the lines, never as the lines.
  - **Conversion (rule 1).** (rate ratio − 1) × Wisconsin current-law permits in eligible places for that outcome, 2027–2031: 46,905 for 5+ homes; all homes from the Stage 2 path. Other building types are taken as unchanged, as in the grid.
  - **Order of checks.** All of rules 1–5 are required, so they are checked cheapest first: width (rule 5), then pre-trend and placebos (rule 4), then calibration (rule 3) only for a version still passing.
    - **Calibration:** 200 fake-reform draws, each giving random event years from the real ones to comparison places, with the same windows. Each draw's interval uses a 199-draw place bootstrap. Pass if 85–95% of the 90% intervals cover a rate ratio of 1.
  - **Rule 4 checks** use stack-clustered standard errors, not the bootstrap (stated):
    - pre-trend leads −5 to −2 against −1;
    - single-family homes;
    - T1's non-residential places as fake reforms.
    Each must include 1.
  - **Replacement bar (rule 5).** The 90% Wisconsin-homes width must be 26,289 or less. All versions are reported either way. Any change to the tool needs Ryan's OK.
- **2026-11-03, C1/C2 lock additions (learning thread; before any count):**
  - **(a) Candidates, fixed now:**
    - C1 negative binomial on 5+ unit homes;
    - C1 Poisson on 5+ unit homes;
    - C1 negative binomial on all homes.
    C2 (buildings) is reported beside the lines and can't become them.
  - **(b) Blind run.** Phase 1 prints, for each candidate, only:
    - its bootstrap width in Wisconsin homes;
    - its calibration coverage;
    - pass/fail on the pre-trend and placebo checks.
    No centres. The narrowest candidate passing all rules is chosen and that choice is committed. Only then does phase 2 print the centres of every version.
  - **(c) Places.** The same 76 places, pools and windows; no trimming.
  - **(d) Disclosure.** An earlier C1/C2 run (stacked design, before these rules) was started and stopped within about a minute, at the hold. It printed nothing and wrote no file, so no result was seen.
- **2026-11-03, 38/39 choice (committed after the blind phase, before any centre was printed):** no candidate passes all rules, so none is chosen and the lines stand.
  - **C1 negative binomial, 5+ homes:** fails width (40,415) and pre-trend.
  - **C1 Poisson, 5+ homes:** passes width (22,814) but fails pre-trend and the T1 placebo.
  - **C1 negative binomial, all homes:** fails width (47,967) and pre-trend.
  - **Calibration:** not run, because no candidate reached it.
  - **Next:** phase 2 now prints the centres of every version for the record.

## Tests 40 (power simulation) and 41 (two-year imputation estimator) (locked 2026-11-03, before any count; owner: "yeah okay, let's do those")

**Running count: 41.** Evidence only. The lines change only if a result meets the locked 25% rule (rules 1–6 of 38/39).

- **40, power check.**
  - **Fake reforms.** In each of 200 simulations (seed 20261104), draw 75 never-repealed places from the union of the real pools without replacement. Give each a fake event year drawn from the real event years, with the same windows (5 before, up to 3 after, as available).
  - **Comparisons.** Each fake place's comparison pool is `cmp.controls`, excluding the real 76, the benchmark list and the other fakes.
  - **Injection.** Extra permits are added to each fake place's after years, at δ permits per 1,000 existing homes a year. δ is sized from Wisconsin gains of G = 0, 5,000, 10,000 and 20,000 homes over 2027–2031 through the Stage 2 path: δ = G ÷ (2,668,677 × 5 ÷ 1,000), so 0, 0.375, 0.749 and 1.499.
  - **Timing profiles,** by year after the event:
    - constant (1, 1, 1);
    - ramp (⅓, ⅔, 1);
    - early-then-fade (1, 1, ½).
  - **Linearity shortcut.** The injection raises only the treated place's after rate, and the matched difference-in-differences is linear in it. So each place's injected effect = its base effect + δ × (mean profile over its after years). Comparison pools are drawn once per simulation, and the full main estimator is computed exactly (stated).
  - **Interval.** The main estimator's 90% interval, from 1,000 cluster resamples. Clusters are counties, because no metro code exists for every pool place (stated).
  - **Report.** Coverage of the true injected effect at each size and profile (the share of 90% intervals containing it), and power (the share of intervals that exclude 0 with the right sign).
- **41, two-year totals, imputation estimator** (Borusyak–Jaravel–Spiess; hand-written, no pyfixest).
  - **Untreated model.** y_it (permits per 1,000 existing homes) = place effect + year effect, fitted on untreated place-years: never-treated pool places in all years, plus repeal places before their event year.
  - **Imputation.** For each repeal place with event + 2 ≤ 2025, the effect is the sum over event years +1 and +2 of (actual − imputed): cumulative permits per 1,000 existing homes over two years.
  - **Aggregation.** Home-weighted and equal-weight means. The share of the 76 places and of their homes covered is reported.
  - **Interval.** 90%, from 1,000 county-cluster resamples.
  - **Leave-one-out.** Leave one city out, and leave one county out as the metro proxy (stated).
  - **Pre-trend.** The model is refitted without the repeal places' years −3 to −1, those years are imputed, and the mean imputed residual must have a 90% interval including 0.
  - **Wisconsin and the 25% rule.** Two-year cumulative ÷ 2 = a yearly rate, converted to Wisconsin homes through the Stage 2 path. The 25% rule needs a 90% width of 26,289 homes or less, plus the pre-trend pass. Calibration (rule 3) is checked only if both pass.
- **2026-11-03, 40/41 additions (audit; before any result):**
  - **40, linearity shortcut.** The shift is added per place inside each resample. Profile means differ by place window (e.g. the ramp is ⅓, ½ or ⅔ for 1–3 after years), and the truth is the home-weighted mean of the per-place shifts.
  - **40, resampling.** The unit resampled is the county cluster of fake places.
  - **40, simulation error.** With 200 sims, about ±2 points on coverage near 90% and ±3.5 points on power near 50%.
  - **40, coverage at G = 0** is compared with the 20,000 placebo sets.
  - **41, rule 4 placebos apply:**
    - single-family homes as the outcome (1-unit homes);
    - T1's non-residential places as fake reforms.
    Both must include 0.
  - **41, year 0.** Year 0 (the event year) is left out of both the effect and the untreated fit.
  - **41, resampling.** Each county resample refits the place and year effects.
  - **41, leave-one-metro-out.** Added as a labelled extra, with CBSA assigned to each of the 76 places by place interior point in the 2024 CBSA boundary file (`data/raw/census_cbsa_cb_2024`).
  - **41, how to describe it if it passes.** "The first two years only, applied to all five", shown beside the event path (+0.02, −1.29, −2.26, −6.50). Two-year totals sit closer to 0 and are narrower partly by construction.

## Test 42 (triple difference by Census size class) and the dose-coding pilot (locked 2026-11-03, before any count; owner OK)

**Running count: 42.** Evidence only.

- **Test 42.**
  - **Outcome.** (5+ unit homes permitted − 1-unit homes permitted) per 1,000 existing homes a year.
  - **Design.** The main matched difference-in-differences on that outcome: the same 76 places, `cmp.controls` pools, windows and home weights. The 1-unit class is the comparison class, consistent with FU6's near-placebo of 0.0. The 2–4 unit class is shown beside it, not used as the comparison.
  - **Interval.** 90%, from 2,000 place resamples, seed 20261104. A metro-clustered version (CBSA by place interior point, as in test 41) is shown beside it.
  - **Backtest.** The same contrast with "after" = years −2 to −1 and "before" = years −5 to −3 must include 0.
  - **Reading.** If land moves between size classes, this measures a relative shift between classes, not added homes.
  - **The 25% rule applies before it could replace any line.**
- **Dose-coding pilot (coding only, not a test; no outcomes read).**
  - **Sample.** 15 of the 76, drawn with seed 20261104, stratified by size tercile (homes) × `simultaneous_rewrite`. That is 6 strata of 2–3 places, allocated in proportion and rounded so the total is 15.
  - **Per place, from the ordinance and the pre-reform code:**
    - required spaces the day before and the day after, for a fourplex, a 20-unit and a 100-unit building on a typical apartment-zoned lot;
    - existing exemptions, waivers and reductions;
    - scope: citywide, areas or project types, plus the share of apartment-eligible land covered where a pre-reform zoning map exists;
    - whether single-family rules changed, and whether they were likely binding;
    - same-time changes to height, density or approvals;
    - hours spent.
  - **Output.** `reference/parking_dose_pilot.csv`.
  - **Closed 2026-11-04 (owner chose "Stop at the pilot", 17:12 UTC).** The dose and exempt-share pilots (15 places) stay as evidence only and feed no line or test. Coding all 76 is not pursued, with no more map coding and no clerk requests. Kingston was finished from public text (no exempt area found). Saranac Lake, Ecorse and Rogers stay not found. See WORK_SESSION_RESULTS.md, "Exempt-share pilot".

## Test 43: do Madison's minimums bind? Bunching in project records, 2015–2022 (locked 2026-11-03, before any count; owner: "go")

**Running count: 43.** Evidence only; Milwaukee is held until Madison shows whether minimums bind.

- **Records.** Madison Legistar "Conditional Use" and planned-development files with 5+ homes in the title, 2015-01-01 to 2022-12-31.
  - The source is each file's Staff Comments PDF, Zoning table: "Required | Proposed", from the auto parking / number of parking stalls row.
  - One record per project: repeat files for the same project (same address, alterations, phases) keep the latest approved one.
- **The rule in force,** coded for each file's date and location before its proposed number is read:
  - Central Area: no minimum since the 2013 code;
  - TOD overlay: from 2023-01-17, so outside this window;
  - planned developments: "per approved plan", recorded as no code minimum;
  - otherwise the district's minimum as stated in the Required cell.
  Only projects with a positive code minimum enter the test.
- **Variables per project:** homes, required stalls, proposed stalls, district, rule, year. No addresses go in any committed file.
- **Shares.** Proposed ÷ required, with three groups:
  - "at the minimum": within 0.05 spaces per home of required;
  - above;
  - below (variance or reduction).
  Also spaces per home.
- **Parser check, before any share is read.** 50 random coded projects (or all, if fewer) are hand-checked against their PDFs. The parser passes at 45 of 50 correct (90%). Below that, every project is hand-checked.
- **Feasibility.** At least 30 projects with a positive minimum and both numbers. The plausible range is 30–120 (audit); if fewer than 30, the result is "not feasible".
- **Prediction (the reading).** If minimums bind, many projects sit at the minimum (bunching). If not, most sit above. The share at the minimum gets a 90% interval from 2,000 project resamples.
- **Stated biases:**
  - by-right projects never appear;
  - projects are mostly large (conditional use is triggered by size or location);
  - the numbers are proposed, not built;
  - projects asking for reductions are over-represented;
  - mixed-use requirements may combine commercial and residential parking.
- **2026-11-03, test 43 additions (learning thread; before any count):**
  - **Files.** All multifamily (2+ homes) conditional-use and site-plan files, 2015–2022, widened from 5+.
  - **Order.** Files are coded in random order (seed 20261104) until there are 30+ projects with a positive minimum and both numbers, or all files are done.
  - **Variance.** Any variance or reduction granted is recorded.
  - **Central Area split.** Central Area projects are reported apart. They have no minimum, so they show spaces per home only.
  - **Repeat files.** Only the last version of each project is kept.
  - **Milwaukee.** No records request.
- **2026-11-03, test 43 audit additions (before any result):**
  1. **Band comparison.** The share within 0.05 spaces per home of the minimum is compared with the share 0.05–0.10 above it. If minimums bind, the first band holds clearly more. This is a comparison, not a pass bar.
  2. **Reduced Required cells.** The code minimum is coded from district and use, and any reduction shown in the Required cell is recorded separately. The test uses the code minimum.
  3. **Parking maximums.** Coded where shown. Projects whose maximum is within 0.25 spaces per home of the minimum are flagged.
  4. **Hand-check.** The 50 checked projects are drawn with seed 20261104. "Correct" means both required and proposed are right.
  5. **Mixed-use projects** (combined requirement) are flagged, and every share is shown with and without them.

## Test 44 (plan only, not run): are single-family homes affected by parking repeal? (written 2026-11-03; owner's question; goes to audit before any run)

**Running count if run: 44.**

- **Step 1, contrast check (done, no outcomes read).** All 76 repeals are citywide. On PRN, 70 cover "all uses" and the other 5 also include residential. The benchmark rule requires all housing, so there are no multifamily-only repeals in the 76 and no scope contrast to test.
- **Alternative, locked: dose of the old single-family minimum.** `parking_old_minimums.csv` codes the old single-family minimum for 50 of the 76:
  - "high" = 2.0 spaces per house (29 places);
  - "low" = 1.0 or less (19 places, including one at 0);
  - the 2 places at 1.5 are left out;
  - places with no coded value are left out.
  - The split is fixed now, by the rule's value, not by results.
- **Outcome.** 1-unit homes permitted per 1,000 existing homes a year, in the main matched difference-in-differences: same pools, windows and home weights.
- **Estimand.** The high-group mean effect minus the low-group mean effect, with a 90% interval from 2,000 place resamples stratified by group (seed 20261104). The overall 1-unit effect is shown beside it. FU6 already reported +0.00 (−0.83 to +0.76).
- **Prediction.** If single-family minimums bound, the high group gains more single-family homes than the low group (difference > 0).
- **Pass rule.** "Supported" only if the 97.5% interval excludes 0 with a positive sign, and a backtest (years −2 and −1 vs −5 to −3, same contrast) includes 0. Otherwise "not supported".
- **What it means for earlier placebos.**
  - If test 44 is supported, single-family homes are not a clean placebo. The single-family checks in 38/39 (passed) and 41 (failed) and FU6 would be partly treatment, not placebo, and test 42's triple difference (5+ minus 1-unit) would subtract part of the effect. Those readings would be relabelled.
  - If it is not supported, the placebo use stands, with this test cited.
- **ADU double counting.** The parking scenario excludes ADUs (Stage 2 item 1), and the ADU scenario models ADU law separately. But the Census permit survey can record a detached ADU as a new 1-unit building in some places. So a 1-unit effect here could partly be ADUs, and adding it to a parking line would overlap the ADU scenario.
  - **Rule:** any single-family effect found stays evidence only. It is not added to the parking lines without Ryan's OK and a check with the ADU thread on how ADUs are counted in BPS for the places involved.
- **2026-11-03, test 44 additions (audit; before running):**
  - **(A) The groups differ by city type.** High includes Austin, San Jose, Raleigh, Durham and Oregon; low includes SF, Minneapolis, Lexington and Buffalo. Added:
    - an equal-weight version;
    - leave out Austin, then Raleigh;
    - a table of both groups by region, size and event year;
    - the same contrast on 5+ unit homes (optional, shown).
  - **(B) MDE.** The MDE is reported. If not supported, the reading is: "the placebo use stands as before, but test 44 can't rule out a single-family effect smaller than the MDE."
  - **Smaller additions:**
    - a version with high-confidence old-minimum codes only;
    - a context line: detached houses usually meet 2 spaces anyway, and townhouses are where the rule more likely bound.

## Tests 45–46: who the comparison places are (locked 2026-11-04, before any count; Ryan's questions 17:20 UTC, relayed by the coordinator)

**Running count: 46.** Evidence and sensitivity only. Neither replaces a line unless it meets the 25% replacement rule; as pool checks they are not candidates.

- **Common set-up.** The 76 repeal places in `reference/parking_expanded_effects.csv` (all homes), each rebuilt with its own script's windows, homes and exclusions (`run_parking_expanded.py`, `run_parking_salvage.py`, `run_parking_partial.py`). The rebuild must match each stored effect to 1e-4 before any new number is read.
- **Test 45, strict pool.** Pools also leave out every city with any record in `reference/parking_reform_taxonomy.csv`: removal or reduction of minimums, any rating (including weaker, not_housing and plan_only), any status. County and state entries are not applied to places. Matching rules otherwise unchanged (state 0.5–2×, then 1/3–3×, then the Census division at 0.5–2× and 1/3–3×, until 5).
  - **Report:** per repeal place, main vs strict pool size; how many repeal places move to a wider window, and which; the home-weighted average (weight homes × after-years) with a 90% place bootstrap (2,000 draws, seed 20261104), beside the main on the same bootstrap. Places left with no pool are listed and left out, and the main is also shown on the same set.
  - **Reading:** "consistent with the main" if the strict average lies inside the main's 90% bootstrap range.
- **Test 46, comparison-place influence.**
  - **Pools saved:** `reference/parking_t46_pools.csv`.
  - **Outliers:** the top and bottom 10% of the 76 effects by rank, 8 each, unweighted.
  - **Per comparison place:** how many repeal places use it, how many of those are outliers, and its mean share of pool homes.
  - **Leave one out:** drop the comparison place from every pool it is in, without re-matching (the pool shrinks), recompute every effect and the weighted average, and list the 10 that move the average most.
  - **Regression (reading only):** outlier flag, and separately |effect|, on log pool size, a widened-window flag, the largest comparison place's share of pool homes, and the absolute comparison change. OLS with robust (HC1) errors, 90% intervals, statsmodels (BSD).
  - **Also shown:** the correlation of each effect with the place's own change and with its comparison change.

## Test 47: do big cities match each other better than same-state cities? (locked 2026-11-04, before any count; Ryan 17:51 UTC)

**Running count: 47.** Evidence only. Ryan's idea: big cities track each other across state lines better than they track same-state cities half to twice their size.

- **Targets.** US places with 250,000+ people (ACS 2020–2024), complete permit years 2012–2025, and not on the main exclusion list (the benchmark repeal list). These are never-repealed cities, so the true effect of a fake repeal is 0. Counted before any outcome: 93 big places, 20 on the list, 72 targets.
- **Two comparison rules for each target.**
  - **Current:** `cmp.controls` as in the main (same state at 0.5–2×, then 1/3–3×, then the division, until 5).
  - **Big-city:** places anywhere in the US at 0.5–2× the target's population, widened to 1/3–3× if fewer than 5, with the same exclusions and complete-years rule.
  - Both rules use the main exclusion list. Ryan's message said "no parking-reform record"; that would leave too few big cities (4,591 cities have a record), so the exclusion matches the main to isolate geography.
- **Score 1, fit over 2012–2025.** RMSE of the yearly gap between the target's permit rate and the pool's pooled rate, after removing the target's mean gap (permits per 1,000 existing homes).
- **Score 2, fake repeals.** Fake repeal years 2017–2021, using the main windows (5 before, 3 after), and the main effect formula.
  - Per target and year: |effect| under each rule.
- **Comparison.** For each target, average its paired differences over the fake years (big-city minus current). Equal weight per target, and home-weighted beside it. 90% range from 2,000 resamples of targets, seed 20261104.
- **Pass rule.** The big-city rule is better if both mean paired differences (RMSE and |fake effect|) are below 0, with 90% ranges that exclude 0. Worse if both are above 0 with ranges excluding 0. Otherwise no clear difference.
- **Follow-up if it is better (locked now).** Rerun the 76 with big-city pools for repeal places with 250,000+ people, keeping everything else as in the main. Report the average and its 90% place bootstrap beside the main. Sensitivity only.

## Method 2: a second way to build the parking estimate (DRAFT LOCK 2026-11-04, before any count; Ryan 18:06–18:15 UTC)

**Status: draft, revised after audit review 1 (18:18 UTC).** Required before the first run: (i) the audit re-checks this lock; (ii) Ryan's choice of the main weighting is written into this section with its time and committed. The run script refuses to start unless that line exists. (iii) Ryan has seen the all-variables trait ranking (with and without SF) and weighed in (Ryan, 18:21 UTC: "don't run method 2 until we get the trait ranking and I weigh in on that"). **Running count: 48** (one locked run, everything reported). Evidence beside the current lines. Any tool change needs Ryan's OK, and replacing a line also needs the 25% replacement rule.

**Why.** Ryan wants to keep the big repeal cities (Austin, Minneapolis, San Francisco) in, compare them fairly, keep reform cities out of the comparison groups, compare like with like (hot with hot, young with young), and weight places more sensibly. These choices are made now, before any method-2 number is seen. The main results (−1.14, test 45) are already known; this is stated plainly.

**Places.** The 76 repeal places in `reference/parking_expanded_effects.csv`, each with its own windows (5 before, up to 3 after) and its own script's special handling (South Bend combined area, trimmed years, 2010 homes for pre-2015 repeals).

**1. Weights (Ryan names the main one before the run).**
- **Ryan's main-weight choice (19:22 UTC):** "the weighting that will best predict the effect of a statewide policy adoption in WI and any other state we load in". It is picked by the weight test below. Ryan confirmed the test and its tie rule at 19:23 UTC ("in the case of a tie, we go with state mix?" … "lock it in"). Hold lifted by Ryan at 19:21 UTC ("let's go!").
- **Weight test (leave one state out; picks the main weight; runs after the bake-off, on the picked heat method's real place effects):**
  - **States:** every evidence state with at least 3 of the 76: Oregon 16, California 7, New York 5, Michigan 5, North Carolina 4, Minnesota 4, Texas 4, Virginia 3, Georgia 3, Maine 3. That is 10 states.
  - **For each held-out state:** build each weighting from the other 66+ places. In this test only, the target-state mix is aimed at the held-out state's repeal places' own homes × after-years in each size band × metro cell, weighted as in the truth (audit). The final Wisconsin estimate still aims at Wisconsin's eligible homes. τ² for random effects is re-estimated without the state.
  - **Prediction:** the weighted mean effect of the other places, after the item 5 winsorising.
  - **Truth:** the held-out state's mean effect weighted by homes × after-years. An equal-weight truth is shown beside it as a sensitivity only.
  - **Score:** mean absolute error across the 10 states, each state counted equally.
  - **Candidates:** (a) random effects, (b) target-state mix, (c) square root of homes, (d) homes, (e) equal.
  - **Winner:** the lowest error, unless the tie rule applies.
  - **Tie rule:** the target-state mix wins if its error is within 10% of the lowest, or if the 90% range of its paired error difference from the lowest includes 0. That range comes from a bootstrap over the 10 states, 2,000 draws, seed 20261104.
  - **Caveat stated now:** 10 states is few, and each state's "truth" is itself noisy, so the tie rule is likely to apply.
  - **Recorded:** the winner and every candidate's errors are committed before the method-2 estimate is reported.
- **Bake-off scoring weight (fixed, because the weight test runs after the bake-off):** random effects, the proposed main. For fake cases, vᵢ is the placebo variance of the real case each fake case is paired with in its stratum. The other weights are reported beside it.
- **(a) Random effects (proposed main).** Weight = 1 / (vᵢ + τ²).
  - vᵢ: the variance of the fake-repeal effects among place i's stand-ins in the full placebo run (`reference/parking_placebo_full_places.csv`), i.e. how noisy a place like i is.
  - τ²: the DerSimonian–Laird between-place spread.
  - Big, steady places count more than small, noisy ones, but no place dominates.
  - τ² is re-estimated in each bootstrap draw.
  - Meaning: random-effects weights estimate "the typical place", not "the average home". A place-level average differs from a home-level one when big and small places respond differently.
- **(b) Target-state mix.** The target state is an input (default Wisconsin; any state FIPS code works, e.g. Tennessee).
  - The target state's eligible homes are split into cells: size band (under 10,000; 10,000–50,000; 50,000–250,000; 250,000+ people) × metro or not. Every permit-issuing unit in the BPS panel is banded by its own ACS 2020–2024 population. This includes Wisconsin's towns, which issue their own permits as minor civil divisions.
    - Metro = the unit's CBSA is a metropolitan statistical area (LSAD M1 in the 2024 Census CBSA file), as in the main traits.
    - Eligible homes = homes outside places that already removed minimums. For Wisconsin that is the 2,668,677 used for the lines; other states use the same rule from the benchmark list.
  - Within each cell, evidence places are weighted by homes. Each cell's total is set to the target state's share of homes in that cell.
  - A cell with fewer than 2 evidence places merges with the adjacent band toward the middle, in the same metro status: the smallest band merges up and the largest merges down. Cells still empty are reported with their share of the target state's eligible homes, and that share is spread over the rest.
  - The effective number of places, (Σw)²/Σw², is reported for each target state. Wisconsin is run, plus Tennessee as a demonstration.
- **(c) Square root of homes × after-years.**
- **Reference only:** (d) homes × after-years (current); (e) equal weights.

**2. Strict comparison pools.**
- **Left out:** every city with any record in `reference/parking_reform_taxonomy.csv`, any policy, rating or status (4,591 matched cities), plus the main exclusions.
- **Widening, one rule for all,** stopping at the first step with at least 10 candidates (see item 3):
  1. same state at 0.5–2× population;
  2. same Census division at 0.5–2×;
  3. nationwide at 0.5–2×;
  4. nationwide at 1/3–3×;
  5. nationwide at any size, nearest 10 on the matching measures plus log population.
- **Big cities:** this lets them find big-city stand-ins out of state, so none drop for lack of a pool. The places that reach step 5 are listed.
- **Every candidate:** must report every year in the window, and must have homes.

**3. Matching on pace and age.**
- **Distance measure** among the candidates at the chosen step, standardised across all US places:
  - before-window permit rate;
  - before-window trend (slope of yearly rates);
  - town age: share of homes built 1990–2009 among homes built before 2010 (ACS 2020–2024 B25034). Every repeal is 2016 or later, so this uses no homes built after any repeal.
- **Distance:** Euclidean distance on z-scores. The z-scores are standardised over all eligible candidates nationwide for the same window.
- **Selection:** keep the 10 nearest (all, if 5–9). Ties are broken by closeness in population, then by key. Step 5 always yields 10, so no place drops for lack of a pool.
- **What this does:** hot markets are compared with hot markets, and young exurbs with young exurbs.
- **Caveat stated:** matching on the before-window rate can bias a difference-in-differences when the two groups come from different populations (regression to the mean). Here it is intended: it makes the comparison places revert the same way.

**3b. Market-heat bake-off (Ryan "okay, do that", 18:19 UTC; picks the heat fix before any real result).** Item 3 is candidate B; the bake-off decides which candidate the real run uses.
- **Candidates:**
  - **A:** size match only. Every candidate at the first ladder step with 10 or more places (item 2), or 10 nearest on log population at step 5.
  - **B:** item 3 (A's step, nearest 10 on before-window rate, trend and town age).
  - **C (hybrid, stated now):** synthetic control for targets with 250,000+ people, B for the rest. Donors are the 50 nearest by population among the strict, shock-screened places nationwide. Non-negative weights summing to 1 are fitted to the target's yearly before-window rates, using up to 10 years before the event, back to 2012.
  - **D:** longer baseline. "Before" = up to 10 years before the event (back to 2012, the first panel year), on both sides, with A's pool. Repeals from 2016–2021 get fewer than 10 years; this is stated.
- **Fake cases:**
  - Never-repealed places under the strict exclusion, shock-screened, with complete permit years.
  - Each gets a pretend repeal year. Cases are drawn to match the 76's mix of event years × size bands (item 1b's bands). They also get the 76's after-year counts.
- **Sets:** 200 fake sets of 76 cases each, drawn with replacement within event-year × size-band strata. Seed 20261104.
  - The number of distinct places in each stratum is reported.
  - If a stratum has fewer than 5 distinct strict-pool places (likely 250,000+), that stratum alone draws from the main exclusion list instead. This is reported.
- **Scores per candidate:**
  - **MAE:** mean absolute set average (true effect 0).
  - **Coverage:** the share of sets whose 90% place bootstrap (500 draws per set) includes 0.
  - **Weighting:** random effects (fixed; see item 1). The other weights are reported beside it.
  - **Coverage error:** each candidate's coverage is reported with its simulation standard error, √(c(1−c)/200), about 2 points.
  - Items 2, 4, 5 and 6 apply to every candidate.
- **Backtest for C:** the synthetic control is refitted on years −5 to −3 only.
- **Limit, stated now:** fake cases have a true effect of 0 and did not choose to repeal, so the bake-off cannot detect bias from cities that repeal just before a boom.
- **Pick:** the lowest MAE among candidates with coverage 85–95%. If none qualifies, the candidate whose coverage is closest to 90%, ties going to the lower MAE.
  - The pick and every candidate's scores are committed before any real-repeal method-2 output is computed. The run script has two stages; stage 2 refuses to start until the pick file is committed.
- **Then:** one real run with the picked candidate, inside the rest of method 2. The other candidates' real results are shown beside it, labelled "not picked".

**3c. Amendment: density, crowding and the shared match (Ryan 19:17 UTC: "include density as a matching trait"; the tutor's spec; written before any method-2 run).**
- **Matching traits, all measured before every repeal** (all repeals are 2016 or later):
  - **crowding:** share of occupied homes with more than 1 person per room, ACS 5-year B25014, for places and county subdivisions.
    - Place-specific vintage: each repeal (or fake-repeal) case uses the latest 5-year file that ends before its event year. A 2016 repeal uses 2011–2015; a 2024 repeal uses 2019–2023.
    - Its comparison candidates are measured on the same vintage.
    - Backtest cases (pseudo-event at year −2) use the vintage ending before their pseudo-event, so a 2016 case uses 2009–2013. Vintages 2009–2013 through 2019–2023 are fetched from the Census API (public domain) into `data/raw/parking_acs_crowding/`, with the key kept out of every file.
  - **density:** log of housing units per square mile of land, 2010 census (Gazetteer HU10 ÷ ALAND_SQMI).
    - No repeal in the 76 is before 2016 (earliest 2016), so the 2010 census is before every repeal.
    - One fixed census count is used for all, rather than a per-case ACS count, because it has no sampling error in small places.
    - Density changes slowly, so a 2010 count ranks places much as a later one would.
  - **town age:** item 3's share of homes built 1990–2009 among homes built before 2010. This is kept instead of "built since 2000", because the latter includes homes built after some repeals (audit review 1).
  - **pre-repeal permitting:** before-window rate and trend.
- **Shared match, held fixed across candidates.** Crowding, density and town age are used in every candidate. Only the heat handling differs, so the bake-off isolates it:
  - **A:** the item 2 ladder; among the candidates at the chosen step, the nearest 10 on crowding, density and town age.
  - **B:** as A, plus before-window rate and trend in the distance.
  - **C:** synthetic control for targets with 250,000+ people; B for the rest.
    - Donors come from inside the population window first: nationwide at 0.5–2×, widening to 1/3–3× if needed.
    - Within that window, the 50 nearest on B's distance are taken (all of them, if fewer than 50).
  - **D:** A's pool, with the 10-year before baseline.
  - This replaces the A and D definitions in item 3b. The scoring and pick rule are unchanged.
- **Distance:** Mahalanobis on standardised traits. The covariance comes from all eligible candidates nationwide for the same window. It is computed inside the population window at each ladder step, with the item 2 widening (state → division → nation). Step 5 adds log population.
- **Ties:** as in item 3.
- **Missing traits:** for a candidate missing a trait, the distance is computed over the traits it has, using the matching block of the covariance. The squared distance is scaled by (traits in total ÷ traits it has), so it is not favoured for having fewer.
- **Reported:** the share of chosen comparison places with any missing trait, and the covariance matrix used at each ladder step.
- **Use:** these are matching traits only. No trait is used to size Wisconsin.
- **Fake cases (item 3b):**
  - fake event years are drawn from 2016–2024 only;
  - all candidates use the same fake cases and the same 200 sets;
  - a fake target is never in its own pool.

**4. Shock rule (objective, outside facts only; applied to comparison places).** A candidate is left out if either:
- **(a)** its housing units fell 10% or more between the 2010 census (Gazetteer HU10) and ACS 2020–2024 (B25002), and it had 1,000+ homes in 2010. The size guard keeps survey noise in tiny places from triggering the rule. This catches places destroyed or largely cleared, such as Paradise, CA (wildfire, 2018).
- **(b)** its land area changed 25% or more between the 2010 and 2024 Gazetteers (large annexations or boundary changes).
- **Places flagged:** the list is reported. In the main version, repeal places that meet either test are flagged, not dropped. A second version also drops flagged repeal places.
- **Timing caveat:** both tests span 2010 to 2020–2024, so they also cover after-years. They use housing-unit counts and boundaries, not permits.
- **Not used:** FEMA disaster declarations, because a declaration alone covers whole counties and most places in them were not hit.

**5. Winsorising.**
- **Comparison places:** each one's yearly permit rate is capped at the 5th and 95th percentiles among that pool's places in that year, in both periods. The pool rate is then the home-weighted mean of the capped rates.
- **Repeal places:** their yearly rates are not capped.
- **Averaging:** the 76 effects are capped at their 5th and 95th percentiles before averaging.

**6. Home counts.** Homes the year before each repeal = ACS 2020–2024 homes minus permits issued from the repeal year to 2024, floored at half (as in improvement round 1). This applies to repeal and comparison places alike, so fast-growing places are not measured against homes built later.

**Report.**
- Each weighting (a)–(e): the average, a 90% place bootstrap (2,000 draws, seed 20261104), and the Wisconsin five-year figure (× 13,343).
- Beside it: the current main, and method 2 with each of items 2–6 switched back one at a time.
- **Backtest:** "before" = years −5 to −3, "after" = years −2 to −1. Pools are re-matched on years −5 to −3 only, so the backtest window plays the role of the full window. Its 90% range should include 0.
- **Also reported:** places left out, cells merged, the shock list, and pool sizes.
- **Percentiles:** numpy's default (linear interpolation), for winsorising and bootstrap ranges alike.
- **Interval caveat:** test 40 found bootstrap 90% ranges cover about 84% of the time.
- **Not in this run:** a placebo-based range for method 2, and a synthetic control for the top-weighted cities. These are offered as follow-ups.

**Where the fixed numbers come from.**
- **10 matched places:** a judgement: enough to average out single-place noise, few enough to stay close matches. (The main pools have a median of 28 places; the 5-place minimum is the main rule.)
- **At least 5:** the main rule's minimum (`cmp.MIN_CONTROLS`).
- **10% home loss:** large enough to exceed normal survey error in places of 1,000+ homes, and small enough to catch disasters and mass clearance.
- **25% land change:** a judgement for "large annexation", set before any list is seen.
- **5th/95th percentiles:** Ryan's choice (winsorize, 5%).
- **2 places a cell:** the fewest that give a within-cell average.
- **Half floor on homes:** improvement round 1's rule.
- **Method 2 run log.**
  - **Inputs:** `reference/parking_acs_crowding.csv`, 727,432 rows, SHA-256 5bdf5fba86fef4b9f2137d97407b23bf0509781574615105a0508c6f04e53484.
  - **Script:** `scripts/run_parking_method2.py`, committed before stage 1.
  - **Weight test truth:** homes × after-years, with an equal-weight truth beside it (sensitivity only).
  - **Wisconsin cells:** built from BPS permit-issuing units (2,220,883 eligible homes in the panel, vs 2,668,677 in the tool's areas). Only the shares are used.
- **Heat method, final choice rule (Ryan 20:00–20:01 UTC, written before the B+D scores were seen):** "It's either D or combo B+D", and "D wins in the case of a tie".
  - B+D (candidate E) replaces D only if, on the same fake cases under random-effects scoring, its MAE is more than 5% lower than D's and its coverage is between 85% and 95%. Otherwise D stands.
  - 5% is the bake-off's own spread: all four candidates sat within about 0.02 MAE, roughly 2%, in every version.
  - C is out (Ryan).

## Method 2 correction and city-size weighting test (DRAFT LOCK 2026-11-04, before any corrected run; awaits Ryan's go and the audit)

**Origin.** Both pieces are post hoc. They follow the method-2 results and the audit's checks (Connecticut matching; Wisconsin cells on 2,668,677). Nothing runs until Ryan says go.

**1. Corrected main (data fixes only).**
- **Connecticut:** units are joined on state + county-subdivision code across all inputs (2010 Gazetteer, ACS 2013–2023 crowding, ACS 2020–2024). That code did not change when Connecticut moved from counties to planning regions in 2022; only the county part did.
- **Before the rerun,** a missing-share table by trait and state is committed (`reference/parking_method2_missing_by_state.csv`). It is there to catch splits like Connecticut's, or Alaska's 2019 borough change.
- **Step 5 reading:** step 5 is "nearest on the measures plus log population", so candidates with no population are excluded there.
- **Unchanged:** the missing-trait rule stays as locked.
- **Wisconsin cells:** built from the tool's 1,925 areas (2,668,677 eligible homes). Metro means the county's CBSA is a metropolitan statistical area (LSAD M1).
- **Same rules otherwise:** stages 1 and 2 are rerun with the same seed. The choice is D or B+D, D wins ties (5% margin), C stays out. The weight test and its tie rule are as locked.
- **Reported:** original and corrected results side by side. The Wisconsin-cells correction alone gives −10,541 homes (−0.79, range −2.80 to +0.40), beside the original −7,012. Effective N is 19.6 vs 30.9.

- **Ryan's go for the corrected run (21:02 UTC):** PROVISIONAL, by the learning thread under Ryan's 21:01 UTC delegation ("if it runs into any blockers, please have the learning thread make a provisional call so that the work can continue without me"); reason given: the audit cleared it, and it fixes a known data error.

- **Ryan's go for the corrected run (15:50 UTC):** "fix canandaigua / remove seabrook / what do you mean about maumee?". This is the go for the batch rerun after the sample fixes, on the corrected method-2 rules.

**2. Sensitivity (labelled, not the main).** Candidates missing any trait the target has are ineligible.

**3. City-size weighting test.** Run on corrected data only, after the corrected weight test. Its results are not seen before this lock is committed.
- **Versions of the target-state mix:**
  - **(i) 4 bands:** under 10,000; 10,000–50,000; 50,000–250,000; 250,000+. This is the main, as locked.
  - **(ii) 3 bands:** cuts at the population terciles of the 76 repeal places.
  - **(iii) Smooth line (an MRP-style version):** each place's effect is fitted with a weighted least-squares line on log population and metro, weighted by homes × after-years. Each target-state place gets a predicted effect, and those predictions are summed using the target state's eligible homes.
  - **(iv) Crowding groups:** three groups at the terciles of the 76 places' pre-repeal crowding, crossed with metro. Crowding is post hoc in origin too: the direction table flagged it.
- **Score:** the leave-one-state-out test, as locked: 10 states, mean absolute error, each state counted equally.
- **Rule:** keep (i) unless another version's error is more than 10% lower and its paired bootstrap range over states (2,000 draws, seed 20261104) excludes 0.
- **Expected:** a tie, given 10 noisy states. The spread across the four is reported either way.
- **If the corrected weight test does not pick the mix,** the size test still runs, as evidence only, and reports its spread. The main weight stays whatever the corrected weight test picks.
- **Smooth line (iii):** predictions are held at the edge of the 76 places' observed log-population range. Many Wisconsin areas are smaller than the smallest repeal place, so they get the prediction at the smallest observed size rather than an extrapolation.
- **Crowding (iv):** Wisconsin's areas use ACS 2019–2023, the latest release fetched. The repeal places use their own pre-repeal vintage (item 3c).
- **Cell merging:** the merge rule (fewer than 2 places in a cell) applies to the 3-band and crowding versions as well.
- **Terciles:** cut points use all 76 places, including the held-out state's. That shares cut points, not outcomes, so it is acceptable.
- **Note on the bands:** the mix's negative lean comes from bands that each cannot be told apart from 0.
- **Order:**
  1. This lock, including the size test, is committed.
  2. The missing-data table is published and checked.
  3. The corrected rerun (stages 1 and 2) runs.
  4. The size test runs.

  No corrected result is seen before steps 1 and 2 are done.
- **Run gate:** the corrected run script refuses to start unless this section has a bullet that starts with Ryan's go, the time in UTC and his words. The format is checked by the script; this sentence does not match it.
- **Pause after the missing-data table:** `--corrected --missing-only` writes the table and stops. The corrected stage 1 refuses to run until that table is committed and unchanged.

## Method 3: prognostic-score matching (DRAFT LOCK 2026-11-04, before any count; Ryan 20:59 UTC: "yeah, okay, ask the parking thread to do that. and consider adding more traits like the TOD thread found")

**Status: draft, revised after audit review 1.** Provisional go by the learning thread (21:04 UTC, under Ryan's 21:01 UTC delegation). It holds only once the audit clears this lock and corrected method 2 has finished; after clearance, only the audit's fixes may be added. This lock is for the plan. A run needs the audit's review and Ryan's go. Its own method, scored by the same fake-repeal rules as the method-2 bake-off.
- **Origin:** post hoc in origin, after method 2's results. It also answers the double-dip note, because traits are chosen and the score is fitted on never-repealed places only.
- **Starting over (Ryan 20:57 UTC):** the score is fitted and checked on never-repealed places only, so that part starts fresh. The choice of method is still post hoc in origin, because method-2 real results have been seen.
- **All places:** every place is included; there are no with/without-San Francisco runs (Ryan 20:59 UTC: "We don't need to run with and without SF. Just include all the places.").

**Order.**
1. The method-2 correction (Connecticut join, missing-data table) runs first, so density and crowding are clean.
2. Then this plan runs, steps 1–6 below.

**Traits allowed** (each measured before the case's event year, so no post-event information):
- **Permit history,** 2012 onward: before-window rate, before-window trend, permit volatility, and the share of permits in 5+ unit buildings in the before window.
- **Size and form:** log population (pre-event homes rule), 2010 census density, metro, and Census division.
- **The parking all-variables traits** (55, `reference/parking_allvars_values.csv` definitions) that exist for any place, measured the same way. Left out: repeal-specific traits that never-repealed places lack (V1, V2 old minimums; V11 repeal year; V12 prior partial reform; V13 rewrite; V14 state share repealed).
- **Census traits from the TOD list** (78 ACS variables across 46 tables) (`reference/tod_allvars_variable_map.csv`, groups housing stock, housing costs, people and households, commuting).
  - Each comes from the ACS 5-year release ending the year before the case's event year, at place or county-subdivision level.
  - Built-year traits are limited to pre-2010 categories. Median-year-built and median-building-age variables are excluded, as are post-2010 bands. The final trait list is reported.
  - Left out: traits needing tract geometry or TOD-only inputs (t-, n- and l03 variables). TOD's transit-specific traits are also left out; the commuting-mode shares (m-variables) are kept, because they describe the place, not a station area.
  - These are fetched from the Census API (public domain; key kept out of every file) for releases 2013–2023, with the same Connecticut join.
- **Missing traits:** gradient boosting uses its own handling. Lasso uses a missing indicator per trait plus the training half's median.

**Steps.**
1. **Split.** Never-repealed places under the strict exclusion, shock-screened and with complete permit years, are split 50/50 at random by place (seed 20261104) into halves A and B. Each place gets pretend event years drawn from 2016–2024, with the same stratified draw as the bake-off.
2. **Fit on A (audit fix, 21:45 UTC):** all event years per place, rather than one stratified draw; CV grouped by place; the B check averaged over rows. Lasso one-hots division, and its inner CV is grouped by place. Built-year traits are stricter than this lock: pre-2000 bands only. The target is each place's permit rate in the after window with no repeal: permits per 1,000 pre-event existing homes a year. This makes the score a prognostic score, the predicted outcome without treatment.
   - Models: gradient boosting (HistGradientBoosting, sklearn, BSD; depth 2, learning rate 0.05, up to 300 iterations with early stopping, at least 5 per leaf) and lasso.
   - The model is chosen by 5-fold cross-validation inside A (seed 20261104), on mean absolute error.
3. **Check on B.** The score's mean absolute error on B is compared with a plain average from A. If the score is not at least 5% better, prognostic matching is dropped. That result is reported, and steps 4–6 are not run.
4. **Fake repeals in B.**
   - **Prognostic matching (P):** the method-2 ladder (corrected), then the 10 nearest on the prognostic score (absolute difference), adding log population at step 5. The heat handling is the corrected method-2 pick.
   - **Today's matching:** the corrected method-2 pick, with the same steps.
   - **Pools for both:** drawn from B only.
   - **Scoring:** as the bake-off (200 sets of 76, random-effects scoring, MAE and 90% coverage with its SE).
5. **Pick (audit clearance 21:10 UTC).** The pick uses the bake-off in B with the A model, as locked. The mirror check (B model on A) is reported only. If the two halves choose different model types, both are reported. P replaces today's matching only if its MAE is more than 5% lower and its coverage is 85–95%. A tie keeps today's matching. The pick is committed before any real-repeal output, with the same code gate as stage 1.
- **Cross-fitting (audit, required):** a second model is fitted on B, chosen and checked the same way with A as its check half. A places are scored with the B model, B places with the A model, and real repeal places with the average of the two models. Every place's score therefore comes from a model that never saw its outcome.
6. **Real run.** Apply the winner to all 76 real places, San Francisco included, with pools from all eligible never-repealed places, scored as above. Report the result under each weighting.

7. **Weight test, rerun, and the Wisconsin figure (Ryan "yes", 21:00 UTC).** After the new matching, the same leave-one-state-out weight test is rerun: same candidates, same tie rule (the target-state mix wins ties).
8. **Size-band check, in the same rerun.** Four versions, using the correction lock's definitions (terciles of the 76, the cell-merge rule, Wisconsin crowding from the latest release fetched):
   - 4 bands;
   - 3 bands cut at terciles;
   - a log-population line held at the edge;
   - a crowding mix.

   Rule: keep the 4 bands unless another version's error is more than 10% lower and its paired bootstrap excludes 0.

**Write-up:** keeps the double-dip note.

**Reported:** the traits used, the model chosen, B-half accuracy, both candidates' fake-repeal scores, and the real result beside the method-2 corrected result and the current lines.

## Method 3b: prognostic matching, second version (LOCK DRAFT 2026-11-05, before any count; Ryan 03:08 UTC: "Yeah I think you can proceed like that with method 3b and the paired bootstrap"; the learning thread's full spec)

**Status: cleared by the audit (03:16 UTC, including grouped-CV boosting iterations).** Time records:
- Ryan approved at 03:08:50 UTC.
- The learning thread's spec was relayed at 03:09:16 UTC.
- The learning thread's PROVISIONAL GO was made at 03:14 UTC, under Ryan's 21:01 UTC delegation. Post hoc in origin: method 2's and method 3's real results have been seen. Any tool change needs Ryan's own OK. Runs stay on the Mac.
- **One candidate, no menu.** It combines the three changes below. Everything else follows the Method 3 lock: traits (as amended), corrected data, all places with San Francisco, every weighting, and cross-fitting for the real run.
- **Rule on narrow ranges:** a narrow real range is not a reason to pick 3b.

**1. Target.** The predicted change with no repeal: the after-window mean minus the before-window mean, with D's 10-year before window (back to 2012). Units: permits per 1,000 pre-event existing homes a year. Fitted on never-repealed places only.

**2. Score.** The average of the boosting and lasso predictions, each fitted inside the fitting half. Settings as method 3:
- **Boosting:** depth 2, learning rate 0.05, at least 5 per leaf. The iteration count (up to 300) is chosen by 5-fold grouped CV by place, then the model is refitted with it fixed. Its own random 20% early stopping is not used.
- **Lasso:** missing indicators plus the training-half median, one-hot division, and the penalty chosen by grouped inner CV by place.
- **Split:** the same A/B split (seed 20261104). The score used in the bake-off is fitted on A only.
- **Stop rule:** the score's error on B must be at least 5% below a plain average of A's change. Otherwise stop and report; D stays.

**3. Matching (3b).**
- **Ladder:** the corrected method-2 ladder.
- **Within the chosen step:** the 10 nearest on a standardized-sum distance, √(z_score² + z_trend²). The z-differences are the score and the before-window trend between candidate and target. The trend is the slope of yearly rates over the standard 5-year before window, the same window as the score's features. Both are standardized over the candidates in the chosen ladder step (all eligible candidates at step 5). Proposed over Mahalanobis because there are only two dimensions; their correlation is reported.
- **Step 5:** adds z-scored log population as a third term.
- **Ties:** broken as in method 2.
- **Effect:** D's 10-year before window, as in the corrected method 2.

**4. Fresh fake repeals in B.**
- **New draws:** seed 20261105, with the same stratified draw (each real case's event year, size band and after-year count).
- **Event years:** kept equal to each real case's own event year (audit recommendation). This replaces the spec's "new fake event years" wording. D's window length depends on the year, so drawing other years would change the mix of window lengths. Freshness comes from the new seed, and so new places and sets.
- **Pools:** from B only.
- **No reuse:** method 3's 5,828 cases are not reused, and the overlap is reported.
- **Scoring:** 200 sets of 76, random-effects scoring; MAE and coverage with its SE, with the other weightings beside.

**5. Pick rule.** 3b replaces D only if all three hold:
- **(a)** the 90% paired-bootstrap range of MAE(3b) − MAE(D) lies entirely below 0. That is 2,000 resamples of the 200 fake sets (seed 20261105), recomputing both MAEs on each resample.
- **(b)** the point gap is at least 2% of D's MAE. This is the learning thread's provisional call, relayed by the coordinator at 2026-11-05 03:09:16 UTC under Ryan's 21:01 UTC delegation. Its reason: the paired bootstrap already guards against noise, so a smaller practical margin than the earlier 5% is enough.
- **(c)** coverage is between 85% and 95%.

Otherwise D stays and 3b is evidence only. The pick is committed before any real-repeal 3b output, with the same code gate.

**Write-up note:** sets share some fake cases, so the paired-bootstrap range is a little too narrow.

**6. Real run.** As method 3: all 76 places with San Francisco and cross-fitted scores. Report every weighting, then the weight test (state mix wins ties), the size check and the Wisconsin figure. If D stays, method 2's corrected results stand and 3b's real results are evidence only. The write-up labels the origin as post hoc.

## Test 49: does the effect build, hold or fade? Event-time checks (DRAFT LOCK 2026-11-05, before any count; Ryan 14:55 UTC; the learning thread's spec)

**Running count: 49.** Evidence only; the lines are unchanged. Ryan: "You are making an assumption (that the effect is positive) when you say the effect doesn't build up over time." Nothing here assumes a sign.

**Estimator: method D on corrected method-2 data.**
- Strict pools, shock rule, matching, winsorising and pre-repeal homes, all as the corrected method 2.
- **D's before window:** up to 10 years, back to 2012.
- **One pool per case:** chosen once and held fixed across years. Pool members must report in every year of D's before window and of the case's whole after window used in the check. The strict "no reform ever" exclusion applies.
- **Effect in after-year k:** (city rate in year ey+k − city's before-window mean) − (winsorised pool rate in year ey+k − pool's before-window mean). Permits per 1,000 pre-event existing homes a year.

**Audit fixes (lock cleared 2026-11-05 14:58 UTC; Ryan's ask is the go):**
- **k:** after-year 1 is the calendar year ey+1, matching method 2's after window, which starts the year after the repeal year. Year 0, the repeal year itself, is shown as context only.
- **Too-small pools:** a case whose pool has fewer than 5 members under the longer window is dropped from that check and listed.
- **Main reading:** the target-state mix, which won the weight test, with random effects and equal weights beside. With 6 slopes at 90%, one could exclude 0 by chance.
- **Same draws:** the bootstrap is paired across every year and every weighting (the same place draws), and the slope is fitted inside each draw.
- **Random effects caveat:** RE uses the placebo variance of a 3-year average effect, and single years are noisier. That is one more reason the mix is the main reading.
- **Leads:** only places with 6 or more before-years have leads, so the leads rows report their own place counts. The mix's cell-merge rule applies; with 15 places most cells merge.
- **Comparison with method 2:** for the 38, the years 1–3 average is shown beside corrected method 2's result for the same places. A large gap would flag a pool effect.
- **Pre-trend:** the check also runs on check 1. It is thin for early repeals: a 2016 repeal has only 2012 as an earlier before-year.

**Check 1 (balanced 3-year set).** The 38 places with all 3 after-years. Effects in after-years 1, 2 and 3 on the same places.

**Check 2 (long set).** Places with 5 or more after-years through 2025: event year 2020 or earlier, 15 places (2016: 1, 2017: 2, 2018: 3, 2019: 5, 2020: 4).
- **After window:** extended as far as the data allow. That is up to 9 years, because 2025 is the last permit year and the earliest repeal is 2016, so no place has 10.
- **Balanced:** years 1–5 on all 15.
- **Years 6+:** reported with the number of places in each year.
- **Pre-trend check (long set):** the same pool and effect formula for the last 3 before-years (ey−3 to ey−1), against the mean of the earlier before-years. Reported with ranges and a slope.

**Per year:** the estimate with a 90% place-bootstrap range (2,000 draws, seed 20261105; places resampled with all their years), under:
- the target-state mix (Wisconsin, tool cells);
- random effects;
- equal weights.

The number of places is shown for each year.

**Slope.** For each check, the slope of the yearly weighted average on k over the balanced years, with its bootstrap 90% range, under each weighting.

**Reading rule (neutral):** "changes with time" only if the slope's 90% range excludes 0, in either direction. Otherwise "no clear change over time". The write-up says plainly that 15 places is thin.

**Runs:** on the Mac. No tool changes without Ryan's OK.

## Reform-type coding for the 15 long-set places (PLAN 2026-11-05, before any coding; Ryan 15:16 UTC: "Did we code any of these 15 places' reform? ie complete repeal of minimums, reduction, reduction within an area, by right v discretionary"; 15:19:11 UTC: "I think we probably need to code all 15"; 15:19:49 UTC: "don't limit to apartment buildings - all residential")

**Purpose.** Describe what each of the 15 places in Test 49's long set actually changed, so the by-year results can be read by reform type. Coding only: this plan reads no new outcomes and runs no test. Any use of the codes in an estimate needs its own lock.

**Places (event year ≤ 2020):**
- San Francisco 2019, Buffalo 2017, Hartford 2017, Dunwoody 2019, Mount Pleasant MI 2018;
- Windham ME 2018, Emeryville 2020, Branson 2018, Canandaigua 2020, Ecorse 2020;
- Bastrop 2019, Seabrook NH 2019, Hudson NY 2019, Maumee 2020, Saranac Lake 2016.

Ecorse and Saranac Lake already have pilot coding, which is re-checked here.

**Revised to the learning thread's spec and Ryan's 15:19:49 UTC note ("don't limit to apartment buildings - all residential"):**
- **Template:** the dose-pilot template (`reference/parking_dose_pilot.csv` columns: required spaces before and after for a fourplex, 20 units and 100 units; prior exemptions; scope; share of apartment land covered; single-family rules; same-time changes; sources; confidence), plus the fields below.
- **Old minimums:** also cover a house and 2–4 unit buildings (a 2-unit and a 3–4 unit example), not only the fourplex, 20-unit and 100-unit examples. Both before and after repeal.
- **Saranac Lake and Ecorse:** missing fields only.
- **Inferences** are marked as inferences, with confidence.
- **First report:** whether approval path and dose vary across the 15.

**Fields, one row per place** (`reference/parking_reform_type_15.csv`):
1. **Repeal type:** full removal of residential minimums / reduction (minimums cut but not removed) / removal for some housing types only (e.g. multifamily only, or 1–2 family only).
2. **Scope:** citywide / within areas (downtown, transit, districts), with the share of apartment-eligible land where known from the dose pilot or the ordinance.
3. **Approval path for every residential type: house, ADU, 2 units, 3–4 units, 5+ units.** For each type, coded before and after repeal, with any size threshold (for example, a hearing above N units), and whether the repeal changed it. Categories:
   - **by right:** staff or administrative review only, no public hearing;
   - **discretionary:** a hearing such as a conditional use, special permit, planned development or variance is required;
   - **mixed:** by right in some zones, a hearing in others; the share is given where known.
   - This is about whether the project needs a hearing at all, not whether a parking waiver exists.
4. **Same-time changes:** other zoning changes adopted within 1 year (a chosen window). For the 9 places flagged as simultaneous rewrites, whether density, height or permitted uses also changed.
5. **Housing scope:** all residential uses / multifamily only / 1–2 family only / other.
6. **Event date check:** the adoption and effective dates against the event year used. Any mismatch is reported, not changed.
7. **Sources:** the ordinance or code text (adopted version and the version the day before), the zoning use tables for the approval path, and PRN as a secondary source. Every field cites its source URL.
8. **Confidence:** high / medium / low, with a note.

**Audit items (15:40 UTC).**
- **Code before looking:** the coding CSV is committed before it is joined to any Test 49 effect, and the grouped table is built only from that committed file.
- **Small groups:** groups will hold only 1–5 places, so no group difference is a finding. A test by type needs its own lock.
- **The version the day before:** the Wayback Machine is a public source; the capture date is cited. "Not found" is marked where there is no earlier version.
- **By right vs discretionary:** coded now as description, because Ryan's 15:16 UTC message asks for it.

**Rules.**
- **Public sources only:** municipal code sites, council agendas and minutes, the Parking Reform Network.
- **Blocked sites:** cited, not worked around.
- **No records requests:** no clerk or records request without Ryan's OK.
- **No addresses.**
- **Saranac Lake first:** check whether its 2016 code removed minimums for all housing or only 1–2 family homes, as the PRN summary hints. If only some housing types, its repeal type is coded "some housing types only" and it is flagged for the by-year reading.
- **Time:** about 15–30 minutes a place. A place that cannot be coded from public text is marked "not found" for that field.

**Output.**
- The CSV and a short table in WORK_SESSION_RESULTS.md.
- The Test 49 long-set results are shown grouped by repeal type and approval path as a description only, with no new test. A test by type would need its own lock; with 15 places, any group would be very small.

## Batch rerun after the sample fixes (DRAFT LOCK 2026-11-05, before any run; Ryan 15:50 UTC: "fix canandaigua / remove seabrook / what do you mean about maumee?")

**Fixes.**
- **Canandaigua, NY:** matched to the Town of Canandaigua's permit series (BPS 36|103500, "Canandaigua town"), which adopted the 2020 repeal. It was matched to the City's (36|103000). Implemented as a name alias in `missing_middleware/parking/comparison.py` (`ALIASES`). This also applies wherever the taxonomy names Canandaigua, NY, which is the town's reform.
- **Seabrook, NH:** removed from the repeal places, because its 2019 change cut only non-residential minimums. Implemented as `reference/parking_sample_corrections.csv`, read by `run_parking_expanded.py`. Seabrook stays out of comparison pools, as before.
- **Maumee, OH:** removed from the repeal places. Ryan, 15:54 UTC: "code maumee as a parking reform but not a repeal, and discretionary". Recorded in the coding CSV and in `parking_sample_corrections.csv`; the removal is applied to partial-search and rescued places too. The repeal places become 74.
- **Sensitivity only, not a fix:** Branson removed, where the wording leaves the minimum partly in force.
- **Approximate side run, Maumee kept in (75 places):** it does not redraw stage 1's fake sets or the placebo spread for 75 places. covers a label-only reading of Ryan's answer. It is post-processing on the batch outputs: Maumee's effect is added back, from the partial-search effects for the main estimate and from a method-2 case computation for method D.

**What is rerun, in one batch, old and new side by side:**
1. The main sample effects (salvage, partial and expanded scripts). The repeal places become 74 (Seabrook and Maumee removed).
2. The full placebo run, which gives the main 90% range in Wisconsin homes (real average with placebo spread).
3. Corrected method 2, both stages, under the same rules. Stage 1's pick uses the correction lock's rule (D or B+D; D wins ties at 5%), the weight test, and the Wisconsin figure.
4. Test 49's event-time summaries.
5. The Branson sensitivity on items 1 and 3.

**Audit fixes (16:52 and 16:58 UTC).**
- **Outputs never touch the originals.** The batch reads and writes a working copy of `reference/` in `data/processed/batch_2026-11-05_ref/`, which is not in git, through `MM_REFERENCE_DIR`. Changed or new files are then copied, keeping subpaths, into `reference/batch_2026-11-05/`.
  - A separate git worktree is not used, because this session must stay in its one folder.
  - The interim method-2 pick is committed only inside `reference/batch_2026-11-05/`. The stage-2 gate checks against that committed copy (`MM_BATCH_COMMITTED_DIR`) and needs the 15:50 UTC gate line (`MM_GATE_TIME`).
  - After the run, `git diff --quiet` must pass for `reference/` outside the batch folder. TOD's files must hash the same before and after.
- **Spillover:** the City of Canandaigua (36|103000) is kept out of the Town's comparison pools (`SPILLOVER` in `comparison.py`; also applied in method 2's eligibility).
- **The Town's data (checked before the run):** it has homes (5,427), population (11,270), 2010 density, town age, crowding for every release 2013–2023, and complete permit years 2012–2025. It is not shock-flagged. Its crowding is 0 in the 2018–2022 and 2019–2023 releases; that is a reported value, not missing.
- **Noted for the report:** with 74 places, stage 1's fake sets change even with the same seed; the pick rule is unchanged. The width is reported against both bars (like-for-like 49,253, post hoc; locked 26,289). Test 49's long set becomes 13 places (Seabrook and Maumee out, Canandaigua on the Town's series), with old and new rows side by side. Ryan's Maumee answer is recorded above with its time (15:54 UTC).

**Tool guard.**
- New outputs are written beside the old ones in `reference/batch_2026-11-05/`, and the committed originals that feed the tool are restored after the run.
- The tool's lines and bundle are not regenerated. Changing them needs Ryan's own OK.
- Scripts that read `parking_old_minimums.csv` (round 3, causal MR, the Stage 2 trait test, T44) are not rerun here; their next run will pick up the Hudson and Emeryville updates.

## Test 50: San Francisco and Emeryville project parking, before and after repeal (DRAFT LOCK 2026-11-05, before any record is read; Ryan 15:53 UTC)

**Running count: 50.** Descriptive evidence, like test 43 (Madison). Nothing changes in the tool. Ryan asked: "How much parking were these projects required to add by law? How much parking did the initial proposal include? What was the eventual number of parking spots required in the approved entitlement?", with units every time stalls are captured, and residential and commercial requirements kept separate for mixed use.

**Projects and windows.** New residential or mixed-use projects of 5+ homes:
- **San Francisco** (repeal effective 2019-01-21): applications filed 2016-01-01 to 2019-01-20 (before) and 2019-01-21 to 2022-12-31 (after).
- **Emeryville** (repeal effective 2020-05-21): applications filed 2017-01-01 to 2020-05-20 (before) and 2020-05-21 to 2023-12-31 (after).
- **Uneven windows:** about 3 years before against about 4 after, so counts are compared as shares, not totals.

**Sampling frame, fixed before any record is read.**
- **San Francisco frame (revised 2026-11-05 about 15:58 UTC, before any project record is read; audit OK 15:59 UTC):** the quarterly pipeline file is a current snapshot only. Projects completed since 2016 have left it, and earlier snapshots were retired. So the frame is DataSF "Planning Department Records - Projects" (qvu5-m3a2; download date recorded), which holds every project record, including withdrawn ones.
  - **Included:** records with 5+ net new homes (`number_of_units_net`), an `open_date` in each window, and a planning decision of approved (entitled). The counts of withdrawn, cancelled and disapproved records in each window are reported beside the sample.
  - **Draw:** if more than 15 in a window, 15 are drawn at random (seed 20261105, after sorting by record id), stratified by parking section: up to 10 from Sec. 151 districts, the rest from Sec. 151.1 districts.
  - **Zoning district:** taken from DataSF "Parcels - Active and Retired" (acdm-wktn) by block and lot. This is current zoning, a proxy for zoning at filing; where the case report names a different district, the case report wins, and the change is reported.
  - **Section:** assigned using Sec. 151.1's district list as of 2018 (source cited).
  - **Conditioning on approval:** drawing only approved cases conditions on approval. Withdrawn, cancelled and disapproved counts are reported by window and section.
  - **Block and lot:** used only for the zoning join, never committed. The case number (record id) is the ID.
  - **Rezonings:** Central SoMa (2018) and other rezonings moved parcels between Sec. 151 and 151.1. The case report wins, and the number of cases that differ is reported.
  - **Parking fields:** `parking_spaces_prop` is not read for any project until the draw is committed.
- **Emeryville:** every 5+ home project before the Planning Commission in each window, from its agendas and staff reports. All are coded.
- **Emeryville frame change (2026-11-05, after coding began; audit OK):**
  - **Why:** Commission agendas and staff reports from before 2025-05-01 are no longer posted, and getting them means asking the Commission Secretary, which would be a records request.
  - **Replacement sources:** the Planning Director's monthly reports to City Council on Commission actions (Council Legistar, Oct 2016 to Feb 2024), the city's Status of Major Development Projects reports (Jan 2024, Jan 2025, Sep 2026), and HCD APR Tables A and A2.
  - **Missing months:** some Director's-report months are missing, mostly Julys. The helper did not list each one, so the exact months are not known.
  - **Wayback copies:** three facts come from them and are labelled in their rows.
  - **Presentation:** with 5 usable rows (1 high confidence), Emeryville is shown as a list of cases, not shares.

**Fields per project:**
- case number; application and approval dates;
- approval path (hearing or not);
- units proposed and approved;
- for residential and, separately, commercial: required spaces under the code in force at application (minimum, and any maximum), stalls in the initial proposal, and stalls approved in the entitlement;
- variances or exceptions to parking;
- sources with URLs;
- confidence.

**Rules.**
- Public sources only: planning case reports and motions, agendas, staff reports, the pipeline data.
- Blocked sites are cited, not worked around. No records requests without Ryan.
- No street addresses in committed files: projects are identified by case number and a short name. Stalls and homes are stored exactly; ratios are rounded only for display.
- Ryan spot-checks 5 rows drawn at random (seed 20261105) before the result is cited, as in test 43.

**Reading change (audit, 2026-11-05 about 16:24 UTC, after the San Francisco coding, before the write-up).** In San Francisco, filing date does not split the rules, because most projects filed before the repeal were approved after it. The reading uses three groups:
- filed and approved before the repeal;
- filed before and approved after (the "switchers"; their proposal-to-approval change is the closest to a same-project before and after);
- filed after.

Frame-versus-case-report section mismatches are all reported. The case report wins, so named NCDs with their own Table 151.1 rows count as 151.1. 2018-016535PRJ (a unit-count documentation record) is dropped. No before-151 replacement exists, because the approved before-151 pool (10) was fully drawn, so that stratum has 9 projects. 2016-012545PRJ stays in the before window by its open date; its SB 35 filing came after the repeal, so it is a switcher.

**Reading (descriptive).**
- **Ratios:** stalls per home, proposed and approved, against the required minimum, before and after repeal.
- **Bunching:** the shares of projects above, at and below the minimum, as in test 43. After repeal, the comparison is against the old minimum.
- **Mixed use:** the commercial share of required spaces is shown separately.
- **No test of difference.** Samples are small, so no difference is a finding.

## Test 51: does subsidized building drive the result? LIHTC check (DRAFT LOCK 2026-11-05, before any count; Ryan 16:27 UTC: "oh yeah, perfect LIHTC")

**Running count: 51.** Sensitivity and evidence only. Tool changes need Ryan's own OK.

**Question.** Several zero-parking projects in the San Francisco records are 100% affordable. Is the main estimate driven by subsidized (tax-credit) building rather than market-rate building?

**Data.**
- **Source:** HUD's public LIHTC database (huduser.gov, public domain). One row per tax-credit project, with place, year allocated, year placed in service, total units and low-income units. The file name, download date and SHA-256 are recorded.
- **Matching:** projects are matched to BPS permit places by state and place FIPS code (the database's place field). Unmatched projects are counted and reported. No addresses are committed.
- **"100% affordable":** low-income units ≥ 95% of total units, which allows for manager units.

**Timing.**
- **Permit year:** the allocation year + 1. This proxies the building-permit year; tax credits are allocated before construction.
- **If allocation year is missing:** the placed-in-service year − 1.
- **Sensitivity:** the permit year is the allocation year itself.
- **Coverage:** the database lags. Projects allocated after its last complete year are missing, so the after-years 2023–2025 are under-counted. This is reported, and a variant ends the windows at the database's last complete year.

**Estimate.**
- **Main sample:** the 74-place main sample after the batch fixes (`reference/batch_2026-11-05/`).
- **Rerun:** the main matched difference-in-differences, with each place's yearly permits reduced by its 100% affordable LIHTC units (floored at 0), for repeal places and comparison places alike. Same pools, windows, homes and weights.
- **Reported:**
  - the home-weighted average with a 90% place bootstrap (2,000 draws, seed 20261105);
  - the Wisconsin figure (× 13,343);
  - the same beside the unadjusted batch result;
  - the share of permits removed in the repeal places and the pools, before and after.
- **Method 2:** the same adjustment run on corrected method 2 (D, target-state mix) as a second line.

**Reading.**
- If the adjusted average moves by less than its range, subsidized building does not drive the result.
- A large move in either direction is reported as evidence of subsidy timing, not as a parking effect.
- No line changes without Ryan's OK.

**Audit fixes (lock cleared once these are in; 16:28 UTC).** These override the matching, range and reading bullets above where they differ.
1. **Geography:** projects are assigned by latitude and longitude to the BPS place or county subdivision (Census boundary files, `geom.py` point-in-polygon), because many of the 74 are towns or townships. The database's place field is used only as a check. Unmatched projects are reported by state. No coordinates are committed.
2. **Range:** the adjusted Wisconsin range uses the same method as the main: the real average with the placebo spread, from a placebo run on adjusted permits.
3. **Reading:** the paired difference, adjusted minus unadjusted on the same places, with a paired place bootstrap (2,000 draws, seed 20261105). "Subsidy does not drive the result" only if that 90% range includes 0. The earlier "a large move" reading is dropped.
4. **Coverage:** if the database ends before 2025, the variant that ends windows at its last complete year is the main reading.
5. **Scope:** only 100%-affordable projects are removed in the main version. A variant removes all LIHTC low-income units.
6. **Floor:** how often the 0 floor binds is reported (place-years and units).
7. **Timing check:** the share of LIHTC units whose proxy permit year has at least that many BPS permits in the place is reported.

**Feasibility finding (2026-11-05, before any estimate).**
- **Source:** HUD's ArcGIS LIHTC service (item 810ccb34dd464ec4ad4697d35fff21a5, last edit 2025-05-14, credit "U.S. Department of Housing and Urban Development, U.S. Census Bureau"; public domain). The huduser.gov download sits behind a bot challenge and is cited, not worked around.
- **Coverage:** allocations by year are 2018: 781, 2019: 437, 2020: 278, 2021: 30. The service looks complete only through about 2019 allocations.
- **Consequence:** under fix 4, only repeals in 2019 or earlier would have after-years, one or two places at most. On current HUD data the test is not feasible.
- **Path, Ryan's call:** a newer national file hand-downloaded by Ryan from huduser.gov (name, date and SHA-256 recorded). If it reaches the 2021–2022 allocations, the test becomes useful.

**Hand-downloaded file (2026-11-05 17:10 UTC, before any estimate).**
- **File:** `lihtcpub.zip` from huduser.gov, hand-downloaded by Ryan on 2026-11-05.
  - SHA-256 e07acee706174b276f89596d614ac5699efa9848659e5834fdfb5198fa0a7288; 29,421,665 bytes.
  - LIHTCPUB.xlsx dated 2026-04-30 (55,345 projects) and the 2024 data dictionary.
  - Kept in `data/raw/hud_lihtc/` (not committed).
- **Projects by allocation year:**

  | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
  | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
  | 1,224 | 1,288 | 1,145 | 1,232 | 1,200 | 1,189 | 1,154 | 935 | 589 | 264 | 176 | 38 |

  - 2,709 rows have code 9999 or 8888 (year missing).
- **Projects by year placed in service:** about 1,100 to 1,200 a year through 2020, then 1,079 in 2021, 1,020 in 2022, 929 in 2023 and 787 in 2024.
- **Reading of coverage:** the database lists projects once they are placed in service, so recent allocations are missing.
  - Allocation years 2014–2020 average about 1,200 a year.
  - 2021 is at 79% of that and 2022 at 49%.
- **Places with an after-year:** if allocations are complete through 2020, permit years run through 2021 and 13 of the 74 places (repeals 2016–2020) have at least one after-year. Counting 2021 as complete adds 12 more (25).
- **Cut-off (Ryan 17:14 UTC, "sure", to the recommendation):**
  - **Main:** allocations through 2020 are complete, so permit years end in 2021, and only repeals in 2020 or earlier with after-years by 2021 count. That is 13 places.
  - **Labelled sensitivity:** allocations through 2021, with permit years through 2022 (25 places).
  - **The full window to 2025:** reported only as a variant, with the undercount stated.
- **Audit advice (17:12 UTC, for Ryan's call):**
  - Main: allocations through 2020 (13 places).
  - Sensitivity, labelled: allocations through 2021 (25 places). 2021 is 79% complete and the missing projects are recent, so treating it as complete undercounts only the late repeals' after-years, which pushes the result toward a fall.
- **Reading line added:** a result that can't be told from zero on 13 places says little.
- **Rows with no allocation year (2,709):**
  - 1,511 have a placed-in-service year and get permit year = that year − 1, as locked. 551 of them were placed in service in 2015–2025.
  - 1,198 have neither year, so they can't be placed in any year and are left out. Whether they fall in the window isn't known.
- **Fix 1 assignment (scripts/assign_parking_lihtc_places.py):**

  | Assigned to | Projects |
  | --- | --- |
  | BPS place | 41,609 |
  | BPS county subdivision | 2,607 |
  | Unmatched (mostly unincorporated land) | 8,873 |
  | No location | 2,256 |
  | **Total** | **55,345** |

  - The database's place field agrees for 34,248 of the 34,428 place-assigned projects that have one.
  - By state: `reference/parking_lihtc_match.csv`.
- **Fix 1 audit fixes (17:22 UTC review, applied before any count; script commit 3f30a70d then this one):**
  1. **Connecticut:** county subdivisions are now matched on state + MCD code. Unmatched in CT was already 0 of 456: the BPS keys in recent years already carry the planning-region codes. The change is a safeguard and moves no project.
  2. **Unmatched share in the town and township states:**

     | State | Unmatched |
     | --- | --- |
     | CT, NJ, RI | 0% |
     | MA, NH | 0.7% |
     | NY | 0.8% |
     | PA, WI | 2.8% |
     | ME | 3.2% |
     | VT | 4.5% |
     | MN | 8.9% |
     | MI | 14.7% |

     The Michigan and Minnesota cases checked (Gaylord, Escanaba, Petoskey, Marquette, Ionia, Minnesota unorganized territories) have no BPS place series at all, so these are not code mismatches. The places can't be in any pool, and leaving them out changes nothing in the estimate.
  3. **Fallback rows:** matched projects whose permit year comes from placed-in-service − 1, by permit year:

     | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
     | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
     | 51 | 64 | 64 | 44 | 41 | 72 | 55 | 41 | 23 | 36 | 6 |

     - The full list is in `reference/parking_lihtc_fallback_by_year.csv`.
     - The cut-off applies to the permit-year proxy whatever its source, because permit years after the cut-off are dropped from the panel.
  4. **Place first:** a project inside a village counts for the village only, never also for its town. Each project carries exactly one key, and the script asserts this.

**Also (descriptive):** the San Francisco and Emeryville project tables get a "100% affordable" flag. For San Francisco it comes from the planning-records fields (affordable units = units, or the 100%-affordable program flag). For Emeryville it comes from HCD Table A2 income splits.

## Test 52: causal diagram, back-door adjustment and tests for unseen back doors (DRAFT PLAN 2026-11-05, before any count; Ryan 17:35–17:37 UTC in the learning thread: "can you do that? Draw the diagram, and block the back doors, make sure you don't block the wrong things, and then test for the back doors we can't see?")

**Running count: 52.** Evidence only. Lines and the tool stay unchanged without Ryan's own OK. This plan goes to the audit and to Ryan before any count.

- **Audit:** cleared (17:48 UTC, including 52i).
- **Ryan's go (17:58 UTC):** "Go". This answers the 17:47 message, which asked "Can I start it?" and stated that the go replaces "ties go to the state mix" with the bake-off-then-stacking rule, for this test only.

**Estimand.** The total effect of a city's residential parking-minimum repeal, as adopted, on homes permitted per 1,000 existing homes a year, in the years after repeal. Anything the same ordinance changed is part of the treatment; E2 and the reform-type coding describe those bundles. A reform adopted in a separate act is a possible confounder.

**The diagram.** Arrows mean "can cause".

```
                 Politics / pro-housing council (P) ──────────────┐
                    │                    │                        │
                    ▼                    ▼                        ▼
 Market demand ──► Repeal (R) ─────► Parking built per home (M1) ─► Homes permitted (Y)
 (D: rents, jobs,   │  ▲              Project size / building type (M2) ─►  ▲
  prices)  ─────────┼──┼──────────────────────────────────────────────────►│
                    │  │                                                    │
 Other housing reforms (Z: upzoning, ADU law, state laws, rewrites) ──────►│
   ▲ (from P, D)    │  │                                                    │
 Recent permit trend (T) ─┘ (a slump or boom can prompt repeal) ──────────►│
 Place traits (S: size, density, age, crowding, metro, state/region) ──►R, ►Y
 One-off shocks (X: disasters, a big project, a closure) ─────────────────►│
 Transit investment (Q) ──► R (TOD-linked repeals) and ──────────────────►│
```

**Back doors (non-causal paths from R to Y) and how each is blocked:**

| Back door | Path | Already blocked by | Gap | This plan |
| --- | --- | --- | --- | --- |
| Place traits | R ← S → Y | Pools matched on state/division, size; method 2 on crowding, density, age | none known | keep |
| Recent permit trend | R ← T → Y | Before window (5 yrs main, 10 yrs method 2); P2 slope matching | Test 49: places were already falling before repeal under RE/equal | **52c**, bound and trend-matched rerun |
| Market demand | R ← D → Y | Partly, via traits and same-state pools | no direct measure of demand change | **52a**, add pre-repeal rent and job growth |
| Other housing reforms | R ← P → Z → Y | E2 split only (same-time rewrite, treated places only) | separate reforms in treated **and** pool places not coded | **52b**, code dated events, adjust and drop |
| Politics | R ← P → (approvals) → Y | none | not measurable directly | **52d**, unseen back-door tests |
| Transit | R ← Q → Y | none in the 74 | small | 52b codes new rail/BRT openings as a dated event |
| Shocks | R ← X → Y (by timing) | placebo spread | disaster rebuilding (Bastrop to check), single large projects | **52e**, leave-one-out and winsorising (already in method 2) |

**Things we must not adjust for (would block the effect or open a new path):**
- **Mediators:** parking built per home (M1), project size and building type (M2), approval-path changes made by the repeal ordinance, land prices after repeal. Adjusting for them would remove part of the effect being measured.
- **Colliders and post-repeal selection:** pools must not be chosen on after-repeal growth, and samples must not be limited to approved or completed projects. Test 50's approved-only sample is descriptive for this reason.
- **Post-repeal traits:** every matching trait must be measured before repeal. The check: the ACS 2020–2024 homes denominator comes after some repeals. 52a reruns the main with a pre-repeal homes count (ACS window ending before the repeal year, or Census 2010) to show this is not a bad control.

**52a. Market demand (adjust).**
- **Measures, each in the 5 years before repeal, for each repeal place and every pool place:**
  - median rent growth (ACS 5-year B25064, earliest window against the window ending the year before repeal);
  - county job growth (BLS QCEW, public domain).
- **Use:** added to method 2's matching traits (crowding, density, age), and as a covariate check that repeal and pool places are balanced. Balance is reported as standardised differences; a difference above 0.25 is flagged.
- **Rerun:** the main and method 2 (D, target-state mix) with the extra traits, read beside the batch result.

**52b. Other housing reforms as dated events (adjust and drop).**
- **Coding, before any outcome is joined:**
  - **State laws:** statewide ADU, middle-housing, parking and by-right laws, by state and effective year (the TOD and ADU threads' lists plus `data/raw/statewide_states`).
  - **Place reforms:** for the 74 repeal places, any upzoning, ADU ordinance, comprehensive rewrite or new rail/BRT line within 3 years either side of the repeal, extending the 15-place coding brief.
  - **Pool places:** ADU ordinances from the Mercatus ADU taxonomy, and parking reforms from the PRN map (`data/raw/prn_reform_map`). Wider pool coding isn't feasible; that gap is stated.
- **Use:**
  1. Drop pool place-years within 3 years of a coded reform, then rerun.
  2. Drop repeal places with a separate reform within 3 years of repeal, then rerun.
  3. State laws: a pool place and its repeal place are already in the same state for most strata. Where the ladder moves to division or nation, drop pool places whose state passed a coded law within the window.
4. **Indicator version (learning thread):** keep every repeal place, and add an indicator for repeal places with a separate reform within 3 years. Report the effect for places without one.
- All of these are run on method D (corrected method 2) as well as the main estimate.
- **Reading:** if the result moves by less than its own range, other reforms don't drive it.

**52c. Recent permit trend (bound and adjust).**
- **Honest-DiD style bound** (relative magnitudes, hand-written as in P3): the post-repeal path may differ from the pool by up to M times the largest pre-repeal gap. Report the result at M = 0, 0.5 and 1, and the M at which the range first includes 0 (the "breakdown" M).
- **Trend-matched rerun:** P2's slope matching on the 74-place sample.
- **Reading:** a small breakdown M means the result rests on trends continuing.

**52d. Tests for back doors we can't see.**
1. **Placebo timing:** the backtest repeated with repeals moved 2 and 4 years early. A real repeal effect should not appear before the repeal.
2. **Placebo outcome:** single-family homes in places whose house minimum was already met by standard garages. This is a weak test, because Test 44 found houses may respond.
3. **Placebo treatment:** places that adopted a different reform (ADU-only) with no parking change, run through the same pipeline. An "effect" there points to a reform-wave back door.
4. **Sensitivity to an unseen confounder:** how strong an unseen back door would need to be to explain away the result. Reported as the share of the pre-trend gap it would need to reproduce (from 52c) and as an E-value style ratio on the permit rate.

**52e. Shocks.** Leave-one-out over the 74, and the share of the result from the largest 3 places. Bastrop is named in advance (2011 wildfire and 2015 flood rebuilding in the county before its 2019 repeal; to be checked against sources).

**52f. Synthetic difference-in-differences (learning thread, item B).**
- **What it does:** weights pool places to track each repeal place's before-repeal path, and weights before-years too.
- **Implementation:** written in numpy, with no new package; any package considered gets its licence checked and Ryan's OK first.
- **Scoring:** on the same fake repeals as method 3b, with 3b's pick rule:
  - a paired bootstrap;
  - it must beat D by at least 2% on error;
  - its 90% range must cover the truth on 85–95% of fake repeals.
- **If it wins:** it is shown beside D. It changes no line without Ryan's OK.

**52g. Spillover (learning thread, item D).** Rerun D using only pool places outside the repeal place's metro. A repeal can pull building from its neighbours or push demand onto them, so spillover can bias the estimate either way. Places with no metro keep their pool. The lost pool size and the match quality of the out-of-metro pools (mean Mahalanobis distance against the original) are reported.

**Learning-thread map:** https://claude.ai/artifact/GdKChVqZArPpuKNYpZ1FKT. Its status (blocked / partly blocked / mostly open) matches the table above. Items A and C are 52b and 52c here.

**Audit fixes (17:40 UTC review, through 947165c5). These override the text above where they differ.**
1. **Timing of other reforms:**
   - Only reforms adopted **before** the repeal year count as confounders, for the drops and the indicator (52b items 1, 2 and 4). For pool places, only place-years before the matched repeal's year count.
   - Reforms adopted at or after the repeal may be caused by it (momentum), so they are post-treatment. They form a labelled sensitivity only.
2. **52b reading:** each shift (rerun minus batch, same places) is reported with its paired 90% range (paired place bootstrap, 2,000 draws, seed 20261105). A shift counts only if its paired range excludes 0, read the same way for either sign.
3. **52c:** the main range already includes 0, so the breakdown M is 0 by definition, and this is stated. The bounds at M = 0, 0.5 and 1 are reported as ranges, without a breakdown value.
4. **Placebo lists, each committed before any join:**
   - **52d.2 (houses):** repeal places whose old minimum for a house was 2 spaces or fewer, taken from `reference/parking_old_minimums.csv` and the reform-type coding. Places with no coded house minimum are left out.
   - **52d.3 (ADU-only reform places):**
     - Places in the Mercatus ADU taxonomy with an ADU ordinance effective 2015–2022.
     - Excluded: any place in the PRN map (any parking reform), any of the 74, and any place in a repeal place's pool.
     - Event year: the ADU ordinance year.
     - The same pipeline and pools are used.
5. **52d.4:** the E-value is dropped, because it is defined for risk ratios. Only the share-of-pre-trend version is kept: the post-repeal gap a hidden factor would need to produce, as a multiple of the largest pre-repeal gap.
6. **52a details:**
   - **Rent growth:** ACS 5-year B25064, the window ending the year before repeal against the non-overlapping window ending 6 years before repeal. Every repeal year in the sample (2016–2024) has both windows (the first place-level window ends in 2009), so no 2012–14 fallback is needed.
   - **Large margins of error (20% is a convention):** where a place's rent margin of error is above 20% of its estimate, the county value is used instead, and the count of such places is reported.
   - **QCEW:** county-level only, so every place in a county gets the same job growth.
7. **Transit (52b):** coded for repeal places only, because pool places are too many to code. This is stated as a limit.
13. **More dated reform lists from the project's other threads (Ryan 17:43 UTC: "we have a pretty good list of reform cities and dates by consulting our other sessions"):**
   - **Sources:** these join 52b as dated events for repeal and pool places alike, committed as one events table before any join. Only events before the matched repeal year count, as in fix 1.

     | File | Rows | What it holds |
     | --- | --- | --- |
     | `reference/statewide_states_laws.csv` | 18 | State ADU laws with adoption, effective and compliance dates |
     | `reference/tod_cases.csv` | 58 | TOD upzonings with adoption and effective dates |
     | `reference/tod_reform_density.csv` | 38 | TOD reforms with reform year (deduplicated against `tod_cases`) |
     | `reference/other_cities_reforms.csv` | 21 | ADU and zoning ordinances with dates |
     | `reference/parking_reform_taxonomy.csv` | 6,318 | Every PRN-coded parking reform, including reductions and partial reforms, with dates |
     | `reference/ca_ab2097_rail_openings.csv` | 61 | California rail station openings with dates |

   - **Added after the learning thread's list (17:44 UTC), also used as written:**

     | File | Rows | What it holds |
     | --- | --- | --- |
     | `data/raw/tod_mbta/compliance_status_2025-09-18.csv` | 177 | MBTA Communities compliance; event = the compliance deadline year for towns marked compliant or conditional |
     | `reference/tod_optiond_stopmodel_places.csv` | — | TOD Option D evidence sets D-11 and D-B; place names, with dates taken from `tod_cases.csv` |
     | `reference/tod_causal_edge_test.csv` | — | Edge-test places; dates from `tod_cases.csv` |
     | `reference/wi_adu_rules.csv` | 299 | Wisconsin city ADU rules (`effective_from`); only the earliest ADU-allowing date per place is used |
     | `data/raw/statewide_states` | — | State-law folders; dates come from `statewide_states_laws.csv` |

   - **Not added:** `reference/ca_ordinances_2019.csv`, because its `rules_as_of` field is a snapshot date, not an adoption date.
   - **Audit additions (17:45 UTC):**
     1. **PRN parking reforms in pool places:** these are left out of 52b's events table. A pool place with a parking reform was itself treated, which is 52h.1's job, so the two checks don't overlap. PRN reforms enter 52b only for repeal places. Those rows are marked `prior parking dose` in the events table: an earlier parking treatment, such as a partial cut, not an unrelated reform (audit 17:46 UTC).
     2. **Uneven coverage:** the lists are dense for CA, MA, WI and the TOD cases and thin elsewhere. Drops are reported by state, and so is the pre-period gap before and after each drop.
     3. **"Before the repeal" for a pool place** means before its matched repeal place's event year.
     4. **Ambiguous names:** any same-name, same-state row that matches more than one BPS place is reported and left out.
   - **Selection after the drop:** dropping reformers may tilt pools toward low-politics, low-demand places. The 52a balance table and the pre-period gap before and after the drop show whether that happened. The indicator version (52b item 4) keeps everyone and conditions on nothing, so it is the fallback reading if the drop tilts the pools.
   - **Write-up:** it names every list used and says that coverage outside them is still partial.
   - **Transit for California pool places:** the rail openings are assigned to places by station location, so in California, transit (item 7) is coded for pool places too.
   - **Dates and places:** each list's date field is used as written (effective date if present, else adoption date). Places are matched to BPS keys by name and state with `cmp.match_place`; rows that don't match are reported.
8. **Denominator check (one, chosen now):** Census 2010 housing units (HU10, gazetteer), which come before every repeal in the sample.
9. **Reading line for all of Test 52:** one test moving alone is not evidence. The same bar applies to both signs, and only a pattern across tests is described.
10. **52d.1:** −2 years repeats the batch backtest, so it is cited, not rerun. Only −4 years is new.
11. **Balance flag:** 0.25 is a convention, used only to flag imbalance, not to accept or reject.
12. **52f:**
    - Unit and time weights are fit on before-years only.
    - Regularisation is fixed now: zeta = (number of repeal places × number of after-years)^(1/4) × the standard deviation of the pool places' year-to-year changes in the before-years (Arkhangelsky et al. 2021).
    - Seed 20261105.

**52h (labelled sensitivity; audit 17:42 UTC: "right in principle"). Pool rules that may filter on after-repeal outcomes (possible colliders; learning thread 17:41 UTC, after Ryan asked "are there any colliders that we accidentally controlled for and reopened?").** None is confirmed. Each rule is rerun on method D and read beside the batch result, with the 52b paired-range reading.
1. **Date-aware "never reformed" rule:**
   - The current rule drops any place that ever reformed parking, even after the window, and a place may reform because its building slumped.
   - The rerun drops a pool place only if its PRN reform took effect before the end of the matched repeal's after-window.
   - This differs from 52b's fix 1 (other housing reforms by place-year). Here the reform is a parking one and the rule is pool exclusion, so the two run separately.
2. **Shock rule without after-years:**
   - Test (b) (land area changed 25% or more, 2010 to 2024) spans the after-years, and towns often annex because they grow.
   - Only the 2010 and 2024 Gazetteers are on disk, so there is no exact pre-repeal version. The rerun drops test (b) entirely and keeps test (a).
   - Test (a) also spans after-years. It is a destruction screen (10% or more of homes lost), so it stays, and this is stated.
3. **Reporting rule relaxed:**
   - The current rule requires every window year present.
   - The rerun lets a pool place miss at most one window year. That year is filled with the place's own mean on the same side (before or after).
   - The share of pools that gain places is reported.
   - The number of filled years before and after repeal is also reported (audit 17:43 UTC).
- **Learning thread's f1–f3, not adopted (52h as accepted stands):**
  - Its f2 runs the homes-fall test on a pre-repeal count. There is no pre-repeal place housing count between 2010 and the ACS windows that is comparable to HU10, so this is noted, not run.
  - Its f3 uses Census-imputed values. The BPS annual place file's imputed estimates are in the same columns already used, so f3 and 52h.3 differ only in places with no record at all in a year, which 52h.3 fills from the place's own mean.
- **Not collider-type and kept:** matching on before-repeal traits only, and the same-state ladder.

**52i. Weighting: bake-off, then stacking** (Ryan 17:46 UTC in the learning thread: "with test 52, you can do the bake off and in the case of no clear winner, stacking?"; drafted by the learning thread).
- **When:** after the other 52 reruns, on the final estimator. That is method D, plus any 52 change Ryan accepts.
- **Candidates:** the same five weightings (target-state mix, random effects, square root, homes, equal).
- **Bake-off:** the same leave-one-state-out test. Each candidate predicts the held-out state's mean; the score is mean absolute error, with equal weight per state.
- **Clear winner:** the lowest-error weighting wins only if, against every other candidate, both hold:
  - (a) the 90% paired-bootstrap range of the error difference (over states, 2,000 draws, seed 20261105) is below 0;
  - (b) the gap is at least 2% of the runner-up's error.
- **No clear winner, then stacking:**
  - Blend shares are non-negative and sum to 1, chosen to minimise the held-out MAE of the blended prediction.
  - The fit is nested: for each held-out state, the shares are fit on the other states, the held-out state is predicted and that prediction is scored.
  - The final shares are fit on all states and reported.
- **Range for the blend:** bootstrap draws that mix the weightings' draws in proportion to the shares.
- **Pass test:** the nested held-out coverage of the blend's 90% ranges must be 85–95%.
  - If it passes, the blend replaces the single pick as the evidence result.
  - If it fails, the target-state mix stays, and the spread across weightings is shown beside it.
- **Tie rule:** for this test, this replaces Ryan's earlier tie rule ("ties go to state mix"), and the write-up says so.
- **Report:**
  - the shares;
  - the effective number of places;
  - the nested MAE and coverage;
  - Wisconsin homes 2027–2031, with its 90% range.
- **No expected result is stated. No tool change without Ryan's own OK.**
- **Audit fixes to 52i (17:48 UTC, before any count):**
  1. **Fold stability:** there are 10 states (11 rows in the batch weight-test file, including the header), so each nested fold fits its shares on 9 states. The shares for every fold are reported, with the range of each share across folds.
  2. **Coverage:** the share of held-out states whose own estimate falls inside the blend's 90% range. With 10 states it moves in 10-point steps, so 85–95% means exactly 9 of 10. This is a knife edge, and the write-up says so.
  3. **Blend range:**
     - The main range is the paired sum: share × draw, using the same bootstrap draw for every weighting. This is the uncertainty of the blended estimate itself.
     - The mixture of the weightings' draws is shown beside it, as a measure of spread across models.
     - Why: the paired sum answers "how sure are we of the blend", which is the question the range is for.
  4. **Bootstrap:** the paired bootstrap resamples places within states (stratified by state), not only whole states, so each held-out state's estimate carries its own noise.
- **Ryan's go must cover the tie-rule replacement:** for this test only, the go replaces "ties go to state mix" with the bake-off-then-stacking rule.

**Run order (concurrent where independent):**
1. 52b coding, committed before any join.
2. 52a data fetch.
3. 52c and 52e need no new data and run first.
4. 52a and 52b reruns.
5. 52d, 52f, 52g and 52h (52f, 52g and 52h need no new data and can run with step 3).
6. 52i last, on the final estimator.

**Rules.**
- Public sources only; blocked sites cited.
- No addresses.
- Same seeds (20261105) and the same 90% ranges.
- Every rerun is read beside the batch result.
- No line changes without Ryan's OK.
- Reported to the audit and Ryan.

## Test 53: core city vs suburb vs outside metro (DRAFT LOCK 2026-11-05, before any count; Ryan 21:09 UTC: "Yes" to "code all 74 places and their comparison cities with RUCA, then run a pre-registered split: core city, suburb or exurb")

**Running count: 53.** Evidence only. No tool change without Ryan's own OK.

**Traits, built before this lock with no outcome read** (19523fef; `reference/parking_place_ruca_traits.csv`):
- **RUCA:** USDA RUCA 2010 tract codes (main, before every repeal), population-weighted onto BPS places. 2020 codes are a check.
- **Principal city:** Census principal-city status (CBSA list 2, July 2023).

**Groups (fixed now, from `area_class`):**

| Group | Repeal places | Definition |
| --- | --- | --- |
| Core | 39 | Principal city of a metropolitan statistical area (Feb 2013 list) |
| Non-core metro | 27 | Suburb (22) + exurb (4) + rural part of a metro (1) |
| Outside metro | 8 | Micropolitan, small town or rural |

- Exurbs alone (4 places) are shown only as a list of cases, because 4 is too few to read.
- The group sizes were seen when the traits were built; nothing else was.

**Estimates.** Method D (target-state mix, the batch effects) and the main (tool) method, on the fixed 74-place sample.
1. **Group averages:** each group's weighted average with its own 90% range (place bootstrap, 2,000 draws, seed 20261105; D's mix weights aimed at Wisconsin cells; main uses homes × after-years). WI homes = rate × 13,343.385.
2. **Differences:** core minus non-core metro, and core minus outside metro, each with a 90% range from resampling places within each group (same seed).
3. **Class-matched pools (D only):** D rerun with each repeal place's pool limited to places of the same `area_class` group, on a working copy of the batch reference with the same ladder. Its shift against the batch uses the paired reading of Test 52b.

**Reading rules.**
- A group difference counts only if its 90% range excludes 0, read the same for either sign, and only if D and main agree in sign.
- With two differences tested, one excluding 0 by chance is plausible, and the write-up says so.
- The 2026-11-05 size bands (10k–100k) were post hoc; this test does not confirm or refute them.
- Group averages are average effects. A single city, Wisconsin's included, can fall well outside them (as in 52i).
- **Wisconsin use:** this is only described, never applied. A Wisconsin split by class would need Ryan's own OK and the 25% replacement rule.

**Audit fixes (21:21 UTC; before any count). These override the text above.**
1. **Prompted by results:** Test 53 was prompted by results already seen. Test 52e showed main's lean comes from SF, Austin and San Jose, all core cities, and Ryan's winners/losers question followed it. It is labelled post hoc in origin.
2. **Principal-city list:** the Feb 2013 Census list (based on 2010 data, before every repeal in the sample) is the main source; July 2023 is a check.
   - The groups above use 2013.
   - 4 of the 74 change group between the lists: West Allis is core in 2013 and a suburb in 2023; Tigard, Dunwoody and Springfield (OR) are suburbs in 2013 and core in 2023.
   - The check version reruns the group averages with the 2023 groups.
3. **Labels:**
   - The "dominant RUCA class" cut (the class holding the most population) is a convention.
   - South Bend's combined-area row is a hand fix (core on both lists).
   - The metro flag is the current one from BPS and 2024 boundaries, and this is stated.
4. **Thin groups:** outside metro has 8 places, so any difference resting on it is thin, and the reading says so. Each group's n is shown beside every range.
5. **Class-matched pools:** pool sizes are reported. Where a class leaves too few pool places, the batch ladder applies unchanged (state, then division, then nation, then step 5).
6. **Nearest-tract fallback:** 5 of the 74 use it (Bandera, Lansing, Social Circle, Millersburg, Saranac Lake).
7. **Equal-city weighting (added 21:31 UTC, before any count; Ryan in the CA AB 2097 thread, 21:30 UTC: equal weight per city "is a very different result than homes weighted ... might be related to our exurb observations ... worth testing"):**
   - Every group average and difference is also reported with equal weight per city, for D (the method-2 "equal" weighting, winsorised as in method 2) and main (plain mean).
   - The reading rule is unchanged.
   - An extra check: whether the gap between equal and home-weighted results is larger in one group than another (the difference of differences, with the same within-group resampling). It is read the same way.
   - **Winsorising:** main's equal-weight mean is winsorised at 5/95 within each group, the same way as D's, so a single place such as Bastrop can't move it alone. Main's home-weighted average stays unwinsorised, as in the tool. (Audit, 21:32 UTC.)
   - **Chance line, updated:** with 2 group differences × 2 weightings, plus the gap differences, there are about 6 comparisons. One or two 90% ranges excluding 0 by chance is plausible, and the write-up says so.
   - This change needs the audit and Ryan's go before the run.

**Revision (Ryan 21:36–21:40 UTC, before any count): six classes and population as a continuous variable.**
- Ryan: "principal is broad so there should probably be different classifications ...".
- Ryan: "running population as a continuous variable in one column, and the main city, secondary principal city, suburb, exurb, outside metro, rural".

These override the three groups above.
- **Classes** (`area_class6` in `reference/parking_place_ruca_traits.csv`; built with no outcome read):

  | Class | Repeal places | Rule |
  | --- | --- | --- |
  | Main city | 31 | The first-named city in its metro's title, on the Feb 2013 list |
  | Secondary principal city | 8 | Other principal cities on the 2013 list |
  | Suburb | 22 | Metro place, dominant RUCA 1 |
  | Exurb | 4 | Metro place, dominant RUCA 2–3 |
  | Outside metro | 7 | Non-metro place, dominant RUCA 1–6 |
  | Rural | 2 | Dominant RUCA 7–10 anywhere, or a metro place with dominant RUCA 4–10 |

  - The South Bend hand fix is "main city".
- **Group averages:** all six classes, for D, main, and both with equal weights, with n beside every range.
  - Classes with fewer than 8 places (exurb 4, outside metro 7, rural 2) are flagged thin, and no difference is read for them.
- **Differences:** main city minus secondary principal city, and main city minus suburb, under both weightings, plus the weighted-minus-equal gap differences.
- **Population, continuous:** the weighted least-squares slope of each place's effect on log10(population). It is reported four ways: D (mix weights), D (equal), main (homes × after-years), main (equal; winsorised 5/95 like D). Ranges come from a place bootstrap (2,000 draws, seed 20261105). The unit is the change in effect per 10× population.
- **Class-matched pools (D):** pools are limited to the same six-class group, with the batch ladder unchanged.
- **Reading:** unchanged, including that D and main must agree in sign. There are now about 10 comparisons (2 differences × 2 weightings, 2 gap differences and 4 slopes), so 1 or 2 ranges excluding 0 by chance is plausible, and the write-up says so.
- **Ryan's go:** his 21:40 message asks for this run. The audit must clear the revision before it runs.
- **Held-out prediction (Ryan 21:41 UTC: "the categories and population might end up being really strong predictors"):**
  - Group averages that differ don't make a predictor, so the run also uses the round-3 tool test (`run_parking_expanded.cv_score`: 10 folds × 20 repeats, the same tools and seed) on the 74 main effects.
  - Features: log10 population and the six-class indicators.
  - Weights: homes × after-years, and equal.
  - A tool passes if its held-out error beats "one average" by 5% or more, as locked for the expanded tools.
  - A pass is evidence only; using it in Wisconsin needs Ryan's OK and the 25% rule.

**Run order:**
1. Code committed before any run.
2. Group averages and differences.
3. Class-matched pools.
4. Write-up to the audit and Ryan.
