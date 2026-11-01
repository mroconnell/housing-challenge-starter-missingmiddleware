"""Station-area model, step D (docs/tod/STATION_AREA_PLAN.md, LOCKED).

Stage 0 (no model): each case's effect per band = change in the reform stops' rate minus change in the comparison
stops' rate, in new homes per 1,000 existing homes per year; raw and scaled to full coverage. New York's and
Philadelphia's many rezonings are averaged into one case each (owner, 15:57). Pooled effect per band = average over
cases (each case once), with the range from leaving one case out. Scores: each left-out case predicted by the others'
average vs by zero (the two simple rules).

    uv run --all-extras python scripts/run_tod_station_model.py
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

OUT = ROOT / "data" / "processed" / "tod_station_area"
BANDS = ["0-1/4", "1/4-1/2", "1/2-1"]


def windows(case: str) -> tuple[int, int]:
    import build_tod_station_lot_table as B
    cfg = {**B.CASES, **{k: v for k, (_, v) in B.adapter_cases().items()}}[case]
    return cfg["before"][1] - cfg["before"][0] + 1, cfg["after"][1] - cfg["after"][0] + 1


def city_of(case: str) -> str:
    return "New York" if case.startswith("nyc_") else "Philadelphia" if case.startswith("phl_") else case


def case_effects() -> pd.DataFrame:
    rows = []
    for f in sorted(OUT.glob("lots_*.parquet")):
        case = f.stem.removeprefix("lots_")
        D = pd.read_parquet(f, columns=["group", "band", "homes_existing", "homes_before_win", "homes_after_win", "in_reform_area", "implausible"])
        D = D[~D.implausible.fillna(False)]
        yb, ya = windows(case)
        g = D.groupby(["group", "band"]).agg(e=("homes_existing", "sum"), b=("homes_before_win", "sum"), a=("homes_after_win", "sum"),
                                             cov=("in_reform_area", "mean"), lots=("band", "size"))
        for band in BANDS:
            try:
                r, c = g.loc[("reform", band)], g.loc[("comparison", band)]
            except KeyError:
                continue
            if r.e <= 0 or c.e <= 0:
                continue
            dr = 1000 * (r.a / ya - r.b / yb) / r.e
            dc = 1000 * (c.a / ya - c.b / yb) / c.e
            rows.append({"case": case, "city": city_of(case), "band": band, "reform_change": dr, "comparison_change": dc,
                         "effect_raw": dr - dc, "coverage": r["cov"], "comparison_coverage": c["cov"],
                         "reform_homes": r.e, "comparison_homes": c.e, "reform_new": r.a + r.b, "comparison_new": c.a + c.b})
    E = pd.DataFrame(rows)
    E["effect_scaled"] = E.effect_raw / (E.coverage - E.comparison_coverage).where(lambda x: x >= 0.2)   # scaling below 20% coverage multiplies noise
    return E


def city_level(E: pd.DataFrame) -> pd.DataFrame:
    """One row per city and band: New York and Philadelphia averaged over their rezonings."""
    num = ["reform_change", "comparison_change", "effect_raw", "effect_scaled", "coverage"]
    return E.groupby(["city", "band"])[num].mean().reset_index()


def pooled(C: pd.DataFrame, col: str) -> pd.DataFrame:
    out = []
    for band, g in C.groupby("band"):
        v = g.set_index("city")[col].dropna()
        if len(v) < 2:
            continue
        loo = pd.Series({k: v.drop(k).mean() for k in v.index})
        out.append({"band": band, "cities": len(v), "average": v.mean(), "loo_low": loo.min(), "loo_high": loo.max(),
                    "median": v.median(), "mae_others_average": (v - loo).abs().mean(), "mae_zero": v.abs().mean()})
    return pd.DataFrame(out)


def main() -> None:
    E = case_effects()
    C = city_level(E)
    pd.set_option("display.width", 200)
    print(C.round(2).to_string(index=False))
    for col in ("effect_raw", "effect_scaled"):
        print(f"\n{col}:")
        print(pooled(C, col).round(2).to_string(index=False))
    C.round(4).to_csv(REFERENCE / "tod_station_area_effects_by_city.csv", index=False)


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------- dates (owner, 17:33: permit year, completion
# year, and a third column: permit year, actual where known, else estimated from completion minus the typical gap)
# Gap measured in LA, where 8,091 lots have both an LADBS new-building permit and a county year built 1 year before to
# 6 years after it: median gap 1 year for 1, 2-4 and 5-49 homes, 2 years for 50+ homes (means 1.04, 0.70, 1.53, 1.91).
# The gap is a property of each county's records: San Diego (860 lots with city permit and county effective year):
# medians 1, 1, 2, 2 (means 1.01, 1.27, 1.90, 2.00); Denver (6,690 matched): 0 in every size group. Counties with no
# matched pairs use the LA/San Diego gap, flagged.
LAG_BY_SIZE = {"1": 1, "2-4": 1, "5-49": 1, "50+": 2}
LAG_BY_COUNTY = {"la": LAG_BY_SIZE, "san_diego": {"1": 1, "2-4": 1, "5-49": 2, "50+": 2}, "denver": {"1": 0, "2-4": 0, "5-49": 0, "50+": 0}}


def permit_year_est(E: pd.DataFrame, county: str = "la") -> pd.Series:
    lag = LAG_BY_COUNTY.get(county, LAG_BY_SIZE)
    size = pd.cut(E.homes, [0, 1, 4, 49, np.inf], labels=list(lag)).astype(str)
    est = E.completed_year - size.map(lag).astype(float)
    return E.permit_year.where(E.permit_year.notna(), est)
