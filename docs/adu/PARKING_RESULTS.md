# ADUs with and without parking requirements: results

Run 2026-11-11 under [PARKING_PLAN.md](PARKING_PLAN.md), which was locked after the audit's review. Nothing in the tool has changed.

## Answer

**The effect of dropping the last parking space for ADUs is unknown.**
- No case separates parking from the other rules that changed with it.
- The two states whose laws need no extra space, Oregon and Maine, sit within the other states' range (P1).
- So the model's level is kept as it is.
- The How-sure wording below is proposed, for Ryan to approve.

## P1. State level (not run; numbers already published in A3)

The two no-parking states sit inside the capped states' spread of misses; 2 against 6 cannot tell.
- Oregon's held-out miss (log of predicted ÷ actual) is +0.119, and Maine's is −0.129.
- The capped states run from −0.088 to +0.187.

## P2. Local changes that removed ADU parking (report only)

Each row is a package; parking is not separable. Counts are ADU permits per year.

| Place, date | Parking change | Other ADU changes at the same time | Before | After | Source |
| --- | --- | --- | --- | --- | --- |
| Seattle, August 2019 | Off-street space no longer required | Owner occupancy removed. 2 ADUs per lot. Detached ADU size cap 800 → 1,000 sq ft. Minimum lot 4,000 → 3,200 sq ft | 2016–2018: 217, 199, 192 (our series); 275, 255, 245 (city report) | 2020–2023: 350, 428, 546, 627 (our series); 2020–2022: 490, 771, 988 (city report) | `reference/other_cities_annual.csv`; Seattle OPCD 2022 ADU report |
| Austin, November 2015 | No parking for ADUs near transit corridors | Minimum lot 7,000 → 5,750 sq ft. Size cap 850 → 1,100 sq ft (0.15 floor-area ratio). Separation 15 → 10 ft | 2012–2015: 17, 53, 51, 56 | 2016–2019: 98, 127, 120, 121 | `reference/other_cities_annual.csv`; `reference/other_cities_reforms.csv` |
| Tacoma, 2019 | Parking dropped | Detached ADUs ("cottages") legalised; owner occupancy dropped | 0.5 a month | 9.25 a month | Sightline, 2020 |
| Tigard, OR, 2018 | No parking near transit | Cottages; 2 ADUs per lot; owner occupancy dropped | 1 (2018) | 25 (2019) | Sightline, 2020 |
| Portland, 2010 onward | Parking not required (timing unclear) | Development-charge (SDC) waiver of about $11,000 (2010–2018); owner-occupancy rule removed earlier | 45 (2010) | 545 (2016); fell after the waiver ended in 2018 | Sightline, 2020; accessorydwellings.org, 2019 |
| Bellingham, WA, May 2018 | Reduced, not removed: one space per bedroom → at least one space | Detached ADUs re-legalised; fees cut; owner occupancy kept | 12 applications (record year before 2018) | 48 applications (2018) | Sightline, 2018 and 2019 |
| Olympia, WA, late 2018 | Parking requirement removed | Owner occupancy removed; height to 24 ft | 5 applications (2017) | 4 (2018); 3 by February 2019 | Sightline, 2019 |
| Vancouver, WA, 2017 | None (parking unchanged at that time) | Owner occupancy removed | 1 application (2016) | 10 (2017), 45 (2018) | Sightline, 2019 |

**Notes**
- **Two Seattle series.** Our series and the city's annual report count differently, so both are shown.
- **Portland.** Its swings follow the fee waiver's deadline more closely than any parking change.
- **Washington cities (Sightline 2019, added 2026-11-12):** the three rows point different ways.
  - Bellingham kept a parking minimum and still quadrupled its applications.
  - Vancouver changed owner occupancy, not parking, and rose 45-fold from 1.
  - Olympia dropped parking and owner occupancy, and its applications did not rise in the first months.
  - These are counts of a few dozen with no comparison places, so they do not separate parking either.

## P3. Proposed How-sure wording (needs Ryan's OK)

> Wisconsin's modelled law needs no extra parking. Six of the eight evidence states allowed up to one space. No study separates parking from the rest of each package. Oregon and Maine, which need no extra space, sit within the other states' range. So the effect of dropping the last space is unknown: it could raise ADU building, or change little where owners add parking anyway.

## Sightline and related research (read 2026-11-11)

- **Seattle.** ADU permits went from 245 (2018) to 988 (2022), 4.0×, for the whole 2019 package.
- **Kent, WA.** 95% of single-family lots can't fit one more space (architect's site analysis, April 2023).
- **Cost.** A parking space costs $4,000–$10,000 (architects, via Sightline 2019).
- **Owners park off-street anyway.** With no mandate, about 25% (Seattle) to 43% (Portland) of ADUs keep all their residents' cars off-street.
- **California cross-section.** Cities with frequent ADU applications were more likely to have no parking standard: 31% against 13% (Pfeiffer, Terner Center). The author says this is not causal.

## Possible data for a later test (2026-11-12; nothing run)

- **Pew (October 2026)** coded the ADU rules of all 346 US cities with 100,000+ people.
  - 81 of the 276 that allow rentable ADUs still require parking in some cases.
  - Pew also estimated ADU permits by city from building-permit data (its Appendix B).
  - Pew reports owner-occupancy and parking rules as "associated with" fewer ADU permits; it gives no causal estimate.
- **Lehigh University's Small Cities Lab** coded 290 cities of 25,000–500,000 people. 58% require parking.
- **What a test would need.** If either coding is published as data, cities with and without ADU parking rules could be compared within the same state. That would be a new plan, locked before counting, and still associational unless rule changes are dated.
- **Not available yet.** pew.org refuses automated reads; the report PDF and any data files would need downloading by hand.
- **Cases named by Pew and the parking thread:**
  - Ann Arbor dropped ADU parking in 2021, a year before its citywide parking repeal.
  - Boise eased parking along with other rules; its ADU permits rose about fivefold from 2019 to 2025 (a package, not parking alone).
