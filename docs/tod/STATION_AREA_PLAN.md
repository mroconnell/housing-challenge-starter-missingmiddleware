# TOD station-area measure: plan (logged before any count, 2026-11-01)

Owner, 13:06: "try the station-area measure - go for it concurrently and retrain one fast fit and fix model to check for errors and iterate/improve quickly before we do a big run all the models." This runs beside the map-based test in [NEW_REFORM_CITIES_PLAN.md](NEW_REFORM_CITIES_PLAN.md). The tool's central line (1,196) does not change from this work until the owner decides.

## The measure

For each reform, the **station-area share** S is the share of the **whole city's** new homes, in permits, built within ½ mile of a rail or bus rapid transit stop. Stops count if they were open, or planned with a dated source, on the reform date (owner rule of 2026-11-01). Lots are counted whether or not they were upzoned.

- **Windows:** as the lot model: before = the 6 years before the reform; after = the 5 years after. A second version starts the after window at line opening.
- **Change:** ΔS = S after − S before.
- **No zoning maps.** Maps are used only later, to place homes within station areas.

**Why:** it counts spillover onto nearby lots that were not upzoned. It is the unit of the tool's Wisconsin baseline ("homes near stops"). And it needs only stop locations and dates.

## Cases

- **The 9 lot-model cities:** New York, Philadelphia, Charlotte, Saint Paul, Seattle, Los Angeles, Chicago, Madison, Bellevue.
- **The new cities:** Denver 2018, Portland 2018 and 2020, Austin (the regulating plans), Salt Lake City 2010.
- **No-reform cities as placebo:** Milwaukee, Columbus, Kansas City, Madison outside the overlay. Each gets a fake reform date, as in the lot model.
- **The city is the unit:** a city's cases are averaged.

## Comparison and noise controls (fixed now)

- **Placebo station areas:** station areas in the no-reform cities, and new stations that had no reform, such as Salt Lake City's 15 TRAX stations outside the city. These measure how much S moves with no reform.
- **Downtown:** every result is shown with and without stops within 1 mile of the city hall point.
- **New lines:** each case records whether its stops opened within 3 years of the reform. Opening years may differ in the comparison.

## Fast fit-and-fix model (one, iterated)

- **First:** the city-level rule ΔS = a + b × (S before − 0.5), fitted leaving one reform city out (the drift form, on the new measure).
- **Then:** the same rule plus "reform coverage", the share of station-area land the reform upzoned. It is filled only where a map exists; otherwise it is left blank and flagged.
- **Score:** median |log(predicted S after ÷ actual S after)| over held-out cities, against same share and average change.
- **After each run:** check for errors and outliers, fix, rerun, as in the earlier loops. No numbers go into the tool from this step.

## Data needed

Citywide permit files with home counts and locations for each city, and dated stop lists. A first inventory of what the existing case downloads already hold is the first step. Gaps are logged before any share is computed.

## Pre-registration (audit list, 2026-11-01 13:07; adopted before any count, and it overrides the sections above where they differ)

1. **Outcome per city:** the change in the share of citywide new homes within ½ mile of the reform's stations, in share points.
2. **Station lists are fixed and committed first.** Planned stops count, with `stop_open_at_reform` recorded and the source for each list.
3. **Controls:** rapid stops in the same city with no reform. Effect = change in reform station areas − change in control station areas. A lot within ½ mile of both goes to the nearest stop. Cities with no control stops are flagged. No-reform cities are kept as a separate placebo check.
4. **Downtown:** stops within 1 mile of city hall count as downtown. The main version includes downtown, because that is where Wisconsin's near-stop homes are. A version without downtown is the second.
5. **Denominator:** citywide permits from one source per city. The 9 cities' lot tables cover only their study areas, so citywide counts come from each city's full permit download where it holds the whole city. Where it does not, the Census permit survey place total is used, and the case is flagged "mixed sources". The source is listed for every city.
6. **Windows:** as the lot model, with a second version starting at line opening.
7. **Wisconsin formula (fixed now).** For each Wisconsin place with main-case stops:
   - extra homes = predicted change in share points × that place's citywide all-housing baseline for 2027–2031 (shared baseline v3);
   - summed over places.
   - The station definition is the one behind the 14,654 baseline (rail and rapid ½ mile, 15-minute bus ¼ mile).
   - The share before is each place's 2019–2024 share of new homes in its near-stop area: Milwaukee and Madison from the lot data, other places from the state's near-stop share × 1.24, as in the re-base.
