# Gate 5: Rubric Assessment and Compliance Check

Prepared 2026-10-26 by the compliance agent for the Gate 5 "Agent self-check" in [MVP_EXECUTION_PLAN.md](../MVP_EXECUTION_PLAN.md#gate-5--statewide-adu-mvp-and-the-good-enough-decision). The model checks (transfer, groupings, sensitivity) are in a separate file, `MODEL_CHECKS.md`, written by another agent.

**The internal ratings below are not predicted judging scores.** They are this team's own reading of its evidence against the published sub-criteria, on a 1–5 scale (1 = absent, 3 = adequate, 5 = hard to improve). Judges use their own rubric, which is not public.

## 1. Official materials: re-checked live

Fetched with `curl` on 2026-10-26.

| Page | HTTP | Size (bytes) | `Last-Modified` | Same as the 2026-10-23 check? |
|---|---|---|---|---|
| [handbook.html](https://housingchallenge.turnout.rocks/handbook.html) | 200 | 21,842 | Fri, 09 Oct 2026 21:08:09 GMT | Yes (same size and date) |
| [rules.html](https://housingchallenge.turnout.rocks/rules.html) | 200 | 46,847 | Fri, 09 Oct 2026 21:08:09 GMT | Yes |
| [index.html](https://housingchallenge.turnout.rocks/index.html) (landing page and FAQ, linked from the handbook) | 200 | 20,064 | Fri, 09 Oct 2026 21:08:09 GMT | Not recorded on 2026-10-23; date predates that check |

SHA-256 of the fetched files: handbook `e7702365…8d96`, rules `9b758867…e568c`, index `cebd916d…d389`. Future checks can compare against these.

Not fetched: the Challenge Platform (sign-in needed; holds the curated dataset list and the submission link), two SharePoint webinar recordings linked from the landing page (video), and the feedback form linked from the rules. Nothing in them was assumed.

**Result: nothing has changed since 2026-10-23** (and none of the pages has changed since 2026-10-09). The key terms, read again from the live text:

| Item | Live text says | Change? |
|---|---|---|
| Deadline | 11:59 pm ET, 16 December 2026 (Rules 3); no late submissions | None |
| Deliverables | Tool, deck (≤30 slides, PDF), demo video, Model & Assumptions Overview (≤25 pages, single-spaced, 7 topics), source code, Policy Scenario Comparison (≤4 pages, single-spaced), plus baseline + ≥3 of 5 scenarios aggregated to the state (Rules 7(a)); SBOM (Rules 7(d)) | None |
| Licence | Apache-2.0 (recommended), MIT, BSD-3-Clause, BSD-2-Clause only; no copyleft or public-domain dedications. Dependencies must be permissive; copyleft or unknown ones "must be flagged and resolved"; exceptions summarized in disclosures (Rules 7(b)) | None |
| SBOM | "export it from Insights → Dependency graph → Export SBOM. Use it to document your dependencies." No file format or location stated | None |
| Demo video | Rules 7(a): "no longer than five (5) minutes", viewable without an account. Handbook checklist and landing page say "5 minutes" / "five-minute"; the Rules prevail | None |
| Judging weights | 30 / 25 / 20 / 15 / 10 with the sub-criteria quoted in section 2 below; "less complete data" preference in Rules 8 | None |

## 2. Rubric assessment

Evidence is from the repository at commit `af3a5e2`, the committed bundle `adu-ecb5971cce`, and the Gate 4 screenshots (regenerated 2026-10-26 after AQ-043, [screenshots/](../gate4/screenshots/)). I viewed `2-compare-desktop.png` and `4-how-sure-desktop.png`; their numbers match AQ-043 (baseline 605, added 5,538 / 8,757 / 16,889, reference line 8,851). I did not start the server; CI and Gate 4 verification already cover the run path.

### Summary

| Criterion (weight) | Internal rating (1–5) | One-line reason |
|---|---|---|
| Transparency & Explainability (30%) | **3** | The tool explains itself very well; the required written companion (Model & Assumptions Overview) is still an empty template |
| Replicability & Scalability (25%) | **3** | Strong commands, tests, provenance; but security/dependency hygiene has an open high alert, an unflagged MPL dependency, no SBOM file, and no demonstrated transfer to another state |
| Usability (20%) | **4** | Clear seven-screen tool with plain language, labels and mobile layout; only one scenario to compare |
| Methodological Soundness (15%) | **4** | Evidence-anchored scenarios, sensitivity and hold-out checks, tests tied to outputs; Midwest transfer still unobserved |
| Policy Insight & Interpretation (10%) | **2** | Good ADU-only insight in the tool, but no cross-scenario comparison exists, and the Policy Scenario Comparison is a template |

Weighted internal average, for orientation only: 0.30×3 + 0.25×3 + 0.20×4 + 0.15×4 + 0.10×2 = **3.25 of 5**. This is not a forecast of judging.

### Transparency & Explainability (30%): 3

| Sub-criterion (Rules 8) | Evidence | Assessment |
|---|---|---|
| Assumptions, architecture, logic clearly defined | Tool tab 5 "Why" (5 evidence cards, 6 assumption cards with status); tab 2 "How each scenario is calculated"; [gate3/README.md](../gate3/README.md); [ASSUMPTIONS_AND_QUESTIONS.md](../ASSUMPTIONS_AND_QUESTIONS.md) AQ-001 to AQ-043; `reference/adu_model_params.json` | Strong in the tool and gate packets, but spread over many gate files |
| What data was available in the state, what was used | Tab 4 "How sure": 9% of single-family homes (161,026 ÷ 1,839,569) in places with observed rates, 22% calculated, 69% assumed; local rules coded for 43 of 1,925 areas | Strong on screen; no single written "data available in Wisconsin" section |
| Sources well-defined, retrievable; limitations communicated | [DATA_PROVENANCE.md](../DATA_PROVENANCE.md) (source, vintage, access date, licence per dataset); README build commands; "strongest challenges" on tab 4 | Strong |
| Sensitivity: how inputs affect outputs | Tab 4 tornado and three grouped tables (`reference/adu_model_sensitivities.csv`) | Strong |
| Interpretable for non-technical policymakers; **technical companion document provided** | Plain-language screens; printable brief (tab 7). **[MODEL_AND_ASSUMPTIONS.md](../MODEL_AND_ASSUMPTIONS.md) is the unfilled template (326 words, all `[bracketed prompts]`)** | The companion document, a required deliverable, is missing |
| Well-annotated models | Python module docstrings, `reference/wi_adu_rules_spec.py`; data dictionaries (`scripts/build_data_dictionaries.py`) | Adequate; not separately audited here |
| Team explains code, including AI-assisted code | **[DISCLOSURES.md](../DISCLOSURES.md) "AI-Assisted Code Generation" section is still the template prompt**; nothing says which AI tools wrote what | Missing |

Gaps, by impact: (1) write the Model & Assumptions Overview; (2) fill the AI-use disclosure and a short "how the code works" explanation; (3) add a written "what data Wisconsin has" section (the tool has it; the document should too).

### Replicability & Scalability (25%): 3

| Sub-criterion | Evidence | Assessment |
|---|---|---|
| Open-source licence and rationale | `LICENSE` is full Apache-2.0 text; GitHub detects `Apache-2.0`; README "License" gives the patent-grant rationale; `pyproject.toml` and `ui/package.json` declare Apache-2.0. **`NOTICE` still has `[Project name]` and `Copyright [yyyy] [team or author name]`** | Pass, with a placeholder to fix |
| Modular, documented code | `missing_middleware/` packages (foundation, permits, model, comparison, review), `scripts/` one per build step, `ui/` separate | Good |
| Clear data requirements; plug in alternative datasets | README command contract fetches every source; `contracts.py`; eight statewide-law states already run through the same pipeline as comparison data | Partial: **no documented "apply to another state" path**, which Rules 8 rewards ("states with less complete data") |
| Separation of assumptions from mechanics | `reference/adu_model_params.json` holds scenario parameters; engine in `missing_middleware/model` | Good |
| Meaningful tests beyond the gate | 320 Python tests (CI run 40290287371 on 2026-10-26: OK, 3 skipped); 13 Playwright tests in `ui/tests/smoke.spec.ts`; bundle reconciliation tests | Good. CI runs only `scripts/test.sh`; the UI tests (`test_ui.sh`) are not in CI |
| Single-command setup; CI | `bash scripts/setup.sh`, `bash scripts/run_tool.sh`; `.github/workflows/ci.yml` (green) | Good. `ci.yml` and `codeql.yml` still carry template comments and commented-out language jobs |
| Dependency hygiene: pinned, current, no unaddressed vulnerabilities | `uv.lock` and `ui/package-lock.json` pin everything; Dependabot alerts on, 0 open. **CodeQL: 1 open high alert** (`py/incomplete-url-substring-sanitization`, `scripts/scan_adu_mentions.py:234`, open since 2026-10-24). **`.github/dependabot.yml` watches only GitHub Actions** (uv and npm blocks commented out). CodeQL scans Python only, not the TypeScript tool. **`certifi` 2026.10.23 (MPL-2.0, pulled in by pyproj/pyogrio) is in GitHub's SBOM but not flagged in DISCLOSURES** | Weak: one eligibility-gate item open (high alert) and one licence item unflagged |

Gaps, by impact: (1) fix or document the CodeQL high alert (eligibility gate); (2) flag `certifi` (MPL-2.0) in DISCLOSURES with a justification or remove it, and add a Python licence check like `ui/scripts/check-licenses.mjs`; (3) export and commit the SBOM; (4) enable Dependabot for `uv` and `npm`, and CodeQL for `javascript-typescript`; (5) document how to run the method for another state; (6) add `test_ui.sh` to CI; (7) fill `NOTICE`.

### Usability (20%): 4

| Sub-criterion | Evidence | Assessment |
|---|---|---|
| Interface clarity, organized | Seven numbered tabs; status strip (model, run, vintages); footer with outcome definition | Strong |
| Ease of scenario comparison | Tab 2 shows all three ADU scenarios and baseline on one chart and table; radio switch updates tiles, table and map | Strong for ADU scenarios; **no comparison across benchmark reforms yet** (only one is built) |
| Clear labelling, instructions, outputs | Observed / Calculated / Assumed pills; "—" with a reason, never 0; units on every tile (e.g. "permits over 2027–2031") | Strong |
| Responsiveness and stability | Precomputed 2.8 MB bundle, no live model; Playwright desktop and mobile smoke tests; mobile screenshots for every screen | Good |
| Plain-language technical terms | Scenario info text; "They are scenarios, not confidence intervals"; definitions of sensitivity case and robustness check on tab 4 | Strong |

Gaps, by impact: (1) cross-reform comparison screen once more scenarios exist; (2) tab 4 is very long (5,302 px tall at 1,280 px wide): consider collapsing the sensitivity tables by default; (3) README screen list and numbers are stale (see section 3).

### Methodological Soundness (15%): 4

| Sub-criterion | Evidence | Assessment |
|---|---|---|
| Economic and land-use logic | Outcome-based increment from statewide-law states; current-law rates by rules group; rural and urban contexts (tab 2 "By type of place") | Good |
| Validity of parameter choices | Scenario levels anchored on named states (lower = mean of Rhode Island 0.6214 and Oregon 0.6826 permits per 1,000 single-family homes per year; AQ-043) | Good |
| Reasonable sensitivity ranges | 15 cases in `reference/adu_model_sensitivities.csv`, grouped by what they move; the two largest (multiplicative law −8,091 permits; California-only regression −6,367) are explained as downside framings | Good |
| Internal consistency | Bundle tests: lower ≤ central ≤ upper, counties and municipalities reconcile to the state (largest gap 0.02 permits), bundle equals reference CSVs | Strong |
| Tests demonstrate the stated method | `tests/test_model_engine.py`, `test_pooled_revision.py`, `test_ui_bundle.py`; three doc-vs-output tests skip in CI because their inputs are git-ignored | Good; the skipped tests only prove consistency on a full local build |

Gaps, by impact: (1) no Midwest state has post-law data (the tool's own "strongest challenge" 1); (2) 69% of single-family homes (1,267,433 ÷ 1,839,569) sit in places with uncoded rules treated as restricted; (3) the Gate 5 transfer checks in `MODEL_CHECKS.md` are still in progress.

### Policy Insight & Interpretation (10%): 2

| Sub-criterion | Evidence | Assessment |
|---|---|---|
| Drivers behind differences across scenarios | ADU drivers explained (tab 2 scenario cards, tab 4). **No other benchmark reform modelled, so no cross-scenario drivers** | Weak |
| Which assumptions matter most, with evidence | Tab 4 tornado and "strongest challenges" | Good for ADUs |
| What the model cannot say; where it applies | Tab 4 and brief limitations; "Results are for areas, never individual lots" | Good for ADUs |
| Less-complete-data states | Not demonstrated | Missing |
| Policy Scenario Comparison document | **[POLICY_SCENARIO_COMPARISON.md](../POLICY_SCENARIO_COMPARISON.md) is a template and says "No scenarios have been modeled yet"** | Missing |

Gaps, by impact: (1) model two more benchmark reforms; (2) write the comparison document; (3) a short note or worked example on applying the method to a data-poorer state.

## 3. Submission checklist

Status: **done**, **partial**, or **missing**, as of commit `af3a5e2`.

### Eligibility gates (pass/fail before scoring)

| Item | Status | Evidence |
|---|---|---|
| Reproducible setup from documented commands | Done | README command contract; `setup.sh` + `test.sh` green in CI (run 40290287371, 2026-10-26); fresh-clone check in [gate4/README.md](../gate4/README.md) |
| Automated tests of core logic, documented command | Done | 320 Python tests pass, 3 skipped; `bash scripts/test.sh`, `bash scripts/test_ui.sh` |
| No committed secrets; secret scanning on, zero open alerts | Done | GitHub API: secret scanning enabled, push protection enabled, 0 open alerts |
| Dependabot alerts and CodeQL on; no unaddressed critical/high | **Partial** | Dependabot alerts enabled (API 204), 0 open. CodeQL runs on every push (Python only). **1 open high-severity CodeQL alert** (`scripts/scan_adu_mentions.py:234`), not fixed or justified anywhere. This alone fails the gate as written |
| Approved licence | Done | `LICENSE` = Apache-2.0 full text; GitHub reports `Apache-2.0`. `NOTICE` placeholders remain (not a gate failure) |
| Public GitHub repo | Done | GitHub API: `visibility: public` |

### Deliverables

| Item | Status | Evidence |
|---|---|---|
| Interactive tool (functional) | Done (ADU only) | `bash scripts/run_tool.sh`; screenshots of 7 screens |
| Baseline + ≥3 benchmark scenarios, state level | **Missing** | Only the ADU scenario (1 of 3 required). Rules 7(a): "Incomplete Submissions will not be scored" |
| Slide deck (≤30 slides, PDF) | Missing | Only [PRESENTATION_GUIDE.md](../PRESENTATION_GUIDE.md) |
| Demo video (≤5 min, no account) | Missing | No recording or link |
| Model & Assumptions Overview (≤25 pages, single-spaced, 7 topics) | **Missing** | [MODEL_AND_ASSUMPTIONS.md](../MODEL_AND_ASSUMPTIONS.md) is the template |
| Policy Scenario Comparison (≤4 pages) | **Missing** | Template; says no scenarios modelled |
| Source code, runnable by a third party | Done | Public repo, command contract, committed bundle lets a fresh clone run without the 1.7 GB of builds |
| SBOM | **Missing (file)** | GitHub's dependency graph produces one (SPDX-2.3, 133 packages: 113 npm, 13 PyPI, 7 GitHub Actions/repo), but no export is committed or stored for submission. Format and location are still not specified by the Rules |
| DATA_PROVENANCE.md | Done | One row per dataset with source, vintage, access date, licence; cleaning in [DATA_COMPLIANCE.md](../DATA_COMPLIANCE.md) |
| DISCLOSURES.md | **Partial** | Dependencies, assets and datasets filled. **AI-assisted code generation, pretrained models, external APIs and "Generated or Copied Code" sections are still template prompts.** `certifi` (MPL-2.0) not flagged |
| README command contract | Done | Setup, run, test, test-the-tool, and every data build listed |
| README placeholders and accuracy | **Partial** | "TODO (owner): list each team member's name and role". Headline numbers are pre-AQ-043: README says 645 / 8,721 / 4,407 / 16,853 and reference line 8,208; the adopted values are 605 / 8,757 / 5,538 / 16,889 and 8,851 |

### Dependency licences

- **npm:** `ui/scripts/check-licenses.mjs` fails on anything outside MIT, ISC, BSD-2/3, Apache-2.0, 0BSD, BlueOak-1.0.0, Python-2.0, CC-BY-4.0, MIT-0, Zlib; DISCLOSURES records 113 packages all permissive (2026-10-25). GitHub's SBOM agrees: no copyleft npm package.
- **Python:** no automated licence check. GitHub's SBOM lists 13 PyPI packages; 12 are permissive. **`certifi` is MPL-2.0** (weak copyleft, named as not allowed for dependencies in Rules 7(b)(ii)) and is a transitive runtime dependency of the `geo` extra. It must be flagged and resolved, or justified as an exception in DISCLOSURES. `numpy`'s declared expression includes a `CC0-1.0` component (bundled sub-file); worth one line in DISCLOSURES.
- **GitHub Actions:** first-party actions only.

## 4. Office-hours questions the live materials already answer

The pages have not changed since 2026-10-09, so these answers were already available; the log still lists them as open. Questions are numbered as in [ASSUMPTIONS_AND_QUESTIONS.md](../ASSUMPTIONS_AND_QUESTIONS.md#questions-for-office-hours).

| Q | Answered? | What the live text says |
|---|---|---|
| 4 (600 sq ft) | Largely | Handbook: "Assume detached and semi-detached ADUs of at least 600 square feet are allowed": a size the law allows, which is the team's reading |
| 6 (permits as outcome) | Yes | Handbook lists "permits, starts, completions, or housing stock growth"; teams "must clearly define and justify that choice" |
| 8 (ranges vs statistical intervals) | Yes | Handbook prefers "estimates, ranges, or sensitivity analyses rather than single-point forecasts"; no statistical intervals required |
| 11 (language) | Yes, in practice | Handbook FAQ: "Any language is acceptable, provided your Submission passes the eligibility gates." Python and TypeScript are memory-safe anyway |
| 12 (video length) | Yes | Rules 7(a): "no longer than five (5) minutes"; the Rules prevail |
| 14 (SBOM format) | Partly | Rules 7(d) name GitHub's Insights → Dependency graph → Export SBOM, which gives SPDX JSON. Where to put it is still unstated |
| 16 (fee $50,000) | Partly | "For comparability across submissions, Teams should assume development fees total $50,000 per unit": uniform for the benchmark; local fees as an extra scenario are not forbidden |
| 17 (early review) | Partly | Rules 7: a submission "reviewed prior to the Submission Deadline" that fails is notified and can be fixed. Whether a team can request this is not stated |
| 20 (no-licence public records) | Partly | Rules 7(b)(iii): teams review terms and use "good judgment"; datasets should ideally be free of restrictions. No explicit public-records rule |

Still open: 1–3, 5, 7, 9 (weight of the less-complete-data preference), 10, 13 (repo after the deadline), 15 (size threshold), 18, 19, 21, 22, 23.

## 5. Top gaps to close before submission (16 December 2026)

1. **Two more benchmark scenarios** (baseline + ≥3 is required; 1 of 3 exists). Without them the submission is incomplete and not scored.
2. **Written deliverables:** Model & Assumptions Overview and Policy Scenario Comparison are templates; the deck and video do not exist. The Overview also carries much of Transparency (30%).
3. **Security gate:** fix or justify the open high CodeQL alert in `scripts/scan_adu_mentions.py:234`; enable Dependabot for `uv` and `npm` and CodeQL for TypeScript.
4. **Dependency licences and SBOM:** flag and resolve `certifi` (MPL-2.0) in DISCLOSURES, add a Python licence check, and export and commit the SPDX SBOM.
5. **Disclosures and README accuracy:** fill the AI-assisted code, models, APIs and copied-code sections of DISCLOSURES; replace the README team TODO and `NOTICE` placeholders; update README numbers to the AQ-043 values. Then document a transfer path to a data-poorer state (Rules 8 preference).
