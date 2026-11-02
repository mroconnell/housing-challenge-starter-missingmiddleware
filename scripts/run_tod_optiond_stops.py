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

    .venv/bin/python scripts/run_tod_optiond_stops.py [--rebuild] [--set D-11|D-B]

Evidence sets (owner 18:50): D-11 = the 11 places; D-B = the 8 station-focused places (outputs carry the suffix _db).
Every summary row is labelled "<set>, stop model, <method>". Methods: others' average, zero, gradient boosting on all
lot / block group / tract traits + coverage (5 fits), the same plus stop-table traits (stop_traits(): service, node and
own-system ridership before the reform, form, the band's land; no station-level or post-reform ridership, no grade or
opening year), and the 4-trait linear models. Lot land is acres_land (stacked condo records counted once).

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
# evidence sets (owner 18:50): D-11 = the 11 places of run_tod_optiond.TRAIN; D-B = the 8 station-focused places
SETS = {"D-11": list(O.TRAIN),
        "D-B": ["New York", "austin_2009", "charlotte_2019", "denver_2018", "seattle_mount_baker_2014",
                "seattle_othello_2012", "slc_2010", "stpaul_2011"]}


def build_cache() -> pd.DataFrame:
    D = O.load(1, tract=True)
    D, med = O.prepare(D, {"fill"})
    lot_cols = [c for c in O.features(D, GROUPS) if c not in O.SWITCHES and c not in O.STOP_FEATS + ["log_dist_m"]]
    D["homes_per_acre"] = (D.homes_existing.clip(lower=0) / D.acres_land.where(D.acres_land > 0)).astype("float32")
    cols = lot_cols + ["homes_per_acre"]
    S = O.to_stops(D, cols, {"equal"})
    del D
    W = O.wisconsin_rows(cols, med)
    W["homes_per_acre"] = W.homes_existing.clip(lower=0) / W.acres_land.where(W.acres_land > 0)
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


# stop-table traits (reference/tod_stop_table.csv, owner 18:24): service, form, and the band's land and setting. Left
# out: station-level and post-reform ridership, grade and opening year (thin coverage; the extra-traits file is used
# only for traits with >= 80% coverage of reform stops, and its ridership columns are never used).
# Band-specific columns take the stop-band's own band (q1 = 0-1/4, q2 = 1/4-1/2; _q / _h = within 1/4 / 1/2 mile).
STOP_NUM = ["tph_peak", "tph_midday", "sld_d4c_station_bg", "n_points_merged", "footprint_m", "n_names_merged",
            # ridership (owner via coordinator): the station's own system, NTD unlinked trips, 5-year average before the
            # reform, and node totals; no station-level or post-reform ridership
            "own_system_upt_pre5_avg", "system_upt_pre5_sum_all", "n_systems_at_node", "transfer_hub",
            "trips_peak_all_systems", "trips_midday_all_systems"]
STOP_BAND = ["dev_acres_dedup", "vacant_dev_acres_dedup", "underused_dev_acres_dedup", "acres_dedup"]
STOP_QH = ["homes_per_acre", "median_land_value_per_acre", "jobs_per_acre", "transit_job_access", "share_lots_vacant"]
MODES = ["heavy rail", "light rail", "light rail/trolley", "streetcar", "commuter rail", "BRT"]
EXTRA = REFERENCE / "tod_stop_extra_traits.csv"   # another helper's added station traits, used where >= 80% coverage
EXTRA_NUM = ["opening_year_best", "opening_after_reform"]


