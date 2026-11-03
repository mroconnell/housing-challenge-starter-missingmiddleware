"""Parking natural experiment N1: Oregon's CFEC parking rules (OAR 660-012), intent-to-treat over every city in the 8
covered metro areas (Portland dropped), against Washington (main) and Idaho (second) places at 1/2-2x population.
docs/parking/CAUSAL_FRAMEWORK_PLAN.md ("Natural experiments N1-N4", locked 2026-11-03).

Covered-city list: cities in the 8 metropolitan planning areas named in DLCD's "Where Parking Reforms Apply"
(Portland Metro, Salem-Keizer, Eugene-Springfield, Albany, Bend, Corvallis, Grants Pass, Medford-Ashland / Rogue Valley),
as members of each area's MPO. DLCD counts 48 cities; the list below has 45 (Portland dropped), flagged.

    uv run python scripts/run_parking_ne_n1.py
Outputs: reference/parking_ne_n1_places.csv, reference/parking_ne_n1.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_parking_comparison as rpc  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

SEED, DRAWS, EVENT = 20261104, 2000, 2023
METROS = {
    "Portland Metro": ["Beaverton", "Cornelius", "Durham", "Fairview", "Forest Grove", "Gladstone", "Gresham", "Happy Valley",
                       "Hillsboro", "Johnson City", "King City", "Lake Oswego", "Maywood Park", "Milwaukie", "Oregon City",
                       "Rivergrove", "Sherwood", "Tigard", "Troutdale", "Tualatin", "West Linn", "Wilsonville", "Wood Village"],
    "Salem-Keizer": ["Salem", "Keizer", "Turner"], "Eugene-Springfield": ["Eugene", "Springfield", "Coburg"],
    "Albany": ["Albany", "Millersburg", "Tangent", "Jefferson"], "Bend": ["Bend"], "Corvallis": ["Corvallis", "Philomath", "Adair Village"],
    "Grants Pass": ["Grants Pass"], "Rogue Valley": ["Medford", "Ashland", "Central Point", "Phoenix", "Talent", "Jacksonville", "Eagle Point"],
}
ST = {"Oregon": "41", "Washington": "53", "Idaho": "16"}


def main() -> None:
    p = cmp.panel(rpc.read_bps_us())
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001"))
    homes = homes[homes > 0]
    popn = geo["acs_geoid"].map(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001"))
    pre, post = cmp.windows(EVENT)
    ok = cmp.complete(p, pre + post) & set(homes.index)
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    reformed = tax[tax["policy"].isin(["rm_min", "reduce_min"]) & tax["adopted_year"].between(2018, 2025) & tax["state"].isin(["Washington", "Idaho"])]
    drop = {k for r in reformed.drop_duplicates("prn_key").itertuples() if (k := cmp.match_place(p, ST[r.state], r.place, r.population))}
    treated = []
    for metro, cities in METROS.items():
        for c in cities:
            k = cmp.match_place(p, "41", c, None)
            treated.append(dict(metro=metro, city=c, key=k, usable=bool(k and k in ok)))
    T = pd.DataFrame(treated)
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].set_index("key")

    def rate(keys, yrs):
        return cmp._rate(p, keys, yrs, "units_total", homes)

    rows = []
    for r in T[T["usable"]].itertuples():
        pop0 = float(popn.get(r.key, np.nan))
        for comp, st in (("Washington", "53"), ("Idaho", "16")):
            cands = [k for k in ok if k.startswith(st + "|") and k not in drop and 0.5 * pop0 <= float(popn.get(k, np.nan)) <= 2 * pop0]
            if len(cands) < 1:
                continue
            eff = (rate([r.key], post) - rate([r.key], pre)) - (rate(cands, post) - rate(cands, pre))
            rows.append(dict(metro=r.metro, city=r.city, key=r.key, comparison=comp, n_controls=len(cands), homes=float(homes[r.key]),
                             effect=eff, in_76=r.key in real.index, effect_76=float(real["effect"].get(r.key, np.nan)) if r.key in real.index else np.nan))
    P = pd.DataFrame(rows)
    P.to_csv(REFERENCE / "parking_ne_n1_places.csv", index=False)
    rng = np.random.default_rng(SEED)
    out = []
    for comp in ("Washington", "Idaho"):
        d = P[(P["comparison"] == comp) & (P["n_controls"] >= 1)].reset_index(drop=True)
        v, w = d["effect"].values, (d["homes"] * len(post)).values
        f = lambda i: np.sum(v[i] * w[i]) / np.sum(w[i])  # noqa: E731
        bs = np.array([f(rng.integers(0, len(v), len(v))) for _ in range(DRAWS)])
        lo, hi, l2, h2 = np.percentile(bs, [5, 95, 1.25, 98.75])
        o = d[d["in_76"]]
        out.append(dict(test=f"N1 ITT vs {comp}", treated_places=len(d), estimate=f(np.arange(len(v))), p05=lo, p95=hi, p0125=l2, p9875=h2,
                        mde=1.645 * bs.std(ddof=1), median_controls=float(d["n_controls"].median()),
                        overlap_places=len(o), overlap_n1=np.average(o["effect"], weights=o["homes"]) if len(o) else np.nan,
                        overlap_76=np.average(o["effect_76"], weights=o["homes"]) if len(o) else np.nan,
                        supported=bool(l2 > 0), feasible=len(d) >= 20))
    S = pd.DataFrame(out)
    S["unit"] = "permits per 1,000 existing homes a year; before 2018-2022, after 2023-2025"
    S["note"] = (f"{int(T['usable'].sum())} of {len(T)} listed covered cities usable (Census permit files complete, homes known); "
                 f"{len(drop)} Washington/Idaho places with a 2018-2025 parking reform dropped from comparisons")
    S.to_csv(REFERENCE / "parking_ne_n1.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.round(3).T.to_string())
    print(T[~T["usable"]]["city"].tolist())


if __name__ == "__main__":
    main()
