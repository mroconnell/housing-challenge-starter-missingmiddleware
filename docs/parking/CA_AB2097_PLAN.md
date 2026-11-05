# CA AB 2097: statewide effect on permits — plan (LOCKED 2026-11-05 16:48 UTC)

Written 2026-11-05 by the CA AB 2097 thread, before any new permit count. Status: **locked 2026-11-05 16:48 UTC (section 9)**.
Section 9 records the lock and any change after it.

**Post hoc relative to the Oct 27 test.** This plan is written after the earlier AB 2097 test found no measurable
change (section 2). It is a second look at the same law with the same permit data, not an independent vote. What is
new: the 2022 covered map, planned stops, local maps, year-by-year leads, a city-level dose check, and edges.
Section 8 (audit early review, 2026-11-05) overrides section 6 where they differ.

## 1. The question

Did AB 2097 (no parking minimums within ½ mile of a major transit stop, in force 1 January 2023) change how many
homes California permitted? Answer in:

- extra homes permitted per 1,000 existing homes a year (same unit as the parking tool);
- extra homes permitted per acre a year (TOD's unit);
- total extra homes permitted in covered land, 2023–2025 (a count).

Every result is a two-sided 90% range. No sign is assumed.

## 2. What we already know

| Earlier work | What it did | Result (90% range) | Unit |
| --- | --- | --- | --- |
| AB 2097 test (TOD, Oct 27; corrected Nov 3) | 185 cities; ½ mile vs ½–1½ mile ring; 2018–22 vs 2023–25 | −0.75 (−2.27 to +0.66), all homes | homes per 1,000 existing homes a year |
| Same, homes in 2+ unit buildings | | −0.65 (−2.01 to +0.71) | same |
| E1 (parking, Nov 3) | Same line, 2–4 home projects only | −0.023 (−0.070 to +0.018) | same |
| Distance bands (parking round 3) | ¼-mile bands to ¾ mile | no slope: +1.16 (−5.39 to +7.75) | same, per mile |
| LA map change (Nov 3) | Did LA's 2024 map widening give a test? | Not feasible | |
| Test 49 / method 2 (76 US repeal places) | Repeal effects nationally | Unclear; repeal places ran low before repeal too | |

Weak spots in the earlier AB 2097 test that a new study could fix:

- **Wrong map.** It used today's Caltrans stop layer. That uses the 20-minute bus rule from 2025 (AB 2553). The law in 2023 used 15 minutes. So some "covered" land was not covered.
- **Planned stops left out.** The law also covers stops planned in the regional transportation plan. The test put that land in the comparison ring.
- **Only two periods.** One before/after average. No year-by-year view of the lead-up.
- **No edge test.** Nothing compares land just inside vs just outside the line.

## 3. Options

| Option | What it does | New? | Cost | Main risk |
| --- | --- | --- | --- | --- |
| **A. Rebuild the 2022 map** | Build major transit stops from late-2022 transit schedules (GTFS), 15-minute rule, plus 2022 planned stops | Fixes the map | Medium | Old schedules may be hard to get or licensed badly |
| **B. Local published maps** | Compare A's map to city maps (LA, San Diego, San Jose, Oakland, Sacramento, others with public maps) | Checks A | Low–medium | City maps are dated 2024–2026 and mix later rules |
| **C. Year-by-year comparison** | Each year 2018–2025 vs 2022, near vs ring | Shows lead-up and ramp | Low once A exists | Few after years (3) |
| **D. Map edges** | Land just inside (⅓–½ mile) vs just outside (½–⅔ mile), same city | Closest-alike land | Low | Very low power; edge is soft (stops change) |
| **E. Take-up check** | Count LA's AB 2097 case filings by year and kind (290 rows on disk, 2023–2026) | Did anyone use it? | Low | One city; many filings are shops, not homes |
| **F. California vs other states** | Whole-state permits vs other states | Big picture | Low | One state, many laws at once; can't separate AB 2097 |

Not recommended: **F**. California passed SB 9, AB 2011, density-bonus and ADU changes in the same years, so a whole-state
comparison cannot isolate AB 2097.

## 4. Recommendation

Run **A + C as the main study**, with **B, D and E as checks**.

- **Main estimate:** year-by-year near-vs-ring comparison on the rebuilt 2022 map. The headline is the 2023–2025 average
  against 2018–2022, as before, so it lines up with the earlier test.
- **B** says how far our map is from city maps (share of land that agrees).
- **D** is reported beside the main result, never instead of it.
- **E** shows whether the law was used at all.

For scale only (a fact about the earlier test, not a forecast): its 90% range was about ±1.5 homes per 1,000 existing
homes a year, which across 1,276,507 near-transit homes is about ±1,900 homes a year.

## 5. Choices for Ryan

| # | Choice | My pick | Why |
| --- | --- | --- | --- |
| 1 | Which map is main | A (rebuilt 2022 map); today's layer as a check | Matches the law as written in 2023 |
| 2 | Count planned stops as covered | Yes; leaving them out as a check | The law covers them |
| 3 | Where old schedules come from | Free public archives first (Cal-ITP, agency sites, Wayback copies). Mobility Database or Transitland need an account and key: your call | I can't create accounts |
| 4 | Permit dating | Issue date main, report year beside it | Your 2026-11-03 rule |
| 5 | Run D (edges) at all | Yes, as a check | Cheap once A exists |

## 6. Plan details (to lock after section 5 is answered)

**Data**
- Permits: HCD Annual Progress Report Table A2, 2018–2025 (on disk), same cleaning as the corrected AB 2097 test:
  issue-date dating, cross-year re-report duplicates dropped, geocoded street addresses only, full reporters only.
- Homes and land: 2020 census blocks (on disk).
- Places dropped as "already no minimums": the same 12-place list as the earlier test, plus San Jose and Sacramento (left out of the main estimate; used as the placebo group, section 8 item 3).
- LA's 2017 transit-oriented upzoning areas left out of group P, as before.

**Map A (fixed before any permit is placed)**
- Schedules: each agency's GTFS feed in force on a weekday in October–December 2022. If missing, the nearest earlier
  2022 feed; if none, the agency is listed as missing and its stops come from today's layer (flagged).
- Rail stations and ferry terminals: always count.
- Bus: a stop counts if two or more routes meet there (stops within 150 m of each other), each running every 15 minutes or
  better in both the 7–9 a.m. and 4–6 p.m. weekday peaks.
- Planned stops: from each region's 2022-era transportation plan where published (SCAG 2020 layer on disk; others found
  in step 1).
- Covered land: within ½ mile (804.672 m, straight line) of a stop. Geometry with `missing_middleware.geom` only.

