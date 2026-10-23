# Gate 1: Interface Workflow Review (ADU MVP)

Prepared 2026-10-23 by the interface/review agent. Status: **proposal for owner review**. Checks the state-first workflow against the legislative audience and the judging rubric (transparency 30, replicability 25, usability 20, method 15, policy insight 10). The owner's mockups (`adu-mockup-*.png`, `adu-map-*.png`) were reviewed as design references only; their numbers and curves are invented.

## 1. Screen flow

Order: **Wisconsin today → statewide ADU comparison → where → how sure → why → pilot drill-down → brief.** Every screen shares one frame:

- Header: breadcrumb `Wisconsin › County › Municipality`; the first screen is always Wisconsin.
- Status strip (always visible): `Model vX.Y · run <run_id> · last observed year 2025 · forecast 2027–2031 · reform effective 2027-01-01 · data vintages ↗`. Replaces the mockup's "Concept preview" banner once real runs exist; keep the yellow banner wording for any run whose manifest flags illustrative parameters.
- Status pills on every number: **Observed** (grey), **Calculated** (blue outline), **Assumed** (amber outline). Missing shows an em dash plus reason, never 0.
- Footer: "Outcome: ADU units authorized by issued building permits. Not completions, not stock growth. Results are for areas, never individual lots."

| # | Screen | Legislator's question | Quantities shown (labels) | Uncertainty and status placement |
| --- | --- | --- | --- | --- |
| 1 | **Wisconsin housing today** (landing) | What is the state of housing in Wisconsin, and where is it heading under current law? | Four indicator tiles, each with period and source: *Housing units* (PEP, latest vintage, annual series 2015–2025); *Occupied / vacant share* (ACS 5-yr, e.g. 2020–2024, with MOE); *Housing mix* (1-unit detached, attached, 2–4, 5+, mobile; ACS B25024); *Homes permitted per year* (BPS 2015–2025, units not permits). Below: "Current-law ADU baseline 2027–2031" and "With ADU reform" summary pair, with a link to screen 2. No composite score, no index, no ranking. | MOE shown as ± next to ACS values; BPS note "permit-issuing places only; coverage N% of municipalities". Each tile carries its status pill and vintage. ADU summary shows central with lower–upper and the share resting on verified rules. |
| 2 | **Statewide ADU comparison** | If we pass this, how many extra ADUs would be permitted statewide in five years, and how sure are we? | Three separated tiles: *Existing eligible single-family lots* (calculated); *Baseline 2027–2031* (central, lower–upper); *Additional from reform 2027–2031* (central, lower–upper). Chart: annual bars 2015–2025 observed ADU permits where known (partial coverage flagged) then 2027–2031 projected; cumulative line for baseline and reform with shaded lower–upper band; vertical rule at 2027-01-01. Provisions panel listing the three benchmark rights and "what it adds compared with current rules" statewide (share of lots gaining each right). | Range tile links to "What drives the range": table of parameters (uptake, ramp, unknown-rules treatment) with low/central/high and the state-total swing for each. Tile subtitle "x% of this estimate rests on verified local rules; y% on estimated rules" with link to screen 4. |
| 3 | **Where: counties and municipalities** | Where does it happen, and does the breakdown add up to the state number? | Choropleth (county, then municipality) plus the same data as a sortable table: eligible lots, baseline, additional (central and range), additional per 1,000 eligible lots, current rights class, rights basis (verified/estimated), permit coverage flag. Totals row and an explicit **Unallocated** row reconcile to screen 2. Optional grouping by context (urban/suburban/rural) and by rights class. | Map legend: 5 classes max; hatched fill for "rules unknown" and "inventory missing"; no graduated symbols or points. Row-level range shown as text "12 (6–20)". A "reconciles ✓" check line under the table shows sum + unallocated = state. |
| 4 | **How sure: coverage and confidence** | How much of this rests on verified facts, and what happens if the unknowns go the other way? | Stacked bar: additional units from verified-rule municipalities vs estimated-rule municipalities vs unallocated. Map of rights verification (verified / source lead / unknown) and permit-data coverage (record-level / aggregate / none). Switch for unknown-rules treatment (sample distribution — default / all permissive / all restrictive) with the resulting state total. List of the ten unknown municipalities with the most eligible lots (the audit priority list). | This is the uncertainty screen; everything on it is labelled by status. Default switch position matches the run manifest; the other positions are precomputed variants, not live edits. |
| 5 | **Why: evidence and assumptions** | Why these numbers, and could I defend them in committee? | Parameter cards (definition, units, low/central/high, evidence type, source links, version). Policy rule register for the pilots and any verified municipality (provision, value, effective date, source section, retrieved date). Source register (publisher, vintage, license, access date). Validation results for this run (invariants passed, back-test notes). Known limitations in plain language. | Evidence type pill (descriptive / quasi-experimental / transferred / judgment). Transferred evidence (California, Portland) is labelled "used for the uptake *range*, not scaled by ratio to Wisconsin". |
| 6 | **Pilot drill-down** (Madison, New Berlin; later any municipality with data) | What does this look like in a place I know? | Rules card: current ADU rules with dates and source; which benchmark rights are new here (share of new rights, plain words). Observed ADU permits by year and category (or "no usable record — audit pending"). Same three tiles as screen 2 for the municipality. Area map (tracts or fixed cells) with three toggleable layers: existing eligible lots (observed/calculated), baseline growth, additional growth; year slider 2027–2031; cell panel with rounded values and ranges. | Cell values rounded to whole units with range ("4–9 additional"); cells below a disclosure threshold show "fewer than 5" and hatch. Footer "no lot-level predictions" retained. Pilot results are never summed into a Wisconsin figure. |
| 7 | **Exportable brief** | Can I take this to a hearing without the team? | Two-page PDF/Markdown: headline (central and range), what the reform changes, where (top counties plus unallocated), coverage share, three biggest drivers, limitations, sources with vintages and licenses, run id, model version, generation date. District version added in a later cycle. | Range and status language carried verbatim; the brief embeds the same reconciliation line as screen 3. |

