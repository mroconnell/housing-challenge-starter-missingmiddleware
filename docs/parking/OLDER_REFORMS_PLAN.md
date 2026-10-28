# Parking: Seattle 2012 and Portland 2002 transit-area reforms, plan written before counting

Written 2026-10-28 by the parking conductor, at Ryan's request. No permit count for any area or place named here has been computed before this file was committed. Changes go in the last section with a date and a reason.

These are transit-area reforms, not the benchmark (all housing, citywide). Like California's AB 2097 test, they are a second check on the main estimate and do not change the tool's numbers.

## 1. Seattle, August 2012

**Reform.** Seattle removed residential parking minimums in urban villages within ¼ mile of frequent transit. The city's Parking Flexibility Areas map is dated 23 August 2012. Urban centers (Downtown, First Hill/Capitol Hill, the University District and others) already had no or reduced minimums before 2012. Outside centers and villages, minimums near frequent transit were cut by up to half.

**Data.**
- The City of Seattle's "Residential Building Permits Issued and Final since 1990" (ArcGIS Online, PDDL). Each permit has its issue year, net new units (`NET_UNITS`) and the comprehensive-plan area it falls in (`COMP_PLAN_NAME`, `COMP_PLAN_TYPE`).
- The city's urban center and village polygons, for land and homes.
- Census 2010 blocks with housing counts (Washington), placed in those polygons by internal point. These give the existing homes in each area.

**Areas.**
- **Treated:** permits in hub and residential urban villages.
- **Comparison:** permits outside urban centers and villages.
- **Left out:** urban centers and manufacturing/industrial centers, which were already exempt or are not residential.
- The urban-village boundaries are today's. Some villages grew after 2015, so a few blocks counted as treated were outside a village in 2012. This leans toward finding no difference.
- Not every 2012 urban village had frequent transit, so some treated land had no reform. This also leans toward finding no difference.

**Outcome.** Net new units permitted per 1,000 existing homes (2010 census) per year.
- Before: 2007–2011. After: 2013–2015 (years 1–3, as in the main comparison). 2012 is left out.
- Effect = (after − before) in treated areas − (after − before) in comparison areas.
- 90% range: 2,000 bootstrap draws of urban villages (treated) and of comparison permits grouped by census tract.
- **Sensitivity 1:** after-years 2013–2017.
- **Sensitivity 2:** comparison permits limited to multifamily and commercial zones (lowrise, midrise, highrise, neighborhood commercial and commercial). Existing homes for those zones are not available, so this case uses the change in log permits: log(after ÷ before), treated minus comparison.

## 2. Portland, Oregon, 2002 (citywide comparison, no map)

**Reform.** Ordinance 177028, the 2002 Parking Code Rewrite, removed minimums within 500 feet of 20-minute transit and ¼ mile of light rail. The repeal year used is 2003, the first full year in effect. Minimums came back in 2013 for buildings over 30 units; that is outside this window.

**Method.** The same method as the 74 repeal places, at citywide scale:
- **Outcome:** permits per 1,000 existing homes per year.
- **Before:** 1998–2002. **After:** 2004–2006. 2007 onward is left out because of the housing crash.
- **Comparison places:** same state at ½–2× population, widening to ⅓–3× and then to the Census division (Pacific). This is the same rule as the main comparison.
- **Data:** Census permit place files for 1998–2006 (older layout, matched by place name). Homes come from the 2000 census, using the Gazetteer place file (HU00).
- **90% range:** bootstrap over comparison places.
- **Diluted result:** the reform covered only part of the city. The share of Portland's homes near frequent transit is not known, so the citywide result is reported as is, without scaling.
- **Sensitivity:** without comparison places that had their own parking reforms in the window, if any are found in the Parking Reform Network data.

## 3. Reported

For each city:
- the effect and its 90% range;
- the before and after rates of the treated and comparison areas;
- how the result compares with the 74-place average (−1.14) and with California's AB 2097 test (+0.13 per 1,000 homes, 90% interval −1.84 to +1.73).

## Changes after writing
