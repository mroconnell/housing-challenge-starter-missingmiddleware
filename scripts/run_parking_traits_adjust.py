"""Parking: repeal comparison adjusted for local boom and bust, and longer windows (docs/parking/TRAITS_ADJUST_PLAN.md).

    uv run --all-extras python scripts/run_parking_traits_adjust.py
Outputs: reference/parking_traits_adjust_{places,summary,path}.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_comparison as rpc  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

MIN_HOMES, SEEDS = 1000, range(20261101, 20261106)
FEATS = ["job_growth", "pay_growth", "state_change", "rate_before", "log_homes", "no_vehicle_share", "vehicles_per_household", "transit_share"]


def wavg_ci(d, col="adjusted"):
    d = d.dropna(subset=[col])
    w = (d["homes"] * d["n_post"]).values
    v = d[col].values
    rng = np.random.default_rng(20261101)
    bs = [np.average(v[i], weights=w[i]) for i in (rng.integers(0, len(v), len(v)) for _ in range(2000))]
    return dict(places=len(d), weighted=float(np.average(v, weights=w)), p05=float(np.percentile(bs, 5)),
                p95=float(np.percentile(bs, 95)), median=float(np.median(v)))


def main() -> None:
    bps = rpc.read_bps_us()
    p = cmp.panel(bps)
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001"))
    homes = homes[homes > 0]
    cfips = (geo["state_fips"] + geo["county_fips"].str.zfill(3))
    jobs = pd.read_csv(REFERENCE / "parking_traits_county_jobs.csv", dtype={"county_fips5": str})
    emp = jobs.pivot_table(index="county_fips5", columns="year", values="employment")
    pay = jobs.pivot_table(index="county_fips5", columns="year", values="avg_pay")
    acs = pd.read_csv(REFERENCE / "parking_traits_acs2019.csv", dtype={"acs_geoid": str}).drop_duplicates("acs_geoid").set_index("acs_geoid")

    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")]
    real = real[real["key"].isin(p["key"])][["key", "place", "event_year", "effect"]]
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    reformed = {k for r in tax[tax["land_use"].fillna("").str.contains("resid|all uses") & (tax["place_type"] == "city")].drop_duplicates("prn_key").itertuples()
                if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    tot = p.pivot_table(index="key", columns="year", values="units_total", aggfunc="sum")

    def rows_for(keys, E):
        pre, post = cmp.windows(int(E))
        post = [y for y in post if y in tot.columns]
        ks = [k for k in keys if k in tot.index and k in homes.index and homes[k] >= MIN_HOMES]
        t = tot.loc[ks]
        t = t[t[pre + post].notna().all(axis=1)]
        h = homes.reindex(t.index)
        d = pd.DataFrame(index=t.index)
        d["event_year"], d["n_post"], d["homes"] = int(E), len(post), h
        d["rate_before"] = t[pre].mean(axis=1) / h * 1000
        d["change"] = t[post].mean(axis=1) / h * 1000 - d["rate_before"]
        cf = cfips.reindex(d.index)
        d["job_growth"] = np.log(emp[post].mean(axis=1).reindex(cf).values / emp[pre].mean(axis=1).reindex(cf).values)
        d["pay_growth"] = np.log(pay[post].mean(axis=1).reindex(cf).values / pay[pre].mean(axis=1).reindex(cf).values)
        d["log_homes"] = np.log(h)
        g = geo["acs_geoid"].reindex(d.index)
        for c in ("no_vehicle_share", "vehicles_per_household", "transit_share"):
            d[c] = acs[c].reindex(g).values
        d["state"] = [k.split("|")[0] for k in d.index]
        return d

    years = sorted(real["event_year"].astype(int).unique())
    pool_keys = [k for k in homes.index if k not in reformed and k not in set(real["key"])]
    P = pd.concat([rows_for(pool_keys, E) for E in years]).reset_index(names="key")
    # state change: all places in the state (pool and repeal), same years, homes-weighted
    allrows = pd.concat([rows_for(list(homes.index), E) for E in years]).reset_index(names="key")
    sc = allrows.groupby(["state", "event_year"]).apply(lambda g: np.average(g["change"], weights=g["homes"]), include_groups=False)
    for D in (P,):
        D["state_change"] = [sc.get((s, e), np.nan) for s, e in zip(D["state"], D["event_year"])]
    Rr = pd.concat([rows_for([r.key], r.event_year).reset_index(names="key").assign(place=r.place, headline_effect=r.effect) for r in real.itertuples()])
    Rr["state_change"] = [sc.get((s, e), np.nan) for s, e in zip(Rr["state"], Rr["event_year"])]
    P = P.dropna(subset=["change"])
    med = P[FEATS].median()

    def fit(kind, D, seed=0):
        X, y, w = D[FEATS].fillna(med), D["change"], (D["homes"] * D["n_post"]).values
        m = LinearRegression() if kind == "wls" else RandomForestRegressor(n_estimators=300, min_samples_leaf=20, max_features=0.5, n_jobs=-1, random_state=seed)
        return m.fit(X, y, sample_weight=w)

    out, places = [], []
    # held-out R^2 by state groups
    states = sorted(P["state"].unique())
    rng = np.random.default_rng(20261101)
    grp = dict(zip(states, rng.permutation(len(states)) % 5))
    for kind in ("wls", "forest"):
        pred = np.full(len(P), np.nan)
        for gi in range(5):
            te = P["state"].map(grp).values == gi
            pred[te] = fit(kind, P[~te]).predict(P.loc[te, FEATS].fillna(med))
        w = P["homes"] * P["n_post"]
        r2 = 1 - np.average((P["change"] - pred) ** 2, weights=w) / np.average((P["change"] - np.average(P["change"], weights=w)) ** 2, weights=w)
        m = fit(kind, P)
        Rk = Rr.copy()
        Rk["predicted_change"] = m.predict(Rk[FEATS].fillna(med))
        Rk["adjusted"] = Rk["change"] - Rk["predicted_change"]
        places.append(Rk.assign(model=kind))
        out.append(dict(model=kind, test="repeal places, adjusted for traits", heldout_r2=float(r2), **wavg_ci(Rk)))
        nosf = Rk[~Rk["place"].isin(["San Francisco"])]
        out.append(dict(model=kind, test="without San Francisco", **wavg_ci(nosf)))
        out.append(dict(model=kind, test="without SF and Minneapolis", **wavg_ci(Rk[~Rk["place"].isin(["San Francisco", "Minneapolis"])])))
        for s in SEEDS:  # noise: random never-reformed rows with the real years, left out of the fit
            r = np.random.default_rng(s)
            fake = []
            for E in Rr["event_year"]:
                cand = P[(P["event_year"] == E)]
                fake.append(cand.index[r.integers(0, len(cand))])
            fake = list(dict.fromkeys(fake))
            mf = fit(kind, P.drop(index=fake), s)
            F = P.loc[fake].copy()
            F["adjusted"] = F["change"] - mf.predict(F[FEATS].fillna(med))
            out.append(dict(model=kind, test=f"noise check, seed {s}", **wavg_ci(F)))
        print(kind, "done", flush=True)
    S = pd.DataFrame(out)
    S.to_csv(REFERENCE / "parking_traits_adjust_summary.csv", index=False)
    PL = pd.concat(places)
    PL.to_csv(REFERENCE / "parking_traits_adjust_places.csv", index=False)

    # B. longer windows: effect by year since repeal, headline comparison places
    tax_ex = {k for r in tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")].drop_duplicates("prn_key").itertuples()
              if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))} | set(real["key"])
    path = cmp.event_path(p, real[["key", "place", "event_year"]], tax_ex, homes, max_k=7)
    path.to_csv(REFERENCE / "parking_traits_adjust_path.csv", index=False)
    ps = path.groupby("k").apply(lambda g: pd.Series(dict(places=len(g), weighted=np.average(g["effect"], weights=g["homes"]),
                                                          median=g["effect"].median())), include_groups=False)
    pd.set_option("display.width", 200)
    print(S.round(3).to_string(index=False))
    print(ps.round(2).to_string())
    print(PL[PL["place"].isin(["San Francisco", "Minneapolis", "Austin", "Raleigh", "San Jose"])][["model", "place", "change", "predicted_change", "adjusted", "headline_effect"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
