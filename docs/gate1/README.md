# Gate 1 Packet: ADU Scope, Model Outline, and Data Contracts

Prepared 2026-10-23 by the conductor. **Status: passed with changes on 2026-10-23.** Owner decisions are recorded in [AQ-021 to AQ-023](../ASSUMPTIONS_AND_QUESTIONS.md#aq-021-gate-1-decisions-on-the-adu-model) and summarized below.

## Owner decisions (2026-10-23)

| ID | Decision |
| --- | --- |
| D1 | No poison pills: the modeled bill removes owner-occupancy and related-occupant rules (AQ-022). Form-only is an optional sensitivity only. |
| D2 | Stylized dates accepted. |
| D3 | Unknown local rules = no ADU rights for the MVP; code the largest jurisdictions and spot-check; systematic coding after the other scenario MVPs; baseline-health reporting across scenarios (AQ-023). |
| D4 | ACS denominator accepted. |
| D5 | Accepted, plus the ADU-equivalent rule: a permit adding a dwelling on a parcel that already has one. |
| D6 | Replace New Berlin with a mid-size city with permit data and no ADU allowance; search for permit data first. |
| D7 | Sequencing over calendar; the calendar below is withdrawn. |
| D8 | Main fast-forwarded. |

The text below is the packet as presented, kept for the record.

## What this gate decides

Whether the ADU model's scope, mechanism, outcome, geography, and data contracts are right before we acquire data and build anything. Approval unlocks Gate 2 work: data acquisition, ordinance coding, and permit audits against these contracts.

## Artifacts, in review order

| # | File | What it is |
| --- | --- | --- |
| 1 | [SCOPE_AND_MODEL.md](SCOPE_AND_MODEL.md) | One-page scope, rights classes, equations, diagram, worked example, display implications, unknown-coverage design |
| 2 | [DATA_CONTRACTS.md](DATA_CONTRACTS.md) | Tables every stage reads and writes; same for pilot and statewide |
| 3 | [POLICY_EVIDENCE_MAP.md](POLICY_EVIDENCE_MAP.md) | Wisconsin, Madison, New Berlin law; ADU uptake evidence; proposed (not adopted) Gate 3 ranges |
| 4 | [DATA_INVENTORY.md](DATA_INVENTORY.md) | Full sources, access checks, coverage table, Gate 2 risks |
| 5 | [INTERFACE_WORKFLOW.md](INTERFACE_WORKFLOW.md) | State-first screen flow and critique of the mockups |
| 6 | [OFFICIAL_MATERIALS_CHECK.md](OFFICIAL_MATERIALS_CHECK.md) | Live handbook and rules versus our digest and spec |

No demo exists at Gate 1; nothing is built yet.

## Owner review: step by step, with my self-assessment

| Step | What you do | What you should see | My result |
| --- | --- | --- | --- |
| 1 | Read the one-page scope and the diagram in SCOPE_AND_MODEL.md | Question, reform, outcome (ADU units at permit issuance), dates, geography, out-of-scope list; diagram from homes and local rules to state total | **Pass.** All parts present. The diagram is Mermaid and renders on GitHub; in a plain text viewer read the "plain-language version" under it. |
| 2 | Follow the worked example | Case A restrictive town: about 1 baseline and about 11 additional over five years ("full") or about 3 ("form-only"); Case B Madison: 0 additional, about 55 baseline; Case C unknown town: about 8, labeled estimated, bounded 0 to 12 | **Pass after repair.** First draft mixed paths and gave a wrong ΔR; rewritten and arithmetic re-checked (11.5, 3.3, 54.6, 8.3, 12.3). Rates are proposals, not adopted. |
| 3 | Check that the five-year outcome and area presentation match your intent | Outcome is gross ADU permits, not completions; display leads with state, county, and context-group totals and shows small areas as rates, never lots | **Needs your judgment.** I recommend it. Be aware the central numbers are small (on the order of 1,000 statewide if half of homes gain rights), so the reform will read as a modest lever. |
| 4 | Inspect the treatment of unknown statewide policy and data coverage | Rights classes include `unknown`; recommended design codes the largest places and all county ordinances, samples the rest, and reports verified versus estimated parts plus bounds | **Needs your judgment (D3).** Feasible in the time available; the full stratified audit is not. |
| 5 | Approve or name a specific change | Decision table below | Yours. |

## Decisions requested

| ID | Decision | Options | My recommendation | What depends on it |
| --- | --- | --- | --- | --- |
| D1 | Does the benchmark override owner-occupancy and related-occupant rules? | Full / form-only / both | **Both: full as headline, form-only as named variant** | New Berlin and most restrictive places' results |
| D2 | Analysis dates | Stylized 2027–2031 with rules frozen 2026-10-31 / realistic 2028–2032 | **Stylized, with implementation lag as a sensitivity** | Every forecast table and label |
| D3 | Unknown local rules | Code top 50 places + applicable county ordinances + sample of 60–100 / exclude unknowns / treat unknowns as prohibited | **Code and sample** | Statewide total, coverage view, Gate 2 workload |
| D4 | Home count used as the denominator | ACS one-unit detached as control total / parcel proxy | **ACS control; parcels only allocate within areas** (parcel proxy overstates Madison by 43%) | Inventory pipeline |
| D5 | What counts as production | New detached + attached headline; conversions separate; legalizations excluded | **As listed** | Outcome definition, evidence calibration |
| D6 | New Berlin permit data (no public records exist) | Records request / coarser method with assumed near-zero baseline / substitute or add a city (Neenah, pre-Aug-2025 Milwaukee) | **Coarser method now, and I draft a records request for you to send if you want one.** I will not contact the city. | Gate 2 pilot baseline |
| D7 | Schedule | See below | **Adopt the compressed calendar** | All later gates |
| D8 | GitHub main | Merged work is on branch `claude/project-thread-0iaj78`; main is a clean fast-forward | **Fast-forward main** | Where future milestone pushes land |

## Schedule risk

The competition deadline is 2026-12-16 (54 days). The plan still holds four more ADU gates and two more scenario MVPs. A calendar that fits, if each review turns around within a day:

| Milestone | Target |
| --- | --- |
| Gate 2 data and connections | 2026-11-02 |
| Gate 3 baseline, response, uncertainty | 2026-11-06 |
| Gate 4 ADU pilot demo | 2026-11-12 |
| Gate 5 statewide ADU MVP | 2026-11-20 |
| Two more scenario MVPs (TOD and parking are current candidates) | 2026-12-06 |
| Submission materials, freeze | 2026-12-14 |

Starting background research on the next two scenarios before Gate 5 would protect this calendar; I will ask before doing so.

## Proposed Gate 2 agent assignments (start after your Gate 1 decision)

| Agent | Owns | Delivers | Acceptance check |
| --- | --- | --- | --- |
| Inventory and geography | acquisition scripts for ACS, PEP, BPS, TIGER, V12; `areas`, `state_conditions`, `inventory`; municipality crosswalk | Pinned, reproducible tables for Wisconsin | Totals reconcile to published state figures; parcel-to-ACS ratio reported by county |
| Policy coding | `policy_rules`, `rights_exposure`; top 50 places, applicable county ordinances, sample | Dated codings with sources and "not found" kept | Second-reader check on a sample of codings |
| Permits and quality | Madison permit extraction, ADU classification, address-to-parcel match; New Berlin per D6 | `permits_observed` (local only), `permits_by_area_year` | Reconciled with the City's own ADU table; audited sample of matched and unmatched records |
| Conductor | shared schemas and validation code, integration, provenance, packet | Gate 2 packet | Owner review steps walked end to end |

## Independent review

A reviewing agent challenged the first draft and found three blockers: the mechanism's "share of rights" was undefined and double-counted the baseline; the worked example mixed paths and contradicted an open decision; and the planned small-area hiding rule would have blanked almost every map area. All three were repaired by moving to rights-class rates measured per one-unit detached home, redoing the example on one path with three cases, and adding "What you will actually see". It also found cross-document inconsistencies (Madison ADU counts from two sources, mismatched enums, a mislabeled New Berlin citation, an outdated "handbook unreachable" note); those are fixed or logged for Gate 2 reconciliation. Its re-check confirmed the rewritten scope and arithmetic, and found six new errors and several stale statements in the other documents (form-only reading conflicting with the class scheme, a parking claim stated as fact, mixed Madison sources, two unsupported coverage claims, the Madison ceiling argument reversing under rate levels, and a zero-effect check that could fail for Madison). All were fixed: a separate `forms_with_occupancy_limits` class, sourced Madison figures, reform set equal to baseline wherever classes match, and supersession notes in the interface and evidence documents.

## Deferred to Gate 2 (recorded so they are not lost)

- Address-to-parcel matching for Madison permits: match method and match quality are separate fields; tolerances will be written into the Gate 2 plan before match rates are evaluated.
- The Madison permit report requires session-based web-form runs; Gate 2 ships a cached, checksummed snapshot as the reproducible fallback.
- The Census API now requires a key; acquisition will default to keyless bulk files so a clean checkout runs without secrets.
- Count of parcels missing improvement value, by county.

## Known limitations at this gate

- Every uptake rate is descriptive evidence from other places; there is no causal Wisconsin estimate and no state-level Wisconsin reform to calibrate against.
- Madison's ADU rate depends on the period chosen (about twofold), and its 2026 pace already exceeds the proposed central rate.
- New Berlin's rules are a source lead (the code site blocked automated access) and its permit baseline will be assumed.
- No statewide record of local ADU rules or ADU permits exists.

## Recommendation

**Advance to Gate 2 once you decide D1–D8**, with any specific changes you name. The mechanism and contracts are, in my assessment, sound enough to acquire data against; the main risks are the unknown-rules workload and the schedule, both addressed by D3 and D7.
