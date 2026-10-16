# Challenge Handbook and Rules: Team Digest

This file is our team's plain-language digest of the official challenge documents. It is not a copy. The official documents are authoritative. Where this digest and the official documents differ, the official documents win.

- **Participant Handbook:** <https://housingchallenge.turnout.rocks/handbook.html>
- **Official Rules:** <https://housingchallenge.turnout.rocks/rules.html>
- **Technical spec in this repo:** [CHALLENGE_SPEC.md](CHALLENGE_SPEC.md)
- **Last checked against the official pages:** 2026-10-16

The Official Rules prevail over the Handbook if the two conflict. The rules say the Sponsor and Administrator can change them at any time (Rules 22), so recheck the official pages before key milestones.

## Key dates (all times Eastern)

| Milestone | Date |
| --------- | ---- |
| Registration Period | 9:00 a.m. Sep 14, 2026 to 9:00 a.m. Oct 7, 2026 (closed) |
| Team roster becomes final | Oct 7, 2026 |
| Coding Period opens | 9:01 a.m. Oct 14, 2026 |
| **Submission Deadline** | **11:59 p.m. Dec 16, 2026** |
| Judging Period | Dec 16, 2026 to Jan 30, 2027 |
| Demo round notice (top five) | On or about Jan 18, 2027 |
| Demo round (remote) | Jan 20, 2027 |
| Challenge Period ends | Jan 30, 2027 |
| Winners announced | On or about February 2027 |

Late submissions are not accepted.

## Eligibility and teams (Rules 2, 4, 5, 10)

- Each participant must be a US resident, 18 or older as of Sep 14, 2026, with a US bank account for the whole Challenge Period.
- A team has 1 to 5 participants. Each person may be on one team. Each team makes one submission.
- The roster was locked at the end of registration. Later changes need exceptional circumstances and Administrator approval.
- The Team Leader represents the team, receives messages, submits, and receives any prize money.
- Only team members may build the submission. Mentors and other non-members may give guidance only.
- People tied to the Sponsor (Arnold Ventures), the Administrator (The Turnout), judges, mentors, and their families are not eligible. Each participant handles any employer or university obligations.

## What we must build (Handbook; Rules 7)

- A functional, interactive tool (web app, notebook, or similar). A mockup does not count.
- State-level results. Smaller geographies are fine if they add up to the state.
- A baseline plus at least three of the five benchmark scenarios, over a five-year horizon:
  1. **ADUs:** one ADU per single-family parcel; detached or semi-detached ADUs of at least 600 sq ft; no extra parking.
  2. **Missing Middle:** 2 to 6 units on single-family parcels, up to three stories.
  3. **Transit-Oriented Density:** more height or FAR near major transit stops. We must define "major transit stop" and justify the distance. Parking may be reduced or removed.
  4. **Parking Reduction:** reduce or remove minimum parking. State what parking developers would still build.
  5. **Development Fee Reduction:** cut total fees by 50%, assuming fees total $50,000 per unit.
- We must define and justify the housing outcome we model (permits, starts, completions, or stock growth).
- For each scenario: change against baseline, what drives it, sensitivity to key inputs, and what the model cannot tell policymakers.
- The work must be original and made during the challenge, except for disclosed open-source parts and public data.

## Required deliverables (Rules 7(a), 7(d))

| # | Deliverable | Limit or format |
| - | ----------- | --------------- |
| 1 | Interactive tool | Must work, not a mockup |
| 2 | Slide deck | 30 slides or fewer, PDF |
| 3 | Demo video | 5 minutes or less, viewable without an account |
| 4 | Model & Assumptions Overview | 25 pages or fewer, single-spaced. Covers purpose, assumptions, data, methods, limitations, sensitivity, and intended users. See [MODEL_AND_ASSUMPTIONS.md](MODEL_AND_ASSUMPTIONS.md) |
| 5 | Source code | Public GitHub repo, OSI license, runnable by a third party from the docs |
| 6 | Policy Scenario Comparison | Non-technical, 4 pages or fewer, single-spaced. See [POLICY_SCENARIO_COMPARISON.md](POLICY_SCENARIO_COMPARISON.md) |
| 7 | Software Bill of Materials (SBOM) | Export from GitHub: Insights, then Dependency graph, then Export SBOM |

Also required: [DATA_PROVENANCE.md](DATA_PROVENANCE.md) and [DISCLOSURES.md](DISCLOSURES.md).

## How we submit (Rules 6, 7)

