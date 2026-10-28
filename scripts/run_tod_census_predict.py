"""Part A of docs/tod/CENSUS_PREDICT_PLAN.md: the 8 prediction methods on the census-measured reforms.

    uv run --all-extras python scripts/run_tod_census_predict.py

Writes reference/tod_census_predict_units.csv and reference/tod_census_predict.csv.
"""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.paths import PROCESSED, RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import traits as T  # noqa: E402
from missing_middleware.tod.control_cities import read_gazetteer  # noqa: E402
from scripts import run_tod_census_cases as R  # noqa: E402
from scripts.run_tod_census_share import slc_boundary  # noqa: E402

FOLD = ("New York", "Seattle", "Los Angeles", "Saint Paul", "Philadelphia", "Jersey City", "Phoenix", "Bellevue", "Austin",
        "Tysons", "Salt Lake City")
HOLD = ("Chicago", "Milpitas")
CITY_GEOID = {"New York": "3651000", "Seattle": "5363000", "Los Angeles": "0644000", "Saint Paul": "2758000",
              "Philadelphia": "4260000", "Chicago": "1714000", "Jersey City": "3436000", "Milpitas": "0647766",
              "Phoenix": "0455000", "Bellevue": "5305210", "Austin": "4805000", "Salt Lake City": "4967000"}
FAIRFAX_HOMES = 407998
INVENTORY = {"New York": "nyc_bloomberg_rezonings_2003_2013", "Seattle": "seattle_nbh_othello_2012", "Los Angeles": "la_warner_center_2013",
             "Saint Paul": "stpaul_green_line_2011", "Philadelphia": "philadelphia_2012_code", "Chicago": "chicago_tod_2013_2015",
             "Jersey City": "jersey_city_journal_square_2010", "Milpitas": "milpitas_tasp_2008",
             "Phoenix": "phoenix_walkable_urban_code_2015", "Bellevue": "bellevue_belred_2009", "Austin": "austin_tod_2005",
             "Tysons": "tysons_2010", "Salt Lake City": "salt_lake_city_tsa_2010"}
# Rail opened after 2009 inside or at the area (plan variable 6; corrected list in plan section 6).
NEW_RAIL = {"salt_lake_city_tsa_2010", "milpitas_tasp_2008", "bellevue_belred_2009", "tysons_2010", "austin_tod_station_plans",
            "stpaul_green_line_2011", "seattle_roosevelt_2012"}
TOOLS = ("wls", "lasso", "elastic_net", "tree", "forest", "boosting", "causal_forest", "knn")
LABELS = {"baseline": "0. plain average", "wls": "1. weighted regression", "lasso": "2. LASSO", "elastic_net": "3. elastic net",
          "tree": "4. regression tree (depth 2)", "forest": "5. random forest", "boosting": "6. gradient boosting",
          "causal_forest": "7. honest causal forest", "knn": "8. nearest neighbours (k = 5)",
          "multilevel": "9. multilevel model (uncertainty only)", "density_only": "pre-reform density alone (weighted regression)"}


def measure(st: str, treated, comp) -> dict:
    p10, p20 = R.block_points(st, 2010), R.block_points(st, 2020)
    t10, t20, c10, c20 = p10[R.within(p10, treated)], p20[R.within(p20, treated)], p10[R.within(p10, comp)], p20[R.within(p20, comp)]
    ta = (t10["land"].sum() + t20["land"].sum()) / 2 / R.ACRE
    ca = (c10["land"].sum() + c20["land"].sum()) / 2 / R.ACRE
    if ta <= 0 or ca <= 0:
        return {}
    dt = (t20["homes"].sum() - t10["homes"].sum()) / ta / 10
    dc = (c20["homes"].sum() - c10["homes"].sum()) / ca / 10
    return {"weight": ta, "comparison_acres": ca, "d_treat": dt, "d_comp": dc, "effect": dt - dc,
            "pre_density": t10["homes"].sum() / ta, "comp_density": c10["homes"].sum() / ca}


