# What counts as a "major transit stop": a first look at data coverage and yield

Written 2026-10-26 by the TOD conductor, in answer to the owner's request: choose the definition that lets us use the most and best statewide datasets, and find the list of stops that gives the biggest defensible yield. Status: first look, for the Gate 1 decision. The numbers come from a scratch run on transit schedules downloaded on 2026-10-26; the automated, committed version is Gate 2 work.

Data inventory: [research/WI_TRANSIT_DATA.md](research/WI_TRANSIT_DATA.md). Evidence on distance: [research/PRODUCTION_EVIDENCE.md](research/PRODUCTION_EVIDENCE.md). How other states define stops: [research/STATE_LAWS_WEST.md](research/STATE_LAWS_WEST.md) and [research/STATE_LAWS_EAST.md](research/STATE_LAWS_EAST.md).

## 1. Which data can measure a definition statewide

Transit schedules in the standard GTFS format, published by the transit agencies themselves, are the best statewide source. Twenty-three of Wisconsin's 28 fixed-route transit agencies publish one. Today a script could download 21 of them. The two exceptions:

- Milwaukee's server timed out, so this run uses a May 2025 copy from the Mobility Database.
- Green Bay's site blocks scripted downloads.

Schedules are the only statewide source that shows how often buses come at each stop today. The two national alternatives are weaker:

- The federal National Transit Map has stop locations for every agency but no frequencies.
- The EPA Smart Location Database measures frequency only for whole block groups. It uses 2020 service and misses 8 Wisconsin agencies, including Madison's bus rapid transit, which opened in 2024.

So the definitions below all use the agencies' own schedules. The Smart Location Database is kept as an independent cross-check, which is also the "top-down" route a state without schedule data could use.

## 2. Candidate definitions and what they cover

Homes are 2020 census housing units in blocks whose centre point lies within the distance of a qualifying stop. Wisconsin had 2,727,726 housing units in the 2020 census. Frequency is weekday scheduled departures in one direction, in each of the hours 7:00 to 7:59 and 8:00 to 8:59.

