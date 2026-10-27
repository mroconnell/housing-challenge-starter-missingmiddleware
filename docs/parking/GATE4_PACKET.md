# Parking scenario: Gate 4 packet (working pilot in the tool)

Written 2026-10-27 by the parking conductor, for Ryan. Status: ready for review. It builds on Gates 1–3 (AQ-046 and AQ-048; Gate 3 approved 2026-10-27).

## 1. What this gate decides, and the answer

Gate 4 decides whether the parking screens show the approved numbers correctly and clearly enough to mark the reform "ready" in the tool.

The parking reform has the same seven screens as ADUs, reading from its own bundle (`ui/public/scenarios/parking/runs/`):

1. **Wisconsin today:**
   - 25,569 homes permitted in 2025;
   - 122,619 expected under current law over 2027–2031;
   - 9 places that already have no parking minimums for housing.
2. **Statewide comparison:** "No measurable change" (0 added) and "High end of the evidence" (29,663 added, +24%), with a chart and a table by year.
3. **Where:** the added homes by county, city, village or town, and Assembly and Senate district, with a place search.
4. **How sure:**
   - cases grouped by what they change;
   - stability checks;
   - the effect by year since repeal;
   - what rests on data and what on judgment.
5. **Why:**
   - the 30 repeal places compared (24 in the average);
   - the parking studies;
   - North Carolina's law.
6. **Pilot examples:**
   - Milwaukee (partial reforms; apartment estimate);
   - West Allis (already repealed, so the law adds 0);
   - Eau Claire (mid-size, partial reform).
7. **Brief:** one card for a legislator.

The upper total is now 29,663, not 29,662. The exact value is 29,662.5, and the bundle now rounds halves up everywhere, so every screen shows the same figure.

## 2. How to look at it

1. In the repo folder, run `bash scripts/run_tool.sh`.
2. Open http://127.0.0.1:4173/#/parking/?preview=1.
   - The "Preview: not yet reviewed" flag shows until you accept this gate.
   - `?preview=0` turns preview off.
   - Check that the run id in the status strip begins `parking-`.
3. Walk each tab. On a phone-width window, check that the chart still reads.

## 3. Owner review steps

1. On **Statewide comparison**, check that the two case names and their one-line explanations say what you want a legislator to read.
2. On **Where**, choose "City, village or town" and search for a place you know. West Allis should show 0 homes it applies to and 0 added.
3. On **How sure**, read "Do different kinds of places respond differently?" and "What rests on data and what on judgment".
4. On **Why**, open "All 30 places" and skim the table.
5. Read the **Brief**.
6. Decide G4-1 and G4-2.

**Self-assessment.** I walked every screen at desktop and phone width. An independent check traced every displayed number to the reference files: all 72 counties, all 99 Assembly and 33 Senate districts, the top 50 places, every sensitivity and every pilot. It found 4 errors, all fixed:
- the 2025 note wrongly said Milwaukee apartments were added (they are not available for 2025);
- the upper total differed by 1 between screens (rounding);
- the with-law total did not equal its rounded parts;
- the "2023–2025 average" note did not mention that Milwaukee's apartments use 2023–2024.

It also listed wording fixes, all made: one name for each case throughout; no "benchmark" or "stylized" on screen; plainer How sure text; a "Not yet checked" tag for studies read only from summaries; notes for estimated values; and year labels thinned on narrow screens. Tests: the Python suite and the full Playwright suite pass, including a new parking test that reads every checked number from the bundle.

## 4. Decisions requested

| # | Decision | Recommendation |
| --- | --- | --- |
| G4-1 | Accept the parking screens and mark the reform "ready" | Yes, after your walk-through |
| G4-2 | Pilot places | Keep Milwaukee, West Allis and Eau Claire. Swap Eau Claire for another mid-size place only if you want one with no reform at all |

## 5. Limitations

- **Where:** the Where screen spreads the high case by homes. It cannot show where minimums actually bind.
- **Milwaukee:** its 2025 apartments are missing, so the 2025 "today" figure undercounts.
- **Rounding:** municipality figures are rounded for display, so rows can differ by 1 from sums.
- **Combined view:** the combined TOD + parking view is not built yet. It waits for TOD's Gate 4 and the contract text (G3-3).
