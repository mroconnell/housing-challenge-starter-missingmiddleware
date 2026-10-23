# Google Open Buildings

**Status:** Fetched (last fetch 2026-10-23)  
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

- Endpoint used for the sample: `https://storage.googleapis.com/open-buildings-data/v3/polygons_s2_level_4_gzip/0e9_buildings.csv.gz`
- v3 polygons. Coverage is Africa, South and Southeast Asia, Latin America and the Caribbean. No United States coverage.

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

First 3 of 5 rows in [`data/sample/google_open_buildings.csv`](../../data/sample/google_open_buildings.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `latitude` | 18.54958867 | 16.02719816 | 17.97890384 | 17.17634556 | 16.22644099 |
| `longitude` | -11.44114405 | -16.50595286 | -15.96423028 | -15.05338038 | -15.74140055 |
| `area_in_meters` | 205.8534 | 23.8248 | 16.5278 | 87.7801 | 11.2692 |
| `confidence` | 0.9049 | 0.6537 | 0.7404 | 0.8793 | 0.6884 |
| `geometry` | POLYGON((-11.4410475000159 18.5495997567978, -11.4411774288… | POLYGON((-16.5059260700478 16.027178327372, -16.50592312963… | POLYGON((-15.9642120059132 17.9788830173195, -15.9642180818… | POLYGON((-15.0533699157599 17.1762766399214, -15.0533346774… | POLYGON((-15.741385054301 16.2264252521455, -15.74138837586… |
| `full_plus_code` | 7CCCGHX5+RGQF | 7C852FGV+VJFW | 7C96X2HP+H864 | 7C965WGW+GJQX | 7C8667G5+HCHJ |

## Refresh

```sh
python3 scripts/fetch_samples.py google_open_buildings
python3 scripts/build_data_dictionaries.py
```
