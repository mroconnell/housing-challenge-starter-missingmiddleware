# Middle housing: Wisconsin plan (LOCKED 2026-11-10)

Drafted 2026-11-10 at Ryan's request. **Not locked; no tool change.** It turns the locked tests' results into proposed tool lines for Wisconsin. The audit reviews it before lock, and Ryan decides any tool change. The choices below were made after Test 1 and some Wisconsin side figures were already computed (the 5–6 unit estimate, the side views, and the yearly table). Each is labelled with what it rests on.

**Honest limit:** unlike the test plan, this plan is written after the test results are known (Test 1: "we do not know", +0.23 per 1,000 single-family homes per year, 90% range −0.07 to +0.65). Its choices are therefore listed with their reasons, and every alternative is shown in "How sure". No choice may be swapped later for one that moves the lines, without a post hoc label.

**Lock record.** Locked 2026-11-10 on Ryan's go ("lock it in", cmsg_01C3Z6G8h32D4UwCcjcGMM7q2pLiUSVd4wYaKVrMTLyRXJ). The audit cleared v3 to lock (timing labels included).

**Decided by Ryan after the audit's v3 clearance; sent to the audit for confirmation:**
- unzoned-town bar dropped;
- flat timing shown as a toggle;
- 5–6 unit estimate kept from the 2–4 route, with the 5+ cross-check.

