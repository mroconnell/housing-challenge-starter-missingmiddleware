"""Round-3 variables V4-V15 for the 71 expanded repeal places (docs/parking/ROUND3_PLAN.md).
No effects are read: only the place list (prn_key, key, event_year) from the expanded match file.

    uv run python scripts/build_parking_round3_vars.py
Output: reference/parking_round3_vars.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_comparison as rpc  # noqa: E402
from missing_middleware.foundation import parsers  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

ACS = RAW / "census_acs5_2024_tbsf"
MKT = RAW / "census_acs5_2024_tbsf_market"


def acs(path, cols):
    d = parsers.read_acs_sf(path, state_fips="", sumlevels=("040", "060", "160"))
    d["acs_geoid"] = d["sumlevel"] + "|" + d["geoid"]
    return d.set_index("acs_geoid")[cols]


def main() -> None:
    m = pd.read_csv(REFERENCE / "parking_expanded_match.csv", dtype={"key": str})
    m = m[m["use"]].copy()
    m["event_year"] = m["event_year"].astype(float).astype(int)
    raw = rpc.read_bps_us()
    p = cmp.panel(raw)
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    m["acs_geoid"] = m["key"].map(geo["acs_geoid"])

    a = acs(MKT / "acsdt5y2024-b25003.dat", ["B25003_E001", "B25003_E003"])
    b = acs(ACS / "acsdt5y2024-b25002.dat", ["B25002_E001", "B25002_E003"])
    c = acs(ACS / "acsdt5y2024-b25034.dat", ["B25034_E001", "B25034_E009", "B25034_E010", "B25034_E011"])
    d = acs(ACS / "acsdt5y2024-b25024.dat", ["B25024_E001", "B25024_E006", "B25024_E007", "B25024_E008", "B25024_E009"])
    t = a.join(b).join(c).join(d)
    t["V4_renter_share"] = t["B25003_E003"] / t["B25003_E001"]
    t["V5_vacancy_rate"] = t["B25002_E003"] / t["B25002_E001"]
    t["V6_share_built_before_1960"] = t[["B25034_E009", "B25034_E010", "B25034_E011"]].sum(axis=1) / t["B25034_E001"]
    t["V7_share_homes_5plus"] = t[["B25024_E006", "B25024_E007", "B25024_E008", "B25024_E009"]].sum(axis=1) / t["B25024_E001"]
    m = m.merge(t[[c for c in t.columns if c.startswith("V")]], left_on="acs_geoid", right_index=True, how="left")

    # permits before repeal (BPS): 5+ share, value per unit relative to the state, volatility
    raw = raw.assign(key=raw["state_fips"].str.strip() + "|" + raw["bps_id"].str.strip())
    val_cols = [c for c in raw.columns if c.endswith("_value") and not c.endswith("_rep")]
    raw["value_total"] = raw[val_cols].sum(axis=1)
    st = raw.groupby(["state_fips", "year"])[["value_total", "units_total"]].sum()
    homes = geo["acs_geoid"].map(acs(ACS / "acsdt5y2024-b25002.dat", ["B25002_E001"])["B25002_E001"])
    rows = []
    for r in m.itertuples():
        pre, _ = cmp.windows(r.event_year)
        x = raw[(raw["key"] == r.key) & raw["year"].isin(pre)]
        u = x["units_total"].sum()
        sf = r.key.split("|")[0]
        stv = st.loc[[(sf, y) for y in pre if (sf, y) in st.index]].sum()
        rate = x.groupby("year")["units_total"].sum() / homes.get(r.key, np.nan) * 1000
        rows.append(dict(prn_key=r.prn_key,
                         V8_share_permits_5plus_before=(x["5plus_units"].sum() / u) if u else np.nan,
                         V9_value_per_unit_rel=((x["value_total"].sum() / u) / (stv["value_total"] / stv["units_total"])) if u and stv["units_total"] else np.nan,
                         V10_permit_volatility=(rate.std(ddof=1) / rate.mean()) if rate.mean() else np.nan,
                         V15_region=str(x["region"].dropna().iloc[0]).strip() if len(x) and x["region"].notna().any() else None))
    m = m.merge(pd.DataFrame(rows), on="prn_key", how="left")

    # own records
    ck = pd.concat([pd.read_csv(REFERENCE / "parking_repeal_checks.csv", dtype=str),
                    pd.read_csv(REFERENCE / "parking_repeal_checks_expanded.csv", dtype=str)]).drop_duplicates("prn_key").set_index("prn_key")
    pr = ck["prior_partial_reforms"].fillna("").str.strip().str.lower()
    m["V11_repeal_year"] = m["event_year"]
    m["V12_prior_partial_reform"] = m["prn_key"].map(~(pr.eq("") | pr.str.startswith(("none", "no ", "unknown", "n/a")))).astype(float)
    m["V13_rewrite_same_time"] = m["simultaneous_rewrite"].astype(float)
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    ref = tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city") & (tax["status"] == "adopted")]
    reform_year = {}
    for r in ref.dropna(subset=["adopted_year"]).itertuples():
        k = cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population)
        if k:
            reform_year[k] = min(int(r.adopted_year), reform_year.get(k, 9999))
    m["V14_state_large_city_share_repealed"] = [cmp.state_share_repealed(p, k.split("|")[0], int(y), reform_year) for k, y in zip(m["key"], m["event_year"])]
    cols = ["prn_key", "place", "state", "key", "acs_geoid"] + sorted([c for c in m.columns if c.startswith("V")], key=lambda c: int(c.split("_")[0][1:]))
    m[cols].round(5).to_csv(REFERENCE / "parking_round3_vars.csv", index=False)
    print(m[cols].notna().mean().round(2).to_dict())


if __name__ == "__main__":
    main()
