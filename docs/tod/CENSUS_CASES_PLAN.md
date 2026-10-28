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

Recorded 2026-10-28 while running (results: [CENSUS_CASES_RESULTS.md](CENSUS_CASES_RESULTS.md)). Items 1 to 3 were fixed before any comparison was computed; item 4 was noticed in the results.

1. **Tysons boundary.** Fairfax County's layer is one polygon of the whole county with Tysons as its only hole (2,140 acres). The hole is used as the boundary.
2. **Cincinnati dropped.** Its zoning layer is a link-only entry on the city's data portal and could not be downloaded by script.
3. **Method check limited to case areas whose permit table spans 2010 to 2018** (corrected 2026-10-28, item 5). Some cases keep their whole permit file and some keep only each member's own before and after years.
4. **The census and permit areas are not the same land.** The permit side counts only eligible lots (treated lots, and unchanged lots in the ring). The census side counts every block whose point lies in the treated area or the ¼-mile ring, including streets, parks and ineligible lots. So the count ratios in section 6 compare different land; the per-acre differences are the like-for-like test.
5. **Correction, 2026-10-28, after the first report.** The first run required permits through 2019 and wrongly dropped Los Angeles, whose stored permits run 2007–2018 and cover the plan's main 2009–2018 alignment. The rule is now "covers 2010 to 2018", from each member's window or its full stored file. Los Angeles is back in. Only one of New York's 17 members (adopted 2013, permits 2007–2018) qualifies, and its land had no homes in either source, so New York is still not comparable.

## 9. Additions requested by the owner, written before running them (2026-10-28)

The owner asked for two more measures: "dropping the per acre in favor of per 1000 existing homes to bring it closer it to the other scenarios", and scoring "blocks based on whether they are entirely in the TOD radius or partially in the TOD radius or not at all". Neither has been computed before this section was committed.

1. **City share.**
   - **Extra homes** = the per-acre difference × the upzoned acres.
   - **Shown as:**
     - **main:** per 1,000 homes in the city in 2010 (2010 Gazetteer), over the decade and per five years (÷ 2). This is the unit of the cities' own net effects in [NET_EFFECT_RESULTS.md](NET_EFFECT_RESULTS.md).
     - per 1,000 homes already on the upzoned land in 2010, shown only where that land had at least 500 homes.
   - **Jurisdictions:** Tysons uses Fairfax County, the body that adopted it. Salt Lake City is recomputed with this plan's general rule (comparison = within ½ mile of the boundary).
2. **Blocks scored by how much of them lies in the area.** Each block's homes are split by the share of its land inside the upzoned area and inside the comparison ring, instead of placing the whole block by its centre point.
   - Blocks are reported as **wholly inside** (99% or more of their land), **partly inside**, or **outside**.
   - The per-acre difference and its 90% interval are recomputed this way (whole blocks resampled with their shares, 2,000 draws, seed 20261031). This is shown beside the centre-point result.
3. **Nothing else changes.** The holdout rule (section 5) is still judged on the centre-point result as planned. The area-share version is reported beside it.

## 10. Growing the census set, and placebo stations: written before running (2026-10-28)

The owner asked to "grow the census set if you can, and add placebo cities to help do that", and to treat pre-reform density as a variable. None of the results below has been computed before this section was committed.

### 10.1 More census-measured reforms

- **Existing cases, census side.** The 8 method-check cases (section 6) already have census estimates of the upzoned land against its ¼-mile ring. They join the census set with that estimate: Saint Paul, Seattle twice, Los Angeles twice, Chicago, Philadelphia, Charlotte. Charlotte is before its reform, so it is labelled "land only" and is not used as a reform.
- **New York's rezonings adopted 2008–2013**, measured with the census from their existing maps (treated land and ¼-mile ring from the net-effect files), one estimate per rezoning. Rezonings adopted before 2008 are left out, because most of their response came before the 2010 count.
- **Seattle Roosevelt (2012):** zoning polygons whose history lists Ordinance 123816, from the City zoning layer already in the Seattle case folder. Same estimate as section 4.
- **Maps still missing** (White Flint, San Francisco 2008 plans, Minneapolis Hiawatha, Oakland Broadway Valdez, Cincinnati, New Rochelle): they stay out unless an official layer is found. This list is reported.

### 10.2 Placebo stations

- **What:** rail stations (National Transit Map stops typed as rail, subway or light rail) in the 13 states already fetched. Stations are left out if they are:
  - inside a city on the 58-reform list (by 2020 Census place boundaries);
  - within 1 mile of any reform boundary in the census set.
- **The fake reform area** is the ½-mile circle around the station. The comparison is the ring from ½ to 1 mile, outside every other placebo station's circle. The estimate is net homes added 2010–2020 per acre, circle minus ring, with blocks scored by the share of their land inside (section 9). Stations with the same name within ¼ mile of each other are merged.
- **Known limit:** the National Transit Map has no opening dates, so some placebo stations opened after 2010. Station opening itself may raise building, which makes the placebo bar higher, not lower.
- **Reported:**
  - the placebo median and 5th to 95th percentile: what station areas gain over their surroundings without a known upzoning;
  - for each real reform, the share of placebo stations with a larger per-acre difference.

  A reform whose result beats 90% of placebos is read as standing out from ordinary station-area growth. This ranking compares a station circle with a plan boundary, so it is a reference, not a formal test.

### 10.3 Pre-reform density

Each census case and placebo records its upzoned area's 2010 homes per acre. It is reported beside each result, and it will be one of the named variables when the prediction tools are rerun on the census set. That rerun gets its own plan.
