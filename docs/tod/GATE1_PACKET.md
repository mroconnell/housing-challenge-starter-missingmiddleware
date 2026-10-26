# Transit-oriented density: Gate 1 packet (scope and model outline)

Written 2026-10-26 by the TOD conductor, for Ryan. Status: ready for review. An independent review agent checked it first, and its findings are fixed below (section 11). Nothing in Gates 2–5 starts until you decide the items in section 8. Decisions you have already made are in AQ-044 and AQ-045 of the [decision log](../ASSUMPTIONS_AND_QUESTIONS.md).

**Owner reply (2026-10-26, AQ-047):**
- T4: density rules come from measured cases, keeping the most effective well-measured designs.
- T5: no affordability mandate, and parking minimums are left to the parking scenario. Results show TOD alone, parking alone and both combined.
- T6, T7 and T10: approved.
- T8 and T9: depend on the case evidence.
- T1 to T3: still open.

The sections below are the packet as reviewed; where they differ from AQ-047, AQ-047 governs.

Analysis date: 26 October 2026. Stylized law start: 1 January 2027. Forecast years: 2027–2031.

## 1. What this gate decides, and the answer

Gate 1 settles four things for the transit-oriented density (TOD) scenario: what it measures, what law it models, what evidence it rests on, and how that evidence becomes homes.

- **Question:** if Wisconsin passed a statewide law on 1 January 2027 raising allowed density near major transit stops, how many more homes would be permitted over 2027–2031 than under current law? How sure are we, why, and where?
- **Outcome:** housing units at permit issuance, by building size (1, 2, 3–4, 5 or more units). This is the same milestone as ADUs and parking, so the three scenarios compare.
- **Where the law applies:** the main case is land within ½ mile of rail and rapid transit stations (the Hop and Kenosha streetcars, Milwaukee's CONNECT 1 rapid bus, Madison's Rapid Route A), and within ¼ mile of bus routes that run every 15 minutes.
  - **Homes covered:** 313,357 of Wisconsin's 2,727,726 homes in the 2020 census (11.5%) ([MAJOR_TRANSIT_STOP.md](MAJOR_TRANSIT_STOP.md)).
  - **Where they are:** Milwaukee County and Dane County hold 98.7% of them. So the scenario is two metro studies plus a simple statewide rule (AQ-044).
  - **Amtrak:** these figures leave Amtrak stations out (decision T3). With them, the figure is 318,394 homes.
- **Baseline near stops:** if each city's baseline is shared out by its share of homes near stops, about 11,870 of the 118,822 homes in the 2027–2031 all-housing baseline would be permitted in these areas without the law. The range is 6,851 to 17,903. 99.4% of the 11,870 fall in the two counties. Census permits under-count Milwaukee's apartments, so this is low for Milwaukee.
- **The law to model:** no state has passed a law that fully meets the benchmark. The nearest are California SB 79, Washington HB 1491, British Columbia's Bill 47 and Massachusetts's MBTA Communities law, and each has escape hatches (section 2). We model the benchmark plainly, with density floors taken from those laws (section 3).
- **What the evidence says so far:** US upzonings near transit have not reliably raised permits within five years ([PRODUCTION_EVIDENCE.md](research/PRODUCTION_EVIDENCE.md)).
  - **Chicago:** the 2013 and 2015 TOD ordinances had no measurable effect on permitted homes.
  - **Los Angeles:** its program is estimated to have added about 562 homes over six years, about 94 a year. The city permitted about 9,900 homes a year (2,278 to 2,656 a quarter), so that is under 1%.
  - **Strong markets:** large effects came from plain upzonings in very strong markets. Auckland's 2016 upzoning added about 21,808 consented homes over 2016–2021, about 4.1% of its 2016 housing stock.

  Expect a TOD answer much smaller than the ADU answer of 8,757 extra permits (central scenario), and one that depends on market strength: Madison more than Milwaukee.

## 2. Policy classification (who really did it)

