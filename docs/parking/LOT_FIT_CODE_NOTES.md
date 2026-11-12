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
| `tests/test_parking_lotfit.py` | 30 unittest cases on synthetic lots (all pass) |

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
    - On an alley lot the model tries the alley row first. It may still use any driveway layout, so an alley never makes a lot fail that would fit without one.
      - The first `--go` run (outputs not kept) let alley lots use only the alley row.
      - In Oshkosh and Kenosha, that made the lower bound block more lots than the upper bound.
      - This was fixed before the outputs were committed.
      - Lower-bound counts can still be higher where alley rules lower the lot minimums (Waukesha, Eau Claire), because more lots pass step 1.
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

## Results (run 2026-11-12, after the audit and Ryan's go at 16:33 UTC)

**What the share is.**
- Share of regular lots where parking blocks the building: lots where parking blocks ÷ lots where the building fits without parking.
- Lots are residential (PROPCLASS exactly 1) with rectangle fill of at least 80%.
- The rules are each place's central rules.
- "main" = lots whose current zoning allows the building (Milwaukee and Madison only). "as_if" = all residential lots under the named district.

**How to read the columns.**
- The two alley columns are **preset bounds, not a range**:
  - **upper bound:** no lot has an alley;
  - **lower bound:** every lot has an alley.
- "Span" is the lowest and highest share across rule variants, each tried alone. It is a **span of assumptions, not a statistical range**.
- Waivers are ignored, so blocking may be overstated.
- Kenosha's 70 ft accessory front yard is not modelled, so Kenosha blocking is understated.

