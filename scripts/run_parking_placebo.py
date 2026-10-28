"""Parking placebo test (docs/parking/PLACEBO_PLAN.md): the same effect calculation on places that never
removed parking minimums, given the real places' repeal years.

    uv run --all-extras python scripts/run_parking_placebo.py          # registered run (20 placebo places per real place)
    uv run --all-extras python scripts/run_parking_placebo.py --full   # every eligible place (owner, 2026-10-27)
Outputs: reference/parking_placebo_places.csv (each placebo place's effect), reference/parking_placebo_summary.csv;
with --full, reference/parking_placebo_full_places.csv and _full_summary.csv
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
from missing_middleware.parking import checks  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

SEED, PER_PLACE, SETS = 20261027, 20, 500
SETS_FULL = 20_000
MIN_STANDINS = 20  # full run: widen state -> Census division -> nation until at least this many stand-ins  # full-pool run: 500 sets left the high end varying by about 0.1 from draw to draw (2026-10-28)


def main() -> None:
    full = "--full" in sys.argv
    tag = "_full" if full else ""
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
    rows, scopes = [], []
    for i, r in (real.iloc[0:0] if "--summary-only" in sys.argv else real).iterrows():
        st = r["key"].split("|")[0]
        pre, post = cmp.windows(int(r["event_year"]))
        post = post[: int(r["n_post"])]
        ok = cmp.complete(p, pre + post) & set(homes.index)
        pop0 = popn.get(r["key"], np.nan)
        if pd.isna(pop0):  # rescued South Bend: the city's own population (SALVAGE_PLAN.md)
            pop0 = r.get("population", np.nan)
        size_ok = [k for k in ok if k not in excluded and 0.5 * pop0 <= popn.get(k, np.nan) <= 2 * pop0]
        cand = [k for k in size_ok if k.startswith(st + "|")]
        scope = "state"
        if full and len(cand) < MIN_STANDINS:  # widen for big cities (Ask-why review, owner 2026-10-28)
            div = geo["division"].get(r["key"], "")
            cand, scope = [k for k in size_ok if geo["division"].get(k, "") == div], "division"
            if len(cand) < MIN_STANDINS:
                cand, scope = size_ok, "nation"
        scopes.append(dict(real_place=r["place"], scope=scope, standins=len(cand)))
        if not cand:
            continue
        print(i, r["place"], len(cand), flush=True)
        pick = list(rng.choice(sorted(cand), size=len(cand) if full else min(PER_PLACE, len(cand)), replace=False))
        cases = pd.DataFrame({"key": pick, "event_year": int(r["event_year"])})
        eff = cmp.effects(p, cases, excluded | {r["key"]}, homes, popn, min_post=1)
        eff = eff[(eff["status"] == "included") & (eff["outcome"] == "all")]
        eff = eff[eff["n_post"] == r["n_post"]]
        for x in eff.itertuples():
            rows.append(dict(real_index=i, real_place=r["place"], placebo_key=x.key, event_year=int(r["event_year"]),
                             n_post=int(x.n_post), homes=x.homes, effect=x.effect))
    if rows:
        pl = pd.DataFrame(rows)
        pl["weight"] = pl["homes"] * pl["n_post"]
        pl.round(4).to_csv(REFERENCE / f"parking_placebo{tag}_places.csv", index=False)
        pd.DataFrame(scopes).to_csv(REFERENCE / f"parking_placebo{tag}_scopes.csv", index=False)
    else:  # --summary-only: reuse the saved placebo places
        pl = pd.read_csv(REFERENCE / f"parking_placebo{tag}_places.csv")
    # placebo places whose own comparison pool was empty have no effect; they cannot be drawn (Ask-why checks)
    dropped = int(pl["effect"].isna().sum())
    pl = pl.dropna(subset=["effect", "weight"])
    pl = pl[pl["weight"] > 0]
    flags = checks.definition(pd.DataFrame(), "placebo places without an effect (left out)", pd.Series([True] * dropped, dtype=bool))
    if full:
        sc = pd.read_csv(REFERENCE / f"parking_placebo{tag}_scopes.csv")
        flags += checks.definition(sc, "real places with fewer than 20 stand-ins", sc["standins"] < MIN_STANDINS)
    checks.report(flags, REFERENCE / f"parking_placebo{tag}_checks.csv")
    rng = np.random.default_rng(SEED + 1)  # set draws use their own stream, so --summary-only reproduces the full run
    groups = {i: g for i, g in pl.groupby("real_index")}
    n_sets = SETS_FULL if full else SETS
    if full:
        draws = np.column_stack([rng.integers(0, len(g), n_sets) for g in groups.values()])
        eff_m = np.column_stack([g["effect"].values[draws[:, j]] for j, g in enumerate(groups.values())])
        w_m = np.column_stack([g["weight"].values[draws[:, j]] for j, g in enumerate(groups.values())])
        avgs = (eff_m * w_m).sum(axis=1) / w_m.sum(axis=1)
    else:
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
                sets=n_sets, real_places_matched=len(groups), real_places=len(real), placebo_places=len(pl),
                spread_real_places=sd_real, spread_placebo_places=sd_pl,
                range_from_placebo_low=real_avg + (np.percentile(avgs, 5) - np.percentile(avgs, 50)),
                range_from_placebo_high=real_avg + (np.percentile(avgs, 95) - np.percentile(avgs, 50)))
    pd.DataFrame([summ]).round(4).to_csv(REFERENCE / f"parking_placebo{tag}_summary.csv", index=False)
    for k, v in summ.items():
        print(k, round(v, 3) if isinstance(v, float) else v)


if __name__ == "__main__":
    main()
