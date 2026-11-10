# How studies scale a zoning effect to a bigger reform

Question: we measured "up to 4 homes per lot" laws. How should we project "up to 6"?
Options: multiply by a dose ratio, add a fixed amount, or use the share of lots that can take 5–6 homes.

Researched 2026-11-10. Public web sources only. No repository edits.
**V** = I read the paper or report text (PDF text extracted). **S** = abstract or secondary summary only.
Local text copies: `(local scratch)`

---

## Summary table

| # | Study | V/S | What was measured | How a bigger or different reform was handled | How uncertainty was carried | Key number (units) | Bigger dose, bigger effect per unit? |
|---|---|---|---|---|---|---|---|
| 1 | Greenaway-McGrevy & Phillips 2023, *J. Urban Econ.* 136:103555 (Auckland) | V | Building permits per statistical area; upzoned vs not-upzoned areas | **No scaling.** Each zone estimated separately: MHS (3 homes, 2 storeys), MHU (3 homes, 3 storeys), THA (5–7 storeys) | Set identification: a range of counterfactual trends (M = 0…14) with 95% intervals. Point estimate only at M = 0 | 2016–2021 extra permits: THA 7,241 (27% of extra), MHU 10,991 (41%), MHS ≈ 32%. Detached homes: confidence sets include zero | Not tested per unit of capacity. MHS (smallest uplift) significant for all homes, not for detached |
| 2 | Greenaway-McGrevy 2023, EPC Working Paper 013 (Auckland, long run) | V | Change in land-price gradient by zone, read as change in the floor area ratio (FAR) developers build to | **Capacity-weighted sum:** (zone FAR uplift × land area × existing FAR), summed over zones | Four specifications (A–D); price-elasticity range −0.5 to −0.8 | Market-valued capacity +18.1% of metro floorspace. That is ≈ 40% of the nominal (paper) capacity increase. Realized 5-year homes ≈ ¼ to ⅕ of that 18.1% | **Concave.** Land-value uplift: MHS 0.205, MHU 0.265, THA 0.369 log points. Much more allowed height gives a smaller extra uplift per storey |
| 3 | Anagol, Ferreira & Rexer, NBER w29440 (rev. Mar 2023), São Paulo | V | Permits vs block-level max built-area ratio (BAR, Brazil's FAR); regression discontinuity plus a Poisson supply model | **Functional-form extrapolation:** log(permits) is linear in max BAR, so the response is exponential. A "double BAR" scenario sits far outside the observed range | Bootstrapped SEs (500 reps) on parameters. Counterfactual home totals are point estimates, with no interval | +1 BAR ≈ ×2 permits (+5.05 permits per unit of area at the mean). Actual reform: avg BAR +0.54 gave +47,030 homes (+1.9% of city stock). Double BAR: +27.5% of stock | **Convex by assumption** (≈3.6× the BAR change gives ≈14× the effect). BAR had no significant effect on single-family permits |
| 4 | Kulka, Sood & Chiumenti, Boston Fed WP 22-10 (2022), Greater Boston | V | Homes per lot at zoning boundaries vs dwelling units per acre (DUPAC), height and multifamily rules | **Linear per unit** within the observed gap (e.g., +4.4 DUPAC). Simulated only small changes (+10% DUPAC, +1 floor) near 23 transit stations | 95% intervals by distance band; insignificant points flagged | Relaxing density limits: +0.43 to +2.4 homes per lot (+27% to +92%). Multifamily or height alone: ≈ 0 | **No significant effect on 4+ unit buildings** in the spatial analysis; they modelled 2–3 unit supply only |
| 5 | Büchler & Lutz 2024, *J. Urban Econ.* 143:103689 (Canton Zurich) | S | Living space and homes after FAR increases; staggered difference-in-differences | Effect split by size of upzoning; working paper used a "≥ 20% FAR increase" cut-off | Standard DiD intervals (not read) | ≈ +9% living space and homes within 5–10 years. Working paper: ≥ 20% FAR uplift gave +13% on treated parcels over 10 years | **Larger upzonings, larger effect** — but also stronger where zoning binds and rents are high. Not shown to be proportional |
| 6 | Terner Center (Metcalf, Garcia et al.), *Will Allowing Duplexes and Lot Splits Create More Housing?* (SB 9), July 2021 | V | Parcel-by-parcel pro forma (MapCraft): best-return option per parcel among 0–4 new units | **Feasibility share.** Each parcel picks its most profitable count. No elasticity used | Sensitivity runs: −10% construction cost → +5% feasible homes (+36,000); +10% cost → −4.5% (−32,000) | Of 7.5M single-family parcels: 78% none feasible, 1% → 1 new home, 12% → 2, 7% → 3, **2% → 4**. 110,000 newly feasible parcels (1.5%). ≈ 700,000 feasible homes in total | **Yes, steep drop-off.** Parcels feasible for ≥ 3 new homes ÷ ≥ 2 ≈ 9/21 ≈ 43%. For ≥ 4 ÷ ≥ 3 ≈ 2/9 ≈ 22% |
| 7 | City of Portland BPS memo (Armstrong & Pastor, 9 Mar 2020) on a 6-unit "deeper affordability" bonus; plus BPS *Middle Housing Progress Report 2018–2024* (Jan 2025) | V | Residual land value (RLV) of a 6-plex vs triplex/4-plex; then permits actually issued | **Pro forma on the 5–6 unit step itself**, by market area | Three market areas (Inner/Middle/Outer); ownership vs rental | 6-plex RLV, Inner: $91,750 rental (vs $322,300 for a triplex); negative in Middle and Outer. Permits 2018–mid-2024: ≈ 12 sixplex units vs ≈ 386 fourplex units* | Shows the 5–6 step can be near-zero when it needs commercial building code (cost assumed $225/sq ft). *Sixplex also needed 50% affordable homes, so this is not a pure dose test |
| 8 | CBO 2019, *Effects on Employment and Family Income of Increasing the Federal Minimum Wage* (non-housing) | V | Employment response to a larger minimum wage than history | **Elasticity itself rescaled with dose.** Bigger rise, more workers affected, indexing and a longer window all raise the elasticity. Plus conversion to directly affected workers | "Two-thirds chance" range for the elasticity; low end ≈ 0 (−0.0005 to +0.0005), high end ≈ 2–3 × median | Teen elasticity: −0.100 ($10), −0.111 ($12), −0.128 ($15). Job loss (median): $12 ≈ 0.3M, range 0–0.8M; $15 ≈ 1.3M, range 0–3.7M | Convex (larger dose, larger elasticity) — the economics of labour demand, not lot fit |

Context, not core:
- **Auckland and NZ capacity assessments (HBAs)** (S): official layering is plan-enabled → commercially feasible → "reasonably expected to be realised". Auckland 2021: ≈ 1.01M dwellings plan-enabled (infill + redevelopment), ≈ 840,000 commercially feasible.
- **Freemark 2019/2020, *Urban Affairs Review*, "Upzoning Chicago"** (S): TOD upzoning raised land prices. No measurable effect on new home permits over 5 years. No scaling.
- **California housing-element sites (Monkkonen/Elmendorf, UCLA Lewis Center)** (S): the median Bay Area city is on track to develop ≈ 8% of its listed sites. For non-vacant sites, ≈ 3%. So zoned capacity overstates output by a lot.
- Not useful for this question: Kuhlmann 2021 (Minneapolis, descriptive), Gyourko & Krimmel (zoning tax, price-based), Kendall & Tulip (price gap), Mayer & Somerville (price elasticity). None scales by capacity. Not verified: a Dong JAPA paper on Portland RIP — searches did not find it.

---

## Details per study

### 1. Greenaway-McGrevy & Phillips (2023), JUE — V
- Citation: R. Greenaway-McGrevy, P.C.B. Phillips, "The impact of upzoning on housing construction in Auckland," *Journal of Urban Economics* 136 (2023) 103555. https://doi.org/10.1016/j.jue.2023.103555 (open copy read: https://www.gwern.net/doc/economics/georgism/2023-greenawaymcgrevy.pdf)
- Design: difference-in-differences on permits in 479 statistical areas, in levels. Upzoned areas are 75.1% of residential land.
- Zones (Table 1): SH (1 home), MHS (3 homes, 8–9 m), MHU (3 homes, 11–12 m), THA (16 m, no home cap).
- Uncertainty: the counterfactual trend is a **set**. The paper widens it until the effect would need an "implausibly large" (> 4×) control trend. Point estimates exist only at M = 0.
- Zone results: THA and MHU significant 2019–2021 at M = 14. MHS not significant at 5% for detached homes. Totals by zone: THA 15.12 permits per area (7,241 total), MHU 22.95 per area (10,991 total).
- **No dose scaling.** The paper reports each zone's effect and does not convert effects to "per unit of capacity".

### 2. Greenaway-McGrevy (2023), EPC WP 013 — V
- "Evaluating the Long-Run Effects of Zoning Reform on Urban Development," Univ. of Auckland Economic Policy Centre WP 013. https://cdn.auckland.ac.nz/assets/business/about/our-research/research-institutes-and-centres/Economic-Policy-Centre--EPC-/013WP.pdf
- Method: a land-price jump reveals the FAR developers will actually build to. Aggregate with eq. (12): ln[Σ e^β_j · a_j · h_j / Σ a_j · h_j].
- Key finding for us: **land-value uplift rises with allowed intensity, but less than proportionally.** MHS 0.205, MHU 0.265, THA 0.369 log points.
- Market-valued capacity (+18.1% of floorspace) is ≈ 40% of the nominal capacity increase (Greenaway-McGrevy & Jones). Realized 5-year permits are ¼–⅕ of that.
- Rough chain: realized homes in 5 years ≈ 8–10% of nominal (paper) capacity. This is my arithmetic: 0.40 × (0.20 to 0.25).

### 3. Anagol, Ferreira & Rexer — V
- "Estimating the Economic Value of Zoning Reform," NBER WP 29440 (Oct 2021, rev. Mar 2023). https://www.nber.org/papers/w29440
- 2016 São Paulo reform: average max BAR 1.54 → 2.09; 48% of blocks unchanged or lower.
- Supply model: Poisson. BAR instrumented by regression discontinuity, price by a Bartik shift-share instrument. Coefficient 0.747 on BAR, so +1 BAR ≈ +5.05 permits at a mean of 4.55.
- Extrapolation: a "Double BAR" scenario (average max BAR 3.49) gives +27.5% of city stock, against +1.9% for the real reform. Closed-economy prices fall 15.5% vs 1.1%.
- Uncertainty: parameters bootstrapped; counterfactual totals have no interval.
- **Lesson:** the extrapolation is driven by functional form (exponential). It is not evidence about the 5–6 unit margin. BAR effects on single-family permits were small and insignificant.

### 4. Kulka, Sood & Chiumenti — V
- "How to Increase Housing Affordability: Understanding Local Deterrents to Building Multifamily Housing," FRB Boston WP 22-10 (2022). https://www.bostonfed.org/-/media/Documents/Workingpapers/PDF/2022/wp2210.pdf
- Boundary discontinuity. Relaxing DUPAC by 4.4 raises the chance of gentle-density (2–3 unit) construction by 14.4%. Relaxing DUPAC by 4.1 raises the chance of high-density construction by 34.1%.
- Price simulation: small changes only (+10% DUPAC, +10 ft height) and local. In spatial analysis, "no statistically significant effects on the supply of four-plus-unit housing."

### 5. Büchler & Lutz — S
- "Making housing affordable? The local effects of relaxing land-use regulation," *J. Urban Econ.* 143 (2024) 103689. https://doi.org/10.1016/j.jue.2024.103689 ; working paper: https://ideas.repec.org/p/arz/wpaper/2022_250.html (PDF blocked)
- Abstract: effect stronger for larger upzonings, where zoning binds, and where rents are high. I did not read the size-by-dose table.

### 6. Terner Center SB 9 — V
- B. Metcalf, D. Garcia, I. Carlton, K. Macfarlane, "Will Allowing Duplexes and Lot Splits on Parcels Zoned for Single-Family Create New Homes?" Terner Center, July 2021. https://ternercenter.berkeley.edu/wp-content/uploads/2021/07/SB-9-Brief-July-2021-Final.pdf
- Universe: 7.5M single-family parcels; 6.1M eligible after exclusions; ≈ 410,000 market-feasible (5.4%); 110,000 newly feasible (1.5%).
- Fig. 4 (share of all parcels, by best new-unit count): business as usual 80/1/16/4 (none, 1, 2, 3 new). Under SB 9: 78/1/12/7/2 (none, 1, 2, 3, 4 new).
- "Duplexes would be the most dominant form"; lot splits ≈ 10% of new units.
- This is the closest **published analogue to "how many offices choose 5 or 6"**: each step up in allowed units is taken by a shrinking share of lots.

### 7. Portland RIP sixplex — V
- BPS memo, "Deeper Affordability Bonus Feasibility Study," 9 Mar 2020. https://efiles.portlandoregon.gov/Record/13647537/File/Document
- Finding: "not economically feasible without other affordable housing incentives … would not be utilized by private developers."
- Inner area: lot budget $91,700 for an affordable 6-plex vs $322,300 for a triplex. 0% of 2016–2019 sales of 5,000 sq ft Inner lots were under that 6-plex budget.
- Outcome check: BPS *Middle Housing in the Single-Dwelling Zones Progress Report 2018–2024* (Jan 2025). https://www.sightline.org/wp-content/uploads/2025/06/Monitoring-reports-Middle-Housing-in-the-Single-Dwelling-Zones-Progress-Report-2018-2024-January-2025.pdf
- Demolition chart labels: fourplex 58% (224 units), sixplex 50% (6 units). That implies ≈ 386 fourplex units and ≈ 12 sixplex units. The figures are my inference from chart labels, so treat them as approximate.
- Also: 1,400+ ADU and middle units were permitted Aug 2021–Jun 2024. A 5,000 sq ft lot typically takes a fourplex.

### 8. CBO minimum wage 2019 — V
- https://www.cbo.gov/publication/55410 (PDF CBO-55410-MinimumWage2019)
- Appendix A: "employment elasticities are higher when the new minimum wage mandates a larger increase." CBO raises the elasticity with dose and reports a two-thirds range that starts near zero.
- Transferable idea: the response to a dose beyond the observed range was **not** assumed proportional. CBO judged the direction of curvature from mechanism and widened the range.

---

## What practice suggests (5 lines)
1. **No study multiplies a measured effect and its range by a capacity ratio.** Where studies extrapolate, they use a fitted functional form (São Paulo, convex by construction) or a parcel feasibility model (Terner, NZ HBAs, Portland).
2. **Planning practice uses a feasibility share:** plan-enabled → feasible → likely realized. Each extra allowed unit is feasible on fewer lots. In Terner's SB 9 model, lots feasible for ≥ 4 new homes are ≈ 22% of those feasible for ≥ 3.
3. **Direct evidence on the 5–6 step is negative-leaning.** Portland's sixplex lost value vs a triplex (commercial code costs) and drew ≈ 12 units vs ≈ 386 fourplex units. Boston found no significant 4+ unit response. Auckland land value rose less than proportionally with allowed intensity.
4. **Evidence for "bigger is more" exists, but is not proportional.** Zurich finds larger upzonings do more, and CBO raises elasticity with dose in labour markets. None of these supports a ×1.7 dose ratio for 4 → 6 homes per lot.
5. **Suggested approach:** model the extra effect as (share of lots that can fit and pencil 5–6 units) × (take-up). Keep the measured 2–4 effect as the base. Set the upper bound no higher than the dose-ratio line, and let the lower bound sit near the 2–4 result. The range comes from feasibility sensitivity, as Terner did with ±10% costs.
