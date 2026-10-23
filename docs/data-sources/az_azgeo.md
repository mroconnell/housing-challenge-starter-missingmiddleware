# Arizona: AZGeo Data Hub (parcels by county)

**Status:** Fetched (last fetch 2026-10-23)  
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

## Sample rows

First 3 of 5 rows in [`data/sample/az_azgeo.csv`](../../data/sample/az_azgeo.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 |
|---|---|---|---|
| `OBJECTID` | 54129566 | 54129567 | 54129568 |
| `apn` | 212-06-095 | 217-01-079 | 173-02-320 |
| `site_address` | 7480 E CHRISTMAS CHOLLA DR | 24218 N 120TH PL | 5835 N 81ST ST |
| `jurisdiction` | SCOTTSDALE | SCOTTSDALE | SCOTTSDALE |

## Refresh

```sh
python3 scripts/fetch_samples.py az_azgeo
python3 scripts/build_data_dictionaries.py
```
