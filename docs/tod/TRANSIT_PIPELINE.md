# TOD transit pipeline: major transit stops and homes near them

Written 2026-10-26 (TOD Gate 2, work package 1). This pipeline turns the scratch analysis behind [MAJOR_TRANSIT_STOP.md](MAJOR_TRANSIT_STOP.md) into scripts and tests. The owner decisions it follows are in AQ-044, AQ-045 and AQ-047 in [ASSUMPTIONS_AND_QUESTIONS.md](../ASSUMPTIONS_AND_QUESTIONS.md).

## 1. How to run

```bash
uv run --all-extras python scripts/fetch_tod_transit.py   # needs network; about 1 to 3 minutes
uv run --all-extras python scripts/build_tod_stops.py     # offline; about 10 seconds
bash scripts/test.sh                                      # offline tests, including tests/test_tod_transit.py
```

- `fetch_tod_transit.py --only ntm` or `--only gtfs` fetches one part. `--feed 50001` refetches one GTFS feed.
- The build also needs two Census files that are already in `data/raw/`:
  - 2020 blocks: `census_tiger_2020_tabblock/tl_2020_55_tabblock20.zip`.
  - Municipal boundaries: `census_cb_2024/cb_2024_55_cousub_500k.zip`.
- Run on the same raw files, the build gives byte-identical outputs.

## 2. Method

1. **Stops and route lines** come from the BTS National Transit Map (NTM): the agencies, stops and routes layers, for every agency the NTM lists in Wisconsin (27 agencies, compiled 2026-09-23).
   - Only boarding points count (`location_type` 0 or blank): 13,044 stops.
   - Amtrak is excluded (AQ-047 item 10). No Amtrak layer is fetched, and any agency named Amtrak is dropped.
2. **Route frequency.** A route is frequent at N trips an hour when, in one direction, at least N trips start in the 7:00 hour and at least N start in the 8:00 hour.
   - The day tested is the Tuesday, Wednesday or Thursday with the most scheduled trips in the 120 days from the download date. If the feed has already expired, the 120 days start at the feed's first day.
   - A trip's start is the time at its lowest `stop_sequence`. The two directions are never added together. GTFS routes are matched to NTM routes by short name (long name when the short name is blank).
   - N = 4 (15-minute service) is the main case; N = 3 (20-minute service) is the high case.
   - Sources by agency:
     - 16 agencies: their official GTFS file.
     - Madison: the route descriptions in the NTM routes layer (`route_desc`), read by `madison_trips_per_hour`. Routes A, B, C, D and 80 come out at 4 trips an hour; all others at 2 or fewer.
     - Green Bay, Manitowoc and the small rural systems: no route counts as frequent (section 5).
3. **A stop qualifies** when it lies within 30 m of a qualifying route line of the same agency.
4. **Rail and rapid transit** means:
   - NTM rail route types;
   - The Hop (every route of NTD id 55312, which is coded as bus);
   - the Kenosha streetcar (`SC`);
   - MCTS CONNECT 1 (`CN1`);
   - Madison Rapid Route A.
5. **Homes** are 2020 census block housing units (`HOUSING20`). A block counts when its internal point lies within the distance of a qualifying stop. Distances are exact point-to-point distances in Wisconsin Transverse Mercator (EPSG:3071).
6. **Municipality.** Each block goes to the 2024 county subdivision that contains its internal point. The 2024 boundaries are shoreline-clipped, so a few lakeside points fall outside every polygon; those blocks go to the nearest county subdivision. The same rule assigns stops.

Definitions (columns of the outputs):

| Key | Rule |
| --- | --- |
| `rapid_half` | (a) rail and rapid stops, ½ mile |
| `main` | rail and rapid ½ mile, plus 15-minute bus stops ¼ mile (main case) |
| `high` | rail and rapid ½ mile, plus 20-minute bus stops ¼ mile (high case) |
| `b_half` | (b) rail and rapid plus 15-minute bus, all ½ mile (sensitivity) |
| `c_half` | (c) rail and rapid plus 20-minute bus, all ½ mile (sensitivity) |
| `any_half` | (e) any boarding stop, ½ mile (context only, not "major" transit) |
| `main_35k` | check: the main case, with rail and rapid getting ½ mile only in cities of 35,000+ people (2020 census) and ¼ mile elsewhere |

## 3. Output files