| Place | Version | Units | Upper bound (no alleys): blocked / fit = share | Span | Lower bound (all alleys): blocked / fit = share | Span |
|---|---|---|---|---|---|---|
| Milwaukee | main | 2 | 0 / 54,960 = 0.0% | 0.0%–0.0% | 0 / 54,960 = 0.0% | 0.0%–0.0% |
| Milwaukee | main | 3 | 7,529 / 22,704 = 33.2% | 3.6%–34.4% | 0 / 22,704 = 0.0% | 0.0%–0.5% |
| Milwaukee | main | 4 | 2,034 / 10,181 = 20.0% | 1.5%–33.7% | 165 / 10,181 = 1.6% | 1.3%–3.2% |
| Milwaukee | as_if | 2 | 0 / 129,749 = 0.0% | 0.0%–0.0% | 0 / 129,749 = 0.0% | 0.0%–0.0% |
| Milwaukee | as_if | 3 | 11,526 / 117,743 = 9.8% | 0.9%–10.1% | 0 / 117,743 = 0.0% | 0.0%–0.2% |
| Milwaukee | as_if | 4 | 22,224 / 86,727 = 25.6% | 0.2%–38.0% | 136 / 86,727 = 0.2% | 0.1%–0.8% |
| Madison | main | 2 | 24 / 31,815 = 0.1% | 0.0%–0.1% | 0 / 31,815 = 0.0% | 0.0%–0.0% |
| Madison | main | 3 | 61 / 10,460 = 0.6% | 0.0%–3.7% | 0 / 10,460 = 0.0% | 0.0%–2.6% |
| Madison | main | 4 | 99 / 8,233 = 1.2% | 0.1%–2.0% | 0 / 8,233 = 0.0% | 0.0%–1.3% |
| Madison | as_if | 2 | 481 / 52,870 = 0.9% | 0.4%–1.4% | 4 / 52,870 = 0.0% | 0.0%–0.4% |
| Madison | as_if | 3 | 495 / 52,870 = 0.9% | 0.4%–3.3% | 4 / 52,870 = 0.0% | 0.0%–2.1% |
| Madison | as_if | 4 | 1,438 / 48,859 = 2.9% | 1.2%–9.3% | 101 / 48,859 = 0.2% | 0.0%–6.8% |
| Appleton | as_if | 2 | 0 / 7,499 = 0.0% | 0.0%–0.0% | 0 / 7,499 = 0.0% | 0.0%–0.0% |
| Appleton | as_if | 3 | 0 / 5,090 = 0.0% | 0.0%–10.8% | 0 / 5,090 = 0.0% | 0.0%–0.8% |
| Appleton | as_if | 4 | 0 / 4,749 = 0.0% | 0.0%–35.9% | 0 / 4,749 = 0.0% | 0.0%–19.4% |
| Waukesha | as_if | 2 | 0 / 12,179 = 0.0% | 0.0%–0.1% | 0 / 14,169 = 0.0% | 0.0%–0.2% |
| Waukesha | as_if | 3 | 0 / 10,804 = 0.0% | 0.0%–0.4% | 0 / 12,179 = 0.0% | 0.0%–0.1% |
| Waukesha | as_if | 4 | 0 / 10,804 = 0.0% | 0.0%–1.9% | 0 / 12,179 = 0.0% | 0.0%–1.9% |
| Eau Claire | as_if | 2 | 52 / 16,426 = 0.3% | 0.0%–2.3% | 0 / 17,482 = 0.0% | 0.0%–1.2% |
| Eau Claire | as_if | 3 | 0 / 13,869 = 0.0% | 0.0%–0.3% | 0 / 13,869 = 0.0% | 0.0%–0.0% |
| Eau Claire | as_if | 4 | 0 / 13,144 = 0.0% | 0.0%–2.5% | 0 / 13,144 = 0.0% | 0.0%–4.5% |
| Oshkosh | as_if | 2 | 61 / 10,132 = 0.6% | 0.6%–1.3% | 8 / 10,132 = 0.1% | 0.1%–0.5% |
| Oshkosh | as_if | 3 | 101 / 10,132 = 1.0% | 0.9%–2.5% | 51 / 10,132 = 0.5% | 0.4%–1.3% |
| Oshkosh | as_if | 4 | 4,386 / 10,132 = 43.3% | 20.6%–51.0% | 2,266 / 10,132 = 22.4% | 12.9%–28.3% |
| Germantown | as_if | 2 | 0 / 3,198 = 0.0% | 0.0%–0.0% | 0 / 3,198 = 0.0% | 0.0%–0.0% |
| Germantown | as_if | 3 | 0 / 1,423 = 0.0% | 0.0%–0.1% | 0 / 1,423 = 0.0% | 0.0%–0.0% |
| Germantown | as_if | 4 | 0 / 1,163 = 0.0% | 0.0%–0.0% | 0 / 1,163 = 0.0% | 0.0%–0.0% |
| Green Bay | as_if | 2 | 0 / 17,054 = 0.0% | 0.0%–1.1% | 0 / 17,054 = 0.0% | 0.0%–0.0% |
| Green Bay | as_if | 3 | 4,515 / 17,054 = 26.5% | 13.3%–39.8% | 0 / 17,054 = 0.0% | 0.0%–0.0% |
| Green Bay | as_if | 4 | 8,081 / 15,031 = 53.8% | 38.1%–62.8% | 585 / 15,031 = 3.9% | 0.0%–32.3% |
| Kenosha | as_if | 2 | 0 / 18,059 = 0.0% | 0.0%–0.0% | 0 / 18,059 = 0.0% | 0.0%–0.0% |
| Kenosha | as_if | 3 | 0 / 6,910 = 0.0% | 0.0%–0.0% | 0 / 6,910 = 0.0% | 0.0%–0.0% |
| Kenosha | as_if | 4 | 2 / 3,536 = 0.1% | 0.0%–0.1% | 2 / 3,536 = 0.1% | 0.0%–0.1% |
| Racine | as_if | 2 | 0 / 8,477 = 0.0% | 0.0%–10.9% | 0 / 8,477 = 0.0% | 0.0%–10.6% |
| Racine | as_if | 3 | 19 / 8,410 = 0.2% | 0.0%–61.9% | 0 / 8,410 = 0.0% | 0.0%–26.4% |
| Racine | as_if | 4 | 317 / 7,445 = 4.3% | 0.0%–70.0% | 0 / 7,445 = 0.0% | 0.0%–48.7% |
| Janesville | as_if | 2 | 0 / 10,376 = 0.0% | 0.0%–0.0% | 0 / 10,376 = 0.0% | 0.0%–0.0% |
| Janesville | as_if | 3 | 0 / 10,376 = 0.0% | 0.0%–0.1% | 0 / 10,376 = 0.0% | 0.0%–0.0% |
| Janesville | as_if | 4 | 0 / 10,376 = 0.0% | 0.0%–3.7% | 0 / 10,376 = 0.0% | 0.0%–0.0% |
| tested places (lot-weighted) | as_if | 2 | 594 / 286,019 = 0.2% | 0.1%–0.6% | 12 / 289,065 = 0.0% | 0.0%–0.5% |
| tested places (lot-weighted) | as_if | 3 | 16,656 / 254,681 = 6.5% | 2.1%–9.4% | 55 / 256,056 = 0.0% | 0.0%–1.4% |
| tested places (lot-weighted) | as_if | 4 | 36,448 / 211,966 = 17.2% | 4.9%–27.0% | 3,090 / 213,341 = 1.4% | 1.0%–5.5% |
| tested places (lot-weighted) | main | 2 | 24 / 86,775 = 0.0% | 0.0%–0.1% | 0 / 86,775 = 0.0% | 0.0%–0.0% |
| tested places (lot-weighted) | main | 3 | 7,590 / 33,164 = 22.9% | 2.5%–24.7% | 0 / 33,164 = 0.0% | 0.0%–1.2% |
| tested places (lot-weighted) | main | 4 | 2,133 / 18,414 = 11.6% | 0.9%–19.3% | 165 / 18,414 = 0.9% | 0.8%–2.4% |

