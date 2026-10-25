# Microsoft Global ML Building Footprints

**Status:** Sample not kept (owner decision D5) (last fetch 2026-10-25)  
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

- Sample not kept (owner decision D5): footprints locate individual buildings and the ODbL is share-alike. The model does not use this source.

## Fields (4)

| Field | Type | Meaning |
|---|---|---|
| `height` |  | Estimated building height in meters. -1 = not estimated. |
| `confidence` |  | Model confidence 0-1. -1 = not available. |
| `geometry_type` |  | Polygon. |
| `geometry` |  | Outline coordinates (cut short in the sample). |

## Sample rows

None. See the status above. What we did find is in [`data/sample/ms_buildings.meta.json`](../../data/sample/ms_buildings.meta.json).


## Refresh

```sh
python3 scripts/fetch_samples.py ms_buildings
python3 scripts/build_data_dictionaries.py
```
