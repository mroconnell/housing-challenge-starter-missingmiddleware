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
