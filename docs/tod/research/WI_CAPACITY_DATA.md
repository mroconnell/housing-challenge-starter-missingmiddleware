# Wisconsin capacity data for TOD method B: inventory (Gate 2, WP3)

Prepared 2026-10-26. All access dates are 2026-10-26 unless stated. Research only: nothing was added to the repo except this file. Test queries and downloads went to scratch (`/private/tmp/claude-501/wi_cap/`).

Method B (see [GATE1_PACKET.md](../GATE1_PACKET.md) and AQ-047 in [ASSUMPTIONS_AND_QUESTIONS.md](../../ASSUMPTIONS_AND_QUESTIONS.md)) needs, for land near qualifying stops: parcel area, land use, existing homes, current allowed density (height, units per acre or lot area per unit), land and improvement values, the Madison TOD overlay boundary, and Milwaukee zoning near CONNECT 1 and the Hop. It also needs building costs and rents for a mid-rise feasibility check.

Scale reminder from [MAJOR_TRANSIT_STOP.md](../MAJOR_TRANSIT_STOP.md), section 3: in the main case, the City of Milwaukee holds 55.2% and the City of Madison 25.3% of homes near stops, so the two cities hold 80.5% between them. The rest of Milwaukee County and Dane County holds another 16.7% (97.2% minus 80.5%). The suburbs therefore matter, but less than the two cities.

## 1. Summary table

"Automated" means a plain script (no browser, no login, no bot-check workaround) fetched data or a valid count from the source on 2026-10-26. Licence status follows the owner decisions in [DATA_COMPLIANCE.md](../../DATA_COMPLIANCE.md) (D1: government records with no licence are accepted as public records; D2: Internet Archive copies accepted with care; D6: hand-coded rules accepted as a documented manual step).

