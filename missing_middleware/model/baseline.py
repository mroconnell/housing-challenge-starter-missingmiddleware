"""Wisconsin current-law ADU rate x and baseline B (Gate 3, work package B).

Outcome: second homes on single-family lots (AQ-032), per 1,000 ACS one-unit
detached homes per year. Baseline for municipality piece a, forecast year t:

    B[a,t] = H[a] * x[a] * g[a,t] / 1000

x is observed where permit records exist (Madison, Pleasant Prairie, Sun
Prairie), and otherwise estimated from the place's coded rights class or, for
uncoded places, treated like `restricted` (AQ-027). g < 1 only for places that
moved from a prohibited regime to an allowed one recently and are still ramping
toward their class rate (for example Sun Prairie after May 2026); g is assumed, not fitted.
Milwaukee uses its measured 2022-2025 rate, flat (owner, 2026-10-26, AQ-043); its ramp is a
baseline sensitivity.

Three baseline paths (low / central / high) move together across all areas
(shared parameter uncertainty, never summed as if independent): each takes the
low, central or high rate for every group and a slow, middle or fast ramp.

Everything here is pure (no network, no file paths) so it can be unit-tested;
scripts/build_wi_baseline.py does the reading and writing.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

FORECAST_YEARS = (2027, 2028, 2029, 2030, 2031)   # forecast years 1..5 (AQ-021)
BRIDGE_YEAR = 2026                                # shown, never in five-year totals
ALL_YEARS = (BRIDGE_YEAR,) + FORECAST_YEARS
PATHS = ("low", "central", "high")

# Hold-out of coded places (AQ-027): drawn from identifiers only, before any rate is estimated.
HOLDOUT_SEED = 20261024
HOLDOUT_SHARE = 0.20
# The three observed pilots are the fitting set named by the owner (AQ-028), so they are not
# eligible for the hold-out; every other coded place is.
MADISON, PLEASANT_PRAIRIE, SUN_PRAIRIE = "5502548000", "5505963300", "5502578600"
MILWAUKEE, FITCHBURG = "5507953000", "5502525950"
FIT_PLACE_IDS = (MADISON, PLEASANT_PRAIRIE, SUN_PRAIRIE)
HOLDOUT_METHOD = (
    "Universe: the 37 coded places in reference/wi_rights_exposure.csv (one row per place, keyed by the "
    "largest piece's 10-digit county-subdivision GEOID), minus the three observed pilots (Madison, "
    "Pleasant Prairie, Sun Prairie), which are the fitting set named in AQ-028. Sorted by id; simple "
    "random sample without replacement of round(0.20 * N) places with "
    "numpy.random.default_rng(20261024).choice. Drawn from identifiers only, before any x was estimated."
)



def draw_holdout(place_ids: list[str], seed: int = HOLDOUT_SEED, share: float = HOLDOUT_SHARE,
                 exclude: tuple[str, ...] = FIT_PLACE_IDS) -> pd.DataFrame:
    """One row per place with holdout True/False; excluded places are never held out."""
    ids = sorted(set(place_ids))
    excl = set(exclude)
    eligible = [i for i in ids if i not in excl]
    n = int(round(share * len(eligible)))
    idx = np.random.default_rng(seed).choice(len(eligible), size=n, replace=False)
    picked = {eligible[i] for i in idx}
    return pd.DataFrame({
        "jurisdiction_id": ids,
        "eligible": [i not in excl for i in ids],
        "holdout": [i in picked for i in ids],
        "seed": seed,
        "universe_size": len(eligible),
        "n_held_out": n,
    })


# Years for a newly liberalized place to reach its class rate, by path (assumed). The central
# value follows the shape of Madison after by-right approval (Dec 2021): 5, 9, 11, 14 second
# homes in 2022-2025, still rising after four years.
RAMP_YEARS = {"low": 6.0, "central": 4.0, "high": 2.0}

RIGHTS_GROUP = {
    "scenario_benchmark": "benchmark",
    "restricted": "restricted",
    "prohibited_explicit": "prohibited",
    "prohibited_implicit": "prohibited",
    # No zoning: ADUs not barred by zoning; no observations, so treated like an unknown place.
    "no_zoning": "undetermined",
    "undetermined": "undetermined",
}


# ---------------------------------------------------------------------------
# Rates and intervals
# ---------------------------------------------------------------------------

def rate_per_1000(units: float, homes: float, years: float) -> float:
    """Second homes per 1,000 one-unit detached homes per year."""
    if homes <= 0 or years <= 0:
        raise ValueError("homes and years must be positive")
    return 1000.0 * units / (homes * years)


def _poisson_cdf(k: int, mu: float) -> float:
    if mu <= 0:
        return 1.0
    term = math.exp(-mu)
    total = term
    for i in range(1, k + 1):
        term *= mu / i
        total += term
    return min(total, 1.0)


def poisson_interval(k: int, conf: float = 0.95) -> tuple[float, float]:
    """Exact (Garwood) two-sided interval for a Poisson count k."""
    if k < 0:
        raise ValueError("count must be non-negative")
    alpha = 1 - conf

    def solve(f, lo, hi):
        for _ in range(200):
            mid = (lo + hi) / 2
            if f(mid):
                hi = mid
            else:
                lo = mid
        return (lo + hi) / 2

    top = 10.0 + 10 * k
    lower = 0.0 if k == 0 else solve(lambda mu: 1 - _poisson_cdf(k - 1, mu) >= alpha / 2, 0.0, top)
    upper = solve(lambda mu: _poisson_cdf(k, mu) <= alpha / 2, 0.0, top)
    return lower, upper


@dataclass(frozen=True)
class Observation:
    """A count of second homes over an exposure of homes x years."""
    key: str
    place: str
    jurisdiction_id: str
    series: str
    window: str
    units: int
    homes: float
    years: float
    regime: str          # rights group in force during the window
    status: str          # observed | observed_candidate
    note: str = ""

    @property
    def exposure(self) -> float:   # thousand home-years
        return self.homes * self.years / 1000.0

    @property
    def rate(self) -> float:
        return rate_per_1000(self.units, self.homes, self.years)

    @property
    def interval(self) -> tuple[float, float]:
        lo, hi = poisson_interval(int(round(self.units)))
        return lo / self.exposure, hi / self.exposure

    def row(self) -> dict:
        lo, hi = self.interval
        return {"key": self.key, "place": self.place, "jurisdiction_id": self.jurisdiction_id,
                "series": self.series, "window": self.window, "units": self.units,
                "homes": self.homes, "years": round(self.years, 3),
                "thousand_home_years": round(self.exposure, 3), "rate_per_1000_yr": self.rate,
                "poisson95_lo": lo, "poisson95_hi": hi, "regime": self.regime,
                "status": self.status, "note": self.note}


def pooled(obs: list[Observation]) -> tuple[float, float, float, int, float]:
    """Pooled rate (total units / total exposure) with exact Poisson interval."""
    k = int(round(sum(o.units for o in obs)))
    e = sum(o.exposure for o in obs)
    lo, hi = poisson_interval(k)
    return k / e, lo / e, hi / e, k, e


def years_between(start: date, end_inclusive: date) -> float:
    return ((end_inclusive - start).days + 1) / 365.25


# ---------------------------------------------------------------------------
# Series helpers for the committed reference tables
# ---------------------------------------------------------------------------

def madison_units(ref: pd.DataFrame, category: str, years: range | list[int]) -> int:
    """Sum `units` for a Madison category over years (reference/madison_adu_permits_by_year.csv)."""
    d = ref[(ref["category"] == category) & (ref["year"].isin(list(years)))]
    if d["year"].nunique() != len(list(years)):
        raise ValueError(f"Madison {category}: missing years")
    return int(round(d["units"].sum()))


def comparison_units(ref: pd.DataFrame, series: str, start: date, end: date,
                     restrictive_only: bool = True) -> int:
    """Sum `units` for a comparison-city series over row sets lying inside [start, end]."""
    d = ref[ref["series"] == series].copy()
    d["ps"] = pd.to_datetime(d["period_start"]).dt.date
    d["pe"] = pd.to_datetime(d["period_end"]).dt.date
    d = d[(d["ps"] >= start) & (d["pe"] <= end)]
    if restrictive_only:
        d = d[d["restrictive_period"].astype(str).str.lower() == "true"]
    return int(round(d["units"].sum()))


# ---------------------------------------------------------------------------
# Group rate table
# ---------------------------------------------------------------------------

def group_rates(benchmark: Observation, prohibited: list[Observation], restricted: list[Observation],
                restricted_high: Observation) -> pd.DataFrame:
    """Rates (low, central, high) per rights group. Simple and transparent:

    - prohibited: pooled observed restrictive-period rate; range is its exact Poisson 95% interval.
    - restricted: pooled observed rate under restricted regimes; low = prohibited central (a
      restricted place can be as quiet as a banned one); high = `restricted_high` (the best
      observed restricted regime, Madison by right with owner occupancy).
    - benchmark (coded, unobserved): central = observed benchmark rate (Madison); low = restricted
      central; high = upper Poisson bound of the benchmark observation.
    - undetermined (uncoded): behaves like restricted (AQ-027) with low = prohibited central.
    """
    p_c, p_lo, p_hi, p_k, p_e = pooled(prohibited)
    r_c, _, _, r_k, r_e = pooled(restricted)
    b_lo, b_hi = benchmark.interval
    rows = [
        {"group": "prohibited", "x_low": p_lo, "x_central": p_c, "x_high": p_hi,
         "basis": "observed (pooled)", "units": p_k, "thousand_home_years": p_e,
         "evidence": "; ".join(o.key for o in prohibited),
         "range_rule": "exact Poisson 95% interval of the pooled count"},
        {"group": "restricted", "x_low": p_c, "x_central": r_c, "x_high": restricted_high.rate,
         "basis": "observed (pooled), applied as estimate", "units": r_k, "thousand_home_years": r_e,
         "evidence": "; ".join(o.key for o in restricted),
         "range_rule": f"low = prohibited central; high = {restricted_high.key}"},
        {"group": "benchmark", "x_low": r_c, "x_central": benchmark.rate, "x_high": b_hi,
         "basis": "observed in Madison, applied as estimate elsewhere", "units": benchmark.units,
         "thousand_home_years": benchmark.exposure, "evidence": benchmark.key,
         "range_rule": "low = restricted central; high = upper Poisson 95% bound for Madison"},
        {"group": "undetermined", "x_low": p_c, "x_central": r_c, "x_high": restricted_high.rate,
         "basis": "assumed: behaves like restricted (AQ-027)", "units": None,
         "thousand_home_years": None, "evidence": "restricted group",
         "range_rule": "low = prohibited central; central and high = restricted"},
    ]
    out = pd.DataFrame(rows)
    _check_order(out, ["x_low", "x_central", "x_high"])
    return out


def _check_order(df: pd.DataFrame, cols: list[str]) -> None:
    v = df[cols].to_numpy(dtype=float)
    if (np.diff(v, axis=1) < -1e-12).any():
        raise ValueError("rates out of order (low <= central <= high violated)")


# ---------------------------------------------------------------------------
# Ramp for recently liberalized places
# ---------------------------------------------------------------------------

def ramp_share(year: int, reform_date: date | None, ramp_years: float) -> float:
    """Share of the way from the pre-reform rate to the new rate reached in calendar `year`,
    measured at mid-year; linear, 0 at the reform date, 1 after `ramp_years`."""
    if reform_date is None:
        return 1.0
    t = (date(year, 7, 1) - reform_date).days / 365.25
    return float(min(1.0, max(0.0, t / ramp_years)))


def ramped_rate(year: int, x_pre: float, x_target: float, reform_date: date | None,
                ramp_years: float) -> float:
    return x_pre + (x_target - x_pre) * ramp_share(year, reform_date, ramp_years)


def liberalizations(rules: pd.DataFrame) -> pd.DataFrame:
    """Places whose detached ADUs moved from `prohibited` to an allowed value on a dated change
    (wi_adu_rules.csv). reform_date is the day after the prohibited row's effective_to."""
    d = rules[rules["provision"] == "detached_allowed"].copy()
    d["jurisdiction_id"] = d["jurisdiction_id"].astype(str)
    out = []
    for jid, g in d.groupby("jurisdiction_id"):
        ended = g[(g["value"] == "prohibited") & g["effective_to"].notna()]
        later = g[(g["value"] != "prohibited") & g["effective_from"].notna()]
        if len(ended) and len(later):
            end = pd.to_datetime(ended["effective_to"]).max().date()
            start = pd.to_datetime(later["effective_from"]).min().date()
            if start > end:
                out.append({"jurisdiction_id": jid, "jurisdiction_name": g["jurisdiction_name"].iloc[0],
                            "reform_date": start, "new_value": later.sort_values("effective_from")["value"].iloc[0]})
    return pd.DataFrame(out, columns=["jurisdiction_id", "jurisdiction_name", "reform_date", "new_value"])