| File | One row per | Contents |
| --- | --- | --- |
| `reference/tod_stops.csv` | stop that qualifies under (c), the widest major-stop definition (3,237 stops) | `ntd_id`, `agency` (NTM agency name), `stop_id` (NTM/GTFS id), `lat` and `lon` (WGS84, 5 decimals), flags `flag_a_rapid`, `flag_b_15min` and `flag_c_20min` (1 = qualifies), and `frequency_source` (where the agency's frequency came from, with the service day and feed validity) |
| `reference/tod_near_stop_homes_by_muni.csv` | Wisconsin county subdivision (1,912 rows; a city split across counties has one row per county) | `area_id` (`muni:<10-digit GEOID>`), `name`, `county`, `homes_2020`; then `homes_near_<key>` and `share_near_<key>` (a share of the row's own 2020 homes) for each key in the table above |
| `reference/tod_definition_summary.csv` | definition key | description, radii (miles), bus threshold (trips an hour), qualifying stops, homes near stops, state total homes (2,727,726), share of the state's homes, homes in Milwaukee city and Madison city, and the shares of the definition's homes in those two cities and in Milwaukee and Dane counties |
| `data/raw/tod_transit/manifest.json` (git-ignored) | downloaded file | URL, access time (UTC), bytes, SHA-256, HTTP Last-Modified, licence or terms, and whether the official or the fallback URL was used. It also lists failed attempts and the sources deliberately not downloaded |

## 4. Results (run of 2026-10-26)

| Definition | Stops (count) | Homes near stops (count; share of the state's 2,727,726 homes) | Share of those homes in Milwaukee County and Dane County |
| --- | --- | --- | --- |
| (a) rail and rapid, ½ mile | 266 | 89,528 (3.3%) | 95.8% |
| **Main case** | 2,777 | **313,564 (11.5%)** | 98.7% |
| High case | 3,237 | 351,606 (12.9%) | 97.5% |
| (b) all ½ mile | 2,777 | 403,304 (14.8%) | 98.8% |
| (c) all ½ mile | 3,237 | 451,457 (16.6%) | 97.1% |
| (e) any stop, ½ mile | 13,044 | 1,052,700 (38.6%) | 51.9% |

**Reconciliation with the scratch run** (AQ-047 item 10: main case 313,357 homes):
- Stop counts are identical for every definition.
- Home counts are 0.07% to 0.8% higher: main case +207 (0.07%), (a) +673 (0.76%), (b) +330 (0.08%).
- The cause is the distance method. The scratch run drew each circle as a 32-sided polygon, which sits slightly inside the true circle. This pipeline measures exact distances.
- Rerunning (a) with the scratch's polygons on today's stops gives exactly 88,855 homes, the scratch figure.
- The input data did not change: the NTM compilation date and the MCTS fallback copy are the same.

**The 35,000-person rule changes nothing.**
- 3 of the 266 rail and rapid stops lie outside cities of 35,000+ people: Madison Route A stops in Shorewood Hills village (2,257 people in 2020). Sun Prairie city had 35,953 people in 2020, so its stops keep ½ mile.
- These 3 stops are also on a 15-minute route (Route A is one). The homes in their ¼-to-½-mile ring are already within ½ mile of Route A stops in Madison.
- So `main_35k` equals `main`: 313,564 homes.

**Eau Claire.** Routes 9 and 19 run 3 trips an hour, so they count in the high case and in (c), not in the main case. In the main case, every frequent bus route is in Milwaukee County or Madison.

## 5. Known gaps

- **MCTS frequency comes from a copy dated May 2025.** The official URL (kamino.mcts.org) timed out again on 2026-10-26, so the fetch used the Mobility Database copy (mdb-2127). That copy was last updated 2025-05-08 and is valid 2025-03-09 to 2025-08-23. Its routes are matched by route number to the September 2026 NTM lines. Rerun the fetch when the official URL answers; the manifest records which source was used.
- **Green Bay** has no current feed that scripts can fetch: the City site returns HTTP 403, and the file name changes with each release. No Green Bay route counts as frequent. Its stops are in the NTM, so they count in (e). Its 2018 feed had about 10 frequent stops.
- **Manitowoc's** feed gives implausible frequencies ([WI_TRANSIT_DATA.md](research/WI_TRANSIT_DATA.md) section 4), so it is not used. The same goes for the small systems with no frequent service: Platteville, Rusk County, Menominee, Bad River, Bay Area Rural, Dunn County, Oneida-Vilas and Sawyer County. None of their routes counts as frequent.
- **Madison's frequency** comes from route descriptions, not timetables. So it is a statement of the minimum service standard, not a count of trips.
- **The route-level test drops and adds stops.** It misses streets where two less-frequent routes overlap to give 15-minute service. It also counts every stop on a frequent route's line, including stops that route skips. Both effects are described in [MAJOR_TRANSIT_STOP.md](MAJOR_TRANSIT_STOP.md) section 4.
- **Coverage gaps:**
  - Superior (Duluth Transit) is not in the NTM extract for Wisconsin agencies.
  - Metra's Kenosha station is not counted.
  - Five NTM stops whose `location_type` reads "Null" are dropped, as in the scratch run.
- **Homes near stops is coverage, not added homes.** It counts existing 2020 homes in the areas a law would cover.
- **Feed validity.** Eau Claire, Beloit and Stevens Point publish feeds valid one month at a time, and Janesville's runs to 2026-12-10. A rerun after those dates picks up the next file.

## 6. Licences and notices

- **BTS National Transit Map** (stops, routes, agencies): the stops layer states Creative Commons Attribution 3.0 United States (CC BY 3.0 US). The agency table lists every Wisconsin agency's data as Public Domain. Attribution: "Source: U.S. Department of Transportation, Bureau of Transportation Statistics, National Transit Map (NTAD)". `reference/tod_stops.csv` redistributes NTM stop ids and rounded coordinates under that attribution.
- **Milwaukee County Transit System GTFS (MCTS Developer Terms)** require these notices wherever the derived data is shown:
  - This product is not sponsored or endorsed by MCTS.
  - Feed last updated 2025-05-08, valid through 2025-08-23 (Mobility Database copy mdb-2127 of the official feed).
  - No MCTS logos are used.
- **Mobility Database**: catalogue metadata is CC0. Feed content stays under the agency's terms, so the MCTS terms above apply to the stored copy.
- **Other agency GTFS feeds**: no licence or terms are stated. They are used as public records under owner decision D1 in [DATA_COMPLIANCE.md](../DATA_COMPLIANCE.md). The feeds stay in git-ignored `data/raw/`; only route-level frequencies feed the outputs.
- **Madison Metro's GTFS file is never downloaded or read** (AQ-045; office-hours questions 24 and 25). A test checks that the fetch and build scripts contain no Madison GTFS address.
- **Census 2020 blocks and 2024 cartographic boundaries**: public domain.
