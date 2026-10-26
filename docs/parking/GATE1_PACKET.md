# Parking scenario: Gate 1 packet (scope and model outline)

Written 2026-10-26 by the parking conductor, for Ryan. Status: ready for review. Nothing in Gates 2–5 starts until you decide the items in section 6.

## 1. What this gate decides, and the answer

Gate 1 settles what the parking scenario measures, what evidence it rests on, and how it will turn that evidence into homes.

- **Question:** if Wisconsin removed minimum parking requirements for all housing statewide from 1 January 2027, how many additional homes would be permitted over 2027–2031 than under current law, how sure are we, why, and where?
- **Outcome:** housing units at permit issuance, by building size (1, 2, 3–4, 5+ units), the same milestone as the ADU scenario.
- **Baseline:** the shared all-housing baseline. About 118,800 units would be permitted over 2027–2031 under current law, with a range of 62,200 to 169,800 ([HOUSING_BASELINE.md](../shared/HOUSING_BASELINE.md)).
- **Evidence base:** cities, not states. No state has removed minimums for all housing. No state law was adopted before 2022, and none has had three full years of permits since taking effect. The Parking Reform Network database gives 47 US cities that removed minimums for all housing, by right, in 2022 or earlier, and 26 of them have at least 20,000 people ([POLICY_TAXONOMY.md](POLICY_TAXONOMY.md)).
- **Where minimums still bind in Wisconsin:** 9 Wisconsin cities and villages already meet the benchmark, including West Allis (2022), La Crosse (2024), Fitchburg (2025) and Franklin (2025). They get no addition from the law. Another 9 nearly meet it (for example DeForest, for multifamily only), and they would get a partial addition. Madison and Milwaukee have partial reforms only.
- **Developer-provided parking:** taken from post-repeal studies, not chosen by us. The clearest full study, Buffalo, found mixed-use projects built 47% of the old minimum, while stand-alone apartment buildings built 117% of it (1.34 spaces per unit against a minimum of 1).

## 2. How the model will work (outline)

Extra homes come only where the minimum forced more parking than developers would have built anyway. Two methods will be built and tested against each other on held-out cities at Gate 3, the same way the ADU work let the data decide:

- **A. Before and after in repeal cities.** Permits per 1,000 existing homes per year, by building size, in each repeal city before and after its repeal, against matched cities that did not repeal (Census permit data, all US places). This gives a direct "percent more homes" by year since repeal.
- **B. Cost saved times supply response.** The spaces no longer required (old minimum minus what developers would still build) times cost per space gives a cost cut per unit. A published supply response turns that cut into more permits, applied only to baseline permits in the building types and places where minimums bind. The Denver study (Terner Center, 2025) used this approach and found about 12.5% more market-rate apartments in a much stronger market.

Then, as for ADUs:
- the law never subtracts: places already at the benchmark get 0;
- the ramp over 2027–2031 comes from the repeal cities' years since repeal;
- the scenarios are named by meaning (for example, "like the weakest repeal cities"), with a median line of real cases;
- sensitivities are grouped by what they move, with the developer-provided-parking range as its own group.

## 3. What the tool can show (to be confirmed at Gate 2)

| ADU tool element | Parking | Note |
| --- | --- | --- |
| Baseline and three scenarios by year | Yes | |
| Median line of real cases | Yes, if method A gives enough cities | |
| Sensitivities grouped by what they move | Yes | Adds the developer-provided-parking range |
| Data-versus-assumption trace | Yes | |
| Where: counties, municipalities, districts | Probably a ranked list | The effect concentrates in apartments in larger places; design choice at Gate 2 |
| Pilot examples | Yes | Milwaukee or Madison; West Allis as the in-state "already repealed" check; one mid-size or suburban place |

## 4. Data and licences

