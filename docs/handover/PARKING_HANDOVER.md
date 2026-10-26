# Handover: parking requirement reduction scenario

Written 2026-10-26 by the ADU conductor for the conductor of the parking-reduction scenario. Read [LESSONS_FROM_ADU.md](LESSONS_FROM_ADU.md) first; it applies in full and is not repeated here. A parallel session is building the transit-oriented density scenario ([TOD_HANDOVER.md](TOD_HANDOVER.md)).

## 1. Your job

Build the parking-reduction scenario for Wisconsin. It runs from research to a working, reviewed part of the tool, through the same five owner gates the ADU scenario used ([MVP_EXECUTION_PLAN.md](../MVP_EXECUTION_PLAN.md)). The owner is Ryan, the product owner. You work in your own project thread and bring every gate packet to him there.

The question to answer, in the owner's terms: **if Wisconsin reduced or eliminated minimum parking requirements statewide at the challenge benchmark, how many additional homes would be permitted over 2027–2031 compared with current law, how confident are we, why, and where?**

## 2. The benchmark (from [CHALLENGE_SPEC.md](../CHALLENGE_SPEC.md))

> **Parking Requirement Reduction.** Reduce or eliminate minimum parking requirements. Specify assumptions about developer-provided parking absent mandates.

Shared assumptions:
- five-year horizon;
- the outcome may be permits, starts, completions or stock growth, defined and justified (ADUs used permits at issuance; stay consistent unless the evidence argues otherwise);
- for each scenario, show the change from the baseline, what drives it, sensitivity, and what the model cannot tell.

The benchmark explicitly asks you to state **how much parking housing developers would still choose to build once minimums are removed**, because buyers, renters and lenders want it. That assumption is part of the answer. Extra homes come only where the minimum forced more parking than the market wanted. If a developer would build 1.5 spaces per unit anyway and the minimum was 1.5, removing it changes nothing for that project. Studies measure this gap; for example, Seattle projects built about 40% fewer spaces than the old minimums required (verify).

**Owner decision already made:** model parking on its own, as the challenge compares scenarios individually. The ADU benchmark already requires no additional parking for ADUs, and the TOD benchmark may assume reduced parking near transit. Don't net those out now; combinations come later. Say plainly in the docs where the scenarios overlap.

## 3. How to approach it (the owner's direction, 2026-10-26)

