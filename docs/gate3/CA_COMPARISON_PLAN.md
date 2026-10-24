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
| Census BPS, California state, counties, permit-issuing places | 2010–2025, annual | **Pulled 2026-10-24** (`scripts/build_ca_bps.py`; state total equals counties and places every year) |
| ADU permits by jurisdiction, 2012–2019 | Building an ADU compilation of HCD-attributed counts, 527 jurisdictions (AQ-017) | Local CSV; to be added to the repository pipeline |
| ADU permits by jurisdiction, 2018–2025 | HCD APR Table A2, `UNIT_CAT = ADU`, building permits issued | To pull (data.ca.gov API) |
| One-unit detached homes by jurisdiction (denominator) | ACS 2020–2024 5-year, California places and county remainders | To pull (same keyless summary files as Wisconsin) |

The two ADU series overlap in 2018–2019; both are kept, and the reporting break is shown rather than smoothed (AQ-017). Unincorporated county areas are separate jurisdictions from their cities.

## Pre-registered definitions

**Outcome.** ADU building permits issued per 1,000 one-unit detached homes per year, by jurisdiction. Secondary: ADU permits as a share of (BPS total units + ADU permits), shown with the caveat that some ADUs also appear in BPS one-unit counts.

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
2. Assemble data: HCD APR pull, the 2012–2019 compilation into the pipeline, ACS California denominators, and a crosswalk of HCD jurisdiction names to Census places. This runs in parallel with estimating Wisconsin `x` and the Milwaukee ramp.
3. Run the study exactly as specified and publish the tables, including the fixed robustness checks.
4. Derive `y` paths, ramp, and spillover; integrate them into the model.
5. Walk through the Gate 3 owner steps, run independent review, and deliver the Gate 3 packet.