No published report grades state TOD laws. The closest, an Urban Institute comparison of 7 laws (December 2025), compares them without grading. So we built the classification from statute text.

**Ratings:**
- **At** means parcel-level height or density rights near defined stops, approved by right, with escape hatches small enough that most station land gains real capacity within a few years.
- **Near** means the core matches the benchmark, but one or two escape hatches shrink or delay it.
- **Weaker** means a planning duty, an opt-in, a capacity average or a grant incentive.

| Law | Rating | Main reason |
| --- | --- | --- |
| California SB 79 (2025) | Near | Parcel-level floors and a by-right path. But: temporary exclusions until about 2030, 7 counties only, and 7% to 13% affordable units on projects over 10 homes |
| Washington HB 1491 (2025) | Near | No parking minimums, plus a state fallback ordinance. But: averages, not parcel floors; 10% to 20% affordable units in every building; deadlines to 2029 |
| British Columbia Bill 47 (2023) | Near | Parcel-level floors at listed stations. But: rezoning is still needed |
| Massachusetts MBTA Communities (2021) | Near | The only enforced, numeric, by-right mandate. But: 15 homes per acre averaged over a district as small as 50 acres, and 96 of 177 towns can put it anywhere |
| Colorado HB24-1313 (2024) | Weaker | A citywide capacity target; each center needs only 15 homes per acre |
| Oregon climate-friendly areas (2022) | Weaker | Not tied to stops |
| Utah HB 462 (2022), Connecticut PA 25-1 (2025), Maryland HB 538 (2024) | Weaker | Planning-only, opt-in or affordability-conditioned |
| Virginia SB 717 (2026) | Not enacted | Would have been "at" (6 storeys and 30 homes per acre within ¼ mile) |

Full tables with statute sections: [STATE_LAWS_WEST.md](research/STATE_LAWS_WEST.md), [STATE_LAWS_EAST.md](research/STATE_LAWS_EAST.md).

## 3. The law we propose to model

"Floor area ratio" (FAR) is building floor space divided by lot area. On a 10,000 sq ft lot, FAR 2.5 allows 25,000 sq ft of floor space, for example a 5-storey building covering half the lot.

| Where | Allowed by right on residential and commercial parcels | Source |
| --- | --- | --- |
| Within ¼ mile of a streetcar or rapid bus station | 65 feet, FAR 3.0, 100 homes per acre | California SB 79's standard for light rail (which includes streetcars) and dedicated-lane rapid bus, inner ¼ mile |
| ¼ to ½ mile from those stations, in cities of 35,000 or more people | 55 feet, FAR 2.5, 80 homes per acre | SB 79, same standard, outer ring (SB 79 applies the outer ring only in cities of 35,000 or more) |
| Within ¼ mile of a 15-minute bus route | 55 feet, FAR 2.5, 80 homes per acre (recommended; see T4) | **Our extension.** No law sets a floor for ordinary buses in mixed traffic. This applies SB 79's lowest standard. FAR 2.5 also matches Washington's average for rapid bus areas. The alternative is British Columbia's floor for bus exchanges in its larger regional cities: FAR 3.5 within 200 m and 2.5 from 200 to 400 m |

What the modelled law does not include:
- **Amtrak stations** (recommended; see T3). SB 79 counts commuter rail only at 48 or more trains a day. Wisconsin's Amtrak stops are served far less often; the exact daily counts are to be confirmed from the timetable at Gate 2.
- **Parking minimums.** They are removed in these areas, as the benchmark allows (T5).
- **Local escape hatches.** Approval is by right, with no local opt-outs, averaging or exclusion maps.
- **An affordability mandate.** The benchmark is a plain density increase, and the Los Angeles and Seattle evidence shows mandates can cancel the effect. A mandate version can be a sensitivity case.

**Places already at the law get no addition**, as for ADUs. Madison's 2023 TOD overlay already raised density along Rapid Route A, and Milwaukee's zoning near CONNECT 1 is coded the same way. Each place's addition comes only from the gap between its current rules and the modelled law.

