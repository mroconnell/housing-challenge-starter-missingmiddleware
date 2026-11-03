"""Parking causal framework, tests T (rail transit x repeal) and E2 (repeal alone vs inside a zoning rewrite).
docs/parking/CAUSAL_FRAMEWORK_PLAN.md (locked 2026-11-03; implementation details logged before counting).

    uv run python scripts/run_parking_causal_t_e2.py
Outputs: reference/parking_causal_t_places.csv, reference/parking_causal_t_e2_summary.csv
"""
from __future__ import annotations

import json
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

SEED, DRAWS = 20261103, 2000


def rail_geoids() -> set:
    """ACS geography ids ('160|SSPPPPP' places, '060|SSCCCMMMMM' county subdivisions) holding at least one rail stop."""
    stops = json.loads((RAW / "tod_census_cases" / "ntm_rail_stops.json").read_text())
    lon = np.array([float(s["stop_lon"]) for s in stops])
    lat = np.array([float(s["stop_lat"]) for s in stops])
    out = set()
    for fname, lev, idcol in (("cb_2024_us_place_500k.zip", "160", "GEOID"), ("cb_2024_us_cousub_500k.zip", "060", "GEOID")):
        lay = geom.read_shapefile(RAW / "census_cb_2024" / fname)
        x, y = geom.transform(lon, lat, 4326, lay.crs)
        hit = geom.points_in_polygons(x, y, lay.polys)
        ids = lay.attrs[idcol].astype(str).values
        out |= {f"{lev}|{ids[i]}" for i in np.unique(hit[hit >= 0])}
    return out


def did(p, key, ctrl, pre, post, homes):
    t0, t1 = cmp._rate(p, [key], pre, "units_total", homes), cmp._rate(p, [key], post, "units_total", homes)
    c0, c1 = cmp._rate(p, ctrl, pre, "units_total", homes), cmp._rate(p, ctrl, post, "units_total", homes)
    return (t1 - t0) - (c1 - c0)


def diff_ci(a_v, a_w, b_v, b_w):
    """Weighted mean of group a minus group b, 90% interval by resampling places within each group."""
    rng = np.random.default_rng(SEED)
    f = lambda v, w: np.sum(v * w) / np.sum(w)  # noqa: E731
    est = f(a_v, a_w) - f(b_v, b_w)
    bs = []
    for _ in range(DRAWS):
        i, j = rng.integers(0, len(a_v), len(a_v)), rng.integers(0, len(b_v), len(b_v))
        bs.append(f(a_v[i], a_w[i]) - f(b_v[j], b_w[j]))
    bs = np.array(bs)
    return est, np.percentile(bs, 5), np.percentile(bs, 95), 1.645 * bs.std(ddof=1)


def main() -> None:
    p = cmp.panel(rpc.read_bps_us())
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
    rail = rail_geoids()
    has_rail = lambda k: geo["acs_geoid"].get(k, "") in rail  # noqa: E731

    rows = []
    for r in real.itertuples():
        pre, post = cmp.windows(int(r.event_year))
        post = post[: int(r.n_post)]
        ctrl, _ = cmp.controls(p, r.key, int(r.event_year), excluded - {r.key}, homes, popn)
        mine = has_rail(r.key)
        same = [c for c in ctrl if has_rail(c) == mine]
        use = same if len(same) >= 5 else ctrl
        rows.append(dict(key=r.key, place=r.place, state=r.state, rail=mine, n_controls=len(ctrl), n_same=len(same),
                         used_same=len(same) >= 5, effect_matched=did(p, r.key, use, pre, post, homes), effect_all=r.effect,
                         weight=r.weight, rewrite=bool(r.simultaneous_rewrite)))
    P = pd.DataFrame(rows)
    P.to_csv(REFERENCE / "parking_causal_t_places.csv", index=False)

    out = []
    nan_t = int(P["effect_matched"].isna().sum())  # places with no computable matched effect (e.g. empty comparison rates)
    Q = P.dropna(subset=["effect_matched"])
    a, b = Q[Q["rail"]], Q[~Q["rail"]]
    est, lo, hi, mde = diff_ci(a["effect_matched"].values, a["weight"].values, b["effect_matched"].values, b["weight"].values)
    loo = []  # audit (2026-11-03): leave one place out
    for j in Q.index:
        R_ = Q.drop(j); ra, rb = R_[R_["rail"]], R_[~R_["rail"]]
        loo.append((np.average(ra["effect_matched"], weights=ra["weight"]) - np.average(rb["effect_matched"], weights=rb["weight"]), Q.loc[j, "place"]))
    lmin, lmax = min(loo), max(loo)
    out.append(dict(test="T rail x repeal: effect with rail minus without", unit="permits per 1,000 existing homes a year",
                    n_a=len(a), n_b=len(b), estimate=est, p05=lo, p95=hi, mde=mde,
                    mean_a=np.average(a["effect_matched"], weights=a["weight"]), mean_b=np.average(b["effect_matched"], weights=b["weight"]),
                    note=f"{int((~P['used_same']).sum())} places used all comparison places (fewer than 5 with the same rail status); {nan_t} with no computable effect left out; leave-one-place-out {lmin[0]:.2f} (without {lmin[1]}) to {lmax[0]:.2f} (without {lmax[1]})"))
    a, b = P[~P["rewrite"]], P[P["rewrite"]]
    est, lo, hi, mde = diff_ci(a["effect_all"].values, a["weight"].values, b["effect_all"].values, b["weight"].values)
    out.append(dict(test="E2 repeal alone minus repeal inside a rewrite (all homes)", unit="permits per 1,000 existing homes a year",
                    n_a=len(a), n_b=len(b), estimate=est, p05=lo, p95=hi, mde=mde,
                    mean_a=np.average(a["effect_all"], weights=a["weight"]), mean_b=np.average(b["effect_all"], weights=b["weight"]),
                    note="rewrite-only group not yet built, so the 2x2 is incomplete"))
    h = pd.read_csv(REFERENCE / "parking_causal_h1h2_places.csv").dropna(subset=["h1_did"])
    h = h[h["h1_weight"] > 0]
    a, b = h[~h["simultaneous_rewrite"]], h[h["simultaneous_rewrite"]]
    if len(a) >= 3 and len(b) >= 3:
        est, lo, hi, mde = diff_ci(a["h1_did"].values, a["h1_weight"].values, b["h1_did"].values, b["h1_weight"].values)
        out.append(dict(test="E2 on H1: homes per 5+ building, alone minus rewrite", unit="homes per building", n_a=len(a), n_b=len(b),
                        estimate=est, p05=lo, p95=hi, mde=mde, mean_a=np.average(a["h1_did"], weights=a["h1_weight"]),
                        mean_b=np.average(b["h1_did"], weights=b["h1_weight"]), note=""))
    S = pd.DataFrame(out)
    S.to_csv(REFERENCE / "parking_causal_t_e2_summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.round(3).to_string(index=False))
    print(P.groupby("rail").agg(places=("key", "size"), homes_weight=("weight", "sum")).to_string())


if __name__ == "__main__":
    main()
