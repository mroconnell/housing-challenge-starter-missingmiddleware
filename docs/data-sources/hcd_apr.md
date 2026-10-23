# California HCD Housing Element Annual Progress Report (APR) data

**Status:** Fetched (last fetch 2026-10-23)  
**Source id:** `hcd_apr`  
**Handbook listing:** Not in the handbook. Added at the team's request.

## Summary

| | |
|---|---|
| Publisher | California Department of Housing and Community Development (HCD) |
| What it is | Every California city and county reports each year on housing applications, entitlements, building permits and certificates of occupancy, project by project, including ADUs. |
| Geography | Jurisdiction (city or county), with project address/APN in the project-level tables. |
| Time coverage and update frequency | Annual, by calendar year, from 2018 onward. Reports due April 1. |
| Units | Housing units by income category (very low, low, moderate, above moderate) and by unit type (SFA, SFD, 2-4, 5+, ADU, MH). |
| Access method | California Open Data Portal (CKAN): dataset page on https://data.ca.gov, API `https://data.ca.gov/api/3/action/datastore_search?resource_id=...`. |
| License | See the dataset page (California open data terms). |
| Use in our model | The best public evidence on ADU response to state reform: California permits by unit type before and after its ADU laws. Useful to calibrate ADU and missing-middle (SB 9) effects for other states. |
| Caveats | California only. Self-reported by jurisdictions, with uneven quality and late filers. Use as calibration evidence, not as data for another state. |

## Access details

- Endpoint used for the sample: `https://data.ca.gov/dataset/housing-element-annual-progress-report-apr-data-by-jurisdiction-and-year`
- Sample table: APR Table A2

## Fields (70)

