# ADU permits outside California: Seattle, Portland, Austin, Denver, Minneapolis

Gate 3 add-on, owner request of 2026-10-24. These are out-of-state evidence for the California comparison and candidate check points for the market-adjusted regression (`missing_middleware/comparison/ca_regression.py`). They are **not** part of the pre-registered [CA_COMPARISON_PLAN.md](CA_COMPARISON_PLAN.md) and change nothing in it.

**All numbers here are descriptive.** Each city changed its rules while its housing market, construction costs and interest rates were also changing, and there is no comparison city. A rate that rose after a reform is *associated with* that reform; it is not an estimate of the reform's effect.

## Plain-language summary

- **Rates are per 1,000 one-unit detached homes per year.** The denominator is the same ACS 2020–2024 5-year count used for California and Wisconsin. The main measure counts ADUs added to a lot that already has a house. ADUs built together with a new house, and legalizations, are excluded where the data identify them.
- **Seattle: rate about 2.7 times higher after its 2019 reform.** Ord. 125854 (effective 2019-08-08) removed owner-occupancy and parking rules and allowed two ADUs per lot.
  - ADUs on existing homes went from **1.40 a year (2016–2018) to 3.81 (2021–2024)**.
  - Counting ADUs built with new houses, the rate went from 1.77 to 5.97. The city's official report gives 6.04.
  - About a third of post-reform ADUs came with a new house, often on redevelopment sites later sold as condos.
- **Portland: a fee waiver came with a big rise, followed by a fall.** It is the clearest case of money, not rights, moving the numbers.
  - The rate went from **0.14 (2007–2009)** to 1.05 under the development-charge waiver (2011–2015), then peaked at **2.93 (2016–2018)** as the waiver's deadline approached.
  - It then fell to 1.51 (2019–2020) and **1.16 (2022–2025)**, even after the 2021–2022 Residential Infill Project allowed two ADUs per house.
- **Austin: about 2.5–2.9 times higher after its 2015 changes.**
  - Secondary apartments on existing homes went from **0.19 (2012–2014) to 0.56 (2016–2019) and 0.49 (2020–2023)**.
  - About two-thirds of Austin's secondary apartments were permitted together with a new house. Including them, the rate is 0.42 → about 1.5.
  - The 2024 HOME reform retired the ADU permit category, so **2024 onward cannot be compared**.
- **Denver: rate roughly doubled in the first year of citywide legalization.** ADUs were legal only where land had been rezoned until Denver allowed them citywide on 2024-12-16.
  - The rate was **0.37 (2016–2022)**, 0.49 in 2023–2024 after a design-standards change, and **0.80 in 2025**, the first citywide year.
- **Minneapolis: the closest Midwest analogue, and low.**
  - The rate was **0.32 (2017–2020)**, then **0.17 (2021–2025)** after the owner-occupancy rule was removed. Removing that rule was not followed by a rise.
  - Minneapolis's home values and rents are close to Madison's.
- **Comparison with the California study and Wisconsin:**
  - California's 2023–2025 levels: 1.23 (previously restrictive places), 3.84 (all grouped places) and 7.31 (the previously most active quarter).
  - **Madison:** 0.16–0.18.
  - **Seattle:** sits between the California all-group and active-quarter levels.
  - **Portland and Austin (with new houses included):** near the California restrictive-group level.
  - **Denver:** reached about two-thirds of the California restrictive-group level in its first citywide year.
  - **Minneapolis:** about Madison's rate.
- **Suggested use:**
  - **Out-of-sample checks:** none of the five cities should become a fitting point in the California regression.
  - **Why not:** none had a state mandate at the same time as California's 2020 wave. The reform types differ (fees in Portland, city rules in Seattle and Austin, zoning coverage in Denver). For Seattle, Austin and Denver, the 2023–2025 window is either incomplete or mixes two regimes.
  - **Good checks:** Seattle and Portland have the strongest data. Minneapolis is the most relevant market for Wisconsin.

## 1. Rates by city and period

ADUs per 1,000 one-unit detached homes per year. **Main measure:** ADUs on existing homes, excluding those built with a new house and identified legalizations. The interval in brackets is a 95% Poisson interval on the count; it ignores year-to-year swings, so it understates real uncertainty. **"Incl. new house"** adds ADUs permitted together with a new primary house; it is closer to what the California APR counts, since the California study could exclude only the few with-new-house ADUs named in the text.

