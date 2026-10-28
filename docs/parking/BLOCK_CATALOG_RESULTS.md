# Parking: block-by-block catalog, results

Written 2026-10-28 by the parking conductor. Plan: [BLOCK_CATALOG_PLAN.md](BLOCK_CATALOG_PLAN.md), committed before counting. Scripts: `scripts/run_parking_block_catalog.py` (reuses TOD's block points: 2000 Summary File 1 headers, 2010 and 2020 TIGER blocks) and `scripts/run_parking_older_towns.py`. Outputs: `reference/parking_block_catalog.csv`, `reference/parking_older_towns.csv`.

## Answer

**With a decade before the reform added, Seattle's promising result mostly disappears.**
- Seattle's urban villages were already growing about as much faster than the rest of the city in 2000–2010 (+24.2 homes per 1,000 a year) as they did in 2010–2020 (+26.2).
- The change in change is +2.0 (90% range −17.5 to +21.9). The 2012 parking reform added little that can be seen.
- The other area cases are small, noisy and lean positive. None is clearly above zero.

## Catalog

The measure is homes added per 1,000 existing homes per year, reform area minus comparison area. The change in change is the 2010s gap minus the 2000s gap.

| Case | Share of 2010s under reform | Homes in reform area, 2000 / 2010 / 2020 | Gap 2000s | Gap 2010s | Change in change (90% range) | Same, net homes per acre per decade |
| --- | ---: | --- | ---: | ---: | --- | ---: |
| Seattle urban villages (2012) | 0.76 | 46,537 / 60,039 / 78,975 | +24.2 | +26.2 | **+2.0 (−17.5 to +21.9)** | +0.89 |
| Minneapolis near-rail cut (2015), 32 stations, downtown left out | 0.48 | 14,907 / 17,074 / 21,951 | +12.0 | +22.9 | +10.9 (−41.0 to +59.3) | +0.55 |
| Hayward, South Hayward BART (2011) | 0.88 | 2,748 / 2,740 / 3,199 | −3.4 | +10.9 | +14.3 (−84.9 to +120.7) | +0.95 |
| Fremont, Warm Springs (2015) | 0.48 | 78 / 5 / 225 | — | — | per 1,000 homes not meaningful (5 homes in 2010) | +1.05 |
| *Cited from TOD:* Chicago TOD ordinances (2013, 2015) | | | | | | −6.25 (−16.5 to +3.7) |
| *Cited from TOD:* Salt Lake City station areas (2010) | | | | | | +2.15 (−1.2 to +5.6) |

TOD's catalog also has Seattle station-area upzonings that sit inside urban villages: Roosevelt, +28.8 net homes per acre (+8.1 to +51.7), and North Beacon Hill and Othello, +17.3 (+1.6 to +32.5). Those areas got the 2012 parking change and an upzoning next to light rail. The villages as a whole got the parking change and show little. This points to upzoning and rail, not parking alone, as what moved building there.

**How to read the ranges.**
- Blocks are resampled within each area and year, as in TOD's 2000 census work. The plan said census tracts, but the 2000 block points carry no tract code. This is noted as a change from the plan.
- The ranges are wide because each case is one area.

## Older repeals through the permit route

Before = 5 years before the repeal; after = years 1–3 after. Rates are permits per 1,000 existing homes (2000 census) per year.

| Town | Repeal | Permits before → after (5 years / 3 years) | Rate before → after | Comparison before → after | Effect |
| --- | --- | --- | --- | --- | ---: |
| Ozawkie, Kansas (216 homes) | 2007 | 17 → 3 | 15.7 → 4.6 | 5.8 → 2.9 | −8.2 |
| Westmoreland, Kansas (293 homes) | 2007 | 70 → 3 | 47.8 → 3.4 | 5.6 → 5.1 | −43.9 |
| Philip, South Dakota (424 homes) | 2009 | 14 → 2 | 6.6 → 1.6 | 14.4 → 5.5 | +3.8 |
| Brownville, Nebraska | 2004 | — | — | — | not matched in the 2000 Gazetteer |

These towns issue a few permits a year, and their after-years fall in the 2008–2011 housing crash. The group average, −13.9, mostly reflects Westmoreland's busy years before the repeal. Like the 9 census-only towns (−4.3 homes per 1,000 a year against comparison places), they show no sign of more building. They are too small to weigh.

## What it means

- **The block-level, Seattle-type cases do not add up to a clear parking effect** once their own past trends are netted out. The cases that do show strong gains combine parking relief with upzoning near rail.
- **This supports the scenario as it stands:** no measurable change from a statewide repeal on its own. The high end allows for some effect in denser, transit-served places.
- **Nothing in the tool changes.**

## Changes from the plan

- **Bootstrap:** blocks are resampled, not census tracts, because the 2000 block points have no tract code (see above).
- **Fremont:** only 5 homes were in its reform area in 2010, so it is reported per acre only.
