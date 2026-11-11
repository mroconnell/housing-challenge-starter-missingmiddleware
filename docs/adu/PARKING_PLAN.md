# ADUs with and without parking requirements: plan (locked 2026-11-11 after the audit's review)

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

## Tests (as locked after the audit)

**P1. State level: not run (its numbers were already published in A3).**
- One line, labelled as already seen: "The two no-parking states sit inside the capped states' spread of misses; 2 against 6 cannot tell."
- Oregon's miss is +0.119 and Maine's −0.129, against the capped states' −0.088 to +0.187.

**P2. Bundled before/after, report only.**
- Dated local changes that removed ADU parking, each with its other simultaneous rule changes and its permits before and after.
- Each is labelled "package; parking not separable".
- Austin 2015 lists all of its ADU rule changes.

**P3. Words only, no line (audit).**
- The figures do not give a share of projects that a cap blocks. Any formula linking them would be a free choice.
- The pooled model already includes Oregon and Maine and finds one common level.
- Proposed How-sure text, pending Ryan's OK: "Wisconsin's modelled law needs no extra parking. Six of the eight evidence states allowed up to one space. No study separates parking from the rest of each package. Oregon and Maine, which need no extra space, sit within the other states' range. So the effect of dropping the last space is unknown: it could raise ADU building, or change little where owners add parking anyway."

## Outputs

- `docs/adu/PARKING_RESULTS.md`.
- `reference/adu_parking_*.csv`.
- No tool change without Ryan's OK.

## Audit

Reviewed 2026-11-11 (`/mnt/project-files/audit/adu_parking_plan_review_2026-11-11.md`). Accepted with the changes above.
