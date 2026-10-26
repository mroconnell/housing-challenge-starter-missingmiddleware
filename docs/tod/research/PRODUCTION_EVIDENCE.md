# Transit-oriented density: measured evidence on housing production

Written 2026-10-26 for TOD Gate 1 (research question 2, 3 and 5 in [GATE1_PLAN.md](../GATE1_PLAN.md)). Research only: no repo data was analysed. Scratch copies of PDFs read for this note are outside the repo.

**Labels used for every figure.**
- *observed*: from a peer-reviewed paper, a working paper with a stated causal design, or an official government file or report.
- *source_lead*: from news, advocacy, a research organisation summarising a list it did not publish, or an official statement whose method is not published. Use only as a pointer.
- *derived*: arithmetic done for this note from the figures cited next to it.

Each statistic gives its unit, what is counted (numerator), what it is counted against (denominator), and whether it is a count, a rate, a share or an estimated effect.

## Bottom line

1. **Upzoning near transit does not reliably raise permits within five years.** The two US cases closest to the benchmark (Chicago 2013 and 2015, Los Angeles TOC 2017) both found no measurable rise in permitted homes over five to six years. That held even though Los Angeles roughly tripled the number of projects proposed. The large positive effects come from broad, plain upzonings in very strong markets (Auckland 2016, São Paulo 2016, Zurich canton). Those effects took two to five years to appear.
2. **Affordability strings can cancel the effect.** Los Angeles TOC (set-aside required) moved production between programs rather than adding to it. Seattle MHA (set-aside or fee) pushed permits off the upzoned blocks. The benchmark's plain height and FAR increase is closer to Auckland and São Paulo than to Los Angeles or Seattle.
3. **Distance: ½ mile for rail or rapid stations, ¼ mile for frequent bus, is a convention, not a measured decay curve.** No study found here estimates how the permit response to an upzoning falls with distance. Ridership studies support about ½ mile for homes. Recent state laws use ½ mile for rail and ¼ mile for bus, tiered closer in.
4. **Weak markets probably see little or no response.** The Urban Institute's 2025 Washington pro forma finds that mid-rise projects do not pencil out in moderate-rent cities, and that more density can make them less feasible there. The Zurich and Chicago results point the same way. For Wisconsin, Madison is the plausible responder. Milwaukee outside its strongest submarkets, Green Bay and the Fox Cities are likely near zero within 2027 to 2031.

## Ranked summary: usefulness for a Wisconsin TOD model

Rank weighs four things: causal design, match to the benchmark (plain height or FAR increase near transit), market similarity to Wisconsin, and whether we could replicate it from open data.

