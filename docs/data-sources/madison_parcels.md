# Madison, WI: tax parcels

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `madison_parcels`  
**Handbook listing:** Not in the handbook. Parcel base for the Madison ADU pilot.

## Summary

| | |
|---|---|
| Publisher | City of Madison (Assessor / Information Technology) |
| What it is | City tax parcels with property use, dwelling units, year built, zoning and lot size. |
| Geography | Parcel. |
| Time coverage and update frequency | Current snapshot, edited as parcels change (see Last edited below). |
| Units | One row per parcel. LotSize is square feet. |
| Access method | ArcGIS FeatureServer: https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA2/FeatureServer/0 (also on https://data-cityofmadison.opendata.arcgis.com/). |
| License | City of Madison open data terms (see the open data portal). |
| Use in our model | Count improved single-family parcels and zoning for ADU eligibility in Madison. |
| Caveats | Madison only. Zoning text (ZoningAll) can list several districts for one parcel. |

## Access details

- Endpoint used for the sample: `https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA2/FeatureServer/0`
- Layer: Tax Parcels
- Total records at fetch time: 82616
- Geometry: esriGeometryPolygon

## Fields (142)

| Field | Type | Meaning |
|---|---|---|
| `OBJECTID` | OID |  |
| `Parcel` | String | Parcel number. |
| `XRefParcel` | String |  |
| `Address` | String |  |
| `DateParcelChanged` | Date |  |
| `PropertyClass` | String |  |
| `PropertyUse` | String | Assessor use description, for example Single family. |
| `AssessmentArea` | Double |  |
| `AreaName` | String |  |
| `MoreThanOneBuild` | String |  |
| `HomeStyle` | String |  |
| `YearBuilt` | Double | Year the main building was built. |
| `Bedrooms` | Double |  |
| `FullBaths` | Double |  |
| `HalfBaths` | Double |  |
| `TotalLivingArea` | Double |  |
| `FirstFloor` | Double |  |
| `SecondFloor` | Double |  |
| `ThirdFloor` | Double |  |
| `AboveThirdFloor` | Double |  |
| `FinishedAttic` | Double |  |
| `Basement` | Double |  |
| `FinishedBasement` | Double |  |
| `ExteriorWall1` | String |  |
| `ExteriorWall2` | String |  |
| `Fireplaces` | Integer |  |
| `CentralAir` | String |  |
| `PartialAssessed` | String |  |
| `AssessedByState` | String |  |
| `CurrentLand` | Double |  |
| `CurrentImpr` | Double |  |
| `CurrentTotal` | Double |  |
| `PreviousLand` | Double |  |
| `PreviousImpr` | Double |  |
| `PreviousTotal` | Double |  |
| `NetTaxes` | Double |  |
| `SpecialAssmnt` | Double |  |
| `OtherCharges` | Double |  |
| `TotalTaxes` | Double |  |
| `LotSize` | Double | Lot area, square feet. |
| `Zoning1` | String | First zoning district. |
| `Zoning2` | String |  |
| `Zoning3` | String |  |
| `Zoning4` | String |  |
| `FrontageStreet` | String |  |
| `WaterFrontage` | String |  |
| `TIFDistrict` | Double |  |
| `TaxSchoolDist` | String |  |
| `AttendanceSchool` | String |  |
| `ElementarySchool` | String |  |
| `MiddleSchool` | String |  |
| `HighSchool` | String |  |
| `Ward` | Double |  |
| `StateAssemblyDistrict` | Double |  |
| `RefuseDistrict` | String |  |
| `RefuseURL` | String |  |
| `PreviousLand2` | Double |  |
| `PreviousImpr2` | Double |  |
| `PreviousTotal2` | Double |  |
| `AlderDistrict` | SmallInteger |  |
| `AssessmentChangeDate` | Date |  |
| `BlockNumber` | SmallInteger |  |
| `BuildingDistrict` | SmallInteger |  |
| `CapitolFireDistrict` | String |  |
| `ConditionalUse` | SmallInteger |  |
| `CouncilHold` | SmallInteger |  |
| `DateAdded` | Date |  |
| `DeedPage` | Integer |  |
| `DeedRestriction` | SmallInteger |  |
| `DeedVolume` | Integer |  |
| `ElectricalDistrict` | SmallInteger |  |
| `EnvHealthDistrict` | SmallInteger |  |
| `ExemptionType` | String |  |
| `FireDistrict` | SmallInteger |  |
| `FloodPlain` | SmallInteger |  |
| `FuelStorageProximity` | SmallInteger |  |
| `HeatingDistrict` | SmallInteger |  |
| `Holds` | String |  |
| `IllegalLandDivision` | SmallInteger |  |
| `LandfillProximity` | SmallInteger |  |
| `LandfillRemediation` | String |  |
| `Landmark` | String |  |
| `LandscapeBuffer` | SmallInteger |  |
| `LocalHistoricalDist` | String |  |
| `LotDepth` | Double |  |
| `LotNumber` | SmallInteger |  |
| `LotType1` | String |  |
| `LotType2` | String |  |
| `LotWidth` | Double |  |
| `MCDCode` | String |  |
| `NationalHistoricalDist` | SmallInteger |  |
| `NeighborhoodDesc` | String |  |
| `NeighborhoodPrimary` | String |  |
| `NeighborhoodSub` | String |  |
| `NeighborhoodVuln` | String |  |
| `NoiseAirport` | SmallInteger |  |
| `NoiseRailroad` | SmallInteger |  |
| `NoiseStreet` | SmallInteger |  |
| `ObsoleteDate` | Date |  |
| `OwnerChangeDate` | Date |  |
| `OwnerOccupied` | String |  |
| `ParcelChangeDate` | Date |  |
| `ParcelCode` | String |  |
| `ParkProximity` | SmallInteger |  |
| `Pending` | String |  |
| `PlanningDistrict` | String |  |
| `PlumbingDistrict` | SmallInteger |  |
| `PoliceDistrict` | String |  |
| `PoliceSector` | SmallInteger |  |
| `PreviousClass` | String |  |
| `PropertyUseCode` | SmallInteger |  |
| `RailroadFrontage` | String |  |
| `ReasonChangeImpr` | String |  |
| `ReasonChangeLand` | String |  |
| `SenateDistrict` | SmallInteger |  |
| `SupervisorDistrict` | SmallInteger |  |
| `TifImpr` | Integer |  |
| `TifLand` | Integer |  |
| `TifYear` | SmallInteger |  |
| `TotalDwellingUnits` | SmallInteger | Dwelling units on the parcel. |
| `TrafficAnalysisZone` | SmallInteger |  |
| `TypeWaterFrontage` | String |  |
| `UWPolice` | String |  |
| `WetlandInfo` | String |  |
| `ZoningAll` | String | All zoning districts on the parcel, comma separated. |
| `ZoningBoardAppeal` | SmallInteger |  |
| `UrbanDesignDistrict` | String |  |
| `HouseNbr` | Integer |  |
| `StreetDir` | String |  |
| `StreetName` | String |  |
| `StreetType` | String |  |
| `Unit` | String |  |
| `StreetID` | Integer |  |
| `StormOutfall` | String |  |
| `FireDemandZone` | Integer |  |
| `FireDemandSubZone` | Integer |  |
| `PropertyChangeDate` | Date |  |
| `MaxConstructionYear` | Integer |  |
| `XCoord` | Double | X coordinate (state plane). |
| `YCoord` | Double | Y coordinate (state plane). |
| `Shape__Area` | Double | SHAPE.STArea() |
| `Shape__Length` | Double | SHAPE.STLength() |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Geometry sample

[`data/sample/geo/madison_parcels.geojson`](../../data/sample/geo/madison_parcels.geojson) has 3 features. For privacy each parcel or unit outline is replaced by its bounding box on a 0.01-degree grid (about 1 km across), so the file shows the layer's attributes and rough location but cannot locate a property. Attributes are masked the same way as the CSV. Coordinates are WGS84 longitude/latitude.

| | |
|---|---|
| Geometry type | Polygon |
| Source coordinate system | EPSG:8193 (Esri 103412) |
| Vertices per feature in the source | 5, 5, 38 |
| Max features per request | 2000 |
| Paging supported | yes |

## Sample rows

First 3 of 5 rows in [`data/sample/madison_parcels.csv`](../../data/sample/madison_parcels.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`. House and unit numbers are removed (street names kept), parcel and record ids are masked to their first 2 characters plus `***`, and coordinates are rounded.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `Parcel` | 07*** | 07*** | 06*** | 07*** | 07*** |
| `XRefParcel` | 07*** | 07*** | 06*** | 07*** | 07*** |
| `Address` | Sudbury Way | Hackney Way | S STONE CREEK Cir | N Westfield Rd | Harding St |
| `DateParcelChanged` |  | 1791980220000 |  |  |  |
| `PropertyClass` | Residential | Residential | Residential | Residential | Residential |
| `PropertyUse` | Single family | Single family | Condominium | Single family | Single family |
| `AssessmentArea` | 47.0 | 47.0 | 5109.0 | 94.0 | 40.0 |
| `AreaName` | Heritage Heights | Heritage Heights | Condominium's in Res Area 109 | Wexford Sawmill Longmeadow | Olbrich |
| `MoreThanOneBuild` | NO | NO | NO | NO | YES |
| `HomeStyle` | Bi-level | Modern Multi Story | Townhouse | Modern Multi Story | Bungalow |
| `YearBuilt` | 1985.0 | 1986.0 | 1996.0 | 1985.0 | 1949.0 |
| `Bedrooms` | 3.0 | 3.0 | 2.0 | 4.0 | 2.0 |
| `FullBaths` | 2.0 | 3.0 | 2.0 | 3.0 | 1.0 |
| `HalfBaths` | 0.0 | 1.0 | 1.0 | 1.0 | 0.0 |
| `TotalLivingArea` | 1022.0 | 1826.0 | 1300.0 | 2550.0 | 736.0 |
| `FirstFloor` | 1022.0 | 1046.0 | 713.0 | 1598.0 | 736.0 |
| `SecondFloor` | 0.0 | 780.0 | 587.0 | 952.0 | 0.0 |
| `ThirdFloor` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `AboveThirdFloor` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `FinishedAttic` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `Basement` | 912.0 | 1046.0 | 681.0 | 1364.0 | 0.0 |
| `FinishedBasement` | 570.0 | 300.0 | 500.0 | 704.0 | 0.0 |
| `ExteriorWall1` | Masonry Facing | Aluminum/Vinyl | Aluminum/Vinyl | Wood | Aluminum/Vinyl |
| `ExteriorWall2` | Cement/Smart |  |  | Masonry Facing |  |
| `Fireplaces` | 0 | 0 | 1 | 1 | 1 |
| `CentralAir` | YES | YES | YES | YES | NO |
| `CurrentLand` | 113600.0 | 111600.0 | 26700.0 | 172200.0 | 134800.0 |
| `CurrentImpr` | 268800.0 | 310800.0 | 351200.0 | 452700.0 | 186600.0 |
| `CurrentTotal` | 382400.0 | 422400.0 | 377900.0 | 624900.0 | 321400.0 |
| `PreviousLand` | 69700.0 | 68500.0 | 26700.0 | 152200.0 | 80600.0 |
| `PreviousImpr` | 307000.0 | 347700.0 | 351200.0 | 495100.0 | 221200.0 |
| `PreviousTotal` | 376700.0 | 416200.0 | 377900.0 | 647300.0 | 301800.0 |
| `NetTaxes` | 6662.72 | 7399.65 | 6685.11 | 11711.13 | 5539.2 |
| `SpecialAssmnt` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `OtherCharges` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `TotalTaxes` | 7134.17 | 10078.15 | 7050.22 | 11658.32 | 5996.13 |
| `LotSize` | 9574.48 | 9199.87 | 0.0 | 10781.1 | 5998.21 |
| `FrontageStreet` | Sudbury Way | Hackney Way | South Stone Creek Cir | N Westfield Rd | Harding St |
| `WaterFrontage` | 0 | 0 | 0 | 0 | 0 |
| `TIFDistrict` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `TaxSchoolDist` | 3269 | 3269 | 3269 | 3269 | 3269 |
| `ElementarySchool` | Kennedy | Kennedy | Chavez | Stephens | Schenk |
| `MiddleSchool` | Whitehorse | Whitehorse | Toki | Gillespie | Whitehorse |
| `HighSchool` | La Follette | La Follette | Memorial | Memorial | La Follette |
| `Ward` | 10.0 | 10.0 | 105.0 | 96.0 | 17.0 |
| `StateAssemblyDistrict` | 78.0 | 78.0 | 80.0 | 79.0 | 76.0 |
| `RefuseDistrict` | 01B | 01B | 04A | 10A | 03B |
| `RefuseURL` | https://www.cityofmadison.com/streets/documents/monB.pdf | https://www.cityofmadison.com/streets/documents/monB.pdf | https://www.cityofmadison.com/streets/documents/tueA.pdf | https://www.cityofmadison.com/streets/documents/friA.pdf | https://www.cityofmadison.com/streets/documents/tueB.pdf |
| `PreviousLand2` | 69700.0 | 68500.0 | 26700.0 | 152200.0 | 80600.0 |
| `PreviousImpr2` | 307000.0 | 347700.0 | 351200.0 | 495100.0 | 221200.0 |
| `PreviousTotal2` | 376700.0 | 416200.0 | 377900.0 | 647300.0 | 301800.0 |
| `AlderDistrict` | 3 | 3 | 7 | 19 | 15 |
| `AssessmentChangeDate` |  | 1791980220000 |  |  |  |
| `BuildingDistrict` | 4 | 4 | 2 | 1 | 4 |
| `DeedRestriction` | 0 | 0 | 0 | 0 | 0 |
| `ElectricalDistrict` | 4 | 4 | 1 | 1 | 4 |
| `EnvHealthDistrict` | 6 | 6 | 11 | 14 | 5 |
| `FireDistrict` | 25 | 25 | 34 | 61 | 25 |
| `FloodPlain` | 0 | 0 | 0 | 0 | 0 |
| `HeatingDistrict` | 7 | 7 | 2 | 1 | 7 |
| `IllegalLandDivision` | 0 | 0 | 0 | 0 | 0 |
| `LandscapeBuffer` | 0 | 0 | 0 | 0 | 0 |
| `LotDepth` | 126.0 | 126.0 | 0.0 | 0.0 | 120.0 |
| `LotType1` | Regular | Regular | Other | Irregular | Regular |
| `LotType2` | No Exception | No Exception | No Exception | No Exception | No Exception |
| `LotWidth` | 76.0 | 73.0 | 0.0 | 0.0 | 50.0 |
| `NationalHistoricalDist` | 0 | 0 | 0 | 0 | 0 |
| `ParcelChangeDate` |  | 1791980220000 |  |  |  |
| `ParcelCode` | A | A | A | A | A |
| `PlanningDistrict` | E | E | W | W | E |
| `PlumbingDistrict` | 3 | 3 | 1 | 1 | 3 |
| `PoliceDistrict` | F | F | A | A | F |
| `PoliceSector` | 612 | 612 | 120 | 126 | 610 |
| `PropertyUseCode` | 1 | 1 | 2 | 1 | 1 |
| `SenateDistrict` | 26 | 26 | 27 | 27 | 26 |
| `SupervisorDistrict` | 16 | 16 | 14 | 15 | 17 |
| `TotalDwellingUnits` | 1 | 1 | 1 | 1 | 1 |
| `TypeWaterFrontage` | No Water Frontage | No Water Frontage | No Water Frontage | No Water Frontage | No Water Frontage |
| `ZoningAll` | SR-C1 | SR-C1 | SR-V2 | PD | TR-C4 |
| `StreetDir` |  |  | S | N |  |
| `StreetName` | Sudbury | Hackney | STONE CREEK | Westfield | Harding |
| `StreetType` | Way | Way | Cir | Rd | St |
| `MaxConstructionYear` | 0 | 0 | 0 | 0 | 0 |
| `XCoord` | 845000 | 845000 | 790000 | 785000 | 835000 |
| `YCoord` | 490000 | 490000 | 460000 | 485000 | 490000 |
| `Shape__Area` | 9699.856852740546 | 9217.66956330629 | 514941.7362779518 | 10365.019789514441 | 5980.0308084769595 |
| `Shape__Length` | 408.2349339575416 | 397.98788341026255 | 2893.39280076627 | 410.54176720788064 | 339.19078430488156 |

## Refresh

```sh
python3 scripts/fetch_samples.py madison_parcels
python3 scripts/build_data_dictionaries.py
```