| Field | Type | Meaning |
|---|---|---|
| `_id` | int |  |
| `JURIS_NAME` | text | City or county that filed the report. |
| `CNTY_NAME` | text | County. |
| `YEAR` | numeric | Reporting year. |
| `PRIOR_APN` | text | Earlier parcel number, if the parcel was split or merged. |
| `APN` | text | Assessor parcel number of the project. |
| `STREET_ADDRESS` | text | Project street address. |
| `PROJECT_NAME` | text | Project name, if any. |
| `JURS_TRACKING_ID` | text | The jurisdiction's own permit or project id. |
| `UNIT_CAT` | text | Unit category: SFD single-family detached, SFA attached, 2 to 4, 5+, ADU, MH mobile home. |
| `TENURE` | text | R renter or O owner. |
| `ACUTELY_LOW_INCOME_DR` | numeric | Units entitled: acutely low income, deed restricted. |
| `ACUTELY_LOW_INCOME_NDR` | numeric | Units entitled: acutely low income, not deed restricted. |
| `EXTREMELY_LOW_INCOME_DR` | numeric | Units entitled: extremely low income, deed restricted. |
| `EXTREMELY_LOW_INCOME_NDR` | numeric | Units entitled: extremely low income, not deed restricted. |
| `VLOW_INCOME_DR` | numeric | Units entitled: very low income, deed restricted. |
| `VLOW_INCOME_NDR` | numeric | Units entitled: very low income, not deed restricted. |
| `LOW_INCOME_DR` | numeric | Units entitled: low income, deed restricted. |
| `LOW_INCOME_NDR` | numeric | Units entitled: low income, not deed restricted. |
| `MOD_INCOME_DR` | numeric | Units entitled: moderate income, deed restricted. |
| `MOD_INCOME_NDR` | numeric | Units entitled: moderate income, not deed restricted. |
| `ABOVE_MOD_INCOME` | numeric | Units entitled: above moderate income. |
| `ENT_APPROVE_DT1` | text | Date the project was entitled. |
| `NO_ENTITLEMENTS` | numeric | Number of units entitled this year. |
| `BP_ACUTELY_LOW_INCOME_DR` | numeric | Units issued building permits: acutely low income, deed restricted. |
| `BP_ACUTELY_LOW_INCOME_NDR` | numeric | Units issued building permits: acutely low income, not deed restricted. |
| `BP_EXTREMELY_LOW_INCOME_DR` | numeric | Units issued building permits: extremely low income, deed restricted. |
| `BP_EXTREMELY_LOW_INCOME_NDR` | numeric | Units issued building permits: extremely low income, not deed restricted. |
| `BP_VLOW_INCOME_DR` | numeric | Units issued building permits: very low income, deed restricted. |
| `BP_VLOW_INCOME_NDR` | numeric | Units issued building permits: very low income, not deed restricted. |
| `BP_LOW_INCOME_DR` | numeric | Units issued building permits: low income, deed restricted. |
| `BP_LOW_INCOME_NDR` | numeric | Units issued building permits: low income, not deed restricted. |
| `BP_MOD_INCOME_DR` | numeric | Units issued building permits: moderate income, deed restricted. |
| `BP_MOD_INCOME_NDR` | numeric | Units issued building permits: moderate income, not deed restricted. |
| `BP_ABOVE_MOD_INCOME` | numeric | Units issued building permits: above moderate income. |
| `BP_ISSUE_DT1` | text | Date building permits were issued. |
| `NO_BUILDING_PERMITS` | numeric | Number of units issued building permits this year. |
| `CO_ACUTELY_LOW_INCOME_DR` | numeric | Units completed (certificate of occupancy): acutely low income, deed restricted. |
| `CO_ACUTELY_LOW_INCOME_NDR` | numeric | Units completed (certificate of occupancy): acutely low income, not deed restricted. |
| `CO_EXTREMELY_LOW_INCOME_DR` | numeric | Units completed (certificate of occupancy): extremely low income, deed restricted. |
| `CO_EXTREMELY_LOW_INCOME_NDR` | numeric | Units completed (certificate of occupancy): extremely low income, not deed restricted. |
| `CO_VLOW_INCOME_DR` | numeric | Units completed (certificate of occupancy): very low income, deed restricted. |
| `CO_VLOW_INCOME_NDR` | numeric | Units completed (certificate of occupancy): very low income, not deed restricted. |
| `CO_LOW_INCOME_DR` | numeric | Units completed (certificate of occupancy): low income, deed restricted. |
| `CO_LOW_INCOME_NDR` | numeric | Units completed (certificate of occupancy): low income, not deed restricted. |
| `CO_MOD_INCOME_DR` | numeric | Units completed (certificate of occupancy): moderate income, deed restricted. |
| `CO_MOD_INCOME_NDR` | numeric | Units completed (certificate of occupancy): moderate income, not deed restricted. |
| `CO_ABOVE_MOD_INCOME` | numeric | Units completed (certificate of occupancy): above moderate income. |
| `CO_ISSUE_DT1` | text | Date the certificate of occupancy was issued. |
| `NO_OTHER_FORMS_OF_READINESS` | numeric | Number of units completed (certificates of occupancy or similar) this year. |
| `EXTR_LOW_INCOME_UNITS` | numeric | Units for extremely low income households. |
| `APPROVE_SB35` | text | Y/N: approved under SB 35 streamlining. |
| `HISTORIC_SITES` | text | Y/N: project on a historic site. |
| `INFILL_UNITS` | text | Y/N: infill project. |
| `FIN_ASSIST_NAME` | text | Public financing programs used. |
| `DR_TYPE` | text | Type of deed restriction. |
| `NO_FA_DR` | text | Units affordable without financial assistance or deed restriction. |
| `TERM_AFF_DR` | text | Term of the affordability restriction, years. |
| `DEM_DES_UNITS` | numeric | Units demolished or destroyed. |
| `DEM_OR_DES_UNITS` | text | Demolished or destroyed (D) units. |
| `DEM_DES_UNITS_OWN_RENT` | text | Whether demolished units were owner or renter. |
| `DENSITY_BONUS_TOTAL` | numeric | Units added by state density bonus law. |
| `DENSITY_BONUS_NUMBER_OTHER_INCENTIVES` | numeric | Count of other density bonus incentives. |
| `DENSITY_BONUS_INCENTIVES` | text | Density bonus incentives used. |
| `DENSITY_BONUS_RECEIVE_REDUCTION` | text | Y/N: received a parking or development standard reduction. |
| `NOTES` | text | Free-text notes. |
| `LATITUDE` | numeric |  |
| `LONGITUDE` | numeric |  |
| `STD_ADDRESS` | text | Standardized address (added by HCD for geocoding). |
| `SCORE` | numeric | Geocoding match score. |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Field groups

| Fields | Meaning |
|---|---|
| `...INCOME_DR / ..._NDR` | Units by income level. DR = deed restricted affordable; NDR = not deed restricted. |
| `ENT_APPROVE_DT1 / NO_ENTITLEMENTS` | Entitlement date and units entitled that year. |
| `BP_* / BP_ISSUE_DT1 / NO_BUILDING_PERMITS` | Units issued building permits, by income, and permit date. |
| `CO_* / CO_ISSUE_DT1 / NO_OTHER_FORMS_OF_READINESS` | Units given a certificate of occupancy (completed), by income, and date. |
| `LATITUDE / LONGITUDE` | Geocoded project location (added by HCD). |

