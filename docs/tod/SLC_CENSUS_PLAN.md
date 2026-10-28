# Salt Lake City's 2010 station-area districts, measured with census block counts: plan written before looking

Written 2026-10-28 by the TOD conductor, at the owner's request ("Is slc reform so old that we could see the development in census or map data?"). No housing count has been tabulated for any area named here before this file was committed; the commit is the timestamp. Changes go in section 8 with a date and a reason.

## 1. Question

Salt Lake City's Transit Station Area (TSA) district (Ordinance 59 of 2010, effective 11 August 2010) removed density limits and allowed 50 to 90 feet around the Airport TRAX line stations on North Temple. The line opened in April 2013. Did the TSA land gain more homes from 2010 to 2020 than nearby land on the same new rail line that was not put in the district?

Salt Lake City has no permit file a script can fetch ([research/CASE_INVENTORY.md](research/CASE_INVENTORY.md)), so the census counts are used instead. The 2010 census counted homes on every block as of 1 April 2010, four months before the reform. The 2020 census counted them again. The change between the two counts is **net homes added on each block, after demolitions**.

## 2. Data (all public, fetched by script, raw files not committed)

- **Homes in 2010:** Census 2010 blocks with housing units (TIGER/Line 2010 block file with population and housing counts, Utah).
- **Homes in 2020:** Census 2020 blocks with housing units (TIGER/Line 2020 block file, HOUSING20, Utah). Block housing-unit totals were published without the 2020 privacy noise.
- **Stations:** the federal National Transit Map stops for the Utah Transit Authority (same source as Wisconsin).
- **TSA district land:** a 2020 snapshot of Salt Lake City zoning published on ArcGIS Online by a consultant (Jacobs). The ordinance's own map (Exhibit C) is no longer online. Only TSA land nearest the 2010 ordinance's stations is used (section 3). This boundary is a known weakness: the 2020 map may differ from the 2010 one.

## 3. Areas

Each block is placed by its internal point, separately for the 2010 and 2020 blocks, so no crosswalk is needed. Land area is the blocks' land area.

- **Stations named in the 2010 ordinance** (and their National Transit Map names):
  - North Temple Viaduct (North Temple Station)
  - 800 West (Jackson/Euclid)
  - Fairpark
  - Cornell (Power)
  - 1950 West (1940 W. North Temple)
  - 2200 West
- **Treated land:** TSA-zoned land in the 2020 map whose nearest rail station is one of these.
- **Comparison 1 (main): same line, not in the district.** Blocks within ½ mile of these stations that are not TSA land.
- **Comparison 2: other new stations outside Salt Lake City, same years.** Blocks within ½ mile of the TRAX stations opened 2011–2013 outside Salt Lake City:
  - West Valley line, August 2011: Decker Lake, West Valley Central, Redwood Junction, River Trail;
  - Mid-Jordan line, August 2011: every station from Bingham Junction west to Daybreak Parkway;
  - Draper extension, August 2013: Kimballs Lane, Draper Town Center.

  Some of these cities may have rezoned their own station areas; if so, comparison 2 leans toward finding no effect.
- **Left out of everything:** TSA land at stations added after 2010 (Library, Trolley, 900 East, Arena), and the downtown free-fare zone.

## 4. Outcome and estimates

- **Main:** net homes added from 2010 to 2020 per acre of land, treated minus comparison 1. Shown also per year (÷ 10), to set beside the other cases' homes per acre per year.
- **Also shown:**
  - the same against comparison 2;
  - net homes added per 1,000 homes in 2010;
  - the treated area's net gain as a share of Salt Lake City's 2010 homes (the city-share unit of [NET_EFFECT_RESULTS.md](NET_EFFECT_RESULTS.md)).
- **Uncertainty:** 90% intervals from resampling blocks within each group, 2,000 draws, seed 20261029.
- **Checks fixed now:**
  - largest single block left out of each group;
  - treated land limited to TSA "core" zones (ending -C);
  - comparison 1 limited to ¼ to ½ mile.

## 5. Limits written down now

- **No before-trend.** The 2000 block counts are not used (no reliable 2000-to-2010 block match was fetched). So the main comparison rests on the treated and comparison land following similar paths without the reform.
- **The new rail line opened in 2013,** so both groups get the line; only the zoning differs.
- **The 2020 map may not match the 2010 district.**
- **Other rezonings near the line between 2010 and 2020 are unknown.** If comparison land was also upzoned, the comparison leans toward finding no effect.

## 6. How it is used

This is context only. It does not change the finalized TOD numbers (AQ-055). If it is measurable, Salt Lake City is added to the case table as a census-measured case, and the result goes beside the other cases, read with the limits above.

## 7. Expectation

None written down. The TSA land is mostly commercial and industrial with few homes in 2010, so a gain per 1,000 existing homes may be large and unstable; per acre is the main measure for that reason.

## 8. Changes after writing

None yet.
