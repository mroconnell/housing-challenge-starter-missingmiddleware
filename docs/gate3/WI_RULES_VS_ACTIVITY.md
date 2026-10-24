# Do Wisconsin's coded local ADU rules predict activity?

Prepared 2026-10-24 for the Gate 3 owner review, in answer to the owner's question of that date. Built by `scripts/build_wi_more_cities.py` with `missing_middleware/permits/wi_more_cities.py` and one adapter module per new place (`missing_middleware/permits/wimc_<place>.py`). All rates are **second-home permits on single-family lots (AQ-032), per 1,000 ACS 2020–2024 one-unit detached homes, per year**. The numerator is permits counted in the complete calendar years 2022–2025 that the source covers. The denominator is homes × complete years ÷ 1,000 ("thousand home-years").

## Plain summary

- **Places measured.** We now have 2022–2025 measurements for **13 Wisconsin places, up from 4**.
  - 9 cover the whole four-year window; 4 cover only 2 or 3 complete years.
  - **9 of the 13 are among the 37 coded places.** The other 4 (Verona, Watertown, Waunakee, Kaukauna) have only provisional rules.
  - That is **short of the 15-place target, and far short of the 20 that rule v1.1 needs before it ranks**.
  - All 24 other coded places were checked. Their permit data is behind a login or a search form, blocked to scripts, or published only as summary counts.
- **Activity is rare.** Only 5 of the 13 places have any counted second home in their complete years:
  - Madison: 39 permits, 0.183 per 1,000 homes per year.
  - Milwaukee: 35 candidate permits, 0.086 per 1,000 per year.
  - Kaukauna: 7 permits, 0.432 per 1,000 per year, from flags only.
  - Watertown: 2 permits, 0.109 per 1,000 per year.
  - Sun Prairie: 1 permit, 0.031 per 1,000 per year.
  - The other 8 measured zero.
- **Do the rules predict activity? Not in a way we can use.**
  - **Explicit prohibition is consistent with no activity.** Pleasant Prairie, Howard and Neenah together counted 0 permits over 63.8 thousand home-years (95% upper bound 0.058 per 1,000 homes per year).
  - **Allowing ADUs, even by right, does not imply activity.** Four places that allowed some ADU form through most of 2022–2025 counted zero: Fitchburg, De Pere, Green Bay and Verona.
  - **The two cities with real activity were not permissive for most of the window.** Madison had an owner-occupancy rule until April 2024. Milwaukee's single-family (RS) districts did not allow ADUs until August 2025.
  - **The rules in force during 2022–2025 have no rank correlation with the rate:** Spearman ρ = 0.05 over 9 coded places.
  - **Today's coding shows a weak negative correlation:** ρ = −0.63, permutation p = 0.06. Madison alone drives it, and Madison is coded benchmark only because of reforms made partway through the window.
- **Market value doesn't explain activity either** (ρ = 0.11 over 9 places). Active Milwaukee has the lowest home value in the set ($184,000). Waunakee, Verona and Fitchburg ($417,000–$516,000) measured zero.
  - This matches the Madison and Minneapolis lesson: rules and market leave most of the variation unexplained.
  - The clearest pattern is size: the only two places with more than a handful of permits are the two biggest cities. That pattern was noticed after looking, so it is reported as an observation, not a test.
- **Recommendation: treat the rules as "not predictive" for grouping.**
  - Keep the owner's rule that unmeasured places are restrictive.
  - Do not build a rules-based or combined grouping for unmeasured places from this evidence.
  - Explicit prohibition supports "restrictive", but that is already the default.
  - Revisit if the measured set reaches 20 (§6).

## 1. What was measured, and how

Same outcome as AQ-032: a legally permitted permanent dwelling with its own kitchen, added on a lot that already has a single-family home.

- **Counted:** ADUs (detached, attached, garage or accessory-building conversion, interior), single-family-to-duplex conversions, and a second new dwelling on a lot that already has a house.
- **Excluded:** legalizations, new two-unit buildings on vacant or cleared lots, teardown-rebuilds, and renewals.
- **Review:** every counted record and every near-hit was judged by hand in the place's adapter (`JUDGMENTS`).
- **Upper bound:** records that could not be confirmed are not counted. Each adds 1 unit to the "upper bound".
- **Access:** plain HTTP GET only, with no browser, form submissions or logins.
- **Privacy:** owner and person fields are dropped at load, and nothing committed carries a house number. Record lists with house numbers redacted are in `data/processed/wi_more_cities/record_review.csv` (git-ignored).

