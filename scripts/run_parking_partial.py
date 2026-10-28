"""Older and partial parking reforms (docs/parking/PARTIAL_REFORMS_PLAN.md).

    uv run python scripts/fetch_parking_older_reforms.py
    uv run python scripts/run_parking_partial.py

Inputs: reference/parking_partial_checks.csv (ordinance and date checks).
Outputs: reference/parking_partial_effects.csv, reference/parking_partial_estimates.csv
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

import run_parking_comparison as rpc  # noqa: E402
import run_parking_expanded as rpe  # noqa: E402
from missing_middleware.foundation import parsers  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

D = RAW / "parking_older_reforms"


def bps_all() -> pd.DataFrame:
    frames = [rpc.read_bps_us()]
    for f in sorted(D.glob("we20[01][0-9]a.txt")):
        y = int(f.name[2:6])
        if 2007 <= y <= 2011:
            d = parsers.read_bps(f, "place", state_fips=None)
            d["year"] = y
            frames.append(d)
    return pd.concat(frames, ignore_index=True)


def homes_2010() -> pd.Series:
    with zipfile.ZipFile(D / "Gaz_places_national.zip") as z:
        g = pd.read_csv(io.BytesIO(z.read("Gaz_places_national.txt")), sep="\t", dtype={"GEOID": str}, encoding="latin-1")
    g.columns = [c.strip() for c in g.columns]
    return g.set_index("160|" + g["GEOID"])["HU10"].astype(float)


def main() -> None:
    checks = pd.read_csv(REFERENCE / "parking_partial_checks.csv")
    use = checks[checks["use"]].copy()
    bps = bps_all()
    p = cmp.panel(bps)
    homes_geo = rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001")
    pop_geo = rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001")
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    popn = geo["acs_geoid"].map(pop_geo)
    h_acs = geo["acs_geoid"].map(homes_geo)
    h_10 = geo["acs_geoid"].map(homes_2010())
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    reformed = tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
    excluded = {k for r in reformed.drop_duplicates("prn_key").itertuples()
                if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[real["source"] != "partial-reforms search"]
    excluded |= set(real["key"].dropna())
    rows = []
    orig_first = cmp.FIRST_YEAR
    for c in use.itertuples():
        k = cmp.match_place(p, rpc.STATE_FIPS.get(c.state, "??"), c.place, None)
        excluded.add(k) if k else None
        if k is None:
            rows.append(dict(place=c.place, state=c.state, group=c.group, status="not found in permit files"))
            continue
        ey = int(c.event_year)
        homes = (h_10 if ey < 2015 else h_acs)
        homes = homes[homes > 0]
        cmp.FIRST_YEAR = 2007 if ey < 2015 else orig_first
        e = cmp.effects(p, pd.DataFrame([{"key": k, "event_year": ey}]), excluded - {k}, homes, popn, min_post=1)
        cmp.FIRST_YEAR = orig_first
        if e.empty:
            rows.append(dict(place=c.place, state=c.state, group=c.group, key=k, event_year=ey, status="no result"))
            continue
        for x in e.to_dict("records"):
            x.update(place=c.place, state=c.state, group=c.group, key=k, event_year=ey, population=float(popn.get(k, np.nan)),
                     prn_key=f"{c.place}, {c.state}, United States", acs_geoid=geo.loc[k, "acs_geoid"],
                     homes_source="2010 census" if ey < 2015 else "ACS 2020-2024")
            rows.append(x)
    out = pd.DataFrame(rows)
    if "homes" in out:
        out["weight"] = out["homes"] * out["n_post"]
    out.round(4).to_csv(REFERENCE / "parking_partial_effects.csv", index=False)
    pd.set_option("display.width", 250)
    cols = [c for c in ("place", "state", "group", "event_year", "status", "pre_years", "post_years", "n_controls", "pop_window", "homes", "effect") if c in out]
    print(out[out.get("outcome", "all") != "2plus"][cols].round(2).to_string(index=False))
    inc = out[(out["status"] == "included") & (out["outcome"] == "all")].reset_index(drop=True)
    est = []
    for lab, d in (("Transit-area or district reforms", inc[inc["group"] == "transit-area or district"]),
                   ("Citywide at the benchmark (main-sample candidates)", inc[inc["group"] == "citywide benchmark"])):
        d = d.reset_index(drop=True)
        if len(d) >= 2:
            m, lo, hi = rpe.boot_mean(d["effect"].values, d["weight"].values)
        elif len(d) == 1:
            m, lo, hi = float(d["effect"].iloc[0]), np.nan, np.nan
        else:
            continue
        est.append(dict(case=lab, places=len(d), effect=m, p05=lo, p95=hi))
    # main comparison with the citywide candidates added (for the owner's decision)
    base = real[(real["status"] == "included") & (real["outcome"] == "all")][["place", "effect", "homes", "n_post"]].assign(
        weight=lambda x: x["homes"] * x["n_post"])
    add = inc[inc["group"] == "citywide benchmark"][["place", "effect", "homes", "n_post", "weight"]]
    d = pd.concat([base, add]).reset_index(drop=True)
    m, lo, hi = rpe.boot_mean(d["effect"].values, d["weight"].values)
    est.append(dict(case="Main comparison with the citywide candidates added", places=len(d), effect=m, p05=lo, p95=hi))
    est = pd.DataFrame(est)
    est.round(4).to_csv(REFERENCE / "parking_partial_estimates.csv", index=False)
    print(est.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
