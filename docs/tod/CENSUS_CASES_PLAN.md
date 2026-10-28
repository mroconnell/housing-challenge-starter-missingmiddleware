# More reforms measured with census block counts, with holdouts and a method check: plan written before looking

Written 2026-10-28 by the TOD conductor, at the owner's request. He asked to add the best candidates and the weaker reforms, to include reforms of 2001–2009 that mostly took effect in 2008–2015, to find the upzoned-area boundaries where possible "with holdouts to verify", and to "check the data we already have done the other way to see if any of our current data sets disagree with this new census methodology and by how much". No housing count has been tabulated for any area named here before this file was committed; the commit is the timestamp. The method follows [SLC_CENSUS_PLAN.md](SLC_CENSUS_PLAN.md). Changes go in section 8 with a date and a reason.

## 1. Questions

1. **New cases.** For each reform below, did the upzoned land gain more homes from 2010 to 2020 than nearby land that was not upzoned?
2. **Holdouts.** Two of the new cases are set aside now. Do their results fall where the other census cases predict?
3. **Method check.** On cases already measured from permits, do census counts and permit counts tell the same story about the same land over the same years? By how much do they differ?

## 2. Data

- **Homes:** Census 2010 blocks with housing counts (TIGER/Line 2010 block file with population and housing) and Census 2020 blocks (TIGER/Line 2020, HOUSING20), for every state below. Public domain, fetched by script.
- **Placement:** blocks are placed by their internal point, each year's own blocks. Land is each block's polygon area.
- **Boundaries** of the upzoned areas (section 3). Only official city or county layers, or our own existing case data. A reform whose boundary cannot be found this way is reported as dropped, with the reason.

## 3. Reforms and boundaries

| Reform | Year | Strength (inventory) | Boundary source | Role |
| --- | --- | --- | --- | --- |
| Jersey City, Journal Square 2060 Redevelopment Plan | adopted 25 Aug 2010 | medium | City of Jersey City zoning layer, "Journal Square 2060" polygons | **holdout** |
| Milpitas, Transit Area Specific Plan | 2008 | medium | City of Milpitas "TASP" layer | **holdout** |
| Phoenix, Walkable Urban Code rezonings | 2015 onward | medium | our Phoenix case data: WU polygons with approval year, members approved 2015–2016 only | fitted |
| Salt Lake City, TSA district | 2010 | medium | [SLC_CENSUS_RESULTS.md](SLC_CENSUS_RESULTS.md), main estimate as already computed | fitted |
| Bellevue, BelRed | 2009 | medium | our Bellevue case data: parcels now in BelRed districts zoned by Ordinance 5875 | fitted |
| Austin, TOD station area plans | 2006–2009 | weak | City of Austin TOD layer, polygons marked "approved station area plan" only (the overlay alone did not raise density) | fitted |
| Tysons, Comprehensive Plan amendment | 2010 | weak | Fairfax County "Tysons Urban Center Boundary" | fitted |
| Cincinnati, form-based code | 2013 | weak | City of Cincinnati zoning layer, form-based transect districts (T3 to T5) | fitted |
| New Rochelle, Downtown Overlay Zone | 2015 | strong | none found (only the paper zoning map) | **dropped** |
| White Flint, Seattle Roosevelt, Minneapolis Hiawatha, Oakland Broadway Valdez, San Francisco Market and Octavia and Eastern Neighborhoods | 2008–2014 | weak | no official boundary layer found in the time given | **dropped**, can be added later |
| Atlanta BeltLine overlay | 2007 | weak | the inventory excludes it: a design overlay, not an upzoning | not used |

Reforms of 2008–2009 have their 2010 count one to two years after adoption. Their result is labelled "before count after adoption"; it understates the effect if building had already started.

## 4. Estimates for new cases (same as Salt Lake City)

- **Treated land:** blocks whose internal point lies inside the boundary.
- **Comparison land:** blocks within ½ mile of the boundary, outside it, and outside every other boundary in this plan.
- **Effect:** net homes added from 2010 to 2020 per acre, treated minus comparison. Also shown per year (÷ 10).
- **Uncertainty:** 90% interval from resampling blocks within each group, 2,000 draws, seed 20261030.
- **Checks:**
  - largest 2020 block left out of each group;
  - comparison limited to ¼ to ½ mile.

## 5. Holdout check, fixed now

The **fitted** cases are Phoenix, Salt Lake City, Bellevue, Austin, Tysons and Cincinnati, or those of them that are measured. They give:

- a **median**;
- a **range** (lowest to highest) of the per-acre-per-year effect.

A holdout **agrees** if its estimate lies inside that range **and** its 90% interval includes the median. Both holdouts agreeing means the census cases tell a consistent story across places. Either disagreeing is reported as the census cases not predicting new places.

## 6. Method check on cases already measured from permits

- **Cases:**
  - Saint Paul;
  - Seattle (North Beacon Hill and Othello; Mount Baker);
  - Los Angeles (Warner Center; Cornfield Arroyo Seco);
  - Chicago;
  - Philadelphia;
  - New York (pooled members);
  - Charlotte. Its reform came in 2019, so this measures land only, not the reform. It is included to test whether the two sources count the same homes.
- **Areas:** each case's own treated land (the "treated union" in its net-effect files) and its ring of unchanged land within ¼ mile. Census blocks are placed by internal point.
- **Census side:** net homes added from 1 April 2010 to 1 April 2020, per acre.
- **Permit side:** homes in permits issued in 2009 to 2018 on the same case's lots, per eligible acre. Permits lead finished homes by about a year. A second alignment, 2010 to 2019, is also shown.
- **Reported, per case:**
  - census homes ÷ permit homes in the treated land and in the ring (1.0 means they agree; below 1 means demolitions, unfinished permits, or census under-counts);
  - the treated-minus-ring difference on each side;
  - the gap between the two differences.
- **Agreement rule:** the two methods agree on a case if the census difference's 90% interval includes the permit difference. Overall they agree if at least two thirds of cases do.

## 7. How it is used

Context and a test of the census method, as for Salt Lake City. No finalized TOD number (AQ-055) changes without the owner.

## 8. Changes after writing

None yet.
