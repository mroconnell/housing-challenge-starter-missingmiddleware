# Arizona: AZGeo Data Hub (parcels by county)

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `az_azgeo`  

## Summary

| | |
|---|---|
| Publisher | Arizona Geographic Information Council / county assessors |
| What it is | Statewide data hub. Parcels, zoning and land use are published county by county. |
| Geography | Parcel, county by county. |
| Time coverage and update frequency | Varies by county. |
| Units | Varies by county. |
| Access method | https://azgeo-data-hub-agic.hub.arcgis.com/ (ArcGIS Hub search, then each layer's REST query endpoint). |
| License | Varies by publisher. |
| Use in our model | Parcel inventory for Arizona. |
| Caveats | No single statewide parcel layer. Each county has its own schema. |

## Access details

- Endpoint used for the sample: `https://maps.scottsdaleaz.gov/arcgis/rest/services/OpenData/MapServer/3`
- Layer: Parcels
- Total records at fetch time: 142108
- Item: Parcels (owner `City_Of_Scottsdale`, id `fcd4ef3733ce4cad8b91b90beb163cf3`)
- Geometry: esriGeometryPolygon

## Fields (5)

| Field | Type | Meaning |
|---|---|---|
| `OBJECTID` | OID |  |
| `apn` | String | Assessor parcel number (Maricopa County format BBB-MM-PPP). |
| `site_address` | String | Street address of the parcel. |
| `jurisdiction` | String | City or town the parcel is in. |
| `Shape` | Geometry |  |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Geometry sample

[`data/sample/geo/az_azgeo.geojson`](../../data/sample/geo/az_azgeo.geojson) has 3 features. For privacy each parcel or unit outline is replaced by its bounding box on a 0.01-degree grid (about 1 km across), so the file shows the layer's attributes and rough location but cannot locate a property. Attributes are masked the same way as the CSV. Coordinates are WGS84 longitude/latitude.

| | |
|---|---|
| Geometry type | Polygon |
| Source coordinate system | EPSG:2868 |
| Vertices per feature in the source | 5, 19, 5 |
| Max features per request | 30000 |
| Paging supported | yes |

## Sample rows

First 3 of 5 rows in [`data/sample/az_azgeo.csv`](../../data/sample/az_azgeo.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`. House and unit numbers are removed (street names kept), parcel and record ids are masked to their first 2 characters plus `***`, and coordinates are rounded.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `apn` | 21*** | 21*** | 17*** | 17*** | 21*** |
| `site_address` | E CHRISTMAS CHOLLA DR | N 120TH PL | N 81ST ST | N 65TH ST | E BELLA VISTA |
| `jurisdiction` | SCOTTSDALE | SCOTTSDALE | SCOTTSDALE | PHOENIX | SCOTTSDALE |

## Refresh

```sh
python3 scripts/fetch_samples.py az_azgeo
python3 scripts/build_data_dictionaries.py
```
