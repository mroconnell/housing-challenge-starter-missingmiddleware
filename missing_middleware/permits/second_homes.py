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
* ``adu_teardown_rebuild`` (owner decision AQ-039, 2026-10-25): an ADU permitted
  together with a new principal house on a lot whose earlier home was razed. One
  net added home, so the ADU unit counts (1 per ADU); the replacement house never
  counts. See `new_house_adus`.

Excluded: legalizations (no new unit is authorized), teardown-rebuild replacement
houses, an ADU permitted with a new house on a previously vacant lot (AQ-039;
kept as the diagnostic ``vacant_lot_new_house_adu`` with its ADU units by year so
the rule can be flipped later), any new two-unit building without ADU wording on
a vacant or cleared lot, and every other record.

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

import re

import pandas as pd

HEADLINE = "second_home_sf_lot"
COMPONENTS = ("adu_detached", "adu_attached", "adu_conversion", "adu_two_unit", "second_dwelling", "sf_to_duplex",
              "adu_teardown_rebuild")
TEXT_COMPONENTS = ("adu_detached", "adu_attached", "adu_conversion")
UPPER = f"{HEADLINE}_upper_bound"
EXCL_PROGRAMME = f"{HEADLINE}_excl_templated_programme"
PROGRAMME = f"{HEADLINE}:templated_programme"
TEARDOWN = "adu_teardown_rebuild"
VACANT = "vacant_lot_new_house_adu"  # diagnostic (AQ-039): excluded from the headline, units kept
VACANT_ROW = f"second_home_diag:{VACANT}"
NEW_HOUSE_WINDOW_DAYS = 365   # an ADU permit this close to a new-house permit on the lot is "with" it
RAZE_BEFORE_DAYS = 1095       # dwelling raze from 3 years before the new-house permit ...
RAZE_AFTER_DAYS = 1095        # ... to 3 years after (owners often raze after moving in)

# a description whose subject is a new principal dwelling ("NEW SINGLE FAMILY HOME", "NEW DUPLEX W/ ADU",
# "MAIN HOUSE"); used for the house of a new-house + ADU project
NEW_HOUSE_RE = re.compile(
    r"\bnew\b.{0,30}?\b(?:single[- ]?family|SFR|SFD|NSFR|home|house|residence|dwelling|duplex|two[- ]family)\b"
    r"|\bNSFR\b|\bmain\s+house\b|\bprincipal\s+(?:house|dwelling|residence)\b", re.I)


def new_house_adus(df: pd.DataFrame, *, key: pd.Series, adu: pd.Series, new_house: pd.Series,
                   dwelling_raze: pd.Series, bundle: pd.Series | None = None,
                   house_replaces_home: pd.Series | None = None,
                   window_days: int = NEW_HOUSE_WINDOW_DAYS, raze_before_days: int = RAZE_BEFORE_DAYS,
                   raze_after_days: int = RAZE_AFTER_DAYS) -> pd.DataFrame:
    """ADUs permitted together with a new principal house, split by the lot's prior state (AQ-039).

    `df` needs permit_id, issue_date, units_added. All masks are aligned to `df`:
    `key` lot key (parcel number), `adu` unit-adding records with ADU wording, `new_house` new
    principal-dwelling records (not ADU-worded), `dwelling_raze` raze/demolition of a dwelling
    (or a teardown signal), `bundle` ADU records that are the new house and the ADU in one permit,
    `house_replaces_home` new-house records already judged to replace a home (teardown text).

    Candidates: (a) a bundle record; (b) a separate ADU record on a lot with a new-house record
    issued within `window_days` (either order). The lot previously had a home if a dwelling raze on
    the lot falls from `raze_before_days` before to `raze_after_days` after the house permit, or the
    house record replaces a home. Teardown -> site "teardown_rebuild", else "vacant_lot".
    ADU units: a bundle adds its units minus the principal house (at least 1); a separate ADU
    record adds its own units. Returns one row per candidate (index = df index): nh_site,
    nh_adu_units, nh_house_permit, nh_evidence.
    """
    bundle = pd.Series(False, index=df.index) if bundle is None else bundle.fillna(False).astype(bool)
    hr = pd.Series(False, index=df.index) if house_replaces_home is None else house_replaces_home.fillna(False)
    have = key.notna()
    houses = df[new_house.fillna(False).astype(bool) & ~adu & have].assign(_k=key)
    razes = df[dwelling_raze.fillna(False).astype(bool) & have].assign(_k=key)
    h_by = {k: g for k, g in houses.groupby("_k")}
    r_by = {k: g for k, g in razes.groupby("_k")}
    rows = {}
    for idx in df.index[adu.fillna(False).astype(bool) & have]:
        r, k = df.loc[idx], key.at[idx]
        ua = int(r["units_added"]) if pd.notna(r["units_added"]) else 0
        if ua <= 0:
            continue
        if bundle.at[idx]:
            hdate, hid, units, hrep = r["issue_date"], r["permit_id"], max(1, ua - 1), bool(hr.at[idx])
        else:
            h = h_by.get(k)
            if h is None:
                continue
            gap = (h["issue_date"] - r["issue_date"]).dt.days.abs()
            h = h[gap <= window_days]
            if not len(h):
                continue
            hh = h.loc[(h["issue_date"] - r["issue_date"]).dt.days.abs().idxmin()]
            hdate, hid, units, hrep = hh["issue_date"], hh["permit_id"], ua, bool(hr.loc[h.index].any())
        z = r_by.get(k)
        hit = pd.DataFrame()
        if z is not None:
            d = (z["issue_date"] - hdate).dt.days
            hit = z[(d >= -raze_before_days) & (d <= raze_after_days)]
        if len(hit):
            zz = hit.iloc[0]
            site, ev = "teardown_rebuild", f"dwelling raze {zz['permit_id']} ({zz['issue_date'].date()})"
        elif hrep:
            site, ev = "teardown_rebuild", "house record replaces an earlier home (teardown wording)"
        else:
            site, ev = "vacant_lot", "no dwelling raze on the lot within the window"
        how = "same permit as the new house" if bundle.at[idx] else f"with new house {hid}"
        rows[idx] = {"nh_site": site, "nh_adu_units": int(units), "nh_house_permit": hid,
                     "nh_evidence": f"{how}; {ev}"}
    return pd.DataFrame.from_dict(rows, orient="index",
                                  columns=["nh_site", "nh_adu_units", "nh_house_permit", "nh_evidence"])


