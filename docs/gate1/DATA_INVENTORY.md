# Gate 1 Data Inventory: Wisconsin ADU Pilot and Statewide ADU MVP

Checked: 2026-10-23. Status: Gate 1 data work package, prepared for coordinator integration and owner review. No data was acquired into the repository. Every access claim below comes from a live request made on the check date: a HEAD request, a metadata or API call, a count or statistics query, or a single report run. Where a source could not be reached, this document says so.

Related: [MVP Execution Plan](../MVP_EXECUTION_PLAN.md) (Gates 1–2), [Project Plan](../PROJECT_PLAN.md), [Assumptions and Questions](../ASSUMPTIONS_AND_QUESTIONS.md) (AQ-007, AQ-014, AQ-018), [Data Sources](../../data/DATA_SOURCES.md), and the existing dictionaries [wi_parcels](../data-sources/wi_parcels.md), [census_bps](../data-sources/census_bps.md) and [acs](../data-sources/acs.md).

## Bottom line

- **Madison: usable record-level permit data exists.** The city's public "Construction Summary" report has every issued building permit from 2010 to the present. It needs no login and exports to CSV. Each record has a permit number, use class, address, a dwelling-unit count ("Dwell"), a description and an issuance date. ADUs have no structured flag. They can be identified from the description text, which needs a manual audit. The yearly sums of "Dwell" track Census BPS closely for 2015–2025. ADU counts are in the [Madison table](#adu-permit-counts-from-the-description-text) below.
- **New Berlin: no record-level permit data is publicly accessible.** Its permit system, Tyler Munis Citizen Self Service, requires an account login and only lets a user look up a permit by its number. The public sources are:
  - Census BPS place totals (1980–2025, all 1-unit or 2-unit buildings in recent years).
  - One year of application counts in the 2025 Housing Affordability Report. These count applications, not issued permits.
  - Assessor building tables with year built and living units.

  None of these identifies family dwelling units (attached in-law units). Options are under [Option set for owner decision](#option-set-for-owner-decision).
- **The statewide foundation is available.** Sources:
  - Census BPS (counties, places and towns, through 2025 plus 2026 monthly).
  - ACS 2020–2024 5-year at tract and block-group level. The API now requires a key, but keyless summary files exist.
  - PEP Vintage 2025 housing units, at county level only.
  - TIGER 2026.
  - LTSB 2024 legislative districts.
  - Wisconsin V12 parcels: 3.57M parcels, public domain, a 516 MB statewide download.

  The main statewide gaps:
  - **No statewide source of municipal ADU ordinance status exists.**
  - **No statewide source identifies ADU permits.** BPS does not identify ADUs separately.
  - **V12 has no dwelling-unit or building-type field.**

## Coverage table

Status key:
- **OA**: observed available (checked live and fit for the stated use).
- **AC**: available with caveats.
- **M**: missing (checked; not publicly available).
- **U**: unknown (not reached or not yet checked).
- **n/a**: not applicable.

| Needed input | Madison | New Berlin | Statewide |
|---|---|---|---|
| Record-level issued building permits (ID, issue date, address, units, description) | **OA**: 2010–2026 YTD, CSV export | **M**: login-only portal | **M**: no statewide permit-record system |
| ADU identification in permits | **AC**: description keywords; no structured flag | **M** | **M**: BPS does not separate ADUs |
| Permit stages (application / issue / final) | **AC**: issuance date only in the public report; other stages are in Accela, not checked | **M**: HAR counts are applications | **AC**: BPS counts authorizations only |
| Annual units authorized (all types) | **OA**: BPS place 516500, 1980–2025; months reported <12 in 2010–2014, 2016 and 2017 | **OA**: BPS place 612500, 12 months reported in most years | **OA**: BPS state, county and place/MCD, through 2025 plus Jan–Aug 2026 |
| Parcel inventory with geometry | **OA**: city Tax Parcels (82,616), V12 | **OA**: city Parcel_View (15,764), V12; Waukesha County service returned 403 | **OA**: V12 (3,574,646) |
| Identification of improved single-family parcels | **OA**: city PropertyUse = "Single family" (49,780) and TotalDwellingUnits | **AC**: assessor Occupancy and LivingUnits in a separate layer; V12 PROPCLASS 1 with IMPVALUE > 0 (13,970) | **AC**: V12 PROPCLASS 1 with IMPVALUE > 0 (1,920,591) is a proxy; no unit count |
| Zoning districts | **OA**: city Zoning Districts layer (2,473 polygons) and parcel ZoningAll | **OA**: city Zoning_View (15,088) | **M**: SCO statewide zoning is 2016–17 county-administered only |
| Current ADU legal status | **AC**: policy agent to confirm code text | **AC**: §275-42 C summarized; the municode text was blocked to automated fetch | **M**: no statewide inventory |
| Housing stock, occupancy, structure type, age (ACS) | **OA**: tract and block group | **OA** | **OA**: 2020–2024 5-year; the API key is a dependency |
| Annual housing-unit estimates (PEP) | **AC**: county (Dane) only | **AC**: county (Waukesha) only | **AC**: county only; sub-county files hold population only |
| Municipal housing-unit estimates (WI DOA) | **U** | **U** | **U**: doa.wi.gov timed out |
| Boundaries (tract, block group, place, MCD) | **OA** | **OA** | **OA**: TIGER 2026 |
| Legislative districts (2024 plan) | **OA** | **OA** | **OA**: LTSB 99/33; TIGER SLD matches |

## Madison

### Building permits: City "Construction Summary" report (record-level)

| Attribute | Finding |
|---|---|
| URL | `https://cityreports.cityofmadison.com/CityReports/ReportViewer/ReportViewer/?ReportPath=/Web%20Access/Building/Permits/Construction%20Summary`, linked from [Permit Reports](https://www.cityofmadison.com/development-services-center/resources/permit-reports). Both return HTTP 200. |
| Publisher | City of Madison, Building Inspection. The underlying system is Accela; the public portal is `https://aca-prod.accela.com/MADISON/` (HTTP 200). |
| Access method | SQL Server Reporting Services ReportViewer (v14). The parameters are Start Date, End Date, and Permit Type (All or New Construction). After the report runs, the viewer's own export endpoint returns `text/csv`. No login is needed. Each date-range run must go through the web form, which needs an ASP.NET session. The session expired during a long run, so automation must reload and re-submit. |
| Fields (CSV header) | `B1_ALT_ID` (permit number, e.g. `BLDNRC-2024-10730`), `Reportable_Data` (use class, e.g. SINGLE FAMILY RESIDENCES), `Address_Part_Address_Line`, `BLDG_SQFT`, `Textbox9` (estimated cost), `Total_Pay` (fees), `Textbox13` (**Dwell**: dwelling units), `Owner_Full_Name`, `Owner_Address_Line`, `Detailed_Description`, `Issuance_Date`, `ContractorBusiness`, `ContractorAddress_Line`. The CSV also holds summary sections after the detail rows; keep only rows whose ID matches `^BLD[A-Z]{3}-\d{4}-\d+`. |
| Permit-ID prefixes | `BLDNRC` (new residential construction; this holds the ADUs), `BLDNCC` (new commercial and multifamily), `BLDRPR` (repair/alteration), `BLDRRZ` / `BLDCRZ` (razing). |
| Years covered | 2010 through 2026 to date (verified 2010–2026). 2008 and 2009 returned no rows. Row counts run from about 4,500 to 8,200 a year; 2026 has 13,316 rows, inflated by repair permits. |
| Location | Street address only. There is no parcel number, no coordinates, and only a free-text unit suffix (e.g. "… ST 2"). To place permits in areas, match each address to the city's Address Points layer or the Tax Parcels `Address` field. |
| Missing | No status or disposition, no application date, no final or occupancy date, and no ADU flag. Duplicate rows exist when a permit is reissued (e.g. one 2025 ADU permit appears twice with different issue dates). Deduplicate on the permit number. |
| Personal data | Owner names and mailing addresses are included. Drop them at ingestion. Keep permit number, address (internal only, for area matching), units, description and date. |
| Size | About 5 MB of CSV per year. A full 2010–2026 pull is about 80 MB. Keep it out of git. |
| License/terms | No open-data license is stated. It is a public-records report published on the city website. Record the access date and cite the city; confirm reuse terms before redistributing record-level extracts. |
| Automation | **Medium.** A scripted browser or an ASP.NET postback client, one run per year. |
| Role | Validation, baseline, and calibration of the Madison observed ADU permit series. |

#### Reconciliation with Census BPS

The yearly sum of "Dwell" over permit rows (not deduplicated) is close to the BPS total units authorized for Madison (place 516500, Units columns).

| Year | City report Dwell sum | BPS units (months reported) |
|---|---|---|
| 2010 | 521 | 526 (5) |
| 2011 | 584 | 621 (0, imputed) |
| 2012 | 1,168 | 1,208 (11) |
| 2013 | 1,851 | 1,235 (5) |
| 2014 | 1,995 | 1,680 (4) |
| 2015 | 1,725 | 1,665 (12) |
| 2016 | 2,372 | 2,381 (10) |
| 2017 | 2,257 | 2,188 (11) |
| 2018 | 1,411 | 1,443 (12) |
| 2019 | 1,758 | 1,658 (12) |
| 2020 | 2,364 | 2,185 (12) |
| 2021 | 3,653 | 3,626 (12) |
| 2022 | 2,297 | 2,360 (12) |
| 2023 | 2,597 | 2,620 (12) |
| 2024 | 2,922 | 2,812 (12) |
| 2025 | 3,620 | 3,383 (12) |

- For 2015–2025 the two series agree within about 7%.
- The 2013–2014 gaps match years when Madison reported only 4–5 months to BPS.
- **Do not treat this as a clean match.** The Dwell sum includes duplicate reissued permits, and BPS imputes values for months that were not reported. Gate 2 should deduplicate, then reconcile again by structure type.

#### ADU permit counts from the description text

Method:
- Search `Detailed_Description` with a case-insensitive pattern for: accessory dwell, \bADU\b, carriage, coach house, granny, in-law, backyard cottage, accessory unit, accessory apartment.
- Count distinct permit numbers with Dwell ≥ 1.
- Run by issuance year, 2010 to 2026 (through 2026-10-23).

| Issue year | ADU permits adding 1 unit | Other keyword records | Notes |
|---|---|---|---|
| 2010–2013 | 0 | 0 | No keyword hits. |
| 2014 | 3 | 1 | Extra record: a "lower level ADU" in a two-family building, Dwell 0. |
| 2015 | 2 | 0 | |
| 2016 | 3 | 1 | Extra record: a renewal of a 2014 permit, Dwell 0. |
| 2017 | 2 | 1 | One of the two is "convert coach house to single family home"; the extra record is a renewal. |
| 2018 | 1 | 0 | |
| 2019 | 2 | 1 | Extra record: a renewal. |
| 2020 | 0 | 0 | |
| 2021 | 1 | 0 | |
| 2022 | 5 | 0 | |
| 2023 | 7 | 2 | One new duplex with an ADU (Dwell 2) and one ADU finish/repair (Dwell 0). |
| 2024 | 10 | 0 | |
| 2025 | 13 | 2 | One garage raze for an ADU (Dwell 0) and one duplicate reissue row. |
| 2026 (to 10/23) | 16 | 9 | Nine "new twin home ADU" / "detached duplex ADU" records with Dwell 2 each. These need classification. |

Findings:
- Keyword-identified, unit-adding ADU permits total **about 49 for 2014–2025, including the coach-house case**. This matches outside reports that Madison had permitted roughly 30–50 ADUs since 2012.
- Activity rises after 2022 (5, 7, 10, 13) and in 2026 to date (16 or more).
- These are **observed lower-bound counts, not audited totals.** Known gaps:
  - ADUs described without these words are missed. The pattern search found several garage or studio items that are not dwellings.
  - Interior or attached conversions may carry Dwell 0.
  - The 2026 "twin home ADU" records may be two-unit buildings or ADU pairs. That needs a check of the permit detail in Accela.
- Example permit numbers for the Gate 2 audit sample: `BLDNRC-2014-07397`, `BLDNRC-2019-04971`, `BLDNRC-2023-05331`, `BLDNRC-2024-12626`, `BLDNRC-2025-07592`, `BLDNRC-2026-11242`.

### Madison parcels and zoning

| Source | URL | Key fields | Count / vintage | Notes |
|---|---|---|---|---|
| City Tax Parcels | `https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA2/FeatureServer/0` | Parcel, Address, PropertyClass, PropertyUse, **TotalDwellingUnits**, YearBuilt, MoreThanOneBuild, LotSize, LotWidth/LotDepth, ZoningAll/Zoning1–4, CurrentLand/Impr, OwnerOccupied, AlderDistrict, StateAssemblyDistrict, SenateDistrict, MaxConstructionYear | 82,616 parcels. PropertyUse: Single family 49,780 (sum of TotalDwellingUnits 49,598), 2 Unit 3,226, 3 Unit 550, Condominium 16,960, Apartments 2,197. Updated continuously; recent change dates are Oct 2026. | maxRecordCount 2000, so paging is required. This is richer than V12 for Madison and should be the pilot inventory source; V12 remains the statewide-consistent comparison. Owner fields are excluded from the listing above and should not be used. License not stated on the service. |
| City Zoning Districts | `https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA/MapServer/9` | ZONING_CODE, Zoning_District, Zoning_Document | 2,473 polygons | Parcels whose ZoningAll contains TR-C or SR-C: 46,348 (exploratory query). |
| Other city layers | `OPEN_DATA/MapServer/20` (Address Points), `/12` (Neighborhood Associations), `/16` (Single-Family Assessment Areas); `OPEN_DATA_PLANNING/MapServer/16` (TOD Overlay), `/12` (Local Historic Districts) | | | Candidate permit-to-address matching and area units. Historic districts can affect ADU feasibility. |
| City open-data hub | `https://data-cityofmadison.opendata.arcgis.com/` (search API 200) | | | A search for "permit" returns only parking permits. **No building-permit dataset exists on the hub.** |
| Dane County LIO hub | `https://gis-countyofdane.opendata.arcgis.com/` (200) | | | Not needed for the city pilot. V12 covers Dane parcels; the Dane County V12 GDB is 45.5 MB. |

## New Berlin

| Item | Finding (2026-10-23) |
|---|---|
| Permit portal | The city's [Building Permits & Inspections page](https://www.newberlinwi.gov/97/Building-Permits-Inspections) (200) has PDF forms only. The [payment instructions](https://www.newberlinwi.gov/DocumentCenter/View/26471/Citizen-Self-Service-Permit-Payment-Instructions) point to `https://newberlincitizens.munisselfservice.com/` (Tyler Munis). `/citizens/` redirects to a Tyler Portico (Okta) login. Lookup works by application number only. **There is no public search, list or export.** |
| Public-records portal | `https://new-berlin-wi.nextrequest.com/` returned 403 behind a Cloudflare challenge. It was not bypassed, and no request was filed. |
| City ArcGIS (org LKgpy6JJatlcMHWR) | `https://services3.arcgis.com/LKgpy6JJatlcMHWR/arcgis/rest/services` (200) has 32 services and **no permit layer**. Useful layers:<br>• `Parcel_View/FeatureServer/5`: 15,764 current parcels.<br>• `Parcel_View/FeatureServer/10`: 1,113 retired parcels.<br>• `Zoning_View/FeatureServer/0`: 15,088 records.<br>• `Assessor_Finance_View/FeatureServer/60` (MD_ResidentialBuildings): 14,087 rows with YearBuilt, LivingUnits and Occupancy (single family 12,005; 2-family 89).<br>• `Assessor_Finance_View/FeatureServer/20` (MD_Assessments): **LastBuildingPermitDate** only, with no type or number.<br>The assessor data has no in-law or family-dwelling-unit flag. |
| Waukesha County GIS | `https://gis.waukeshacounty.gov/host/rest/services` returned **403 (Cloudflare)**. Service names are known from the arcgis.com index (Web_Tax_Parcel, Historic_Parcels, ZoningCountyShoreland). No permit service was found. |
| 2025 Housing Affordability Report | [PDF](https://newberlinwi.gov/DocumentCenter/View/25878/2025-Housing-Affordability-Report) (200), dated January 2026, covers calendar 2025. It reports 33 new single-family homes, 0 duplex units, 193 residential alterations and 32 additions. A footnote says these are **applications received, not issued permits**. It has a dwelling-unit inventory (17,728 units in 2025) and **no ADU or family-dwelling-unit counts**. Only the 2025 edition was found. |
| Plan Commission records | The CivicClerk API `https://newberlinwi.api.civicclerk.com/v1/Events` (200) lists 60 Plan Commission events, 2022–2026, as PDFs. Family dwelling units need only a staff zoning permit (§275-24), so they will mostly be absent here. |
| Census BPS | Place 612500 (FIPS 56375) in [mw{YYYY}a.txt](https://www2.census.gov/econ/bps/Place/Midwest%20Region/), annual 1980–2025. Recent years:<br>• 2018: 74 one-unit, 12 two-unit.<br>• 2019: 40 / 22.<br>• 2020: 28 / 16.<br>• 2021–2025: 33, 18, 20, 32, 33 one-unit and 0 two-unit.<br>The 2025 figure of 33 matches the report's 33 applications. |
| ADU rules | The municode URL returned 403 to automated fetch. A third-party summary of §275-42 C says: detached ADUs are prohibited; an attached "family dwelling unit" is allowed with owner occupancy, related occupants, 2 occupants maximum, at most 50% of the principal dwelling's floor area, and a zoning permit. **The [DocumentView DID=502 link](https://www.newberlinwi.gov/DocumentView.aspx?DID=502) cited in AQ-014 resolves to the "Sheds" guide, not ADU guidance.** The AQ-014 citation needs correcting by its owner. A family dwelling unit is an attached unit permitted as an alteration or addition, so it probably does not appear in BPS new-unit counts. |

### Option set for owner decision

Do not file a records request or contact anyone without owner authorization.

1. **Records request** under Wis. Stat. §§ 19.31–19.39, through NextRequest or the clerk. Ask for:
   - A CSV export from Munis of residential building and zoning permits, 2015 (or the earliest available) to the present.
   - Fields: permit number, type and subtype, work description, application date, issue date, final or occupancy date, status, tax key, address, dwelling units added, and valuation.
   - Any zoning permits under §275-42 C / §275-24 (family dwelling units) and recorded deed-restriction references.
   - Earlier Housing Affordability and New Housing Fee reports.

   This needs owner approval of the request text and acceptance of possible staff-time charges and delay. It is the only route to a family-dwelling-unit count.
2. **Coarser method.** Treat New Berlin as a restrictive-law exemplar using:
   - BPS place totals.
   - Assessor YearBuilt and LivingUnits.
   - V12 single-family inventory.
   - A stated assumption that permitted ADU production is approximately zero, unobserved and uncertain.

   This needs the assumption recorded with a sensitivity range. It cannot validate ADU production.
3. **Substitute or add a jurisdiction** with open permit records and restrictive rules. Neenah (monthly detailed PDF reports, per AQ-014) and pre-August-2025 Milwaukee (LMS records from 2016) are the known leads; neither was re-checked in this package. This needs a policy classification plus a portal check. New Berlin should not be silently replaced (MVP plan, Gate 2).

## Statewide sources

| Source | URL checked (status) | Publisher | Vintage | Geography | Key fields | License | Access / size | Automation | Role |
|---|---|---|---|---|---|---|---|---|---|
| Census BPS: county | [co2025a.txt](https://www2.census.gov/econ/bps/County/co2025a.txt) (200, 375 KB) | Census Bureau | Annual 1990–2025; monthly to Aug 2026 (`co2608`) | County | 1, 2, 3–4 and 5+ unit buildings, units and value; reported vs. imputed | Public domain | Flat CSV with 2 header rows | High | Baseline |
| Census BPS: place/MCD | [mw2025a.txt](https://www2.census.gov/econ/bps/Place/Midwest%20Region/mw2025a.txt) (200, 1.2 MB) | Census Bureau | Annual 1980–2025; monthly to Aug 2026 | About 1,152 WI jurisdictions in 2025, about 502 of them towns | As above, plus 6-digit ID, FIPS place/MCD, months reported | Public domain | As above | High | Baseline and coverage. **ADUs are not separately identified**; they may appear as 1-unit or be absent. Treat months-reported < 12 as imputed. |
| ACS 5-year | [API groups B25001/2/24/34](https://api.census.gov/data/2024/acs/acs5/groups/B25024.json) (200). The data call without a key returns **302 to `missing_key.html`**. | Census Bureau | 2020–2024 (2025 5-year not yet released) | Tract, block group, place, MCD, SLDL/SLDU | B25001 total units; B25002 occupancy; B25024 units in structure; B25034 year built; MOEs | Public domain | API (free key needed) or keyless [table-based summary files](https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/) (B25024 47.9 MB, B25034 50.1 MB; national) | High | Inventory context and housing health |
| PEP housing units | [CO-EST2025-HU-55.xlsx](https://www2.census.gov/programs-surveys/popest/tables/2020-2025/housing/totals/CO-EST2025-HU-55.xlsx) (200, 17 KB) | Census Bureau | Vintage 2025 (2020–2025) | State and county only | Annual housing units | Public domain | xlsx only; the CSV dataset path returns 404 | Medium | Stock and net change. Not gross construction. |
| WI DOA housing-unit estimates | [Population_Estimates.aspx](https://doa.wi.gov/Pages/LocalGovtsGrants/Population_Estimates.aspx) (**timed out**, two attempts) | WI DOA Demographic Services | Jan 1 estimates (final around October) | County; municipal coverage unconfirmed | | | | **U** | Possible municipal stock source. Recheck from another network. |
| TIGER/Line 2026 | e.g. `https://www2.census.gov/geo/tiger/TIGER2026/TRACT/tl_2026_55_tract.zip` (200) | Census Bureau | 2026 (posted 2026-10-06) | Tract 7.7 MB, BG 13.9 MB, place 3.5 MB, COUSUB 8.6 MB, SLDL 3.7 MB, SLDU 3.1 MB | GEOIDs | Public domain | Zipped shapefiles | High | Area keys. Match the boundary vintage to ACS 2024 (TIGER 2024 or 2020 tracts) before joining. |
| WI legislative districts | [WI_Assembly_Districts_2024](https://services1.arcgis.com/FDsAtKBk8Hy4cAH0/arcgis/rest/services/WI_Assembly_Districts_2024/FeatureServer/0) (count 99); WI_Senate_Districts_2024 (33) | WI LTSB | 2023 Act 94 plan (Feb 2024) | Assembly, Senate | ASM2024, SEN2024 | "Open and publicly available… use at your own risk" | FeatureServer, maxRecordCount 2000 | High | District explanations. TIGER SLD 2024/2026 has identical geometry (drop the ZZZ feature). |
| WI V12 statewide parcels | [FeatureServer](https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/Wisconsin_Statewide_Parcels_DB/FeatureServer/0) (200); [statewide GDB zip](https://web.s3.wisc.edu/parcels/v12_parcels/V12.0.0_Wisconsin_Parcels_2026_10.3_Compressed.zip) (200, **515.8 MB**; uncompressed variant 759.9 MB); county zips listed in `https://www.sco.wisc.edu/parcels/data-county/links_v1200.csv`; [schema PDF](https://www.sco.wisc.edu/parcels/data/assets/V12/V12_Wisconsin_Statewide_Parcels_Schema_Documentation.pdf) (200) | WI DOA / UW SCO | V12, released 2026-06-30; mostly 2025 tax roll | Parcel (3,574,646) | PARCELID, TAXPARCELID, PROPCLASS, AUXCLASS, IMPVALUE, LNDVALUE, ESTFMKVALUE, GISACRES, PLACENAME, CONAME, address fields, LATITUDE/LONGITUDE | **Public domain, no use restrictions** (schema PDF) | Bulk GDB; the API (2,000 per page, about 1,800 requests) is for counts only | High | Statewide inventory proxy. See the note on single-family identification below. |
| SCO zoning | [sco.wisc.edu/data/zoning](https://www.sco.wisc.edu/data/zoning/) (200) | UW SCO | 2016–2017 | County-administered zoning only | | | | n/a | **Not usable** for municipal ADU rules |
| Statewide municipal ADU ordinance status | Search of policy, realtor, UW and zoning-atlas sources | — | — | — | — | — | — | — | **Missing.** No statewide inventory exists. Statewide ADU bills AB 449 / SB 473 failed on 2026-03-23 (web search only; docs.legis.wisconsin.gov timed out), so there is no statewide mandate. |

### Identifying improved single-family parcels in V12

- V12 has **no dwelling-unit count, building type or year built.**
- PROPCLASS is a text field that can hold combined classes (112 distinct values, e.g. `1,4`).
- The recommended proxy is `PROPCLASS = '1' AND IMPVALUE > 0`, with these caveats:
  - It includes condominiums and multifamily residential (class 1 is residential, not single-family).
  - IMPVALUE is null for 337,057 parcels.
  - PROPCLASS is null for 419,544 parcels, mostly exempt parcels.
  - Condominium units can overlap.

| Area | PROPCLASS='1' AND IMPVALUE>0 | Comparison |
|---|---|---|
| Statewide | 1,920,591 | 2,102,599 with `LIKE '%1%'` |
| Madison | 71,226 | The city layer has 49,780 "Single family" parcels |
| New Berlin | 13,970 | 12,005 single-family buildings in the assessor table |

So the V12 proxy overstates single-family inventory by about 43% in Madison and about 16% in New Berlin. Gate 2 must calibrate it against local assessor data, ACS B25024 (1-unit detached) and Census block counts, and report the adjustment as an assumption.

## Top Gate 2 risks

1. **There is no statewide ADU permit observation.** BPS does not separate ADUs, and only Madison has an observable ADU series. It is small: about 49 unit-adding permits over 2014–2025, and about 16–25 in 2026 to date. Statewide response must rest on transferred evidence with wide ranges, not local calibration.
2. **There is no statewide inventory of local ADU rules.** About 1,850 cities, villages and towns have no compiled ADU status. Most must be carried as "unknown" with an explicit sensitivity treatment. The policy agent will need a sampling design for any audited subset.
3. **New Berlin has no public permit records.** The owner must choose between a records request, the coarser method, or adding a jurisdiction. Its family dwelling units are attached alterations, probably invisible to BPS, so "restrictive" production cannot be observed from public data.
4. **Madison ADU classification is text-based.** It misses ADUs not described with the keywords, may include Dwell-0 conversions, and the 2026 "twin home ADU" records are ambiguous. Gate 2 needs:
   - A manual audit sample, with Accela detail lookups.
   - Deduplication of reissued permits.
   - An address-to-parcel match rate, since the report has address only and no parcel number.
5. **The V12 single-family proxy overstates eligible inventory** (Madison +43%). Local assessor layers differ by municipality, so statewide calibration must use ACS or Census counts at area level.
6. **Access fragility.**
   - The Madison report needs session-based scraping.
   - Waukesha County GIS, municode, NextRequest (Cloudflare 403) and doa.wi.gov (timeouts) were unreachable by script.
   - The Census API now requires a key, so a `CENSUS_API_KEY` must be provisioned; the keyless summary files are a fallback.
7. **Reporting completeness in BPS.** Madison reported fewer than 12 months in 2010–2014, 2016 and 2017, so imputed values affect the baseline period. Statewide, check months reported for each jurisdiction before using place-level baselines.
8. **Boundary and vintage alignment.** ACS 2024 uses 2020-vintage tracts; TIGER 2026, the V12 2026 parcels and the 2024 legislative plan need documented crosswalks. Wisconsin towns (MCDs) are BPS reporting units and must be kept as areas.

## URLs checked on 2026-10-23

These are in addition to those already linked in the tables.

- Madison: `https://maps.cityofmadison.com/arcgis/rest/services/Public?f=json` (200; services OPEN_DATA, OPEN_DATA2, OPEN_DATA_PLANNING, Property_Lookup and others; no permit layer); `https://elam.cityofmadison.com/CitizenAccess/` (redirects to aca-prod.accela.com/MADISON, 200); `https://www.cityofmadison.com/dpced/building-inspection` (200).
- Census BPS place files `mw2010a.txt` through `mw2025a.txt` (200; Madison and New Berlin rows extracted). Census API `https://api.census.gov/data/2024/acs/acs5?get=NAME,B25024_001E&for=state:55` (302 to the missing-key page).
- V12 statewide GDB HEAD: Content-Length 515,810,191, Last-Modified 2026-06-30. LTSB Assembly count query: 99.

Some checks came from delegated sub-checks in this package:
- New Berlin portal and ArcGIS checks.
- TIGER sizes.
- PEP paths.
- V12 statistics queries.
- LTSB Senate.
- The statewide ADU inventory search.

Their scratch outputs are under the session scratchpad (`…/scratchpad/data/nb` and `…/scratchpad/data/sw`), not in the repository.
