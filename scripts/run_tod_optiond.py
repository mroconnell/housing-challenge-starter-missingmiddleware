"""Option D, the transit district mandate (docs/tod/OPTION_D_PLAN.md; owner decisions 2026-11-02 10:45).

The law: every Wisconsin city with qualifying rail or rapid-bus stops zones a by-right multifamily district covering
15% of the lot acres within 1/4 mile of those stops. No site is picked: the district is treated as spread at random
over the 1/4-mile land, so each lot there is in the district with probability 0.15 and the answer is the expected
extra homes (a density in the radius, owner 2026-11-02).

Training: the 11 places whose reform covered under 30% of the lots within 1/4 mile (reform minus comparison
coverage): New York, Philadelphia, Austin, Charlotte, Chicago 2015, Denver, Portland 2020, Seattle Mount Baker,
Seattle Othello, Salt Lake City, Saint Paul. Lot rows as in scripts/run_tod_station_lotmodel.py (near-all lots:
every lot outside New York and Philadelphia, their reform lots, one fixed comparison set per seed).

Test (place is the unit): hide one place, fit on the other 10, predict its measured effect per 100 lot acres a year
by band; compare the median absolute error with two benchmark rules: zero, and the other places' average measured
effect. Steadiness: each fit is the average of K gradient-boosting fits with different seeds and no random early
stopping.

    uv run --all-extras python scripts/run_tod_optiond.py --trait-groups lot [--k 5] [--share 0.15] [--tag name]
        [--learner gb|rf|cf|cf_honest] [--level lot|stop] [--max-samples 0.3]

Learners (owner question 2026-11-02 14:25, plan log): gb = gradient boosting (default, as before); rf = random forest,
same on/off effect; cf / cf_honest = a causal forest at stop level built from scikit-learn only (no EconML, licence
rule), as methods 9/10 of scripts/run_tod_model_menu.py.
Writes reference/tod_optiond_loco_<tag>.csv (hidden-place test) and reference/tod_optiond_wisconsin_<tag>.csv.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import REFERENCE  # noqa: E402
import run_tod_station_lotmodel as L  # noqa: E402
import run_tod_station_model as M  # noqa: E402

TRAIN = ["New York", "Philadelphia", "austin_2009", "charlotte_2019", "chicago_2015", "denver_2018", "portland_2020",
         "seattle_mount_baker_2014", "seattle_othello_2012", "slc_2010", "stpaul_2011"]
SHARE = 0.15
HOMES_HALF_MILE_STATE, HOMES_HALF_MILE_MKE_MAD = 89_528, 80_930   # as scripts/build_tod_station_area_line.py
SWITCHES = ("reform_stop", "in_reform_area", "coverage", "strings_attached", "mandate")


def mandate_of() -> dict:
    c = pd.read_csv(REFERENCE / "tod_inclusionary_coding.csv")
    return dict(zip(c.case_id, c.mandate_in_window.eq("yes").astype(float)))


def load(seed: int, tract: bool) -> pd.DataFrame:
    mand = mandate_of()
    rng = np.random.default_rng(seed)
    parts = []
    for f in sorted(L.OUT.glob("lots_*.parquet")):
        case = f.stem.removeprefix("lots_")
        if M.city_of(case) not in TRAIN:
            continue
        d = L.load_case(case, "permit_est", rng, "full", seed, tract=tract)
        if d is None:
            continue
        key = M.city_of(case) if M.city_of(case) in ("New York", "Philadelphia") else case
        d["mandate"] = np.float32(mand.get(key, 0.0)) * d.reform_stop
        parts.append(d)
    return pd.concat(parts, ignore_index=True)


def features(D: pd.DataFrame, groups: list[str]) -> list[str]:
    cols = L.features(D, [g for g in groups if g != "mandate"])
    if "mandate" in groups:
        cols.append("mandate")
    return cols


FILL_COLS = ["log_land_value_per_acre", "land_value_rank_in_case", "bldg_to_land", "building_age"]


def prepare(D: pd.DataFrame, fixes: set[str]) -> tuple[pd.DataFrame, dict]:
    """Round-2 fixes (plan log 2026-11-02):
    fill   - lot traits missing for a whole place (Austin: no land values; Philadelphia: no year built) are filled with
             the median over all training lots, so a hidden place with a gap is not sent down a branch learned from
             some other place's gap;
    equal  - each place gets the same total weight (the place is the unit of the test; New York and Philadelphia had
             about 95% of the weight); within a place, lot weights keep their ratios."""
    D = D.copy()
    med = {}
    if "fill" in fixes:
        for c in FILL_COLS:
            med[c] = float(np.nanmedian(D[c].astype(float)))
            D[c] = D[c].fillna(med[c])
    if "equal" in fixes:
        D["w"] = D.w / D.groupby("city").w.transform("sum") * 1e5
    return D, med


class Bag:
    """Average of K gradient-boosting fits (seeds 1..K), all 300 rounds (no random early stopping)."""

    def __init__(self, k: int, offset: int = 0, min_samples_leaf: int = 200, **kw):
        self.k, self.offset, self.leaf, self.kw = k, offset, min_samples_leaf, kw

    def fit(self, X, y, w):
        from sklearn.ensemble import HistGradientBoostingRegressor
        self.m = [HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, min_samples_leaf=self.leaf,
                                                early_stopping=False, random_state=s, **self.kw).fit(X, y, sample_weight=w)
                  for s in range(1 + self.offset, self.k + 1 + self.offset)]
        return self

    def predict(self, X):
        return np.mean([m.predict(X) for m in self.m], axis=0)


class Forest:
    """Average of K random forests (seeds 1..K), 300 trees each; gaps filled with the training medians.
    `max_samples` = share of rows drawn for each tree."""

    def __init__(self, k: int, offset: int = 0, min_samples_leaf: int = 50, max_samples: float = 0.3):
        self.k, self.offset, self.leaf, self.ms = k, offset, min_samples_leaf, max_samples

    def _fill(self, X):
        return X.fillna(self.med).replace([np.inf, -np.inf], 0.0)

    def fit(self, X, y, w):
        from sklearn.ensemble import RandomForestRegressor
        self.med = X.median().fillna(0.0)
        Z = self._fill(X)
        self.m = [RandomForestRegressor(n_estimators=300, min_samples_leaf=self.leaf, max_samples=self.ms, n_jobs=-1,
                                        random_state=s).fit(Z, y, sample_weight=w)
                  for s in range(1 + self.offset, self.k + 1 + self.offset)]
        return self

    def predict(self, X):
        Z = self._fill(X)
        return np.mean([m.predict(Z) for m in self.m], axis=0)


def make_model(a, level: str):
    """The outcome model for the on/off effect: gradient boosting (as before) or a random forest."""
    if a.learner == "rf":
        return Forest(a.k, a.bag_offset, min_samples_leaf=50 if level == "stop" else 200, max_samples=a.max_samples)
    return Bag(a.k, a.bag_offset, min_samples_leaf=20) if level == "stop" else Bag(a.k, a.bag_offset)


CF_SEED = 20261102


class CausalForest:
    """Causal forest without EconML (licence rule), as dml_forest() in scripts/run_tod_model_menu.py:
    1. cross-fitted (3 folds) outcome model m(x) = E[y | x] and treatment model e(x) = P(reform stop | x);
    2. residuals y - m and t - e;
    3. a random forest fitted to (y - m) / (t - e) with weights w (t - e)^2 (the R-learner) gives the effect tau(x).
    honest: half the rows grow the trees, the other half re-estimates each leaf's effect."""

    def __init__(self, honest: bool, min_samples_leaf: int = 20, seed: int = CF_SEED):
        self.honest, self.leaf, self.seed = honest, min_samples_leaf, seed

    def fit(self, X, y, t, w):
        from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor, RandomForestRegressor
        from run_tod_model_menu import _SkForest, honest_leaves
        self.med = X.median().fillna(0.0)
        Z = X.fillna(self.med).to_numpy(dtype=float)
        y, t, w = np.asarray(y, float), np.asarray(t, int), np.asarray(w, float)
        fold = np.random.default_rng(self.seed).integers(0, 3, len(y))
        m_hat, e_hat = np.zeros(len(y)), np.zeros(len(y))
        for f in range(3):
            tr, te = fold != f, fold == f
            m_hat[te] = HistGradientBoostingRegressor(random_state=self.seed).fit(Z[tr], y[tr], sample_weight=w[tr]).predict(Z[te])
            e_hat[te] = HistGradientBoostingClassifier(random_state=self.seed).fit(
                Z[tr], t[tr], sample_weight=w[tr]).predict_proba(Z[te])[:, 1]
        e_hat = np.clip(e_hat, 0.02, 0.98)
        ry, rt = y - m_hat, t - e_hat
        rf = RandomForestRegressor(n_estimators=400, min_samples_leaf=self.leaf, max_samples=0.3, n_jobs=-1,
                                   random_state=self.seed)
        if not self.honest:
            self.f = _SkForest(rf.fit(Z, ry / rt, sample_weight=w * rt ** 2))
            return self
        half = np.random.default_rng(self.seed + 1).random(len(y)) < 0.5
        rf.fit(Z[half], (ry / rt)[half], sample_weight=(w * rt ** 2)[half])
        self.f = _SkForest(rf, honest_leaves(rf, Z[~half], ry[~half], rt[~half], w[~half]))
        return self

    def effect(self, X):
        return self.f.effect(X.fillna(self.med).to_numpy(dtype=float))


