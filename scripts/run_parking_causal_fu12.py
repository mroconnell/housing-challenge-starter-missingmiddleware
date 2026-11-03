"""Parking causal follow-ups FU1 (apartment-share matching) and FU2 (Austin against Sun Belt peers).
docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Stage 1 follow-ups" (owner OK 2026-11-03; post hoc to Stage 1; locked before counting).

    uv run python scripts/run_parking_causal_fu12.py
Outputs: reference/parking_causal_fu1_places.csv, reference/parking_causal_fu12_summary.csv
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

SEED, DRAWS = 20261103, 2000
PEERS = [("48", "Dallas"), ("48", "Houston"), ("48", "San Antonio"), ("48", "Fort Worth"), ("04", "Phoenix"),
         ("47", "Nashville-Davidson"), ("13", "Atlanta"), ("12", "Tampa"), ("12", "Orlando"), ("12", "Jacksonville"), ("32", "Las Vegas")]


def main() -> None:
    bps = rpc.read_bps_us()
    p = cmp.panel(bps)
    b = bps.assign(key=bps["state_fips"].astype(str).str.strip() + "|" + bps["bps_id"].astype(str).str.strip()).drop_duplicates(["key", "year"])
    u5 = b.pivot_table(index="key", columns="year", values="5plus_units", aggfunc="sum")
    ut = p.pivot_table(index="key", columns="year", values="units_total", aggfunc="sum")
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

    def share(keys, yrs):
        a = np.nansum(u5.reindex(index=list(keys), columns=yrs).values)
        t = np.nansum(ut.reindex(index=list(keys), columns=yrs).values)
        return a / t if t > 0 else np.nan

    def did(key, ctrl, pre, post):
        t0, t1 = cmp._rate(p, [key], pre, "units_total", homes), cmp._rate(p, [key], post, "units_total", homes)
        c0, c1 = cmp._rate(p, ctrl, pre, "units_total", homes), cmp._rate(p, ctrl, post, "units_total", homes)
        return (t1 - t0) - (c1 - c0), t0, t1, c0, c1

    rows = []
    for r in real.itertuples():
        pre, post = cmp.windows(int(r.event_year))
        post = post[: int(r.n_post)]
        ctrl, _ = cmp.controls(p, r.key, int(r.event_year), excluded - {r.key}, homes, popn)
        s0 = share([r.key], pre)
        cs = pd.Series({c: share([c], pre) for c in ctrl}).dropna()
        near = list(cs[(cs - s0).abs() <= 0.10].index)
        fill = len(near) < 5
        if fill:
            near = list((cs - s0).abs().sort_values().index[:5])
        eff, *_ = did(r.key, near, pre, post)
        rows.append(dict(place=r.place, state=r.state, key=r.key, share_5plus=s0, ctrl_share_all=share(ctrl, pre),
                         ctrl_share_matched=share(near, pre), n_controls=len(ctrl), n_matched=len(near), filled_to_5=fill,
                         effect_main=r.effect, effect_share_matched=eff, weight=r.weight))
    F = pd.DataFrame(rows)
    F.to_csv(REFERENCE / "parking_causal_fu1_places.csv", index=False)
    rng = np.random.default_rng(SEED)
    out = []
    G = F.dropna(subset=["effect_share_matched"])
    for col, lab in (("effect_main", "main (for reference)"), ("effect_share_matched", "FU1 apartment-share matched")):
        for wlab, w in (("home-weighted", G["weight"].values), ("equal-weight", np.ones(len(G)))):
            v = G[col].values
            f = lambda i: np.sum(v[i] * w[i]) / np.sum(w[i])  # noqa: E731
            bs = np.array([f(rng.integers(0, len(v), len(v))) for _ in range(DRAWS)])
            out.append(dict(test=f"{lab}, {wlab}", places=len(G), estimate=f(np.arange(len(v))), p05=np.percentile(bs, 5), p95=np.percentile(bs, 95)))
    out.append(dict(test="FU1 check: mean before-window 5+ share, repeal places / all comparison / matched comparison",
                    places=len(G), estimate=np.nan,
                    note=f"{G['share_5plus'].mean():.3f} / {G['ctrl_share_all'].mean():.3f} / {G['ctrl_share_matched'].mean():.3f}; "
                         f"{int(G['filled_to_5'].sum())} places filled to the 5 nearest"))
    # FU2 Austin vs Sun Belt peers
    a = real[real["place"] == "Austin"].iloc[0]
    pre, post = cmp.windows(int(a.event_year))
    post = post[: int(a.n_post)]
    peers = [k for st, n in PEERS if (k := cmp.match_place(p, st, n, None)) and k not in excluded and k in homes.index]
    eff, t0, t1, c0, c1 = did(a.key, peers, pre, post)
    per = []
    for k in peers:
        per.append(f"{geo.loc[k, 'name']} {cmp._rate(p, [k], pre, 'units_total', homes):.1f}->{cmp._rate(p, [k], post, 'units_total', homes):.1f}")
    out.append(dict(test="FU2 Austin vs Sun Belt peers (DiD)", places=len(peers), estimate=eff,
                    note=f"Austin {t0:.1f}->{t1:.1f}; peers pooled {c0:.1f}->{c1:.1f}; main effect {a.effect:.2f}; " + "; ".join(per)))
    S = pd.DataFrame(out)
    S["unit"] = "permits per 1,000 existing homes a year"
    S.to_csv(REFERENCE / "parking_causal_fu12_summary.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 400)
    print(S.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
