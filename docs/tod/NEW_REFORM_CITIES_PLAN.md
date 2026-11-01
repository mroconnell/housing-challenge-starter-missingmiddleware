# New reform cities for the TOD lot model: Denver, Austin, Portland (plan, logged before any of their data is used)

Owner, 2026-11-01: "add reform cities, especially those three." Why: lots teach the model where homes land within a city, but the size of a city's reform effect has one value per city, and we have 9 (8 scorable).

## The test, frozen now (before any new city's data is read)

- **Rule under test:** the drift rule as adopted in AQ-068. Change in the upzoned lots' share of a city's new homes = a + b × (share before − 0.5). It is fitted on the existing 9 cities: a = −0.038, b = −0.398 (`scripts/build_tod_lot_model_line.py`). It is **not refitted** before scoring a new city.
- **Benchmarks:**
  - average-change rule (+0.040, pre-registered);
  - same share as before.
- **Score:** |log(predicted share after ÷ actual share after)| for each new city, and the median over the new cities.
- **Definitions are unchanged from the lot model** (plan items 31–48):
  - Lot groups come from the reform's day-one map.
  - Upzoned lots more than ½ mile from rail or rapid are relabelled.
  - Every lot is kept.
  - Windows: 6 years before, 5 after, on a 5-year basis.
  - Shares are measured within the study area (reform lots plus a ½-mile ring).
- The machine-learning methods are also scored on the new cities as a second check, with no retuning.

## Candidates and data found so far (2026-11-01)

| City | Candidate transit upzoning | Year | Permits with home counts | Zoning before and after |
| --- | --- | --- | --- | --- |
| **Denver** | 38th & Blake station-area height amendments: incentive overlay IO-1 with design overlay DO-7, in Five Points, Elyria Swansea and Globeville, about 270 acres. Also 2016: 61st & Peña station area (DIA / Gateway), about 570 acres | 2018 (and 2016) | Yes: the city's residential construction permits layer has a `UNITS` field and points, but starts in July 2012 (before window 2012–2017, about 5.5 years) | Yes: the zone map amendments layer gives each rezoning's from-zone, to-zone, overlay, ordinance year and polygon (1,868 amendments) |
| **Austin** | Candidates: ETOD overlay (May 2024; too recent, with under 2 years after); Vertical Mixed Use along transit corridors (2006–2008); TOD districts (about 2005) | To choose | Yes: Issued Construction Permits (Socrata `3syk-w9eu`) has `housing_units`, about 2.3 million rows | To check: Austin zoning-case history |
| **Portland** | Candidates: Mixed Use Zones in centers and corridors (2018); Better Housing by Design (effective March 2020; multi-dwelling zones, partly transit-linked); earlier station-area rezonings (122nd Ave MAX 2006; Interstate MAX 2008) | To choose | Yes: the city's layer of permits creating new homes since 1995 (from the permit database) | To check: historical zoning layers |

## Next steps

1. Pick one reform per city using the lot model's rules: transit-linked, a raised allowance, a mapped day-one boundary, and at least 5 years after. Log the choice here before counting permits.
2. Write a case adapter for each, like `case_bellevue.py`: lots, day-one groups, permits placed on lots.
3. Build their lot rows, run the frozen test, and report.

## Added 2026-11-01, before any permit is counted (audit review of this plan)

**1. What each outcome means.** There is no threshold. The drift rule "held" if its median score over the new cities beats both the average-change rule and same share.

| Outcome | What we tell the owner |
| --- | --- |
| Drift rule beats both | It stays the central line |
| Loses to average change | The pre-registered 798 may be the better central |
| Loses to same share | The effect near stops may be about 0 |

Each city's score is reported too. With about 3 to 5 new cases, one city can flip the median, and that is said with the result.

**2. Which reform.** Every candidate that meets the lot model's rules is scored. No choice is made, and nothing is dropped. Ruled-out candidates are logged here with the reason before any permit is counted.

