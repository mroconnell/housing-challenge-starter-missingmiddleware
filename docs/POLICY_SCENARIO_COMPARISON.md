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
- the parking baseline is 124,000 new homes of all kinds statewide over 2027–2031; its range is 56,500 to 218,865 homes (aims at 90%; shared baseline v4; central unchanged from v3). It held 12 of 12 Wisconsin checks and 88.3% of other-state checks for 2009–2020, a window chosen after the results. It missed the 2005–08 run-up to the crash, like every method tested. Only the statewide total was tested.
- the TOD baseline is 14,654 new homes of all kinds near major transit stops over 2027–2031.

So this comparison puts every reform on two common footings:
- **as a share of the all-housing baseline**: additional permits ÷ the 124,000 homes Wisconsin is expected to permit over 2027–2031 under current law;
- **per 1,000 existing homes**: additional permits over 2027–2031 ÷ Wisconsin's 2,778,572 housing units (ACS 2020–2024, table B25002) × 1,000.

The ADU share is an approximate size comparison, not a strict share: the Census permit count behind the 124,000 misses many ADUs, especially those built inside or attached to an existing house.

# Results: 90% Ranges

Extra homes permitted over 2027–2031, compared with current law. ADUs and TOD show only their 90% range (uniform display, owner 2026-11-05, ADUs and TOD: "both"; parking follows when the owner finishes it; [UNIFORM_DISPLAY_SPEC.md](UNIFORM_DISPLAY_SPEC.md)). The reforms are listed in a fixed order, not ranked. No single number stands for a reform's result. The side lines below the table give context.

| Reform | 90% range, extra homes, 2027–2031 | Low and high as a share of the 124,000-home all-housing baseline | Low and high per 1,000 existing homes (five-year total) | How the range is built | Coverage |
| --- | --- | ---: | ---: | --- | --- |
| **ADUs** (ADU permits: second homes on single-family lots) | 8,055 to 13,666 | 6.5% to 11.0% of the 124,000 all-housing baseline (not of the 786 ADU baseline) | 2.9 to 4.9 | Held-out prediction error: how far the model missed each of 7 statewide-law states it had not seen (root mean square log error 0.136 × t at 6 degrees of freedom, 1.943) | Checked on 7 states: 7 of 7 inside; too few to measure a factor, so not widened |
| **TOD** | 3,922 to 16,335 | 3.2% to 13.2% | 1.4 to 5.9 | Bootstrap of the 11 district places (4,866 to 15,361), widened ×1.1827 | 84.5% before widening |
| **Parking** | Not yet on the range display (owner still working on parking). Current lines: low end −15,380, central 0, high end 19,649 | −12.4%, 0%, 15.8% | −5.5, 0, 7.1 | Low end: measured average of 74 repeal places; high end: placebo spread | Not checked against real outcomes |

- **ADUs: law-side error only.** The range leaves out Wisconsin-side inputs:
  - today's rates where they are assumed. 74% of the addition is in such places; the codings tested move the result from 9,319 to 10,734.
  - how the with-law level is spread across places.

**Side lines (context, never the result).**

| Reform | Side line | Extra homes, 2027–2031 |
| --- | --- | ---: |
| ADUs | Typical adoption (the former central) | 10,492 |
| ADUs | Median path of the 8 statewide-law states | 10,038 |
| ADUs | Like Rhode Island and Oregon, the 2 slowest statewide-law states | 6,321 |
| ADUs | High end, near California (only California is higher; outside the range) | 19,784 |
| TOD | Average district place, 11 places (the former central) | 10,028 |
| TOD | Edge test, the rezoned lots' own gain (5 places) | 3,958 |
| TOD | Average scaled to a 15% district (11 places) | 12,521 |
| TOD | Rezoning near new transit lines, 2×2 (9 places) | 13,451 |
| TOD | The same, minus the growth already under way before the reforms | 5,624 |

What the side lines mean:
- **ADUs.**
  - Typical adoption is the model's level for a typical statewide-law state.
  - The 8-state median follows the path the eight statewide-law states actually took.
  - Rhode Island and Oregon are the two slowest.
  - California alone has gone above the high end.
