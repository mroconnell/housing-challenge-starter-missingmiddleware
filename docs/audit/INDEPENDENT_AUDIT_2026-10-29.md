# Independent audit of all work so far

Written 2026-10-29 by a separate cloud session, at Ryan's request. Nothing in the model was changed. No reference number used by the tool was changed. This file and one new list of checked sites (`reference/tod_overdense_site_audit.csv`) are the only additions.

## What was audited

- **Commit:** `main` at `0b2018e` (2026-10-29 06:24 CET). It holds:
  - TOD up to plan item 28 (`056bbeb`) and the over-dense lot list (`0b2018e`);
  - ADU up to AQ-063 (`5630a90`);
  - parking up to `60b2307`.
- **Read after the main audit:** plan items 29 to 31 (`a0bfc74`, `00aa0b3`, `81c8efb`). Item 31 is the new lot-group rule. Section 2b checks it.
- **Not yet audited:** the rebuilt lot table under item 31, the causal-forest refit, and the new Wisconsin lot estimate. They were still running on Ryan's Mac.
- **How:** I read the code and docs. I also read the raw city files on Ryan's Mac (New York building jobs and lot maps, Chicago, Philadelphia and Seattle permits) and the TOD lot table. No raw data or ids are committed.

## The short answer

- **No finding changes a headline number in the tool.**
  - ADU stays 6,734 / 10,788 / 20,057 extra permits.
  - Parking stays 0 / 19,937.
  - TOD stays 171 / 2,509 / 17,148.
  - Reason: the headlines rest on other states, the federal permit survey and three published studies. They do not rest on the city cases below.
- **The TOD city cases and the TOD lot model have real counting mistakes.** These feed the lot model (the candidate "extra line"), the Madison test, and the case numbers quoted in the docs.
- **The over-dense lots are mostly real towers.** Ryan was right. But two other mistakes hide among them:
  - New York hotel rooms are counted as homes;
  - Chicago counts some towers twice.
- **Flagging the 94 lots is not enough.** The same two mistakes sit in many lots below 500 homes per acre too.

## Ranked findings

Rank is by how much the finding could move a result Ryan relies on. "Lot model" means the TOD lot-level model and its scoring.

