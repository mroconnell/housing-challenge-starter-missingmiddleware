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
