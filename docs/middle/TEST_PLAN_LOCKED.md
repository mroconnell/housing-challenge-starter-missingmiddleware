# Middle housing: test plan (LOCKED 2026-11-09)

Drafted 2026-11-06. v1 on 2026-11-09 followed the [measurement check](MEASUREMENT_CHECK_RESULTS.md) and the [power check](POWER_CHECK.md). **v2 on 2026-11-09 adds the weak-spot and backdoor fixes Ryan accepted** (see "Changes in v2"). **v3 on 2026-11-09 answers the audit of v2** ([review](../audit/MIDDLE_HOUSING_DESIGN_V2_REVIEW_2026-11-09.md); see "Changes in v3"). **v4 on 2026-11-09 changes the primary test** so that its result is useful either way (Ryan: "a narrowish range that excludes 0, or a range that includes 0 and indicates we don't know"); see "Changes in v4" and the disclosure there.

**Not locked.** No count in this design has been run, and it states no expected results. The audit thread reviews it before any lock. Ryan decides any tool change. Candidates and data: [CANDIDATES.md](CANDIDATES.md). No-peeking rules and log: [MEASUREMENT_CHECK_LOG.md](MEASUREMENT_CHECK_LOG.md).

**Lock record.** Locked 2026-11-09 on Ryan's go ("yes and yes", message cmsg_01C3Z6G8h32D4UwCcjcGMM7qTLvWJ1Ge1EZPRt6izReSic). Audit verdict on v5: lock OK ([review, all rounds](../audit/MIDDLE_HOUSING_DESIGN_V2_REVIEW_2026-11-09.md)). Content = draft v5 plus the two audit lock items. The only lock-time changes are the run order and moving the "before lock" no-outcome steps to step 0. Any change after this commit is labelled **post hoc** in the results.

## The question

When a state makes 2–4 homes legal on lots that allowed one house, does the number of homes permitted each year in 2–4 unit buildings change, and by how much? The answer is per 1,000 single-family homes, compared with the same places without the law. (The handbook scenario allows 2–6 homes. See "What we count" for why we measure to 4.)

**Causal diagram:**
- **The path we want:** law → 2–4 homes legal on house lots → projects built → homes permitted.
- **Backdoors** (each is handled under "How backdoors are handled"):
  - city size, land and existing homes;
  - interest rates, costs and COVID;
  - pro-housing politics;
  - low building before the law;
  - a housing shortage that changes over time;
  - other housing reforms;
  - state ADU laws (a new detached ADU is a 1-unit building in Census, so it sits inside M1);
  - spillover to nearby places;
  - Census filing rules.

## Primary result (fixed now)

**Test 1 with four states (Oregon, California, Maine, Vermont), measure M2 (homes in 2–4 unit buildings).** Every other test and measure supports it. No other result may be promoted to the headline after results are seen.

- **Why M2:** the [design bake-off](DESIGN_BAKEOFF.md) (2012–2018 data only) found M2 gives the narrowest range in every design: about ±0.28 per 1,000 single-family homes per year with four states, against about ±1.8 for M1.
- **Goal (Ryan, 2026-11-09):** a range that excludes 0 shows a causal effect (rise or fall). A range that includes 0 means we do not know; it is never read as "no effect", and its width is always reported.

## What we count

- **Unit:** homes permitted, per 1,000 single-family homes, per year.
- **Denominator:** single-family homes, detached plus attached (ACS 2020–2024, table B25024, rows 2 and 3), adjusted to each year as in the ADU model (`homes_by_year.py`).
- **Source:** Census permits (Building Permits Survey) for every test and every state (Ryan, 2026-11-08). Homes are counted, not lots.