- **TOD** (option D since AQ-071; lines AQ-072, AQ-075). The law zones a district on 15% of the land within ¼ mile of rail and rapid stops.
  - The average district place: 11 US places zoned a district near some of their rail or rapid stops, on average on 12% of the land within ¼ mile. Their mean effect within ¼ mile was 33.54 extra homes per 100 lot acres a year. Applied to Wisconsin's ¼-mile land, that gives 10,028.
  - The edge test counts only the rezoned lots' own gain: lots just inside a district boundary against lots just outside.
  - Scaled to 15%, the average gives 12,521.
  - The 2×2 failed the fake-years check, so it is also shown with its before-reform growth taken out.
  - Statewide scale (owner, 2026-11-02): all lot acres within ¼ mile of rail and rapid stops ÷ those in Milwaukee and Madison cities, 6,394 ÷ 5,212 = 1.227.
- **Parking** side lines follow when parking moves to the range display.

**Against each reform's own baseline:**
- ADUs: 8,055 to 13,666 second homes on a baseline of 786. That is 10.2 to 17.4 times what current law would produce.
- TOD: 3,922 to 16,335 homes on a baseline of 14,654 near stops. That is 26.8% to 111.5% more.
- Parking (current lines): −15,380 to 19,649 homes on a baseline of 124,000, central 0. That is −12.4% to +15.8%.

**How confident we are.**

| Reform | Confidence | Why |
| --- | --- | --- |
| ADUs | Medium | Eight states have passed similar laws. When each is left out, the model predicts five of the seven non-California states within about 15%; it is about 21% too high for Washington and 19% too high for Vermont. No Midwest state has data yet. |
| TOD | Low | The central averages 11 US places that chose their own district land, often land builders wanted; none is in Wisconsin, and a state mandate may do less. No model beat that average on places it had not seen. |
| Parking | Medium that the effect is small within five years; low on the high end | 74 real repeals show no measurable rise on average within three years. |

The reforms are not ranked (rule 8 of the display spec). The ADU and TOD 90% ranges overlap: ADUs 8,055 to 13,666, TOD 3,922 to 16,335.

# What Drives the Differences

**ADUs add the most in the central scenario because the law creates a right on almost 1.84 million lots where today very few owners build one.**
- At today's pace Wisconsin would permit 530 second homes on single-family lots over five years. That is 0.06 permits per 1,000 single-family homes per year.
- The tool's baseline also rises 7.3% a year, as ADU permits did in places with no statewide law. That gives 786 over 2027–2031, or 0.09 permits per 1,000 single-family homes per year (AQ-065).
- In the eight states with a statewide ADU law, a typical place reached about 1.1 permits per 1,000 single-family homes per year once the law had been in force four years.
- The model applies that rate to Wisconsin's 1,839,569 single-family homes, phased in (about 68% of the full effect in 2027, 85% in 2028 and all of it from 2029). It spreads the statewide total across places by home value alone: a place with 10% higher home values gets about a 10% higher rate.

**TOD's central rests on the average of 11 places that zoned a transit district.**
- The law (option D, AQ-071): every city with rail or rapid stops zones a by-right apartment district on 15% of the land within ¼ mile of them.
- Near the 11 places' reform stops, building within ¼ mile rose by about 33.54 extra homes per 100 lot acres a year, against similar stops without reform.
- Applied to Wisconsin's 4,874 lot acres within ¼ mile of rail and rapid stops in Milwaukee and Madison, for 5 years, and scaled to the state by its share of that land (×1.227): 10,028 extra homes over 2027–2031 (range 7,580 to 12,010).
- The places' districts averaged 12% of that land. Scaled to the law's 15%, 12,521 (the former upper, now a what-if). Districts of 10% and 25% give 8,347 and 20,868.
- The lower, 3,958, counts only the rezoned lots' own gain (edge test, 5 places). The upper, 12,521, is the 11-place average scaled to a 15% district.
- These results describe districts, not citywide upzoning: for the 5 broad upzonings left out (BelRed, Honolulu, Los Angeles TOC, San Diego, Chicago 2022; measured −13.3 to +29.4 per 100 lot acres a year), the average rule missed by a median 42.9, the scaled rule by 240, and zero by 10.6.
- Land beyond ¼ mile counts zero: no rule beat zero there on hidden places.
- Homes are placed by each place's lot acres within ¼ mile of rail and rapid stops (the district is spread at random over that land).
- Caveat: the training cities chose their land, often land builders already wanted; a mandate may do less.
- The former central for the broader law (13,229 as shown; 13,686 on the corrected data; AQ-070) and the earlier ones (Stacy et al. 2,509; drift rule 1,196) are kept as what-ifs.

