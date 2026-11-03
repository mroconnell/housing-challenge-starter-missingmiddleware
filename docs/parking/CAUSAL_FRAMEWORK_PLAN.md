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