class ClusterCausalForest:
    """Stabilised honest causal forest (plan log 2026-11-02 21:04, owner exploration), scikit-learn trees only, built
    the way grf's causal_forest does with `clusters` (cluster = place):
    - nuisances m(x) = E[y | x] and e(x) = P(reform stop | x) cross-fitted over 3 folds of whole places;
    - each of `n_trees` trees draws half of the places (whole places, not stops); of those, a `honesty` share of the
      places grows the tree on the R-learner pseudo-outcome (y - m) / (t - e) with weights w (t - e)^2, and the other
      places re-estimate each leaf's effect, tau = sum w (t - e)(y - m) / sum w (t - e)^2;
    - a prediction averages the honest leaf effects over the trees whose leaf the estimating places reached;
    - out-of-bag effects (trees that did not draw the row's place) feed the doubly robust averages and the calibration
      test (diagnostics())."""

    def __init__(self, seed: int, n_trees: int = 2000, min_samples_leaf: int = 40, honesty: float = 0.3,
                 sample_fraction: float = 0.5, per_place: int | None = None, max_features=None, oob: bool = True):
        self.seed, self.n, self.leaf, self.hon, self.frac = seed, n_trees, min_samples_leaf, honesty, sample_fraction
        self.per_place, self.mf, self.oob = per_place, max_features, oob

    def fit(self, X, y, t, w, g):
        from joblib import Parallel, delayed
        from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
        from sklearn.tree import DecisionTreeRegressor
        self.med = X.median().fillna(0.0)
        Z = X.fillna(self.med).to_numpy(dtype=float)
        y, t, w, g = np.asarray(y, float), np.asarray(t, int), np.asarray(w, float), np.asarray(g)
        rng = np.random.default_rng(self.seed)
        places = np.unique(g)
        pf = dict(zip(places, rng.permutation(len(places)) % 3))
        fold = np.array([pf[x] for x in g])
        m_hat, e_hat = np.zeros(len(y)), np.zeros(len(y))
        for f in range(3):
            tr, te = fold != f, fold == f
            m_hat[te] = HistGradientBoostingRegressor(random_state=self.seed).fit(Z[tr], y[tr], sample_weight=w[tr]).predict(Z[te])
            e_hat[te] = HistGradientBoostingClassifier(random_state=self.seed).fit(
                Z[tr], t[tr], sample_weight=w[tr]).predict_proba(Z[te])[:, 1]
        e_hat = np.clip(e_hat, 0.02, 0.98)
        ry, rt = y - m_hat, t - e_hat
        k = max(2, int(round(self.frac * len(places))))
        n_grow = max(1, int(round(self.hon * k)))
        draws = []
        for _ in range(self.n):
            pick = rng.choice(places, size=k, replace=False)
            draws.append((pick[:n_grow], pick[n_grow:], int(rng.integers(2 ** 31 - 1))))
        pseudo, pw = ry / rt, w * rt ** 2
        rows_of = {p: np.flatnonzero(g == p) for p in places}

        def take(ps, r):
            """Rows of places ps; at most per_place rows from each (grf's samples_per_cluster), place weights kept."""
            out = []
            for p in ps:
                ix = rows_of[p]
                out.append(ix if not self.per_place or len(ix) <= self.per_place
                           else r.choice(ix, self.per_place, replace=False))
            return np.concatenate(out)

        def one(grow, est, rs):
            r = np.random.default_rng(rs)
            gi, ei = take(grow, r), take(est, r)
            tree = DecisionTreeRegressor(min_samples_leaf=self.leaf, max_features=self.mf, random_state=rs).fit(
                Z[gi], pseudo[gi], sample_weight=pw[gi])
            n = tree.tree_.node_count
            le = tree.apply(Z[ei])
            num = np.bincount(le, weights=(w * rt * ry)[ei], minlength=n)
            den = np.bincount(le, weights=pw[ei], minlength=n)
            val = np.full(n, np.nan)
            val[den > 0] = num[den > 0] / den[den > 0]
            return tree, val

        self.trees = Parallel(n_jobs=4, prefer="threads")(delayed(one)(*d) for d in draws)
        self.draws = draws
        self.y, self.t, self.w, self.g, self.m_hat, self.e_hat = y, t, w, g, m_hat, e_hat
        if not self.oob:
            return self
        # out-of-bag effects for the training rows
        acc, cnt = np.zeros(len(y)), np.zeros(len(y))
        for (tree, val), (grow, est, _) in zip(self.trees, draws):
            oob = ~np.isin(g, np.concatenate([grow, est]))
            v = val[tree.apply(Z[oob])]
            ok = np.isfinite(v)
            idx = np.flatnonzero(oob)[ok]
            acc[idx] += v[ok]; cnt[idx] += 1
        self.tau_oob = np.where(cnt > 0, acc / np.maximum(cnt, 1), np.nan)
        return self

    def effect(self, X):
        Z = X.fillna(self.med).to_numpy(dtype=np.float32)
        acc, cnt = np.zeros(len(Z)), np.zeros(len(Z))
        for tree, val in self.trees:
            v = val[tree.apply(Z)]
            ok = np.isfinite(v)
            acc[ok] += v[ok]; cnt[ok] += 1
        return np.where(cnt > 0, acc / np.maximum(cnt, 1), np.nan)

    def diagnostics(self, n_boot: int = 2000) -> dict:
        """Doubly robust (AIPW) average effects with a place-bootstrap interval, and grf's calibration test."""
        from scipy import stats
        ok = np.isfinite(self.tau_oob)
        y, t, w, g, m, e, tau = (x[ok] for x in (self.y, self.t, self.w, self.g, self.m_hat, self.e_hat, self.tau_oob))
        ry, rt = y - m, t - e
        ate_score = tau + rt / (e * (1 - e)) * (ry - rt * tau)          # = grf's AIPW score, target "all"
        mu0 = m - e * tau
        att_num = t * (y - mu0) - (1 - t) * e / (1 - e) * (y - mu0)      # grf's target "treated"
        places = np.unique(g)
        idx = {p: np.flatnonzero(g == p) for p in places}
        rng = np.random.default_rng(self.seed + 7)
        ate = float(np.sum(w * ate_score) / np.sum(w)); att = float(np.sum(w * att_num) / np.sum(w * t))
        bs_ate, bs_att = [], []
        for _ in range(n_boot):
            ii = np.concatenate([idx[p] for p in rng.choice(places, size=len(places), replace=True)])
            bs_ate.append(np.sum(w[ii] * ate_score[ii]) / np.sum(w[ii]))
            bs_att.append(np.sum(w[ii] * att_num[ii]) / max(np.sum(w[ii] * t[ii]), 1e-12))
        # calibration: regress y - m on mean.forest.prediction and differential.forest.prediction (no intercept)
        tbar = float(np.sum(w * tau) / np.sum(w))
        A = np.column_stack([tbar * rt, (tau - tbar) * rt])
        WA = A * w[:, None]
        bread = np.linalg.pinv(A.T @ WA)
        beta = bread @ (WA.T @ ry)
        u = ry - A @ beta
        meat = np.zeros((2, 2))
        for p in places:
            s_ = (WA[g == p] * u[g == p, None]).sum(0)
            meat += np.outer(s_, s_)
        G = len(places)
        V = G / (G - 1) * bread @ meat @ bread
        se = np.sqrt(np.diag(V))
        tst = beta / se
        p1 = stats.t.sf(tst, df=G - 1)                                     # one-sided, H0: coefficient <= 0
        return {"aipw_ate": ate, "aipw_ate_lo": float(np.percentile(bs_ate, 2.5)), "aipw_ate_hi": float(np.percentile(bs_ate, 97.5)),
                "aipw_att": att, "aipw_att_lo": float(np.percentile(bs_att, 2.5)), "aipw_att_hi": float(np.percentile(bs_att, 97.5)),
                "calib_mean_coef": beta[0], "calib_mean_se": se[0], "calib_mean_p_gt0": p1[0],
                "calib_mean_p_ne1": float(2 * stats.t.sf(abs((beta[0] - 1) / se[0]), df=G - 1)),
                "calib_diff_coef": beta[1], "calib_diff_se": se[1], "calib_diff_p_gt0": p1[1],
                "rows_with_oob_effect": int(ok.sum()), "rows": int(len(ok)), "places": G}


