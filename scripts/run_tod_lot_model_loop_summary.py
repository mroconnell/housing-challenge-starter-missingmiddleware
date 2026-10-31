"""Every loop round and city in one table, with one summary score (docs/tod/LOT_MODEL_PLAN.md item 57.2).

    uv run --all-extras python scripts/run_tod_lot_model_loop_summary.py

Score = median over cities of |log(predicted / actual homes after)|; "same pace as before" is scored the same way.
Writes reference/tod_lot_model_loop_summary.csv.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from missing_middleware.paths import REFERENCE  # noqa: E402


def score(pred: pd.Series, act: pd.Series) -> float:
    ok = (pred > 0) & (act > 0)
    v = np.abs(np.log(pred[ok] / act[ok]))
    return float(np.median(v)) if len(v) else np.nan


def main() -> None:
    rows = []
    for f in sorted(REFERENCE.glob("tod_lot_model_loop_round*.csv")):
        m = re.match(r"tod_lot_model_loop_round(\d+)(?:_seed(\d+))?", f.stem)
        R = pd.read_csv(f)
        for _, r in R.iterrows():
            rows.append({"round": int(m.group(1)), "seed": int(m.group(2)) if m.group(2) else 20261031, "city": r["city"],
                         "actual_after": r["actual_after"], "model_after": r["model_after"], "same_pace": r["before"]})
    T = pd.DataFrame(rows)
    T.round(1).to_csv(REFERENCE / "tod_lot_model_loop_summary.csv", index=False)
    S = T.groupby(["round", "seed"]).apply(lambda g: pd.Series({
        "cities": len(g), "score_model": score(g["model_after"], g["actual_after"]),
        "score_same_pace": score(g["same_pace"], g["actual_after"]),
        "cities_at_or_below_zero": int((g["model_after"] <= 0).sum())})).reset_index()
    pd.set_option("display.width", 200)
    print(S.round(2).to_string(index=False))
    W = T[T["seed"] == 20261031].pivot(index="city", columns="round", values="model_after")
    W["actual"] = T.groupby("city")["actual_after"].first()
    print((100 * (W.drop(columns="actual").div(W["actual"], axis=0) - 1)).round(0).to_string())


if __name__ == "__main__":
    main()
