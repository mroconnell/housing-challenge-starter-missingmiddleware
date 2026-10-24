# Census TIGER/Line boundaries (2024)

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `census_tiger`  
**Handbook listing:** Not in the handbook. Used by the Wisconsin foundation build.

## Summary

| | |
|---|---|
| Publisher | U.S. Census Bureau, Geography Division |
| What it is | Boundary shapefiles with identifiers. The pipeline uses the 2024 state, county, county subdivision, place, tract and block group files, plus the 2024 cartographic CBSA file for metro type. |
| Geography | State, county, county subdivision, place, tract, block group (2020 tracts and block groups). |
| Time coverage and update frequency | Annual vintages. 2024 boundaries are as of January 1, 2024. |
| Units | One polygon per geographic unit. ALAND and AWATER are square meters. |
| Access method | Zipped shapefiles under https://www2.census.gov/geo/tiger/TIGER2024/ (for example COUSUB/tl_2024_55_cousub.zip). CBSA: https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_cbsa_20m.zip. |
| License | Public domain (U.S. federal government work). |
| Use in our model | Join keys (GEOID) and boundaries for every Census table, and the municipality key for Wisconsin towns, villages and cities. |
| Caveats | Boundaries only, no housing counts. Match the boundary vintage to each statistical release, and document boundary changes before comparing years. |

## Access details

- Endpoint used for the sample: `https://www2.census.gov/geo/tiger/TIGER2024/COUSUB/tl_2024_55_cousub.zip`
- Total records at fetch time: 1925
- Projection (.prj): GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]
- Geometry: Polygon (in the .shp file; not sampled)
- Sample is Wisconsin county subdivisions (towns, cities, villages), the layer the pipeline uses as its municipality key. The same field pattern applies to the state, county, place, tract and block group files.

## Fields (16)

| Field | Type | Meaning |
|---|---|---|
| `STATEFP` | string | 2-digit state FIPS code (55 = Wisconsin). |
| `COUNTYFP` | string | 3-digit county FIPS code. |
| `COUSUBFP` | string | 5-digit county subdivision FIPS code. |
| `COUSUBNS` | string | GNIS identifier. |
| `GEOID` | string | Full identifier: state + county + county subdivision (10 digits). The pipeline's municipality id. |
| `GEOIDFQ` | string |  |
| `NAME` | string | Name without the type, for example Madison. |
| `NAMELSAD` | string | Name with the legal/statistical type, for example Madison city. |
| `LSAD` | string | Legal/statistical area description code (for example 25 = city, 43 = town, 47 = village). |
| `CLASSFP` | string | FIPS class code. |
| `MTFCC` | string | MAF/TIGER feature class code. |
| `FUNCSTAT` | string | Functional status (A = active government). |
| `ALAND` | number | Land area in square meters. |
| `AWATER` | number | Water area in square meters. |
| `INTPTLAT` | string | Latitude of the internal point. |
| `INTPTLON` | string | Longitude of the internal point. |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Sample rows

First 3 of 5 rows in [`data/sample/census_tiger.csv`](../../data/sample/census_tiger.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `STATEFP` | 55 | 55 | 55 | 55 | 55 |
| `COUNTYFP` | 123 | 123 | 123 | 123 | 123 |
| `COUSUBFP` | 14675 | 15675 | 16875 | 16900 | 19850 |
| `COUSUBNS` | 01582960 | 01582985 | 01583013 | 01583014 | 01583078 |
| `GEOID` | 5512314675 | 5512315675 | 5512316875 | 5512316900 | 5512319850 |
| `GEOIDFQ` | 0600000US5512314675 | 0600000US5512315675 | 0600000US5512316875 | 0600000US5512316900 | 0600000US5512319850 |
| `NAME` | Christiana | Clinton | Coon | Coon Valley | De Soto |
| `NAMELSAD` | Christiana town | Clinton town | Coon town | Coon Valley village | De Soto village |
| `LSAD` | 43 | 43 | 43 | 47 | 47 |
| `CLASSFP` | T1 | T1 | T1 | C5 | C5 |
| `MTFCC` | G4040 | G4040 | G4040 | G4040 | G4040 |
| `FUNCSTAT` | A | A | A | F | F |
| `ALAND` | 85994190 | 93049391 | 90379773 | 2885562 | 2409681 |
| `AWATER` | 227787 | 40689 | 4862 | 9239 | 0 |
| `INTPTLAT` | +43.6808804 | +43.6863925 | +43.6968244 | +43.7018929 | +43.4312436 |
| `INTPTLON` | -090.8460711 | -090.7407576 | -090.9779003 | -091.0114147 | -091.1970839 |

## Refresh

```sh
python3 scripts/fetch_samples.py census_tiger
python3 scripts/build_data_dictionaries.py
```
