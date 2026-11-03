"""Parking work session B1: multifamily-zoned lots (Chicago only; allowed FAR >= 1.2 before), reform lots (within 402 m of
a station, 2015 TOD parking rule) vs comparison lots (402-805 m). Net new homes per 100 multifamily-zoned lot acres a year,
reform minus comparison change, 90% interval from 500 m cells. docs/parking/CAUSAL_FRAMEWORK_PLAN.md (Work session, B1).

    uv run --all-extras python scripts/run_parking_ws_b1.py
Output: reference/parking_ws_b1.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import REFERENCE  # noqa: E402
from scripts import run_parking_lot_cities as LC  # noqa: E402
from scripts import run_parking_lot_test as LT  # noqa: E402

SEED, DRAWS = 20261104, 2000


def per_acre(g):
    t, c = g[g["pinched"] == 1], g[g["pinched"] == 0]
    f = lambda x: ((x["after_py"] - x["before_py"]).sum() / x["acres"].sum()) * 100  # noqa: E731
    return f(t) - f(c), f(t), f(c)


def main() -> None:
    d = LT.lots()
    d = d[(d["treated"] == 0) & (d["city"] == "Chicago") & (d["far_before"] >= 1.2) & (d["acres"] > 0)].copy()
    d = d[(d["dist_station_m"] <= 805)]
    d["pinched"] = d["parking"]
    d["permits_main"] = d["permits"]
    d["cell"] = "Chicago:" + (d["x5070"] // LC.CELL).astype(int).astype(str) + "_" + (d["y5070"] // LC.CELL).astype(int).astype(str)
    L = LC.add_rates(d, "permits_main")
    est, it, ic = per_acre(L)
    rng = np.random.default_rng(SEED)
    cells = L["cell"].unique()
    grp = {c: x for c, x in L.groupby("cell")}
    bs = []
    for _ in range(DRAWS):
        s = pd.concat([grp[c] for c in rng.choice(cells, len(cells))])
        if (s["pinched"] == 1).any() and (s["pinched"] == 0).any():
            bs.append(per_acre(s)[0])
    out = pd.DataFrame([dict(city="Chicago", reform_lots=int((L["pinched"] == 1).sum()), comparison_lots=int((L["pinched"] == 0).sum()),
                             reform_change=it, comparison_change=ic, estimate=est, p05=np.percentile(bs, 5), p95=np.percentile(bs, 95),
                             p0125=np.percentile(bs, 1.25), p9875=np.percentile(bs, 98.75),
                             unit="net new homes per 100 multifamily-zoned lot acres a year (after minus before)",
                             note="one city: descriptive, not 'supported'; FAR >= 1.2 before; reform = within 402 m of a station")])
    out.to_csv(REFERENCE / "parking_ws_b1.csv", index=False)
    print(out.drop(columns=["unit", "note"]).round(3).T.to_string())


if __name__ == "__main__":
    main()