**Defaults taken at lock, where Ryan had not yet answered.** These are the recommended options, and Ryan may change any of them, labelled post hoc:
1. **Extra line "with add-ons":** core + townhouses and split-lot homes (×2.25, the middle of Test 6's 1.5–3) + 5–6 unit buildings. Central about +3,900 homes over 2027–2031; the range is computed in the build by the same rules.
2. **Extra line "stronger reform":** the core scaled by homes allowed per lot (handbook up to 6, against each tested law's by-right maximum, from the law-strength coding, statutes only). Labelled as a possibility. Not computed until the coding is done.
3. **Beside the core:** 1–6 unit homes (measured 1–4 plus the 5–6 estimate, labelled partly estimated). All homes stays beside the core at the same size, as the locked test plan requires, labelled "too noisy to decide".

## What the tool would show

- **Reform:** the handbook scenario. 2–6 homes allowed on every parcel now limited to one house, up to 3 stories, statewide.
- **Outcome:** extra homes permitted, all building sizes, 2027–2031. This matches TOD and parking, on the shared all-housing baseline (v4: central 124,000).
- **Lines:** lower, central and upper, labelled by meaning, plus the headline "the evidence cannot yet tell whether this raises building" while the main test reads "we do not know".

## Step 1. The rate (from the locked tests)

| Line | Rate: extra homes in 2–4 unit buildings per 1,000 single-family homes per year | Source |
| --- | ---: | --- |
| Lower | −0.07 | Test 1, bottom of the 90% range |
| Central | +0.23 | Test 1 estimate (four states, reported-only Census data) |
| Upper | +0.65 | Test 1, top of the 90% range |

- **Check beside it:** Test 5's held-out miss for a state the method has not seen is about ±0.27. That is close to Test 1's own half-width.
- **No zero floor:** the lower line stays negative, because the evidence allows a fall (project rule: no evidence-free floors).

## Step 2. Which Wisconsin homes it applies to

**All 1,839,569 single-family homes** (ACS 2020–2024, detached plus attached). Ryan, 2026-11-10.
- **The 239 towns with no general zoning are not left out.** Their shoreland is under county zoning, with single-family or two-family limits and farm-district single-family rules (Barron County check: [measurement/ARLAND_UNZONED_CHECK.md](measurement/ARLAND_UNZONED_CHECK.md)).
- **Places whose R-1 already allows a duplex also count as restricted.** Lot-size rules usually keep most lots at one home, and the reform allows at least 2 on every lot. The second unit counts.

## Step 3. Adjustments (each one shown on its own in "How sure")

| # | Adjustment | Proposed for the central line | Range used | Evidence |
| --- | --- | --- | --- | --- |
| A | Townhouses and split-lot homes Census files as one-unit | **Not applied** (central stays in Census terms, like the baseline) | ×1.5 to ×3 in the upper line | Test 6: records with townhouses are 1.5–3.2 × Census 2–4 counts |
| B | 5–6 unit buildings | **Not applied** in the central line | ×1.08 to ×1.36 in the upper line (law states); Wisconsin's own lower bound ×1.015 shown in "How sure" | [FIVE_SIX_UNIT_ESTIMATE.md](FIVE_SIX_UNIT_ESTIMATE.md): 7% to 27% of 2–6 unit homes |
| C | Law strength: the handbook scenario is broader than the four states' laws | **Not applied** (no evidence on how effects scale with strength) | None; stated under "what the model cannot tell" | Law-strength coding records the gap. **It is done after the results were seen**, although the test plan meant it before lock (audit, 2026-11-10). Its rule is fixed below before any coding |
| D | Substitution: middle housing replacing houses or big buildings | **Not applied** (Test 7 shows no clear fall in other building) | All-homes reading from Test 1 shown beside the lines | Test 7: 5+ and one-unit homes, "we do not know" |
| E | Timing: laws take time to bind and build | **Flat** over 2027–2031 (the Test 1 after windows are years 1–3 after binding) | Ramp starting at half in 2027 as a sensitivity | None direct; stated |

- **Why the central adds nothing:**
  - The central line is the measured estimate, in the same Census terms as the baseline.
  - Every adjustment rests on a ratio from other places, so each is shown, not folded in.
- **The upper line:** Test 1's top (+0.65) × A × B, using the middle of each range (×2.25 and ×1.22).
  - The highest and lowest combinations are shown in "How sure".
  - **Alternative:** the upper line uses Test 1's top alone, with A and B shown only in "How sure". Ryan decides.

## Step 4. Arithmetic (all 1,839,569 single-family homes)

| Line | Per year | 2027–2031 |
| --- | ---: | ---: |
| Lower (−0.07) | about −130 | about −640 |
| Central (+0.23) | about +420 | about +2,100 |
| Upper, Test 1 top only (+0.65) | about +1,200 | about +6,000 |
| Upper with A and B mid (+0.65 × 2.25 × 1.22 = 1.78) | about +3,300 | about +16,400 |

Against the 124,000-home baseline, the central is about +1.7%.

## Step 5. Where (map)

- Split the statewide line by each place's single-family homes (step 2), at the same rate everywhere.
- **Alternative:** weight by each place's current 2–4 unit share (the "health" baseline idea, ASSUMPTIONS AQ). That needs its own evidence test, so it is not proposed now.

## Step 6. What the tool must say

- **Headline:** "The evidence cannot yet tell whether allowing 2–6 homes raises building. Our best estimate is about +420 homes a year (range −130 to +1,200)," or the step 2 numbers.
- **Disclosures carried from the tests:**
  - (a) the measure and states were chosen after raw trends were seen;
  - the comparison pools were thin;
  - California's result is a package of laws;
  - Census misses townhouses (×1.5–3);
  - 5–6 unit buildings are outside the count.
- **"What the model cannot tell":**
  - effects of a law broader than any tested;
  - homes built, as opposed to permitted;
  - a demand shock in the same year as a law.

## Law-strength coding rule (fixed before any coding; statutes and rules only)

For Oregon HB 2001, California SB 9, Maine LD 2003 and Vermont Act 47, as in force during each state's Test 1 after window, record from the statute or rule text only:
1. the most homes allowed by right on a lot zoned for one house (by city size or area where it differs);
2. where it applies: city-size thresholds, zones, growth areas, water and sewer conditions;
3. the share of the state's single-family homes in covered places (Census ACS, by the statute's own thresholds);
4. carve-outs: owner occupancy, lot-size minimums, parking, design review, historic districts;
5. whether approval is ministerial.

For each item, compare with the handbook scenario (2–6 homes, 3 stories, every single-family parcel). The coding feeds only the "what the model cannot tell" text and the Wisconsin plan's statement of the gap. It does not change any line unless a new plan, locked first, says how.


## Decisions (Ryan, 2026-11-10)

These replace the proposals in steps 2–6 wherever they differ.

| Item | Decision |
| --- | --- |
| Places | All 1,839,569 single-family homes. The "unzoned towns" coding was a mistake and is dropped; duplex-allowing R-1 counts as restricted |
| Core lines | Driven only by Test 1's comparison model on Census homes in 2–4 unit buildings, the type of reform tested (up to 4 homes per lot): lower −0.07, central +0.23, upper +0.65 per 1,000 single-family homes per year |
| In Wisconsin, 2027–2031 | With the measured slow start: lower about −490; central about +1,600; upper about +4,530 homes (split by today's mix: 92% 2-unit, 8% 3–4 unit) |
| Timing | **Measured slow start** (Ryan, 2026-11-10; cross-scenario rule: every scenario uses its own measured timing). 2027 = −21% of full size: the first year each law bound averaged −0.05 against +0.26 per 1,000 single-family homes per year in the main after-years (Oregon 2022 −0.20, California 2022 −0.30, Vermont 2023 +0.33; Maine's first year is inside its window). Full size from 2028. **Post hoc**; rests on 3 states and 1 year each. Lines: about −490 / +1,600 / +4,530 homes over 2027–2031. Flat timing is a **toggle** in the tool, not a line (Ryan): −640 / +2,100 / +6,000 with the toggle off. **Labels (audit, 2026-11-10):** (1) the share rests on 3 single years, whose noise (about ±0.27 per 1,000 per state, Test 5) is larger than the share itself, so the sign of the 2027 share is not measured; (2) because the share is negative, the lower line's 2027 value sits slightly above 0, which is not an error; (3) this rule binds all scenarios, and ADU, TOD and parking each state a measured basis. |
| Law strength | Unscaled |
| Headline | Audit's accurate wording, accepted by Ryan (2026-11-10): "The evidence can't tell yet. We'll know more when we have a full five years in the other states. Most of the range for 2–4 unit homes is above zero, but it includes a small fall, and there is enough noise that we're not sure it's caused by this reform." |

**Shown right beside the core lines, at the same size (locked reporting rule; audit of v1):**

| Measure | Test 1, four states (log-ratio reading) | Applied to the Wisconsin baseline, 2027–2031 | Reading |
| --- | --- | --- | --- |
| M2, core: 2–4 unit homes | +0.23 per 1,000 per year (−0.07 to +0.65) | about +2,100 (−640 to +6,000) | we do not know |
| M1: 1–4 unit homes | +7% (−18% to +29%) vs comparison places | +5,200 (−12,900 to +21,100), on 72,040 baseline 1–4 unit homes | we do not know |
| M3: all homes | +8% (−14% to +32%) | +10,400 (−17,400 to +39,400), on 124,000 baseline homes | we do not know |

**Why the core uses the rate difference while M1 and M3 use the ratio (audit, lock note 1):**
- The core lines carry Test 1's measured change in homes per 1,000 single-family homes per year straight to Wisconsin's single-family homes. That avoids leaning on Wisconsin's own small, lumpy 2–4 unit baseline (8,546 homes over five years).
- M1 and M3 have large baselines, where the locked ratio reading is the governing one.
- **"How sure" bar:** M2 converted by the ratio method, +32.7% (−21.4% to +91.9%) on the 8,546 baseline 2–4 unit homes, about +2,790 homes (−1,830 to +7,860).

M1 and M3 are converted by the locked ratio reading. The percentage range is applied to the shared baseline's 2027–2031 central for that size. Their rate-difference ranges are not used.

**Extra lines and "How sure" bars only, never in the core range:**
- **5–6 unit buildings:** +390 homes (90% range −150 to +1,400), from a share assumption ([FIVE_SIX_UNIT_ESTIMATE.md](FIVE_SIX_UNIT_ESTIMATE.md)). Kept from the 2–4 route (Ryan, 2026-11-10). Cross-check from the measured 5+ effect × California's 3.0% share of 5+ homes in 5–6 unit projects: about +130 (−410 to +1,160).
- **Townhouses and split-lot homes:** Census files them as one-unit; ×1.5 to ×3 (Test 6). Shown as a bar, plus an optional higher line with its explanation.
- **A stronger reform:** the handbook allows 2–6 homes by right on every lot. A bar labelled as a possibility, with no evidence-based multiplier.
- **A ramp (post hoc, Ryan 2026-11-10):** a bar where years 4–5 climb at the after-law slopes of the market-normalized ratio (Oregon +0.42 and California +0.33 per year; the unit is the change per year in the ratio of the state's 2–4 unit rate index to its comparison places' index, both indexed to 2015–2019 = 1.0; on 4 years each). It is labelled as resting on 4 noisy years, and as possibly part of a trend already under way: the pre-law slopes in the same unit were Oregon +0.13, California +0.25 and Maine +0.10 per year. Recheck when 2026–2027 data arrive.
- **Trend-adjusted view (post hoc, 2026-11-10):** after projecting each state's pre-law trend in the market-normalized ratio forward, the after-law years average below it. Oregon −0.52, California −1.35, Maine −0.19, Vermont −0.14, in the ratio's units. Read this way, the reform years show a small fall, not a rise. It is shown as a "How sure" note: the pre-law trends rest on 7–9 noisy points (California's on a 2021 spike), and the locked fake-reform-year check for M2 passed.
- **Unzoned towns: dropped (Ryan, 2026-11-10).** Their "no zoning" coding was wrong (the Barron County check); every single-family home counts, and they get no bar or map.
- **Measured side views:** one-unit homes +3,400 (−13,600 to +17,900); 5+ unit homes +4,400 (−13,600 to +38,600). Both come from Test 1's four-state log-ratio result (one-unit +5%, −21% to +28%; 5+ +8%, −26% to +74%), measured over each state's locked after window (2023–2025, or 2024–2025 for Maine and Vermont). Each is applied to the baseline's 2027–2031 central for that size (63,494 and 51,960). Both read "we do not know", and both are dominated by ordinary houses or large buildings.
- **Weakest point, stated beside the result:** the West comparison group is thin (85 places reporting every year) and lumpy.

## Decisions for Ryan before lock

1. **Places:** all single-family homes (decided, Ryan 2026-11-10).
2. **Upper line:** Test 1 top with adjustments A and B (proposed), or Test 1 top alone?
3. **Timing:** flat (proposed), or a ramp?
4. **Law strength:** leave it unscaled and stated (proposed)? Any scaling would need new evidence and a new plan.
5. **Headline wording:** keep "cannot yet tell" while Test 1 reads "we do not know"?

## Still to do before lock (no outcomes)

- Law-strength coding for the four states (documents only).
- Bundle and screens per the scenario contract (status stays `in_development` until Ryan accepts a pilot).
