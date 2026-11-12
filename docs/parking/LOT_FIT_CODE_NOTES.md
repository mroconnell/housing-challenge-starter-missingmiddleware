# Parking lot-fit test: code notes (choices where the plan is silent)

**Status: 2026-11-12. The audit cleared the code with one fix: alley bounds (below). Ryan's go is recorded at 16:33 UTC.** Results: `reference/parking_lotfit_shares.csv`, `reference/parking_lotfit_spans.csv`, `reference/parking_lotfit_sanity_milwaukee.csv`.

## Labels that go with every result

- **Alleys are two preset bounds, not a range.** TIGER alleys are not used (audit option b).
  - **Upper bound:** no lot has an alley.
  - **Lower bound:** every lot has an alley.
- **The low and high across rule variants are a span of assumptions, not a statistical range.**
- **Waivers are ignored**, so blocking may be overstated. Milwaukee's 2-unit blocking is 0 by rule.
- **Milwaukee sanity check uses modelled rules only.** MPROP's `PARKING_SPACES` and `CORNER_LOT` are empty in the file on disk. So no recorded-spaces check is possible, and no lot gets the corner-lot rules.
- **Madison zoning comes from `ZoningAll`.** `Zoning1` is empty in the file on disk.
- **The Kenosha (RS-3) and Janesville (R1) "as if allowed" districts were judged from the codes' purpose statements.** No zoning map was read.
- **Kenosha's 70 ft accessory front yard is not modelled.** Blocking there is understated.
- **Oshkosh rules are cited to §30-175.** They were read from the official pages in a browser, which the audit ruled was not a workaround.

**Code conflicts (how each was resolved).**

| Place | Conflict | Central | Variant |
|---|---|---|---|
| Green Bay | Figure 2 gives 5 or 6 stalls; §44-1580(e) gives 6 or 8, with 3 or 4 garages | §44-1580(e) | Figure 2 totals |
| Green Bay | Storage-room exception (2 garages) | Ignored, as discretionary | — |
| Janesville | "Two spaces for each dwelling": a dwelling may mean the whole building | 2 per unit | 2 per building |
| Madison | Lot coverage vs building coverage; the definition was blocked | Buildings only | All impervious surface |
| Milwaukee | 2 stalls per 3 units gives 2.67 for 4 units; no rounding rule | Rounded up to 3 | — |

**Plan corrections found while coding.**
- Oshkosh 2 units need 4 stalls, not 2.
- Oshkosh's parking section is §30-175, not §30-75.
- Milwaukee RT1–RT3 do not allow new 3–4 unit buildings. Only RT4 and RT5 do, as a limited use.
- Madison's 2-unit minimum is 1 stall per building, as printed.
- Eau Claire GR allows 3–4 units only as a limited use (next to certain districts or on a collector road).
- Germantown's Rm districts allow 3+ units only; 2 units are in Rd-2.

Plan: [LOT_FIT_PLAN.md](LOT_FIT_PLAN.md). Its Choices and Audit fixes blocks override the draft.

## Files

| File | What it does |
|---|---|
| `scripts/fetch_parking_lotfit.py` | Fetches V12 parcels (11 places) and TIGER 2024 county roads into `data/raw/parking_lotfit/`, with a manifest |
| `reference/parking_lotfit_rules.csv` | Hand-coded rules: one row per rule, with source, status and use |
| `scripts/run_parking_lotfit.py` | Runs the fit test, variants, aggregates and the Milwaukee sanity check |
| `scripts/run_parking_lotfit.sh` | Runner: fetch if missing, tests, licence check, then a synthetic smoke run (or `--go`) |
| `tests/test_parking_lotfit.py` | 29 unittest cases on synthetic lots (all pass) |

**Rules table columns.**
- `use` values:
  - central: used in the main run;
  - span_variant: one variant;
  - waiver_ignored: recorded but not used (audit fix 7);
  - info: a different building or district;
  - gap: not found or blocked.
- `status` values: verified, plan, assumption, choice_pending_audit, not_found, blocked.
- `units` and `condition` limit a row to a unit count or a lot condition: alley, corner, tod_overlay, lot_area_le_7500, small_lot_w60_d100.

