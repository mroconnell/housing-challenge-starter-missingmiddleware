# Transit-oriented density: Gate 1 plan

Written 2026-10-26 by the TOD conductor. Status: plan for owner review; no Gate 1 work has been accepted yet.

The question, in the owner's terms: **if Wisconsin passed a statewide transit-oriented density law at the challenge benchmark, how many additional homes would be permitted over 2027–2031 compared with current law, how confident are we, why, and where?**

Benchmark (verbatim, [CHALLENGE_SPEC.md](../CHALLENGE_SPEC.md)): *Increase allowable residential density near major transit stops via greater heights and/or floor area ratios. Define "major transit stop" and justify your proximity threshold. You may assume parking requirements are reduced or eliminated.*

## 1. Research questions

1. **Which reforms really happened?** Which states and cities raised allowed density near transit in a way that matches the benchmark, and which passed weak versions (opt-outs, alternative compliance, tiny station areas, discretionary review kept, affordability mandates that make projects infeasible, capacity "on average" rather than on every parcel)? Effective dates and local-compliance dates recorded separately.
2. **What happened to permits afterward?** For each benchmark-faithful case: homes permitted in the station areas per year, before and after the change, per acre or per existing home in the station area, by year since the change. Each figure marked "observed" (official file) or "source lead" (news, report, vendor).
3. **What is a "major transit stop", and how far does the effect reach?** Candidate definitions: rail or bus rapid transit station; bus stop with a stated peak frequency (for example every 15 minutes). Candidate distances: ¼ mile and ½ mile. Evidence: statute definitions (California, Colorado, Washington, Oregon, Massachusetts), and whether permits in the comparison cases fall off with distance from the stop.
4. **How much of Wisconsin is near a qualifying stop?** Two routes, compared:
   - bottom-up: stops from public transit schedules (GTFS), filtered by frequency and mode, buffered, then homes, land and recent permits counted inside;
   - top-down: share of homes likely to be near a qualifying stop, predicted from block or tract density and urban-area size, without stop data (the route a data-poorer state could use).
5. **Does the response transfer?** Do mid-size, bus-only cities respond like rail cities and big metros? Wisconsin's markets are softer than Los Angeles or Auckland, so a market-strength check is needed, settled by held-out cases rather than a chosen multiplier.
6. **What is the current-law baseline in station areas?** The all-housing baseline comes from the parking session (Census building permits by area, year and structure type, 2027–2031 projection). TOD's baseline is the share of it near qualifying stops; the allocation rule is tested against Madison and Milwaukee permit locations already in the repo.

## 2. Policy-taxonomy search

Step 1, look for an existing classification (the Mercatus-for-ADUs equivalent). Candidates to check: Mercatus Center work on state transit-zoning laws; Terner Center (Berkeley) analyses of SB 79 and earlier California transit laws; Pew and Brookings state zoning-reform trackers; the Massachusetts Housing Partnership and Boston Indicators reviews of MBTA Communities; Sightline on Washington and Oregon; academic reviews of Auckland's 2016 upzoning (Greenaway-McGrevy and coauthors).

Step 2, if none separates real from weak reform, build the classification from statute text, with one row per law or program and these columns: station definition, distance, density or height floor, by-right or discretionary, opt-outs and alternative compliance, affordability conditions, parking treatment, effective and compliance dates, and a benchmark rating (at, near, weaker) with the reasoning. Starting leads (unverified): Massachusetts MBTA Communities, California SB 79 and earlier transit laws, Colorado HB24-1313, Washington HB 1491, Oregon climate-friendly areas, Utah HB 462, Connecticut PA 25-1, and the city programs in Los Angeles (Transit Oriented Communities), San Diego, Minneapolis, Seattle, Portland and Auckland, plus Madison's own TOD overlay as the in-state case.

Expectation from the leads: no state law has two or more years of permit data yet, so the evidence will probably be city programs plus a station-area capacity and feasibility check, not a pooled state rate. Both will be tested if the data allow.

## 3. Data candidates (licence to be checked for each before use)

| Need | Candidate | Notes |
| --- | --- | --- |
| Stops and service frequency | GTFS feeds: Milwaukee County Transit System (including the CONNECT 1 bus rapid transit line and the Hop streetcar), Madison Metro (including Rapid Route A), Green Bay, Valley Transit (Fox Cities), Kenosha, Racine, Waukesha, La Crosse, Eau Claire and others; Amtrak and Metra | Fetched automatically from the agencies or the Mobility Database; licence per feed |
| Agency service levels | National Transit Database | Already in the repo (public domain) |
| Homes and land near stops | 2020 census blocks with housing-unit counts; ACS; Wisconsin statewide parcels (V12) | Census and V12 already used by the ADU work |
| Current-law baseline | All-housing baseline from the parking session | Shared, not fetched twice |
| In-state before/after | Madison TOD overlay boundary and Madison permits | Both already in the repo |
| Comparison cases | Los Angeles building permits and planning reports on the TOC program; Massachusetts 3A development tracker; California housing progress reports (Table A2, already in the repo); Minneapolis, Seattle and Portland permits (already in the repo); Auckland Council consent data | Some of these are city open data with stated licences; check each |
| Transit for the parking session | The same stop and frequency layer | Built once here and shared, if the parking session needs it |

## 4. Tool outputs expected (to be confirmed at Gate 2)

From the ADU tool: a baseline line and three scenarios by year, labelled by meaning; a median or reference line of real cases if enough cases exist; sensitivities grouped by what they move; the trace of what rests on data versus assumption; pilot pages. The "Where" screen likely needs a different design, because most of the effect may sit in Milwaukee and Madison: probably a list of station areas and cities rather than a 1,925-place map. That design is a decision for the owner at Gate 2, once the station-area counts are known.

## 5. Shared piece: the multi-scenario tool shell

Built alongside Gate 1–2 research, after the coordinator hands over ownership of the shared UI files for this piece: a scenario picker and registry, shared screens that read the selected scenario, and `docs/shared/SCENARIO_CONTRACT.md`. The ADU screens, numbers and tests must not change apart from the picker. A test will check that the ADU bundle and screens are unchanged.

## 6. Decisions needed from the owner

| # | Decision | Recommendation |
| --- | --- | --- |
| T1 | Outcome | All housing units in permits at issuance, in station areas, the same milestone as ADUs, so the scenarios compare |
| T2 | Law start | Stylized 1 January 2027, as for ADUs |
| T3 | How strong a law to model | Take the density floor, heights and distances from the benchmark-faithful state laws found in step 2 (for example the median of them), not a number we choose; the owner approves the resulting law text at Gate 1 |
| T4 | Parking inside TOD | Assume parking minimums are removed in station areas, as the benchmark allows, and say so; no netting against the parking scenario |
| T5 | Bottom-up or top-down for the headline | Decide at Gate 2 with held-out tests; build both |
| T6 | How the tool shows a two-city scenario | Decide at Gate 2 once station-area counts are known |
| T7 | Start the shell now | Yes, in parallel with research, once the coordinator confirms the file handover |
