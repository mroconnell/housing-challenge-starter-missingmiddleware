# Microsoft Global ML Building Footprints

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `ms_buildings`  
**Handbook listing:** Microsoft's Building Footprints

## Summary

| | |
|---|---|
| Publisher | Microsoft (Bing Maps) |
| What it is | Building outlines detected from aerial and satellite imagery with machine learning. |
| Geography | Global, including all U.S. states. Files are split by zoom-9 quadkey tiles. |
| Time coverage and update frequency | Imagery from about 2014-2024. Updated irregularly. |
| Units | Polygons in WGS84 (EPSG:4326). Height in meters where estimated (-1 = no estimate). Confidence 0-1. |
| Access method | Index CSV at `https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv` lists one gzipped GeoJSON-lines file per tile. Older U.S.-only state files: https://github.com/microsoft/USBuildingFootprints. |
| License | Open Data Commons Open Database License (ODbL). |
| Use in our model | Count existing buildings per parcel, building coverage and open lot area. Key for ADU potential (room in the back yard) and missing-middle lot screening. |
| Caveats | ODbL is share-alike for derived databases. No building use or unit count. Misses some small sheds and garages; can merge attached buildings. |

## Access details

- Endpoint used for the sample: `https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv`
- Sample tile: quadkey 023100000 (UnitedStates), `https://minedbuildings.z5.web.core.windows.net/global-buildings/2026-02-03/global-buildings.geojsonl/RegionName=UnitedStates/quadkey=023100000/part-00051-4feead82-d499-422b-94cb-c036c212127a.c000.csv.gz`
- Each tile is a gzipped GeoJSON-lines file keyed by a zoom-9 quadkey.

## Fields (4)

| Field | Type | Meaning |
|---|---|---|
| `height` |  | Estimated building height in meters. -1 = not estimated. |
| `confidence` |  | Model confidence 0-1. -1 = not available. |
| `geometry_type` |  | Polygon. |
| `geometry` |  | Outline coordinates (cut short in the sample). |

## Geometry sample

[`data/sample/geo/ms_buildings.geojson`](../../data/sample/geo/ms_buildings.geojson) has 3 complete features (geometry and all attributes, owner fields redacted). Coordinates are converted to WGS84 longitude/latitude for GeoJSON. Open it in QGIS or geojson.io.

| | |
|---|---|
| Geometry type | Polygon |
| Source coordinate system | EPSG:4326 |
| Vertices per feature in the sample | 7, 7, 5 |

## Sample rows

First 3 of 5 rows in [`data/sample/ms_buildings.csv`](../../data/sample/ms_buildings.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `height` | 4.720228672027588 | 0.3306068480014801 | 5.420207977294922 | 4.937102794647217 | 5.9013519287109375 |
| `confidence` | 0.9975000023841858 | 0.9735999703407288 | 0.9593999981880188 | 0.9991999864578247 | 0.9775000214576721 |
| `geometry_type` | Polygon | Polygon | Polygon | Polygon | Polygon |
| `geometry` | [[[-111.79850590983126, 40.681111201952895], [-111.79855351… | [[[-111.79936773668163, 40.58328396658282], [-111.799358372… | [[[-111.79983328725602, 40.66440028302329], [-111.799714365… | [[[-111.80020886398563, 40.66561419893265], [-111.800072628… | [[[-111.80026781656855, 40.45033269606244], [-111.800100299… |

## Refresh

```sh
python3 scripts/fetch_samples.py ms_buildings
python3 scripts/build_data_dictionaries.py
```
