"""Which traits matter, judged on held-out cities (audit section 9; docs/tod/MODEL_MENU_PLAN.md round 4 rule, step 3).

    uv run --all-extras python scripts/run_tod_heldout_importance.py --model pace|share

For each left-out city, the model is fitted on the other cities. Then each trait GROUP is shuffled within the left-out
city's rows, jointly, and the city totals are recomputed. Importance = rise in the registered score:
- pace: median |log(predicted / actual)| of city-window totals over matched rows (chosen cell: forest, leaf 50, no lot size);
- share: median |log| of the calibrated share after (K left out, held at its unshuffled value), gradient boosting.
Writes reference/tod_heldout_importance_{model}.csv.
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
import run_tod_lot_model as L  # noqa: E402
import run_tod_model_menu as M  # noqa: E402

GROUPS = {
    "distance to rail or rapid stop": lambda c: c in ("log_dist_stop", "log_dist_station"),
    "city has no rail or rapid stop": lambda c: c in ("no_rail_rapid",),
    "existing homes on the lot": lambda c: c in ("log_census_homes", "homes_on_lot", "homes_missing"),
    "rents, values, incomes": lambda c: c in ("log_rent", "log_home_value", "log_income", "log_value", "rent_to_cost", "pays_room")
                                        or c.startswith("v_c") or c in ("v_p11_median_income", "v_p12_per_capita_income", "v_p22_median_earnings"),
    "housing stock (age, type, vacancy)": lambda c: c.startswith("v_h"),
    "people (age, households, education, poverty)": lambda c: c.startswith("v_p") and c not in ("v_p11_median_income", "v_p12_per_capita_income", "v_p22_median_earnings"),
    "commuting and cars": lambda c: c.startswith("v_m"),
    "density and tract size": lambda c: c.startswith("v_l"),
    "place's past permit pace and size": lambda c: c in ("place_permits_per_1000_prior", "log_place_homes"),
    "lot size and shape": lambda c: c in ("log_acres", "log_width"),
    "zoning level and change": lambda c: c in ("level_rank_in_city", "rel_gain", "rel_gain_known", "far_now", "far_known", "upzoned"),
    "lot's group in the reform": lambda c: c.startswith("group_") or c in ("in_reform", "no_reform"),
    "building nearby before": lambda c: c in ("built_before", "log_near_before", "log_before5", "log_area_rate_before",
                                              "log_near400_rate_before", "share_upzoned_half_mile", "stops_1mile"),
}


def groups_for(cols) -> dict[str, list[str]]:
    out = {g: [c for c in cols if f(c)] for g, f in GROUPS.items()}
    return {g: v for g, v in out.items() if v}


def shuffle(X: pd.DataFrame, cols: list[str], rng) -> pd.DataFrame:
    Y = X.copy()
    perm = rng.permutation(len(Y))
    Y[cols] = Y[cols].to_numpy()[perm]
    return Y


def run_pace() -> pd.DataFrame:
    import run_tod_pace_loop as P
    M.LEAF = 50
    D = pd.read_parquet(L.OUT / "lots_rebuilt_halfmile.parquet")
    D = L.five_year_basis(L.dedupe_lots(D)).reset_index(drop=True)
    R = P.long_rows(D)
    for c, v in {"Chicago": ("Chicago city", "17"), "Madison": ("Madison city", "55"), "Bellevue": ("Bellevue city", "53")}.items():
        P.PLACE.setdefault(c, v)
    series, hu = P.bps_series()
    M.milwaukee_fix(series)
    X = P.traits(R, 2, series, hu).drop(columns=["log_acres", "log_width"])
    y, w = R["y5"].clip(lower=0).values, R["w"].values
    base = P.bps_baseline(R, series, hu)
    G = groups_for(X.columns)
    cities = sorted(R["city"].unique())
    rng = np.random.default_rng(M.SEED)
    pred = {g: np.full(len(R), np.nan) for g in ["(none)"] + list(G)}
    for c in cities:
        te = (R["city"] == c).values
        keep, w2 = M.thin(y, w, R["city"].isin(L.training_cities(cities, c)).values)
        m = M.Method(4).fit(X[keep], y[keep], w2[keep])
        pred["(none)"][te] = np.clip(m.predict(X[te]), 0, None)
        for g, cols in G.items():
            pred[g][te] = np.clip(m.predict(shuffle(X[te], cols, rng)), 0, None)
        print(c, flush=True)
    out = []
    for g, p in pred.items():
        T = R.assign(p=p * R["w"], a=R["y5"] * R["w"]).groupby(["city", "window", "start"])[["p", "a"]].sum().reset_index()
        T = T.merge(base, on=["city", "window", "start"])
        T = T[T["bps_same_pace"].notna() & (T["a"] > 0) & (T["p"] > 0)]
        out.append({"group": g, "traits": len(G.get(g, [])), "score": float(np.median(np.abs(np.log(T["p"] / T["a"]))))})
    return pd.DataFrame(out)


def run_share() -> pd.DataFrame:
    A, Xa, Xb, WN = M.share_design()
    y = A["ua5"].clip(lower=0).values
    w = A["w"].values
    ac = A["acres"].clip(lower=0.01).values
    hpa = y / ac
    up = (A["treated"] == 1).values
    tr = (A["_wi"] == 0).values
    allc = sorted(A.loc[tr, "city"].unique())
    reform = [c for c in allc if not c.endswith("placebo")]
    G = groups_for(Xa.columns)
    rng = np.random.default_rng(M.SEED)
    res = {g: [] for g in ["(none)"] + list(G)}
    for c in reform:
        te = (A["city"] == c).values
        ms = {}
        for g_, X in ((True, Xa), (False, Xb)):
            keep, w2 = M.thin(hpa, w * ac, A["city"].isin(L.training_cities(allc, c)).values & tr & (up == g_))
            ms[g_] = M.Method(5).fit(X[keep], hpa[keep], w2[keep])
        acc, uu, wt = np.minimum(ac[te], M.ACAP), up[te], w[te]
        ua, ub = A.loc[te, "ua5"].values, A.loc[te, "ub5"].values
        sa = float((ua * wt)[uu].sum() / max((ua * wt).sum(), 1e-9))
        sb = float((ub * wt)[uu].sum() / max((ub * wt).sum(), 1e-9))
        for g, cols in [("(none)", [])] + list(G.items()):
            xa, xb = (Xa[te], Xb[te]) if not cols else (shuffle(Xa[te], cols, rng), shuffle(Xb[te], [x for x in cols if x in Xb], rng))
            p_off = np.clip(ms[False].predict(L.forecast_view(xb)), 0, None) * acc
            p_on = p_off.copy()
            p_on[uu] = np.clip(ms[True].predict(L.forecast_view(xa[uu])), 0, None) * acc[uu]
            s_on = float((p_on * wt)[uu].sum() / max((p_on * wt).sum(), 1e-9))
            s_off = float((p_off * wt)[uu].sum() / max((p_off * wt).sum(), 1e-9))
            res[g].append({"city": c, "uplift": s_on - s_off, "sa": sa, "sb": sb, "change": sa - sb})
        print(c, flush=True)
    base = pd.DataFrame(res["(none)"])
    k_loo = {c: base.loc[base.city != c, "change"].sum() / base.loc[base.city != c, "uplift"].sum() for c in base.city}
    out = []
    for g, rows in res.items():
        T = pd.DataFrame(rows)
        cal = T["sb"] + T["city"].map(k_loo) * T["uplift"]
        ok = (cal > 0) & (T["sa"] > 0)
        out.append({"group": g, "traits": len(G.get(g, [])), "score": float(np.median(np.abs(np.log(cal[ok] / T.loc[ok, "sa"])))),
                    "uplift_change_corr": float(np.corrcoef(T["uplift"], T["change"])[0, 1])})
    return pd.DataFrame(out)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["pace", "share"], required=True)
    a = ap.parse_args(argv)
    T = run_pace() if a.model == "pace" else run_share()
    b = float(T.loc[T["group"] == "(none)", "score"].iloc[0])
    T["score_rise"] = T["score"] - b
    T = T.sort_values("score_rise", ascending=False)
    T.round(4).to_csv(REFERENCE / f"tod_heldout_importance_{a.model}.csv", index=False)
    print(T.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