| # | Finding | Kind of mistake | What it moves | Size |
| ---: | --- | --- | --- | --- |
| 1 | New York hotel rooms are counted as homes | Counting | TOD New York cases, lot model | At least 28,950 of 340,490 "homes" in New York new-building jobs 2003–2015 (8.5%) are in buildings the city's lot data later class as hotels. In the Hudson Yards rezoning, hotel rooms are at least 1,570 of about 2,900 homes on upzoned land (over half). |
| 2 | Lot areas are pre-assembly fragments, and real towers pass 500 homes per acre | Unit / geometry | Lot model traits; the 500-per-acre flag | 9 checked towers sit on lots 2 to 14 times smaller than their real site. 7 of 12 real sites still exceed 500 homes per acre (282 to 876). |
| 2b | The "FAR" column still mixes different measures: Madison's is height, and Wisconsin's is a third kind | Unit mix-up (same kind as Charlotte) | Lot model, Madison holdout, Wisconsin estimate | Madison prints no FAR. Its "FAR" is stories × 70% coverage. The Wisconsin run uses allowed homes instead. The same Madison lot can get FAR 1.4 in training and 0.49 in the Wisconsin run. See section 2c. |
| 3 | **Mostly fixed by item 31.** The "rezoned later" trait still carries the project | Trait known only after the fact | Lot model; Wisconsin estimate | Items 29–30 counted developer petitions as upzoning (about 9,700 homes on 1,000 Charlotte acres). Item 31 drops that: groups now follow the day-one map. But "rezoned later" is now a trait. A rezoning often happens because a project is coming. And no Wisconsin lot can have it on day one. See section 2b. |
| 4 | Madison's measured effect rests on 187 acres of comparison land | Thin comparison | Lot model holdout score; Madison test | Comparison land went from 421 homes before to 0 after. That alone gives Madison 2,069 extra homes. Against the overlay's own lots whose density did not rise, the effect is about zero. |
| 5 | Chicago counts some buildings twice (foundation permit plus full permit) | Counting | TOD Chicago case, lot model | About 5,600 of 88,372 Chicago permit units in 2009–2025 (6%), of which about 2,800 in 2016–2020, Chicago's after years. |
| 6 | Saint Paul loses 44% of its upzoned homes to the duplicate-lot weight | Counting | Lot model; Saint Paul actual | Homes on upzoned land after reform: 670 counted, 376 after the weight. Also only 1 year before the reform, multiplied by 5. |
| 7 | The "unchanged" forest learns from every non-upzoned lot; the yardstick uses eligible comparison lots only | Training vs scoring definition | Lot model pass or fail | 29% of the forest's rows are other groups (in-reform lots whose density did not rise, rezoned again, already allowed, parks). They grow 1 to 4 homes per acre, against 0.36 on comparison land. |
| 8 | "Missing" flags act as city labels, and Wisconsin lots are all "missing" | Training vs Wisconsin definition | Wisconsin lot estimate | Homes on the lot are known only in New York, Los Angeles and Seattle. Wisconsin lots are all marked missing, although Milwaukee's property file has the count. |
| 9 | Thin-comparison rule mixes two methods, and 25% does not protect small reforms | Thin comparison; rule changed after results | Lot model scores | One New York reform with 2 comparison acres scores −2,117 homes from a single project. Thin reforms are scored before-versus-after with no time trend. |
| 10 | Philadelphia: one permit for many townhouses lands on one tiny lot; the duplicate filter also merges separate homes | Geometry; counting | TOD Philadelphia case | Small per lot. Also a citywide permit rush in 2021 (26,777 units, five times a normal year) falls in the after years of the 2016–2020 reforms. |
| 11 | Los Angeles Cornfield Arroyo Seco shows 0 homes on 197 upzoned acres, before and after | Possible matching gap | Los Angeles actual (−585) | Needs a check: permit matching, or park land counted as upzoned. |
| 12 | Parking comparison places may include partial reformers; homes from 2020–2024 are the denominator in every year | Contamination; later data in earlier years | Parking central and high end | Not sized. Probably small. Weighting matters more: unweighted average +0.42, weighted −1.14 permits per 1,000 homes per year. |
| 13 | Stale numbers in shared docs | Documentation | Readers | Model & Assumptions says the median repeal place is −0.50; the data say −0.12. DELIVERABLES_STATUS still shows the old ADU numbers (605; 8,757). |
| 14 | Small code hazards | Code | Future runs | See the last section. None changed a committed result. |

## 1. The over-dense lots: what is really at those sites

Ryan asked for a check of the real sites, and said "those just sound like skyscrapers". I matched every New York, Chicago, Philadelphia and Seattle lot in `reference/tod_lot_model_overdense_sites.csv` to the city's own permit records, by place and year. Then I read New York's later lot map (MapPLUTO 18v1) for building type, floors and lot area. Results per lot are in `reference/tod_overdense_site_audit.csv`.

### What I found

| Verdict | Lots | Homes |
| --- | ---: | ---: |
| Real building, same unit count as the city's permit or job | 80 | 10,659 |
| Real building, but the lot in our table is a fragment of the real site | 9 | 3,204 |
| Hotel rooms counted as homes (New York) | 19 | 3,683 |
| Same building counted twice (Chicago) | 2 | 862 |
| Small Philadelphia row-house lots (townhouse projects, repeats) | 21 | 356 |
| **All** | **131** | **18,764** |

- **Most are towers.** New York jobs show 12 to 44 floors. Chicago permits say "31-story residential tower", "27 story", "25 story" and so on.
- **The lot is often too small in our table, not the building too big.** Developers assemble several small lots into one site. Our table uses the lot map from before the reform, so the permit lands on one old fragment. Examples (homes per acre on our lot, then on the real site from the later lot map):

| Neighbourhood | Floors | Homes | Our lot (acres) | Real site (acres) | Per acre, our lot | Per acre, real site |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Hudson Yards, West 37th St | 43 | 835 | 0.102 | 1.360 | 8,186 | 614 |
| Hudson Yards, West 37th St | 23 | 394 | 0.056 | 0.784 | 7,036 | 502 |
| Garment District, West 38th St | 24 | 568 | 0.646 | 1.133 | 879 | 501 |
| West Chelsea, West 23rd St | 14 | 337 | 0.171 | 0.453 | 1,971 | 743 |
| Long Island City, 5th St | 42 | 522 | 0.474 | 1.851 | 1,101 | 282 |
| Long Island City, 50th Ave | 32 | 372 | 0.391 | 0.425 | 951 | 876 |
| Williamsburg, Green St | 6 | 130 | 0.149 | 0.975 | 872 | 133 |

