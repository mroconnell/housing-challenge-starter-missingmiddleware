"""CA AB 2097 study, step 1b (part 2): permit cleaning, field checks and permit counts around the rail map.
Counts only: no rates, no differences, no estimates. Zones use the rail map only (bus stops not yet built), so
"ring" and "beyond" here still include land near bus major stops; the ring of the plan is 1/2-2/3 plus 2/3-1 1/2.

Plan: docs/parking/CA_AB2097_PLAN.md (locked; section 8 and section 9 entries for density bonus, LIHTC, HUD check,
rail-only edge). Runs only after the audit has checked this script.

Inputs
- HCD Annual Progress Report Table A2 (data/raw/hcd_apr_a2/tablea2.csv), cleaned with the earlier AB 2097 test's rules
  (missing_middleware.tod.ab2097.clean_permits: issue-date dating, cross-report-year de-duplication, street-level
  geocodes only).
- Rail stops: reference/ca_ab2097_rail_stations.csv (step 1b part 1), stops open at the end of 2022 (opened before
  2018, 2018-2022, or closed after 2022 and added back).

Outputs (no addresses, no project ids)
- reference/ca_ab2097_step1_field_checks.csv: by report year, rows with permits, share with the density-bonus field
  filled, share with the financing field filled, rows matching the LIHTC text list, and LIHTC-matched rows dropped for
  lacking a street-level point.
- reference/ca_ab2097_step1_lihtc_samples.csv: 20 random matched and 20 random unmatched non-blank financing values
  (the field text only), seed 20261105, for review before any estimate.
- reference/ca_ab2097_step1_rail_counts.csv: by permit year, jurisdiction group (main kept, placebo, dropped) and zone
  (rail 0-1/3, 1/3-1/2, 1/2-2/3 mile, ring 1/2-1 1/2 mile, beyond), number of projects and homes (all homes, homes in
  2+ unit buildings, homes in projects of 5+ homes). The same for Palo Alto alone.
- Printed: the cleaning counts and the full-reporter count.

    uv run python scripts/ca_ab2097_step1b_permits.py            # field checks and samples only
    uv run python scripts/ca_ab2097_step1b_permits.py --counts   # later, after the audit clears the counts
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import ab2097 as ab  # noqa: E402
import run_ab2097_test as run  # noqa: E402

A2 = RAW / "hcd_apr_a2" / "tablea2.csv"
COLS = ["JURIS_NAME", "YEAR", "UNIT_CAT", "NO_BUILDING_PERMITS", "LATITUDE", "LONGITUDE", "STD_ADDRESS",
        "STREET_ADDRESS", "BP_ISSUE_DT1", "DENSITY_BONUS_TOTAL", "FIN_ASSIST_NAME"]
LIHTC_RE = r"(?i)tax credit|lihtc|\bctcac\b|\btcac\b|\bcdlac\b"  # fixed in the plan (2026-11-05 17:05 entry)
SEED = 20261105
MILE = ab.MILE_M
# Plan: dropped from the main estimate; used as placebo cities (section 8, audit blocks; Mountain View dropped).
PLACEBO = set(ab.ALREADY_NO_MINIMUMS) | set(ab.REPEALED_CITYWIDE_LATER)
DROPPED = {"MOUNTAIN VIEW"}


def zone(d: np.ndarray) -> np.ndarray:
    return np.select([d < MILE / 3, d < MILE / 2, d < 2 * MILE / 3, d < 1.5 * MILE],
                     ["rail 0-1/3", "rail 1/3-1/2", "rail 1/2-2/3", "ring 2/3-1 1/2"], "beyond 1 1/2")


def field_checks(a2: pd.DataFrame) -> None:
    d = a2[pd.to_numeric(a2.NO_BUILDING_PERMITS, errors="coerce").fillna(0) > 0].copy()
    d["db_filled"] = d.DENSITY_BONUS_TOTAL.notna() & (d.DENSITY_BONUS_TOTAL.astype(str).str.strip() != "")
    fin = d.FIN_ASSIST_NAME.fillna("").astype(str).str.strip()
    d["fin_filled"] = fin != ""
    d["lihtc"] = fin.str.contains(LIHTC_RE, regex=True)
    geo = ab.is_geocoded(pd.to_numeric(d.LATITUDE, errors="coerce"), pd.to_numeric(d.LONGITUDE, errors="coerce"),
                         d.STD_ADDRESS)
    d["lihtc_dropped_not_street"] = d.lihtc & ~geo
    d["not_street"] = ~geo
    d["is_5plus"] = d.UNIT_CAT.astype(str).str.strip() == "5+"
    d["db_above_0_5plus"] = d.is_5plus & (pd.to_numeric(d.DENSITY_BONUS_TOTAL, errors="coerce").fillna(0) > 0)
    g = d.groupby("YEAR").agg(rows_with_permits=("db_filled", "size"), db_filled=("db_filled", "mean"),
                              fin_filled=("fin_filled", "mean"), lihtc_rows=("lihtc", "sum"),
                              lihtc_dropped_not_street=("lihtc_dropped_not_street", "sum"),
                              all_rows_dropped_not_street=("not_street", "sum"),
                              rows_5plus=("is_5plus", "sum"), rows_5plus_db_above_0=("db_above_0_5plus", "sum")
                              ).reset_index()
    g["share_all_rows_dropped_not_street"] = g.all_rows_dropped_not_street / g.rows_with_permits
    g["share_5plus_rows_db_above_0"] = g.rows_5plus_db_above_0 / g.rows_5plus
    g = g.rename(columns={"YEAR": "report_year", "db_filled": "share_density_bonus_filled",
                          "fin_filled": "share_financing_filled"})
    g.round(4).to_csv(REFERENCE / "ca_ab2097_step1_field_checks.csv", index=False)
    print(g.round(3).to_string(index=False))
    vals = fin[d.fin_filled]
    m, u = vals[d.lihtc[d.fin_filled]], vals[~d.lihtc[d.fin_filled]]
    rng = np.random.default_rng(SEED)
    pick = lambda s: s.iloc[rng.choice(len(s), size=min(20, len(s)), replace=False)] if len(s) else s  # noqa: E731
    pd.concat([pd.DataFrame({"matched": True, "financing_text": pick(m).to_numpy()}),
               pd.DataFrame({"matched": False, "financing_text": pick(u).to_numpy()})]).to_csv(
        REFERENCE / "ca_ab2097_step1_lihtc_samples.csv", index=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--counts", action="store_true",
                    help="also write the permit counts by zone (held by the audit until the bus-map choice is in the "
                         "plan and the estimation script is committed)")
    a = ap.parse_args()
    a2 = pd.read_csv(A2, usecols=COLS, low_memory=False)
    field_checks(a2)
    if not a.counts:
        print("counts not written (run with --counts once the audit clears them)")
        return
    p, info = ab.clean_permits(a2.drop(columns=["DENSITY_BONUS_TOTAL", "FIN_ASSIST_NAME"]))
    print("cleaning:", info)
    rep = ab.full_reporters(p)
    print(f"full reporters: {len(rep)}")
    # project size (homes in the project across its records in the same permit year)
    p["project_homes_year"] = p.groupby(["project", "year"]).all_units.transform("sum")
    p["units_5plus_project"] = np.where(p.project_homes_year >= 5, p.all_units, 0.0)

    st = pd.read_csv(REFERENCE / "ca_ab2097_rail_stations.csv")
    st = st[st["mode"] != "ferry"]
    st = st[st.opened.isin(["before 2018 (assumed: not in openings table)", "2018-2022",
                            "closed or moved after 2022 (added back)"])]
    stops = run.lonlat_points(st.reset_index(drop=True), st.lon, st.lat)
    pts = run.lonlat_points(p, p.lon, p.lat)
    p["zone"] = zone(run.nearest_m(pts, stops))
    p["group"] = np.where(p.juris.isin(DROPPED), "dropped",
                          np.where(p.juris.isin(PLACEBO), "placebo",
                                   np.where(p.juris.isin(rep), "main (full reporters)", "not full reporter")))

    def counts(df: pd.DataFrame, area: str) -> pd.DataFrame:
        g = df.groupby(["year", "group", "zone"]).agg(projects=("project", "nunique"), homes=("all_units", "sum"),
                                                      homes_2plus=("units_2plus", "sum"),
                                                      homes_in_5plus_projects=("units_5plus_project", "sum")).reset_index()
        g.insert(0, "area", area)
        return g

    out = pd.concat([counts(p, "California"), counts(p[p.juris == "PALO ALTO"], "Palo Alto")], ignore_index=True)
    out.to_csv(REFERENCE / "ca_ab2097_step1_rail_counts.csv", index=False)
    print(out[out.area == "Palo Alto"].to_string(index=False))


if __name__ == "__main__":
    main()