**Places near stops whose current zoning we have not coded (T9).** As in the ADU work (AQ-023), they are treated like the coded places in the same city, and shown as their own line in the trace, never silently set to zero or to full gain.

## 4. How the model will work

### 4.1 Diagram

```
Homes and land near qualifying stops (federal transit map + 2020 census blocks + parcels)
        │
        ├─► Baseline: shared all-housing baseline × share near stops ─────────────► permits without the law
        │
        └─► Gap in allowed density (modelled law − current zoning, floored at 0)
                 │
                 ├─ Method A: permits per acre per unit of added density, from upzoned areas (by year since the change)
                 └─ Method B: feasible capacity (local rents vs building costs) × measured take-up rate
                          │
                          ▼
                 Addition by year (ramp from the cases) ──► station areas ──► cities, counties, districts, state
```

### 4.2 Two methods, tested against each other

Both methods work on areas, never on individual lots. Held-out cases decide between them at Gate 3, as in the ADU work.

**A. Before and after in upzoned station areas.** For each case, we count homes permitted per year in the upzoned areas, against nearby areas that were not upzoned, by year since the change. Each case raised density by a different amount, so the result is scaled per unit of added allowed density: extra permits per acre per year for each 1.0 of added FAR. That makes the cases comparable, and the dose itself comes from the data.

The cases:
1. Madison's TOD overlay (2023);
2. Chicago's 2013 and 2015 ordinances, a Midwestern rail city with open permit data;
3. Los Angeles's program;
4. São Paulo and Auckland, as the strong-market upper end.

Each case's published measure is converted to permits per acre with a stated rule. For example, São Paulo's +66% multifamily permit filings per block is converted using that city's own pre-change filings per block. A case that cannot be converted is shown as context only.

**B. Capacity, feasibility and take-up.** For each station area:
- **New capacity:** the homes the modelled law allows, minus the larger of what current zoning allows and what already stands. That is the parcel area × 80 homes per acre (or 100), minus the larger of (parcel area × the current allowed density) and the existing homes, floored at zero.
- **Feasibility:** the share of that capacity on sites where a mid-rise building would pay for itself at local rents (ACS) and building costs.
- **Take-up:** the share of feasible sites that redevelop each year, measured from Milwaukee permits only. Madison is held out for the test below.

### 4.3 The Madison test, and its limits

Before we tabulate Madison's apartment permits inside versus outside the overlay, we write down the definition, the comparison areas and the rule. Then each method predicts the overlay's effect.

Three limits apply:
- **Earlier look:** we have already looked at Madison's permits for the ADU work, including ADUs inside and outside the overlay (AQ-029), but not at apartments by overlay.
- **Short window:** there are only three full years after the overlay (2023–2025). 2026 is partial and is shown but not fitted on.
- **Rapid Route A** opened in 2024, during the test period.

The positive cases elsewhere show little in years 1 and 2, so the test may be too weak to separate the two methods. If so, the fallback is to hold out Chicago instead, and to report that neither method could be confirmed in-state.

### 4.4 Then, as for ADUs

- **Baseline:** the shared all-housing baseline, shared out to station areas by each city's share of homes near stops. The rule is tested against where Milwaukee and Madison permits actually landed. If you approve the parking thread's decision P8, Milwaukee's apartment series uses the city's property file.
- **Ramp:** taken from the cases' years since the change, not assumed.
- **Scenarios** are named by meaning, each built from real cases, never by dividing or multiplying another:
  - "Little response (like Chicago and Los Angeles)";
  - "Like Madison's overlay";
  - "Strong-market response (like Auckland and São Paulo)".
- **Sensitivities** are grouped by what they move:
  - the law's addition;
  - the baseline only;
  - only where homes land;
  - the stop definition and distance, as their own group.
- **Rest of the state:** the places outside Milwaukee County and Dane County, which hold 1.3% of the homes near stops, use the same method with their own market strength.

### 4.5 Bottom-up and top-down

