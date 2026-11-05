"""POST HOC (written after all earlier results were seen; Ryan 2026-11-05 22:33 "go"): the city-type and size splits
re-run with the parking thread's settled six classes and 2010 population, so both studies classify cities the same
way. Reported only; none of this changes the main result or the plan's reading rules.

    uv run python scripts/ca_ab2097_posthoc3.py

Inputs reused unchanged from the parking thread (Test 53): reference/parking_place_ruca_traits.csv, column
area_class6 (main city, secondary principal city, suburb, exurb, outside metro, rural; file at 03c49d7a, code 970037ea),
and 2010 census population POP10 from data/raw/parking_older_reforms/Gaz_places_national.zip (2010 Gazetteer places),
as scripts/run_parking_t53_area.py does. Places are joined by BPS key (city) and by GEOID 06+PLACEFP (population).

1. By class: the city-level (BPS) share slope, homes-weighted, and the near-vs-ring headline (homes other than ADUs,
   main group, main map). n per class; classes with fewer than 5 jurisdictions not run; fewer than 10 read as thin.
   County unincorporated areas have no class and are left out of the split (as in post hoc 2).
2. Size: the city-level check with log10(2010 population) as a continuous interaction, homes-weighted and equal
   weight: change in the share slope per tenfold more people (two-sided), and the share slope at 10,000, 50,000,
   250,000 and 1,000,000 people (conventions). Lead placebo (2021-2022 minus 2018-2020) the same way.
Units: city-level slopes are change in BPS permits per 1,000 existing homes a year per 1.0 share of homes within
1/2 mile; near-vs-ring rows are homes in issued permits per 1,000 existing homes (2020) a year, 2023-2025 vs 2018-2022.
90% ranges from 2,000 resamples (places or jurisdictions).

Reading rule, set before the run (same for both signs): none of these is evidence of cause on its own; a row whose
range excludes 0 is "a pattern worth a planned test", never a finding. Chance line: of about 30 rows, about 3 would
exclude 0 by chance with no real differences. Results that repeat post hoc 2's pattern are not independent of it.

Outputs: reference/ca_ab2097_posthoc3_city_types6.csv, reference/ca_ab2097_posthoc3_size_pop.csv.
"""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ca_ab2097_estimate as E  # noqa: E402
import ca_ab2097_posthoc2 as P2  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import ab2097 as ab  # noqa: E402


def pop10() -> pd.Series:
    z = zipfile.ZipFile(RAW / "parking_older_reforms" / "Gaz_places_national.zip")
    g = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), sep="\t", dtype=str)
    g.columns = g.columns.str.strip()
    return pd.to_numeric(g.set_index("GEOID")["POP10"], errors="coerce")


def place_table6(b: pd.DataFrame) -> pd.DataFrame:
    t = P2.place_table(b)
    rt = pd.read_csv(REFERENCE / "parking_place_ruca_traits.csv", dtype=str)
    rt = rt[rt.state_fips == "06"].assign(bps=lambda r: r.key.str.split("|").str[1])
    t = t.merge(rt[["bps", "area_class6"]], on="bps", how="left")
    t["area_class6"] = t.area_class6.fillna("unmatched")
    t["pop10"] = ("06" + t.placefp).map(pop10())
    return t


def size_pop(t: pd.DataFrame) -> pd.DataFrame:
    t = t[t.pop10 > 0]
    lp = np.log10(t.pop10.to_numpy(float))
    X = np.c_[np.ones(len(t)), t.share, lp, t.share * lp]
    rng = np.random.default_rng(E.SEED)
    idx = [rng.integers(0, len(t), len(t)) for _ in range(E.DRAWS)]
    rows = []
    for col in ("change", "lead"):
        y = t[col].to_numpy(float)
        for wname, w in (("homes-weighted", t.homes.to_numpy(float)), ("equal weight", np.ones(len(t)))):
            beta = P2.wls(X, y, w)
            dr = np.array([P2.wls(X[i], y[i], w[i]) for i in idx])
            lo, hi = E.interval(dr[:, 3])
            rows.append({"outcome": col, "weight": wname, "term": "share x log10(2010 population)",
                         "estimate": beta[3], "low": lo, "high": hi,
                         "unit": "change in the share slope per tenfold more people (two-sided)"})
            for pp in (10_000, 50_000, 250_000, 1_000_000):
                v, dv = beta[1] + beta[3] * np.log10(pp), dr[:, 1] + dr[:, 3] * np.log10(pp)
                lo, hi = E.interval(dv)
                rows.append({"outcome": col, "weight": wname, "term": f"share slope at {pp:,} people",
                             "estimate": v, "low": lo, "high": hi,
                             "unit": "change in BPS permits per 1,000 existing homes a year per 1.0 share of homes "
                                     "within 1/2 mile"})
    out = pd.DataFrame(rows)
    out["n_places"] = len(t)
    return out


def main() -> None:
    b = pd.read_parquet(E.CACHE / "blocks.parquet")
    p = pd.read_parquet(E.CACHE / "permits.parquet")
    rep = ab.full_reporters(p)
    c = E.cells_for(b, "main")
    main_j = E.with_treated_land(c, [j for j in rep if j not in E.PLACEBO | E.DROPPED])
    t = place_table6(b)
    print(f"places: {len(t)}; with 2010 population: {int((t.pop10 > 0).sum())}")
    print(t.area_class6.value_counts().to_string())
    bc = P2.by_class(t, b, E.permits_for(p, "main"), main_j, "area_class6").assign(label="POST HOC")
    bc.to_csv(REFERENCE / "ca_ab2097_posthoc3_city_types6.csv", index=False)
    print(bc.round(3).to_string(index=False))
    sp = size_pop(t).assign(label="POST HOC")
    sp.to_csv(REFERENCE / "ca_ab2097_posthoc3_size_pop.csv", index=False)
    print(sp.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
