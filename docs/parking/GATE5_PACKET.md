# Parking scenario: Gate 5 packet (statewide MVP)

Written 2026-10-27 by the parking conductor, for Ryan. Status: ready for review. It builds on Gates 1–4 (AQ-046 and AQ-048; Gate 4 accepted 2026-10-27).

## 1. What this gate decides, and the answer

Gate 5 decides whether the parking scenario is good enough to submit as one of the challenge's benchmark scenarios. **Recommendation: yes.**

It answers the benchmark question with a clear, evidence-based "little or no measurable change", plus a stated high end. It states the required assumption about the parking developers would still build. It reconciles to the state, reproduces from a fresh copy of the repository, and every number on its screens has been checked independently.

## 2. Checks done for this gate

| Check | Result |
| --- | --- |
| Reconciles to the state | The places and the unallocated row add to the published state total in every year and building size, plus the labelled Milwaukee adjustment. Places, counties and districts add to the statewide high end. The bundle's validation runs 6 checks; all pass. |
| Fresh copy | A clean clone from GitHub passes all 500 Python tests, and rebuilds the parking bundle from the committed reference tables to the same run id. A full rebuild from raw data follows [REBUILD.md](REBUILD.md); the baseline build now stops if the Milwaukee property file is missing, rather than silently dropping the adjustment. |
| Tool tests | The full Playwright suite passes, including the parking test, which reads every checked number from the bundle. |
| Independent reviews | Gate 2 (method and numbers), Gate 3 (scenario and baseline) and Gate 4 (every displayed number). All findings were fixed. |
| Data rules | Every source is fetched by script, with URL, date and SHA-256 recorded, and every licence is listed in DATA_PROVENANCE and DISCLOSURES. No personal data are used: owner fields in the Milwaukee property file are never read. The parking scripts read only year built and unit count; the ADU baseline script also reads street addresses to match permits, and addresses are not published. |
| Benchmark requirement | The developer-provided parking assumption is stated on the Why screen and in the Model & Assumptions section. |
| Combined view | Parking publishes its additions by place, split near transit stops and elsewhere, for the combined TOD + parking view. TOD builds the combined bundle once its own numbers exist. |

## 3. Rubric self-check (weights from the challenge handbook)

| Criterion | Weight | How the parking scenario meets it | Weak point |
| --- | ---: | --- | --- |
| Transparency | 30% | The comparison was registered before results were read, with deviations recorded. Every place's before and after rates are on screen, and the data-versus-judgment trace is shown. | The ordinance checks rest on secondary copies of the code where city sites blocked access (confidence is recorded for each place). |
| Replicability | 25% | Uses national Census data for every US place, so another state can run it unchanged. Data are fetched automatically, the bundle rebuilds byte for byte, and tests run on a fresh clone. | The Milwaukee adjustment is Wisconsin-specific (the published series is the sensitivity case). |
| Usability | 20% | The same seven screens as ADUs, with plain case names, a brief, and a place search. | No map yet; Where is a ranked table. |
| Soundness | 15% | Matched comparison places, checks against each ordinance, leave-one-out model choice, a resampled range, and stability checks. | 24 places, most repealing alongside a zoning rewrite; the places chose to repeal (self-selection). |
| Policy insight | 10% | A clear and counter-intuitive finding, why it happens (developers keep building parking), and what it means for Wisconsin. | Rents and parking supply are out of scope. |

## 4. Owner review steps

1. Read section 1, and the Brief tab at http://127.0.0.1:4199/#/parking/brief (after `PORT=4199 bash scripts/run_tool.sh`).
2. Read [MODEL_AND_ASSUMPTIONS_PARKING.md](MODEL_AND_ASSUMPTIONS_PARKING.md), the parking section for the submission's Model & Assumptions document.
3. Decide G5-1 and G5-2.

**Self-assessment.** I ran the fresh-clone check and the test suites myself. The independent review found three gaps, all outside the parking files:
- the README does not yet mention parking;
- the Policy Scenario Comparison document is still empty;
- the shared Model & Assumptions document has no parking section yet.

The ADU conductor owns those documents and is assembling them from my parking text, pending your approval of that arrangement. The rubric row I am least sure of is usability: legislators may expect a map, and the Where tab's table answers "where" but is less immediate.

## 5. Decisions requested

| # | Decision | Recommendation |
| --- | --- | --- |
| G5-1 | Is the parking scenario good enough to submit? | Yes |
| G5-2 | Add a map to the Where tab (reusing the ADU map) before submission? | Yes, if time allows after TOD and the combined view. The table already answers the question. |

## 6. Limitations carried into the submission

- The evidence covers three years after repeal, in 24 places.
- 18 of the 24 places repealed parking minimums as part of a wider zoning rewrite.
- The high end is spread by homes, not by where minimums bind.
- Milwaukee's 2025 apartments are missing from the baseline.
- North Carolina's statewide law has no data yet.
- Whether evidence from cities that repealed by choice may stand in for a statewide law is still open: office-hours question 26.
- Seattle, Minneapolis and Champaign are cited as leads only; Buffalo is the one study read in full.
