# Gate 5 UI contract: what the bundle builder should read

For the UI agent (owner of `ui/`, `scripts/build_ui_bundle.py` and `tests/test_ui_bundle.py`). Written 2026-10-26 by the model and data agent. The adopted outputs the Gate 4 bundle reads are **unchanged**. Gate 5 adds two sets of outputs: the unknown-rules switch and legislative districts. Method and checks: [MODEL_CHECKS.md](MODEL_CHECKS.md).

**Units (unchanged).**
- Permits = second-home permits at issuance (ADUs plus house-to-duplex conversions on lots with a home).
- Rates = permits per 1,000 one-unit detached homes per year.
- `path` is `lower` / `central` / `upper`, shown as "lower / central / strong adoption".
- The engine's `year` 1–5 = forecast years 2027–2031.

**Rebuild order:** `run_adu_model.py` → `run_unknown_rules_variants.py` → `build_district_allocation.py` → `run_gate5_checks.py` → `build_ui_bundle.py`.

## 1. Unknown-rules switch (screen 4, "How sure")

Offer three precomputed runs that share one `run_group_id`. Default: `like_restricted`, which is the adopted run and equals every number already in the bundle.

| `unknown_treatment` | Suggested switch label | `contract_enum` |
| --- | --- | --- |
| `like_restricted` | "Like places that restrict ADUs (adopted)" | replaces `sample_mix` (AQ-027) |
| `like_prohibited` | "Like places that prohibit ADUs" | `all_prohibited` |
| `like_benchmark` | "Like places that already allow ADUs as the bill would" | `all_compliant` |

Files:

| File | Grain | Columns to use |
| --- | --- | --- |
| `reference/adu_model_unknown_rules_statewide.csv` | variant × path, 2027–2031 | `run_group_id`, `run_id`, `unknown_treatment`, `adopted`, `label`, `path`, `baseline_units`, `additional_units`, `total_with_law`, `d_baseline_units`, `d_additional_units`, `d_total_with_law`, `x_rate_uncoded`, `uncoded_homes` (1,267,433), `state_homes` (1,839,569) |
| `reference/adu_model_unknown_rules_statewide_by_year.csv` | variant × path × year | `forecast_year`, `baseline_units`, `additional_units`, `total_with_law` |
| `reference/adu_model_unknown_rules_by_county.csv` | variant × county × path, 2027–2031 | `parent_county_id`, `homes`, `uncoded_homes`, `baseline_units`, `additional_units`, `total_with_law` |
| `reference/adu_model_unknown_rules_by_context.csv` | variant × context group × path, 2027–2031 | as for counties, keyed by `context_group` |
| `reference/adu_model_unknown_rules_by_area.csv` | variant × area (1,925), 2027–2031 | `area_id`, `homes`, `x_rate`, `uncoded`, `baseline`, `additional_lower`, `additional_central`, `additional_upper` |
| `data/processed/model_run/unknown_rules/results_long.parquet` | variant × area × path × year | the engine columns of `model_run/results_long.parquet`, plus `run_group_id`, `run_id`, `unknown_treatment` |
| `data/processed/model_run/unknown_rules/run_manifest.json` | run group | runs, input hashes, validation list |

**Text the screen should carry** (numbers from the statewide CSV, central, 2027–2031):
- "Places with uncoded rules hold 1,267,433 of 1,839,569 single-family homes (69%)."
- If they behave like prohibited places: baseline 418 instead of 605, addition 8,915 instead of 8,757, total with the law 9,334 instead of 9,361.
- If they behave like places that already allow ADUs: baseline 1,409, addition 8,072, total 9,481.
- "The law's addition moves opposite to the baseline, so the total with the law barely moves. From 2030 the three totals are equal."

**Checks to add in the bundle tests:**
- the `like_restricted` rows equal the adopted statewide, by-year and county figures;
- every variant's counties sum to its statewide row (they do, to within 10⁻¹² permits);
- lower ≤ central ≤ upper within each variant.

## 2. Legislative districts (screen 3 "Where", and the brief)

