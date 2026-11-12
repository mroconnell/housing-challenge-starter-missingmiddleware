# Parking: lot-fit test, DRAFT plan (not locked)

**Status: DRAFT, 2026-11-12. Not locked. Nothing has been computed.** Written by a parking-thread helper at Ryan's request. Ryan must make the choices in section 9 before this is locked. After locking, changes go in the last section with a date and a reason.

## 1. Question

- On Wisconsin residential lots, how often does a parking minimum physically stop a 2–4 unit building?
- "Stops" means: the building fits with setbacks and no parking, but not once the required stalls and their access are added.
- Model: Kent, WA. An architect found 95% of single-family lots couldn't fit one more space (April 2023; see [../adu/PARKING_RESULTS.md](../adu/PARKING_RESULTS.md), "Sightline and related research").

**What kind of number this is.** An engineering estimate of where parking binds. It is not a causal effect, and it does not count homes.

## 2. Data

| Item | Use | Source | Licence | On disk? |
|---|---|---|---|---|
| WI statewide parcels, V12 (2026 release, tax roll 2025) | Lot outline, area, property class, place | SCO / DOA FeatureServer `Wisconsin_Statewide_Parcels_DB/FeatureServer/0` (layer V1200_WisconsinParcels_2026) | Public; item says "free for public consumption as of 06/30/2026"; repo classes it Public (Wis. Stat. 59.72) | Pleasant Prairie and Sun Prairie only (`data/raw/wi_v12_parcels_*`) |
| Milwaukee MPROP | Zoning, lot area, corner lot, units, parking spaces, building area | City of Milwaukee | CC-BY | Yes (`data/raw/milwaukee_mprop/mprop.csv`) |
| Madison tax parcels | Zoning (`Zoning1`), lot size, dwelling units | City of Madison GIS | Not stated; public record (owner decision D1) | Yes (`data/raw/madison_parcels/`) |
| TIGER/Line 2024 roads, WI counties | Alleys (MTFCC S1730) behind lots | Census | Public domain | No; small county files |
| Local zoning rules | Stalls per unit, setbacks, coverage | Official codes and ordinances (section 4) | Public record (D1) | Hand-coded, as for ADU rules (D6) |
| Building footprints (Microsoft US) | Only for an "existing house kept" variant | Microsoft USBuildingFootprints, Wisconsin file 3,173,347 buildings, 817 MiB | ODbL (share-alike) | No; owner decision D5 dropped samples |

**V12 coverage.**
- 3,574,646 parcels statewide (count query, 2026-11-12).
- 2,137,180 have property class exactly `1` (residential).
- 2,331,950 have a class starting with `1` (includes mixed classes).
- V12 has **no zoning field** and no dwelling count. Zoning comes from city layers or MPROP.

**Size.** The service returns 2,000 records a page. One mid-size city is a few thousand to ~170,000 lots. No single file over 200 MB is needed.

## 3. Geometry rules

### 3.1 Lot shape

- Lot width: shorter side of the minimum rotated rectangle. Reuse `min_rect_widths()` in `missing_middleware/geom_extra_tod.py` (already used by `scripts/run_tod_lot_model.py` and `scripts/run_parking_lot_cities.py`).
- Lot depth: area ÷ width.
- Lots are treated as rectangles. Irregular lots (rectangle fill under 80%) are reported apart.
- Alley: a TIGER alley within 5 m of the rear half of the lot.

### 3.2 The building (a new building, not the existing house)

| Units | Floors (central) | Floor area per unit, incl. stairs (central) | Footprint (central) |
|---|---|---|---|
| 2 (stacked two-flat) | 2 | 1,000 sq ft | 1,000 sq ft |
| 3 (stacked) | 3 | 1,000 sq ft | 1,000 sq ft |
| 4 (two per floor) | 2 | 1,000 sq ft | 2,000 sq ft |

- Variants: 800 and 1,200 sq ft per unit; fourplex on 3 floors.
- Floors never above the district height limit.
- The building sits at the front setback, as wide as the buildable width allows (minus any driveway strip), minimum 20 ft.

