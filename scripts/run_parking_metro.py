"""Parking: each repeal city against its own metro neighbours (docs/parking/METRO_PLAN.md).

    uv run --all-extras python scripts/run_parking_metro.py
Outputs: reference/parking_metro_places.csv, reference/parking_metro_summary.csv
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

MIN_HOMES, SEEDS = 1000, range(20261101, 20261106)


def summ(d):
    d = d.dropna(subset=["effect"])
    w = d["homes"] * d["n_post"]
    rng = np.random.default_rng(20261101)
    bs = [np.average(d["effect"].values[i], weights=w.values[i]) for i in (rng.integers(0, len(d), len(d)) for _ in range(2000))]
    return dict(places=len(d), weighted=float(np.average(d["effect"], weights=w)), p05=float(np.percentile(bs, 5)),
                p95=float(np.percentile(bs, 95)), median=float(d["effect"].median()))


def main() -> None:
    bps = rpc.read_bps_us()
    p = cmp.panel(bps)
    b = bps.assign(key=bps["state_fips"].astype(str).str.strip() + "|" + bps["bps_id"].astype(str).str.strip())
    last = b.sort_values("year").drop_duplicates("key", keep="last").set_index("key")
    cbsa = last["cbsa"].astype(str).str.strip()
    csa = last["csa"].astype(str).str.strip()
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001"))
    homes = homes[homes > 0]

    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")][["key", "place", "event_year", "effect"]]
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    base_ex = {k for r in tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")].drop_duplicates("prn_key").itertuples()
               if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))} | set(real["key"])
    mat = set(pd.read_csv(REFERENCE / "parking_reform_material.csv").query("material")["prn_key"])
    myear = {}
    for r in tax[tax["prn_key"].isin(mat)].itertuples():
        k = cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population)
        if k:
            myear[k] = min(myear.get(k, 9999), r.adopted_year if pd.notna(r.adopted_year) else -1)

    def metro_controls(pp, key, event_year, excluded, hh, population=None):
        pre, post = cmp.windows(event_year)
        end = (pre + post)[-1]
        ex = excluded | {k for k, y in myear.items() if y <= end}
        ok = cmp.complete(pp, pre + post) & set(hh[hh >= MIN_HOMES].index)
        for lab, code in (("metro", cbsa), ("combined area", csa)):
            c0 = code.get(key, "")
            if c0 in ("", "99999", "999", "nan"):
                continue
            c = [k for k in ok if k != key and k not in ex and code.get(k) == c0]
            if len(c) >= cmp.MIN_CONTROLS:
                return c, lab
        return [], "no metro peers"

    cmp.controls = metro_controls
    e = cmp.effects(p, real[["key", "event_year"]], base_ex, homes, min_post=1)
    e = e[(e["status"] == "included") & (e["outcome"] == "all")].merge(real[["key", "place", "effect"]].rename(columns={"effect": "headline_effect"}), on="key")
    e.to_csv(REFERENCE / "parking_metro_places.csv", index=False)
    usable = e[e["n_controls"] >= cmp.MIN_CONTROLS]
    head = real.merge(e[["key", "homes", "n_post"]], on="key")
    rows = [dict(group="headline comparison (same places)", **summ(head[head["key"].isin(usable["key"])])),
            dict(group="metro neighbours", **summ(usable)),
            dict(group="metro neighbours, without San Francisco", **summ(usable[usable["place"] != "San Francisco"])),
            dict(group="metro neighbours, without SF and Minneapolis", **summ(usable[~usable["place"].isin(["San Francisco", "Minneapolis"])]))]

    # noise check: never-reformed places with metro peers, given the real repeal years
    pool = [k for k in homes[homes >= MIN_HOMES].index if k not in base_ex and k not in myear and cbsa.get(k, "99999") not in ("99999", "")]
    years = real["event_year"].astype(int).values
    for s in SEEDS:
        rng = np.random.default_rng(s)
        fk = rng.choice(sorted(pool), size=len(real), replace=False)
        fe = cmp.effects(p, pd.DataFrame({"key": fk, "event_year": rng.choice(years, size=len(fk))}), base_ex, homes, min_post=1)
        fe = fe[(fe["status"] == "included") & (fe["outcome"] == "all") & (fe["n_controls"] >= cmp.MIN_CONTROLS)]
        rows.append(dict(group=f"noise check: random never-reformed places, seed {s}", **summ(fe)))
    S = pd.DataFrame(rows)
    S.to_csv(REFERENCE / "parking_metro_summary.csv", index=False)
    pd.set_option("display.width", 200)
    print(S.round(2).to_string(index=False))
    print(e[e["place"].isin(["San Francisco", "Minneapolis", "St. Paul", "Seattle", "Austin", "San Jose", "Raleigh", "Buffalo"])][
        ["place", "pop_window", "n_controls", "rate_before", "rate_after", "ctrl_before", "ctrl_after", "effect", "headline_effect"]].round(2).to_string(index=False))
    print("no metro peers:", e.loc[e["n_controls"] < cmp.MIN_CONTROLS, "place"].tolist())


if __name__ == "__main__":
    main()