- **Real towers do exceed 500 homes per acre.** On their real sites, 7 of these 12 checked buildings are above 500. So a fixed 500 cut would wrongly move or drop real homes.
- **Hotels.** 19 New York lots (3,683 "homes") are hotels. New York's building-job file counts hotel rooms as "dwelling units". The later lot map shows these buildings with hotel building classes and 0 residential units. They cluster on West 39th and 40th Streets (Hudson Yards), in Downtown Brooklyn, Hudson Square and Jamaica.
- **The hotel problem is much bigger than the flagged lots.** Across all New York new-building jobs fully permitted in 2003–2015, at least 28,950 of 340,490 "units" (8.5%) are in buildings later classed as hotels. Another 117,083 units could not be matched to the later map (mostly condominiums), so the true share is likely higher. Most of these hotels are below 500 per acre and are not flagged.
- **Chicago double counts.** The 805-home lot near North Avenue is one 31-to-32-floor tower. It was counted twice: a foundation permit for 400 units (2016) and a full permit for 405 units (2017). The duplicate filter only merges permits with exactly the same unit count. Citywide this misses about 5,600 units in 2009–2025.
- **Philadelphia.** Most flagged lots are 0.01 to 0.02 acres with 10 to 40 homes. Many are one permit for 13 to 22 townhouses placed on one row-house lot. A few are the same project filed several times at one point. One permit for a "single family dwelling" carries 10 units.
- **Seattle.** Both flagged lots are real apartment buildings (194 and 107 homes).
- **New York jobs are not double counted.** Repeat jobs on the same lot with the same unit count are about 2% of units, and almost none among buildings of 50+ homes.

### Is flagging alone enough?

No.
- The flag finds the symptom (a tiny lot), not the causes.
- Hotels and Chicago duplicates mostly sit below 500 per acre, so the flag misses most of them.
- And it flags real towers, which are fine.

### What I recommend instead

These follow the evidence above, and need no guessed threshold or distance.
1. **Remove hotel rooms in New York.** Best: use New York City Planning's Housing Database. It is the official cleaned version of the same building jobs. It counts permanent homes only ("Class A"), so hotel rooms are out. It is public. Simpler: drop jobs whose lot is later classed as a hotel in MapPLUTO.
2. **Use the real site.** Take the job's own tax lot from the first lot map after the permit year. Merge the old lots that fall inside it into one "site" row for the lot model. The TOD thread proposed this in item 28, and the table above shows it works.
3. **Merge Chicago's staged permits.** Treat permits at the same point within 18 months as one building when one is a foundation or partial permit, or when one cites the other's permit number, and the unit counts are within 10%. Keep the larger count.
4. **Philadelphia townhouse permits.** Spread each project over the lots it covers (the later subdivided lots), or treat the parent lot as the site.
5. **Then a flag from the zoning, not a fixed number.** Flag a lot whose homes exceed what its own allowed floor area could hold at, say, 400 square feet per home. That is specific to each lot and needs no city-wide guess.

## 2. The mid-range TOD cities, case by case

Ryan asked whether the middle cities have mistakes too, since the lowest (Los Angeles) and highest (New York) both did. They do. Numbers below are from the current lot table, on the 5-year basis, with each reform scored against its own comparison land (item 23 to 27 rules).

| City | Extra homes measured | Main concern |
| --- | ---: | --- |
| Madison | 2,069 | Rests on 187 comparison acres that went from 421 homes to 0 (finding 4). |
| Charlotte | 1,896 before item 29 | Petition rule withdrawn by item 31 (finding 3). |
| Saint Paul | 110 | 44% of upzoned homes lost to the duplicate-lot weight; 1 year before, times 5 (finding 6). |
| Seattle | 311 | One project is 68% of Othello's upzoned homes and another 66% of Mount Baker's. |
| Chicago | 122 | Staged permits counted twice (finding 5). 3,255 acres of downtown planned developments left out as not eligible. |
| Philadelphia | 5,789 (64 reforms) | Townhouse permits on one lot; 2021 permit rush in the after years (finding 10). |
| Bellevue | 0 | No homes in the window on either side; now scored with no comparison (thin). |

