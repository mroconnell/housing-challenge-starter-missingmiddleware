# Madison, WI: building permit Construction Summary report

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `madison_permits`  
**Handbook listing:** Not in the handbook. Record-level permits for the Madison ADU pilot.

## Summary

| | |
|---|---|
| Publisher | City of Madison, Building Inspection (Accela permit system) |
| What it is | Every issued building permit in a date range: permit number, use class, address, square feet, estimated cost, units and description. The pipeline finds ADUs from the description text. |
| Geography | Street address. No parcel number or coordinates; the pipeline matches addresses to Madison address points. |
| Time coverage and update frequency | Issue dates 2010 to today. The report has issue date only (no application or final dates). |
| Units | One row per permit (reissued permits can appear twice). |
| Access method | SQL Server Reporting Services report at https://cityreports.cityofmadison.com/CityReports/ReportViewer/ReportViewer/?ReportPath=/Web%20Access/Building/Permits/Construction%20Summary, exported to CSV by missing_middleware/permits/madison.py. |
| License | No open-data license stated. A public-records report on the city website; cite the city and record the access date. |
| Use in our model | Observed Madison ADU permits by year, the floor for ADU uptake paths. See docs/gate2/MADISON_PERMITS.md. |
| Caveats | No ADU flag: ADUs come from keyword matching in descriptions. The raw report includes owner names and addresses; we drop them at fetch. About 5 MB per year, so never commit full pulls. |

## Access details

- Endpoint used for the sample: `https://cityreports.cityofmadison.com/CityReports/ReportViewer/ReportViewer/?ReportPath=/Web%20Access/Building/Permits/Construction%20Summary`
- Sample window: 2026-09-17 to 2026-09-30
- Permits in the window: 672
- SSRS report, run for a two-week window. Owner and contractor columns are dropped at fetch, as the pipeline does. New residential permits (BLDNRC) are listed first.

## Fields (9)

| Field | Type | Meaning |
|---|---|---|
| `B1_ALT_ID` | string | Permit number, for example BLDNRC-2024-10730. Prefix BLDNRC = new residential construction (holds the ADUs), BLDNCC = new commercial/multifamily, BLDRPR = repair/alteration, BLDRRZ/BLDCRZ = razing. |
| `Reportable_Data` | string | Use class, for example SINGLE FAMILY RESIDENCES. |
| `Address_Part_Address_Line` | string | Street address of the work. |
| `BLDG_SQFT` | string | Building square feet. |
| `Textbox9` | string | Estimated construction cost, dollars. |
| `Total_Pay` | string | Permit fees paid, dollars. |
| `Textbox13` | string | Dwelling units added (Dwell). |
| `Detailed_Description` | string | Free-text work description. ADUs are found by keyword here. |
| `Issuance_Date` | string | Permit issue date. |

## Sample rows

First 3 of 5 rows in [`data/sample/madison_permits.csv`](../../data/sample/madison_permits.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`. House and unit numbers are removed (street names kept), parcel and record ids are masked to their first 2 characters plus `***`, and coordinates are rounded.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `B1_ALT_ID` | BLDNRC-2026-18290 | BLDNRC-2026-20255 | BLDNRC-2026-22006 | BLDNRC-2026-21587 | BLDNRC-2026-22062 |
| `Reportable_Data` | TWO FAMILY RESIDENCES | TWO FAMILY RESIDENCES | RESIDENTIAL GARAGES | RESIDENTIAL GARAGES | RESIDENTIAL GARAGES |
| `Address_Part_Address_Line` | SPAIGHT ST | TOMPKINS | GREGORY ST | OAKRIDGE AVE | ROGERS ST |
| `BLDG_SQFT` | 425 | 2,994 | 320 | 280 | 400 |
| `Textbox9` | $190,500 | $200,000 | $22,000 | $36,785 | $63,423 |
| `Total_Pay` | $168 | $810 | $75 | $75 | $75 |
| `Textbox13` | 0 | 2 | 0 | 0 | 0 |
| `Detailed_Description` | TWO STORY HEATED ADDITION WITH NEW DECK | NEW TWIN HOME ADU | 16 X 20 DETACHED GARAGE | 280 SQ FT DETACHED UNHEATED GARAGE | 20.5 X 19.5 DETACHED GARAGE |
| `Issuance_Date` | 09/17/2026 | 09/30/2026 | 09/23/2026 | 09/25/2026 | 09/28/2026 |

## Refresh

```sh
python3 scripts/fetch_samples.py madison_permits
python3 scripts/build_data_dictionaries.py
```
