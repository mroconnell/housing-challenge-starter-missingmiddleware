"""Test 56 flag list (docs/parking/CAUSAL_FRAMEWORK_PLAN.md, "Test 56", confound 1; committed before any count).
Reads no permit outcome: only the 74 batch places' names, keys and repeal years, place ids from the Census permit files
(for the 2010 population join, as Test 53), the Test 52b events table and the reform-type coding.

    uv run --all-extras python scripts/build_parking_t56_flags.py

A repeal place is flagged when a plex legalization falls within 3 years either side of its repeal year:
  1. reference/parking_t52_b_events.csv rows of type "middle-housing upzoning", "TOD upzoning" or "state housing law"
     matched to the place (|event year - repeal year| <= 3), taken as the lock names them (the description is kept;
     some "state housing law" rows are ADU laws, e.g. Colorado HB24-1152, and are flagged all the same);
  2. Oregon HB 2001 (2019; adopted 2019, compliance 2021 for cities of 10,000-24,999 and 2022 for 25,000+): Oregon
     places of 10,000+ people (2010 census) whose repeal year is within 3 years of 2019 or of their compliance year;
  3. reference/parking_reform_type_15.csv (same_time_changes_within_1yr, rewrite_density_height_uses): coded by hand
     below (yes / unclear / no); only "yes" flags.
Every Oregon place is listed (`oregon`) for the no-Oregon variant. The 25,000 split uses the same 2010 population.
Outputs: reference/parking_t56_flags.csv (74 rows, in the batch's place order), reference/parking_t56_plex_legal_15.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import parking_t56_common as c56  # noqa: E402

REF = ROOT / "reference"
BATCH = REF / "batch_2026-11-05"
WINDOW = 3
EVENT_TYPES = ("middle-housing upzoning", "TOD upzoning", "state housing law")
HB2001_ADOPTED = 2019
HB2001_COMPLIANCE = {10_000: 2021, 25_000: 2022}  # population floor -> compliance year (ORS 197.758)

# reform-type coding (15 long-set places): does a change within 1 year, or the rewrite, legalize 2-4 unit homes?
TYPE15 = {
    ("San Francisco", "California"): ("no", "process changes (Ord. 179-18) and Central SoMa heights; no plex legalization coded"),
    ("Emeryville", "California"): ("no", "parking article rewrite; residential use rows identical 2017 vs 2021"),
    ("Bastrop", "Texas"): ("yes", "full code rewrite: duplex P2-P4, triplex/fourplex P4 place types"),
    ("Buffalo", "New York"): ("yes", "Green Code rewrite: density limits relaxed in residential zones"),
    ("Hudson", "New York"): ("no", "single-section amendment (commercial uses)"),
    ("Canandaigua", "New York"): ("unclear", "L.L. 1-2020 amended residential districts; content not read"),
    ("Hartford", "Connecticut"): ("no", "residential permitted-use table unchanged"),
    ("Seabrook", "New Hampshire"): ("yes", "mixed use of up to 5 units made conditional in zone 2"),
    ("Windham", "Maine"): ("yes", "residential uses permitted in C-1; minimum lot size and density removed in C-1/C-2"),
    ("Dunwoody", "Georgia"): ("no", "stand-alone text amendment"),
    ("Branson", "Missouri"): ("unclear", "unified development code; use-table and density changes not verified"),
    ("Maumee", "Ohio"): ("no", "no density, height or use changes found"),
    ("Mount Pleasant", "Michigan"): ("unclear", "form-based rewrite: more mixed use, but duplexes limited in CD-3; direction unclear"),
    ("Saranac Lake", "New York"): ("yes", "2016 code rewrite: administrative permit for two-family, smaller lots"),
    ("Ecorse", "Michigan"): ("yes", "new zoning ordinance: 2-4 family by right in MFR/FR/NMU/CC"),
}


def main() -> None:
    e = pd.read_csv(BATCH / "parking_expanded_effects.csv",
                    usecols=["prn_key", "place", "state", "source", "key", "event_year", "status", "outcome", "population"])
    real = e[(e["status"] == "included") & (e["outcome"] == "all")].reset_index(drop=True)
    assert len(real) == 74, len(real)
    real["event_year"] = real["event_year"].astype(int)
    # 2010 population as Test 53 (place ids from the permit files' panel, as run_parking_method2.Data)
    geo = c56.geo_table(c56.all_homes_bps()).drop_duplicates("key", keep="last").set_index("key")["acs_geoid"]
    pop10, src = c56.pop2010(real["key"].tolist(), geo, real["population"].astype(float).tolist())
    real["pop2010"], real["pop2010_source"] = pop10, src
    real["size_group"] = ["under 25,000" if v < c56.SPLIT else "25,000 or more" for v in pop10]
    real["oregon"] = real["state"] == "Oregon"

    ev = pd.read_csv(REF / "parking_t52_b_events.csv", dtype=str)
    ev = ev[ev["event_type"].isin(EVENT_TYPES) & ev["bps_key"].isin(set(real["key"]))].copy()
    ev["event_year"] = pd.to_numeric(ev["event_year"], errors="coerce")
    flags = {k: [] for k in real["key"]}
    for r in ev.itertuples():
        ey = int(real.loc[real["key"] == r.bps_key, "event_year"].iloc[0])
        if pd.notna(r.event_year) and abs(int(r.event_year) - ey) <= WINDOW:
            flags[r.bps_key].append(f"52b {r.event_type}: {r.description} ({int(r.event_year)})")
    for r in real[real["oregon"]].itertuples():
        if r.pop2010 >= 10_000:
            comp = HB2001_COMPLIANCE[25_000 if r.pop2010 >= 25_000 else 10_000]
            if min(abs(r.event_year - HB2001_ADOPTED), abs(r.event_year - comp)) <= WINDOW:
                flags[r.key].append(f"Oregon HB 2001 (adopted {HB2001_ADOPTED}, compliance {comp})")
    t15 = pd.read_csv(REF / "parking_reform_type_15.csv")
    t15_code = {}
    for r in t15.itertuples():
        code, why = TYPE15[(r.place, r.state)]
        m = real[(real["place"] == r.place) & (real["state"] == r.state)]
        t15_code[(r.place, r.state)] = code
        if code == "yes" and len(m):
            k = m["key"].iloc[0]
            if abs(int(r.event_year_used) - int(m["event_year"].iloc[0])) <= WINDOW:
                flags[k].append(f"reform-type coding: {why}")
    real["flag_plex"] = real["key"].map(lambda k: bool(flags[k]))
    real["flag_reasons"] = real["key"].map(lambda k: " | ".join(flags[k]))
    real["type15_code"] = [t15_code.get((p, s), "") for p, s in zip(real["place"], real["state"])]
    real.insert(0, "i", range(len(real)))
    cols = ["i", "place", "state", "key", "prn_key", "source", "event_year", "pop2010", "pop2010_source", "size_group",
            "oregon", "flag_plex", "flag_reasons", "type15_code"]
    real[cols].to_csv(REF / "parking_t56_flags.csv", index=False)

    # guard 2: plex legality before repeal, 15 long-set places only (listed as cases, not a split)
    keep = ["place", "state", "event_year_used", "approval_2unit_before", "approval_3to4_before", "req_before_2unit",
            "req_before_3to4", "same_time_changes_within_1yr", "rewrite_density_height_uses", "confidence"]
    L = t15[keep].copy()
    L["in_74"] = [((p, s) in set(zip(real["place"], real["state"]))) for p, s in zip(L["place"], L["state"])]
    L["plex_change_code"] = [TYPE15[(p, s)][0] for p, s in zip(L["place"], L["state"])]
    L.to_csv(REF / "parking_t56_plex_legal_15.csv", index=False)

    print("places:", len(real), "| flagged:", int(real["flag_plex"].sum()), "| Oregon:", int(real["oregon"].sum()),
          "| flagged or Oregon:", int((real["flag_plex"] | real["oregon"]).sum()))
    print("size groups:", real["size_group"].value_counts().to_dict(), "| 2010 population fallback:",
          int((real["pop2010_source"] != "2010 census (Gazetteer)").sum()))
    src = pd.Series([s.split(":")[0].split(" (")[0] for f in flags.values() for s in f]).value_counts()
    print("flag reasons by source:", src.to_dict())
    pd.set_option("display.width", 250)
    print(real[real["flag_plex"]][["place", "state", "event_year", "pop2010", "flag_reasons"]].to_string(index=False))


if __name__ == "__main__":
    main()
