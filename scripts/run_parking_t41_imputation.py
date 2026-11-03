"""Parking test 41: two-year cumulative effect with an imputation estimator (Borusyak-Jaravel-Spiess), hand-written.
docs/parking/CAUSAL_FRAMEWORK_PLAN.md ("Tests 40 and 41" and the 40/41 additions; locked 2026-11-03).

    uv run python scripts/run_parking_t41_imputation.py
Output: reference/parking_t41.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_parking_comparison as rpc  # noqa: E402
from missing_middleware import geom  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

SEED, BOOT = 20261104, 1000
WI = 2_668_677 * 5 / 1000  # Wisconsin homes per (permit per 1,000 homes a year) over 2027-2031
BAR = 26_289.0


def twfe(y, unit, year, iters=200):
    """Place + year effects by alternating means on the observations given."""
    nu, ny = unit.max() + 1, year.max() + 1
    a, g = np.zeros(nu), np.zeros(ny)
    for _ in range(iters):
        a_new = np.bincount(unit, y - g[year], nu) / np.maximum(np.bincount(unit, minlength=nu), 1)
        g_new = np.bincount(year, y - a_new[unit], ny) / np.maximum(np.bincount(year, minlength=ny), 1)
        g_new -= g_new[0]
        if max(np.max(np.abs(a_new - a)), np.max(np.abs(g_new - g))) < 1e-10:
            a, g = a_new, g_new
            break
        a, g = a_new, g_new
    return a, g


def main() -> None:
    bps = rpc.read_bps_us()
    p = cmp.panel(bps)
    b = bps.assign(key=bps["state_fips"].astype(str).str.strip() + "|" + bps["bps_id"].astype(str).str.strip()).drop_duplicates(["key", "year"])
    one = b.set_index(["key", "year"])["1unit_units"]
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001"))
    homes = homes[homes > 0]
    popn = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001"))
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    bench = {k for r in tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
             .drop_duplicates("prn_key").itertuples() if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].copy()
    t1 = pd.read_csv(REFERENCE / "parking_t1_places.csv")
    county = (geo["state_fips"].astype(str) + geo["county_fips"].astype(str).str.zfill(3)).to_dict()
    # CBSA for the repeal places (leave-one-metro-out extra)
    pl = geom.read_shapefile(RAW / "census_cb_2024" / "cb_2024_us_place_500k.zip")
    cb = geom.read_shapefile(RAW / "census_cbsa_cb_2024" / "cb_2024_us_cbsa_20m.zip")
    pid = {f"160|{g}": i for i, g in enumerate(pl.attrs["GEOID"].astype(str))}

    def run(treated, outcome, excluded):
        pools = set()
        for r in treated.itertuples():
            pools |= set(cmp.controls(p, r.key, int(r.event_year), excluded - {r.key}, homes, popn)[0])
        keys = sorted((set(treated["key"]) | pools) & set(homes.index))
        d = p[p["key"].isin(keys) & p["year"].between(2012, 2025)][["key", "year", "units_total"]].drop_duplicates(["key", "year"]).copy()
        if outcome == "1unit_units":
            d["units_total"] = [one.get((k, y), np.nan) for k, y in zip(d["key"], d["year"])]
        d = d.dropna(subset=["units_total"])
        d["y"] = d["units_total"] / d["key"].map(homes) * 1000
        ev = dict(zip(treated["key"], treated["event_year"].astype(int)))
        d["ev"] = d["key"].map(ev)
        d["rel"] = d["year"] - d["ev"]
        d = d[~(d["rel"] == 0)]  # year 0 out of everything
        return d, ev

    def estimate(d, ev, drop_pre=False):
        untreated = d["ev"].isna() | (d["rel"] < 0)
        if drop_pre:
            untreated &= ~(d["rel"].between(-3, -1))
        u_idx, ukeys = pd.factorize(d["key"])
        y_idx, ykeys = pd.factorize(d["year"], sort=True)
        m = untreated.values
        a, g = twfe(d["y"].values[m], u_idx[m], y_idx[m])
        seen = np.bincount(u_idx[m], minlength=len(ukeys)) > 0
        yhat = a[u_idx] + g[y_idx]
        res = d["y"].values - yhat
        out = {}
        target = d["rel"].between(1, 2) if not drop_pre else d["rel"].between(-3, -1)
        for k in ev:
            sel = (d["key"].values == k) & target.values & seen[u_idx]
            need = 2 if not drop_pre else 3
            if sel.sum() == need:
                out[k] = float(res[sel].sum()) if not drop_pre else float(res[sel].mean())
        return out

    def agg(effects, wmap):
        ks = list(effects)
        v = np.array([effects[k] for k in ks])
        w = np.array([wmap[k] for k in ks])
        return ks, v, w

    def cluster_boot(d, ev, wmap, drop_pre=False):
        rng = np.random.default_rng(SEED)
        cl = d["key"].map(county).values
        ucl = np.unique(cl)
        groups = {c: d.index[cl == c] for c in ucl}
        hw, ew = [], []
        for _ in range(BOOT):
            pick = rng.choice(ucl, len(ucl))
            parts = []
            for j, c in enumerate(pick):
                g_ = d.loc[groups[c]].copy()
                g_["key"] = g_["key"] + f"#{j}"
                parts.append(g_)
            bd = pd.concat(parts, ignore_index=True)
            bev = {k: ev[k.split("#")[0]] for k in bd["key"].unique() if k.split("#")[0] in ev}
            e = estimate(bd, bev, drop_pre)
            if not e:
                continue
            ks, v, w = agg(e, {k: wmap[k.split("#")[0]] for k in e})
            hw.append(np.sum(v * w) / np.sum(w))
            ew.append(v.mean())
        return np.array(hw), np.array(ew)

    rows = []
    ex_main = bench | set(real["key"])
    d, ev = run(real, "units_total", ex_main)
    wmap = dict(zip(real["key"], real["homes"]))
    eff = estimate(d, ev)
    ks, v, w = agg(eff, wmap)
    hw_b, ew_b = cluster_boot(d, ev, wmap)
    hw, ewm = float(np.sum(v * w) / np.sum(w)), float(v.mean())
    lo, hi = np.percentile(hw_b, [5, 95])
    share_places, share_homes = len(ks) / len(real), sum(wmap[k] for k in ks) / real["homes"].sum()
    rows.append(dict(test="41 main: two-year cumulative, all homes (home-weighted)", places=len(ks), share_places=share_places,
                     share_homes=share_homes, estimate=hw, p05=lo, p95=hi, equal_weight=ewm,
                     ew_p05=np.percentile(ew_b, 5), ew_p95=np.percentile(ew_b, 95),
                     wi_center=hw / 2 * WI, wi_p05=lo / 2 * WI, wi_p95=hi / 2 * WI, wi_width=(hi - lo) / 2 * WI))
    # leave one city / county / metro out
    names = dict(zip(real["key"], real["place"]))
    loo_c = [np.sum(np.delete(v, i) * np.delete(w, i)) / np.sum(np.delete(w, i)) for i in range(len(v))]
    cnty = np.array([county.get(k, k) for k in ks])
    loo_k = [np.sum(v[cnty != c] * w[cnty != c]) / np.sum(w[cnty != c]) for c in np.unique(cnty)]
    gid = [pid.get(geo.loc[k, "acs_geoid"]) for k in ks]
    cbsa = []
    for gi in gid:
        if gi is None:
            cbsa.append("none")
            continue
        x, y = geom.representative_points([pl.polys[gi]])
        h = geom.points_in_polygons(x, y, cb.polys)
        cbsa.append(str(cb.attrs["GEOID"].iloc[h[0]]) if h[0] >= 0 else "none")
    cbsa = np.array(cbsa)
    loo_m = [np.sum(v[cbsa != c] * w[cbsa != c]) / np.sum(w[cbsa != c]) for c in np.unique(cbsa)]
    rows.append(dict(test="41 leave one city out (range)", estimate=np.nan, p05=min(loo_c), p95=max(loo_c),
                     note=f"most influential: {names[ks[int(np.argmin(loo_c))]]} / {names[ks[int(np.argmax(loo_c))]]}"))
    rows.append(dict(test="41 leave one county out (range)", estimate=np.nan, p05=min(loo_k), p95=max(loo_k)))
    rows.append(dict(test="41 leave one metro out (range; extra)", estimate=np.nan, p05=min(loo_m), p95=max(loo_m)))
    # pre-trend
    pt = estimate(d, ev, drop_pre=True)
    ks2, v2, w2 = agg(pt, wmap)
    pb, _ = cluster_boot(d, ev, wmap, drop_pre=True)
    rows.append(dict(test="41 pre-trend: mean imputed residual, years -3..-1", places=len(ks2), estimate=float(np.sum(v2 * w2) / np.sum(w2)),
                     p05=np.percentile(pb, 5), p95=np.percentile(pb, 95)))
    # placebos
    d1, ev1 = run(real, "1unit_units", ex_main)
    e1 = estimate(d1, ev1)
    k1, v1, w1 = agg(e1, wmap)
    b1, _ = cluster_boot(d1, ev1, wmap)
    rows.append(dict(test="41 placebo: single-family homes", places=len(k1), estimate=float(np.sum(v1 * w1) / np.sum(w1)),
                     p05=np.percentile(b1, 5), p95=np.percentile(b1, 95)))
    ex_t1 = ex_main | set(t1["key"])
    dt, evt = run(t1.rename(columns={}), "units_total", ex_t1)
    wt = dict(zip(t1["key"], t1["homes"]))
    et = estimate(dt, evt)
    kt, vt, wtt = agg(et, wt)
    bt, _ = cluster_boot(dt, evt, wt)
    rows.append(dict(test="41 placebo: T1 non-residential places", places=len(kt), estimate=float(np.sum(vt * wtt) / np.sum(wtt)),
                     p05=np.percentile(bt, 5), p95=np.percentile(bt, 95)))
    S = pd.DataFrame(rows)
    inc0 = lambda r: r["p05"] <= 0 <= r["p95"]  # noqa: E731
    m = S.iloc[0]
    passes = bool(m["wi_width"] <= BAR and inc0(S.iloc[4]) and inc0(S.iloc[5]) and inc0(S.iloc[6]))
    S["unit"] = "cumulative permits per 1,000 existing homes over event years +1 and +2 (pre-trend: mean yearly residual)"
    S["rule"] = ""
    S.loc[0, "rule"] = f"width <= {BAR:,.0f}: {m['wi_width'] <= BAR}; pre-trend and placebos include 0: {inc0(S.iloc[4]) and inc0(S.iloc[5]) and inc0(S.iloc[6])}; passes (before calibration): {passes}"
    S.to_csv(REFERENCE / "parking_t41.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 140)
    print(S.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
