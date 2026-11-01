# Parking: adjusting the repeal comparison for local boom and bust, and longer windows, plan written before running

Written 2026-11-01 by the parking conductor. Ryan: "I like tying in BLS, and car ownership rates in the city? and ridership rates for the mass transit in the city? And yeah, try longer windows too." No result below has been computed before this file was committed.

## A. Adjusting for local boom and bust

**Idea.** Predict each place's change in permits (after minus before) from what happened to its local economy, using places that never repealed. Then ask whether repeal places changed more or less than predicted.

**Data (public, every state):**

| Trait | Source | Level | Years |
| --- | --- | --- | --- |
| Job growth | BLS QCEW, all industries, total covered employment, annual average (`data.bls.gov/cew/data/api/{year}/a/industry/10.csv`) | county | 2012–2025 |
| Wage growth | same, average annual pay | county | 2012–2025 |
| Car ownership | ACS 5-year B25044: households with no vehicle; vehicles per household | place / county subdivision | release ending 2019 (before most repeals) |
| Transit use | ACS 5-year B08301: share of workers commuting by public transit | place / county subdivision | release ending 2019 |

Transit agency ridership (the National Transit Database) is reported by agency, not city, so the commute share stands in for it. This is noted.

**Rows.** Every never-reformed place with at least 1,000 homes, each given a "window" at each repeal year used by the 76 cases: 5 years before and 1–3 after, as in the headline.

- **Outcome:** the change in permits per 1,000 existing homes per year, after minus before.
- **Inputs:**
  - the county's job growth and pay growth over the same before and after years;
  - the place's car ownership and transit share;
  - its before-rate;
  - log homes;
  - its state's change over the same years (the regional level).

**Models:**
- weighted least squares;
- a random forest.

Both are fitted on never-reformed places with whole states held out (5 groups of states), and scored on held-out states.

**Adjusted effect.** For each repeal place: its actual change minus the model's predicted change. It is averaged with home × after-year weights, with a 90% resampling range, and set beside the headline −1.14.

**Noise check.** The same adjusted effect for 76 never-reformed places drawn at random with the real years (5 seeds), using fits that leave them out.

**Also reported:**
- how much of the never-reformed places' change the traits explain (held-out R²);
- San Francisco's and Minneapolis's adjusted effects.

## B. Longer windows

Years 4–7 after repeal exist only for repeals in 2018 or earlier (6 places), and years 4–6 for 2019 (5 more). The year-by-year effect path (`comparison.event_path`) is reported for k = 1 to 7 with the number of places at each k. It is described, not used for the tool: 6 to 11 places cannot support an estimate.

## Use

If the adjusted average moves clearly away from the noise check, it goes to Ryan as a candidate for the central or low line. The tool does not change from this run.

## Changes after writing
