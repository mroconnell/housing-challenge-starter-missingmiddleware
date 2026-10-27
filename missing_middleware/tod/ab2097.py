"""California AB 2097 test (docs/tod/AB2097_TEST_PREREG.md, including its section 8 changes).

AB 2097 removed parking minimums within 1/2 mile of a major transit stop from 1 January 2023. The test compares
homes permitted near transit with a ring 1/2 to 1 1/2 miles out, before (2018-2022) and after (2023-2025):

- Group P (parking alone): near transit, outside areas upzoned before 2023, in full-reporting jurisdictions that
  were not already free of parking minimums. Comparison: the ring in the same jurisdictions.
- Group T+P (TOD plus parking): near transit, inside an area upzoned before 2023 (Los Angeles TOC tiers, 2017).
  Comparison: the ring in the jurisdictions that have such land.
- Combination term: T+P estimate minus P estimate.
- Outcomes: all units, and units in buildings of 2 or more units ("2 to 4" and "5+"), in issued building permits.
  Rates per 1,000 existing homes (2020 census) per year (main) and per acre of land per year.
- Main interval: 90%, resampling whole jurisdictions, 2,000 draws, fixed seed. Sensitivity: resampling projects
  (missing_middleware.tod.cases.bootstrap_did).
- Displacement check: each group's ring against land more than 1 1/2 miles from any stop, same jurisdictions.

The arithmetic works on plain tables so it can be tested without geography:
- `cells`: one row per jurisdiction x zone x upzoned flag, with homes and acres (from census blocks).
- `permits`: one row per de-duplicated permit record, with juris, project, year, zone, upz, units, units_2plus.
Zones: "near", "ring", "beyond", or "gap" (land in no area, used by the 1/4-mile sensitivity).

Privacy: project ids are one-way hashes made in memory; no address, APN or tracking id is written out.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from missing_middleware.tod import cases

MILE_M = 1609.344
NEAR_M = 0.5 * MILE_M
QUARTER_M = 0.25 * MILE_M
RING_M = 1.5 * MILE_M
YEARS = list(range(2018, 2026))
BEFORE = [2018, 2019, 2020, 2021, 2022]
AFTER = [2023, 2024, 2025]
N_DRAWS = 2000
SEED = 20261027
LEVEL = 0.90
THIN_JURIS = 10
TWO_PLUS = ("2 to 4", "5+")
OUTCOMES = ("all_units", "units_2plus")
MEASURES = {"per_1000_homes": ("homes", 1000.0), "per_acre": ("acres", 1.0)}

# Prereg section 8 item 1; final list in AB2097_TEST_RESULTS.md section 1a (HCD JURIS_NAME spelling).
ALREADY_NO_MINIMUMS = ("SAN FRANCISCO", "EMERYVILLE", "ALAMEDA", "CULVER CITY", "BERKELEY", "POMONA", "EUREKA",
                       "SAN DIEGO", "HAYWARD", "FREMONT", "OAKLAND", "STOCKTON")
REPEALED_CITYWIDE_LATER = ("SAN JOSE", "SACRAMENTO")
LA = "LOS ANGELES"


# --------------------------------------------------------------------------- permits

def is_geocoded(lat: pd.Series, lon: pd.Series, std_address: pd.Series) -> pd.Series:
    """Prereg section 8 item 8: coordinates plus an HCD standardized street address (street and city, not a city
    name alone). Fallback points (city or county centroids) have no standardized street address."""
    s = std_address.fillna("").astype(str)
    has_street = s.str.match(r"^([^,]+,){2,}\s*California,")
    return lat.notna() & lon.notna() & has_street


def _norm(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.upper().str.replace(r"[^A-Z0-9]+", " ", regex=True).str.strip()


def project_id(juris: pd.Series, address: pd.Series) -> pd.Series:
    """One-way hash of jurisdiction plus standardized address (prereg section 8 item 14)."""
    key = _norm(juris) + "|" + _norm(address)
    return key.map(lambda k: hashlib.sha1(k.encode()).hexdigest()[:16])


def clean_permits(a2: pd.DataFrame, years: list[int] = YEARS) -> tuple[pd.DataFrame, dict]:
    """Table A2 rows -> permit records with units, the geocoding rule and de-duplication applied.

    Needs JURIS_NAME, YEAR, UNIT_CAT, NO_BUILDING_PERMITS, LATITUDE, LONGITUDE, STD_ADDRESS, STREET_ADDRESS.
    Returns (records, counts) where counts reports what each step removed."""
    d = a2.copy()
    d["units"] = pd.to_numeric(d["NO_BUILDING_PERMITS"], errors="coerce").fillna(0.0)
    d = d[(d["units"] > 0) & d["YEAR"].isin(years)]
    info = {"records_with_permits": int(len(d)), "units_with_permits": float(d["units"].sum())}
    geo = is_geocoded(pd.to_numeric(d["LATITUDE"], errors="coerce"), pd.to_numeric(d["LONGITUDE"], errors="coerce"),
                      d["STD_ADDRESS"])
    info["units_not_geocoded"] = float(d.loc[~geo, "units"].sum())
    d = d[geo].copy()
    d["addr"] = _norm(d["STREET_ADDRESS"]).where(_norm(d["STREET_ADDRESS"]) != "", _norm(d["STD_ADDRESS"]))
    key = ["JURIS_NAME", "addr", "YEAR", "UNIT_CAT", "units"]
    n0, u0 = len(d), d["units"].sum()
    d = d.drop_duplicates(key)
    info["duplicate_records_dropped"] = int(n0 - len(d))
    info["duplicate_units_dropped"] = float(u0 - d["units"].sum())
    out = pd.DataFrame({
        "juris": d["JURIS_NAME"].astype(str).str.upper().str.strip().values,
        "project": project_id(d["JURIS_NAME"], d["STD_ADDRESS"]).values,
        "year": d["YEAR"].astype(int).values,
        "unit_cat": d["UNIT_CAT"].astype(str).values,
        "all_units": d["units"].astype(float).values,
        "lat": pd.to_numeric(d["LATITUDE"]).values,
        "lon": pd.to_numeric(d["LONGITUDE"]).values,
    })
    out["units_2plus"] = np.where(out["unit_cat"].isin(TWO_PLUS), out["all_units"], 0.0)
    return out, info


def full_reporters(permits: pd.DataFrame, years: list[int] = YEARS) -> list[str]:
    """Jurisdictions with at least one geocoded record with permitted units in every year (section 8 item 13)."""
    yrs = permits.groupby("juris")["year"].apply(lambda s: set(s))
    return sorted(j for j, s in yrs.items() if set(years) <= s)


def zone_of(dist_m: np.ndarray | pd.Series, near_m: float = NEAR_M, ring_m: float = RING_M,
            ring_inner_m: float = NEAR_M) -> np.ndarray:
    """near (< near_m), ring (ring_inner_m to ring_m), beyond (>= ring_m), gap (near_m to ring_inner_m)."""
    d = np.asarray(dist_m, dtype=float)
    z = np.where(d < near_m, "near", np.where(d < ring_inner_m, "gap", np.where(d < ring_m, "ring", "beyond")))
    return z


# --------------------------------------------------------------------------- groups

@dataclass
class Group:
    name: str
    juris: list[str]
    treat: tuple[str, bool]          # (zone, upz) of the treated land
    comp: tuple[str, bool] = ("ring", False)
    extra: dict = field(default_factory=dict)


def define_groups(cells: pd.DataFrame, reporters: list[str], include_repealed: bool = False,
                  only: list[str] | None = None) -> dict[str, Group]:
    """Group P and group T+P, from the denominator cells (prereg sections 3 and 8)."""
    rep = set(reporters) if only is None else set(reporters) & set(only)
    drop = set(ALREADY_NO_MINIMUMS) | (set() if include_repealed else set(REPEALED_CITYWIDE_LATER))
    has = cells[cells["homes"] > 0].groupby(["zone", "upz"])["juris"].apply(set)
    near_out = has.get(("near", False), set())
    near_in = has.get(("near", True), set())
    p = sorted((rep - drop) & near_out)
    tp = sorted(rep & near_in)
    return {"P": Group("P", p, ("near", False)), "T+P": Group("T+P", tp, ("near", True))}


def _arrays(g: Group, cells: pd.DataFrame, permits: pd.DataFrame, outcome: str, denom: str, years: list[int],
            treat=None, comp=None):
    """Per-jurisdiction unit arrays (juris x year) and denominators for the treated and comparison land."""
    treat = treat or g.treat
    comp = comp or g.comp
    J = list(g.juris)
    ix = {j: i for i, j in enumerate(J)}
    yx = {y: k for k, y in enumerate(years)}
    out = {}
    for lab, (z, u) in (("t", treat), ("c", comp)):
        c = cells[(cells["zone"] == z) & (cells["upz"] == u) & cells["juris"].isin(J)]
        den = np.zeros(len(J))
        for j, v in c.groupby("juris")[denom].sum().items():
            den[ix[j]] = v
        p = permits[(permits["zone"] == z) & (permits["upz"] == u) & permits["juris"].isin(J) & permits["year"].isin(years)]
        mat = np.zeros((len(J), len(years)))
        for (j, y), v in p.groupby(["juris", "year"])[outcome].sum().items():
            mat[ix[j], yx[y]] += v
        out[lab] = (mat, den)
    return out


def _did_arrays(t_units, t_den, c_units, c_den, nb: int, na_idx: list[int], scale: float) -> float:
    def ch(units, den):
        if den <= 0:
            return float("nan")
        r = units / den * scale
        return r[na_idx].mean() - r[:nb].mean()
    return ch(t_units, t_den) - ch(c_units, c_den)


def estimate(g: Group, cells: pd.DataFrame, permits: pd.DataFrame, outcome: str = "all_units",
             measure: str = "per_1000_homes", before: list[int] = BEFORE, after: list[int] = AFTER,
             draws: int = N_DRAWS, seed: int = SEED, treat=None, comp=None, keep_draws: bool = False) -> dict:
    """DiD of the group's treated land against its comparison land, with a jurisdiction-resampling interval."""
    denom, scale = MEASURES[measure]
    years = list(before) + list(after)
    arr = _arrays(g, cells, permits, outcome, denom, years, treat, comp)
    (tm, td), (cm, cd) = arr["t"], arr["c"]
    nb = len(before)
    aidx = list(range(nb, len(years)))
    tu, cu = tm.sum(axis=0), cm.sum(axis=0)
    est = _did_arrays(tu, td.sum(), cu, cd.sum(), nb, aidx, scale)

    def rate(u, d, idx):
        return float(u[idx].mean() / d * scale) if d > 0 else float("nan")
    row = {"estimate": est,
           "treat_rate_before": rate(tu, td.sum(), list(range(nb))), "treat_rate_after": rate(tu, td.sum(), aidx),
           "comp_rate_before": rate(cu, cd.sum(), list(range(nb))), "comp_rate_after": rate(cu, cd.sum(), aidx),
           "treat_units_before": float(tu[:nb].sum()), "treat_units_after": float(tu[nb:].sum()),
           "comp_units_before": float(cu[:nb].sum()), "comp_units_after": float(cu[nb:].sum()),
           "treat_denominator": float(td.sum()), "comp_denominator": float(cd.sum()),
           "n_juris": int((td > 0).sum()),
           "n_juris_permits_both_periods": int(((tm[:, :nb].sum(1) > 0) & (tm[:, nb:].sum(1) > 0)).sum())}
    J = len(g.juris)
    lo = hi = float("nan")
    dr = np.full(draws, np.nan)
    if J >= 2:
        rng = np.random.default_rng(seed)
        for k in range(draws):
            s = rng.integers(0, J, J)
            dr[k] = _did_arrays(tm[s].sum(0), td[s].sum(), cm[s].sum(0), cd[s].sum(), nb, aidx, scale)
        lo, hi = np.nanquantile(dr, [(1 - LEVEL) / 2, 1 - (1 - LEVEL) / 2])
    row.update({"low": float(lo), "high": float(hi), "interval": "jurisdictions" if J >= 2 else "none (one jurisdiction)"})
    if keep_draws:
        row["draws"] = dr
    return row


