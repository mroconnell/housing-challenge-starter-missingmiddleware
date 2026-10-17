# Tennessee: Comptroller parcel and land use data

**Status:** Manual request only (not fetched) (last fetch 2026-10-17)  
**Source id:** `tn_comptroller`  

## Summary

| | |
|---|---|
| Publisher | Tennessee Comptroller of the Treasury, Division of Property Assessments |
| What it is | Statewide parcel and land use maps. |
| Geography | Parcel. |
| Time coverage and update frequency | Varies. |
| Units | Varies. |
| Access method | Request form on https://comptroller.tn.gov. No open download. |
| License | Per request terms. |
| Use in our model | Parcel inventory for Tennessee if the request is granted. |
| Caveats | Needs a manual request. Cannot be part of an automated data pipeline as-is. |

## Access details

- Endpoint used for the sample: `https://comptroller.tn.gov/office-functions/pa/gisredistricting/redistricting-and-land-use-maps/parcel-data.html`
- Parcel and land use data require a request form. Not fetched automatically.

## What the source page says

> Parcel Data var digitalData = { pageInfo: {} }; digitalData.pageInfo.pageName = "office-functions:pa:gisredistricting:redistricting-and-land-use-maps:parcel-data"; Skip to Main Content Go to Comptroller.TN.gov Section Close Menu Print This Page Go to Home \| Tennessee Comptroller of the Treasury About Us Comptroller of the Treasury Jason E. Mumpower Comptroller Emeritus Justin P. Wilson Learn About Our Office Public Records Requests Office Functions Research and Education Accountability State Audit Local Government Audit Investigations Property Assessments State Assessed Properties State Government Finance Local Government Finance Research and Education Accountability Research and Education Accountability Health Provider Review Open Records Counsel Small Business Advocate Higher Education Resource Officer Boards State Board of Equalization State Funding Board Tennessee Local Development Authority Tennessee State School Bond Authority State Energy Policy Council Tennessee Board of Utility Regulation Tennessee Transportation Financing Authority Joint Capital Tourism Board Find a Report Maps Careers News Contact Us Print This Page Go to Search Download Redistricting, Land Use Maps an…

## Sample rows

First 0 of 0 rows in [`data/sample/tn_comptroller.csv`](../../data/sample/tn_comptroller.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

_No sample rows._

## Refresh

```sh
python3 scripts/fetch_samples.py tn_comptroller
python3 scripts/build_data_dictionaries.py
```