| Definition | Qualifying stops (count) | Homes within ¼ mile (count, share of the state's 2,727,726) | Homes within ½ mile (count, share) |
| --- | --- | --- | --- |
| (a) Rail and bus rapid transit stations only (Amtrak, the Hop and Kenosha streetcars, Milwaukee CONNECT 1, Madison Rapid Route A) | 169 | 51,077 (1.9%) | 94,237 (3.5%) |
| (d) California's legal definition: (a), plus stops where two bus routes, each every 15 minutes at both peaks, meet | 418 | 98,845 (3.6%) | 191,288 (7.0%) |
| (b) (a), plus bus stops served every 15 minutes or better (4 or more departures an hour) | 2,299 | 313,139 (11.5%) | 469,352 (17.2%) |
| (c) (a), plus bus stops served every 20 minutes or better (3 or more departures an hour) | 2,931 | 369,319 (13.5%) | 535,946 (19.6%) |
| (e) Any stop with weekday service (not "major" transit) | 11,691 | 831,057 (30.5%) | 1,003,823 (36.8%) |

Two hybrid rules, using the distances most state laws use (½ mile for rail and rapid transit, ¼ mile for bus):

| Hybrid | Homes (count, share of the state's 2,727,726) | Land (acres) |
| --- | --- | --- |
| Rail and bus rapid transit within ½ mile, plus 15-minute bus within ¼ mile | 330,804 (12.1%) | 73,170 |
| Rail and bus rapid transit within ½ mile, plus 20-minute bus within ¼ mile | 385,488 (14.1%) | 87,963 |

Cross-check: the EPA Smart Location Database puts 579,836 of Wisconsin's 2,681,232 housing units in 2018 (22%) in block groups with 4 or more transit trips an hour. That is close to definition (b) at ½ mile, which covers 17.2%. The block-group measure is coarser, and it counts both directions and every route within ¼ mile, so it should come out higher.

Where the homes are: under definition (b), Milwaukee County Transit System stops account for 313,620 homes within ½ mile and Madison Metro for 92,862, out of 469,352. Every other agency adds less than 20,000 each. So the scenario is mostly about Milwaukee and Madison under every definition except (e).

## 3. Recommendation

- **Main definition: (b), 15-minute bus plus rail and bus rapid transit.** Every agency with frequent service except Green Bay can measure it from its own schedule. It matches the frequency test most state laws use, including California and Colorado. Of the definitions that are defensibly "major", it has the second-largest yield.
- **High case: (c), 20-minute service.** This is the biggest yield that is still defensible as "major" transit. It covers 66,594 more homes within ½ mile than (b) (535,946 against 469,352), about 14% more. It uses the same data and the same script.
- **Distance:**
  - ½ mile from rail and bus rapid transit stations, and ¼ mile from frequent bus stops, as the main case;
  - ½ mile from all qualifying stops as a sensitivity case.

  No study found measures how the building response falls off with distance. The ¼ and ½ mile split is the convention in state laws and ridership research, so the distance becomes a sensitivity, not a fitted value.
- **Not recommended:**
  - (a) is too narrow: Wisconsin has only 4 rapid or rail lines.
  - (d) is a California-specific transfer test.
  - (e) includes hourly buses, which no state treats as major transit.

## 4. Caveats and open items

- **Licence decision for the owner:** Madison Metro's data licence limits use to "assisting mass transit riders or in furtherance of promoting public transportation". It also claims ownership of derived data. Options:
  - email Metro to confirm the use is allowed (recommended);
  - read the clause as covering a study of building homes near transit;
  - use the National Transit Map stop locations with Madison's published route frequencies instead.
- **Milwaukee:** the official feed URL timed out. The fallback is the Mobility Database copy (May 2025) or the National Transit Map load from September 2026. Gate 2 will retry the official source first.
- Green Bay and Superior are not yet counted. Green Bay's 2018 feed had 10 frequent stops, and Superior is served by Duluth Transit.
- A pair of stops across the street counts twice in the stop counts; the home counts are not affected.
- "Homes near stops" is the area a law would cover, not the number of homes it would add. How many more homes get permitted depends on land that can redevelop and on whether mid-rise housing pays for itself in each market. That is the Gate 3 question.

## 5. How much would city-specific studies cover? (owner question, 2026-10-26)

The same scratch run, with each census block assigned to its city, village or town (2024 county subdivisions). Shares are of homes (2020 census housing units) near a qualifying stop.

| Area studied | Main rule: rail and rapid ½ mile, 15-minute bus ¼ mile (330,804 homes) | 15-minute, all stops ½ mile (469,352 homes) | 20-minute high case, ½ mile (535,946 homes) |
| --- | --- | --- | --- |
| Milwaukee city | 177,963 (53.8%) | 224,870 (47.9%) | 241,840 (45.1%) |
| Milwaukee city and Madison city | 245,483 (74.2%) | 308,810 (65.8%) | 335,255 (62.6%) |
| The 10 largest municipalities | 89.6% | 84.0% | 81.7% |
| Milwaukee County and Dane County (all municipalities, the service areas of the two big transit systems) | 304,215 (92.0%) | 405,962 (86.5%) | 448,341 (83.7%) |
| Number of municipalities with any covered homes | 54 | 59 | 69 |

What this means:
- Two city studies, Milwaukee and Madison, cover about two-thirds to three-quarters of the homes the law would reach.
- Two county-wide studies, Milwaukee County and Dane County, cover 84% to 92%. The extra comes mostly from inner suburbs on Milwaukee's bus network (West Allis, Wauwatosa, Shorewood, South Milwaukee, Cudahy, Greenfield, Whitefish Bay) and from Fitchburg next to Madison.
- The remaining 8% to 16% is spread over about 50 smaller cities, led by La Crosse, Eau Claire, Oshkosh, Racine, Kenosha and Janesville, with no single place above 2.2%. A simpler statewide rule could cover them.
- Homes covered is not the same as homes added. If the response depends on market strength, as the evidence suggests, the added homes will be more concentrated in Madison than these shares show.
- Census building permits under-count Milwaukee city apartments (see [HOUSING_BASELINE.md](../shared/HOUSING_BASELINE.md)), so a Milwaukee study would need the city's own permit and property records, which are already in the repo.
