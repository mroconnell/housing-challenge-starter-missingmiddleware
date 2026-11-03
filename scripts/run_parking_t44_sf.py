"""Parking test 44: does the old single-family minimum (2.0 vs <= 1.0 per house) change the 1-unit permit effect of repeal?
docs/parking/CAUSAL_FRAMEWORK_PLAN.md ("Test 44" and additions, locked 2026-11-03).

    uv run python scripts/run_parking_t44_sf.py
Outputs: reference/parking_t44.csv, reference/parking_t44_groups.csv
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
    tab = {c: b.pivot_table(index="key", columns="year", values=c, aggfunc="sum") for c in ("1unit_units", "5plus_units")}
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
    om = pd.read_csv(REFERENCE / "parking_old_minimums.csv").drop_duplicates("prn_key")
    real = real.merge(om[["prn_key", "old_min_single_family", "confidence"]], on="prn_key", how="left")
    real["group"] = np.where(real["old_min_single_family"] == 2.0, "high", np.where(real["old_min_single_family"] <= 1.0, "low", None))

    def rate(col, keys, yrs):
        d = homes.reindex(list(keys)).sum()
        return float(np.nansum(tab[col].reindex(index=list(keys), columns=yrs).values)) / len(yrs) / d * 1000 if d > 0 else np.nan

    rows = []
    for r in real.itertuples():
        e = int(r.event_year)
        pre, post = cmp.windows(e)
        post = post[: int(r.n_post)]
        ctrl, _ = cmp.controls(p, r.key, e, excluded - {r.key}, homes, popn)
        if not ctrl or r.key not in homes.index:
            continue
        did = lambda col, a, b_: (rate(col, [r.key], b_) - rate(col, [r.key], a)) - (rate(col, ctrl, b_) - rate(col, ctrl, a))  # noqa: E731
        early, late = [y for y in pre if y <= e - 3], [y for y in pre if y >= e - 2]
        rows.append(dict(place=r.place, state=r.state, key=r.key, group=r.group, confidence=r.confidence, weight=r.weight, homes=r.homes,
                         event_year=e, region=str(geo.loc[r.key, "division"]), sf=did("1unit_units", pre, post),
                         apt=did("5plus_units", pre, post), sf_backtest=did("1unit_units", early, late) if early and late else np.nan))
    P = pd.DataFrame(rows)
    rng = np.random.default_rng(SEED)

    def contrast(d, col, weighted=True):
        d = d.dropna(subset=[col])
        h, l = d[d["group"] == "high"], d[d["group"] == "low"]
        if len(h) < 2 or len(l) < 2:
            return dict(n_high=len(h), n_low=len(l))
        f = (lambda x: np.average(x[col], weights=x["weight"])) if weighted else (lambda x: x[col].mean())
        bs = np.array([f(h.iloc[rng.integers(0, len(h), len(h))]) - f(l.iloc[rng.integers(0, len(l), len(l))]) for _ in range(DRAWS)])
        est = f(h) - f(l)
        return dict(n_high=len(h), n_low=len(l), high=f(h), low=f(l), estimate=est, p05=np.percentile(bs, 5), p95=np.percentile(bs, 95),
                    p0125=np.percentile(bs, 1.25), p9875=np.percentile(bs, 98.75), mde=1.645 * bs.std(ddof=1))

    out = []
    G = P[P["group"].notna()]
    for lab, d, col, wt in (("main: 1-unit homes, home-weighted", G, "sf", True), ("equal-weight", G, "sf", False),
                            ("without Austin", G[G["place"] != "Austin"], "sf", True), ("without Raleigh", G[G["place"] != "Raleigh"], "sf", True),
                            ("high-confidence codes only", G[G["confidence"] == "high"], "sf", True),
                            ("backtest: years -2,-1 vs -5..-3 (must include 0)", G, "sf_backtest", True),
                            ("same contrast on 5+ unit homes (optional)", G, "apt", True)):
        out.append(dict(test=f"44 {lab}", **contrast(d, col, wt)))
    main = out[0]
    bt = out[5]
    supported = main.get("p0125", -1) > 0 and bt.get("p05", 1) <= 0 <= bt.get("p95", -1)
    S = pd.DataFrame(out)
    S["unit"] = "1-unit (or 5+) homes permitted per 1,000 existing homes a year; high (old SF min 2.0) minus low (<= 1.0)"
    S["reading"] = ""
    S.loc[0, "reading"] = ("supported" if supported else "not supported") + "; overall 1-unit effect (FU6) +0.00 (-0.83 to +0.76)"
    S.to_csv(REFERENCE / "parking_t44.csv", index=False)
    T = G.assign(size_tercile=pd.qcut(G["homes"], 3, labels=["small", "middle", "large"])).groupby("group").agg(
        places=("key", "size"), median_homes=("homes", "median"), median_event_year=("event_year", "median"),
        regions=("region", lambda s: "; ".join(f"{k} {v}" for k, v in s.value_counts().items())),
        sizes=("size_tercile", lambda s: "; ".join(f"{k} {v}" for k, v in s.value_counts().items())),
        places_list=("place", lambda s: ", ".join(s))).reset_index()
    T.to_csv(REFERENCE / "parking_t44_groups.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.drop(columns=["unit"]).round(3).to_string(index=False))
    print(T.drop(columns="places_list").to_string(index=False))


if __name__ == "__main__":
    main()
