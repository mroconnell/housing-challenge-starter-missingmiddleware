"""Parking pre-trend follow-ups P1 (short before window), P2 (match on before-trend), P3 (relative-magnitude bound).
docs/parking/CAUSAL_FRAMEWORK_PLAN.md ("Pre-trend follow-ups P1-P3", locked).

    uv run python scripts/run_parking_p123.py
Output: reference/parking_p123.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_parking_comparison as rpc  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

SEED, DRAWS = 20261104, 2000


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
    R = lambda ks, ys: cmp._rate(p, ks, ys, "units_total", homes)  # noqa: E731

    def slope(k, yrs):
        v = np.array([R([k], [y]) for y in yrs])
        return np.polyfit(np.array(yrs, float), v, 1)[0] if len(yrs) >= 3 and np.all(np.isfinite(v)) else np.nan

    rows = []
    for r in real.itertuples():
        e = int(r.event_year)
        pre, post = cmp.windows(e)
        post = post[: int(r.n_post)]
        ctrl, _ = cmp.controls(p, r.key, e, excluded - {r.key}, homes, popn)
        if not ctrl or r.key not in homes.index:
            continue
        short = [y for y in pre if y >= e - 2]
        p1 = (R([r.key], post) - R([r.key], short)) - (R(ctrl, post) - R(ctrl, short)) if short else np.nan
        s0 = slope(r.key, pre)
        cs = pd.Series({c: slope(c, pre) for c in ctrl}).dropna()
        near = list((cs - s0).abs().sort_values().index[:10]) if np.isfinite(s0) and len(cs) else ctrl
        p2 = (R([r.key], post) - R([r.key], pre)) - (R(near, post) - R(near, pre))
        early, late = [y for y in pre if y <= e - 3], [y for y in pre if y >= e - 2]
        pt = ((R([r.key], late) - R([r.key], early)) - (R(near, late) - R(near, early))) if early and late else np.nan
        gaps = {e - y: (R([r.key], [y]) - R(ctrl, [y])) - (R([r.key], [e - 1]) - R(ctrl, [e - 1])) for y in pre if y != e - 1}
        rows.append(dict(place=r.place, key=r.key, weight=r.weight, main=r.effect, p1=p1, p2=p2, p2_pretrend=pt, n_slope_matched=len(near),
                         **{f"gap_{k}": v for k, v in gaps.items()}))
    P = pd.DataFrame(rows)
    rng = np.random.default_rng(SEED)

    def wm(col):
        d = P.dropna(subset=[col])
        v, w = d[col].values, d["weight"].values
        f = lambda i: np.sum(v[i] * w[i]) / np.sum(w[i])  # noqa: E731
        bs = np.array([f(rng.integers(0, len(v), len(v))) for _ in range(DRAWS)])
        return f(np.arange(len(v))), np.percentile(bs, 5), np.percentile(bs, 95), len(d)

    out = []
    for col, lab in (("main", "main (5-year before window)"), ("p1", "P1 short before window (years -2, -1)"),
                     ("p2", "P2 matched on before-trend and level"), ("p2_pretrend", "P2 pre-trend check (years -2,-1 vs -5..-3)")):
        m, lo, hi, n = wm(col)
        out.append(dict(test=lab, places=n, estimate=m, p05=lo, p95=hi))
    gcols = [c for c in P.columns if c.startswith("gap_")]
    G = max(abs(np.average(P[c].dropna(), weights=P.loc[P[c].notna(), "weight"])) for c in gcols)
    mm = out[0]
    out.append(dict(test="P3 bound, M = 1 (main 90% interval widened by the largest before-window gap)", places=mm["places"],
                    estimate=mm["estimate"], p05=mm["p05"] - G, p95=mm["p95"] + G, note=f"largest home-weighted before-year gap G = {G:.3f}"))
    S = pd.DataFrame(out)
    S["unit"] = "permits per 1,000 existing homes a year"
    S["pass_rule"] = ""
    moved = (S.loc[1, "estimate"] >= S.loc[0, "estimate"]) and (S.loc[2, "estimate"] >= S.loc[0, "estimate"])
    pt_pass = S.loc[3, "p05"] <= 0 <= S.loc[3, "p95"]
    S.loc[0, "pass_rule"] = f"P1 and P2 move toward 0 or above: {moved}; P2 pre-trend passes: {pt_pass}; candidate for Ryan: {moved and pt_pass}"
    S.to_csv(REFERENCE / "parking_p123.csv", index=False)
    P.to_csv(REFERENCE / "parking_p123_places.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 150)
    print(S.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
