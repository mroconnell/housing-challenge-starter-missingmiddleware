# States with statewide ADU laws: is there post-law permit data?

Gate 3 add-on, owner question of 2026-10-24: do any of the 18 states with a statewide ADU law have ADU permit data for 1–5 years after the law took effect, so the statewide-law ("industry formation") effect assumed for Wisconsin (AQ-024, AQ-027, AQ-034) can be checked outside California? This is **not** part of the pre-registered [CA_COMPARISON_PLAN.md](CA_COMPARISON_PLAN.md) and changes nothing in it. City series already built in [OTHER_CITIES.md](OTHER_CITIES.md) (Seattle, Portland, Austin, Denver, Minneapolis) are reused, not redone.

**All numbers are descriptive.** Every state changed its law while interest rates, construction costs and local rules were also changing, and there is no comparison state. A rate that rose after a law is *associated with* the law; it is not an estimate of the law's effect.

## Plain-language summary

- **Yes, but only a few states, and mostly for 1–4 years.** Six of the 18 states have an official ADU count after their law. Only two have statewide or near-statewide counts covering several post-law years: **Oregon** (4 years) and **Washington** (2 years after enactment; compliance only began in mid-2025). **Rhode Island** is the only state with official statewide counts both before and after its law, but for just one post-law year.
- **Five states have nothing usable yet.** Arkansas, Iowa and Nevada passed laws too recently. Connecticut has no ADU count at all. Hawaii and Maryland only had to comply in 2026.
- **The first years after a state law look similar across states: about 0.8–1.1 ADUs per 1,000 one-unit detached homes a year.** That holds for Oregon cities outside Portland (0.90), Washington cities outside Seattle (0.75–0.84), Rhode Island (0.97), Massachusetts (0.79), Maine (0.98), Utah (1.13) and Chittenden County, Vermont (0.94).
  - California's first strong law year (2017) was 0.66. California then climbed to 1.48 (2018–19) and 3.88 (2023–25) as later laws and its ADU industry built up.
  - Madison's rate is 0.16 and Minneapolis's is 0.17 ([OTHER_CITIES.md](OTHER_CITIES.md)).
  - So far no other state shows California's later climb. Most have had too few years to tell.
- **Where there is a before, the rate roughly doubled or more.**
  - **Washington cities outside Seattle:** 0.39 (2019–23) → 0.75 after enactment, before most cities had to comply.
  - **Rhode Island:** 0.23 → 0.97.
  - **Chittenden County, Vermont:** 0.62 → 0.94.
  - **Oregon cities outside Portland:** 0.46 in the law's own year → 0.90.
- **Caution on definitions.** Most state series include ADUs built with a new house, are self-reported and do not cover every town. The Wisconsin ADU-type measure excludes ADUs built with a new house, so these state rates are, if anything, high for comparison.
- **Markets.** All useful states except Maine have higher home values than Wisconsin ($266,500). Maine ($296,600) and Tucson ($266,200) are the closest; Spokane ($363,500) and Chittenden County ($439,200) are in between.
- **Top three tests of the statewide-law effect for Wisconsin:**
  1. **Washington.** It has the best data: an official statewide ADU column for 2011–2026 with a long baseline, a strong law, and city detail, including lower-value Spokane. Only the 2024–2026 years after enactment are usable now. Re-run when the 2027 and 2028 files arrive.
  2. **Oregon.** Strong law, official counts for four post-law years in cities over 10,000, but no year before the law.
  3. **Vermont (Chittenden County).** A Midwest-like market with four years of data before and after Act 179, but only regionally and under a weaker law.
  - **Maine** is the closest market and has a strong law, but only one year of data. **Rhode Island** has the only statewide before-and-after series, under a narrow law. Both are close behind.

### Summary table

Rates are ADUs per 1,000 one-unit detached homes per year (ACS 2020–2024 B25024_002 for the geography shown). "Years after" counts whole years of usable data after the law's effective date (in brackets: after the local compliance date, where different). Full table: [`reference/statewide_states_laws.csv`](../../reference/statewide_states_laws.csv).

