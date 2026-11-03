"""Parking causal framework, E2 completed as a 2x2: repeal alone, repeal + rewrite, rewrite only (TOD upzoned places).
docs/parking/CAUSAL_FRAMEWORK_PLAN.md (E2 2x2, locked before counting).

    uv run python scripts/run_parking_causal_e2x2.py
Outputs: reference/parking_causal_e2x2_places.csv, reference/parking_causal_e2x2_summary.csv
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
    real = real[(real["status"] == "included") & (real["outcome"] == "all")]
    excluded |= set(real["key"])
    rep_geo = set(real["acs_geoid"])
    tod = pd.read_csv(REFERENCE / "tod_places_for_parking_2x2.csv", dtype={"geoid": str})
    up = tod[tod["group"] == "upzoned"].copy()
    up["acs_geoid"] = np.where(up["geo_type"] == "place", "160|", "060|") + up["geoid"].str.zfill(7)
    by_geo = {g: k for k, g in geo["acs_geoid"].items()}
    up["key"] = up["acs_geoid"].map(by_geo)
    # mechanical fallback when the GEOID differs (e.g. Indianapolis "city (balance)"): match by name within the state
    name = up["place_name"].str.replace(r" city.*$| town$| village$", "", regex=True)
    miss = up["key"].isna()
    up.loc[miss, "key"] = [cmp.match_place(p, rpc.STATE_FIPS.get(st, "??"), n, None) for st, n in zip(up.loc[miss, "state"], name[miss])]
    excluded |= set(up["key"].dropna())
    up = up[up["upzoning_year"].between(2013, 2024) & ~up["acs_geoid"].isin(rep_geo)]
    up["cell"] = np.where(up["parking_changed_with_upzoning"] == "yes", "upzoning + station-area parking removal", "rewrite only")
    rows = []
    for r in up.itertuples():
        if not isinstance(r.key, str) or r.key not in homes.index:
            rows.append(dict(place=r.place_name, state=r.state, cell=r.cell, event_year=int(r.upzoning_year), note="not matched to permit data"))
            continue
        e = int(r.upzoning_year)
        pre, post = cmp.windows(e)
        ctrl, label = cmp.controls(p, r.key, e, excluded - {r.key}, homes, popn)
        if not ctrl:
            rows.append(dict(place=r.place_name, state=r.state, cell=r.cell, event_year=e, key=r.key, n_controls=0, note="no comparison places"))
            continue
        t0, t1 = cmp._rate(p, [r.key], pre, "units_total", homes), cmp._rate(p, [r.key], post, "units_total", homes)
        c0, c1 = cmp._rate(p, ctrl, pre, "units_total", homes), cmp._rate(p, ctrl, post, "units_total", homes)
        rows.append(dict(place=r.place_name, state=r.state, cell=r.cell, event_year=e, key=r.key, n_pre=len(pre), n_post=len(post),
                         n_controls=len(ctrl), pool=label, homes=float(homes[r.key]), effect=(t1 - t0) - (c1 - c0),
                         weight=float(homes[r.key]) * len(post), note=""))
    U = pd.DataFrame(rows)
    U.to_csv(REFERENCE / "parking_causal_e2x2_places.csv", index=False)
    cells = {"repeal alone": real[~real["simultaneous_rewrite"]], "repeal + rewrite": real[real["simultaneous_rewrite"]]}
    for c in ("rewrite only", "upzoning + station-area parking removal"):
        cells[c] = U[(U["cell"] == c)].dropna(subset=["effect"])
    rng = np.random.default_rng(SEED)
    f = lambda d: np.average(d["effect"], weights=d["weight"])  # noqa: E731
    out, draws = [], {}
    for c, d in cells.items():
        bs = np.array([f(d.iloc[rng.integers(0, len(d), len(d))]) for _ in range(DRAWS)])
        draws[c] = bs
        out.append(dict(cell=c, places=len(d), mean_effect=f(d), p05=np.percentile(bs, 5), p95=np.percentile(bs, 95)))
    inter = f(cells["repeal + rewrite"]) - f(cells["repeal alone"]) - f(cells["rewrite only"])
    ib = draws["repeal + rewrite"] - draws["repeal alone"] - draws["rewrite only"]
    out.append(dict(cell="interaction: (repeal + rewrite) - (repeal alone) - (rewrite only)", places=np.nan, mean_effect=inter,
                    p05=np.percentile(ib, 5), p95=np.percentile(ib, 95), mde=1.645 * ib.std(ddof=1)))
    S = pd.DataFrame(out)
    S["unit"] = "permits per 1,000 existing homes a year, against matched places that did neither"
    S.to_csv(REFERENCE / "parking_causal_e2x2_summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(U[["place", "cell", "event_year", "n_pre", "n_post", "n_controls", "effect", "note"]].round(2).to_string(index=False))
    print(S.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