## Tables in this dataset

| Table | Records | Fields |
|---|---|---|
| APR Table A | 358014 | `JURIS_NAME`, `CNTY_NAME`, `YEAR`, `PRIOR_APN`, `APN`, `STREET_ADDRESS`, `PROJECT_NAME`, `JURS_TRACKING_ID`, `UNIT_CAT`, `TENURE`, `APP_SUBMIT_DT`, `ACUTELY_LOW_INCOME_DR`, `ACUTELY_LOW_INCOME_NDR`, `EXTREMELY_LOW_INCOME_DR`, `EXTREMELY_LOW_INCOME_NDR`, `VLOW_INCOME_DR`, `VLOW_INCOME_NDR`, `LOW_INCOME_DR`, `LOW_INCOME_NDR`, `MOD_INCOME_DR`, `MOD_INCOME_NDR`, `ABOVE_MOD_INCOME`, `TOT_PROPOSED_UNIT… |
| APR Table A2 | 924139 | `JURIS_NAME`, `CNTY_NAME`, `YEAR`, `PRIOR_APN`, `APN`, `STREET_ADDRESS`, `PROJECT_NAME`, `JURS_TRACKING_ID`, `UNIT_CAT`, `TENURE`, `ACUTELY_LOW_INCOME_DR`, `ACUTELY_LOW_INCOME_NDR`, `EXTREMELY_LOW_INCOME_DR`, `EXTREMELY_LOW_INCOME_NDR`, `VLOW_INCOME_DR`, `VLOW_INCOME_NDR`, `LOW_INCOME_DR`, `LOW_INCOME_NDR`, `MOD_INCOME_DR`, `MOD_INCOME_NDR`, `ABOVE_MOD_INCOME`, `ENT_APPROVE_DT1`, `NO_ENTITLEMENTS… |
| APR Table C | 147970 | `JURISDICTION`, `COUNTY`, `YEAR`, `APN`, `STREET_ADDRESS`, `PROJECT_NAME`, `JURS_TRACKING_ID`, `REZONE_DT`, `VLOW_INCOME`, `LOW_INCOME`, `MOD_INCOME`, `ABOVE_MOD_INCOME`, `SHORTFALL_DESC`, `PARCEL_SIZE`, `GEN_PLAN_DESIGNATION`, `ZONING`, `MIN_DENSITY_ALLOWED`, `MAX_DENSITY_ALLOWED`, `REALISTIC_CAPACITY`, `PARCEL_VACANT_NONVACANT`, `DESCRIPTION` |
| APR Table D | 147618 | `JURIS_NAME`, `YEAR`, `PROGRAM_NAME`, `PROGRAM_OBJECTIVE`, `ACCOMPLISHED_DT`, `APPLICABLE_CYCLE`, `PROGRAM_STATUS_LIST`, `PROGRAM_STATUS`, `QUANTIFIED_OUTCOMES_CATEGORY`, `QUANTIFIED_OUTCOMES_COUNT`, `SUPPORTING_DOCUMENTS` |
| APR Table E | 39 | `JURISDICTION`, `COUNTY`, `YEAR`, `APN`, `STREET_ADDRESS`, `PROJECT_NAME`, `JURS_TRACKING_ID`, `VLOW_INCOME`, `LOW_INCOME`, `MOD_INCOME`, `ABOVE_MOD_INCOME`, `DEV_BONUS_DESC`, `DATE_APPROVED` |
| APR Table F | 292 | `JURISDICTION_NAME`, `YEAR`, `ACTIVITY`, `ELI_NON_RHNA`, `VLI_NON_RHNA`, `LI_NON_RHNA`, `TOTAL_UNITS`, `DESCRIPTION`, `ELI_RHNA`, `VLI_RHNA`, `LI_RHNA`, `TOTAL_UNITS_RHNA`, `DESCRIPTION_RHNA` |
| APR Table F2 | 17 | `JURISDICTION`, `COUNTY`, `YEAR`, `PRIOR_APN`, `APN`, `STREET_ADDRESS`, `PROJECT_NAME`, `JURS_TRACKING_ID`, `UNIT_CAT`, `TENURE`, `VLOW_INCOME_DR`, `VLOW_INCOME_NDR`, `LOW_INCOME_DR`, `LOW_INCOME_NDR`, `MOD_INCOME_DR`, `MOD_INCOME_NDR`, `ABOVE_MOD_INCOME`, `TOTAL_CONVERTED`, `DATE_CONVERTED`, `NOTES` |
| APR Table G | 438 | `JURISDICTION`, `COUNTY`, `YEAR`, `APN`, `STREET_ADDRESS`, `PROJECT_NAME`, `JURS_TRACKING_ID`, `REALISTIC_CAPACITY`, `TRANSFERRED_TO`, `INTENDED_USE` |
| APR Table H | 11870 | `JURISDICTION`, `COUNTY`, `YEAR`, `APN`, `STREET_ADDRESS`, `EXISTING_USE_TYPE`, `NUM_OF_UNITS`, `SURPLUS_TYPE`, `PARCEL_SIZE`, `NOTES` |
| APR Table I | 245 | `JURISDICITON`, `COUNTY`, `YEAR`, `APN`, `STREET_ADDRESS`, `PROJECT_NAME`, `JURS_TRACKING_ID`, `ACTIVITY`, `DATE`, `VLOW_INCOME`, `LOW_INCOME`, `MOD_INCOME`, `ABOVE_MOD_INCOME`, `NOTES` |
| APR Table K | 1647 | `JURISDICTION`, `COUNTY`, `YEAR`, `PREFERENCE_POLICY`, `WEBSITE`, `NOTES` |
| APR Table L | 226 | `JURISDICTION`, `COUNTY`, `YEAR`, `APN`, `STREET_ADDRESS`, `DATE_OF_DESIGNATION`, `DESIGNATION_LEVEL`, `HISTORIC_SITE_PERIOD`, `AREAS_OF_SIGNIFICANCE`, `PARCEL_SIZE`, `NOTES` |

