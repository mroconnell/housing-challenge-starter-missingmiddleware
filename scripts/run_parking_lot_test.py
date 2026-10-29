"""Parking lot-level test (docs/parking/LOT_TEST_PLAN.md), on TOD's lot table.

    uv run --all-extras python scripts/run_parking_lot_test.py

Input: data/processed/tod_lot_model/lots.parquet (TOD), data/raw/parking_older_reforms/seattle_urban_villages.geojson.
Outputs: reference/parking_lot_effects.csv, reference/parking_lot_predict.csv (aggregates only; no lot rows).
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from missing_middleware.paths import PROCESSED, RAW, REFERENCE  # noqa: E402

SEED, DRAWS, CELL = 20261028, 2000, 500.0
NARROW_M, SMALL_ACRES, MIN_GAIN = 10.0, 0.1, 0.05


def parse(py: str) -> dict[int, float]:
    out = {}
    for part in str(py or "").split(";"):
        if ":" in part:
            y, u = part.split(":")
            out[int(float(y))] = out.get(int(float(y)), 0.0) + float(u)
    return out


def lots() -> pd.DataFrame:
    d = pd.read_parquet(PROCESSED / "tod_lot_model" / "lots.parquet")
    d["permits"] = d["permit_years"].map(parse)
    v = gpd.read_file(RAW / "parking_older_reforms" / "seattle_urban_villages.geojson").to_crs(5070)
    v = v[v["UV_TYPE"].isin(["HUV", "RUV"])]
    s = d[d["city"] == "Seattle"]
    g = gpd.GeoDataFrame(s[[]], geometry=gpd.points_from_xy(s["x5070"], s["y5070"]), crs=5070)
    inside = gpd.sjoin(g, v[["geometry"]], predicate="within").index.unique()
    d["parking"] = 0.0
    d.loc[inside, "parking"] = 1.0
    chi = d["city"] == "Chicago"
    d.loc[chi & (d["dist_station_m"] <= 402.336), "parking"] = 1.0
    d["cell"] = d["city"] + ":" + (d["x5070"] // CELL).astype(int).astype(str) + "_" + (d["y5070"] // CELL).astype(int).astype(str)
    return d


def rates(d: pd.DataFrame, years: list[int]) -> tuple[float, float]:
    """(built lots, units) per 1,000 lots per year."""
    if not len(d) or not years:
        return np.nan, np.nan
    b = d["permits"].map(lambda p: sum(1 for y in years if y in p)).sum()
    u = d["permits"].map(lambda p: sum(p.get(y, 0.0) for y in years)).sum()
    return b / len(d) / len(years) * 1000, u / len(d) / len(years) * 1000


def effect_table(sub: pd.DataFrame, pre, post) -> dict:
    t, c = sub[sub["parking"] == 1], sub[sub["parking"] == 0]
    (tb0, tu0), (tb1, tu1) = rates(t, pre), rates(t, post)
    (cb0, cu0), (cb1, cu1) = rates(c, pre), rates(c, post)
    return dict(reform_lots=len(t), comparison_lots=len(c), built_effect=(tb1 - tb0) - (cb1 - cb0), units_effect=(tu1 - tu0) - (cu1 - cu0),
                reform_built_before=tb0, reform_built_after=tb1, comp_built_before=cb0, comp_built_after=cb1,
                reform_units_before=tu0, reform_units_after=tu1, comp_units_before=cu0, comp_units_after=cu1)


def boot(sub, pre, post, rng):
    cells = sub["cell"].unique()
    groups = {c: g for c, g in sub.groupby("cell")}
    out = []
    for _ in range(DRAWS):
        pick = rng.choice(cells, len(cells))
        e = effect_table(pd.concat([groups[c] for c in pick]), pre, post)
        out.append((e["built_effect"], e["units_effect"]))
    a = np.array(out)
    return np.nanpercentile(a[:, 0], [5, 95]), np.nanpercentile(a[:, 1], [5, 95])


def windows(sub: pd.DataFrame, city: str) -> tuple[list[int], list[int]]:
    if city == "Chicago":
        return list(range(2009, 2013)), list(range(2016, 2021))
    lo, hi = int(sub["window_first"].min()), int(sub["window_last"].max())
    return list(range(lo, 2012)), list(range(2013, hi + 1))


def main() -> None:
    d = lots()
    d = d[d["treated"] == 0]  # leave out TOD-upzoned lots
    rng = np.random.default_rng(SEED)
    rows = []
    for city in ("Seattle", "Chicago"):
        base = d[d["city"] == city]
        pre, post = windows(base, city)
        for lab, m in (("all lots", np.ones(len(base), bool)), (f"narrow (under {NARROW_M:.0f} m)", base["width_m"] < NARROW_M),
                       (f"wider ({NARROW_M:.0f} m or more)", base["width_m"] >= NARROW_M),
                       (f"small (under {SMALL_ACRES} acre)", base["acres"] < SMALL_ACRES),
                       (f"larger ({SMALL_ACRES} acre or more)", base["acres"] >= SMALL_ACRES)):
            sub = base[np.asarray(m)]
            e = effect_table(sub, pre, post)
            (b5, b95), (u5, u95) = boot(sub, pre, post, rng)
            rows.append(dict(city=city, lots=lab, before=f"{pre[0]}-{pre[-1]}", after=f"{post[0]}-{post[-1]}", **e,
                             built_p05=b5, built_p95=b95, units_p05=u5, units_p95=u95))
    eff = pd.DataFrame(rows)
    allrows = eff[eff["lots"] == "all lots"]
    w = allrows["reform_lots"] + allrows["comparison_lots"]
    pooled = dict(city="Pooled (weighted by lots)", lots="all lots", built_effect=np.average(allrows["built_effect"], weights=w),
                  units_effect=np.average(allrows["units_effect"], weights=w))
    eff = pd.concat([eff, pd.DataFrame([pooled])], ignore_index=True)
    eff.round(4).to_csv(REFERENCE / "parking_lot_effects.csv", index=False)

    # prediction on unseen cities
    from sklearn.ensemble import HistGradientBoostingClassifier
    # far_before has different units by city (feet, ranks, stories, 0/1): use its rank within each city (audit 2e, 2026-10-29)
    d["far_rank_in_city"] = d.groupby("city")["far_before"].rank(pct=True).fillna(0.5)
    feats = ["acres", "width_m", "far_rank_in_city", "dist_station_m", "homes_on_lot", "built_before", "rent", "home_value", "income"]
    X = d[feats].copy()
    X["use"] = d["use"].astype("category").cat.codes
    for c in d["city"].unique():
        X[f"city_{c}"] = (d["city"] == c).astype(float)
    y = d["builds_after"].values
    pr = []
    for hold in ("Seattle", "Chicago"):
        te = (d["city"] == hold).values
        res = {}
        for with_flag in (False, True):
            Xf = X.copy()
            if with_flag:
                Xf["parking"] = d["parking"].values
            Xf = Xf.drop(columns=[f"city_{hold}"])
            m = HistGradientBoostingClassifier(max_depth=4, learning_rate=0.05, max_iter=300, random_state=SEED).fit(Xf[~te], y[~te])
            p = m.predict_proba(Xf[te])[:, 1]
            reform = d.loc[te, "parking"].values == 1
            res[with_flag] = dict(brier=float(np.mean((p - y[te]) ** 2)),
                                  count_error=float(abs(p[reform].sum() - y[te][reform].sum()) / max(y[te][reform].sum(), 1)))
        pr.append(dict(held_out=hold, brier_without=res[False]["brier"], brier_with=res[True]["brier"],
                       brier_gain=1 - res[True]["brier"] / res[False]["brier"],
                       count_error_without=res[False]["count_error"], count_error_with=res[True]["count_error"],
                       count_gain=1 - res[True]["count_error"] / res[False]["count_error"] if res[False]["count_error"] else np.nan,
                       reform_lots_built=int(y[te][d.loc[te, "parking"].values == 1].sum())))
    pr = pd.DataFrame(pr)
    pr["passes"] = (pr["brier_gain"] >= MIN_GAIN) & (pr["count_gain"] >= MIN_GAIN)
    pr.round(4).to_csv(REFERENCE / "parking_lot_predict.csv", index=False)
    pd.set_option("display.width", 250)
    print(eff[["city", "lots", "before", "after", "reform_lots", "comparison_lots", "built_effect", "built_p05", "built_p95",
               "units_effect", "units_p05", "units_p95"]].round(2).to_string(index=False))
    print(pr.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
