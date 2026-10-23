# MVP Execution Plan

Updated: 2026-10-23. Status: plan prepared for owner review; implementation gates have not passed.

## Product destination and sequence

The product opens with Wisconsin housing conditions, current-law baseline projections, and statewide policy comparisons. Local jurisdictions are drill-downs and development pilots. ADU forecasts report housing units authorized by permits over five years, aggregated to defensible areas, with lower, central, and upper paths. Existing inventory, observed activity, projected baseline, additional growth, legal capacity, and completed homes remain distinct.

The owner selected this sequence, with no date or effort cap:

1. Build a functioning ADU pilot using Madison and provisional restrictive-policy example New Berlin.
2. Expand that ADU model to Wisconsin, with a state-first interface and an explicit coverage and generalization method.
3. Review whether the statewide ADU MVP is good enough. Improve material weaknesses until it is.
4. Build and review MVPs for the other benchmark scenarios, using the shared state profile and output conventions. TOD and parking are current candidates, subject to evidence review.
5. Once the scenario MVPs demonstrate the right approach, deepen individual components and transfer those improvements across scenarios. Complete statewide comparisons, policy packages, district explanations, and submission materials.

An ADU-only MVP is an intermediate milestone. The competition submission requires statewide results, a baseline, and at least three benchmark scenarios. No pilot or ADU-only gate establishes full submission compliance.

## Can the pilot scale?

The code, input schemas, evidence records, and interface components should be reusable. Two cities do not establish a representative statewide development rate. Do not multiply their results by Wisconsin's population or single-family stock.

Design a statewide geographic ledger during pilot development. Every area has inventory, available policy evidence, observed permit coverage, assumptions, source vintages, and an uncertainty flag. Distinguish observed, calculated, and assumed values. The statewide stage must identify relevant differences such as existing ADU rights, single-family inventory, and broad development context; select grouping and response pooling only where the evidence supports them. A jurisdiction sample for checking statewide transfer should extend beyond the two pilots.

Use coarser estimates where detailed local data are unavailable, with explicit assumptions and sensitivity. Unknown legal conditions must remain visible and must not be silently coded as permissive or restrictive. Uncovered areas and their possible contribution require an explicit treatment approved at the statewide gate. State totals must not quietly exclude them.

Pilot data contracts must support statewide aggregation from the start. Detailed local maps may arrive before statewide map detail; a statewide headline may only use a defensible statewide method.

## Multi-agent working agreement

All agent sessions execute locally. Routine logical milestone commits and competent GitHub pushes are authorized by the owner without additional publication approval. PRs and isolated worktrees are optional tools, not required ceremony. Preserve existing unrelated work and avoid committing large raw data, owner-provided PDFs, or unrelated files.

Use one coordinating agent and bounded work packages. At most three specialist agents run alongside the coordinator when capacity permits. Assign exclusive ownership of files or directories during each parallel work package, and give every assignment explicit inputs, outputs, dependencies, checks, and a completion report. Serialize changes to shared schemas, integration files, and common documentation. The coordinator integrates and checks the combined result.

Prefer clear groups of work and logical milestones over tiny scattered commits. Explain the analytical reason for a change in documentation and meaningful comments. Keep outputs, assumptions, source versions, and validation results tied to the same milestone version.

At every owner gate, agents first assess the work themselves, repair failures they can resolve, and prepare the review packet. The human gate is still required: silence is not approval. Dependent work waits for the owner's decision. Independent, already-authorized work may continue when it does not preempt that decision.

## Common acceptance standard

Every gate packet includes:

- What changed and the question the milestone answers.
- A checklist marked pass, fail, or unknown, with concrete evidence and artifact links.
- A short demo or worked example, expected results, and literal review instructions.
- Known limitations, effect on the results, and any proposed workaround or scope change.
- Agent self-assessment and reviewer findings; unresolved disagreement must be visible.
- The exact decision requested from the owner and the next work it unlocks.

Checks must verify meaningful behavior. Examples include reconciling sums, identifying duplicates, checking known spatial matches, preserving missingness, correct law timing, and applying no new rights when a reform matches current rules. Passing a test suite alone does not establish valid evidence or model calibration. Set quantitative tolerances in advance of evaluating the relevant results; document why they are appropriate rather than inventing a universal match-rate threshold.

## Gate 1 — Scope, model outline, and statewide data contract

### Agent work

The coordinator prepares the ADU mechanism diagram and stable input/output contracts. A data agent inventories full sources and access conditions. A policy/evidence agent maps relevant laws and studies to proposed model mechanisms. An interface/review agent checks the state-first workflow against the intended legislative audience.

Define the analysis date, permitted-unit milestone, treatment of conversions/legalizations, study geography, required provenance fields, and a candidate statewide aggregation structure. Propose technology choices after checking actual acquisition and spatial-processing requirements. The choice of software is routine implementation work unless it creates an important access, licensing, reproducibility, or cost dependency.

### Agent self-check

