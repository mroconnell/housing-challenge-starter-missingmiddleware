# ADU improvement loop, round 4: Washington's partial law year (plan written before running)

Written 2026-11-01 by the ADU conductor. Owner decision (2026-11-01): count Washington's 2026 law year by the months its cities were under the law, as a test round first. No result below had been computed when this file was committed.

## Problem

Washington's only law year in the model is OFM estimate year 2026 (April 2025 to March 2026), coded as one full year of law for every city outside Seattle. But HB 1337 binds each city six months after its county's plan update (RCW 36.70A.130):
- King, Pierce, Snohomish and Kitsap: from 2025-06-30, so 9 of the 12 months;
- Clallam, Clark, Island, Jefferson, Lewis, Mason, San Juan, Skagit, Thurston and Whatcom: from about 2025-12-31, so 3 months;
- all other counties: from 2026-12-31 or later, so 0 months.

## Variant W1 (the test)

- Washington's 2026 law row keeps only the cities in King, Pierce, Snohomish and Kitsap counties (incorporated, Seattle excluded): their ADU permits (OFM) over their single-family homes (ACS 2020–2024, year-matched as now).
- Its exposure is 9 of 12 months (0.75 of a year), as Massachusetts 2025 counts 11 of 12.
- Every other Washington city's 2026 row is left out (3 months or none is too little to call a law year).
- Everything else as adopted (AQ-066).

## Reported

Against the adopted run: the held-out log error by state and RMS (each of 7 states left out), Washington's own miss, and Wisconsin's lower, central, upper and reference line. Flags and the worst miss traced, as before. This is a coding correction: it is judged on the rule (count only time under the law), not on the score. Ryan decides before the tool changes.

## Changes after writing

None yet.
