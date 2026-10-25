"""Spaghetti (ensemble) plots of ADU permitting before and after statewide laws.

The x axis is event time: year 1 is the first full year a statewide law was in
force, and years 0 and below are before it. Rates are ADU (second-home) permits
per 1,000 one-unit detached homes per year.

Two charts, both in docs/gate3/:

- adoption_spaghetti_states.png: each statewide-law state (faint), the median
  and low-high range across states, and Wisconsin's model path (statewide).
- adoption_spaghetti_cities.png: each Madison-like city in Washington, Oregon
  and Rhode Island (faint), their median, Madison's own history, and the
  model's path for Madison.

Run: uv run --with matplotlib python scripts/plot_adoption_spaghetti.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference"
DOCS = ROOT / "docs" / "gate3"
WI_HOMES = 1_839_569
MADISON_ID = "muni:5502548000"
FORECAST_START = 2027  # stylized: law in force from forecast year 1 (AQ-021)

NAMES = {"WA_inc_exSeattle": "Washington (cities excl. Seattle)", "OR_panel32_exPortland": "Oregon (32 cities excl. Portland)",
         "VT_chittenden": "Vermont (Chittenden)", "UT_mih": "Utah", "MA_statewide": "Massachusetts",
         "ME_statewide": "Maine", "RI_statewide": "Rhode Island"}
GREY, BLUE, GREEN, ORANGE, RED, PURPLE = "#4a5568", "#2b6cb0", "#2f855a", "#c05621", "#e53e3e", "#805ad5"


def _style(ax, title, xmin):
    ax.axvline(0.5, color="black", lw=0.8, alpha=0.6)
    ax.text(0.55, ax.get_ylim()[1] * 0.97, "statewide law takes effect →", fontsize=7.5, va="top")
    ax.set_xlabel("Years before (≤ 0) and after (≥ 1) the statewide law")
    ax.set_ylabel("ADU permits per 1,000 single-family homes per year")
    ax.set_xticks(range(xmin, 6))
    ax.set_xlim(xmin - 0.3, 6.6)
    ax.set_title(title, fontsize=11)
    ax.legend(fontsize=7.5, loc="upper left", frameon=False)
    ax.grid(alpha=0.25)


def states_chart() -> Path:
    annual = pd.read_csv(REF / "statewide_states_annual.csv")
    pts = pd.read_csv(REF / "pooled_adoption_points.csv")
    curve = pd.read_csv(REF / "statewide_adoption_curve.csv")
    by_year = pd.read_csv(REF / "adu_model_statewide_by_year.csv")
    k1 = pts[pts["k"] == 1].set_index("series")["year"]

    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    ax.set_ylim(0, 2.7)
    obs = curve[curve["n_states"] >= 4]  # years with 4+ states; later years shown dashed
    ax.fill_between(obs["k"], obs["min_rate"], obs["max_rate"], color=BLUE, alpha=0.12,
                    label="Low-to-high range across states (excl. California)")
    for series, g in annual[annual["series"].isin(k1.index)].groupby("series"):
        k = g["year"] - k1[series] + 1
        g = g.assign(k=k)[(k >= -5) & (k <= 5)].sort_values("k")
        ax.plot(g["k"], g["per_1000_homes"], color=GREY, alpha=0.4, lw=1.1, marker="o", ms=2.5)
        ax.annotate(NAMES.get(series, series), (g["k"].iloc[-1], g["per_1000_homes"].iloc[-1]), xytext=(4, 0),
                    textcoords="offset points", fontsize=6.5, color=GREY, va="center")
    ca = curve.dropna(subset=["ca_rate_k_from_2017_law"])
    ca_k = [-2, -1, 0] + ca["k"].tolist()
    ca_r = [0.12, 0.12, 0.12] + ca["ca_rate_k_from_2017_law"].tolist()  # 2014-2016 mean (CA_STUDY_RESULTS.md §8)
    ax.plot(ca_k, ca_r, color=ORANGE, alpha=0.55, lw=1.1, marker="o", ms=2.5)
    ax.annotate("California (2017 law)", (ca_k[-1], ca_r[-1]), xytext=(4, 0), textcoords="offset points",
                fontsize=6.5, color=ORANGE, va="center")
    ax.plot(obs["k"], obs["median_rate"], color=BLUE, lw=3.2, label="Median across states (excl. California)")
    ax.plot(curve["k"][curve["k"] >= obs["k"].max()], curve["median_rate"][curve["k"] >= obs["k"].max()],
            color=BLUE, lw=2, ls="--", alpha=0.7, label="Median, years with only 3 states")
    for path, style in (("central", dict(lw=2.4, ls="-")), ("lower", dict(lw=1.2, ls=":")), ("upper", dict(lw=1.2, ls=":"))):
        p = by_year[by_year["path"] == path]
        rate = (p["baseline_units"] + p["additional_units"]) / WI_HOMES * 1000
        ax.plot(p["year"], rate, color=GREEN, **style,
                label="Wisconsin model, central" if path == "central" else ("Wisconsin model, lower and upper" if path == "lower" else None))
    wi_now = by_year[by_year["path"] == "central"]["baseline_units"].iloc[0] / WI_HOMES * 1000
    ax.plot([-5, 0], [wi_now, wi_now], color=RED, lw=1.6, ls="-.", label=f"Wisconsin today, no law ({wi_now:.2f})")
    _style(ax, "Statewide ADU laws: each state, the median, and the Wisconsin model", -5)
    fig.text(0.01, 0.005, "Sources: reference/statewide_states_annual.csv, pooled_adoption_points.csv, statewide_adoption_curve.csv, "
             "adu_model_statewide_by_year.csv.\nState counts include ADUs built with a new house. Maine and Massachusetts have one year.",
             fontsize=6, color="#718096")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    out = DOCS / "adoption_spaghetti_states.png"
    fig.savefig(out)
    return out


def cities_chart() -> Path:
    cities = pd.read_csv(REF / "madison_like_annual.csv")
    cities = cities[cities["state"].isin(["WA", "OR", "RI"]) & cities["year_since_law"].between(-5, 5)]
    med = pd.read_csv(REF / "madison_like_median_path.csv")
    med = med[med["group"] == "WA+OR Madison-like (main)"]
    mad = pd.read_csv(REF / "madison_adu_permits_by_year.csv")
    mad = mad[(mad["category"] == "second_home_sf_lot") & mad["year"].between(2014, 2025)]
    lv = pd.read_csv(REF / "pooled_wi_y_by_area.csv").set_index("area_id").loc[MADISON_ID]
    homes = lv["homes"]

    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    ax.set_ylim(0, 2.7)
    ax.fill_between(med["year_since_law"], med["min_rate"], med["max_rate"], color=PURPLE, alpha=0.08,
                    label="Low-to-high range across those cities")
    for (state, city), g in cities.groupby(["state", "city"]):
        g = g.sort_values("year_since_law")
        ax.plot(g["year_since_law"], g["rate_per_1000"], color=GREY, alpha=0.35, lw=1, marker="o", ms=2)
        ax.annotate(f"{city}, {state}", (g["year_since_law"].iloc[-1], g["rate_per_1000"].iloc[-1]), xytext=(3, 0),
                    textcoords="offset points", fontsize=6, color=GREY, va="center")
    ax.plot(med["year_since_law"], med["median_rate"], color=PURPLE, lw=3.2,
            label="Median of Madison-like cities in WA and OR")
    k = mad["year"] - FORECAST_START + 1
    ax.plot(k, mad["units"] / homes * 1000, color=RED, lw=2, marker="o", ms=3,
            label="Madison, observed 2014–2025 (no state law; plotted as if the law took effect in 2027)")
    ys = [lv[f"y_k{i}_central"] for i in range(1, 6)]
    ax.plot(range(1, 6), ys, color=GREEN, lw=2.4, label="Model path for Madison, central")
    ax.plot([k.iloc[-1], 1], [mad["units"].iloc[-1] / homes * 1000, ys[0]], color=GREEN, lw=1, ls=":")
    _style(ax, "Madison-like cities under statewide ADU laws, and Madison", -5)
    fig.text(0.01, 0.005, "Sources: reference/madison_like_annual.csv, madison_like_median_path.csv, madison_adu_permits_by_year.csv, "
             "pooled_wi_y_by_area.csv.\nCity counts include ADUs built with a new house; Madison excludes vacant-lot ones (AQ-039).",
             fontsize=6, color="#718096")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    out = DOCS / "adoption_spaghetti_cities.png"
    fig.savefig(out)
    return out


if __name__ == "__main__":
    print(states_chart())
    print(cities_chart())