def to_area_permits(g: Group, permits: pd.DataFrame, outcome: str, treat=None, comp=None) -> pd.DataFrame:
    """Permits of a group labelled with cases.TREAT / cases.COMP, in the shape cases.py expects."""
    treat = treat or g.treat
    comp = comp or g.comp
    p = permits[permits["juris"].isin(g.juris)]
    t = (p["zone"] == treat[0]) & (p["upz"] == treat[1])
    c = (p["zone"] == comp[0]) & (p["upz"] == comp[1])
    out = p[t | c].copy()
    out["area"] = np.where(t[t | c], cases.TREAT, cases.COMP)
    out["units"] = out[outcome]
    return out[["project", "area", "year", "units"]]


def denominators(g: Group, cells: pd.DataFrame, measure: str, treat=None, comp=None) -> dict:
    treat = treat or g.treat
    comp = comp or g.comp
    denom, _ = MEASURES[measure]
    c = cells[cells["juris"].isin(g.juris)]
    return {cases.TREAT: float(c[(c.zone == treat[0]) & (c.upz == treat[1])][denom].sum()),
            cases.COMP: float(c[(c.zone == comp[0]) & (c.upz == comp[1])][denom].sum())}


def project_interval(g: Group, cells: pd.DataFrame, permits: pd.DataFrame, outcome: str, measure: str,
                     before: list[int] = BEFORE, after: list[int] = AFTER, draws: int = N_DRAWS, seed: int = SEED,
                     treat=None, comp=None) -> tuple[float, float, np.ndarray]:
    """Project-resampling interval (cases.bootstrap_did)."""
    _, scale = MEASURES[measure]
    ap = to_area_permits(g, permits, outcome, treat, comp)
    den = denominators(g, cells, measure, treat, comp)
    if not den[cases.TREAT] or not den[cases.COMP]:
        return float("nan"), float("nan"), np.full(draws, np.nan)
    return cases.bootstrap_did(ap, den, list(before), list(after), draws=draws, seed=seed, scale=scale)


