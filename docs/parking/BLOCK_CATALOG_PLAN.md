# Parking: block-by-block catalog of area reforms like Seattle's urban villages, plan written before counting

Written 2026-10-28 by the parking conductor, at Ryan's request: "catalog the Seattle villages block by block as a promising result and find any other cases (even if they're noisy) that are similar … Use the TOD block counts." No block count for the areas named here has been tabulated for this catalog before this file was committed. Seattle's 2010–2020 figures were already computed ([CENSUS_ROUTE_RESULTS.md](CENSUS_ROUTE_RESULTS.md)), so they are known; everything else is new. Changes go in the last section with a date and a reason.

## 1. Measure

For each reform area against its comparison area:
- **Homes:** Census 2000 blocks (Summary File 1 geographic headers, as fetched by TOD's `run_tod_census2000.py`), 2010 blocks and 2020 blocks. Each year's blocks are placed by internal point.
- **Growth:** homes added per 1,000 existing homes per year, for each decade (2000–2010 on 2000 homes, 2010–2020 on 2010 homes). Net homes per acre per year is also reported, to compare with TOD.
- **Before gap:** the reform area minus the comparison area, 2000–2010. **After gap:** the same for 2010–2020.
- **Change in change:** after gap minus before gap. This is the headline for each case. It nets out a gap that was already there before the reform.
- **Share of the decade under the reform** is reported for each case. It is not used to scale the result, because the before decade is also partly affected for some cases.
- **90% range:** 2,000 bootstrap draws of census tracts (2020 tracts), within the reform and comparison areas separately.

## 2. Cases

| Case | Reform area | Comparison area | Reform in effect from |
| --- | --- | --- | --- |
| Seattle urban villages | Hub and residential urban villages (today's boundaries) | Rest of Seattle outside urban centers, villages and industrial centers | August 2012 |
| Hayward, South Hayward BART | Within ½ mile of South Hayward BART | ½ to 1½ miles from the station | 2011 |
| Fremont, Warm Springs | Within ½ mile of Warm Springs/South Fremont BART | ½ to 1½ miles from the station | July 2015; the station opened in 2017 |
| Minneapolis near-rail parking cut | Within ½ mile of light-rail stations, inside Minneapolis | The rest of Minneapolis, outside downtown | 2015. Minimums were removed for buildings of 50 or fewer units and halved for larger ones. Only the rail part is mapped; the ¼-mile bus part is not. |
| Chicago TOD ordinances (2013, 2015) | From TOD's catalog | | cited, not rerun |
| Salt Lake City station areas (2010) | From TOD's catalog | | cited, not rerun |

Station locations come from the National Transit Map rail stops already fetched by TOD (`data/raw/tod_census_cases/ntm_rail_stops.json`).

**Left out:**
- Portland 2002: needs a map of the 2002 light-rail and frequent-bus network.
- Seattle 2006: the reform could not be confirmed.
- San Diego 2019, Charlotte 2019, Albuquerque 2018: under two years of the decade, and no later census yet.

## 3. Older repeals with permit data

Brownville, Nebraska (2004), Ozawkie and Westmoreland, Kansas (2007) and Philip, South Dakota (2009) are run through the permit route. The method:
- the same windows: 5 years before and years 1–3 after;
- same-state comparison places at ½–2× their 2000 population;
- Census permit place files back to 1999, read by place name.

They are reported as a group and do not enter the 76-place average. They predate its 2015–2024 window, and it would only change with Ryan's approval.

## 4. Use

This is a catalog of evidence, reported case by case. It does not change the tool.

## Changes after writing
