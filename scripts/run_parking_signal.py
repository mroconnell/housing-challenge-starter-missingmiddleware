"""Parking: quick signal passes on the 76-place comparison (docs/parking/SIGNAL_PLAN.md, items 1 and 3).

    uv run python scripts/run_parking_signal.py
Output: reference/parking_signal_groups.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import REFERENCE  # noqa: E402

SOUTH = {"Delaware", "District of Columbia", "Florida", "Georgia", "Maryland", "North Carolina", "South Carolina", "Virginia",
         "West Virginia", "Alabama", "Kentucky", "Mississippi", "Tennessee", "Arkansas", "Louisiana", "Oklahoma", "Texas"}
MOUNTAIN = {"Arizona", "Colorado", "Idaho", "Montana", "Nevada", "New Mexico", "Utah", "Wyoming"}


def summ(g, col="effect"):
    g = g.dropna(subset=[col])
    w = g["homes"] * g["n_post"]
    rng = np.random.default_rng(20261101)
    bs = []
    for _ in range(2000):
        i = rng.integers(0, len(g), len(g))
        bs.append(np.average(g[col].values[i], weights=w.values[i]))
    nosf = g[g["place"] != "San Francisco"]
    return dict(places=len(g), weighted=float(np.average(g[col], weights=w)), p05=float(np.percentile(bs, 5)),
                p95=float(np.percentile(bs, 95)), median=float(g[col].median()),
                weighted_without_sf=float(np.average(nosf[col], weights=nosf["homes"] * nosf["n_post"])) if len(nosf) else np.nan)


def main() -> None:
    e = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    e = e[e["status"] == "included"]
    a = e[e["outcome"] == "all"].set_index("key")
    m = e[e["outcome"] == "2plus"].set_index("key")
    a["booming"] = a["ctrl_after"] > a["ctrl_before"]
    a["sunbelt"] = a["state"].isin(SOUTH | MOUNTAIN)
    rows = [dict(group="all 76", **summ(a))]
    for lab, mask in (("booming market", a["booming"]), ("cooling market", ~a["booming"]),
                      ("Sunbelt (South + Mountain)", a["sunbelt"]), ("rest of country", ~a["sunbelt"])):
        rows.append(dict(group=lab, **summ(a[mask])))
    # 3. project size
    one = a.copy()
    one["effect"] = a["effect"] - m["effect"].reindex(a.index)
    rows.append(dict(group="homes in 2+ unit buildings", **summ(m.assign(n_post=a["n_post"].reindex(m.index)))))
    rows.append(dict(group="homes in 1-unit buildings", **summ(one)))
    sh = a[["homes", "n_post", "place"]].copy()
    pa, pb = m["rate_after"] / a["rate_after"].replace(0, np.nan), m["rate_before"] / a["rate_before"].replace(0, np.nan)
    ca, cb = m["ctrl_after"] / a["ctrl_after"].replace(0, np.nan), m["ctrl_before"] / a["ctrl_before"].replace(0, np.nan)
    sh["effect"] = ((pa - pb) - (ca - cb)) * 100
    rows.append(dict(group="share of homes in 2+ unit buildings (percentage points)", **summ(sh)))
    for lab, mask in (("2+ unit homes, booming market", a["booming"]), ("2+ unit homes, cooling market", ~a["booming"])):
        rows.append(dict(group=lab, **summ(m[mask.reindex(m.index).fillna(False)].assign(n_post=a["n_post"].reindex(m.index)))))
    out = pd.DataFrame(rows)
    out.to_csv(REFERENCE / "parking_signal_groups.csv", index=False)
    pd.set_option("display.width", 200)
    print(out.round(2).to_string(index=False))
    print(a.loc[a["booming"]].sort_values("homes", ascending=False)[["place", "effect"]].head(8).round(2).to_string())


if __name__ == "__main__":
    main()
