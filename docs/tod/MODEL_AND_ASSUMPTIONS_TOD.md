# Transit-oriented density (TOD): model and assumptions

Master copy for the TOD section of [MODEL_AND_ASSUMPTIONS.md](../MODEL_AND_ASSUMPTIONS.md). Last updated 2026-10-27 (AQ-053, AQ-054). Decisions: AQ-044 to AQ-051 in [ASSUMPTIONS_AND_QUESTIONS.md](../ASSUMPTIONS_AND_QUESTIONS.md). Detail: [GATE3_PACKET.md](GATE3_PACKET.md), [MODEL.md](MODEL.md).

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
| Little | about 34 | 0.14% | 0.006% |
| Typical | about 502 | 2.0% | 0.09% |
| Strong | about 3,430 | 14.0% | 0.62% |

The station-area share in section 2 (0.055%, 0.8% or 5.5% of the 313,564 homes near stops) stays on the 2020 census count, because the station areas are built from census blocks.

**No median line for TOD.** A median line of real cases is shown only when a reform has at least 4 comparable cases. TOD's scenarios rest on 3 whole-city studies, so it has none.

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
- **Size of the effect (AQ-050).** Each scenario is a share of the homes in the station areas, taken from a study of the whole-city net effect after upzoning:
  - Little response, like Los Angeles's Transit Oriented Communities program: 0.055% over five years.
  - Typical response, like the average loosening reform across 1,136 US cities (Stacy et al. 2023): 0.8%.
  - Strong response, like Auckland's 2016 upzoning: 5.5%.

  The Los Angeles and Auckland figures are divided by the share of each city the reform covered (61% of homes and 75.2% of residential land), so they apply per upzoned home.
- **Never subtracts.** Places already at or above the law get no addition. No addition is negative.
- **Timing.**
  - Little and typical follow the yearly build-up measured after 17 New York City rezonings in 2003–2013.
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
- **The typical scenario rests on a general study.** Only 28 of Stacy et al.'s 96 loosening reforms changed floor area, density or height. It is measured 3 or more years after reform, but is placed here inside five years.
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

## 6. Sensitivity notes (extra homes 2027–2031, typical unless stated)

- **The law's addition:**
  - Stacy et al.'s 95% interval: 665 to 4,352.
  - Without the coverage adjustment: little 105, strong 12,895.
  - Final year smoothed: same totals, with 562 homes in 2031 instead of 166.
  - Per-acre sizing: 14,212, 39,767 and 151,973. These fail the scale check.
  - Per-acre sizing at the Madison and Chicago rate (0.23): 13,477. Capped at the 95th percentile of comparable metro-years (9.06 apartment permits per 1,000 homes), it falls to 6,834.
- **Where homes land:**
  - Rail and rapid stops only: 716.
  - 20-minute service: 2,813.
  - All 15-minute stops within ½ mile: 3,226.
  - Placement without suburbs: Milwaukee metro 1,272 and Madison metro 1,237 (main: 1,637 and 827).
- **Baseline only:** 8,386 to 21,874, or 11,875 with Milwaukee's apartments as the Census published them. The addition is unchanged.

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
