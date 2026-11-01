"""The station-area line for the tool's "Little response" path (owner, 2026-11-01 20:31: draft option A).

Reads the lot model's Wisconsin output (scripts/run_tod_station_lotmodel.py, lot traits; within ¼ mile of rail and
rapid stops in Milwaukee and Madison, extra homes over 5 years; range = the fits that each leave one training place
out) and scales it to the state by homes within ½ mile of rail and rapid stops (2020 census blocks: 89,528 statewide,
80,930 in Milwaukee and Madison; scripts/build_tod_station_wisconsin.py). Beyond ¼ mile the model did not beat zero on
hidden places, so those bands count zero (locked rule). No floor at zero (owner rule: no evidence-free floors).

    uv run --all-extras python scripts/build_tod_station_area_line.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from missing_middleware.paths import REFERENCE  # noqa: E402

HOMES_HALF_MILE_STATE, HOMES_HALF_MILE_MKE_MAD = 89_528, 80_930


def main() -> None:
    scale = HOMES_HALF_MILE_STATE / HOMES_HALF_MILE_MKE_MAD
    rows = []
    for line, f, note in (("station_area", "tod_station_lotmodel_wisconsin_lot.csv", "lot-trait model (main)"),
                          ("station_area_strings", "tod_station_lotmodel_wisconsin_lot_strings.csv",
                           "lot-trait model with the strings-attached city trait (did not earn a place; shown as a what-if)")):
        w = pd.read_csv(REFERENCE / f).set_index("band").loc["0-1/4"]
        rows.append({"line": line, "extra_homes_2027_2031": round(w.all_cities * scale, 1), "range_low": round(w.low * scale, 1),
                     "range_high": round(w.high * scale, 1), "two_city_value": w.all_cities, "statewide_scale": round(scale, 4),
                     "note": note})
    out = pd.DataFrame(rows)
    out.to_csv(REFERENCE / "tod_station_area_line.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
