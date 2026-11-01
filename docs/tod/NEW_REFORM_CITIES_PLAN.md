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
