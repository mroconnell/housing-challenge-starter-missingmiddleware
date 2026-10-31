# Parking improvement loop, round 2: which comparison places count as reformed, plan written before running

Written 2026-10-31 by the parking conductor. Ryan: "Option A for now. Keep doing runs until you're confident in your results. Keep improving data sets where necessary." No V7 result has been computed before this file was committed.

## What round 1 left open

The high end depends on which comparison places are treated as reformed:
- Treating every Parking Reform Network housing entry as a reform (V6) empties big-city pools.
- Ignoring undated entries (V6u) left San Jose one stand-in short of the rule.

A look at the entries behind the thin pools (31 undated "weaker" entries in the heaviest places' pools) shows that most do not touch apartment building across a city. They are removals for a downtown only, for houses and accessory units only, or optional reductions.

## The data fix: code each entry as material or not

An entry is **material** (it can change apartment building over a large area) if it removes minimums (`rm_min`) and the network's rating reason is one of:
- removed for all housing, by right;
- removed for housing with conditions (other, size of project, historic preservation);
- removed for one residential class only (multi-family);
- removal limited to transit-oriented areas, or conditioned on transit service, including the combinations with downtown or main street.

**Not material:**
- reductions (`reduce_min`);
- downtown-only or main-street-only removals;
- removals for low-density housing, houses or accessory units only;
- removals for affordable or supportive housing only;
- plans or reports with no code change.

The coding is saved per entry in `reference/parking_reform_material.csv`.

## V7

The same as V6: scaled reported permits, pre-repeal homes and population, national fallback. The one difference: a comparison place is left out only if it has a **material** entry that is undated or dated on or before the end of the case's after-window. Repeals at or near the benchmark stay excluded.

## Rule, set now

- If every real place has at least 20 placebo stand-ins in V7, V7's placebo high end is proposed to Ryan to replace 19,937, whatever it is.
- If not, 19,937 stays, and V7 joins the sensitivity cases.
- Reported as in round 1:
  - the real average with its 90% resampling range;
  - the placebo 5th, 50th and 95th percentiles;
  - the real average's percentile among the placebo sets;
  - pool sizes and stand-in counts;
  - flags;
  - the worst-moving place, traced.

## Changes after writing
