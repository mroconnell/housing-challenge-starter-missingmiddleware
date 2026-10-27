# Transit-oriented density: Gate 4 notes (the pilot in the tool)

Written 2026-10-27 by the TOD Gate 4 work package. Status: built, not yet reviewed. The reform stays `in_development` in `ui/src/scenarios/registry.json`; review it in preview mode at `#/tod/today?preview=1` (run `bash scripts/run_tool.sh`).

## Files

- `scripts/build_tod_bundle.py` writes `ui/public/scenarios/tod/runs/<run_id>/` (manifest, statewide, areas, map, howsure, why, pilots; about 0.2 MB) and `latest.json`. The run id hashes every input file; a rerun gives the same bytes; only the current run is kept. 23 validation checks are stored in the manifest.
- `ui/src/scenarios/tod/` (`index.ts`, `screens.ts`, `map.ts`, `types.ts`, `tod.css`), registered as `tod: todReform` in `ui/src/main.ts`.
- Tests: `tests/test_tod_bundle.py` (contract keys, run id = hash of inputs, numbers equal the reference CSVs, byte-identical rebuild, no parcel ids, under 5 MB) and `ui/tests/tod.spec.ts` (holding page without preview, every screen loads with no console errors, headline numbers equal the bundle, a11y structure on 11 screen states).

## What each screen shows and where its numbers come from

| Screen | Shows | Source (all via the bundle) |
| --- | --- | --- |
| Wisconsin today | Homes near qualifying stops (main case), current-law permits near stops 2027–2031 and their share of the statewide baseline, the definition ladder (narrowest to widest, "any stop" as context), the law's height and density by band, the qualifying transit systems | `tod_definition_summary.csv`, `tod_model_statewide.csv`, `housing_baseline_statewide_by_year.csv`, `tod_station_areas.csv` (law columns), `tod_stops.csv` |
| Statewide comparison | Timing caveat (G3-4) first; the three scenarios named by meaning with their evidence; chart and table by year, current law with its range, the reference line dotted | `tod_model_statewide.csv` |
| Where | Milwaukee metro, Madison metro and the rest of the state as one line; an SVG map of station areas (stops from `tod_stops.csv`, circles of ½ and ¼ mile, municipality outlines from the ADU bundle's `geo_munis.json`, rounded to about 100 m); a sortable table by place, county, Assembly and Senate district, with a scenario switch | `tod_model_by_area.csv`, `_by_county`, `_by_assembly_district`, `_by_senate_district`, `tod_near_stop_homes_by_muni.csv` |
| How sure | Sensitivities grouped by what they move (law's addition, where homes land, current law only); the per-acre sizing set aside; the scale check against each metro's own record; the Madison comparison (labelled not set in advance); the observed / calculated / assumed trace; what the model cannot tell | `tod_model_sensitivities.csv`, `tod_model_checks.csv`, `tod_scale_check.csv`, `tod_scale_check_metro_years.csv` |
| Why | The three net-effect studies; the Madison test (prediction against measured, with intervals, and rates by year 2017–2026); the comparison cases; the policy classification of 58 reforms | `tod_case_estimates.csv`, `tod_cases.csv`, `tod_madison_test_*.csv`; study texts from `docs/tod/research/NET_EFFECT_SOURCES.md` |
| Pilot examples | Milwaukee CONNECT 1 and Madison Rapid Route A corridors (stops, land, extra homes by year); Eau Claire with zero and the reason | as above, plus `tod_station_areas.csv` for the corridor land |
| Brief | One printable page with the same numbers and run id | as above |

**One new calculation, in the builder.** A corridor's extra homes are each place's modelled addition times the corridor's share of that place's placement measure. That measure is added floor area for Milwaukee and Madison (coded) and the estimated room for new homes for other places. It is the rule the model already uses to place homes, applied within a place. Milwaukee's figures cover CONNECT 1 and The Hop together, because the station-area bands do not separate them. Example: CONNECT 1 plus The Hop, typical response, 199 extra homes over 2027–2031, of which 142 are in Wauwatosa.

**Fixes after the independent check (2026-10-27).**
- TOD styles are now scoped, so ADU's sort headers are unchanged; a test checks this.
- The pilot land table shows three figures: acres, acres the law covers, and acres where it adds room (land with added floor area or estimated room above zero).
- Wording is plainer, and the classification table gives short reasons.
- The bundle keeps 4 decimals and rounds once on screen.
- Where explains places that get extra homes but have few homes near stops. It also lists places whose Census permit counts for 2021–2025 are very low: Wauwatosa reported 1, 2, 2, 1 and 2 new homes a year, none of them apartments.
- An unknown pilot slug shows a not-found message.

## Not done, or worth a look

- The map is a simple SVG with no basemap, made from stop points and municipality outlines. It is not maplibre. Station areas are drawn as circles around stops, not the model's census-block areas.
- No observed history of permits near stops, so the comparison chart starts in 2027.
- The policy classification is shown as rated in `tod_cases.csv`, not re-derived.
- Transit-line names on "Wisconsin today" and the study descriptions are text in the builder, taken from MAJOR_TRANSIT_STOP.md, TRANSIT_PIPELINE.md and NET_EFFECT_SOURCES.md.
- If the ADU bundle is rerun, its new `geo_munis.json` changes the TOD run id. The numbers stay the same.
- The suburbs placement (G3-2 amended) and the G3-3 reversal still await the owner's confirmation. The bundle follows the reference CSVs as committed.
