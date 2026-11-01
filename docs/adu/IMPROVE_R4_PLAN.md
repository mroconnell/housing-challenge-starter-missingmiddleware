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

- **2026-11-01, audit review of the first run (before any rerun):** W1 divided all 12 months' permits (437) by 0.75 years, which overstates the four counties' rate by about a third. Two corrected versions replace it, and both are reported:
  - **W2 (pre-law months removed):** 437 minus the four counties' permits expected in the 3 pre-law months at their rate in the year before (estimate year 2025: 502 permits, so 502 × 3/12 = 125.5), over 0.75 years.
  - **W3 (even spread):** 437 over 1.0 year.
- **The same rule applies to Massachusetts.** Its 2025 count covers the whole calendar year, but the law took effect on 2 February, and it is divided by 11/12 of a year. No Massachusetts pre-law rate exists, so variant M counts it over 1.0 year. Reported alone and with W2 and W3.
- **Check:** no city is split by OFM between one of the four counties and any other county. The split cities (Auburn, Bothell, Enumclaw, Milton, Pacific) lie wholly within the four counties.
