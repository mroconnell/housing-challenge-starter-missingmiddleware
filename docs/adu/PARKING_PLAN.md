# ADUs with and without parking requirements: plan (draft for the audit, not locked)

Written 2026-11-11 at Ryan's request (parking thread, 01:03 UTC): "do ADUs with or without parking and … read the Sightline research too". No count has been run.
- **No expected direction.** Removing parking rules could raise ADU building, or change little where owners build parking anyway.
- **Approvals.** The audit reviews this plan before any run, and Ryan decides any tool change.

## Why it matters for Wisconsin

- **What the Wisconsin law does.** The modelled law allows an ADU with **no extra parking**.
- **What the evidence states did.** Most of the 8 statewide-law states the model learns from **capped** ADU parking at 1 space instead (reference/statewide_states_laws.csv):

| Parking rule in the state law | States |
| --- | --- |
| No space beyond the house's (like Wisconsin's law) | Oregon (from 2020), Maine |
| A cap of 1 space, or none near transit | California, Washington, Massachusetts, Rhode Island (1 per bedroom), Utah (may require 1), Vermont (1 per unit in sewer areas, from 2024) |

- **The risk.** If parking requirements hold ADUs back, typical adoption may understate a no-parking law.
- **The question.** How much does "no parking at all" add over "at most 1 space"?

## What Sightline's research shows

Read 2026-11-11. The sources and figures are in the helper's notes, summarised here.

- **No parking-only effect size.** Every before/after case removed parking along with other rules: Seattle 2019, California 2019, Tacoma, Tigard and Portland.
  - Seattle's 2019 change also dropped owner occupancy, allowed 2 ADUs per lot and cut the minimum lot size.
  - Seattle's ADU permits went from 245 (2018) to 988 (2022), 4.0×. That is the whole package, not parking.
- **Feasibility and cost evidence:**
  - Kent, WA: 95% of single-family lots can't fit one more space (architect's site analysis).
  - $4,000–$10,000 per space, about 10–20% of a small ADU's cost.
- **Behaviour with no mandate.** About 25–45% of ADUs still keep their residents' cars off-street (Seattle, Portland surveys). In two small Washington cities, 71–88% of new ADUs added no space.
- **Cross-section.** California cities with frequent ADU applications were more likely to have no parking standard (31% against 13%; Terner Center). The author says this is not causal.

## What our data can and cannot test

- **Within California: not feasible.** The 2019 ordinance coding has 54 places with an extra-parking rule and only 3 without (16 unknown). That is too few for a comparison.
- **Seattle's 2019 change: report only.** Parking and owner occupancy were removed together, so the two can't be separated.
- **State level: descriptive only.** 2 states without a parking rule against 6 with a cap.

## Tests

**P1. State level, descriptive.**
- Compare the A3 held-out misses (log of predicted ÷ actual, already computed) for the 2 no-parking states against the 6 capped states.
- Report each state's miss and the two groups' means.
- No interval and no pass rule: 2 against 6 cannot test anything.
- Label it "too few states to tell".

**P2. Bundled before/after, report only.**
- List the dated local changes that removed ADU parking, with each one's other simultaneous changes and its permits before and after:
  - Seattle 2019 (our series);
  - Austin 2015, no parking near corridors (our series);
  - Tacoma, Tigard and Portland (Sightline's figures).
- Each is labelled "package effect; parking not separable".

**P3. A bounded what-if for Wisconsin, on How sure only.**
- **Share of projects a 1-space cap blocks.** The Kent feasibility figure (95%) bounds how many lots can't fit a space. The share of ADUs that keep cars off-street with no mandate (25–45%) bounds how many would build a space anyway. The lower bound is 0, and the upper bound comes from those two figures. All of it is fixed now, before the run.
- **The what-if.** The extra ADUs if Wisconsin's no-parking law adds that share on top of typical adoption, applied only to the capped states' part of the pooled level. It is shown as a labelled what-if line, never as the range.
- **Not a measured effect.** It is built from feasibility and behaviour figures, not from a measured parking effect. It says so beside the line.

## Outputs

- `docs/adu/PARKING_RESULTS.md`.
- `reference/adu_parking_*.csv`.
- No tool change without Ryan's OK.

## Open for the audit

- Whether P3 is defensible at all, or should be words only. My default is a what-if line on How sure, with its bounds stated.
- Whether P1 should be dropped as uninformative.
