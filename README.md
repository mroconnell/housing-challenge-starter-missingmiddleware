# Missing Middleware

An interactive tool for Wisconsin legislators and legislative aides that estimates how three statewide housing reforms could change housing permitted over 2027–2031, compared with current law: an accessory dwelling unit (ADU) law, parking requirement reduction and transit-oriented density (TOD). Pick a reform in the header. Each reform has its own outcome and evidence ([Model & Assumptions Overview](docs/MODEL_AND_ASSUMPTIONS.md); [Policy Scenario Comparison](docs/POLICY_SCENARIO_COMPARISON.md)); the ADU section below describes the ADU reform. Headlines, 2027–2031:
- **ADU:** 8,757 additional second-home permits (5,538 to 16,889), on a 605-permit current-law baseline.
- **Parking reduction:** 0 additional permitted homes in the central case and 29,662 at the high end of the evidence, on a 122,619-home all-housing baseline.
- **TOD:** 2,509 additional permitted homes near major transit stops in the typical case (171 to 17,148), on a 14,464-home near-stop baseline.

The three results are not added together: they overlap (TOD homes are part of the all-housing count, and the ADU law already removes parking requirements for ADUs).

## What the tool does: the ADU reform

The tool runs locally in a web browser and shows the adopted Gate 3 model ([Gate 3 packet](docs/gate3/README.md)); the browser runs no model, it reads a precomputed bundle.

**Outcome.** Second-home permits at issuance on lots that already have a single-family home: ADUs plus single-family-to-duplex conversions. They are not completed homes, and every result is for an area, never for a lot. A rate is permits in a year ÷ thousands of one-unit detached homes (Wisconsin has 1,839,569, ACS 2020–2024).

**Headline (model output, 2027–2031, law in effect 1 January 2027, stylized).** All numbers are second-home permits summed over the five years 2027–2031, statewide; the source of truth is [`reference/adu_model_statewide.csv`](reference/adu_model_statewide.csv) (adopted run, AQ-043 in [ASSUMPTIONS_AND_QUESTIONS.md](docs/ASSUMPTIONS_AND_QUESTIONS.md)).
- Under current law: **605** permits.
- Added by the law: **8,757** additional permits in the central scenario, **5,538** in the lower scenario and **16,889** in the strong adoption scenario. The scenarios show how much eight statewide-law states differ from one another; they are not statistical confidence intervals. How each input moves these numbers is in [`reference/adu_model_sensitivities.csv`](reference/adu_model_sensitivities.csv).

**Seven screens.**
1. **Wisconsin today:** housing units, single-family homes, vacancy (including seasonal homes), homes permitted and the production rate (9.0 per 1,000 housing units in 2025), housing mix, and, labelled separately, the ADU baseline and addition.
2. **Statewide comparison:** the modelled law, the three scenarios explained, annual and five-year permits, and the adoption reference line (8,851 permits over 2027–2031: the median observed path of the eight statewide-law states; [`reference/adu_model_reference_lines.csv`](reference/adu_model_reference_lines.csv)).
3. **Where:** county, municipality, Assembly-district and Senate-district map (area fills only) with a year slider, a details panel, and a searchable table that reconciles to the state.
4. **How sure:** how much of the addition rests on observed, calculated and assumed current-law rates, a switch for how places with uncoded local rules behave (three precomputed runs), the sensitivity analysis, robustness checks, and the strongest challenges.
5. **Why:** evidence and assumption cards with links to the write-ups, and the comparison-state charts.
6. **Pilot examples:** Madison, Pleasant Prairie and Sun Prairie: current rules with ordinance sections, observed permits, and the forecast.
7. **Brief:** a printable three-page summary.

