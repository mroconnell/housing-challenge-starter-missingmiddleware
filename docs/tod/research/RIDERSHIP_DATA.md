# Transit ridership data for the TOD comparison cities

Prepared 2026-10-27 (all access dates are 2026-10-27). Research only: no data was added to the repo. Test queries were small API calls; one 2-page Sound Transit PDF was fetched to scratch (`/private/tmp/claude-501/rid/`). Two questions from the owner:

- (a) How big is each city's transit? (a possible "transit size" trait for [TRAITS_PLAN.md](../TRAITS_PLAN.md))
- (b) Did ridership at stations near rezoned land rise or fall in a predictable way before and after the rezoning?

Terms used below. **Boardings** (the NTD calls them unlinked passenger trips, UPT) count every time a rider gets on a vehicle, so a trip with one transfer counts twice. **Entries** count people passing a fare gate into a station; transfers inside the station are not counted. The two are not comparable across agencies.

## Summary table

"Automated" means a plain script got data on 2026-10-27 (tested) or the source is an API or direct file link (not tested, marked so). "Before/after" asks whether the series has at least 3 years before and 3 years after the reform at the stations that matter.

| City (reform year) | Source | Level | Years | Licence or terms | Automated | Covers before/after? |
|---|---|---|---|---|---|---|
| All US cities | NTD Complete Monthly Ridership (`8bui-9xvu`) | Agency by mode, monthly boardings, plus vehicle revenue miles and hours | Jan 2002 to Aug 2026 | Public domain | Yes (SODA API, tested) | Yes at agency level for every US case |
| New York (2003 to 2013) | MTA Subway Station Monthly Ridership (`ak4z-sape`, data.ny.gov) | Station complex, monthly entries | Feb 2017 to Sep 2026 | data.ny.gov terms; attribution "Metropolitan Transportation Authority"; no restrictive licence in metadata | Yes (tested) | **No**: starts 4 to 14 years after the rezonings |
| New York | MTA Subway Hourly Ridership (`t69i-h2me`, `wujg-7c2s`, `5wq4-mkjj`) | Station complex, hourly entries | Jan 2017 to present | As above | Yes (tested) | No |
| New York | MTA Turnstile Usage Data, one dataset per year (`i55r-43gk` 2014 to `k7j9-jnct` 2022) | Turnstile, 4-hour cumulative counters (entries and exits) | 2014 to 2022 on data.ny.gov; 2010 to 2013 raw files no longer at web.mta.info (HTTP 404) | As above | Yes for 2014+ (not tested; large) | No: earliest is 2010 |
| New York | MTA annual "subway ridership by station" spreadsheets | Station complex, annual entries, each file showing about 6 years | Current site has 2018+ files; older tables reported back to about 1998 | MTA website, no licence stated | **No**: mta.info returns HTTP 403 to scripts; Wayback also refused | Possibly, if archived tables for about 1998 to 2013 can be recovered (source_lead) |
| Philadelphia (2012) | SEPTA ridership statistics (OpenDataPhilly) | Bus and trolley stop average daily boardings (one file per season); Regional Rail station boardings | Bus stops Fall 2014 to Summer 2025; Regional Rail stations 2017 to 2024; route and mode monthly 2019+ | "License not specified", "Public use" | Yes (ArcGIS Hub CSV links, not tested) | **No**: every series starts after 2012 |
| Philadelphia | SEPTA `HighSpeed` stations layer (Market-Frankford, Broad Street) | Station, weekday, Saturday and Sunday boardings | One undated snapshot | None stated | Yes (ArcGIS REST, fields tested) | No |
| Charlotte (2019) | CATS station boardings, public records request 2094 | Blue Line station, average weekday, Saturday, Sunday boardings and alightings | 2018 only | Public record | No (PDF) | No (one year before); a records request for 2015 to 2024 could fix this |
| Saint Paul (2011) | Metropolitan Council "Transit Stops Boardings and Alightings" | Stop, average daily boardings and alightings | Latest Fall (2024); older vintages not confirmed | Public data under Minnesota Statutes chapter 13 (per metadata) | Unclear: gisdata.mn.gov moved to gis.data.mn.gov and old file URLs return 404 | **No by design**: the Green Line opened June 2014, 3 years after the rezoning, so its stations have no "before" |
| Chicago (2013, 2015) | CTA "L" Station Entries, Daily Totals (`5neh-572f`, data.cityofchicago.org) | Station, daily entries (weekday, Saturday, Sunday or holiday) | 1 Jan 2001 to 31 Jul 2026, 148 stations | City of Chicago data portal terms (free use, no warranty) | Yes (tested) | **Yes**: 12 years before 2013 and 10 years after 2015 |
| Chicago | CTA bus routes daily totals (`jyb9-n7fm`); bus stop boardings October 2012 (`mq3i-nnqe`) | Route daily; stop, one month | Routes 2001+; stops Oct 2012 only | As above | Yes (not tested) | Routes yes; stops no |
| Los Angeles (2013) | LA Metro line ridership statistics and board reports | Line, monthly; station boardings only in occasional board reports | Line level about 2009+ | Metro website, no licence stated | No: the ridership statistics site timed out from a script | Line level yes; **no open station series found** |
| Seattle (2012, 2014) | Sound Transit quarterly Service Delivery Performance Reports | Link station, average weekday boardings | About 2010 to 2019 in PDF tables; recent months in a Power BI dashboard | Sound Transit website terms | No (PDF tables; Power BI is not scriptable) | **Probably yes** for Othello, Beacon Hill, Mount Baker (open since July 2009); needs PDF extraction and a check of the 2010 to 2013 reports |
| Bellevue (2009) | Sound Transit (as above); King County Metro route reports | Station; route | East Link stations from April 2024 | As above | No | **No by design**: stations opened 15 years after the rezoning |
| Toronto (2014) | TTC "Subway ridership" annual station tables (Transparency and Accountability pages); ArcGIS layer for 2012 to 2013 | Station, typical weekday users | 2007-2008 table, 2012-2013 layer, recent years to 2023-2024 | TTC website copyright, not under the Toronto open licence | Partly (PDFs and one ArcGIS layer) | **No by design**: Eglinton Crosstown opened 8 Feb 2026 |
| Madison (2023) | City of Madison "Metro Ridership by Stop" and "by Route Stop" (MapServer layers 64 and 63) | Stop, estimated average weekday boardings | February 2024 only | City of Madison Data Policy: "informational purposes", City reserves its IP, no reuse licence stated | Yes (ArcGIS REST, tested) | No (one month, after the June 2023 network redesign) |
| Milwaukee (2018, 2023) | MCTS 2008 weekday ridership by stop (UWM GeoDiscovery); MCTS press figures for CONNECT 1 | Stop, average weekday ons and offs | 2008 only; CONNECT 1 only as press numbers | UWM catalogue record; MCTS none stated | Partly | No |