| Rank | Case | What changed, when | Outcome measured | Headline result | Method | Benchmark match | Replicable from open data | Use in our model |
|---|---|---|---|---|---|---|---|---|
| 1 | Madison TOD overlay (WI) | Overlay adopted 17 Jan 2023: more units and stories as of right, no parking minimums, mostly within ¼ mile of high-capacity routes | City statement only so far | About 40% of new homes since adoption are in the overlay, which is about 17% of city area (source_lead, method not published) | None yet | Good: plain unit and story increases, parking minimums removed, no set-aside | Partly: overlay boundary and permits are in the repo; permits report has no open licence | The only in-state case; our own before/after test |
| 2 | Los Angeles TOC (2017) | ½ mile of major transit stops, tiered density bonus (about 50% to 80%), parking cuts, by-right path, in exchange for affordable units | Proposals, permits, housing stock | Projects proposed citywide rose from 54.7 to 195.6 per quarter; units permitted citywide 2,278 to 2,656 per quarter (descriptive); causal net effect about 562 units over 6 years, about 0.04 percentage points of stock growth (observed) | Border difference-in-differences | Weak to medium: bundled with set-aside and streamlining | Partly: LA permits on city open data portal (licence to check); HCD annual progress reports | Strong-market, rail-and-bus case showing proposals do not equal permits |
| 3 | Auckland Unitary Plan (2016) | About 75% of residential land upzoned, heights and site coverage raised, no set-aside | Dwelling consents (permits) | About 21,808 extra dwellings consented over 2016 to 2021, about 4.1% of the 2016 stock (observed) | Difference-in-differences with set-identified counterfactuals | Medium: plain upzoning, but citywide not transit-specific | Yes: Stats NZ consents (CC BY 4.0); Auckland Council consent and zoning data (licence to check) | Upper bound for a plain upzoning in a very strong market; timing profile |
| 4 | São Paulo transit axes (2014 plan, 2016 zoning) | Max built-area ratio raised along rail and bus corridors (axis zones up to 4.0) | Multifamily permit filings, listings, stock | +66% multifamily permit filings per block at the boundary; long-run stock +1.6% to +1.9% (observed) | Spatial difference-in-discontinuities plus equilibrium model | Good: FAR increase defined by distance to stations and bus corridors | Possibly: GeoSampa city data (not checked) | Best transit-defined causal estimate; gives distance definitions |
| 5 | Chicago TOD ordinances (2013, 2015) | +0.5 to +1.0 FAR and parking cuts within 600 ft to ½ mile of rail | Permitted dwellings, land values | No effect on permitted dwellings over 5 years; land values rose (observed) | Difference-in-differences | Good: FAR plus parking, close to benchmark | Yes: Chicago Data Portal permits (city terms of use) | Midwestern rail city; null short-run result |
| 6 | Washington pro forma (Urban Institute for Commerce, Dec 2025) | Tests HB 1491 densities (2.5 FAR BRT, 3.5 FAR rail) in 12 station areas | Financial feasibility | Feasible only in the highest-rent places; infeasible in Everett, Renton and Spokane; more density can lower feasibility where rents are moderate (observed, modelled) | Pro forma | Direct: models a state TOD law | Model not public; inputs described | Market-strength screen for Wisconsin cities |
| 7 | Seattle MHA (2017, 2019) | Upzoning in 33 neighbourhoods tied to set-aside or fee | Permits | Permitting fell on MHA blocks relative to nearby non-MHA blocks; gap up to 70% of average border permitting (observed, working paper) | Border difference-in-differences | Weak: upzoning bundled with mandate | Yes: Seattle permits open data | Warning on strings attached |
| 8 | Zurich canton (1995 to 2020) | Municipal FAR increases | Housing units and floor space on 100 m cells | +9% units after 5 to 10 years, nothing in years 1 to 4; larger where rents high and zoning binding (observed) | Staggered difference-in-differences | Medium: plain FAR increase, not transit-specific | Paper is CC BY 4.0; data Swiss cantonal | Lag and market-strength modifiers |
| 9 | Vancouver Broadway Plan (2022) | Subway-corridor plan, large height increases | Pipeline by stage | 24,778 units proposed in 126 residential projects by Q3 2025, but 4 projects at building-permit stage and 2 at occupancy (observed) | Descriptive | Good: transit corridor height increase | City memos (PDF) | Shows multi-year lag from proposal to permit |
| 10 | Massachusetts MBTA Communities (2021) | By-right multifamily districts averaging 15 units per acre, mostly near transit | Projects in pipeline | 6,898 units in 102 projects in 34 towns by late 2025, under 1% of about 2 million homes; about one third within ½ mile of a train station (source_lead, state-compiled list) | Descriptive | Medium: density floor by right, district location partly chosen by town | State list via report (licence to check) | Only state TOD-type law with any pipeline data |
| 11 | Minneapolis 2040 (2020) | Citywide triplexes, higher density on transit corridors, parking minimums removed, inclusionary rule | Permits, rents | No measurable supply increase citywide (observed, working paper) | Synthetic control | Weak: bundled citywide package | Yes: Minneapolis Fed dashboard; city permits | Context only |
| 12 | San Diego Complete Communities (2020) | Opt-in FAR bonus in Transit Priority Areas for affordable units plus amenity fee | Affordable units permitted | Affordable units through the program rose from 16 (2021) to 302 (2024) (observed) | Descriptive | Weak: opt-in bonus with set-aside and fee | Yes: city Annual Report on Homes dataset | Context only |
| 13 | Stacy et al. 2023, 1,136 US cities | 180 upzonings and downzonings, 2000 to 2019 | Address counts | Upzonings associated with +0.8% housing supply 3 to 9 years after (observed) | Fixed effects with city trends | Mixed reform types | Partly | General prior for any upzoning |
| 14 | Portland Residential Infill Project (2021) | Fourplexes and more in single-dwelling zones | Permits | 271 middle-housing units and 102 houses permitted in year one (observed, city report) | Descriptive | Not transit | Yes | Not used for TOD |

Not found: rigorous production studies for transit-area zoning in Denver, Atlanta or Toronto (Major Transit Station Areas), for New Zealand's 2022 walkable-catchment rule (NPS-UD Policy 3(c)), or for British Columbia's 2023 Transit-Oriented Areas law. State laws in Colorado (2024), Washington (2025) and California (SB 79, 2025) are too new for permit data.

## Case notes

### 1. Los Angeles Transit Oriented Communities (TOC)

**Citation.** Stephanie Kestelman, "Effects of Transit-Oriented Incentive Programs: Evidence from Los Angeles," Harvard Joint Center for Housing Studies working paper, 1 December 2025. Landing page: https://www.jchs.harvard.edu/research-areas/working-papers/effects-transit-oriented-incentive-programs-evidence-los-angeles. Blog: https://www.jchs.harvard.edu/blog/transit-oriented-incentive-programs-and-multifamily-housing-evidence-los-angeles. Slides (7 Nov 2025): https://www.jchs.harvard.edu/sites/default/files/media-files/2025-11/kestelman_transit-oriented_incentives_slides_jchs.pdf. The jchs.harvard.edu server returns HTTP 403 to automated fetchers, so the working-paper PDF was not read directly. The same analysis is Chapter 1 of her dissertation, which is open access: Kestelman, *Essays on Housing Policy*, Harvard PhD dissertation, May 2025, https://dash.harvard.edu/handle/1/42719786 (PDF via DASH). The figures below are from the dissertation chapter. The working paper's summary figure ("fewer than 560 units over six years") matches the dissertation's 562.01, so the versions agree on the headline.

**What changed.** The TOC guidelines took effect 22 September 2017 under voter-approved Measure JJJ. They apply within ½ mile of "major transit stops": rail stations, and intersections of bus lines with peak headways of 15 minutes or less. Only lots already zoned for multifamily housing qualify, and only projects of 5 or more units. Incentives are tiered by transit type and distance. They include density bonuses (about 50% to 80% more units by tier), FAR increases, parking reductions and a by-right path, in exchange for on-site income-restricted units. Projects with 50 or more units at base density still went through discretionary review. Kestelman reports that 37.8% of parcels in the eligibility zone were zoned multifamily (share of parcels, observed).

