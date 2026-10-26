# Parking: results of the repeal comparison (Gate 2, first full run)

Written 2026-10-26 by the parking conductor. Plan: [COMPARISON_PLAN.md](COMPARISON_PLAN.md), including deviations 1 and 2. Status: for owner review. These are not Gate 3 numbers.

## Answer

**In the three years after US places removed parking minimums for all housing, they did not permit measurably more homes than similar places that kept them.**
- **Average change:** the homes-weighted average change was −1.29 permits per 1,000 existing homes per year, against comparison places, across 24 repeal places. The bootstrap range (5th–95th percentile) runs from −3.68 to +2.33, so it includes zero.
- **Direction:** 9 of the 24 places rose faster than their comparison places, and 15 rose slower.
- **Apartments** (units in buildings of 2+ units): −1.60 permits per 1,000 homes per year, with a range of −3.59 to +1.20. Again 9 of 24 places rose.
- **Size and setting:** the data cannot tell city types apart. The best model by held-out prediction used city size and metro setting. It predicted only 5% better than one average for all places: a mean error of 4.81 against 5.07 permits per 1,000 homes per year. Both of its slopes have bootstrap ranges that include zero. No size cut-off (10,000, 20,000, 50,000 or 100,000 people) predicted better than one average.

## The sample

| Step | Places |
| --- | ---: |
| PRN places at the benchmark, adopted 2015–2022 | 46 |
| Not found in the Census permit place files (Wilmington NC, South Bend, 4 Michigan villages) | −6 |
| Ordinance check: weaker than the benchmark (Norman, Maumee, Camden), minimums restored in the after period (Central Falls), or no repeal event (Chattahoochee Hills) | −5 |
| Too recent once the effective date was used (San Jose, Anchorage), or missing permit years (Gastonia, Avondale Estates, Calumet) | −5 |
| **Included** | **30** |
| of which rated "near" by the ordinance check (separate arm) | 6 |
| **Main sample** | **24** |

The included places, their before and after rates, comparison places and effects are in `reference/parking_comparison_effects.csv`. The model comparison is in `reference/parking_comparison_models.csv`, and the estimates in `reference/parking_comparison_estimates.csv`. Script: `scripts/run_parking_comparison.py`.

## Points to note

- **West Allis, the in-state case, rose.** It permitted 2.63 units per 1,000 homes per year in 2017–2021 and 7.49 in 2023–2025. Its 216 comparison places in Wisconsin barely moved (8.93 and 9.03), so the effect is +4.76. The repeal came with a complete new zoning code, so this cannot be credited to parking alone.
- **Big cities mostly fell against their comparisons:**
  - San Francisco −4.43 (2019);
  - Minneapolis −8.09 (2021);
  - Lexington −4.46;
  - St. Paul −1.57 (2021);
  - Raleigh +7.02.
- **Small places swing widely.** Bastrop TX rose by +27.8 and Bandera TX fell by −25.9. Each has a few hundred to a few thousand homes, so they carry little weight.
- **"Near" arm (6 places),** reported but not pooled: Buffalo +0.78, Windham +8.12, Cambridge MD −6.68, Branson +3.86, Canandaigua +2.63, Seabrook −1.93.
- **Simultaneous rewrites:** 18 of the 24 main places repealed minimums as part of a wider zoning rewrite, by the check's broad flag. That leaves only 6 places without one, too few to test.

## What this means

This fits the other evidence:
- in Buffalo, stand-alone apartment buildings still built more parking than the old minimum;
- Ryan's point (AQ-046) that where low-parking development is seen as risky, developers keep building parking.

Over three years, a repeal on its own has not produced a measurable rise in permits. The largest average effect the data allow is about +2.3 permits per 1,000 homes per year.

What it cannot show:
- effects after year 3;
- effects in places where the minimum bound hard, which may be hidden in an average across places where it didn't.

## Decision for the owner

| Option | What the tool would show |
| --- | --- |
| **A (recommended)** | The central is no measurable change in permits. An upper case at the top of the range the data allow (+2.33 per 1,000 homes per year for all units, or +1.20 for apartments), labelled "if the effect is at the top of what the evidence allows". No lower case below zero, because a repeal never subtracts. |
| B | As A, plus a cost-based estimate (parking cost saved times a supply response) as a separate "what the economics suggest" line, clearly marked as modelled rather than observed. |
| C | Model city types separately anyway. Not recommended: the held-out test found no size or setting split that predicts better than one average. |
