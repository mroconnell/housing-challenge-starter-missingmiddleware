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

BUILT_SPACES_PER_HOME = {  # median project, spaces per home, where a study reports it
    "Los Angeles transit program": (0.81, "12 projects filed 2024-2026 (docs/parking/LA_TOC_RESULTS.md)"),
    "Seattle (secondary)": (0.5, "386 near-transit projects 2012-2016, city data via Seattle Times (2016-12-03)"),
}


def main() -> None:
    rows = [dict(group="wisconsin_rule", place=k.replace(" city", "").replace(" village", ""), spaces_per_home=round(v, 3),
                 share_of_old_rule_built=np.nan, source="Mankato 2025 staff comparison of Wisconsin codes")
            for k, v in sorted(mech.MINIMUMS.items(), key=lambda kv: -kv[1])]
    for k, s in mech.SOURCES_S.items():
        sp, src = BUILT_SPACES_PER_HOME.get(k, (np.nan, "project study (docs/parking/MECHANISM_RESULTS.md)"))
        rows.append(dict(group="after_repeal", place=k.replace(" (secondary)", "").replace(" transit program", ""),
                         spaces_per_home=sp, share_of_old_rule_built=round(1 - s, 3), source=src))
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
