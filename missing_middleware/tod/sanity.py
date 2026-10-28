"""Light sanity flags for TOD model inputs. They never stop a run: they are printed and saved beside the results.

Three kinds of flag (owner, 2026-10-28, after the rail-only stop list coded Madison's lots 96 km from transit):

1. **Units:** each lot-table column has a written unit and a plausible range; values outside it are flagged.
2. **Policy definition:** an upzoned lot farther from a qualifying stop than the policy allows is flagged.
3. **Out of range:** a city whose lots mostly sit outside the other cities' range on a trait is flagged, because a
   model cannot learn about traits it has not seen.
"""
from __future__ import annotations

import pandas as pd

# column: (unit, low, high). Ranges are generous: they catch wrong units, not unusual lots.
UNITS: dict[str, tuple[str, float, float]] = {
    "acres": ("acres", 0.0, 500.0),
    "width_m": ("metres", 0.0, 2000.0),
    "dist_station_m": ("metres to nearest rail or rapid-bus stop", 0.0, 5000.0),
    "stops_1mile": ("count of rail and rapid-bus stops within 1,609 m", 0.0, 500.0),
    "share_upzoned_half_mile": ("share of nearby lot acres upzoned, 0 to 1", 0.0, 1.0),
    "far_before": ("floor area ratio (FAR cities); height in feet or a district order elsewhere", 0.0, 200.0),
    "homes_on_lot": ("homes", 0.0, 5000.0),
    "units_before": ("homes permitted in the 6 before years", 0.0, 5000.0),
    "units_after": ("homes permitted in the 5 after years", 0.0, 5000.0),
    "rent": ("dollars per month, tract median gross rent", 100.0, 6000.0),
    "home_value": ("dollars, tract median home value", 10_000.0, 5_000_000.0),
    "income": ("dollars per year, tract median household income", 5_000.0, 500_000.0),
    "year_built": ("calendar year", 1700.0, 2030.0),
}
FAR_MAX = 30.0   # a floor area ratio above this is almost surely a different unit (e.g. feet of height)


def unit_flags(D: pd.DataFrame, far_cities: tuple[str, ...] = ()) -> list[dict]:
    out = []
    for col, (unit, lo, hi) in UNITS.items():
        if col not in D:
            continue
        v = pd.to_numeric(D[col], errors="coerce")
        bad = (v < lo) | (v > hi)
        for city, n in bad.groupby(D["city"]).sum().items():
            if n:
                out.append({"kind": "units", "city": city, "item": col,
                            "detail": f"{int(n)} lots outside {lo:g} to {hi:g} ({unit})"})
    if far_cities and "far_before" in D:
        m = D["city"].isin(far_cities) & (pd.to_numeric(D["far_before"], errors="coerce") > FAR_MAX)
        for city, n in m.groupby(D["city"]).sum().items():
            if n:
                out.append({"kind": "units", "city": city, "item": "far_before",
                            "detail": f"{int(n)} lots with floor area ratio above {FAR_MAX:g}: likely another unit"})
        lv = pd.to_numeric(D["far_before"], errors="coerce")
        lv_after = lv + pd.to_numeric(D.get("far_gain", 0), errors="coerce").fillna(0)
        for city in far_cities:
            m = D["city"] == city
            vals = set(pd.concat([lv[m], lv_after[m]]).dropna().round(6).unique())
            if m.any() and vals <= {0.0, 1.0}:
                out.append({"kind": "units", "city": city, "item": "far_before",
                            "detail": "floor area ratio takes only 0 and 1: likely an in/out flag, not a ratio"})
    return out


def policy_flags(D: pd.DataFrame, max_m: float = 805.0) -> list[dict]:
    out = []
    t = D[D["treated"] == 1]
    far = (t["dist_station_m"] > max_m).groupby(t["city"]).mean()
    for city, s in far.items():
        if s > 0:
            out.append({"kind": "policy", "city": city, "item": "dist_station_m",
                        "detail": f"{s:.0%} of upzoned lots beyond {max_m:g} m of a qualifying stop"})
    return out


def range_flags(X: pd.DataFrame, city: pd.Series, share: float = 0.25) -> list[dict]:
    """For each city and trait: share of its lots outside the other cities' 1st to 99th percentile."""
    out = []
    for c in city.unique():
        me, rest = city == c, city != c
        for f in X.columns:
            lo, hi = X.loc[rest, f].quantile([0.01, 0.99])
            if lo == hi:
                continue
            s = ((X.loc[me, f] < lo) | (X.loc[me, f] > hi)).mean()
            if s > share:
                out.append({"kind": "out of range", "city": c, "item": f,
                            "detail": f"{s:.0%} of lots outside other cities' 1st to 99th percentile "
                                      f"({lo:.3g} to {hi:.3g}); city median {X.loc[me, f].median():.3g}"})
    return out


def report(flags: list[dict], path=None) -> pd.DataFrame:
    F = pd.DataFrame(flags, columns=["kind", "city", "item", "detail"])
    print(f"SANITY FLAGS: {len(F)} (flags only, run continues)", flush=True)
    if len(F):
        print(F.to_string(index=False), flush=True)
    if path is not None:
        F.to_csv(path, index=False)
    return F
