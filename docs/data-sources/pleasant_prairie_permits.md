# Pleasant Prairie, WI: issued permits (SmartGov detail report)

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `pleasant_prairie_permits`  
**Handbook listing:** Not in the handbook. Record-level permits for the restrictive comparison pilot.

## Summary

| | |
|---|---|
| Publisher | Village of Pleasant Prairie (SmartGov public report, Exago WebReports) |
| What it is | Every issued permit in a date range: permit type, number, estimated cost, issue date, site address, parcel number and description. |
| Geography | Site address and Kenosha County parcel number (for example 91-4-122-084-0706), matched to V12 parcels. |
| Time coverage and update frequency | Issue dates 2003-10 to today (dense from 2008). |
| Units | One row per permit. |
| Access method | Form post on https://vlg-pleasantprairie-wi.smartgovcommunity.com/Public/ReportsView, then Exago JSON calls. Scripted in missing_middleware/permits/pleasant_prairie.py. CSV and Excel export are disabled, so the report is read as RTF. |
| License | No open-data license stated. A public report on the Village's portal; cite the Village and the access date. |
| Use in our model | ADU-equivalent series for a place that prohibits ADUs. See docs/gate2/COMPARISON_PERMITS.md. |
| Caveats | No dwelling-unit field: units are calculated from the permit type. No year built anywhere public, so a prior dwelling is read from the parcel's permit history. The raw report has owner names, mailing addresses and contractors; the pipeline's loader drops them, and the sample uses that loader. About 29 MB of RTF per year. |

## Access details

- Endpoint used for the sample: `https://vlg-pleasantprairie-wi.smartgovcommunity.com/Public/ReportsView/ViewReport?reportId=361fe732-f57f-4e4c-827c-72b67cc09ca6&reportType=Exago`
- Sample window: 2026-09-01 to 2026-09-30
- Permits in the window: 213
- SmartGov/Exago report, run for one month and exported as RTF. Rows are the pipeline's standard frame: owner, contractor and fee fields are dropped, and owner names are removed from descriptions. New-building and razing permits are listed first.

## Fields (16)

| Field | Type | Meaning |
|---|---|---|
| `permit_id` | string | Permit or record number, as published. |
| `permit_type` | string | Permit type as published. |
| `use_class` | string | Use class. Here it repeats the permit type or record kind. |
| `address_raw` | string | Site address as published. |
| `units_raw` | string | Dwelling units added, calculated from the type and description (see units_basis). |
| `description` | string | Free-text work description, with names removed. |
| `issue_date` | string | Permit issue date. |
| `est_cost` | string | Estimated cost, dollars (blank when not published). |
| `bldg_sqft` | string | Building square feet (not published here, so blank). |
| `jurisdiction_id` | string | County subdivision GEOID of the municipality. |
| `source_id` | string | Pipeline source id. |
| `parcel_raw` | string | Parcel number as printed on the permit. |
| `parcel_key` | string | Parcel number normalised to match the V12 PARCELID. |
| `address_unit` | string |  |
| `units_basis` | string | Where units_raw came from: the permit type, the description text, or both. |
| `description_prefix_removed` | string |  |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Sample rows

First 3 of 5 rows in [`data/sample/pleasant_prairie_permits.csv`](../../data/sample/pleasant_prairie_permits.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `permit_id` | SF26-07-125 | COM26-07-038 | COM26-08-016 | COM26-09-003 | COM26-09-018 |
| `permit_type` | NEW SINGLE FAMILY DWELLING | COMMERCIAL LOW VOLTAGE ELECTRICAL | COMMERCIAL LOW VOLTAGE ELECTRICAL | COMMERCIAL LOW VOLTAGE ELECTRICAL | COMMERCIAL LOW VOLTAGE ELECTRICAL |
| `use_class` | NEW SINGLE FAMILY DWELLING | COMMERCIAL LOW VOLTAGE ELECTRICAL | COMMERCIAL LOW VOLTAGE ELECTRICAL | COMMERCIAL LOW VOLTAGE ELECTRICAL | COMMERCIAL LOW VOLTAGE ELECTRICAL |
| `address_raw` | 113TH ST | 122ND ST | 128TH AVE | 76TH ST | 120TH AVE |
| `units_raw` | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `description` | NEW SINGLE FAMILY HOME | Low voltage fire alarm | Lilly 1st floor Office and Lobby Remodel | Electrical for Wall Sign | Signage Installation (1) Blade Sign and (1) Backlit Channel… |
| `issue_date` | 2026-09-14 00:00:00 | 2026-09-21 00:00:00 | 2026-09-04 00:00:00 | 2026-09-23 00:00:00 | 2026-09-25 00:00:00 |
| `est_cost` | 674892.0 | 118763.0 | 10200.0 | 5200.0 | 2675.0 |
| `jurisdiction_id` | 5505963300 | 5505963300 | 5505963300 | 5505963300 | 5505963300 |
| `source_id` | pleasant_prairie_permits | pleasant_prairie_permits | pleasant_prairie_permits | pleasant_prairie_permits | pleasant_prairie_permits |
| `parcel_raw` | 92-4-122-263-**** | 92-4-122-312-**** | 91-4-121-244-**** | 91-4-122-082-**** | 92-4-122-302-**** |
| `parcel_key` | 92-4-122-263-**** | 92-4-122-312-**** | 91-4-121-244-**** | 91-4-122-082-**** | 92-4-122-302-**** |
| `units_basis` | type | none | none | none | none |
| `description_prefix_removed` | False | False | False | False | False |

## Refresh

```sh
python3 scripts/fetch_samples.py pleasant_prairie_permits
python3 scripts/build_data_dictionaries.py
```
