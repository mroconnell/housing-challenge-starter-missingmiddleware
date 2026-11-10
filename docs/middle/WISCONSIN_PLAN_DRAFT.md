# Middle housing: Wisconsin plan (draft v1, for audit; not locked)

Drafted 2026-11-10 at Ryan's request. **Not locked; no tool change.** It turns the locked tests' results into proposed tool lines for Wisconsin. The audit reviews it before lock, and Ryan decides any tool change. The choices below were made after Test 1 and some Wisconsin side figures were already computed (the 5–6 unit estimate, the side views, and the yearly table). Each is labelled with what it rests on.

**Honest limit:** unlike the test plan, this plan is written after the test results are known (Test 1: "we do not know", +0.23 per 1,000 single-family homes per year, 90% range −0.07 to +0.65). Its choices are therefore listed with their reasons, and every alternative is shown in "How sure". No choice may be swapped later for one that moves the lines, without a post hoc label.

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
| Places | All 1,839,569 single-family homes. "Unzoned" towns and duplex-allowing R-1 count as restricted |
| Core lines | Driven only by Test 1's comparison model on Census homes in 2–4 unit buildings, the type of reform tested (up to 4 homes per lot): lower −0.07, central +0.23, upper +0.65 per 1,000 single-family homes per year |
| In Wisconsin, 2027–2031 | Lower about −640; central about +2,100; upper about +6,000 homes (split by today's mix: 92% 2-unit, 8% 3–4 unit) |
| Timing | Flat across 2027–2031 (**post hoc**: rests on yearly data read after the results). Year-by-year data show no climb in the law states' own rates; the Oregon and California gap trend comes from comparison places falling (`reference/middle_m2_yearly_by_state.csv`) |
| Law strength | Unscaled |
| Headline | Ryan's wording, with the audit's accuracy note pending his call: "The evidence can't tell yet. We'll know more when we have a full five years in the other states. Most of the range for 2–4 unit homes is above zero, but it includes a small fall, and there is enough noise that we're not sure it's caused by this reform." |

**Shown right beside the core lines, at the same size (locked reporting rule; audit of v1):**

| Measure | Test 1, four states (log-ratio reading) | Applied to the Wisconsin baseline, 2027–2031 | Reading |
| --- | --- | --- | --- |
| M2, core: 2–4 unit homes | +0.23 per 1,000 per year (−0.07 to +0.65) | about +2,100 (−640 to +6,000) | we do not know |
| M1: 1–4 unit homes | +7% (−18% to +29%) vs comparison places | +5,200 (−12,900 to +21,100), on 72,040 baseline 1–4 unit homes | we do not know |
| M3: all homes | +8% (−14% to +32%) | +10,400 (−17,400 to +39,400), on 124,000 baseline homes | we do not know |

M1 and M3 are converted by the locked ratio reading. The percentage range is applied to the shared baseline's 2027–2031 central for that size. Their rate-difference ranges are not used.

**Extra lines and "How sure" bars only, never in the core range:**
- **5–6 unit buildings:** +390 homes (90% range −150 to +1,400), from a share assumption ([FIVE_SIX_UNIT_ESTIMATE.md](FIVE_SIX_UNIT_ESTIMATE.md)).
- **Townhouses and split-lot homes:** Census files them as one-unit; ×1.5 to ×3 (Test 6). Shown as a bar, plus an optional higher line with its explanation.
- **A stronger reform:** the handbook allows 2–6 homes by right on every lot. A bar labelled as a possibility, with no evidence-based multiplier.
- **A ramp:** years 4–5 climbing as in California's 2022–2025 gap. A bar.
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
