# Model & Assumptions: parking requirement reduction

Written 2026-10-27 by the parking conductor. Status: the parking section for the project's [Model & Assumptions Overview](../MODEL_AND_ASSUMPTIONS.md), which is a shared file. It follows that file's headings, so the coordinator can merge it there.

## Purpose and scope

**The question.** If Wisconsin removed minimum parking requirements for all housing from 1 January 2027, how many more homes would be permitted over 2027–2031 than under current law, how sure are we, and where would they be?

**The outcome.** New housing units authorized by building permits, counted at permit issuance, in all building sizes. The unit is the same as in the ADU scenario.

**The law modelled.** No minimum off-street parking may be required for any housing, statewide. This matches the challenge benchmark ("Reduce or eliminate minimum parking requirements"), read as "eliminate". North Carolina's HB 162 (signed 6 July 2026, in effect 1 January 2027) is the closest real law. It has no permit data yet.

## Core assumptions and their rationale

1. **Developer-provided parking without mandates (the benchmark's required assumption).** We assume developers keep building the parking that renters, buyers and lenders want. A repeal adds homes only where a minimum forced more parking than the market wanted. The evidence:
   - **Buffalo**, after its 2017 citywide repeal (Hess, D. B., and Rehler, J. (2021), "Minus Minimums: Development Response to the Removal of Minimum Parking Requirements in Buffalo (NY)", *Journal of the American Planning Association* 87(3), 396–408, doi:10.1080/01944363.2020.1864225; read in full): 36 major projects provided 79% of the spaces the old minimums required. Mixed-use projects provided 47%. Stand-alone apartment buildings provided 117%, or 1.34 spaces per unit against a minimum of 1.
   - **Seattle, Minneapolis and Champaign:** similar reductions in parking built. These are source leads, not yet checked against the full papers.

   The scenario does not set a parking ratio itself. It uses the permit outcomes of places that repealed, so whatever parking their developers chose is already built into the result. As an illustration, for Wisconsin we assume developers would build about four-fifths of the spaces today's minimums require, and about all of them for stand-alone apartment buildings, as in Buffalo (79% and 117%). The permit numbers do not depend on this illustration.
2. **Evidence from cities and villages, not states.** No state has removed minimums for all housing long enough to measure. The response comes from 76 US places that did, between 2016 and 2024 (expanded from a first set of 24, then 71; on 2026-10-28 three dropped places were rescued, South Bend, Gastonia and Avondale Estates, and two more were found, Maumee and Saranac Lake; [EXPANDED_RESULTS.md](EXPANDED_RESULTS.md), [SALVAGE_RESULTS.md](SALVAGE_RESULTS.md), [PARTIAL_REFORMS_RESULTS.md](PARTIAL_REFORMS_RESULTS.md)):
   - each checked against its ordinance;
   - each compared with similar places in its own state (falling back to its Census division when the state has too few) that kept their minimums.
   A second, independent check agrees. California's AB 2097 removed minimums within ½ mile of major transit stops in 2023. Near transit, permits changed by +0.13 permits per 1,000 existing homes per year against areas ½ to 1½ miles away (90% interval −1.84 to +1.73, 185 jurisdictions); see [COMPARISON_RESULTS.md](COMPARISON_RESULTS.md).
3. **Central case, "No measurable change" (0 added).** In the one to three years after repeal, the repeal places' permit rate changed by −1.14 permits per 1,000 existing homes per year compared with similar places. The 90% range (5th to 95th percentile of 2,000 resamples) is −3.47 to +1.43 permits per 1,000 existing homes per year. A repeal is not modelled as reducing permits, so the central case is 0.
4. **Upper case, "High end of the evidence".** +0.95 permits per 1,000 existing homes per year (owner decision, 2026-10-27, option B; 76 places, 2026-10-28). It comes from the control-city (placebo) test: 20,000 placebo studies, drawn from 4,626 cities that never repealed and given the real places' repeal years, have averages whose middle 90% spans 4.4 permits per 1,000 existing homes per year (−0.79 to +3.59). Centred on the real average of −1.14, that spread runs from −3.44 to +0.95. Earlier runs gave +0.91 (20 cities per place, 12,184 permits), +0.96 (71 places, 500 sets, 12,947 permits) and +0.95 (74 places, 12,759 permits). The earlier high end, the 95th percentile of 2,000 resamples of the 76 places (+1.43, 19,186 permits), is kept as a sensitivity case, as is the first 24 places' +2.21. The rate is applied to the 2,684,793 existing Wisconsin homes outside the 9 places that already have no minimums (10 municipality pieces, because Brodhead spans two counties). That gives 12,695 permits over 2027–2031, 10.4% above current law (12,695 of 122,619).
   **Shared reporting (AQ-054).** In additional homes permitted per year against the shared all-housing baseline, the central case adds 0 a year and the upper case about 2,539 a year. Home counts that compare reforms use ACS 2020–2024 total housing units: 2,778,572 statewide, of which 2,684,793 are outside places already at the benchmark. The median of real cases, applied to Wisconsin, is shown as a reference line: the median repeal place changed by −0.12 permits per 1,000 existing homes per year. Since a repeal is not modelled as reducing permits, the line sits at 0, the same as the central case.
   **Control-city (placebo) check.** 4,626 cities that kept their minimums were given the real places' repeal years and run through the same calculation, 20,000 times. Only 2.7% of these placebo studies came out as low as the real places, so there is no sign that a repeal raised permits. Their spread sets the upper case ([PLACEBO_RESULTS.md](PLACEBO_RESULTS.md)).
5. **Timing.** The effect was measured over years 1–3, and it does not build up over time. The upper case is held flat through 2031. That is an assumption, and the measured path suggests it is generous.
6. **Where the upper case lands.** It is spread in proportion to existing homes, because the comparison could not tell which kinds of places respond more (owner decision AQ-046; no size split beat one average).

## Data sources and cleaning steps

| Data | Use | Licence |
| --- | --- | --- |
| Census Building Permits Survey: Wisconsin places 2015–2025; all US places 2012–2025; state totals 1990–2025 | Baseline; repeal comparison; baseline range | Public domain |
| ACS 2020–2024 (housing units, population, rent) | Existing homes; matching comparison places | Public domain |
| Milwaukee Master Property file | Milwaukee's apartment permits, which the Census file under-counts | CC-BY |
| Parking Reform Network reform map (pinned commit) | Which places removed minimums, and how fully | MIT |
| Municipal codes and ordinances (46 places) | Checking each repeal: in force, dates, exceptions, other zoning changes | Public records, cited |

Cleaning is recorded in [HOUSING_BASELINE.md](../shared/HOUSING_BASELINE.md), [POLICY_TAXONOMY.md](POLICY_TAXONOMY.md) and [COMPARISON_PLAN.md](COMPARISON_PLAN.md) (deviations 1–4). Every download is fetched by script, with URL, date and SHA-256 recorded.

## Methodological approach

**Baseline.**
- Census permits are allocated to the 1,925 municipality pieces, and reconciled to the state through an explicit unallocated row.
- Each place is held at its 2023–2025 average. That window was chosen by a held-out-year test against trend and other window lengths.
- The range is Wisconsin's 10th–90th percentile five-year outcomes since 1990.

**Response.** A pre-registered before/after comparison, a difference in differences:
- each place's change in permits per 1,000 existing homes, minus the same change in its comparison places;
- averaged with each place weighted by its homes;
- tested by leaving one place out at a time, resampling, leaving one state out, and other checks.

**Scenario.** Option A (owner, 2026-10-26): central 0, upper at the high end of the likely range. Places already at the benchmark get 0.

## Limitations and known edge cases

- The sample is 76 places, and most repealed as part of a wider zoning rewrite. Parking's own effect cannot be fully separated out. Some places have only one or two years since repeal.
- No prediction tool (weighted regression, lasso, random or causal forest) and no city trait beat one average on places left out of the fit, so every Wisconsin place gets the same rate.
- The after period is three years. Larger projects may take longer to reach a permit.
- The places chose to repeal, so they may differ from places that did not.
- The Census permit data have reporting gaps. Milwaukee's apartments are estimated, and its 2025 figure is missing.
- The upper case is spread by homes, not by where minimums actually bind. Rural towns with few minimums get a share.
- The tool does not estimate rents, parking supply, traffic or street-parking spillover.
- Whether evidence from cities that repealed by choice may stand in for a statewide law is still open: office-hours question 26.
- The baseline and the bundle rebuild exactly from the committed reference tables. A full rebuild from raw data follows the order in [REBUILD.md](REBUILD.md).

## Sensitivity notes

Five-year totals, 2027–2031, in additional permits unless noted. All are in the tool under "How sure".

| Changes | Case | Value |
| --- | --- | ---: |
| The statewide total | Resampling the 76 real places (earlier high end) | 19,186 |
| The statewide total | Only buildings of 2 or more units counted (resampling) | 10,373 |
| The statewide total | Without San Francisco (resampling) | 24,520 |
| The statewide total | Combined with California's transit-area law | 15,138 |
| The statewide total | First 24 places only (earlier estimate) | 29,662 |
| The statewide total and where it lands | Prediction by city size and setting (first 24 places) | 32,135 |
| The statewide total and where it lands | Towns left out | 8,829 |
| The statewide total and where it lands | Places that partly removed minimums left out | 12,619 |
| Current law only | Census as published for Milwaukee | 118,822 permits under current law |

Stability (first 24 places): leaving one state out at a time gave an average effect of −2.47 to +0.09 permits per 1,000 homes per year.

## Intended users and appropriate use cases

Wisconsin legislators and staff asking whether a statewide parking repeal would raise housing production.
- **Appropriate:** reading the result as "little or no measurable change within five years, with a stated high end", and seeing where that high end would fall.
- **Not appropriate:** reading municipal figures as local forecasts; using them to judge a parking repeal's effect on rents or parking supply.