# ---------------------------------------------------------------------------
# Area assignment and baseline
# ---------------------------------------------------------------------------

def assign_rates(areas: pd.DataFrame, rates: pd.DataFrame, observed: dict[str, dict],
                 overrides: dict[str, dict] | None = None) -> pd.DataFrame:
    """One row per area with rate paths.

    areas: area_id, place_id (coded place id or None), name, homes, current_class.
    rates: group_rates() output.
    observed: place_id -> {"low","central","high","basis"} for places with their own permit rate.
    overrides: place_id -> {"target": {path: rate}, "pre": {path: rate}, "reform_date": date,
                            "basis": str}; ramping places (liberalizers).
    """
    overrides = overrides or {}
    r = rates.set_index("group")
    rows = []
    for a in areas.itertuples(index=False):
        cls = a.current_class if isinstance(a.current_class, str) else "undetermined"
        group = RIGHTS_GROUP[cls]
        pid = a.place_id if isinstance(a.place_id, str) else None
        row = {"area_id": a.area_id, "place_id": pid, "name": a.name, "homes": a.homes,
               "current_class": cls, "rate_group": group, "reform_date": None, "pre_low": None,
               "pre_central": None, "pre_high": None}
        if pid in overrides:
            o = overrides[pid]
            for p in PATHS:
                row[f"x_{p}"] = o["target"][p]
                row[f"pre_{p}"] = o["pre"][p]
            row["reform_date"] = o["reform_date"]
            row["x_status"] = o.get("status", "estimated")
            row["x_basis"] = o["basis"]
        elif pid in observed:
            o = observed[pid]
            for p in PATHS:
                row[f"x_{p}"] = o[p]
            row["x_status"] = "observed"
            row["x_basis"] = o["basis"]
        else:
            for p in PATHS:
                row[f"x_{p}"] = float(r.loc[group, f"x_{p}"])
            row["x_status"] = "assumed" if group == "undetermined" else "estimated"
            row["x_basis"] = (f"{group}_group_rate" if group != "undetermined"
                              else "uncoded_like_restricted_AQ027")
        rows.append(row)
    out = pd.DataFrame(rows)
    _check_order(out, ["x_low", "x_central", "x_high"])
    return out