HCD publishes a data dictionary (DOCX) for each table on the dataset page.

## Sample rows

First 3 of 5 rows in [`data/sample/hcd_apr.csv`](../../data/sample/hcd_apr.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `_id` | 1 | 2 | 3 | 4 | 5 |
| `JURIS_NAME` | STANISLAUS COUNTY | STANISLAUS COUNTY | STANISLAUS COUNTY | STANISLAUS COUNTY | STANISLAUS COUNTY |
| `CNTY_NAME` | Stanislaus | Stanislaus | Stanislaus | Stanislaus | Stanislaus |
| `YEAR` | 2020 | 2020 | 2020 | 2020 | 2020 |
| `APN` | 081-002-032 | 022-029-112 | 020-003-019 | 041-004-008 | 038-048-002 |
| `STREET_ADDRESS` | 1464 CLARK  RD | 7708 MONTEREY AVE | 4455 HAWKINS RD | 525 GRAYSON | 627 HERNDON RD |
| `JURS_TRACKING_ID` | BLD2002-01052 | BLD2020-0390 | BLD2019-2591 | BLD2018-2134 | BLD2020-0174 |
| `UNIT_CAT` | MH | MH | MH | ADU | ADU |
| `TENURE` | Renter | Owner | Renter | Renter | Renter |
| `ACUTELY_LOW_INCOME_DR` | 0 | 0 | 0 | 0 | 0 |
| `ACUTELY_LOW_INCOME_NDR` | 0 | 0 | 0 | 0 | 0 |
| `EXTREMELY_LOW_INCOME_DR` | 0 | 0 | 0 | 0 | 0 |
| `EXTREMELY_LOW_INCOME_NDR` | 0 | 0 | 0 | 0 | 0 |
| `VLOW_INCOME_DR` | 0 | 0 | 0 | 0 | 0 |
| `VLOW_INCOME_NDR` | 0 | 0 | 0 | 0 | 0 |
| `LOW_INCOME_DR` | 0 | 0 | 0 | 0 | 0 |
| `LOW_INCOME_NDR` | 0 | 0 | 0 | 0 | 0 |
| `MOD_INCOME_DR` | 0 | 0 | 0 | 0 | 0 |
| `MOD_INCOME_NDR` | 0 | 0 | 0 | 0 | 0 |
| `ABOVE_MOD_INCOME` | 0 | 0 | 0 | 0 | 0 |
| `NO_ENTITLEMENTS` | 0 | 0 | 0 | 0 | 0 |
| `BP_ACUTELY_LOW_INCOME_DR` | 0 | 0 | 0 | 0 | 0 |
| `BP_ACUTELY_LOW_INCOME_NDR` | 0 | 0 | 0 | 0 | 0 |
| `BP_EXTREMELY_LOW_INCOME_DR` | 0 | 0 | 0 | 0 | 0 |
| `BP_EXTREMELY_LOW_INCOME_NDR` | 0 | 0 | 0 | 0 | 0 |
| `BP_VLOW_INCOME_DR` | 0 | 0 | 0 | 0 | 0 |
| `BP_VLOW_INCOME_NDR` | 0 | 0 | 0 | 0 | 0 |
| `BP_LOW_INCOME_DR` | 0 | 0 | 0 | 0 | 0 |
| `BP_LOW_INCOME_NDR` | 0 | 0 | 0 | 0 | 0 |
| `BP_MOD_INCOME_DR` | 0 | 0 | 0 | 0 | 0 |
| `BP_MOD_INCOME_NDR` | 0 | 0 | 0 | 0 | 0 |
| `BP_ABOVE_MOD_INCOME` | 1 | 1 | 1 | 0 | 1 |
| `BP_ISSUE_DT1` | 2020-03-05 | 2020-07-15 | 2020-02-12 |  | 2020-03-31 |
| `NO_BUILDING_PERMITS` | 1 | 1 | 1 | 0 | 1 |
| `CO_ACUTELY_LOW_INCOME_DR` | 0 | 0 | 0 | 0 | 0 |
| `CO_ACUTELY_LOW_INCOME_NDR` | 0 | 0 | 0 | 0 | 0 |
| `CO_EXTREMELY_LOW_INCOME_DR` | 0 | 0 | 0 | 0 | 0 |
| `CO_EXTREMELY_LOW_INCOME_NDR` | 0 | 0 | 0 | 0 | 0 |
| `CO_VLOW_INCOME_DR` | 0 | 0 | 0 | 0 | 0 |
| `CO_VLOW_INCOME_NDR` | 0 | 0 | 0 | 0 | 0 |
| `CO_LOW_INCOME_DR` | 0 | 0 | 0 | 0 | 0 |
| `CO_LOW_INCOME_NDR` | 0 | 0 | 0 | 0 | 0 |
| `CO_MOD_INCOME_DR` | 0 | 0 | 0 | 0 | 0 |
| `CO_MOD_INCOME_NDR` | 0 | 0 | 0 | 0 | 0 |
| `CO_ABOVE_MOD_INCOME` | 1 | 1 | 0 | 1 | 1 |
| `CO_ISSUE_DT1` | 2020-03-05 | 2021-01-29 |  | 2020-03-11 | 2020-07-14 |
| `NO_OTHER_FORMS_OF_READINESS` | 1 | 1 | 0 | 1 | 1 |
| `EXTR_LOW_INCOME_UNITS` | 0 | 0 | 0 | 0 | 0 |
| `APPROVE_SB35` | N | N | N | N | N |
| `HISTORIC_SITES` | 0 | 0 | 0 | 0 | 0 |
| `INFILL_UNITS` | 0 | 0 | 0 | 0 | 0 |
| `NO_FA_DR` | 0 | 0 | 0 | 0 | 0 |
| `DEM_DES_UNITS` | 0 | 0 | 0 | 0 | 0 |
| `DENSITY_BONUS_TOTAL` | 0 | 0 | 0 | 0 | 0 |
| `DENSITY_BONUS_NUMBER_OTHER_INCENTIVES` | 0 | 0 | 0 | 0 | 0 |
| `NOTES` | MOBILE HOME ON PRIVATE PROPERTY (PIERS) 2002 GOLDEN WEST HO… | MANUFACTURED DWELLING - 1980 LANCER 1568 SQ FT - NEW HOMESI… | 1152 SQ. FT. MANUFACTURED HOME / 2019 CHAMPION MODEL # CM 3… | Garage Conversion to ADU (Change garage to living space) | ACCESSORY DWELLING UNIT ( 1037 SF ) W/ ATTACHED PATIO COVER… |
| `LATITUDE` | 37.655693 | 37.526333 | 37.571711 | 37.565911 | 37.620783 |
| `LONGITUDE` | -121.085881 | -121.011812 | -120.64586 | -121.000101 | -120.975385 |
| `STD_ADDRESS` | 1464 Clark Rd, Modesto, California, 95358 | 7708 Monterey Ave, Ceres, California, 95307 | 4455 Hawkins Rd, Denair, California, 95316 | 525 W Grayson Rd, Modesto, California, 95358 | 627 Herndon Rd, Modesto, California, 95351 |
| `SCORE` | 93.96 | 94.39 | 88.36 | 92.11 | 88.15 |

## Refresh

```sh
python3 scripts/fetch_samples.py hcd_apr
python3 scripts/build_data_dictionaries.py
```
