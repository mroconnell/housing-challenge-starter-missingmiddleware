# Transit-oriented density: Gate 2 packet (usable data)

Written 2026-10-26 by the TOD conductor, for Ryan. Status: ready for your review. Two independent agents checked it first: one verified the data and results, the other reviewed this packet (section 9). Gate 3, the model, waits for your decisions in section 7.

## 1. What this gate decides, and the answer

Gate 2 asks whether the data is good enough to build the model on. For the Wisconsin side it is. For the evidence from other cities, it is a start but not enough yet.

- **Transit stops:** automated and tested ([TRANSIT_PIPELINE.md](TRANSIT_PIPELINE.md)).
  - Stop locations come from the federal National Transit Map. Frequency is set route by route from 16 agencies' own schedules, and from Madison's published route descriptions; Madison's own file is not used.
  - The main case covers 313,564 of Wisconsin's 2,727,726 homes in the 2020 census (11.5%). Of those, 98.7% are in Milwaukee County and Dane County.
- **Land and zoning near stops:** built for Milwaukee city and Madison city ([STATION_AREAS.md](STATION_AREAS.md)). The main case holds 24,378 acres of eligible parcel land: 14,198 in Milwaukee and 10,180 in Madison.
- **Room to build under the modelled law:**
  - About 735,000 homes more than today's zoning and buildings allow in Milwaukee, and about 546,000 in Madison.
  - This is room, not a forecast. Wisconsin permitted 25,569 homes of all kinds in 2025 (Census Building Permits Survey).
  - The figures assume 1,000 sq ft of floor space per home, a number of ours that will be measured from Wisconsin permits at Gate 3, so they will move.
- **Comparison cities:** 58 transit-area upzonings found; 20 have open permit data and a mapped boundary ([CASE_INVENTORY.md](research/CASE_INVENTORY.md)). Five were measured, following a plan written before counting ([CASE_ANALYSIS_PLAN.md](CASE_ANALYSIS_PLAN.md), [CASE_RESULTS.md](CASE_RESULTS.md)).

| Case | Role | Extra homes permitted per eligible acre per year (90% interval) | Added allowed floor area ratio | Extra homes permitted per acre per year for each 1.0 of added floor area ratio |
| --- | --- | --- | --- | --- |
| Fourth Avenue, Park Slope, New York (2003; 19 acres) | Used to fit the model | +6.98 (+4.38 to +9.73) | +2.38 | +2.93 |
| Downtown Brooklyn, New York (2004; 28 acres) | Used to fit the model | +13.28 (+8.03 to +19.24) | +6.06 | +2.19 |
| Charlotte light rail districts (2019) | Used to fit the model | +0.13 (+0.01 to +0.28) | +30.4 feet of height (no floor-area rule) | +0.004 per added foot |
| Chicago (2015) | Test case, never used to fit | +0.12 (−0.02 to +0.26) | +0.50 | +0.24 (−0.03 to +0.53) |
| Saint Paul Green Line (2011) | Context only (1 year of data before the change) | −0.09 (−0.44 to +0.26) | +1.01 | — |

What this means in plain terms:
- **New York:** upzoning near transit added many homes per acre in two small New York neighborhoods. New York kept its parking minimums, so these are the only cases of density increases without parking reform.
- **Charlotte and Chicago:** it added very few. Per unit of added density, Chicago's effect is 0.24 against a New York average of 2.56, about a tenth. Chicago's interval runs from nothing to about a fifth of New York's. The doses also differ: Chicago added 0.5 of floor area ratio, New York 2.4 to 6.1.
- **The "most effective design" (AQ-047, item 1):** the plan's rule (section 6) needs a design to sit above the median of the fitted cases and to hold up on the test cases. Park Slope, at +2.93, is above the two-case median of 2.56. With only two cases, one is always above. Chicago does not confirm it. So under the plan, the law stays on the SB 79 floors from Gate 1 unless the Madison test or more cases say otherwise.

## 2. What changed in the method during Gate 2, and why

**One area rule for every case.** The independent check found that Charlotte's first result, −0.41 extra homes per acre per year, came from how the areas were drawn ([GATE2_VERIFICATION.md](GATE2_VERIFICATION.md)):
- 1,856 of the 2,111 homes permitted in the treatment area before the change sat on land already zoned for transit density.
- The comparison ring also held earlier dense zoning.

The rule now used everywhere:
- **Treatment:** only lots whose allowed density actually rose.
- **Comparison:** only lots whose zoning did not change during the window.

This applies the eligible-land definition you approved in AQ-047, and it is recorded as a dated change in the plan. The first results are kept as a sensitivity case.

