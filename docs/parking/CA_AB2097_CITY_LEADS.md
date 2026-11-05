# CA AB 2097: city map leads (searched 2026-11-05, before lock)

Plan: [CA_AB2097_PLAN.md](CA_AB2097_PLAN.md), section 8 (city sample, six checks per city, hearings).
Web reading only: no permits read or placed, no GIS layers downloaded, no records requests or emails.
User agent `missing-middleware-research/1.0 (public data)`; sites that refused it are cited, not worked around.
Searched by four helpers in parallel; their full notes follow the summary. One helper sent one Sacramento attribute
query (no geometry) against the brief; its output was not used.

## Summary

| City | Source of lead | Result | Map date | Hearing on AB 2097 |
| --- | --- | --- | --- | --- |
| Sacramento | Paper frame (placebo: 2024 repeal) | GIS layer (city "AB 2097 Parking") | created 2023-02-03; edited 2026-11-05 (republished, so edit date ≠ drawing date) | None on AB 2097 itself found |
| Truckee | Paper frame | GIS layer (½ mile around Train Depot) | last edited 2024-01-09 | Cited on one project, Planning Commission 2024-09-17 |
| Oakland | Paper frame | GIS layer; Spring 2023 version (15-minute rule) still online, Fall 2026 version (20-minute) | Spring 2023; 2026-09-30 | None specific found |
| Los Angeles | Paper frame | GIS layers only from 2024 (a district clip) and 2026; no 2023 layer | 2024-02-21 (clip); 2026 | Information items and project cases; no map or code adopted |
| Palo Alto | Paper frame | PDF map only (3 Caltrain stations) | June 2023 (archived copy 2023-12-19) | Council 2024-11-12, 7-0 to apply AB 2097 by the attached radius map; PC 2024-05-29, 2024-07-10 |
| Santa Cruz | Paper frame | PDF map only (Coastal Commission exhibit) | Commission hearing 2024-03-15 | Parking-code amendment; city adoption date not found |
| Rancho Cordova | Paper frame | No map found (light-rail buffer layer not labelled AB 2097) | | None found |
| Roseville | Paper frame | No map found | | None found |
| South Lake Tahoe | Paper frame | No map found | | None found |
| San Jose | Paper frame (placebo: 2023 repeal) | No map found | | Repeal hearings 2022; adopted 2023-01-10, effective 2023-04-10 |
| Fresno | Paper frame | No map found | | None found |
| Merced | Paper frame | No map found (one site refused our user agent) | | None found |
| Irvine | Paper frame | No map found | | None found |
| Beverly Hills | Paper frame and opposed | No map found | | Council first reading 2025-10-28 limiting street-parking permits for AB 2097-type projects |
| San Clemente | Paper frame | No map found (staff proposed one 2026-06-17; tabled) | | HCD technical-assistance letter 2023-11-17 |
| Santa Clarita | Opposed | No map found; code section on parking near major stops (date not confirmed) | | Council staff report 2022-03-22 recommended opposing the bill |
| San Marcos | Opposed | No map found | | Resolution 2022-9100 (agenda 2022-12-13) delegating the "findings" exception to staff |
| Rancho Palos Verdes | Opposed | No map found | | None found |
| Torrance | Opposed | No map found | | None found |
| San Francisco | Placebo | No map found (none needed) | | None found |
| Emeryville | Placebo | No map found (none needed) | | None found |

**Regional map:** SACOG publishes a dated AB 2097 map (2025-12-12, replacing a 2022-09-23 draft on the 2020 plan),
which SACOG calls illustrative. MTC publishes major-stop layers; no sampled city cites them.

**Counts:** 21 cities. GIS layer: 4 (Sacramento, Truckee, Oakland, Los Angeles). PDF map only: 2 (Palo Alto,
Santa Cruz). No map found: 15. Usable dated 2023 layers: Oakland Spring 2023 and Sacramento (created 2023-02-03,
drawing date unclear). Licences: not stated on any city layer found; to be recorded before any download.

**Status of facts in this file (audit 2026-11-05):** the summary table rests on primary pages read (city layers,
agendas, staff reports, Coastal Commission exhibits). Items in the notes that came only from search-result snippets
or news summaries (marked as such there, for example Palo Alto vote counts from local news and Santa Clarita's code
section from a third-party summary) are **leads only**, not facts, until a primary source is read.

Personal staff usernames and emails were removed from the notes (audit); item IDs and URLs are kept.

## Full notes by group

---

### AB 2097 city map leads: Los Angeles, Beverly Hills, Rancho Palos Verdes, Torrance, Santa Clarita, Irvine

Researched 2026-11-05. Web research only. Only metadata (item records, layer JSON) was read; no geometry was queried.
All curl calls sent `User-Agent: missing-middleware-research/1.0 (public data)`.
Shared regional source for all six cities (SCAG region). These are SCAG ArcGIS Online items, last modified 2026-05-11. Licence text starts "provided by SCAG for general planning and informational purposes only…".
- Major Transit Stops, base year 2022: https://maps.scag.ca.gov/scaggis/rest/services/OpenData/Major_Transit_Stops_Plan_Year_2022/MapServer/0
- Major Transit Stops, plan year 2050: https://maps.scag.ca.gov/scaggis/rest/services/OpenData/Major_Transit_Stops_Plan_Year_2050/MapServer/0
- TPAs (AB 2553), plan year 2050: https://maps.scag.ca.gov/scaggis/rest/services/OpenData/TPA_AB2553_Planyear2050_boundary_scag_RDP/MapServer/0

Wayback note: the availability API worked for a first batch of URLs. Later the CDX call returned "Temporarily Offline", and a retry got HTTP 429 (rate-limited). I did not retry again. As a result, the ZIMAS layer was not checked in the archive for 2023.

---

### Los Angeles
(Already known items were not redone: the 2026 "AB2097_clip" polygon, the 2022-12-29 and 2023-10-23 memos, the 2024-04-16 transit methodology memo, the HCD letters, and the empty ZIMAS group.)
- Classification: **GIS layer found (usable)**. The usable layer is the 2026 LADCP layer already known. I found no earlier citywide city layer. The only earlier layer is a LADOT Council District 1 clip from 2024 (below).
- Map, new leads only:
  1. **LADOT "CD1_AlFresco_AB2097_3_WFL1"**, a Feature Service. https://services1.arcgis.com/tp9wqSVX1AitKgjd/arcgis/rest/services/CD1_AlFresco_AB2097_3_WFL1/FeatureServer . Item f58430c356bb43c3981fd91075a26d2f, owner: a staff account (name removed). Item created and modified 2024-02-21.
     - Layer 6 is `Area_within_Half_Mile_MajorTransitStop_CD1Clip`. Its editingInfo.lastEditDate is 2024-02-21 14:17. Fields are OBJECTID, Id, and shape only, with no source attribute.
     - Layer 1 is `LACounty_Parcels_AB2097_CD1_Clip`, the parcels flagged as AB 2097-qualifying.
     - The item snippet says "half-mile buffer from nearest major transit stop, parcels that qualified for AB 2097".
     - It covers **Council District 1 only** and was made for the Al Fresco dining program.
     - Related items: web map 9af772f04d804ff0ac334c5516969077 (modified 2024-07-10) and StoryMap "Al Fresco Interactive Tool" https://storymaps.arcgis.com/stories/f49ae1247c914dc1a7b7b1f522613aa8 (modified 2024-06-12).
     - Licence/terms: not stated.
     - The source of the buffer is not stated. It may be a clip of the citywide area then in ZIMAS, but this is not confirmed.
  2. **LADCP items, all from 2026 and all owned by one staff account (name removed)** (org tzwalEyxl2rpamKs). An org search for "2097" returned only these 4 items, so no 2023 version is on ArcGIS Online.
     - "AB2097": https://services1.arcgis.com/tzwalEyxl2rpamKs/arcgis/rest/services/AB2097/FeatureServer . Created 2026-03-02. Layer 1 is `AB2097_VanNuysCBDCDO`, last edit 2026-03-12. This is a **Van Nuys CBD CDO clip only**. Access information: "Southern California Association of Governments (SCAG)". Licence not stated.
     - "AB2097 Exempts parking minimums within a half mile of major transit": https://services1.arcgis.com/tzwalEyxl2rpamKs/arcgis/rest/services/AB2097_Exempts_parking_minimums_within_a_half_mile_of_major_transit/FeatureServer . Created and modified 2026-03-18. Access information: SCAG.
     - Item 2ef629e3a13e41dfaf148d5d040ab539, created 2026-04-30. This is most likely the known "AB2097_clip".
     - Web map "Van Nuys Central Business District Map", 954af93212e241338966f675928cc39a, modified 2026-05-28.
     - The item text quotes PRC 21064.3 with "20 minutes or less", i.e. the AB 2553 rule.
  3. **ZIMAS** has a parcel field, not a public layer. The city's AB 2097 page tells users to open "Planning and Zoning" and read the "AB 2097 Eligibility" field.
     - The REST group `zma/zimas/MapServer/1500` "AB 2097 Entitlement Areas" has subLayers [] and description "New Group Layer". This confirms the known finding.
     - Older versions of the city page are archived at the Wayback Machine. Monthly snapshots exist for 2023-07-09, 2023-08-01, 2023-09-27, 2023-11-06, 2023-12-07, 2024-04-21 and 2024-07-15, plus a 301 redirect on 2025-08-05. Example: http://web.archive.org/web/20231207162052/https://www.planning.lacity.org/project-review/assembly-bill-2097 . The snapshot body came back empty to curl and was not read.
     - The case-filings list is archived at 20231130042804 and 20240415035802.
     - The ZIMAS REST directory is archived at 20221115151111, before the law took effect. No 2023 layer snapshot was checked because of the 429.
  - Date: 2024-02-21 (LADOT CD1 clip); 2026-03-02 to 2026-04-30 (LADCP). Form: GIS layer, plus the ZIMAS web viewer field.
