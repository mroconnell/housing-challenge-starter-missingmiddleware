# Parking: per-project (mechanism) estimate, plan

Written 2026-11-01 by the parking mechanism thread, before any result was computed. Changes after this commit are logged at the bottom as deviations. Results will go in `MECHANISM_RESULTS.md`. Script: `scripts/run_parking_mechanism.py`. This is a candidate line for Ryan; it does not change the tool or any other scenario.

## Question

If Wisconsin removes parking minimums statewide in 2027, how does each project change, and what does that add up to over 2027–2031?

Past tests counted permits city by city. Counts swing 30–50% with the market, so a parking effect could not be told from noise (central 0; high end 19,937 homes over 2027–2031). This plan looks inside projects instead:

- **Intensive margin:** how each project changes (homes per building, parking per home, cost per home).
- **Extensive margin:** how many projects happen. This is left to the baseline (122,619 homes over 2027–2031), except through the cost route in Part B.

## Two routes, kept apart

| Route | What it measures | Data | Can it be negative? |
| --- | --- | --- | --- |
| A. Measured project size | Change in homes per apartment building, and small-building permits, after real repeals | Census permits (buildings and units by building size), 76 repeal places | Yes |
| B. Cost chain (mechanism) | Spaces not built × cost per space ÷ cost per home × how much building responds to cost | Published project studies, Wisconsin codes, Census permit values, Wisconsin land values | No, by construction (stated as a limit, not a finding) |

A and B are not added together. B's supply response already covers bigger projects and extra projects, so adding A would count the same homes twice. A is the check on B.

## Part A: measured project size (Census permits)

**Places.** The 76 repeal places in `reference/parking_expanded_effects.csv` (status "included"), with their repeal years and the same before and after windows as the headline comparison. Comparison places are chosen the same way (same state and 0.5–2× population, widening as in `missing_middleware/parking/comparison.py`).

**Outcomes** (from the Census Building Permits Survey place files, 2012–2025, which give buildings and units by building size):

| Id | Outcome | Unit | Weight |
| --- | --- | --- | --- |
| A1 | Homes per building in 5+ unit buildings | Change in log(homes ÷ buildings), after minus before, repeal place minus comparison places. Shown as a percent change. | Number of 5+ unit buildings in the place, before plus after |
| A2 | Homes in 2–4 unit buildings (small-lot projects) | Permits per 1,000 existing homes per year, change in change | Existing homes × after-years (as the headline) |
| A3 | Number of 5+ unit buildings | Buildings per 1,000 existing homes per year, change in change | Existing homes × after-years |

A1 needs at least 2 buildings of 5+ units in the place in each window, and at least 2 in the comparison group in each window. Places that fail are listed, not dropped silently.

**Noise check (placebo).** For each repeal place, up to 40 never-reformed places in the same Census division at 0.5–2× its population get a fake repeal in the same year (seed 20261101). Each is compared with its own comparison places. 20,000 fake sets each take one random partner per real place. The real average is placed in that distribution. This also answers a pre-set question: **is project size less noisy than permit counts?** The ratio of the placebo 5th–95th width to its mean level is compared between A1 and the headline all-units outcome.

**Held-out test.** Leave one state out at a time. Predict each left-out place with the weighted average of the places in other states, and compare its weighted mean absolute error with predicting zero. A1's average counts as a measured effect only if (1) the real average is outside the placebo 5th–95th range **and** (2) the leave-one-state-out average beats zero.

**Wisconsin conversion (route A).**
- A1: percent change × Wisconsin 5+ unit baseline homes where minimums still bind (see Part C), over 2027–2031. This assumes the number of apartment buildings stays at baseline.
- A2: effect × existing homes where minimums bind ÷ 1,000 × 5 years.
- Range: the leave-one-out 5th–95th percentile of the average, and the placebo range beside it. If neither test passes, A is reported as "no measurable change in project size", with its range as the evidence-based limit of the intensive margin.

## Part B: cost chain (mechanism)

For each Wisconsin municipality piece and building size:

> extra homes = baseline homes where minimums bind × supply response × (spaces saved per home × cost per space ÷ total cost per home)

A cost cut of c% of a project's total cost works like a c% higher sale price for the builder, so homes rise by about (supply response × c).

| Piece | Central and range (draws) | Evidence |
| --- | --- | --- |
| **s, share of old required spaces not built** (all projects pooled) | Each draw picks one of four project studies at random: Buffalo 0.21 (1,942 of 2,444 required spaces built; Hess and Rehler 2021), Los Angeles transit program 0.33 (151 of 224.5; `LA_TOC_RESULTS.md`), Seattle 0.40 (about 40% fewer than required; Gabbe, Pierce and Clowers 2020, secondary summary to be checked), Champaign 0.54 (1,833 of 3,975; Sohoni and Lee 2024) | Project-level studies |
| **m, old minimum spaces per home** | Home-weighted average of the multifamily minimum in the 10 municipalities with the most projected 5+ unit homes (57% of the 5+ baseline), looked up in their codes in this run; range = lowest to highest of the 10. If a code cannot be read, it is listed and left out. | Municipal codes |
| **Cost per space** | Urban context (foundation `context = urban`): structured, uniform $29,900 (WGI 2024 national median) to $52,000 (UCLA 2026, above-ground average of 17 cities). Other contexts: surface, construction uniform $1,500–$10,000 plus land: 330 sq ft per space (space plus aisle) × the municipality's median assessed land value per sq ft of residential and commercial parcels (Wisconsin statewide parcels V9, 2023). | Cost surveys; Wisconsin parcels |
| **Total cost per home** | Census permit value per home in Wisconsin 5+ unit buildings, 2023–2025, statewide (hard cost) ÷ hard-cost share uniform 0.60–0.67 (Terner Center 2020: hard costs are more than 60% of total; its example 65%). The same for 2 and 3–4 unit buildings with their own permit values. | Census permits; Terner Center |
| **Supply response** (percent more homes per percent higher net price) | Triangular 0.11 / 0.30 / 0.59 (Baum-Snow and Han 2024: 0.3 average for housing units; 0.11 at the city centre, 0.59 halfway to the metro edge) | Published estimate |

