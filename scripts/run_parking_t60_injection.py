"""Test 60 (post hoc; CAUSAL_FRAMEWORK_PLAN.md "Test 60"): injection catch rate, 2-4 unit homes, main method.

    uv run --all-extras python scripts/run_parking_t60_injection.py

Each of Test 56's 20,000 stand-in sets (true effect 0) gets a known effect delta added to its weighted average; the
Test 56 range rule (average + delta, plus the placebo spread p05-p50 and p95-p50) is applied, and the fake counts as
caught if the range excludes 0 on delta's side. delta = 0 gives the false-alarm rate. Output:
reference/parking_t60_catch_rate.csv.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.pop("MM_BPS_OUTCOME", None)

import summarise_parking_t56 as s  # noqa: E402

O = "units_2_4"
WI = 13343.385
HOMES = (0, 1000, 2500, 4727, 10000)


def main() -> None:
    cols, E, W, check = s.standin_draws(O)
    v = s.set_avgs(cols, E, W, False)  # weighted set averages (homes x after-years weights), as the headline
    p05, p50, p95 = np.percentile(v, [5, 50, 95])
    lo_off, hi_off = p05 - p50, p95 - p50
    rows = []
    for h in HOMES:
        for sgn in ((1,) if h == 0 else (1, -1)):
            d = sgn * h / WI
            est = v + d
            lo, hi = est + lo_off, est + hi_off
            if h == 0:
                caught = float(np.mean((lo > 0) | (hi < 0)))
                side = "either side (false alarm)"
            else:
                caught = float(np.mean(lo > 0)) if sgn > 0 else float(np.mean(hi < 0))
                side = "above 0" if sgn > 0 else "below 0"
            rows.append(dict(injected_wisconsin_homes_5yr=sgn * h, injected_rate=d, catch_rate=caught, caught_if=side,
                             sets=len(v), placebo_p05_minus_p50=lo_off, placebo_p95_minus_p50=hi_off,
                             draw_rebuild_max_diff=check, unit="homes per 1,000 existing homes a year"))
    out = pd.DataFrame(rows)
    out.round(6).to_csv(s.REF / "parking_t60_catch_rate.csv", index=False)
    print(out[["injected_wisconsin_homes_5yr", "injected_rate", "catch_rate", "caught_if"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
