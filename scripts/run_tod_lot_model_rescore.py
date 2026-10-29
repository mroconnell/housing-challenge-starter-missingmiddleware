"""Rescore lot-model runs with per-reform actual extra homes (docs/tod/LOT_MODEL_PLAN.md section 9, item 23).

    uv run --all-extras python scripts/run_tod_lot_model_rescore.py

Reads each rebuilt run's saved city guesses (reference/tod_lot_model_by_city_*_rebuilt*.csv) and writes
*_rescored.csv beside them, plus reference/tod_lot_model_rescored_summary.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import REFERENCE  # noqa: E402
import run_tod_lot_model as L  # noqa: E402


def per_reform_actuals(D: pd.DataFrame) -> pd.DataFrame:
    D = L.five_year_basis(L.dedupe_lots(D))   # item 32.6
    rows = []
    for (city, unit), d in D.groupby(["city", "unit"]):
        t = d[d.treated == 1]
        c = d[(d.treated == 0) & (d["comparison_eligible"] == 1)]
        ta, ca = (t.acres * t.w).sum(), (c.acres * c.w).sum()
        if ta == 0:
            continue
        thin = ca < 0.25 * ta   # item 25.4: too little own comparison land -> the city's eligible comparison land
        if thin:   # item 27: no adjustment rather than another reform's neighbours
            ca = 0.0
        ua, ub = (t.ua5 * t.w).sum(), (t.ub5 * t.w).sum()
        if ca > 0:
            ex = (ua - ta * (c.ua5 * c.w).sum() / ca) - (ub - ta * (c.ub5 * c.w).sum() / ca)
        else:
            ex = ua - ub
        rows.append({"city": city, "unit": unit, "upzoned_acres": ta, "comparison_acres": ca, "actual_extra": ex,
                     "comparison_from_city": bool(thin)})
    return pd.DataFrame(rows)


def rescore(by_city: Path, D: pd.DataFrame) -> pd.DataFrame:
    E = pd.read_csv(by_city)
    mcol = "method" if "method" in E else "model"
    R = per_reform_actuals(D)
    act = R.groupby("city")["actual_extra"].sum()
    acres = R.groupby("city")["upzoned_acres"].sum()
    folds = [c for c in act.index if c not in L.HOLD]
    E["actual_extra_homes"] = E["city"].map(act)
    E["baseline_extra"] = [act[[x for x in folds if x != c]].sum() / acres[[x for x in folds if x != c]].sum() * acres[c]
                           for c in E["city"]]
    E["error_baseline"] = (E["baseline_extra"] - E["actual_extra_homes"]).abs()
    E["error_model"] = (E["model_extra"] - E["actual_extra_homes"]).abs()
    out = []
    for kind, g in E.groupby(mcol, sort=False):
        f, h = g[g.role == "fold"], g[g.role == "holdout"].set_index("city")
        zero = f["actual_extra_homes"].abs().mean()
        better = {c: bool(h.loc[c, "error_model"] < h.loc[c, "error_baseline"]) for c in L.HOLD}
        out.append({"run": by_city.stem.replace("tod_lot_model_by_city_", ""), "method": kind,
                    "fold_mean_error_baseline": f["error_baseline"].mean(), "fold_mean_error_guess_zero": zero,
                    "fold_mean_error_model": f["error_model"].mean(),
                    "fold_cities_better": int((f["error_model"] < f["error_baseline"]).sum()),
                    **{f"{c.lower()}_better": v for c, v in better.items()},
                    "passes_old_rule": bool(f["error_model"].mean() < f["error_baseline"].mean() and all(better.values())),
                    "passes_new_rule": bool(f["error_model"].mean() < min(f["error_baseline"].mean(), zero) and sum(better.values()) >= 2)})
    E.round(3).to_csv(by_city.with_name(by_city.stem + "_rescored.csv"), index=False)
    return pd.DataFrame(out), R


def main() -> None:
    base = pd.read_parquet(L.OUT / "lots_rebuilt_halfmile.parquet")
    drop = base.drop(base.groupby("city")["units_after"].idxmax().values)
    S, Rs = [], None
    for f in sorted(REFERENCE.glob("tod_lot_model_by_city_*_rebuilt*.csv")):
        if f.stem.endswith("_rescored") or "_land" in f.stem or "_v32" not in f.stem:
            continue
        s, R = rescore(f, drop if "droplargest" in f.stem else base)
        S.append(s)
        if "droplargest" not in f.stem:
            Rs = R
    S = pd.concat(S, ignore_index=True)
    S.round(1).to_csv(REFERENCE / "tod_lot_model_rescored_summary.csv", index=False)
    Rs.round(1).to_csv(REFERENCE / "tod_lot_model_actual_by_reform.csv", index=False)
    pd.set_option("display.width", 250)
    print(Rs.groupby("city")[["upzoned_acres", "actual_extra"]].sum().round(0).to_string())
    print(S.round(0).to_string(index=False))


if __name__ == "__main__":
    main()