**3. Edge cases, settled now:**
- **Fewer before-years than 6:** a case needs at least 3 before-years and 3 after-years. Fewer than 6 is put on the 5-year basis as usual. Denver's permits start in July 2012, so 38th & Blake (2018) has about 5.5 before-years, and 61st & Peña (2016) about 3.5; both qualify.
- **"Rapid":** means rail or bus rapid transit open on the reform date. Upzoned lots more than ½ mile from such a stop are relabelled as in item 48. The result is accepted even if this removes most of a case's lots. If no lot is left within ½ mile, the case is ruled out as "not transit-linked".
- **Corridor reforms:** the ½-mile ring is kept. Each case's study-area acres and its share of the city's homes are reported.
- **Denver's incentive overlay (IO-1):** extra height is earned by providing affordable homes. It counts as a raised allowance, like Los Angeles's transit incentive program. It is flagged, and a second version scores only lots whose base zone allows more (for example, industrial I-A to mixed-use I-MX-8).
- **No refit:** the central line (1,181) is not refitted with the new cities until this test is reported. Any refit is a separate, later step.

### Candidates logged so far

| Case | Status |
| --- | --- |
| Denver 2018, 38th & Blake station area (ordinances 15 and 17 of 2018; incentive overlay IO-1 and design overlay DO-7; Five Points, Elyria Swansea, Globeville, Cole) | Qualifies (rail station 38th & Blake, A Line, open 2016) |
| Denver 2016, 61st & Peña station area | To check: the station opened in April 2016; the rezoning date is to be confirmed against it |
| Austin ETOD overlay, May 2024 | Ruled out: under 3 after-years |
| Austin Vertical Mixed Use, 2006–2008 | To check: no rail or rapid open then (MetroRail opened 2010; MetroRapid 2014), so it is likely "not transit-linked" |
| Austin TOD districts (Plaza Saltillo, MLK, Lamar/Justin; about 2005–2008) | To check: they were planned around MetroRail stations, which opened in March 2010 |
| Portland Mixed Use Zones, 2018 | To check: share of the area within ½ mile of MAX or streetcar |
| Portland Better Housing by Design, 2020 | To check: the same |

## Results so far

**Denver 2016, 61st & Peña: ruled out** before counting. Ordinance 347 of 2016 kept every base zone (C-MU-30 to C-MU-30, C-MU-20 to C-MU-20, and so on) and changed only overlays (airport influence). No allowance was raised.

**Denver 2018, 38th & Blake (run 2026-11-01): `reference/tod_new_city_test_denver_2018.csv`.** Data and placement:
- **Permits:** Denver's residential and commercial construction permits, "new building" with units. Apartments are filed as commercial permits; a first pass that read only the residential file found about 230 homes and was corrected before scoring.
- **Placement:** each permit is placed on the lot whose shape holds its point, with the schedule number as fallback.
- **Windows:** before, July 2012 to 2017 (5.5 years); after, 2019–2023.
- **Study area:** 8,313 lots, 4,782 acres. Upzoned lots more than ½ mile from a rail station open in 2018 are relabelled (75 lots).

| Version | Upzoned lots (acres) | Share before | Share after (actual) | Drift rule | Average change | Same share |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Main (incentive overlay IO-1 or a higher base zone) | 447 (404) | 2.4% (88 of 3,650) | **45.0%** (2,638 of 5,859) | 17.6% (score 0.94) | 6.4% (1.96) | 2.4% (2.93) |
| Base zone only | 86 (47) | 0.0% (1 of 3,650) | **19.8%** (1,159 of 5,859) | 16.1% (0.21) | 4.0% (1.60) | 0.0% (6.58) |

Scores are |log(predicted ÷ actual)|; lower is better. In both versions the drift rule beats both benchmarks. In the main version, all three under-predict the rise: the actual share went from 2% to 45%.

