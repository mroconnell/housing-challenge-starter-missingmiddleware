"""Run the pre-registered parking trait test (docs/parking/TRAITS_PLAN.md).

    uv run python scripts/run_parking_traits.py

Dataset A: reference/parking_comparison_effects.csv (US repeal places, main + with conditions).
Dataset B: reference/tod_ab2097_by_jurisdiction.csv (California AB 2097 group P, near transit).
Traits: reference/parking_place_traits.csv.
Outputs: reference/parking_traits_results.csv, reference/parking_traits_dataset_{a,b}.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

TRAITS = ["T1_home_value_rel", "T2_income_rel", "T3_log_density", "T4_single_family_share", "T5_log_land_sqmi", "T6_value_to_income"]
LABELS = {"T1_home_value_rel": "Median home value (relative to state)", "T2_income_rel": "Median household income (relative to state)",
          "T3_log_density": "Homes per square mile (log)", "T4_single_family_share": "Share of homes that are single-family detached",
          "T5_log_land_sqmi": "Land area (log square miles)", "T6_value_to_income": "Home value relative to income"}
SEED, DRAWS, MIN_GAIN = 20261027, 2000, 0.05


def dataset_a(traits: pd.DataFrame) -> pd.DataFrame:
    import run_parking_comparison as rpc
    p = cmp.panel(rpc.read_bps_us())
    geo = p.drop_duplicates("key", keep="last").set_index("key")["acs_geoid"]
    e = pd.read_csv(REFERENCE / "parking_comparison_effects.csv")
    e = e[(e["status"] == "included") & (e["outcome"] == "all")].copy()
    e["acs_geoid"] = e["key"].map(geo)
    return e[["place", "state", "arm", "homes", "effect", "acs_geoid"]].merge(traits, on="acs_geoid", how="left", suffixes=("", "_t"))


def dataset_b(traits: pd.DataFrame) -> pd.DataFrame:
    j = pd.read_csv(REFERENCE / "tod_ab2097_by_jurisdiction.csv")
    j = j[j["near_permits_both_periods"].astype(bool) & ~j["jurisdiction"].str.contains("COUNTY")].copy()
    ca = traits[(traits["state"].astype(str).str.zfill(2) == "06") & traits["acs_geoid"].str.startswith("160|")].copy()
    ca["key"] = ca["name"].str.replace(r" (city|town)$", "", regex=True).str.upper()
    ca = ca.drop_duplicates("key")
    out = j.merge(ca, left_on="jurisdiction", right_on="key", how="left")
    out = out.rename(columns={"did_per_1000_homes_per_year": "effect", "homes_near_transit_2020": "weight"})
    return out


def loo(x: np.ndarray, y: np.ndarray, w: np.ndarray, use_trait: bool) -> float:
    X = np.column_stack([np.ones(len(y)), x]) if use_trait else np.ones((len(y), 1))
    err = []
    for i in range(len(y)):
        m = np.arange(len(y)) != i
        b = cmp.wls(X[m], y[m], w[m])
        err.append(abs(X[i] @ b - y[i]))
    return float(np.sum(np.array(err) * w) / w.sum())


def test(d: pd.DataFrame, trait: str, weight: str, label: str) -> dict:
    d = d.dropna(subset=["effect", trait, weight])
    d = d[d[weight] > 0]
    x, y, w = d[trait].values.astype(float), d["effect"].values.astype(float), d[weight].values.astype(float)
    base, with_t = loo(x, y, w, False), loo(x, y, w, True)
    b = cmp.wls(np.column_stack([np.ones(len(y)), x]), y, w)
    rng = np.random.default_rng(SEED)
    slopes = []
    for _ in range(DRAWS):
        i = rng.integers(0, len(y), len(y))
        if np.ptp(x[i]) == 0:
            continue
        slopes.append(cmp.wls(np.column_stack([np.ones(len(i)), x[i]]), y[i], w[i])[1])
    return {"dataset": label, "trait": trait, "label": LABELS[trait], "places": len(d), "error_one_average": base,
            "error_with_trait": with_t, "gain": 1 - with_t / base, "slope": b[1],
            "slope_p05": float(np.percentile(slopes, 5)), "slope_p95": float(np.percentile(slopes, 95))}


def main() -> None:
    traits = pd.read_csv(REFERENCE / "parking_place_traits.csv", dtype={"state": str})
    a, b = dataset_a(traits), dataset_b(traits)
    a.to_csv(REFERENCE / "parking_traits_dataset_a.csv", index=False)
    b.to_csv(REFERENCE / "parking_traits_dataset_b.csv", index=False)
    print("dataset A places with traits:", a.dropna(subset=["T1_home_value_rel"]).shape[0], "of", len(a))
    print("dataset B matched:", b["acs_geoid"].notna().sum(), "of", len(b), "; unmatched:", sorted(b.loc[b["acs_geoid"].isna(), "jurisdiction"]))
    rows = [test(a, t, "homes", "A: US repeal places") for t in TRAITS] + [test(b, t, "weight", "B: California AB 2097, near transit") for t in TRAITS]
    r = pd.DataFrame(rows)
    piv = r.pivot(index="trait", columns="dataset", values=["gain", "slope"])
    passes = {}
    for t in TRAITS:
        ga, gb = piv.loc[t, ("gain", "A: US repeal places")], piv.loc[t, ("gain", "B: California AB 2097, near transit")]
        sa, sb = piv.loc[t, ("slope", "A: US repeal places")], piv.loc[t, ("slope", "B: California AB 2097, near transit")]
        passes[t] = bool(ga >= MIN_GAIN and gb >= MIN_GAIN and np.sign(sa) == np.sign(sb))
    r["passes"] = r["trait"].map(passes)
    r.round(4).to_csv(REFERENCE / "parking_traits_results.csv", index=False)
    print(r[["dataset", "label", "places", "error_one_average", "error_with_trait", "gain", "slope", "slope_p05", "slope_p95", "passes"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