def assign(full: pd.DataFrame, judgments: dict[str, dict] | None = None,
           new_house: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return full with second_home_component / second_home_units / second_home_note.

    `new_house`: output of `new_house_adus` (AQ-039). A counted candidate on a teardown lot gets
    component ``adu_teardown_rebuild`` with its ADU units; one on a previously vacant lot is taken
    out of the headline and its ADU units go to ``second_home_vacant_lot_units`` (diagnostic).

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
    vacant = pd.Series(0, index=df.index, dtype=int)
    if new_house is not None and len(new_house):
        nh = new_house[new_house.index.isin(df.index)]
        nh = nh[counted.loc[nh.index]]
        td = nh.index[nh["nh_site"] == "teardown_rebuild"]
        comp[td], units[td] = TEARDOWN, nh.loc[td, "nh_adu_units"].astype(float).values
        note[td] = "rule:teardown_rebuild_adu:" + nh.loc[td, "nh_evidence"]
        va = nh.index[nh["nh_site"] == "vacant_lot"]
        comp[va], units[va] = None, pd.NA
        vacant[va] = nh.loc[va, "nh_adu_units"].astype(int).values
        note[va] = "excluded:vacant_lot_new_house_adu:" + nh.loc[va, "nh_evidence"]
    for p, j in judgments.items():
        m = pid.eq(p)
        if not m.any():
            continue
        vacant[m] = int(j.get("vacant_lot_units", 0))
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
    df["second_home_vacant_lot_units"] = vacant
    return df


def _upper(full: pd.DataFrame, year: int) -> pd.DataFrame:
    if "second_home_upper_units" not in full.columns:
        return full.iloc[0:0].assign(second_home_upper_units=0)
    return full[(full["year"] == year) & (full["second_home_upper_units"] > 0)]


def _vacant(full: pd.DataFrame, year: int) -> pd.DataFrame:
    if "second_home_vacant_lot_units" not in full.columns:
        return full.iloc[0:0].assign(second_home_vacant_lot_units=0)
    return full[(full["year"] == year) & (full["second_home_vacant_lot_units"] > 0)]


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
        v = _vacant(full, y)
        r[f"diag_{VACANT}_units"], r[f"diag_{VACANT}_permits"] = int(v["second_home_vacant_lot_units"].sum()), len(v)
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
    v = _vacant(full, year)
    out.append({"name": VACANT_ROW, "permits": len(v), "units": int(v["second_home_vacant_lot_units"].sum())})
    if "templated_programme" in full.columns:
        p = _programme(s)
        out.append({"name": PROGRAMME, "permits": int(p.sum()), "units": int(s.loc[p, "second_home_units"].sum())})
        out.append({"name": EXCL_PROGRAMME, "permits": int((~p).sum()),
                    "units": int(s.loc[~p, "second_home_units"].sum())})
    return out
