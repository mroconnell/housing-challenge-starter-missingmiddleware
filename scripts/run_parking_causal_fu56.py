"""Parking causal follow-ups FU5 (apartment-only outcome) and FU6 (single-family near-placebo).
docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Stage 1 follow-ups" (owner OK 2026-11-03 02:29; post hoc; locked before counting).

    uv run python scripts/run_parking_causal_fu56.py
Outputs: reference/parking_causal_fu56_places.csv, reference/parking_causal_fu56_summary.csv
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
ACS = RAW / "census_acs5_2024_tbsf"


def main() -> None:
    bps = rpc.read_bps_us()
    p = cmp.panel(bps)
    b = bps.assign(key=bps["state_fips"].astype(str).str.strip() + "|" + bps["bps_id"].astype(str).str.strip()).drop_duplicates(["key", "year"])
    tab = {c: b.pivot_table(index="key", columns="year", values=c, aggfunc="sum") for c in ("5plus_units", "1unit_units")}
    tab["units_total"] = p.pivot_table(index="key", columns="year", values="units_total", aggfunc="sum")
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(rpc.acs_table(ACS / "acsdt5y2024-b25002.dat", "B25002_E001"))
    homes = homes[homes > 0]
    h5 = sum(geo["acs_geoid"].map(rpc.acs_table(ACS / "acsdt5y2024-b25024.dat", f"B25024_E00{i}")).fillna(0) for i in (6, 7, 8, 9))
    popn = geo["acs_geoid"].map(rpc.acs_table(ACS / "acsdt5y2024-b01003.dat", "B01003_E001"))
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    excluded = {k for r in tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
                .drop_duplicates("prn_key").itertuples() if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].copy()
    excluded |= set(real["key"])

    def rate(col, keys, yrs, den):
        t = tab[col].reindex(index=list(keys), columns=yrs)
        d = den.reindex(list(keys)).sum()
        return float(np.nansum(t.values)) / len(yrs) / d * 1000 if d > 0 else np.nan

    def did(col, key, ctrl, pre, post, den):
        return (rate(col, [key], post, den) - rate(col, [key], pre, den)) - (rate(col, ctrl, post, den) - rate(col, ctrl, pre, den))

    rows = []
    for r in real.itertuples():
        pre, post = cmp.windows(int(r.event_year))
        post = post[: int(r.n_post)]
        ctrl, _ = cmp.controls(p, r.key, int(r.event_year), excluded - {r.key}, homes, popn)
        rows.append(dict(place=r.place, state=r.state, key=r.key, weight=r.weight,
                         total_check=did("units_total", r.key, ctrl, pre, post, homes),
                         apt_per_existing_apt=did("5plus_units", r.key, ctrl, pre, post, h5),
                         apt_per_all_homes=did("5plus_units", r.key, ctrl, pre, post, homes),
                         single_family=did("1unit_units", r.key, ctrl, pre, post, homes)))
    P = pd.DataFrame(rows).replace([np.inf, -np.inf], np.nan)
    P.to_csv(REFERENCE / "parking_causal_fu56_places.csv", index=False)
    rng = np.random.default_rng(SEED)
    labels = {"total_check": ("Total homes (headline, recomputed)", "permits per 1,000 existing homes a year"),
              "apt_per_existing_apt": ("FU5a homes in 5+ unit buildings per 1,000 existing 5+ unit homes", "per 1,000 existing homes in 5+ unit buildings a year"),
              "apt_per_all_homes": ("FU5b homes in 5+ unit buildings per 1,000 existing homes", "permits per 1,000 existing homes a year"),
              "single_family": ("FU6 near-placebo: single-family homes per 1,000 existing homes", "permits per 1,000 existing homes a year")}
    out = []
    for col, (lab, unit) in labels.items():
        d = P.dropna(subset=[col])
        v = d[col].values
        for wl, w in (("home-weighted", d["weight"].values), ("equal-weight", np.ones(len(d)))):
            f = lambda i: np.sum(v[i] * w[i]) / np.sum(w[i])  # noqa: E731
            bs = np.array([f(rng.integers(0, len(v), len(v))) for _ in range(DRAWS)])
            lo, hi = np.percentile(bs, [5, 95])
            out.append(dict(test=lab, weighting=wl, places=len(d), estimate=f(np.arange(len(v))), p05=lo, p95=hi, unit=unit,
                            reading="above 0" if lo > 0 else ("below 0" if hi < 0 else "interval includes 0")))
    S = pd.DataFrame(out)
    S.to_csv(REFERENCE / "parking_causal_fu56_summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.drop(columns="unit").round(3).to_string(index=False))


if __name__ == "__main__":
    main()
