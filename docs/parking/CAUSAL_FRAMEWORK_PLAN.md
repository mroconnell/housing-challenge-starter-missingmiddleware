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
