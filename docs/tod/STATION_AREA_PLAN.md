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
