# Wisconsin: Statewide parcel map (V-series)

**Status:** Fetched (last fetch 2026-10-17)  
**Source id:** `wi_parcels`  

## Summary

| | |
|---|---|
| Publisher | Wisconsin State Cartographer's Office / Department of Administration |
| What it is | Standardized statewide parcels with property class, values, and address. |
| Geography | Parcel, statewide. |
| Time coverage and update frequency | Yearly version (V10, V11...). |
| Units | Dollars, acres. |
| Access method | https://www.sco.wisc.edu/parcels/data/ (download by county) and ArcGIS FeatureServer. |
| License | Open (see SCO). |
| Use in our model | One of the best statewide parcel schemas. Zoning is collected separately by SCO. |
| Caveats | Values and classes come from local assessors and vary in quality. |

## Access details

- Endpoint used for the sample: `https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/Wisconsin_Statewide_Parcels_DB/FeatureServer/0`
- Layer: V1200_WisconsinParcels_2026
- Total records at fetch time: 3574646
- Last edited: 2026-06-30
- Item: Wisconsin Statewide Parcels DB (owner `djvogel2_WI_DOA`, id `2386813b23ea4e51a009f7d1d6b76e02`)
- Geometry: esriGeometryPolygon

## Fields (47)

| Field | Type | Meaning |
|---|---|---|
| `OBJECTID` | OID |  |
| `STATEID` | String | State ID |
| `PARCELID` | String | Parcel ID |
| `TAXPARCELID` | String | Tax Parcel ID |
| `PARCELDATE` | String | Parcel Date |
| `TAXROLLYEAR` | String | Tax Roll Year |
| `OWNERNME1` | String | Primary owner name. Redacted in our sample. |
| `OWNERNME2` | String | Secondary owner name. Redacted in our sample. |
| `PSTLADRESS` | String | Owner mailing address. Redacted in our sample. |
| `SITEADRESS` | String | Full Physical Address |
| `ADDNUMPREFIX` | String | Address Number Prefix |
| `ADDNUM` | String | Address Number |
| `ADDNUMSUFFIX` | String | Address Number Suffix |
| `PREFIX` | String | Prefix |
| `STREETNAME` | String | Street Name |
| `STREETTYPE` | String | Street Type |
| `SUFFIX` | String | Suffix |
| `LANDMARKNAME` | String | Landmark Name |
| `UNITTYPE` | String | Unit Type |
| `UNITID` | String | Unit ID |
| `PLACENAME` | String | Place Name |
| `ZIPCODE` | String | Zip Code |
| `ZIP4` | String | Zip Code Plus 4 |
| `STATE` | String | State |
| `SCHOOLDIST` | String | School District |
| `SCHOOLDISTNO` | String | School District Number |
| `CNTASSDVALUE` | Double | Total assessed value, dollars. |
| `LNDVALUE` | Double | Assessed Value of Land |
| `IMPVALUE` | Double | Assessed Value of Improvements |
| `MFLVALUE` | Double | Assessed Value of MFL/FCL Land |
| `ESTFMKVALUE` | Double | Estimated fair market value, dollars. |
| `NETPRPTA` | Double | Net Property Tax |
| `GRSPRPTA` | Double | Gross Property Tax |
| `PROPCLASS` | String | Wisconsin property class. 1 residential, 2 commercial, 3 manufacturing, 4 agricultural, 5 undeveloped, 5M ag forest, 6 forest, 7 other, X1-X4 exempt. |
| `AUXCLASS` | String | Auxiliary class for exempt or special lands. |
| `ASSDACRES` | Double | Assessed Acres |
| `DEEDACRES` | Double | Deeded Acres |
| `GISACRES` | Double | Parcel area from GIS geometry, acres. |
| `CONAME` | String | County Name |
| `LOADDATE` | String | Load Date |
| `PARCELFIPS` | String | County FIPS code of the source. |
| `PARCELSRC` | String | Parcel Source |
| `LONGITUDE` | Double |  |
| `LATITUDE` | Double |  |
| `SITEADRESS_STAND` | String |  |
| `Shape__Area` | Double |  |
| `Shape__Length` | Double |  |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Sample rows

