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

None yet.
