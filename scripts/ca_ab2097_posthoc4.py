"""POST HOC (written after all earlier results were seen; Ryan 2026-11-08 "sure, I'd like to know that"): does a city's
own reading of AB 2097 change what gets built? Reported only; it does not change the main result or the plan's rules.

    uv run python scripts/ca_ab2097_posthoc4.py

Within each city, land (2020 census blocks by internal point; permits by point) is split by two maps: the city's own
map (scripts/ca_ab2097_side_checks.city_polys) and our main map's 1/2-mile area (zone_main == "near"):
  city_only = inside the city's map, outside ours;  both;  ours_only = inside ours, outside the city's;
  neither = inside the city, outside both.
Contrasts (homes other than ADUs per 1,000 existing homes (2020) a year; after vs 2018-2022; difference-in-
differences; 90% range from 2,000 resamples of projects, since each is one city):
  A. "Local reading": city_only vs neither, in Santa Cruz (after = 2023-2025) and Sacramento (after = 2023 only,
     because Sacramento repealed minimums citywide from 2024-03-28; 2023-2025 shown beside it, labelled affected by
     the repeal).
  B. "Our reading only" (reverse case): ours_only vs neither, in Oakland (after = 2023-2025). Oakland is an early-reform
     city (no minimums in its downtown zones before 2023).
Counts of existing homes and of permitted homes in each area and period are reported first.
Labels: Santa Cruz's map is approximate (rebuilt by hand from its 2024 PDF); Sacramento's layer was created 2023-02-03
and republished since; Oakland's is "as of Spring 2023". Los Angeles's TOC land is not involved (no city here).

Reading rule, set before the run (same for both signs): these are supporting examples, not evidence of cause; a range
excluding 0 is "a pattern worth noting". Chance line: of the 4 contrast rows, each has about a 1 in 10 chance of
excluding 0 with no real difference. Few permits may fall in some areas; areas with fewer than 20 permitted homes in
either period are labelled too thin to read (a convention).

Output: reference/ca_ab2097_posthoc4_local_reading.csv (counts and contrasts; no addresses).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ca_ab2097_estimate as E  # noqa: E402
import ca_ab2097_side_checks as S  # noqa: E402
import run_ab2097_test as run  # noqa: E402
from missing_middleware import geom as G  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import ab2097 as ab  # noqa: E402

CASES = [("A: local reading", "SANTA CRUZ", "city_only", [2023, 2024, 2025], ""),
         ("A: local reading", "SACRAMENTO", "city_only", [2023], "after = 2023 only (citywide repeal from 2024-03-28)"),
         ("A: local reading", "SACRAMENTO", "city_only", [2023, 2024, 2025], "affected by the 2024 citywide repeal"),
         ("B: our reading only", "OAKLAND", "ours_only", [2023, 2024, 2025], "Oakland: early-reform city")]
THIN = 20


def main() -> None:
    b = pd.read_parquet(E.CACHE / "blocks.parquet").merge(
        run.read_blocks(["GEOID20", "INTPTLAT20", "INTPTLON20"])[["GEOID20", "x", "y"]], on="GEOID20")
    a2 = pd.read_csv(RAW / "hcd_apr_a2" / "tablea2.csv", usecols=E.A2_COLS, low_memory=False)
    p = E.add_census_points(E.clean_permits_full(a2), set(E.raw_keys(a2)))
    p = p[p.lat.notna()].copy()
    p = run.lonlat_points(p, p.lon, p.lat)
    stops = E.stop_sets()["main"]
    p["near_ours"] = run.nearest_m(p, stops) < E.MILE / 2
    rail = pd.read_csv(REFERENCE / "ca_ab2097_rail_stations.csv")
    rows, sized = [], set()
    for label, city, treat, after, note in CASES:
        polys, _ = S.city_polys(city, rail)
        bc, pc = b[b.juris == city].copy(), p[p.juris == city].copy()
        for frame, ours in ((bc, (bc.zone_main == "near").to_numpy()), (pc, pc.near_ours.to_numpy())):
            inc = G.points_in_any(frame.x.to_numpy(), frame.y.to_numpy(), polys)
            frame["zone"] = np.select([inc & ~ours, inc & ours, ~inc & ours], ["city_only", "both", "ours_only"], "neither")
            frame["upz"] = False
        cells = bc.groupby(["juris", "upz", "zone"])[["homes", "acres"]].sum().reset_index()
        g = ab.Group(city, [city], (treat, False), ("neither", False))
        before = E.BEFORE
        r = ab.estimate(g, cells, pc, "homes_non_adu", "per_1000_homes", before, after, draws=10)
        lo, hi, _ = ab.project_interval(g, cells, pc, "homes_non_adu", "per_1000_homes", before, after)
        thin = min(r["treat_units_before"], r["treat_units_after"], r["comp_units_before"], r["comp_units_after"]) < THIN
        rows.append({"contrast": label, "city": city, "treated_area": treat, "comparison_area": "neither",
                     "after_years": "-".join(map(str, [after[0], after[-1]])), "note": note,
                     "existing_homes_treated": r["treat_denominator"], "existing_homes_neither": r["comp_denominator"],
                     "permitted_homes_treated_before": r["treat_units_before"],
                     "permitted_homes_treated_after": r["treat_units_after"],
                     "permitted_homes_neither_before": r["comp_units_before"],
                     "permitted_homes_neither_after": r["comp_units_after"],
                     "estimate": r["estimate"], "low": lo, "high": hi,
                     "read": "too thin to read" if thin else "",
                     "interval": f"projects, {ab.N_DRAWS} resamples, seed {ab.SEED}",
                     "unit": "homes other than ADUs per 1,000 existing homes (2020) a year; difference-in-differences",
                     "label": "POST HOC"})
        if city not in sized:  # existing homes in each of the four areas, once per city
            sized.add(city)
            for z, h in bc.groupby("zone").homes.sum().items():
                rows.append({"contrast": "area size", "city": city, "treated_area": z, "existing_homes_treated": h,
                             "unit": "existing homes (2020)", "label": "POST HOC"})
    out = pd.DataFrame(rows)
    out.to_csv(REFERENCE / "ca_ab2097_posthoc4_local_reading.csv", index=False)
    print(out.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
