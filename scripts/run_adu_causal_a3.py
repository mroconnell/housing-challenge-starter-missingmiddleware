"""ADU causal framework A3 (docs/adu/CAUSAL_FRAMEWORK_PLAN.md, locked before running).

How far off the model was for a state it never saw: the adopted pooled model (rv.build defaults = V6s rules,
AQ-065/066/067) is refitted with each of the 7 non-California statewide-law states held out. Errors are
log(predicted / observed) post-law ADU rates. Range 1: central x exp(+/- t(6 df, 90%) x RMS). Range 2:
bootstrap over states (10,000 draws, seed 20261103) of the RMS, central x exp(+/- 1.645 x 95th percentile RMS),
plus each state's own miss applied to the central. Law-side error only.

Run: uv run python scripts/run_adu_causal_a3.py
Outputs: reference/adu_causal_a3_by_state.csv, reference/adu_causal_a3_range.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_adu_vermont_options as vto  # noqa: E402
import run_pooled_revision as rv  # noqa: E402
from missing_middleware.comparison import pooled_regression as pr  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

T6_90 = 1.943180
SEED = 20261103


def main():
    ctx = vto.context()
    p = rv.build(ctx["d"], ctx["pan"])
    la = vto.loso(p, vto.CFG_A, pr.STATEWIDE_STATES)
    e = np.log(la["pred_rate"].astype(float) / la["obs_rate"].astype(float))
    st = pd.read_csv(REFERENCE / "adu_model_statewide.csv").set_index("path")["additional_units"]
    c = float(st["central"])
    rms = float(np.sqrt(np.mean(e ** 2)))
    rng = np.random.default_rng(SEED)
    boot = np.array([np.sqrt(np.mean(rng.choice(e.to_numpy(), len(e)) ** 2)) for _ in range(10_000)])
    b95 = float(np.percentile(boot, 95))
    by = pd.DataFrame({"state": e.index, "obs_rate": la["obs_rate"].values, "pred_rate": la["pred_rate"].values,
                       "log_error": e.values, "central_if_wi_missed_like_this": c * np.exp(-e.values)})
    rng_rows = pd.DataFrame([
        dict(version="t 6 df x RMS", rms=rms, multiplier=T6_90, low=c * np.exp(-T6_90 * rms), central=c,
             high=c * np.exp(T6_90 * rms)),
        dict(version="1.645 x bootstrap 95th pct RMS", rms=b95, multiplier=1.645, low=c * np.exp(-1.645 * b95),
             central=c, high=c * np.exp(1.645 * b95)),
        dict(version="each state's own miss (min-max)", rms=np.nan, multiplier=np.nan,
             low=by.central_if_wi_missed_like_this.min(), central=c, high=by.central_if_wi_missed_like_this.max())])
    rng_rows["mean_log_error"] = float(e.mean())
    by.round(4).to_csv(REFERENCE / "adu_causal_a3_by_state.csv", index=False)
    rng_rows.round(4).to_csv(REFERENCE / "adu_causal_a3_range.csv", index=False)
    print(by.round(3).to_string(index=False)); print(rng_rows.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
