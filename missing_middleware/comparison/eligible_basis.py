"""Eligible-property basis for the pooled model (owner reframing 2026-10-25; docs/gate3/ELIGIBLE_BASIS.md).

Question: "How many new ADU permits per 1,000 eligible properties result from a statewide
benchmark ADU law?"

- Numerator = permits, flattened to at most 1 per parcel per year (distinct APN / parcel id, or
  normalised site address where there is no parcel id) in every source with ids.
- Denominator = properties eligible under the place's actual ADU law: one-unit detached homes
  (ACS B25024_002) plus, where the law reaches them, one-unit attached homes (003), multifamily
  buildings (004-009 converted from housing units to buildings with stated units-per-building
  assumptions) and mobile homes (010). Buildings stand in for parcels.

Pure functions of data frames; tests run offline on fixtures.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# ACS B25024 components (housing units by units in structure)
# ---------------------------------------------------------------------------
COMPONENTS = {   # component -> B25024 estimate column
    "sf_det": "B25024_E002", "sf_att": "B25024_E003", "mf2": "B25024_E004", "mf3_4": "B25024_E005",
    "mf5_9": "B25024_E006", "mf10_19": "B25024_E007", "mf20_49": "B25024_E008", "mf50p": "B25024_E009",
    "mobile": "B25024_E010",
}
MF = ("mf2", "mf3_4", "mf5_9", "mf10_19", "mf20_49", "mf50p")

# Units per building (housing units in the band / buildings). The owner (2026-10-25) asked to lean
# toward large sizes for the central: the law adds at most a few ADUs to a property however big
# the complex, so a complex should count as few properties. "small" = bottom of each band (most
# properties), "mid" = band midpoints, "large" = top of each band (central), "very_large" = top
# of band and a 1.25 buildings-per-parcel complex factor on 5+ bands (fewest properties).
SIZES = {
    "small": {"mf2": 2, "mf3_4": 3, "mf5_9": 5, "mf10_19": 10, "mf20_49": 20, "mf50p": 50},
    "mid": {"mf2": 2, "mf3_4": 3.5, "mf5_9": 7, "mf10_19": 14.5, "mf20_49": 34.5, "mf50p": 100},
    "large": {"mf2": 2, "mf3_4": 4, "mf5_9": 9, "mf10_19": 19, "mf20_49": 49, "mf50p": 150},
    "very_large": {"mf2": 2, "mf3_4": 4, "mf5_9": 9 * 1.25, "mf10_19": 19 * 1.25, "mf20_49": 49 * 1.25,
                   "mf50p": 150 * 1.25},
}
CENTRAL_SIZE = "large"

# Law scope: share of each component's properties that is eligible (1 = all, 0.5 = about half,
# e.g. Maine's 3-unit structures inside the 3-4 band). Mobile homes are 0 in every central (most
# sit in parks or on leased spaces, not on their own lot) and 1 in the high where the law covers
# single-family dwellings without the word "detached".
_SF = {"sf_det": 1.0}
_SF1 = {"sf_det": 1.0, "sf_att": 1.0}
_ALL_MF = {c: 1.0 for c in MF}
LAW_SCOPE = {
    # key -> (low, central, high, legal basis, legal status)
    "CA": (
        {**_SF1, **_ALL_MF}, {**_SF1, **_ALL_MF}, {**_SF1, **_ALL_MF, "mobile": 1.0},
        "Gov. Code 66314 (lot with a proposed or existing single-family or multifamily dwelling) and 66323 "
        "(multifamily: conversions of non-livable space, up to 2 detached; up to 8 from 2025, SB 1211)",
        "source_lead (repo law table verified for the single-family rules; multifamily scope from statute "
        "summaries, not re-read here: leginfo returned HTTP 403)"),
    "WA": (
        _SF1, {**_SF1, "mf2": 1.0, "mf3_4": 1.0}, {**_SF1, **_ALL_MF, "mobile": 1.0},
        "RCW 36.70A.681: two ADUs on lots in all zoning districts in a UGA that allow single-family homes; "
        "RCW 36.70A.696(1) defines an ADU as on the same lot as a single-family unit, duplex, triplex, "
        "townhome or other housing unit",
        "verified (partly: RCW pages truncated); zone-based, so large apartment buildings in multifamily-only zones "
        "are out in the central"),
    "OR": (
        _SF, _SF, {**_SF1, "mobile": 1.0},
        "ORS 197.312(5): at least one ADU for each detached single-family dwelling in areas zoned for them",
        "verified (repo law table; DLCD guidance)"),
    "RI": (
        _SF, _SF1, {**_SF1, "mf2": 1.0, "mf3_4": 1.0},
        "RIGL 45-24-73 (2024): ADU on a lot with a single-family dwelling; whether the 2022 law reaches multi-unit "
        "dwellings could not be re-read (rilegislature.gov refused connections)",
        "unknown (multifamily scope); single-family scope verified in the repo law table"),
    "MA": (
        _SF, {**_SF1, "mf2": 1.0, "mf3_4": 1.0}, {**_SF1, **_ALL_MF, "mobile": 1.0},
        "M.G.L. c.40A s.3: one protected-use ADU in single-family residential zoning districts, on a lot with a "
        "principal dwelling (760 CMR 71.02); zone-based like Washington",
        "source_lead (statute and regulation pages refused/403 here; repo law table verified)"),
    "ME": (
        {**_SF1, "mf2": 1.0}, {**_SF1, "mf2": 1.0, "mf3_4": 0.5}, {**_SF1, "mf2": 1.0, "mf3_4": 1.0, "mobile": 1.0},
        "30-A MRSA 4364-B(1),(3)(A): an ADU on any lot with a single-family dwelling unit or a 2-unit or "
        "3-unit residential structure (the 3-4 band counted at one half in the central)",
        "verified (statute text read 2026-10-25)"),
    "UT": (
        _SF, _SF, _SF1,
        "Utah Code 10-21-303 (HB 82, 2021): internal ADUs within a primary dwelling, a detached single-family "
        "dwelling occupied by its owner",
        "source_lead (le.utah.gov section body not readable here; repo law table verified)"),
    "VT": (
        _SF, _SF1, {**_SF1, "mobile": 1.0},
        "24 V.S.A. 4412(1)(E): one ADU within or appurtenant to a single-family dwelling",
        "verified (statute text read 2026-10-25)"),
    "minneapolis": (
        _SF1 | {"mf2": 1.0}, _SF1 | {"mf2": 1.0}, _SF1 | {"mf2": 1.0},
        "2014 ordinance: ADUs with single- and two-family homes citywide (owner direction: SF + two-family)",
        "verified (repo reforms table)"),
    "seattle": (
        _SF, _SF1, {**_SF1, "mf2": 1.0, "mf3_4": 1.0},
        "SMC 23.44.041 (to 2025): AADU/DADU on single-family-zoned lots with one principal house; from 2025 SMC "
        "23.42.022 (HB 1337)",
        "source_lead (municode 403 here)"),
    "portland": (
        _SF, _SF1, {**_SF1, "mf2": 1.0, "mobile": 1.0},
        "33.205: ADUs with a house, attached house or manufactured home (RIP 2021-22: two ADUs per house)",
        "source_lead (portland.gov code page 404 here)"),
    "austin": (
        _SF, _SF, _SF1,
        "LDC 25-2-1463 (to 2024): secondary apartment on an SF-3 lot with a single-family house",
        "source_lead"),
    "denver": (
        _SF, _SF, _SF1,
        "Denver Zoning Code: ADU accessory to a primary single-unit dwelling (citywide from 2024-12-16)",
        "source_lead"),
}
STATE_OF_SERIES = {"WA_inc_exSeattle": "WA", "OR_panel32_exPortland": "OR", "RI_statewide": "RI",
                   "MA_statewide": "MA", "ME_statewide": "ME", "UT_mih": "UT", "VT_chittenden": "VT"}
SCENARIOS = {   # denominator scenario -> (law scope index, size set): fewest / central / most properties
    "low": (0, "very_large"),
    "central": (1, CENTRAL_SIZE),
    "high": (2, "small"),
}


def buildings(units: pd.DataFrame, sizes: dict) -> pd.DataFrame:
    """Housing units by band -> buildings by band (multifamily bands only); one-unit and mobile
    components are one property per unit."""
    out = pd.DataFrame(index=units.index)
    for c in COMPONENTS:
        if c not in units:
            continue
        out[c] = units[c].astype(float) / (sizes[c] if c in MF else 1.0)
    return out


def eligible(units: pd.DataFrame, scope: dict, sizes: dict) -> pd.Series:
    """Eligible properties = sum over components of scope share x properties."""
    b = buildings(units, sizes)
    return sum(b[c].fillna(0) * float(w) for c, w in scope.items() if c in b)


def mf_properties(units: pd.DataFrame, sizes: dict) -> pd.Series:
    b = buildings(units, sizes)
    return b[[c for c in MF if c in b]].sum(axis=1)


def components_from_acs(acs: pd.DataFrame) -> pd.DataFrame:
    """read_acs_sf-style B25024 frame -> one column per component (housing units)."""
    out = acs[[c for c in acs.columns if c in ("geoid", "sumlevel", "geo_id")]].copy()
    for k, col in COMPONENTS.items():
        out[k] = pd.to_numeric(acs[col], errors="coerce")
    return out


def scenario_eligible(units: pd.DataFrame, key: str, scenario: str, size: str | None = None) -> pd.Series:
    i, sz = SCENARIOS[scenario]
    return eligible(units, LAW_SCOPE[key][i], SIZES[size or sz])


# ---------------------------------------------------------------------------
# Flattening to permits: at most one per parcel per year
# ---------------------------------------------------------------------------

def norm_site(s: pd.Series) -> pd.Series:
    """Upper-case letters/digits and single spaces; empty -> NA."""
    t = (s.fillna("").astype(str).str.upper().str.replace(r"[^A-Z0-9 ]", " ", regex=True)
         .str.replace(r"\s+", " ", regex=True).str.strip())
    return t.mask(t.eq(""))


def site_key(parcel: pd.Series, address: pd.Series | None = None, row_id: pd.Series | None = None) -> tuple[pd.Series, pd.Series]:
    """Parcel id where present, else 'A:' + normalised address, else 'R:' + row id (one permit).
    Returns (key, basis) with basis in {'parcel', 'address', 'row'}."""
    p = parcel.astype("string").str.strip().replace("", pd.NA)
    a = norm_site(address) if address is not None else pd.Series(pd.NA, index=parcel.index, dtype="string")
    r = (row_id.astype(str) if row_id is not None else pd.Series(parcel.index.astype(str), index=parcel.index))
    key = p.where(p.notna(), ("A:" + a).where(a.notna(), "R:" + r))
    basis = pd.Series(np.select([p.notna(), a.notna()], ["parcel", "address"], "row"), index=parcel.index)
    return key.astype(str), basis


def flatten(df: pd.DataFrame, by: list[str], key: str = "site", units: str = "units") -> pd.DataFrame:
    """Per group (e.g. jurisdiction-year): units, permit rows and distinct sites (= flattened permits)."""
    g = df.groupby(by)
    out = g.agg(units=(units, "sum"), rows=(key, "size"), permits=(key, "nunique")).reset_index()
    out["units_per_permit"] = out["units"] / out["permits"].where(out["permits"] > 0)
    return out


def capped_events(df: pd.DataFrame, juris: str = "juris_name", key: str = "site", year: str = "year",
                  cap: int = 2) -> pd.DataFrame:
    """Distinct (juris, site, year) events with `keep` = the site's 1st..cap-th event year
    (cumulated over all years). Row-keyed sites (no parcel id) are always kept."""
    e = df.drop_duplicates([juris, key, year]).sort_values([juris, key, year]).copy()
    e["event_order"] = e.groupby([juris, key]).cumcount() + 1
    e["keep"] = (e["event_order"] <= cap) | e[key].str.startswith("R:")
    return e


# ---------------------------------------------------------------------------
# Equal-propensity test
# ---------------------------------------------------------------------------

def propensity(permits_sf: float, permits_mf: float, props_sf: float, props_mf: float) -> dict:
    """Permits per 1,000 properties on single-family and multifamily lots, their ratio, and the
    blended rate's overstatement of the single-family rate (blended / single-family)."""
    r_sf = permits_sf / props_sf * 1000
    r_mf = permits_mf / props_mf * 1000
    blended = (permits_sf + permits_mf) / (props_sf + props_mf) * 1000
    return dict(rate_sf=r_sf, rate_mf=r_mf, ratio_mf_to_sf=r_mf / r_sf if r_sf > 0 else np.nan,
                rate_blended=blended, blended_over_sf=blended / r_sf if r_sf > 0 else np.nan)


def sf_rate_from_blended(blended: float, s: float, m: float, rho: float) -> float:
    """Single-family-lot rate implied by a blended rate when multifamily propensity = rho x
    single-family: blended = r_sf (s + rho m) / (s + m)."""
    return blended * (s + m) / (s + rho * m)
