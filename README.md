<!--
==============================================================================
HOW TO USE THIS TEMPLATE (delete this comment block once you've read it)

1. Click "Use this template" on GitHub to create your own PUBLIC repository. DONE
2. Read docs/REPO_SETUP_GUIDE.md and turn on the repository security settings (secret scanning, push protection, code scanning). These are settings, not files, so the template cannot enable them for you. DONE
3. Replace every [bracketed placeholder] below with your project's details.
4. Fill in the "Command contract" so anyone can set up, run, and test your tool with the exact commands you list.
5. Work through SUBMISSION_CHECKLIST.md before you submit.

This template is language-agnostic. Use Python, JavaScript, Go, R, or anything else. The files here are configuration and documentation only; nothing forces a particular language or framework on you.
==============================================================================
-->

# Missing Middleware

A state-level simulator for Wisconsin legislators and legislative aides to compare how pro-housing reforms, individually and in combination, could change housing supply over five years and explain those impacts in specific legislative districts. The planned tool connects a diagnostic map of existing housing and development opportunities to policy scenarios with explicit assumptions and ranges of possible outcomes.

## What this tool does

The project is in planning. The intended workflow has two parts:

1. **Configure My State:** use Census housing and permit data, Wisconsin parcels, transit access, and available local records to establish a baseline and investigate development opportunities.
2. **Model the Future:** compare a no-reform baseline with individual reforms and combinations addressing ADUs, transit-oriented density, and parking reduction, with statewide and district explanations. Development-fee reduction and missing middle remain additional candidates. An expanded economic-scenario layer is optional.

See the [Project Plan](docs/PROJECT_PLAN.md) for the data strategy, research milestones, and unresolved modeling choices. No policy scenarios are implemented yet.

## Command contract

The interactive tool is not built yet (it arrives at Gate 4). The data pipeline built so far runs from a clean checkout with these commands.

| Step  | Command | Notes |
| ----- | ------- | ----- |
| Setup | `bash scripts/setup.sh` | Installs Python dependencies into `.venv` with [uv](https://docs.astral.sh/uv/) (installs uv if missing) |
| Test  | `bash scripts/test.sh` | Offline unit tests of parsing, classification, matching, and contracts |
| Build statewide foundation | `uv run python scripts/build_foundation.py` | Downloads about 270 MB of public Census files (no API key) into `data/raw/` and builds `data/processed/foundation/` |
| Build Madison permits | `uv run python scripts/build_madison_permits.py --fetch` | About 40 minutes the first time; omit `--fetch` to rebuild from cache |
| Build comparison-city permits | `uv run python scripts/build_comparison_permits.py --fetch` | Pleasant Prairie and Sun Prairie; about 11 minutes the first time |
| Rebuild local ADU rule tables | `uv run python scripts/build_reference_rules.py reference reference data/processed/adu_mention_scan` | Needs `uv run python scripts/scan_adu_mentions.py` first (network) |
| Gate 2 review map | `uv run python scripts/build_gate2_review_map.py` | Writes `data/processed/review/gate2_map.html`; needs the builds above |
| Run | to be defined at Gate 4 | |

Environment: macOS or Linux with Python 3.12+ and internet access for the build steps. No secrets are required. `pdftotext` (poppler) is only needed for the optional Howard fallback adapter.

If your tool needs environment variables, copy `.env.example` to `.env` and fill in the values before running.

## Data

The planned baseline combines Census annual housing-stock estimates, ACS neighborhood housing characteristics, 2020 Census block housing counts, and the Building Permits Survey with Wisconsin parcel data. Local records will add detail where available. See the [data-source plan](data/DATA_SOURCES.md#project-data-plan-for-wisconsin) and [Project Plan](docs/PROJECT_PLAN.md).

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

[List team members. All contributors must agree to the license and the challenge's [Official Rules](https://housingchallenge.turnout.rocks/rules.html).]
