"""What the TOD baseline near stops looks like re-based on station areas' share of NEW homes (owner, 2026-10-31 16:09).

    uv run --all-extras python scripts/run_tod_rebase_check.py

Today's baseline (missing_middleware/tod/model.py section 6): each municipality's all-housing baseline x its share of
EXISTING homes near stops (main case). Re-based: x share of new homes near stops = min(1, share of homes x m), where m is
the measured ratio (share of new homes / share of 2010 homes, main-case stops) from the lot data:
Milwaukee 1.35-1.37 and Madison 1.15-1.16 (their own); every other municipality 1.15 (low), 1.28 (both cities pooled,
central), 1.37 (high). A look only: the tool's numbers are not changed. Writes reference/tod_rebase_check.csv.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference"
OWN = {"Milwaukee city": (1.353, 1.351, 1.369), "Madison city": (1.150, 1.155, 1.162)}   # (low, central, high)
OTHER = (1.15, 1.28, 1.37)


def main() -> None:
    A = pd.read_csv(REF / "tod_model_by_area.csv")
    a = A[(A.sizing == "net_effect") & (A.scenario == "typical")]
    a = a.groupby(["area_id", "name", "county"], as_index=False).agg(
        share=("share_near_stops", "first"), low=("baseline_near_low_2027_2031", "sum"),
        central=("baseline_near_central_2027_2031", "sum"), high=("baseline_near_high_2027_2031", "sum"))
    rows = []
    for _, r in a.iterrows():
        m = OWN.get(r["name"], OTHER)
        new_share = [min(1.0, r["share"] * x) for x in m]
        f = [ns / r["share"] if r["share"] > 0 else 1.0 for ns in new_share]   # multiplier on today's baseline
        rows.append({**r.to_dict(), "multiplier_low": f[0], "multiplier_central": f[1], "multiplier_high": f[2],
                     "rebased_central_pace_low_share": r["central"] * f[0], "rebased_central": r["central"] * f[1],
                     "rebased_central_pace_high_share": r["central"] * f[2],
                     "rebased_low_pace": r["low"] * f[1], "rebased_high_pace": r["high"] * f[1]})
    T = pd.DataFrame(rows).sort_values("central", ascending=False)
    T.round(3).to_csv(REF / "tod_rebase_check.csv", index=False)
    s = T.sum(numeric_only=True)
    print(f"today: central {s['central']:,.0f} (pace range {s['low']:,.0f}-{s['high']:,.0f})")
    print(f"re-based: central {s['rebased_central']:,.0f}; share range {s['rebased_central_pace_low_share']:,.0f}-"
          f"{s['rebased_central_pace_high_share']:,.0f}; pace range {s['rebased_low_pace']:,.0f}-{s['rebased_high_pace']:,.0f}")
    print(T.head(6)[["name", "share", "central", "multiplier_central", "rebased_central"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
