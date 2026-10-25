"""Spaghetti plot of ADU adoption after statewide laws.

Faint lines: each statewide-law state's observed rate by year after its law
(reference/pooled_adoption_points.csv; California from
reference/statewide_adoption_curve.csv, counted from its 2017 law).
Bold line and band: the median and low-high range across the non-California
states (reference/statewide_adoption_curve.csv), the adoption reference line.
Also drawn: the model's typical-state path, the Madison-like cities' median
(reference/madison_like_median_path.csv) and Madison today.

Rates are ADU (second-home) permits per 1,000 one-unit detached homes per year.

Run: uv run --with matplotlib python scripts/plot_adoption_spaghetti.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference"
OUT = ROOT / "docs" / "gate3" / "adoption_spaghetti.png"

NAMES = {"WA": "Washington", "OR": "Oregon (outside Portland)", "VT": "Vermont (Chittenden)",
         "UT": "Utah", "MA": "Massachusetts", "ME": "Maine", "RI": "Rhode Island"}


def main() -> None:
    pts = pd.read_csv(REF / "pooled_adoption_points.csv")
    curve = pd.read_csv(REF / "statewide_adoption_curve.csv")
    ml = pd.read_csv(REF / "madison_like_median_path.csv")
    ml = ml[ml["group"] == "WA+OR Madison-like (main)"]
    params = json.loads((REF / "adu_model_params.json").read_text())
    ramp = params["paths"]["central"]["ramp"]
    madison = pd.read_csv(REF / "wi_baseline_observed.csv").set_index("key").loc["madison_2022_2025", "rate_per_1000_yr"]

    fig, ax = plt.subplots(figsize=(9, 5.6), dpi=150)
    ax.fill_between(curve["k"], curve["min_rate"], curve["max_rate"], color="#2b6cb0", alpha=0.12,
                    label="Range across those states (low to high)")
    for st, g in pts.groupby("cluster"):
        g = g.sort_values("k")
        ax.plot(g["k"], g["rate"], color="#4a5568", alpha=0.35, lw=1.2, marker="o", ms=3)
        ax.annotate(NAMES.get(st, st), (g["k"].iloc[-1], g["rate"].iloc[-1]), xytext=(4, 0),
                    textcoords="offset points", fontsize=7, color="#4a5568", va="center")
    ca = curve.dropna(subset=["ca_rate_k_from_2017_law"])
    ax.plot(ca["k"], ca["ca_rate_k_from_2017_law"], color="#c05621", alpha=0.5, lw=1.2, marker="o", ms=3)
    ax.annotate("California (from 2017 law)", (ca["k"].iloc[-1], ca["ca_rate_k_from_2017_law"].iloc[-1]),
                xytext=(4, 0), textcoords="offset points", fontsize=7, color="#c05621", va="center")
    ax.plot(curve["k"], curve["median_rate"], color="#2b6cb0", lw=3.2,
            label="Median of statewide-law states (excl. California)")
    ax.plot(range(1, 6), [1.30 * r for r in ramp], color="#2f855a", lw=2, ls="--",
            label="Model: typical statewide-law state (1.30 once ramped)")
    ax.plot(ml["year_since_law"], ml["median_rate"], color="#805ad5", lw=2, ls=":", marker="s", ms=4,
            label="Madison-like cities in WA and OR (median)")
    ax.axhline(madison, color="#e53e3e", lw=1.2, ls="-.", label=f"Madison today ({madison:.2f})")
    ax.set_xlabel("Year after the statewide law took effect")
    ax.set_ylabel("ADU permits per 1,000 single-family homes per year")
    ax.set_xticks(range(1, 6))
    ax.set_xlim(0.8, 6.2)
    ax.set_ylim(0, None)
    ax.set_title("ADU permitting after statewide laws: each state, the median and the model", fontsize=11)
    ax.legend(fontsize=7.5, loc="upper left", frameon=False)
    ax.grid(alpha=0.25)
    fig.text(0.01, 0.005, "Sources: reference/pooled_adoption_points.csv, statewide_adoption_curve.csv, "
             "madison_like_median_path.csv, adu_model_params.json. Counts include ADUs built with a new house.",
             fontsize=6, color="#718096")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
