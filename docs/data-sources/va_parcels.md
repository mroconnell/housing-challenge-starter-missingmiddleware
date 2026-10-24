# Virginia: VGIN statewide parcels

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `va_parcels`  

## Summary

| | |
|---|---|
| Publisher | Virginia Geographic Information Network (VGIN) |
| What it is | Parcel boundaries collected from localities into one statewide layer. |
| Geography | Parcel, most localities. |
| Time coverage and update frequency | Updated yearly. |
| Units | Varies. |
| Access method | https://vgin.vdem.virginia.gov/pages/cl-data-download and the VGIN ArcGIS REST services. |
| License | See VGIN terms. |
| Use in our model | Parcel inventory for Virginia. Zoning and land use downloads are on the same page by locality. |
| Caveats | Few attributes. Not every locality is included. |

## Access details

- Endpoint used for the sample: `https://vginmaps.vdem.virginia.gov/arcgis/rest/services/VA_Base_Layers/VA_Parcels/FeatureServer/0`
- Layer: Virginia Parcels
- Total records at fetch time: 4174364
- Geometry: esriGeometryPolygon

## Fields (9)

| Field | Type | Meaning |
|---|---|---|
| `Shape__Area` | Double | SHAPE.STArea() |
| `Shape__Length` | Double | SHAPE.STLength() |
| `OBJECTID` | OID |  |
| `VGIN_QPID` | Double | VGIN statewide unique parcel id. |
| `FIPS` | String | 5-digit county/city FIPS code. |
| `LOCALITY` | String | County or independent city. |
| `PARCELID` | String | Local parcel id. |
| `PTM_ID` | String | Local parcel tax map id. |
| `LASTUPDATE` | Date | Date VGIN last updated the record (epoch milliseconds). |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Geometry sample

[`data/sample/geo/va_parcels.geojson`](../../data/sample/geo/va_parcels.geojson) has 3 complete features (geometry and all attributes, owner fields redacted). Coordinates are converted to WGS84 longitude/latitude for GeoJSON. Open it in QGIS or geojson.io.

| | |
|---|---|
| Geometry type | Polygon |
| Source coordinate system | EPSG:3857 (Esri 102100) |
| Vertices per feature in the sample | 16, 14, 21 |
| Max features per request | 2000 |
| Paging supported | yes |

## Sample rows

First 3 of 5 rows in [`data/sample/va_parcels.csv`](../../data/sample/va_parcels.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `Shape__Area` | 68479.26863561 | 108092.42892208 | 22161.91687417 | 87340.612971475 | 25426.091694405 |
| `Shape__Length` | 1036.4584052498724 | 2597.0133857630963 | 625.0360800082909 | 1333.0479941205813 | 1423.051278747487 |
| `OBJECTID` | 1 | 2 | 3 | 4 | 5 |
| `VGIN_QPID` | 5110100000001.0 | 5110100000002.0 | 5110100000003.0 | 5110100000004.0 | 5110100000005.0 |
| `FIPS` | 51101 | 51101 | 51101 | 51101 | 51101 |
| `LOCALITY` | King William County | King William County | King William County | King William County | King William County |
| `PARCELID` | 10-12 | 13-34 | 26-34H | 13-38A | 25-36B |
| `PTM_ID` | 10-12 | 13-32 | 26-34H | 13-38A | 25-36B |
| `LASTUPDATE` | 1773705600000 | 1773705600000 | 1773705600000 | 1773705600000 | 1773705600000 |

## Refresh

```sh
python3 scripts/fetch_samples.py va_parcels
python3 scripts/build_data_dictionaries.py
```
