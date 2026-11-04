"""Method 2 follow-up checks (audit 2026-11-04, after the results):
(a) Wisconsin cells on the tool's 2,668,677 eligible homes (reference/parking_model_by_area.csv: population band x
    metro, metro = county's CBSA is a metropolitan statistical area, LSAD M1), as the lock specified, instead of the
    BPS-unit cells the run used; recompute the D, target-state-mix result. (b) 90% bootstrap range for each size-band
    mean. (c) the trait missing for San Francisco's step-5 pool.
Output: reference/parking_method2_wi_cells_check.csv

    uv run --all-extras python scripts/check_parking_method2_wi_cells.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_parking_comparison as rpc  # noqa: E402
import run_parking_method2 as m  # noqa: E402
from missing_middleware.dbf import read_shapefile_attributes  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402


def tool_cells() -> pd.Series:
    a = pd.read_csv(REFERENCE / "parking_model_by_area.csv", dtype={"county_id": str})
    bps = rpc.read_bps_us()
    w = bps[bps["state_fips"].astype(str).str.strip() == "55"].copy()
    w["county"] = "55" + w["county_fips"].astype(str).str.strip().str.zfill(3)
    cb = w.groupby("county")["cbsa"].agg(lambda s: s.astype(str).str.strip().mode().iloc[0])
    lsad = read_shapefile_attributes(RAW / "census_cbsa_cb_2024" / "cb_2024_us_cbsa_20m.zip").set_index("CBSAFP")["LSAD"]
    a["metro"] = a["county_id"].map(cb).map(lsad).eq("M1").astype(float)
    a["band"] = m.band_of(pd.to_numeric(a["population"]).fillna(0))
    return a.groupby(["metro", "band"])["eligible_homes"].sum()


def main() -> None:
    d = pd.read_csv(REFERENCE / "parking_method2_places.csv")
    d = d[d["variant"] == "method 2, D"].reset_index(drop=True)
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].dropna(subset=["effect"]).reset_index(drop=True)
    D = m.Data()
    _, cases = m.real_cases()
    ev = pd.DataFrame({"v": m.placebo_v(len(real)), "homes": real["homes"].values, "n_post": real["n_post"].values,
                       "band": m.band_of(real["population"].fillna(0)), "metro": [D.metro.get(c["key"], 0.0) for c in cases]})
    ev["base"] = ev["homes"] * ev["n_post"]
    y = d["effect"].values
    rows = []
    for lab, cells in (("BPS-unit cells (as run)", m.target_cells(D, "55")), ("tool-area cells (2,668,677)", tool_cells())):
        a = m.weighted_avg("target-state mix", y, ev, cells)
        lo, hi = m.boot_range("target-state mix", y, ev, cells, m.BOOT, m.SEED)
        w, empty = m.mix_weights(ev, cells)
        shares = (cells / cells.sum()).round(3).to_dict()
        rows.append(dict(check=f"D, target-state mix, {lab}", value=a, p05=lo, p95=hi, wi_homes=a * m.WI_K, wi_p05=lo * m.WI_K,
                         wi_p95=hi * m.WI_K, eligible_homes=float(cells.sum()), effective_places=float(w.sum() ** 2 / (w ** 2).sum()),
                         note="cell shares " + str(shares)))
    yw = m.winsor(y)
    rng = np.random.default_rng(m.SEED)
    for b in range(4):
        idx = np.where(ev["band"].values == b)[0]
        boots = [yw[rng.choice(idx, len(idx))].mean() for _ in range(m.BOOT)]
        rows.append(dict(check=f"size band {b} mean (winsorised, equal weight)", value=float(yw[idx].mean()),
                         p05=float(np.percentile(boots, 5)), p95=float(np.percentile(boots, 95)), note=f"{len(idx)} places"))
    sf = next(c for c in cases if c["place"] == "San Francisco")
    h = D.homes_pre(sf["event_year"])
    pl = m.long_pre(sf["event_year"], sf["pre"], False)
    s = m.select_pool(D, sf["key"], sf["event_year"], pl, sf["post"], "A", m.OPT_MAIN)
    T = m.traits(D, s["pool"] + [sf["key"]], pl, sf["event_year"], h, False, True)
    miss = T.loc[s["pool"]].isna().mean()
    rows.append(dict(check="San Francisco step-5 pool: share missing by trait", note=str(miss.round(2).to_dict()) +
                     f"; target missing: {T.loc[sf['key']].isna().to_dict()}"))
    out = pd.DataFrame(rows)
    out.round(4).to_csv(REFERENCE / "parking_method2_wi_cells_check.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.round(3).to_string())


if __name__ == "__main__":
    main()
