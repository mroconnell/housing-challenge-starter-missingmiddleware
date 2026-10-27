"""Per-jurisdiction table for the California AB 2097 test, group P (parking near transit alone).

For the parking scenario's pre-registered trait test (docs/parking/TRAITS_PLAN.md). One row per jurisdiction in group P
with near-transit permits in both periods: homes near transit, near and ring permit rates before (2018-2022) and after
(2023-2025), and the jurisdiction's own difference-in-differences, all units, per 1,000 existing homes (2020 census) per
year. No traits are joined here (the parking thread runs that test).

Run after scripts/run_ab2097_test.py (it reuses that script's cached cells and permits).
Output: reference/tod_ab2097_by_jurisdiction.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import run_ab2097_test as run  # noqa: E402
from missing_middleware.tod import ab2097 as ab  # noqa: E402


def main() -> None:
    cells, permits, _ = run.build()
    c, p = run.spec_tables(cells, permits, "zone")
    reporters = ab.full_reporters(p)
    g = ab.define_groups(c, reporters)["P"]
    years = list(ab.YEARS)
    bi = [years.index(y) for y in ab.BEFORE]
    ai = [years.index(y) for y in ab.AFTER]
    arr = ab._arrays(g, c, p, "all_units", "homes", years)
    (tu, td), (cu, cd) = arr["t"], arr["c"]
    rows = []
    for k, j in enumerate(g.juris):
        if td[k] <= 0 or cd[k] <= 0:
            continue
        rate = lambda m, d, idx: 1000 * m[k, idx].sum() / d / len(idx)  # noqa: E731
        nb, na = rate(tu, td[k], bi), rate(tu, td[k], ai)
        cb, ca = rate(cu, cd[k], bi), rate(cu, cd[k], ai)
        both = tu[k, bi].sum() > 0 and tu[k, ai].sum() > 0
        rows.append({"jurisdiction": j, "homes_near_transit_2020": round(float(td[k]), 1), "homes_ring_2020": round(float(cd[k]), 1),
                     "near_rate_before": round(nb, 4), "near_rate_after": round(na, 4),
                     "ring_rate_before": round(cb, 4), "ring_rate_after": round(ca, 4),
                     "did_per_1000_homes_per_year": round((na - nb) - (ca - cb), 4),
                     "near_permits_both_periods": both})
    df = pd.DataFrame(rows).sort_values("jurisdiction")
    out = ROOT / "reference" / "tod_ab2097_by_jurisdiction.csv"
    df.to_csv(out, index=False)
    print(f"{len(df)} jurisdictions in group P; {int(df.near_permits_both_periods.sum())} with near-transit permits in both periods -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
