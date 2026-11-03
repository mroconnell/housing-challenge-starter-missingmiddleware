"""Parking test 40: power and coverage simulation for the main matched difference-in-differences.
docs/parking/CAUSAL_FRAMEWORK_PLAN.md ("Tests 40 and 41", locked 2026-11-03).

    uv run python scripts/run_parking_t40_power.py
Output: reference/parking_t40_power.csv
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

SEED, SIMS, BOOT, N = 20261104, 200, 1000, 75
SIZES = {0: 0.0, 5000: 5000 / 13343.385, 10000: 10000 / 13343.385, 20000: 20000 / 13343.385}
PROFILES = {"constant": (1, 1, 1), "ramp": (1 / 3, 2 / 3, 1), "early then fade": (1, 1, 0.5)}


def main() -> None:
    p = cmp.panel(rpc.read_bps_us())
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001"))
    homes = homes[homes > 0]
    popn = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001"))
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    bench = {k for r in tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
             .drop_duplicates("prn_key").itertuples() if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")]
    base_ex = bench | set(real["key"])
    pools = set()
    for r in real.itertuples():
        pools |= set(cmp.controls(p, r.key, int(r.event_year), base_ex - {r.key}, homes, popn)[0])
    pools = np.array(sorted(pools & set(homes.index)))
    county = geo["state_fips"].astype(str) + geo["county_fips"].astype(str).str.zfill(3)
    events = real["event_year"].astype(int).values
    rng = np.random.default_rng(SEED)
    R = lambda ks, ys: cmp._rate(p, ks, ys, "units_total", homes)  # noqa: E731
    sims = []
    for s in range(SIMS):
        fake = rng.choice(pools, N, replace=False)
        ev = rng.choice(events, N)
        ex = base_ex | set(fake)
        rows = []
        for k, e in zip(fake, ev):
            pre, post = cmp.windows(int(e))
            if not pre or not post or k not in cmp.complete(p, pre + post):
                continue
            ctrl, _ = cmp.controls(p, k, int(e), ex - {k}, homes, popn)
            if not ctrl:
                continue
            base = (R([k], post) - R([k], pre)) - (R(ctrl, post) - R(ctrl, pre))
            if not np.isfinite(base):
                continue
            prof = {nm: float(np.mean(v[: len(post)])) for nm, v in PROFILES.items()}
            rows.append(dict(base=base, w=float(homes[k]) * len(post), cl=county.get(k, k), **{f"m_{nm}": v for nm, v in prof.items()}))
        d = pd.DataFrame(rows)
        cls = d["cl"].unique()
        idx = {c: np.where(d["cl"].values == c)[0] for c in cls}
        draws = [np.concatenate([idx[c] for c in rng.choice(cls, len(cls))]) for _ in range(BOOT)]
        w = d["w"].values
        for nm in PROFILES:
            for G, delta in SIZES.items():
                v = d["base"].values + delta * d[f"m_{nm}"].values
                truth = float(np.sum(delta * d[f"m_{nm}"].values * w) / np.sum(w))
                est = float(np.sum(v * w) / np.sum(w))
                bs = np.array([np.sum(v[i] * w[i]) / np.sum(w[i]) for i in draws])
                lo, hi = np.percentile(bs, [5, 95])
                sims.append(dict(sim=s, profile=nm, wi_gain=G, truth=truth, estimate=est, lo=lo, hi=hi, places=len(d)))
        if (s + 1) % 20 == 0:
            print(f"sim {s + 1}/{SIMS}", flush=True)
    S = pd.DataFrame(sims)
    out = S.groupby(["profile", "wi_gain"]).apply(lambda g: pd.Series(dict(
        sims=len(g), mean_truth=g["truth"].mean(), mean_estimate=g["estimate"].mean(),
        coverage=float(((g["lo"] <= g["truth"]) & (g["truth"] <= g["hi"])).mean()),
        power_right_sign=float((g["lo"] > 0).mean()) if g.name[1] > 0 else np.nan,
        false_positive=float(((g["lo"] > 0) | (g["hi"] < 0)).mean()) if g.name[1] == 0 else np.nan,
        mean_width=float((g["hi"] - g["lo"]).mean()), places=float(g["places"].mean()))), include_groups=False).reset_index()
    out["unit"] = "permits per 1,000 existing homes a year; wi_gain = injected Wisconsin homes 2027-2031"
    out.to_csv(REFERENCE / "parking_t40_power.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.drop(columns="unit").round(3).to_string(index=False))


if __name__ == "__main__":
    main()
