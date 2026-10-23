# FHFA House Price Index (HPI)

**Status:** Fetched (last fetch 2026-10-23)  
**Source id:** `fhfa_hpi`  
**Handbook listing:** Federal Housing Finance Agency House Price Index (FHFA HPI)

## Summary

| | |
|---|---|
| Publisher | Federal Housing Finance Agency |
| What it is | Repeat-sales index of single-family home prices from Fannie Mae and Freddie Mac mortgages (and other sources for the all-transactions index). |
| Geography | Nation, census division, state, metro (CBSA), county, ZIP3, 5-digit ZIP and tract (annual developmental indexes). |
| Time coverage and update frequency | Monthly (purchase-only, nation/division), quarterly (state/metro), annual (county/ZIP/tract). |
| Units | Index values. Base period differs by file (for example 1991 Q1 = 100). Use changes over time, not levels across places. |
| Access method | CSV downloads listed at https://www.fhfa.gov/data/hpi/datasets. Master file holds all main series. |
| License | Public domain (U.S. federal government work). |
| Use in our model | Price growth feeds the feasibility side: higher price growth makes more projects pencil after a reform. |
| Caveats | Single-family only; no condos or rents. Indexes track change, not price levels. |

## Access details

- Endpoint used for the sample: `https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv`

## Fields (12)

| Field | Type | Meaning |
|---|---|---|
| `hpi_type` |  | traditional, distress-free, etc. |
| `hpi_flavor` |  | purchase-only, all-transactions, expanded-data. |
| `frequency` |  | monthly or quarterly. |
| `level` |  | Geography level (USA, State, MSA, Census Division...). |
| `place_name` |  | Geography name. |
| `place_id` |  | Geography id (state abbreviation, CBSA code...). |
| `yr` |  | Year. |
| `period` |  | Month or quarter number. |
| `index_nsa` |  | Index, not seasonally adjusted. |
| `index_sa` |  | Index, seasonally adjusted (where available). |
| `rstderr` |  |  |
| `note` |  |  |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Other FHFA HPI files found on the datasets page

- https://www.fhfa.gov/document/d/hpi/2025q1_hpi_technical_note_tables.xlsx
- https://www.fhfa.gov/document/d/hpi/2026m01_hpi_technical_note_expanded_indexes.xlsx
- https://www.fhfa.gov/document/d/hpi/hpi_dictionary.xlsx
- https://www.fhfa.gov/document/d/hpi/hpi_specifications.xlsx
- https://www.fhfa.gov/hpi/download/annual/hpi_at_cbsa.xlsx
- https://www.fhfa.gov/hpi/download/annual/hpi_at_county.xlsx
- https://www.fhfa.gov/hpi/download/annual/hpi_at_national.xlsx
- https://www.fhfa.gov/hpi/download/annual/hpi_at_state.xlsx
- https://www.fhfa.gov/hpi/download/annual/hpi_at_tract.csv
- https://www.fhfa.gov/hpi/download/annual/hpi_at_zip3.xlsx
- https://www.fhfa.gov/hpi/download/annual/hpi_at_zip5.xlsx
- https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv
- https://www.fhfa.gov/hpi/download/monthly/hpi_po_monthly_hist.xlsx
- https://www.fhfa.gov/hpi/download/monthly/hpi_po_monthly_nsa.xlsx
- https://www.fhfa.gov/hpi/download/monthly/hpi_po_monthly_sa.xlsx
- https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_3zip.xlsx
- https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_metro.csv
- https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_metro.txt
- https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_metro.xlsx
- https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_mh.xlsx
- https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_multid_metro.xlsx
- https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_nonmetro.xlsx
- https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_pr.xlsx
- https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_state.csv
- https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_state.txt
- https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_state.xlsx
- https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_state_vol.txt
- https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_state_vol.xlsx
- https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_us_and_census.csv
- https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_us_and_census.txt

## Sample rows

First 3 of 5 rows in [`data/sample/fhfa_hpi.csv`](../../data/sample/fhfa_hpi.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `hpi_type` | traditional | traditional | traditional | traditional | traditional |
| `hpi_flavor` | purchase-only | purchase-only | purchase-only | purchase-only | purchase-only |
| `frequency` | monthly | monthly | monthly | monthly | monthly |
| `level` | USA or Census Division | USA or Census Division | USA or Census Division | USA or Census Division | USA or Census Division |
| `place_name` | East North Central Division | East North Central Division | East North Central Division | East North Central Division | East North Central Division |
| `place_id` | DV_ENC | DV_ENC | DV_ENC | DV_ENC | DV_ENC |
| `yr` | 1991 | 1991 | 1991 | 1991 | 1991 |
| `period` | 1 | 2 | 3 | 4 | 5 |
| `index_nsa` | 100.00 | 100.87 | 101.32 | 101.73 | 102.32 |
| `index_sa` | 100.00 | 100.86 | 100.89 | 100.96 | 101.30 |

## Refresh

```sh
python3 scripts/fetch_samples.py fhfa_hpi
python3 scripts/build_data_dictionaries.py
```
