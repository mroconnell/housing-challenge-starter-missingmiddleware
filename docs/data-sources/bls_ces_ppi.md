# BLS construction employment (CES) and construction cost indexes (PPI)

**Status:** Fetched (last fetch 2026-10-23)  
**Source id:** `bls_ces_ppi`  
**Handbook listing:** Bureau of Labor Statistics (construction employment, costs)

## Summary

| | |
|---|---|
| Publisher | U.S. Bureau of Labor Statistics |
| What it is | Monthly construction employment (Current Employment Statistics) and Producer Price Indexes (PPI) for construction inputs. Series sampled: CES2000000001 (all construction jobs), CES2023610001 (residential building construction jobs), WPUSI012011 (PPI, construction materials) and WPUIP2311001 (PPI, goods used in residential construction). |
| Geography | National for the series sampled. CES also has state and metro series (SMU prefix). |
| Time coverage and update frequency | Monthly. Released about the first Friday of the next month (CES) and mid-month (PPI). |
| Units | CES: thousands of employees. PPI: index (base period varies by series, 1982=100 for WPUSI012011). |
| Access method | BLS Public Data API v2, `POST https://api.bls.gov/publicAPI/v2/timeseries/data/` with a JSON list of series ids. No key needed for up to 25 series and 10 years; a free key raises limits. |
| License | Public domain (U.S. federal government work). |
| Use in our model | Cost growth assumptions for feasibility (fee and parking scenarios), and construction labor capacity as a ceiling on production. |
| Caveats | National cost indexes do not capture local cost differences. Recent months are preliminary and get revised. The PPIs measure input costs, not home sale prices; BLS has no new-home price index (Census publishes one). Series PCU236115236115 does not exist in the BLS API. |

## Access details

- Endpoint used for the sample: `https://api.bls.gov/publicAPI/v2/timeseries/data/ (POST)`

## Fields (7)

| Field | Type | Meaning |
|---|---|---|
| `seriesID` |  | BLS series id. CES = employment, WPU/PCU = producer price index. |
| `series_title` |  | Plain-language name of the series (added by our script). |
| `year` |  | Calendar year. |
| `period` |  | M01-M12 for months, M13 for annual average. |
| `periodName` |  | Month name. |
| `value` |  | Series value (thousands of jobs, or index points). |
| `footnotes` |  | P = preliminary, and other BLS notes. |

## Sample rows

First 3 of 8 rows in [`data/sample/bls_ces_ppi.csv`](../../data/sample/bls_ces_ppi.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 | Row 6 | Row 7 | Row 8 |
|---|---|---|---|---|---|---|---|---|
| `seriesID` | CES2000000001 | CES2000000001 | CES2023610001 | CES2023610001 | WPUSI012011 | WPUSI012011 | WPUIP2311001 | WPUIP2311001 |
| `series_title` | All employees, construction, US, seasonally adjusted (thous… | All employees, construction, US, seasonally adjusted (thous… | All employees, residential building construction, US, SA (t… | All employees, residential building construction, US, SA (t… | PPI: construction materials (index 1982=100) | PPI: construction materials (index 1982=100) | PPI: net inputs to residential construction, goods (index) | PPI: net inputs to residential construction, goods (index) |
| `year` | 2026 | 2026 | 2026 | 2026 | 2026 | 2026 | 2026 | 2026 |
| `period` | M09 | M08 | M09 | M08 | M09 | M08 | M09 | M08 |
| `periodName` | September | August | September | August | September | August | September | August |
| `value` | 8364 | 8353 | 922.7 | 919.7 | 378.610 | 375.792 | 355.225 | 348.930 |
| `footnotes` | preliminary | preliminary | preliminary | preliminary | Preliminary. All indexes are subject to monthly revisions u… | Preliminary. All indexes are subject to monthly revisions u… | Preliminary. All indexes are subject to monthly revisions u… | Preliminary. All indexes are subject to monthly revisions u… |

## Refresh

```sh
python3 scripts/fetch_samples.py bls_ces_ppi
python3 scripts/build_data_dictionaries.py
```
