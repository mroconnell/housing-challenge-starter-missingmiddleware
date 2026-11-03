# Parking work session results (natural experiments, denominators, grid)

Plans: `docs/parking/CAUSAL_FRAMEWORK_PLAN.md`, sections "Natural experiments N1–N4" and "Work session" (locked 2026-11-03 before any count). **Running test count: 32** (27 after N1–N4; the grid, S1, B1, the combination and the backtest make 32). Nothing in the tool changes without Ryan's OK.

## N2, Minneapolis step 2 (first stage)

- **Contrast:** outside the 2015 areas minus inside, May 2021 on vs 2016–May 2021, in car spaces per home.
- **Result:** +0.03 (90% −0.16 to +0.29; 97.5% −0.24 to +0.36). MDE 0.22.
- **Cells:**
  - outside 0.68 → 0.61 (72 → 30 projects);
  - inside 0.71 → 0.61 (104 → 54 projects).
- **Reading:** not supported. The prediction was negative.
- **Power:** an MDE of 0.22 is about the whole citywide drop after 2015 (0.24, F1). N2 cannot rule out an effect of the size seen elsewhere.
- **Partial treatment:** the inside group was only partly treated before 2021. The 2015 rule removed minimums for 3–50 home projects and halved them for 51+, and 2021 removed the rest. That shrinks the expected gap.
- **Balance:** not feasible. The cells are 33 / 8 / 20 / 8 projects, below the 20-per-side rule, so balance is not used.
