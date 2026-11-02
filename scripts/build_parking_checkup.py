"""Parking check-up table for the tool's Today screen (owner, 2026-11-02): parking required per new apartment in
Wisconsin cities today, against parking built in cities after they removed minimums.

    uv run python scripts/build_parking_checkup.py
Output: reference/parking_checkup_spaces.csv

Sources are the mechanism study's (docs/parking/MECHANISM_RESULTS.md, scripts/run_parking_mechanism.py):
- Wisconsin minimums: Mankato's 2025 staff comparison of 16 Wisconsin cities (spaces per home, bedroom rules at a
  50/50 mix of studio-or-one-bedroom and two-bedroom homes);
- built after repeal: project studies in Buffalo, Los Angeles, Seattle and Champaign (share of the old requirement
  that developers still built); Los Angeles's median project and Seattle's near-transit median in spaces per home.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_mechanism as mech  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

# Parking built per new home after a repeal (owner, 2026-11-02: lead with cold, Midwest and non-coastal cities).
# (place, spaces per home or None, share of the old requirement built or None, climate note, source)
BUILT = [
    ("Minneapolis", 4914 / 7925, None, "cold",
     "approved projects 2021-2023 after the 2021 repeal: 4,914 car spaces for 7,925 homes (Minneapolis Planning Commission "
     "approvals compiled by A. Schieferdecker; old rule 1 per home)"),
    ("St. Paul", 82 / 114, None, "cold", "one building, Lexington and Randolph: redesigned after the 2021 repeal from 91 homes "
     "and 88 spaces to 114 homes and 82 spaces (Minnesota Reformer, 2023-08-31); a single example"),
    ("Buffalo", 1942 / 2444 * 1.0, 1942 / 2444, "cold", "36 major developments in the first two years of the 2017 Green Code (Hess and Rehler, "
     "JAPA 2021); old residential rule 1 per home, so about 0.79 per home if homes kept the overall share (all uses)"),
    ("Los Angeles", 0.81, 151 / 224.5, "car-dependent", "median of 12 projects filed 2024-2026 (docs/parking/LA_TOC_RESULTS.md); "
     "share from transit-program projects (docs/parking/MECHANISM_RESULTS.md)"),
    ("Seattle", 0.5, 0.60, "", "386 near-transit projects 2012-2016, city data via Seattle Times (2016-12-03)"),
    ("Champaign", None, 1833 / 3975, "cold", "43 downtown and campus projects in 7 years after the 2015-16 repeal (Sohoni and Lee, JAPA 2023)"),
]
NO_RATIO = [
    ("Anchorage", "Removed minimums citywide in 2023. The city's 2026 review found no verified negative effects; developments "
     "still provide off-street parking, and one Girdwood housing project used the freedom to build fewer spaces."),
    ("Duluth", "Removed minimums citywide in December 2023 (downtown and Canal Park already had none). The city sold two "
     "downtown ramps to a housing developer to serve tenants; new buildings with under 0.5 spaces per home must file a parking plan."),
]


def main() -> None:
    rows = [dict(group="wisconsin_rule", place=k.replace(" city", "").replace(" village", ""), spaces_per_home=round(v, 3),
                 share_of_old_rule_built=np.nan, source="Mankato 2025 staff comparison of Wisconsin codes")
            for k, v in sorted(mech.MINIMUMS.items(), key=lambda kv: -kv[1])]
    for place, sp, share, climate, src in BUILT:
        rows.append(dict(group="after_repeal", place=place, spaces_per_home=round(sp, 3) if sp is not None else np.nan,
                         share_of_old_rule_built=round(share, 3) if share is not None else np.nan, source=f"{climate}|{src}"))
    for place, note in NO_RATIO:
        rows.append(dict(group="after_repeal_note", place=place, spaces_per_home=np.nan, share_of_old_rule_built=np.nan, source=note))
    pp = pd.read_csv(REFERENCE / "parking_mechanism_part_b_per_project.csv").iloc[0]
    built_share = 1 - float(np.median(list(mech.SOURCES_S.values())))
    rows.append(dict(group="summary", place="Wisconsin, homes where minimums bind (weighted)", spaces_per_home=round(pp["old_min_spaces_per_home"], 3),
                     share_of_old_rule_built=np.nan, source="parking_mechanism_part_b_per_project.csv"))
    rows.append(dict(group="summary", place="Same homes without a mandate (typical share built)", spaces_per_home=round(pp["old_min_spaces_per_home"] * built_share, 3),
                     share_of_old_rule_built=round(built_share, 3), source="median of the four project studies"))
    out = pd.DataFrame(rows)
    out.to_csv(REFERENCE / "parking_checkup_spaces.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