def baseline(assigned: pd.DataFrame, years: tuple[int, ...] = ALL_YEARS,
             ramp_years: dict[str, float] = RAMP_YEARS) -> pd.DataFrame:
    """Long table: area_id, year, path, homes, x_rate (plateau), x_year (rate in force that
    year), g (= x_year / x_rate), baseline_units = homes * x_year / 1000."""
    rows = []
    for a in assigned.itertuples(index=False):
        for p in PATHS:
            target = getattr(a, f"x_{p}")
            pre = getattr(a, f"pre_{p}")
            rd = a.reform_date if isinstance(a.reform_date, date) else None
            for y in years:
                xy = target if rd is None else ramped_rate(y, pre, target, rd, ramp_years[p])
                g = 1.0 if target == 0 else xy / target
                rows.append({"area_id": a.area_id, "year": y, "path": p, "homes": a.homes,
                             "x_rate": target, "x_year": xy, "g": g,
                             "baseline_units": a.homes * xy / 1000.0,
                             "in_five_year_total": y in FORECAST_YEARS})
    return pd.DataFrame(rows)


def check_baseline(b: pd.DataFrame, state_homes: float | None = None) -> list[str]:
    """Analytical checks; returns a list of problems (empty if none)."""
    problems = []
    if (b["baseline_units"] < 0).any():
        problems.append("negative baseline")
    piv = b.pivot_table(index=["area_id", "year"], columns="path", values="baseline_units")
    if ((piv["low"] > piv["central"] + 1e-12) | (piv["central"] > piv["high"] + 1e-12)).any():
        problems.append("paths out of order")
    if ((b["g"] < -1e-12) | (b["g"] > 1 + 1e-9)).any():
        problems.append("g outside [0, 1]")
    if state_homes is not None:
        h = b.drop_duplicates("area_id")["homes"].sum()
        if abs(h - state_homes) > 0.5:
            problems.append(f"area homes {h} != state {state_homes}")
    return problems


