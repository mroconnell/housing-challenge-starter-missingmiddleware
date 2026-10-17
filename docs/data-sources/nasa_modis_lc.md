# NASA MODIS Land Cover Type (MCD12Q1)

**Status:** Fetched (last fetch 2026-10-17)  
**Source id:** `nasa_modis_lc`  
**Handbook listing:** NASA Land Use/Land Cover database

## Summary

| | |
|---|---|
| Publisher | NASA LP DAAC (served for point queries by ORNL DAAC) |
| What it is | Yearly global land cover at 500 m from the MODIS satellites, in several classification schemes. |
| Geography | Global, 500 m pixels. |
| Time coverage and update frequency | Yearly, 2001 to about two years ago. |
| Units | Class code per pixel. LC_Type1 uses the IGBP scheme, where 13 = urban and built-up. |
| Access method | Point and small-area subsets: ORNL DAAC MODIS web service, `https://modis.ornl.gov/rst/api/v1/MCD12Q1/subset` (no login). Full tiles: NASA Earthdata / LP DAAC (free Earthdata login). |
| License | NASA open data, no restrictions on use. |
| Use in our model | Coarse cross-check of urban extent, and the only land cover option for places NLCD does not cover. Too coarse for parcel-level work. |
| Caveats | 500 m pixels are much coarser than NLCD. Prefer NLCD for U.S. states. The handbook's 'NASA Land Use/Land Cover database' does not name a product; we chose MCD12Q1 as the standard NASA land cover product. |

## Access details

- Endpoint used for the sample: `https://modis.ornl.gov/rst/api/v1/MCD12Q1/subset`
- Latest date: A2024001
- MODIS MCD12Q1 v061 yearly land cover, 500 m. Point subsets via ORNL DAAC web service (no login). Bulk tiles need a NASA Earthdata login.

## Fields (9)

| Field | Type | Meaning |
|---|---|---|
| `point` |  | Name of the sample point (added by our script). |
| `latitude` |  | Latitude. |
| `longitude` |  | Longitude. |
| `band` |  | Product band. LC_Type1 = IGBP classification. |
| `modis_date` |  | MODIS date code, AYYYYDDD. |
| `calendar_date` |  | Start date of the year the map represents. |
| `tile` |  | MODIS sinusoidal tile id (hXXvYY). |
| `value` |  | Land cover class. IGBP: 13 urban, 12 cropland, 10 grassland, 1-5 forest, 17 water. |
| `cellsize_m` |  | Pixel size in meters. |

## Sample rows

First 3 of 3 rows in [`data/sample/nasa_modis_lc.csv`](../../data/sample/nasa_modis_lc.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 |
|---|---|---|---|
| `point` | Salt Lake City UT | Madison WI | Hartford CT |
| `latitude` | 40.7608 | 43.0731 | 41.7658 |
| `longitude` | -111.891 | -89.4012 | -72.6734 |
| `band` | LC_Type1 | LC_Type1 | LC_Type1 |
| `modis_date` | A2024001 | A2024001 | A2024001 |
| `calendar_date` | 2024-01-01 | 2024-01-01 | 2024-01-01 |
| `tile` | h09v04 | h11v04 | h12v04 |
| `value` | 13 | 13 | 13 |
| `cellsize_m` | 463.312716528 | 463.312716528 | 463.312716528 |

## Refresh

```sh
python3 scripts/fetch_samples.py nasa_modis_lc
python3 scripts/build_data_dictionaries.py
```
