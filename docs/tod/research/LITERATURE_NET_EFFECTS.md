# Why upzonings add many homes in some places and few in others, and how much is borrowed

Written 2026-10-27 for the TOD thread, after the owner asked two questions:

1. Why do upzonings near transit add many homes in some places and almost none in others?
2. How much of a local gain is building moved from nearby, rather than new homes?

It reads alongside [PRODUCTION_EVIDENCE.md](PRODUCTION_EVIDENCE.md) (the case-by-case evidence), [NET_EFFECT_SOURCES.md](NET_EFFECT_SOURCES.md) (the check of the three borrowed net-effect figures), [TRAITS_RESULTS.md](../TRAITS_RESULTS.md) (our finding that no single local trait predicts held-out cities) and [NET_EFFECT_PLAN.md](../NET_EFFECT_PLAN.md) (our planned borrowing test). Research only: no repo data was analysed for this note.

**Labels used for every figure** (the same as in PRODUCTION_EVIDENCE.md).
- *observed*: from a peer-reviewed paper, a working paper with a stated causal design, or an official file.
- *source_lead*: from a summary, blog or report whose method is not published, or a figure not checked against the original. A pointer only.
- *derived*: arithmetic done for this note from the figures cited next to it.

Each statistic gives its unit, what is counted, what it is counted against, and the kind of number (count, share, rate or estimated effect).

## Answer first

1. **Borrowing from next door is small in the studies that measured it closely.** Four studies that compared upzoned land with a ring of unchanged land just outside it found no measurable loss in the ring. Two found a small *gain* there: New York (Liao 2026, Peng 2023), São Paulo (Anagol, Ferreira and Rexer), and Zurich (Büchler and Lutz 2024).
2. **Where borrowing was found, it travelled far, not next door.** In Auckland, the upzoning pulled building from distant areas with spare vacant land, not from the blocks next door. The naive gap (upzoned minus not upzoned) was about 1.6 times the net figure (34,614 against 21,808 permits, derived). In Lower Hutt, the point estimate is that about 38% of the extra permits came from other towns in the Wellington region. That figure was not statistically significant.
3. **Strings also move building.** Seattle's upzoning with an affordability mandate pushed permits onto nearby blocks without the mandate. Los Angeles TOC moved projects between programs rather than adding projects.
4. **What decides whether an upzoning builds homes, in order of how well it is supported:**
   - whether the old limit actually held building back (binding zoning);
   - market strength (rents high enough to pay for the new building type);
   - the size of the upzoning;
   - how much of the city is upzoned at once (wide reforms beat spot upzonings);
   - time (little in years 1 to 3);
   - the building cycle (interest rates, tax-abatement deadlines);
   - by-right approval;
   - land that is easy to redevelop (vacant, industrial, large lots).
   Transit quality and network coverage have almost no direct evidence either way.
5. **These factors interact.** A large upzoning on land that was already built to its limit, in a high-rent area, responds strongly. Remove any one of the three and the response shrinks towards zero. That is one plausible reason why single traits, tested one at a time, did not predict our held-out cities.
6. **Two more citywide net figures can be added to Los Angeles, Stacy et al. and Auckland:**
   - New York (Peng 2023, model-based): +0.7% of the city's housing in the long run;
   - São Paulo (Anagol et al., model-based): +1.6% of the city's housing in the long run.
   There are also two Auckland updates and one Lower Hutt metro figure (table in section 4).

## Summary table

