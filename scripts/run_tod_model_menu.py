"""TOD full model runs: 8 methods plus the EconML causal forest (docs/tod/MODEL_MENU_PLAN.md; plan item 66).

Method 8 (causal forest) needs EconML installed separately (`uv pip install econml`); it is not a project dependency
(licence allowlist, see MODEL_MENU_PLAN.md dependency note).

    uv run --all-extras python scripts/run_tod_model_menu.py --model pace|share [--methods 0,1,...]

pace: the no-reform baseline (rows and traits of run_tod_pace_loop.py round 2), held-out city and later-years tests.
share: the round-8 share model (as run_tod_wi_net.py round 4), leave one reform city out, plus the Wisconsin net.
Writes reference/tod_menu_{model}_{method}.csv and reference/tod_menu_{model}_summary.csv.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import REFERENCE  # noqa: E402
import run_tod_lot_model as L  # noqa: E402

SEED = 20261031
NAMES = {0: "plain_average", 1: "linear_regression", 2: "lasso", 3: "regression_tree", 4: "random_forest",
         5: "gradient_boosting", 6: "nearest_neighbours", 7: "multilevel", 8: "causal_forest",
         9: "causal_forest_sklearn", 10: "causal_forest_sklearn_honest"}
ACAP = 2.97
EXCLUDE_HOLD = False
DROP_DATED = False   # audit check: drop traits dated after a window starts (2010 census homes; ACS at the reform year)
LEAF = 50            # random forest leaf size (baseline round 4 grid)
DROP_TRAITS: list[str] = []
EXCLUDE_CITY = ""    # audit check: leave one city out of all share-model training
TAG = ""


class Method:
    """fit(X, y, w, groups) / predict(X); traits are filled and scaled inside for the non-tree methods."""

    def __init__(self, k: int):
        self.k = k

    def _prep(self, X, fit: bool):
        from sklearn.decomposition import PCA
        Z = X.to_numpy(dtype=float)
        if fit:
            self.med = np.nanmedian(Z, axis=0)
            self.med = np.where(np.isfinite(self.med), self.med, 0.0)
        Z = np.where(np.isfinite(Z), Z, self.med)
        if fit:
            self.mu, self.sd = Z.mean(0), Z.std(0)
            self.sd[self.sd == 0] = 1.0
        Z = (Z - self.mu) / self.sd
        if self.k in (6, 7):
            if fit:
                self.pca = PCA(n_components=15, random_state=SEED).fit(Z)
            Z = self.pca.transform(Z)
        return Z

    def fit(self, X, y, w, groups=None):
        from sklearn import linear_model, neighbors, tree, ensemble
        k = self.k
        if k == 0:
            self.c = float(np.average(y, weights=w))
            return self
        if k in (3, 4, 5):
            Z = X
            m = {3: tree.DecisionTreeRegressor(min_samples_leaf=200, random_state=SEED),
                 4: ensemble.RandomForestRegressor(n_estimators=300, min_samples_leaf=LEAF, n_jobs=-1, random_state=SEED),
                 5: ensemble.HistGradientBoostingRegressor(random_state=SEED)}[k]
            if k in (3, 4):
                self.med = X.median()
                Z = X.fillna(self.med).replace([np.inf, -np.inf], 0)
            self.m = m.fit(Z, y, sample_weight=w)
            return self
        Z = self._prep(X, True)
        if k == 1:
            self.m = linear_model.Ridge(alpha=1.0).fit(Z, y, sample_weight=w)
        elif k == 2:
            self.m = linear_model.Lasso(alpha=0.01, max_iter=5000).fit(Z, y, sample_weight=w)
        elif k == 6:
            self.m = neighbors.KNeighborsRegressor(n_neighbors=50, weights="uniform", n_jobs=-1).fit(Z, y)
        elif k == 7:
            import statsmodels.api as sm
            exog = sm.add_constant(Z)
            self.m = sm.MixedLM(y, exog, groups=np.asarray(groups)).fit(method="lbfgs")
        return self

    def predict(self, X):
        k = self.k
        if k == 0:
            return np.full(len(X), self.c)
        if k in (3, 4):
            return self.m.predict(X.fillna(self.med).replace([np.inf, -np.inf], 0))
        if k == 5:
            return self.m.predict(X)
        Z = self._prep(X, False)
        if k == 7:
            import statsmodels.api as sm
            return np.asarray(sm.add_constant(Z, has_constant="add") @ self.m.fe_params)
        return self.m.predict(Z)


def milwaukee_fix(series: dict) -> None:
    """Shared baseline rule P8 (docs/shared/HOUSING_BASELINE.md 3a): the permit survey under-counts Milwaukee's 3+ unit
    buildings. Permit years 2015-2024 = survey 1- and 2-unit + property-file (MPROP) 3-4 and 5+ units built the next year."""
    d = pd.read_csv(REFERENCE / "housing_baseline_milwaukee_check.csv")
    p = d.pivot_table(index="year", columns="structure_type", values=["bps_permitted_units", "mprop_units_by_year_built"])
    s = series["Milwaukee placebo"].copy().astype(float)
    for yr in range(2015, 2025):
        s.loc[yr] = (p.loc[yr, ("bps_permitted_units", "1unit")] + p.loc[yr, ("bps_permitted_units", "2units")]
                     + p.loc[yr + 1, ("mprop_units_by_year_built", "3_4units")] + p.loc[yr + 1, ("mprop_units_by_year_built", "5plus")])
    series["Milwaukee placebo"] = s


class _SkForest:
    """The fitted final stage, with the same .effect(X) call as EconML's CausalForestDML."""

    def __init__(self, rf, leaf_values=None):
        self.rf, self.leaf_values = rf, leaf_values

    def effect(self, Z):
        if self.leaf_values is None:
            return self.rf.predict(Z)
        leaves = self.rf.apply(Z)
        return np.mean([self.leaf_values[t][leaves[:, t]] for t in range(leaves.shape[1])], axis=0)


