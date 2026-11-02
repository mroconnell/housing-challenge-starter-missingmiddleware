# Policy Scenario Comparison

Missing Middleware, Wisconsin, 2027–2031. Assembled 2026-10-27 from the three reform sessions' adopted results. Methods and assumptions are in the [Model & Assumptions Overview](MODEL_AND_ASSUMPTIONS.md).

# Scenarios Addressed

The tool compares Wisconsin's current law (the baseline) with three of the five benchmark reforms. Each is modelled as a state law in force from 1 January 2027, and each counts housing units in issued building permits over the five years 2027–2031.

| Reform | The modelled state law | Where it applies | What it counts |
| --- | --- | --- | --- |
| **Accessory dwelling units (ADUs)** | One ADU allowed on every lot with a single-family home, detached or attached, at least 600 square feet, with no extra parking | Every single-family lot in the state (1,839,569 single-family homes) | Second homes added on lots that already have a single-family home |
| **Parking requirement reduction** | No minimum off-street parking may be required for any housing | Every municipality, except the 9 Wisconsin places that have already removed their minimums | All new homes, every building size |
| **Transit-oriented density (TOD)** | Option D, the transit district mandate (AQ-071, 2026-11-02): every city with rail or rapid-bus stops zones a by-right multifamily district (15+ homes per acre) on 15% of the lot acres within ¼ mile of those stops; parking rules unchanged. Replaces the earlier benchmark law (SB 79-style heights on about 71% of the land within ¼ mile) | The district: land within ¼ mile of streetcar and rapid-bus stops (6,394 lot acres; Milwaukee and Dane counties, plus Kenosha). Counted in the station areas: within ½ mile of those stops and ¼ mile of 15-minute bus stops, 313,564 homes (2020 census) | All new homes near those stops |

Missing Middle and development fee reduction are not modelled.

**Comparing the three fairly.** The three reforms count different things against different baselines:
- the ADU baseline is 786 second homes on single-family lots statewide over 2027–2031;
- the parking baseline is 124,000 new homes of all kinds statewide over 2027–2031 (shared baseline v3 final, 2026-11-01; was 122,619);
- the TOD baseline is 14,654 new homes of all kinds near major transit stops over 2027–2031.

So this comparison puts every reform on two common footings:
- **as a share of the all-housing baseline**: additional permits ÷ the 124,000 homes Wisconsin is expected to permit over 2027–2031 under current law;
- **per 1,000 existing homes**: additional permits over 2027–2031 ÷ Wisconsin's 2,778,572 housing units (ACS 2020–2024, table B25002) × 1,000.

The ADU share is an approximate size comparison, not a strict share: the Census permit count behind the 124,000 misses many ADUs, especially those built inside or attached to an existing house.

# Ranking of Results

Additional homes permitted over 2027–2031, compared with current law. Scenarios are named by the evidence they stand for, not by statistical confidence.

| Rank (central) | Reform | Lower | **Central** | Upper | Central, then upper, as a share of the 124,000-home all-housing baseline | Central, then upper, per 1,000 existing homes (five-year total) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | **ADUs** | 6,321 | **10,492** | 19,784 | 8.5%; 16.0% | 3.8; 7.1 |
| 2 | **TOD** | 450 | **8,856** | 11,057 | 7.1%; 8.9% | 3.2; 4.0 |
| 3 | **Parking** | −15,326 | **0** | 19,937 | 0%; 16.1% | 0; 7.2 |