def units() -> pd.DataFrame:
    rows = []
    city_of = {"jersey_city_journal_square_2010": "Jersey City", "milpitas_tasp_2008": "Milpitas", "phoenix_wu_2015_2016": "Phoenix",
               "bellevue_belred_2009": "Bellevue", "austin_tod_station_plans": "Austin", "tysons_2010": "Tysons"}
    geoms = {c: R.boundary(c) for c in R.NEW_CASES}
    geoms["salt_lake_city_tsa_2010"] = slc_boundary()
    every = unary_union([g[1] for g in geoms.values()])
    for case, (treated, exclude) in geoms.items():
        st = "49" if case == "salt_lake_city_tsa_2010" else R.NEW_CASES[case][0]
        ring = treated.buffer(R.HALF).difference(every).difference(exclude)
        m = measure(st, treated, ring)
        if m:
            rows.append({"case": case, "city": city_of.get(case, "Salt Lake City"), **m})
    cases = {"stpaul_green_line_2011": ("27", "Saint Paul"), "seattle_nbh_othello_2012": ("53", "Seattle"),
             "seattle_mount_baker_2014": ("53", "Seattle"), "la_warner_center_2013": ("06", "Los Angeles"),
             "la_cornfield_arroyo_seco_2013": ("06", "Los Angeles"), "chicago_tod_2013_2015": ("17", "Chicago"),
             "philadelphia_2012_remapping": ("42", "Philadelphia")}
    for case, (st, city) in cases.items():
        mem = pickle.loads((PROCESSED / "tod_net_effect" / f"areas_{case}.pkl").read_bytes())
        to = lambda g, crs: gpd.GeoSeries([g], crs=crs).to_crs(R.CRS).iloc[0]  # noqa: E731
        treated = unary_union([to(m["treated_union"], m["crs"]) for m in mem])
        upz = unary_union([to(m["upzoned_union"], m["crs"]) for m in mem])
        m = measure(st, treated, upz.buffer(R.QUARTER).difference(upz))
        if m:
            rows.append({"case": case, "city": city, **m})
    for mm in pickle.loads((PROCESSED / "tod_net_effect" / "areas_nyc_pooled_2003_2013.pkl").read_bytes()):
        if not 2008 <= mm["effective_year"] <= 2013:
            continue
        to = lambda g: gpd.GeoSeries([g], crs=mm["crs"]).to_crs(R.CRS).iloc[0]  # noqa: E731
        upz = to(mm["upzoned_union"])
        m = measure("36", to(mm["treated_union"]), upz.buffer(R.QUARTER).difference(upz))
        if m:
            rows.append({"case": f"nyc_{mm.get('id')}", "city": "New York", **m})
    z = gpd.read_file(RAW / "tod_cases" / "seattle" / "zoning_current.geojson").to_crs(R.CRS)
    rv = z[z["ZONINGHISTORY"].astype(str).str.contains("ORD123816")].geometry.make_valid().union_all()
    m = measure("53", rv, rv.buffer(R.HALF).difference(rv))
    rows.append({"case": "seattle_roosevelt_2012", "city": "Seattle", **m})
    d = pd.DataFrame(rows)
    gaz = read_gazetteer(RAW / "tod_control_cities" / "Gaz_places_national.zip").set_index("geoid")["hu10"]
    inv = pd.read_csv(REFERENCE / "tod_cases.csv").set_index("case_id")
    d["city_homes"] = [FAIRFAX_HOMES if c == "Tysons" else float(gaz[CITY_GEOID[c]]) for c in d["city"]]
    d["rent"] = [pd.to_numeric(inv.loc[INVENTORY[c], "median_gross_rent_usd_per_month"], errors="coerce") for c in d["city"]]
    d["home_value"] = [pd.to_numeric(inv.loc[INVENTORY[c], "median_home_value_usd"], errors="coerce") for c in d["city"]]
    d["x_log_pre_density"] = np.log(d["pre_density"] + 1)
    d["x_log_acres"] = np.log(d["weight"])
    d["x_log_comp_density"] = np.log(d["comp_density"] + 1)
    d["x_rent"] = d["rent"]
    d["x_home_value"] = np.log(d["home_value"])
    d["x_log_city_homes"] = np.log(d["city_homes"])
    d["x_new_rail"] = d["case"].isin(NEW_RAIL).astype(float)
    return d


def role(c: str) -> str:
    return "fold" if c in FOLD else ("always held out" if c in HOLD else "context")


