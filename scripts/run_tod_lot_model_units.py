"""Every lot-model trait with its unit and its median in each city (docs/tod/LOT_MODEL_PLAN.md item 39.4).

    uv run --all-extras python scripts/run_tod_lot_model_units.py

Writes reference/tod_lot_model_trait_units_v37.csv. Traits are as the item 37/39 model sees them.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import REFERENCE  # noqa: E402
import run_tod_lot_model as L  # noqa: E402

UNIT = {"log_acres": "log of acres", "log_width": "log of metres", "log_dist_station": "log of (1 + metres to rail or rapid stop)",
        "level_rank_in_city": "rank within city, 0 to 1", "upzoned": "0 or 1", "rel_gain": "after ÷ before − 1 (printed-FAR cities)",
        "rel_gain_known": "0 or 1", "far_now": "floor area ratio (printed-FAR cities only)", "far_known": "0 or 1",
        "built_before": "0 or 1", "log_near_before": "log of (1 + homes per year within 150 m, before)",
        "log_rent": "log of 2024 dollars per month", "log_value": "log of 2024 dollars", "log_income": "log of 2024 dollars per year",
        "rent_to_cost": "ratio (both 2024 dollars)", "pays_room": "log homes room × rent-to-cost", "in_reform": "0 or 1",
        "rezoned_later": "0 or 1", "no_reform": "0 or 1", "log_census_homes": "log of (1 + census block homes shared by area: 2010 blocks in training and placebo cities, 2020 in the Wisconsin run)",
        "share_upzoned_half_mile": "share 0 to 1", "log_stops_1mile": "log of (1 + rail and rapid stops within 1,609 m)",
        "traits_after_reform": "0 or 1", "no_rail_rapid": "0 or 1", "far_known": "0 or 1"}


def main() -> None:
    L.FIT.update(item25=True, item32=True, item34=True, item37=True)
    D = pd.read_parquet(L.OUT / "lots_rebuilt_halfmile.parquet")
    cache = {k: L.cost_per_home(k[0], int(k[1]) - 1) for k in set(zip(D["city"], D["eff_year"]))}
    D["cost_per_home"] = [cache[(c, y)] for c, y in zip(D["city"], D["eff_year"])]
    X = L.features(D, False)
    raw = L.features.__wrapped__(D, False) if hasattr(L.features, "__wrapped__") else None
    rows = []
    for c, g in X.groupby(D["city"]):
        for t in X.columns:
            rows.append({"trait": t, "city": c, "median": g[t].median(), "p5": g[t].quantile(0.05), "p95": g[t].quantile(0.95)})
    T = pd.DataFrame(rows)
    T["unit"] = T["trait"].map(lambda t: UNIT.get(t, "0 or 1" if t.startswith("group_") else ("share 0 to 1" if "share" in t else "")))
    missing = sorted(set(T.loc[T["unit"] == "", "trait"]))
    if missing:
        print("traits without a unit:", missing, flush=True)
    miss = {"rent": D["rent"], "home_value": D["home_value"], "income": D["income"], "far_before": D["far_before"],
            "census_homes": D["census_homes"], "dist_station_m": D["dist_station_m"]}
    M = pd.DataFrame({k: v.isna().groupby(D["city"]).mean() for k, v in miss.items()}).T
    T.round(3).to_csv(REFERENCE / "tod_lot_model_trait_units_v37.csv", index=False)
    M.round(3).to_csv(REFERENCE / "tod_lot_model_trait_missing_v37.csv")
    med = T.pivot(index="trait", columns="city", values="median")
    pd.set_option("display.width", 250)
    print(med.round(2).to_string())


if __name__ == "__main__":
    main()
