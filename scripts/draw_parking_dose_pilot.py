"""Draw the 15-place dose-coding pilot sample (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, dose-coding pilot; locked).
Stratified by size tercile (existing homes) x simultaneous_rewrite, proportional allocation rounded to 15, seed 20261104.

    uv run python scripts/draw_parking_dose_pilot.py
Output: reference/parking_dose_pilot_sample.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import REFERENCE  # noqa: E402


def main() -> None:
    r = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    r = r[(r["status"] == "included") & (r["outcome"] == "all")].copy()
    r["size_tercile"] = pd.qcut(r["homes"], 3, labels=[0, 1, 2])
    g = r.groupby(["size_tercile", "simultaneous_rewrite"], observed=True)
    n = g.size()
    alloc = n / n.sum() * 15
    a = np.floor(alloc).astype(int)
    rem = 15 - a.sum()
    a[(alloc - a).sort_values(ascending=False).index[:rem]] += 1
    rng = np.random.default_rng(20261104)
    pick = []
    for k, grp in g:
        s = grp.sample(int(a[k]), random_state=int(rng.integers(1e9)))
        pick.append(s[["place", "state", "event_year", "homes", "simultaneous_rewrite", "size_tercile"]].assign(
            stratum_size=int(n[k]), stratum_allocation=int(a[k])))
    P = pd.concat(pick, ignore_index=True)
    P.to_csv(REFERENCE / "parking_dose_pilot_sample.csv", index=False)
    print(P.to_string(index=False))


if __name__ == "__main__":
    main()