**Milwaukee sanity check** (modelled rules only; MPROP's parking and corner fields are empty).

| Alley bound | Units | Existing buildings | Could not fit (share) | Of which: other rules | Of which: parking | Label |
|---|---|---|---|---|---|---|
| Upper (no alleys) | 2 | 32,544 | 5,893 (18.1%) | 5,893 | 0 | — |
| Upper (no alleys) | 3 | 2,202 | 1,168 (53.0%) | 689 | 479 | rule model may be too strict |
| Upper (no alleys) | 4 | 2,647 | 1,336 (50.5%) | 1,186 | 150 | rule model may be too strict |
| Upper (no alleys) | 2–4 | 37,393 | 8,397 (22.5%) | 7,768 | 629 | — |
| Lower (all alleys) | 2–4 | 37,393 | 7,807 (20.9%) | 7,768 | 39 | — |
| Lower (all alleys) | 3 | 2,202 | 689 (31.3%) | 689 | 0 | — |
| Lower (all alleys) | 4 | 2,647 | 1,225 (46.3%) | 1,186 | 39 | — |

- The audit's 50% rule is set on the 2–4 unit total. That total is not labelled under either bound.
- The 3-unit and 4-unit rows are labelled under the upper bound.
- Most "could not fit" cases fail step 1 (lot minimums and the building box), not parking.

## Audit rulings on the results (2026-11-12 17:34 UTC)

- **Code fixed after the first output; the fix restores lower ≤ upper.**
  - In the first --go run, the lower bound (every lot has an alley) blocked more lots than the upper bound in Oshkosh and Kenosha, which is impossible by definition.
  - Fix d254ba8b lets alley lots also use a driveway layout. The upper bound is unchanged by it.
  - The first run's outputs were deleted before their figures were recorded. They were not kept and can't be recovered.
- **The Milwaukee sanity label applies to the 2–4 unit total only.**
  - That total is 22.5% (8,397 of 37,393 existing buildings could not fit, upper bound), so there is no label.
  - Plain note, not the locked label: the 3-unit row is 53.0% and the 4-unit row is 50.5%.
- **Why the sanity check fails:** most failures come from lot and building rules, not parking (upper bound: 7,768 of 8,397). So the building model may be strict on lot rules, which shrinks the denominator.
- **Scope:** the shares cover the 11 tested places, weighted by lot. They are not results for all of Wisconsin.
- **Spans** are spans of assumptions. The "no parking in the rear setback" variant drives most of the high end; Racine reaches 70%.