1. **Start from the tool, but iterate.** The finished ADU tool shows the target: a baseline, three scenarios by year, a median line of real cases, sensitivities grouped by what they move, a trace of what rests on data versus assumption, and maps by area and district. Write down at Gate 1 which of those your scenario can fill. The owner is *not* married to that format. If parking reform mostly affects multifamily projects in larger places, the "by area" view may need rethinking. Expect several rounds of tool design ↔ data development. You may propose changes to the shared screens, even the ADU ones, so all scenarios read as one report. Propose them through the coordinator; don't edit shared files yourself.
2. **Statewide evidence first, local detail for spot checks only.** Begin with states, and then cities, that removed or cut parking minimums, and what happened to permits and to parking provided afterward. Coding Wisconsin's local parking minimums is for pilots and spot checks. It was costly and weakly predictive for ADUs.
3. **Policy research is a first-class step (owner's explicit request).** Before any modelling, find a credible source that classifies which states and cities truly removed parking minimums and which made partial or hollow changes: transit-only exemptions, affordable-only exemptions, large-project carve-outs, replacement of minimums by discretionary review. For ADUs, the Mercatus 2025 taxonomy did this and was a turning point. A strong candidate here is the Parking Reform Network's map and database of parking-mandate reforms; check its coverage, method and licence. If no source is adequate, build the classification yourself from statute and ordinance text and post-reform data, and show your reasoning. Record adoption dates and effective dates separately.
4. **The mechanism matters.** Parking minimums raise cost per unit and use land, and they bind mainly where developers would otherwise build less parking: infill, multifamily, small lots, and near transit. Be explicit about the channel you model:
   - a direct before/after change in permits;
   - a cost-per-unit change times a supply response;
   - or both, tested against each other with held-out cases, the way the ADU work let the data decide.

## 4. Evidence leads (verify; none of this is confirmed)

You own this scenario's policy inventory. A one-off scan of all benchmarks ([docs/scenarios/STATE_ADOPTION_INVENTORY.md](../scenarios/STATE_ADOPTION_INVENTORY.md), 2026-10-26) gives unverified starting leads only. Leads to check:
- **Statewide:**
  - California AB 2097 (2022; no minimums near major transit, effective 2023);
  - Oregon's Climate-Friendly and Equitable Communities parking reforms (2023);
  - Colorado HB24-1304 (2024);
  - Washington SB 5184 (2025);
  - partial limits in Maine and Montana;
  - possibly others (Minnesota, New Hampshire, Texas).
  Most are recent, so post-law production data will be thin.
- **City reforms with studies:**
  - Buffalo's 2017 Green Code (citywide elimination; studied by Hess and Rehler);
  - Minneapolis (2021 citywide elimination);
  - Seattle (frequent-transit areas; studies of parking provided versus former minimums, e.g. Gabbe, Pierce and Clowers);
  - San Diego (2019, near transit);
  - Portland;
  - Los Angeles adaptive reuse (1999) as an early case.
- **"Developer-provided parking absent mandates":** several of these studies measure how many spaces developers chose to build after reform. That gives your benchmark assumption directly, with a range.
- **Benchmark mismatch:** some reforms are transit-only or affordable-only, so they are partial versions of the benchmark. Classify each case, as we did for ADUs (we capped beyond-benchmark ADUs and removed apartment-lot ADUs from California's counts).

### Heads-up from the one-off scan (unverified)

- **Many laws, no production data.** About 15 states have laws at or near the benchmark (e.g. North Carolina from 2027, Washington ESSB 5184, Connecticut PA 25-1), but no post-law production data is tied to any of them.
- **City studies mostly measure parking built, not homes.** For example, Seattle projects built about 40% fewer spaces than the old minimums required.
- **A different method is likely.** The scan suggests a cost-per-project and supply-response model may fit better than pooling states' post-law rates. Test that against any before/after permit evidence you can find (Buffalo, Minneapolis).
- **No statewide source of Wisconsin minimums.** Wisconsin parking minimums aren't compiled statewide, which is another reason local coding is for spot checks only.

## 5. Wisconsin specifics to establish (verify each)

- **Current minimums:** whether any Wisconsin cities have already cut parking minimums (e.g. Milwaukee or Madison in parts of the city), with dates. Treat local codes as spot checks, as for ADUs. The statewide model should not depend on coding every municipality.
- **Baseline:** you build the all-housing baseline (see §7). Parking effects likely concentrate in multifamily (5+ and 2–4 units), so the structure-type split matters.
- **Where minimums bind:** propose a statewide way to estimate where minimums actually bind (e.g. by structure type, lot size, density or context) using statewide data, and test it against the case cities.
- **Overlap with TOD:** frequent-transit areas may define partial exemptions in other states. The TOD session builds the multi-scenario tool shell you'll plug into, and fetches transit-stop data; coordinate through the coordinator rather than duplicating it.
- **Pilots:** likely candidates are a large city (Milwaukee or Madison) and a mid-size or suburban place where minimums are typical, as the "does it transfer" check.

## 6. Suggested gate plan (adapt it; owner decisions go in the AQ log)

| Gate | What you bring |
| --- | --- |
| 1. Scope and outline | Policy research and taxonomy (full vs partial reforms); mechanism options; the developer-provided-parking assumption and its evidence; the outcome and eligible base; which tool outputs you expect to fill; data contract; licence check of each source; office-hours questions. |
| 2. Usable data | Comparison-case data assembled ("observed" vs "source lead"); Wisconsin statewide inputs for where minimums bind; a pre-registered comparison plan. |
| 3. Baseline, response, uncertainty | Baseline by structure type; response from the cases, with held-out tests deciding the model choices; scenarios labelled by meaning (lower = average of the weakest real cases, not a divided central); median line; ramp from data; sensitivities grouped by what they move, including the developer-provided-parking assumption. |
| 4. Working pilot in the tool | Parking in the multi-scenario tool via the scenario contract; pilots; independent verification of every displayed number. |
| 5. Statewide MVP | Reconciliation to the state and districts; trace; rubric check; the owner's "good enough" decision. |

## 7. Shared piece you build

You build the **all-housing baseline** for both new scenarios (LESSONS §6):
- all permitted units by area, year and structure type (1, 2, 3–4, 5+) from the Census Building Permits Survey data already in the repo (`data/processed/foundation/`);
- a current-law projection for 2027–2031, chosen by a held-out-year test;
- an explicit unallocated row that reconciles to the state;
- outputs in `reference/housing_baseline_*.csv`, documented in `docs/shared/HOUSING_BASELINE.md`, with tests.

Build it early, since the TOD session needs it too. Missing permit reports are not zero.

## 8. Working arrangements

- **Repo:** `/Users/mroconnell/Documents/housing-challenge-starter-missingmiddleware` (public). Routine commits and pushes to `main` are authorized; commit per logical work package.
- **Your files:**
  - `docs/parking/`, `reference/parking_*`, `missing_middleware/parking/`, `scripts/*parking*`, `tests/test_parking*`;
  - your scenario's UI files under the scenario contract, e.g. `ui/src/scenarios/parking/`, once the shell exists.
- **Shared files** belong to the ADU conductor: the engine, the bundle builder's shared parts, shared screens, the AQ log structure, DATA_PROVENANCE, DISCLOSURES and the compliance scripts. Add your own AQ entries and provenance rows, but keep the edits small and re-read the file before writing, since other sessions edit it too. For anything else shared, ask through the coordinator.
- **Tests:** `bash scripts/test.sh` and `bash scripts/test_ui.sh` must pass before each push. Check a fresh clone before calling a gate done.
- **Deadline:** submission is due 16 December 2026, 11:59 pm ET. The owner prefers correct sequencing to calendar pressure, but both new scenarios are needed for a scored submission.

## 9. First steps

1. Read LESSONS_FROM_ADU.md, the gate packets (`docs/gate3/README.md`, `docs/gate5/README.md`) and the state-adoption inventory.
2. Run the tool (`bash scripts/run_tool.sh`) and look at every screen.
3. Post a short Gate 1 plan in your thread: research questions, the policy-taxonomy search, data candidates, and which decisions you'll need from the owner.
4. Start the policy research and the developer-provided-parking evidence.