Audit notes on Denver (2026-11-01):
- **Commercial-permit fix:** it was committed in the same commit as the results, so git cannot show that it came before scoring. The first pass's output (about 230 homes) was read before any share was computed.
- **Placement in the study area:** the 0.548 match rate is citywide. Inside the study area, July 2012–2023 new-building permits hold 10,137 homes; 10,002 were placed by point, 18 by schedule number, and 117 (1.2%) were not placed. Inside the reform area: 4,306 by point, 0 by number, 56 not placed, out of 4,362. Outside it, in the ring: 5,696 by point, 18 by number, 61 not placed, out of 5,775.
- **Scoring:** Denver counts once in the median, using the main version. The base-zone-only version (1 home of 3,650 before) is a check only.
- **Reading:** the drift rule wins but misses the size, 17.6% predicted against 45.0% actual.

## Search scope for Austin and Portland (logged before any of their permits are counted; audit review sections 5–6)

**Scope (both cities):** every city zoning change adopted 2010–2020 that raised allowed homes on a mapped area within ½ mile of a rail or bus rapid transit stop open on the adoption date, with at least 3 years of permit data before and 3 after.

- **Austin rapid stops:** MetroRail (opened March 2010); MetroRapid 801 and 803 (January 2014 and August 2014).
- **Portland rapid stops:** MAX light rail and the Portland Streetcar, using each line's opening date.

**Sources searched for zoning changes:**
- Portland: the city's zoning-proposal layers, which hold the existing and adopted zone for each mapped change (`BPS_Planning_Projects`, base zone proposals, status "adopted" or "amended").
- Austin: the city's zoning cases with ordinance numbers and dates (to search).

Every change found is logged below as qualifies or ruled out, with the reason. All that qualify are scored. Permits are not looked at by area before this log is complete.

**Permit data limits found:** Portland's published permit layers run 2005–2022 by year, with a field for new units (`NUMNEWUNITS`). So a Portland change needs to be adopted by 2019 to have 3 after-years.

### Log

| City | Change | Adopted | Status | Reason |
| --- | --- | --- | --- | --- |
| Austin | TOD regulating plans: Plaza Saltillo, MLK, Lamar/Justin | 2008–2009 (effective March 2009 for Saltillo and MLK) | Ruled out | Before MetroRail opened (March 2010): no rapid stop open on the adoption date |
| Austin | ETOD overlay | May 2024 | Ruled out | Under 3 after-years |
| Austin | Search done 2026-11-01: City of Austin zoning cases (open data `edir-dcnf`), approved 2010–2020 with the City as applicant (85 cases), plus "Neighborhood Planning" cases (29 approved, none a zoning change) | — | — | — |
| Austin | Bouldin Vertical Mixed Use (C14-2007-0220), 764 acres | 17 Dec 2012 | Ruled out | MetroRapid 801 on South Congress opened January 2014; no rail or rapid stop within ½ mile open on the adoption date |
| Salt Lake City | 2010 transit station-area districts on the North Temple line (SLC_CENSUS_RESULTS.md) | 2010 | Ruled out under this test | The North Temple TRAX line opened in 2013, so no rail stop was open on the reform date. It was measured in October with 2010 and 2020 census blocks, not permits, so it has no before window for the share test. That result: +0.92 homes per acre over the decade, interval −2.15 to +3.97 |
| Austin | Garrison Park neighborhood plan combining district (C14-2014-0019), 1,258 acres; part of the South Austin Combined Plan | Adopted 6 Nov 2014 as ordinance 20141106-088 (amended 11 Feb 2016) | Ruled out: no day-one map (data reason, as pre-set) | It is a neighborhood plan combining district: mostly residential infill options (such as secondary apartments and small lots), which are ADU-type allowances, plus possibly some base rezonings. Public GIS holds no from/to zones. The city's zoning-ordinance polygons have no zones, and the case lists them as "see comments". Settling it needs the ordinance documents read tract by tract. MetroRapid 803 (opened August 2014) runs nearby on South Lamar and at Westgate |
| Austin | Parks, greenbelts and historic designations (about 70 cases) | 2011–2018 | Ruled out | Do not raise allowed homes (to P-Public or adding H) |
| Austin | PUD amendments and single sites (Estancia, North Austin Medical Center, Lamar/Manchaca and others) | 2011–2018 | Ruled out | Single-owner or applicant-led changes, not a city policy area (see the note below) |

