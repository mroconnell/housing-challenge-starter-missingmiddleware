"""Parking placebo test (docs/parking/PLACEBO_PLAN.md): the same effect calculation on places that never
removed parking minimums, given the real places' repeal years.

    uv run --all-extras python scripts/run_parking_placebo.py
Outputs: reference/parking_placebo_places.csv (each placebo place's effect), reference/parking_placebo_summary.csv
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

SEED, PER_PLACE, SETS = 20261027, 20, 500


def main() -> None:
    p = cmp.panel(rpc.read_bps_us())
    homes_geo = rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001")
    pop_geo = rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001")
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(homes_geo)
    homes = homes[homes > 0]
    popn = geo["acs_geoid"].map(pop_geo)
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    reformed = tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
    excluded = set()
    for r in reformed.drop_duplicates("prn_key").itertuples():
        k = cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population)
        if k:
            excluded.add(k)
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].reset_index(drop=True)
    excluded |= set(real["key"])
    rng = np.random.default_rng(SEED)
    rows = []
    for i, r in real.iterrows():
        st = r["key"].split("|")[0]
        pre, post = cmp.windows(int(r["event_year"]))
        post = post[: int(r["n_post"])]
        ok = cmp.complete(p, pre + post) & set(homes.index)
        pop0 = popn.get(r["key"], np.nan)
        cand = [k for k in ok if k.startswith(st + "|") and k not in excluded and 0.5 * pop0 <= popn.get(k, np.nan) <= 2 * pop0]
        if not cand:
            continue
        pick = list(rng.choice(sorted(cand), size=min(PER_PLACE, len(cand)), replace=False))
        cases = pd.DataFrame({"key": pick, "event_year": int(r["event_year"])})
        eff = cmp.effects(p, cases, excluded | {r["key"]}, homes, popn, min_post=1)
        eff = eff[(eff["status"] == "included") & (eff["outcome"] == "all")]
        eff = eff[eff["n_post"] == r["n_post"]]
        for x in eff.itertuples():
            rows.append(dict(real_index=i, real_place=r["place"], placebo_key=x.key, event_year=int(r["event_year"]),
                             n_post=int(x.n_post), homes=x.homes, effect=x.effect))
    pl = pd.DataFrame(rows)
    pl["weight"] = pl["homes"] * pl["n_post"]
    pl.round(4).to_csv(REFERENCE / "parking_placebo_places.csv", index=False)
    groups = {i: g for i, g in pl.groupby("real_index")}
    avgs = []
    for _ in range(SETS):
        picks = [g.iloc[rng.integers(0, len(g))] for g in groups.values()]
        s = pd.DataFrame(picks)
        avgs.append(np.average(s["effect"], weights=s["weight"]))
    avgs = np.array(avgs)
    real_avg = float(np.average(real["effect"], weights=real["homes"] * real["n_post"]))
    w_real = real["homes"] * real["n_post"]
    sd_real = float(np.sqrt(np.average((real["effect"] - real_avg) ** 2, weights=w_real)))
    pm = np.average(pl["effect"], weights=pl["weight"])
    sd_pl = float(np.sqrt(np.average((pl["effect"] - pm) ** 2, weights=pl["weight"])))
    summ = dict(real_average=real_avg, placebo_p05=float(np.percentile(avgs, 5)), placebo_p50=float(np.percentile(avgs, 50)),
                placebo_p95=float(np.percentile(avgs, 95)), share_placebo_at_or_below_real=float((avgs <= real_avg).mean()),
                real_places_matched=len(groups), real_places=len(real), placebo_places=len(pl),
                spread_real_places=sd_real, spread_placebo_places=sd_pl,
                range_from_placebo_low=real_avg + (np.percentile(avgs, 5) - np.percentile(avgs, 50)),
                range_from_placebo_high=real_avg + (np.percentile(avgs, 95) - np.percentile(avgs, 50)))
    pd.DataFrame([summ]).round(4).to_csv(REFERENCE / "parking_placebo_summary.csv", index=False)
    for k, v in summ.items():
        print(k, round(v, 3) if isinstance(v, float) else v)


if __name__ == "__main__":
    main()
