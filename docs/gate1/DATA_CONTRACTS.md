# Gate 1: Statewide-Compatible Data Contracts (ADU)

Prepared 2026-10-23. Status: **proposal for owner review**. These are the tables every pipeline stage reads and writes. The pilot and the statewide run use the same tables; the pilot simply has more rows marked *observed*.

## Conventions shared by all tables

- **Two status vocabularies, used consistently everywhere:** every *value* is `observed` (taken from a source), `calculated` (derived by a documented rule), or `assumed` (a transferred or chosen parameter), stored in a `*_status` column. Every *legal or evidence claim* is `verified`, `source_lead`, or `unknown`.
- **Missing is not zero:** missing values are null with a `missing_reason` (`not_reported`, `not_collected`, `not_matched`, `not_yet_audited`). A zero means a source reported zero.
- **Provenance:** every row carries `source_id` (key into the source register) and `source_vintage`. Runs carry a manifest (below).
- **Identifiers:** Census GEOIDs for statistical areas; `wi_muni_id` = Census county subdivision GEOID (10 digits, state+county+cousub) for cities, villages, and towns, with a crosswalk for municipalities spanning counties; parcels use the V12 `STATEID`.
- **Privacy:** owner names and mailing addresses are never loaded. Record-level permit addresses stay in the local raw-data area (git-ignored) and are only used to match to parcels and areas. Published outputs are area aggregates.
- **Format:** Parquet or CSV for tables, GeoJSON/GeoParquet for geometry, one directory per run under `data/processed/<run_id>/` (git-ignored); small fixtures under `tests/fixtures/`.

## 1. `areas`

| Field | Type | Notes |
| --- | --- | --- |
| area_id | string | GEOID or `muni:<wi_muni_id>` |
| level | enum | state, county, municipality, tract, block_group, grid_cell |
| name | string | |
| parent_ids | list | county and municipality containing the area, where nested |
| boundary_source_id, boundary_vintage | string | e.g. TIGER 2024 |
| land_area_sqm | number | |
| context_group | enum | urban / suburban / small community / rural, rule documented at Gate 2; used for grouping and pooling |
| population | number | latest PEP or ACS, labeled |

## 2. `source_register`

One row per dataset version: source_id, publisher, URL, version/vintage, access date, license/terms, access method, checksum, and the acquisition script. Feeds `docs/DATA_PROVENANCE.md`.

## 2a. `state_conditions` (landing screen; per area and year)

Defined indicators only, no composite score.

| Field | Type | Notes |
| --- | --- | --- |
| area_id, year | string, int | state and counties; municipalities where published |
| indicator | enum | housing_units (PEP), occupied_units, vacant_units, vacancy_rate, units_1_detached, units_1_attached, units_2_4, units_5_plus, mobile_home (ACS B25024), permitted_units_total, permitted_units_1unit, permitted_units_2_4, permitted_units_5plus (BPS) |
| value, moe | number | MOE for ACS; null otherwise |
| period_type | enum | annual, acs_5yr (period stated), point_in_time |
| status, source_id, source_vintage | | as above |
| reporting_coverage | number or null | BPS: share of places reporting (reported vs imputed) |

## 3. `inventory` (per area)

| Field | Type | Notes |
| --- | --- | --- |
| area_id | string | |
| homes_1unit_detached, homes_1unit_detached_moe | number | **control total** from ACS B25024 (the denominator for all rates) |
| parcel_proxy_count | integer or null | parcel or assessor count used only to allocate within the area |
| parcel_to_acs_ratio | number or null | reported by county so proxy bias is visible |
| total_housing_units | number | PEP or ACS, labeled |
| method_note | string | allocation method; the parcel proxy rule is set at Gate 2 after checking it against assessor data |
| missing_reason | enum or null | |

## 4. `policy_rules` (per jurisdiction and provision, historical versions kept)

| Field | Type | Notes |
| --- | --- | --- |
| rule_id | string | stable |
| jurisdiction_id | string | `wi_muni_id`, county, or `state:WI` |
| provision | enum | detached_allowed, attached_allowed, owner_occupancy, occupant_restriction, min_lot_size, max_size_sqft, parking_required, approval_type, other |
| value | string/number | coded value |
| effective_from, effective_to | date or null | passage, effective, operative, and local implementation dates kept as separate fields when they differ |
| source_url, source_section, retrieved | string, date | |
| verification | enum | verified / source_lead / unknown |

## 5. `rights_exposure` (per municipality and scenario)