**Note on the scope (added before any Austin or Portland permit is counted):** "zoning change" means a city-initiated change covering many owners, like Denver's legislative ordinances. Rezonings requested by one owner for one project are left out. They are chosen because a project is coming, so their share of new homes after would rise by construction, not by policy.
| Portland | Mixed-use zone conversion and 2035 Comprehensive Plan map (CS/CG/CM/CN/CO to CM1/CM2/CM3/CE, citywide centers and corridors) | Effective 24 May 2018 | Qualifies on data (2026-11-01) | The city's zoning archive (`PPD_Zoning_Archive`) publishes the whole zoning map before 24 May 2018 (layer 91) and from 25 May 2018 (layer 3). Each lot's zone is read from both. Before window 2012–2017, after window 2019–2023. Raised allowed homes judged by the table below |
| Portland | Map amendments "mp" (IG1/IH/EG to EX/EG1; industrial to central employment, which allows homes) | To confirm | To check | 9 polygons |
| Portland | Better Housing by Design ("bhd"), 1,296 adopted zone changes | Effective 1 March 2020 | Qualifies on data (2026-11-01 data check) | The earlier "permits end 2022" was wrong: the city's current permit layers (`BDS_Permit`, residential and commercial construction, with `NUMNEWUNITS`) run 1996–2026. Before window 2014–2019, after window 2021–2025. Raised allowed homes judged by the table below |
| Portland | 82nd Avenue study map amendments | Adopted 30 May 2019 | To check | 21.5 acres, mostly employment zones (EG1, no homes); a few R5 to R2 and R5/R2.5 to CE (homes raised). After-years 2020–2022 (3). Needs a MAX stop within ½ mile |


**Existing 9 cities, checked against the city-initiated rule:** all nine are city-initiated, area-wide reforms:
- New York's pooled rezonings (city-led area rezonings);
- Philadelphia's zoning remapping;
- Charlotte's 2019 TOD ordinance;
- Saint Paul's Green Line rezoning;
- Los Angeles's Warner Center and Cornfield Arroyo Seco specific plans;
- Seattle's station-area legislative rezonings;
- Chicago's 2015 TOD ordinance;
- Madison's 2023 transit overlay;
- Bellevue's BelRed plan.

None of them is a single-owner, single-site rezoning, so the rule matches them.

**Portland zone capacity table (logged before any Portland permit is counted).** Allowed homes per acre, from Title 33. Densities are as written; floor-area zones are turned into homes at 1,000 square feet per home.

| Zone | Before 2020 | Homes per acre | Zone | From 2020 | Homes per acre |
| --- | --- | ---: | --- | --- | ---: |
| R5 | 1 per 5,000 sq ft | 8.7 | RM1 | floor area 1.0 | 43.6 |
| R3 | 1 per 3,000 sq ft | 14.5 | RM2 | floor area 1.5 | 65.3 |
| R2 | 1 per 2,000 sq ft | 21.8 | RM3 | floor area 2.0 | 87.1 |
| R1 | 1 per 1,000 sq ft | 43.6 | RM4 | floor area 4.0 | 174.2 |
| RH | floor area 2.0 (base) | 87.1 | | | |

Upzoned means homes per acre rose:
- R2→RM1, R1→RM2, R3→RM1, R5→RM1 and RH→RM4 are upzoned.
- RH→RM3 is equal, so not rising.
- RH areas mapped at floor area 4:1 before (some central areas) would make RH→RM4 equal too. This is flagged and checked in a second version that leaves out RH→RM4.

