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

[`data/sample/geo/va_parcels.geojson`](../../data/sample/geo/va_parcels.geojson) has 3 features. For privacy each parcel or unit outline is replaced by its bounding box on a 0.01-degree grid (about 1 km across), so the file shows the layer's attributes and rough location but cannot locate a property. Attributes are masked the same way as the CSV. Coordinates are WGS84 longitude/latitude.

| | |
|---|---|
| Geometry type | Polygon |
| Source coordinate system | EPSG:3857 (Esri 102100) |
| Vertices per feature in the source | 16, 14, 21 |
| Max features per request | 2000 |
| Paging supported | yes |

## Sample rows

First 3 of 5 rows in [`data/sample/va_parcels.csv`](../../data/sample/va_parcels.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`. House and unit numbers are removed (street names kept), parcel and record ids are masked to their first 2 characters plus `***`, and coordinates are rounded.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `Shape__Area` | 68479.26863561 | 108092.42892208 | 22161.91687417 | 87340.612971475 | 25426.091694405 |
| `Shape__Length` | 1036.4584052498724 | 2597.0133857630963 | 625.0360800082909 | 1333.0479941205813 | 1423.051278747487 |
| `VGIN_QPID` | 51*** | 51*** | 51*** | 51*** | 51*** |
| `FIPS` | 51101 | 51101 | 51101 | 51101 | 51101 |
| `LOCALITY` | King William County | King William County | King William County | King William County | King William County |
| `PARCELID` | 10*** | 13*** | 26*** | 13*** | 25*** |
| `PTM_ID` | 10*** | 13*** | 26*** | 13*** | 25*** |
| `LASTUPDATE` | 1773705600000 | 1773705600000 | 1773705600000 | 1773705600000 | 1773705600000 |

## Refresh

```sh
python3 scripts/fetch_samples.py va_parcels
python3 scripts/build_data_dictionaries.py
```
