# TOD no-reform pace model: results, rounds 1–4 (2026-10-31)

Plan: [PACE_MODEL_PLAN.md](PACE_MODEL_PLAN.md). Script: `scripts/run_tod_pace_loop.py`. Per-round tables: `reference/tod_pace_loop_round{N}[_seedS].csv`. Holdouts (Chicago, Madison, Bellevue) not used.

Score: median |log(predicted ÷ actual)| of 5-year homes built, over city-windows. Lower is better. 0.38 means typically about 46% off (e^0.38 = 1.46).

## Scores

| Round | Change | Held-out place: model (3 seeds) | Held-out later years: model (3 seeds) |
| --- | --- | --- | --- |
| 1 | Lot and tract traits only | 0.77 (1 seed) | 0.57 (1 seed) |
| 2 | + place's past permit pace (national permit survey) | 0.66–0.75 | 0.51–0.59 |
| 3 | Place pace as a starting level the lot model adjusts | 0.77–1.00 | **0.29–0.31** |
| 4 | Homes per lot instead of per acre (fixes round 3's worst miss) | 0.66–0.75 | 0.56–0.71 |
| — | **Benchmark: same pace as before (permit survey)** | **0.58** | 0.38 |
| — | Flat average homes per acre | 1.39 | — |

The held-out place test has 30 city-windows. The later-years test has only 4 (the no-reform cities' after windows): too few to weigh (audit).

## Findings

1. **For a place's total, the permit survey's "same pace as before" is the best no-reform estimate so far.** The lot model beat it only on the later-years test in round 3, which has 4 data points. It never beat it on held-out places.
2. **The lot model's value is where homes go inside a place, not how many.** This supports the round-8 design: place total from the permit survey; lot model splits it.
3. **Station areas get more than their share of existing homes.** Correction (same day): the first table used rail and rapid stops only (½ mile). The tool's main case also counts 15-minute bus stops (¼ mile); `reference/tod_stops.csv`. Under the main case the gap is much smaller:

| Place and definition | Share of 2010 homes | Share of new homes, before window | Share of new homes, after window |
| --- | ---: | ---: | ---: |
| Milwaukee, main case | 72.0% (171,644 of 238,237) | 98.6% (8,523 of 8,648) | 97.3% (5,479 of 5,633) |
| Madison (whole city), main case | 81.5% (81,409 of 99,944) | 93.7% (8,007 of 8,542) | 94.7% (12,972 of 13,703) |
| Milwaukee, rail and rapid only | 12.7% (30,298 of 238,237) | 57.4% (4,964 of 8,648) | 41.6% (2,341 of 5,633) |
| Madison, rail and rapid only | 48.0% (47,943 of 99,944) | 63.7% (5,440 of 8,542) | 67.3% (9,219 of 13,703) |

   Windows: Milwaukee 2013–2018 and 2020–2024; Madison 2011–2022 and 2018–2025 by area. The two cities hold 82% of the main case's homes near stops. Under the main case, station areas got about 1.15× (Madison) to 1.35× (Milwaukee) their share of homes. So the 14,464 baseline may be low by roughly 15–35%, not 1.4–4×. Owner decision; no number changed.

## Bad data and code found and fixed

| Round | Problem | Fix |
| --- | --- | --- |
| 1 | Columbus and Kansas City 2010 homes about 5× too high: block homes were shared over the 20% sample of lots, then weighted by 5 | Each lot's share divided by the sample weight (plan item 63); both lot tables patched; lot model also used this trait |
| 3 | Kansas City: 600-acre farm and park parcels predicted thousands of homes (homes per acre × acres) | Round 4 predicts homes per lot |
| 1–4 | Most homes come from a few big projects: the top 10 lots hold 30–59% of a no-reform city's 5-year homes | Not a bug. Explains why lot sums are noisy |
| — | Milwaukee's permit survey under-counts apartments (parking thread's finding); our lot data agrees with the property file | Benchmark for Milwaukee is too low; parking's corrected series should be used |

## Data left out (not in every state)

See the plan's table: zoning levels, city property records, building age, land values, lot-level permit history, lot use.
