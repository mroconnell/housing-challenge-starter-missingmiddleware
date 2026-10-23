# Utah: Statewide parcels (LIR)

**Status:** Fetched (last fetch 2026-10-23)  
**Source id:** `ut_parcels`  

## Summary

| | |
|---|---|
| Publisher | Utah Geospatial Resource Center (UGRC) |
| What it is | County parcels with Land Information Records (LIR): property class, value, building square feet, year built. |
| Geography | Parcel, one layer per county. |
| Time coverage and update frequency | Updated yearly per county. |
| Units | Dollars, square feet, acres. |
| Access method | https://gis.utah.gov/products/sgid/cadastre/parcels/ and UGRC ArcGIS services. |
| License | Open (see UGRC). |
| Use in our model | Parcel inventory with property type and value. |
| Caveats | One layer per county. No zoning. |

## Access details

- Endpoint used for the sample: `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/Parcels_SaltLake_LIR/FeatureServer/0`
- Layer: Parcels_SaltLake_LIR
- Total records at fetch time: 399432
- Last edited: 2026-10-14
- Geometry: esriGeometryPolygon

## Fields (30)

| Field | Type | Meaning |
|---|---|---|
| `OBJECTID` | OID |  |
| `COUNTY_NAME` | String | County Name |
| `COUNTY_ID` | String | County ID |
| `ASSESSOR_SRC` | String | County Assessor Info URL |
| `BOUNDARY_SRC` | String | County Recorder Info URL |
| `DISCLAIMER` | String | Disclaimer URL |
| `CURRENT_ASOF` | Date | Date the county data was current (epoch milliseconds). |
| `PARCEL_ID` | String | Parcel ID |
| `SERIAL_NUM` | String | Serial Number |
| `PARCEL_ADD` | String | Parcel Address |
| `PARCEL_CITY` | String | Parcel City |
| `TAXEXEMPT_TYPE` | String | Tax Exempt Type |
| `TAX_DISTRICT` | String | Tax District |
| `TOTAL_MKT_VALUE` | Double | Total market value, dollars. |
| `LAND_MKT_VALUE` | Double | Land market value, dollars. |
| `PARCEL_ACRES` | Double | Parcel Acres |
| `PROP_CLASS` | String | Property class (Residential, Commercial, Tax Exempt...). |
| `PRIMARY_RES` | String | Y/N: primary residence. |
| `HOUSE_CNT` | String | Number of housing units on the parcel. |
| `SUBDIV_NAME` | String | Subdivision Name |
| `BLDG_SQFT` | Double | Building square feet. |
| `BLDG_SQFT_INFO` | String | Square Footage Note |
| `FLOORS_CNT` | Double | Number of Floors |
| `FLOORS_INFO` | String | Number of Floors Note |
| `BUILT_YR` | SmallInteger | Year built. |
| `EFFBUILT_YR` | SmallInteger | Effective Year Built |
| `CONST_MATERIAL` | String | Construction Material |
| `PROP_TYPE` | String | Property Type |
| `Shape__Area` | Double |  |
| `Shape__Length` | Double |  |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Sample rows

First 3 of 5 rows in [`data/sample/ut_parcels.csv`](../../data/sample/ut_parcels.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 |
|---|---|---|---|
| `OBJECTID` | 1 | 2 | 3 |
| `COUNTY_NAME` | Salt Lake County | Salt Lake County | Salt Lake County |
| `COUNTY_ID` | 18 | 18 | 18 |
| `ASSESSOR_SRC` | https://www.saltlakecounty.gov/assessor/ | https://www.saltlakecounty.gov/assessor/ | https://www.saltlakecounty.gov/assessor/ |
| `BOUNDARY_SRC` | https://www.saltlakecounty.gov/recorder/ | https://www.saltlakecounty.gov/recorder/ | https://www.saltlakecounty.gov/recorder/ |
| `DISCLAIMER` | http://www.utah.gov/disclaimer.html | http://www.utah.gov/disclaimer.html | http://www.utah.gov/disclaimer.html |
| `CURRENT_ASOF` | 1790640000000 | 1790640000000 | 1790640000000 |
| `PARCEL_ID` | 01364000010000 | 08153760150000 | 02131000010000 |
| `SERIAL_NUM` |  |  |  |
| `PARCEL_ADD` | 2121 N 8800 W | 2217 N REDWOOD RD | 3505 N 3200 W |
| `PARCEL_CITY` |  | Salt Lake City |  |
| `TAXEXEMPT_TYPE` | Other |  | Other |
| `TAX_DISTRICT` | ACT | 13 | ACT |
| `TOTAL_MKT_VALUE` | 2048000 | 9061600 | 512000 |
| `LAND_MKT_VALUE` | 2048000 | 2134300 | 512000 |
| `PARCEL_ACRES` | 640 | 4.09 | 160 |
| `PROP_CLASS` | Tax Exempt - Government | Commercial | Tax Exempt - Government |
| `PRIMARY_RES` |  |  |  |
| `HOUSE_CNT` |  | 2 |  |
| `SUBDIV_NAME` |  | M H Cook Commercial Amd |  |
| `BLDG_SQFT` |  | 38645 |  |
| `BLDG_SQFT_INFO` |  |  |  |
| `FLOORS_CNT` |  | 1 |  |
| `FLOORS_INFO` |  | typically includes above grade levels only, except with bas… |  |
| `BUILT_YR` |  | 2008 |  |
| `EFFBUILT_YR` |  | 2012 |  |
| `CONST_MATERIAL` |  | Cn |  |
| `PROP_TYPE` |  |  |  |
| `Shape__Area` | 390849.78515625 | 28892.9140625 | 60963.50390625 |
| `Shape__Length` | 3083.9116359996146 | 756.1444303100632 | 1483.631295212288 |

## Refresh

```sh
python3 scripts/fetch_samples.py ut_parcels
python3 scripts/build_data_dictionaries.py
```