**Table 1. Measured places** (`reference/wi_measured_permits_2022_2025.csv`)

- **Rate** and **upper rate:** permits per 1,000 one-unit detached homes per year. The numerator is permits in complete years; the denominator is homes × complete years ÷ 1,000.
- **95%:** exact Poisson interval on the count, divided by the same denominator.

| Place | GEOID | Permits (complete years) | Upper bound | Complete years | Homes | Rate | 95% | Upper rate | Stage | Quality |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Madison city | 5502548000 | 39 | 39 | 2022–2025 | 53,292 | 0.183 | 0.130–0.250 | 0.183 | issued | A |
| Milwaukee city | 5507953000 | 35 (candidates) | 54 | 2022–2025 | 101,402 | 0.086 | 0.060–0.120 | 0.133 | issued | C |
| Sun Prairie city | 5502578600 | 1 | 1 | 2022–2025 | 8,118 | 0.031 | 0.001–0.172 | 0.031 | application | A |
| Pleasant Prairie village | 5505963300 | 0 | 1 | 2022–2025 | 6,332 | 0 | 0–0.146 | 0.039 | issued | A |
| Fitchburg city | 5502525950 | 0 | 0 | 2022–2025 | 5,999 | 0 | 0–0.154 | 0 | issued | B |
| Howard village | 5500935950 | 0 | 1 | 2022–2025 | 5,544 | 0 | 0–0.166 | 0.045 | issued | A |
| De Pere city (holdout) | 5500919775 | 0 | 5 | 2022–2025 | 6,522 | 0 | 0–0.141 | 0.192 | application | C |
| Verona city (not coded) | 5502582600 | 0 | 3 | 2022–2025 | 3,618 | 0 | 0–0.255 | 0.207 | issued | B |
| Waunakee village (not coded) | 5502584350 | 0 | 0 | 2022–2025 | 3,986 | 0 | 0–0.231 | 0 | issued | C |
| Kaukauna city (not coded) | 5508738800 | 7 | 8 | 2023–2025 | 5,401 | 0.432 | 0.174–0.890 | 0.494 | issued | C |
| Watertown city (not coded) | 5505583975 | 2 | 5 | 2023–2025 | 6,102 | 0.109 | 0.013–0.395 | 0.273 | issued | A |
| Green Bay city | 5500931000 | 0 | 6 | 2022–2024 | 26,655 | 0 | 0–0.046 | 0.075 | issued | A |
| Neenah city | 5513955750 | 0 | 0 | 2024–2025 | 8,172 | 0 | 0–0.226 | 0 | issued | A |

Quality: **A** = descriptions + type or units + lot check; **B** = descriptions or type, no lot check; **C** = flags only, sparse text, or a structural gap.

Source, method and caveats per place (year-by-year counts and coverage are in `reference/wi_rules_vs_activity_by_year.csv`):

- **Madison, Pleasant Prairie, Sun Prairie, Fitchburg:** unchanged from Gate 2 and Gate 3. The pilot reference tables are read as they are and were not rebuilt; their files are unchanged.
- **Milwaukee:** data.milwaukee.gov building permits (CC-BY, to 2026-06-15) matched to MPROP.
  - Uses the Gate 3 candidate rule (`model.baseline.milwaukee_candidates`). Central count is 35: 27 conversions or attached units and 8 detached-garage units. Upper count is 54.
  - The open data has no description or unit count, so these are **unverified candidates** (grade C). That is why Gate 3 treated Milwaukee as unmeasured.
  - Shown here because the owner asked for as many places as possible. Every test is also reported in a way that lets you drop it mentally: Milwaukee is one of the 9.
- **Howard:** village archive of monthly permit-activity PDFs (`villageofhoward.com/Archive.aspx?AMID=41`), all 48 months. 2012–2021 used only as lot history.
  - **0 counted.** One unconfirmed second "new single-family dwelling" permit at an address with an earlier one (2022).
  - The year-end summaries show 0 two-family units in every year.
