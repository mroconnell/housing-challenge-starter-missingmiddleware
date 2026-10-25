# Pennsylvania: PASDA county parcel layers (sample of counties)

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `pa_pasda_parcels`  

## Summary

| | |
|---|---|
| Publisher | Each county, republished by Penn State / PASDA |
| What it is | County parcel boundaries with assessment attributes. One layer per county, found through the PASDA catalog (see pa_pasda). We sample 6 counties to compare their fields. |
| Geography | Parcel, one county at a time. |
| Time coverage and update frequency | Each county uploads on its own schedule. File names carry a year-month stamp (for example 202607). |
| Units | One row per parcel polygon. |
| Access method | ArcGIS MapServer per county at https://mapservices.pasda.psu.edu/server/rest/services/pasda/<County>/MapServer (query with f=json). Bulk zip, KMZ and GeoJSON downloads are on each DataSummary page, for example https://www.pasda.psu.edu/download/adamscounty/AdamsCounty_Parcels202607.zip. |
| License | Varies by county. Check each dataset's metadata page. |
| Use in our model | Parcel inventory for Pennsylvania, if the team picks Pennsylvania. |
| Caveats | Not homogeneous. In our 6-county sample, fields per layer range from 5 (Lancaster: geometry and an account number only) to 38 (Berks: owner, deed, land use and assessed values). No attribute field name appears in all 6, apart from geometry and ids. The parcel id is called Parcel_ID, PIN, PROPID, PARCEL_NUM, TAXIDNUM or ACCOUNT. Assessed values appear only in Berks and Bucks. A statewide table needs a crosswalk per county, and some counties will need a join to separate assessment data. See the field comparison below. |

## Access details

- Endpoint used for the sample: `https://mapservices.pasda.psu.edu/server/rest/services/pasda`
- Each county publishes its own parcel layer with its own field names. Rows are 2 per county; columns are the union of all counties' fields, so most cells are blank.

## Fields (85)