def wisconsin_rows(cols: list[str], med: dict | None = None) -> pd.DataFrame:
    W = L.wisconsin_rows()
    W["mandate"] = 0.0   # option D: by right, no affordability requirement
    for c, v in (med or {}).items():
        W[c] = W[c].fillna(v)
    return W


def wisconsin_extra(model, W: pd.DataFrame, cols: list[str], share: float) -> pd.Series:
    """Expected extra homes a year by band when a random `share` of the 1/4-mile lot land is in the district."""
    X = W[cols].astype(float)
    off = X.copy()
    off[[c for c in SWITCHES if c in cols]] = 0.0
    q = (W.band == "0-1/4").values
    base = model.predict(off)
    on = X.copy()
    on["reform_stop"] = 1.0
    if "coverage" in cols:
        on["coverage"] = np.where(q, share, 0.0)
    if "in_reform_area" in cols:
        in1 = on.copy(); in1["in_reform_area"] = np.where(q, 1.0, 0.0)
        in0 = on.copy(); in0["in_reform_area"] = 0.0
        exp = np.where(q, share * model.predict(in1) + (1 - share) * model.predict(in0), model.predict(in0))
    else:
        exp = model.predict(on)
    return pd.Series(exp - base, index=W.index).groupby(W.band).sum()


