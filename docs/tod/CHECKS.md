# Standing checks for every TOD run

Adopted 2026-10-28 by the owner, after the stop list held rail stops only and coded Madison's upzoned lots about 96 km from transit. The same checks were passed to the parking and ADU threads.

**Rule: checks flag, they never stop a run.** Flags are printed at the top of the run's output and saved beside its results.

## 1. Flag check (seconds, before any fit)

Code: `missing_middleware/tod/sanity.py` (tests in `tests/test_tod_sanity.py`). The lot model calls it for every fit stage and writes `reference/tod_lot_model_flags_<stage>.csv`.

- **Units:** each input column has a written unit and a plausible range. Values outside it are flagged. A floor area ratio above 30 is flagged as "likely another unit" (Charlotte's feet of height).
- **Policy definition:** upzoned land farther from a qualifying stop than the policy allows is flagged (½ mile, the Wisconsin benchmark's rail and rapid rung).
- **Out of range:** a city where more than 25% of lots sit outside the other cities' 1st to 99th percentile on a trait is flagged. A model cannot learn about values it has not seen.

## 2. Units written with every column

New columns get their unit in `sanity.UNITS` (or the results file's own unit column) when they are created. Shorthand is explained the first time it appears in anything the owner reads.

## 3. "Ask why" on the worst miss

After every model run or measurement, take the city or case with the largest miss (or most extreme value), and trace which inputs drove it. Write one line: the cause, and whether it is a coding error, a known feature, or a new question for the owner.

## 4. Two-source checks (once per new data source)

- Our upzoned acres against the plan's published acres.
- Permits against census home counts for the same place and years.
- A map of a few random lots per city against the policy's stops and boundary (kept local; no lot ids committed).
- The same checks on the Wisconsin inputs the tool uses.