| City | Period | Years | ADUs (main) | Rate, main [95%] | Rate incl. new house | Rules in force |
| --- | --- | --- | ---: | ---: | ---: | --- |
| Seattle | before 2019 reform | 2016–2018 | 608 | **1.40** [1.29–1.51] | 1.77 (official 1.77) | Detached ADUs citywide since 2009; owner occupancy and parking required |
| Seattle | longer before | 2010–2018 | 1,314 | 1.01 [0.95–1.06] | 1.23 (official 1.23) | same |
| Seattle | year 1 after | 2020 | 350 | 2.41 [2.17–2.68] | 3.19 (official 3.28) | Ord. 125854 (effective 2019-08-08) |
| Seattle | after | 2021–2024 | 2,210 | **3.81** [3.65–3.97] | 5.97 (official 6.04) | Ord. 125854; before HB 1337 compliance (2025-06-30) |
| Portland | before fee waiver | 2007–2009 | 68 | **0.14** [0.11–0.18] | 0.17 | ADUs allowed; development charges paid |
| Portland | waiver | 2011–2015 | 843 | 1.05 [0.98–1.12] | 1.26 | Development-charge waiver from 2010 |
| Portland | waiver deadline peak | 2016–2018 | 1,415 | **2.93** [2.78–3.09] | 3.36 | Waiver expiry 2018-07-31 |
| Portland | permanent exemption | 2019–2020 | 487 | 1.51 [1.38–1.65] | 1.78 | Exemption only with a no-short-term-rental covenant; Oregon HB 2001 ADU rules from 2020 |
| Portland | after RIP | 2022–2025 | 746 | **1.16** [1.08–1.25] | 1.28 | Residential Infill Project (2021-08-01, 2022-06-30) |
| Austin | before 2015 changes | 2012–2014 | 121 | **0.19** [0.16–0.23] | 0.42 | Secondary apartments on lots of 7,000 sq ft or more |
| Austin | after, early | 2016–2019 | 466 | **0.56** [0.51–0.61] | 1.56 | Ord. 20151119-080 (effective 2015-11-30) |
| Austin | after, late | 2020–2023 | 408 | 0.49 [0.44–0.54] | 1.48 | same, before HOME |
| Austin | after HOME | 2024– | — | not comparable | — | ADU category retired 2024-02-05 |
| Denver | zone-by-zone | 2016–2022 | 380 | **0.37** [0.34–0.41] | 0.37 | ADUs only where zoned (about 36% of land) |
| Denver | design standards changed | 2023–2024 | 142 | 0.49 [0.41–0.57] | 0.49 | 2023 text amendment, no rezoning |
| Denver | citywide | 2025 | 117 | **0.80** [0.66–0.96] | 0.82 | Citywide from 2024-12-16 (one year observed) |
| Minneapolis | owner occupancy required | 2017–2020 | 109 | **0.32** [0.27–0.39] | 0.34 | 2014 ordinance; data start Dec 2016 |
| Minneapolis | owner occupancy removed | 2021–2025 | 73 | **0.17** [0.14–0.22] | 0.20 | Removed for attached and detached ADUs, 2021 |

**Before/after ratios (main measure):**
- Seattle: ×2.7 (×3.4 including new houses).
- Portland: ×7.4 for waiver against pre-waiver, ×21 at the peak, ×8.2 after RIP.
- Austin: ×2.9 early, ×2.5 late.
- Denver: ×2.2 in the first citywide year.
- Minneapolis: ×0.54 after the owner-occupancy rule was removed.

Annual counts are in [`reference/other_cities_annual.csv`](../../reference/other_cities_annual.csv); every period and measure is in [`reference/other_cities_period_rates.csv`](../../reference/other_cities_period_rates.csv).

### 1.1 Against the California groups and Madison

| Place | Window | Rate per 1,000 per year | Median home value | Median gross rent |
| --- | --- | ---: | ---: | ---: |
| California, previously restrictive places (73) | 2023–2025 | 1.23 [0.70–2.01] | — | — |
| California, all grouped places | 2023–2025 | 3.84 [2.63–5.30] | — | — |
| California, previously most active quarter | 2023–2025 | 7.31 | — | — |
| Seattle | 2021–2024 | 3.81 (5.97 incl. new house) | $938,600 | $2,030 |
| Portland | 2022–2025 | 1.16 (1.28) | $581,500 | $1,655 |
| Austin | 2020–2023 | 0.49 (1.48) | $555,300 | $1,729 |
| Denver | 2025 | 0.80 (0.82) | $616,000 | $1,831 |
| Minneapolis | 2021–2025 | 0.17 (0.20) | $362,200 | $1,371 |
| Madison, ADU-type part | 2022–2025 | 0.164 | $372,900 | $1,413 |
| Madison, all second homes (floor window, G2-9) | 2022–2025 | 0.183; floor ÷ 0.8 = 0.229 | | |