| Study | Place, reform | Design | Sample | Headline (unit, kind) | Borrowing / spillover finding | Bears on |
| --- | --- | --- | --- | --- | --- | --- |
| Liao 2026, *Regional Science and Urban Economics* | New York, neighbourhood upzonings 2004 to 2013 | Parcel difference-in-differences (DiD), upzoned land against a 1,000 ft ring outside; plus rings at 0 to 1,000, 1,000 to 2,000 and 2,000 to 3,000 ft | Parcel panel of rezoned areas | Residential units +4% after 7 years; +8% on parcels with the largest capacity increase (estimated effects, % of units on treated parcels) | Inner ring gained slightly, not significant: "positive but limited spillover". So no borrowing from next door. | Q1, Q2 |
| Peng 2023, Penn job-market paper | New York, Bloomberg rezonings 2002 to 2013, floor area added equal to 5% of city housing | Ring DiD plus dynamic spatial model | Granular NYC parcel panel | Long-run citywide housing supply +0.7% (model counterfactual) | Positive spillovers to surrounding areas, delayed | Q1, Q3, Q4 |
| Su, Curran-Groome and Freemark 2026, Urban Institute | New York (7 neighbourhood upzonings), Philadelphia (2012 code) | Propensity-matched comparison areas, event study | NYC parcels (PLUTO); Philadelphia block faces | NYC: about 4,100 extra units in 4 years; Philadelphia: up to about 4,000 extra unit permits a year (estimated effects) | Not measured; authors say they cannot yet tell whether gains were substitutive | Q2, Q4 |
| Anagol, Ferreira and Rexer, *AEJ: Economic Policy* | São Paulo 2016, built-area ratio raised along transit axes | Spatial boundary discontinuity plus equilibrium model | About 45,000 blocks | +66% multifamily permit filings at the boundary; long-run city stock +1.6% (published) or +1.9% (NBER) | No sign that control blocks near the boundary lost permits; "minimal substitution" | Q1, Q4 |
| Greenaway-McGrevy and Phillips 2023, *JUE* | Auckland 2016, about 75% of residential land | DiD with a bound on displacement from control-area trends | 479 statistical areas | +21,808 permits 2016 to 2021, 4.11% of 530,300 dwellings (net) | Displacement came over long distances from areas with more vacant land; naive gap 34,614 | Q1, Q3, Q4 |
| Greenaway-McGrevy 2023, EPC WP 015 | Auckland, update to 2022 | As above, wider control group (rural and business zones) | As above | At least 27,000 extra permits by 2022, 5.11% of stock | Wider control lets housing displace business and rural building; author calls it a lower bound | Q4 |
| Greenaway-McGrevy 2025, EPC WP 017 | Auckland | Synthetic control against other NZ cities | NZ commuting zones | 52,200 extra permits 2017 to 2023, 46% of 112,300 issued | Net of any shifts inside Auckland by design | Q3, Q4 |
| Maltman and Greenaway-McGrevy 2025, *J. Housing Economics* | Lower Hutt (NZ), about 80% of residential land upzoned from late 2010s | Synthetic control for Lower Hutt and for each neighbouring town | Wellington region towns | Starts about tripled; region-wide +9.5% to +18.2% | Point estimate: 1,157 of 3,006 extra Lower Hutt consents (38%) displaced from neighbours; not significant | Q1, Q3, Q4 |
| Büchler and Lutz 2024, *JUE* | Zurich canton, municipal FAR increases 1995 to 2020 | Staggered DiD on 100 m cells | 168 municipalities | +9% units after 5 to 10 years; +30% where zoning was binding vs +2% to +7% where not | No spillover for most upzonings; large ones +5% on neighbouring cells after 15 years (weak) | Q1, Q2 |
| Wang and Krimmel 2023, SSRN working paper | Seattle MHA 2017 and 2019 | Border DiD | Seattle blocks | MHA blocks 4.8 points less likely to get a permit per year | Permits shifted to non-MHA blocks, up to 70% of average border permitting | Q1 |
| Kestelman 2025, Harvard JCHS | Los Angeles TOC 2017 | Border DiD | ½-mile boundary segments | +2.02% stock locally over 6 years; +0.04 points citywide | Projects switched program; border estimate counts building pulled from just outside | Q1, Q4 |
| Freemark 2023, *J. Planning Literature* | Review | Review of all peer-reviewed English studies to spring 2023 | All studies found | Long run: small increases in upzoned areas | "Initial evidence" of no substitution elsewhere | Q1, Q2 |
| Murray and Limb 2023, *Urban Policy and Research* | Brisbane, 19 activity centres around transit, 1996 to 2016 | Site panel, regressions | 25,775 sites within 1,200 m of the main transit node | 2% of zoned capacity used in any 5-year period; 78% of sites with capacity stayed undeveloped | Not measured | Q2, Q3 |
| Dong 2024, *JPER* (online 2021) | Portland 2000 to 2017 | Propensity-matched parcels, survival models | Upzoned and matched parcels | Upzoning raised development probability, density and units, most on vacant or underused parcels | Not measured | Q2 |
| Gabbe 2018, *JPER*; 2019, *JAPA* | Los Angeles 2002 to 2016 | Parcel logit; policy review | About 780,000 parcels | 1.1% of land area upzoned 2002 to 2014 | Not measured; upzoning went where resistance was low | Q2 |
| Kuhlmann 2021, *JAPA* | Minneapolis 2040 | Border DiD on sale prices | Houses within 3 km of the city border | Prices of affected houses +3% to +5% | Prices, not building | Q2 |
| Kulka, Sood and Chiumenti 2022, Boston Fed WP | Greater Boston | Boundary discontinuity at zoning lines | Lot-level zoning | Relaxing density limits raises supply; height or use changes alone do little | Not measured | Q2 |
| Brooks and Lutz 2016, *AEJ: Economic Policy* | Los Angeles County 1999 to 2011 | Repeat sales of parcels | 2.3 million parcels | Land sold for assembly carries a 15% to 40% premium | n/a | Q2 |
| Baum-Snow 2023, *J. Economic Perspectives* | US tracts | Review with tract supply elasticities | US census tracts | Median tract supply elasticity 0.15 in metros over 5 million, 0.44 under 500,000 | n/a | Q2, Q3 |
| Greenaway-McGrevy and So 2026, *Economic Inquiry* | Auckland rents | Synthetic control | NZ urban areas | Rents 23% lower by 2024 than the counterfactual; starts per head more than doubled | n/a | Q3 |

---

## 1. Borrowing: is local building moved from nearby?

There are two kinds of design. They give different answers, and the difference matters for our plan.

### 1a. Ring studies: compare upzoned land with land just outside

**Liao 2026, New York.** Hsi-Ling Liao, "The effect of rezoning on local housing supply and demand: Evidence from New York City," *Regional Science and Urban Economics* 117 (2026) 104188. https://doi.org/10.1016/j.regsciurbeco.2025.104188. Open working-paper version: https://papers.hsilingliao.com/Upzoning_Liao_JMP.pdf (SSRN 4886140).
- **Design and sample.** Parcel-level DiD of the 2004 to 2013 neighbourhood upzonings. Upzoned parcels are compared with parcels within 1,000 ft outside the boundary, with census-tract fixed effects.
- **Main result** (observed). Residential units on upzoned parcels rose by more than 4% after seven years (estimated effect, % of units). Parcels with the largest capacity increase gained 8%. Effects became significant only two to three years after upzoning.
- **Borrowing test** (observed). Rings at 0 to 1,000 ft and 1,000 to 2,000 ft were compared with an outer ring at 2,000 to 3,000 ft.
  - The inner ring gained units slightly, not significant at 95%.
  - So the ring did not lose building. The author reads the main estimate as a lower bound of the local effect.
- **Bearing.** This is the closest published design to our [NET_EFFECT_PLAN.md](../NET_EFFECT_PLAN.md) borrowing test (treatment, ¼-mile ring, far land). It found no next-door borrowing in one of our fitted cities. The author warns that the result is "hyper-local", not the city-wide effect.

**Peng 2023, New York.** Xuequan Elsie Peng, "The Dynamics of Urban Development: Evidence from Zoning Reform in New York," University of Pennsylvania job-market paper, 2023 (working paper). https://penniur.upenn.edu/publications/the-dynamics-of-urban-development-evidence-from-land-use-reform-in-new-york and https://sites.google.com/view/elsiepeng.
- **Design.** A spatial ring design, then a dynamic spatial model fitted to the data.
- **Findings** (observed, abstract):
  - the Bloomberg reform added floorspace allowance equal to 5% of the city's housing stock;
  - supply responded slowly;
  - new building had *positive* spillovers on surrounding areas, delayed by the slow supply response;
  - in the model, the reform raises the city's total housing supply by 0.7% in the long run;
  - high redevelopment costs erode 67% of the policy's potential effect on new development.