What the scenario names mean:
- **ADUs:** the lower is "sluggish adoption" (the average of Rhode Island and Oregon); the central is "typical adoption"; the upper is "strong adoption", the high end of what states with a statewide ADU law have reached, which only California has passed. If Wisconsin followed the median path the eight statewide-law states actually took, the law would add 10,038 homes.
- **TOD** (option D since AQ-071, 2026-11-02): all three lines come from 11 US places that zoned a district near some of their rail or rapid stops (on average 12% of the land within ¼ mile), measured against similar stops without reform. The central is "the average district place": their mean effect within ¼ mile (32.85 extra homes per 100 lot acres a year) applied to Wisconsin's ¼-mile land, 8,856 (6,715 to 10,624 when each place is left out in turn); no model beat this average on hidden places. The upper is the same scaled to a 15% district, 11,057 (8,053 to 14,836). The lower is the best lot model (lot and place traits), 450 (−121 to 818). The former lines for the broader law (central 13,229, Auckland 17,148, little 43) are kept as what-ifs.
- **Parking:** the central is "no measurable change"; the upper is "the high end of the evidence"; the lower is "the low end of the evidence" (owner, 2026-11-01): the measured average of 76 repeal places against similar places, −1.14 permits per 1,000 existing homes per year, applied without a floor at zero. That is −15,326 homes over 2027–2031, 12.4% below current law (124,000). It is driven mostly by San Francisco and Minneapolis.
- **Median lines.** A "median of real cases" line is shown only where a reform has at least four comparable cases. ADUs (8 states) and parking (76 places) have one. Parking's median place changed by −0.12 permits per year per 1,000 existing homes, so its line is shown at 0, the same as its central. TOD shows none: its central is already the average of the 11 district places (AQ-071), so a separate median line would repeat it.

ADU figures were revised again on 2026-11-01 (AQ-067 in the [assumptions log](ASSUMPTIONS_AND_QUESTIONS.md)): lower 6,321, central 10,492, upper 19,784 on a 786 baseline. Massachusetts' 2025 count is now divided by a full year, because its survey covers January. Earlier that day (AQ-066) they were 6,321, 10,615 and 19,925, when Madison moved onto the statewide model like every other place. Before that they were 6,223, 10,349 and 19,294 on 786 (AQ-065, 2026-10-31), 6,804, 10,679 and 19,535 on 530 (AQ-064, 2026-10-29), 6,734, 10,788 and 20,057 (AQ-061, 2026-10-28), and first 5,538, 8,757 and 16,889 on 605. ADU shares are of the 124,000-home all-housing baseline (central 10,492 ÷ 124,000 = 8.5%; upper 19,784 ÷ 124,000 = 16.0%); per 1,000 existing homes they are ÷ 2,778.572 thousand housing units (central 3.8; upper 7.1).

**Against each reform's own baseline:**
- The ADU central adds 10,492 second homes to a baseline of 786, which is 13.3 times as many as current law would produce.
- The TOD central adds 8,856 homes to a baseline of 14,654 near stops, which is 60.4% more.
- The parking upper adds 19,937 homes to a baseline of 124,000, which is 16.1% more (about 3,987 a year).

**How confident we are.**

| Reform | Confidence in the central | Why |
| --- | --- | --- |
| ADUs | Medium | Eight states have passed similar laws. When each is left out, the model predicts five of the seven non-California states within about 15%; it is about 21% too high for Washington and 19% too high for Vermont. No Midwest state has data yet. |
| TOD | Low | The central averages 11 US places that chose their own district land, often land builders wanted; none is in Wisconsin, and a state mandate may do less. No model beat that average on places it had not seen. |
| Parking | Medium that the effect is small within five years; low on the high end | 76 real repeals show no measurable rise on average within three years. |

**The ranking depends on the scenario.** On the central scenarios the order is ADUs (10,492), then TOD (8,856), then parking (0). On the upper scenarios parking (19,937) is just ahead of ADUs (19,784), then TOD (11,057). The gap is 153 homes: 0.8% of parking's 19,937. So the top two are close to tied on the upper scenarios. (Before AQ-071, TOD's central of 13,229 for the broader law ranked first.)

# What Drives the Differences

**ADUs add the most in the central scenario because the law creates a right on almost 1.84 million lots where today very few owners build one.**
- At today's pace Wisconsin would permit 530 second homes on single-family lots over five years. That is 0.06 permits per 1,000 single-family homes per year.
- The tool's baseline also rises 7.3% a year, as ADU permits did in places with no statewide law. That gives 786 over 2027–2031, or 0.09 permits per 1,000 single-family homes per year (AQ-065).
- In the eight states with a statewide ADU law, a typical place reached about 1.1 permits per 1,000 single-family homes per year once the law had been in force four years.
- The model applies that rate to Wisconsin's 1,839,569 single-family homes, phased in (about 68% of the full effect in 2027, 85% in 2028 and all of it from 2029). It spreads the statewide total across places by home value alone: a place with 10% higher home values gets about a 10% higher rate.

