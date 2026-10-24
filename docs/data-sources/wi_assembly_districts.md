# Wisconsin State Assembly districts (2024 plan)

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `wi_assembly_districts`  
**Handbook listing:** Not in the handbook. For reporting results by legislative district.

## Summary

| | |
|---|---|
| Publisher | Wisconsin Legislative Technology Services Bureau (LTSB) |
| What it is | The 99 Assembly district boundaries from 2023 Wisconsin Act 94 (February 2024). A Senate layer (33 districts) is published alongside. |
| Geography | State Assembly district. |
| Time coverage and update frequency | 2024 plan, in effect from the 2024 elections. |
| Units | One polygon per district. |
| Access method | ArcGIS FeatureServer: https://services1.arcgis.com/FDsAtKBk8Hy4cAH0/arcgis/rest/services/WI_Assembly_Districts_2024/FeatureServer/0 (Senate: WI_Senate_Districts_2024). |
| License | "Open and publicly available... use at your own risk" (LTSB). |
| Use in our model | Explain bill and package results locally, by district. |
| Caveats | Census geographies cross district lines, so district totals need an allocation method. Reconcile statewide totals for each chamber. |

## Access details

- Endpoint used for the sample: `https://services1.arcgis.com/FDsAtKBk8Hy4cAH0/arcgis/rest/services/WI_Assembly_Districts_2024/FeatureServer/0`
- Layer: WI_Assembly_Districts_2024
- Total records at fetch time: 99
- Last edited: 2025-09-09
- Geometry: esriGeometryPolygon

## Fields (5)

| Field | Type | Meaning |
|---|---|---|
| `FID` | OID |  |
| `ASM2024` | String |  |
| `SEN2024` | String |  |
| `Shape__Area` | Double |  |
| `Shape__Length` | Double |  |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Geometry sample

[`data/sample/geo/wi_assembly_districts.geojson`](../../data/sample/geo/wi_assembly_districts.geojson) has 1 complete features (geometry and all attributes, owner fields redacted). Coordinates are converted to WGS84 longitude/latitude for GeoJSON. Open it in QGIS or geojson.io.

| | |
|---|---|
| Geometry type | Polygon |
| Source coordinate system | EPSG:3857 (Esri 102100) |
| Vertices per feature in the sample | 2254 |
| Simplified for size | yes: kept every 16th of 35614 vertices |
| Max features per request | 2000 |
| Paging supported | yes |

## Sample rows

First 3 of 5 rows in [`data/sample/wi_assembly_districts.csv`](../../data/sample/wi_assembly_districts.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `FID` | 1 | 2 | 3 | 4 | 5 |
| `ASM2024` | 1 | 2 | 3 | 4 | 5 |
| `SEN2024` | 1 | 1 | 1 | 2 | 2 |
| `Shape__Area` | 4753538766.65625 | 2325989760.7773438 | 2326528654.8554688 | 2260116822.1992188 | 1362234740.140625 |
| `Shape__Length` | 807108.0514643062 | 308780.75756498484 | 257764.07632887104 | 355921.23240206536 | 230283.0161571233 |

## Refresh

```sh
python3 scripts/fetch_samples.py wi_assembly_districts
python3 scripts/build_data_dictionaries.py
```
