# TOD Gate 2: independent verification notes

Written 2026-10-26 by the TOD conductor, recording what an independent verification agent found when it checked the Gate 2 data and case results. Its scratch scripts were outside the repo; this note keeps the findings.

## Reproducibility

The agent rebuilt the outputs in a separate copy of the repo. `scripts/run_tod_cases.py`, `scripts/build_tod_stops.py` and `scripts/build_tod_station_areas.py` reproduced every `reference/tod_*.csv` file byte for byte. This was checked before the area-rule fix (commit 6500493). After the fix, the case tables were rebuilt by the scripts, and the tests pass (442 tests).

It also recomputed, with its own code, the first-round difference-in-differences from the per-year rates:
- Charlotte −0.4056 units per eligible acre per year;
- Park Slope 7.0571;
- Downtown Brooklyn 11.2584.

All three matched. Its own project bootstrap for Charlotte gave a 90% interval of −0.711 to −0.131, against −0.695 to −0.119 in the committed results.

## Findings, all fixed in commit 82c83ac

1. **Charlotte's −0.41 came from the area definitions.** 1,856 of the 2,111 homes permitted in the treatment area before 2019 were on parcels already zoned TOD-CC; those parcels cover 124.8 of 961.2 eligible acres. The comparison ring also held earlier dense zoning (TOD-M, TOD-MO, MUDD, UMUD). Excluding land already zoned dense from both areas gave +0.03. The fix was one area rule for every case, recorded in [CASE_ANALYSIS_PLAN.md](CASE_ANALYSIS_PLAN.md), section 7.
2. **Downtown Brooklyn's comparison area held upzoned lots.** 18 lots (4.58 acres) just outside the amendment had their residential floor area ratio raised from 4 to 10. They are now excluded.
3. **The permit-file check against the Census permit survey left out before-period years.** For Charlotte, 2013 is +39% (11,919 units in the county file against 8,558 in the survey). They are now included.
4. **One misquoted number** ("2,613" for 2023, where the table has 2,610). Corrected.
5. **New York's "literal plan" figures were mislabelled.** They were replaced by a true whole-amendment version.
6. **Chicago's staged-permit merge removed separate homes.** It merged 2,583 permits (5,470 units); it now merges 340, and a test covers the rule.

## Spot checks (10 permits per area, first round)

- **Charlotte:** cleaned rows equalled the raw rows in every sample. No floor-by-floor double counting was found. The permit's own parcel agreed with the located parcel for 92.4% of units, and no disagreement moved a permit between treatment and comparison. The unlocated large projects (340 units in 2013, plus 144 and 57 units) fall outside the main areas.
- **New York:** every job within 600 m of the areas was located. 82% in Park Slope and 64% in Downtown Brooklyn matched by block and lot; the rest were placed on the nearest lot within 40 m.
- **Held-out and Madison rules:** Chicago appears only as a held-out check. No Madison permits are read anywhere.
- **Privacy:** no parcel numbers, block-and-lot ids, PINs, owner names or permit ids are in committed files.