### 3.3 Parking

| Item | Central | Variants | Source |
|---|---|---|---|
| Stall (90°) | 9 ft × 18 ft | 8.5 ft × 18 ft | Waukesha Table 22.06(4)(F); Eau Claire LDO Table 17.08.05(G); Iowa SUDAS Ch. 8 Table 8B-1.01 (reports ULI/NPA *Dimensions of Parking*) |
| Two-way aisle (90°) | 24 ft | 20 ft | Waukesha, Eau Claire tables; SUDAS 8B-1.02; St. Paul Sec. 63.305 (20 ft) |
| Driveway (no alley) | 10 ft | 8 ft | Waukesha Table 22.06(3)(D) (8 ft minimum); Milwaukee 295-505-4-c (18 ft maximum) |
| Alley | Alley serves as the aisle; stalls back into it | none | — |
| Tandem stalls | Not counted toward units' stalls | Counted, up to 2 per unit | Ryan to choose |
| Front-yard parking | Not allowed | — | Appleton §23-43(e)(3); Madison s.28.031(4) |
| Parking in rear setback | Allowed | Not allowed | Check per code |
| Garage | Surface stalls | 1 garage stall per unit (Germantown) | — |

### 3.4 Setbacks and coverage

Use each place's district table (section 4). Where a lot's zoning doesn't allow 2–4 units, see choice C2 in section 9.

### 3.5 The fit test

For each lot and unit count (2, 3, 4):

1. **Fits with no parking?** Building fits the buildable box (lot minus setbacks), meets the coverage cap and minimum lot area/width.
2. **Fits with required parking?** Add required stalls (rounded up) behind the building.
   - **With alley:** stalls in rows along the rear; alley is the aisle.
   - **No alley:** a driveway strip from the street (may use the side setback), plus stalls and a 24 ft aisle, or 2 stalls with no aisle (backing down the drive).
   - Coverage counts paving where the code caps impervious surface (Eau Claire, Oshkosh); building only where it caps buildings (Milwaukee, Madison).
3. **Class.**
   - **Parking blocks:** fits at step 1, fails at step 2.
   - **Other rules block:** fails at step 1.
   - **Fits:** passes step 2.

## 4. Sample of places and their rules (read 2026-11-12)

Stalls per dwelling unit, minimum. "Verified" = read from official text (code, city PDF or adopted ordinance).

| Place | 2 units | 3 units | 4 units | Main 2–4 unit districts | Status | Source |
|---|---|---|---|---|---|---|
| Milwaukee | 0 (max 4) | 1 (RM1–RM4) or 2 per 3 units (RT4, RT5) | same | RT1–RT5 (3–4 units a limited use) | Verified via ordinance 240997 (passed 2025-04-22), Table 295-403-2-a; city site 403 | milwaukee.legistar1.com, file 240997 |
| Madison | "1 (location only)"; per building or per unit to confirm | 1 (location only) | 1 | TR-C2, TR-C4, TR-V1, TR-V2 | Verified via ORD-23-00013, Table 28I-3; none in Central area, IG and TOD overlay; Municode 403 | legistar.granicus.com/madison, file 74703 |
| Appleton | 2 (3 if 4+ bedrooms) | 1–2 per unit + 1 visitor per 2 units | same | R-2 (2 only), R-3 | Verified, Ch. 23 Supp. 100, §23-172(m) | appletonwi revize PDF |
| Waukesha | 2 | 1.5 (5 total) | 1.5 (6) | RN-2, RN-3, RN-4 | Verified, Ord. 2026-4, Table 22.06(4)(B)(3) | municodeonline PDF |
| Eau Claire | 2 | 2 | 2 | GR, NR | Verified, LDO Table 17.08.05(C) (code replaced 2025-10-01) | eauclairewi.gov DocumentCenter 1033 |
| Oshkosh | 2 | 1 + 1 guest per 4 units (4 total) | 5 total | TR-10, MR-12 | Verified, §30-75 | hosting.civiclinq.com/oshkoshwi |
| Germantown (village) | 2, 1 in garage | 2, 1 in garage | same | Rd-2, Rm-1 to Rm-3 | Verified with caveat: June 2023 review copy | germantownwi.gov DocumentCenter 7658 |
| Green Bay | 2 per unit, 1 enclosed (garage) | 5 total, 2 enclosed | 6 total, 2 enclosed | R1, R2 (district list to confirm) | Verified from a code PDF Ryan supplied (2026-11-12; Supplement No. 10, Oct 2026), §44-1726 Figure 2. Downtown (D): residential needs only evidence of 1 available space per unit. Narrow-lot exception §44-1747(c). Stalls 8 × 15 ft for 1–4 units (§44-1747(b)(1)); driveways do not count toward the minimum (§44-1747(b)(2)) | Green Bay Municipal Code Ch. 44 (Municode); PDF not committed |
| Kenosha | — | — | — | — | Blocked (city PDF 403) | — |
| Racine | — | — | — | — | Blocked (Municode 403) | — |
| Janesville | — | — | — | — | Blocked (city site, Municode, zoning hub 403) | — |
| Menomonee Falls, Pleasant Prairie, Sussex, Mount Pleasant, Caledonia (villages) | — | — | — | — | Blocked (Municode or ecode360 403, or village PDFs 403/404) | — |

