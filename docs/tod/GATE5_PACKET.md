# Transit-oriented density: Gate 5 packet (statewide review and the "good enough" decision)

Written 2026-10-27 by the TOD Gate 5 agent, for Ryan. **Status: draft for your decision.** It follows the structure of the [ADU Gate 5 packet](../gate5/README.md). No model output changed in this gate: every TOD reference table (`reference/tod_*.csv`) is the run adopted at Gate 3 and Gate 4 (AQ-050, AQ-051, AQ-053). The tool's TOD bundle changed only to apply the new cross-reform reporting rules (AQ-054) and plainer wording (section 4).

**Units.**
- **homes** = housing units in issued building permits (not completed homes), summed over 2027–2031 unless a year is named;
- **extra homes** = homes permitted with the law minus homes permitted under current law, in the same places;
- **station areas** = land within ½ mile of rail and bus rapid transit stations, or ¼ mile of stops on bus routes running every 15 minutes at the morning peak (the main case);
- **homes near stops** = 2020 census housing units in station areas (313,564), counted from 2020 census blocks;
- **Wisconsin's homes** for any cross-reform figure = ACS 2020–2024 total housing units (B25002): 2,778,572 (AQ-054);
- **statewide all-housing baseline** = homes of every type expected to be permitted statewide under current law: 122,619 over 2027–2031 (24,524 a year), from `reference/housing_baseline_statewide_by_year.csv`.

## 1. What this gate decides

Whether the TOD reform is good enough to **finalize**: its numbers frozen and sent to the ADU thread for the submission documents (AQ-053, G4-3). The plan's Gate 5 asks for a statewide reconciliation, a fresh-clone check, a final plain-wording pass and a rubric self-check ([MVP_EXECUTION_PLAN.md](../MVP_EXECUTION_PLAN.md#gate-5--statewide-adu-mvp-and-the-good-enough-decision)). TOD is the second of the three benchmark scenarios the submission needs (baseline plus at least 3 of 5).

## 2. The answer (adopted numbers)