- **Secondary report** (source_lead, Jason Barr's blog summary, https://buildingtheskyline.org/upzoning-1/): blocks compared with blocks within 650 m. Units rose about 4% after 6 years and about 8% after 12. Small upzonings (FAR up under 30%) gave about 2% after 10 years; large ones (over 92%) about 8%. Not checked against the paper.

**Anagol, Ferreira and Rexer, São Paulo.** "Estimating the Economic Value of Zoning Reform," *American Economic Journal: Economic Policy*, https://doi.org/10.1257/pol.20230542. NBER WP 29440, https://www.nber.org/papers/w29440.
- **Borrowing test** (observed, section 5.3 of the NBER version). Both treated and control blocks near a boundary were compared with "pure control" blocks more than 0.5 km away, following Diamond and McQuade (2019).
  - Control blocks near treated blocks did not have lower permit counts.
  - Treated blocks near and far from the boundary responded alike.
  - The authors conclude there was minimal substitution of projects from control to treatment blocks.

**Büchler and Lutz 2024, Zurich.** "Making housing affordable? The local effects of relaxing land-use regulation," *Journal of Urban Economics* 143, 103689. https://doi.org/10.1016/j.jue.2024.103689 (open access).
- **Spillovers** (observed, section 4.3 and 5): most upzonings had no effect on neighbouring non-upzoned cells. Large upzonings had a weak positive spillover of about +5% living space and units after 15 years, significant only in one estimator.
- The authors explain positive spillovers by owners holding several adjacent cells, and by owners redeveloping when nearby new buildings are denser.

**Kestelman 2025, Los Angeles TOC** (checked in [NET_EFFECT_SOURCES.md](NET_EFFECT_SOURCES.md)).
- The border estimate is +2.02% of stock on the treated side over six years. The citywide figure is 0.04 percentage points (observed).
- The gap is so large partly because TOC projects replaced projects that would have used other programs (the state density bonus, ordinary zoning). That is substitution between programs, not between places.

**Wang and Krimmel 2023, Seattle MHA.** "Upzoning with Strings Attached," SSRN 4578637, https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4578637 (working paper).
- Building moved *out* of the upzoned blocks to nearby blocks without the mandate. The shift was up to 70% of average border permitting (observed).
- Mainly low-rise multifamily (townhouses, duplexes). This is borrowing in the other direction, caused by the cost attached to the upzoning.

### 1b. Wide-area studies: compare the whole city or region with a counterfactual

**Greenaway-McGrevy and Phillips 2023, Auckland.** *JUE* 136, 103555, https://doi.org/10.1016/j.jue.2023.103555.
- **Displacement travelled far** (observed). The authors say the evidence "suggests that upzoning in Auckland reallocated permits over large distances": from distant areas with more vacant land to nearer areas with less. Methods that assume spillovers fade with distance were judged untenable.
- **Their fix.** They extrapolate the pre-reform trend in non-upzoned areas as the counterfactual. Anything below that trend after 2016 is treated as displaced.
- **Size of the adjustment.**
  - Unadjusted gap 2016 to 2021: 34,614 permits. Adjusted, net: 21,808 (observed).
  - The naive gap is 1.59 times the net (derived, 34,614 ÷ 21,808).
  - In this framework a displaced permit is counted twice in the naive gap: once as a gain inside, once as a loss outside. The correction is the naive gap minus twice the displacement (stated in Greenaway-McGrevy 2023, WP 015, section 2.1). On that reading about 6,400 permits were displaced: (34,614 − 21,808) ÷ 2 (derived). That is about 23% of the roughly 28,200 extra permits inside upzoned areas (derived, 6,403 ÷ 28,211). This decomposition is ours, not the paper's.
- **Robustness.** The 2021 effect stays significant unless the counterfactual allows more than about four times the trend rise in non-upzoned permits (published version) (observed).

**Maltman and Greenaway-McGrevy 2025, Lower Hutt.** "Going it alone: The impact of upzoning on housing construction in Lower Hutt," *Journal of Housing Economics* 67 (2025) 102032, https://doi.org/10.1016/j.jhe.2024.102032. Working paper: https://www.auckland.ac.nz/assets/business/about/our-research/documents/WP-018.pdf.
- **Reform.** Lower Hutt, one town in the Wellington region, upzoned about 80% of its residential land in steps from the late 2010s, on its own.
- **Effect** (observed): consents per head about tripled, and starts nearly tripled, over six years, against a synthetic control.
- **Borrowing test.** Each neighbouring town got its own synthetic control.
  - Over 2018 to 2023, Wellington City fell 920 consents below its counterfactual, Kāpiti Coast 407, Upper Hutt 18; Porirua was 126 above.
  - Net deficit across the four: 1,157 consents (observed).
  - Against Lower Hutt's 3,006 extra consents, that is 38% (observed, author's arithmetic): "roughly two out of every five" extra consents may have displaced one elsewhere.
  - None of these deficits is statistically significant. Wellington City's shortfall overlaps a COVID-era population fall of 1.5% (2020 to 2022).
- **Region-wide net:** +1,848 consents. That is +12.6% on the region's counterfactual consents with point-estimate displacement, +18.2% with none, and +9.5% with the pooled spillover estimate (observed). Denominator: consents in the five Wellington-region towns, 16,501 over six years. Not housing stock.

