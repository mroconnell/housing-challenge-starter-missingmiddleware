"""City-size weighting test on the corrected method-2 effects (CAUSAL_FRAMEWORK_PLAN.md, "Method 2 correction and
city-size weighting test", item 3; post hoc in origin). Four versions of the target-state mix, scored by the locked
leave-one-state-out test; keep (i) unless another is >10% lower and its paired bootstrap over states excludes 0.

    uv run --all-extras python scripts/check_parking_method2_size_test.py
Needs reference/parking_method2_corrected_pick.csv (committed) and parking_method2_corrected_places.csv.
Outputs: reference/parking_method2_size_test.csv, parking_method2_size_test_wi.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_parking_comparison as rpc  # noqa: E402
import run_parking_method2 as m  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

VERSIONS = ("(i) 4 bands", "(ii) 3 bands at terciles", "(iii) smooth line on log population", "(iv) crowding terciles")


def cells_mean(y, ev, bins_ev, cells) -> float:
    e = ev.assign(band=bins_ev)
    w, _ = m.mix_weights(e, cells)
    return float(np.sum(w * y) / np.sum(w)) if w.sum() > 0 else np.nan


def smooth_pred(y, logpop, metro, base, logpop_t, metro_t, h_t) -> float:
    X = np.column_stack([np.ones(len(y)), logpop, metro])
    b = m.cmp.wls(X, y, base)
    lp = np.clip(logpop_t, logpop.min(), logpop.max())  # held at the edge of the observed range
    pred = np.column_stack([np.ones(len(lp)), lp, metro_t]) @ b
    return float(np.sum(pred * h_t) / np.sum(h_t))


def main() -> None:
    m.SUF, m.CORRECTED = "_corrected", True
    pick = str(pd.read_csv(REFERENCE / "parking_method2_corrected_pick.csv")["candidate"].iloc[0])
    P = pd.read_csv(REFERENCE / "parking_method2_corrected_places.csv")
    P = P[P["variant"] == f"method 2, {pick}"].reset_index(drop=True)
    run(P["effect"].values, "parking_method2_size_test")


def run(y, out: str) -> None:
    """Size test on the 76 effects y (corrected data); writes reference/{out}.csv, {out}_by_state.csv, {out}_wi.csv."""
    m.SUF, m.CORRECTED = "_corrected", True
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].dropna(subset=["effect"]).reset_index(drop=True)
    D = m.Data()
    _, cases = m.real_cases()
    pop = real["population"].fillna(0).values
    ev = pd.DataFrame({"homes": real["homes"].values, "n_post": real["n_post"].values,
                       "metro": [D.metro.get(c["key"], 0.0) for c in cases]})
    ev["base"] = ev["homes"] * ev["n_post"]
    crowd = np.array([D.crowd_for(c["event_year"]).get(c["key"], np.nan) for c in cases])
    t_pop = np.quantile(pop, [1 / 3, 2 / 3])
    t_cr = np.nanquantile(crowd, [1 / 3, 2 / 3])
    bins = {"(i) 4 bands": m.band_of(pop), "(ii) 3 bands at terciles": np.digitize(pop, t_pop),
            "(iv) crowding terciles": np.digitize(np.nan_to_num(crowd, nan=np.nanmedian(crowd)), t_cr)}
    ok = np.isfinite(y)
    states = real["state"].value_counts()
    states = list(states[states >= 3].index)
    err = {v: [] for v in VERSIONS}
    for s in states:
        hold = (real["state"] == s).values & ok
        tr = (~(real["state"] == s).values) & ok
        truth = float(np.average(y[hold], weights=ev["base"].values[hold]))
        yt = m.winsor(y[tr])
        for v in VERSIONS:
            if v.startswith("(iii)"):
                pred = smooth_pred(yt, np.log(pop[tr].clip(1)), ev["metro"].values[tr], ev["base"].values[tr],
                                   np.log(pop[hold].clip(1)), ev["metro"].values[hold], ev["base"].values[hold])
            else:
                b = bins[v]
                hc = ev[hold].assign(band=b[hold]).groupby(["metro", "band"])["base"].sum()
                pred = cells_mean(yt, ev[tr].reset_index(drop=True), b[tr], hc)
            err[v].append(abs(pred - truth))
    E = pd.DataFrame(err, index=states)
    mae = E.mean()
    rng = np.random.default_rng(m.SEED)
    rows = []
    base_v = "(i) 4 bands"
    winner = base_v
    for v in VERSIONS:
        d = [E[v].values[i].mean() - E[base_v].values[i].mean() for i in (rng.integers(0, len(E), len(E)) for _ in range(m.BOOT))]
        lo, hi = np.percentile(d, 5), np.percentile(d, 95)
        better = v != base_v and mae[v] < 0.9 * mae[base_v] and hi < 0
        rows.append(dict(version=v, mae=mae[v], minus_4bands_p05=lo, minus_4bands_p95=hi, beats_4_bands=bool(better)))
        if better and mae[v] < mae[winner]:
            winner = v
    R = pd.DataFrame(rows).assign(winner=winner)
    E.loc["mean absolute error"] = mae
    E.round(4).to_csv(REFERENCE / f"{out}_by_state.csv")
    R.round(4).to_csv(REFERENCE / f"{out}.csv", index=False)
    # Wisconsin figure under each version (tool areas, 2,668,677 eligible homes)
    a = pd.read_csv(REFERENCE / "parking_model_by_area.csv", dtype={"county_id": str})
    cells4 = m.tool_cells_wi()
    a_pop = pd.to_numeric(a["population"]).fillna(0).values
    metro_map = {}
    for (mt, bd), _ in cells4.items():
        metro_map[(mt, bd)] = mt
    bps = rpc.read_bps_us()
    w = bps[bps["state_fips"].astype(str).str.strip() == "55"].copy()
    w["county"] = "55" + w["county_fips"].astype(str).str.strip().str.zfill(3)
    cb = w.groupby("county")["cbsa"].agg(lambda s: s.astype(str).str.strip().mode().iloc[0])
    lsad = m.read_shapefile_attributes(m.RAW / "census_cbsa_cb_2024" / "cb_2024_us_cbsa_20m.zip").set_index("CBSAFP")["LSAD"]
    a_metro = a["county_id"].map(cb).map(lsad).eq("M1").astype(float).values
    a_h = pd.to_numeric(a["eligible_homes"]).values
    a_cr = ("060|" + a["area_id"].str.replace("muni:", "", regex=False)).map(D.crowd.get(2023, pd.Series(dtype=float))).values
    yw = m.winsor(y[ok])
    evo = ev[ok].reset_index(drop=True)
    wi = []
    for v in VERSIONS:
        if v.startswith("(iii)"):
            val = smooth_pred(yw, np.log(pop[ok].clip(1)), evo["metro"].values, evo["base"].values, np.log(a_pop.clip(1)), a_metro, a_h)
        else:
            if v.startswith("(i)"):
                ab = m.band_of(a_pop)
            elif v.startswith("(ii)"):
                ab = np.digitize(a_pop, t_pop)
            else:
                ab = np.digitize(np.nan_to_num(a_cr, nan=np.nanmedian(a_cr)), t_cr)
            cells = pd.DataFrame({"metro": a_metro, "band": ab, "h": a_h}).groupby(["metro", "band"])["h"].sum()
            val = cells_mean(yw, evo, bins[v][ok], cells)
        wi.append(dict(version=v, rate=val, wi_homes=val * m.WI_K))
    pd.DataFrame(wi).round(4).to_csv(REFERENCE / f"{out}_wi.csv", index=False)
    pd.set_option("display.width", 200)
    print(E.round(3).to_string())
    print(R.round(3).to_string(index=False))
    print(pd.DataFrame(wi).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