Owner decisions carried into Gate 5: Madison alone keeps the observed path of Madison-like cities (so its rate with the law is below its suburbs') and is re-examined in December 2026, when its 2026 count is final; small, high-value villages keep their high rates (no cap). The Gate 5 decision packet is [docs/gate5/README.md](docs/gate5/README.md).

## Command contract

The Gate 4 interactive ADU tool runs locally with the first two commands below (Python 3.12+ and Node.js 20+). The committed JSON bundle in `ui/public/runs/` lets the tool run without the data builds; the build commands reproduce every input from public sources.

| Step  | Command | Notes |
| ----- | ------- | ----- |
| Setup | `bash scripts/setup.sh` | Installs Python dependencies into `.venv` with [uv](https://docs.astral.sh/uv/) (installs uv if missing) and the tool's npm packages in `ui/` |
| **Run the tool** | `bash scripts/run_tool.sh` | Rebuilds the JSON bundle from the adopted model outputs (when `data/processed/model_run/` exists), builds `ui/`, and serves it at http://127.0.0.1:4173/. If port 4173 is taken, set another: `PORT=4199 bash scripts/run_tool.sh` |
| Parking reform | (same command) | The tool has a reform picker in the header; the parking reform is at http://127.0.0.1:4173/#/parking/. Its full rebuild order is in [docs/parking/REBUILD.md](docs/parking/REBUILD.md). |
| TOD reform | (same command) | The TOD reform is at http://127.0.0.1:4173/#/tod/ (pick it in the header). Rebuild order: `fetch_tod_transit.py` → `build_tod_stops.py` → `fetch_tod_parcels_zoning.py` → `build_tod_station_areas.py` → `run_tod_model.py` → `run_tod_scale_check.py` → `run_tod_model.py` (again) → `build_tod_bundle.py` → `build_combined_bundle.py`, each as `uv run python scripts/<name>`. Optional evidence scripts: `run_tod_cases.py`, `run_tod_madison_test.py`, `run_ab2097_test.py`. |
| Test  | `bash scripts/test.sh` | Offline unit tests of parsing, classification, matching, and contracts, then the Python dependency licence check (`scripts/check_python_licenses.py`; fails on any licence outside the permissive allowlist, lists reviewed exceptions such as `certifi`, see [DISCLOSURES](docs/DISCLOSURES.md#dependency-licenses)) |
| Test the tool | `bash scripts/test_ui.sh` | Bundle tests (reconciliation, lower ≤ central ≤ upper, bundle = reference CSVs, missing ≠ 0), npm licence check, type check, build, and Playwright smoke tests (desktop and mobile Chromium). In a fresh clone one bundle test, `test_bundle_is_current`, is skipped: the bundle's run id is a hash of its 50 input files, and only a full rebuild with the data builds on disk (about 1.7 GB) can confirm that the committed bundle is current |
| Build the tool's data bundle | `uv run --all-extras python scripts/build_ui_bundle.py` | Writes `ui/public/runs/<run_id>/` (about 4.0 MB, 14 files) from `reference/adu_model_*.csv`, the unknown-rules and district tables, the baseline, coverage and rule tables and `data/processed/`; copies the simplified district outlines into the bundle; the run id is a hash of the inputs. Run it last in the Gate 5 rebuild order below |
| Gate 5 rebuild order (model side) | `uv run python scripts/fetch_legislative_districts.py` (once) → `uv run python scripts/run_adu_model.py` → `uv run python scripts/run_unknown_rules_variants.py` → `uv run python scripts/build_district_allocation.py` → `uv run python scripts/run_gate5_checks.py` | The fetch downloads the 2024 Assembly and Senate districts (LTSB) and the 2020 Census blocks (291 MB) into `data/raw/`. Then: the adopted run; the three unknown-rules runs; the district allocation; the Gate 5 self-check tables. Then rebuild the bundle (row above). See [docs/gate5/MODEL_CHECKS.md](docs/gate5/MODEL_CHECKS.md) |
| Develop the tool | `cd ui && npm run dev` | Live-reloading dev server at http://127.0.0.1:5173/ |
| Fetch map outlines | `bash scripts/fetch_map_outlines.sh` | Downloads the 2024 Census cartographic boundary files (about 13 MB, shoreline-clipped) that the map draws; needed only to rebuild the bundle |
| Build statewide foundation | `uv run python scripts/build_foundation.py` | Downloads about 270 MB of public Census files (no API key) into `data/raw/` and builds `data/processed/foundation/` |
| Build Madison permits | `uv run python scripts/build_madison_permits.py --fetch` | About 40 minutes the first time; omit `--fetch` to rebuild from cache |
| Build comparison-city permits | `uv run python scripts/build_comparison_permits.py --fetch` | Pleasant Prairie and Sun Prairie; about 11 minutes the first time |
| Rebuild local ADU rule tables | `uv run python scripts/build_reference_rules.py reference reference data/processed/adu_mention_scan` | Needs `uv run python scripts/scan_adu_mentions.py` first (network) |
| Build California BPS (comparison state) | `uv run python scripts/build_ca_bps.py` | Census BPS for California 2010–2025, for the California comparison study |
| Gate 2 review map | `uv run python scripts/build_gate2_review_map.py` | Writes `data/processed/review/gate2_map.html`; needs the builds above |
| Refresh the SBOM | `bash scripts/export_sbom.sh` | Exports GitHub's dependency-graph SBOM (SPDX 2.3 JSON, same as Insights → Dependency graph → Export SBOM) to [`sbom/sbom.spdx.json`](sbom/sbom.spdx.json); needs the GitHub CLI signed in |

Environment: macOS or Linux with Python 3.12+, Node.js 20+ for the tool, and internet access for the build steps. The Playwright tests use an installed Chromium (`cd ui && npx playwright install chromium` if none is present). No secrets are required. `pdftotext` (poppler) is only needed for the optional Howard fallback adapter.

If your tool needs environment variables, copy `.env.example` to `.env` and fill in the values before running.

## Data

The ADU tool uses Census housing estimates (ACS 2020–2024, Population Estimates Vintage 2025, Building Permits Survey 2015–2025), TIGER/Line 2024 areas and cartographic boundary files for the map, coded local ADU ordinances, city permit records for Madison, Pleasant Prairie and Sun Prairie, and permit series from eight states with statewide ADU laws. The map's lake-clipped outlines come from `data/raw/census_cb_2024/` (Census cartographic boundary files 2024, 1:500,000), fetched by `bash scripts/fetch_map_outlines.sh`. See the [data-source plan](data/DATA_SOURCES.md#project-data-plan-for-wisconsin) and [Project Plan](docs/PROJECT_PLAN.md).

Automated acquisition and preparation commands for the statewide foundation and pilot permits are listed in the command contract above. Do not commit raw or large datasets; follow [data/README.md](data/README.md). Record the exact releases and transformations used in [Data Provenance](docs/DATA_PROVENANCE.md).

## Documentation

- [Project Plan](docs/PROJECT_PLAN.md) — scope, two-part workflow, data strategy, and next milestones
- [MVP Execution Plan](docs/MVP_EXECUTION_PLAN.md) — sequential scenario MVPs, multi-agent work packages, self-checks, and step-by-step owner review gates
- [Challenge Handbook and Rules digest](docs/CHALLENGE_HANDBOOK.md) — key dates, deliverables, gates, and scoring in one place
- [Challenge Specification](docs/CHALLENGE_SPEC.md) — what to build and how it is scored
- [Model & Assumptions Overview](docs/MODEL_AND_ASSUMPTIONS.md) — how the tool works and what it assumes
- [Policy Scenario Comparison](docs/POLICY_SCENARIO_COMPARISON.md) — scenario ranking and drivers
- [Data Provenance](docs/DATA_PROVENANCE.md) — sources, licenses, and cleaning steps
- [Disclosures](docs/DISCLOSURES.md) — AI tools, pretrained models, and external services
- [Presentation Guide](docs/PRESENTATION_GUIDE.md) — slide deck and demo video guidance

## License

This project is licensed under the **Apache License 2.0** (see [LICENSE](LICENSE)), the challenge's recommended default because its express patent grant is the safest choice for tools that may later be adopted or integrated downstream.

The challenge also permits **MIT**, **BSD 3-Clause**, and **BSD 2-Clause**. If you choose one of these instead, replace the LICENSE file with the full text of your chosen license and update this section. Copyleft licenses (GPL, AGPL, LGPL, MPL, EUPL) and public-domain dedications (CC0, the Unlicense) are **not** permitted for submission code. Your dependencies must also be permissively licensed — see docs/DISCLOSURES.md.

## Team

**Missing Middleware**

- TODO (owner): list each team member's name and role here. All contributors must agree to the license and the challenge's [Official Rules](https://housingchallenge.turnout.rocks/rules.html).