| Field | Type | Meaning |
|---|---|---|
| `OBJECTID` | OID | In 6 of 6 counties |
| `Shape` | Geometry | In 6 of 6 counties |
| `Shape_Area` | Double | In 6 of 6 counties |
| `Shape_Length` | Double | In 6 of 6 counties |
| `GlobalID` | String | In 2 of 6 counties: Allegheny, Centre |
| `LOT` | String | In 2 of 6 counties: Berks, Centre |
| `PIN` | String | In 2 of 6 counties: Allegheny, Berks |
| `Shape_Leng` | Double | In 2 of 6 counties: Adams, Allegheny |
| `ACCOUNT` | String | In 1 of 6 counties: Lancaster |
| `ACREAGE` | Double | In 1 of 6 counties: Berks |
| `ACTIVE` | String | In 1 of 6 counties: Centre |
| `ADDRESS` | String | In 1 of 6 counties: Bucks |
| `BUILDING_V` | Double | In 1 of 6 counties: Bucks |
| `CALCACREAG` | Double | In 1 of 6 counties: Allegheny |
| `CAMA_ACRES` | Double | In 1 of 6 counties: Centre |
| `CARE_OF` | String | In 1 of 6 counties: Bucks |
| `CLASS` | String | In 1 of 6 counties: Berks |
| `CLNGREEN` | String | In 1 of 6 counties: Berks |
| `CNG` | String | In 1 of 6 counties: Centre |
| `COMBINED_S` | String | In 1 of 6 counties: Adams |
| `COMMENT1` | String | In 1 of 6 counties: Centre |
| `COMMENT2` | String | In 1 of 6 counties: Centre |
| `COMMENTS` | String | In 1 of 6 counties: Allegheny |
| `DATADATE` | Date | In 1 of 6 counties: Berks |
| `DATE_` | String | In 1 of 6 counties: Centre |
| `DEED_AREA` | String | In 1 of 6 counties: Bucks |
| `DEED_DATE` | Date | In 1 of 6 counties: Berks |
| `DEEDAMOUNT` | Double | In 1 of 6 counties: Berks |
| `DEEDBOOK` | String | In 1 of 6 counties: Berks |
| `DEEDED_ACR` | Double | In 1 of 6 counties: Adams |
| `DEEDPAGE` | String | In 1 of 6 counties: Berks |
| `DEEDSX1` | String | In 1 of 6 counties: Berks |
| `DEEDSX2` | String | In 1 of 6 counties: Berks |
| `DEFQUE` | String | In 1 of 6 counties: Centre |
| `DESCR1` | String | In 1 of 6 counties: Berks |
| `DESCR2` | String | In 1 of 6 counties: Berks |
| `DESCR3` | String | In 1 of 6 counties: Berks |
| `DESCR4` | String | In 1 of 6 counties: Berks |
| `DISTRICT_N` | String | In 1 of 6 counties: Adams |
| `FARMSTEAD` | String | In 1 of 6 counties: Berks |
| `FLAG` | String | In 1 of 6 counties: Centre |
| `FULLMAILAD` | String | In 1 of 6 counties: Berks |
| `FULLSITEAD` | String | In 1 of 6 counties: Berks |
| `HOMESTEAD` | String | In 1 of 6 counties: Berks |
| `LAND_USE_C` | String | In 1 of 6 counties: Bucks |
| `LAND_VALUE` | Double | In 1 of 6 counties: Bucks |
| `LANDUSE` | String | In 1 of 6 counties: Berks |
| `LOCATION` | String | In 1 of 6 counties: Centre |
| `MAP_ACRES` | Double | In 1 of 6 counties: Centre |
| `MAPBLOCKLO` | String | In 1 of 6 counties: Allegheny |
| `MODIFY_DAT` | Date | In 1 of 6 counties: Bucks |
| `MUNI` | String | In 1 of 6 counties: Berks |
| `MUNICIPALI` | String | In 1 of 6 counties: Bucks |
| `MUNICIPALN` | String | In 1 of 6 counties: Berks |
| `MUNICODE` | Integer | In 1 of 6 counties: Allegheny |
| `NAME1` | String | In 1 of 6 counties: Berks |
| `NOTES` | String | In 1 of 6 counties: Allegheny |
| `OBJECTID_1` | OID | In 1 of 6 counties: Centre |
| `OLDTAXIDNU` | String | In 1 of 6 counties: Centre |
| `OWNER1` | String | In 1 of 6 counties: Bucks |
| `OWNER2` | String | In 1 of 6 counties: Bucks |
| `Parcel_ID` | String | In 1 of 6 counties: Adams |
| `PARCEL_NUM` | String | In 1 of 6 counties: Bucks |
| `PARCEL_TYP` | String | In 1 of 6 counties: Centre |
| `PLANBKPG` | String | In 1 of 6 counties: Berks |
| `PLATREF1` | String | In 1 of 6 counties: Centre |
| `PLATREF2` | String | In 1 of 6 counties: Centre |
| `PROPERTY_T` | String | In 1 of 6 counties: Adams |
| `PROPID` | String | In 1 of 6 counties: Berks |
| `PSEUDONO` | String | In 1 of 6 counties: Allegheny |
| `SALE_DATE` | String | In 1 of 6 counties: Adams |
| `SCHOOL` | String | In 1 of 6 counties: Berks |
| `ShapeSTAre` | Double | In 1 of 6 counties: Centre |
| `ShapeSTLen` | Double | In 1 of 6 counties: Centre |
| `SHORT_NAME` | String | In 1 of 6 counties: Adams |
| `SITEADDRES` | String | In 1 of 6 counties: Berks |
| `SQL_UPDATE` | String | In 1 of 6 counties: Adams |
| `TAX_DIST` | String | In 1 of 6 counties: Berks |
| `TAX_DIST_N` | String | In 1 of 6 counties: Berks |
| `TAXIDNUM` | String | In 1 of 6 counties: Centre |
| `TOTAL_VALU` | Double | In 1 of 6 counties: Bucks |
| `VALUBLDG` | Double | In 1 of 6 counties: Berks |
| `VALULAND` | Double | In 1 of 6 counties: Berks |
| `VALULNDMKT` | Double | In 1 of 6 counties: Berks |
| `VALUTOTAL` | Double | In 1 of 6 counties: Berks |

## Field comparison across counties

| County | Layer | Parcels | Fields | Parcel id | Address | Land use | Value | Area |
|---|---|---|---|---|---|---|---|---|
| AdamsCounty | Adams County Parcels 202610 | 46908 | 13 | `Parcel_ID` | none | none | none | none |
| AlleghenyCounty | Allegheny County Parcels 20261019 | 587044 | 13 | `PIN` | none | none | none | `CALCACREAG` |
| BerksCounty | Berks County - Parcels 202601 | 156838 | 38 | `PROPID`, `PIN` | `FULLSITEAD`, `SITEADDRES` | `CLASS`, `LANDUSE` | `VALULNDMKT`, `VALULAND`, `VALUBLDG`, `VALUTOTAL` | `ACREAGE` |
| BucksCounty | Bucks County - Parcels 202605 | 237546 | 16 | `PARCEL_NUM` | `ADDRESS` | `LAND_USE_C` | `LAND_VALUE`, `TOTAL_VALU` | `DEED_AREA` |
| CentreCounty | Centre County - Parcels 202501 | 62031 | 24 | `TAXIDNUM`, `OLDTAXIDNU` | `LOCATION` | none | none | `MAP_ACRES`, `CAMA_ACRES` |
| LancasterCounty | Lancaster County Parcels 202609 | 188990 | 5 | `ACCOUNT` | none | none | none | none |

The concept columns are a name match only. They show which fields probably hold that idea, not a checked crosswalk.

## Geometry sample

[`data/sample/geo/pa_pasda_parcels.geojson`](../../data/sample/geo/pa_pasda_parcels.geojson) has 6 features. For privacy each parcel or unit outline is replaced by its bounding box on a 0.01-degree grid (about 1 km across), so the file shows the layer's attributes and rough location but cannot locate a property. Attributes are masked the same way as the CSV. Coordinates are WGS84 longitude/latitude.

