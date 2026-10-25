# Oregon: Metro RLIS Taxlots (Portland region)

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `or_metro_taxlots`  

## Summary

| | |
|---|---|
| Publisher | Oregon Metro (Regional Land Information System) |
| What it is | Tax lots for the three Portland-area counties (Multnomah, Washington, Clackamas). |
| Geography | Parcel (tax lot), Portland metro only. |
| Time coverage and update frequency | Updated quarterly. |
| Units | Dollars for values, square feet/acres for areas. |
| Access method | https://rlisdiscovery.oregonmetro.gov (free account for some downloads). ArcGIS item 9d3c396ffad44649bc7451465aa300f0. |
| License | See RLIS terms. |
| Use in our model | Parcel inventory for Portland metro. |
| Caveats | Portland region only, not statewide. |

## Access details

- Endpoint used for the sample: `https://services2.arcgis.com/McQ0OlIABe29rJJy/arcgis/rest/services/Taxlots_(Public)/FeatureServer/3`
- Layer: Taxlots  (Public)
- Total records at fetch time: 647192
- Last edited: 2026-08-26
- Item: Taxlots (Public) (owner `OregonMetro.RLIS`, id `b3cabe5845ec47eab61c54e0c631313c`)
- Geometry: esriGeometryPolygon

## Fields (32)

| Field | Type | Meaning |
|---|---|---|
| `TLID` | String | Tax lot id (map + lot number). |
| `PRIMACCNUM` | String | County assessor primary account number. |
| `ALTACCNUM` | String |  |
| `SITEADDR` | String | Site address. |
| `SITECITY` | String |  |
| `SITEZIP` | String |  |
| `BLDGSQFT` | Integer | Building square feet. |
| `A_T_ACRES` | Double | Assessor lot size, acres. |
| `YEARBUILT` | SmallInteger | Year built. |
| `PROP_CODE` | String | County property code. |
| `LANDUSE` | String | Metro land use class: SFR single-family, MFR multifamily, COM, IND, VAC vacant, and others. |
| `TAXCODE` | String |  |
| `SALEDATE` | String | Last sale, YYYYMM. |
| `SALEPRICE` | Integer | Last sale price, dollars. |
| `COUNTY` | String | M Multnomah, W Washington, C Clackamas. |
| `X_COORD` | Integer |  |
| `Y_COORD` | Integer |  |
| `JURIS_CITY` | String | City, or UNINCORPORATED. |
| `GIS_ACRES` | Double |  |
| `STATECLASS` | String | Oregon state property class code. |
| `ORTAXLOT` | String |  |
| `LANDVAL` | Double | Real market land value, dollars. |
| `BLDGVAL` | Double | Real market building value, dollars. |
| `TOTALVAL` | Double | Total real market value, dollars. |
| `ASSESSVAL` | Double | Assessed value for tax, dollars (capped by Measure 50, often below market). |
| `FID` | OID |  |
| `AREA` | Double |  |
| `HAS_MANY` | Single |  |
| `Shape__Area` | Double |  |
| `Shape__Length` | Double |  |
| `PUBLIC_OWN` | Integer | 1 if publicly owned. |
| `OWNERTYPE` | String | PRIVATE or a public owner type. |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Geometry sample

[`data/sample/geo/or_metro_taxlots.geojson`](../../data/sample/geo/or_metro_taxlots.geojson) has 3 features. For privacy each parcel or unit outline is replaced by its bounding box on a 0.01-degree grid (about 1 km across), so the file shows the layer's attributes and rough location but cannot locate a property. Attributes are masked the same way as the CSV. Coordinates are WGS84 longitude/latitude.

| | |
|---|---|
| Geometry type | Polygon |
| Source coordinate system | EPSG:2913 |
| Vertices per feature in the source | 5, 5, 26 |
| Max features per request | 2000 |
| Paging supported | yes |

## Sample rows

First 3 of 5 rows in [`data/sample/or_metro_taxlots.csv`](../../data/sample/or_metro_taxlots.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`. House and unit numbers are removed (street names kept), parcel and record ids are masked to their first 2 characters plus `***`, and coordinates are rounded.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `TLID` | 1N*** | 1N*** | 1N*** | 1N*** | 1N*** |
| `PRIMACCNUM` | R2*** | R2*** | R2*** | R2*** | R2*** |
| `SITEADDR` | NW 146TH TER | NW RIDGELINE ST | NW DAWNWOOD DR | NW LYNCH LN | NW SCOTTSDALE DR |
| `SITECITY` | PORTLAND | PORTLAND | PORTLAND | PORTLAND | BEAVERTON |
| `SITEZIP` | 97229 | 97229 | 97229 | 97229 | 97229 |
| `BLDGSQFT` | 2485 | 3649 | 1974 | 2582 | 2772 |
| `A_T_ACRES` | 0.09 | 0.11 | 0.11 | 0.09 | 0.14 |
| `YEARBUILT` | 2025 | 2023 | 1998 | 2014 | 2001 |
| `PROP_CODE` | 100 | 101 | 101 | 101 | 101 |
| `LANDUSE` | VAC | SFR | SFR | SFR | SFR |
| `TAXCODE` | 052.54 | 052.54 | 051.50 | 051.50 | 051.50 |
| `SALEDATE` | 202603 | 202605 | 202606 | 202606 | 202605 |
| `SALEPRICE` | 779999 | 1050000 | 680500 | 742000 | 740000 |
| `COUNTY` | W | W | W | W | W |
| `X_COORD` | 7605000 | 7605000 | 7605000 | 7600000 | 7600000 |
| `Y_COORD` | 705000 | 705000 | 700000 | 705000 | 695000 |
| `JURIS_CITY` | UNINCORPORATED | UNINCORPORATED | UNINCORPORATED | UNINCORPORATED | UNINCORPORATED |
| `GIS_ACRES` | 0.09297543 | 0.11038921 | 0.11106264 | 0.08524383 | 0.14429924 |
| `STATECLASS` | 100 | 101 | 101 | 101 | 101 |
| `ORTAXLOT` | 34*** | 34*** | 34*** | 34*** | 34*** |
| `LANDVAL` | 342000 | 374100 | 365000 | 385670 | 365000 |
| `BLDGVAL` | 0 | 775500 | 294530 | 420060 | 370500 |
| `TOTALVAL` | 342000 | 1149600 | 659530 | 805730 | 735500 |
| `ASSESSVAL` | 184540 | 601280 | 304060 | 490410 | 498360 |
| `AREA` | 4050.0096 | 4808.5541 | 4830.89323 | 3713.22129 | 6286.23329 |
| `HAS_MANY` | 0 | 0 | 0 | 0 | 0 |
| `Shape__Area` | 4050.009765625 | 4808.5537109375 | 4835.1796875 | 3713.22119140625 | 6289.50390625 |
| `Shape__Length` | 269.99959252148966 | 296.35536703797237 | 279.04110422977624 | 268.42201754942545 | 315.67779809452895 |
| `PUBLIC_OWN` | 0 | 0 | 0 | 0 | 0 |
| `OWNERTYPE` | PRIVATE | PRIVATE | PRIVATE | PRIVATE | PRIVATE |

## Refresh

```sh
python3 scripts/fetch_samples.py or_metro_taxlots
python3 scripts/build_data_dictionaries.py
```