- **De Pere** (a Gate 3 holdout; see §5): monthly project reports by application month, all 48 months. New single-family counts match the city's year-end summaries within ±2 a year.
  - **No free-text descriptions**, only fixed type names and census codes.
  - 0 confirmed; 5 new-dwelling projects on lots with a house are the upper bound.
  - **Probably a large undercount:** ADUs have been legal since 2023-01-01, but one filed as a remodel or addition is invisible in this source.
- **Neenah:** monthly "Building Permit Activity" PDFs via the city's WordPress media API.
  - Complete only for 2024 and 2025 (2022: 5 months; 2023: 8 months).
  - **0 counted.** The 2025 new-dwelling count matches the city's annual report.
- **Green Bay:** the city's monthly "Detail Summary of Projects Issued" reports. The live site blocks plain HTTP behind a Cloudflare challenge, so the **exact files were taken from Internet Archive copies of the same URLs** (owner decision needed, §7).
  - 2022–2024 complete. July 2024 comes from the yearly report. 2025 has only February.
  - Lot check against the 2019 statewide parcel roll.
  - **0 counted.** 6 unconfirmed: a furnace permit for a "mother-in-law suite behind main house", an electrical permit for a "new lower suite" with kitchen circuits, and 4 likely rebuilds.
- **Kaukauna** (not coded): "Building Inspection Report" attachments to Common Council packets on Municode Meetings. The city site blocks scripts.
  - **No free text.** Counts rest on the permit system's own work target, "Additional dwelling unit".
  - 2022 is missing January and February. Some months print no work target.
  - 7 counted (1 in 2023, 1 in 2024, 5 in 2025). Grade C.
- **Verona** (not coded): annual construction-report PDFs.
  - 2024 has type, cost and occupancy only (grade C that year).
  - **0 counted**; 3 unconfirmed.
- **Watertown** (not coded): monthly permit PDFs for 2023–2025. 2022 exists only as a summary chart.
  - 2 ADUs in 2025, both confirmed by conditional-use staff reports.
- **Waunakee** (not coded): the village's ArcGIS layer of **new** residential permits. Alterations and conversions are structurally invisible (grade C).
  - 0 counted. ADUs were legal only from 2024-05-06.

**Not measured (24 coded places)**, with the reason found for each:

