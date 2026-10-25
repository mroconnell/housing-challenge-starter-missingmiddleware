# Google Open Buildings

**Status:** Sample not kept (owner decision D5) (last fetch 2026-10-25)  
**Source id:** `google_open_buildings`  
**Handbook listing:** Google's Open Buildings

## Summary

| | |
|---|---|
| Publisher | Google Research |
| What it is | Building outlines detected from satellite imagery, with confidence scores. |
| Geography | Africa, South and Southeast Asia, Latin America and the Caribbean. No coverage of the United States. |
| Time coverage and update frequency | v3, imagery to 2022. A 2.5D temporal dataset covers 2016-2023 for the same regions. |
| Units | Area in square meters, confidence 0-1, polygons in WKT (WGS84). |
| Access method | Public CSV tiles on Google Cloud Storage, `https://storage.googleapis.com/open-buildings-data/v3/polygons_s2_level_4_gzip/{tile}_buildings.csv.gz`. Also in Google Earth Engine. |
| License | CC BY 4.0 and ODbL v1.0 (user's choice). |
| Use in our model | None for U.S. states. Use Microsoft footprints instead. |
| Caveats | Listed in the handbook but it does not cover any U.S. state. Kept here so the team does not spend time on it. |

## Access details

- Sample not kept (owner decision D5): no U.S. coverage, and footprints locate individual buildings.

## Fields (6)

| Field | Type | Meaning |
|---|---|---|
| `latitude` |  | Latitude of building centroid. |
| `longitude` |  | Longitude of building centroid. |
| `area_in_meters` |  | Footprint area, square meters. |
| `confidence` |  | Model confidence 0.65-1. |
| `geometry` |  | Outline as WKT (cut short in the sample). |
| `full_plus_code` |  | Open Location Code of the centroid. |

## Sample rows

None. See the status above. What we did find is in [`data/sample/google_open_buildings.meta.json`](../../data/sample/google_open_buildings.meta.json).


## Refresh

```sh
python3 scripts/fetch_samples.py google_open_buildings
python3 scripts/build_data_dictionaries.py
```
