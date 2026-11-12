"""Test 57, added after the lock (audit, 2026-11-12 13:59 UTC), display only: the before-window rate with both arms
pooled, beside each run's MDE, so the MDE can be read as a share of the usual level.

    uv run python scripts/summarise_parking_t57_pooled_rate.py

Rate = 100 x (sum of units) / (sum of eligible lot acres), both arms together, averaged over the run's before-window
years (homes per 100 eligible lot acres a year). Not split by arm. Output: reference/parking_t57_pooled_rate.csv.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
P = ROOT / "data" / "processed" / "t57"
REF = ROOT / "reference"
BEFORE = {"ny_dob": (2011, 2015), "ny_dob_keepmih": (2011, 2015), "ny_dob_samezone": (2011, 2015),
          "ny_dob_legacy2020": (2011, 2015), "ny_hpd": (2014, 2015), "ny_hpd_keepmih": (2014, 2015), "sf_a": (2003, 2007)}


def main() -> None:
    mde = pd.read_csv(REF / "parking_t57_mde.csv").set_index("run")["mde"]
    rows = []
    for run, (a, b) in BEFORE.items():
        d = pd.read_csv(P / f"panel_{run}.csv")
        d = d[(d["year"] >= a) & (d["year"] <= b)]
        y = d.groupby("year")[["units", "acres"]].sum()
        rate = float((100 * y["units"] / y["acres"]).mean())
        rows.append(dict(run=run, before_window=f"{a}-{b}", pooled_before_rate=round(rate, 3), mde=round(float(mde[run]), 3),
                         mde_share_of_pooled_rate=round(float(mde[run]) / rate, 3),
                         unit="homes per 100 eligible lot acres a year",
                         label="added after the lock, display only; both arms pooled, not split by arm"))
    out = pd.DataFrame(rows)
    out.to_csv(REF / "parking_t57_pooled_rate.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
