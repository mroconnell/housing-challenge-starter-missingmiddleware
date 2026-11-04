"""Direction of the top all-variables traits (descriptive; Ryan 2026-11-04). Average effect above vs below each trait's
median, weighted by homes x after-years and equally, with and without San Francisco, plus a 90% place-bootstrap range
for the gap (2,000 draws, seed 20261104; the median split is redone in each draw).

    uv run --all-extras python scripts/check_parking_allvars_direction.py
Output: reference/parking_allvars_direction.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import REFERENCE  # noqa: E402

TRAITS = {"rate_before": "Permit rate before repeal", "A_rent_burden_30plus": "Rent burden 30%+",
          "A_crowded_share": "Crowded homes", "A_labour_force_participation": "Labour-force participation",
          "A_rooms_1to3_share": "Small homes (1-3 rooms)", "V5_vacancy_rate": "Vacancy"}
SEED, DRAWS = 20261104, 2000


def gap(x, y, w):
    med = np.median(x)
    hi, lo = x > med, x <= med
    if hi.sum() == 0 or lo.sum() == 0:
        return np.nan, np.nan, np.nan
    a, b = np.average(y[hi], weights=w[hi]), np.average(y[lo], weights=w[lo])
    return a, b, a - b


def main() -> None:
    v = pd.read_csv(REFERENCE / "parking_allvars_values.csv")
    e = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    e = e[(e["status"] == "included") & (e["outcome"] == "all")][["prn_key", "effect", "weight"]]
    d0 = v.merge(e, on="prn_key")
    rows = []
    for sf in ("with SF", "without SF"):
        d = d0 if sf == "with SF" else d0[d0["place"] != "San Francisco"]
        for wl in ("homes", "equal"):
            for t, lab in TRAITS.items():
                s = d.dropna(subset=[t])
                x, y = s[t].values, s["effect"].values
                w = s["weight"].values if wl == "homes" else np.ones(len(s))
                a, b, g = gap(x, y, w)
                rng = np.random.default_rng(SEED)
                bs = [gap(x[i], y[i], w[i])[2] for i in (rng.integers(0, len(s), len(s)) for _ in range(DRAWS))]
                bs = np.array(bs)[np.isfinite(bs)]
                rows.append(dict(run=sf, weights=wl, trait=lab, places=len(s), above=a, below=b, gap=g,
                                 gap_p05=np.percentile(bs, 5), gap_p95=np.percentile(bs, 95)))
    out = pd.DataFrame(rows)
    out.round(3).to_csv(REFERENCE / "parking_allvars_direction.csv", index=False)
    print(out.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