**Charlotte's two versions are both small, and neither is clean.** Most Charlotte apartment projects get a private rezoning first. The new rule drops those lots from the comparison area, which lowers the comparison's growth. The old rule mixed dense land into both groups.

**Charlotte's dose.** Charlotte has no floor-area rules, so its effect is reported per added foot of height. A first draft borrowed New York's conversion, which would have been an arbitrary number; that was removed.

## 3. Data coverage

| Piece | Observed | Missing or assumed |
| --- | --- | --- |
| Stops and route lines | All 27 Wisconsin agencies in the federal map | Superior and Metra's Kenosha station are not in the extract |
| Route frequency | 16 agencies' own schedules; Madison from its published route descriptions | Milwaukee uses a May 2025 copy because its server times out. Green Bay has no current schedule, so none of its routes counts as frequent. Manitowoc and small systems are not fetched |
| Homes near stops | 2020 census blocks, every place | — |
| Parcels near stops | Statewide parcel map, Milwaukee and Dane counties | Other counties are not fetched (1.3% of homes near stops) |
| Current zoning rules | Milwaukee, 52 districts (March 2025 code); Madison, 44 districts (March 2026 city summary) | Milwaukee's 2025 "Growing MKE" changes are not coded. Madison's overlay rule for 3- and 4-home buildings is not coded. Planned developments are treated as allowing only what exists. The inner suburbs (16.7% of homes near stops) are not coded, and their fallback to existing density is not built yet |
| Existing homes on parcels | Milwaukee property file; Madison assessor | The parcel counts are 6.3% above the 2020 census in Milwaukee (186,743 against 175,633 homes near stops) and 9.1% above in Madison (87,951 against 80,609), consistent with six years of building since 2020 |
| Comparison cases | 5 measured, with permits, boundaries, and zoning before and after | Not yet measured: the New York pooled set (23 rezonings), the medium-design cases, and the moderate-market cases (G2-3) |
| Madison test | Land layer built: 2,932 eligible acres in the overlay, 1,226 in the ¼-mile ring outside it, 7,107 elsewhere | Permits not yet counted, on purpose (plan written beforehand) |

## 4. Quality findings

- **Reproducible:** the scripts rebuilt every TOD reference table byte for byte in a separate copy of the repo, and the verifier's own code matched the estimates ([GATE2_VERIFICATION.md](GATE2_VERIFICATION.md)).
- **City permit files against the Census permit survey:**
  - Charlotte's county file runs 41% to 54% above the survey in 2023–2024, and 39% above in 2013, the year of a 903-unit burst in the treatment area.
  - New York's building filings run 27% to 34% below the survey in 5 of 6 years before the change.
  - Chicago's totals are within 8% in 5 of 9 years, and 19% to 54% above in the other 4.

  These gaps shift levels but cancel largely in the before-and-after differences.
- **Location matching** (share of new-home permits in the study years placed on a lot; [GATE2_EXAMPLES.md](GATE2_EXAMPLES.md)):
  - **Charlotte 2013–2024:** 12,107 of 12,374 permits (97.8%). The 267 not placed hold 888 of 49,119 homes (1.8%).
  - **Park Slope 1997–2008:** all 12,045 Brooklyn jobs were placed. 68.4% matched by block and lot, 3.2% by a point inside a lot, and 28.4% to the nearest lot within 40 m. Downtown Brooklyn is similar.
  - **Two Park Slope records to check before Gate 3:** one comparison job whose id match sits 1,345 m from its own point, and one possible duplicate treatment job (46 or 69 homes).
- **Privacy:** no parcel numbers, owner names or permit ids are in any committed file, and a test checks this.
- **Clean tests kept clean:** no Madison permits have been counted by overlay, and Chicago was never used to fit.

## 5. Concrete examples for your review

[GATE2_EXAMPLES.md](GATE2_EXAMPLES.md) shows:
- source permit records beside the cleaned rows the model used;
- one permit followed from the raw file to its lot, its area and the yearly rate it adds to, plus one permit that could not be matched;
- a zoning change with its dated source, from Park Slope, and a Wisconsin zoning rule with its code section;
- maps of the station areas in Milwaukee and Madison, and of the Park Slope areas.

## 6. Owner review steps

1. **Read section 1** and the case table. Does "large only in New York" match your sense of the evidence?
2. **Open [GATE2_EXAMPLES.md](GATE2_EXAMPLES.md):**
   - compare a raw permit with its cleaned row;
   - follow the traced permit to its area;
   - read the Park Slope zoning change and its dated source.
