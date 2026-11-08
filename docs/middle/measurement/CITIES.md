# How city permit data record middle housing (measurement check, cities)

Run 2026-11-08, 00:27–00:36 UTC. Only documentation, field lists, labels without counts, and single example records from before each reform were read. **No post-reform count, sum, rate or chart was seen.** Rule breaks and edge cases are listed at the end.

V = verified in at least one pre-reform example record. S = stated in documentation, or inferred from labels only.

---

## Austin (Socrata 3syk-w9eu; reform 2024-02-05)

| Case | How recorded | Field / value | Source | V/S |
|---|---|---|---|---|
| Townhouse (fee-simple or condo-regime) | One BP per unit, housing_units=1. Small infill: `R- 101 Single Family Houses` (e.g. "3 story 2 unit townhome Bldg 2 Unit C", lot "N55 FT OF LOT 11 BLK 2 BANISTER ACRES", total_lot_sq_ft=0). Site-plan projects: `C- 101 Single Family Houses` ("3-Story Condominiums", 1 unit each, same tcad_id) | permit_class, condominium (Yes/No), description | ex. records 2023-10 to 2024-02 | V |
| Condo-regime "SFR" | R-101 with condominium=Yes, total_lot_sq_ft=0, site plan number in description (SP-2018-0390C) | condominium=Yes | ex. 2024-01/02 | V |
| Duplex | `R- 103 Two Family Bldgs`, housing_units=2, one permit. Also used for greenfield "TH" duplexes in subdivisions ("Acadia TH", Easton-type plats). `C- 103` used for each 2-unit building inside a multi-building complex | permit_class | ex. 2021–2024 | V |
| Triplex / fourplex | `C- 104 Three & Four Family Bldgs`, housing_units 3–4, one permit per building. Large complexes file one C-104 permit per building (Bldg 1, Bldg 9 on a 33.5-acre tract) | permit_class, housing_units | ex. 2023 | V |
| 5–6 unit building | `C- 105 Five or More Family Bldgs`, housing_units 5–6 (e.g. "5 unit 2-story townhome development" on part of LOT 8). Some C-105 rows have housing_units=1 (part-building/void permits) | permit_class, housing_units | ex. 2023 | V |
| ADU | `R- 102 Secondary Apartment`, housing_units=1 | permit_class | ex. 2024-01 | V |
| Lot split / resubdivided-lot home | R-101 on lot named "LOT 18A *RESUB OF LOT 17-18…" | legal_description text "RESUB" | ex. 2023-12/2024-01 | V |
| Small-lot detached | R-101; small-lot only visible from total_lot_sq_ft (0 = condo/unknown) | total_lot_sq_ft | ex. | V (field) |
| Conversion | No dedicated class seen; would be R-434/R-435 with work_class Remodel. housing_units may not record the added unit | permit_class, work_class | labels only | S |

**Infill vs new subdivision:** best of all cities. legal_description carries the subdivision name with section/phase ("EASTON PARK SEC 3A PHS 1 BLK G LOT 22") or "RESUB"/"ABS … ACR" (unplatted acreage). tcad_id joins Travis CAD parcels (plat year, year built of the old house). masterpermitnum links to the plan-review project, and descriptions quote the site plan number. Trap: R-103 and C-104 are widely used in greenfield tracts, so the class alone does not mean infill.

