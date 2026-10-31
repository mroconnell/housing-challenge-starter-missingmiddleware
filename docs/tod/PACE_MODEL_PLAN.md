# TOD no-reform pace model: plan (logged before any run)

Written 2026-10-31 at the owner's request (go given 14:34). Candidate 2 in [WHERE_HOMES_GO_CANDIDATES.md](WHERE_HOMES_GO_CANDIDATES.md).

## Question

How many homes get built on a lot over 5 years **with no TOD reform**? Summed over lots, this is a place's no-reform pace. It is "model 1" in the owner's two-model framing; the share model / law-on model is "model 2".

## Training rows (lot-windows with no TOD rules in force)

1. **Before window of every lot** in every non-holdout city (the 6 years before each reform; untreated by definition).
2. **After window of the no-reform cities only** (Madison outside overlay, Milwaukee, Columbus, Kansas City). In reform cities the after window is left out for every lot, including comparison lots, because building may move between them (audit advice, 14:36).

Holdouts Chicago, Madison and Bellevue are never fitted on or scored in the loop (same rule as plan item 49).

## Traits: only data any state has

- Lot: acres, width, 2010 census-block homes shared to the lot, distance to rail or rapid stop (or "none").
- Census tract (ACS 5-year): the 91 `v_` variables, rent, value, income.
- Place (round 2 on): the place's own permits per year from the national Census Building Permits Survey, in the years before the window, per 2010 home; place size.
- Not used: city zoning levels, city permit history at lot level, land values (not in every state), anything from the window being predicted.

## Outcome and tool

Two parts (audit advice): chance the lot builds anything in 5 years, times homes per acre if it builds, times acres. Fast tool: histogram gradient boosting. Three seeds per round.

## Two held-out tests

1. **Held-out place:** leave one city out; predict both its windows.
2. **Held-out later years (forward):** fit on before windows only (every city, including each no-reform city's own); predict the no-reform cities' after windows. This is the test closest to forecasting 2027–2031.

## Scores (no pass/fail; owner item 42)

For each city and window: predicted total homes vs actual, also as homes per 1,000 existing homes per year. One summary score, fixed now: median |log(predicted ÷ actual)| over the city-windows of each test. The worst miss is traced to data or code before the model changes.
Baselines:
- **Flat:** training cities' average homes per acre × acres.
- **Permit survey pace:** the place's permits per year in the 5 years before the window (national file) × 5 × (study area's 2010 homes ÷ place's 2010 homes).

## Checks each round

Units table, sanity flags, a data check of lot sums vs the permit survey for whole-city no-reform cities, and an "ask why" on the biggest misses. Checks flag only; they never stop a run.

## Comparison with parking and ADU

The place totals (permit survey pace and model) are sent to the parking and ADU threads, which are building the same no-reform model at city and state level.

## Data left out because not every state has it (owner asked for this list)

| Left out | Why not in every state |
| --- | --- |
| Zoning level before and after (floor area, height) | Each city codes it differently; no statewide zoning map in most states |
| Homes on the lot from city property records | Only some cities record it; 2010 census-block homes used instead |
| Building age and building-to-land value | Only in some city or county files |
| Land and lot market values | Assessor files differ by state; some are not market values |
| City permit history at lot level as a trait | Needs geocoded city permits; the national permit survey (place level) used instead |
| Lot use (residential, commercial, industrial) | 78% "unknown"; coded differently by city |
| Reform-area traits (group, shares) | Not a no-reform trait |
