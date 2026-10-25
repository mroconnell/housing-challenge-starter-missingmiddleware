# Wisconsin V12 statewide parcels

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `wi_v12_parcels`  
**Handbook listing:** Not in the handbook. Parcel base for the Pleasant Prairie and Sun Prairie pipelines.

## Summary

| | |
|---|---|
| Publisher | Wisconsin DOA / State Cartographer's Office (Statewide Parcel Initiative) |
| What it is | Every parcel in Wisconsin with parcel ids, site address, assessed values, property class, acres and a point location. |
| Geography | Parcel polygons; LATITUDE and LONGITUDE give a point. |
| Time coverage and update frequency | V12 (2026 release, tax roll 2025). A current snapshot only. |
| Units | One row per parcel. |
| Access method | ArcGIS FeatureServer https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/Wisconsin_Statewide_Parcels_DB/FeatureServer/0 |
| License | Public (Wis. Stat. 59.72). |
| Use in our model | Matches permit parcel numbers to locations, then to tracts and block groups. |
| Caveats | No year built and no dwelling count. Owner name and mailing fields exist on the layer; the pipeline never requests them, and the sample redacts them. |

## Access details

- Endpoint used for the sample: `https://services3.arcgis.com/n6uYoouQZW75n5WI/arcgis/rest/services/Wisconsin_Statewide_Parcels_DB/FeatureServer/0`
- Layer: V1200_WisconsinParcels_2026
- Total records at fetch time: 9835
- Last edited: 2026-06-30
- Geometry: esriGeometryPolygon
- Sample rows are from Pleasant Prairie. The pipeline also pulls Sun Prairie (CITY OF SUN PRAIRIE, DANE) and requests only non-owner fields.

## Fields (47)

| Field | Type | Meaning |
|---|---|---|
| `OBJECTID` | OID |  |
| `STATEID` | String | State ID |
| `PARCELID` | String | Local parcel id; the permit parcel numbers match this. |
| `TAXPARCELID` | String | Tax Parcel ID |
| `PARCELDATE` | String | Parcel Date |
| `TAXROLLYEAR` | String | Tax Roll Year |
| `OWNERNME1` | String | Primary Owner Name |
| `OWNERNME2` | String | Secondary Owner Name |
| `PSTLADRESS` | String | Full Mailing Address |
| `SITEADRESS` | String | Site address. |
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
| `PLACENAME` | String | Municipality, for example VILLAGE OF PLEASANT PRAIRIE. |
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
| `PROPCLASS` | String | Property class (1 residential, 2 commercial, and so on). |
| `AUXCLASS` | String | Auxiliary Class of Property |
| `ASSDACRES` | Double | Assessed Acres |
| `DEEDACRES` | Double | Deeded Acres |
| `GISACRES` | Double | GIS Acres |
| `CONAME` | String | County name. |
| `LOADDATE` | String | Load Date |
| `PARCELFIPS` | String | Parcel Source FIPS |
| `PARCELSRC` | String | Parcel Source |
| `LONGITUDE` | Double | Parcel point longitude. |
| `LATITUDE` | Double | Parcel point latitude. |
| `SITEADRESS_STAND` | String |  |
| `Shape__Area` | Double |  |
| `Shape__Length` | Double |  |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Geometry sample

[`data/sample/geo/wi_v12_parcels.geojson`](../../data/sample/geo/wi_v12_parcels.geojson) has 3 features. For privacy each parcel or unit outline is replaced by its bounding box on a 0.01-degree grid (about 1 km across), so the file shows the layer's attributes and rough location but cannot locate a property. Attributes are masked the same way as the CSV. Coordinates are WGS84 longitude/latitude.

| | |
|---|---|
| Geometry type | Polygon |
| Source coordinate system | EPSG:3857 (Esri 102100) |
| Vertices per feature in the source | 8, 10, 40 |
| Max features per request | 2000 |
| Paging supported | yes |

## Sample rows

First 3 of 5 rows in [`data/sample/wi_v12_parcels.csv`](../../data/sample/wi_v12_parcels.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`. House and unit numbers are removed (street names kept), parcel and record ids are masked to their first 2 characters plus `***`, and coordinates are rounded.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `STATEID` | 05*** | 05*** | 05*** | 05*** | 05*** |
| `PARCELID` | 91*** | 91*** | 91*** | 91*** | 91*** |
| `TAXROLLYEAR` | 2025 | 2025 | 2025 | 2025 | 2025 |
| `OWNERNME1` | [redacted] | [redacted] | [redacted] | [redacted] | [redacted] |
| `PSTLADRESS` | [redacted] |  |  |  |  |
| `SITEADRESS` | 122ND AVE | GREEN BAY RD |  |  |  |
| `STREETNAME` | 122ND | GREEN BAY |  |  |  |
| `STREETTYPE` | AVENUE | ROAD |  |  |  |
| `PLACENAME` | VILLAGE OF PLEASANT PRAIRIE | VILLAGE OF PLEASANT PRAIRIE | VILLAGE OF PLEASANT PRAIRIE | VILLAGE OF PLEASANT PRAIRIE | VILLAGE OF PLEASANT PRAIRIE |
| `ZIPCODE` | 53142 | 53142 | 53104 | 53158 | 53158 |
| `STATE` | WI | WI | WI | WI | WI |
| `SCHOOLDIST` | BRISTOL #1 SCHOOL DISTRICT | KENOSHA SCHOOL DISTRICT | BRISTOL #1 SCHOOL DISTRICT | BRISTOL #1 SCHOOL DISTRICT | BRISTOL #1 SCHOOL DISTRICT |
| `SCHOOLDISTNO` | 0665 | 2793 | 0665 | 0665 | 0665 |
| `CNTASSDVALUE` | 185554000 | 119900 |  | 100 |  |
| `LNDVALUE` | 23086000 | 119900 |  | 100 |  |
| `IMPVALUE` | 162468000 | 0 |  | 0 |  |
| `ESTFMKVALUE` | 199735200 | 129100 |  |  |  |
| `NETPRPTA` | 2782793.35 | 1560.89 |  | 1.5 |  |
| `PROPCLASS` | 3 | 3 |  | 5 |  |
| `AUXCLASS` |  |  | X4 |  | X4 |
| `ASSDACRES` | 136.6 | 0.96 | 28.32 | 12.62 | 1.92 |
| `DEEDACRES` | 136.6 | 0.9 | 28.32 | 12.62 | 1.92 |
| `CONAME` | KENOSHA | KENOSHA | KENOSHA | KENOSHA | KENOSHA |
| `LOADDATE` | 3/09/2026 | 3/09/2026 | 3/09/2026 | 3/09/2026 | 3/09/2026 |
| `PARCELFIPS` | 059 | 059 | 059 | 059 | 059 |
| `PARCELSRC` | KENOSHA | KENOSHA | KENOSHA | KENOSHA | KENOSHA |
| `LONGITUDE` | -87.96 | -87.89 | -87.95 | -87.95 | -87.96 |
| `LATITUDE` | 42.54 | 42.56 | 42.54 | 42.54 | 42.54 |
| `SITEADRESS_STAND` | 122ND AVENUE | GREEN BAY ROAD |  |  |  |
| `Shape__Area` | 1018143.6537942886 | 6763.89453125 | 211317.9680314064 | 94555.89757657051 | 14320.92578125 |
| `Shape__Length` | 4568.739429540138 | 482.5380124596213 | 2339.067187978497 | 2165.2002223168697 | 482.08234110459017 |

## Refresh

```sh
python3 scripts/fetch_samples.py wi_v12_parcels
python3 scripts/build_data_dictionaries.py
```
