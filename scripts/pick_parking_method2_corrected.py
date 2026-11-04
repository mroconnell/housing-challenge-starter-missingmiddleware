"""Corrected method-2 heat pick under the correction lock's rule: D or B+D (candidate E), B+D only if its MAE is >5%
lower than D's with coverage 85-95%; D wins ties; C out. Same fake sets and seed as the corrected stage 1, random-effects
scoring. Overwrites reference/parking_method2_corrected_pick.csv (stage 1's own lowest-MAE row is kept as a note).

    uv run --all-extras python scripts/pick_parking_method2_corrected.py
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


def _fx(chunk):
    D = m._G["D"]
    out = {}
    for (k, ey, pre, post) in chunk:
        case = dict(key=k, event_year=ey, pre=pre, post=post, pop=D.popn.get(k, np.nan))
        for c in ("D", "E"):
            out[(k, ey, pre, post, c)] = m.case_effect(D, case, c, m.OPT_MAIN)["effect"]
    return out


def main() -> None:
    m.SUF, m.CORRECTED = "_corrected", True
    stage1 = pd.read_csv(REFERENCE / "parking_method2_corrected_pick.csv").iloc[0].to_dict()
    D = m.Data()
    sets, v = cc.build_sets(D)
    uniq = sorted({(k, ey, pre, post) for row in sets for (k, ey, pre, post, _) in row})
    m._G = dict(D=D)
    ctx = mp.get_context("fork")
    eff = {}
    with cf.ProcessPoolExecutor(m.WORKERS, mp_context=ctx) as ex:
        for part in ex.map(_fx, [uniq[i::m.WORKERS] for i in range(m.WORKERS)]):
            eff.update(part)
    m._G = dict(D=D, eff=eff, sets=sets, v=v, cells=m.target_cells(D, "55"))
    with cf.ProcessPoolExecutor(2, mp_context=ctx) as ex:
        res = {r["candidate"]: r for r in ex.map(m._score, [("D", "random effects"), ("E", "random effects")])}
    d, e = res["D"], res["E"]
    use_e = e["mae"] < 0.95 * d["mae"] and 0.85 <= e["coverage"] <= 0.95
    pick = "E" if use_e else "D"
    rule = "B+D: MAE >5% below D with coverage 85-95%" if use_e else "D (B+D not >5% better with coverage 85-95%; D wins ties)"
    pd.DataFrame([dict(candidate=pick, rule=rule, mae=res[pick]["mae"], coverage=res[pick]["coverage"],
                       d_mae=d["mae"], d_coverage=d["coverage"], e_mae=e["mae"], e_coverage=e["coverage"],
                       stage1_lowest_mae_any=f"{stage1['candidate']} ({stage1['mae']:.4f}, {stage1['coverage']:.3f}); not the corrected rule")]) \
        .to_csv(REFERENCE / "parking_method2_corrected_pick.csv", index=False)
    print(d, e, "PICK", pick, rule, sep="\n")


if __name__ == "__main__":
    main()
