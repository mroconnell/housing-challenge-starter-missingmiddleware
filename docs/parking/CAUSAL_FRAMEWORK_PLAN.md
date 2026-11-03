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
