# Handover: transit-oriented density (TOD) scenario

Written 2026-10-26 by the ADU conductor for the conductor of the TOD scenario. Read [LESSONS_FROM_ADU.md](LESSONS_FROM_ADU.md) first; it applies in full and is not repeated here. A parallel session is building the parking-reduction scenario ([PARKING_HANDOVER.md](PARKING_HANDOVER.md)).

## 1. Your job

Build the transit-oriented density scenario for Wisconsin. It runs from research to a working, reviewed part of the tool, through the same five owner gates the ADU scenario used ([MVP_EXECUTION_PLAN.md](../MVP_EXECUTION_PLAN.md)). The owner is Ryan, the product owner. You work in your own project thread and bring every gate packet to him there.

The question to answer, in the owner's terms: **if Wisconsin passed a statewide TOD law at the challenge benchmark, how many additional homes would be permitted over 2027–2031 compared with current law, how confident are we, why, and where?**

## 2. The benchmark (from [CHALLENGE_SPEC.md](../CHALLENGE_SPEC.md))

> **Transit-Oriented Density.** Increase allowable residential density near major transit stops via greater heights and/or floor area ratios. Define "major transit stop" and justify your proximity threshold. You may assume parking requirements are reduced or eliminated.

Shared assumptions:
- five-year horizon;
- the outcome may be permits, starts, completions or stock growth, defined and justified (ADUs used permits at issuance; stay consistent unless the evidence argues otherwise);
- for each scenario, show the change from the baseline, what drives it, sensitivity, and what the model cannot tell.

**Owner decision already made:** model TOD on its own, as the challenge compares scenarios individually. Don't net out the parking scenario or the ADU scenario; combinations come later.

## 3. How to approach it (the owner's direction, 2026-10-26)