First 3 of 5 rows in [`data/sample/wi_parcels.csv`](../../data/sample/wi_parcels.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 |
|---|---|---|---|
| `OBJECTID` | 1 | 2 | 3 |
| `STATEID` | 001008002310010 | 001008014680000 | 001008014480000 |
| `PARCELID` | 008002310010 | 008014680000 | 008014480000 |
| `TAXPARCELID` |  |  |  |
| `PARCELDATE` |  |  |  |
| `TAXROLLYEAR` | 2025 | 2025 | 2025 |
| `OWNERNME1` | [redacted] | [redacted] | [redacted] |
| `OWNERNME2` |  |  | [redacted] |
| `PSTLADRESS` | [redacted] | [redacted] | [redacted] |
| `SITEADRESS` | 3733 STATE ROAD 13 | 1339 GEM CT | 3725 13TH AVE |
| `ADDNUMPREFIX` |  |  |  |
| `ADDNUM` | 3733 | 1339 | 3725 |
| `ADDNUMSUFFIX` |  |  |  |
| `PREFIX` | STATE ROAD |  |  |
| `STREETNAME` | 13 | GEM | 13TH |
| `STREETTYPE` |  | COURT | AVENUE |
| `SUFFIX` |  |  |  |
| `LANDMARKNAME` |  |  |  |
| `UNITTYPE` |  |  |  |
| `UNITID` |  |  |  |
| `PLACENAME` | TOWN OF DELL PRAIRIE | TOWN OF DELL PRAIRIE | TOWN OF DELL PRAIRIE |
| `ZIPCODE` |  |  |  |
| `ZIP4` |  |  |  |
| `STATE` | WI | WI | WI |
| `SCHOOLDIST` | WISCONSIN DELLS SCHOOL DISTRICT | WISCONSIN DELLS SCHOOL DISTRICT | WISCONSIN DELLS SCHOOL DISTRICT |
| `SCHOOLDISTNO` | 6678 | 6678 | 6678 |
| `CNTASSDVALUE` | 94500 | 194400 | 175300 |
| `LNDVALUE` | 22700 | 39200 | 42200 |
| `IMPVALUE` | 71800 | 155200 | 133100 |
| `MFLVALUE` |  |  |  |
| `ESTFMKVALUE` | 110700 | 227700 | 205300 |
| `NETPRPTA` | 1097.67 | 2316.19 | 2083.22 |
| `GRSPRPTA` | 1097.67 | 2316.19 | 2083.22 |
| `PROPCLASS` | 1 | 1 | 1 |
| `AUXCLASS` |  |  |  |
| `ASSDACRES` | 1.27 | 0.41 | 0.5 |
| `DEEDACRES` | 1.27 | 0.41 | 0.5 |
| `GISACRES` | 1.07 | 0.41 | 0.5 |
| `CONAME` | ADAMS | ADAMS | ADAMS |
| `LOADDATE` | 3/04/2026 | 3/04/2026 | 3/04/2026 |
| `PARCELFIPS` | 001 | 001 | 001 |
| `PARCELSRC` | ADAMS | ADAMS | ADAMS |
| `LONGITUDE` | -89.81329557339049 | -89.82514291109914 | -89.81874527912566 |
| `LATITUDE` | 43.708437821023544 | 43.710686495136024 | 43.70921449944699 |
| `SITEADRESS_STAND` | 3733 STH 13 | 1339 GEM COURT | 3725 13TH AVENUE |
| `Shape__Area` | 8325.3046875 | 3163.0546875 | 3855.09765625 |
| `Shape__Length` | 375.0245305387647 | 232.01973696079494 | 253.21304213326442 |

## Refresh

```sh
python3 scripts/fetch_samples.py wi_parcels
python3 scripts/build_data_dictionaries.py
```