Navigation rule: screens 2–5 are tabs under Wisconsin; screen 6 is reached by clicking a municipality on screen 3 or from a "Pilot examples" link; the breadcrumb always returns to the state view.

## 2. Mockup critique

**Keep.** The three separated tiles (baseline / with reform / additional); the three map layers (existing, baseline growth, additional growth) with a year slider; the dashed-baseline chart legend; the evidence cards with source status ("audit pending", "source identified"); the persistent outcome footer; the plain-language tab names; the mobile single-column stacking; the "What drives the range?" link; the explicit "Permits, not completed homes" line.

**Conflicts and fixes.**

| Issue | Where | Fix |
| --- | --- | --- |
| City-first framing: study-area dropdown defaults to New Berlin/Madison; the first headline is a city result | all mockups | Landing is Wisconsin (screen 1). Municipality choice moves to screen 3/6 behind a breadcrumb. Pilot pages carry "pilot example, not a statewide result". |
| "0 permitted ADU units under current law" shown as fact; New Berlin permits are unaudited | compare tiles, brief table | Render baseline as "0–1 (assumed, restrictive class)" or "no observed record — audit pending". A bare 0 appears only when a source reported zero. |
| Range "40–180" with no driver; "Scenario range" band unlabeled | tiles, chart | Label the band "lower–upper paths"; the range tile links to the driver table (screen 2). Show all three paths at once; drop the "Development response: Central assumption" dropdown that hides the range. |
| Point markers (circles) and green parcel fills read as lot predictions | adu-map-*.png | No point symbols on growth layers. Growth is area fill only (tracts/cells). Parcel outlines allowed only in the existing-inventory layer, labelled "existing homes". |
| Fractional cell values ("3.9 baseline", "+5.9") imply false precision | map cell panel | Whole units with range; disclosure threshold with hatching. |
| No coverage or verified-vs-estimated view anywhere | all | Screen 4; subtitle on the statewide tile. |
| "Apply benchmark reform" checkbox toggles the comparison away | compare panel | Baseline and reform always side by side; the checkbox goes. |
| X axis "Reform starts, Year 1–5" has no calendar | chart | Calendar years 2027–2031, observed history to the left, rule at the effective date. |
| California permit counts shown beside Wisconsin tiles | evidence tab | Keep, but in a "transferred evidence" card with the sentence from screen 5; never a ratio. |
| "7,000 newly eligible parcels" conflates eligibility with new rights | brief dot matrix | Label "lots gaining new rights under the benchmark" and show the share, not an invented count. |
| Esri/HERE basemap attribution | map | Licensing and reproducibility risk; see §4. |
| "Concept preview" banner carries no date or version | header | Becomes the status strip. |

## 3. Contract gaps (SCOPE_AND_MODEL.md, DATA_CONTRACTS.md)

The contracts cover screens 2, 3, 6 well. Gaps, in priority order:

> **Conductor note (rev 2, 2026-10-23):** items 1–10 below were incorporated into [DATA_CONTRACTS.md](DATA_CONTRACTS.md). Field names and enums in DATA_CONTRACTS govern (for example `state_conditions`, `unknown_treatment` = sample_mix / all_compliant / all_prohibited, and the rights classes prohibited / restricted / compliant / no_zoning / unknown). Mockup quantities remain illustrative; there is no observed statewide ADU permit series to chart.
>
> **Superseded by SCOPE_AND_MODEL rev 2** wherever this document says otherwise: (a) the model uses rights-class rates per one-unit detached home, not a "share of new rights" or ΔR; (b) modeled small-area values are rounded and labeled, never hidden, and only observed permit counts are suppressed; (c) screen 2 shows observed Census BPS total production for context, not an observed statewide ADU series; (d) example figures such as "120 (60–210)" and "12 (6–20)" are placeholders, not model output; (e) the unknown-rules switch reads "sample mix / all compliant / all prohibited"; (f) the effective date is shown as "stylized: reform effective at start of forecast year 1 (labeled 2027)".