| Field | Type | Notes |
| --- | --- | --- |
| jurisdiction_id, scenario_id | string | scenario variants include `adu_full` and `adu_form_only` (decision D1) |
| current_class | enum | prohibited, restricted, compliant, no_zoning, unknown |
| reform_class | enum | same vocabulary plus forms_with_occupancy_limits (form-only variant); equals current_class where the reform adds nothing |
| class_basis | enum | coded_verified, coded_source_lead, imputed_from_sample, not_found |
| rules_as_of | date | ordinance version date; current law frozen at 2026-10-31 |
| rights_added_text | string | plain-language list of rights the reform adds here, e.g. "detached ADUs; removes related-occupant rule" |
| rule_ids | list | links to `policy_rules` |

## 6. `permits_observed` (record level, local only; never published)

| Field | Type | Notes |
| --- | --- | --- |
| record_key | string | hashed source permit id |
| jurisdiction_id | string | |
| stage | enum | application, approval, issued, finaled/completed, expired, withdrawn |
| stage_date | date | one row per stage, so stages stay distinct |
| unit_category | enum | adu_detached, adu_attached, adu_conversion, adu_legalization, other_residential |
| classification_method | enum | structured_field, text_rule, manual_review |
| units_added | integer or null | |
| parcel_stateid, area_id | string | after matching |
| match_method | enum | parcel_id, address_exact, address_normalized, geocode, unmatched |
| match_quality | enum | confirmed, probable, ambiguous; tolerances (address normalization rules, geocode distance) are fixed in the Gate 2 plan before match rates are evaluated |
| source_id | string | |

Published derivative: `permits_by_area_year` (area_id, year, unit_category, units, coverage flag, `suppressed` when an *observed* count is below the disclosure threshold recorded in run_manifest). Modeled values are never suppressed; they are rounded and labeled.

## 7. `parameters`

| Field | Type | Notes |
| --- | --- | --- |
| param_id | string | e.g. r_compliant, r_restricted, r_prohibited, r_forms_with_occupancy_limits, r_no_zoning, ramp_y1 |
| low, central, high | number | units stated |
| units | string | e.g. "authorized ADU units per 1,000 one-unit detached homes per year" (a level, not an increment) |
| applies_to | string | rights class, context group, or all |
| evidence_ids | list | links to evidence records (POLICY_EVIDENCE_MAP) |
| evidence_type | enum | descriptive, quasi-experimental, transferred, judgment |
| version | string | |

## 8. `scenario_results`

| Field | Type | Notes |
| --- | --- | --- |
| run_id, scenario_id | string | baseline is its own scenario_id |
| area_id, year | string, int | forecast years 2027–2031 plus bridge year 2026 flagged |
| path | enum | lower, central, upper |
| homes_1unit_detached | number | inventory control total, repeated for display |
| unit_category | enum | adu_new (detached + attached) or adu_conversion; legalizations never appear here |
| baseline_units | number | authorized ADU units under current law |
| baseline_basis | enum | observed_rate / class_rate / ramping_after_recent_reform |
| additional_units | number | reform minus baseline, same path |
| additional_units_verified, additional_units_estimated | number | split by whether the area's rights are verified or estimated; sum to additional_units |
| homes_verified_share | number | share of one-unit detached homes in municipalities with verified rights |
| rights_basis | enum | verified / estimated / mixed (for aggregates) |
| unallocated | boolean | true for the explicit state remainder row |
| unallocated_reason | enum or null | no_inventory, boundary_mismatch, unmatched_permits, other |

Display values are whole units with ranges; fractional per-area values are internal only.

Invariant checks: areas plus unallocated rows sum to the state row for every year and path; the reform case equals the baseline and additional_units is exactly 0 wherever reform_class equals current_class, including where the baseline uses an observed rate; lower ≤ central ≤ upper; cumulative totals never decrease.

## 9. `coverage_ledger` (per municipality)

| Field | Type | Notes |
| --- | --- | --- |
| jurisdiction_id | string | |
| inventory_status | enum | observed / calculated / missing |
| rights_verification | enum | verified / source_lead / unknown |
| rights_checked_on | date or null | |
| permit_coverage | enum | record_level / bps_aggregate_only / none |
| permit_years | string | e.g. "2016-2025" |
| assumed_params | list | param_ids that are transferred or assumed for this jurisdiction |
| confidence | enum | higher / moderate / low, rule documented |

Drives the coverage map and the "how much rests on assumptions" display.

## 9a. `sensitivity_results`

run_group_id, param_id (or unknown_treatment variant), low/high setting, resulting state five-year additional units, and swing versus central. Feeds the "what drives the range" view.

## 10. `run_manifest`

run_id, run_group_id (links precomputed variants), run date, model version (git commit), scenario definitions, parameter version, unknown_treatment (sample_mix / all_compliant / all_prohibited), disclosure threshold for observed counts, analysis dates (last observed year, effective date, forecast years), every source_id and vintage used, limitations text, and the validation results for that run.
