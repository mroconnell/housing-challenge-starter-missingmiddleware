# Oregon: Metro RLIS Taxlots (Portland region)

**Status:** Fetched (last fetch 2026-10-23)  
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

## Sample rows

First 3 of 5 rows in [`data/sample/or_metro_taxlots.csv`](../../data/sample/or_metro_taxlots.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 |
|---|---|---|---|
| `TLID` | 1N117AA08200 | 1N117BA03400 | 1N117DD13200 |
| `PRIMACCNUM` | R2223193 | R2221202 | R2073774 |
| `ALTACCNUM` |  |  |  |
| `SITEADDR` | 7813 NW 146TH TER | 15651 NW RIDGELINE ST | 14610 NW DAWNWOOD DR |
| `SITECITY` | PORTLAND | PORTLAND | PORTLAND |
| `SITEZIP` | 97229 | 97229 | 97229 |
| `BLDGSQFT` | 2485 | 3649 | 1974 |
| `A_T_ACRES` | 0.09 | 0.11 | 0.11 |
| `YEARBUILT` | 2025 | 2023 | 1998 |
| `PROP_CODE` | 100 | 101 | 101 |
| `LANDUSE` | VAC | SFR | SFR |
| `TAXCODE` | 052.54 | 052.54 | 051.50 |
| `SALEDATE` | 202603 | 202605 | 202606 |
| `SALEPRICE` | 779999 | 1050000 | 680500 |
| `COUNTY` | W | W | W |
| `X_COORD` | 7606079 | 7603502 | 7606042 |
| `Y_COORD` | 704755 | 704852 | 700646 |
| `JURIS_CITY` | UNINCORPORATED | UNINCORPORATED | UNINCORPORATED |
| `GIS_ACRES` | 0.09297543 | 0.11038921 | 0.11106264 |
| `STATECLASS` | 100 | 101 | 101 |
| `ORTAXLOT` | 3401.00N01W0700--00000 ROW | 3401.00N01W0700--00000 ROW | 3401.00N01W0700--00000 ROW |
| `LANDVAL` | 342000 | 374100 | 365000 |
| `BLDGVAL` | 0 | 775500 | 294530 |
| `TOTALVAL` | 342000 | 1149600 | 659530 |
| `ASSESSVAL` | 184540 | 601280 | 304060 |
| `FID` | 1 | 2 | 3 |
| `AREA` | 4050.0096 | 4808.5541 | 4830.89323 |
| `HAS_MANY` | 0 | 0 | 0 |
| `Shape__Area` | 4050.009765625 | 4808.5537109375 | 4835.1796875 |
| `Shape__Length` | 269.99959252148966 | 296.35536703797237 | 279.04110422977624 |
| `PUBLIC_OWN` | 0 | 0 | 0 |
| `OWNERTYPE` | PRIVATE | PRIVATE | PRIVATE |

## Refresh

```sh
python3 scripts/fetch_samples.py or_metro_taxlots
python3 scripts/build_data_dictionaries.py
```
