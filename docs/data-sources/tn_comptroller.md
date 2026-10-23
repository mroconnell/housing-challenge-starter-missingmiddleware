# Tennessee: Comptroller parcel data

**Status:** Manual request only (not fetched) (last fetch 2026-10-23)  
**Source id:** `tn_comptroller`  

## Summary

| | |
|---|---|
| Publisher | Tennessee Comptroller of the Treasury, Division of Property Assessments (Geographic Services) |
| What it is | Statewide parcel shapefiles by county, joined to assessment records through the GISLINK field. |
| Geography | Parcel. 86 of 95 counties; the other 9 come from county assessors. |
| Time coverage and update frequency | Updated weekly. No historical downloads. |
| Units | Esri shapefile plus an Assessment_Data dbf table. |
| Access method | Free. Fill in the request form embedded on the Parcel Data page (https://comptroller.tn.gov/office-functions/pa/gisredistricting/redistricting-and-land-use-maps/parcel-data.html). The direct Formstack link says the form cannot be found, so use the page. The form asks for name, mailing address, counties, attestation and disclaimer checkboxes. Contact GIS.Data@cot.tn.gov. |
| License | Disclaimer only (no warranty). The page says the data can be used in a commercial application. |
| Use in our model | Parcel inventory for Tennessee, if the team picks Tennessee. |
| Caveats | Each download needs a signed form, and the page says it offers no automated downloads. So it cannot be part of an automated pipeline as-is. |

## Access details

- Endpoint used for the sample: `https://comptroller.tn.gov/office-functions/pa/gisredistricting/redistricting-and-land-use-maps/parcel-data.html`
- Free weekly-updated county shapefiles, but each download goes through a Formstack form that asks for a name, mailing address, the counties wanted, and two signed checkboxes (an attestation and a disclaimer). 86 counties are offered. Chester, Davidson, Hamilton, Hickman, Knox, Montgomery, Rutherford, Shelby and Williamson come from county assessors instead. The page also says there are no automate…

## What the source page says

> Parcel Data var digitalData = { pageInfo: {} }; digitalData.pageInfo.pageName = "office-functions:pa:gisredistricting:redistricting-and-land-use-maps:parcel-data"; Skip to Main Content Go to Comptroller.TN.gov Section Close Menu Print This Page Go to Home \| Tennessee Comptroller of the Treasury About Us Comptroller of the Treasury Jason E. Mumpower Comptroller Emeritus Justin P. Wilson Learn About Our Office Public Records Requests Office Functions Research and Education Accountability State Audit Local Government Audit Investigations Property Assessments State Assessed Properties State Government Finance Local Government Finance Research and Education Accountability Health Provider Review Open Records Counsel Small Business Advocate Higher Education Resource Officer Boards State Board of Equalization State Funding Board Tennessee Local Development Authority Tennessee State School Bond Authority State Energy Policy Council Tennessee Board of Utility Regulation Tennessee Transportation Financing Authority Joint Capital Tourism Board Find a Report Maps Careers News Contact Us Print This Page Go to Search Download Redistricting, Land Use Maps and Parcel Data Land Use Maps County Dis…

## Sample rows

None. See the status above. What we did find is in [`data/sample/tn_comptroller.meta.json`](../../data/sample/tn_comptroller.meta.json).


## Refresh

```sh
python3 scripts/fetch_samples.py tn_comptroller
python3 scripts/build_data_dictionaries.py
```
