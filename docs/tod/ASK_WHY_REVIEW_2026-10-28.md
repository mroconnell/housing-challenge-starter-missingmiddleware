# One-off "ask why" review of TOD work to date

Written 2026-10-28 at the owner's request ("do a one off 'Ask why' on everything we've done so far"). For each result, the most extreme value, its cause, and what kind of issue it is. **No scenario number has changed.**

Kinds: **error** (coding mistake, fixed or to fix), **known** (already explained or disclosed), **question** (owner decision).

## Summary

| # | Result | Most extreme value | Why | Kind |
| --- | --- | --- | --- | --- |
| 1 | Lot model | Madison guessed 10,172 extra homes, actual 794 | Stop list was rail only; Madison's lots coded 96 km from transit | error, fixed (lot plan item 14) |
| 2 | Lot model | Los Angeles Warner Center lots 7.2 km from transit | Same: the G Line busway was missing | error, fixed (item 14) |
| 3 | Lot model | Charlotte blew up linear models | Heights in feet read as floor area ratio | error, fixed (item 12) |
| 4 | Cases | Charlotte: 73% of homes on rezoned land were on industrial land, left out | Eligible land excludes industrial zoning, in cases and Wisconsin | question (AQ-060) |
| 5 | Cases | LA Cornfield Arroyo Seco: 13 of 650 published acres counted | Mostly industrial (same rule); 0 homes were built on the industrial part | question (AQ-060) |
| 6 | Cases | Madison +1.24% of city homes over 5 years, highest permit city | Only 3 after years (2023–2025); projects may have been in the pipeline before the law; interval 0.03% to 2.43% | known (wide interval shown) |
| 7 | Whole cities | Minneapolis −7.6%, Seattle −5.0%, Portland −3.3% | 2010s boom then bust; boom-city placebos test it | known (BOOM_SLIVER_RESULTS) |
| 8 | Slivers | Milpitas +7.7% from 3% coverage | Upzoned land held few homes before, so the ratio is large | known (shown without it) |
| 9 | Census check | Philadelphia: census homes grew 1.92 × the permit survey's count | The permit survey likely undercounts Philadelphia; our case uses the city's own permits | question (see below) |
| 10 | Census check | Milwaukee: census homes grew 0.46 × permits | Demolitions and losses; the tool's baseline is permits (AQ-001) | known, worth stating |
| 11 | Wisconsin tool | Year 5 gets 6.6% of the typical total, after 47.9% in year 4 | The New York pooled ramp's year 5 dips | known (sensitivity "ramp_year5_alt") |
| 12 | Wisconsin tool | Shorewood Hills village: 4.5 extra homes per 100 homes; Milwaukee city 0.2 | Placement follows eligible acres × added floor area; Milwaukee's zoning already allows more, so the law adds less there | known mechanism, worth stating |
| 13 | Wisconsin tool | 4,420 acres of industrial land in the main station areas left out (Milwaukee 3,659, Madison 761) | Same eligible-land rule as item 4 | question (AQ-060) |

## Notes

- **Item 9, Philadelphia.** The control-city comparison uses the Census permit survey for every city. If it undercounts Philadelphia by about half, Philadelphia's control-city result is less reliable than the others. The case measurement itself uses the city's permits and is not affected. Check next: compare the city's own permit totals with the permit survey for 2010–2019.
- **Permits vs census, all cities** (`reference/tod_audit_permits_census.csv`): census change ÷ permits ran 0.68 (Charlotte) to 1.28 (Chicago), apart from Philadelphia (1.92) and Milwaukee (0.46). Values below 1 are expected where many 2018–2019 permits were not finished by the April 2020 count, or where homes were demolished.
- **Acres audit** (our upzoned acres ÷ published acres): Seattle 78% and 95%, Warner Center 82%, Bellevue 56%, Charlotte 46%, Madison 10%, Cornfield 2%. Madison's 10% is the Madison test's own rule (lots whose allowed density rose); the others are mostly the industrial rule.
- **Lot model flags still raised after the fix** are real differences, not errors: Madison and Bellevue upzoned most land near their stops; Bellevue's lots are much bigger; only New York has existing-home counts; Seattle's single-family lots have no floor area limit.

## Not yet checked

- Map spot-check of random lots per city.
- Philadelphia's own permits vs the permit survey (item 9).