**Step 1 — feasibility, counts only (no permits by area).** Report: agencies found / missing, stops by type, covered
acres and homes, and agreement with today's layer and with the city maps (B). If schedules can be found only for agencies
covering under 80% of today's major stops, stop and report the coverage to Ryan. The 80% cut-off is a chosen rule,
not from evidence.

**Comparison**
- Near: covered land. Ring: ½–1½ miles, same city. Same groups as before (P = parking only).
- Outcome: homes in issued permits per 1,000 existing homes a year; per acre; all homes and 2+ unit buildings.
- Year-by-year: each year's near-minus-ring gap minus the 2022 gap, 2018–2025.
- Headline: 2023–2025 average vs 2018–2022 average.
- Lead-up check: 2018–2020 vs 2021–2022, same contrast. "Balanced" if its range includes 0; else flagged, not adjusted.
- Edges (D): ⅓–½ mile vs ½–⅔ mile, same city, same years.
- Total count: headline × covered existing homes ÷ 1,000 × 3 years, with its range from the same draws.

**Ranges:** 90%, 2,000 resamples of whole cities, fixed seed. Minimum detectable effect reported.

**Checks fixed now:** today's map; no planned stops; rail, BRT and ferry only; report-year dating; drop 2023;
drop the largest project in each cell; drop Los Angeles (this also tests the homes weighting, since LA is the largest weight).

**Known threats:** other 2023 laws (AB 2011, SB 9, density bonus) apply near and away from transit alike, but not fully;
late reporting lowers recent years (issue-date dating); high interest rates in 2022–2023; three after years only;
many projects permitted in 2023 were designed before the law.

## 7. Rules followed

- Model runs on the Mac. GIS layers and schedules stay out of git. No addresses committed.
- Downloads send `missing-middleware-research/1.0 (public data)`, no email. No records requests or emails.
- Each schedule feed's licence is recorded; feeds without open terms are listed and left out.
- No new Python dependency without Ryan's OK. No OpenStreetMap. No shapely/GEOS.
- No tool change from this study without Ryan's OK.

## 8. Changes after writing

**2026-11-05, before any count, from Ryan's opening message:** Ryan notes that, per Amy Lee's research, each
jurisdiction interpreted AB 2097's covered area differently. The source has not been read yet; step 1 finds and cites it.
Consequences for the draft:
- Option B can be more than a check. For a sample of cities with published local maps, the local map can be the
  covered area for that city, with map A beside it. Sample: chosen before any permits are placed, spread across regions
  and city sizes, listed with each map's date and source.
- Map dates matter. Where a city published or changed its map on a known date, that date is a second split for an
  edge test (land added or dropped by the map change), as Ryan suggested. The LA case (2024 widening) was not feasible
  on 2026-11-03; other cities are checked in step 1.
- Choice 1 in section 5 now has a third option: local maps main where they exist, map A elsewhere.

**2026-11-05, before any count, audit early review** (`audit/parking_ca_ab2097_plan_early_review_2026-11-05.md`,
reviewed from a summary). Each item is now part of the plan:

1. **Which permit data.** The near-vs-ring test needs geocoded project permits. Census BPS is city-level only. Source:
   HCD Table A2 (latitude, longitude and HCD standardized address). Step 1 recounts, by year 2018–2025, the
   jurisdictions with geocoded permits every year and their share of statewide permitted homes. The Oct 27 test kept
   360 of 531 filing jurisdictions and 1,005,786 of 1,214,141 permitted homes (82.8%), before the Nov 3 duplicate fix.
2. **Net vs moved.** A near-vs-ring gain can be homes moving from the ring, with no net gain. Added: a **city-level
   dose check**. For every California place in Census BPS: permits per 1,000 existing homes a year, 2023–2025 against
   2018–2022, regressed on the share of the place's 2020 homes inside the 2022 covered area. A real net effect shows as a
   slope; a move inside cities does not. 90% range from 2,000 resamples of places. The ring-vs-beyond check from the
   Oct 27 test is kept too.
3. **Places that already reformed** (the 12-place list, plus San Jose and Sacramento): left out of the main estimate
   under the strict rule, and used as a **placebo group** (placebo test: the reading rule needs its 90% range to include 0).
4. **ADUs.** State law already limited ADU parking near transit. Main outcome = homes in issued permits **excluding
   ADUs** (Table A2 unit categories other than ADU). ADUs are reported on their own. All homes and 2+ unit buildings are
   shown beside.