**TOD's central rests on the average of 11 places that zoned a transit district.**
- The law (option D, AQ-071): every city with rail or rapid stops zones a by-right apartment district on 15% of the land within ¼ mile of them.
- Near the 11 places' reform stops, building within ¼ mile rose by about 32.85 extra homes per 100 lot acres a year, against similar stops without reform.
- Applied to Wisconsin's 4,874 lot acres within ¼ mile of rail and rapid stops in Milwaukee and Madison, for 5 years, and scaled to the state (×1.106): 8,856 extra homes over 2027–2031 (range 6,715 to 10,624).
- The places' districts averaged 12% of that land; scaled to the law's 15%, 11,057 (the upper).
- Land beyond ¼ mile counts zero: no rule beat zero there on hidden places.
- Homes are placed by each place's lot acres within ¼ mile of rail and rapid stops (the district is spread at random over that land).
- Caveat: the training cities chose their land, often land builders already wanted; a mandate may do less.
- The former central for the broader law (13,229, AQ-070) and the earlier ones (Stacy et al. 2,509; drift rule 1,196) are kept as what-ifs.

**Parking's central is zero because the 76 US places that removed their parking minimums did not permit measurably more homes in the next three years than similar places that kept them.**
- The places removed minimums between 2017 and 2022. They were drawn from 46 places that adopted repeals in 2015–2022, each checked against its ordinance.
- Each place's permits per 1,000 existing homes in up to five years before the repeal (from 2012) were compared with years 1–3 after it, against similar places in the same state that kept their minimums (a difference-in-differences).
- Weighted by each place's number of homes, the average change was −1.14 permits per year per 1,000 existing homes (all housing units, ACS 2020–2024 table B25002). The 90% range was −3.47 to +1.43, which includes zero.
- In plain words, developers in those places kept building about as much parking as buyers, renters and lenders wanted. In Buffalo, the developers of 36 major projects still built 79% of the spaces the old minimums had required. So where a minimum did not force more parking than the market wanted, removing it changed little.
- The law is not modelled as reducing housing, so the central is zero rather than negative.
- The upper case uses a ceiling from a control-city (placebo) test: 9,420 cities that never repealed, at least 20 stand-ins for each real place, were given the real places' repeal years and run through the same calculation 20,000 times. Their spread, centred on the real average, tops out at +1.49 permits per year per 1,000 existing homes, which agrees with resampling the 76 places (+1.43). Applied to the 2,684,793 Wisconsin homes outside the 9 places that already have no minimums, that gives 19,937 homes over five years.

**Why the upper cases are so different from the centrals.**
- **Parking:** the evidence is centred on zero, so its high end is far from its central.
- **TOD:** the upper only scales the central from the places' 12% districts to the law's 15% (11,057 ÷ 8,856 = 1.25 times).
- **ADUs:** the upper is almost twice the central (1.9 times: 19,784 ÷ 10,492). It is set at the high end of how much the eight statewide-law states differ from one another; only California has gone higher.

# Which Assumptions Matter Most