**Licence:** dataset metadata licence = "Public Domain U.S. Government" (licenseId USGOV_WORKS, termsLink https://www.usa.gov/government-works). Attribution "City of Austin, Texas - data.austintexas.gov". The description links the City of Austin Open Data Terms of Use (https://data.austintexas.gov/stories/s/ranj-cccq, licenseId "SEE_TERMS_OF_USE"). That page renders only with JavaScript, so its text was **not read**. Disclaimer in the description: data "for informational use only and may differ from official department data".

---

## Raleigh (ArcGIS Building_Permits/FeatureServer/0; reform 2021-07-06)

| Case | How recorded | Field / value | Source | V/S |
|---|---|---|---|---|
| Townhouse | One permit per unit: workclass=`Townhouse`, censuslandusecode=102 "RESIDENTIAL TOWNHOUSE", housingunitstotal=1. Lots named in the text ("TOWNHOMES LOTS 51-56"), projectname "DSLC - Cadence at Town Center" | censuslandusecode 102, workclass | ex. 2021-06 | V |
| Duplex | censuslandusecode=103, housingunitstotal=2, workclass "New Residential Dwelling" (infill, e.g. "DUPLEX … Demo 45399-2020"). **Trap:** 103 is also used for 2-unit "carriage" buildings inside large apartment complexes (projectname "DSLC - North Ridge Apartments", workclass "New Building") | censuslandusecode 103 + workclass + projectname | ex. 2021 | V |
| Triplex / fourplex | censuslandusecode=104, housingunitstotal=4 ("4 unit townhome style apartment"), one permit per building, workclass "New Building" | 104 | ex. 2019 | V |
| 5–6 unit building | censuslandusecode=105. housingunitstotal is unreliable: one 105 building in a 315-unit project shows 2 | 105 + housingunitstotal | ex. 2020–21 | V |
| Condo building | censuslandusecode=100 "RESIDENTIAL CONDOMINIUM" (not a Census code), housingunitstotal per building (5) | 100 | ex. 2021-03 | V |
| ADU | adu_type = Attached ADU / Detached ADU (labels in all years also include "Internal ADU" and "NOT Accessory Dwelli…"). censuslandusecode stays 101. housingunitstotal is 0 or 1 (inconsistent). permitclass may be 434/438 | adu_type | ex. 2021-06 | V |
| Small-lot / infill detached | 101; description text "---infill applies---" / "---not infill---" (Raleigh's residential infill review) | proposedworkdescription text | ex. 2020–21 | V |
| Lot split home | No structured field. Text names the lot ("Hayes Barton Lot 13"; demolition permit cited) | text, pin | ex. | V (text only) |
| Conversion | workclass "Change Of Use" (e.g. garage to ADU) | workclass | ex. | V |

**missing_middle flag:** before 2021-07-06 the values are only blank, null or "No". Earliest "No" seen: applied 2019, issued 2020-05-08. So the field existed before the reform, with "No" back-filled or entered by staff. Across all years the labels are null / '' / No / Yes (labels only, no counts, rule 2). The city's Missing Middle Metrics page defines the units as those in subdivisions, ASRs and building permits "enabled by TC-5-20 and/or TC-20-21" (detached, tiny house/cottage court, attached/duplex, townhouse, apartment, ADU), with data collection from 2021-07-06. The flag therefore marks **reform-enabled** projects. It is an outcome-defined (treatment-defined) flag, it does not exist before treatment, and it cannot serve as a neutral pre/post measure. One example record carries a staff note dated 9/30/26 confirming its Census code, so codes are being revised after the fact.

**Census land use codes in use:** 0, 100, 101–105, 112, 213, 214, 318–329, 434, 437, 438, 601, 602, 645–649. There is no 106 or 114.

**Infill vs new subdivision:** partly possible. pin (Wake PIN) joins to parcels and plats. "DSLC -" projectname marks large site-plan projects. Infill text tags and "LOTS x–y" also help. devplanid and corlotid were empty in every sample.

**Licence (exact text, item licenseInfo, https://www.arcgis.com/home/item.html?id=bdfad82b15344d37beb28d7f90b6c4be; the same text is in the service metadata XML):** "Open Raleigh Data Policy. By using data made available through this site, the user agrees to all the conditions stated in the following paragraphs as well as the terms and conditions described under the City of Raleigh Open Data Privacy Policy. THE CITY OF RALEIGH MAKES NO REPRESENTATIONS OR WARRANTY… Right to Modify and/or Discontinue Feeds: The City of Raleigh reserves the right to modify and/or discontinue providing any or all of the data feeds at any time and to require the termination of any and all displaying, distributing or otherwise using any or all of the data for any reason… Use of the data.raleighnc.gov website constitutes acceptance of this policy." **There is no open licence grant.** The text implies that use and distribution are allowed, but the City can revoke them.

---

## Charlotte / Mecklenburg (meckgis BuildingPermits/FeatureServer/0; reform 2023-06-01)

| Case | How recorded | Field / value | Source | V/S |
|---|---|---|---|---|
| Townhouse | One permit per unit: usdcdesc `102 - One Family Attached/Townhouse (land sold w/unit)`, numunits=1, permittype "One/Two Family". projname "TH MATTAMY … Bldg 10 Lots 43-46"; subdiv sometimes set ("NORTHHAMPTON TOWNHOMES") | usdcdesc 102 | ex. 2023-05 | V |
| Duplex | `103 - Two Family / Duplex`, numunits=2, one permit. Infill examples on R-3/R-8 lots; also "BLU SOUTH" builder product | usdcdesc 103 | ex. 2023 | V |
| Triplex / fourplex (rental) | `104 - 3 & 4 Family Apartments`, numunits=4, permittype Commercial; large complexes file one per building (LakePointe Bldg 17, 18, 20 on one parcel, zoning UR-2(CD)) | 104 | ex. 2023-05 | V |
| 3–4 unit condo | `114 - 3 & 4 Family Condos`, **numunits=1 per unit permit** (one permit per condo unit) | 114 | ex. 2022 | V |
| 5–6 units | `105 - 5 or More…` or `115` condos; numunits is unreliable (footing/foundation section permits show 1) | 105/115 | ex. 2023 | V |
| ADU | **Coded `101 - One Family Detached`**, numunits=1. Only identifiable from text "New. Accessory Dwelling Unit." in permitdesc, or "ADU" in projname | permitdesc text | ex. 2023-04/05 | V |
| Small-lot / lot-split detached | 101; no lot-size field. Lot numbers appear in projname/permitdesc | text, parcelnum | ex. | V (text) |
| Conversion | 434 "Res Dwelling (Addition, Alteration…)"; no unit field change seen | usdcdesc 434 | labels | S |

**Infill vs new subdivision:** partly possible. `subdiv` is filled for some greenfield plats ("THE PRESERVE AT KINSLEY LAKES", "WALDEN PONDS") and for townhome projects, but is often null. `zonecode` is free text with conditional-rezoning tags ("(CD)", "MX-1 INNOV", petition numbers), which mark negotiated master-planned sites. Pre-UDO codes (R-3, R-5, R-8) can be mapped to the post-UDO N1-x districts. One pre-reform label "N1-B" appears (label only). parcelnum joins Mecklenburg parcels. **Trap:** county data, so filter taxjuris='CHARLOTTE'.

**Licence (exact text, item fc9d171ecd4d44a58c7dad840cd58aa2, owner MecklenburgCoNC, https://www.arcgis.com/home/item.html?id=fc9d171ecd4d44a58c7dad840cd58aa2):** "Although every effort has been made to ensure the accuracy of information, errors and conditions originating from physical sources used to develop the corporate database may be reflected in the data supplied. Users of this data must be aware of data conditions and bear responsibility for the appropriate use of the information… Mecklenburg County makes no warranty, either expressed or implied, as to the accuracy or completeness of any information archived and distributed. The digital information is distributed on an as is basis." accessInformation: "Mecklenburg County GIS". **This is a disclaimer only, with no licence grant.** Note: other CharlotteNC copies of Mecklenburg layers state CC BY-NC-SA 4.0 (non-commercial). This permits item does not.

---

## Minneapolis (CCS_Permits/FeatureServer/0; reform 2020-01-01)

| Case | How recorded | Field / value | Source | V/S |
|---|---|---|---|---|
| Townhouse | permitType Res, occupancyType `TH`, workType New, dwellingUnitsNew per permit (2 for a 2-unit building). **Data error seen:** 5-unit "townhouse style apartment" with dwellingUnitsNew=0 | occupancyType TH | ex. 2017 | V |
| Duplex | Res / `TFD` / New, dwellingUnitsNew=2. Some rows have text "Source Information is Not Available" | occupancyType TFD | ex. 2019 | V |
| Triplex / fourplex | permitType **Commercial**, occupancyType `3to4`, workType New, dwellingUnitsNew 3–4 | 3to4 | ex. 2019 | V |
| 5–6 unit | Commercial / `MFD` / New, dwellingUnitsNew 6 (two buildings on two permits) | MFD + dwellingUnitsNew | ex. 2019 | V |
| ADU | **No ADU code.** New SFD with ADU is coded SFD, dwellingUnitsNew=1, so the ADU unit is not counted. Only the comments text says "ADU". occupancyType "Accessory" = garages/decks | comments text | ex. 2018–19 | V |
| Conversion | workType `Conversion`, with dwellingUnitsNew and dwellingUnitsEliminated (duplex→triplex: new 3, eliminated 2). `UnitCon`/`UnitFinish` for shell units | workType | ex. 2019 | V |
| Lot split / small-lot | No field; APN only | APN | – | S |

**Traps:** trade permits (Mechanical/Plumbing) carry the same occupancyType/workType "NewRes" with null units, so filter permitType IN ('Res','Commercial'). Duplicate rows were seen (BLDG802166 twice). Dwelling counts are stored as text.
**Infill vs new subdivision:** no subdivision field. APN joins Hennepin County parcels and plats. The city is almost fully platted, so greenfield risk is low but not zero.
**Licence (item df4bfccbe60b42a6a93fb7bc1fd84cc0):** "To the extent possible under law, City of Minneapolis has waived all copyright and related or neighboring rights to Open Data" (CC0-style waiver) plus a GIS accuracy disclaimer (Minn. Stat. 466.03 subd. 21).

---

## Portland OR (on-disk residential_building_permits.csv; reform 2021-08-01; only rows ISSUEDATE < 2021-08-01 read)

| Case | How recorded | Field / value | Source | V/S |
|---|---|---|---|---|
| Townhouse | NEWTYPE `Townhouse`, SUB `Townhouse (2 Units)` or `Townhouse (3 or more units)`, **one permit per unit, NEW_UNITS=1**. Text often says "all on one lot", and all units share one PROPLOT (R158284) | NEWTYPE/SUB | ex. 2019 | V |
| Rowhouse vs townhouse | `Rowhouse` / SUB `Rowhouse (2 units)` appears only in older years (2013 example). Each unit is on **its own lot** ("ROSELYN PLACE, LOT 3/LOT 4", separate PROPLOT). Not in 2015–2021 labels, so it is an older system label | NEWTYPE | ex. 2013 | V |
| Duplex | NEWTYPE `Duplex`. **Inconsistent:** some duplexes are one permit with NEW_UNITS=2, others are two permits (one per address) with NEW_UNITS=1 each | NEW_UNITS | ex. 2019 | V |
| Triplex / fourplex | `Apartments/Condos` (SUB "3 or more units"), **one permit per building with NEW_UNITS=3 or 4** ("NEW 4-UNIT, 3 STORY APARTMENT BUILDING"); multi-building sites have one permit per building ("1 OF 4") | NEW_UNITS | ex. 2019 | V |
| 5–6 unit | Apartments/Condos, NEW_UNITS 5–6 ("6-PLEX") | NEW_UNITS | ex. 2019 | V |
| ADU | NEWTYPE `Accessory Dwelling Unit`, IS_ADU=True, NEW_UNITS=1; address "- Unit B"; includes garage conversions (NEWCLASS Alteration) and revision permits (FOLDERNUMB "-REV-01-") | IS_ADU | ex. 2019 | V |
| Conversion | NEWTYPE `Conversion` (label pre-reform), or Duplex + NEWCLASS Alteration ("CONVERT SFR TO DUPLEX", NEW_UNITS=1) | NEWCLASS/NEWTYPE | ex. 2019–21 | V |
| Lot split / land division home | **No structured field.** FOLDER_DES text: "PARTITION PLAT 2006-167, LOT 2"; "ON TRACT 6 OF 14-252647-FP" (land-use case number, FP = final plat). PROPLOT/PROPGISID1 change after a split | FOLDER_DES text | ex. 2016–20 | V |

**Traps:** revisions (-REV-) repeat units, so count only base folders. One old folder (04-007460) appears with a 2020 ISSUEDATE (re-issued). Use NEWCLASS='New Construction'.
**Infill vs new subdivision:** partial. Land-use case numbers in text (-FP-, PARTITION PLAT) and the property ID can be matched to Portland land-division case data. Text such as "on one lot" tells same-lot townhouses apart from platted rowhouses.
**Licence:** _downloads.json says "City of Portland open data (PortlandMaps); no license stated on item" (not re-checked in this run).

---

## Sacramento (BldgPermitIssued_Archive/FeatureServer/0; reform 2024-02-27; rows filtered to Status_Date years ≤ 2023)

| Case | How recorded | Field / value | Source | V/S |
|---|---|---|---|---|
| Townhouse | Category `Single Family`, Sub_Type New Building, **one permit per unit** ("UNIT 2 OF 5 TOWNHOME PROJECT"). Re-issued "permit to complete" rows have House_Count=0 | text only | ex. 2022 | V |
| Half-plex | Category `Half Plex`/`Half-Plex`. Samples were all minor repair permits, so it is unclear how new ones are filed | Category | ex. 2023 | V (label) |
| Duplex | Category `Duplex`, New Building, House_Count=2. **Trap:** a "2-unit ADU" building is also filed as Duplex | Category | ex. 2023 | V |
| Triplex / fourplex | Type Commercial, Category `Apts 3-4`, New Building, House_Count=4. **Trap:** "duplex with two ADUs" filed as Apts 3-4 | Category | ex. 2023 | V |
| 5–6 unit | `Apts 5+` + House_Count. No new-build sample found in the window | Category | labels | S |
| Condo | Category `Condos` (samples were repairs) | – | labels | S |
| ADU | **No ADU category.** Detached ADU = Category Single Family, New Building, House_Count=1. Attached/conversion ADU = Category Duplex with Activity_Code `C11 CONVERT SFR TO DUPLEX`. Text "ADU" in Work_Desc/Project_Name | text, Activity_Code | ex. 2023 | V |
| Conversion | Activity_Code C11 (SFR→duplex), C12 (duplex→half), I3 GARAGE CONVERSION | Activity_Code | ex. 2023 | V |
| Greenfield tract home | Sub_Type `Production Permit`, master plan number "MP-…" and plan/elevation in Work_Desc | Sub_Type | ex. 2023-12 | V |
| Lot split | No field; Parcel_No only | – | S |

**Infill vs new subdivision:** a usable signal exists: Sub_Type 'Production Permit' (master-plan tract homes) versus 'New Building' (custom/infill). Parcel_No joins Sacramento County parcels. **Traps:** Status_Date is a text field (MM/DD/YYYY). The archive was last updated 2024-03-25, says it holds "the last 9 years", and may include a few post-reform weeks, so always filter by date. Sub_Type '1-5' belongs to signs, not housing.
**Licence:** the item licenseInfo and accessInformation are **empty** (item ec9060482ef749899bb20f6dc8003530). The governing text is the City of Sacramento Open Data Terms of Use, https://www.cityofsacramento.gov/content/dam/portal/it/gis/open-data/OpenDataTermsOfUse.pdf: "The City grants any interested user (the 'User') access to and use of the Data subject to the City's Open Data Terms of Use (the 'Terms') and applicable laws. The Terms, constituting a binding agreement…". Acceptance happens "by machine-consuming, or downloading and using the Data". Derivative Work is defined and covered. "The City reserves the right to claim or seek to protect any patent, copyright, trademark, or other intellectual property rights". The page will flag any claimed IP. Warranty disclaimer ("as available"). The terms can be modified by notice. **The terms allow use, but give no explicit redistribution licence.**

---

## Durham (metadata comparison only; ODbL, excluded)
All Building Permits layer (services2.arcgis.com/G5vR3cOjh6g2Ed8E/.../Inspections/FeatureServer/12). Fields include DWELLING_UNITS, BLD_Type, Occupancy, TYPE, BLDB_ACTIVITY, SQFT_LAND, PIN. BLD_Type labels (2017 to before 2019-10-01): Single Family House, **Townhouse**, Duplex, 3-4 Residential Units, 5+ Residential Units, **Accessory Dwelling**, Modular Unit, Mobile Home… These are the cleanest type labels of any city. Licence text: "The Open Database License (ODbL)… It is listed here as a general reference, not as a binding document. The City and County of Durham reserve all their rights in relation to the data provided here."

## Houston (fields only)
data.houstontx.gov has only "City of Houston Residential Building Permits by Month and Year" (Planning and Development Dept.), resource c9cef716…: fields `_id, Year, Month, Single Family, Multi-Family, Residential`, monthly from 2004. It is **aggregate only**: no record-level data, no townhouse/duplex split, no lot field, so it cannot measure middle housing. The whole series is after Houston's 1998 reform, so **no rows were opened** (datastore query limit=0, fields only). Licence: Open Data Commons Attribution (ODC-BY).

---

## Cross-city summary
- **Townhouses are filed one permit per unit almost everywhere** (Austin, Raleigh, Charlotte, Portland, Sacramento). Minneapolis is the exception (one permit per building). Unit counts must sum across permits. Building counts would need grouping by project, address or parcel.
- **ADUs are hidden inside "single family" codes** in Charlotte (101), Sacramento (Single Family/Duplex) and Minneapolis (SFD). Explicit ADU fields exist only in Austin (R-102), Raleigh (adu_type) and Portland (IS_ADU / NEWTYPE).
- **Census 103/104 codes are routinely used for buildings inside large greenfield complexes** (Raleigh carriage buildings, Charlotte LakePointe, Austin Acadia TH duplexes). Unit type alone cannot separate infill middle housing from tract or complex development.
- **Best infill signals:** Austin legal_description (subdivision/section/phase, RESUB) + tcad_id; Sacramento Production Permit flag; Charlotte subdiv + zonecode (CD) tags; Raleigh pin + "DSLC" projectname + infill text tags; Portland land-use case numbers in text + property ID. Every city needs a parcel/plat join (plat date before the reform, existing house on the lot) for a clean rule.
- **No city has a structured "lot split / land division" field on the permit.** Lot splits must come from plat/partition records joined by parcel.

---

## Query log (UTC, 2026-11-08)

| Time | Query / page | Date filter | Rule |
|---|---|---|---|
| 00:27:51 | MEASUREMENT_CHECK_LOG.md (repo) | – | 1 |
| 00:27:58–59 | Layer metadata ?f=json: Raleigh, Mecklenburg, Minneapolis, Sacramento | none (field lists) | 1/2 |
| 00:28:16–29 | Raleigh distinct values ×14 fields (permittypemapped … missing_middle) | issueddate < 2021-07-06 | 2 |
| 00:28:39 | FeatureServer service pages ×4 (item ids) | – | 1 |
| 00:28:46–47 | ArcGIS item pages: Raleigh bdfad82b…, Minneapolis df4bfccb…, Sacramento ec906048… (desc, licence) | – | 1 |
| 00:28:57–58 | Minneapolis distinct permitType, occupancyType, workType, status, dwellingUnitsNew | issueDate < 2020-01-01 | 2 |
| 00:28:59–29:25 | Mecklenburg distinct ×12 fields | issuedate < 2023-06-01 | 2 |
| 00:29:37–40 | Minneapolis examples ×8 (≤2 records each) | 2017-01-01 ≤ issueDate < 2020-01-01 | 5 |
| 00:29:50–52 | Minneapolis examples ×6 (≤3 each) | 2016-01-01 ≤ issueDate < 2020-01-01 | 5 |
| 00:30:04–14 | Charlotte examples ×7 (≤3 each) | 2021-01-01 ≤ issuedate < 2023-06-01, taxjuris CHARLOTTE | 5 |
| 00:30:30–32 | Charlotte subdiv-populated examples ×2 | issuedate < 2023-06-01; 2019-01-01 ≤ issuedate < 2023-01-01 | 5 |
| 00:30:33 | Charlotte distinct zonecode | 2022-01-01 ≤ issuedate < 2023-06-01 | 2 |
| 00:30:47–49 | Raleigh examples ×9 (≤3 each) | 2020-01-01 ≤ issueddate < 2021-07-06, inside city | 5 |
| 00:31:07–08 | Raleigh earliest missing_middle='No'; 104, 103, text examples | issueddate < 2021-07-06 (various starts) | 5 |
| 00:31:08–09 | Raleigh distinct missing_middle and adu_type, **all years, labels only** | none (see note 1) | 2 |
| 00:31:19 | Sacramento OBJECTID ≤ 2 (to learn date format; both rows 2016-01-01) | OBJECTID ≤ 2 (see note 2) | 5 |
| 00:31:31–34 | Sacramento distinct Type, Sub_Type, Category, Rpt_Status, Activity_Code | Status_Date year 2014–2023 | 2 |
| 00:31:50–52 | Sacramento examples ×11 (≤3 each) | Status_Date year 2021–2023 | 5 |
| 00:32:01 | Austin Socrata metadata /api/views/3syk-w9eu.json | – | 1 |
| 00:32:09–11 | Austin distinct permit_class, work_class, condominium, permit_type_desc ($group, no count) | 2021-01-01 ≤ issue_date < 2024-02-05, permittype BP | 2 |
| 00:32:23–48 | Austin examples ×10 (≤3 each) | same window, work_class New | 5 |
| 00:33:08 | Portland CSV: labels + examples (later rows dropped in code before printing) | 2015-01-01 ≤ ISSUEDATE < 2021-08-01 | 3/5 |
| 00:33:23 | Portland CSV: Rowhouse, TH 3+, conversion examples | ISSUEDATE < 2021-08-01 | 5 |
| 00:33:37 | ArcGIS search: Mecklenburg, Durham items; Houston CKAN package_search | – | 1 |
| 00:33:47 | Mecklenburg item fc9d171e… and Durham item 266bb082… pages; Durham layer fields | – | 1 |
| 00:33:58–34:01 | Houston CKAN searches ×4; Durham distinct BLD_Type, Occupancy, TYPE, PROJECT_TYPE, BLDB_ACTIVITY | Durham: 2017-01-01 ≤ ISSUE_DATE < 2019-10-01 | 1/2 |
| 00:34:08 | Houston package_show residential-building-permits | – | 1 |
| 00:34:13 | Houston datastore_search limit=0 (fields only, 0 records) | n/a | 2 |
| ~00:34:30 | Web search + Sacramento hub item page (404) + Sacramento Terms of Use PDF (text extracted locally) | – | 1 |
| 00:34:47 | Raleigh service metadata XML | – | 1 |
| ~00:35:00 | Austin terms story page (JS only, not readable) ×3 tries; Raleigh "missing middle" web search | – | 1 |
| ~00:35:10 | Raleigh Missing Middle Metrics page (raleighnc.gov), fetched with instruction to report definitions only, no numbers | – (see note 3) | 1 |

## Edge cases and possible rule issues (all reported)
1. **Raleigh missing_middle / adu_type labels without a date filter (rule 2).** Labels seen: null, '', No, Yes; and null, '', Attached ADU, Detached ADU, Internal ADU, "NOT Accessory Dwelli". These are labels only, with no counts and no dates. This shows that "Yes" and "Internal ADU" exist in some year, probably after the reform.
2. **Sacramento OBJECTID ≤ 2** had no date filter. Both rows returned were 2016-01-01 repair permits (pre-reform).
3. **Raleigh Missing Middle Metrics page** probably shows post-reform counts. It was read through a fetch helper told to return definitions only. The summary I received had no numbers, only the collection window (2021-07-06 to 2026-07-14) and link names. The linked archival PDF and dashboards were **not** opened.
4. A pre-reform Raleigh record contained a 2026 staff note on code review. This is not an outcome, but it shows codes are being revised after the fact.
5. Portland: the code loaded post-reform rows into memory, dropped them by ISSUEDATE and never printed them. Houston: no rows opened.
6. No counts, sums or charts of any post-reform period were seen. No before/after comparison was made.