5. **Event study, locked now (Test 49 lesson).**
   - Leads: 2018, 2019, 2020 and 2021, each against 2022. Lags: 2023, 2024, 2025, each against 2022.
   - Placebo date: pretend the law began in 2020 (2018–2019 vs 2020–2022), same contrast.
   - Distance bands (D): 0–⅓, ⅓–½, ½–⅔ mile, each against the 1–1½ mile ring.
   - **Stated now:** if the leads trend (their slope's 90% range excludes 0) or the placebo date "finds" an effect,
     the headline is reported as **not evidence of cause**, whatever its sign.
   - **Main weighting:** pooled rates (homes-weighted), as in the Oct 27 test. Equal weight per city beside it.
6. **Which date.** AB 2097 applies to projects by application, which Table A2 does not record. Main: building-permit
   issue date (Ryan's 2026-11-03 rule). Check: entitlement approval date (`ENT_APPROVE_DT1`) where filled. 2023 is
   treated as a partial year; "drop 2023" is a fixed check.
7. **Other laws near transit, and how each is handled:**

   | Law or program | Overlaps the ½-mile area? | Handling |
   | --- | --- | --- |
   | AB 2011 (2023, commercial corridors) | Partly | Not flagged in Table A2; stated as a threat |
   | SB 9 (2022, lot splits/duplexes) | No, citywide | Ring absorbs; 1–4 home projects shown apart |
   | SB 35 streamlining (2018) | No, citywide | `APPROVE_SB35` projects dropped as a check |
   | State density bonus (parking relief near transit since 2016) | Yes | `DENSITY_BONUS_TOTAL` > 0 projects shown apart; E1's 2–4 home split repeated |
   | LA TOC (2017) | Yes, LA only | Left out of group P, as before |
   | LA ED 1 (Dec 2022, 100% affordable) | Partly, LA only | LA dropped as a check |
   | Builder's remedy (2022–2024, non-compliant cities) | No | Stated only |
   | Local reforms in the 12-place list | Yes | Item 3 |

   (AB 2011 is not flagged in Table A2, so its overlap cannot be removed; it is stated as a threat.)
8. **Licences.** Each GTFS feed's licence is recorded in the fetch log; feeds without open terms are listed and left out.
   No OpenStreetMap-derived layer.
9. **Geometry, no GEOS.** All geometry with `missing_middleware/geom.py`: Albers projection (EPSG:3310), KD-tree
   nearest-stop distances, `points_in_polygons` for city maps. No shapely, GEOS or matplotlib.path.
10. **Post hoc label.** Added at the top of this file.
11. **Ryan's calls.** Using LA's case-filings export (E, already on disk) and any records request are Ryan's call.
    F (California vs other states) is rejected because SB 9, AB 2011, density-bonus and ADU changes hit California in
    the same years, so a whole-state comparison cannot isolate AB 2097.

**2026-11-05, before any count, audit review of a9052ceb:**
1. Geometry uses `missing_middleware/geom.py` only (item 9 edited).
2. **Dose check lead placebo.** The 2018–2020 vs 2021–2022 change in each place's permits per 1,000 existing homes a
   year, regressed on the same covered share. If its 90% range excludes 0, the dose result is "not evidence of cause".
   Dose check details: homes-weighted (2020 homes) main, equal weight beside; the 14 already-reformed places are left
   out; the covered share comes from map A (2022 rebuild).
3. Section 6 now leaves San Jose and Sacramento out of the main estimate, matching section 8 item 3.
4. **Relative vs net.** The near-vs-ring estimate is labelled a **relative effect** (near transit compared with
   nearby land). It can include homes moved from the ring. The **net statewide answer comes from the dose check.**
5. **Anticipation check.** The law was signed in September 2022, so 2022 may already show it. Check: the same event
   study with 2018–2021 as the reference period.
6. The 80% stop-coverage cut-off is labelled a chosen rule; coverage goes to Ryan (section 6, step 1).
7. Main map: the audit leans to map A main, local maps as a check. Ryan's call (section 5, choice 1).
8. Amy Lee's source is read and cited before the city sample is chosen.
9. "Drop Los Angeles" check added; it also tests the homes weighting.

**2026-11-05, before any count, after reading Amy Lee's source** (Lee, Millard-Ball and Manville, "State Preemption
in Theory and Practice: The Case of Parking Requirements", *Urban Affairs Review* 62(4): 1165–1195, 2026, online
2025, DOI 10.1177/10780874251385240, CC BY 4.0; supplied by Ryan). What it says, in short:
- Six anonymous case cities, 25 interviews, summer 2024. Qualitative; no permit counts.
- Cities drew covered areas very differently (its Table 4): bus stops "meet" within 50 m (Caltrans) or 500 ft (SCAG),
  or by cross streets (SACOG); stations as a point or a whole parcel; distance from parcel edge or centroid; peak
  defined as best hour or average; planned stops counted, ignored, or counted only if funded.
- Cities used the law as a springboard (went further), a shield (followed it, deflected blame), or an obstacle
  (narrow reading, slow reviews).
- Developers mostly kept some parking (lenders, renters) and took the cautious reading to avoid delays.

Changes to this plan:
1. **Map A is the "law as written" map**, not each city's real map. Two bracket maps are added as fixed checks, built
   from Table 4's columns: **wide** (bus stops meet within 500 ft, any peak hour, planned stops in, distance from
   parcel edge approximated by +100 m) and **narrow** (within 50 m, average of peak hours, existing stops only,
   stations as points). If the main estimate's sign or size changes much between them, that is reported.
2. **City sample for local maps (option B):** drawn from the paper's 15-city sampling frame (its Table 1: Beverly
   Hills, Fresno, Irvine, Los Angeles, Merced, Oakland, Palo Alto, Rancho Cordova, Roseville, Sacramento, San Jose,
   San Clemente, Santa Cruz, South Lake Tahoe, Truckee), keeping those with a public AB 2097 map. Chosen before any
   permit is placed. Sacramento and San Jose stay in the placebo group.
3. **Springboard places.** Culver City, Mountain View, Sacramento and San Jose (named in the paper as going beyond the
   ½ mile) are already on the dropped or placebo list, except Mountain View (2024, precise-plan areas only), which is
   now added to the placebo group.
