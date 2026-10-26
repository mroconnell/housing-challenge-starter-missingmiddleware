# Madison TOD overlay test: plan written before looking at the results

Written 2026-10-26 by the TOD conductor, before anyone has counted Madison's apartment or other new-housing permits inside versus outside the TOD overlay. The commit that adds this file is the timestamp. Any later change to this plan is listed in section 8 with its date and reason. Related: [GATE1_PACKET.md](GATE1_PACKET.md) section 4.3, AQ-047.

**What has already been seen.** The ADU work counted ADU permits inside and outside the overlay (AQ-029). No count of new housing units by overlay, by year, has been made for any purpose.

## 1. Question

Did Madison's TOD overlay change how many homes were permitted per acre per year inside it? Which of the two TOD methods, fitted without Madison, predicts that change better?

## 2. Areas

- **Treatment:** parcels inside the TOD overlay boundary (`data/raw/madison_tod/tod_boundary.geojson`). The overlay was adopted on 17 January 2023 (ORD-23-00013); its effective date is to be confirmed from the ordinance before the count.
- **Main comparison:** parcels outside the overlay, within ¼ mile of its edge.
- **Second comparison:** all other Madison parcels in residential, mixed-use or commercial zoning districts.
- **Eligible land, for both:**
  - parcels in residential, mixed-use or commercial zoning, from Madison parcels and zoning, which are in the repo;
  - excluding parks, water, streets, institutional campuses and cemeteries;
  - excluding parcels whose use code is single-family, where the overlay did not change single-family rules.

  Acres are parcel acres, not gross land.

## 3. Outcome

- **Housing units:** the "Dwell" field (dwelling units added) in new-construction permits, BLDNRC and BLDNCC, from Madison's Construction Summary report, by issue date. These are permits at issuance, as for the ADU work.
- **Rate:** units per acre of eligible land per year, separately for treatment and comparison.
- **Location:** each permit is placed by matching its address to Madison address points, with the pipeline already used for ADUs. The match rate and every unmatched permit with 10 or more units are reported.
- **Duplicates:** reissued permits are de-duplicated by permit number.

## 4. Periods

- **Before:** 2017–2022, 6 full years.
- **After:** 2023–2025, 3 full years.
- **2026** is partial: shown, not used in the estimate (LESSONS §5).
- **A ramp check:** the after years are also shown one by one.

## 5. Estimate and uncertainty

- **Main estimate (difference-in-differences):** (treatment after − treatment before) − (comparison after − comparison before). The result is in units per acre per year.
- **Uncertainty:** a 90% interval from resampling whole projects (permits at the same address in the same year count as one project), 2,000 draws, fixed seed. Large projects make the counts lumpy, so this is the honest interval.
- **Sensitivity cases, fixed now:**
  - the second comparison area;
  - leaving out the single largest project in each area and period;
  - 2024–2025 only as the after period, since Rapid Route A opened on 22 September 2024;
  - permits per 1,000 existing homes instead of per acre (AQ-047, item 8).
- **Dose:** the added allowed floor area, the overlay's allowance minus the base district's, is coded from the zoning code for each district in the overlay. The effect per unit of added floor area is reported next to the main estimate.

## 6. How the methods are judged

1. Method A is fitted on the other cases, without Madison. It predicts the Madison difference-in-differences from Madison's dose.
2. Method B uses Milwaukee's measured take-up rate and Madison's rents and capacity. It predicts the same number.
3. Whichever prediction is closer to the main estimate, in units per acre per year, wins and becomes the main method.
4. **If both predictions fall inside the 90% interval, the test cannot separate the methods.** Then:
   - Chicago is held out instead, with the same rules;
   - the brief says plainly that neither method was confirmed in Wisconsin.

## 7. Known threats, stated now

- **Rapid Route A** opened during the after period (22 September 2024).
- **The overlay bundled several changes:** it also removed parking minimums and some conditional-use hearings, so the estimate is for the bundle, not for density alone.
- **Interest rates:** rose sharply in 2022–2023, slowing apartment starts nationally. The comparison area absorbs this only if both areas were hit alike.
- **Three after years** may be too few to see an effect. Other cases show little in years 1 and 2.
- **Address matching** may miss large projects with campus-style addresses. Unmatched large permits are listed so this can be checked.

## 8. Changes after writing

**2026-10-26, made while counting (TOD Gate 3 stage 2).** Results are in [MADISON_TEST_RESULTS.md](MADISON_TEST_RESULTS.md).

- **Method B dropped.** Method B was not computable, as recorded in [GATE3_MODEL_SPEC.md](GATE3_MODEL_SPEC.md) section 9, before the count.
  - So section 6 becomes one test: method A is confirmed if its committed prediction lies inside the measured 90% interval.
  - The Chicago fallback in section 6.4 is not triggered.
- **Areas follow the uniform rule** of [CASE_ANALYSIS_PLAN.md](CASE_ANALYSIS_PLAN.md) section 7, instead of section 2 as written.
  - **Treatment:** eligible overlay lots whose allowed FAR rose (CC, RMX, TSS, TR-V2, NMX).
  - **Comparison:** eligible lots outside the overlay within ¼ mile of treated land, whose zoning did not change in 2017–2025.
  - **In no area:** overlay lots whose density did not rise, land already at the law (downtown districts) and lots rezoned in the window.
  - **Second comparison:** all other eligible lots, with the same exclusions.
  - **Reason:** the owner's decision G2-2 applies one area rule to every case.
  - **Kept as a sensitivity:** the areas as written in section 2, judged the same way.
- **The judged number is converted to the prediction's basis.** The prediction is per acre of all eligible overlay land (dose 0.374). The uniform rule's treatment is the land whose density rose (dose 0.977).
  - The measured estimate is multiplied by 0.374 ÷ 0.977 before it is compared with 0.251.
  - Its interval is multiplied by the same factor.
  - This is the same as comparing effects per 1.0 of added FAR.
  - **Reason:** method A predicts no effect where density did not rise, so both bases describe the same prediction.
- **How "zoning changed in the window" is read.**
  - **Source:** Madison has no dated zoning snapshots, so the City's zoning map amendment ordinances (MGO 28.022) are used instead. These are the ordinances passed with enactment dates in 2017–2025, 278 in all, from the Legistar web API.
  - **Placing them on lots:** the addresses in their titles are matched to lots with the ADU address matcher. A range covers every address in it.
  - **Addresses that no longer exist:** the nearest house number on the same street, within 50, is used.
  - **Attachments:** lots outside the City's 1 January 2016 boundary (TIGER 2016) count as rezoned. Their zoning was assigned in the window, and the permit report does not cover them before attachment.
  - **Reason:** this is the only dated record of Madison rezonings found.
- **Ambiguous address matches** are placed when every candidate parcel lies on the same lot. Others stay unmatched.
- **Effective date confirmed.** ORD-23-00013 passed on 17 January 2023 and was enacted (published) on 26 January 2023 (Legistar file 74703). 2023 stays an after year, as written.
- **Dose.** The dose is coded from `reference/tod_zoning_rules_madison.csv`, the same coding as the committed prediction: overlay stories replace the base district's where higher.
