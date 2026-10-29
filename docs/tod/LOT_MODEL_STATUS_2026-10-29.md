# TOD lot model: status readout, 2026-10-29 (08:20 Mac time)

Written by the TOD thread at the owner's request, for the cloud audit session. The decision log is [LOT_MODEL_PLAN.md](LOT_MODEL_PLAN.md) section 9, items 1–35. The audits are [LOT_MODEL_AUDIT_2026-10-29.md](LOT_MODEL_AUDIT_2026-10-29.md) and [../audit/INDEPENDENT_AUDIT_2026-10-29.md](../audit/INDEPENDENT_AUDIT_2026-10-29.md). **No scenario number in the tool has changed** (TOD 171 / 2,509 / 17,148).

## 1. Run status

One full rebuild (chain started 06:56) with every fix through item 35:

| Step | Status |
| --- | --- |
| Rebuild 9 case cities (`collect`, `add_bellevue`) | Done 07:06 |
| Tract traits, values, all 91 variables, census homes, ½-mile rule | Done 07:13 |
| Spread assembled New York sites (item 33) | Done: 2,712 homes after and 552 before spread to other day-one lots; 360 lots marked "part of an assembled site" |
| Land values | Done 07:17 |
| Wisconsin lot table (built in parallel) | Done |
| Causal forest, 4 versions (main; seed 7; largest project out; check with "rezoned later") | Running: 6 of 9 cities each; the 3 holdouts (Chicago, Madison, Bellevue) running |
| Wisconsin estimate | **Paused by the owner** until he says go; not started |
| Rescore (item 23–27 scoring, item 32.6 dedupe) | Runs automatically when the forests finish |

## 2. What went into this rebuild (items 31–35)

- **31, day-one groups:** a lot's group comes from the reform's map on the day it passed. Inside and upzoned = TOD lot; nearby outside = comparison lot; later rezoning is a trait, not an exclusion. Items 29–30 withdrawn.
- **32, cloud audit fixes:**
  1. New York hotel jobs dropped, using MapPLUTO 18v1 building class H with no residential units: 455 jobs, 40,363 "units". Lot model only (`case_nyc.EXCLUDE_HOTELS`).
  2. Chicago staged permits merged: same point, within about 18 months, unit counts within 10%; the larger count is kept (`case_chicago.STAGED_RELAXED`).
  3. "Rezoned later" is left out of the fitted model; one check run keeps it (`--with-rezoned-later`).
  4. The unchanged forest learns from eligible comparison lots only, the same lots the yardstick uses.
  5. Traits only some cities have are dropped: homes on the lot from city records, soft-site ratio, building age, and their missing flags.
  6. Stacked lots at one point within one reform become one row; the weight is 1 ÷ the number of reforms holding the point (`dedupe_lots`).
  7. Madison is reported both ways.
- **33, assembly (owner chose option B):** a New York lot's homes are shared over the day-one lots of the same reform that sit inside the tax lot holding the building in the first MapPLUTO release after the permit year. There is no merging of lots and no hindsight in the lot set.
- **34, zoning limits (cloud section 2c):**
  1. Madison is not a floor-area-ratio city (its levels are stories × 0.70).
  2. Wisconsin levels are not read as floor area ratio.
  3. "Gain known" only where the level before is above 0 and the gain is finite; floor area after is blank where unlimited.
  4. Seattle level flags.
  5. A level-source flag per city in each flag file.
- **35, units (cloud section 2d):**
  1. Homes built nearby before become per before year.
  2. Wisconsin homes on the lot were already 2020 block homes shared by area.
  3. Milwaukee year-built (completion, not permit) is noted; the lag is to be measured on Madison.

## 3. Results so far: training cities, all 4 versions

Extra homes over 5 years. "Actual" and "plain average" here come from the run's own (pooled) scoring. The final rescore uses per-reform scoring and will shift them slightly.

| City | Actual | Plain average | Main | Seed 7 | Largest project out (its actual) | With "rezoned later" |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| New York | 8,903 | 2,235 | 6,585 | 6,096 | 5,709 (9,255) | 6,612 |
| Philadelphia | 3,310 | 1,414 | 2,604 | 2,342 | 2,833 (2,454) | 2,649 |
| Saint Paul | 404 | 1,154 | 342 | 486 | 71 (158) | 498 |
| Charlotte | 1,686 | 5,513 | 3,222 | 3,577 | 1,150 (1,686) | 3,243 |
| Seattle | 323 | 243 | −283 | −164 | −172 (−34) | −198 |
| Los Angeles | −195 | 3,755 | 3,144 | 3,135 | 2,000 (−570) | 3,166 |

- The forest is closer than the plain average in 5 of 6 training cities in the main version. Seattle is the miss.
- Los Angeles is far off for both the forest and the plain average.
- Holdouts (Chicago, Madison, Bellevue) are pending; they decide the pass under the old and new rules.

## 4. Open risks and known gaps

1. **Scale:** Wisconsin's law upzones about 168,000 lots; all training cases together about 21,000. The owner may narrow the modelled law (fewer stops, smaller radius) once the model is trusted.
2. **Madison's actual** rests on 187 comparison acres that went from 421 homes to 0. Against in-overlay lots whose density did not rise, the effect is about zero. This matters because Madison is a holdout.
3. **Thin comparison land** (Greenpoint–Williamsburg, Warner Center, Bellevue and some Philadelphia bills) is scored on the upzoned change with no trend. A federal permit-survey trend is suggested, not done.
4. **Not done yet:**
   - sites rebuilt from later lot maps outside New York;
   - Philadelphia townhouse permits spread over subdivided lots;
   - Chicago downtown planned developments (left out as not eligible);
   - a map spot-check of random lots;
   - lot-model tests.
5. **Saint Paul** has one before year; the yes/no "built before" trait remains weaker there.
6. **Milwaukee building-before** uses year built from the property file (completion), while elsewhere it uses permits.
7. **Many versions have been tried** (runs A to E, then items 12–35). Any pass is stated with that caveat.
8. **Queued, not approved yet:** a true causal forest (EconML `CausalForestDML`, MIT licence) as an extra pre-registered method, and Milwaukee and Madison no-reform rows.

## 5. Owner decisions recorded today

- Groups are set by the day-one map; nothing is dropped for later rezoning (item 31).
- Option B for assembled sites (item 33).
- Zoning-limit and units fixes (items 34–35).
- Lot-model runs stay on the Mac. If cloud runs are ever needed, only a de-identified fit table, shared privately and never committed.
- Wisconsin estimate paused until the owner says go.