3. **Look at the Milwaukee and Madison maps** in that file. Do the station areas sit on CONNECT 1 along Wisconsin Avenue, the streetcar downtown, and Rapid Route A along East Washington Avenue and University Avenue?
4. **Open [CASE_RESULTS.md](CASE_RESULTS.md) at "Charlotte"** and read why the first result was negative.
5. **Decide G2-1 to G2-9** in section 7.

**Self-assessment.** I walked each step.
- The Park Slope rows show some building in both areas before 2003: the comparison area had 108 homes in 1999. After 2003, the treatment area had 69, 113, 0, 297 and 207 homes in 2004–2008. So the jump is real but lumpy: a few large projects in a 19-acre area.
- The Milwaukee and Madison acres look plausible; 45% of Madison's main-case land lies inside its own TOD overlay.
- **Weakest point:** the fitted evidence is two small New York neighborhoods. That cannot set a Wisconsin law or its effect on its own, which is why G2-3 matters most.

## 7. Decisions requested

| # | Decision | Recommendation |
| --- | --- | --- |
| G2-1 | Is the Wisconsin data fit for Gate 3? | Yes, with the gaps in section 3 shown in the tool's trace |
| G2-2 | Accept the one area rule (only lots whose allowed density rose; comparisons with no zoning change) | Yes. It applies AQ-047, and the first results stay as a sensitivity |
| G2-3 | Measure more cases before fitting | Yes, in this order. Each new case is added to the plan with today's date before its permits are counted, since I am choosing them after seeing the first results:<br>1. the New York pooled set, which is already in the plan;<br>2. three moderate-rent cases with a medium or strong design and open data: Philadelphia 2012 (median rent $1,397 a month), Raleigh 2021 ($1,572) and Phoenix 2015 ($1,582);<br>3. Ann Arbor 2021 ($1,649) as a second test case.<br>The plan's higher-rent cases (Los Angeles Warner Center $1,933, Seattle $2,030, Bellevue $2,572) come after, if time allows. For scale, Milwaukee's rent is $1,059 and Madison's $1,413 |
| G2-4 | The law's design | Stay on the SB 79 floors from Gate 1 (plan section 6), unless the Madison test or the new cases point to a design that holds up on the test cases |
| G2-5 | Market strength | Test whether the effect per added density rises with rent, fitting on the fitted cases only. Chicago, Ann Arbor and Madison judge the result. If it holds, Milwaukee and Madison get effects for their own rent levels. If not, the three scenarios ("little response", "like Madison's overlay", "strong-market response") stay as in AQ-047 |
| G2-6 | Milwaukee's zoning version | Code the 2025 "Growing MKE" amendments from the adopted ordinance before Gate 3, rather than use the March 2025 code |
| G2-7 | TOD alone versus TOD plus parking | Accept that "TOD alone" rests on the New York cases, the only ones that kept parking minimums. The combined view uses the parking thread's evidence for the parking part |
| G2-8 | Single-family lots near stops | Keep them eligible; the benchmark covers residential land and they hold 55% of Milwaukee's room to build and 51% of Madison's. Show a sensitivity that leaves them out |
| G2-9 | Suburbs near stops (16.7% of homes near stops) | Build the fallback at Gate 3: the room to build is measured from existing homes per acre and the modelled law, with zoning marked "not coded" in the trace |

Still open from earlier: the Madison Metro licence (office-hours questions 24 and 25). Nothing in Gate 2 uses Madison's file.

## 8. Limitations

- **Few measured cases,** and the two that show an effect are small neighborhoods in the strongest housing market in the country.
- **City upzonings are not a statewide law.** Cities chose where to upzone, often near projects already planned.
- **Parking cannot be separated.** New York kept its parking minimums, and Charlotte, Chicago and Saint Paul cut them. Because market strength and decade differ too, the cases cannot separate TOD alone from TOD plus parking.
- **Room to build is not building.** The 1.28 million homes of room in the two cities shows space, not demand.
- **Five years is short.** In the cases, the after-period rate builds up over years 1 to 5.

## 9. Independent review

1. **Data verification.** A verification agent rebuilt every table, recomputed the estimates with its own code, sampled permits and checked the rules ([GATE2_VERIFICATION.md](GATE2_VERIFICATION.md)). It found one blocker and five smaller issues, all fixed in commit 82c83ac.
2. **Packet review.** A second agent reviewed this packet and found four blockers:
   - the "moderate markets" cases in G2-3 were in fact higher-rent;
   - G2-4's reason did not follow the plan's rule;
   - several numbers had no committed source or did not match one;
   - the self-assessment described Park Slope wrongly.

   It also listed missing review items (source records, a traced permit, a dated zoning change, a map check), missing decisions (G2-7 to G2-9), and jargon. All of these are fixed in this version.
