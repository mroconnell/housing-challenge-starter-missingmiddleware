"""Parking Stage 2, item 4: the one pre-chosen trait, excess-parking cost as a share of home value, held-out test.
docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Stage 2 plan" (locked 2026-11-03 before any Stage 2 count).

trait = max(0, old minimum - 0.6) x cost per space / ACS 2024 median home value
cost per space: structured $40,950 if the place's median home value >= the US median, else surface $5,750.
Test: 5 folds by place (seed 20261103); home-weighted linear fit of the main effect on the trait vs the plain
home-weighted average; error = home-weighted mean absolute error on held-out places. Kept only if strictly lower.

    uv run python scripts/run_parking_stage2_trait.py
Output: reference/parking_stage2_trait_test.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_parking_comparison as rpc  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

SEED, FOLDS, FLOOR, STRUCT, SURF = 20261103, 5, 0.6, 40_950.0, 5_750.0
B25077 = RAW / "census_acs5_2024_tbsf_market" / "acsdt5y2024-b25077.dat"


def us_median() -> float:
    for line in B25077.read_text().splitlines():
        if line.startswith("0100000US"):
            return float(line.split("|")[1])
    raise SystemExit("US row missing")


def main() -> None:
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].copy()
    om = pd.read_csv(REFERENCE / "parking_old_minimums.csv").drop_duplicates("prn_key")
    real = real.merge(om[["prn_key", "old_min_apartment"]], on="prn_key", how="left")
    val = rpc.acs_table(B25077, "B25077_E001")
    real["home_value_acs"] = real["acs_geoid"].map(val)
    usm = us_median()
    cost = np.where(real["home_value_acs"] >= usm, STRUCT, SURF)
    real["trait"] = np.maximum(0, real["old_min_apartment"] - FLOOR) * cost / real["home_value_acs"]
    d = real.dropna(subset=["trait", "effect"]).reset_index(drop=True)
    rng = np.random.default_rng(SEED)
    fold = rng.permutation(np.arange(len(d)) % FOLDS)
    v, w, x = d["effect"].values, d["weight"].values, d["trait"].values
    pa, pt = np.empty(len(d)), np.empty(len(d))
    for f in range(FOLDS):
        tr, te = fold != f, fold == f
        pa[te] = np.average(v[tr], weights=w[tr])
        X = np.column_stack([np.ones(tr.sum()), x[tr]])
        sw = np.sqrt(w[tr])
        b = np.linalg.lstsq(X * sw[:, None], v[tr] * sw, rcond=None)[0]
        pt[te] = b[0] + b[1] * x[te]
    err = lambda p: np.average(np.abs(v - p), weights=w)  # noqa: E731
    X = np.column_stack([np.ones(len(d)), x])
    sw = np.sqrt(w)
    full = np.linalg.lstsq(X * sw[:, None], v * sw, rcond=None)[0]
    ea, et = err(pa), err(pt)
    out = pd.DataFrame([dict(places=len(d), left_out=len(real) - len(d), us_median_home_value=usm,
                             trait_median=float(np.median(x)), trait_p10=float(np.percentile(x, 10)), trait_p90=float(np.percentile(x, 90)),
                             share_zero_excess=float((x == 0).mean()), heldout_error_plain=ea, heldout_error_trait=et,
                             passes=bool(et < ea), full_sample_intercept=full[0], full_sample_slope=full[1],
                             unit="error in permits per 1,000 existing homes a year; trait is a share of home value")])
    out.to_csv(REFERENCE / "parking_stage2_trait_test.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.round(4).T.to_string())


if __name__ == "__main__":
    main()
