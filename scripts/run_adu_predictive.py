"""ADU predictive test: plain average, the adopted two-stage model refitted on the same rows, and three two-part
flexible models (causal forest, boosted trees, regularised Poisson regression), judged by the pass rule fixed in
docs/adu/PREDICTIVE_PLAN.md before any outcome was computed. Results: docs/adu/PREDICTIVE_RESULTS.md.

    uv run --all-extras python scripts/build_adu_predictive_panel.py   # first (see its docstring for --fetch)
    uv run --all-extras python scripts/run_adu_predictive.py

Inputs: data/processed/adu_predictive/{panel,features,market,wi_features}.parquet; for the adopted model's aggregate
members and the Wisconsin step, the same local inputs as scripts/run_pooled_regression.py.
Outputs (aggregates only):
    reference/adu_predictive_results.csv   one row per method x test: mean miss, units won, pass
    reference/adu_predictive_by_unit.csv   one row per test x held-out unit x method: observed, predicted, miss
    reference/adu_predictive_placebo.csv   no-law rows: miss and the law effect each two-part method would assign
    reference/adu_predictive_robustness.csv  other seeds, for any forest or boosting pass
    reference/adu_predictive_wi_*.csv      only if a method passes (PREDICTIVE_PLAN section 8)
    data/processed/adu_predictive/predictions.parquet, summary.json
Units: rates are ADU permits per 1,000 one-unit detached homes per year; a miss is |predicted - observed| in that unit.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.comparison import pooled_regression as pr  # noqa: E402

PROCESSED = ROOT / "data" / "processed"
REFERENCE = ROOT / "reference"
OUT = PROCESSED / "adu_predictive"
SEED = 20261028
ROBUST_SEEDS = (20261029, 20261030, 20261031, 20261032, 20261033)

LAW_STATES = ("CA", "WA", "OR", "RI", "MA", "ME", "UT", "VT")
TEST1_STATES = ("WA", "OR", "RI", "MA", "ME", "UT", "VT")
TEST1_SERIES = {"WA": "WA_cities", "OR": "OR_cities", "RI": "RI_statewide", "MA": "MA_statewide",
                "ME": "ME_statewide", "UT": "UT_mih", "VT": "VT_chittenden"}
FOLD_CLUSTERS = ("CA", "WA", "OR", "RI", "MA", "ME", "UT", "VT", "TX", "CO", "MN", "WI", "HI", "MD", "MT")
CITY_FOLD = {"seattle": "WA", "portland": "OR", "austin": "TX", "denver": "CO", "minneapolis": "MN", "madison": "WI"}
METHODS = ("plain_average", "current_model", "causal_forest", "boosted_trees", "regularised_regression")
ADVANCED = ("causal_forest", "boosted_trees", "regularised_regression")
LABELS = {"plain_average": "Plain average", "current_model": "Adopted model, refitted on the same rows",
          "causal_forest": "Causal forest (two parts)", "boosted_trees": "Boosted trees (two parts)",
          "regularised_regression": "Regularised Poisson regression (two parts)", "guess_zero": "Guess zero"}
CUR_WITHIN = ("value_dev", "income_dev", "log_homes", "law", "local", "k1", "k2", "k3")
ALPHAS = tuple(np.logspace(-4, 1, 10))


# ---------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------

def load():
    panel = pd.read_parquet(OUT / "panel.parquet")
    feats = pd.read_parquet(OUT / "features.parquet").set_index("geo")
    market = pd.read_parquet(OUT / "market.parquet").set_index("geo")
    panel["rate"] = panel["count"] / panel["homes"] * 1000
    return panel, feats, market


def cluster_weights(rows: pd.DataFrame) -> np.ndarray:
    """Home-years, rescaled so every state (cluster) carries the same total weight (the adopted scheme)."""
    hy = rows["homes"].to_numpy(float)
    tot = pd.Series(hy).groupby(rows["cluster"].to_numpy()).transform("sum").to_numpy()
    w = hy / tot
    return w / w.mean()


def treat_cols(rows: pd.DataFrame, part: str, k_override: int | None = None, strong_override: int | None = None) -> np.ndarray:
    local = rows["local"].to_numpy(float)
    if part == "nolaw":
        return local[:, None]
    k = rows["k"].to_numpy(float) if k_override is None else np.full(len(rows), float(k_override))
    k = np.clip(np.nan_to_num(k, nan=4.0), 1, 4)
    strong = rows["strong"].to_numpy(float) if strong_override is None else np.full(len(rows), float(strong_override))
    return np.column_stack([strong, k == 1, k == 2, k == 3, local]).astype(float)


# ---------------------------------------------------------------------------
# methods
# ---------------------------------------------------------------------------

def plain_average(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """Per law status: equal-weighted mean over training states of each state's pooled rate."""
    out = np.zeros(len(test))
    for law in (0, 1):
        tr = train[train["law"].eq(law)]
        by = tr.groupby("cluster").apply(lambda g: g["count"].sum() / g["homes"].sum() * 1000, include_groups=False)
        lev = float(by.mean()) if len(by) else 0.0
        out[test["law"].eq(law).to_numpy()] = lev
    return out


