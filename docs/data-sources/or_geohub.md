# Oregon: GEOHub parcels and zoning

**Status:** Fetched (last fetch 2026-10-17)  
**Source id:** `or_geohub`  

## Summary

| | |
|---|---|
| Publisher | State of Oregon (Geospatial Enterprise Office) |
| What it is | Statewide portal with county parcel layers and a statewide zoning compilation. |
| Geography | Parcel / zoning district, incomplete county coverage. |
| Time coverage and update frequency | Varies. |
| Units | Varies. |
| Access method | https://geohub.oregon.gov (ArcGIS Hub). |
| License | See item pages. |
| Use in our model | Zoning for Oregon outside Portland metro. |
| Caveats | Coverage is incomplete. |

## Access details

- Endpoint used for the sample: `https://services8.arcgis.com/8PAo5HGmvRMlF2eU/arcgis/rest/services/Zoning/FeatureServer/0`
- Layer: ZoneOR_Gov2Pub
- Total records at fetch time: 114823
- Last edited: 2023-07-19
- Item: Zoning (owner `OR_FRAMEWORK`, id `72416393747c4cdf9110920656f90f83`)
- Geometry: esriGeometryPolygon

## Fields (15)

| Field | Type | Meaning |
|---|---|---|
| `OBJECTID` | OID |  |
| `LUnitID` | String |  |
| `SUnitID` | String |  |
| `localZCode` | String | Zoning code as the local government writes it. |
| `localZDesc` | String | Local zoning description. |
| `orZCode` | String | Oregon statewide standardized zoning class code. |
| `orZDesc` | String | Oregon statewide standardized zoning class name (for example Commercial - General). |
| `codeRef` | String |  |
| `effDate` | String | Date the zoning took effect (YYYYMMDD). |
| `unitOwner` | String |  |
| `ownerName` | String | Government that adopted the zoning (not a property owner). |
| `ownerType` | String | County or City. |
| `gsteward` | String | Agency that maintains the data. |
| `Shape__Area` | Double |  |
| `Shape__Length` | Double |  |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Sample rows

First 3 of 5 rows in [`data/sample/or_geohub.csv`](../../data/sample/or_geohub.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 |
|---|---|---|---|
| `OBJECTID` | 1 | 2 | 3 |
| `LUnitID` |  |  |  |
| `SUnitID` | 1135845_CG | 1135845_CG | 1135845_CG |
| `localZCode` |  |  |  |
| `localZDesc` |  |  |  |
| `orZCode` | CG | CG | CG |
| `orZDesc` | Commercial - General | Commercial - General | Commercial - General |
| `codeRef` | GNIS | GNIS | GNIS |
| `effDate` | 20140825 | 20140825 | 20140825 |
| `unitOwner` | 1135845 | 1135845 | 1135845 |
| `ownerName` | Baker County | Baker County | Baker County |
| `ownerType` | County | County | County |
| `gsteward` | Baker County | Baker County | Baker County |
| `Shape__Area` | 537591.75 | 497109.125 | 285557.390625 |
| `Shape__Length` | 3767.3286250713586 | 3003.1079853285105 | 2625.0746361604206 |

## Refresh

```sh
python3 scripts/fetch_samples.py or_geohub
python3 scripts/build_data_dictionaries.py
```
