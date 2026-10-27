# TOD trait test: plan written before looking at results

Written 2026-10-27 by the TOD conductor, at the owner's request ("Add all of your hunches to mine and run the big test"), before any trait has been compared with any effect. The commit that adds this file is the timestamp. Any later change goes in section 8 with a date and a reason. The parking scenario ran a similar test ([TRAITS_PLAN.md](../parking/TRAITS_PLAN.md)).

## 1. Question

Why did upzoning near transit add many homes in some places and almost none in others? Can the answer narrow Wisconsin's range (171 to 17,148 extra homes over 2027–2031)?

## 2. Units of analysis

The question is answered on the separate rezonings and station areas inside each measured case, not on whole cities. A case with five cities would be too few to learn anything.

| City | Units | Count (expected) |
| --- | --- | --- |
| New York | Each of the 17 measured rezonings in the pooled set | 17 |
| Philadelphia | Each remapping bill area | up to 83 |
| Charlotte | Each station area within its 2019 districts | about 20 |
| Chicago | Each station area with upzoned land | to be listed |
| Saint Paul | Each Green Line station area (context: 1 year before only) | about 18 |
| Madison | The overlay, split by corridor segment | to be listed |

**Rules for including a unit:**
- Its own difference-in-differences is computed with the same rules as its case ([CASE_ANALYSIS_PLAN.md](CASE_ANALYSIS_PLAN.md)): treatment lots whose allowed density rose against unchanged lots nearby.
- A unit is kept if it has at least 5 eligible acres in each of the treatment and comparison areas. The unit list is fixed before any trait is joined.

## 3. Outcome

Extra homes permitted per eligible acre per year: the after period minus the before period, against the comparison area. Each unit is weighted by its eligible treatment acres.

## 4. Traits tested

Measured for each unit's treatment area before the change, from sources already in use or openly available (American Community Survey by tract, parcels, the Census Gazetteer and transit stops). Each trait's exact source is written down before it is joined.

**The owner's:**
1. Median home value.
2. Average lot size of treatment parcels.
3. Existing density: homes per eligible acre before the change.
4. Local earnings: median household income.
5. Land area of the city.

**The TOD conductor's:**
6. Median gross rent (market strength).
7. Size of the upzoning: added floor area ratio, or added height where no ratio exists.
8. Building rate before the change: homes permitted per acre per year.
9. Share of treatment land that was vacant, parking or industrial before the change (large-site potential).
10. Distance from the unit's centre to the city's downtown.
11. Jobs within 30 minutes by transit, or a published access index if the jobs data cannot be fetched openly.
12. Whether the reform also cut parking minimums (city level).

## 5. How a trait is judged (held-out test)

1. **Baseline model:** the weighted mean effect across the units used for fitting, with no traits.
2. **One trait at a time:** a weighted linear model of the effect on that trait. Rent, home value, income, density and land area are entered as logarithms.
3. **Leave-one-city-out:**
   - Each city's units are predicted from a model fitted on the other cities only.
   - Prediction error is the acre-weighted mean absolute error in extra homes per acre per year.
   - A trait passes if it lowers the held-out error against the baseline model, both on average across cities and in at least half of the cities.
4. **The two named test cases:** Chicago and Madison units are always predicted, never used for fitting, and reported separately.
5. **Two-trait model:** only the traits that pass are combined, two at a time, and judged the same way. No trait is kept for fitting the cases well; only held-out prediction counts.
6. **Multiple testing:** with 12 traits, some will pass by chance. Every trait's result is reported, and a trait that passes in only one held-out city is called a near-miss, not a finding.

## 6. How a result would be used

- **If a trait passes:** it is applied to each Wisconsin station area, using that area's own value of the trait, to give an area-specific rate for placing and sizing the per-acre response. The statewide net-effect scenarios (AQ-050) stay as they are unless the owner decides otherwise. The trait-based result is shown as a sensitivity and on the "Why" screen.
- **If no trait passes:** say so plainly. The range stays as it is.

## 7. Known threats, stated now

- **New York dominates.** Its units are many and large, so leaving New York out is the most important fold.
- **Different cities, different decades.** Philadelphia's units measure mostly height changes, and some of its remapping lowered density.
- **Some units are small, so their effects are noisy.** Acre weighting limits this.
- **Traits travel together.** Rent, income and home value are correlated, so the one-at-a-time test can show which helps but not which causes.

## 8. Changes after writing

All entries are dated 2026-10-27. They were written while running the test; results are in [TRAITS_RESULTS.md](TRAITS_RESULTS.md). Items 1 to 4 were settled before the unit list was fixed; items 5 to 11 before any trait was joined to an effect; items 12 and 13 after the first held-out run.

1. **How station areas and segments are cut (section 2).** The plan names the units but not the cut.
   - **Station areas** (Charlotte, Chicago, Saint Paul): each treated lot goes to its nearest station. Stops within 150 m of each other (platforms, two directions) are one station. Saint Paul uses its case's Green Line stations only.
   - **Madison's corridor segments:** the Isthmus core (treated lots within 1 mile of the State Capitol) and eight 45-degree sectors around it.
   - **Each unit's comparison:** the case's own comparison lots within ¼ mile of the unit's treated lots, the case's ring rule applied to the unit. Neighbouring units can share comparison lots.
   - **Reason:** the plan's "its own difference-in-differences ... with the same rules as its case" needs a comparison per unit; this is the case rule at unit scale. The cut uses only geography, not outcomes.
