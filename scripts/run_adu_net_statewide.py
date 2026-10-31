"""ADU statewide net check (owner ask 2026-10-31: permits after reform minus no-reform baseline, statewide Wisconsin).

Recomputes the net from the engine outputs and checks the pieces agree: with-law minus baseline equals the addition;
places, counties and districts add to the state; no place is below zero; the held-out score. Reports the net and its
share of the shared all-housing baseline (122,619 central; 118,822 as published).

Run: uv run python scripts/run_adu_net_statewide.py   Output: reference/adu_net_statewide.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from missing_middleware.paths import PROCESSED, REFERENCE  # noqa: E402

ALL_HOMES = {"central": 122_619, "as published": 118_822}


def main():
    st = pd.read_csv(REFERENCE / "adu_model_statewide.csv").set_index("path")
    res = pd.read_parquet(PROCESSED / "model_run/results_long.parquet")
    res5 = res[res.year.between(1, 5)] if res.year.max() <= 10 else res[res.year.between(2027, 2031)]
    cty = pd.read_csv(REFERENCE / "adu_model_by_county.csv").groupby("path")[["baseline_units", "additional_units"]].sum()
    out, flags = [], []
    for lvl in ("assembly", "senate"):
        d = pd.read_csv(REFERENCE / f"adu_model_by_{lvl}_district.csv", dtype={"forecast_year": str})
        d = d[d.forecast_year.eq("2027-2031")].groupby("path")[["baseline_units", "additional_units"]].sum()   # 5-year rows
        for p in st.index:
            if abs(d.loc[p, "additional_units"] - st.loc[p, "additional_units"]) > 0.5:
                flags.append(f"{lvl} districts do not add to the state ({p})")
    for p in st.index:
        g = res5[res5.path.eq(p)]
        add, base = float(st.loc[p, "additional_units"]), float(st.loc[p, "baseline_units"])
        if abs(g.additional_units.sum() - add) > 0.5 or abs(g.baseline_units.sum() - base) > 0.5:
            flags.append(f"places do not add to the state ({p})")
        if abs(cty.loc[p, "additional_units"] - add) > 0.5:
            flags.append(f"counties do not add to the state ({p})")
        if (g.additional_units < -1e-9).any():
            flags.append(f"a place has a negative addition ({p})")
        out.append(dict(path=p, baseline_no_reform=base, with_law=base + add, net_added=add,
                        net_share_of_all_homes_central=add / ALL_HOMES["central"],
                        net_share_of_all_homes_as_published=add / ALL_HOMES["as published"]))
    # outliers: places whose 5-year addition per 1,000 single-family homes per year is far above the rest
    areas = pd.read_parquet(PROCESSED / "model_baseline/engine_areas.parquet")[["area_id", "homes", "x_basis"]]
    c = res5[res5.path.eq("central")].groupby("area_id")[["baseline_units", "additional_units"]].sum().join(
        areas.set_index("area_id"))
    c = c[c.homes > 0]
    c["add_rate"] = c.additional_units / c.homes / 5 * 1000
    c["base_rate"] = c.baseline_units / c.homes / 5 * 1000
    q = c.add_rate.quantile([0.5, 0.99])
    top = c.sort_values("add_rate").tail(5)
    names = pd.read_parquet(PROCESSED / "foundation/areas.parquet").set_index("area_id")["name"]
    top.assign(name=top.index.map(names)).round(3).to_csv(REFERENCE / "adu_net_statewide_top_places.csv")
    print("addition per 1,000 homes per year: median", round(q[0.5], 3), "99th pct", round(q[0.99], 3))
    print(top.assign(name=top.index.map(names))[["name", "homes", "add_rate", "base_rate", "x_basis"]].round(3).to_string())
    g3 = pd.read_csv(REFERENCE / "pooled_revision_g3f2.csv")
    rms = float(g3[g3.option.eq("cap_a2") & g3.config.eq("A_ca_in_common_level")].rms_log_error.iloc[0])
    t = pd.DataFrame(out).assign(held_out_rms_log_error=rms, flags="; ".join(flags) or "none")
    t.round(4).to_csv(REFERENCE / "adu_net_statewide.csv", index=False)
    print(t.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