**Outcomes and numbers (all observed, Kestelman 2025 unless stated).**
- Projects proposed citywide: average 54.7 projects per quarter before TOC, 195.6 per quarter after (count per quarter, descriptive).
- Projects permitted citywide: 53 per quarter before, 62.1 per quarter after (descriptive).
- Multifamily units permitted citywide: 2,278 units per quarter before, 2,656 per quarter after (descriptive). That is about 9,112 a year before and about 10,624 a year after (derived), a rise of about 17% that is not attributed to TOC.
- Causal design: a border difference-in-differences comparing parcels just inside and just outside ½-mile "Major Transit Areas", split into 2-mile boundary segments, within a 0.5-mile caliper.
  - Units proposed: +27.6 units per year per boundary segment (estimated effect, p < 0.01).
  - Units permitted: no statistically measurable effect.
  - Housing stock: TOC raised the growth rate of the housing stock by 0.04 percentage points, equal to 562 units over 6 years (estimated effect), or about 94 units a year (derived). Against about 10,600 multifamily units permitted citywide a year, that is under 1% (derived).
- Composition: units in mixed-income buildings rose by 2.7 units per year per segment from a baseline of 1.5 (estimated effect, p < 0.05). With no change in total permits, Kestelman reads this as income-restricted units replacing market-rate units.
- Take-up was high: by end of 2023, projects using TOC made up nearly 15% of all units permitted between 2004 and 2023 (share of units, observed). So the null is not low take-up. It is substitution: projects that would have been built anyway, often through California's state density bonus or ordinary zoning, switched to TOC.
- Her stated reasons for the null: the main pipeline of projects reached the permit stage in 2020 to 2022 (COVID-19, then higher interest rates); many applications were early-stage "tier verifications" (42.4% of not-yet-permitted applications against 32.2% of permitted ones, shares of applications); and the 50-unit discretionary threshold.

**Supporting official and academic figures.**
- LA City Planning, Housing Progress Report, July 2018 (observed): in the first 9 months (22 Sep 2017 to 30 Jun 2018), TOC accounted for 5,571 proposed units, 1,145 of them covenanted affordable, and 19% of all units in entitlement filings. https://planning.lacity.gov/odocument/480ec28c-4fde-4714-8590-e689a5fe116c
- LA 2024 Housing Element Annual Progress Report (observed): 37 TOC applications in 2024 with 1,828 units (count of units applied for). https://planning.lacity.gov/odocument/992abaf8-49bb-454f-9a38-3c2af3181fcb/Updated_LosAngeles2024APR.pdf
- Manville, Gray, Phillips and Monkkonen, UC ITS brief, January 2022 (observed): median approval time 434 days for by-right TOC projects against 731 days for discretionary non-TOC projects; with controls, by-right TOC approved 35% faster. https://escholarship.org/uc/item/1cd667p1
- Terner Center inclusionary-zoning paper, April 2024: nearly 50,000 units proposed under TOC, one third of proposed units citywide (source_lead for the count). https://ternercenter.berkeley.edu/wp-content/uploads/2024/04/Inclusionary-Zoning-Paper-April-2024-Final.pdf
- Gabriel and Kung, "Development approval times and new housing supply: Evidence from Los Angeles," *Journal of Urban Economics* (2026), https://doi.org/10.1016/j.jue.2026.103872. A 25% cut in approval times would have raised the 2010 to 2022 production rate by 12.7% (estimated effect, observed). Relevant to the by-right part of a TOD law, not to density itself.

**Benchmark match.** Weak to medium. TOC is a density bonus traded for affordable units, plus streamlining and parking cuts. It is not a plain height or FAR increase. It applies only where multifamily was already allowed.

**Replication data.** City of Los Angeles building permits on data.lacity.org and the City Planning case data (licence to check before use). California HCD annual progress report Table A2 is already in the repo. Kestelman's linked entitlement-to-permit file is not public.

### 2. Auckland Unitary Plan, 2016

**Citation.** Ryan Greenaway-McGrevy and Peter C. B. Phillips, "The impact of upzoning on housing construction in Auckland," *Journal of Urban Economics* 136 (2023) 103555, https://doi.org/10.1016/j.jue.2023.103555. Open preprint: https://eprints.soton.ac.uk/476826/.