**Su, Curran-Groome and Freemark 2026, New York and Philadelphia.** "How Big Upzonings Affect Housing Supply," Urban Institute, April 2026. https://www.urban.org/research/publication/how-big-upzonings-affect-housing-supply (PDF: https://www.urban.org/sites/default/files/2026-04/How%20Big%20Upzonings%20Affect%20Housing%20Supply.pdf).
- The authors state that more research is needed to know whether the effects were "primarily substitutive" (observed). No borrowing estimate.
- Philadelphia: the citywide upzoning did not shift *where* developers applied for permits. Upzoned areas got more units per project, not more projects.

**Freemark 2023 review.** Yonah Freemark, "Zoning change: Upzonings, downzonings, and their impacts on residential construction, housing costs, and neighborhood demographics," *Journal of Planning Literature* 38(4) (2023), https://doi.org/10.1177/08854122231166961. Summary page: https://www.urban.org/research/publication/zoning-change.
- **Short run:** mixed. Some studies find no rise in construction, others significant rises.
- **Long run:** small increases in upzoned areas, with "initial evidence" that this does not substitute for construction elsewhere (source_lead for the exact wording, from the summary page).
- **Caveat:** most studies cover small upzonings.

### 1c. What the two designs together say

- **Next-door borrowing is small or negative.** The ring designs in New York, São Paulo and Zurich find the unchanged land just outside either unaffected or slightly *better* off. Neighbours seem to build a little more when the area is improving, not less.
- **Regional borrowing can be real.** Auckland and (possibly) Lower Hutt show building pulled from far away: areas with spare greenfield land, or other towns. This is invisible to a ring design.
- **Strings move building next door.** Seattle MHA, and LA TOC between programs.
- **Reading for our plan.** A ¼-mile ring that shows no loss would match the literature. It would not show that the local gain is all new. The far land (¼ to 1½ miles) may itself be where building came from.

---

## 2. What predicts whether an upzoning produces construction

### 2a. Whether the old limit was binding

- **Büchler and Lutz 2024, Zurich** (observed). Among large upzonings (FAR up more than 30.7%):
  - cells already built to the old limit (897 cells) gained about 30% more housing after 15 years;
  - cells not built to the limit (2,523 cells) gained only about 2% to 7%, not significantly different from zero.
  - Binding was measured as built floors equal to the allowed maximum before the change.
- **Murray and Limb 2023, Brisbane** (observed). Mark Limb and Cameron K. Murray, "We zoned for density and got higher house prices: Supply and price effects of upzoning over 20 years," *Urban Policy and Research* 41(2), https://doi.org/10.1080/08111146.2022.2124966. Open copy: https://eprints.qut.edu.au/235371/.
  - Sample: 25,775 sites within 1,200 m walk of the main transit node in 19 activity centres, 1996 to 2016.
  - Dwellings rose from 36,000 to 47,000. Zoned spare capacity rose from about 33,000 to 66,000 extra dwellings.
  - Only 2% of zoned capacity was used in any five-year period (share of capacity).
  - 78% of sites with capacity in the first period stayed undeveloped (share of sites).
  - The authors argue capacity was not binding. Adding more could not raise building.
- **Liao 2026, New York** (observed). Parcels inside upzoned districts whose allowed capacity did not rise showed no price gain. The housing gain was concentrated on parcels with the largest capacity increase.
- **Kulka, Sood and Chiumenti, Greater Boston** (observed). "How to Increase Housing Affordability: Understanding Local Deterrents to Building Multifamily Housing," Boston Fed WP 22-10, https://www.bostonfed.org/-/media/Documents/Workingpapers/PDF/2022/wp2210.pdf.
  - Relaxing density limits (minimum lot size, maximum units) raises supply.
  - Allowing multifamily, or raising height alone, has little effect on units built.
  - The constraint that binds is the one that matters.

### 2b. Market strength

- **Zurich** (observed). Ten years after upzoning, housing rose about 23% to 25% in above-median-rent cells against 8% to 9% in below-median ones. The difference is not statistically significant.
- **New York and Philadelphia** (observed, Su et al. 2026).
  - Jerome Avenue in the Bronx, the upzoned area with the slowest rent growth before, showed no significant gain.
  - Gowanus, high and rising rents on former industrial land, showed the largest gain.
  - In Philadelphia, areas with little demand before the reform did not attract projects after it.
- **New York** (observed, Liao). Price gains on upzoned parcels were concentrated in the central city "where demand may be higher".
- **Chicago, Washington pro forma, Los Angeles:** see [PRODUCTION_EVIDENCE.md](PRODUCTION_EVIDENCE.md) section "Market strength".
- **Kuhlmann 2021, Minneapolis** (observed). "Upzoning and Single-Family Housing Prices," *JAPA* 87(3), 383 to 395, https://doi.org/10.1080/01944363.2020.1852101.
  - Affected houses rose 3% to 5% in price within a year of the 2040 plan, against houses in neighbouring cities within 3 km.
  - Larger in inexpensive neighbourhoods and on small lots.
  - So the market priced in a redevelopment option. Price gains alone do not mean building follows.

### 2c. Size of the upzoning

