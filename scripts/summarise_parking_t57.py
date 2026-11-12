"""Test 57 summary (CAUSAL_FRAMEWORK_PLAN.md, Test 57 LOCK): reads the panels made by build_parking_t57_ny_panel.py and
build_parking_t57_sf_panel.py and applies parking_t57_common.

    uv run python scripts/summarise_parking_t57.py --first   # step 1: cells and before-window jobs per arm, too-few, MDE
    uv run python scripts/summarise_parking_t57.py --all     # every cell and the reading (after step 1 is reported)
    ... [--panels DIR] [--out DIR] [--tag TAG]               # other folders (synthetic smoke tests); default
                                                             # data/processed/t57 -> reference/

--first computes no treated-vs-control effect: only cell parts, clusters, before-window jobs and acres per arm, the
too-few flag, and the MDE (2.486 x the SD of the main effect's bootstrap draws; no centre or percentile is computed).
Writes parking_t57_counts.csv, parking_t57_mde.csv and parking_t57_hpd_placement.csv (HPD not-placed share by
year, whole city, not split by arm; audit code rulings 06:28 UTC).
--all writes parking_t57_cells.csv (exactly parking_t57_common.N_CELLS rows, asserted), parking_t57_reading.csv (the
lock's rules applied mechanically, with the diluted-outcome, balance and bundling labels beside each run). Event-study
rows are cells. The only headline cell is NY 2016, all DOB new-building units (ny_dob:main).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import parking_t57_common as C  # noqa: E402

PANELS, OUT = ROOT / "data/processed/t57", ROOT / "reference"
BALANCE_CSV = ROOT / "reference/parking_t57_nyc_tz_check.csv"


def load(panels: Path, key: str) -> pd.DataFrame:
    p = pd.read_csv(panels / f"panel_{key}.csv")
    assert set(p.columns) >= {"cluster", "arm", "year", "units", "jobs", "acres"}, key
    assert set(p.arm.unique()) <= {"T", "C"}, key
    return p


def balance_label() -> str:
    """The pre-period imbalance across the NY line (levels in 2016, 50-400 m bands), from the committed check table."""
    if not BALANCE_CSV.exists():
        return "balance table missing"
    b = pd.read_csv(BALANCE_CSV)
    b = b[b.section == "balance"]
    v = lambda item, arm: float(b[(b["item"] == item) & b["arm"].str.startswith(arm)]["value"].iloc[0])  # noqa: E731
    return ("pre-period imbalance (MapPLUTO 16v1, lots in the 50-400 m bands; levels, not trends): homes per lot acre "
            f"{v('existing units per lot acre', 'inside'):.1f} inside vs {v('existing units per lot acre', 'outside'):.1f} outside; "
            f"R6-R10 share of lot area {v('zoning mix: R6-R10 (higher density residence)', 'inside'):.1%} vs "
            f"{v('zoning mix: R6-R10 (higher density residence)', 'outside'):.1%}; manufacturing "
            f"{v('zoning mix: M (manufacturing)', 'inside'):.1%} vs {v('zoning mix: M (manufacturing)', 'outside'):.1%}; median "
            f"year built {v('median year built (lots with units, unit-weighted)', 'inside'):.0f} vs "
            f"{v('median year built (lots with units, unit-weighted)', 'outside'):.0f}; lot size balanced "
            "(table includes outside lots in Manhattan CDs 101-108, which the panels leave out). The leads are the "
            "pre-trend check")


def first(panels: Path, out: Path, tag: str) -> None:
    cnt = pd.DataFrame([C.counts(r, load(panels, k)) for k, r in C.RUNS.items()])
    cnt.to_csv(out / f"parking_t57_counts{tag}.csv", index=False)
    mde = pd.DataFrame([C.mde(r, load(panels, k)) for k, r in C.RUNS.items()])
    mde.to_csv(out / f"parking_t57_mde{tag}.csv", index=False)
    pd.set_option("display.width", 250)
    print(cnt.drop(columns=["rule", "outcome"]).to_string(index=False))
    print(mde[["run", "bootstrap_sd", "mde", "draws_used", "unit"]].to_string(index=False))
    hp = hpd_placement(panels)
    hp.to_csv(out / f"parking_t57_hpd_placement{tag}.csv", index=False)
    print(hp.to_string(index=False))


def hpd_placement(panels: Path) -> pd.DataFrame:
    """HPD new-construction buildings not placed on a lot, by project start year, whole city (not split by arm)."""
    f = panels / "hpd_placement_by_year.csv"
    assert f.exists(), f"{f} missing: run build_parking_t57_ny_panel.py"
    h = pd.read_csv(f)
    assert set(h.columns) == {"year", "records", "not_placed", "not_placed_share"} and h.year.is_unique
    h["scope"] = "whole city, not split by arm; HPD new construction with >= 1 income-restricted unit, by project start year"
    return h


def all_cells(panels: Path, out: Path, tag: str) -> None:
    cnt, mde = pd.read_csv(out / f"parking_t57_counts{tag}.csv"), pd.read_csv(out / f"parking_t57_mde{tag}.csv")
    rows = []
    for k, r in C.RUNS.items():
        rows += C.cells(r, load(panels, k), C.FIRST_YEAR[r.city])
    cells = pd.DataFrame(rows)
    assert len(cells) == C.N_CELLS == 95, (len(cells), C.N_CELLS)
    assert cells["cell"].is_unique and int(cells["headline"].sum()) == 1
    bal = balance_label()
    cells["balance"] = [bal if c == "New York" else "" for c in cells["city"]]
    cells["too_few_to_read"] = cells["run"].map(cnt.set_index("run")["too_few_to_read"])
    cells.to_csv(out / f"parking_t57_cells{tag}.csv", index=False)
    rd = C.reading(cells, cnt, mde)
    rd["balance"] = [bal if c == "New York" else "" for c in rd["city"]]
    chance = rd.attrs["chance"]
    rd = pd.concat([rd, pd.DataFrame([dict(run="(all)", reading=chance)])], ignore_index=True)
    rd.to_csv(out / f"parking_t57_reading{tag}.csv", index=False)
    pd.set_option("display.width", 250)
    print(rd[["run", "role", "too_few_to_read", "leads_excluding_0", "placebo_dates_excluding_0", "main_excludes_0",
              "reading"]].to_string(index=False))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--first", action="store_true", help="counts, too-few flags and MDE only (no effect)")
    g.add_argument("--all", action="store_true", help="every cell and the reading")
    ap.add_argument("--panels", default=str(PANELS))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--tag", default="", help="suffix for output names (e.g. _synthetic)")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (first if a.first else all_cells)(Path(a.panels), out, a.tag)


if __name__ == "__main__":
    main()
