"""Option D exploration (plan log 2026-11-02 after 16:46): does a model built on reform stops beat the place-based
average? Not a tool change.

Unit: one reform stop-band. Its own measured effect = its change (after minus before, new homes per 100 lot acres a
year, as run_tod_optiond.to_stops) minus the acre-weighted average change of the comparison stop-bands in the same
case and band. Comparison stops are the counterfactual only. Owner 2026-11-02 16:51: no random forest or
causal forest / R-learner on this set yet; benchmarks, the 4-trait linear model and the (cheap) gradient boosting only.

Test: hide all stops of one place, fit on the other 10. Benchmarks per hidden stop: the other places' average stop
effect (each place averaged first, then places equally) and zero. Scores: median absolute error per stop (each
place's stops weighted so each place counts equally), and place totals (acre-weighted mean of predicted stop effects;
New York and Philadelphia averaged over rezonings) vs the measured effect.

Wisconsin: each 1/4-mile stop-band with coverage 0.15; extra homes = effect x lot acres / 100 x 5 x statewide scale.

    .venv/bin/python scripts/run_tod_optiond_stops.py [--rebuild]

The lots are loaded once and the stop-band table cached to data/processed/tod_station_area/optiond_stops_cache.parquet.
Writes reference/tod_optiond_stopmodel_{summary,places,stops}.csv (no parcel ids).
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
import run_tod_optiond as O  # noqa: E402

CACHE = O.L.OUT / "optiond_stops_cache.parquet"
GROUPS = ["lot", "place", "tract"]
LINEAR = ["vacant", "log_land_value_per_acre", "log_homes_per_acre", "sld_transit_job_access"]
SHARE = 0.15
YEARS = 5
BANDS = ["0-1/4", "1/4-1/2"]


def build_cache() -> pd.DataFrame:
    D = O.load(1, tract=True)
    D, med = O.prepare(D, {"fill"})
    lot_cols = [c for c in O.features(D, GROUPS) if c not in O.SWITCHES and c not in O.STOP_FEATS + ["log_dist_m"]]
    D["homes_per_acre"] = (D.homes_existing.clip(lower=0) / D.acres.where(D.acres > 0)).astype("float32")
    cols = lot_cols + ["homes_per_acre"]
    S = O.to_stops(D, cols, {"equal"})
    del D
    W = O.wisconsin_rows(cols, med)
    W["homes_per_acre"] = W.homes_existing.clip(lower=0) / W.acres.where(W.acres > 0)
    WS = O.wisconsin_stops(W, cols)
    del W
    S["wi"], WS["wi"] = False, True
    keep = ["city", "case", "stop_id", "band", "wa", "y", "reform_stop", "coverage", "wi"] + cols
    out = pd.concat([S[keep], WS[keep]], ignore_index=True)
    out["stop_id"] = out.stop_id.astype(str)
    out.attrs["lot_cols"] = lot_cols
    out.to_parquet(CACHE, index=False)
    pd.Series(lot_cols).to_csv(CACHE.with_suffix(".cols.csv"), index=False)
    return out


def wmedian(x: np.ndarray, w: np.ndarray) -> float:
    o = np.argsort(x)
    x, c = np.asarray(x)[o], np.cumsum(np.asarray(w)[o])
    return float(x[np.searchsorted(c, 0.5 * c[-1])])


def place_total(R: pd.DataFrame, col: str) -> pd.Series:
    """Acre-weighted mean over each case's reform stops, then the mean over a place's cases (as measured)."""
    c = (R[col] * R.wa).groupby(R.case).sum() / R.wa.groupby(R.case).sum()
    return c.groupby(R.groupby("case").city.first()).mean()


def equal_w(R: pd.DataFrame) -> pd.Series:
    return R.wa / R.groupby("city").wa.transform("sum") * 1e5


class Linear:
    def __init__(self, cols):
        self.cols = cols

    def fit(self, X, y, w):
        from sklearn.linear_model import LinearRegression
        self.med = X[self.cols].median()
        self.m = LinearRegression().fit(X[self.cols].fillna(self.med), y, sample_weight=w)
        return self

    def predict(self, X):
        return self.m.predict(X[self.cols].fillna(self.med))


def models(lot_cols):
    full = lot_cols + ["coverage"]
    return {
        "gradient_boosting": (lambda: O.Bag(5, 0, min_samples_leaf=20), full),
        "linear_4": (lambda: Linear(LINEAR), LINEAR),
        "linear_4_plus_coverage": (lambda: Linear(LINEAR + ["coverage"]), LINEAR + ["coverage"]),
    }


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args(argv)
    if CACHE.exists() and not a.rebuild:
        C = pd.read_parquet(CACHE)
        lot_cols = pd.read_csv(CACHE.with_suffix(".cols.csv")).iloc[:, 0].tolist()
    else:
        C = build_cache()
        lot_cols = C.attrs["lot_cols"]
    C["log_homes_per_acre"] = np.log1p(C.homes_per_acre)
    lot_cols = lot_cols + ["log_homes_per_acre"]
    S, WS = C[~C.wi].copy(), C[C.wi].copy()
    print(f"stop-band rows {len(S):,} (reform {int(S.reform_stop.sum()):,}); Wisconsin {len(WS):,}; traits {len(lot_cols)}")

    # each reform stop's own measured effect
    cbar = S[S.reform_stop == 0].groupby(["case", "band"]).apply(lambda g: np.average(g.y, weights=g.wa))
    S["cbar"] = [cbar.get((c, b), np.nan) for c, b in zip(S.case, S.band)]
    S["effect"] = S.y - S.cbar
    # the places' measured effects (permit_est, as run_tod_optiond.py), read from its hidden-place test file
    measured = pd.read_csv(REFERENCE / "tod_optiond_loco_lot_place_fix_equal_fill_stops_k5_s1.csv").set_index(
        ["city", "band"])["measured"]
    scale = float(pd.read_csv(REFERENCE / "tod_optiond_line.csv").statewide_scale.iloc[0])
    M = models(lot_cols)

    stops, places, wis = [], [], []
    for band in BANDS:
        R = S[(S.band == band) & (S.reform_stop == 1) & S.effect.notna()].copy()
        Wb = WS[WS.band == band].copy()
        Wb["coverage"] = SHARE if band == "0-1/4" else 0.0
        own = place_total(R, "effect")
        print(f"\n{band}: reform stop-bands {len(R):,}; per place:\n"
              + R.groupby("city").size().to_string())
        print("stop-based place totals vs measured:\n" + pd.DataFrame(
            {"stops": own, "measured": measured.xs(band, level=1).reindex(own.index)}).round(2).to_string())
        P = {k: pd.Series(np.nan, index=R.index) for k in ["others_average", "zero", *M]}
        P["zero"][:] = 0.0
        wb = {k: [] for k in M}
        for city in O.TRAIN:
            tr, te = R[R.city != city], R[R.city == city]
            if te.empty:
                continue
            P["others_average"][te.index] = own.drop(city).mean()
            for k, (mk, cols) in M.items():
                m = mk().fit(tr[cols].astype(float), tr.effect, equal_w(tr))
                P[k][te.index] = m.predict(te[cols].astype(float))
                wb[k].append(float((m.predict(Wb[cols].astype(float)) * Wb.wa).sum() / 100))
            print(city, "done", flush=True)
        # full fits for the Wisconsin central
        central = {}
        for k, (mk, cols) in M.items():
            m = mk().fit(R[cols].astype(float), R.effect, equal_w(R))
            central[k] = float((m.predict(Wb[cols].astype(float)) * Wb.wa).sum() / 100)

        ws = 1.0 / R.groupby("city").city.transform("size")
        out = R[["city", "case", "stop_id", "band", "wa", "coverage", "effect"]].rename(columns={"wa": "lot_acres"})
        for k, v in P.items():
            out[k] = v
        stops.append(out)
        meas_b = measured.xs(band, level=1).reindex(own.index)
        for k, v in P.items():
            tot = place_total(R.assign(_p=v), "_p")
            for city in own.index:
                places.append({"band": band, "method": k, "city": city, "measured": meas_b[city],
                               "stop_reconstructed": own[city], "predicted": tot[city]})
            f = YEARS * scale
            wrow = {"band": band, "method": k, "per_stop_median_error": wmedian((v - R.effect).abs().values, ws.values),
                    "place_total_median_error": float((tot - meas_b).abs().median()),
                    "place_total_median_error_vs_stop_reconstructed": float((tot - own).abs().median()),
                    "wisconsin_acres": float(Wb.wa.sum())}
            if k in central:
                wrow |= {"wisconsin_central": central[k] * f, "wisconsin_low": min(wb[k]) * f,
                         "wisconsin_high": max(wb[k]) * f}
            elif k == "others_average":
                lo = [own.drop(c).mean() for c in own.index]
                wrow |= {"wisconsin_central": own.mean() * Wb.wa.sum() / 100 * f,
                         "wisconsin_low": min(lo) * Wb.wa.sum() / 100 * f, "wisconsin_high": max(lo) * Wb.wa.sum() / 100 * f}
            wis.append(wrow)

    pd.set_option("display.width", 220)
    T = pd.DataFrame(wis).round(2)
    print("\n" + T.to_string(index=False))
    T.to_csv(REFERENCE / "tod_optiond_stopmodel_summary.csv", index=False)
    pd.DataFrame(places).round(3).to_csv(REFERENCE / "tod_optiond_stopmodel_places.csv", index=False)
    pd.concat(stops).round(3).to_csv(REFERENCE / "tod_optiond_stopmodel_stops.csv", index=False)


if __name__ == "__main__":
    main()