| Reason | Places |
| --- | --- |
| Search form or login only | Eau Claire (Evolve, ASP.NET postback), Waukesha (eTRAKiT), La Crosse (EnerGov), New Berlin (Munis login), Mount Pleasant (BS&A login), Stevens Point (GovPilot), Racine (Cityworks) |
| Lookup only | Greenfield and Oak Creek (BS&A), Brookfield (OpenGov API 403) |
| Blocked to scripts | Wausau and Janesville (Akamai 403; Wausau's monthly PDFs exist and would be a good source if downloaded by a person), Muskego, Mequon, Sheboygan, West Bend, West Allis, Oshkosh (no response; Laserfiche reports are JavaScript-only), Wauwatosa (EnerGov times out) |
| Summary counts only | Fond du Lac, Manitowoc, Menomonee Falls, Franklin, Appleton (monthly summaries; 2025 map layer is a 63-record sample) |
| Nothing found | Kenosha (active permits only), Caledonia, Beloit, Superior |

Plover (not coded) is also not measured: only 2025–2026 months are posted.

## 2. Activity groups (rule v1 and v1.1)

The rule is `comparison.ca_regression.state_relative_groups`, applied to the measured places' own distribution:

- **active** = rate in the top quarter of measured places, with at least 3 permits;
- **restrictive** = zero permits, or not measured;
- **middle** = the rest.
- **Rule v1.1** allows "active" only when at least 20 places are measured.

**Pre-registered sample: the whole 2022–2025 window.** 9 places count as measured. The v1 cutoff is the rate of the 3rd-ranked place (ceil(0.25 × 9) = 3), which is Sun Prairie's 0.031 per 1,000 per year.

- **v1:** Madison and Milwaukee are active. Sun Prairie is at the cutoff but has only 1 permit (fewer than 3), so it is middle. The other measured places are restrictive. Kaukauna, Watertown, Green Bay and Neenah are restrictive because they are not measured over the whole window.
- **v1.1:** with only 9 measured places (under 20), no place can be active. Madison and Milwaukee become middle.

**Sensitivity: 2 or more complete years.** 13 places count as measured.

- The v1 cutoff (ceil(0.25 × 13) = 4th rate) is again Milwaukee's 0.086.
- Kaukauna and Madison are active, Milwaukee is active (at the cutoff, with 35 ≥ 3 permits), and Watertown and Sun Prairie are middle.
- **v1.1** again allows no active place.

Groups per place are in `reference/wi_rules_vs_activity_places.csv`.

## 3. Rules against activity

Rules come from `reference/wi_rights_exposure.csv` (`adu_full`) and `wi_adu_rules.csv`, coded two ways:

- **Current coding:** the class and flags as coded today.
- **In force for most of 2022–2025** (`WINDOW_RULES`): read from the dated rule rows. It differs from today's coding for:
  - Madison: owner occupancy to 2024-04-25, so restricted for 28 of 48 months;
  - Milwaukee: RS districts prohibited until 2025-08-01, 43 of 48 months;
  - Sun Prairie: no ADU text until 2026-05;
  - Fitchburg: attached, conditional and owner-occupied until 2025-09;
  - De Pere: prohibited in 2022, then restricted;
  - Green Bay: detached by conditional use.

The activity window is 2022–2025, so the in-force coding is the fair test. The current coding is shown because it is what the owner asked about.

**Rule strictness scale** used for the rank correlations: 0 = benchmark; 1 = restricted by tier-2 limits only; 2 = restricted with a tier-1 flag; 3 = prohibited (explicit or implicit).

**Table 2. Cross-tab, 9 coded places measured for 2 or more complete years (group v1, 2-year sample; current coding).** Each cell is the count of places. The denominator is the row total.

| Current rights class | active | middle | restrictive | Row total | Pooled rate (permits ÷ thousand home-years) |
| --- | --- | --- | --- | --- | --- |
| scenario_benchmark | 1 (Madison) | 0 | 0 | 1 | 0.183 (39 ÷ 213.2) |
| restricted | 1 (Milwaukee) | 1 (Sun Prairie) | 3 (Fitchburg, De Pere, Green Bay) | 5 | 0.063 (36 ÷ 568.1) |
| prohibited (all explicit here) | 0 | 0 | 3 (Pleasant Prairie, Howard, Neenah) | 3 | 0 (0 ÷ 63.8; 95% upper 0.058) |

**Ordinance status:**

- `mentioned_allowed`: 6 places (2 active, 1 middle, 3 restrictive), pooled 0.096 (75 ÷ 781.3).
- `unmentioned`: 2 places (Pleasant Prairie, Neenah), both restrictive, 0 ÷ 41.7.
- `prohibited`: 1 place (Howard), restrictive, 0 ÷ 22.2.

**Tier:**

- Tier-1 flag: 3 places (Milwaukee active; De Pere and Green Bay restrictive), pooled 0.068 (35 ÷ 511.7).
- Tier-2 only: 2 places (Sun Prairie middle, Fitchburg restrictive), pooled 0.018 (1 ÷ 56.5).

**Number of flags:**

- 0 flags (benchmark or prohibited): 4 places, 0.141 (39 ÷ 277.0).
- 1 flag: 3 places, 0.078 (36 ÷ 462.1).
- 2 flags: 1 place, 0 ÷ 26.1.
- 3 flags: 1 place, 0 ÷ 80.0.

All cells, samples and both groupings are in `reference/wi_rules_vs_activity_crosstabs.csv` and `_rates.csv`.

**Rules in force during the window:**

- Restricted: 4 places (Madison active; Fitchburg, De Pere and Green Bay restrictive), pooled 0.114 (39 ÷ 343.2).
- Prohibited: 5 places (Milwaukee active; Sun Prairie middle; Pleasant Prairie, Howard and Neenah restrictive), pooled 0.072 (36 ÷ 501.9).
- **The in-force coding orders the pooled rates the wrong way only because of Milwaukee.** Without Milwaukee, prohibited is 1 ÷ 96.3 = 0.010.

**Table 3. Spearman rank correlations, rule strictness or market against the rate** (`reference/wi_rules_vs_activity_correlations.csv`). ρ runs from −1 to 1 over n places. p is the share of 20,000 random permutations with |ρ| at least as large. A negative ρ for strictness means stricter rules go with lower rates.

| Sample (n places) | Strictness, current | Strictness, in force 2022–25 | Median home value | Median household income |
| --- | --- | --- | --- | --- |
| Coded, whole window (7) | −0.63 (p 0.16) | 0.00 (p 1.00) | 0.04 (p 0.95) | −0.57 (p 0.20) |
| Coded, 2+ years (9) | −0.63 (p 0.06) | 0.05 (p 1.00) | 0.11 (p 0.78) | −0.26 (p 0.49) |
| Coded, 2+ years, without holdout De Pere (8) | −0.67 (p 0.07) | −0.06 (p 1.00) | 0.08 (p 0.88) | −0.25 (p 0.55) |
| All 13, with provisional rules for the 4 uncoded places | −0.16 (p 0.60) | 0.05 (p 0.96) | −0.24 (p 0.44) | −0.43 (p 0.14) |

Using the upper-bound rate instead, every strictness correlation is between −0.39 and +0.18, with no p below 0.2.

- **Among restricted places only**, the number of flags in force has n = 4 and ρ = −0.54 (p 0.75): too few places to read anything.

**Table 4. Rules-based grouping against the measured group** (`reference/wi_rules_vs_activity_prediction.csv`)

The rules-based grouping maps benchmark → active, restricted → middle, prohibited → restrictive. Agreement is places where that mapping matches the measured group, out of measured places.

| Sample | Rules-based grouping, current coding | Same, rules in force 2022–25 | "Everyone restrictive" (the current default) |
| --- | --- | --- | --- |
| Coded, 2+ years, v1 (9 places) | 5 of 9 | 3 of 9 | 6 of 9 |
| Coded, 2+ years, v1.1 (9 places) | 5 of 9 | 4 of 9 | 6 of 9 |
| Coded, whole window, v1 (7 places) | 4 of 7 | 2 of 7 | 4 of 7 |

**The rules-based grouping never beats calling every place restrictive.**

- The misses are restricted places that measured zero: Fitchburg, De Pere and Green Bay.
- The other misses are places whose activity did not match their rules in force: Milwaukee was RS-prohibited but active; Madison had owner occupancy but was active.

**Ordered model.** Not fitted. Among coded places only 3 have any counted permit, and only 2 have more than one. A one-variable ordered logit on 9 places with 3 non-zero outcomes would not be identified in any useful sense. This follows the owner's instruction to fit one only if the counts justify it.

## 4. Market as a competing explanation

Median home value is ACS 2020–2024 B25077, county subdivision of the place's largest piece. It has **no rank relation with the rate**: ρ = 0.11, p 0.78, over 9 coded places.

- The two active places sit at both ends of the market: Madison $372,900; Milwaukee $184,000, the lowest of all 13.
- The highest-value places measured zero: Waunakee $515,900, Verona $420,400, Fitchburg $417,200.
- Sun Prairie ($365,700) is in Madison's market but under different rules in the window: 0.031 against Madison's 0.183. That is the one same-market contrast, and it points to rules mattering.
- The Madison–Minneapolis point stands: neither permissive rules nor a strong market is enough by itself.

**Post-hoc observation (not a test; noticed after looking):** the only two places with more than 7 permits are the two largest cities.

- For a place of 5,000–8,000 homes, Madison's rate (0.183 per 1,000 per year) implies 3–6 permits expected in four years. For example: Pleasant Prairie 25.3 thousand home-years × 0.183 = 4.6 expected; Verona 14.5 × 0.183 = 2.6.
- So zeros at small places are only moderately informative one by one: the probability of zero is e^−4.6 ≈ 1% for Pleasant Prairie and e^−2.6 ≈ 7% for Verona.
- Pooled, they are strongly informative. Fitchburg, De Pere and Green Bay (allowed or restricted in the window) counted **0 over 130.0 thousand home-years** (95% upper 0.028 per 1,000 per year), well under Madison's 0.183.

## 5. Deviations and caveats

1. **Measured set below target.** There are 13 places (9 coded), not 15–20. The pre-registered rule needs the whole window, so the test was also run on the 2-or-more-complete-years sample. Both samples are reported.
2. **Window-in-force coding is my reading** of the dated rule rows, not a new coding pass (`WINDOW_RULES` in the module). The current coding is reported unchanged beside it.
3. **Holdout:** De Pere is a Gate 3 holdout. It enters the descriptive tables only, and every test is repeated without it (Table 3, row 3). No model was fitted here.
4. **Stages differ.** Sun Prairie and De Pere are applications; the rest are issued permits. Three Kaukauna months are applications.
5. **Weak sources:**
   - Milwaukee, De Pere, Kaukauna and Waunakee are grade C.
   - De Pere and Waunakee structurally miss most ADU forms, so their zeros are lower bounds.
   - Kaukauna's 7 rest on a work-target flag with no description.
6. **Provisional rules for the 4 uncoded places** are source leads gathered while measuring. They are not in `wi_adu_rules.csv` and are used only in the labelled sensitivity.
7. **Kaukauna is coded "no ADU provision" from the Gate 2 search**, yet it issued 7 "Additional dwelling unit" permits in 2023–2025. Either the rules search missed a provision or these are units allowed in two-family zones. **The coding needs re-checking.**
8. **The counts are units**, as in Gate 3 (`permits` in rule v1 = second-home units). For these places units and permits differ by at most the Madison two-unit cases.

## 6. Recommendation

Of the three options, **choose "not predictive"**:

- Keep the owner's rule v1/v1.1 with unmeasured = restrictive.
- Do not assign unmeasured coded places to middle or active from their rules.

Reasons:

- (a) The rules in force during 2022–2025 have no rank correlation with measured activity (ρ = 0.05 over 9 places).
- (b) A rules-based grouping agrees with the measured group for 3–5 of 9 places, never more than the 6 of 9 from calling every place restrictive.
- (c) The only relation that holds is that explicit prohibition goes with zero (3 of 3 places, 0 over 63.8 thousand home-years), and the default already gives that.

**Rejected alternatives:**

- **A combined rule** ("prohibited → restrictive, allowed and large → middle") would be fitted to the same 9 places it is judged on.
- **A rules-based grouping** is rejected for reason (b).

Revisit when the measured set reaches 20. The cheapest additions:

- **Wausau:** monthly PDFs with parcel IDs, 2015–2026, if a person downloads them in a browser.
- **Green Bay 2025:** the same, from the live site.
- **Neenah 2022–2023 months** and **Watertown 2022:** records requests, outside this brief.
- **Eau Claire and Waukesha:** a search-form export, if the owner allows form-based public searches like the Pleasant Prairie precedent.

## 7. Decisions for the owner or conductor

1. **Internet Archive copies for Green Bay.** The city's own report PDFs were fetched from web.archive.org because the live site blocks plain HTTP. Accept as a source, or drop Green Bay?
2. **Re-check Kaukauna's rules** (see §5, item 7) before coding it into `wi_adu_rules.csv`.
3. **Milwaukee counts as measured here** (grade C candidates) but was "unmeasured" in Gate 3's `wi_observations_2022_2025`. Which treatment should the regression grouping use? This doc does not change `ca_regression_wi_activity_groups.csv`.
4. **Form-based public searches** (Eau Claire Evolve, Waukesha eTRAKiT) are the main route to more places. They were not used, per "no forms".

## Reproduce

```
uv run python scripts/build_wi_more_cities.py --fetch   # first time: downloads into data/raw/wimc_<place>/
uv run python scripts/build_wi_more_cities.py           # rebuild from caches (about 1 minute)
bash scripts/test.sh                                    # includes tests/test_wi_more_cities.py
```

PDF parsing uses the system `pdftotext` (poppler). Scanned months use `tesseract` and `pdftoppm` if installed: Howard October 2024, De Pere December 2022, three Kaukauna months. Without them those months come back empty and the coverage table says so.
