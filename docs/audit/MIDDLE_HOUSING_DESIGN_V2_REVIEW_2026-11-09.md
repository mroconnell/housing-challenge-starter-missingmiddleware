# Middle housing test design v2 review (main 1b0f9af5; TEST_DESIGN_DRAFT.md v2; AUDIT_REQUEST_2026-11-09.md)
2026-11-09 ~19:15 UTC. Ryan's ask 19:05:56 UTC (cmsg_01C3Z6G8h32D4UwCcjcGMM7qND5gHHdHPnW4KL4TFUKGtq).
Order: no test run. Power check read 2012-2018 only (script skips later files; checked lines 37-44, 109-146). OK.

Verdict: NOT READY TO LOCK. 3 must-fixes, 5 should-fixes. The structure (one primary result, M3 always beside M1, fake-state ranking, symmetric rules, "not detectable is not zero") is sound.

## Must fix
1. Test 1 comparison pool for Oregon and California is Alaska and Hawaii only. Comparison places come from the same Census division. Pacific = AK, CA, HI, OR, WA, and WA is left out. Border-county exclusion removes nothing from AK/HI. Large California places (1/2-2x population) have almost no match there. Fix: state the pool now (e.g. Pacific + Mountain, minus AZ, MT, WA, minus border counties), and give fake states the same rule (their own division plus one neighbour), so the ranking compares like with like. Also make the design and the power-check code use the same matching (design: 1/2-2x per place; code: population bands weighted by the fake state's homes).
2. ADUs sit inside M1. Census files a new detached ADU as a 1-unit building (MEASUREMENT_CHECK_RESULTS line 21). Both treated states had ADU laws whose surge spans the windows (California 2017 and 2020 packages; Oregon's 2018 ADU rule). Most comparison states did not. So M1 can move with ADUs, not middle housing. Fix: add "state ADU laws" as a backdoor, marked open; pre-set a sensitivity for California that removes APR detached-ADU counts by year from M1 (Oregon has no such series; say so); and read M2 beside M1 with this in mind.
3. Test 3 stand-ins can be law-state places. The stand-in pool (code line 144) excludes candidate cities only. Portland's first scope is its own state, where HB 2001 binds every city over 10,000. Spokane's after window reaches Washington's HB 1110 (2025). Fix: stand-ins exclude places in any state whose law binds during that city's after window. Label Portland as overlapping the state law.

## Should fix
4. Disclosure (Q1). Census units by building size 2012-2025 for all 5 Test 3 cities were seen on screen on 2026-11-06, before M1 was chosen on 2026-11-09. The power-check reason is sound, and M1, M2 and M3 are all published, so the risk is only in which leads. Label Test 3 "post-reform counts by building size were seen before the measure was chosen; read as supporting only". Test 1 is less exposed (Portland, Sacramento and California's SB 9-flagged totals only); say so in one line.
5. Test 2 data rule. With reported-only data the 9,000-10,999 band has 1 covered and 3 left-out cities (POWER_CHECK). The design's data rule (reported only) makes Test 2 near-empty. State now which columns Test 2 uses, and keep it a side check. The shared cutoff with ORS 197A.100 is already a stated limit; keeping it is fine at low cost.
6. Windows (Q4). Oregon's before window includes 2019 (law signed 2019-08-08). Waiting for the law could lower 2019 permits and push the result up; pre-set a sensitivity with 2015-2018. California's 2023 start is fair; 2022 shown separately is good.
7. Test 4 windows. "Reform moved 3 years earlier, using only years before the real reform" needs exact fake before/after years per state and city, set now. Oregon: fake law 2016 leaves after years 2017-2019 only if 2019 counts as before the law; state it.
8. Wording (Q6). The question says "how many more homes get permitted". Say "how does the number of homes permitted change". Also say the Test 1 pair statistic is the unweighted mean of the two states' log ratios (as in the power check), and label the 5th/95th cut-offs as a convention.

## Answers in brief
- Q2: fake-pair ranking is the right main inference with 2 treated states, once fix 1 is in. California is a very large state, so its own noise is smaller than a typical fake state's; this makes the test cautious, not over-confident.
- Q3: keep Test 2 as a side check (fix 5).
- Q5: M2 share is a fair guard against house-building swings, but ADUs (fix 2) lower the share too. One-unit homes in Test 7 cover the rest.
- Q6: rules are symmetric. No expected result found apart from the wording in 8.
- Q7: 2012-2018 is the post-crash recovery; it likely overstates noise, so the detection bars are on the cautious side. The 2023-2025 after years include the rate shock, which may add noise too. Keep as is, with that caveat.

## v3 review (52ec2c34, 19:12:03 UTC), no test run
All 8 items answered. Checked:
- Must 1: pool is the Census region minus law states, candidates and border counties; fake states use own region, other untested states; code (test1_state_stats) now matches each place at 1/2-2x and weights by homes. Matches the design.
- Must 2: ADU backdoor marked open; California without-ADU sensitivity removes all APR ADUs (over-removes), read as a bound. Fair.
- Must 3: LAW_STATES_2025 = CA, OR, WA, ME, VT, MT excluded from stand-ins in code; Portland labelled.
- Shoulds 4-8: in. Extra disclosure (state-level 2-4 unit rates for OR, CA, ME, VT from STATE_ADOPTION_INVENTORY, 2026-10-26) is stated; it touches M2, which is second; M1 was chosen on the power check. Acceptable as disclosed.
Verdict: LOCK OK, with 2 wording fixes that can go in the lock commit:
a. Backdoor table, "Interest rates, costs, COVID": says "same division"; now "same region".
b. Data rules: add the Test 2 exception (filled-in columns main, reported-only sensitivity), as Spokane's is.

## v4 review (788525f + 8f5d03c, 19:19 UTC), no test run
Ryan's asks: 19:18:46 UTC (goal: range excludes 0 or "we do not know"), 19:19:44 UTC (screen comparison states for other upzoning, TOD, investment; named MA, NY, PA, UT, CO).
Bake-off (040ecf0) read 2012-2018 only. Goal and reading rule are symmetric; no threshold; range always reported. OK.

Verdict: NOT READY TO LOCK. 2 must-fixes, 2 small fixes.

### Must 1. Disclosure now touches the primary result
- The raw state M2 rates seen on 2026-11-06 are for exactly the 4 primary states. v4 both promotes M2 and adds Maine and Vermont, the two states whose seen raw rates rose (ME 0.56 -> 0.70, VT 0.62 -> 0.69; OR 0.59 -> 0.59, CA 0.50 -> 0.52).
- The bake-off reason (narrowest range, pre-law data only) is sound, and the seen numbers have no comparison side, which decides the test. So the exposure is limited, but it cannot be undone.
- Required: (a) every Test 1 headline says the measure and state set were chosen after raw treated-state M2 trends were seen; (b) the Oregon + California result (the v3 primary set) is shown at the same size beside the 4-state result, and if they differ under the reading rule the headline says so; (c) report the comparison side's own before/after change beside each result, so readers see how much comes from it.

### Must 2. Comparison states are screened only at place level
- v4 screens places against local reform lists. It does not screen state laws in comparison states. Several bind inside the after windows (2023-2025 West; 2024-2025 Northeast):
  - Massachusetts: MBTA Communities law (2021; zoning deadlines 2023-2025) requires multifamily zoning by right near transit.
  - Colorado: HB24-1313 transit-oriented communities (2024).
  - Utah: HB 462 station-area plans (2022).
  - Rhode Island: 2023-2024 housing package; Connecticut: 2021 PA 21-29. New Hampshire: check 2024-2025 laws.
  - New York City: City of Yes (Dec 2024) is local; NYC is unlikely to match Maine or Vermont places at 1/2-2x, but say so.
  - Pennsylvania: no statewide law found; keep, subject to the place screen.
- Required: a fixed rule, set now from statutes only: a comparison state is left out if a statewide law that legalises or mandates zoning for 2+ unit homes (middle housing, TOD, multifamily by right) takes effect before the end of its after window. Apply the same rule to fake states, so the spread stays like for like. List each state's call and source before lock. Large state investment programs: list as an open backdoor (not screenable cleanly).
- Rerun the bake-off width with the screened pool (pre-law data only) and report the new range width; Northeast may get thin.

### Small fixes
- "With only 2 treated states" in the second-inference line: now 4.
- Headline wording: "a rise relative to comparison places", with the open backdoors (California package, ADU laws for M1, same-year shocks) stated beside it, since "causal" holds only if they are closed.

## v5 review (2e64722 + bf1df9e, 19:30 UTC), no test run
- Must 1: headline items (a)-(d) in (design lines 54-58). OK.
- Must 2: statute-only rule fixed, applied to fake states (34 remain), sources in measurement/COMPARISON_STATE_REFORMS.md, investment marked open. Spot-checked NY, NJ, PA, NV, ID, AK, WY, NM rows: calls follow the rule. NJ's 2024 fair-share law is noted as mostly 2026+; fine as noted. Bake-off rerun on screened pool: M2 four-state bar 0.41 (range about +/-0.27). OK.
Verdict: LOCK OK, with 2 items in the lock commit:
1. Unmatched-place rule (new in v5) drops the largest California cities, which changes what California's result describes. Pre-set one sensitivity now: unmatched treated places get comparison places from the screened national pool at 1/2-2x (same ladder as Test 3: region, then nation). Report it beside the main result with the unmatched share.
2. Buffalo: the relay lists it as dropped, but COMPARISON_STATE_REFORMS line 85 says its 2017 Green Code is constant through both windows (so kept). Make the design and the sources file say the same thing.