| Dataset | Use in method B | Coverage | Licence or terms | Automated | Size | Notes |
|---|---|---|---|---|---|---|
| Wisconsin V12 statewide parcels, REST (SCO / DOA) | Parcel outline and area, property class, land and improvement values | All 72 counties; 3,574,646 parcels | Public records (Wis. Stat. 59.72); "provided free of charge", no warranty | Yes (tested) | Milwaukee County 280,676 parcels; Dane County 218,857; about 1.8 KB per parcel as GeoJSON | No dwelling count, no zoning, no year built. Already used in repo (Dane and Kenosha pieces) |
| V12 statewide bulk file geodatabase | Same, in one file | Statewide | Same | Yes (HTTP 200 on HEAD) | 515.8 MB zip (compressed gdb); 759.9 MB zip (uncompressed gdb) | Needs GDAL to read .gdb. REST is easier for two counties |
| Milwaukee MPROP (in repo) | Homes (NR_UNITS), land use, lot area, zoning, values per tax key | City of Milwaukee; 159,950 records | CC BY (data.milwaukee.gov) | Yes (in repo) | 90.2 MB CSV | No geometry; joins to V12 PARCELID by TAXKEY (7 of 8 sampled keys matched) |
| Milwaukee zoning districts, layer 11 | Zoning district per parcel polygon | City of Milwaukee; 148,088 polygons, 52 district codes | CC BY (data.milwaukee.gov "zoning") | Yes (tested) | Shapefile zip 17.5 MB | Same codes as MPROP ZONING. Overlay layers (DIZ, IS, NC, SPROZ and others) are layers 3 to 10 |
| Milwaukee Zoning Code, ch. 295 (density and height tables) | Allowed units and height by district | City of Milwaukee | Public law | No live (city site returns a Cloudflare challenge, HTTP 403). Yes via Internet Archive copies (D2) | Subch. 5 PDF about 639 KB (capture 2025-03-24); subch. 6 about 471 KB (2025-03-23); subch. 7 about 353 KB (2025-08-09) | Hand-code 52 districts (D6). Captures may predate the 2025 Growing MKE amendments (new RT5 district); check Legistar |
| Madison tax parcels (in repo) | Homes (TotalDwellingUnits), use, lot size, zoning per parcel | City of Madison; 82,616 parcels | Not stated on service; public City GIS (D1) | Yes (in repo) | 101 MB GeoJSON | CurrentLand and CurrentImpr exist on the layer but were not requested; add them on the next fetch |
| Madison zoning districts, OPEN_DATA layer 9 | District polygons | City of Madison; 2,473 polygons | City open data terms | Yes (sample fetched earlier) | Small | Parcel layer already carries Zoning1 to Zoning4, so the polygons are optional |
| Madison Zoning District Summary (13 March 2026) | Max stories and max dwelling units per acre for every district; TOD overlay additions | City of Madison | Public record (D1) | Yes (tested, HTTP 200) | 162 KB, 6 pages | Official city summary; the cleanest single source for coding Madison |
| Madison TOD overlay boundary (in repo) | Which parcels are already at TOD rules | City of Madison | City open data terms | Yes (in repo) | 224 KB, 1 polygon | No attributes beyond area |
| Fitchburg zoning | District per area | City of Fitchburg; 10,431 polygons, 20 district codes | None stated (D1) | Yes (tested) | Small | Official city ArcGIS Online layer, edited 2026 |
| Middleton zoning areas | District per area | City of Middleton; 154 polygons | None stated (D1) | Yes (tested) | Small | Its "Zoning Height Limit" layer is airport zoning in feet above sea level (976 to 1,245), not a building height cap |
| Shorewood zoning and land use | District per parcel | Village of Shorewood; 3,522 parcels | "For use by the general public" | Yes (tested) | Small | Layer also holds owner names; never request those fields |
| Wauwatosa zoning ("Official Beta") | District per area | City of Wauwatosa | None found | No: server gis.wauwatosa.net timed out | Unknown | Found through the city's ArcGIS Online web map; retry later |
| West Allis, Greenfield, South Milwaukee, Cudahy, Whitefish Bay, Glendale, Monona zoning GIS | District per area | Each place | n/a | No: no official public layer found | n/a | Monona: only a vendor copy (not official). A "Milwaukee County Zoning" item on ArcGIS Online is a 2021 copy of City of Milwaukee zoning made by a private account; do not use |
| SCO statewide zoning V2 (2016) and V3 (2017) | None | County-administered general, shoreland, floodplain, farmland and airport zoning | Free | Yes | Not checked | Stale and does not cover city or village zoning near stops |
| National Zoning Atlas, Wisconsin | None for now | "In progress" for 1,922 jurisdictions; no counts published | Terms bar reuse, download and scraping without written permission | No | n/a | Not usable unless the owner gets written permission |
| HUD Unit Total Development Cost limits, 2024 | Hard and total cost per unit by building type and bedrooms | Milwaukee and Madison rows, among others | Public domain (U.S. government work) | Yes (PDF fetched); values parsed from PDF | 1.2 MB PDF | Built from RSMeans and Marshall & Swift averages, so it is the free route to RSMeans-based costs. 2025 or 2026 table not found at the same URL pattern |
| BLS PPI, inputs to residential construction (WPUIP2311001) | Inflate 2024 costs to 2026 and later | National | Public domain | Yes (API tested; September 2026 value 355.225, preliminary) | Tiny | Already in repo pipeline (`bls_ces_ppi`) |
| ACS 2020 to 2024 5-year B25064 median gross rent (in repo) | Market strength by tract | Every tract and place | Public domain | Yes (in repo, summary files) | 17.3 MB | Milwaukee County 302 tract rows, Dane County 125 |
| ACS B25111 median gross rent by year structure built | Rent of recent buildings, closer to new-build rent | Every tract and place | Public domain | Yes (HTTP 200 on HEAD) | 59.8 MB | Not yet in repo |
| HUD Fair Market Rents FY2026 | Rent floor check | Metro and county | Public domain | No: the xlsx returned HTTP 202 with an empty body (bot check), and the API needs a free token | Small | Owner could register for a token; Claude cannot create accounts |
| Census C30 value put in place | Not a unit cost; spending totals only | National | Public domain | Not tested: the Census API now redirects keyless calls to "missing_key" | Small | Low value for a feasibility check |
| WHEDA tax-credit budgets; Urban Institute pro forma | Local cost cross-check | n/a | n/a | No | n/a | No published per-unit cost dataset or open pro forma found |

## 2. Statewide parcels (V12)

