"""Tornado chart of the sensitivity cases (AQ-042, AQ-043): one horizontal bar per case, showing its
central minus the adopted central, in additional second-home permits over 2027-2031, sorted by size.

Input: reference/adu_model_sensitivities.csv (scripts/run_adu_model.py).
Output: docs/gate3/sensitivity_tornado.png.
Run: uv run --with matplotlib python scripts/plot_sensitivity_tornado.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SHORT = {   # csv `change` prefix -> short bar label
    "Madison at its pooled level": "Madison at its pooled level",
    "California out of the common level": "California out of the common level",
    "LA-calibrated multifamily correction": "LA-calibrated multifamily correction",
    "no ramp": "No ramp (full rate from 2027)",
    "rural and small-community places at the Madison floor": "Rural and small places at the Madison floor",
    "eligible-property basis": "Eligible-property basis (no one-unit attached)",
    "multiplicative": "Multiplicative law",
    "California-only market regression": "California-only market regression",
    "no reporting-share correction": "No reporting-share correction",
    "reporting-share correction for Maine": "Reporting-share correction without Utah",
    "Washington's law years": "Washington from enactment",
    "Vermont 2024 dropped": "Vermont 2024 dropped",
    "Vermont dropped": "Vermont dropped",
    "all three AQ-061": "Comparison states as at Gate 4",
}


def label(change: str) -> str:
    return next((v for k, v in SHORT.items() if change.startswith(k)), change)


def main() -> Path:
    s = pd.read_csv(ROOT / "reference/adu_model_sensitivities.csv")
    central = float(s.loc[s["change"].str.startswith("adopted"), "central_additional_5yr"].iloc[0])
    # cases that change the statewide addition's central (the 10th-percentile lower changes only the lower; the
    # baseline-only cases are in reference/adu_model_baseline_only_effects.csv)
    keep = s["moves"].eq("statewide addition") if "moves" in s else ~s["change"].str.startswith("adopted")
    s = s[keep & (s["central_additional_5yr"] - central).abs().gt(0.05)].copy()
    s["delta"] = s["central_additional_5yr"] - central
    s = s.reindex(s["delta"].abs().sort_values().index)
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=150)
    colors = ["#2b6cb0" if d > 0 else "#c05621" for d in s["delta"]]
    ax.barh([label(c) for c in s["change"]], s["delta"], color=colors)
    for y, (d, v) in enumerate(zip(s["delta"], s["central_additional_5yr"])):
        ax.text(d + (60 if d >= 0 else -60), y, f"{d:+,.0f}  (central {v:,.0f})", va="center",
                ha="left" if d >= 0 else "right", fontsize=8)
    ax.axvline(0, color="black", lw=0.8)
    lo = min(s["delta"].min(), 0)
    ax.set_xlim(lo * 1.45, max(s["delta"].max(), 0) * 1.3 + 3200)
    ax.set_xlabel("Change from the adopted central, additional second-home permits over 2027–2031")
    ax.set_title(f"Sensitivity cases: change from the central of {central:,.0f} additional permits (2027–2031)", fontsize=11)
    ax.grid(axis="x", alpha=0.25)
    fig.text(0.01, 0.01, "Source: reference/adu_model_sensitivities.csv. Each case changes one assumption; the eligible-property case "
             "has its own 636-permit baseline.", fontsize=6.5, color="#718096")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    out = ROOT / "docs/gate3/sensitivity_tornado.png"
    fig.savefig(out)
    return out


if __name__ == "__main__":
    print(main())
