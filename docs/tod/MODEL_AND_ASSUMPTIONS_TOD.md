# Transit-oriented density (TOD): model and assumptions

Master copy for the TOD section of [MODEL_AND_ASSUMPTIONS.md](../MODEL_AND_ASSUMPTIONS.md). Last updated 2026-11-03 (AQ-075, upper back to the average scaled to 15%, the 2×2 readings as what-ifs; AQ-072, lines from the causal framework; AQ-071, option D; earlier AQ-068 to AQ-070, AQ-053, AQ-054, AQ-057). Option D plan and log: [OPTION_D_PLAN.md](OPTION_D_PLAN.md); causal framework: [CAUSAL_FRAMEWORK_PLAN.md](CAUSAL_FRAMEWORK_PLAN.md). Decisions: AQ-044 to AQ-051 in [ASSUMPTIONS_AND_QUESTIONS.md](../ASSUMPTIONS_AND_QUESTIONS.md). Detail: [GATE3_PACKET.md](GATE3_PACKET.md), [MODEL.md](MODEL.md).

## 1. Purpose and scope

The tool estimates how many more homes would be permitted in Wisconsin over 2027–2031 if the state passed a transit-oriented density law. Since AQ-071 (owner, 2026-11-02) the modelled law is **option D, the transit district mandate**: every Wisconsin city with qualifying rail or rapid stops zones a by-right multifamily district (at least 15 homes per acre) covering 15% of the lot acres within ¼ mile of those stops. It replaces the earlier benchmark law (SB 79-style heights and floor area on about 71% of the lots within ¼ mile), whose lines are kept as what-ifs.

- **Outcome:** housing units in issued building permits, compared with current law in the same places. Not completed homes.
- **Law start:** a stylized 1 January 2027.
- **Scope of the reform:** the reform is modelled on its own. Parking minimums are not changed; they belong to the parking scenario. A separate combined view shows the two together.
- **Where it applies:** the district is within ¼ mile of streetcar and rapid bus stations (6,394 lot acres: Madison 3,647, Milwaukee 1,564, Wauwatosa 614, Kenosha 265, Shorewood Hills 161, Sun Prairie 93, Burke 47, Blooming Grove 2). Results are counted, against current law, in the station areas: within ½ mile of streetcar and rapid bus stations, and within ¼ mile of bus routes with service every 15 minutes or better at the morning peak.
  - That covers 313,564 of Wisconsin's 2,727,726 homes in the 2020 census (11.5%).
  - 98.7% of those homes are in Milwaukee County and Dane County.

**Shared reporting units (AQ-054).** For comparison across reforms, the TOD scenarios are restated against the statewide all-housing baseline and on Wisconsin's ACS 2020–2024 home count. These figures are not stacked or added to the other reforms.

| Scenario | Extra homes permitted a year, statewide | As a share of the statewide all-housing baseline (124,000 homes over 2027–2031) | As a share of Wisconsin's 2,778,572 homes (ACS 2020–2024) |
| --- | --- | --- | --- |
| Lower: the rezoned parcels' own gain only (3,958 over five years) | about 792 | 3.2% | 0.14% |
| Central: the average district place, across about 12% of lots within ¼ mile of transit (10,028) | about 2,006 | 8.1% | 0.36% |
| Upper: the average district place, scaled up to 15% of lots within ¼ mile of transit (12,521) | about 2,504 | 10.1% | 0.45% |

The station-area shares (1.3%, 3.2% and 4.0% of the 313,564 homes near stops) stay on the 2020 census count, because the station areas are built from census blocks.

**No median line for TOD.** A median line of real cases is shown only when a reform has at least 4 comparable cases. TOD shows none: its central is already the average of the 11 district places.

## 2. Core assumptions and their rationale

- **What counts as a "major transit stop" (AQ-044, AQ-047).** The main definition is rail and rapid bus (the Hop and Kenosha streetcars, Milwaukee's CONNECT 1, Madison's Rapid Route A) plus any stop on a route running 4 or more trips an hour in one direction at 7:00–8:59 on weekdays.
  - The 15-minute test matches California, Colorado and most state laws, and every Wisconsin agency's own schedule can measure it.
  - Amtrak stations are excluded: they run far fewer than the 48 trains a day that California's SB 79 requires for commuter rail.
  - The distances (½ mile for rail and rapid bus, ¼ mile for bus) follow the state laws reviewed. No study measures how the building response falls off with distance.
