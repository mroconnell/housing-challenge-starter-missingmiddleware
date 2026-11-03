"""Parking Stage 2, item 2: lines with "near" places set to 0 (locked plan), beside the current lines.
Does not change the tool; writes reference/parking_stage2_near_recount.csv.

    uv run python scripts/run_parking_stage2_near.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.parking import model as pm  # noqa: E402
from missing_middleware.paths import PROCESSED, REFERENCE  # noqa: E402


def main() -> None:
    areas = pd.read_parquet(PROCESSED / "foundation" / "areas.parquet")
    munis = areas[areas["level"] == "municipality"][["area_id", "name", "muni_type", "housing_units_acs"]].rename(columns={"housing_units_acs": "homes"})
    bench = pd.read_csv(REFERENCE / "parking_wi_benchmark_places.csv")
    at = set(bench.loc[bench["benchmark_rating"] == "at", "area_id"])
    near = set(bench.loc[bench["benchmark_rating"] == "near", "area_id"])
    high = float(pd.read_csv(REFERENCE / "parking_placebo_full_summary.csv")["range_from_placebo_high"].iloc[0])
    low = float(pd.read_csv(REFERENCE / "parking_placebo_full_summary.csv")["real_average"].iloc[0])
    rows = []
    for lab, ex in (("current (at = 0)", at), ("Stage 2 main (at and near = 0)", at | near)):
        h = pm.eligible_homes(munis, ex)
        rows.append(dict(version=lab, eligible_homes=float(h.sum()),
                         low=float(pm.additions(h, low, floor=False).values.sum()), high=float(pm.additions(h, high).values.sum()),
                         near_places="; ".join(sorted(munis.set_index("area_id").loc[list(near), "name"])) if ex is not at else ""))
    out = pd.DataFrame(rows)
    out.to_csv(REFERENCE / "parking_stage2_near_recount.csv", index=False)
    print(out.round(0).to_string(index=False))


if __name__ == "__main__":
    main()
