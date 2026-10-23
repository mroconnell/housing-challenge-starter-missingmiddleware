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

Fill in the exact commands a stranger would run. These three commands are what reviewers use to reproduce your tool, so they must work from a clean checkout. Use whatever tooling you like (Make, npm scripts, a justfile, shell scripts, or plain commands) — only the documented commands matter.

| Step  | Command                     | Notes |
| ----- | --------------------------- | ----- |
| Setup | `[e.g., pip install -r requirements.txt]` | Installs dependencies |
| Run   | `[e.g., python app.py]`     | Starts the tool |
| Test  | `[e.g., pytest]`            | Runs the automated tests |

If there any assumptions on the environment required to run these commands, list them explicitly. Submissions with complicated build processes should provide a Dockerfile as a convenience.

If your tool needs environment variables, copy `.env.example` to `.env` and fill in the values before running.

## Data

The planned baseline combines Census annual housing-stock estimates, ACS neighborhood housing characteristics, 2020 Census block housing counts, and the Building Permits Survey with Wisconsin parcel data. Local records will add detail where available. See the [data-source plan](data/DATA_SOURCES.md#project-data-plan-for-wisconsin) and [Project Plan](docs/PROJECT_PLAN.md).

Automated acquisition and preparation commands are still to be implemented. Do not commit raw or large datasets; follow [data/README.md](data/README.md). Record the exact releases and transformations used in [Data Provenance](docs/DATA_PROVENANCE.md).

## Documentation

- [Project Plan](docs/PROJECT_PLAN.md) — scope, two-part workflow, data strategy, and next milestones
- [MVP Execution Plan](docs/MVP_EXECUTION_PLAN.md) — sequential scenario MVPs, multi-agent work packages, self-checks, and step-by-step owner review gates
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
