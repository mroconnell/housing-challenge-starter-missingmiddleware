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

   For the write-up (audit): under the main case, station areas already get 94–99% of new homes in Milwaukee and Madison, so a share-based TOD effect has little room to move there. A narrower benchmark definition (plan item 61, option a) would give it room.

## Bad data and code found and fixed

| Round | Problem | Fix |
| --- | --- | --- |
| 1 | Columbus and Kansas City 2010 homes about 5× too high: block homes were shared over the 20% sample of lots, then weighted by 5 | Each lot's share divided by the sample weight (plan item 63); both lot tables patched; lot model also used this trait |
| 3 | Kansas City: 600-acre farm and park parcels predicted thousands of homes (homes per acre × acres) | Round 4 predicts homes per lot |
| 1–4 | Most homes come from a few big projects: the top 10 lots hold 30–59% of a no-reform city's 5-year homes | Not a bug. Explains why lot sums are noisy |
| — | Milwaukee's permit survey under-counts apartments (parking thread's finding); our lot data agrees with the property file | Benchmark for Milwaukee is too low; parking's corrected series should be used |

## Data left out (not in every state)

See the plan's table: zoning levels, city property records, building age, land values, lot-level permit history, lot use.

## Allotment by stop type (owner ask, 16:05; kept for the benchmark-definition decision)

Table: `reference/tod_stop_type_allotment.csv`, one row per city and stop band. Each lot is placed in its first matching band, in this order: rail/rapid within ¼ mile, rail/rapid ¼ to ½ mile, 15-minute bus within ¼ mile, 15-minute bus ¼ to ½ mile, 20-minute bus (same two rings), then not near a major stop. Stops come from `reference/tod_stops.csv`. New homes are on a 5-year basis.

| City | Stop band | Share of 2010 homes | Share of new homes, before | Share of new homes, after |
| --- | --- | ---: | ---: | ---: |
| Milwaukee | Rail/rapid, within ¼ mi | 7.8% | 41.0% | 27.8% |
| Milwaukee | Rail/rapid, ¼–½ mi | 4.9% | 16.4% | 13.8% |
| Milwaukee | 15-min bus, within ¼ mi | 59.3% | 41.2% | 55.7% |
| Milwaukee | 15-min bus, ¼–½ mi | 17.4% | 1.2% | 0.8% |
| Milwaukee | 20-min bus, within ½ mi | 10.6% | 0.2% | 2.0% |
| Madison | Rail/rapid, within ¼ mi | 24.8% | 48.8% | 40.5% |
| Madison | Rail/rapid, ¼–½ mi | 23.2% | 14.9% | 26.8% |
| Madison | 15-min bus, within ¼ mi | 33.5% | 30.0% | 27.4% |
| Madison | 15-min bus, ¼–½ mi | 17.4% | 5.4% | 1.2% |
| Madison | Not near a major stop | 1.2% | 0.8% | 4.2% |

Years: Milwaukee before 2013–2018, after 2020–2024. Madison varies by area: before 2011–2022, after 2018–2025. Counts are in the CSV.

Reading: rail and rapid stops take two to five times their share of homes. Lots within ¼ mile of a 15-minute bus roughly match their share. Lots ¼ to ½ mile from a bus stop get almost nothing.

## Re-base look (owner, 16:09: "let's see what TOD looks like rebased"; not applied)

`scripts/run_tod_rebase_check.py` → `reference/tod_rebase_check.csv`. Each place's baseline near stops is multiplied by the measured ratio of new-home share to existing-home share (main-case stops). The ratios are Milwaukee 1.35, Madison 1.16, and 1.28 elsewhere (both cities pooled; range 1.15–1.37). A share cannot go above 100%.

| | Today | Re-based |
| --- | ---: | ---: |
| Homes near stops without the law, 2027–2031, central | 14,464 | 17,597 (17,322–17,885 from the share range) |
| Pace range (low–high) | 8,386–21,874 | 10,201–26,619 |
| Typical TOD effect, as a share of the baseline | 2,509 = 17.3% | 2,509 = 14.3% |

The extra homes (171 / 2,509 / 17,148) do not change, because they are built on existing homes.

### Reconciled re-base (audit sweep, 16:13)

Madison's share near stops was 62.8% in the tool and 81.5% in the lot data. The cause was the denominator, not the stops. Using the Wisconsin lot table with 2020 homes and the same stop list, Madison has 79,033 homes near stops; the tool has 80,609. But the lot tables leave out the city's outer areas: 112,231 of Madison's 128,430 homes in 2020.

Recomputed on one stop list (main case), 2020 homes and whole-city denominators, homes built 2019–2024:

| City | Share of 2020 homes near stops (tool) | New homes near stops, 2019–2024 | Ratio |
| --- | ---: | ---: | ---: |
| Milwaukee | 68.2% (175,633 of 257,614) | 95.0% (6,236 of 6,566; property file, by year built) | 1.393 |
| Madison | 62.8% (80,609 of 128,430) | 76.9% (11,739 of 15,261; permits, by permit year) | 1.226 |
| Elsewhere (**assumption**: both cities pooled) | 66.4% | 82.4% | 1.240 (range 1.226–1.393) |

Re-based baseline near stops, 2027–2031: **18,322** (share range 18,297–18,598; pace range 10,623–27,715). This replaces the earlier 17,597.
