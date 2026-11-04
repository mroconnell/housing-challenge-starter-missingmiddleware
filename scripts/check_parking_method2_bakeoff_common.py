"""Method 2 bake-off check (audit, 2026-11-04): count non-finite fake effects per candidate, then rescore all four
candidates on the fake cases that are finite for every candidate. Rebuilds the same strata, sets and fake effects as
stage 1 (same seed). Outputs: reference/parking_method2_fake_effects.csv, parking_method2_bakeoff_common.csv

    uv run --all-extras python scripts/check_parking_method2_bakeoff_common.py
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
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402


def build_sets(D):
    """Same strata and draws as m.stage1."""
    real, cases = m.real_cases()
    v = m.placebo_v(len(real))
    rng = np.random.default_rng(m.SEED)
    strata = {}
    for c in cases:
        pre, post = cmp.windows(c["event_year"])
        post = post[: c["n_post"]]
        band = int(m.band_of([c["pop"] if np.isfinite(c["pop"]) else D.popn.get(c["key"], 0)])[0])
        sk = (c["event_year"], band, c["n_post"])
        if sk not in strata:
            ok = D.complete(tuple(pre + post))

            def pool_of(exc):
                return sorted(k for k in ok if k not in exc and k not in D.shock and k in D.homes.index
                              and int(m.band_of([D.popn.get(k, 0)])[0]) == band)
            s = pool_of(D.strict_exc)
            if len(s) < 5:
                s = [k for k in pool_of(D.main_exc) if k not in {x["key"] for x in cases}]
            strata[sk] = (s, pre, post)
    sets = []
    for _ in range(m.SETS):
        row = []
        for c in cases:
            band = int(m.band_of([c["pop"] if np.isfinite(c["pop"]) else D.popn.get(c["key"], 0)])[0])
            s, pre, post = strata[(c["event_year"], band, c["n_post"])]
            row.append((s[rng.integers(0, len(s))], c["event_year"], tuple(pre), tuple(post), c["i"]))
        sets.append(row)
    return sets, v


def main() -> None:
    D = m.Data()
    sets, v = build_sets(D)
    uniq = sorted({(k, ey, pre, post) for row in sets for (k, ey, pre, post, _) in row})
    print(len(uniq), "distinct fake cases", flush=True)
    m._G = dict(D=D)
    ctx = mp.get_context("fork")
    eff = {}
    with cf.ProcessPoolExecutor(m.WORKERS, mp_context=ctx) as ex:
        for part in ex.map(m._fake_effects, [uniq[i::m.WORKERS] for i in range(m.WORKERS)]):
            eff.update(part)
    rows = [dict(key=k, event_year=ey, pre=" ".join(map(str, pre)), post=" ".join(map(str, post)), candidate=c, effect=e)
            for (k, ey, pre, post, c), e in eff.items()]
    F = pd.DataFrame(rows)
    F.round(5).to_csv(REFERENCE / "parking_method2_fake_effects.csv", index=False)
    nan = F.assign(nan=~np.isfinite(F["effect"])).groupby("candidate")["nan"].sum()
    print("non-finite fake effects by candidate:", nan.to_dict(), flush=True)
    bad = {(k, ey, pre, post) for (k, ey, pre, post, c), e in eff.items() if not np.isfinite(e)}
    # common cases: drop any fake case that is non-finite for any candidate, for every candidate
    common = {key: (np.nan if key[:4] in bad else val) for key, val in eff.items()}
    m._G = dict(D=D, eff=common, sets=sets, v=v, cells=m.target_cells(D, "55"))
    jobs = [(c, w) for c in m.CANDIDATES for w in m.WEIGHTS]
    with cf.ProcessPoolExecutor(m.WORKERS, mp_context=ctx) as ex:
        res = list(ex.map(m._score, jobs))
    R = pd.DataFrame(res)
    R["non_finite_cases_dropped"] = len(bad)
    R.round(4).to_csv(REFERENCE / "parking_method2_bakeoff_common.csv", index=False)
    print(R.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