| Reform | Assumption | What changing it does (additional homes, 2027–2031) |
| --- | --- | --- |
| Parking | **The ends of the range** | The upper case is the top of the placebo-based range (+1.49). The lower case is the measured average (−1.14), unfloored: −15,326. |
| Parking | **Which places are in the evidence** | Using only the first 24 places studied, the high end is 29,662; combining the 76 places with 185 California cities under AB 2097 gives 15,138; leaving out San Francisco gives 24,520. |
| Parking | **How the range is built** | An earlier placebo version with too few stand-ins for big cities gave +0.95 (12,695); resampling the 76 places gives +1.43 (19,186), close to the adopted 19,937. |
| Parking | **How the comparison cities are cleaned** (improvement loop round 1) | The headline high end (19,937) is the lowest of four versions and may be understated; it is uncertain by about 2×. The other versions: undated reform entries kept as comparisons 29,843; strict cleaning, resampling 38,230; strict cleaning, placebo 49,712. The central stays about zero in every version. Round 2 kept 19,937 (owner); its better-cleaned versions are sensitivities: apartment-scale reforms only 29,307; with California, Oregon and Washington state laws excluded too 27,671. |
| Parking | Counting only buildings of 2 or more units | The high end falls to 10,373. |
| TOD | **Which law, and which line** (AQ-071) | Option D: little 450 (−121 to 818), central 8,856 (6,715 to 10,624), strong 11,057 (8,053 to 14,836), each range with one place left out. The former lines for the broader law: little 43, central 13,229, strong (Auckland) 17,148; earlier: Los Angeles 171, drift rule 1,196, Stacy et al. 2,509. |
| TOD | District size: the places' 12% or the law's 15% | 8,856 unscaled (central) or 11,057 scaled (upper). |
| TOD | Where homes land | By ¼-mile land (adopted): Milwaukee metro 3,018, Madison metro 5,471 (central). By the broader law's added floor area: 5,778 and 2,919. Totals unchanged. |
| TOD | The definition of a major transit stop | The law's addition does not change (the district is tied to rail and rapid stops). Current law near stops does: 6,206 (rail and rapid only), 14,654 (main), 15,984 (20-minute buses), 18,676 (all 15-minute stops within ½ mile). |
| ADUs | **How the law works**: whether it lifts every place toward one common level, as in the eight states, or only multiplies today's low rates | A multiplicative law adds 791; a model fitted on California cities alone adds 2,255; the adopted model adds 10,492. |
| ADUs | **Whether Wisconsin responds like a typical state or like the slowest** | 6,321 (like Rhode Island and Oregon) to 19,784 (strong adoption). |
| ADUs | Whether rural and small-town Wisconsin respond like the model says | At Madison's low minimum rate, the central falls from 10,492 to 5,649. |
| ADUs | The phase-in | Without it, the central rises to 11,585. |
| ADUs | How the comparison states' counts are read (AQ-061, AQ-064, AQ-065, AQ-067) | Without scaling up for towns that did not report, the central is 9,084; with Washington's law years counted from enactment, 9,621; with all three AQ-061 changes undone, 8,402. With every comparison year read against 2020–2024 homes, 10,781; with Maine's reporting share as a share of homes (0.62, not 0.73), 10,724. With the law years coded as before AQ-065 (Vermont by year built, Oregon and Seattle years not yet cut to the state law), 10,593. Massachusetts' 2025 count divided by 11/12 of a year, as before AQ-067, gave 10,615. |
| ADUs | Whether Vermont is a comparison state (its counts are by year built, moved one year earlier since AQ-065; AQ-062) | Left out, the central rises from 10,492 to 10,772 and the upper from 19,784 to 21,540; kept in as adopted. |
| ADUs | Whether Madison follows the statewide model (AQ-066) | On the path of similar cities in Washington and Oregon (before AQ-066), Madison adds 111, not 372. The central falls from 10,492 to 10,231; the upper from 19,784 to 19,159. |

**Can one input flip the ranking?** Yes:
- if parking's high end is taken as the expectation, parking passes the ADU central, with 19,937 homes;
- TOD's upper (11,057) passes the ADU central (10,492); the former central for the broader law (13,229) would too;
- if the ADU law only multiplies today's rates (791), ADUs fall below TOD's central (8,856), though they stay above TOD's lower (450).

What does *not* move the ADU total much is how we coded local rules. If the 69% of single-family homes in places with uncoded ADU rules behaved like places that ban ADUs, the total with the law would fall by only 0.2%, from 11,278 to 11,256 homes.

# Baselines With No Reform (in progress)

Each scenario's answer is "with the reform minus without it". This table lines up the "without" half for Wisconsin, 2027–2031. The three count different things, so they should nest, not match. Each scenario is testing its baseline with forward and held-out checks (improvement loop, 2026-10-31).