| State | Mercatus class | Law effective (local compliance) | ADU data source | Years after law with data | Rates (before → after) |
| --- | --- | --- | --- | ---: | --- |
| California | strong | 2017-01-01 (2019 package 2020-01-01) | HCD APR Table A2, official statewide | 5+ | 0.12 (2014–16) → 0.66 (2017) → 1.48 (2018–19) → 2.46 (2020–22) → 3.88 (2023–25) |
| Washington | strong | 2023-07-23 (2025-06-30 for the four Puget Sound counties; later elsewhere) | OFM permits by structure type, official statewide | 2 (0) | Cities excl. Seattle: 0.12 (EY2011–16), 0.39 (EY2019–23) → 0.75 (EY2024–25) → 0.84 (EY2026). All areas: 0.81 → 1.07 → 1.04 |
| Oregon | strong | 2018-07-01 (HB 2001 parking/owner rules 2020-01-01) | DLCD HB 4006 reports, cities over 10,000 | 4 | 32 cities excl. Portland: 0.46 (2018, law year) → 0.90 (2019–22) |
| Montana | strong | 2024-01-01 (enjoined until 2024-09-03) | none statewide; Bozeman applications | 1 (proxy) | Bozeman 1.82 (2020–23) → 0.84 (2024) |
| Arizona | strong | 2024-09-14 (2025-01-01) | none statewide; city figures (source_lead) | 1 (proxy) | Tucson 0.48 (2022) → 0.62 (2025); Phoenix detached 0.22 (2025) |
| Colorado | strong | 2024-05-13 (2025-06-30) | none statewide | 0 | Colorado Springs 0.08 (2024, before); Denver in OTHER_CITIES.md |
| Maine | strong | signed 2022-04-27 (2024-01-01 / 2024-07-01) | MOCA housing data collection, 182 towns | 1 | 0.98 (2025; state denominator, ~73% of population reporting); Portland ME 1.22 → 1.14 |
| Massachusetts | strong | 2025-02-02 | EOHLC ADU Tracker | 1 | 0.79 (2025; 293 of 351 towns, undercount) |
| Arkansas | strong | 2025-08-05 (2026-01-01) | none | 0 | — |
| Iowa | strong | 2025-07-01 | none | 0 | — |
| New Hampshire | weaker | 2017-06-01 (HB 577 2025-07-01) | OPD survey; ADUs not split until CY2025 | 5 (proxy) | Conversions proxy 0.92 (2020–24), no baseline |
| Vermont | weaker | Act 179 2020-10-12 (by right since 2004) | Chittenden County RPC inventory (regional) | 4 | Chittenden 0.62 (2016–20) → 0.94 (2021–24) |
| Connecticut | weaker | 2022-01-01 (2023-01-01; 115 of 169 towns opted out) | none | 0 | — |
| Rhode Island | weaker | 2024-06-25 | RI EOH annual ADU report | 1 | 0.23 (2021–23) → 0.60 (2024) → 0.97 (2025) |
| Utah | weaker | 2021-10-01 (internal ADUs only) | DWS Moderate Income Housing reports | 3 | 1.13 (report years 2023–25), no baseline |
| Hawaii | weaker | 2024-05-28 (2026-12-31) | none statewide; Honolulu permits | 0 | Honolulu (own 2015 ordinance) 1.14 (2016–23), 1.31 (2024) |
| Maryland | weaker | 2025-10-01 (2026-10-01) | none statewide; Montgomery keyword count | 0 | Montgomery 0.42 (2020–25, local rules) |
| Nevada | weaker | 2026-07-01 | none | 0 | — |

**Comparison points:**
- **Madison:** 0.16 for the ADU-type part in 2022–2025, or 0.21 after dividing by 0.8.
- **Minneapolis:** 0.17 in 2021–2025.
- **California's restrictive-group plateau:** 1.23 in 2023–2025.

