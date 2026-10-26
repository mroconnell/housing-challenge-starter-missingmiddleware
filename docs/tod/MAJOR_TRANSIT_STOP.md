# What counts as a "major transit stop": data, method and how many homes each definition covers

Written 2026-10-26 by the TOD conductor. Status: first look, for the Gate 1 decision. The numbers come from a scratch run on 2026-10-26; the automated, committed pipeline is Gate 2 work.

Owner decisions so far:
- **AQ-044:** show the definitions as a ladder from narrowest to widest, with 15-minute service as the main case, and focus on city-specific studies of the Milwaukee and Madison areas.
- **AQ-045:** use one consistent stop source for every city, the federal National Transit Map. Do not use Madison Metro's own schedule file while its licence is an open office-hours question (questions 24 and 25 in [ASSUMPTIONS_AND_QUESTIONS.md](../ASSUMPTIONS_AND_QUESTIONS.md)).

Background research: [research/WI_TRANSIT_DATA.md](research/WI_TRANSIT_DATA.md) (data and licences), [research/PRODUCTION_EVIDENCE.md](research/PRODUCTION_EVIDENCE.md) (distance), [research/STATE_LAWS_WEST.md](research/STATE_LAWS_WEST.md) and [research/STATE_LAWS_EAST.md](research/STATE_LAWS_EAST.md) (how other states define stops).

## 1. Method

**Stops and route lines come from the federal National Transit Map.** The U.S. DOT Bureau of Transportation Statistics compiles every agency's published stops and route shapes into the National Transit Map (compiled 23 September 2026). It is fetched by script from the BTS ArcGIS service, and the stops layer is labelled CC BY 3.0. The map covers 27 Wisconsin agencies, with 13,052 boarding stops and 1,063 route shapes, including Green Bay and Milwaukee. Amtrak's 8 Wisconsin train stations come from the public-domain BTS Amtrak Stations layer.

**How often buses come is tested route by route.** The National Transit Map has no timetables. So a route counts as frequent when it runs at least 4 trips an hour (15-minute service), or 3 an hour (20-minute service), in one direction, in both the 7:00 and the 8:00 weekday hours. A stop qualifies when it lies within 30 metres of a qualifying route's line on the map. Each route's frequency comes from a source whose terms allow our use:
- the agency's own schedule file, for 16 agencies. Milwaukee's is a May 2025 copy, because its server timed out;
- for Madison, the route descriptions Madison publishes, which the National Transit Map carries. Routes A, B, C, D and 80 say "at least every 15 minutes" on weekday daytimes; every other Madison route runs every 30 minutes or less often. Madison's schedule file is not used.

**Rail and rapid transit** means every rail route in the map (Amtrak, the Hop streetcar, the Kenosha streetcar), plus Milwaukee's CONNECT 1 and Madison's Rapid Route A.

**Homes** are 2020 census housing units in blocks whose centre point lies within the distance. Wisconsin had 2,727,726.

## 2. How many homes each definition covers

| Definition (narrowest to widest) | Stops (count) | Homes within ½ mile (count, share of the state's 2,727,726) |
| --- | --- | --- |
| (a) Rail and rapid transit only | 274 | 94,504 (3.5%) |
| (b) (a), plus stops on bus routes every 15 minutes | 2,785 | 407,832 (15.0%) |
| (c) (a), plus stops on bus routes every 20 minutes | 3,245 | 455,821 (16.7%) |
| (e) Any stop (for context; not "major" transit) | 13,052 | 1,055,136 (38.7%) |

With the distances most state laws use (½ mile from rail and rapid transit, ¼ mile from frequent bus):

| Rule | Homes (count, share of the state's 2,727,726) |
| --- | --- |
| **Main case:** rail and rapid within ½ mile, 15-minute bus within ¼ mile | **318,394 (11.7%)** |
| High case: rail and rapid within ½ mile, 20-minute bus within ¼ mile | 356,373 (13.1%) |

California's definition (stops where two 15-minute routes meet) needs stop-level timetables. It cannot be measured from the National Transit Map, so it drops off the ladder.

## 3. How much would city-specific studies cover

| Area studied | Main case (318,394 homes) | (b) 15-minute, all ½ mile (407,832) | (c) 20-minute, all ½ mile (455,821) |
| --- | --- | --- | --- |
| Milwaukee city | 175,737 (55.2%) | 214,703 (52.6%) | 238,796 (52.4%) |
| Madison city | 80,595 (25.3%) | 94,625 (23.2%) | 94,625 (20.8%) |
| Milwaukee city and Madison city | 80.5% | 75.8% | 73.2% |
| Milwaukee County and Dane County | 97.2% | 97.6% | 96.1% |

Under the 15-minute and 20-minute definitions, almost everything is in Milwaukee County and Dane County. The route-level test finds no 15-minute route outside Milwaukee and Madison apart from two Eau Claire routes. The rest of the state matters only under the rail and rapid definition, through Amtrak stations and the Kenosha streetcar, and under "any stop".

## 4. Compared with the first run, which used Madison's file

The first run, earlier on 26 October, tested each stop's own timetable and used Madison's file. That run is superseded; its figures are no longer used.

- **Main-case total:** 330,804 homes then, 318,394 now (12,410 fewer, or 3.8%).
- **Milwaukee city:** 177,963 then, 175,737 now.
- **Madison city:** 67,520 then, 80,595 now (19% more).

The route-level test changes the count in both directions:
- **It drops overlaps.** It misses stretches where two 30-minute routes share a street to give 15-minute service. This mostly drops stops in Milwaukee's inner suburbs, La Crosse, Oshkosh and Racine.
- **It adds local stops.** It counts any stop on the line of a frequent route, even one the frequent route skips. This is why Madison rises: its 15-minute routes A to D share streets with many local stops.

A stop-level test would fix both effects, but it needs each agency's stop-level timetable. For Madison, that is the file we are not using for now.

## 5. Recommendation

- **Main case:** rail and rapid transit within ½ mile, plus 15-minute bus routes within ¼ mile. That is 318,394 homes.
- **Ladder, narrowest to widest:**
  1. (a) rail and rapid only, 94,504 homes within ½ mile;
  2. the main case;
  3. the 20-minute high case, 356,373 homes;
  4. the ½-mile sensitivity on all frequent stops.
- **Study design (AQ-044):** two metro studies, Milwaukee County and Dane County, which cover 96% to 98% of the homes under every frequent-service definition. A simple statewide rule handles the rest.

## 6. Caveats and open items

- **Office-hours question 25:** does Madison's licence follow its data into the National Transit Map? The map's agency table lists every Wisconsin agency's licence as "Public Domain", while its stops layer says CC BY 3.0. Both allow our use.
- **Milwaukee's frequencies** come from a May 2025 schedule copy, matched by route number to the September 2026 map. Gate 2 retries the official file.
- **Green Bay** has no current schedule file, so no Green Bay route counts as frequent. Its 2018 file had about 10 frequent stops.
- **Not yet in the extract:** Superior (Duluth Transit) and Metra's Kenosha station.
- **Coverage, not added homes:** "homes near stops" is the area a law would cover, not the number of homes it would add. That depends on land that can redevelop and on whether mid-rise housing pays for itself in each market, which is the Gate 3 question.