1. **Start from the tool, but iterate.** The finished ADU tool shows the target: a baseline, three scenarios by year, a median line of real cases, sensitivities grouped by what they move, a trace of what rests on data versus assumption, and maps by area and district. Write down at Gate 1 which of those your scenario can fill. But the owner is *not* married to that format. If TOD turns out to be concentrated in a few large cities, the "by area" display may need rethinking. Expect several rounds of tool design ↔ data development. You may propose changes to the shared screens, even the ADU ones, so all scenarios read as one report. Propose them through the coordinator; don't edit shared files yourself.
2. **Statewide evidence first, local detail for spot checks only.** Begin with states, and then cities, that changed density rules near transit, and what happened to permits afterward. Wisconsin local-rule coding is for pilots and spot checks.
3. **Policy research is a first-class step (owner's explicit request).** Before any modelling, find a credible report that classifies which states truly implemented TOD-style upzoning near transit and which passed half-hearted or poison-pilled versions: opt-outs, alternative compliance, tiny station areas, retained discretionary review, affordability mandates that make projects infeasible. For ADUs, the Mercatus 2025 taxonomy did this and was a turning point. If no such report exists, build the classification yourself from statute text and each state's post-law data, and show your reasoning. Record effective dates and local-compliance dates separately; they differ a lot for TOD (Massachusetts' compliance deadlines ran 2023–2025).
4. **Defining "major transit stop" and the distance threshold is a central piece of evidence, not a footnote.** The owner sees two routes and wants both considered:
   - **Bottom-up:** identify actual qualifying stops from public transit schedules (GTFS: frequency, mode), draw distance buffers, and count the parcels, homes or blocks inside.
   - **Top-down:** estimate the share of homes or parcels likely to be near a qualifying stop from surrounding density or similar statewide variables, without stop-level data.

   Compare them, and justify the threshold (e.g. California's statutory "major transit stop" definition, 1/4 vs 1/2 mile, rail vs frequent bus) with evidence.

## 4. Evidence leads (verify; none of this is confirmed)

You own this scenario's policy inventory. A one-off scan of all benchmarks ([docs/scenarios/STATE_ADOPTION_INVENTORY.md](../scenarios/STATE_ADOPTION_INVENTORY.md), 2026-10-26) gives unverified starting leads only. Leads to check:
- **Statewide:**
  - Massachusetts MBTA Communities Act (2021; multifamily zoning near stations; compliance 2023–2025);
  - California SB 79 (2025, density near major transit stops) and the earlier transit-related density laws;
  - Colorado HB24-1313 (transit-oriented communities);
  - Washington HB 1491 (2025);
  - Oregon's Climate-Friendly and Equitable Communities rules;
  - Utah HB 462 (2022, station-area plans).
  Most are recent, so expect few post-law years.
- **City or program evidence with production data:**
  - Los Angeles Transit Oriented Communities incentive program (2017);
  - San Diego transit-priority-area bonuses;
  - Minneapolis 2040;
  - Seattle and Portland upzonings;
  - Auckland's 2016 upzoning (peer-reviewed; international, so transfer with care).
- **Expect the same benchmark-mismatch issue we had with ADUs.** Programs may bundle affordability requirements or density bonuses that go beyond, or fall short of, a plain height and FAR increase. Classify each case against the benchmark.

### Heads-up from the one-off scan (unverified)

- **No state has 2 or more years of post-law production data yet.** California SB 79 has been in force since 2026-07-01, and Washington, Colorado and Oregon bind between 2024 and 2029. Massachusetts has about 2 years of pipeline counts.
- **The best measured precedent may be Los Angeles's Transit Oriented Communities program.**
- **Pooled rates may not work.** A pooled post-law rate, as for ADUs, may not be possible. The scan suggests "station-area capacity × a per-acre yield" from city cases instead. Test both if the data allow.
- **Wisconsin data is ready.** The Milwaukee and Madison transit feeds may already cover their bus rapid transit lines, and the Madison TOD overlay is in the repo.

## 5. Wisconsin specifics to establish (verify each)

- **Transit:**
  - Milwaukee County Transit System, including its bus rapid transit line and the Milwaukee streetcar;
  - Madison Metro, including its bus rapid transit;
  - Amtrak stations (Hiawatha and Empire Builder) and Metra in Kenosha;
  - frequent bus in Green Bay, the Fox Cities and others.

  Check whether each agency publishes GTFS, and under what licence.
- **Concentration:** TOD may be concentrated in Milwaukee and Madison. Decide early, with the owner, how the tool shows a scenario that is mostly two cities.
- **Baseline:** the all-housing baseline (all permitted units by area, year and structure type, from Census building permits) is built by the parking session and shared with you (see LESSONS §6). Your current-law baseline is the part of it near qualifying stops. Say how you allocate it.
- **Pilots:** likely candidates are Milwaukee and Madison corridors, plus one mid-size city with only bus service, as the "does it transfer" check. That is the analogue of the ADU test of cities like Madison.

## 6. Suggested gate plan (adapt it; owner decisions go in the AQ log)

| Gate | What you bring |
| --- | --- |
| 1. Scope and outline | Policy research and taxonomy (benchmark-faithful vs weak states and programs); candidate definitions of "major transit stop" and distance thresholds; bottom-up vs top-down options; the outcome and eligible base; which tool outputs you expect to fill; data contract; licence check of each source; office-hours questions. |
| 2. Usable data | Statewide transit-stop or density inputs fetched automatically; eligible homes or parcels near stops statewide; the comparison-case data assembled ("observed" vs "source lead"); a pre-registered comparison plan. |
| 3. Baseline, response, uncertainty | Baseline near stops; response from the cases, with held-out tests deciding the model choices; scenarios labelled by meaning (lower = average of the weakest real cases, not a divided central); median line; ramp from data; sensitivities grouped by what they move. |
| 4. Working pilot in the tool | TOD in the multi-scenario tool via the scenario contract; pilots; independent verification of every displayed number. |
| 5. Statewide MVP | Reconciliation to the state and districts; trace; rubric check; the owner's "good enough" decision. |

## 7. Shared piece you build

You build the **multi-scenario tool shell and scenario contract** for both new scenarios (LESSONS §6):
- a scenario picker and registry;
- shared screens that read the selected scenario;
- `docs/shared/SCENARIO_CONTRACT.md`.

Build it early, ideally alongside Gate 1–2 research, since the parking session will plug into it. The ADU screens must look and behave the same apart from the picker, and the ADU numbers and tests must not change. The shared files are owned by the ADU conductor, so tell the coordinator before you start, so ownership is handed to you for this piece.

## 8. Working arrangements

- **Repo:** `/Users/mroconnell/Documents/housing-challenge-starter-missingmiddleware` (public). Routine commits and pushes to `main` are authorized; commit per logical work package.
- **Your files:**
  - `docs/tod/`, `reference/tod_*`, `missing_middleware/tod/`, `scripts/*tod*`, `tests/test_tod*`;
  - your scenario's UI files under the scenario contract, e.g. `ui/src/scenarios/tod/`, once the shell exists.
- **Shared files** belong to the ADU conductor: the engine, the bundle builder's shared parts, shared screens, the AQ log structure, DATA_PROVENANCE, DISCLOSURES and the compliance scripts. Add your own AQ entries and provenance rows, but keep the edits small and re-read the file before writing, since other sessions edit it too. For anything else shared, ask through the coordinator.
- **The parking session** builds the all-housing baseline you'll use, and may need your transit data (frequent-transit areas often define parking exemptions). Coordinate through the coordinator rather than fetching the same source twice.
- **Tests:** `bash scripts/test.sh` and `bash scripts/test_ui.sh` must pass before each push. Check a fresh clone before calling a gate done.
- **Deadline:** submission is due 16 December 2026, 11:59 pm ET. The owner prefers correct sequencing to calendar pressure, but both new scenarios are needed for a scored submission.

## 9. First steps

1. Read LESSONS_FROM_ADU.md, the gate packets (`docs/gate3/README.md`, `docs/gate5/README.md`) and the state-adoption inventory.
2. Run the tool (`bash scripts/run_tool.sh`) and look at every screen.
3. Post a short Gate 1 plan in your thread: research questions, the policy-taxonomy search, data candidates, and which decisions you'll need from the owner.
4. Start the policy research and the "major transit stop" definition work.