Trace one hypothetical result from inventory through current rights, changed rights, uptake, timing, and area totals. Show which inputs are available, assumed, or missing. Confirm that the contracts support both pilot and statewide runs and do not require an exhaustive parcel-level law audit before any broader estimate is possible.

### Owner review: step by step

1. Read the one-page scope and model diagram.
2. Follow the worked example from an existing home to an additional permitted unit.
3. Check that the five-year outcome and area-level presentation match your intent.
4. Inspect the proposed treatment of unknown statewide policy/data coverage.
5. Approve the specification or identify a specific assumption or boundary to change.

**Unlocks:** acquisition, normalization, and detailed policy/evidence work against agreed contracts.

## Gate 2 — Usable data and verified connections

### Parallel agent work

- **Inventory/geography:** acquire and pin pilot inventory and statewide background sources; retain geometries, source IDs, vintages, and common-area crosswalks.
- **Policy/evidence:** verify California package timing and relevant local rules; audit Menlo Park's reported fee history; define prior versus changed rights for the Wisconsin pilots.
- **Permits/quality:** obtain historical issued permit records, identify authorized ADU units, distinguish stages, and establish location fields and reporting coverage.

The coordinator integrates these tables, checks licenses/access, and records every assumption and transformation. Preserve historical source alternatives, including the recovered 2012–2019 compilation and newer HCD series, rather than silently replacing discrepant observations.

### Agent self-check

Report missing years and fields, duplicate handling, unit definitions, coordinate systems, match rates, unmatched records, and boundary/vintage differences. Independently inspect a documented sample of successful and unsuccessful joins, ambiguous classifications, and records near geographic boundaries. Investigate systematic mismatches; do not report only an overall percentage. Reconcile appropriate aggregates while noting sources that share underlying inputs.

If New Berlin cannot support a reliable permit baseline, prepare a concrete choice: obtain an authorized records request, use a justified coarser method, or substitute a different jurisdiction. Do not silently replace the user-selected example. Prepare requests for owner review; contacting other people requires authorization.

### Owner review: step by step

1. Open the coverage table: identify what is observed, missing, and assumed for each pilot and for the statewide foundation.
2. Inspect a few source records beside their cleaned versions.
3. Follow an issued permit through its parcel and geographic-area match; inspect one unmatched example too.
4. Read a current-law and reform classification with the linked dated source.
5. Check the map against recognizable streets and land uses.
6. Review the agent's quality findings and accept the data's fitness for the proposed model, or choose a documented workaround.

**Unlocks:** numerical baseline construction and response calibration on accepted inputs.

## Gate 3 — Baseline, policy response, and uncertainty specification

### Agent work

A baseline agent compares simple current-law projection methods and proposes a central method and range. A response/evidence agent develops time-dependent ADU uptake assumptions from selected comparison evidence. A validation agent independently challenges definitions, prior-rights treatment, evidence transfer, confounding, and numerical behavior. The coordinator integrates the model and area allocation.

Separate additional legal opportunity from the number of owners expected to participate. Distinguish evidence-derived parameters, descriptive observations, transferred assumptions, and newly estimated effects. Account for earlier California reforms when studying the 2020 package. A before/after rise is not automatically a causal effect. The MVP must address the judging criteria; it need not invent a new causal study merely to appear sophisticated.

Construct coherent lower, central, and upper five-year paths. Explain why their assumptions differ and what evidence supports them. Use the same background setting in baseline and reform cases; avoid counting an uncertainty source twice. Aggregate shared parameter uncertainty consistently instead of treating every area as independent. Specify spatial allocation at a resolution justified by the evidence.

### Agent self-check

Test unchanged-policy equivalence, correct eligibility/timing, duplicate opportunities, unit accounting, aggregation, and area totals. Test effects of alternative evidence selections, baseline periods, uptake paths, and geographic resolution. Use historical holdouts or back-tests where the evidence permits; explain when sparse observations limit validation. Predictive checks and causal identification are different questions.

### Owner review: step by step

1. Follow one baseline calculation and one reform calculation using the same inputs.
2. Check that existing local permissions reduce the *change in rights* where appropriate.
3. Read the source and rationale for the central development-response assumption.
4. Compare the lower and upper paths and identify which assumptions produce the difference.
5. Inspect the historical validation and the strongest challenge raised by the reviewing agent.
6. Decide whether the model is defensible enough to demonstrate, or request a specific revision.

**Unlocks:** an integrated pilot demonstration using accepted model mechanics.

## Gate 4 — Working ADU pilot

### Agent work

Integrate the pilot inventory, baseline, reform estimates, evidence panels, and aggregate map. The interface agent implements the reviewed direction; the coordinator owns model/UI consistency. A verification agent runs a clean reproduction and checks every displayed value against the underlying scenario output.

Pilot screens must make statewide ambition clear without presenting two pilot results as Wisconsin totals. Show existing inventory and observed activity separately from future baseline and incremental ADU permitting. Display data vintages, assumptions, coverage, and limitations where users need them.

### Agent self-check

