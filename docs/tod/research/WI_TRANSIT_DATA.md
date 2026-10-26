# Wisconsin transit stop and frequency data: inventory for the TOD scenario

Prepared 2026-10-26 (all access dates below are 2026-10-26 unless stated). Research only: no data was added to the repo. Feeds were downloaded to scratch (`/private/tmp/claude-501/wi_tod/`) to test reachability and run a first frequency count; the script used is `/private/tmp/claude-501/wi_tod_scripts/freq.py`.

## Summary table

"Automatable" means a stable direct URL returned a GTFS zip to a plain script on 2026-10-26. "Licence" is what the agency (or, where marked, the Transitland Atlas record of the agency's terms) states. "None stated" means no licence or terms page was found; under owner decision D1 in [DATA_COMPLIANCE.md](../../DATA_COMPLIANCE.md) such government records are accepted as public records.

| Agency (NTD id) | Fixed-route modes in NTD 2025 | GTFS URL | Licence or terms | Automatable | Notes |
|---|---|---|---|---|---|
| Milwaukee County Transit System, MCTS (50008) | MB (CONNECT 1 BRT is reported inside MB, not as RB) | https://kamino.mcts.org/gtfs/google_transit.zip (linked from ridemcts.com/policies/developer-terms) | MCTS Developer Terms: revocable licence to reproduce and redistribute; must state the product is not sponsored by MCTS, show the date the data was last updated and the date through which it is valid; no MCTS logos | **No (today)**: connection timed out three times; Mobility Database marks the URL inactive | Last copy held by Mobility Database (mdb-2127) is dated 2025-05-08 and valid 2025-03-09 to 2025-08-23. BTS National Transit Map loaded a current MCTS feed on 2026-09-23 (3,696 stops) |
| The Hop streetcar, City of Milwaukee (55312) | SR | https://thehopmke.transloc.com/Secure/Admin/Reports/GTFSDownload.aspx | None stated | Yes | Valid 2026-09-01 to 2031-01-01. Routes are coded `route_type` 3 (bus), so the streetcar must be flagged by agency, not by route type |
| Madison Metro Transit, City of Madison (50005) | MB, RB (Rapid Route A) | https://transitdata.cityofmadison.com/GTFS/mmt_gtfs.zip | City of Madison Transit Data Developer License: revocable; "limited to uses that utilize the Data for assisting mass transit riders or in furtherance of promoting public transportation"; City claims ownership of data "derived from" its data | Yes (Last-Modified 2026-08-24) | **Licence question for owner** (see below). Feed has a "Route B" but only Route A is branded Rapid; Route B BRT is still planned |
| Green Bay Metro (50002) | MB | City page https://greenbaywi.gov/496/Transit-Data-Developer; file https://greenbaywi.gov/DocumentCenter/View/12124/Transit-Data-August-2024 | Per Transitland Atlas copy of the City licence: licence granted, credit optional ("Data provided under license granted by the City of Green Bay, Metro Transit") | **No**: HTTP 403 to scripts (same block noted in DATA_COMPLIANCE D3); file name changes with each release | Mobility Database copy (mdb-917) is from 2018 to 2020 and unusable. BTS National Transit Map has 1,497 current stops (2026-09-23) |
| Valley Transit, Appleton / Fox Cities (50001) | MB | https://ridemyvalleytransit.com/gtfs | None stated | Yes (rebuilt daily) | Syncromatics-hosted official feed |
| Kenosha Area Transit and Kenosha streetcar (50003) | MB, SR | https://kenoshatransit.com/gtfs | None stated (Atlas points to gtfs-directory.syncromatics.com, which has no terms text) | Yes (rebuilt daily) | Streetcar is route `SC`, coded as bus (`route_type` 3) |
| RYDE Racine (50006) | MB, CB | https://racine.connexionz.net/rtt/public/utility/gtfs.aspx (redirects to /resource/gtfs.zip) | None stated | Yes (Last-Modified 2026-09-07) | |
| Waukesha Metro Transit (50096) | MB, CB | https://mywaukeshametro.com/gtfs | None stated | Yes (rebuilt daily) | Mobility Database entry mdb-396 is an old, inactive URL |
| La Crosse MTU (50004) | MB | https://ridemtu.com/gtfs | None stated (Atlas cites an Interline archive licence, not the City) | Yes (rebuilt daily) | Mobility Database entry ntd-50004 is an old, inactive URL |
| Eau Claire Transit (50099) | MB | https://gtfs.ect.cadavl.com/ECT/GTFS/GTFS_ECT.zip | None stated | Yes (rebuilt daily) | Feed valid only one month at a time (2026-10-26 to 2026-11-25) |
| GO Transit, Oshkosh (50009) | MB | https://data.trilliumtransit.com/gtfs/oshkosh-wi-us/oshkosh-wi-us.zip | None stated by agency (Atlas: attribution not required, derived products allowed) | Yes (Last-Modified 2026-09-18) | |
| Shoreline Metro, Sheboygan (50088) | MB | https://data.trilliumtransit.com/gtfs/sheboygan-wi-us/sheboygan-wi-us.zip | As Oshkosh | Yes (Last-Modified 2026-02-05) | |
| Metro Ride, Wausau (50091) | MB | https://data.trilliumtransit.com/gtfs/wausau-wi-us/wausau-wi-us.zip | As Oshkosh | Yes (Last-Modified 2024-04-16) | File not updated for 2.5 years; only 327 of 567 stops are served on a weekday, so the feed may be stale |
| Janesville Transit System (50108) | MB | https://data.trilliumtransit.com/gtfs/jts-wi-us/jts-wi-us.zip | As Oshkosh | Yes (Last-Modified 2026-10-15) | |
| Beloit Transit System (50109) | MB | https://passio3.com/beloit/passioTransit/gtfs/google_transit.zip | None stated | Yes | |
| Fond du Lac Area Transit (50171) | MB | http://www.fonddulac.ridesystems.net/Secure/Admin/Reports/GTFSDownload.aspx | None stated | Yes | Plain http |
| Stevens Point Transit / Central Transportation (50359) | MB | https://passio3.com/centraltrans/passioTransit/gtfs/google_transit.zip | None stated | Yes | |
| Maritime Metro Transit, Manitowoc (50461) | MB | https://rapid.nationalrtap.org/GTFSFileManagement/UserUploadFiles/13162/MMTfeedfinal.zip | None stated | Yes (Last-Modified 2025-02-13) | Frequency result looks wrong (see below); National RTAP URLs change when a new file is uploaded |
| Platteville, Rusk County, La Crosse County (SMRT), Menominee Tribe, Bad River Band (50431, 50295, 50442, 55228, 55282) | MB | National RTAP upload URLs (see Atlas ids below) | None stated | Yes, but URLs are file-specific | Rusk and Menominee feeds expired (2026-05-01 and 2026-03-31). None has frequent service |
| Bay Area Rural Transit (50401), Dunn County (50226), Oneida-Vilas (55319), Merrill (50505), Ozaukee County commuter bus (50161) | MB or CB | No official feed found | n/a | No | BTS National Transit Map holds stops for 50401 (47), 50226 (16) and 55319 (9). None is a candidate for a frequent stop |
| Duluth Transit Authority, serving Superior (MN agency) | MB | https://duluthtransit.com/gtf/google_transit.zip | Developer page returns 403 to scripts; Atlas record: attribution not required, derived products allowed | Yes (Last-Modified 2026-08-05) | Must clip to the Wisconsin boundary; a rough box puts about 190 of 777 stops on the Superior side |
| Amtrak (Hiawatha, Empire Builder, Borealis) | Intercity rail | https://content.amtrak.com/content/gtfs/GTFS.zip | None found | Yes (Last-Modified 2026-10-25) | 8 Wisconsin rail stations: Milwaukee, Milwaukee Airport, Sturtevant, Columbus, Portage, Wisconsin Dells, Tomah, La Crosse. Prefer the public-domain BTS NTAD Amtrak Stations layer for locations |
| Metra (Union Pacific North, Kenosha station) | Commuter rail | https://schedules.metrarail.com/gtfs/schedule.zip | Metra licence page (metra.com) returns 403 to scripts; Atlas: attribution not required, derived products allowed | Yes (Last-Modified 2026-10-22) | One Wisconsin station. Location also available from BTS layers |

Mobility Database and Transitland identifiers:

| Agency | Mobility Database id (status) | Transitland feed onestop id |
|---|---|---|
| MCTS | mdb-2127 (inactive); RT feeds mdb-2128 to 2130 active | f-dp9-milwaukeecountytransitsystem |
| The Hop | none | f-the~hop~mke |
| Madison Metro | mdb-394 (active) | f-dp8m-metrotransit~cityofmadison |
| Green Bay Metro | mdb-917 (inactive) | f-green~bay~wi~us |
| Valley Transit | mdb-2069 (active) | f-dpc5-valleytransit |
| Kenosha | none | f-kenosha~wi~us |
| RYDE Racine | mdb-2246 (active) | f-dp9e-belleurbansystem |
| Waukesha Metro | mdb-396 (inactive) | f-dp9k-waukeshacounty~wi~us |
| La Crosse MTU | ntd-50004 (inactive) | f-lacrosse~wi~us |
| Eau Claire Transit | mdb-208 (inactive) | f-9zyy-eauclairetransit |
| GO Transit Oshkosh | mdb-397 (active) | f-dpc4-oshkosh~wi~us |
| Shoreline Metro | mdb-399 (active) | f-dpc8-sheboygan~wi~us |
| Metro Ride Wausau | mdb-830 (active) | f-wausau~wi~us |
| Janesville | mdb-393 (active) | f-dp8d-jts~wi~us |
| Beloit | tld-77 (active) | f-dp89-beloittransit~wi~us |
| Fond du Lac | tld-7929 (active) | f-fond~du~lac |
| Stevens Point | tld-4757 (active) | f-stevens~point~wi |
| Manitowoc | none | f-cityofmanitowoc~wi~us |
| Platteville; Rusk; La Crosse County; Menominee; Bad River | none | f-cityofplatteville~wi~us; f-ruskcountytransitcommission~wi~us; f-countyoflacrosse~wi~us; f-menomineeindiantribeofwisconsin~wi~us; f-badriverbandoflakesuperiortribeofchippewa~wi~us |
| Duluth Transit | mdb-301 (active) | f-cbq6-duluthtransitauthority |
| Amtrak | mdb-11 (active) | f-9-amtrak~amtrakcalifornia~amtrakcharteredvehicle |
| Metra | mdb-2854 (active) | f-dp3-metra |

## 1. Agency list from the NTD

Source: NTD Annual Data View, Service (by Mode), `https://data.transportation.gov/resource/4fir-qbim.json`, filtered to `max_state='WI'`, report years 2024 and 2025 (dataset updated 2026-10-14). Licence: public domain (federal work), already documented in [ntd.md](../../data-sources/ntd.md).

- Report year 2025 has 109 agency-mode rows. Most are demand response (DR) shared-ride taxis.
- 28 agencies report a fixed-route mode (MB bus, RB bus rapid transit, SR streetcar, CB commuter bus) in 2024 or 2025. The table above covers all of them.
- Largest fixed-route systems by 2025 unlinked passenger trips (boardings per year):
  - MCTS bus: 25,029,801 trips.
  - Madison bus: 9,709,406 trips; Madison Rapid Route A (RB): 2,678,767 trips.
  - Kenosha bus: 1,150,984 trips; Kenosha streetcar: 22,689 trips.
  - RYDE Racine bus: 929,422 trips.
  - Green Bay bus: 787,156 trips.
  - Eau Claire bus: 689,919 trips; La Crosse bus: 670,148 trips.
  - Oshkosh bus: 572,273 trips; Valley Transit bus: 555,479 trips; Sheboygan bus: 535,165 trips.
  - The Hop streetcar: 494,557 trips.
  - Wausau 416,328; Waukesha 396,668; Janesville 366,682 trips.
- MCTS reports CONNECT 1 inside its MB (bus) total, so NTD alone cannot separate BRT from local bus in Milwaukee. Madison reports Rapid Route A separately as RB.
- The NTD has no stop locations or schedules. The Stations and Facilities tables (`wfz2-eft6`, `aqct-knjk`) only count facilities by type and decade.
- Out-of-state operators serving Wisconsin (Duluth Transit, Amtrak, Metra) report under their own states.

## 2. GTFS feeds: reachability and terms

How the list was built: the Mobility Database catalogue CSV (`https://files.mobilitydatabase.org/feeds_v2.csv`, 6,686 feeds) and the Transitland Atlas repository (github.com/transitland/transitland-atlas, CC BY 4.0) were searched for Wisconsin agencies; every listed static URL was then fetched once.

Findings:

- 23 of 28 fixed-route agencies have an official GTFS feed (official means published by the agency or its contracted vendor, not a third-party mirror). 21 of those 23 returned a valid zip to a script today. The 2 that did not are MCTS (connection timeout) and Green Bay (HTTP 403). The other 5 agencies, all small, have no feed we could find.
- Hosting: most mid-size systems publish through their AVL or scheduling vendor (Syncromatics, Trillium, Passio, TransLoc, RideSystems, Connexionz, CAD/AVL). These are the agencies' own publication channels, not commercial mirrors; the vendor sites show no terms that restrict download.
- The Mobility Database catalogue is behind for Wisconsin: 6 of the active feeds (Hop, Kenosha, Waukesha, La Crosse, Eau Claire, Manitowoc) are missing or listed under dead URLs. The Transitland Atlas is more current and is the better discovery index.
- **MCTS.** The terms page still links the kamino.mcts.org file, but the host did not answer (three tries with up to 90 seconds). It may block some networks or be down. The BTS National Transit Map loaded MCTS on 2026-09-23, so a working copy existed last month. For this first look we used the Mobility Database's stored copy of May 2025. Action: retry from another network, or ask MCTS for the current address.
- **Madison licence.** The City of Madison terms limit use to "assisting mass transit riders or in furtherance of promoting public transportation", and say data derived from City data stays City property. A housing model that maps homes near transit plausibly furthers public transportation, but this is a judgement call and the derived-data clause is broad. This is the only possible licence blocker found; it needs an owner decision (and could be settled by an email to Metro).
- **MCTS licence** is usable but carries notice duties: say the tool is not sponsored by MCTS, and show the feed's last-updated date and its validity end date.
- **Green Bay** must be fetched by hand or taken from a national layer; its City licence (as recorded by Transitland) is permissive.
- Mobility Database terms (last updated 2024-01-23): catalogue metadata is CC0; "Content within the feeds is licensed by their respective data owners". Its API needs a free account token; the catalogue CSV and stored `latest.zip` copies download without login. Its stored copies are a mirror, so under our rules they are a fallback only, with the agency licence still applying.
- Transitland's hosted API and archive require attribution to Transitland and an API key; the Atlas repository itself is CC BY 4.0. Using the Atlas only to find official URLs is clean.

## 3. National stop layers as fallbacks

| Layer | What it has | Wisconsin coverage | Licence | Use for us |
|---|---|---|---|---|
| BTS National Transit Map, Stops and Routes (NTAD), ArcGIS FeatureServer `NTAD_National_Transit_Map_Stops` | GTFS stops and route shapes, compiled 2026-09-23, keyed by `ntd_id` | Every Wisconsin fixed-route agency with a feed, including Green Bay (1,497 stops) and MCTS (3,696 stops), plus Bay Area Rural, Dunn County and Oneida-Vilas | Layer states "Creative Commons Attribution 3.0 United States (CC-BY-3.0)" | Best statewide stop-location fallback, queryable by API. **No stop times**, so it cannot test frequency |
| BTS NTAD Amtrak Stations | Station points | 8 Wisconsin rail stations and 31 Thruway bus stops | Public domain ("work of the United States government ... unrestricted public use") | Use for Amtrak station locations instead of the Amtrak GTFS, which states no licence |
| BTS Intermodal Passenger Connectivity Database | Terminal points by mode | Rail and intercity terminals | Public domain | Cross-check for Metra Kenosha and Amtrak |
| NTD Stations and Facilities | Counts by agency, type and decade | All reporters | Public domain | Counts only; no locations |
| EPA Smart Location Database v3 (2021) | Block-group D4 transit measures (below) | 11 of 72 counties have transit values | EPA public data (federal work); the map service credits "EPA Office of Community Revitalization" | Top-down cross-check, not a stop layer |

EPA Smart Location Database D4 variables (user guide, May 2021, Appendix B):

- D4A: distance in metres from the block group's population-weighted centre to the nearest transit stop.
- D4B025 and D4B050: share of block-group jobs within 0.25 and 0.5 mile of a fixed-guideway station.
- D4C: aggregate transit trips per hour, weekday 4 to 7 pm, summed over all routes with a stop within 0.25 mile of the block group boundary, both directions.
- D4D and D4E: D4C per square mile and per person.
- Transit inputs are 2020 GTFS. The Wisconsin agencies included are only MCTS, Madison, Racine, La Crosse, Janesville, Oshkosh and Duluth. Green Bay, Valley Transit, Kenosha, Waukesha Metro, Eau Claire, Sheboygan, Wausau and The Hop are missing, and Madison's BRT did not exist yet.
- Housing units (`CountHU`) are 2018 estimates on 2019 block-group boundaries (2010-census vintage), even though the service carries a `GEOID20` field.
- Fetchable automatically from `https://geodata.epa.gov/arcgis/rest/services/OA/SmartLocationDatabase/MapServer/14/query` (tested today).

## 4. Frequency first look (scratch download)

Method (`freq.py`): for each feed, pick the Tuesday to Thursday with the most scheduled trips in the next 120 days of the feed's validity; count weekday departures per stop per clock hour; a stop is "frequent at N" when it has at least N departures in **each** of the hours 7:00 to 7:59 and 8:00 to 8:59. "One direction" sums all routes in the busiest single direction (stricter); "any direction" sums both directions. Stops are boarding points (`location_type` 0 or blank).

| Feed (service day tested) | Stops in feed | Routes | Stops served that weekday | ≥4 trips per hour, any direction | ≥4 trips per hour, one direction | ≥3 trips per hour, one direction |
|---|---|---|---|---|---|---|
| MCTS (2025-06-19, May 2025 copy) | 3,735 | 50 | 3,698 | 1,840 | 1,765 | 2,210 |
| Madison Metro (2026-10-27) | 1,662 | 29 | 1,659 | 421 | 402 | 468 |

Both counts include the rail and BRT stops of definition (a). MCTS CONNECT 1 has 34 stops; Madison Rapid Route A has 84 stops. Results for every other feed are in the definitions section below.

Caveats: the MCTS copy is 14 months old; peak is a two-hour morning window; a stop pair across the street counts as two stops. Manitowoc's feed gives 135 of 286 stops at 4 or more trips per hour, which is not credible for a system running 6 buses at peak (NTD 2025 VOMS), so that feed needs checking before use.

## 5. Candidate "major transit stop" definitions compared on statewide data

The owner asked which definition uses the most and best statewide data and gives the biggest defensible yield. Counts below are stops (boarding points), summed across the 22 Wisconsin feeds we fetched plus 9 rail stations (8 Amtrak, 1 Metra). They exclude Green Bay (no current feed fetched) and Superior (Duluth feed not clipped). MCTS uses the May 2025 copy. Manitowoc is excluded from (b) to (d) because of the data problem above.

| Definition | Statewide data that can measure it | Agencies measurable | Qualifying stops, Wisconsin (count of stops) | Of which MCTS and Madison | Main gaps |
|---|---|---|---|---|---|
| (a) Rail and BRT stations only | Agency GTFS (Hop, Kenosha streetcar, CONNECT 1, Route A); BTS NTAD Amtrak Stations (public domain); NTM stops | All (only 4 systems plus 9 rail stations) | 170 (34 CONNECT 1 + 84 Route A + 26 Hop + 17 Kenosha streetcar + 9 rail) | 118 | Smallest yield. Streetcars are coded as bus in GTFS, and NTD lumps CONNECT 1 into bus, so BRT and streetcar must be flagged by hand from route names (a documented manual step) |
| (b) (a) plus bus stops with ≥4 trips per hour at peak (15-minute service) | Agency GTFS stop times only | 21 of 28 fixed-route agencies today (Green Bay and MCTS need a working URL; 5 have no feed) | 2,300 (one direction); about 2,440 if both directions are summed | 2,167 | Green Bay probably adds few (10 stops in its 2018 feed); NTM and SLD cannot measure it |
| (c) (a) plus ≥3 trips per hour (20-minute service) | Agency GTFS | Same as (b) | 2,898 (one direction) | 2,678 | Same as (b). Adds about 600 stops (26 percent more than (b)), mostly in Milwaukee (+445) |
| (d) California PRC 21064.3: rail, BRT or ferry station, or the intersection of two or more bus routes each at 15 minutes or better in both morning and afternoon peaks | Agency GTFS | Same as (b) | About 580: 170 under (a) plus about 410 bus stops where two qualifying routes meet within 150 metres (MCTS 345, Madison 55, Wausau 7, Eau Claire 2, Janesville 1) | About 520 | Strictest bus test. The Wausau and Eau Claire hits are transfer centres where timed pulses pass the test |
| (e) Any stop of an NTD-reporting fixed-route system | NTM stops (all agencies, CC BY 3.0) or agency GTFS | All 28 (NTM covers 26) | About 11,550 served on a weekday in our 22 feeds, about 13,200 with Green Bay and Superior | 5,357 | Not "major" transit; would cover hourly rural and small-city routes. Easiest to measure |
| (f) EPA SLD D4C thresholds, block-group level | EPA SLD only | 7 Wisconsin agencies, 2020 service | Not a stop count. Block groups (count) and housing units (2018) at or above each threshold: D4C ≥4 trips per hour: 1,098 block groups, 579,836 housing units; ≥8: 685 block groups, 366,266 units; ≥16: 221 block groups, 139,307 units. All block groups with any transit value: 1,485, 792,261 units. Wisconsin total: 4,473 block groups, 2,681,232 units | Most of the 1,098 are in Milwaukee County (815 block groups have transit values there) and Dane County (211) | 2020 schedules, 2010-vintage boundaries; misses 8 agencies; D4C sums both directions and every route within 0.25 mile of a large area, so "≥4" is far looser than (b); cannot be turned into stop buffers |

What this means:

- The definitions that agency GTFS can measure, (a) to (d), have the best statewide coverage of current service. They cover every agency with frequent service except Green Bay. Green Bay's stop locations are in the NTM, but its frequency would need a manual feed download.
- (e) and (f) can be measured with the least work, but (e) is not a "major" stop and (f) is out of date and leaves out a third of the state's urban systems.
- The biggest defensible yield is **(c), 20-minute peak service plus rail and BRT**: about 2,900 stops, or 26 percent more than (b). It is defensible because it uses the same agency data and method as (b), and a published 20-minute threshold is easy to explain. It is less standard than 15 minutes; California's "high-quality transit corridor" and most state TOD laws use 15. A sound plan is to run (b) as the main case and (c) as a high case, both from the same script.
- Counting both directions (as the original brief's "any direction" does) adds about 6 percent to (b) statewide (about 2,440 stops instead of 2,300). Counting one direction is the more defensible reading of "15-minute service".
- Almost all of the yield under (b) to (d) is in Milwaukee and Madison: 94 percent of (b) stops (2,167 of 2,300). So the MCTS feed access problem matters more than any other gap.

## 6. Top-down estimate without stop data

Statewide Wisconsin data that supports an estimate of homes near transit without building a stop layer:

- **2020 Census DHC, table H1 (housing units) at block level**, Census API, public domain. Already listed in [data/DATA_SOURCES.md](../../../data/DATA_SOURCES.md). Blocks are small enough to buffer around stops or route lines.
- **ACS 5-year B25001 and B25024 at block group** (homes by structure type), already listed.
- **EPA SLD** `CountHU`, D4A and D4C at block group (section 3). A first bound: 579,836 housing units (2018) lie in block groups with D4C of at least 4 trips per hour, about 22 percent of 2,681,232 units statewide.
- **BTS National Transit Map routes** (shapes, CC BY 3.0) can be buffered by 0.5 mile and overlaid on census blocks as a route-based proxy where stop times are missing.
- **NTD service-area population** (`max_service_area_population` in `4fir-qbim`) gives a coarse agency-level ceiling.
- **TIGER/Line 2020 blocks and block groups** for the overlays (already listed).

No statewide WisDOT transit stop layer was found in this pass; that was not searched exhaustively.

## 7. Recommended data plan

1. Fetch the 21 working official GTFS URLs automatically, with the access date, Last-Modified header and SHA-256 recorded in a manifest. Store raw feeds git-ignored under `data/raw/`.
2. MCTS: retry the official URL from another network; if it stays down, email MCTS for the current address. Do not use the Mobility Database copy in the final run except as a documented fallback.
3. Madison: owner decides whether the "promoting public transportation" clause covers our use, or emails Metro to confirm.
4. Green Bay: take stop locations from the BTS National Transit Map (automatable) and either download the City file by hand or treat Green Bay as having no frequent stops (its 2018 feed had 10).
5. Use BTS NTAD Amtrak Stations (public domain) for intercity rail stations, and flag The Hop, the Kenosha streetcar, CONNECT 1 and Madison Route A by route name.
6. Clip Duluth Transit stops to the Wisconsin boundary for Superior.
7. Keep EPA SLD as a cross-check only.

## Sources and access

| Source | URL | Version or date seen | Licence |
|---|---|---|---|
| NTD Annual Data View, Service (by Mode) | https://data.transportation.gov/resource/4fir-qbim.json | Updated 2026-10-14; report years 2024 and 2025 | Public domain |
| NTD Complete Monthly Ridership | https://data.transportation.gov/resource/8bui-9xvu.json | Full reporters only | Public domain |
| NTD 2024 Reporter Agency Information | https://data.transportation.gov/resource/ccvf-fykn.json | Updated 2026-07-07; no GTFS URL field | Public domain |
| Mobility Database catalogue | https://files.mobilitydatabase.org/feeds_v2.csv | 6,686 feeds, read 2026-10-26 | CC0 (metadata); feeds under owners' terms |
| Transitland Atlas | https://github.com/transitland/transitland-atlas | main branch, cloned 2026-10-26 | CC BY 4.0 |
| BTS National Transit Map Stops | https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_National_Transit_Map_Stops/FeatureServer/0 | Compiled 2026-09-23 | CC BY 3.0 US |
| BTS NTAD Amtrak Stations | https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_Amtrak_Stations/FeatureServer/0 | As of 2026-10-08 | Public domain |
| EPA Smart Location Database v3 | https://geodata.epa.gov/arcgis/rest/services/OA/SmartLocationDatabase/MapServer/14 ; user guide https://www.epa.gov/system/files/documents/2023-10/epa_sld_3.0_technicaldocumentationuserguide_may2021_0.pdf | v3, 2021 (2020 GTFS) | U.S. federal data |
| MCTS developer terms | https://www.ridemcts.com/policies/developer-terms | Read 2026-10-26 | As quoted above |
| Madison Metro licence | http://transitdata.cityofmadison.com/MetroTransitDataTermsOfUse.pdf | Read 2026-10-26 | As quoted above |
| Mobility Database API terms | https://mobilitydatabase.org/terms-and-conditions | Last updated 2024-01-23 | As quoted above |