**Parking's central is zero because the 74 US places that removed their parking minimums did not permit measurably more homes in the next three years than similar places that kept them.**
- The places removed minimums between 2017 and 2022. They were drawn from 46 places that adopted repeals in 2015–2022, each checked against its ordinance.
- Each place's permits per 1,000 existing homes in up to five years before the repeal (from 2012) were compared with years 1–3 after it, against similar places in the same state that kept their minimums (a difference-in-differences).
- Weighted by each place's number of homes, the average change was −1.15 permits per year per 1,000 existing homes (all housing units, ACS 2020–2024 table B25002). The 90% range was −3.63 to +1.45, which includes zero. The sample was corrected on 2026-11-05 (Canandaigua's town series, Seabrook and Maumee removed; owner OK), from 76 places.
- In plain words, developers in those places kept building about as much parking as buyers, renters and lenders wanted. In Buffalo, the developers of 36 major projects still built 79% of the spaces the old minimums had required. So where a minimum did not force more parking than the market wanted, removing it changed little.
- The central is zero ("no measurable change"). There is no floor at zero: the low end applies the measured average, −1.15, and gives −15,380 homes.
- The upper case uses a ceiling from a control-city (placebo) test: 9,185 cities that never repealed, at least 20 stand-ins for each real place, were given the real places' repeal years and run through the same calculation 20,000 times. Their spread, centred on the real average, tops out at +1.47 permits per year per 1,000 existing homes, which agrees with resampling the 74 places (+1.45). Applied to the 2,668,677 Wisconsin homes outside the 18 places left out (9 that already have no minimums and 9 near-benchmark places), that gives 19,649 homes over five years.

**Why the ranges differ in width.**
- **TOD:** 11 places is a small sample, and the range is widened to pass its coverage test.
- **ADUs:** the model missed hidden states by a typical 14%. The range covers that error only.

# Which Assumptions Matter Most

Figures in this section are the former centrals and lines under each change. They show what moves, not the result.

| Reform | Assumption | What changing it does (additional homes, 2027–2031) |
| --- | --- | --- |
| Parking | **The ends of the range** | The upper case is the top of the placebo-based range (+1.47). The lower case is the measured average (−1.15), unfloored: −15,380. |
| Parking | **Which places are in the evidence** | Using only the first 24 places studied, the high end is 29,662; combining the 76 places (before the 74-place correction) with 185 California cities under AB 2097 gives 15,138; leaving out San Francisco gives 24,520. |
| Parking | **How the range is built** | An earlier placebo version with too few stand-ins for big cities gave +0.95 (12,695); resampling the 74 places gives +1.45 (19,328), close to the adopted 19,649. |
| Parking | **How the comparison cities are cleaned** (improvement loop round 1) | The headline high end (19,818 then; 19,649 on the 74-place sample) is the lowest of four versions and may be understated; it is uncertain by about 2×. The other versions: undated reform entries kept as comparisons 29,843; strict cleaning, resampling 38,230; strict cleaning, placebo 49,712. The central stays about zero in every version. Round 2 kept the headline high end (then 19,937; 19,818 after Stage 2) (owner); its better-cleaned versions are sensitivities: apartment-scale reforms only 29,307; with California, Oregon and Washington state laws excluded too 27,671. |
| Parking | Counting only buildings of 2 or more units | The high end falls to 10,373. |
| TOD | **Which law, and which line** (AQ-071, AQ-072) | Option D: lower 3,958 (90% range 2,280 to 5,791), central 10,028 (7,580 to 12,010, each place left out), upper 12,521 (9,089 to 16,771, each place left out), AQ-075. What-ifs: the 2×2 near new lines 13,451 (10,431 to 15,049); the 2×2 minus its before-reform growth 5,624 (2,340 to 9,684); former option D lower 824 (−90 to 1,006). The former lines for the broader law, recomputed on the corrected data: little −70 (shown as 43), central 13,686 (shown as 13,229), strong (Auckland) 17,148; earlier: Los Angeles 171, drift rule 1,196, Stacy et al. 2,509. |
| TOD | District size | 10,028 unscaled (central; the places averaged 12%) or 12,521 scaled to 15% (the upper, AQ-075). Scaled to 10%: 8,347; to 25%: 20,868. A straight line through the places at 15%: 8,143. |
| TOD | Where homes land | By ¼-mile land (adopted): Milwaukee metro 3,417, Madison metro 6,195 (central). By the broader law's added floor area: 6,408 and 3,238. Totals unchanged. |
| TOD | The definition of a major transit stop | The law's addition does not change (the district is tied to rail and rapid stops). Current law near stops does: 6,206 (rail and rapid only), 14,654 (main), 15,984 (20-minute buses), 18,676 (all 15-minute stops within ½ mile). |
| ADUs | **How the law works**: whether it lifts every place toward one common level, as in the eight states, or only multiplies today's low rates | A multiplicative law adds 791; a model fitted on California cities alone adds 2,255; the adopted model adds 10,492. |
| ADUs | **Whether Wisconsin responds like a typical state or like the slowest** | 6,321 (like Rhode Island and Oregon) to 19,784 (strong adoption). |
| ADUs | Whether rural and small-town Wisconsin respond like the model says | At Madison's low minimum rate, the central falls from 10,492 to 5,649. |
| ADUs | The phase-in | Without it, the central rises to 11,585. |
| ADUs | How the comparison states' counts are read (AQ-061, AQ-064, AQ-065, AQ-067) | Without scaling up for towns that did not report, the central is 9,084; with Washington's law years counted from enactment, 9,621; with all three AQ-061 changes undone, 8,402. With every comparison year read against 2020–2024 homes, 10,781; with Maine's reporting share as a share of homes (0.62, not 0.73), 10,724. With the law years coded as before AQ-065 (Vermont by year built, Oregon and Seattle years not yet cut to the state law), 10,593. Massachusetts' 2025 count divided by 11/12 of a year, as before AQ-067, gave 10,615. |
| ADUs | Whether Vermont is a comparison state (its counts are by year built, moved one year earlier since AQ-065; AQ-062) | Left out, the central rises from 10,492 to 10,772 and the upper from 19,784 to 21,540; kept in as adopted. |
| ADUs | Whether Madison follows the statewide model (AQ-066) | On the path of similar cities in Washington and Oregon (before AQ-066), Madison adds 111, not 372. The central falls from 10,492 to 10,231; the upper from 19,784 to 19,159. |

