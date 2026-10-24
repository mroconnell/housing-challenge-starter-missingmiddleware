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

The series never changes ``unit_category``; it adds record columns
``second_home_component``, ``second_home_units``, ``second_home_note`` and
``second_home_upper_units``. A judgment that excludes a rule hit as doubtful
(``"upper_bound": True``: a likely-false parcel-rule hit, or a record pending
evidence) keeps the units it would add in ``second_home_upper_units``, so every
table can show an "unconfirmed upper bound" beside the headline. The same
mechanism is used in every city (Madison, Pleasant Prairie, Sun Prairie).

An optional record flag ``templated_programme`` (set by the city adapter; Madison
only) marks permits from one builder programme with templated specifications;
``by_year`` and ``long_rows`` then also report the headline without it.
"""
from __future__ import annotations

import pandas as pd

HEADLINE = "second_home_sf_lot"
COMPONENTS = ("adu_detached", "adu_attached", "adu_conversion", "adu_two_unit", "second_dwelling", "sf_to_duplex")
TEXT_COMPONENTS = ("adu_detached", "adu_attached", "adu_conversion")
UPPER = f"{HEADLINE}_upper_bound"
EXCL_PROGRAMME = f"{HEADLINE}_excl_templated_programme"
PROGRAMME = f"{HEADLINE}:templated_programme"


def assign(full: pd.DataFrame, judgments: dict[str, dict] | None = None) -> pd.DataFrame:
    """Return full with second_home_component / second_home_units / second_home_note.

    `judgments`: permit_id -> {"counts": bool, "units": int, "component": str | None,
    "judgment": str, "evidence": str, "upper_bound": bool (optional)}. A judgment
    overrides the automatic assignment for that record (it is how ADU bundles held for
    review are resolved). An excluding judgment with ``upper_bound`` true keeps the
    record's would-be units (the rule's units, else ``units_if_counted``) in
    ``second_home_upper_units``.
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
    upper_extra = pd.Series(0, index=df.index, dtype=int)
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
            if j.get("upper_bound"):
                would = units[m].fillna(j.get("units_if_counted", 0)).astype(float)
                upper_extra[m] = would.astype(int).values
            comp[m], units[m] = None, pd.NA
            note[m] = ("judged_excluded_upper_bound:" if j.get("upper_bound") else "judged_excluded:") + j["judgment"]
    note[comp.notna() & note.isna()] = "rule"
    df["second_home_component"] = comp
    df["second_home_units"] = units.fillna(0).astype(int).where(comp.notna(), 0)
    df["second_home_note"] = note
    df["second_home_upper_units"] = df["second_home_units"] + upper_extra
    return df


def _upper(full: pd.DataFrame, year: int) -> pd.DataFrame:
    if "second_home_upper_units" not in full.columns:
        return full.iloc[0:0].assign(second_home_upper_units=0)
    return full[(full["year"] == year) & (full["second_home_upper_units"] > 0)]


def _programme(s: pd.DataFrame) -> pd.Series:
    return s["templated_programme"].fillna(False).astype(bool)


def by_year(full: pd.DataFrame, years) -> pd.DataFrame:
    """Wide year table: headline units and permits, units per component, the unconfirmed
    upper bound, and (if the adapter flags one) the headline without the templated programme."""
    rows = []
    has_prog = "templated_programme" in full.columns
    for y in years:
        s = full[(full["year"] == y) & full["second_home_component"].notna()]
        r = {"year": y, HEADLINE: int(s["second_home_units"].sum()), f"{HEADLINE}_permits": len(s)}
        for c in COMPONENTS:
            r[c] = int(s.loc[s["second_home_component"] == c, "second_home_units"].sum())
        u = _upper(full, y)
        r[UPPER] = int(u["second_home_upper_units"].sum()) if len(u) else r[HEADLINE]
        r[f"{UPPER}_permits"] = len(u) if len(u) else len(s)
        if has_prog:
            p = _programme(s)
            r["templated_programme_units"] = int(s.loc[p, "second_home_units"].sum())
            r["templated_programme_permits"] = int(p.sum())
            r[EXCL_PROGRAMME] = r[HEADLINE] - r["templated_programme_units"]
            r[f"{EXCL_PROGRAMME}_permits"] = len(s) - int(p.sum())
        rows.append(r)
    return pd.DataFrame(rows)


def long_rows(full: pd.DataFrame, year: int) -> list[dict]:
    """Rows for the long reference tables: the headline, one row per component, the
    unconfirmed upper bound and, if flagged, the templated programme and the headline without it."""
    s = full[(full["year"] == year) & full["second_home_component"].notna()]
    out = [{"name": HEADLINE, "permits": len(s), "units": int(s["second_home_units"].sum())}]
    for c in COMPONENTS:
        x = s[s["second_home_component"] == c]
        out.append({"name": f"{HEADLINE}:{c}", "permits": len(x), "units": int(x["second_home_units"].sum())})
    u = _upper(full, year)
    out.append({"name": UPPER, "permits": len(u) if len(u) else len(s),
                "units": int(u["second_home_upper_units"].sum()) if len(u) else out[0]["units"]})
    if "templated_programme" in full.columns:
        p = _programme(s)
        out.append({"name": PROGRAMME, "permits": int(p.sum()), "units": int(s.loc[p, "second_home_units"].sum())})
        out.append({"name": EXCL_PROGRAMME, "permits": int((~p).sum()),
                    "units": int(s.loc[~p, "second_home_units"].sum())})
    return out