| Measure | What it counts | Role |
| --- | --- | --- |
| M1: homes in 1–4 unit buildings | Census 1-unit, 2-unit and 3–4 unit homes. Census files townhouses, side-by-side duplexes, split-lot and small-lot homes as 1-unit, so they are all inside | Second: always published beside M2; includes townhouses and split-lot homes but is too noisy to decide alone |
| **M2: homes in 2–4 unit buildings** | Census 2-unit and 3–4 unit homes. Leaves out townhouses and split-lot homes (Census files them as 1-unit) and mostly leaves out ADUs | **Main** (v4) |
| M2 share: M2 ÷ M1 | Share of 1–4 unit homes that sit in 2–4 unit buildings | Second. Guards against ordinary house-building swings: in California, 2018–2021, detached houses were 195,736 of 233,636 homes in 1–4 unit buildings (84%) |
| M3: all homes | Every building size | Always published beside M2, labelled as the net effect on housing |
| M4: homes in 5+ unit buildings | Census 5+ | Check (substitution) |
| M5: townhouse-inclusive counts | City records (Austin, Minneapolis; Portland if its licence passes) and California progress reports (SFA category) | Measurement check only (Test 6) |

- **Why stop at 4:** in the power check, leaving out 5+ buildings roughly halved the noise in every test. Census cannot cap at 10, 30 or 100 units; 5+ is its only size cut.
- **5–6 unit sensitivity:** M1 plus 3.0% of Census 5+ homes. That is the share of 5+ homes in projects of 5 or 6 homes in California's 2018–2021 progress reports. Reported beside M1 as a rough estimate.

## Reporting rules (fixed before any result)

- **M2 leads** every result, chart and tool line. **M1 and M3 are always published right beside it**, at the same size, labelled as too noisy to decide on their own (v4; replaces the v1–v3 rule that M1 leads).
- **If M2 and M1 or M3 point in different directions** under the reading rule, the headline says so in plain words.
- **Every result states the range of effects the data still allow**, not only whether the range excludes 0.
- **Test 1 headline requirements (audit of v4, must 1):**
  - (a) It says that the measure (M2) and the four states were chosen after raw state trends in M2 had been seen for them (see the v4 disclosure).
  - (b) The Oregon + California result is shown beside the four-state result, at the same size. If the two read differently, the headline says so.
  - (c) The comparison places' own before/after change in M2 is reported beside each result, in the same units.
  - (d) The open backdoors (see the table) are listed beside the headline.
- **"No detectable change" never means zero.** Every result is shown with its test's smallest detectable effect from the power check, in the same units.
- No measure or test is promoted or dropped after results are seen. Any later change is labelled post hoc.

## Test 1. State laws against similar places elsewhere (primary)

- **Treated states:** Oregon, California, Maine and Vermont: every state whose law gives at least 2 full years of data after it by 2025. Oregon and California alone are a sensitivity.
- **Comparison regions:** West for Oregon and California; Northeast for Maine and Vermont (New Hampshire, Massachusetts, Connecticut, Rhode Island, New York, New Jersey, Pennsylvania).
- **California is labelled "California's 2022 package".** SB 9 arrived alongside other state housing laws, which this design cannot separate: ADU laws, AB 2011 (2023), SB 684 (operative 2024-07-01) and SB 1123 (2025-07-01).

| State | Before | After | Left out |
| --- | --- | --- | --- |
| Oregon | 2015–2019 | 2023–2025 | 2020–2022 (compliance years and COVID) |
| California | 2018–2021 | 2023–2025 | 2022 (first year, reported separately) |
| Maine | 2019–2023 | 2024–2025 | — |
| Vermont | 2019–2022 | 2024–2025 | 2023 |

- **Comparison pool (fixed now; audit fix 1):**
  - Census permit-issuing places in the **same Census region** as the treated state, in states with no statewide middle-housing law through 2025.
  - For Oregon and California (West region), that means places in Alaska, Hawaii, Idaho, Nevada, Utah, Wyoming, Colorado and New Mexico.
  - Washington, Maine, Vermont, Montana and Arizona places are left out everywhere.
  - Leave out every candidate city.
  - Leave out any place found with its own 2–6 unit reform. Before lock, comparison places are screened against reform lists only, never outcomes: NYU Furman Land Use Reform Tracker, Pew, the Mercatus and Terner lists, and [CANDIDATES.md](CANDIDATES.md).
  - **Leave out places in counties that border Oregon or California** (Census county adjacency file), to avoid spillover.