## Choices for audit (plan silent or unclear)

### A. Rules table

1. **"As if allowed" district for the 7 places the audit did not name.** Each uses the place's main 2–4 unit district from the plan, per C2:

   | Place | District |
   |---|---|
   | Milwaukee | RT4 |
   | Madison | TR-V1 |
   | Appleton | R-3 |
   | Waukesha | RN-2 |
   | Eau Claire | GR |
   | Oshkosh | TR-10 |
   | Germantown, 2 units | Rd-2 |
   | Germantown, 3–4 units | Rm-1 |

   - These rows are marked `choice_pending_audit`.
   - Germantown Rm-1 needs 21,780 sq ft and 120 ft of width. Few lots may pass step 1, so its 3–4 unit share may be undefined.
2. **Audit-named as-if districts were judged from the codes' purpose statements; no zoning map was read.**
   - Green Bay R-1 and Racine R2: fairly sure.
   - Kenosha RS-3 and Janesville R1: unsure. Alternatives are in the table: Kenosha RS-2 or RG-1; Janesville R2.
3. **Tandem and driveway stalls.**
   - Where a code says "no", they are not counted.
   - Where a code is silent, they are counted, per C4.
   - Kenosha, Green Bay and Oshkosh differ by unit count; see the table rows.
   - The variant counts none anywhere.
4. **Which rule wins.** A condition row (alley, corner, TOD overlay, small lot) beats everything. After that: place, then district, then unit count.
5. **Plan variants for stall and aisle size** (8.5 ft stall, 20 ft aisle) apply only where the place's code is silent. Where the code sets the size, its own variant rows apply.
   - Two variants apply everywhere: "no parking in the rear setback" and "no tandem".
   - Driveway width = the larger of 10 ft (plan) and the code's minimum. The 8 ft variant never goes below the code's minimum.
6. **Milwaukee.**
   - Front setback: the code sets the block average and gives no number. Central is 20 ft, the RT3/RT4 cap; the variant is 10 ft. Both are assumptions.
   - Stall: the code sets 160 sq ft. Central is 9 × 18 ft; the variant is 8.9 ft wide, the narrowest that meets 160 sq ft.
   - The RT4/RT5 ratio gives 2.67 stalls for 4 units. Rounded up to 3, as the plan says; the code has no rounding rule.
   - Side setbacks: the south/east side uses the larger value, and the total is enforced.
   - Corner lots come from MPROP `CORNER_LOT`.
   - Transit and on-street credits are ignored (waivers).
7. **Madison.**
   - Coverage counts buildings only (plan 3.5). The variant counts all impervious surface. The definition (MGO 28.211) was blocked.
   - TOD overlay: no minimum, and 3–4 units are allowed in TR-C. A lot is "in" if its interior point falls inside `data/raw/madison_tod/tod_boundary.geojson`.
   - The Central area and IG exemptions are not modelled (no layer on disk). This may overstate blocking there.
   - Stall, aisle and driveway sizes and the tandem rule are blocked (Municode 403), so plan defaults are used.
   - Two-unit minimum: 1 stall per building, as printed. The two-unit twin (2 stalls) is a side-by-side type, marked info.
8. **Green Bay.**
   - Central uses the district rule, §44-1580(e): 6 or 8 stalls, with 3 or 4 garages.
   - The Figure 2 totals (5 or 6 stalls) are a span variant.
   - The storage-room exception (2 garages) is discretionary, so it is ignored.
   - Driveway stalls on 2-unit "narrow lots" are not modelled; "narrow" is undefined.
   - The 60% small-lot coverage applies to every lot of 7,500 sq ft or less. The code also requires the lot to predate 2015-12-03, and creation dates are unknown.
   - 8 × 15 ft stall (code); 9 × 18 ft variant.