Building sizes:
- **5+ units and 2–4 units:** the chain above. The project studies are of larger projects, so the 2–4 unit result is flagged as untested.
- **1 unit:** no change, on evidence: the measured 1-unit effect in the 76 repeal places is +0.03 permits per 1,000 homes per year (−0.74 to +0.76; `SIGNAL_RESULTS.md`), and Milwaukee and many other codes already exempt houses. This is not a logical floor.

**Draws.** 10,000 draws (seed 20261101). Report the 5th, 50th and 95th percentile of the Wisconsin total, and each piece's share of the spread (rerun with each piece held at its central value).

**Held-out tests for B.**
1. **Leave one study out** for s: predict each study's s from the mean of the other three. Report each miss. If the largest miss is wider than the draw range, the range is widened to cover it (pre-set rule) and this is reported.
2. **Against real repeals:** B's implied percent change in 2+ unit permits in the 76 repeal places (each with its own before-rate; Buffalo left out because it is a source) is compared with the measured 2+ unit effect. Score: weighted mean absolute error of B against predicting zero. B's predicted changes will probably be small next to the noise, so this test may not separate them. If so, that is reported as "uninformative", not as a pass.
3. **Against Part A:** is B's statewide percent inside A's 5th–95th ranges?

## Part C: where Wisconsin minimums still bind

- **Already at the benchmark, no change:** municipalities rated "at" in `reference/parking_reform_taxonomy.csv` (Algoma, Brodhead, Cottage Grove, Fitchburg, Franklin, Gilman, La Crosse, Omro, West Allis), plus Pewaukee city and Roberts (guidance only, no mandates). This is evidence (their law already has no minimums), not a floor.
- **Madison:** the share of new 5+ unit homes (built 2015–2024, Madison tax parcels) in districts with no minimums: downtown districts (DC, UMX, UOR, DR1, DR2) and the TOD overlay (`data/raw/madison_tod/tod_boundary.geojson`; adopted 2023, so applied to the baseline). That share is removed.
- **Milwaukee:** the share of new 5+ unit homes (built 2015–2024, MPROP) in downtown C9 districts, which have no minimums, is removed. Planned developments (PD) negotiate parking and are kept as binding.
- **Everywhere else:** binding. Partial exemptions (elderly housing, studios) are kept as binding.

## Output

1. Per-project effect, with range: homes per apartment building (A1), parking spaces per home (s × m), cost saved per home ($ and percent), and the percent more apartments.
2. Wisconsin net over 2027–2031, lower / central / upper, for route A and route B, beside the tool lines (central 0; low candidates −15,303 and −18,100; high end 19,937).
3. Pre-set use: route B is offered as a candidate line only if test B1's misses fit inside its range and B is no worse than zero in test B2. Otherwise it is shown as evidence only. Route A follows the two-part rule in Part A.

## Rules

- Every number states its unit, numerator and denominator.
- Runs are flagged, not stopped. Before each run, flag inputs far outside the evidence; after, trace the largest miss.
- Long steps run detached on this Mac (`nohup caffeinate -i`), with a checkpoint after each step in `data/interim/parking_mechanism/`.
- No new dependencies. If one is needed, ask Ryan first and run the licence check.
- No zero floors without evidence; the 1-unit and already-exempt zeros above cite theirs.

## Deviations

1. **Old minimums (m), before results.** Code lookups for the top 10 municipalities mostly failed (codes not readable online). Instead, m comes from one 2025 staff compilation of multifamily minimums that lists 17 Wisconsin cities (Mankato, MN Planning Commission packet, 2025-08-27, "Parking Information – Other Communities"). La Crosse is dropped (repealed in 2024). Bedroom-based rules use 1.5 bedrooms per home (half studio or one-bedroom, half two-bedroom; assumed). Places not listed take, in each draw, one value picked at random from the listed cities other than Madison and Milwaukee. The plan's "top 10 by 5+ homes" would also have included Fitchburg and West Allis, which have no minimums.
2. **Madison's TOD overlay, before results.** Whether the 2023 overlay removes minimums could not be confirmed. Madison's exempt share is drawn between downtown districts only (11.4% of new 5+ unit homes) and downtown plus the overlay (44.2%).
3. **Land values.** 63% of 2+ unit baseline rows matched a municipality in the statewide parcel file by name and county. The rest take their county's median (flagged in `parking_mechanism_where_binding.csv`).
Note (audit, 2026-11-01): deviations 1 and 2 were decided before results but committed in the same commit as the results (4a4448d), so their timing cannot be checked from git.

4. **Unplanned checks, after results.** Austin carries 31% of A1's weight, so A1 was re-tested unweighted, as a median, without Austin, and as each place's own change without comparison places (`parking_mechanism_part_a_robustness.csv`). These are checks, not replacements for the pre-set result.