- **The law (AQ-071; replaces AQ-047, AQ-049).** Option D: every city with rail or rapid stops (The Hop, the Kenosha streetcar, CONNECT 1, Rapid Route A) zones a by-right multifamily district, at least 15 homes per acre, on **15% of the lot acres within ¼ mile** of those stops. No affordability mandate; parking unchanged. The 15% follows what the training places used (owner: "base the district size on the benchmark policy which is based on what we have good data for ... 15% of lot acres within .25 miles of the stops is a good start", 2026-11-02). No site is picked: the district is spread at random over the ¼-mile land (owner: "I'd rather not pick specific sites but instead just show density in a radius of the TOD. But random is fine too."), so each lot there is in the district with probability 0.15. Land beyond ¼ mile counts zero. The former law (65 feet, FAR 3.0 and 100 homes per acre within ¼ mile of a station; 55 feet beyond) is kept only for the what-ifs.
- **Evidence (AQ-071).** 11 US places whose reform covered under 30% of the lots within ¼ mile (Philadelphia, Chicago 2015, Seattle Mount Baker, Denver, Seattle Othello, New York, Salt Lake City, Saint Paul, Charlotte, Portland 2020, Austin), each measured as reform stops against similar comparison stops, before and after. Their districts averaged 12% of the ¼-mile lots. By the rule fixed before results, the central is the best model only if it beats the other places' average on hidden places; no model did (median error within ¼ mile: average 19.3, zero 28.1, best model 22.3; extra homes per 100 lot acres a year).
- **Size of the effect (AQ-071).** Extra homes near stops over 2027–2031, Wisconsin (`reference/tod_optiond_line.csv`; ranges = each place left out in turn):
  - **Lower: the rezoned parcels' own gain only, 3,958 (90% range 2,280 to 5,791; leave one place out 1,600 to 4,873)** (AQ-072). The edge test: lots just inside a district boundary against lots just outside (91 m), after minus before, in the 5 places whose two sides were alike before the reform (Philadelphia, Austin, Chicago 2015, Denver, Saint Paul), pooled 88.2 extra homes per 100 lot acres a year of district land × 15% × 4,874 lot acres ÷ 100 × 5 years × 1.227. It counts only the rezoned lots' own gain, so it is a floor; fake boundaries show about zero, and broad upzonings show no jump ([CAUSAL_FRAMEWORK_PLAN.md](CAUSAL_FRAMEWORK_PLAN.md), Test 2 and its expansion).
  - **Central: the average district place, across about 12% of lots within ¼ mile of transit, 10,028 (range 7,580 to 12,010).** The places' mean effect within ¼ mile, 33.54 extra homes per 100 lot acres a year × 4,874 lot acres within ¼ mile of rail and rapid stops (Milwaukee and Madison) × 5 years × 1.227 for the rest of the state.
  - **Statewide scale (owner 2026-11-02 14:54, "You can switch.").** All Wisconsin lot acres within ¼ mile of rail and rapid stops ÷ those in the cities of Milwaukee and Madison: 6,394 ÷ 5,212 = 1.227, computed from `reference/tod_station_areas.csv` (the same land the placement uses). It replaced homes within ½ mile, 89,528 ÷ 80,930 = 1.106.
  - **Upper: the average district place, scaled up to 15% of lots within ¼ mile of transit, 12,521 (leave one place out 9,089 to 16,771)** (AQ-075; the option D upper of AQ-071). The 11 places' pooled effect per share of land zoned × 15%: 41.9 extra homes per 100 lot acres a year within ¼ mile, × the same acres, years and scale (`reference/tod_optiond_line.csv` row `optiond_average_scaled_15`, copied to `reference/tod_causal_lines.csv` row `upper_average_scaled_15`). Caveat: among the 11 places the effect fell as the district share grew (rank correlation −0.32; a straight line at 15% gives 8,143), so scaling up leans on the smallest districts. Owner: "good catch - yes to all three", 2026-11-03 11:52.
  - **The 2×2 readings, now what-ifs (AQ-075).** Upzoning with new transit lines (T2b; the upper under AQ-072): near lines 0–3 years old at the reform, rezoned stops gained 44.99 extra homes per 100 lot acres a year more than new-line stops not rezoned: 13,451 (leave one place out 10,431 to 15,049). Its before-reform check (T2b-PT) failed: rezoned stops on new lines were already gaining 30.2 per 100 lot acres a year before any reform (90% 12.0 to 50.7). Upzoning with new transit lines, minus the growth already under way before the reforms (fake-years check): 18.8 per 100 lot acres a year, 5,624 homes (paired place bootstrap 90% −2,776 to 13,666; leave one place out 2,340 to 9,684), read from `reference/tod_causal_line_age_pretrend.csv`.
  - **Beside the central:** line-age matched 6,932 (90% 2,717 to 14,147); Massachusetts MBTA Communities, first year: no rise; Los Angeles TOC tier cutoffs: a bigger bonus did not add building. Transit alone (new lines, no rezoning): +17.8 per 100 lot acres a year, about 5,315 homes, which belongs in the baseline, not the law.
  - Former option D lower (AQ-071), now a what-if: 824 (best lot model, −90 to 1,006). The option D upper (12,521) is the upper line again (AQ-075).
  - Former lines (broader law), now what-ifs: central 13,229 as shown then, 13,686 recomputed with the corrected lot data (average reform city at 71% coverage, AQ-070); strong 17,148 (Auckland); little 43 as shown then, −70 recomputed (station-area model, AQ-069).
  - **Labels (owner 2026-11-02 22:29):** "approve the TOD lines. I think Central should say (average, across 12% of lots within .25 miles of transit) and Upper should say (scaled to 15% of lots within .25 miles of transit)". The tool now reads "Central: the average district place, across about 12% of lots within ¼ mile of transit" and "Upper: the average district place, scaled up to 15% of lots within ¼ mile of transit".
  - **Data fixes behind these lines (2026-11-02).** Lot land counted once; missing lot sizes filled from each city's own Census land share; New York hotel, condo-hotel, care-home and superseded-job rule rows and Philadelphia double counts removed (3,929 rule rows plus 45 hand rows); Seattle corrections. Before the fixes the lines were 499 / 9,822 / 12,264.