**Madison in more detail.** Inside the overlay, lots whose density did not rise grew from 1,476 to 2,589 homes. Upzoned lots grew from 552 to 976. Per year, both grew about 3.5 times. So against neighbours inside the overlay, the upzoning shows almost no extra effect. The big number comes only from the small comparison area outside, which happened to build nothing in 2023–2025. The pre-registered Madison test found 0.08 extra homes per acre per year, about 190 homes over five years on these acres. The lot model's yardstick says 2,069. These two cannot both be right.

**Charlotte and Chicago "rezoned again" (items 29–30).** These rules counted later rezonings that "took up" the reform as upzoning. Chicago's version was narrowed to drop planned developments after results were seen. Charlotte kept developer petitions. The two cities followed different rules. Item 31 withdraws both. Section 2b checks the new rule.

## 2b. The new lot-group rule (item 31)

**The rule.** A lot's group is fixed by the reform's map on the day it passed. Inside the zone with density up: TOD lot. Outside and nearby: comparison lot. Later rezoning is a trait, not a group.

**Verdict: this is the right rule.** It is one rule for every city. It is set before the rebuild. It does not depend on what got built. It ends the Chicago vs Charlotte mismatch.

**Ryan's question: is the method roughly right?** Yes. In plain steps:

1. Take cities that passed a TOD reform.
2. For each lot, note: did it get built on? How many homes? Inside or outside the zone?
3. Compare before vs after, inside vs nearby outside.
4. Check placebo cities, where nothing changed.
5. Train a model on these lots.
6. Apply it to Wisconsin lots, inside and outside a modelled zone.

We do not need to judge why each lot was built. That is correct. But two things still matter:

- **Count homes the same way everywhere.** Hotel rooms, double-counted permits and lot fragments (findings 1, 2, 4) still distort step 2. The new rule does not fix them.
- **Only use traits we would know in Wisconsin on day one.**

**One problem left: the "rezoned later" trait.**

- It is only known after the window ends.
- A rezoning often happens because a project is coming. So the trait partly records the outcome.
- The model will learn "rezoned later means many homes". That is true but not useful.
- No Wisconsin lot has this trait on day one. So every Wisconsin lot must get "no". The Wisconsin script does not yet set this column (checked at `81c8efb`). The trait's effect then helps fit training lots but never applies in Wisconsin.

Think of it like predicting who will win a race, using "crossed the finish line first" as a clue.

**Suggest:**

- Fit and score the model both with and without "rezoned later".
- Use the "without" version for Wisconsin.
- Report the "with" version only as a check.

**Ryan's scope note.** Wisconsin's modelled law can have fewer stops or a smaller radius. That keeps it closer to the training cases (about 8 times their upzoned lots now). This is a sound way to limit risk. It is a choice of law, not a model fix, so it can wait.

## 2c. Height or density read as FAR: other cities

Ryan asked if other cities had problems like Charlotte's (height read as FAR). I had not checked this city by city. I have now. Charlotte itself is fixed (plan item 12). Four problems of the same kind remain.

The model's "FAR" column feeds three traits: `far_now`, `rel_gain` (how much FAR rose, as a share) and `pays_room`. It also sets the lot ceiling. So the column should mean the same thing in every city.

**What each city puts in the "FAR" column:**

| City | What the column holds | Same as printed FAR? |
| --- | --- | --- |
| New York | Printed residential FAR | Yes |
| Chicago | Printed FAR | Yes |
| Saint Paul | Printed FAR. T4 has no limit (stored as blank). Industrial zones are stored as 0. | Mostly |
| Seattle | City capacity model FAR. Single-family zones are stored as 0. | Mostly |
| Madison | Stories × 70% lot coverage. Madison's code prints no FAR (0 of 44 rows in its rule table). | **No: it is height** |
| Wisconsin run (Madison, Milwaukee) | Allowed homes × floor area per home ÷ lot area | **No: a third measure** |
| Charlotte, Philadelphia, Los Angeles, Bellevue | Left out of FAR traits (rank only) | Correctly handled |

**Problem 1: Madison's "FAR" is height.**

- Madison is a holdout city. It is also one of the two Wisconsin cities.
- Madison's code limits stories and homes per acre. It prints no FAR.
- The code turns stories into FAR by multiplying by 70% coverage.
- This ignores the homes-per-acre limit. 23 Madison districts have one, and it is usually the tighter limit.
- The overlay adds stories. So Madison's "FAR rose" can mean "more stories allowed", even where allowed homes per acre stayed the same.