**Outcome so far, if Denver stays the only new case:** "1 new case: the drift rule beat both benchmarks but under-predicted (17.6% vs 45.0%)." One case can neither confirm nor overturn the central line, so 1,181 stays.

**Portland BHD, settled before counting (audit review section 8):**
- **Versions:**
  - main (all raises in the table);
  - leave out RH→RM4 (RH may have been 4:1 already);
  - leave out R1→RM2 (473 changes). At about 1,500 sq ft per home, RM2 allows about what R1 did. Its lots stay in the study area as not upzoned.
- **Residential Infill Project (effective August 2021):** it raised allowed homes on most single-dwelling lots citywide, inside BHD's after window, so many ring lots also rose. The day-one groups are kept. Ring homes on single-dwelling (Infill-Project) lots are reported separately.
- **½-mile rule:** stops are MAX and Portland Streetcar stops open in March 2020. Division FX2 bus rapid transit opened in 2022 and does not count. BHD is citywide, so many upzoned lots will be relabelled; this is accepted in advance and the count is reported.
- **Also in the before window:** the 2017 inclusionary housing rule (mandatory affordable homes in buildings of 20 or more units). It may have pulled permits forward into early 2017.


**Portland 2018 capacity table (logged before counting).** Base floor area from Title 33 (2017 code for the old zones, 2018 code for the new), turned into homes per acre at 1,000 square feet per home (× 43.56). Residential zones use the BHD table above, with R2.5 at 1 home per 2,500 sq ft (17.4) and R7 at 1 per 7,000 (6.2). Employment and industrial zones that allow no homes count as 0.

| Old zone | Floor area | New zone | Floor area |
| --- | ---: | --- | ---: |
| CN1, CN2, CO1 | 0.75 | CM1 | 1.5 |
| CO2 | 2.0 | CM2 | 2.5 |
| CM (old mixed commercial) | 1.0 | CM3 | 3.0 |
| CS, CG | 3.0 | CE | 2.5 |
| CX | 4.0 | CX | 4.0 |
| EX | 3.0 | EX | 3.0 |

"Upzoned" means homes per acre rose. On paper CS→CM2 and CG→CE are falls: base floor area went from 3.0 to 2.5. In practice CS was capped at 45 feet. That is accepted as written and flagged. A second version counts only lots whose zone changed from residential, employment or industrial to a mixed-use zone.

The same archive will be used to check BHD's lot zones (archive layers before and after 1 March 2020) against the proposal layer.

**Portland 2020, Better Housing by Design (run 2026-11-01): `reference/tod_new_city_test_portland_2020.csv`.**
- Study area: 193,507 lots, 49,703 acres. Upzoned: 8,600 lots in the main version; 13,999 upzoned lots more than ½ mile from MAX or streetcar were relabelled.
- Placement: 17 of 31,305 homes before and 4 of 16,638 after were not placed.
- Ring homes on single-dwelling (Infill-Project) lots: 4,165 before, 2,735 after.

| Version | Share before | Share after (actual) | Drift rule | Average change | Same share |
| --- | ---: | ---: | ---: | ---: | ---: |
| Main | 4.2% (1,300 of 31,198) | 5.2% (863 of 16,634) | 18.6% (score 1.28) | 8.1% (0.45) | 4.2% (0.22) |
| Without RH→RM4 | 2.9% | 3.8% | 17.8% (1.54) | 6.8% (0.58) | 2.9% (0.29) |
| Without R1→RM2 | 2.5% | 3.6% | 17.6% (1.58) | 6.5% (0.59) | 2.5% (0.36) |