class TwoPart:
    """One model fitted on law-in-force rows and one on no-law rows (the TOD run-E construction)."""

    def __init__(self, kind: str, seed: int = SEED):
        self.kind, self.seed = kind, seed
        self.models = {}

    def _make(self, X, y, w, groups):
        from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
        if self.kind == "causal_forest":
            m = RandomForestRegressor(n_estimators=500, min_samples_leaf=20, max_features=1 / 3, n_jobs=-1,
                                      random_state=self.seed)
            m.fit(X, y, sample_weight=w)
            return m
        if self.kind == "boosted_trees":
            m = HistGradientBoostingRegressor(loss="poisson", max_depth=3, learning_rate=0.05, max_iter=500,
                                              min_samples_leaf=20, early_stopping=True, validation_fraction=0.2,
                                              n_iter_no_change=20, random_state=self.seed)
            m.fit(X, y, sample_weight=w)
            return m
        if self.kind == "regularised_regression":
            return fit_poisson_cv(X, y, w, groups)
        raise ValueError(self.kind)

    def fit(self, rows: pd.DataFrame, F: np.ndarray):
        for part, law in (("law", 1), ("nolaw", 0)):
            sel = rows["law"].eq(law).to_numpy()
            if sel.sum() < 30:
                self.models[part] = None
                continue
            r = rows[sel]
            X = np.hstack([F[sel], treat_cols(r, part)])
            self.models[part] = self._make(X, r["rate"].to_numpy(float), cluster_weights(r), r["cluster"].to_numpy())
            self.models[part + "_fallback"] = float(np.average(r["rate"], weights=cluster_weights(r)))
        return self

    def predict_part(self, rows: pd.DataFrame, F: np.ndarray, part: str, **kw) -> np.ndarray:
        m = self.models.get(part)
        if m is None:
            return np.full(len(rows), self.models.get(part + "_fallback", 0.0))
        X = np.hstack([F, treat_cols(rows, part, **kw)])
        return np.clip(m.predict(X), 0, None)

    def predict(self, rows: pd.DataFrame, F: np.ndarray) -> np.ndarray:
        law = rows["law"].eq(1).to_numpy()
        out = np.zeros(len(rows))
        if law.any():
            out[law] = self.predict_part(rows[law], F[law], "law")
        if (~law).any():
            out[~law] = self.predict_part(rows[~law], F[~law], "nolaw")
        return out


class _Scaled:
    def __init__(self, mu, sd, model):
        self.mu, self.sd, self.model = mu, sd, model

    def predict(self, X):
        return self.model.predict((X - self.mu) / self.sd)


def fit_poisson_cv(X, y, w, groups):
    """L2 Poisson regression; penalty chosen from ALPHAS by leave-one-state-out CV inside the training rows
    (weighted Poisson deviance)."""
    from sklearn.linear_model import PoissonRegressor
    from sklearn.metrics import mean_poisson_deviance
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd[sd == 0] = 1
    Z = (X - mu) / sd
    ug = np.unique(groups)
    best, best_a = np.inf, ALPHAS[-1]
    if len(ug) >= 3:
        for a in ALPHAS:
            dev = []
            for g in ug:
                tr, te = groups != g, groups == g
                m = PoissonRegressor(alpha=a, max_iter=300)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    m.fit(Z[tr], y[tr], sample_weight=w[tr])
                p = np.clip(m.predict(Z[te]), 1e-9, None)
                dev.append(mean_poisson_deviance(y[te], p, sample_weight=w[te]))
            d = float(np.mean(dev))
            if d < best:
                best, best_a = d, a
    m = PoissonRegressor(alpha=best_a, max_iter=500)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m.fit(Z, y, sample_weight=w)
    m.chosen_alpha_ = best_a
    return _Scaled(mu, sd, m)


# ---- adopted model, refitted --------------------------------------------------------------------