def honest_leaves(rf, Z, ry, rt, w) -> list[np.ndarray]:
    """Honesty: each leaf's effect is re-estimated on the held-back half (never used to grow the trees), solving the
    local R-learner moment: tau = sum(w * rt * ry) / sum(w * rt^2). Leaves the half never reaches keep the tree's value."""
    leaves = rf.apply(Z)
    out = []
    for t, est in enumerate(rf.estimators_):
        n = est.tree_.node_count
        num = np.bincount(leaves[:, t], weights=w * rt * ry, minlength=n)
        den = np.bincount(leaves[:, t], weights=w * rt ** 2, minlength=n)
        v = est.tree_.value[:, 0, 0].copy()
        ok = den > 0
        v[ok] = num[ok] / den[ok]
        out.append(v)
    return out


def dml_forest(Xb, y, t, wt, mask, honest: bool = False):
    """Causal forest without EconML (licence allowlist): the same double-machine-learning design, scikit-learn only.
    1. cross-fitted (3 folds) outcome model m(x) = E[y | x] and upzoning model e(x) = P(upzoned | x);
    2. residuals y - m and t - e;
    3. a random forest fitted to (y - m) / (t - e) with weights (t - e)^2 (the R-learner), giving the effect tau(x).
    Law-off level from gradient boosting on non-upzoned lots, as for method 8. Returns (off, effect model, medians)."""
    from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor, RandomForestRegressor
    keep, w2 = thin(y, wt, mask)
    off = Method(5).fit(Xb[keep & ~t], y[keep & ~t], w2[keep & ~t])
    med = Xb[keep].median()
    Z = Xb[keep].fillna(med).to_numpy()
    yy, tt, ww = y[keep], t[keep].astype(int), w2[keep]
    fold = np.random.default_rng(SEED).integers(0, 3, len(yy))
    m_hat, e_hat = np.zeros(len(yy)), np.zeros(len(yy))
    for f in range(3):
        a, b = fold != f, fold == f
        m_hat[b] = HistGradientBoostingRegressor(random_state=SEED).fit(Z[a], yy[a], sample_weight=ww[a]).predict(Z[b])
        e_hat[b] = HistGradientBoostingClassifier(random_state=SEED).fit(Z[a], tt[a], sample_weight=ww[a]).predict_proba(Z[b])[:, 1]
    e_hat = np.clip(e_hat, 0.02, 0.98)
    ry, rt = yy - m_hat, tt - e_hat
    rf = RandomForestRegressor(n_estimators=400, min_samples_leaf=50, max_samples=0.3, n_jobs=-1, random_state=SEED)
    if not honest:
        rf.fit(Z, ry / rt, sample_weight=ww * rt ** 2)
        return off, _SkForest(rf), med
    half = np.random.default_rng(SEED + 1).random(len(yy)) < 0.5   # half grows the trees, the other half estimates
    rf.fit(Z[half], (ry / rt)[half], sample_weight=(ww * rt ** 2)[half])
    return off, _SkForest(rf, honest_leaves(rf, Z[~half], ry[~half], rt[~half], ww[~half])), med


