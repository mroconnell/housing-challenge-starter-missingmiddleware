# TOD net effect and coverage: plan written before looking

Written 2026-10-27 by the TOD conductor, after the owner's questions about whether nearby building is just being moved, and about transit coverage. Written before any of the comparisons below are computed. The commit that adds this file is the timestamp. Changes go in section 8 with a date and a reason.

## 1. Questions

1. **Borrowing.** When land near transit was upzoned, did building fall just outside it? If so, how much of the local gain is building moved from next door rather than new homes?
2. **Net effect.** What is each city's own net effect: homes gained inside, minus homes lost in the ring next door?
3. **Coverage.** Do cities whose transit covers a large, continuous share of the city respond differently from cities with small, separate islands of transit coverage?
4. **Large sites.** Does the size of the largest continuous eligible site near a station predict the response?

## 2. Cases and areas

- **Cases:** every case in the fitted set (New York, Philadelphia, Charlotte, Saint Paul, Los Angeles, Seattle), plus Chicago and Madison, which are still never used for fitting.
- **Areas, per case:**
  - treatment (upzoned land, as before);
  - the ring (unchanged land within ¼ mile of the treatment);
  - far land (unchanged land ¼ to 1½ miles from the treatment, in the same city).
- **Rules:** the eligible-land rules are as in [CASE_ANALYSIS_PLAN.md](CASE_ANALYSIS_PLAN.md).

## 3. Borrowing and net effect

- **Borrowing:** the difference-in-differences of the ring against far land, in homes permitted per eligible acre per year, after against before. A negative value means building moved out of the ring.
- **Net effect:** (the treatment's difference against far land × treatment acres) + (the ring's difference against far land × ring acres), in extra homes per year. It is divided by the city's housing stock to give a citywide net share, comparable with the Los Angeles, Stacy et al. and Auckland figures.
- **Uncertainty:** 90% intervals from resampling projects within each case, 2,000 draws, seed 20261027.

## 4. Coverage traits (owner's theory)

- **City coverage:** the share of the city's land, and of its homes, within ½ mile of rail or rapid stations and ¼ mile of 15-minute buses. Measured with the same stop rules as Wisconsin, from the National Transit Map and each city's schedules, in the year before its reform.
- **Island size:** for each unit, the area of the continuous covered patch it sits in. A long connected network gives large patches; scattered stations give small islands.
- **Largest continuous eligible site:** for each unit, the largest group of touching eligible parcels within the station area, in acres.

## 5. Tests

- **Coverage and the net effect.** Unit-level traits (island size, largest site) enter the trait test with the same leave-one-city-out rule and the same pass rule. The rule is the latest entry in [TRAITS_PLAN.md](TRAITS_PLAN.md) section 8: beat the plain average in at least two-thirds of fitted cities, on the mean error, and on Chicago and Madison separately.
- **City coverage** has one value per city, so it is not judged as a predictor. It is reported next to each city's net effect, with the warning that six to eight cities cannot separate it from everything else about them.

## 6. How a result would be used

If the cities' own net effects are measured with intervals tighter than the spread between the borrowed studies, they are brought to the owner as a candidate replacement for the borrowed scenario sizes (AQ-050, AQ-056). That would mean, for example, the lowest, the median and the highest city net share. Nothing changes without the owner's approval.

## 7. Known threats, stated now

- **Rings are small,** so the borrowing estimates are noisy.
- **Far land can also be affected** by citywide booms.
- **Coverage is measured from today's stop layers** where historical ones are missing; this is recorded per city.

## 8. Changes after writing

**2026-10-27, corridor versus scattered nodes (owner request; written before any shape is measured).** Two more unit-level traits, measured on each unit's upzoned land and judged by the same rule as section 5:
- **Elongation:** the length of the upzoned patch divided by its average width, using the minimum rotated rectangle. A long strip along a street or line scores high; a round station circle scores near 1.
- **Corridor share:** the share of the case's upzoned land lying in pieces at least ½ mile long.

Each case is also labelled "corridor" (mostly long continuous strips, such as Madison's overlay or Park Slope's Fourth Avenue) or "nodes" (mostly separate station circles, such as Charlotte or Chicago), from these measures with a ½ cut on corridor share. Because shape is mostly one design choice per city, the label is reported next to each city's net effect rather than judged as a predictor.

**2026-10-27, two additions from the literature review ([research/LITERATURE_NET_EFFECTS.md](research/LITERATURE_NET_EFFECTS.md)), written before any result of this plan is seen.**
- **Binding limit.** The strongest predictor in the literature is whether the old limit was binding (Zurich). Each unit gets a trait: the acre-weighted ratio of existing built density (homes per acre, or floor area where known) to the density allowed before the reform. A value near 1 means lots were already built to the old limit. It is judged by the same rule as section 5.
- **Distant borrowing.** In Auckland, building was drawn from distant areas, not next door. Where each case has land beyond 1½ miles, that land's change after against before is also compared with the rest of the region (other jurisdictions in the same county or metro, from Census permits). This is reported as a check on whether "far land" is itself affected.

