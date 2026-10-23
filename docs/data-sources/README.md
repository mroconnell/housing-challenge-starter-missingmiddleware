# Data source checklist

This folder has one data dictionary per source. The sources come from the "Data and Resources" section of the [Challenge Handbook](https://housingchallenge.turnout.rocks/handbook.html) and the state portal list in [data/DATA_SOURCES.md](../../data/DATA_SOURCES.md). Each page lists the fields, units, geography, update frequency, how to access the data, and a few sample rows.

Sample rows live in [data/sample/](../../data/sample/). They are small on purpose. The handbook says not to commit large source data, so the full datasets must be downloaded by our pipeline.

## How to refresh

```sh
python3 scripts/fetch_samples.py          # all sources (standard library only)
python3 scripts/build_data_dictionaries.py  # rewrite these pages
```

The **Fetch data samples** GitHub Actions workflow runs the same script and commits the results. Facts we wrote by hand (publisher, units, caveats) are in `scripts/source_catalog.py`.

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