California figures are from [CA_STUDY_RESULTS.md](CA_STUDY_RESULTS.md); Madison's are from [WI_BASELINE.md](WI_BASELINE.md). Home values and rents are ACS 2020–2024 5-year (B25077, B25064), the same vintage as the California and Wisconsin market data. California counts include most ADUs built with new houses and an unknown share of legalizations, so the "incl. new house" column is the closer comparison.

**What this shows (descriptive):**
- **Rates rise with market strength.** The two highest-value markets (Seattle and the California active places) have the highest rates.
- **Strong markets do not guarantee high rates.** Austin, Denver and Portland have values above $550,000 but rates near or below the California restrictive-group level.
- **Minneapolis, the market most like Madison, has a rate close to Madison's.** That supports the Wisconsin baseline sitting well below California levels. It does not show that rules make no difference: Minneapolis's 2014–2021 rules kept owner occupancy, and its later reforms (three units per lot from 2020) offered competing options.

## 2. Reform timeline

Full table with sources: [`reference/other_cities_reforms.csv`](../../reference/other_cities_reforms.csv) (researched 2026-10-24). "Verified" means read on an official or primary page.

| Jurisdiction | Measure | Effective | Change | Status |
| --- | --- | --- | --- | --- |
| Seattle | Ord. 123141 | ≈ 2009-12-04 | Detached ADUs in all single-family zones | number verified; date a source lead |
| Seattle | **Ord. 125854** | **2019-08-08** | Owner occupancy and parking removed; two ADUs per lot (not two detached); larger DADUs | verified |
| Seattle | Ord. 127211 (HB 1337) | 2025-06-30 | Two ADUs in any mix, including two detached | verified |
| Seattle | Ord. 127376 (HB 1110) | 2026-01-21 | Neighborhood zones allow 4–6 units; ADUs count toward density | verified |
| Washington | EHB 1337 | 2023-07-23 (cities: after next plan update; King County 2025-06-30) | Two ADUs, no owner occupancy, fee caps | verified |
| Portland | Res. 36766 SDC waiver | ≈ 2010-04 (adopted 2010-03-03); extended to 2018-07-31 | Development charges waived for ADUs | adoption verified |
| Portland | Ord. 187471 | 2016-01-01 | Siting and design relaxed | verified |
| Portland | Ord. 189050 | 2018-08-01 | Permanent waiver only with a 10-year no-short-term-rental covenant | verified |
| Portland | Ord. 190093 / 190851 (RIP 1, 2) | 2021-08-01 / 2022-06-30 | Up to 4–6 units; two ADUs per house | verified |
| Oregon | SB 1051 / HB 2001 | 2018-07-01 / 2020-01-01 (ADU rules) | ADU with every detached house; no owner occupancy or parking requirements | verified |
| Austin | **Ord. 20151119-080** | **2015-11-30** | Minimum lot 7,000 → 5,750 sq ft; larger units; no parking near transit corridors | verified |
| Austin | HOME phase 1 / 2 | 2024-02-05 / 2024-08-16 | Three units per lot; ADU uses replaced by two-unit and three-unit residential; small lots | verified |
| Denver | ADUs in Denver amendment | 2023-07-05 | **Design standards only; no rezoning** | verified |
| Denver | Citywide ADUs | **2024-12-16** | ADUs in all residential zones (about 70% of land, up from 36%) | verified |
| Colorado | HB24-1152 | 2024-05-13; local compliance 2025-06-30 | One ADU wherever single-unit homes are allowed | verified |
| Minneapolis | 2014 ordinance | 2014-12-05 (adopted) | ADUs citywide with owner occupancy | adoption verified |
| Minneapolis | 2040 plan / three units | 2020-01-01 | Up to three units per lot | verified |
| Minneapolis | Owner occupancy removed | 2021-02-26 (adopted) | Removed for detached and attached ADUs; internal ADUs keep it | adoption verified |