- **Bottom-up:** stops from the transit map. This is the headline.
- **Top-down cross-check:** the EPA Smart Location Database counts 579,836 of 2,681,232 homes (2018), or 22%, in block groups with 4 or more transit trips an hour. The bottom-up figure is 15% within ½ mile of all 15-minute stops.

  The EPA measure counts both directions and every route near a block group, so it should come out higher. It is the route a state without schedule data could use. Both are reported; the gap is a measure of how much a data-poorer state would overstate coverage.

### 4.6 Worked example: tracing one station area

Status of each input: available, to build, or to measure.

| Step | What happens | Inputs | Status |
| --- | --- | --- | --- |
| 1 | Pick a stretch of a 15-minute Milwaukee route. Census blocks within ¼ mile hold *H* homes on *L* acres of parcels | Transit map, 2020 blocks | Available |
| 2 | Baseline: Milwaukee's 2027–2031 baseline permits × this area's share of Milwaukee homes near stops = *B* | Shared baseline | Available (Milwaukee correction pending P8) |
| 3 | Rights: current zoning allows *Z* homes per acre; the law allows 80. New capacity = max(*L* × 80 − max(*L* × *Z*, existing homes), 0) | Milwaukee zoning, parcels | To build: Milwaukee zoning and statewide parcels are not yet in the repo |
| 4 | Response: method A gives extra permits per acre per year per 1.0 of added FAR. Method B gives feasible new capacity × Milwaukee's measured take-up rate | Cases; ACS rents; building costs | To measure at Gate 3 |
| 5 | Ramp and totals: spread the addition over 2027–2031, then add up to Milwaukee, Milwaukee County, Assembly and Senate districts, and the state | Shared district crosswalk | Available |

### 4.7 Output data contract (Gate 2–3 files)

- `reference/tod_stops.csv`: qualifying stops by definition, with source and frequency basis.
- `reference/tod_station_areas.csv`: homes, acres, current and modelled density, by area and definition.
- `reference/tod_cases.csv`: the comparison cases, each marked "observed" or "source lead". Each case also records, for the year of its change and each year after, how many of its state's (or country's) large cities had adopted a transit-area upzoning, and their share of the state's large-city population. This is collected now so a later question can be answered: does a city's response differ when most of its state's large cities reform at the same time (owner's question, 2026-10-26)? The parking scenario records the same measure for parking repeals.
- `reference/tod_model_statewide.csv` and `reference/tod_model_by_area.csv`: baseline and additions by year and scenario.
- `reference/tod_model_sensitivities.csv`.
- The tool bundle goes in `ui/public/scenarios/tod/runs/`, following [SCENARIO_CONTRACT.md](../shared/SCENARIO_CONTRACT.md).

## 5. What the tool can show (to be confirmed at Gate 2)

| ADU tool element | TOD | Note |
| --- | --- | --- |
| Wisconsin today | Yes | Homes near stops by definition, transit lines on a map |
| Baseline and three scenarios by year | Yes | |
| Median line of real cases | Only if method A yields enough cases | Probably too few; we will say so |
| Sensitivities grouped by what they move | Yes | Adds the stop-definition ladder and the distance |
| Data-versus-assumption trace | Yes | |
| Where | Redesign | A list or map of station areas and corridors in the two metros, not a map of 1,925 places (T10) |
| Pilot examples | Yes | A Madison Rapid Route A corridor; a CONNECT 1 corridor; Eau Claire, which has the only 15-minute routes outside the two metros, as the "does it transfer" check |
| Reform picker | Done | On main ([SCENARIO_CONTRACT.md](../shared/SCENARIO_CONTRACT.md)) |

## 6. Data and licences