- **Where homes land (AQ-071).** Each place's share of the statewide total = its share of the lot acres within ¼ mile of rail and rapid stops (central: Madison 5,721, Milwaukee 2,453, Wauwatosa 964, Kenosha 416, Shorewood Hills 252, Sun Prairie 145, Burke 73, Blooming Grove 4). The former placement by the old law's added floor area (AQ-051) is a what-if.
- **No floor at zero.** Places already at or above the law get no addition, but a measured line may be below zero where the evidence says so (owner rule against evidence-free floors).
- **Timing.**
  - All three lines follow the yearly build-up measured after 17 New York City rezonings in 2003–2013.
  - The former strong line (Auckland) keeps Auckland's own yearly pattern in its what-if.
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
5. **Sizing.** Since AQ-071 the statewide total comes from the 11 district places' measured station-area effects (section 2), and homes are placed across places in proportion to lot acres within ¼ mile of rail and rapid stops. The per-acre response from the cases above no longer sizes or places the line.
6. **Aggregation.** Station areas add up to municipalities, counties, Assembly and Senate districts, and the state.

## 5. Limitations and known edge cases

- **No Wisconsin test of the adopted sizing.** The Madison test checked the per-acre method, which no longer sizes or places homes.
- **Chosen land versus a mandate.** The 11 places chose their district land, often land builders already wanted (old industrial land, low-value lots). A state mandate makes every city act, on land it may pick less well, so it may do less; the random placement does not capture this. Near Milwaukee's new streetcar, building rose by a similar amount with no rezoning, so part of the measured gain may come from new transit or booming neighbourhoods.
- **District size.** The places averaged 12% districts; the law asks for 15%. The upper line (12,521) assumes the effect grows in proportion; the central does not scale it.
- **No model beat the average.** Lot, stop-level, place, tract and affordability-rule models were all tried (OPTION_D_PLAN.md log); none beat the plain average on hidden places, so the lines carry no Wisconsin-specific trait adjustment.
- **Districts, not citywide upzoning.** For the 5 broad upzonings left out of training (BelRed, Honolulu, Los Angeles TOC, San Diego, Chicago 2022; measured −13.3 to +29.4 extra homes per 100 lot acres a year within ¼ mile), the average rule predicts +33.5 for each (median miss 42.9), the scaled rule 139 to 279 (median miss 240), and zero misses by a median 10.6 (`reference/tod_optiond_broad_check.csv`). The lines describe districts, not citywide upzoning.
- **Record years.** The lower line takes the Madison metro's apartment permitting above its own record year in 2030; the central and the upper in 2029–2030 (Madison) and 2030 (Milwaukee). No line passes the highest peer-metro year. The compare screen says so beside the lines.
- **Baseline and new-line growth.** The near-stop baseline (14,654) spreads each place's 2023–2025 permits by its share of homes near stops; it includes years after The Hop and most of CONNECT 1's first year but not Rapid Route A, and does not concentrate growth near the new stops. Its ¼-mile part is about 4,250 over five years, against about 5,315 for transit-alone growth; in Milwaukee recent building within ¼ mile (about 200 homes a year in new 5+ unit buildings, 2018–2025) is about twice the baseline's ¼-mile share (about 94 a year). So current law near stops may be understated; the law's lines exclude transit-alone growth (AQ-072).
- **Madison's 2023 overlay** already allows more along much of Rapid Route A; the model does not credit it, so Madison's share may be overstated.
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
  - Lower at the ends of its range: 2,280 to 5,791 (90%). Central: 7,580 to 12,010 (each place left out). Upper: 9,089 to 16,771 (each place left out).
  - Upzoning with new transit lines (the 2×2): 13,451; minus the growth already under way before the reforms: 5,624 (AQ-075). Former option D lower 824 (best lot model). Line-age matched: 6,932.
  - District of 10%: 8,347; of 25%: 20,868 (the upper line's method). Straight line through the places at 15%: 8,143.
  - Former lines for the broader law, recomputed with the corrected lot data: central 13,686 (shown as 13,229, AQ-070), strong 17,148 (Auckland, its own yearly pattern), little −70 (shown as 43, AQ-069). Earlier: Los Angeles TOC 171, drift rule 1,196 (AQ-068), Stacy et al. 2,509.
  - Final year smoothed: same totals, with 2,248 homes in 2031 instead of 664 (central).
- **Where homes land (totals unchanged):**
  - Placed by the broader law's added floor area (AQ-051): Milwaukee metro 6,542 and Madison metro 3,305 (main: 3,417 and 6,195).
  - Only Milwaukee and Madison cities get homes: Milwaukee metro 3,010 and Madison metro 7,018.
  - Stop definitions change only current law near stops: rail and rapid only 6,206; 20-minute buses 15,984; all 15-minute stops within ½ mile 18,676 (main 14,654). The law's addition is the same.
- **Baseline only:** 8,495 to 22,161, or 11,503 with Milwaukee's apartments as the Census published them. The addition is unchanged.

## 7. Intended users and appropriate use cases

- **Intended users:** Wisconsin legislators and staff, and local officials in Milwaukee, Madison and other cities with frequent transit.
- **Good uses:**
  - comparing the likely size of a TOD law with current law;
  - seeing where the extra homes would go;
  - understanding the range of the evidence (the upper line is about 3.2 times the lower one);
  - comparing TOD with ADU and parking reform.
- **Not appropriate for:**
  - parcel-level forecasts;
  - predicting a specific project;
  - setting housing targets;
  - forecasting effects after 2031;
  - judging rents or displacement.

Read the scenarios as different readings of the same 11 district places (best model, plain average, average scaled to 15%), not as a statistical confidence interval.
