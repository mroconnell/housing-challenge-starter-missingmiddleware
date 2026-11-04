"""Correction-lock sensitivity (item 2, labelled, not the main): candidates missing any trait the target has are
ineligible. Corrected data, picked heat method (D), every weighting. Output: reference/parking_method2_corrected_complete_traits.csv

    uv run --all-extras python scripts/check_parking_method2_complete_traits.py
"""
from __future__ import annotations

import concurrent.futures as cf
import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_parking_method2 as m  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402


def _one(c):
    return m.case_effect(m._G["D"], c, m._G["pick"], {**m.OPT_MAIN, "complete": True})["effect"]


def main() -> None:
    m.SUF, m.CORRECTED = "_corrected", True
    pick = str(pd.read_csv(REFERENCE / "parking_method2_corrected_pick.csv")["candidate"].iloc[0])
    D = m.Data()
    real, cases = m.real_cases()
    m._G = dict(D=D, pick=pick)
    with cf.ProcessPoolExecutor(m.WORKERS, mp_context=mp.get_context("fork")) as ex:
        y = np.array(list(ex.map(_one, cases)))
    ev = pd.DataFrame({"v": m.placebo_v(len(real)), "homes": real["homes"].values, "n_post": real["n_post"].values,
                       "band": m.band_of(real["population"].fillna(0)), "metro": [D.metro.get(c["key"], 0.0) for c in cases]})
    ev["base"] = ev["homes"] * ev["n_post"]
    ok = np.isfinite(y)
    wi = m.target_cells(D, "55")
    out = []
    for kind in m.WEIGHTS:
        a = m.weighted_avg(kind, y[ok], ev[ok].reset_index(drop=True), wi)
        lo, hi = m.boot_range(kind, y[ok], ev[ok].reset_index(drop=True), wi, m.BOOT, m.SEED)
        out.append(dict(variant=f"sensitivity: missing-trait candidates ineligible, {pick}", weights=kind, places=int(ok.sum()),
                        average=a, p05=lo, p95=hi, wi_homes=a * m.WI_K, wi_p05=lo * m.WI_K, wi_p95=hi * m.WI_K))
    pd.DataFrame(out).round(4).to_csv(REFERENCE / "parking_method2_corrected_complete_traits.csv", index=False)
    print(pd.DataFrame(out).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
