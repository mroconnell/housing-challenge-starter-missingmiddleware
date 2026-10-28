"""Part B of docs/tod/CENSUS_PREDICT_PLAN.md: New York's downzoned lots near stations, the mirror test.

    uv run --all-extras python scripts/run_tod_nyc_downzoning.py

Rebuilds each pooled New York rezoning with the case adapter (missing_middleware/tod/case_nyc.py) and keeps the lots
inside the rezoning whose allowed residential floor area fell, within 1/2 mile of a rail or subway stop. Writes
reference/tod_nyc_downzoning.csv (aggregates only).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import cases as C  # noqa: E402
from scripts import run_tod_census_cases as R  # noqa: E402
from scripts.run_tod_net_effect import _permits_from_points, capture  # noqa: E402

SEED = 20261033
BEFORE, AFTER = list(range(-6, 0)), list(range(1, 6))


def rail_stops(crs):
    s = pd.DataFrame(json.load(open(RAW / "tod_census_cases" / "ntm_rail_stops.json"))).dropna(subset=["stop_lat", "stop_lon"])
    g = gpd.GeoDataFrame(geometry=gpd.points_from_xy(s.stop_lon, s.stop_lat), crs=4326).to_crs(crs)
    return g.geometry.union_all()


def main() -> None:
    from missing_middleware.tod import case_nyc as N
    rng = np.random.default_rng(SEED)
    frames, members, cen = [], [], []
    stops = None
    for ulurp, (name, boro) in N.POOLED.items():
        with capture(nyc=N) as cap:
            try:
                m = N.build_member(ulurp, boro)
            except Exception as e:  # noqa: BLE001
                print(f"  {name}: {type(e).__name__}: {e}")
                continue
        args, area = cap["uniform"][-1]
        L = args["parcels"]
        if stops is None:
            stops = rail_stops(L.crs)
        eff = int(m["effective_year"])
        elig = args["eligible"].astype(bool)
        lb, la = args["level_before"].astype(float), args["level_after"].astype(float)
        near = L.geometry.representative_point().distance(stops) <= C.HALF_MILE_M
        down = args["in_reform"].astype(bool) & (la < lb - 1e-9) & elig & near & ~args["changed_outside"].astype(bool)
        up = area == C.TREAT
        comp = area == C.COMP
        acres = L.geometry.area / C.SQM_PER_ACRE
        lab = pd.Series(None, index=L.index, dtype=object)
        lab[comp] = "comparison"
        lab[up] = "upzoned"
        lab[down] = "downzoned"
        jg, ix = cap["jobs"][-1]
        q = _permits_from_points(jg, ix).dropna(subset=["pix"])
        q["area"] = lab.reindex(q["pix"].astype(int)).values
        q = q[q["area"].notna()].copy()
        q["year"] = q["year"].astype(int) - eff
        q["project"] = f"{ulurp}:" + q["project"].astype(str)
        frames.append(q[["project", "area", "year", "units"]])
        dose = float(((la - lb)[down] * acres[down]).sum() / acres[down].sum()) if down.any() else np.nan
        updose = float(((la - lb)[up] * acres[up]).sum() / acres[up].sum()) if up.any() else np.nan
        members.append({"rezoning": ulurp, "name": name, "adopted": eff, "downzoned_acres": float(acres[down].sum()),
                        "upzoned_acres": float(acres[up].sum()), "comparison_acres": float(acres[comp].sum()),
                        "downzoned_far_change": dose, "upzoned_far_change": updose})
        if 2008 <= eff <= 2013 and down.any() and comp.any():
            dg = L.loc[down].to_crs(R.CRS).geometry.make_valid().union_all()
            cg = L.loc[comp].to_crs(R.CRS).geometry.make_valid().union_all()
            p10, p20 = R.block_points("36", 2010), R.block_points("36", 2020)
            t10, t20, c10, c20 = p10[R.within(p10, dg)], p20[R.within(p20, dg)], p10[R.within(p10, cg)], p20[R.within(p20, cg)]
            est, lo, hi = R.diff_with_interval(t10, t20, c10, c20, rng)
            cen.append({"rezoning": ulurp, "adopted": eff, "census_downzoned_minus_comparison_per_acre_decade": est,
                        "low": lo, "high": hi, "downzoned_homes_2010": t10["homes"].sum(), "downzoned_homes_2020": t20["homes"].sum()})
        print(f"{name} ({eff}): down {acres[down].sum():.1f} ac, up {acres[up].sum():.1f} ac", flush=True)
    P = pd.concat(frames, ignore_index=True)
    M = pd.DataFrame(members)
    rows = []
    for side in ("downzoned", "upzoned"):
        d = P[P["area"].isin([side, "comparison"])].replace({"area": {side: C.TREAT, "comparison": C.COMP}})
        denom = {C.TREAT: float(M[f"{side}_acres"].sum()), C.COMP: float(M["comparison_acres"].sum())}
        est = C.did(d, denom, BEFORE, AFTER)
        lo, hi, _ = C.bootstrap_did(d, denom, BEFORE, AFTER, seed=SEED)
        dose = float((M[f"{side}_far_change"] * M[f"{side}_acres"]).sum() / M[f"{side}_acres"].sum())
        val = float(est["did"])
        rows.append({"side": side, "measure": "permits, stacked event years -6..-1 vs 1..5, per eligible acre per year",
                     "acres": denom[C.TREAT], "did_per_acre_year": val, "low": lo, "high": hi, "far_change": dose,
                     "per_far": val / abs(dose) if dose else np.nan})
    # Per rezoning, downzoned side only (owner question 2026-10-28: any missed construction?).
    per = []
    for r in M.itertuples():
        if r.downzoned_acres < 1:
            continue
        sub = P[P["project"].str.startswith(f"{r.rezoning}:") & P["area"].isin(["downzoned", "comparison"])]
        d = sub.replace({"area": {"downzoned": C.TREAT, "comparison": C.COMP}})
        denom = {C.TREAT: r.downzoned_acres, C.COMP: r.comparison_acres}
        e = C.did(d, denom, BEFORE, AFTER)
        lo_, hi_, _ = C.bootstrap_did(d, denom, BEFORE, AFTER, seed=SEED)
        b = d[(d["area"] == C.TREAT) & d["year"].isin(BEFORE)]["units"].sum()
        a = d[(d["area"] == C.TREAT) & d["year"].isin(AFTER)]["units"].sum()
        per.append({"rezoning": r.rezoning, "name": r.name, "adopted": r.adopted, "downzoned_acres": r.downzoned_acres,
                    "far_change": r.downzoned_far_change, "homes_permitted_6_years_before": b, "homes_permitted_5_years_after": a,
                    "did_per_acre_year": e["did"], "low": lo_, "high": hi_,
                    "implied_homes_per_year": e["did"] * r.downzoned_acres})
    pd.DataFrame(per).round(3).to_csv(REFERENCE / "tod_nyc_downzoning_by_rezoning.csv", index=False)
    print(pd.DataFrame(per).round(2).to_string())
    out = pd.DataFrame(rows)
    out.round(4).to_csv(REFERENCE / "tod_nyc_downzoning.csv", index=False)
    M.round(3).to_csv(REFERENCE / "tod_nyc_downzoning_members.csv", index=False)
    pd.DataFrame(cen).round(4).to_csv(REFERENCE / "tod_nyc_downzoning_census.csv", index=False)
    pd.set_option("display.width", 250)
    print(M.round(2).to_string())
    print(out.round(3).to_string())
    print(pd.DataFrame(cen).round(2).to_string())


if __name__ == "__main__":
    main()