**Portland 2018, mixed-use conversion and Comprehensive Plan map (run 2026-11-01): `reference/tod_new_city_test_portland_2018.csv`.** Lot zones were read from the archive before 24 May 2018 and from 25 May 2018; 22,869 lots changed zone.
- Study area: 211,347 lots. Upzoned: 1,976 lots in the main version; 4,952 relabelled for being more than ½ mile from rail.
- Placement: 62 of 27,405 homes before and 0 of 20,602 after were not placed.

| Version | Share before | Share after (actual) | Drift rule | Average change | Same share |
| --- | ---: | ---: | ---: | ---: | ---: |
| Main | 3.9% (1,056 of 27,344) | 3.1% (638 of 20,602) | 18.4% (1.78) | 7.8% (0.93) | 3.9% (0.22) |
| Into mixed use from other zones only | 1.3% | 0.9% | 16.9% (2.88) | 5.3% (1.72) | 1.3% (0.34) |

**Score so far: 3 new cases from 2 cities, main versions.** Austin's Garrison Park (2016) is still to check under the search log. As a third city, it could break the tie.

| Case | Drift rule | Average change | Same share |
| --- | ---: | ---: | ---: |
| Denver 2018 | 0.94 | 1.96 | 2.93 |
| Portland 2020 | 1.28 | 0.45 | 0.22 |
| Portland 2018 | 1.78 | 0.93 | 0.22 |
| **Median** | **1.28** | **0.93** | **0.22** |

**Outcome: inconclusive** (audit review, 2026-11-01).
- The two Portland cases share a city, study areas and windows, so they are not independent. The plan did not say how to merge cases from one city.
- Counting each case: same share wins (median 0.22).
- Counting Portland once (mean of its two cases): the medians over Denver and Portland are drift 1.24, average change 1.32, same share 1.58, so drift narrowly wins.
- So the central line stays at 1,196 unless the owner decides otherwise, and "about 0" is shown as a sensitivity.
- Infill Project check: per year, single-dwelling ring homes fell 21% (694 to 547), against 36% for the whole study area (5,200 to 3,327). It barely affected the result.

Caveats:
- One case can flip the median.
- The two Portland reforms were citywide re-codings with modest raises; Denver's was a targeted station-area upzoning. In Denver the share rose far more than any rule predicted. This is a caveat only, not a pre-registered split. It matches the 9 training cities, where low-share cases ranged from 0 (Bellevue) to +0.34 (New York).
- Portland's study areas are most of the city, so "share" there is diluted by citywide building.

**Garrison Park (Austin), settled before any permit is read (audit, 2026-11-01):**
1. Infill options are scored by allowed homes per acre, before vs after. A secondary apartment adds 1 home per lot. A small-lot option uses the homes per acre implied by the new minimum lot size.
2. "Upzoned" means lots where that figure rose, taken from the ordinance's day-one tract map. Base rezonings use the Austin zone table.
3. Windows: before 2009–2014, after 2015–2019, on the 5-year basis.

If the ordinance cannot be read tract by tract, the case is logged as "ruled out: no day-one map" (a data reason).

**Garrison Park, 2026-11-01:** the ordinance (20141106-088) and its tract exhibits could not be found in public form. The city's document system, ordinance chart and council pages give only the number and short descriptions. Without a tract-by-tract day-one map it is ruled out, as pre-set. No permit was read.

**Final state of this test: 3 cases from 2 cities (Denver, Portland ×2). Inconclusive.**
- Counting Portland once, the drift rule narrowly wins: median 1.24, against 1.32 for average change and 1.58 for same share.
- Counting each case, same share wins (0.22).
- The central line stays at 1,196 unless the owner decides otherwise. "About 0" is shown as a sensitivity.

## Owner rule change, 2026-11-01 11:11 (after the Denver and Portland results were seen)

Owner: "developers know a rail line is being planned ahead of its opening ... This is a trait (transit stop not opened at time of reform) not a disqualifier."

