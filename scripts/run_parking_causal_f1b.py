"""Parking causal framework, test F1b: Minneapolis 2015 transit-area cut, projects inside vs outside the areas it
covered. docs/parking/CAUSAL_FRAMEWORK_PLAN.md (F1b, locked before counting; decisions logged before the first mean).

Inputs: the F1 project sheet (scripts/run_parking_causal_f1.py reader) and zone tags from
scripts/fetch_parking_mpls_zones.py (data/processed/parking_first_stage/mpls_f1b_zone_tags.csv).

    uv run python scripts/run_parking_causal_f1b.py
Output: reference/parking_causal_f1b_summary.csv
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

SEED, DRAWS = 20261103, 2000


def did(cells, rng):
    r = f1.ratio
    ib, ia, ob, oa = cells
    est = (r(ia) - r(ib)) - (r(oa) - r(ob))
    bs = []
    for _ in range(DRAWS):
        s = [x.iloc[rng.integers(0, len(x), len(x))] for x in cells]
        bs.append((r(s[1]) - r(s[0])) - (r(s[3]) - r(s[2])))
    p05, p95 = np.percentile(bs, [5, 95])
    return dict(inside_before=r(ib), inside_after=r(ia), outside_before=r(ob), outside_after=r(oa),
                n_inside_before=len(ib), n_inside_after=len(ia), n_outside_before=len(ob), n_outside_after=len(oa),
                difference=est, p05=p05, p95=p95, mde=1.645 * np.std(bs, ddof=1),
                reading="binding (fewer spaces per home)" if p95 < 0 else ("more spaces per home" if p05 > 0 else "interval includes 0"))


def main() -> None:
    d = f1.read_xlsx_year_sheets(f1.XLSX)
    t = pd.read_csv(PROCESSED / "parking_first_stage" / "mpls_f1b_zone_tags.csv")[["sheet", "row", "zone", "near_edge_33m"]]
    d = d.merge(t, on=["sheet", "row"], how="left")
    d = d.dropna(subset=["homes", "car"])
    d = d[(d["homes"] >= 5) & (d["later_action"] == "") & (d["downtown"] != "Y") & (d["zone"] != "downtown")]
    win = d[d["date"] < f1.CUT_2021]
    unmatched = int((win["zone"] == "unmatched").sum())
    win = win[win["zone"] != "unmatched"]
    rng = np.random.default_rng(SEED)

    def cells(x, cut=f1.CUT_2015):
        b, a = x[x["date"] < cut], x[x["date"] >= cut]
        ins = lambda y: y[y["zone"] == "covered"]  # noqa: E731
        out = lambda y: y[y["zone"].isin(["outside", "ua"])]  # noqa: E731
        return ins(b), ins(a), out(b), out(a)

    rows = [dict(case="main: outside includes University Area", **did(cells(win), rng)),
            dict(case="sensitivity: University Area projects dropped", **did(cells(win[win["zone"] != "ua"]), rng)),
            dict(case="locked plan date: split at 2015-05-01", **did(cells(win, pd.Timestamp("2015-05-01")), rng)),
            dict(case="sensitivity: projects within 33 m of a zone edge dropped", **did(cells(win[~win["near_edge_33m"].fillna(False).astype(bool)]), rng))]
    S = pd.DataFrame(rows)
    S["note"] = (f"5+ home projects outside downtown, 2011-01 to 2021-05-13, split 2015-07-18; {unmatched} unmatched addresses left out; "
                 "unit car spaces per home; DiD = (inside after - before) - (outside after - before)")
    S.to_csv(REFERENCE / "parking_causal_f1b_summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.drop(columns="note").round(3).to_string(index=False))


if __name__ == "__main__":
    main()
