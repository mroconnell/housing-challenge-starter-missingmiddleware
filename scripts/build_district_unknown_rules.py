"""Assembly and Senate district figures for the three unknown-rules assumptions (owner request 2026-11-11).

Same allocation as scripts/build_district_allocation.py: district value = sum over areas of the area's block-weighted
share in the district (reference/adu_model_district_crosswalk.csv) x the area's value, for every path and year, plus
an explicit "unallocated" row (state total minus the districts). Area values come from the variant engine run
(data/processed/model_run/unknown_rules/results_long.parquet). The adopted assumption (like_restricted) must reproduce
reference/adu_model_by_assembly_district.csv and _by_senate_district.csv; the script stops if it does not.

Run: uv run python scripts/build_district_unknown_rules.py
Outputs: reference/adu_model_unknown_rules_by_assembly_district.csv, reference/adu_model_unknown_rules_by_senate_district.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from missing_middleware.paths import PROCESSED, REFERENCE  # noqa: E402

YEAR0 = 2026


def allocate(res: pd.DataFrame, cw: pd.DataFrame, col: str, level: str, label: str) -> pd.DataFrame:
    sh = cw.groupby(["area_id", col], as_index=False)["share"].sum()
    homes = cw.groupby(col)["homes_allocated"].sum()
    m = res.merge(sh, on="area_id", how="inner")
    for c in ("baseline_units", "additional_units"):
        m[c] = m[c] * m["share"]
    d = m.groupby([col, "path", "year"], as_index=False)[["baseline_units", "additional_units"]].sum()
    st = res.groupby(["path", "year"], as_index=False)[["baseline_units", "additional_units"]].sum()
    tot = d.groupby(["path", "year"], as_index=False)[["baseline_units", "additional_units"]].sum()
    un = st.merge(tot, on=["path", "year"], suffixes=("", "_d"))
    un = un.assign(baseline_units=un.baseline_units - un.baseline_units_d, additional_units=un.additional_units - un.additional_units_d)
    un[col] = "unallocated"
    d = pd.concat([d, un[[col, "path", "year", "baseline_units", "additional_units"]]], ignore_index=True)
    d["forecast_year"] = (d["year"] + YEAR0).astype(str)
    five = d.groupby([col, "path"], as_index=False)[["baseline_units", "additional_units"]].sum().assign(forecast_year="2027-2031")
    d = pd.concat([d.drop(columns="year"), five], ignore_index=True)
    d = d.rename(columns={col: "district"})
    d["district"] = d["district"].astype(str)
    d["level"] = level
    d["district_label"] = d["district"].map(lambda x: "Not allocated to a district" if x == "unallocated" else f"{label} District {x}")
    d["homes"] = d["district"].map(lambda x: float(homes.get(x, homes.get(int(x), 0.0))) if x != "unallocated" else 0.0)
    return d


def main():
    res = pd.read_parquet(PROCESSED / "model_run/unknown_rules/results_long.parquet")
    cw = pd.read_csv(REFERENCE / "adu_model_district_crosswalk.csv", dtype={"assembly_district": str, "senate_district": str})
    out = []
    for level, col, label, adopted_file in (("assembly", "assembly_district", "Assembly", "adu_model_by_assembly_district.csv"),
                                            ("senate", "senate_district", "Senate", "adu_model_by_senate_district.csv")):
        parts = []
        for v, g in res.groupby("unknown_treatment"):
            parts.append(allocate(g, cw, col, level, label).assign(unknown_treatment=v))
        d = pd.concat(parts, ignore_index=True)
        ad = pd.read_csv(REFERENCE / adopted_file, dtype={"district": str})
        chk = d[d.unknown_treatment.eq("like_restricted")].merge(ad, on=["district", "path", "forecast_year"], suffixes=("", "_a"))
        gap = max((chk.additional_units - chk.additional_units_a).abs().max(), (chk.baseline_units - chk.baseline_units_a).abs().max())
        if len(chk) != len(ad) or gap > 0.01:
            raise SystemExit(f"{level}: adopted assumption does not reproduce {adopted_file} (rows {len(chk)} vs {len(ad)}, gap {gap})")
        print(f"ok  {level}: like_restricted reproduces {adopted_file} (largest gap {gap:.4f} permits)")
        st = res.groupby(["unknown_treatment", "path"])[["additional_units"]].sum()
        sums = d[d.forecast_year.eq("2027-2031")].groupby(["unknown_treatment", "path"])[["additional_units"]].sum()
        print(f"ok  {level}: districts plus unallocated equal the state, largest gap {(sums - st).abs().max().iloc[0]:.4f}")
        cols = ["unknown_treatment", "level", "district", "district_label", "path", "forecast_year", "homes", "baseline_units", "additional_units"]
        d[cols].round(4).to_csv(REFERENCE / f"adu_model_unknown_rules_by_{level}_district.csv", index=False)
        out.append(d)


if __name__ == "__main__":
    main()