| Data | Use | Licence | Status |
| --- | --- | --- | --- |
| Federal National Transit Map (BTS): stops, routes, agencies, compiled 2026-09-23 | Stop locations and route lines, every agency | Stops layer: CC BY 3.0; agency table: public domain | Fetched by script; committed fetch at Gate 2 |
| Agency schedule files (16 agencies) | Route frequency | Per agency. Milwaukee requires "not sponsored" and date notices | Fetched by script. Milwaukee's server times out, so a May 2025 copy is used for now |
| Madison route descriptions in the transit map | Madison route frequency | As the map | Used instead of Madison's own file (AQ-045) |
| Madison Metro schedule file | Not used | Restrictive (office-hours questions 24 and 25) | Set aside |
| 2020 census blocks (housing units) | Homes near stops | Public domain | In repo |
| Shared all-housing baseline | Baseline | Built from public-domain Census permits | In repo |
| Wisconsin statewide parcels | Capacity, existing buildings (method B) | Public records | Only Dane and Kenosha extracts in repo; statewide fetch at Gate 2 |
| Madison zoning and TOD overlay boundary | Current rights; Madison test | Public records | In repo |
| Milwaukee zoning | Current rights | Public records; to check | Not in repo; Gate 2 |
| Madison and Milwaukee permits, Milwaukee property file | Madison test; take-up rate | Public records; property file CC BY | In repo |
| ACS rents and values by tract | Market strength (method B) | Public domain | In repo |
| Building costs | Method B | To find | Gate 2 |
| Chicago and Los Angeles permit open data | Method A cases | City terms of use; to check | Gate 2 |
| EPA Smart Location Database | Top-down cross-check | Federal public data | Fetched by script |
| Published studies (Auckland, São Paulo, Chicago, Los Angeles, Zurich, Urban Institute) | Method A ranges and checks | Cited, not redistributed | Read |

## 7. Owner review steps

1. **Read section 1.** Does the question match what you want to answer?
2. **Read the table in section 2.** Do the ratings match your sense of which states really did it?
3. **Read the table in section 3.** Are those heights and densities what you'd call "the benchmark, done properly"? Note which row is our own extension.
4. **Follow the worked example in section 4.6** from homes near a stop to extra permits. Check which inputs are still missing.
5. **Open [MAJOR_TRANSIT_STOP.md](MAJOR_TRANSIT_STOP.md), section 3.** Check the Milwaukee County and Dane County share against your sense of where frequent transit runs.
6. **Read the "Bottom line" of [PRODUCTION_EVIDENCE.md](research/PRODUCTION_EVIDENCE.md).** Are you comfortable with a TOD answer that may be small?
7. **Decide T1 to T10** in section 8.

**Self-assessment.** I walked each step myself.
- **Step 3:** the floors trace to statute sections in the research files, except the 15-minute bus row, which is our extension and is now labelled as such.
- **Step 4:** the worked example runs end to end on paper. The missing inputs are Milwaukee zoning, statewide parcels and building costs; that is the main Gate 2 load.
- **Step 5:** the stop counts look right against the networks. The route-level test drops some Milwaukee suburban stops where two 30-minute routes overlap.
- **Weakest point:** evidence transfer. Wisconsin's markets are softer than the cases with large effects, and the case closest to Wisconsin, Chicago, shows none. The Madison test may be too short to settle it (section 4.3).

## 8. Decisions requested

