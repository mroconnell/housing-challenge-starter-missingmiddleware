# Wisconsin: Statewide parcel map (V-series)

**Status:** Fetched (last fetch 2026-10-24)  
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

## Geometry sample

[`data/sample/geo/wi_parcels.geojson`](../../data/sample/geo/wi_parcels.geojson) has 3 features. For privacy each parcel or unit outline is replaced by its bounding box on a 0.01-degree grid (about 1 km across), so the file shows the layer's attributes and rough location but cannot locate a property. Attributes are masked the same way as the CSV. Coordinates are WGS84 longitude/latitude.

| | |
|---|---|
| Geometry type | Polygon |
| Source coordinate system | EPSG:3857 (Esri 102100) |
| Vertices per feature in the source | 8, 10, 40 |
| Max features per request | 2000 |
| Paging supported | yes |

## Sample rows

First 3 of 5 rows in [`data/sample/wi_parcels.csv`](../../data/sample/wi_parcels.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`. House and unit numbers are removed (street names kept), parcel and record ids are masked to their first 2 characters plus `***`, and coordinates are rounded.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `STATEID` | 00*** | 00*** | 00*** | 00*** | 00*** |
| `PARCELID` | 00*** | 00*** | 00*** | 00*** | 00*** |
| `TAXROLLYEAR` | 2025 | 2025 | 2025 | 2025 | 2025 |
| `OWNERNME1` | [redacted] | [redacted] | [redacted] | [redacted] | [redacted] |
| `OWNERNME2` |  |  | [redacted] |  |  |
| `PSTLADRESS` | [redacted] | [redacted] | [redacted] | [redacted] | [redacted] |
| `SITEADRESS` | STATE ROAD 13 | GEM CT | 13TH AVE | 13TH AVE | B GEM CT |
| `PREFIX` | STATE ROAD |  |  |  |  |
| `STREETNAME` | 13 | GEM | 13TH | 13TH | GEM |
| `STREETTYPE` |  | COURT | AVENUE | AVENUE | COURT |
| `PLACENAME` | TOWN OF DELL PRAIRIE | TOWN OF DELL PRAIRIE | TOWN OF DELL PRAIRIE | TOWN OF DELL PRAIRIE | TOWN OF DELL PRAIRIE |
| `STATE` | WI | WI | WI | WI | WI |
| `SCHOOLDIST` | WISCONSIN DELLS SCHOOL DISTRICT | WISCONSIN DELLS SCHOOL DISTRICT | WISCONSIN DELLS SCHOOL DISTRICT | WISCONSIN DELLS SCHOOL DISTRICT | WISCONSIN DELLS SCHOOL DISTRICT |
| `SCHOOLDISTNO` | 6678 | 6678 | 6678 | 6678 | 6678 |
| `CNTASSDVALUE` | 94500 | 194400 | 175300 | 167000 | 202400 |
| `LNDVALUE` | 22700 | 39200 | 42200 | 5800 | 48600 |
| `IMPVALUE` | 71800 | 155200 | 133100 | 161200 | 153800 |
| `ESTFMKVALUE` | 110700 | 227700 | 205300 | 195600 | 237100 |
| `NETPRPTA` | 1097.67 | 2316.19 | 2083.22 | 1817.01 | 2413.77 |
| `GRSPRPTA` | 1097.67 | 2316.19 | 2083.22 | 1981.98 | 2413.77 |
| `PROPCLASS` | 1 | 1 | 1 | 1 | 1 |
| `ASSDACRES` | 1.27 | 0.41 | 0.5 | 0.29 | 0.31 |
| `DEEDACRES` | 1.27 | 0.41 | 0.5 | 0.29 | 0.31 |
| `GISACRES` | 1.07 | 0.41 | 0.5 | 0.29 | 0.31 |
| `CONAME` | ADAMS | ADAMS | ADAMS | ADAMS | ADAMS |
| `LOADDATE` | 3/04/2026 | 3/04/2026 | 3/04/2026 | 3/04/2026 | 3/04/2026 |
| `PARCELFIPS` | 001 | 001 | 001 | 001 | 001 |
| `PARCELSRC` | ADAMS | ADAMS | ADAMS | ADAMS | ADAMS |
| `LONGITUDE` | -89.81 | -89.83 | -89.82 | -89.82 | -89.83 |
| `LATITUDE` | 43.71 | 43.71 | 43.71 | 43.71 | 43.71 |
| `SITEADRESS_STAND` | STH 13 | GEM COURT | 13TH AVENUE | 13TH AVENUE | GEM COURT B |
| `Shape__Area` | 8325.3046875 | 3163.0546875 | 3855.09765625 | 2269.2890625 | 2435.01953125 |
| `Shape__Length` | 375.0245305387647 | 232.01973696079494 | 253.21304213326442 | 207.23321394035924 | 241.03292275238843 |

## Refresh

```sh
python3 scripts/fetch_samples.py wi_parcels
python3 scripts/build_data_dictionaries.py
```
