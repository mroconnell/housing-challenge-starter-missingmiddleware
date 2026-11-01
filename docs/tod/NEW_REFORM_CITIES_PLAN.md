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
| Austin | Later changes 2010–2020 | — | To search | Zoning cases |
| Portland | Mixed-use zone conversion (CS/CG/CM/CN to CM1/CM2/CM3/CE, citywide centers and corridors) | 2018 (effective May 2018) | Not testable from public GIS yet | The proposal layers hold no from/to zones for it (the "mp" entries are 9 small industrial/employment polygons). Needs Portland's 2017 zoning snapshot: Metro RLIS archive or a request to the city's GIS team |
| Portland | Map amendments "mp" (IG1/IH/EG to EX/EG1; industrial to central employment, which allows homes) | To confirm | To check | 9 polygons |
| Portland | Better Housing by Design ("bhd") | 2019 (effective March 2020) | Ruled out | Permit layers end in 2022: 2 after-years |
| Portland | 82nd Avenue study map amendments | Adopted 30 May 2019 | To check | 21.5 acres, mostly employment zones (EG1, no homes); a few R5 to R2 and R5/R2.5 to CE (homes raised). After-years 2020–2022 (3). Needs a MAX stop within ½ mile |
