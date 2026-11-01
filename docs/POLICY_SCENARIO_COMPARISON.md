# Policy Scenario Comparison

Missing Middleware, Wisconsin, 2027–2031. Assembled 2026-10-27 from the three reform sessions' adopted results. Methods and assumptions are in the [Model & Assumptions Overview](MODEL_AND_ASSUMPTIONS.md).

# Scenarios Addressed

The tool compares Wisconsin's current law (the baseline) with three of the five benchmark reforms. Each is modelled as a state law in force from 1 January 2027, and each counts housing units in issued building permits over the five years 2027–2031.

| Reform | The modelled state law | Where it applies | What it counts |
| --- | --- | --- | --- |
| **Accessory dwelling units (ADUs)** | One ADU allowed on every lot with a single-family home, detached or attached, at least 600 square feet, with no extra parking | Every single-family lot in the state (1,839,569 single-family homes) | Second homes added on lots that already have a single-family home |
| **Parking requirement reduction** | No minimum off-street parking may be required for any housing | Every municipality, except the 9 Wisconsin places that have already removed their minimums | All new homes, every building size |
| **Transit-oriented density (TOD)** | Higher allowed heights and density near major transit stops (California SB 79's minimums: 55 to 65 feet), with parking rules unchanged | Within ½ mile of streetcar and rapid-bus stops and ¼ mile of bus stops with service every 15 minutes or better: 313,564 homes (2020 census), 98–99% of them in Milwaukee and Dane counties | All new homes near those stops |

Missing Middle and development fee reduction are not modelled.

**Comparing the three fairly.** The three reforms count different things against different baselines:
- the ADU baseline is 786 second homes on single-family lots statewide over 2027–2031;
- the parking baseline is 124,000 new homes of all kinds statewide over 2027–2031 (shared baseline v3 final, 2026-11-01; was 122,619);
- the TOD baseline is 14,464 new homes of all kinds near major transit stops over 2027–2031.

So this comparison puts every reform on two common footings:
- **as a share of the all-housing baseline**: additional permits ÷ the 124,000 homes Wisconsin is expected to permit over 2027–2031 under current law;
- **per 1,000 existing homes**: additional permits over 2027–2031 ÷ Wisconsin's 2,778,572 housing units (ACS 2020–2024, table B25002) × 1,000.

The ADU share is an approximate size comparison, not a strict share: the Census permit count behind the 124,000 misses many ADUs, especially those built inside or attached to an existing house.

# Ranking of Results

Additional homes permitted over 2027–2031, compared with current law. Scenarios are named by the evidence they stand for, not by statistical confidence.

| Rank (central) | Reform | Lower | **Central** | Upper | Central, then upper, as a share of the 124,000-home all-housing baseline | Central, then upper, per 1,000 existing homes (five-year total) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | **ADUs** | 6,321 | **10,492** | 19,784 | 8.5%; 16.0% | 3.8; 7.1 |
| 2 | **TOD** | 171 | **1,181** | 17,148 | 1.0%; 13.8% | 0.4; 6.2 |
| 3 | **Parking** | −15,326 | **0** | 19,937 | 0%; 16.1% | 0; 7.2 |

What the scenario names mean:
- **ADUs:** the lower is "sluggish adoption" (the average of Rhode Island and Oregon); the central is "typical adoption"; the upper is "strong adoption", the high end of what states with a statewide ADU law have reached, which only California has passed. If Wisconsin followed the median path the eight statewide-law states actually took, the law would add 10,038 homes.
- **TOD:** the lower is a "little response", like Los Angeles's transit program; the central (since AQ-068) is the lot model's drift rule, measured on 9 US transit upzonings: 1,181 extra homes near stops (601 to 1,662 when each city is left out in turn). It was found after seeing results; the rule set in advance gives 798, and Stacy et al.'s typical loosening reform (2,509, the former central) is kept as a comparison. The upper is a "strong response", like Auckland's 2016 upzoning.
- **Parking:** the central is "no measurable change"; the upper is "the high end of the evidence"; the lower is "the low end of the evidence" (owner, 2026-11-01): the measured average of 76 repeal places against similar places, −1.14 permits per 1,000 existing homes per year, applied without a floor at zero. That is −15,326 homes over 2027–2031, 12.5% below current law. It is driven mostly by San Francisco and Minneapolis.
- **Median lines.** A "median of real cases" line is shown only where a reform has at least four comparable cases. ADUs (8 states) and parking (76 places) have one. Parking's median place changed by −0.12 permits per year per 1,000 existing homes, so its line is shown at 0, the same as its central. TOD has only three whole-city studies, so it has none.

ADU figures were revised again on 2026-11-01 (AQ-067 in the [assumptions log](ASSUMPTIONS_AND_QUESTIONS.md)): lower 6,321, central 10,492, upper 19,784 on a 786 baseline. Massachusetts' 2025 count is now divided by a full year, because its survey covers January. Earlier that day (AQ-066) they were 6,321, 10,615 and 19,925, when Madison moved onto the statewide model like every other place. Before that they were 6,223, 10,349 and 19,294 on 786 (AQ-065, 2026-10-31), 6,804, 10,679 and 19,535 on 530 (AQ-064, 2026-10-29), 6,734, 10,788 and 20,057 (AQ-061, 2026-10-28), and first 5,538, 8,757 and 16,889 on 605. ADU shares are of the 124,000-home all-housing baseline (central 10,492 ÷ 124,000 = 8.5%; upper 19,784 ÷ 124,000 = 16.0%); per 1,000 existing homes they are ÷ 2,778.572 thousand housing units (central 3.8; upper 7.1).

**Against each reform's own baseline:**
- The ADU central adds 10,492 second homes to a baseline of 786, which is 13.3 times as many as current law would produce.
- The TOD central adds 1,181 homes to a baseline of 14,464 near stops, which is 8.2% more.
- The parking upper adds 19,937 homes to a baseline of 124,000, which is 16.1% more (about 3,987 a year).

**How confident we are.**

| Reform | Confidence in the central | Why |
| --- | --- | --- |
| ADUs | Medium | Eight states have passed similar laws. When each is left out, the model predicts five of the seven non-California states within about 15%; it is about 21% too high for Washington and 19% too high for Vermont. No Midwest state has data yet. |
| TOD | Low | The three studies that size the effect disagree about a hundredfold. None is a Wisconsin test, and the typical study is mostly of ADU and lot-size reforms, not transit upzonings. |
| Parking | Medium that the effect is small within five years; low on the high end | 76 real repeals show no measurable rise on average within three years. |

**The ranking depends on the scenario.** On the central scenarios the order is ADUs, then TOD, then parking. On the upper scenarios parking (19,937) is just ahead of ADUs (19,784), then TOD (17,148). The gap is 153 homes: 0.8% of parking's 19,937. So the top two are close to tied on the upper scenarios.

# What Drives the Differences

**ADUs add the most in the central scenario because the law creates a right on almost 1.84 million lots where today very few owners build one.**
- At today's pace Wisconsin would permit 530 second homes on single-family lots over five years. That is 0.06 permits per 1,000 single-family homes per year.
- The tool's baseline also rises 7.3% a year, as ADU permits did in places with no statewide law. That gives 786 over 2027–2031, or 0.09 permits per 1,000 single-family homes per year (AQ-065).
- In the eight states with a statewide ADU law, a typical place reached about 1.1 permits per 1,000 single-family homes per year once the law had been in force four years.
- The model applies that rate to Wisconsin's 1,839,569 single-family homes, phased in (about 68% of the full effect in 2027, 85% in 2028 and all of it from 2029). It spreads the statewide total across places by home value alone: a place with 10% higher home values gets about a 10% higher rate.

**TOD adds a small share in the typical case because the area it covers is small, and the measured citywide effects of upzoning are modest within five years.**
- The law reaches the 313,564 homes near frequent transit, which is 11.5% of Wisconsin's 2,727,726 homes (2020 census).
- The typical study found an extra 0.8% growth in the housing stock three or more years after a loosening reform. Applied to the station areas, that is 2,509 homes, the former central; since AQ-068 the central is the lot model's drift rule, 1,181.
- Places already at or above the law's heights and densities get no addition.

**Parking's central is zero because the 76 US places that removed their parking minimums did not permit measurably more homes in the next three years than similar places that kept them.**
- The places removed minimums between 2017 and 2022. They were drawn from 46 places that adopted repeals in 2015–2022, each checked against its ordinance.
- Each place's permits per 1,000 existing homes in up to five years before the repeal (from 2012) were compared with years 1–3 after it, against similar places in the same state that kept their minimums (a difference-in-differences).
- Weighted by each place's number of homes, the average change was −1.14 permits per year per 1,000 existing homes (all housing units, ACS 2020–2024 table B25002). The 90% range was −3.47 to +1.43, which includes zero.
- In plain words, developers in those places kept building about as much parking as buyers, renters and lenders wanted. In Buffalo, the developers of 36 major projects still built 79% of the spaces the old minimums had required. So where a minimum did not force more parking than the market wanted, removing it changed little.
- The law is not modelled as reducing housing, so the central is zero rather than negative.
- The upper case uses a ceiling from a control-city (placebo) test: 9,420 cities that never repealed, at least 20 stand-ins for each real place, were given the real places' repeal years and run through the same calculation 20,000 times. Their spread, centred on the real average, tops out at +1.49 permits per year per 1,000 existing homes, which agrees with resampling the 76 places (+1.43). Applied to the 2,684,793 Wisconsin homes outside the 9 places that already have no minimums, that gives 19,937 homes over five years.

**Why the upper cases are so different from the centrals.**
- **Parking:** the evidence is centred on zero, so its high end is far from its central.
- **TOD:** the three studies disagree by a factor of about 100, from Los Angeles's 0.055% of station-area homes to Auckland's 5.5%.
- **ADUs:** the upper is almost twice the central (1.9 times: 19,784 ÷ 10,492). It is set at the high end of how much the eight statewide-law states differ from one another; only California has gone higher.

# Which Assumptions Matter Most

| Reform | Assumption | What changing it does (additional homes, 2027–2031) |
| --- | --- | --- |
| Parking | **The ends of the range** | The upper case is the top of the placebo-based range (+1.49). The lower case is the measured average (−1.14), unfloored: −15,326. |
| Parking | **Which places are in the evidence** | Using only the first 24 places studied, the high end is 29,662; combining the 76 places with 185 California cities under AB 2097 gives 15,138; leaving out San Francisco gives 24,520. |
| Parking | **How the range is built** | An earlier placebo version with too few stand-ins for big cities gave +0.95 (12,695); resampling the 76 places gives +1.43 (19,186), close to the adopted 19,937. |
| Parking | **How the comparison cities are cleaned** (improvement loop round 1) | The headline high end (19,937) is the lowest of four versions and may be understated; it is uncertain by about 2×. The other versions: undated reform entries kept as comparisons 29,843; strict cleaning, resampling 38,230; strict cleaning, placebo 49,712. The central stays about zero in every version. Round 2 kept 19,937 (owner); its better-cleaned versions are sensitivities: apartment-scale reforms only 29,307; with California, Oregon and Washington state laws excluded too 27,671. |
| Parking | Counting only buildings of 2 or more units | The high end falls to 10,373. |
| TOD | **Which study sets the size** | Little 171, central 1,181 (drift rule; 798 by the rule set in advance; 2,509 by Stacy et al.), strong 17,148: a hundredfold spread. Within the typical study's own interval the result is 665 to 4,352. |
| TOD | Adjusting each study for the share of its city it covered | Without that adjustment, little is 105 and strong 12,895. |
| TOD | The definition of a major transit stop | Rail and rapid-bus stops only: 716. Twenty-minute buses: 2,813. All 15-minute stops within ½ mile: 3,226. |
| ADUs | **How the law works**: whether it lifts every place toward one common level, as in the eight states, or only multiplies today's low rates | A multiplicative law adds 791; a model fitted on California cities alone adds 2,255; the adopted model adds 10,492. |
| ADUs | **Whether Wisconsin responds like a typical state or like the slowest** | 6,321 (like Rhode Island and Oregon) to 19,784 (strong adoption). |
| ADUs | Whether rural and small-town Wisconsin respond like the model says | At Madison's low minimum rate, the central falls from 10,492 to 5,649. |
| ADUs | The phase-in | Without it, the central rises to 11,585. |
| ADUs | How the comparison states' counts are read (AQ-061, AQ-064, AQ-065, AQ-067) | Without scaling up for towns that did not report, the central is 9,084; with Washington's law years counted from enactment, 9,621; with all three AQ-061 changes undone, 8,402. With every comparison year read against 2020–2024 homes, 10,781; with Maine's reporting share as a share of homes (0.62, not 0.73), 10,724. With the law years coded as before AQ-065 (Vermont by year built, Oregon and Seattle years not yet cut to the state law), 10,593. Massachusetts' 2025 count divided by 11/12 of a year, as before AQ-067, gave 10,615. |
| ADUs | Whether Vermont is a comparison state (its counts are by year built, moved one year earlier since AQ-065; AQ-062) | Left out, the central rises from 10,492 to 10,772 and the upper from 19,784 to 21,540; kept in as adopted. |
| ADUs | Whether Madison follows the statewide model (AQ-066) | On the path of similar cities in Washington and Oregon (before AQ-066), Madison adds 111, not 372. The central falls from 10,492 to 10,231; the upper from 19,784 to 19,159. |

**Can one input flip the ranking?** Yes:
- if parking's high end is taken as the expectation, parking passes the ADU central, with 19,937 homes;
- if TOD follows the strong study, it passes the ADU central;
- if the ADU law only multiplies today's rates, ADUs fall below TOD's former typical case (2,509).

What does *not* move the ADU total much is how we coded local rules. If the 69% of single-family homes in places with uncoded ADU rules behaved like places that ban ADUs, the total with the law would fall by only 0.2%, from 11,278 to 11,256 homes.

# Baselines With No Reform (in progress)

Each scenario's answer is "with the reform minus without it". This table lines up the "without" half for Wisconsin, 2027–2031. The three count different things, so they should nest, not match. Each scenario is testing its baseline with forward and held-out checks (improvement loop, 2026-10-31).

| Scenario | What the baseline counts | In the tool | Tested alternative | Status |
| --- | --- | ---: | ---: | --- |
| Parking | All permitted homes, statewide | 124,000 | 119,703 (boosted trees; owner-approved side case) | Same pace kept as the main rule. It ran 22% low in Wisconsin's 2021–2025; the trees expect some of the recent pace to fade ([NO_REFORM_MODEL_RESULTS.md](parking/NO_REFORM_MODEL_RESULTS.md)) |
| TOD | Homes permitted in station areas | 14,464 | to come | being tested |
| ADUs | ADU permits on single-family lots | 786 | 786 (same pace plus the trend of no-law places; was 530 at today's pace) | Adopted 2026-10-31 (AQ-065). The trend model scored better; it lowers the law's addition by about 233 ([NO_REFORM_R1_RESULTS.md](adu/NO_REFORM_R1_RESULTS.md)) |

- **Nesting checks.** TOD's station-area baseline (14,464) is below the statewide total (124,000): about 12% of it. ADU's 786 is under 1% of the statewide total (0.6%).
- **ADUs need a place-by-place baseline.** A statewide no-law level from other states' cities would give 4,390 ADU permits, about 5.6 times the tool's 786. Those cities are much more active than typical Wisconsin places.

# Net Added Homes, Statewide (in progress)

Owner ask (2026-10-31): permits after each reform minus permits with no reform, Wisconsin, 2027–2031, on the shared all-housing baseline (124,000 homes; 119,379 as published).

| Scenario | Lower | Central | Upper | Central as a share of 124,000 | Source |
| --- | ---: | ---: | ---: | ---: | --- |
| ADUs (ADU permits) | 6,321 | 10,492 | 19,784 | 8.5% | [NET_STATEWIDE_R1.md](adu/NET_STATEWIDE_R1.md) |
| TOD (all homes) | 0 | 1,181 (tool central, AQ-068) | 839–1,382 | 1.0% | [WI_NET_PLAN.md](tod/WI_NET_PLAN.md) (round 4); AQ-068 |
| Parking, route A (the tool) | −15,326 | 0 | 19,937 | 0% | [NET_WI_RESULTS.md](parking/NET_WI_RESULTS.md) |
| Parking, route B (trees) | −4,171 | 0 | 0 | 0% | [NET_WI_RESULTS.md](parking/NET_WI_RESULTS.md) |

- **TOD lower is 0:** homes may only move into station areas from elsewhere, with no net gain.
- **TOD upper 839–1,382:** the calibrated range, with the calibration factor K about 0.11–0.12, measured by leaving each of 9 reform cities out in turn.
- **TOD sensitivities** (the tool is unchanged): with K at the median city's ratio (0.42), about 3,040–4,830; uncalibrated, 7,229–11,505.
- **Parking route B is thin:** it rests on 28 reform places, so it only backs up the central (about zero), not the range.

# What the Tool Cannot Say

- **Whether Wisconsin will behave like the places the evidence comes from.** No Midwest state has data after a statewide ADU law; no state has removed parking minimums long enough to measure; the TOD sizing has no Wisconsin test of its own.
- **Effects after 2031, or late effects.** The parking evidence covers only three years after a repeal, and larger projects may take longer to reach a permit. The TOD studies measure effects three or more years out, so much of a TOD law's effect may come after 2031.
- **The effect of reforms combined.** The three results should not be added up:
  - TOD homes are part of the all-housing count that parking applies to;
  - the ADU law already removes parking requirements for ADUs;
  - the TOD cases cannot separate TOD from parking reform.
  
  The tool shows each reform on its own. Where TOD and parking overlap near transit stops, the tool's combined view takes the larger of the two effects near stops rather than their sum. Over 2027–2031 its low case is −15,155 homes (TOD 171 plus parking −15,326), its central 1,181, and its high case 34,921, with the simple sum, 37,085, shown only as an upper bound.
- **Rents, prices, displacement, parking supply, traffic or transit ridership.** None is modelled.
- **Finished homes.** Permits are not completions, and the figures are not net of demolitions.
- **Local forecasts.** Municipal, county and district figures are shares of a statewide estimate. They reconcile exactly to the state, but they are not forecasts for any place, lot or project.

Two TOD changes await the owner's confirmation (keeping the measured build-up unsmoothed; scaling the suburbs' placement by 0.719). Neither changes the totals above.

**Sources.** `reference/adu_model_statewide.csv`, `adu_model_sensitivities.csv`, `adu_model_reference_lines.csv`, `parking_model_sensitivities.csv`, `tod_model_statewide.csv`, `tod_model_sensitivities.csv`, `housing_baseline_statewide_by_year.csv`; decisions AQ-032 to AQ-051, AQ-061, AQ-064 and AQ-065 in the [assumptions log](ASSUMPTIONS_AND_QUESTIONS.md).