- **"Rapid stop open on the reform date" is dropped as a reason to rule a case out.** A stop that was planned or under construction on the reform date counts, if it opened later. Whether the stop was open on the reform date is recorded as a trait: `stop_open_at_reform` (yes or no), with years until opening.
- **Windows** stay anchored on the reform date. As a second version, the after window starts when the line opens.
- **Reopened:**
  - Austin TOD regulating plans (Plaza Saltillo and MLK, effective March 2009; Lamar/Justin, 2008); MetroRail opened March 2010.
  - Austin Bouldin VMU (Dec 2012); MetroRapid 801 opened January 2014.
  - Salt Lake City station-area districts (2010); the North Temple line opened 2013. It needs permits with home counts; the October work used census blocks only.
- **Not reopened:** Denver 61st & Peña, ruled out because no base zone was raised; Austin ETOD 2024 (too few after-years); Garrison Park (no day-one map).
- The change was made after results were seen and is labelled as such. The already-scored cases do not change, since all three had stops open.

**Settled before counting any Austin or Salt Lake City permit (audit, 2026-11-01 11:12):**
1. **"Planned" stops:** stops in the alignment that was adopted or funded on the reform date, taken from a dated plan document, never "stops eventually built". A stop moved or cancelled later is kept at its planned place. Sources:
   - **Austin 2008–09 TOD plans:** the stations named in each station area plan itself (Plaza Saltillo Final SAP, adopted Dec 2008; MLK Jr. Blvd. Final SAP, March 2009; Lamar/Justin Final SAP, 2008). Capital Metro's commuter rail was approved by voters in November 2004 ("All Systems Go").
   - **Austin Bouldin VMU 2012:** MetroRapid route 801 stops as funded in Capital Metro's federal Small Starts grant (2011–2012). The stop list is taken from the funding document.
   - **Salt Lake City 2010:** the Airport TRAX (North Temple) line stations as funded under UTA FrontLines 2015 (approved 2006; the line was under construction from 2008).
2. **Windows:** the reform-date window is the main version. The window starting at line opening is a labelled second version.
3. **The city is the unit.** Each city's cases are averaged into one score, with the per-case results shown beside it. This applies to Portland (2 cases) and Austin (3–4) too.
4. **The trait `stop_open_at_reform`** is filled for every case, including the 9 training cities. Charlotte's LYNX Blue Line opened in November 2007; some Charlotte rezonings came earlier.
5. **No refit.** The trait is recorded only, and is not used in this test.

