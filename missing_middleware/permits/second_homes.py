"""Headline outcome series: second homes on single-family lots (AQ-032).

Definition (owner decision AQ-032, 2026-10-24): any legally permitted permanent
dwelling with its own kitchen added on a lot that already has a single-family
home. Components stay visible:

* ``adu_detached``, ``adu_attached``, ``adu_conversion``: text-rule ADUs that
  are counted (>= 1 unit, not a renewal duplicate). Conversions of garages,
  accessory buildings and interiors are included where they add a legal unit
  (AQ-030 keeps interior conversions tracked as their own line).
* ``adu_two_unit``: a judged ADU-text record adding two units in one building
  beside an existing house (Madison "detached duplex ADU" / "twin home ADU",
  allowed since the October 2025 Housing Forward ordinance: up to two ADUs per
  lot, duplex ADUs). Only records listed in a city's judgment table enter.
* ``second_dwelling``: ADU-equivalent (AQ-021) new dwelling on a parcel that
  already had one, not labelled ADU.
* ``sf_to_duplex``: single-family-to-duplex conversions (ADU-equivalent
  duplex conversions, Dwell-0 text conversions, and judged conversions the
  parcel match could not place).

Excluded: legalizations (no new unit is authorized), teardown-rebuilds, any
new two-unit building on a vacant or cleared lot (even if labelled ADU), and
every other record.

The series never changes ``unit_category``; it adds three record columns
(``second_home_component``, ``second_home_units``, ``second_home_note``).
"""
from __future__ import annotations

import pandas as pd

HEADLINE = "second_home_sf_lot"
COMPONENTS = ("adu_detached", "adu_attached", "adu_conversion", "adu_two_unit", "second_dwelling", "sf_to_duplex")
TEXT_COMPONENTS = ("adu_detached", "adu_attached", "adu_conversion")


def assign(full: pd.DataFrame, judgments: dict[str, dict] | None = None) -> pd.DataFrame:
    """Return full with second_home_component / second_home_units / second_home_note.

    `judgments`: permit_id -> {"counts": bool, "units": int, "component": str | None,
    "judgment": str, "evidence": str}. A judgment overrides the automatic
    assignment for that record (it is how ADU bundles held for review are resolved).
    """
    judgments = judgments or {}
    df = full.copy()
    comp = pd.Series(None, index=df.index, dtype=object)
    note = pd.Series(None, index=df.index, dtype=object)
    counted = df["counted"].astype(bool)
    cat = df["unit_category"]
    for c in TEXT_COMPONENTS:
        comp[counted & cat.eq(c)] = c
    note[counted & cat.eq("adu_legalization")] = "excluded:legalization"
    eq = counted & cat.eq("adu_equivalent")
    series = df["adu_eq_series"] if "adu_eq_series" in df.columns else pd.Series(None, index=df.index)
    comp[eq & series.eq("second_dwelling")] = "second_dwelling"
    comp[eq & series.eq("duplex_conversion")] = "sf_to_duplex"
    units = df["units_added"].where(comp.notna()).astype("Float64")
    pid = df["permit_id"]
    for p, j in judgments.items():
        m = pid.eq(p)
        if not m.any():
            continue
        if j.get("counts"):
            c = j["component"]
            if c not in COMPONENTS:
                raise ValueError(f"{p}: unknown second-home component {c!r}")
            comp[m], units[m] = c, float(j["units"])
            note[m] = "judged:" + j["judgment"]
        else:
            comp[m], units[m] = None, pd.NA
            note[m] = "judged_excluded:" + j["judgment"]
    note[comp.notna() & note.isna()] = "rule"
    df["second_home_component"] = comp
    df["second_home_units"] = units.fillna(0).astype(int).where(comp.notna(), 0)
    df["second_home_note"] = note
    return df


def by_year(full: pd.DataFrame, years) -> pd.DataFrame:
    """Wide year table: headline units and permits, then units per component."""
    rows = []
    for y in years:
        s = full[(full["year"] == y) & full["second_home_component"].notna()]
        r = {"year": y, HEADLINE: int(s["second_home_units"].sum()), f"{HEADLINE}_permits": len(s)}
        for c in COMPONENTS:
            r[c] = int(s.loc[s["second_home_component"] == c, "second_home_units"].sum())
        rows.append(r)
    return pd.DataFrame(rows)


def long_rows(full: pd.DataFrame, year: int) -> list[dict]:
    """Rows for the long reference tables: the headline, then one row per component."""
    s = full[(full["year"] == year) & full["second_home_component"].notna()]
    out = [{"name": HEADLINE, "permits": len(s), "units": int(s["second_home_units"].sum())}]
    for c in COMPONENTS:
        x = s[s["second_home_component"] == c]
        out.append({"name": f"{HEADLINE}:{c}", "permits": len(x), "units": int(x["second_home_units"].sum())})
    return out