## Notes by source

### NTD (agency level, all US cities)

Confirmed by query on 2026-10-27: the NTD monthly file runs from January 2002 to August 2026 for every agency below. The series to use is `upt` (boardings) and, for supply, `vrm` (vehicle revenue miles) and `voms` (vehicles in peak service), all in the same rows.

| City | NTD agency (id) | Modes to sum | 2019 boardings (trips per year) | Series notes |
|---|---|---|---|---|
| New York | MTA New York City Transit (20008) | HR, MB, RB, CB | Subway (HR) 2,723,960,145; bus (MB) 691,616,614 | Select Bus Service coded RB from 2012 |
| Philadelphia | SEPTA (30019) | HR, MB, SR, TB, CR | HR 91,253,676; MB 152,152,387; SR 24,898,413; CR 35,114,104 | Trolleys coded LR until Dec 2011, SR after |
| Charlotte | City of Charlotte, CATS (40008) | LR, MB, SR | LR 8,875,581; MB 14,516,464 | LR 4,816,511 in 2017 rose to 7,123,616 in 2018 when the Blue Line Extension opened (March 2018), one year before the 2019 rezoning |
| Saint Paul | Metro Transit (50027) | LR, MB, RB | LR 25,299,442; MB 51,860,027 | LR 10,162,919 in 2013 rose to 23,003,457 in 2015 with the Green Line; Metro Transit also serves Minneapolis |
| Chicago | CTA (50066) | HR, MB | HR 218,467,141; MB 237,276,400 | Metra (commuter rail) is a separate agency |
| Los Angeles | LA Metro (90154) | HR, LR, MB, RB | HR 41,775,490; LR 51,396,408; MB 270,595,093; RB 6,714,108 | BRT (G and J Lines) coded RB only from July 2012; before that it is inside MB, so the G Line alone is not separable in the NTD |
| Seattle, Bellevue | Sound Transit (00040); King County Metro (00001) | ST: LR, CB, CR; KCM: MB, TB | ST LR 24,761,684; KCM MB 104,362,252 and TB 17,373,451 | ST LR jumped from 11,530,411 (2015) to 19,011,368 (2016) when University Link opened; ST LR also includes Tacoma Link |
| Madison | City of Madison (50005) | MB, RB | MB 12,856,514 | |
| Milwaukee | Milwaukee County (50008); City of Milwaukee, The Hop (55312) | MB; SR | MCTS MB 28,972,674; Hop SR 760,321 | CONNECT 1 BRT is reported inside MB. Hop series starts Nov 2018 |
| Toronto | Not in NTD | | | Use TTC annual Operating Statistics (annual boardings, web pages 2014 onward). Not openly licensed; the numbers are facts that can be cited |

