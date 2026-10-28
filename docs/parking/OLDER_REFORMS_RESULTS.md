# Parking: Seattle 2012 and Portland 2002 transit-area reforms, results

Written 2026-10-28 by the parking conductor. Plan: [OLDER_REFORMS_PLAN.md](OLDER_REFORMS_PLAN.md), committed before counting. Scripts: `scripts/fetch_parking_older_reforms.py`, `scripts/run_parking_older_reforms.py`. Outputs: `reference/parking_older_results.csv`, `reference/parking_older_seattle_areas.csv`, `reference/parking_older_portland_places.csv`.

These reforms cover transit areas only, not the benchmark (all housing, citywide). They are a second check and do not change the tool's numbers.

## Answer

**Both older reforms point upward, unlike the 74 recent citywide repeals. Neither result is clean enough to change the scenario.**
- **Seattle:** after 2012, permits in urban villages rose much faster than in the rest of the city. But the villages were already the city's main growth areas, and the boom of 2013–2015 landed there first. Measured as a proportion, the gain is about 46%, and the before-years swing nearly as widely.
- **Portland:** citywide permits rose 2.3 per 1,000 existing homes per year more than in similar West Coast cities. The 90% range runs from just below zero (−0.2) to +4.4.

## Seattle, 2012

The covered areas are hub and residential urban villages (24 villages, 60,039 homes in 2010). The comparison is the rest of the city outside urban centers and villages (144 census tracts, 181,603 homes). Permits are net new units: units created minus units demolished.

| Case | Effect | 90% range | Villages, before → after | Rest of city, before → after |
| --- | ---: | --- | --- | --- |
| Main: after-years 2013–2015 | +24.0 | +11.4 to +37.6 | 23.1 → 49.4 | 4.8 → 7.0 |
| After-years 2013–2017 | +21.5 | +11.5 to +33.6 | 23.1 → 48.5 | 4.8 → 8.6 |
| Comparison limited to multifamily and commercial zones (change in log permits) | +0.38 | — | 1,390 → 2,967 a year | 885 → 1,286 a year |

The first two rows are in permits per 1,000 existing homes per year; before = 2007–2011. In the last row, a log change of +0.38 means the villages' permits grew about 46% faster than the comparison's (2.14 times against 1.45 times).

**Check added after seeing the result (not in the plan):** the yearly ratio of the villages' rate to the rest of the city's.

| Years | Ratio, villages ÷ rest of city |
| --- | --- |
| 2005–2011 (before) | 2.1 to 7.0; 4.6 on average |
| 2013–2015 (after) | 6.1 to 7.9; 6.9 on average |
| 2016–2019 | 3.8 to 6.6; 5.1 on average |

**Reading.**
- **The levels difference is mostly scale.** The villages already permitted about four to five times as much per home as the rest of the city, so any citywide boom adds far more homes there. The +24 is mainly that.
- **The proportional gain is about 46%, but noisy.** It is within the range the ratio swung before the reform, and it faded after 2015.
- **Other things changed too.** The same years brought upzoning in the villages, light rail and the city's growth strategy. This test cannot separate parking from them.
- **Leaning toward no difference:** some outer comparison land near transit also had its minimums cut by up to half in 2012, and today's village boundaries include land added after 2015.

## Portland, 2002

Portland city against the 9 Pacific-division cities of half to twice its 2000 population. No Oregon city was large enough. Before = 1998–2002, after = 2004–2006; homes = 2000 census.

| Case | Effect | 90% range | Portland, before → after | Comparison, before → after |
| --- | ---: | --- | --- | --- |
| Main | +2.32 | −0.17 to +4.44 | 9.7 → 14.3 | 9.0 → 11.3 |
| Without Seattle | +2.22 | −0.74 to +4.56 | 9.7 → 14.3 | 7.9 → 10.3 |

All in permits per 1,000 existing homes per year. The comparison cities are Anaheim, Fresno, Long Beach, Oakland, Sacramento, San Francisco, San Jose, Santa Ana and Seattle.

**Reading.**
- **Diluted:** the reform covered only land near frequent transit, so the citywide figure understates any effect there.
- **Unusual years before:** Portland's permits dipped in 2000–2001 (7.6 and 7.0) after a high 1998 (13.6), so part of the gain may be a rebound.
- **Mostly California comparisons:** these were cities with very different housing markets in those years.

## What it means for the scenario

These older, transit-area reforms are the first cases in this work that point to more homes. They differ from the benchmark in three ways:
- they covered dense, transit-served areas, not whole cities;
- they came in strong regional housing markets;
- they came with other pro-growth changes.

That fits the view that parking minimums bind mainly where land is expensive and transit is good. The scenario's high end (+0.95 per 1,000 existing homes per year statewide) already allows for an effect of that kind in Wisconsin's denser places. The central case stays at "no measurable change" for a statewide repeal.