1. **No statewide housing-conditions table** for screen 1. `inventory` holds only eligible lots and one total. Add `housing_indicators` (area_id, indicator_id, period_start, period_end, value, moe, status, source_id, source_vintage) covering PEP units by year, ACS occupancy/vacancy, ACS B25024 mix, BPS units by year, and BPS place coverage.
2. **Verified-vs-estimated share is not computable at state level.** `scenario_results.rights_basis` is per row, but the state row needs `additional_units_verified` and `additional_units_estimated` (or the UI must sum municipality rows every time). Add both to the state and county rows, plus `eligible_lots_verified_share`.
3. **Unallocated row has no reason.** Add `unallocated_reason` enum (inventory_missing, rights_unknown_excluded, permit_coverage, boundary_mismatch) and allow several rows.
4. **No `baseline_basis`.** Scope says Madison's baseline rate is observed and elsewhere assumed; `scenario_results` only has `rights_basis`. Add `baseline_basis` (observed / transferred / assumed).
5. **Unknown-rules treatment is not a run field.** Screen 4's switch needs `run_manifest.unknown_treatment` (sample_distribution / all_permissive / all_restrictive) and the precomputed variants to share a `run_group_id`.
6. **No sensitivity output.** "What drives the range" needs `sensitivity_results` (run_id, param_id, setting, state_additional_units, delta_vs_central).
7. **Dates are implicit.** Add `run_manifest.last_observed_year`, `reform_effective_date`, `forecast_years`, `generated_at`.
8. **`coverage_ledger` is prose.** Give it fields: jurisdiction_id, inventory_status, rights_verification, permit_coverage (record_level / aggregate / none), permit_years_from/to, assumed_param_ids, confidence_flag (enum with definitions), eligible_sf_lots (for the audit priority list).
9. **Plain-language rights text.** `rights_exposure` has `basis` (rule ids); screen 6 needs `rights_added_text` and per-provision new/not-new flags.
10. **Disclosure threshold** for tract/cell outputs: a `suppressed` boolean and the threshold in `run_manifest`; the handbook asks for a small-cell statement.
11. **`areas` lacks `context_group`** (urban/suburban/rural) and `population` (for per-capita display and the statewide transfer check).
12. **`permits_by_area_year.coverage` flag is undefined.** Give it the same enum as the ledger.
13. **Brief content.** Add `limitations` (list) and `scenario_definitions` fields (provision list, effective date) to `run_manifest` so the brief is generated from the run, not hand-written.
14. **Conversions/legalizations.** Scope counts conversions separately; `scenario_results` has no `unit_category`. Either add it or state that results are detached+attached only.

## 4. Usability, accessibility, and minimal tech

**Requirements.** WCAG 2.2 AA. Every chart and map has a table equivalent and a text summary ("Through 2031: about 120 additional units, range 60–210"). Keyboard: tabs, switches, year slider, table rows, and map areas (list fallback) reachable and operable; visible focus. Colour: baseline vs additional differ by hue and pattern (dashed/solid, hatched/solid); sequential map scale from a colour-blind-safe ramp (viridis or ColorBrewer), max 5 classes, grey hatch for unknown/suppressed; never red/green alone. Mobile: single column, tiles before charts, map replaced by the table under 600 px wide; text 16 px minimum; tap targets 44 px. Plain language: "single-family lots", "homes permitted", "share of new rights" (not ΔR), "lower/upper path" (not CI); glossary tooltips on every pill. Numbers: whole units, two significant figures over 100, ranges always beside centrals.

**Minimal stack (all permissive licences, local launch).** Python pipeline (pandas, GeoPandas, pyarrow; BSD/Apache) writes `data/processed/<run_id>/` plus a small `ui/public/runs/<run_id>/` JSON bundle (state, county, municipality, pilot tracts; a few MB). Static front end: Vite + Svelte or plain TypeScript (MIT), Observable Plot (ISC) for charts, MapLibre GL JS (BSD-3) with GeoJSON for 72 counties and municipalities, PMTiles (BSD-3) only if municipality geometry is too heavy. No basemap at state level; for pilots use OpenFreeMap or Protomaps vector tiles (ODbL data, attribution shown) or none. No live model in the browser: switches select precomputed variants, so the UI cannot drift from the Python results and the verification agent compares JSON to Parquet. Commands: `make setup` (pip + npm), `make run` (build bundle, serve on localhost), `make test` (pytest invariants: reconciliation, lower ≤ central ≤ upper, zero uplift where ΔR = 0, missing ≠ zero; Playwright smoke for keyboard and mobile viewport). Streamlit/Dash are acceptable fallbacks but make keyboard access and the static export harder.

## 5. Owner decisions requested

1. Confirm the screen order and that municipality selection lives behind the breadcrumb.
2. Approve removing point markers and the reform checkbox from the map and compare screens.
3. Accept contract additions 1–7 before Gate 2 acquisition starts (they change what the data agent must collect).
4. Confirm precomputed variants rather than a browser-side model.
5. Choose the pilot disclosure threshold (proposal: suppress cells with fewer than 5 projected units or fewer than 20 eligible lots).