2. **New York's unit count.** The plan expected 17 units. All 17 pooled-set rezonings were built, but 6 have under 5 eligible treatment or comparison acres and are dropped by the plan's own 5-acre rule. No change of rule; recorded because the count differs from the plan's table.
3. **Saint Paul is fitted.** Its case is context only (1 before year). The plan's unit table lists it, and section 5 excludes only Chicago and Madison from fitting, so its units are fitted. Reason: the plan as written.
4. **Which cities the pass rule counts (section 5.3).** "On average across cities and in at least half of the cities" is judged on the four leave-one-city-out folds: New York, Philadelphia, Charlotte and Saint Paul. "On average" is the simple mean of the four cities' acre-weighted errors. Chicago and Madison are predicted from all four and reported separately (section 5.4). A trait that lowers the error in exactly one fold city is a near-miss (section 5.6). Reason: the plan does not say whether the two always-held-out cities count toward "half of the cities"; reading 5.4 as "reported separately" keeps them out of the judging.
5. **ACS vintages (section 4, "before the change").** Rent, home value and income come from the ACS 2006–2010 5-year file for every unit outside Madison and from 2018–2022 for Madison, by tract, in 2024 dollars (CPI-U).
   - No ACS exists before 2005–2009, so for New York rezonings of 2003–2010 the values are from around or after the change.
   - The Census Data API now needs a key. The 2006–2010 summary files were used instead; for New York, the whole-state file stalled on the Census server, so the per-sequence files of the same release were used.
6. **Density's logarithm (section 5.2).** Some units had no homes before, so the logarithm is of (homes per acre + 1).
7. **Size of the upzoning (trait 7).** Only added floor area ratio is used. Charlotte's dose is added height in feet and Philadelphia has no dose, so their units have no value for this trait. The trait is judged on the units that have it, against the baseline on the same units. Reason: feet and FAR cannot enter one linear model, and the cases already keep them apart.
8. **Existing density (trait 3).** New York uses units on the lots in the MapPLUTO snapshot before each rezoning. Charlotte, Chicago, Philadelphia and Saint Paul use 2010 census block homes inside treated lots (the cases' rule). Madison uses today's parcel dwelling units, which include homes built after 2023.
9. **Vacant, parking or industrial land (trait 9).** Only New York has land use from before the change. Elsewhere the parcel layers are today's, so lots that received a new-housing permit in the unit's before or after years are left out of the share. Otherwise land that was built on would read as "not vacant" because it was built on.
10. **Jobs access (trait 11).** Jobs data (LEHD LODES) can be fetched openly, but jobs within 30 minutes by transit for each city before its change would need that city's past transit schedules and a routing run. The published index used instead is the EPA Smart Location Database v3 field D5BR: jobs within a 45-minute transit trip, weighted by travel time, from 2017 schedules and jobs, by block group.
11. **City land area (trait 5)** is from the 2024 Gazetteer (today's boundaries).
12. **Wisconsin step (section 6).** The only passing trait (12, parking minimums cut) is a city-level property of the law, so it cannot give each Wisconsin station area its own rate. The sensitivity table gives every area two rates, with the trait at 0 (the current model, parking left to the parking scenario) and at 1 (Gate 1 benchmark T5). Reason: section 6 assumes an area-level trait; this one is not.
13. **Near-miss before half-of-cities (sections 5.3 and 5.6).** The first run judged added FAR (trait 7) a pass: it is testable in only two fold cities (New York and Saint Paul) and lowered the error in one, which is "half". Section 5.6 calls a trait that passes in only one held-out city a near-miss, so the rule now applies 5.6 first: lower error in exactly one fold city is a near-miss, whatever the number of folds. This was changed after seeing the first run; it changed trait 7 from pass to near-miss and no other verdict.

**2026-10-27, exploratory combinations (owner request, "run it"; written before any pair is tested).** The confirmatory test above allowed pairs only of passing traits. As an exploration, every pair of the 12 traits (66 pairs) is tested, plus one small regression tree with depth at most 2 and at least 8 units per leaf, fitted on the same traits.
- **Folds and errors:** the same leave-one-city-out folds over New York, Philadelphia, Charlotte and Saint Paul. The same acre-weighted error. Traits use the same logarithms.
- **Stricter pass rule, fixed now:** a pair or tree passes only if all three hold:
  - it beats the no-trait baseline in at least 3 of the 4 fitted cities;
  - it beats the baseline on average across the fitted cities;
  - it beats the baseline on both held-out cases, Chicago and Madison, each by itself.
- **How results are shown:** every pair's result is reported. Anything that passes is labelled exploratory: shown as a sensitivity only, never used for the main estimate, and stated with the warning that about 3 of 66 pairs would be expected to look good by chance.

**2026-10-27, how the exploratory tree is built (details the entry above leaves open; fixed before the tree was run).** The tree is a least-squares regression tree weighted by eligible treatment acres. It may split on any of the 12 traits, as entered in the one-trait tests, and each split is "trait ≤ threshold", with thresholds halfway between adjacent observed values. Its leaves predict the acre-weighted mean effect. A unit with no value for the split's trait goes to the child with more acres; added FAR and two other traits are missing for some units. The tree is refitted inside each fold, and Chicago and Madison are predicted from the tree fitted on all four fitted cities. Pairs drop units missing either trait, and the baseline is judged on the same units, as in the one-trait test.
