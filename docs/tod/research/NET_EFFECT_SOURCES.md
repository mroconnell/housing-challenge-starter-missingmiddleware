# Net-effect sizing: source check

Written 2026-10-26. This file checks the three published values behind the net-effect sizing in [GATE3_MODEL_SPEC.md](../GATE3_MODEL_SPEC.md) section 9 (last entry) and [MODEL.md](../MODEL.md) section 11. Each value was checked against the original text.

Summary of verdicts:

| Scenario | Value as used in the repo | Verdict |
| --- | --- | --- |
| Little | Los Angeles TOC, 0.04 percentage points of stock growth **a year** | **Corrected.** The 0.04 points is over six years (2017 to 2023), not a year. |
| Typical | Stacy et al., +0.8% of housing supply 3 to 9 years after an upzoning | **Confirmed with corrections to the wording.** It is per loosening reform, measured in USPS address counts, as an average over all years 3 or more after passage. Many reforms were not upzonings in the FAR or height sense. |
| Strong | Auckland, 21,808 extra consents 2016 to 2021, 4.1% of 530,300 dwellings, yearly effects −2.63 to 18.00 | **Confirmed.** No numeric interval is published for the total. |

---

## 1. Los Angeles Transit Oriented Communities (little)

**Citation.** Stephanie Kestelman, "Effects of Transit-Oriented Incentive Programs: Evidence from Los Angeles," Harvard Joint Center for Housing Studies working paper, 1 December 2025. https://www.jchs.harvard.edu/research-areas/working-papers/effects-transit-oriented-incentive-programs-evidence-los-angeles

**What was read.** The JCHS working-paper PDF could not be downloaded (the server refuses automated requests). The working-paper abstract and the JCHS blog post were read. The full text read is Chapter 1 of the same author's dissertation, which carries the same title: Stephanie Kestelman, *Essays on Housing Policy*, Harvard PhD dissertation, 2025, https://dash.harvard.edu/handle/1/42719786 (PDF: https://dash.harvard.edu/bitstreams/7be7fec5-63c8-4b9b-8b46-4563500cb299/download). The figures below are from the dissertation chapter. The blog for the working paper says "fewer than 560 housing units over six years", where the dissertation says 562.01. The working paper may have revised the figure slightly. This should be checked against the working-paper PDF by hand.

**Exact figure.** The dissertation's introduction says TOC "increased the rate of growth in the housing stock by 0.04 percentage points, or 562.01 housing units over 6 years."
- Unit: percentage points of growth in the housing stock, and housing units.
- Period: six years, 2017 to 2023. **This is a six-year total, not a yearly rate.**
- Numerator: 562.01 extra housing units (estimated effect, as stated).
- Denominator: the citywide stock of Los Angeles. The paper does not state which year's stock it used. 562.01 ÷ 0.0004 implies about 1.405 million units (derived). The nearest figures the paper states are 1,372,033 units in 2010 and 27,218 units of growth from 2010 to 2016, which gives 1,399,251 in 2016 (derived).

**How the 0.04 points appears to be built.** The body of the chapter gives two numbers side by side:
- the border difference-in-differences estimate: the housing stock on the treated side of the ½-mile Major Transit Area border rose by 33.54 units per boundary segment from 2017 to 2023, over a baseline mean of 1,654.80 units per segment. That is 2.02% (estimated effect, p < 0.01);
- for comparison, Los Angeles's citywide stock grew 1.98% from 2010 to 2016 (27,218 ÷ 1,372,033, observed).

2.02 − 1.98 = 0.04 percentage points (derived). The paper does not spell out this subtraction, but it is the only reading that matches the stated numbers. If this is right, the 0.04 points is not a regression coefficient. It compares the local effect with the city's earlier growth rate.

**Interval.** None is published for the 0.04 points or the 562 units. The underlying border estimate (+33.54 units per segment) is shown only as a year-by-year chart (Figure 1.4) with 95% confidence intervals, standard errors clustered by Major Transit Area, and a p-value below 0.01. No numeric interval is given in the text.

**What it measures.** Total residential units per parcel in the 2006 to 2023 county assessor files, summed by side of each boundary segment. A separate estimate on permits found no statistically measurable effect on units permitted, while units proposed rose by 27.6 a year per segment (p < 0.01).

**Verdict: corrected.** Was "0.04 percentage points of stock growth a year" (MODEL.md section 11 table, GATE3_MODEL_SPEC.md section 9). Is "0.04 percentage points over six years, 2017 to 2023", or about 0.007 points a year (derived). Over a five-year window that is about 0.033% of stock (0.04 × 5/6, derived), not 0.2%. "562 units over 6 years" is confirmed.