**Places that already removed minimums for all housing** (Parking Reform Network, `reference/parking_wi_benchmark_places.csv`): West Allis, La Crosse, Franklin, Fitchburg, Cottage Grove, Omro, Brodhead, Algoma, Gilman. Their share is 0 by rule; they are listed, not tested.

**Selected setbacks and coverage (verified).**

| District | Min lot area | Min width | Front | Side | Rear | Max coverage |
|---|---|---|---|---|---|---|
| Milwaukee RT3 | 3,000 sq ft; 1,800 per unit | 30 ft | block average | 1.5 / 3 ft | 15 ft | 50% (60% corner), buildings |
| Milwaukee RT4 | 2,400 sq ft; 1,200 per unit | 24 ft | block average | 1.5 / 3 ft | 15 ft | 70% (85% corner), buildings |
| Madison TR-C4 (3 units) | 4,000 sq ft | 40 ft | 20 ft | 5 ft | lesser of 30% of depth or 30 ft | 65% |
| Madison TR-V1 (3–4 units) | 3,000 sq ft | 30 ft | 20 ft | 5 ft | lesser of 25% or 25 ft | 70% |
| Waukesha RN-2, 3–4 units | 6,000 (alley) / 8,000 sq ft | 50 ft | 15 ft | 5 ft | 30 ft | none found |
| Eau Claire GR/NR | 4,000 / 6,000 / 8,000 sq ft (2/3/4 units) | 40–60 ft | 20 ft | 5 ft | 20 ft | 65–70%, impervious |
| Oshkosh TR-10 | 7,200 sq ft | 30 ft | 25 ft | 7.5 ft | 25 ft | 50%, impervious |
| Appleton R-3 (3+ units) | 1,500 per unit | 80 ft | 20 ft | 20 ft | 35 ft | 70% |

Full rows, sections and URLs: helper notes from 2026-11-12, to be moved into a hand-coded `reference/parking_lot_fit_rules.csv` (one row per rule, URL on every row, as for `wi_adu_rules.csv`) when the plan is locked.

## 5. Outputs

- **Main:** share of residential lots (property class 1) where parking blocks, by place and by unit count (2, 3, 4).
  - Numerator: lots classed "parking blocks". Denominator: lots that fit with no parking (step 1).
  - Also shown: the share blocked by other rules, of all residential lots.