def five_year(b: pd.DataFrame, by: list[str] | None = None) -> pd.DataFrame:
    """Five-year (2027-2031) baseline totals by path (bridge year excluded)."""
    keys = (by or []) + ["path"]
    d = b[b["in_five_year_total"]]
    out = d.groupby(keys)["baseline_units"].sum().unstack("path").reset_index()
    return out[(by or []) + list(PATHS)] if by else out


def holdout_status_check(coded: pd.DataFrame) -> pd.DataFrame:
    """Does the first-pass ordinance status predict the second-pass rights group?
    Rule: mentioned_allowed -> allowed (benchmark or restricted); unmentioned or prohibited ->
    prohibited; could_not_access -> no prediction."""
    pred = {"mentioned_allowed": "allowed", "unmentioned": "prohibited", "prohibited": "prohibited"}
    out = coded.copy()
    out["predicted"] = out["ordinance_status"].map(pred)
    actual = out["current_class"].map(RIGHTS_GROUP)
    out["actual"] = actual.map({"benchmark": "allowed", "restricted": "allowed",
                                "prohibited": "prohibited", "undetermined": "undetermined"})
    out["correct"] = out["predicted"] == out["actual"]
    return out


# ---------------------------------------------------------------------------
# Extra Wisconsin evidence (plain HTTP sources): Milwaukee open permits, Fitchburg reports
# ---------------------------------------------------------------------------

