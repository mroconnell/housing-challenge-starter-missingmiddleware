"""Method 2 bake-off, fair post hoc rescore (audit 2026-11-04): C uses B's effect wherever its synthetic control
cannot be built (C's own rule: B where synthetic control is not used); all four candidates scored on every fake case.
Reads reference/parking_method2_fake_effects.csv. Output: reference/parking_method2_bakeoff_fallback.csv

    uv run --all-extras python scripts/check_parking_method2_bakeoff_fallback.py
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
import check_parking_method2_bakeoff_common as cc  # noqa: E402
import run_parking_method2 as m  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402


def main() -> None:
    D = m.Data()
    sets, v = cc.build_sets(D)
    F = pd.read_csv(REFERENCE / "parking_method2_fake_effects.csv")
    tup = lambda s: tuple(int(x) for x in str(s).split())  # noqa: E731
    eff = {(r.key, int(r.event_year), tup(r.pre), tup(r.post), r.candidate): r.effect for r in F.itertuples()}
    filled = 0
    for key in [k for k in eff if k[4] == "C" and not np.isfinite(eff[k])]:
        eff[key] = eff[key[:4] + ("B",)]
        filled += 1
    print("C cases filled with B:", filled, flush=True)
    m._G = dict(D=D, eff=eff, sets=sets, v=v, cells=m.target_cells(D, "55"))
    with cf.ProcessPoolExecutor(m.WORKERS, mp_context=mp.get_context("fork")) as ex:
        res = list(ex.map(m._score, [(c, w) for c in m.CANDIDATES for w in m.WEIGHTS]))
    R = pd.DataFrame(res).assign(c_filled_with_b=filled, label="post hoc: C falls back to B where synthetic control fails")
    R.round(4).to_csv(REFERENCE / "parking_method2_bakeoff_fallback.csv", index=False)
    print(R.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