| Data | Use | Licence | Status |
| --- | --- | --- | --- |
| Census Building Permits Survey (state 1990–2025; WI places 2015–2025) | Baseline; method A outcomes | Public domain | In repo; fetched automatically |
| Census BPS place files, other regions | Method A comparison cities | Public domain | To fetch at Gate 2 |
| Parking Reform Network reform-map data | Classification of reforms | MIT | Fetched automatically, pinned commit |
| Milwaukee Master Property file (MPROP) | Check on Milwaukee's apartment permits | CC-BY | In repo |
| City ordinance text for the comparison and Wisconsin cities | Checking each case | Public records | Gate 2 |
| Published studies (Buffalo, Seattle, Minneapolis, Champaign, Denver) | Developer-provided parking; method B check | Cited, not redistributed | Buffalo read in full; others are source leads |
| Cost per parking space, Wisconsin | Method B | To find | Gate 2 |
| GTFS transit stops (from the TOD session) | Partial-reform comparisons only | Per feed | Shared, not fetched twice |

The reference tables committed so far are `reference/housing_baseline_*.csv`, `reference/parking_reform_taxonomy.csv` and `reference/parking_reform_cases.csv`, all with tests.

## 5. Owner review steps

1. Read section 1 above and the "Answer so far" in [POLICY_TAXONOMY.md](POLICY_TAXONOMY.md). Does the question match what you want to answer?
2. Open `reference/parking_reform_cases.csv` and filter `state` = Wisconsin. Do any of the 18 rows look wrong to you from local knowledge?
3. Open [HOUSING_BASELINE.md](../shared/HOUSING_BASELINE.md) and read "Open issues". Decide P8 and P9 below.
4. Decide P1–P9 below.

**Self-assessment.** I ran each step myself. The Wisconsin list in step 2 fits what I could check: West Allis's and La Crosse's PRN summaries describe code changes with dates. Fitchburg's summary says its minimums were a planning policy, not an ordinance, so its 2025 "repeal" changed less than the date suggests. The baseline reconciles to the published state total in every year and building size (a test checks this). The weakest point is Milwaukee's apartment series (P8).

## 6. Decisions requested

| # | Decision | Recommendation |
| --- | --- | --- |
| P1 | Outcome | Housing units at permit issuance, by building size, as for ADUs |
| P2 | Law start | Stylized 1 January 2027 |
| P3 | Law strength | Full removal for all housing statewide. Partial versions (caps, small projects only) only as sensitivities |
| P4 | Developer-provided parking | A range taken from the post-repeal studies, by project type; shown as its own sensitivity group |
| P5 | Method | Build both A (before/after in repeal cities) and B (cost times supply response); held-out cities decide at Gate 3 |
| P6 | Evidence base | The 47 US cities rated "at" the benchmark and adopted by 2022, each checked against the ordinance before use; cities with simultaneous upzoning flagged and tested with and without |
| P7 | Places already at the benchmark | Get no addition (the "never subtracts" rule); the list comes from PRN, checked against each ordinance |
| P8 | Milwaukee's apartment permits (baseline) | Replace Milwaukee's 3–4 and 5+ unit series with an estimate from the city's property file, as a labelled adjustment; keep Census-as-published as a sensitivity |
| P9 | Baseline range | Wisconsin's long-run 10th–90th percentile five-year outcomes since 1990; the recent-decade range and the 2007–2011 worst case as sensitivities |

## 7. Limitations

- City repeals are not a statewide law: the cities chose to repeal, and many changed other rules at the same time. Matched comparison cities and the held-out test address this only in part.
- Most repeal cities are larger and stronger markets than most of Wisconsin. A transfer check (like the ADU Madison-like-cities test) will be pre-registered at Gate 2.
- PRN dates are mostly adoption dates, and its "adopted" status includes some plans. Every case used is checked against the ordinance.
- The Census permit data under-counts Milwaukee's apartments (P8). Other cities could have similar gaps that have not been checked.

## 8. Questions for office hours

1. Does a city-repeal evidence base satisfy "grounded in evidence" for a statewide-law scenario, given that no state law has post-law data yet?
2. Is a model-based cost-per-unit estimate acceptable as the main method if before/after city data are too noisy?
3. Is it acceptable to correct a Census permit series (Milwaukee) from a city's property file, if the adjustment is labelled and the published series is kept as a sensitivity?
