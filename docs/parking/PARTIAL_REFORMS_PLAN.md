# Parking: older and partial reforms, 1998–2020, plan written before counting

Written 2026-10-28 by the parking conductor, at Ryan's request: "do #1 and look up dates for the largest 50 or so". No permit outcome for any place named here has been computed before this file was committed. Changes go in the last section with a date and a reason.

## Candidates

`reference/parking_older_candidates.csv` lists them, drawn from the Parking Reform Network data (MIT licence, pinned commit). It excludes places already in the 74-place comparison and only includes entries that affect housing ("residential" or "all uses"), adopted, city level, covering more than a downtown or main street.
- **List A (24 entries):** dated 1998–2020.
- **List B (50 entries):** undated removals, the 50 largest places not already checked.

## Which reforms count

A reform counts if it removed residential parking minimums, or cut them by at least half, for apartments or all housing, over one of these areas:
- the whole city ("citywide");
- transit areas or a large planned district ("transit-area or district").

It does not count if it:
- covers only accessory dwelling units, only one- and two-family homes, only non-residential uses, or only affordable or supportive housing;
- covers only a downtown or business district;
- is an optional reduction: a waiver, fee-in-lieu, land banking, EV chargers, bike parking or a travel-demand plan;
- was a place that had no minimums before (no repeal event).

Each candidate is screened first on the network's own summary. Those that pass are checked against the ordinance or official sources for the adoption or effective date and the coverage. The checks go in `reference/parking_partial_checks.csv`, with source links.

## Groups and method

- **Citywide reforms at or near the benchmark, 2015–2024:** these are what the 74-place comparison measures. They are added to it under the expanded comparison's rules, and the comparison, the placebo test and the Wisconsin numbers are rerun. Any change to the tool's high end goes to Ryan before it is final.
- **Transit-area or district reforms, and citywide reductions, 1998–2020:** run citywide with the Portland method. Each place is compared with places in its own state at ½–2× its population, widening to ⅓–3× and then to its Census division, using the same windows (5 years before, years 1–3 after the effective year) and weights (homes × after-years). Homes are from the 2000 census for repeal years before 2010 and the 2010 census for 2010–2014. From 2015 on they come from ACS 2020–2024, as in the main comparison.
- **Reported:**
  - the group's weighted average effect, with a 90% range from 2,000 resamples of places;
  - each place's effect;
  - a split between transit-area reforms and citywide reductions.

  These results are diluted, because only part of each city was covered, and they are reported as a second check. They do not change the tool.
- **Permit data:** the Census permit place files for 1993–2011 are added for all four regions. The older file layout is read by place name, as for Portland.

## Changes after writing
- **2026-10-28, while running (before Charlotte's effect was computed):** Charlotte is dropped. Its permits are filed in the Mecklenburg County row, and its reform covered only TOD districts.
- **2026-10-28, after screening:** only Hayward (2011) needed permit years before 2012, so only the West region files for 2007–2011 were added. No citywide reduction passed the screen (all were optional reductions), so there is no reductions split.