STOP_FEATS = ["reform_stop", "coverage", "band_q", "band_h", "log_stop_acres"]


def to_stops(D: pd.DataFrame, lot_cols: list[str], fixes: set[str]) -> pd.DataFrame:
    """Round 3 (plan log): one row per stop and band. Target: change in new homes per 100 lot acres a year (after
    window minus before window), as the measured effect is built; row weight: lot acres (each place equal if `equal`).
    Features: reform stop, coverage, band, log of the band's lot acres, and acre-weighted means of the lot traits."""
    D = D.copy()
    D["wa"] = D.w * D.acres_land.fillna(0).clip(lower=0)      # land counted once (scripts/fix_tod_station_acres.py)
    D["d_homes"] = D.w * (D.y - D.rate_before)
    g = D.groupby(["city", "case", "stop_id", "band"], sort=False)
    if "mandate" not in D:
        D["mandate"] = 0.0
    S = g.agg(wa=("wa", "sum"), d_homes=("d_homes", "sum"), reform_stop=("reform_stop", "max"),
              coverage=("coverage", "max"), mandate=("mandate", "max")).reset_index()
    for c in lot_cols:
        D["_x"] = D[c].astype(float) * D.wa
        D["_n"] = D.wa.where(D[c].notna(), 0.0)
        t = D.groupby(["city", "case", "stop_id", "band"], sort=False)[["_x", "_n"]].sum().reset_index(drop=True)
        S[c] = (t._x / t._n.where(t._n > 0)).values
    S = S[S.wa > 0].copy()
    S["y"] = 100 * S.d_homes / S.wa
    S["band_q"], S["band_h"] = (S.band == "0-1/4").astype(float), (S.band == "1/4-1/2").astype(float)
    S["log_stop_acres"] = np.log(S.wa / S.groupby("case").wa.transform("count").clip(lower=1) + 0.01)
    S["w"] = S.wa / S.groupby("city").wa.transform("sum") * 1e5 if "equal" in fixes else S.wa
    return S


