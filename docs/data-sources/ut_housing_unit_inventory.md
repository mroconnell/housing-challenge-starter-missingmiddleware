# Utah: Housing Unit Inventory

**Status:** Fetched (last fetch 2026-10-23)  
**Source id:** `ut_housing_unit_inventory`  

## Summary

| | |
|---|---|
| Publisher | Utah Geospatial Resource Center (UGRC) / Wasatch Front Regional Council |
| What it is | Parcel-level count of housing units and housing type, with year built, for Wasatch Front counties. |
| Geography | Parcel / development, Wasatch Front counties. |
| Time coverage and update frequency | Updated yearly. |
| Units | Housing units (count), year built, acres. |
| Access method | ArcGIS FeatureServer, https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/HousingUnitInventory/FeatureServer/0. |
| License | See UGRC terms (open). |
| Use in our model | Unusually good: actual unit counts and types by parcel, including ADUs and duplexes. Lets us measure missing-middle and ADU production over time in Utah. |
| Caveats | Not every Utah county is covered. |

## Access details

- Endpoint used for the sample: `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/HousingUnitInventory/FeatureServer/0`
- Layer: HousingUnitInventory
- Total records at fetch time: 702461
- Last edited: 2026-10-21
- Geometry: esriGeometryPolygon

## Fields (18)

| Field | Type | Meaning |
|---|---|---|
| `OBJECTID` | OID |  |
| `UNIT_ID` | Integer | Id of the housing development record. |
| `TYPE` | String | Housing type: single_family, multi_family, townhome, duplex, ADU and similar. |
| `SUBTYPE` | String | More detailed housing type. |
| `IS_OUG` | String | 1 if an owned unit grouping (condo or townhome complex) shown as one record. |
| `UNIT_COUNT` | Double | Number of housing units. |
| `DUA` | Double | Dwelling units per acre. |
| `ACRES` | Double | Area, acres. |
| `TOT_BD_FT2` | Double | Total building floor area, square feet. |
| `TOT_VALUE` | Double | Total market value, dollars. |
| `APX_BLT_YR` | Double | Approximate year built. |
| `BLT_DECADE` | Integer | Decade built. |
| `CITY` | String | City. |
| `COUNTY` | String | County. |
| `SUBCOUNTY` | String | Sub-county area used by the regional council. |
| `EVAL_DATE` | Date | Date the record was reviewed. |
| `Shape__Area` | Double |  |
| `Shape__Length` | Double |  |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Sample rows

First 3 of 5 rows in [`data/sample/ut_housing_unit_inventory.csv`](../../data/sample/ut_housing_unit_inventory.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 |
|---|---|---|---|
| `OBJECTID` | 1 | 2 | 3 |
| `UNIT_ID` | 1001 | 1002 | 2001 |
| `TYPE` | single_family | single_family | single_family |
| `SUBTYPE` | single_family | single_family | single_family |
| `IS_OUG` | 0 | 0 | 0 |
| `UNIT_COUNT` | 1 | 1 | 1 |
| `DUA` | 3.57 | 5.26 | 5.56 |
| `ACRES` | 0.28 | 0.19 | 0.18 |
| `TOT_BD_FT2` | 4434 | 949 | 1787 |
| `TOT_VALUE` | 665500 | 408000 | 574000 |
| `APX_BLT_YR` | 1973 | 2000 | 1899 |
| `BLT_DECADE` | 1970 | 2000 | 1890 |
| `CITY` | Millcreek | Roy | Salt Lake City |
| `COUNTY` | Salt Lake | Weber | Salt Lake |
| `SUBCOUNTY` | North Salt Lake County (WFRC) | South Weber County (WFRC) | North Salt Lake County (WFRC) |
| `EVAL_DATE` |  |  |  |
| `Shape__Area` | 1956.9375 | 1348.015625 | 1237.9453125 |
| `Shape__Length` | 192.40428794479112 | 149.69905492905326 | 232.67475213938638 |

## Refresh

```sh
python3 scripts/fetch_samples.py ut_housing_unit_inventory
python3 scripts/build_data_dictionaries.py
```
