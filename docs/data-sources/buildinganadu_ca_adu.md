# California ADU permits by city, 2012-2019 (BuildinganADU.com compilation of HCD data)

**Status:** Fetched (last fetch 2026-10-24)  
**Source id:** `buildinganadu_ca_adu`  
**Handbook listing:** Not in the handbook. Added for the historical California ADU series (AQ-017).

## Summary

| | |
|---|---|
| Publisher | Building an ADU (buildinganadu.com), compiled from California HCD reports |
| What it is | Annual ADU building permits by California city or county, 2012 through 2019. A public Google Sheet linked from https://www.buildinganadu.com/california-adu-charts. |
| Geography | Jurisdiction (city or county) as reported to HCD. The City and County of Los Angeles are separate rows. |
| Time coverage and update frequency | Annual, 2012-2019. A static compilation, not updated. |
| Units | ADU permits (count) per jurisdiction per year. |
| Access method | Google Sheet CSV export: https://docs.google.com/spreadsheets/d/10rb8p7DU379vQw9oeS_Z9dwK9F9c5ZBeTw09wQlvwQY/export?format=csv (no login). |
| License | No license stated. Cite BuildinganADU.com as compiler and California HCD as the upstream source. |
| Use in our model | Pre-2018 California ADU permit history, before the current HCD APR tables start (see hcd_apr). Descriptive baseline and pre-period for the ADU scenario. |
| Caveats | Third-party compilation, not an agency file. Early zeros are reported values, not proof of no construction. Permits only, no completions. For 2018-2019 prefer the HCD APR tables and keep both versions. Gray's California YIMBY report (Jan 2024) used a similar series; we have not reproduced its exact files. |

## Access details

- Endpoint used for the sample: `https://docs.google.com/spreadsheets/d/10rb8p7DU379vQw9oeS_Z9dwK9F9c5ZBeTw09wQlvwQY/export?format=csv&gid=0`
- Jurisdiction rows: 527
- Sums are over jurisdiction rows (our check against docs/ASSUMPTIONS_AND_QUESTIONS.md AQ-017). The last sample row is Los Angeles.

## Fields (9)

| Field | Type | Meaning |
|---|---|---|
| `Jurisdiction` | string |  |
| `2012` | int |  |
| `2013` | int |  |
| `2014` | int |  |
| `2015` | int |  |
| `2016` | int |  |
| `2017` | int |  |
| `2018` | int |  |
| `2019` | int |  |

Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.

## Statewide sums

Sum of 527 jurisdiction rows, by year. Compare with the table in docs/ASSUMPTIONS_AND_QUESTIONS.md (AQ-017).

| Year | ADU permits |
|---|---|
| 2012 | 158 |
| 2013 | 745 |
| 2014 | 728 |
| 2015 | 1,109 |
| 2016 | 1,269 |
| 2017 | 4,974 |
| 2018 | 8,900 |
| 2019 | 14,702 |

## Sample rows

First 3 of 6 rows in [`data/sample/buildinganadu_ca_adu.csv`](../../data/sample/buildinganadu_ca_adu.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 | Row 6 |
|---|---|---|---|---|---|---|
| `Jurisdiction` | ADELANTO | AGOURA HILLS | ALAMEDA | ALAMEDA COUNTY | ALBANY | LOS ANGELES |
| `2012` | 0 | 0 | 0 | 0 | 0 | 0 |
| `2013` | 0 | 0 | 0 | 1 | 0 | 15 |
| `2014` | 0 | 0 | 0 | 0 | 0 | 71 |
| `2015` | 0 | 0 | 0 | 0 | 0 | 97 |
| `2016` | 0 | 0 | 0 | 0 | 11 | 80 |
| `2017` | 0 | 4 | 6 | 3 | 9 | 2342 |
| `2018` | 0 | 6 | 0 | 10 | 17 | 4079 |
| `2019` | 0 | 7 | 26 | 21 | 23 | 6747 |

## Refresh

```sh
python3 scripts/fetch_samples.py buildinganadu_ca_adu
python3 scripts/build_data_dictionaries.py
```
