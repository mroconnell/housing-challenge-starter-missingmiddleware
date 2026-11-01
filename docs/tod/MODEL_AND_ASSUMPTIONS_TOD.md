# Transit-oriented density (TOD): model and assumptions

Master copy for the TOD section of [MODEL_AND_ASSUMPTIONS.md](../MODEL_AND_ASSUMPTIONS.md). Last updated 2026-11-01 (AQ-068, AQ-069, AQ-070; earlier AQ-053, AQ-054, AQ-057). Decisions: AQ-044 to AQ-051 in [ASSUMPTIONS_AND_QUESTIONS.md](../ASSUMPTIONS_AND_QUESTIONS.md). Detail: [GATE3_PACKET.md](GATE3_PACKET.md), [MODEL.md](MODEL.md).

## 1. Purpose and scope

The tool estimates how many more homes would be permitted in Wisconsin over 2027–2031 if the state passed the challenge's transit-oriented density benchmark: higher allowed heights and floor area near major transit stops.

- **Outcome:** housing units in issued building permits, compared with current law in the same places. Not completed homes.
- **Law start:** a stylized 1 January 2027.
- **Scope of the reform:** the reform is modelled on its own. Parking minimums are not changed; they belong to the parking scenario. A separate combined view shows the two together.
- **Where it applies:** within ½ mile of streetcar and rapid bus stations, and within ¼ mile of bus routes with service every 15 minutes or better at the morning peak.
  - That covers 313,564 of Wisconsin's 2,727,726 homes in the 2020 census (11.5%).
  - 98.7% of those homes are in Milwaukee County and Dane County.

**Shared reporting units (AQ-054).** For comparison across reforms, the TOD scenarios are restated against the statewide all-housing baseline and on Wisconsin's ACS 2020–2024 home count. These figures are not stacked or added to the other reforms.

| Scenario | Extra homes permitted a year, statewide | As a share of the statewide all-housing baseline (122,619 homes over 2027–2031) | As a share of Wisconsin's 2,778,572 homes (ACS 2020–2024) |
| --- | --- | --- | --- |
| Little or no response (43 over five years) | about 9 | 0.035% | 0.002% |
| Central: average reform city (13,229) | about 2,646 | 10.8% | 0.48% |
| Strong: Auckland (17,148) | about 3,430 | 14.0% | 0.62% |

The station-area shares in section 2 (0.014%, 4.2% and 5.5% of the 313,564 homes near stops) stay on the 2020 census count, because the station areas are built from census blocks.

**No median line for TOD.** A median line of real cases is shown only when a reform has at least 4 comparable cases. TOD's lines rest on different kinds of evidence (our 16-place station-area data and one whole-city study), so it has none.

## 2. Core assumptions and their rationale

- **What counts as a "major transit stop" (AQ-044, AQ-047).** The main definition is rail and rapid bus (the Hop and Kenosha streetcars, Milwaukee's CONNECT 1, Madison's Rapid Route A) plus any stop on a route running 4 or more trips an hour in one direction at 7:00–8:59 on weekdays.
  - The 15-minute test matches California, Colorado and most state laws, and every Wisconsin agency's own schedule can measure it.
  - Amtrak stations are excluded: they run far fewer than the 48 trains a day that California's SB 79 requires for commuter rail.
  - The distances (½ mile for rail and rapid bus, ¼ mile for bus) follow the state laws reviewed. No study measures how the building response falls off with distance.
- **The law (AQ-047, AQ-049).** We use California SB 79's minimums for light rail and dedicated-lane bus:
  - 65 feet, floor area ratio (FAR) 3.0 and 100 homes per acre within ¼ mile of a station;
  - 55 feet, FAR 2.5 and 80 homes per acre from ¼ to ½ mile;
  - the same 55-foot standard within ¼ mile of 15-minute buses. This last one is our extension: no law sets a floor for ordinary buses.

  The law is by right, with no opt-outs and no affordability mandate. We looked for a better design in the evidence, but no measured design outperformed the others once held-out cases were checked.
- **Size of the effect (AQ-068 to AQ-070; first set by AQ-050).** Extra homes near stops over 2027–2031, Wisconsin:
  - **Little or no response: 43 (range −161 to 343)** (AQ-069). Our station-area lot model: building near 16 US places' reform stations compared with similar stations without reform, every lot within a mile, tested by hiding one place at a time. It beat simple rules only within ¼ mile (beyond that it counts zero). Broad upzonings near every station (Los Angeles TOC, San Diego, Chicago 2022, Honolulu) gained about nothing so far; Wisconsin's law is broad (71% of lots within ¼ mile), so the model puts it with them. What it rests on: those four programs, each with a weakness (Los Angeles not a blind test; San Diego county completion dates and 3 after-years; Chicago 2022 3 after-years and incomplete comparison records; Honolulu two quiet stations). Shown beside it: Los Angeles TOC (171, the former little line) and the model with a strings-attached trait (214).
  - **Central: if Wisconsin did as well as the average reform city, 13,229 (range 9,147–17,108)** (AQ-070). The same data's pre-registered scaled version: one pooled ratio within ¼ mile (68.9 extra homes per 100 lot acres a year at full coverage, each place counted once) × Wisconsin's 71% coverage × 4,874 lot acres × 5 years × 1.106 for the rest of the state. Weighted by each place's homes it is about 11,706. The measured effect fell, not rose, with coverage (rank correlation −0.66): a line through the places at 71% gives about −570, the five broad places alone about −460, the unscaled average about 5,950; near Milwaukee's new streetcar building rose by a similar amount with no rezoning. So the central is closer to an upper estimate, and its range shows only the effect of leaving out one place at a time. Shown beside it: the lot-model drift rule (1,196, the former central, AQ-068), the pre-registered average change (808) and Stacy et al. 2023 (2,509).
  - **Strong response: like Auckland's 2016 upzoning, 17,148** (5.5% of homes near stops): 21,808 extra homes over 2016–2021, or 4.11% of the city's homes, divided by the 75.2% of residential land it covered.
