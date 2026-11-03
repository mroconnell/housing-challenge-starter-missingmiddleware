"""Parking causal follow-up FU7: lot-size bands (Jenks natural breaks, k = 3, per city) on the four-city lot table.
docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Stage 1 follow-ups" (owner OK 2026-11-03 02:29; post hoc; locked before counting).
Data and outcome as scripts/run_parking_lot_cities.py: net new homes per 1,000 lots a year, pinched minus comparison change.

    uv run --all-extras python scripts/run_parking_causal_fu7_lotbands.py
Output: reference/parking_causal_fu7_lotbands.csv (aggregates only)
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

SEED, DRAWS, K = 20261103, 2000, 3


def jenks(values: np.ndarray, k: int) -> list[float]:
    """Exact Fisher-Jenks breaks (minimum within-class squared deviation) on the sorted input; returns k-1 upper bounds."""
    x = np.sort(values)
    n = len(x)
    cs, cs2 = np.concatenate([[0], np.cumsum(x)]), np.concatenate([[0], np.cumsum(x * x)])
    ssd = lambda i, j: (cs2[j] - cs2[i]) - (cs[j] - cs[i]) ** 2 / (j - i)  # noqa: E731  (x[i:j])
    cost = np.full((k + 1, n + 1), np.inf)
    arg = np.zeros((k + 1, n + 1), int)
    cost[0, 0] = 0.0
    for m in range(1, k + 1):
        for j in range(m, n + 1):
            best, bi = np.inf, 0
            for i in range(m - 1, j):
                c = cost[m - 1, i] + ssd(i, j)
                if c < best:
                    best, bi = c, i
            cost[m, j], arg[m, j] = best, bi
    cuts, j = [], n
    for m in range(k, 0, -1):
        i = arg[m, j]
        cuts.append(i)
        j = i
    cuts = sorted(cuts)[1:]
    return [float(x[c - 1]) for c in cuts]


def boot(g: pd.DataFrame, rng) -> tuple[float, float]:
    cells = g["cell"].unique()
    grp = {c: x for c, x in g.groupby("cell")}
    bs = []
    for _ in range(DRAWS):
        s = pd.concat([grp[c] for c in rng.choice(cells, len(cells))])
        if (s["pinched"] == 1).any() and (s["pinched"] == 0).any():
            bs.append(LC.effect(s))
    return float(np.percentile(bs, 5)), float(np.percentile(bs, 95))


def main() -> None:
    rng = np.random.default_rng(SEED)
    lots = pd.concat([LC.sf(), LC.buffalo(), LC.tod_cities()], ignore_index=True)
    lots["cell"] = lots["city"] + ":" + (lots["x5070"] // LC.CELL).astype(int).astype(str) + "_" + (lots["y5070"] // LC.CELL).astype(int).astype(str)
    L = LC.add_rates(lots, "permits_main")
    L = L[L["acres"] > 0].copy()
    L["la"] = np.log(L["acres"])
    rows, band_eff = [], {}
    for city, g in L.groupby("city"):
        q = np.quantile(g["la"].values, np.linspace(0, 1, 1000))
        br = jenks(q, K)
        g = g.assign(band=np.digitize(g["la"].values, br, right=True))
        for bnd in range(K):
            s = g[g["band"] == bnd]
            if (s["pinched"] == 1).sum() < 20 or (s["pinched"] == 0).sum() < 20:
                rows.append(dict(city=city, band=bnd, note="fewer than 20 lots on a side"))
                continue
            lo, hi = boot(s, rng)
            e = LC.effect(s)
            band_eff[(city, bnd)] = e
            rows.append(dict(city=city, band=bnd, acres_from=float(np.exp(s["la"].min())), acres_to=float(np.exp(s["la"].max())),
                             pinched_lots=int((s["pinched"] == 1).sum()), comparison_lots=int((s["pinched"] == 0).sum()),
                             effect=e, p05=lo, p95=hi))
        # reference: the October 0.1-acre split
        for lab, s in (("ref <0.1 acre", g[g["acres"] < 0.1]), ("ref >=0.1 acre", g[g["acres"] >= 0.1])):
            if (s["pinched"] == 1).sum() >= 20 and (s["pinched"] == 0).sum() >= 20:
                rows.append(dict(city=city, band=lab, pinched_lots=int((s["pinched"] == 1).sum()),
                                 comparison_lots=int((s["pinched"] == 0).sum()), effect=LC.effect(s)))
    cities = sorted(L["city"].unique())
    for bnd in range(K):
        vals = {c: band_eff[(c, bnd)] for c in cities if (c, bnd) in band_eff}
        loo = {c: np.mean([v for k, v in vals.items() if k != c]) for c in vals}
        rows.append(dict(city="pooled (equal-weight mean of cities)", band=bnd, effect=np.mean(list(vals.values())),
                         note="leave one city out: " + "; ".join(f"without {c} {v:.1f}" for c, v in loo.items())))
    out = pd.DataFrame(rows)
    out["unit"] = "net new homes per 1,000 lots a year, pinched minus comparison change"
    out.to_csv(REFERENCE / "parking_causal_fu7_lotbands.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 200)
    print(out.drop(columns="unit").round(3).to_string(index=False))


if __name__ == "__main__":
    main()
