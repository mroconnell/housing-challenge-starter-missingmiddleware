"""Parking natural experiment N2: Minneapolis step 2, first stage (car spaces per home), outside minus inside the
2015 covered areas, 2021 repeal. docs/parking/CAUSAL_FRAMEWORK_PLAN.md ("Natural experiments N1-N4", locked).

    uv run python scripts/run_parking_ne_n2.py
Output: reference/parking_ne_n2.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_parking_causal_f1 as f1  # noqa: E402
from missing_middleware.paths import PROCESSED, REFERENCE  # noqa: E402

SEED, DRAWS, MIN_SIDE = 20261104, 2000, 20


def did(cells, rng, z):
    r = f1.ratio
    ob, oa, ib, ia = cells
    est = (r(oa) - r(ob)) - (r(ia) - r(ib))
    bs = []
    for _ in range(DRAWS):
        s = [x.iloc[rng.integers(0, len(x), len(x))] for x in cells]
        bs.append((r(s[1]) - r(s[0])) - (r(s[3]) - r(s[2])))
    bs = np.array(bs)
    return dict(outside_before=r(ob), outside_after=r(oa), inside_before=r(ib), inside_after=r(ia),
                n_outside_before=len(ob), n_outside_after=len(oa), n_inside_before=len(ib), n_inside_after=len(ia),
                difference=est, p05=np.percentile(bs, 5), p95=np.percentile(bs, 95),
                p0125=np.percentile(bs, 1.25), p9875=np.percentile(bs, 98.75), mde=1.645 * bs.std(ddof=1))


def main() -> None:
    d = f1.read_xlsx_year_sheets(f1.XLSX)
    t = pd.read_csv(PROCESSED / "parking_first_stage" / "mpls_f1b_zone_tags.csv")[["sheet", "row", "zone"]]
    d = d.merge(t, on=["sheet", "row"], how="left").dropna(subset=["homes", "car"])
    d = d[(d["homes"] >= 5) & (d["later_action"] == "") & (d["downtown"] != "Y") & d["zone"].isin(["covered", "outside", "ua"])]
    out_ = lambda x: x[x["zone"].isin(["outside", "ua"])]  # noqa: E731
    in_ = lambda x: x[x["zone"] == "covered"]  # noqa: E731
    rng = np.random.default_rng(SEED)
    rows = []
    b = d[(d["date"] >= pd.Timestamp("2016-01-01")) & (d["date"] < f1.CUT_2021)]
    a = d[d["date"] >= f1.CUT_2021]
    cells = (out_(b), out_(a), in_(b), in_(a))
    feas = min(len(c) for c in cells) >= MIN_SIDE
    main_row = dict(case="N2 main: outside minus inside, 2016-2021-05 vs 2021-05 on", feasible=feas, **did(cells, rng, None)) if feas else \
        dict(case="N2 main", feasible=False, n_cells=str([len(c) for c in cells]))
    rows.append(main_row)
    pb, pa = d[d["date"] < pd.Timestamp("2014-01-01")], d[(d["date"] >= pd.Timestamp("2014-01-01")) & (d["date"] < f1.CUT_2015)]
    pcells = (out_(pb), out_(pa), in_(pb), in_(pa))
    if min(len(c) for c in pcells) >= 5:
        rows.append(dict(case="balance: same contrast 2011-2013 vs 2014-2015-07 (coarse)", feasible=min(len(c) for c in pcells) >= MIN_SIDE,
                         **did(pcells, rng, None)))
    else:
        rows.append(dict(case="balance", feasible=False, n_cells=str([len(c) for c in pcells])))
    S = pd.DataFrame(rows)
    S["unit"] = "car spaces per home (5+ home projects, downtown dropped)"
    S["prediction"] = "negative"
    S.to_csv(REFERENCE / "parking_ne_n2.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.round(3).T.to_string())


if __name__ == "__main__":
    main()