- **No floor at zero.** Places already at or above the law get no addition, but a measured line may be below zero where the evidence says so (the little line's low end, −161; owner rule against evidence-free floors).
- **Timing.**
  - Little and central follow the yearly build-up measured after 17 New York City rezonings in 2003–2013.
  - Strong follows Auckland's own yearly pattern.
  - The build-up was fixed before the results were seen, and is not smoothed.

## 3. Data sources and cleaning steps

All data are fetched by script, with the source, date, size and checksum recorded. Raw files are not committed ([DATA_PROVENANCE.md](../DATA_PROVENANCE.md)).

- **Transit stops and routes:** the U.S. DOT National Transit Map (BTS, compiled 23 September 2026; 27 Wisconsin agencies, 13,052 stops).
  - Route frequency comes from 16 agencies' own GTFS schedules. Milwaukee's official file timed out, so a May 2025 copy from the Mobility Database is used.
  - Madison's frequency comes from its route descriptions in the National Transit Map. Madison Metro's own file is not used while its licence is an open question for office hours (AQ-045).
  - Amtrak stations come from the BTS Amtrak Stations layer.
- **Homes near stops:** 2020 census blocks (housing units), with a block counted when its internal point lies within the distance.
- **Land and zoning:**
  - Wisconsin statewide parcels (V12) for the six counties with qualifying stops.
  - Milwaukee zoning: 52 districts, including the 2025 RT5 district.
  - Madison zoning: 44 districts, plus the 2023 TOD overlay.
  - Existing homes: Milwaukee's property file and Madison's assessor data.
  - Suburbs' zoning is not coded. Their room to build is estimated from existing density, then scaled by 0.719, the ratio of coded to estimated capacity measured in Milwaukee and Madison.
- **Floor area per home:** measured from permits for new buildings of 5 or more homes, 2018–2025:
  - Madison: 1,512 sq ft;
  - Milwaukee: 1,192 sq ft;
  - pooled: 1,467 sq ft.
- **Baseline:** the shared all-housing baseline (Census Building Permits Survey, with Milwaukee's apartments taken from the city's property file, AQ-048). Each place's baseline is split by its share of homes near stops.
- **Comparison cases:** city permit files with unit counts and dates, matched to parcels and zoning before and after the reform.
  - Cases: Charlotte, New York (Park Slope, Downtown Brooklyn and 17 rezonings pooled), Philadelphia, Chicago, Saint Paul and Madison.
  - Cleaning: duplicate and staged permits are removed, and the per-year counts are checked against the Census survey.
  - Privacy: no parcel or permit numbers are committed.

## 4. Methodological approach

1. **Policy research.** Ten state laws were classified against the benchmark from their statute text. None fully meets it; California SB 79, Washington HB 1491, British Columbia Bill 47 and Massachusetts's MBTA Communities law come nearest. 58 city upzonings were inventoried.
2. **Comparison cases, against a plan written beforehand** ([CASE_ANALYSIS_PLAN.md](CASE_ANALYSIS_PLAN.md)).
   - Method: difference-in-differences of homes permitted per eligible acre per year, comparing lots whose allowed density rose with lots whose zoning did not change.
   - Results, in extra homes per acre per year for each 1.0 of added floor area ratio:
     - Park Slope 2.93;
     - Downtown Brooklyn 2.20;
     - the New York pooled set 0.67;
     - Chicago, held out, 0.24.
   - Charlotte and Philadelphia are small or have no floor-area measure.
3. **A held-out Wisconsin test** ([MADISON_TEST_PREREG.md](MADISON_TEST_PREREG.md)). The per-acre method predicted, in advance, that Madison's 2023 overlay would add 0.25 homes per acre per year. The measured effect was 0.08 (90% interval −0.17 to +0.31): it passed, but only weakly.
4. **A scale check.** Spread over all land near Wisconsin stops, per-acre rates gave 14,212 to 151,973 extra homes. That would take Madison's apartment permitting beyond its own record. A block-level gain partly moves building from neighbouring blocks.
5. **Sizing.** The adopted method (AQ-050) takes the statewide total from whole-city net effects (section 2). The per-acre response is used only to place homes across station areas, in proportion to eligible acres times added floor area.
6. **Aggregation.** Station areas add up to municipalities, counties, Assembly and Senate districts, and the state.

## 5. Limitations and known edge cases

- **No Wisconsin test of the adopted sizing.** The Madison test checked the per-acre method, which now only places homes.
- **The central line is closer to an upper estimate.** It averages 16 places, most of which upzoned a small area near their stations; the measured effect fell, not rose, with coverage, and the broad programs most like Wisconsin's law gained about nothing so far (the little line). Near Milwaukee's new streetcar, building rose by a similar amount with no rezoning, so part of the measured gain may come from new transit or booming neighborhoods rather than zoning ([STATION_AREA_PLAN.md](STATION_AREA_PLAN.md)).
- **Former typical line (Stacy et al. 2023, now a what-if).** Only 28 of Stacy et al.'s 96 loosening reforms changed floor area, density or height; a 2025–2026 AEI Housing Center review found most of its 180 reforms minor, misplaced or misclassified ([research/STACY_AEI_REVIEW.md](research/STACY_AEI_REVIEW.md), AQ-059).
- **Why places differ.** A pre-registered effect-heterogeneity analysis tested 12 local traits (such as home values, incomes, rents, lot sizes, existing density and distance to downtown) on rezonings and station areas in six cities, using leave-one-city-out cross-validation. Eight methods were tried: weighted regression, LASSO, a regression tree, a random forest, gradient boosting, a causal forest, nearest neighbours and a multilevel model. All 66 pairs of traits were also tested. None predicted where upzoning added more homes better than a plain average, so the scenarios stay wide ([TRAITS_RESULTS.md](TRAITS_RESULTS.md)). A second test entered 91 census variables (housing, incomes, commuting, car ownership and more) for 8 cities; again nothing beat the plain average ([ALLVARS_RESULTS.md](ALLVARS_RESULTS.md)).
- **Checks against our own cities.** In 8 US cities that upzoned land near transit, the extra homes permitted over five years, net of building moved within the city, came to 0.04% (Los Angeles) to 1.24% (Madison) of the city's homes. Saint Paul, with one year of data before its reform, was −0.12%. In no city did building fall next to the upzoned area ([NET_EFFECT_RESULTS.md](NET_EFFECT_RESULTS.md)). A comparison of six of these cities with 10 matched US cities that made no such reform agreed in 5 of 6. But it can only detect changes of about 4% to 5% of a city's homes over five years, so it cannot narrow the range ([CONTROL_CITIES_RESULTS.md](CONTROL_CITIES_RESULTS.md)).
- **TOD alone versus TOD with parking reform.** The cases cannot separate the two.
- **Concentration.** Almost all extra homes land in Milwaukee County and Dane County.
- **Edge cases:**
  - Places with few homes but eligible vacant or commercial land, such as River Hills, get additions.
  - Wauwatosa's Census permit counts are low, which may be an under-count like Milwaukee's.
- **Data gaps:**
  - Green Bay has no current schedule, so none of its routes counts as frequent.
  - Superior and Metra's Kenosha station are missing.
  - Milwaukee's schedule is from 2025.
- **Not modelled:** rents, displacement, transit ridership and completions.

## 6. Sensitivity notes (extra homes 2027–2031, central unless stated)

- **The law's addition:**
  - Little or no response at the ends of its range: −161 to 343. Former little line (Los Angeles TOC): 171. With the strings-attached trait: 214.
  - Central at the ends of its range (each of 16 places left out): 9,147 to 17,108. Weighted by each place's homes: about 11,706. Unscaled pre-registered average: about 5,950.
  - Former central line (lot-model drift rule, AQ-068): 1,196. Pre-registered average change: 808. Stacy et al. 2023: 2,509.
  - Strong as published (no coverage adjustment): 12,895.
  - Final year smoothed: same totals, with 2,965 homes in 2031 instead of 876.
- **Where homes land:**
  - Rail and rapid stops only: 3,777.
  - 20-minute service: 14,834.
  - All 15-minute stops within ½ mile: 17,015.
  - Placement without suburbs: Milwaukee metro 6,708 and Madison metro 6,521 (main: 8,631 and 4,361).
- **Baseline only:** 8,495 to 22,161, or 11,503 with Milwaukee's apartments as the Census published them. The addition is unchanged.

## 7. Intended users and appropriate use cases

- **Intended users:** Wisconsin legislators and staff, and local officials in Milwaukee, Madison and other cities with frequent transit.
- **Good uses:**
  - comparing the likely size of a TOD law with current law;
  - seeing where the extra homes would go;
  - understanding why the evidence disagrees (a hundredfold spread between scenarios);
  - comparing TOD with ADU and parking reform.
- **Not appropriate for:**
  - parcel-level forecasts;
  - predicting a specific project;
  - setting housing targets;
  - forecasting effects after 2031;
  - judging rents or displacement.

Read the scenarios as different bodies of evidence, not as a statistical confidence interval.