def stop_effect(model, S: pd.DataFrame, cols: list[str]) -> pd.Series:
    R = S[S.reform_stop == 1]
    off = R[cols].astype(float).copy(); off[[c for c in ("reform_stop", "coverage", "mandate") if c in cols]] = 0.0
    d = (model.predict(R[cols].astype(float)) - model.predict(off)) * R.wa
    return d.groupby(R.band).sum() / R.wa.groupby(R.band).sum()


def wisconsin_stops(W: pd.DataFrame, lot_cols: list[str]) -> pd.DataFrame:
    W = W.copy()
    W["w"], W["y"], W["city"] = 1.0, 0.0, "Wisconsin"
    W["rate_before"] = 0.0
    S = to_stops(W, lot_cols, set())
    return S


def wisconsin_stop_extra(model, S: pd.DataFrame, cols: list[str], share: float) -> pd.Series:
    off = S[cols].astype(float).copy(); off[[c for c in ("reform_stop", "coverage", "mandate") if c in cols]] = 0.0
    on = S[cols].astype(float).copy(); on["reform_stop"] = 1.0
    if "mandate" in cols:
        on["mandate"] = 0.0   # option D: by right
    on["coverage"] = np.where(S.band == "0-1/4", share, 0.0)
    return ((model.predict(on) - model.predict(off)) * S.wa / 100).groupby(S.band).sum()


def main_stops(a, groups, fixes) -> None:
    D, med = prepare(load(a.seed, "tract" in groups), fixes - {"equal"})
    lot_cols = [c for c in features(D, groups) if c not in SWITCHES and c not in STOP_FEATS + ["log_dist_m"]]
    S = to_stops(D, lot_cols, fixes)
    cols = STOP_FEATS + (["mandate"] if "mandate" in groups else []) + lot_cols
    print(f"stop-band rows {len(S):,}; places {S.city.nunique()}; features {cols}")
    measured = M.city_level(M.case_effects("permit_est")).set_index(["city", "band"])["effect_per_100_acres"]
    measured = measured[measured.index.get_level_values(0).isin(TRAIN)]
    WS = wisconsin_stops(wisconsin_rows(cols, med), lot_cols)
    rows, wi = [], []
    for city in TRAIN:
        tr, te = S[S.city != city], S[S.city == city]
        m = make_model(a, "stop").fit(tr[cols].astype(float), tr.y, tr.w)
        wi.append(wisconsin_stop_extra(m, WS, cols, a.share).rename(f"without {city}"))
        for band, v in stop_effect(m, te, cols).items():
            others = measured.drop(index=city, level=0, errors="ignore").xs(band, level=1).mean()
            rows.append({"city": city, "band": band, "measured": measured.get((city, band), np.nan), "model": v,
                         "others_average": others})
    finish(a, rows, wi, make_model(a, "stop").fit(S[cols].astype(float), S.y, S.w),
           lambda m: wisconsin_stop_extra(m, WS, cols, a.share), groups, fixes | {"stops"})


def learner_tag(a) -> str:
    """Output-name suffix for the learners added 2026-11-02 (gradient-boosting names unchanged)."""
    if a.learner == "gb":
        return ""
    return (f"_{a.learner}" + (f"_ms{a.max_samples:g}" if a.learner == "rf" and a.max_samples != 0.3 else "")
            + (f"_cs{a.cf_seed}" if a.learner.startswith("cf") and a.cf_seed != CF_SEED else "")
            + (f"_t{a.cf_trees}_l{a.cf_leaf}_h{a.cf_honesty:g}" if a.learner == "cf_stable" else "")
            + ("_q" if a.learner.startswith("cf") and a.cf_bands == "0-1/4" else ""))


def main_cf(a, groups, fixes) -> None:
    """Causal forest at stop level (plan log 2026-11-02 after 14:25). One forest per band (coverage exists only at
    reform stops, so it is not a trait; the 1/4-mile forest gives the effect of a district like the training places').
    Treatment = reform stop; outcome = change in new homes per 100 lot acres a year; traits = acre-weighted trait means.
    Rows weighted by lot acres, each place the same total weight within a band. Hidden place = acre-weighted effect
    over its reform stops; Wisconsin = effect x lot acres / 100 over every Wisconsin stop in the band."""
    D, med = prepare(load(a.seed, "tract" in groups), fixes - {"equal"})
    lot_cols = [c for c in features(D, groups) if c not in SWITCHES and c not in STOP_FEATS + ["log_dist_m"]]
    S = to_stops(D, lot_cols, fixes)
    del D
    print(f"stop-band rows {len(S):,}; places {S.city.nunique()}; traits {len(lot_cols)}: {lot_cols}")
    print(S.groupby(["band", "reform_stop"]).size().unstack().to_string())
    measured = M.city_level(M.case_effects("permit_est")).set_index(["city", "band"])["effect_per_100_acres"]
    measured = measured[measured.index.get_level_values(0).isin(TRAIN)]
    WS = wisconsin_stops(wisconsin_rows(lot_cols, med), lot_cols)
    honest = a.learner == "cf_honest"
    seeds = [int(x) for x in a.cf_seeds.split(",")] if a.cf_seeds else [a.cf_seed]
    for seed in seeds:     # one data load for every seed (seed-variance test, plan log 2026-11-02 17:10)
        a.cf_seed = seed
        print(f"--- causal forest seed {seed}", flush=True)
        cf_one_seed(a, S, WS, lot_cols, measured, honest, groups, fixes)