9. **Kenosha.** Required stalls may not sit in the 70 ft "accessory front yard". The model only keeps parking out of the front setback, and stalls behind a building that starts at 15 ft may sit inside 70 ft. So **Kenosha blocking is likely understated**. This needs a decision: model the 70 ft line, or report it as a limit.
10. **Janesville.**
    - Central is 2 stalls per unit (4 for a two-unit building). The variant is 2 per building.
    - Two derived coverage caps both apply in the central run:
      - impervious surface 75% (green area at least 25%);
      - buildings 60% (open space at least 40%).
      The rules helper had listed 60% as a variant. I changed it because both rules apply at once.
    - Front-yard parking is allowed by code, but the model never uses the front yard.
    - The apartment paving buffers (§42-419) apply only to R3M and above, so they are not modelled for R1.
11. **Other places.**
    - Racine: no coverage cap; aisle width not found, so 24 ft.
    - Appleton R-3 for 3–4 units: width 80 ft, side 20 ft, rear 35 ft, height 45 ft. Bedroom-based totals are info, because the model's units are 2-bedroom.
    - Waukesha RN-2: lot area and width vary by units and alley. One driveway stall counts for 2 units. Minimum drive is 12 ft for 3+ units.
    - Eau Claire: width and coverage vary by units and alley.
    - Oshkosh: no parking in the rear or side setback. On small 2-unit lots (under 60 ft wide or 100 ft deep), stacked driveway stalls count. Lot depth is area ÷ width.
    - Germantown: stall size from a redline review copy.

### B. Geometry

12. **Floors** = the planned floors (2, 3 and 2; variant: fourplex on 3), capped by floor(stories) and by floor(height ÷ 11 ft).
    - A half story is not a floor.
    - Footprint = units × 1,000 sq ft ÷ floors.
    - The 11 ft story height is an assumption.
13. **Building shape.** As wide as the buildable width allows, but **never shallower than 20 ft** (the plan sets only a 20 ft minimum width).
14. **Driveway (no alley).**
    - It runs in the wider side setback.
    - If it is wider than that setback, the extra comes off the building width. If the building then can't fit, parking blocks ("driveway squeezes building").
15. **Parking zone.**
    - Depth: from the back of the building to the rear lot line, or to the rear setback line where setback parking is not allowed.
    - Width: the full lot, or the buildable width where side-setback parking is not allowed.
    - No gap between the building and the parking.
16. **Layouts.** A lot fits if any layout meets both the stall count and coverage.
    - **With an alley:** one row along the rear; the alley is the aisle.
    - **N0:** up to 2 stalls, or a 2-car garage, at the end of the drive, backing down it. In-line drive stalls beside the building count here only, up to the code's cap.
    - **N1:** a cross aisle behind the building, with a row behind it and, if deep enough, a row in front of it.
    - **N2:** the drive widens to an aisle along the side, with stalls on one or both sides.
17. **Tandem.** Doubles open stalls in rows at least 2 stalls deep. It never applies to garages.
18. **Garages** (12 × 22 ft, an assumption) go first in each row and count as buildings for coverage.
19. **Paving** for impervious caps = driveway (front setback + building depth) + aisle + the open stalls used.
    - Step 1 counts the building only, even under an impervious cap (no driveway or walk in step 1).
20. **Alley.**
    - A TIGER S1730 road within 5 m of the lot outline (outline sampled every 1 m).
    - Rear half: the half of the lot's depth axis away from the nearest other TIGER road within 100 m. With no road within 100 m, any alley counts.
    - The depth axis is the long side of the minimum rotated rectangle.
    - **Not used in the run (audit option b).** TIGER barely maps Wisconsin alleys. Records with MTFCC S1730 in the 2024 county roads files:

      | County | FIPS | Alley records |
      |---|---|---|
      | Milwaukee | 55079 | 4 |
      | Dane | 55025 | 14 |
      | Outagamie | 55087 | 47 |
      | Brown, Eau Claire, Winnebago | 55009, 55035, 55139 | 0 |

    - Every lot is run twice instead, under two preset bounds (not a range):
      - **upper bound:** no lot has an alley;
      - **lower bound:** every lot has an alley.
    - Alley-dependent rules follow the bound, for example Eau Claire's width and Waukesha's lot area.
    - The alley / no-alley split is dropped.
    - The TIGER detection code (`alley_flags`) is kept but not called.
21. **Corner lots** are known only in Milwaukee. Elsewhere every lot is treated as interior.

### C. Lots, versions, outputs