def predict(tool: str, train: pd.DataFrame, test: pd.DataFrame, cols: list[str]) -> np.ndarray:
    y, w = train["effect"].values.astype(float), train["weight"].values.astype(float)
    if tool == "baseline":
        return T.fit_predict(train, test, [])
    if tool == "tree":
        return T.predict_tree(T.fit_tree(train, cols), test)
    if tool == "wls":
        return T.fit_predict(train, test, cols)
    Xtr, Xte, _ = T.weighted_fill(train, test, cols)
    if tool in ("lasso", "elastic_net"):
        from sklearn.linear_model import ElasticNetCV, LassoCV
        Ztr, Zte = T.standardize(Xtr, Xte)
        g = train["city"].values
        splits = [(np.where(g != c)[0], np.where(g == c)[0]) for c in pd.unique(g)]
        m = LassoCV(alphas=50, cv=splits, max_iter=200000) if tool == "lasso" else \
            ElasticNetCV(l1_ratio=[0.1, 0.3, 0.5, 0.7, 0.9, 0.95, 0.99], alphas=50, cv=splits, max_iter=200000)
        m.fit(Ztr, y, sample_weight=w)
        return m.predict(Zte)
    if tool == "forest":
        from sklearn.ensemble import RandomForestRegressor
        m = RandomForestRegressor(n_estimators=500, min_samples_leaf=5, random_state=T.TOOL_SEED, n_jobs=-1)
        m.fit(Xtr, y, sample_weight=w)
        return m.predict(Xte)
    if tool == "boosting":
        from sklearn.ensemble import GradientBoostingRegressor
        m = GradientBoostingRegressor(max_depth=2, learning_rate=0.05, n_estimators=1000, validation_fraction=0.2,
                                      n_iter_no_change=20, random_state=T.TOOL_SEED)
        m.fit(Xtr, y, sample_weight=w)
        return m.predict(Xte)
    if tool == "knn":
        Ztr, Zte = T.standardize(Xtr, Xte)
        return T.knn_predict(Ztr, y, w, Zte)
    if tool == "causal_forest":
        return T.causal_forest_predict(Xtr, train["d_treat"].values.astype(float), w, train["d_comp"].values.astype(float),
                                       train["comparison_acres"].values.astype(float), Xte)
    raise ValueError(tool)


def errors(d: pd.DataFrame, tool: str, cols: list[str]) -> pd.DataFrame:
    rows = []
    for c in FOLD + HOLD:
        test = d[d["city"] == c]
        train = d[d["city"].isin([f for f in FOLD if f != c])]
        if test.empty:
            continue
        pm, pb = predict(tool, train, test, cols), T.fit_predict(train, test, [])
        ob, ww = test["effect"].values.astype(float), test["weight"].values.astype(float)
        rows.append({"city": c, "role": role(c), "error_baseline": T.weighted_mae(pb, ob, ww), "error_model": T.weighted_mae(pm, ob, ww),
                     "measured_mean": float(np.sum(ob * ww) / ww.sum()), "predicted_mean_model": float(np.sum(pm * ww) / ww.sum())})
    return pd.DataFrame(rows)


def judge(e: pd.DataFrame) -> dict:
    import math
    f, h = e[e["role"] == "fold"], e[e["role"] == "always held out"].set_index("city")
    better = int((f["error_model"] < f["error_baseline"] - 1e-12).sum())
    need = math.ceil(2 * len(FOLD) / 3)
    held = {c: bool(c in h.index and h.loc[c, "error_model"] < h.loc[c, "error_baseline"] - 1e-12) for c in HOLD}
    ok = better >= need and f["error_model"].mean() < f["error_baseline"].mean() - 1e-12 and all(held.values())
    return {"verdict": "pass" if ok else "fail", "fold_cities_better": better, "fold_cities_needed": need,
            "mean_error_baseline": f["error_baseline"].mean(), "mean_error_model": f["error_model"].mean(),
            **{f"beats_baseline_{c.lower()}": v for c, v in held.items()}}


def main() -> None:
    d = units()
    assert not T.check_private(d)
    d.round(5).to_csv(REFERENCE / "tod_census_predict_units.csv", index=False)
    cols = [c for c in d.columns if c.startswith("x_")]
    print(d[["case", "city", "weight", "effect", "pre_density"]].round(3).to_string())
    rows = []
    for tool, cc, label in [("baseline", [], LABELS["baseline"])] + [(t, cols, LABELS[t]) for t in TOOLS] + \
                           [("wls", ["x_log_pre_density"], LABELS["density_only"])]:
        e = errors(d, tool, cc)
        j = judge(e) if tool != "baseline" else {"verdict": "baseline"}
        row = {"method": label, **j}
        for r in e.itertuples():
            row[f"err_base_{r.city}"], row[f"err_model_{r.city}"] = r.error_baseline, r.error_model
        rows.append(row)
        print(label, j.get("verdict"), j.get("fold_cities_better"), flush=True)
    # 9. multilevel: uncertainty for a new city
    full = T.random_intercept_fit(d[d["city"].isin(FOLD)])
    lo, hi = T.new_city_interval(full)
    rows.append({"method": LABELS["multilevel"], "verdict": "uncertainty only",
                 "detail": f"overall mean {full['mu']:+.3f} homes per acre per year; 90% interval for a new city {lo:+.3f} to {hi:+.3f}"})
    out = pd.DataFrame(rows)
    out.round(4).to_csv(REFERENCE / "tod_census_predict.csv", index=False)
    pd.set_option("display.width", 250)
    print(out[["method", "verdict", "fold_cities_better", "mean_error_baseline", "mean_error_model", "beats_baseline_chicago",
               "beats_baseline_milpitas"]].round(3).to_string())
    print(rows[-1]["detail"])


if __name__ == "__main__":
    main()