- Only the Team Leader submits, through a team-specific link sent at the start of the Coding Period.
- The repo must be public when reviewers look at it. Reviewers may check before the deadline.
- If a pre-deadline review finds a failed requirement, the Team Leader is told and can fix it before the deadline. Anything not fixed in time is disqualified.
- The rules do not say whether repo changes after the deadline count. Plan to freeze the repo at the deadline, and ask the Administrator if this matters.

## Eligibility gates (pass/fail before scoring)

A failed gate removes the submission from scoring.

1. **Reproducible setup:** the tool runs from the README commands on a clean checkout, with no hidden manual steps.
2. **Automated tests:** tests cover the core analytical logic, pass on a clean checkout, and have a documented run command.
3. **No committed secrets:** secret scanning is on, with zero open alerts.
4. **Security scanning:** Dependabot and CodeQL are on, with no unaddressed critical or high findings (or a written reason for each).
5. **OSI license:** Apache-2.0 (recommended), MIT, BSD-3-Clause, or BSD-2-Clause. Copyleft (GPL, AGPL, LGPL, MPL, EUPL) and public-domain dedications (CC0, Unlicense) are not allowed. Dependencies must also be permissively licensed.

The SBOM is the source of truth for dependencies. Flagged dependencies must be fixed, and any exceptions listed in the disclosures (Rules 7(b)(ii)).

## Scoring (Rules 8)

| Criterion | Weight |
| --------- | ------ |
| Transparency & Explainability | 30% |
| Replicability & Scalability | 25% |
| Usability | 20% |
| Methodological Soundness | 15% |
| Policy Insight & Interpretation | 10% |

- Judges have backgrounds in economics, planning, simulation modeling, and civic tech. They use a standard rubric.
- The top five go to a remote demo round: 15 minutes to present and demo, then 5 minutes of questions. The tool demo is the focus. Judges may change scores after the demo.
- Ties go to the higher Transparency & Explainability score.
- The top three after the demo round win: **$20,000**, **$12,000**, and **$6,000**.
- Teams in the demo round may be asked to sign a non-exclusive, non-commercial Sponsor License.

## Data rules (Rules 7(b)(iii); Handbook)

- The code license does not cover data. Each dataset keeps its own terms, and we must check them.
- Prefer datasets with no use restrictions. Paid or proprietary data is allowed only if access can continue and it stays free to end users.
- Do not commit large source datasets. The tool must fetch data automatically from the authoritative source, with minimal manual steps.
- Do not use sensitive, confidential, restricted-use, or personally identifiable data.
- For each dataset, record the source, version, access date, license, cleaning steps, and limitations.
- Suggested public sources include Census ACS, the Census Building Permits Survey, BLS, FHFA HPI, USPS vacancy data, the National Transit Database, USGS NLCD, building footprint datasets, and state and local open data portals. See also [data/DATA_SOURCES.md](../data/DATA_SOURCES.md).

## AI use and disclosure (Rules 7(c), 8)

- AI-assisted development is allowed and is not penalized.
- We must disclose AI coding tools, pretrained models, external APIs and services, and all third-party code, dependencies, and datasets, with their licenses.
- We must be able to explain, test, and secure everything we submit. Code that cannot be verified, explained, or reproduced scores lower.

## Language and tooling (Handbook)

- The Handbook asks for a memory-safe language. [CHALLENGE_SPEC.md](CHALLENGE_SPEC.md) lists Python, JavaScript, Go, and R as examples.
- If a required tool (for example CodeQL) does not support our language, document the gap.

## Ownership and publicity (Rules 11, 12)

- The team decides ownership among its members. Open source does not transfer ownership.
- Entering grants the Sponsor and Administrator a non-exclusive, royalty-free license to use the submission to run and judge the challenge.
- Entering also allows promotional use of names, hometowns, team and project names, and the submission. Winners may appear in a public gallery or report.

## Disqualification (Rules 6, 9, 10, 22)

- Missing the deadline or leaving a failed requirement unfixed.
- Breaking the rules or the law, tampering, harassment, or other unfair conduct.
- Not providing requested license agreements or documents.
- A prize can be forfeited if the Team Leader misses a step (for example the W-9) or a member is found ineligible.

## Support and contacts

- Weekly mentor office hours, webinars, and a matchmaking channel on the Challenge Platform (Rules 4).
- Questions: housing.challenge@turnout.rocks (Rules 24).

## Open questions to confirm with the Administrator

- Which SBOM file format (SPDX or CycloneDX) is expected, and where it should go.
- Whether repo changes after the deadline are ignored or count against us.
