"""Parking work session combo (b): TOD + parking combined band from paired draws. docs/parking/CAUSAL_FRAMEWORK_PLAN.md
(combo (b) lock). Evidence only; no tool change.

Parking draws: the 20,000 placebo set averages centred on the real average (reference/parking_placebo_full_draws.csv),
first 2,000, in permits per 1,000 eligible homes a year x 2,668,677 homes x 5 years / 1,000; central = 0. Positive parking
draws x 0.899 (share of parking's upper addition off TOD-covered lots in the combined bundle: 17,819 / 19,818); negative
draws pass through. TOD draws: reference/tod_line_draws.csv.

    uv run python scripts/run_parking_ws_combo_b.py
Output: reference/parking_ws_combo_b.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import REFERENCE  # noqa: E402

HOMES, YEARS, OFF_TOD = 2_668_677, 5, 17_819 / 19_818
TOD_UPPER_TOOL = 13_451


def main() -> None:
    t = pd.read_csv(REFERENCE / "tod_line_draws.csv")
    n = len(t)
    pk = pd.read_csv(REFERENCE / "parking_placebo_full_draws.csv")["centred_on_real"].values[:n] * HOMES * YEARS / 1000
    pk = np.where(pk > 0, pk * OFF_TOD, pk)
    tod = {"lower": t["lower_homes"].values, "central": t["central_homes"].values, "upper (draws as supplied, 12,521 basis)": t["upper_homes"].values,
           "upper (rescaled to the tool's 13,451)": t["central_homes"].values * TOD_UPPER_TOOL / 10_028}
    rows = []
    for line, tv in tod.items():
        pv = np.zeros(n) if line == "central" else pk
        idx = tv + pv
        srt = np.sort(tv) + np.sort(pv)
        rows.append(dict(line=line, tod_p05=np.percentile(tv, 5), tod_p95=np.percentile(tv, 95),
                         parking_p05=np.percentile(pv, 5), parking_p95=np.percentile(pv, 95),
                         combined_index_p05=np.percentile(idx, 5), combined_index_p50=np.percentile(idx, 50), combined_index_p95=np.percentile(idx, 95),
                         combined_sorted_p05=np.percentile(srt, 5), combined_sorted_p95=np.percentile(srt, 95)))
    out = pd.DataFrame(rows)
    out["unit"] = "Wisconsin extra homes permitted 2027-2031"
    out["note"] = ("index pairing assumes TOD and parking errors are unrelated; sorted pairing (low with low) is the widest case if they move "
                   "together. TOD's supplied upper draws are on the 12,521 basis; the tool's TOD upper is 13,451 (AQ-072), shown rescaled.")
    out.to_csv(REFERENCE / "parking_ws_combo_b.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.drop(columns=["unit", "note"]).round(0).to_string(index=False))


if __name__ == "__main__":
    main()