def drop_largest(g: Group, permits: pd.DataFrame, outcome: str, before=BEFORE, after=AFTER) -> pd.DataFrame:
    """Permits with the largest project (by this outcome) in each area and period left out (cases.drop_largest_project)."""
    p = permits[permits["juris"].isin(g.juris)].copy()
    t = (p["zone"] == g.treat[0]) & (p["upz"] == g.treat[1])
    c = (p["zone"] == g.comp[0]) & (p["upz"] == g.comp[1])
    p["area"] = np.where(t, cases.TREAT, np.where(c, cases.COMP, "other"))
    p["units"] = p[outcome]
    kept = cases.drop_largest_project(p[p["units"] > 0], list(before), list(after))
    rest = p[p["units"] <= 0]
    return pd.concat([kept, rest]).drop(columns=["area", "units"])


def interval_of(draws: np.ndarray) -> tuple[float, float]:
    d = draws[~np.isnan(draws)]
    if not len(d):
        return float("nan"), float("nan")
    lo, hi = np.quantile(d, [(1 - LEVEL) / 2, 1 - (1 - LEVEL) / 2])
    return float(lo), float(hi)


def rates_by_year(groups: dict[str, Group], cells: pd.DataFrame, permits: pd.DataFrame, years=YEARS) -> pd.DataFrame:
    """Units, homes, acres and rates by group, area (near / ring / beyond), outcome and year."""
    rows = []
    for gname, g in groups.items():
        areas = {"near": g.treat, "ring": g.comp, "beyond": ("beyond", False)}
        for area, (z, u) in areas.items():
            c = cells[(cells.zone == z) & (cells.upz == u) & cells.juris.isin(g.juris)]
            homes, acres = float(c.homes.sum()), float(c.acres.sum())
            p = permits[(permits.zone == z) & (permits.upz == u) & permits.juris.isin(g.juris)]
            for oc in OUTCOMES:
                for y in years:
                    py = p[(p.year == y) & (p[oc] > 0)]
                    units = float(py[oc].sum())
                    rows.append({"group": gname, "area": area, "outcome": oc, "year": int(y),
                                 "period": "before" if y in BEFORE else "after",
                                 "units": units, "projects": int(py.project.nunique()),
                                 "jurisdictions_with_permits": int(py.juris.nunique()),
                                 "homes_2020": round(homes), "acres": round(acres, 1),
                                 "units_per_1000_homes": units / homes * 1000 if homes else float("nan"),
                                 "units_per_acre": units / acres if acres else float("nan")})
    return pd.DataFrame(rows)


def usable(n_juris_both: int) -> str:
    """Prereg section 8 item 5: fewer than about 10 jurisdictions with permits in both periods -> too thin."""
    return "usable" if n_juris_both >= THIN_JURIS else "too thin"
