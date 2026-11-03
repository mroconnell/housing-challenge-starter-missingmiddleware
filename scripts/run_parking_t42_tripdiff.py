"""Parking test 42: triple difference by Census size class, (5+ unit homes - 1-unit homes) per 1,000 existing homes a year,
in the main matched difference-in-differences. docs/parking/CAUSAL_FRAMEWORK_PLAN.md (Test 42, locked 2026-11-03).

    uv run python scripts/run_parking_t42_tripdiff.py
Output: reference/parking_t42.csv
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

SEED, DRAWS = 20261104, 2000
WI = 2_668_677 * 5 / 1000


def main() -> None:
    bps = rpc.read_bps_us()
    p = cmp.panel(bps)
    b = bps.assign(key=bps["state_fips"].astype(str).str.strip() + "|" + bps["bps_id"].astype(str).str.strip()).drop_duplicates(["key", "year"])
    b["b24u"] = b["2units_units"] + b["3_4units_units"]
    tab = {c: b.pivot_table(index="key", columns="year", values=c, aggfunc="sum") for c in ("5plus_units", "1unit_units", "b24u")}
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001"))
    homes = homes[homes > 0]
    popn = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001"))
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    excluded = {k for r in tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
                .drop_duplicates("prn_key").itertuples() if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].copy()
    excluded |= set(real["key"])
    pl = geom.read_shapefile(RAW / "census_cb_2024" / "cb_2024_us_place_500k.zip")
    cb = geom.read_shapefile(RAW / "census_cbsa_cb_2024" / "cb_2024_us_cbsa_20m.zip")
    pid = {f"160|{g}": i for i, g in enumerate(pl.attrs["GEOID"].astype(str))}

    def rate(col, keys, yrs):
        d = homes.reindex(list(keys)).sum()
        return float(np.nansum(tab[col].reindex(index=list(keys), columns=yrs).values)) / len(yrs) / d * 1000 if d > 0 else np.nan

    def gap(keys, yrs):
        return rate("5plus_units", keys, yrs) - rate("1unit_units", keys, yrs)

    rows = []
    for r in real.itertuples():
        e = int(r.event_year)
        pre, post = cmp.windows(e)
        post = post[: int(r.n_post)]
        ctrl, _ = cmp.controls(p, r.key, e, excluded - {r.key}, homes, popn)
        if not ctrl or r.key not in homes.index:
            continue
        main = (gap([r.key], post) - gap([r.key], pre)) - (gap(ctrl, post) - gap(ctrl, pre))
        b24 = (rate("b24u", [r.key], post) - rate("b24u", [r.key], pre)) - (rate("b24u", ctrl, post) - rate("b24u", ctrl, pre))
        early, late = [y for y in pre if y <= e - 3], [y for y in pre if y >= e - 2]
        bt = (gap([r.key], late) - gap([r.key], early)) - (gap(ctrl, late) - gap(ctrl, early)) if early and late else np.nan
        gi = pid.get(geo.loc[r.key, "acs_geoid"])
        cbsa = "none"
        if gi is not None:
            x, y = geom.representative_points([pl.polys[gi]])
            h = geom.points_in_polygons(x, y, cb.polys)
            cbsa = str(cb.attrs["GEOID"].iloc[h[0]]) if h[0] >= 0 else f"none-{r.key}"
        rows.append(dict(key=r.key, place=r.place, weight=r.weight, cbsa=cbsa, tripdiff=main, b24=b24, backtest=bt))
    P = pd.DataFrame(rows)
    rng = np.random.default_rng(SEED)
    out = []

    def summarize(col, lab, metro=False):
        d = P.dropna(subset=[col]).reset_index(drop=True)
        v, w = d[col].values, d["weight"].values
        f = lambda i: np.sum(v[i] * w[i]) / np.sum(w[i])  # noqa: E731
        if metro:
            cl = d["cbsa"].values
            u = np.unique(cl)
            idx = {c: np.where(cl == c)[0] for c in u}
            bs = np.array([f(np.concatenate([idx[c] for c in rng.choice(u, len(u))])) for _ in range(DRAWS)])
        else:
            bs = np.array([f(rng.integers(0, len(v), len(v))) for _ in range(DRAWS)])
        lo, hi = np.percentile(bs, [5, 95])
        est = f(np.arange(len(v)))
        out.append(dict(test=lab, places=len(d), estimate=est, p05=lo, p95=hi, equal_weight=float(v.mean()),
                        wi_p05=lo * WI if col == "tripdiff" else np.nan, wi_p95=hi * WI if col == "tripdiff" else np.nan,
                        wi_width=(hi - lo) * WI if col == "tripdiff" else np.nan))

    summarize("tripdiff", "42 main: (5+ minus 1-unit) homes per 1,000 existing homes a year, place bootstrap")
    summarize("tripdiff", "42 main, metro-clustered bootstrap", metro=True)
    summarize("b24", "42 beside: 2-4 unit homes per 1,000 existing homes a year")
    summarize("backtest", "42 backtest: years -2,-1 vs -5..-3 (must include 0)")
    S = pd.DataFrame(out)
    S["note"] = "relative shift between size classes if land moves between them; 25% rule bar 26,289 homes"
    S.to_csv(REFERENCE / "parking_t42.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.drop(columns="note").round(3).to_string(index=False))


if __name__ == "__main__":
    main()
