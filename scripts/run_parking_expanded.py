"""Expanded parking comparison and prediction tools (docs/parking/EXPANDED_PLAN.md).

    uv run python scripts/run_parking_expanded.py

Inputs: reference/parking_repeal_checks.csv (first 46) and parking_repeal_checks_expanded.csv (131 more),
the Census permit and ACS inputs used by scripts/run_parking_comparison.py, reference/parking_place_traits.csv,
reference/tod_ab2097_by_jurisdiction.csv and tod_ab2097_results.csv (California, from the TOD work).
Outputs: reference/parking_expanded_{effects,estimates,tools}.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_comparison as rpc  # noqa: E402
import run_parking_traits as rpt  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

SEED = 20261027
FEATURES_US = ["T1_home_value_rel", "T2_income_rel", "T3_log_density", "T4_single_family_share", "T5_log_land_sqmi",
               "T6_value_to_income", "log_pop", "metro", "rel_rent", "rate_before"]
FEATURES_SHARED = ["T1_home_value_rel", "T2_income_rel", "T3_log_density", "T4_single_family_share", "T5_log_land_sqmi",
                   "T6_value_to_income", "log_homes"]


def year_of(v) -> int | None:
    s = str(v or "").strip()
    return int(s[:4]) if s[:4].isdigit() else None


def all_checks() -> pd.DataFrame:
    a = pd.read_csv(REFERENCE / "parking_repeal_checks.csv", dtype=str)
    a["source"] = "first 46"
    b = pd.read_csv(REFERENCE / "parking_repeal_checks_expanded.csv", dtype=str)
    b["source"] = "expanded"
    c = pd.concat([a, b], ignore_index=True)
    ev = []
    for r in c.itertuples():
        e = getattr(r, "event_year", None)
        y = year_of(e) if isinstance(e, str) and e and e != "nan" else (year_of(r.effective_date) or year_of(r.adoption_date))
        ev.append(y)
    c["event_year"] = ev
    rf = [year_of(x) for x in c.get("repealed_from", pd.Series([None] * len(c)))]
    old_rf = [year_of(x) for x in c.get("repealed_from_year", pd.Series([None] * len(c)))]
    c["repealed_year"] = [x or y for x, y in zip(rf, old_rf)]
    c["event_year"] = pd.to_numeric(c["event_year"], errors="coerce")
    c["repealed_year"] = pd.to_numeric(c["repealed_year"], errors="coerce")
    c["no_event"] = c.get("no_event", "False").fillna("False").astype(str).str.lower().eq("true")
    z = c["simultaneous_zoning_changes"].fillna("").str.strip().str.lower()
    c["simultaneous_rewrite"] = ~(z.eq("") | z.str.startswith(("none", "unknown", "no ")))
    return c


def us_effects() -> tuple[pd.DataFrame, pd.DataFrame]:
    p = cmp.panel(rpc.read_bps_us())
    homes_geo = rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001")
    rent_geo = rpc.acs_table(RAW / "census_acs5_2024_tbsf_market" / "acsdt5y2024-b25064.dat", "B25064_E001")
    pop_geo = rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001")
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(homes_geo)
    homes = homes[homes > 0]
    popn = geo["acs_geoid"].map(pop_geo)
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    reformed = tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
    excluded = set()
    for r in reformed.drop_duplicates("prn_key").itertuples():
        k = cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population)
        if k:
            excluded.add(k)
    checks = all_checks()
    cases = pd.read_csv(REFERENCE / "parking_reform_cases.csv").drop_duplicates("prn_key").set_index("prn_key")
    rows = []
    for c in checks.itertuples():
        pc = cases.loc[c.prn_key] if c.prn_key in cases.index else None
        k = cmp.match_place(p, rpc.STATE_FIPS.get(c.state, "??"), c.place, None if pc is None else pc["population"])
        rating = str(c.benchmark_rating_checked).strip().lower()
        reason = []
        if k is None:
            reason.append("not found in Census permit files")
        if rating not in ("at", "near"):
            reason.append(f"ordinance check: {rating}")
        if c.event_year is None or pd.isna(c.event_year):
            reason.append("no repeal date found")
        elif not (2015 <= int(c.event_year) <= 2024):
            reason.append(f"repeal year {int(c.event_year)} outside 2015-2024")
        if bool(c.no_event):
            reason.append("no minimums before either")
        if pd.notna(c.repealed_year) and pd.notna(c.event_year) and int(c.repealed_year) <= int(c.event_year) + 3:
            reason.append(f"minimums restored in {int(c.repealed_year)}")
        rows.append(dict(prn_key=c.prn_key, place=c.place, state=c.state, source=c.source, rating=rating, key=k,
                         event_year=c.event_year, simultaneous_rewrite=bool(c.simultaneous_rewrite),
                         use=not reason, note="; ".join(reason)))
    match = pd.DataFrame(rows)
    use = match[match["use"]].copy()
    use["event_year"] = use["event_year"].astype(int)
    eff = cmp.effects(p, use[["prn_key", "place", "state", "source", "rating", "key", "event_year", "simultaneous_rewrite"]],
                      excluded, homes, popn, min_post=1)
    st_rent = {k.split("|")[1]: v for k, v in rent_geo.items() if k.startswith("040|")}
    eff["acs_geoid"] = eff["key"].map(geo["acs_geoid"])
    eff["population"] = eff["key"].map(popn)
    eff["log_pop"] = cmp.log_pop(eff["population"])
    eff["rel_rent"] = [rent_geo.get(g) / st_rent.get(str(k).split("|")[0], np.nan) for g, k in zip(eff["acs_geoid"], eff["key"])]
    import geopandas as gpd
    g = gpd.read_file("zip://" + str(RAW / "census_cbsa_cb_2024" / "cb_2024_us_cbsa_20m.zip"), ignore_geometry=True)
    cbsa = g.set_index("CBSAFP")["LSAD"]
    bcb = rpc.read_bps_us().assign(key=lambda d: d["state_fips"].str.strip() + "|" + d["bps_id"].str.strip()) \
        .drop_duplicates("key", keep="last").set_index("key")["cbsa"].astype(str).str.strip()
    eff["metro"] = [1.0 if cbsa.get(bcb.get(k, ""), "") == "M1" else 0.0 for k in eff["key"]]
    traits = pd.read_csv(REFERENCE / "parking_place_traits.csv", dtype={"state": str})
    eff = eff.merge(traits.drop(columns=["state", "name"]), on="acs_geoid", how="left", suffixes=("", "_acs"))
    eff["weight"] = eff["homes"] * eff["n_post"].fillna(0)
    return match, eff


def boot_mean(y, w, draws=2000, seed=SEED):
    rng = np.random.default_rng(seed)
    out = [np.average(y[i], weights=w[i]) for i in (rng.integers(0, len(y), len(y)) for _ in range(draws))]
    return float(np.average(y, weights=w)), float(np.percentile(out, 5)), float(np.percentile(out, 95))


# ---- prediction tools ----------------------------------------------------------------------
def _impute(train: pd.DataFrame, test: pd.DataFrame, cols):
    med = train[cols].median()
    return train[cols].fillna(med).values, test[cols].fillna(med).values


def predict(tool: str, Xtr, ytr, wtr, Xte, rng):
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LassoCV
    from sklearn.preprocessing import StandardScaler
    if tool == "one average":
        return np.full(len(Xte), np.average(ytr, weights=wtr))
    sc = StandardScaler().fit(Xtr)
    A, B = sc.transform(Xtr), sc.transform(Xte)
    if tool == "weighted regression, all traits":
        X1 = np.column_stack([np.ones(len(A)), A])
        b = cmp.wls(X1, ytr, wtr)
        return np.column_stack([np.ones(len(B)), B]) @ b
    if tool == "lasso":
        m = LassoCV(cv=5, random_state=int(rng.integers(1e9)), max_iter=20000).fit(A, ytr, sample_weight=wtr)
        return m.predict(B)
    if tool == "random forest":
        m = RandomForestRegressor(n_estimators=500, min_samples_leaf=5, random_state=int(rng.integers(1e9)), n_jobs=-1)
        return m.fit(A, ytr, sample_weight=wtr).predict(B)
    if tool == "causal forest (honest)":
        idx = rng.permutation(len(A))
        h1, h2 = idx[: len(idx) // 2], idx[len(idx) // 2:]
        m = RandomForestRegressor(n_estimators=500, min_samples_leaf=5, random_state=int(rng.integers(1e9)), n_jobs=-1)
        m.fit(A[h1], ytr[h1], sample_weight=wtr[h1])
        leaves2, leavesT = m.apply(A[h2]), m.apply(B)
        mean_all = np.average(ytr[h2], weights=wtr[h2])
        preds = np.zeros(len(B))
        for t in range(leaves2.shape[1]):
            df = pd.DataFrame({"leaf": leaves2[:, t], "yw": ytr[h2] * wtr[h2], "w": wtr[h2]}).groupby("leaf").sum()
            val = (df["yw"] / df["w"]).to_dict()
            preds += np.array([val.get(lf, mean_all) for lf in leavesT[:, t]])
        return preds / leaves2.shape[1]
    raise ValueError(tool)


TOOLS = ["one average", "weighted regression, all traits", "lasso", "random forest", "causal forest (honest)"]


def cv_score(d: pd.DataFrame, cols, wcol="weight", folds=10, repeats=20, test_mask=None, extra_train=None) -> dict:
    """Weighted mean absolute error on left-out rows, by tool. test_mask limits scoring to some rows
    (the California cross-test); extra_train rows are always in training."""
    rng = np.random.default_rng(SEED)
    scores = {t: [] for t in TOOLS}
    idx_all = np.arange(len(d))
    test_idx = idx_all if test_mask is None else idx_all[test_mask]
    for _ in range(repeats):
        perm = rng.permutation(test_idx)
        for f in range(folds):
            te = perm[f::folds]
            tr = np.setdiff1d(idx_all, te)
            dtr, dte = d.iloc[tr], d.iloc[te]
            if extra_train is not None:
                dtr = pd.concat([dtr, extra_train])
            Xtr, Xte = _impute(dtr, dte, cols)
            ytr, wtr = dtr["effect"].values.astype(float), dtr[wcol].values.astype(float)
            yte, wte = dte["effect"].values.astype(float), dte[wcol].values.astype(float)
            for t in TOOLS:
                pr = predict(t, Xtr, ytr, wtr, Xte, rng)
                scores[t].append((np.abs(pr - yte) * wte).sum() / wte.sum())
    return {t: float(np.mean(v)) for t, v in scores.items()}


def main() -> None:
    match, eff = us_effects()
    # places rescued under docs/parking/SALVAGE_PLAN.md (owner approved adding them, 2026-10-28)
    sal = REFERENCE / "parking_salvage_effects.csv"
    if sal.exists():
        s = pd.read_csv(sal)
        s = s[s["status"] == "included"]
        eff = pd.concat([eff, s[[c for c in s.columns if c in eff.columns]]], ignore_index=True)
    # citywide repeals found in the partial-reforms search (owner approved adding them, 2026-10-28)
    part = REFERENCE / "parking_partial_effects.csv"
    if part.exists():
        s = pd.read_csv(part)
        s = s[(s["status"] == "included") & (s["group"] == "citywide benchmark")].assign(source="partial-reforms search", rating="at",
                                                                                          simultaneous_rewrite=False)
        eff = pd.concat([eff, s[[c for c in s.columns if c in eff.columns]]], ignore_index=True)
    match.to_csv(REFERENCE / "parking_expanded_match.csv", index=False)
    eff.to_csv(REFERENCE / "parking_expanded_effects.csv", index=False)
    inc = eff[(eff["status"] == "included") & (eff["outcome"] == "all")].dropna(subset=["effect"]).reset_index(drop=True)
    inc2 = eff[(eff["status"] == "included") & (eff["outcome"] == "2plus")].dropna(subset=["effect"]).reset_index(drop=True)
    print("places included:", len(inc), "| by source:", inc["source"].value_counts().to_dict(), "| rating:", inc["rating"].value_counts().to_dict())

    est = []

    def add(name, d):
        if len(d) < 3:
            return
        m, lo, hi = boot_mean(d["effect"].values, d["weight"].values)
        est.append(dict(case=name, places=len(d), effect=m, p05=lo, p95=hi))
    add("Expanded, all units (headline candidate)", inc)
    add("Expanded, units in buildings of 2+ units", inc2)
    add("Expanded, removed for all housing only", inc[inc["rating"] == "at"])
    add("Expanded, places with 3 after-years only", inc[inc["n_post"] == 3])
    add("Expanded, without a zoning rewrite at the same time", inc[~inc["simultaneous_rewrite"]])
    add("Expanded, without San Francisco", inc[inc["place"] != "San Francisco"])
    add("First 24 places (for reference)", inc[(inc["source"] == "first 46") & (inc["rating"] == "at") & (inc["n_post"] == 3)])
    # California pooled (precision weights 1 / width^2)
    ca = pd.read_csv(REFERENCE / "tod_ab2097_results.csv")
    ca = ca[(ca["case"] == "main") & (ca["group"] == "P") & (ca["outcome"] == "all_units") & (ca["measure"] == "per_1000_homes")].iloc[0]
    us = est[0]
    wus, wca = 1 / (us["p95"] - us["p05"]) ** 2, 1 / (ca["interval90_high"] - ca["interval90_low"]) ** 2
    pooled = (us["effect"] * wus + ca["estimate"] * wca) / (wus + wca)
    half = 1 / np.sqrt(wus + wca) / 2 * 1.0
    est.append(dict(case="California AB 2097 near transit (TOD test)", places=int(ca["n_jurisdictions"]), effect=ca["estimate"],
                    p05=ca["interval90_low"], p95=ca["interval90_high"]))
    est.append(dict(case="Expanded US and California, precision-weighted (sensitivity)", places=len(inc) + int(ca["n_jurisdictions"]),
                    effect=pooled, p05=pooled - half, p95=pooled + half))
    pd.DataFrame(est).round(4).to_csv(REFERENCE / "parking_expanded_estimates.csv", index=False)
    print(pd.DataFrame(est).round(2).to_string(index=False))

    # prediction tools: US places
    us_scores = cv_score(inc, FEATURES_US)
    # California cross-test: train on US + other California cities, score left-out California cities
    b = rpt.dataset_b(pd.read_csv(REFERENCE / "parking_place_traits.csv", dtype={"state": str}))
    b = b.dropna(subset=["effect"]).copy()
    b["weight"] = b["weight"].astype(float)
    b["log_homes"] = np.log10(b["homes"].clip(lower=1))
    us2 = inc.copy()
    us2["log_homes"] = np.log10(us2["homes"].clip(lower=1))
    # put US weights on the same scale as California's (each source sums to 1)
    us2["weight"] = us2["weight"] / us2["weight"].sum()
    b["weight"] = b["weight"] / b["weight"].sum()
    ca_scores = cv_score(b.reset_index(drop=True), FEATURES_SHARED, extra_train=us2[FEATURES_SHARED + ["effect", "weight"]])
    rows = []
    for t in TOOLS:
        rows.append(dict(tool=t, us_error=us_scores[t], us_gain=1 - us_scores[t] / us_scores["one average"],
                         ca_error=ca_scores[t], ca_gain=1 - ca_scores[t] / ca_scores["one average"]))
    tools = pd.DataFrame(rows)
    tools["passes"] = (tools["us_gain"] >= 0.05) & (tools["ca_gain"] > 0) & (tools["tool"] != "one average")
    tools.round(4).to_csv(REFERENCE / "parking_expanded_tools.csv", index=False)
    print(tools.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
