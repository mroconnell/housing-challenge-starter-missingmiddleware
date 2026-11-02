"""T5: Massachusetts MBTA Communities, feasibility count and year-1 event study (docs/tod/CAUSAL_FRAMEWORK_PLAN.md,
"Test 5 (T5)", locked before any count).

Inputs (local): BPS Northeast annual place files data/raw/tod_control_cities/bps/ne{2015..2025}a.txt (state 25 rows =
Massachusetts towns); ACS 2015-2019 housing units by county subdivision (data/raw/parking_acs_history/
acs5_2019_cousub25.json); EOHLC compliance status sheet of 2025-09-18 (data/raw/tod_mbta/).

    .venv/bin/python scripts/run_tod_causal_mbta.py

Writes reference/tod_causal_mbta_event.csv (town counts and estimates; no raw rows).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

BPS = RAW / "tod_control_cities" / "bps"
SEED, DRAWS = 20261105, 2000
YEARS = range(2015, 2026)


def bps() -> pd.DataFrame:
    rows = []
    for y in YEARS:
        D = pd.read_csv(BPS / f"ne{y}a.txt", header=None, skiprows=3, dtype=str)
        D = D[D[1].str.strip() == "25"]
        num = lambda c: pd.to_numeric(D[c], errors="coerce").fillna(0)  # noqa: E731
        rows.append(pd.DataFrame({"year": y, "county": D[3].str.strip(), "mcd": D[6].str.strip(), "name": D[16].str.strip(),
                                  "months": num(15), "units": num(18) + num(21) + num(24) + num(27), "units5": num(27),
                                  "units_rep": num(30) + num(33) + num(36) + num(39), "units5_rep": num(39)}))
    return pd.concat(rows, ignore_index=True)


def norm(s: str) -> str:
    s = re.sub(r"\s+(town|city|Town city|city|Town)$", "", str(s).strip(), flags=re.I)
    return re.sub(r"\s+(town|city)$", "", s, flags=re.I).strip().lower()


def main() -> None:
    B = bps()
    B["key"] = B.name.map(norm)
    A = json.load(open(RAW / "parking_acs_history" / "acs5_2019_cousub25.json"))
    A = pd.DataFrame(A[1:], columns=A[0])
    A = pd.DataFrame({"county": A["county"], "mcd": A["county subdivision"], "homes": pd.to_numeric(A.B25001_001E)})
    S = pd.read_csv(RAW / "tod_mbta" / "compliance_status_2025-09-18.csv")
    S.columns = [c.strip() for c in S.columns]
    S = S.apply(lambda c: c.astype(str).str.strip())
    S["key"] = S.Municipality.str.lower().replace({"manchester": "manchester-by-the-sea"})
    dl = S["Compliance Deadlines"]
    S["original_deadline_kept"] = dl.isin(["12/31/2023", "12/31/2024"])
    S["cohort"] = np.where(dl == "12/31/2023", 2023, np.where(dl == "12/31/2025", 2025, 2024))
    S.loc[S.key == "milton", "cohort"] = 2023
    S["compliant"] = S["Compliance Status"].isin(["Compliant", "Conditional Compliance"])
    towns = B[B.year == 2025][["key", "county", "mcd"]].drop_duplicates("key")
    S = S.merge(towns, on="key", how="left")
    unmatched = S[S.mcd.isna()].Municipality.tolist()
    S = S.dropna(subset=["mcd"]).merge(A, on=["county", "mcd"], how="left")
    P = B.merge(S[["key", "cohort", "compliant", "homes"]], on="key")
    P = P[P.homes > 0]
    feas = int((S.compliant & S.cohort.isin([2023, 2024])).sum())
    feas_strict = int((S.compliant & S.original_deadline_kept).sum())
    out = [{"row": "feasibility", "name": "compliant or conditional towns with deadline <= 12/31/2024 (ITT cohorts incl. late)", "value": feas},
           {"row": "feasibility", "name": "same, original deadline kept (not 7/14/2025)", "value": feas_strict},
           {"row": "feasibility", "name": "communities on the sheet / matched to BPS", "value": len(S), "note": "unmatched: " + "; ".join(unmatched)},
           {"row": "feasibility", "name": "PASS (>=20)", "value": float(feas_strict >= 20)}]
    for c in (2023, 2024, 2025):
        out.append({"row": "cohort", "name": f"cohort {c}", "value": int((S.cohort == c).sum()), "note": f"compliant {int((S.compliant & (S.cohort == c)).sum())}"})
    rng = np.random.default_rng(SEED)

    def att(Pv: pd.DataFrame, ycol: str, g: int, ctrl: list[int], year1: int, base: range, weight: bool):
        w = Pv.pivot_table(index="key", columns="year", values=ycol)
        info = Pv.drop_duplicates("key").set_index("key")[["cohort", "homes"]]
        chg = w[year1] - w[list(base)].mean(axis=1)
        T, C = chg[info.cohort == g].dropna(), chg[info.cohort.isin(ctrl)].dropna()
        wt, wc = (info.homes.reindex(T.index), info.homes.reindex(C.index)) if weight else (pd.Series(1.0, T.index), pd.Series(1.0, C.index))
        est = np.average(T, weights=wt) - np.average(C, weights=wc)
        bt = rng.integers(0, len(T), (DRAWS, len(T)))
        bc = rng.integers(0, len(C), (DRAWS, len(C)))
        d = (np.einsum("dn,dn->d", T.values[bt], wt.values[bt]) / wt.values[bt].sum(1)
             - np.einsum("dn,dn->d", C.values[bc], wc.values[bc]) / wc.values[bc].sum(1))
        return est, d, len(T), len(C)

    variants = {"main: all units per 1,000 homes": ("y", False, False, False),
                "5+ units per 1,000 homes": ("y5", False, False, False),
                "compliant-only treated": ("y", True, False, False),
                "reported-only columns, 0-month towns dropped": ("yrep", False, True, False),
                "homes-weighted": ("y", False, False, True)}
    P["y"] = 1000 * P.units / P.homes
    P["y5"] = 1000 * P.units5 / P.homes
    P["yrep"] = 1000 * P.units_rep / P.homes
    for vname, (ycol, comp_only, rep, weight) in variants.items():
        Pv = P.copy()
        if comp_only:
            Pv = Pv[~(Pv.cohort.isin([2023, 2024]) & ~Pv.compliant)]
        if rep:
            bad = Pv[(Pv.months == 0)].key.unique()
            Pv = Pv[~Pv.key.isin(bad)]
        for label, shift in (("year 1", 0), ("pre-trend placebo (one year early)", 1)):
            parts = []
            for g, ctrl in ((2023, [2024, 2025]), (2024, [2025])):
                y1 = g + 1 - shift
                base = range(g - 3 - shift, g - shift)
                e, d, nt, nc = att(Pv, ycol, g, ctrl, y1, base, weight)
                parts.append((e, d, nt))
                out.append({"row": "att", "variant": vname, "test": label, "name": f"cohort {g}, year {y1} vs {base.start}-{base.stop - 1}",
                            "value": e, "lo90": np.percentile(d, 5), "hi90": np.percentile(d, 95), "treated": nt, "controls": nc})
            n = np.array([p[2] for p in parts], float)
            e = sum(p[0] * k for p, k in zip(parts, n)) / n.sum()
            d = sum(p[1] * k for p, k in zip(parts, n)) / n.sum()
            lo, hi = np.percentile(d, [5, 95])
            out.append({"row": "att", "variant": vname, "test": label, "name": "pooled (cohort-size weighted)", "value": e, "lo90": lo, "hi90": hi,
                        "treated": int(n.sum()), "note": "positive" if lo > 0 else "negative" if hi < 0 else "no detectable year-1 change"})
    # descriptive: mean units per 1,000 homes by cohort and year
    M = P.groupby(["cohort", "year"]).y.mean().unstack("year").round(2)
    for c, r in M.iterrows():
        out.append({"row": "trend", "name": f"cohort {c} mean units per 1,000 homes", "note": "; ".join(f"{y}: {v}" for y, v in r.items())})
    O = pd.DataFrame(out)
    O.round(3).to_csv(REFERENCE / "tod_causal_mbta_event.csv", index=False)
    pd.set_option("display.width", 250, "display.max_colwidth", 200)
    print(O.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
