# CA AB 2097: statewide effect on permits — options and plan (DRAFT, not locked)

Written 2026-11-05 by the CA AB 2097 thread, before any new permit count. Status: **draft for Ryan and the audit**.
Nothing runs until Ryan picks the options in section 5 and the audit clears the lock.

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

What to expect, stated now:
- The earlier range was about ±1.5 homes per 1,000 existing homes a year. Across 1,276,507 near-transit homes that is about
  ±1,900 homes a year.
- A better map should reduce dilution toward zero. It will not make the range much narrower.
- **Most likely outcome: the "no measurable change" answer stands.** The study is worth running if the map fix matters, or if
  the year-by-year view shows a lead-up gap like Test 49 found nationally.

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
   under the strict rule, and used as a **placebo group** (expected: no change at their line in 2023).
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
4. **Expectation stated now.** The paper expects a modest, uneven effect: uneven local reading, the "findings" escape
   hatch, and developers who keep parking. A null near-vs-ring result fits this and does not show the law did nothing
   for any project.

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
   - **Clear positive** (range above 0, leads balanced): evidence the law raised permits near transit on average,
     despite uneven local reading. Net statewide gain only if the dose check agrees.
   - **Clear negative** (range below 0, leads balanced): does not fit the paper's account; read first as a sign of a
     confound (other laws, rates, LA programs) or of homes moving away, not as the law cutting homes, unless the
     dose check and the placebo group both support it.
   - Any result with trending leads or a placebo-date "effect": not evidence of cause (item 5 of the first audit block).
