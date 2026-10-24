# Sun Prairie, WI: submitted permits (Power BI report)

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `sun_prairie_permits`  
**Handbook listing:** Not in the handbook. Same-market restrictive check against Madison.

## Summary

| | |
|---|---|
| Publisher | City of Sun Prairie (Power BI publish-to-web report 'All Submitted Permits Report') |
| What it is | Every submitted permit record: record number, record type, description, parcel, status, street address, subdivision and date submitted. |
| Geography | Street address and Dane County 12-digit parcel number, matched to V12 parcels. |
| Time coverage and update frequency | Submitted 2015-07 to the last model refresh (Munis records to mid-2021, OpenGov after). |
| Units | One row per submitted record. |
| Access method | Linked from https://cityofsunprairie.com/974/Construction-Reports. The anonymous Power BI querydata API is queried once per year by missing_middleware/permits/sun_prairie.py. |
| License | No open-data license stated. A report published to the web by the City; cite the City and the access date. |
| Use in our model | Historical ADU-equivalent series next to Madison. See docs/gate2/COMPARISON_PERMITS.md. |
| Caveats | Submission date only, no issue date; withdrawn, void and denied records add 0 units. No dwelling-unit field. Counts run 14-29% below Census BPS in 2016, 2021 and 2022. Owner Name and Contractor are never requested. |

## Access details

- Endpoint used for the sample: `https://app.powerbigov.us/view?r=eyJrIjoiZmI1ZTVjMDktNDA2OS00ZWJmLWE0MGUtYjBhYTUxZjVlNzQxIiwidCI6ImJiNmMzYjZlLTllYTEtNGNkMS1iODExLTc4N2ZiNmU0MzkxNCJ9&pageName=ReportSection`
- Sample window: submitted in 2025
- Permits in the window: 2859
- Power BI publish-to-web report, queried for one submission year. Owner Name and Contractor are never requested; builder names are removed from new-home descriptions. Records that add units are listed first.

## Fields (20)

| Field | Type | Meaning |
|---|---|---|
| `permit_id` | string | Permit or record number, as published. |
| `permit_type` | string | Permit type as published. |
| `use_class` | string | Use class. Here it repeats the permit type or record kind. |
| `address_raw` | string | Site address as published. |
| `units_raw` | string | Dwelling units added, calculated from the type and description (see units_basis). |
| `description` | string | Free-text work description, with names removed. |
| `issue_date` | string | Date submitted (there is no issue date). |
| `est_cost` | string | Estimated cost, dollars (blank when not published). |
| `bldg_sqft` | string | Building square feet (not published here, so blank). |
| `jurisdiction_id` | string | County subdivision GEOID of the municipality. |
| `source_id` | string | Pipeline source id. |
| `parcel_raw` | string | Parcel number as printed on the permit. |
| `parcel_key` | string | Parcel number normalised to match the V12 PARCELID. |
| `address_unit` | string |  |
| `units_basis` | string | Where units_raw came from: the permit type, the description text, or both. |
| `record_kind` | string | Record kind from the pipeline's classifier (for example new single-family). |
| `record_status` | string | Record status as published. |
| `withdrawn` | string | True when the status is withdrawn, void, denied or stopped. |
| `subdivision` | string | Subdivision name. |
| `record_ct` | string | Record count from the Power BI model (normally 1). |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Sample rows

First 3 of 5 rows in [`data/sample/sun_prairie_permits.csv`](../../data/sample/sun_prairie_permits.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `permit_id` | OTFD-25-100 | OTFD-25-103 | OTFD-25-118 | OTFD-25-12 | OTFD-25-122 |
| `permit_type` | OTFD - One or two-family homes  new construction, additions… | OTFD - One or two-family homes  new construction, additions… | OTFD - One or two-family homes  new construction, additions… | OTFD - One or two-family homes  new construction, additions… | OTFD - One or two-family homes  new construction, additions… |
| `use_class` | new_sf | new_sf | new_sf | new_sf | new_sf |
| `address_raw` | LONNIE LN | WAVERLY WAY | WINDING STREAM WAY | WATER LILY CIR | WAVERLY WAY |
| `units_raw` | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| `description` | single family home construction | SINGLE FAMILY RESIDENCE - NEW CONSTRUCTION | SINGLE FAMILY RESIDENCE - NEW CONSTRUCTION | SINGLE FAMILY HOME- NEW CONSTRUCTION | SINGLE FAMILY RESIDENCE - NEW CONSTRUCTION |
| `issue_date` | 2025-03-31 11:16:21 | 2025-04-01 14:37:29 | 2025-04-14 15:47:33 | 2025-01-16 08:39:58 | 2025-04-15 09:53:18 |
| `jurisdiction_id` | 5502578600 | 5502578600 | 5502578600 | 5502578600 | 5502578600 |
| `source_id` | sun_prairie_permits | sun_prairie_permits | sun_prairie_permits | sun_prairie_permits | sun_prairie_permits |
| `parcel_raw` | 09103626**** | 09103616**** | 08101316**** | 08101331**** | 09113124**** |
| `parcel_key` | 09103626**** | 09103616**** | 08101316**** | 08101331**** | 09113124**** |
| `units_basis` | type+text | type+text | type+text | type+text | type+text |
| `record_kind` | new_sf | new_sf | new_sf | new_sf | new_sf |
| `record_status` | Complete | Complete | Complete | Complete | Complete |
| `withdrawn` | False | False | False | False | False |
| `subdivision` | SERENITY ESTATES | RESERVE, THE | SMITH'S CROSSING - 6TH ADDITION |  |  |
| `record_ct` | 1 | 1 | 1 | 1 | 1 |

## Refresh

```sh
python3 scripts/fetch_samples.py sun_prairie_permits
python3 scripts/build_data_dictionaries.py
```