def cf_one_seed(a, S, WS, lot_cols, measured, honest, groups, fixes) -> None:
    def fit(Sb):
        w = Sb.wa / Sb.groupby("city").wa.transform("sum") * 1e5 if "equal" in fixes else Sb.wa
        if a.learner == "cf_stable":
            return ClusterCausalForest(a.cf_seed, a.cf_trees, a.cf_leaf, a.cf_honesty).fit(
                Sb[lot_cols].astype(float), Sb.y, Sb.reform_stop, w, Sb.city)
        return CausalForest(honest, a.cf_leaf, a.cf_seed).fit(Sb[lot_cols].astype(float), Sb.y, Sb.reform_stop, w)

    def wis(f) -> pd.Series:
        return pd.Series({b: float((f[b].effect(WS.loc[WS.band == b, lot_cols].astype(float))
                                    * WS.loc[WS.band == b, "wa"] / 100).sum()) for b in f})

    bands = [b for b in ("0-1/4", "1/4-1/2", "1/2-1") if b in set(S.band) and (not a.cf_bands or b in a.cf_bands.split(","))]
    rows, wi = [], []
    for city in TRAIN:
        f = {b: fit(S[(S.band == b) & (S.city != city)]) for b in bands}
        wi.append(wis(f).rename(f"without {city}"))
        for b in bands:
            te = S[(S.band == b) & (S.city == city) & (S.reform_stop == 1)]
            if te.empty:
                continue
            v = float(np.average(f[b].effect(te[lot_cols].astype(float)), weights=te.wa))
            others = measured.drop(index=city, level=0, errors="ignore").xs(b, level=1).mean()
            rows.append({"city": city, "band": b, "measured": measured.get((city, b), np.nan), "model": v,
                         "others_average": others})
        print(city, "done", flush=True)
    F = {b: fit(S[S.band == b]) for b in bands}
    full = wis(F)
    tag = finish(a, rows, wi, None, lambda _: full, groups, fixes | {"stops"})
    if a.learner == "cf_stable":
        diag = pd.DataFrame([{"band": b, **F[b].diagnostics()} for b in bands])
        print("\nfull fit, doubly robust averages (extra new homes per 100 lot acres a year) and calibration test:\n"
              + diag.round(3).T.to_string())
        diag.round(4).to_csv(REFERENCE / f"tod_optiond_cfdiag_{tag}.csv", index=False)