**Problem 2: training and Wisconsin use different measures for the same lot.**

- Madison training lots use stories × 70%.
- Madison and Milwaukee Wisconsin lots use allowed homes × floor area per home ÷ lot area. This one does include the homes-per-acre limit.
- Example: an SR-C1 lot (2 stories, 14 homes per acre).
  - Training "FAR" = 2 × 0.70 = 1.4.
  - Wisconsin "FAR" = 14 × 1,512 sq ft ÷ 43,560 = 0.49.
- So the same lot looks about 3 times denser in training than in the Wisconsin run.
- For "already built" districts (`existing_is_rule`), the Wisconsin "FAR" is the floor area of the homes that are there now. That is what is built, not what is allowed.

**Problem 3: zero and "no limit" are read as "no change".**

- The relative gain is "FAR added ÷ FAR before". When FAR before is 0, the code cannot divide. It then sets the gain to 0 but still marks it as "known".
- This hits Seattle single-family lots (stored as FAR 0) that were upzoned. These are some of the biggest upzonings.
- It also hits Saint Paul industrial lots (FAR 0) that were rezoned to housing.
- Saint Paul T4 has no FAR limit. It is stored as blank, so its gain also becomes "known 0".
- The model is told these lots got no added FAR. In fact they got the most.

**Problem 4: Seattle's before and after come from two different fields.**

- Before uses `MAXFAR` (2010 capacity model). After uses `RES_MAX_FAR` (2016 model, residential only).
- If the two fields measure different things, some lots will look upzoned or downzoned when nothing changed.
- Missing before-values are set to 0. A lot with a missing 2010 value and a 2016 value will look upzoned.
- I could not check this without the Seattle files. It should be checked on Ryan's Mac.

**Not a problem:**

- Philadelphia and Los Angeles use a rank of districts. They are kept out of FAR traits.
- Bellevue is a 0/1 flag. It is kept out of FAR traits (item 18).
- New York and Chicago also have homes-per-lot limits that the FAR column ignores. That is the same for every lot in those cities, so it is a smaller issue.

**Suggest one rule for every city:**

1. Use **allowed homes per acre** as the one measure. Work it out the same way everywhere: the lowest of the printed homes-per-acre limit, and printed FAR (or stories × coverage) ÷ floor area per home.
2. Use this same calculation for training lots and Wisconsin lots.
3. When the before-value is 0 or has no limit, mark the relative gain as "not known". Do not set it to 0.
4. Check Seattle's two fields on a sample of lots whose zoning did not change.
5. Add a sanity flag: for each city, print how many lots get their FAR from printed FAR, from height, from homes per acre, or from what is built now.

None of this changes the headline numbers. It changes the lot model's traits, so it should be fixed before the lot model is offered as an extra line.

## 3. TOD lot model and Wisconsin estimate: other checks

- **Item 25 fixes (forest sees the upzoning, use dropped, keys apart, 2024 dollars, rail and rapid stops, training-only fills, 2020 block homes):** the code does what the plan says.
- **The unchanged forest (finding 7).** It is fitted on every lot that was not upzoned, with the lot-group columns as traits. An upzoned lot is "in the reform" and "not comparison land", so the forest likens it to in-reform lots whose density did not rise, or that were rezoned again. The yardstick ("actual extra homes") uses eligible comparison lots only. So the model and the yardstick measure against different neighbours. Suggest: fit the unchanged forest on the same lots the yardstick uses, or score both ways.
- **Missing flags (finding 8).** `homes_missing`, `soft_missing` and `age = −1` are known only in some cities. A forest can use them as city labels. Wisconsin lots have all three missing, so they are treated like Philadelphia, Chicago or Charlotte lots. Suggest: fill homes on the lot for Milwaukee from its property file, or drop these traits from the forest.
- **Duplicate-lot weight.** The weight 1 ÷ (lots at the same point) is right when each copy carries the same homes (lots in two reforms; Philadelphia and New York). It undercounts when the homes sit on one copy (stacked lots in one reform; Saint Paul and Chicago). Suggest: weight only copies across reforms; for stacked lots in one reform, put the homes on the group once.
- **Thin comparison (finding 9).** Suggest: use the city's own trend from the federal permit survey as the comparison for thin reforms, and require a minimum in acres as well as 25%.
- **Construction cost.** Charlotte's cost is looked up as "Mecklenburg County" in the city permit files, which list places. It probably comes back blank and is filled with the median. Small.
- **Milwaukee building before** comes from year built (finished homes), not permits. Already noted in item 21.

