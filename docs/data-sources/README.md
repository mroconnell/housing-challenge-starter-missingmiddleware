# Data source checklist

This folder has one data dictionary per source. The sources come from the "Data and Resources" section of the [Challenge Handbook](https://housingchallenge.turnout.rocks/handbook.html) and the state portal list in [data/DATA_SOURCES.md](../../data/DATA_SOURCES.md). Each page lists the fields, units, geography, update frequency, how to access the data, and a few sample rows.

Sample rows live in [data/sample/](../../data/sample/). They are small on purpose. The handbook says not to commit large source data, so the full datasets must be downloaded by our pipeline.

## What the samples leave out

The samples are for learning the fields. They are not inputs for spatial work.

- The CSVs hold attributes only, and every cell is cut to 200 characters. Building footprint polygons in the CSVs are incomplete.
- For sources with geometry, a few complete features are saved separately in `data/sample/geo/` as GeoJSON. See the table below.
- Each sample has a few rows, not the full layer. Full layers need paging (ArcGIS `resultOffset`, up to the layer's max record count).

The modeling pipeline needs its own download step that keeps full geometry, gets every record, records the coordinate system, and checks joins. Asking for geometry does not add information a layer lacks: parcel points stay points, and building outlines do not give dwelling counts or zoning.

## How to refresh

```sh
python3 scripts/fetch_samples.py          # all sources (standard library only)
python3 scripts/build_data_dictionaries.py  # rewrite these pages
```

The **Fetch data samples** GitHub Actions workflow runs the same script and commits the results. Facts we wrote by hand (publisher, units, caveats) are in `scripts/source_catalog.py`.

## Data shape by source

Each source below also has a small GeoJSON file with a few complete features, so you can see the real geometry before picking a state. Parcel and housing-unit outlines are the exception: for privacy each one is replaced by a box on a 0.01-degree grid (about 1 km), and Avg vertices gives the source outline's count.

| Source | Geometry | Source CRS | Records | Max per request | Paging | Avg vertices | Sample |
|---|---|---|---|---|---|---|---|
| [Microsoft Global ML Building Footprints](ms_buildings.md) | Polygon | EPSG:4326 |  |  |  | 6 | [geojson](../../data/sample/geo/ms_buildings.geojson) |
| [Arizona: AZGeo Data Hub (parcels by county)](az_azgeo.md) | Polygon | EPSG:2868 | 142108 | 30000 | yes | 10 | [geojson](../../data/sample/geo/az_azgeo.geojson) |
| [Connecticut: CAMA and Parcel Layer](ct_cama_parcels.md) | Polygon | EPSG:6434 (Esri 103016) | 1320686 | 2000 | yes | 8 | [geojson](../../data/sample/geo/ct_cama_parcels.geojson) |
| [Oregon: Metro RLIS Taxlots (Portland region)](or_metro_taxlots.md) | Polygon | EPSG:2913 | 647192 | 2000 | yes | 12 | [geojson](../../data/sample/geo/or_metro_taxlots.geojson) |
| [Oregon: GEOHub parcels and zoning](or_geohub.md) | Polygon | EPSG:3857 (Esri 102100) | 114823 | 2000 | yes | 15 | [geojson](../../data/sample/geo/or_geohub.geojson) |
| [Hawaii: Statewide parcels](hi_parcels.md) | Polygon | EPSG:3750 (Esri 102202) | 384035 | 1000 | yes | 5 | [geojson](../../data/sample/geo/hi_parcels.geojson) |
| [Pennsylvania: PASDA county parcel layers (sample of counties)](pa_pasda_parcels.md) | Polygon | varies by county; see counties | 1279357 | 1000 | yes | 8 | [geojson](../../data/sample/geo/pa_pasda_parcels.geojson) |
| [Utah: Housing Unit Inventory](ut_housing_unit_inventory.md) | Polygon | EPSG:3857 (Esri 102100) | 702461 | 2000 | yes | 6 | [geojson](../../data/sample/geo/ut_housing_unit_inventory.geojson) |
| [Utah: Statewide parcels (LIR)](ut_parcels.md) | Polygon | not stated | 399432 | 2000 | yes | 8 | [geojson](../../data/sample/geo/ut_parcels.geojson) |
| [Virginia: VGIN statewide parcels](va_parcels.md) | Polygon | EPSG:3857 (Esri 102100) | 4174364 | 2000 | yes | 17 | [geojson](../../data/sample/geo/va_parcels.geojson) |
| [Wisconsin: Statewide parcel map (V-series)](wi_parcels.md) | Polygon | EPSG:3857 (Esri 102100) | 3574646 | 2000 | yes | 19 | [geojson](../../data/sample/geo/wi_parcels.geojson) |
| [Rhode Island: RIGIS land use](ri_rigis.md) | Polygon | EPSG:3438 (Esri 102730) | 26361 | 2000 | yes | 83 | [geojson](../../data/sample/geo/ri_rigis.geojson) |
| [New Hampshire: NH GRANIT parcels](nh_granit.md) | Point | EPSG:3437 (Esri 102710) | 617065 | 2000 | yes | 1 | [geojson](../../data/sample/geo/nh_granit.geojson) |
| [Wisconsin V12 statewide parcels](wi_v12_parcels.md) | Polygon | EPSG:3857 (Esri 102100) | 9835 | 2000 | yes | 19 | [geojson](../../data/sample/geo/wi_v12_parcels.geojson) |
| [Madison, WI: tax parcels](madison_parcels.md) | Polygon | EPSG:8193 (Esri 103412) | 82616 | 2000 | yes | 16 | [geojson](../../data/sample/geo/madison_parcels.geojson) |
| [Madison, WI: address points](madison_address_points.md) | Point | EPSG:8193 (Esri 103412) | 157222 | 2000 | yes | 1 | [geojson](../../data/sample/geo/madison_address_points.geojson) |
| [Madison, WI: zoning districts](madison_zoning.md) | Polygon | EPSG:8193 (Esri 103412) | 2473 | 2000 | yes | 20 | [geojson](../../data/sample/geo/madison_zoning.geojson) |
| [Wisconsin State Assembly districts (2024 plan)](wi_assembly_districts.md) | Polygon | EPSG:3857 (Esri 102100) | 99 | 2000 | yes | 2254 | [geojson](../../data/sample/geo/wi_assembly_districts.geojson) |

## National sources named in the handbook

| Done | Source | Status | Sample rows | Geography | Main caveat |
|---|---|---|---|---|---|
| [x] | [American Community Survey (ACS) 5-year estimates](acs.md) | Fetched | 5 | Nation, state, county, place, tract, block group (5-year). 1-year onl… | Estimates, not counts |
| [x] | [BLS construction employment (CES) and construction cost indexes (PPI)](bls_ces_ppi.md) | Fetched | 8 | National for the series sampled. CES also has state and metro series … | National cost indexes do not capture local cost differences |
| [x] | [BLS Quarterly Census of Employment and Wages (QCEW), construction](bls_qcew.md) | Fetched | 5 | Nation, state, MSA and county. | Cells are suppressed (disclosure_code = N) where few employers exist |
| [x] | [USGS National Land Cover Database (NLCD / Annual NLCD)](nlcd.md) | Fetched | 5 | Contiguous U.S. (Alaska, Hawaii and Puerto Rico have separate older p… | Raster, so it has no parcel or zoning boundaries |
| [x] | [NASA MODIS Land Cover Type (MCD12Q1)](nasa_modis_lc.md) | Fetched | 3 | Global, 500 m pixels. | 500 m pixels are much coarser than NLCD |
| [x] | [Microsoft Global ML Building Footprints](ms_buildings.md) | Fetched | 5 | Global, including all U.S. states. Files are split by zoom-9 quadkey … | ODbL is share-alike for derived databases |
| [x] | [Google Open Buildings](google_open_buildings.md) | Fetched | 5 | Africa, South and Southeast Asia, Latin America and the Caribbean. No… | Listed in the handbook but it does not cover any U.S. state |
| [x] | [Census Building Permits Survey (BPS)](census_bps.md) | Fetched | 10 | Nation, region, state, metro, county, and about 20,000 permit-issuing… | Permits are not completions; some permitted units are never built |
| [x] | [FHFA House Price Index (HPI)](fhfa_hpi.md) | Fetched | 5 | Nation, census division, state, metro (CBSA), county, ZIP3, 5-digit Z… | Single-family only; no condos or rents |
| [ ] | [HUD Aggregated USPS Administrative Data on Address Vacancies](usps_vacancy.md) | Restricted (not fetched) | 0 | Census tract. | Restricted access, so we did not fetch rows |
| [x] | [National Transit Database (NTD)](ntd.md) | Fetched | 5 | Transit agency (with city/state and urbanized area), by mode. | NTD has no stop or station locations |

## Added by the team

| Done | Source | Status | Sample rows | Geography | Main caveat |
|---|---|---|---|---|---|
| [x] | [California HCD Housing Element Annual Progress Report (APR) data](hcd_apr.md) | Fetched | 5 | Jurisdiction (city or county), with project address/APN in the projec… | California only |
| [x] | [California ADU permits by city, 2012-2019 (BuildinganADU.com compilation of HCD data)](buildinganadu_ca_adu.md) | Fetched | 6 | Jurisdiction (city or county) as reported to HCD. The City and County… | Third-party compilation, not an agency file |
| [x] | [Census annual housing-unit estimates (Population Estimates Program)](census_pep_housing_units.md) | Fetched | 6 | State and county. Sub-county PEP files have population only, not hous… | Net stock change, not gross new construction |
| [x] | [Census TIGER/Line boundaries (2024)](census_tiger.md) | Fetched | 5 | State, county, county subdivision, place, tract, block group (2020 tr… | Boundaries only, no housing counts |

## State open data portals (from data/DATA_SOURCES.md)

| Done | Source | Status | Sample rows | Geography | Main caveat |
|---|---|---|---|---|---|
| [x] | [Arizona: AZGeo Data Hub (parcels by county)](az_azgeo.md) | Fetched | 5 | Parcel, county by county. | No single statewide parcel layer |
| [x] | [Connecticut: CAMA and Parcel Layer](ct_cama_parcels.md) | Fetched | 5 | Parcel, statewide. | Zoning and land use codes are town-specific and not standardized. |
| [x] | [Oregon: Metro RLIS Taxlots (Portland region)](or_metro_taxlots.md) | Fetched | 5 | Parcel (tax lot), Portland metro only. | Portland region only, not statewide. |
| [x] | [Oregon: GEOHub parcels and zoning](or_geohub.md) | Fetched | 5 | Parcel / zoning district, incomplete county coverage. | Coverage is incomplete. |
| [x] | [Hawaii: Statewide parcels](hi_parcels.md) | Fetched | 5 | Parcel, statewide. | The statewide layer has parcel ids and shapes only |
| [x] | [Pennsylvania: PASDA (Pennsylvania Spatial Data Access)](pa_pasda.md) | Fetched | 10 | Mostly county. | A catalog, not a single dataset |
| [x] | [Pennsylvania: PASDA county parcel layers (sample of counties)](pa_pasda_parcels.md) | Fetched | 12 | Parcel, one county at a time. | Not homogeneous |
| [ ] | [Tennessee: Comptroller parcel data](tn_comptroller.md) | Manual request only (not fetched) | 0 | Parcel. 86 of 95 counties; the other 9 come from county assessors. | Each download needs a signed form, and the page says it offers no automated downloads |
| [x] | [Utah: Housing Unit Inventory](ut_housing_unit_inventory.md) | Fetched | 5 | Parcel / development, Wasatch Front counties. | Not every Utah county is covered. |
| [x] | [Utah: Statewide parcels (LIR)](ut_parcels.md) | Fetched | 5 | Parcel, one layer per county. | One layer per county |
| [x] | [Virginia: VGIN statewide parcels](va_parcels.md) | Fetched | 5 | Parcel, most localities. | Few attributes |
| [x] | [Wisconsin: Statewide parcel map (V-series)](wi_parcels.md) | Fetched | 5 | Parcel, statewide. | Values and classes come from local assessors and vary in quality. |
| [x] | [Rhode Island: RIGIS land use](ri_rigis.md) | Fetched | 5 | Land use polygons, statewide. | No statewide parcels or zoning. |
| [x] | [New Hampshire: NH GRANIT parcels](nh_granit.md) | Fetched | 5 | Parcel, partial statewide coverage. | Not every town is included |

## Wisconsin pilot sources (used by the pipeline)

| Done | Source | Status | Sample rows | Geography | Main caveat |
|---|---|---|---|---|---|
| [x] | [Madison, WI: building permit Construction Summary report](madison_permits.md) | Fetched | 5 | Street address. No parcel number or coordinates; the pipeline matches… | No ADU flag: ADUs come from keyword matching in descriptions |
| [x] | [Pleasant Prairie, WI: issued permits (SmartGov detail report)](pleasant_prairie_permits.md) | Fetched | 5 | Site address and Kenosha County parcel number (format NN-N-NNN-NNN-NN… | No dwelling-unit field: units are calculated from the permit type |
| [x] | [Sun Prairie, WI: submitted permits (Power BI report)](sun_prairie_permits.md) | Fetched | 5 | Street address and Dane County 12-digit parcel number, matched to V12… | Submission date only, no issue date; withdrawn, void and denied records add 0 units |
| [x] | [Wisconsin V12 statewide parcels](wi_v12_parcels.md) | Fetched | 5 | Parcel polygons; LATITUDE and LONGITUDE give a point. | No year built and no dwelling count |
| [x] | [Madison, WI: tax parcels](madison_parcels.md) | Fetched | 5 | Parcel. | Madison only |
| [x] | [Madison, WI: address points](madison_address_points.md) | Fetched | 5 | Address point. | Unit suffixes in permit addresses are free text, so some permits will not match. |
| [x] | [Madison, WI: zoning districts](madison_zoning.md) | Fetched | 5 | Zoning district polygon. | Zoning layers show districts, not what the code allows |
| [x] | [Wisconsin State Assembly districts (2024 plan)](wi_assembly_districts.md) | Fetched | 5 | State Assembly district. | Census geographies cross district lines, so district totals need an allocation method |