def main_cf_lot(a) -> None:
    """Stabilised honest causal forest at LOT level (owner exploration 2026-11-02 21:04, coordinator spec): D-11, the
    1/4-mile band, lot rows from scripts/run_tod_optiond_dml.py's loader (lot + block-group/place + tract traits + the
    stop-table traits of the lot's stop; comparison lots sampled, one fixed NY/PHL set per seed). Outcome: 100 x (new
    homes a year after - before) / land acres; weight: lot weight x land acres, each place the same total. Two
    treatments: "stop" (reform stop; hidden-place prediction = acre-weighted effect over its reform-stop lots) and
    "in_area" (lot in the reform area of a reform stop; prediction = acre-weighted effect over its district lots x its
    district land share). Wisconsin: effect on each Wisconsin 1/4-mile lot x its land / 100 (x 15% for in_area: the law's
    district) x 5 years x statewide scale."""
    import time
    import run_tod_optiond_dml as DML
    band = "0-1/4"
    seeds = [int(x) for x in a.cf_seeds.split(",")] if a.cf_seeds else [a.cf_seed]
    measured = M.city_level(M.case_effects("permit_est")).set_index(["city", "band"])["effect_per_100_acres"]
    measured = measured[measured.index.get_level_values(0).isin(TRAIN)].to_dict()
    ST = DML.stop_traits()
    cases = DML.all_cases()
    many = [c for c in cases if c.startswith(("nyc_", "phl_"))]
    t0 = time.time()
    base = DML.load_cases([c for c in cases if c not in many], 1, [band], ST)
    print(f"loaded other places: {len(base):,} lots, {time.time() - t0:.0f} s", flush=True)
    W = L.wisconsin_rows()
    W = W[W.band == band].merge(ST, on=["case", "stop_id", "band"], how="left")
    scale = DML.SCALE
    for seed in seeds:
        a.cf_seed = seed
        D = DML.finish_rows(pd.concat([base, DML.load_cases(many, seed, [band], ST)], ignore_index=True))
        D = D[D.city.isin(TRAIN)].reset_index(drop=True)
        D["om"] = D.om0 / D.groupby("city").om0.transform("sum") * 1e5
        cols = DML.xcols(D)
        share = DML.district_share(D).to_dict()
        Wx = W.copy()
        for c in DML.O.FILL_COLS + DML.STOP_X:
            if c in Wx:
                Wx[c] = Wx[c].fillna(np.nanmedian(D[c].astype(float)))
        Wx = Wx.reindex(columns=cols).astype(np.float32)
        wland = W.acres_land.astype(float).fillna(0).clip(lower=0).values
        print(f"--- seed {seed}: {len(D):,} lots, {D.city.nunique()} places, {len(cols)} traits, "
              f"Wisconsin {len(Wx):,} lots ({wland.sum():,.0f} land acres)", flush=True)
        X = D[cols].astype(np.float32)

        def fit(mask, tr, oob=False):
            return ClusterCausalForest(seed, a.cf_trees, a.cf_leaf, a.cf_honesty, per_place=a.cf_per_place,
                                       max_features=a.cf_max_features, oob=oob).fit(
                X[mask], D.yy[mask], D[tr][mask], D.om[mask], D.city[mask])

        def wis(f, tr):
            return float((f.effect(Wx) * wland / 100).sum() * (SHARE if tr == "D_in_area" else 1.0) * 5 * scale)

        rows, each, diag = [], [], []
        for tr in ("D_stop", "D_in_area"):
            name = tr.removeprefix("D_")
            F = fit(np.ones(len(D), bool), tr, oob=True)
            d = F.diagnostics()
            diag.append({"seed": seed, "treatment": name, **d, "wisconsin_full": wis(F, tr)})
            print(f"  {name} full fit: AIPW ATT {d['aipw_att']:.2f} ({d['aipw_att_lo']:.2f} to {d['aipw_att_hi']:.2f}); "
                  f"ATE {d['aipw_ate']:.2f}; calibration mean {d['calib_mean_coef']:.2f}, differential "
                  f"{d['calib_diff_coef']:.2f} (p {d['calib_diff_p_gt0']:.3f}); Wisconsin {diag[-1]['wisconsin_full']:,.0f}",
                  flush=True)
            del F
            ws = {"seed": seed, "treatment": name, "full fit": diag[-1]["wisconsin_full"]}
            for h in TRAIN:
                f = fit((D.city != h).values, tr)
                te = (D.city == h).values & (D[tr].values == 1)
                v = float(np.average(f.effect(X[te]), weights=D.om[te]))
                pred = v * (share.get((h, band), np.nan) if name == "in_area" else 1.0)
                meas = measured.get((h, band), np.nan)
                others = np.mean([measured[(p, band)] for p in TRAIN if p != h and (p, band) in measured])
                rows.append({"seed": seed, "treatment": name, "city": h, "band": band, "effect_on_treated": v,
                             "district_share": share.get((h, band), np.nan), "model": pred, "measured": meas,
                             "others_average": others, "err_model": abs(pred - meas), "err_avg": abs(others - meas),
                             "err_zero": abs(meas)})
                ws[f"without {h}"] = wis(f, tr)
                print(f"    hidden {h}: predicted {pred:.1f}, measured {meas:.1f}", flush=True)
            each.append(ws)
            R = pd.DataFrame([r for r in rows if r["treatment"] == name])
            print(f"  {name}: median miss model {R.err_model.median():.2f}, others' average {R.err_avg.median():.2f}, "
                  f"zero {R.err_zero.median():.2f}", flush=True)
        tag = (f"lot_D11_q_t{a.cf_trees}_l{a.cf_leaf}_h{a.cf_honesty:g}_pp{a.cf_per_place}_mf{a.cf_max_features}"
               f"_cs{seed}")
        pd.DataFrame(rows).round(4).to_csv(REFERENCE / f"tod_optiond_cflot_loco_{tag}.csv", index=False)
        pd.DataFrame(each).round(1).to_csv(REFERENCE / f"tod_optiond_cflot_wisconsin_each_{tag}.csv", index=False)
        pd.DataFrame(diag).round(4).to_csv(REFERENCE / f"tod_optiond_cflot_diag_{tag}.csv", index=False)
        del D, X


