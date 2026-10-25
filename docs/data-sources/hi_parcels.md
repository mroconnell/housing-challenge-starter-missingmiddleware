# Hawaii: Statewide parcels

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `hi_parcels`  

## Summary

| | |
|---|---|
| Publisher | Hawaii Statewide GIS Program |
| What it is | Tax map key (TMK) parcel boundaries for all four counties in one layer. |
| Geography | Parcel, statewide. |
| Time coverage and update frequency | Updated periodically. |
| Units | Acres / square feet. |
| Access method | https://geoportal.hawaii.gov (ArcGIS Hub; REST query endpoint). |
| License | See item page. |
| Use in our model | Parcel inventory for Hawaii. Zoning is on the same portal by county. |
| Caveats | The statewide layer has parcel ids and shapes only. Land and building values, use class and owner type are in the county parcel layers on the same service (for example Parcels - Hawaii County) and in county assessor records. Zoning is a separate layer per county. |

## Access details

- Endpoint used for the sample: `https://geodata.hawaii.gov/arcgis/rest/services/ParcelsZoning/MapServer/25`
- Layer: Statewide TMKs
- Total records at fetch time: 384035
- Item: Parcels - Hawaii Statewide (owner `HawaiiStateGIS`, id `579b8dcb7a8e44c1af201e1b3cdf655f`)
- Geometry: esriGeometryPolygon

## Fields (18)

| Field | Type | Meaning |
|---|---|---|
| `objectid` | OID | FID |
| `shape` | Geometry | Shape |
| `tmk` | Integer | Tax Map Key, the Hawaii parcel id (island, zone, section, plat, parcel). |
| `tmk_txt` | String | TMK as text. |
| `county` | String | County name. |
| `division` | String | TMK division (first digit of the TMK): 1 Oahu, 2 Maui County, 3 Hawaii County, 4 Kauai. |
| `island` | String | Island code (HAW, OAH, MAU...). |
| `zone` | String | TMK zone (2nd digit of the TMK). Not zoning. |
| `section` | String | TMK section. |
| `plat` | String | TMK plat. |
| `plat1` | String | TMK plat, zero-padded. |
| `parcel` | String | TMK parcel number. |
| `parcel1` | String | TMK parcel number, zero-padded. |
| `gisacres` | Double | Parcel area from GIS geometry, acres. |
| `cty_tmk` | String | TMK without the division digit (county format). |
| `qpub_link` | String | Link to the county assessor (qPublic) record. |
| `st_area(shape)` | Double |  |
| `st_perimeter(shape)` | Double |  |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Geometry sample

[`data/sample/geo/hi_parcels.geojson`](../../data/sample/geo/hi_parcels.geojson) has 3 features. For privacy each parcel or unit outline is replaced by its bounding box on a 0.01-degree grid (about 1 km across), so the file shows the layer's attributes and rough location but cannot locate a property. Attributes are masked the same way as the CSV. Coordinates are WGS84 longitude/latitude.

| | |
|---|---|
| Geometry type | Polygon |
| Source coordinate system | EPSG:3750 (Esri 102202) |
| Vertices per feature in the source | 5, 5, 5 |
| Max features per request | 1000 |
| Paging supported | yes |

## Sample rows

First 3 of 5 rows in [`data/sample/hi_parcels.csv`](../../data/sample/hi_parcels.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`. House and unit numbers are removed (street names kept), parcel and record ids are masked to their first 2 characters plus `***`, and coordinates are rounded.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `tmk` | 38*** | 38*** | 38*** | 38*** | 38*** |
| `tmk_txt` | 38*** | 38*** | 38*** | 38*** | 38*** |
| `county` | Hawaii | Hawaii | Hawaii | Hawaii | Hawaii |
| `division` | 3 | 3 | 3 | 3 | 3 |
| `island` | HAW | HAW | HAW | HAW | HAW |
| `zone` | 8 | 8 | 8 | 8 | 8 |
| `section` | 9 | 8 | 8 | 8 | 8 |
| `gisacres` | 0.2300499 | 0.16977402 | 0.16975509 | 0.17306839 | 0.17084862 |
| `cty_tmk` | 89*** | 88*** | 88*** | 88*** | 88*** |
| `st_area(shape)` | 930.9826425866745 | 687.0538207842359 | 686.9772409296497 | 700.3857085684095 | 691.402583104587 |
| `st_perimeter(shape)` | 122.72679528475079 | 111.98270600577544 | 112.0491522904305 | 112.79718312940749 | 112.33948801211821 |

## Refresh

```sh
python3 scripts/fetch_samples.py hi_parcels
python3 scripts/build_data_dictionaries.py
```
