# Rhode Island: RIGIS land use

**Status:** Fetched (last fetch 2026-10-17)  
**Source id:** `ri_rigis`  

## Summary

| | |
|---|---|
| Publisher | Rhode Island Geographic Information System |
| What it is | Statewide land use / land cover polygons. Parcels and zoning are kept by municipalities. |
| Geography | Land use polygons, statewide. |
| Time coverage and update frequency | Periodic (for example 2020 edition). |
| Units | Land use code, acres. |
| Access method | https://www.rigis.org (ArcGIS Hub). |
| License | See RIGIS terms. |
| Use in our model | Land use context for Rhode Island. |
| Caveats | No statewide parcels or zoning. |

## Access details

- Endpoint used for the sample: `https://services2.arcgis.com/S8zZg9pg23JUEexQ/arcgis/rest/services/PLAN_Land_Use_2025_spf/FeatureServer/0`
- Layer: PLAN_Land_Use_2025_spf
- Total records at fetch time: 26361
- Last edited: 2024-11-14
- Item: Land Use (2025) (owner `URIEDC_RIGIS`, id `101c1a4ffb024b4da2b5ab1c9b6bd6d6`)
- Geometry: esriGeometryPolygon

## Fields (5)

| Field | Type | Meaning |
|---|---|---|
| `OBJECTID` | OID |  |
| `Map_Legend` | String | Land use / land cover class name. |
| `Acres` | Double | Polygon area, acres. |
| `Shape__Area` | Double |  |
| `Shape__Length` | Double |  |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Sample rows

First 3 of 5 rows in [`data/sample/ri_rigis.csv`](../../data/sample/ri_rigis.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 |
|---|---|---|---|
| `OBJECTID` | 1 | 2 | 3 |
| `Map_Legend` | Conservation/Limited | Conservation/Limited | Conservation/Limited |
| `Acres` | 1.54932442 | 2.20739928 | 0.71056649 |
| `Shape__Area` | 67488.5750837326 | 96154.31768035889 | 30952.278121471405 |
| `Shape__Length` | 2894.4848075237774 | 4157.803908219824 | 893.1685988049755 |

## Refresh

```sh
python3 scripts/fetch_samples.py ri_rigis
python3 scripts/build_data_dictionaries.py
```
