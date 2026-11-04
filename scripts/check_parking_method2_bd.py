"""Method 2 post hoc side check E = B + D (Ryan 2026-11-04 19:46 UTC, after the bake-off scores were seen): pace
matching (B) with the 10-year before window (D), pace measured over that same window. Scored on the same fake cases as
the common-case rescore of A-D (reference/parking_method2_fake_effects.csv, cases finite for every candidate), then
run on the 76 real repeals as a side line only, not the method 2 result.
Outputs: reference/parking_method2_bd_bakeoff.csv, parking_method2_bd_real.csv

    uv run --all-extras python scripts/check_parking_method2_bd.py
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


def _fake_e(chunk):
    D = m._G["D"]
    return {(k, ey, pre, post, "E"): m.case_effect(D, dict(key=k, event_year=ey, pre=pre, post=post, pop=D.popn.get(k, np.nan)), "E", m.OPT_MAIN)["effect"]
            for (k, ey, pre, post) in chunk}


def main() -> None:
    D = m.Data()
    sets, v = cc.build_sets(D)
    F = pd.read_csv(REFERENCE / "parking_method2_fake_effects.csv")
    tup = lambda s: tuple(int(x) for x in str(s).split())  # noqa: E731
    eff = {(r.key, int(r.event_year), tup(r.pre), tup(r.post), r.candidate): r.effect for r in F.itertuples()}
    uniq = sorted({(k, ey, pre, post) for row in sets for (k, ey, pre, post, _) in row})
    m._G = dict(D=D)
    ctx = mp.get_context("fork")
    with cf.ProcessPoolExecutor(m.WORKERS, mp_context=ctx) as ex:
        for part in ex.map(_fake_e, [uniq[i::m.WORKERS] for i in range(m.WORKERS)]):
            eff.update(part)
    cands = list(m.CANDIDATES) + ["E"]
    bad = {key[:4] for key, e in eff.items() if not np.isfinite(e)}
    print("non-finite E:", sum(1 for key, e in eff.items() if key[4] == "E" and not np.isfinite(e)), "| cases dropped:", len(bad), flush=True)
    common = {key: (np.nan if key[:4] in bad else val) for key, val in eff.items()}
    m._G = dict(D=D, eff=common, sets=sets, v=v, cells=m.target_cells(D, "55"))
    with cf.ProcessPoolExecutor(m.WORKERS, mp_context=ctx) as ex:
        res = list(ex.map(m._score, [(c, w) for c in cands for w in m.WEIGHTS]))
    R = pd.DataFrame(res).assign(cases_dropped=len(bad), label="post hoc (B+D added after the bake-off was seen)")
    R.round(4).to_csv(REFERENCE / "parking_method2_bd_bakeoff.csv", index=False)
    print(R.round(4).to_string(index=False), flush=True)
    # real repeals: side line only
    real, cases = m.real_cases()
    ev = pd.DataFrame({"v": m.placebo_v(len(real)), "homes": real["homes"].values, "n_post": real["n_post"].values,
                       "band": m.band_of(real["population"].fillna(0)), "metro": [D.metro.get(c["key"], 0.0) for c in cases]})
    ev["base"] = ev["homes"] * ev["n_post"]
    y = np.array([m.case_effect(D, c, "E", m.OPT_MAIN)["effect"] for c in cases])
    ok = np.isfinite(y)
    wi = m.target_cells(D, "55")
    out = []
    for kind in m.WEIGHTS:
        a = m.weighted_avg(kind, y[ok], ev[ok].reset_index(drop=True), wi)
        lo, hi = m.boot_range(kind, y[ok], ev[ok].reset_index(drop=True), wi, m.BOOT, m.SEED)
        out.append(dict(variant="side line: B + D (post hoc)", weights=kind, places=int(ok.sum()), average=a, p05=lo, p95=hi,
                        wi_homes=a * m.WI_K, wi_p05=lo * m.WI_K, wi_p95=hi * m.WI_K))
    pd.DataFrame(out).round(4).to_csv(REFERENCE / "parking_method2_bd_real.csv", index=False)
    print(pd.DataFrame(out).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