**2026-10-27, car-dependence traits (owner request; written before any result of this plan is seen).** Three unit-level traits from the American Community Survey by tract, for the treatment area, using the 5-year survey nearest before each reform (the earliest available, 2005–2009, for reforms before 2009). Each is judged by the same rule as section 5:
- **Car-free households:** the share of households with no vehicle available (table B25044 or B08201).
- **Transit commuting:** the share of workers commuting by public transit (B08301).
- **Commute time:** the mean travel time to work, in minutes (B08303, or aggregate travel time ÷ workers).

Driver's-licence counts are published only by state (FHWA), so they cannot vary across station areas and are not used.

**2026-10-27, how the plan was carried out (deviations recorded while running it).** Results are in [NET_EFFECT_RESULTS.md](NET_EFFECT_RESULTS.md).
1. **Work extents.** Two case adapters load lots only near each rezoning: New York within a box 1,500 m around each member, and Philadelphia within 2,000 m of each bill. Both are less than 1½ miles (2,414 m). While those adapters run, that one distance is widened to 2,700 m; nothing else changes. Every case's treatment and ring acres and its own estimate are reproduced exactly. Los Angeles parcels and permits were fetched only for each plan's area plus 1.8 km, so its far land stops there; this is shown per case as the share of the ¼ to 1½ mile band that has lots.
2. **Far land** is eligible land in the same city that the case's rule leaves unchanged. It may include the case's second-comparison lots. Lots the rule puts in no area are never far land: rezoned elsewhere, already at the law, or in the reform but not risen. Stacked cases (New York, Philadelphia) get far land per member and are stacked in event time, like the other areas.
3. **Years.** Each case keeps its own before and after years. Madison uses its test's years: before 2017 to 2022, after 2023 to 2025, including the effective year. Saint Paul has only one before year; its case is context only, but the plan lists it, so it is reported with that warning.
4. **City stock and shares.**
   - The stock is 2010 Census homes in the city's 2010 boundary; Madison uses 2020 blocks in its 2024 boundary. These come from the coverage build.
   - The five-year share is 5 × the yearly share.
   - Los Angeles and Seattle each have two cases. Their net homes are added, and their resampling draws are added, since the draws are independent.
5. **Coverage** (plan section 7, as foreseen). Coverage uses today's stops and timetables: National Transit Map rail stops (compiled 2026-09-23) and each main agency's current GTFS. No historical feeds could be fetched without an account.
   - A bus stop qualifies when a 15-minute route's trips serve it. This replaces Wisconsin's rule of a stop within 30 m of the route line.
   - Madison counts Rapid Route A, which opened after its 2023 reform.
   - Code: `scripts/build_tod_net_coverage.py`.
6. **Unit traits.** Each trait is measured on each trait-test unit's eligible treatment lots, the land whose density rose.
   - **Island size:** the covered patch that overlaps most of that land.
   - **Largest site:** lots within 1 m of each other count as touching. "Within the station area" is read as the unit's upzoned eligible lots.
   - **Elongation:** length² ÷ area. Length is the long side of the minimum rotated rectangle; average width is area ÷ length.
   - **Pieces:** lots within 30 m of each other are one piece, which bridges streets.
   - **Logs:** island size, largest site and elongation are entered as log(value + 1) because they span orders of magnitude. This was fixed in the code before the test was run.
   - **Corridor share and label:** the unit-level share is measured on the unit's lots. The case label is measured on the reform's whole upzoned land: reform lots whose density rose, before the at-law and rezoned-elsewhere exclusions, with stacked members together.
7. **Binding limit.** The ratio is homes per eligible acre before (trait 3 of the trait test) ÷ the homes per acre the old limit allowed. The allowed figure is the acre-weighted old FAR × 43,560 ÷ 1,417 square feet a home (pooled Milwaukee and Madison new buildings, `reference/tod_floor_area_per_home.csv`).
   - Only units whose old limit is a FAR have a value: New York, Chicago, Saint Paul, Seattle and Madison. Charlotte has heights, Philadelphia has no dose, and Los Angeles has ordinal levels.
   - So the trait is testable in only 3 of the 6 fold cities and cannot pass.
8. **Car dependence.**
   - **Vintages:** ACS 2006–2010 for every unit outside Madison (the vintage the trait test already uses, with sequences 25, 30 and 97 fetched for New York, California and Washington); ACS 2018–2022 for Madison. For reforms after 2011 (Charlotte, Philadelphia's later bills, Seattle, Los Angeles, Chicago), 2006–2010 is not the survey nearest before the reform; those vintages were not fetched.
   - **Mean commute:** B08013 aggregate minutes ÷ (B08301 workers − worked at home).
   - **Unit values:** ratios of acre-weighted tract counts.
9. **Distant borrowing.**
   - **"Rest of the region":** the other counties of the city's 2024 metro area (CBSA), from Census county permit files for 1996–2025. Place-level files on disk start in 2012.
   - **Land beyond 1½ miles:** the city's own permit records more than 1½ miles from the treatment. Stacked cases use the mean over members.
   - **Gaps:** Los Angeles has no citywide permit file. Saint Paul's file has units only from 2010.
10. **The trait test** uses the several-tools frame (`run_tod_traits.wide_frame`), the one-trait weighted regression and `traits.judge_tools`. A trait missing for a unit drops that unit, and the plain average is judged on the same units.