- Regional map relied on: SCAG. The LADCP items credit SCAG in their access information, and the 2024-04-16 memo (already known) adopts SCAG's stop method. URLs are in the header.
- Public hearing(s) on AB 2097:
  - **2022-08/09, City Council, CF 22-0002-S117.** A resolution to put support for AB 2097 in the City's 2021–22 State Legislative Program. Resolution: https://cityclerk.lacity.org/onlinedocs/2022/22-0002-S117_reso_8-26-22.pdf . Public comments are dated 2022-08-26 to 2022-09-21; neighborhood councils were split. Final council vote: not found, because the lms.lacity.gov file page renders by JavaScript and came back empty. This is before the law took effect.
  - **2023-01-18, West Los Angeles Area Planning Commission.** An AB 2097 overview was given in the Senior City Planner's report, information only. Per a search snippet of the minutes, the full discussion is available as audio. The minutes are at https://planning.lacity.gov/dcpapi2/meetings/document/73831 , which returned HTTP 403 to fetch.
  - **2023-08-23, City Planning Commission.** Approved a project that the City then found ineligible because it relied on a planned stop. Source: HCD letter 2023-11-17 (already known). This was a project hearing, not an AB 2097 policy item.
  - **Nov 2023, South LA Area Planning Commission.** Appeal of case ZA-2023-1767 (Crenshaw Blvd). The appellant's filing cites the 2023-10-23 memo, per a search snippet. Outcome not found.
  - **2025-08-26, Council PLUM Committee, CF 25-0642** (Blumenfield/Raman/Yaroslavsky). A motion to report on removing off-street parking minimums citywide, framed as going beyond AB 2097. Vote 3-1. Report: https://cityclerk.lacity.org/onlinedocs/2025/25-0642_rpt_PLUM_s_08-26-25.pdf . Council action record dated 2025-09-18 lists the PLUM report as adopted: https://cityclerk.lacity.org/onlinedocs/2025/25-0642_ca_09-18-25.pdf . The vote tally was garbled in the extract. This was a report request; no map was adopted.
  - No council or CPC hearing that adopted an AB 2097 map or code amendment was found.
- Interpretation notes:
  - The city first treated planned RTP stops as not eligible (Aug–Nov 2023). It reversed after the HCD letters; a 2024-03-29 determination counts planned RTP stops.
  - The current page lists the three "substantially negative impact" findings and a 30-day timeline. No use of the findings was found.
  - Eligibility is per parcel in ZIMAS.
- Checked:
  1. Current city page https://planning.lacity.gov/project-review/assembly-bill-2097 (curl, 200; links to ZIMAS, the Oct 2023 memo, and the case filings).
  2. ArcGIS Online searches "Los Angeles AB 2097" and "AB2097"; LADCP org search (orgid tzwalEyxl2rpamKs, "2097 OR parking OR major transit"); LADOT org search; https://zimas.lacity.org/arcgis/rest/services (folders zm4, zma; layer 1500 read).
  3. Searches for council/CPC AB 2097 items; cityclerk.lacity.org documents for 22-0002-S117 and 25-0642; lms.lacity.gov pages (empty); planning.lacity.gov meeting documents 73831, 74695 and CP-7855 (all 403).
  4. SCAG, as above.
  5. Wayback availability API and CDX for the city page, ZIMAS REST and case filings (CDX for ZIMAS offline, then 429).
  6. Searches "Los Angeles City Council AB 2097 parking hearing 2023" and "Los Angeles parking "major transit stop" City Planning Commission AB 2097 staff report".

