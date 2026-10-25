# Eligible-property basis: ADU permits per 1,000 eligible properties

Prepared 2026-10-25 to test the owner's reframing of the same day. Status: **tested, not adopted (AQ-042).** The owner kept POOLED_REVISION option (ii) configuration A as the headline because it predicts held-out states best (RMS log error 0.113, against 0.132 for flattened permits per house and 0.168 / 0.202 for the eligible-property variants). The run without one-unit attached homes (lower 4,254, central 8,164, Strong adoption 15,318) is a sensitivity case, and the eligible-property variants are robustness checks, in the [Gate 3 packet](README.md). Everything here is in files named `eligible_basis_*`.

**The question being tested:** "How many new ADU permits per 1,000 eligible properties result from a statewide benchmark ADU law?"

- **Numerator: permits, not units.** At most 1 per parcel per year. A parcel is a distinct APN or parcel id, or the normalised site address where there is no id.
- **Denominator: properties eligible under each place's actual ADU law.** Wisconsin's benchmark scenario covers parcels with an existing single-family home, so Wisconsin's denominator stays at one-unit detached homes.

**Owner decisions applied (2026-10-25):**
- California stays in the between-state common level (configuration A).
- Madison follows the observed Madison-like path: 0.452, 0.542, 0.601, 0.799, 1.076 permits per 1,000 one-unit detached homes per year in years 1–5. The result without the path is shown as a line.
- "Strong adoption" is the configuration's 90th-percentile upper, not California's level.
- California: no LA calibration. The cap is unnecessary under flattening; results are shown with and without it.

**Units used throughout.** Unless a sentence says otherwise:
- A **rate** is ADU permits (flattened) issued in a year ÷ thousands of eligible properties. Eligible properties come from ACS 2020–2024 B25024, as defined in section 1.
- **Additional permits** are Wisconsin with-law permits minus the current-law baseline, summed over 2027–2031, from the engine. The engine baseline is **636 permits over 2027–2031**: the 645 of POOLED_REVISION × 0.987, the Wisconsin flattening factor in section 2.
- A **log error** is log(predicted rate ÷ observed rate) for a held-out state over its post-law years. **RMS** is taken over the 7 non-California statewide-law states.

All results describe associations across states and places. They are not causal effects.

## Plain-language summary

- **Wisconsin, main eligible-basis run (configuration A, Madison on the observed path):**
  - Lower **3,920**, central **7,532**, Strong adoption **14,126** additional permits over 2027–2031.
  - With Madison at the pooled level instead: 3,911 / 7,665 / 14,519.
  - The POOLED_REVISION main candidate, option (ii) cap + A2, had a central of 8,912 (8,721 with Madison on the path). Option (iii), LA-calibrated, had 8,579 (8,402).
- **Where the 1,189-permit drop comes from.** The comparison is option (ii) 8,721 → 7,532, with Madison on the path in both.
  - Numerator change, −247 (8,721 → 8,474): flattened permits, multifamily-lot ADUs put back in, and the Minneapolis duplex adjustment dropped.
  - Multifamily properties in the denominator, −310 (8,474 → 8,164).
  - One-unit attached homes in the denominator, −632 (8,164 → 7,532).
  - So the largest single step is not multifamily at all. It is counting California's (and Massachusetts', Washington's, Vermont's) townhouses and other one-unit attached homes as eligible.
- **California 2023–2025, 369 grouped non-holdout jurisdictions:**

  | Basis | Numerator | Denominator (property-years) | Rate per 1,000 per year |
  | --- | ---: | ---: | ---: |
  | As used (ADU units per one-unit detached home) | 76,927 units | 20,009,419 | 3.84 |
  | Cap + A2 (POOLED_REVISION option ii) | 71,441 units | 20,009,419 | 3.57 |
  | Cap + LA-calibrated (option iii) | 58,565 units | 20,009,419 | 2.93 |
  | Flattened permits per one-unit detached home | 66,675 permits | 20,009,419 | 3.33 |
  | Flattened permits per (detached + multifamily properties) | 66,675 permits | 21,299,693 | 3.13 |
  | **Eligible basis, central** (detached + attached + multifamily) | 66,675 permits | 23,962,830 | **2.78** |
  | Eligible basis, low / high denominator | 66,675 permits | 23,886,700 / 25,695,950 | 2.79 / 2.60 |
  | Eligible basis, with the 2-parcel-year cap | 66,594 permits | 23,962,830 | 2.78 |
  | Single-family-lot rate implied by the LA County propensity ratio | — | — | 2.56 (ratio 2.61) to 2.75 (ratio 1.24) |

