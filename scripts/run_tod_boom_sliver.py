"""Boom-and-bust placebo cities, and a sliver-sized Wisconsin law (docs/tod/BOOM_SLIVER_PLAN.md).

    uv run --all-extras python scripts/run_tod_boom_sliver.py

Writes reference/tod_boom_placebos.csv and reference/tod_sliver_law.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import control_cities as cc  # noqa: E402
from scripts.run_tod_conversion import BROAD  # noqa: E402

CITY_HOMES_2020 = {"Milwaukee": None, "Madison": None}


def boom() -> pd.DataFrame:
    bps = cc.read_bps(RAW / "tod_control_cities" / "bps")
    gaz = cc.read_gazetteer(RAW / "tod_control_cities" / "Gaz_places_national.zip")
    panel, places = cc.link(bps, gaz, cc.read_county_hu(RAW / "tod_control_cities" / "Gaz_counties_national.zip"))
    inv = cc.inventory_geoids(pd.read_csv(REFERENCE / "tod_cases.csv"), gaz)
    Rt = cc.rates(panel, places)
    cc.REFORMS = [b[0] for b in BROAD]
    P = places.set_index("geoid")
    rows = []
    for rf, _ in BROAD:
        if rf.year < 2015:
            continue
        b, a = cc.years(rf.before), cc.years(rf.after)
        ok = Rt.reindex(columns=b + a).notna().all(axis=1)
        base = cc.eligible(rf, Rt, places, inv)
        t_before = Rt.loc[rf.geoid, b].mean()
        lo, hi = 0.75, 1.25
        hu = P.loc[rf.geoid, "hu10"]
        sel = []
        while len(sel) < 10 and lo > 0.05:
            cand = [g for g in base.index if ok.get(g, False)]
            sel = [g for g in cand if lo * t_before <= Rt.loc[g, b].mean() <= hi * t_before]
            lo, hi = lo * 0.9, hi * 1.1
        ch = (Rt.loc[sel, a].mean(axis=1) - Rt.loc[sel, b].mean(axis=1))
        tch = Rt.loc[rf.geoid, a].mean() - t_before
        eff = tch - ch.median()
        rows.append({"city": rf.city, "reform_year": rf.year, "boom_cities": len(sel),
                     "boom_city_examples": "; ".join(P.loc[sel, "place_name"].head(8)),
                     "reform_city_before_rate": t_before, "reform_city_change": tch, "boom_cities_median_change": ch.median(),
                     "effect_5yr_pct": cc.to_5yr_share(eff), "low_5yr_pct": cc.to_5yr_share(tch - ch.quantile(0.95)),
                     "high_5yr_pct": cc.to_5yr_share(tch - ch.quantile(0.05)),
                     "share_of_boom_cities_falling_as_much": float((ch <= tch).mean())})
    return pd.DataFrame(rows)


def sliver() -> pd.DataFrame:
    p = pd.read_csv(REFERENCE / "tod_conversion_points.csv")
    s = p[(p["coverage_homes"] < 0.05) & ~p["case"].isin(["nyc_program_2005"]) & p["gain_5yr_pct"].notna()].copy()
    s["response"] = s["gain_5yr_pct"] / (s["coverage_homes"] * 100)   # % of city homes per 1 point of coverage
    m = pd.read_csv(REFERENCE / "tod_near_stop_homes_by_muni.csv")
    homes = {c: float(m.loc[m["name"] == f"{c} city", "homes_2020"].iloc[0]) for c in ("Milwaukee", "Madison")}
    sa = pd.read_csv(REFERENCE / "tod_station_areas.csv")
    rq = {c: float(sa[(sa["city"] == f"{c} city") & (sa["band"] == "rapid_quarter")]["existing_homes"].sum()) for c in homes}
    out = []
    for label, ss in (("all 14 sliver cities", s), ("without Milpitas and Bellevue", s[~s["city"].isin(["Milpitas", "Bellevue"])])):
        q25, q50, q75 = ss["response"].quantile([0.25, 0.5, 0.75])
        for cov in (0.03, 0.06):
            row = {"response_set": label, "cities": len(ss), "coverage_pct": cov * 100,
                   "response_p25": q25, "response_median": q50, "response_p75": q75}
            for c, h in homes.items():
                for k, q in (("little", q25), ("typical", q50), ("strong", q75)):
                    row[f"{c.lower()}_{k}"] = q * cov * 100 / 100 * h
            for k in ("little", "typical", "strong"):
                row[f"both_{k}"] = row[f"milwaukee_{k}"] + row[f"madison_{k}"]
            out.append(row)
    o = pd.DataFrame(out)
    o.attrs["coverage_rapid_quarter"] = {c: rq[c] / homes[c] for c in homes}
    o.attrs["homes"] = homes
    mad = s[s["city"] == "Madison"]["response"].iloc[0]
    o.attrs["madison_own_vs_others"] = (mad, s[s["city"] != "Madison"]["response"].median())
    o.attrs["ratios"] = s[["city", "coverage_homes", "gain_5yr_pct", "response"]]
    return o


def main() -> None:
    B = boom()
    B.round(4).to_csv(REFERENCE / "tod_boom_placebos.csv", index=False)
    S = sliver()
    S.round(2).to_csv(REFERENCE / "tod_sliver_law.csv", index=False)
    pd.set_option("display.width", 250)
    print(B.round(2).T.to_string())
    print(S.attrs["ratios"].round(3).to_string())
    print("rail and rapid 1/4 mile coverage:", {k: round(v, 3) for k, v in S.attrs["coverage_rapid_quarter"].items()}, S.attrs["homes"])
    print("Madison own response vs median of others:", S.attrs["madison_own_vs_others"])
    print(S.round(0).T.to_string())


if __name__ == "__main__":
    main()
