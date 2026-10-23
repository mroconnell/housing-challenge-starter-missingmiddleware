# HUD Aggregated USPS Administrative Data on Address Vacancies

**Status:** Restricted (not fetched) (last fetch 2026-10-23)  
**Source id:** `usps_vacancy`  
**Handbook listing:** USPS vacancy data

## Summary

| | |
|---|---|
| Publisher | U.S. Department of Housing and Urban Development (from USPS) |
| What it is | Counts of residential and business addresses, and how many are vacant or 'no-stat', by census tract, each quarter. |
| Geography | Census tract. |
| Time coverage and update frequency | Quarterly. |
| Units | Address counts. |
| Access method | HUD USER portal, https://www.huduser.gov/portal/datasets/usps.html. Requires a registered login. |
| License | Restricted. HUD's terms limit access to governmental entities and registered non-profit organizations. |
| Use in our model | Would measure vacancy and new address growth at tract level (a proxy for completions). |
| Caveats | Restricted access, so we did not fetch rows. Access is restricted, and the handbook says not to use restricted-use data. Recommend not using it unless the team confirms eligibility and the rules allow it. Use ACS vacancy instead. |

## Access details

- Endpoint used for the sample: `https://www.huduser.gov/portal/datasets/usps.html`
- HUD/USPS vacancy data needs a HUD USER login and is limited to governmental entities and registered non-profits. Not fetched.

## Sample rows

None. See the status above. What we did find is in [`data/sample/usps_vacancy.meta.json`](../../data/sample/usps_vacancy.meta.json).


## Refresh

```sh
python3 scripts/fetch_samples.py usps_vacancy
python3 scripts/build_data_dictionaries.py
```
