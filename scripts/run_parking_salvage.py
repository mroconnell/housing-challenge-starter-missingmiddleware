"""Rescue dropped parking repeal places (docs/parking/SALVAGE_PLAN.md, sections 1-2).

    uv run python scripts/run_parking_salvage.py

- South Bend, Indiana: permits are filed in the Census row "St. Joseph County Unincorporated Area" (one
  building department for the city and the unincorporated county). Added as that combined area.
- Gastonia, Avondale Estates, Calumet: after-years cut at the first missing year (0 months reported counts as
  missing), before-years trimmed to the unbroken run before the repeal.
Outputs: reference/parking_salvage_effects.csv, reference/parking_salvage_estimates.csv
"""
from __future__ import annotations

import sys
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

SJ_KEY = "18|687500"          # St. Joseph County Unincorporated Area (includes the City of South Bend)
SOUTH_BEND = "160|1871000"
SJ_COUNTY = "050|18141"
SJ_OTHER_PLACES = ("Mishawaka", "New Carlisle", "Walkerton")   # places with their own permit rows
TRIM_CASES = ("Gastonia", "Avondale Estates", "Calumet")


def acs(path: Path, col: str, sumlevels=("050", "160")) -> pd.Series:
    d = parsers.read_acs_sf(path, state_fips="", sumlevels=sumlevels)
    return d.assign(g=d["sumlevel"] + "|" + d["geoid"]).set_index("g")[col]


def main() -> None:
    bps = rpc.read_bps_us()
    p = cmp.panel(bps)
    # add the St. Joseph County row, which panel() drops as a county remainder
    sj = bps[(bps["state_fips"].astype(str).str.strip() == "18") & (bps["bps_id"].astype(str).str.strip() == "687500")].copy()
    sj["fips_place"] = "00001"
    p = pd.concat([p, cmp.panel(sj)], ignore_index=True)
    months = bps.assign(key=bps["state_fips"].astype(str).str.strip() + "|" + bps["bps_id"].astype(str).str.strip())
    months = months.set_index(["key", "year"])["months_reported"]

    homes_geo = rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001")
    pop_geo = rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001")
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(homes_geo)
    popn = geo["acs_geoid"].map(pop_geo)
    h2 = acs(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001")
    p2 = acs(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001")
    others = [k for k in geo.index if k.startswith("18|") and geo.loc[k, "county_fips"] == "141" and geo.loc[k, "name"].replace(" town", "") in SJ_OTHER_PLACES]
    homes[SJ_KEY] = h2[SJ_COUNTY] - homes.reindex(others).sum()
    popn[SJ_KEY] = p2[SJ_COUNTY] - popn.reindex(others).sum()
    sb_share = float(h2[SOUTH_BEND] / homes[SJ_KEY])
    homes = homes[homes > 0]

    # same exclusions as the expanded comparison (every reformed place is kept out of comparison pools)
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    reformed = tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
    excluded = {k for r in reformed.drop_duplicates("prn_key").itertuples()
                if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[real["source"] != "rescued"]
    excluded |= set(real["key"].dropna()) | {SJ_KEY}

    match = pd.read_csv(REFERENCE / "parking_expanded_match.csv")
    rows = []
    sb = match[match["place"] == "South Bend"].iloc[0]
    cases = [dict(prn_key=sb.prn_key, place="South Bend (with unincorporated St. Joseph County)", state="Indiana",
                  key=SJ_KEY, event_year=int(sb.event_year), rating=sb.rating, rule="combined area",
                  simultaneous_rewrite=bool(sb.simultaneous_rewrite))]
    for nm in TRIM_CASES:
        m = match[match["place"] == nm].iloc[0]
        cases.append(dict(prn_key=m.prn_key, place=nm, state=m.state, key=m.key, event_year=int(m.event_year),
                          rating=m.rating, rule="missing years trimmed",
                          simultaneous_rewrite=bool(m.simultaneous_rewrite)))
    orig_windows = cmp.windows
    for c in cases:
        pre, post = orig_windows(c["event_year"])
        have = {y for y in p.loc[p["key"] == c["key"], "year"] if months.get((c["key"], y), 0) > 0}
        post_ok = []
        for y in post:
            if y not in have:
                break
            post_ok.append(y)
        pre_ok = []
        for y in sorted(pre, reverse=True):
            if y not in have:
                break
            pre_ok.insert(0, y)
        note = f"before {pre_ok[0] if pre_ok else '-'}-{pre_ok[-1] if pre_ok else '-'}, after {post_ok[0] if post_ok else '-'}-{post_ok[-1] if post_ok else '-'}"
        if len(pre_ok) < cmp.PRE_YEARS_MIN or len(post_ok) < 1:
            rows.append({**c, "status": "excluded: too few years after trimming", "note": note})
            continue
        cmp.windows = lambda ey, a=pre_ok, b=post_ok: (list(a), list(b))
        # complete() would reject the place for its own gap years outside the trimmed window; only the window counts
        e = cmp.effects(p, pd.DataFrame([{"key": c["key"], "event_year": c["event_year"]}]), excluded - {c["key"]},
                        homes, popn, min_post=1)
        cmp.windows = orig_windows
        if e.empty or e.iloc[0]["status"] != "included":
            rows.append({**c, "status": "excluded: " + (str(e.iloc[0]["status"]) if not e.empty else "no result"), "note": note})
            continue
        for x in e.to_dict("records"):
            x.update({k: v for k, v in c.items()})
            x["note"] = note
            x["source"] = "rescued"
            x["population"] = float(popn.get(c["key"], np.nan))
            if c["key"] == SJ_KEY:
                x["effect_combined_area"] = x["effect"]
                x["south_bend_share_of_homes"] = sb_share
                x["effect"] = x["effect"] / sb_share
                x["homes"] = float(h2[SOUTH_BEND])
                x["population"] = float(p2[SOUTH_BEND])
                x["acs_geoid"] = SOUTH_BEND
            rows.append(x)
    out = pd.DataFrame(rows)
    out["weight"] = out["homes"] * out["n_post"]
    out.round(4).to_csv(REFERENCE / "parking_salvage_effects.csv", index=False)
    print(out[["place", "outcome", "status", "note", "n_post", "homes", "effect"] + [c for c in ("effect_combined_area",) if c in out]].round(2).to_string())
    out = out[(out.get("outcome") == "all") | (out["status"] != "included")]

    base = real[(real["status"] == "included") & (real["outcome"] == "all")][["place", "effect", "homes", "n_post"]].copy()
    base["weight"] = base["homes"] * base["n_post"]
    add = out[out["status"] == "included"][["place", "effect", "homes", "n_post", "weight"]]
    est = []
    for label, d in (("Expanded 71 places (current)", base), ("71 plus rescued places", pd.concat([base, add])),
                     ("71 plus rescued, South Bend not scaled", pd.concat([base, add.assign(effect=np.where(
                         add["place"].str.startswith("South Bend"), out.loc[out["status"] == "included"].get("effect_combined_area", add["effect"]), add["effect"]))]))):
        d = d.reset_index(drop=True)
        m, lo, hi = rpe.boot_mean(d["effect"].values, d["weight"].values)
        est.append(dict(case=label, places=len(d), effect=m, p05=lo, p95=hi))
    est = pd.DataFrame(est)
    est.round(4).to_csv(REFERENCE / "parking_salvage_estimates.csv", index=False)
    print(est.round(2).to_string(index=False))
    print("South Bend share of combined-area homes", round(sb_share, 3))


if __name__ == "__main__":
    main()
