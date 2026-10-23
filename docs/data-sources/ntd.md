# National Transit Database (NTD)

**Status:** Fetched (last fetch 2026-10-23)  
**Source id:** `ntd`  
**Handbook listing:** National Transit Database

## Summary

| | |
|---|---|
| Publisher | Federal Transit Administration |
| What it is | Ridership, service, and agency data reported by U.S. transit agencies. |
| Geography | Transit agency (with city/state and urbanized area), by mode. |
| Time coverage and update frequency | Monthly ridership series and annual reports. |
| Units | Unlinked passenger trips, vehicle revenue miles and hours, dollars. |
| Access method | Socrata open data on https://data.transportation.gov (SODA API, `/resource/{id}.json`). Also https://www.transit.dot.gov/ntd. |
| License | Public domain (U.S. federal government work). |
| Use in our model | Which agencies and modes have frequent, high-ridership service, for the transit-oriented density scenario. |
| Caveats | NTD has no stop or station locations. Station locations need GTFS feeds or the BTS National Transit Map (https://data-usdot.opendata.arcgis.com). |

## Access details

- Endpoint used for the sample: `https://data.transportation.gov/resource/8bui-9xvu.json`
- Dataset: Complete Monthly Ridership (with Adjustments and Estimates)
- Total records at fetch time: 372801
- Rows last updated: 2026-10-01

## Fields (18)

| Field | Type | Meaning |
|---|---|---|
| `ntd_id` | text | NTD agency id. |
| `legacy_ntd_id` | text | Deprecated form of NTD ID used prior to 2019 |
| `agency` | text | Transit agency name. |
| `mode_type_of_service_status` | text | Indicates whether a mode and type of service has ended (inactive) or is continuing (active) as recorded in the NTD at the time of publication of this file. |
| `reporter_type` | text | Full Reporter, Reduced Reporter, and so on. |
| `uace_cd` | text | Census urban area code the agency serves. |
| `uza_name` | text | Urbanized area name. |
| `mode` | text | Mode code: MB bus, HR heavy rail, LR light rail, CR commuter rail, DR demand response, and others. |
| `tos` | text | Type of service: DO directly operated, PT purchased transportation. |
| `_3_mode` | text | Mode group: Bus, Rail, Ferry, Other. |
| `date` | calendar_date | Month of the observation. |
| `upt` | number | Unlinked passenger trips (boardings) in the month. |
| `voms` | number | Vehicles operated in maximum service. |
| `vrh` | number | Vehicle revenue hours. |
| `vrm` | number | Vehicle revenue miles. |
| `agency_mode_tos_date` | text | Unique row identifier derived by concatenating agency, mode, TOS, UZA, status, reporter type and date columns. |
| `state` | text | State of the agency. |
| `fta_region` | text | The FTA region in which the reporter is located. |

## Related NTD table: 2022 - 2025 NTD Annual Data - Stations and Facilities (by Mode and Age)

Station and facility counts by agency and mode, useful for the transit scenario. API: `https://data.transportation.gov/resource/wfz2-eft6.json`.

| Field | Type | Meaning |
|---|---|---|
| `agency` | text | The transit agency's name. |
| `city` | text | The city in which the agency is headquartered. |
| `state` | text | The state in which the agency is headquartered. |
| `ntd_id` | text | A five-digit identifying number for each agency used in the current NTD system. |
| `organization_type` | text | Description of the agency's legal entity. |
| `reporter_type` | text | The type of NTD report that the agency completed this year. |
| `report_year` | text | The year for which the data was reported. |
| `uace_code` | text | UACE Code remains consistent across census years. |
| `uza_name` | text | The name of the agency's Urbanized Area. |
| `primary_uza_population` | number | The population of the urbanized area primarily served by the agency. |
| `agency_voms` | number | The number of revenue vehicles operated across the whole agency to meet the annual maximum service requirement. This is the revenue vehicle count during the pe… |
| `modes` | text | Modes served by a given facility. |
| `facility_type` | text | Brief description of facility purpose. |
| `pre1940` | number | Count of a certain facility type in the era before the 1940s. |
| `_1940s` | number | Count of a certain facility type in the 1940s. |
| `_1950s` | number | Count of a certain facility type in the 1950s. |
| `_1960s` | number | Count of a certain facility type in the 1960s. |
| `_1970s` | number | Count of a certain facility type in the 1970s. |
| `_1980s` | number | Count of a certain facility type in the 1980s. |
| `_1990s` | number | Count of a certain facility type in the 1990s. |
| `_2000s` | number | Count of a certain facility type in the 2000s. |
| `_2010s` | number | Count of a certain facility type in the 2010s. |
| `_2020s` | number | Count of a certain facility type in the 2020s. |
| `total_facilities` | number | Total count of a facility type. |

## Sample rows

First 3 of 5 rows in [`data/sample/ntd.csv`](../../data/sample/ntd.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.

| Field | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 |
|---|---|---|---|---|---|
| `ntd_id` | 00001 | 00001 | 00001 | 00001 | 00001 |
| `legacy_ntd_id` | 0001 | 0001 | 0001 | 0001 | 0001 |
| `agency` | King County | King County | King County | King County | King County |
| `mode_type_of_service_status` | Active | Active | Active | Active | Active |
| `reporter_type` | Full Reporter | Full Reporter | Full Reporter | Full Reporter | Full Reporter |
| `uace_cd` | 80389 | 80389 | 80389 | 80389 | 80389 |
| `uza_name` | Seattle--Tacoma, WA | Seattle--Tacoma, WA | Seattle--Tacoma, WA | Seattle--Tacoma, WA | Seattle--Tacoma, WA |
| `mode` | DR | DR | DR | DR | DR |
| `tos` | PT | PT | PT | PT | PT |
| `_3_mode` | Bus | Bus | Bus | Bus | Bus |
| `date` | 2002-01-01T00:00:00.000 | 2002-02-01T00:00:00.000 | 2002-03-01T00:00:00.000 | 2002-04-01T00:00:00.000 | 2002-05-01T00:00:00.000 |
| `upt` | 135144 | 127378 | 136030 | 142204 | 144697 |
| `voms` | 574 | 574 | 574 | 574 | 574 |
| `vrh` | 53306 | 46865 | 51889 | 52674 | 53306 |
| `vrm` | 746158 | 656324 | 726578 | 736975 | 746158 |
| `agency_mode_tos_date` | 00001_DR_PT_Active_Full Reporter_80389_2002-01-01 | 00001_DR_PT_Active_Full Reporter_80389_2002-02-01 | 00001_DR_PT_Active_Full Reporter_80389_2002-03-01 | 00001_DR_PT_Active_Full Reporter_80389_2002-04-01 | 00001_DR_PT_Active_Full Reporter_80389_2002-05-01 |
| `state` | WA | WA | WA | WA | WA |
| `fta_region` | 10 | 10 | 10 | 10 | 10 |

## Refresh

```sh
python3 scripts/fetch_samples.py ntd
python3 scripts/build_data_dictionaries.py
```