22. **Lots.**
    - The fetch takes parcels with PROPCLASS containing 1 (mixed classes too). The run keeps PROPCLASS exactly "1".
    - Irregular lots (rectangle fill under 80%) are reported apart. All splits are of regular lots.
23. **Main version.**
    - A lot counts only if its district is coded in the rules table and allows the unit count.
    - Coded districts:
      - Milwaukee: RT1–RT5 and RM1–RM3. RM4–RM7 and commercial districts are left out.
      - Madison: TR-C2/C3/C4, TR-V1/V2, TR-U1, SR-C1, SR-C3.
    - Lots in other districts are not in the main denominator.
    - Madison zoning: `Zoning1` is empty in every row of the file on disk (`data/raw/madison_parcels/tax_parcels.geojson`), so the code reads `ZoningAll`.
      - It takes the first coded district listed.
      - Otherwise it takes the first entry that is not a WP- (wellhead) or HIS- (historic) overlay.
24. **Milwaukee sanity check.**
    - It covers existing buildings with MPROP `NR_UNITS` of 2–4.
    - Each gets the model building (units × 1,000 sq ft) on its own district's rules. Where the district is not coded, RT4 applies.
    - **Blocker found:** `PARKING_SPACES` and `CORNER_LOT` are empty in every row of the MPROP file on disk (`data/raw/milwaukee_mprop/mprop.csv`, assessment year 2026). The other check columns are filled: `NR_UNITS`, `ZONING`, `LOT_AREA`.
    - So the check runs on two bases, each reported separately:
      - **Modelled rules.** This is audit fix 5 as written, and it sets the label. Stalls are what the modelled rules require.
      - **Recorded spaces.** Stalls are `PARKING_SPACES`, with no garages. On the file on disk this reads "not computable", because no building has a value.
    - Because 2-unit Milwaukee buildings need 0 stalls, the modelled-rules check mostly tests step 1 for them.
    - "Could not fit" means failing step 1 or step 2. Both parts are reported.
    - The label "rule model may be too strict" is set when more than 50% could not fit. It is applied per unit count and to the 2–4 unit total.
    - Step-1 failures (non-conforming old lots) may dominate. This is reported, not retuned.
    - For audit: should the check refetch MPROP or use another source for recorded spaces? Not done; it needs an OK.
    - With `CORNER_LOT` empty, no Milwaukee lot gets the corner-lot rules (coverage 85% and so on). This leans toward overstating blocking.
25. **"Tested places" row.**
    - Lot-weighted sums: lots where parking blocks ÷ lots that fit without parking.
    - A variant that can't apply in a place leaves that place at its central value.
26. **Span.**
    - One variant at a time: the low and high share across the variant groups.
    - Labelled as a span of assumptions, not a statistical range.
    - Every row carries the waiver note (audit fix 7).
    - Variant rows that belong together are applied together: Milwaukee front setback (all districts); Green Bay stall 9 × 18 ft; Green Bay Figure 2 totals.
27. **Stall counts** round up (plan 3.5).

## Process notes

- I ran `run_parking_lotfit.py` once on synthetic lots before its first commit (424a9bf). Every later run followed a commit.
- Oshkosh:
  - curl got only an empty JavaScript page from civiclinQ.
  - A direct call to the site's data service was denied by the permission system, and was not used.
  - The official pages were read in the built-in browser. The audit ruled this was not a workaround.
  - The rules are cited to §30-175.
- Madison: Municode returned HTTP 403. The rules come from adopted ordinances on Legistar: ORD-25-00066, ORD-23-00013 and ORD-25-00094.
- No new dependencies. The licence check passed.

## Input checks (counts only; no fit test run on real lots)

| Place | Residential lots (PROPCLASS exactly 1) | Rectangle fill at least 80% | TIGER alley flag | Zoning joined | In a coded district | Madison TOD overlay |
|---|---|---|---|---|---|---|
| Germantown | 7,311 | 4,420 | 0 | — | — | — |
| Madison | 74,497 | 54,460 | 0 | 74,420 of 74,497 parcel IDs match | 40,898 | 16,430 |
| Milwaukee | 142,308 | 132,180 | 4 | 142,182 | 71,862 | — |

The other 8 places were fetched but not loaded.
