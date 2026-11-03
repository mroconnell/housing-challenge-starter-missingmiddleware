"""Charts for the exploratory NLCD hard-surface pilot (Buffalo vs Rochester, New York).

Reads reference/nlcd_pilot_buffalo_rochester.csv (from scripts/run_nlcd_paved_pilot.py) and writes
docs/parking/nlcd_pilot_buffalo_rochester.png with three panels:
1. New hard surface other than roads (acres per year), per 1,000 land acres so the two cities compare.
2. New road surface (acres per year), per 1,000 land acres.
3. New hard surface other than roads per home permitted the year before (square feet per home), 2006 onward.
The dashed line marks 2017, Buffalo's first year with no parking minimums.

Run: uv run --all-extras --with matplotlib python scripts/plot_nlcd_pilot.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "reference" / "nlcd_pilot_buffalo_rochester.csv"
OUT = ROOT / "docs" / "parking" / "nlcd_pilot_buffalo_rochester.png"
COLORS = {"Buffalo": "#1f5fa8", "Rochester": "#c2571a"}


def main() -> Path:
    d = pd.read_csv(SRC)
    fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=True)
    for city, g in d.groupby("city"):
        per = 1000 / g["land_acres"]
        axes[0].plot(g["year"], g["new_other_hard_acres_per_year"] * per, marker="o", ms=3, label=city,
                     color=COLORS.get(city))
        axes[1].plot(g["year"], g["new_road_hard_acres_per_year"] * per, marker="o", ms=3, label=city,
                     color=COLORS.get(city))
        col = "new_other_hard_sqft_per_home_prev_year_permits"
        if col in g:
            axes[2].plot(g["year"], g[col], marker="o", ms=3, label=city, color=COLORS.get(city))
    axes[0].set_ylabel("acres per year\nper 1,000 land acres")
    axes[0].set_title("New hard surface other than roads (roofs, lots, driveways)")
    axes[1].set_ylabel("acres per year\nper 1,000 land acres")
    axes[1].set_title("New road surface")
    axes[2].set_ylabel("square feet per home")
    axes[2].set_title("New non-road hard surface per home permitted the year before")
    for ax in axes:
        ax.axhline(0, color="#888", lw=0.8)
        ax.axvline(2017, color="#444", ls="--", lw=1)
        ax.grid(alpha=0.3)
    axes[0].legend(frameon=False)
    axes[2].set_xlabel("year (satellite map year)")
    fig.text(0.01, 0.005, "Source: USGS Annual NLCD Collection 1.1 (CC0); Census Building Permits Survey. "
             "Dashed line: 2017, Buffalo repeal. Exploratory, not a test.", fontsize=7)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150)
    return OUT


if __name__ == "__main__":
    print(main())
    sys.exit(0)