def aggregate_members() -> pd.DataFrame:
    """The adopted member geographies of the aggregate state series (county subdivisions / places)."""
    import run_pooled_regression as rp
    acs = pr.read_acs_members(rp.acs_paths(), {"44", "25", "23", "49", "50"})
    parts = []
    for sid in ("RI_statewide", "MA_statewide", "ME_statewide", "UT_mih", "VT_chittenden"):
        from missing_middleware.comparison import statewide_states as ss
        den = ss.SERIES[sid]["denominator"]
        m = pr.members_for(acs, "cousubs", den[1], rp.STATE_PARENT[sid])
        parts.append(m.assign(group_id=sid))
    return pd.concat(parts, ignore_index=True)


def current_inputs(panel: pd.DataFrame, market: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """pooled_regression rows and members for every panel row. Members: the row's own geography (California
    jurisdictions with the adopted ca_dataset market values); aggregates: the adopted member geographies
    (Honolulu, Montgomery County, Bozeman: their own geography). Missing medians take the row's context
    homes-weighted mean, flagged."""
    ca = pd.read_parquet(PROCESSED / "ca_regression" / "ca_dataset.parquet").set_index("census_geoid")
    rows = panel.copy()
    rows["group_id"] = np.where(rows["level"].eq("aggregate") & rows["series"].isin(
        ["RI_statewide", "MA_statewide", "ME_statewide", "UT_mih", "VT_chittenden"]), rows["series"],
        np.where(rows["cluster"].eq("CA"), "ca:" + rows["ca_geoid"].fillna(""), rows["geo"]))
    rows["years"] = 1.0
    rows["incl_new_house"] = True
    rows["coverage"] = 1.0
    rows["pre_rate"] = np.nan
    mem = []
    agg = aggregate_members()
    mem.append(agg)
    own = rows[~rows["group_id"].isin(agg["group_id"]) & ~rows["cluster"].eq("CA")].drop_duplicates("group_id")
    mk = market.reindex(own["geo"])
    m = pd.DataFrame({"group_id": own["group_id"].values, "geoid": own["geo"].values, "sumlevel": own["level"].values,
                      "homes": own["homes"].values, "value": mk["value"].values, "income": mk["income"].values,
                      "rent": mk["rent"].values, "renter_share": mk["renter_share"].values, "filled": ""})
    ctx = own["context"].values
    for c in ("value", "income", "rent", "renter_share"):
        miss = m[c].isna()
        if miss.any():
            means = m.assign(ctx=ctx).dropna(subset=[c]).groupby("ctx").apply(
                lambda g: np.average(g[c], weights=g["homes"].clip(lower=1)), include_groups=False)
            m.loc[miss, c] = pd.Series(ctx[miss.to_numpy()]).map(means).to_numpy()
            m.loc[miss, "filled"] += f"{c}_context;"
    mem.append(m)
    car = rows[rows["cluster"].eq("CA")].drop_duplicates("group_id")
    cm = ca.reindex(car["ca_geoid"])
    mem.append(pd.DataFrame({"group_id": car["group_id"].values, "geoid": car["ca_geoid"].values, "sumlevel": "160",
                             "homes": cm["homes"].values, "value": cm["value"].values, "income": cm["income"].values,
                             "rent": cm["rent"].values, "renter_share": cm["renter_share"].values,
                             "filled": cm["filled"].fillna("").values}))
    members = pd.concat(mem, ignore_index=True)
    members = members[members["homes"].fillna(0) > 0]
    return rows, members


def current_fit_predict(rows: pd.DataFrame, members: pd.DataFrame, train: np.ndarray, test: np.ndarray) -> np.ndarray:
    tr = rows[train].reset_index(drop=True)
    p_tr = pr.Pooled(tr[["cluster", "series", "group_id", "year", "count", "years", "law", "local", "k", "incl_new_house",
                          "coverage", "pre_rate"]], members[members["group_id"].isin(tr["group_id"])])
    s2 = tuple(c for c in LAW_STATES if c in set(tr["cluster"]))
    f = pr.fit_two_stage(p_tr, pr.TSpec("current", CUR_WITHIN, (), stage2_clusters=s2))
    te = rows[test].reset_index(drop=True)
    p_te = pr.Pooled(te[["cluster", "series", "group_id", "year", "count", "years", "law", "local", "k", "incl_new_house",
                          "coverage", "pre_rate"]], members[members["group_id"].isin(te["group_id"])])
    pred = pr.predict_rows_ts(f, p_te)
    # predicted count for the row's own homes (aggregate members' homes can differ slightly from the series' homes)
    rate = pred["pred_count"].to_numpy() / pred["homes"].to_numpy() * 1000
    return rate


# ---------------------------------------------------------------------------
# folds and predictions
# ---------------------------------------------------------------------------

def folds(panel: pd.DataFrame) -> list[tuple[str, np.ndarray, np.ndarray]]:
    out = []
    for c in FOLD_CLUSTERS:
        test = panel["cluster"].eq(c).to_numpy()
        if test.any():
            out.append((c, ~test, test))
    final_test = panel["series"].isin(["WA_cities", "OR_cities"]).to_numpy()
    out.append(("final_WA_OR", ~panel["cluster"].isin(["WA", "OR"]).to_numpy(), final_test))
    return out


def run_all(panel, feats, market, seed=SEED, methods=METHODS, log=print) -> pd.DataFrame:
    F_all = feats.reindex(panel["geo"]).to_numpy(float)
    rows_cur, members = current_inputs(panel, market)
    preds = []
    for name, train, test in folds(panel):
        tr, te = panel[train], panel[test]
        d = te[["row_id"]].copy()
        d["fold"] = name
        if "plain_average" in methods:
            d["plain_average"] = plain_average(tr, te)
        if "current_model" in methods:
            d["current_model"] = current_fit_predict(rows_cur, members, train, test)
        for meth in ADVANCED:
            if meth not in methods:
                continue
            tp = TwoPart(meth, seed).fit(tr, F_all[train])
            d[meth] = tp.predict(te, F_all[test])
            d[f"{meth}__law_part"] = tp.predict_part(te, F_all[test], "law", k_override=4, strong_override=1)
            d[f"{meth}__nolaw_part"] = tp.predict_part(te, F_all[test], "nolaw")
        d["guess_zero"] = 0.0
        preds.append(d)
        log(f"fold {name}: {int(test.sum())} rows", flush=True)
    return pd.concat(preds, ignore_index=True)


# ---------------------------------------------------------------------------
# scoring (PREDICTIVE_PLAN sections 6 and 7)
# ---------------------------------------------------------------------------

def pooled_rate(g: pd.DataFrame, col: str) -> float:
    return float((g[col] * g["homes"]).sum() / g["homes"].sum())


def score_unit(g: pd.DataFrame, cols: list[str]) -> dict:
    """g: rows of one held-out unit with observed `rate` and predicted rate columns. Per geography, rates pooled over
    its rows; rate miss = homes-weighted mean |pred - obs|; where-only miss = 1/2 sum |pred share - obs share|."""
    g = g.assign(obs_cnt=g["rate"] * g["homes"] / 1000)
    geo = g.groupby("geo").agg(homes=("homes", "sum"), obs=("obs_cnt", "sum"), hm=("homes", "mean"))
    out = {"n_geographies": len(geo), "obs_rate": float(geo["obs"].sum() / geo["homes"].sum() * 1000)}
    for c in cols:
        pc = (g[c] * g["homes"] / 1000).groupby(g["geo"]).sum()
        pr_ = pc / geo["homes"] * 1000
        ob = geo["obs"] / geo["homes"] * 1000
        out[f"pred_rate__{c}"] = float(pc.sum() / geo["homes"].sum() * 1000)
        out[f"rate_miss__{c}"] = float(np.average((pr_ - ob).abs(), weights=geo["hm"]))
        if geo["obs"].sum() > 0 and pc.sum() > 0 and len(geo) > 1:
            out[f"where_miss__{c}"] = float(0.5 * (pc / pc.sum() - geo["obs"] / geo["obs"].sum()).abs().sum())
        else:
            out[f"where_miss__{c}"] = np.nan
    return out


def madison_like_geos() -> set[str]:
    ml = pd.read_csv(REFERENCE / "madison_like_cities.csv", dtype=str)
    return {"place:" + g.replace("1600000US", "") for g in ml["geo_id"]}


def score(panel: pd.DataFrame, pred: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    P = pred.merge(panel[["row_id", "cluster", "series", "geo", "year", "law", "homes", "rate", "count", "unit_group"]],
                   on="row_id")
    rows = []
    # test 1: statewide
    for st in TEST1_STATES:
        g = P[P["fold"].eq(st) & P["series"].eq(TEST1_SERIES[st]) & P["law"].eq(1)]
        if g.empty:
            continue
        obs = pooled_rate(g, "rate")
        r = {"test": "1_how_much", "unit": st, "rows": len(g), "obs_rate": obs}
        for c in cols:
            p = pooled_rate(g, c)
            r[f"pred_rate__{c}"] = p
            r[f"miss__{c}"] = abs(p - obs)
            r[f"log_error__{c}"] = np.log(p / obs) if p > 0 and obs > 0 else np.nan
        rows.append(r)
    # tests 2 and 3: where
    units = [(f"{c} tracts", CITY_FOLD[c], P["series"].eq(f"{c}_tracts")) for c in CITY_FOLD]
    units += [("California jurisdictions", "CA", P["series"].eq("CA_jurisdictions")),
              ("Washington cities", "final_WA_OR", P["series"].eq("WA_cities")),
              ("Oregon cities", "final_WA_OR", P["series"].eq("OR_cities"))]
    mlg = madison_like_geos()
    ml_mask = P["geo"].isin(mlg) & P["law"].eq(1) & (
        (P["cluster"].eq("CA") & P["fold"].eq("CA")) | (P["cluster"].isin(["WA", "OR"]) & P["fold"].eq("final_WA_OR")))
    for name, fold, m in units + [("Madison-like cities", None, ml_mask)]:
        g = P[m & (P["fold"].eq(fold) if fold else True)]
        if g.empty:
            continue
        s = score_unit(g, cols)
        rows.append({"test": "2_where_rate", "unit": name, "rows": len(g), "n_geographies": s["n_geographies"],
                     "obs_rate": s["obs_rate"], **{f"pred_rate__{c}": s[f"pred_rate__{c}"] for c in cols},
                     **{f"miss__{c}": s[f"rate_miss__{c}"] for c in cols}})
        rows.append({"test": "3_where_only", "unit": name, "rows": len(g), "n_geographies": s["n_geographies"],
                     "obs_rate": s["obs_rate"], **{f"miss__{c}": s[f"where_miss__{c}"] for c in cols if c != "guess_zero"}})
    return pd.DataFrame(rows)


def judge(by_unit: pd.DataFrame, methods=ADVANCED) -> pd.DataFrame:
    need = {"1_how_much": 4, "2_where_rate": 6, "3_where_only": 6}
    out = []
    for test, g in by_unit.groupby("test"):
        g = g.dropna(subset=["miss__plain_average", "miss__current_model"])
        base = {m: float(g[f"miss__{m}"].mean()) for m in ("plain_average", "current_model")}
        gz = float(g["miss__guess_zero"].mean()) if "miss__guess_zero" in g else np.nan
        for m in ("plain_average", "current_model", *methods, "guess_zero"):
            col = f"miss__{m}"
            if col not in g or g[col].isna().all():
                continue
            mean = float(g[col].mean())
            r = {"test": test, "method": m, "label": LABELS[m], "units": len(g), "mean_miss": mean,
                 "plain_average_mean_miss": base["plain_average"], "current_model_mean_miss": base["current_model"],
                 "guess_zero_mean_miss": gz}
            if m in methods:
                wins = int(((g[col] < g["miss__plain_average"]) & (g[col] < g["miss__current_model"])).sum())
                r.update(units_beating_both=wins, units_needed=need[test],
                         beats_plain_on_mean=mean < base["plain_average"], beats_current_on_mean=mean < base["current_model"],
                         loses_to_guess_zero=(mean > gz) if not np.isnan(gz) else np.nan)
                r["passes"] = bool(r["beats_plain_on_mean"] and r["beats_current_on_mean"] and wins >= need[test])
            out.append(r)
    return pd.DataFrame(out)


def placebo(panel: pd.DataFrame, pred: pd.DataFrame) -> pd.DataFrame:
    """No-law rows in their own state's fold: rate miss of each method, and the law effect (law part at year 4+,
    strong law, minus the no-law part) each two-part method would assign. Rates per 1,000 homes per year."""
    P = pred.merge(panel[["row_id", "cluster", "series", "geo", "law", "homes", "rate"]], on="row_id")
    P = P[P["law"].eq(0) & P["fold"].eq(P["cluster"])]
    out = []
    for s, g in P.groupby("series"):
        r = {"series": s, "rows": len(g), "obs_rate": pooled_rate(g, "rate")}
        for m in METHODS + ("guess_zero",):
            if m in g:
                gg = g.assign(_p=g[m])
                r[f"pred_rate__{m}"] = pooled_rate(gg, "_p")
                r[f"miss__{m}"] = abs(r[f"pred_rate__{m}"] - r["obs_rate"])
        for m in ADVANCED:
            if f"{m}__law_part" in g:
                eff = g[f"{m}__law_part"] - g[f"{m}__nolaw_part"]
                r[f"law_effect__{m}"] = float((eff * g["homes"]).sum() / g["homes"].sum())
        out.append(r)
    return pd.DataFrame(out)


# ---------------------------------------------------------------------------
# Owner process rule of 2026-10-28: flags before each run (never stop the run)
# ---------------------------------------------------------------------------

PANEL_UNITS = {   # column -> (unit, check)
    "count": ("ADU permits in the row's year (after the outcome rules)", lambda s: s >= 0),
    "homes": ("one-unit detached homes (ACS 2020-2024 B25024_002)", lambda s: s > 0),
    "rate": ("ADU permits per 1,000 one-unit detached homes per year", lambda s: (s >= 0) & (s <= 50)),
    "law": ("0/1 statewide law in force", lambda s: s.isin([0, 1])),
    "local": ("0/1 local ADU reform in force", lambda s: s.isin([0, 1])),
    "strong": ("0/1 Mercatus strong law (0 when no law)", lambda s: s.isin([0, 1])),
    "k": ("years since the statewide law (1 = first full year); missing when no law", lambda s: s.isna() | s.between(1, 12)),
    "year": ("calendar year (OFM estimate year for Washington cities)", lambda s: s.between(2012, 2026)),
}
# First year coded as law in force, from the effective / compliance dates in STATEWIDE_STATES.md
LAW_FIRST_YEAR = {"CA": 2017, "WA": 2024, "OR": 2019, "RI": 2025, "MA": 2025, "ME": 2025, "UT": 2022, "VT": 2021,
                  "CO": 2025}


def feature_unit(col: str, kinds: dict) -> tuple[str, callable]:
    base, _, suffix = col.partition("__")
    if suffix == "rank":
        return "rank within context (0-1)", lambda s: s.between(0, 1)
    if suffix == "logratio":
        return "log ratio to context homes-weighted mean", lambda s: s.abs() <= 6
    if suffix == "missing":
        return "0/1 missing flag", lambda s: s.isin([0.0, 1.0])
    k = kinds.get(base)
    if k == "share":
        return "share (0-1)", lambda s: s.between(0, 1)
    if k in ("years", "minutes"):
        return k, lambda s: s.between(0, 200)
    if k in ("count", "ratio"):
        return k, lambda s: s >= 0
    return "unknown", lambda s: pd.Series(True, index=s.index)


def flags(panel: pd.DataFrame, feats: pd.DataFrame) -> pd.DataFrame:
    import build_adu_predictive_panel as B
    kinds = {v[0]: v[3] for v in B.VARIABLES}
    out = []

    def add(kind, where, column, n, detail):
        out.append(dict(flag_type=kind, where=where, column=column, n_rows=int(n), detail=detail))

    # units: panel columns
    for col, (unit, ok) in PANEL_UNITS.items():
        bad = ~ok(panel[col])
        if bad.any():
            for ug, g in panel[bad].groupby("unit_group"):
                add("unit_check", ug, col, len(g), f"{unit}: {len(g)} rows outside the plausible range, e.g. "
                    f"{', '.join(f'{v:.3g}' for v in g[col].head(3))}")
    # units: features
    for col in feats.columns:
        unit, ok = feature_unit(col, kinds)
        bad = ~ok(feats[col])
        if bad.any():
            add("unit_check", "features", col, bad.sum(), f"{unit}: {int(bad.sum())} geographies outside, e.g. "
                f"{', '.join(f'{v:.3g}' for v in feats.loc[bad, col].head(3))}")
    # units: raw dollar values must be positive
    vals = pd.read_parquet(OUT / "values.parquet").set_index("geo").reindex(panel["geo"].unique())
    for vid, _, _, kind, _ in B.VARIABLES:
        if kind == "dollar":
            bad = vals[vid].notna() & (vals[vid] <= 0)
            if bad.any():
                add("unit_check", "values", vid, bad.sum(), "dollars not positive")
            miss = vals[vid].isna().sum()
            if miss:
                add("missing_input", "values", vid, miss, f"{miss} panel geographies have no ACS value (filled; flagged)")
    # policy definition: law in force before its effective date
    early = panel[panel["law"].eq(1) & (panel["year"] < panel["cluster"].map(LAW_FIRST_YEAR))]
    for ug, g in early.groupby("unit_group"):
        add("policy_definition", ug, "law", len(g), "coded law in force before the law's first full year")
    nolaw_late = panel[panel["law"].eq(0) & (panel["year"] >= panel["cluster"].map(LAW_FIRST_YEAR))]
    for ug, g in nolaw_late.groupby("unit_group"):
        add("policy_definition", ug, "law", len(g), "coded no law in a year on or after the law's first full year")
    # policy definition: >2 per parcel and apartment lots (what the outcome rules can and cannot remove)
    info = json.loads((OUT / "build_info.json").read_text())
    for city, d in info.get("tract_cities", {}).items():
        if "units_in_years" in d:
            add("policy_definition", f"{city} tracts", "count", 0,
                f"2-per-parcel cap and factors: {d['units_in_years']:.0f} ADU units in the years -> "
                f"{d['kept_after_cap_and_factors']:.1f} kept; {d['kept_no_tract_or_outside']:.1f} kept units had no tract "
                f"inside the city (left out)")
    add("policy_definition", "all non-California rows", "count", 0,
        "ADUs on apartment (multifamily) lots cannot be identified outside California (and Minneapolis duplex lots, "
        "removed by factor); they remain in the counts. California: definite A2 multifamily-lot units removed; "
        "'possible' ones remain")
    add("policy_definition", "Washington, Oregon, aggregates", "count", 0,
        "no parcel ids in these series, so the 2-per-parcel cap cannot be applied (rare in practice)")
    # out of training range: each held-out unit's homes-weighted median trait vs training rows' 1st-99th pct
    F = feats.reindex(panel["geo"])
    F.index = panel.index
    units = {f"{c} tracts": (CITY_FOLD[c], panel["series"].eq(f"{c}_tracts")) for c in CITY_FOLD}
    units.update({"California jurisdictions": ("CA", panel["series"].eq("CA_jurisdictions")),
                  "Washington cities": ("final_WA_OR", panel["series"].eq("WA_cities")),
                  "Oregon cities": ("final_WA_OR", panel["series"].eq("OR_cities"))})
    units.update({s: (TEST1_STATES[[TEST1_SERIES[x] for x in TEST1_STATES].index(s)], panel["series"].eq(s))
                  for s in ("RI_statewide", "MA_statewide", "ME_statewide", "UT_mih", "VT_chittenden")})
    cols = [c for c in feats.columns if not c.endswith("__missing")]
    for name, (fold, m) in units.items():
        train = ~panel["cluster"].isin(["WA", "OR"] if fold == "final_WA_OR" else [fold])
        lo, hi = F.loc[train, cols].quantile(0.01), F.loc[train, cols].quantile(0.99)
        g = F.loc[m, cols]
        w = panel.loc[m, "homes"].to_numpy()
        med = g.apply(lambda s: s.iloc[np.argsort(s.to_numpy())][np.cumsum(w[np.argsort(s.to_numpy())]) >= w.sum() / 2].iloc[0])
        far = [c for c in cols if med[c] < lo[c] or med[c] > hi[c]]
        for c in far:
            add("out_of_training_range", name, c, m.sum(),
                f"held-out typical value {med[c]:.3g} outside training 1st-99th percentile [{lo[c]:.3g}, {hi[c]:.3g}]")
        # also: columns where 25%+ of the unit's homes sit outside the training 1st-99th percentile
        outside = ((g < lo) | (g > hi)).mul(w, axis=0).sum() / w.sum()
        for c in outside[outside >= 0.25].index:
            if c not in far:
                add("out_of_training_range", name, c, m.sum(),
                    f"{outside[c]:.0%} of the unit's home-years have values outside training 1st-99th percentile "
                    f"[{lo[c]:.3g}, {hi[c]:.3g}]")
    return pd.DataFrame(out)


# ---------------------------------------------------------------------------
# Wisconsin (only for a method that passes; PREDICTIVE_PLAN section 8)
# ---------------------------------------------------------------------------

def wisconsin(panel, feats, method: str, adopted_central: float) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    import run_pooled_regression as rp
    import run_pooled_revision as rr
    d = rp.load()
    wi, base, growth = d["wi"], d["baseline"], d["growth"]
    G = rr.growth_matrix(wi, growth)
    wf = pd.read_parquet(OUT / "wi_features.parquet").set_index("geo")
    geo = "cousub:" + wi["area_id"].str.replace("muni:", "", regex=False)
    Fw = wf.reindex(geo).reindex(columns=feats.columns).to_numpy(float)
    Fw = np.where(np.isnan(Fw), np.nanmean(Fw, axis=0), Fw)
    tp = TwoPart(method, SEED).fit(panel, feats.reindex(panel["geo"]).to_numpy(float))
    rws = pd.DataFrame({"local": 0.0, "k": 1.0, "strong": 1.0, "law": 1}, index=range(len(wi)))
    Y = np.column_stack([tp.predict_part(rws, Fw, "law", k_override=min(k, 4), strong_override=1) for k in range(1, 6)])
    add = pr.additional(wi, Y, base, G, per_area_max=True)
    H = wi["homes"].to_numpy(float)
    x = wi["x_rate"].to_numpy(float)
    per_area = (H[:, None] * np.maximum(Y - x[:, None] * G, 0) / 1000).sum(axis=1)
    areas = pd.DataFrame({"area_id": wi["area_id"], "name": wi["name"], "county": wi["parent_county_id"], "homes": H,
                          "current_law_rate": x, "predicted_rate_year1": Y[:, 0], "predicted_rate_year5": Y[:, 4],
                          "additional_2027_2031": per_area})
    county = areas.groupby("county").agg(homes=("homes", "sum"), additional_2027_2031=("additional_2027_2031", "sum")).reset_index()
    county["share_of_state"] = county["additional_2027_2031"] / county["additional_2027_2031"].sum()
    county["additional_at_adopted_central"] = county["share_of_state"] * adopted_central
    stat = {"method": method, "additional_2027_2031": float(add.sum()), "by_year": add.round(1).tolist(),
            "statewide_rate_by_year": ((H[:, None] * Y).sum(axis=0) / H.sum()).round(4).tolist()}
    return areas, county, stat


# ---------------------------------------------------------------------------

def main():
    panel, feats, market = load()
    OUT.mkdir(parents=True, exist_ok=True)
    fl = flags(panel, feats)                      # owner rule: flag before each run, never stop
    fl.to_csv(REFERENCE / "adu_predictive_flags.csv", index=False)
    print(fl.groupby("flag_type").size().to_string())
    if "--reuse" in sys.argv and (OUT / "predictions.parquet").exists():   # rescore saved main-seed predictions
        pred = pd.read_parquet(OUT / "predictions.parquet")
    else:
        pred = run_all(panel, feats, market)
        pred.to_parquet(OUT / "predictions.parquet", index=False)
    cols = list(METHODS) + ["guess_zero"]
    by_unit = score(panel, pred, cols)
    res = judge(by_unit)
    pl = placebo(panel, pred)
    by_unit.round(4).to_csv(REFERENCE / "adu_predictive_by_unit.csv", index=False)
    res.round(4).to_csv(REFERENCE / "adu_predictive_results.csv", index=False)
    pl.round(4).to_csv(REFERENCE / "adu_predictive_placebo.csv", index=False)
    summary = {"rows": int(len(panel)), "features": int(feats.shape[1]),
               "rows_by_cluster": panel.groupby("cluster").size().to_dict(),
               "passes": res[res.get("passes", pd.Series(dtype=bool)).fillna(False).astype(bool)][["test", "method"]].to_dict("records")}
    # current-model log errors on test 1, to compare with the adopted 0.113
    t1 = by_unit[by_unit["test"].eq("1_how_much")]
    summary["test1_rms_log_error"] = {m: float(np.sqrt(np.nanmean(t1[f"log_error__{m}"] ** 2))) for m in METHODS}
    # robustness of any forest / boosting pass
    passing = res[res.get("passes", False).fillna(False).astype(bool)] if "passes" in res else res.iloc[0:0]
    rob = []
    for m in sorted(set(passing["method"]) & {"causal_forest", "boosted_trees"}):
        for s in ROBUST_SEEDS:
            p2 = run_all(panel, feats, market, seed=s, methods=(m,), log=lambda *a, **k: None)   # baselines do not use a seed
            p2 = p2[["row_id", "fold", m]].merge(pred[["row_id", "fold", "plain_average", "current_model"]],
                                                 on=["row_id", "fold"])
            p2["guess_zero"] = 0.0
            r2 = judge(score(panel, p2, ["plain_average", "current_model", m, "guess_zero"]), methods=(m,))
            for r in r2[r2["method"].eq(m)].itertuples():
                rob.append({"method": m, "seed": s, "test": r.test, "mean_miss": r.mean_miss, "passes": r.passes})
    if rob:
        rb = pd.DataFrame(rob)
        rb.to_csv(REFERENCE / "adu_predictive_robustness.csv", index=False)
        summary["robustness"] = rb.groupby(["method", "test"])["passes"].sum().reset_index().to_dict("records")
    # Wisconsin, only for passing methods
    adopted = float(pd.read_csv(REFERENCE / "adu_model_statewide.csv").set_index("path").loc["central", "additional_units"])
    summary["wisconsin"] = []
    for m in sorted(set(passing["method"])):
        areas, county, stat = wisconsin(panel, feats, m, adopted)
        stat["tests_passed"] = passing.loc[passing["method"].eq(m), "test"].tolist()
        county.round(4).to_csv(REFERENCE / f"adu_predictive_wi_by_county_{m}.csv", index=False)
        areas.round(5).to_parquet(OUT / f"wi_areas_{m}.parquet", index=False)
        summary["wisconsin"].append(stat)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(res.round(3).to_string())
    print(json.dumps(summary, indent=1, default=str)[:4000])


if __name__ == "__main__":
    main()
