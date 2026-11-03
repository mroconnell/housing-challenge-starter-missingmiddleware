"""Parking work session combo (a): parking removed vs not, at TOD's edge-test scale (post hoc; TOD results published).
docs/parking/CAUSAL_FRAMEWORK_PLAN.md (combo (a) detail).

    uv run python scripts/run_parking_ws_combo_a.py
Output: reference/parking_ws_combo_a.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import REFERENCE  # noqa: E402

CODE = {"Charlotte 2019": "removed", "Denver 2018": "removed", "Portland 2020": "removed", "New York": "not", "Philadelphia": "not",
        "Austin 2009": "not", "Chicago 2015": "not", "Saint Paul 2011": "not", "Salt Lake City 2010": "not"}


def main() -> None:
    d = pd.read_csv(REFERENCE / "tod_causal_edge_expand.csv")
    d = d[d["section"].str.startswith("original 11") & (d["variant"] == "main (91 m)") & d["unit"].isin(CODE)].copy()
    d["parking"] = d["unit"].map(CODE)
    d["balance_pass"] = d["balance_pass"].astype(str).str.lower().eq("true")
    k = d[d["balance_pass"]]
    a, b = k[k["parking"] == "removed"]["edge_effect_per_100_acres_per_year"].values, k[k["parking"] == "not"]["edge_effect_per_100_acres_per_year"].values
    rows = [dict(item=f"place: {r.unit} ({r.parking}; balance {'pass' if r.balance_pass else 'FAIL'})", value=r.edge_effect_per_100_acres_per_year) for r in d.itertuples()]
    if len(a) and len(b):
        rng = np.random.default_rng(20261104)
        bs = [rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(2000)]
        est = a.mean() - b.mean()
        loo = [(np.delete(a, i).mean() - b.mean()) for i in range(len(a)) if len(a) > 1] + [(a.mean() - np.delete(b, i).mean()) for i in range(len(b)) if len(b) > 1]
        rows.insert(0, dict(item=f"removed ({len(a)}) minus not removed ({len(b)}), balance-passing places", value=est,
                            p05=np.percentile(bs, 5), p95=np.percentile(bs, 95), loo_min=min(loo), loo_max=max(loo)))
    out = pd.DataFrame(rows)
    out["unit"] = "extra homes per 100 lot acres a year at the district edge (TOD T3 main, 91 m)"
    out["label"] = "POST HOC (TOD edge results already published)"
    out.to_csv(REFERENCE / "parking_ws_combo_a.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.drop(columns=["unit", "label"]).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