- **Range:** lowest and highest share across the rule variants in section 3 (stall, aisle, driveway, tandem, floor area, rear-setback parking). Each variant also reported alone.
- **Split:** alley and no alley; lot width under 40 ft and 40 ft or more.
- **Weighting:** a lot-weighted average of the tested places, labelled as "tested places", not "Wisconsin".
- **Sanity check (Milwaukee):** existing 2–4 unit buildings (MPROP `NR_UNITS`) and their recorded `PARKING_SPACES`. If the test says most of them could not fit their parking, the rules are too strict.

## 6. What it can't say

- **Not a causal effect.** It says where a minimum is a hard physical barrier, not how many homes a repeal adds.
- **Market demand.** A lot where parking blocks may still see no building if rents don't cover costs.
- **Owners may build parking anyway.** Buffalo developers built 79% of the old required spaces after repeal (Hess and Rehler 2021). A lot freed from the rule may still be built with parking, or not built.
- **Variances and waivers.** Many codes allow reductions (transit, on-street credit, Plan Commission). The test ignores them, so it may overstate blocking.
- **Simplified geometry.** Rectangles, one building layout, no trees, slopes or utility easements.
- **Existing house.** The central test is a new building. Keeping the existing house needs footprints (ODbL; see choice C5).

## 7. How it would be used

- **Supporting evidence beside the 2–4 unit range.** It does not change the scenario line or its range.
- Shown as: "Where 2–4 units are allowed, parking minimums physically block X% of tested lots in [places] (range Y–Z%)."
- Could inform where the upper case lands (MODEL_AND_ASSUMPTIONS_PARKING.md notes the upper case "is spread by homes, not by where minimums actually bind"). Any such use needs a separate plan and Ryan's OK.

## 8. Feasibility

| Item | Source | Licence | Status |
|---|---|---|---|
| Lot outlines, area, class | WI V12 statewide parcels (SCO/DOA FeatureServer) | Public, "free for public consumption" | Ready; 2 places on disk, others fetchable by script |
| Zoning per lot: Milwaukee | MPROP `ZONING` | CC-BY | On disk |
| Zoning per lot: Madison | City tax parcels `Zoning1` | Public record (D1) | On disk |
| Zoning per lot: other places | City zoning GIS layers | To check per city | Not checked |
| Alleys | TIGER/Line 2024 roads | Public domain | Not on disk; small |
| Parking minimums, 7 places | Official codes/ordinances | Public record (D1) | Verified 2026-11-12 |
| Parking minimums, 8+ places | Municode, ecode360, city sites | — | **Blocked (HTTP 403 or bot check)**; need manual browser read or records request |
| Setbacks, coverage | Same as above | Public record | Verified for 7 places; blocked for the rest |
| Stall, aisle, driveway sizes | Waukesha, Eau Claire codes; Iowa SUDAS Ch. 8 | Public | Verified |
| Garage sizes | Builder guides only | — | Not verified; garage variant optional |
| Building footprints | Microsoft USBuildingFootprints (817 MiB WI file) | ODbL, share-alike | Not needed for central test; D5 says no samples |
| Lot width code | `min_rect_widths()` in `missing_middleware/geom_extra_tod.py` | Repo | Reusable |
| Dependencies | numpy, pandas, shapely already used | — | No new dependency planned; run the licence check if that changes |

## 9. Choices for Ryan

- **C1. Places.** Use the 7 verified places only, or wait for manual reads of the blocked ones (Green Bay, Kenosha, Racine, Janesville and villages)?
- **C2. Which lots.** Test only lots whose zoning allows 2–4 units today, or all residential lots "as if allowed" (using the place's main 2–4 unit district rules, matching the middle housing scenario)?
- **C3. Building size.** 1,000 sq ft per unit and 2–3 floors as central?
- **C4. Tandem stalls.** Count them toward the minimum or not?
- **C5. Existing house.** New building only, or also "keep the house, add units" (needs ODbL footprints, or Milwaukee's MPROP building area as a proxy)?
- **C6. Zoning layers.** Fetch city zoning layers for the places beyond Milwaukee and Madison (licence checked per city)?

## Changes after writing

(none yet; plan not locked)