def finish(a, rows, wi, m, wfun, groups, fixes) -> None:
    R = pd.DataFrame(rows)
    R["err_model"], R["err_avg"], R["err_zero"] = ((R.model - R.measured).abs(), (R.others_average - R.measured).abs(),
                                                   R.measured.abs())
    pd.set_option("display.width", 200)
    print(R.round(2).to_string(index=False))
    med = R.groupby("band")[["err_model", "err_avg", "err_zero"]].median()
    print("\nmedian absolute error by band (extra homes per 100 lot acres a year):\n" + med.round(2).to_string())
    scale = HOMES_HALF_MILE_STATE / HOMES_HALF_MILE_MKE_MAD
    X = pd.concat(wi, axis=1)
    central = wfun(m)
    out = pd.DataFrame({"central": central, "low": X.min(axis=1), "high": X.max(axis=1)})
    out.loc["total"] = out.sum()
    out = (5 * scale * out).round(1)
    print(f"\nWisconsin statewide, extra homes over 5 years, district = {a.share:.0%} of 1/4-mile lot acres:\n"
          + out.to_string())
    tag = a.tag or (a.trait_groups.replace(",", "_") + (f"_fix_{'_'.join(sorted(fixes))}" if fixes else "")
                    + f"_k{a.k}_s{a.seed}" + (f"_o{a.bag_offset}" if a.bag_offset else "") + learner_tag(a))
    R.round(4).to_csv(REFERENCE / f"tod_optiond_loco_{tag}.csv", index=False)
    out.to_csv(REFERENCE / f"tod_optiond_wisconsin_{tag}.csv")
    if a.learner != "gb":   # seed-variance test (plan log 2026-11-02 17:10): every left-out fit and the full fit
        E = pd.concat([X, central.rename("full fit")], axis=1)
        E.loc["total"] = E.sum()
        (5 * scale * E).round(1).to_csv(REFERENCE / f"tod_optiond_wisconsin_each_{tag}.csv")
    return tag


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trait-groups", default="lot")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--seed", type=int, default=1, help="New York / Philadelphia comparison set")
    ap.add_argument("--share", type=float, default=SHARE)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--fixes", default="", help="comma list of round-2 fixes: fill,equal")
    ap.add_argument("--level", default="lot", choices=["lot", "stop"], help="round 3: stop-and-band rows")
    ap.add_argument("--bag-offset", type=int, default=0, help="steadiness check: use fit seeds offset+1..offset+k")
    ap.add_argument("--learner", default="gb", choices=["gb", "rf", "cf", "cf_honest", "cf_stable"],
                    help="gb = gradient boosting (as before); rf = random forest; cf/cf_honest = causal forest (stop level)")
    ap.add_argument("--max-samples", type=float, default=0.3, help="rf: share of rows drawn for each tree")
    ap.add_argument("--cf-seed", type=int, default=CF_SEED, help="causal forest: seed for folds, halves and trees")
    ap.add_argument("--cf-leaf", type=int, default=20, help="causal forest: minimum stop-band rows per leaf")
    ap.add_argument("--cf-seeds", default="", help="comma list: run these causal-forest seeds on one data load")
    ap.add_argument("--cf-bands", default="", help="causal forest: comma list of bands to fit (default all)")
    ap.add_argument("--cf-trees", type=int, default=2000, help="cf_stable: number of trees")
    ap.add_argument("--cf-per-place", type=int, default=0, help="cf_stable lot level: rows drawn per place per tree")
    ap.add_argument("--cf-max-features", type=float, default=None, help="cf_stable: share of traits tried per split")
    ap.add_argument("--cf-honesty", type=float, default=0.3, help="cf_stable: share of drawn places that grow a tree")
    a = ap.parse_args(argv)
    groups = a.trait_groups.split(",") if a.trait_groups else []
    fixes = set(x for x in a.fixes.split(",") if x)
    if a.learner == "cf_stable" and a.level == "lot":
        return main_cf_lot(a)
    if a.learner in ("cf", "cf_honest", "cf_stable"):
        if a.level != "stop":
            ap.error("the causal forest runs at stop level only: add --level stop")
        return main_cf(a, groups, fixes)
    if a.level == "stop":
        return main_stops(a, groups, fixes)
    D, med = prepare(load(a.seed, "tract" in groups), fixes)
    cols = features(D, groups)
    print(f"rows {len(D):,}; places {D.city.nunique()}; features {len(cols)}: {cols}")
    measured = M.city_level(M.case_effects("permit_est")).set_index(["city", "band"])["effect_per_100_acres"]
    measured = measured[measured.index.get_level_values(0).isin(TRAIN)]
    W = wisconsin_rows(cols, med)
    rows, wi = [], []
    for city in TRAIN:
        tr, te = D[D.city != city], D[D.city == city]
        m = make_model(a, "lot").fit(tr[cols].astype(float), tr.y, tr.w)
        wi.append(wisconsin_extra(m, W, cols, a.share).rename(f"without {city}"))
        for band, v in L.effect_by_band(m, te, cols).items():
            others = measured.drop(index=city, level=0, errors="ignore").xs(band, level=1).mean()
            rows.append({"city": city, "band": band, "measured": measured.get((city, band), np.nan), "model": v,
                         "others_average": others})
    R = pd.DataFrame(rows)
    R["err_model"], R["err_avg"], R["err_zero"] = ((R.model - R.measured).abs(), (R.others_average - R.measured).abs(),
                                                   R.measured.abs())
    pd.set_option("display.width", 200)
    print(R.round(2).to_string(index=False))
    med = R.groupby("band")[["err_model", "err_avg", "err_zero"]].median()
    print("\nmedian absolute error by band (extra homes per 100 lot acres a year):\n" + med.round(2).to_string())
    m = make_model(a, "lot").fit(D[cols].astype(float), D.y, D.w)
    scale = HOMES_HALF_MILE_STATE / HOMES_HALF_MILE_MKE_MAD
    full = wisconsin_extra(m, W, cols, a.share)
    X = pd.concat(wi, axis=1)
    out = pd.DataFrame({"central": full, "low": X.min(axis=1), "high": X.max(axis=1)})
    out.loc["total"] = out.sum()
    out = (5 * scale * out).round(1)     # statewide, 2027-2031
    print(f"\nWisconsin statewide, extra homes over 5 years, district = {a.share:.0%} of 1/4-mile lot acres:\n"
          + out.to_string())
    tag = a.tag or (a.trait_groups.replace(",", "_") + (f"_fix_{'_'.join(sorted(fixes))}" if fixes else "")
                      + f"_k{a.k}_s{a.seed}" + (f"_o{a.bag_offset}" if a.bag_offset else "") + learner_tag(a))
    R.round(4).to_csv(REFERENCE / f"tod_optiond_loco_{tag}.csv", index=False)
    out.to_csv(REFERENCE / f"tod_optiond_wisconsin_{tag}.csv")


if __name__ == "__main__":
    main()
