# Madison, WI: zoning districts

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `madison_zoning`  
**Handbook listing:** Not in the handbook. Zoning for the Madison ADU pilot.

## Summary

| | |
|---|---|
| Publisher | City of Madison, Planning |
| What it is | Zoning district polygons with district code and a link to the district's code text. |
| Geography | Zoning district polygon. |
| Time coverage and update frequency | Current snapshot. |
| Units | One polygon per district area. |
| Access method | ArcGIS MapServer: https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA/MapServer/9. |
| License | City of Madison open data terms. |
| Use in our model | Which parcels sit in districts where ADUs are allowed (for example TR-C and SR-C). |
| Caveats | Zoning layers show districts, not what the code allows. Pair with the ordinance text. |

## Access details

- Endpoint used for the sample: `https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA/MapServer/9`
- Layer: Zoning Districts
- Total records at fetch time: 2473
- Geometry: esriGeometryPolygon

## Fields (10)

| Field | Type | Meaning |
|---|---|---|
| `OBJECTID` | OID |  |
| `ZONING_CODE` | String | District code, for example TR-C1. |
| `ZON_ANNO` | String | Zoning Annotation |
| `PD_ID` | Integer | PD-ID |
| `ZON_PREFIX` | String | Zoning Prefix |
| `Shape` | Geometry |  |
| `Shape.STArea()` | Double |  |
| `Shape.STLength()` | Double |  |
| `Zoning_Document` | String | Link to the district's code text. |
| `Zoning_District` | String | District name. |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Geometry sample

[`data/sample/geo/madison_zoning.geojson`](../../data/sample/geo/madison_zoning.geojson) has 3 complete features (geometry and all attributes, owner fields redacted). Coordinates are converted to WGS84 longitude/latitude for GeoJSON. Open it in QGIS or geojson.io.

| | |
|---|---|
| Geometry type | Polygon |
| Source coordinate system | EPSG:8193 (Esri 103412) |
| Vertices per feature in the sample | 11, 34, 14 |
| Max features per request | 2000 |
| Paging supported | yes |

## Sample rows

First 3 of 5 rows in [`data/sample/madison_zoning.csv`](../../data/sample/madison_zoning.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `OBJECTID` | 81989 | 81990 | 81991 | 81992 | 81993 |
| `ZONING_CODE` | IL | CN | A | PD | SR-C3 |
| `PD_ID` | 0 | 0 | 0 | 0 | 0 |
| `Shape.STArea()` | 382314.16805876326 | 325736.0298328476 | 148709.00167390535 | 206218.46250743596 | 614856.4345018403 |
| `Shape.STLength()` | 2902.0513309213993 | 3474.332181965639 | 3290.1564419456804 | 1859.1219243563346 | 6049.492059260662 |
| `Zoning_Document` | https://library.municode.com/wi/madison/codes/code_of_ordin… | https://library.municode.com/wi/madison/codes/code_of_ordin… | https://library.municode.com/wi/madison/codes/code_of_ordin… | https://library.municode.com/wi/madison/codes/code_of_ordin… | https://library.municode.com/wi/madison/codes/code_of_ordin… |
| `Zoning_District` | http://www.cityofmadison.com/assessor/documents/ZoningDistr… | http://www.cityofmadison.com/assessor/documents/ZoningDistr… | http://www.cityofmadison.com/assessor/documents/ZoningDistr… | http://www.cityofmadison.com/assessor/documents/ZoningDistr… | http://www.cityofmadison.com/assessor/documents/ZoningDistr… |

## Refresh

```sh
python3 scripts/fetch_samples.py madison_zoning
python3 scripts/build_data_dictionaries.py
```
