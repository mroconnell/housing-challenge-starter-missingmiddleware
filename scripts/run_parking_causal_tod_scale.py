"""Parking x rezoning at the TOD (station-area) scale. POST HOC and descriptive: the station-area effects were seen
before this grouping was made (docs/parking/CAUSAL_STAGE1_RESULTS.md).

Effects: TOD's station-area effect within 1/4 mile per place, extra homes per 100 lot acres a year
(reference/tod_causal_line_age.csv, column "measured"). Parking coding: TOD's place list for the parking 2x2
(reference/tod_places_for_parking_2x2.csv: "yes" = minimums removed with the rezoning). Seattle is "unknown" and left out.

    uv run python scripts/run_parking_causal_tod_scale.py
Output: reference/parking_causal_tod_scale.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import REFERENCE  # noqa: E402

CODE = {"Austin": "partial", "Charlotte": "yes", "Chicago 2015": "partial", "Denver": "yes", "New York": "no",
        "Philadelphia": "partial", "Portland 2020": "yes", "Saint Paul": "partial", "Salt Lake City": "partial"}


def main() -> None:
    d = pd.read_csv(REFERENCE / "tod_causal_line_age.csv")
    d = d[d["row"] == "place"].set_index("place").loc[list(CODE)]
    d["parking"] = d.index.map(CODE)
    rem = d["parking"] == "yes"
    rng = np.random.default_rng(20261103)
    a, b = d.loc[rem, "measured"].values, d.loc[~rem, "measured"].values
    bs = [rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(2000)]
    rows = [dict(item="removed minus not removed (equal-weight)", value=a.mean() - b.mean(), p05=np.percentile(bs, 5),
                 p95=np.percentile(bs, 95), places_removed=len(a), places_not=len(b))]
    for p in d.index:
        e = d.drop(p)
        rows.append(dict(item=f"without {p}", value=e.loc[e["parking"] == "yes", "measured"].mean() - e.loc[e["parking"] != "yes", "measured"].mean()))
    for p, r in d.iterrows():
        rows.append(dict(item=f"place: {p} ({r['parking']})", value=r["measured"]))
    out = pd.DataFrame(rows)
    out["unit"] = "extra homes per 100 lot acres a year within 1/4 mile"
    out.to_csv(REFERENCE / "parking_causal_tod_scale.csv", index=False)
    print(out.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