| # | Decision | Recommendation |
| --- | --- | --- |
| T1 | Outcome | Housing units at permit issuance, by building size, as for ADUs and parking |
| T2 | Law start | Stylized 1 January 2027 |
| T3 | Which stations | Streetcars and rapid bus (CONNECT 1, Rapid Route A) count as rail and rapid stations; Amtrak stations do not (below SB 79's 48-trains-a-day test). This changes the main case from 318,394 to 313,357 homes |
| T4 | Density floors | Streetcar and rapid bus stations: SB 79's light-rail standard (65 feet, FAR 3.0, 100 homes per acre within ¼ mile; 55 feet, FAR 2.5, 80 homes per acre to ½ mile in cities of 35,000 or more). 15-minute bus within ¼ mile: 55 feet, FAR 2.5, 80 homes per acre, our extension of SB 79's lowest standard. British Columbia's bus floors as the alternative and as a sensitivity |
| T5 | Parking inside TOD | Minimums removed in the TOD areas, as the benchmark allows. Not netted against the parking scenario, per your earlier direction |
| T6 | Method | Build A (before and after, scaled per unit of added density) and B (capacity × feasibility × take-up). The Madison test decides; Chicago is the fallback hold-out |
| T7 | Scenarios | Named by real cases: little response (Chicago, Los Angeles), Madison-like, strong market (Auckland, São Paulo) |
| T8 | Places already at the law | No addition. Madison's overlay and Milwaukee's zoning near CONNECT 1 are coded against the law |
| T9 | Uncoded zoning near stops | Treated like coded places in the same city, shown separately in the trace |
| T10 | The "Where" screen | Station areas and corridors in the two metros, with the rest of the state as one line; design shown at Gate 2 |

One earlier decision needs a correction, for you to note. The ladder you confirmed in AQ-044 included California's definition, where two 15-minute routes meet. That definition needs stop-level timetables, which the federal transit map does not have. So it drops off the ladder under AQ-045, and the ladder runs:
1. rail and rapid only;
2. the main case;
3. 20-minute service;
4. all frequent stops within ½ mile.

## 9. Limitations and schedule

- **City programs are not a statewide law.** Cities chose to upzone, often with other changes at the same time. Comparison areas and the hold-out test address this only in part.
- **Proposals are not permits.** Los Angeles shows that many more proposals need not mean more permits, so the outcome is fixed at permits.
- **Few cases, mixed designs.** Only Chicago and Madison resemble Wisconsin, so ranges will be wide, and we will say so.
- **Frequency data has gaps.**
  - Milwaukee's schedule is a 2025 copy.
  - Green Bay has no current schedule.
  - Madison's frequency comes from route descriptions.
  - The route-level test misses overlapping routes.
  - The 30-metre tolerance for "on the route" and the 7:00–8:59 test hours are our choices; both are sensitivity cases.
- **Five years is short for mid-rise housing.** Vancouver's Broadway Plan had 24,778 homes proposed in 126 projects by late 2025, about three years in, but only 4 of those projects had reached building permit. Much of a TOD law's effect may fall after 2031, and the brief will say so.
- **Schedule:** about 7 weeks remain to 16 December.
  - Gate 2 (data) target: 9 November.
  - Gate 3 (model) target: 20 November.
  - Gate 4 (tool) target: 30 November.
  - Gate 5 target: 7 December.

  If method B's data (statewide parcels, Milwaukee zoning, building costs) is not ready by 9 November, method B is cut to the two metros and the rest of the state uses method A alone.

## 10. Questions for office hours

Already in the [decision log](../ASSUMPTIONS_AND_QUESTIONS.md): 24 (Madison Metro's licence) and 25 (whether the transit map's data carries the agencies' licences).

Added on 2026-10-26 and shared with the parking scenario:
- **26:** does evidence from city programs satisfy "grounded in evidence" for a statewide law when no state law has post-law permit data? (shared with parking)
- **27:** may the TOD scenario remove parking minimums inside station areas while the parking scenario is reported separately, without netting the two?

Relevant to T5: the parking scenario's comparison found no measurable average rise in permits in the 3 years after a parking repeal, across 24 US places ([COMPARISON_RESULTS.md](../parking/COMPARISON_RESULTS.md)). So the parking part of the TOD law is not expected to add much on its own.

## 11. Independent review

An independent review agent checked this packet on 2026-10-26 against the research files, the challenge rules and the parking packet. It confirmed every headline number against its source. It found 4 blockers:
1. a missing review note;
2. the bus floor overstated as agreed by three laws, when it is our extension;
3. Amtrak placed on a rail standard it does not meet;
4. the Madison test described as cleaner than it is.

It also found 11 other issues, among them:
- no dose scaling in method A;
- a double subtraction in the worked example;
- a pending parking decision described as settled;
- the dropped California definition;
- missing Gate 1 items: diagram, rating table, unknown-zoning rule, top-down comparison, output contract, schedule;
- jargon.

All are fixed above, except the office-hours question merge with parking, which is coordinated with the parking thread.
