# Connecticut: CAMA and Parcel Layer

**Status:** Fetched (last fetch 2026-10-17)  
**Source id:** `ct_cama_parcels`  

## Summary

| | |
|---|---|
| Publisher | State of Connecticut (Office of Policy and Management) |
| What it is | Statewide parcels joined to town assessor (CAMA) records: land use, zoning, building details and values. |
| Geography | Parcel, statewide. |
| Time coverage and update frequency | Updated about yearly. |
| Units | Dollars for values, acres or square feet for areas (see field names). |
| Access method | ArcGIS item 82a733423a244c43a9d4bf552954cea9 on https://geodata.ct.gov (FeatureServer query API, CSV/GeoJSON download). |
| License | See item page. |
| Use in our model | Parcel inventory with zoning and land use in one layer. Good for ADU, missing-middle and parking scenarios in Connecticut. |
| Caveats | Zoning and land use codes are town-specific and not standardized. |

## Access details

- Endpoint used for the sample: `https://services3.arcgis.com/3FL1kr7L4LvwA2Kb/arcgis/rest/services/Connecticut_CAMA_and_Parcel_Layer/FeatureServer/0`
- Layer: Connecticut_CAMA_and_Parcel_Layer
- Total records at fetch time: 1320686
- Last edited: 2026-10-06
- Item: Connecticut CAMA and Parcel Layer (owner `ctgisoffice`, id `82a733423a244c43a9d4bf552954cea9`)
- Geometry: esriGeometryPolygon

## Fields (62)

| Field | Type | Meaning |
|---|---|---|
| `OBJECTID` | OID |  |
| `Source_Date` | String |  |
| `Source_Type` | String |  |
| `Source_Name` | String |  |
| `Editor` | String |  |
| `Editor_Comment` | String | Editor Comment |
| `Edit_Date` | String | Edit Date |
| `Edit_Method` | String |  |
| `Edit_Type` | String |  |
| `Location` | String |  |
| `Link` | String |  |
| `Parcel_Type` | String | Parcel Type |
| `Town_Name` | String | Connecticut town. |
| `Unit_Type` | String |  |
| `Parcel_ID` | String | Town parcel id (map/block/lot). |
| `ZIP_CODE` | String |  |
| `FIPS` | String | Census block FIPS code of the parcel. |
| `CAMA_Link` | String | Key that joins the parcel to the town assessor (CAMA) record. |
| `COG` | String | Council of Governments region. |
| `Parcel_Collection_Year` | String |  |
| `OBJECTID_1` | String | OBJECTID |
| `Location_1` | String | Location |
| `Property_Zip` | String |  |
| `link_1` | String | link |
| `Property_City` | String | Property City |
| `Owner` | String | Owner name. Redacted in our sample. |
| `Co_Owner` | String | Second owner name. Redacted in our sample. |
| `Mailing_Address` | String | Owner mailing address. Redacted in our sample. |
| `Mailing_City` | String | Mailing City |
| `Mailing_State` | String | Mailing State |
| `Mailing_Zip` | String |  |
| `Assessed_Total` | Double | Total assessed value, dollars (CT assesses at 70% of market value). |
| `Assessed_Land` | Double | Assessed value of land, dollars. |
| `Assessed_Building` | Double | Assessed value of buildings, dollars. |
| `Pre_Yr_Assessed_Total` | Double | Pre Yr Assessed Total |
| `Appraised_Land` | Double | Appraised (market) value of land, dollars. |
| `Appraised_Building` | Double | Appraised (market) value of buildings, dollars. |
| `Appraised_Outbuilding` | Double | Appraised Outbuilding |
| `Valuation_Year` | Double | Valuation Year |
| `Land_Acres` | Double | Lot size, acres. |
| `Zone` | String | Local zoning district code. Codes differ by town. |
| `State_Use` | String | State land use code (for example 101 = single family). |
| `State_Use_Description` | String | Text for State_Use. |
| `Model` | String |  |
| `Condition` | String |  |
| `Living_Area` | Double | Finished living area, square feet. |
| `Effective_Area` | Double | Effective (weighted) building area, square feet. |
| `Total_Rooms` | Double | Total Rooms |
| `Number_of_Bedroom` | Double | Number of Bedroom |
| `Number_of_Baths` | Double | Number of Baths |
| `Number_of_Half_Baths` | Double | Number of Half Baths |
| `Sale_Price` | Double | Last sale price, dollars. |
| `Sale_Date` | String | Last sale date. |
| `Prior_Sale_Date` | String | Prior Sale Date |
| `Prior_Book_Page` | String | Prior Book Page |
| `Prior_Sale_Price` | String | Prior Sale Price |
| `Occupancy` | Double | Number of dwelling units in the building, where recorded. Our reading; confirm in publisher docs. |
| `AYB` | Double | Actual year built. |
| `EYB` | Double | Effective year built (after renovations). |
| `CAMA_Collection_Year` | Integer |  |
| `Shape__Area` | Double | Polygon area in the layer's units (square meters for Web Mercator). |
| `Shape__Length` | Double | Polygon perimeter in the layer's units. |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Sample rows