**Area and denominator.**
- The eligible area is every parcel within ½ mile of a major transit stop. Only lots zoned for multifamily housing could use the incentives, and only projects of 5 or more units.
- Table 1.1 of the chapter: 308,866 of Los Angeles's 662,145 parcels are within ½ mile of a major transit stop, which is 46.6% of parcels (derived). Mean residential units per parcel are 2.6 inside the area and 2.0 citywide, so the area holds roughly 61% of the city's units (derived, from rounded means).
- 48.2% of parcels inside the area are zoned multifamily, against 30.4% citywide (Table 1.1, observed). The chapter's text gives 37.8% for the same comparison. The table and text disagree.
- So the 562 units as a share of the station-area stock would be about 0.07% over six years (562 ÷ about 0.8 to 0.86 million, derived), not 0.04%. Applying 0.04 points to station-area stock slightly understates it. Both are very small.
- The local border estimate, 2.02% of treated-side stock over six years, is the station-area number. It is about 50 times the citywide figure. It also compares against the control side of the same border, so it counts any building pulled from just outside the boundary as new.

---

## 2. Stacy et al. 2023 (typical)

**Citation.** Christina Stacy, Chris Davis, Yonah Slifkin Freemark, Lydia Lo, Graham MacDonald, Vivian Zheng and Rolf Pendall, "Land-use reforms and housing costs: Does allowing for increased density lead to greater affordability?", *Urban Studies* 60(14) (2023), 2919 to 2940. https://doi.org/10.1177/00420980231159500. Copy read: https://gwern.net/doc/economics/georgism/2023-stacy.pdf (the published article). The journal is *Urban Studies*, not *Urban Affairs Review*.

**Exact figure.** Table 4, column 1: reforms loosening restrictions, post period, coefficient **0.008 (standard error 0.003), p < 0.01**, on the natural log of total addresses.
- Unit: a semi-elasticity, so about +0.8% of a city's address count.
- **Per reform.** The treatment variable counts the loosening reforms a city has passed to date. So 0.8% is the association for each loosening reform, not for "an upzoning" in general.
- Numerator and denominator: change in the city's total USPS address count over the city's total address count. Addresses come from USPS tract data, moved to places with a crosswalk. Addresses are not housing units or permits; they count existing and new delivery points.
- Sample: a quarterly panel of 1,136 cities in eight metro areas, 2005 Q4 to 2021 Q1, 68,634 observations.

**Interval.** Not printed in the paper. From the coefficient and standard error, the 95% interval is about +0.2% to +1.4% (0.008 ± 1.96 × 0.003, derived).

**Timing.** The post period is every year **three or more years** after passage, compared with the three years before. It is an average over all such years. Reforms were passed 2005 to 2019 and the panel ends in 2021, so the window reaches past nine years for early reforms. The abstract's wording is "within three to nine years of reform passage". The implementation period (two years before to two years after) shows no significant effect (0.003, standard error 0.002).
- The year-by-year model (Table 6) does not show a rising path. For loosening reforms, every yearly coefficient on addresses from year 1 to year 6 and later is 0.000 or 0.001, none significant.

**What counts as a reform.** Reforms found in newspaper articles from 2000 to 2019 by machine learning, then hand-coded. The dataset holds 180 reforms passed 2005 to 2019: 96 loosening and 84 tightening. Loosening reforms by type (Table 2): ADUs 35, minimum lot size 19, FAR or density 15, height limits 13, general rezoning 11, mixed use 3. So fewer than a third (28 of 96) are FAR, density or height changes. Small reforms that affected only one or two neighbourhoods were left out on purpose. About one third of all reforms were in the Los Angeles metro area.