4. *(Withdrawn 2026-11-05 15:39 UTC at Ryan's request: no forecast of the result. See the last block.)*

**2026-11-05, before any count, audit review of bb5ac099:**
1. **Mountain View** is dropped from both the main estimate and the placebo group. Its own 2024 reform means its
   2024–2025 years are not "no change expected", and keeping 2023 alone would leave one thin after year. This replaces
   item 3 of the block above.
2. **Bracket maps, no cut-off.** The main, wide and narrow results are reported side by side, and the write-up says
   plainly whether the sign differs. No "changes much" threshold. This replaces the last sentence of item 1 above.
3. **Labels.** "+100 m for distance from the parcel edge" is a chosen stand-in, not from evidence. Map A's 150 m
   bus-meeting rule is about SCAG's 500 ft (152 m), so on that point the wide map equals map A; the wide map differs
   only in peak hour, planned stops and parcel edge.
4. **What each result would mean (stated now):**
   - **Null** (90% range includes 0): fits the paper's uneven take-up; says no average effect large enough to see.
   - **Clear positive or clear negative** (90% range above 0, or below 0): read the same way for both signs. It counts
     as evidence that the law changed permits near transit, in that direction, only if all of these hold: the leads
     are balanced; the placebo group is near 0 (its 90% range includes 0); there is no placebo-date effect. A net
     statewide claim, either sign, is made only if the dose check agrees in sign with its own range excluding 0.
     The same confounds are listed beside either sign: other laws near transit (item 7 table), interest rates and
     costs, Los Angeles programs, late reporting, and homes moving between near and ring land.
   - Any result with trending leads or a placebo-date "effect": not evidence of cause (item 5 of the first audit block).

**2026-11-05 15:37 UTC, Ryan's answers to the 5 choices (section 5), before any count:**
Ryan's message, word for word:

> So #1 is our "theoretical map" -- that sounds good
> #2 yes, in our theoretical map. There should be a trait for each row (whether that's by lot or stop) that says when the stop launched and unlaunched stops can have a future date
> #3 yes, unless TOD has a better answer for this like a national agency database
> #4 HCD APR Data, issue date
> #5 yes, but run this on both our "theoretical map" (which you called main map) and a few actual maps we find for cities

The plan's reading of it:
1. **Main map = the "theoretical map"** (map A, the law as written in 2022). City maps and the wide and narrow maps
   are checks.
2. **Planned stops are in the theoretical map.** Every stop row carries a **launch date**: the date service began
   (existing stops), or the planned opening year from the regional plan (planned stops; may be in the future).
   Uses, fixed now:
   - Main: all stops with a launch date up to the plan horizon count as covered from 1 January 2023, as the law says.
   - Check: existing stops only (launch date on or before 31 December 2022).
   - Check: land whose nearest stop launched during 2018–2025 shown apart, since a new station can raise permits by
     itself.
   - Launch dates come from the agency or regional plan; where none is found the row is marked "date unknown" and
     counted in the main map.
3. **Old schedules:** free public archives first, unless TOD names a better source (for example a national agency
   database). Waiting on TOD's answer, relayed by the coordinator. **The plan is not locked until then.**
4. **Permits:** HCD Annual Progress Report Table A2, dated by building-permit issue date. Report-year dating stays
   beside it as a fixed check.
5. **Edge check:** run on the theoretical map **and** on a few actual city maps (from the local-map sample in the
   first block of this section). Reported beside the main result, never in place of it.

**2026-11-05 15:38 UTC, Ryan: add a rail-only edge check (draft, plan not locked):**
- Why: rail stations are the least disputed part of the law (the paper calls an existing rail station "the most
  unambiguous" case), so the ½-mile line around them is the most predictable edge.
- Stops: existing rail stations (heavy, light, commuter rail, and Amtrak stations; launch date on or before 31 December
  2022). Station = the stop point in the schedule data; "station as a whole parcel" is not built.
- Edge: ⅓–½ mile vs ½–⅔ mile from the nearest rail station, same city. Land within ½ mile of any bus, BRT, ferry or
  planned stop is left out of both sides, so "outside" is land no reading of the law covers.
- Same outcome, years, dating, groups and ranges as the main edge check. Reported beside it.
- Counts of permits on each side are reported first.

**2026-11-05, audit pre-check of ff6c84aa (draft, plan not locked):**
1. Ryan's 15:37 message is quoted word for word above the numbered reading.
2. **"Up to the plan horizon"** means a planned stop counts if it is in the region's transportation plan in force on
   1 January 2023, at any opening year up to that plan's horizon. Expected plans, confirmed in step 1: SCAG Connect
   SoCal 2020 (to 2045; layer on disk), MTC/ABAG Plan Bay Area 2050 (to 2050), SANDAG 2021 Regional Plan (to 2050),
   SACOG 2020 MTP/SCS (to 2040), and each other MPO's plan in force on that date. Step 1 lists every plan, its
   adoption date and horizon year, and reports the number and share of stop rows marked "date unknown".
3. **Lead test with and without new stations.** Land near stops that opened in 2018–2022 can change before 2023
   because of the station itself, which could make the leads trend for reasons unrelated to AB 2097. The lead test
   (and the dose check's lead placebo) runs with and without that land. If the leads trend only with that land in,
   the write-up says so and reads the main result from the version without it.

**2026-11-05 15:38 UTC, Ryan on rail (draft, plan not locked):** "bus lines can change and we have to look them all
up, but rail, light rail, street car, etc are all more static and predictable"
- The rail-only edge check counts heavy rail, light rail, streetcar, commuter rail and Amtrak stations. Streetcar is
  included as rail. The law says "rail ... station" without defining it; no source read so far says streetcars are in
  or out, so a check without streetcars is run only to show whether they matter.
- Rail stations need no timetables (the law counts any existing rail station), so the rail-only checks do not depend
  on the old bus schedules (choice 3). Station locations and opening dates can come from the stop data already on disk
  plus agency opening dates.

**2026-11-05 15:39 UTC, Ryan: no prejudging.** Ryan asked what the caveats were based on and why the plan prejudged
the data. Forecasts of the result were removed: the "most likely outcome" line (section 4), the paper-based
expectation (item 4 of the paper block), and "expect few permits near the line" (rail edge). They were guesses from
earlier California and edge tests, not from this study's data. The streetcar note now says only that the law does
not define "rail station". The reading rules (what a null, positive or negative result would mean) stay, because
they are rules fixed before counting, not forecasts.

**2026-11-05, TOD's answers (relayed by the coordinator):**
- **Schedules:** no federal source keeps old timetables. The BTS National Transit Map serves only its current
  compile and has no timetables; the National Transit Database has none. Leads to test in step 1 (none federal):
  Cal-ITP (Caltrans) GTFS archive (said to start about 2021; access and licence to check), Mobility Database dated
  versions, Transitland archive (account and key; Ryan's call). Ryan's choice 3 therefore means free public archives
  first.
- **Planned stops:** only stops in transportation plans in force in 2022 (not today's plans). If a region's plan
  cannot be mapped, its planned stops are left out and listed.
- **Permit cleaning:** reuse `missing_middleware/tod/ab2097.clean_permits` (issue date, report year only if blank,
  cross-year de-duplication keeping the earliest report). The report-year check uses the same de-duplication.
- **Edges, fixed now:** a 25 m donut on each side of the line (as TOD used); a bunching check of permits by distance
  in 50 m steps across the line; non-geocoded Table A2 rows dropped (`ab2097.is_geocoded`).

**2026-11-05, audit check of 7589b145 (rail-only edge), draft, plan not locked:**
1. Ryan's messages, word for word:
   - 15:38:27 UTC: "Can we also perhaps run an edge map on more predictable rail stops?"
   - 15:38:52 UTC: "bus lines can change and we have to look them all up, but rail, light rail, street car, etc are all more static and predictable"
   - 15:39:36 UTC (edited 15:40:00): "Caveat re permits near line: 1) what is that caveat based on? 2) why are you prejudging the data and biasing me :D"
2. **Station list:** heavy rail, light rail, **streetcar**, commuter rail and Amtrak stations.
3. **Amtrak-only stations** (no other rail service) stay in, since the law counts any rail station. Check: without them.
4. **New stations:** the rail-only edge runs with and without stations opened in 2018–2022, the same rule as the main
   lead test.
5. **Who is left:** leaving out land near any bus, BRT, ferry or planned stop drops much of the dense urban land, so
   the remaining stations may lean suburban. Step 1 reports the stations and land kept (by county and by 2020 homes
   per acre) so the reader can see which places this check speaks for.
6. **Station source:** rail stations need no schedules. Step 1 tests a static public station list with opening dates
   (for example the BTS NTAD rail stations layer), records its licence, and uses it for this check if it covers the
   California rail systems. Agency opening dates fill gaps.

**2026-11-05 15:45 UTC, Ryan: "check github too because I think people have made maps for AB 2097 and SB 79 that
might speak to this - check the licensing on those gh projects and their data sets"** (draft, plan not locked).
GitHub search of repositories and code ("AB 2097", "AB2097", "SB 79", "SB79", "21064.3", "major_transit_stop",
"high quality transit"), checked 2026-11-05:

| Project | What it has | Licence | Use here |
| --- | --- | --- | --- |
| SACOG/major-transit-stops | Scripts that flag *planned* (model-year) major stops for AB 2097 and SB 79 from SACOG's travel-model network; README says to use GTFS for existing stops. No data files beyond a small extra-stops CSV | MIT | Method reference for Sacramento-region planned stops; the model network itself is not in the repo |
| cal-itp/data-analyses (`high_quality_transit_areas`) | The code behind Caltrans' monthly HQTA / major-stop layers. Documents the method: AM peak 6:00–8:59, PM 3:00–6:59, stops within 500 ft of two corridors' crossing, 50 m stop-to-corridor join. Since 2024 uses the 20-minute rule for bus major stops | **AGPL-3.0** (GPL family) | **Code not used or copied.** Its published method is cited as one reading of the law. Its data outputs are Caltrans public layers (already used); dated past outputs are not in the repo |
| cal-itp/data-infra | The pipeline that archives California GTFS feeds | AGPL-3.0 | Code not used. Whether its archived feeds (about 2021 on) are publicly downloadable is a step-1 lead |
| Vikram-T/sb79-analysis | SB 79 parcel tiers, Berkeley only, today's stops | Apache-2.0 | Not useful (one city, current stops) |
| ajbeattie/sb79-sf | SB 79 capacity, San Francisco only | MIT | Not useful (SF is dropped as already reformed) |
| sdamerdji/sb79 and other SB 79 class projects | SB 79 parcel maps | No licence stated | Not used (no licence means no right to reuse) |
| consbio CEQA site-check repos | Statewide CEQA exemption scripts using major stops (ArcGIS arcpy) | No licence stated | Not used |

No GitHub project found holds a dated 2022 statewide major-stop map or 2022 timetables. Step 1 therefore also
checks: (a) the Cal-ITP archive's public access and licence; (b) dated copies of the Caltrans HQTA layers (for example
in web archives) from before the 2024 rule change, which would give a 15-minute statewide map built by Caltrans.
The Cal-ITP method choices (peak hours, 500 ft, 50 m) are listed beside ours in the map write-up.

**2026-11-05, audit notes on the GitHub check (82a1b72b), draft, plan not locked:**
1. The Cal-ITP (AGPL) README is read and cited for its method only. Our map code is written from the law text, not
   ported from Cal-ITP code.
2. The Caltrans HQTA layers' licence or terms are recorded in the fetch log, as for the GTFS feeds.
3. A dated pre-2024 Caltrans HQTA layer, if found, is **Caltrans' reading** of the law. It is a check beside the wide
   and narrow maps, not map A.
4. **Peak hours differ:** map A uses 7:00–9:00 a.m. and 4:00–6:00 p.m. on weekdays; Cal-ITP uses 6:00–8:59 a.m. and
   3:00–6:59 p.m. Both are listed in the map write-up.
5. GTFS feeds from any archive keep their own agency licences; an archive's terms do not replace them. Each feed's
   agency licence is recorded.

**2026-11-05 16:03 UTC, Ryan: "San Francisco and Emeryville may be interesting too"** (draft, plan not locked).
- Both had no parking minimums citywide before AB 2097 (San Francisco effective 2019-01-21, Ord. 311-18; Emeryville effective 2020-05-21, Ord. 20-005; dates as coded by the parking thread), so the
  law changed nothing at their ½-mile line. They are added to the city sample as **placebo cities**: the main
  comparison and the edge test are run at the theoretical map's line in each, and the reading rule needs each range to
  include 0.
- They have no reason to publish an AB 2097 map; the theoretical map's line is used. If one exists it is recorded.
- Emeryville did not file geocoded permits every year 2018–2025 in the earlier test. Step 1 counts its years with
  permits; if it is short, it is shown with that caveat or listed as too thin, not replaced.

**2026-11-05 16:06 UTC, Ryan: support and opposition lists from the AB 2097 (Friedman) committee analysis**
(pasted by Ryan; the exact analysis title and date are found and cited in step 1). Draft, plan not locked.

Coding, fixed now from the lists as given:
- **Opposed (city as a body):** Beverly Hills, Rancho Palos Verdes, San Marcos, Santa Clarita, Torrance.
  Group letters (California Contract Cities Association, Marin County Council of Mayors and Council Members) are not
  coded to single cities, since the lists do not say which members signed.
- **Supported by a local official (not the city as a body):** San Mateo, Menlo Park, Culver City, Petaluma, Santa
  Monica, Emeryville, West Hollywood, Seaside, Berkeley, Gilroy, La Mesa, Sunnyvale, Mountain View. One official's
  support is a weaker signal than a city's letter; this is stated beside every result.
- Already dropped or placebo, so not in this split: Culver City, Emeryville, Berkeley (earlier reform list) and
  Mountain View (dropped).
- **Neither:** all other kept cities.

Uses:
1. **City-map sample:** the five opposing cities are added to the local-map sample (Beverly Hills is already in it).
   Same rules: listed before counting, map date and source recorded, no replacements.
2. **Stance split (described only):** the main near-vs-nearby comparison shown separately for opposed, supported-by-
   an-official, and neither. Each group's number of cities and permits is shown first. It follows the paper's idea that
   local stance shaped how the law was applied. It is one more split among several, so a single group differing is
   not read as a finding on its own.

**2026-11-05 16:07 UTC, Ryan: "these are just leads that we can check to see if the city did anything that we can use - don't get bogged down by a lead if it's not turning up a real map"** (draft, plan not locked).
- **Time box per city lead:** check the city's planning web page, its open-data or ArcGIS site, and one web search
  for "AB 2097 map" with the city's name. If no map turns up, record "no map found" with what was checked, and move on.
  No records requests, no emails.
- Cities with no map found stay out of the local-map check; they are not replaced.

**2026-11-05, audit notes on aeb2dfe3, bc13311a and 46d4bc86 (draft, plan not locked):**
1. Emeryville's own citywide repeal (effective 2020-05-21) falls inside the lead years. Both its near and ring land
   are covered by it, so it should cancel out in near vs ring; this is stated beside Emeryville's lead results.
2. The five opposed cities are a **second source** for the city-map sample (the committee analysis), separate from the
   paper's 15-city frame, and are labelled so. Where one has no public map: "no map found", no replacement.
3. Each stance group shows covered homes (2020) and covered acres beside its city and permit counts.

**2026-11-05 16:16 UTC, Ryan: "well a bit deeper than that :D"** (on the time box). Replaces the three-step time
box above. For each city lead, check all of these, then stop:
1. The city's planning or AB 2097 web page, and its zoning code for an AB 2097 section.
2. The city's map viewers and open-data / ArcGIS sites, including the list of map layers (REST service directory)
   for any AB 2097, "reduced parking", "major transit stop" or "transit priority area" layer.
3. City council and planning commission agendas and staff reports from 2022 to 2025 mentioning AB 2097 (maps are
   often attached as figures).
4. Which regional map the city says it relies on (SCAG, SANDAG, SACOG or MTC), and whether that map is public.
5. Web-archive copies of the pages in 1–2, for dated older versions.
6. Two web searches: the city's name with "AB 2097 map", and with "parking" "major transit stop".
Results are recorded per city as one of: GIS layer found (usable), PDF map only (recorded, digitized only if the city
is in the sample and the map is legible), relies on a regional map (named), or no map found (with what was checked).
No records requests, no emails, no logins.

**2026-11-05 16:16 UTC, Ryan: "probably want to see if they had a public hearing about ab 2097"** (draft, not locked).
Check 3 above also records, per city: whether the council or planning commission held a public hearing or agenda item
on AB 2097 (2022–2025); its date and body; and what came of it (code amendment adopted, map adopted, "findings"
escape hatch used, information only, or none found). A dated adoption of a map or code change is a candidate date for
the map-date edge test (section 8, Ryan's opening note). Hearings are read from public agendas, minutes and videos'
written summaries only.

**2026-11-05, after the city-lead search (docs/parking/CA_AB2097_CITY_LEADS.md) and the audit's review of it
(draft, plan not locked):**
1. **The local-map check rests on very few cities.** Of 21 cities searched, the only dated 2023 city layer for a city
   kept in the main estimate is Oakland's (Spring 2023, 15-minute rule). Sacramento's layer (created 2023-02-03) is in
   the placebo group. Los Angeles's layers are from 2024 and 2026. This is stated beside every local-map result.
2. **Candidates for the map-date and rail edge ideas** (counts expected to be small; counts reported first):
   Palo Alto (radius map adopted by council 2024-11-12, 7-0, around 3 Caltrain stations; PDF map) and Truckee
   (½-mile layer around one rail depot, last edited 2024-01-09).
3. **Licences: Ryan's call.** No city layer found states a licence; SCAG's layer says "for general planning and
   informational purposes only". Using layers with no stated licence as inputs kept out of git (never committed or
   redistributed) needs Ryan's OK. Until then they are not downloaded. The third-party "AB 2097 Eligibility Areas"
   layer (modified 2023-12-15, an individual's account) falls under the no-licence, no-reuse rule unless Ryan says
   otherwise.

**2026-11-05 16:42 UTC, Ryan on the licence question: "for this research phase, let's say yes"** (draft, not locked).
- City and regional AB 2097 layers with no stated licence (and SCAG's "general planning and informational purposes"
  layer) may be used as research inputs in this phase: kept out of git, never redistributed, cited by URL and access
  date, with any terms text recorded in the fetch log.
- "This research phase" only: any use in the tool, or any published derived layer, needs Ryan's OK again.
- The third-party individual's "AB 2097 Eligibility Areas" layer (2023-12-15) stays out; Ryan's answer covered the
  city and regional layers asked about.
- Downloads still wait for the lock and the audit's check of the step-1 script.

**2026-11-05 16:43 UTC, Ryan: "and you can convert those PDFs to maps too right?"** (draft, not locked).
Yes, for the two PDF-only cities, by rebuilding rather than tracing:
- Both PDFs show ½-mile circles around named stops (Palo Alto: 3 Caltrain stations; Santa Cruz: individual stops,
  including on the UCSC campus). Each circle's centre is matched to a stop in public stop data (or the station
  location), and the circle is redrawn at ½ mile with `missing_middleware/geom.py`.
- Check: the rebuilt map is laid over the PDF page by eye (pages viewed as images, no new software), and every
  circle is listed as matched, unsure, or not matched. Unsure or unmatched circles are reported, not guessed.
- No new dependency. PDF tools under GPL-family or AGPL licences (for example PyMuPDF, poppler) are not used.
- Labelled "rebuilt from a PDF" wherever used; the city's exact edge may differ by tens of metres.

**2026-11-05 16:43 UTC, Ryan: "I'd say the Palo Alto finding is perfect"** (draft, not locked).
- Palo Alto becomes a **named case** for the rail edge test: the city's own ½-mile circles around 3 Caltrain stations
  (Downtown, California Ave, San Antonio), shown by June 2023; staff found no 15-minute bus intersection.
- The line is taken to start on 1 January 2023 (the law), since the June 2023 map already showed the circles. Step 1
  compares the 2023 map with the 2024 council map (Attachment B); if they differ, the 2024-11-12 vote date is added as
  a second split for the land that changed.
- The 2024-11-12 vote counts come from news summaries; they are leads until confirmed in official minutes.
- Permit and land counts on each side of Palo Alto's line are reported before any estimate.

## 9. Lock

**Locked 2026-11-05 16:48 UTC by Ryan.** Asked "Is that a go to lock the plan?", Ryan answered in this thread at
16:48:30 UTC: "it is". The plan is this file as of this commit: sections 1–7 as amended by every dated block in
section 8 (later blocks replace earlier ones where they say so). No permit has been read or placed by area for this
study. Any later change goes below with a date and a reason, labelled pre- or post-count.

### Changes after lock

- 2026-11-05 19:02–19:04 UTC, post-lock, pre-count, Ryan: "the hcd apr data should have a specific street address /
  APN", then "yeah" to re-geocoding. Non-street rows with a house-numbered street address are re-geocoded with the
  U.S. Census Bureau geocoder (`scripts/ca_ab2097_regeocode.py`; public domain, no account; addresses kept out of git).
  Accepted matches (Match, Exact or Non_Exact) join the main permit set; the match rate by year and jurisdiction and
  the HCD-vs-Census distance on a comparison sample are reported in step 1, before any count. The street-level-only
  set (no re-geocoding) becomes a check. Runs after the audit clears the script. The headline question (city-level
  check) is still open with Ryan.
- 2026-11-05, post-lock, pre-count (no permit placed by area), geocode fall-off, after the audit's notes:
  - **Dropped rows sit on repeated city or county points:** in every report year, 80%–98% of rows without a
    street-level point share a point with 10 or more other rows (2025: 97.6%); unique points are 0.4%–4.2%. Their
    location says nothing about distance to a stop, so dropping them is right; no "distinct points" check is possible.
  - **Stable-geocode check, cut fixed now:** jurisdictions whose share of rows without a street-level point changed by
    5 percentage points or less (a chosen fixed number, not from evidence) between report years 2018–2022 and
    2023–2025. The kept set likely leans away from fast-growing outer places, so this check answers a narrower
    question. The list is committed before any count:
    `reference/ca_ab2097_geocode_stability.csv` (532 jurisdictions; 324 kept). The main estimate and the checks are
    re-run on the kept jurisdictions.
  - **Caveat carried by every point-based result:** the drops rise only after 2022 and cluster in fast-growing outer
    places and in houses (2024–2025: townhouses 43%, houses 32%, 5+ unit rows 21%, ADUs 3%).
  - **Weight in the write-up (proposed; needs Ryan's OK, since it changes the headline after the lock):** the city-level dose check uses Census BPS city totals, not points, so it is not
    touched by this; the write-up leads with it for the statewide "extra homes" answer, with the point-based near/ring
    results beside it.
  - How Ryan wants this handled is still open; this entry fixes the checks so the choice cannot follow the counts.
- 2026-11-05, post-lock, pre-count, after the step 1 field checks (`reference/ca_ab2097_step1_field_checks.csv`) and
  the audit's notes:
  - **Density-bonus field** is zero-filled (non-blank in 100% of rows), so "no bonus" and "not reported" look the
    same. Among "5+" rows with permits, the share with a bonus above 0 by report year: 2018 0.9%, 2019 0.6%,
    2020 2.1%, 2021 4.5%, 2022 11.2%, 2023 8.8%, 2024 9.7%, 2025 17.2%. A jump between years may come from reporting,
    not real use. Outcomes A and B are therefore **descriptive only**, shown with this table.
  - **Financing field** is filled in 0.9%–2.5% of rows with permits. Outcomes C and D are **descriptive only**; the
    HUD check shows whether the flag tracks real LIHTC.
  - **Street-level geocodes fall off in recent report years, for all rows.** Rows with permits dropped for lacking a
    street-level point: 2018 4.3%, 2019 2.8%, 2020 2.4%, 2021 2.5%, 2022 4.8%, 2023 8.7%, 2024 17.4%, 2025 20.7%. This
    straddles the before/after line and affects the main outcome. Before any count, step 1 reports the same rates by
    jurisdiction and unit category, and the question of how to handle it goes to Ryan (no fix chosen yet).
- 2026-11-05 18:17 UTC, post-lock, **pre-count** (no permit placed by area yet), Ryan confirmed the reading above:
  "yes, and you can use more specific bus details like archive.org results to sanity check the caltrans data (or
  other similar side checks)". **Change to the main map (labelled post-lock, pre-count):**
  - Rail, ferry and Amtrak: the dated end-2022 map (step 1b part 1) — main.
  - Bus: today's Caltrans major-stop layer (existing bus major stops) — main bus map, labelled "later map, 20-minute
    rule (post-2024)"; it covers more land than the 2023 15-minute rule did.
  - Dated 2022 bus schedules (web archive: Muni, San Diego MTS and others; OpenMobilityData if found), the National
    Transit Database service check and MTC's 2017 layers (an earlier map; data licence checked first): side checks
    of the bus map, reported in step 1.
  - Every result is also shown on the rail-only map.
  - The section-6 / gap-rule wording that made dated schedules the main bus source is replaced by this entry.
  - Write-up note (audit): today's bus layer marks land as covered where service was added after 2023 and leaves out
    land where service was cut since then. Both blur the line between near and ring; the dated side checks show by
    how much.
- 2026-11-05 18:14–18:15 UTC, post-lock, pre-count, Ryan, verbatim: 18:14:00 "use current caltrans data like the
  challenge literature suggests"; 18:14:19 "sure on MTC" (to adding MTC's 2017 layers as a Bay Area check);
  18:15:15 "yeah, I think just getting hard data on rail stops will already be huge". Reading sent to Ryan for
  confirmation (not yet applied): rail/ferry/Amtrak dated end-2022 map stays main; today's Caltrans bus major stops
  become the main bus map (labelled as a later map using the post-2024 20-minute rule, which covers more land than the
  2023 rule); dated-schedule bus maps become a check; every result also shown rail-only. MTC 2017 layers: an earlier
  map (before 2023), used as a check after their data licence is checked (code is Apache-2.0).
- **Rule for California providers in the OpenMobilityData listing, fixed before reading it:** a provider counts as
  California if its name or feed id matches a California GTFS feed in the Mobility Database catalog (feeds_v2.csv,
  `location.subdivision_name` = California) by provider name (case-insensitive, ignoring punctuation) or by the
  legacy TransitFeeds id the catalog records; plus this hand list of slugs, written now: ac-transit, la-metro,
  sfmta, octa, sacrt, vta, long-beach-transit, foothill-transit, big-blue-bus, san-diego-mts.
- 2026-11-05 18:13 UTC, post-lock, pre-count, Ryan: "yeah, do both" (to: check the OpenMobilityData archive for
  2022 schedules, and add a National Transit Database check for gap agencies).
  - **OpenMobilityData archive** (former TransitFeeds, stored publicly by the Mobility Database): a metadata-only
    listing (`scripts/ca_ab2097_step1a_omd_archive.py`) first, cleared by the audit. Qualifying copies follow the
    calendar rule above (service covers 2022-12-14). The bucket's terms are logged; each feed keeps its agency licence.
  - **Service check for gap agencies** (National Transit Database, a challenge-suggested source, public domain):
    for each gap agency, annual bus vehicle revenue hours (bus, rapid bus and commuter bus modes) in report year
    2022 and in the latest year, and their ratio. Shown beside the gap agencies' share of today's bus major stops.
    It is described only: it tells the reader how much an agency's service changed since 2022, not which stops did.
- 2026-11-05, post-lock, pre-count, after the web-archive check (21 of 293 California feeds with a Sep–Dec 2022
  copy) and the audit's request for a rule for feeds without one. **Rule for each bus feed, fixed now, whatever
  archive is used:**
  1. A saved copy counts as the late-2022 schedule only if its service calendar (`calendar.txt` /
     `calendar_dates.txt`) covers Wednesday 2022-12-14 (a normal weekday in the target window). The copy's capture date
     alone does not count. Among qualifying copies, the one whose calendar start is latest on or before 2022-12-14 is used.
  2. No qualifying copy: the agency is listed as a gap, and its bus major stops come from today's Caltrans layer,
     flagged "later map" (section 6's existing fallback). Every result is also shown without those stops.
  3. The share of today's Caltrans bus major stops that fall in gap agencies is reported in step 1, before any
     estimate.
  4. Today's Caltrans layer uses the 20-minute bus rule adopted after 2024 (AB 2553), so gap stops will tend to
     cover more land than the 2023 15-minute rule did. The results without gap stops are the check on that.
- 2026-11-05 17:20 UTC, post-lock, pre-count, Ryan: "I dropped some LIHTC data in raw data in local (parking reform
  thread is using it too)". The file is HUD's national LIHTC database (`data/raw/hud_lihtc/lihtcpub.zip`, release
  2026-04-30, hand-downloaded by Ryan; provenance in that folder). HUD lists a project only once placed in service,
  so recent allocation years are incomplete (parking thread: 2021 at 79% and 2022 at 49% of a normal year). It
  therefore cannot measure 2023–2025 and is used **only as a check of the Table A2 LIHTC flag**:
  - For California projects HUD lists with allocation years 2018–2020, the share that match a Table A2 project
    flagged LIHTC (same jurisdiction, within 150 m, permit year within 3 years of allocation), and the share of
    A2-flagged 2018–2020 projects that match a HUD project. Reported in step 1, before any estimate.
  - Matching reuses the parking thread's place assignment (`scripts/assign_parking_lihtc_places.py`, 3a26cd2b) where it
    fits; the file is read only, never committed.
  - Table A2 points are HCD's own geocode (street-level only, `ab2097.is_geocoded`); no new geocoding. Step 1
    also reports, by permit year, how many A2 LIHTC-flagged projects are dropped for lacking a street-level point.
- 2026-11-05, post-lock, pre-count, audit notes:
  - `FIN_ASSIST_NAME` and `DENSITY_BONUS_TOTAL` are confirmed as column names in the Table A2 file on disk
    (`data/raw/hcd_apr_a2/tablea2.csv`).
  - The LIHTC 20+20 sample review happens before any estimate; any change to the match list after it is logged here
    with its time and reason.
  - **Reading rule for the five secondary outcomes** (density bonus A and B, LIHTC C and D, deed-restricted homes):
    on their own they are not evidence of cause, whichever sign they show. They are read only beside the main
    result and under the same leads, placebo-group and placebo-date checks.
  - Step 1b part 1: an openings row dates only stops of its group within 150 m of the row's point (not a whole
    chained station); each dated set's stop count and span are printed. The run stops if 0 Amtrak stations return.
- 2026-11-05, post-lock, **pre-count** (no permits read), after the first try of step 1b part 1 (stopped on a code
  error before any output) and the audit's note on Muni surface stops:
  - **Which rail stops count as a "rail station":** main = every stop the National Transit Map codes as light rail,
    streetcar, subway or rail, including street-level light-rail stops. This matches Caltrans' own reading: its major
    transit stop layer lists 763 existing rail major stops for the City and County of San Francisco (2,428 statewide),
    which includes Muni surface stops. Check: without rail stops also coded as bus stops (street level).
  - **Distances are measured to stop points**, not merged station centres, so a chain of close stops cannot move the
    ½-mile line. Stations (stops of a mode within 150 m) are used only for counts, dates and flags.
  - **Dates join within a group:** subway-running light rail is coded as either light rail or subway, so the two
    urban rail modes join as one group; commuter rail, intercity rail and ferry join only to themselves. Openings
    rows with no stop of their group within 300 m are listed for the step 1 review.
- 2026-11-05 17:05 UTC, post-lock, **pre-count**, Ryan: "okay, let's go with web archive for now. Can we add a
  lihtc test the same way we added a density bonus test?"
  - **Bus schedules (choice 3):** web-archive copies of each agency's schedule file; the Mobility Database is the
    backup for gaps only if Ryan later agrees to its account.
  - **LIHTC test, a secondary outcome** read by the same rules as the main result (same groups, years, dating,
    resampling, leads and placebo checks; a rise, a fall or no change all reported as found):
    - Source, main: HCD Table A2 itself. A project is "LIHTC" when its financing-assistance field
      (`FIN_ASSIST_NAME`) names low-income housing tax credits (text match, case-insensitive: "tax credit",
      "LIHTC", "TCAC", "CTCAC", "CDLAC"). The match list is fixed now; step 1 reports fill rates by report year
      and 20 random matched and 20 random unmatched non-blank values, before any estimate.
    - Outcome C: share of permitted projects with 5 or more homes that are LIHTC (among those with the field
      filled), near vs ring, 2023–2025 vs 2018–2022.
    - Outcome D: homes in LIHTC projects per 1,000 existing homes a year, same contrast.
    - 9% and 4% credit deals are shown apart only if a source separates them (Table A2 does not); then from the
      California Tax Credit Allocation Committee award lists, after their licence or terms are checked.
    - Also reported, same contrast: deed-restricted affordable homes (Table A2 building-permit columns ending in
      `_DR`) per 1,000 existing homes a year.
    - HUD's national LIHTC file is not used for the after years: the parking thread found it complete only to about
      2019 allocations.
- 2026-11-05 16:56 UTC, post-lock, **pre-count**, Ryan: "sure, add it" (to adding a density-bonus test from
  Manville and Smith's 2022 letter, "AB 2097 Will Not Undermine the State Density Bonus or the Los Angeles Transit
  Oriented Communities Program", UCLA/USC, 2022-08-29, supplied by Ryan). Added as a **secondary outcome**, read by
  the same rules as the main result (same groups, years, dating, resampling, leads and placebo checks):
  - `DENSITY_BONUS_TOTAL` is read as HCD's field for the number of extra homes granted by the density bonus
    (bonus homes only). A project "used the density bonus" when it is above 0.
  - Outcome A: among permitted projects with 5 or more homes **whose density-bonus field is filled**, the share
    that used the density bonus; near transit vs the ring, 2023–2025 vs 2018–2022. Check: blank counted as 0.
  - Outcome B (homes in density-bonus projects, not bonus homes): all permitted homes in projects that used the density bonus, per 1,000 existing homes a year, same
    contrast. Check: bonus homes only (the field's own count).
  - Before any estimate, step 1 reports how often the density-bonus fields are filled, by report year, since the
    form changed over the years. If fill rates differ sharply between before and after years, the outcome is shown
    with that caveat.
  - The letter is cited only as the reason for the test. A rise, a fall or no change are all reported as found.
  - Los Angeles's TOC areas stay out of group P, as in the main estimate.
- 2026-11-05, pre-count: step 1a script cleared by the audit (review of 659b82c7, fixes applied in 0e566643). Step 1a runs as `scripts/ca_ab2097_step1a_sources.py` at commit 0e566643. Step 1b gets its own audit check before it runs.