| File | Grain | Columns |
| --- | --- | --- |
| `reference/adu_model_by_assembly_district.csv` | district (1–99, plus `unallocated`) × path × `forecast_year` (`2027`…`2031`, `2027-2031`) | `level`, `district` (string), `district_label` ("Assembly District 12" / "Not allocated to a district"), `path`, `forecast_year`, `homes` (allocated single-family homes), `baseline_units`, `additional_units`, `total_with_law`, `baseline_per_1000_homes_per_year`, `additional_per_1000_homes_per_year` |
| `reference/adu_model_by_senate_district.csv` | district (1–33, plus `unallocated`) × path × `forecast_year` | same columns, `level` = `senate` |
| `reference/adu_model_district_crosswalk.csv` | area × Assembly district | `area_id`, `name`, `parent_county_id`, `assembly_district`, `senate_district`, `share`, `area_homes`, `homes_allocated`, `method`: for a details panel ("this district includes 28% of Madison's single-family homes") |
| `data/processed/districts/geo_assembly.geojson` | 99 polygons, WGS84, simplified to 150 m (189 KB) | properties `district` (int), `senate` (int) |
| `data/processed/districts/geo_senate.geojson` | 33 polygons (125 KB) | property `district` (int) |
| `data/processed/districts/allocation_checks.json` | checks | reconciliation gaps, block-weight checks, comparison with area weights |

**Rules for the screen.**
- **Reconciliation line.** Show it the way the county and municipality views do: districts plus the `unallocated` row sum to the Wisconsin total for the chosen path and year. The `unallocated` row is 0.0 in this run but must stay in the table and the sum, and must never be dropped silently.
- **Keep districts apart from counties and municipalities.** Districts are a separate geography switch (Assembly / Senate). Do not mix them with county or municipality fills.
- **Caveat** (under the map, in the details panel and in the brief): "District figures share each municipality's result by where its single-family homes are (2020 census blocks). They are not forecasts for any neighbourhood or lot." Districts have equal populations but very different numbers of single-family homes (5,147 to 46,412), so show the per-1,000-homes rate next to counts.
- **The unknown-rules switch does not apply to districts** in this run: district tables exist for the adopted run only. Grey the switch out, or say "adopted assumption", when the district view is on.
- **Outlines.** Great Lakes waters are already excluded from the district polygons. Inland lakes are inside them, as in the TIGER municipality layer.
- **Bundle checks.** Each Senate district equals the sum of its three Assembly districts (`senate` property, or `senate_district` in the crosswalk). Assembly and Senate both reconcile to `adu_model_statewide.csv` and `_by_year.csv` for every path and year.

## 3. Landing screen ("Wisconsin today")

No new files are needed. The Gate 4 bundle already has stock, occupancy/vacancy, mix and production with vintages. Six gaps are listed in [MODEL_CHECKS.md §3e](MODEL_CHECKS.md#3e-landing-screen-housing-health-indicators):
- the vacancy label (includes seasonal homes);
- an optional production rate of 9.0 permitted units per 1,000 housing units in 2025 (25,569 ÷ 2,840,960), with a different denominator from the ADU rate;
- ACS figures are 5-year periods, and PEP has no margin of error;
- the BPS `source_id`;
- no tenure or affordability indicator, and no composite score;
- year built is available.

`reference/gate5_housing_health.csv` lists each indicator with year, source and uncertainty.

## 4. Optional: Gate 5 evidence tables

If screens 4 and 5 or the brief want them, each is a small CSV in `reference/`:
- `gate5_trace.csv`: totals by current-law basis (observed / estimated = "Calculated" / assumed) × context;
- `gate5_context_contrast.csv` and `gate5_context_examples.csv`: urban, suburban, small-community and rural rates, with examples;
- `gate5_sensitivity_summary.csv`: unknown rules, groupings and response rates in one table;
- `gate5_pilot_multiplier_check.csv`: why the statewide figure is not a pilot multiplier;
- `gate5_model_drivers.csv`: home value, income and size effects on the statewide rate, plus `alloc_value_dev`, the home-value term that spreads the total across places (AQ-061: only that term differs place to place).
