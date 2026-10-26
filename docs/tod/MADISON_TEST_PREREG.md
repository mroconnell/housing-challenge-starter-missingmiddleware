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

None yet.