If Wisconsin passed the benchmark TOD law on 1 January 2027 (stylized):
- **Under current law, about 14,464 homes** would be permitted in the station areas over 2027–2031 (range 8,386 to 21,874; Wisconsin's 10th and 90th percentile five-year outcomes).
- **The law would add** (extra homes, 2027–2031):

| Scenario (named after its evidence) | Extra homes | Share of the 313,564 homes near stops (2020 census) | Extra homes a year, statewide | Above the statewide all-housing baseline (24,524 homes a year) | Share of Wisconsin's 2,778,572 homes (ACS 2020–2024) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Little response, like Los Angeles's transit program | 171 | 0.055% | about 34 | 0.14% | 0.006% |
| **Typical response**, like the average loosening reform in 1,136 US cities | **2,509** (range 665 to 4,352) | 0.8% | **about 502** | **2.0%** | 0.09% |
| Strong response, like Auckland's 2016 upzoning | 17,148 | 5.5% | about 3,430 | 14.0% | 0.62% |

How the shared-unit columns are computed (in `scripts/build_tod_bundle.py`, from the reference files, not typed in): extra homes a year = five-year extra homes ÷ 5 (typical: 2,508.5 ÷ 5 = 501.7); above the baseline = five-year extra homes ÷ 122,619 (typical: 2,508.5 ÷ 122,619 = 2.05%, shown on screen as "2.05%"); share of Wisconsin's homes = five-year extra homes ÷ 2,778,572 (typical: 0.090%).

- **By year, typical:** 245, 233, 663, 1,202 and 166 extra homes in 2027 to 2031. The 2031 dip is the measured New York build-up, kept as fixed in advance (AQ-053, G4-2).
- **Where, typical:** Milwaukee metro 1,637, Madison metro 827, Kenosha County 45. By city: Milwaukee 516, Madison 501, Wauwatosa 293, West Allis 198, Verona 130. Eau Claire and every other mid-size city: 0 (no bus route runs every 15 minutes).
- **No median line.** A median line of real cases is shown only when a reform has at least 4 comparable cases (AQ-054). TOD's three scenarios rest on 3 whole-city studies, one each, so TOD has none. The old "median of the three studies" line, which equalled the typical response, is removed.

The scenarios are three bodies of evidence, about a hundredfold apart (17,148 ÷ 171 = 100); they are not a statistical interval.

## 3. Reconciliation

Checked on `reference/tod_model_*.csv` and on the tool's bundle, for the baseline (low, central, high), every scenario (little, typical, strong) and every year 2027–2031 plus the five-year total. Script: a scratch check, rerun on the fresh clone.

| Check | Result |
| --- | --- |
| Station-area stock | `tod_model_statewide.csv` stock = **313,564** homes = the sum of `homes_near_main` over all 1,912 rows of `tod_near_stop_homes_by_muni.csv` = the bundle's `stock_homes` = the sum of the bundle's 29 places' homes near stops = the sum of its three metro rows. |
| Baseline near stops | **14,463.78** homes (central; low 8,385.71, high 21,873.61). Places, counties, Assembly districts and Senate districts each add up to it. |
| Places → state | 29 place rows (28 with homes near stops, plus River Hills village, which has no home near a main-case stop but eligible land, and gets 5.7 typical extra homes). Largest gap: 0.0004 homes (extra), 0.0002 (baseline). No place with homes near stops is missing. |
| Places → counties → state | Each county equals the sum of its places (largest gap 0.0002 homes); counties without places are exactly 0; counties add to the state within 0.0001 homes. |
| Assembly and Senate districts → state | Largest gap 0.0041 homes (extra) and 0.0055 (baseline), from rounding each of 99 or 33 rows to 4 decimals. Each Senate district equals the sum of its three Assembly districts (0.0001). |
| District crosswalk coverage | All 29 TOD places are in `adu_model_district_crosswalk.csv`; each place's shares sum to 1 (within 0.000001). **No home is unallocated**: a "not allocated to a district" row would be 0.0. |
| Years → five-year total | Exact for every scenario (0.0000). |
| Bundle | Places, counties, districts and metros add to the statewide extra homes and baseline within 0.005 homes for every scenario. The builder's 30 validation checks pass. |
| No negative addition | 0 negative values at any level. |
| Shared all-housing baseline (AQ-054, new) | Places add up to 122,619.16 homes. Counties and districts add up to 122,710.83, plus the shared baseline's own "unallocated" row of **−91.67 homes** = 122,619.16. That row belongs to the parking thread's baseline (a reconciliation residual, not allocated to any place); the bundle carries it explicitly. |

**Gaps found: none in the TOD numbers.** Two caveats, both disclosed on screen:
- **District figures split each place's numbers by where its detached houses are** (the ADU crosswalk), not by where its homes near stops are. They reconcile exactly, but for Milwaukee and Madison, where 68% and 63% of homes are near stops, part of each city's addition is shown in districts far from a stop.
- The shared baseline's −91.67 unallocated homes (above).

## 4. Fresh-clone result

A fresh clone of `main` (commit `3a22322`) into `/private/tmp/claude-501/tod-gate5/clone`:

| Step | Result |
| --- | --- |
| `bash scripts/setup.sh` | OK (uv sync and `npm ci`) |
| `bash scripts/test.sh` | 531 tests OK, 3 skipped (they need git-ignored outputs); licence check 13 distributions, 1 flagged exception (`certifi`), 0 failures |
| `bash scripts/test_ui.sh` | 23 bundle tests OK; npm licences OK; type check and build OK; Playwright **122 passed, 6 skipped** |
| `PORT=4392 bash scripts/run_tool.sh` | Builds and serves; uses the committed ADU bundle because the processed ADU run is not in git (as designed); serves TOD run `tod-494eba2693` |

**Rebuild of every TOD reference CSV and the bundle, in order**, in a second clone with the raw files:

| Order | Script | Network? | Automated? | Result |
| --- | --- | --- | --- | --- |
| 1 | `fetch_tod_transit.py` | yes (3 min) | yes | **Refetched live on 2026-10-27.** 15 of 19 files had the same SHA-256 as the adopted run; 4 GTFS feeds changed bytes (The Hop, Fond du Lac, Beloit, Stevens Point). Every output below was still byte-identical. |
| — | other raw inputs (2020 blocks, 2024 boundaries, TIGER 2024, ACS, BPS, Wisconsin V12 parcels, city zoning, Madison parcels and permits, Milwaukee MPROP) | yes | yes: `fetch_legislative_districts.py`, `fetch_map_outlines.sh`, the foundation sources, `fetch_tod_parcels_zoning.py --counties all`, `build_madison_permits.py --fetch`, `build_wi_baseline.py` | **Not refetched** (copied from the working copy; checksums in each manifest). The city parcel, zoning and MPROP layers are "current" layers, so a later refetch will differ. |
| — | Madison TOD overlay boundary (`data/raw/madison_tod/tod_boundary.geojson`) | — | **no**: no fetch script and no manifest | Gap (decision T5-4) |
| — | `data/raw/tod_model/` (HUD cost table, ACS B25111, CBRE and IREM PDFs) | yes | **no**: fetched by hand with `curl`; manifest present | Gap; needed only for the abandoned cost-based method's diagnostics (decision T5-3) |
| 2 | `build_tod_stops.py` | no | yes | byte-identical (30 s) |
| 3 | `build_tod_station_areas.py` | no | yes | byte-identical (39 s) |
| 4 | `run_tod_model.py` | no | yes | byte-identical |
| 5 | `run_tod_scale_check.py` | only if its Census files are missing | yes | byte-identical |
| 4 again | `run_tod_model.py` | no | yes | byte-identical. The model reads `tod_scale_check.csv` and the scale check reads the model's per-acre tables; the per-acre tables do not depend on the scale check, so one more model run is a fixed point. |
| 6 | `build_tod_bundle.py` | no | yes | byte-identical: `tod-494eba2693` |

`git status` was clean after the whole chain. Not rerun here: the comparison cases (`fetch_tod_cases.py`, `run_tod_cases.py`; 6.2 GB of raw files), the Madison test and the AB 2097 test. Their outputs are committed model inputs and were reproduced byte for byte by the Gate 3 independent check.

After this gate's changes (section 5), the same clone rebuilt the TOD bundle as `tod-0c6f3bd953`, byte-identical to the working copy's build, and with the combined bundle rebuilt all tests passed: 533 Python tests OK (3 skipped), Playwright 122 passed, 6 skipped.

## 5. What changed in this gate

**AQ-054 rules (owner, all three reforms):**
1. **Shared unit.** The builder computes, from the reference files, each scenario's extra homes a year, its share of the statewide all-housing baseline and its share of ACS homes, plus each place's, county's and district's all-housing baseline. On screen:
   - Statewide comparison: a new card, "Against all new homes in Wisconsin", with one plain line ("In the typical response the law adds about 502 homes a year statewide, about 2.05% above the 24,524 homes a year Wisconsin is expected to permit under current law…") and the overlap caveat: reforms are never added together. Each scenario tile also says "about N a year".
   - Brief: the same line.
   - Where: a new column, "Extra a year, of all new homes a year there" (for example Milwaukee city: 103 of 996, +10.4%). No percentage is shown where fewer than 5 homes a year are expected, because a percentage of almost nothing misleads (Wauwatosa: 59 of 2).
   - Nothing is stacked or added to another reform on the TOD screens.
2. **Home count.** The 313,564 station-area homes stay on 2020 census blocks and are now labelled "2020 census" everywhere. The ACS count, 2,778,572, appears next to them on "Wisconsin today" and in the shared-unit line. The ladder's share of the state stays on the 2020 census total (2,727,726), so both sides of that ratio come from the same count; it is labelled as such.
3. **Median line.** Removed from the chart, legend, table and bundle. One plain line explains why: "A median line of real cases is shown only when there are at least 4 comparable cases. The transit-oriented density scenarios rest on 3 whole-city studies, one for each scenario, so there is no median line." A builder check enforces it.

**Plain-language fixes (wording only, no numbers):**
- "Current-law permits near stops" → "Permitted near stops, current law" (Where tables) and "Homes permitted near all qualifying stops in … under current law" (pilot tiles): the old label counted homes but called them permits.
- How sure: "Cases that change…" → "What-ifs that change…", and the column "Case" → "What if", so they are not confused with the comparison cases on Why.
- How sure: the 95th-percentile cap sentence rewritten in plain words.
- Why: "Per 1.0 of added floor area ratio" now says what that is ("extra floor space equal to the lot's area").
- Statewide comparison: "the study's 95% interval" → "range from the study's 95% interval".

**Tests (nothing hard-coded):** `tests/test_tod_bundle.py` gains a shared-units test (statewide baseline, ACS count, per year, both shares, every place's all-housing baseline, each level plus the unallocated row = the state, all read from the CSVs) and checks that no median line exists. `ui/tests/tod.spec.ts` checks the shared-unit line, the ACS count, the median note, the absence of the old line, the new Where column and the brief line against the bundle.

**Run id:** `tod-494eba2693` → **`tod-0c6f3bd953`** (8 files, 0.22 MB, 30 of 30 validation checks). `additions_by_area.json`, `map.json`, `pilots.json` and `why.json` are byte-identical; `statewide.json`, `areas.json` and `howsure.json` changed. **The combined bundle must be rebuilt** (`uv run python scripts/build_combined_bundle.py`): its run id hashes the TOD manifest, so 2 Python and 2 Playwright combined tests fail until then. No combined number changes.

## 6. Rubric self-check

Internal ratings out of 5, not predicted judging scores.

| Criterion (weight) | Rating | Strengths | Gaps | Concrete fixes |
| --- | --- | --- | --- | --- |
| Transparency and explainability (30%) | 4 | Every screen opens with what the reader is looking at; the trace marks each part observed, calculated or assumed; each scenario names and links its study; the hundredfold spread is explained as disagreeing evidence; sensitivities grouped by what they move; pre-registered Madison test shown with its weak pass. | The typical scenario rests on a study of mostly ADU and lot-size reforms (28 of 96 changed floor area, density or height); the README describes only ADUs. | Add a TOD section and the rebuild order to the README; keep the "typical rests on a general study" caveat on the brief (it is on How sure). |
| Replicability and scalability (25%) | 3 | Whole chain rebuilds byte for byte; fresh clone passes setup and both test suites; transit, parcels, zoning, Census and scale-check inputs fetched by script with checksums; national stop source (National Transit Map), so the station-area method runs for any state. | Madison overlay boundary has no fetch script or manifest; the cost-method raw files were fetched by hand; comparison cases need 6.2 GB of raw files; zoning is coded for two cities only (others use the scaled estimate); the model ↔ scale-check input loop is undocumented. | T5-3 and T5-4 below; one line in `docs/tod/MODEL.md` on the run order (model, scale check, model). |
| Usability (20%) | 4 | Seven screens, the same shell as ADU and parking; districts for legislators; printable brief; desktop and phone checked, no horizontal page scroll; Playwright structure and accessibility checks on 11 TOD views. | Where table is long on a phone and now has one more column; district split is an approximation; no manual screen-reader pass. | Owner's VoiceOver pass (shared with ADU); optionally hide the County and Room columns on phones. |
| Methodological soundness (15%) | 3 | Sizing by whole-city net effects avoids counting building moved from nearby blocks; scale check against metro records; held-out Madison test written before counting; never subtracts; reconciles at every level. | No Wisconsin test of the adopted sizing; effects measured 3+ years out are placed inside five years; typical study is not about transit upzoning; suburbs' room estimated and scaled by 0.719. | None before submission; Iowa-style future test does not exist for TOD. State the limits (done). |
| Policy insight (10%) | 3 | Clear message: a TOD law tied to 15-minute service reaches only Milwaukee and Madison; the typical response is about 2% above statewide permitting; Eau Claire shows the law misses mid-size cities; the 20-minute and all-½-mile what-ifs show the design levers. | The design levers (stop definition) sit on How sure, not on the brief; the combined TOD-plus-parking view is still "in development". | One brief sentence on the stop definition as the main design choice (2,509 → 2,813 with 20-minute buses; 716 with rail and rapid only). |

Weighted: 0.30 × 4 + 0.25 × 3 + 0.20 × 4 + 0.15 × 3 + 0.10 × 3 = **3.50 of 5**.

## 7. Limitations

1. **No Wisconsin test of the size of the effect.** The Madison test checked the per-acre method, which now only places homes.
2. **The typical scenario rests on a general study** of loosening reforms, mostly about accessory dwellings and lot sizes.
3. **Timing.** The studies measured effects 3 or more years after reform; the model places them inside 2027–2031.
4. **Concentration.** 98.7% of homes near stops are in Milwaukee County and Dane County; no other city has 15-minute buses (Green Bay's schedule could not be tested).
5. **District figures** split each place's numbers by its detached houses, not its homes near stops.
6. **Low recent Census permit counts** in Wauwatosa, South Milwaukee, Greenfield and Cudahy make their current-law figure very small (flagged to the parking thread, which owns the baseline).
7. **Raw-data gaps** for replication: the Madison overlay boundary, and the hand-fetched cost-method files (two of them commercial PDFs hosted by a third party).
8. **Not modelled:** rents, displacement, ridership, completions, lot-level outcomes.

## 8. Owner review steps

1. Run `bash scripts/run_tool.sh` (or `PORT=4180 …` if 4173 is busy), open `#/tod/compare`, and check the footer shows run `tod-0c6f3bd953` (after the combined bundle is rebuilt).
2. **Statewide comparison:** find 2,509 extra homes (typical), 171 and 17,148; the new card "Against all new homes in Wisconsin" (about 502 a year, about 2.05% above 24,524 a year); the note on why there is no median line; the chart has three scenario lines and current law, no dotted line.
3. **Wisconsin today:** 313,564 homes near stops labelled 2020 census, and the ACS count 2,778,572 next to it.
4. **Where:** switch to Assembly districts and back; check the last column for Milwaukee (103 of 996 a year) and that Wauwatosa shows no percentage.
5. **Brief:** the shared-unit line under the numbers table.
6. Read sections 3, 6 and 9 of this packet.
7. Choose: **finalize**, **iterate on named weaknesses**, or **revisit the model**.

**My self-assessment.** The numbers reconcile at every level and rebuild byte for byte from the scripts. The weakest part is still the evidence behind the typical scenario, which no amount of Wisconsin work can fix before submission. The rest of the gaps are replication housekeeping.

## 9. Decisions requested

| # | Decision | Recommendation |
| --- | --- | --- |
| T5-1 | **Is TOD good enough to finalize?** Freeze the adopted numbers (14,464 baseline; 171 / 2,509 / 17,148 extra homes) and send them to the ADU thread for the submission documents. | **Yes, finalize.** Reconciliation and the fresh-clone rebuild found no gap in the numbers; the remaining weaknesses are about the evidence (stated on screen) and housekeeping (T5-3, T5-4), which do not change any number. |
| T5-2 | Accept how AQ-054 was applied: the shared-unit card and brief line, a by-area column with no percentage under 5 homes a year, the ladder's share kept on the 2020 census with the ACS count beside it, and the median line removed. | **Yes.** |
| T5-3 | The cost-based method's raw files (CBRE and IREM PDFs from third-party or summary copies, fetched by hand) are needed for `run_tod_model.py` to run, though only for diagnostics of a method that was set aside. | **Make that step optional** (skip the feasibility table when the files are absent) and record the two sources in DATA_COMPLIANCE.md; no adopted number uses them. |
| T5-4 | The Madison TOD overlay boundary has no fetch script or manifest. | **Add it to `fetch_tod_parcels_zoning.py`** with a manifest entry before submission. |
| T5-5 | District placement: keep the detached-home split, or split by homes near stops using 2020 blocks. | **Keep for now** (disclosed, reconciles); do the block-level split only if the district view becomes central to the submission. |
| T5-6 | Add a TOD section and the rebuild order to the README. | **Yes**, in the submission-documents pass. |