Sources: [WI_BASELINE.md](WI_BASELINE.md), [OTHER_CITIES.md](OTHER_CITIES.md), [CA_STUDY_RESULTS.md](CA_STUDY_RESULTS.md).

## 1. The state list (Mercatus 2025)

Hamilton and Peterson, ["A Taxonomy of State Accessory Dwelling Unit Laws 2025"](https://www.mercatus.org/research/policy-briefs/taxonomy-state-accessory-dwelling-unit-laws-2025) (August 2025). The text says 18 states have broadly legalized ADUs: 10 with strong laws and 8 with weaker ones. The tables and appendix are images, in both the local PDF text and the HTML page.

**How the list was verified:**
- **Strong (10):** Arizona, Arkansas, California, Colorado, Iowa, Maine, Massachusetts, Montana, Oregon, Washington.
  - Named in text by co-author Kol Peterson's ["Strong Statewide ADU Reform Matrix"](https://accessorydwellings.org/2025/08/07/strong-statewide-adu-reform-matrix/) (2025-08-07). **Verified.**
- **Weaker (8):** Connecticut, Hawaii, Maryland, Nevada, New Hampshire, Rhode Island, Utah, Vermont.
  - The 18 minus the 10.
  - Two secondary reproductions of Table 1 give the same list ([dmvadu.com](https://dmvadu.com/national/national-adu-trends), [Maxable](https://maxablespace.com/which-us-states-have-passed-adu-laws/)).
  - The 2024 Mercatus brief's text-readable Table 1 lists six of the eight as non-bold (weaker): NH, VT, UT, CT, RI, HI. That table rated Massachusetts weaker in 2024; its 2025 law made it strong. MD and NV were added in 2025.
  - **Source_lead:** the 2025 image table itself was not read.
- **Strong, as Mercatus defines it:** the state bars all three of Peterson's "poison pills" (owner occupancy, extra parking, discretionary review) and requires both attached and detached ADUs.
  - Maine is classed strong, although its owner-occupancy ban (LD 1829) arrives later.

## 2. Laws, by state

Provisions describe what localities may not do. They were verified on the statute or an official summary unless marked source_lead; dates, provisions and sources are in [`reference/statewide_states_laws.csv`](../../reference/statewide_states_laws.csv).

**Benchmark** (SCOPE_AND_MODEL.md): one ADU by right on every lot with a house, detached and attached, at least 600 sq ft, no extra parking, and (modeled) no owner occupancy.

**Closest to the benchmark:** Washington, Montana, Arizona, Arkansas, Iowa, Massachusetts and California.

**Further from it:**
- **Oregon:** reasonable siting and design rules still apply.
- **Maine:** conditional-use review survives where housing is conditional, and owner occupancy is allowed until LD 1829.
- **Colorado:** covers 67 metro jurisdictions only.
- **The weaker eight:**
  - New Hampshire: owner occupancy allowed; attached only until 2025.
  - Utah: internal ADUs only, owner occupancy allowed.
  - Rhode Island: by right only on lots of 20,000+ sq ft or inside existing footprints.
  - Connecticut: opt-out.
  - Hawaii: standards left to counties.
  - Maryland: silent on owner occupancy.
  - Nevada: local ordinance required.
  - Vermont: by-right since 2004; size and parking eased in 2020 and 2023.

| State | Key law(s) | By right | Owner occupancy banned | Parking | Size | Fees |
| --- | --- | --- | --- | --- | --- | --- |
| CA | AB 2299/SB 1069 (2016), 2017 and 2019 packages | yes | yes (2020) | none near transit; max 1 | 800 sq ft must be allowed | no impact fee < 750 sq ft |
| WA | EHB 1337 (RCW 36.70A.680–.681) | yes | yes | none near major transit; else 1–2 | cap ≥ 1,000 sq ft; two ADUs | impact fee ≤ 50% |
| OR | SB 1051 / HB 4031; HB 2001 | partial | yes (2020) | none (2020) | not set | — |
| MT | SB 528 (MCA 76-2-345) | yes | yes | none | cap 75% / 1,000 sq ft | no impact fee; $250 cap |
| AZ | HB 2720 (A.R.S. 9-461.18), cities > 75k | yes | yes for long-term rentals | none | cap 75% / 1,000 sq ft | — |
| CO | HB24-1152, 67 jurisdictions | yes | yes | none new | 500–750 sq ft protected | — |
| ME | LD 2003 (30-A MRSA 4364-B), LD 1706 dates | partial | later (LD 1829) | none extra | min 190 sq ft | — |
| MA | Ch. 150 Acts 2024 (c.40A s.3) | yes | yes | max 1; none near transit | up to 900 sq ft protected | — |
| AR | Act 313 of 2025 | yes | yes | none | cap 75% / 1,000 sq ft | $250 caps |
| IA | SF 592 (2025) | yes | yes | none | cap ≥ max(1,000 sq ft, 50%) | same as house |
| NH | SB 146 (2016); HB 577 (2025) | no → yes (2025) | no | 2025: max 1 extra | cap ≥ 750 sq ft | — |
| VT | 24 V.S.A. 4412; Act 179; Act 47 | yes | unclear | max 1 in sewer areas (2024-12) | cap ≥ max(30%, 900 sq ft) | — |
| CT | PA 21-29 (CGS 8-2o), opt-out | yes where not opted out | effectively | max 1 | cap ≥ min(30%, 1,000 sq ft) | no new utility fees |
| RI | P.L. 2024 ch. 284/285 (45-24-73) | limited lots | no | max 1 per bedroom | cap ≥ 900 / 1,200 sq ft | ≤ single-family fees |
| UT | HB 82 (2021) | internal only | no | may require 1 | not relative to house | — |
| HI | Act 39 (2024) | no | no | — | — | scaled to size |
| MD | HB 1466 (2025) | yes (ministerial) | no | none near transit; else max 1 | — | none < 750 sq ft |
| NV | AB 396 (2025) | no | no | max 1, conditional | — | — |

Notes:
- Montana's law was enjoined from 2023-12-29 until the Montana Supreme Court reversed on 2024-09-03; the merits ruling upheld it on 2025-03-03.
- Washington's 1993 law (RCW 43.63A.215) required local ADU rules but allowed discretionary permits; it was repealed in 2023.
- Maine's original compliance date was 2023-07-01. LD 1706 moved it to 2024-01-01 for councils and 2024-07-01 for town-meeting towns.

## 3. ADU permit data, by state

Annual counts: [`reference/statewide_states_annual.csv`](../../reference/statewide_states_annual.csv). Each row carries its source and status (observed = read from the official file; source_lead = news or vendor figure).

**Official statewide or near-statewide ADU counts**

- **Washington (OFM).**
  - **Source:** "Reported Permits, Completions and Demolitions by Structure Type", one row per city or county per estimate year (EY = April 2 of the previous year to April 1). ADU permits are their own column from 2011.
  - **Coverage gap:** unincorporated areas report ADUs only from EY2021. The consistent series is therefore incorporated places excluding Seattle (280 cities and towns, 1,058,941 one-unit detached homes).
  - **Counts, cities and towns excluding Seattle:** 101 (EY2011) → 306 (EY2019) → 617 (EY2023) → 717, 861, 888 (EY2024–26).
  - **Seattle:** 872 in EY2026.
  - **Cross-check:** OFM's own 2026 Population Trends report says 2,135 ADUs were completed in Apr 2025–Mar 2026; the workbook gives 2,157.
  - **Timing:** HB 1337 binds King, Pierce, Snohomish and Kitsap cities from 2025-06-30, other western counties from about 2025-12-31, and Spokane and eastern counties from 2026-12-31 or later. So only EY2026 is even partly post-compliance.
  - **What the rise shows:** most of it came after enactment but before compliance. That fits cities adopting early, an industry anticipating the law, or both.
- **Oregon (DLCD HB 4006).**
  - **Source:** annual summaries for cities over 10,000 people, 2018–2023.
  - **Statewide totals:** 795, 657, 544, 605, 640 (2018–22).
  - **Portland:** 614 in 2018 falling to 276 in 2022. This is the end of the fee waiver ([OTHER_CITIES.md](OTHER_CITIES.md)).
  - **Panel used here:** the 32 cities that reported every year, excluding Portland: 166, 289, 357, 333, 335.
  - **Gaps:**
    - 2023 is incomplete (no Portland, Hillsboro or Tigard).
    - From 2024 the survey moved to Portland State University; no ADU tables were found.
    - Reporting started in 2018, the law's own year, so there is no pre-law year.
- **Rhode Island (EOH annual ADU report, RIGL 45-24-76).**
  - **Permits:** 62, 53, 71, 163, 262 (2021–25).
  - **Certificates of occupancy:** 33, 44, 38, 66, 82.
  - **Coverage:** self-reported; 32 of 39 municipalities reported 2025 (Pawtucket missing). Coverage for 2021–23 is not stated.
  - **Conflicting figure:** a Boston Globe commentary cites 11 for 2021 from the Housing Fact Book (not verified).
- **Massachusetts (EOHLC ADU Tracker).**
  - **2025:** 1,224 ADU building permits and 1,639 applications, from 293 of 351 municipalities. It is an undercount; 65 towns gave first-half figures only.
  - **Cumulative to June 2026:** 2,084 permits.
  - **Mix:** half detached.
  - **Before the law:** no statewide count.
- **Maine (MOCA 2025 Statewide Housing Data Collection, first year).**
  - **2025:** 516 ADUs permitted in 182 reporting municipalities (about 73% of the population), 7% of permitted units.
  - **Before 2025:** no statewide count.
  - **Rate shown:** uses the state's homes, so it is a lower bound. If every ADU came from the reporting towns, the rate among them would be about 1.3.
- **Utah (DWS Moderate Income Housing reports).**
  - **Counts:** about 90 "specified" cities and counties answer "building permits issued to construct an ADU": 903, 836, 1,013 (report years ending July 2023, 2024, 2025). The balanced panel went 833 → 973 (2024 → 2025).
  - **Caveats:**
    - Self-reported, with definitions that vary; Vineyard counts basement-finish permits, and Cedar Hills' 1,111 was excluded.
    - There is no question before 2023.
    - Rate shown uses the state's homes.

**Proxies (no statewide ADU count)**
- **New Hampshire:**
  - OPD's survey has no ADU field through 2024. The "conversions" column, net units from any conversion, gave 309–507 a year in 2020–24.
  - ADU counts begin with calendar 2025, with the report due about January 2027.
  - Mercatus 2023 found 0.12–1.46 per 1,000 one-unit homes a year in 8 towns, 2017–21.
- **Vermont:** no statewide permit series.
  - Chittenden County RPC's ADU inventory by year built gives 18–30 a year in 2016–20 and 26–57 in 2021–24.
  - The DHCD E911 "new housing" layer is marked unverified, and its data capture changed in 2022 and 2026. Not used.
- **Montana:**
  - Bozeman ADU applications were 13, 23, 28, 14, 9 (2020–24), falling after SB 528; the duplex law may substitute.
  - Missoula reports only fiscal-year-to-date fragments.
- **Arizona** (source_lead):
  - Tucson applications: 61 in 2022, about 80 in 2025.
  - Phoenix: 233 ADU permits Sep 2023–Sep 2024 (city press release, verified); 84 detached in 2025 (vendor analysis).
  - Phoenix and Tucson reformed before the state law.
- **Colorado:** Colorado Springs 10 in 2024 (source_lead). Pre-law city baselines from Bell Policy (Boulder about 50 a year).
- **Hawaii:**
  - Honolulu permits flagged ADU: 101–266 a year in 2016–21, 111–123 in 2022–23, 222 in 2024.
  - This follows Honolulu's 2015 ordinance, not the state law.
- **Maryland:**
  - Montgomery County permits whose text names an ADU: 5 (2019) → 115 (2025).
  - This is a keyword count that includes trade permits, so it is rough. It follows local rules (2019).
- **Connecticut, Arkansas, Iowa, Nevada:** no counts.
  - RPA (2026): "There is no statewide source tracking production of ADUs in CT."
  - Des Moines had 8 ADUs under its earlier owner-occupied rules (source_lead).

**Definitions:**
- All series count at permit issuance except Chittenden (year built) and Utah (report years ending July).
- None separates ADUs built with a new house except where noted; Honolulu flags new buildings (12–30% of its ADU permits a year).
- Missing years are missing, not zero.

## 4. Rates before and after

Per 1,000 one-unit detached homes per year. The 95% Poisson interval is on the count only; it ignores year-to-year swings and reporting gaps, so it understates real uncertainty. Full table, with counts and homes: [`reference/statewide_states_period_rates.csv`](../../reference/statewide_states_period_rates.csv). Denominators and markets: [`reference/statewide_states_acs.csv`](../../reference/statewide_states_acs.csv).

| Series | Window | Rate [95%] | Years after law | Median home value | Median rent |
| --- | --- | ---: | --- | ---: | ---: |
| WA cities excl. Seattle | EY2011–16 | 0.12 [0.11–0.13] | before | $595,200* | $1,713* |
| | EY2019–23 | 0.39 [0.38–0.41] | before | | |
| | EY2024–25 | **0.75** [0.71–0.78] | enacted, not yet binding | | |
| | EY2026 | **0.84** [0.78–0.90] | under 1 after compliance | | |
| WA all areas | EY2021–23 → EY2024–25 → EY2026 | 0.81 → 1.07 → 1.04 | | $564,600 | $1,760 |
| Spokane (state law binds 2026-12-31) | EY2011–21 → EY2023–26 | 0.08 → 0.52 | local 2022 reform | $363,500 | $1,215 |
| OR 32 cities excl. Portland | 2018 (law year) | 0.46 [0.39–0.53] | 0 | $482,229* | $1,515* |
| | 2019–22 | **0.90** [0.85–0.95] | 1–4 | | |
| Rhode Island | 2021–23 | 0.23 [0.20–0.26] | before | $404,200 | $1,342 |
| | 2024 | 0.60 [0.51–0.70] | law year | | |
| | 2025 | **0.97** [0.85–1.09] | 1 | | |
| Massachusetts | 2025 | **0.79** [0.75–0.84] (undercount) | 1 | $562,100 | $1,762 |
| Maine | 2025 | **0.98** [0.90–1.07] (lower bound) | 1 | $296,600 | $1,139 |
| Portland, ME | 2022–23 → 2024–25 | 1.22 → 1.14 | before → 0–1 | $489,600 | $1,577 |
| Utah (MIH reporters) | report years 2023–25 | **1.13** [1.09–1.17] | 1–4 | $489,400 | $1,496 |
| New Hampshire (conversions proxy) | 2020–24 | 0.92 [0.88–0.96] | 3–7 | $402,500 | $1,491 |
| Chittenden County, VT | 2016–20 → 2021–24 | 0.62 → **0.94** [0.80–1.11] | before → 1–4 | $439,200 | $1,646 |
| Honolulu | 2016–23 → 2024 | 1.14 → 1.31 | local ordinance | $897,500 | $2,083 |
| Montgomery County, MD | 2020–25 | 0.42 | local rules | $640,300 | $2,068 |
| Bozeman, MT | 2020–23 → 2024 | 1.82 → 0.84 | before → 0 | $687,900 | $1,717 |
| Tucson, AZ | 2022 → 2025 | 0.48 → 0.62 | before → 1 | $266,200 | $1,145 |
| Phoenix, AZ (detached only) | 2025 | 0.22 | 1 | $420,700 | $1,582 |
| California, non-holdout groups | 2014–16 → 2017 → 2018–19 → 2020–22 → 2023–25 | 0.12 → 0.66 → 1.48 → 2.46 → 3.88 | before → 1 → 2–3 → 4–6 → 7–9 | $734,700 (state) | $2,036 |
| Wisconsin (state) | — | Madison 0.16 | — | $266,500 | $1,087 |

\* Home-weighted mean of the member places' ACS medians (an approximation). All markets are ACS 2020–2024 5-year B25077 and B25064 for the geography shown.

**What this shows (descriptive):**
- **Year 1–4 after a state law clusters near 1 per 1,000** in seven different series: WA, OR, RI, MA, ME, UT and Chittenden. This is close to California's restrictive-group plateau (1.23) and above California's own first strong-law year (0.66).
  - It is well below California's statewide plateau (3.88). California reached that only after three rounds of law and, per the owner, an industry that formed mainly after 2020 (AQ-034).
- **The jumps are in high-value markets.** The three series closest to Wisconsin's market (Maine $297k; Spokane $364k, under a local reform; Tucson $266k) show 0.98, 0.52 and 0.62. These are lower or similar, not higher.
- **No state is yet a clean test of industry formation.** Industry formation needs years 3–5 after a binding statewide law, and only Oregon (years 1–4, cities only, no pre-law year) and Utah (internal ADUs only) reach that.
  - Oregon outside Portland rose in 2019–2020 and then held flat at about 0.9. That is a plateau, not the continuing climb California showed.
- **Washington's rise came before its law bound most cities.** That is consistent with an industry or local response to a credible statewide mandate, but it cannot be separated from city reforms adopted on their own timetable (for example Spokane's 2022 interim rules) and the 2021–22 building boom.

## 5. Usefulness ranking for the Wisconsin statewide-law test

Ranking: [`reference/statewide_states_ranking.csv`](../../reference/statewide_states_ranking.csv). California is excluded because it is the regression's fitting state, not an independent test.

**Score:** a weighted sum, written in `rank_states`:
- years of post-law data after the effective date, capped at 5 (weight 0.35);
- data quality: official statewide 1, official partial 0.75, regional 0.5, city proxy 0.35, not ADU-specific 0.25 (weight 0.25);
- a same-source pre-law baseline, counted only if there are post-law years (weight 0.10);
- closeness of the law to the benchmark: strong 1, weaker 0.5, minus 0.25 if not both attached and detached, minus 0.1 if not fully by right (weight 0.20);
- closeness of the data geography's median home value to Wisconsin's, scored 0 at three times or one third (weight 0.10).

**Sensitivity:** counting years after local compliance instead (AQ-034's timing note) drops Washington from 1st to 8th (0.717 → 0.477). Everything else is unchanged. The score is a judgment aid, not a statistic.

| Rank | State | Class | Years after (effective / compliance) | Data | Baseline | Score |
| ---: | --- | --- | --- | --- | --- | ---: |
| 1 | Washington | strong | 2 / 0 | official statewide | yes | 0.717 |
| 2 | Oregon | strong | 4 / 4 | official, cities > 10k | no | 0.694 |
| 3 | Vermont | weaker | 4 / 4 | regional (Chittenden) | yes | 0.660 |
| 4 | Maine | strong | 1 / 1 | official, 73% of population | no | 0.528 |
| 5 | New Hampshire | weaker | 5 / 5 | not ADU-specific | no | 0.505 |
| 6 | Rhode Island | weaker | 1 / 1 | official, self-reported | yes | 0.500 |
| 7 | Utah | weaker | 3 / 3 | official, self-reported | no | 0.492 |
| 8 | Massachusetts | strong | 1 / 1 | official, undercount | no | 0.490 |
| 9 | Montana | strong | 1 / 1 | city proxy | yes | 0.471 |
| 10 | Arizona | strong | 1 / 1 | city proxy | no | 0.457 |
| 11 | Colorado | strong | 0 / 0 | city proxy | no | 0.339 |
| 12 | Maryland | weaker | 0 / 0 | county proxy | yes | 0.208 |
| 13–14 | Arkansas, Iowa | strong | 0 | none | — | 0.200 |
| 15 | Hawaii | weaker | 0 | county proxy | yes | 0.168 |
| 16 | Connecticut | weaker | 0 | none | — | 0.100 |
| 17 | Nevada | weaker | 0 | none | — | 0.080 |

**Suggested use (for the conductor; nothing here is adopted):**
- **Washington as the main out-of-sample check.** Use incorporated places excluding Seattle, plus city detail. Two uses:
  - Compare the regression's prediction for Washington cities' markets with EY2024–26.
  - When OFM's EY2027–28 files arrive, test whether rates keep rising after compliance (industry formation) or plateau.
  - Spokane is the closest Washington market to Madison; its state compliance date (2026-12-31) gives a clean future before/after.
- **Oregon as a four-year post-law check.** Its plateau near 0.9 is the best current evidence on years 2–4 after a strong statewide law outside California.
- **Vermont/Chittenden, Maine and Rhode Island as low-weight checks** closer to Wisconsin's market or with a true before.
- **None should become a regression fitting point.** Definitions differ (most include ADUs built with new houses; Utah is internal only), and coverage is partial and self-reported. The same reasoning applies as for the five cities in [OTHER_CITIES.md](OTHER_CITIES.md) §4.
- **Re-check later:** Iowa (the Midwest strong-law state, first full year 2026), New Hampshire (first ADU counts about January 2027), Massachusetts (second year) and Arkansas.

## 6. Reproduce

```
uv run python scripts/build_statewide_states.py --print   # writes reference/statewide_states_*.csv
bash scripts/test.sh                                      # offline tests incl. tests/test_statewide_states.py
```

- **Code:**
  - `missing_middleware/comparison/statewide_states.py`: state table, series, periods, ACS reader, rates and ranking.
  - `scripts/build_statewide_states.py`: builds the outputs.
- **ACS inputs (read only):** existing `data/raw/census_acs5_2024_tbsf` (B25024) and `census_acs5_2024_tbsf_market` (B25077, B25064).
- **Place lists:** Census 2020 place-code files in `data/raw/statewide_states/census_place_codes/`.
  - Used to pick incorporated places in Washington and match the 32 Oregon cities by name.
  - Also used to check the city GEOIDs used for Spokane, Bozeman, Phoenix, Tucson, Colorado Springs and Portland ME.
- **Raw copies** (git-ignored, each folder with `_downloads.json`: URL, access date 2026-10-24, bytes, SHA-256): `data/raw/statewide_states/{wa,or,nh,vt,ut,hi,md}/`. They hold:
  - the OFM workbook, DLCD PDFs and NH OPD CSV;
  - the Chittenden and DHCD aggregate queries;
  - the Utah MIH PDFs and extracted counts;
  - the Honolulu and Montgomery aggregate queries.
- **Read but not saved:** mass.gov, maine.gov and housing.ri.gov block scripted downloads (HTTP 403). Their figures were read from the official pages and PDFs through a text-fetch service and are recorded with URLs in the laws table.
- **How counts get into the build:** annual counts are written into `SERIES`, transcribed or extracted from those sources. The build does not re-parse PDFs or Excel, because the project has no Excel reader dependency.
  - The Washington figures were re-extracted from the OFM workbook on 2026-10-24 and matched.
- **Personal data:** none requested or kept. All queries were aggregates.

**Unknowns and limits:**
- The Mercatus 2025 table images were not read; the weaker-state list is a source_lead (section 1).
- Several dates are source_lead:
  - Arizona's general effective date;
  - Arkansas's effective date;
  - the Washington county compliance schedule beyond the four Puget Sound counties;
  - Maine LD 1829's effective date.
- Oregon has no 2024–2025 tables yet.
- Rhode Island's coverage for 2021–23 is not stated.
- Utah's counts are parsed from free text.
