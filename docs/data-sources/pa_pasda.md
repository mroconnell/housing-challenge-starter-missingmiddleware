# Pennsylvania: PASDA (Pennsylvania Spatial Data Access)

**Status:** Fetched (last fetch 2026-10-23)  
**Source id:** `pa_pasda`  

## Summary

| | |
|---|---|
| Publisher | Penn State / PASDA |
| What it is | Catalog of state, county and municipal GIS datasets, including county parcels and some zoning. |
| Geography | Mostly county. |
| Time coverage and update frequency | Varies by dataset. |
| Units | Varies. |
| Access method | https://www.pasda.psu.edu (search, then download shapefiles per dataset). |
| License | Varies by publisher. |
| Use in our model | Find county parcel and zoning files for Pennsylvania. |
| Caveats | A catalog, not a single dataset. Sample rows are catalog entries. Parcel rows from 6 counties are in pa_pasda_parcels. |

## Access details

- Endpoint used for the sample: `https://www.pasda.psu.edu/uci/SearchResults.aspx?Keyword=parcels`
- PASDA is a catalog of county/municipal datasets (mostly shapefile downloads). Rows are catalog entries, not parcel records.

## Fields (3)

| Field | Type | Meaning |
|---|---|---|
| `dataset_id` |  |  |
| `title` |  |  |
| `summary_url` |  |  |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Sample rows

First 3 of 10 rows in [`data/sample/pa_pasda.csv`](../../data/sample/pa_pasda.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 | Row 6 | Row 7 | Row 8 | Row 9 | Row 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| `dataset_id` | 1918 | 1214 | 70 | 1695 | 2251 | 2037 | 1916 | 2652 | 2084 | 2653 |
| `title` | Adams County - Parcels | Allegheny County - Parcels | Allegheny County - Zip Codes | Bedford County - Parcels | Berks County - Parcels | Blair County - Parcels | Bradford County - Parcels | Bucks County - Owned Parcels | Bucks County - Parcels | Bucks County - Preserved Parcels |
| `summary_url` | https://www.pasda.psu.edu/uci/DataSummary.aspx?dataset=1918 | https://www.pasda.psu.edu/uci/DataSummary.aspx?dataset=1214 | https://www.pasda.psu.edu/uci/DataSummary.aspx?dataset=70 | https://www.pasda.psu.edu/uci/DataSummary.aspx?dataset=1695 | https://www.pasda.psu.edu/uci/DataSummary.aspx?dataset=2251 | https://www.pasda.psu.edu/uci/DataSummary.aspx?dataset=2037 | https://www.pasda.psu.edu/uci/DataSummary.aspx?dataset=1916 | https://www.pasda.psu.edu/uci/DataSummary.aspx?dataset=2652 | https://www.pasda.psu.edu/uci/DataSummary.aspx?dataset=2084 | https://www.pasda.psu.edu/uci/DataSummary.aspx?dataset=2653 |

## Refresh

```sh
python3 scripts/fetch_samples.py pa_pasda
python3 scripts/build_data_dictionaries.py
```