**Strength of evidence.** A fixed-effects model with city trends. The authors say they "cannot fully assert a causal relationship". A falsification test with future reforms finds no pre-trend in addresses. A published critique exists (Econ Journal Watch, https://econjwatch.org/articles/a-critique-of-an-urban-studies-article-on-the-housing-supply-impact-of-land-use-reforms); it was not read for this check.

**Verdict: confirmed, with corrections to the wording.** "+0.8% of housing supply across 1,136 US cities, significant" is confirmed. Corrections:
- was "upzonings", is "each reform loosening land-use restrictions" (mostly ADU and lot-size reforms);
- was "housing supply", is "USPS address count";
- was "3 to 9 years after", is "average of all years 3 or more after passage" (the abstract says 3 to 9);
- the repo's evidence table says "180 upzonings and downzonings, 2000 to 2019"; the reforms were passed 2005 to 2019, and the newspapers searched span 2000 to 2019.

**Area and denominator.** The denominator is the whole city's address count. The paper does not measure what share of each city each reform covered; it assumes the reforms affected cities overall, and many were citywide (ADU and lot-size rules). Applying 0.8% to station-area stock is therefore fair only if the station-area rule is read as the whole "city" the reform covered. If a reform covered part of a city, the effect per affected home would be larger than 0.8%, but the paper gives no way to size that.

---

## 3. Auckland Unitary Plan (strong)

**Citation.** Ryan Greenaway-McGrevy and Peter C. B. Phillips, "The impact of upzoning on housing construction in Auckland," *Journal of Urban Economics* 136 (2023) 103555. https://doi.org/10.1016/j.jue.2023.103555. Copy read: Cowles Foundation Paper 1863, https://cowles.yale.edu/sites/default/files/2024-02/p1863.pdf (the published article).

**Exact figure.** Section 5.4: spillover-adjusted treatment effects for 2016 to 2021 are −2.63, 2.34, 6.79, 8.95, 12.09 and 18.00, summing to 45.53. Times 479 statistical areas, that is 21,808 additional permits. The paper says this is 4.11% of the city's housing stock, using Statistics New Zealand's 530,300 dwellings in Auckland at the end of 2016.
- Unit: dwelling permits (building consents), not completions. At historic completion rates of 95% to 99%, the paper converts this to 20,718 to 21,590 completed dwellings.
- Yearly effects: extra permits per statistical area per year, upzoned part against non-upzoned part.
- Numerator: 21,808 extra permits. Denominator: 530,300 dwellings, the whole of Auckland, end of 2016.
- "Spillover-adjusted" means the paper subtracts building it estimates was moved out of non-upzoned areas, using an extrapolated linear trend in those areas. So 21,808 is a net figure, after displacement. Before the adjustment, upzoned areas had 34,614 more permits than non-upzoned areas over 2016 to 2021.

**Interval.** No numeric interval is published for 21,808 or 4.11%. Figure 14 shows yearly 95% confidence intervals (standard errors clustered by statistical area) as a chart only. As a robustness bound, the 2021 effect stays significant unless the counterfactual allows more than about four times the trend increase in non-upzoned permits (4,469 against 1,116 extra permits).

**Timing.** The paper's treatment date (year 0) is **2015**, because the first draft of the plan was published in 2013 and building may have shifted early. The plan became operative in November 2016. The six yearly effects are 2016 to 2021, which the paper calls the five years after the reform. The paper notes permits were still rising in 2021, so the full effect was not yet seen.

**Verdict: confirmed.** 21,808, 4.1% (4.11%), 530,300 and the six yearly effects all match.

Two notes for the model:
- MODEL.md treats 2016 as year 0 and uses 2017 to 2021 as years 1 to 5. Those five effects sum to 48.16 per statistical area, or 23,069 permits, 4.35% of stock (derived). The model applies 4.1%, which includes 2016's −2.63. The profile and the total come from slightly different year sets.
- The paper's own year 0 is 2015, not 2016.

**Area and denominator.** The denominator is all of Auckland's dwellings. 75.2% of residential land was classed as upzoned (by the authors' FAR test). That is a share of land, not of dwellings; the paper does not give the share of dwellings in upzoned areas. Dividing 4.11% by 0.752 gives about 5.5% of stock in upzoned areas (derived), which matches the spec's ÷ 0.75 sensitivity. The upzoning was concentrated within reach of transit but was not a station-area rule.

---

## Is it fair to apply each as a share of station-area stock?

| Study | Denominator in the study | Share of the city covered | Effect per covered home (derived) |
| --- | --- | --- | --- |
| Los Angeles TOC | Citywide stock, about 1.4 million units | About 47% of parcels, roughly 61% of units, within ½ mile of major transit | About 0.07% over six years |
| Stacy et al. | Each city's total USPS addresses | Not measured; many reforms citywide | Unknown; at least 0.8% per reform |
| Auckland | All 530,300 Auckland dwellings | 75.2% of residential land | About 5.5% over 2016 to 2021 |

- All three are net figures for a whole city, so they fit the model's purpose of avoiding counting building pulled from nearby blocks.
- Applying the citywide share to station-area stock understates the per-covered-home effect in all three, by a factor of roughly 1.3 (Auckland) to 1.6 (Los Angeles). For Stacy et al. the factor is unknown.
- Wisconsin's station areas would cover a much smaller share of each city than these reforms did. A smaller covered area leaves more uncovered land nearby to pull building from, so the per-covered-home net effect could be lower than in these studies, not higher. None of the three studies measures that case directly.