def thin(y: np.ndarray, w: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Keep every building row; draw 10% of the zero rows and weight them x10 (same draw for every method)."""
    rng = np.random.default_rng(SEED)
    keep = mask & ((y > 0) | (rng.random(len(y)) < 0.10))
    w2 = np.where(y > 0, w, w * 10.0)
    return keep, w2


# ------------------------------------------------------------------ model 1: no-reform pace
def run_pace(methods: list[int]) -> None:
    import run_tod_pace_loop as P
    D = pd.read_parquet(L.OUT / "lots_rebuilt_halfmile.parquet")
    if EXCLUDE_HOLD:   # check: the 10 cities of the pace loop, to reconcile with its rounds
        D = D[~D["city"].isin(L.HOLD)]
    D = L.five_year_basis(L.dedupe_lots(D)).reset_index(drop=True)
    R = P.long_rows(D)
    for c in ("Chicago", "Madison", "Bellevue"):
        P.PLACE.setdefault(c, {"Chicago": ("Chicago city", "17"), "Madison": ("Madison city", "55"), "Bellevue": ("Bellevue city", "53")}[c])
    series, hu = P.bps_series()
    milwaukee_fix(series)   # round 3 (audit check 2)
    X = P.traits(R, 2, series, hu)
    if DROP_TRAITS:
        X = X.drop(columns=[c for c in DROP_TRAITS if c in X.columns])
    if DROP_DATED:
        X = X.drop(columns=[c for c in X.columns if c.startswith("v_") or c in ("log_census_homes", "log_rent", "log_home_value", "log_income")])
        print("traits kept:", list(X.columns), flush=True)
    y = R["y5"].clip(lower=0).values
    w = R["w"].values
    cities = sorted(R["city"].unique())
    base = P.bps_baseline(R, series, hu)
    summ = []
    for k in methods:
        if k == 8:
            continue   # no treatment in the no-reform model
        t0 = time.time()
        loco, fwd = np.full(len(R), np.nan), np.full(len(R), np.nan)
        for c in cities:
            te = (R["city"] == c).values
            keep, w2 = thin(y, w, R["city"].isin(L.training_cities(cities, c)).values)
            m = Method(k).fit(X[keep], y[keep], w2[keep], R.loc[keep, "city"].values)
            loco[te] = np.clip(m.predict(X[te]), 0, None)
        aft = (R["window"] == "after").values
        keep, w2 = thin(y, w, (R["window"] == "before").values)
        m = Method(k).fit(X[keep], y[keep], w2[keep], R.loc[keep, "city"].values)
        fwd[aft] = np.clip(m.predict(X[aft]), 0, None)
        R["p_loco"], R["p_fwd"] = loco, fwd
        rows = []
        for (c, wdw, s0), g in R.groupby(["city", "window", "start"]):
            rows.append({"city": c, "window": wdw, "start": s0, "actual": float((g["y5"] * g["w"]).sum()),
                         "place_out": float((g["p_loco"] * g["w"]).sum()),
                         "forward": float((g["p_fwd"] * g["w"]).sum()) if wdw == "after" else np.nan})
        T = pd.DataFrame(rows).merge(base, on=["city", "window", "start"], how="left")
        for col in ("place_out", "forward", "bps_same_pace"):
            ok = (T[col] > 0) & (T["actual"] > 0)
            T[f"abslog_{col}"] = np.abs(np.log(T[col] / T["actual"])).where(ok)
        T.round(2).to_csv(REFERENCE / f"tod_menu_pace_{NAMES[k]}{TAG}.csv", index=False)
        worst = T.loc[T["abslog_place_out"].idxmax()] if T["abslog_place_out"].notna().any() else None
        af = T["window"] == "after"
        mt, st = T["bps_same_pace"].notna(), T["start"] >= 2011
        summ.append({"method": NAMES[k], "held_out_city": T["abslog_place_out"].median(), "later_years": T.loc[af, "abslog_forward"].median(),
                     "matched_rows_model": T.loc[mt, "abslog_place_out"].median(), "matched_rows_survey": T.loc[mt, "abslog_bps_same_pace"].median(),
                     "city_median_model": T.groupby("city")["abslog_place_out"].median().median(),
                     "city_median_survey": T.groupby("city")["abslog_bps_same_pace"].median().median(),
                     "start2011_model": T.loc[st, "abslog_place_out"].median(), "start2011_survey": T.loc[st, "abslog_bps_same_pace"].median(),
                     "bench_same_pace_city": T["abslog_bps_same_pace"].median(), "bench_same_pace_later": T.loc[af, "abslog_bps_same_pace"].median(),
                     "worst_miss": None if worst is None else f"{worst.city} {worst.window} {worst.start}: {worst.place_out:,.0f} vs {worst.actual:,.0f}",
                     "minutes": round((time.time() - t0) / 60, 1)})
        # Wisconsin 2027-2031: fit on every row; homes on main-case near-stop lots in Milwaukee and Madison, then the
        # statewide near-stop figure scaled by the near-stop baseline (two cities hold 82% of near-stop homes; x1.147)
        if not EXCLUDE_HOLD:
            Wr, near = wi_pace_rows(P, series, hu)
            Xw = P.traits(Wr, 2, series, hu)[X.columns]
            if k == methods[0]:   # audit: Wisconsin lots outside the training range (flag only)
                from missing_middleware.tod import sanity as SN
                Xall = pd.concat([X, Xw], ignore_index=True)
                cty = pd.concat([R["city"].where(~R["city"].isin(["Milwaukee placebo", "Madison placebo"]), "train " + R["city"]),
                                 "WI " + Wr["city"]], ignore_index=True)
                fl = [f for f in SN.range_flags(Xall, cty) if str(f["city"]).startswith("WI")]
                SN.report(fl, REFERENCE / f"tod_menu_pace_wi_flags{TAG}.csv")
            keep, w2 = thin(y, w, np.ones(len(R), bool))
            m = Method(k).fit(X[keep], y[keep], w2[keep], R.loc[keep, "city"].values)
            pw = np.clip(m.predict(Xw), 0, None)
            for c in ("Milwaukee placebo", "Madison placebo"):
                mm = (Wr["city"] == c).values
                summ[-1][f"WI_{c.split()[0]}_near_2027_2031"] = float(pw[mm & near].sum())
                summ[-1][f"WI_{c.split()[0]}_table_2027_2031"] = float(pw[mm].sum())
            two = summ[-1]["WI_Milwaukee_near_2027_2031"] + summ[-1]["WI_Madison_near_2027_2031"]
            summ[-1]["WI_statewide_near_2027_2031"] = two * 14463.78 / (9220.49 + 3393.66)
        print(summ[-1], flush=True)
        pd.DataFrame(summ).round(3).to_csv(REFERENCE / f"tod_menu_pace_summary{TAG}{'_' + '_'.join(map(str, methods)) if len(methods) < 9 else ''}.csv", index=False)


def wi_pace_rows(P, series, hu) -> tuple[pd.DataFrame, np.ndarray]:
    """Wisconsin lots for 2027-2031 with the pace traits; near = main-case station area (rail/rapid 1/2 mi, 15-min bus 1/4 mi)."""
    from scipy.spatial import cKDTree
    W = pd.read_parquet(L.OUT / "wi_lots.parquet")
    W = W.assign(w=1.0, window="forecast", start=2027, end=2031, y5=np.nan)
    W["city"] = W["city"] + " placebo"   # the permit-survey place keys (Milwaukee placebo, Madison placebo) name the cities
    S = pd.read_csv(REFERENCE / "tod_stops.csv")
    px, py = L.lonlat_to_5070(S.lon, S.lat)
    xy = W[["x5070", "y5070"]].to_numpy()
    d = lambda m: cKDTree(np.c_[px[m], py[m]]).query(xy)[0]  # noqa: E731
    near = (d((S.flag_a_rapid == 1).values) <= 805) | (d((S.flag_b_15min == 1).values) <= 402)
    return W, near


# ------------------------------------------------------------------ model 2: TOD share model
def share_design():
    """Training lots (all cities) and Wisconsin lots, with the round-8 traits (as run_tod_wi_net.py rounds 3-4, variant a)."""
    import run_tod_wi_net as WN
    L.FIT.update(item25=True, item32=True, item34=True, item37=True, item46=True)
    T = pd.read_parquet(L.OUT / "lots_rebuilt_halfmile.parquet")
    cache = {k: L.cost_per_home(k[0], int(k[1]) - 1) for k in set(zip(T["city"], T["eff_year"]))}
    T["cost_per_home"] = [cache[(c, y)] for c, y in zip(T["city"], T["eff_year"])]
    T = L.five_year_basis(L.dedupe_lots(T))
    W = pd.read_parquet(L.OUT / "wi_lots.parquet")
    L.BPS_NAME.setdefault("Milwaukee", ("55", "Milwaukee"))
    L.BPS_NAME.setdefault("Madison", ("55", "Madison"))
    wc = {c: L.cost_per_home(c, 2022) for c in W["city"].unique()}
    W["cost_per_home"] = W["city"].map(wc)
    W = W.assign(w=1.0, placebo=0.0, rezoned_later=0.0, window_first=2019, ub5=W["units_before"] * 5 / 6, ua5=0.0)
    W.loc[(W["lot_group"] == "upzoned") & (W["use"] == "ind"), "lot_group"] = "upzoned_from_industrial"
    W["city"] = "WI " + W["city"]
    W["unit"] = "wi|" + W["unit"].astype(str)
    A = pd.concat([T.assign(_wi=0), W.assign(_wi=1)], ignore_index=True)
    Xa, Xb = L.features(A, True), L.features(A, False)
    V = A[[c for c in A.columns if c.startswith("v_")]].replace([np.inf, -np.inf], np.nan)
    Xa, Xb = pd.concat([Xa, V], axis=1), pd.concat([Xb, V], axis=1)
    from scipy.spatial import cKDTree
    wa = A["w"] * A["acres"].clip(lower=0.01)
    area_rate = (A["ub5"] * A["w"]).groupby(A["unit"]).transform("sum") / wa.groupby(A["unit"]).transform("sum")
    near = np.zeros(len(A))
    for u, ix in A.groupby("unit").groups.items():
        d = A.loc[ix]
        xy = d[["x5070", "y5070"]].to_numpy()
        nb = cKDTree(xy).query_ball_point(xy, r=400)
        h, ac = (d["ub5"] * d["w"]).to_numpy(), (d["acres"].clip(lower=0.01) * d["w"]).to_numpy()
        near[A.index.get_indexer(ix)] = [h[n].sum() / ac[n].sum() for n in nb]
    out = []
    for X in (Xa, Xb):
        X = X.assign(log_before5=np.log1p(A["ub5"].values), log_area_rate_before=np.log1p(area_rate.values),
                     log_near400_rate_before=np.log1p(near))
        out.append(X.drop(columns=[c for c in X.columns if c.startswith("reform_share_")]))
    return A, out[0], out[1], WN


def run_share(methods: list[int]) -> None:
    A, Xa, Xb, WN = share_design()
    y = A["ua5"].clip(lower=0).values
    w = A["w"].values
    ac = A["acres"].clip(lower=0.01).values
    hpa = y / ac
    up = (A["treated"] == 1).values
    tr = (A["_wi"] == 0).values & (A["city"] != EXCLUDE_CITY).values
    allc = sorted(A.loc[tr, "city"].unique())
    reform = [c for c in allc if not c.endswith("placebo")]
    tot = WN.city_totals()
    summ = []
    for k in methods:
        t0 = time.time()

        def fit_pair(mask):
            if k in (9, 10):   # causal forest built from scikit-learn only (BSD): double machine learning, R-learner final stage
                return ("cf", *dml_forest(Xb, hpa, up, w * ac, mask, honest=(k == 10)))
            if k == 8:   # causal forest: law-off level from boosting; law-on = law-off + forest effect of being upzoned
                from econml.dml import CausalForestDML
                from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
                keep, w2 = thin(hpa, w * ac, mask)
                off = Method(5).fit(Xb[keep & ~up], hpa[keep & ~up], w2[keep & ~up])
                Xf = Xb[keep].fillna(Xb[keep].median()).to_numpy()
                cf = CausalForestDML(model_y=HistGradientBoostingRegressor(random_state=SEED),
                                     model_t=HistGradientBoostingClassifier(random_state=SEED), discrete_treatment=True,
                                     n_estimators=400, min_samples_leaf=50, max_samples=0.3, random_state=SEED, cv=3)
                cf.fit(hpa[keep], up[keep].astype(int), X=Xf, sample_weight=w2[keep])
                med = Xb[keep].median()
                return ("cf", off, cf, med)
            ms = {}
            for g, X in ((True, Xa), (False, Xb)):
                keep, w2 = thin(hpa, w * ac, mask & (up == g))
                ms[g] = Method(k).fit(X[keep], hpa[keep], w2[keep], A.loc[keep, "city"].values)
            return ("pair", ms[True], ms[False], None)

        def predict(model, te):
            acc = np.minimum(ac[te], ACAP)
            uu = up[te]
            if model[0] == "cf":
                _, off, cf, med = model
                p_off = np.clip(off.predict(Xb[te]), 0, None) * acc
                tau = cf.effect(Xb[te].fillna(med).to_numpy())
                p_on = p_off.copy()
                p_on[uu] = np.clip(p_off[uu] / acc[uu] + tau[uu], 0, None) * acc[uu]
                return p_on, p_off
            _, mon, moff = model[:3]
            p_off = np.clip(moff.predict(L.forecast_view(Xb[te])), 0, None) * acc
            p_on = p_off.copy()
            if uu.any():
                p_on[uu] = np.clip(mon.predict(L.forecast_view(Xa[te][uu])), 0, None) * acc[uu]
            return p_on, p_off

        rows = []
        for c in reform:
            te = (A["city"] == c).values
            model = fit_pair(A["city"].isin(L.training_cities(allc, c)).values & tr)
            p_on, p_off = predict(model, te)
            uu, wt = up[te], w[te]
            s_on = float((p_on * wt)[uu].sum() / max((p_on * wt).sum(), 1e-9))
            s_off = float((p_off * wt)[uu].sum() / max((p_off * wt).sum(), 1e-9))
            ua, ub = A.loc[te, "ua5"].values, A.loc[te, "ub5"].values
            sa = float((ua * wt)[uu].sum() / max((ua * wt).sum(), 1e-9))
            sb = float((ub * wt)[uu].sum() / max((ub * wt).sum(), 1e-9))
            rows.append({"city": c, "share_before": sb, "share_after": sa, "model_on": s_on, "model_off": s_off,
                         "model_uplift": s_on - s_off, "actual_change": sa - sb})
        Rk = pd.DataFrame(rows)
        Kk = float(Rk["actual_change"].sum() / Rk["model_uplift"].sum()) if Rk["model_uplift"].sum() != 0 else np.nan
        ok = (Rk["model_on"] > 0) & (Rk["share_after"] > 0)
        Rk["abslog_model"] = np.abs(np.log(Rk["model_on"] / Rk["share_after"])).where(ok)
        Rk["abslog_same_share"] = np.abs(np.log(Rk["share_before"] / Rk["share_after"])).where(ok & (Rk["share_before"] > 0))
        cal = Rk["share_before"] + Kk * Rk["model_uplift"]
        okc = (cal > 0) & (Rk["share_after"] > 0)
        Rk["abslog_calibrated"] = np.abs(np.log(cal / Rk["share_after"])).where(okc)
        # Wisconsin: fit on every training city
        model = fit_pair(tr)
        braw = 0.0
        for c in ("Milwaukee", "Madison"):
            te = (A["city"] == "WI " + c).values
            p_on, p_off = predict(model, te)
            uu = up[te]
            so, sf = p_on / max(p_on.sum(), 1e-9), p_off / max(p_off.sum(), 1e-9)
            t = tot.loc[WN.CITY_NAME[c]]
            total = float(t["all_housing"]) * min(1.0, float(A.loc[te, "census_homes"].sum()) / float(t["homes_2020"]))
            braw += float(so[uu].sum() - sf[uu].sum()) * total
        scale = WN.NEAR_STATE["today"] / float(tot.loc[["Milwaukee city", "Madison city"], "near"].sum())
        Rk.round(4).to_csv(REFERENCE / f"tod_menu_share_{NAMES[k]}{TAG}.csv", index=False)
        worst = Rk.loc[Rk["abslog_model"].idxmax()] if Rk["abslog_model"].notna().any() else None
        summ.append({"method": NAMES[k], "held_out_city_share": Rk["abslog_model"].median(),
                     "held_out_city_calibrated": Rk["abslog_calibrated"].median(), "bench_same_share": Rk["abslog_same_share"].median(),
                     "K": Kk, "WI_B_raw": braw * scale, "WI_B_calibrated": Kk * braw * scale if Kk == Kk else np.nan,
                     "worst_miss": None if worst is None else f"{worst.city}: {worst.model_on:.3f} vs {worst.share_after:.3f}",
                     "minutes": round((time.time() - t0) / 60, 1)})
        print(summ[-1], flush=True)
        pd.DataFrame(summ).round(4).to_csv(REFERENCE / f"tod_menu_share_summary{TAG}{'_' + '_'.join(map(str, methods)) if len(methods) < 9 else ''}.csv", index=False)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["pace", "share"], required=True)
    ap.add_argument("--methods", default="0,1,2,3,4,5,6,7,8")
    ap.add_argument("--no-holdouts", action="store_true", help="check: leave Chicago, Madison and Bellevue out")
    ap.add_argument("--leaf", type=int, default=50)
    ap.add_argument("--drop-traits", default="", help="comma list of traits to leave out (baseline round 4 grid)")
    ap.add_argument("--exclude-city", default="", help="share model check: leave this city out of all training")
    ap.add_argument("--drop-dated", action="store_true", help="check: drop census homes and ACS traits (dated after windows start)")
    a = ap.parse_args(argv)
    ms = [int(x) for x in a.methods.split(",")]
    global EXCLUDE_HOLD, TAG, DROP_DATED  # noqa: PLW0603
    EXCLUDE_HOLD, DROP_DATED = a.no_holdouts, a.drop_dated
    TAG = ("_noholdouts" if a.no_holdouts else "") + ("_nodated" if a.drop_dated else "")
    global EXCLUDE_CITY, LEAF, DROP_TRAITS
    EXCLUDE_CITY = a.exclude_city
    LEAF, DROP_TRAITS = a.leaf, [t for t in a.drop_traits.split(",") if t]
    if LEAF != 50:
        TAG += f"_leaf{LEAF}"
    if DROP_TRAITS:
        TAG += "_no_" + "_".join(t.replace("log_", "") for t in DROP_TRAITS)
    if EXCLUDE_CITY:
        TAG += "_without_" + EXCLUDE_CITY.replace(" ", "_").lower()
    (run_pace if a.model == "pace" else run_share)(ms)


if __name__ == "__main__":
    main()