Caveats:
- NTD is reported by agency, not by city. Metro Transit, Sound Transit, King County Metro, SEPTA and LA Metro all serve far more than the reform city. Divide by the agency's service-area population (NTD annual Agency Information table), not by city population, or the large regional agencies will look oversized.
- The monthly file includes FTA adjustments and estimates for some months; annual sums match the annual NTD within a few percent but not exactly.

### New York

The open station series begins in 2017 (monthly and hourly entries by station complex). The 2003 to 2013 rezonings need about 1998 to 2018 at minimum. Two routes exist, neither tested end to end:
1. MTA's annual station ridership tables (one spreadsheet per year, each with about 6 years of annual entries by station). The current files are on mta.info, which returns HTTP 403 to scripts. Older years (before about 2013) would come from archived copies. Manual download by the owner is the likely path.
2. Raw turnstile files from May 2010 were once at web.mta.info; the old URLs now return HTTP 404. Even if recovered, 2010 is after most rezonings.

Test query: Union St (R) station, Park Slope Fourth Avenue corridor, had 2,266,962 entries in 2019 and 2,005,303 in 2025 (annual entries, from monthly rows).

### Chicago

The best source found. Daily entries at all 148 "L" stations from 1 January 2001, with the same station ids throughout. Test query: Logan Square entries were 1,385,623 in 2001, 2,199,436 in 2013 (the ordinance year) and 2,315,219 in 2015 (the amendment year), then 2,261,714 in 2019 (annual entries). Note that both Chicago ordinances apply near every CTA and Metra station, so a before/after test must compare stations by how much land was actually upzoned around them (the trait plan's Chicago units), not treated against untreated stations. Metra station counts are separate and were not checked.

### Philadelphia

SEPTA's open files start in Fall 2014 (bus stops) and 2017 (Regional Rail stations). Nothing open covers subway or trolley stations before the 2012 remapping. DVRPC has historical Regional Rail station counts in reports (not checked).

### Charlotte

The only station-level file found is a 2018 public records response (City Clerk request 2094, `gis.charlottenc.gov/static/PublicRecords/2094.pdf`) with average weekday boardings by Blue Line station (for example CTC 4,273 boardings per weekday; 25th Street 80). A records request for 2015 to 2024 by station would make a before/after test possible. The 2018 line extension is a confounder: ridership on the original stations shifted when 10 new stations opened a year before the rezoning.

### Saint Paul, Bellevue, Toronto, Madison, Milwaukee

In all five, the transit line the rezoning anticipated opened after the rezoning (Green Line 2014, East Link 2024, Eglinton Crosstown 2026, Madison Rapid Route A 2024, CONNECT 1 2023). There is no "before" ridership at those stations, so question (b) cannot be asked as a before/after test. Only a cross-section is possible: after opening, do stations with more rezoned land have more boardings? For Saint Paul this would use Metro Transit stop boardings, if older Fall vintages (2015 to 2019) can be found on the moved Minnesota Geospatial Commons.

Madison licence: the ridership-by-stop layers are City of Madison open data, not Metro's GTFS feed, so the GTFS developer licence set aside by the owner does not apply. The City Data Policy grants no explicit reuse licence and reserves the City's IP. Same status as other "none stated" public records under DATA_COMPLIANCE decision D1; owner to confirm. The file is one month (February 2024) and cannot support a time comparison anyway.

### Los Angeles

No open station-level series found for the G Line (Warner Center) or the L Line (Chinatown, Lincoln Heights/Cypress Park). LA Metro's line-level ridership site timed out from scripts. Station boardings appear in some board report handouts (libraryarchives.metro.net) and could be requested. In NTD, the G Line cannot be separated from other BRT.

### Seattle

Sound Transit's quarterly Service Delivery Performance Reports (2017 and 2018 PDFs confirmed by search) include a table of average weekday boardings by Link station. The reports note that station boardings use a different method from system totals, so compare stations only with stations. Whether the 2010 to 2013 reports carry the same table was not confirmed; the 2012 monthly summary checked does not. Confounders: University Link opened March 2016 and Northgate Link October 2021, both shifting boardings at southern stations.

## Recommended plan

### Question (b): station-level before/after ridership

1. **Chicago: do it.** Daily entries for 2001 to 2026 at every station, scriptable, permissive terms. Measure each station's change in annual entries from the 3 years before 2013 to the 3 years after 2015, and compare stations with more upzoned land against stations with little or none (dose response). Use 2017 to 2019 as the "after" window to stay clear of 2020 pandemic losses. Weakness: all stations were eligible, and the CTA lost riders systemwide after 2015 (NTD heavy rail boardings fell from 241,676,065 in 2015 to 218,467,141 in 2019, a 9.6% drop in trips per year), so only differences between stations are meaningful.
2. **Seattle: worth a manual pass.** Three stations (Othello, Beacon Hill, Mount Baker) against the other original Link stations, 2010 to 2019, from PDF tables. With 3 treated stations this is a description, not a test.
3. **New York: only if the owner can download MTA's archived annual station tables by hand.** If 1998 to 2019 annual entries by station are recovered, the 17 pooled rezonings have nearby stations and many untouched stations to compare against. This would be the strongest test. Without those files New York cannot be used.
4. **Charlotte: only with a records request** to CATS for annual average weekday boardings by Blue Line station, 2015 to 2024.
5. **Not possible:** Philadelphia (no open data before 2014), Los Angeles (no open station series), and the five cities whose line opened after the rezoning.

Expect a weak signal. New homes near a station add riders slowly and in small numbers compared with a station's total: 1,000 new homes producing about 0.5 transit trips per home per weekday is about 500 boardings per weekday, against several thousand at a typical Chicago or New York station. Year-to-year noise from service changes will often be as large.

### Question (a): agency ridership as a "transit size" trait

1. Build one table from the NTD monthly file: for each unit's city and effective year, sum annual boardings and vehicle revenue miles over the agencies in the table above, for the year before the effective year. Divide by the agencies' service-area population. This gives boardings per resident per year and revenue miles per resident per year.
2. Prefer **revenue miles per resident** as the trait (how much service is run), and keep boardings per resident as a second version. Ridership is partly an outcome of density, so it is more likely to carry the effect back into the trait.
3. Toronto has no NTD; use TTC annual Operating Statistics if Toronto units are ever added.
4. Limitation the owner should weigh first: the trait test fits on 4 cities (New York, Philadelphia, Charlotte, Saint Paul) with leave-one-city-out folds. A city-level trait has one value per city, so in each fold it is fitted on 3 values and cannot be told apart from anything else about those cities. The parking-minimums trait already ran into this (TRAITS_PLAN section 8, item 12). A unit-level version would be more useful: **station busyness before the rezoning** (entries at the unit's nearest station). Today that exists only for Chicago (2001+), and for New York only if the archived tables are recovered.

## Sources checked

- NTD monthly ridership API: https://data.transportation.gov/resource/8bui-9xvu.json
- MTA datasets: https://data.ny.gov/resource/ak4z-sape.json, `t69i-h2me`, `wujg-7c2s`, `5wq4-mkjj`, turnstile `i55r-43gk` to `k7j9-jnct`; annual pages such as https://www.mta.info/agency/new-york-city-transit/subway-bus-ridership-2023
- CTA: https://data.cityofchicago.org/resource/5neh-572f.json and related `t2rn-p8d7`, `jyb9-n7fm`, `mq3i-nnqe`
- SEPTA: https://opendataphilly.org/datasets/septa-ridership-statistics; https://services.arcgis.com/fLeGjb7u4uXqeF9q/ArcGIS/rest/services/HighSpeed/FeatureServer
- Charlotte: https://gis.charlottenc.gov/static/PublicRecords/2094.pdf
- Metropolitan Council: dataset `us-mn-state-metc-trans-stop-boardings-alightings` (formerly gisdata.mn.gov)
- Sound Transit: https://www.soundtransit.org/ride-with-us/system-performance-tracker/ridership; quarterly reports such as https://www.soundtransit.org/sites/default/files/2017-q2-service-delivery-performance-report.pdf
- TTC: https://www.ttc.ca/transparency-and-accountability (Operating Statistics; Subway Ridership 2023-2024 PDF); https://transittoronto.ca/archives/reports/ttc-subway_ridership_2007-2008.pdf; https://services.arcgis.com/As5CFN3ThbQpy8Ph/ArcGIS/rest/services/TorontoSubwayStations_Ridership/FeatureServer
- Madison: https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA_TRANS/MapServer/64 and /63; https://www.cityofmadison.com/policy/data
- Milwaukee: https://geodiscovery.uwm.edu/catalog/ark:-77981-gmgspc2t81v/metadata; https://ridemcts.com/who-we-are/news/mcts-announces-positive-ridership-numbers-on-conne