- **Comparison-state screen (fixed now from statutes only; audit of v4, must 2):**
  - **Rule:** a state is never a comparison state or a fake law state if a statewide middle-housing, transit-area or station-area density, by-right multifamily, or multifamily parking-minimum law **first binds between 2015 and 2025**. Laws binding before 2015 are constant across every window and are allowed.
  - **Dropped under the rule:**
    - Massachusetts (MBTA Communities, 2023–2024);
    - Colorado (HB24-1313, HB24-1304, 2024–2025);
    - Rhode Island (2023–2024 package);
    - Connecticut (PA 21-29, 2021–2023);
    - Utah (HB 462 station-area plans, 2022–2025);
    - New Hampshire (SB 284 parking cap, 2025-09-13);
    - Texas (SB 840, SB 15, 2025-09-01);
    - Florida (Live Local Act, 2023-07-01);
    - Maryland (HB 538, 2024).
  - **Places dropped for their own reform of the same kinds (2015–2025):** Anchorage, Boise, the five New York City boroughs, Philadelphia, Pittsburgh, Trenton, Buffalo, Reno, St. Paul, Chicago, Alexandria, plus every candidate city.
  - **Remaining comparison states:**
    - West: Alaska, Idaho, Nevada, New Mexico, Wyoming. Hawaii's permits are issued by counties, which the place files do not use.
    - Northeast: New York, New Jersey, Pennsylvania.
  - **Sources:** each state's call, law, dates and source are in [measurement/COMPARISON_STATE_REFORMS.md](measurement/COMPARISON_STATE_REFORMS.md). ADU-only laws are not in the rule (they mainly add 1-unit buildings), but they are listed there.
  - **Fake law states** follow the same rule. That leaves 34 states.
- **Unmatched places (fixed now):** a treated place with no comparison place at ½–2× its population is left out of Test 1. The share of the treated state's single-family homes left out this way is reported beside the result. This applies to the largest California cities, because the screened West pool is small.
- **Unmatched-place sensitivity (audit of v5, item 1; fixed now):** unmatched places get comparison places at ½–2× their population from the screened pool, region first, then the nation, using the same ladder as Test 3. This version is reported beside the main result, together with the unmatched share.
- **Buffalo:** dropped under the fixed rule, because its Green Code first bound in 2017. The sources file now says the same.
- **Matching, fixed now:**
  - Each treated place is matched to pool places at ½–2× its population. Its comparison rate is the pooled rate of that set.
  - The comparison side for a state is its places' comparison rates, weighted by each place's single-family homes.
  - Matching does not use outcomes. The power-check code uses the same rule (`scripts/middle_power_check.py`, `test1_state_stats`).
- **Statistic:** pooled log rate ratio, weighted by homes. In treated places it is permits after ÷ (homes × years after), over the same before. That is divided by the same ratio in comparison places. The difference in homes per 1,000 single-family homes per year is reported second.
- **Main inference: rank against fake law states.**
  - Each untested state is treated as a fake law state and run through the same statistic. Its pool is places in its own Census region in other untested states, with the same matching rule. That gave 43 states in the rerun power check.
  - Draws are made in sets of four, one fake state per real state's windows.
  - 10,000 sets, seed 20261103.
  - **The set statistic is the unweighted mean of the four states' log rate ratios**, for fake sets and for the real set alike. It is also reported in homes per 1,000 single-family homes per year.
  - The real set is placed in that spread.
- **Second inference:** 90% bootstrap over places, clustered by state, plus a leave-one-state-out range. With only 4 treated states, this can look too precise, so it is not the main reading.
- **Reading rule (symmetric; the 5th and 95th percentile cut-offs are a convention):**
  - Above the fake sets' 95th percentile: a rise relative to comparison places (the 90% range excludes 0).
  - Below their 5th percentile: a fall.
  - Otherwise: we do not know (the range includes 0). The range is always reported.
