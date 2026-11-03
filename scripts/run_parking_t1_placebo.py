"""Parking T1: non-residential placebo. Places that cut or removed parking minimums for non-residential uses only
(PRN taxonomy 'not_housing'), same difference-in-differences as the 76. docs/parking/CAUSAL_FRAMEWORK_PLAN.md (T1, locked).

    uv run python scripts/run_parking_t1_placebo.py
Outputs: reference/parking_t1_places.csv, reference/parking_t1_placebo.csv
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
    bps = rpc.read_bps_us()
    p = cmp.panel(bps)
    b = bps.assign(key=bps["state_fips"].astype(str).str.strip() + "|" + bps["bps_id"].astype(str).str.strip()).drop_duplicates(["key", "year"])
    u5 = b.pivot_table(index="key", columns="year", values="5plus_units", aggfunc="sum")
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001"))
    homes = homes[homes > 0]
    popn = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001"))
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    bench = {k for r in tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
             .drop_duplicates("prn_key").itertuples() if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")]
    excluded = bench | set(real["key"])
    c = tax[(tax["benchmark_rating"] == "not_housing") & (tax["place_type"] == "city") & tax["adopted_year"].between(2013, 2024)]
    housing = tax[tax["benchmark_rating"].isin(["at", "near", "weaker"])]
    rows, coded = [], []
    for r in c.sort_values(["prn_key", "adopted_year"]).drop_duplicates("prn_key").itertuples():
        e = int(r.adopted_year)
        hh = housing[(housing["prn_key"] == r.prn_key) & ((housing["adopted_year"] - e).abs() <= 3)]
        k = cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population)
        reason = "housing reform within 3 years" if len(hh) else ("not in permit files" if not k else ("among the 76 or benchmark list" if k in excluded else ""))
        coded.append(dict(prn_key=r.prn_key, place=r.place, state=r.state, event_year=e, key=k, excluded=reason))
    C = pd.DataFrame(coded)
    keep = C[C["excluded"] == ""]
    excluded_all = excluded | set(C["key"].dropna())
    for r in keep.itertuples():
        pre, post = cmp.windows(int(r.event_year))
        if len(pre) < cmp.PRE_YEARS_MIN or len(post) < 1 or r.key not in cmp.complete(p, pre + post) or r.key not in homes.index:
            continue
        ctrl, _ = cmp.controls(p, r.key, int(r.event_year), excluded_all - {r.key}, homes, popn)
        if not ctrl:
            continue
        e_all = (cmp._rate(p, [r.key], post, "units_total", homes) - cmp._rate(p, [r.key], pre, "units_total", homes)) - \
                (cmp._rate(p, ctrl, post, "units_total", homes) - cmp._rate(p, ctrl, pre, "units_total", homes))
        r5 = lambda ks, ys: float(np.nansum(u5.reindex(index=list(ks), columns=ys).values)) / len(ys) / homes.reindex(list(ks)).sum() * 1000  # noqa: E731
        e5 = (r5([r.key], post) - r5([r.key], pre)) - (r5(ctrl, post) - r5(ctrl, pre))
        rows.append(dict(place=r.place, state=r.state, key=r.key, event_year=r.event_year, n_post=len(post), n_controls=len(ctrl),
                         homes=float(homes[r.key]), weight=float(homes[r.key]) * len(post), effect_all=e_all, effect_5plus=e5))
    P = pd.DataFrame(rows)
    C.to_csv(REFERENCE / "parking_t1_coded.csv", index=False)
    P.to_csv(REFERENCE / "parking_t1_places.csv", index=False)
    rng = np.random.default_rng(SEED)
    out = []
    for col in ("effect_all", "effect_5plus"):
        d = P.dropna(subset=[col])
        v, w = d[col].values, d["weight"].values
        f = lambda i: np.sum(v[i] * w[i]) / np.sum(w[i])  # noqa: E731
        bs = np.array([f(rng.integers(0, len(v), len(v))) for _ in range(DRAWS)]) if len(v) else np.array([np.nan])
        lo, hi = np.percentile(bs, [5, 95])
        out.append(dict(outcome=col, places=len(d), feasible=len(d) >= 8, estimate=f(np.arange(len(v))) if len(v) else np.nan, p05=lo, p95=hi,
                        equal_weight=float(np.mean(v)) if len(v) else np.nan, passes=bool(lo <= 0 <= hi) if len(d) >= 8 else None))
    S = pd.DataFrame(out)
    S["unit"] = "permits per 1,000 existing homes a year"
    S["note"] = f"{len(C)} PRN not_housing entries coded; " + "; ".join(f"{k}: {v}" for k, v in C['excluded'].replace('', 'kept').value_counts().items())
    S.to_csv(REFERENCE / "parking_t1_placebo.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