### Beverly Hills
- Classification: **No map found**
- Map: none found. Date: not found. Licence/terms: not stated.
- Regional map relied on: not stated.
- Public hearing(s) on AB 2097:
  - **Oct 2024 (exact date not found), City Council.** Discussion about limiting preferential parking permits for projects with reduced parking. Staff were directed to draft an ordinance (Beverly Hills Courier 2024-10-06 and BH Weekly).
  - **Mar 2025 and Jun 2025, Traffic and Parking Commission.** Reviewed the conceptual program (Courier 2025-06-29).
  - **2025-10-28, City Council.** Unanimously approved the first reading of an ordinance that bars preferential parking permits for residents of new projects with fewer on-site spaces than code requires. AB 2097 is cited as the reason (Beverly Press, https://beverlypress.com/2025/10/beverly-hills-will-restrict-parking-for-new-affordable-housing/). Second reading and ordinance number not found. No AB 2097 map is mentioned. This is a permit-side response, not a code amendment adopting AB 2097.
  - 2022 council position on the bill: not found.
- Interpretation notes:
  - The code uses the PRC 21064.3 definition for SB 9 parking exemptions (BHMC 10-3-2615 and 10-3-2419).
  - City documents name La Cienega/3rd St as a major transit stop, and the Metro D Line La Cienega/Wilshire station as under construction (search snippets from a project description and an SCPE findings document).
  - Planned-stop treatment: not found.
- Checked:
  1. beverlyhills.org pages surfaced by search (Density Bonus Guidelines, Housing Element redline, project documents); BHMC 10-3-2615 and 10-3-2419 via search.
  2. https://gis.beverlyhills.org/arcgis/rest/services, 56 services across all folders. Only zoning and parking-meter layers; no transit or AB 2097 layer. Open data `OD/OpenData_BeverlyHillsGeoHub` has City Boundary, Trees, Bike Racks and Generalized Landuse. ArcGIS Online searches "Beverly Hills transit", "Beverly Hills parking", "Beverly Hills major transit": none relevant.
  3. Searches for council/commission AB 2097 items; Courier and Beverly Press articles; BH Weekly 2024 issue 1307 (only a letter to the editor mentioning AB 2097).
  4. None stated.
  5. Wayback: planning page snapshot 20231103105532 (https://www.beverlyhills.org/departments/communitydevelopment/planning/); GIS REST only 2015.
  6. Searches "Beverly Hills AB 2097 map" and "Beverly Hills parking "major transit stop" AB 2097 planning commission".

### Rancho Palos Verdes
- Classification: **No map found**
- Map: none found. Date: not found. Licence/terms: not stated.
- Regional map relied on: not stated.
- Public hearing(s) on AB 2097: none found. The Legislation Corner and archive pages surfaced by search do not mention AB 2097.
- Interpretation notes:
  - The ADU code (Ordinance 628; draft Chapter 17.10, 2024) waives ADU parking within ½-mile walking distance of a "public transit" stop. It defines that as a stop served by LA Metro or PV Peninsula Transit Authority. This is ADU law, not AB 2097.
  - The draft code cites PRC 21155 for "major transit stop" in the ADU height rule.
  - No AB 2097 section was found.
- Checked:
  1. rpvca.gov search results (Parking Programs, ADU drafts, Ordinance 628, housing element pages).
  2. ArcGIS Online RPV org (orgid ujpK9Y5GvE6XyZF1) searched for 2097/parking/transit/TPA/HQTA/TOD; 31 hits, all parks or the 2018–19 "Citywide Parking Plan" for preserves. gis.rpvca.gov/arcgis/rest/services returned 404.
  3. Searches "rpvca.gov AB 2097 OR major transit stop staff report" and "Rancho Palos Verdes Assembly Bill 2097 city council legislative".
  4. None stated.
  5. Wayback: https://www.rpvca.gov/LegislationCorner has no snapshot.
  6. Searches "Rancho Palos Verdes AB 2097 parking" and "Rancho Palos Verdes "major transit stop" housing element parking".

### Torrance
- Classification: **No map found**
- Map: no AB 2097 layer found. Possibly related but not AB 2097:
  - Torrance org layers `Quarter_Mile_Walkshed`, `Housing_Corridors`, `Tor_transit_system_wgs` and `Torrance_Transit_Bus_Stop` (item 448ab0e292e94f8ebc4dd832d99c9b4d, modified 2025-08-20), at https://services1.arcgis.com/38fAqAZVRCrVtPUU/arcgis/rest/services .
  - Date: not found. Licence: not stated.
- Regional map relied on: not stated.
- Public hearing(s) on AB 2097: none found.
- Interpretation notes: none found.
- Checked:
  1. Searches for a Torrance code "major transit stop" definition and housing element AB 2097 mentions (no hits).
  2. https://services1.arcgis.com/38fAqAZVRCrVtPUU/arcgis/rest/services: about 250 services listed; no 2097, parking-exempt, TPA or HQTA names.
  2. https://gis.torranceca.gov/server/rest/services: folders only; public services are empty; the portal needs a token, which was not attempted.
  2. ArcGIS Online searches "Torrance AB 2097", "Torrance transit stop", "Torrance parking", "Torrance major transit", "Torrance transit priority": nothing relevant.
  3. Searches "Torrance city council planning commission 65863.2 OR AB 2097 staff report parking" and ""Torrance" "Assembly Bill 2097"": no hits.
  4. None stated.
  5. Wayback: planning page snapshot dates from 2021-04-30 only (http://web.archive.org/web/20210430065426/https://www.torranceca.gov/our-city/community-development/planning).
  6. Searches "Torrance AB 2097 map" and "Torrance parking "major transit stop" AB 2097 city council".

### Santa Clarita
- Classification: **No map found**. No AB 2097 map was found.
- Map:
  - The city's REST server has layers "Half-Mile Walking Distance from Local Bus Stops" (layer 14) and "Half-Mile Buffer from Local Bus Routes" (layer 9) at https://maps.santa-clarita.com/arcgis/rest/services/Transportation/MapServer .
  - They have no description, edit date or licence text. They are labelled for local bus stops and are not tied to AB 2097. My guess is ADU "public transit" use, but this is not confirmed.
  - Date: not found.
- Regional map relied on: not stated.
- Public hearing(s) on AB 2097:
  - **2022-03-22, City Council, Consent Calendar Item 5.** Staff recommended the Council oppose AB 2097 (with SB 897 and SB 1067), following the Council Legislative Committee on 2022-03-08. Report: https://santaclarita.gov/home/showpublisheddocument/20940/637836281774930000 (4 pages, no map). Outcome: not found; minutes not checked.
  - Code: SCMC §17.51.060(N)(4) "Parking Within One-Half (1/2) Mile of a Major Transit Stop". Per a search snippet, it says city standards "may not be imposed" within ½ mile, keeps the state findings exceptions, and says a permit "does not run with the land".
  - The adopting ordinance and hearing date were not found. ecode360 https://ecode360.com/48595826 returned 403, and the citation comes from a third-party summary.
- Interpretation notes:
  - The 2022 staff report lists three existing Metrolink stations (Via Princessa, Santa Clarita, Newhall) **and the future Vista Canyon station** as major transit stops, plus three bus corridors.
  - It describes the area as "one-half mile walking distance", but that was the bill as introduced, which included high-quality transit corridors.
  - Code-era measurement and the treatment of planned stops: not found.
- Checked:
  1. santaclarita.gov documents (AB 2097 staff report and bill text); the ecode360 Chapter 17.51 page (403).
  2. https://maps.santa-clarita.com/arcgis/rest/services: 47 services across all folders; only the layers above are transit-related; no 2097 names.
  2. ArcGIS Online searches "Santa Clarita AB 2097", "Santa Clarita transit stop", "Santa Clarita parking", "Santa Clarita major transit": nothing from the city.
  3. Searches "santaclarita.gov "AB 2097" parking planning commission" and the "Parking Within One-Half Mile…" code search.
  4. None stated.
  5. Wayback: https://santaclarita.gov/planning/ snapshot 20231206210935; the REST Transportation MapServer has no snapshot.
  6. Searches "Santa Clarita AB 2097 map" and "Santa Clarita parking "major transit stop" AB 2097 unified development code".

### Irvine
- Classification: **No map found**
- Map: none found. Date: not found. Licence/terms: not stated.
- Regional map relied on: not stated. OCTA and SCAG are the likely sources, but no city statement was found.
- Public hearing(s) on AB 2097: none found.
- Interpretation notes:
  - No AB 2097 section or "major transit stop" definition was found in the Irvine zoning code.
  - An older IBC Vision Plan EIR names Irvine Station (Metrolink) and the Tustin Metrolink station as serving the area, per a search snippet.
- Checked:
  1. Searches for Irvine code and housing element mentions of AB 2097 or "major transit stop": no hits.
  2. https://gis.cityofirvine.org/arcgis/rest/services, 106 services across all folders: only parks and lighting matched.
  2. ArcGIS Online Irvine org (orgid 3mkVbLdbLBFHrfbK) searched for 2097/parking/transit/TPA/HQTA/TOD: 110 hits, all parks, Great Park, zoning or parcels.
  2. ArcGIS Online searches "Irvine AB 2097" and "Irvine transit stop/priority": none from the city.
  3. Searches "cityofirvine.org "AB 2097" parking planning commission staff report" and ""Irvine" "Assembly Bill 2097" city council OR planning commission": no hits.
  4. None stated.
  5. Wayback: REST directory snapshot 20221115151055; https://www.cityofirvine.org/community-development/planning has no snapshot.
  6. Searches "Irvine AB 2097 map" and "Irvine parking "major transit stop" AB 2097 zoning code".

---

## Summary
- **Los Angeles:** The only usable map is the 2026 LADCP layer, sourced from SCAG. The earliest machine-readable city layer found is LADOT's 2024-02-21 Council District 1 clip ("Area_within_Half_Mile_MajorTransitStop_CD1Clip"). No 2023 layer was found on ArcGIS Online, and the ZIMAS group layer is empty.
- **LA hearings:** I found no hearing that adopted an AB 2097 map or code. There was a West LA APC information item (2023-01-18), project hearings on planned stops (CPC 2023-08-23; South LA APC appeal, Nov 2023), and the citywide CF 25-0642 (PLUM 2025-08-26, council 2025-09).
- **Santa Clarita:** City Council staff recommended opposing AB 2097 on 2022-03-22. The report listed a future station (Vista Canyon) as a major transit stop. The code now has §17.51.060(N)(4); its adoption date was not found. No AB 2097 map was found.
- **Beverly Hills:** City Council passed a first reading on 2025-10-28 restricting street parking permits for AB 2097 projects. No map was found.
- **Rancho Palos Verdes, Torrance, Irvine:** No AB 2097 map, hearing, or code section was found. Their GIS directories and ArcGIS Online orgs have no AB 2097 layers.

---

### AB 2097 city map leads — coast group
Cities: San Clemente, San Marcos, Santa Cruz, San Francisco (placebo), Emeryville (placebo).
Research date: 2026-11-05. Web research only. No GIS features or permit data downloaded.

### San Clemente
- Classification: **No map found**. A map was *proposed* in June 2026 but not adopted or published.
- Map: none published. The 2026-06-17 Planning Commission staff report, Attachment 1, "Option 7: Publish Map of Reduced Parking Areas", proposes a parcel map. https://www.sanclemente.gov/AgendaCenter/ViewFile/Item/2323?fileID=13950 (PDF, Attachment 1, section VII, Option 7). Date: not found (no map exists yet). Form: none. Licence/terms: not stated.
- Regional map relied on: not stated. The city is in the SCAG region. SCAG's public layers exist, for example "Major Transit Stops … base year 2022", https://maps.scag.ca.gov/scaggis/rest/services/OpenData/Major_Transit_Stops_Plan_Year_2022/MapServer/0 (item modified 2026-05-11). The city does not cite it.
- Public hearing(s) on AB 2097:
  - 2026-06-17, Planning Commission. "Gateway Overlay and Economic Development Initiatives – Draft Report". Option 7 proposes publishing an AB 2097 map. Staff recommendation: give feedback and "table the item to a date uncertain". Outcome: information/feedback only. No map adopted. No later hearing found.
  - 2023-11-17, HCD letter (state, not a hearing). HCD Housing Accountability Unit technical-assistance letter to the city's Community Development Director: https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/HAU/san-clemente-ta-ab2097-hau459-111723.pdf. It concerns an applicant's ADU conversion (project address omitted). HCD says to measure ½ mile as a **straight line from the nearest parcel edge** to any point on the transit-stop parcel, **not walking distance**. It also says San Clemente Pier Metrolink station qualifies under PRC 21064.3(a). Context: in the coastal zone the city has no fully certified LCP, so the Coastal Commission also reviewed parking.
  - No AB 2097 code amendment found.
- Interpretation notes:
  - Staff wrote that it "is not expressly clear as to what constitutes a major transit stop", which is why they proposed a map.
  - The staff report text lists the PRC 21155 definition, including "transit stops that are included in any applicable regional transportation plan". So planned RTP stops are named, but no map applies them.
  - Hotels are noted as excluded.
  - No findings exemption found.
- Checked:
  1. City page and code. Zoning Chapter 17.64 parking, via third-party mirrors (zoneomics, gocodebook); no AB 2097 or "major transit stop" text found. No city AB 2097 web page found.
  2. GIS. City ArcGIS Online org `services3.arcgis.com/x68DaqVkReQwi0Vd` services directory (150 services). It has parking/LCP layers (LCP_parking_and_TDM_study_area, Parking_AGO, Housing_Overlay_Zone, Zoning…) but no AB 2097, transit-stop, TPA or HQTA layer. ArcGIS Online search "San Clemente AB 2097" returned 0. "San Clemente parking" returned only a consultant parking-occupancy study (crassociates, 2025).
  3. Agendas. Web search of the sanclemente.gov AgendaCenter. Grepped six 2026 PC/council/ZA documents (Items 2284, 2264, 2230, 2272, 2211, 2251); none mention AB 2097 except item 2323 above.
  4. Regional map: none cited.
  5. Wayback for the item 2323 PDF and the Planning page: no snapshots.
  6. Searches "San Clemente AB 2097 map" and "San Clemente parking \"major transit stop\"": no city map. Extra searches found the June 2026 staff report and the HCD letter.

### San Marcos
- Classification: **No map found** (for AB 2097). A related SB 79 ordinance relies on SANDAG's SB 79 map. That map is not an AB 2097 map.
- Map: none for AB 2097. Date: not found. Form: n/a. Licence/terms: not stated.
- Regional map relied on: for AB 2097, not stated. For the city's SB 79 TOD ordinance (Draft SMMC Ch. 20.800, Legistar TMP-2467 Exhibit E, PDF created 2026-06-08), "Transit-oriented development stops" are those on SANDAG's "most current Map of Transit-Oriented Development Stops and Zones": https://www.sandag.org/draftsb79todmap (draft released 2026-06-18 per SANDAG/news; final status not found). The same chapter says auto parking follows Ch. 20.340 "to the extent not preempted", citing Gov. Code 65863.2. Exhibit: https://sanmarcos.legistar.com/View.ashx?M=F&ID=15565263&GUID=9360C691-8E8C-4740-BDB6-514429BF74A3
- Public hearing(s) on AB 2097:
  - **2022-12-13, City Council**, agenda item 11. "ADOPT Resolution … Delegating to and Authorizing the City Manager and/or Planning Division Director to Make Determinations and Findings Relating to … AB 2097, AB 2011, and SB 6". Legistar matter TMP-1822, later titled "RESOLUTION 2022-9100". The resolution delegates the power to make the AB 2097 written findings (the 65863.2(b) "negative impact" exception) to the City Manager/Planning Director (Zoning Administrator). Draft text: https://legistar2.granicus.com/sanmarcos/attachments/f70f2324-8204-4229-9c01-d845dceb6647.pdf. Outcome: resolution number 2022-9100 was assigned, but no vote record or minutes were found in the Legistar API.
  - 2026-06-15, Planning Commission. SB 79 TOD Alternative Plan (TA26-0001). The ordinance text defers to AB 2097 for parking. It is not an AB 2097 map. Agenda: https://www.sanmarcosca.gov/files/assets/city/v/1/boards-and-commissions/planning-commission/agendas/6152026-agenda.pdf. Outcome: not confirmed.
- Interpretation notes:
  - The resolution recital says the city's zoning ordinance has no "provisions relating to parking requirements within a half-mile of transit". The city therefore applies AB 2097 directly, with a delegated **findings escape hatch**. No use of the findings was found.
  - The Housing Laws page says the city cannot require parking for housing near "bus stops or train stations" (no map).
  - Major stops are not listed for AB 2097. The SB 79 ordinance lists the four SPRINTER stations: Palomar College, San Marcos Civic Center, CSU San Marcos, Nordahl Road.
- Checked:
  1. https://www.sanmarcosca.gov/Resident-Services/Housing/Housing-Laws (AB 2097 text, no map). Title 20 / Ch. 20.340 via search; no AB 2097 section found.
  2. GIS. City ArcGIS org (owner SMCGISAdmin, `services1.arcgis.com/e7Mp0AHrN8K5Kx6X`, 53 services). No transit/TPA/AB 2097 layer; only Railroad and Park. Hub site https://gis-sanmarcos.hub.arcgis.com. The city server `maps2.san-marcos.net/smgispub/rest/services` returned no response. ArcGIS Online "San Marcos AB 2097" returned 0. SANDAG `geo.sandag.org/server/rest/services/Hosted` lists no AB 2097 layer; "Transit_Priority_Areas" there is City of San Diego only.
  3. Agendas. Legistar API (client `sanmarcos`): matters with "2097" in the title found TMP-1822. Event 1153 (2022-12-13) item 11. Parking-titled matters 2022–2026 had nothing else relevant.
  4. Regional map: SANDAG, for SB 79 only (above).
  5. Wayback: Housing-Laws page earliest closest snapshot 2026-01-08 (http://web.archive.org/web/20260108080535/https://www.sanmarcosca.gov/Resident-Services/Housing/Housing-Laws). No 2023 copy found.
  6. Searches "San Marcos AB 2097 map" (results mixed with San Marcos TX; no map) and "San Marcos California parking \"major transit stop\"" (no city source). Extra: Streetsblog "SB 79 Deconstructed: San Marcos" (2026-07-20).

### Santa Cruz
- Classification: **PDF map only**
- Map: California Coastal Commission, LCP-3-STC-23-0047-2 Part C (Parking Updates), Exhibits. "Exhibit 2: Map of AB 2097 Applicability in the City of Santa Cruz Coastal Zone", PDF page 22 of 22: https://documents.coastal.ca.gov/reports/2024/3/F13c/F13c-3-2024-exhibits.pdf
  - The map shows "Transit Stops", a "One-half Mile Buffer", the city boundary and the coastal zone boundary on an aerial base.
  - Date: not printed on the map. The exhibit packet is for the 2024-03-15 hearing; the staff report was prepared 2024-02-23.
  - Form: PDF image (raster). Licence/terms: not stated.
  - Staff report: https://documents.coastal.ca.gov/reports/2024/3/F13c/F13c-3-2024-report.pdf (it calls Exhibit 2 "a map of the City's major transit stops to which the one-half mile buffer has been applied").
- Regional map relied on: not stated. The AMBAG region would be the relevant one. No AMBAG major-stop layer was found on ArcGIS Online.
- Public hearing(s) on AB 2097:
  - City adoption of the parking code amendment. The amendment adds SCMC 24.12.220(1)(b), "development within one half-mile of a Major Transit Stop", and 24.22.530, which defines Major Transit Stop by PRC 21155. Adoption date and ordinance number: not found. The LCP amendment was filed complete 2024-02-13.
  - 2024-03-15, California Coastal Commission (state body). De minimis LCP amendment determination reported. The staff report recommends approval; final vote record not checked.
  - 2025-08-26 (approx.; Lookout article dated 2025-08-27 says "Tuesday"), City Council. Unanimous resolution directing staff to re-examine development parking/transport impacts in response to AB 2097. Information/direction only.
  - 2026-05-12, City Council. Accepted staff recommendations: explore excluding certain new multifamily projects from residential permit parking; plan lines; objective standards (citizenportal summary). Direction only.
  - 2026-09 (exact date not found; citizenportal article dated 2026-09-25), City Council. Introduced an ordinance making projects that use state law to reduce/eliminate parking ineligible for residential permit parking. Second reading/adoption not found.
- Interpretation notes:
  - The code uses the PRC **21155** definition, so planned RTP stops are included in principle.
  - The code keeps the lodging exclusion and the 65863.2(b) findings route ("where the city is authorized to enforce minimum auto parking requirements pursuant to subdivision (b)").
  - The Exhibit 2 buffers are drawn around individual stops. They include many UCSC campus stops plus Mission St, Soquel Ave/Water St and Metro Center/Laurel St.
  - Coastal Commission staff: the only qualifying stop inside the coastal zone is Metro Center/Laurel St. West Cliff and Seabright are outside the buffer.
  - Map source/author not stated (it appears to be city-supplied for the LCP submittal; not confirmed).
- Checked:
  1. City code. codepublishing Ch. 24.12 returned 403. Code text was taken from the Coastal Commission exhibit. City doc https://cityofsantacruz.prod.govaccess.org/home/showpublisheddocument/98267/638418114758370000 (a search snippet describes it as the parking ordinance proposal reflecting AB 2097) refused the connection. The same document on santacruzca.gov returned 403.
  2. GIS. City ArcGIS org `services5.arcgis.com/RjgxPpXv8MHiv19f` (owner: cruzgis and a staff account (name removed), 156 services). Only Downtown_Parking_District, ResParkingView, CoSCZoning and Zoning_Overlays; no AB 2097/transit/TPA layer. Hub https://data1-cruzgis.opendata.arcgis.com. Guessed city ArcGIS Server hosts (gis.cityofsantacruz.com etc.) gave no response. ArcGIS Online "Santa Cruz AB 2097" returned only **SJSU student** layers (owner: a university student account (removed), e.g. https://services8.arcgis.com/A76GjgcBUTTcwFGS/arcgis/rest/services/Major_Stops___1_2_Mile_Radius_WFL1/FeatureServer, modified 2024-04-25). These are not city maps.
  3. Agendas. The city is not on the Legistar API (clients tried: santacruz, cityofsantacruz, santacruzca). Used news (Lookout 2025-08-27; citizenportal 2026-05-14 and 2026-09-25, the latter 403) and Coastal Commission records.
  4. Regional map: none cited.
  5. Wayback: the govaccess doc 98267 (three URL variants) and the CCC exhibit PDF had no snapshots.
  6. Searches "Santa Cruz AB 2097 map" (no direct hit) and "Santa Cruz parking \"major transit stop\"" (county CEQA transit map only). Extra searches found the CCC F13c report.

### San Francisco (placebo: no minimums citywide since 2019-01-21)
- Classification: **No map found**
- Map: none. Date: not found. Form: n/a. Licence/terms: not stated.
- Regional map relied on: not stated. Public MTC layers exist:
  - "San Francisco Bay Region Major Transit Stops": https://services3.arcgis.com/i2dkYWmb4wHvYPda/arcgis/rest/services/cdot_br_hq_transit_stops_apr2026/FeatureServer (item modified 2026-09-03; based on Caltrans High Quality Transit Stops).
  - "Transit Priority Areas (April 2026)": https://services3.arcgis.com/i2dkYWmb4wHvYPda/arcgis/rest/services/transit_priority_areas_2026/FeatureServer (modified 2026-09-16).
  - Licence on both: "made available to the public solely for informational purposes" (Caltrans disclaimer text).
- Public hearing(s) on AB 2097: none found.
- Interpretation notes / treatment of AB 2097:
  - No city AB 2097 page, map, code amendment or hearing was found.
  - The 2022 Senate analysis of AB 2097 cites San Francisco's 2018 elimination of parking minimums as a model.
  - AB 2097 appears to have needed no local action. That is an inference: no city source says so.
- Checked:
  1. sfplanning.org searches for "2097": no Planning page found.
  2. ArcGIS Online "San Francisco AB 2097" returned 0. "SF Planning major transit" found no SF Planning layer. `sfplanninggis.org` REST directories returned no JSON. DataSF (Socrata catalog API) "major transit stop", "AB 2097", "transit priority" returned 0 results.
  3. Legistar API (client `sfgov`): matter titles with "2097", "AB 2097", "Assembly Bill 2097" or "major transit" returned no AB 2097 items (only unrelated 2002–2013 communications). Search for a Planning Commission AB 2097 item found none (closest: 2023-04-28 Housing Element implementation briefing, no AB 2097 mention seen).
  4. Regional: MTC layers above (city does not cite them).
  5. Wayback for sfplanning.org/state-housing-laws: no snapshot.
  6. Searches "San Francisco AB 2097 map" and "San Francisco parking \"major transit stop\"": no city source.

### Emeryville (placebo: no minimums citywide, effective 2020-05-21)
- Classification: **No map found**
- Map: none for AB 2097. Date: not found. Form: n/a. Licence/terms: not stated.
  - The city has a non-AB 2097 layer, "General Plan Resources Transit Hubs" (buffered circles around 2 city Transit Hubs): https://services3.arcgis.com/ljOdqLVbHpS7dOJQ/arcgis/rest/services/General_Plan_Resources_Transit_Hubs_View/FeatureServer (created 2024-09-02, modified 2025-04-14; licence not stated). It is a General Plan "Major Transit Hub" designation, not AB 2097.
- Regional map relied on: not stated. The MTC layers listed under San Francisco cover Emeryville.
- Public hearing(s) on AB 2097: none found.
  - Background, pre-AB 2097: 2019-08-26 council study session on eliminating minimum parking (ID-2019-435). Planning Commission hearing reported for 2019-10-24 (ID-2019-503). Ordinance amending Planning Regulations Article 4 Ch. 4 "To Eliminate The Minimum Parking Requirements" (ID-2020-102, intro 2020-03-17).
- Interpretation notes / treatment of AB 2097:
  - No city AB 2097 page, map or hearing was found.
  - The city had already removed minimums citywide (Wikipedia notes the repeal plus parking maximums), so AB 2097 appears to have needed no local action. That is an inference: no city source says so.
- Checked:
  1. emeryville.org search for "2097": only an unrelated 2010 lease memo.
  2. City ArcGIS org `services3.arcgis.com/ljOdqLVbHpS7dOJQ` (194 services): Transit_Stop_8ft_Buffer (2023), Transit Hubs, Zoning_View, Traffic_Signs_Parking_Limits; no AB 2097/TPA layer. ArcGIS Online "Emeryville AB 2097" returned 0.
  3. Legistar API (client `emeryville`): titles with "2097", "AB 2097", "Assembly Bill 2097" returned 0. "major transit" returned only 2024–2025 Planning Commission items naming the "Major Transit Hub" General Plan class.
  4. Regional: MTC (city does not cite it).
  5. Wayback for www.emeryville.org/1180/Planning-Building: no snapshot.
  6. Searches "Emeryville AB 2097 map" and "Emeryville parking \"major transit stop\"": no city source.

## Summary
- **Santa Cruz** is the only city with an actual AB 2097 map: a PDF image, Coastal Commission LCP-3-STC-23-0047-2 Part C, Exhibit 2, p. 22, for the 2024-03-15 hearing. It shows ½-mile buffers around individual stops, including UCSC campus stops. The code adopts the PRC 21155 definition.
- **San Clemente** has no map. Staff *proposed* one on 2026-06-17 because the term is unclear; the item was tabled. HCD's 2023-11-17 letter to the city sets straight-line, parcel-edge measurement.
- **San Marcos** has no AB 2097 map. Council delegated the AB 2097 findings escape hatch to staff (Resolution 2022-9100, agenda 2022-12-13). The 2026 SB 79 ordinance relies on SANDAG's SB 79 TOD map, not an AB 2097 map.
- **San Francisco and Emeryville (placebos)**: no AB 2097 map, page or hearing found. Both had removed minimums before 2023. MTC regional layers exist but neither city cites them.

---

### AB 2097 city map leads: Oakland, Palo Alto, San Jose, Fresno, Merced

Research date: 2026-11-05. Read-only, web only. Only metadata (service directories, layer JSON, item records) was read with curl. No features or geometry were queried.
Sites that refused our research user agent (HTTP 403): paloalto.gov / cityofpaloalto.org, records.sanjoseca.gov, imaginemerced.com. These were recorded and skipped; no other headers were tried.

### Oakland
- Classification: **GIS layer found (usable)**
- Map:
  - (a) Current city layer: https://services.arcgis.com/9tC74aDHuml0x5Yz/arcgis/rest/services/NoParkingMinimumAB2097_Fall26/FeatureServer/0 (layer "NoPkgMinAB2097_2026Fall"). Date: `editingInfo.lastEditDate` = 2026-09-30. The description says "Last update: Sept. 28, 2026 using Fall 2026 AC Transit shapefiles". ArcGIS item d397e2e354fc42e89d4c9d88552de203 was created and modified 2026-09-30. Form: GIS layer (polygon). Licence/terms: none stated. Credit text: "AC Transit GIS Portal … with input from Owen Goetze Oakland Planner at AC Transit. Oakland Planning & Building Department".
  - (b) Public web map "DRAFT AB2097 No Parking Minimums": item 16a2b4cd144b4d938405ec047ace7fd3, created 2023-05-01, modified 2026-09-30. It now points to layer (a). The app is item e29ce512e2084cc58add5cc9946440f3, created and modified 2023-05-01: https://oakgis.maps.arcgis.com/apps/instant/basic/index.html?appid=e29ce512e2084cc58add5cc9946440f3
  - (c) Same layer in the city's own server: https://gismaps.oaklandca.gov/server/rest/services/Planning_and_Zoning_Controls/MapServer/24 "Parking Reduction Near Major Transit (AB2097)". Its description matches (a) (20-minute threshold). No edit date is shown. Licence: not stated.
  - (d) **Older 2023 version** (still online): https://gisapps1.mapoakland.com/oakgis/rest/services/Prod/CEDA_App_PRODGIS/MapServer/22 and http://gisapps1.mapoakland.com/oakgis/rest/services/Prod/CEDA_report_PRODGIS_June2024/MapServer/18. The description says "based on major transit stops as of Spring 2023", with a 15-minute threshold. Credit text names an AC Transit staff member (name removed). No edit date in the JSON. Licence: not stated.
  - Related city layers that may help a comparison (not AB 2097): BARTandHighFrequencyStops2025 (modified 2025-08-12), BARTandHighFrequencyStops2026 (2026-09-30), TransitAccessibleAreas_2025 / _2026, and "No Parking for ADUs". All are in the same org (services.arcgis.com/9tC74aDHuml0x5Yz).
- Regional map relied on: not stated. The city layer is built from AC Transit stop data, not from an MTC map. The MTC regional layers exist (see Palo Alto) but Oakland does not cite them.
- Public hearing(s) on AB 2097: none found that was specific to AB 2097.
  - Planning Code Title 17 (supplement effective 2024-01-16) has a "Major transit stop" definition tied to PRC 21155, with a 15-minute threshold. The 2023 Phase 1 General Plan Update code package was adopted 2023-10-03 (Ord. 13763 C.M.S., effective 2023-10-30). Whether that package added the definition: not confirmed.
  - No council or Planning Commission item adopting the AB 2097 map was found.
- Interpretation notes:
  - Covered area = "within one-half mile distance from major transit stops". That covers rail/BRT, ferry terminals served by bus or rail, and intersections of 2 or more bus routes.
  - The bus threshold changed: 15 min in the Spring 2023 layer, 20 min in the Fall 2026 layer (after AB 2553).
  - Whether planned RTP stops are included: not stated.
  - How distance is measured (buffer from stop point vs. parcel edge): not stated.
  - Use of the findings exemption: not found.
  - The map keeps the word "DRAFT" in its title.
- Checked:
  1. Planning Code Title 17 PDF (oaklandca.gov and cao-94612 S3 copy effective 2024-01-16); Phase 1 GPU code amendments page.
  2. ArcGIS Online search "Oakland AB 2097", "Oakland major transit stop", owner: a staff account (name removed), orgid 9tC74aDHuml0x5Yz "parking"; layer JSON for (a), (c), (d).
  3. Search for PC/Council staff reports (PC 2024-04-03 ADU/clean-up report; Phase 1 GPU 2023); Legistar 22-0606 (affordable housing parking, not AB 2097).
  4. MTC layers (none cited by the city).
  5. Wayback availability (timestamps 2023, 2024, 2025) for the gisapps1 layer 22, the oakgis app, and the gismaps layer 24: no snapshots. The Phase 1 page has a snapshot dated 2025-06-26.
  6. Web searches "Oakland AB 2097 map" and "Oakland parking "major transit stop"".

### Palo Alto
- Classification: **PDF map only**
- Map:
  - (a) "Map of AB2097 radii", cited in the PTC staff report of 2023-11-08: www.paloaltoonline.com/news/reports/1686780169.pdf. The live URL now returns 404. Wayback copy dated 2023-12-19: http://web.archive.org/web/20231219025537/https://www.paloaltoonline.com/news/reports/1686780169.pdf. The map came with the June 19, 2023 council informational report. Date: about June 2023 (exact map date not found). Form: PDF. Licence: not stated.
  - (b) "AB 2097 Boundary Map (PDF, 4MB)" is listed on https://www.paloalto.gov/Departments/Planning-Development-Services/Current-Planning/Ordinances-Maps-Guidelines-Standards. The direct file URL was not obtained: the site returned 403 to our user agent. Date not found.
  - (c) "Attachment B – AB2097 Map" in the Council packet of 2024-08-12 (item postponed) and 2024-11-12. URL not obtained.
  - No city GIS layer was found. The Planning and Transportation folders on gis.cityofpaloalto.org/server/rest/services return "Token Required" (499).
- Regional map relied on: the Downtown Housing Plan Community Assessment Report (2025-06-05) says MTC "Transit Priority Areas" define where AB 2097 applies. The council-adopted radius map is the city's own. Public MTC layers: "Transit Priority Areas (2026)" https://services3.arcgis.com/i2dkYWmb4wHvYPda/arcgis/rest/services/Transit_Priority_Areas_(2026)/FeatureServer and "San Francisco Bay Region Major Transit Stops" https://services3.arcgis.com/i2dkYWmb4wHvYPda/arcgis/rest/services/cdot_br_hq_transit_stops_apr2026/FeatureServer (modified 2026-09-03; the Caltrans data note says data are informational only).
- Public hearing(s) on AB 2097:

  | Date | Body | Item | Outcome |
  |---|---|---|---|
  | 2022-10-24 and 2022-11-14 | Council (NVCAP item) | AB 2097 summary | Information only |
  | 2023-06-19 | Council | Consent item 43, AB 2097 informational report | Information only |
  | 2023-11-08 | PTC | State-law informational report, includes handout | Information only |
  | 2024-04-24 | PTC | Study session | Discussion only |
  | 2024-05-29 | PTC | Title 18/21 ordinance with AB 2097 language | Recommended to Council, except §18.52.040(d) (loading space) |
  | 2024-07-10 | PTC | Continued AB 2097 discussion | Not found |
  | 2024-08-12 | Council | Ordinance item, with Attachment B AB2097 map | Postponed to a date uncertain |
  | 2024-11-12 | Council | Ordinance first reading | 6-1. Separate votes: 7-0 to "apply AB 2097 within the transit radius depicted in Attachment B" (map adopted as direction); 6-1 to base ADA/EV spaces on the full pre-AB 2097 requirement; motion to table failed 3-4. Source: Palo Alto Civic and theboringparts summaries, not official minutes |
  | 2024-12-16 | Council | Reintroduced first reading | Not found |
  | 2025-02-03 | Council | ADA/EV spaces | 7-0 for "option one": ADA/EV spaces based on parking provided voluntarily; ordinance to return on consent (Palo Alto Civic summary) |

- Interpretation notes:
  - Covered stops: Downtown (University Ave), California Ave and San Antonio Caltrain stations.
  - The Downtown radius accounts for the offset bus transit centre next to the University Ave station.
  - As of January 2023, staff found no bus intersection meeting the 15-min test.
  - Covered = property "within the shaded radius circles".
  - Staff said the findings exemption is not expected to be used unless Council directs otherwise.
  - The PTC retail item (2024-08-14) notes 16 CD-C parcels just outside the Downtown radius and a proposal to extend the exemption to the whole CD-C zone (outcome not found).
  - Planned RTP stops: not stated.
- Checked:
  1. paloalto.gov ordinances/maps page (via fetch tool; curl got 403); PTC 2023-11-08 report; PTC 2024-07-10 report; PAMC 18.52 draft text.
  2. gis.cityofpaloalto.org REST directory (Planning, Transportation: token required); ArcGIS Online "Palo Alto AB 2097" and "Palo Alto transit" (only 2018 third-party SB 827 maps).
  3. Council/PTC agendas via Midpen Media, Palo Alto Civic and city PDFs.
  4. MTC TPA and major transit stop layers.
  5. Wayback: the paloaltoonline radius PDF has a snapshot dated 2023-12-19.
  6. Web searches "Palo Alto AB 2097 map" and "Palo Alto parking "major transit stop"".

### San Jose
- Classification: **No map found** (for AB 2097). Parking minimums were repealed citywide, so an AB 2097 map is not needed locally.
- Map: no AB 2097 layer or PDF found. Nearest city layer: "Major Transit Stops Half-Mile Buffer" at https://geo.sanjoseca.gov/server/rest/services/PLN/PLN_LandDesignations/MapServer/32.
  - Its description ties it to AB 2011/SB 6 (2024 updates), not AB 2097. It treats only BART, Caltrain and VTA stations as major transit stops.
  - Edit date: not shown. Copyright text: "PBCE, Department of Public Works". Licence: not stated.
  - The same service has layer 46 "High Quality Transit Stops" (GTFS from January 2020 plus Plan Bay Area 2050 planned stops; under-16-minute headway).
  - The Geocortex service has "Transit Hub (Half Mile)" (layer 205).
- Regional map relied on: not stated for AB 2097. Layer 46 uses Plan Bay Area 2050 (MTC) planned stops.
- Public hearing(s) on AB 2097: none found that was specific to AB 2097. Hearings on the citywide parking-minimum repeal (PP22-015, Ord. 30857):

  | Date | Body | Item | Outcome |
  |---|---|---|---|
  | 2021-08-27 | Council | Study session | Discussion |
  | 2022-06-08 | Planning Commission | Policy direction | Recommended 5-2-3 |
  | 2022-06-14 | Council | Policy direction (file 22-916) | Directed staff to draft citywide removal |
  | 2022-11-16 | Planning Commission | Item 5.b | Recommended approval 9-0-1 |
  | 2022-12-06 | Council | Item 8.3(a), file 22-1876 | Passed for publication, unanimous |
  | 2023-01-10 | Council | Final adoption (file 23-007) | Ord. 30857 adopted; effective 2023-04-10 |

  News (San José Spotlight, 2022-09-29) quotes staff saying AB 2097 "will likely apply to much of the city". No staff map was found.
- Interpretation notes: the citywide repeal goes beyond AB 2097, so no AB 2097 map or findings are needed. The AB 2011 buffer counts rail stations only. The HQTS layer includes planned RTP stops.
- Checked:
  1. sanjoseca.gov parking/TDM page (via fetch tool; earlier WebFetch got 403); Municode 2023 ordinance list.
  2. geo.sanjoseca.gov/server/rest/services (PLN, DOT, CED, OPN, REF, HSG folders); layers 32 and 46; ArcGIS Online "San Jose AB 2097", "San Jose major transit stop", "San Jose parking minimum".
  3. Legistar 22-916, 22-1876, 23-007; PC 2022-11-16 staff report.
  4. MTC layers.
  5. Wayback: the parking/TDM page has a snapshot dated 2024-01-02.
  6. Web searches "San Jose AB 2097 map" and "San Jose parking "major transit stop"".

### Fresno
- Classification: **No map found**
- Map: none found. Date: not found. Licence: not applicable.
- Regional map relied on: not stated. Fresno COG (the MPO) publishes a "Transit_Stops" layer (modified 2024-11-06): https://services.arcgis.com/v2YXtBuIb8gr4ywi/arcgis/rest/services/Transit_Stops/FeatureServer. No major-transit-stop or TPA layer was found. HCD's AB 2097 advisory lists Fresno COG peak hours.
- Public hearing(s) on AB 2097: none found.
- Interpretation notes:
  - The Development Code (Municode Art. 24) has no AB 2097 or Gov. Code 65863.2 reference in the version seen.
  - §15-2413.B gives a 30% reduction within ¼ mile of a transit stop with 15-minute service (local rule, not AB 2097). Downtown districts require 0.5 space per unit for housing and none for non-residential uses.
  - Fresno has the "Q" BRT line, but no city statement was found on whether its stations count as BRT stations under PRC 21060.2.
- Checked:
  1. fresno.gov planning/parking page; planning documents index; Municode Article 24.
  2. gis4u.fresno.gov/arcgis/rest/services (DARM, Parking, FAX folders: no services listed publicly); gis.fresno.gov (301 redirect); ArcGIS Online "Fresno AB 2097", "Fresno major transit stop", "Fresno HQTA", "Fresno transit priority area", owner: a staff account (name removed).
  3. Web/Exa search of agendas.fresno.gov and fresno.legistar.com for AB 2097: no hits. The documents.fresno.gov WebLink needs cookies (not used).
  4. Fresno COG layers (above).
  5. Wayback: fresno.gov/planning/parking has a snapshot dated 2023-11-30 (no AB 2097 content seen in search snippet).
  6. Web searches "Fresno AB 2097 map" and "Fresno parking "major transit stop"".

### Merced
- Classification: **No map found**
- Map: none found. Date: not found. Licence: not applicable.
- Regional map relied on: not stated. No MCAG major-transit-stop or TPA layer was found.
- Public hearing(s) on AB 2097: none found.
  - Legistar file 23-536 (2023, a 54-unit affordable project) names the Amtrak station and the Transportation Center as "major transit stop[s]". The context is density bonus (AB 1763), not AB 2097. Meeting date and body not confirmed.
- Interpretation notes:
  - Zoning Ordinance Ch. 20.38 gives local reductions: up to 5% within 400 ft of a city-approved bus stop, 10% within 400 ft of a transit center, and up to 20% with a TDM plan (Housing Element constraints chapter, 2025).
  - The City Housing Element says parking reductions "will be tackled by new laws", without naming AB 2097.
- Checked:
  1. cityofmerced.gov zoning ordinance and planning pages; City Housing Element and constraints chapter (mercedmjhe.com).
  2. ArcGIS Online "Merced AB 2097", "Merced transit stop", "Merced TPA", "Merced high quality transit", owner: a staff account (email removed) (112 items; none on parking or transit), MCAGonline. A city ArcGIS REST host was not found (gis.cityofmerced.org did not respond).
  3. Web/Exa search of cityofmerced.legistar.com and granicus for AB 2097: only file 23-536.
  4. MCAG: nothing found.
  5. Wayback: zoning ordinance page has a snapshot dated 2025-08-06. imaginemerced.com refused our user agent (403).
  6. Web searches "Merced AB 2097 map" and "Merced parking "major transit stop"".

## Summary
- **Oakland**: usable city GIS layer, dated 2026-09-30, using AC Transit Fall 2026 data and a 20-minute threshold. An older Spring 2023 version (15-minute threshold) is still online. No hearing specific to AB 2097 was found.
- **Palo Alto**: PDF radius maps (June 2023, with a Wayback copy dated 2023-12-19) cover the 3 Caltrain stations. Council voted 7-0 on 2024-11-12 to apply AB 2097 within the Attachment B radius. PTC hearings were held 2024-05-29 and 2024-07-10.
- **San Jose**: no AB 2097 map. Parking minimums were repealed citywide (PC 2022-11-16; Council 2022-12-06; adopted 2023-01-10; effective 2023-04-10). The only close layer is an AB 2011/SB 6 rail-station buffer.
- **Fresno and Merced**: no AB 2097 map, hearing or code reference found. Only local transit parking reductions exist, and no regional major-transit-stop map is cited.
- Third-party layer to note (not city-made): "AB 2097 Eligibility Areas for ABAG SACOG SANDAG SCAG" (owner: an individual account (name removed), item f490bb51cb684aaf8a2b21edd6499fb9, modified 2023-12-15). It may cover the 3 Bay Area cities. The item record could not be read (no title returned).

---

### AB 2097 city map leads — Sacramento region and Tahoe/Truckee

Researched 2026-11-05. Read-only: web search, page reads, ArcGIS item/layer JSON metadata.
User-Agent sent on every curl: `missing-middleware-research/1.0 (public data)`.
Disclosure: one Sacramento attribute-only query (`returnDistinctValues`, `returnGeometry=false`) was sent by mistake. Its output was not used. No geometry was requested.

## Regional context: SACOG (covers Sacramento, Rancho Cordova, Roseville; not Tahoe Basin, not Truckee)
- **SACOG's current AB 2097 app:** "AB 2097 MTPSCS 2025 Major Transit Stops", an ArcGIS Experience.
  - URL: https://experience.arcgis.com/experience/eaa59e8a00cb42e3b49c715458b39743
  - Item created 2025-04-15, modified 2026-10-14. The description says "Map Updated Dec 12, 2025" and "Date Published: 12/12/2025".
  - Disclaimer: the map is "for illustrative purposes only" and "does not reflect the interpretation of any local government". Local governments make the final call.
  - Licence: SACOG "provides data as a public service… as-is", with no warranty and an indemnity clause.
  - There is also an "AB2097" Hub page (item d4654e5a3b174ef39a75a66030006592), created 2026-09-25 and modified 2026-10-14.
- **Web map behind the app:** "2025 MTP/SCS Existing and Planned Major Transit Stops" (item e4e7142f63494cdf9e48f95637d2a0a2), created and modified 2026-01-23, tagged AB2097. It shows ½-mile buffers around existing and planned stops in the 2025 MTP/SCS.
- **2025 layers:**
  - Planned 2050 buffer: https://services.sacog.org/hosting/rest/services/MTP_SCS/Major_Transit_Stops_Half_Mile_Buffer_Planned_2050/FeatureServer (item 42de0c3878a24ec2992483ae77e8aba5). Item created 2025-12-11, modified 2025-12-15. Description says "Adopted November 20th 2025". The layer JSON has no `editingInfo`.
  - Planned 2035 buffer: https://services.sacog.org/hosting/rest/services/MTP_SCS/Major_Transit_Stops_Half_Mile_Buffer_Planned_2035/FeatureServer (item 6c7b8fac60dc4c7bb97c8daffbadabcb), modified 2025-12-15.
  - Existing stops come from Caltrans data: SACOG items 7a912a3f4a72441dadfb4ce6126cb606 and 1907e8f236474bae98db1b09cee95c38. Both point to https://caltrans-gis.dot.ca.gov/arcgis/rest/services/CHrailroad/CA_HQ_Transit_Areas/FeatureServer and .../CA_HQ_Transit_Stops/FeatureServer.
  - Wording differs between layers. The 2050 buffer says "15 minutes or less". The Existing_Major_Transit_Stops and 2025 Blueprint layers say "20 minutes or less", the post-AB 2553 test.
- **Earlier SACOG AB 2097 map (2020 MTP/SCS):**
  - App: "2020 MTP/SCS Existing and Planned Major Transit Stops", https://sacog.maps.arcgis.com/apps/webappviewer/index.html?id=9df1c17713e546feb905c5d3493a3ea3 . Description says "Date Published: 09/23/2022" and calls it a "draft map". Item created 2024-09-24, modified 2024-12-18. Tagged AB2097.
  - Web map a795f96413954db09a32d954bf051312, modified 2025-01-06.
  - Planned 2040 buffer: https://services.sacog.org/hosting/rest/services/Transportation/2020_MTP_SCS_Planned_Major_Transit_Stops__2040__Half_Mile_Buffer/FeatureServer (item 40c0ba695c1c47cfa37c3546b61a3b92), modified 2024-12-18.
  - Also https://services.sacog.org/hosting/rest/services/Hosted/2040_Major_Stops_Half_Mi_Buffer/FeatureServer (item 73d179cb72114731b91296a8c5a8390c), modified 2024-12-20.
  - No Wayback copy of the 2020 app was found.
- **Other SACOG layers with similar names:**
  - In https://services.sacog.org/hosting/rest/services/Transportation : 2025_Blueprint_Planned_Major_Transit_Stops, 2025_Blueprint_Transit_Priority_Areas, 2025_Blueprint_High_Frequency_Transit_Areas, Existing_Major_Transit_Stops(_2020), Major_Transit_Stop_SB743_SACOG and Major_Transit_Stop_Half_Mile_Area_SB743.
  - SB_79_Transit_Oriented_Development_Stops/Zones are for SB 79, not AB 2097.
  - None of these layers' JSON has `editingInfo`. Item modified dates run from 2026-05 to 2026-07.
- **SACOG housing legislation page:** https://www.sacog.ca.gov/planning/land-use/housing/housing-legislation . It returned HTTP 403 to WebFetch. A Wayback copy exists: http://web.archive.org/web/20231201161618/https://www.sacog.org/planning/land-use/housing/housing-legislation .
- **SACOG/major-transit-stops on GitHub:** MIT licence, created 2025-04-11, last push 2026-02-18. The README is one line ("Scripts related to identifying and creating layers of major transit stops…").
- **Third-party layer (not a city map):** "AB 2097 Eligibility Areas for ABAG SACOG SANDAG SCAG" by an individual account (name removed), modified 2023-12-15. URL: https://services5.arcgis.com/kXdJ0DN2OncA9tPy/arcgis/rest/services/AB_2097_Eligibility_Areas_for_ABAG_SACOG_SANDAG_SCAG/FeatureServer
- **Outside SACOG:**
  - South Lake Tahoe is in the Tahoe Basin. Its MPO is TRPA/TMPO, not SACOG.
  - Truckee is in Nevada County. Nevada County is not in the SACOG region.
  - The SACOG 2025 web map draws a "SACOG Planning Area" boundary layer.

---

### Sacramento
- Classification: **GIS layer found (usable)**
- Map:
  - Layer: https://services5.arcgis.com/54falWtcpty3V47Z/arcgis/rest/services/AB_2097_Parking/FeatureServer/0 . Item 12110af6dd4641f38e25b3a92df9366d, "AB 2097 Parking", owner Publisher_SacCity, public. Tags: CDD, Planning, Parking, LILA.
  - Dates: item created 2023-02-03. Item modified 2026-11-05, and layer `editingInfo.lastEditDate` is 2026-11-05 13:36 UTC. The service appears to be republished often (other Publisher_SacCity layers also show 2026-11-05), so the last-edit date is not the date the coverage was set.
  - Fields: PROXIMITY_TYPE, STOP_INFORMATION and editor fields.
  - Form: GIS layer. Licence/terms: not stated (empty licenseInfo and copyrightText).
  - Viewer named in the memo: https://www.arcgis.com/apps/webappviewer/index.html?id=6f8e021cb286482b9a649e33ac6e67ea . Its item no longer exists ("Item does not exist or is inaccessible"). Wayback copy: http://web.archive.org/web/20240616033540/https://www.arcgis.com/apps/webappviewer/index.html?id=6f8e021cb286482b9a649e33ac6e67ea .
- Regional map relied on: not stated. The city's layer is its own.
- Public hearing(s) on AB 2097:
  - None found on AB 2097 itself.
  - Related item: the Planning and Design Commission heard the parking-revisions project (Parking Strategy) on 2024-11-14. Video: https://sacramento.granicus.com/player/clip/6107?view_id=34&meta_id=803512 . Outcome not found on the city page.
  - The 2040 General Plan, adopted February 2024 per the city page, ended off-street minimum vehicle parking citywide.
  - City page says staff plan an ordinance for the Commission and Council in spring/summer 2026.
- Interpretation notes:
  - City memo "History of Sacramento's Parking Mandates", dated 2023-08-14, author Ryan Dodge, Associate Planner.
    - URL: https://www.cityofsacramento.gov/content/dam/portal/cdd/Planning/parking-revisions/A-Short-History-of-Sacramentos-Parking-Mandates.pdf (Wayback 20240629).
    - It says "AB 2097 covers 46% of the land area of the city" (unit: share of city land area; numerator and denominator not given).
    - It links to the "AB 2097 Parking" layer.
    - A Comstock's article gives 44% instead. The city memo is the primary source.
  - Whether planned (RTP) stops are included: not stated. The layer's STOP_INFORMATION field may hold this; not checked.
  - Whether distance is measured from the parcel edge: not stated.
  - Findings exemption: none found.
  - Since the 2024 citywide repeal, AB 2097 has little practical effect here, but the layer still exists.
- Checked:
  1. City parking-revisions page https://www.cityofsacramento.gov/community-development/planning/housing/parking-revisions and the history memo PDF.
  2. ArcGIS Online search: "Sacramento AB 2097", "AB 2097 Parking", "AB2097", owner Publisher_SacCity. Layer JSON read.
  3. Web search of Granicus/Legistar for "AB 2097": no hits. City page hearing links.
  4. Regional reliance: none stated.
  5. Wayback: parking-revisions page 20240403170819; memo 20240629233358; viewer 20240616033540.
  6. Web searches "Sacramento AB 2097 map" and "Sacramento parking "major transit stop"".

### Rancho Cordova
- Classification: **No map found** (no map labelled AB 2097. A candidate city layer is listed below.)
- Map:
  - No AB 2097 map found.
  - Candidate layers: "Light Rail Stations Buffer HalfMile", https://maps.cityofranchocordova.org/externalarcgis/rest/services/EXTERNAL/External_Planning_Layers/MapServer/32 , and "Light Rail Stations Buffer QuarterMile" (layer 31).
  - Service: "Public facing Planning Viewer for the City of Rancho Cordova", copyright "City of Rancho Cordova".
  - The layers have no description and no date (no editingInfo). Licence/terms: not stated.
  - Nothing ties these layers to AB 2097. They may support the code's ¼-mile and ½-mile transit reductions below.
- Regional map relied on: not stated. SACOG's map covers the city.
- Public hearing(s) on AB 2097: none found.
- Interpretation notes:
  - Zoning Code §23.719.080(B)(3), "Reduction for Parking Near Major Transit Stops", allows a 25% reduction within ½ mile and 50% within ¼ mile. It lists "light rail stations, BRT stations, or significant bus facilities". (Read on gocodebook.com, 2026-10 edition, not the official code.)
  - The code does not cite AB 2097 or §65863.2.
  - Official code (codepublishing) is current through Ordinance 10-2024 (2024-10-21).
- Checked:
  1. City planning pages; municipal code Title 23 ch. 23.719 (gocodebook, codepublishing).
  2. REST directory https://maps.cityofranchocordova.org/externalarcgis/rest/services (EXTERNAL folder). ArcGIS Online search "Rancho Cordova parking/transit" and owner GISadmin_RanchoCordova (Zoning, Zoning Viewer only).
  3. Web search for agendas, cityofranchocordova.org "AB 2097": none.
  4. Regional reliance: not stated.
  5. Wayback: planning page 20240101100703 (no AB 2097 content checked beyond availability).
  6. Web searches "Rancho Cordova AB 2097 map" and "Rancho Cordova parking "major transit stop"".

### Roseville
- Classification: **No map found**
- Map: none found. Licence/terms: n/a.
- Regional map relied on: not stated. SACOG's map covers the city.
- Public hearing(s) on AB 2097: none found. (A Planning Commission item on 2026-03-27, PL26-0134, was an ADU code amendment and does not mention AB 2097.)
- Interpretation notes:
  - Parking chapter is Title 19 ch. 19.26 (ecode360). Its text was not reached.
  - A third-party summary (gocodebook) does not mention AB 2097, §65863.2 or "major transit stop". It mentions only ADU transit exemptions (§19.60.050).
- Checked:
  1. Planning page; Title 19 via gocodebook and ecode360 index.
  2. REST directory https://ags.roseville.ca.us/arcgis/rest/services : PublicServices folder. Layers checked: ReferenceData (bus stop, bus route), AdministrativeArea, PropertyInformationToolLayers. No transit buffer or AB 2097 layer. ArcGIS Online searches "Roseville AB 2097/transit/parking" and owner CityofRoseville: nothing relevant.
  3. Web search roseville.granicus.com / roseville.ca.us "AB 2097": none.
  4. Regional reliance: not stated.
  5. Wayback: planning page 20240102100748.
  6. Web searches "Roseville AB 2097 map" and "Roseville parking "major transit stop"".

### South Lake Tahoe
- Classification: **No map found**
- Map: none found for AB 2097. Licence/terms: n/a.
- Regional map relied on: not stated. The city is outside SACOG; its regional body is TRPA/TMPO.
  - TRPA has a "1/2 Mile from Transit" web map (item 8e1785a95e5c464a8d955db7332276b7, owner: a staff account (name removed), modified 2021-09-30).
  - Per its description, that map is for TRPA Residential Bonus Unit eligibility, not AB 2097.
  - TRPA also has a "Transit Hubs" layer (b7b3f01d2401497bba58adddd847501a, modified 2026-01-13).
- Public hearing(s) on AB 2097: none found.
- Interpretation notes:
  - City code (gocodebook summary) does not mention AB 2097, §65863.2 or "major transit stop". It mentions only the ADU waiver within ½ mile of transit (§6.85.050(H)(9)).
  - The Tourist Core Area Plan takes precedence over citywide rules where they conflict.
  - AB 2097 excludes hotel/motel projects, which may matter in a lodging-heavy city. Not addressed in any city document found.
- Checked:
  1. City code (gocodebook Title 6 / parking summary; codepublishing ordinance table).
  2. ArcGIS Online: searches "South Lake Tahoe transit stop/parking/zoning/city"; owner: a staff account (email removed), 284 items scanned for transit/2097/parking (only "Parking Restrictions" and plan-area layers); TRPA items.
  3. Web search slt.granicus.com / cityofslt.us "AB 2097": none.
  4. Regional reliance: not stated.
  5. Wayback: https://www.cityofslt.us/169/Planning gave no snapshot (the URL may not exist).
  6. Web searches "South Lake Tahoe AB 2097 map" and "South Lake Tahoe parking "major transit stop"".

### Truckee
- Classification: **GIS layer found (usable)**
- Map:
  - Layer: "Train Depot 1/2mile buffer (AB2097)", https://services5.arcgis.com/i75zh9vlhYUpqwjr/arcgis/rest/services/TraiinDepot_AB2097/FeatureServer/0 (item fb52ef258c134d729cc2ec422907e846, public). One polygon layer, `editingInfo.lastEditDate` 2024-01-09 16:13 UTC, item created and modified 2024-01-09.
  - Shown in web map "Transit AB 2097 Map" (ea24c2a0a9a7412c825427f5a1fb351f; created 2024-01-09, modified 2024-03-20).
  - Also shown in StoryMap "Truckee AB 2097", https://storymaps.arcgis.com/stories/b2f3afe1613e4c3daa942268e6133b5d (created 2024-01-09, modified 2024-03-20).
  - Owner: a staff account (name removed).
  - Licence/terms: not stated. The StoryMap says it is "for informational purposes only" and that project proponents must show their location within ½ mile of the Train Depot.
- Regional map relied on: none; the Town drew its own. Truckee is not in SACOG.
- Public hearing(s) on AB 2097:
  - No policy hearing found.
  - Project-level mention: Planning Commission, 2024-09-17, Planning Application 2024-0000014 (Residences at Jibboom).
    - Staff said "the parking requirement is zero" and the Town "cannot impose a parking standard". The minutes cite "AB-27", probably a typo for AB 2097 (inference).
    - Resolution 2024-12 approved.
    - Minutes: https://mccmeetingspublic.blob.core.usgovcloudapi.net/truckeeca-meet-40d50e620ef84636975f03e1ba71f532/ITEM-Attachment-001-c3151b0ad39a400cbb6d5cc5e42637af.pdf
- Interpretation notes:
  - The StoryMap says Truckee has one major stop, the Train Depot/Amtrak station. The buffer is ½ mile around it.
  - It quotes the 15-minute bus test (pre-AB 2553). No bus intersections are counted.
  - Planned stops: not mentioned. Distance measured from the station point or a footprint: not stated.
  - The web map also overlays active planning applications, which the StoryMap says are updated every six months or less.
- Checked:
  1. Town planning pages; Development Code search (no AB 2097 or major transit stop text found).
  2. ArcGIS Online search "Truckee transit" and owner: a staff account (name removed); layer and item JSON read.
  3. Town meeting documents (mccmeetingspublic blob) via web search; PC minutes 2024-09-17 read.
  4. Regional reliance: none (own map).
  5. Wayback: no snapshot of the StoryMap; https://www.townoftruckee.gov/1082/Planning gave none.
  6. Web searches "Truckee AB 2097 map" and "Truckee parking "major transit stop"".

---

## Summary
- **Own GIS layers (2 of 5 cities):** Sacramento and Truckee.
  - Sacramento: "AB 2097 Parking" layer, created 2023-02-03, republished often (last 2026-11-05). Its 2023-08-14 memo says it covers 46% of city land.
  - Truckee: one ½-mile Train Depot buffer, last edited 2024-01-09.
- **SACOG regional map:** public AB 2097 map, 2025 MTP/SCS version published 2025-12-12. It replaced a 2020 MTP/SCS draft dated 2022-09-23. It is "illustrative" and not endorsed by local governments.
- **No AB 2097 map (3 of 5 cities):** Rancho Cordova, Roseville, South Lake Tahoe. None states reliance on SACOG or TRPA.
  - Rancho Cordova has an unlabelled ½-mile light-rail buffer layer. Its code has its own transit reduction (§23.719.080(B)(3)).
- **Hearings:** no AB 2097 policy hearing found in any of the five cities. Truckee cited the law on one project (PC 2024-09-17). Sacramento's parking hearings (PDC 2024-11-14) concern the post-repeal parking strategy.
