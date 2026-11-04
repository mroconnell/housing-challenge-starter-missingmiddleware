"""Yearly permit rates for every comparison place used by the 76 parking repeal places (data export, no test;
Ryan's chart request 2026-11-04 17:44 UTC).

    uv run --all-extras python scripts/export_parking_comparison_yearly_rates.py
Output: reference/parking_comparison_yearly_rates.csv, one row per comparison place and year, 2012-2025.
Pools, panels and homes are the ones each repeal place's own script uses (recorded as in scripts/run_parking_t45_t46.py).
A comparison place used by more than one script takes the panel and homes of the first script that used it
(the main expanded comparison); homes_differ_across_pools flags places whose homes differ between scripts
(the partial-reforms script uses 2010 census homes for repeals before 2015).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_comparison as rpc  # noqa: E402,F401
import run_parking_t45_t46 as t  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

YEARS = range(2012, 2026)


def main() -> None:
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].dropna(subset=["effect"]).reset_index(drop=True)
    m = t.rebuild(real, t.collect())
    assert m["found"].all() and ((m["effect"] - real["effect"]).abs() <= 1e-4).all(), "rebuild mismatch"
    first, homes_seen, users = {}, {}, {}
    for i, x in m.iterrows():
        c = x["call"]
        for k in c["pool"]:
            first.setdefault(k, c)
            homes_seen.setdefault(k, set()).add(round(float(c["homes"].get(k, np.nan)), 1))
            users.setdefault(k, set()).add(real.loc[i, "place"] + ", " + real.loc[i, "state"])
    rows = []
    by_panel = {}
    for k, c in first.items():
        pid = id(c["p"])
        if pid not in by_panel:
            q = c["p"]
            by_panel[pid] = (q.groupby(["key", "year"])["units_total"].sum(), q.drop_duplicates("key", keep="last").set_index("key")["name"])
        permits, names = by_panel[pid]
        h = float(c["homes"].get(k, np.nan))
        for y in YEARS:
            pe = permits.get((k, y), np.nan)
            rows.append(dict(comparison_key=k, name=names.get(k, ""), state_fips=k.split("|")[0],
                             state=next((s for s, f in t.rpc.STATE_FIPS.items() if f == k.split("|")[0]), ""), year=y,
                             permits=pe, existing_homes=h, rate=pe / h * 1000 if pd.notna(pe) and h > 0 else np.nan,
                             reported=bool(pd.notna(pe)), used_by_repeal_places=len(users[k]),
                             homes_differ_across_pools=len(homes_seen[k]) > 1))
    out = pd.DataFrame(rows)
    out.round(4).to_csv(REFERENCE / "parking_comparison_yearly_rates.csv", index=False)
    print(len(out), "rows,", out["comparison_key"].nunique(), "comparison places,",
          int(out.drop_duplicates("comparison_key")["homes_differ_across_pools"].sum()), "with homes differing")


if __name__ == "__main__":
    main()