- **Sensitivities, fixed now:**
  - **Oregon and California only** (pairs of fake states).
  - **Oregon before window 2015–2018** (audit fix 6). The law passed on 2019-08-08, and waiting for it could have changed 2019 permits.
  - **California without ADUs** (audit fix 2). M1 minus the ADU permits in California's progress reports (Table A2 "ADU" category), by jurisdiction and year, for California places only. The progress reports do not split detached from attached ADUs, and Census leaves out attached and converted ADUs. So this removes too much, and it is read as a bound, not a correction.
  - **Oregon has no comparable ADU series.** Its M1 result is read with that stated.

## Test 2. Cities just above and below Oregon's 10,000 line (side check)

- **Why:** cities were sorted by the state's own population estimate (PSU certified July 2020), not by any choice of theirs. Three cities over 10,000 by the Census 2020 count were left out ([OREGON_CUTOFF_CHECK.md](OREGON_CUTOFF_CHECK.md)).
- **Groups (law's count, non-Metro):** covered cities over 10,000 (duplexes from 2021-06-30) against left-out cities up to 10,000.
- **Bands:** main 9,000–10,999 (5 covered, 6 left out); wider 5,000–14,999 reported second.
- **Windows:** before 2016–2018; after 2022–2024. HB 3395 (2023) extended duplexes to cities of 2,500+ from 2025-06-30, so 2025 is out.
- **Statistic:** covered cities' mean change in rate minus left-out cities' mean change. 90% bootstrap over cities, seed 20261103. Same symmetric reading rule.
- **Data columns (audit fix 5):** Census filled-in columns, because reported-only data leave 1 covered and 3 left-out cities in the band. Reported-only is a sensitivity.
- **Before this test runs (step 0):** check each left-out city's zoning code (documents only) for duplexes allowed before 2021. A left-out city that already allowed duplexes on most single-family lots before 2021 is dropped, and the drop is reported.
- **Known limit:** housing production strategies (ORS 197A.100) use the same line. Their effect cannot be separated.
- **Later:** the same design for Montana (cutoff 5,000; in force 2024-09-03) and Washington (cutoff 25,000), when their data allow.

## Test 3. City reforms against stand-in cities (supporting only)

**Disclosure (audit fix 4):** Census permit counts by building size for 2012–2025 were seen for all five cities on 2026-11-06, before M1 was chosen. Test 3 is therefore read as supporting only. It can never lead.

- **Cities and reform years:**
  - Minneapolis 2020, with 2022–2024 flagged as injunction years;
  - Raleigh 2022;
  - Spokane 2023;
  - Walla Walla 2019;
  - Portland 2022.
- **Windows:**
  - Before: the 3 full years before the city's first reform was adopted. Example: Raleigh adopted TC-5-20 in July 2021, so its before years are 2018–2020.
  - After: every full year from the first full reform year to 2025.
- **Stand-ins:** at least 20 cities per real city that never had such a reform, each given the real city's reform year.
  - Drawn from its own state, then its Census division, then the nation, at ½–2× its population (the parking rule).
  - **Never from a state whose middle-housing law binds during that city's after window** (audit fix 3): Oregon, California, Washington, Maine, Vermont and Montana.
  - **Portland is labelled as overlapping Oregon's HB 2001.** Its result mixes the city's own reform with the state law.
  - Stand-ins are screened against the same reform lists as Test 1.
- **Data:** Census permits for all five cities. Census filled in Spokane's 2018, 2020 and 2021 rows entirely, so Spokane uses the filled-in columns, is flagged, and is checked against Washington's own (OFM) total permits. OFM counts are never pooled with Census counts.
- **Result:** each real city's percentile among its stand-ins, plus their middle-90% spread.
- **Reading rule:**
  - Above the stand-ins' 95th percentile: a rise.
  - Below the 5th: a fall.
  - Otherwise: no detectable change.

## Test 4. Fake reform years (pre-trend check)

- **What:** rerun Tests 1, 2 and 3 with fake reform years, using only years before every real reform was passed.
- **Exact fake windows (fixed now; audit fix 7):**

| Place | Fake before | Fake after | Why it is clean |
| --- | --- | --- | --- |
| Test 1: Oregon, California, Maine, Vermont (and their fake-state spread) | 2012–2014 | 2016–2018 | Laws passed 2019-08-08 (Oregon), 2021-09-16 (California), 2022 (Maine), 2023 (Vermont) |
| Test 2: Oregon cities | 2012–2014 | 2016–2018 | Before HB 2001 passed |
| Test 3: Minneapolis, Raleigh, Spokane, Portland | 2012–2014 | 2016–2018 | Adopted 2019-11, 2021-07, 2022-07 and 2020-08 (Oregon's law 2019-08) |
| Test 3: Walla Walla | 2012–2014 | 2015–2017 | Adopted 2018-12-19 |

- **Reading rule:** the fake-year result should read "no detectable change" under each test's own rule. If it does not, the main result is read as partly a trend that was already under way.
- **Note:** these windows match the power check's. The power check used only fake states and stand-ins, never these places.

## Test 5. Hide each case in turn (held-out test)

- **What:** as in the ADU A3 test, hide each treated state or city in turn, predict it from the rest, and record the miss.
- **Output:** "how far off the method was for a place it never saw", shown beside the result.
- **Limit:** with 7 cases (2 states, 5 cities), the range is rough.
- **Rule:** report only.

## Test 6. How much Census permits miss (measurement check)

- **What:** in places with both counts, compare M5 (townhouse-inclusive records) with Census M1 and M2, before and after each reform.
- **Places:** Austin, Minneapolis, California (progress reports), and Portland if its licence passes.
- **Output:** the ratio of each record count to the Census count, with a 90% bootstrap interval.
- **Rule:** report only.

## Test 7. Did other building fall? (substitution check)

- **What:** Tests 1 and 3 rerun on M3 (all homes), M4 (5+ unit homes) and one-unit homes.
- **Rule:** report each with the same reading rule as its test.

## Law strength (coded before lock, no outcomes)

For each treated state and city, record:
- homes allowed per lot;
- where the rule applies (city sizes, zones);
- the share of single-family homes covered;
- any carve-outs.

This shows how far each law falls short of the handbook scenario (2–6 homes, 3 stories). The Wisconsin plan can then scale results, and the scaling rule is set in that plan.

## How backdoors are handled

| Backdoor | How the design blocks it | Status |
| --- | --- | --- |
| City size, land, existing homes | Before/after within each place, so fixed traits cancel | Blocked |
| Interest rates, costs, COVID | Comparison places of similar size in the same region share the years | Blocked |
| Pro-housing politics | The fixed part cancels; Test 2 compares cities under the same state politics | Mostly blocked |
| Low building before the law (bounce-back) | Test 4; matching on size and region | Blocked only if Test 4 passes |
| Housing shortage changing over time | Test 4 catches trends already under way | **Partly open:** a shock starting the same year as the law is not caught |
| Other housing reforms | Reform-list screening; candidate cities left out; California labelled as a package | **Partly open:** California's package; Oregon's housing-plan rule at the same line |
| Comparison states' own reforms | Statute screen drops states and places with qualifying laws binding 2015–2025 | Blocked for statewide laws found; **open** for local reforms not on any list |
| Large state housing funding programs (for example Colorado's Prop 123, New Jersey's fair-share law) | Not screened: funding is not zoning | **Open** |
| State ADU laws (detached ADUs are 1-unit in Census, inside M1) | California sensitivity without ADUs (a bound); M2 read beside M1 | **Open:** Oregon has no ADU series; comparison states' ADU trends unknown |
| Spillover to nearby places | Counties bordering Oregon or California left out of comparisons | Blocked for neighbours; wider spillover open |
| Census filing rules | M1 includes townhouses and split-lot homes; Test 6 measures the remaining gap | Measured, not removed |

## Data rules

- **Census permits:** use the "reported" columns, and keep only places reporting all 12 months in every window year. Census's filled-in columns are a sensitivity case, with two exceptions where filled-in columns are the main case and reported-only is the sensitivity: Spokane (Test 3) and the Oregon line (Test 2).
- **Licences (Ryan, 2026-11-09):**
  - Out: Durham (ODbL), Raleigh, Mecklenburg County and Sacramento (no open licence). Census still covers those cities.
  - In: Austin (public domain) and Minneapolis (copyright waived).
  - Portland: checked before use.
- **Data needed:** Census permits and ACS are on disk. Also needed: the Census county adjacency file, Census place files for 2010–2011 (Test 4), and Austin and Minneapolis records from open APIs.

## Run order

Set at lock (Ryan, 2026-11-09: "yes and yes" to locking and to running the Oregon edge test first). Changing the order cannot change any estimate, because every rule is fixed here.

1. Test 2 (Oregon line), after its zoning check (step 0).
2. Test 6 (measurement).
3. Test 4 (fake years).
4. Test 1 (primary).
5. Test 3.
6. Tests 5 and 7.

**Step 0, before the test each feeds, no outcomes:** the Test 2 zoning check, border-county list, law-strength coding, and any remaining reform-list screening. These were listed as "before lock" in v5. They are done before the test that needs them, still without reading outcomes, and are logged in MEASUREMENT_CHECK_LOG.md.

## Smallest detectable effects (power check, 2012–2018 permits only)

| Test | M2: homes in 2–4 unit buildings | M1: homes in 1–4 unit buildings |
| --- | --- | --- |
| 1. Four states (primary), screened pool | about 0.41 (range about ±0.27) | about 3.1 |
| 1. Oregon and California only, screened pool | about 0.69 | about 4.9 |
| 2. Oregon line, 9,000–10,999 | about 1.8 | about 8.4 |
| 3. One city (screened stand-ins) | 0.6 to 2.3 | 10.4 to 13.8 |

All per 1,000 single-family homes per year; smallest change caught with 80% power. The Test 1 rows were rerun on the screened pool (34 fake states). Sources: [DESIGN_BAKEOFF.md](DESIGN_BAKEOFF.md), [POWER_CHECK.md](POWER_CHECK.md).

Full tables: [POWER_CHECK.md](POWER_CHECK.md), rerun after the audit with the v3 pool and stand-in rules.

## What this design cannot tell us

- The effect on homes built, rather than permitted.
- Effects on 5–6 unit buildings: M1 stops at 4, and Census cannot separate 5–6 from larger buildings.
- Small effects: each test can only detect effects at least as large as the power check shows.
- SB 9's effect apart from California's other 2022–2025 housing laws.
- A demand shock that starts in the same year as a law.
- How much of any change in M1 comes from ADUs rather than middle housing, outside California.
- Effects in states whose laws are newer than the data (Washington, Montana, Arizona). Washington's state law is added as a test when OFM's 2027–2028 data arrive.
- Whether a state's result transfers to Wisconsin. That is a separate plan, started in parallel, using no results from these tests.

## Changes in v2 (accepted by Ryan, 2026-11-09)

| # | Weak spot | Change |
| --- | --- | --- |
| 1 | Two treated states make a state-clustered bootstrap look too precise | Main inference is the rank among fake law-state pairs; the bootstrap is second |
| 2 | California passed many housing laws at once | Result labelled "California's 2022 package" |
| 3 | M1 is mostly ordinary houses | M2 share (2–4 unit homes ÷ M1) added as a fixed side line |
| 4 | City tests can only see big effects | "Not detectable" never means zero; detection bar shown beside every result |
| 5 | Many tests and measures | One primary result named: Test 1, M1 |
| 6 | Comparison places may have reformed, or caught spillover | Reform-list screening before lock; counties bordering Oregon or California left out |
| 7 | Laws differ in strength | Law strength coded before lock |
| 8 | No bridge to Wisconsin | Wisconsin plan started in parallel, using no results |
| 9 | Spokane fill-ins; few fake years; rough held-out range | Spokane checked against OFM totals; limits stated |
| — | Open decisions from v1 | Licences settled (see Data rules); Test 2 is a side check; Washington state law added when its data arrive |

## Disclosure for Test 1 (audit fix 4)

Test 1 is less exposed than Test 3, but not unexposed. Seen before M1 was chosen:
- Portland and Sacramento Census counts by building size, 2012–2025 (two places among many).
- California's statewide SB 9-flagged totals, 2022–2025.
- State-level rates of homes in 2–4 unit buildings, before and after, for Oregon, California, Maine and Vermont, published in [STATE_ADOPTION_INVENTORY.md](../scenarios/STATE_ADOPTION_INVENTORY.md) on 2026-10-26, before this workstream. These were read during step 1, and the Oregon 2019–2021 figure is quoted in the power check. That exposure is on M2 at state level, not on M1.

## Changes in v3 (answers to the audit of v2, 2026-11-09)

| Audit item | Change |
| --- | --- |
| Must 1: Oregon and California's pool was Alaska and Hawaii only | Pool is the same Census region, minus law states and border counties; fake states use the same rule; design and code both match at ½–2× per place; power check rerun |
| Must 2: ADUs inside M1 | State ADU laws added as an open backdoor; California without-ADU sensitivity fixed (read as a bound); Oregon's lack of a series stated |
| Must 3: stand-ins from law states | Stand-ins never from Oregon, California, Washington, Maine, Vermont or Montana; Portland labelled as overlapping HB 2001; power check rerun |
| Should 4: disclosure | Test 3 labelled supporting only; Test 1 exposure stated, including the state-level 2–4 unit rates from October |
| Should 5: Test 2 columns | Census filled-in columns; reported-only as sensitivity |
| Should 6: Oregon 2019 | Sensitivity with before window 2015–2018 |
| Should 7: fake years | Exact fake windows set for every place |
| Should 8: wording | Question reworded; pair statistic defined as the unweighted mean; 5th/95th labelled a convention |

## Changes in v4 (Ryan, 2026-11-09)

| Change | Why |
| --- | --- |
| Primary measure M2 (homes in 2–4 unit buildings), not M1 | Narrowest range in every design (bake-off, 2012–2018 data only); M1 never got under a useful width |
| Four states in the primary test | Narrows the range from about ±0.50 to about ±0.28; Oregon and California alone become a sensitivity |
| Goal: a range that excludes 0, or an honest "we do not know" | Ryan: a noisy test that can only say "no detectable change" is useless |
| Every result reports the range the data allow | So "we do not know" still says how big an effect is ruled out |
| No decision threshold | Ryan declined the 1-per-1,000 threshold |

**Disclosure (important for the audit):** in step 1 (2026-11-06) the lead researcher read the October inventory's raw before/after state rates of homes in 2–4 unit buildings for exactly these four states (Oregon 0.59 → 0.59; California 0.50 → 0.52; Maine 0.56 → 0.70; Vermont 0.62 → 0.69; per 1,000 one-unit detached homes per year, different windows, no comparison places), and quoted Oregon's to Ryan. The audit of v2 accepted this exposure because it was on M2 while M1 led. v4 makes M2 primary. The reason for the switch is the bake-off, run on 2012–2018 data only, in which M2 had the narrowest range in every design. The audit should judge whether this exposure is acceptable.

## Changes in v5 (audit of v4, 2026-11-09)

| Audit item | Change |
| --- | --- |
| Must 1: the disclosure touches the primary result | Headline requirements (a)–(d): disclosure in every Test 1 headline; Oregon + California shown beside the four-state result; comparison places' own change shown; open backdoors listed |
| Must 2: Ryan's screen of comparison states | Statute-only rule fixed; 9 states and 13 places dropped, with sources; same rule for fake states; investment programs marked as an open backdoor; bake-off and power rerun on the screened pool |
| Small: "2 treated states" | Now "4 treated states" |
| Small: headline wording | "A rise relative to comparison places" |
| Added | Unmatched-place rule (largest California cities) |
