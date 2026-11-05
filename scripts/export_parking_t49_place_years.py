"""Per-place, per-year export for test 49's chart (output only; same estimate as scripts/run_parking_t49_event_time.py).

    uv run --all-extras python scripts/export_parking_t49_place_years.py
Output: reference/parking_byyear_place_effects.csv (permits per 1,000 pre-event existing homes a year; South Bend's rates
are for its combined city + unincorporated county area, its effect is scaled to the city as in the main estimate).
Weights are each place's share within its set and after-year, under the target-state mix (Wisconsin), random effects and
equal weights, after the same per-year winsorising used for the averages.
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
import run_parking_t49_event_time as t  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402


def weights(kind, y, ev, cells):
    yy = m.winsor(y)
    if kind == "random effects":
        w, _ = m.dl_weights(yy, ev["v"].values)
    elif kind == "target-state mix":
        w, _ = m.mix_weights(ev, cells)
    else:
        w = np.ones(len(yy))
    return w / w.sum()


def main() -> None:
    m.SUF, m.CORRECTED = "_corrected", True
    D = m.Data()
    real, cases = m.real_cases()
    t.G.update(D=D, cases=cases)
    last_year = int(D.P.columns.max())
    n_after = {i: last_year - c["event_year"] for i, c in enumerate(cases)}
    jobs = [(i, 3, "balanced3") for i in range(len(cases)) if int(real.loc[i, "n_post"]) == 3]
    jobs += [(i, n_after[i], "long") for i in range(len(cases)) if n_after[i] >= 5]
    with cf.ProcessPoolExecutor(m.WORKERS, mp_context=mp.get_context("fork")) as ex:
        res = list(ex.map(t._run, [(i, k) for i, k, _ in jobs]))
    ev_all = pd.DataFrame({"v": m.placebo_v(len(real)), "homes": real["homes"].values, "n_post": 1,
                           "band": m.band_of(real["population"].fillna(0)), "metro": [D.metro.get(c["key"], 0.0) for c in cases]})
    ev_all["base"] = ev_all["homes"]
    cells = m.target_cells(D, "55")
    rows = []
    for (i, r), (_, k_max, set_) in zip(res, jobs):
        if r["effects"] is None:
            continue
        c, dt = cases[i], r["detail"]
        for k, e in sorted(r["effects"].items()):
            y = c["event_year"] + k
            rows.append(dict(place=c["place"], state=c["state"], event_year=c["event_year"], set=set_, after_year=k, calendar_year=y,
                             own_rate=dt["own"].get(y), comparison_rate=dt["comp"].get(y), own_before=dt["own_before"],
                             comparison_before=dt["comp_before"], effect_that_year=e, i=i))
    X = pd.DataFrame(rows)
    for kind, col in (("target-state mix", "weight_state_mix"), ("random effects", "weight_random_effects"), ("equal", "weight_equal")):
        X[col] = np.nan
        for (set_, k), g in X[X["after_year"] >= 0].groupby(["set", "after_year"]):
            ok = g["effect_that_year"].notna()
            if ok.sum() == 0:
                continue
            ev = ev_all.iloc[g.loc[ok, "i"].values].reset_index(drop=True)
            X.loc[g.index[ok], col] = weights(kind, g.loc[ok, "effect_that_year"].values, ev, cells)
    X = X.drop(columns="i")
    X.round(5).to_csv(REFERENCE / "parking_byyear_place_effects.csv", index=False)
    print(len(X), "rows;", X.groupby("set")["place"].nunique().to_dict())


if __name__ == "__main__":
    main()