- **G3F-2 still picks A, but the eligible basis predicts held-out states worse.**
  - RMS log error: A **0.202**, B 0.217, best C (income) 0.297. Under POOLED_REVISION option (ii) the values were 0.113 / 0.132 / 0.243.
  - Most of the damage comes from the denominator. Flattened permits on the old one-unit-detached denominator give RMS 0.132 (A) / 0.150 (B). Dropping one-unit attached homes gives 0.168 / 0.184.
  - A over B is still inside the noise. A has the lower error in 62% of state resamples. With one state removed from the data, A wins 5 of 7 times; B wins without Washington or Rhode Island.
- **Equal propensity fails, in the direction the owner suspected.**
  - In LA County, 2023–2025, an eligible multifamily property drew about 13.6 ADU permits per 1,000 per year. A one-unit detached home drew 5.2. The ratio is **2.6** (large-building sizes; 1.8 with small sizes).
  - The ratio stays above 1 in every building-size band. Leaving out the 4+-ADU complexes barely moves it (2.52).
  - The best-measured weak point pulls it down: many small multifamily parcels are two detached houses on one lot. Correcting for that gives a ratio of **1.2–1.5**.
  - Statewide, the blended California rate (2.78) therefore overstates the single-family-lot rate by about 1–9%, i.e. 2.56–2.75 permits per 1,000 per year.
  - Applied as a sensitivity (California multifamily properties weighted by the ratio of 2.64), the Wisconsin central moves from 7,532 to 7,433.
- **Verdict (section 8):** the numerator half of the reframing holds up and is cheap: flattening moves Wisconsin by under 3%. The denominator half is defensible in law, but it worsens the out-of-sample test. It also hangs on one choice the law does not settle well: whether one-unit attached homes, mostly condominium townhouses, are "eligible properties" in practice.

## 1. Denominators: eligible properties by state, from the law

Source: ACS 2020–2024 5-year B25024 (housing units by units in structure), for the same member geographies (places, county subdivisions, California jurisdictions) the pooled model already uses. Components: one-unit detached (002), one-unit attached (003), 2 (004), 3–4 (005), 5–9 (006), 10–19 (007), 20–49 (008), 50+ (009), mobile home (010). Code: [`eligible_basis.py`](../../missing_middleware/comparison/eligible_basis.py) `LAW_SCOPE`; table: [`eligible_basis_denominators.csv`](../../reference/eligible_basis_denominators.csv).

**Rules applied consistently across laws:**
- **One-unit attached (003)** counts where the law says "single-family dwelling" without "detached": CA, WA, MA, ME, RI, VT, Minneapolis, Seattle, Portland. It is left out where the law says detached: Oregon, Utah's internal ADUs, and the Austin and Denver codes. Section 4 shows that this legal rule and observed behaviour disagree.
- **Mobile homes (010)** are out of every central, because most sit in parks or on leased spaces rather than on their own lot. They are in the high wherever the law covers single-family dwellings.
- Each scenario combines a law reading with building sizes. **Low** = narrow law reading with very large buildings (fewest properties). **Central** = central reading with large buildings. **High** = broad reading with small buildings and mobile homes.