def stop_traits(C: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    T = pd.read_csv(REFERENCE / "tod_stop_table.csv", low_memory=False)
    T["stop_id"] = T.stop_id.astype(str)
    T = T.drop_duplicates(["case", "stop_id"]).set_index(["case", "stop_id"])
    k = pd.MultiIndex.from_arrays([C.case, C.stop_id.astype(str)])
    q = (C.band == "0-1/4").values
    out, cols = {}, []
    for c in STOP_NUM:
        out["st_" + c] = T[c].reindex(k).astype(float).values
    for c in STOP_BAND:
        out["st_" + c] = np.where(q, T[c + "_q1"].reindex(k).values, T[c + "_q2"].reindex(k).values).astype(float)
    for c in STOP_QH:
        out["st_" + c] = np.where(q, T[c + "_q"].reindex(k).values, T[c + "_h"].reindex(k).values).astype(float)
    md = T["mode"].reindex(k).values
    for m in MODES:
        out["st_mode_" + m.replace(" ", "_").replace("/", "_")] = (md == m).astype(float)
    if EXTRA.exists():   # keyed by case and stop_key; joined to stop_id through the stop table
        X = pd.read_csv(EXTRA, low_memory=False)
        key = T.reset_index()[["case", "stop_id", "stop_key"]]
        X = X.merge(key, on=["case", "stop_key"], how="inner").drop_duplicates(["case", "stop_id"]).set_index(["case", "stop_id"])
        R = C[(~C.wi) & (C.reform_stop == 1)]
        kr = pd.MultiIndex.from_arrays([R.case, R.stop_id.astype(str)]).unique()
        for c in EXTRA_NUM:
            if c in X and X[c].reindex(kr).notna().mean() >= 0.8:
                out["sx_" + c] = pd.to_numeric(X[c].reindex(k), errors="coerce").values
        if "grade_best" in X:
            g = X["grade_best"].where(X["grade_best"] != "unknown")
            if g.reindex(kr).notna().mean() >= 0.8:
                gk = g.reindex(k).values
                for v in sorted(g.dropna().unique()):
                    out["sx_grade_" + str(v).replace(" ", "_")] = np.where(pd.isna(gk), np.nan, (gk == v).astype(float))
    D = pd.DataFrame(out, index=C.index)
    return D, list(D.columns)


def models(lot_cols, st_cols=()):
    full = lot_cols + ["coverage"]
    return {
        "gradient_boosting": (lambda: O.Bag(5, 0, min_samples_leaf=20), full),
        "gradient_boosting_plus_stop_traits": (lambda: O.Bag(5, 0, min_samples_leaf=20), full + list(st_cols)),
        "linear_4": (lambda: Linear(LINEAR), LINEAR),
        "linear_4_plus_coverage": (lambda: Linear(LINEAR + ["coverage"]), LINEAR + ["coverage"]),
    }


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--set", default="D-11", choices=list(SETS))
    a = ap.parse_args(argv)
    set_places = SETS[a.set]
    suffix = "" if a.set == "D-11" else "_" + a.set.replace("-", "").lower()
    if CACHE.exists() and not a.rebuild:
        C = pd.read_parquet(CACHE)
        lot_cols = pd.read_csv(CACHE.with_suffix(".cols.csv")).iloc[:, 0].tolist()
    else:
        C = build_cache()
        lot_cols = C.attrs["lot_cols"]
    C["log_homes_per_acre"] = np.log1p(C.homes_per_acre)
    lot_cols = lot_cols + ["log_homes_per_acre"]
    ST, st_cols = stop_traits(C)
    C = pd.concat([C, ST], axis=1)
    print(f"stop-table traits ({len(st_cols)}): {st_cols}")
    S, WS = C[~C.wi & C.city.isin(set_places)].copy(), C[C.wi].copy()
    print(f"stop-band rows {len(S):,} (reform {int(S.reform_stop.sum()):,}); Wisconsin {len(WS):,}; traits {len(lot_cols)}")

    # each reform stop's own measured effect
    cbar = S[S.reform_stop == 0].groupby(["case", "band"]).apply(lambda g: np.average(g.y, weights=g.wa))
    S["cbar"] = [cbar.get((c, b), np.nan) for c, b in zip(S.case, S.band)]
    S["effect"] = S.y - S.cbar
    # the places' measured effects (permit_est, as run_tod_optiond.py)
    # (computed here from the current lots and hand-check rows, as run_tod_optiond.main_stops does)
    measured = O.M.city_level(O.M.case_effects("permit_est")).set_index(["city", "band"])["effect_per_100_acres"]
    scale = float(pd.read_csv(REFERENCE / "tod_optiond_line.csv").statewide_scale.iloc[0])
    M = models(lot_cols, st_cols)

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
        for city in set_places:
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
                places.append({"set": a.set, "band": band, "method": k, "city": city, "measured": meas_b[city],
                               "stop_reconstructed": own[city], "predicted": tot[city]})
            f = YEARS * scale
            wrow = {"label": f"{a.set}, stop model, {k}", "set": a.set, "band": band, "method": k, "per_stop_median_error": wmedian((v - R.effect).abs().values, ws.values),
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
    T.to_csv(REFERENCE / f"tod_optiond_stopmodel_summary{suffix}.csv", index=False)
    pd.DataFrame(places).round(3).to_csv(REFERENCE / f"tod_optiond_stopmodel_places{suffix}.csv", index=False)
    pd.concat(stops).round(3).to_csv(REFERENCE / f"tod_optiond_stopmodel_stops{suffix}.csv", index=False)


if __name__ == "__main__":
    main()