What does *not* move the ADU total much is how we coded local rules. If the 69% of single-family homes in places with uncoded ADU rules behaved like places that ban ADUs, the total with the law would fall by only 0.2%, from 11,278 to 11,256 homes.

# Baselines With No Reform (in progress)

Each scenario's answer is "with the reform minus without it". This table lines up the "without" half for Wisconsin, 2027–2031. The three count different things, so they should nest, not match. Each scenario is testing its baseline with forward and held-out checks (improvement loop, 2026-10-31).

| Scenario | What the baseline counts | In the tool | Tested alternative | Status |
| --- | --- | ---: | ---: | --- |
| Parking | All permitted homes, statewide | 124,000 | 119,750 (boosted trees; owner-approved side case) | Same pace kept as the main rule. It ran 22% low in Wisconsin's 2021–2025; the trees expect some of the recent pace to fade ([NO_REFORM_MODEL_RESULTS.md](parking/NO_REFORM_MODEL_RESULTS.md)) |
| TOD | Homes permitted in station areas | 14,654; range 6,677 to 25,865 (v4 statewide pair applied to this area; aims at 90% for the state total, not tested for this area) | 18,558 (re-based; not adopted) | On shared baseline v4 |
| ADUs | ADU permits on single-family lots | 786 | 786 (same pace plus the trend of no-law places; was 530 at today's pace) | Adopted 2026-10-31 (AQ-065). The trend model scored better; it lowers the law's addition by about 233 ([NO_REFORM_R1_RESULTS.md](adu/NO_REFORM_R1_RESULTS.md)) |

- **Nesting checks.** TOD's station-area baseline (14,654) is below the statewide total (124,000): about 12% of it. ADU's 786 is under 1% of the statewide total (0.6%).
- **ADUs need a place-by-place baseline.** A statewide no-law level from other states' cities would give 4,390 ADU permits, about 5.6 times the tool's 786. Those cities are much more active than typical Wisconsin places.

# Net Added Homes, Statewide (in progress)

Owner ask (2026-10-31): permits after each reform minus permits with no reform, Wisconsin, 2027–2031, on the shared all-housing baseline (124,000 homes; 119,379 as published).

| Scenario | 90% range | Former lines (lower, central, upper) | Source |
| --- | --- | --- | --- |
| ADUs (ADU permits) | 8,055 to 13,666 | 6,321; 10,492; 19,784 | [NET_STATEWIDE_R1.md](adu/NET_STATEWIDE_R1.md); [CAUSAL_FRAMEWORK_RESULTS.md](adu/CAUSAL_FRAMEWORK_RESULTS.md) |
| TOD (all homes) | 3,922 to 16,335 | 3,958; 10,028; 12,521 | [OPTION_D_PLAN.md](tod/OPTION_D_PLAN.md); [CAUSAL_FRAMEWORK_PLAN.md](tod/CAUSAL_FRAMEWORK_PLAN.md); AQ-071, AQ-072, AQ-075 |
| Parking, route A (the tool) | not yet (owner still working on parking) | −15,380; 0; 19,649 | [NET_WI_RESULTS.md](parking/NET_WI_RESULTS.md) |
| Parking, route B (trees) | not computed | −4,171; 0; 0 | [NET_WI_RESULTS.md](parking/NET_WI_RESULTS.md) |

- **TOD lines now match the tool** (AQ-072, option D): lower = edge test, the rezoned lots' own gain; central = the 11 district places' average within ¼ mile; upper = the central scaled to a 15% district (AQ-075). The 2×2 near new lines (13,451) and its trend-adjusted version (5,624) are what-ifs, as are the former option D lower (824; AQ-071) and the earlier lines (43, 13,229, Auckland 17,148 as shown; AQ-069, AQ-070) are what-ifs.
- **Earlier TOD net figures** (WI_NET_PLAN.md round 4, kept for the record): calibrated 839–1,382; with K at the median city's ratio (0.42) about 3,040–4,830; uncalibrated 7,229–11,505; the drift-rule central 1,196 (AQ-068) is now a what-if.
- **Parking route B is thin:** it rests on 28 reform places, so it only backs up the central (about zero), not the range.

# What the Tool Cannot Say

- **Whether Wisconsin will behave like the places the evidence comes from.** No Midwest state has data after a statewide ADU law; no state has removed parking minimums long enough to measure; the TOD sizing has no Wisconsin test of its own.
- **Effects after 2031, or late effects.** The parking evidence covers only three years after a repeal, and larger projects may take longer to reach a permit. The TOD places' effects build up over several years, so much of a TOD law's effect may come after 2031.
- **The effect of reforms combined.** The three results should not be added up:
  - TOD homes are part of the all-housing count that parking applies to;
  - the ADU law already removes parking requirements for ADUs;
  - the TOD cases cannot separate TOD from parking reform.
  
  The tool shows each reform on its own. The combined TOD and parking view stays as it is until parking moves to the range display. Then it will show a range from a paired simulation of the reforms' draws, never a sum of range ends. Its current lines (rebuilt on the 74-place parking sample, combined-56ea544b03): where TOD and parking overlap near transit stops, it takes the larger of the two effects near stops rather than their sum. Over 2027–2031 its low case is −11,422 homes (TOD 3,958 plus parking −15,380), its central 10,028, and its high case 30,202. The simple sum, 32,170, is only an upper bound (on the 76-place sample: −11,276, 10,028 and 30,355; sum 32,338) (before AQ-071: −15,283, 13,229 and 34,921; sum 37,085).
- **Rents, prices, displacement, parking supply, traffic or transit ridership.** None is modelled.
- **Finished homes.** Permits are not completions, and the figures are not net of demolitions.
- **Local forecasts.** Municipal, county and district figures are shares of a statewide estimate. They reconcile exactly to the state, but they are not forecasts for any place, lot or project.

One TOD change awaits the owner's confirmation (keeping the measured build-up unsmoothed); it does not change the totals above. The suburbs' 0.719 placement scaling no longer applies: since AQ-071 homes are placed by land within ¼ mile of rail and rapid stops.

**Sources.** `reference/adu_model_statewide.csv`, `adu_model_sensitivities.csv`, `adu_model_reference_lines.csv`, `parking_model_sensitivities.csv`, `tod_model_statewide.csv`, `tod_model_sensitivities.csv`, `housing_baseline_statewide_by_year.csv`; decisions AQ-032 to AQ-051, AQ-061, AQ-064, AQ-065 and AQ-071 in the [assumptions log](ASSUMPTIONS_AND_QUESTIONS.md).
