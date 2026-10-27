# Transit-oriented density: Gate 4 packet (working pilot in the tool)

Written 2026-10-27 by the TOD conductor, for Ryan. Status: ready for review. An independent verifier checked every displayed number first (section 5).

## 1. What this gate decides

Is the TOD part of the tool right, clear and usable enough to become a full reform next to ADUs and parking? If you accept it, its status changes from "in development" to "ready", and it appears without preview mode.

## 2. How to look at it

1. Run `bash scripts/run_tool.sh` and open the address it prints. If an old server is still running on port 4173, use `PORT=4180 bash scripts/run_tool.sh` instead.
2. Go to `#/tod/today?preview=1`. Preview mode then stays on for that browser tab.
3. Check that the footer shows run `tod-494eba2693` (updated 2026-10-27: the bundle now also publishes `additions_by_area.json` for the combined view; no displayed number changed).

## 3. Owner review steps

1. **Wisconsin today.** Which stops count, the ladder of definitions from narrowest to widest, and the 313,564 homes near stops.
2. **Statewide comparison.** The baseline near stops (14,464 homes over 2027–2031) plus the three scenarios: little 171, typical 2,509 and strong 17,148 extra homes. The timing note comes first. The reference line is dotted.
3. **Where.**
   - Sort the table, and switch between municipalities, counties, Assembly districts and Senate districts.
   - Find Madison: 501 extra homes in the typical scenario.
   - Read the notes on places with few homes near stops, and on places whose recent Census permit counts look too low (Wauwatosa, South Milwaukee, Greenfield, Cudahy).
4. **How sure.** Sensitivities grouped by what they move, the scale check, and what the model cannot tell you.
5. **Why.** The policy classification, the comparison cases, the Madison test (prediction against measured) and the three studies behind the scenarios.
6. **Pilot examples.**
   - Milwaukee CONNECT 1 and The Hop: 199 extra homes in the typical scenario, 142 of them in Wauwatosa.
   - Madison Rapid Route A.
   - Eau Claire: zero additions, because it has no 15-minute routes. This is the "does it transfer" example.
7. **Brief.** One printable page.
8. **ADU and parking.** Check their screens look unchanged.

**My self-assessment.** I walked each screen on desktop and mobile, using the verifier's screenshots and the fixed build:
- The headline numbers match [GATE3_PACKET.md](GATE3_PACKET.md).
- Each screen opens with what you are looking at, and the chart comes before the table.
- **Weakest screen:** "Where". The extra homes are spread by the per-acre method, so places with vacant or commercial land near stops can gain more than their homes suggest. It is explained on the page, but a reader may still find it odd.
- **Second-weakest:** the yearly path. Typical drops to 166 homes in 2031 because the measured build-up was kept (G3-3 as amended).

## 4. Limitations

- **The map is a simple drawing,** not a street basemap: stops, their ½- and ¼-mile circles, and municipality outlines.
- **No observed history of permits near stops,** so the comparison chart starts in 2027.
- **Milwaukee's corridor pilot combines CONNECT 1 and The Hop,** because the station-area data cannot separate them.
- **Low recent Census permit counts** in Wauwatosa, South Milwaukee, Greenfield and Cudahy probably understate their current-law baseline. This has been flagged to the parking thread, which owns the baseline.
- **Two Gate 3 amendments still await your confirmation:** keeping the measured build-up, and scaling the suburbs' placement by 0.719. The screens already use both. Neither changes the statewide totals.

## 5. Independent verification

The verifier worked in a fresh copy of the repo:
- setup and both test suites passed;
- the bundle rebuilt byte for byte;
- it extracted 3,394 numbers from 31 screen states, on desktop and mobile, and traced each to the reference tables;
- it recomputed 567 values on the Where tables and pilots from scratch.

It found two blockers:
1. **A TOD style leaked onto ADU's Where screen,** removing padding and alignment from its sort buttons.
2. **A pilot column was mislabelled.** It said "acres where the law adds room" but showed all eligible acres.

It also listed wording, rounding and labelling fixes. All are fixed (commit bcb94f7). A new test guards ADU's sort buttons. A rerun of the verifier's own scripts found no wrong values and no console errors.

**Tests:** 507 Python tests and 104 Playwright tests pass. The 4 skipped tests are a preview test that no longer applies now that parking is "ready", and mobile keyboard tests.

## 6. Decisions requested

| # | Decision | Recommendation |
| --- | --- | --- |
| G4-1 | Accept the TOD screens and mark TOD "ready" | Yes, after your walk-through |
| G4-2 | Confirm the two Gate 3 amendments (measured build-up kept; suburbs scaled by 0.719) | Yes |
| G4-3 | Next step | Build the combined TOD-plus-parking view (sum, and the larger of the two near stops, side by side), then the statewide Gate 5 review |
