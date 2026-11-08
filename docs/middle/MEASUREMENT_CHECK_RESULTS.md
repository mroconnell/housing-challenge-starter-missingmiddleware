# Middle housing: how permits are recorded, and a proposed measure

Run 2026-11-08 (UTC) under the no-peeking rules in [MEASUREMENT_CHECK_LOG.md](MEASUREMENT_CHECK_LOG.md). Only documentation, field lists, category labels, records from before each reform, and places outside every test were read. No result was seen, beyond the disclosures in the log. Full source notes:
- [measurement/CENSUS_AND_STATES.md](measurement/CENSUS_AND_STATES.md)
- [measurement/CALIFORNIA.md](measurement/CALIFORNIA.md)
- [measurement/CITIES.md](measurement/CITIES.md)

**Not locked.** Ryan decides the measure. The audit thread reviews it before any lock.

## How each source files middle housing

| Case | Census permits (BPS) | Washington (OFM) | California (progress reports) | Maine (MOCA) | City permit records |
| --- | --- | --- | --- | --- | --- |
| Townhouse | 1-unit, if it has a ground-to-roof wall, no unit above another, and separate heating and meters | Multi-unit, by row size: a row of 3 is "3/4" | "SFA" by definition, but rows show townhomes filed as "2 to 4" and "5+" | Single-family | One permit per unit (Austin, Raleigh, Charlotte, Portland, Sacramento) |
| Side-by-side duplex with separate utilities | 2 one-unit buildings | Duplex | Varies | 2 single-family homes | Varies |
| Stacked duplex, triplex, fourplex | 2-unit or 3–4 unit | Duplex or 3/4 | "2 to 4" | 2-unit or 3–4 | Census codes 103 and 104 |
| Home on a split lot (SB 9, Oregon land division) | 1-unit; the split records nothing | 1-unit | SB 9 flag from the 2023 report only; no flag for 2022 | 1-unit | Only in description text |
| Small-lot subdivision home (California SB 684, SB 1123) | 1-unit | — | No flag | — | Only in description text |
| 5–6 unit building | "5+" (5 to 499 units) | "Five+" | "5+" | 5+ | Units field, where reliable |
| Conversion (house to duplex) | Not counted | Counted: 1 removed, 2 added | No flag | Counted | Some cities (Minneapolis, Sacramento) |
| ADU | Only if it is a new detached building (1-unit) | Own column | Own category | Own row | Often hidden in single-family codes |

## What this means

1. **No source records lot splits or small lots before the reforms.** California's SB 9 flag starts with the 2023 report, so it has no "before". Cities show splits only in free text.
2. **Census counts most middle housing as one-unit homes.** That covers townhouses, side-by-side duplexes, split-lot homes and small-lot homes. Its 2–4 unit column holds only stacked or shared-system buildings.
3. **Sources disagree on townhouses.** Census and Maine count them as one-unit; Washington counts them as multi-unit. So Washington's counts can't be pooled with Census counts.
4. **No source separates 5–6 unit buildings at city level.**
   - Census 5+ ranges from 5 to 499 units.
   - In 2015, only 126 of 1,712 places with 5+ permits (7%) had exactly one 5–6 unit building, the only case where the size is known.
5. **Unit type can't tell infill from tract building.**
   - Codes 103 and 104 also appear in large apartment complexes and tract duplexes.
   - Telling them apart needs parcel and plat records, city by city. The handbook warns against that kind of parcel-level precision.
6. **City flags made for the reform can't be used.** Raleigh's `missing_middle` flag marks units the reform enabled, starting 2021-07-06. It has no match before the reform.
7. **Census fills in some places.** In 2015, 2,868 of 20,122 place rows (14%) were fully estimated by Census (0 months reported).
8. **Montana's Census counts miss small buildings.** Some Montana areas don't require permits for 1–4 unit buildings.
9. **California's Starter Home act is new.** SB 684 has applied since 2024-07-01 (multifamily-zoned lots) and SB 1123 since 2025-07-01 (vacant single-family lots). That is fewer than 2 full years, so it goes on the candidate list as "not yet".

## Proposed measure

| Role | Measure | Why |
| --- | --- | --- |
| **Main** | **All homes permitted** (Census, all building sizes) per 1,000 single-family homes per year | Catches townhouses, lot splits, small lots and 5–6 unit buildings. Tract building that would have happened anyway cancels out against the comparison places. It is what the handbook scores (change in housing production). It exists in every state. |
| Second | Homes in 2–4 unit buildings (Census) | The only middle-housing type Census sees directly. Read it as a lower bound on the middle-housing part. |
| Second | One-unit homes and 5+ homes (Census) | Shows where any change in all homes came from. |
| Check only | Townhouse-inclusive counts from city records (Austin and Minneapolis; Portland if its licence passes) and Washington's own counts | Measures how much the Census split misses. Not pooled with Census counts. |

**Cost of the main measure:** all homes vary much more from year to year than 2–4 unit homes do. Tests will only detect larger effects. The smallest detectable effect for each test can be computed from years before the reforms only, before lock.

## Licences found

| Source | Terms | Proposed |
| --- | --- | --- |
| Austin | Public domain | Use |
| Minneapolis | Copyright waived | Use |
| Raleigh | City may "require the termination of any and all displaying, distributing or otherwise using" the data; no open licence | Out under the licence rule |
| Mecklenburg County | Disclaimer only; no licence | Out under the licence rule |
| Sacramento | Use "subject to the City's Open Data Terms of Use"; the City may claim rights; no right to redistribute | Out under the licence rule |
| Durham | ODbL | Out (already) |
| Portland | No licence stated (not re-checked) | Check before use |

## Choices for Ryan

1. **Main measure:** all homes (proposed), or 2–4 unit homes only?
2. **Townhouses and lot splits:** accept that they are counted only inside "all homes", not on their own?
3. **Licences:** drop Raleigh, Mecklenburg and Sacramento city records (Census counts still cover those cities)?
4. **Washington:** use its own counts only within Washington, never pooled with Census?
5. **Power first:** compute the smallest detectable effect for each test, from pre-reform years only, before lock?
