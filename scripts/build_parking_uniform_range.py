"""Parking's 90% range for the uniform display (docs/UNIFORM_DISPLAY_SPEC.md; owner 2026-11-04: no centre lines,
exact numbers, the same 90% range for every reform). Not read by the tool until Ryan approves the spec.

    uv run --all-extras python scripts/build_parking_uniform_range.py
Output: reference/parking_uniform_range.csv (extra homes permitted in Wisconsin, 2027-2031)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import REFERENCE  # noqa: E402

ELIGIBLE_HOMES = 2_668_677  # ACS 2020-2024, outside the 18 places that already removed minimums
YEARS = 5
BASELINE_V3 = 124_000  # statewide current-law baseline, 2027-2031


def main() -> None:
    s = pd.read_csv(REFERENCE / "parking_placebo_full_summary.csv").iloc[0]
    k = ELIGIBLE_HOMES * YEARS / 1000
    sw = pd.read_csv(REFERENCE / "parking_model_statewide_by_year.csv")
    upper_model = float(sw.loc[sw["year"].between(2027, 2031), "addition_upper"].sum())
    rows = [
        ("range_low", "Low end of 90% range", float(s["range_from_placebo_low"])),
        ("range_high", "High end of 90% range", float(s["range_from_placebo_high"])),
        ("side_measured_average", "Measured average, 76 repeal places", float(s["real_average"])),
    ]
    out = pd.DataFrame([{"id": i, "label": lab, "rate_per_1000_homes_year": rate, "homes_2027_2031": round(rate * k),
                         "share_of_baseline_v3": round(rate * k / BASELINE_V3, 4)} for i, lab, rate in rows])
    hi = int(out.loc[out["id"] == "range_high", "homes_2027_2031"].iloc[0])
    assert abs(hi - upper_model) < 1, (hi, upper_model)  # must match the tool's current upper line
    out.to_csv(REFERENCE / "parking_uniform_range.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
