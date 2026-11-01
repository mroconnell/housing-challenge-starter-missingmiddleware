"""The TOD lot-model line (owner, 2026-11-01: "take the drift rule as our current favorite in the tool").

    uv run --all-extras python scripts/build_tod_lot_model_line.py

Drift rule (docs/tod/MODEL_MENU_RESULTS.md, post-hoc mean-reversion sensitivity): across the 9 reform cities,
change in the upzoned lots' share of new homes = a + b x (share before - 0.5). Applied to Milwaukee and Madison's
law-on lots (share before = actual 2019-2024 share in each city's lot table), times each table's no-reform total
2027-2031, scaled to the state by the near-stop baseline (x 1.147). Range: the 9 fits leaving one city out.
Also writes the pre-registered average-change benchmark for comparison.
Reads reference/tod_menu_share_gradient_boosting.csv (actual shares are the same in every method's table).
Writes reference/tod_lot_model_line.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from missing_middleware.paths import REFERENCE  # noqa: E402

SHARE_BEFORE = {"Milwaukee": 0.245, "Madison": 0.261}   # actual 2019-2024 share on law-on lots (wi_lots.parquet)
TABLE_HOMES = {"Milwaukee": 245266.0, "Madison": 112231.0}   # 2020 census homes in each city's lot table


def wi_inputs() -> tuple[list, float]:
    """From the current model outputs (they follow the shared all-housing baseline): each city's no-reform total
    2027-2031 in its lot table, and the statewide scale (state near-stop baseline / the two cities')."""
    A = pd.read_csv(REFERENCE / "tod_model_by_area.csv")
    a = A[(A.sizing == "net_effect") & (A.scenario == "typical")].groupby("name").agg(
        share=("share_near_stops", "first"), near=("baseline_near_central_2027_2031", "sum"))
    H = pd.read_csv(REFERENCE / "tod_near_stop_homes_by_muni.csv").groupby("name")["homes_2020"].sum()
    wi = []
    for c in ("Milwaukee", "Madison"):
        n = f"{c} city"
        total = float(a.loc[n, "near"] / a.loc[n, "share"]) * min(1.0, TABLE_HOMES[c] / float(H[n]))
        wi.append((c, SHARE_BEFORE[c], total))
    state = float(a["near"].sum())
    return wi, state / float(a.loc[["Milwaukee city", "Madison city"], "near"].sum())


def drift_total(d: pd.DataFrame, WI: list, SCALE: float) -> float:
    a, b = np.linalg.lstsq(np.c_[np.ones(len(d)), d["share_before"] - 0.5], d["actual_change"].to_numpy(), rcond=None)[0]
    return sum((a + b * (sb - 0.5)) * t for _, sb, t in WI) * SCALE


def main() -> None:
    R = pd.read_csv(REFERENCE / "tod_menu_share_gradient_boosting.csv")
    WI, SCALE = wi_inputs()
    print("Wisconsin inputs:", [(c, round(t, 1)) for c, _, t in WI], "scale", round(SCALE, 4), flush=True)
    central = drift_total(R, WI, SCALE)
    loo = [drift_total(R[R.city != c], WI, SCALE) for c in R.city]
    avg = float(R["actual_change"].mean()) * sum(t for *_, t in WI) * SCALE
    out = pd.DataFrame([
        {"line": "lot_model_drift", "extra_homes_2027_2031": central, "range_low": min(loo), "range_high": max(loo),
         "rule": "change in upzoned share = a + b x (share before - 0.5), 9 reform cities; Wisconsin share before 2019-2024",
         "range_rule": "9 fits leaving one reform city out"},
        {"line": "average_change_benchmark", "extra_homes_2027_2031": avg, "range_low": np.nan, "range_high": np.nan,
         "rule": "others' average change in upzoned share (+0.040), pre-registered", "range_rule": ""},
    ])
    out.round(1).to_csv(REFERENCE / "tod_lot_model_line.csv", index=False)
    print(out.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
