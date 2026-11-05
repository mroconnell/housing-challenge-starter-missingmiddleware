"""CA AB 2097 study: POST HOC checks asked for by the audit after the first estimate run (2026-11-05). Reported only;
they do not change the main result. Needs scripts/ca_ab2097_estimate.py --build (with the line150_main flag).

1. Unlocated permits by report year, in jurisdictions with any covered (near) land on the main map vs without:
   homes in rows with no HCD street-level point and no accepted Census point.
2. Headline (homes other than ADUs, main group, main map) with blocks and permits within 150 m of the 1/2-mile line
   left out of both near and ring.

    uv run python scripts/ca_ab2097_posthoc.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ca_ab2097_estimate as E  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import ab2097 as ab  # noqa: E402


def main() -> None:
    b = pd.read_parquet(E.CACHE / "blocks.parquet")
    p = pd.read_parquet(E.CACHE / "permits.parquet")
    covered = set(b[(b.zone_main == "near") & (b.homes > 0)].juris.dropna())
    a2 = pd.read_csv(RAW / "hcd_apr_a2" / "tablea2.csv", usecols=E.A2_COLS, low_memory=False)
    keys = set(pd.read_parquet(RAW.parent / "interim" / "ca_ab2097_geocode" / "points.parquet").query(
        "kind == 'failed_hcd'").key)
    c = E.clean_permits_full(a2)
    c["located"] = c.hcd_street | c.geo_key.isin(keys)
    c["city_has_covered_land"] = c.juris.isin(covered)
    t = c.groupby(["report_year", "city_has_covered_land"]).apply(
        lambda g: pd.Series({"homes": g.units.sum(), "homes_unlocated": g.units[~g.located].sum()}),
        include_groups=False).reset_index()
    t["share_unlocated"] = t.homes_unlocated / t.homes
    t.to_csv(REFERENCE / "ca_ab2097_posthoc_unlocated.csv", index=False)
    print(t.round(3).to_string(index=False))

    rep = ab.full_reporters(p)
    main_j = [j for j in rep if j not in E.PLACEBO | E.DROPPED]
    b2, p2 = b[~b.line150_main], p[~p.line150_main]
    g = E.group("main", E.with_treated_land(E.cells_for(b2, "main"), main_j))
    est, dr = E.event_study(g, E.cells_for(b2, "main"), E.permits_for(p2, "main"), "homes_non_adu")
    e, d = E.period_contrast(est, dr, E.BEFORE, E.AFTER)
    lo, hi = E.interval(d)
    out = pd.DataFrame([{"case": "POST HOC: headline without land within 150 m of the 1/2-mile line", "map": "main",
                         "group": "main", "outcome": "homes_non_adu", "estimate": e, "low": lo, "high": hi,
                         "unit": "homes in issued permits per 1,000 existing homes (2020) per year"}])
    out.to_csv(REFERENCE / "ca_ab2097_posthoc_line150.csv", index=False)
    print(out.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
