# Madison, WI: address points

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `madison_address_points`  
**Handbook listing:** Not in the handbook. Used to place Madison permits on parcels.

## Summary

| | |
|---|---|
| Publisher | City of Madison |
| What it is | One point per official address, with the parcel number it sits on. |
| Geography | Address point. |
| Time coverage and update frequency | Current snapshot. |
| Units | One row per address. |
| Access method | ArcGIS MapServer: https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA/MapServer/20. |
| License | City of Madison open data terms. |
| Use in our model | Match permit street addresses to parcels (missing_middleware/permits/match.py). |
| Caveats | Unit suffixes in permit addresses are free text, so some permits will not match. |

## Access details

- Endpoint used for the sample: `https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA/MapServer/20`
- Layer: Address Points
- Total records at fetch time: 157222
- Geometry: esriGeometryPoint

## Fields (15)

| Field | Type | Meaning |
|---|---|---|
| `OBJECTID` | OID |  |
| `HouseNbr` | Integer | House Number |
| `StreetDir` | String | Street Direction |
| `StreetName` | String | Street Name |
| `StreetType` | String | Street Type |
| `Unit` | String |  |
| `Address` | String | Full street address. |
| `ZipCode` | Integer | ZIP code. |
| `MailCode` | String |  |
| `XCoord` | Double |  |
| `YCoord` | Double |  |
| `Parcel` | String | Parcel number the address belongs to. |
| `DateAdded` | Date |  |
| `DateChanged` | Date |  |
| `SHAPE` | Geometry |  |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Geometry sample

[`data/sample/geo/madison_address_points.geojson`](../../data/sample/geo/madison_address_points.geojson) has 3 complete features (geometry and all attributes, owner fields redacted). Coordinates are converted to WGS84 longitude/latitude for GeoJSON. Open it in QGIS or geojson.io.

| | |
|---|---|
| Geometry type | Point |
| Source coordinate system | EPSG:8193 (Esri 103412) |
| Vertices per feature in the sample | 1, 1, 1 |
| Max features per request | 2000 |
| Paging supported | yes |

## Sample rows

First 3 of 5 rows in [`data/sample/madison_address_points.csv`](../../data/sample/madison_address_points.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `StreetName` | Globe | Globe | Globe | Globe | Globe |
| `StreetType` | Dr | Dr | Dr | Dr | Dr |
| `Unit` | 101 | 102 | 104 | 105 | 107 |
| `Address` | Globe Dr Unit 101 | Globe Dr Unit 102 | Globe Dr Unit 104 | Globe Dr Unit 105 | Globe Dr Unit 107 |
| `ZipCode` | 53717 | 53717 | 53717 | 53717 | 53717 |
| `MailCode` | A | A | A | A | A |
| `XCoord` | 785000 | 785000 | 785000 | 785000 | 785000 |
| `YCoord` | 480000 | 480000 | 480000 | 480000 | 480000 |
| `Parcel` | 07082210**** | 07082210**** | 07082210**** | 07082210**** | 07082210**** |
| `DateAdded` | 1532649600000 | 1532649600000 | 1532649600000 | 1532649600000 | 1532649600000 |

## Refresh

```sh
python3 scripts/fetch_samples.py madison_address_points
python3 scripts/build_data_dictionaries.py
```
