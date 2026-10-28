# Parking: rescuing dropped places, plan written before computing results

Written 2026-10-28 by the parking conductor, at Ryan's request: look hard for South Bend, fill or trim Gastonia's missing years, search harder for Algoma, and test the census-count method (used by TOD for Salt Lake City) against permit data. No effect has been computed for any place named here before this file was committed. Changes go in the last section with a date and a reason.

## 1. South Bend, Indiana (repealed 2021)

**What we found before computing anything.** South Bend has no row of its own in the Census permit files for 2012–2025. The city and St. Joseph County share one building department. Its 2026 fee schedule says it covers the City of South Bend and the unincorporated county. In the Census files, the row "St. Joseph County Unincorporated Area" has the county's permits outside Mishawaka and the small towns, and the county total equals the sum of the place rows. So South Bend's permits are filed inside that row.

**Rule.** South Bend is added as a combined area: the city plus unincorporated St. Joseph County.
- Permits: the "St. Joseph County Unincorporated Area" row.
- Homes: ACS 2020–2024 homes for St. Joseph County minus its incorporated places other than South Bend.
- Comparison places, windows and weights: the same rules as every other place, matched on the combined area's population.
- **Main figure:** the combined area's effect divided by South Bend's share of the combined area's homes. This assumes the unincorporated county was not affected by the city's repeal.
- **Sensitivity:** the combined area's effect, not scaled.

The city's open-data portal has only currently active permits, so it cannot replace the Census row.

## 2. Gastonia, North Carolina, and the other places with missing permit years

Gastonia repealed in 2021. It reported for 2012–2022. Its 2023 row has 0 months reported, and it has no rows for 2024–2025.

**Rule, applied to every place excluded only for missing permit years** (Gastonia, Avondale Estates, Calumet):
- a year with 0 months reported counts as missing;
- the after-years are cut back to the years before the first missing one, and the before-years to the unbroken run just before the repeal;
- the place is kept if it has at least 1 after-year and at least 3 before-years, the same minimums as the expanded comparison.

Census monthly files are not used to fill gaps, because a place with no annual row also has no monthly reports.

## 3. Algoma, Wisconsin

Search for an adoption date in the city code, council and plan commission minutes, and local news. If a date is found and checked against the ordinance, Algoma is added under the expanded comparison's rules. If not, it stays out and the search is recorded.

## 4. The census-count method, checked against permits

**Question.** How closely does the change in a place's homes between the 2010 and 2020 censuses match the permits it issued over the same years?

**Data.**
- Census 2010 blocks with housing counts, and Census 2020 blocks with housing counts (TIGER/Line, public domain).
- 2020 place boundaries (TIGER/Line).
- Census permit place files, 2010–2019. The 2010 and 2011 files are added for this test.

**States:** Wisconsin, Indiana, Minnesota and North Carolina (for the check), plus South Carolina, South Dakota and Pennsylvania (for the dropped 2008–2013 repeals).

**Method.**
- Both years' blocks are placed in 2020 place boundaries by each block's internal point, so boundaries do not change between the counts.
- Census change = 2020 homes minus 2010 homes.
- Permits = units permitted in 2010–2019. This ignores a lag of up to about a year from permit to completion; a sensitivity uses 2009–2018 where 2009 files are available.
- Places are kept if they have all 10 permit years and at least 100 homes in 2010.

**Reported.**
- correlation between census change and permits, across places;
- the median ratio of census change to permits, overall and by size band (under 2,500 homes; 2,500–25,000; over 25,000);
- the share of places where the two disagree by more than half the permits, or by more than 50 homes;
- how often the two agree on whether a place grew faster than the state's median place.

**Use.** If the census change tracks permits closely (correlation of at least 0.9 and a median ratio between 0.7 and 1.1), the five dropped 2008–2013 repeals are measured with census counts, against same-state comparison places at ½ to 2× population, as a separate check and not merged into the 71-place average. If not, the test result is reported and those five stay out.

## 5. After this

- Rescued places are added to the expanded comparison. The comparison, the placebo test and the Wisconsin numbers are rerun.
- Any change to the tool's high end goes to Ryan before it is final.

## Changes after writing
- **2026-10-28, after the owner approved adding the rescued places:** the full-pool placebo run uses 20,000 sets instead of 500. Repeated 500-set draws moved the high end by about ±0.1 permits per 1,000 existing homes per year, from chance alone.
