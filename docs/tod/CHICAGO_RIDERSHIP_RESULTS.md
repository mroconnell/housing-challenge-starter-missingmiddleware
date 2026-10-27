# Chicago "L" ridership after transit-area upzoning: results

Plan: [CHICAGO_RIDERSHIP_PREREG.md](CHICAGO_RIDERSHIP_PREREG.md) (commit bfe1226). Data notes: [research/RIDERSHIP_DATA.md](research/RIDERSHIP_DATA.md). Code: `missing_middleware/tod/ridership.py`, `scripts/fetch_cta_ridership.py`, `scripts/run_chicago_ridership.py`. Tables: `reference/tod_chicago_ridership_results.csv`, `reference/tod_chicago_ridership_by_station_year.csv`.

## 1. What was built

- **Ridership.** CTA "L" station entries, daily totals (City of Chicago portal `5neh-572f`), 1 January 2009 to 31 December 2019: 574,054 rows, 146 station ids. Entries count people passing a fare gate; transfers inside a station are not counted. The file repeats 618 station-days in 2011 with slightly different counts; each repeated pair was averaged.
- **Station locations.** CTA "List of 'L' Stops" (`8pix-ypme`): 302 platform rows, 144 stations; each station is the average of its platform points.
- **Upzoned land, floor area and homes, per station, within ½ mile (804.7 m) of the station point:**
  - treated eligible acres: eligible parcels the Chicago case adapter labels as upzoned (B or C district with a -3 or -5 bulk suffix in November 2012, within 1,320 ft of a CTA or Metra stop, not already at the new limit and not rezoned otherwise), counted by each parcel's representative point;
  - added floor area: treated acres × 43,560 sq ft × the added floor area ratio (+0.5 on -3 districts, +1.0 on -5 districts);
  - homes permitted 2016–2019: homes in City of Chicago new-construction permits (units read from the work description and staged permits for one building merged, with the case adapter's own functions), by permit location;
  - existing homes: 2010 census block housing units, by block internal point.
- Neighbouring stations' ½-mile circles overlap, so one parcel or permit can count for more than one station.

## 2. Dropped stations and the two groups (written before any comparison)

Written by `scripts/run_chicago_ridership.py --stage lists` on 2026-10-27, before `--stage estimate` was run. Up to this point only data availability (which days each station had entries) and the station measures (upzoned acres, permits, homes) had been tabulated; no station's ridership change had been computed.

The ridership file has 146 station ids for 2009–2019. 46 are dropped, 100 are kept: **20 treated** and **80 comparison** stations.

How "closed" was read (fixed before any comparison): a station with no entries on at least 7 days in a row in 2009–2019, or with no entries in some year. How "rebuilt" was read: a full reconstruction or new station house recorded by the CTA (list in section 6). The Loop: every station inside the Loop, elevated and subway.

### Dropped (46 stations)

| Station | Id | Reason |
|---|---|---|
| 47th-Dan Ryan | 41230 | Red Line South, closed May-October 2013 |
| 63rd-Dan Ryan | 40910 | Red Line South, closed May-October 2013 |
| 69th | 40990 | Red Line South, closed May-October 2013 |
| 79th | 40240 | Red Line South, closed May-October 2013 |
| 87th | 41430 | Red Line South, closed May-October 2013 |
| 95th/Dan Ryan | 40450 | Red Line South, closed May-October 2013 |
| Adams/Wabash | 40680 | Loop station (entries mix transfers) |
| Argyle | 41200 | closed 40 days in a row, 2012-08-25 to 2012-10-03 |
| Berwyn | 40340 | closed 41 days in a row, 2012-10-06 to 2012-11-15 |
| California/Milwaukee | 40570 | closed 40 days in a row, 2014-09-05 to 2014-10-14 |
| Cermak-Chinatown | 41000 | Red Line South, closed May-October 2013 |
| Cermak-McCormick Place | 41690 | opened or rebuilt in the window: Cermak-McCormick Place: opened February 2015 |
| Clark/Division | 40630 | opened or rebuilt in the window: Clark/Division: station rebuilt with new entrances (CTA rehabilitation, 2013-2015) |
| Clark/Lake | 40380 | Loop station (entries mix transfers) |
| Damen/Milwaukee | 40590 | closed 61 days in a row, 2014-10-20 to 2014-12-19 |
| Dempster-Skokie | 40140 | closed 121 days in a row, 2015-07-01 to 2015-10-29 |
| Garfield-Dan Ryan | 41170 | Red Line South, closed May-October 2013 |
| Grand/State | 40330 | opened or rebuilt in the window: Grand (Red): station rebuilt (CTA renovation completed 2012) |
| Granville | 40760 | closed 40 days in a row, 2012-06-02 to 2012-07-11 |
| Jackson/Dearborn | 40070 | Loop station (entries mix transfers) |
| Jackson/State | 40560 | Loop station (entries mix transfers) |
| Jarvis | 41190 | closed 41 days in a row, 2012-11-02 to 2012-12-12 |
| Kimball | 41290 | closed 9 days in a row, 2013-07-13 to 2013-07-21 |
| LaSalle | 41340 | Loop station (entries mix transfers) |
| LaSalle/Van Buren | 40160 | Loop station (entries mix transfers) |
| Lake/State | 41660 | Loop station (entries mix transfers) |
| Lawrence | 40770 | closed 42 days in a row, 2012-10-20 to 2012-11-30 |
| Library | 40850 | Loop station (entries mix transfers) |
| Madison/Wabash | 40640 | Loop station (entries mix transfers); also entries in only 9 of 11 years (opened or closed) |
| Monroe/Dearborn | 40790 | Loop station (entries mix transfers) |
| Monroe/State | 41090 | Loop station (entries mix transfers) |
| Morgan-Lake | 41510 | opened or rebuilt in the window: Morgan: opened May 2012 |
| Morse | 40100 | closed 41 days in a row, 2012-06-30 to 2012-08-09 |
| Oakton-Skokie | 41680 | opened or rebuilt in the window: Oakton-Skokie: opened April 2012 |
| Paulina | 41310 | closed 92 days in a row, 2009-01-01 to 2009-04-02 |
| Quincy/Wells | 40040 | Loop station (entries mix transfers) |
| Randolph/Wabash | 40200 | Loop station (entries mix transfers); also entries in only 10 of 11 years (opened or closed) |
| Sox-35th-Dan Ryan | 40190 | Red Line South, closed May-October 2013 |
| State/Lake | 40260 | Loop station (entries mix transfers) |
| Thorndale | 40880 | closed 41 days in a row, 2012-08-18 to 2012-09-27 |
| Washington/Dearborn | 40370 | Loop station (entries mix transfers) |
| Washington/State | 40500 | Loop station (entries mix transfers); also entries in only 0 of 11 years (opened or closed) |
| Washington/Wabash | 41700 | Loop station (entries mix transfers); also opened or rebuilt in the window: Washington/Wabash: opened August 2017 |
| Washington/Wells | 40730 | Loop station (entries mix transfers) |
| Wellington | 41210 | closed 208 days in a row, 2009-01-01 to 2009-07-27 |
| Wilson | 40540 | opened or rebuilt in the window: Wilson: rebuilt 2014-2018 (CTA Wilson Station Reconstruction, completed February 2018) |

### Treated (20 stations: at least 5 eligible acres upzoned within ½ mile)

| Station | Treated eligible acres | Added floor area (sq ft) | Homes permitted 2016–2019 | Existing homes 2010 |
|---|---|---|---|---|
| 43rd | 10.2 | 221,514 | 155 | 6,097 |
| 47th-South Elevated | 11.9 | 258,777 | 126 | 5,902 |
| 51st | 11.8 | 257,918 | 32 | 4,846 |
| Addison-North Main | 10.5 | 228,483 | 696 | 16,545 |
| Ashland-Lake | 5.2 | 113,623 | 599 | 3,313 |
| Belmont-North Main | 13.9 | 302,166 | 391 | 14,072 |
| Chicago/Milwaukee | 6.6 | 143,649 | 903 | 5,071 |
| Cumberland | 6.2 | 135,742 | 0 | 3,118 |
| Diversey | 11.6 | 251,696 | 282 | 12,662 |
| East 63rd-Cottage Grove | 19.2 | 418,791 | 132 | 6,862 |
| Fullerton | 7.1 | 154,737 | 827 | 9,200 |
| Garfield-South Elevated | 6.9 | 150,685 | 59 | 3,268 |
| Grand/Milwaukee | 6.7 | 146,635 | 1,327 | 7,982 |
| Howard | 13.3 | 288,647 | 44 | 9,479 |
| Indiana | 9.8 | 214,413 | 93 | 5,097 |
| King Drive | 16.6 | 362,421 | 1 | 5,698 |
| Logan Square | 6.3 | 137,405 | 108 | 9,471 |
| Sedgwick | 5.9 | 128,968 | 861 | 14,109 |
| Sheridan | 8.7 | 188,762 | 460 | 16,304 |
| Southport | 5.9 | 128,245 | 578 | 10,548 |

### Comparison (80 stations)

| Station | Treated eligible acres | Homes permitted 2016–2019 | Existing homes 2010 |
|---|---|---|---|
| 18th | 0.2 | 156 | 5,500 |
| 35-Bronzeville-IIT | 4.1 | 41 | 3,146 |
| 35th/Archer | 0.1 | 97 | 3,341 |
| 54th/Cermak | 0.0 | 0 | 4,468 |
| Addison-Brown | 2.3 | 337 | 8,589 |
| Addison-O'Hare | 0.0 | 58 | 4,775 |
| Armitage | 0.5 | 155 | 6,630 |
| Ashland-Orange | 0.0 | 137 | 2,298 |
| Ashland/63rd | 0.0 | 0 | 3,845 |
| Austin-Forest Park | 0.0 | 0 | 3,773 |
| Austin-Lake | 0.6 | 6 | 6,196 |
| Belmont-O'Hare | 2.8 | 193 | 6,841 |
| Bryn Mawr | 2.4 | 23 | 16,860 |
| California-Cermak | 1.2 | 2 | 4,643 |
| California-Lake | 0.3 | 27 | 2,882 |
| Central Park | 0.0 | 0 | 6,178 |
| Central-Evanston | 0.0 | 0 | 2,266 |
| Central-Lake | 1.0 | 6 | 6,698 |
| Chicago/Franklin | 2.3 | 5,413 | 20,295 |
| Chicago/State | 2.3 | 2,654 | 28,833 |
| Cicero-Cermak | 0.0 | 0 | 3,552 |
| Cicero-Forest Park | 0.2 | 1 | 2,952 |
| Cicero-Lake | 0.0 | 1 | 3,419 |
| Clinton-Forest Park | 0.0 | 1,587 | 6,905 |
| Clinton-Lake | 1.3 | 3,251 | 9,797 |
| Conservatory | 0.7 | 20 | 4,004 |
| Damen-Brown | 2.7 | 207 | 9,094 |
| Damen-Cermak | 0.3 | 103 | 6,970 |
| Davis | 0.0 | 0 | 6,879 |
| Dempster | 0.0 | 0 | 6,065 |
| Division/Milwaukee | 4.9 | 466 | 9,278 |
| Forest Park | 0.0 | 0 | 2,666 |
| Foster | 0.0 | 0 | 5,039 |
| Francisco | 3.9 | 102 | 8,520 |
| Halsted-Orange | 0.1 | 77 | 2,973 |
| Halsted/63rd | 4.5 | 16 | 4,020 |
| Harlem-Forest Park | 0.0 | 0 | 3,817 |
| Harlem-Lake | 0.0 | 0 | 7,645 |
| Harlem-O'Hare | 0.0 | 3 | 2,387 |
| Harrison | 0.0 | 2,847 | 9,860 |
| Irving Park-Brown | 0.8 | 175 | 8,135 |
| Irving Park-O'Hare | 0.2 | 57 | 5,375 |
| Jefferson Park | 0.0 | 85 | 4,728 |
| Kedzie-Brown | 3.6 | 108 | 9,100 |
| Kedzie-Cermak | 0.0 | 0 | 6,096 |
| Kedzie-Homan-Forest Park | 2.1 | 10 | 3,835 |
| Kedzie-Lake | 3.1 | 14 | 3,830 |
| Kedzie-Midway | 0.0 | 33 | 2,434 |
| Kostner | 0.0 | 0 | 2,882 |
| Laramie | 1.3 | 1 | 5,442 |
| Linden | 0.0 | 0 | 1,399 |
| Loyola | 2.2 | 203 | 11,969 |
| Main | 0.0 | 0 | 6,475 |
| Medical Center | 1.2 | 109 | 2,956 |
| Merchandise Mart | 0.0 | 2,820 | 14,074 |
| Midway Airport | 0.0 | 1 | 2,626 |
| Montrose-Brown | 1.8 | 153 | 8,495 |
| Montrose-O'Hare | 1.1 | 27 | 3,334 |
| North/Clybourn | 2.7 | 360 | 5,311 |
| Noyes | 0.0 | 0 | 3,168 |
| O'Hare Airport | 0.0 | 0 | 0 |
| Oak Park-Forest Park | 0.0 | 0 | 3,500 |
| Oak Park-Lake | 0.0 | 0 | 5,930 |
| Polk | 0.7 | 29 | 3,155 |
| Pulaski-Cermak | 0.0 | 0 | 5,189 |
| Pulaski-Forest Park | 0.8 | 1 | 5,010 |
| Pulaski-Lake | 0.5 | 6 | 3,044 |
| Pulaski-Orange | 3.6 | 1 | 3,259 |
| Racine | 1.2 | 546 | 6,802 |
| Ridgeland | 0.0 | 0 | 4,405 |
| Rockwell | 4.2 | 224 | 7,156 |
| Roosevelt | 0.0 | 4,580 | 13,795 |
| Rosemont | 0.0 | 0 | 1 |
| South Boulevard | 0.0 | 0 | 7,083 |
| UIC-Halsted | 0.7 | 1,936 | 6,333 |
| Western-Brown | 3.8 | 249 | 8,233 |
| Western-Cermak | 1.3 | 43 | 5,499 |
| Western-Forest Park | 2.0 | 188 | 4,155 |
| Western-Orange | 0.0 | 0 | 3,440 |
| Western/Milwaukee | 2.8 | 973 | 9,401 |

<!-- lists end -->
## 3. Main result

Computed by `scripts/run_chicago_ridership.py --stage estimate` after section 2 was written. Every number is in `reference/tod_chicago_ridership_results.csv`. Intervals are 90% intervals from resampling stations (2,000 draws, seed 20261027).

- **Average weekday entries per station** (mean over stations of each station's yearly average):
  - 20 treated stations: 4,274 entries per weekday in 2009–2014, 4,223 in 2016–2019. The mean change in log entries was −4.8%.
  - 80 comparison stations: 3,039 entries per weekday in 2009–2014, 3,121 in 2016–2019. The mean change in log entries was +0.4%.
- **Difference in differences (main):** weekday entries at treated stations changed **5.1% less** than at comparison stations (−5.1%; 90% interval −10.7% to +0.7%). In entries: 133 fewer entries per weekday per station (90% interval 319 fewer to 48 more).
- The interval includes zero. The test finds no rise in ridership at stations whose surroundings were upzoned, relative to other stations; the point estimate is a small relative fall.

**Year by year** (gap in mean log weekday entries, treated minus comparison, relative to 2014, as a percentage): 2009 +2.0%, 2010 +1.1%, 2011 +0.9%, 2012 +0.5%, **2013 +15.3%**, 2014 0, 2015 −0.2%, 2016 −0.9%, 2017 −1.1%, 2018 −2.4%, 2019 −4.2%. Two things follow:

- Treated stations were already losing ground slowly before the ordinances (about 2 percentage points from 2009 to 2014), and the drift continued afterwards.
- 2013 is an outlier. During the Red Line South closure (May–October 2013) the CTA sent riders to Green Line South stations, 7 of which are treated; Garfield (Green) averaged 7,030 weekday entries in 2013 against 1,347 in 2012. 2013 sits in the plan's before years, which pulls the main estimate down. The plan did not foresee this; it is shown by the unplanned check in section 5.

## 4. Dose: more upzoned land, more homes permitted

Each station's change in mean log weekday entries (2016–2019 against 2009–2014), regressed on one measure at a time, over all 100 kept stations (treated and comparison).

- **Treated eligible acres within ½ mile:** each additional 10 acres went with a **8.3% smaller** change in weekday entries (90% interval 11.9% to 3.3% smaller). Kept stations range from 0 to 19.2 treated acres.
- **Homes permitted 2016–2019 per 1,000 existing homes within ½ mile** (99 stations; O'Hare has no homes): each additional 10 permitted homes per 1,000 existing homes went with a **0.43% larger** change (90% interval +0.25% to +0.69%). The median kept station had 11 permitted homes per 1,000 existing homes; a quarter had more than 30; the most had 332.

The two point in opposite directions, and neither isolates the ordinances:

- The upzoned land is concentrated around the Green Line South stations (Cottage Grove, King Drive, 47th, 51st, 43rd, Indiana, Garfield), which lost riders over the decade like much of the South Side, and which gained the 2013 diversion in their before years. Those 7 stations' mean change in log entries was −18.7%; the other 13 treated stations' was +3.7%, against +0.4% for comparison stations (description, not part of the plan, no interval).
- Homes permitted are highest near downtown (Chicago/Franklin, Roosevelt, Clinton, Merchandise Mart, Harrison, UIC-Halsted), and most of those stations are comparison stations with little upzoned land. The positive slope says stations with more new homes kept more riders; it does not say the ordinances caused those homes.

## 5. Sensitivities

Fixed in the plan:

| Case | Treated / comparison stations | Difference in differences (90% interval) | Per 10 treated acres | Per 10 permitted homes per 1,000 existing |
|---|---|---|---|---|
| Main: weekday entries | 20 / 80 | −5.1% (−10.7% to +0.7%) | −8.3% (−11.9% to −3.3%) | +0.43% (+0.25% to +0.69%) |
| Saturday plus Sunday or holiday entries | 20 / 80 | −7.5% (−13.3% to −1.5%) | −10.9% (−14.2% to −7.1%) | +0.17% (−0.03% to +0.42%) |
| Leaving out the 5 busiest stations (Chicago/State, Fullerton, Belmont, Roosevelt, O'Hare) | 18 / 77 | −5.1% (−11.1% to +1.3%) | −8.6% (−12.3% to −3.2%) | +0.51% (+0.31% to +0.82%) |
| 2013 as the change year (before 2009–2012, after 2014–2019) | 20 / 80 | −2.6% (−6.6% to +1.9%) | −4.7% (−7.6% to −0.8%) | +0.34% (+0.15% to +0.63%) |

In entries per day per station: weekend −255 (−439 to −93); 5 busiest left out −70 (−264 to +112); 2013 change year −47 (−203 to +115).

Not in the plan (added after the main results were seen; plan section 7, items 10 and 11):

| Check | Treated / comparison stations | Difference in differences (90% interval) | Per 10 treated acres | Per 10 permitted homes per 1,000 existing |
|---|---|---|---|---|
| 17 stations outside Chicago left out (Evanston, Skokie, Wilmette, Oak Park, Forest Park, Cicero, Rosemont) | 20 / 63 | −4.8% (−10.5% to +1.3%) | −8.3% (−12.1% to −3.2%) | +0.50% (+0.30% to +0.82%) |
| 2013 left out of the before years (Red Line South diversion) | 20 / 80 | −3.0% (−7.7% to +1.9%) | −6.1% (−9.4% to −1.5%) | +0.42% (+0.24% to +0.68%) |

## 6. Reading the result, and limits

**Conclusion.** Chicago's 2013 and 2015 transit-area upzoning is not followed by a measurable rise in "L" ridership at the stations whose surroundings were upzoned. Weekday entries there changed between about 11% less and about 1% more than at other stations (main estimate −5.1%). Every specification's point estimate is negative, and only the weekend one excludes zero. Stations with more new homes per existing home did keep more riders, but that growth was mostly near downtown and not on the upzoned land. This is context for legislators: in Chicago, the upzoning by itself did not show up in station ridership within four years. It does not change any housing number in the model.

**Limits.**

- Small doses. The ordinances added +0.5 or +1.0 floor area ratio on 5 to 19 acres per treated station. At about 0.5 transit trips per home per weekday, the 132 homes permitted near Cottage Grove would add about 66 entries per weekday against about 1,100 (research/RIDERSHIP_DATA.md).
- The treated group is not a random draw: 7 of 20 treated stations are on the Green Line South, where ridership fell for reasons unrelated to zoning, and treated stations were already drifting down before 2013.
- 2013 diversion (section 3) pulls the main estimate toward a fall; leaving 2013 out gives −3.0% (−7.7% to +1.9%).
- 46 of 146 stations are dropped, including 7 Red Line North stations closed about 40 days each in 2012 and the 9 Red Line South stations; some of these had upzoned land (for example Jarvis, Morse, Lawrence, Argyle, Wilson, Cermak-Chinatown).
- Homes permitted are read from permit work descriptions (the case adapter's parser) and count only City of Chicago permits, so stations outside or at the edge of the city are under-counted.
- Entries count gate entries only; riders who transfer inside a station or board by bus are not counted.

**Sources for the rebuilt stations** (section 2): Wilson — CTA Wilson Station Reconstruction, completed February 2018 ([Wikipedia summary](https://en.wikipedia.org/wiki/Wilson_station_(CTA)); [Railway Track & Structures](https://www.rtands.com/?p=10344)); Clark/Division — CTA rehabilitation with new entrances ([Progressive Railroading](https://progressiverailroading.com/passenger_rail/news/CTA-finishes-50-million-rehab-of-Red-Line-station--45958)); Grand (Red) — CTA renovation ([CBS Chicago](https://www.cbsnews.com/chicago/news/newly-renovated-grand-avenue-red-line-stop-unveiled/)). Openings (Morgan, Oakton-Skokie, Cermak-McCormick Place, Washington/Wabash) are confirmed by the first month with entries in the ridership file.

**Data terms.** CTA ridership and stops: City of Chicago data portal terms of use (free use, provided as is, no warranty); attribution Chicago Transit Authority. Hashes and access times: `data/raw/cta_ridership/manifest.json`.