def parse_milwaukee_address(addr: str) -> tuple[int, str, str] | None:
    """'1234 N 35TH ST, MILWAUKEE, WI 532100000' -> (1234, 'N', '35TH'). Street type dropped."""
    import re
    m = re.match(r"^\s*(\d+)\S*\s+([NSEW])\s+(.+?),", str(addr).upper())
    if not m:
        return None
    words = m.group(3).split()
    name = " ".join(words[:-1]) if len(words) > 1 else words[0]
    return int(m.group(1)), m.group(2), name


def milwaukee_candidates(permits: pd.DataFrame, mprop: pd.DataFrame) -> pd.DataFrame:
    """Flag Milwaukee permits that may add a second home on a lot that already had a home.

    permits: record_id, issued (Timestamp), permit_type, use, units_impact, address.
    mprop (current Master Property file): house_lo, house_hi, sdir, street, nr_units, yr_built.
    The open data has no description and no unit count, so these are *candidates*:
      - component `conversion_or_attached`: residential alteration that adds units;
      - component `detached_garage_unit`: detached-garage permit that adds units;
      - component `new_dwelling_on_occupied_lot`: new one/two-family construction on a parcel
        whose recorded building predates the permit (could be a rear house or a replacement).
    `central` needs a unique parcel match, an existing building (year built before the permit
    year) and one recorded unit; `upper` also admits two recorded units (the record may already
    show the added unit) and new dwellings on occupied lots.
    """
    m = mprop.copy()
    m["lo"] = pd.to_numeric(m["house_lo"], errors="coerce")
    m["hi"] = pd.to_numeric(m["house_hi"], errors="coerce")
    m["nr_units"] = pd.to_numeric(m["nr_units"], errors="coerce")
    m["yr_built"] = pd.to_numeric(m["yr_built"], errors="coerce")
    by_street = {k: g for k, g in m.groupby(["sdir", "street"])}
    p = permits[(permits["units_impact"] == "Added or Gained")
                & permits["permit_type"].str.startswith("Residential")].copy()
    rows = []
    for r in p.itertuples(index=False):
        parsed = parse_milwaukee_address(r.address)
        n_match, units, built = 0, None, None
        if parsed:
            g = by_street.get((parsed[1], parsed[2]))
            if g is not None:
                hit = g[(g["lo"] <= parsed[0]) & (g["hi"] >= parsed[0])]
                n_match = len(hit)
                if n_match == 1:
                    units, built = hit["nr_units"].iloc[0], hit["yr_built"].iloc[0]
        use = str(r.use).strip().lower()
        if "alteration" in r.permit_type.lower():
            comp = "conversion_or_attached"
        elif use == "detached garage":
            comp = "detached_garage_unit"
        else:
            comp = "new_dwelling_on_occupied_lot"
        existing = n_match == 1 and built is not None and 0 < built < r.issued.year
        central = existing and units == 1 and comp != "new_dwelling_on_occupied_lot"
        upper = existing and units in (1, 2)
        rows.append({"record_id": r.record_id, "issued": r.issued, "component": comp,
                     "parcel_matches": n_match, "nr_units": units, "yr_built": built,
                     "central": bool(central), "upper": bool(upper)})
    return pd.DataFrame(rows, columns=["record_id", "issued", "component", "parcel_matches",
                                       "nr_units", "yr_built", "central", "upper"])


FITCHBURG_ADU_PATTERN = (
    r"\bADUs?\b|accessory dwelling|accessory living|dependen\w* (?:living|unit)|in[- ]law|granny|"
    r"second (?:dwelling|living|residential) unit|2nd (?:dwelling|unit)|"
    r"(?:basement|garage|lower level) (?:apartment|dwelling unit)|apartment (?:in|above)|"
    r"convert\w* .{0,40}(?:duplex|two[- ]family|2[- ]family|2 unit)|coach house|"
    r"guest (?:house|suite|apartment)|living quarters|efficiency unit|backyard cottage"
)


def adu_text_hits(texts: list[str]) -> list[str]:
    """Descriptions that name an ADU-type second home (Fitchburg reports have no unit field)."""
    import re
    pat = re.compile(FITCHBURG_ADU_PATTERN, re.I)
    return [t for t in texts if t and pat.search(t)]