8. **Training and holdout:** train on the 9 cities. Denver, Portland, Austin and Salt Lake City are held out and scored the same way, with the city as the unit.
9. **The fast fit-and-fix model:** "ΔS rule": change = a + b × (share before − 0.5) + c × reform effect from controls, fitted leaving one city out. Its score is median |log(predicted S after ÷ actual)|. The number is for finding errors only; it is not a tool line. After each run the sanity flags are run and the worst miss is traced.
10. **Framing (as in AQ-068):** like the lot share, this measure cannot tell homes that moved from new homes.

The central line (1,196) stays until this is tested. The Austin and Salt Lake City conditions in NEW_REFORM_CITIES_PLAN.md still apply.

## Committed before any count (2026-11-01)

- **Station lists** (`reference/tod_station_area_stations.csv`, built by `scripts/run_tod_station_area.py --stage stations`). Every rail or rapid stop inside each city's 2024 Census place boundary, from the national transit map's rail stops, LA's G Line, Wisconsin's rapid stops, Denver's RTD stations and Portland's MAX and Streetcar.
  - Reform stations are within ½ mile of the case's upzoned land; control stations are the city's others. Downtown means within 1 mile of city hall.
  - Counts, control / reform: New York 425/122, Philadelphia 335/229, Charlotte 21/23, Chicago 96/182, Los Angeles 212/17, Seattle 31/3, Saint Paul 4/10, Madison 27/105, Bellevue 3/3, Denver 30/5, Portland 19/116, Austin 4/5, Salt Lake City 13/16. Milwaukee has 83 control stations (no reform; placebo).
  - `stop_open_at_reform`: known for Austin and Salt Lake City (no), Denver and Portland (yes). For the 9 cities it is filled from the lot model's case notes when the shares are run.
- **Citywide permit inventory** (`reference/tod_station_area_permit_inventory.csv`). Every city has a whole-city file except Los Angeles, whose downloads hold the reform areas only. Los Angeles uses the Census permit survey place total as its denominator and is flagged "mixed sources; no control stations". Chicago's units are parsed from text, as in its case adapter. Salt Lake City's homes are completions.

**Chicago hand check (audit fix 5; 30 random permits, seed 20261101, read before any share):**
- 27 of 30 were parsed correctly. That includes 14 non-housing permits (tents, cranes, offices) correctly at 0.
- One miss: "erect a new 2 story w/ basement ... attached garage ... RM5" was read as 0, probably 1 home.
- One false positive: "fourth floor addition to existing single family residence" was read as 1 new home.
- One staged permit: "foundation and superstructure through the 4th floor ... 31 story ... 349 dwelling units" counts 349 homes, which a later full permit would count again. The shares stage applies the lot model's staged-permit merge (`case_chicago.dedupe_staged_relaxed`), as in item 32.2.

## Revised design: rates by distance band (DRAFT for the owner's check before anything is counted, 2026-11-01)

Owner, 13:25 and 13:27: measure new homes per 1,000 existing homes in each kind of area. Distance to a high-quality stop stands in for being upzoned. This replaces the share outcome (items 1 and 9 above). The audit's updated list (section E of its pre-registration note) is folded in.

**Bands.** Each permit and each census block goes to its nearest stop.
- **TOD:** within ½ mile.
- **Near:** ½ to 1 mile.
- **Far:** the rest of the city.

TOD takes priority over near. Each band is drawn around reform stops and, separately, around control stops (same city, no reform, open or planned at the reform date).