- **Zurich** (observed). Median FAR increase was 30.6%. Small upzonings gave +3% to +5% units after ten years; large ones +9% to +13%.
- **New York** (source_lead, Barr's summary of Peng). About 2% after 10 years for FAR increases under 30%; about 8% for increases over 92%.
- **Our own test:** added FAR had a positive slope on all fitting units (+1.76 homes per acre per year per added FAR) but did not travel to held-out cities ([TRAITS_RESULTS.md](../TRAITS_RESULTS.md)).

### 2d. Sites: vacancy, size and assembly

- **Dong, Portland** (observed). Hongwei Dong, "Exploring the Impacts of Zoning and Upzoning on Housing Development: A Quasi-experimental Analysis at the Parcel Level," *Journal of Planning Education and Research* 44(1) (2024), 403 to 415 (online 2021), https://doi.org/10.1177/0739456X21990728.
  - Upzoned parcels were more likely to be developed, at higher density, than matched parcels, 2000 to 2017.
  - The effect was strongest on vacant and underused parcels.
  - A blog summary gives 240 homes on 111 upzoned parcels against 8 on 58 matched parcels (source_lead, not checked).
- **Brooks and Lutz 2016, Los Angeles County** (observed). "From Today's City to Tomorrow's City: An Empirical Investigation of Urban Land Assembly," *AEJ: Economic Policy* 8(3), 69 to 105, https://doi.org/10.1257/pol.20130399.
  - Land sold to be assembled with neighbours trades at a 15% to 40% premium over other land (estimated premium, share of price).
  - Holdouts make assembly costly. Small lots under separate owners respond less.
- **Baum-Snow 2023** (observed). "Constraints on City and Neighborhood Growth: The Central Role of Housing Supply," *Journal of Economic Perspectives* 37(2), 53 to 74, https://doi.org/10.1257/jep.37.2.53.
  - The median census tract's housing supply elasticity is 0.15 in metros of 5 million or more, rising to 0.44 in metros under 500,000 (elasticity, % change in units per % change in price).
  - Dense, built-up tracts are least elastic, partly because of land assembly.
- **Auckland** (observed). Displaced building came from areas with *more* vacant land. Greenfield land competes with upzoned infill.
- **Our own test:** the vacant, parking or industrial share failed as a single trait ([TRAITS_RESULTS.md](../TRAITS_RESULTS.md)).

### 2e. Approval process

- **Gabriel and Kung 2026** (in PRODUCTION_EVIDENCE.md). In Los Angeles, a 25% cut in approval times would have raised production 2010 to 2022 by 12.7% (estimated effect).
- **Manville, Gray, Phillips and Monkkonen 2022** (in PRODUCTION_EVIDENCE.md). By-right TOC projects were approved 35% faster, with controls.
- **Gabbe 2018** (observed). C. J. Gabbe, "Why Are Regulations Changed? A Parcel Analysis of Upzoning in Los Angeles," *JPER* 38(3), https://doi.org/10.1177/0739456X17696034. Open copy: https://scholarcommons.scu.edu/cgi/viewcontent.cgi?article=1052&context=ess.
  - Los Angeles upzoned only about 1.1% of its land area from 2002 to 2014 (share of land).
  - Upzoning went where political resistance was low (few homeowners, away from the beach and high-scoring schools).
  - So *where* upzonings happen is itself selected. Gabbe (*JAPA* 85(2), 2019, https://doi.org/10.1080/01944363.2018.1559078) adds that about 1,200 acres were rezoned to allow at least 50 units per acre, 2000 to 2016.

### 2f. Lags

| Study | When the effect appears |
| --- | --- |
| São Paulo | Filings rise about one year after the reform |
| New York (Liao) | Significant after two to three years, still growing at seven |
| Zurich | Nothing in years 1 to 4; +9% at 5 to 10 years; still growing at 15 |
| Auckland | Negative in 2016, rising each year to 2021 |
| Philadelphia (Su et al.) | Not significant until six years after the 2012 code |
| Stacy et al. | Average over years 3 or more after passage |

Philadelphia's slow start was partly the years-long remapping of the code onto the zoning map (observed, Su et al.).

### 2g. Interest rates and the building cycle

- **Auckland** (observed, Greenaway-McGrevy 2025, EPC WP 017, https://www.auckland.ac.nz/assets/business/our-research/docs/economic-policy-centre/EPC-WP017.pdf). Permits rose from about 9,200 in 2015 to a record 21,000 in 2022. They fell after an "unprecedented rise in interest rates" and a recession, but stayed above the 2002 peak.
- **Philadelphia** (observed, Su et al.). The largest gap came in 2021, when a ten-year tax abatement on new building was about to end. Upzoning supplied capacity that a financing shock then filled.
- **Los Angeles** (observed, Kestelman). The TOC pipeline reached permits in 2020 to 2022, during COVID-19 and then rising rates.
- **Brisbane** (observed, Murray and Limb). Supply and price moved mostly with time periods common to all centres, not with each centre's capacity.
- **Murray 2021 (theory).** "A Housing Supply Absorption Rate Equation," *Journal of Real Estate Finance and Economics*, https://doi.org/10.1007/s11146-020-09815-z.
  - Landowners choose a pace of sales that protects price growth.
  - In this model higher interest rates *raise* the optimal pace of supply, because holding land costs more.
  - Density limits can speed supply, by lowering the gain from waiting.
  - This runs against the usual view and is theory, not a measured effect.

### 2h. Transit quality and network coverage

- **No study found tests whether transit quality, or how much of a city the network covers, changes the construction response to an upzoning.** The owner's coverage theory is untested in the literature, not refuted.
- **Indirect evidence.**
  - **Auckland** (observed). Greenaway-McGrevy and Jones, *Urban Studies* 62(12) (2025), https://doi.org/10.1177/00420980241311521. After the reform, housing starts moved closer to rapid-transit stations, motorway access and job centres. The shift came entirely from upzoned areas. The upzoning was itself concentrated near transport.
  - **San Diego** (observed). King and Fischer, "Long Term Land Use Effects of New Rail Investment: Lessons from San Diego," *Urban Science* 2(1) (2018), https://doi.org/10.3390/urbansci2010006. Three decades after rail opened, station areas showed no consistent pattern of denser zoning or new mixed-use building. Existing land use was sticky.
  - **US BRT** (observed, descriptive). Nelson and others, NITC-RR-650 (TREC, Portland State), https://ppms.trec.pdx.edu/media/project_files/NITC-RR-650.pdf. In metros with BRT, the share of new multifamily floor space within ½ mile of BRT rose from 2.2% (2000 to 2007) to 5.2% (2008 to 2015). The authors warn this may be relocation, "resulting in no net development gain".
  - **ITDP 2013** (source_lead, advocacy report, https://itdp.org/wp-content/uploads/2013/11/More-Development-For-Your-Transit-Dollar_ITDP.pdf). Across 21 US corridors, it ranks government support first, land-market strength second and transit quality third as predictors of TOD investment.
- **Our own tests:** transit jobs access (EPA D5BR) failed as a trait ([TRAITS_RESULTS.md](../TRAITS_RESULTS.md)).

---

## 3. Statewide and wide reforms, and general equilibrium

**Wide reforms have produced much larger responses than spot upzonings.**

| Reform | Share upzoned | Response | Source |
| --- | --- | --- | --- |
| Auckland 2016 | About 75% of residential land | New permits per head about doubled within five years; 52,200 extra permits 2017 to 2023, 46% of the 112,300 issued | Greenaway-McGrevy 2025, WP 017 (observed, working paper) |
| Lower Hutt | About 80% of residential land | Starts about tripled | Maltman and Greenaway-McGrevy 2025 (observed) |
| Los Angeles | 1.1% of land, 2002 to 2014 | Small | Gabbe 2018 (observed) |
| Chicago 2013, 2015 | Small strips near stations | None in five years | Freemark 2020 (observed) |

**Reasons given for why wide reforms differ** (Greenaway-McGrevy 2025, WP 017, observed as the author's argument):
- more sites compete, so land prices rise less per site (citing Kulish and others 2012);
- builders can scale up;
- permitting is faster.

The Lower Hutt paper adds competition between landowners (citing Phillips 2022).

**Does a broad upzoning spread demand thin?**
- **Brisbane: yes, in effect.** Capacity there far exceeded what the market absorbed (2% of capacity per five years). Adding capacity did not raise the pace.
- **Absorption.** Murray's absorption-rate argument says the market builds at the pace demand growth allows, whatever the zoned capacity.
- **Long-run citywide effects are modest relative to the capacity added** (derived ratios, to compare orders of magnitude only):

| Place | Long-run stock gain | Capacity added | Ratio (derived) |
| --- | --- | --- | --- |
| São Paulo | 1.6% | 36% more allowed floor area | 0.044 |
| New York (Peng) | 0.7% | 5% of stock | 0.14 |
| Auckland, 5 to 6 years | 4.1% to 5.1% of stock | About trebled | Not computed (still rising) |

**Between cities.**
- Molloy, Nathanson and Paciorek, "Housing supply and affordability: Evidence from rents, housing consumption and household location," *JUE* 129 (2022) 103427, https://doi.org/10.1016/j.jue.2022.103427 (observed). Across US metros, 1980 to 2016, supply constraints had sizeable effects on prices and stock growth. Their effects on rents, sorting across metros and location within metros were modest to negligible.
- Greenaway-McGrevy and So, "Can zoning reform reduce housing costs? Evidence from rents in Auckland," *Economic Inquiry* (2026), https://doi.org/10.1111/ecin.70075 (observed). Auckland rents were 23% lower by 2024 than a synthetic control of other NZ cities. The authors note that in-migration to Auckland would bias that estimate *down*.
- Lower Hutt rents were about 21% lower by 2023 (observed).

**Statewide or national reforms.**
- No rigorous evaluation found of New Zealand's 2021 Medium Density Residential Standards or 2020 NPS-UD. Nor of California SB 9, Oregon HB 2001, or the state TOD laws in PRODUCTION_EVIDENCE.md.
- One 2026 paper on the NZ standards was found but left out. It is labelled as autonomously generated research, not peer-reviewed.
- **Stacy et al. 2023** remains the only multi-city panel (per reform, citywide addresses; see NET_EFFECT_SOURCES.md).
- **Paris region** (observed, descriptive, not causal). Freemark, "Doubling housing production in the Paris region," *International Journal of Housing Policy* 21(2) (2021), https://doi.org/10.1080/19491247.2019.1682233.
  - Authorised homes rose from an average of 43,000 a year (1991 to 2014) to 98,300 (2017) and 89,200 (2018).
  - This followed regional targets, enforcement of local plans from above, public land and subsidy together. It was not an upzoning alone.

---

## 4. Citywide net-effect figures

The three in use first, then candidates to add. "Net" means after building moved from elsewhere in the area named in the denominator.

| Place | Figure | Numerator | Denominator | Period | Kind | What it nets out | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Los Angeles TOC (in use) | +0.04 percentage points | 562 units | Citywide stock, about 1.4 million | 2017 to 2023 (6 years) | Estimated effect less earlier growth rate | Compares the local estimate with the city's earlier growth rate | Kestelman 2025 |
| Stacy et al. (in use) | +0.8% per loosening reform | Change in USPS addresses | City's address count | Average of years 3+ after passage | Estimated association | Whole-city outcome | Stacy et al. 2023 |
| Auckland (in use) | +4.11% | 21,808 permits | 530,300 dwellings, end 2016 | 2016 to 2021 | Estimated effect | Displacement from non-upzoned Auckland residential land, by extrapolated trend | Greenaway-McGrevy and Phillips 2023 |
| **Auckland update** | +5.11% | At least 27,000 permits | Auckland stock (as above) | To 2022 | Estimated effect (author: a lower bound) | Also displacement from rural and business zones | Greenaway-McGrevy 2023, EPC WP 015, https://cdn.auckland.ac.nz/assets/business/about/our-research/research-institutes-and-centres/Economic-Policy-Centre--EPC-/WP015.pdf |
| **Auckland, synthetic control** | +9.8% (derived) | 52,200 extra permits | 530,300 dwellings, 2016 | 2017 to 2023 (7 years) | Estimated effect | All within-Auckland shifts; not moves from other NZ cities | Greenaway-McGrevy 2025, WP 017 |
| **São Paulo** | +1.6% (published) or +1.9% (NBER) | Long-run housing stock change | City housing stock | Long run (model) | Model counterfactual | Whole-city equilibrium | Anagol, Ferreira and Rexer |
| **New York, Bloomberg rezonings** | +0.7% | Long-run total housing supply change | City housing stock | Long run (model) | Model counterfactual | Whole-city dynamic spatial model | Peng 2023 (working paper) |
| **Lower Hutt, Wellington region** | +12.6% (range +9.5% to +18.2%) | 1,848 net extra consents (3,006 in Lower Hutt less 1,157 displaced) | Counterfactual regional consents (16,501 − 1,848) | 2018 to 2023 (6 years) | Estimated effect on the flow of consents, not on stock | Point-estimate displacement from four neighbouring towns | Maltman and Greenaway-McGrevy 2025 |
| **New York, 7 upzonings** | About 4,100 units | Extra units on upzoned parcels | None citywide stated | 4 years after each upzoning | Estimated local effect | Not netted (authors say substitution unknown) | Su et al. 2026 |
| **Philadelphia 2012 code** | Up to about 4,000 unit permits a year | Extra permits, upzoned vs matched block faces | None citywide stated | Peak year 2021 | Estimated local effect | Not netted | Su et al. 2026 |

**Notes on adding them.**
- **Comparable as shares of whole-city stock:** São Paulo and New York (Peng). Both are model-based long-run figures, not measured counts. They sit between Los Angeles (0.04 points) and Auckland (4.1%), close to Stacy et al.'s 0.8%. That supports the "typical" scenario size.
- **Auckland synthetic control** (9.8% over seven years) is larger than the 4.11% in use because:
  - it covers seven years, not six;
  - it compares against other cities, not other parts of Auckland, so it keeps building that moved within Auckland only if that building would not otherwise have happened.
  It may double-count gains from New Zealand's 2013 to 2016 Special Housing Areas. Keep 4.11% as the strong scenario; cite 9.8% as an upper check.
- **Lower Hutt** is a share of regional *consents*, not stock. Lower Hutt's dwelling stock was not found in the paper, so a stock share cannot be derived here.
- **New York and Philadelphia (Su et al.)** are local, not net. Do not add them as net figures. They are close to our own fitted cases and can serve as checks on those.

---

## 5. Implications for our model

### 5a. For the borrowing test in NET_EFFECT_PLAN.md

1. **Expect the ¼-mile ring to show little or no loss.** That is what Liao (New York), Anagol et al. (São Paulo) and Büchler and Lutz (Zurich) found at that scale. A null ring result should be reported as "no next-door borrowing", not "no borrowing".
2. **Borrowing, where found, came from far away** (Auckland: from areas with spare vacant land; Lower Hutt: from other towns). Our "far land" (¼ to 1½ miles) is the comparison in the plan. If it lost building too, the plan's net effect is overstated. Suggested addition, to be written into the plan's section 8 before looking: compare far land after against before with the rest of the city beyond 1½ miles, or with the city's own pre-reform trend extrapolated (the Greenaway-McGrevy and Phillips method).
3. **The plan's net formula matches the Auckland logic.** Treatment and ring are each against far land, times acres. Under the Auckland framework, a home moved from far land into treatment counts twice in a treatment-minus-far gap. A short note in the plan on this would help readers.

### 5b. Testable theories, ranked by support in the literature

Each could be pre-registered in the style of [TRAITS_PLAN.md](../TRAITS_PLAN.md). Each uses data the cases already hold or can fetch.

1. **Binding zoning (strongest support: Zurich, Brisbane, New York).**
   - Theory: units whose lots were built close to the old limit respond more.
   - Measure: built FAR ÷ old maximum FAR, acre-weighted, before the change. New York has both in MapPLUTO; Chicago and Madison have assessor floor area and zoning.
   - Not in our 12 traits.
2. **Market strength × binding × size, together.**
   - Theory: response needs all three (Zurich's split results).
   - Test as an interaction, or as a rule: rent above a cost threshold AND binding AND added FAR above a cutoff, against the plain average.
   - Single traits failing ([TRAITS_RESULTS.md](../TRAITS_RESULTS.md)) is what this theory predicts.
3. **Effective capacity added, not added FAR.**
   - Theory: homes newly allowed per acre beyond what is already built predict better than the FAR change.
   - The same 1.0 added FAR means nothing on a lot built far below the old limit.
4. **Share of the city upzoned.**
   - Theory: wide reforms respond more per acre (Auckland, Lower Hutt against Chicago, Los Angeles).
   - One value per city, so report it beside each city's net effect, as the plan does for coverage.
5. **Approval route.**
   - Theory: units where the change made projects by-right respond more than units where hearings remained.
   - Madison's overlay mechanism is exactly this.
6. **Cycle timing.**
   - Theory: part of the spread between cities is when their after-years fell in the cycle.
   - Test: add national multifamily starts per year as a control, or compare effects in years before and after 2022.
7. **Transit coverage and island size (owner's theory).**
   - No published support or refutation found.
   - Keep as in the plan. State plainly that it is a new question, not a replication.

### 5c. For Wisconsin scenario sizes (for the owner, nothing changed)

- The new figures (São Paulo 1.6%, New York 0.7%) fall inside the current little-to-strong range and near the typical scenario. They do not argue for moving it.
- Brisbane's evidence argues that in areas where zoned capacity already exceeds demand, more capacity adds little. Wisconsin cities where station areas are built well below their current zoning would sit near the "little" scenario. Whether that is true of Milwaukee or Madison station areas is not known. It is checkable with assessor floor area against zoning.
- None of these studies measures a station-area-only reform covering a small share of a city with spare greenfield land nearby. That is the Wisconsin case. Auckland's evidence suggests such land is where displaced building would come from, so a net effect below the borrowed studies is plausible.

---

## Sources

Peer-reviewed or published:
- Anagol, S., Ferreira, F., Rexer, J. "Estimating the Economic Value of Zoning Reform." *AEJ: Economic Policy*. https://doi.org/10.1257/pol.20230542 ; NBER WP 29440, https://www.nber.org/papers/w29440
- Baum-Snow, N. (2023). "Constraints on City and Neighborhood Growth: The Central Role of Housing Supply." *JEP* 37(2), 53 to 74. https://doi.org/10.1257/jep.37.2.53
- Brooks, L., Lutz, B. (2016). "From Today's City to Tomorrow's City." *AEJ: Economic Policy* 8(3), 69 to 105. https://doi.org/10.1257/pol.20130399
- Büchler, S., Lutz, E. (2024). "Making housing affordable? The local effects of relaxing land-use regulation." *JUE* 143, 103689. https://doi.org/10.1016/j.jue.2024.103689
- Dong, H. (2024, online 2021). "Exploring the Impacts of Zoning and Upzoning on Housing Development." *JPER* 44(1), 403 to 415. https://doi.org/10.1177/0739456X21990728
- Freemark, Y. (2020). "Upzoning Chicago." *Urban Affairs Review* 56(3), 758 to 789. https://doi.org/10.1177/1078087418824672
- Freemark, Y. (2021). "Doubling housing production in the Paris region." *International Journal of Housing Policy* 21(2). https://doi.org/10.1080/19491247.2019.1682233
- Freemark, Y. (2023). "Zoning change: Upzonings, downzonings, and their impacts on residential construction, housing costs, and neighborhood demographics." *Journal of Planning Literature* 38(4). https://doi.org/10.1177/08854122231166961
- Gabbe, C. J. (2018). "Why Are Regulations Changed? A Parcel Analysis of Upzoning in Los Angeles." *JPER* 38(3). https://doi.org/10.1177/0739456X17696034
- Gabbe, C. J. (2019). "Changing Residential Land Use Regulations to Address High Housing Prices." *JAPA* 85(2). https://doi.org/10.1080/01944363.2018.1559078
- Greenaway-McGrevy, R., Jones, J. A. (2025). "Can zoning reform change urban development patterns? Evidence from Auckland." *Urban Studies* 62(12). https://doi.org/10.1177/00420980241311521
- Greenaway-McGrevy, R., Phillips, P. C. B. (2023). "The impact of upzoning on housing construction in Auckland." *JUE* 136, 103555. https://doi.org/10.1016/j.jue.2023.103555
- Greenaway-McGrevy, R., So, Y. (2026). "Can zoning reform reduce housing costs? Evidence from rents in Auckland." *Economic Inquiry*. https://doi.org/10.1111/ecin.70075
- King, D., Fischer, L. A. (2018). "Long Term Land Use Effects of New Rail Investment: Lessons from San Diego." *Urban Science* 2(1). https://doi.org/10.3390/urbansci2010006
- Kuhlmann, D. (2021). "Upzoning and Single-Family Housing Prices." *JAPA* 87(3), 383 to 395. https://doi.org/10.1080/01944363.2020.1852101
- Liao, H.-L. (2026). "The effect of rezoning on local housing supply and demand: Evidence from New York City." *Regional Science and Urban Economics* 117, 104188. https://doi.org/10.1016/j.regsciurbeco.2025.104188
- Limb, M., Murray, C. K. (2023). "We zoned for density and got higher house prices." *Urban Policy and Research* 41(2). https://doi.org/10.1080/08111146.2022.2124966
- Maltman, M., Greenaway-McGrevy, R. (2025). "Going it alone: The impact of upzoning on housing construction in Lower Hutt." *Journal of Housing Economics* 67, 102032. https://doi.org/10.1016/j.jhe.2024.102032
- Molloy, R., Nathanson, C., Paciorek, A. (2022). "Housing supply and affordability." *JUE* 129, 103427. https://doi.org/10.1016/j.jue.2022.103427
- Murray, C. K. (2021). "A Housing Supply Absorption Rate Equation." *Journal of Real Estate Finance and Economics*. https://doi.org/10.1007/s11146-020-09815-z
- Stacy, C. and others (2023). "Land-use reforms and housing costs." *Urban Studies* 60(14), 2919 to 2940. https://doi.org/10.1177/00420980231159500

Working papers and reports:
- Greenaway-McGrevy, R. (2023). "The Impact of Upzoning on Housing Construction in Auckland: Update and Extended Results." EPC WP 015. https://cdn.auckland.ac.nz/assets/business/about/our-research/research-institutes-and-centres/Economic-Policy-Centre--EPC-/WP015.pdf
- Greenaway-McGrevy, R. (2025). "Can zoning reform increase housing construction? Evidence from Auckland." EPC WP 017. https://www.auckland.ac.nz/assets/business/our-research/docs/economic-policy-centre/EPC-WP017.pdf
- Kestelman, S. (2025). "Effects of Transit-Oriented Incentive Programs: Evidence from Los Angeles." Harvard JCHS. See NET_EFFECT_SOURCES.md.
- Kulka, A., Sood, A., Chiumenti, N. (2022). "How to Increase Housing Affordability." Boston Fed WP 22-10. https://www.bostonfed.org/-/media/Documents/Workingpapers/PDF/2022/wp2210.pdf
- Nelson, A. C. and others. NITC-RR-650, BRT and economic development. https://ppms.trec.pdx.edu/media/project_files/NITC-RR-650.pdf
- Peng, X. E. (2023). "The Dynamics of Urban Development: Evidence from Zoning Reform in New York." Job-market paper. https://penniur.upenn.edu/publications/the-dynamics-of-urban-development-evidence-from-land-use-reform-in-new-york
- Su, Y., Curran-Groome, W., Freemark, Y. (2026). "How Big Upzonings Affect Housing Supply." Urban Institute. https://www.urban.org/research/publication/how-big-upzonings-affect-housing-supply
- Wang, B. X., Krimmel, J. (2023). "Upzoning with Strings Attached." SSRN 4578637. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4578637

Pointers only (source_lead): Barr, "Upzoning" blog summary, https://buildingtheskyline.org/upzoning-1/ ; ITDP (2013), https://itdp.org/wp-content/uploads/2013/11/More-Development-For-Your-Transit-Dollar_ITDP.pdf .

**Not read for this note:**
- the Econ Journal Watch critique of Stacy et al.;
- the full text of Freemark 2023 (the summary page was read);
- the published AEJ text of Anagol et al. (the NBER version was read for the spillover section);
- the full Peng paper (abstract only);
- a Georgetown thesis on spillovers of Seattle's Urban Villages, found but not read.
