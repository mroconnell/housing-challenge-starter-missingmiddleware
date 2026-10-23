# New Hampshire: NH GRANIT parcels

**Status:** Fetched (last fetch 2026-10-23)  
**Source id:** `nh_granit`  

## Summary

| | |
|---|---|
| Publisher | NH GRANIT (University of New Hampshire) |
| What it is | Parcel mosaic assembled from towns. |
| Geography | Parcel, partial statewide coverage. |
| Time coverage and update frequency | Varies by town. |
| Units | Varies. |
| Access method | https://www.nhgeodata.unh.edu (ArcGIS services). |
| License | See GRANIT terms. |
| Use in our model | Parcel inventory for New Hampshire. |
| Caveats | Not every town is included. Few attributes. |

## Access details

- Endpoint used for the sample: `https://nhgeodata.unh.edu/nhgeodata/rest/services/CAD/ParcelMosaic/MapServer/0`
- Layer: Parcel Points
- Total records at fetch time: 617065
- Geometry: esriGeometryPoint

## Fields (19)

| Field | Type | Meaning |
|---|---|---|
| `OBJECTID` | OID |  |
| `Shape` | Geometry |  |
| `ParcelOID` | Integer |  |
| `NH_GIS_ID` | String | Statewide parcel id (town id + local parcel id). |
| `OID_1` | String | OID |
| `PID` | String | Local parcel id. |
| `TownID` | String | NH town code. |
| `Town` | String | Town name. |
| `Name` | String |  |
| `U_ID` | String |  |
| `DisplayId` | String |  |
| `CountyId` | String | County code. |
| `SLU` | String | State land use code (for example 11 = single family residential, 22 = vacant). Our reading; confirm in publisher docs. |
| `SLUC` | String | State land use code, cleaned. Our reading; confirm in publisher docs. |
| `SLUM` | String | State land use code, modifier. Our reading; confirm in publisher docs. |
| `NBC` | Integer | Number of buildings on the parcel (assessor). Our reading; confirm in publisher docs. |
| `LocalNBC` | String | Local land use / neighborhood code. Our reading; confirm in publisher docs. |
| `StreetAddress` | String | Site address. |
| `ORIG_FID` | Integer |  |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Geometry sample

[`data/sample/geo/nh_granit.geojson`](../../data/sample/geo/nh_granit.geojson) has 3 complete features (geometry and all attributes, owner fields redacted). Coordinates are converted to WGS84 longitude/latitude for GeoJSON. Open it in QGIS or geojson.io.

| | |
|---|---|
| Geometry type | Point |
| Source coordinate system | EPSG:3437 (Esri 102710) |
| Vertices per feature in the sample | 1, 1, 1 |
| Max features per request | 2000 |
| Paging supported | yes |

## Sample rows

First 3 of 5 rows in [`data/sample/nh_granit.csv`](../../data/sample/nh_granit.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `OBJECTID` | 1 | 2 | 3 | 4 | 5 |
| `ParcelOID` | 173431 | 173432 | 173433 | 173434 | 173435 |
| `NH_GIS_ID` | 104001-252-010-000 | 104001-252-006-000 | 104001-229-066-000 | 104001-227-016-000 | 104001-228-011-000 |
| `PID` | 252-010-000 | 252-006-000 | 229-066-000 | 227-016-000 | 228-011-000 |
| `TownID` | 4001 | 4001 | 4001 | 4001 | 4001 |
| `Town` | Acworth | Acworth | Acworth | Acworth | Acworth |
| `Name` | CamaID: 252-010-000 | CamaID: 252-006-000 | CamaID: 229-066-000 | CamaID: 227-016-000 | CamaID: 228-011-000 |
| `U_ID` | 4001-550 | 4001-594 | 4001-15 | 4001-424 | 4001-449 |
| `DisplayId` | 252-010-000 | 252-006-000 | 229-066-000 | 227-016-000 | 228-011-000 |
| `CountyId` | 10 | 10 | 10 | 10 | 10 |
| `SLU` | 22 | 22 | 11 | 11 | 11 |
| `SLUC` | 22 | 22 | 11 | 11 | 11 |
| `NBC` | 0 | 0 | 2 | 2 | 2 |
| `LocalNBC` | 40 | 50 | 100 | 100 | 100 |
| `StreetAddress` | RHOADES RD | MULLIGAN RD | 30 CHARLESTOWN RD | 422 RIVER RD | 81 JOHN SYMONDS RD |
| `ORIG_FID` | 65017 | 65018 | 65019 | 65020 | 65021 |

## Refresh

```sh
python3 scripts/fetch_samples.py nh_granit
python3 scripts/build_data_dictionaries.py
```