**Corrections to earlier notes (for the conductor; [POLICY_EVIDENCE_MAP.md](../gate1/POLICY_EVIDENCE_MAP.md) §5 is not mine to edit):**
- **Seattle's ADU ordinance number:** it is **125854**, not 125984. 125984 is a parks fee schedule.
- **Seattle's 2019 second ADU:** the 2019 reform did not allow two detached ADUs; that came in 2025.
- **Denver's 2023 change:** it was not citywide legalization. Citywide legalization came on 2024-12-16.
- **Austin's 2015 lot-size change:** the minimum became "a standard lot" (5,750 sq ft). The 5,750 figure is not written in the ordinance.

## 3. Methods and data quality

| City | Source (official) | Rule (fields and filters) | Years usable | Main weaknesses |
| --- | --- | --- | --- | --- |
| Seattle | Building Permits, data.seattle.gov `76t5-zqzr` (public domain), plus the official [OPCD 2024 ADU Annual Report](https://seattle.gov/documents/Departments/OPCD/OngoingInitiatives/EncouragingBackyardCottages/OPCD-ADUAnnualReport2024.pdf), Exhibit 10 | `permittypemapped`=Building; `dwellingunittype` lists an Accessory Dwelling type; issued; not cancelled. Units = ADU types listed (or `housingunitsadded` on ADU-only permits). With new house = house listed on a 'New' permit, or a new house permit at the same address within 365 days. Legalization by text | 2005–2024 (official series 2010–2024) | `dwellingunittype` stops being filled from July 2025, so 2025 is masked. Same-address matching misses some redevelopment sites: the official condo-parcel share (57% in 2022) is higher than our new-house share (36%), so the main measure may still be slightly high |
| Portland | BDS Residential Building Permits (PortlandMaps open data, layer 89: permits creating at least one unit since 1995) | `IS_ADU` true; `PDXBND`=YES; `ISSUEDATE` year. Detached = New Construction of an ADU; attached or conversion = Alteration or Addition; with new house = new house permit flagged ADU. One ADU per permit. Legalization by text | 1995–2025 (2026 partial) | Item metadata last edited 2023, but records run to 2026-08. The city's own figures are higher (615 in 2016 against our 538; 86 in 2010 against our 67), possibly by application or a different date basis |
| Austin | Issued Construction Permits, data.austintexas.gov `3syk-w9eu` (public domain) | Building permits in class `R- 102 Secondary Apartment`; full or limited purpose; not void or withdrawn; non-dwellings dropped. Units = `housing_units`. With new house = a house permit on the same parcel (`tcad_id`) within 365 days; the median gap is 0 days. Legalization by text. Sensitivity adds other residential classes whose text names an ADU (0.38 → 0.73 → 0.65) | 2005–2023 | **HOME retired the category on 2024-02-05; 2024+ is not comparable.** Detached vs attached is rarely stated (60% unknown). The same-parcel rule is a heuristic. The city's HOME annual report counts applications (162 two-unit approvals in the first year), not issued ADUs |
| Denver | Residential Construction Permits (Denver open data, Accela RESCON, ArcGIS layer 316) | Building statistics code `026` (ADU; addresses like "… 1/2" and "… ADU" confirm it) on any of the three code fields; not cancelled; change-of-contractor, repair and move permits dropped. Detached = New Building; attached or conversion = Addition, Alteration or Change of Use; with new house = 026 alongside a dwelling code | 2016–2025 (records start 2012; Accela went live 2015-06-07) | **No description field: legalizations cannot be screened, and attached or conversion ADUs not coded 026 are missed** (92% of counted ADUs are detached). Secondary check: about 389 permits 2018 to May 2024 (Denverite) against our 360 for 2018–2023 |
| Minneapolis | CCS Permits (Minneapolis open data, ArcGIS) | Residential permits whose comments name an ADU; abandoned ADUs dropped; **one ADU per parcel per 24 months** (foundation, shell and finish permits collapse). Legalization by text (the city's standard "built without a permit" warning is ignored) | 2017–2025 | Records start Dec 2016, so there is no pre-2014 baseline. Text matching and de-duplication are heuristics. Small counts. The secondary figure of 13–15 a year (2020–2022) matches ours (15, 15, 14) |

**Shared definitions:**
- **Counted at:** permit issuance, by calendar issue year.
- **Missing is never zero:** years a source does not cover are blank in the annual table.
- **Exclusion shares in the main windows** (with new house / legalization):
  - Seattle 2021–2024: 36% / 0%.
  - Portland 2016–2018: 12% / 2.4%.
  - Austin 2016–2023: 66% / 0.3%.
  - Denver 2016–2025: 0.6% / not identifiable.
  - Minneapolis 2017–2025: 8% / 2.9%.
- **ADUs, not permits:** all five series count ADU units, not permits. Seattle permits can carry two ADUs; the other cities' rules give one per permit.

**Cross-check against the official Seattle series** ([`reference/other_cities_crosscheck.csv`](../../reference/other_cities_crosscheck.csv)):
- Open-data ADUs including new houses are within **2.8%** of the OPCD totals in every year 2010–2024.
- The median absolute gap is 0.8%.

**Denominators** ([`reference/other_cities_acs.csv`](../../reference/other_cities_acs.csv)): ACS 2020–2024 5-year B25024_002, place level.

| Place | One-unit detached homes |
| --- | ---: |
| Seattle | 144,993 |
| Portland | 160,807 |
| Austin | 209,772 |
| Denver | 145,528 |
| Minneapolis | 84,075 |
| Madison | 53,292 (matches the Wisconsin baseline) |

- **Fixed denominator:** a single count is applied to every year. Austin and Denver grew a lot over 2010–2025, so their early-year rates are somewhat understated relative to later years.
- **Exposure, not eligible lots:** this is an exposure measure, not a count of eligible lots. Denver allowed ADUs on only about 36% of its land before 2024-12-16.

## 4. Suitability as regression or validation points

[`reference/other_cities_points.csv`](../../reference/other_cities_points.csv) has one row per city with:
- the 2017–2019 rate and the group it would fall in under the California wave-3 rule;
- the 2023–2025 rate with its exposure;
- ACS home value, rent and income;
- a suggested use and caveat.

| City | 2017–2019 rate (CA group rule) | 2023–2025 rate (years observed) | Suggested use | Data quality |
| --- | ---: | ---: | --- | --- |
| Seattle | 1.43 (active) | 4.26 (2 of 3) | Out-of-sample check | strong |
| Portland | 2.56 (active) | 1.03 (3) | Out-of-sample check | strong |
| Austin | 0.58 (middle) | 0.41 (1 of 3) | Weak check only | weak |
| Denver | 0.38 (middle) | 0.59 (3; mixes regimes) | Out-of-sample check | moderate |
| Minneapolis | 0.33 (middle) | 0.17 (3) | Out-of-sample check | moderate |

**Why checks and not fitting points:**
1. **Different treatment.** The California regression explains post-2020 plateaus that followed a statewide mandate, by pre-2020 group and market. None of these cities had a mandate in force over 2020–2025 until Washington's and Colorado's took effect in mid-2025; Oregon's 2018–2020 laws arrived after Portland was already permissive.
2. **Windows.** For Seattle the 2023–2025 window is incomplete, for Austin it is broken, and for Denver it mixes two legal regimes.
3. **Definitions.** Denver misses conversions, and Austin's new-house rule is a heuristic. Adding a few heterogeneous points to about 300 California places would add noise more than information.

**How to use them:** compare each city's observed rate with the regression's prediction for its group and its ACS market values, and report the direction and size of the miss. Seattle and Portland are the strongest tests. Minneapolis tests the low-value end, near Wisconsin's markets.

## 5. Reproduce

```
uv run python scripts/build_other_cities.py --fetch   # download raw data (about 60 MB), then build
uv run python scripts/build_other_cities.py           # rebuild from data/raw
bash scripts/test.sh                                  # offline tests incl. tests/test_other_cities.py
```

**Raw data** (git-ignored, each folder with a `_downloads.json` giving URL, query, access date, bytes and SHA-256; accessed 2026-10-24):
- `data/raw/seattle_permits_socrata/`
- `data/raw/seattle_opcd_adu_report/`
- `data/raw/portland_res_permits/`
- `data/raw/austin_permits_socrata/`
- `data/raw/denver_rescon_permits/`
- `data/raw/minneapolis_ccs_permits/`

**Personal data:** no applicant, contractor or phone fields were requested. Permit site addresses stay in `data/raw`.

**ACS inputs:** read from the existing `census_acs5_2024_tbsf` (B25024) and `census_acs5_2024_tbsf_market` (B25077, B25064, B19013) folders.

**Code:**
- `missing_middleware/comparison/other_cities.py`: classifiers, reform table, rates.
- `scripts/build_other_cities.py`: downloads and outputs.