**Noted, not adjusted** (owner's rule): Austin's 2008–09 windows run through the Great Recession. Austin's permit data (Issued Construction Permits, `housing_units`) starts long before 2003; new-construction building permits with homes are present every year from 1980.

**Data found for the reopened cases (2026-11-01, before any permit is counted):**
- **Austin regulating plans:** the city publishes subdistrict maps for five plans, with floor area, height and density limits (`PLANNINGCADASTRE_regulating_plan_subdistrict`): Plaza Saltillo (PS), MLK, Lamar/Justin (LJ), and two plans not yet in the log, North Burnet/Gateway (NBG, about 2009, around the Kramer station) and East Riverside Corridor (ERC, 2013). The maps are the plans as amended to 2024–2025, not day-one maps. The day-one maps exist only as images in the original plan PDFs. The pre-plan zoning is not in public GIS.
- **Salt Lake City 2010:** the October study used a 2020 zoning snapshot for the district boundary, since the 2010 ordinance map is no longer online. For homes, the Utah Housing Unit Inventory (statewide GIS, units and year built per parcel) can stand in for permits, counting completions as Milwaukee's property file does.

**Open question for the owner and the audit:** use today's amended maps as a stand-in for the day-one maps, flagged for hindsight, or rule these cases out under "no day-one map"? Using today's maps risks counting later rezonings, which were made because building came, as part of the reform.

## Austin day-one maps, committed before any Austin permit is loaded (2026-11-01)

**File:** `reference/tod_austin_dayone_regulating_plans.geojson`, the city's regulating-plan subdistrict polygons for Plaza Saltillo, MLK and Lamar/Justin (566 polygons; 96, 87 and 178 acres).

**Check against the original plans** (archived copies in `data/raw/tod_new_cities/austin/plans/`):

| Plan | Original | Revisions | What the revisions changed | Day-one map |
| --- | --- | --- | --- | --- |
| Lamar/Justin | Adopted 11 Dec 2008, effective 1 Mar 2009 | None on the archived copy | — | Today's polygons; outer boundary matches the adoption cover map |
| MLK | Approved 12 Mar 2009, effective 23 Mar 2009 | 24 May 2012 (ordinance 20120524-128) | The district outline on the revised cover matches the adopted subdistrict pattern | Today's polygons; boundary unchanged |
| Plaza Saltillo | Adopted 11 Dec 2008, effective 1 Mar 2009 | 2013, and twice in 2018 | 2018 added a fifth subdistrict, "TOD Urban Mixed Use", on the Capital Metro tract; it is mapped back to its day-one subdistrict (TOD Mixed Use) | Today's polygons; boundary unchanged |

**Rules:**
- **Upzoned:** every lot in a regulating-plan subdistrict, except right-of-way (TROW). The TOD base district replaced the earlier zoning with TOD subdistricts. Version 2 leaves out the low-density residential subdistrict (TOD LDR).
- **Pre-plan zoning:** not in public GIS. Whether each lot's allowed homes rose is assumed from the subdistricts (flagged).
- **Reform date:** main version 1 March 2009 (the regulating plans). Version 2 uses May 2005, the TOD ordinance that first drew the district boundaries with interim rules.
- **Windows:** main, before 2003–2008 and after 2010–2014. Version 2, before 1999–2004 and after 2006–2010.
- **Stops:** the planned MetroRail stations named in each station area plan (Plaza Saltillo, MLK, Crestview/Lamar-Justin), from the station list. Not open on the reform date (MetroRail opened March 2010); recorded as a trait.
- **North Burnet/Gateway (about 2009) and East Riverside (2013):** no original map could be found, in the archive or on the city site. Ruled out as "no day-one map" unless one is found.
- **Austin is one city:** the three plans are scored together as one case.

**Austin TOD regulating plans (run 2026-11-01): `reference/tod_new_city_test_austin.csv`.**
- Study area: 11,602 lots, 3,265 acres. Upzoned: 281 lots (177 acres). 550 lots in plan areas more than ½ mile from the three planned stations were relabelled; most are MLK's eastern patches.
- Placement: 0 homes before and 1 after were not placed.
- Stops were not open on the reform date (trait).

| Version | Share before | Share after (actual) | Drift rule | Average change | Same share |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2009 plans (main) | 3.9% (93 of 2,368) | **23.9%** (592 of 2,472) | 18.5% (score 0.26) | 7.9% (1.11) | 3.9% (1.81) |
| 2009, without low-density residential | 1.7% | 23.9% | 17.1% (0.33) | 5.7% (1.43) | 1.7% (2.62) |
| 2005 TOD ordinance date | 0.5% (6 of 1,146) | 10.4% (206 of 1,979) | 16.4% (0.46) | 4.5% (0.84) | 0.5% (2.99) |

**By city, main versions, Salt Lake City still to come.** The city is the unit; Portland is the mean of its two cases.

| City | Drift rule | Average change | Same share |
| --- | ---: | ---: | ---: |
| Denver | 0.94 | 1.96 | 2.93 |
| Portland (mean of 2) | 1.53 | 0.69 | 0.22 |
| Austin | 0.26 | 1.11 | 1.81 |
| **Median** | **0.94** | **1.11** | **1.81** |

So far the drift rule beats both benchmarks on the city median. The two station-area upzonings (Denver, Austin) jumped and the drift rule came closest. Portland's citywide re-codings barely moved.