First 3 of 5 rows in [`data/sample/ct_cama_parcels.csv`](../../data/sample/ct_cama_parcels.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 |
|---|---|---|---|
| `OBJECTID` | 1 | 2 | 3 |
| `Source_Date` |  |  |  |
| `Source_Type` |  |  |  |
| `Source_Name` |  |  |  |
| `Editor` | AppGeo | AppGeo | AppGeo |
| `Editor_Comment` | Adjusted parcel boundaries | Adjusted parcel boundaries | Adjusted parcel boundaries |
| `Edit_Date` | 10/1/2014 | 10/1/2014 | 10/1/2014 |
| `Edit_Method` |  |  |  |
| `Edit_Type` |  |  |  |
| `Location` | GILEAD RD | GILEAD RD | GILEAD RD |
| `Link` | 206 | 11 | 207 |
| `Parcel_Type` | PARCEL | PARCEL | PARCEL |
| `Town_Name` | Andover | Andover | Andover |
| `Unit_Type` |  |  |  |
| `Parcel_ID` | 25/022/000019 | 17/017/014-15 | 25/022/000020 |
| `ZIP_CODE` | 06248 | 06232 | 06248 |
| `FIPS` | 09013526102 | 09013526102 | 09013528100 |
| `CAMA_Link` | 01080-206 | 01080-11 | 01080-207 |
| `COG` | Capitol Region | Capitol Region | Capitol Region |
| `Parcel_Collection_Year` | 2026 | 2026 | 2026 |
| `OBJECTID_1` |  |  |  |
| `Location_1` | 281 GILEAD RD | 280 GILEAD RD | 275 GILEAD RD |
| `Property_Zip` |  |  |  |
| `link_1` | 01080-206 | 01080-11 | 01080-207 |
| `Property_City` | Andover | Andover | Andover |
| `Owner` | [redacted] | [redacted] | [redacted] |
| `Co_Owner` | [redacted] |  |  |
| `Mailing_Address` | [redacted] | [redacted] | [redacted] |
| `Mailing_City` | [redacted] | [redacted] | [redacted] |
| `Mailing_State` | [redacted] | [redacted] | [redacted] |
| `Mailing_Zip` |  |  |  |
| `Assessed_Total` | 441560 | 171500 | 196490 |
| `Assessed_Land` | 36960 | 37800 | 36750 |
| `Assessed_Building` |  |  |  |
| `Pre_Yr_Assessed_Total` |  |  |  |
| `Appraised_Land` | 52800 | 54000 | 52500 |
| `Appraised_Building` | 577300 | 187800 | 224400 |
| `Appraised_Outbuilding` | 700 | 1100 | 1700 |
| `Valuation_Year` | 2021 | 2021 | 2021 |
| `Land_Acres` | 2 | 3 | 2 |
| `Zone` | ARD | ARD | ARD |
| `State_Use` | 1010 | 1010 | 1010 |
| `State_Use_Description` | Single Fam  MDL-01 | Single Fam  MDL-01 | Single Fam  MDL-01 |
| `Model` | 1.0 | 1.0 | 1.0 |
| `Condition` | A | G | G |
| `Living_Area` | 3879 | 1848 | 1250 |
| `Effective_Area` | 4807 | 2023 | 2167 |
| `Total_Rooms` | 9 | 6 | 5 |
| `Number_of_Bedroom` | 4 | 3 | 3 |
| `Number_of_Baths` | 3 | 2 | 2 |
| `Number_of_Half_Baths` | 1 | 0 | 1 |
| `Sale_Price` | 357000 | 0 | 145000 |
| `Sale_Date` | 7/21/2020 12:00:00 AM | 12/29/1997 12:00:00 AM | 1/28/1992 12:00:00 AM |
| `Prior_Sale_Date` |  |  |  |
| `Prior_Book_Page` | 0055/0217 | 0068/1068 | 0054/0535 |
| `Prior_Sale_Price` | 163400.0 | 135000.0 | 40000.0 |
| `Occupancy` | 1 | 1 | 1 |
| `AYB` | 2021 | 1986 | 1991 |
| `EYB` | 2021 | 2004 | 2005 |
| `CAMA_Collection_Year` | 2026 | 2026 | 2026 |
| `Shape__Area` | 45924.39978027344 | 113904.96948242188 | 69888.23443192244 |
| `Shape__Length` | 998.540688658286 | 1576.2894192202698 | 1102.442748856254 |

## Refresh

```sh
python3 scripts/fetch_samples.py ct_cama_parcels
python3 scripts/build_data_dictionaries.py
```