| State or city | Law (basis) | Central components | Legal status | Eligible ÷ one-unit detached: low / central / high |
| --- | --- | --- | --- | --- |
| California | Gov. Code 66314 (lot with an existing or proposed single-family or multifamily dwelling); 66323 (multifamily: conversions of non-livable space, up to 2 detached, up to 8 from 2025 under SB 1211) | detached, attached, all multifamily | source_lead for the multifamily scope (leginfo returned 403 here) | 1.189 / **1.192** / 1.278 |
| Washington | RCW 36.70A.681: two ADUs on lots in UGA zones that allow single-family homes. RCW 36.70A.696(1): ADU on a lot with "a single-family housing unit, duplex, triplex, townhome or other housing unit" | detached, attached, 2, 3–4 (the mandate is zone-based, so large apartments in multifamily-only zones are out) | verified (RCW text, partly truncated) | 1.082 / **1.128** / 1.228 |
| Oregon | ORS 197.312(5): an ADU for each detached single-family dwelling | detached | verified (repo law table) | 1.000 / **1.000** / 1.178 |
| Rhode Island | RIGL 45-24-73 (2024): single-family lots. Whether the 2022 law reaches multi-unit dwellings could not be re-read (rilegislature.gov refused connections) | detached, attached; 2 and 3–4 only in the high | **unknown** (multifamily scope) | 1.000 / **1.072** / 1.235 |
| Massachusetts | c.40A s.3: one protected-use ADU in single-family residential districts, on a lot with a principal dwelling (760 CMR 71.02) | detached, attached, 2, 3–4 | source_lead (pages refused or 403 here) | 1.000 / **1.258** / 1.328 |
| Maine | 30-A MRSA 4364-B(1),(3)(A): ADU on a lot with a single-family dwelling or a 2-unit or 3-unit structure | detached, attached, 2, half of 3–4 | verified (statute read) | 1.070 / **1.080** / 1.213 |
| Utah | 10-21-303: internal ADU within an owner-occupied detached primary dwelling | detached | source_lead | 1.000 / **1.000** / 1.120 |
| Vermont | 24 V.S.A. 4412(1)(E): one ADU within or appurtenant to a single-family dwelling | detached, attached | verified (statute read) | 1.000 / **1.181** / 1.246 |
| Minneapolis | 2014 ordinance: single- and two-family homes (owner direction) | detached, attached, 2 | verified (repo) | 1.189 in every scenario |
| Seattle | SMC 23.44.041 (to 2025), single-family lots | detached, attached | source_lead | 1.000 / **1.167** / 1.225 |
| Portland | 33.205: house, attached house, manufactured home | detached, attached | source_lead | 1.000 / **1.099** / 1.150 |
| Austin, Denver | secondary apartment / ADU accessory to a single-unit house | detached | source_lead | 1.000 / **1.000** / 1.118, 1.218 |

The legal statuses for Oregon, Rhode Island, Massachusetts, Utah, California's multifamily scope and the four cities are partly from the repo's law table and statute summaries. Official pages for them refused connections or returned 403/404 on 2026-10-25. They should be re-read before adoption.

### Multifamily properties: housing units → buildings → parcels

- **Buildings.** Each band's housing units are divided by an assumed number of units per building:

  | Size set | 2 | 3–4 | 5–9 | 10–19 | 20–49 | 50+ | California multifamily properties (statewide) |
  | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
  | small (band bottom) | 2 | 3 | 5 | 10 | 20 | 50 | 738,033 |
  | mid (band midpoint) | 2 | 3.5 | 7 | 14.5 | 34.5 | 100 | 602,617 |
  | **large (band top; central)** | 2 | 4 | 9 | 19 | 49 | 150 | **525,727** |
  | very large (large × 1.25 buildings per parcel on 5+ bands) | 2 | 4 | 11.25 | 23.75 | 61.25 | 187.5 | 495,106 |

  Statewide one-unit detached homes are 8,354,468, so multifamily properties are 5.9–8.8% of them.