| Scenario | What the baseline counts | In the tool | Tested alternative | Status |
| --- | --- | ---: | ---: | --- |
| Parking | All permitted homes, statewide | 124,000 | 119,750 (boosted trees; owner-approved side case) | Same pace kept as the main rule. It ran 22% low in Wisconsin's 2021–2025; the trees expect some of the recent pace to fade ([NO_REFORM_MODEL_RESULTS.md](parking/NO_REFORM_MODEL_RESULTS.md)) |
| TOD | Homes permitted in station areas | 14,654 (range 8,495–22,161) | 18,558 (re-based; not adopted) | On shared baseline v3 |
| ADUs | ADU permits on single-family lots | 786 | 786 (same pace plus the trend of no-law places; was 530 at today's pace) | Adopted 2026-10-31 (AQ-065). The trend model scored better; it lowers the law's addition by about 233 ([NO_REFORM_R1_RESULTS.md](adu/NO_REFORM_R1_RESULTS.md)) |

- **Nesting checks.** TOD's station-area baseline (14,654) is below the statewide total (124,000): about 12% of it. ADU's 786 is under 1% of the statewide total (0.6%).
- **ADUs need a place-by-place baseline.** A statewide no-law level from other states' cities would give 4,390 ADU permits, about 5.6 times the tool's 786. Those cities are much more active than typical Wisconsin places.

# Net Added Homes, Statewide (in progress)

Owner ask (2026-10-31): permits after each reform minus permits with no reform, Wisconsin, 2027–2031, on the shared all-housing baseline (124,000 homes; 119,379 as published).

| Scenario | Lower | Central | Upper | Central as a share of 124,000 | Source |
| --- | ---: | ---: | ---: | ---: | --- |
| ADUs (ADU permits) | 6,321 | 10,492 | 19,784 | 8.5% | [NET_STATEWIDE_R1.md](adu/NET_STATEWIDE_R1.md) |
| TOD (all homes) | 450 (−121 to 818) | 8,856 (6,715–10,624) | 11,057 (8,053–14,836) | 7.1% | [OPTION_D_PLAN.md](tod/OPTION_D_PLAN.md); AQ-071 |
| Parking, route A (the tool) | −15,326 | 0 | 19,937 | 0% | [NET_WI_RESULTS.md](parking/NET_WI_RESULTS.md) |
| Parking, route B (trees) | −4,171 | 0 | 0 | 0% | [NET_WI_RESULTS.md](parking/NET_WI_RESULTS.md) |

- **TOD lines now match the tool** (AQ-071, option D): lower = best lot model (lot and place traits); central = the 11 district places' average within ¼ mile; upper = the same scaled to a 15% district. The former lines (43, 13,229, Auckland 17,148; AQ-069, AQ-070) are what-ifs.
- **Earlier TOD net figures** (WI_NET_PLAN.md round 4, kept for the record): calibrated 839–1,382; with K at the median city's ratio (0.42) about 3,040–4,830; uncalibrated 7,229–11,505; the drift-rule central 1,196 (AQ-068) is now a what-if.
- **Parking route B is thin:** it rests on 28 reform places, so it only backs up the central (about zero), not the range.

# What the Tool Cannot Say

- **Whether Wisconsin will behave like the places the evidence comes from.** No Midwest state has data after a statewide ADU law; no state has removed parking minimums long enough to measure; the TOD sizing has no Wisconsin test of its own.
- **Effects after 2031, or late effects.** The parking evidence covers only three years after a repeal, and larger projects may take longer to reach a permit. The TOD places' effects build up over several years, so much of a TOD law's effect may come after 2031.
- **The effect of reforms combined.** The three results should not be added up:
  - TOD homes are part of the all-housing count that parking applies to;
  - the ADU law already removes parking requirements for ADUs;
  - the TOD cases cannot separate TOD from parking reform.
  
  The tool shows each reform on its own. Where TOD and parking overlap near transit stops, the tool's combined view takes the larger of the two effects near stops rather than their sum. Over 2027–2031 its low case is −14,877 homes (TOD 450 plus parking −15,326), its central 8,856, and its high case 29,046, with the simple sum, 30,994, shown only as an upper bound (before AQ-071: −15,283, 13,229 and 34,921; sum 37,085).
- **Rents, prices, displacement, parking supply, traffic or transit ridership.** None is modelled.
- **Finished homes.** Permits are not completions, and the figures are not net of demolitions.
- **Local forecasts.** Municipal, county and district figures are shares of a statewide estimate. They reconcile exactly to the state, but they are not forecasts for any place, lot or project.

One TOD change awaits the owner's confirmation (keeping the measured build-up unsmoothed); it does not change the totals above. The suburbs' 0.719 placement scaling no longer applies: since AQ-071 homes are placed by land within ¼ mile of rail and rapid stops.

**Sources.** `reference/adu_model_statewide.csv`, `adu_model_sensitivities.csv`, `adu_model_reference_lines.csv`, `parking_model_sensitivities.csv`, `tod_model_statewide.csv`, `tod_model_sensitivities.csv`, `housing_baseline_statewide_by_year.csv`; decisions AQ-032 to AQ-051, AQ-061, AQ-064, AQ-065 and AQ-071 in the [assumptions log](ASSUMPTIONS_AND_QUESTIONS.md).
