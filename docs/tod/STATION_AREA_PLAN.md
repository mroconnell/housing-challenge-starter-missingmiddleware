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
- **National trait files** (`scripts/fetch_tod_station_traits.py`): LEHD LODES jobs by block for 13 states, 9 years 2004–2022 (117 files, none missing); National Register of Historic Places polygons, all states (22,905, with listing dates). Floodplain (FEMA flood hazard areas) will be queried per station area when the lot table is built; transit trips per hour needs archived schedule files from the reform years (to source).
- **San Diego County parcels fetched** (1,089,056; city of San Diego 393,788). Year field is the Assessor's two-digit *effective* year (a major remodel can move it forward, so some older buildings would read as new); "00" mixes 2000 and unknown (43% of "00" parcels have a building). City of San Diego homes by effective year: 2015 6,338; 2016 4,868; 2017 3,966; 2018 5,555; 2019 5,542; 2020 6,637; 2021 5,749; 2022 5,175; 2023 4,750; 2024 7,103; 2025 8,697 — same scale as permits (2,800–5,900 a year), consistent with completions lagging permits plus some remodels. If the owner approves county year-built counts for comparison areas, this caveat goes with San Diego.
- **LA County parcels fetched** (2,433,309, all with centre points; 3.82 million homes in all, close to the county's ACS count of about 3.6 million). Homes by year built in Los Angeles (situs city): 2011 2,563; 2013 5,831; 2015 6,375; 2016 11,764; 2018 11,806; 2019 14,184; 2020 12,006; 2022 11,325 — following city permits (2013 8,385 → 2015 16,100) about two years later, as expected for completions.

### City list decision (owner 2026-11-01 15:01): all cases, coverage as the trait
"Run it your way for now, we may revisit and run it based on coverage and benchmark coding later." Training cases: New York (23 rezonings) and Philadelphia (85 rezonings), each one case for city-level tests (averaging pick still pending); Chicago 2015 TOD ordinance; Saint Paul; Charlotte; Seattle (Othello 2012, Mount Baker 2014); LA Warner Center; LA Cornfield–Arroyo Seco; Bellevue BelRed; Denver 2018; Portland 2020; Austin 2009; Salt Lake City 2010; LA TOC 2017 (training only); San Diego 2021; Chicago Connected Communities 2022; Honolulu 2017. Madison 2023 is a Wisconsin check, not training (after window too short). A later version may select by coverage and by design against the benchmark (option B), written as a rule before it is run.
- **King County records** (Seattle, Bellevue and their comparison cities): Assessor building extracts (parcels, residential buildings, apartment complexes, commercial buildings, condo complexes: year built and homes) and 636,786 parcel points with appraised land and building values, zoning, use, lot size (Seattle 180,410; Bellevue 33,003). 9.7% of parcels lack a point (mostly unaddressed or condo-unit records): to place from the parcel shapes if they matter near stops.
- **Cook County records** (Chicago and its comparison suburbs): parcel universe and assessed values for 2016 and 2024, residential characteristics 2024 (fetched: 1.86 million parcels each year; 1.10 million residential building records). Year built is missing for large apartment and condo buildings in the open files, so county year-built counts would undercount Chicago-area apartments; Chicago-area comparison counts may need suburban permit files instead (flagged for the owner's year-built decision).

### Owner answers (2026-11-01 15:57: "Yes to all")
- Comparison areas count homes from county year-built records (same source on both sides), with city permits as a check in reform cities; where a county file lacks year built for large buildings (Cook), suburban permit files are used instead, flagged.
- Wisconsin areas served only by regular buses get no TOD effect.
- New York's and Philadelphia's many rezonings are averaged into one case each for city-level tests.
- If only one city has strings attached, it is shown with and without.
- **Chicago ordinance file** (owner-supplied, saved as data/raw/tod_radius_programs/chicago/connected_communities_ordinance.pdf): it is the City's two-page summary, not the ordinance text, so it has no list of bus corridors. It confirms: benefits within a 10-minute walk of every CTA and Metra station and a 5-minute walk of "corridors with high-frequency bus service and/or strategic potential"; TOD density incentives require more affordable units (so Chicago 2022 counts as strings attached); residential parking capped at 1 per 2 homes; no parking required for affordable housing. Chicago's reform area stays rail-only (½ mile) as the main version; a second version adds CTA's high-frequency bus routes (¼ mile), flagged as an approximation of the ordinance's list.
- **Salt Lake County parcels** (Utah UGRC LIR, 399,432 parcels with centre points): market land and total values, year built and effective year, homes, class. **Saint Paul parcels** (83,420): market values, land use, year built, homes, last sale, points; owner fields not requested.
- **More parcels**: Denver whole city (240,496: class, zoning, appraised values, year built, homes, last sale; no owner fields); Mecklenburg County (NC OneMap: values, structure year, use, sale date; no homes field, so Charlotte counts come from permits); Travis County (386,682 TCAD parcels: land value and zoning only, current values; Austin counts from permits); Portland-area taxlots (tri-county, 607,019: year built, homes, values for three years, sale). Charlotte and Austin have no rail stops in other cities of their metros, so their comparison stops stay in-city, flagged like Honolulu.
- **Open data gaps (to settle before step C)**: (1) Chicago-area comparison counts: Cook County's open files give year built for houses and 2–6-flats but not for large apartment or condo buildings; options are suburban permit files (Evanston, Oak Park, Skokie publish some) or counting new condo and apartment parcel numbers as they first appear in the Assessor's yearly parcel universe; to test both on a sample. (2) Transit trips per hour in the reform years needs archived schedule files (GTFS) per agency; today's schedules are available everywhere, archives are not uniform. (3) Floodplain from FEMA flood hazard areas, queried per station area when the lot table is built. Twin Cities parcel points (Hennepin, Ramsey) fetching for Saint Paul's Minneapolis comparison stops.
- **Transit frequency source (owner 16:41: use a national database)**: EPA Smart Location Database transit frequency per block group (D4-series: service frequency within ¼ mile, evening peak), 2013 version (2012 schedules) for before-reform values and 2021 version (2020 schedules) for later reforms and Wisconsin. Replaces per-stop trips per hour from archived schedules. Public domain; same method for every agency.
- **EPA Smart Location Database fetched**: version 2 (2017 release, 2012 schedules; 399 MB) and version 3 (2021, 2020 schedules; 553 MB), national file geodatabases, public domain. Transit frequency is used per block group (owner 16:42: block group is fine); rail or bus, distance and years since opening stay per stop.

### Hand checks (30 random permits per new city, seed 20261101, before any counting)
- **Los Angeles**: 27 of 30 read correctly (homes match the work description; garages, carports, shade structures correctly at 0; ADUs sit in their own field). 2 double counts: a "supplemental to permit …" and a "permit extension … re-check plans" each repeat an earlier permit's homes. Across the city such supplements and extensions carry 0.7% of homes in 2011–16 and 1.0% in 2018–22, nearly equal, so left in and flagged. 1 unclear: "21-unit apartment" recorded as 13 homes added (likely net of homes demolished).
- **San Diego**: the layer has no work description, so the check is on job type and status: 30 of 30 handled as intended (5 cancelled permits dropped; 9 ADU/companion-unit permits excluded, as ADUs belong to the ADU scenario; one-family permits at 1 home).
- **Honolulu**: 2 revoked permits correctly dropped; but ADU and ohana permits (5 of 30) were being counted. Fixed: ADU, ohana and "accessory dwelling" permits now excluded, as in LA and San Diego. After the fix Honolulu matches the Census permit survey: 1.02 in 2011–16, 1.00 in 2018–22, 1.06 in 2023–25 (was 1.14–1.17).

### Step C, first pass (2026-11-01; fit-and-fix, nothing final)
`scripts/build_tod_station_lot_table.py` builds the lot table for LA TOC, San Diego and Honolulu (lots within 1 mile of a reform or comparison rail stop; bands by distance; coverage = share of lots in the program map; new homes from county year built on both sides, Honolulu from island-wide permits). Fixes made in the first rounds:
1. San Diego: the same building on two records (possessory-interest copy) and condo master records duplicating their unit parcels — removed.
2. Existing homes: buildings with unknown year now count as existing (were dropped).
3. Implausible counts: more than 2,000 new homes per acre (catches the LA roll's placeholder counts 999/1,001/1,003 on small lots; 5 lots, 5,001 homes). A building-value test was tried and dropped: LA's roll carries many new buildings at a partial in-construction value.
4. Honolulu values: condo units summed to their parcel.
Open issues found:
- **Completion lag**: year built counts finished homes, about two years after the permit, so an "after" window starting the reform year mostly counts projects permitted before the reform. Proposed fix (for the owner): shift year-built windows two years later (LA 2013–18 / 2020–24; San Diego 2017–22 / 2023–25, three after-years).
- **Big projects dominate**: lots with 100+ new homes carry 53% (LA), 61% (San Diego), 69% (Honolulu) of new homes; each is listed for a hand check (e.g. an 838-home record in Lemon Grove, 1.25 acres).
- Honolulu existing homes need census blocks (not yet joined); Honolulu's two reform stations saw almost no building (2 and 4 homes within ¼ mile).
- **Traits joined** (`scripts/enrich_tod_station_lots.py`, all three first-pass cases): EPA Smart Location Database per block group (transit frequency, frequency per square mile, jobs per acre, transit job access, share of households with no car, walkability index); block-group job growth over the 5 years before the reform (LODES, 2020 blocks); historic register (listed before the reform); the lot model's 78 tract variables from the ACS ending the year before the reform (filled for 99–100% of lots). Method note: versions 2 and 3 of the Smart Location Database measure transit frequency on different scales (California block groups: median 12.7 vs 4.3; rank correlation 0.57), so version 3 (2020 schedules) is used for every case and for Wisconsin, with version 2 kept beside it as a check. Census 2016–20 sequence files for California and 2010 tract shapes for Colorado, Hawaii and Oregon were added to the ACS fetch.
- **Step D scaffold** (`scripts/run_tod_station_model.py`): per case and band, effect = change at reform stops − change at comparison stops (new homes per 1,000 existing homes per year), raw and scaled by coverage difference (only where coverage is 20% or more; below that, scaling multiplied noise, e.g. Honolulu ¼–½ mile at 9% coverage gave −117); New York and Philadelphia rezonings averaged per city; pooled average per band with leave-one-out range; scores vs zero and vs others' average.
- **Honolulu first look (not final)**: the two 2017 TOD stations (Waipahu, West Loch) saw almost no building (2 and 4 homes within ¼ mile in the windows) while the comparison stations include the downtown/Kaka'ako towers (32.6 → 45.1 per 1,000 a year within ¼ mile). The comparison set is not like-for-like; proposal: restrict Honolulu's comparison to stations outside the downtown–Kaka'ako–Ala Moana core (or rely on traits to absorb it), for the owner and auditor.
- **Hand check of every lot with 100+ new homes** (LA 223 rows, San Diego 92, Honolulu 32; local file data/processed/tod_station_area/hand_check_big_lots.csv): confirmed or plausible on most; 44 wrong counts, 5 duplicates, 32 unverifiable. Main finding: county unit fields count **hotel rooms, self-storage units and beds** as homes (LA use codes 18xx: 21 hotels; San Diego land use 26 hotels, 44 storage; the 1,600 "homes" in Chula Vista are the Gaylord Pacific resort's rooms; the 838 in Lemon Grove are a Public Storage building). These sit mostly on the comparison side (other cities have no permit cross-check), so they inflated comparison growth. Fixed: LA 18xx and San Diego 26/44 carry 0 homes; wrong counts take the corrected number; duplicates go to 0; unverifiable lots are flagged (column hand_check) for a with/without check. Honolulu: Symphony Honolulu counted twice (foundation and building permits), corrected to 388.
- **Cluster cases built by helper module** `scripts/station_cases/cluster_west.py` (Denver 2018, Portland 2020, Austin 2009, Salt Lake City 2010): condo master and twin records removed (Denver 47,069 homes), storage/hotel/nursing units zeroed, permits placed on their own parcel or the nearest lot big enough (unplaced homes 0.2–5%), Austin cut to its Travis County part, Salt Lake City uses the city's housing unit inventory (the county file misses apartments). Census permit-survey ratios before/after: Denver 0.92/0.85, Portland 0.99/1.42, Austin 1.12/1.06, Salt Lake City 1.25/1.81 (completions vs permits). Flags: Austin has one comparison stop; Portland's reform reached 75 of 88 stops, leaving few comparison stops; Salt Lake City's comparison is in-city.
- **Per-building events (owner 17:33)**: each case also saves events_<case>.parquet (local): one row per new-building record from 2000 on, with permit year and/or completion year, homes, source, the preferred date type for that case (the one available on both sides of its comparison), and the lot's hand-check flag. Window totals are computed from it at model time, so windows can be shifted or the date type switched without re-collecting. First cases: LA 58,041 rows (permits 131,997 homes on the city side; county year built 188,953 homes on both sides); San Diego 27,230 (year built); Honolulu 3,279 (permits, island-wide). Hand-check corrections are recorded at lot level; in events they show as the lot's flag.
- **Estimated permit year (owner 17:33)**: third date column = actual permit year where known, else completion year minus the typical gap by building size, measured in LA on 8,091 lots with both an LADBS new-building permit and a county year built (gap 1 year before to 6 after): median 1 year for 1, 2–4 and 5–49 homes, 2 years for 50+ (means 1.04, 0.70, 1.53, 1.91). To be re-measured with Denver's matched pairs and checked (share of LA buildings whose estimated year equals the actual). Windows run on this column by default.
- **Gap check**: in LA the estimated permit year equals the actual one for 49% of matched buildings and is within 1 year for 94% (9,246 buildings). Denver's matched pairs (6,690 buildings) show a median gap of **0** years in every size group (means 0.09–0.32): Denver's assessor year built is close to the permit year. So the gap is a property of each county's records, not of construction: it will be measured per county wherever both dates exist (LA, Denver, San Diego city permits vs county records; San Diego, 860 lots: medians 1, 1, 2, 2 by size), and counties with no pairs will be flagged as using another county's gap.
- **North cases** (`scripts/station_cases/cluster_north.py`): Seattle Othello 2012 and Mount Baker 2014 (2 reform / 8 in-city / 2 out-of-city comparison stations), Bellevue BelRed 2009, Saint Paul 2011 (one before-year, 2010), Charlotte 2019. Fixes: King County rental buildings in a condo regime carried all homes on one or two unit records (about 30,000 homes missing; now the complex's home count), Charlotte floor-by-floor staged permits deduplicated, Saint Paul hotel and nursing-home units dropped (3,668), same-line-status stations only, Othello and Mount Baker lots excluded from each other's comparison. Census ratios (before/after): Othello 1.15/1.06, Mount Baker 1.00/1.03, Bellevue 0.93/0.75, Saint Paul 3.00 (one year, 66 vs 22)/0.68, Charlotte 0.88/0.95. Flags: Minneapolis parcel points have no home counts, so Saint Paul has only in-city comparison stops; Charlotte's comparison includes the streetcar (different mode) and only two Blue Line stations; Redmond's Overlake stations had their own rezoning (flag for Bellevue). Builder change: towers on small parcels are no longer "implausible" when the building is worth $150,000+ per home (6 real Seattle towers were being dropped).
- **Stage 0 first look** (estimated-permit-year dates; 14 cities with partial New York/Philadelphia/Chicago; not final): within ¼ mile, effect per 1,000 existing homes averages 100 a year but the median is 24, because places with few homes before (BelRed's industrial land: 727) blow up the denominator. Per 100 lot acres the ¼-mile effect is steadier: average 29 new homes a year (leave-one-out 22–34; median 18); ¼–½ mile −2 and ½–1 mile −1 (about zero). Others' average does not yet predict a left-out city better than zero (¼ mile: error 37.9 vs 37.3 per 100 acres). Added per-acre effects beside the per-1,000-homes ones (planned as the second version).
- **New York and Philadelphia** (`scripts/station_cases/nyc_phl.py`): 23 + 85 rezoning cases (2 and 19 have no reform stop and serve only as comparison, flagged). New York existing homes from MapPLUTO (vintage before each reform), permits placed by lot number; "1-2-3 family" jobs capped at 3 homes (two jobs carried 3,291 and 4,871); refiled jobs counted once; 2002–03 lots matched by lot number (had duplicated ~95,000 points per case). Philadelphia existing homes from 2010 blocks weighted by building type (OPA has no homes field); hotels, dorms, rooming houses, nursing homes and ADUs left out. Census ratios: New York 1.00–1.19 by window; Philadelphia 1.03–1.26. Remaining: New York towers on one tax lot of a multi-lot zoning lot exceed 2,000 homes per acre (3.8% of new homes; New York's file cannot exclude hotels or dorms); Philadelphia's after windows include the 2021 rush before the tax-abatement cut (both sides).
- **Is the ¼-mile concentration real where the rule covers ½ mile? (owner, 17:56)** Early read (stage 0, per 100 lot acres a year): LA TOC −4.5 (0–¼) / +1.3 (¼–½); San Diego −10.7 / −12.1; cities whose ¼-mile band was mostly upzoned only (coverage < 50%) median +23.8 / +2.6. So the ¼-mile pattern so far comes from cluster cases; the two true ½-mile programs show no gain in either band against their comparison stops. Caveats: LA and San Diego counts are county completions with an estimated permit year; San Diego has 3 after-years; LA's comparison cities boomed near their own stations. Recheck with Chicago 2022 and the trait model.
- **Chicago 2015 and 2022** (`scripts/station_cases/chicago.py`): county year built on both sides (no suburban permit file found; new-PIN counting rejected: one 8-year span, no apartment units, mixes in condo conversions). Added Cook Assessor files: 2026 residential characteristics, 2026 condo units, 2021–25 commercial (apartment) sheets; hotel, nursing, hospital, assisted-living, parking and storage units removed; north-suburb unit counts from unit-mix fields; earliest year built across sheets (trails permits by about a year). 194 Chicago and 74 comparison stops (Evanston 10, Oak Park 6, Blue Island 6, others 1–3). Census ratios for county year built: 2009–14 1.60 (boom projects finishing), 2016–21 0.96, 2023–25 1.04. **Flag:** the county's apartment sheets end in 2023 for the south suburbs (Oak Park, Cicero, Berwyn, Forest Park), 2024 for Chicago, 2025 for the north suburbs, so the 2022 case's after window undercounts the comparison side and would flatter the reform; lots carry `apt_sheet_last` for a check (e.g. north-suburb-only comparison). Evanston cut TOD parking in September 2017 (parking only; flag). No bus-corridor version (no official list).
- **Stage 1 fast lot model, round 1** (lot traits only; gradient boosting; each city hidden in turn; before Chicago and before all traits were joined): median absolute error per 100 acres a year, model / others' average / zero: 0–¼ mile 21.3 / 26.2 / 28.1; ¼–½ 10.5 / 9.6 / 11.5; ½–1 5.5 / 2.9 / 2.9. The model beats both simple rules only within ¼ mile so far. Runtime 10 minutes. Next rounds: add place traits, then tract traits (stage order), with Chicago in.
- **Stage 1, rounds 2–4 (all 16 places with reform stops, 1.79 million sampled lot rows; each place hidden in turn)**: median absolute error per 100 lot acres a year within ¼ mile, model / others' average / zero: lot traits only 13.3 / 25.5 / 22.8; + place traits (distance, EPA, jobs, historic) 18.2; + 78 tract traits 20.1. Per the staged plan, place and tract traits do not earn their place (they make hidden-place predictions worse); lot traits stay. ¼–½ mile: 9.1 / 9.3 / 10.3 (no real skill); ½–1 mile: 4.8 / 3.0 / 2.6 (worse than zero). The model's predictions are compressed (−1 to 28 within ¼ mile) while measured effects range −33 to +129; the two largest measured effects (Denver 128.6, Seattle Mount Baker 121.5 with 3% coverage) need a check of their big projects before the next round.
- **Wisconsin lot table** (`scripts/build_tod_station_wisconsin.py`, local output wi_lots_station.parquet): 39,039 Milwaukee and Madison lots within 1 mile of 84 rail/rapid stations (266 stops merged); homes built 2020–24 from parcel year built as the before rate; law start 2025; coverage from the older Wisconsin lot table's upzoned flag (68–88% by band; Madison ½–1 mile 51%). Homes within ½ mile: 80,930 in the two cities of 89,528 statewide (9.6% elsewhere: Kenosha 3,776, Wauwatosa 3,317, Shorewood Hills 957, others small) — the statewide figure scales the two-city estimate. Off-range flags vs training: Milwaukee building age (median 103 years vs 37–96; 13.5% of lots beyond the training range), tract building age, lower rents and owner share, flat job growth (2019→22 spans COVID).
