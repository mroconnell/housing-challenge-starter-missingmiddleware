# California Comparison Study: Pre-Registered Plan

Prepared 2026-10-24 by the conductor for owner approval (AQ-031). **Status: proposed; no results have been computed.** Group definitions, outcomes, windows, and sensitivity checks below are fixed before any post-reform comparison is run, so the study cannot be tuned to a desired answer.

## Questions the study answers for the Wisconsin model

1. **Rate under a permissive statewide law (`y`).** How many ADU permits per 1,000 single-family homes did California jurisdictions produce once state law required ADUs to be allowed?
2. **Ramp.** How fast did production rise after each wave, year by year?
3. **Statewide spillover (AQ-027).** Did jurisdictions that were already permissive also rise after the state laws?
4. **ADU share of new construction.** What share of California's new units were ADUs before and after each wave, and what would that share imply for Wisconsin's Census BPS totals (owner's model, candidate for the upper path)?

## Data

| Input | Coverage | Status |
| --- | --- | --- |
| Census BPS, California state, counties, permit-issuing places | 2010–2025, annual | **Pulled** (`scripts/build_ca_bps.py`) |
| ADU permits by jurisdiction, 2012–2019 | Building an ADU compilation of HCD-attributed counts, 527 jurisdictions (AQ-017) | **Pulled** (`scripts/build_ca_comparison_data.py`) |
| Permits by jurisdiction and unit category, 2018–2025 | HCD APR Table A2 | **Pulled**; see [CA_COMPARISON_DATA.md](../gate2/CA_COMPARISON_DATA.md) for the step 0 reconciliation |
| One-unit detached homes by jurisdiction (denominator) | ACS 2020–2024 5-year, California places and county remainders | **Pulled** |

The two ADU series overlap in 2018–2019; both are kept, and the reporting break is shown rather than smoothed (AQ-017). Unincorporated county areas are separate jurisdictions from their cities.

## Step 0: reconcile California BPS with HCD APR (owner request, 2026-10-24)

Before the study, compare the two California sources jurisdiction by jurisdiction for 2018–2025 (the years both cover project-level permits):

- **Non-ADU units:** HCD single-family detached + single-family attached + 2–4 + 5+ permits versus BPS total units. Report the ratio by year, by county, and for the 50 largest jurisdictions, with the largest mismatches listed.
- **Where ADUs land in BPS:** compare BPS one-unit units with HCD single-family units, with and without HCD ADUs added. If BPS one-unit counts track "single-family plus ADUs", ADUs are partly inside BPS; if they track single-family alone, BPS leaves ADUs out. This decides how to read Wisconsin's BPS one-unit counts and whether the ADU-share model double counts.
- **Coverage:** jurisdictions that report to one source but not the other, late or missing APR filings, and BPS imputed versus reported values.
- **2012–2019 compilation versus HCD APR** in the 2018–2019 overlap, so the reporting break is measured, not assumed.

Results are descriptive data-quality findings; they set how the study's outcomes are read but do not change its pre-registered groups or windows.

## Outcome definition across the two states (amended 2026-10-24, before any results)

AQ-032 asks for the same definition in every state. HCD's public Table A2 cannot reproduce Wisconsin's "second homes on single-family lots" exactly: it has no SB 9 field (SB 9 appears only in free-text notes), and single-family-to-duplex conversions are mixed into "2 to 4" with new duplexes on vacant lots. Its ADU category also includes junior ADUs, legalizations, ADUs on multifamily lots, and ADUs built with a new house. So:

- **Calibration outcome (both states): ADU-type second homes.** California: HCD `ADU` building permits, excluding rows identifiable as legalizations; junior ADUs included (Wisconsin counts observed interior conversions too); ADUs on multifamily lots or built with a new house excluded where the record identifies them, otherwise noted as a known overcount. Wisconsin: detached, attached, conversion, and two-unit ADU components.
- **Wisconsin-only component: single-family-to-duplex conversions.** Shown in Wisconsin's headline, but with no California counterpart; any reform effect applied to them is a stated assumption, not a calibrated result.
- **Sources by year:** the 2012–2019 compilation for 2012–2017; HCD APR for 2018 onward, using permits dated in the report year (step 0's main measure). Fixed sensitivities: HCD issue-year measure for every year, and the compilation for 2018–2019. Step 0 found 2018 undercounted under the main measure (mostly Los Angeles), which is why both are shown.
- **Holdout:** every number that feeds the model is computed on non-holdout jurisdictions only; holdout jurisdictions appear only in descriptive data-quality tables.

## Pre-registered definitions

**Outcome.** ADU-type second homes (as defined above) permitted per 1,000 one-unit detached homes per year, by jurisdiction. Secondary: ADU permits as a share of (BPS total units + ADU permits), shown with the caveat that some ADUs also appear in BPS one-unit counts.

**Waves and their own pre-periods** (AQ-031):

| Wave | Effective | Main content | Pre-period | Post window |
| --- | --- | --- | --- | --- |
| 1 | 2017-01-01 | SB 1069 / AB 2299: ministerial approval, conversions, parking limits | 2014–2016 | 2017 (before wave 2) |
| 2 | 2018-01-01 | SB 229 / AB 494: cleanup | 2014–2016 | 2018–2019 |
| 3 | 2020-01-01 | AB 68 / AB 881 / SB 13: exemption ADU floor (65852.2(e), later 66323), fee limits, owner-occupancy pause | 2017–2019 | 2020–2025 |

**Groups**, defined only from pre-period outcomes (consistent with the outcome approach, AQ-028):

- *Already permissive:* jurisdictions in the top quarter of ADU permits per 1,000 homes in the wave's pre-period, with at least 3 permits.
- *Restrictive:* jurisdictions with zero reported ADU permits in every pre-period year.
- *Middle:* everyone else; reported but not used for the main contrast.
- Jurisdictions with missing reports in a pre-period year are excluded from that wave, not counted as zero.

**Comparisons.**

- Year-by-year group means (event-study table and chart), relative to each group's own pre-period mean.
- Difference-in-differences: restrictive group's change minus permissive group's change, per wave.
- **Spillover:** the permissive group's own post-wave change. Wave 1 is shared by both groups' clocks, so spillover is read mainly from wave 3.
- **Ramp:** restrictive group's year-k level as a share of its year-4-to-6 plateau after wave 3.

**Fixed robustness checks** (all shown, none chosen after the fact):

- No COVID adjustment. A version excluding 2020 is reported alongside the main result.
- Alternative permissive cutoff (top third instead of top quarter).
- City of Los Angeles excluded, because its size and early surge could dominate group means.

## Statewide view: Wisconsin versus California (owner request, 2026-10-24)

A simple statewide "health" comparison using the same ADU-blind source in both states:

- Census BPS permitted units per 1,000 existing homes per year, Wisconsin and California, 2010–2025, each indexed to its own 2014–2016 average, with the three California wave dates marked.
- California's HCD ADU permits shown as a layer on top of its BPS line, so the share of any divergence that is ADUs is visible. Step 0 decides whether California BPS already includes some ADUs, which determines whether that layer is added or already inside the line.
- Reading: divergence after a wave is descriptive. Total permits also respond to rents, interest rates, and other reforms, so only the ADU layer is attributed to ADU policy. The model's expectation that Wisconsin's ADU rate converges toward California's after a statewide law is an assumption drawn from the study below, stated as such.

## Held-out data for testing the model (pre-registered)

Set aside before any fitting, and used only to test the finished curve:

- **California jurisdictions:** a random 20% of jurisdictions (fixed random seed, drawn and saved before the study runs), excluded from estimating the plateau, ramp, and spillover; the fitted curve must predict their post-wave rates.
- **Wisconsin:** Madison and Sun Prairie are not used to fit the California curve; Madison versus Sun Prairie is the in-state check.
- **Unknown local rules (AQ-027):** a random sample of the 37 coded Wisconsin places is held out to test the rule that unknown places behave like restricted ones, by predicting their current rate from ordinance status alone.
- **Later states:** Oregon (2018 law, Portland earlier), Washington (2020), Montana (2023), and Massachusetts (2025), as available, test the curve out of state.

Results on held-out data are reported as they come out, including misses. Later regression on all data (to refine the curve) happens only after the held-out test is published.

## How the results feed the Wisconsin model

| Study result | Model input |
| --- | --- |
| Restrictive group's post-wave-3 plateau | Candidate central or upper `y`, alongside the Madison floor ÷ 0.8 (AQ-024, AQ-030) |
| Year-by-year ramp | `ramp[t]` for each path; a faster upper-path ramp only if the data show one |
| Permissive group's post-wave change | Spillover term for Wisconsin places already at benchmark |
| ADU share of new units | Owner's share model: share × Wisconsin BPS totals, an upper-path candidate and cross-check |

Transfer to Wisconsin is an assumption, not a result: California has higher rents and land values, a longer reform history, and counts that include some conversions and legalizations. Gate 3 states this beside every transferred number.

## Wisconsin check

Madison (by right since December 2021) versus Sun Prairie (prohibited until May 2026), same housing market: difference in ADU permits per 1,000 homes before and after 2021, as a check on the central path.

## When this happens in Gate 3

1. Owner approves this plan, alongside the Gate 2 decisions.
2. Assemble data and run step 0 (BPS versus HCD reconciliation): HCD APR pull, the 2012–2019 compilation into the pipeline, ACS California denominators, and a crosswalk of HCD jurisdiction names to Census places. This runs in parallel with estimating Wisconsin `x` and the Milwaukee ramp.
3. Run the study exactly as specified and publish the tables, including the fixed robustness checks.
4. Derive `y` paths, ramp, and spillover; integrate them into the model.
5. Walk through the Gate 3 owner steps, run independent review, and deliver the Gate 3 packet.
