# USGS National Land Cover Database (NLCD / Annual NLCD)

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `nlcd`  
**Handbook listing:** USGS National Land Cover Database (NLCD)

## Summary

| | |
|---|---|
| Publisher | U.S. Geological Survey with the MRLC consortium |
| What it is | 30-meter land cover raster with 16 classes, including four developed intensity classes and impervious surface. |
| Geography | Contiguous U.S. (Alaska, Hawaii and Puerto Rico have separate older products). 30 m pixels. |
| Time coverage and update frequency | Annual NLCD covers 1985 onward, one map per year. Updated roughly yearly. |
| Units | Class code per pixel (integer). Impervious products are percent of pixel. |
| Access method | Bulk GeoTIFF/COG downloads from https://www.mrlc.gov/data and USGS EarthExplorer. Point lookups through the MRLC GeoServer WMS (GetFeatureInfo), as our script does. |
| License | Public domain (U.S. federal government work). |
| Use in our model | Find developed vs. undeveloped land near transit or in zoned areas. Developed-low-intensity (class 22) is a rough proxy for single-family areas where ADUs and missing-middle infill would happen. |
| Caveats | Raster, so it has no parcel or zoning boundaries. 30 m pixels blur small lots. Hawaii is not in the CONUS product. |

## Access details

- Endpoint used for the sample: `https://www.mrlc.gov/geoserver/mrlc_display/wms`
- Layer: NLCD_2021_Land_Cover_Science_Product_L48
- Raster data. Sample rows are pixel values at 5 points via WMS GetFeatureInfo.

## Fields (5)

| Field | Type | Meaning |
|---|---|---|
| `point` |  | Name of the sample point (added by our script). |
| `lat` |  | Latitude of the sample point. |
| `lon` |  | Longitude of the sample point. |
| `layer` |  | WMS layer queried. |
| `PALETTE_INDEX` |  | Same class code, palette form. |

## Sample rows

First 3 of 5 rows in [`data/sample/nlcd.csv`](../../data/sample/nlcd.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `point` | Salt Lake City UT | Hartford CT | Madison WI | Providence RI | Rural Lancaster Co PA |
| `lat` | 40.7608 | 41.7658 | 43.0731 | 41.824 | 40.0 |
| `lon` | -111.891 | -72.6734 | -89.4012 | -71.4128 | -76.2 |
| `layer` | NLCD_2021_Land_Cover_Science_Product_L48 | NLCD_2021_Land_Cover_Science_Product_L48 | NLCD_2021_Land_Cover_Science_Product_L48 | NLCD_2021_Land_Cover_Science_Product_L48 | NLCD_2021_Land_Cover_Science_Product_L48 |
| `PALETTE_INDEX` | 24 | 24 | 24 | 24 | 82 |

## Refresh

```sh
python3 scripts/fetch_samples.py nlcd
python3 scripts/build_data_dictionaries.py
```