| | |
|---|---|
| Geometry type | Polygon |
| Source coordinate system | varies by county; see counties |
| Vertices per feature in the source | 10, 5, 11, 11, 5, 8 |
| Max features per request | 1000 |
| Paging supported | yes |

## Sample rows

One row from each county, out of 12 rows in [`data/sample/pa_pasda_parcels.csv`](../../data/sample/pa_pasda_parcels.csv). Fields that are blank in every shown row are hidden. Owner names and mailing addresses are replaced with `[redacted]`. House and unit numbers are removed (street names kept), parcel and record ids are masked to their first 2 characters plus `***`, and coordinates are rounded.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 | Row 6 |
|---|---|---|---|---|---|---|
| `pasda_county` | AdamsCounty | AlleghenyCounty | BerksCounty | BucksCounty | CentreCounty | LancasterCounty |
| `Parcel_ID` | 40*** |  |  |  |  |  |
| `DEEDED_ACR` | 0 |  |  |  |  |  |
| `DISTRICT_N` | TYRONE TWP |  |  |  |  |  |
| `Shape_Leng` | 416.518020776 | 306.498674201 |  |  |  |  |
| `Shape_Length` | 416.5180207764215 | 306.49838986591016 | 1271.0149202203818 | 48.222509572013514 | 503.9305682211005 | 306.0447537217413 |
| `Shape_Area` | 10131.144899610563 | 3251.1447646296588 | -45077.73277939899 | 104.10029328552962 | 10212.34776844263 | 3037.8317193431826 |
| `PIN` |  | 01*** | 53*** |  |  |  |
| `MAPBLOCKLO` |  | 10*** |  |  |  |  |
| `MUNICODE` |  | 941 |  |  |  |  |
| `CALCACREAG` |  | 0.07 |  |  |  |  |
| `PROPID` |  |  | 01*** |  |  |  |
| `NAME1` |  |  | [redacted] |  |  |  |
| `FULLMAILAD` |  |  | [redacted] |  |  |  |
| `FULLSITEAD` |  |  | WATER ST |  |  |  |
| `MUNI` |  |  | READING |  |  |  |
| `ACREAGE` |  |  | 1.03389299 |  |  |  |
| `DEED_DATE` |  |  | 115344000000 |  |  |  |
| `DEEDAMOUNT` |  |  | 0 |  |  |  |
| `TAX_DIST` |  |  | 01 |  |  |  |
| `DESCR2` |  |  | DETACHED IMPROVEMENTS |  |  |  |
| `SCHOOL` |  |  | 19 |  |  |  |
| `CLASS` |  |  | E |  |  |  |
| `VALULNDMKT` |  |  | 17400 |  |  |  |
| `VALULAND` |  |  | 0 |  |  |  |
| `VALUBLDG` |  |  | 0 |  |  |  |
| `VALUTOTAL` |  |  | 0 |  |  |  |
| `LANDUSE` |  |  | 2506 |  |  |  |
| `HOMESTEAD` |  |  | NOT ENROLLED |  |  |  |
| `FARMSTEAD` |  |  | NOT ENROLLED |  |  |  |
| `MUNICIPALN` |  |  | READING |  |  |  |
| `DATADATE` |  |  | 1767916800000 |  |  |  |
| `TAX_DIST_N` |  |  | CITY OF READING |  |  |  |
| `PARCEL_NUM` |  |  |  | 54*** |  |  |
| `ADDRESS` |  |  |  | YARDLEY COMMONS |  |  |
| `OWNER1` |  |  |  | [redacted] |  |  |
| `OWNER2` |  |  |  | [redacted] |  |  |
| `CARE_OF` |  |  |  | [redacted] |  |  |
| `MUNICIPALI` |  |  |  | Yardley Borough |  |  |
| `LAND_VALUE` |  |  |  | 0 |  |  |
| `BUILDING_V` |  |  |  | 15200 |  |  |
| `TOTAL_VALU` |  |  |  | 15200 |  |  |
| `LAND_USE_C` |  |  |  | 1013 |  |  |
| `MODIFY_DAT` |  |  |  | 1753833600000 |  |  |
| `TAXIDNUM` |  |  |  |  | 32*** |  |
| `MAP_ACRES` |  |  |  |  | 0.23444325 |  |
| `CAMA_ACRES` |  |  |  |  | 0.22 |  |
| `PARCEL_TYP` |  |  |  |  | Standard |  |
| `FLAG` |  |  |  |  | True |  |
| `DATE_` |  |  |  |  | 2022-06-06T13:24:24Z |  |
| `DEFQUE` |  |  |  |  | 32*** |  |
| `ShapeSTAre` |  |  |  |  | 10212.347767747995 |  |
| `ShapeSTLen` |  |  |  |  | 503.93056821661986 |  |
| `ACCOUNT` |  |  |  |  |  | 60*** |

## Refresh

```sh
python3 scripts/fetch_samples.py pa_pasda_parcels
python3 scripts/build_data_dictionaries.py
```