**Measure.** New homes per 1,000 existing homes per year in each band, before and after; existing homes come from census blocks by centroid. The census is the last one before the reform: 2000 for Austin and Salt Lake City, 2010 for reforms from 2011 to 2020, 2020 for Wisconsin. Anything after the reform is flagged.
- A per-acre version is reported too, because upzoned industrial land with few homes makes per-home rates explode (Denver, Charlotte, parts of Chicago and Philadelphia).
- **Primary version: per 1,000 homes**, matching Wisconsin's near-stop baseline. Per acre is shown beside it.

**Effect.** (After − before in the reform TOD band) − (after − before in the control TOD band). Shown beside it:
- **Near-band spillover:** the same difference for the near band. It can be negative.
- **Far-band check:** the far band's change in reform cities against Milwaukee's (no reform), to test whether homes moved.

**Coverage (revised after the audit, section F).**
- **One definition for training and Wisconsin:** the share of the TOD band's existing homes (census blocks) that sit on upzoned lots. This replaces the earlier land shares, which counted streets and parks for the training cities but not for Wisconsin's 87% (a lots figure). The land shares (Chicago 1% … Bellevue 32%) are kept only as a description.
- **No city-by-city division and no cap.** One pooled ratio of sums: effect per covered home = Σ(city effect × band homes) ÷ Σ(coverage × band homes). Low-coverage cities add little to either sum, so their noise is not multiplied.
- **Two versions, both pre-registered; the owner picks the tool line:**
  - **Raw (distance only):** the measured effect, applied to Wisconsin's band homes.
  - **Scaled (Wisconsin's law):** effect per covered home × Wisconsin's coverage (same definition) × band homes.
- **Testing the straight-line assumption:** coverage goes into the fast model as a trait, with the slope of effect on coverage fitted leaving one city out. Reading set now: if the effect rises with coverage, scaling is supported; if not, that is said beside the scaled figure.
- Wisconsin's coverage is outside the training range (the training maximum is about a third). Under the owner's rule this is stated, not a reason to withhold the number.

**Combining:** the city is the unit. New York's 22 cases and Philadelphia's 64 are averaged, as Portland's and Austin's were (owner's pick pending). Los Angeles has no citywide permits, so it gets the plain change in its reform TOD band, flagged.

**Fast model:** effect per city, leaving one city out, scored by absolute error in homes per 1,000 per year. Benchmarks: zero, and the other cities' average. The 4 new cities are held out. Milwaukee, the placebo, should show about 0.

**Wisconsin formula (fixed now):** raw: extra homes 2027–2031 = effect (per 1,000 existing homes per year) × existing homes in Wisconsin's rail and rapid-bus ½-mile areas (2020 census: 89,528) ÷ 1,000 × 5. Scaled: the pooled effect per covered home × Wisconsin's coverage × 89,528 ÷ 1,000 × 5.
- Bus-only areas get no TOD effect under the owner's pick (pending).
- The result is shown beside 1,196.
- Bands match the near-stop baseline's definition (rail and rapid ½ mile).

**Kept from before:** stop opening year and mode as traits; Milwaukee placebo; Chicago staged-permit merge; Madison with and without; framing that moved homes and new homes are told apart only through the near and far bands.

## Proposed next step: true radius programs (awaiting the owner's go; audit section G noted in advance)

The owner (13:36) pointed out that the training reforms are mostly lot clusters, not radius upzonings like the Wisconsin benchmark.

**Share of buildable land upzoned near each case's stations** (gross land × 0.75 for streets), within ¼ mile / ½ mile:
- LA Warner Center 74% / 57%; Bellevue BelRed 72% / 43%;
- Austin 37/20, Charlotte 35/19, Salt Lake City 32/21, Saint Paul 30/13, LA Cornfield 23/17, Denver and Portland 16–20/18;
- Seattle and Madison 12–20 / 5–10; New York, Chicago and Philadelphia 2–8 / 1–4.

**Proposed radius cases:** LA Transit Oriented Communities (2017); San Diego Complete Communities (2020); Chicago Connected Communities (2022). The audit's conditions, to be locked once the owner says go:
1. **Controls:** same-type stops in other cities of the same metro without the program (LA County cities outside Los Angeles, San Diego County cities, Cook County suburbs). The ½–1 mile band is not used as a control, because of spillover.
2. **Windows:** LA 2011–16 before and 2018–22 after; San Diego 2014–19 and 2021–25; Chicago 2016–21 and 2023–25. No COVID or interest-rate adjustment; the outside-city controls absorb those shocks.
3. **LA TOC is opt-in by incentive.** It counts, with "incentive vs by-right" as a trait; Wisconsin's benchmark is by-right.
4. **San Diego and Chicago also changed parking rules**, so their effect is upzoning plus parking. This is stated, and the combined view's max rule keeps the two from being added.
5. **LA TOC is not blind** (LA_TOC_RESULTS.md exists), so it is used for training only.
6. **Stop lists and radii** are each program's own on its adoption date. They include frequent buses, which is closer to Wisconsin's definition.
7. **Coverage** is measured the same way everywhere. Wisconsin's 87%, a share of lots, is recomputed on the buildable-land basis.
8. **Weighting:** the radius programs are the main evidence; the cluster cases feed the coverage slope. With 3 cases, scoring is leave-one-out and labelled "3 cases".
9. **Coverage stays a continuous trait**, with no "radius-like" cut-off.

### Radius programs: scoping so far (2026-11-01; owner said go to scoping, 13:43)

| Program | In force | Radius rule | Stops | Whole-city permits with homes | Status |
| --- | --- | --- | --- | --- | --- |
| Los Angeles Transit Oriented Communities | 22 Sep 2017 (guidelines revised Feb 2018) | Four tiers within ½ mile (2,640 ft) of a major transit stop | Rail stations and crossings of two 15-minute bus routes (existing or planned) | Yes: LADBS permits 2010–2019 (`dyxf-7hc4`) and 2020 on (`pi9x-tg5x`), `du_changed`, lat/lon | Training only (not blind; LA_TOC_RESULTS.md exists). Opt-in incentive with affordable homes |
| San Diego Complete Communities Housing Solutions | 8 Jan 2021 (ordinance O-21275); later amendments 2022 and 2023, which moved to "Sustainable Development Areas" | Transit priority areas: ½ mile of an existing or planned major transit stop | State major-transit-stop definition (includes frequent buses) | Yes: city Housing Element permit layer (webmaps.sandiego.gov PLN_Housing_ServiceLayers/0), 2003–2026, `TOTAL_DU`, lat/lon; use Building Permit + Combination Building Permit only (2018: 6,373 homes; check against the Census permit survey for double counts) | Candidate. After window 2022–2025 (4 years). Parking rules also changed |
| Chicago Connected Communities | Adopted 20 Jul 2022 | ½ mile (2,640 ft) of rail entrances; ¼ mile (1,320 ft) of listed bus corridors | CTA rail and listed bus corridors | Yes: city permits (units parsed from text; staged-permit merge) | Candidate. After window 2023–2025 (3 years, the minimum). Parking also changed |
| Honolulu TOD Special District, Waipahu | October 2017 (ordinances 17-54 and 17-56); other station areas later | Special district around each rail station; mixed-use zoning replacing single-use | Skyline rail (opened June 2023; planned at the reform; a trait) | Yes: building permits 2005–June 2025 (`4vab-c87q`), `numunitsadd`, location | Candidate |
| Seattle Mandatory Housing Affordability | March 2019 | No: urban-village boundaries, some widened to a 10-minute walk of light rail or two frequent bus lines; zoning drawn by hand | Light rail, frequent bus crossings | Yes (Seattle permits) | Cluster-style, not a radius rule. Usable as a hand-drawn comparison only |
| Minneapolis 2040 | January 2020 | No: corridor districts along transit routes plus citywide three-unit lots | Corridors | To check | Corridor-style, not a radius rule; also a citywide change, so no in-city control. Drop |
| Raleigh frequent transit areas | 2022 onward (BRT corridors) | Corridor overlay along bus rapid transit lines | BRT (opened 2025 or later) | To check | Too recent and corridor-style. Drop for now |
| Washington HB 1110, Massachusetts MBTA Communities, Charlotte UDO, Toronto station areas, California SB 79 | 2023–2025 | Yes | — | — | Too recent (under 3 after-years) |

Nothing is counted until the owner confirms the locked plan.

### Owner change (2026-11-01 13:48): split the inner band

"we can differentiate between .25 and .5 mile." The TOD band becomes two bands: inner (0 to ¼ mile) and outer (¼ to ½ mile). Each gets its own rate per 1,000 existing homes, its own reform-minus-control effect, and its own coverage. Wisconsin is applied band by band (homes within ¼ mile, and homes from ¼ to ½ mile, of rail and rapid stops). Programs with a ¼-mile rule (Chicago bus corridors) count only in the inner band for those stops.

### Owner proposal (2026-11-01 13:56): test traits in three stages

1. Block traits (distance band, existing density, vacant land, land value, home prices).
2. Stop traits (rail or bus, open at reform or not), tested on what stage 1 leaves unexplained.
3. City traits, a short list of the biggest theories only (by-right or incentive, parking cut too, market strength), tested on what stages 1–2 leave unexplained, at most 1–2 kept.

Every stage is scored by hiding a whole city at a time. A stage's traits are kept only if they beat the stage before. The order and the city shortlist are fixed before any counting.

### Owner note (2026-11-01 13:57): lot rows for stage 1

Use lot-by-lot rows where parcels allow: vacancy, existing homes on the lot, lot size, building-to-land value as lot traits. New homes are predicted per lot, summed by band, divided by the band's existing homes (rate per 1,000). Parcel tables are needed for San Diego, Chicago and Honolulu (to fetch and check fields). Wisconsin uses the statewide parcel layer. Blocks are the fallback where parcels lack those fields.

### Structure and baseline (2026-11-01 14:03, owner questions)

- Steps B–C end in one frozen lot table (band, lot traits, before/after counts, reform or comparison stop, coverage). Step D reads only that table, so a model can be swapped by rerunning D and E only.
- Baseline: the shared all-housing baseline v3 (14,654 near stops over 5 years). This method adds extra homes on top; comparison stops are used only inside training cities. Check: Wisconsin before-rates × band homes should roughly match 14,654.

### Trait list draft (2026-11-01 14:05; owner list plus additions, awaiting lock)

Stop: rail or bus (GTFS); trips per hour as ridership stand-in (GTFS); distance to downtown; years since opening.
Neighborhood (ACS block group unless noted, values from before each reform): car ownership; commute time; transit commute share; income; median rent; median home value; vacancy rate; FHFA tract price index; jobs nearby (LEHD LODES; EPA Smart Location Database); age of existing buildings.
Lot (assessor; FEMA; NRHP): vacant; existing homes; lot size; building-to-land value; publicly owned; floodplain; historic district.
City: by-right or incentive; parking cut at same time; affordable units required; coverage; metro permits per person (Census BPS).
Caveat: ACS block groups start 2009; earlier reforms use Census 2000.
Market strength at lot level (owner question 14:06): land value per sq ft (assessor, ranked within city); recent sale price and date (assessor or deeds; WI real estate transfer returns); building-to-land value; permits within ~500 ft in the 5 years before the reform (no after-reform years, to avoid leakage); building age. ACS and FHFA tract measures kept as neighborhood backups. Check point-permit coverage across Wisconsin before relying on the nearby-building trait statewide.

### Trait list by level (2026-11-01 14:12, shown to owner; 32 traits)
Lot (11): vacant; existing homes; lot size; land value per sq ft; building-to-land value; building age; recent sale price; publicly owned; floodplain; historic district; permits within ~500 ft in prior 5 years.
Block (2): existing homes per acre; jobs nearby (LEHD).
Block group (8, ACS before reform; EPA): car ownership; commute time; transit commute share; median income; median rent; median home value; vacancy rate; walkability.
Tract (1): FHFA home price trend.
Stop (5): rail or bus; trips per hour; years since opening; distance to downtown; band.
City (5): by-right or incentive; parking cut at same time; affordable units required; coverage by band; metro permits per person.
Rent, value, income, land value tested first as one "market strength" group.

### Correction (2026-11-01 14:13): start from the lot model's 125 traits
Source: reference/tod_lot_model_importance_runD_allvars_rebuilt_seed7.csv. 78 tract census traits (v_h 21, v_p 22, v_m 18, v_c 14, v_l 3); 17 lot; 5 location; 21 zoning-map flags (group_ 11, reform_share 7, upzoned, share_upzoned_half_mile, in_reform); 4 missing-data flags. Plan: keep the 104 non-map traits; replace the 21 map flags with distance band and coverage; add the new traits from the 14:12 list. About 120 traits in total.

### Trait list v2 (2026-11-01 14:15, owner: keep 104, replace map flags, add new) — 123 traits
Lot 26 = kept 20 (soft_site, soft_missing, log_width, log_acres, use_ind/res/com/mixed, homes_on_lot, homes_missing, age, built_before, rent_to_cost, log_near_before; zoning-rule traits level_rank_in_city, rel_gain, rel_gain_known, far_now, far_known, pays_room) + new 6 (land value per sq ft, building-to-land value, recent sale price, publicly owned, floodplain, historic district).
Block 2 = log_census_homes + jobs nearby (LODES).
Block group 1 = walkability (EPA Smart Location Database).
Tract 82 = 78 ACS v_ traits + log_rent, log_value, log_income + FHFA price trend.
Stop 7 = log_stops_1mile, log_dist_station + band, rail or bus, trips per hour, years since opening, distance to downtown.
City 5 = by-right or incentive, parking cut, affordable units required, coverage by band, metro permits per person.
Decided (owner 14:18): keep the 6 zoning-rule lot traits, with a "rules unknown" flag where no zoning layer exists.
Bottlenecks (owner 14:18): tract (82 traits on about 1,000–2,000 tracts) is tested first as about 5 groups (housing stock, people, commuting, costs, density), with single traits only inside a group that earns its place; city (5 traits on about 10 cities) is tested one trait at a time, with at most 1–2 kept, and untestable ones shown as a with/without range.
City traits (owner 14:20): bring the owner the actual split at step D3. Incentive and affordable-required are grouped as one "strings attached" trait. If only one city has strings attached, flag it and propose dropping it from training rather than spending a city test on it. Rough split now (to confirm in step B): strings attached = LA TOC, probably San Diego, Seattle (affordable only); parking cut too = San Diego, Chicago, LA TOC.
City market strength (owner 14:23): tracked and reported for each city (metro home price ÷ building cost; metro permits per person beside it) but not used in the city-level tests. Added as tested traits: population growth (tract; Census 2000/2010/2020, ACS) and job growth (block; LEHD). Trait count: 124 tested (lot 26, block 3, block group 1, tract 83, stop 7, city 4, with incentive and affordable-required tested together as "strings attached") plus 1 tracked.
City tests (owner 14:25): incentive-vs-by-right and inclusionary requirement tracked separately, tested only together as "strings attached"; parking cut tracked, not tested. Proposed (awaiting owner OK): coverage measured per stop and band (share of that stop's band homes upzoned) and carried on each lot, making it a stop-level trait; the city level then tests only strings attached. Radius programs anchor the near-100% coverage end that Wisconsin's law implies.
City slot (owner 14:29): one spare city test slot is held open; parking cut is the leading candidate, to decide once the split is seen.

## LOCKED (owner "go for it", 2026-11-01 14:29)
Cities: Charlotte, Austin, Salt Lake City, Seattle, LA Warner Center, Bellevue BelRed; LA TOC (training only), San Diego CCHS, Chicago Connected Communities 2022, Honolulu. Bands 0–¼, ¼–½, ½–1 mile, farther (exact distance in the model). 124 tested traits; stage order lot/block → tract (≈5 groups first) → stop (coverage per stop and band) → city (strings attached; one spare slot, parking cut leading). Shared baseline v3. Steps B–E as listed 13:59; frozen lot table between C and D. Any change after this point goes back to the owner.

### How the locked plan meets audit section G (2026-11-01)
1. **Out-of-city metro controls.** For the radius programs, comparison stops are same-type stops in other cities of the same metro: LA (Metro rail and frequent-bus stops in Pasadena, Long Beach, Santa Monica, Culver City, other LA County cities), San Diego (trolley and rapid stops in Chula Vista, National City, La Mesa, El Cajon, Santee), Chicago (CTA stops in Evanston, Oak Park, Skokie, Forest Park, Cicero). Honolulu has no out-of-city rail (the city is the whole county): its comparison is island bus-trunk stops outside the TOD districts, flagged as a weaker control and shown with and without. The six existing cluster cases keep their in-city uncovered-stop comparisons, with out-of-metro-city stops added where the metro has them (Seattle, Bellevue, Charlotte none, Austin none, SLC: UTA stops in other cities).
2. **Set windows (fixed now, before counting).** LA TOC 2011–16 before / 2018–22 after; San Diego 2014–19 / 2021–25; Chicago 2016–21 / 2023–25; Honolulu 2011–16 / 2018–25 (rail opening 2023 is a trait); existing six keep the windows already used in the lot model and new-city test.
3. **Incentive vs by-right.** Tracked separately with inclusionary requirements; tested only together as one "strings attached" city trait. LA TOC is training only. If only one city has strings attached, the owner is asked whether to drop it from training.
4. **Parking overlap.** Parking cut is tracked per city and held as the leading candidate for the one spare city test. San Diego and Chicago results are shown with and without, and the combined view's rule (b) is unchanged.
5. **Wisconsin coverage on the same definition.** Coverage is the share of homes in each stop's band that sit on lots the reform upzones. Wisconsin's is recomputed per stop and band the same way: the share of band homes on lots the proposed law would upzone (eligible zoning classes), not assumed 100%.

### Auditor fixes applied (2026-11-01 14:32; review: audit/tod_station_area_locked_plan_review_2026-11-01.md)
- San Diego windows corrected: before 2015–20, after 2021–25 (in force 8 Jan 2021). This replaces the 2014–19 before window above and the "2022–2025" note in the scoping table.
- Honolulu: primary after window 2018–22; second version 2023–25 (after the rail opening).
- Each comparison city will be listed with "own TOD rezoning in window: yes/no + source"; stops in cities that did their own are flagged and shown with and without.
- Put to owner (pending): keep all 14 cases with coverage as the trait (auditor's recommendation) or one written coverage rule; county year-built for comparison areas; bus-only Wisconsin areas get no TOD effect; average NYC and Philadelphia; single strings-attached city shown with and without, or dropped.

### Step B log
- **San Diego permits** (2026-11-01): 23,054 permit records fetched (building and combination permits with homes). Cleaned in `sd_permits()`: issued only; new-home job codes only; legacy one/two/three-four-family permits capped at 1/2/4 homes (some store the whole subdivision on each permit, e.g. 35,200 "homes" on a 2006 garage permit, 3,954 on one 2017 two-family permit); one row per approval. Against the Census permit survey for San Diego city: 0.83 of Census homes in 2015–20 (26,195 vs 31,564) and 0.81 in 2021–25 (22,958 vs 28,418), steady across the windows; 2021 is low (0.58) during the move to the new permit system in Dec 2021. Remaining gap is likely ADUs and permits outside the layer; same share before and after, so the before/after change is not biased by it.
- **Los Angeles permits, whole city** (2026-11-01): 103,808 new-building permits (LADBS e67z-kt2n, dyxf-7hc4, pi9x-tg5x). Against the Census permit survey for Los Angeles city: 0.94–1.04 a year in 2008–2022 (2011–16 and 2018–22 windows both within 0.91–1.04); later years drift lower (0.78 in 2025). Homes without a location: 0.2% (2011–16) and 1.3% (2018–22); all have parcel numbers, so they can be placed later if needed.
- **Honolulu permits** (2026-11-01): 32,608 permits with homes added (data.honolulu.gov 4vab-c87q). No coordinates: placed by tax-map key on Oahu parcels (State GIS mirror of HOLIS, April 2026).
- **Honolulu permits cleaned** (`hnl_permits()`): issued only; hotels and foundation-only permits removed; one row per tax-map key, year, homes and address. Against the Census permit survey (Honolulu): 1.14 in 2011–16 and 1.17 in 2018–22 (steady); single years swing (2021: 2.6, 2023: 0.63) because high-rise permits and the Census count fall in different years. Placement: by tax-map key on today's parcels 77% (2011–16) / 88% (2018–22) of homes; the rest at the centre of their plat (parcels redrawn since; a plat is roughly block-sized); permits with no tax-map key (5–8% of homes) are left out, flagged.
- **Program maps** (2026-11-01): LA TOC tiers as of October 2017 (City Planning layer `TOC_Tiers_Oct2017_new`): tier 1 110 sq mi, tier 2 49, tier 3 65, tier 4 4; 228 sq mi in all, about half the city, so LA's comparison must come from other cities (as planned). San Diego transit priority areas (City Planning layer): 124 sq mi, but this copy was redrawn in January 2026 (2050 regional plan), not the 2021 day-one map; the day-one map is still needed (archive copy, or rebuild from the 2021 regional plan's major transit stops). Chicago has no published layer: it will be built from CTA and Metra rail entrances (2,640 ft) and the ordinance's listed bus corridors (1,320 ft).
- **San Diego day-one map**: SANDAG's hosted copy of the City's transit priority areas (created Oct 2022, 2021 regional plan) is 116 sq mi; the City's January 2026 copy is 124 sq mi and contains 99% of it. The 2022 copy is used as the reform map (closest available to January 2021), flagged: at the January 2021 start the rule used the then-current map, which may differ at the edges.
- **Honolulu maps**: the 2017 TOD zone changes are hand-drawn (Waipahu Transit Center: 38 pieces; West Loch: 30 pieces, mostly business/apartment/industrial to mixed use, 60–90 ft), so Honolulu is a cluster case with coverage measured, not a full radius. HART stations: 21 (opened 2023 and later). Comparison for Honolulu: rail stations whose own TOD rezoning came after the window (adoption dates per station to confirm), plus bus-trunk stops, flagged as in-city controls.
- **Stops for comparison metros**: the national transit map rail stops cover LA County (497 stops within the metro box), San Diego County (225), Chicago area (686) and Seattle area (140); Honolulu rail comes from HART.
- **County property records** (fetching, local only, no owner names): San Diego County parcels (SANDAG copy of the Assessor file, 1,089,056 parcels: land and building values, homes, effective year built, last recorded document date, land use, zoning, point); LA County parcels (2,433,309: year built and homes for up to five buildings, roll values with base years, use, public-agency flag, centre point); Honolulu assessed land and building values by tax-map key (325,559 rows; no year built or homes in the open file, but Honolulu's permit file covers the whole island, so its comparison stops can use permits).
- Caveat for California land values: under Proposition 13, assessed values reflect the year of last sale, not today's market; the base year is kept so the trait can be adjusted or ranked within sale-year groups.
- Chicago bus corridors: the ordinance's list could not be downloaded (city site refuses automated downloads); owner asked to save the PDF. Until then Chicago's reform area is ½ mile of rail only, flagged.
- **National trait files** (`scripts/fetch_tod_station_traits.py`): LEHD LODES jobs by block for 13 states, 2004–2022 (fetching); National Register of Historic Places polygons, all states (22,905, with listing dates). Floodplain (FEMA flood hazard areas) will be queried per station area when the lot table is built; transit trips per hour needs archived schedule files from the reform years (to source).
- **San Diego County parcels fetched** (1,089,056; city of San Diego 393,788). Year field is the Assessor's two-digit *effective* year (a major remodel can move it forward, so some older buildings would read as new); "00" mixes 2000 and unknown (43% of "00" parcels have a building). City of San Diego homes by effective year: 2015 6,338; 2016 4,868; 2017 3,966; 2018 5,555; 2019 5,542; 2020 6,637; 2021 5,749; 2022 5,175; 2023 4,750; 2024 7,103; 2025 8,697 — same scale as permits (2,800–5,900 a year), consistent with completions lagging permits plus some remodels. If the owner approves county year-built counts for comparison areas, this caveat goes with San Diego.
