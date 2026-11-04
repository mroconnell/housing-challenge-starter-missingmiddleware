"""Yearly permit rates for the 76 parking repeal places and their comparison groups (data export, no test;
Ryan's chart request 2026-11-04 17:26 UTC).

    uv run --all-extras python scripts/export_parking_place_yearly_rates.py
Output: reference/parking_place_yearly_rates.csv, one row per repeal place and year, 2012-2025.
Pools, homes and panels are the ones each place's own script uses (recorded as in scripts/run_parking_t45_t46.py).
comparison_rate is pooled: the reporting pool places' permits / their existing homes x 1,000 (places that did not
report that year are left out of both; inside the estimate windows every pool place reports). South Bend's rows are for the combined city + unincorporated St. Joseph County area its permits are filed under.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_t45_t46 as t  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

YEARS = range(2012, 2026)


def main() -> None:
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].dropna(subset=["effect"]).reset_index(drop=True)
    m = t.rebuild(real, t.collect())
    assert m["found"].all() and ((m["effect"] - real["effect"]).abs() <= 1e-4).all(), "rebuild mismatch"
    rows = []
    for i, x in m.iterrows():
        c, r = x["call"], real.loc[i]
        key = c["key"]
        own = c["p"][c["p"]["key"] == key].groupby("year")["units_total"].sum()
        pool = c["p"][c["p"]["key"].isin(c["pool"])].groupby("year")["units_total"].sum()
        rep = c["p"][c["p"]["key"].isin(c["pool"])].groupby("year")["key"].unique()
        h_own = float(c["homes"][key])
        h_pool = float(c["homes"].reindex(c["pool"]).sum())
        in_win = set(c["pre"]) | set(c["post"])
        for y in YEARS:
            pe = own.get(y, np.nan)
            pp = pool.get(y, np.nan)
            reporting = list(rep.get(y, []))
            h_rep = float(c["homes"].reindex(reporting).sum())
            rows.append(dict(key=key, place=r["place"], state=r["state"], event_year=int(r["event_year"]), year=y,
                             k=y - int(r["event_year"]), in_estimate_window=y in in_win,
                             window_part="before" if y in c["pre"] else "after" if y in c["post"] else "",
                             permits=pe, existing_homes=h_own, own_rate=pe / h_own * 1000 if pd.notna(pe) else np.nan,
                             comparison_permits=pp, comparison_homes_all=h_pool, comparison_homes_reporting=h_rep,
                             comparison_rate=pp / h_rep * 1000 if pd.notna(pp) and h_rep > 0 else np.nan,
                             comparison_places=len(c["pool"]), comparison_places_reporting=len(reporting),
                             comparison_window=c["window"]))
    out = pd.DataFrame(rows)
    out.round(4).to_csv(REFERENCE / "parking_place_yearly_rates.csv", index=False)
    print(len(out), "rows,", out["key"].nunique(), "places")


if __name__ == "__main__":
    main()