**What it is.** The Statewide Parcel Map Initiative (Wisconsin DOA and the State Cartographer's Office) compiles county parcel files each spring. V12 was collected January to May 2026; most tax-roll values are for 2025. The next release, V13, is planned for 30 June 2027.

**Access.**
- REST: `https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/Wisconsin_Statewide_Parcels_DB/FeatureServer/0`, layer `V1200_WisconsinParcels_2026`, last edited 2026-06-30, 2,000 records per page, JSON, GeoJSON and PBF output. Spatial filters work: an envelope query around downtown Milwaukee returned 854 parcels.
- Bulk: `https://web.s3.wisc.edu/parcels/v12_parcels/V12.0.0_Wisconsin_Parcels_2026_10.3_Compressed.zip` (515,810,191 bytes) and the uncompressed version (759,926,092 bytes). SCO describes the full set as 3.56 million records and 1.6 GB. Per-county shapefile and .gdb downloads are linked from `https://www.sco.wisc.edu/parcels/data-county/`, but that page builds its links in JavaScript, so the REST service is the simpler county route.
- Terms: SCO states the data "is provided free of charge" and asks users to fill in a feedback form; no warranty. The repo already records it as public records under Wis. Stat. 59.72 and passes all compliance checks.

**Fields that matter.** PARCELID, PLACENAME, CONAME, PROPCLASS (1 residential, 2 commercial, 3 manufacturing, and so on), AUXCLASS, LNDVALUE, IMPVALUE, CNTASSDVALUE, ESTFMKVALUE, ASSDACRES, DEEDACRES, GISACRES, the polygon, and LATITUDE and LONGITUDE. There is **no dwelling-unit count, no zoning field and no year built**. Existing homes must come from MPROP (Milwaukee), the Madison assessor layer, or Census blocks elsewhere.

**Data quality found in test queries.**
- GISACRES is empty for all 218,857 Dane County parcels. Use ASSDACRES (missing for 59 of 81,652 Madison parcels) or compute area from the polygon.
- Shape__Area is in Web Mercator square metres, which overstates true area by a factor of about 1.87 at Wisconsin's latitude. A Madison parcel with 2,479 m² of Shape__Area has 0.33 assessed acres (1,335 m²). Always reproject to Wisconsin Transverse Mercator (EPSG:3071) before measuring.
- City of Milwaukee: 7,144 of 159,542 parcels (4.5%) have no land value and 8,046 (5.0%) have no property class. These are mostly exempt land. City of Madison: no parcel lacks a land value, and 13 lack a class.
- City of Milwaukee parcels by class: 142,308 residential, 8,675 commercial, 513 manufacturing.

**Counties with qualifying stops.** Parcel counts by county (REST, 2026-10-26): Milwaukee 280,676; Dane 218,857; Waukesha 164,715; Brown 105,679; Racine 84,569; Kenosha 68,499; La Crosse 54,142; Eau Claire 52,015. Any county can be fetched the same way with `CONAME='...'` plus a spatial filter, so later counties need no new code.

**Size.** The repo's Sun Prairie extract is 22.7 MB for 12,427 parcels, about 1.8 KB per parcel. Both whole counties (499,533 parcels) would be about 0.9 GB of GeoJSON. Filtering to the half-mile stop buffers should cut that to well under half, since the buffers cover a small share of each county's area.

## 3. Zoning

### 3.1 City of Milwaukee

**GIS.** `https://milwaukeemaps.milwaukee.gov/arcgis/rest/services/planning/zoning/MapServer/11` (Zoning) has 148,088 parcel-shaped polygons and fields Zoning, ZoningCFN, ZoningCategory and ZoningType. The data portal (`data.milwaukee.gov`, dataset "zoning") offers the same as a 17.5 MB shapefile, licensed Creative Commons Attribution. Layers 0 to 2 hold planned developments (PD, DPD, GPD), and layers 3 to 10 hold overlays. Layer 12 shows the downtown subdistricts.

MPROP (already in repo) carries the same 52 codes in its ZONING field, so for the city the GIS layer is needed only for outlines and overlays. The most common districts are RT4 (32,149 polygons), RS6 (30,953), RT3 (19,255), RT2 (17,585) and RS5 (15,004). No RT5 polygon appears yet.

**Code text.** Chapter 295 is published as PDFs on `city.milwaukee.gov`, but the site returned a Cloudflare challenge (HTTP 403) to plain scripts, as did Municode. The Internet Archive holds recent copies of each subchapter, which owner decision D2 allows. From the 24 March 2025 copy of subchapter 5 (Table 295-505-1) and the 23 March 2025 copy of subchapter 6 (Table 295-605-2):

| District | Minimum lot area per home (sq ft) | Equivalent homes per acre | Maximum height (ft) |
|---|---|---|---|
| RS1 to RS5 | One home per lot (minimum lot 20,000 to 6,000) | 2.2 to 7.3 | 45 |
| RS6 | 3,600 | 12.1 | 45 |
| RT1 | 3,600 | 12.1 | 45 |
| RT2 | 2,400 | 18.2 | 45 |
| RT3 | 1,800 | 24.2 | 45 |
| RT4 | 1,200 | 36.3 | 48 |
| RM1 | 2,400 | 18.2 | 45 |
| RM2 | 1,200 | 36.3 | 45 |
| RM3 | 2,400 (3 or more homes) | 18.2 | 45 |
| RM4 | 1,200 | 36.3 | 60 |
| RM5 | 800 | 54.5 | 60 |
| RM6 | 400 | 108.9 | 85 |
| RM7 | 150 | 290.4 | 85, or no limit if floor-area conditions are met |
| RO1 | 2,400 | 18.2 | 45 |
| RO2 | 400 | 108.9 | 85 |
| NS1 | 2,400 | 18.2 | 45 |
| NS2 | 1,200 | 36.3 | 60 |
| LB1 | 1,200 | 36.3 | 45 |
| LB2 | 800 | 54.5 | 60 |
| LB3 | 300 | 145.2 | 75 |
| RB1 | 1,200 | 36.3 | 85 |
| RB2 | 800 | 54.5 | 85 |
| CS | 1,200 | 36.3 | 60 |

Homes per acre is 43,560 square feet divided by the minimum lot area per home. The code allows smaller lot areas for permanent supportive housing; the table shows the standard figure.

Still to code: downtown C9 districts (subchapter 7, copy of 9 August 2025), industrial districts (subchapter 8), PD (site-specific, so treat existing use as the rule), and the overlays. The scaled-back Growing MKE zoning changes and a new RT5 district (5 to 8 homes) were approved in 2025 according to press reports; the date and text were not confirmed here, so the coded table must be checked against Legistar before use.

### 3.2 City of Madison

**GIS.** The repo already holds the tax parcels with Zoning1 and ZoningAll per parcel, and the TOD overlay boundary (`data/raw/madison_tod/tod_boundary.geojson`, one polygon). The district polygon layer is `https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA/MapServer/9` (2,473 polygons; only a sample is in the repo).

**Code rules.** The city's "Zoning District Summary" (`https://www.cityofmadison.com/development-services-center/documents/ZoningTable.pdf`, dated 13 March 2026, fetched by script) gives, for every district, the maximum number of stories and the maximum dwelling units per acre. Examples: TR-C1 2 stories and 8 to 17 homes per acre; TR-U2 6 stories and 14 to 124 homes per acre; NMX 3 stories and 87 homes per acre; TSS 3 stories and 124 homes per acre; CC-T 5 stories and 87 homes per acre; RMX 5 stories and no maximum density. Downtown districts take their height from the Downtown Height Map. Several districts allow extra stories with conditional use approval.

**TOD overlay (MGO 28.104, ORD-23-00013, adopted January 2023).** The same summary lists what the overlay adds:
- In the small residential districts (TR-R, SR-C1 to SR-C3, TR-C1 to TR-C3), 3 to 4 home buildings and townhomes become permitted; TR-C4 gains 4-home buildings.
- Larger buildings become permitted in the varied and urban districts (for example 25 to 36 homes in SR-V2 and TR-U1, 37 to 60 in TR-U2, and 61 to 100 home mixed-use buildings in CC-T).
- Maximum stories rise to 4 in SR-V2, TR-V2, NMX and TSS; 5 in TR-U2; 6 in CC; and 8 in RMX.
- It sets a 2-story minimum for non-residential and larger residential buildings, a 20-foot maximum setback, and no minimum parking.

The 3 to 4 home allowance in the small districts matches the "Housing Forward" amendment introduced on 28 October 2025. The March 2026 summary already shows it, which suggests it passed; confirm the ordinance number in Legistar. The Madison Municode page also returned a Cloudflare challenge, so the summary PDF is the practical source. Note that the "units per acre" ranges vary by building type; for capacity, use the top of each range for multifamily-permitted districts and the per-type lot areas in Chapter 28 if a finer split is needed.

### 3.3 Suburbs

Inner Milwaukee suburbs on MCTS routes: Wauwatosa publishes an official zoning layer through its ArcGIS Online web map (`gis.wauwatosa.net/geo/rest/services/Planning/Zoning/MapServer/0`), but the server timed out from here. Shorewood publishes a parcel layer with zoning ("For use by the general public"). No official public zoning GIS was found for West Allis, Greenfield, South Milwaukee, Cudahy, Whitefish Bay or Glendale; the West Allis GIS server returned 404 and the Milwaukee County Land Information Office REST service did not respond. Their codes would also have to be hand-coded from ecode360 or Municode, which have not been checked for script access.

Dane suburbs: Fitchburg (10,431 polygons, 20 districts, edited 2026) and Middleton (154 polygons) publish zoning on ArcGIS Online with no licence stated, which D1 covers. Monona has only an unofficial vendor copy.

### 3.4 Regional and statewide zoning

- **SCO statewide zoning (V2 2016, V3 2017):** county-administered general, shoreland, floodplain, farmland and airport zoning. It is out of date and does not cover cities and villages, which is where the stops are.
- **National Zoning Atlas:** Wisconsin is "in progress" (all 1,922 jurisdictions), with no completion counts. Its Terms of Use bar using, storing, downloading or distributing site content without written permission and bar scraping. Not usable without permission.
- **SEWRPC:** a regional zoning dataset could not be checked; the web search budget for this session ran out. SEWRPC does publish an ArcGIS Online layer "SE WI Transit Service Quality 2025", which may interest the transit work package.

## 4. Existing homes per parcel

**Milwaukee MPROP** (`data/raw/milwaukee_mprop/mprop.csv`, 159,950 records, 2026 assessment for 159,556 of them):
- `NR_UNITS` is present on 150,817 records and sums to 394,145. This total counts units of every kind: hotel rooms (land use 7011, 9,544 units) and commercial units are included. Residential land-use codes (those starting with 88) sum to 274,267 units. Filter by land use, and check the total against the ACS count of housing units for the city before use.
- `LOT_AREA` (square feet) is above zero on 151,039 records; `ZONING`, `LAND_USE`, `C_A_LAND` and `C_A_IMPRV` (current land and improvement values), `YR_BUILT`, `NR_STORIES` and `BLDG_AREA` are also present.
- No geometry: join TAXKEY to V12 PARCELID (7 of 8 sampled keys matched) or to the city's own parcel layer (`property/parcels_mprop/MapServer`, layers "MPROP_lite" and "MPROP_full").

**Madison assessor parcels** (`data/raw/madison_parcels/tax_parcels.geojson`, 82,616 parcels):
- `TotalDwellingUnits` is above zero on 68,010 parcels and sums to 137,002 homes. Condominium parcels (16,960) carry 15,808 of these; check for double counting between condominium notation parcels and unit parcels.
- `LotSize` (square feet), `PropertyUse`, `PropertyClass`, `Zoning1` and `ZoningAll` are in the repo. `CurrentLand` and `CurrentImpr` exist on the service but were not requested; add them, or take values from V12.

Everywhere else, homes come from Census 2020 blocks, as AQ-047 item 9 already plans.

## 5. Building costs and rents

**Costs.**
- **HUD Unit Total Development Cost limits, 2024** (`https://hud.gov/sites/dfiles/PIH/documents/2024_Units_TDC_Limits.pdf`, November 2024). HUD builds these from the average of RSMeans and Marshall & Swift costs, so they are a free, public-domain way to get RSMeans-based local costs. For a 2-bedroom home (900 square feet):

| Place and building type | Housing construction cost (hard cost) | Per sq ft | Total development cost | Per sq ft |
|---|---|---|---|---|
| Milwaukee, elevator | $206,727 | $230 | $330,764 | $368 |
| Madison, elevator | $204,973 | $228 | $327,957 | $364 |
| Milwaukee, walk-up | $177,122 | $197 | $309,964 | $344 |
| Madison, walk-up | $173,683 | $193 | $303,945 | $338 |

  The table is for modest public housing, so it may understate market-rate finishes and structured parking. It is a PDF, so values are parsed or typed with the URL and checksum recorded (the same manual-step flag as other PDF sources). The 2025 and 2026 tables were not at the same URL pattern (HTTP 404); look for the newer notice before Gate 3.
- **BLS PPI, inputs to residential construction (WPUIP2311001):** API works without a key; use it to move 2024 costs to the forecast years.
- **Census C30 (value of construction put in place):** spending totals, not cost per unit. Low value here. The Census API now needs a key for every call.
- **Wisconsin-specific:** no published WHEDA per-unit cost summary was found. A 2025 Marquette Lubar Center blog reports a median of $414,000 per home, excluding land, for 47 Minnesota tax-credit projects in 2024, and notes the author asked WHEDA for the same data. Useful only as a cross-check.
- **Urban Institute pro forma:** no open pro forma with cost inputs was found. RSMeans and CoStar are paid and are not used.

**Rents.**
- **ACS B25064 median gross rent** is in the repo by tract and place (2020 to 2024 5-year): City of Milwaukee $1,059 a month, City of Madison $1,413, Milwaukee County $1,101, Dane County $1,398. These cover all rented homes, most of them old, so they understate rents in new buildings.
- **ACS B25111 median gross rent by year structure built** (summary file, 59.8 MB, available) gives rents in buildings built since 2020 by tract or place, which is the better input for new-build feasibility.
- **HUD Fair Market Rents:** a useful floor (40th percentile of recent movers' rents), but the scripted download hit a bot check and the API needs a free token. The owner could register for one.

## 6. Recommended Gate 2 fetch plan (by 9 November)

**Minimum set to run method B in the two metros:**
1. **V12 parcels for Milwaukee and Dane counties** through REST, filtered to the union of the main-case stop buffers (half mile for rail and rapid, quarter mile for 15-minute bus, plus a margin). Request non-owner fields and geometry only. Reproject to EPSG:3071 and compute area from the polygon. One script, a few hundred 2,000-record pages. About 1 day.
2. **MPROP** (in repo): join on TAXKEY to V12 PARCELID; take residential units, LOT_AREA, ZONING, LAND_USE and values. Half a day.
3. **Madison parcels:** re-fetch with CurrentLand and CurrentImpr added; take TotalDwellingUnits, LotSize and Zoning1. Half a day.
4. **Milwaukee zoning layer 11 and PD and overlay layers** (CC BY), to flag PD and overlay parcels. Half a day.
5. **Two hand-coded rule tables** (D6), each row with a URL:
   - Milwaukee: 52 districts, with minimum lot area per home and maximum height, from the Internet Archive copies of Chapter 295 subchapters 5 to 8 (record capture dates and checksums), then checked against any 2025 Legistar amendments. One day.
   - Madison: about 35 districts, with maximum stories and maximum homes per acre, plus the TOD overlay columns, from the 13 March 2026 Zoning District Summary. Half a day.
6. **Costs:** HUD 2024 TDC rows for Milwaukee and Madison (elevator and walk-up), inflated with BLS PPI WPUIP2311001. **Rents:** ACS B25064 (in repo) plus B25111 by tract. Half a day.

That is about 4 to 5 working days, inside the 9 November target.

**Suburbs (16.7% of homes near stops):** use V12 parcels and Census block homes for them, and apply the fallback below unless Wauwatosa's layer comes back and can be coded in time. Fitchburg, Middleton and Shorewood can be added if there is time; each needs a small rule table.

**Later counties** (Eau Claire, Kenosha, Racine, La Crosse, Waukesha, Brown): same V12 query with a different county name. They matter only in the wider stop definitions.

## 7. Fallback if zoning cannot be coded in time

If the Milwaukee or Madison rule tables (or any suburb) are not ready by 9 November:
1. **Allowed density by broad class instead of district.** Group zoning codes (already on every Milwaukee and Madison parcel) into four classes: one and two family, small multifamily, mixed-use corridor, and downtown or no limit. Give each class one allowed density taken from the tables above (for example 36 homes per acre for Milwaukee's RT4 and RM2 class, 54 for LB2 and RM5, and Madison's printed maximum per acre for each class). This needs only a short lookup, not a full code reading.
2. **Where there is no zoning at all** (suburbs without GIS), use existing density near stops as the baseline headroom measure: homes per acre of eligible parcel land from Census blocks and V12 classes, as AQ-047 item 9 allows. Treat the law's allowed density as the target and the existing density as the starting point, and flag these places as "zoning not coded" in the tool.
3. **If even that is late,** follow the rule already in the Gate 1 packet: method B is cut to the two cities, and the rest of the state uses method A alone.

## 8. Blockers and open items

- **Script blocks:** the Milwaukee code site and Municode both return Cloudflare challenges. The Internet Archive route works for Milwaukee (D2). No workaround was attempted.
- **HUD FMR** needs a free API token, which only the owner can register for.
- **Wauwatosa and Milwaukee County LIO** servers did not respond; retry before deciding on the suburb fallback.
- **SEWRPC regional zoning** is unchecked because the web search budget for this session ran out; a follow-up search is needed.
- **Milwaukee 2025 zoning amendments** (Growing MKE, RT5) need checking against the Internet Archive copies.
- **Madison 2025 Housing Forward TOD changes** need the adopted ordinance number confirmed in Legistar.