- **Why "large" is the central (owner, 2026-10-25).** The law adds at most a few ADUs to a property however big the complex, so a complex should count as few properties. The A2 data agree with that logic:
  - Statewide, in 2023–2025, 90.3% of ADU parcel-years had 1 ADU unit, 8.2% had 2, 0.6% had 3, and 0.9% had 4+ (70,789 / 6,394 / 505 / 681 of 78,369 parcel-years). The 4+ parcel-years hold 5.3% of ADU units (4,763 of 89,855). Source: [`eligible_basis_a2_adu_per_parcel.csv`](../../reference/eligible_basis_a2_adu_per_parcel.csv).
  - In LA County (assessor rolls), a 4+-ADU parcel-year is rare on small buildings. Among multifamily-lot ADU parcel-years, it is 0.6% on 2-unit lots and 2.1% on 3–4-unit lots, but 18% on 20–49-unit lots and 31% on 50+-unit lots. So 4+-ADU parcels mark the large complexes, as the owner expected. Parcels with 1–3 ADUs on multifamily lots are mostly small buildings: 72% of them have 2–4 existing units (4,399 of 6,119 parcel-years).
- **The choice barely matters for the rate**, because small buildings dominate the count of multifamily properties. California 2023–2025 runs from 2.72 (small) to 2.79 (very large) permits per 1,000 eligible properties per year. The Wisconsin central runs from 7,485 to 7,536.

### Building vs parcel (weak point 1, measured)

- **HCD A2 cannot count the existing multifamily stock.** It lists only parcels that received a permit. It is used here only to profile ADU parcels: ADUs per parcel, and the existing units on the parcel via the LA assessor match.
- **Overstatement (complexes).** A complex of several buildings on one parcel counts as several properties. Among LA County 5+-unit ADU parcels, 23% have 2+ building records (mean 1.39). The "very large" size set allows for this (1.25 buildings per parcel), and it moves the California rate by 0.3%.
- **Understatement (small lots with two buildings), the larger effect.** Many small multifamily parcels are not one 2-unit or 3–4-unit structure:
  - Among LA County 2-unit ADU parcels, 49% have 2+ building records (often two detached houses). Among 3–4-unit parcels, 56% do.
  - ACS counts those houses as one-unit detached. So B25024 understates small multifamily parcels and overstates single-family parcels.
  - Scaling the 2 and 3–4 bands by 1 ÷ (1 − that share) raises LA County multifamily properties from 157,107 to 269,548. It could also take up to 321,108 units out of LA's 1,726,695 one-unit detached homes (an upper bound: it assumes all are detached).
  - This matters mostly for the propensity test (section 4), not for the totals. Statewide, it moves properties between the single-family and multifamily columns and changes their sum little.
- **Condominiums.** ACS multifamily units include condominium buildings. Legally these are multifamily structures, but in LA County condo/PUD parcels drew only 9 ADU parcel-years in 2023–2025, against 26,329 on single-family lots.

## 2. Numerators flattened to permits

Table: [`eligible_basis_numerators.csv`](../../reference/eligible_basis_numerators.csv). Site keys are built in memory; no address leaves `data/raw`.

