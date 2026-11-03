"""Parking causal framework: Stage 1 rerun with the added 25k+ repeal cities (reference/parking_repeal_checks_v2.csv).
docs/parking/CAUSAL_FRAMEWORK_PLAN.md ("more mid-sized and large repeal cities", locked before coding).
Kept: checked rating at/near, effective year 2015-2024. Same difference-in-differences, windows and comparison rules as
the 76 places. The tool keeps using the 76 places.

    uv run python scripts/run_parking_causal_v2places.py
Outputs: reference/parking_causal_v2_places.csv, reference/parking_causal_v2_summary.csv
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


def boot_mean(v, w, rng):
    f = lambda i: np.sum(v[i] * w[i]) / np.sum(w[i])  # noqa: E731
    bs = np.array([f(rng.integers(0, len(v), len(v))) for _ in range(DRAWS)])
    return f(np.arange(len(v))), np.percentile(bs, 5), np.percentile(bs, 95)


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
    v2 = pd.read_csv(REFERENCE / "parking_repeal_checks_v2.csv")
    v2 = v2[v2["benchmark_rating_checked"].isin(["at", "near"]) & pd.to_numeric(v2["event_year"], errors="coerce").between(2015, 2024)].copy()
    pops = tax.drop_duplicates("prn_key").set_index("prn_key")["population"]
    v2["key"] = [cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, pops.get(r.prn_key)) for r in v2.itertuples()]
    z = v2["simultaneous_zoning_changes"].fillna("").str.strip().str.lower()
    v2["simultaneous_rewrite"] = ~(z.eq("") | z.str.startswith(("none", "unknown", "no ")))
    excluded |= set(v2["key"].dropna())
    cases = v2.dropna(subset=["key"])[["prn_key", "place", "state", "key", "event_year", "simultaneous_rewrite"]]
    cases["event_year"] = cases["event_year"].astype(int)
    eff = cmp.effects(p, cases, excluded, homes, popn, min_post=1)
    new = eff[(eff["status"] == "included") & (eff["outcome"] == "all")].copy()
    new["weight"] = new["homes"] * new["n_post"]
    dropped = pd.concat([eff[eff["status"] != "included"][["place", "status"]].drop_duplicates(),
                         v2[v2["key"].isna()][["place"]].assign(status="not in Census permit files")])
    cols = ["place", "state", "key", "event_year", "simultaneous_rewrite", "homes", "n_post", "effect", "weight"]
    allp = pd.concat([real[cols].assign(group="76 places"), new[cols].assign(group="added")], ignore_index=True)
    allp.to_csv(REFERENCE / "parking_causal_v2_places.csv", index=False)

    rng = np.random.default_rng(SEED)
    out = []
    for lab, d in (("76 places", allp[allp["group"] == "76 places"]), ("76 + added", allp)):
        m, lo, hi = boot_mean(d["effect"].values, d["weight"].values, rng)
        out.append(dict(test="Average effect (home-weighted)", set=lab, places=len(d), estimate=m, p05=lo, p95=hi))
        m, lo, hi = boot_mean(d["effect"].values, np.ones(len(d)), rng)
        out.append(dict(test="Average effect (equal-weight)", set=lab, places=len(d), estimate=m, p05=lo, p95=hi))
        a, b = d[~d["simultaneous_rewrite"].astype(bool)], d[d["simultaneous_rewrite"].astype(bool)]
        f = lambda x: np.average(x["effect"], weights=x["weight"])  # noqa: E731
        bs = [f(a.iloc[rng.integers(0, len(a), len(a))]) - f(b.iloc[rng.integers(0, len(b), len(b))]) for _ in range(DRAWS)]
        out.append(dict(test="E2 repeal alone minus repeal + rewrite", set=lab, places=len(d), estimate=f(a) - f(b),
                        p05=np.percentile(bs, 5), p95=np.percentile(bs, 95)))
        lh = np.log(d["homes"].values)
        cut = np.median(lh)
        hi_, lo_ = d[lh > cut], d[lh <= cut]
        g = lambda x: x["effect"].mean()  # noqa: E731
        bs = [g(hi_.iloc[rng.integers(0, len(hi_), len(hi_))]) - g(lo_.iloc[rng.integers(0, len(lo_), len(lo_))]) for _ in range(DRAWS)]
        out.append(dict(test="M3 city size, unweighted median split, large minus small (full sample)", set=lab, places=len(d),
                        estimate=g(hi_) - g(lo_), p05=np.percentile(bs, 5), p95=np.percentile(bs, 95)))
    S = pd.DataFrame(out)
    S["unit"] = "permits per 1,000 existing homes a year"
    S["note"] = "added places left out: " + "; ".join(f"{r.place} ({r.status})" for r in dropped.itertuples()) if len(dropped) else ""
    S.to_csv(REFERENCE / "parking_causal_v2_summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(new[["place", "state", "event_year", "n_post", "n_controls", "homes", "effect", "simultaneous_rewrite"]].round(2).to_string(index=False))
    print(dropped.to_string(index=False))
    print(S.drop(columns=["note"]).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