A clean run acquires/prepares inputs, produces numerical results, and launches the tool through documented commands. Core analytical checks pass. Every scenario selection, timeline change, headline total, map aggregation, and evidence link is consistent. Test both pilot jurisdictions, mobile/desktop layouts, and keyboard access. No forecast marks imply that a named lot will build an ADU.

### Owner review: step by step

1. Follow the supplied setup/run instructions or open the prepared local demo.
2. Select each pilot and explain its baseline back in your own words.
3. Apply the benchmark reform and inspect annual and five-year additional permits.
4. Open the map, change the year, and distinguish inventory, baseline growth, and additional growth.
5. Open the evidence and uncertainty explanations; identify at least one assumption you can challenge.
6. Review agent checks and decide whether the ADU mechanism is ready for statewide expansion or needs another pilot iteration.

**Unlocks:** statewide ADU implementation; pilot completion is not competition readiness.

## Gate 5 — Statewide ADU MVP and the “good enough” decision

### Agent work

Implement the statewide profile and permit context, document local-rule coverage, select justified geographic groupings and pooling assumptions, and test transfer beyond Madison and New Berlin. Show how assumed or unverified coverage affects statewide totals and ranges. Reconcile all area outputs to Wisconsin, with explicit treatment of unknown/unallocated portions.

The landing screen presents statewide housing conditions and statewide baseline/ADU projections. “Housing health” uses defined indicators such as housing stock, occupancy/vacancy, housing mix, and permitted production with dates and uncertainty; do not invent an opaque composite score. General housing production and ADU-specific forecasts must retain separate labels and denominators. Detailed local maps are optional drill-downs where supported.

### Agent self-check

Demonstrate the statewide method independently of a simple pilot multiplier. Check at least contrasting urban, suburban, smaller-community, and rural contexts where source coverage permits, and explain unsupported contexts. Trace state totals and ranges to source groups and assumptions. Report sensitivity to unknown local rules, alternative groupings, and transferred response rates.

Score the tool against the repository judging rubric: transparency/explainability 30%, replicability/scalability 25%, usability 20%, methodological soundness 15%, and policy insight 10%. Verify against authoritative competition materials before making a submission-compliance claim; the live handbook and rules were fetched on 2026-10-23 and matched the saved handbook (see [gate1/OFFICIAL_MATERIALS_CHECK.md](gate1/OFFICIAL_MATERIALS_CHECK.md)); recheck before submission. Record evidence for each criterion and remaining gaps; internal scores are not predicted judging scores.

### Owner review: step by step

1. Open the landing screen and identify Wisconsin's current housing conditions and baseline projection.
2. Apply the ADU reform and identify the statewide additional permitted units and lower/upper paths.
3. Follow the explanation of why those results differ across broad areas.
4. Inspect how much of the result depends on verified local evidence versus assumptions or incomplete coverage.
5. Reconcile the displayed geographic breakdown to the statewide result.
6. Read the rubric assessment, strongest sensitivity, and remaining limitations.
7. Choose **good enough to extend**, **iterate on named weaknesses**, or **revisit the model approach**.

**Unlocks:** MVP work on additional benchmark scenarios only after the owner accepts the statewide ADU foundation.

## Later scenario and refinement cycles

For each additional scenario, repeat data readiness, mechanism/range review, integrated demo, and statewide “good enough” review. Reuse verified state-profile inputs, provenance, uncertainty conventions, validation tools, map components, and briefs; add scenario-specific data only as the mechanism requires.

After at least three scenario MVPs work statewide, test combined packages without double counting shared sites or parking benefits. Revisit weak components across all scenarios when evidence or methods improve. Complete district views at defensible resolution, an exportable policy brief, required documentation, deck, video, disclosures, and final reproducibility/security/license gates.

Preserve a prioritized improvement backlog. A proposed detail should identify the decision it improves, supporting evidence, likely impact on results, and effort/dependencies. Defer details that add apparent precision without a material improvement in policy interpretation.

## Current position

**2026-10-23:** Gate 1 passed with changes (see the [Gate 1 packet](gate1/README.md) and AQ-021 to AQ-023). Gate 2 work is under way: statewide background acquisition, Madison permit extraction and ADU classification, a search for a mid-size restrictive comparison city with accessible permit records (replacing New Berlin), and coding of the largest jurisdictions' ADU rules. The owner prioritizes correct sequencing over calendar targets.

The assumptions log, initial California policy register, historical ADU source trace, and interface/map concepts exist. Full pilot data acquisition, audited joins, a calibrated model, statewide ADU estimates, and functioning production UI remain to be built. The map concepts contain illustrative growth; they are not validation evidence or completed analytical milestones.

## References

- [Project Plan](PROJECT_PLAN.md)
- [Assumptions and Open Questions](ASSUMPTIONS_AND_QUESTIONS.md)
- [Policy Catalog](POLICY_CATALOG.md)
- [Challenge Specification and rubric](CHALLENGE_SPEC.md)
- [Official Handbook](https://housingchallenge.turnout.rocks/handbook.html) and [Official Rules](https://housingchallenge.turnout.rocks/rules.html); both fetched live on 2026-10-23 and matching the owner-provided saved handbook.