**What changed.** The plan became operative 15 November 2016. It upzoned about three quarters of residential land (75.2% by the authors' FAR test) into Terrace Housing and Apartments (five storeys, 50% site coverage), Mixed Housing Urban and Mixed Housing Suburban, from previous single-house zoning. It roughly trebled the dwellings that could be built. There was no affordability requirement.

**Numbers (observed).**
- Attached-dwelling permits in upzoned areas rose from under 1,000 a year in 2016 to near 10,000 a year by 2021 (counts per year, descriptive).
- Spillover-adjusted treatment effects, in extra permits per statistical area per year, for 2016 to 2021: -2.63, 2.34, 6.79, 8.95, 12.09, 18.00. That sums to 45.53 per statistical area. Times 479 statistical areas, it gives 21,808 additional dwellings consented over five years.
- 21,808 is about 4.1% of the 530,300 dwellings in Auckland at end of 2016 (share of stock), or about 4,360 extra consents a year on average (derived), rising each year.
- By zone: 27% of the increase was in Terrace Housing and Apartments, 41% in Mixed Housing Urban, 32% in Mixed Housing Suburban (shares of the estimated increase).
- The result stays statistically significant even if the control areas' counterfactual trend is allowed to be about four times its fitted value.
- A 2022 summary of the working-paper version gave 26,903 extra dwellings, about 5% of stock (source_lead, superseded). A separate synthetic-control paper finds the reform roughly doubled new dwelling permits per capita within five years (Greenaway-McGrevy, EPC working paper 017, https://www.auckland.ac.nz/assets/business/our-research/docs/economic-policy-centre/EPC-WP017.pdf; observed, working paper).

**Transit specifics.** The reform was not a transit rule, but upzoning was concentrated near transport. Greenaway-McGrevy and Jones, "Can zoning reform change urban development patterns? Evidence from Auckland," *Urban Studies* 62(12) (2025), https://ideas.repec.org/a/sae/urbstu/v62y2025i12p2415-2435.html, show:
- the upzoned share of residential land falls off beyond about 6 km of a rapid-transit station;
- after the reform, consents moved closer to rapid-transit stations, highway on-ramps, job centres and the CBD. For example, the median consent moved from 19.9 km to 17.9 km from the CBD (distance, observed);
- the shift came entirely from upzoned areas.

New Zealand's 2020 National Policy Statement on Urban Development, Policy 3(c), requires tier 1 councils to enable at least six storeys within walkable catchments of rapid-transit stops. Guidance treats 400 m as about a five-minute walk and 800 m as about ten minutes (https://environment.govt.nz/assets/Publications/Files/Understanding-and-implementing-intensification-provisions-for-NPS-UD.pdf). Auckland's plan change to do this was delayed, and no production evaluation was found.

**Benchmark match.** Medium. A plain height and coverage increase like the benchmark, but over most of the city rather than near stops. The authors warn that Auckland's latent demand is unusually high and that broad upzoning may lower land prices more than a targeted corridor upzoning would.

**Replication data.** Stats NZ building consents are published under CC BY 4.0. Auckland Council geocoded consents and Unitary Plan zones are on the council open data portal (licence to check).

### 3. São Paulo transit axes, 2014 master plan and 2016 zoning law

**Citation.** Santosh Anagol, Fernando Ferreira and Jonah Rexer, "Estimating the Economic Value of Zoning Reform," *American Economic Journal: Economic Policy*, pp. 235 to 274, https://doi.org/10.1257/pol.20230542. NBER working paper 29440 (revised March 2023): https://www.nber.org/papers/w29440.

**What changed.** Each of about 45,000 city blocks got a maximum built-area ratio (the local term for FAR). The citywide average rose from 1.55 to 2.09, about 36% more allowed floor area. 45% of blocks gained 1.0 or more. The largest increases were in "transformation" zones along the Eixos de Estruturação da Transformação Urbana. Under the 2014 plan these are blocks within 400 m of rail, metro and elevated-guideway stations (extended to blocks reached within 600 m), and within 150 m of bus-corridor axes (extended to 300 m). Gestão Urbana SP: https://gestaourbana.prefeitura.sp.gov.br/estruturacao-territorial/eixos-de-transformacao/localizacao/. Axis zones allow a maximum built-area ratio of 4.0. Building above the basic ratio of 1.0 requires a per-square-metre fee. The 2023 revision (Lei 17.975) widened future axis areas to 700 m around stations and 400 m from bus corridors.

**Numbers (observed).**
- At the boundary, a 1.4-point increase in the maximum built-area ratio raised multifamily permit filings by 0.003 permits per block per quarter, a 66% increase over the control mean (estimated effect).
- No effect on single-family permits.
- The effect appeared about one year after the reform and grew afterwards.
- Housing units listed for sale rose 10% in blocks allowed more density.
- The equilibrium model gives a long-run housing stock increase of 1.6% (published version) or 1.9% (NBER version), and a price fall of 0.4% to 0.5% (estimated effects, citywide).

**Benchmark match.** Good. This is the closest causal match: a FAR increase whose geography is defined by distance to stations and bus corridors, with no set-aside. It differs in market (a megacity) and in the fee for building above the basic ratio.

**Replication data.** Permit and zoning layers from the city's GeoSampa portal (not checked).

### 4. Chicago TOD ordinances, 2013 and 2015

**Citation.** Yonah Freemark, "Upzoning Chicago: Impacts of a Zoning Reform on Property Values and Housing Construction," *Urban Affairs Review* 56(3) (2020), 758 to 789, https://doi.org/10.1177/1078087418824672. Ordinance appendix: https://yonahfreemark.com/wp-content/uploads/2019/09/Freemark-2019-Appendix-Upzoning-Chicago.pdf.

**What changed.**
- 2013 ordinance (11 Sep 2013): lots within 600 ft of rail entrances, or 1,200 ft on designated Pedestrian Streets. Parking up to 50% lower. Business, commercial and downtown lots with FAR 3 could get +0.5 FAR (16.7% more floor area), plus more units per lot and more height.
- 2015 ordinance (24 Sep 2015): ¼ mile of stations, or ½ mile on Pedestrian Streets. Residential parking minimums could be removed entirely. FAR up to 4.0 if on-site affordable units were included. Bonuses granted by administrative adjustment instead of a council rezoning.
- 2019 and 2022 (Connected Communities): extended to frequent bus corridors and a ten-minute walk of every station.

**Numbers (observed).**
- Difference-in-differences on 2010 to 2018 permits and sales: significant increases in transaction values on parcels given more allowed floor area, and higher condominium prices.
- No effect on the number of newly permitted dwellings over five years.
- The City's ETOD appendix counts 150 projects approved to use TOD benefits from 1 Jan 2016 to 6 Feb 2019 (count, official). https://www.chicago.gov/content/dam/city/sites/etod/Pdfs/ETOD-Appendix-C-9-13-20.pdf
- The City's 2022 Connected Communities fact sheet states that 90% of TOD-incentive investment bypassed the South and West sides (share of investment, source_lead because method not published). https://www.chicago.gov/content/dam/city/sites/etod/Pdfs/6-21-22-Connected-Communities-Ordinance.pdf

**Benchmark match.** Good: FAR increase plus parking relief near rail, modest size. Freemark notes five years may be too short to see effects.

**Replication data.** Chicago Data Portal building permits (City terms of use; licence to confirm) and zoning layers.

### 5. Seattle Mandatory Housing Affordability (MHA)

**Citation.** Betty Xiao Wang and Jacob Krimmel, "Upzoning with Strings Attached: Evidence from Seattle's Affordable Housing Mandate," SSRN 4578637 (2023), https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4578637. NYU Furman Center brief: https://www.furmancenter.org/publication/upzoning-with-strings-attached-evidence-from-seattles-affordable-housing-mandate/.

**What changed.** In 2017 and 2019, 33 neighbourhoods (mainly urban villages, many transit-anchored) were upzoned. Every project on an MHA parcel had to provide affordable units or pay a fee, whether or not it used the extra capacity.

**Numbers (observed, working paper).**
- After MHA, an MHA block was 4.8 percentage points less likely to receive a permit in a given year than a non-MHA block (estimated effect). The overall annual chance of a permit per block was about 2.4% (rate).
- At the border, the shift away from MHA blocks could be as large as 70% of average permitting.
- The effect is driven by low-rise multifamily (townhouses, duplexes).
- The study covers only three years, two of them during COVID-19.

**Benchmark match.** Weak (mandate attached). Useful as evidence that a cost attached to an upzoning can outweigh the extra capacity.

**Replication data.** Seattle permits on data.seattle.gov.

### 6. Zurich canton municipal upzonings, 1995 to 2020

**Citation.** Simon Büchler and Elena Lutz, "Making housing affordable? The local effects of relaxing land-use regulation," *Journal of Urban Economics* 143 (2024) 103689, https://doi.org/10.1016/j.jue.2024.103689 (open access, CC BY 4.0).

**Numbers (observed).**
- Upzoned 100 m by 100 m cells gained about 9% more housing units and floor space 5 to 10 years after the FAR increase, relative to cells upzoned later (estimated effect).
- No effect in the first four years.
- Small upzonings: +3% to +5% units after ten years. Large upzonings: +9% to +13%.
- Effects are stronger where the old FAR was fully used and where rents are high.
- 15 years after upzoning, 50% of treated cells had new construction.

**Benchmark match.** Medium: plain FAR increase, not transit-defined. Most useful for timing and for the rule that response grows with rent level and size of upzoning.

### 7. Minneapolis 2040

**What changed.** Adopted Dec 2018, effective 1 Jan 2020. Triplexes allowed citywide, higher densities on transit routes and near METRO stations, parking minimums removed (May 2021), inclusionary zoning for 20 or more units.

**Numbers.**
- Gu and Munro, SSRN 5347083 (2025), synthetic control against 83 cities: price and rent growth fell, but the authors find no new-supply effect and, if anything, slower construction (observed, working paper). https://doi.org/10.2139/ssrn.5347083
- The Minneapolis Fed tracks supply against a 126-city synthetic control (dashboard, observed): https://www.minneapolisfed.org/article/2025/unpacking-supply-and-demand-in-rent-trends-since-the-minneapolis-2040-plan
- Metropolitan Council development-trends reports (descriptive, official):
  - 2009 to 2022: about 52,000 housing units built near high-frequency transit, including 31,600 within ½ mile of light rail, 18,500 within ½ mile of BRT and 13,350 within ¼ mile of high-frequency bus (counts; categories overlap). https://metrocouncil.org/News-Events/Transportation/Newsletters/2023-TOD-report.aspx
  - 2009 to 2024: 39% of regional permitted development value lay along high-frequency transit, on 4% of regional land (shares). https://www.metrotransit.org/TOD-Studies-and-Projects

**Benchmark match.** Weak. Bundled citywide package; transit corridors not separately evaluated.

### 8. San Diego Complete Communities: Housing Solutions

**What changed.** Adopted November 2020 (ordinance O-21275). An opt-in FAR bonus within Transit Priority Areas (½ mile of major transit stops) on sites zoned 20 or more units per acre. Projects must include affordable units and either build public amenities or pay a fee.

**Numbers.**
- Affordable units permitted through the program: 16 in 2021, 302 in 2024; 562 over 2021 to 2024, which is 11.7% of affordable units permitted through city incentive programs (counts and share, observed). San Diego Independent Budget Analyst, 2025: https://www.sandiego.gov/sites/default/files/2025-10/25-35-additional-analysis-of-2025-annual-report-on-homes.pdf
- Citywide, about 8,700 to 8,800 homes were permitted in 2024 (count, official; the report and the mayor's release differ slightly).
- The Mayor's office reported 22 building permits for about 1,600 homes under the program from December 2020 to March 2024 (source_lead). https://www.sandiego.gov/mayor/complete-communities-now

**Benchmark match.** Weak (opt-in bonus with set-aside and fee). No causal study found.

### 9. Vancouver Broadway Plan, and British Columbia Bill 47

The Broadway Plan was adopted June 2022 and took effect September 2022, along the Broadway Subway (opening expected 2027). It allows large height increases near stations. City of Vancouver quarterly memo for Q3 2025 (observed):
- 126 residential projects with 24,778 proposed units, about 90% rental;
- but only 4 projects at building-permit stage and 2 at occupancy, three years after adoption.

https://vancouver.ca/files/cov/2025-11-04-coucil-memo-council-memo-to-mayor-council-broadway-plan.pdf. The city's capacity estimate is 41,500 units over 30 years. This is descriptive, not causal, but it shows the lag between proposals and permits even in a very strong market.

British Columbia's Bill 47 (2023) Transit-Oriented Areas set minimum allowable density and height by distance (see Distance below). No outcome data was found.

### 10. Massachusetts MBTA Communities (Section 3A), 2021

Towns served by the MBTA must zone at least one district allowing multifamily housing by right at an average of at least 15 units per acre, near transit where feasible. Compliance deadlines ran from 2023 to 2025. Amy Dain, *An Early Look at the MBTA Communities Permitting Pipeline*, Boston Indicators, January 2026, https://www.tbf.org/-/media/indicators/boston-indicators-reports/report-files/2026/mbtac_012726_v2.pdf (source_lead: a state-compiled list mixing proposed, permitted and built projects):
- 6,898 units (6,804 net) in 102 projects in 34 of 177 municipalities by late 2025;
- under 1% of the nearly 2 million homes in the 177 municipalities (share);
- just under one third of units within ½ mile of a train station and 57% within 1 mile (shares of units);
- 19 projects of 100 or more units hold 77% of units;
- districts cover slightly more than 1% of land in the 141 towns analysed.

**Benchmark match.** Medium. A by-right density floor, but towns chose where to put the districts, and many put them away from stations.

### 11. Madison, Wisconsin TOD overlay

**Adoption.** Legistar file 74703, ordinance ORD-23-00013. Second substitute adopted by the Common Council 17 January 2023, enacted 26 January 2023. https://madison.legistar.com/LegislationDetail.aspx?ID=5940143&GUID=193488C0-42CA-43A4-8A38-8172CEA0B643. It replaced the placeholder MGO 28.104.

**Geography.** Planning staff report, 17 Nov 2022 (https://madison.legistar.com/View.ashx?GUID=6F2EAD77-F339-4D21-A706-40DD9EF3B97A&ID=11472581&M=F):
- generally within ¼ mile of high-capacity transit routes (the East-West BRT and Metro's primary routes);
- some employment and retail areas between ¼ and ½ mile were added around the BRT termini;
- historic districts, the UW campus and downtown are excluded;
- 6,031 parcel acres in total (official).

The city now describes the overlay as about 17% of the city's area (source_lead). The repo boundary file `data/raw/madison_tod/tod_boundary.geojson` is a single dissolved polygon with Shape.STArea 373,458,954 square feet, about 8,573 gross acres including streets (derived; the file has no CRS tag, so state-plane feet is assumed). That is consistent with 17% of Madison's land area. Rapid Route A (East-West BRT) began service in September 2024 (source_lead), so the first 20 months of the overlay predate BRT service.

**Rules (official staff report, Table 2).** The overlay raises the permitted-use thresholds, so projects up to these sizes no longer need a conditional-use hearing:

| Base zoning | Parcel acres in overlay | Change under the overlay |
|---|---|---|
| Single-family districts | 1,288 | Two-family dwellings permitted |
| SR-V1 | 82 | Up to 12 units permitted (was 8) |
| SR-V2, TR-V2 | 227, 67 | Up to 24 to 36 units, 4 stories as of right |
| TR-U1, TR-U2 | 43, 19 | Up to 36 or 60 units; TR-U2 5 stories |
| NMX | 45 | Mixed-use up to 48 units (was 24), 4 stories |
| TSS | 82 | Mixed-use up to 60 units, 4 stories |
| CC-T | 391 | Mixed-use up to 100 units |
| CC | 628 | 6 stories as of right |
| RMX | 24 | 8 stories as of right |
| TE | 213 | Mixed-use up to 24 units permitted |
| Other districts (no bonus) | 2,267 | Site standards only |

Other rules across the overlay:
- No minimum parking.
- A TOD maximum of 1.5 spaces per multifamily unit (against 2.5 outside the overlay).
- Usable open space requirements removed.
- Two-story minimum for multifamily, mixed-use and employment buildings.
- Maximum setbacks, and no parking between building and street.

**Later changes.** On 28 Oct 2025 the Mayor introduced Legistar 90552 to 90556 to allow four-unit buildings on all residential lots in the overlay and to restrict car-oriented uses (https://www.cityofmadison.com/mayor/priorities/housing-forward/winter-2025-proposals). Final adoption was not verified for this note. Citywide "Housing Forward" changes in 2025 (two units on any single-family lot, and others) are confounders for any before/after test.

**Evidence so far.** The city states that "about 40% of new homes built in Madison since this ordinance was adopted have occurred within the TOD overlay" (share of new homes, source_lead: official statement with no published method or denominator years). No before/after or comparison-area analysis was found. Because the overlay follows corridors where multifamily development already concentrated, this share does not by itself show an effect.

**What an analysis would need (not done here).**
- **Permits.** From the repo's Construction Summary report ([madison_permits.md](../../data-sources/madison_permits.md)), new multifamily is under prefix BLDNCC and small residential under BLDNRC. Units come from the `Textbox13` field. Dates are issue date only, with no application date, so proposals cannot be seen. Rows must be geocoded by address-point matching, as the ADU pipeline does. Reissued permits must be de-duplicated. There is no open licence, so publish only aggregates with citation.
- **Periods.** At least 2015 to 2022 before, and 2023 to the latest full year after. Mark September 2024 (BRT start) and 2025 (Housing Forward) as separate breaks.
- **Treatment.** The overlay boundary (in repo), split by base zoning at January 2023 (city zoning layer, to fetch), so that districts with height or unit bonuses can be separated from the "Other" 2,267 acres with none.
- **Comparison.** Candidates: a ring from ¼ to ½ mile outside the overlay; or corridors with frequent bus service left out of the overlay; or the same corridors in other Dane County municipalities. Each needs a parallel pre-trend check.
- **Approval route.** Plan Commission conditional-use records (Legistar) for multifamily projects inside and outside the overlay, to test whether the overlay moved projects from conditional to permitted use. This is the overlay's main mechanism.
- **Denominators.** Existing homes (2020 census blocks) and parcel acres inside the overlay, so results can be expressed as permits per acre and per existing home.

## Distance threshold: how far does the effect reach?

**No study found measures how the permit response to an upzoning decays with distance from a stop.** The available evidence is indirect.

1. **Ridership catchments.** Guerra, Cervero and Tischler, "Half-Mile Circle: Does It Best Represent Transit Station Catchments?", *Transportation Research Record* 2276 (2012), https://doi.org/10.3141/2276-12, open version https://escholarship.org/uc/item/68r764df. Based on 1,449 rail and BRT stations in 21 US cities (observed):
   - the choice of catchment hardly changes how well ridership is predicted (adjusted R² 0.742 to 0.746 across population radii);
   - the best fit is ½ mile for residents and ¼ mile for jobs;
   - each resident within ¼ mile is associated with 0.338 more weekday trips, against 0.249 within ½ mile (coefficients, trips per resident).
   This supports ½ mile for housing near rail-type stations. It gives no evidence on bus stops.
2. **Land-use change around new rail.** Kim, Houston and others, "Transit Investment Impacts on Land Use Beyond the Half-Mile Mark," UC ITS (2017), https://escholarship.org/uc/item/6cv0d1rs (observed, descriptive and logistic models): in Los Angeles County, land-use change after light-rail openings extended beyond ½ mile, varied by line, and grew a few years after opening. Yang, Su and Cao, *Transport Policy* 99 (2020): in Shenzhen, development intensity responds to metro distance up to a threshold of about 1.25 km (observed). Neither study is about upzoning.
3. **Where projects actually locate in upzoned transit areas.**
   - Massachusetts: about one third of pipeline units are within ½ mile of a train station, 57% within 1 mile (source_lead).
   - Chicago: of 54 completed buildings with on-site affordable units under the city's Affordable Requirements Ordinance, 42.6% were within one block and 68.5% within two blocks of a station (Chicago Cityscape, 2019; source_lead).
   - São Paulo's axes reached 400 to 600 m from stations and 150 to 300 m from bus corridors, and the city widened them to 700 m and 400 m in 2023, reportedly because development capacity was concentrated in too narrow a band (source_lead on motive).
4. **What laws use** (Urban Institute review, Dec 2025, in https://leg.wa.gov/media/q4ypx0bj/tod-phase-ii-final-reports.pdf, Tables 1 and 2):

| Law | Rail or metro | Bus or BRT | Density or height |
|---|---|---|---|
| British Columbia Bill 47 (2023) | 660 ft, ¼ mile, ½ mile tiers for SkyTrain | ¼ mile of bus exchanges | 5 FAR and 20 floors within 660 ft of SkyTrain, falling to 3 FAR and 8 floors at ½ mile |
| California SB 79 (2025) | 200 ft, ¼ mile, ½ mile tiers | Qualifying BRT included | 4.5 FAR and 95 ft near heavy rail, falling to 2.5 FAR and 55 ft at ½ mile from other modes |
| Colorado HB24-1313 (2024) | ½ mile of light and commuter rail | ¼ mile of frequent bus | Average 40 units per acre |
| Washington HB 1491 (2025) | ½ mile of light and commuter rail | ¼ mile of BRT | Average 3.5 FAR near rail, 2.5 FAR near BRT |
| Massachusetts MBTA Communities (2021) | Mostly within ½ mile | Not separately defined | Average 15 units per acre |
| Madison overlay (2023) | None | ¼ mile of high-capacity routes, some areas to ½ mile | See table above |
| Twin Cities reporting convention | ½ mile of LRT and BRT stations | ¼ mile of high-frequency bus | Reporting only |

**Reading for Wisconsin.** All Wisconsin service that could qualify is bus (Madison Route A and B BRT, Milwaukee CONNECT 1, frequent local routes), plus the Milwaukee streetcar and a few Amtrak and Metra stations. The best-supported choice is:
- ¼ mile of BRT stations and of stops on routes with 15-minute or better peak headways;
- ½ mile of rail stations;
- a ½-mile BRT variant as a sensitivity test.

Madison's own overlay uses ¼ mile, which gives an in-state precedent. The lack of measured permit-decay curves should be stated plainly in the model.

## Market strength: does upzoning produce construction in weak or moderate markets?

1. **Washington pro forma.** Freemark, Lo and Su, *The Financial Feasibility of Transit-Oriented Development*, Urban Institute for Washington Commerce, December 2025, bundled at https://leg.wa.gov/media/q4ypx0bj/tod-phase-ii-final-reports.pdf (also https://www.urban.org/sites/default/files/2025-12/Final_The_Financial_Feasibility_of_Transit-Oriented_Development.pdf, which blocks automated download). Observed, modelled, sketch-level, 2025 inputs. A 200-unit prototype was tested at 2.5, 3.5 and 5 FAR in 12 station areas, with 10% of units affordable at 60% of area median income and a 20-year property-tax exemption:
   - projects pencil out in parts of Bellevue, Kirkland, Redmond, Seattle and Vancouver (WA);
   - in Everett, Renton and Spokane, rents are too low for most projects;
   - median tract rents range from under $1,000 a month in Spokane to over $3,000 in the central Puget Sound;
   - construction cost per square foot rises with height: $200 to $275 for 1 to 5 storeys (wood frame), $225 to $285 for 6 to 8 storeys (podium), $300 to $400 for 9 or more storeys;
   - where land and rents are high, more density improves feasibility; where they are low or moderate, taller buildings can reduce feasibility, because the extra cost is not recovered.
   The authors conclude that "communities with low market demand may see no effect" of higher allowed density. They also find that permanent affordability requirements can push developers away from transit areas.
2. **Zurich.** The supply response is larger where rents are high and the old zoning was binding (Büchler and Lutz 2024, observed).
3. **Chicago.** No permit effect in five years (Freemark 2020, observed). The city states that 90% of TOD-incentive investment went to the North and Near West sides, bypassing the South and West sides (source_lead). Inside one city, the incentive worked only where the market was already strong.
4. **Los Angeles.** Even in a very high-rent city, higher interest rates and construction costs from 2022 stopped projects that had approvals (Kestelman 2025, observed).
5. **Auckland.** The authors caution that Auckland's very high latent demand may not carry over to other cities (observed, authors' caveat).
6. **Cross-city prior.** Stacy et al., "Land-use reforms and housing costs," *Urban Studies* (2023), https://doi.org/10.1177/00420980231159500: upzonings in 1,136 cities in 8 metro areas are associated with a 0.8% rise in address counts 3 to 9 years after passage, and no effect in the first two years (estimated association, observed).
7. **Trend near rail.** Housing growth within ½ mile of rail stations in the typical US state rose from 9.7% (2000 to 2010) to 13.7% (2010 to 2020) (percentage growth in units, Urban Institute 2025, observed). Station areas were already gaining share before any state TOD law.

**Reading for Wisconsin.** Wisconsin's Fair Market Rents and new-construction rents are far below the cities where TOD upzoning has produced homes. On these sources:
- Madison is the only Wisconsin market likely to respond in 2027 to 2031, and mainly in 3 to 5 storey wood-frame buildings.
- Milwaukee may respond in its strongest submarkets (downtown edge, East Side, Bay View, Walker's Point).
- Green Bay, the Fox Cities and smaller transit cities are likely near zero.
- Height allowances above about 5 storeys add little where rents cannot cover podium or concrete costs. Removing parking minimums and the conditional-use hearing (Madison's main changes) may matter more than extra height.
- The market screen should be tested on held-out cases, not chosen by hand.

## What this implies for the Wisconsin model (for discussion at Gate 2)

These are suggestions from the evidence above, not estimates.

1. **Use permits, not proposals.** Los Angeles and Vancouver show proposals rising 2 to 4 times while permits stay flat for years. Our outcome (permits at issuance) is the right one, and any proposal-based case should be discounted.
2. **Ramp.** Every positive case shows little or nothing in years 1 to 2 after adoption and growth in years 3 to 5 and beyond (Auckland, São Paulo, Zurich, Stacy et al.). A law starting 1 January 2027 should have most of its 2027 to 2031 effect in 2029 to 2031.
3. **Range of effect sizes from cases.** Cases differ in units, so this is a qualitative ordering, not a pooled rate:
   - zero or negative: Chicago, LA TOC (net), Seattle MHA, Minneapolis;
   - modest: Zurich, +9% units on upzoned cells after 5 to 10 years; Stacy et al., +0.8% citywide stock after 3 to 9 years;
   - large: São Paulo, +66% multifamily filings at the boundary; Auckland, +4.1% of regional stock in 5 years, with attached permits in upzoned areas up about tenfold.
   The large effects come from broad, plain upzonings in megacity or very strong markets.
4. **Scale by market strength.** A low case near zero outside Madison, and a central case where station-area multifamily permits in Madison-like markets rise by a modest share of baseline by year 5, are consistent with the evidence. The share should be calibrated against the Madison before/after test. The Washington pro forma method (required rent premium against local rents) is a transparent way to classify Wisconsin station areas.
5. **Substitution.** Los Angeles and Seattle show much of the "new" activity in transit areas moves from elsewhere in the same city. A statewide net count should not add station-area gains without netting displacement. Auckland's spillover-robust method is the model to follow if we estimate it.

## Leads not verified for this note

- Kestelman's December 2025 working-paper PDF itself (403 to automated fetch). Figures here come from the May 2025 dissertation chapter, which matches the headline.
- The Greenaway-McGrevy and Jones *Urban Studies* article's quantitative effects near rapid-transit stations beyond the descriptive shift.
- Limb and Murray (2022), Brisbane: zoning changes had minimal effect on construction (cited by Greenaway-McGrevy and Phillips; not read).
- Kuhlmann (2021), *Journal of the American Planning Association*: early price effects of Minneapolis 2040 (prices, not permits; not read).
- Santos Nogueira (2025), thesis on developers' response to São Paulo's transit zoning, https://doi.org/10.48683/1926.00125093 (not read).
- Statistics Canada tables 34-10-0298-01 and 34-10-0299-01 (released 14 Aug 2026): housing starts and completions by distance to public transport. Open Canadian data (Statistics Canada Open Licence) that could give a starts-by-distance profile, but not an upzoning effect.
- Auckland Council's NPS-UD plan change (walkable catchments around rapid-transit stops): current status and any consent data.
- Madison Legistar 90552 to 90556: adoption status and final text.
