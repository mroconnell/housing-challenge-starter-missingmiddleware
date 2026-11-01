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
    # Central (owner 2026-11-01 22:31): the pre-registered scaled version, "if Wisconsin did as well as the average
    # reform city, at its coverage": pooled ratio of sums within 1/4 mile (effect per 100 lot acres a year / coverage
    # difference, each place once) x Wisconsin coverage x Wisconsin lot acres x 5 years x statewide scale; range = the
    # same with each place left out in turn. An upper bound per the Milwaukee streetcar check.
    C = pd.read_csv(REFERENCE / "tod_station_area_effects_by_city.csv")
    V = pd.read_csv(REFERENCE / "tod_station_area_wisconsin_versions.csv").set_index("band").loc["0-1/4"]
    q = C[C.band == "0-1/4"].dropna(subset=["effect_per_100_acres", "coverage_diff"])
    val = lambda d: d.effect_per_100_acres.sum() / d.coverage_diff.sum() * V.wi_coverage * V.wi_acres / 100 * 5 * scale  # noqa: E731
    loo = [val(q[q.city != c]) for c in q.city]
    rows.append({"line": "average_reform_scaled", "extra_homes_2027_2031": round(val(q), 1), "range_low": round(min(loo), 1),
                 "range_high": round(max(loo), 1), "two_city_value": round(val(q) / scale, 1), "statewide_scale": round(scale, 4),
                 "note": f"pre-registered scaled version: {len(q)} places, pooled ratio within 1/4 mile x Wisconsin coverage "
                         f"{V.wi_coverage:.3f} x {V.wi_acres:,.0f} lot acres; range = each place left out"})
    out = pd.DataFrame(rows)
    out.to_csv(REFERENCE / "tod_station_area_line.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