## 4. ADU

The ADU "ask why" review (AQ-061) was thorough, and its fixes are in. I looked for more mistakes of the listed kinds and found none that move the numbers.
- **Checked:** reporting-share corrections, Massachusetts' 11-month year, Washington's compliance years, the value cap, the engine formula and the worked examples. All match the doc.
- **Minor:**
  - The Madison floor divides Madison's rate by 0.8 ("Madison's rules are about 80% of the benchmark"). That is a judgment factor of the kind Ryan rejected elsewhere. It rarely binds.
  - The with-law rate is in ADU units, the current-law rate in permits. For ADUs these are almost the same.
  - `scripts/run_pooled_revision.py` builds the reference points from the last loop variable (the LA-calibrated option). The seven non-California states do not depend on that option, so the result is right, but the code is fragile.

## 5. Parking

- **The control-city (placebo) fix is right.** Every real place now has at least 20 stand-ins. The high end, +1.4852 permits per 1,000 homes per year × 2,684,793 homes × 5 years = 19,937 permits, checks out.
- **Comparison places (finding 12).** Only full or near-full city repeals are kept out of the comparison and stand-in pools. Places with partial reforms (downtown only, near transit only) can still be comparisons. That would pull the effect toward zero. Suggest a check that drops every place on the reform map.
- **Denominator.** Homes from ACS 2020–2024 are used for every year from 2012. For early repeals this includes homes built after the repeal. The effect is probably small.
- **Weighting.** Five big cities carry 43% of the weight. The unweighted average is +0.42; the weighted one is −1.14. Already disclosed in the ask-why review.
- **Where the high end lands.** It is spread over all homes, including rural towns with no parking minimums. The "towns left out" case (13,866) already shows this.

## 6. Baseline, combined view, docs and tests

- The shared baseline (122,619 permits) matches its doc. Milwaukee uses a 2023–2024 average, others 2023–2025; this is disclosed.
- The Model & Assumptions document is in sync with each scenario's master copy (rerunning `scripts/sync_model_doc.py` changes nothing).
- **Stale numbers:** line 48 of `docs/MODEL_AND_ASSUMPTIONS.md` gives the parking median as −0.50; it is −0.12 (`reference/parking_expanded_effects.csv`). `docs/shared/DELIVERABLES_STATUS.md` still shows ADU 605 and 8,757.
- **Tests:** 672 pass. `pytest` also tries to run `test_permits` in `missing_middleware/tod/madison_test.py`, which is not a test; renaming it would stop that error. The project's own runner (`unittest`) is not affected.

## 7. Code hazards (no committed result was affected)

- `fit()` in `scripts/run_tod_lot_model.py` writes the lot table back to disk after it drops each city's largest project (`--drop-largest`). Running that stage would silently remove those lots for every later run. I checked: the largest lots are still in the current table.
- The withdrawn density move (item 26) checked only the moved homes against the receiving lot's size, not the homes already on it.
- The TOD lot-model scripts have no tests.

## What I checked and found correct

- The 5-year basis gives the right year counts in every city.
- Per-reform scoring code matches items 23, 24 and 27.
- New York building jobs are not double counted.
- The parking high-end arithmetic.
- The Model & Assumptions sync.
- The over-dense lots in Seattle and most in New York and Chicago are real buildings.

## Suggested order of work

1. Remove New York hotel rooms (Housing Database or hotel class), then rescore the New York cases and the lot model.
2. Merge Chicago's staged permits. Use one density measure (allowed homes per acre) for every city, in training and in Wisconsin (section 2c).
3. Score the lot model with and without the "rezoned later" trait (item 31).
4. Use real sites (assembled lots) in the lot model.
5. Fix the Saint Paul duplicate weight.
6. Recheck Madison against in-overlay neighbours.
7. Fix the two stale doc numbers.

The rebuild under item 31 will still carry findings 1, 2 and 4 to 9. I suggest not offering the lot model as an extra line until at least items 1 to 5 above are done.
