"""Run the pre-registered round-3 test (docs/parking/ROUND3_PLAN.md).

    uv run --all-extras python scripts/run_parking_round3.py
Inputs: reference/parking_expanded_effects.csv, parking_round3_vars.csv, parking_old_minimums.csv,
parking_transit_share.csv, parking_surface_lots.csv, parking_place_traits.csv (traits T1-T6 for the tools),
tod_ab2097_by_jurisdiction.csv (California check for V4-V7).
Outputs: reference/parking_round3_variables.csv, _variables_california.csv, _tools.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_expanded as rpe  # noqa: E402
import run_parking_traits as rpt  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

SEED, FOLDS, REPEATS, DRAWS, MIN_GAIN = 20261027, 10, 20, 2000, 0.05
SINGLE = ["V1_old_min_apartment", "V2_old_min_single_family", "V4_renter_share", "V5_vacancy_rate", "V6_share_built_before_1960",
          "V7_share_homes_5plus", "V8_share_permits_5plus_before", "V9_value_per_unit_rel", "V10_permit_volatility",
          "V11_repeal_year", "V12_prior_partial_reform", "V13_rewrite_same_time", "V14_state_large_city_share_repealed",
          "V15_region", "V16_share_homes_near_transit", "V17_share_land_surface_parking", "V18_share_parking_in_large_sites",
          "V19_log_island_acres", "V20_share_households_no_car", "V21_share_commute_transit", "V22_mean_commute_minutes"]


def data() -> pd.DataFrame:
    e = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    d = e[(e["status"] == "included") & (e["outcome"] == "all")].copy()
    d = d.merge(pd.read_csv(REFERENCE / "parking_round3_vars.csv").drop(columns=["place", "state", "key", "acs_geoid"]), on="prn_key", how="left")
    m = pd.read_csv(REFERENCE / "parking_old_minimums.csv")[["prn_key", "old_min_apartment", "old_min_single_family"]]
    d = d.merge(m.rename(columns={"old_min_apartment": "V1_old_min_apartment", "old_min_single_family": "V2_old_min_single_family"}), on="prn_key", how="left")
    d = d.merge(pd.read_csv(REFERENCE / "parking_transit_share.csv")[["prn_key", "V16_share_homes_near_transit", "V19_log_island_acres"]], on="prn_key", how="left")
    s = REFERENCE / "parking_surface_lots.csv"
    if s.exists():
        d = d.merge(pd.read_csv(s)[["prn_key", "V17_share_land_surface_parking", "V18_share_parking_in_large_sites"]], on="prn_key", how="left")
    else:
        d["V17_share_land_surface_parking"] = np.nan
        d["V18_share_parking_in_large_sites"] = np.nan
    # region as a numeric code for single tests (one dummy per region would be more parameters than this test allows)
    d["V15_region"] = pd.to_numeric(d["V15_region"], errors="coerce")
    return d


def cv_single(d: pd.DataFrame, var: str) -> dict:
    x = d.dropna(subset=[var, "effect", "weight"])
    x = x[x["weight"] > 0].reset_index(drop=True)
    if len(x) < 15 or x[var].nunique() < 2:
        return {"places": len(x), "error_one_average": np.nan, "error_with_variable": np.nan, "gain": np.nan, "slope": np.nan, "slope_p05": np.nan, "slope_p95": np.nan}
    rng = np.random.default_rng(SEED)
    e0, e1 = [], []
    X = np.column_stack([np.ones(len(x)), x[var].values.astype(float)])
    y, w = x["effect"].values.astype(float), x["weight"].values.astype(float)
    for _ in range(REPEATS):
        perm = rng.permutation(len(x))
        for f in range(FOLDS):
            te = perm[f::FOLDS]
            tr = np.setdiff1d(np.arange(len(x)), te)
            m0 = np.average(y[tr], weights=w[tr])
            b = cmp.wls(X[tr], y[tr], w[tr])
            e0.append((np.abs(m0 - y[te]) * w[te]).sum() / w[te].sum())
            e1.append((np.abs(X[te] @ b - y[te]) * w[te]).sum() / w[te].sum())
    b = cmp.wls(X, y, w)
    sl = []
    for _ in range(DRAWS):
        i = rng.integers(0, len(x), len(x))
        if np.ptp(X[i, 1]) == 0:
            continue
        sl.append(cmp.wls(X[i], y[i], w[i])[1])
    return {"places": len(x), "error_one_average": float(np.mean(e0)), "error_with_variable": float(np.mean(e1)),
            "gain": 1 - np.mean(e1) / np.mean(e0), "slope": float(b[1]),
            "slope_p05": float(np.percentile(sl, 5)), "slope_p95": float(np.percentile(sl, 95))}


def main() -> None:
    d = data()
    rows = []
    for v in SINGLE:
        r = cv_single(d, v)
        r["variable"] = v
        r["passes"] = bool(r["places"] >= 15 and r["gain"] >= MIN_GAIN and (r["slope_p05"] > 0 or r["slope_p95"] < 0))
        rows.append(r)
    res = pd.DataFrame(rows)[["variable", "places", "error_one_average", "error_with_variable", "gain", "slope", "slope_p05", "slope_p95", "passes"]]
    res.round(4).to_csv(REFERENCE / "parking_round3_variables.csv", index=False)
    print(res.round(3).to_string(index=False))

    # California check for V4-V7 (city traits that exist there), same single-variable test
    import build_parking_round3_vars as b3
    ca = rpt.dataset_b(pd.read_csv(REFERENCE / "parking_place_traits.csv", dtype={"state": str})).dropna(subset=["effect", "acs_geoid"])
    A = b3.acs(b3.MKT / "acsdt5y2024-b25003.dat", ["B25003_E001", "B25003_E003"]).join(
        b3.acs(b3.ACS / "acsdt5y2024-b25002.dat", ["B25002_E001", "B25002_E003"])).join(
        b3.acs(b3.ACS / "acsdt5y2024-b25034.dat", ["B25034_E001", "B25034_E009", "B25034_E010", "B25034_E011"])).join(
        b3.acs(b3.ACS / "acsdt5y2024-b25024.dat", ["B25024_E001", "B25024_E006", "B25024_E007", "B25024_E008", "B25024_E009"]))
    A["V4_renter_share"] = A["B25003_E003"] / A["B25003_E001"]
    A["V5_vacancy_rate"] = A["B25002_E003"] / A["B25002_E001"]
    A["V6_share_built_before_1960"] = A[["B25034_E009", "B25034_E010", "B25034_E011"]].sum(axis=1) / A["B25034_E001"]
    A["V7_share_homes_5plus"] = A[["B25024_E006", "B25024_E007", "B25024_E008", "B25024_E009"]].sum(axis=1) / A["B25024_E001"]
    ca = ca.merge(A[["V4_renter_share", "V5_vacancy_rate", "V6_share_built_before_1960", "V7_share_homes_5plus"]], left_on="acs_geoid", right_index=True, how="left")
    ca["weight"] = ca["weight"].astype(float)
    carows = []
    for v in ["V4_renter_share", "V5_vacancy_rate", "V6_share_built_before_1960", "V7_share_homes_5plus"]:
        r = cv_single(ca, v)
        r["variable"] = v
        carows.append(r)
    cares = pd.DataFrame(carows)
    cares.round(4).to_csv(REFERENCE / "parking_round3_variables_california.csv", index=False)
    print(cares.round(3).to_string(index=False))

    # all variables together, with the expanded plan's tools (missing values imputed from the training fold)
    feats = rpe.FEATURES_US + [v for v in SINGLE if v not in rpe.FEATURES_US]
    feats = [f for f in feats if f in d.columns and d[f].notna().sum() >= 15]
    sc = rpe.cv_score(d.reset_index(drop=True), feats)
    tools = pd.DataFrame([{"tool": t, "error": e, "gain": 1 - e / sc["one average"]} for t, e in sc.items()])
    tools["passes"] = (tools["gain"] >= MIN_GAIN) & (tools["tool"] != "one average")
    tools["features"] = len(feats)
    tools.round(4).to_csv(REFERENCE / "parking_round3_tools.csv", index=False)
    print(tools.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