| Source | Key | Years | Units | Permits (parcel-years) | Units per permit |
| --- | --- | --- | ---: | ---: | ---: |
| California A2, study main measure, statewide | APN (97.6–99.9% of rows), else address | 2023 | 28,256 | 25,212 | 1.121 |
| | | 2024 | 30,338 | 26,310 | 1.153 |
| | | 2025 | 31,945 | 27,508 | 1.161 |
| California A2, all ADU rows with an APN (owner's check) | APN | 2023 | 35,054 | 31,424 | 1.116 |
| Seattle (Washington allows 2 per lot) | address | 2021–2024 | 3,462 | 3,156 | 1.097 |
| Portland | property id | 2019–2022 | 1,092 | 1,051 | 1.039 |
| Austin | TCAD parcel | 2016–2023 | 2,549 | 2,465 | 1.034 |
| Denver | schedule number | 2016–2025 | 643 | 629 | 1.022 |
| Minneapolis | APN (already 1 per 24 months) | 2017–2025 | 198 | 198 | 1.000 |
| Wisconsin: Madison, Sun Prairie, Pleasant Prairie (parcel id, else address); Milwaukee central candidates (address) | | 2022–2025 | 76 | 75 | 1.013 |

- **The owner's California figure is reproduced.** The owner had 34,959 units on 31,334 parcels in 2023; this run gets 35,054 on 31,424, about 1.12. It covers every A2 ADU row with permitted units and an APN, including late reports. The study's main measure is used in the model: 79,030 permits from 90,539 units over 2023–2025, all jurisdictions (1.15). For the 369 jurisdictions in the California rate it is 66,675 permits.
- **The cap is redundant once flattened.** Capping at 2 parcel-years per parcel, cumulated 2018–2025, removes 81 of 66,675 permits in the 369 jurisdictions over 2023–2025.
- **State series with unit counts only:**
  - Washington (OFM): × **0.912**, Seattle's 2021–2024 permits ÷ units. It is the closest parcel data under a 2-per-lot rule.
  - Oregon (DLCD): × **0.962**, Portland's 2019–2022 ratio.
  - Rhode Island, Massachusetts, Maine, Utah, Vermont: × 1. Each law allows one ADU per lot, so a parcel-year is about one unit.
- **Wisconsin:** × **0.987** (75 parcel-years ÷ 76 permits, 2022–2025), applied to every area's current-law rate, the baseline and the Madison floor. The floor becomes 0.2345 × 0.987 = 0.2314.
- **Kept from POOLED_REVISION:** the vacant-lot factor × 0.951 on non-California series that include ADUs built with a new house.
- **Dropped:** the Minneapolis duplex-lot adjustment (× 0.873). Duplex lots are now in Minneapolis's denominator, so their ADUs belong in the numerator. The California A2 multifamily-lot removal is dropped for the same reason.

## 3. G3F-2 on the eligible basis

Files: [`eligible_basis_g3f2.csv`](../../reference/eligible_basis_g3f2.csv), [`eligible_basis_loso.csv`](../../reference/eligible_basis_loso.csv). The method is as in POOLED_REVISION section 2: 5,000 resamples, and each state dropped from the data in turn.

| Run | A: CA in | B: CA out | Best C (income) | A's share of resamples | A wins with one state removed (of 7) | A, RMS range with one state removed |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| POOLED_REVISION option (ii), units per one-unit detached home (for comparison) | 0.113 | 0.132 | 0.243 | 66% | 5 | 0.108–0.159 |
| Flattened permits per one-unit detached home (numerator change only) | 0.132 | 0.150 | 0.257 | 66% | 5 | 0.132–0.175 |
| **Eligible basis (main)** | **0.202** | 0.217 | 0.297 | 62% | 5 | 0.186–0.236 |
| Eligible basis, with the cap | 0.202 | 0.217 | 0.297 | 62% | 5 | 0.186–0.236 |
| Eligible basis without one-unit attached | 0.168 | 0.184 | 0.279 | 62% | 5 | 0.153–0.202 |

Log error by held-out state, eligible basis, configuration A:

| WA | OR | RI | MA | ME | UT | VT | Mean |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| +0.30 | −0.04 | −0.12 | +0.31 | −0.06 | −0.23 | +0.16 | +0.045 |

- **A still wins** in every run; B wins only without Washington or Rhode Island, as before.
- **Why the fit worsens.** The eligible basis raises the denominators of Massachusetts (× 1.26), Vermont (× 1.18) and Washington (× 1.13) but not of Utah or Oregon (× 1.00). The model then over-predicts the first three and under-predicts Utah more. Under the old basis the states' rates per single-family home were more alike than their rates per eligible property.
- This is evidence about the states' actual behaviour: permits track the stock of detached houses more closely than the legal eligibility count. It is not evidence about the law itself.

## 4. Equal propensity: LA County test (weak point 2, measured)

Files: [`eligible_basis_propensity_la.csv`](../../reference/eligible_basis_propensity_la.csv), [`eligible_basis_parcel_check.csv`](../../reference/eligible_basis_parcel_check.csv).
- Numerator: LA County A2 permits flattened to parcel-years. Each is classed by the assessor roll of its report year (single-family, 2, 3–4, 5+ units); unmatched permits are spread pro rata.
- Denominators, from LA County ACS B25024 (0500000US06037): 1,726,695 one-unit detached homes; multifamily properties 228,911 (small sizes), 182,602 (mid), 157,107 (large), 145,918 (very large).

| Year | Permits | On SF lots | On MF lots | SF rate | MF rate (large) | MF ÷ SF: small / mid / large |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2018 | 4,923 | 4,812 | 87 | 2.79 | 0.55 | 0.14 / 0.17 / 0.20 |
| 2019 | 6,675 | 6,475 | 141 | 3.75 | 0.90 | 0.16 / 0.21 / 0.24 |
| 2020 | 5,440 | 4,932 | 456 | 2.86 | 2.90 | 0.70 / 0.87 / 1.02 |
| 2021 | 8,584 | 7,192 | 1,268 | 4.17 | 8.07 | 1.33 / 1.67 / 1.94 |
| 2022 | 11,153 | 8,846 | 2,094 | 5.12 | 13.33 | 1.79 / 2.24 / 2.60 |
| 2023 | 10,869 | 8,419 | 2,177 | 4.88 | 13.86 | 1.95 / 2.45 / 2.84 |
| 2024 | 11,227 | 8,872 | 2,114 | 5.14 | 13.46 | 1.80 / 2.25 / 2.62 |
| 2025 | 11,739 | 9,404 | 2,124 | 5.45 | 13.52 | 1.70 / 2.14 / 2.48 |

Rates are permits per 1,000 properties per year. Before 2020, multifamily lots had little ADU access; SB 13 and AB 68 opened them from 2020.

**By building size, 2023–2025** (matched parcel-years ÷ 3 ÷ properties × 1,000; band set by the parcel's existing units):

| Lot | Parcel-years | Properties | Rate | Share with 4+ ADUs |
| --- | ---: | ---: | ---: | ---: |
| one-unit detached | 26,329 | 1,726,695 | 5.08 | — |
| 2 units | 2,769 | 47,711 | 19.3 | 0.6% |
| 3–4 | 1,682 | 53,452 | 10.5 | 2.1% |
| 5–9 | 976 | 31,665 | 10.3 | 3.3% |
| 10–19 | 458 | 14,658 | 10.4 | 8.1% |
| 20–49 | 274 | 6,872 | 13.3 | 18.2% |
| 50+ | 99 | 2,749 | 12.0 | 31.3% |

**What drives the ratio** (2023–2025, multifamily ÷ single-family rate):

| Variant | Ratio |
| --- | ---: |
| ACS buildings, large sizes | 2.61 |
| Same, leaving out 4+-ADU parcel-years (the large complexes) | 2.52 |
| Parcel-corrected: small multifamily lots that are two buildings, multifamily side only | 1.52 |
| Parcel-corrected on both sides (upper bound on the units moved out of single-family) | 1.24 |

**Reading:**
- An eligible multifamily property in LA County was **1.2–2.8 times** as likely to get an ADU permit as a single-family one in 2022–2025. The ratio is higher than 1 in every building band.
- The large complexes are not what drives it: leaving them out takes the ratio from 2.61 to 2.52. Under the owner's view (a 200-apartment complex with 40 conversion ADUs counts once), it remains well above 1.
- The best-supported range is 1.2–1.5, after the parcel correction. The 2-unit band's 19.3 is the most inflated by the two-houses-on-one-lot issue.
- **California statewide.** Statewide there are 9,440,507 one-unit homes (detached + attached) and 525,727 multifamily properties. If the multifamily ratio is ρ, the single-family-lot rate is 2.78 × (S + M) ÷ (S + ρM):

  | ρ | Single-family-lot rate | Blended overstates it by |
  | ---: | ---: | ---: |
  | 2.61 | 2.56 | 8.5% |
  | 1.52 | 2.71 | 2.8% |
  | 1.24 | 2.75 | 1.2% |

  This assumes LA's ratio holds statewide. LA has the largest multifamily-lot ADU share in the state, so it is probably an upper bound.
- **One-unit attached homes: an untested propensity, and a large denominator item.** California has 1,086,039 one-unit attached homes, twice its 525,727 multifamily properties. LA condominium/PUD parcels got 9 ADU parcel-years in 2023–2025. If one-unit attached homes behave like condominiums, equal propensity fails far worse for them than for multifamily. Dropping them moves the Wisconsin central from 7,532 to 8,164 and improves G3F-2 (0.202 → 0.168).

## 5. Wisconsin engine outputs on the eligible basis

File: [`eligible_basis_wi.csv`](../../reference/eligible_basis_wi.csv).
- Engine baseline: 636 permits over 2027–2031.
- Floor: 0.2314 permits per 1,000 one-unit detached homes per year.
- Path ramps (main): central 0.67, 0.84, 0.85, 1, 1; lower 0.65, 0.82, 0.84, 1, 1; upper 0.68, 0.84, 0.86, 1, 1.
- Values are additional permits over 2027–2031; "Madison path" = the owner's decision.

| | Eligible basis, main (A) | POOLED_REVISION (ii) cap + A2 | POOLED_REVISION (iii) LA-calibrated |
| --- | ---: | ---: | ---: |
| Baseline | 636 | 645 | 645 |
| **Lower**, Madison path | **3,920** | — | — |
| Lower, Madison pooled | 3,911 | 4,424 | 4,586 |
| **Central**, Madison path | **7,532** | 8,721 | 8,402 |
| Central, Madison pooled (line) | 7,665 | 8,912 | 8,579 |
| **Strong adoption** (90th percentile), Madison path | **14,126** | — | — |
| Strong adoption, Madison pooled | 14,519 | 17,374 | 15,621 |
| Wisconsin at California's own level (for reference) | 18,344 | 22,694 | 19,150 |
| Central rate, 2027 → year 4+ (per 1,000 one-unit detached homes per year) | 0.71 → 1.03 | 0.79 → 1.21 | 0.79 → 1.14 |
| Between-state spread τ (8 states); 80% factor | 0.40; × or ÷ 1.83 | 0.42; × or ÷ 1.89 | 0.38; × or ÷ 1.76 |
| Common level / California level (law in force, year 4+, typical place) | 0.88 / 2.00 | 1.00 / 2.45 | — / 2.08 |
| Adoption reference line (median observed path, vacant-lot rule) | 7,736 | 8,208 | 8,208 |
| Sensitivity: multiplicative law | 674 | 722 | 683 |
| Sensitivity: California-only market regression (permits per eligible property) | 2,095 | 2,361 | 2,185 |
| Sensitivity: no ramp | 8,793 | 10,476 | 9,879 |
| Sensitivity: rural places at the floor | 4,337 | 4,921 | 4,776 |

Notes:
- Madison's own addition: 136 permits on the path against 269 at the pooled central level.
- The POOLED_REVISION lower and upper figures were published only with Madison at the pooled level.
- The four sensitivity rows have Madison at the pooled level, as in POOLED_REVISION.
- Adoption line rates: 0.66, 0.78, 0.74, 1.18, 1.18 permits per 1,000 eligible properties per year.
- Each state's level (law in force, year 4+, typical place) is in [`eligible_basis_stage2_levels.csv`](../../reference/eligible_basis_stage2_levels.csv): CA 2.00, UT 1.07, WA 0.97, ME 0.93, VT 0.76, MA 0.67, OR 0.62, RI 0.58. Wisconsin's year-4+ rate under "Strong adoption" is 1.87, which is again above every state's level except California's (2.00).

**Sensitivities on the eligible basis** (central, Madison path; lower and Strong adoption in brackets):

| Run | Central [lower, Strong adoption] |
| --- | ---: |
| Main | 7,532 [3,920, 14,126] |
| With the 2-parcel-year cap | 7,530 [3,920, 14,119] |
| Configuration B (owner chose A; information only) | 6,642 [4,453, 9,807] |
| Denominator low (narrow law reading, very large buildings) | 8,082 [4,457, 14,381] |
| Denominator high (broad reading, small buildings, mobile homes) | 6,828 [3,493, 12,985] |
| Without one-unit attached homes | 8,164 [4,254, 15,318] |
| Propensity-adjusted (California multifamily properties × 2.64) | 7,433 [4,010, 13,477] |
| Size set small / mid / very large | 7,485 / 7,514 / 7,536 |
| Numerator only (flattened permits per one-unit detached home) | 8,474 [4,361, 16,101] |

## 6. California's 2023–2025 rate under each basis

See the table in the summary. As used **3.84** (ADU units per one-unit detached home). Cap + A2 **3.57**. LA-calibrated **2.93**. Eligible basis per permit **2.78** (2.60–2.79 over the denominator scenarios; 3.13 without one-unit attached homes).

All are for the 369 grouped non-holdout jurisdictions with reports, 2023–2025: 20,009,419 one-unit-detached home-years and 23,962,830 eligible property-years. Source: [`eligible_basis_ca_rates.csv`](../../reference/eligible_basis_ca_rates.csv).

## 7. Deviations and limits

1. **Pooled model mechanics.** Eligible properties replace one-unit detached homes as each member's exposure. The size term (log of properties) and the state-context weights follow from that. Wisconsin's prediction still uses its one-unit detached homes, which is its eligible count under the benchmark.
2. **Building sizes.** The units-per-building assumptions are by band. The 50+ band mean (150 central) is assumed; the range 50–187.5 is shown.
3. **Legal scope.** It is partly source_lead (section 1 table). Rhode Island's multifamily scope is unknown.
4. **The LA propensity test:**
   - It is one county, and it uses assessor classes at the roll of the permit year.
   - The parcel correction rests on building-record counts among ADU parcels. These may not represent all small multifamily parcels.
5. **Unit-to-permit factors.** Washington's and Oregon's factors come from their largest city (Seattle, Portland). The Madison-like path is used as published (in units per one-unit detached home); flattening would lower it by about 1–9%.
6. **G3F-2 scores 5 configurations on the same 7 states**, so the winner's RMS is optimistic.

## 8. Verdict

**The reframing holds up in part.**

- **Numerator: adopt.** Counting a permit once per parcel per year in every source is clean and consistent. It reproduces the owner's 1.12 units per parcel-year. It makes the California cap and the A2 multifamily-lot removal unnecessary. It moves Wisconsin's central by about 3% (8,721 → 8,474 with Madison on the path).
- **Denominator: defensible in law, but fragile in practice.** It has three weak points:
  1. **Equal propensity is false in LA County.** Multifamily properties draw 1.2–2.8 times as many ADU permits per property as single-family ones. The effect on the blended California rate is small (it overstates the single-family-lot rate by about 1–9%), because there are few multifamily properties next to houses.
  2. **One-unit attached homes are the largest denominator item, and the least likely to get ADUs in practice.** Most are condominium townhouses, and LA condo/PUD parcels drew almost none. Including them is what the law literally allows. It removes about 630 Wisconsin permits and worsens the cross-state test the most.
  3. **The cross-state test worsens.** G3F-2 RMS rises from 0.113 (option ii) to 0.202. States' ADU permits follow their detached-house stock more closely than their legal eligibility counts. Configuration A still wins, inside the noise as before.
- **If the owner adopts the eligible basis,** the evidence favours this central: flattened permits ÷ (one-unit detached + multifamily properties at large building sizes), without one-unit attached homes. California 2023–2025 would then be **3.13** permits per 1,000 eligible properties per year, and Wisconsin **8,164** [4,254, 15,318] with Madison on the path. That is within 7% of the POOLED_REVISION option (ii) result, so the headline story would not change.

## Reproduce

```
uv run python scripts/run_eligible_basis.py      # about 60 seconds; writes reference/eligible_basis_*.csv
uv run --with pytest python -m pytest -q          # includes tests/test_eligible_basis.py
```

Code: [`eligible_basis.py`](../../missing_middleware/comparison/eligible_basis.py), [`run_eligible_basis.py`](../../scripts/run_eligible_basis.py) (reuses `pooled_revision.py` and `run_pooled_revision.py`). Tests: [`test_eligible_basis.py`](../../tests/test_eligible_basis.py).

All inputs are already local: no new datasets and no downloads. The statute pages consulted on 2026-10-25 were read only for legal scope.
